# Zigbee2MQTT Skill

Provides direct access to Zigbee devices via Zigbee2MQTT, enabling device
management, monitoring, and debugging beyond what Home Assistant exposes.

## Overview

| Attribute | Value |
| --------- | ----- |
| **Category** | IoT / Zigbee |
| **Protocol** | MQTT (via Zigbee2MQTT bridge) |
| **Default Access** | subscribe (readonly) |
| **Risk Level** | Medium (can affect device pairings) |

## Architecture

```text
+-------------------------------------------------------------------------+
|                      ZIGBEE2MQTT ARCHITECTURE                           |
+-------------------------------------------------------------------------+
|                                                                         |
|   +----------+     +--------------+     +----------+     +----------+   |
|   |  Zigbee  |---->|  Zigbee2MQTT |---->|   MQTT   |---->|  Agent   |   |
|   | Devices  |     |   Bridge     |     |  Broker  |     |          |   |
|   +----------+     +--------------+     +----------+     +----------+   |
|                                                                         |
|   Topics:                                                               |
|   - zigbee2mqtt/{device}           - Device state                       |
|   - zigbee2mqtt/{device}/set       - Control device                     |
|   - zigbee2mqtt/{device}/get       - Request state                      |
|   - zigbee2mqtt/bridge/...         - Bridge management                  |
|                                                                         |
+-------------------------------------------------------------------------+
```

## Configuration

### Via MQTT Skill

Zigbee2MQTT uses MQTT, so configure via the MQTT skill:

```json
{
  "mcpServers": {
    "mqtt": {
      "command": "mcp-mqtt",
      "env": {
        "MQTT_BROKER": "${MQTT_BROKER_URL}",
        "MQTT_USERNAME": "${MQTT_USERNAME}",
        "MQTT_PASSWORD": "${MQTT_PASSWORD}"
      }
    }
  }
}
```

### CLI Access

```bash
# Subscribe to all Zigbee2MQTT messages
mosquitto_sub -h emqx.local -t "zigbee2mqtt/#" -v

# Get specific device state
mosquitto_sub -h emqx.local -t "zigbee2mqtt/living_room_sensor" -C 1

# Request device state update
mosquitto_pub -h emqx.local -t "zigbee2mqtt/living_room_sensor/get" \
  -m '{"state": ""}'

# Control device (requires write access)
mosquitto_pub -h emqx.local -t "zigbee2mqtt/kitchen_light/set" \
  -m '{"state": "ON", "brightness": 200}'
```

## Access Levels

| Level | Topics | Use Case |
| ----- | ------ | -------- |
| `subscribe` | `zigbee2mqtt/+`, `zigbee2mqtt/bridge/state` | Monitoring |
| `publish-get` | Above + `zigbee2mqtt/+/get` | Active polling |
| `publish-set` | Above + `zigbee2mqtt/+/set` | Device control |
| `bridge-admin` | Above + `zigbee2mqtt/bridge/request/*` | Pairing, config |

### MQTT ACL for Agents

```yaml
# EMQX ACL
acl:
  - username: claude-agent
    permission: allow
    action: subscribe
    topics:
      - "zigbee2mqtt/+"
      - "zigbee2mqtt/+/availability"
      - "zigbee2mqtt/bridge/state"
      - "zigbee2mqtt/bridge/info"
      - "zigbee2mqtt/bridge/devices"
      - "zigbee2mqtt/bridge/groups"
      - "zigbee2mqtt/bridge/logging"

  - username: claude-agent
    permission: allow
    action: publish
    topics:
      - "zigbee2mqtt/+/get"
      - "zigbee2mqtt/bridge/request/health_check"

  # Deny control by default
  - username: claude-agent
    permission: deny
    action: publish
    topics:
      - "zigbee2mqtt/+/set"
      - "zigbee2mqtt/bridge/request/permit_join"
      - "zigbee2mqtt/bridge/request/device/remove"
```

## Topic Reference

### Device Topics

```yaml
# Device state (published by Z2M)
zigbee2mqtt/{friendly_name}:
  # Varies by device type
  # Sensor example:
  temperature: 21.5
  humidity: 45
  battery: 85
  linkquality: 120
  voltage: 2900

  # Light example:
  state: "ON"
  brightness: 254
  color_temp: 350
  color:
    x: 0.123
    y: 0.456

  # Contact sensor:
  contact: true
  battery: 90
  linkquality: 89

# Device availability
zigbee2mqtt/{friendly_name}/availability:
  "online" | "offline"

# Request state update
zigbee2mqtt/{friendly_name}/get:
  {"state": "", "brightness": ""}  # Empty values = request

# Set device state
zigbee2mqtt/{friendly_name}/set:
  {"state": "ON", "brightness": 200}
```

