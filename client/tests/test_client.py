"""Tests for synchronous ClaudeClient."""

import pytest
from unittest.mock import Mock, patch
from claude_code_client import (
    ClaudeClient,
    CompletionResponse,
    AgenticTaskResponse,
    AuthenticationError,
    RateLimitError,
    PermissionError,
)


def test_client_initialization():
    """Test client initialization."""
    client = ClaudeClient(api_key="test-key")
    assert client.api_key == "test-key"
    assert client.base_url == "http://localhost:8000/v1"
    assert client.timeout == 300


def test_context_manager():
    """Test client context manager."""
    with patch("claude_code_client.client.httpx.Client"):
        with ClaudeClient(api_key="test-key") as client:
            assert client is not None


def test_simple_completion():
    """Test simple completion."""
    with patch("claude_code_client.client.httpx.Client") as MockClient:
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": "Async/await is a syntax for asynchronous programming.",
            "model": "sonnet",
            "usage": {"total_tokens": 50, "cost": 0.001},
        }
        MockClient.return_value.post.return_value = mock_response

        client = ClaudeClient(api_key="test-key", base_url="http://test:8000/v1")
        response = client.complete("What is async/await?")

        assert isinstance(response, CompletionResponse)
        assert "Async/await" in response.content
        assert response.model == "sonnet"


def test_agentic_task():
    """Test agentic task execution."""
    with patch("claude_code_client.client.httpx.Client") as MockClient:
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "task_id": "task-123",
            "status": "completed",
            "result": {"summary": "Analysis complete"},
            "execution_log": [
                {
                    "step": 1,
                    "timestamp": "2024-01-01T00:00:00Z",
                    "action": "tool_call",
                    "details": {"tool": "Read", "file": "test.py"},
                }
            ],
            "artifacts": [],
            "usage": {"total_cost": 0.05},
        }
        MockClient.return_value.post.return_value = mock_response

        client = ClaudeClient(api_key="test-key", base_url="http://test:8000/v1")
        result = client.execute_task(
            description="Analyze code", allow_tools=["Read"], timeout=60
        )

        assert isinstance(result, AgenticTaskResponse)
        assert result.status == "completed"
        assert len(result.execution_log) == 1


def test_authentication_error():
    """Test authentication error handling."""
    with patch("claude_code_client.client.httpx.Client") as MockClient:
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Invalid API key"
        MockClient.return_value.post.return_value = mock_response

        client = ClaudeClient(api_key="test-key", base_url="http://test:8000/v1")
        with pytest.raises(AuthenticationError):
            client.complete("Test")


def test_rate_limit_error():
    """Test rate limit error handling."""
    with patch("claude_code_client.client.httpx.Client") as MockClient:
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        MockClient.return_value.post.return_value = mock_response

        client = ClaudeClient(api_key="test-key", base_url="http://test:8000/v1")
        with pytest.raises(RateLimitError):
            client.complete("Test")


def test_permission_error():
    """Test permission error handling."""
    with patch("claude_code_client.client.httpx.Client") as MockClient:
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.text = "Permission denied: agent not allowed"
        MockClient.return_value.post.return_value = mock_response

        client = ClaudeClient(api_key="test-key", base_url="http://test:8000/v1")
        with pytest.raises(PermissionError):
            client.execute_task(description="Test", allow_agents=["forbidden"])


def test_headers():
    """Test request headers."""
    client = ClaudeClient(api_key="test-key-123")
    headers = client._get_headers()

    assert headers["Authorization"] == "Bearer test-key-123"
    assert headers["Content-Type"] == "application/json"
