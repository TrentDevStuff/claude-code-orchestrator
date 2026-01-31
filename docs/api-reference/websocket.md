# WebSocket Streaming API

Stream agentic task execution events in real-time using WebSocket.

## Endpoint

```
WS /v1/stream
```

## Authentication

Include API key in query parameter or header:

```
ws://localhost:8000/v1/stream?api_key=sk-proj-your-key
```

Or in header:
```
Authorization: Bearer sk-proj-your-key
```

## Event Types

### thinking
Claude's internal reasoning about the task.

```json
{
  "type": "thinking",
  "content": "The user wants me to analyze code for security issues. I should first read the file to understand its structure.",
  "timestamp": "2026-01-30T12:00:00Z"
}
```

### tool_call
When Claude invokes a tool (Read, Grep, Bash, etc).

```json
{
  "type": "tool_call",
  "tool": "Read",
  "arguments": {
    "file_path": "src/api.py"
  },
  "timestamp": "2026-01-30T12:00:01Z"
}
```

### tool_result
Result of a tool invocation.

```json
{
  "type": "tool_result",
  "tool": "Read",
  "status": "success",
  "result": "import fastapi\n...",
  "timestamp": "2026-01-30T12:00:02Z"
}
```

### agent_spawn
When Claude spawns a sub-agent.

```json
{
  "type": "agent_spawn",
  "agent": "security-auditor",
  "reason": "Need specialized security analysis",
  "timestamp": "2026-01-30T12:00:03Z"
}
```

### skill_invoke
When a skill is invoked.

```json
{
  "type": "skill_invoke",
  "skill": "semantic-text-matcher",
  "input": {
    "text1": "SQL injection vulnerability",
    "text2": "Unvalidated database query"
  },
  "timestamp": "2026-01-30T12:00:04Z"
}
```

### result
Final task result and completion.

```json
{
  "type": "result",
  "status": "completed",
  "summary": "Found 3 security issues in the code",
  "result": {
    "issues": [
      {
        "severity": "high",
        "type": "sql_injection",
        "location": "src/api.py:145"
      }
    ]
  },
  "artifacts": [
    {
      "type": "file",
      "path": "security_audit_report.md",
      "size_bytes": 4521
    }
  ],
  "usage": {
    "input_tokens": 2500,
    "output_tokens": 1200,
    "total_tokens": 3700,
    "total_cost": 0.45
  },
  "timestamp": "2026-01-30T12:00:10Z"
}
```

### error
Error occurred during task execution.

```json
{
  "type": "error",
  "error": {
    "type": "permission_error",
    "message": "Tool 'Bash' is not allowed"
  },
  "timestamp": "2026-01-30T12:00:05Z"
}
```

## Examples

### Python Client Streaming

```python
from client import ClaudeClient

client = ClaudeClient(api_key="sk-proj-your-key")

for event in client.stream_task("Analyze code for issues"):
    if event["type"] == "thinking":
        print(f"🤔 Thinking: {event['content'][:100]}...")

    elif event["type"] == "tool_call":
        print(f"🔧 Calling {event['tool']}: {event['arguments']}")

    elif event["type"] == "tool_result":
        print(f"✓ {event['tool']} completed")

    elif event["type"] == "agent_spawn":
        print(f"🤖 Spawned agent: {event['agent']}")

    elif event["type"] == "result":
        print(f"✅ Task completed!")
        print(f"Summary: {event['summary']}")
        print(f"Cost: ${event['usage']['total_cost']:.4f}")
```

### JavaScript/Node.js

```javascript
const ws = new WebSocket("ws://localhost:8000/v1/stream?api_key=sk-proj-your-key");

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: "start_task",
    description: "Analyze src/api.py for security issues",
    allow_tools: ["Read", "Grep"]
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  switch (message.type) {
    case "thinking":
      console.log("🤔", message.content);
      break;
    case "tool_call":
      console.log("🔧", message.tool, message.arguments);
      break;
    case "result":
      console.log("✅ Done!", message.summary);
      ws.close();
      break;
    case "error":
      console.error("❌", message.error.message);
      ws.close();
      break;
  }
};
```

### cURL with WebSocket

```bash
# Using websocat tool
websocat "ws://localhost:8000/v1/stream?api_key=sk-proj-your-key"

# Send task
{"description": "Analyze code", "allow_tools": ["Read"]}

# Receive events
{"type": "thinking", "content": "..."}
{"type": "tool_call", "tool": "Read", ...}
...
{"type": "result", "status": "completed", ...}
```

## Async Python Example

```python
import asyncio
from client import AsyncClaudeClient

async def main():
    client = AsyncClaudeClient(api_key="sk-proj-your-key")

    async for event in client.stream_task("Generate tests"):
        print(f"Event: {event['type']}")

        if event["type"] == "result":
            print(f"Task completed in {event['timestamp']}")
            break

asyncio.run(main())
```

## Connection Limits

- **Max connections per API key**: 10 (Pro: 100, Enterprise: custom)
- **Max message size**: 64KB
- **Idle timeout**: 5 minutes
- **Max duration**: 10 minutes

## Backpressure Handling

If your client can't keep up with events:

```python
import asyncio

async for event in client.stream_task("..."):
    # Process event
    await asyncio.sleep(0.1)  # Add delay if needed
```

## Reconnection

If connection drops, reconnect with the same task ID to resume:

```python
try:
    async for event in client.stream_task("..."):
        process(event)
except ConnectionError:
    # Reconnect to resume
    async for event in client.stream_task_resume(task_id):
        process(event)
```

## Best Practices

1. **Handle all event types** - Don't assume specific event sequences
2. **Add error handling** - Network failures can occur
3. **Set reasonable timeouts** - Client-side timeouts prevent hangs
4. **Don't flood with messages** - Allow time between sent events
5. **Close connections gracefully** - Always call close() when done