### Bridge Topics

```yaml
# Bridge state
zigbee2mqtt/bridge/state:
  "online" | "offline"

# Bridge info
zigbee2mqtt/bridge/info:
  coordinator:
    ieee_address: "0x00124b001cd..."
    type: "zStack3x0"
  version: "1.33.0"
  config:
    homeassistant: true
    permit_join: false
  network:
    channel: 15
    pan_id: 6754
    extended_pan_id: [221, 221, ...]

# All devices
zigbee2mqtt/bridge/devices:
  - ieee_address: "0x00158d000..."
    friendly_name: "living_room_sensor"
    type: "EndDevice"
    definition:
      vendor: "Xiaomi"
      model: "WSDCGQ11LM"
      description: "Aqara temperature sensor"
    power_source: "Battery"
    battery: 85
    linkquality: 120

# Groups
zigbee2mqtt/bridge/groups:
  - id: 1
    friendly_name: "living_room_lights"
    members:
      - ieee_address: "0x00158d000..."
        endpoint: 1

# Bridge logging
zigbee2mqtt/bridge/logging:
  level: "info"
  message: "Device 'kitchen_motion' joined"
```

### Bridge Requests

```yaml
# Health check
zigbee2mqtt/bridge/request/health_check: {}

# Get network map
zigbee2mqtt/bridge/request/networkmap:
  type: "raw"  # or "graphviz"
  routes: true

# Permit join (admin only)
zigbee2mqtt/bridge/request/permit_join:
  value: true
  time: 120  # seconds

# Device interview
zigbee2mqtt/bridge/request/device/interview:
  id: "0x00158d000..."

# Rename device
zigbee2mqtt/bridge/request/device/rename:
  from: "0x00158d000..."
  to: "kitchen_sensor"

# Remove device (admin only)
zigbee2mqtt/bridge/request/device/remove:
  id: "kitchen_sensor"
  force: false
```

## Query Patterns for Agents

### Device Inventory

```bash
# Get all devices
mosquitto_sub -h emqx.local -t "zigbee2mqtt/bridge/devices" -C 1 | \
  jq '.[] | {name: .friendly_name, vendor: .definition.vendor, model: .definition.model, battery: .battery}'
```

### Network Health

```bash
# Check link quality across network
mosquitto_sub -h emqx.local -t "zigbee2mqtt/bridge/devices" -C 1 | \
  jq '.[] | {name: .friendly_name, lqi: .linkquality, battery: .battery}' | \
  jq -s 'sort_by(.lqi)'
```

### Device Status

```bash
# Get specific device state
mosquitto_pub -h emqx.local -t "zigbee2mqtt/kitchen_sensor/get" -m '{"state": ""}'
mosquitto_sub -h emqx.local -t "zigbee2mqtt/kitchen_sensor" -C 1
```

## Example Usage

### Device Health Report

```markdown
Agent task: "Report on Zigbee network health"

## Zigbee Network Health Report

### Network Info
- Coordinator: CC2652P (zStack3x0)
- Channel: 15
- Devices: 47 total (12 routers, 35 end devices)

### Device Status
| Status | Count | Details |
|--------|-------|---------|
| Online | 44 | Normal operation |
| Offline | 3 | See below |
| Low Battery | 5 | < 20% |
| Weak Signal | 8 | LQI < 50 |

### Offline Devices
| Device | Last Seen | Type |
|--------|-----------|------|
| garage_door_sensor | 3 hours ago | Contact |
| basement_motion | 12 hours ago | Motion |
| outdoor_temp | 2 days ago | Temp/Humidity |

### Low Battery Devices
| Device | Battery | Last Changed |
|--------|---------|--------------|
| bedroom_motion | 12% | 3 months ago |
| front_door_sensor | 15% | 2 months ago |
| mailbox_sensor | 8% | 4 months ago |

### Weak Signal Devices
| Device | LQI | Nearest Router |
|--------|-----|----------------|
| shed_sensor | 23 | garage_outlet (LQI: 45) |
| garden_motion | 31 | patio_light (LQI: 67) |

### Recommendations
1. Replace batteries: mailbox_sensor (critical), bedroom_motion
2. Check outdoor_temp - may need re-pairing
3. Add router near shed to improve mesh
```

### Troubleshooting Device

Agent task: "The kitchen motion sensor isn't triggering automations"

Investigation: `kitchen_motion`

Device Info:

