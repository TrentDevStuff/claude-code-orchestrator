#!/bin/bash
# Claude Code Orchestrator - Unified Menu Launcher
# Select model, permissions, and launch orchestrator session

cd "$(dirname "$0")" || exit 1
clear

# ── Debug log setup ──────────────────────────────────────────
DEBUG_LOG=".claude/orch-launch-debug.log"
: > "$DEBUG_LOG"  # truncate on each run
log() { echo "[$(date '+%H:%M:%S')] $*" >> "$DEBUG_LOG"; }
log "=== Orchestrator launch started ==="
log "Platform: $(uname -s) $(uname -m)"
log "Shell: $SHELL"
log "PWD: $(pwd)"
log "Python3 path: $(which python3 2>/dev/null || echo 'NOT FOUND')"
log "Python path: $(which python 2>/dev/null || echo 'NOT FOUND')"
log "Claude path: $(which claude 2>/dev/null || echo 'NOT FOUND')"

echo "============================================"
echo "  Claude Code Orchestrator"
echo "============================================"
echo ""
echo "(Debug log: $DEBUG_LOG)"
echo ""

# Pre-flight checks
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    log "FAIL: Python not found"
    echo "ERROR: Python not found in PATH."
    read -p "Press enter to exit..."
    exit 1
fi

PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi
log "Using Python: $PYTHON_CMD ($($PYTHON_CMD --version 2>&1))"

if ! command -v claude &> /dev/null; then
    log "FAIL: Claude Code not found"
    echo "ERROR: Claude Code not found in PATH."
    echo "Install: https://docs.anthropic.com/en/docs/claude-code"
    read -p "Press enter to exit..."
    exit 1
fi
log "Claude version: $(claude --version 2>&1 || echo 'unknown')"

# Install watchdog if needed
if ! $PYTHON_CMD -c "import watchdog" 2>/dev/null; then
    echo "Installing watchdog dependency..."
    log "Installing watchdog..."
    $PYTHON_CMD -m pip install watchdog --quiet
    log "Watchdog install exit code: $?"
else
    log "Watchdog: already installed"
fi

# Model selection menu
echo ""
echo "SELECT MODEL:"
echo "  1) Haiku (fastest, cheapest - use for delegation)"
echo "  2) Sonnet (balanced - default planning)"
echo "  3) Opus (most capable - complex reasoning)"
echo ""
read -p "Choice (1-3, default=2): " MODEL_CHOICE
MODEL_CHOICE=${MODEL_CHOICE:-2}

case "$MODEL_CHOICE" in
    1) MODEL="haiku" ;;
    2) MODEL="sonnet" ;;
    3) MODEL="opus" ;;
    *)
        echo "Invalid choice. Defaulting to sonnet."
        MODEL="sonnet"
        ;;
esac

echo "Selected: $MODEL"
log "Model: $MODEL"

# Permissions selection menu
echo ""
echo "SELECT PERMISSIONS:"
echo "  1) Bypass all (full automation - CI/testing)"
echo "  2) Respect current (user's existing settings - default)"
echo ""
read -p "Choice (1-2, default=2): " PERMS_CHOICE
PERMS_CHOICE=${PERMS_CHOICE:-2}

if [ "$PERMS_CHOICE" == "1" ]; then
    PERMS_FLAG="--dangerously-skip-permissions"
    PERMS_MODE="BYPASS (session-only, no config changes)"
else
    PERMS_FLAG=""
    PERMS_MODE="RESPECT (uses your current permissions)"
fi
log "Permissions: $PERMS_MODE"

# Create workspace
mkdir -p ".claude/workspaces" ".claude/pending_workers"
log "Workspace dirs created"

# ── Daemon cleanup ───────────────────────────────────────────
echo ""
echo "Cleaning up stale daemon processes..."

# Kill daemon by explicit PID from previous run (most reliable)
if [ -f ".claude/.daemon-pid" ]; then
    OLD_PID=$(cat ".claude/.daemon-pid" 2>/dev/null)
    log "Found stale .daemon-pid: $OLD_PID"
    kill -9 "$OLD_PID" 2>/dev/null && log "Killed PID $OLD_PID" || log "PID $OLD_PID already dead"
else
    log "No stale .daemon-pid file"
fi

# Find and kill any remaining worker-daemon.py processes
STALE_PIDS=$(pgrep -f "worker-daemon.py" 2>/dev/null)
if [ -n "$STALE_PIDS" ]; then
    log "Found stale daemon PIDs via pgrep: $STALE_PIDS"
    echo "$STALE_PIDS" | while read pid; do
        kill -9 "$pid" 2>/dev/null && log "Killed stale PID $pid" || log "Failed to kill $pid"
    done
else
    log "No stale daemon processes found via pgrep"
fi

# Clean up stale PID file and logs
rm -f ".claude/.daemon-pid" 2>/dev/null
rm -f ".claude/.daemon.log" 2>/dev/null
log "Cleaned up stale files"

# Brief pause to ensure processes are terminated
sleep 1
log "Post-cleanup pause done"

# ── Start daemon ─────────────────────────────────────────────
echo ""
echo "Starting fresh daemon..."

$PYTHON_CMD .claude/worker-daemon.py > ".claude/.daemon.log" 2>&1 &
DAEMON_PID=$!
log "Daemon launched with PID: $DAEMON_PID"
sleep 2

# Verify daemon is actually running
if kill -0 "$DAEMON_PID" 2>/dev/null; then
    log "Daemon is running (PID $DAEMON_PID confirmed alive)"
else
    log "WARNING: Daemon PID $DAEMON_PID is NOT running!"
    log "Daemon log contents:"
    log "$(cat .claude/.daemon.log 2>/dev/null || echo '(empty or missing)')"
    echo "WARNING: Daemon may have failed to start. Check $DEBUG_LOG"
fi

echo ""
echo "============================================"
echo "Ready to launch orchestrator"
echo "Model: $MODEL"
echo "Permissions: $PERMS_MODE"
echo "============================================"
echo ""

# ── Launch orchestrator ──────────────────────────────────────
echo ""
echo "Launching orchestrator session with system prompt..."

PROMPT_FILE=".claude/master-prompt.md"
if [ ! -f "$PROMPT_FILE" ]; then
    log "FAIL: $PROMPT_FILE not found!"
    echo "ERROR: $PROMPT_FILE not found!"
    read -p "Press enter to exit..."
    exit 1
fi
PROMPT_SIZE=$(wc -c < "$PROMPT_FILE" | tr -d ' ')
log "System prompt file: $PROMPT_FILE ($PROMPT_SIZE bytes)"

log "Launching: claude --system-prompt <${PROMPT_SIZE}b> --model $MODEL $PERMS_FLAG"

if [ -z "$PERMS_FLAG" ]; then
    claude --system-prompt "$(cat "$PROMPT_FILE")" --model "$MODEL"
else
    claude --system-prompt "$(cat "$PROMPT_FILE")" $PERMS_FLAG --model "$MODEL"
fi

CLAUDE_EXIT=$?
log "Claude session exited with code: $CLAUDE_EXIT"

echo ""
echo "Orchestrator session ended."
log "=== Orchestrator launch finished ==="
read -p "Press enter to exit..."
