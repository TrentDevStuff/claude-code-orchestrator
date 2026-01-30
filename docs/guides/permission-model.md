# Permission Model

Understanding API key permissions and access control.

## Overview

Each API key has specific permissions controlling:

- **Tools** - Which tools can be used (Read, Grep, Bash, etc.)
- **Agents** - Which agents can be spawned
- **Skills** - Which skills can be invoked
- **Resource limits** - Timeouts, costs, rate limits

## Permission Tiers

### Free Tier

Good for getting started and testing.

**Tools:**
- Read (read-only)
- Grep (search only)

**Agents:** None

**Limits:**
- Rate limit: 10 requests/minute
- Timeout: 60 seconds
- Budget: $0.10/month
- Max task cost: $0.01

**Use cases:**
- Learning the API
- Small one-off tasks
- Testing

### Pro Tier

Good for regular usage and small projects.

**Tools:**
- Read
- Grep
- Bash (execution)
- Edit
- Write

**Agents:**
- Standard agents (documentation, testing, analysis)

**Limits:**
- Rate limit: 100 requests/minute
- Timeout: 300 seconds (5 minutes)
- Budget: $1.00/month
- Max task cost: $0.50

**Use cases:**
- Production applications
- Regular code analysis
- Automated testing
- Documentation generation

### Enterprise Tier

Full access with custom limits.

**Tools:** All

**Agents:** All

**Skills:** All

**Limits:** Custom - contact sales

**Use cases:**
- High-volume applications
- Mission-critical automation
- Custom requirements
- Compliance/auditing

## Configuring Permissions

### In Dashboard

1. Go to https://claude.ai/api/keys
2. Select an API key
3. Click "Permissions"
4. Choose what to allow:

```
☑ Read files
☑ Search (Grep)
☐ Execute shell (Bash)
☑ Use documentation agent
☐ Use security agent
```

5. Save changes

### Per-Task

Request specific tools for a task:

```python
result = client.execute_task(
    description="Count Python files",
    allow_tools=["Bash"],  # Only request what you need
)
```

If key doesn't have permission, API returns 403 error:

```json
{
  "error": {
    "type": "permission_error",
    "message": "Tool 'Bash' is not allowed for this API key"
  }
}
```

## Permission Types

### Tool Permissions

Control which tools can be used:

```python
# These work
client.execute_task(description="...", allow_tools=["Read"])
client.execute_task(description="...", allow_tools=["Grep"])

# This fails if key doesn't have Bash permission
client.execute_task(description="...", allow_tools=["Bash"])

# This fails - Edit not in Free tier
client.execute_task(description="...", allow_tools=["Edit"])
```

### Agent Permissions

Control which agents can be spawned:

```python
# Works if key has permission
result = client.execute_task(
    description="...",
    allow_agents=["security-auditor"]
)

# Fails without permission
result = client.execute_task(
    description="...",
    allow_agents=["performance-analyzer"]  # May not be allowed
)
```

### Skill Permissions

Control which skills can be invoked:

```python
# If allowed
result = client.execute_task(
    description="...",
    allow_skills=["semantic-text-matcher"]
)

# If not allowed, fails
result = client.execute_task(
    description="...",
    allow_skills=["advanced-nlp-skill"]
)
```

### Resource Limits

Control usage constraints:

- **Timeout** - Maximum task duration (seconds)
- **Budget** - Monthly spending limit
- **Rate limit** - Requests per minute
- **Max cost** - Per-task cost limit

## Best Practices

### 1. Principle of Least Privilege

Only enable what's needed:

```python
# ❌ Bad: Overly permissive
result = client.execute_task(
    description="Count Python files",
    allow_tools=["Read", "Grep", "Bash", "Edit", "Write"]
)

# ✅ Good: Minimal permissions
result = client.execute_task(
    description="Count Python files",
    allow_tools=["Bash"]
)
```

### 2. Separate Keys by Purpose

Create different keys for different uses:

| Key | Permissions | Environment | Purpose |
|-----|------------|-------------|---------|
| `analyze-key` | Read, Grep | CI/CD | Code analysis |
| `generate-key` | Read, Write, Edit | CI/CD | Code generation |
| `admin-key` | All | Production | Emergency use only |

