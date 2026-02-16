---
type: effort
effort_id: EFFORT-MCP-Tool-Routing
project: PROJECT-Claude-Code-API-Service
status: planning
priority: high
progress: 0%
created: 2026-02-16T12:00:00Z
last_updated: 2026-02-16T12:00:00Z
linked_goal: null
---

# EFFORT: MCP Tool Routing

## Overview

Enable agents running through claude-code-api-service to invoke MCP tools (especially advancedmd-mcp on port 8080). This is the critical path for the Feb 24 scheduling demo -- the scheduler agent needs to call MCP tools like `findAppointmentOpenings` and `bookAppointment` through the API service.

## Problem

Currently, claude-code-api-service spawns `claude -p` as a subprocess. The Claude CLI process needs MCP server configuration to access MCP tools. Without it, agents can't reach advancedmd-mcp or any other MCP server.

## Scope

### In Scope

1. **MCP configuration passthrough** -- Ensure spawned Claude CLI processes have access to MCP server config
2. **MCP tool invocation validation** -- Verify agents can actually call MCP tools and get real data back
3. **Permission integration** -- MCP tool access controlled by permission profiles
4. **End-to-end test** -- Agent submits via API -> calls MCP tool -> returns real data

### Out of Scope

- Building new MCP servers
- MCP tool development
- Modifying advancedmd-mcp itself

## Plan

See [[PLAN-2026-02-16-mcp-tool-routing]] for detailed implementation plan.

## Success Criteria

- [ ] Agent submitted via `/v1/task` can call advancedmd-mcp tools
- [ ] Real data returned from MCP tool invocation (not simulation)
- [ ] Permission profiles can allow/deny MCP tool access
- [ ] End-to-end: API request -> agent -> MCP tool -> real scheduling data

## Related

- Tasks: T-2026-02-03-010, T-2026-02-03-012
- Service: advancedmd-mcp (port 8080, 122 tools)
- Demo: Feb 24 scheduling demo for Tim C.
