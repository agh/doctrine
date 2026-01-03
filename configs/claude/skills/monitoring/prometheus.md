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

### MCP Server (if available)

```json
{
  "mcpServers": {
    "prometheus": {
      "command": "mcp-prometheus",
      "env": {
        "PROMETHEUS_URL": "${PROMETHEUS_URL}",
        "PROMETHEUS_AUTH": "${PROMETHEUS_AUTH}"
      }
    }
  }
}
```

### Direct API Access

For CLI-based access or when MCP server unavailable:

```bash
# Query via curl
curl -G "${PROMETHEUS_URL}/api/v1/query" \
  --data-urlencode "query=up{job='api'}"

# Range query
curl -G "${PROMETHEUS_URL}/api/v1/query_range" \
  --data-urlencode "query=rate(http_requests_total[5m])" \
  --data-urlencode "start=$(date -d '1 hour ago' +%s)" \
  --data-urlencode "end=$(date +%s)" \
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

| Capability | Description |
| ---------- | ----------- |
| `instant_query` | Point-in-time metric value |
| `range_query` | Metrics over time range |
| `series` | List matching time series |
| `labels` | List label names/values |
| `targets` | Scrape target status |
| `alerts` | Active alert status |
| `rules` | Alerting/recording rules |

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

```yaml
# Basic auth
PROMETHEUS_AUTH="user:password"

# Bearer token
PROMETHEUS_AUTH="Bearer ${TOKEN}"

# mTLS (recommended for production)
# Configure via environment or config file
```

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
#!/bin/bash
# prometheus-query.sh - Wrapper for agent use

PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"

query() {
  local promql="$1"
  curl -s -G "${PROMETHEUS_URL}/api/v1/query" \
    --data-urlencode "query=${promql}" | jq -r '.data.result'
}

query_range() {
  local promql="$1"
  local start="$2"
  local end="$3"
  local step="${4:-60}"

  curl -s -G "${PROMETHEUS_URL}/api/v1/query_range" \
    --data-urlencode "query=${promql}" \
    --data-urlencode "start=${start}" \
    --data-urlencode "end=${end}" \
    --data-urlencode "step=${step}" | jq -r '.data.result'
}

# Usage
query 'up{job="api"}'
query_range 'rate(http_requests_total[5m])' \
  "$(date -d '1 hour ago' +%s)" "$(date +%s)"
```
