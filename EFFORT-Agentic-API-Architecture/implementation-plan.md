# Implementation Plan: Agentic API

This document outlines the technical implementation roadmap if the decision is made to pursue agentic task execution capabilities.

---

## Phased Rollout Strategy

### Phase 1: Foundation (Current - Wave 1-3)
**Goal**: Prove the simple API concept
**Duration**: 4-6 weeks
**Status**: In Progress

#### Initiatives (Existing)
- ✅ INIT-001: Worker Pool Manager
- ✅ INIT-002: Model Auto-Router
- ⏳ INIT-003: Budget Manager
- ⏸️ INIT-004: REST API Endpoints
- ⏸️ INIT-005: Token Tracking
- ⏸️ INIT-006: Redis Integration
- ⏸️ INIT-007: WebSocket Streaming
- ⏸️ INIT-008: Authentication Middleware
- ⏸️ INIT-009: Python Client Library
- ⏸️ INIT-010: Documentation & Examples

#### Deliverables
- Working simple completion API
- `/v1/chat/completions` endpoint
- Worker pool management
- Budget tracking
- Basic authentication

#### Success Criteria
- Simple API functional
- 95%+ uptime
- < 2s response time
- Tests passing
- Documentation complete

---

### Phase 2: Agentic POC (Wave 4)
**Goal**: Validate agentic concept
**Duration**: 2-3 weeks
**Status**: Planned (pending decision)

#### New Initiatives

##### INIT-011: Agentic Task Executor (Core)
**Complexity**: High
**Budget**: 25k tokens
**Description**: Core agentic task execution engine

**Requirements**:
- Parse agentic task requests
- Spawn Claude CLI in agentic mode
- Enable tool/agent/skill access
- Capture multi-turn execution log
- Return results + artifacts
- Timeout enforcement
- Error handling

**Implementation**:
```python
# src/agentic_executor.py

class AgenticExecutor:
    def __init__(self, worker_pool: WorkerPool):
        self.worker_pool = worker_pool
        self.sandbox_manager = SandboxManager()

    async def execute_task(
        self,
        description: str,
        allow_tools: List[str],
        allow_agents: List[str],
        allow_skills: List[str],
        working_directory: str,
        timeout: int,
        max_cost: float
    ) -> AgenticResult:
        # Create sandbox
        sandbox = self.sandbox_manager.create_sandbox()

        # Build Claude CLI command
        cmd = self._build_agentic_command(
            description, allow_tools, allow_agents, allow_skills
        )

        # Execute in sandbox with monitoring
        result = await self._execute_in_sandbox(
            sandbox, cmd, timeout, max_cost
        )

        # Cleanup sandbox
        self.sandbox_manager.destroy_sandbox(sandbox)

        return result
```

**Tests**:
- test_simple_agentic_task()
- test_tool_usage_in_task()
- test_agent_spawning()
- test_skill_invocation()
- test_timeout_enforcement()
- test_cost_limit_enforcement()

**Deliverables**:
- Working agentic executor
- POC endpoint `/v1/task` (alpha)
- Basic execution logging

---

##### INIT-012: Security & Sandboxing (Critical)
**Complexity**: High
**Budget**: 30k tokens
**Description**: Docker-based sandboxing with security controls

**Requirements**:
- Docker container isolation
- Network restrictions (no egress)
- Filesystem restrictions (workspace-only write)
- Resource limits (CPU, memory, disk)
- Command blacklist enforcement
- File path validation
- Security event logging

**Implementation**:
```python
# src/sandbox_manager.py

class SandboxManager:
    def create_sandbox(self, task_id: str) -> Sandbox:
        # Create Docker container
        container = docker.from_env().containers.run(
            image="claude-code-sandbox:latest",
            detach=True,
            network_mode="none",  # No network
            cpu_period=100000,
            cpu_quota=100000,  # 1 CPU core
            mem_limit="1g",
            memswap_limit="1g",
            pids_limit=100,
            read_only=True,
            tmpfs={"/tmp": "rw,noexec,nosuid,size=100m"},
            volumes={
                "/project": {"bind": "/project-ro", "mode": "ro"},
                f"/tmp/workspace-{task_id}": {"bind": "/workspace", "mode": "rw"}
            },
            security_opt=["no-new-privileges"],
            cap_drop=["ALL"]
        )

        return Sandbox(task_id, container)

    def destroy_sandbox(self, sandbox: Sandbox):
        sandbox.container.stop()
        sandbox.container.remove()
        shutil.rmtree(f"/tmp/workspace-{sandbox.task_id}")
```

