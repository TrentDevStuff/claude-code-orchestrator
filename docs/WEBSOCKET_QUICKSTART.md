# WebSocket Quick Start Guide

## Start the Server

```bash
python main.py
```

You should see:
```
✓ Worker pool started (max_workers=5)
✓ Budget manager initialized
✓ Auth manager initialized
✓ API services ready
✓ WebSocket streaming ready
```

## Test with Example Client

```bash
python examples/websocket_client.py
```

## Manual Testing with Python

### Option 1: Simple Test

```python
import asyncio
import json
import websockets

async def test():
    async with websockets.connect("ws://localhost:8080/v1/stream") as ws:
        # Send request
        await ws.send(json.dumps({
            "type": "chat",
            "model": "haiku",
            "messages": [{"role": "user", "content": "Hello!"}]
        }))

        # Receive response
        async for message in ws:
            data = json.loads(message)
            if data["type"] == "token":
                print(data["content"], end="")
            elif data["type"] == "done":
                print(f"\nDone! Cost: ${data['cost']}")
                break

asyncio.run(test())
```

### Option 2: Interactive Session

```python
import asyncio
import json
import websockets

async def interactive():
    async with websockets.connect("ws://localhost:8080/v1/stream") as ws:
        while True:
            prompt = input("\nYou: ")
            if prompt.lower() in ['quit', 'exit']:
                break

            await ws.send(json.dumps({
                "type": "chat",
                "model": "haiku",
                "messages": [{"role": "user", "content": prompt}]
            }))

            print("Claude: ", end="")
            async for message in ws:
                data = json.loads(message)
                if data["type"] == "token":
                    print(data["content"], end="", flush=True)
                elif data["type"] == "done":
                    print()
                    break
                elif data["type"] == "error":
                    print(f"\nError: {data['error']}")
                    break

asyncio.run(interactive())
```

## Test with websocat (CLI tool)

Install websocat:
```bash
# macOS
brew install websocat

# Linux
cargo install websocat
```

Connect and send messages:
```bash
websocat ws://localhost:8080/v1/stream
```

Then type (hit Enter to send):
```json
{"type":"chat","model":"haiku","messages":[{"role":"user","content":"What is 2+2?"}]}
```

## Test with JavaScript (Browser)

```javascript
const ws = new WebSocket('ws://localhost:8080/v1/stream');

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'chat',
    model: 'haiku',
    messages: [{role: 'user', content: 'What is 2+2?'}]
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

## Run Automated Tests

```bash
# Run WebSocket tests only
pytest tests/test_websocket.py -v

# Run all tests
pytest tests/ -v
```

## Check Endpoint Status

```bash
# Check if endpoint is registered
curl http://localhost:8080/

# Should include:
# "stream": "ws://localhost:8080/v1/stream"
```

## Common Issues

### "WebSocket service not initialized"
- Make sure the server is fully started
- Check for error messages in server output

### Connection refused
- Verify server is running on port 8080
- Check firewall settings

### Budget exceeded
- Set a budget or use "default" project which has unlimited budget
- Check budget status: `curl http://localhost:8080/v1/usage?project_id=default`

## Next Steps

- See `docs/WEBSOCKET.md` for full documentation
- See `examples/websocket_client.py` for complete examples
- See `tests/test_websocket.py` for test cases
