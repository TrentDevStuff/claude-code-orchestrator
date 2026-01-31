# Claude Code API Documentation

Welcome to the Claude Code API Service! This **self-hosted API** wraps your Claude Code CLI subscription, enabling any application to use Claude with full agentic capabilities.

## Key Features

- **Text Completions**: Simple text-to-text generation
- **Agentic Tasks**: Complex multi-step problem solving with tool orchestration
- **Agent & Skill Discovery**: Access your entire `~/.claude/` ecosystem
- **WebSocket Streaming**: Real-time token-by-token streaming
- **Permission System**: Fine-grained access control for multi-tenant deployments
- **Audit Logging**: Complete audit trail for compliance

## Quick Links

- **[5-Minute Quickstart](quickstart.md)** - Get up and running fast
- **[Getting Started Guide](guides/getting-started.md)** - Detailed setup instructions
- **[API Reference](api-reference/completions.md)** - Complete endpoint documentation

## How It Works

This service runs on your machine and wraps the Claude Code CLI:

```
Your Application
      ↓
  HTTP/WebSocket
      ↓
Claude Code API Service (localhost:8006)
      ↓
Claude Code CLI (your subscription)
      ↓
  Your ~/.claude/ ecosystem
    - Agents
    - Skills
    - Tools
```

## Simple Completions API

Send a prompt, get Claude's response:

```python
import sys
sys.path.insert(0, '/path/to/claude-code-api-service')
from client import ClaudeClient

client = ClaudeClient(
    base_url="http://localhost:8006",
    api_key="YOUR_API_KEY"
)

response = client.complete("Explain quantum computing in simple terms")
print(response.content)
```

## Agentic Task Execution

Let Claude autonomously solve complex problems using tools (Read, Grep, Bash), spawn agents, and invoke skills:

```python
result = client.agentic_task(
    description="Analyze our codebase for security vulnerabilities",
    allow_tools=["Read", "Grep"],
    allow_agents=["security-auditor"]
)
print(result['summary'])
```

## WebSocket Streaming

Stream results in real-time with event-by-event updates:

```python
for event in client.stream("Analyze this code for improvements"):
    print(event, end='', flush=True)
```

## Core Concepts

### API Keys

Create API keys locally to control access:

```bash
# Using CLI
claude-api keys create --project-id my-app --profile enterprise

# Or using Python
from src.auth import AuthManager
auth = AuthManager()
api_key = auth.generate_key("my-app", rate_limit=100)
```

### Models

The API uses your Claude Code subscription models:
- **Haiku**: Fast, cost-effective for simple tasks
- **Sonnet**: Balanced performance and cost
- **Opus**: Most capable, for complex reasoning

### Permission Tiers

Control what tools, agents, and skills are available per API key:
- **Free**: Read-only tools, 60-second timeout
- **Pro**: Read/Write/Bash, 5-minute timeout
- **Enterprise**: All tools/agents/skills, custom limits

### Budget Control

Set spending limits per API key to control costs.

## Documentation Structure

```
docs/
├── index.md                          # This page
├── quickstart.md                     # 5-minute quickstart
├── api-reference/
│   ├── completions.md               # Text completion endpoint
│   ├── agentic-tasks.md             # Task execution endpoint
│   ├── websocket.md                 # WebSocket streaming
│   └── authentication.md            # API keys and auth
├── guides/
│   ├── getting-started.md           # Setup and installation
│   ├── agentic-api-guide.md        # How to use agentic features
│   ├── security-best-practices.md  # Security guidelines
│   ├── permission-model.md         # Permission system
│   └── error-handling.md           # Error codes and handling
├── examples/
│   ├── code-analysis.md            # Analyze code for issues
│   ├── documentation-generation.md # Generate documentation
│   ├── test-generation.md          # Generate test code
│   └── multi-agent-workflow.md     # Complex multi-agent tasks
├── deployment/
│   ├── docker-compose.md           # Deploy with Docker
│   ├── production.md               # Production deployment
│   └── monitoring.md               # Monitoring and observability
└── client-libraries/
    └── python.md                   # Python client reference
```

## Getting Help

- **Interactive API Docs**: Visit `http://localhost:8006/docs` when the service is running
- **CLI Help**: Run `claude-api --help`
- **Examples**: See [examples](examples/) for common use cases
- **Issues**: Report issues at https://github.com/TrentDevStuff/claude-code-api-service/issues

## Next Steps

1. [Start the service](guides/getting-started.md#step-2-start-the-api-service)
2. [Create an API key](guides/getting-started.md#step-3-create-api-keys)
3. [Run the quickstart](quickstart.md)
4. [Explore examples](examples/)
