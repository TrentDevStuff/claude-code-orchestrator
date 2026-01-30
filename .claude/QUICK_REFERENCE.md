# Quick Reference — Orchestrator Cheat Sheet

## Launch System

```bash
# First time only (installs dependencies, creates directories)
Windows: install-claude-orchestrator.bat
Mac/Linux: bash install-claude-orchestrator.sh

# Start orchestrator
Windows: claude-orch.bat
Mac/Linux: ./claude-orch.sh
```

## File Locations (Quick Access)

```
.claude/
├── initiatives.json              Master state (all initiatives, tokens, status)
├── pending_workers/              Drop manifests here to spawn workers
├── workspaces/INIT-XXX/          Per-initiative work directory
│   ├── findings.txt              Helper output, exploration results
│   ├── instructions.txt          Task queue (main → helper)
│   └── session_output.json       Worker stdout with token data
└── alerts/                       Budget exceeded notifications
```

## Worker Types

| Type | Model | Use Case | Cost |
|------|-------|----------|------|
| Orchestrator | Opus/Sonnet | Planning, complex reasoning | Expensive |
| Main Worker | Sonnet | Execution, coordination | Medium |
| Helper | Haiku | Exploration, batch ops | 8x cheaper |
| Planner | Haiku | Task decomposition (swarm) | Cheap |
| Executor | Haiku | Parallel execution (swarm) | Very cheap |

## Spawn a Helper (3 Steps)

```bash
# 1. Write helper block (FIRST)
.claude/pending_workers/INIT-XXX_helper.txt

# 2. Write manifest (SECOND — triggers daemon)
.claude/pending_workers/manifest.json
{"initiative_id": "INIT-XXX", "workers": [{"file": "INIT-XXX_helper.txt", "model": "haiku", "type": "helper"}]}
```

**Templates**: See `.claude/HELPER_TEMPLATES.md` for copy-paste blocks

## Check Status

```bash
# Ask orchestrator
"show me status"

# Check initiative state
cat .claude/initiatives.json

# Daemon log
powershell .claude/orch-tools.ps1 daemon-log

# Worker output
cat .claude/workspaces/INIT-XXX/session_output.json

# Token usage (specific initiative)
powershell .claude/orch-tools.ps1 check-worker INIT-XXX
```

## Token Budget Zones

| Zone | Budget Used | Action |
|------|-------------|--------|
| GREEN | 0-50% | Normal operations |
| YELLOW | 50-75% | Delegate everything, no optional work |
| RED | 75-90% | Emergency mode, max delegation, log warning |
| HALT | 90-100% | STOP, write status, set "blocked_budget" |

**Check your budget**: Read `initiatives.json` before major operations

## ORCH-001: The #1 Rule

**NEVER use Task tool (inline agents).** ALWAYS spawn terminal helpers via daemon.

**Orchestrator restrictions**:
- ONLY read `.claude/*.md` files and `initiatives.json`
- NEVER read user code directly
- Spawn helpers for ALL exploration/analysis

**Main worker restrictions**:
- Read files ONLY when: (1) You know exact path, (2) File <100 lines, (3) You're about to edit specific lines
- Spawn Haiku helper for: exploration, analysis, reading large files, batch ops

**Helper protocol**:
- Read `.claude/HELPER_WORKER_SYSTEM.md` first
- Execute instructions EXACTLY, no thinking
- Write findings to `workspace/findings.txt`
- Zero creativity, minimum tokens

## Common Commands

```bash
# Daemon management (from Git Bash on Windows)
powershell .claude/orch-tools.ps1 daemon-status
powershell .claude/orch-tools.ps1 daemon-start
powershell .claude/orch-tools.ps1 daemon-stop
powershell .claude/orch-tools.ps1 daemon-restart

# Check daemon log
powershell .claude/orch-tools.ps1 daemon-log

# Check worker status
powershell .claude/orch-tools.ps1 check-worker INIT-XXX

# View worker token usage
powershell .claude/orch-tools.ps1 session-output INIT-XXX

# Kill process by PID
powershell .claude/orch-tools.ps1 kill-pid 12345

# List all Python processes
powershell .claude/orch-tools.ps1 list-python
```

## Workspace Coordination

### Main → Helper Task Delegation

**Main worker writes** to `workspace/instructions.txt`:
```
---
TASK: update_config_files
FILES: config/api.json, config/db.json
ACTION: replace "old_value" with "new_value"
STATUS: pending
---
```

