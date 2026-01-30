# Feature Wish List for Claude Code API Service

Here's my wish list for building the Claude Code API Service. Prioritize based on dependencies. Run tests after each feature.

## Core Infrastructure (Wave 1 - Build First)

### 1. Worker Pool Manager
**Location**: `src/worker_pool.py`

Create a robust worker pool manager for handling Claude CLI subprocesses:
- Process pool with configurable max workers (default 5)
- `submit(prompt, model, project_id)` → returns task_id
- `get_result(task_id, timeout=30)` → returns completion + usage
- `kill(task_id)` → terminates worker
- PID tracking for all active workers
- Queue system when all workers are busy
- Timeout handling (30s default)
- Automatic cleanup of completed workers
- Process health monitoring

**Implementation details**:
- Use subprocess.Popen for Claude CLI invocation
- Read prompt into variable, pass as argument (preserves TTY)
- Command: `claude -p "$(cat prompt.txt)" --model {model} --output-format json`
- Parse JSON output for token usage
- Store results in temp files per task

**Tests**:
- test_submit_task()
- test_get_result()
- test_timeout_handling()
- test_worker_cleanup()
- test_concurrent_workers()

---

### 2. Model Auto-Router
**Location**: `src/model_router.py`

Intelligent model selection based on task complexity and budget:
- `auto_select_model(prompt, context_size, budget_remaining)` → returns model name
- Analyzes prompt complexity (length, keywords, structure)
- Routes simple tasks to Haiku (8x cheaper)
- Routes medium tasks to Sonnet
- Routes complex tasks to Opus
- Considers remaining budget (if low, prefer Haiku)

**Routing heuristics**:
- Prompt < 100 chars + simple keywords → Haiku
- Context > 10k tokens → Opus (best for large context)
- Keywords like "analyze", "architect", "debug" → Sonnet
- Budget < 1000 tokens remaining → Haiku only
- Default → Sonnet

**Tests**:
- test_simple_task_routes_to_haiku()
- test_complex_task_routes_to_sonnet()
- test_large_context_routes_to_opus()
- test_low_budget_forces_haiku()

---

### 3. Budget Manager
**Location**: `src/budget_manager.py`

Per-project budget tracking and enforcement:
- SQLite database: `budgets.db`
- Tables: `projects`, `usage_log`
- `check_budget(project_id, estimated_tokens)` → bool
- `track_usage(project_id, model, tokens, cost)` → void
- `get_usage(project_id, period='month')` → usage stats
- `set_budget(project_id, monthly_limit)` → void
- Budget exceeded alerts
- Usage analytics (by project, by model, by time)

**Database schema**:
```sql
CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    name TEXT,
    monthly_token_limit INTEGER,
    created_at TIMESTAMP
);

CREATE TABLE usage_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT,
    model TEXT,
    tokens INTEGER,
    cost_usd REAL,
    timestamp TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
```

**Tests**:
- test_check_budget_allows_within_limit()
- test_check_budget_blocks_over_limit()
- test_track_usage()
- test_get_usage_stats()

---

## API Endpoints (Wave 2 - Depends on Wave 1)

### 4. REST API Endpoints
**Location**: `src/api.py`

Complete REST API with OpenAPI documentation:

**Endpoints**:

```python
POST /v1/chat/completions
Request:
{
  "model": "auto|haiku|sonnet|opus",
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."}
  ],
  "project_id": "string",
  "max_tokens": 1000,
  "temperature": 0.7
}
Response:
{
  "id": "cmpl_xxx",
  "choices": [{
    "message": {"role": "assistant", "content": "..."},
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 150,
    "total_tokens": 175,
    "cost_usd": 0.000044
  }
}

POST /v1/batch
Request:
{
  "requests": [
    {"model": "haiku", "prompt": "Task 1"},
    {"model": "haiku", "prompt": "Task 2"}
  ],
  "parallel": true,
  "project_id": "string"
}
Response:
{
  "results": [...],
  "total_tokens": 500,
  "total_cost": 0.0002
}

GET /v1/usage?project_id=xxx&period=month
Response:
{
  "project_id": "xxx",
  "period": "month",
  "total_tokens": 15000,
  "total_cost": 0.45,
  "by_model": {
    "haiku": {"tokens": 10000, "cost": 0.0025},
    "sonnet": {"tokens": 5000, "cost": 0.015}
  }
}

POST /v1/route
Request: {"task_description": "...", "context_size": 500}
Response: {"recommended_model": "haiku", "reasoning": "..."}
```

**Pydantic models** for request/response validation
**Error handling** with proper HTTP status codes
**Rate limiting** per project
**API key authentication** via Bearer tokens

**Tests**:
- test_chat_completion()
- test_batch_processing()
- test_usage_endpoint()
- test_route_endpoint()
- test_authentication()
- test_rate_limiting()

---

### 5. Token Tracking
**Location**: `src/token_tracker.py`

Parse Claude CLI output and track usage:
- Parse `--output-format json` from Claude CLI
- Extract `usage.input_tokens`, `usage.output_tokens`
- Calculate costs based on model pricing
- Store in usage_log database
- Aggregate by project, model, timeframe
- Export usage reports (CSV, JSON)

