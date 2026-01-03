# IoT Skills

Skills for interacting with IoT devices, home automation systems, and sensor
networks.

## Architecture Overview

```text
+-----------------------------------------------------------------------------+
|                          IOT SKILL STACK                                    |
+-----------------------------------------------------------------------------+
|                                                                             |
|   +---------------------------------------------------------------------+   |
|   |                    HOME ASSISTANT                                   |   |
|   |              (Unified Smart Home Platform)                          |   |
|   |   - Entity management    - Automations    - Dashboards              |   |
|   +---------------------------------------------------------------------+   |
|                    |                    |                    |              |
|                    v                    v                    v              |
|   +------------------+   +------------------+   +------------------+        |
|   |   ZIGBEE2MQTT    |   |     ESPHOME      |   |   OTHER ADD-ONS  |        |
|   |  (Zigbee Bridge) |   |  (ESP Devices)   |   |  (Z-Wave, etc.)  |        |
|   +------------------+   +------------------+   +------------------+        |
|           |                      |                      |                   |
|           +----------------------+----------------------+                   |
|                                  v                                          |
|   +---------------------------------------------------------------------+   |
|   |                        MQTT / EMQX                                  |   |
|   |                    (Message Transport)                              |   |
|   |   - Pub/Sub messaging    - Topic routing    - Device telemetry     |   |
|   +---------------------------------------------------------------------+   |
|                                  |                                          |
|                                  v                                          |
|   +---------------------------------------------------------------------+   |
|   |                      PHYSICAL DEVICES                               |   |
|   |  Zigbee: Sensors, Lights, Switches    ESP: Custom sensors, relays  |   |
|   |  WiFi: Smart plugs, cameras           Other: Z-Wave, Thread, etc.  |   |
|   +---------------------------------------------------------------------+   |
|                                                                             |
+-----------------------------------------------------------------------------+
```

## Available Skills

| Skill | Protocol | Primary Use Case |
| ----- | -------- | ---------------- |
| [MQTT / EMQX](mqtt.md) | MQTT 3.1.1/5.0 | Raw device messaging, telemetry |
| [Home Assistant](homeassistant.md) | REST/WebSocket | Unified home control, automations |
| [Zigbee2MQTT](zigbee2mqtt.md) | MQTT | Zigbee device management |
| [ESPHome](esphome.md) | Native API/MQTT/REST | ESP device debugging, OTA |
| [Tasmota](tasmota.md) | MQTT/HTTP | Power monitoring, Sonoff devices |

## Access Patterns

### Query Flow by Task

| Task | Primary Skill | Fallback |
| ---- | ------------- | -------- |
| "What's the temperature?" | Home Assistant | MQTT direct |
| "Why won't the light turn on?" | Zigbee2MQTT | Home Assistant logs |
| "Is the sensor online?" | MQTT (LWT) | ESPHome logs |
| "Debug the ESP device" | ESPHome | MQTT + Serial |
| "Show device battery levels" | Zigbee2MQTT | Home Assistant |
| "Analyze energy usage" | Home Assistant | MQTT history |

### Protocol Selection

```text
Home Assistant API
+-- Best for: Unified queries, automation state, entity history
+-- Access: REST API with long-lived token
+-- Example: "Show all lights that are on"

MQTT Direct
+-- Best for: Real-time telemetry, raw device data
+-- Access: MQTT subscribe/publish
+-- Example: "Stream temperature sensor data"

Zigbee2MQTT
+-- Best for: Zigbee-specific diagnostics, network topology
+-- Access: MQTT (zigbee2mqtt/# topics)
+-- Example: "Show Zigbee mesh network health"

ESPHome
+-- Best for: ESP device debugging, firmware, OTA
+-- Access: Dashboard API, Native API, or MQTT
+-- Example: "Check ESP device memory usage"
```

## Common Agent Tasks

### Device Health Monitoring

```markdown
Agent: system/iot-monitor
Skills: mqtt (subscribe), homeassistant (readonly)

Tasks:
1. Monitor device availability via MQTT LWT
2. Check battery levels via Zigbee2MQTT
3. Alert on devices offline > 1 hour
4. Report WiFi signal strength for ESP devices
```

### Automation Debugging

