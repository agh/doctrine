# PostgreSQL Skill

Provides SQL query access to PostgreSQL databases for analysis, debugging, and
operational intelligence.

## Overview

| Attribute | Value |
| --------- | ----- |
| **Category** | Database |
| **MCP Server** | `@modelcontextprotocol/server-postgres` |
| **Default Access** | readonly |
| **Risk Level** | Low (readonly) / Medium (read-write) |

## MCP Configuration

### Basic Setup

```json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "POSTGRES_CONNECTION": "${POSTGRES_URL}"
      }
    }
  }
}
```

### Multiple Databases

```json
{
  "mcpServers": {
    "postgres-prod": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "POSTGRES_CONNECTION": "${POSTGRES_PROD_READONLY_URL}"
      }
    },
    "postgres-analytics": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "POSTGRES_CONNECTION": "${POSTGRES_ANALYTICS_URL}"
      }
    }
  }
}
```

## Access Levels

| Level | PostgreSQL Role | Permissions | Use Case |
| ----- | --------------- | ----------- | -------- |
| `readonly` | `agent_readonly` | SELECT | Analysis, debugging |
| `analyst` | `agent_analyst` | SELECT, CREATE TEMP TABLE | Complex analysis |
| `operator` | `agent_operator` | SELECT, INSERT, UPDATE (ops tables) | Incident response |
| `admin` | `agent_admin` | Full access | Migration support |

### Creating Roles

```sql
-- Readonly role (recommended for most agents)
CREATE ROLE agent_readonly WITH LOGIN PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE mydb TO agent_readonly;
GRANT USAGE ON SCHEMA public TO agent_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO agent_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT ON TABLES TO agent_readonly;

-- Analyst role (for complex analysis)
CREATE ROLE agent_analyst WITH LOGIN PASSWORD 'secure_password';
GRANT agent_readonly TO agent_analyst;
GRANT CREATE ON SCHEMA pg_temp TO agent_analyst;

-- Operator role (for incident response)
CREATE ROLE agent_operator WITH LOGIN PASSWORD 'secure_password';
GRANT agent_readonly TO agent_operator;
GRANT INSERT, UPDATE ON ops.incidents, ops.deployments TO agent_operator;
```

## Capabilities

The PostgreSQL skill provides:

| Capability | Description |
| ---------- | ----------- |
| `query` | Execute SELECT queries |
| `list_tables` | List available tables |
| `describe_table` | Get table schema |
| `list_schemas` | List database schemas |

## Example Usage

### Deployment Analysis

```sql
-- Recent deployments
SELECT
  version,
  deployed_at,
  deployed_by,
  environment,
  status
FROM deployments
WHERE environment = 'production'
ORDER BY deployed_at DESC
LIMIT 20;
```

### Error Correlation

```sql
-- Errors by hour with deployment markers
WITH hourly_errors AS (
  SELECT
    date_trunc('hour', occurred_at) as hour,
    COUNT(*) as error_count
  FROM errors
  WHERE occurred_at > NOW() - INTERVAL '48 hours'
  GROUP BY 1
),
deploy_times AS (
  SELECT
    date_trunc('hour', deployed_at) as hour,
    version
  FROM deployments
  WHERE deployed_at > NOW() - INTERVAL '48 hours'
)
SELECT
  e.hour,
  e.error_count,
  d.version as deployment
FROM hourly_errors e
LEFT JOIN deploy_times d ON e.hour = d.hour
ORDER BY e.hour;
```

### Release Metrics

```sql
-- Release frequency and stability
SELECT
  date_trunc('week', deployed_at) as week,
  COUNT(*) as releases,
  COUNT(*) FILTER (WHERE rolled_back) as rollbacks,
  ROUND(100.0 * COUNT(*) FILTER (WHERE rolled_back) / COUNT(*), 1)
    as rollback_pct
FROM deployments
WHERE environment = 'production'
  AND deployed_at > NOW() - INTERVAL '3 months'
GROUP BY 1
ORDER BY 1;
```

### Incident Investigation

```sql
-- Find changes around incident time
SELECT
  'deployment' as event_type,
  version as detail,
  deployed_at as occurred_at
FROM deployments
WHERE deployed_at BETWEEN $1 - INTERVAL '1 hour' AND $1 + INTERVAL '1 hour'

UNION ALL

SELECT
  'config_change' as event_type,
  key || ' = ' || new_value as detail,
  changed_at as occurred_at
FROM config_changes
WHERE changed_at BETWEEN $1 - INTERVAL '1 hour' AND $1 + INTERVAL '1 hour'

ORDER BY occurred_at;
```

## Agents That Use This Skill

| Agent | Access | Purpose |
| ----- | ------ | ------- |
| `ops/release-manager` | readonly | Deployment history, release metrics |
| `ops/rollback-advisor` | readonly | Incident correlation, change analysis |
| `ops/deploy-validator` | readonly | Pre/post deploy verification |
| `security/incident-response-lead` | readonly | Forensic investigation |

## Graceful Degradation

When PostgreSQL is unavailable, agents should:

| Scenario | Fallback |
| -------- | -------- |
| Deployment history | Parse git tags and CI artifacts |
| Error correlation | Use log files or monitoring APIs |
| Release metrics | Derive from git commit history |

## Security Considerations

### Connection Security

- **MUST** use SSL connections (`sslmode=require` or `verify-full`)
- **MUST** use dedicated agent credentials (not personal or app credentials)
- **SHOULD** restrict by IP/network where possible
- **MUST** use connection pooling for high-volume usage

### Query Safety

- **MUST** use parameterized queries for any user-provided values
- **SHOULD** set statement timeout to prevent runaway queries
- **MUST NOT** allow agents to execute DDL (CREATE, DROP, ALTER)
- **SHOULD** limit result set sizes

```sql
-- Set statement timeout (in PostgreSQL connection)
SET statement_timeout = '30s';

-- Or in connection string
postgres://user@host/db?options=-c%20statement_timeout%3D30s
```

### Audit Logging

Enable query logging for agent connections:

```sql
-- In postgresql.conf or per-role
ALTER ROLE agent_readonly SET log_statement = 'all';
ALTER ROLE agent_readonly SET log_min_duration_statement = 0;
```

### Sensitive Data

- **MUST** exclude PII tables from agent access where possible
- **SHOULD** use views to mask sensitive columns
- **MUST** document which tables contain sensitive data

```sql
-- Create a safe view for agents
CREATE VIEW agent_users AS
SELECT
  id,
  created_at,
  subscription_tier,
  -- Mask email
  CONCAT(LEFT(email, 2), '***@***') as email_masked
FROM users;

GRANT SELECT ON agent_users TO agent_readonly;
-- Do NOT grant on users table directly
```
