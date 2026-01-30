# Wave 5: Complete Foundation & Integration

**Goal**: Integrate agentic capabilities with existing API, add Python client library, expand documentation

**Duration**: ~1 week
**Total Initiatives**: 3
**Complexity**: Medium (foundation exists, just needs integration)

---

## INIT-024: Integrate Agentic Executor with API

**Complexity**: Medium
**Model**: Sonnet
**Budget**: 20k tokens
**Duration**: 2 days
**Branch**: `feature/INIT-024-agentic-api-integration`

### Overview
Integrate the agentic executor (INIT-011) with the existing FastAPI application. Add the `/v1/task` endpoint, wire up permission validation, and enable agentic WebSocket streaming.

### Requirements

#### 1. Add `/v1/task` Endpoint

**Location**: `src/api.py`

Add new endpoint:
```python
@router.post("/task")
async def execute_agentic_task(
    request: AgenticTaskRequest,
    api_key: str = Depends(verify_api_key)
) -> AgenticTaskResponse:
    """
    Execute an agentic task with full Claude Code capabilities.

    Requires:
    - Valid API key with agentic permissions
    - Task description
    - Optional: allowed tools, agents, skills

    Returns:
    - Task results
    - Execution log
    - Generated artifacts
    - Usage statistics
    """
    # Validate permissions
    permission_validation = await permission_manager.validate_task_request(
        api_key=api_key,
        requested_tools=request.allow_tools,
        requested_agents=request.allow_agents,
        requested_skills=request.allow_skills
    )

    if not permission_validation.allowed:
        raise HTTPException(403, f"Permission denied: {permission_validation.reason}")

    # Execute task
    response = await agentic_executor.execute_task(request)

    return response
```

#### 2. Integrate Permission Manager with Auth

**Location**: `src/api.py`

Update API initialization to include permission checks:
```python
from src.permission_manager import PermissionManager
from src.agentic_executor import AgenticExecutor

# Initialize at startup
permission_manager = PermissionManager()
agentic_executor = AgenticExecutor(
    worker_pool=worker_pool,
    budget_manager=budget_manager,
    audit_logger=audit_logger
)
```

#### 3. Add Agentic WebSocket Streaming

**Location**: `src/websocket.py`

Add support for streaming agentic execution events:
```python
async def stream_agentic_task(
    self,
    websocket: WebSocket,
    request: AgenticTaskRequest
):
    """Stream agentic task execution in real-time."""
    await websocket.accept()

    try:
        # Stream events: thinking, tool_call, agent_spawn, skill_invoke, result
        async for event in self._execute_with_streaming(request):
            await websocket.send_json({
                "type": event.type,
                "content": event.content,
                "timestamp": event.timestamp
            })
    except WebSocketDisconnect:
        # Client disconnected
        pass
```

Event types:
- `thinking`: Claude's reasoning
- `tool_call`: Tool invocation (Read, Grep, Bash)
- `agent_spawn`: Agent launched
- `skill_invoke`: Skill called
- `result`: Final result + artifacts

#### 4. Update OpenAPI Schema

Add Pydantic models to FastAPI schema:
- `AgenticTaskRequest`
- `AgenticTaskResponse`
- `ExecutionLogEntry`
- `Artifact`

Update API docs with examples.

### Acceptance Criteria

- [ ] `/v1/task` endpoint works end-to-end
- [ ] Permission validation enforced
- [ ] Agentic WebSocket streaming functional
- [ ] OpenAPI schema updated
- [ ] Integration tests pass (test simple task, tool usage, agent spawning)
- [ ] Documentation updated

### Test Cases

**File**: `tests/test_agentic_api_integration.py`

```python
@pytest.mark.asyncio
async def test_agentic_task_endpoint():
    """Test /v1/task endpoint."""
    response = await client.post("/v1/task", json={
        "description": "Analyze src/api.py for issues",
        "allow_tools": ["Read", "Grep"],
        "timeout": 60
    }, headers={"Authorization": "Bearer test-key"})

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert "result" in data
    assert "execution_log" in data

@pytest.mark.asyncio
async def test_permission_denied():
    """Test that permission validation works."""
    response = await client.post("/v1/task", json={
        "description": "Test",
        "allow_agents": ["forbidden-agent"]
    }, headers={"Authorization": "Bearer limited-key"})

    assert response.status_code == 403
    assert "Permission denied" in response.json()["detail"]

@pytest.mark.asyncio
async def test_websocket_agentic_streaming():
    """Test WebSocket streaming of agentic events."""
    async with client.websocket_connect("/v1/stream") as ws:
        await ws.send_json({
            "type": "agentic_task",
            "description": "Simple test",
            "allow_tools": ["Read"]
        })

        events = []
        async for message in ws.iter_json():
            events.append(message["type"])
            if message["type"] == "result":
                break

        assert "thinking" in events
        assert "tool_call" in events
        assert "result" in events
```

