"""
Simple example of using the Claude API Client.

This is a minimal example to get started quickly.
"""

from client import ClaudeClient, Model


def main():
    # Create a client (using context manager for automatic cleanup)
    with ClaudeClient(base_url="http://localhost:8080") as client:
        # Simple completion
        print("1. Simple completion:")
        response = client.complete("Write a haiku about coding")
        print(f"   {response.content}")
        print(f"   (Cost: ${response.cost:.4f}, Model: {response.model})\n")

        # Using a specific model
        print("2. Using Haiku model:")
        response = client.complete("Count to 5", model=Model.HAIKU)
        print(f"   {response.content}")
        print(f"   (Cost: ${response.cost:.4f})\n")

        # Batch processing
        print("3. Batch processing:")
        prompts = [
            "What is 2+2?",
            "Name a primary color",
            "What day comes after Monday?"
        ]
        results = client.batch(prompts, model=Model.HAIKU)

        print(f"   Completed: {results.completed}/{results.total}")
        print(f"   Total cost: ${results.total_cost:.4f}")

        for i, result in enumerate(results.results, 1):
            if result.status == "completed":
                print(f"   {i}. {result.content}")

        # Check usage
        print("\n4. Usage statistics:")
        stats = client.get_usage(period="month")
        print(f"   Total tokens this month: {stats.total_tokens:,}")
        print(f"   Total cost this month: ${stats.total_cost:.2f}")


if __name__ == "__main__":
    print("Claude API Client - Simple Example")
    print("=" * 50)
    print("\nMake sure the API service is running:")
    print("  python main.py\n")

    try:
        main()
        print("\n✓ Example completed successfully!")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Is the API service running? (python main.py)")
        print("  2. Is it accessible at http://localhost:8080?")
        print("  3. Check the service logs for errors")
