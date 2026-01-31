# Python Client Library

Complete reference for the Claude Code API Python client.

## Installation

The client library is included in the repository's `client/` directory:

```bash
# Clone repository
git clone https://github.com/TrentDevStuff/claude-code-api-service.git

# Install httpx dependency
pip install httpx
```

Then import in your code:

```python
import sys
sys.path.insert(0, '/path/to/claude-code-api-service')
from client import ClaudeClient
```

Or copy the `client/` directory to your project:

```bash
cp -r claude-code-api-service/client/ your-project/
```

## Quick Start

```python
from client import ClaudeClient

client = ClaudeClient(
    base_url="http://localhost:8006",
    api_key="YOUR_API_KEY"
)

# Simple completion
response = client.complete("What is Python?")
print(response.content)

# Agentic task
result = client.agentic_task(
    description="Count Python files in src/",
    allow_tools=["Bash", "Glob"]
)
print(f"Result: {result}")
```

## Client Initialization

### Basic

```python
from client import ClaudeClient

client = ClaudeClient(
    base_url="http://localhost:8006",
    api_key="YOUR_API_KEY"
)
```

### With Options

```python
client = ClaudeClient(
    base_url="http://localhost:8006",
    api_key="YOUR_API_KEY",
    timeout=300,
    max_retries=3,
    project_id="my-app"
)
```

### From Environment Variable

```python
import os
from client import ClaudeClient

client = ClaudeClient(
    base_url="http://localhost:8006",
    api_key=os.getenv("CLAUDE_API_KEY")
)
```

## Methods

### complete()

Simple text completion.

```python
response = client.complete(
    prompt="Explain quantum computing",
    model="sonnet",  # or "haiku", "opus", "auto"
    timeout=None     # Override default timeout
)

print(response.content)
print(f"Tokens: {response.usage.total_tokens}")
print(f"Cost: ${response.cost:.4f}")
```

**Parameters:**
- `prompt` (str): Input text
- `model` (str): Model to use (optional, defaults to "auto")
- `timeout` (float): Request timeout in seconds

**Returns:**
- `Response` with `content`, `usage`, and `cost` fields

### agentic_task()

Execute an agentic task with tools, agents, and skills.

```python
result = client.agentic_task(
    description="Analyze code for security issues",
    allow_tools=["Read", "Grep"],
    allow_agents=["security-auditor"],
    allow_skills=["semantic-text-matcher"],
    timeout=300,
    max_cost=1.0
)

print(f"Status: {result['status']}")
print(f"Summary: {result['result']['summary']}")
print(f"Cost: ${result['usage']['total_cost']:.4f}")

for artifact in result.get('artifacts', []):
    print(f"Generated: {artifact['path']}")
```

**Parameters:**
- `description` (str): Task description
- `allow_tools` (list): Tools to enable
- `allow_agents` (list): Agents to allow
- `allow_skills` (list): Skills to allow
- `timeout` (int): Task timeout in seconds
- `max_cost` (float): Maximum cost in USD

**Returns:**
- Dict with `status`, `result`, `artifacts`, `execution_log`, `usage`

### stream()

Stream completion chunks as they arrive.

```python
# Sync
for chunk in client.stream("Write a story"):
    print(chunk, end="", flush=True)

# Async
async for chunk in async_client.stream("Write a story"):
    print(chunk, end="", flush=True)
```

### batch()

Process multiple prompts in parallel.

```python
prompts = [
    "Write a haiku",
    "Count to 5",
    "List 3 colors"
]

results = client.batch(
    prompts=prompts,
    model="haiku",
    parallel=True
)

print(f"Completed: {results.completed}/{results.total}")
print(f"Total cost: ${results.total_cost:.4f}")

for result in results.results:
    if result.status == "completed":
        print(f"✓ {result.content}")
    else:
        print(f"✗ Error: {result.error}")
```

### get_usage()

Get usage statistics for a project.

```python
stats = client.get_usage(period="month")

print(f"Total tokens: {stats.total_tokens:,}")
print(f"Total cost: ${stats.total_cost:.2f}")

for model_name, model_stats in stats.by_model.items():
    print(f"{model_name}: {model_stats['tokens']:,} tokens")
```

### health()

Check API service health.

```python
health = client.health()
print(f"Status: {health['status']}")
print(f"Services: {health['services']}")
```

## Async Client

For async applications:

```python
from client import AsyncClaudeClient
import asyncio

async def main():
    async with AsyncClaudeClient(
        base_url="http://localhost:8006",
        api_key="YOUR_KEY"
    ) as client:
        # Async completion
        response = await client.complete("Hello")
        print(response.content)

        # Async task
        result = await client.agentic_task(
            description="Count files",
            allow_tools=["Bash"]
        )
        print(result['status'])

        # Async streaming
        async for chunk in client.stream("Write a poem"):
            print(chunk, end='', flush=True)

asyncio.run(main())
```

## Data Models

### Response

```python
response.id           # str: Unique task ID
response.model        # str: Model used
response.content      # str: Generated text
response.usage        # Usage object
  .input_tokens       # int
  .output_tokens      # int
  .total_tokens       # int
response.cost         # float: USD
```

### BatchResult

