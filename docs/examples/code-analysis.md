# Example: Automated Code Analysis

Analyze your codebase for issues, security vulnerabilities, and quality problems.

## Overview

Use the agentic API with the security-auditor agent to automatically find:
- Security vulnerabilities
- Code quality issues
- Performance bottlenecks
- Design problems

## Prerequisites

- Python 3.8+
- Claude Code API key with `security-auditor` agent permission
- `claude-code-client` installed

## Step 1: Create Analysis Script

Create `analyze_code.py`:

```python
from client import ClaudeClient
import json
import os

client = ClaudeClient()

# Analyze a specific file
result = client.execute_task(
    description="""
    Analyze src/api.py for security vulnerabilities.
    Look for:
    - SQL injection risks
    - Authentication/authorization issues
    - Sensitive data exposure
    - Unvalidated input handling
    - Missing CORS validation
    """,
    allow_tools=["Read", "Grep"],
    allow_agents=["security-auditor"],
    timeout=300,
    max_cost=2.0
)

print(f"Status: {result.status}")
print(f"\nSummary:")
print(result.result['summary'])

print(f"\nExecution Log:")
for entry in result.execution_log:
    print(f"  {entry.timestamp}: {entry.action} - {entry.status}")

print(f"\nGenerated Artifacts:")
for artifact in result.artifacts:
    print(f"  - {artifact.path} ({artifact.size_bytes} bytes)")

print(f"\nCost: ${result.usage.total_cost:.4f}")
```

## Step 2: Run Analysis

```bash
python analyze_code.py
```

Expected output:

```
Status: completed

Summary:
Found 3 security issues in src/api.py:

1. [HIGH] SQL Injection Risk (Line 145)
   The query builder concatenates user input without parameterization.
   Fix: Use prepared statements or ORM parameterized queries.

2. [MEDIUM] Missing CORS Validation (Line 267)
   CORS headers not validated against whitelist.
   Fix: Implement origin validation before setting CORS headers.

3. [LOW] Hardcoded Credentials (Line 89)
   Database password hardcoded in source.
   Fix: Move to environment variables.

Execution Log:
  2026-01-30T12:00:00Z: tool_call - success
  2026-01-30T12:00:01Z: tool_call - success
  2026-01-30T12:00:05Z: agent_spawn - success

Generated Artifacts:
  - security_audit_report.md (4521 bytes)
  - vulnerable_code_locations.json (1203 bytes)

Cost: $0.45
```

## Step 3: Review Generated Reports

The API creates detailed artifacts. Check `security_audit_report.md`:

```markdown
# Security Audit Report

**File**: src/api.py
**Date**: 2026-01-30
**Severity**: HIGH

## Summary
Found 3 security issues requiring attention.

## Issues

### 1. SQL Injection (HIGH)
**Location**: Line 145 in `query_builder()`
**Description**: User input concatenated directly into SQL query

**Vulnerable Code**:
\`\`\`python
def build_query(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return query
\`\`\`

**Fix**:
\`\`\`python
def build_query(user_id):
    query = "SELECT * FROM users WHERE id = ?"
    return (query, [user_id])
\`\`\`

...
```

## Advanced: Analyze Entire Codebase

For larger codebases, break into pieces:

```python
import glob
from concurrent.futures import ThreadPoolExecutor
from client import ClaudeClient

client = ClaudeClient()

# Get all Python files
python_files = glob.glob("src/**/*.py", recursive=True)

def analyze_file(file_path):
    """Analyze a single file."""
    result = client.execute_task(
        description=f"Analyze {file_path} for security issues",
        allow_tools=["Read", "Grep"],
        allow_agents=["security-auditor"]
    )
    return {
        "file": file_path,
        "status": result.status,
        "summary": result.result.get('summary'),
        "cost": result.usage.total_cost
    }

# Analyze all files in parallel
print(f"Analyzing {len(python_files)} files...")
with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(analyze_file, python_files))

# Aggregate results
total_cost = sum(r['cost'] for r in results)
failed_count = sum(1 for r in results if r['status'] != 'completed')

print(f"✓ Analyzed {len(results)} files")
print(f"✗ Failed: {failed_count}")
print(f"💰 Total cost: ${total_cost:.2f}")

# Show issues by severity
issues = []
for result in results:
    if 'HIGH' in result['summary']:
        issues.append({
            "file": result['file'],
            "severity": "HIGH"
        })

print(f"\nHigh-severity issues found in {len(issues)} files:")
for issue in issues:
    print(f"  - {issue['file']}")
```