**Dockerfile**:
```dockerfile
FROM python:3.11-slim

# Install Claude CLI
RUN pip install claude-cli

# Create unprivileged user
RUN useradd -m -u 1000 claude && \
    chown claude:claude /workspace

USER claude
WORKDIR /workspace

ENTRYPOINT ["claude", "-p", "--dangerously-skip-permissions"]
```

**Tests**:
- test_network_isolation()
- test_filesystem_isolation()
- test_resource_limits()
- test_command_blocking()
- test_path_validation()
- test_container_cleanup()

**Deliverables**:
- Docker sandbox implementation
- Security validation tests passing
- Dockerfile + build scripts

---

##### INIT-013: Permission System
**Complexity**: Medium
**Budget**: 15k tokens
**Description**: Per-API-key permission profiles

**Requirements**:
- API key permission storage (SQLite)
- Tool/agent/skill whitelists per key
- Resource limit configuration per key
- Permission validation middleware
- Permission violation logging

**Database Schema**:
```sql
CREATE TABLE api_key_permissions (
    api_key TEXT PRIMARY KEY,
    allowed_tools TEXT,  -- JSON array
    allowed_agents TEXT,  -- JSON array
    allowed_skills TEXT,  -- JSON array
    max_concurrent_tasks INTEGER,
    max_cpu_cores REAL,
    max_memory_gb REAL,
    max_execution_seconds INTEGER,
    max_cost_per_task REAL,
    network_access BOOLEAN,
    filesystem_access TEXT,  -- "readonly" | "readwrite" | "none"
    created_at TIMESTAMP,
    FOREIGN KEY (api_key) REFERENCES api_keys(key)
);
```

**API**:
```python
# src/permission_manager.py

class PermissionManager:
    def validate_task_request(
        self,
        api_key: str,
        requested_tools: List[str],
        requested_agents: List[str],
        requested_skills: List[str]
    ) -> PermissionValidation:
        profile = self.get_profile(api_key)

        # Check each permission
        if not all(t in profile.allowed_tools for t in requested_tools):
            return PermissionValidation(
                allowed=False,
                reason="Tool not allowed"
            )

        # ... similar checks for agents, skills

        return PermissionValidation(allowed=True)
```

**Tests**:
- test_permission_validation()
- test_tool_whitelist_enforcement()
- test_resource_limit_enforcement()

**Deliverables**:
- Permission system implementation
- API key management endpoints
- Permission violation logging

---

##### INIT-014: Audit Logging
**Complexity**: Low
**Budget**: 10k tokens
**Description**: Comprehensive audit trail

**Requirements**:
- Log all tool calls
- Log all file accesses
- Log all bash commands
- Log all agent/skill invocations
- Log security events
- Searchable log interface

**Schema**:
```sql
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    api_key TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    event_type TEXT NOT NULL,  -- "tool_call" | "file_access" | "bash_command" | "security_event"
    details TEXT NOT NULL,  -- JSON
    INDEX(task_id),
    INDEX(api_key),
    INDEX(event_type),
    INDEX(timestamp)
);
```

**Implementation**:
```python
# src/audit_logger.py

class AuditLogger:
    def log_tool_call(self, task_id: str, api_key: str, tool: str, args: dict):
        self.db.execute(
            "INSERT INTO audit_log (task_id, api_key, event_type, details) VALUES (?, ?, ?, ?)",
            (task_id, api_key, "tool_call", json.dumps({"tool": tool, "args": args}))
        )

    def log_security_event(self, task_id: str, api_key: str, event: str, details: dict):
        self.db.execute(
            "INSERT INTO audit_log (task_id, api_key, event_type, details) VALUES (?, ?, ?, ?)",
            (task_id, api_key, "security_event", json.dumps({"event": event, **details}))
        )

        # Also alert if critical
        if event in ["unauthorized_access", "blocked_command"]:
            self.alert_security_team(task_id, api_key, event, details)
```