### 3. Environment-Specific Keys

Use different keys per environment:

```bash
# .env.development
CLAUDE_API_KEY=sk-proj-dev-key

# .env.production
CLAUDE_API_KEY=sk-proj-prod-key
```

```python
import os

env = os.getenv("ENVIRONMENT", "development")
api_key = os.getenv(f"CLAUDE_API_KEY_{env.upper()}")
```

### 4. Monitor Permission Errors

```python
from claude_code_client import PermissionError

try:
    result = client.execute_task(description="...")
except PermissionError as e:
    logger.warning(f"Permission denied: {e}")
    # Use fallback with allowed tools
    result = client.execute_task(
        description="...",
        allow_tools=["Read"]  # Fallback
    )
```

### 5. Request Elevated Permissions Carefully

For production tasks, request Pro or Enterprise:

```python
try:
    result = client.execute_task(
        description="Execute deploy script",
        allow_tools=["Bash"],
        timeout=600
    )
except PermissionError:
    print("Need Pro tier for this task")
    print("Visit https://claude.ai/api/pricing")
```

## Permission Inheritance

If no permissions specified, uses key's default permissions:

```python
# Uses key's configured permissions
result = client.execute_task(description="...")

# Requests specific tools (must be subset of key's permissions)
result = client.execute_task(
    description="...",
    allow_tools=["Read"]  # Must be in key's allowed tools
)
```

If you request a tool the key doesn't have, error:

```json
{
  "error": {
    "type": "permission_error",
    "message": "Tool 'Bash' not allowed. Upgrade to Pro tier."
  }
}
```

## Advanced: Wildcard Permissions

Some configurations support wildcards:

```
tools: ["Read", "Grep", "Bash"]      # Exact list
agents: ["*"]                        # All agents
skills: ["semantic-*"]               # Matching prefix
```

Check documentation for your tier.

## Compliance

### HIPAA

For HIPAA-regulated data, use Enterprise tier with:
- Compliance agreements (BAA)
- Audit logging enabled
- Encryption at rest/transit
- Access controls

```python
# Requires Enterprise + HIPAA agreement
result = client.execute_task(
    description="Analyze HIPAA data",
    # Must be HIPAA-compliant key
)
```

### GDPR

For EU data, ensure:
- Data processing agreement signed
- Tools restricted to EU servers
- Audit logging enabled

### SOC 2

For SOC 2 compliance:
- All access logged
- Regular security audits
- Encryption enforced
- Access controls documented

## Audit Logging

All permission checks are logged:

```
[2026-01-30 12:00:00] Permission check: sk-proj-abc123
  Tool requested: Bash
  Key allows: ["Read", "Grep"]
  Result: DENIED (permission_error)
```

View logs in API Keys dashboard:
1. Go to https://claude.ai/api/keys/audit
2. Filter by API key
3. See all access attempts

## Troubleshooting

### "Permission denied" Error

```json
{
  "error": {
    "type": "permission_error",
    "message": "Tool 'Bash' is not allowed for this API key"
  }
}
```

**Solutions:**
1. Check key's permissions: https://claude.ai/api/keys
2. Upgrade to Pro tier for more tools
3. Use allowed tools instead
4. Contact support if in doubt

### "Rate limit exceeded"

```json
{
  "error": {
    "type": "rate_limit_error",
    "message": "Rate limit exceeded (10/min). Reset in 60 seconds."
  }
}
```

**Solutions:**
1. Wait before retrying
2. Upgrade to Pro for higher limits
3. Implement exponential backoff
4. Batch requests efficiently

### "Budget limit exceeded"

```json
{
  "error": {
    "type": "cost_exceeded_error",
    "message": "Task would exceed monthly budget of $0.10"
  }
}
```

**Solutions:**
1. Upgrade plan for higher budget
2. Use `max_cost` parameter to prevent overruns
3. Optimize tasks to use fewer tokens
4. Monitor usage in dashboard

## Next Steps

- [Get API key](getting-started.md#getting-your-api-key)
- [Security best practices](security-best-practices.md)
- [Agentic API guide](agentic-api-guide.md)
- [Upgrade plan](https://claude.ai/pricing)
