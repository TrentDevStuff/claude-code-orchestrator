"""
Example usage of the Claude API Client Library.

This example demonstrates all major features:
- Simple completions
- Model selection
- Batch processing
- Usage tracking
- Error handling
- Async operations
"""

import asyncio
from client import (
    ClaudeClient,
    AsyncClaudeClient,
    Model,
    ClaudeAPIError,
    BudgetExceededError,
)


def example_basic_usage():
    """Basic usage example."""
    print("=" * 60)
    print("EXAMPLE 1: Basic Usage")
    print("=" * 60)

    with ClaudeClient(base_url="http://localhost:8080") as client:
        # Simple completion
        response = client.complete("Write a haiku about Python programming")

        print(f"Response ID: {response.id}")
        print(f"Model used: {response.model}")
        print(f"Content:\n{response.content}")
        print(f"Cost: ${response.cost:.4f}")
        print(f"Tokens: {response.usage.total_tokens}")


def example_model_selection():
    """Example with explicit model selection."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Model Selection")
    print("=" * 60)

    with ClaudeClient(base_url="http://localhost:8080") as client:
        # Use different models
        models = [Model.HAIKU, Model.SONNET, Model.AUTO]

        for model in models:
            print(f"\nUsing model: {model.value}")
            response = client.complete(
                "Count to 3",
                model=model
            )
            print(f"Response: {response.content}")
            print(f"Actual model: {response.model}")
            print(f"Cost: ${response.cost:.4f}")


def example_batch_processing():
    """Example of batch processing."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Batch Processing")
    print("=" * 60)

    with ClaudeClient(base_url="http://localhost:8080") as client:
        prompts = [
            "What is 2+2?",
            "Name a color",
            "Count from 1 to 3",
            "Say hello",
        ]

        print(f"Processing {len(prompts)} prompts in batch...")
        results = client.batch(prompts, model=Model.HAIKU)

        print(f"\nResults:")
        print(f"- Total: {results.total}")
        print(f"- Completed: {results.completed}")
        print(f"- Failed: {results.failed}")
        print(f"- Total cost: ${results.total_cost:.4f}")
        print(f"- Total tokens: {results.total_tokens}")

        print("\nIndividual results:")
        for i, result in enumerate(results.results, 1):
            if result.status == "completed":
                print(f"{i}. ✓ {result.content[:50]}...")
                print(f"   Cost: ${result.cost:.4f}")
            else:
                print(f"{i}. ✗ Error: {result.error}")


def example_usage_tracking():
    """Example of usage tracking."""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Usage Tracking")
    print("=" * 60)

    with ClaudeClient(base_url="http://localhost:8080") as client:
        # Make some requests
        print("Making a few requests...")
        for i in range(3):
            client.complete(f"Say hello #{i+1}", model=Model.HAIKU)

        # Check usage
        print("\nChecking usage statistics...")

        # Monthly usage
        stats = client.get_usage(period="month")
        print(f"\nMonthly usage:")
        print(f"- Total tokens: {stats.total_tokens:,}")
        print(f"- Total cost: ${stats.total_cost:.2f}")

        if stats.limit:
            print(f"- Budget limit: {stats.limit:,} tokens")
            print(f"- Remaining: {stats.remaining:,} tokens")
            print(f"- Used: {(stats.total_tokens / stats.limit * 100):.1f}%")

        print(f"\nPer-model breakdown:")
        for model_name, model_stats in stats.by_model.items():
            print(f"- {model_name}:")
            print(f"  Tokens: {model_stats['tokens']:,}")
            print(f"  Cost: ${model_stats['cost']:.4f}")


def example_error_handling():
    """Example of error handling."""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Error Handling")
    print("=" * 60)

    with ClaudeClient(base_url="http://localhost:8080") as client:
        try:
            # This might fail due to various reasons
            response = client.complete("Test prompt")
            print(f"Success: {response.content[:50]}...")

        except BudgetExceededError as e:
            print(f"⚠️  Budget exceeded: {e}")
            print("Consider using a cheaper model or increasing budget")

        except ClaudeAPIError as e:
            print(f"❌ API error: {e}")
            print("Check service status and try again")


def example_streaming():
    """Example of streaming responses."""
    print("\n" + "=" * 60)
    print("EXAMPLE 6: Streaming (placeholder)")
    print("=" * 60)

    with ClaudeClient(base_url="http://localhost:8080") as client:
        print("Streaming response:")
        print("> ", end="", flush=True)

        for chunk in client.stream("Tell me a short joke"):
            print(chunk, end="", flush=True)

        print("\n")


async def example_async_operations():
    """Example of async operations."""
    print("\n" + "=" * 60)
    print("EXAMPLE 7: Async Operations")
    print("=" * 60)

    async with AsyncClaudeClient(base_url="http://localhost:8080") as client:
        # Single async completion
        print("Making async completion...")
        response = await client.complete("What is async programming?")
        print(f"Response: {response.content[:100]}...")

        # Async batch
        print("\nMaking async batch request...")
        prompts = ["Hello", "Goodbye", "Thank you"]
        results = await client.batch(prompts, model=Model.HAIKU)
        print(f"Processed {results.completed}/{results.total} prompts")

        # Async usage stats
        print("\nFetching async usage stats...")
        stats = await client.get_usage()
        print(f"Total tokens: {stats.total_tokens:,}")


def example_health_check():
    """Example of health check."""
    print("\n" + "=" * 60)
    print("EXAMPLE 8: Health Check")
    print("=" * 60)

    try:
        with ClaudeClient(base_url="http://localhost:8080") as client:
            health = client.health()

            print(f"Service status: {health['status']}")
            print(f"Version: {health['version']}")
            print(f"Services: {health['services']}")

            if health['status'] == 'ok':
                print("✓ Service is healthy and ready")
            else:
                print("⚠️  Service has issues")

    except Exception as e:
        print(f"❌ Service is unavailable: {e}")


def example_multiple_projects():
    """Example of using multiple projects."""
    print("\n" + "=" * 60)
    print("EXAMPLE 9: Multiple Projects")
    print("=" * 60)

    with ClaudeClient(base_url="http://localhost:8080") as client:
        projects = ["project-a", "project-b", "project-c"]

        for project_id in projects:
            # Make request for this project
            response = client.complete(
                f"Hello from {project_id}",
                model=Model.HAIKU,
                project_id=project_id
            )

            # Check usage for this project
            stats = client.get_usage(project_id=project_id)

            print(f"\n{project_id}:")
            print(f"  Response: {response.content[:30]}...")
            print(f"  Total tokens: {stats.total_tokens}")
            print(f"  Total cost: ${stats.total_cost:.4f}")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("CLAUDE API CLIENT - USAGE EXAMPLES")
    print("=" * 60)
    print("\nNote: Make sure the API service is running at http://localhost:8080")
    print("Start it with: python main.py\n")

    try:
        # Check if service is running
        with ClaudeClient(base_url="http://localhost:8080") as client:
            health = client.health()
            if health['status'] != 'ok':
                print("⚠️  Warning: Service is not healthy")
                return

        # Run examples
        example_basic_usage()
        example_model_selection()
        example_batch_processing()
        example_usage_tracking()
        example_error_handling()
        example_streaming()

        # Run async examples
        asyncio.run(example_async_operations())

        example_health_check()
        example_multiple_projects()

        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure the API service is running:")
        print("  python main.py")


if __name__ == "__main__":
    main()
