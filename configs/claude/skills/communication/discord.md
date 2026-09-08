# Discord Skill

Provides messaging capabilities for notifications, alerts, and team
communication through Discord webhooks and bot integration.

## Overview

| Attribute | Value |
| --------- | ----- |
| **Category** | Communication |
| **MCP Server** | None; direct webhook HTTP (or `mcp-discord@1.3.4` for bot access) |
| **Default Access** | post (send-only) |
| **Risk Level** | Low |

## MCP Configuration

The packages `mcp-discord-webhook` and `mcp-discord-bot` do not exist. Both
resolve to HTTP 404 on the npm registry, so every `npx -y` invocation naming
them fails before any Discord call is made.

### Webhook-Based (Simplest)

For send-only notifications, post to the webhook URL directly. This needs no
package, so there is no third-party code in the credential's path:

```bash
curl -sS --fail-with-body -X POST "$DISCORD_WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d '{
    "content": "Release v1.2.0 published",
    "allowed_mentions": {"parse": []}
  }'
```

**Why**: a webhook URL is a bearer credential for one channel. Handing it to an
unaudited npm package that runs on every `npx -y` resolution widens the blast
radius for no capability gain.

No MCP wrapper is recommended for the webhook path. The most visible candidate,
`@lmquang/mcp-discord-webhook@1.3.1`, contains no reference to any `DISCORD_*`
environment variable; its `webhookUrl` is a **required per-call tool
parameter**, so the credential has to be supplied to the model on every call
rather than held in the environment. That defeats the point of treating the URL
as a secret.

Agents **MUST** verify that a candidate package reads the variable a
configuration sets before relying on it:

```bash
npm pack @lmquang/mcp-discord-webhook@1.3.1
tar -xzf lmquang-mcp-discord-webhook-1.3.1.tgz
grep -rc 'DISCORD' package/   # 0 matches
```

### Bot-Based (Full Features)

Reading message history requires a bot application. `mcp-discord@1.3.4` exists
and is not deprecated; the same review-and-pin requirement applies.

```json
{
  "mcpServers": {
    "discord": {
      "command": "npx",
      "args": ["-y", "mcp-discord@1.3.4"],
      "env": {
        "DISCORD_TOKEN": "${DISCORD_BOT_TOKEN}"
      }
    }
  }
}
```

### Multiple Channels

One webhook per channel, each in its own variable:

```bash
post_discord() {
  curl -sS --fail-with-body -X POST "$1" \
    -H 'Content-Type: application/json' \
    -d "$2"
}

post_discord "$DISCORD_RELEASES_WEBHOOK" "$release_payload"
post_discord "$DISCORD_ALERTS_WEBHOOK" "$alert_payload"
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

### Creating a Bot Application

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
   and create a New Application.
2. Under **Bot**, copy the token. Treat it as a secret; regenerating it
   invalidates the old one.
3. Under **Bot -> Privileged Gateway Intents**, enable **Message Content** if
   the agent must read message text. This is off by default.
4. Under **Installation**, set the install context, add the `bot` scope and the
   permissions from the table below, then use the generated install link.

The `bot` scope already carries application commands; `applications.commands`
is only needed for an app that installs commands without a bot user.

### Permissions and Intents

Discord gates capability twice, and both gates **MUST** be satisfied:

| Capability | Permission | Intent |
| ---------- | ---------- | ------ |
| Send message to channel | Send Messages | — |
| Send message in thread | Send Messages in Threads | — |
| Read channel history (REST) | View Channel + Read Message History | — |
| Read message **text** | as above | `MESSAGE_CONTENT` (privileged) |
| Receive live messages (Gateway) | View Channel | `GUILD_MESSAGES` |
| Add reaction | Add Reactions | — |
| Create thread | Create Public Threads | — |
| Pin message | Manage Messages | — |

Permissions decide which endpoints succeed. Intents decide which data the
payload contains. Without `MESSAGE_CONTENT` an app receives empty `content`,
`embeds`, `attachments` and `components`, so `read_messages` returns messages
with no text and the failure is silent — no error, just blank fields.

Four documented exceptions deliver content without the intent: the app's own
messages, DMs with the app, messages that mention the app, and the target of a
message context-menu command.

**Why**: `MESSAGE_CONTENT` is a privileged intent. It must be enabled in the
portal, and for apps in 100 or more guilds it must also be approved after
verification. Connecting with an unconfigured privileged intent closes the
Gateway connection with close code `4014`.

## Capabilities

| Capability | Access | Description |
| ---------- | ------ | ----------- |
| `send_message` | post | Send message to channel |
| `send_embed` | post | Send rich embed message |
| `read_messages` | readonly | Read channel history (needs `MESSAGE_CONTENT`) |
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

Every payload **MUST** carry an explicit `allowed_mentions`. Webhook and
interaction payloads default to `{"parse": ["users"]}`, so a user mention
pasted into untrusted content still pings by default.

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
  }],
  "allowed_mentions": {"parse": []}
}
```

