#!/usr/bin/env python3
"""
Code Analyzer Example

Demonstrates:
- Model routing based on complexity
- Analyzing Python code files
- Using different models for different tasks
- Cost optimization strategies
- Route recommendation API
"""

import sys
sys.path.append('..')

from pathlib import Path
from client.claude_client import ClaudeClient, Model


# Sample code snippets for analysis
SAMPLE_CODE = {
    "simple": '''
def hello(name):
    """Simple greeting function"""
    return f"Hello, {name}!"

result = hello("World")
print(result)
''',

    "medium": '''
class DataProcessor:
    """Process and transform data"""

    def __init__(self, data):
        self.data = data
        self.processed = []

    def filter(self, condition):
        """Filter data based on condition"""
        self.processed = [item for item in self.data if condition(item)]
        return self

    def transform(self, func):
        """Transform processed data"""
        self.processed = [func(item) for item in self.processed]
        return self

    def get_result(self):
        """Return processed results"""
        return self.processed
''',

    "complex": '''
import asyncio
from typing import List, Optional, Callable
from dataclasses import dataclass

@dataclass
class Task:
    """Represents an async task"""
    id: str
    fn: Callable
    args: tuple
    result: Optional[any] = None

class AsyncTaskPool:
    """Manages concurrent async task execution"""

    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers
        self.tasks = []
        self.results = {}
        self.semaphore = asyncio.Semaphore(max_workers)

    async def submit(self, task: Task):
        """Submit task to pool"""
        async with self.semaphore:
            try:
                task.result = await task.fn(*task.args)
                self.results[task.id] = task.result
            except Exception as e:
                self.results[task.id] = f"Error: {e}"

    async def run_all(self, tasks: List[Task]):
        """Execute all tasks concurrently"""
        await asyncio.gather(*[self.submit(task) for task in tasks])
        return self.results
'''
}


def analyze_code_simple(client: ClaudeClient, code: str):
    """
    Simple code analysis using Haiku (fast, cheap).

    Args:
        client: Claude API client
        code: Code to analyze

    Returns:
        Analysis result
    """
    prompt = f"""
Analyze this Python code and provide:
1. Brief description of what it does
2. Any obvious bugs or issues
3. One improvement suggestion

Code:
```python
{code}
```

Keep the response concise (2-3 sentences per point).
"""

    print("Task: Simple code review")
    print(f"Model: Haiku (fast, cheap)")
    print()

    response = client.complete(prompt, model=Model.HAIKU)

    print("Analysis:")
    print(response.content)
    print()
    print(f"Stats: {response.usage.total_tokens} tokens, ${response.cost:.6f}")
    print()

    return response


def analyze_code_detailed(client: ClaudeClient, code: str):
    """
    Detailed code analysis using Sonnet (balanced).

    Args:
        client: Claude API client
        code: Code to analyze

    Returns:
        Analysis result
    """
    prompt = f"""
Perform a detailed code review of this Python code:

```python
{code}
```

Provide:
1. **Functionality**: Detailed explanation of what the code does
2. **Code Quality**: Assessment of code structure, naming, and style
3. **Potential Issues**: List any bugs, edge cases, or problems
4. **Performance**: Analysis of efficiency and optimization opportunities
5. **Best Practices**: Suggestions for improvements following Python best practices
6. **Security**: Any security considerations or vulnerabilities

Be thorough but concise.
"""

    print("Task: Detailed code review")
    print(f"Model: Sonnet (more capable)")
    print()

    response = client.complete(prompt, model=Model.SONNET)

    print("Analysis:")
    print(response.content)
    print()
    print(f"Stats: {response.usage.total_tokens} tokens, ${response.cost:.6f}")
    print()

    return response


def get_route_recommendation(client: ClaudeClient, code: str, task: str):
    """
    Get model routing recommendation for a task.

    Args:
        client: Claude API client
        code: Code snippet
        task: Description of analysis task

    Returns:
        Routing recommendation
    """
    prompt = f"Analyze this code: {task}"
    context_size = len(code.split())  # Rough token estimate

    try:
        recommendation = client.get_route_recommendation(
            prompt=prompt,
            context_size=context_size
        )

        print(f"Recommended model: {recommendation['recommended_model']}")
        print(f"Reasoning: {recommendation['reasoning']}")
        print()

        budget = recommendation['budget_status']
        print(f"Budget status:")
        print(f"  Used: {budget['total_tokens']:,} tokens (${budget['total_cost']:.4f})")
        if budget['limit']:
            print(f"  Limit: {budget['limit']:,} tokens")
            print(f"  Remaining: {budget['remaining']:,} tokens")
        print()

        return recommendation

    except Exception as e:
        print(f"Error getting recommendation: {e}")
        return None


