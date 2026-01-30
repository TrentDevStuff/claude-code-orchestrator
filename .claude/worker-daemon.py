#!/usr/bin/env python3
"""
Worker Daemon - Autonomous worker spawning and lifecycle management

Watches .claude/pending_workers/ for manifest.json files.
When found, spawns Claude Code workers in Windows Terminal tabs using:
  claude --model {model} --dangerously-skip-permissions (interactive mode)

Workers run fully autonomously - no human paste/interaction needed.
Communication happens through .claude/initiatives.json and workspace directories.
"""

import json
import os
import sys
import time
import subprocess
import shutil
import threading
import platform
import signal
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

try:
    import psutil
except ImportError:
    psutil = None


# Platform detection constants
IS_WINDOWS = platform.system() == "Windows"
IS_MAC = platform.system() == "Darwin"
IS_LINUX = platform.system() == "Linux"


class WorkerDaemon:
    def __init__(self):
        self.project_dir = Path.cwd()
        self.base_dir = self.project_dir / ".claude"
        self.pending_dir = self.base_dir / "pending_workers"
        self.workspaces_dir = self.base_dir / "workspaces"
        self.initiatives_file = self.base_dir / "initiatives.json"
        self.pid_file = self.base_dir / ".daemon-pid"
        self.state_file = self.base_dir / ".daemon-state.json"

        # Track active workers: {initiative_id: {worker_file: info}}
        self.active_workers = {}

        # Track completion timestamps for grace period: {initiative_id: timestamp}
        self._completion_grace = {}

        # Prevent concurrent/duplicate spawn_workers calls (race condition guard)
        self._spawn_lock = threading.Lock()

        # Source file self-watch for auto-reload
        self._source_path = os.path.abspath(__file__)
        self._source_mtime = os.path.getmtime(self._source_path)

        # Ensure directories exist
        self.pending_dir.mkdir(parents=True, exist_ok=True)
        self.workspaces_dir.mkdir(parents=True, exist_ok=True)

        # Restore state from previous daemon instance (if auto-reloaded)
        self._restore_state()

        # Kill-and-replace: if an old daemon is running, kill it so we take over
        if self.pid_file.exists():
            try:
                old_pid = int(self.pid_file.read_text().strip())
                if old_pid != os.getpid() and self._is_process_running(old_pid):
                    print(f"Killing old daemon (PID: {old_pid}) — replacing with fresh instance.")
                    try:
                        if IS_WINDOWS:
                            subprocess.run(
                                ["taskkill", "/F", "/PID", str(old_pid)],
                                capture_output=True, timeout=5
                            )
                        else:
                            os.kill(old_pid, signal.SIGKILL)
                    except Exception:
                        pass
                    time.sleep(1)
            except (ValueError, OSError):
                pass  # Stale PID file, safe to overwrite

        # Save our PID
        self.pid_file.write_text(str(os.getpid()))

        print("=" * 56)
        print("  WORKER DAEMON - Autonomous Worker Management")
        print("=" * 56)
        print(f"  PID:     {os.getpid()}")
        print(f"  Project: {self.project_dir}")
        print(f"  Watch:   {self.pending_dir}")
        print()

    def _is_process_running(self, pid):
        """Check if a process with the given PID exists (cross-platform)."""
        try:
            if psutil:
                return psutil.pid_exists(pid)
            elif IS_WINDOWS:
                result = subprocess.run(
                    ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                    capture_output=True, text=True, timeout=5
                )
                return str(pid) in result.stdout
            else:
                # Unix: sending signal 0 checks existence without killing
                os.kill(pid, 0)
                return True
        except (OSError, ProcessLookupError):
            return False
        except Exception:
            return False

    def _restore_state(self):
        """Restore daemon state from previous instance after auto-reload."""
        if not self.state_file.exists():
            return

        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                state = json.load(f)

            self.active_workers = state.get("active_workers", {})
            self._completion_grace = state.get("completion_grace", {})

            print("[AUTO-RELOAD] Restored state from previous daemon instance:")
            print(f"  Active workers: {len(self.active_workers)} initiatives")
            print(f"  Completion grace: {len(self._completion_grace)} initiatives")

            # Delete state file after successful restoration
            self.state_file.unlink()
        except Exception as e:
            print(f"[WARN] Failed to restore daemon state: {e}")
            # Clean up corrupted state file
            try:
                self.state_file.unlink()
            except Exception:
                pass

    def _save_state(self):
        """Save daemon state for restoration after auto-reload."""

        def _make_serializable(obj):
            """Convert Path objects and other non-serializable types to strings."""
            if isinstance(obj, dict):
                return {str(k): _make_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [_make_serializable(item) for item in obj]
            elif isinstance(obj, Path):
                return str(obj)
            return obj

        state = {
            "active_workers": _make_serializable(self.active_workers),
            "completion_grace": _make_serializable(self._completion_grace),
        }

        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to save daemon state: {e}")
            return False

    def _check_source_change(self):
        """Check if the daemon's source file has been modified.

        If changed, wait 2 seconds (cooldown for writer to finish),
        then auto-reload the daemon.
        """
        try:
            current_mtime = os.path.getmtime(self._source_path)

            if current_mtime != self._source_mtime:
                print("\n" + "=" * 56)
                print("  SOURCE FILE CHANGED - AUTO-RELOADING DAEMON")
                print("=" * 56)
                print(f"  Source: {self._source_path}")
                print(f"  Old mtime: {self._source_mtime}")
                print(f"  New mtime: {current_mtime}")
                print()

                # 2-second cooldown to let writer finish
                print("  Waiting 2 seconds for writer to finish...")
                time.sleep(2)

                self._auto_reload()
        except Exception as e:
            print(f"[WARN] Failed to check source file change: {e}")

    def _auto_reload(self):
        """Auto-reload the daemon by saving state and re-executing itself."""
        print("  Saving daemon state...")
        if not self._save_state():
            print("[ERROR] Failed to save state, aborting reload.")
            return

        print("  Stopping filesystem observer...")
        # Observer will be stopped in the finally block of run()

        print("  Re-executing daemon...")
        print()

        # Platform-specific re-exec
        if IS_WINDOWS:
            # Windows: spawn new process then exit
            subprocess.Popen([sys.executable] + sys.argv)
            sys.exit(0)
        else:
            # Unix: replace current process with new one
            os.execv(sys.executable, [sys.executable] + sys.argv)

    def _generate_worker_script(self, script_file, pid_file, tab_title, model, block_file, workspace_dir=None):
        """Generate platform-specific worker launch script.

        CRITICAL: Block content must be read into a variable and passed as
        a CLI argument, NOT piped via stdin.  Piping destroys the TTY and
        breaks Ink's raw-mode requirement for interactive Claude sessions.
        Passing raw text as inline argument breaks on shell-special chars
        like '->'.  Reading into a variable first handles both problems:
        stdin stays as TTY, and PowerShell/bash pass the variable content
        as a single properly-quoted argument.
        """
        block_abs = block_file.absolute()

        if IS_WINDOWS:
            # PowerShell script — read file into variable, pass as argument
            pid_file_abs = pid_file.absolute()
            script_content = (
                f"$PID | Out-File -FilePath '{pid_file_abs}' -NoNewline\n"
                f"Write-Host ''\n"
                f"Write-Host '=== {tab_title} ===' -ForegroundColor Cyan\n"
                f"Write-Host 'Model: {model}' -ForegroundColor Gray\n"
                f"Write-Host 'Launching worker...'\n"
                f"Write-Host ''\n"
                f"$prompt = Get-Content -Path '{block_abs}' -Raw -Encoding UTF8\n"
            )
            if workspace_dir:
                output_file = (workspace_dir / "session_output.json").absolute()
                script_content += (
                    f"$output = '{output_file}'\n"
                    f"claude -p \"$prompt\" --model {model} --dangerously-skip-permissions --output-format json 2>&1 | Out-File -FilePath $output -Encoding UTF8\n"
                )
            else:
                script_content += (
                    f"claude -p \"$prompt\" --model {model} --dangerously-skip-permissions --output-format json\n"
                )
        else:
            # Bash script — read file into variable, pass as quoted argument
            pid_file_abs = pid_file.absolute()
            script_content = (
                f"#!/bin/bash\n"
                f"echo $$ > {pid_file_abs}\n"
                f"echo ''\n"
                f"echo '=== {tab_title} ==='\n"
                f"echo 'Model: {model}'\n"
                f"echo 'Launching worker...'\n"
                f"echo ''\n"
                f"prompt=$(cat '{block_abs}')\n"
            )
            if workspace_dir:
                output_file = (workspace_dir / "session_output.json").absolute()
                script_content += (
                    f"output='{output_file}'\n"
                    f"claude -p \"$prompt\" --model {model} --dangerously-skip-permissions --output-format json > \"$output\" 2>&1\n"
                )
            else:
                script_content += (
                    f"claude -p \"$prompt\" --model {model} --dangerously-skip-permissions --output-format json\n"
                )

        script_file.write_text(script_content, encoding="utf-8")

        # Make bash scripts executable on Unix
        if not IS_WINDOWS:
            os.chmod(script_file, 0o755)

        return script_file

    def _show_notification(self, title, message, notification_type="info"):
        """Show platform-specific notification.

        Args:
            title: Notification title
            message: Notification message
            notification_type: "info" or "warning"
        """
        try:
            if IS_WINDOWS:
                # Windows Forms MessageBox via PowerShell
                icon = "Information" if notification_type == "info" else "Warning"
                subprocess.Popen([
                    "powershell", "-Command",
                    f"[System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms') | Out-Null; "
                    f"[System.Windows.Forms.MessageBox]::Show('{message}', '{title}', 'OK', '{icon}')"
                ], creationflags=0x00000008)  # CREATE_NO_WINDOW
            elif IS_MAC:
                # macOS: osascript notification
                subprocess.Popen([
                    "osascript", "-e",
                    f'display notification "{message}" with title "{title}"'
                ])
            else:
                # Linux: notify-send (most common), fallback to console
                if shutil.which("notify-send"):
                    urgency = "critical" if notification_type == "warning" else "normal"
                    subprocess.Popen(["notify-send", "-u", urgency, title, message])
                else:
                    # Fallback: just print to console
                    print(f"\n[NOTIFICATION] {title}: {message}\n")
        except Exception:
            # Fallback: print to console
            print(f"\n[NOTIFICATION] {title}: {message}\n")

    def _get_terminal_command(self, workers_data):
        """Build platform-specific terminal spawning command."""
        if IS_WINDOWS:
            # Windows Terminal multi-tab command
            wt_cmd = ["wt"]
            for idx, (script_file, tab_title) in enumerate(workers_data):
                if idx > 0:
                    wt_cmd.append(";")
                wt_cmd.extend([
                    "new-tab",
                    "-d", str(self.project_dir),
                    "--title", tab_title,
                    "powershell", "-NoExit", "-ExecutionPolicy", "Bypass",
                    "-File", str(script_file.absolute()),
                ])
            return wt_cmd

        elif IS_MAC:
            # macOS: use osascript to open tabs in Terminal.app
            # Return list of individual commands (we'll execute them separately)
            commands = []
            for script_file, tab_title in workers_data:
                script_abs = script_file.absolute()
                osascript_cmd = [
                    "osascript", "-e",
                    f'tell application "Terminal" to do script "bash \\"{script_abs}\\""'
                ]
                commands.append(osascript_cmd)
            return commands

        else:
            # Linux: use gnome-terminal (fallback to xterm if not available)
            terminal_bin = shutil.which("gnome-terminal") or shutil.which("xterm") or "x-terminal-emulator"

            if "gnome-terminal" in terminal_bin:
                # gnome-terminal supports multiple tabs in one command
                cmd = [terminal_bin]
                for idx, (script_file, tab_title) in enumerate(workers_data):
                    if idx > 0:
                        cmd.append("--tab")
                    else:
                        cmd.append("--")
                    cmd.extend(["bash", str(script_file.absolute())])
                return [cmd]  # Return as list of one command
            else:
                # xterm/fallback: spawn separate terminals
                commands = []
                for script_file, tab_title in workers_data:
                    cmd = [terminal_bin, "-e", "bash", str(script_file.absolute())]
                    commands.append(cmd)
                return commands

    # ------------------------------------------------------------------
    # Manifest processing
    # ------------------------------------------------------------------

    def process_existing_manifests(self):
        """Scan pending_workers/ for manifests that existed before daemon started."""
        manifest = self.pending_dir / "manifest.json"
        if manifest.exists():
            print("Found existing manifest on startup, processing...")
            time.sleep(0.5)
            self.spawn_workers(manifest)

    def spawn_workers(self, manifest_path):
        """Read a manifest and spawn autonomous Claude workers in terminal tabs."""
        if not self._spawn_lock.acquire(blocking=False):
            print(f"  [SKIP] spawn_workers already running, ignoring duplicate call.")
            return
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except Exception as e:
            print(f"[ERROR] Reading manifest: {e}")
            self._spawn_lock.release()
            return

        initiative_id = manifest["initiative_id"]
        workers = manifest["workers"]

        # Deduplicate: never spawn the same initiative twice
        if initiative_id in self.active_workers:
            print(f"  [SKIP] Workers for {initiative_id} already active. Ignoring duplicate.")
            # Clean up the manifest so it doesn't keep triggering
            try:
                if manifest_path.exists():
                    manifest_path.unlink()
                for w in workers:
                    bf = self.pending_dir / w["file"]
                    if bf.exists():
                        bf.unlink()
            except Exception:
                pass
            self._spawn_lock.release()
            return

        # Immediately delete manifest to prevent any other code path from
        # finding it (watchdog, fallback scan, etc.)
        try:
            if manifest_path.exists():
                manifest_path.unlink()
        except Exception:
            pass

        print(f"\n>>> Spawning {len(workers)} worker(s) for {initiative_id}")

        # Workspace & logs
        workspace_dir = self.workspaces_dir / initiative_id
        logs_dir = workspace_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        self.active_workers[initiative_id] = {}

        # Collect worker data for terminal spawning
        workers_data = []

        for idx, worker in enumerate(workers):
            block_file = self.pending_dir / worker["file"]
            if not block_file.exists():
                print(f"  [WARN] Block file missing: {block_file}")
                continue

            # Copy block to workspace (persistent copy)
            workspace_block = workspace_dir / worker["file"]
            shutil.copy2(block_file, workspace_block)

            log_file = logs_dir / worker["file"].replace(".txt", ".log")
            model = worker.get("model", "sonnet")
            worker_type = worker.get("type", "worker").upper()
            tab_title = f"{initiative_id} {worker_type}"

            # Generate platform-specific launcher script
            script_ext = ".ps1" if IS_WINDOWS else ".sh"
            script_file = workspace_dir / worker["file"].replace(".txt", f"_run{script_ext}")

            # PID tracking for auto-close on completion
            pids_dir = workspace_dir / "pids"
            pids_dir.mkdir(parents=True, exist_ok=True)
            pid_file = pids_dir / f"{worker_type.lower()}.pid"

            # Generate script using helper method
            self._generate_worker_script(
                script_file=script_file,
                pid_file=pid_file,
                tab_title=tab_title,
                model=model,
                block_file=workspace_block,
                workspace_dir=workspace_dir
            )

            # Add to workers data for terminal spawning
            workers_data.append((script_file, tab_title))

            self.active_workers[initiative_id][worker["file"]] = {
                "log_file": log_file,
                "type": worker_type,
                "model": model,
            }

            print(f"  + {worker_type} ({model}): {worker['file']}")

        # Launch platform-specific terminal(s)
        try:
            terminal_commands = self._get_terminal_command(workers_data)

            # Execute terminal command(s)
            if IS_WINDOWS:
                # Single command with multiple tabs
                # CREATE_NEW_CONSOLE creates a visible console window (required for wt.exe to show)
                subprocess.Popen(terminal_commands, creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                # List of commands (one per tab on Mac, or single multi-tab command on Linux)
                for cmd in terminal_commands:
                    subprocess.Popen(cmd)

            print(f"  Terminal tabs opened.")
            print(f"  Logs -> {logs_dir}")

            # Clean up block files after terminals have had time to read them
            # (manifest already deleted immediately after reading)
            time.sleep(3)
            for worker in workers:
                bf = self.pending_dir / worker["file"]
                if bf.exists():
                    bf.unlink()
            print(f"  Pending files cleaned up.")

        except Exception as e:
            print(f"  [ERROR] Spawning workers: {e}")
        finally:
            self._spawn_lock.release()

    # ------------------------------------------------------------------
    # Completion monitoring
    # ------------------------------------------------------------------

    def _close_worker_tabs(self, initiative_id):
        """Kill worker processes for completed workers using stored PIDs.

        Uses SIGTERM on Unix for graceful termination.
        """
        pids_dir = self.workspaces_dir / initiative_id / "pids"
        if not pids_dir.exists():
            return

        closed_count = 0
        for pid_file in pids_dir.glob("*.pid"):
            try:
                pid = int(pid_file.read_text().strip())
                worker_type = pid_file.stem  # e.g., "worker", "helper"

                # Check if process is still running
                if not self._is_process_running(pid):
                    # Already dead, just clean up PID file
                    pid_file.unlink()
                    continue

                # Terminate the process
                if IS_WINDOWS:
                    subprocess.run(
                        ["taskkill", "/F", "/PID", str(pid)],
                        capture_output=True, timeout=5
                    )
                else:
                    os.kill(pid, signal.SIGTERM)  # Graceful termination

                print(f"    Auto-closed {initiative_id} {worker_type} (PID {pid})")
                pid_file.unlink()
                closed_count += 1
            except Exception:
                pass  # Process may have already exited

        return closed_count

    def check_worker_health(self):
        """Check if any tracked worker PIDs have died unexpectedly.

        For each active initiative:
        1. Check each worker PID still exists
        2. If dead AND initiative not done → respawn continuation worker
        3. If dead AND initiative done → clean up normally
        """
        if not self.active_workers:
            return

        try:
            with open(self.initiatives_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return

        initiatives = data.get("initiatives", []) if isinstance(data, dict) else data
        init_map = {init.get("id"): init for init in initiatives}

        for init_id, workers_info in list(self.active_workers.items()):
            init = init_map.get(init_id)
            if not init:
                continue

            workspace_dir = self.workspaces_dir / init_id
            pids_dir = workspace_dir / "pids"

            if not pids_dir.exists():
                continue

            # Check each worker's PID
            for pid_file in list(pids_dir.glob("*.pid")):
                try:
                    pid = int(pid_file.read_text().strip())
                    is_running = self._is_process_running(pid)

                    if not is_running:
                        # Worker died - check if initiative is complete
                        status = init.get("status")

                        if status != "done":
                            # RESPAWN: Initiative not complete, worker crashed
                            worker_type = pid_file.stem  # e.g., "worker", "checker"
                            print(f"\n!!! WORKER DEATH DETECTED: {init_id}/{worker_type} (PID {pid})")
                            print(f"    Initiative status: {status}")
                            print(f"    Respawning continuation worker...")
                            self._respawn_continuation_worker(init_id, worker_type, init)

                        # Clean up PID file regardless
                        try:
                            pid_file.unlink()
                        except Exception:
                            pass
                except (ValueError, OSError):
                    continue

    def _respawn_continuation_worker(self, init_id, worker_type, init):
        """Spawn a continuation worker to resume a dead worker's task.

        Creates a manifest with:
        - Same initiative_id
        - Same model
        - Marked as continuation/resume
        - Instructions to pick up where the previous worker left off
        """
        workspace_dir = self.workspaces_dir / init_id

        # Find the original block file
        original_block = None
        for block_file in workspace_dir.glob(f"*{worker_type}*.txt"):
            if "continuation" not in block_file.name:
                original_block = block_file
                break

        if not original_block:
            print(f"    [ERROR] Could not find original block file for {worker_type}")
            return

        # Read original instructions
        try:
            original_instructions = original_block.read_text(encoding="utf-8")
        except Exception:
            print(f"    [ERROR] Could not read original instructions")
            return

        # Get model from active_workers tracking or init
        model = "sonnet"  # Default
        for worker_info in self.active_workers.get(init_id, {}).values():
            model = worker_info.get("model", "sonnet")
            break

        # Create continuation instructions
        continuation_block_name = f"{init_id}_{worker_type}_continuation.txt"
        continuation_block = workspace_dir / continuation_block_name

        continuation_instructions = (
            "⚠️  CONTINUATION/RESUME MODE\n"
            "===========================\n"
            f"This worker was auto-spawned to resume after an unexpected crash.\n"
            f"Initiative: {init_id}\n"
            f"Worker Type: {worker_type.upper()}\n\n"
            "CRITICAL RESUME INSTRUCTIONS:\n"
            "1. Read .claude/initiatives.json and find your initiative's progress_log\n"
            "2. Review workspace files in .claude/workspaces/{init_id}/ to understand prior progress\n"
            "3. Check what was already completed — DO NOT duplicate work\n"
            "4. Continue from where the previous worker left off\n"
            "5. Update progress_log with 'resumed_after_crash: <description of what you're continuing>'\n\n"
            "ORIGINAL WORKER INSTRUCTIONS:\n"
            "==============================\n"
            f"{original_instructions}"
        )
        continuation_block.write_text(continuation_instructions, encoding="utf-8")

        # Create continuation manifest
        pending_manifest = {
            "initiative_id": init_id,
            "workers": [
                {
                    "file": continuation_block_name,
                    "type": worker_type,
                    "model": model,
                }
            ]
        }

        # Copy block file to pending directory
        pending_block = self.pending_dir / continuation_block_name
        shutil.copy2(continuation_block, pending_block)

        # Write manifest to pending (triggers daemon respawn)
        manifest_path = self.pending_dir / "manifest.json"
        manifest_path.write_text(json.dumps(pending_manifest, indent=2), encoding="utf-8")

        print(f"    ✓ Continuation worker spawned: {continuation_block_name}")
        print(f"    ✓ Manifest created: {manifest_path}")

    def check_worker_token_usage(self):
        """Poll session_output.json files and update initiatives.json with actual token usage."""
        if not self.initiatives_file.exists() or not self.active_workers:
            return

        try:
            with open(self.initiatives_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return  # File might be mid-write

        initiatives = data.get("initiatives", []) if isinstance(data, dict) else data
        updated = False

        for init in initiatives:
            init_id = init.get("id")
            if init_id not in self.active_workers:
                continue

            # Workspace for this initiative
            workspace_dir = self.workspaces_dir / init_id
            session_output_file = workspace_dir / "session_output.json"

            if not session_output_file.exists():
                continue

            try:
                try:
                    session_text = session_output_file.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    session_text = session_output_file.read_text(encoding="utf-16-le")
                if not session_text.strip():
                    continue

                # Find the last complete JSON object in the file
                # (may have text before the final result)
                import re
                json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
                matches = re.findall(json_pattern, session_text)
                if not matches:
                    continue

                last_json_str = matches[-1]
                session_data = json.loads(last_json_str)

                # Extract token usage from the structure
                usage = session_data.get("usage", {})
                input_tokens = usage.get("input_tokens", 0)
                output_tokens = usage.get("output_tokens", 0)
                cache_read_input = usage.get("cache_read_input_tokens", 0)
                cache_creation_input = usage.get("cache_creation_input_tokens", 0)

                total_tokens = input_tokens + output_tokens + cache_read_input + cache_creation_input

                # Update initiatives.json tokens_used for this initiative
                if total_tokens > 0:
                    init["tokens_used"] = total_tokens
                    updated = True

            except (json.JSONDecodeError, ValueError, FileNotFoundError, OSError):
                continue  # Skip on any parsing/file error

        # Write back if we updated anything
        if updated:
            try:
                with open(self.initiatives_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
            except Exception:
                pass  # Silently fail if file is locked

    def check_completion(self):
        """Poll initiatives.json for completed initiatives and budget overruns."""
        if not self.initiatives_file.exists() or not self.active_workers:
            return

        try:
            with open(self.initiatives_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return  # File might be mid-write

        initiatives = data.get("initiatives", []) if isinstance(data, dict) else data

        for init in initiatives:
            init_id = init.get("id")
            status = init.get("status")
            tokens_used = init.get("tokens_used", 0)
            token_budget = init.get("token_budget", 0)

            if init_id not in self.active_workers:
                continue

            # --- Budget exceeded alert ---
            budget_alert_key = f"{init_id}_budget_alerted"
            if (token_budget > 0 and tokens_used > token_budget
                    and not getattr(self, budget_alert_key, False)):
                setattr(self, budget_alert_key, True)
                pct = int(tokens_used / token_budget * 100)
                print(f"\n!!! BUDGET EXCEEDED: {init_id}")
                print(f"    Used: {tokens_used:,} / Budget: {token_budget:,} ({pct}%)")
                # Write alert file for orchestrator to detect
                alerts_dir = self.base_dir / "alerts"
                alerts_dir.mkdir(exist_ok=True)
                alert = {
                    "initiative_id": init_id,
                    "event": "budget_exceeded",
                    "tokens_used": tokens_used,
                    "token_budget": token_budget,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                }
                alert_file = alerts_dir / f"{init_id}_budget.json"
                alert_file.write_text(json.dumps(alert, indent=2))
                # Windows toast notification
                self._show_notification(
                    title="Worker Daemon - Budget Alert",
                    message=f"Initiative {init_id} exceeded budget!\\n"
                            f"Used: {tokens_used:,} / Budget: {token_budget:,} ({pct}%)",
                    notification_type="warning"
                )

            # --- Completion with grace period ---
            if status == "done":
                # First time seeing this completion? Start grace period
                if init_id not in self._completion_grace:
                    self._completion_grace[init_id] = time.time()
                    print(f"\n<<< Initiative {init_id} completed!")
                    print(f"    Starting 5-second grace period before auto-close...")
                    continue

                # Check if grace period has elapsed
                grace_elapsed = time.time() - self._completion_grace[init_id]
                if grace_elapsed < 5.0:
                    # Still in grace period, check again next cycle
                    continue

                # Grace period over, close worker tabs
                print(f"    Grace period elapsed, closing worker tabs...")
                closed_count = self._close_worker_tabs(init_id)

                # Clean up tracking
                del self.active_workers[init_id]
                del self._completion_grace[init_id]

                # Show notification
                if closed_count > 0:
                    print(f"    {closed_count} worker tab(s) closed.")
                self._show_notification(
                    title="Worker Daemon - Task Complete",
                    message=f"Initiative {init_id} completed!\\n"
                            f"Tokens used: {tokens_used:,}",
                    notification_type="info"
                )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def cleanup(self):
        """Remove PID file on shutdown."""
        try:
            if self.pid_file.exists():
                self.pid_file.unlink()
        except OSError:
            pass
        print("\nDaemon stopped.")

    def scan_for_manifest(self):
        """Fallback scan: check if manifest.json exists and process it.

        This catches cases where watchdog events were missed (atomic
        writes, rapid overwrites, etc.).  Called periodically from the
        main loop.
        """
        manifest = self.pending_dir / "manifest.json"
        if manifest.exists():
            print("\n[Fallback scan] Found unprocessed manifest, processing...")
            # Atomically claim the manifest before processing
            claimed_path = manifest.with_suffix(".json.processing")
            try:
                manifest.rename(claimed_path)
                self.spawn_workers(claimed_path)
            except FileNotFoundError:
                # Already processed by another code path
                pass
            except Exception as e:
                print(f"  [ERROR] Fallback scan claim failed: {e}")

    def run(self):
        """Main loop: watch for manifests, poll for completion."""
        # Process any manifest that already exists
        self.process_existing_manifests()

        # File watcher for new manifests
        handler = _ManifestHandler(self)
        observer = Observer()
        observer.schedule(handler, str(self.pending_dir), recursive=False)
        observer.start()

        print("Watching for new worker manifests...")
        print("Polling completion every 10s (with fallback manifest scan).")
        print("Press Ctrl+C to stop.\n")

        try:
            while True:
                self._check_source_change()  # Auto-reload on source change
                self.check_worker_health()   # Auto-resume dead workers
                self.check_worker_token_usage()  # Update token usage every 30s
                self.check_completion()
                self.scan_for_manifest()
                time.sleep(10)
        except KeyboardInterrupt:
            pass
        finally:
            observer.stop()
            observer.join()
            self.cleanup()


class _ManifestHandler(FileSystemEventHandler):
    """Watchdog handler that triggers worker spawning on manifest changes.

    Handles created, modified, and moved events to cover all ways a file
    can appear in the directory (direct write, atomic write via rename,
    overwrite of existing file, etc.).
    """

    def __init__(self, daemon):
        self.daemon = daemon
        self._lock = threading.Lock()
        self._processing = False

    def _handle_manifest(self, path):
        """Process a manifest file if it looks like manifest.json."""
        if not path.endswith("manifest.json"):
            return

        # Prevent concurrent processing (multiple events can fire for
        # the same write operation).
        if not self._lock.acquire(blocking=False):
            return
        try:
            if self._processing:
                return
            self._processing = True
        finally:
            self._lock.release()

        try:
            print(f"\nManifest detected! Waiting for block files...")
            manifest_path = Path(path)

            # BUG FIX: Atomically claim the manifest by renaming it BEFORE processing
            # This prevents duplicate processing from multiple filesystem events
            claimed_path = manifest_path.with_suffix(".json.processing")
            try:
                manifest_path.rename(claimed_path)
            except FileNotFoundError:
                # Another event already claimed it, abort
                print("  [SKIP] Manifest already claimed by another event.")
                self._processing = False
                return
            except Exception as e:
                print(f"  [ERROR] Failed to claim manifest: {e}")
                self._processing = False
                return

            # Wait for all block files to be ready
            for attempt in range(12):  # Up to 60 seconds
                time.sleep(5)
                try:
                    with open(claimed_path, "r", encoding="utf-8") as f:
                        manifest = json.load(f)
                    all_ready = all(
                        (claimed_path.parent / w["file"]).exists()
                        for w in manifest["workers"]
                    )
                    if all_ready:
                        break
                except Exception:
                    continue
            else:
                print("  [WARN] Timed out waiting for block files.")

            # Pass the claimed path to spawn_workers (it will delete it)
            self.daemon.spawn_workers(claimed_path)
        finally:
            self._processing = False

    def on_created(self, event):
        if not event.is_directory:
            self._handle_manifest(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self._handle_manifest(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self._handle_manifest(event.dest_path)


if __name__ == "__main__":
    daemon = WorkerDaemon()
    daemon.run()
