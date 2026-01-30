"""Claude Code API Client Library."""

from .client import ClaudeClient
from .async_client import AsyncClaudeClient
from .models import (
    CompletionRequest,
    CompletionResponse,
    AgenticTaskRequest,
    AgenticTaskResponse,
    ExecutionLogEntry,
    Artifact
)
from .exceptions import (
    ClaudeAPIError,
    AuthenticationError,
    RateLimitError,
    PermissionError,
    TimeoutError,
    CostExceededError
)

__version__ = "0.1.0"

__all__ = [
    "ClaudeClient",
    "AsyncClaudeClient",
    "CompletionRequest",
    "CompletionResponse",
    "AgenticTaskRequest",
    "AgenticTaskResponse",
    "ExecutionLogEntry",
    "Artifact",
    "ClaudeAPIError",
    "AuthenticationError",
    "RateLimitError",
    "PermissionError",
    "TimeoutError",
    "CostExceededError",
]
