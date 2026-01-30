# Example: Multi-Agent Workflows

Chain multiple agentic tasks together to solve complex problems.

## Overview

Workflows use multiple sequential or parallel tasks:

1. **Analysis Phase** - Understand the problem
2. **Planning Phase** - Create solution plan
3. **Implementation Phase** - Execute changes
4. **Validation Phase** - Verify results

## Simple Workflow: Code Improvement

```python
from claude_code_client import ClaudeClient

client = ClaudeClient()

print("=== Phase 1: Analyze ===")
analysis = client.execute_task(
    description="Analyze src/api.py for code quality issues",
    allow_tools=["Read", "Grep"],
    allow_agents=["code-analyzer"]
)

print("Issues found:")
print(analysis.result['summary'])

print("\n=== Phase 2: Generate Fixes ===")
fixes = client.execute_task(
    description=f"""
    Based on these code quality issues:
    {analysis.result['issues']}

    Generate improved versions of the functions.
    Focus on:
    - Readability
    - Performance
    - Error handling
    """,
    allow_tools=["Read", "Write"],
    allow_agents=["code-analyzer"]
)

print("\n=== Phase 3: Generate Tests ===")
tests = client.execute_task(
    description="Generate tests for the improved code",
    allow_tools=["Read"],
    allow_agents=["test-generator"]
)

print(f"\nGenerated {len(tests.artifacts)} test files")
```

## Complex Workflow: Feature Implementation

Implement a feature end-to-end:

```python
print("=== Step 1: Design ===")
design = client.execute_task(
    description="""
    Design API endpoint for user authentication.
    Include:
    - Request/response format
    - Error handling
    - Database schema
    - Security considerations
    """,
    allow_tools=["Read"],
    allow_agents=["documentation-generator"]
)

print("\n=== Step 2: Implement ===")
implementation = client.execute_task(
    description=f"""
    Based on this design:
    {design.result['summary']}

    Implement the authentication endpoint in FastAPI.
    Include proper error handling and validation.
    """,
    allow_tools=["Read", "Write", "Edit"],
    allow_agents=["code-analyzer"]
)

print("\n=== Step 3: Test ===")
testing = client.execute_task(
    description="Generate comprehensive tests for the new auth endpoint",
    allow_tools=["Read"],
    allow_agents=["test-generator"]
)

print("\n=== Step 4: Document ===")
documentation = client.execute_task(
    description="Generate API documentation for the new endpoint",
    allow_tools=["Read"],
    allow_agents=["documentation-generator"]
)

print(f"\n✓ Implementation complete")
print(f"  Files: {len(implementation.artifacts)}")
print(f"  Tests: {len(testing.artifacts)}")
print(f"  Docs: {len(documentation.artifacts)}")
```

## Parallel Workflows

Execute independent tasks in parallel:

```python
from concurrent.futures import ThreadPoolExecutor
import time

client = ClaudeClient()

tasks = [
    {
        "name": "Analyze API",
        "description": "Analyze src/api.py for security issues",
        "agents": ["security-auditor"]
    },
    {
        "name": "Analyze Models",
        "description": "Analyze src/models.py for design issues",
        "agents": ["code-analyzer"]
    },
    {
        "name": "Analyze Database",
        "description": "Analyze src/database.py for performance",
        "agents": ["performance-analyzer"]
    }
]

def run_analysis(task):
    """Run a single analysis task."""
    result = client.execute_task(
        description=task['description'],
        allow_agents=task['agents'],
        allow_tools=["Read", "Grep"]
    )
    return {
        "name": task['name'],
        "status": result.status,
        "summary": result.result.get('summary'),
        "cost": result.usage.total_cost
    }

print("Running analyses in parallel...")
start = time.time()

with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(run_analysis, tasks))

elapsed = time.time() - start

print(f"\n✓ Completed in {elapsed:.1f} seconds\n")

for result in results:
    print(f"{result['name']}: {result['status']}")
    print(f"  Cost: ${result['cost']:.2f}")

total_cost = sum(r['cost'] for r in results)
print(f"\nTotal cost: ${total_cost:.2f}")
```

## Conditional Workflows

Use results from one task to inform the next:

```python
client = ClaudeClient()

# Phase 1: Analyze
print("Analyzing code...")
analysis = client.execute_task(
    description="Find performance bottlenecks in src/",
    allow_tools=["Read", "Grep"],
    allow_agents=["performance-analyzer"]
)

bottlenecks = len(analysis.result.get('bottlenecks', []))

# Phase 2: Decide next step based on findings
if bottlenecks > 5:
    print(f"Found {bottlenecks} bottlenecks - generating optimization plan")

    optimization = client.execute_task(
        description=f"""
        Create optimization plan for these bottlenecks:
        {analysis.result['bottlenecks']}

        Prioritize by impact and effort.
        """,
        allow_tools=["Read"],
        allow_agents=["performance-analyzer"]
    )

    # Phase 3: Implement optimizations
    print("Implementing optimizations...")
    improvements = client.execute_task(
        description=f"""
        Based on this optimization plan:
        {optimization.result['plan']}

        Generate improved versions of the code.
        """,
        allow_tools=["Read", "Write"],
        allow_agents=["code-analyzer"]
    )

    print(f"✓ Generated {len(improvements.artifacts)} optimized files")

else:
    print(f"Only {bottlenecks} bottlenecks found - no optimization needed")
```

## Error Handling in Workflows

Handle failures gracefully:

