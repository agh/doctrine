# PostgreSQL Skill

Provides SQL query access to PostgreSQL databases for analysis, debugging, and
operational intelligence.

## Overview

| Attribute | Value |
| --------- | ----- |
| **Category** | Database |
| **MCP Server** | `crystaldba/postgres-mcp:0.3.0` |
| **Default Access** | readonly (`--access-mode=restricted`) |
| **Risk Level** | Low (readonly) / Medium (read-write) |

## MCP Configuration

Agents **MUST NOT** use `@modelcontextprotocol/server-postgres`. npm marks it
`"Package no longer supported"` at its final version `0.6.2`, and its source now
lives in the `modelcontextprotocol/servers-archived` repository. It also reads
its connection string from `argv[2]`, not from an environment variable, so an
`env`-only configuration exits before it opens a connection:

```console
$ POSTGRES_CONNECTION=postgres://... npx -y @modelcontextprotocol/server-postgres
npm warn deprecated @modelcontextprotocol/server-postgres@0.6.2: Package no longer supported.
Please provide a database URL as a command-line argument
```

This guide pins [`crystaldba/postgres-mcp`](https://github.com/crystaldba/postgres-mcp)
at `0.3.0`. It reads `DATABASE_URI` from the environment and takes an explicit
access mode.

### Basic Setup

```json
{
  "mcpServers": {
    "postgres": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "DATABASE_URI",
        "crystaldba/postgres-mcp:0.3.0",
        "--access-mode=restricted"
      ],
      "env": {
        "DATABASE_URI": "${POSTGRES_READONLY_URL}"
      }
    }
  }
}
```

`--access-mode=restricted` is **REQUIRED**. The server defaults to
`unrestricted`, which registers `execute_sql` as "Execute any SQL query" and
runs writes and DDL. Under `restricted` the same call is rejected before it
reaches the server:

```console
$ ... execute_sql {"sql": "DELETE FROM public.users"}
Error: Error validating query: DELETE FROM public.users
```

**Why**: the access mode is the only server-side control over what the tool will
execute. A pinned image tag keeps that behaviour reproducible; `latest` can
change the default under you.

### Multiple Databases

```json
{
  "mcpServers": {
    "postgres-prod": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "DATABASE_URI",
        "crystaldba/postgres-mcp:0.3.0",
        "--access-mode=restricted"
      ],
      "env": {
        "DATABASE_URI": "${POSTGRES_PROD_READONLY_URL}"
      }
    },
    "postgres-analytics": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "DATABASE_URI",
        "crystaldba/postgres-mcp:0.3.0",
        "--access-mode=restricted"
      ],
      "env": {
        "DATABASE_URI": "${POSTGRES_ANALYTICS_URL}"
      }
    }
  }
}
```

The server's access mode is a convenience guard, not a security boundary. The
database role in `DATABASE_URI` **MUST** independently lack every privilege the
agent is not meant to hold. See [Creating Roles](#creating-roles).

## Access Levels

| Level | PostgreSQL Role | Permissions | Use Case |
| ----- | --------------- | ----------- | -------- |
| `readonly` | `agent_readonly` | SELECT on named tables | Analysis, debugging |
| `analyst` | `agent_analyst` | readonly + TEMPORARY on database | Complex analysis |
| `operator` | `agent_operator` | readonly + INSERT/UPDATE on `ops` | Incident response |
| `admin` | `agent_admin` | Full access | Migration support |

Anything above `readonly` also needs `--access-mode=unrestricted`, because
`restricted` rejects writes before they reach the database. Grant that
combination only to a role whose privileges are themselves limited to the
tables it is meant to change.

### Creating Roles

Every grant below is additive and independent: PostgreSQL combines privileges
held directly, via `PUBLIC`, and via every granted role. A role therefore reads
whatever *any* of its grants permits, so scope grants to named objects.

```sql
-- Readonly role (recommended for most agents)
CREATE ROLE agent_readonly WITH LOGIN PASSWORD 'replace_me';
GRANT CONNECT ON DATABASE mydb TO agent_readonly;
GRANT USAGE ON SCHEMA public TO agent_readonly;

-- Grant each approved table by name.
GRANT SELECT ON public.deployments, public.errors, public.config_changes
  TO agent_readonly;

-- Analyst role (for complex analysis)
CREATE ROLE agent_analyst WITH LOGIN PASSWORD 'replace_me';
GRANT agent_readonly TO agent_analyst;
GRANT TEMPORARY ON DATABASE mydb TO agent_analyst;

-- Operator role (for incident response)
CREATE ROLE agent_operator WITH LOGIN PASSWORD 'replace_me';
GRANT agent_readonly TO agent_operator;
GRANT USAGE ON SCHEMA ops TO agent_operator;
GRANT SELECT, INSERT, UPDATE ON ops.incidents, ops.deployments TO agent_operator;
GRANT USAGE, SELECT ON SEQUENCE
  ops.incidents_id_seq, ops.deployments_id_seq TO agent_operator;
```

Three details are load-bearing:

- Temporary-object creation is a **database** privilege. `GRANT CREATE ON SCHEMA
  pg_temp` fails with `ERROR: schema "pg_temp" does not exist` in any session
  that has not already created a temporary object, so `GRANT TEMPORARY ON
  DATABASE` is **REQUIRED** instead.
- `INSERT` on a table is not sufficient. Without `USAGE` on the schema the
  statement fails with `permission denied for schema ops`, and a `bigserial`
  column then fails with `permission denied for sequence incidents_id_seq`.
- Agents **MUST NOT** be given blanket schema grants. `GRANT SELECT ON ALL
  TABLES IN SCHEMA public` grants every current table, including tables holding
  personal data, and `ALTER DEFAULT PRIVILEGES ... GRANT SELECT ON TABLES`
  extends that to every table created afterwards.

**Why**: a role's effective authority is the union of its grants. Naming the
approved objects is the only form that stays correct when someone later adds a
sensitive table to the same schema.

Verify the result rather than assuming it:

```sql
SELECT has_table_privilege('agent_readonly', 'public.users', 'SELECT');
--  f
```

## Capabilities

`crystaldba/postgres-mcp:0.3.0` registers these tools. The list was read from a
live `tools/list` response, not from prose:

| Capability | Description |
| ---------- | ----------- |
| `execute_sql` | Run SQL; read-only under `--access-mode=restricted` |
| `list_schemas` | List all schemas in the database |
| `list_objects` | List tables, views, sequences or extensions in a schema |
| `get_object_details` | Column, constraint and index detail for one object |
| `explain_query` | Return an execution plan, optionally with `ANALYZE` |
| `analyze_db_health` | Health checks (bloat, connections, vacuum, indexes) |
| `analyze_workload_indexes` | Recommend indexes from `pg_stat_statements` |
| `analyze_query_indexes` | Recommend indexes for supplied queries |
| `get_top_queries` | Slowest or most resource-intensive statements |

`explain_query` with `analyze: true` and `analyze_db_health` execute work
against the live server. Agents **MUST NOT** point them at a production primary
without an explicit statement timeout.

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

`$1` carries no type of its own. Written bare, `$1 - INTERVAL '1 hour'`
resolves the parameter as `interval`, and the query fails to plan:

```text
ERROR:  operator does not exist: timestamp with time zone >= interval
HINT:  No operator matches the given name and argument types.
```

Cast every parameter at its first use:

```sql
-- Find changes around incident time
SELECT
  'deployment' AS event_type,
  version AS detail,
  deployed_at AS occurred_at
FROM deployments
WHERE deployed_at BETWEEN $1::timestamptz - INTERVAL '1 hour'
                      AND $1::timestamptz + INTERVAL '1 hour'

UNION ALL

SELECT
  'config_change' AS event_type,
  key || ' = ' || new_value AS detail,
  changed_at AS occurred_at
FROM config_changes
WHERE changed_at BETWEEN $1::timestamptz - INTERVAL '1 hour'
                     AND $1::timestamptz + INTERVAL '1 hour'

ORDER BY occurred_at;
```

The `execute_sql` tool accepts a single `sql` string and no parameter array, so
there is no bind channel through the MCP server. Agents **MUST** run
parameterised statements through a client that binds values — `psql` with
`PREPARE`/`EXECUTE`, or a driver — and **MUST NOT** build the statement by
interpolating an incident timestamp into the SQL text.

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
- **MUST** verify that the base table is unreadable after adding a masking view

A masking view adds a grant; it removes nothing. If the role can already read
the base table, it keeps reading the base table:

```sql
-- Don't: the view is readable, and so is the raw column
SET ROLE agent_readonly;
SELECT email_masked FROM agent_users;  -- al***@***
SELECT email FROM public.users;        -- alice@example.invalid
```

```sql
-- Do: create the view, then withdraw base-table access
CREATE VIEW agent_users WITH (security_barrier = true) AS
SELECT
  id,
  created_at,
  subscription_tier,
  -- Mask email
  CONCAT(LEFT(email, 2), '***@***') AS email_masked
FROM users;

REVOKE ALL ON public.users FROM agent_readonly;
GRANT SELECT ON agent_users TO agent_readonly;
```

Then confirm the denial:

```sql
SET ROLE agent_readonly;
SELECT has_table_privilege(current_user, 'public.users', 'SELECT');
--  f
SELECT email FROM public.users;
--  ERROR:  permission denied for table users
```

**Why**: `security_barrier` controls when user-supplied functions may see rows
passing through the view. It is not an access boundary, and it has no effect on
a separate grant that already permits reading the table directly.

`REVOKE` withdraws only the privileges named in it. Access also reaching the
role through `PUBLIC` or through another granted role survives, so audit with
`has_table_privilege` rather than reading the grant statements.
