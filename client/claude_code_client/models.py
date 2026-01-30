"""Pydantic models for Claude Code API."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CompletionRequest(BaseModel):
    """Request model for simple text completion."""
    prompt: str = Field(..., description="Input text prompt")
    model: Optional[str] = Field(default=None, description="Model to use (haiku/sonnet/opus), auto-selected if None")
    max_tokens: int = Field(default=1000, description="Maximum tokens to generate")
    temperature: float = Field(default=1.0, ge=0.0, le=2.0, description="Sampling temperature")


class CompletionResponse(BaseModel):
    """Response model for text completion."""
    content: str
    model: str
    usage: Dict[str, Any]


class ExecutionLogEntry(BaseModel):
    """Single entry in execution log."""
    step: int
    timestamp: str
    action: str  # "tool_call", "agent_spawn", "skill_invoke", "thinking", "result"
    details: Dict[str, Any]


class Artifact(BaseModel):
    """Generated artifact from task execution."""
    type: str  # "file", "report", "data"
    path: str
    size_bytes: int
    created_at: str


class AgenticTaskRequest(BaseModel):
    """Request model for agentic task execution."""
    description: str = Field(..., description="Natural language task description")
    allow_tools: List[str] = Field(default_factory=list, description="Allowed tools (Read, Grep, Bash, etc.)")
    allow_agents: List[str] = Field(default_factory=list, description="Allowed agents to spawn")
    allow_skills: List[str] = Field(default_factory=list, description="Allowed skills to invoke")
    working_directory: str = Field(default="/project", description="Working directory for task")
    timeout: int = Field(default=300, description="Timeout in seconds (max 600)")
    max_cost: float = Field(default=1.00, description="Maximum cost in USD")
    model: Optional[str] = Field(default=None, description="Model to use (haiku/sonnet/opus), auto-selected if None")
    project_id: str = Field(default="default", description="Project ID for budget tracking")


class AgenticTaskResponse(BaseModel):
    """Response model for agentic task execution."""
    task_id: str
    status: str  # "completed", "failed", "timeout", "cost_exceeded"
    result: Dict[str, Any]
    execution_log: List[ExecutionLogEntry]
    artifacts: List[Artifact]
    usage: Dict[str, Any]
