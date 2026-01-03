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
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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
  sensitive_data_accessed BOOLEAN DEFAULT FALSE,

  -- Indexes
  INDEX idx_agent_id (agent_id),
  INDEX idx_timestamp (timestamp),
  INDEX idx_action_type (action_type),
  INDEX idx_session_id (session_id)
);

-- Partition by month for retention
CREATE TABLE agent_audit_log_2025_01 PARTITION OF agent_audit_log
  FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
```

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

Use Claude Code hooks to capture actions:

```json
{
  "hooks": {
    "PostToolCall": {
      "command": "agent-audit-log",
      "timeout": 5000
    }
  }
}
```

```bash
#!/bin/bash
# agent-audit-log - Hook to log tool calls

# Receive tool call details from stdin
TOOL_CALL=$(cat)

# Extract relevant fields
TOOL_NAME=$(echo "$TOOL_CALL" | jq -r '.tool_name')
PARAMETERS=$(echo "$TOOL_CALL" | jq -c '.parameters')
RESULT=$(echo "$TOOL_CALL" | jq -c '.result')

# Log to audit destination
curl -X POST "${AUDIT_LOG_URL}/log" \
  -H "Content-Type: application/json" \
  -d @- <<EOF
{
  "timestamp": "$(date -Iseconds)",
  "agent": {
    "id": "${AGENT_ID}",
    "session_id": "${SESSION_ID}"
  },
  "action": {
    "type": "tool",
    "name": "${TOOL_NAME}",
    "tool": {
      "name": "${TOOL_NAME}",
      "parameters": ${PARAMETERS}
    }
  },
  "outcome": {
    "status": "success",
    "result": ${RESULT}
  }
}
EOF
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
