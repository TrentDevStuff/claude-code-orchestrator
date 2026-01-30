# Claude Code API Documentation

Welcome to the Claude Code API! This comprehensive API enables you to programmatically access Claude's capabilities with advanced features including:

- **Text Completions**: Simple text-to-text generation
- **Agentic Tasks**: Complex multi-step problem solving with tool orchestration
- **WebSocket Streaming**: Real-time token-by-token streaming
- **Permission System**: Fine-grained access control for multi-tenant deployments
- **Audit Logging**: Complete audit trail for compliance

## Quick Links

- **[5-Minute Quickstart](quickstart.md)** - Get up and running in 5 minutes
- **[Getting Started Guide](guides/getting-started.md)** - Detailed setup instructions
- **[API Reference](api-reference/completions.md)** - Complete endpoint documentation

## Key Features

### Simple Completions API
Send a prompt, get Claude's response. Perfect for straightforward tasks.

```python
from claude_code_client import ClaudeClient

client = ClaudeClient(api_key="sk-proj-...")
response = client.complete("Explain quantum computing in simple terms")
print(response.content)
```

### Agentic Task Execution
Let Claude autonomously solve complex problems using tools (Read, Grep, Bash), spawn agents, and invoke skills.

```python
result = client.execute_task(
    description="Analyze our codebase for security vulnerabilities",
    allow_tools=["Read", "Grep"],
    allow_agents=["security-auditor"]
)
print(result.summary)
for artifact in result.artifacts:
    print(f"Generated: {artifact.path}")
```

### WebSocket Streaming
Stream results in real-time with event-by-event updates.

```python
for event in client.stream_task("Analyze this code for improvements"):
    if event["type"] == "thinking":
        print(f"🤔 {event['content']}")
    elif event["type"] == "tool_call":
        print(f"🔧 {event['tool']}")
    elif event["type"] == "result":
        print(f"✅ {event['summary']}")
```

## Core Concepts

### API Keys
Every request requires a valid API key. Get one by signing up on our platform.

```bash
export CLAUDE_API_KEY="sk-proj-your-key-here"
```

### Models
The API automatically selects the right model for your task:
- **Haiku**: Fast, cost-effective for simple tasks
- **Sonnet**: Balanced performance and cost
- **Opus**: Most capable, for complex reasoning

### Permission Tiers
Control what tools, agents, and skills are available:
- **Free**: Read-only tools, 60-second timeout
- **Pro**: Read/Grep/Bash, 5-minute timeout
- **Enterprise**: All tools/agents/skills, custom limits

### Budgets
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

- **Docs**: Check [documentation](guides/getting-started.md)
- **Examples**: See [examples](examples/) for common use cases
- **API Reference**: See [API reference](api-reference/)
- **GitHub Issues**: Report issues on GitHub

## Next Steps

1. [Get your API key](guides/getting-started.md#getting-your-api-key)
2. [Install the Python client](guides/getting-started.md#installing-the-client)
3. [Run the quickstart](quickstart.md)
4. [Explore examples](examples/)
