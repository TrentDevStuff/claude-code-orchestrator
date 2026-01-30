#!/bin/bash
# Monitor orchestrator progress

cd ~/claude-code-api-service

echo "========================================="
echo "  Claude Code API Service Build Status"
echo "  $(date)"
echo "========================================="
echo ""

# Check initiatives
echo "📊 Initiative Status:"
echo ""
python3 << 'PYTHON'
import json
with open('.claude/initiatives.json') as f:
    data = json.load(f)
    for init in data['initiatives']:
        status = init['status']
        tokens = init.get('tokens_used', 0)
        budget = init['token_budget']
        pct = int(tokens / budget * 100) if budget > 0 else 0

        emoji = {
            'done': '✅',
            'in_progress': '🔄',
            'review': '📝',
            'planned': '⏳',
            'failed_rolled_back': '❌'
        }.get(status, '❓')

        print(f"{emoji} {init['id']}: {init['title'][:40]:40s} [{status:12s}] {pct:3d}%")
PYTHON

echo ""
echo "---"
echo ""

# Check what's been built
echo "📁 Files Created:"
[ -f src/worker_pool.py ] && echo "  ✅ src/worker_pool.py ($(wc -l < src/worker_pool.py) lines)"
[ -f src/model_router.py ] && echo "  ✅ src/model_router.py ($(wc -l < src/model_router.py) lines)"
[ -f src/budget_manager.py ] && echo "  ✅ src/budget_manager.py ($(wc -l < src/budget_manager.py) lines)"
[ -f src/api.py ] && echo "  ✅ src/api.py ($(wc -l < src/api.py) lines)"
[ -f src/token_tracker.py ] && echo "  ✅ src/token_tracker.py ($(wc -l < src/token_tracker.py) lines)"
[ -f src/cache.py ] && echo "  ✅ src/cache.py ($(wc -l < src/cache.py) lines)"
[ -f src/websocket.py ] && echo "  ✅ src/websocket.py ($(wc -l < src/websocket.py) lines)"
[ -f src/auth.py ] && echo "  ✅ src/auth.py ($(wc -l < src/auth.py) lines)"
[ -f client/claude_client.py ] && echo "  ✅ client/claude_client.py ($(wc -l < client/claude_client.py) lines)"

echo ""
echo "---"
echo ""

# Check active workers
echo "🔧 Active Workers:"
WORKERS=$(ps aux | grep "claude.*-p" | grep -v grep | wc -l | tr -d ' ')
echo "  $WORKERS Claude processes running"

if [ "$WORKERS" -gt 0 ]; then
    ps aux | grep "claude.*-p" | grep -v grep | awk '{print "  - PID "$2": "$11" "$12}' | head -5
fi

echo ""
echo "---"
echo ""

# Check git branches
echo "🌿 Git Branches:"
git branch | grep feature | head -10

echo ""
echo "---"
echo ""

# Quick summary
MERGED=$(git log --oneline --all --grep="Merge INIT-" | wc -l | tr -d ' ')
echo "📈 Progress Summary:"
echo "  Merged features: $MERGED/10"
echo "  Active workers: $WORKERS"
echo ""