**Model pricing** (per 1K tokens):
- Haiku: $0.00025
- Sonnet: $0.003
- Opus: $0.015

**Tests**:
- test_parse_claude_output()
- test_calculate_cost()
- test_store_usage()
- test_aggregate_usage()

---

### 6. Redis Integration
**Location**: `src/cache.py`

Caching and queue management:
- Redis connection pool
- Request queue (when workers busy)
- Response caching (identical prompts)
- Session state (for WebSocket)
- Cache invalidation
- TTL management (responses: 1 hour, sessions: 24 hours)

**Functions**:
- `cache_response(prompt, response, ttl=3600)`
- `get_cached_response(prompt)`
- `queue_request(request_data)`
- `dequeue_request()`
- `store_session(session_id, data)`
- `get_session(session_id)`

**Tests**:
- test_cache_and_retrieve()
- test_cache_expiration()
- test_queue_operations()
- test_session_management()

---

## Advanced Features (Wave 3 - Depends on Wave 2)

### 7. WebSocket Streaming
**Location**: `src/websocket.py`

Real-time streaming responses:

```python
# WebSocket endpoint
@app.websocket("/v1/stream")
async def websocket_endpoint(websocket: WebSocket):
    # Accept connection
    # Receive request
    # Spawn Claude CLI
    # Stream tokens as they arrive
    # Send usage stats on completion
```

**Protocol**:
```json
// Client → Server
{
  "type": "chat",
  "model": "sonnet",
  "messages": [...]
}

// Server → Client (streaming)
{"type": "token", "content": "Hello"}
{"type": "token", "content": " world"}
{"type": "done", "usage": {...}}
```

**Tests**:
- test_websocket_connection()
- test_streaming_response()
- test_websocket_error_handling()

---

### 8. Authentication Middleware
**Location**: `src/auth.py`

API key management and validation:
- API key generation
- Bearer token validation
- Per-key rate limiting
- Key revocation
- SQLite table: `api_keys`

**Schema**:
```sql
CREATE TABLE api_keys (
    key TEXT PRIMARY KEY,
    project_id TEXT,
    rate_limit INTEGER,  -- requests per minute
    created_at TIMESTAMP,
    last_used_at TIMESTAMP,
    revoked BOOLEAN
);
```

**Middleware**:
- Validate `Authorization: Bearer xxx` header
- Check key is not revoked
- Enforce rate limits
- Update last_used_at

**Tests**:
- test_valid_key_accepted()
- test_invalid_key_rejected()
- test_rate_limiting()
- test_revoked_key_rejected()

---

### 9. Python Client Library
**Location**: `client/claude_client.py`

Easy-to-use Python client:

```python
from claude_code_api import ClaudeClient

client = ClaudeClient(
    base_url="http://localhost:8080",
    api_key="xxx",
    project_id="my-app"
)

# Simple completion
response = client.complete("Explain async/await", model="auto")
print(response.content)

# Streaming
for token in client.stream("Write a story"):
    print(token, end='')

# Batch processing
results = client.batch([
    "Task 1",
    "Task 2",
    "Task 3"
], parallel=True)

# Usage stats
usage = client.get_usage(period='month')
print(f"Tokens: {usage.total_tokens}")
```

**Features**:
- Sync and async support
- Automatic retries
- Error handling
- Type hints
- Comprehensive docstrings

**Tests**:
- test_client_complete()
- test_client_stream()
- test_client_batch()
- test_client_usage()
- test_async_client()

---

### 10. Documentation & Examples
**Location**: `docs/`

Comprehensive documentation:
- API reference (OpenAPI/Swagger)
- Client library guide
- Integration examples:
  - Chatbot UI integration
  - Code analysis tool
  - Batch document processor
  - Multi-agent workflow
- Deployment guide:
  - Docker setup
  - Environment variables
  - Configuration options
- Architecture diagrams
- Cost optimization tips

**Files**:
- `docs/API.md` - API reference
- `docs/CLIENT.md` - Client library guide
- `docs/EXAMPLES.md` - Integration examples
- `docs/DEPLOYMENT.md` - Deployment guide
- `docs/ARCHITECTURE.md` - System architecture
- `examples/chatbot/` - Chatbot example
- `examples/code_analyzer/` - Code tool example
- `docker-compose.yml` - Docker setup

**Tests**:
- Validate all code examples run successfully
- Test Docker deployment works

---

## Testing Requirements

All features MUST include:
- Unit tests with pytest
- Integration tests where applicable
- Minimum 80% code coverage
- All tests must pass before merge
- Type hints for all functions
- Docstrings for all public APIs

## Git Workflow

- Each feature on its own branch: `feature/INIT-XXX-description`
- Checkpoint commits as work progresses
- Run `pytest` before marking complete
- Auto-merge to main on passing tests
- Rollback on test failures

## Success Criteria

- [ ] All 10 features implemented and tested
- [ ] Main branch stable with passing tests
- [ ] API documentation complete
- [ ] At least one working integration example
- [ ] Docker deployment functional
- [ ] Cost optimization validated (60%+ savings vs direct API)

---

**Now go build it!** 🚀
