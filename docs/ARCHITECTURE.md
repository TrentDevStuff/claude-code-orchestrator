# Architecture - Claude Code API Service

System architecture and component design documentation.

## System Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                         Client Applications                       │
│  (Web Apps, Mobile Apps, Scripts, Services)                      │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             │ HTTP/REST
                             │
┌────────────────────────────▼─────────────────────────────────────┐
│                      FastAPI Server (main.py)                     │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ API Router (src/api.py)                                    │ │
│  │  • POST /v1/chat/completions                               │ │
│  │  • POST /v1/batch                                          │ │
│  │  • GET  /v1/usage                                          │ │
│  │  • POST /v1/route                                          │ │
│  └────────────────────────────────────────────────────────────┘ │
└──┬────────────────┬──────────────────┬─────────────────────────┬─┘
   │                │                  │                         │
   │                │                  │                         │
   ▼                ▼                  ▼                         ▼
┌─────────────┐ ┌──────────────┐ ┌──────────────┐  ┌──────────────────┐
│ Worker Pool │ │ Model Router │ │Budget Manager│  │   Token Tracker  │
│(worker_pool │ │(model_router │ │(budget_mgr   │  │(token_tracker.py)│
│     .py)    │ │     .py)     │ │   .py)       │  │                  │
└──────┬──────┘ └──────────────┘ └──────┬───────┘  └──────────────────┘
       │                                  │
       │                                  │
       ▼                                  ▼
┌────────────────────┐           ┌────────────────┐
│  Claude CLI Procs  │           │ SQLite Database│
│  (subprocess)      │           │ (budgets.db)   │
│  • haiku workers   │           │ • Projects     │
│  • sonnet workers  │           │ • Usage logs   │
│  • opus workers    │           │ • Budgets      │
└────────────────────┘           └────────────────┘
         │
         ▼
┌────────────────────┐
│   Redis Cache      │
│  (optional)        │
│  • Prompt caching  │
│  • Rate limiting   │
└────────────────────┘
```

## Core Components

### 1. FastAPI Server (`main.py`)

**Purpose:** HTTP server and application orchestrator

**Responsibilities:**
- Serve REST API endpoints
- Manage application lifecycle (startup/shutdown)
- Initialize and coordinate services
- Handle CORS, middleware

**Key Code:**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    worker_pool = WorkerPool(max_workers=5)
    budget_manager = BudgetManager(db_path="data/budgets.db")

    worker_pool.start()
    initialize_services(worker_pool, budget_manager)

    yield

    # Shutdown
    worker_pool.stop()
```

**Configuration:**
- Port: 8080 (default)
- CORS: Enabled for all origins (configurable)
- Timeout: 30s default per request

### 2. API Router (`src/api.py`)

**Purpose:** REST API endpoint definitions

**Endpoints:**
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v1/chat/completions` | POST | Single completion request |
| `/v1/batch` | POST | Parallel batch processing |
| `/v1/usage` | GET | Usage statistics |
| `/v1/route` | POST | Model routing recommendation |
| `/health` | GET | Health check |
| `/` | GET | API information |

**Flow for `/v1/chat/completions`:**
```
1. Receive request → Validate with Pydantic
2. Auto-select model (if not specified) → model_router.py
3. Check budget → budget_manager.py
4. Submit to worker pool → worker_pool.py
5. Wait for completion
6. Track usage → budget_manager.py
7. Return response
```

**Error Handling:**
- `400` - Invalid request
- `429` - Budget exceeded
- `500` - Task failed or service error

### 3. Worker Pool (`src/worker_pool.py`)

**Purpose:** Manage concurrent Claude CLI processes

**Architecture:**
```
WorkerPool
├── Task Queue (FIFO)
├── Active Workers (dict)
├── Monitor Thread (background)
└── Task Results (dict)
```

**Features:**
- **Max workers:** Configurable limit (default: 5)
- **Task queue:** Overflow requests queued
- **Timeout handling:** Automatic cleanup after timeout
- **PID tracking:** Monitor active processes
- **Cost calculation:** Automatic based on token usage

**Lifecycle:**
```
1. submit(prompt, model) → Generate task_id
2. Queue task
3. Monitor thread picks up task
4. Start Claude CLI subprocess
5. Wait for completion
6. Parse JSON output
7. Calculate cost
8. Store result
9. Cleanup temp files
```

**Cost Calculation (January 2026 pricing):**
```python
COST_PER_MTK = {
    "haiku": {"input": 0.25, "output": 1.25},
    "sonnet": {"input": 3.00, "output": 15.00},
    "opus": {"input": 15.00, "output": 75.00},
}

cost = (input_tokens / 1_000_000) * input_rate + \
       (output_tokens / 1_000_000) * output_rate
