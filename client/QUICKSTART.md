# Quick Start Guide - Claude API Client

## 30-Second Start

```python
from client import ClaudeClient

with ClaudeClient(base_url="http://localhost:8080") as client:
    response = client.complete("Hello, Claude!")
    print(response.content)
```

## Installation

```bash
pip install httpx>=0.26.0
```

## Common Use Cases

### 1. Simple Completion

```python
from client import ClaudeClient

with ClaudeClient() as client:
    response = client.complete("Write a haiku about Python")
    print(response.content)
    print(f"Cost: ${response.cost:.4f}")
```

### 2. Choose a Model

```python
from client import ClaudeClient, Model

with ClaudeClient() as client:
    # Fast and cheap
    response = client.complete("Hello", model=Model.HAIKU)

    # Balanced
    response = client.complete("Explain async", model=Model.SONNET)

    # Most capable
    response = client.complete("Design a system", model=Model.OPUS)

    # Automatic (recommended)
    response = client.complete("Your task", model=Model.AUTO)
```

### 3. Batch Processing

```python
with ClaudeClient() as client:
    prompts = ["What is Python?", "What is Rust?", "What is Go?"]
    results = client.batch(prompts, model=Model.HAIKU)

    for result in results.results:
        print(result.content)
```

### 4. Check Usage

```python
with ClaudeClient(project_id="my-app") as client:
    stats = client.get_usage(period="month")
    print(f"Tokens: {stats.total_tokens:,}")
    print(f"Cost: ${stats.total_cost:.2f}")
    print(f"Remaining: {stats.remaining:,}")
```

### 5. Error Handling

```python
from client import ClaudeClient, BudgetExceededError, TimeoutError

with ClaudeClient() as client:
    try:
        response = client.complete("Your prompt")
    except BudgetExceededError:
        print("Budget exceeded - use cheaper model")
        response = client.complete("Your prompt", model=Model.HAIKU)
    except TimeoutError:
        print("Timed out - increase timeout")
        response = client.complete("Your prompt", timeout=60.0)
```

### 6. Async Operations

```python
import asyncio
from client import AsyncClaudeClient

async def main():
    async with AsyncClaudeClient() as client:
        response = await client.complete("Hello!")
        print(response.content)

asyncio.run(main())
```

## Response Object

```python
response = client.complete("Hello")

# Available attributes:
response.id          # Task ID
response.model       # Model used (haiku, sonnet, opus)
response.content     # Generated text
response.usage       # Usage(input_tokens, output_tokens, total_tokens)
response.cost        # Cost in USD
response.project_id  # Project ID
```

## Configuration

```python
client = ClaudeClient(
    base_url="http://localhost:8080",  # API URL
    project_id="my-project",            # Project for billing
    timeout=30.0,                       # Timeout in seconds
    max_retries=3,                      # Retry attempts
    retry_delay=1.0                     # Delay between retries
)
```

## Next Steps

- **Full Documentation**: `client/README.md`
- **Examples**: `examples/client_usage.py`
- **API Reference**: `docs/CLIENT_LIBRARY.md`
- **Tests**: `tests/test_client.py`

## Troubleshooting

**"Connection refused"**
- Start API service: `python main.py`

**"Module not found"**
- Add to path: `sys.path.append('/path/to/claude-code-api-service')`

**"httpx not installed"**
- Install: `pip install httpx>=0.26.0`

**Need help?**
- See full documentation in `client/README.md`
- Check examples in `examples/`
