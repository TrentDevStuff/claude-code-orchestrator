"""Asynchronous Claude Code API client."""

from typing import AsyncIterator, List, Optional
import httpx

from .models import (
    CompletionRequest,
    CompletionResponse,
    AgenticTaskRequest,
    AgenticTaskResponse,
)
from .exceptions import (
    ClaudeAPIError,
    AuthenticationError,
    RateLimitError,
    PermissionError,
    TimeoutError as ClientTimeoutError,
    CostExceededError,
)


class AsyncClaudeClient:
    """
    Asynchronous Python client for Claude Code API.

    Usage:
        async with AsyncClaudeClient(api_key="sk-proj-...") as client:
            # Simple completion
            response = await client.complete("Explain async/await")
            print(response.content)

            # Agentic task
            result = await client.execute_task(
                description="Analyze our API for security issues",
                allow_tools=["Read", "Grep"],
                allow_agents=["security-auditor"]
            )
            print(result.result)
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "http://localhost:8000/v1",
        timeout: int = 300,
    ):
        """
        Initialize async Claude Code client.

        Args:
            api_key: API key for authentication
            base_url: Base URL for API (default: http://localhost:8000/v1)
            timeout: Default timeout in seconds (default: 300)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)

    async def __aenter__(self):
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

    def _get_headers(self) -> dict:
        """Get request headers with auth."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _handle_error(self, response: httpx.Response):
        """Handle API error responses."""
        if response.status_code == 401:
            raise AuthenticationError("Invalid API key")
        elif response.status_code == 403:
            raise PermissionError(f"Permission denied: {response.text}")
        elif response.status_code == 429:
            raise RateLimitError("Rate limit exceeded")
        elif response.status_code == 504:
            raise ClientTimeoutError("Request timeout")
        elif response.status_code >= 400:
            raise ClaudeAPIError(f"API error: {response.status_code} {response.text}")

    async def complete(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 1.0,
    ) -> CompletionResponse:
        """
        Simple text completion (async).

        Args:
            prompt: Input text
            model: Model to use (haiku/sonnet/opus), auto-selected if None
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-2.0)

        Returns:
            CompletionResponse with generated text

        Raises:
            AuthenticationError: Invalid API key
            RateLimitError: Rate limit exceeded
            ClaudeAPIError: Other API errors
        """
        request = CompletionRequest(
            prompt=prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        response = await self._client.post(
            f"{self.base_url}/chat/completions",
            json=request.model_dump(),
            headers=self._get_headers(),
        )

        if response.status_code != 200:
            self._handle_error(response)

        return CompletionResponse(**response.json())

    async def execute_task(
        self,
        description: str,
        allow_tools: Optional[List[str]] = None,
        allow_agents: Optional[List[str]] = None,
        allow_skills: Optional[List[str]] = None,
        working_directory: str = "/project",
        timeout: int = 300,
        max_cost: float = 1.0,
        model: Optional[str] = None,
        project_id: str = "default",
    ) -> AgenticTaskResponse:
        """
        Execute an agentic task with Claude Code capabilities (async).

        Args:
            description: Natural language task description
            allow_tools: Tools to enable (Read, Grep, Bash, etc.)
            allow_agents: Agents to allow
            allow_skills: Skills to allow
            working_directory: Working directory for task
            timeout: Task timeout in seconds
            max_cost: Maximum cost in USD
            model: Model to use (haiku/sonnet/opus), auto-selected if None
            project_id: Project ID for budget tracking

        Returns:
            AgenticTaskResponse with results, logs, artifacts

        Raises:
            AuthenticationError: Invalid API key
            PermissionError: Tools/agents not allowed for this API key
            ClientTimeoutError: Task exceeded timeout
            CostExceededError: Task exceeded cost limit
            ClaudeAPIError: Other errors
        """
        request = AgenticTaskRequest(
            description=description,
            allow_tools=allow_tools or [],
            allow_agents=allow_agents or [],
            allow_skills=allow_skills or [],
            working_directory=working_directory,
            timeout=timeout,
            max_cost=max_cost,
            model=model,
            project_id=project_id,
        )

        response = await self._client.post(
            f"{self.base_url}/task",
            json=request.model_dump(),
            headers=self._get_headers(),
            timeout=timeout + 10,  # Add buffer to timeout
        )

        if response.status_code != 200:
            self._handle_error(response)

        data = response.json()

        # Check for cost/timeout status
        if data.get("status") == "cost_exceeded":
            raise CostExceededError(f"Task exceeded cost limit: {data.get('usage', {})}")
        elif data.get("status") == "timeout":
            raise ClientTimeoutError(f"Task exceeded timeout: {timeout}s")

        return AgenticTaskResponse(**data)

    async def stream_task(
        self,
        description: str,
        **kwargs,
    ) -> AsyncIterator[dict]:
        """
        Stream agentic task execution events in real-time (async).

        Args:
            description: Task description
            **kwargs: Same as execute_task()

        Yields:
            Event dictionaries:
            - {"type": "thinking", "content": "..."}
            - {"type": "tool_call", "tool": "Read", "file": "..."}
            - {"type": "result", "summary": "...", "artifacts": [...]}

        Example:
            async for event in client.stream_task("Analyze code"):
                if event["type"] == "thinking":
                    print(f"🤔 {event['content']}")
                elif event["type"] == "tool_call":
                    print(f"🔧 {event['tool']}")
                elif event["type"] == "result":
                    print(f"✅ {event['summary']}")
        """
        import websockets
        import json

        ws_url = self.base_url.replace("http://", "ws://").replace("https://", "wss://")
        ws_url = f"{ws_url}/stream"

        async with websockets.connect(
            ws_url,
            additional_headers={"Authorization": f"Bearer {self.api_key}"},
        ) as websocket:
            # Send task request
            request = AgenticTaskRequest(
                description=description,
                allow_tools=kwargs.get("allow_tools", []),
                allow_agents=kwargs.get("allow_agents", []),
                allow_skills=kwargs.get("allow_skills", []),
                working_directory=kwargs.get("working_directory", "/project"),
                timeout=kwargs.get("timeout", 300),
                max_cost=kwargs.get("max_cost", 1.0),
                model=kwargs.get("model"),
                project_id=kwargs.get("project_id", "default"),
            )

            await websocket.send(json.dumps({"type": "agentic_task", **request.model_dump()}))

            # Stream events
            async for message in websocket:
                event = json.loads(message)
                yield event
                if event.get("type") == "result":
                    break
