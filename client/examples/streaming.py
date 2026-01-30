"""Example: WebSocket streaming of agentic task."""

from claude_code_client import ClaudeClient

# Initialize client
client = ClaudeClient(api_key="sk-proj-your-key")

# Stream agentic task execution
print("Streaming task execution...\n")

for event in client.stream_task(
    description="Analyze src/api.py for issues",
    allow_tools=["Read", "Grep"],
    timeout=120,
):
    if event["type"] == "thinking":
        print(f"🤔 {event['content']}")
    elif event["type"] == "tool_call":
        print(f"🔧 {event.get('tool', 'unknown')}: {event.get('details', {})}")
    elif event["type"] == "agent_spawn":
        print(f"🤖 Agent spawned: {event.get('agent', 'unknown')}")
    elif event["type"] == "skill_invoke":
        print(f"⚙️ Skill invoked: {event.get('skill', 'unknown')}")
    elif event["type"] == "result":
        print(f"\n✅ Task completed!")
        print(f"Summary: {event.get('summary', 'N/A')}")
        print(f"Artifacts: {len(event.get('artifacts', []))}")
        break

# Close client
client.close()
