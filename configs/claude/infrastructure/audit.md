# Agent Audit Logging

Comprehensive logging of all agent actions for compliance, debugging, and
learning.

## Overview

Every agent action **MUST** be logged:

```text
+---------------------------------------------------------------------------+
|                          AUDIT LOGGING                                    |
+---------------------------------------------------------------------------+
|                                                                           |
|   WHAT TO LOG                                                             |
|   -----------                                                             |
|   - Tool invocations (read, write, bash, etc.)                            |
|   - Skill usage (postgres queries, github API calls)                      |
|   - External calls (web search, web fetch)                                |
|   - Decisions made (why agent chose action X)                             |
|   - Outcomes (did action succeed, what was result)                        |
|   - Errors (what failed, why)                                             |
|                                                                           |
|   WHY LOG                                                                 |
|   -------                                                                 |
|   - Compliance & audit trails                                             |
|   - Debugging agent behavior                                              |
|   - Learning from outcomes (train better agents)                          |
|   - Cost tracking (API calls, tokens used)                                |
|   - Security monitoring (detect anomalies)                                |
|                                                                           |
+---------------------------------------------------------------------------+
```

## Log Schema

### Standard Log Entry

```yaml
log_entry:
  # Identity
  id: uuid
  timestamp: iso8601

  # Agent context
  agent:
    id: "ops/release-manager"
    session_id: uuid
    conversation_id: uuid  # Links to user conversation

  # Action details
  action:
    type: "tool" | "skill" | "external" | "decision" | "error"
    name: string

    # For tool invocations
    tool:
      name: "Bash" | "Read" | "Write" | "Edit" | "Grep" | etc.
      parameters:
        # Tool-specific parameters

    # For skill usage
    skill:
      name: "postgres" | "github" | "discord" | etc.
      operation: string
      parameters:
        # Skill-specific parameters

    # For external calls
    external:
      type: "web_search" | "web_fetch" | "api_call"
      target: url | query
      parameters:
        # Call-specific parameters

    # For decisions
    decision:
      question: string
      options_considered:
        - option: string
          reasoning: string
          score: float
      chosen: string
      confidence: float

  # Outcome
  outcome:
    status: "success" | "failure" | "partial"
    result:
      # Summarized result (not full content for privacy)
    error:
      type: string
      message: string

  # Resource usage
  resources:
    tokens_input: int
    tokens_output: int
    duration_ms: int
    cost_usd: float  # Estimated

  # Security context
  security:
    permission_level: "readonly" | "read-write" | "admin"
    resources_accessed:
      - type: string
        identifier: string
    sensitive_data_accessed: boolean
```

### Examples

#### Tool Invocation

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-01-02T10:30:15.123Z",
  "agent": {
    "id": "ops/release-manager",
    "session_id": "abc123",
    "conversation_id": "user-conv-456"
  },
  "action": {
    "type": "tool",
    "name": "Bash",
    "tool": {
      "name": "Bash",
      "parameters": {
        "command": "git log --oneline -10",
        "description": "List recent commits"
      }
    }
  },
  "outcome": {
    "status": "success",
    "result": {
      "exit_code": 0,
      "output_lines": 10,
      "output_preview": "abc123 feat: add user profile..."
    }
  },
  "resources": {
    "duration_ms": 234
  },
  "security": {
    "permission_level": "readonly",
    "resources_accessed": [
      {"type": "git_repository", "identifier": "/path/to/repo"}
    ]
  }
}
```

#### Skill Usage

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "timestamp": "2025-01-02T10:30:20.456Z",
  "agent": {
    "id": "ops/release-manager",
    "session_id": "abc123",
    "conversation_id": "user-conv-456"
  },
  "action": {
    "type": "skill",
    "name": "postgres",
    "skill": {
      "name": "postgres",
      "operation": "query",
      "parameters": {
        "query_hash": "sha256:abc123...",
        "query_preview": "SELECT version, deployed_at FROM deployments...",
        "tables_accessed": ["deployments"]
      }
    }
  },
  "outcome": {
    "status": "success",
    "result": {
      "rows_returned": 10,
      "execution_time_ms": 45
    }
  },
  "resources": {
    "duration_ms": 52
  },
  "security": {
    "permission_level": "readonly",
    "resources_accessed": [
      {"type": "database_table", "identifier": "public.deployments"}
    ],
    "sensitive_data_accessed": false
  }
}
```

