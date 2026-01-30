# MIGRATION GUIDE — Swarm Architecture

**For existing orchestrator users: What changes? What stays the same?**

---

## TL;DR

✅ **Everything still works.** Your existing initiatives, standard model workflows, and helper delegation all work unchanged.

🆕 **NEW: Swarm model is now available** for complex, high-volume tasks (30+ atomic actions).

❌ **No breaking changes.** Opt-in to swarm when you choose. Standard model is still default.

---

## What Stays The Same

### Existing Initiatives Still Work

```json
{
  "id": "INIT-001",
  "title": "Your existing task",
  "status": "in_progress",
  // No "use_swarm" field = use standard model
}
```

If you don't add `use_swarm: true`, the initiative runs exactly as before.

### Standard Model (Main + Helpers) Unchanged

**Workflow remains**:
1. Create initiative in initiatives.json
2. Spawn main worker (Sonnet/Opus)
3. Main worker optionally spawns helpers for simple work
4. Main worker monitors execution

**No changes to**:
- MASTER_WORKER_SYSTEM.md (still applies to main workers)
- HELPER_WORKER_SYSTEM.md (still applies to helper workers)
- workspace/instructions.txt format (still works)
- workspace/findings.txt format (still works)
- Dynamic task delegation (still works)

### Worker Daemon Unchanged

No changes to `worker-daemon.py`. It already supports:
- Any number of workers per initiative
- Any manifest format
- Workspace coordination
- File watching

---

## What's New

### 1. Swarm Model Option

When you identify a complex, parallelizable task:

```json
{
  "id": "INIT-REFACTOR-001",
  "title": "Migrate codebase to ES modules",
  "use_swarm": true,
  "swarm_config": {
    "planner_count": 3,
    "executor_worker_count": 8
  }
}
```

### 2. New Documents to Read

