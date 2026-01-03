# Agent Coordination

Patterns for multi-agent coordination, shared state, and swarm behavior.

## Overview

When multiple agents work together, they need:

1. **Shared State**: What do we collectively know?
2. **Task Coordination**: Who's working on what?
3. **Communication**: How do agents signal each other?
4. **Consensus**: How do we make collective decisions?

## Architecture Patterns

### Pattern 1: Blackboard (Shared Workspace)

Agents read from and write to a shared knowledge store:

```text
+---------------------------------------------------------------------------+
|                           BLACKBOARD                                      |
+---------------------------------------------------------------------------+
|                                                                           |
|   +-------------------------------------------------------------------+   |
|   |                      SHARED STATE                                 |   |
|   |                                                                   |   |
|   |  context:                                                         |   |
|   |    task: "investigate incident INC-1234"                          |   |
|   |    started: 2025-01-02T10:30:00Z                                  |   |
|   |                                                                   |   |
|   |  findings:                                                        |   |
|   |    - agent: ops/deploy-validator                                  |   |
|   |      finding: "deployment v1.2.3 at 10:15 UTC"                    |   |
|   |    - agent: security/incident-response-lead                       |   |
|   |      finding: "error rate spike correlates with deploy"           |   |
|   |                                                                   |   |
|   |  hypotheses:                                                      |   |
|   |    - "database connection pool exhaustion" (confidence: 0.7)      |   |
|   |    - "memory leak in new feature" (confidence: 0.3)               |   |
|   |                                                                   |   |
|   |  actions_taken:                                                   |   |
|   |    - agent: ops/rollback-advisor                                  |   |
|   |      action: "recommended rollback"                               |   |
|   |      status: awaiting_approval                                    |   |
|   +-------------------------------------------------------------------+   |
|                                                                           |
|        ^              ^              ^              ^                     |
|        |              |              |              |                     |
|   +----+----+   +----+----+   +----+----+   +----+----+                   |
|   | Agent A |   | Agent B |   | Agent C |   | Agent D |                   |
|   | (read/  |   | (read/  |   | (read/  |   | (read/  |                   |
|   |  write) |   |  write) |   |  write) |   |  write) |                   |
|   +---------+   +---------+   +---------+   +---------+                   |
|                                                                           |
+---------------------------------------------------------------------------+
```

### Pattern 2: Coordinator (Orchestrator)

One agent coordinates, others execute:

```text
+---------------------------------------------------------------------------+
|                          COORDINATOR                                      |
+---------------------------------------------------------------------------+
|                                                                           |
|                      +------------------+                                 |
|                      |   ops/architect  |                                 |
|                      |   (coordinator)  |                                 |
|                      +--------+---------+                                 |
|                               |                                           |
|              +----------------+----------------+                          |
|              |                |                |                          |
|              v                v                v                          |
|   +------------------+ +------------------+ +------------------+          |
|   | release-manager  | | deploy-validator | | rollback-advisor |          |
|   |    (worker)      | |    (worker)      | |    (worker)      |          |
|   +------------------+ +------------------+ +------------------+          |
|                                                                           |
|   Coordinator:                                                            |
|   1. Receives task                                                        |
|   2. Decomposes into subtasks                                             |
|   3. Assigns to workers                                                   |
|   4. Aggregates results                                                   |
|   5. Makes final decision                                                 |
|                                                                           |
+---------------------------------------------------------------------------+
```

### Pattern 3: Event-Driven (Pub/Sub)

Agents communicate via events:

