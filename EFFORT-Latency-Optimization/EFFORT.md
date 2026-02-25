---
type: effort
effort_id: EFFORT-Latency-Optimization
project: PROJECT-Claude-Code-API-Service
status: in_progress
priority: high
progress: 10%
created: 2026-02-25T22:00:00Z
last_updated: 2026-02-25T22:00:00Z
linked_goal: null
---

# EFFORT: Latency Optimization

## Overview

Downstream AI services report 5-15 seconds of latency per call through claude-code-api-service. Extended thinking analysis identified 6 latency sources, with 3 critical bottlenecks accounting for the majority of the problem.

## Root Cause Analysis

Total measured overhead (excluding Claude API inference time): **~5,500ms average**

### Bottleneck #1: Claude CLI Cold Start (3,000-8,000ms)

Every request spawns a brand new `claude` process via `subprocess.Popen(shell=True)`. This means every request pays for: bash shell startup, Node.js runtime init, Claude CLI config loading, `$(cat prompt.txt)` subshell expansion, and API connection establishment to Anthropic. The CLI was designed for interactive human use, not sub-second API calls.

**Location:** `src/worker_pool.py:412` — `subprocess.Popen(cmd, shell=True, executable="/bin/bash")`

### Bottleneck #2: Event Loop Blocking in /v1/process (0-5,000ms stall under concurrency)

The `/v1/process` compatibility endpoint calls `worker_pool.get_result()` **synchronously** inside an async handler, blocking the entire asyncio event loop for the full request duration (10-30s). While blocked, no other requests are processed — health checks hang, WebSocket connections stall, and concurrent requests serialize.

Contrast with `/v1/chat/completions` which correctly uses `await loop.run_in_executor()`.

**Location:** `src/api.py:546` — `result = worker_pool.get_result(task_id, timeout=timeout)`

### Bottleneck #3: Monitor Loop Polling (0-600ms added latency)

The monitor loop uses a compounding delay pattern:
- `task_queue.get(timeout=0.5)` — up to 500ms wait
- `time.sleep(0.1)` — 100ms per cycle
- Result polling in `get_result()` — another 100ms per cycle

**Location:** `src/worker_pool.py:342-359` — `_monitor_loop()`

### Minor Sources

| Source | Latency | Location |
|--------|---------|----------|
| Auth: 3 SQLite queries, new connection each | ~3ms | `src/auth.py:144,175,222` |
| Budget check: async SQLite | ~2ms | `budget_manager.py` |
| Temp dir + file write | <1ms | `worker_pool.py:369` |

## Fix Plan (Priority Order)

### P0: Fix /v1/process Event Loop Blocking [5 min]

Change `api.py:546` from synchronous to async:
```python
# Before (BLOCKS event loop):
result = worker_pool.get_result(task_id, timeout=timeout)

# After (runs in thread pool):
loop = asyncio.get_event_loop()
result = await loop.run_in_executor(None, worker_pool.get_result, task_id, timeout)
```

**Impact:** Eliminates request serialization. Under concurrent load, this is the single biggest throughput killer.

### P1a: Replace Polling with Event-Based Notification [30 min]

Replace `sleep(0.1)` polling in `get_result()` with `threading.Event`:
- Add `done_event = threading.Event()` to `Task` dataclass
- Call `task.done_event.set()` in `_process_completed_task()`
- Replace polling loop with `task.done_event.wait(timeout=timeout)`

**Impact:** Sub-millisecond notification instead of 100ms polling. Saves 100-400ms per request.

### P1b: Direct Task Start in submit() [20 min]

When workers are available, start the task immediately in `submit()` instead of queuing for the monitor loop:
- If `active_workers < max_workers`, call `_start_task()` directly
- Only queue when at capacity
- Keep monitor loop for overflow processing and completion detection

**Impact:** Eliminates 0-600ms queue pickup delay.

### P2: Anthropic SDK Direct Path (optional) [2-4 hours]

For downstream services that only need LLM completions (no tool use), bypass CLI entirely and use the `anthropic` Python SDK. Eliminates 3-8 seconds of CLI cold start.

**Trade-off:** Loses Claude Code features (tools, CLAUDE.md, project context). May want to offer both paths — CLI for agentic tasks, SDK for simple completions.

### P3: SQLite Connection Pooling + Query Batching [30 min]

- Keep persistent SQLite connection with WAL mode instead of opening per-query
- Combine auth validation + rate limit check into single query
- Cache budget check results for a few seconds

**Impact:** Saves ~5-10ms per request.

## Expected Results

| Fix | Overhead Saved | Cumulative |
|-----|----------------|------------|
| P0 alone | Eliminates serialization (10-30s under concurrency) | Massive throughput improvement |
| + P1a+P1b | 200-1000ms per request | ~50ms overhead |
| + P2 (SDK path) | 3,000-8,000ms per request | Near-zero overhead for simple calls |
| + P3 | 5-10ms | Negligible |

## Success Criteria

- [ ] `/v1/process` no longer blocks the event loop (P0)
- [ ] Request overhead < 200ms (excluding CLI start + API time) (P1)
- [ ] Concurrent requests process in parallel, not serialized
- [ ] Health checks respond in <50ms even under load
- [ ] Optional: simple completion calls < 2 seconds total (P2)

## Related

- EFFORT-Compatibility-Adapter — `/v1/process` endpoint quality
- EFFORT-Production-Hardening — service reliability
- Reported by: downstream AI services (ai-rag-services on port 8002)
