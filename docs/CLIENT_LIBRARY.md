# Client Library - Claude Code API Service

The Python client library provides a clean, type-safe interface for interacting with the Claude Code API Service.

## Installation

The client library is included in the repository:

```python
# Add to your Python path or install locally
import sys
sys.path.append('/path/to/claude-code-api-service')

from client.claude_client import ClaudeClient, AsyncClaudeClient
```

Or copy `client/claude_client.py` to your project.

### Dependencies

```bash
pip install httpx  # For HTTP requests
```

## Quick Start

### Synchronous Client

```python
from client.claude_client import ClaudeClient

# Create client
client = ClaudeClient(
    base_url="http://localhost:8080",
    project_id="my-app"
)

# Simple completion
response = client.complete("What is Python?")
print(response.content)
print(f"Cost: ${response.cost:.6f}")

# Always close the client
client.close()
```

### With Context Manager (Recommended)

```python
from client.claude_client import ClaudeClient

with ClaudeClient(project_id="my-app") as client:
    response = client.complete("Explain FastAPI in one sentence")
    print(response.content)

# Client automatically closed
```

### Async Client

```python
import asyncio
from client.claude_client import AsyncClaudeClient

async def main():
    async with AsyncClaudeClient(project_id="my-app") as client:
        response = await client.complete("What is async programming?")
        print(response.content)

asyncio.run(main())
```

## Core Features

### 1. Chat Completions

```python
from client.claude_client import ClaudeClient, Model

with ClaudeClient(project_id="demo") as client:
    # Auto model selection
    response = client.complete("Write a haiku about Python")

    # Explicit model
    response = client.complete(
        "List all Python built-in functions",
        model=Model.HAIKU  # Fast, cheap
    )

    # Complex task
    response = client.complete(
        "Analyze this codebase architecture and suggest improvements",
        model=Model.SONNET  # More capable
    )

    print(response.content)
    print(f"Model: {response.model}")
    print(f"Tokens: {response.usage.total_tokens}")
    print(f"Cost: ${response.cost:.6f}")
```

### 2. Batch Processing

```python
with ClaudeClient() as client:
    prompts = [
        "What is Python?",
        "What is Rust?",
        "What is Go?",
        "What is JavaScript?"
    ]

    # Process all in parallel
    batch_response = client.batch(prompts, model=Model.HAIKU)

    print(f"Completed: {batch_response.completed}/{batch_response.total}")
    print(f"Total cost: ${batch_response.total_cost:.4f}")

    # Process results
    for result in batch_response.results:
        if result.status == "completed":
            print(f"\\n{result.prompt}:")
            print(result.content)
        else:
            print(f"\\nFailed: {result.error}")
```

### 3. Usage Tracking

```python
with ClaudeClient(project_id="my-app") as client:
    # Get usage statistics
    stats = client.get_usage(period="month")

    print(f"Project: {stats.project_id}")
    print(f"Total tokens: {stats.total_tokens:,}")
    print(f"Total cost: ${stats.total_cost:.2f}")

    # Budget information
    if stats.limit:
        usage_pct = (stats.total_tokens / stats.limit) * 100
        print(f"Budget: {usage_pct:.1f}% used")
        print(f"Remaining: {stats.remaining:,} tokens")

    # Usage by model
    print("\\nBy model:")
    for model_name, model_stats in stats.by_model.items():
        print(f"  {model_name}: {model_stats['tokens']:,} tokens, ${model_stats['cost']:.4f}")
```

### 4. Health Checks

```python
with ClaudeClient() as client:
    health = client.health()

    print(f"Status: {health['status']}")
    print(f"Version: {health['version']}")
    print(f"Services: {health['services']}")
```

## Async Examples

### Concurrent Requests

```python
import asyncio
from client.claude_client import AsyncClaudeClient

async def ask_question(client, question):
    """Ask a single question"""
    response = await client.complete(question)
    return response.content

async def main():
    async with AsyncClaudeClient(project_id="demo") as client:
        # Ask multiple questions concurrently
        questions = [
            "What is Python?",
            "What is Rust?",
            "What is Go?"
        ]

        # Run all requests concurrently
        tasks = [ask_question(client, q) for q in questions]
        results = await asyncio.gather(*tasks)

        for question, answer in zip(questions, results):
            print(f"\\nQ: {question}")
            print(f"A: {answer}")

asyncio.run(main())
```

### Async Batch Processing

