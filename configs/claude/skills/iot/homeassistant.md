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

```json
{
  "mcpServers": {
    "homeassistant": {
      "command": "mcp-homeassistant",
      "env": {
        "HASS_URL": "${HASS_URL}",
        "HASS_TOKEN": "${HASS_TOKEN}"
      }
    }
  }
}
```

### Long-Lived Access Token

1. Go to Home Assistant → Profile → Long-Lived Access Tokens
2. Create token with descriptive name: "Claude Agent - Read Only"
3. Store token securely (SOPS, Vault, etc.)

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

| Level | Permissions | Use Case |
| ----- | ----------- | -------- |
| `readonly` | Read states, history, config | Monitoring, debugging |
| `automation` | Read + trigger automations | Automation testing |
| `control` | Read + control devices | Full management |
| `admin` | Full access + configuration | Setup, maintenance |

### Scoped Access (Recommended)

Create dedicated users with limited access:

```yaml
# Home Assistant configuration.yaml
homeassistant:
  auth_providers:
    - type: homeassistant

# Create user with limited entity access
# Settings → People → Users → Add User
# Then use entity permissions or areas
```

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

  auto_approve:
    - automation.trigger  # Safe to test automations
    - script.*           # Pre-approved scripts
```

### Rate Limiting

```yaml
rate_limits:
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

```bash
# Query Supervisor for system status
curl -s -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
  "http://supervisor/core/api/states" | jq

# Get add-on status
curl -s -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
  "http://supervisor/addons" | jq

# Get system info
curl -s -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
  "http://supervisor/info" | jq
```

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
{% set low_battery = states.sensor
   | selectattr('attributes.device_class', 'eq', 'battery')
   | selectattr('state', 'lt', '20') | list %}
Low battery ({{ low_battery | length }}):
{% for sensor in low_battery %}
- {{ sensor.name }}: {{ sensor.state }}%
{% endfor %}

{# Lights on with power usage #}
{% set lights_on = states.light | selectattr('state', 'eq', 'on') | list %}
Lights on: {{ lights_on | length }}
{% for light in lights_on %}
- {{ light.name }}: {{ light.attributes.brightness | default(100) }}%
{% endfor %}
```
