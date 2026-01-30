"""Example: Agentic task execution."""

from claude_code_client import ClaudeClient

# Initialize client
client = ClaudeClient(api_key="sk-proj-your-key")

# Execute agentic task
result = client.execute_task(
    description="Analyze our API code for security vulnerabilities",
    allow_tools=["Read", "Grep"],
    allow_agents=["security-auditor"],
    timeout=300,
    max_cost=1.00,
)

print(f"Status: {result.status}")
print(f"Summary: {result.result.get('summary', 'N/A')}")

print(f"\nExecution Log:")
for entry in result.execution_log:
    print(f"  [{entry.timestamp}] {entry.action}: {entry.details}")

print(f"\nGenerated Artifacts:")
for artifact in result.artifacts:
    print(f"  - {artifact.path} ({artifact.size_bytes} bytes)")

print(f"\nCost: ${result.usage.get('total_cost', 0):.4f}")

# Close client
client.close()
