# SWARM ARCHITECTURE — REAL EXAMPLES

These examples show how to use the swarm model for different types of complex tasks.

---

## Example 1: Bulk Configuration Update (High Volume, Parallel)

**Task**: Update API endpoints across 50 config files from v1 to v2

### Orchestrator Decision

```json
{
  "id": "INIT-001",
  "title": "Update API endpoints v1 → v2 (50 files)",
  "use_swarm": true,
  "swarm_config": {
    "planner_count": 2,
    "executor_worker_count": 10,
    "reason": "50 independent file updates = perfect parallelization"
  },
  "token_budget": 15000
}
```

### Plan Output (from 2 planners)

```json
{
  "tasks": [
    {
      "id": "update_config_1",
      "title": "Update config/api-staging.json",
      "action": "edit",
      "files_affected": ["config/api-staging.json"],
      "atomic_instruction": "In config/api-staging.json, replace all occurrences of 'https://api.v1.example.com' with 'https://api.v2.example.com'",
      "depends_on": [],
      "parallel_safe": true,
      "estimated_tokens": 100
    },
    {
      "id": "update_config_2",
      "title": "Update config/api-prod.json",
      "action": "edit",
      "files_affected": ["config/api-prod.json"],
      "atomic_instruction": "In config/api-prod.json, replace all occurrences of 'https://api.v1.example.com' with 'https://api.v2.example.com'",
      "depends_on": [],
      "parallel_safe": true,
      "estimated_tokens": 100
    },
    // ... 48 more tasks, one per file
  ],
  "total_tasks": 50,
  "estimated_execution_minutes": 5
}
```

### Execution (10 workers in parallel)

```
Worker 1: Claims task_1 (config/api-staging.json) → executes → DONE (2 min)
Worker 2: Claims task_2 (config/api-prod.json) → executes → DONE (2 min)
Worker 3: Claims task_3 → executes → DONE (2 min)
...
Worker 10: Claims task_10 → executes → DONE (2 min)

Then workers loop back and claim tasks 11-20, etc.

Result: 50 tasks completed in ~5 minutes (vs. 50 minutes sequential)
```

### Cost Analysis

- Planners: 2 × 1.5k = 3k tokens
- Executors: 50 × 100 = 5k tokens
- **Total: 8k tokens**

- Alternative (single main worker): 15k tokens planning + batch execution
- **Savings: 46% cheaper + 10x faster**

---

## Example 2: Large Codebase Refactor (Complex, Many Dependencies)

**Task**: Migrate from TypeScript interfaces to discriminated unions across 80 files

### Planner Decomposition

Planners recognize:
- Can't update all files in parallel (dependency chain)
- Need: Define union types first → update consumers → fix imports → test

```json
{
  "tasks": [
    {
      "id": "phase1_define_unions",
      "title": "Create discriminated union type definitions",
      "action": "create",
      "files_affected": ["src/types/unions.ts"],
      "atomic_instruction": "Create src/types/unions.ts with discriminated unions: [exact_types_here]",
      "depends_on": [],
      "parallel_safe": true
    },
    {
      "id": "phase1_create_index",
      "title": "Create union index file",
      "action": "create",
      "files_affected": ["src/types/index.ts"],
      "atomic_instruction": "Create src/types/index.ts exporting: export * from './unions'",
      "depends_on": [],
      "parallel_safe": true
    },
    {
      "id": "phase2_update_api_1",
      "title": "Update API handlers to use unions",
      "action": "batch_edit",
      "files_affected": ["src/api/handlers/*"],
      "atomic_instruction": "In src/api/handlers/*, replace 'interface User' with 'type User = UserUnion' and import unions",
      "depends_on": ["phase1_define_unions", "phase1_create_index"],
      "parallel_safe": true,
      "count": 20
    },
    // ... many more phase 2 tasks
    {
      "id": "phase3_test_suite",
      "title": "Run full test suite",
      "action": "run",
      "atomic_instruction": "Run: npm test (verify all tests pass with new unions)",
      "depends_on": ["phase2_update_api_1", "phase2_update_models", "phase2_update_utils"],
      "parallel_safe": false
    }
  ],
  "coordination_notes": "Three phases with dependencies enforced. Phase 1 (types) finishes, then Phase 2 (updates) runs in parallel, then Phase 3 (tests) runs final check."
}
```

### Execution with Dependencies

```
Worker 1: Claims phase1_define_unions → executes → DONE
Worker 2: Claims phase1_create_index → executes → DONE

Wait for both phase1 tasks...

Workers 1-8: Claim phase2 tasks (20 parallel updates) → all execute → DONE

Wait for all phase2 tasks...

Worker 1: Claims phase3_test_suite → executes → DONE
```

### Cost Analysis

- Planners (3): 3 × 2k = 6k tokens
- Executors (8): ~40 tasks × 300 tokens = 12k tokens
- **Total: 18k tokens**

- Alternative (main worker plans + delegates batch updates): 25k+ tokens
- **Savings: 28% cheaper + parallel phase execution**

---

