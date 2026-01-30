# Wave 4 Wish List: Agentic API Capabilities

**Context**: Wave 1-3 complete. Simple API foundation is built. Now add agentic task execution capabilities.

**Plan Documentation**: `EFFORT-Agentic-API-Architecture/PLAN-Agentic-Implementation-2026-01-30T18-43-51Z.md`

**Supporting Docs**:
- Architecture analysis: `EFFORT-Agentic-API-Architecture/architectural-analysis.md`
- Use cases: `EFFORT-Agentic-API-Architecture/use-cases.md`
- Security model: `EFFORT-Agentic-API-Architecture/security-considerations.md`

---

## Priority: Build These 4 Features

**Important**: Before starting any initiative, read the detailed specs in the plan document above.

### 1. Agentic Task Executor (INIT-011)
**Location**: `src/agentic_executor.py`

Build the core agentic task execution engine:
- `AgenticExecutor` class that orchestrates Claude CLI in agentic mode
- Parse agentic task requests (description, allowed tools/agents/skills)
- Submit to worker pool with proper configuration
- Enable Claude Code's full capabilities (tools, agents, skills, multi-turn)
- Capture execution log (every tool call, agent spawn, skill invoke)
- Collect generated artifacts from workspace
- Timeout enforcement (configurable, default 300s)
- Cost limit enforcement (halt at max_cost threshold)
- Return structured result: summary, artifacts, execution_log, usage stats

**API Interface** (add to FastAPI app):
```python
POST /v1/task
Request: {
  "description": "Analyze src/worker_pool.py for race conditions",
  "allow_tools": ["Read", "Grep", "Bash"],
  "allow_agents": ["security-auditor"],
  "allow_skills": ["vulnerability-scanner"],
  "working_directory": "/project/src",
  "timeout": 300,
  "max_cost": 1.00
}
```

**Integration**:
- Use existing WorkerPool (INIT-001) for subprocess management
- Use existing BudgetManager (INIT-003) for cost tracking
- Use existing ModelRouter (INIT-002) for model selection

**Tests** (`tests/test_agentic_executor.py`):
- test_simple_agentic_task() - Basic task execution
- test_tool_usage() - Read, Grep, Bash tools work
- test_agent_spawning() - Can spawn agents
- test_skill_invocation() - Can invoke skills
- test_timeout_enforcement() - Long tasks timeout correctly
- test_cost_limit_enforcement() - Halts at cost cap
- test_artifact_collection() - Collects generated files
- test_execution_log() - Captures all actions
- test_error_handling() - Graceful failure handling

**Success Criteria**: POC agentic task completes successfully with tools/agents/skills

---

### 2. Security & Sandboxing (INIT-012) 🔒 CRITICAL
**Location**: `src/sandbox_manager.py`, `docker/Dockerfile.sandbox`

Docker-based sandbox for secure agentic task execution. **This MUST be complete before public launch.**

**Requirements**:
- `SandboxManager` class - Create/destroy Docker containers per task
- `Dockerfile.sandbox` - Secure Claude Code container image
- Network isolation: `network_mode: none` (no outbound access)
- Filesystem isolation: Read-only project files, workspace-only write
- Resource limits: 1 CPU core, 1GB RAM, 100MB workspace, 300s timeout
- Security options: no-new-privileges, drop all capabilities, unprivileged user
- Command validation: Block dangerous commands (rm -rf, curl, sudo, etc.)
- Path validation: Block sensitive paths (/etc/passwd, .env, *.key, etc.)
- Container cleanup: Destroy after task completes (success or failure)
- Security event logging: Log all blocked attempts

**Dockerfile.sandbox**:
```dockerfile
FROM python:3.11-slim
RUN pip install claude-cli
RUN useradd -m -u 1000 claude
USER claude
WORKDIR /workspace
ENTRYPOINT ["claude", "-p"]
```

**Docker Security Settings**:
- network_mode: none
- read_only: true
- security_opt: ["no-new-privileges"]
- cap_drop: ["ALL"]
- CPU/memory/PID limits
- tmpfs workspace with noexec,nosuid

**Blocked Commands** (minimum):
- `rm -rf`, `dd if=`, `mkfs`, `format`
- `curl`, `wget`, `nc`, `telnet` (network tools)
- `sudo`, `su`, `chmod +s` (privilege escalation)
- Fork bombs, infinite loops

**Blocked Paths** (minimum):
- `/etc/passwd`, `/etc/shadow`
- `~/.ssh/`, `.env`, `credentials.json`, `secrets.yaml`
- `*.pem`, `*.key`, API tokens

