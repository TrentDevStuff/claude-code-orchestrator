# SWARM ARCHITECTURE — QUICK REFERENCE

One-page guide to the swarm model for complex tasks.

---

## TL;DR: What Is a Swarm?

**Instead of one main worker doing everything:**
```
Main worker plans → Main worker executes → takes forever, expensive
```

**Use a swarm:**
```
1-3 Planners decompose task → 5-10 Executors run in parallel → 10x faster, 40% cheaper
```

---

## When to Use Swarm

✅ **High-volume, parallelizable work:**
- 50+ config files needing same update
- Bulk refactor across 80+ files
- Batch operations (100+ similar edits)

❌ **Small or sequential tasks:**
- Single feature (< 20 files)
- Critical bug requiring reasoning
- Refactor with heavy dependencies

**Quick test**: Can you break this task into 30+ independent atomic actions? If yes → SWARM.

---

## Quick Setup (Orchestrator)

### 1. Create Initiative
```json
{
  "id": "INIT-XXX",
  "title": "Your complex task",
  "use_swarm": true,
  "swarm_config": {
    "planner_count": 3,
    "executor_worker_count": 8
  }
}
```

### 2. Spawn Planners (Write manifest)
```json
{
  "initiative_id": "INIT-XXX",
  "workers": [
    {"file": "INIT-XXX_planner1.txt", "model": "haiku", "type": "planner"},
    {"file": "INIT-XXX_planner2.txt", "model": "haiku", "type": "planner"},
    {"file": "INIT-XXX_planner3.txt", "model": "haiku", "type": "planner"}
  ]
}
```

### 3. Wait for plan.json
Monitor: `.claude/workspaces/INIT-XXX/plan.json`

### 4. Spawn Executors (Write manifest)
```json
{
  "initiative_id": "INIT-XXX",
  "workers": [
    {"file": "INIT-XXX_exec1.txt", "model": "haiku", "type": "executor"},
    {"file": "INIT-XXX_exec2.txt", "model": "haiku", "type": "executor"},
    // ... 6 more executor workers
  ]
}
```

### 5. Monitor execution_log.json
All tasks will be marked `completed` when done.

---

## Planner Job (1-3 agents)

**Role**: Decompose complex task into atomic chunks

**Input**: Complex task description
**Output**: `.claude/workspaces/INIT-XXX/plan.json` with task list
**Cost**: ~2k tokens each
**Read**: `.claude/PLANNER_WORKER_SYSTEM.md`

**Quick checklist**:
- [ ] 30-100 atomic tasks (not 5, not 500)
- [ ] Each task has exact `atomic_instruction` (no ambiguity)
- [ ] Dependencies marked accurately
- [ ] Parallel-safe tasks marked `true`
- [ ] Similar tasks grouped into batch operations

---

## Executor Job (5-10 agents)

**Role**: Execute atomic tasks in parallel

**Input**: `.claude/workspaces/INIT-XXX/plan.json` (shared by all)
**Output**: Updates to `workspace/execution_log.json`
**Cost**: ~200-500 tokens each
**Read**: `.claude/EXECUTION_SWARM_SYSTEM.md`

**Quick checklist**:
- [ ] Read plan.json
- [ ] Find next pending task (not locked)
- [ ] Create lock file (prevent conflicts)
- [ ] Execute instruction exactly
- [ ] Update execution_log
- [ ] Delete lock file
- [ ] Repeat until all tasks done

---

## File Structure (Swarm Workspace)

```
.claude/workspaces/INIT-XXX/
├── plan.json              ← Planners write, executors read
├── execution_log.json     ← Executors write progress here
├── task_locks/            ← Prevents conflicts (worker-created)
│   ├── task_1.lock
│   ├── task_2.lock
│   └── ...
├── findings.txt           ← Questions, blockers, notes
└── results/               ← (optional) Final outputs
```

---

## How Executors Coordinate (No Central Server)

**Lock protocol** (prevents two workers executing same task):
1. Worker claims task: `touch task_locks/task_N.lock`
2. Other workers see lock → skip task
3. Task execution completes
4. Worker: `rm task_locks/task_N.lock`
5. Next worker can now claim that task

**Dependency protocol** (ensures task_B waits for task_A):
1. Worker wants to execute task_B
2. Checks execution_log.json: is task_A (dependency) `completed`?
3. If NO → skip task_B, try next task
4. If YES → claim task_B and execute

---

## Cost Comparison

### Example: Update 50 config files

**Standard Model** (1 main worker):
- Planning: 3k tokens
- Batch editing 50 files sequentially: 8k tokens
- Total: 11k tokens
- Time: 60 minutes (if you were counting)

**Swarm Model** (3 planners + 8 executors):
- 3 planners × 1.5k = 4.5k tokens
- 8 executors × 300 tokens = 2.4k tokens
- Total: 6.9k tokens
- Time: 5 minutes (parallel execution)

**Savings: 37% cheaper, 12x faster**

---

## Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| Two workers executing same task | Use task locks (EXECUTION_SWARM_SYSTEM.md) |
| Worker waiting for dependency | Check execution_log.json, wait if dependency not `completed` |
| Executor can't understand instruction | Write to findings.txt, main worker will clarify |
| Task fails mid-execution | Log error to execution_log.json, release lock, move to next task |
| Circular dependencies in plan | Planner should catch this. If it happens, write to findings.txt |

---

## Decision Tree

```
User asks for complex task
  ↓
Is task > 50 atomic actions AND mostly independent?
  ├─ NO → Use STANDARD model (main + optional helpers)
  └─ YES → Is task high-priority and time-critical?
           ├─ NO → Use SWARM (will be 40% cheaper + 5x faster)
           └─ YES → Use SWARM anyway (speed matters more than cost)

Proceed with SWARM:
  1. Create initiative with swarm_config
  2. Spawn 1-3 planners → wait for plan.json
  3. Spawn 5-10 executors → wait for execution_log.json completion
  4. Done
```

---

## When Swarm Fails

**Planner produces bad plan** → Main worker sees `findings.txt` error → Orchestrator creates new initiative with corrected task description

**Executor gets stuck** → Writes to `findings.txt` → Main worker clarifies → Orchestrator updates plan and restarts stuck executor

**Circular dependencies discovered** → Executor reports to `findings.txt` → Orchestrator regenerates plan without cycles

**Main worker judges swarm is overkill mid-task** → Write recommendation to `findings.txt` → Orchestrator pivots back to standard model for remaining work

---

## Reading List (In Order)

1. **This file** (2 min) — Understand the concept
2. **SWARM_EXAMPLES.md** (5 min) — See real examples
3. **PLANNER_WORKER_SYSTEM.md** (10 min) — If you're a planner
4. **EXECUTION_SWARM_SYSTEM.md** (10 min) — If you're an executor
5. **master-prompt.md → "SWARM ARCHITECTURE"** — Full details

---

## Key Insight

**The swarm model isn't about "making Haiku smarter". It's about:**
- Breaking big problems into small atomic tasks (planners do this)
- Executing many small tasks in parallel (executors do this)
- Avoiding expensive single-worker planning (swarm cost is 40% cheaper)
- Removing bottlenecks (5-10 workers working simultaneously)

**This is why it works.**
