"""Custom exceptions for Claude Code API client."""


class ClaudeAPIError(Exception):
    """Base exception for all API errors."""
    pass


class AuthenticationError(ClaudeAPIError):
    """Invalid or missing API key."""
    pass


class RateLimitError(ClaudeAPIError):
    """Rate limit exceeded."""
    pass


class PermissionError(ClaudeAPIError):
    """Tool/agent/skill not allowed for this API key."""
    pass


class TimeoutError(ClaudeAPIError):
    """Task exceeded timeout."""
    pass


class CostExceededError(ClaudeAPIError):
    """Task exceeded cost limit."""
    pass
