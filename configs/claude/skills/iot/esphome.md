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

### 1. Device Builder / CLI

The ESPHome Dashboard is now
[Device Builder](https://github.com/esphome/device-builder) (1.14.4). Its REST
surface is a compatibility shim: the module is marked `DEPRECATED` in source and
exists for the Home Assistant integration until that migrates to the `/ws`
multiplexed API.

There are no per-device REST routes. `/devices/<name>/info`,
`/devices/<name>/logs`, `/devices/<name>/compile` and `/devices/<name>/upload`
do not exist. An unmatched `GET` returns the front-end HTML shell rather than a
`404`, so a script that only checks the status code will treat the failure as
success.

Agents **MUST** drive builds through the `esphome` CLI, pinned to 2026.8.2:

```bash
# Validate configuration
esphome config living_room_sensor.yaml

# Compile only
esphome compile living_room_sensor.yaml

# Compile and flash over the air
esphome upload living_room_sensor.yaml

# Stream logs from the device
esphome logs living_room_sensor.yaml
```

**Why**: the CLI exits non-zero on failure and takes the same YAML the device
already uses, so a failed validation stops the pipeline. The deprecated HTTP
routes give neither guarantee.

The two legacy read endpoints that do exist are shaped differently from the
guide's original assumption. `/devices` returns an **object** with `configured`
and `importable` arrays, not a bare array:

```bash
ESPHOME_URL="http://esphome.local:6052"

# List configured device names
curl -sS --fail-with-body "${ESPHOME_URL}/devices" \
  | jq -r '.configured[].name'

# Online-status map, keyed by config filename
curl -sS --fail-with-body "${ESPHOME_URL}/ping" | jq

# Fully resolved config as JSON
curl -sS --fail-with-body \
  "${ESPHOME_URL}/json-config?configuration=living_room_sensor.yaml" | jq
```

`/compile` and `/upload` are WebSocket endpoints reached with `GET`, not `POST`
REST calls. Use the CLI rather than driving them directly.

### 2. Native API (Direct Device)

Pinned to `aioesphomeapi` 46.3.0. Note that ESPHome 2026.8.2 itself pins
`aioesphomeapi==45.10.3`, so install the client in its own environment.

```python
import asyncio

from aioesphomeapi import APIClient


async def connect_to_device() -> None:
    cli = APIClient(
        address="living_room_sensor.local",
        port=6053,
        noise_psk="<base64 key from api.encryption.key>",
    )
    await cli.connect(login=True)
    try:
        # Get device info
        device_info = await cli.device_info()
        print(f"Device: {device_info.name}")
        print(f"Version: {device_info.esphome_version}")

        # Returns a tuple, not a flat list
        entities, services = await cli.list_entities_services()
        for entity in entities:
            print(f"  {entity.name}: {entity.object_id}")

        # Subscribe to state changes
        def on_state(state) -> None:
            print(f"State update: {state}")

        # Not a coroutine: do not await it
        cli.subscribe_states(on_state)
        await asyncio.sleep(60)
    finally:
        await cli.disconnect()


asyncio.run(connect_to_device())
```

Three details are load-bearing:

- `list_entities_services()` returns
  `tuple[list[EntityInfo], list[UserService]]`. Iterating it directly yields
  the two lists, and `entity.name` then raises
  `AttributeError: 'list' object has no attribute 'name'`.
- `subscribe_states()` is a plain method returning `None`. Awaiting it raises
  `TypeError: object NoneType can't be used in 'await' expression`. It returns
  no unsubscribe handle; end the subscription by disconnecting.
- The client **MUST** be disconnected. Without the `finally`, the connection
  and its reconnect logic outlive the function.

Prefer `noise_psk` over `password`. The `password` parameter still exists on
`APIClient`, but transport encryption authenticates the peer and protects the
session, whereas the API password does neither.

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

# Power Monitoring - Sonoff POW R1 (HLW8012)
# GPIO12 is the relay on this board and MUST NOT be used as sel_pin:
# ESPHome drives sel_pin as an output and toggles it to switch the
# HLW8012 between voltage and current measurement.
switch:
  - platform: gpio
    pin: GPIO12
    name: "Relay"

sensor:
  - platform: hlw8012
    sel_pin: GPIO5
    cf_pin: GPIO14
    cf1_pin: GPIO13
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

The Sonoff POW **R2** is a different board: its metering chip is a CSE7766 on
the ESP8266's single UART, not an HLW8012. Applying the R1 block above to an R2
drives the relay pin as a measurement-select output and produces no readings.

```yaml
# Power Monitoring - Sonoff POW R2 (CSE7766)
# The CSE7766 occupies the only UART, so serial logging must be off.
logger:
  baud_rate: 0

uart:
  rx_pin: RX
  baud_rate: 4800
  parity: EVEN

switch:
  - platform: gpio
    pin: GPIO12
    name: "Relay"

sensor:
  - platform: cse7766
    voltage:
      name: "Voltage"
      filters:
        - throttle_average: 10s
    current:
      name: "Current"
      filters:
        - throttle_average: 10s
    power:
      name: "Power"
      filters:
        - throttle_average: 10s
    energy:
      name: "Energy"
      filters:
        - throttle: 10s
```

The CSE7766 pushes readings rather than being polled, so it takes no
`update_interval`; rate is controlled with `throttle_average` filters.

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
# List all ESPHome devices with status.
# /devices returns an object with `configured` and `importable` arrays,
# so it must not be indexed as a bare array.
curl -sS --fail-with-body "${ESPHOME_URL}/devices" | jq '.configured[] | {
  name: .name,
  address: .address,
  configuration: .configuration
}'

