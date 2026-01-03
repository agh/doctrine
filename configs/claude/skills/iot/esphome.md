# ESPHome Skill

Provides access to ESPHome devices for monitoring, debugging, configuration management, and OTA updates.

## Overview

| Attribute | Value |
| --------- | ----- |
| **Category** | IoT / ESP32/ESP8266 |
| **Protocol** | Native API, MQTT, REST |
| **Default Access** | readonly |
| **Risk Level** | Medium-High (can flash firmware) |

## Architecture

```text
+-------------------------------------------------------------------------+
|                        ESPHOME ARCHITECTURE                             |
+-------------------------------------------------------------------------+
|                                                                         |
|   +-------------------------------------------------------------------+ |
|   |                     ESPHome Dashboard                             | |
|   |                    (YAML configs, OTA)                            | |
|   +-------------------------------------------------------------------+ |
|                              |                                          |
|              +---------------+---------------+                          |
|              v               v               v                          |
|   +--------------+  +--------------+  +--------------+                  |
|   |   ESP32      |  |   ESP8266    |  |   ESP32-C3   |                  |
|   |   Device     |  |   Device     |  |   Device     |                  |
|   +--------------+  +--------------+  +--------------+                  |
|          |                 |                 |                          |
|          +-----------------+-----------------+                          |
|                            |                                            |
|              +-------------+-------------+                              |
|              v                           v                              |
|   +------------------+        +------------------+                      |
|   |   Native API     |        |      MQTT        |                      |
|   |  (Home Assistant)|        |   (Optional)     |                      |
|   +------------------+        +------------------+                      |
|                                                                         |
+-------------------------------------------------------------------------+
```

## Access Methods

### 1. ESPHome Dashboard API

```bash
# ESPHome Dashboard REST API
ESPHOME_URL="http://esphome.local:6052"

# List all devices
curl -s "${ESPHOME_URL}/devices" | jq

# Get device info
curl -s "${ESPHOME_URL}/devices/living_room_sensor/info"

# Get device logs
curl -s "${ESPHOME_URL}/devices/living_room_sensor/logs"

# Compile device (check config)
curl -X POST "${ESPHOME_URL}/devices/living_room_sensor/compile"

# OTA update (admin only)
curl -X POST "${ESPHOME_URL}/devices/living_room_sensor/upload"
```

### 2. Native API (Direct Device)

```python
import aioesphomeapi

async def connect_to_device():
    cli = aioesphomeapi.APIClient(
        address="living_room_sensor.local",
        port=6053,
        password="",  # or API password if set
    )
    await cli.connect(login=True)

    # Get device info
    device_info = await cli.device_info()
    print(f"Device: {device_info.name}")
    print(f"Version: {device_info.esphome_version}")

    # List entities
    entities = await cli.list_entities_services()
    for entity in entities:
        print(f"  {entity.name}: {entity.object_id}")

    # Subscribe to state changes
    def on_state(state):
        print(f"State update: {state}")

    await cli.subscribe_states(on_state)
```

### 3. MQTT (If Configured)

```yaml
# ESPHome device config with MQTT
mqtt:
  broker: emqx.local
  topic_prefix: esphome/living_room_sensor

# Topics:
# esphome/living_room_sensor/sensor/temperature/state
# esphome/living_room_sensor/switch/relay/state
# esphome/living_room_sensor/switch/relay/command
```

### 4. REST API (If Configured)

```yaml
# ESPHome device config with web server
web_server:
  port: 80

# Endpoints:
# GET  /sensor/temperature  - Get sensor value
# POST /switch/relay/turn_on
# POST /switch/relay/turn_off
# POST /switch/relay/toggle
```

## Configuration

### MCP Server

```json
{
  "mcpServers": {
    "esphome": {
      "command": "mcp-esphome",
      "env": {
        "ESPHOME_DASHBOARD_URL": "${ESPHOME_URL}",
        "ESPHOME_DASHBOARD_PASSWORD": "${ESPHOME_PASSWORD}"
      }
    }
  }
}
```

### SSH + CLI Access

For direct YAML config management:

```bash
# ESPHome configs typically in /config/esphome/
ssh homeassistant 'ls /config/esphome/*.yaml'

# View device config
ssh homeassistant 'cat /config/esphome/living_room_sensor.yaml'

# Validate config
ssh homeassistant 'esphome config /config/esphome/living_room_sensor.yaml'

# Compile (check for errors)
ssh homeassistant 'esphome compile /config/esphome/living_room_sensor.yaml'

# View logs
ssh homeassistant 'esphome logs /config/esphome/living_room_sensor.yaml'
```

## Access Levels

| Level | Permissions | Use Case |
| ----- | ----------- | -------- |
| `readonly` | View configs, logs, states | Monitoring, debugging |
| `logs` | Above + live log streaming | Deep debugging |
| `control` | Above + entity control | Automation testing |
| `config` | Above + edit YAML configs | Development |
| `admin` | Above + compile, OTA flash | Full management |

