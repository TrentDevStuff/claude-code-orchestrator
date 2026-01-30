# .claude/ Directory — System Components Guide

This directory contains all orchestrator system files. This guide helps you understand what each file does and how they fit together.

## Directory Structure

```
.claude/
├── System Prompts & Rules
│   ├── master-prompt.md                    Orchestrator role (auto-loaded on launch)
│   ├── MASTER_WORKER_SYSTEM.md             Main worker rules & ORCH-001 enforcement
│   ├── HELPER_WORKER_SYSTEM.md             Helper zero-think protocol
│   ├── PLANNER_WORKER_SYSTEM.md            Swarm planner rules
│   └── EXECUTION_SWARM_SYSTEM.md           Swarm executor protocol
│
├── Efficiency & Cost Management
│   ├── HAIKU_EFFICIENCY_COMMITMENT.md      Cost analysis & delegation framework
│   ├── MODEL_CONSENT_PROMPT.md             Sonnet/Opus worker commitment
│   ├── COMMITMENT_MANIFEST.md              System-wide efficiency manifesto
│   └── ORCH-001-violations-guide.md        Violation patterns reference
│
├── Templates & References
│   ├── HELPER_TEMPLATES.md                 Copy-paste helper blocks
│   ├── SWARM_EXAMPLES.md                   Example swarm decompositions
│   ├── SWARM_QUICK_REFERENCE.md            Swarm commands lookup
│   ├── IMPLEMENTATION_SUMMARY.md           Swarm architecture overview
│   ├── MIGRATION_GUIDE.md                  System upgrade guide
│   └── QUICK_REFERENCE.md                  One-page user cheat sheet
│
├── Operational Scripts
│   ├── worker-daemon.py                    Background daemon (lifecycle mgmt)
│   ├── watch-for.py                        File watcher utility
│   ├── orch-tools.ps1                      PowerShell management utility
│   └── prompts/
│       ├── haiku-init.txt                  Haiku worker boot prompt
│       └── opus-sonnet-init.txt            Sonnet/Opus worker boot prompt
│
└── Runtime State (created automatically)
    ├── initiatives.json                    Master state file
    ├── .daemon-pid                         Daemon process ID
    ├── .daemon-state.json                  Daemon runtime state
    ├── pending_workers/                    Manifest drop folder
    ├── workspaces/                         Per-initiative work dirs
    └── alerts/                             Budget alert files
```

## Core System Prompts

### master-prompt.md
**Purpose**: Defines the orchestrator role and responsibilities
**Read by**: Master orchestrator session (auto-loaded on launch)
**Key sections**:
- ORCH-001 enforcement mandate (orchestrator NEVER reads user code)
- Initiative planning workflow
- Manifest generation instructions
- Tool usage restrictions (spawns helpers, never explores manually)

### MASTER_WORKER_SYSTEM.md
**Purpose**: Rules for main workers (Sonnet/Opus)
**Read by**: All main workers (first step after boot)
**Key rules**:
- ORCH-001: NEVER use Task tool, only daemon-spawned terminal helpers
- Token budget discipline (GREEN/YELLOW/RED zones)
- Tool restrictions (Read only .claude files, spawn helpers for everything else)
- Mandatory waste audit on completion

### HELPER_WORKER_SYSTEM.md
**Purpose**: Zero-think protocol for Haiku helpers
**Read by**: All helper workers (first step after boot)
**Key protocol**:
- Execute instructions EXACTLY, no creativity
- Poll instructions.txt, write to findings.txt
- Minimize tokens (no exploration, no thinking, just execute)
- Cost efficiency (Haiku is 8x cheaper than Sonnet)

### PLANNER_WORKER_SYSTEM.md & EXECUTION_SWARM_SYSTEM.md
**Purpose**: Swarm architecture for complex task decomposition
**When used**: For tasks requiring 50+ atomic changes
**Flow**: Planners decompose → write plan.json → Executors execute in parallel
**Benefit**: 10x parallelization for batch operations

