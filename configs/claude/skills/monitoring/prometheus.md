# Prometheus / VictoriaMetrics Skill

Provides PromQL query access to metrics for analysis, debugging, alerting
investigation, and capacity planning.

## Overview

| Attribute | Value |
| --------- | ----- |
| **Category** | Monitoring |
| **Protocol** | HTTP API (Prometheus-compatible) |
| **Compatible Systems** | Prometheus, VictoriaMetrics, Thanos, Cortex, Mimir |
| **Default Access** | readonly |
| **Risk Level** | Low |

## Configuration

### MCP Server

Use the official [`prometheus/prometheus-mcp`](https://github.com/prometheus/prometheus-mcp)
server, pinned at `v0.18.0`:

```json
{
  "mcpServers": {
    "prometheus": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "PROMETHEUS_MCP_SERVER_PROMETHEUS_URL",
        "-v", "/etc/prometheus-mcp:/config:ro",
        "ghcr.io/tjhop/prometheus-mcp-server:v0.18.0",
        "--http.config=/config/http-config.yml",
        "--mcp.tools=core"
      ],
      "env": {
        "PROMETHEUS_MCP_SERVER_PROMETHEUS_URL": "${PROMETHEUS_URL}"
      }
    }
  }
}
```

Authentication is configured with a
[Prometheus HTTP config](https://prometheus.io/docs/prometheus/latest/configuration/configuration/#http_config)
file passed via `--http.config`, not through an environment variable:

```yaml
# /etc/prometheus-mcp/http-config.yml
authorization:
  type: Bearer
  credentials_file: /config/token
tls_config:
  ca_file: /config/ca.pem
```

`--mcp.tools=core` loads only `docs_list`, `docs_read`, `docs_search`, `query`,
`range_query`, `metric_metadata`, `label_names`, `label_values` and `series`.
Without it the server registers every tool.

TSDB administration — `delete_series`, `snapshot`, `clean_tombstones` — stays
unavailable unless the server is started with
`--dangerous.enable-tsdb-admin-tools`. Agents **MUST NOT** be given that flag.

**Why**: the previously documented `mcp-prometheus` configuration set a
`PROMETHEUS_AUTH` variable. That package documents only `PROMETHEUS_URL`, so
the credential was never sent and the configuration silently failed against any
protected endpoint. Configuration **MUST** use the variable or flag the chosen
implementation actually reads.

### Direct API Access

For CLI-based access or when the MCP server is unavailable:

```bash
# Query via curl
curl -sS --fail-with-body -G "${PROMETHEUS_URL}/api/v1/query" \
  --data-urlencode "query=up{job='api'}"

# Range query. `date -d` is GNU-only and fails on macOS/BSD with
# "date: illegal option -- d", so compute epochs portably.
now=$(date +%s)
curl -sS --fail-with-body -G "${PROMETHEUS_URL}/api/v1/query_range" \
  --data-urlencode "query=rate(http_requests_total[5m])" \
  --data-urlencode "start=$((now - 3600))" \
  --data-urlencode "end=${now}" \
  --data-urlencode "step=60"
```

### VictoriaMetrics Specifics

VictoriaMetrics is fully Prometheus-compatible but offers additional APIs:

```bash
# VictoriaMetrics URL patterns
VICTORIA_URL="http://victoriametrics:8428"

# Standard Prometheus API (compatible)
${VICTORIA_URL}/api/v1/query
${VICTORIA_URL}/api/v1/query_range

# VictoriaMetrics extensions
${VICTORIA_URL}/api/v1/export          # Export raw data
${VICTORIA_URL}/api/v1/labels          # List all label names
${VICTORIA_URL}/api/v1/label/__name__/values  # List all metric names
```

## Capabilities

Tool names are those registered by `prometheus-mcp-server` v0.18.0 under
`--mcp.tools=core`:

| Capability | Description |
| ---------- | ----------- |
| `query` | Point-in-time metric value (instant query) |
| `range_query` | Metrics over a time range |
| `series` | List matching time series |
| `label_names` | List label names |
| `label_values` | List values for a label |
| `metric_metadata` | Type and help text for a metric |
| `docs_search` | Search official Prometheus documentation |

`targets`, `rules` and `alerts` are real tools but are not in the core set;
add them explicitly with `--mcp.tools=targets --mcp.tools=rules` when needed.

## PromQL Patterns for Agents

### Service Health

```promql
# Is the service up?
up{job="api", environment="production"}

# Uptime percentage (last 24h)
avg_over_time(up{job="api"}[24h]) * 100
```

### Error Rates

```promql
# Current error rate
sum(rate(http_requests_total{status=~"5.."}[5m]))
/ sum(rate(http_requests_total[5m])) * 100

# Error rate by endpoint
sum by (handler) (rate(http_requests_total{status=~"5.."}[5m]))
/ sum by (handler) (rate(http_requests_total[5m])) * 100
```

### Latency

```promql
# p50 latency
histogram_quantile(0.50,
  sum(rate(http_request_duration_seconds_bucket[5m])) by (le))

# p95 latency
histogram_quantile(0.95,
  sum(rate(http_request_duration_seconds_bucket[5m])) by (le))

# p99 latency
histogram_quantile(0.99,
  sum(rate(http_request_duration_seconds_bucket[5m])) by (le))

# Latency by endpoint
histogram_quantile(0.95,
  sum(rate(http_request_duration_seconds_bucket[5m])) by (le, handler)
)
```

### Throughput

```promql
# Requests per second
sum(rate(http_requests_total[5m]))

# Requests per second by endpoint
sum by (handler) (rate(http_requests_total[5m]))

# Requests per second by status
sum by (status) (rate(http_requests_total[5m]))
```

### Resource Utilization

```promql
# CPU usage percentage
100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Memory usage percentage
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100

# Disk usage percentage
(1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) * 100
```

### Container Metrics (Kubernetes)

```promql
# Container CPU usage
sum(rate(container_cpu_usage_seconds_total{container!=""}[5m])) by (pod)

# Container memory usage
sum(container_memory_working_set_bytes{container!=""}) by (pod)

# Pod restart count
sum(kube_pod_container_status_restarts_total) by (pod)
```

### Deployment Comparison

```promql
# Compare error rates: last hour vs previous hour
(
  sum(increase(http_requests_total{status=~"5.."}[1h]))
  / sum(increase(http_requests_total[1h]))
)
/
(
  sum(increase(http_requests_total{status=~"5.."}[1h] offset 1h))
  / sum(increase(http_requests_total[1h] offset 1h))
)
```

### Anomaly Detection

```promql
# Current value vs 7-day average (detect anomalies)
(
  sum(rate(http_requests_total[5m]))
  - avg_over_time(sum(rate(http_requests_total[5m]))[7d:1h])
)
/ stddev_over_time(sum(rate(http_requests_total[5m]))[7d:1h])
```

## Example Usage Patterns

### Pre-Deploy Health Check

```markdown
Query these metrics before deploying:

1. Error rate baseline:
   sum(rate(http_requests_total{status=~"5.."}[1h]))
   / sum(rate(http_requests_total[1h]))

2. Latency baseline:
   histogram_quantile(0.95,
     sum(rate(http_request_duration_seconds_bucket[1h])) by (le))

3. Resource headroom:
   avg(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))

Save these values for post-deploy comparison.
```

### Post-Deploy Validation

```markdown
Compare current metrics to pre-deploy baseline:

1. Error rate delta: Should be < 10% increase
2. Latency delta: Should be < 20% increase
3. Resource utilization: Should not spike

If any metric exceeds threshold, recommend investigation or rollback.
```

### Incident Investigation

```markdown
When investigating an incident at time T:

1. Find the change point:
   rate(http_requests_total{status=~"5.."}[1m])
   # Look for spike timing

2. Correlate with deployments:
   changes(kube_deployment_status_observed_generation[1h])

3. Check resource exhaustion:
   node_memory_MemAvailable_bytes
   container_cpu_usage_seconds_total

4. Check dependencies:
   up{job=~".*-dependency"}
```

## Agents That Use This Skill

| Agent | Access | Purpose |
| ----- | ------ | ------- |
| `ops/release-manager` | readonly | Pre/post deploy metrics |
| `ops/deploy-validator` | readonly | Health validation |
| `ops/rollback-advisor` | readonly | Incident metrics |
| `security/incident-response-lead` | readonly | Forensic analysis |

## Graceful Degradation

| If Missing | Fallback |
| ---------- | -------- |
| Prometheus unavailable | Use CI test results only |
| Historical data missing | Compare to static thresholds |
| Specific metric missing | Use proxy metrics or skip check |

## Security Considerations

### Authentication

```bash
# Basic auth: the wrapper sends these as -u user:password
PROMETHEUS_USER="agent"
PROMETHEUS_PASSWORD="..."

# Bearer token: sent as an Authorization header
PROMETHEUS_TOKEN="..."

# mTLS (recommended for production)
# Configure via the MCP server's --http.config file, or curl --cert/--key
```

Whichever is chosen, the credential **MUST** be read by the code that makes the
request. A variable that nothing sends leaves the connection unauthenticated
while appearing configured, and the failure only shows up as an unexpected
`401` from a protected server.

### Network Security

- **SHOULD** access via internal network only
- **MUST NOT** expose Prometheus publicly without auth
- **SHOULD** use TLS for all connections
- **MAY** use SSH tunnel for remote access

### Query Safety

- **SHOULD** set query timeout (prevent runaway queries)
- **SHOULD** limit time range for expensive queries
- **MUST NOT** allow agents to modify recording rules
- **SHOULD** use read-only user/role if available

```yaml
# VictoriaMetrics query limits
-search.maxQueryDuration=30s
-search.maxQueueDuration=10s
-search.maxPointsPerTimeseries=30000
```

## CLI Access Pattern

When MCP is unavailable, agents can use direct HTTP:

```bash
#!/usr/bin/env bash
# prometheus-query.sh - Wrapper for agent use
set -euo pipefail

PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"

# One place where every HTTP call is made, so every call fails closed.
_api() {
  local path="$1"; shift

  local auth=()
  if [ -n "${PROMETHEUS_TOKEN:-}" ]; then
    auth=(-H "Authorization: Bearer ${PROMETHEUS_TOKEN}")
  elif [ -n "${PROMETHEUS_USER:-}" ]; then
    auth=(-u "${PROMETHEUS_USER}:${PROMETHEUS_PASSWORD:?password required}")
  fi

  local body rc
  # ${arr[@]+"${arr[@]}"} keeps an empty array from tripping `set -u`
  # on bash 3.2, which is what macOS ships.
  # `|| rc=$?` stops `set -e` killing the script before the body is shown.
  rc=0
  body=$(curl -sS --fail-with-body --max-time 30 -G \
    ${auth[@]+"${auth[@]}"} \
    "${PROMETHEUS_URL}${path}" "$@") || rc=$?

  if [ "$rc" -ne 0 ]; then
    printf 'prometheus request failed (curl %s): %s\n' "$rc" "$body" >&2
    return "$rc"
  fi

  # A 200 response can still carry status:"error".
  if [ "$(printf '%s' "$body" | jq -r '.status')" != "success" ]; then
    printf 'prometheus error: %s\n' \
      "$(printf '%s' "$body" | jq -r '.error // "unknown"')" >&2
    return 1
  fi

  # Partial results are reported, not silently dropped.
  printf '%s' "$body" | jq -r '.warnings // [], .infos // [] | .[]' >&2

  printf '%s' "$body"
}

query() {
  _api /api/v1/query --data-urlencode "query=$1" | jq -r '.data.result'
}

query_range() {
  local promql="$1" start="$2" end="$3" step="${4:-60}"
  _api /api/v1/query_range \
    --data-urlencode "query=${promql}" \
    --data-urlencode "start=${start}" \
    --data-urlencode "end=${end}" \
    --data-urlencode "step=${step}" | jq -r '.data.result'
}

# Usage
now=$(date +%s)
query 'up{job="api"}'
query_range 'rate(http_requests_total[5m])' "$((now - 3600))" "${now}"
```

The original wrapper reported failure as success. `curl -s` exits `0` on an
HTTP `400`, and piping straight into `jq -r '.data.result'` prints `null`:

```console
$ query 'rate(((('
null
$ echo $?
0
```

The version above exits non-zero and prints the server's message on stderr.
Four things make that work, and all four are **REQUIRED**:

- `set -euo pipefail`, so a failing command ends the script.
- `--fail-with-body`, so an HTTP error is a non-zero `curl` exit **and** the
  response body is still printed.
- An explicit `.status == "success"` check, because Prometheus returns
  `{"status":"error"}` inside some `200` responses.
- `--max-time 30`, so a hung request cannot stall the agent indefinitely.

`warnings` and `infos` are forwarded to stderr. Prometheus sets them when a
query hit a limit and returned partial data, which otherwise looks identical to
a complete result.

`PROMETHEUS_TOKEN` or `PROMETHEUS_USER`/`PROMETHEUS_PASSWORD` are attached to
every request rather than being declared and ignored.

`date -d '1 hour ago'` is GNU-specific. On macOS it fails with `date: illegal
option -- d`, so the wrapper does arithmetic on `date +%s`, which is portable.