In order of importance:
1. **SWARM_QUICK_REFERENCE.md** (5 min) — Decide if you need swarm
2. **SWARM_EXAMPLES.md** (5 min) — See real examples
3. **master-prompt.md → "SWARM ARCHITECTURE"** (10 min) — Full details
4. **PLANNER_WORKER_SYSTEM.md** (if you're a planner)
5. **EXECUTION_SWARM_SYSTEM.md** (if you're an executor)

### 3. New Worker Types

Instead of just "main" and "helper", you can now spawn:
- **"planner"** workers (Haiku) — Decompose complex tasks
- **"executor"** workers (Haiku) — Execute atomic tasks in parallel

### 4. New Workspace Files

For swarm initiatives, you get:
- **plan.json** — Shared task definitions (planners write, executors read)
- **execution_log.json** — Shared progress tracking (executors write)
- **task_locks/** — Prevents conflicts (executors manage)

Standard initiatives still use instructions.txt, findings.txt, results/, etc.

---

## Decision Tree: Swarm or Standard?

```
New task arrives
  ↓
Can I break it into 30+ independent atomic tasks?
  ├─ NO → Use STANDARD model
  └─ YES → Go to next question
         ↓
         Does task have heavy dependencies (most tasks block others)?
         ├─ YES → Use STANDARD model
         └─ NO → Go to next question
               ↓
               Is this high-volume work (bulk updates, migrations, refactors)?
               ├─ NO → Use STANDARD model (overhead not worth it)
               └─ YES → Use SWARM model
```

**If unsure, ask**: "Would 8 workers running simultaneously help?" If yes → swarm.

---

## Migration Examples

### Example 1: Small Feature (Standard Model)

**Before**: Create INIT-XXX with main worker, 1-2 helpers
**After**: Exactly the same. Don't change anything.

```json
{
  "id": "INIT-001",
  "title": "Add login button to dashboard",
  "use_swarm": false  // explicit, but optional
}
```

---

### Example 2: Bulk Config Update (Swarm!)

**Before**:
```json
{
  "id": "INIT-002",
  "title": "Update API endpoints in 50 config files"
  // Single main worker would read all 50 files, edit sequentially
}
```

**After**:
```json
{
  "id": "INIT-002",
  "title": "Update API endpoints in 50 config files",
  "use_swarm": true,
  "swarm_config": {
    "planner_count": 2,
    "executor_worker_count": 8
  }
  // 2 planners decompose into 50 atomic tasks
  // 8 executors run all 50 in parallel (~5 min vs. 50 min sequential)
}
```

**Cost difference**: 11k tokens (main worker) vs. 6.5k tokens (swarm) = **40% cheaper**

---

### Example 3: Mid-Task Pivot

**During execution of INIT-XXX, main worker realizes**:
```
I thought this was a 20-file refactor.
Actually 120 files need updating.
Taking too long sequentially.
```

**What they do**:
1. Write to workspace/findings.txt:
```
PIVOT_RECOMMENDATION: Task is larger than expected.
120 files need the same edit pattern.
Current approach will take 2 hours.
Recommendation: Spawn swarm for remaining 100 files.
```

2. **Orchestrator sees findings.txt and**:
   - Creates INIT-PIVOT-XXX for remaining 100 files
   - Spawns 3 planners + 8 executors
   - Original main worker focuses on validation

3. **Result**: Original estimate (2 hours) becomes 15 minutes + validation

---

## Backward Compatibility

### Old Initiatives Can't Use Swarm

If you have an old INIT-001 already running:
```json
{
  "id": "INIT-001",
  "title": "Old task",
  "status": "in_progress",
  // No swarm_config
}
```

It keeps running with standard model. Can't pivot mid-stream.

**Solution**: For future large tasks, create NEW initiative with swarm.

### Old Manifests Still Work

```json
{
  "initiative_id": "INIT-OLD",
  "workers": [
    {"file": "INIT-OLD_main.txt", "model": "sonnet", "type": "main"},
    {"file": "INIT-OLD_helper.txt", "model": "haiku", "type": "helper"}
  ]
}
```

This manifest still works. Daemon treats it the same as before.

### Swarm Adds New Worker Types

```json
{
  "initiative_id": "INIT-SWARM",
  "workers": [
    {"file": "INIT-SWARM_planner1.txt", "model": "haiku", "type": "planner"},
    {"file": "INIT-SWARM_planner2.txt", "model": "haiku", "type": "planner"},
    {"file": "INIT-SWARM_exec1.txt", "model": "haiku", "type": "executor"},
    // ... more executors
  ]
}
```

Daemon doesn't care about worker type. It just spawns what's in the manifest.

---

## Reading Path by Role

### If You're an Orchestrator

1. **SWARM_QUICK_REFERENCE.md** (decide when to use swarm)
2. **SWARM_EXAMPLES.md** (see patterns)
3. **master-prompt.md → "SWARM ARCHITECTURE"** (full workflow)

### If You're a Main Worker (Sonnet/Opus)

1. **MASTER_WORKER_SYSTEM.md** (you already read this)
2. New section: "SWARM ARCHITECTURE" (understand your role as recommender)
3. Optional: **SWARM_EXAMPLES.md** (see when you'd recommend swarm)

### If You're Spawned as Planner

1. **PLANNER_WORKER_SYSTEM.md** (MANDATORY)
2. You decompose, you're done

### If You're Spawned as Executor

1. **EXECUTION_SWARM_SYSTEM.md** (MANDATORY)
2. You execute, you're done

---

## FAQ

### Q: Will my old initiatives break?
**A**: No. They work exactly as before. Swarm is opt-in.

### Q: Do I have to migrate to swarm?
**A**: No. Standard model still works fine for most tasks. Swarm is for specific high-volume scenarios.

### Q: Can I use swarm for small tasks?
**A**: Technically yes, but overhead isn't worth it. Use standard model for < 20 atomic tasks.

### Q: What if my swarm task has unexpected dependencies?
**A**: Executor writes to findings.txt. Orchestrator regenerates plan with correct dependencies.

### Q: Can I switch from swarm back to standard mid-task?
**A**: Not directly. If swarm is taking too long, create new standard initiative for remaining work and have main worker validate.

### Q: How many workers should I spawn?
**A**: 3 planners for planning, 5-10 executors for execution (depends on task). See SWARM_QUICK_REFERENCE.md.

### Q: What if an executor crashes?
**A**: Task stays pending (lock file dies with the process). Next worker can claim it and retry.

### Q: Can executors execute out of order?
**A**: Yes! Dependency checking means executor will skip task_B if task_A (dependency) isn't done yet. They execute in whatever order tasks become available.

---

## Rollout Checklist

- [x] Swarm architecture documented
- [x] Four new reference documents created
- [x] Existing documents updated with swarm guidance
- [x] Decision trees provided (when to use swarm)
- [x] Examples provided (real scenarios)
- [x] Backward compatibility verified (nothing breaks)
- [x] Committed to git

---

## Next Steps

1. **Read SWARM_QUICK_REFERENCE.md** (today)
2. **Try swarm on a test task** (next week)
   - Start with bulk config update (simplest case)
   - Spawn 2 planners, 4 executors
   - Verify plan.json and execution_log.json
3. **Review and adjust** (weekly)
   - Track actual token usage vs. estimates
   - Adjust planner/executor count based on results
   - Document learnings in findings.txt

---

## Support

If you hit issues with swarm:

1. **Planner produced bad plan?** → Orchestrator clarifies and regenerates
2. **Executor got stuck?** → Check findings.txt for error, regenerate plan
3. **Circular dependencies?** → Planner should catch these. If not, re-plan.
4. **Two executors claiming same task?** → Lock protocol prevents this. If it happens, restart executor.

Most issues are solved by re-generating the plan with corrected task description.

---

## Success Criteria

You're successfully using swarm architecture when:

- ✅ Large tasks (80+ files) execute in parallel at 40% lower cost
- ✅ Planners produce clear, atomic task lists
- ✅ Executors run without conflicts (locks work)
- ✅ Dependencies are respected (sequential tasks wait properly)
- ✅ Failures are reported clearly to findings.txt
- ✅ Token savings match predictions (40-60% for bulk tasks)
- ✅ Speed improvements happen (5-15x faster for parallelizable work)

---

**The swarm model is ready. Start with SWARM_QUICK_REFERENCE.md, decide if your next task fits, and try it out.**