## Efficiency & Cost Framework

### HAIKU_EFFICIENCY_COMMITMENT.md
**Purpose**: Cost multiplier analysis and delegation framework
**Key insight**: Haiku is 3.75x cheaper than Sonnet, 18.75x cheaper than Opus
**Framework**: 5 delegation scenarios, 5 documented exceptions, decision tree
**Commitment**: Workers agree to delegate aggressively to maximize efficiency

### ORCH-001-violations-guide.md
**Purpose**: Quick reference for what NOT to do
**Contains**: Common violation patterns with WRONG/RIGHT examples
**Use case**: Workers check this when unsure about tool usage

## Templates & Quick References

### HELPER_TEMPLATES.md
**Purpose**: Copy-paste ready helper block templates
**Contains**: 4 templates (EXPLORATION, CODE_SEARCH, FILE_AUDIT, CONTEXT)
**Usage**: Workers copy template, fill in specifics, write to pending_workers/

### QUICK_REFERENCE.md
**Purpose**: One-page cheat sheet for users and workers
**Contains**: Common commands, file locations, quick troubleshooting

## Operational Scripts

### worker-daemon.py (Background Daemon)
**Purpose**: Filesystem watcher and worker lifecycle manager
**Runs as**: Background Python process (launched by claude-orch.bat/sh)
**Key responsibilities**:
- Watch `pending_workers/` for manifest.json files
- Spawn new workers in terminal tabs when manifest detected
- Monitor initiatives.json for completion (auto-close finished tabs)
- Track token usage and raise budget alerts
- Auto-reload when source file changes (development feature)

**Key methods**:
- `spawn_workers()`: Creates new terminal tabs with Claude Code sessions
- `check_completion()`: Monitors initiatives.json, closes done workers
- `check_worker_token_usage()`: Parses session output, updates token counts
- `_auto_reload()`: Detects source changes, restarts daemon preserving state

### watch-for.py (File Watcher Utility)
**Purpose**: Poll a file for a specific string, exit when found
**Usage**: `python .claude/watch-for.py <file> <search_string> [--timeout]`
**Use case**: Launchers use this to wait for "EXPLORATION_COMPLETE" in findings.txt
**Cost**: Zero Claude tokens (pure Python CPU)

### orch-tools.ps1 (Management Utility)
**Purpose**: PowerShell commands for system management from Git Bash
**Commands**:
- `daemon-status`: Check if daemon is running
- `daemon-log`: Show daemon log output
- `daemon-start/stop/restart`: Lifecycle management
- `check-worker <init_id>`: Check worker status
- `session-output <init_id>`: View worker token usage

**Usage**: `powershell .claude/orch-tools.ps1 daemon-status`

## Runtime State Files

### initiatives.json
**Purpose**: Master state file for all initiatives
**Schema**:
```json
{
  "initiatives": [
    {
      "id": "INIT-XXX",
      "title": "Task description",
      "complexity": "low|medium|high",
      "token_budget": 15000,
      "tokens_used": 8500,
      "status": "planned|in_progress|done|blocked",
      "workspace": ".claude/workspaces/INIT-XXX",
      "progress_log": ["phase_1_complete: ...", "phase_2_in_progress: ..."],
      "last_updated": "2026-01-29T12:00:00Z"
    }
  ]
}
```

**Updated by**:
- Orchestrator: Creates initiatives, sets status
- Daemon: Updates tokens_used every 30 seconds (auto-tracking)
- Workers: Append to progress_log, set status to done

### .daemon-pid
**Purpose**: Single line containing daemon process ID
**Usage**: Launcher checks this to kill old daemon before starting new one

### .daemon-state.json
**Purpose**: Daemon runtime state (persists across restarts)
**Contains**: Active worker PIDs, completion grace periods, process tracking
**Lifecycle**: Written before daemon reload, read on boot, deleted after restore

## Runtime Directories

