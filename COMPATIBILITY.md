# AI Services API Compatibility

This service provides **full API compatibility** with the production AI service at `/Users/trent/ai-services`, allowing prototypes to switch between services by simply changing the port number.

## Quick Comparison

| Service | Port | Providers | Best For |
|---------|------|-----------|----------|
| **Production AI Service** | 8000 | OpenAI, Anthropic, Google, DeepSeek, LMStudio | Production, multi-provider, all features |
| **Claude Code API** | 8006 | Claude Code only (via subscription) | Prototyping, cost optimization, rapid development |

## Switching Between Services

**Change ONE line in your prototype:**

```python
# Production AI service
BASE_URL = "http://localhost:8000"

# Claude Code API (for prototyping)
BASE_URL = "http://localhost:8006"
```

**The API calls remain IDENTICAL!**

## Compatible Endpoints

### POST /v1/process

**Exact same format as production service:**

```python
import requests

response = requests.post(
    "http://localhost:8006/v1/process",  # ← Only difference is port!
    headers={"Authorization": "Bearer YOUR_API_KEY"},
    json={
        "provider": "anthropic",
        "model_name": "claude-3-haiku",
        "system_message": "You are a helpful assistant",
        "user_message": "Hello!",
        "max_tokens": 100
    }
)

# Response format matches exactly:
{
    "content": "Hello! How can I help you?",
    "model": "claude-3-haiku",
    "provider": "anthropic",
    "metadata": {
        "actual_model": "haiku",  # What Claude Code used
        "usage": {...},
        "cost_usd": 0.000015,
        "mapped_from": "anthropic:claude-3-haiku → claudecode:haiku"
    }
}
```

### GET /v1/providers

Lists available providers:

```bash
curl http://localhost:8006/v1/providers
```

Returns:
```json
[
    {
        "name": "claudecode",
        "available": true,
        "models": ["haiku", "sonnet", "opus"]
    },
    {
        "name": "anthropic",
        "available": true,
        "models": ["haiku", "sonnet", "opus", "claude-3-haiku", ...]
    }
]
```

### GET /v1/providers/{provider}/models

Get model capabilities:

```bash
curl http://localhost:8006/v1/providers/anthropic/models
```

## Model Mapping

When your prototype requests a specific provider/model, we map it to the best Claude equivalent:

### Anthropic Models (Direct Mapping)
| Requested | Maps To | Reason |
|-----------|---------|--------|
| claude-3-haiku, claude-3-5-haiku | `haiku` | Direct match |
| claude-3-sonnet, claude-3-5-sonnet | `sonnet` | Direct match |
| claude-3-opus, claude-3-5-opus | `opus` | Direct match |

### OpenAI Models (Capability-Based)
| Requested | Maps To | Reason |
|-----------|---------|--------|
| gpt-3.5-turbo, gpt-4o-mini | `haiku` | Fast, cheap |
| gpt-4, gpt-4o | `sonnet` | Balanced |
| gpt-4-turbo, o1-preview, o1-mini | `opus` | Most capable |

### Google Models
| Requested | Maps To | Reason |
|-----------|---------|--------|
| gemini-1.5-flash, gemini-2.0-flash | `haiku` | Fast |
| gemini-1.5-pro, gemini-2.0-pro | `sonnet` | Balanced |

### DeepSeek, LMStudio, Others
| Requested | Maps To | Reason |
|-----------|---------|--------|
| Any model | `sonnet` | Safe default |

## Supported Features

### ✅ Fully Supported
- Synchronous requests
- Message history (`messages` array)
- Legacy format (`system_message` + `user_message`)
- Max tokens, temperature
- Token usage tracking
- Cost calculation
- Budget management
- Authentication
- Rate limiting

### ⚠️ Partially Supported
- **Streaming**: Use WebSocket `/v1/stream` instead of SSE
- **Async processing**: Not implemented (use synchronous)

### ❌ Not Supported (Gracefully Ignored)
- Tool/function calling
- Multimodal content (images, video)
- Structured outputs (JSON schema)
- Memory management
- Multiple provider selection (Claude Code only)

When unsupported features are requested, they are logged but the request proceeds without them.

## Example: Switching a Chatbot

**Original code (production service):**
```python
import requests

API_KEY = "your_key"
BASE_URL = "http://localhost:8000/v1"

def chat(message):
    response = requests.post(
        f"{BASE_URL}/process",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "provider": "openai",
            "model_name": "gpt-4",
            "user_message": message
        }
    )
    return response.json()["content"]
```

**Switch to Claude Code (ONE line change):**
```python
import requests

API_KEY = "your_key"
BASE_URL = "http://localhost:8006/v1"  # ← ONLY CHANGE!

def chat(message):
    response = requests.post(
        f"{BASE_URL}/process",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "provider": "openai",        # Will map to Claude
            "model_name": "gpt-4",       # Will map to sonnet
            "user_message": message
        }
    )
    return response.json()["content"]
```

**Result:**
- ✅ Same code
- ✅ Same API format
- ✅ Zero code changes except port
- ✅ Uses Claude Code subscription (no separate API cost)

## Cost Benefits

**Production service using OpenAI:**
- gpt-4: $0.03 per 1K input tokens
- 1000 requests × 500 tokens = $15/day

**Claude Code service:**
- sonnet via Claude Code: $0 (included in $20/month subscription)
- Same 1000 requests = $0/day
- **Savings: $15/day = $450/month!**

## When to Use Each Service

### Use Production AI Service (Port 8000) When:
- Need multiple providers (OpenAI, Google, etc.)
- Need tool/function calling
- Need multimodal (images, video)
- Need structured outputs
- Production deployment
- Need proven stability

### Use Claude Code API (Port 8006) When:
- Prototyping new features
- Cost optimization during development
- Claude is sufficient (no multi-provider needed)
- Rapid iteration
- Using Claude Code Max subscription

## Migration Path

1. **Develop on Claude Code API** (port 8006, zero cost)
2. **Test with production API** (port 8006 → 8000, one line change)
3. **Deploy with production service** (final port 8000)

**Or run both simultaneously** - prototype on 8006, production traffic on 8000!

## Testing Both Services

```bash
# Test production service
curl -X POST http://localhost:8000/v1/process \
  -H "Authorization: Bearer YOUR_KEY" \
  -d '{"provider": "openai", "model_name": "gpt-4", "user_message": "Hello"}'

# Test Claude Code service (SAME FORMAT!)
curl -X POST http://localhost:8006/v1/process \
  -H "Authorization: Bearer YOUR_KEY" \
  -d '{"provider": "openai", "model_name": "gpt-4", "user_message": "Hello"}'

# Same request format, different implementation!
```

## API Key Management

Generate API key for Claude Code service:

```python
from src.auth import AuthManager

auth = AuthManager("data/auth.db")
api_key = auth.generate_key(project_id="my-app", rate_limit=100)
print(f"API Key: {api_key}")
```

Use the same key format as production service: `cc_xxxxx`

---

**Your prototypes can now use EITHER service with zero code changes!** 🚀