```python
import asyncio
from client.claude_client import AsyncClaudeClient

async def process_documents():
    async with AsyncClaudeClient(project_id="doc-processor") as client:
        documents = [
            "Summarize document 1...",
            "Summarize document 2...",
            "Summarize document 3..."
        ]

        batch_response = await client.batch(documents, model="haiku")

        for result in batch_response.results:
            if result.status == "completed":
                print(f"Summary: {result.content}")

asyncio.run(process_documents())
```

### Streaming (Future Feature)

```python
import asyncio
from client.claude_client import AsyncClaudeClient

async def stream_story():
    async with AsyncClaudeClient() as client:
        # Note: Streaming not yet implemented, falls back to complete()
        async for chunk in client.stream("Write a short story"):
            print(chunk, end="", flush=True)

asyncio.run(stream_story())
```

## Error Handling

### Budget Exceeded

```python
from client.claude_client import ClaudeClient, BudgetExceededError

with ClaudeClient(project_id="limited-budget") as client:
    try:
        response = client.complete("Analyze this large codebase...")
    except BudgetExceededError as e:
        print(f"Budget exceeded: {e.message}")
        # Switch to cheaper model or wait until next month
```

### Timeout Errors

```python
from client.claude_client import ClaudeClient, TimeoutError

with ClaudeClient() as client:
    try:
        response = client.complete(
            "Very complex task...",
            timeout=60.0  # 60 second timeout
        )
    except TimeoutError as e:
        print(f"Request timed out: {e}")
        # Retry with longer timeout or simpler prompt
```

### Rate Limiting

```python
from client.claude_client import ClaudeClient, RateLimitError
import time

with ClaudeClient() as client:
    try:
        response = client.complete("Question")
    except RateLimitError as e:
        print("Rate limited, waiting...")
        time.sleep(5)
        # Retry
        response = client.complete("Question")
```

### General Error Handling

```python
from client.claude_client import ClaudeClient, ClaudeAPIError

with ClaudeClient() as client:
    try:
        response = client.complete("Question")
    except BudgetExceededError:
        print("Budget exceeded - use cheaper model")
    except TimeoutError:
        print("Request timed out - try shorter prompt")
    except RateLimitError:
        print("Rate limited - wait and retry")
    except ClaudeAPIError as e:
        print(f"API error: {e.status_code} - {e.message}")
    except Exception as e:
        print(f"Unexpected error: {e}")
```

## Advanced Usage

### Automatic Retries

The client automatically retries failed requests:

```python
client = ClaudeClient(
    base_url="http://localhost:8080",
    max_retries=5,       # Retry up to 5 times
    retry_delay=2.0      # Wait 2 seconds between retries
)
```

Retry behavior:
- **Server errors (500+)**: Automatic retry with exponential backoff
- **Timeout errors**: Automatic retry
- **Client errors (4xx)**: No retry (except rate limits)

### Custom Timeouts

```python
with ClaudeClient() as client:
    # Short timeout for simple tasks
    response = client.complete(
        "Count to 10",
        timeout=5.0
    )

    # Long timeout for complex tasks
    response = client.complete(
        "Analyze this 100k line codebase",
        timeout=300.0  # 5 minutes
    )
```

### Multiple Projects

```python
with ClaudeClient() as client:
    # Override project_id per request
    chatbot_response = client.complete(
        "Hello!",
        project_id="chatbot"
    )

    analyzer_response = client.complete(
        "Analyze code",
        project_id="code-analyzer"
    )

    # Each project has separate budget
```

### Model Selection Strategy

```python
from client.claude_client import ClaudeClient, Model

with ClaudeClient() as client:
    # Simple tasks → Haiku (cheap, fast)
    client.complete("List Python keywords", model=Model.HAIKU)

    # Medium complexity → Sonnet (balanced)
    client.complete("Explain async/await", model=Model.SONNET)

    # Complex reasoning → Opus (most capable)
    client.complete("Design a distributed system", model=Model.OPUS)

    # Auto-selection → Let API choose (recommended)
    client.complete("Your task", model=Model.AUTO)
```

## Best Practices

### 1. Use Context Managers

Always use `with` statements to ensure proper cleanup:

```python
# ✅ Good
with ClaudeClient() as client:
    response = client.complete("Question")

# ❌ Bad (may leak connections)
client = ClaudeClient()
response = client.complete("Question")
# Forgot to call client.close()
```

### 2. Handle Errors Gracefully

