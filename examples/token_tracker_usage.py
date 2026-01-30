"""
Example usage of TokenTracker with BudgetManager integration.

This example demonstrates:
1. Parsing Claude CLI JSON output
2. Calculating token costs
3. Integrating with BudgetManager for tracking
"""

import asyncio
import json
import tempfile
import os
from src.token_tracker import TokenTracker
from src.budget_manager import BudgetManager


async def example_basic_usage():
    """Basic usage example of TokenTracker."""
    print("=" * 60)
    print("Basic TokenTracker Usage")
    print("=" * 60)

    # Simulate Claude CLI output
    claude_output = json.dumps({
        "usage": {
            "input_tokens": 1500,
            "output_tokens": 800
        },
        "model": "claude-3-sonnet-20240229"
    })

    # Parse the output
    result = TokenTracker.parse_claude_output(claude_output)

    print(f"\nParsed Result:")
    print(f"  Input Tokens:  {result['input_tokens']:,}")
    print(f"  Output Tokens: {result['output_tokens']:,}")
    print(f"  Total Tokens:  {result['total_tokens']:,}")
    print(f"  Model:         {result['model']}")
    print(f"  Model Tier:    {result['model_tier']}")
    print(f"  Cost:          ${result['cost_usd']:.6f}")
    print()


async def example_cost_comparison():
    """Compare costs across different models."""
    print("=" * 60)
    print("Cost Comparison Across Models")
    print("=" * 60)

    # Same token counts for all models
    input_tokens = 10000
    output_tokens = 5000

    models = ["haiku", "sonnet", "opus"]

    print(f"\nFor {input_tokens:,} input and {output_tokens:,} output tokens:\n")

    for model in models:
        cost = TokenTracker.calculate_cost(input_tokens, output_tokens, model)
        print(f"  {model.capitalize():8} ${float(cost):>8.6f}")

    print()


async def example_integration_with_budget_manager():
    """Example of integrating TokenTracker with BudgetManager."""
    print("=" * 60)
    print("Integration with BudgetManager")
    print("=" * 60)

    # Initialize BudgetManager with temp file (in-memory db has connection issues)
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    temp_db.close()
    budget_manager = BudgetManager(db_path=temp_db.name)

    # Set up a project with budget
    project_id = "demo-project"
    await budget_manager.set_budget(
        project_id=project_id,
        monthly_limit=100000,
        name="Demo Project"
    )
    print(f"\nSet up project '{project_id}' with 100,000 token limit")

    # Simulate multiple API calls
    api_calls = [
        {
            "usage": {"input_tokens": 1200, "output_tokens": 600},
            "model": "claude-3-haiku-20240307"
        },
        {
            "usage": {"input_tokens": 2500, "output_tokens": 1500},
            "model": "claude-3-sonnet-20240229"
        },
        {
            "usage": {"input_tokens": 800, "output_tokens": 400},
            "model": "claude-3-haiku-20240307"
        }
    ]

    print("\nProcessing API calls:")
    total_cost = 0

    for i, call_data in enumerate(api_calls, 1):
        # Parse Claude output
        result = TokenTracker.parse_claude_output(json.dumps(call_data))

        # Track usage in BudgetManager
        await budget_manager.track_usage(
            project_id=project_id,
            model=result["model_tier"],
            tokens=result["total_tokens"],
            cost=result["cost_usd"]
        )

        total_cost += result["cost_usd"]

        print(f"\n  Call {i}:")
        print(f"    Model:  {result['model_tier']}")
        print(f"    Tokens: {result['total_tokens']:,}")
        print(f"    Cost:   ${result['cost_usd']:.6f}")

    # Get usage statistics
    usage_stats = await budget_manager.get_usage(project_id)

    print("\n" + "=" * 60)
    print("Usage Statistics")
    print("=" * 60)
    print(f"\nTotal Tokens: {usage_stats['total_tokens']:,}")
    print(f"Total Cost:   ${usage_stats['total_cost']:.6f}")
    print(f"Budget Limit: {usage_stats['limit']:,} tokens")
    print(f"Remaining:    {usage_stats['remaining']:,} tokens")
    print(f"Used:         {(usage_stats['total_tokens'] / usage_stats['limit'] * 100):.1f}%")

    print("\nUsage by Model:")
    for model, stats in usage_stats['by_model'].items():
        print(f"  {model:8} {stats['tokens']:>6,} tokens  ${stats['cost']:>8.6f}")

    # Clean up
    os.unlink(temp_db.name)
    print()


async def example_budget_checking():
    """Example of checking budget before making API calls."""
    print("=" * 60)
    print("Budget Checking Example")
    print("=" * 60)

    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    temp_db.close()
    budget_manager = BudgetManager(db_path=temp_db.name)

    # Set up project with small budget
    project_id = "small-budget-project"
    await budget_manager.set_budget(
        project_id=project_id,
        monthly_limit=5000,
        name="Small Budget Project"
    )
    print(f"\nProject '{project_id}' has 5,000 token limit")

    # Use up most of the budget
    await budget_manager.track_usage(
        project_id=project_id,
        model="haiku",
        tokens=4500,
        cost=0.001
    )
    print("Used 4,500 tokens")

    # Try to check budget for new request
    estimated_tokens = 1000
    print(f"\nChecking if we can use {estimated_tokens:,} more tokens...")

    can_proceed = await budget_manager.check_budget(project_id, estimated_tokens)

    if can_proceed:
        print("✓ Budget allows this request")
    else:
        print("✗ Budget exceeded! Request would go over limit")

        # Get current usage
        usage = await budget_manager.get_usage(project_id)
        print(f"\nCurrent usage: {usage['total_tokens']:,} / {usage['limit']:,} tokens")
        print(f"Remaining: {usage['remaining']:,} tokens")

    # Clean up
    os.unlink(temp_db.name)
    print()


async def main():
    """Run all examples."""
    await example_basic_usage()
    await example_cost_comparison()
    await example_integration_with_budget_manager()
    await example_budget_checking()


if __name__ == "__main__":
    asyncio.run(main())