## Capabilities

| Capability | Method | Description |
| ---------- | ------ | ----------- |
| `list_devices` | Dashboard API | List all ESPHome devices |
| `get_device_info` | Native API | Device details, version |
| `get_logs` | Dashboard/CLI | Live or historical logs |
| `get_config` | SSH | Read YAML configuration |
| `validate_config` | CLI | Check config syntax |
| `list_entities` | Native API | All sensors, switches, etc. |
| `get_state` | Native API/MQTT | Current entity states |
| `control_entity` | Native API/MQTT | Control switches, lights |
| `compile` | Dashboard/CLI | Compile firmware |
| `upload_ota` | Dashboard/CLI | Flash new firmware |

## ESPHome YAML Patterns

### Common Sensor Configurations

```yaml
# Temperature/Humidity (DHT22)
sensor:
  - platform: dht
    pin: GPIO4
    model: DHT22
    temperature:
      name: "Temperature"
      filters:
        - sliding_window_moving_average:
            window_size: 5
    humidity:
      name: "Humidity"
    update_interval: 60s

# Motion (PIR)
binary_sensor:
  - platform: gpio
    pin: GPIO5
    name: "Motion"
    device_class: motion
    filters:
      - delayed_off: 30s

# Door/Window Contact
binary_sensor:
  - platform: gpio
    pin:
      number: GPIO12
      mode: INPUT_PULLUP
      inverted: true
    name: "Door"
    device_class: door

# Power Monitoring (HLW8012 - Sonoff POW)
sensor:
  - platform: hlw8012
    sel_pin: GPIO12
    cf_pin: GPIO5
    cf1_pin: GPIO14
    voltage:
      name: "Voltage"
    current:
      name: "Current"
    power:
      name: "Power"
    energy:
      name: "Energy"
    update_interval: 10s
```

### Common Actuator Configurations

```yaml
# Relay Switch
switch:
  - platform: gpio
    pin: GPIO13
    name: "Relay"
    id: relay1

# PWM Light
light:
  - platform: monochromatic
    name: "Dimmer"
    output: pwm_output
    gamma_correct: 2.8

output:
  - platform: ledc
    pin: GPIO5
    id: pwm_output
    frequency: 1000 Hz

# RGB Light
light:
  - platform: rgb
    name: "RGB Light"
    red: red_output
    green: green_output
    blue: blue_output

# Servo
servo:
  - id: servo1
    output: servo_output
    auto_detach_time: 2s
```

## Query Patterns for Agents

### Device Inventory

```bash
# List all ESPHome devices with status
curl -s "${ESPHOME_URL}/devices" | jq '.[] | {
  name: .name,
  status: .status,
  address: .address,
  version: .current_version
}'
```

### Device Health Check

```bash
# Get device info via native API
esphome logs living_room_sensor.yaml --device living_room_sensor.local 2>&1 | \
  grep -E "(Connected|WiFi|Heap|Uptime)"

# Check for common issues:
# - WiFi signal strength
# - Free heap memory
# - Uptime (frequent reboots?)
```

### Configuration Analysis

```bash
# Extract sensors from config
cat /config/esphome/living_room_sensor.yaml | \
  yq '.sensor[].name, .binary_sensor[].name, .switch[].name'
```

## Example Usage

### Device Health Report

```markdown
Agent task: "Report on all ESPHome devices"

## ESPHome Device Health Report

### Summary
- Total devices: 23
- Online: 21
- Offline: 2
- Update available: 5

### Device Status

| Device | Status | Version | WiFi | Uptime |
|--------|--------|---------|------|--------|
| living_room_sensor | Online | 2024.2.0 | -52 dBm | 15d 4h |
| kitchen_power | Online | 2024.2.0 | -61 dBm | 8d 12h |
| garage_door | Online | 2024.1.0 | -73 dBm | 2d 1h |
| outdoor_sensor | Offline | 2024.1.0 | - | - |
| shed_relay | Offline | 2023.12.0 | - | - |

### Issues Detected

#### Offline Devices
1. **outdoor_sensor**
   - Last seen: 4 hours ago
   - Last known WiFi: -78 dBm (weak)
   - Possible cause: WiFi signal, power loss

2. **shed_relay**
   - Last seen: 2 days ago
   - Possible cause: Power outage in shed

#### Needs Update
| Device | Current | Available |
|--------|---------|-----------|
| garage_door | 2024.1.0 | 2024.2.0 |
| bedroom_fan | 2024.1.0 | 2024.2.0 |
| patio_lights | 2023.12.0 | 2024.2.0 |

### Recommendations
1. Check power to shed (shed_relay offline)
2. Add WiFi extender for outdoor_sensor
3. Schedule OTA updates for 5 devices
```

### Debugging Device

Agent task: "The kitchen power monitor is showing incorrect readings"

Investigation: `kitchen_power`

Device Info:

