---
created: 2026-01-31T11:45:00Z
updated: 2026-01-31T11:45:00Z
status: not_started
priority: low
effort_id: EFFORT-Agent-Discovery-Phase-3
project: claude-code-api-service
goal: Add smart agent/skill recommendations
type: effort
dependencies: ["EFFORT-Agent-Discovery-Phase-1", "EFFORT-Agent-Discovery-Phase-2"]
---

# EFFORT: Smart Agent/Skill Recommendations (Phase 3)

## Overview

Intelligent recommendation system that suggests the best agents/skills for a given task based on description, past usage patterns, success rates, and tool requirements.

## Problem Statement

**Current State:**
- Users must know which agents exist
- No guidance on which agent to use for a task
- Trial and error to find the right agent
- No learning from past successes

**User Need:**
- "Which agent should I use for workflow extraction?"
- "Recommend an agent for analyzing PDFs"
- "What's the best agent for my use case?"
- "Show me agents similar to what worked before"

## Goals

1. **Task-Based Recommendations** - Suggest agents based on task description
2. **Tool-Based Matching** - Find agents with required tools
3. **Success-Rate Ranking** - Prioritize agents with high success rates
4. **Similarity Matching** - Find agents similar to past successful tasks
5. **Cost Awareness** - Consider cost in recommendations
6. **Learning System** - Improve recommendations over time

## Success Criteria

- ✅ `claude-api agents recommend "task description"` returns relevant agents
- ✅ Recommendations ranked by relevance and success rate
- ✅ Tool-based filtering works
- ✅ Cost-aware recommendations available
- ✅ Similar-task matching works
- ✅ Accuracy improves with more usage data

## Scope

### In Scope
- Keyword matching (task description → agent description)
- Tool requirement matching
- Success rate integration from Phase 2
- Cost-based filtering
- CLI recommendation command
- API endpoint

### Out of Scope
- ML-based recommendations (future enhancement)
- Real-time personalization
- A/B testing of recommendations
- Detailed explanation of recommendations

## Commands to Add

```bash
# Recommend agents for a task
claude-api agents recommend "Extract workflow from meeting transcript"

# Recommend with tool requirements
claude-api agents recommend "Analyze document" --needs-tools Read,Write

# Cost-aware recommendations
claude-api agents recommend "Process data" --max-cost 1.00

# Similar to past task
claude-api agents recommend --similar-to TASK_ID

# For skills
claude-api skills recommend "Parse PDF forms"
```

## Technical Approach

**Matching Algorithm:**
1. **Keyword Matching** - TF-IDF or semantic similarity
2. **Tool Filtering** - Exact match on required tools
3. **Success Rate** - Weight by historical success rate
4. **Cost Filtering** - Remove agents exceeding budget
5. **Ranking** - Combined score of relevance + success + cost

**Implementation:**
```python
class RecommendationEngine:
    def recommend(
        self,
        task_description: str,
        required_tools: List[str] = None,
        max_cost: float = None,
        limit: int = 5
    ) -> List[AgentRecommendation]:
        # 1. Get all agents
        # 2. Filter by tools
        # 3. Calculate similarity scores
        # 4. Weight by success rate
        # 5. Filter by cost
        # 6. Return top N
```

**API Endpoint:**
```python
POST /v1/agents/recommend
{
  "task_description": "...",
  "required_tools": ["Read", "Write"],
  "max_cost": 1.00,
  "limit": 5
}
```

## Timeline

**Estimated Duration:** 3-4 hours

**Breakdown:**
- Recommendation engine: 2 hours
- API endpoint: 30 minutes
- CLI command: 30 minutes
- Testing: 30 minutes
- Documentation: 30 minutes

## Dependencies

**Requires:**
- Phase 1 (Discovery) - agent/skill data
- Phase 2 (Analytics) - success rates and costs
- Text similarity library (sklearn or sentence-transformers)

**Optional:**
- ML models for better matching (future)

## Example Output

```bash
$ claude-api agents recommend "Extract workflow from meeting transcript"

Recommended Agents:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. company-workflow-analyst (95% match)
   Success Rate: 92%
   Avg Cost: $0.45
   Model: sonnet
   Why: Specialized in workflow extraction from transcripts

2. document-processor (78% match)
   Success Rate: 88%
   Avg Cost: $0.23
   Model: haiku
   Why: Handles document analysis, lower cost

3. meeting-transcript-processor (72% match)
   Success Rate: 85%
   Avg Cost: $0.38
   Model: sonnet
   Why: Processes meeting content, includes summarization
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Use: claude-api agents info AGENT_NAME for details
```

## Future Enhancements

- ML-based semantic matching
- Collaborative filtering (users like you used...)
- Personalized recommendations per project
- Explanation generation (why this agent?)
- Confidence scores