**Tests** (`tests/test_sandbox.py`):
- test_network_isolation() - curl fails
- test_filesystem_isolation() - can't read /etc/passwd
- test_resource_limits() - CPU/memory caps enforced
- test_command_blocking() - dangerous commands rejected
- test_path_validation() - sensitive files blocked
- test_container_cleanup() - containers destroyed
- test_concurrent_sandboxes() - multiple isolated tasks
- test_timeout_enforcement() - hard timeout kills task
- test_workspace_isolation() - tasks can't see each other

**Integration**:
- AgenticExecutor calls SandboxManager.create_sandbox() before execution
- All agentic tasks run inside sandboxes (no exceptions)

**Success Criteria**: Penetration test shows no sandbox escapes, no sensitive data access

---

### 3. Permission System (INIT-013)
**Location**: `src/permission_manager.py`

Per-API-key permission profiles for tool/agent/skill access control.

**Requirements**:
- `PermissionManager` class - Validate task requests against API key profiles
- Database table: `api_key_permissions` (SQLite)
- Permission validation: Check tools/agents/skills against whitelist
- Resource validation: Check timeout/cost against limits
- Permission violation logging (to audit log)
- Default permission profiles (Free, Pro, Enterprise)
- Admin API for permission management

**Database Schema**:
```sql
CREATE TABLE api_key_permissions (
    api_key TEXT PRIMARY KEY,
    allowed_tools TEXT NOT NULL,        -- JSON: ["Read", "Grep", "Bash"]
    blocked_tools TEXT NOT NULL,        -- JSON: ["Write", "Edit"]
    allowed_agents TEXT NOT NULL,       -- JSON: ["security-auditor"]
    allowed_skills TEXT NOT NULL,       -- JSON: ["vulnerability-scanner"]
    max_concurrent_tasks INTEGER DEFAULT 3,
    max_cpu_cores REAL DEFAULT 1.0,
    max_memory_gb REAL DEFAULT 1.0,
    max_execution_seconds INTEGER DEFAULT 300,
    max_cost_per_task REAL DEFAULT 1.00,
    network_access BOOLEAN DEFAULT FALSE,
    filesystem_access TEXT DEFAULT 'readonly',
    workspace_size_mb INTEGER DEFAULT 100,
    FOREIGN KEY (api_key) REFERENCES api_keys(key)
);
```

**Default Profiles**:
- **Free**: Read-only, no agents, 1 concurrent, 60s timeout
- **Pro**: Read+Grep+Bash, 3 agents, 3 concurrent, 300s timeout
- **Enterprise**: Custom negotiated permissions

**Validation Flow**:
```python
# Validate before creating sandbox
profile = permission_manager.get_profile(api_key)
permission_manager.validate_task_request(
    api_key,
    requested_tools,
    requested_agents,
    requested_skills,
    timeout,
    max_cost
)
# If validation fails → 403 Permission Denied
# If validation passes → proceed to sandbox
```

**Tests** (`tests/test_permissions.py`):
- test_permission_validation()
- test_tool_whitelist_enforcement()
- test_agent_whitelist_enforcement()
- test_resource_limit_enforcement()
- test_permission_violation_logging()
- test_default_profiles()

**Integration**:
- Add middleware to `/v1/task` endpoint
- Validate BEFORE creating sandbox

**Success Criteria**: Unauthorized tools/agents rejected, limits enforced

---

### 4. Audit Logging & Monitoring (INIT-014)
**Location**: `src/audit_logger.py`

Comprehensive audit trail for all agentic task activity.

**Requirements**:
- `AuditLogger` class - Log all task events
- Database table: `audit_log` (SQLite)
- Event types: tool_call, file_access, bash_command, agent_spawn, skill_invoke, security_event
- Severity levels: info, warning, critical
- Security alerts: Immediate notification for blocked attempts
- Log viewer API: Query logs by task_id, api_key, event_type, date range
- Analytics queries: Most used tools, security events by key, avg execution time

**Database Schema**:
```sql
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    api_key TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    event_type TEXT NOT NULL,
    details TEXT NOT NULL,  -- JSON
    severity TEXT DEFAULT 'info',
    INDEX(task_id),
    INDEX(api_key),
    INDEX(event_type),
    INDEX(timestamp)
);
```

