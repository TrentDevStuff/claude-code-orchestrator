# Python Client Library

Complete reference for the Claude Code Python client.

## Installation

```bash
pip install claude-code-client
```

## Quick Start

```python
from claude_code_client import ClaudeClient

client = ClaudeClient(api_key="sk-proj-your-key")

# Simple completion
response = client.complete("What is Python?")
print(response.content)

# Agentic task
result = client.execute_task(
    description="Count Python files in src/",
    allow_tools=["Bash"]
)
print(f"Result: {result.result}")
```

## Client Initialization

### Basic

```python
from claude_code_client import ClaudeClient

client = ClaudeClient(api_key="sk-proj-your-key")
```

### With Options

```python
client = ClaudeClient(
    api_key="sk-proj-your-key",
    base_url="https://api.claude.ai/v1",
    timeout=300,
    max_retries=3
)
```

### From Environment Variable

```python
import os
from claude_code_client import ClaudeClient

api_key = os.getenv("CLAUDE_API_KEY")
client = ClaudeClient(api_key=api_key)
```

## Methods

### complete()

Simple text completion.

```python
response = client.complete(
    prompt="Explain quantum computing",
    model="sonnet",  # or "haiku", "opus"
    max_tokens=500,
    temperature=0.7,
    top_p=1.0
)

print(response.content)
print(f"Tokens: {response.usage.total_tokens}")
print(f"Cost: ${response.usage.cost:.4f}")
```

**Parameters:**
- `prompt` (str): Input text
- `model` (str): Model to use (optional, auto-selected)
- `max_tokens` (int): Max output tokens
- `temperature` (float): Randomness (0-2)
- `top_p` (float): Nucleus sampling (0-1)

**Returns:**
- `CompletionResponse` with `content` and `usage` fields

### execute_task()

Execute an agentic task.

```python
result = client.execute_task(
    description="Analyze code for security issues",
    allow_tools=["Read", "Grep"],
    allow_agents=["security-auditor"],
    allow_skills=["semantic-text-matcher"],
    timeout=300,
    max_cost=1.0,
    context={"project": "myapp"}
)

print(f"Status: {result.status}")
print(f"Summary: {result.result['summary']}")
print(f"Cost: ${result.usage.total_cost:.4f}")

for artifact in result.artifacts:
    print(f"Generated: {artifact.path}")
```

**Parameters:**
- `description` (str): Task description
- `allow_tools` (list): Tools to enable
- `allow_agents` (list): Agents to spawn
- `allow_skills` (list): Skills to invoke
- `timeout` (int): Task timeout in seconds
- `max_cost` (float): Maximum cost in USD
- `context` (dict): Additional context

**Returns:**
- `AgenticTaskResponse` with `status`, `result`, `artifacts`, `execution_log`, `usage`

### stream_task()

Stream task execution in real-time.

```python
for event in client.stream_task("Analyze code"):
    if event["type"] == "thinking":
        print(f"🤔 {event['content']}")
    elif event["type"] == "tool_call":
        print(f"🔧 {event['tool']}")
    elif event["type"] == "result":
        print(f"✅ Done: {event['summary']}")
```

**Yields:**
- Event dictionaries with `type`, `content`, `timestamp`

**Event types:**
- `thinking` - Internal reasoning
- `tool_call` - Tool invocation
- `tool_result` - Tool output
- `agent_spawn` - Agent spawned
- `skill_invoke` - Skill called
- `result` - Final result

## Async Client

For async applications:

```python
from claude_code_client import AsyncClaudeClient
import asyncio

async def main():
    client = AsyncClaudeClient(api_key="sk-proj-your-key")

    # Async completion
    response = await client.complete("Hello")
    print(response.content)

    # Async task
    result = await client.execute_task(
        description="Count files",
        allow_tools=["Bash"]
    )
    print(result.status)

    # Async streaming
    async for event in client.stream_task("Analyze"):
        if event["type"] == "result":
            print(event['summary'])
            break

asyncio.run(main())
```

## Data Models

### CompletionResponse

```python
from claude_code_client.models import CompletionResponse

response.content      # str: Generated text
response.model        # str: Model used
response.stop_reason  # str: Why it stopped
response.usage        # Usage object
  .input_tokens       # int
  .output_tokens      # int
  .total_tokens       # int
  .cost               # float: USD
```

### AgenticTaskResponse

```python
from claude_code_client.models import AgenticTaskResponse

result.id             # str: Task ID
result.status         # str: "completed", "failed", "timeout"
result.result         # dict: Task results
result.execution_log  # list: Action log
result.artifacts      # list: Generated files
  [0].type            # str: "file", "text", etc
  [0].path            # str: File path
  [0].size_bytes      # int
  [0].created_at      # str: ISO timestamp
result.usage          # Usage: tokens and cost
result.created_at     # str: ISO timestamp
result.completed_at   # str: ISO timestamp
```

### Exceptions

```python
from claude_code_client import (
    ClaudeAPIError,         # Base exception
    AuthenticationError,    # 401
    PermissionError,       # 403
    RateLimitError,        # 429
    TimeoutError,          # Task timeout
    CostExceededError,     # Budget exceeded
)

try:
    response = client.complete("Test")
except AuthenticationError:
    print("Invalid API key")
except RateLimitError:
    print("Rate limited, retry later")
except ClaudeAPIError as e:
    print(f"Error: {e}")
```