```

### 4. Model Router (`src/model_router.py`)

**Purpose:** Intelligent model selection based on task complexity

**Routing Logic:**
```python
def auto_select_model(prompt, context_size, budget_remaining):
    # 1. Budget constraint
    if budget_remaining < 1000:
        return "haiku"

    # 2. Context constraint
    if context_size > 10000:
        return "opus"

    # 3. Complexity analysis
    if len(prompt) < 100 and has_simple_keywords(prompt):
        return "haiku"

    if has_complex_keywords(prompt) and budget_remaining >= 5000:
        return "sonnet"

    # 4. Default
    return "sonnet"
```

**Keywords:**
- **Simple:** list, format, count, show, get, create, add
- **Complex:** analyze, architect, debug, design, implement, optimize

**Example Routing:**
| Prompt | Context | Budget | Selected Model |
|--------|---------|--------|---------------|
| "List Python files" | 50 | 100k | Haiku |
| "Analyze codebase" | 5k | 100k | Sonnet |
| "Review 50k lines" | 15k | 100k | Opus |
| "Simple task" | 100 | 500 | Haiku (budget) |

### 5. Budget Manager (`src/budget_manager.py`)

**Purpose:** Per-project budget tracking and enforcement

**Database Schema:**
```sql
CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    name TEXT,
    monthly_token_limit INTEGER,
    created_at TIMESTAMP
);

CREATE TABLE usage_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    model TEXT NOT NULL,
    tokens INTEGER NOT NULL,
    cost_usd REAL NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE INDEX idx_usage_project_timestamp
ON usage_log(project_id, timestamp);
```

**Operations:**
- `check_budget(project_id, estimated_tokens)` → bool
- `track_usage(project_id, model, tokens, cost)` → void
- `get_usage(project_id, period)` → stats
- `set_budget(project_id, monthly_limit)` → void

**Budget Enforcement:**
```
1. Check current month usage
2. Estimate request tokens
3. Verify: current + estimated <= limit
4. If exceeds → Return 429
5. If passes → Allow request
6. After completion → Track actual usage
```

### 6. Token Tracker (`src/token_tracker.py`)

**Purpose:** Parse Claude CLI output and calculate costs

**Parsing Flow:**
```
1. Receive JSON string from Claude CLI
2. Extract usage: { input_tokens, output_tokens }
3. Extract model name
4. Determine model tier (haiku/sonnet/opus)
5. Calculate cost: (tokens / 1000) * rate_per_1k
6. Return structured data
```

**Example Output:**
```python
{
    "input_tokens": 150,
    "output_tokens": 300,
    "total_tokens": 450,
    "model": "claude-3-sonnet-20240229",
    "model_tier": "sonnet",
    "cost_usd": 0.005850
}
```

### 7. Cache Layer (`src/cache.py`)

**Purpose:** Redis-based caching for performance

**Cached Data:**
- Frequent prompts → completions
- Usage statistics → aggregated stats
- Rate limit counters → request counts

**Cache Strategy:**
- **TTL:** 1 hour for completions
- **Invalidation:** On budget changes
- **Key format:** `prompt:{hash}`, `usage:{project_id}:{period}`

## Data Flow

### Chat Completion Request

```
Client
  │
  │ POST /v1/chat/completions
  │ { messages, model?, project_id }
  ▼
API Router (src/api.py)
  │
  │ Validate request (Pydantic)
  ▼
Model Router (if model not specified)
  │
  │ auto_select_model(prompt, context, budget)
  ▼
Budget Manager
  │
  │ check_budget(project_id, estimated_tokens)
  ▼
Worker Pool
  │
  │ submit(prompt, model, project_id)
  │ → task_id
  ▼
Monitor Thread
  │
  │ Start Claude CLI subprocess
  │ claude -p "prompt" --model sonnet --output-format json
  ▼
Claude CLI Process
  │
  │ Generate completion
  │ Return JSON with usage stats
  ▼
Worker Pool
  │
  │ Parse JSON (token_tracker)
  │ Calculate cost
  │ Store result
  ▼
API Router
  │
  │ track_usage(project_id, tokens, cost)
  │ Format response
  ▼
Client
  │
  │ { id, model, content, usage, cost }
```

### Batch Processing Request

```
Client
  │
  │ POST /v1/batch
  │ { prompts: [...], model?, project_id }
  ▼
API Router
  │
  │ For each prompt:
  │   submit to worker pool → task_ids[]
  ▼
Worker Pool
  │
  │ Process all in parallel (up to max_workers)
  ▼
Aggregate Results
  │
  │ Collect all task results
  │ Calculate total cost, total tokens
  │ Track usage for each
  ▼
Client
  │
  │ { total, completed, failed, results, total_cost }