```python
def run_workflow_with_fallbacks():
    """Workflow with fallback strategies."""

    try:
        print("Step 1: Analyze security...")
        analysis = client.execute_task(
            description="Find security vulnerabilities",
            allow_agents=["security-auditor"],
            allow_tools=["Read", "Grep"],
            timeout=300
        )
    except TimeoutError:
        print("Security analysis timed out, using local scanner")
        # Fall back to local tool
        analysis = local_security_scan()

    try:
        print("Step 2: Generate fixes...")
        fixes = client.execute_task(
            description=f"Fix: {analysis.result['issues']}",
            allow_tools=["Read", "Write"],
            timeout=300
        )
    except PermissionError:
        print("Write permission required, upgrade tier")
        return False

    try:
        print("Step 3: Generate tests...")
        tests = client.execute_task(
            description="Test the fixes",
            allow_agents=["test-generator"],
            allow_tools=["Read"],
            max_cost=1.0
        )
    except CostExceededError:
        print("Test generation too expensive, using manual approach")
        tests = manual_test_generation()

    return True

success = run_workflow_with_fallbacks()
```

## Monitoring Workflow Progress

Track progress and costs:

```python
class WorkflowMonitor:
    def __init__(self):
        self.steps = []
        self.total_cost = 0

    def run_step(self, name, task_fn):
        """Run a step and track progress."""
        print(f"\n▶ {name}...")

        start = time.time()
        result = task_fn()
        elapsed = time.time() - start

        cost = result.usage.total_cost
        self.total_cost += cost

        self.steps.append({
            "name": name,
            "status": result.status,
            "duration": elapsed,
            "cost": cost,
            "artifacts": len(result.artifacts)
        })

        print(f"✓ {name} ({elapsed:.1f}s, ${cost:.2f})")
        return result

    def summary(self):
        """Print workflow summary."""
        print("\n" + "="*50)
        print("WORKFLOW SUMMARY")
        print("="*50)

        for step in self.steps:
            status_icon = "✓" if step['status'] == "completed" else "✗"
            print(f"{status_icon} {step['name']:<20} {step['duration']:>6.1f}s  ${step['cost']:>6.2f}")

        print("="*50)
        print(f"Total cost: ${self.total_cost:.2f}")
        print(f"Total time: {sum(s['duration'] for s in self.steps):.1f}s")

# Use monitor
monitor = WorkflowMonitor()

monitor.run_step("Analyze Code", lambda: client.execute_task(
    description="Analyze code quality",
    allow_agents=["code-analyzer"],
    allow_tools=["Read"]
))

monitor.run_step("Generate Tests", lambda: client.execute_task(
    description="Generate tests",
    allow_agents=["test-generator"],
    allow_tools=["Read"]
))

monitor.run_step("Generate Docs", lambda: client.execute_task(
    description="Generate documentation",
    allow_agents=["documentation-generator"],
    allow_tools=["Read"]
))

monitor.summary()
```

## Real-World Example

Complete code review workflow:

```python
def complete_code_review(repo_path):
    """Run complete code review workflow."""

    client = ClaudeClient()
    monitor = WorkflowMonitor()

    # 1. Security analysis
    security = monitor.run_step("Security Analysis", lambda: client.execute_task(
        description=f"Analyze {repo_path} for security vulnerabilities",
        allow_agents=["security-auditor"],
        allow_tools=["Read", "Grep"],
        timeout=600
    ))

    # 2. Quality analysis
    quality = monitor.run_step("Code Quality", lambda: client.execute_task(
        description=f"Analyze {repo_path} for code quality issues",
        allow_agents=["code-analyzer"],
        allow_tools=["Read", "Grep"]
    ))

    # 3. Performance analysis
    performance = monitor.run_step("Performance Analysis", lambda: client.execute_task(
        description=f"Analyze {repo_path} for performance bottlenecks",
        allow_agents=["performance-analyzer"],
        allow_tools=["Read", "Grep"]
    ))

    # 4. Generate improvements
    improvements = monitor.run_step("Generate Fixes", lambda: client.execute_task(
        description=f"""
        Generate improved code based on:
        - Security issues: {security.result['count']}
        - Quality issues: {quality.result['count']}
        - Performance issues: {performance.result['count']}
        """,
        allow_tools=["Read", "Write", "Edit"],
        timeout=600
    ))

    # 5. Generate tests
    tests = monitor.run_step("Test Generation", lambda: client.execute_task(
        description="Generate comprehensive tests for improved code",
        allow_agents=["test-generator"],
        allow_tools=["Read"]
    ))

    # 6. Generate review report
    report = monitor.run_step("Generate Report", lambda: client.execute_task(
        description="Generate comprehensive code review report",
        allow_agents=["documentation-generator"],
        allow_tools=["Read"]
    ))

    monitor.summary()

    # Save artifacts
    print("\nSaving results...")
    for result_set in [security, quality, performance, improvements, tests, report]:
        for artifact in result_set.artifacts:
            print(f"  ✓ {artifact.path}")

    return {
        "security": security,
        "quality": quality,
        "performance": performance,
        "improvements": improvements,
        "tests": tests,
        "report": report
    }

# Run the workflow
results = complete_code_review("src/")
```

## Best Practices

1. **Start simple** - Master basic workflows before complex ones
2. **Use error handling** - Workflows can fail at any step
3. **Monitor progress** - Track time and cost
4. **Parallelize when possible** - Run independent tasks together
5. **Conditional logic** - Use results to guide next steps
6. **Save artifacts** - Preserve all generated outputs
7. **Log everything** - For debugging and auditing
8. **Test workflows** - Verify with small test cases first
9. **Cost awareness** - Monitor spending throughout
10. **Document workflows** - Explain what each step does

## See Also

- [Code Analysis Example](code-analysis.md)
- [Test Generation Example](test-generation.md)
- [Documentation Generation](documentation-generation.md)
- [Agentic API Guide](../guides/agentic-api-guide.md)