#### Web Search

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "timestamp": "2025-01-02T10:30:25.789Z",
  "agent": {
    "id": "ops/release-manager",
    "session_id": "abc123",
    "conversation_id": "user-conv-456"
  },
  "action": {
    "type": "external",
    "name": "web_search",
    "external": {
      "type": "web_search",
      "target": "kubernetes pod restart loop causes",
      "parameters": {
        "result_count": 10
      }
    }
  },
  "outcome": {
    "status": "success",
    "result": {
      "results_returned": 10,
      "domains": ["kubernetes.io", "stackoverflow.com", "github.com"]
    }
  },
  "resources": {
    "duration_ms": 1234,
    "cost_usd": 0.001
  },
  "security": {
    "permission_level": "readonly"
  }
}
```

#### Decision

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "timestamp": "2025-01-02T10:31:00.000Z",
  "agent": {
    "id": "ops/rollback-advisor",
    "session_id": "abc123",
    "conversation_id": "user-conv-456"
  },
  "action": {
    "type": "decision",
    "name": "rollback_recommendation",
    "decision": {
      "question": "Should we rollback deployment v1.2.3?",
      "options_considered": [
        {
          "option": "rollback",
          "reasoning": "Error rate 5x baseline, affecting 15% of users",
          "score": 0.85
        },
        {
          "option": "hotfix",
          "reasoning": "Root cause identified, fix is simple",
          "score": 0.60
        },
        {
          "option": "monitor",
          "reasoning": "Errors may be transient",
          "score": 0.20
        }
      ],
      "chosen": "rollback",
      "confidence": 0.85
    }
  },
  "outcome": {
    "status": "success",
    "result": {
      "recommendation": "rollback",
      "awaiting_approval": true
    }
  }
}
```

## Log Destinations

### Local File (Development)

```yaml
audit:
  destination: file
  path: /var/log/agent-audit/
  rotation:
    max_size: 100MB
    max_age: 30d
    compress: true
```

### VictoriaLogs (Production)

```yaml
audit:
  destination: victorialogs
  url: ${VICTORIALOGS_URL}
  stream: agent-audit

  # Structured logging
  format: json

  # Add standard labels
  labels:
    environment: production
    cluster: main
```

### PostgreSQL (Queryable)

```sql
CREATE TABLE agent_audit_log (
  id UUID NOT NULL DEFAULT gen_random_uuid(),
  timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  -- Agent identity
  agent_id VARCHAR(100) NOT NULL,
  session_id UUID,
  conversation_id UUID,

  -- Action
  action_type VARCHAR(50) NOT NULL,
  action_name VARCHAR(100) NOT NULL,
  action_details JSONB NOT NULL,

  -- Outcome
  outcome_status VARCHAR(20) NOT NULL,
  outcome_result JSONB,
  outcome_error JSONB,

  -- Resources
  tokens_input INT,
  tokens_output INT,
  duration_ms INT,
  cost_usd DECIMAL(10, 6),

  -- Security
  permission_level VARCHAR(20),
  resources_accessed JSONB,
  sensitive_data_accessed BOOLEAN NOT NULL DEFAULT FALSE,

  -- A unique constraint on a partitioned table MUST contain every
  -- partition-key column, so the key is (id, timestamp), not id alone
  PRIMARY KEY (id, timestamp)
) PARTITION BY RANGE (timestamp);

-- Indexes are separate statements in PostgreSQL. Created on the partitioned
-- parent, they propagate to every current and future partition.
CREATE INDEX agent_audit_log_agent_id_idx ON agent_audit_log (agent_id);
CREATE INDEX agent_audit_log_timestamp_idx ON agent_audit_log (timestamp DESC);
CREATE INDEX agent_audit_log_action_type_idx ON agent_audit_log (action_type);
CREATE INDEX agent_audit_log_session_id_idx ON agent_audit_log (session_id);

-- Partition by month for retention
CREATE TABLE agent_audit_log_2026_09 PARTITION OF agent_audit_log
  FOR VALUES FROM ('2026-09-01') TO ('2026-10-01');

-- A default partition keeps an out-of-range insert from being rejected
CREATE TABLE agent_audit_log_default PARTITION OF agent_audit_log DEFAULT;
```