## Step 4: Integrate with CI/CD

### GitHub Actions

Create `.github/workflows/security-audit.yml`:

```yaml
name: Security Audit

on: [push, pull_request]

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install httpx  # Required dependency for client

      - name: Run security audit
        env:
          CLAUDE_API_KEY: ${{ secrets.CLAUDE_API_KEY }}
        run: python analyze_code.py

      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: security-report
          path: security_audit_report.md
```

### GitLab CI

Create `.gitlab-ci.yml`:

```yaml
security_audit:
  image: python:3.11
  script:
    - pip install httpx  # Required dependency for client
    - python analyze_code.py
  artifacts:
    paths:
      - security_audit_report.md
    reports:
      # Can also integrate with GitLab SAST
```

## Handling Results

### Parse JSON Results

```python
import json

# The vulnerable_code_locations.json contains structured data
with open('vulnerable_code_locations.json', 'r') as f:
    vulnerabilities = json.load(f)

for vuln in vulnerabilities:
    print(f"{vuln['severity']}: {vuln['type']}")
    print(f"  Location: {vuln['file']}:{vuln['line']}")
    print(f"  Description: {vuln['description']}")
```

### Create Issues from Findings

```python
import json
import subprocess

# Parse vulnerabilities
with open('vulnerable_code_locations.json', 'r') as f:
    vulnerabilities = json.load(f)

# Create GitHub issues for HIGH severity
for vuln in vulnerabilities:
    if vuln['severity'] == 'HIGH':
        title = f"Security: {vuln['type']} in {vuln['file']}"
        body = f"""
Found {vuln['severity']} security issue:

**Type**: {vuln['type']}
**Location**: {vuln['file']}:{vuln['line']}
**Description**: {vuln['description']}

Fix: {vuln['fix']}
        """

        # Create issue via GitHub CLI
        subprocess.run([
            'gh', 'issue', 'create',
            '--title', title,
            '--body', body,
            '--label', 'security'
        ])
```

## Cost Optimization

### Limit Scope

```python
# Analyze only modified files
result = client.execute_task(
    description="Analyze only api.py and auth.py for security issues",
    allow_tools=["Read"],
    max_cost=0.5  # Limit cost
)
```

### Use Cached Results

```python
import hashlib

def get_file_hash(file_path):
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

# Cache analysis results
cache = {}

for file_path in python_files:
    file_hash = get_file_hash(file_path)

    if file_hash in cache:
        print(f"Using cached result for {file_path}")
        continue

    result = client.execute_task(
        description=f"Analyze {file_path}"
    )

    cache[file_hash] = result
```

## Real-World Example

Check our own repository:

```bash
# Analyze Claude Code API codebase
python -c "
from client import ClaudeClient

client = ClaudeClient()
result = client.execute_task(
    description='Find all security vulnerabilities in src/',
    allow_tools=['Read', 'Grep'],
    allow_agents=['security-auditor'],
    timeout=600
)

print('Status:', result.status)
print('Issues:', result.result['issues_found'])
print('Cost: \$', result.usage.total_cost)
"
```

## Best Practices

1. **Run regularly** - At least on every push
2. **Act on findings** - Create issues for HIGH severity
3. **Track trends** - Monitor changes over time
4. **Integrate early** - Check PRs before merge
5. **Cost awareness** - Large codebases can get expensive
6. **Combine tools** - Use security-auditor + your own linters
7. **False positives** - Review findings, not all are real issues
8. **Fix prioritization** - Address HIGH severity first

## Troubleshooting

### High Costs

Analyze fewer files or use `max_cost` parameter:

```python
result = client.execute_task(
    description="Analyze src/api.py",
    allow_tools=["Read"],
    max_cost=0.5  # Fail if exceeds $0.50
)
```

### Timeout

Break analysis into smaller pieces:

```python
# Instead of analyzing all at once
result = client.execute_task(
    description="Analyze src/",
    timeout=600
)

# Do it file by file
for file in files:
    result = client.execute_task(
        description=f"Analyze {file}",
        timeout=300
    )
```

### Permission Denied

Upgrade API key tier:

```python
# Requires Pro tier for security-auditor agent
```

See [permission model](../guides/permission-model.md) for details.