**Events to Log**:
1. Tool calls: `{"type": "tool_call", "tool": "Read", "file": "src/worker_pool.py"}`
2. Bash commands: `{"type": "bash_command", "command": "pytest tests/"}`
3. Agent spawns: `{"type": "agent_spawn", "agent": "security-auditor"}`
4. Skill invocations: `{"type": "skill_invoke", "skill": "vulnerability-scanner"}`
5. Security events: `{"type": "security_event", "event": "blocked_command", "command": "curl"}`

**Security Alerts** (immediate):
- Blocked command attempts
- Permission violations
- Sensitive file access attempts
- Resource limit hits
- Repeated failures (potential probing)

**Tests** (`tests/test_audit_logging.py`):
- test_tool_call_logging()
- test_security_event_logging()
- test_log_search()
- test_analytics_queries()
- test_alert_generation()

**Integration**:
- AgenticExecutor calls audit_logger at every step
- SandboxManager logs security events

**Success Criteria**: All events logged, security alerts fire correctly

---

## Modifications to Existing Initiatives

### INIT-004: REST API Endpoints (ADD)
**Add**: `/v1/task` endpoint using AgenticExecutor
**Add**: Pydantic models for `AgenticTaskRequest` and `AgenticTaskResponse`
**Add**: Integration with permission validation

### INIT-007: WebSocket Streaming (ADD)
**Add**: Stream agentic execution steps in real-time
**Event types**: `thinking`, `tool_call`, `agent_spawn`, `skill_invoke`, `result`

**Example stream**:
```json
{"type": "thinking", "content": "I'll analyze for race conditions"}
{"type": "tool_call", "tool": "Read", "file": "src/worker_pool.py"}
{"type": "agent_spawn", "agent": "security-auditor"}
{"type": "result", "summary": "Found 2 issues", "artifacts": [...]}
```

### INIT-009: Python Client Library (ADD)
**Add**: `client.execute_task()` method
**Add**: Async support for long-running tasks
**Add**: Streaming support via websocket

**Example usage**:
```python
result = client.execute_task(
    description="Analyze API for security issues",
    allow_tools=["Read", "Grep"],
    allow_agents=["security-auditor"]
)
```

---

## Execution Guidelines

### Dependency Order
**Wave 4A** (parallel - no dependencies):
- INIT-011 (Agentic Executor)
- INIT-012 (Sandbox)
- INIT-014 (Audit Logging)

**Wave 4B** (after 4A):
- INIT-013 (Permissions) - needs audit logger integration

**Wave 4C** (after all above):
- Modify INIT-004, INIT-007, INIT-009

### Git Branching
Each initiative gets its own branch:
- `feature/INIT-011-agentic-executor`
- `feature/INIT-012-security-sandbox`
- `feature/INIT-013-permissions`
- `feature/INIT-014-audit-logging`

### Testing Requirements
- All tests MUST pass before merge
- Security penetration testing for INIT-012 (blocking)
- Integration tests for full agentic workflow
- Performance benchmarks (< 60s avg execution)

### Security Requirements
⚠️ **CRITICAL**: INIT-012 (Sandbox) is BLOCKING for any public launch. No shortcuts. No "we'll add it later." Docker sandbox MUST be complete and penetration tested before agentic API goes live.

---

## Success Criteria (All Must Pass)

- [ ] Can execute agentic tasks with tools (Read, Grep, Bash)
- [ ] Can spawn agents during task execution
- [ ] Can invoke skills during task execution
- [ ] All tasks run in Docker sandbox (no exceptions)
- [ ] Network isolation verified (no egress possible)
- [ ] Filesystem isolation verified (no /etc access)
- [ ] Dangerous commands blocked (curl, rm -rf, sudo, etc.)
- [ ] Sensitive paths blocked (.env, SSH keys, etc.)
- [ ] Permission system enforces API key limits
- [ ] All events logged to audit trail
- [ ] Security alerts fire on violations
- [ ] Penetration test shows no sandbox escapes
- [ ] Integration tests pass (end-to-end agentic workflow)
- [ ] Performance: < 60s average task execution
- [ ] Cost: Actual vs estimated within 20%

---

## Notes for Orchestrator

**Read the plan first**: Before starting work, read `EFFORT-Agentic-API-Architecture/PLAN-Agentic-Implementation-2026-01-30T18-43-51Z.md` for complete details.

**Security is non-negotiable**: INIT-012 must be complete and tested before launch. No compromises.

**Test after each feature**: Run pytest after completing each initiative. Don't merge broken code.

**Budget tracking**: Each initiative has token budget. Track usage, report when approaching limits.

---

**Let's build the agentic API that no one else offers.** 🚀
