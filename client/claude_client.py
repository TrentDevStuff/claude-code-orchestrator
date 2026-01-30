"""
Claude Code API Client Library

A user-friendly Python client for interacting with the Claude Code API Service.
Supports both synchronous and asynchronous operations with automatic retries,
comprehensive error handling, and full type hints.
"""

import httpx
import asyncio
from typing import Optional, List, Dict, Any, Iterator, AsyncIterator, Union
from dataclasses import dataclass
from enum import Enum
import time


# ============================================================================
# Data Models
# ============================================================================

class Model(str, Enum):
    """Available Claude models."""
    HAIKU = "haiku"
    SONNET = "sonnet"
    OPUS = "opus"
    AUTO = "auto"  # Automatic model selection


@dataclass
class Usage:
    """Token usage statistics."""
    input_tokens: int
    output_tokens: int
    total_tokens: int


@dataclass
class Response:
    """Response from a completion request."""
    id: str
    model: str
    content: str
    usage: Usage
    cost: float
    project_id: str


@dataclass
class BatchResult:
    """Result for a single batch item."""
    id: Optional[str]
    prompt: str
    status: str
    content: Optional[str] = None
    usage: Optional[Usage] = None
    cost: Optional[float] = None
    error: Optional[str] = None


@dataclass
class BatchResponse:
    """Response from a batch processing request."""
    total: int
    completed: int
    failed: int
    results: List[BatchResult]
    total_cost: float
    total_tokens: int


@dataclass
class UsageStats:
    """Usage statistics for a project."""
    project_id: str
    period: str
    total_tokens: int
    total_cost: float
    by_model: Dict[str, Dict[str, Union[int, float]]]
    limit: Optional[int]
    remaining: Optional[int]


# ============================================================================
# Exceptions
# ============================================================================

class ClaudeAPIError(Exception):
    """Base exception for Claude API errors."""
    pass


class AuthenticationError(ClaudeAPIError):
    """Authentication failed."""
    pass


class BudgetExceededError(ClaudeAPIError):
    """Project budget exceeded."""
    pass


class TimeoutError(ClaudeAPIError):
    """Request timed out."""
    pass


class RateLimitError(ClaudeAPIError):
    """Rate limit exceeded."""
    pass


# ============================================================================
# Synchronous Client
# ============================================================================

