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
# Recommended Tasmota settings for agent access.
# Backlog runs the sequence in order; commands marked "and restart" take
# effect after the reboot Tasmota performs itself.

Backlog Topic kitchen_plug; TelePeriod 60; SetOption19 0
```

`SetOption19 0` is the **default** and selects the native Tasmota discovery
protocol used by the Home Assistant Tasmota integration. It does not "enable
sensor telemetry" — telemetry is controlled by `TelePeriod`. Setting
`SetOption19 1` selects the deprecated MQTT discovery, which is not compiled
into release binaries at all.

There are no `LwtTopic`, `LwtOnline` or `LwtOffline` commands. Tasmota
publishes availability to `tele/%topic%/LWT` with the retained payloads
`Online` and `Offline`. The full topic is derived from `FullTopic` and
`Topic`, so it changes only if `FullTopic` is changed:

```text
# Inspect, don't invent
FullTopic          # default: %prefix%/%topic%/
Status 6           # shows MqttHost, MqttPort and the LWT topic in use
```

## Access Levels

| Level | Permissions | Topics |
| ----- | ----------- | ------ |
| `readonly` | Subscribe only | `tele/#`, `stat/#` |
| `query` | Above + status requests | Above + `cmnd/+/Status` |
| `control` | Above + power control | Above + `cmnd/+/Power*` |
| `admin` | Full control | All topics |

### MQTT ACL

