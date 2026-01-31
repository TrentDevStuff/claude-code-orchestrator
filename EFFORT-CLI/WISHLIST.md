---
created: 2026-01-31T10:17:13Z
type: wishlist
effort: EFFORT-CLI
project: claude-code-api-service
plan: PLAN-CLI-2026-01-31-031714.md
orchestration_mode: manual
---

# CLI Build Wish List

**Reference Plan:** [PLAN-CLI-2026-01-31-031714.md](./PLAN-CLI-2026-01-31-031714.md)

**Build Mode:** Manual orchestration (Claude Code manages directly, no autonomous spawning)

---

## Features to Build (Prioritized by Dependencies)

### Wave 1: Foundation (Can Run in Parallel)

**INIT-001: CLI Framework & Configuration**
- Priority: CRITICAL (blocks everything else)
- Files: `cli/claude_api.py`, `cli/__init__.py`, `cli/utils.py`, `cli/config.py`, `setup.py`
- Dependencies: None
- Description: Set up Typer CLI framework, Rich formatting, config auto-detection
- Acceptance: `claude-api --help` works, config loads correctly
- Estimated Tokens: ~3k

**INIT-002: API Client Wrapper**
- Priority: CRITICAL (blocks all API-calling commands)
- Files: `cli/api_client.py`
- Dependencies: None
- Description: Shared HTTP client for all API calls with error handling
- Acceptance: Can make GET/POST requests to service, handles errors gracefully
- Estimated Tokens: ~2k

---

### Wave 2: Core Commands (Depends on Wave 1)

**INIT-003: Service Management Commands**
- Priority: HIGH
- Files: `cli/commands/service.py`
- Dependencies: INIT-001, INIT-002
- Commands: `service start/stop/restart/status/logs`
- Description: Process management, log tailing, health checks on startup
- Acceptance: Can start/stop service, view logs, check status
- Estimated Tokens: ~5k

**INIT-004: Health Check Commands**
- Priority: HIGH
- Files: `cli/commands/health.py`
- Dependencies: INIT-001, INIT-002
- Commands: `health check/deps/ping`
- Description: Service health, dependency verification, quick ping
- Acceptance: Health checks show accurate status, dependency issues reported
- Estimated Tokens: ~3k

**INIT-005: API Key Management**
- Priority: HIGH
- Files: `cli/commands/keys.py`
- Dependencies: INIT-001, INIT-002
- Commands: `keys create/list/revoke/permissions/test`
- Description: Wrap AuthManager and PermissionManager for key operations
- Acceptance: Can create/manage API keys, set permissions
- Estimated Tokens: ~4k

---

### Wave 3: Monitoring & Analytics (Depends on Wave 2)

**INIT-006: Usage Analytics**
- Priority: MEDIUM
- Files: `cli/commands/usage.py`
- Dependencies: INIT-001, INIT-002
- Commands: `usage summary/by-project/by-model/costs/export`
- Description: Query budget manager, format analytics, export data
- Acceptance: Usage stats accurate, export formats work
- Estimated Tokens: ~4k

**INIT-007: Worker Pool Management**
- Priority: MEDIUM
- Files: `cli/commands/workers.py`
- Dependencies: INIT-001, INIT-002
- Commands: `workers status/list/clear-queue/kill`
- Description: Worker pool inspection, queue management
- Acceptance: Shows real-time worker status, can manage queue
- Estimated Tokens: ~3k

**INIT-008: Task Management**
- Priority: MEDIUM
- Files: `cli/commands/tasks.py`
- Dependencies: INIT-001, INIT-002
- Commands: `tasks list/get/cancel/logs`
- Description: Task listing, inspection, cancellation
- Acceptance: Can view active tasks, inspect details, cancel tasks
- Estimated Tokens: ~4k

---

### Wave 4: Configuration & Testing (Depends on Wave 2)

**INIT-009: Testing Commands**
- Priority: MEDIUM
- Files: `cli/commands/test.py`
- Dependencies: INIT-001, INIT-002, INIT-005 (needs keys)
- Commands: `test completion/task/agents/skills/all`
- Description: Quick endpoint tests, agent/skill discovery validation
- Acceptance: All endpoint tests work, clear pass/fail reporting
- Estimated Tokens: ~4k

**INIT-010: Configuration Commands**
- Priority: LOW
- Files: `cli/commands/config.py`
- Dependencies: INIT-001, INIT-002
- Commands: `config show/validate/port/env`
- Description: Display and validate configuration
- Acceptance: Config validation catches issues, shows accurate info
- Estimated Tokens: ~3k

**INIT-011: Budget Management**
- Priority: LOW
- Files: `cli/commands/budgets.py`
- Dependencies: INIT-001, INIT-002
- Commands: `budgets list/set/usage/alerts`
- Description: Budget management wrapper
- Acceptance: Budget commands work correctly
- Estimated Tokens: ~3k

**INIT-012: Audit Logs**
- Priority: LOW
- Files: `cli/commands/audit.py`
- Dependencies: INIT-001, INIT-002
- Commands: `audit events/failed-auth/export`
- Description: Security event querying and filtering
- Acceptance: Audit logs queryable, export works
- Estimated Tokens: ~3k

---

### Wave 5: Polish & Documentation (Depends on All Previous)

**INIT-013: Help Text & Error Handling**
- Priority: HIGH (quality)
- Files: All command files
- Dependencies: INIT-003 through INIT-012
- Description: Comprehensive help, error messages with suggestions, progress bars
- Acceptance: All commands have clear help, errors suggest solutions
- Estimated Tokens: ~2k

**INIT-014: Documentation**
- Priority: MEDIUM
- Files: `cli/README.md`, `cli/EXAMPLES.md`, `cli/INTEGRATION.md`
- Dependencies: All previous
- Description: CLI usage guide, common workflows, Claude Code integration
- Acceptance: Documentation complete and accurate
- Estimated Tokens: ~2k

**INIT-015: Installation & Packaging**
- Priority: HIGH
- Files: `setup.py`, `requirements.txt`, shell completion scripts
- Dependencies: All previous
- Description: Package setup, dependencies, shell completion
- Acceptance: Can install with pip, completion works
- Estimated Tokens: ~2k

---

## Execution Strategy

**Manual Orchestration Approach:**
1. Build Wave 1 features first (foundation)
2. Test thoroughly before moving to Wave 2
3. Wave 2+ can be built in parallel within each wave
4. Continuous testing as we go
5. User stays engaged for decisions/approvals
6. No autonomous spawning - I execute directly

**Total Estimated Cost:** ~47k tokens across 15 initiatives

**Estimated Time:** 2-3 hours of focused work (with user engagement)

**Git Strategy:**
- Work directly on main OR create a feature branch (user preference?)
- Commit after each major feature
- Test before each commit

---

## Safety Notes

**Why Manual Orchestration:**
Given the orchestrator's documented issues (file deletion, rule non-compliance, gaslighting), we're using manual orchestration where I (Claude Code) execute directly with user oversight rather than spawning autonomous workers.

**Benefits:**
- ✅ User stays in control
- ✅ No risk of file deletion
- ✅ Can pivot on issues immediately
- ✅ Clearer communication
- ✅ Safer for production codebase

---

## Ready to Execute?

**Proposed Approach:**
1. I'll build Wave 1 (INIT-001 and INIT-002)
2. Test to ensure foundation works
3. Move to Wave 2 (service, health, keys)
4. Continue through waves with testing at each stage

**User Decision Points:**
- Git branch strategy (main vs feature branch?)
- Should I proceed with Wave 1 now?
- Any priority changes to the wish list?