class ClaudeClient:
    """
    Synchronous client for Claude Code API Service.

    Example:
        client = ClaudeClient(
            base_url="http://localhost:8080",
            project_id="my-project"
        )

        response = client.complete("Hello, how are you?")
        print(response.content)
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        api_key: Optional[str] = None,
        project_id: str = "default",
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize Claude API client.

        Args:
            base_url: Base URL of the API service
            api_key: API key for authentication (future feature)
            project_id: Default project ID for budget tracking
            timeout: Default timeout for requests in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.project_id = project_id
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Create HTTP client
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        self.client = httpx.Client(
            base_url=self.base_url,
            headers=headers,
            timeout=timeout
        )

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def _request_with_retry(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> httpx.Response:
        """
        Make HTTP request with automatic retries.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional arguments for httpx request

        Returns:
            HTTP response

        Raises:
            ClaudeAPIError: If request fails after all retries
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                response = self.client.request(method, endpoint, **kwargs)

                # Handle specific status codes
                if response.status_code == 401:
                    raise AuthenticationError("Authentication failed")
                elif response.status_code == 429:
                    error_data = response.json()
                    if "Budget exceeded" in error_data.get("detail", ""):
                        raise BudgetExceededError(error_data["detail"])
                    else:
                        raise RateLimitError("Rate limit exceeded")
                elif response.status_code >= 500:
                    # Server error - retry
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (attempt + 1))
                        continue

                response.raise_for_status()
                return response

            except httpx.TimeoutException as e:
                last_error = TimeoutError(f"Request timed out: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue

            except httpx.RequestError as e:
                last_error = ClaudeAPIError(f"Request failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue

        raise last_error or ClaudeAPIError("Request failed after all retries")

    def complete(
        self,
        prompt: str,
        model: Union[str, Model] = Model.AUTO,
        project_id: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> Response:
        """
        Generate a completion for a single prompt.

        Args:
            prompt: Input prompt text
            model: Model to use (haiku, sonnet, opus, or auto)
            project_id: Project ID (overrides default)
            timeout: Request timeout (overrides default)

        Returns:
            Response object with completion and usage statistics

        Example:
            response = client.complete("Write a haiku about Python")
            print(response.content)
            print(f"Cost: ${response.cost:.4f}")
        """
        # Prepare request data
        request_data = {
            "messages": [{"role": "user", "content": prompt}],
            "project_id": project_id or self.project_id
        }

        # Add model if not auto
        model_str = model.value if isinstance(model, Model) else model
        if model_str != "auto":
            request_data["model"] = model_str

        # Add timeout if specified
        if timeout:
            request_data["timeout"] = timeout

        # Make request
        response = self._request_with_retry(
            "POST",
            "/v1/chat/completions",
            json=request_data
        )

        # Parse response
        data = response.json()
        return Response(
            id=data["id"],
            model=data["model"],
            content=data["content"],
            usage=Usage(**data["usage"]),
            cost=data["cost"],
            project_id=data["project_id"]
        )

    def stream(
        self,
        prompt: str,
        model: Union[str, Model] = Model.AUTO,
        project_id: Optional[str] = None
    ) -> Iterator[str]:
        """
        Stream completion chunks as they arrive.

        Note: Streaming is not yet implemented in the API.
        This method falls back to complete() and yields the full response.

        Args:
            prompt: Input prompt text
            model: Model to use
            project_id: Project ID (overrides default)

        Yields:
            Content chunks

        Example:
            for chunk in client.stream("Write a story"):
                print(chunk, end="", flush=True)
        """
        # TODO: Implement actual streaming when API supports it
        response = self.complete(prompt, model, project_id)
        yield response.content

    def batch(
        self,
        prompts: List[str],
        model: Union[str, Model] = Model.AUTO,
        project_id: Optional[str] = None,
        parallel: bool = True,
        timeout: Optional[float] = None
    ) -> BatchResponse:
        """
        Process multiple prompts in batch.

        Args:
            prompts: List of prompt strings
            model: Model to use for all prompts
            project_id: Project ID (overrides default)
            parallel: Process in parallel (currently always True on server)
            timeout: Per-prompt timeout (overrides default)

        Returns:
            BatchResponse with results for all prompts

        Example:
            prompts = ["Hello", "Write a haiku", "Count to 5"]
            results = client.batch(prompts, model="haiku")

            for result in results.results:
                if result.status == "completed":
                    print(result.content)
                else:
                    print(f"Error: {result.error}")
        """
        # Prepare batch items
        batch_items = [
            {"prompt": prompt, "id": str(i)}
            for i, prompt in enumerate(prompts)
        ]

        # Prepare request data
        request_data = {
            "prompts": batch_items,
            "project_id": project_id or self.project_id
        }

        # Add model if not auto
        model_str = model.value if isinstance(model, Model) else model
        if model_str != "auto":
            request_data["model"] = model_str

        # Add timeout if specified
        if timeout:
            request_data["timeout"] = timeout

        # Make request
        response = self._request_with_retry(
            "POST",
            "/v1/batch",
            json=request_data
        )

        # Parse response
        data = response.json()
        results = [
            BatchResult(
                id=item["id"],
                prompt=item["prompt"],
                status=item["status"],
                content=item.get("content"),
                usage=Usage(**item["usage"]) if item.get("usage") else None,
                cost=item.get("cost"),
                error=item.get("error")
            )
            for item in data["results"]
        ]

        return BatchResponse(
            total=data["total"],
            completed=data["completed"],
            failed=data["failed"],
            results=results,
            total_cost=data["total_cost"],
            total_tokens=data["total_tokens"]
        )

    def get_usage(
        self,
        period: str = "month",
        project_id: Optional[str] = None
    ) -> UsageStats:
        """
        Get usage statistics for a project.

        Args:
            period: Time period (month, week, day)
            project_id: Project ID (overrides default)

        Returns:
            UsageStats with token counts, costs, and budget info

        Example:
            stats = client.get_usage(period="month")
            print(f"Total cost: ${stats.total_cost:.2f}")
            print(f"Tokens used: {stats.total_tokens:,}")
            print(f"Budget remaining: {stats.remaining:,} tokens")
        """
        response = self._request_with_retry(
            "GET",
            "/v1/usage",
            params={
                "project_id": project_id or self.project_id,
                "period": period
            }
        )

        data = response.json()
        return UsageStats(
            project_id=data["project_id"],
            period=data["period"],
            total_tokens=data["total_tokens"],
            total_cost=data["total_cost"],
            by_model=data["by_model"],
            limit=data.get("limit"),
            remaining=data.get("remaining")
        )

    def health(self) -> Dict[str, Any]:
        """
        Check API service health.

        Returns:
            Health status dictionary

        Example:
            health = client.health()
            print(f"Status: {health['status']}")
        """
        response = self._request_with_retry("GET", "/health")
        return response.json()


# ============================================================================
# Asynchronous Client
# ============================================================================

class AsyncClaudeClient:
    """
    Asynchronous client for Claude Code API Service.

    Example:
        async with AsyncClaudeClient() as client:
            response = await client.complete("Hello!")
            print(response.content)
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        api_key: Optional[str] = None,
        project_id: str = "default",
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize async Claude API client.

        Args:
            base_url: Base URL of the API service
            api_key: API key for authentication (future feature)
            project_id: Default project ID for budget tracking
            timeout: Default timeout for requests in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.project_id = project_id
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Create async HTTP client
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=timeout
        )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Close the async HTTP client."""
        await self.client.aclose()

    async def _request_with_retry(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> httpx.Response:
        """
        Make async HTTP request with automatic retries.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional arguments for httpx request

        Returns:
            HTTP response

        Raises:
            ClaudeAPIError: If request fails after all retries
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                response = await self.client.request(method, endpoint, **kwargs)

                # Handle specific status codes
                if response.status_code == 401:
                    raise AuthenticationError("Authentication failed")
                elif response.status_code == 429:
                    error_data = response.json()
                    if "Budget exceeded" in error_data.get("detail", ""):
                        raise BudgetExceededError(error_data["detail"])
                    else:
                        raise RateLimitError("Rate limit exceeded")
                elif response.status_code >= 500:
                    # Server error - retry
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay * (attempt + 1))
                        continue

                response.raise_for_status()
                return response

            except httpx.TimeoutException as e:
                last_error = TimeoutError(f"Request timed out: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue

            except httpx.RequestError as e:
                last_error = ClaudeAPIError(f"Request failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue

        raise last_error or ClaudeAPIError("Request failed after all retries")

    async def complete(
        self,
        prompt: str,
        model: Union[str, Model] = Model.AUTO,
        project_id: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> Response:
        """
        Asynchronously generate a completion for a single prompt.

        Args:
            prompt: Input prompt text
            model: Model to use (haiku, sonnet, opus, or auto)
            project_id: Project ID (overrides default)
            timeout: Request timeout (overrides default)

        Returns:
            Response object with completion and usage statistics

        Example:
            response = await client.complete("Write a haiku")
            print(response.content)
        """
        # Prepare request data
        request_data = {
            "messages": [{"role": "user", "content": prompt}],
            "project_id": project_id or self.project_id
        }

        # Add model if not auto
        model_str = model.value if isinstance(model, Model) else model
        if model_str != "auto":
            request_data["model"] = model_str

        # Add timeout if specified
        if timeout:
            request_data["timeout"] = timeout

        # Make request
        response = await self._request_with_retry(
            "POST",
            "/v1/chat/completions",
            json=request_data
        )

        # Parse response
        data = response.json()
        return Response(
            id=data["id"],
            model=data["model"],
            content=data["content"],
            usage=Usage(**data["usage"]),
            cost=data["cost"],
            project_id=data["project_id"]
        )

    async def stream(
        self,
        prompt: str,
        model: Union[str, Model] = Model.AUTO,
        project_id: Optional[str] = None
    ) -> AsyncIterator[str]:
        """
        Stream completion chunks asynchronously.

        Note: Streaming is not yet implemented in the API.
        This method falls back to complete() and yields the full response.

        Args:
            prompt: Input prompt text
            model: Model to use
            project_id: Project ID (overrides default)

        Yields:
            Content chunks

        Example:
            async for chunk in client.stream("Write a story"):
                print(chunk, end="", flush=True)
        """
        # TODO: Implement actual streaming when API supports it
        response = await self.complete(prompt, model, project_id)
        yield response.content

    async def batch(
        self,
        prompts: List[str],
        model: Union[str, Model] = Model.AUTO,
        project_id: Optional[str] = None,
        parallel: bool = True,
        timeout: Optional[float] = None
    ) -> BatchResponse:
        """
        Process multiple prompts in batch asynchronously.

        Args:
            prompts: List of prompt strings
            model: Model to use for all prompts
            project_id: Project ID (overrides default)
            parallel: Process in parallel (currently always True on server)
            timeout: Per-prompt timeout (overrides default)

        Returns:
            BatchResponse with results for all prompts

        Example:
            prompts = ["Hello", "Write a haiku", "Count to 5"]
            results = await client.batch(prompts)

            for result in results.results:
                print(result.content if result.status == "completed" else result.error)
        """
        # Prepare batch items
        batch_items = [
            {"prompt": prompt, "id": str(i)}
            for i, prompt in enumerate(prompts)
        ]

        # Prepare request data
        request_data = {
            "prompts": batch_items,
            "project_id": project_id or self.project_id
        }

        # Add model if not auto
        model_str = model.value if isinstance(model, Model) else model
        if model_str != "auto":
            request_data["model"] = model_str

        # Add timeout if specified
        if timeout:
            request_data["timeout"] = timeout

        # Make request
        response = await self._request_with_retry(
            "POST",
            "/v1/batch",
            json=request_data
        )

        # Parse response
        data = response.json()
        results = [
            BatchResult(
                id=item["id"],
                prompt=item["prompt"],
                status=item["status"],
                content=item.get("content"),
                usage=Usage(**item["usage"]) if item.get("usage") else None,
                cost=item.get("cost"),
                error=item.get("error")
            )
            for item in data["results"]
        ]

        return BatchResponse(
            total=data["total"],
            completed=data["completed"],
            failed=data["failed"],
            results=results,
            total_cost=data["total_cost"],
            total_tokens=data["total_tokens"]
        )

    async def get_usage(
        self,
        period: str = "month",
        project_id: Optional[str] = None
    ) -> UsageStats:
        """
        Get usage statistics for a project asynchronously.

        Args:
            period: Time period (month, week, day)
            project_id: Project ID (overrides default)

        Returns:
            UsageStats with token counts, costs, and budget info

        Example:
            stats = await client.get_usage(period="week")
            print(f"Weekly cost: ${stats.total_cost:.2f}")
        """
        response = await self._request_with_retry(
            "GET",
            "/v1/usage",
            params={
                "project_id": project_id or self.project_id,
                "period": period
            }
        )

        data = response.json()
        return UsageStats(
            project_id=data["project_id"],
            period=data["period"],
            total_tokens=data["total_tokens"],
            total_cost=data["total_cost"],
            by_model=data["by_model"],
            limit=data.get("limit"),
            remaining=data.get("remaining")
        )

    async def health(self) -> Dict[str, Any]:
        """
        Check API service health asynchronously.

        Returns:
            Health status dictionary

        Example:
            health = await client.health()
            print(f"Status: {health['status']}")
        """
        response = await self._request_with_retry("GET", "/health")
        return response.json()