## Error Handling

```python
from claude_code_client import ClaudeAPIError

try:
    result = client.execute_task(
        description="...",
        max_cost=1.0
    )
except TimeoutError:
    print("Task timed out")
except PermissionError:
    print("Permission denied - upgrade tier")
except CostExceededError as e:
    print(f"Would cost ${e.estimated_cost}")
except ClaudeAPIError as e:
    print(f"API error: {e.status_code} - {e}")
```

## Advanced Usage

### With Retries

```python
import time
from claude_code_client import RateLimitError

def execute_with_retries(fn, max_retries=3):
    for attempt in range(max_retries):
        try:
            return fn()
        except RateLimitError:
            if attempt == max_retries - 1:
                raise
            wait = 2 ** attempt
            print(f"Rate limited, waiting {wait}s")
            time.sleep(wait)

response = execute_with_retries(
    lambda: client.complete("Test")
)
```

### Batch Operations

```python
import concurrent.futures

tasks = [
    "Analyze api.py",
    "Analyze models.py",
    "Analyze database.py"
]

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(
        lambda desc: client.execute_task(description=desc),
        tasks
    ))

for result in results:
    print(f"{result.id}: {result.status}")
```

### Context Management

```python
from contextlib import contextmanager

@contextmanager
def tracked_task(description):
    """Context manager for task tracking."""
    print(f"Starting: {description}")
    result = client.execute_task(description=description)
    try:
        yield result
    finally:
        print(f"Completed: {result.status}, Cost: ${result.usage.total_cost}")

with tracked_task("Analyze code") as result:
    print(result.result['summary'])
```

### Custom Middleware

```python
class MetricsMiddleware:
    def __init__(self, client):
        self.client = client
        self.total_cost = 0
        self.total_tokens = 0

    def execute_task(self, **kwargs):
        result = self.client.execute_task(**kwargs)
        self.total_cost += result.usage.total_cost
        self.total_tokens += result.usage.total_tokens
        return result

    def get_stats(self):
        return {
            "total_cost": self.total_cost,
            "total_tokens": self.total_tokens,
            "avg_cost_per_task": self.total_cost / (self.total_tokens or 1)
        }

middleware = MetricsMiddleware(client)
result = middleware.execute_task(description="Test")
print(middleware.get_stats())
```

## Configuration

### Environment Variables

```bash
export CLAUDE_API_KEY="sk-proj-..."
export CLAUDE_BASE_URL="https://api.claude.ai/v1"
export CLAUDE_TIMEOUT="300"
```

### .env File

```python
from dotenv import load_dotenv
import os

load_dotenv()

client = ClaudeClient(
    api_key=os.getenv("CLAUDE_API_KEY")
)
```

## Logging

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("claude_code_client")
logger.setLevel(logging.DEBUG)

# Use client
client = ClaudeClient(api_key="...")
response = client.complete("Test")
```

## Performance Tips

1. **Use streaming for long tasks** - Get feedback faster
2. **Parallel execution** - Run independent tasks together
3. **Set appropriate timeouts** - Don't wait forever
4. **Use budget limits** - Prevent runaway costs
5. **Cache results** - Don't re-analyze same code
6. **Batch similar tasks** - Reduce overhead
7. **Use cheaper models** - Haiku for simple tasks
8. **Reuse client** - Don't create new instances

## Examples

### Analyze Python Files

```python
import glob

client = ClaudeClient()

py_files = glob.glob("src/**/*.py", recursive=True)

for py_file in py_files[:3]:  # Limit to 3 files
    result = client.execute_task(
        description=f"Find bugs in {py_file}",
        allow_tools=["Read"],
        allow_agents=["code-analyzer"]
    )

    if result.result.get('bugs'):
        print(f"{py_file}: {len(result.result['bugs'])} issues found")
```

### Generate Documentation

```python
result = client.execute_task(
    description="Generate API docs for src/api.py",
    allow_tools=["Read"],
    allow_agents=["documentation-generator"]
)

for artifact in result.artifacts:
    if artifact.path.endswith('.md'):
        with open(artifact.path, 'r') as f:
            print(f.read())
```

### Stream Real-time Results

```python
for event in client.stream_task("Analyze code"):
    if event["type"] == "thinking":
        print(f"Thinking: {event['content'][:80]}...")
    elif event["type"] == "tool_call":
        print(f"Calling tool: {event['tool']}")
    elif event["type"] == "result":
        print(f"Done! Summary: {event['summary']}")
        break
```

## Troubleshooting

### "Invalid API key"

- Check `CLAUDE_API_KEY` environment variable
- Verify key at https://claude.ai/api/keys
- Key should start with `sk-proj-`

### "Rate limit exceeded"

- Wait 60 seconds
- Implement exponential backoff
- Upgrade to Pro tier

### "Permission denied"

- Upgrade API key tier
- Request specific tools in dashboard
- Check key permissions

## Support

- **Docs**: https://claude.ai/docs
- **Issues**: https://github.com/anthropics/claude-code-api
- **Email**: support@claude.ai