**Helper reads** instructions.txt, executes, writes results to `workspace/results/`

**Main worker reads** `workspace/findings.txt` when helper writes "COMPLETE" marker

### Helper Reporting Pattern

Helper writes to `workspace/findings.txt`:
```
## EXPLORATION RESULTS

### FILES FOUND
- src/api.ts (127 lines) — REST API endpoints
- src/db.ts (89 lines) — Database connections

### PATTERN MATCHES
Line 45: function connectToServer() {...}
Line 89: class DatabaseClient {...}

EXPLORATION_COMPLETE
```

Main worker polls for "EXPLORATION_COMPLETE" marker (or uses `watch-for.py`)

## Waste Audit (Before Completion)

Every worker MUST add waste audit to progress_log before setting status="done":

```
"waste_audit: tokens_used=8500 (57% of 15k budget), manual_reads=3 (<100 lines pre-edit), helpers_spawned=2, tasks_delegated=5"
```

**Confess violations**:
```
"waste_audit: VIOLATION — used Task tool N times instead of spawning helpers"
"waste_audit: VIOLATION — read N files for exploration instead of spawning helper"
```

## Swarm Architecture (Complex Tasks)

**When to use**: 50+ atomic changes, parallelizable work

**Flow**:
1. Orchestrator spawns 1-3 PLANNER workers (Haiku)
2. Planners decompose task → write `workspace/plan.json`
3. Orchestrator spawns 5-10 EXECUTOR workers (Haiku)
4. Executors poll plan.json, execute tasks in parallel
5. Executors write to `workspace/execution_log.json`

**Benefit**: 10x parallelization, 90% cost savings

**Docs**: `.claude/EXECUTION_SWARM_SYSTEM.md`, `.claude/PLANNER_WORKER_SYSTEM.md`

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Workers not spawning | Check daemon running: `powershell .claude/orch-tools.ps1 daemon-status` |
| Duplicate workers | Fixed in INIT-007, daemon uses atomic manifest claim |
| Token counts wrong | Daemon auto-tracks every 30s, read `initiatives.json` |
| Worker crashed | Daemon auto-resumes (INIT-004), continuation worker spawned |
| Budget exceeded | Desktop alert + alert JSON in `.claude/alerts/` |
| Can't find helper output | Check `workspace/INIT-XXX/findings.txt` |
| Daemon not reloading | Auto-reload on source change (INIT-010), 10s check interval |

## File Watch Utility

```bash
# Wait for helper to finish (zero tokens, pure Python)
python .claude/watch-for.py workspace/INIT-XXX/findings.txt "EXPLORATION_COMPLETE" --timeout=300

# Exit codes: 0 (found), 1 (timeout), 2 (error)
```

## Session Output Format

Workers spawn with `--output-format=json`, stdout contains:
```json
{
  "usage": {
    "input_tokens": 1234,
    "output_tokens": 567,
    "cache_read_input_tokens": 890,
    "cache_creation_input_tokens": 234
  },
  "total_cost_usd": 0.012
}
```

Daemon parses this every 30s → updates `initiatives.json` tokens_used

## Key Docs (Read These)

| File | When to Read |
|------|--------------|
| `MASTER_WORKER_SYSTEM.md` | Main workers (Sonnet/Opus) on boot |
| `HELPER_WORKER_SYSTEM.md` | Helper workers (Haiku) on boot |
| `HELPER_TEMPLATES.md` | When spawning helpers |
| `HAIKU_EFFICIENCY_COMMITMENT.md` | Understand delegation framework |
| `ORCH-001-violations-guide.md` | When unsure about tool usage |
| `.claude/README.md` | System components guide |

## One-Liner Reminders

- **Orchestrator**: Never read user code, spawn helpers instead
- **Main worker**: Read only files you're about to edit (<100 lines)
- **Helper**: Execute exactly, no thinking, minimum tokens
- **Token discipline**: Check budget before major operations
- **Delegation**: Writing 200-token instruction replaces 15k tokens of work
- **Waste audit**: Mandatory before completion, reference actual token counts
- **Swarm**: Use for 50+ changes, 10x parallelization benefit

## Support

- Issues: https://github.com/anthropics/claude-code/issues
- Main README: `../README.md`
- System Guide: `.claude/README.md`
