# Claude API CLI Skill

**Quick access to Claude Code API Service management via CLI.**

## When to Use This Skill

User wants to:
- Start/stop/check the API service
- Create or manage API keys
- Test API endpoints
- Check service health
- Verify dependencies (Redis, Claude CLI, agents, skills)

## Quick Commands

### Service Management
```bash
claude-api service start --background    # Start service
claude-api service stop                  # Stop service
claude-api service status                # Check status
```

### Health Checks
```bash
claude-api health ping                   # Quick check
claude-api health check                  # Full health check
claude-api health deps                   # Verify dependencies
```

### API Keys
```bash
# Create key (returns key + instructions)
claude-api keys create --project-id PROJECT --profile PROFILE

# List all keys
claude-api keys list

# View permissions
claude-api keys permissions KEY_PREFIX
```

**Profiles:** `free`, `pro`, `enterprise`

### Testing
```bash
# Test all endpoints (requires API key)
claude-api test all --key API_KEY

# Test specific endpoints
claude-api test completion --key API_KEY
claude-api test agents --key API_KEY
```

### Configuration
```bash
claude-api config-show                   # Show config
claude-api config-validate               # Verify dependencies
```

## Common Workflows

### User: "Is the service running?"
```bash
claude-api health ping
```

### User: "Start the service"
```bash
# Check dependencies first
claude-api health deps

# Start service
claude-api service start --background

# Verify it started
claude-api service status
```

### User: "I need an API key"
```bash
# Create enterprise key (full permissions)
claude-api keys create --project-id PROJECT_NAME --profile enterprise

# Returns:
# - API key
# - Permissions summary
# - .env snippet
```

### User: "Test if everything works"
```bash
# If they have a key
claude-api test all --key THEIR_KEY

# If they need a key first
claude-api keys create --project-id test --profile enterprise
# Then use returned key for testing
```

### User: "Why isn't it working?"
```bash
# Check service status
claude-api service status

# Check dependencies
claude-api health deps

# Full health check
claude-api health check

# Common issues:
# - Service not running → claude-api service start --background
# - Redis not running → brew services start redis (macOS)
# - Port in use → claude-api service stop, then start
```

## Output Handling

**Default:** Beautiful Rich tables (human-readable)

**JSON mode:** Add `--json` for parsing:
```bash
claude-api keys list --json
```

**Other formats:**
```bash
claude-api keys create --output env     # For .env files
claude-api keys create --output json    # For scripts
```

## Important Notes

**Service Location:**
- CLI auto-detects service directory
- Config: `~/.claude-api/config.yaml`
- PID file: `~/.claude-api/service.pid`

**Authentication:**
- Most endpoints require API key
- Test commands need `--key` option
- Keys never expire (manual revocation only)

**Placeholder Commands:**
- `usage`, `workers`, `tasks` - Need API enhancements
- These show what data they would display
- Clear messaging about required API work

## Error Messages

CLI provides helpful suggestions:
```
✗ Service is not running
  → Start with: claude-api service start
```

Follow the suggestions - they're accurate!

## For Detailed Reference

Read `command-reference.md` in this skill directory for:
- Complete command list
- All options and flags
- Troubleshooting guide
- Integration examples

## Script Usage

```python
# Execute CLI commands
result = subprocess.run(["claude-api", "health", "ping"], capture_output=True)

# Parse JSON output
result = subprocess.run(
    ["claude-api", "keys", "list", "--json"],
    capture_output=True,
    text=True
)
keys = json.loads(result.stdout)
```

## Summary

**Most common user needs:**
1. "Start the service" → `service start --background`
2. "Create API key" → `keys create --project-id X --profile enterprise`
3. "Is it working?" → `health check` or `test all --key KEY`
4. "Stop the service" → `service stop`

**Always check service status first if user reports issues.**

For comprehensive documentation: `cli/README.md` in project root.