### pending_workers/
**Purpose**: Drop folder for worker spawn manifests
**Workflow**:
1. Worker/orchestrator writes manifest.json here
2. Daemon detects file (filesystem watcher)
3. Daemon spawns new worker tab
4. Daemon deletes manifest (consumed)

**Manifest format**:
```json
{
  "initiative_id": "INIT-XXX",
  "workers": [
    {"file": "INIT-XXX_helper.txt", "model": "haiku", "type": "helper"}
  ]
}
```

**Note**: Always write block file FIRST, manifest SECOND (manifest triggers daemon)

### workspaces/
**Purpose**: Per-initiative working directories
**Structure**: `workspaces/INIT-XXX/` (created automatically)
**Files per workspace**:
- `instructions.txt`: Task queue (main writes, helpers read and execute)
- `findings.txt`: Shared discoveries (helpers write analysis results)
- `results/`: Completed task results
- `execution_log.json`: Swarm execution tracking
- `plan.json`: Decomposed task plan (swarm mode)
- `session_output.json`: Worker stdout with token usage data

**Coordination pattern**:
- Main worker writes task to instructions.txt
- Helper polls instructions.txt (every 10 seconds)
- Helper executes, writes results to results/
- Helper writes findings to findings.txt
- Main worker reads findings.txt when "COMPLETE" marker appears

### alerts/
**Purpose**: Budget exceeded notifications
**Trigger**: Daemon writes alert when initiative tokens > budget
**Format**: `INIT-XXX_budget.json` with alert details
**Delivery**: Desktop notification + JSON file for inspection

## Key Workflows

### Worker Spawning
1. Orchestrator/worker writes `pending_workers/INIT-XXX_worker.txt` (block content)
2. Orchestrator/worker writes `pending_workers/manifest.json` (triggers daemon)
3. Daemon detects manifest via filesystem watcher
4. Daemon spawns `claude -p --model=haiku --output-format=json` in new terminal tab
5. Worker boots, reads .claude/HELPER_WORKER_SYSTEM.md (or MASTER_WORKER_SYSTEM.md)
6. Worker executes task, writes to initiatives.json and workspace/

### Token Tracking
1. Daemon spawns workers with `--output-format=json`
2. Worker stdout redirected to `workspace/session_output.json`
3. Daemon parses JSON every 30 seconds (looks for `usage.*_tokens` fields)
4. Daemon updates `initiatives.json` tokens_used field
5. Workers read initiatives.json to check budget zones (GREEN/YELLOW/RED)

### Worker Completion
1. Worker sets `status: "done"` in initiatives.json
2. Worker writes final waste_audit to progress_log
3. Daemon detects status change (check_completion loop)
4. Daemon waits 5 seconds (grace period for final writes)
5. Daemon kills worker process (auto-close tab)

## Common Questions

**Q: Where do I find system rules for workers?**
A: `MASTER_WORKER_SYSTEM.md` for main workers, `HELPER_WORKER_SYSTEM.md` for helpers

**Q: How do I spawn a helper?**
A: Copy template from `HELPER_TEMPLATES.md`, write to `pending_workers/`, then write manifest.json

**Q: Where do workers write their output?**
A: `workspaces/INIT-XXX/findings.txt` for analysis, `results/` for task output

**Q: How do I check token usage?**
A: Read `initiatives.json` tokens_used field (auto-updated by daemon every 30s)

**Q: What if a worker crashes?**
A: Daemon auto-resumes crashed workers (INIT-004 feature) — continuation worker reads progress_log and resumes

**Q: How do I debug daemon issues?**
A: `powershell .claude/orch-tools.ps1 daemon-log` shows daemon output

**Q: What's the difference between main and helper workers?**
A: Main workers (Sonnet/Opus) plan and coordinate. Helpers (Haiku) execute simple tasks at 8x lower cost.

## See Also

- Main README.md: Project overview and quick start
- QUICK_REFERENCE.md: One-page cheat sheet
- HAIKU_EFFICIENCY_COMMITMENT.md: Full delegation framework
- HELPER_TEMPLATES.md: Ready-to-use helper blocks
