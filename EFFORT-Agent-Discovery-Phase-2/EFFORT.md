---
created: 2026-01-31T11:45:00Z
updated: 2026-01-31T11:45:00Z
status: not_started
priority: low
effort_id: EFFORT-Agent-Discovery-Phase-2
project: claude-code-api-service
goal: Add usage analytics for agents and skills
type: effort
dependencies: ["EFFORT-Agent-Discovery-Phase-1"]
---

# EFFORT: Agent/Skill Usage Analytics (Phase 2)

## Overview

Track agent and skill usage through the API service to provide analytics, identify patterns, and optimize performance. Includes API endpoints and CLI commands for viewing usage statistics.

## Problem Statement

**Current State:**
- Agents/skills are invoked via `/v1/task` endpoint
- No tracking of which agents/skills are used
- No success/failure metrics
- No cost tracking per agent
- No performance metrics

**User Need:**
- "Which agents are most popular?"
- "What's the success rate of agent X?"
- "How much does agent Y typically cost?"
- "Which agents are slow?"
- "What tasks use which agents?"

## Goals

1. **Usage Tracking** - Record every agent/skill invocation
2. **Success Metrics** - Track completion vs failure rates
3. **Cost Analysis** - Track costs per agent/skill
4. **Performance Metrics** - Duration, token usage
5. **CLI Access** - View analytics via CLI commands
6. **API Endpoints** - Query analytics programmatically

## Success Criteria

- ✅ All agent/skill invocations are tracked
- ✅ Database stores: agent, task_id, status, cost, duration, tokens
- ✅ CLI commands show usage stats
- ✅ API endpoints for analytics queries
- ✅ Historical data retained (configurable retention period)
- ✅ Reports generation (daily/weekly/monthly summaries)

## Scope

### In Scope
- Database schema for usage tracking
- Tracking in agentic_executor.py
- API endpoints for analytics
- CLI commands for viewing stats
- Cost and performance metrics
- Success/failure tracking

### Out of Scope
- Recommendations (Phase 3)
- Agent testing (Phase 5)
- Real-time alerting
- ML-based insights

## Commands to Add

```bash
# Agent analytics
claude-api agents stats [AGENT_NAME]
claude-api agents leaderboard [--by usage|cost|success-rate]
claude-api agents history AGENT_NAME [--period week|month]

# Skill analytics
claude-api skills stats [SKILL_NAME]
claude-api skills leaderboard

# Reports
claude-api analytics report [--period day|week|month]
claude-api analytics export --output stats.csv
```

## Technical Approach

**Database Schema:**
```sql
CREATE TABLE agent_usage (
    id INTEGER PRIMARY KEY,
    agent_name TEXT NOT NULL,
    task_id TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    status TEXT NOT NULL,  -- completed, failed
    duration_seconds REAL,
    cost_usd REAL,
    input_tokens INTEGER,
    output_tokens INTEGER,
    project_id TEXT,
    error_message TEXT
);

CREATE INDEX idx_agent_name ON agent_usage(agent_name);
CREATE INDEX idx_timestamp ON agent_usage(timestamp);
CREATE INDEX idx_project_id ON agent_usage(project_id);
```

**Tracking Points:**
- `src/agentic_executor.py` - Hook into task execution
- Record start, completion, metrics
- Handle failures gracefully

**API Endpoints:**
```python
GET /v1/agents/{name}/analytics
GET /v1/agents/leaderboard
GET /v1/skills/{name}/analytics
GET /v1/analytics/report
```

## Timeline

**Estimated Duration:** 4-6 hours

**Breakdown:**
- Database schema & setup: 1 hour
- Tracking implementation: 2 hours
- API endpoints: 1.5 hours
- CLI commands: 1 hour
- Testing & documentation: 30 minutes

## Dependencies

**Requires:**
- Phase 1 (Discovery CLI) - foundation
- Database (SQLite or PostgreSQL)
- API service running

**Enables:**
- Phase 3 (Recommendations) - uses analytics for recommendations
- Better cost optimization
- Performance monitoring

## Future Enhancements

- Real-time dashboards
- Alerting (e.g., high failure rate)
- Predictive analytics
- Cost forecasting
