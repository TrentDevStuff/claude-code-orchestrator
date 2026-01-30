# Example: Automated Test Generation

Automatically generate test cases for your code.

## Overview

Use the agentic API with the test-generator agent to create:
- Unit tests
- Integration tests
- Edge case tests
- Mocking strategies

## Quick Start

```python
from claude_code_client import ClaudeClient

client = ClaudeClient()

result = client.execute_task(
    description="""
    Generate comprehensive test cases for src/models.py User class.
    Include unit tests for:
    - Initialization
    - Validation
    - Method calls
    - Edge cases
    """,
    allow_tools=["Read"],
    allow_agents=["test-generator"]
)

# Save generated tests
for artifact in result.artifacts:
    if "test" in artifact.path:
        print(f"Generated: {artifact.path}")
```

## Step-by-Step

### Step 1: Analyze Code

```python
result = client.execute_task(
    description="Read src/models.py and identify all classes and methods needing tests",
    allow_tools=["Read"]
)
```

### Step 2: Generate Tests

```python
result = client.execute_task(
    description="""
    Generate pytest test cases for src/models.py.
    Use fixtures for setup.
    Include mocking for database calls.
    Aim for >80% code coverage.
    """,
    allow_tools=["Read"],
    allow_agents=["test-generator"]
)
```

### Step 3: Integrate into Test Suite

```python
result = client.execute_task(
    description="""
    Generate test_api.py for src/api.py with:
    - Pytest fixtures
    - Mock database
    - Test all endpoints
    - Test error cases
    - Use HTTPTestClient
    """,
    allow_tools=["Read"],
    allow_agents=["test-generator"]
)

# Save to tests/ directory
for artifact in result.artifacts:
    if artifact.path.endswith('.py'):
        with open(f"tests/{artifact.path}", 'w') as f:
            # Save generated test file
            print(f"Saved test: tests/{artifact.path}")
```

## Advanced Example

### Generate Tests for Multiple Files

```python
import glob

client = ClaudeClient()
python_files = glob.glob("src/**/*.py", recursive=True)

for py_file in python_files:
    # Generate test for each file
    result = client.execute_task(
        description=f"""
        Generate comprehensive pytest tests for {py_file}.
        - Test all classes
        - Test all public methods
        - Include edge cases
        - Use mocks for external calls
        - Write docstrings for each test
        """,
        allow_tools=["Read"],
        allow_agents=["test-generator"],
        timeout=300
    )

    if result.status == "completed":
        # Save generated tests
        test_name = py_file.replace("src/", "tests/test_")
        for artifact in result.artifacts:
            print(f"Generated: {test_name}")
```

### Generate Integration Tests

```python
result = client.execute_task(
    description="""
    Generate integration test cases that:
    1. Start a test database
    2. Create API test client
    3. Test full user flows:
       - User registration
       - Login
       - Create post
       - Like post
       - Delete account
    4. Verify database state after each operation
    """,
    allow_tools=["Read", "Grep"],
    allow_agents=["test-generator"]
)
```

## CI/CD Integration

### GitHub Actions

Create `.github/workflows/test-generation.yml`:

```yaml
name: Generate Tests

on:
  pull_request:
    paths:
      - 'src/**'

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install claude-code-client pytest

      - name: Generate tests
        env:
          CLAUDE_API_KEY: ${{ secrets.CLAUDE_API_KEY }}
        run: |
          python -c "
          from claude_code_client import ClaudeClient
          client = ClaudeClient()
          result = client.execute_task(
              description='Generate tests for new code in src/',
              allow_agents=['test-generator'],
              allow_tools=['Read']
          )
          "

      - name: Run tests
        run: pytest tests/ -v

      - name: Check coverage
        run: pytest tests/ --cov=src --cov-report=term
```

## Coverage Analysis

Generate tests to improve coverage:

```python
import subprocess
import json

# Run coverage analysis
result = subprocess.run(
    ["pytest", "tests/", "--cov=src", "--cov-report=json"],
    capture_output=True
)

# Find uncovered lines
with open(".coverage.json") as f:
    coverage = json.load(f)
    uncovered_files = [
        f for f, data in coverage["files"].items()
        if data["summary"]["percent_covered"] < 80
    ]

# Generate tests for uncovered code
for file in uncovered_files[:3]:  # Limit to 3 files
    result = client.execute_task(
        description=f"""
        Generate additional tests for {file} to improve coverage.
        Focus on branches and edge cases not yet covered.
        """,
        allow_tools=["Read"],
        allow_agents=["test-generator"]
    )
```

## Common Test Patterns

### Mock External Services

```python
# Request to generator
description = """
Generate tests for src/api.py that:
- Mock the database connection
- Mock external API calls
- Use unittest.mock.patch
- Test error cases when services are down
"""

result = client.execute_task(
    description=description,
    allow_tools=["Read"],
    allow_agents=["test-generator"]
)
```

### Test Error Handling

```python
result = client.execute_task(
    description="""
    Generate tests for error handling in src/api.py:
    - 400 Bad Request
    - 401 Unauthorized
    - 404 Not Found
    - 500 Server Error
    - Database connection errors
    - Validation errors
    """,
    allow_tools=["Read"],
    allow_agents=["test-generator"]
)
```

### Performance Tests

```python
result = client.execute_task(
    description="""
    Generate performance tests for src/database.py:
    - Query response time < 100ms
    - Bulk operations
    - Connection pooling
    - Memory usage
    Use pytest-benchmark
    """,
    allow_tools=["Read"],
    allow_agents=["test-generator"]
)
```

## Best Practices

1. **Review generated tests** - AI tests need human review
2. **Run locally first** - Test on your machine before CI
3. **Combine strategies** - Use both unit and integration tests
4. **Maintain coverage** - Aim for >80% code coverage
5. **Update regularly** - Regenerate when code changes
6. **Use fixtures** - Share setup code across tests
7. **Mock external services** - Don't call real APIs in tests
8. **Test edge cases** - Generated tests should handle unusual inputs
9. **Documentation** - Add docstrings explaining test purpose
10. **Performance** - Don't let tests be slow

## Troubleshooting

### Generated Tests Don't Pass

Specify clearer requirements:

```python
result = client.execute_task(
    description="""
    Generate passing pytest tests for src/models.py that:
    - Import User, Post classes correctly
    - Use SQLAlchemy ORM patterns from existing tests
    - Match the coding style in src/
    - Use real test data structures
    """,
    allow_tools=["Read", "Grep"],
    allow_agents=["test-generator"]
)
```

### Too Many Edge Cases

Focus on important ones:

```python
result = client.execute_task(
    description="""
    Generate tests for src/utils.py functions:
    - Happy path (normal inputs)
    - Error cases (None, empty, negative)
    - Do NOT generate tests for every possible input combination
    """,
    allow_tools=["Read"],
    allow_agents=["test-generator"]
)
```

## See Also

- [Code Analysis Example](code-analysis.md)
- [Documentation Generation](documentation-generation.md)
- [Agentic API Guide](../guides/agentic-api-guide.md)
