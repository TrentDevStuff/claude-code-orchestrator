# Error Handling Guide

Comprehensive guide to handling API errors gracefully.

## Error Types

### AuthenticationError (401)

Invalid or missing API key.

```python
from claude_code_client import AuthenticationError

try:
    response = client.complete("Test")
except AuthenticationError as e:
    print("Invalid API key")
    print(f"Error: {e}")
```

**Causes:**
- Missing `CLAUDE_API_KEY` environment variable
- Revoked API key
- Expired key
- Malformed key format

**Solutions:**
1. Check key exists: `echo $CLAUDE_API_KEY`
2. Verify key at https://claude.ai/api/keys
3. Generate new key if revoked
4. Ensure key starts with `sk-proj-`

### PermissionError (403)

Tool/agent/skill not allowed for API key.

```python
from claude_code_client import PermissionError

try:
    result = client.execute_task(
        description="...",
        allow_tools=["Bash"]
    )
except PermissionError as e:
    print("Bash tool not allowed")
    # Fall back to Read-only
    result = client.execute_task(description="...", allow_tools=["Read"])
```

**Causes:**
- Tool not in key's allowed list
- Insufficient permissions tier
- Agent/skill requires upgrade

**Solutions:**
1. Use allowed tools only
2. Upgrade to Pro/Enterprise tier
3. Request specific tool in dashboard
4. Check API key permissions

### RateLimitError (429)

Too many requests in short time.

```python
from claude_code_client import RateLimitError
import time

def retry_with_backoff(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt  # Exponential backoff
            print(f"Rate limited, waiting {wait_time}s")
            time.sleep(wait_time)

response = retry_with_backoff(lambda: client.complete("Test"))
```

**Causes:**
- Exceeded requests per minute limit
- Too many concurrent connections
- Burst of requests

**Solutions:**
1. Wait before retrying
2. Implement exponential backoff
3. Upgrade to Pro for higher limits
4. Batch requests efficiently

### TimeoutError

Task exceeded time limit.

```python
from claude_code_client import TimeoutError

try:
    result = client.execute_task(
        description="Analyze large codebase",
        timeout=300  # 5 minutes
    )
except TimeoutError:
    print("Task exceeded timeout")
    # Simplify task or increase timeout
    result = client.execute_task(
        description="Analyze main API file only",
        timeout=600  # 10 minutes
    )
```

**Causes:**
- Task too complex
- Timeout too short
- Network latency
- Server overload

**Solutions:**
1. Increase timeout parameter
2. Simplify task scope
3. Break into smaller tasks
4. Retry later if server busy

### CostExceededError

Task would exceed budget limit.

```python
from claude_code_client import CostExceededError

try:
    result = client.execute_task(
        description="...",
        max_cost=1.0
    )
except CostExceededError as e:
    print(f"Would cost more than $1.00")
    print(f"Estimated cost: {e.estimated_cost}")
    # Simplify or skip task
```

**Causes:**
- Task too complex (many tokens)
- `max_cost` parameter too low
- Running expensive model (Opus)

**Solutions:**
1. Increase `max_cost` limit
2. Use simpler task
3. Use cheaper model (Haiku)
4. Simplify description

### ClaudeAPIError (Other)

Generic API error.

```python
from claude_code_client import ClaudeAPIError

try:
    response = client.complete("Test")
except ClaudeAPIError as e:
    print(f"API error: {e}")
    print(f"Error type: {e.error_type}")
    print(f"HTTP status: {e.status_code}")
```

**Solutions:**
1. Check error message
2. Review request parameters
3. Check API status: https://claude.ai/status
4. Contact support if persistent

## Handling Errors Comprehensively

```python
from claude_code_client import (
    ClaudeClient,
    AuthenticationError,
    PermissionError,
    RateLimitError,
    TimeoutError,
    CostExceededError,
    ClaudeAPIError
)

client = ClaudeClient()

try:
    result = client.execute_task(
        description="Analyze code",
        allow_tools=["Read", "Grep"],
        timeout=300,
        max_cost=1.0
    )

except AuthenticationError:
    # Handle auth errors
    print("ERROR: Invalid API key")
    exit(1)

except PermissionError as e:
    # Handle permission errors
    print(f"ERROR: Permission denied - {e}")
    print("Upgrade tier or adjust permissions")
    exit(1)

except RateLimitError:
    # Handle rate limiting with backoff
    print("WARN: Rate limited, retrying...")
    time.sleep(60)
    result = client.execute_task(description="Analyze code")

except TimeoutError:
    # Handle timeouts
    print("WARN: Task timed out, breaking into smaller pieces")
    results = []
    for file in files:
        result = client.execute_task(
            description=f"Analyze {file}",
            timeout=600
        )
        results.append(result)

except CostExceededError as e:
    # Handle cost overruns
    print(f"WARN: Cost limit reached ({e.estimated_cost})")
    print("Simplifying task...")
    result = client.execute_task(
        description="Analyze main file only",
        max_cost=2.0
    )

except ClaudeAPIError as e:
    # Generic error handling
    print(f"ERROR: API error - {e}")
    # Log and retry
    logger.error(f"API error: {e}")
    time.sleep(5)
    result = client.execute_task(description="Analyze code")
```

## Retry Strategies

### Simple Retry

```python
import time

def retry_simple(func, max_retries=3, delay=1):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(delay)

result = retry_simple(lambda: client.execute_task(...))
```

### Exponential Backoff

