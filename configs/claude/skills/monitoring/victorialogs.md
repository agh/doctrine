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

# Query logs. Bound by time and use := for whole-field identity.
curl -sS --fail-with-body -G "${VICTORIALOGS_URL}/select/logsql/query" \
  --data-urlencode "query=_time:1h AND error AND service:=api" \
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
# Find all error logs in the last hour
_time:1h AND error

# Find errors in one specific service (exact field match)
_time:1h AND error AND service:=api

# Find by log level
_time:1h AND level:=error

# Find by multiple fields
_time:1h AND level:=error AND service:=api AND environment:=production

# Exclude patterns
_time:1h AND error AND NOT "health check"
```

### Time-Based Queries

There is no implicit default window. A query with no `_time` filter and no
`start`/`end` request parameters selects across the whole retention period, so
an "error count" taken that way is not the count for the last hour.

Every operational query **MUST** be bounded, by one of these two mechanisms —
not both, because mixing them makes the selected range depend on how the
relative filter is anchored:

```logsql
# 1. Bound in the query
_time:1h AND level:error
_time:15m AND level:error

# 2. Bound with request parameters, leaving _time out of the query
#    start=2026-09-08T09:00:00Z&end=2026-09-08T10:00:00Z
level:error
```

Absolute ranges **MUST** carry a full date. A bare clock range is rejected:

```logsql
# Don't: HTTP 400, "cannot parse start time in _time filter"
level:error AND _time:[10:00, 11:00]

# Do
level:error AND _time:[2026-09-08T10:00:00Z, 2026-09-08T11:00:00Z]
```

Operators **SHOULD** enforce a server-side ceiling so an unbounded query
cannot scan everything:

```bash
victoria-logs -search.maxQueryTimeRange=24h -search.maxQueryDuration=30s
```

`-search.maxLines` does not exist; passing it stops the server from starting
with `flag provided but not defined: -search.maxLines`. Use `| limit N` in the
query to cap returned rows.

**Why**: an unbounded LogsQL query is not an error. It returns results, they
just describe a different period from the one the operator had in mind, and
nothing in the response says so.

### Field Queries

```logsql
# Word filter: matches any field value CONTAINING the word `api`,
# including `prod-api` and `api-gateway`
service:api

# Exact filter: matches only the whole value `api`
service:=api

# Prefix match
service:api*

# Regex match
service:~"api-v[0-9]+"

# Numeric comparison
status:>400
latency_ms:>1000
```

Identity comparisons — service names, environments, hostnames, request IDs —
**MUST** use `:=`. With one `prod-api` row alongside six `api` rows,
`service:api` returned 7 rows and `service:=api` returned 6. The same applies
to `environment:production`, which also matches `pre-production`.

### Text Search

```logsql
# Contains word
error

# Contains phrase
"connection refused"

# Prefix wildcard: the * MUST be outside the quotes
timeout*

# Case insensitive
i(error)
```

Quoting the wildcard turns it into a literal character. `"timeout*"` searches
for the phrase `timeout*` and returned 0 rows against logs containing
`timeout` and `timeouts`; the unquoted `timeout*` returned 3.

### Aggregations

`stats` takes its grouping **before** the functions:

```logsql
# Count by field
error | stats by (service) count()

# Named output, so later pipes can refer to it
error | stats by (service) count() as errors

# Count by time bucket
error | stats by (_time:1h) count() as n

# Multiple aggregations
* | stats by (service) count() as n, avg(latency_ms) as avg_ms,
      max(latency_ms) as max_ms
```

`stats count() by service` is rejected with HTTP 400,
`cannot parse "stats" pipe: unexpected token "service"`.

Sorting refers to the **output** field. An unnamed `count()` produces a field
literally called `count(*)`, so either alias it or quote the generated name,
and wrap the sort key in parentheses:

```logsql
# Don't: HTTP 400
* | stats by (service) count() | sort by count desc

# Do: alias it
* | stats by (service) count() as n | sort by (n desc)

# Also valid: quote the generated field name
* | stats by (service) count() | sort by ("count(*)" desc)
```

## Query Patterns for Agents

### Error Investigation

```logsql
# Find errors around incident time
level:=error AND _time:[2026-09-08T10:00:00Z, 2026-09-08T10:30:00Z]

# Find stack traces
_time:1h AND ("Exception" OR "Traceback" OR "panic:")

# Find errors by request ID
_time:24h AND request_id:=abc123

# Find errors with context
_time:1h AND level:=error | fields service, _msg, stack_trace
```

### Deployment Correlation

```logsql
# Errors after deployment
level:=error AND _time:30m
| stats by (_time:5m) count() as n