- Model: Philips Hue Motion (9290012607)
- IEEE: 0x00178801088...
- Type: EndDevice
- Power: Battery (67%)

Current State:

```json
{
  "occupancy": false,
  "illuminance_lux": 142,
  "temperature": 22.3,
  "battery": 67,
  "linkquality": 89
}
```

Message History (last hour):

| Time | Occupancy | LQI |
| ---- | --------- | --- |
| 10:15 | true | 89 |
| 10:16 | false | 87 |
| 10:45 | true | 91 |
| 10:46 | false | 89 |

Analysis:

- Device IS reporting occupancy changes
- Good link quality (89)
- Battery adequate (67%)

Root Cause: The device is working correctly at the Zigbee level. The issue is
likely in Home Assistant automation, not the device.

Next steps:

1. Check Home Assistant automation state
2. Verify automation trigger conditions
3. Review recent HA config changes

### Network Visualization

```markdown
Agent task: "Show me the Zigbee mesh topology"

## Zigbee Network Topology

### Coordinator
└── CC2652P (Channel 15)

### Router Devices (12)
├── living_room_outlet (LQI: 255)
│   ├── living_room_sensor (LQI: 120)
│   ├── tv_backlight (LQI: 200)
│   └── window_sensor_1 (LQI: 89)
├── kitchen_outlet (LQI: 234)
│   ├── kitchen_motion (LQI: 89)
│   ├── fridge_sensor (LQI: 145)
│   └── stove_sensor (LQI: 167)
├── hallway_light (LQI: 220)
│   ├── front_door_sensor (LQI: 156)
│   └── hallway_motion (LQI: 189)
...

### Weak Links (LQI < 50)
- shed_sensor → garage_outlet: LQI 23 ⚠️
- garden_motion → patio_light: LQI 31 ⚠️

### Recommendation
Add a router device (smart plug) in the garage to strengthen
the mesh connection to outdoor devices.
```

## Agents That Use This Skill

| Agent | Access | Purpose |
| ----- | ------ | ------- |
| `system/iot-monitor` | subscribe | Device health monitoring |
| `ops/home-automation` | publish-get | Debugging, testing |
| `security/iot-security` | subscribe | Anomaly detection |

## Graceful Degradation

| If Missing | Fallback |
| ---------- | -------- |
| Z2M bridge offline | Alert, check coordinator |
| Specific device offline | Check battery, signal, last seen |
| MQTT broker down | Query Home Assistant API |

## Security Considerations

### Network Security

- **MUST** use TLS for MQTT connections
- **SHOULD** isolate Zigbee network from other IoT
- **MUST** disable permit_join when not pairing
- **SHOULD** monitor for unknown devices

### Agent Restrictions

```yaml
# Agents should NOT:
agent_restrictions:
  - permit_join         # Could allow rogue devices
  - device/remove       # Could break automations
  - device/configure    # Could misconfigure devices
  - touchlink/factory_reset  # Destructive

# Agents MAY (with approval):
agent_allowed_with_approval:
  - device/rename       # Safe rename
  - device/interview    # Re-interview stuck device
```

### Monitoring for Anomalies

```yaml
# Alert on suspicious activity
alerts:
  - name: unknown_device_joined
    topic: zigbee2mqtt/bridge/event
    condition: type == "device_joined" AND NOT in_known_devices
    action: alert_security

  - name: permit_join_enabled
    topic: zigbee2mqtt/bridge/info
    condition: config.permit_join == true
    action: alert_if_unexpected

  - name: coordinator_offline
    topic: zigbee2mqtt/bridge/state
    condition: state == "offline"
    action: alert_critical
```

## Device Database

Common device patterns for agent reference:

### Sensors

```yaml
temperature_humidity:
  vendors: [Xiaomi, Sonoff, Tuya]
  exposes: [temperature, humidity, battery, voltage, linkquality]
  update_interval: 5-60 min (configurable)

motion:
  vendors: [Philips, Xiaomi, Ikea]
  exposes: [occupancy, illuminance, battery, temperature]
  cooldown: 60-120 sec typical

contact:
  vendors: [Xiaomi, Sonoff, Tuya]
  exposes: [contact, battery, voltage]
  reports: on state change
```

### Actuators

```yaml
light:
  vendors: [Philips, Ikea, Innr]
  exposes: [state, brightness, color_temp, color_xy]
  features: [transition, effect]

switch:
  vendors: [Sonoff, Tuya, Xiaomi]
  exposes: [state, power, voltage, current, energy]
  may_include: power_monitoring

cover:
  vendors: [Tuya, Zemismart]
  exposes: [state, position, tilt]
  commands: [open, close, stop, goto]
```
