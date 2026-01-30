"""Example: Async client usage."""

import asyncio
from claude_code_client import AsyncClaudeClient


async def main():
    """Run async examples."""
    # Initialize async client
    async with AsyncClaudeClient(api_key="sk-proj-your-key") as client:
        # Simple completion
        print("Running simple completion...")
        response = await client.complete("What is async/await?")
        print(f"Response: {response.content}\n")

        # Agentic task
        print("Running agentic task...")
        result = await client.execute_task(
            description="Analyze src/api.py",
            allow_tools=["Read"],
            timeout=60,
        )
        print(f"Status: {result.status}")
        print(f"Result: {result.result}\n")

        # Streaming
        print("Streaming task execution...")
        async for event in client.stream_task(
            description="Simple analysis",
            allow_tools=["Read"],
        ):
            if event["type"] == "thinking":
                print(f"🤔 Thinking...")
            elif event["type"] == "result":
                print(f"✅ Done: {event.get('summary', 'N/A')}")
                break


if __name__ == "__main__":
    asyncio.run(main())