- Platform: ESP8266 (Sonoff POW R2)
- ESPHome: 2024.2.0
- Uptime: 8 days, 12 hours
- WiFi: -61 dBm (good)
- Free Heap: 24KB (healthy)

Current Readings:

| Metric | Value | Notes |
| ------ | ----- | ----- |
| Voltage | 242.3 V | Reasonable |
| Current | 0.02 A | Very low |
| Power | 4.8 W | Matches V*I |
| Energy | 12.4 kWh | Total since boot |

Configuration Check - default values detected:

```yaml
sensor:
  - platform: hlw8012
    current_resistor: 0.001  # Default value
    voltage_divider: 2351    # Default value
```

Diagnosis: The HLW8012 calibration values are defaults. This sensor needs
calibration for accurate readings.

Recommended Fix - Option 1, calibrate with known load:

```yaml
sensor:
  - platform: hlw8012
    # Measure actual values and adjust:
    current_resistor: 0.00095  # Adjust based on actual
    voltage_divider: 2400      # Adjust based on multimeter
```

Recommended Fix - Option 2, use calibrate_linear filter:

```yaml
filters:
  - calibrate_linear:
      - 0.0 -> 0.0
      - 5.0 -> 4.85  # Measured: 5A reads as 4.85A
```

### Bulk Configuration Update

Agent task: "Add a restart button to all ESPHome devices"

Change Required - add to all device configs:

```yaml
button:
  - platform: restart
    name: "${device_name} Restart"
```

Devices to Update (23 total):

Phase 1: Test on 3 devices:

- living_room_sensor
- kitchen_power
- garage_door

Phase 2: Roll out to remaining 20

Procedure:

1. Edit YAML configs (SSH)
2. Validate each config
3. Compile to check for errors
4. OTA flash during low-usage hours (2-4 AM)
5. Verify device comes back online

Rollback Plan:

- Keep backup of original configs
- If device fails OTA, physical access required
- Serial flash as last resort

## Agents That Use This Skill

| Agent | Access | Purpose |
| ----- | ------ | ------- |
| `system/iot-monitor` | readonly | Device health monitoring |
| `ops/home-automation` | logs | Debugging automations |
| `code/esphome-dev` | config | Help write ESPHome YAML |
| `system/iot-admin` | admin | OTA updates, management |

## Graceful Degradation

| If Missing | Fallback |
| ---------- | -------- |
| Dashboard offline | Direct device API access |
| Device offline | Check last known state in HA |
| Native API timeout | Try MQTT or REST if configured |
| OTA fails | Fallback to serial flash |

## Security Considerations

### Device Security

```yaml
# Recommended ESPHome security settings

# API password (or encryption key in newer versions)
api:
  encryption:
    key: !secret esphome_api_key

# OTA password
ota:
  password: !secret esphome_ota_password

# Web server authentication (if used)
web_server:
  port: 80
  auth:
    username: admin
    password: !secret esphome_web_password

# Disable UART logging in production
logger:
  level: INFO
  baud_rate: 0  # Disable UART
```

### Agent Restrictions

```yaml
# Agents should NOT (without approval):
restricted_actions:
  - ota_flash           # Could brick device
  - factory_reset       # Data loss
  - wifi_reconfigure    # Could lose device
  - delete_config       # Config loss

# Agents MAY:
allowed_actions:
  - view_logs
  - view_config
  - validate_config
  - control_entities    # With approval
  - restart_device      # With approval
```

### Network Isolation

```yaml
# Recommended network setup:
networks:
  iot_vlan:
    id: 30
    subnet: 10.0.30.0/24
    devices:
      - esphome_devices
    access:
      - mqtt_broker
      - home_assistant
      - esphome_dashboard
    blocked:
      - internet          # No cloud access
      - other_vlans       # Isolated
```

## Common Troubleshooting

### WiFi Connection Issues

```yaml
# Improve WiFi stability
wifi:
  ssid: !secret wifi_ssid
  password: !secret wifi_password

  # Fixed IP for stability
  manual_ip:
    static_ip: 10.0.30.100
    gateway: 10.0.30.1
    subnet: 255.255.255.0

  # Fast reconnect
  fast_connect: true

  # Power save off for reliability
  power_save_mode: none

  # Fallback AP for recovery
  ap:
    ssid: "${device_name} Fallback"
    password: !secret ap_password

captive_portal:
```

### Memory Issues

```yaml
# Reduce memory usage
logger:
  level: WARN  # Less verbose

# Disable unused components
# Remove web_server if not needed
# Reduce sensor update frequencies

sensor:
  - platform: wifi_signal
    update_interval: 300s  # Less frequent

  - platform: uptime
    update_interval: 300s
```

### Boot Loops

```bash
# If device boot loops after OTA:

# 1. Check logs during boot
esphome logs device.yaml --device device.local

# 2. Look for:
#    - GPIO conflicts
#    - Memory allocation failures
#    - Component initialization errors

# 3. Recovery options:
#    - Wait for fallback AP (if configured)
#    - Serial flash with safe config
#    - Physical reset button (if available)
```
