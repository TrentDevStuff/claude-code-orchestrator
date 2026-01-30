# 5-Minute Quickstart

Get up and running with the Claude Code API in just 5 minutes.

## Prerequisites

- Python 3.8+
- An API key (get one at https://claude.ai/api)

## Step 1: Install the Client

```bash
pip install claude-code-client
```

## Step 2: Set Your API Key

```bash
export CLAUDE_API_KEY="sk-proj-your-key-here"
```

## Step 3: Make Your First Request

### Simple Completion

```python
from claude_code_client import ClaudeClient

client = ClaudeClient(api_key="sk-proj-your-key")

# Simple text completion
response = client.complete("What is the capital of France?")
print(response.content)
# Output: The capital of France is Paris.

print(f"Tokens used: {response.usage.total_tokens}")
print(f"Cost: ${response.usage.cost:.4f}")
```

### Agentic Task

```python
# Execute an agentic task
result = client.execute_task(
    description="Count the number of Python files in the current directory",
    allow_tools=["Bash"]
)

print(f"Status: {result.status}")
print(f"Result: {result.result['summary']}")
print(f"Cost: ${result.usage.total_cost:.4f}")
```

### WebSocket Streaming

```python
# Stream results in real-time
for event in client.stream_task("Explain async/await in Python"):
    if event["type"] == "thinking":
        print(f"Thinking: {event['content'][:50]}...")
    elif event["type"] == "result":
        print(f"Done! Summary: {event['summary']}")
```

## Common Use Cases

### Analyze Code

```python
result = client.execute_task(
    description="Analyze src/api.py for security issues",
    allow_tools=["Read", "Grep"],
    timeout=60
)

for artifact in result.artifacts:
    print(f"Generated: {artifact.path}")
```

### Generate Documentation

```python
result = client.execute_task(
    description="Generate API documentation for src/models.py",
    allow_tools=["Read"],
    allow_agents=["documentation-generator"]
)
```

### Generate Tests

```python
result = client.execute_task(
    description="Generate test cases for the User model",
    allow_tools=["Read"],
    allow_agents=["test-generator"]
)
```

## Error Handling

```python
from claude_code_client import (
    ClaudeAPIError,
    AuthenticationError,
    RateLimitError,
    PermissionError
)

try:
    response = client.complete("Test")
except AuthenticationError:
    print("Invalid API key")
except RateLimitError:
    print("Rate limit exceeded, retry later")
except PermissionError:
    print("You don't have permission to use this tool/agent")
except ClaudeAPIError as e:
    print(f"API error: {e}")
```

## Next Steps

- Read the [Getting Started Guide](guides/getting-started.md) for detailed setup
- Explore [examples](examples/) for more use cases
- Check the [API Reference](api-reference/) for complete documentation
- Review [security best practices](guides/security-best-practices.md)

## Need Help?

- Check the [FAQ](guides/getting-started.md#faq)
- Review [error handling guide](guides/error-handling.md)
- See [troubleshooting](guides/getting-started.md#troubleshooting)
