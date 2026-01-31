# Security Best Practices

Essential security practices for using the Claude Code API safely.

## API Key Management

### Storage

- **Never commit to version control** - Use `.env` files with `.gitignore`
- **Use environment variables** - Store keys in `CLAUDE_API_KEY`
- **Use secrets management** - In production, use:
  - AWS Secrets Manager
  - Azure Key Vault
  - HashiCorp Vault
  - Kubernetes Secrets

### Rotation

- **Rotate regularly** - Every 90 days minimum
- **Revoke old keys** - Immediately after rotation
- **Different keys per environment**:
  - Development key
  - Staging key
  - Production key

### Access Control

```python
import os

api_key = os.getenv("CLAUDE_API_KEY")
if not api_key:
    raise ValueError("CLAUDE_API_KEY not set")

# Don't accept key from command line or user input
# This prevents accidental exposure
```

## Principle of Least Privilege

Grant minimum permissions needed:

```python
# ❌ Bad: Unrestricted permissions
client = ClaudeClient(api_key=key)
result = client.execute_task(
    description="...",
    allow_tools=["Read", "Grep", "Bash", "Edit", "Write"]
)

# ✅ Good: Only needed tools
result = client.execute_task(
    description="Count Python files",
    allow_tools=["Bash"]  # Only Bash needed
)
```

### API Key Permissions

Set up separate keys with specific permissions:

- **Analysis key**: Read, Grep only
- **Generation key**: Read, Write, Edit
- **Admin key**: Full access

Configure using the CLI:

```bash
claude-api keys permissions YOUR_KEY --set-profile pro
```

## Rate Limiting & Budget Enforcement

### Set Maximum Cost

```python
# Prevent runaway costs
result = client.execute_task(
    description="Analyze code",
    max_cost=5.00  # Fail if exceeds $5
)
```

### Monitor Usage

```python
response = client.complete("Test")

cost = response.usage.cost
if cost > 0.50:
    print(f"Warning: High cost request ${cost}")
```

### Rate Limiting

Implement backoff for rate limits:

```python
import time
from client import RateLimitError

def make_request_with_retry():
    for attempt in range(3):
        try:
            return client.complete("Test")
        except RateLimitError:
            wait_time = (2 ** attempt)
            print(f"Rate limited, waiting {wait_time}s")
            time.sleep(wait_time)
    raise Exception("Max retries exceeded")
```

## Input Validation

Validate all user input before sending to API:

```python
def validate_task_description(description: str) -> str:
    """Validate task description."""
    if not description:
        raise ValueError("Description required")

    if len(description) > 10000:
        raise ValueError("Description too long")

    # Prevent prompt injection
    dangerous_patterns = ["eval(", "__import__", "os.system"]
    if any(p in description for p in dangerous_patterns):
        raise ValueError("Invalid characters in description")

    return description

description = validate_task_description(user_input)
result = client.execute_task(description=description)
```

## Sandbox Isolation

The API runs tasks in isolated sandboxes. Understand limitations:

- **Filesystem isolation**: Can't access system files
- **Network isolation**: No external network access
- **Resource limits**: CPU, memory, disk limits
- **Command filtering**: Dangerous commands blocked

Therefore:

```python
# ✅ Safe: Task runs in sandbox
result = client.execute_task(
    description="Run tests",
    allow_tools=["Bash"]
)

# NOT a security risk - commands run in isolated sandbox
```

## Audit Logging

Enable audit logging for compliance:

```python
from client import ClaudeClient, AuditLogger

audit_logger = AuditLogger()

# Log all requests
@audit_logger.log_request
def make_api_call():
    response = client.complete("Test")
    return response

result = make_api_call()

# View audit logs
logs = audit_logger.get_logs(days=30)
for log in logs:
    print(f"{log['timestamp']}: {log['action']}")
```

## Secure Deployment

### Environment Variables

