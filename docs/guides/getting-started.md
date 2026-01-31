# Getting Started

Complete guide to setting up and using the Claude Code API Service.

## Overview

This is a **self-hosted API service** that wraps your Claude Code CLI subscription, enabling any application to use Claude with full agentic capabilities. It's not a cloud service - you run it on your own machine.

## Prerequisites

- **Python 3.11+**
- **Claude Code CLI** installed and authenticated ([get it here](https://docs.anthropic.com/en/docs/claude-code))
- **Redis** (optional - for caching)
- **Docker** (optional - for containerized deployment)

Verify Claude Code CLI is working:

```bash
claude --version
```

## Step 1: Clone and Install

```bash
# Clone the repository
git clone https://github.com/TrentDevStuff/claude-code-api-service.git
cd claude-code-api-service

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install CLI (optional but recommended)
pip install -e .
```

## Step 2: Start the API Service

```bash
# Start in foreground
python main.py

# Or use CLI for background operation
claude-api service start --background
```

The server starts at `http://localhost:8006`.

Verify it's running:

```bash
curl http://localhost:8006/health
# Or
claude-api health ping
```

Visit `http://localhost:8006/docs` for interactive API documentation.

## Step 3: Create API Keys

API keys control access to the service. Create them using the CLI or Python.

### Using CLI (Recommended)

```bash
# Create an enterprise-tier key (full access)
claude-api keys create --project-id my-app --profile enterprise

# Create a limited key
claude-api keys create --project-id test --profile pro --rate-limit 50

# List all keys
claude-api keys list

# View key permissions
claude-api keys permissions YOUR_KEY
```

### Using Python

```python
from src.auth import AuthManager
from src.permission_manager import PermissionManager

# Create key
auth = AuthManager()
api_key = auth.generate_key("my-project", rate_limit=100)

# Set permissions
perm = PermissionManager()
perm.apply_default_profile(api_key, "enterprise")  # or "pro", "free"

print(f"API Key: {api_key}")
```

### Permission Tiers

| Tier | Tools | Agents | Rate Limit | Max Cost/Task |
|------|-------|--------|------------|---------------|
| **Free** | Read, Grep | None | 10/min | $0.10 |
| **Pro** | Read, Grep, Bash, Edit, Write | Standard | 100/min | $1.00 |
| **Enterprise** | All | All | Custom | $10.00 |

## Step 4: Make Your First Request

### Using curl

```bash
# Chat completion
curl -X POST http://localhost:8006/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "haiku",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# Agentic task
curl -X POST http://localhost:8006/v1/task \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "description": "List Python files in the current directory",
    "allow_tools": ["Bash", "Glob"],
    "timeout": 60
  }'
```

### Using Python Client

The client library is included in the `client/` directory:

```python
import sys
sys.path.insert(0, '/path/to/claude-code-api-service')
from client import ClaudeClient

# Create client
client = ClaudeClient(
    base_url="http://localhost:8006",
    api_key="YOUR_API_KEY"
)

# Simple completion
response = client.complete("Explain Python decorators")
print(response.content)
print(f"Cost: ${response.cost:.4f}")

# Agentic task with tools
result = client.agentic_task(
    description="Count lines of code in src/",
    allow_tools=["Bash", "Glob"],
    timeout=120
)
print(f"Result: {result}")
```

## Understanding Models

The API supports three models from your Claude Code subscription:

| Model | Speed | Cost | Best For |
|-------|-------|------|----------|
| **Haiku** | Very Fast | Cheapest | Simple tasks, quick responses |
| **Sonnet** | Balanced | Medium | General purpose, most use cases |
| **Opus** | Slower | Most Expensive | Complex reasoning, analysis |

Specify a model or let the API auto-select:

```python
# Explicit model
response = client.complete("...", model="opus")

# Auto-select based on complexity (default)
response = client.complete("...", model="auto")
```

## Using Your Claude Code Ecosystem

The API discovers agents and skills from your `~/.claude/` directory:

```bash
# See what's available
curl http://localhost:8006/v1/capabilities \
  -H "Authorization: Bearer YOUR_KEY"
```

Use them in agentic tasks:

```python
result = client.agentic_task(
    description="Analyze meeting transcript for workflow insights",
    allow_agents=["company-workflow-analyst"],
    allow_skills=["semantic-text-matcher"],
    allow_tools=["Read", "Write"],
    timeout=300
)
```

## WebSocket Streaming

For real-time responses:

```python
for event in client.stream("Write a poem about coding"):
    print(event, end='', flush=True)
```

Or with JavaScript:

```javascript
const ws = new WebSocket('ws://localhost:8006/v1/stream');

ws.send(JSON.stringify({
  type: 'chat',
  model: 'sonnet',
  messages: [{role: 'user', content: 'Write a poem'}],
  api_key: 'YOUR_KEY'
}));

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  if (msg.type === 'token') {
    console.log(msg.content);
  }
};
```

## Managing Costs

Track usage and set limits:

```python
# Check cost after request
response = client.complete("Test")
print(f"Cost: ${response.cost:.4f}")
print(f"Tokens: {response.usage.total_tokens}")

# Set budget limit for task
result = client.agentic_task(
    description="...",
    max_cost=1.0  # Fail if would exceed $1.00
)

# Check usage stats
curl http://localhost:8006/v1/usage?project_id=my-app \
  -H "Authorization: Bearer YOUR_KEY"
```

## Error Handling

```python
from client import (
    ClaudeAPIError,
    AuthenticationError,
    RateLimitError,
    BudgetExceededError,
    TimeoutError
)

try:
    response = client.complete("Test")
except AuthenticationError:
    print("Invalid API key")
except RateLimitError:
    print("Rate limited - wait and retry")
except BudgetExceededError:
    print("Budget exceeded")
except TimeoutError:
    print("Request timed out")
except ClaudeAPIError as e:
    print(f"API error: {e}")
```

## Debugging

Enable logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or check service logs:

```bash
# If running in background
claude-api service logs --follow
```

## Common Issues

### "Service not running"

```bash
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

Your API key doesn't have permission for the requested tool/agent:

```bash
# Check permissions
claude-api keys permissions YOUR_KEY

# Upgrade to enterprise
claude-api keys permissions YOUR_KEY --set-profile enterprise
```

### "Rate limit exceeded"

Wait and retry, or increase rate limit:

```python
import time

def retry_with_backoff(fn, max_retries=3):
    for attempt in range(max_retries):
        try:
            return fn()
        except RateLimitError:
            wait_time = 2 ** attempt
            print(f"Rate limited, waiting {wait_time}s")
            time.sleep(wait_time)
    raise Exception("Max retries exceeded")
```

### "Claude CLI not found"

Install Claude Code CLI:

```bash
# Visit: https://docs.anthropic.com/en/docs/claude-code
```

## Docker Deployment

For containerized deployment:

```bash
# Build and start
docker-compose up -d

# Check health
curl http://localhost:8006/health

# View logs
docker-compose logs -f
```

## Next Steps

1. Explore [API Reference](../api-reference/) for all endpoints
2. Check [examples](../examples/) for common use cases
3. Review [security best practices](security-best-practices.md)
4. Learn about [agentic features](agentic-api-guide.md)
5. Set up [production deployment](../deployment/production.md)

## FAQ

**Q: What's the cost?**
A: This uses your existing Claude Code subscription - no additional cost. Token costs are standard Claude pricing.

**Q: Can I run this in production?**
A: Yes! See [production deployment guide](../deployment/production.md) for best practices.

**Q: How is this different from the Anthropic API?**
A: This wraps Claude Code CLI, giving you access to your `~/.claude/` agents, skills, and full tool capabilities (Read, Write, Bash, etc.).

**Q: Can multiple applications use this?**
A: Yes! Create separate API keys for each application with appropriate permissions.

## Support

- **CLI Help**: `claude-api --help`
- **Docs**: Check `/docs` endpoint when service is running
- **Issues**: https://github.com/TrentDevStuff/claude-code-api-service/issues