# New error patterns (not seen before)
_time:30m AND level:=error AND NOT _msg:~"known-error-pattern"

# First occurrence of error
level:=error AND _time:30m | sort by (_time) | limit 1
```

### Performance Analysis

```logsql
# Slow requests
_time:1h AND latency_ms:>1000

# Slow requests by endpoint
_time:1h AND latency_ms:>1000
| stats by (endpoint) count() as n, avg(latency_ms) as avg_ms

# Latency percentiles
_time:1h | stats by (service) quantile(0.95, latency_ms) as p95
```

### Security Investigation

```logsql
# Authentication failures
_time:1h AND ("authentication failed" OR "invalid token" OR "unauthorized")

# Suspicious patterns
_time:1h AND "SQL" AND ("OR 1=1" OR "DROP" OR "UNION")

# Rate limiting triggers
_time:1h AND ("rate limit" OR "too many requests")

# Access from unusual IPs
_time:1h AND NOT client_ip:~"10\\..*" AND NOT client_ip:~"192\\.168\\..*"
```

### Service Dependencies

```logsql
# Downstream failures
_time:1h AND ("connection refused" OR "timeout" OR "ECONNRESET")

# Database issues
_time:1h AND service:=api AND ("database" OR "postgres" OR "connection pool")

# External API failures
_time:1h AND "external" AND (level:=error OR status:>400)
```

## Example Usage

### Incident Triage

```markdown
When investigating an incident at 10:30 UTC on 2026-09-08:

1. Find error spike:
   level:=error AND _time:[2026-09-08T10:00:00Z, 2026-09-08T11:00:00Z]
   | stats by (_time:5m) count() as n

2. Identify affected services:
   level:=error AND _time:[2026-09-08T10:25:00Z, 2026-09-08T10:35:00Z]
   | stats by (service) count() as n | sort by (n desc)

3. Find root cause:
   level:=error AND _time:[2026-09-08T10:25:00Z, 2026-09-08T10:35:00Z]
   | sort by (_time) | limit 50

4. Check for correlating events:
   ("deploy" OR "restart" OR "config change")
   AND _time:[2026-09-08T10:00:00Z, 2026-09-08T10:30:00Z]
```

Absolute ranges are **REQUIRED** here. A relative `_time:10m` describes a
window relative to the query's end point, not the incident, so it silently
selects a different slice of the incident than intended.

### Pre-Deploy Baseline

```markdown
Capture error patterns before deployment:

1. Current error rate:
   level:=error AND _time:1h | stats count() as n

2. Error types:
   level:=error AND _time:1h
   | stats by (_msg) count() as n | sort by (n desc) | limit 20

3. Known error patterns (to filter post-deploy):
   level:=error AND _time:24h
   | stats by (_msg) count() as n | sort by (n desc)
```

### Post-Deploy Validation

```markdown
Compare post-deploy to baseline:

1. New error count:
   level:=error AND _time:15m | stats count() as n

2. New error types (not in baseline):
   level:=error AND _time:15m AND NOT _msg:~"known-pattern"

3. Error rate trend:
   level:=error AND _time:1h | stats by (_time:5m) count() as n
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
# GOOD: _time:1h AND level:=error | fields service, _msg, _time
```

### Access Control

VictoriaLogs itself does not authenticate or authorise queries. Enforce
separation with `vmauth` in front of it:

```yaml
# vmauth config: agents get read-only access to one tenant
users:
  - username: ops-agent
    password: "${OPS_AGENT_PASSWORD}"
    url_map:
      - src_paths: ["/select/logsql/query", "/select/logsql/hits"]
        url_prefix: "http://victorialogs:9428"
        headers:
          - "AccountID: 1"
          - "ProjectID: 1"
```

Only the `/select/...` paths are mapped, so the same credential cannot reach
`/insert/...` or the `/debug/pprof` handlers.

**Why**: VictoriaLogs has no built-in user model. Anything reachable on port
9428 can query every tenant and, on the insert paths, write to them. The
boundary has to be an external proxy.

```yaml
# Recommended: separate log streams by retention and audience
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

```bash
# VictoriaLogs server flags (verified against v1.52.0 --help)
victoria-logs \
  -search.maxQueryDuration=30s \
  -search.maxConcurrentRequests=10 \
  -search.maxQueryTimeRange=24h
```

`-search.maxLines` is not a VictoriaLogs flag. Starting the server with it
fails immediately:

```console
$ victoria-logs -search.maxLines=10000
flag provided but not defined: -search.maxLines
```

