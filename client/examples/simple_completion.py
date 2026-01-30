"""Example: Simple text completion."""

from claude_code_client import ClaudeClient

# Initialize client
client = ClaudeClient(api_key="sk-proj-your-key")

# Simple completion
response = client.complete("Explain Python asyncio in 3 sentences")
print(response.content)
print(f"\nTokens: {response.usage.get('total_tokens', 0)}")
print(f"Cost: ${response.usage.get('cost', 0):.4f}")

# Close client
client.close()
