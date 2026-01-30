# ORCH-001 Violations Guide — Quick Reference

**IF YOU'RE THINKING THIS → DO THIS INSTEAD**

---

### Reading & Analysis

❌ "I'll read this file to understand the system"
✓ Spawn EXPLORATION helper → read findings.txt when done

❌ "Let me review this before editing"
✓ Use Glob to find exact lines → read only those lines → edit immediately

❌ "I need to check the current state"
✓ Spawn CONTEXT helper → read status_summary.txt when done

---

### Searching & Pattern Finding

❌ "I'll grep for error handlers"
✓ Spawn CODE SEARCH helper → read findings.txt with results

❌ "Let me find where this function is used"
✓ Spawn CODE SEARCH helper → read findings.txt with matches

❌ "I'll search the codebase for the pattern"
✓ Spawn CODE SEARCH helper → read findings.txt with all occurrences

---

### File Inspection

❌ "Let me read the config to decide"
✓ Spawn EXPLORATION helper → read findings.txt with analysis

❌ "I need to check if all files exist"
✓ Spawn FILE AUDIT helper → read findings.txt with audit results

---

### Verification & Checks

❌ "I'll read several files to understand the structure"
✓ Spawn EXPLORATION helper for multiple files at once

❌ "Let me verify the implementation is complete"
✓ Spawn FILE AUDIT helper with checklist

---

## The Core Rule

**If you're reading a file that isn't .claude/* or initiatives.json, you're violating ORCH-001.**

**Delegate instead using HELPER_TEMPLATES.md**

Cost analysis:
- Your reading + thinking: 5,000-8,000 tokens
- Helper reading + reporting: 1,000-1,500 tokens
- **SAVINGS: 70-85%**

---

## What You CAN Read Directly

- .claude/master-prompt.md
- .claude/MASTER_WORKER_SYSTEM.md
- .claude/HELPER_WORKER_SYSTEM.md
- .claude/initiatives.json
- .claude/workspaces/[YOUR_INIT]/findings.txt (after helper completes)

---

## What Requires a Helper

- Source code files (*.py, *.rs, *.js, *.ts, etc)
- Config files (*.json, *.yaml, *.toml, etc)
- Workspace files (instructions.txt, context.json, results/*, etc)
- README.md or other documentation
- Any file >100 lines
- Any pattern search or exploration
- Any "I need to understand" scenario

---

## Helper Template Cheat Sheet

| Need | Use Template | Output |
|------|--------------|--------|
| Understand code structure | EXPLORATION | findings.txt |
| Find where something is | CODE SEARCH | findings.txt |
| Verify completeness | FILE AUDIT | findings.txt |
| Check progress status | CONTEXT | status_summary.txt |

Copy templates from .claude/HELPER_TEMPLATES.md, fill in brackets, spawn via manifest.

---

## ⚠️ WHY TASK TOOL IS BANNED (Economic Analysis)

### The Task Tool Cost Trap

**What happens when you use Task tool (inline agents):**

```
You spawn Task → Agent runs in YOUR context → Results dump back into YOUR expensive session
              ↓                                            ↓
              Blocking (you wait idle)           Context bloat (inflates every token)
              1.5-3k tokens per spawn            ~2-4k tokens added to context
              + your idle time penalty           + downstream tokens multiply
```

**Example: "Let me use Task to explore the codebase"**
- Task tool cost: 2k tokens
- Result lands in your context: 2k tokens added
- Every subsequent response now has 2k extra context bloat
- Over a 10-turn session: 2k × 10 = 20k extra tokens wasted
- **Total damage: 22k tokens**

**Correct approach: Spawn terminal helper**
- Write helper block: 200 tokens
- Daemon spawns helper: 0 tokens (you keep working)
- Helper explores: 2k tokens (runs on Haiku, not your context)
- Helper writes findings.txt: 1k tokens
- You read findings.txt: 500 tokens
- **Total cost: 3.7k tokens (84% cheaper) + no context bloat + non-blocking**

### Why Task Tool Doesn't Fit ORCH Architecture

The entire system is designed to avoid inline agents because they are:

1. **Blocking**: Your expensive session idles while agent runs
   - Opportunity cost: Could be planning/reasoning instead
   - Time cost: Human waiting (annoying UX)

2. **Context bloat**: Results dump into YOUR context
   - Multiplier effect: Every future token costs more
   - Compounding waste: Blocks on blocks on blocks

3. **No efficiency control**: Inline agents lack:
   - ORCH-001 discipline
   - Budget tracking
   - Zero-think protocol
   - Token waste audits

4. **Expensive model**: Agent runs on YOUR model tier
   - Task tool in Sonnet session: Wastes expensive Sonnet tokens
   - Terminal helper: Runs on Haiku (3.75x cheaper)

### Math: Task Tool vs. Terminal Helper

**Scenario: "I need to understand the file structure"**

**Option A: Task tool (WRONG)**
- Spawn Explore agent (Haiku) via Task: 1.5k tokens
- Agent explores: 3k tokens
- Results land in your context: 3k tokens
- Your remaining turns now have 3k extra context: 3k × 5 turns = 15k overhead
- **Total: 1.5k + 3k + 3k + 15k = 22.5k tokens**

**Option B: Terminal helper (CORRECT)**
- Write helper block: 200 tokens
- Helper explores (on Haiku, separate session): 3k tokens
- You read findings.txt (small summary): 500 tokens
- No context bloat (results stay in findings.txt, you read selectively)
- **Total: 200 + 3k + 500 = 3.7k tokens**

**Savings: 22.5k - 3.7k = 18.8k tokens (83% cheaper)**

### The Swarm Alternative

For complex planning (where you might "use Task to explore"), use the SWARM architecture instead:

```
❌ WRONG: Use Task tool to plan the refactor
   - Blocking, expensive, context bloat

✅ CORRECT: Spawn 1-3 planner agents (terminal workers)
   - Non-blocking (you keep working)
   - Cheaper (Haiku, no context bloat)
   - Better results (dedicated planning agents)
   - Massive parallelism (3 planners work simultaneously)
```

See `.claude/master-prompt.md` → "SWARM ARCHITECTURE" section for details.

### ABSOLUTE RULE: No Task Tool, Ever

**The only way to use agents is:**
1. Write worker block to `.claude/pending_workers/INIT-XXX_*.txt`
2. Write manifest to `.claude/pending_workers/manifest.json`
3. Daemon spawns terminal worker
4. Worker runs in separate session (non-blocking, efficient)
5. You read results from workspace when done

**You NEVER use Task tool. Period.**

Cost difference is too large to justify. Economics are undeniable.

---

## Economic Principle: ALWAYS Delegate > Always Read

**Key insight: Spawning a helper is always cheaper than reading files yourself**

Compare:
- Reading 5 files yourself: 5-8k tokens (YOU are expensive)
- Spawning helper to read 5 files: 1-1.5k tokens (HAIKU is cheap)
- Savings: 70-85%

**Exception**: Only read if:
1. File < 100 lines
2. You're editing it right now
3. You haven't read it before (no re-reading)

**Otherwise: ALWAYS spawn a helper. The economics are undeniable.**
