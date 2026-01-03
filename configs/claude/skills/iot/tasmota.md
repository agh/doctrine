# Tasmota Skill

Provides access to Tasmota-flashed devices for monitoring, configuration, and control.

## Overview

| Attribute | Value |
| --------- | ----- |
| **Category** | IoT / ESP8266/ESP32 |
| **Protocol** | MQTT, HTTP API |
| **Default Access** | readonly (MQTT subscribe) |
| **Risk Level** | Medium (can control devices, flash firmware) |

## Architecture

```text
+-------------------------------------------------------------------------+
|                       TASMOTA ARCHITECTURE                              |
+-------------------------------------------------------------------------+
|                                                                         |
|   +-------------------------------------------------------------------+ |
|   |                      MQTT Broker (EMQX)                           | |
|   +-------------------------------------------------------------------+ |
|              |                    |                    |                |
|              v                    v                    v                |
|   +--------------+     +--------------+     +--------------+            |
|   |   Sonoff     |     |   Sonoff     |     |   Generic    |            |
|   |   Basic R2   |     |   POW R2     |     |   ESP8266    |            |
|   +--------------+     +--------------+     +--------------+            |
|                                                                         |
|   Topic Structure:                                                      |
|   - tele/{device}/STATE   - Telemetry (periodic)                        |
|   - stat/{device}/RESULT  - Command responses                           |
|   - cmnd/{device}/POWER   - Commands                                    |
|   - tele/{device}/SENSOR  - Sensor readings                             |
|   - tele/{device}/LWT     - Last Will (online/offline)                  |
|                                                                         |
+-------------------------------------------------------------------------+
```

## Access Methods

### 1. MQTT (Primary)

```bash
# Subscribe to all Tasmota telemetry
mosquitto_sub -h emqx.local -t "tele/#" -v

# Get device state
mosquitto_sub -h emqx.local -t "stat/kitchen_plug/RESULT" &
mosquitto_pub -h emqx.local -t "cmnd/kitchen_plug/STATE" -m ""

# Control device (requires write access)
mosquitto_pub -h emqx.local -t "cmnd/kitchen_plug/POWER" -m "ON"

# Get sensor readings
mosquitto_sub -h emqx.local -t "tele/+/SENSOR" -v

# Get device status
mosquitto_pub -h emqx.local -t "cmnd/kitchen_plug/STATUS" -m "0"
```

### 2. HTTP API (Direct Device)

```bash
# Get device status
curl "http://kitchen_plug.local/cm?cmnd=Status%200"

# Control power
curl "http://kitchen_plug.local/cm?cmnd=Power%20On"

# Get sensor data
curl "http://kitchen_plug.local/cm?cmnd=Status%2010"

# Get network info
curl "http://kitchen_plug.local/cm?cmnd=Status%205"
```

### 3. Console Commands (via MQTT)

```bash
# Any Tasmota console command via MQTT
mosquitto_pub -h emqx.local -t "cmnd/kitchen_plug/Backlog" \
  -m "Power On; Dimmer 50"

# Get configuration
mosquitto_pub -h emqx.local -t "cmnd/kitchen_plug/Status" -m "0"
```

## Configuration

### MCP Server

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

### Tasmota Device Configuration

```text
# Recommended Tasmota settings for agent access

# Set MQTT topic
Topic kitchen_plug

# Set telemetry period (seconds)
TelePeriod 60

# Enable sensor telemetry
SetOption19 0

# Enable LWT for availability tracking
LwtTopic %topic%/LWT
LwtOnline Online
LwtOffline Offline
```

## Access Levels

| Level | Permissions | Topics |
| ----- | ----------- | ------ |
| `readonly` | Subscribe only | `tele/#`, `stat/#` |
| `query` | Above + status requests | Above + `cmnd/+/Status` |
| `control` | Above + power control | Above + `cmnd/+/Power*` |
| `admin` | Full control | All topics |

### MQTT ACL

```yaml
# EMQX ACL for Tasmota
acl:
  - username: claude-agent
    permission: allow
    action: subscribe
    topics:
      - "tele/#"
      - "stat/#"

  - username: claude-agent
    permission: allow
    action: publish
    topics:
      - "cmnd/+/Status"      # Status queries only
      - "cmnd/+/State"

  - username: claude-agent
    permission: deny
    action: publish
    topics:
      - "cmnd/+/Power*"      # No power control
      - "cmnd/+/Restart"     # No restart
      - "cmnd/+/Reset"       # No factory reset
      - "cmnd/+/Upgrade"     # No firmware upgrade
```

