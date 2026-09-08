# Home Assistant Skill

Provides access to Home Assistant for smart home monitoring, automation debugging, and device management.

## Overview

| Attribute | Value |
| --------- | ----- |
| **Category** | IoT / Home Automation |
| **Protocol** | REST API, WebSocket |
| **Default Access** | readonly |
| **Risk Level** | Medium-High (controls physical devices) |

## Configuration

### MCP Server

Home Assistant ships its own MCP server. Enable the
[Model Context Protocol Server](https://www.home-assistant.io/integrations/mcp_server/)
integration (Settings -> Devices & services -> Add Integration) and connect to
`/api/mcp` over Streamable HTTP. Verified against Home Assistant 2026.9.1.

```bash
claude mcp add-json "HA" '{
  "type": "http",
  "url": "https://<your_home_assistant_url>/api/mcp",
  "oauth": {
    "clientId": "http://localhost:12345",
    "callbackPort": 12345
  }
}' --client-secret
```

`clientId` is the CLI's own local callback URL, not the Home Assistant URL.
Home Assistant uses IndieAuth, so no client ID is pre-registered.

Where the client cannot reach a public URL, or does not speak Streamable HTTP,
bridge with `mcp-proxy` 0.12.0 and a long-lived access token:

```json
{
  "mcpServers": {
    "homeassistant": {
      "command": "mcp-proxy",
      "args": [
        "--transport=streamablehttp",
        "--stateless",
        "http://homeassistant.local:8123/api/mcp"
      ],
      "env": {
        "API_ACCESS_TOKEN": "${HASS_TOKEN}"
      }
    }
  }
}
```

**Why**: the native server is the only path with a supported access-control
surface — the exposed-entities list and the integration's "Control Home
Assistant" switch. Community servers such as PyPI `mcp-homeassistant` 0.1.0 wrap
the raw REST API, so they inherit the token's full authority with no filtering.

The MCP server serves the Assist API, which covers entity state and control.
It does **not** cover history, logbook, template rendering or configuration
inspection. Use the REST endpoints below for those, and keep the two paths
distinct so the access model of each stays clear.

### Long-Lived Access Token

1. Go to Home Assistant -> Profile -> Security -> Long-Lived Access Tokens
2. Create the token **while signed in as the restricted agent user**, not as an
   owner or administrator
3. Store the token in secret management (SOPS, Vault, etc.)

The token's name is a label with no effect on authority. A token called
"Claude Agent - Read Only" created by an administrator can call every service
that administrator can call. Authority comes from the **user**, so the
restriction **MUST** be applied to the user account.

### CLI Access

```bash
# Using curl
HASS_URL="http://homeassistant.local:8123"
HASS_TOKEN="your_long_lived_token"

# Get all states
curl -s -H "Authorization: Bearer ${HASS_TOKEN}" \
  "${HASS_URL}/api/states" | jq

# Get specific entity
curl -s -H "Authorization: Bearer ${HASS_TOKEN}" \
  "${HASS_URL}/api/states/sensor.living_room_temperature"

# Call service (requires write access)
curl -X POST -H "Authorization: Bearer ${HASS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "light.kitchen"}' \
  "${HASS_URL}/api/services/light/turn_on"
```

## Access Levels

Home Assistant enforces access through **users and groups**, not through token
names. There are three built-in groups, defined in
`homeassistant/auth/permissions/system_policies.py`:

| Group ID | Name | Policy |
| -------- | ---- | ------ |
| `system-admin` | Administrators | `{"entities": true}` plus admin-only APIs |
| `system-users` | Users | `{"entities": true}` |
| `system-read-only` | Read Only | `{"entities": {"all": {"read": true}}}` |

| Level | How it is enforced | Use Case |
| ----- | ------------------ | -------- |
| `readonly` | Non-admin user in the **Read Only** group | Monitoring, debugging |
| `control` | Non-admin user in the **Users** group | Device management |
| `scoped` | Custom group policy, or MCP exposed entities | Restricted control |
| `admin` | Administrator user | Setup, maintenance |

There is no built-in tier that grants "read plus trigger automations" and
nothing else. Building one requires a custom group policy or a filtering proxy.

### Creating a Restricted Agent User

```text
Settings -> People -> Users -> Add User
  Name:                  Claude Agent
  Can only log in from the local network:  optional
  Advanced mode:         off
  Administrator:         OFF          <- required
```

Then assign the group. The UI exposes Administrator as a toggle; assigning
**Read Only** is done through the user's group membership.

Verify the result rather than trusting the label:

```bash
# Must fail with 401 Unauthorized for a Read Only user
curl -s -o /dev/null -w '%{http_code}\n' -X POST \
  -H "Authorization: Bearer ${HASS_AGENT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "light.kitchen"}' \
  "${HASS_URL}/api/services/light/turn_on"
```

**Why**: a long-lived access token inherits the authority of the user who
created it, for as long as it exists. Naming it "Read Only" changes nothing,
and neither does declaring `auth_providers` in `configuration.yaml` — that
setting selects *how* users log in, not *what* they may do.

Two limitations **MUST** be stated to whoever relies on this:

- Permissions never apply to the **owner** account. An owner always has full
  access, whatever the group policy says.
- Per-entity policies are applied by Home Assistant's API layer. Some APIs
  remain reachable to all users with a reduced scope, so a restricted user is
  not equivalent to a network-level block.

### Scoping the MCP Server

For MCP clients, the exposed-entities list is the enforcement point:

```text
Settings -> Voice assistants -> Expose
  - Expose only the entities the agent needs
  - Clear everything else
Settings -> Devices & services -> Model Context Protocol Server -> Configure
  - "Control Home Assistant": off for a monitoring agent
```

Non-administrator users may use the Assist API at `/api/mcp` and
`/api/mcp/assist`. Connecting to any other LLM API at `/api/mcp/<api_id>`
requires an administrator.

## Capabilities

| Capability | API Endpoint | Description |
| ---------- | ------------ | ----------- |
| `get_states` | `GET /api/states` | All entity states |
| `get_state` | `GET /api/states/{entity_id}` | Single entity state |
| `get_history` | `GET /api/history/period` | Historical states |
| `get_logbook` | `GET /api/logbook` | Event log |
| `get_config` | `GET /api/config` | HA configuration |
| `list_services` | `GET /api/services` | Available services |
| `call_service` | `POST /api/services/{domain}/{service}` | Execute service |
| `fire_event` | `POST /api/events/{event_type}` | Fire event |
| `get_template` | `POST /api/template` | Render template |

## Query Patterns for Agents

### Get All Entities by Domain

```bash
# All lights
curl -s -H "Authorization: Bearer ${HASS_TOKEN}" \
  "${HASS_URL}/api/states" | \
  jq '[.[] | select(.entity_id | startswith("light."))]'

# All sensors
curl -s -H "Authorization: Bearer ${HASS_TOKEN}" \
  "${HASS_URL}/api/states" | \
  jq '[.[] | select(.entity_id | startswith("sensor."))]'

# All automations
curl -s -H "Authorization: Bearer ${HASS_TOKEN}" \
  "${HASS_URL}/api/states" | \
  jq '[.[] | select(.entity_id | startswith("automation."))]'
```

### Get Entity History

```bash
# Temperature history for last 24 hours
curl -s -H "Authorization: Bearer ${HASS_TOKEN}" \
  "${HASS_URL}/api/history/period?filter_entity_id=sensor.living_room_temperature" | \
  jq '.[0] | map({state, last_changed})'
```

### Render Template

```bash
# Complex query using Jinja2 template
curl -s -X POST -H "Authorization: Bearer ${HASS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "template": "{% set lights = states.light | selectattr(\"state\", \"eq\", \"on\") | list %}{{ lights | length }} lights on: {{ lights | map(attribute=\"name\") | join(\", \") }}"
  }' \
  "${HASS_URL}/api/template"
```

### Check Automation Status

```bash
# Get automation details
curl -s -H "Authorization: Bearer ${HASS_TOKEN}" \
  "${HASS_URL}/api/states/automation.motion_lights" | jq '{
    state: .state,
    last_triggered: .attributes.last_triggered,
    mode: .attributes.mode,
    friendly_name: .attributes.friendly_name
  }'
```

## Example Usage

### Home Status Report

```markdown
Agent task: "Give me a status report of the home"

Response:

## Home Status Report - 2025-01-02 10:30

### Climate
| Zone | Temperature | Humidity | HVAC |
|------|-------------|----------|------|
| Living Room | 21.5°C | 45% | Heating |
| Bedroom | 19.2°C | 52% | Off |
| Kitchen | 22.1°C | 38% | Off |

### Lighting
- 3 lights on: Kitchen (80%), Hallway (100%), Office (60%)
- 12 lights off

### Security
- All doors: Closed ✓
- All windows: Closed ✓
- Alarm: Armed (Away mode)
- Motion: No activity (15 min)

### Energy
- Current power: 1,234W
- Today's usage: 12.5 kWh
- Solar generation: 0W (night)

### Issues Detected
- ⚠️ Garage door sensor: Unavailable (last seen 2h ago)
- ⚠️ Battery low: Motion sensor hallway (15%)
```

### Automation Debugging

```markdown
Agent task: "The motion light automation isn't working. Debug it."

Investigation:

1. **Automation State**
   - automation.motion_hallway_light: `on`
   - Last triggered: Never
   - Mode: single

2. **Trigger Entity**
   - binary_sensor.hallway_motion: `off`
   - Last changed: 2 hours ago
   - Device class: motion

3. **Action Entity**
   - light.hallway: `off`
   - Available: `true`

4. **Trace Analysis**
   Checking automation traces...
   - No traces found (automation never triggered)

5. **Root Cause**
   Motion sensor hasn't changed state in 2 hours.
   Checking sensor:
   - Battery: 5% ⚠️
   - RSSI: -85 dBm (weak)

**Diagnosis**: Motion sensor battery critically low, not detecting motion.

**Recommendation**:
1. Replace motion sensor battery
2. Consider adding battery monitoring automation
```

### Energy Analysis

```markdown
Agent task: "Analyze our energy usage patterns"

Analysis:

## Energy Usage Analysis

### Daily Pattern (Last 7 Days)
| Hour | Avg Usage | Peak Day |
|------|-----------|----------|
| 00-06 | 0.8 kWh | Fri (1.2) |
| 06-09 | 2.1 kWh | Mon (2.8) |
| 09-17 | 1.5 kWh | Wed (2.1) |
| 17-21 | 3.2 kWh | Sat (4.1) |
| 21-00 | 1.8 kWh | Sun (2.3) |

### Top Consumers
1. HVAC: 45% (8.2 kWh/day avg)
2. Water Heater: 20% (3.6 kWh/day)
3. Kitchen: 15% (2.7 kWh/day)
4. Entertainment: 10% (1.8 kWh/day)
5. Other: 10% (1.8 kWh/day)

### Recommendations
1. **HVAC Optimization**
   - Current: Running 18 hours/day
   - Suggestion: Reduce overnight temp by 2°C
   - Estimated savings: 15%

2. **Standby Power**
   - Detected: 120W constant draw
   - Sources: TV, game console, chargers
   - Suggestion: Smart power strips
```

## Agents That Use This Skill

| Agent | Access | Purpose |
| ----- | ------ | ------- |
| `system/home-monitor` | readonly | Status monitoring, alerts |
| `ops/home-automation` | automation | Debug automations |
| `security/home-security` | readonly | Security monitoring |
| `code/ha-developer` | readonly | Help develop automations |

## Graceful Degradation

| If Missing | Fallback |
| ---------- | -------- |
| HA unavailable | Query MQTT directly for device states |
| History unavailable | Use current state only |
| Specific integration down | Report as unavailable |

## Security Considerations

### Token Security

- **MUST** use long-lived tokens, not passwords
- **MUST** store tokens in secret management (SOPS)
- **SHOULD** create dedicated tokens per agent
- **MUST** rotate tokens periodically

### Access Restrictions

```yaml
# Restrict agent access to specific entities
# Use Home Assistant's built-in entity permissions

# Or create a proxy that filters:
allowed_domains:
  - sensor
  - binary_sensor
  - climate
  - light
  - switch
  - automation

denied_domains:
  - camera          # Privacy
  - device_tracker  # Privacy
  - person          # Privacy
  - alarm_control_panel  # Security-critical
```

### Action Safety

Approval **MUST** be decided by the resolved target and its physical effect,
never by the service name alone.

```yaml
# Require approval for actions
action_approval:
  always_require:
    - alarm_control_panel.*
    - lock.*
    - cover.garage*

  require_if_away:
    - light.*
    - switch.*
    - climate.*

  # No blanket auto-approval. automation.trigger and script.turn_on are
  # indirections: resolve the automation or script first, and apply the
  # rules above to every action it performs.
  resolve_before_approval:
    - automation.trigger
    - script.*
    - scene.apply
    - scene.turn_on
```

`automation.trigger` runs the automation's action block, and a script runs
whatever it contains. Either can call `lock.unlock` or
`alarm_control_panel.disarm`, so auto-approving them re-authorises exactly the
actions the list above restricts.

**Why**: the guard has to sit on the effect, not on the entry point. A rule
keyed to `lock.*` is bypassed by any script that calls `lock.unlock` if scripts
are pre-approved as a class.

Where the resolved actions cannot be enumerated in advance, the call **MUST**
be treated as requiring approval.

### Rate Limiting

Home Assistant has no per-token API rate-limit setting. Limits **MUST** be
implemented in the agent client or in a reverse proxy in front of Home
Assistant; the block below is client-side policy, not Home Assistant
configuration.

```yaml
# Client-side policy, enforced by the agent or an intermediary proxy.
# Home Assistant does not read this.
client_rate_limits:
  api_calls: 100/minute
  service_calls: 10/minute
  history_queries: 5/minute
```

## Complex Installation Patterns

### Multi-Instance Setup

```yaml
# Multiple Home Assistant instances
instances:
  main:
    url: http://homeassistant.local:8123
    token: ${HASS_MAIN_TOKEN}
    purpose: Primary home

  cabin:
    url: http://cabin-ha.vpn:8123
    token: ${HASS_CABIN_TOKEN}
    purpose: Vacation property

  office:
    url: http://office-ha.local:8123
    token: ${HASS_OFFICE_TOKEN}
    purpose: Office building
```

### Add-on Integration

Common add-ons agents might query:

```yaml
addons:
  # Zigbee2MQTT - query via MQTT skill
  zigbee2mqtt:
    access: mqtt://emqx/zigbee2mqtt/#

  # Node-RED - query via HA API
  nodered:
    access: ${HASS_URL}/api/states/switch.nodered_*

  # ESPHome - query via HA API
  esphome:
    access: ${HASS_URL}/api/states/sensor.esphome_*

  # InfluxDB - query directly for history
  influxdb:
    access: http://influxdb:8086
    skill: influxdb
```

### Supervisor API (Advanced)

These calls only work **from inside a Home Assistant app (add-on) container**.
`SUPERVISOR_TOKEN` is injected into the app's environment by the Supervisor; it
does not exist in an ordinary shell, and `http://supervisor/` does not resolve
outside the Supervisor network. An agent running on a workstation **MUST** use
the Core REST API on port 8123 instead.

Declare the grants the app needs in its `config.yaml`:

```yaml
# Add-on config.yaml
homeassistant_api: true   # unlocks http://supervisor/core/api/
hassio_api: true          # unlocks the rest of http://supervisor/
hassio_role: default      # raise only if a specific endpoint requires it
```

```bash
# Inside the app container. SUPERVISOR_TOKEN is provided by the Supervisor.
curl -s -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
  "http://supervisor/core/api/states" | jq

curl -s -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
  "http://supervisor/addons" | jq

curl -s -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
  "http://supervisor/info" | jq
```

A documented subset is reachable without `hassio_api: true`: `/core/api`,
`/core/api/stream`, `/core/websocket`, `/addons/self/*`, `/services*`,
`/discovery*` and `/info`. `/addons` is not in that subset, so the middle call
above needs the grant.

**Why**: naming the grants makes the app's authority auditable. `hassio_api`
opens the Supervisor control plane, which can start, stop and reconfigure every
app on the system — a much larger surface than reading entity states.

## Template Examples

Useful templates for agent queries:

```jinja2
{# Count devices by domain #}
{% set domains = states | map(attribute='domain') | unique | list %}
{% for domain in domains %}
{{ domain }}: {{ states[domain] | list | length }}
{% endfor %}

{# Find unavailable entities #}
{% set unavailable = states | selectattr('state', 'eq', 'unavailable') | list %}
Unavailable entities ({{ unavailable | length }}):
{% for entity in unavailable %}
- {{ entity.entity_id }}
{% endfor %}

{# Battery levels below threshold #}
{# states() returns strings, so '9' < '20' is false and '100' < '20' is
   true under a string comparison. Convert to a number and reject
   non-numeric states explicitly. #}
{% set ns = namespace(low=[], bad=[]) %}
{% for s in states.sensor
     | selectattr('attributes.device_class', 'eq', 'battery') %}
  {% if s.state not in ['unknown', 'unavailable', ''] and
        s.state | float(-1) >= 0 %}
    {% if s.state | float < 20 %}
      {% set ns.low = ns.low + [s] %}
    {% endif %}
  {% else %}
    {% set ns.bad = ns.bad + [s] %}
  {% endif %}
{% endfor %}
Low battery ({{ ns.low | length }}):
{% for sensor in ns.low %}
- {{ sensor.name }}: {{ sensor.state }}%
{% endfor %}
Unreadable ({{ ns.bad | length }}):
{% for sensor in ns.bad %}
- {{ sensor.name }}: {{ sensor.state }}
{% endfor %}

{# Lights on with brightness #}
{# The brightness attribute is 0-255, not a percentage. #}
{% set lights_on = states.light | selectattr('state', 'eq', 'on') | list %}
Lights on: {{ lights_on | length }}
{% for light in lights_on %}
{% set b = light.attributes.brightness | default(none) %}
{% if b is none %}
- {{ light.name }}: on (not dimmable)
{% else %}
- {{ light.name }}: {{ (b | float(0) / 255 * 100) | round(0) | int }}%
{% endif %}
{% endfor %}
```

Both templates above were rendered against fixtures covering `9`, `15`, `100`,
`unknown`, `unavailable` and an empty state. The original string comparison
selected `100` and `15` as low while excluding `9`; the corrected version
selects `9` and `15` and reports the three unreadable sensors separately.
The original brightness line printed `128%` and `255%`; the corrected version
prints `50%` and `100%`.
