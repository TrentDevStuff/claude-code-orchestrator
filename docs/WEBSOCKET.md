# WebSocket Streaming API

Real-time streaming chat endpoint for Claude Code API Service.

## Overview

The WebSocket endpoint provides real-time token-by-token streaming of chat responses, enabling a better user experience for interactive applications.

**Endpoint:** `ws://localhost:8080/v1/stream`

## Protocol

### Client → Server

Send a JSON message with the following structure:

```json
{
  "type": "chat",
  "model": "haiku",
  "messages": [
    {"role": "user", "content": "Hello, Claude!"}
  ],
  "project_id": "my-project"
}
```

**Fields:**
- `type` (required): Message type. Must be `"chat"`.
- `model` (optional): Model to use. Options: `"haiku"`, `"sonnet"`, `"opus"`. Default: `"sonnet"`.
- `messages` (required): Array of message objects with `role` and `content`.
- `project_id` (optional): Project identifier for budget tracking. Default: `"default"`.

### Server → Client

The server sends multiple JSON messages:

#### Token Message (streaming)

```json
{
  "type": "token",
  "content": "Hello"
}
```

Sent continuously as tokens are generated.

#### Done Message (completion)

```json
{
  "type": "done",
  "usage": {
    "input_tokens": 10,
    "output_tokens": 5,
    "total_tokens": 15
  },
  "cost": 0.0001875,
  "model": "haiku"
}
```

Sent when the response is complete.

#### Error Message

```json
{
  "type": "error",
  "error": "Error description"
}
```

Sent when an error occurs.

## Usage Examples

### Python (websockets)

```python
import asyncio
import json
import websockets

async def chat():
    uri = "ws://localhost:8080/v1/stream"

    async with websockets.connect(uri) as websocket:
        # Send request
        await websocket.send(json.dumps({
            "type": "chat",
            "model": "haiku",
            "messages": [{"role": "user", "content": "What is 2+2?"}]
        }))

        # Receive streaming response
        while True:
            response = await websocket.recv()
            data = json.loads(response)

            if data["type"] == "token":
                print(data["content"], end="", flush=True)
            elif data["type"] == "done":
                print(f"\n\nCost: ${data['cost']:.6f}")
                break
            elif data["type"] == "error":
                print(f"Error: {data['error']}")
                break

asyncio.run(chat())
```

### JavaScript (Browser)

```javascript
const ws = new WebSocket('ws://localhost:8080/v1/stream');

ws.onopen = () => {
  // Send request
  ws.send(JSON.stringify({
    type: 'chat',
    model: 'haiku',
    messages: [{role: 'user', content: 'What is 2+2?'}]
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'token') {
    // Append token to UI
    document.getElementById('response').textContent += data.content;
  } else if (data.type === 'done') {
    console.log('Cost:', data.cost);
  } else if (data.type === 'error') {
    console.error('Error:', data.error);
  }
};
```

### cURL (via websocat)

```bash
# Install websocat: https://github.com/vi/websocat
websocat ws://localhost:8080/v1/stream

# Then type:
{"type":"chat","model":"haiku","messages":[{"role":"user","content":"What is 2+2?"}]}
```

## Multiple Messages

You can send multiple chat messages on the same WebSocket connection:

```python
async with websockets.connect(uri) as websocket:
    # First message
    await websocket.send(json.dumps({
        "type": "chat",
        "model": "haiku",
        "messages": [{"role": "user", "content": "What is 2+2?"}]
    }))

    # Read response...

    # Second message
    await websocket.send(json.dumps({
        "type": "chat",
        "model": "haiku",
        "messages": [{"role": "user", "content": "What is the capital of France?"}]
    }))

    # Read response...
```

## Error Handling

### Budget Exceeded

```json
{
  "type": "error",
  "error": "Budget exceeded for project my-project"
}
```

Returned when the project has exhausted its monthly token budget.

### Invalid Model

```json
{
  "type": "error",
  "error": "Invalid model: gpt-4. Must be haiku, sonnet, or opus"
}
```

Returned when an unsupported model is requested.

### Invalid JSON

```json
{
  "type": "error",
  "error": "Invalid JSON format"
}
```

Returned when the client sends malformed JSON.

### Unknown Message Type

```json
{
  "type": "error",
  "error": "Unknown message type: unknown"
}
```

Returned when the client sends a message with an unrecognized type.

## Features

- **Real-time Streaming:** Tokens are sent as they're generated
- **Budget Integration:** Automatic budget checking before processing
- **Usage Tracking:** All requests are tracked in BudgetManager
- **Error Handling:** Graceful error responses for all failure cases
- **Multiple Messages:** Send multiple requests on same connection
- **Cost Calculation:** Accurate cost reporting per request

## Implementation Details

### Architecture

- **WebSocketStreamer:** Main class handling connections
- **Token Streaming:** Tokens are chunked and sent in real-time
- **Process Management:** Uses subprocess to run Claude CLI
- **Budget Manager:** Validates budgets and tracks usage
- **Worker Pool:** Integrates with existing worker pool architecture

### Cost Calculation

Costs are calculated using the same rates as the REST API:

| Model | Input ($/MTk) | Output ($/MTk) |
|-------|---------------|----------------|
| Haiku | $0.25 | $1.25 |
| Sonnet | $3.00 | $15.00 |
| Opus | $15.00 | $75.00 |

### Timeouts

- Default timeout: 30 seconds per request
- Connection automatically closes on disconnect

## Testing

Run the WebSocket tests:

```bash
pytest tests/test_websocket.py -v
```

Run the example client:

```bash
python examples/websocket_client.py
```

## Comparison with REST API

| Feature | WebSocket | REST API |
|---------|-----------|----------|
| Streaming | ✓ Real-time | ✗ Block until complete |
| Latency | Low (tokens as generated) | Higher (wait for full response) |
| Connection | Persistent | One-shot |
| Overhead | Lower (reuse connection) | Higher (new request each time) |
| Use Case | Interactive chat | Batch processing |

## Best Practices

1. **Reuse Connections:** Keep the WebSocket open for multiple messages
2. **Handle Errors:** Always handle `error` message type
3. **Budget Management:** Monitor budget status to avoid failures
4. **Timeouts:** Implement client-side timeouts for long-running requests
5. **Reconnection:** Implement reconnection logic for network issues

## Next Steps

- See `examples/websocket_client.py` for working examples
- Check `tests/test_websocket.py` for test cases
- Review `src/websocket.py` for implementation details