```python
import time
import random

def retry_exponential(func, max_retries=5):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise

            # Exponential backoff with jitter
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            print(f"Attempt {attempt + 1} failed, waiting {wait_time:.1f}s")
            time.sleep(wait_time)

result = retry_exponential(lambda: client.execute_task(...))
```

### Circuit Breaker

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = None

    def call(self, func):
        if self.is_open():
            raise Exception("Circuit breaker is open")

        try:
            result = func()
            self.reset()
            return result
        except Exception as e:
            self.record_failure()
            raise

    def is_open(self):
        if self.failures >= self.failure_threshold:
            if time.time() - self.last_failure_time < self.timeout:
                return True
            self.reset()
        return False

    def record_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()

    def reset(self):
        self.failures = 0

breaker = CircuitBreaker()
result = breaker.call(lambda: client.execute_task(...))
```

## Logging Errors

Always log errors for debugging:

```python
import logging

logger = logging.getLogger(__name__)

try:
    result = client.execute_task(description="...")

except PermissionError as e:
    logger.warning(f"Permission denied: {e}", extra={
        "api_key": "***",
        "tool": "Bash"
    })

except ClaudeAPIError as e:
    logger.error(f"API error: {e}", exc_info=True, extra={
        "status_code": e.status_code,
        "request_id": e.request_id
    })
```

Don't expose sensitive information in logs:

```python
# ❌ Bad: Exposes API key
logger.error(f"Error with key {api_key}: {e}")

# ✅ Good: Masks API key
api_key_preview = api_key[:20] + "..."
logger.error(f"Error with key {api_key_preview}: {e}")
```

## Graceful Degradation

Provide fallbacks when API fails:

```python
def analyze_code(file_path, use_api=True):
    if use_api:
        try:
            result = client.execute_task(
                description=f"Analyze {file_path}"
            )
            return result
        except (TimeoutError, ClaudeAPIError):
            logger.warning("API failed, using local analysis")

    # Fallback: local analysis
    with open(file_path, 'r') as f:
        code = f.read()
    return local_analyze(code)

result = analyze_code("src/api.py")
```

## Error Messages

Provide helpful error messages:

```python
# ❌ Bad: Cryptic
except ClaudeAPIError:
    print("Error")

# ✅ Good: Helpful and actionable
except PermissionError:
    print("""
    Tool 'Bash' is not allowed for your API key.

    Solutions:
    1. Upgrade to Pro tier: https://claude.ai/pricing
    2. Request specific tool in dashboard
    3. Use Read/Grep instead of Bash

    Need help? Contact support@claude.ai
    """)
```

## Monitoring & Alerts

Monitor error rates:

```python
from collections import defaultdict
import time

class ErrorMonitor:
    def __init__(self, alert_threshold=0.1):
        self.errors = defaultdict(int)
        self.total = 0
        self.alert_threshold = alert_threshold

    def record_error(self, error_type):
        self.errors[error_type] += 1
        self.total += 1

        error_rate = len(self.errors) / self.total if self.total > 0 else 0
        if error_rate > self.alert_threshold:
            self.alert(f"High error rate: {error_rate:.1%}")

    def alert(self, message):
        logger.critical(message)
        # Send to monitoring system

monitor = ErrorMonitor()

try:
    result = client.execute_task(...)
except Exception as e:
    monitor.record_error(type(e).__name__)
    raise
```

## Testing Error Handling

Test with mock errors:

```python
import pytest
from unittest.mock import patch
from claude_code_client import RateLimitError

@pytest.mark.asyncio
async def test_rate_limit_retry():
    """Test retry on rate limit."""
    with patch.object(client, 'execute_task') as mock:
        # First call fails, second succeeds
        mock.side_effect = [
            RateLimitError("Rate limited"),
            {"status": "completed"}
        ]

        result = retry_with_backoff(
            lambda: client.execute_task(description="...")
        )

        assert result["status"] == "completed"
        assert mock.call_count == 2
```

## Common Error Scenarios

### Scenario: Network Timeout

```python
try:
    result = client.execute_task(..., timeout=300)
except TimeoutError:
    # Network was slow, retry with longer timeout
    result = client.execute_task(..., timeout=600)
```

### Scenario: Insufficient Permissions

```python
try:
    result = client.execute_task(
        description="...",
        allow_tools=["Bash"]
    )
except PermissionError:
    # Bash not allowed, use Read instead
    result = client.execute_task(
        description="...",
        allow_tools=["Read"]
    )
```

### Scenario: Cost Overrun

```python
try:
    result = client.execute_task(
        description="Analyze large codebase",
        max_cost=1.0
    )
except CostExceededError:
    # Task too expensive, break it up
    results = []
    for file in split_into_chunks("src/"):
        result = client.execute_task(
            description=f"Analyze {file}",
            max_cost=0.5
        )
        results.append(result)
```

## Best Practices

1. **Always catch specific exceptions** - Don't use bare `except:`
2. **Log before re-raising** - Preserve error context
3. **Provide actionable errors** - Help users fix problems
4. **Implement retry logic** - Handle transient failures
5. **Monitor error rates** - Detect systemic issues
6. **Don't expose secrets** - Redact API keys from errors
7. **Test error paths** - Verify fallbacks work
8. **Set reasonable timeouts** - Prevent hangs
9. **Use circuit breakers** - Prevent cascading failures
10. **Document known errors** - Help users troubleshoot

## Support

Can't fix the error? Contact support:
- **Email**: support@claude.ai
- **Status**: https://claude.ai/status
- **GitHub Issues**: https://github.com/anthropics/claude-code-api/issues