```python
result.id             # str: Prompt ID
result.prompt         # str: Original prompt
result.status         # str: "completed" or "failed"
result.content        # str: Generated text (if completed)
result.usage          # Usage (if completed)
result.cost           # float (if completed)
result.error          # str (if failed)
```

### BatchResponse

```python
results.total         # int: Total prompts
results.completed     # int: Successfully completed
results.failed        # int: Failed prompts
results.results       # List[BatchResult]
results.total_cost    # float: Total cost
results.total_tokens  # int: Total tokens
```

## Exceptions

```python
from client import (
    ClaudeAPIError,         # Base exception
    AuthenticationError,    # 401 - Invalid API key
    PermissionError,        # 403 - Tool/agent not allowed
    RateLimitError,         # 429 - Rate limit exceeded
    TimeoutError,           # Task timeout
    BudgetExceededError,    # Budget exceeded
)

try:
    response = client.complete("Test")
except AuthenticationError:
    print("Invalid API key - create one with: claude-api keys create")
except RateLimitError:
    print("Rate limited, retry later")
except PermissionError:
    print("Tool not allowed for your API key")
except BudgetExceededError:
    print("Budget exceeded")
except ClaudeAPIError as e:
    print(f"API error: {e}")
```

## Error Handling

```python
from client import ClaudeAPIError

try:
    result = client.agentic_task(
        description="...",
        max_cost=1.0
    )
except TimeoutError:
    print("Task timed out")
except PermissionError:
    print("Permission denied - upgrade API key tier")
except BudgetExceededError as e:
    print(f"Would cost ${e.estimated_cost}")
except ClaudeAPIError as e:
    print(f"API error: {e}")
```

## Advanced Usage

### With Retries

```python
import time
from client import RateLimitError

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

### Context Manager

```python
with ClaudeClient(base_url="http://localhost:8006", api_key="KEY") as client:
    response = client.complete("Hello")
    print(response.content)
# Client is automatically closed
```

### Multiple Projects

```python
with ClaudeClient(base_url="http://localhost:8006", api_key="KEY") as client:
    # Project A
    response_a = client.complete("Prompt for A", project_id="project-a")
    stats_a = client.get_usage(project_id="project-a")

    # Project B
    response_b = client.complete("Prompt for B", project_id="project-b")
    stats_b = client.get_usage(project_id="project-b")

    print(f"Project A cost: ${stats_a.total_cost:.2f}")
    print(f"Project B cost: ${stats_b.total_cost:.2f}")
```

## Configuration

### Environment Variables

```bash
export CLAUDE_API_KEY="cc_your_key_here"
export CLAUDE_API_URL="http://localhost:8006"
export CLAUDE_TIMEOUT="300"
```

### .env File

```python
from dotenv import load_dotenv
import os

load_dotenv()

client = ClaudeClient(
    base_url=os.getenv("CLAUDE_API_URL", "http://localhost:8006"),
    api_key=os.getenv("CLAUDE_API_KEY")
)
```

## Logging

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("client")
logger.setLevel(logging.DEBUG)

client = ClaudeClient(base_url="http://localhost:8006", api_key="KEY")
response = client.complete("Test")
```

## Performance Tips

1. **Use streaming for long tasks** - Get feedback faster
2. **Parallel execution** - Use `batch()` for independent tasks
3. **Set appropriate timeouts** - Don't wait forever
4. **Use budget limits** - Prevent runaway costs
5. **Use cheaper models** - Haiku for simple tasks
6. **Reuse client** - Don't create new instances per request

## Examples

### Analyze Python Files

```python
import glob

client = ClaudeClient(base_url="http://localhost:8006", api_key="KEY")

py_files = glob.glob("src/**/*.py", recursive=True)

for py_file in py_files[:3]:  # Limit to 3 files
    result = client.agentic_task(
        description=f"Find bugs in {py_file}",
        allow_tools=["Read"]
    )

    if result.get('result', {}).get('bugs'):
        print(f"{py_file}: issues found")
```

### Generate Documentation

```python
result = client.agentic_task(
    description="Generate API docs for src/api.py",
    allow_tools=["Read"]
)

for artifact in result.get('artifacts', []):
    if artifact['path'].endswith('.md'):
        print(f"Generated: {artifact['path']}")
```

### Stream Real-time Results

```python
for chunk in client.stream("Write a poem about coding"):
    print(chunk, end='', flush=True)
print()  # Newline at end
```

## Troubleshooting

### "Service not responding"

```bash
# Check if service is running
curl http://localhost:8006/health

# Start it
python main.py
# Or
claude-api service start --background
```

### "Invalid API key"

```bash
# List existing keys
claude-api keys list

# Create new key
claude-api keys create --project-id test --profile enterprise
```

### "Permission denied"

```bash
# Check key permissions
claude-api keys permissions YOUR_KEY

# Upgrade to enterprise
claude-api keys permissions YOUR_KEY --set-profile enterprise
```

### "Rate limit exceeded"

Wait 60 seconds or implement exponential backoff (see "With Retries" above).

## Requirements

- Python 3.8+
- httpx >= 0.26.0

## Support

- **CLI Help**: `claude-api --help`
- **Interactive Docs**: `http://localhost:8006/docs`
- **Issues**: https://github.com/TrentDevStuff/claude-code-api-service/issues