```markdown
Agent: ops/home-automation
Skills: homeassistant (readonly), zigbee2mqtt (subscribe), esphome (logs)

Tasks:
1. Check automation trigger conditions
2. Trace message flow through MQTT
3. Verify device states match expectations
4. Identify timing issues in automations
```

### Network Diagnostics

```markdown
Agent: system/iot-monitor
Skills: zigbee2mqtt (subscribe), mqtt (subscribe)

Tasks:
1. Map Zigbee mesh topology
2. Identify weak signal devices
3. Find routing bottlenecks
4. Recommend router placement
```

## Security Model

### Access Levels by Skill

| Skill | Default | Elevated | Admin |
| ----- | ------- | -------- | ----- |
| MQTT | subscribe | publish-get | publish-set |
| Home Assistant | readonly | automation | control |
| Zigbee2MQTT | subscribe | publish-get | bridge-admin |
| ESPHome | readonly | logs | admin (OTA) |

### Restricted Actions

```yaml
# Actions that MUST require human approval
restricted_actions:
  # Home Assistant
  - alarm_control_panel.*     # Security critical
  - lock.*                    # Physical security
  - cover.garage*             # Physical access

  # Zigbee2MQTT
  - permit_join               # Could allow rogue devices
  - device/remove             # Could break automations

  # ESPHome
  - ota_flash                 # Could brick device
  - factory_reset             # Data loss
  - wifi_reconfigure          # Could lose device

  # MQTT
  - commands/+/set            # Direct device control
  - config/#                  # Device configuration
```

### Network Isolation

```yaml
# Recommended VLAN setup
vlans:
  iot:
    id: 30
    subnet: 10.0.30.0/24
    devices:
      - zigbee_coordinator
      - esphome_devices
      - wifi_sensors
    allowed_access:
      - mqtt_broker
      - home_assistant
      - esphome_dashboard
    blocked:
      - internet              # No cloud access
      - management_vlan       # Isolated from infra
```

## Graceful Degradation

```text
+-------------------------------------------------------------+
|                    DEGRADATION CHAIN                        |
+-------------------------------------------------------------+
|                                                             |
|   Home Assistant Down?                                      |
|   +-- Query MQTT directly for device states                 |
|       +-- Query ESPHome devices directly via Native API     |
|           +-- Check Zigbee2MQTT for Zigbee devices          |
|                                                             |
|   MQTT Broker Down?                                         |
|   +-- Query Home Assistant API (if available)               |
|       +-- Query ESPHome REST API directly                   |
|           +-- SSH to HA and check local state               |
|                                                             |
|   Specific Device Offline?                                  |
|   +-- Check last known state in Home Assistant              |
|       +-- Check MQTT retained messages                      |
|           +-- Report as unavailable with last seen time     |
|                                                             |
+-------------------------------------------------------------+
```

## Example: Full Stack Debug

```markdown
User: "The kitchen motion sensor isn't triggering the lights"

Agent Investigation:

1. **Home Assistant** (automation state)
   - automation.kitchen_motion_lights: ON
   - Last triggered: Never
   - Mode: single

2. **Zigbee2MQTT** (device state)
   - binary_sensor.kitchen_motion
   - Device: Philips Hue Motion
   - Battery: 67%
   - LQI: 89 (good)
   - Last state change: 2 hours ago

3. **MQTT** (message flow)
   - Subscribe to zigbee2mqtt/kitchen_motion
   - No messages received in test period
   - Motion detected but no MQTT publish?

4. **Root Cause**
   - PIR sensor cooldown set to 120 seconds
   - Sensor detected motion, entered cooldown
   - Subsequent motion ignored

5. **Fix**
   - Reduce cooldown via Zigbee2MQTT config
   - Or adjust automation to use occupancy instead of motion
```

## Agents Using IoT Skills

| Agent | Skills | Purpose |
| ----- | ------ | ------- |
| `system/iot-monitor` | mqtt, homeassistant, zigbee2mqtt, esphome | Device health |
| `ops/home-automation` | homeassistant, zigbee2mqtt, esphome | Automation debugging |
| `security/iot-security` | mqtt, zigbee2mqtt | Anomaly detection, rogue devices |
| `code/esphome-dev` | esphome | Help write ESPHome YAML |
| `code/ha-developer` | homeassistant | Help develop automations |
