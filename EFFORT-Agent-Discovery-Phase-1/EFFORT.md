---
created: 2026-01-31T11:45:00Z
updated: 2026-01-31T11:45:00Z
status: planning
priority: medium
effort_id: EFFORT-Agent-Discovery-Phase-1
project: claude-code-api-service
goal: Add CLI commands for agent/skill discovery
type: effort
dependencies: []
---

# EFFORT: Agent/Skill Discovery CLI (Phase 1)

## Overview

Add CLI commands to discover, search, and inspect agents and skills available through the Claude Code API Service. Uses existing `agent_discovery.py` infrastructure - no API changes required.

## Problem Statement

**Current State:**
- Service discovers 25 agents and 17 skills from `~/.claude/`
- Users can query via API: `GET /v1/capabilities`
- No CLI commands to explore what's available
- Users don't know which agents/skills exist or what they do

**User Pain:**
- "What agents can I use?"
- "Which agent handles workflow analysis?"
- "What does the company-workflow-analyst agent do?"
- "Show me all skills related to PDFs"

## Goals

1. **Agent Discovery** - List, search, and inspect agents via CLI
2. **Skill Discovery** - List, search, and inspect skills via CLI
3. **Beautiful Output** - Rich formatted tables with useful info
4. **Filtering** - Filter by model, tags, tools
5. **Search** - Keyword search in names and descriptions

## Success Criteria

- ✅ `claude-api agents list` shows all agents with key details
- ✅ `claude-api agents info AGENT` shows comprehensive agent details
- ✅ `claude-api agents search KEYWORD` finds relevant agents
- ✅ Same commands for skills
- ✅ Filtering options (--model, --tags, --tools)
- ✅ Beautiful Rich table formatting
- ✅ Help text for all commands

## Scope

### In Scope
- CLI commands for agent/skill discovery
- Filtering and search functionality
- Integration with existing agent_discovery.py
- Documentation updates (CLI README, skill)

### Out of Scope
- Usage analytics (Phase 2)
- Recommendations (Phase 3)
- Registry management (Phase 4)
- Agent testing (Phase 5)
- API endpoint changes (uses existing `/v1/capabilities`)

## Commands to Add

```bash
# Agents
claude-api agents list [--model MODEL] [--tools TOOL] [--json]
claude-api agents info AGENT_NAME
claude-api agents search QUERY

# Skills
claude-api skills list [--tags TAG] [--json]
claude-api skills info SKILL_NAME
claude-api skills search QUERY
```

## Technical Approach

**Reuse Existing:**
- `src/agent_discovery.py` - Already discovers agents/skills
- `src/api_client.py` - Already has `get_capabilities()` method
- CLI framework (Typer + Rich) - Already set up

**New Files:**
- `cli/commands/agents.py` - Agent discovery commands
- `cli/commands/skills.py` - Skill discovery commands (or combine in agents.py)

**No API Changes:**
- Uses existing `GET /v1/capabilities` endpoint
- All processing happens CLI-side

## Implementation Tasks

1. Create `cli/commands/agents.py` with:
   - `list` command with filtering
   - `info` command for details
   - `search` command with keyword matching

2. Create `cli/commands/skills.py` (or add to agents.py)
   - Same structure as agents

3. Register commands in main CLI

4. Update CLI README with new commands

5. Update claude-api-cli skill with discovery commands

6. Test all commands

## Timeline

**Estimated Duration:** 2-3 hours

**Breakdown:**
- Commands implementation: 1.5 hours
- Testing: 30 minutes
- Documentation: 30 minutes

## Dependencies

**Requires:**
- Existing CLI framework (✅ complete)
- agent_discovery.py (✅ exists)
- API running with /v1/capabilities (✅ exists)

**Blocks:**
- Phase 2 (Analytics) - needs discovery commands as foundation
- Phase 3 (Recommendations) - needs discovery infrastructure

## Success Metrics

**Usability:**
- User can find agents by name in < 5 seconds
- User can discover agent capabilities without reading code
- Search finds relevant agents with keyword matching

**Technical:**
- Commands execute in < 2s
- Output is readable and informative
- Filtering works correctly

## Example Usage

```bash
# List all agents
$ claude-api agents list
                          Available Agents (25)
┌──────────────────────────────┬─────────┬────────────────────────────────┐
│ Name                         │ Model   │ Description                    │
├──────────────────────────────┼─────────┼────────────────────────────────┤
│ company-workflow-analyst     │ sonnet  │ Extract workflows from source  │
│ workflow-sync-agent          │ sonnet  │ Integrate cross-company flows  │
│ accessibility-auditor        │ opus    │ WCAG 2.1 compliance audits     │
│ ...                          │ ...     │ ...                            │
└──────────────────────────────┴─────────┴────────────────────────────────┘

# Filter by model
$ claude-api agents list --model haiku
Shows only Haiku agents

# Get agent details
$ claude-api agents info company-workflow-analyst
                  company-workflow-analyst
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Model:        sonnet
Description:  DUAL-MODE WORKFLOW ANALYST - Extracts workflow
              data from meeting transcripts...

Tools:        Read, Write, Edit, MultiEdit, Bash, Grep, Glob,
              Documentation

How to Use:   Task(
                subagent_type="company-workflow-analyst",
                prompt="Extract workflow from transcript",
                description="Extract workflow"
              )

# Search for workflow-related agents
$ claude-api agents search workflow
Found 5 agents:
  • company-workflow-analyst
  • workflow-sync-agent
  • workflow-direct-modifier
  • workflow-structure-agent
  • ganf-workflow-generator

# List skills
$ claude-api skills list
Shows all 17 skills with descriptions
```

## Documentation Updates

**CLI README:**
- Add agents/skills discovery section
- Document filtering options
- Show examples

**claude-api-cli Skill:**
- Update SKILL.md with discovery commands
- Add to common workflows

## Future Enhancements (Later Phases)

- Phase 2: Usage statistics per agent
- Phase 3: Smart recommendations
- Phase 4: Registry management
- Phase 5: Agent testing via API

## Notes

This is the foundation for agent/skill management. Keep it simple and focused on discovery. Analytics, recommendations, and management come in later phases.

**Key principle:** Use existing infrastructure, add value through better UX.