Agents **MUST NOT** apply audit DDL straight to production. Apply it to a
disposable database first, on the PostgreSQL version you run:

```bash
docker run -d --name audit-schema-test -e POSTGRES_PASSWORD=test postgres:18
docker exec -i audit-schema-test psql -U postgres -v ON_ERROR_STOP=1 \
  < audit-schema.sql
docker rm -f audit-schema-test
```

**Why**: MySQL-style inline `INDEX` clauses are not valid PostgreSQL, a
`PARTITION OF` clause needs a parent declared `PARTITION BY`, and PostgreSQL
rejects a primary key that omits a partition-key column. All three fail at
`CREATE TABLE` time, so a migration test catches them before deployment.

## Querying Audit Logs

### Recent Activity by Agent

```sql
SELECT
  action_type,
  action_name,
  outcome_status,
  timestamp
FROM agent_audit_log
WHERE agent_id = 'ops/release-manager'
  AND timestamp > NOW() - INTERVAL '1 hour'
ORDER BY timestamp DESC;
```

### Failed Actions

```sql
SELECT
  agent_id,
  action_name,
  outcome_error,
  timestamp
FROM agent_audit_log
WHERE outcome_status = 'failure'
  AND timestamp > NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC;
```

### Cost Analysis

```sql
SELECT
  agent_id,
  DATE_TRUNC('day', timestamp) as day,
  SUM(cost_usd) as total_cost,
  SUM(tokens_input + tokens_output) as total_tokens,
  COUNT(*) as action_count
FROM agent_audit_log
WHERE timestamp > NOW() - INTERVAL '30 days'
GROUP BY agent_id, DATE_TRUNC('day', timestamp)
ORDER BY day DESC, total_cost DESC;
```

### Security Audit

```sql
SELECT
  agent_id,
  action_name,
  resources_accessed,
  timestamp
FROM agent_audit_log
WHERE sensitive_data_accessed = TRUE
  AND timestamp > NOW() - INTERVAL '7 days'
ORDER BY timestamp DESC;
```

### Learning: Action Outcomes

```sql
-- Which actions succeed vs fail?
SELECT
  agent_id,
  action_name,
  COUNT(*) as total,
  COUNT(*) FILTER (WHERE outcome_status = 'success') as successes,
  ROUND(
    100.0 * COUNT(*) FILTER (WHERE outcome_status = 'success') / COUNT(*),
    1
  ) as success_rate
FROM agent_audit_log
WHERE timestamp > NOW() - INTERVAL '30 days'
GROUP BY agent_id, action_name
HAVING COUNT(*) > 10
ORDER BY success_rate ASC;
```

## Integration with Claude Code

### Hook-Based Logging

Claude Code fires `PostToolUse` after a tool succeeds and `PostToolUseFailure`
after a tool fails. Both take an array of matcher groups; each group holds an
array of handlers. Register the same logger on both events:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/agent-audit-log",
            "args": [],
            "timeout": 5
          }
        ]
      }
    ],
    "PostToolUseFailure": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/agent-audit-log",
            "args": [],
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

**Why**: `PostToolCall` is not a Claude Code event, and an object where an
array is expected is discarded, so the hook never runs. `timeout` is in
seconds, not milliseconds. Setting `args` selects exec form, which substitutes
`${CLAUDE_PROJECT_DIR}` into `command` without shell quoting.