```

## Concurrency Model

### Thread Safety

```python
# Worker Pool
class WorkerPool:
    def __init__(self):
        self.lock = threading.Lock()  # Protects shared state
        self.tasks: Dict[str, Task] = {}
        self.task_queue: Queue = Queue()
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
```

**Protected Operations:**
- Task submission
- Task status updates
- Worker count changes
- Process cleanup

### Async/Await (FastAPI)

```python
# API endpoints run in async context
async def chat_completion(request: ChatCompletionRequest):
    # Submit task (sync operation)
    task_id = worker_pool.submit(...)

    # Wait for result (blocking → async wrapper)
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        worker_pool.get_result,
        task_id
    )
```

### Process Isolation

Each Claude CLI invocation runs in a separate process:
- **Isolation:** Tasks don't interfere
- **Cleanup:** Process death = automatic cleanup
- **Monitoring:** PID tracking for all workers

## Scalability

### Horizontal Scaling

**Stateless Design:**
- No in-memory session state
- All state in SQLite/Redis
- Each instance independent

**Load Balancing:**
```
Load Balancer
    │
    ├─→ API Instance 1 (Worker Pool)
    │
    ├─→ API Instance 2 (Worker Pool)
    │
    └─→ API Instance 3 (Worker Pool)
         │
         └─→ Shared SQLite/Redis
```

**Considerations:**
- SQLite → PostgreSQL for high concurrency
- Redis for distributed caching
- Shared file system for budgets.db

### Vertical Scaling

**Increase Workers:**
```python
# More workers = more concurrent Claude CLI processes
worker_pool = WorkerPool(max_workers=20)
```

**Resource Requirements:**
- **Memory:** ~500MB per worker
- **CPU:** 1 core per 5 workers
- **Disk:** Minimal (temp files cleaned up)

## Security

### Threat Model

**Threats:**
1. **Unauthorized access** → API key authentication
2. **Budget abuse** → Per-project limits
3. **Injection attacks** → Input sanitization
4. **DoS** → Rate limiting

**Mitigations:**
- API key middleware (future)
- Budget enforcement (implemented)
- Pydantic validation (implemented)
- Rate limiting (optional, via Redis)

### Data Privacy

- **No persistent prompts:** Temp files deleted after completion
- **Encrypted transport:** HTTPS in production
- **Access logs:** Minimal logging, no prompt content

## Performance

### Latency Breakdown

Typical request (Sonnet, 100-token prompt):

| Component | Time | % |
|-----------|------|---|
| API routing | 5ms | 1% |
| Budget check | 10ms | 2% |
| Queue wait | 0-5s | 0-50% |
| Claude CLI startup | 500ms | 10% |
| Model inference | 2-3s | 30-40% |
| JSON parsing | 10ms | 2% |
| Response formatting | 5ms | 1% |
| **Total** | **3-8s** | **100%** |

**Bottlenecks:**
- Claude CLI startup time
- Worker pool size (queue wait)
- Model inference time

**Optimizations:**
- Increase `max_workers` to reduce queue time
- Use Haiku for simple tasks (faster inference)
- Redis caching for repeated prompts

### Throughput

**Single instance (5 workers):**
- Haiku: ~30 requests/minute
- Sonnet: ~15 requests/minute
- Opus: ~5 requests/minute

**Scaled (3 instances, 5 workers each):**
- 3x throughput
- Shared budget tracking
- Independent worker pools

## Error Handling

### Error Propagation

```
Claude CLI Process Error
  │
  ▼
Worker Pool (catch exception)
  │
  │ Mark task as FAILED
  │ Store error message
  ▼
API Router (check status)
  │
  │ If FAILED → HTTPException(500)
  ▼
Client (receives error response)
  │
  │ { detail: "Task failed: ..." }
```

### Retry Strategy

**Client-side retries:**
- Automatic in `ClaudeClient` (max 3 retries)
- Exponential backoff
- Only retry on 500+ errors

**Server-side:**
- No automatic retries (client's responsibility)
- Idempotent operations (budget checks)

## Testing

### Test Coverage

| Component | Test File | Coverage |
|-----------|-----------|----------|
| Worker Pool | `test_worker_pool.py` | 90% |
| Model Router | `test_model_router.py` | 95% |
| Budget Manager | `test_budget_manager.py` | 85% |
| Token Tracker | `test_token_tracker.py` | 95% |
| API | `test_api.py` | 80% |

### Integration Tests

```python
# tests/test_api.py
def test_end_to_end_completion():
    # Submit request → Wait → Check response
    response = client.post("/v1/chat/completions", ...)
    assert response.status_code == 200
    assert "content" in response.json()
```

## Future Enhancements

1. **WebSocket streaming** - Real-time response streaming
2. **Multi-tenant isolation** - Database per tenant
3. **Advanced caching** - Semantic similarity caching
4. **Request queuing** - Redis-based distributed queue
5. **Metrics dashboard** - Grafana/Prometheus integration
6. **A/B testing** - Model comparison framework

## Diagrams

See also:
- Component interaction diagram (above)
- Data flow diagrams (above)
- Deployment architecture (DEPLOYMENT.md)