```text
+---------------------------------------------------------------------------+
|                         EVENT BUS                                         |
+---------------------------------------------------------------------------+
|                                                                           |
|   +-------------------------------------------------------------------+   |
|   |                      MESSAGE BUS                                  |   |
|   |                                                                   |   |
|   |  Topics:                                                          |   |
|   |  - agent.task.assigned                                            |   |
|   |  - agent.finding.reported                                         |   |
|   |  - agent.action.proposed                                          |   |
|   |  - agent.action.completed                                         |   |
|   |  - agent.error.occurred                                           |   |
|   +-------------------------------------------------------------------+   |
|        |              |              |              |                     |
|        | subscribe    | subscribe    | subscribe    | publish             |
|        v              v              v              v                     |
|   +---------+   +---------+   +---------+   +---------+                   |
|   | Agent A |   | Agent B |   | Agent C |   | Agent D |                   |
|   |         |   |         |   |         |   |         |                   |
|   | listens |   | listens |   | listens |   | publishes|                  |
|   | to:     |   | to:     |   | to:     |   | findings |                  |
|   | tasks   |   | findings|   | actions |   |         |                   |
|   +---------+   +---------+   +---------+   +---------+                   |
|                                                                           |
+---------------------------------------------------------------------------+
```

## Implementation

### Shared State Store

Use Redis or PostgreSQL for coordination state:

```yaml
# Redis-based coordination
coordination:
  backend: redis
  url: ${REDIS_URL}
  key_prefix: "agent:swarm:"

  # State structure
  keys:
    context: "agent:swarm:{session}:context"
    findings: "agent:swarm:{session}:findings"
    tasks: "agent:swarm:{session}:tasks"
    locks: "agent:swarm:{session}:locks"
```

```sql
-- PostgreSQL-based coordination
CREATE TABLE agent_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMP DEFAULT NOW(),
  context JSONB NOT NULL,
  status VARCHAR(50) DEFAULT 'active'
);

CREATE TABLE agent_findings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES agent_sessions(id),
  agent_id VARCHAR(100) NOT NULL,
  finding_type VARCHAR(50) NOT NULL,
  content JSONB NOT NULL,
  confidence FLOAT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE agent_tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES agent_sessions(id),
  assigned_to VARCHAR(100),
  task_type VARCHAR(50) NOT NULL,
  parameters JSONB,
  status VARCHAR(50) DEFAULT 'pending',
  result JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  completed_at TIMESTAMP
);
```

### Task Queue

Distribute work across agents:

```yaml
# Task queue schema
task:
  id: uuid
  type: "investigate" | "analyze" | "remediate" | "report"
  priority: 1-10
  assigned_to: agent_id | null
  parameters:
    target: string
    context: object
  constraints:
    timeout: duration
    requires_approval: boolean
  status: pending | assigned | running | completed | failed
  result: object | null
```

### Lock Management

Prevent conflicts when agents work on same resources:

```python
# Distributed locking pattern
class AgentLock:
    def __init__(self, redis_client, resource_id, agent_id):
        self.redis = redis_client
        self.resource_id = resource_id
        self.agent_id = agent_id
        self.lock_key = f"agent:lock:{resource_id}"

    def acquire(self, timeout=30):
        """Acquire lock with timeout."""
        return self.redis.set(
            self.lock_key,
            self.agent_id,
            nx=True,  # Only if not exists
            ex=timeout  # Auto-expire
        )

    def release(self):
        """Release lock if we own it."""
        # Lua script for atomic check-and-delete
        script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        return self.redis.eval(script, 1, self.lock_key, self.agent_id)

# Usage
lock = AgentLock(redis, "file:/src/main.py", "ops/release-manager")
if lock.acquire():
    try:
        # Modify file
        pass
    finally:
        lock.release()
else:
    # Another agent is working on this
    pass
```

## Communication Protocol

### Message Format

```yaml
# Standard agent message
message:
  id: uuid
  timestamp: iso8601
  source:
    agent: "ops/release-manager"
    session: uuid
  type: "finding" | "action" | "request" | "response"

  # For findings
  finding:
    category: "observation" | "hypothesis" | "conclusion"
    content: string
    confidence: 0.0-1.0
    evidence:
      - source: "prometheus"
        query: "rate(errors[5m])"
        result: "0.05"

  # For actions
  action:
    type: "query" | "modify" | "notify" | "escalate"
    target: string
    parameters: object
    requires_approval: boolean

  # For requests
  request:
    to: agent_id | "any"
    capability: "analyze_logs" | "query_metrics" | "check_deployment"
    parameters: object

  # For responses
  response:
    request_id: uuid
    status: "success" | "failure"
    result: object
```

### Event Types