The handler reads one JSON object on stdin. `PostToolUse` supplies
`tool_response`; `PostToolUseFailure` supplies `error` instead, so the outcome
**MUST** be derived from `hook_event_name` rather than hard-coded:

```bash
#!/usr/bin/env bash
# agent-audit-log - PostToolUse / PostToolUseFailure hook
set -euo pipefail

EVENT=$(cat)

case "$(jq -r '.hook_event_name' <<<"$EVENT")" in
  PostToolUse)        STATUS=success ;;
  PostToolUseFailure) STATUS=failure ;;
  *)                  exit 0 ;;
esac

# Fields absent from an event serialise as null, not as missing keys
jq -c --arg status "$STATUS" '{
  timestamp: (now | todate),
  agent: {
    session_id: .session_id,
    cwd: .cwd,
    permission_mode: .permission_mode
  },
  action: {
    type: "tool",
    name: .tool_name,
    tool_use_id: .tool_use_id,
    input: .tool_input
  },
  outcome: {
    status: $status,
    duration_ms: .duration_ms,
    result: .tool_response,
    error: .error
  }
}' <<<"$EVENT" |
  curl -sS --fail-with-body -X POST "${AUDIT_LOG_URL}/log" \
    -H "Content-Type: application/json" \
    --data-binary @-
```

A failed POST leaves the script with a non-zero status, which Claude Code
reports as a non-blocking hook error in the transcript instead of silently
dropping the audit record. Only exit code 2 blocks, and a `PostToolUse` hook
**MUST NOT** exit 2 for a logging failure: the tool has already run.

### Validating Hook Configuration in CI

`claude doctor` reports rejected settings but still exits 0, so CI **MUST**
fail on the report text rather than on the exit status:

```bash
#!/usr/bin/env bash
# ci-check-claude-settings - fail the build on settings Claude Code rejects
set -euo pipefail

report=$(claude doctor 2>&1)
printf '%s\n' "$report"

if printf '%s\n' "$report" | grep -q '^Invalid settings'; then
  echo "Claude Code rejected part of the settings above" >&2
  exit 1
fi
```

### MCP Server for Audit

```json
{
  "mcpServers": {
    "audit": {
      "command": "mcp-audit-logger",
      "env": {
        "AUDIT_BACKEND": "postgres",
        "AUDIT_DATABASE_URL": "${AUDIT_DATABASE_URL}",
        "AGENT_ID": "${AGENT_ID}"
      }
    }
  }
}
```

## Privacy Considerations

### Data Minimization

```yaml
audit:
  # Don't log full content, just metadata
  content_logging:
    file_contents: false  # Log file path, not contents
    query_results: false  # Log row count, not data
    bash_output: truncate # First 500 chars only

  # Redact sensitive patterns
  redaction:
    patterns:
      - "password[=:]\\S+"
      - "api[_-]?key[=:]\\S+"
      - "secret[=:]\\S+"
      - "token[=:]\\S+"
    replacement: "[REDACTED]"
```

### Retention Policy

```yaml
audit:
  retention:
    hot: 7d      # Full detail, fast queries
    warm: 30d    # Aggregated, slower queries
    cold: 365d   # Archived, compliance only

  # Auto-delete PII after period
  pii_retention: 30d
```

## Alerting on Audit Events

```yaml
alerts:
  # Alert on sensitive data access
  - name: sensitive_data_accessed
    condition: |
      agent_audit_log
      | sensitive_data_accessed = true
      | count() > 0
    window: 5m
    action: notify_security

  # Alert on high failure rate
  - name: agent_failure_spike
    condition: |
      agent_audit_log
      | outcome_status = 'failure'
      | count() by agent_id
      | count > 10
    window: 15m
    action: notify_ops

  # Alert on unusual activity
  - name: unusual_agent_activity
    condition: |
      agent_audit_log
      | count() by agent_id
      | count > avg(count) * 3
    window: 1h
    action: notify_security
```
