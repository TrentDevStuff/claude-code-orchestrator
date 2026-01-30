"""
REST API endpoints for Claude Code API Service.

Provides endpoints for:
- Chat completions (single prompts)
- Batch processing (multiple prompts)
- Usage tracking and reporting
- Model routing recommendations
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import asyncio
from datetime import datetime

from src.worker_pool import WorkerPool, TaskStatus
from src.model_router import auto_select_model
from src.budget_manager import BudgetManager
from src.auth import verify_api_key


# ============================================================================
# Pydantic Models
# ============================================================================

class Message(BaseModel):
    """Single message in a conversation."""
    role: str = Field(..., description="Role: 'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message content")


class ChatCompletionRequest(BaseModel):
    """Request model for chat completions."""
    messages: List[Message] = Field(..., description="Conversation messages")
    model: Optional[str] = Field(None, description="Model to use (haiku, sonnet, opus). If not provided, auto-selected.")
    timeout: float = Field(30.0, description="Request timeout in seconds", ge=1.0, le=300.0)
    max_tokens: Optional[int] = Field(None, description="Estimated context size for auto-routing")


class Usage(BaseModel):
    """Token usage statistics."""
    input_tokens: int
    output_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    """Response model for chat completions."""
    id: str = Field(..., description="Unique task ID")
    model: str = Field(..., description="Model used")
    content: str = Field(..., description="Generated response")
    usage: Usage
    cost: float = Field(..., description="Cost in USD")
    project_id: str


class BatchPrompt(BaseModel):
    """Single prompt in a batch request."""
    prompt: str = Field(..., description="Prompt text")
    id: Optional[str] = Field(None, description="Optional identifier for this prompt")


class BatchRequest(BaseModel):
    """Request model for batch processing."""
    prompts: List[BatchPrompt] = Field(..., description="List of prompts to process")
    model: Optional[str] = Field(None, description="Model to use for all prompts")
    timeout: float = Field(30.0, description="Per-prompt timeout in seconds", ge=1.0, le=300.0)


class BatchResult(BaseModel):
    """Result for a single batch item."""
    id: Optional[str] = Field(None, description="Prompt ID (if provided)")
    prompt: str
    status: str
    content: Optional[str] = None
    usage: Optional[Usage] = None
    cost: Optional[float] = None
    error: Optional[str] = None


class BatchResponse(BaseModel):
    """Response model for batch processing."""
    total: int
    completed: int
    failed: int
    results: List[BatchResult]
    total_cost: float
    total_tokens: int


class RouteRequest(BaseModel):
    """Request model for model routing recommendation."""
    prompt: str = Field(..., description="Task description/prompt")
    context_size: int = Field(0, description="Estimated context size in tokens", ge=0)


class RouteResponse(BaseModel):
    """Response model for routing recommendation."""
    recommended_model: str
    reasoning: str
    budget_status: Dict[str, Any]


class UsageByModel(BaseModel):
    """Usage stats for a single model."""
    tokens: int
    cost: float


class UsageResponse(BaseModel):
    """Response model for usage statistics."""
    project_id: str
    period: str
    total_tokens: int
    total_cost: float
    by_model: Dict[str, UsageByModel]
    limit: Optional[int]
    remaining: Optional[int]


# ============================================================================
# API Router
# ============================================================================

router = APIRouter(prefix="/v1", tags=["API"])

# Global instances (will be initialized in main.py)
worker_pool: Optional[WorkerPool] = None
budget_manager: Optional[BudgetManager] = None


def initialize_services(pool: WorkerPool, budget: BudgetManager):
    """Initialize global service instances."""
    global worker_pool, budget_manager
    worker_pool = pool
    budget_manager = budget


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def chat_completion(
    request: ChatCompletionRequest,
    project_id: str = Depends(verify_api_key)
) -> ChatCompletionResponse:
    """
    Generate a chat completion using Claude CLI.

    - Requires valid API key via Bearer token
    - Uses WorkerPool for process management
    - Auto-selects model if not specified
    - Tracks usage in BudgetManager
    - Returns completion + usage statistics
    """
    if worker_pool is None or budget_manager is None:
        raise HTTPException(status_code=500, detail="Services not initialized")

    # Combine messages into a single prompt
    prompt = "\n\n".join([f"{msg.role}: {msg.content}" for msg in request.messages])

    # Auto-select model if not provided
    if request.model is None:
        # Get budget remaining
        usage_stats = await budget_manager.get_usage(project_id, period="month")
        budget_remaining = usage_stats.get("remaining") or float('inf')

        context_size = request.max_tokens or len(prompt.split())
        request.model = auto_select_model(prompt, context_size, budget_remaining)

    # Check budget before proceeding
    estimated_tokens = len(prompt.split()) * 2  # Rough estimate
    budget_ok = await budget_manager.check_budget(project_id, estimated_tokens)

    if not budget_ok:
        raise HTTPException(
            status_code=429,
            detail=f"Budget exceeded for project {project_id}"
        )

    # Submit task to worker pool
    task_id = worker_pool.submit(
        prompt=prompt,
        model=request.model,
        project_id=project_id,
        timeout=request.timeout
    )

    # Wait for result (blocking in async context)
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        worker_pool.get_result,
        task_id,
        request.timeout
    )

    # Handle errors
    if result.status != TaskStatus.COMPLETED:
        raise HTTPException(
            status_code=500,
            detail=f"Task failed: {result.error}"
        )

    # Track usage
    await budget_manager.track_usage(
        project_id=project_id,
        model=request.model,
        tokens=result.usage["total_tokens"],
        cost=result.cost
    )

    return ChatCompletionResponse(
        id=task_id,
        model=request.model,
        content=result.completion,
        usage=Usage(**result.usage),
        cost=result.cost,
        project_id=project_id
    )


@router.post("/batch", response_model=BatchResponse)
async def batch_processing(
    request: BatchRequest,
    project_id: str = Depends(verify_api_key)
) -> BatchResponse:
    """
    Process multiple prompts in parallel using the worker pool.

    - Requires valid API key via Bearer token
    - Submits all prompts concurrently
    - Waits for all to complete
    - Returns aggregate statistics
    """
    if worker_pool is None or budget_manager is None:
        raise HTTPException(status_code=500, detail="Services not initialized")

    # Auto-select model if not provided
    model = request.model
    if model is None:
        # Use first prompt for model selection
        usage_stats = await budget_manager.get_usage(project_id, period="month")
        budget_remaining = usage_stats.get("remaining") or float('inf')

        first_prompt = request.prompts[0].prompt
        context_size = len(first_prompt.split())
        model = auto_select_model(first_prompt, context_size, budget_remaining)

    # Submit all tasks
    task_ids = []
    for batch_item in request.prompts:
        task_id = worker_pool.submit(
            prompt=batch_item.prompt,
            model=model,
            project_id=project_id,
            timeout=request.timeout
        )
        task_ids.append((task_id, batch_item))

    # Wait for all results
    loop = asyncio.get_event_loop()
    results = []
    total_cost = 0.0
    total_tokens = 0
    completed = 0
    failed = 0

    for task_id, batch_item in task_ids:
        result = await loop.run_in_executor(
            None,
            worker_pool.get_result,
            task_id,
            request.timeout
        )

        if result.status == TaskStatus.COMPLETED:
            completed += 1
            total_cost += result.cost
            total_tokens += result.usage["total_tokens"]

            # Track usage
            await budget_manager.track_usage(
                project_id=project_id,
                model=model,
                tokens=result.usage["total_tokens"],
                cost=result.cost
            )

            results.append(BatchResult(
                id=batch_item.id,
                prompt=batch_item.prompt,
                status="completed",
                content=result.completion,
                usage=Usage(**result.usage),
                cost=result.cost
            ))
        else:
            failed += 1
            results.append(BatchResult(
                id=batch_item.id,
                prompt=batch_item.prompt,
                status="failed",
                error=result.error
            ))

    return BatchResponse(
        total=len(request.prompts),
        completed=completed,
        failed=failed,
        results=results,
        total_cost=total_cost,
        total_tokens=total_tokens
    )


@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    project_id: str = Depends(verify_api_key),
    period: str = Query("month", description="Time period: month, week, or day")
) -> UsageResponse:
    """
    Get usage statistics for a project.

    Query parameters:
    - project_id: Project identifier
    - period: Time period (month, week, day)

    Returns usage stats, costs, and budget information.
    """
    if budget_manager is None:
        raise HTTPException(status_code=500, detail="Budget manager not initialized")

    try:
        stats = await budget_manager.get_usage(project_id, period)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Convert by_model to proper format
    by_model = {
        model_name: UsageByModel(**model_stats)
        for model_name, model_stats in stats["by_model"].items()
    }

    return UsageResponse(
        project_id=project_id,
        period=period,
        total_tokens=stats["total_tokens"],
        total_cost=stats["total_cost"],
        by_model=by_model,
        limit=stats["limit"],
        remaining=stats["remaining"]
    )


@router.post("/route", response_model=RouteResponse)
async def route_recommendation(
    request: RouteRequest,
    project_id: str = Depends(verify_api_key)
) -> RouteResponse:
    """
    Get model routing recommendation for a prompt.

    - Requires valid API key via Bearer token
    - Tests the model routing logic and returns:
    - Recommended model
    - Reasoning for the selection
    - Current budget status
    """
    if budget_manager is None:
        raise HTTPException(status_code=500, detail="Budget manager not initialized")

    # Get budget status
    usage_stats = await budget_manager.get_usage(project_id, period="month")
    budget_remaining = usage_stats.get("remaining") or float('inf')

    # Get recommendation
    recommended_model = auto_select_model(
        request.prompt,
        request.context_size,
        budget_remaining
    )

    # Generate reasoning
    reasoning_parts = []

    if budget_remaining < 1000:
        reasoning_parts.append("Budget constraint: Insufficient budget forces Haiku")
    elif request.context_size > 10000:
        reasoning_parts.append("Context constraint: Large context requires Opus")

    if len(request.prompt) < 100:
        simple_keywords = ["list", "format", "count", "show", "get", "create", "add"]
        if any(kw in request.prompt.lower() for kw in simple_keywords):
            reasoning_parts.append("Simple prompt with basic keywords → Haiku")

    complex_keywords = ["analyze", "architect", "debug", "design", "implement", "optimize",
                       "refactor", "review", "test", "diagnose", "strategy"]
    if any(kw in request.prompt.lower() for kw in complex_keywords):
        if budget_remaining >= 5000:
            reasoning_parts.append("Complex reasoning keywords with sufficient budget → Sonnet")
        else:
            reasoning_parts.append("Complex keywords but limited budget → Haiku")

    if not reasoning_parts:
        reasoning_parts.append("Medium complexity task → Sonnet (default)")

    reasoning = " | ".join(reasoning_parts)

    return RouteResponse(
        recommended_model=recommended_model,
        reasoning=reasoning,
        budget_status={
            "total_tokens": usage_stats["total_tokens"],
            "total_cost": usage_stats["total_cost"],
            "limit": usage_stats["limit"],
            "remaining": usage_stats["remaining"]
        }
    )
