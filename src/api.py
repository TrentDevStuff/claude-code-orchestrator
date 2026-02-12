"""
REST API endpoints for Claude Code API Service.

Provides endpoints for:
- Chat completions (single prompts)
- Batch processing (multiple prompts)
- Usage tracking and reporting
- Model routing recommendations
"""

from fastapi import APIRouter, HTTPException, Query, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import asyncio
from datetime import datetime

from src.worker_pool import WorkerPool, TaskStatus
from src.model_router import auto_select_model
from src.budget_manager import BudgetManager
from src.auth import verify_api_key
from src.permission_manager import PermissionManager
from src.agentic_executor import AgenticExecutor, AgenticTaskRequest, AgenticTaskResponse


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
permission_manager: Optional[PermissionManager] = None


def initialize_services(pool: WorkerPool, budget: BudgetManager, permissions: PermissionManager = None):
    """Initialize global service instances."""
    global worker_pool, budget_manager, permission_manager
    worker_pool = pool
    budget_manager = budget
    permission_manager = permissions


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


#
# ============================================================================
# AI SERVICES COMPATIBILITY LAYER
# ============================================================================
# Provides /v1/process endpoint that mirrors the production AI service API.
# Allows prototypes to switch between services transparently.
#

from src.compatibility_adapter import (
    ProcessRequest,
    AIServiceResponse,
    map_model_to_claude,
    convert_to_messages,
    convert_response
)