### Payload Limits

Exceeding any of these returns `400 Bad Request`, so agents **MUST** validate
before sending rather than discovering the limit from a failed alert:

| Field | Limit |
| ----- | ----- |
| `content` | 2,000 characters |
| `embeds` | 10 per message |
| All embeds combined | 6,000 characters |
| `embed.title`, `field.name`, `author.name` | 256 characters |
| `embed.description` | 4,096 characters |
| `embed.fields` | 25 per embed |
| `field.value` | 1,024 characters |
| `footer.text` | 2,048 characters |
| Attachments | 25 MiB per message |
| `allowed_mentions.roles` / `.users` | 100 ids each |

The 6,000-character total counts `title`, `description`, `field.name`,
`field.value`, `footer.text` and `author.name` across every embed in the
message.

Agents **MUST** truncate to the limit with a visible marker and **SHOULD**
attach the full text as a file rather than dropping it. Discord counts
**characters**, not bytes, so truncate with a character-aware tool. `head -c`
counts bytes: it splits multi-byte characters, producing invalid UTF-8 that
Discord rejects with `400`, and a byte-vs-character length test skips the
marker entirely on non-ASCII content.

```bash
body=$(printf '%s' "$long_text" | python3 -c '
import sys
t = sys.stdin.read()
limit = 1900
sys.stdout.write(t if len(t) <= limit
                 else t[:limit] + "\n... truncated, full log attached")')
```

### Alert Notification

```json
{
  "content": "<@&123456789012345678> Deployment alert",
  "embeds": [{
    "title": "Elevated error rate",
    "color": 15548997,
    "fields": [
      {"name": "Environment", "value": "production", "inline": true},
      {"name": "Error rate", "value": "0.12% -> 0.45%", "inline": true}
    ],
    "footer": {"text": "ops/deploy-validator"}
  }],
  "allowed_mentions": {
    "parse": [],
    "roles": ["123456789012345678"]
  }
}
```

`@oncall` typed as literal text is not a mention. It renders as plain text and
pages nobody. A role mention is `<@&ROLE_ID>`, and it only notifies when that
role id is listed in `allowed_mentions.roles`.

`parse` is mutually exclusive with `roles` and `users`: listing `"roles"` in
`parse` makes every role mention in the content live, whereas the empty `parse`
above plus an explicit id allowlists exactly one role.

Two further conditions apply: the role's `mentionable` field must be `true`, or
the app needs the `MENTION_EVERYONE` permission; and `@everyone`/`@here`
require `MENTION_EVERYONE` regardless.

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

`{mention}` **MUST** be substituted with a role id in `<@&ID>` form and the same
id **MUST** be added to `allowed_mentions.roles`. A display name such as
`@oncall` renders as inert text.

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
- **MUST** set `allowed_mentions` explicitly on every payload
- **MUST** sanitise any user-provided content before embedding it
- **MUST** include agent identifier in messages

Embeds do **not** prevent injection. They constrain layout, not content: an
embed field renders Markdown, renders links, and will happily carry text
supplied by whoever filed the issue being summarised. The controls that do work
are mention suppression, length validation, and not turning untrusted strings
into links.

```json
{
  "content": "Issue title: @everyone click http://attacker.example",
  "allowed_mentions": {"parse": []}
}
```

With `{"parse": []}` the `@everyone` above renders as text and notifies nobody.
Without it, a webhook still parses user mentions by default.

Agents **SHOULD** strip or defang URLs taken from untrusted input, and
**MUST NOT** place untrusted text into `embed.url`, `author.url` or
`footer.icon_url`, which are rendered as live links or fetched by Discord.

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

The Discord step is a fragment of the release workflow in the
[GitHub skill](github.md#release-workflow). It posts the notes that an earlier
step created, and fails the job if Discord rejects the payload:

```yaml
      - name: Announce release
        env:
          DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_RELEASES_WEBHOOK }}
        run: |
          set -euo pipefail
          payload=$(jq -n \
            --arg title "Release ${GITHUB_REF_NAME}" \
            --rawfile notes RELEASE_NOTES.md \
            '{embeds: [{title: $title,
                        description: ($notes | .[0:4096])}],
              allowed_mentions: {parse: []}}')
          curl -sS --fail-with-body -X POST "$DISCORD_WEBHOOK_URL" \
            -H 'Content-Type: application/json' \
            -d "$payload"
```

`jq -n --rawfile` builds the JSON, so a backtick or quote in the release notes
cannot break out of the payload. `--fail-with-body` makes a `400` a job
failure and prints Discord's reason.

### Alert Integration

```yaml
alerts:
  - name: HighErrorRate
    condition: error_rate > 1%
    action:
      discord:
        webhook: ${DISCORD_ALERTS_WEBHOOK}
        template: alert
        # Role id, not a display name. Must also appear in
        # allowed_mentions.roles for the ping to fire.
        mention: "<@&123456789012345678>"
```