**Tests**:
- test_tool_call_logging()
- test_security_event_logging()
- test_log_search()

**Deliverables**:
- Audit logging implementation
- Log viewer interface
- Security alert integration

---

### Phase 3: Alpha Testing (Internal)
**Goal**: Test agentic API with real use cases
**Duration**: 2 weeks
**Status**: Future

#### Activities
- Deploy to staging environment
- Internal testing with real agents/skills
- Performance benchmarking
- Security penetration testing
- Cost analysis
- Bug fixes

#### Test Cases
1. **Code Analysis**: "Analyze our API for security issues"
2. **Documentation**: "Generate API docs from FastAPI app"
3. **Test Generation**: "Create test suite for budget_manager.py"
4. **Multi-Agent**: "Extract workflow from meeting, sync to files"

#### Success Criteria
- 90%+ task success rate
- No security breaches in pen test
- Execution time < 5 minutes average
- Cost within budget estimates
- No memory leaks or resource exhaustion

---

### Phase 4: Beta Release (Limited)
**Goal**: Gather customer feedback
**Duration**: 4 weeks
**Status**: Future

#### Activities
- Invite 10-20 beta users
- Provide limited API keys
- Gather usage data
- Collect feedback
- Iterate on pain points

#### Beta User Profile
- Technical users (developers, DevOps)
- Willing to provide feedback
- Understanding of alpha quality
- Diverse use cases

#### Metrics to Track
- Task success rate
- Average execution time
- Cost per task
- User satisfaction
- Feature requests
- Bug reports

---

### Phase 5: Public Launch
**Goal**: General availability
**Duration**: Ongoing
**Status**: Future

#### Pre-Launch Checklist
- [ ] Security audit complete
- [ ] Load testing passed
- [ ] Documentation complete
- [ ] Pricing finalized
- [ ] Support plan ready
- [ ] Monitoring dashboard live
- [ ] Incident response plan
- [ ] Legal terms reviewed

#### Launch Plan
1. Announce Tier 2 (Agentic API)
2. Migrate beta users to production
3. Open signups for new users
4. Marketing campaign
5. Monitor closely for issues

---

## Technical Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────┐
│                   API Gateway                        │
│  - Authentication                                    │
│  - Rate Limiting                                     │
│  - Request Routing                                   │
└──────────────────┬──────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
  ┌─────▼─────┐        ┌─────▼──────┐
  │  Simple   │        │  Agentic   │
  │  Handler  │        │  Handler   │
  └─────┬─────┘        └─────┬──────┘
        │                    │
        │              ┌─────▼──────────┐
        │              │ Permission     │
        │              │ Validator      │
        │              └─────┬──────────┘
        │                    │
        │              ┌─────▼──────────┐
        │              │ Sandbox        │
        │              │ Manager        │
        │              └─────┬──────────┘
        │                    │
  ┌─────▼────────────────────▼──────┐
  │       Worker Pool                │
  │  ┌──────┐  ┌──────┐  ┌──────┐  │
  │  │Worker│  │Worker│  │Worker│  │
  │  └──────┘  └──────┘  └──────┘  │
  └─────┬────────────────────┬──────┘
        │                    │
  ┌─────▼─────┐        ┌─────▼──────┐
  │  Budget   │        │  Audit     │
  │  Manager  │        │  Logger    │
  └───────────┘        └────────────┘