## Example 3: Multi-Service Migration (Extreme Parallelization)

**Task**: Migrate 5 microservices from REST to gRPC simultaneously

### Swarm Configuration

```json
{
  "use_swarm": true,
  "swarm_config": {
    "planner_count": 3,
    "executor_worker_count": 15,
    "reason": "5 independent services, each service has 30+ parallel tasks"
  }
}
```

### Plan Structure

Planners produce 150+ tasks organized by service:

```json
{
  "tasks": [
    // Service 1: gRPC setup (4 tasks, no deps)
    {"id": "svc1_proto", "service": "user-service", "depends_on": []},
    {"id": "svc1_codegen", "service": "user-service", "depends_on": ["svc1_proto"]},
    {"id": "svc1_handlers", "service": "user-service", "depends_on": ["svc1_codegen"], "parallel_safe": true, "count": 8},
    {"id": "svc1_client", "service": "user-service", "depends_on": ["svc1_codegen"]},

    // Service 2: gRPC setup (parallel with Service 1)
    {"id": "svc2_proto", "service": "order-service", "depends_on": []},
    {"id": "svc2_codegen", "service": "order-service", "depends_on": ["svc2_proto"]},
    {"id": "svc2_handlers", "service": "order-service", "depends_on": ["svc2_codegen"], "parallel_safe": true, "count": 12},

    // ... Services 3, 4, 5 (all in parallel)

    // Final: Integration tests
    {"id": "integration_tests", "depends_on": ["svc1_client", "svc2_client", "svc3_client", "svc4_client", "svc5_client"]}
  ]
}
```

### Execution Pattern

```
Services 1-5: Proto definition (5 parallel tasks, ~1 min)
  ↓
Services 1-5: Code generation (5 parallel tasks, ~2 min)
  ↓
Services 1-5: Handler updates (50 parallel tasks, ~8 min) — All 15 workers busy
  ↓
Services 1-5: Client setup (5 parallel tasks, ~2 min)
  ↓
Integration tests (1 task, ~5 min)

Total: ~18 minutes vs. ~2 hours sequential
```

### Why Swarm Wins Here

- **5 independent services**: Each can be worked on in parallel
- **50+ handler updates**: Massively parallelizable (15 workers run simultaneously)
- **Dependencies enforced**: Proto before codegen, codegen before handlers
- **Extreme speedup**: 7x faster with proper parallelization
- **Cost efficiency**: Haiku executors at 1/4 cost of main worker

---

## Example 4: When NOT to Use Swarm

**Task**: Fix one critical bug in authentication middleware

### Why Standard Model Is Better

- Only 2-3 files affected
- Requires Sonnet-level reasoning (security implications)
- Changes are sequential (each fix depends on understanding the previous)
- No parallelization opportunity

```json
{
  "id": "INIT-BUG-001",
  "title": "Fix authentication bypass bug",
  "use_swarm": false,
  "reason": "Single, critical issue requiring main worker reasoning. Too small for swarm overhead."
}
```

**Cost**: 1 main worker (Sonnet) ~ 5k tokens
**Not worth**: 3 planner agents + 5 executor agents = 12k tokens minimum overhead

---

## Example 5: When to Pivot from Standard to Swarm Mid-Task

**Scenario**: Main worker discovers the task is much larger than expected

### Trigger

Main worker is executing INIT-XXX when they realize:
- 100+ files need similar updates
- Changes are parallelizable
- Current sequential approach will be slow

### What They Do

1. Write to findings.txt:
```
PIVOT_RECOMMENDATION: Task is larger than expected. 120 files need updating with same pattern.
Current status: 10 files done, 110 remaining.
Recommendation: Spawn swarm for remaining work.
```

2. Orchestrator sees recommendation and:
   - Creates new initiative INIT-YYY for remaining 110 files
   - Spawns 3 planners to decompose those 110 files
   - Spawns 10 executors to parallelize
   - Much faster completion

3. Original main worker focuses on final validation/testing

**Cost benefit**: 110 files at 8x speed + 8x cheaper executors = 87% faster, 40% cheaper than continuing alone

---

## Summary: When to Use Swarm

| Scenario | Use Swarm? | Why |
|----------|-----------|-----|
| Bulk config update (50+ files, same change) | ✅ YES | High volume, parallelizable |
| Large refactor (80+ files, complex) | ✅ YES | Needs decomposition, many independent tasks |
| Critical bug fix (3 files) | ❌ NO | Too small, requires main worker reasoning |
| New feature (15 files, complex logic) | ❌ NO | Requires design decisions throughout |
| Database migration (10+ scripts, independent) | ✅ YES | Independent, high-volume, parallelizable |
| API endpoint redesign (20+ endpoints, sequential) | ❌ NO | Endpoints depend on each other, needs design reasoning |
| Update imports in 200 files | ✅ YES | Highly parallel, simple atomic task |
| Fix test failures (20 tests failing) | ❌ NO | Each test needs diagnosis (not atomic) |

**Rule of thumb**: If you can decompose the task into 30+ independent, atomic operations, swarm wins. Otherwise, use standard model.
