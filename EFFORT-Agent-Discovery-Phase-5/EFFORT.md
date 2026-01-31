---
created: 2026-01-31T11:45:00Z
updated: 2026-01-31T11:45:00Z
status: not_started
priority: low
effort_id: EFFORT-Agent-Discovery-Phase-5
project: claude-code-api-service
goal: Add agent/skill testing framework
type: effort
dependencies: ["EFFORT-Agent-Discovery-Phase-1"]
---

# EFFORT: Agent/Skill Testing Framework (Phase 5)

## Overview

Create a testing framework for validating agents and skills through the API service, including test suites, quality scoring, and regression testing.

## Problem Statement

**Current State:**
- No way to test agents before using them
- No validation that agents work correctly
- No quality metrics for agent output
- No regression testing when agents change

**User Need:**
- "Does this agent work?"
- "Test agent X with sample input"
- "Validate all agents before deployment"
- "Run regression tests on agents"
- "Quality score for agent output"

## Goals

1. **Agent Testing** - Test agents via CLI with sample inputs
2. **Quality Scoring** - Rate agent output quality
3. **Test Suites** - Predefined tests for each agent
4. **Regression Testing** - Detect when agents break
5. **Validation** - Verify agents meet requirements
6. **Performance Testing** - Measure speed and cost

## Success Criteria

- ✅ `claude-api agents test AGENT` runs agent with test input
- ✅ Test results include: success/failure, duration, cost, quality score
- ✅ Test suites can be defined per agent
- ✅ Regression detection when output changes
- ✅ Performance benchmarks per agent
- ✅ Validation against expected output

## Scope

### In Scope
- CLI test commands
- Test suite definitions
- Quality scoring (basic)
- API endpoint for testing
- Performance metrics
- Test result history

### Out of Scope
- Advanced AI-based quality assessment
- Automated test generation
- Load testing
- Integration testing with external services

## Test Suite Format

```yaml
# .claude/tests/company-workflow-analyst.yaml
agent: company-workflow-analyst
version: 1.0
tests:
  - name: "Extract simple workflow"
    input:
      description: "Extract workflow from this text: User logs in, fills form, submits."
      allow_tools: ["Read"]
    expected:
      status: completed
      duration_max_seconds: 30
      cost_max_usd: 1.00
      output_contains: ["login", "form", "submit"]

  - name: "Handle missing input"
    input:
      description: "Extract workflow"
    expected:
      status: failed
      error_contains: "no input provided"
```

## Commands to Add

```bash
# Test single agent
claude-api agents test AGENT_NAME \
  --task "Test task description" \
  --key API_KEY

# Run test suite
claude-api agents test AGENT_NAME --suite

# Test all agents
claude-api agents test-all --suite

# Benchmark agent
claude-api agents benchmark AGENT_NAME --iterations 10

# Validate agent
claude-api agents validate AGENT_NAME

# Compare agent versions
claude-api agents compare AGENT_NAME --v1 v1.0 --v2 v2.0
```

## Technical Approach

**Testing Framework:**
```python
class AgentTester:
    def test_agent(
        self,
        agent_name: str,
        task: str,
        expected_output: Dict = None,
        max_cost: float = None,
        max_duration: float = None
    ) -> TestResult:
        # 1. Execute agent via API
        # 2. Measure duration and cost
        # 3. Compare output to expected
        # 4. Calculate quality score
        # 5. Return detailed results

    def run_test_suite(self, agent_name: str) -> List[TestResult]:
        # Run all tests for agent

    def benchmark(self, agent_name: str, iterations: int) -> Benchmark:
        # Run agent multiple times, aggregate metrics
```

**Quality Scoring:**
```python
def score_output(actual: str, expected: Dict) -> float:
    """
    Score output quality (0-100)
    - Contains expected keywords: +points
    - Matches expected format: +points
    - Reasonable length: +points
    - No errors: +points
    """
```

**API Endpoint:**
```python
POST /v1/agents/{name}/test
{
  "task": "Test task",
  "expected": {...},
  "max_cost": 1.00
}
```

## Timeline

**Estimated Duration:** 2-3 hours

**Breakdown:**
- Testing framework: 1.5 hours
- CLI commands: 30 minutes
- Test suite format: 30 minutes
- Documentation: 30 minutes

## Dependencies

**Requires:**
- Phase 1 (Discovery) - agent information
- API service with /v1/task endpoint

**Optional:**
- Phase 2 (Analytics) - historical comparison

## Example Output

```bash
$ claude-api agents test company-workflow-analyst --suite

Testing: company-workflow-analyst
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Test 1: Extract simple workflow
  ✓ Status: completed
  ✓ Duration: 12.3s (under 30s limit)
  ✓ Cost: $0.45 (under $1.00 limit)
  ✓ Output contains: login, form, submit
  Quality Score: 95/100

Test 2: Handle complex workflow
  ✓ Status: completed
  ⚠ Duration: 45.2s (exceeds 30s limit)
  ✓ Cost: $0.78
  ✓ Output structure valid
  Quality Score: 88/100

Test 3: Handle missing input
  ✓ Status: failed
  ✓ Error message correct
  Quality Score: 100/100

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Results: 3/3 tests passed
Average Quality: 94/100
Total Cost: $1.23

⚠ Warnings:
  • Test 2 exceeded duration limit (45.2s > 30s)

$ claude-api agents benchmark company-workflow-analyst --iterations 5

Benchmark Results: company-workflow-analyst
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Iterations:     5
Success Rate:   100% (5/5)
Avg Duration:   14.2s (min: 12.1s, max: 18.3s)
Avg Cost:       $0.52 (min: $0.45, max: $0.61)
Avg Tokens:     1,234 (in: 456, out: 778)
Quality Score:  92/100
```

## Test Suite Management

```bash
# Create test suite
claude-api agents create-test AGENT_NAME

# Edit test suite
claude-api agents edit-test AGENT_NAME

# Validate test suite
claude-api agents validate-test AGENT_NAME

# Run specific test
claude-api agents test AGENT_NAME --test "Extract simple workflow"
```

## Integration with CI/CD

```bash
# In CI pipeline
claude-api agents test-all --suite --json > test-results.json
if [ $? -ne 0 ]; then
  echo "Agent tests failed"
  exit 1
fi
```

## Future Enhancements

- AI-powered output quality assessment
- Visual regression testing
- Performance regression detection
- Automated test generation from usage patterns
- Test coverage metrics
- A/B testing of agent versions