```

### File Structure (After Phase 2)

```
claude-code-api-service/
├── src/
│   ├── worker_pool.py          # INIT-001 ✅
│   ├── model_router.py         # INIT-002 ✅
│   ├── budget_manager.py       # INIT-003 ✅
│   ├── api.py                  # INIT-004 (modified for /v1/task)
│   ├── token_tracker.py        # INIT-005 ✅
│   ├── cache.py                # INIT-006 ✅
│   ├── websocket.py            # INIT-007 (modified for agentic streaming)
│   ├── auth.py                 # INIT-008 ✅
│   ├── agentic_executor.py     # INIT-011 🆕
│   ├── sandbox_manager.py      # INIT-012 🆕
│   ├── permission_manager.py   # INIT-013 🆕
│   └── audit_logger.py         # INIT-014 🆕
├── docker/
│   ├── Dockerfile.sandbox      # INIT-012 🆕
│   └── docker-compose.yml
├── tests/
│   ├── test_agentic_executor.py    # INIT-011 🆕
│   ├── test_sandbox.py             # INIT-012 🆕
│   ├── test_permissions.py         # INIT-013 🆕
│   └── test_audit_logging.py       # INIT-014 🆕
└── docs/
    └── agentic-api.md          # INIT-011 🆕
```

---

## Resource Requirements

### Development Team
- 1 Senior Backend Engineer (agentic executor)
- 1 Security Engineer (sandboxing)
- 1 DevOps Engineer (Docker infrastructure)
- 1 QA Engineer (testing)

### Timeline Summary
- Phase 1 (Foundation): 6 weeks - **In Progress**
- Phase 2 (Agentic POC): 3 weeks
- Phase 3 (Alpha Testing): 2 weeks
- Phase 4 (Beta Release): 4 weeks
- Phase 5 (Public Launch): Ongoing

**Total to Public Launch**: ~15 weeks from today

### Cost Estimates

**Development Cost**:
- Engineering: 4 people × 9 weeks × $80/hr × 40hr = $115,200
- Infrastructure: $2,000/month × 3 months = $6,000
- Security audit: $15,000
- **Total**: ~$136,000

**Ongoing Costs**:
- Infrastructure: $5,000/month
- Support: $10,000/month
- Monitoring: $500/month
- **Total**: ~$15,500/month

---

## Risk Analysis

### High Risk
- **Security breach**: Docker escape, data exfiltration
  - **Mitigation**: Thorough pen testing, security audit
- **Resource exhaustion**: Malicious users DoS the system
  - **Mitigation**: Strict resource limits, rate limiting

### Medium Risk
- **Cost overruns**: Agentic tasks more expensive than estimated
  - **Mitigation**: Per-task cost caps, better routing
- **Performance issues**: Slow execution, timeouts
  - **Mitigation**: Optimize sandbox startup, caching

### Low Risk
- **User confusion**: Don't understand agentic vs simple
  - **Mitigation**: Clear documentation, examples
- **Limited adoption**: Nobody uses agentic features
  - **Mitigation**: Marketing, use case examples

---

## Success Metrics

### Technical Metrics
- **Availability**: 99.9% uptime
- **Performance**: < 60s average task execution
- **Security**: 0 critical vulnerabilities
- **Cost**: < $0.10 average cost per task

### Business Metrics
- **Adoption**: 30% of users try agentic API
- **Retention**: 60% of agentic users stay active
- **Revenue**: $10k MRR from Tier 2 within 3 months
- **NPS**: > 40 for agentic users

---

## Go/No-Go Decision Criteria

### Proceed with Agentic API if:
✅ Security model validated by third-party
✅ POC demonstrates value (Phase 2)
✅ Cost model is sustainable
✅ Team has capacity for 3-month project
✅ Customer demand confirmed

### Defer Agentic API if:
❌ Security concerns unresolved
❌ POC shows limited value
❌ Cost model unsustainable
❌ Team bandwidth constrained
❌ No clear customer demand

---

## Next Steps

1. **Decision**: Choose architectural option (1, 2, or 3)
2. **If proceeding with agentic**:
   - Add Wave 4 initiatives to roadmap
   - Assign team members
   - Set timeline
   - Begin Phase 2 planning
3. **If not proceeding**:
   - Complete Wave 1-3 as planned
   - Revisit agentic decision in 6 months

---

**This is an ambitious but achievable plan. The hybrid approach de-risks the agentic implementation while delivering value incrementally.** 🚀