# Online status, keyed by config filename
curl -sS --fail-with-body "${ESPHOME_URL}/ping" | jq
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

Configuration Check - wrong sensor platform for this board:

```yaml
# Found on the device: an HLW8012 block on a POW R2
sensor:
  - platform: hlw8012
    sel_pin: GPIO12
    current_resistor: 0.001  # Default value
    voltage_divider: 2351    # Default value
```

Diagnosis: the POW R2 meters with a CSE7766 over UART, not an HLW8012. The
configuration names the wrong driver, and `sel_pin: GPIO12` drives the relay
pin as a measurement-select output. Calibration **MUST NOT** be attempted while
the driver is mismatched; adjusting `current_resistor` or `voltage_divider`
tunes a device that is not present.

Recommended Fix - use the board's real sensor:

```yaml
logger:
  baud_rate: 0

uart:
  rx_pin: RX
  baud_rate: 4800
  parity: EVEN

sensor:
  - platform: cse7766
    voltage:
      name: "Voltage"
    current:
      name: "Current"
    power:
      name: "Power"
```

Only once the correct driver reports plausible values does calibration apply.
On a genuine POW R1 (HLW8012), calibrate with a known load:

```yaml
sensor:
  - platform: hlw8012
    sel_pin: GPIO5
    cf_pin: GPIO14
    cf1_pin: GPIO13
    # Measure actual values and adjust:
    current_resistor: 0.00095  # Adjust based on actual
    voltage_divider: 2400      # Adjust based on multimeter
```

Or use a `calibrate_linear` filter on the affected sensor:

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
# Recommended ESPHome security settings, validated against ESPHome 2026.8.2

# API encryption key (replaces the legacy api password)
api:
  encryption:
    key: !secret esphome_api_key

# OTA is platform-based. A bare `ota: password:` fails validation with
# "'ota' requires a 'platform' key but it was not specified."
ota:
  - platform: esphome
    password: !secret esphome_ota_password

# Web server authentication (if used)
web_server:
  port: 80
  auth:
    type: digest
    username: admin
    password: !secret esphome_web_password

# Disable UART logging in production
logger:
  level: INFO
  baud_rate: 0  # Disable UART
```

`auth.type` still defaults to `basic` in 2026.8.2, and omitting it logs a
deprecation warning; the default becomes `digest` in ESPHome 2027.1.0. Set the
type explicitly either way.

**Why**: basic authentication sends the password in an easily reversible form
on every request. Digest does not, and stating the type explicitly means the
2027.1.0 default change cannot alter the device's behaviour unannounced.

Two settings are conditional rather than universal:

```yaml
# Only when a browser on another origin must call the device
web_server:
  port: 80
  auth:
    type: digest
    username: admin
    password: !secret esphome_web_password
  allowed_origins:
    - http://homeassistant.local:8123

# Only when firmware should also be uploadable through the web UI.
# ota.web_server requires the web_server component above.
ota:
  - platform: esphome
    password: !secret esphome_ota_password
  - platform: web_server
```

`web_server: ota:` accepts only `false`, to disable web OTA. Enabling it
requires the separate `web_server` OTA platform above. Adding that platform
widens the attack surface to anyone who can reach port 80, so add it only when
the web upload path is actually wanted.

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
