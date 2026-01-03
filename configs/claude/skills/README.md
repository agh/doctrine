# Skills

Skills extend agent capabilities through MCP (Model Context Protocol) servers.
They provide agents with access to external systems for analysis,
communication, and action.

## Concept

```text
+-------------------------------------------------------------+
|                      AGENT + SKILLS                         |
+-------------------------------------------------------------+
|                                                             |
|   Agent declares:           Environment provides:           |
|   +------------------+     +------------------+             |
|   | skills_available | <-- | MCP Servers      |             |
|   | - postgres       |     | - postgres       |             |
|   | - github         |     | - github         |             |
|   | - discord        |     | - discord        |             |
|   +------------------+     +------------------+             |
|          |                                                  |
|   Agent uses available skills when contextually relevant    |
|   Agent gracefully degrades when skills are missing         |
|                                                             |
+-------------------------------------------------------------+
```

## Skill Categories

| Category | Purpose | Examples |
| -------- | ------- | -------- |
| **databases/** | Query data for analysis | PostgreSQL, MySQL, SQLite |
| **communication/** | Interact with services/humans | GitHub, Discord, Jira |
| **infrastructure/** | Observe/control systems | Kubernetes, AWS, UniFi |
| **monitoring/** | Metrics and observability | Prometheus, Datadog |
| **knowledge/** | Context enrichment | Notion, Confluence |

## Access Levels

Skills define access levels that agents should request:

| Level | Description | Risk |
| ----- | ----------- | ---- |
| `readonly` | Read/query only | Low |
| `read-write` | Read and modify | Medium |
| `execute` | Run actions | High |
| `admin` | Full control | Critical |

**Principle**: Agents **SHOULD** request the minimum access level needed.

## Configuration

Skills are configured via MCP server settings:

### Project-Level (`.mcp.json`)

```json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "POSTGRES_CONNECTION": "postgres://readonly@localhost/mydb"
      }
    }
  }
}
```

### User-Level (`~/.claude/settings.json`)

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "ghp_xxxx"
      }
    }
  }
}
```

## Agent Integration

Agents declare skills they can leverage in their `skills_available` section:

```markdown
## Skills Available

| Skill | Access | Use For |
|-------|--------|---------|
| `postgres` | readonly | Query deployment history |
| `github` | read-write | Create PRs, manage releases |
| `discord` | post | Send notifications |

### Graceful Degradation

| If Missing | Fallback Behavior |
|------------|-------------------|
| `postgres` | Use git history instead |
| `discord` | Log notifications locally |
```

## Creating New Skills

Each skill document **MUST** include:

1. **Overview**: What the skill provides
2. **MCP Configuration**: How to set up the server
3. **Access Levels**: Available permission tiers
4. **Capabilities**: What the skill enables
5. **Example Usage**: Concrete examples
6. **Security Considerations**: Risks and mitigations
7. **Agents**: Which agents use this skill

## Security Model

### Credential Management

- **MUST NOT** hardcode credentials in configs
- **MUST** use environment variables or secret managers
- **SHOULD** use scoped tokens with minimal permissions
- **MUST** rotate credentials regularly

### Audit Requirements

- **SHOULD** log all skill invocations
- **MUST** include agent ID and conversation context
- **SHOULD** retain logs per compliance requirements

### Access Control

```text
+-------------------------------------------------------------+
|                    ACCESS DECISION                          |
+-------------------------------------------------------------+
|                                                             |
|   readonly actions     -> Auto-approve                      |
|   read-write actions   -> Context-dependent                 |
|   execute actions      -> Human approval recommended        |
|   admin actions        -> Human approval required           |
|                                                             |
+-------------------------------------------------------------+
```

## Available Skills

### Databases

- [PostgreSQL](databases/postgres.md) - SQL query access

### Communication

- [GitHub](communication/github.md) - Repository and PR management
- [Discord](communication/discord.md) - Messaging and notifications

### Monitoring

- [Prometheus / VictoriaMetrics](monitoring/prometheus.md) - Metrics queries (PromQL)
- [VictoriaLogs](monitoring/victorialogs.md) - Log queries (LogsQL)

### IoT

- [MQTT / EMQX](iot/mqtt.md) - IoT messaging and device communication
- [Home Assistant](iot/homeassistant.md) - Smart home monitoring and automation
- [Zigbee2MQTT](iot/zigbee2mqtt.md) - Zigbee device management via MQTT
- [ESPHome](iot/esphome.md) - ESP32/ESP8266 device management and OTA
- [Tasmota](iot/tasmota.md) - Tasmota device monitoring and power analysis

## Infrastructure

Beyond skills, agents require infrastructure for coordination and security:

- [Coordination](../infrastructure/coordination.md) - Multi-agent state sharing
  and swarm behavior
- [Audit Logging](../infrastructure/audit.md) - Log all agent actions for
  compliance and learning
- [Secrets](../infrastructure/secrets.md) - Secure credential access with SOPS
