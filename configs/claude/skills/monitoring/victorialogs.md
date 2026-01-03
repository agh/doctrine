# VictoriaLogs Skill

Provides log query access for debugging, incident investigation, and pattern
analysis using LogsQL.

## Overview

| Attribute | Value |
| --------- | ----- |
| **Category** | Monitoring / Logs |
| **Protocol** | HTTP API |
| **Query Language** | LogsQL |
| **Default Access** | readonly |
| **Risk Level** | Low-Medium (may contain sensitive data) |

## Configuration

### Direct API Access

```bash
# VictoriaLogs URL
VICTORIALOGS_URL="http://victorialogs:9428"

# Query logs
curl -G "${VICTORIALOGS_URL}/select/logsql/query" \
  --data-urlencode "query=error AND service:api" \
  --data-urlencode "limit=100"
```

### Environment Variables

```bash
export VICTORIALOGS_URL="http://victorialogs:9428"
export VICTORIALOGS_AUTH=""  # If authentication required
```

## LogsQL Query Patterns

### Basic Queries

```logsql
# Find all error logs
error

# Find errors in specific service
error AND service:api

# Find by log level
level:error

# Find by multiple fields
level:error AND service:api AND environment:production

# Exclude patterns
error AND NOT "health check"
```

### Time-Based Queries

```logsql
# Last hour (default)
error

# Specific time range (use HTTP params)
# start=2025-01-02T09:00:00Z&end=2025-01-02T10:00:00Z

# Relative time in query
_time:1h  # Last hour
_time:15m # Last 15 minutes
```

### Field Queries

```logsql
# Exact match
service:api

# Prefix match
service:api*

# Regex match
service:~"api-v[0-9]+"

# Numeric comparison
status:>400
latency_ms:>1000
```

### Text Search

```logsql
# Contains word
error

# Contains phrase
"connection refused"

# Wildcard
"timeout*"

# Case insensitive
i(error)
```

### Aggregations

```logsql
# Count by field
error | stats count() by service

# Count by time bucket
error | stats by (_time:1h) count()

# Multiple aggregations
* | stats count(), avg(latency_ms), max(latency_ms) by service
```

## Query Patterns for Agents

### Error Investigation

```logsql
# Find errors around incident time
level:error AND _time:[2025-01-02T10:00:00Z, 2025-01-02T10:30:00Z]

# Find stack traces
"Exception" OR "Traceback" OR "panic:"

# Find errors by request ID
request_id:abc123

# Find errors with context
level:error | fields service, message, stack_trace
```

### Deployment Correlation

```logsql
# Errors after deployment
level:error AND _time:30m
| stats count() by (_time:5m)

# New error patterns (not seen before)
level:error AND NOT message:~"known-error-pattern"

# First occurrence of error
level:error | sort by (_time) | limit 1
```

### Performance Analysis

```logsql
# Slow requests
latency_ms:>1000

# Slow requests by endpoint
latency_ms:>1000 | stats count(), avg(latency_ms) by endpoint

# Latency percentiles
* | stats quantile(0.95, latency_ms) by service
```

### Security Investigation

```logsql
# Authentication failures
"authentication failed" OR "invalid token" OR "unauthorized"

# Suspicious patterns
"SQL" AND ("OR 1=1" OR "DROP" OR "UNION")

# Rate limiting triggers
"rate limit" OR "too many requests"

# Access from unusual IPs
NOT client_ip:~"10\\..*" AND NOT client_ip:~"192\\.168\\..*"
```

### Service Dependencies

```logsql
# Downstream failures
"connection refused" OR "timeout" OR "ECONNRESET"

# Database issues
service:api AND ("database" OR "postgres" OR "connection pool")

# External API failures
"external" AND (level:error OR status:>400)
```

## Example Usage

### Incident Triage

```markdown
When investigating incident at 10:30 UTC:

1. Find error spike:
   level:error AND _time:[10:00, 11:00] | stats count() by (_time:5m)

2. Identify affected services:
   level:error AND _time:[10:25, 10:35] | stats count() by service

3. Find root cause:
   level:error AND _time:[10:25, 10:35] | sort by (_time) | limit 50

4. Check for correlating events:
   ("deploy" OR "restart" OR "config change") AND _time:[10:00, 10:30]
```