Cap returned rows with `| limit N` in the query, or the `limit` request
parameter, instead.

## CLI Access Pattern

```bash
#!/usr/bin/env bash
# victorialogs-query.sh - Wrapper for agent use
set -euo pipefail

VICTORIALOGS_URL="${VICTORIALOGS_URL:-http://localhost:9428}"

# GNU date and BSD date disagree on relative-time syntax, so compute
# timestamps with python3, which behaves the same everywhere.
# datetime.timezone.utc is used rather than datetime.UTC, which needs 3.11+.
iso_ago() {
  python3 -c "
import datetime as d, sys
now = d.datetime.now(d.timezone.utc)
print((now - d.timedelta(seconds=int(sys.argv[1])))
      .isoformat().replace('+00:00', 'Z'))" "$1"
}

iso_offset() {
  python3 -c "
import datetime as d, sys
t = d.datetime.fromisoformat(sys.argv[1].replace('Z', '+00:00'))
print((t + d.timedelta(seconds=int(sys.argv[2])))
      .isoformat().replace('+00:00', 'Z'))" "$1" "$2"
}

query_logs() {
  local logsql="$1"
  local limit="${2:-100}"
  local start="${3:-$(iso_ago 3600)}"
  local end="${4:-$(iso_ago 0)}"

  local auth=()
  if [ -n "${VICTORIALOGS_TOKEN:-}" ]; then
    auth=(-H "Authorization: Bearer ${VICTORIALOGS_TOKEN}")
  elif [ -n "${VICTORIALOGS_USER:-}" ]; then
    auth=(-u "${VICTORIALOGS_USER}:${VICTORIALOGS_PASSWORD:?password required}")
  fi

  local body rc
  # ${arr[@]+"${arr[@]}"} keeps an empty array from tripping `set -u`
  # on bash 3.2, which is what macOS ships.
  # `|| rc=$?` stops `set -e` killing the script before the body is shown.
  rc=0
  body=$(curl -sS --fail-with-body --max-time 60 -G \
    ${auth[@]+"${auth[@]}"} \
    "${VICTORIALOGS_URL}/select/logsql/query" \
    --data-urlencode "query=${logsql}" \
    --data-urlencode "limit=${limit}" \
    --data-urlencode "start=${start}" \
    --data-urlencode "end=${end}") || rc=$?

  if [ "$rc" -ne 0 ]; then
    printf 'victorialogs request failed (curl %s): %s\n' "$rc" "$body" >&2
    return "$rc"
  fi
  printf '%s\n' "$body"
}

# Count errors by service in last hour
count_errors() {
  query_logs 'level:=error | stats by (service) count() as n | sort by (n desc)'
}

# Find errors around a timestamp. The window is expressed once, through
# start/end; adding a relative _time filter as well would re-bound the
# range a second time and select a different slice.
errors_around() {
  local timestamp="$1"
  local seconds="${2:-300}"
  query_logs 'level:=error' 100 \
    "$(iso_offset "${timestamp}" "-${seconds}")" \
    "$(iso_offset "${timestamp}" "${seconds}")"
}

# Usage
query_logs 'level:=error AND service:=api'
count_errors
errors_around "2026-09-08T10:30:00Z" 600
```

Three properties make this safe to call from an agent:

- `set -euo pipefail` plus `curl --fail-with-body` make an HTTP error a
  non-zero exit, with the server's own message printed to stderr. Without
  `--fail`, `curl` exits `0` on a `400` and the caller treats the error text
  as results.
- `--max-time 60` bounds a runaway query.
- The declared credentials are actually sent. `VICTORIALOGS_TOKEN` or
  `VICTORIALOGS_USER`/`VICTORIALOGS_PASSWORD` are attached to every request.

Invalid LogsQL therefore fails loudly rather than returning nothing:

```console
$ query_logs '* | stats count() by service'
victorialogs request failed (curl 22): cannot parse `query` arg [...]:
cannot parse "stats" pipe: unexpected token "service"
$ echo $?
22
```

**Why**: VictoriaLogs has no built-in user model. Put it behind the `vmauth`
proxy described in [Access Control](#access-control); the wrapper's job is only
to present the credential.

## Integration with Prometheus

Cross-reference logs with metrics:

```markdown
1. Detect anomaly in metrics:
   Prometheus: rate(http_requests_total{status=~"5.."}[5m]) > 0.01

2. Find corresponding logs:
   VictoriaLogs: level:=error AND _time:5m AND service:=api

3. Correlate by request ID:
   VictoriaLogs: _time:1h AND request_id:="<id-from-trace>"
```