### Documentation Updates

**File**: `docs/agentic-api.md` (new)

Include:
- How to use `/v1/task`
- Permission model explanation
- WebSocket streaming guide
- Example requests/responses
- Security best practices

### References

- Existing: `src/agentic_executor.py` (already implemented)
- Existing: `src/permission_manager.py` (already implemented)
- Existing: `src/api.py` (modify)
- Existing: `src/websocket.py` (modify)
- Plan: `EFFORT-Agentic-API-Architecture/PLAN-*.md`

---

## INIT-009: Python Client Library

**Complexity**: Medium
**Model**: Sonnet
**Budget**: 25k tokens
**Duration**: 3 days
**Branch**: `feature/INIT-009-python-client`

### Overview
Create a Python client library for the Claude Code API. Support both simple completions and agentic task execution. Include WebSocket streaming, async/await, type hints, and comprehensive error handling.

### Requirements

#### 1. Project Structure

```
client/
├── pyproject.toml          # Package metadata
├── README.md               # Client documentation
├── claude_code_client/
│   ├── __init__.py
│   ├── client.py           # Main ClaudeClient class
│   ├── models.py           # Pydantic models
│   ├── exceptions.py       # Custom exceptions
│   ├── streaming.py        # WebSocket streaming
│   └── async_client.py     # Async client variant
├── examples/
│   ├── simple_completion.py
│   ├── agentic_task.py
│   ├── streaming.py
│   └── async_example.py
└── tests/
    ├── test_client.py
    ├── test_streaming.py
    └── test_async_client.py
```

#### 2. Main Client Class

**File**: `claude_code_client/client.py`

```python
from typing import List, Optional, Iterator
from .models import CompletionRequest, CompletionResponse, AgenticTaskRequest, AgenticTaskResponse
from .streaming import StreamingClient
from .exceptions import ClaudeAPIError, AuthenticationError, RateLimitError

class ClaudeClient:
    """
    Python client for Claude Code API.

    Usage:
        client = ClaudeClient(api_key="sk-proj-...")

        # Simple completion
        response = client.complete("Explain async/await")
        print(response.content)

        # Agentic task
        result = client.execute_task(
            description="Analyze our API for security issues",
            allow_tools=["Read", "Grep"],
            allow_agents=["security-auditor"]
        )
        print(result.summary)
        for artifact in result.artifacts:
            print(f"Generated: {artifact.path}")
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "http://localhost:8000/v1",
        timeout: int = 300
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self._session = None

    def complete(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 1000
    ) -> CompletionResponse:
        """
        Simple text completion.

        Args:
            prompt: Input text
            model: Model to use (haiku/sonnet/opus), auto-selected if None
            max_tokens: Maximum tokens to generate

        Returns:
            CompletionResponse with generated text

        Raises:
            AuthenticationError: Invalid API key
            RateLimitError: Rate limit exceeded
            ClaudeAPIError: Other API errors
        """
        # Implementation
        pass

    def execute_task(
        self,
        description: str,
        allow_tools: List[str] = None,
        allow_agents: List[str] = None,
        allow_skills: List[str] = None,
        timeout: int = 300,
        max_cost: float = 1.0
    ) -> AgenticTaskResponse:
        """
        Execute an agentic task with Claude Code capabilities.

        Args:
            description: Natural language task description
            allow_tools: Tools to enable (Read, Grep, Bash, etc.)
            allow_agents: Agents to allow
            allow_skills: Skills to allow
            timeout: Task timeout in seconds
            max_cost: Maximum cost in USD

        Returns:
            AgenticTaskResponse with results, logs, artifacts

        Raises:
            AuthenticationError: Invalid API key
            PermissionError: Tools/agents not allowed for this API key
            TimeoutError: Task exceeded timeout
            ClaudeAPIError: Other errors
        """
        # Implementation
        pass

    def stream_task(
        self,
        description: str,
        **kwargs
    ) -> Iterator[dict]:
        """
        Stream agentic task execution events in real-time.

        Args:
            description: Task description
            **kwargs: Same as execute_task()

        Yields:
            Event dictionaries:
            - {"type": "thinking", "content": "..."}
            - {"type": "tool_call", "tool": "Read", "file": "..."}
            - {"type": "result", "summary": "...", "artifacts": [...]}

        Example:
            for event in client.stream_task("Analyze code"):
                if event["type"] == "thinking":
                    print(f"🤔 {event['content']}")
                elif event["type"] == "tool_call":
                    print(f"🔧 {event['tool']}")
                elif event["type"] == "result":
                    print(f"✅ {event['summary']}")
        """
        # Implementation using WebSocket
        pass
```