### Pre-Deploy Baseline

```markdown
Capture error patterns before deployment:

1. Current error rate:
   level:error AND _time:1h | stats count()

2. Error types:
   level:error AND _time:1h | stats count() by message | limit 20

3. Known error patterns (to filter post-deploy):
   level:error AND _time:24h | stats count() by message | sort by count desc
```

### Post-Deploy Validation

```markdown
Compare post-deploy to baseline:

1. New error count:
   level:error AND _time:15m | stats count()

2. New error types (not in baseline):
   level:error AND _time:15m AND NOT message:~"known-pattern"

3. Error rate trend:
   level:error AND _time:1h | stats count() by (_time:5m)
```

## Agents That Use This Skill

| Agent | Access | Purpose |
| ----- | ------ | ------- |
| `ops/deploy-validator` | readonly | Post-deploy error detection |
| `ops/rollback-advisor` | readonly | Incident log analysis |
| `security/incident-response-lead` | readonly | Security investigation |
| `code/reviewer` | readonly | Debug failing tests |

## Graceful Degradation

| If Missing | Fallback |
| ---------- | -------- |
| VictoriaLogs unavailable | Use application logs directly (kubectl logs) |
| Specific logs missing | Widen time range or service scope |
| Query timeout | Reduce time range, add filters |

## Security Considerations

### Sensitive Data

Logs often contain sensitive information:

- **MUST** filter PII before agent access where possible
- **SHOULD** use field-level access controls if available
- **MUST NOT** log query results containing credentials
- **SHOULD** mask sensitive patterns in agent output

```logsql
# Avoid queries that might return secrets
# BAD: * | fields *
# GOOD: level:error | fields service, message, timestamp
```

### Access Control

```yaml
# Recommended: Separate log streams
production-logs:   # Agents get readonly
  retention: 30d
  access: [ops-agents]

security-logs:     # Restricted access
  retention: 90d
  access: [security-team]

audit-logs:        # Agent actions logged here
  retention: 365d
  access: [compliance-team]
```

### Query Limits

```yaml
# VictoriaLogs query limits
-search.maxQueryDuration=30s
-search.maxConcurrentRequests=10
-search.maxLines=10000
```

## CLI Access Pattern

```bash
#!/bin/bash
# victorialogs-query.sh - Wrapper for agent use

VICTORIALOGS_URL="${VICTORIALOGS_URL:-http://localhost:9428}"

query_logs() {
  local logsql="$1"
  local limit="${2:-100}"
  local start="${3:-$(date -d '1 hour ago' -Iseconds)}"
  local end="${4:-$(date -Iseconds)}"

  curl -s -G "${VICTORIALOGS_URL}/select/logsql/query" \
    --data-urlencode "query=${logsql}" \
    --data-urlencode "limit=${limit}" \
    --data-urlencode "start=${start}" \
    --data-urlencode "end=${end}"
}

# Count errors by service in last hour
count_errors() {
  query_logs 'level:error | stats count() by service'
}

# Find errors around timestamp
errors_around() {
  local timestamp="$1"
  local window="${2:-5m}"
  query_logs "level:error AND _time:${window}" 100 \
    "$(date -d "${timestamp} - ${window}" -Iseconds)" \
    "$(date -d "${timestamp} + ${window}" -Iseconds)"
}

# Usage
query_logs 'level:error AND service:api'
count_errors
errors_around "2025-01-02T10:30:00Z" "10m"
```

## Integration with Prometheus

Cross-reference logs with metrics:

```markdown
1. Detect anomaly in metrics:
   Prometheus: rate(http_requests_total{status=~"5.."}[5m]) > 0.01

2. Find corresponding logs:
   VictoriaLogs: level:error AND _time:5m AND service:api

3. Correlate by request ID:
   VictoriaLogs: request_id:<id-from-trace>
```