def compare_models_for_task(client: ClaudeClient, code: str):
    """
    Compare different models for the same task.

    Args:
        client: Claude API client
        code: Code to analyze
    """
    print("=" * 70)
    print("MODEL COMPARISON FOR CODE ANALYSIS")
    print("=" * 70)
    print()

    prompt = f"""
Analyze this Python code and explain what it does:

```python
{code}
```

Provide a clear, concise explanation.
"""

    results = {}

    for model in [Model.HAIKU, Model.SONNET]:
        print(f"Using {model.value.upper()}:")
        print("-" * 70)

        response = client.complete(prompt, model=model)

        print(response.content)
        print()
        print(f"Tokens: {response.usage.total_tokens}, Cost: ${response.cost:.6f}")
        print()

        results[model.value] = {
            "tokens": response.usage.total_tokens,
            "cost": response.cost,
            "quality": len(response.content.split())  # Word count as quality proxy
        }

    # Comparison summary
    print("=" * 70)
    print("COMPARISON")
    print("=" * 70)
    print()

    haiku = results["haiku"]
    sonnet = results["sonnet"]

    print(f"Cost comparison:")
    print(f"  Haiku:  ${haiku['cost']:.6f}")
    print(f"  Sonnet: ${sonnet['cost']:.6f}")
    print(f"  Savings with Haiku: {((sonnet['cost'] - haiku['cost']) / sonnet['cost'] * 100):.1f}%")
    print()

    print(f"Response length:")
    print(f"  Haiku:  {haiku['quality']} words")
    print(f"  Sonnet: {sonnet['quality']} words")
    print()

    print(f"Recommendation:")
    if sonnet['quality'] > haiku['quality'] * 1.5:
        print("  Sonnet provides significantly more detail - worth the extra cost")
    else:
        print("  Haiku provides good value - similar quality at lower cost")
    print()


def analyze_file(client: ClaudeClient, file_path: str):
    """
    Analyze a Python file from disk.

    Args:
        client: Claude API client
        file_path: Path to Python file
    """
    path = Path(file_path)

    if not path.exists():
        print(f"Error: File not found: {file_path}")
        return

    if path.suffix != '.py':
        print(f"Error: Not a Python file: {file_path}")
        return

    print(f"Analyzing file: {path.name}")
    print()

    # Read file
    code = path.read_text()

    # Get routing recommendation
    print("Getting routing recommendation...")
    recommendation = get_route_recommendation(
        client,
        code,
        f"Perform detailed code review of {path.name}"
    )

    if recommendation:
        recommended_model = Model[recommendation['recommended_model'].upper()]
    else:
        recommended_model = Model.AUTO

    # Analyze with recommended model
    print(f"Analyzing with {recommended_model.value}...")
    print()

    prompt = f"""
Perform a code review of this Python file:

File: {path.name}

```python
{code}
```

Provide:
1. Summary of functionality
2. Code quality assessment
3. Key issues or improvements
"""

    response = client.complete(prompt, model=recommended_model)

    print("Analysis:")
    print(response.content)
    print()
    print(f"Model used: {response.model}")
    print(f"Tokens: {response.usage.total_tokens}, Cost: ${response.cost:.6f}")
    print()


def main():
    """Main entry point."""
    print("=" * 70)
    print("Claude Code API - Code Analyzer")
    print("=" * 70)
    print()

    # Initialize client
    with ClaudeClient(project_id="code-analyzer", timeout=60.0) as client:
        # Check API health
        health = client.health()
        print(f"✓ API Status: {health['status']}")
        print()

        print("Options:")
        print("  1. Simple analysis (sample code, Haiku)")
        print("  2. Detailed analysis (sample code, Sonnet)")
        print("  3. Compare models (same task, different models)")
        print("  4. Analyze Python file (with auto-routing)")
        print("  5. Get routing recommendation")
        print()

        choice = input("Select option (1-5): ").strip()
        print()

        if choice == "1":
            analyze_code_simple(client, SAMPLE_CODE["simple"])

        elif choice == "2":
            analyze_code_detailed(client, SAMPLE_CODE["complex"])

        elif choice == "3":
            compare_models_for_task(client, SAMPLE_CODE["medium"])

        elif choice == "4":
            file_path = input("Enter Python file path: ").strip()
            print()
            analyze_file(client, file_path)

        elif choice == "5":
            print("Code complexity levels:")
            print("  1. Simple")
            print("  2. Medium")
            print("  3. Complex")
            print()
            complexity = input("Select complexity (1-3): ").strip()

            complexity_map = {"1": "simple", "2": "medium", "3": "complex"}
            code_key = complexity_map.get(complexity, "medium")

            print()
            get_route_recommendation(
                client,
                SAMPLE_CODE[code_key],
                "Perform detailed code analysis"
            )

        else:
            print("Invalid choice")
            return

        # Show usage statistics
        print()
        print("=" * 70)
        print("USAGE STATISTICS")
        print("=" * 70)
        print()

        stats = client.get_usage(period="month")
        print(f"Project: {stats.project_id}")
        print(f"Total cost: ${stats.total_cost:.4f}")
        print(f"Total tokens: {stats.total_tokens:,}")
        print()

        if stats.by_model:
            print("By model:")
            for model_name, model_stats in stats.by_model.items():
                print(f"  {model_name}: ${model_stats['cost']:.4f} ({model_stats['tokens']:,} tokens)")
        print()


if __name__ == "__main__":
    main()