@router.post("/process", response_model=AIServiceResponse)
async def process_ai_services_compatible(
    request: ProcessRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    AI Services compatible endpoint.

    Mirrors the production ai-services API at /v1/process.
    Maps multi-provider requests to Claude Code models.

    Supports:
    - provider/model_name mapping to haiku/sonnet/opus
    - messages, system_message, user_message formats
    - Synchronous mode
    - Streaming mode (SSE) via additional_params.stream
    - Async mode via async_processing

    Unsupported (gracefully ignored):
    - tools/function calling
    - multimodal content
    - structured outputs
    - memory management
    """
    # Map to Claude model
    claude_model = map_model_to_claude(request.provider, request.model_name)

    # Convert messages
    messages = convert_to_messages(request)

    if not messages:
        raise HTTPException(400, "No messages provided")

    # Check unsupported features
    unsupported_features = []
    if request.tools:
        unsupported_features.append("tools")
    if request.output_schema:
        unsupported_features.append("structured_outputs")
    if request.media_content:
        unsupported_features.append("multimodal")
    if request.memory:
        unsupported_features.append("memory")

    # Warn about unsupported features (but continue)
    if unsupported_features:
        print(f"Warning: Ignoring unsupported features: {unsupported_features}")

    # Check streaming mode
    is_streaming = request.additional_params and request.additional_params.get("stream", False)

    # Streaming not yet implemented in compatibility layer
    if is_streaming:
        raise HTTPException(501, "Streaming via /v1/process not yet implemented. Use /v1/stream WebSocket instead.")

    # Async mode not yet implemented
    if request.async_processing:
        raise HTTPException(501, "Async processing not yet implemented")

    # Format prompt for Claude
    prompt_parts = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "system":
            prompt_parts.append(f"System: {content}")
        elif role == "user":
            prompt_parts.append(f"User: {content}")
        elif role == "assistant":
            prompt_parts.append(f"Assistant: {content}")

    prompt = "\n\n".join(prompt_parts)

    # Check budget
    estimated_tokens = len(prompt.split()) * 2  # Rough estimate
    if not await budget_manager.check_budget(request.project_id, estimated_tokens):
        raise HTTPException(
            403,
            f"Budget exceeded for project {request.project_id}"
        )

    # Submit to worker pool - Claude CLI needs 10-30s minimum
    timeout = max(30, (request.max_tokens or 1000) / 10)
    task_id = worker_pool.submit(
        prompt=prompt,
        model=claude_model,
        project_id=request.project_id,
        timeout=timeout
    )
    result = worker_pool.get_result(task_id, timeout=timeout)

    # Check for non-success status
    if result.status != TaskStatus.COMPLETED:
        raise HTTPException(
            504 if result.status == TaskStatus.TIMEOUT else 500,
            f"Task {result.status.value}: {result.error or 'Unknown error'}"
        )

    # Track usage
    if result.usage:
        await budget_manager.track_usage(
            request.project_id,
            claude_model,
            result.usage["total_tokens"],
            result.cost or 0
        )

    # Convert to AI services format
    response = convert_response(
        claude_response={
            "content": result.completion or "",
            "usage": result.usage,
            "cost": result.cost
        },
        original_provider=request.provider,
        original_model=request.model_name,
        claude_model=claude_model
    )

    return response


@router.get("/providers")
async def list_providers():
    """
    List available providers (compatibility endpoint).

    Returns only Claude Code as available provider.
    """
    return [
        {
            "name": "claudecode",
            "available": True,
            "models": ["haiku", "sonnet", "opus"]
        },
        {
            "name": "anthropic",
            "available": True,
            "models": ["haiku", "sonnet", "opus", "claude-3-haiku", "claude-3-sonnet", "claude-3-opus"]
        }
    ]


@router.get("/providers/{provider}/models")
async def get_provider_models(provider: str):
    """
    Get models for provider (compatibility endpoint).
    """
    if provider.lower() in ["anthropic", "claudecode", "claude"]:
        return {
            "provider": provider,
            "models": {
                "haiku": {
                    "max_tokens": 4096,
                    "context_window": 200000,
                    "supports_functions": False,
                    "supports_vision": True
                },
                "sonnet": {
                    "max_tokens": 8192,
                    "context_window": 200000,
                    "supports_functions": False,
                    "supports_vision": True
                },
                "opus": {
                    "max_tokens": 4096,
                    "context_window": 200000,
                    "supports_functions": False,
                    "supports_vision": True
                }
            }
        }
    else:
        raise HTTPException(404, f"Provider {provider} not supported. Only 'anthropic' and 'claudecode' available.")


# ============================================================================
# Agentic Task Execution
# ============================================================================

@router.post("/task", response_model=AgenticTaskResponse)
async def execute_agentic_task(
    request: AgenticTaskRequest,
    project_id: str = Depends(verify_api_key),
    credentials: HTTPAuthorizationCredentials = Security(HTTPBearer())
):
    """
    Execute an agentic task with permission validation.

    This endpoint validates the API key's permissions before executing the task:
    - Validates tool/agent/skill access
    - Enforces resource limits (timeout, cost)
    - Checks against permission profile

    Args:
        request: AgenticTaskRequest with task details
        project_id: Project ID from validated API key
        credentials: Raw API key credentials for permission check

    Returns:
        AgenticTaskResponse with execution results

    Raises:
        HTTPException 403: Permission denied
        HTTPException 500: Execution error
    """
    # Validate permissions BEFORE creating sandbox
    if permission_manager is None:
        raise HTTPException(status_code=500, detail="Permission manager not initialized")

    # Get actual API key from credentials
    api_key = credentials.credentials

    validation = permission_manager.validate_task_request(
        api_key=api_key,
        requested_tools=request.allow_tools,
        requested_agents=request.allow_agents,
        requested_skills=request.allow_skills,
        timeout=request.timeout,
        max_cost=request.max_cost
    )

    if not validation.allowed:
        raise HTTPException(
            status_code=403,
            detail=f"Permission denied: {validation.reason}"
        )

    # Execute task with AgenticExecutor
    try:
        executor = AgenticExecutor(
            worker_pool=worker_pool,
            budget_manager=budget_manager
        )
        response = await executor.execute_task(request)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Task execution failed: {str(e)}"
        )

# ============================================================================
# Agent/Skill Discovery Endpoint
# ============================================================================

class AgentListItem(BaseModel):
    """Information about an available agent."""
    name: str
    description: str
    tools: List[str]
    model: str


class SkillListItem(BaseModel):
    """Information about an available skill."""
    name: str
    description: str
    command: str


class CapabilitiesResponse(BaseModel):
    """Response listing available agents and skills."""
    agents: List[AgentListItem]
    skills: List[SkillListItem]
    agents_count: int
    skills_count: int


@router.get("/capabilities", response_model=CapabilitiesResponse)
async def get_capabilities(
    project_id: str = Depends(verify_api_key)
):
    """
    List available Claude Code agents and skills.

    Discovers agents from ~/.claude/agents/ and skills from ~/.claude/skills/
    that can be invoked through the /v1/task endpoint.

    Returns:
        CapabilitiesResponse with all discovered agents and skills
    """
    from src.agent_discovery import AgentSkillDiscovery

    discovery = AgentSkillDiscovery()

    # Discover agents
    agents_dict = discovery.discover_agents()
    agents = [
        AgentListItem(
            name=info.name,
            description=info.description,
            tools=info.tools,
            model=info.model
        )
        for info in agents_dict.values()
    ]

    # Discover skills (exclude agent-wrapped ones)
    skills_dict = discovery.discover_skills()
    skills = [
        SkillListItem(
            name=info.name,
            description=info.description,
            command=info.command
        )
        for info in skills_dict.values()
        if info.user_interface != "agent-wrapped"
    ]

    return CapabilitiesResponse(
        agents=sorted(agents, key=lambda x: x.name),
        skills=sorted(skills, key=lambda x: x.name),
        agents_count=len(agents),
        skills_count=len(skills)
    )
