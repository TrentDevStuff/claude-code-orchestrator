# Claude Code API Client

A simple, elegant Python client library for interacting with the Claude Code API Service.

## Features

- **Synchronous and Async Support**: Use `ClaudeClient` for sync operations or `AsyncClaudeClient` for async workflows
- **Automatic Retries**: Configurable retry logic with exponential backoff (default: 3 attempts)
- **Type Hints**: Full type hints throughout for better IDE support
- **Error Handling**: Comprehensive exception hierarchy for different error types
- **Batch Processing**: Process multiple prompts in parallel
- **Usage Tracking**: Monitor token usage and costs
- **Context Managers**: Clean resource management with context managers

## Installation

```bash
# Install httpx (required dependency)
pip install httpx
```

Then add the client directory to your Python path or copy it to your project.

## Quick Start

### Synchronous Usage

```python
from client import ClaudeClient

# Create client
with ClaudeClient(base_url="http://localhost:8080") as client:
    # Simple completion
    response = client.complete("Write a haiku about Python")
    print(response.content)
    print(f"Cost: ${response.cost:.4f}")
```

### Asynchronous Usage

```python
import asyncio
from client import AsyncClaudeClient

async def main():
    async with AsyncClaudeClient(base_url="http://localhost:8080") as client:
        # Simple completion
        response = await client.complete("Write a haiku about Python")
        print(response.content)

asyncio.run(main())
```

## API Reference

### ClaudeClient / AsyncClaudeClient

#### Constructor

```python
client = ClaudeClient(
    base_url="http://localhost:8080",  # API service URL
    api_key=None,                       # API key (future feature)
    project_id="default",               # Default project for billing
    timeout=30.0,                       # Request timeout in seconds
    max_retries=3,                      # Maximum retry attempts
    retry_delay=1.0                     # Delay between retries
)
```

#### Methods

##### complete()

Generate a completion for a single prompt.

```python
response = client.complete(
    prompt="Your prompt here",
    model="auto",              # "auto", "haiku", "sonnet", or "opus"
    project_id=None,           # Override default project
    timeout=None               # Override default timeout
)

# Response fields
print(response.id)          # Unique task ID
print(response.model)       # Model used
print(response.content)     # Generated text
print(response.usage)       # Token usage stats
print(response.cost)        # Cost in USD
```

##### stream()

Stream completion chunks as they arrive (falls back to complete until API supports streaming).

```python
# Sync
for chunk in client.stream("Write a story"):
    print(chunk, end="", flush=True)

# Async
async for chunk in client.stream("Write a story"):
    print(chunk, end="", flush=True)
```

##### batch()

Process multiple prompts in parallel.

```python
prompts = [
    "Write a haiku",
    "Count to 5",
    "List 3 colors"
]

results = client.batch(
    prompts=prompts,
    model="haiku",             # Model for all prompts
    project_id=None,           # Override default project
    parallel=True,             # Process in parallel (default)
    timeout=None               # Per-prompt timeout
)

# Results
print(f"Completed: {results.completed}/{results.total}")
print(f"Total cost: ${results.total_cost:.4f}")

for result in results.results:
    if result.status == "completed":
        print(f"✓ {result.content}")
    else:
        print(f"✗ Error: {result.error}")
```

##### get_usage()

Get usage statistics for a project.

```python
stats = client.get_usage(
    period="month",            # "month", "week", or "day"
    project_id=None            # Override default project
)

print(f"Total tokens: {stats.total_tokens:,}")
print(f"Total cost: ${stats.total_cost:.2f}")
print(f"Remaining budget: {stats.remaining:,} tokens")

# Per-model breakdown
for model_name, model_stats in stats.by_model.items():
    print(f"{model_name}: {model_stats['tokens']:,} tokens, ${model_stats['cost']:.2f}")
```

##### health()

Check API service health.

```python
health = client.health()
print(f"Status: {health['status']}")
print(f"Services: {health['services']}")
```

## Model Selection

The client supports automatic model selection based on prompt complexity and budget:

```python
from client import Model

# Explicit model selection
response = client.complete("Hello", model=Model.HAIKU)
response = client.complete("Analyze this code", model=Model.SONNET)
response = client.complete("Complex architecture", model=Model.OPUS)

# Automatic selection (default)
response = client.complete("Your prompt", model=Model.AUTO)
```

## Error Handling

The client provides specific exceptions for different error types:

