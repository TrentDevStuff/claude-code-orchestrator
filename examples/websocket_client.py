#!/usr/bin/env python3
"""
WebSocket Client Example

Demonstrates how to connect to the Claude Code API WebSocket endpoint
and stream real-time chat responses.

Usage:
    python examples/websocket_client.py
"""

import asyncio
import json
import websockets


async def stream_chat():
    """Connect to WebSocket and stream a chat response."""
    uri = "ws://localhost:8080/v1/stream"

    print("Connecting to WebSocket endpoint...")

    async with websockets.connect(uri) as websocket:
        print("✓ Connected!")

        # Send a chat request
        request = {
            "type": "chat",
            "model": "haiku",
            "messages": [
                {"role": "user", "content": "What is 2+2? Give me a short answer."}
            ],
            "project_id": "test-project"
        }

        print(f"\nSending: {request['messages'][0]['content']}\n")
        await websocket.send(json.dumps(request))

        print("Streaming response:")
        print("-" * 60)

        full_response = ""

        # Receive streaming tokens
        while True:
            response = await websocket.recv()
            data = json.loads(response)

            if data["type"] == "token":
                # Print token without newline
                token = data["content"]
                print(token, end="", flush=True)
                full_response += token

            elif data["type"] == "done":
                # Final message with usage stats
                print("\n" + "-" * 60)
                print(f"\n✓ Complete!")
                print(f"Model: {data['model']}")
                print(f"Tokens: {data['usage']['total_tokens']}")
                print(f"Cost: ${data['cost']:.6f}")
                break

            elif data["type"] == "error":
                # Error occurred
                print(f"\n✗ Error: {data['error']}")
                break


async def multiple_messages():
    """Send multiple messages on the same connection."""
    uri = "ws://localhost:8080/v1/stream"

    print("Testing multiple messages on same connection...")

    async with websockets.connect(uri) as websocket:
        print("✓ Connected!")

        questions = [
            "What is 2+2?",
            "What is the capital of France?",
            "Name one planet in our solar system."
        ]

        for i, question in enumerate(questions, 1):
            print(f"\n[{i}/{len(questions)}] {question}")
            print("-" * 60)

            request = {
                "type": "chat",
                "model": "haiku",
                "messages": [{"role": "user", "content": question}],
                "project_id": "test-project"
            }

            await websocket.send(json.dumps(request))

            # Receive response
            while True:
                response = await websocket.recv()
                data = json.loads(response)

                if data["type"] == "token":
                    print(data["content"], end="", flush=True)
                elif data["type"] == "done":
                    print(f"\n(Tokens: {data['usage']['total_tokens']}, "
                          f"Cost: ${data['cost']:.6f})")
                    break
                elif data["type"] == "error":
                    print(f"\n✗ Error: {data['error']}")
                    break

        print("\n✓ All messages completed!")


async def test_error_handling():
    """Test error handling."""
    uri = "ws://localhost:8080/v1/stream"

    print("Testing error handling...")

    async with websockets.connect(uri) as websocket:
        print("✓ Connected!")

        # Test 1: Invalid JSON
        print("\nTest 1: Sending invalid JSON")
        await websocket.send("not valid json")

        response = await websocket.recv()
        data = json.loads(response)
        print(f"Response: {data}")

        # Test 2: Invalid model
        print("\nTest 2: Invalid model")
        request = {
            "type": "chat",
            "model": "gpt-4",  # Invalid model
            "messages": [{"role": "user", "content": "Hello"}]
        }
        await websocket.send(json.dumps(request))

        response = await websocket.recv()
        data = json.loads(response)
        print(f"Response: {data}")

        # Test 3: Unknown message type
        print("\nTest 3: Unknown message type")
        request = {"type": "unknown"}
        await websocket.send(json.dumps(request))

        response = await websocket.recv()
        data = json.loads(response)
        print(f"Response: {data}")

        print("\n✓ Error handling tests completed!")


async def main():
    """Run examples."""
    print("=" * 60)
    print("WebSocket Client Examples")
    print("=" * 60)

    try:
        # Example 1: Basic streaming
        print("\n[Example 1] Basic Streaming")
        print("=" * 60)
        await stream_chat()

        await asyncio.sleep(1)

        # Example 2: Multiple messages
        print("\n\n[Example 2] Multiple Messages")
        print("=" * 60)
        await multiple_messages()

        await asyncio.sleep(1)

        # Example 3: Error handling
        print("\n\n[Example 3] Error Handling")
        print("=" * 60)
        await test_error_handling()

    except websockets.exceptions.WebSocketException as e:
        print(f"\n✗ WebSocket error: {e}")
        print("\nMake sure the server is running:")
        print("  python main.py")
    except Exception as e:
        print(f"\n✗ Error: {e}")


if __name__ == "__main__":
    print("\nNote: Make sure the server is running first:")
    print("  python main.py\n")

    asyncio.run(main())