EMQX's file authoriser takes Erlang terms; see
[MQTT / EMQX](mqtt.md#topic-based-acl) for the file format, how to register it
as an authorization source, and why denied publishes are silent.

```erlang
%% acl.conf — Tasmota agent rules
{deny,  {username, "claude-agent"}, publish,
        ["cmnd/+/Power",       %% No power control
         "cmnd/+/Power1",
         "cmnd/+/Power2",
         "cmnd/+/Restart",     %% No restart
         "cmnd/+/Reset",       %% No factory reset
         "cmnd/+/Upgrade"]}.   %% No firmware upgrade
{allow, {username, "claude-agent"}, subscribe, ["tele/#", "stat/#"]}.
{allow, {username, "claude-agent"}, publish,
        ["cmnd/+/Status", "cmnd/+/State"]}.
{deny, all}.
```

Topic filters use MQTT wildcards only. `cmnd/+/Power*` is not a prefix pattern:
`*` has no special meaning, so that filter matches a topic whose last segment is
the literal text `Power*` and leaves `cmnd/device/Power1` allowed. Each relay
command **MUST** be listed explicitly.

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

```text
# Status 0 - all status information (1 - 11)
cmnd/{device}/Status 0
```

| Command | Returns |
| ------- | ------- |
| `Status` | Abbreviated status |
| `Status 0` | Everything from 1 to 11 in one response |
| `Status 1` | Device parameters |
| `Status 2` | Firmware information |
| `Status 3` | Logging and telemetry settings |
| `Status 4` | Memory |
| `Status 5` | Network |
| `Status 6` | MQTT (host, port, LWT topic) |
| `Status 7` | Time |
| `Status 8` | Connected sensors (kept for backwards compatibility) |
| `Status 9` | Power **thresholds** (power-monitoring modules only) |
| `Status 10` | Connected sensors (replaces `Status 8`) |
| `Status 11` | Same payload as the `TelePeriod` STATE message |

`Status 11` returns the STATE message: uptime, Wi-Fi and relay state. It does
**not** return energy readings. Live power and energy come from `Status 10`, or
from the `tele/{device}/SENSOR` telemetry message. `Status 9` returns the
configured thresholds, not a measurement.

`Sensor` is a dispatcher for driver-specific subcommands such as `Sensor20`; a
bare `Sensor` addresses no driver and is not a way to read values.

## Query Patterns for Agents

Every pipeline below uses `mosquitto_sub -v`, which prints `topic payload` on
one line. The topic carries the device name; the payload never does.

### Device Inventory

```bash
# Get all Tasmota devices via retained LWT
mosquitto_sub -h emqx.local -v -t "tele/+/LWT" -W 5 \
  | awk '{print $1, $2}'

# Parse STATE messages for device info
mosquitto_sub -h emqx.local -v -t "tele/+/STATE" -C 10 -W 60 \
  | jq -Rs '
      [ split("\n")[]
        | select(length > 0)
        | (index(" ")) as $i
        | {topic: .[0:$i], payload: (.[$i+1:] | fromjson? // {})}
      ]
      | map({device: (.topic | split("/")[1]),
             uptime: .payload.Uptime,
             rssi: .payload.Wifi.RSSI})'
```

### Power Monitoring

```bash
# Get all power readings, skipping devices without an ENERGY block
mosquitto_sub -h emqx.local -v -t "tele/+/SENSOR" -C 10 -W 60 \
  | jq -Rs '
      [ split("\n")[]
        | select(length > 0)
        | (index(" ")) as $i
        | {topic: .[0:$i], payload: (.[$i+1:] | fromjson? // {})}
      ]
      | map(select(.payload.ENERGY))
      | map({device: (.topic | split("/")[1]),
             power: .payload.ENERGY.Power,
             today: .payload.ENERGY.Today})'
```

### Network Health

```bash
# Check WiFi signal strength across devices
mosquitto_sub -h emqx.local -v -t "tele/+/STATE" -C 10 -W 60 \
  | jq -Rs '
      [ split("\n")[]
        | select(length > 0)
        | (index(" ")) as $i
        | {topic: .[0:$i], payload: (.[$i+1:] | fromjson? // {})}
      ]
      | map({device: (.topic | split("/")[1]),
             rssi: .payload.Wifi.RSSI,
             signal: .payload.Wifi.Signal,
             downtime: .payload.Wifi.Downtime})
      | sort_by(.signal)'
```

**Why**: without `-v` the topic is absent and `.topic` evaluates to `null`, so
every row is reported against an unnamed device. Adding `-v` alone is not
enough either — the line is then no longer valid JSON, and `jq -s` fails with
`parse error: Invalid literal`. The topic **MUST** be split from the payload
before the payload is parsed.

`fromjson? // {}` keeps a malformed retained message from aborting the whole
batch.

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
3. Pin the device to one access point. `AP1` sets the SSID only and takes no
   BSSID argument; the BSSID is a separate command:

```text
Backlog SSId1 HomeNetwork; BSSId1 AA:BB:CC:DD:EE:FF; WifiConfig 5
```

`WifiConfig 5` makes the device wait for the selected AP to return rather than
rebooting or falling back to another AP.

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
# Recommended Tasmota security settings (Tasmota 15.6.0)

# Set web admin password for user `admin`
WebPassword your_secure_password

# Web UI exposure:
#   0 = web server off
#   1 = user (read-only) pages
#   2 = admin pages  <- MORE access, not less
# Use 0 to disable the web UI, or 1 to leave status pages available.
WebServer 1

# MQTT over TLS. MqttHost takes a hostname or IP only: a URL such as
# mqtts://emqx.local:8883 is stored verbatim as the hostname and never
# resolves, so the device stops reaching the broker entirely.
# Use an IP or a resolvable DNS name, NOT an mDNS `.local` name.
Backlog MqttHost 10.0.30.10; MqttPort 8883; SetOption103 1

# Keep boot-loop recovery enabled (default 1). SetOption36 0 disables the
# mechanism that restores working settings after repeated crash reboots.
SetOption36 1
```

`SetOption103 1` requires a TLS-capable build; release binaries with `-tls` in
the name include it, and standard builds do not. Verify with `Status 2` before
relying on it. Tasmota validates the broker against the CA compiled into the
firmware, so a private CA needs a matching build.

Avoid `.local` names for `MqttHost`: the command reference states explicitly
that mDNS names must not be used there in standard builds. Use an IP address or
a DNS name the device can resolve.

**Why**: each of these three commands previously did the opposite of the stated
intent. `WebServer 2` grants administrative web access rather than removing it;
a URL in `MqttHost` breaks broker connectivity instead of adding TLS; and
`SetOption36 0` removes the recovery path that restores a device stuck in a
crash loop, turning a recoverable fault into a reflash.

Confirm recovery still works before changing anything remotely:

```text
Status 6           # MQTT host, port and LWT topic actually in use
Status 2           # firmware build, to confirm TLS support
```

Where a device is reachable only over the network, a serial console or a
physical reset button **MUST** be available before applying Wi-Fi, MQTT or web
server changes.

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
