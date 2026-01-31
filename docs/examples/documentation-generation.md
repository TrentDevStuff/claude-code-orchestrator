# Example: Automated Documentation Generation

Automatically generate API documentation from your code.

## Overview

Use the agentic API to generate:
- API endpoint documentation
- Function/class docstrings
- README files
- Architecture diagrams
- User guides

## Quick Example

```python
from client import ClaudeClient

client = ClaudeClient()

result = client.execute_task(
    description="""
    Generate comprehensive API documentation for all endpoints
    in src/api.py. Include:
    - Endpoint descriptions
    - Request/response examples
    - Error codes
    - Authentication requirements
    """,
    allow_tools=["Read"],
    allow_agents=["documentation-generator"]
)

# Save generated documentation
for artifact in result.artifacts:
    if artifact.path.endswith('.md'):
        print(f"Generated: {artifact.path}")
```

## Step-by-Step Guide

### Step 1: Analyze Source Code

```python
result = client.execute_task(
    description="Read src/api.py and generate API documentation",
    allow_tools=["Read"]
)

# Review the generated documentation
print(result.result['summary'])
```

### Step 2: Customize Documentation

Add project-specific details:

```python
result = client.execute_task(
    description=f"""
    Generate API documentation for src/api.py with:
    - Project: MyApp
    - Version: 1.0.0
    - Base URL: https://api.myapp.com
    - Authentication: Bearer tokens
    - Rate limit: 1000 requests/hour
    Include examples for common use cases.
    """,
    allow_tools=["Read"],
    allow_agents=["documentation-generator"]
)
```

### Step 3: Integrate with Build Process

Create `docs/generate.py`:

```python
from client import ClaudeClient
import os

client = ClaudeClient()

# Generate docs for each module
modules = [
    "src/api.py",
    "src/models.py",
    "src/auth.py",
    "src/database.py"
]

for module in modules:
    print(f"Generating docs for {module}...")

    result = client.execute_task(
        description=f"Generate comprehensive documentation for {module}",
        allow_tools=["Read"],
        allow_agents=["documentation-generator"],
        timeout=300
    )

    if result.status == "completed":
        for artifact in result.artifacts:
            # Save to docs directory
            dest = f"docs/generated/{os.path.basename(artifact.path)}"
            os.makedirs(os.path.dirname(dest), exist_ok=True)

            # Copy artifact
            print(f"  → {dest}")
```

### Step 4: Generate README

```python
result = client.execute_task(
    description="""
    Generate a comprehensive README.md for our Python API project.
    Include:
    - Project overview
    - Installation instructions
    - Quick start example
    - API endpoints summary
    - Configuration guide
    - Contributing guidelines
    - License
    """,
    allow_tools=["Read", "Glob"],
    allow_agents=["documentation-generator"]
)

# The README.md will be in artifacts
for artifact in result.artifacts:
    if artifact.path == "README.md":
        print(f"Generated README ({artifact.size_bytes} bytes)")
```

## Advanced Examples

### Generate Architecture Diagrams

```python
result = client.execute_task(
    description="""
    Based on src/api.py, src/models.py, and src/database.py,
    generate:
    1. System architecture diagram (Mermaid format)
    2. Database schema diagram
    3. Request flow diagram
    """,
    allow_tools=["Read"],
    allow_agents=["documentation-generator"]
)

# Look for diagram files
for artifact in result.artifacts:
    if ".mmd" in artifact.path or ".svg" in artifact.path:
        print(f"Generated diagram: {artifact.path}")
```

### Generate User Guide

```python
result = client.execute_task(
    description="""
    Create a user guide for the API with:
    - Getting started section
    - Common use cases with examples
    - Authentication setup
    - Error handling
    - Troubleshooting
    - FAQ section
    """,
    allow_tools=["Read"],
    allow_agents=["documentation-generator"]
)
```

## Continuous Documentation

### GitHub Actions Workflow

Create `.github/workflows/generate-docs.yml`:

```yaml
name: Generate Docs

on:
  push:
    paths:
      - 'src/**'
      - 'docs/generate.py'

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
        run: pip install httpx

      - name: Generate documentation
        env:
          CLAUDE_API_KEY: ${{ secrets.CLAUDE_API_KEY }}
        run: python docs/generate.py

      - name: Commit changes
        run: |
          git config user.name "docs-bot"
          git config user.email "bot@example.com"
          git add docs/generated/
          git commit -m "docs: auto-generated documentation" || true
          git push
```

## Quality Tips

1. **Add examples** - Include working code examples in generated docs
2. **Update regularly** - Regenerate when code changes
3. **Review output** - AI-generated docs need human review
4. **Maintain by hand** - Generated docs are starting points
5. **Version control** - Commit generated docs to git
6. **Supplement tools** - Combine with Sphinx, MkDocs, etc.

## Troubleshooting

### Generation Incomplete

If generated docs are incomplete, be more specific:

```python
# Instead of vague description
description="Generate docs"

# Be specific
description="""
Generate API documentation including:
- All GET endpoints with request/response examples
- All POST endpoints with payload examples
- All error responses with codes
- Authentication flow
"""
```

### Cost Too High

Limit scope to reduce tokens:

```python
result = client.execute_task(
    description="Generate docs for api.py endpoints only",
    allow_tools=["Read"],
    max_cost=1.0
)
```

## Combining with MkDocs

Integrate generated docs with MkDocs:

```bash
# Generate docs
python docs/generate.py

# Build site
mkdocs build

# Deploy
mkdocs gh-deploy
```

Update `mkdocs.yml`:

```yaml
docs_dir: docs
site_name: MyApp API

nav:
  - Home: index.md
  - Generated:
    - API: generated/api.md
    - Models: generated/models.md
    - Auth: generated/auth.md
```

See [deployment guide](../deployment/docker-compose.md) for more.
