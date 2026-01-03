# Discord Skill

Provides messaging capabilities for notifications, alerts, and team
communication through Discord webhooks and bot integration.

## Overview

| Attribute | Value |
| --------- | ----- |
| **Category** | Communication |
| **MCP Server** | `mcp-discord` (community) or custom |
| **Default Access** | post (send-only) |
| **Risk Level** | Low |

## MCP Configuration

### Webhook-Based (Simplest)

For send-only notifications, webhooks are simplest and most secure:

```json
{
  "mcpServers": {
    "discord": {
      "command": "npx",
      "args": ["-y", "mcp-discord-webhook"],
      "env": {
        "DISCORD_WEBHOOK_URL": "${DISCORD_WEBHOOK_URL}"
      }
    }
  }
}
```

### Bot-Based (Full Features)

For reading messages and richer interaction:

```json
{
  "mcpServers": {
    "discord": {
      "command": "npx",
      "args": ["-y", "mcp-discord-bot"],
      "env": {
        "DISCORD_BOT_TOKEN": "${DISCORD_BOT_TOKEN}",
        "DISCORD_GUILD_ID": "${DISCORD_GUILD_ID}"
      }
    }
  }
}
```

### Multiple Channels

```json
{
  "mcpServers": {
    "discord-releases": {
      "command": "npx",
      "args": ["-y", "mcp-discord-webhook"],
      "env": {
        "DISCORD_WEBHOOK_URL": "${DISCORD_RELEASES_WEBHOOK}"
      }
    },
    "discord-alerts": {
      "command": "npx",
      "args": ["-y", "mcp-discord-webhook"],
      "env": {
        "DISCORD_WEBHOOK_URL": "${DISCORD_ALERTS_WEBHOOK}"
      }
    }
  }
}
```

## Access Levels

| Level | Method | Permissions | Use Case |
| ----- | ------ | ----------- | -------- |
| `post` | Webhook | Send messages only | Notifications, alerts |
| `readonly` | Bot | Read messages, reactions | Context gathering |
| `read-write` | Bot | Send, read, react | Interactive workflows |
| `manage` | Bot | Manage channels, pins | Rarely needed |

### Creating Webhooks

1. Open Discord -> Server Settings -> Integrations -> Webhooks
2. Click "New Webhook"
3. Name it (e.g., "Release Bot", "Alert Bot")
4. Select target channel
5. Copy webhook URL

### Creating Bot Token

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create New Application
3. Go to Bot -> Add Bot
4. Copy token
5. Under OAuth2 -> URL Generator:
   - Scopes: `bot`
   - Permissions: Select required permissions
6. Use generated URL to add bot to server

## Capabilities

| Capability | Access | Description |
| ---------- | ------ | ----------- |
| `send_message` | post | Send message to channel |
| `send_embed` | post | Send rich embed message |
| `read_messages` | readonly | Read channel history |
| `add_reaction` | read-write | React to messages |
| `create_thread` | read-write | Create thread from message |
| `pin_message` | manage | Pin/unpin messages |

## Example Usage

### Release Notification

```markdown
Send to #releases:

**Release v1.2.0**

**Changes:**
- Added user profile editing
- Fixed timezone display bug
- Improved API performance by 40%

**Breaking Changes:** None

[View Release](https://github.com/org/repo/releases/tag/v1.2.0)
```

### Embed Format

```json
{
  "embeds": [{
    "title": "Release v1.2.0",
    "color": 5025616,
    "fields": [
      {
        "name": "Added",
        "value": "- User profile editing\n- Rate limiting",
        "inline": false
      },
      {
        "name": "Fixed",
        "value": "- Timezone display\n- Session handling",
        "inline": false
      }
    ],
    "footer": {
      "text": "Released by ops/release-manager"
    },
    "timestamp": "2025-01-02T10:30:00.000Z"
  }]
}
```

### Alert Notification

```markdown
Send to #alerts:

**Deployment Alert**

Environment: **production**
Status: **Elevated error rate**

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Error Rate | 0.12% | 0.45% | +275% |

**Action Required:** Investigate or consider rollback.

CC: @oncall
```

### Incident Thread

```markdown
Create thread in #incidents:

**INC-1234: API Latency Spike**

**Timeline:**
- 10:30 - Latency increase detected
- 10:32 - Alert fired
- 10:35 - Investigation started

**Status:** Investigating

Updates will be posted in this thread.
```

## Agents That Use This Skill

| Agent | Access | Purpose |
| ----- | ------ | ------- |
| `ops/release-manager` | post | Release announcements |
| `ops/deploy-validator` | post | Deployment status |
| `ops/rollback-advisor` | post | Rollback notifications |
| `security/incident-response-lead` | read-write | Incident coordination |

## Graceful Degradation

When Discord is unavailable, agents should:

| Scenario | Fallback |
| -------- | -------- |
| Release notification | Log to file, continue release |
| Alert | Use backup channel (email, PagerDuty) |
| Incident thread | Create GitHub issue instead |

## Message Templates

### Release Announcement

```markdown
## {project} {version}

{summary}

### Changes
{changelog}

### Links
- [Release Notes]({release_url})
- [Diff]({compare_url})

---
*Released by {agent} at {timestamp}*
```

### Deploy Status

```markdown
## {emoji} Deploy {status}

**Environment:** {environment}
**Version:** {version}
**Duration:** {duration}

{details}

---
*{agent} - {timestamp}*
```

### Alert

```markdown
## {severity_emoji} {alert_title}

**Severity:** {severity}
**Environment:** {environment}

### Metrics
{metrics_table}

### Recommended Action
{action}

{mention}
```

## Security Considerations

### Webhook Security

- **MUST** treat webhook URLs as secrets
- **MUST NOT** commit webhook URLs to repositories
- **SHOULD** use separate webhooks per channel/purpose
- **SHOULD** rotate webhooks periodically
- **MAY** use webhook with thread_id for contained discussions

### Bot Security

- **MUST** use minimal required permissions
- **MUST** restrict bot to specific channels/servers
- **SHOULD** implement rate limiting
- **MUST NOT** store message content (privacy)

### Content Guidelines

- **MUST NOT** post sensitive data (secrets, PII, credentials)
- **SHOULD** sanitize any user-provided content
- **SHOULD** use embeds for structured data (prevents injection)
- **MUST** include agent identifier in messages

### Rate Limits

Discord rate limits:

- Webhooks: 30 requests/minute per webhook
- Bot API: Varies by endpoint

Agents **SHOULD**:

- Batch notifications where sensible
- Implement backoff on 429 responses
- Queue non-urgent messages
- Use threads to reduce channel noise

## Channel Organization

Recommended channel structure for agent notifications:

```text
NOTIFICATIONS
+-- #releases        -> Release announcements
+-- #deployments     -> Deploy status updates
+-- #changelog       -> Automated changelog posts

ALERTS
+-- #alerts          -> System alerts
+-- #incidents       -> Incident threads
+-- #security        -> Security notifications

AUTOMATION
+-- #agent-logs      -> Agent activity logs
+-- #agent-debug     -> Debug/verbose output
```

## Integration Patterns

### Release Pipeline

```yaml
# In release workflow
- name: Announce Release
  run: |
    claude /release --announce discord
  env:
    DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_RELEASES_WEBHOOK }}
```

### Alert Integration

```yaml
# In monitoring/alerting
alerts:
  - name: HighErrorRate
    condition: error_rate > 1%
    action:
      discord:
        webhook: ${DISCORD_ALERTS_WEBHOOK}
        template: alert
        mention: "@oncall"
```
