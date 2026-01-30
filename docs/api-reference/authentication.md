# Authentication

All API requests require authentication with an API key.

## Getting Your API Key

1. Sign up at https://claude.ai/api
2. Go to API Keys section
3. Click "Generate New Key"
4. Copy the key (shown only once)
5. Store securely (treat like a password)

## Using Your API Key

### HTTP Header

Recommended method. Include in `Authorization` header:

```bash
curl -X POST https://api.claude.ai/v1/chat/completions \
  -H "Authorization: Bearer sk-proj-your-key-here" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello"}]}'
```

### Query Parameter

Fallback for WebSocket or special cases:

```bash
ws://localhost:8000/v1/stream?api_key=sk-proj-your-key-here
```

### Environment Variable

```bash
export CLAUDE_API_KEY="sk-proj-your-key-here"
```

Python client will automatically use this:

```python
from claude_code_client import ClaudeClient

# Uses CLAUDE_API_KEY environment variable
client = ClaudeClient()

# Or explicit
client = ClaudeClient(api_key="sk-proj-your-key-here")
```

## API Key Security

### ✅ Do

- Store keys in environment variables
- Use `.env` files (never commit)
- Rotate keys regularly
- Use different keys per environment (dev/prod)
- Restrict key permissions to minimum needed

### ❌ Don't

- Commit keys to version control
- Expose in client-side code
- Share keys via email/chat
- Use the same key for multiple projects
- Log or print API keys

### Securing Keys in Code

```python
import os
from dotenv import load_dotenv

load_dotenv()  # Loads from .env file

api_key = os.getenv("CLAUDE_API_KEY")
if not api_key:
    raise ValueError("CLAUDE_API_KEY environment variable not set")

client = ClaudeClient(api_key=api_key)
```

### .env File Example

```
CLAUDE_API_KEY=sk-proj-your-key-here
CLAUDE_API_URL=https://api.claude.ai/v1
```

Add to `.gitignore`:

```
.env
.env.local
.env.*.local
```

## API Key Permissions

Each API key has specific permissions:

- **Tools allowed**: Which tools can be used (Read, Grep, Bash, etc.)
- **Agents allowed**: Which agents can be spawned
- **Skills allowed**: Which skills can be invoked
- **Rate limits**: Requests per minute, tokens per day
- **Budget limit**: Maximum monthly spend

Manage permissions in the [API Keys dashboard](https://claude.ai/api/keys).

## Permission Tiers

### Free

- Tools: Read, Grep (read-only)
- Agents: None
- Rate limit: 10 requests/minute
- Budget: $0.10/month
- Timeout: 60 seconds

### Pro

- Tools: Read, Grep, Bash, Edit, Write
- Agents: Standard agents
- Rate limit: 100 requests/minute
- Budget: $1.00/month
- Timeout: 300 seconds (5 minutes)

### Enterprise

- Tools: All
- Agents: All
- Skills: All
- Rate limit: Custom
- Budget: Custom
- Timeout: Custom

Request Enterprise tier on your [account page](https://claude.ai/account).

## Error Responses

### 401 Unauthorized - Missing Key

```json
{
  "error": {
    "type": "authentication_error",
    "message": "Missing Authorization header"
  }
}
```

### 401 Unauthorized - Invalid Key

```json
{
  "error": {
    "type": "authentication_error",
    "message": "Invalid API key"
  }
}
```

### 403 Forbidden - Insufficient Permissions

```json
{
  "error": {
    "type": "permission_error",
    "message": "Tool 'Bash' is not allowed for this API key"
  }
}
```

### 429 Rate Limited

```json
{
  "error": {
    "type": "rate_limit_error",
    "message": "Rate limit exceeded. Reset in 60 seconds."
  }
}
```

## Revoking Keys

If a key is compromised:

1. Go to [API Keys dashboard](https://claude.ai/api/keys)
2. Find the key
3. Click "Revoke"
4. Generate a new key
5. Update your applications

Revoked keys stop working immediately.

## Rate Limiting

The API enforces rate limits per API key:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1672531200
```

When rate limited (429 response):

```python
import time
from claude_code_client import RateLimitError

while True:
    try:
        response = client.complete("...")
        break
    except RateLimitError as e:
        # Back off and retry
        time.sleep(60)
```

## Token Budget

Track token usage and costs:

```python
response = client.complete("Test")

print(f"Tokens: {response.usage.total_tokens}")
print(f"Cost: ${response.usage.cost:.4f}")
```

Set budgets to prevent overspend:

```python
result = client.execute_task(
    description="Analyze code",
    max_cost=1.0  # Stop if exceeds $1.00
)
```

## Monitoring Usage

View usage on [API Keys dashboard](https://claude.ai/api/keys):

- Requests this month
- Tokens used
- Cost to date
- Rate limit status

## Support

Issues with authentication?

- Check your API key is valid
- Verify it's not revoked
- Confirm it has required permissions
- Check rate limit status
- Contact support: support@claude.ai
