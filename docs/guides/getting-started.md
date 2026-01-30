# Getting Started

Complete guide to setting up and using the Claude Code API.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- An API key (get one at https://claude.ai/api)

## Step 1: Get Your API Key

1. Visit https://claude.ai/api
2. Sign up or log in
3. Navigate to "API Keys"
4. Click "Generate New Key"
5. Copy the key (displayed only once)
6. Store it safely

## Step 2: Set Up Environment Variable

Store your API key securely using an environment variable:

```bash
export CLAUDE_API_KEY="sk-proj-your-key-here"
```

Or in a `.env` file:

```
CLAUDE_API_KEY=sk-proj-your-key-here
```

Load it with `python-dotenv`:

```python
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("CLAUDE_API_KEY")
```

## Step 3: Install the Python Client

```bash
pip install claude-code-client
```

Verify installation:

```bash
python -c "import claude_code_client; print('OK')"
```

## Step 4: Make Your First Request

Create `hello.py`:

```python
from claude_code_client import ClaudeClient

client = ClaudeClient()  # Uses CLAUDE_API_KEY env var

response = client.complete("What is Python?")
print(response.content)
```

Run it:

```bash
python hello.py
```

Expected output:

```
Python is a high-level, interpreted programming language...
```

## Step 5: Try an Agentic Task

Create `analyze.py`:

```python
from claude_code_client import ClaudeClient

client = ClaudeClient()

result = client.execute_task(
    description="Count the lines of Python code in the current directory",
    allow_tools=["Bash"]
)

print(f"Status: {result.status}")
print(f"Result: {result.result['summary']}")
print(f"Cost: ${result.usage.total_cost:.4f}")
```

Run it:

```bash
python analyze.py
```

## Understanding Models

The API has three models:

| Model | Speed | Cost | Best For |
|-------|-------|------|----------|
| **Haiku** | Very Fast | Cheapest | Simple tasks, quick responses |
| **Sonnet** | Balanced | Medium | General purpose, most use cases |
| **Opus** | Slower | Most Expensive | Complex reasoning, analysis |

The API auto-selects based on your task. Specify manually:

```python
response = client.complete("...", model="opus")
```

## Error Handling

Always handle errors gracefully:

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
    print("Rate limited, retry later")
except PermissionError:
    print("Tool not allowed for your key")
except ClaudeAPIError as e:
    print(f"Error: {e}")
```

## Using WebSocket Streaming

Stream results in real-time:

```python
for event in client.stream_task("Analyze code"):
    if event["type"] == "thinking":
        print(f"🤔 Thinking...")
    elif event["type"] == "tool_call":
        print(f"🔧 {event['tool']}")
    elif event["type"] == "result":
        print(f"✅ Done!")
        print(event['summary'])
```

## Async Client

For async applications:

```python
import asyncio
from claude_code_client import AsyncClaudeClient

async def main():
    client = AsyncClaudeClient()
    response = await client.complete("Hello")
    print(response.content)

asyncio.run(main())
```

## Managing Costs

Monitor and control spending:

```python
# Check response cost
response = client.complete("Test")
print(f"Cost: ${response.usage.cost:.4f}")

# Set budget limit
result = client.execute_task(
    description="...",
    max_cost=5.00  # Fail if exceeds $5
)

# Check usage
print(f"Tokens: {response.usage.total_tokens}")
print(f"Input: {response.usage.input_tokens}")
print(f"Output: {response.usage.output_tokens}")
```

## Debugging

Enable logging to see detailed information:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
client = ClaudeClient()
```

Or use environment variable:

```bash
CLAUDE_DEBUG=1 python script.py
```

## Common Issues

### "Invalid API key"

- Check CLAUDE_API_KEY environment variable is set
- Verify key from https://claude.ai/api/keys
- Ensure key is not revoked

### "Rate limit exceeded"

- Wait 60 seconds before retrying
- Upgrade to Pro tier for higher limits
- Implement exponential backoff:

```python
import time

def retry_with_backoff(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError:
            wait_time = 2 ** attempt
            print(f"Rate limited, waiting {wait_time}s")
            time.sleep(wait_time)
```

### "Permission denied"

- Tool/agent/skill not allowed for your API key
- Upgrade tier or request specific permission
- Check API Keys dashboard for permissions

### Network timeouts

- Increase timeout parameter:

```python
client = ClaudeClient(timeout=600)  # 10 minutes
```

- Break large tasks into smaller ones
- Check API status at https://claude.ai/status

## Next Steps

1. Read [API Reference](../api-reference/) for detailed docs
2. Check [examples](../examples/) for use cases
3. Review [security best practices](security-best-practices.md)
4. Explore [agentic features guide](agentic-api-guide.md)

## FAQ

**Q: How much does it cost?**
A: See [pricing](../api-reference/completions.md#pricing). Start with Free tier, upgrade as needed.

**Q: Can I use it in production?**
A: Yes! Use Enterprise tier for production workloads with custom limits.

**Q: What data do you collect?**
A: See Privacy Policy at https://claude.ai/privacy. We don't use requests to train models.

**Q: Can I deploy locally?**
A: See [Docker deployment](../deployment/docker-compose.md).

**Q: How do I report security issues?**
A: Email security@claude.ai with details.

## Support

- **Docs**: https://claude.ai/docs
- **Status**: https://claude.ai/status
- **Email**: support@claude.ai
- **GitHub**: https://github.com/anthropics/claude-code-api
