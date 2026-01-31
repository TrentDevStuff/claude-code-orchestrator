# Claude API CLI Skill

**For humans:** This skill teaches Claude Code how to use the `claude-api` CLI tool.

## What This Skill Does

Provides Claude Code with knowledge about the CLI tool for managing the Claude Code API Service, including:

- Service lifecycle management (start/stop/restart/status)
- Health checks and dependency verification
- API key creation and management
- Endpoint testing
- Configuration validation

## How It Works

1. **Skill Discovery:** Claude sees the description and knows when this skill applies
2. **SKILL.md:** Quick reference for common commands and workflows
3. **command-reference.md:** Detailed documentation (loaded on-demand)
4. **Rule:** `~/.claude/rules/claude-api-cli.md` provides quick access patterns

## Files

- `skill.json` - Metadata and description for discovery
- `SKILL.md` - Navigation hub and quick reference (< 500 lines)
- `command-reference.md` - Complete command documentation (on-demand)
- `README.md` - This file (for humans, not loaded by Claude)

## Usage Pattern

When user says: "Create an API key"

Claude will:
1. Recognize this matches the skill description
2. (Optional) Read SKILL.md if needed for syntax
3. Execute: `claude-api keys create --project-id PROJECT --profile enterprise`
4. Report the generated key to the user

## Design Philosophy

Following best practices from `~/.claude/skills/system-guide/agent-skill-best-practices.md`:

- **Concise:** SKILL.md is navigation hub, not exhaustive reference
- **Progressive disclosure:** Detailed reference in separate file
- **Description-driven:** Rich description for accurate discovery
- **Direct execution:** Claude executes CLI commands directly (no wrappers)

## Token Budget

- SKILL.md: ~400 lines (~3k tokens)
- Description: 250 chars
- Command reference: 800 lines (on-demand only)

Total impact when invoked: ~3k tokens (SKILL.md only loaded when needed)

## Testing

After creating this skill, test with:

```bash
# Ask Claude:
"Is the API service running?"
"Create me an API key for project 'test'"
"Test all the endpoints"
```

Claude should use the CLI directly without needing to ask how.
