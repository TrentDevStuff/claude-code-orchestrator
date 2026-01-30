# 🚀 Launch Instructions - Claude Code Orchestrator

## Overview

This project uses the **claude-code-orchestrator** to autonomously build all 10 features in parallel. You give it the wish list, go do something else, and come back to working code.

## Prerequisites

✅ Already complete:
- [x] Project directory created
- [x] Git repository initialized
- [x] FastAPI skeleton built
- [x] Test suite configured
- [x] Orchestrator integrated
- [x] Initial commit created

## Step 1: Install Dependencies

```bash
cd ~/claude-code-api-service

# Install Python dependencies for the orchestrator
pip install watchdog

# Verify Claude Code CLI is available
which claude
# Should output: /usr/local/bin/claude (or similar)
```

## Step 2: Launch the Orchestrator

### Option A: macOS (Recommended)

```bash
# Make scripts executable (if not already)
chmod +x Mac/*.command
chmod +x claude-orch.sh

# Double-click this file in Finder:
open Mac/START-HERE.command

# OR run from terminal:
./Mac/START-HERE.command
```

### Option B: Terminal (Alternative)

```bash
./claude-orch.sh
```

## Step 3: Select Model & Permissions

When the launcher starts, you'll see a menu:

```
SELECT MODEL:
  1) Haiku (fastest, cheapest - use for delegation)
  2) Sonnet (balanced - default planning)
  3) Opus (most capable - complex reasoning)

Choice (1-3, default=2):
```

**Recommended**: Press `2` (Sonnet) for the orchestrator itself

```
SELECT PERMISSIONS:
  1) Bypass all (full automation - CI/testing)
  2) Respect current (user's existing settings - default)

Choice (1-2, default=2):
```

**For overnight build**: Press `1` (Bypass all) - full automation
**For watching it work**: Press `2` (Respect current) - see approvals

## Step 4: Provide the Wish List

Once the orchestrator starts, you'll see:

```
========================================
  Claude Code Orchestrator
========================================
Ready to launch orchestrator session...
```

**Copy and paste the entire wish list** from `WISHLIST.md`:

```
Here's my wish list for building the Claude Code API Service.
Prioritize based on dependencies. Run tests after each feature.

[... paste the full wish list from WISHLIST.md ...]
```

## Step 5: Walk Away! 🎉

The orchestrator will:

1. **Analyze** the wish list and detect dependencies
2. **Create initiatives** (INIT-001 through INIT-010)
3. **Determine waves** based on what can run in parallel
4. **Spawn workers** in separate terminal tabs
5. **Build features** autonomously
6. **Run tests** after each feature
7. **Merge to main** when tests pass
8. **Rollback** when tests fail

**Expected timeline**: 6-9 hours (mostly unattended)

## Step 6: Monitor Progress (Optional)

### Check Status

In the orchestrator session:
```
You: status
```

Response will show:
```
INIT-001: Worker Pool Manager - MERGED (tests passed)
INIT-002: Model Auto-Router - IN PROGRESS (60% budget used)
INIT-003: Budget Manager - MERGED (tests passed)
...
```

### Watch Workers

You'll see terminal tabs spawn with names like:
- `INIT-001 MAIN` - Main worker for feature 1
- `INIT-002 HELPER` - Helper worker for feature 2

### View Logs

```bash
# Daemon log
cat .claude/.daemon.log

# Specific worker log
cat .claude/workspaces/INIT-001/logs/main.log

# Usage tracking
cat .claude/initiatives.json
```

## Step 7: Handle Failures (If Any)

If a feature fails (tests don't pass), the orchestrator will:
1. Retry the fix (up to 2 attempts)
2. Rollback the branch if still failing
3. Mark initiative as `failed_rolled_back`
4. Move on to next feature

**To fix manually**:
```bash
# Check what failed
cat .claude/workspaces/INIT-XXX/logs/main.log

# The branch is preserved for manual review
git checkout feature/INIT-XXX-description

# Fix the issue
# Run tests
pytest

# Merge manually when fixed
git checkout main
git merge feature/INIT-XXX-description --no-ff
```

## Step 8: Verify Completion

When all features are complete:

```bash
# Check git branches
git branch
# Should see: main + feature branches (merged or failed)

# Run full test suite
pytest

# Check what got built
ls -la src/
# Should see:
# - worker_pool.py
# - model_router.py
# - budget_manager.py
# - api.py
# - token_tracker.py
# - cache.py
# - websocket.py
# - auth.py

# Check client library
ls -la client/
# Should see: claude_client.py

# Check documentation
ls -la docs/
```

## Step 9: Test the API

```bash
# Start the server
python main.py

# In another terminal, test endpoints
curl http://localhost:8080/health

# Test chat completion
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "haiku",
    "messages": [{"role": "user", "content": "Hello!"}],
    "project_id": "test"
  }'
```

## Architecture Overview

```
Wave 1 (Parallel):
  INIT-001: Worker Pool Manager
  INIT-002: Model Auto-Router
  INIT-003: Budget Manager
  ↓ (all must complete before Wave 2)

Wave 2 (Parallel):
  INIT-004: REST API Endpoints (needs 1,2,3)
  INIT-005: Token Tracking (needs 3)
  INIT-006: Redis Integration
  ↓ (all must complete before Wave 3)

Wave 3 (Parallel):
  INIT-007: WebSocket Streaming (needs 4,5)
  INIT-008: Authentication (needs 4)
  INIT-009: Python Client (needs 4,7)
  INIT-010: Documentation
```

## Cost Estimate

**With orchestrator (model routing):**
- Wave 1: 3 Haiku workers + 1 Sonnet orchestrator ≈ $0.50
- Wave 2: 2 Haiku + 1 Sonnet workers ≈ $0.40
- Wave 3: 3 Haiku workers + 1 Sonnet worker ≈ $0.60
- **Total: ~$1.50**

**Manual (all Sonnet):**
- 10 features × 2000 tokens each ≈ 20K tokens
- Cost: 20K × $0.003/1K = $60
- **Savings: $58.50 (97% cheaper!)**

## Troubleshooting

### Workers not spawning
```bash
# Check daemon is running
ps aux | grep worker-daemon

# Restart daemon
pkill -f worker-daemon
./claude-orch.sh
```

### Tests failing
```bash
# Install test dependencies
pip install -r requirements.txt

# Run specific test
pytest tests/test_basic.py -v

# Check what's missing
pytest --collect-only
```

### Budget alerts
```bash
# Check initiatives.json for budget usage
cat .claude/initiatives.json | grep tokens_used

# Increase budget for specific initiative
# Edit .claude/initiatives.json, increase token_budget field
```

## What to Expect

**Successful run:**
- ✅ 8-10 features merged to main
- ✅ All tests passing
- ✅ API endpoints functional
- ✅ Client library working
- ✅ Documentation complete

**Typical outcome:**
- ✅ 7-9 features merged
- ⚠️ 1-2 features rolled back (need manual fixes)
- ✅ Main branch stable
- ✅ Most functionality working

**Time saved:**
- Manual development: 20+ hours over several days
- With orchestrator: 6-9 hours unattended
- **Your actual time: ~30 minutes** (setup + verification)

---

## Ready? Launch it!

```bash
cd ~/claude-code-api-service
./Mac/START-HERE.command

# Then paste the wish list from WISHLIST.md
# And go do something else! 🎉
```

The orchestrator will handle everything. Come back in 6-9 hours to a working API service!
