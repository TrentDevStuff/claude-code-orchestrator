"""
Claude Code API Client Library

A simple, elegant Python client for interacting with Claude Code API Service.

Quick Start:
    from client import ClaudeClient

    # Synchronous usage
    with ClaudeClient(base_url="http://localhost:8080") as client:
        response = client.complete("Hello, Claude!")
        print(response.content)

    # Async usage
    async with AsyncClaudeClient(base_url="http://localhost:8080") as client:
        response = await client.complete("Hello, Claude!")
        print(response.content)
"""

from client.claude_client import (
    # Clients
    ClaudeClient,
    AsyncClaudeClient,

    # Enums
    Model,

    # Data models
    Response,
    Usage,
    BatchResult,
    BatchResponse,
    UsageStats,

    # Exceptions
    ClaudeAPIError,
    AuthenticationError,
    BudgetExceededError,
    TimeoutError,
    RateLimitError,
)

__version__ = "0.1.0"

__all__ = [
    # Clients
    "ClaudeClient",
    "AsyncClaudeClient",

    # Enums
    "Model",

    # Data models
    "Response",
    "Usage",
    "BatchResult",
    "BatchResponse",
    "UsageStats",

    # Exceptions
    "ClaudeAPIError",
    "AuthenticationError",
    "BudgetExceededError",
    "TimeoutError",
    "RateLimitError",
]