#### 3. Async Client

**File**: `claude_code_client/async_client.py`

Async variant with same API:
```python
class AsyncClaudeClient:
    async def complete(...) -> CompletionResponse:
        ...

    async def execute_task(...) -> AgenticTaskResponse:
        ...

    async def stream_task(...) -> AsyncIterator[dict]:
        ...
```

#### 4. Exception Hierarchy

**File**: `claude_code_client/exceptions.py`

```python
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
```

#### 5. Pydantic Models

**File**: `claude_code_client/models.py`

Mirror server-side models:
- `CompletionRequest`
- `CompletionResponse`
- `AgenticTaskRequest`
- `AgenticTaskResponse`
- `ExecutionLogEntry`
- `Artifact`

#### 6. Package Metadata

**File**: `pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "claude-code-client"
version = "0.1.0"
description = "Python client for Claude Code API"
readme = "README.md"
requires-python = ">=3.8"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "you@example.com"}
]
dependencies = [
    "httpx>=0.24.0",
    "pydantic>=2.0.0",
    "websockets>=11.0.0"
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "mypy>=1.0.0"
]

[project.urls]
Homepage = "https://github.com/yourusername/claude-code-client"
Documentation = "https://claude-code-client.readthedocs.io"
```

### Acceptance Criteria

- [ ] Simple completion works
- [ ] Agentic task execution works
- [ ] WebSocket streaming works
- [ ] Async client works
- [ ] Type hints on all public methods
- [ ] 90%+ test coverage
- [ ] Examples run successfully
- [ ] README with quickstart
- [ ] Can install via pip

### Test Cases

**File**: `tests/test_client.py`

```python
def test_simple_completion():
    client = ClaudeClient(api_key="test-key")
    response = client.complete("What is 2+2?")
    assert response.content is not None
    assert len(response.content) > 0

def test_agentic_task():
    client = ClaudeClient(api_key="test-key")
    result = client.execute_task(
        description="Analyze src/api.py",
        allow_tools=["Read"]
    )
    assert result.status == "completed"
    assert len(result.execution_log) > 0

def test_streaming():
    client = ClaudeClient(api_key="test-key")
    events = list(client.stream_task("Simple task"))
    assert len(events) > 0
    assert events[-1]["type"] == "result"

@pytest.mark.asyncio
async def test_async_client():
    client = AsyncClaudeClient(api_key="test-key")
    response = await client.complete("Test")
    assert response.content is not None
```

### Examples

**File**: `examples/simple_completion.py`

```python
from claude_code_client import ClaudeClient

client = ClaudeClient(api_key="sk-proj-your-key")

response = client.complete("Explain Python asyncio in 3 sentences")
print(response.content)
print(f"\nTokens: {response.usage.total_tokens}")
print(f"Cost: ${response.usage.cost:.4f}")
```

**File**: `examples/agentic_task.py`

```python
from claude_code_client import ClaudeClient

client = ClaudeClient(api_key="sk-proj-your-key")

result = client.execute_task(
    description="Analyze our API code for security vulnerabilities",
    allow_tools=["Read", "Grep"],
    allow_agents=["security-auditor"],
    timeout=300
)

print(f"Status: {result.status}")
print(f"Summary: {result.result['summary']}")
print(f"\nExecution Log:")
for entry in result.execution_log:
    print(f"  [{entry.timestamp}] {entry.action}: {entry.details}")

print(f"\nGenerated Artifacts:")
for artifact in result.artifacts:
    print(f"  - {artifact.path} ({artifact.size_bytes} bytes)")

print(f"\nCost: ${result.usage.total_cost:.4f}")
```

### References

- Server models: `src/agentic_executor.py`
- API endpoints: `src/api.py`
- WebSocket: `src/websocket.py`

---

## INIT-010: Documentation Expansion

**Complexity**: Low
**Model**: Haiku (documentation = simple task)
**Budget**: 15k tokens
**Duration**: 2 days
**Branch**: `feature/INIT-010-documentation`

### Overview
Expand documentation to cover the full API including agentic capabilities. Create comprehensive guides, examples, and deployment documentation.

### Requirements

#### 1. Documentation Structure

