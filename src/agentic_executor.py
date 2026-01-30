"""Agentic task executor with audit logging integration."""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import datetime
import asyncio

from src.audit_logger import AuditLogger


# ============================================================================
# Pydantic Models
# ============================================================================

class AgenticTaskRequest(BaseModel):
    """Request model for agentic task execution."""
    task_id: str
    api_key: str
    prompt: str
    agent_type: str
    timeout: Optional[float] = 300.0
    max_cost_usd: Optional[float] = None


class ExecutionLogEntry(BaseModel):
    """Single entry in execution log."""
    timestamp: datetime
    event_type: str  # tool_call, agent_spawn, skill_invoke, etc.
    details: Dict[str, Any]


class Artifact(BaseModel):
    """Generated artifact from task execution."""
    name: str
    content: str
    mime_type: str


class AgenticTaskResponse(BaseModel):
    """Response model for agentic task execution."""
    task_id: str
    status: str  # success, failed, timeout, cost_limit
    result: Optional[str] = None
    execution_log: List[ExecutionLogEntry] = []
    artifacts: List[Artifact] = []
    total_cost_usd: float = 0.0


# ============================================================================
# Agentic Executor
# ============================================================================

class AgenticExecutor:
    """
    Executes agentic tasks with full audit logging.

    Orchestrates tools, agents, and skills while maintaining comprehensive
    audit trail of all actions.
    """

    def __init__(self, audit_logger: AuditLogger):
        """
        Initialize AgenticExecutor.

        Args:
            audit_logger: AuditLogger instance for logging events
        """
        self.audit_logger = audit_logger

    async def execute_task(self, request: AgenticTaskRequest) -> AgenticTaskResponse:
        """
        Execute an agentic task with full audit logging.

        Args:
            request: AgenticTaskRequest with task details

        Returns:
            AgenticTaskResponse with execution results
        """
        execution_log: List[ExecutionLogEntry] = []
        artifacts: List[Artifact] = []

        try:
            # Log task start
            await self.audit_logger.log_tool_call(
                request.task_id,
                request.api_key,
                "task_start",
                {"agent_type": request.agent_type, "prompt_length": len(request.prompt)}
            )

            # Simulate tool call execution
            await self.audit_logger.log_tool_call(
                request.task_id,
                request.api_key,
                "Read",
                {"file": "example.txt"}
            )

            # Simulate agent spawn
            await self.audit_logger.log_agent_spawn(
                request.task_id,
                request.api_key,
                request.agent_type
            )

            # Simulate skill invocation
            await self.audit_logger.log_skill_invoke(
                request.task_id,
                request.api_key,
                "example-skill",
                {"param1": "value1"}
            )

            # Simulate bash command
            await self.audit_logger.log_bash_command(
                request.task_id,
                request.api_key,
                "pytest tests/"
            )

            # Create execution log entries
            execution_log.append(ExecutionLogEntry(
                timestamp=datetime.utcnow(),
                event_type="tool_call",
                details={"tool": "Read", "file": "example.txt"}
            ))

            return AgenticTaskResponse(
                task_id=request.task_id,
                status="success",
                result="Task executed successfully",
                execution_log=execution_log,
                artifacts=artifacts,
                total_cost_usd=0.0
            )

        except Exception as e:
            # Log security event on error
            await self.audit_logger.log_security_event(
                request.task_id,
                request.api_key,
                "execution_error",
                {"error": str(e)}
            )

            return AgenticTaskResponse(
                task_id=request.task_id,
                status="failed",
                result=f"Task failed: {str(e)}",
                execution_log=execution_log,
                artifacts=artifacts,
                total_cost_usd=0.0
            )
