#!/usr/bin/env python3
"""Orchestrator tools - cross-platform utilities for Claude Code orchestration.

Usage:
    python .claude/orch-tools.py ensure-dirs path1 path2 ...
    python .claude/orch-tools.py file-exists path1 ...
    python .claude/orch-tools.py dir-exists path1 ...
    python .claude/orch-tools.py gen-worker --type main --init INIT-017 --model sonnet --title "Implement feature" --task "task.txt" --budget 75k
    python .claude/orch-tools.py gen-worker --type helper --init INIT-017 --model haiku --title "Catalog files" --task "task.txt" --budget 8k
    python .claude/orch-tools.py gen-manifest --init INIT-017 --workers "INIT-017_main.txt:sonnet:main,INIT-017_helper.txt:haiku:helper"
"""
import sys
import os
import json
import time
import argparse
from datetime import datetime, timezone

# Fix Windows console encoding for Unicode output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# ── Directory/file utilities ──

def ensure_dirs(paths):
    for p in paths:
        os.makedirs(p, exist_ok=True)
        print(f"OK: {p}")

def file_exists(paths):
    for p in paths:
        print(f"{'EXISTS' if os.path.isfile(p) else 'MISSING'}: {p}")

def dir_exists(paths):
    for p in paths:
        print(f"{'EXISTS' if os.path.isdir(p) else 'MISSING'}: {p}")


# ── Worker block templates ──

MAIN_WORKER_TEMPLATE = """MAIN WORKER for {init_id}: {title}
Model: {model_label}
Workspace: .claude/workspaces/{init_id}/

MANDATORY FIRST STEPS (DO THESE BEFORE ANYTHING ELSE):
1. Read .claude/MASTER_WORKER_SYSTEM.md — THIS IS YOUR LAW. Internalize ORCH-001.
2. Read .claude/initiatives.json, find {init_id}
3. Set status to "in_progress" immediately in initiatives.json
4. Ensure workspace directory exists: .claude/workspaces/{init_id}/

ORCH-001 COMPLIANCE (NON-NEGOTIABLE):
- NEVER use the Task tool (inline agents are BANNED)
- NEVER read files to "explore" — SPAWN A TERMINAL HELPER instead
- NEVER read >300 lines manually — spawn a helper to summarize to findings.txt
- ONLY use Read tool for files <100 lines that you are about to IMMEDIATELY edit
- Delegate ALL exploration, analysis, and batch work to terminal-spawned helpers

{task_content}

WORKSPACE FILES:
- instructions.txt: Delegate tasks to helper (you write, helper reads)
- findings.txt: Share discoveries (both read/write)
- results/: Read completed work from helper

SELF-SPAWNING HELPERS:
1. Write helper block: .claude/pending_workers/{init_id}_helper.txt
2. Write manifest: .claude/pending_workers/manifest.json (AFTER block file)
3. Daemon auto-spawns the helper in a new terminal tab
Shortcut: python .claude/orch-tools.py gen-worker --type helper --init {init_id} --model haiku --title "Helper task" --task path/to/task.txt --budget 8k

BUDGET CIRCUIT BREAKER:
- Token budget: {budget}
- 0-50%: Normal ops, delegate aggressively
- 50-75%: Heightened efficiency, delegate EVERYTHING
- 75-90%: EMERGENCY — critical path only
- 90%+: HALT. Write remaining work to instructions.txt. Set status "budget_warning". EXIT.

WASTE AUDIT (MANDATORY AT SESSION END):
Add to progress_log: "waste_audit: manual_reads=N, helpers_spawned=N, tasks_delegated=N, task_tool_violations=0, estimated_savings=Nk tokens"
"""

HELPER_WORKER_TEMPLATE = """HELPER WORKER for {init_id}: {title} — Helper Bot
Model: {model_label}
Workspace: .claude/workspaces/{init_id}/

MANDATORY FIRST STEP:
1. Read .claude/HELPER_WORKER_SYSTEM.md — THIS IS YOUR LAW. Internalize the Zero-Think Protocol.

THEN:
2. Read .claude/initiatives.json, find {init_id}

{task_content}

AFTER completing your task:
- Poll workspace/instructions.txt every 30 seconds for additional tasks
- Execute any additional tasks exactly as described
- When main worker sets initiative status to "done", exit

ZERO-THINK PROTOCOL (NON-NEGOTIABLE):
- DON'T explore beyond your task scope
- DON'T refactor or improve anything
- DON'T reason about architecture — just execute
- If unclear: write "BLOCKED: [question]" in findings.txt — do NOT guess
- NEVER use Task tool / spawn agents. YOU are the cheap layer.

TOKEN BUDGET: {budget}
BUDGET LIMIT: At 80%, wrap up and write what you have. Don't leave incomplete.
"""

