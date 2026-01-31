# Agentic API Guide

Complete guide to using the Claude Code agentic task execution API.

## What is Agentic Task Execution?

Agentic tasks let Claude autonomously solve complex problems by:

1. **Planning** - Breaking down the task
2. **Using tools** - Read files, search code, run commands
3. **Iterating** - Analyzing results and refining
4. **Generating artifacts** - Creating files and reports

Unlike simple completions which just generate text, agentic tasks can take action.

## When to Use Agentic vs Simple API

### Use Simple Completions For:
- Quick answers
- Content generation
- Explanations
- Creative writing

```python
response = client.complete("Explain quantum computing")
```

### Use Agentic Tasks For:
- Code analysis
- Documentation generation
- Test generation
- Automation
- Multi-step workflows

```python
result = client.execute_task(
    description="Analyze our API for security vulnerabilities"
)
```

## Basic Usage

### Simple Task

```python
from client import ClaudeClient

client = ClaudeClient()

result = client.execute_task(
    description="Count the number of Python files in src/"
)

print(f"Status: {result.status}")
print(f"Result: {result.result}")
print(f"Cost: ${result.usage.total_cost:.4f}")
```

### Task with Tools

Control which tools are available:

```python
result = client.execute_task(
    description="Find all security issues in src/api.py",
    allow_tools=["Read", "Grep"],
    timeout=300
)
```

### Task with Agents

Spawn specialized agents:

```python
result = client.execute_task(
    description="Generate comprehensive test cases for User model",
    allow_agents=["test-generator"],
    allow_tools=["Read"]
)

print(f"Generated artifacts: {len(result.artifacts)}")
for artifact in result.artifacts:
    print(f"  - {artifact.path}")
```

### Task with Skills

Invoke data processing skills:

```python
result = client.execute_task(
    description="Find semantically similar text in our codebase",
    allow_skills=["semantic-text-matcher"],
    allow_tools=["Read", "Grep"]
)
```

## Discovering Available Agents & Skills

Before using agents and skills, discover what's available in your `~/.claude/` directory.

### Using the CLI

```bash
# List all agents
claude-api agents list --key YOUR_API_KEY

# Search for specific agents
claude-api agents search workflow --key YOUR_API_KEY

# Get detailed information
claude-api agents info company-workflow-analyst --key YOUR_API_KEY

# List all skills
claude-api skills list --key YOUR_API_KEY

# Search skills
claude-api skills search text --key YOUR_API_KEY
```

### Using the API

```python
import requests

response = requests.get(
    "http://localhost:8006/v1/capabilities",
    headers={"Authorization": "Bearer YOUR_API_KEY"}
)

capabilities = response.json()

# List agent names
print("Available agents:")
for agent in capabilities['agents']:
    print(f"  - {agent['name']} ({agent['model']})")

# List skill names
print("\nAvailable skills:")
for skill in capabilities['skills']:
    print(f"  - {skill['name']}")
```

### Finding the Right Agent

Use the search feature to find agents by capability:

```bash
# Find workflow-related agents
claude-api agents search workflow --key YOUR_API_KEY

# Find security agents
claude-api agents search security --key YOUR_API_KEY

# Find documentation agents
claude-api agents search doc --key YOUR_API_KEY
```

Then use the agent name in your task:

```python
result = client.execute_task(
    description="Extract workflow from meeting transcript",
    allow_agents=["company-workflow-analyst"],
    allow_tools=["Read"]
)
```

## Available Tools

| Tool | Use Case | Limitations |
|------|----------|------------|
| **Read** | Read file contents | Reads single files |
| **Grep** | Search with regex | Pattern matching only |
| **Bash** | Run shell commands | Sandboxed, no network |
| **Edit** | Modify files in place | Text editing only |
| **Write** | Create new files | Creates in working dir |
| **Glob** | Find files by pattern | Pattern matching |

Example usage:

```python
result = client.execute_task(
    description="Find all TODO comments in Python files",
    allow_tools=["Glob", "Grep"],
    context={"file_pattern": "**/*.py"}
)
```

## Available Agents

Agents are specialized AI workers for specific tasks:

| Agent | Specialization | Output |
|-------|-----------------|--------|
| **security-auditor** | Security vulnerability detection | Security report |
| **documentation-generator** | Auto-generate docs | Markdown files |
| **test-generator** | Generate test cases | Python test files |
| **code-analyzer** | Code quality analysis | Analysis report |
| **performance-analyzer** | Find bottlenecks | Performance report |

Use agents for complex, specialized tasks:

```python
# Security analysis with specialized agent
result = client.execute_task(
    description="Find SQL injection vulnerabilities",
    allow_agents=["security-auditor"],
    allow_tools=["Read", "Grep"]
)

# Test generation with specialized agent
result = client.execute_task(
    description="Generate tests for models.py",
    allow_agents=["test-generator"],
    allow_tools=["Read"]
)
```

## Available Skills

Skills are data processing components:

| Skill | Function | Output |
|-------|----------|--------|
| **semantic-text-matcher** | Find similar text | Similarity scores |
| **entity-mapper** | Normalize entities | Standardized IDs |
| **decision-framework** | Make decisions | Decisions + confidence |

Example:

```python
result = client.execute_task(
    description="Find duplicate function definitions",
    allow_skills=["semantic-text-matcher"],
    allow_tools=["Grep"]
)
```

## Execution Flow

### 1. Submit Task

```python
result = client.execute_task(
    description="Analyze code",
    allow_tools=["Read", "Grep"],
    timeout=300,
    max_cost=1.0
)
```

### 2. Claude Plans

Claude analyzes the task and plans steps.

### 3. Iterative Execution

Claude executes steps iteratively:
- Uses tools to gather information
- Analyzes results
- Refines approach
- Generates artifacts

### 4. Complete

Returns final results with:
- Execution summary
- Generated artifacts
- Token usage & cost
- Full execution log

## Streaming Results

Stream task execution in real-time:

```python
for event in client.stream_task(
    description="Analyze code",
    allow_tools=["Read"]
):
    if event["type"] == "thinking":
        print(f"🤔 {event['content'][:80]}...")

    elif event["type"] == "tool_call":
        print(f"🔧 Calling {event['tool']}")

    elif event["type"] == "tool_result":
        print(f"✓ {event['tool']} completed")

    elif event["type"] == "result":
        print(f"✅ Done!")
        break
```

## Analyzing Results

### Status

```python
if result.status == "completed":
    print("Task completed successfully")
elif result.status == "timeout":
    print("Task exceeded timeout")
elif result.status == "failed":
    print("Task failed with error")
```

### Summary

```python
print(f"Summary: {result.result['summary']}")
```

### Artifacts

```python
for artifact in result.artifacts:
    print(f"{artifact.path} ({artifact.size_bytes} bytes)")
    print(f"  Type: {artifact.type}")
    print(f"  Created: {artifact.created_at}")
```

### Execution Log

```python
for entry in result.execution_log:
    print(f"{entry.timestamp}: {entry.action}")
    if entry.status == "error":
        print(f"  Error: {entry.error}")
```

### Cost

```python
print(f"Total cost: ${result.usage.total_cost:.4f}")
print(f"Tokens: {result.usage.total_tokens}")
print(f"  Input: {result.usage.input_tokens}")
print(f"  Output: {result.usage.output_tokens}")
```

## Common Patterns

### Code Analysis

```python
result = client.execute_task(
    description="Find security vulnerabilities in src/api.py",
    allow_tools=["Read", "Grep"],
    allow_agents=["security-auditor"],
    max_cost=2.0,
    timeout=300
)

print(result.result['issues'])
```

### Documentation Generation

