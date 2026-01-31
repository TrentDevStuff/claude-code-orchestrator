# 5-Minute Quickstart

Get up and running with the Claude Code API in just 5 minutes.

## Prerequisites

- Python 3.11+
- Claude Code CLI installed ([get it here](https://docs.anthropic.com/en/docs/claude-code))
- The API service running (see below)

## Step 1: Start the API Service

```bash
# Clone the repository (if you haven't)
git clone https://github.com/TrentDevStuff/claude-code-api-service.git
cd claude-code-api-service

# Install dependencies
pip install -r requirements.txt

# Start the server
python main.py
```

Server starts at `http://localhost:8006`. Verify with:

```bash
curl http://localhost:8006/health
```

## Step 2: Create an API Key

Use the CLI or Python to create an API key:

**Using CLI (recommended):**
```bash
# Install CLI
pip install -e .

# Create a key
claude-api keys create --project-id my-app --profile enterprise
```

**Using Python:**
```python
from src.auth import AuthManager
from src.permission_manager import PermissionManager

auth = AuthManager()
api_key = auth.generate_key("my-app", rate_limit=100)

perm = PermissionManager()
perm.apply_default_profile(api_key, "enterprise")

print(f"Your API key: {api_key}")
```

## Step 3: Make Your First Request

### Simple Completion

```bash
curl -X POST http://localhost:8006/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "haiku",
    "messages": [{"role": "user", "content": "What is the capital of France?"}]
  }'
```

### Using the Python Client

```python
import sys
sys.path.insert(0, '/path/to/claude-code-api-service')
from client import ClaudeClient

client = ClaudeClient(
    base_url="http://localhost:8006",
    api_key="YOUR_API_KEY"
)

# Simple completion
response = client.complete("What is the capital of France?")
print(response.content)
print(f"Tokens used: {response.usage.total_tokens}")
print(f"Cost: ${response.cost:.4f}")
```

### Agentic Task

```bash
curl -X POST http://localhost:8006/v1/task \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "description": "Count the number of Python files in the current directory",
    "allow_tools": ["Bash", "Glob"],
    "timeout": 60
  }'
```

Or with Python:

```python
result = client.agentic_task(
    description="Count the number of Python files in the current directory",
    allow_tools=["Bash", "Glob"],
    timeout=60
)

print(f"Status: {result['status']}")
print(f"Result: {result['result']}")
```

## Common Use Cases

### Analyze Code

```python
result = client.agentic_task(
    description="Analyze src/api.py for security issues",
    allow_tools=["Read", "Grep"],
    timeout=60
)

for artifact in result.get('artifacts', []):
    print(f"Generated: {artifact['path']}")
```

### Discover Available Agents & Skills

**Using the CLI (recommended):**
```bash
# List all agents
claude-api agents list --key YOUR_API_KEY

# Search for workflow-related agents
claude-api agents search workflow --key YOUR_API_KEY

# Get detailed info about an agent
claude-api agents info company-workflow-analyst --key YOUR_API_KEY

# List all skills
claude-api skills list --key YOUR_API_KEY

# Search skills
claude-api skills search text --key YOUR_API_KEY
```

**Using the API:**
```python
import requests

resp = requests.get(
    "http://localhost:8006/v1/capabilities",
    headers={"Authorization": "Bearer YOUR_API_KEY"}
)
print(resp.json())
```

**Use an agent in a task:**
```python
result = client.agentic_task(
    description="Extract workflow insights from meeting.txt",
    allow_agents=["company-workflow-analyst"],
    allow_skills=["semantic-text-matcher"],
    allow_tools=["Read", "Write"]
)
```

### Generate Documentation

```python
result = client.agentic_task(
    description="Generate API documentation for src/models.py",
    allow_tools=["Read"],
    timeout=120
)
```

## Error Handling

```python
from client import (
    ClaudeAPIError,
    AuthenticationError,
    RateLimitError,
    BudgetExceededError
)

try:
    response = client.complete("Test")
except AuthenticationError:
    print("Invalid API key - create one with: claude-api keys create")
except RateLimitError:
    print("Rate limit exceeded, retry later")
except BudgetExceededError:
    print("Budget exceeded for this API key")
except ClaudeAPIError as e:
    print(f"API error: {e}")
```

## Next Steps

- Read the [Getting Started Guide](guides/getting-started.md) for detailed setup
- Explore [examples](examples/) for more use cases
- Check the [API Reference](api-reference/) for complete documentation
- Review [security best practices](guides/security-best-practices.md)

## Troubleshooting

**Service not running?**
```bash
# Check health
curl http://localhost:8006/health

# Or use CLI
claude-api health ping
```

**Invalid API key?**
```bash
# List keys
claude-api keys list

# Create new key
claude-api keys create --project-id test --profile enterprise
```

**Need help?**
- Check [CLI README](../cli/README.md) for command reference
- See [error handling guide](guides/error-handling.md)