```
docs/
├── index.md                  # Landing page
├── quickstart.md             # 5-minute quickstart
├── api-reference/
│   ├── completions.md        # Simple completion API
│   ├── agentic-tasks.md      # Agentic task API
│   ├── websocket.md          # WebSocket streaming
│   └── authentication.md     # API keys & auth
├── guides/
│   ├── getting-started.md    # Detailed setup
│   ├── agentic-api-guide.md  # How to use agentic features
│   ├── security-best-practices.md
│   ├── permission-model.md   # Understanding permissions
│   └── error-handling.md     # How to handle errors
├── examples/
│   ├── code-analysis.md      # Example: Analyze code
│   ├── documentation-generation.md
│   ├── test-generation.md
│   └── multi-agent-workflow.md
├── deployment/
│   ├── docker-compose.md     # Deploy with Docker
│   ├── production.md         # Production deployment
│   └── monitoring.md         # Monitoring & observability
└── client-libraries/
    └── python.md             # Python client guide
```

#### 2. API Reference Documentation

Auto-generate from OpenAPI schema:
```bash
# Generate docs from FastAPI app
python -m mkdocs build
```

Include:
- All endpoints
- Request/response schemas
- Example requests
- Error codes
- Rate limits

#### 3. Agentic API Guide

**File**: `docs/guides/agentic-api-guide.md`

Cover:
- What is agentic task execution?
- When to use simple vs agentic API
- Available tools, agents, skills
- Permission tiers (Free/Pro/Enterprise)
- Cost considerations
- Example use cases

#### 4. Security Best Practices

**File**: `docs/guides/security-best-practices.md`

Cover:
- API key management (environment variables, never commit)
- Principle of least privilege (only allow needed tools/agents)
- Sandbox isolation model
- Audit logging
- Rate limiting
- Cost controls

#### 5. Example Use Cases

**File**: `docs/examples/code-analysis.md`

Full walkthrough:
```markdown
# Example: Automated Code Analysis

## Overview
Use the agentic API to analyze your codebase for security vulnerabilities.

## Prerequisites
- API key with `security-auditor` agent permission
- Tools: Read, Grep

## Step 1: Make the Request

\`\`\`python
from claude_code_client import ClaudeClient

client = ClaudeClient(api_key="sk-proj-...")

result = client.execute_task(
    description="Analyze our FastAPI application for security vulnerabilities",
    allow_tools=["Read", "Grep"],
    allow_agents=["security-auditor"],
    timeout=300,
    max_cost=1.00
)
\`\`\`

## Step 2: Review Results

[Full example with output]

## Step 3: Review Artifacts

[Explanation of generated reports]
```

Similar guides for:
- Documentation generation
- Test generation
- Multi-agent workflows

#### 6. Deployment Guide

**File**: `docs/deployment/docker-compose.md`

Full deployment setup:
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///data/api.db
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./data:/data
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

Include:
- Environment variables
- Volume mounts
- Health checks
- Logging configuration

### Acceptance Criteria

- [ ] All sections complete
- [ ] Code examples tested and working
- [ ] Screenshots/diagrams where helpful
- [ ] Search functionality works
- [ ] Mobile-friendly
- [ ] Can deploy docs to GitHub Pages

### Tech Stack

- **MkDocs** with Material theme
- Auto-generated OpenAPI docs
- Code syntax highlighting
- Search enabled

### Setup

```bash
cd docs/
pip install mkdocs mkdocs-material
mkdocs serve  # Preview at http://localhost:8001
mkdocs build  # Generate static site
```

### References

- Existing: `README_TOKEN_TRACKER.md` (good example)
- API: `src/api.py`
- Models: `src/agentic_executor.py`

---

## Wave 5 Execution Strategy

### Parallel Development
All 3 initiatives can run in parallel:
- **Worker 1** (Sonnet): INIT-024 (API integration)
- **Worker 2** (Sonnet): INIT-009 (Python client)
- **Worker 3** (Haiku): INIT-010 (Documentation)

### Timeline
- **Day 1-2**: INIT-024 (API integration)
- **Day 2-4**: INIT-009 (Python client)
- **Day 3-5**: INIT-010 (Documentation)
- **Day 6-7**: Integration testing + fixes

### Success Criteria
- [ ] `/v1/task` endpoint working
- [ ] Python client installable and working
- [ ] Complete documentation site
- [ ] All tests passing (210+ tests)
- [ ] Example scripts run successfully
- [ ] Can deploy full stack with Docker Compose

### Post-Wave 5 State
**Result**: Production-ready agentic API with Python client and comprehensive docs.

**Next**: Wave 6 (Alpha hardening) or start using the API!

---

## References

- **Status Assessment**: `STATUS-ASSESSMENT.md`
- **Full Roadmap**: `WAVES-5-7-PLAN.md`
- **Wave 4 Results**: `.claude/initiatives.json`
- **Implementation Plan**: `EFFORT-Agentic-API-Architecture/PLAN-*.md`