```python
with ClaudeClient() as client:
    try:
        response = client.complete(prompt)
    except BudgetExceededError:
        # Fallback to cheaper model
        response = client.complete(prompt, model=Model.HAIKU)
    except TimeoutError:
        # Simplify prompt or increase timeout
        response = client.complete(simplified_prompt, timeout=60.0)
```

### 3. Monitor Usage

```python
with ClaudeClient(project_id="my-app") as client:
    # Check budget before expensive operations
    stats = client.get_usage()

    if stats.remaining and stats.remaining < 10000:
        print("Low budget! Using Haiku.")
        model = Model.HAIKU
    else:
        model = Model.AUTO

    response = client.complete(prompt, model=model)
```

### 4. Use Batch for Multiple Prompts

```python
# ✅ Good - Batch processing (parallel)
with ClaudeClient() as client:
    results = client.batch(prompts)  # All run in parallel

# ❌ Bad - Sequential processing
with ClaudeClient() as client:
    results = [client.complete(p) for p in prompts]  # One at a time
```

### 5. Set Appropriate Timeouts

```python
with ClaudeClient() as client:
    # Short prompts → Short timeout
    client.complete("Hello", timeout=10.0)

    # Long prompts → Long timeout
    client.complete(long_document, timeout=120.0)

    # Batch → Timeout per item
    client.batch(prompts, timeout=30.0)  # 30s per prompt
```

## Data Models

### Response

```python
@dataclass
class Response:
    id: str              # Unique task ID
    model: str           # Model used (haiku, sonnet, opus)
    content: str         # Generated completion
    usage: Usage         # Token usage statistics
    cost: float          # Cost in USD
    project_id: str      # Project identifier
```

### Usage

```python
@dataclass
class Usage:
    input_tokens: int    # Input token count
    output_tokens: int   # Output token count
    total_tokens: int    # Total tokens
```

### BatchResponse

```python
@dataclass
class BatchResponse:
    total: int                 # Total prompts
    completed: int             # Successfully completed
    failed: int                # Failed prompts
    results: List[BatchResult] # Individual results
    total_cost: float          # Total cost
    total_tokens: int          # Total tokens
```

### UsageStats

```python
@dataclass
class UsageStats:
    project_id: str                              # Project ID
    period: str                                  # Time period
    total_tokens: int                            # Total tokens used
    total_cost: float                            # Total cost
    by_model: Dict[str, Dict[str, Union[int, float]]]  # Per-model stats
    limit: Optional[int]                         # Token limit
    remaining: Optional[int]                     # Tokens remaining
```

## API Reference

### ClaudeClient

| Method | Description | Returns |
|--------|-------------|---------|
| `complete(prompt, model, project_id, timeout)` | Generate completion | `Response` |
| `batch(prompts, model, project_id, parallel, timeout)` | Batch processing | `BatchResponse` |
| `get_usage(period, project_id)` | Get usage statistics | `UsageStats` |
| `health()` | Health check | `Dict` |
| `close()` | Close HTTP client | None |

### AsyncClaudeClient

Same methods as `ClaudeClient`, but all are `async` and must be awaited.

### Models Enum

```python
class Model(str, Enum):
    HAIKU = "haiku"    # Fast, cheap
    SONNET = "sonnet"  # Balanced
    OPUS = "opus"      # Most capable
    AUTO = "auto"      # Automatic selection
```

## Examples in Repository

See the `examples/` directory for complete working examples:

- `examples/simple_chatbot.py` - Interactive chatbot
- `examples/batch_processor.py` - Document batch processing
- `examples/code_analyzer.py` - Code analysis with model routing
- `examples/api_usage.py` - Direct API calls without client

## Troubleshooting

### "Connection refused"

API server not running. Start it:
```bash
python main.py
```

### "Module not found: client.claude_client"

Add the repository to your Python path:
```python
import sys
sys.path.append('/path/to/claude-code-api-service')
```

### "httpx not installed"

Install the dependency:
```bash
pip install httpx
```

### Slow responses

- Check your network connection
- Increase timeout: `client.complete(prompt, timeout=60.0)`
- Use cheaper/faster model: `model=Model.HAIKU`
- Check API server logs for issues

## Next Steps

- **[Getting Started](GETTING_STARTED.md)** - Setup and first API call
- **[API Reference](API_REFERENCE.md)** - REST API documentation
- **[Deployment](DEPLOYMENT.md)** - Production deployment guide
- **[Architecture](ARCHITECTURE.md)** - System design details