## Topic Reference

### Telemetry Topics

```yaml
# tele/{device}/STATE - Periodic state
{
  "Time": "2025-01-02T10:30:00",
  "Uptime": "1T12:30:45",
  "UptimeSec": 131445,
  "Heap": 24,
  "SleepMode": "Dynamic",
  "Sleep": 50,
  "LoadAvg": 19,
  "MqttCount": 1,
  "POWER": "ON",
  "Wifi": {
    "AP": 1,
    "SSId": "HomeNetwork",
    "BSSId": "AA:BB:CC:DD:EE:FF",
    "Channel": 6,
    "Mode": "11n",
    "RSSI": 72,
    "Signal": -64,
    "LinkCount": 1,
    "Downtime": "0T00:00:03"
  }
}

# tele/{device}/SENSOR - Sensor readings
{
  "Time": "2025-01-02T10:30:00",
  "ENERGY": {
    "TotalStartTime": "2024-01-01T00:00:00",
    "Total": 123.456,
    "Yesterday": 4.567,
    "Today": 1.234,
    "Power": 45,
    "ApparentPower": 50,
    "ReactivePower": 20,
    "Factor": 0.90,
    "Voltage": 240,
    "Current": 0.188
  }
}

# tele/{device}/LWT - Availability
"Online" | "Offline"
```

### Status Commands

```yaml
# Status 0 - Full status
cmnd/{device}/Status 0

# Status 1 - Device parameters
# Status 2 - Firmware info
# Status 4 - Memory
# Status 5 - Network
# Status 6 - MQTT
# Status 7 - Time
# Status 8 - Sensors
# Status 10 - Sensor readings
# Status 11 - Power consumption
```

## Query Patterns for Agents

### Device Inventory

```bash
# Get all Tasmota devices via retained LWT
mosquitto_sub -h emqx.local -t "tele/+/LWT" -C 10 -W 5

# Parse STATE messages for device info
mosquitto_sub -h emqx.local -t "tele/+/STATE" -C 10 -W 60 | \
  jq -s '.[] | {device: .topic, uptime: .Uptime, wifi: .Wifi.RSSI}'
```

### Power Monitoring

```bash
# Get all power readings
mosquitto_sub -h emqx.local -t "tele/+/SENSOR" -C 10 | \
  jq 'select(.ENERGY) | {device: .topic, power: .ENERGY.Power, today: .ENERGY.Today}'
```

### Network Health

```bash
# Check WiFi signal strength across devices
mosquitto_sub -h emqx.local -t "tele/+/STATE" -C 10 | \
  jq '{device: .topic, rssi: .Wifi.RSSI, signal: .Wifi.Signal, downtime: .Wifi.Downtime}'
```

## Example Usage

### Device Health Report

```markdown
Agent task: "Report on all Tasmota devices"

## Tasmota Device Health Report

### Summary
- Total devices: 15
- Online: 14
- Offline: 1
- Power monitoring: 8 devices

### Device Status

| Device | Status | Uptime | WiFi | Power |
|--------|--------|--------|------|-------|
| kitchen_plug | Online | 15d 4h | -52 dBm | 45W |
| laundry_washer | Online | 8d 12h | -61 dBm | 0W |
| garage_outlet | Offline | - | - | - |
| living_room_lamp | Online | 22d 1h | -48 dBm | 12W |

### Power Summary
- Total current: 234W
- Today's usage: 5.6 kWh
- This month: 156.3 kWh

### Issues Detected

#### Offline Devices
1. **garage_outlet**
   - Last seen: 6 hours ago
   - Last RSSI: -78 dBm (weak)
   - Possible cause: WiFi signal, power loss

#### Weak Signal Devices
| Device | RSSI | Recommendation |
|--------|------|----------------|
| shed_plug | -75 dBm | Add WiFi extender |
| basement_sensor | -72 dBm | Relocate device |
```

### Power Analysis

Agent task: "Analyze power consumption of kitchen appliances"

