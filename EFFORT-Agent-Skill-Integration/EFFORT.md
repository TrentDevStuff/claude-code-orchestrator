---
type: effort
effort_id: EFFORT-Agent-Skill-Integration
project: claude-code-api-service
status: completed
priority: high
progress: 100%
created: 2026-01-30T17:00:00Z
last_updated: 2026-01-30T22:30:00Z
linked_goal: null
---

# EFFORT: Integrate Claude Code Agents & Skills into API

## Title

Integrate Claude Code Agents & Skills into API

## Overview

Enable the API service to discover and invoke agents/skills from `~/.claude/` directory, making the full Claude Code ecosystem available through the API. This transforms the service from a simple LLM wrapper into a comprehensive agentic platform.

## Scope

### Agent & Skill Discovery
- Scan `~/.claude/agents/` for available agents
- Scan `~/.claude/skills/` for available skills
- Parse agent YAML frontmatter for metadata
- Parse skill.json for skill metadata
- Build registry of available capabilities

### Enhanced Agentic Prompting
- Inject agent descriptions into agentic task prompts
- Inject skill descriptions into agentic task prompts
- Include invocation examples (Task/Skill tools)
- Provide context-aware capability recommendations
- Enable natural language routing to agents/skills

### Execution & Tracking
- Track agent invocations in execution logs
- Track skill invocations in execution logs
- Capture agent/skill performance metrics
- Log capability usage patterns

### Permission & Validation
- Update permission system to validate against discovered agents/skills
- Prevent unauthorized agent/skill access
- Enforce capability-based access control
- Validate agent/skill parameters

## Success Criteria

1. **Discovery:** API can list all available agents and skills from `~/.claude/`
2. **Agent Invocation:** Agentic tasks successfully invoke agents like `company-workflow-analyst`
3. **Skill Invocation:** Agentic tasks successfully invoke skills like `semantic-text-matcher`
4. **Logging:** Execution logs show detailed agent/skill invocations
5. **Permissions:** Permission validation works with discovered capabilities
6. **Documentation:** API docs include agent/skill registry and usage examples

## Related Efforts

- **EFFORT-Agentic-API-Architecture** - Architectural decision on agentic capabilities exposure

## Notes

This effort builds on the architectural decision in EFFORT-Agentic-API-Architecture, implementing the hybrid approach of exposing both simple completion API and full agentic capabilities. The integration with `~/.claude/` agents and skills is what differentiates this service from standard LLM APIs.

**Key Design Principles:**
- Agents/skills are discovered dynamically (no hardcoding)
- Metadata drives prompt enhancement
- Natural language routing reduces API complexity
- Permission system enforces security
- Usage tracking enables optimization

## Current Status

✅ **COMPLETED** (2026-01-30)

Successfully integrated full agent/skill discovery system into the API service:

### Implementation Highlights

- **Agent Discovery:** Implemented `src/agent_discovery.py` with caching and validation
  - Discovered 25 agents from `~/.claude/agents/`
  - Parses YAML frontmatter for metadata
  - Validates agent definitions and tool access

- **Skill Discovery:** Full skill registry from `~/.claude/skills/`
  - Discovered 17 skills with metadata
  - Parses `skill.json` for capability information
  - Supports namespaced skills (e.g., `ganf-workflow-generator:test-scenario-generator`)

- **Enhanced Agentic Executor:** Updated prompting system
  - Injects agent descriptions and invocation examples
  - Injects skill descriptions and invocation examples
  - Provides context-aware capability recommendations
  - Enables natural language routing to agents/skills

- **Capabilities Endpoint:** Added GET `/v1/capabilities`
  - Lists all discovered agents with metadata
  - Lists all discovered skills with metadata
  - Enables clients to query available capabilities

- **Testing:** All 11 tests passing
  - Unit tests for discovery system
  - Integration tests with real tasks
  - Successfully tested agent/skill invocation in agentic mode

### Key Deliverables

✅ Discovery system with caching and validation
✅ Enhanced agentic prompting with agent/skill metadata
✅ Capabilities API endpoint
✅ Execution tracking (logs show agent/skill invocations)
✅ Permission validation (validates against discovered capabilities)
✅ Documentation (API docs include registry and usage examples)

This was a mini-initiative that successfully transformed the service from a simple LLM wrapper into a comprehensive agentic platform with access to the full Claude Code ecosystem.