```bash
# .env file (never commit)
CLAUDE_API_KEY=sk-proj-...
CLAUDE_API_URL=http://localhost:8006
CLAUDE_TIMEOUT=300
CLAUDE_MAX_COST=1.0
```

### Docker Secrets

```yaml
services:
  api:
    secrets:
      - api_key
    environment:
      - CLAUDE_API_KEY_FILE=/run/secrets/api_key

secrets:
  api_key:
    file: ./secrets/api_key.txt
```

### Kubernetes Secrets

```bash
kubectl create secret generic claude-api-key \
  --from-literal=api_key=$CLAUDE_API_KEY
```

```yaml
env:
  - name: CLAUDE_API_KEY
    valueFrom:
      secretKeyRef:
        name: claude-api-key
        key: api_key
```

## HTTPS Only

Always use HTTPS in production:

```python
# Local development
client = ClaudeClient(
    base_url="http://localhost:8006",
    api_key=api_key
)

# In production, use HTTPS with a reverse proxy
```

## Error Handling

Don't expose sensitive information in errors:

```python
# ❌ Bad: Exposes API key
except ClaudeAPIError as e:
    print(f"Error with key {api_key}: {e}")

# ✅ Good: Hide sensitive details
except ClaudeAPIError as e:
    logger.error(f"API error: {e}")
    return {"error": "Request failed"}
```

## Data Protection

### PII (Personally Identifiable Information)

Don't send PII to the API unless necessary:

```python
# ❌ Bad: Sends personal data
result = client.execute_task(
    description=f"Analyze email from {user_email}: {message}"
)

# ✅ Good: Anonymous analysis
result = client.execute_task(
    description="Analyze email sentiment"
)
```

### Sensitive Data

If you must send sensitive data:

1. Encrypt before sending
2. Use dedicated keys with restrictions
3. Set tight budgets
4. Monitor access logs
5. Delete after use

## DDoS Protection

API has built-in protection:

- Rate limiting per API key
- Connection limits
- Request size limits
- Timeout enforcement

Your application should also implement:

```python
from fastapi import FastAPI
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.backends.redis import RedisBackend

app = FastAPI()

@app.post("/analyze")
@FastAPILimiter.limit("10/minute")
async def analyze(task: str):
    result = client.execute_task(description=task)
    return result
```

## Monitoring & Alerts

Set up monitoring:

```python
import logging

logger = logging.getLogger(__name__)

try:
    response = client.complete("Test")
except RateLimitError:
    logger.warning("Rate limited")
    # Alert admin
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    # Alert admin, investigate
```

## Compliance

### GDPR

- Get user consent before processing
- Allow data deletion requests
- Implement data retention policies
- Use data processing agreements

### HIPAA

- Use Enterprise tier with BAA
- Encrypt data in transit (HTTPS)
- Audit all access
- Implement access controls

### SOC 2

- Regular security audits
- Incident response plan
- Encryption at rest/transit
- Access controls & monitoring

## Security Checklist

- [ ] API key in environment variable, never in code
- [ ] HTTPS used in production
- [ ] Least privilege permissions configured
- [ ] Cost limits enforced
- [ ] Input validation implemented
- [ ] Error handling doesn't expose secrets
- [ ] Audit logging enabled
- [ ] Rate limiting in place
- [ ] PII protected or avoided
- [ ] Regular key rotation scheduled
- [ ] Security monitoring enabled
- [ ] Incident response plan exists

## Reporting Security Issues

Found a security vulnerability?

**DO NOT** open a public GitHub issue.

Open an issue at https://github.com/TrentDevStuff/claude-code-api-service/issues with:
- Description of vulnerability
- Steps to reproduce
- Potential impact
- Your name/affiliation

We'll acknowledge within 24 hours and work with you on a fix.

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [API Security Best Practices](https://cheatsheetseries.owasp.org/cheatsheets/REST_API_Security_Cheat_Sheet.html)
- [Secrets Management Guide](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