Kitchen Power Analysis:

| Device | Avg Power | Peak | Today | Yesterday |
| ------ | --------- | ---- | ----- | --------- |
| refrigerator | 85W | 150W | 2.04 kWh | 2.10 kWh |
| dishwasher | 0W | 1800W | 1.2 kWh | 0 kWh |
| coffee_maker | 0W | 1200W | 0.3 kWh | 0.25 kWh |
| microwave | 0W | 1100W | 0.15 kWh | 0.20 kWh |

Daily Pattern:

```text
Hour  | kWh
------+-----
00-06 | 0.5  [====]
06-09 | 1.8  [================]
09-12 | 0.8  [=======]
12-14 | 1.2  [===========]
17-20 | 2.1  [===================]
20-24 | 0.9  [========]
```

Insights:

- Refrigerator cycles every 45 minutes (normal)
- Dishwasher ran at 19:30 (1800W peak for 45 min)
- Coffee maker used at 07:15 and 14:30

### Troubleshooting Device

Agent task: "The living room lamp keeps disconnecting"

Investigation: `living_room_lamp`

Device Info:

- Hardware: Sonoff Basic R2
- Firmware: 12.4.0 (Tasmota)
- Uptime: 2 hours 15 minutes (recent restart)

Connection History (24h):

| Time | Event | Duration |
| ---- | ----- | -------- |
| 10:30 | Disconnected | 3 min |
| 08:15 | Disconnected | 5 min |
| 03:45 | Disconnected | 2 min |
| 22:10 | Disconnected | 4 min |

WiFi Analysis:

- Current RSSI: -68 dBm (marginal)
- Channel: 6 (congested)
- AP switches detected: Yes

Diagnosis: Device is on the edge of WiFi coverage and experiencing:

1. Low signal strength (-68 dBm)
2. Channel congestion (channel 6)
3. AP roaming between access points

Recommendations:

1. Move device closer to AP or add repeater
2. Consider changing WiFi channel to 1 or 11
3. Set fixed BSSID in Tasmota config: `WifiConfig 5` and
   `AP1 HomeNetwork AA:BB:CC:DD:EE:FF`

## Agents That Use This Skill

| Agent | Access | Purpose |
| ----- | ------ | ------- |
| `system/iot-monitor` | readonly | Device health, availability |
| `ops/home-automation` | query | Power monitoring, debugging |
| `security/iot-security` | readonly | Anomaly detection |

## Graceful Degradation

| If Missing | Fallback |
| ---------- | -------- |
| Device offline | Check Home Assistant for last known state |
| MQTT broker down | Query device HTTP API directly |
| HTTP API timeout | Check WiFi and power status |

## Security Considerations

### Device Security

```text
# Recommended Tasmota security settings

# Set web admin password
WebPassword your_secure_password

# Disable web console for remote access
WebServer 2

# Enable MQTT TLS
MqttHost mqtts://emqx.local:8883

# Disable unnecessary features
SetOption36 0  # Disable boot loop control
```

### Agent Restrictions

```yaml
# Agents should NOT (without approval):
restricted_commands:
  - Power*         # Device control
  - Restart        # Device restart
  - Reset          # Factory reset
  - Upgrade        # Firmware upgrade
  - Backlog        # Multiple commands
  - Template       # Hardware config
  - Module         # Hardware config
  - GPIO*          # GPIO configuration

# Agents MAY:
allowed_commands:
  - Status*        # Status queries
  - State          # State query
```

## Common Tasmota Commands

### Status Commands

| Command | Description |
| ------- | ----------- |
| `Status 0` | Full status dump |
| `Status 5` | Network info |
| `Status 8` | Sensor status |
| `Status 10` | Sensor readings |
| `Status 11` | Power readings |

### Diagnostic Commands

| Command | Description |
| ------- | ----------- |
| `State` | Current device state |
| `Modules` | Available modules |
| `GPIO` | Current GPIO config |
| `I2CScan` | Scan I2C bus |

### Sensor Commands

| Command | Description |
| ------- | ----------- |
| `TelePeriod` | Set telemetry interval |
| `Sensor` | Sensor configuration |
| `HumOffset` | Humidity calibration |
| `TempOffset` | Temperature calibration |
