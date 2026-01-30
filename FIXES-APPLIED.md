---
created: 2026-01-30T03:20:00Z
updated: 2026-01-30T03:20:00Z
type: technical-documentation
---

# Critical Fixes Applied to Claude Code Orchestrator

This fork of cyberkrunk69/claude-code-orchestrator includes critical fixes for robust operation across different environments.

## Original Repository

**Source**: https://github.com/cyberkrunk69/claude-code-orchestrator
**Fork**: https://github.com/TrentDevStuff/claude-code-orchestrator
**License**: MIT

## Fixes Applied

### FIX #1: Working Directory Not Set

**File**: `.claude/worker-daemon.py` (lines 256-257)
**Commit**: b91d91b

**Problem:**
```bash
# Generated worker script was missing cd command
#!/bin/bash
echo $$ > /path/to/pids/main.pid
prompt=$(cat '/path/to/prompt.txt')
claude -p "$prompt" ...
# Worker starts in RANDOM directory (wherever terminal was)
# Tries to read .claude/MASTER_WORKER_SYSTEM.md → FILE NOT FOUND
```

**Solution:**
```bash
#!/bin/bash
cd '/Users/trent/claude-code-api-service'  # ← ADDED THIS
echo $$ > /path/to/pids/main.pid
prompt=$(cat '/path/to/prompt.txt')
claude -p "$prompt" ...
# Worker always starts in project root
# Can reliably find .claude/ system files
```

**Code Change:**
```python
# Before
script_content = (
    f"#!/bin/bash\n"
    f"echo $$ > {pid_file_abs}\n"
    # ...
)

# After
project_dir_abs = self.project_dir.absolute()
script_content = (
    f"#!/bin/bash\n"
    f"cd '{project_dir_abs}'\n"  # ← ADDED THIS LINE
    f"echo $$ > {pid_file_abs}\n"
    # ...
)
```

**Impact:**
- Workers can now find `.claude/MASTER_WORKER_SYSTEM.md`
- Workers can read `initiatives.json` correctly
- Workers start in consistent directory
- Applies to both macOS (bash) and Windows (PowerShell)

---

### FIX #2: Claude CLI Path Not Found

**File**: `.claude/worker-daemon.py` (lines 48, 247-275)
**Commit**: 32cb617

**Problem:**
```bash
# Worker script hardcoded 'claude' command
claude -p "$prompt" --model sonnet ...

# Daemon-spawned shells don't inherit user PATH
# If claude is in nvm/pyenv/custom path → NOT FOUND
# Error: claude: command not found
```

**Solution:**
```python
# Daemon detects full path at startup
class WorkerDaemon:
    def __init__(self):
        # ... other init ...

        # Detect claude CLI full path
        self.claude_path = shutil.which("claude") or "claude"
        # Returns: /Users/trent/.nvm/versions/node/v22.15.0/bin/claude

# Use full path in generated scripts
script_content += (
    f"{self.claude_path} -p \"$prompt\" --model {model} ..."
)
```

**Code Changes:**
```python
# 1. Add to __init__
self.claude_path = shutil.which("claude") or "claude"

# 2. Replace all 4 occurrences of 'claude' command:
# PowerShell with output
f"{self.claude_path} -p \"$prompt\" ..."  # (was: f"claude -p ...")

# PowerShell without output
f"{self.claude_path} -p \"$prompt\" ..."  # (was: f"claude -p ...")

# Bash with output
f"{self.claude_path} -p \"$prompt\" ..."  # (was: f"claude -p ...")

# Bash without output
f"{self.claude_path} -p \"$prompt\" ..."  # (was: f"claude -p ...")
```

**Impact:**
- Works with nvm-installed Claude Code
- Works with pyenv, rbenv, or any custom PATH
- Works across different developer environments
- No manual PATH configuration required
- Portable across macOS/Linux/Windows

---

## Combined Impact

**Before fixes:**
- ❌ Workers spawned but couldn't find system files
- ❌ Workers couldn't execute claude command
- ❌ Projects failed with "files don't exist" errors
- ❌ Only worked if claude in standard PATH AND terminal started in project dir

**After fixes:**
- ✅ Workers always find system files (correct working directory)
- ✅ Workers always find claude command (auto-detected path)
- ✅ Works in any environment (nvm, pyenv, rbenv, custom PATH)
- ✅ Robust operation across different setups
- ✅ **Orchestrator actually works!**

## Testing

```bash
# Test the fixes work
cd ~/claude-code-api-service
./Mac/START-HERE.command

# Paste wish list
# Workers should spawn successfully now
```

## Contributing Back Upstream

These fixes could benefit the original project. Consider submitting a PR to:
https://github.com/cyberkrunk69/claude-code-orchestrator

## For Future Projects

When using this orchestrator on OTHER projects:

1. **Copy the FIXED version**:
   ```bash
   cp -r ~/claude-code-api-service/.claude ~/your-new-project/
   cp ~/claude-code-api-service/claude-orch.sh ~/your-new-project/
   cp -r ~/claude-code-api-service/Mac ~/your-new-project/
   ```

2. **Or clone your fork**:
   ```bash
   cd ~/your-new-project
   git clone https://github.com/TrentDevStuff/claude-code-orchestrator.git
   cp claude-code-orchestrator/.claude ./
   cp claude-code-orchestrator/*.sh ./
   cp -r claude-code-orchestrator/Mac ./
   ```

Both fixes are now permanently in your fork for reuse!

## Version Info

- **Original**: cyberkrunk69/claude-code-orchestrator @ commit unknown
- **This fork**: TrentDevStuff/claude-code-orchestrator @ commit 32cb617
- **Fixes applied**: 2026-01-30
- **Tested on**: macOS Darwin 24.1.0, Claude Code CLI via nvm
