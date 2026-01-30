"""Tests for asynchronous AsyncClaudeClient."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from claude_code_client import (
    AsyncClaudeClient,
    CompletionResponse,
    AgenticTaskResponse,
    AuthenticationError,
)


@pytest.mark.asyncio
async def test_client_initialization():
    """Test async client initialization."""
    with patch("claude_code_client.async_client.httpx.AsyncClient") as MockClient:
        MockClient.return_value.aclose = AsyncMock()
        client = AsyncClaudeClient(api_key="test-key")
        assert client.api_key == "test-key"
        assert client.base_url == "http://localhost:8000/v1"
        await client.close()


@pytest.mark.asyncio
async def test_context_manager():
    """Test async client context manager."""
    with patch("claude_code_client.async_client.httpx.AsyncClient") as MockClient:
        MockClient.return_value.aclose = AsyncMock()
        async with AsyncClaudeClient(api_key="test-key") as client:
            assert client is not None


@pytest.mark.asyncio
async def test_simple_completion():
    """Test async simple completion."""
    with patch("claude_code_client.async_client.httpx.AsyncClient") as MockClient:
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": "Async/await is a syntax for asynchronous programming.",
            "model": "sonnet",
            "usage": {"total_tokens": 50, "cost": 0.001},
        }
        MockClient.return_value.post = AsyncMock(return_value=mock_response)
        MockClient.return_value.aclose = AsyncMock()

        client = AsyncClaudeClient(api_key="test-key", base_url="http://test:8000/v1")
        response = await client.complete("What is async/await?")

        assert isinstance(response, CompletionResponse)
        assert "Async/await" in response.content
        await client.close()


@pytest.mark.asyncio
async def test_agentic_task():
    """Test async agentic task execution."""
    with patch("claude_code_client.async_client.httpx.AsyncClient") as MockClient:
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "task_id": "task-123",
            "status": "completed",
            "result": {"summary": "Analysis complete"},
            "execution_log": [],
            "artifacts": [],
            "usage": {"total_cost": 0.05},
        }
        MockClient.return_value.post = AsyncMock(return_value=mock_response)
        MockClient.return_value.aclose = AsyncMock()

        client = AsyncClaudeClient(api_key="test-key", base_url="http://test:8000/v1")
        result = await client.execute_task(
            description="Analyze code", allow_tools=["Read"], timeout=60
        )

        assert isinstance(result, AgenticTaskResponse)
        assert result.status == "completed"
        await client.close()


@pytest.mark.asyncio
async def test_authentication_error():
    """Test async authentication error handling."""
    with patch("claude_code_client.async_client.httpx.AsyncClient") as MockClient:
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Invalid API key"
        MockClient.return_value.post = AsyncMock(return_value=mock_response)
        MockClient.return_value.aclose = AsyncMock()

        client = AsyncClaudeClient(api_key="test-key", base_url="http://test:8000/v1")
        with pytest.raises(AuthenticationError):
            await client.complete("Test")
        await client.close()
