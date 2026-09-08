# Zigbee2MQTT Skill

Provides direct access to Zigbee devices via Zigbee2MQTT, enabling device
management, monitoring, and debugging beyond what Home Assistant exposes.

## Overview

| Attribute | Value |
| --------- | ----- |
| **Category** | IoT / Zigbee |
| **Protocol** | MQTT (via Zigbee2MQTT bridge) |
| **Version** | Zigbee2MQTT 2.14.1 |
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

EMQX's file authoriser takes Erlang terms; see
[MQTT / EMQX](mqtt.md#topic-based-acl) for the file format, how to register it
as an authorization source, and why denied publishes are silent.

```erlang
%% acl.conf — Zigbee2MQTT agent rules
{deny,  {username, "claude-agent"}, publish,
        ["zigbee2mqtt/+/set",
         "zigbee2mqtt/bridge/request/permit_join",
         "zigbee2mqtt/bridge/request/device/remove"]}.
{allow, {username, "claude-agent"}, subscribe,
        ["zigbee2mqtt/+",
         "zigbee2mqtt/+/availability",
         "zigbee2mqtt/bridge/state",
         "zigbee2mqtt/bridge/info",
         "zigbee2mqtt/bridge/devices",
         "zigbee2mqtt/bridge/health",
         "zigbee2mqtt/bridge/groups",
         "zigbee2mqtt/bridge/logging"]}.
{allow, {username, "claude-agent"}, publish,
        ["zigbee2mqtt/+/get",
         "zigbee2mqtt/bridge/request/health_check"]}.
{deny, all}.
```

The deny rule comes first because EMQX applies the first matching rule.
`zigbee2mqtt/+/set` would otherwise never be reached.

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
# Zigbee2MQTT 2.x publishes an object, retained. Version 1.x published the
# bare strings "online"/"offline"; a v1-era consumer sees a JSON object and
# never matches.
zigbee2mqtt/{friendly_name}/availability:
  {"state": "online"} | {"state": "offline"}

# Request state update. Only properties the device actually supports can be
# read; Zigbee2MQTT logs "No converter available for '<property>'" and skips
# anything else. Battery sensors such as WSDCGQ11LM support no /get at all.
zigbee2mqtt/{friendly_name}/get:
  {"brightness": ""}  # Empty values = request

# Set device state
zigbee2mqtt/{friendly_name}/set:
  {"state": "ON", "brightness": 200}
```

### Bridge Topics

```yaml
# Bridge state (object payload, retained)
zigbee2mqtt/bridge/state:
  {"state": "online"} | {"state": "offline"}

# Bridge info. permit_join is top-level, NOT under config.
zigbee2mqtt/bridge/info:
  coordinator:
    ieee_address: "0x00124b001cd..."
    type: "zStack3x0"
  version: "2.14.1"
  permit_join: false
  permit_join_end: null
  config:
    homeassistant:
      enabled: true
  network:
    channel: 15
    pan_id: 6754
    extended_pan_id: [221, 221, ...]

# All devices — INVENTORY ONLY. There is no battery or linkquality here.
zigbee2mqtt/bridge/devices:
  - ieee_address: "0x00158d000..."
    friendly_name: "living_room_sensor"
    type: "EndDevice"
    supported: true
    disabled: false
    manufacturer: "LUMI"
    definition:
      vendor: "Aqara"
      model: "WSDCGQ11LM"
      description: "Temperature and humidity sensor"
    power_source: "Battery"

# Bridge health — counters, published every `health.interval` minutes
zigbee2mqtt/bridge/health:
  response_time: 1749991304357
  mqtt:
    connected: true
    published: 9
  devices:
    "0x00158d000...":
      leave_count: 1
      network_address_changes: 1
      messages: 4
      messages_per_sec: 0.0033

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
  namespace: "z2m"
```

Current measured values — `battery`, `linkquality`, `temperature` and the rest
— arrive only on each device's own state topic,
`zigbee2mqtt/{friendly_name}`, when the device reports. They are not in
`bridge/devices`.

### Bridge Requests

```yaml
# Health check
zigbee2mqtt/bridge/request/health_check: {}

# Get network map
zigbee2mqtt/bridge/request/networkmap:
  type: "raw"  # or "graphviz"
  routes: true

# Permit join (admin only). `time` is REQUIRED and is the only field that
# opens the network; a payload without it is rejected as "Invalid payload".
zigbee2mqtt/bridge/request/permit_join:
  time: 120  # seconds; 0 closes the network
  device: "living_room_router"  # optional: join via one router only

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

A `value: true` field is accepted but ignored. Older recipes pairing
`value: true` with `time: 120` appear to work only because `time` is valid on
its own; `value: true` alone does nothing.

## Query Patterns for Agents

### Device Inventory

`bridge/devices` is the inventory. It carries identity and capability, not
measurements:

```bash
# Get all devices
mosquitto_sub -h emqx.local -t "zigbee2mqtt/bridge/devices" -C 1 | jq -r '
  .[] | select(.type != "Coordinator")
      | {name: .friendly_name,
         vendor: .definition.vendor,
         model: .definition.model,
         power: .power_source}'
```

### Network Health

Battery and link quality arrive on each device's own state topic. Collect
inventory and live state separately, then join them by friendly name:

```bash
# 1. Inventory (retained, returns immediately)
mosquitto_sub -h emqx.local -t "zigbee2mqtt/bridge/devices" -C 1 \
  > devices.json

# 2. Live state, one line per message, topic preserved
timeout 300 mosquitto_sub -h emqx.local -v -t "zigbee2mqtt/+" \
  > states.txt

# 3. Join. Devices that reported nothing, or that expose no battery or
#    linkquality, come back null rather than being dropped.
jq -Rs '
  [ split("\n")[]
    | select(length > 0)
    | (index(" ")) as $i
    | {name: (.[0:$i] | split("/")[1]),
       payload: (.[$i+1:] | fromjson? // {})}
  ] | group_by(.name)
    | map({name: .[0].name,
           battery: (map(.payload.battery) | map(select(. != null)) | last),
           lqi: (map(.payload.linkquality) | map(select(. != null)) | last)})
' states.txt > live.json

jq -s '
  (.[0] | map(select(.type != "Coordinator"))) as $inv
  | (.[1] | INDEX(.name)) as $live
  | $inv | map({name: .friendly_name,
                model: .definition.model,
                battery: ($live[.friendly_name].battery),
                lqi: ($live[.friendly_name].lqi)})
  | sort_by(.lqi // 9999)
' devices.json live.json
```

`mosquitto_sub -v` prints `topic payload` on one line, so the pipeline splits
at the first space and parses only the remainder as JSON. Feeding the whole
line to `jq` yields a parse error, and dropping `-v` loses the device identity.

**Why**: the previous form read `.battery` and `.linkquality` from
`bridge/devices`, where neither field exists. Every device reported `null`, and
a report built on it silently claimed no device had a low battery.

Mains-powered devices expose no `battery`, and some devices report no
`linkquality`, so `null` is a normal result that **MUST NOT** be rendered as
zero.

### Bridge Counters

`bridge/health` carries per-device counters — messages seen, network-address
changes, how often a device left the network — published every
`health.interval` minutes:

```bash
mosquitto_sub -h emqx.local -t "zigbee2mqtt/bridge/health" -C 1 | jq -r '
  .devices | to_entries[]
  | select(.value.leave_count > 0 or .value.network_address_changes > 0)
  | {ieee: .key, leaves: .value.leave_count,
     addr_changes: .value.network_address_changes}'
```

### Topology and LQI

Per-neighbour link quality and routes come from the network map, not from any
state topic:

```bash
mosquitto_pub -h emqx.local -t "zigbee2mqtt/bridge/request/networkmap" \
  -m '{"type":"raw","routes":true}'
mosquitto_sub -h emqx.local -t "zigbee2mqtt/bridge/response/networkmap" -C 1 \
  | jq '.data.value.links | sort_by(.linkquality) | .[0:10]'
```

### Device Status

Only properties a device actually supports can be polled. `living_room_sensor`
in the inventory above is a WSDCGQ11LM, which defines no writable converters at
all, so every `/get` on it is skipped with
`No converter available for '<property>'`:

```bash
# Don't: this device supports no /get, and has no `state` property
mosquitto_pub -h emqx.local -t "zigbee2mqtt/living_room_sensor/get" \
  -m '{"state": ""}'
```

```bash
# Do: wait for the sensor's own report
mosquitto_sub -h emqx.local -t "zigbee2mqtt/living_room_sensor" -C 1 | jq

# Do: poll a device that documents a readable property, e.g. a bulb
mosquitto_pub -h emqx.local -t "zigbee2mqtt/kitchen_light/get" \
  -m '{"state": ""}'
mosquitto_sub -h emqx.local -t "zigbee2mqtt/kitchen_light" -C 1 | jq
```

Battery sensors sleep between reports, so a `/get` would not reach them even if
the property were readable. Check the device page on zigbee2mqtt.io: each
expose states whether `/get` and `/set` are possible.

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
    # permit_join is top-level in bridge/info, not under config.
    # `config.permit_join` is always undefined and never fires.
    condition: permit_join == true
    action: alert_if_unexpected

  - name: coordinator_offline
    topic: zigbee2mqtt/bridge/state
    # v2 publishes {"state":"offline"}, not the bare string "offline".
    condition: state.state == "offline"
    action: alert_critical
```

### Migrating from Zigbee2MQTT 1.x

| Concern | 1.x | 2.x |
| ------- | --- | --- |
| Device availability | `"online"` / `"offline"` | `{"state":"online"}` |
| Bridge state | `"online"` / `"offline"` | `{"state":"online"}` |
| Home Assistant discovery | `homeassistant: true` | `homeassistant.enabled: true` |
| Permit join in `bridge/info` | under `config` | top-level `permit_join` |
| Permit join request | `{"value":true,"time":120}` | `{"time":120}` |

A consumer written for 1.x does not error on 2.x payloads; it compares a JSON
object against a string, never matches, and reports every device as healthy.
Availability and bridge-state checks **MUST** be re-tested after upgrading.

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