MODEL_LABELS = {
    "sonnet": "Sonnet (complex reasoning)",
    "opus": "Opus (highest capability)",
    "haiku": "Haiku (lightweight, cost-efficient — 8x cheaper than Sonnet)",
}

def gen_worker(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", required=True, choices=["main", "helper"])
    parser.add_argument("--init", required=True, help="Initiative ID e.g. INIT-017")
    parser.add_argument("--model", required=True, choices=["haiku", "sonnet", "opus"])
    parser.add_argument("--title", required=True, help="Short worker title")
    parser.add_argument("--task", required=True, help="Path to task content file (plain text)")
    parser.add_argument("--budget", required=True, help="Token budget e.g. 75k")
    parser.add_argument("--out", help="Output path (default: .claude/pending_workers/{init}_{type}.txt)")
    opts = parser.parse_args(args)

    task_path = opts.task
    if not os.path.isfile(task_path):
        print(f"ERROR: Task file not found: {task_path}")
        sys.exit(1)
    with open(task_path, "r", encoding="utf-8") as f:
        task_content = f.read().strip()

    template = MAIN_WORKER_TEMPLATE if opts.type == "main" else HELPER_WORKER_TEMPLATE
    block = template.format(
        init_id=opts.init,
        title=opts.title,
        model_label=MODEL_LABELS.get(opts.model, opts.model),
        task_content=task_content,
        budget=opts.budget,
    )

    out_path = opts.out or f".claude/pending_workers/{opts.init}_{opts.type}.txt"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(block)
    print(f"OK: {out_path} ({opts.type} worker, {opts.model}, {opts.budget})")


# ── Manifest generation ──

def gen_manifest(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("--init", required=True, help="Initiative ID(s) e.g. INIT-017 or INIT-017,INIT-023")
    parser.add_argument("--workers", required=True, help="Comma-separated file:model:type e.g. INIT-017_main.txt:sonnet:main,INIT-017_helper.txt:haiku:helper")
    opts = parser.parse_args(args)

    workers = []
    for entry in opts.workers.split(","):
        parts = entry.strip().split(":")
        if len(parts) != 3:
            print(f"ERROR: Bad worker spec '{entry}' — expected file:model:type")
            sys.exit(1)
        workers.append({"file": parts[0], "model": parts[1], "type": parts[2]})

    manifest = {
        "initiative_id": opts.init,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "workers": workers,
    }

    out_path = ".claude/pending_workers/manifest.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"OK: {out_path} ({len(workers)} workers)")


# ── Worker output monitoring ──

def worker_output(args):
    """Read worker output/logs for an initiative. Shows what each worker produced.

    Usage:
        worker-output INIT-017              # All workers for initiative
        worker-output INIT-017 --tail 50    # Last 50 lines per worker
        worker-output INIT-017 --worker main  # Specific worker type
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("init_id", help="Initiative ID e.g. INIT-017")
    parser.add_argument("--tail", type=int, default=0, help="Show last N lines (0=all)")
    parser.add_argument("--worker", help="Filter by worker type substring (e.g. main, helper)")
    opts = parser.parse_args(args)

    workspace = os.path.join(".claude", "workspaces", opts.init_id)
    if not os.path.isdir(workspace):
        print(f"NO WORKSPACE: {workspace}")
        return

    found = False

    # Check output JSON files (claude -p output)
    for f in sorted(os.listdir(workspace)):
        if not f.endswith("_output.txt"):
            continue
        if opts.worker and opts.worker.lower() not in f.lower():
            continue

        found = True
        filepath = os.path.join(workspace, f)
        print(f"\n{'='*60}")
        print(f"OUTPUT: {f}")
        print(f"SIZE: {os.path.getsize(filepath)} bytes")
        print(f"{'='*60}")

        try:
            with open(filepath, "r", encoding="utf-8") as fh:
                content = fh.read()
        except UnicodeDecodeError:
            with open(filepath, "r", encoding="utf-16-le") as fh:
                content = fh.read()

        if not content.strip():
            print("(empty)")
            continue

        lines = content.splitlines()
        if opts.tail and len(lines) > opts.tail:
            print(f"... ({len(lines) - opts.tail} lines skipped) ...")
            lines = lines[-opts.tail:]
        print("\n".join(lines))

    # Check log files
    logs_dir = os.path.join(workspace, "logs")
    if os.path.isdir(logs_dir):
        for f in sorted(os.listdir(logs_dir)):
            if not f.endswith(".log"):
                continue
            if opts.worker and opts.worker.lower() not in f.lower():
                continue

            found = True
            filepath = os.path.join(logs_dir, f)
            print(f"\n{'='*60}")
            print(f"LOG: {f}")
            print(f"SIZE: {os.path.getsize(filepath)} bytes")
            print(f"{'='*60}")

            with open(filepath, "r", encoding="utf-8") as fh:
                lines = fh.readlines()

            if not lines:
                print("(empty)")
                continue

            if opts.tail and len(lines) > opts.tail:
                print(f"... ({len(lines) - opts.tail} lines skipped) ...")
                lines = lines[-opts.tail:]
            print("".join(lines))

    # Check workspace communication files
    for comm_file in ["findings.txt", "instructions.txt"]:
        filepath = os.path.join(workspace, comm_file)
        if os.path.isfile(filepath):
            found = True
            size = os.path.getsize(filepath)
            print(f"\n{'='*60}")
            print(f"WORKSPACE: {comm_file} ({size} bytes)")
            print(f"{'='*60}")
            with open(filepath, "r", encoding="utf-8") as fh:
                content = fh.read()
            if content.strip():
                lines = content.splitlines()
                if opts.tail and len(lines) > opts.tail:
                    print(f"... ({len(lines) - opts.tail} lines skipped) ...")
                    lines = lines[-opts.tail:]
                print("\n".join(lines))
            else:
                print("(empty)")

    # Check PID files for running status
    pids_dir = os.path.join(workspace, "pids")
    if os.path.isdir(pids_dir):
        pid_files = [f for f in os.listdir(pids_dir) if f.endswith(".pid")]
        if pid_files:
            print(f"\n{'='*60}")
            print(f"WORKER PIDS:")
            print(f"{'='*60}")
            for f in pid_files:
                filepath = os.path.join(pids_dir, f)
                with open(filepath, "r") as fh:
                    pid = fh.read().strip()
                # Check if process is running
                try:
                    import subprocess
                    result = subprocess.run(
                        ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                        capture_output=True, text=True, timeout=5
                    )
                    running = pid in result.stdout
                except Exception:
                    running = False
                status = "RUNNING" if running else "DEAD"
                print(f"  {f.replace('.pid','')}: PID {pid} [{status}]")

    if not found:
        print(f"No output files found for {opts.init_id}")
        print(f"Workspace contents: {os.listdir(workspace) if os.path.isdir(workspace) else 'N/A'}")


def worker_status(args):
    """Quick status of all active workers across all initiatives.

    Usage: worker-status
    """
    workspaces = os.path.join(".claude", "workspaces")
    if not os.path.isdir(workspaces):
        print("No workspaces directory found.")
        return

    for init_id in sorted(os.listdir(workspaces)):
        workspace = os.path.join(workspaces, init_id)
        if not os.path.isdir(workspace):
            continue

        # Gather info
        outputs = [f for f in os.listdir(workspace) if f.endswith("_output.txt")]
        pids_dir = os.path.join(workspace, "pids")
        findings = os.path.join(workspace, "findings.txt")

        has_findings = os.path.isfile(findings) and os.path.getsize(findings) > 0

        print(f"\n{init_id}:")

        if not outputs and not os.path.isdir(pids_dir):
            print(f"  (no worker output yet)")
            continue

        # Check each output file
        for out_file in outputs:
            filepath = os.path.join(workspace, out_file)
            size = os.path.getsize(filepath)
            worker_name = out_file.replace("_output.txt", "")

            # Check PID
            pid_status = "?"
            if os.path.isdir(pids_dir):
                # Try to match pid file
                for pf in os.listdir(pids_dir):
                    pid_path = os.path.join(pids_dir, pf)
                    try:
                        with open(pid_path) as fh:
                            pid = fh.read().strip()
                        import subprocess
                        result = subprocess.run(
                            ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                            capture_output=True, text=True, timeout=5
                        )
                        pid_status = "RUNNING" if pid in result.stdout else "DONE"
                    except Exception:
                        pid_status = "?"

            print(f"  {worker_name}: {size} bytes output [{pid_status}]")

        if has_findings:
            # Show first line of findings as summary
            with open(findings) as fh:
                first_line = fh.readline().strip()
            print(f"  findings.txt: {first_line[:80]}")


# ── Worker completion watcher ──

def watch_workers(args):
    """Block until all workers for an initiative finish. Designed to run as a
    background task so the orchestrator gets a <task-notification> on completion.

    Usage:
        python .claude/orch-tools.py watch-workers INIT-017+023-v2
        python .claude/orch-tools.py watch-workers INIT-017+023-v2 --poll 15 --timeout 600
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("init_id", help="Initiative workspace ID to watch")
    parser.add_argument("--poll", type=int, default=3, help="Poll interval in seconds (default 3)")
    parser.add_argument("--timeout", type=int, default=1800, help="Max wait in seconds (default 1800 = 30min)")
    opts = parser.parse_args(args)

    import subprocess as sp

    workspace = os.path.join(".claude", "workspaces", opts.init_id)
    pids_dir = os.path.join(workspace, "pids")

    if not os.path.isdir(workspace):
        print(f"ERROR: Workspace {workspace} not found")
        sys.exit(1)

    print(f"Watching workers for {opts.init_id} (poll={opts.poll}s, timeout={opts.timeout}s)")
    elapsed = 0

    while elapsed < opts.timeout:
        time.sleep(opts.poll)
        elapsed += opts.poll

        # Check if any workers are still running via PID files
        any_running = False
        worker_summary = []

        if os.path.isdir(pids_dir):
            for pf in os.listdir(pids_dir):
                if not pf.endswith(".pid"):
                    continue
                pid_path = os.path.join(pids_dir, pf)
                worker_name = pf.replace(".pid", "")
                try:
                    with open(pid_path) as fh:
                        pid = fh.read().strip()
                    # Check if process alive
                    if sys.platform == "win32":
                        result = sp.run(
                            ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                            capture_output=True, text=True, timeout=5
                        )
                        running = pid in result.stdout
                    else:
                        try:
                            os.kill(int(pid), 0)
                            running = True
                        except OSError:
                            running = False

                    if running:
                        any_running = True
                        worker_summary.append(f"  {worker_name}: RUNNING (PID {pid})")
                    else:
                        worker_summary.append(f"  {worker_name}: FINISHED (PID {pid})")
                except Exception:
                    worker_summary.append(f"  {worker_name}: UNKNOWN")

        # If no PID dir or no running workers, check if output files exist
        if not any_running:
            # Collect output summaries
            outputs = []
            for f in sorted(os.listdir(workspace)):
                if f.endswith("_output.txt"):
                    filepath = os.path.join(workspace, f)
                    size = os.path.getsize(filepath)
                    # Read last 3 lines as summary
                    with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
                        lines = fh.readlines()
                    tail = "".join(lines[-3:]).strip() if lines else "(empty)"
                    outputs.append(f"  {f}: {size} bytes\n    Last output: {tail[:200]}")

            findings_path = os.path.join(workspace, "findings.txt")
            findings_summary = ""
            if os.path.isfile(findings_path) and os.path.getsize(findings_path) > 0:
                with open(findings_path, "r", encoding="utf-8", errors="replace") as fh:
                    first_line = fh.readline().strip()
                findings_summary = f"\n  findings.txt: {first_line[:100]}"

            print(f"\n=== ALL WORKERS FINISHED for {opts.init_id} ===")
            print(f"Elapsed: {elapsed}s")
            print(f"\nWorker status:")
            print("\n".join(worker_summary) if worker_summary else "  (no PID files)")
            print(f"\nOutputs:")
            print("\n".join(outputs) if outputs else "  (no output files)")
            if findings_summary:
                print(findings_summary)
            print(f"\nRun: python .claude/orch-tools.py worker-output {opts.init_id}")
            sys.exit(0)

        # Still running — print brief heartbeat
        running_count = sum(1 for s in worker_summary if "RUNNING" in s)
        print(f"  [{elapsed}s] {running_count} worker(s) still running...")

    print(f"\nTIMEOUT after {opts.timeout}s — workers may still be running")
    sys.exit(1)


# ── Generate SESSION_TLDR.md from initiatives.json ──

def gen_tldr(args):
    """Generate SESSION_TLDR.md from initiatives.json.

    Usage: python orch-tools.py gen-tldr
    """
    claude_dir = os.path.dirname(os.path.abspath(__file__))
    initiatives_path = os.path.join(claude_dir, "initiatives.json")
    tldr_path = os.path.join(claude_dir, "SESSION_TLDR.md")

    if not os.path.exists(initiatives_path):
        print(f"ERROR: {initiatives_path} not found")
        return

    try:
        with open(initiatives_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"ERROR reading initiatives.json: {e}")
        return

    initiatives = data.get("initiatives", [])

    # Separate by status
    done = [i for i in initiatives if i.get("status") == "done"]
    active = [i for i in initiatives if i.get("status") in ("in_progress", "planned")]
    blocked = [i for i in initiatives if i.get("status") == "blocked"]

    # Sort by last_updated or created (newest first)
    done.sort(key=lambda x: x.get("last_updated") or x.get("created"), reverse=True)
    active.sort(key=lambda x: x.get("created"), reverse=True)

    # Calculate stats
    total_budget = sum(i.get("token_budget", 0) for i in initiatives)
    total_spent = sum(i.get("tokens_used", 0) for i in initiatives)

    # Build TLDR
    lines = [
        "# What's Going On",
        "",
        "*Auto-generated from initiatives.json. Last updated: " + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC") + "*",
        "",
        "---",
        "",
        "## Active Work",
        "",
    ]

    if active:
        for init in active[:5]:  # Show top 5 active
            status = init.get("status", "?")
            title = init.get("title", "Untitled")
            iid = init.get("id", "?")
            tokens = init.get("tokens_used", 0)
            budget = init.get("token_budget", 0)
            pct = f"{100*tokens//budget}%" if budget else "?"
            lines.append(f"- **[{iid}]** {title} ({pct} of {budget//1000}k)")
    else:
        lines.append("Nothing active right now.")

    lines.extend(["", "## Recently Completed", ""])

    if done:
        for init in done[:10]:  # Show top 10 completed
            title = init.get("title", "Untitled")
            iid = init.get("id", "?")
            lines.append(f"- [{iid}] {title}")
    else:
        lines.append("No completed initiatives yet.")

    lines.extend([
        "",
        "## Budget Summary",
        "",
        f"**Total**: {total_spent:,} / {total_budget:,} tokens ({100*total_spent//total_budget if total_budget else 0}%)",
        f"**Active initiatives**: {len(active)}",
        f"**Completed**: {len(done)}",
        f"**Blocked**: {len(blocked)}",
        "",
        "---",
        "",
        "<!-- Worker updates appended here -->",
    ])

    # Write TLDR
    tldr_content = "\n".join(lines)
    try:
        with open(tldr_path, 'w', encoding='utf-8') as f:
            f.write(tldr_content)
        print(f"✓ Generated {tldr_path}")
        print(f"  Active: {len(active)} | Completed: {len(done)} | Budget: {total_spent}/{total_budget}")
    except Exception as e:
        print(f"ERROR writing {tldr_path}: {e}")


# ── Command dispatch ──

COMMANDS = {
    "ensure-dirs": ensure_dirs,
    "file-exists": file_exists,
    "dir-exists": dir_exists,
    "gen-worker": gen_worker,
    "gen-manifest": gen_manifest,
    "worker-output": worker_output,
    "worker-status": worker_status,
    "watch-workers": watch_workers,
    "gen-tldr": gen_tldr,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"Commands: {', '.join(COMMANDS.keys())}")
        sys.exit(1)
    COMMANDS[sys.argv[1]](sys.argv[2:])
