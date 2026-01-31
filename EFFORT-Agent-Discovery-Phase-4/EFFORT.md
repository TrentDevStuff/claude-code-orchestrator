---
created: 2026-01-31T11:45:00Z
updated: 2026-01-31T11:45:00Z
status: not_started
priority: low
effort_id: EFFORT-Agent-Discovery-Phase-4
project: claude-code-api-service
goal: Add agent/skill registry and management
type: effort
dependencies: ["EFFORT-Agent-Discovery-Phase-1"]
---

# EFFORT: Agent/Skill Registry & Management (Phase 4)

## Overview

Create a registry system for managing which agents/skills are available through the API service, with enable/disable controls, tagging, cost limits, and service-specific agents.

## Problem Statement

**Current State:**
- All agents in `~/.claude/agents/` are automatically available
- No control over which agents can be used via API
- No service-specific agents
- No organization/tagging system
- No cost controls per agent

**User Need:**
- "Disable expensive agents for production"
- "Only allow certain agents for project X"
- "Create custom agents specifically for API service"
- "Organize agents by category/capability"
- "Set cost limits per agent"

## Goals

1. **Registry System** - Central registry for agent/skill configuration
2. **Enable/Disable** - Control which agents are available via API
3. **Tagging** - Organize agents by capability/category
4. **Cost Limits** - Set max cost per agent invocation
5. **Service-Specific Agents** - Agents designed for API service use
6. **Project Whitelisting** - Restrict agents to specific projects

## Success Criteria

- ✅ Registry file manages agent availability
- ✅ CLI commands for enable/disable
- ✅ Tag-based organization and filtering
- ✅ Cost limits enforced
- ✅ Service-specific agent directory
- ✅ Project-level access control

## Scope

### In Scope
- Registry file format (JSON/YAML)
- CLI management commands
- Enable/disable functionality
- Tagging system
- Cost limits per agent
- Service-specific agent directory
- Project whitelisting

### Out of Scope
- Web UI for management
- Role-based access control (RBAC)
- Agent versioning
- Agent marketplace

## Registry File Format

```json
{
  "version": "1.0",
  "agents": {
    "company-workflow-analyst": {
      "enabled": true,
      "tags": ["workflow", "analysis", "enterprise"],
      "max_cost_per_invocation": 2.00,
      "allowed_projects": ["*"],  // * = all projects
      "description_override": null,
      "notes": "Primary workflow extraction agent"
    },
    "expensive-opus-agent": {
      "enabled": false,
      "tags": ["analysis", "expensive"],
      "max_cost_per_invocation": 10.00,
      "allowed_projects": ["premium-project"],
      "notes": "Disabled for cost reasons"
    }
  },
  "skills": {
    "semantic-text-matcher": {
      "enabled": true,
      "tags": ["matching", "nlp"],
      "allowed_projects": ["*"]
    }
  },
  "settings": {
    "service_agents_dir": ".claude/agents/api-service",
    "auto_discover": true,
    "default_enabled": true
  }
}
```

**Location:** `.claude/registry.json`

## Service-Specific Agents

**Directory:** `.claude/agents/api-service/`

**Example Agents:**
- `api-optimizer.md` - Optimizes API usage patterns
- `api-troubleshooter.md` - Diagnoses API issues
- `batch-processor.md` - Handles batch API requests efficiently
- `cost-analyzer.md` - Analyzes and reduces API costs

## Commands to Add

```bash
# Registry management
claude-api agents enable AGENT_NAME
claude-api agents disable AGENT_NAME
claude-api agents set-limit AGENT_NAME --max-cost 2.00

# Tagging
claude-api agents tag AGENT_NAME TAG1,TAG2
claude-api agents list --tag workflow

# Project restrictions
claude-api agents allow AGENT_NAME --project-id my-app
claude-api agents deny AGENT_NAME --project-id test-app

# Service-specific agents
claude-api agents create api-optimizer \
  --template service-agent \
  --description "Optimizes API usage"

# Registry operations
claude-api registry show
claude-api registry validate
claude-api registry export --output registry-backup.json
```

## Technical Approach

**Registry Manager:**
```python
class AgentRegistry:
    def __init__(self, registry_path: str = ".claude/registry.json"):
        self.registry = self.load_registry()

    def is_enabled(self, agent: str) -> bool:
        """Check if agent is enabled"""

    def get_max_cost(self, agent: str) -> Optional[float]:
        """Get cost limit for agent"""

    def is_allowed_for_project(self, agent: str, project_id: str) -> bool:
        """Check project access"""

    def enable(self, agent: str):
        """Enable agent"""

    def disable(self, agent: str):
        """Disable agent"""

    def set_cost_limit(self, agent: str, max_cost: float):
        """Set cost limit"""
```

**Integration:**
- `src/agentic_executor.py` - Check registry before allowing agent
- `src/agent_discovery.py` - Filter based on registry
- Cost enforcement in task execution

## Timeline

**Estimated Duration:** 2-3 hours

**Breakdown:**
- Registry file format & manager: 1 hour
- CLI commands: 1 hour
- Integration with executor: 30 minutes
- Testing & documentation: 30 minutes

## Dependencies

**Requires:**
- Phase 1 (Discovery) - foundation

**Optional:**
- Phase 2 (Analytics) - cost data for limits

## Example Usage

```bash
# View registry
$ claude-api registry show
Registry: .claude/registry.json
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Agents:   25 total (23 enabled, 2 disabled)
Skills:   17 total (17 enabled)

Disabled Agents:
  • expensive-opus-agent (cost limit exceeded)
  • deprecated-agent

# Disable expensive agent
$ claude-api agents disable expensive-opus-agent
✓ Agent disabled: expensive-opus-agent

# Set cost limit
$ claude-api agents set-limit company-workflow-analyst --max-cost 2.00
✓ Max cost set: $2.00 per invocation

# Tag agent
$ claude-api agents tag company-workflow-analyst workflow,enterprise
✓ Tags updated: workflow, enterprise

# List by tag
$ claude-api agents list --tag workflow
Workflow Agents (5):
  • company-workflow-analyst
  • workflow-sync-agent
  • workflow-direct-modifier
  • workflow-structure-agent
  • ganf-workflow-generator

# Create service-specific agent
$ claude-api agents create api-cost-analyzer \
  --template service-agent \
  --model haiku \
  --description "Analyzes API usage and suggests optimizations"
✓ Agent created: .claude/agents/api-service/api-cost-analyzer.md
```

## Future Enhancements

- Agent versioning (v1, v2, etc.)
- Agent deprecation warnings
- Agent templates/scaffolding
- Web UI for registry management
- Import/export registry configurations
- Shared registry across services
