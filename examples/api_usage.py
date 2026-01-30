#!/usr/bin/env python3
"""
Example usage of Claude Code API Service endpoints.

Demonstrates:
- Single chat completion
- Batch processing
- Usage tracking
- Model routing recommendation
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8080"


def chat_completion_example():
    """Example: Single chat completion with auto model selection."""
    print("\n=== Chat Completion Example ===")

    response = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json={
            "messages": [
                {"role": "user", "content": "Explain what a REST API is in one sentence."}
            ],
            "project_id": "demo-project",
            "timeout": 30.0
        }
    )

    if response.status_code == 200:
        data = response.json()
        print(f"Model used: {data['model']}")
        print(f"Response: {data['content']}")
        print(f"Usage: {data['usage']}")
        print(f"Cost: ${data['cost']:.6f}")
    else:
        print(f"Error: {response.status_code} - {response.text}")


def batch_processing_example():
    """Example: Process multiple prompts in parallel."""
    print("\n=== Batch Processing Example ===")

    response = requests.post(
        f"{BASE_URL}/v1/batch",
        json={
            "prompts": [
                {"prompt": "What is Python?", "id": "q1"},
                {"prompt": "What is JavaScript?", "id": "q2"},
                {"prompt": "What is Rust?", "id": "q3"}
            ],
            "model": "haiku",
            "project_id": "demo-project",
            "timeout": 30.0
        }
    )

    if response.status_code == 200:
        data = response.json()
        print(f"Total: {data['total']}, Completed: {data['completed']}, Failed: {data['failed']}")
        print(f"Total cost: ${data['total_cost']:.6f}")
        print(f"Total tokens: {data['total_tokens']}")

        for result in data['results']:
            if result['status'] == 'completed':
                print(f"\n{result['id']}: {result['content'][:100]}...")
            else:
                print(f"\n{result['id']}: FAILED - {result['error']}")
    else:
        print(f"Error: {response.status_code} - {response.text}")


def usage_tracking_example():
    """Example: Get usage statistics for a project."""
    print("\n=== Usage Tracking Example ===")

    response = requests.get(
        f"{BASE_URL}/v1/usage",
        params={
            "project_id": "demo-project",
            "period": "month"
        }
    )

    if response.status_code == 200:
        data = response.json()
        print(f"Project: {data['project_id']}")
        print(f"Period: {data['period']}")
        print(f"Total tokens: {data['total_tokens']}")
        print(f"Total cost: ${data['total_cost']:.4f}")

        if data['limit']:
            print(f"Limit: {data['limit']} tokens")
            print(f"Remaining: {data['remaining']} tokens")
            usage_pct = (data['total_tokens'] / data['limit']) * 100
            print(f"Usage: {usage_pct:.1f}%")

        print("\nUsage by model:")
        for model, stats in data['by_model'].items():
            print(f"  {model}: {stats['tokens']} tokens, ${stats['cost']:.4f}")
    else:
        print(f"Error: {response.status_code} - {response.text}")


def model_routing_example():
    """Example: Get model routing recommendation."""
    print("\n=== Model Routing Example ===")

    test_cases = [
        {
            "prompt": "List all Python files",
            "context_size": 50,
            "description": "Simple task"
        },
        {
            "prompt": "Analyze and refactor this complex codebase architecture",
            "context_size": 5000,
            "description": "Complex task"
        },
        {
            "prompt": "Review this large codebase",
            "context_size": 15000,
            "description": "Large context"
        }
    ]

    for test in test_cases:
        response = requests.post(
            f"{BASE_URL}/v1/route",
            json={
                "prompt": test["prompt"],
                "context_size": test["context_size"],
                "project_id": "demo-project"
            }
        )

        if response.status_code == 200:
            data = response.json()
            print(f"\n{test['description']}:")
            print(f"  Prompt: \"{test['prompt'][:50]}...\"")
            print(f"  Recommended: {data['recommended_model']}")
            print(f"  Reasoning: {data['reasoning']}")
        else:
            print(f"Error: {response.status_code} - {response.text}")


def health_check():
    """Example: Check API health status."""
    print("\n=== Health Check ===")

    response = requests.get(f"{BASE_URL}/health")

    if response.status_code == 200:
        data = response.json()
        print(f"Status: {data['status']}")
        print(f"Version: {data['version']}")
        print(f"Services: {data['services']}")
    else:
        print(f"Error: {response.status_code} - {response.text}")


if __name__ == "__main__":
    print("Claude Code API Service - Example Usage")
    print("=" * 50)

    # Check if API is running
    try:
        health_check()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: API is not running!")
        print("Start the API with: python main.py")
        exit(1)

    # Run examples
    try:
        chat_completion_example()
        batch_processing_example()
        usage_tracking_example()
        model_routing_example()
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")

    print("\n" + "=" * 50)
    print("Examples complete!")