```yaml
events:
  # Lifecycle events
  session.started:
    session_id: uuid
    initiator: agent_id
    context: object

  session.completed:
    session_id: uuid
    outcome: object

  # Work events
  task.created:
    task_id: uuid
    type: string
    parameters: object

  task.assigned:
    task_id: uuid
    agent_id: string

  task.completed:
    task_id: uuid
    result: object

  # Knowledge events
  finding.reported:
    finding_id: uuid
    agent_id: string
    category: string
    content: object

  hypothesis.proposed:
    hypothesis_id: uuid
    agent_id: string
    description: string
    confidence: float

  hypothesis.validated:
    hypothesis_id: uuid
    validated_by: agent_id
    result: boolean
    evidence: object
```

## Consensus Patterns

### Voting

Multiple agents vote on decisions:

```yaml
consensus:
  type: voting
  quorum: majority | unanimous | threshold
  threshold: 0.7  # If threshold type
  timeout: 5m

  # Example: Should we rollback?
  proposal:
    action: rollback
    version: v1.2.3

  votes:
    - agent: ops/deploy-validator
      vote: yes
      confidence: 0.9
      reason: "Error rate 5x baseline"

    - agent: ops/rollback-advisor
      vote: yes
      confidence: 0.85
      reason: "Matches previous incident pattern"

    - agent: security/incident-response-lead
      vote: abstain
      reason: "No security implications detected"

  result:
    decision: rollback
    votes_for: 2
    votes_against: 0
    abstentions: 1
```

### Confidence Aggregation

Combine agent confidence scores:

```python
def aggregate_confidence(findings: list[Finding]) -> float:
    """
    Aggregate confidence from multiple agent findings.
    Uses weighted average based on agent expertise and evidence strength.
    """
    if not findings:
        return 0.0

    weighted_sum = 0.0
    weight_total = 0.0

    for finding in findings:
        # Weight by agent expertise in this domain
        expertise_weight = get_agent_expertise(finding.agent, finding.category)

        # Weight by evidence strength
        evidence_weight = len(finding.evidence) * 0.1 + 0.5

        weight = expertise_weight * evidence_weight
        weighted_sum += finding.confidence * weight
        weight_total += weight

    return weighted_sum / weight_total if weight_total > 0 else 0.0
```

## Swarm Behaviors

### Parallel Investigation

Multiple agents investigate simultaneously:

```yaml
swarm:
  type: parallel_investigation

  task: "Investigate incident INC-1234"

  agents:
    - ops/deploy-validator:
        focus: "Check recent deployments and changes"

    - security/incident-response-lead:
        focus: "Analyze error patterns and logs"

    - ops/rollback-advisor:
        focus: "Assess rollback feasibility"

  coordination:
    share_findings: true
    avoid_duplicate_queries: true
    timeout: 10m

  synthesis:
    agent: ops/architect
    action: "Combine findings and recommend action"
```

### Progressive Refinement

Agents build on each other's work:

```yaml
swarm:
  type: progressive_refinement

  stages:
    - stage: 1
      agent: ops/deploy-validator
      task: "Identify recent changes"
      output: changes_list

    - stage: 2
      agent: security/incident-response-lead
      task: "Correlate changes with errors"
      input: changes_list
      output: correlation_report

    - stage: 3
      agent: ops/rollback-advisor
      task: "Recommend action based on correlation"
      input: correlation_report
      output: recommendation
```

## MCP Server for Coordination

```json
{
  "mcpServers": {
    "agent-swarm": {
      "command": "mcp-agent-swarm",
      "env": {
        "SWARM_BACKEND": "redis",
        "REDIS_URL": "${REDIS_URL}",
        "AGENT_ID": "${AGENT_ID}"
      }
    }
  }
}
```

**Capabilities:**

- `swarm.join_session` - Join a coordination session
- `swarm.post_finding` - Share a finding
- `swarm.get_findings` - Read others' findings
- `swarm.claim_task` - Claim a task
- `swarm.complete_task` - Mark task complete
- `swarm.propose_action` - Propose action for voting
- `swarm.vote` - Vote on proposal