```python
from client import (
    ClaudeAPIError,
    AuthenticationError,
    BudgetExceededError,
    TimeoutError,
    RateLimitError
)

try:
    response = client.complete("Hello")
except BudgetExceededError:
    print("Project budget exceeded")
except TimeoutError:
    print("Request timed out")
except RateLimitError:
    print("Rate limit exceeded")
except AuthenticationError:
    print("Authentication failed")
except ClaudeAPIError as e:
    print(f"API error: {e}")
```

## Advanced Examples

### Batch Processing with Error Handling

```python
prompts = ["Prompt 1", "Prompt 2", "Prompt 3"]
results = client.batch(prompts, model="haiku")

successful = [r for r in results.results if r.status == "completed"]
failed = [r for r in results.results if r.status == "failed"]

print(f"Success rate: {len(successful)}/{results.total}")
print(f"Total cost: ${results.total_cost:.4f}")

for result in failed:
    print(f"Failed prompt: {result.prompt}")
    print(f"Error: {result.error}")
```

### Usage Monitoring

```python
# Check usage before making requests
stats = client.get_usage(period="month")

if stats.remaining and stats.remaining < 1000:
    print("Warning: Low budget remaining")
    # Use cheaper model
    response = client.complete("Your prompt", model="haiku")
else:
    # Use default model selection
    response = client.complete("Your prompt")
```

### Async Batch Processing

```python
import asyncio
from client import AsyncClaudeClient

async def process_prompts():
    async with AsyncClaudeClient() as client:
        prompts = ["Prompt 1", "Prompt 2", "Prompt 3"]
        results = await client.batch(prompts)

        print(f"Processed {results.completed}/{results.total} prompts")
        print(f"Total tokens: {results.total_tokens:,}")

        return results

results = asyncio.run(process_prompts())
```

### Custom Retry Logic

```python
# Configure retries
client = ClaudeClient(
    base_url="http://localhost:8080",
    max_retries=5,      # Try up to 5 times
    retry_delay=2.0     # Wait 2 seconds between retries
)

response = client.complete("Your prompt")
```

### Multiple Projects

```python
# Track usage across multiple projects
with ClaudeClient() as client:
    # Project A
    response_a = client.complete("Prompt for A", project_id="project-a")
    stats_a = client.get_usage(project_id="project-a")

    # Project B
    response_b = client.complete("Prompt for B", project_id="project-b")
    stats_b = client.get_usage(project_id="project-b")

    print(f"Project A cost: ${stats_a.total_cost:.2f}")
    print(f"Project B cost: ${stats_b.total_cost:.2f}")
```

## Testing

```python
# Check if service is running
try:
    health = client.health()
    if health["status"] == "ok":
        print("Service is healthy")
except Exception as e:
    print(f"Service unavailable: {e}")
```

## Data Models

### Response

```python
@dataclass
class Response:
    id: str                  # Unique task ID
    model: str              # Model used
    content: str            # Generated text
    usage: Usage            # Token usage
    cost: float             # Cost in USD
    project_id: str         # Project ID
```

### Usage

```python
@dataclass
class Usage:
    input_tokens: int       # Input tokens
    output_tokens: int      # Output tokens
    total_tokens: int       # Total tokens
```

### BatchResult

```python
@dataclass
class BatchResult:
    id: Optional[str]       # Prompt ID
    prompt: str             # Original prompt
    status: str             # "completed" or "failed"
    content: Optional[str]  # Generated text (if completed)
    usage: Optional[Usage]  # Token usage (if completed)
    cost: Optional[float]   # Cost (if completed)
    error: Optional[str]    # Error message (if failed)
```

### BatchResponse

```python
@dataclass
class BatchResponse:
    total: int              # Total prompts
    completed: int          # Successfully completed
    failed: int             # Failed prompts
    results: List[BatchResult]  # Individual results
    total_cost: float       # Total cost in USD
    total_tokens: int       # Total tokens used
```

### UsageStats

```python
@dataclass
class UsageStats:
    project_id: str         # Project ID
    period: str             # Time period
    total_tokens: int       # Total tokens used
    total_cost: float       # Total cost in USD
    by_model: Dict[str, Dict[str, Union[int, float]]]  # Per-model stats
    limit: Optional[int]    # Budget limit (if set)
    remaining: Optional[int]  # Remaining budget (if set)
```

## Requirements

- Python 3.8+
- httpx >= 0.26.0

## License

MIT
