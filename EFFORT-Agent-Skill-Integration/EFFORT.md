---
type: effort
effort_id: EFFORT-Agent-Skill-Integration
project: claude-code-api-service
status: not_started
priority: high
progress: 0%
created: 2026-01-30T17:00:00Z
last_updated: 2026-01-30T17:00:00Z
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

Not started. Waiting for completion of EFFORT-Agentic-API-Architecture planning phase.