```python
result = client.execute_task(
    description="Generate API documentation for all endpoints in src/api.py",
    allow_tools=["Read"],
    allow_agents=["documentation-generator"]
)

for artifact in result.artifacts:
    print(f"Generated: {artifact.path}")
```

### Test Generation

```python
result = client.execute_task(
    description="Generate comprehensive test cases for User model",
    allow_tools=["Read"],
    allow_agents=["test-generator"]
)

for artifact in result.artifacts:
    if artifact.path.endswith(".py"):
        print(f"Test file: {artifact.path}")
```

### Code Refactoring

```python
result = client.execute_task(
    description="Refactor database queries for better performance in src/db.py",
    allow_tools=["Read", "Grep", "Edit"],
    allow_agents=["performance-analyzer"],
    timeout=600
)
```

## Cost Management

### Estimate Before Running

```python
# Estimate based on description length and tools
desc_tokens = len(description) / 4  # Rough estimate
tools_tokens = 500 * len(allow_tools)  # Each tool ~500 tokens
estimated_cost = (desc_tokens + tools_tokens) * 0.00015  # Price per token
```

### Set Budget Limit

```python
result = client.execute_task(
    description="...",
    max_cost=5.00  # Fail if exceeds $5
)

if result.status == "failed" and "cost" in result.error:
    print("Cost limit exceeded")
```

### Monitor Usage

```python
result = client.execute_task(...)

if result.usage.total_cost > 1.0:
    logger.warning(f"High cost: ${result.usage.total_cost}")
```

## Error Handling

```python
from client import (
    ClaudeAPIError,
    TimeoutError,
    PermissionError,
    CostExceededError
)

try:
    result = client.execute_task(
        description="...",
        allow_tools=["Read"]
    )
except TimeoutError:
    print("Task exceeded timeout, try again or increase timeout")

except PermissionError:
    print("Tool not allowed for your API key")

except CostExceededError:
    print("Task would exceed maximum cost")

except ClaudeAPIError as e:
    print(f"API error: {e}")
```

## Best Practices

1. **Be specific** - Detailed descriptions lead to better results
   ```python
   # ❌ Vague
   description="Analyze the code"

   # ✅ Specific
   description="Find SQL injection vulnerabilities in user input handling"
   ```

2. **Set appropriate timeouts** - Balance between cost and completeness
   ```python
   timeout=300  # 5 minutes for complex tasks
   ```

3. **Use least privilege** - Only allow needed tools
   ```python
   allow_tools=["Read", "Grep"]  # Don't allow Bash if not needed
   ```

4. **Stream for feedback** - For long-running tasks
   ```python
   for event in client.stream_task(...):
       if event["type"] == "result":
           break
   ```

5. **Process artifacts** - Don't ignore generated files
   ```python
   for artifact in result.artifacts:
       with open(artifact.path, 'r') as f:
           process(f.read())
   ```

## Advanced Topics

### Multi-step Workflows

Chain multiple tasks:

```python
# Step 1: Analyze code
analysis = client.execute_task(
    description="Analyze src/api.py for issues",
    allow_tools=["Read", "Grep"]
)

# Step 2: Generate fixes
fixes = client.execute_task(
    description=f"Based on these issues: {analysis.result}, generate fixes",
    allow_tools=["Read", "Write"]
)
```

### Parallel Tasks

Run independent tasks concurrently:

```python
import concurrent.futures

tasks = [
    "Analyze api.py for security",
    "Analyze models.py for performance",
    "Analyze utils.py for quality"
]

with concurrent.futures.ThreadPoolExecutor() as executor:
    results = list(executor.map(
        lambda desc: client.execute_task(description=desc),
        tasks
    ))
```

### Conditional Logic

```python
result = client.execute_task(
    description="Find TODOs in code"
)

if len(result.result['todos']) > 10:
    follow_up = client.execute_task(
        description="Prioritize the TODOs by importance"
    )
```
