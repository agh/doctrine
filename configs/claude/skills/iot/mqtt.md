# MQTT / EMQX Skill

Provides MQTT messaging capabilities for IoT device communication, monitoring, and automation.

## Overview

| Attribute | Value |
| --------- | ----- |
| **Category** | IoT |
| **Protocol** | MQTT 3.1.1 / 5.0 |
| **Compatible Brokers** | EMQX, Mosquitto, HiveMQ, AWS IoT Core |
| **Default Access** | subscribe (read-only) |
| **Risk Level** | Medium (can affect physical devices) |

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
        "MQTT_PASSWORD": "${MQTT_PASSWORD}",
        "MQTT_CLIENT_ID": "claude-agent-${AGENT_ID}"
      }
    }
  }
}
```

### EMQX-Specific Configuration

```json
{
  "mcpServers": {
    "emqx": {
      "command": "mcp-mqtt",
      "env": {
        "MQTT_BROKER": "mqtts://emqx.local:8883",
        "MQTT_USERNAME": "${EMQX_USERNAME}",
        "MQTT_PASSWORD": "${EMQX_PASSWORD}",
        "MQTT_TLS": "true",
        "MQTT_TLS_CA": "/path/to/ca.crt"
      }
    }
  }
}
```

### CLI Access

```bash
# Using mosquitto_sub/pub
mosquitto_sub -h emqx.local -p 8883 \
  -u "${MQTT_USERNAME}" -P "${MQTT_PASSWORD}" \
  --cafile /path/to/ca.crt \
  -t "sensors/#" -v

mosquitto_pub -h emqx.local -p 8883 \
  -u "${MQTT_USERNAME}" -P "${MQTT_PASSWORD}" \
  --cafile /path/to/ca.crt \
  -t "commands/device1/set" \
  -m '{"state": "on"}'
```

## Access Levels

| Level | MQTT Operations | Use Case |
| ----- | --------------- | -------- |
| `subscribe` | Subscribe to topics, receive messages | Monitoring, analysis |
| `publish` | Subscribe + publish to specific topics | Automation, control |
| `admin` | Full access + broker management | Configuration |

### Topic-Based ACL

```yaml
# EMQX ACL configuration
acl:
  - username: claude-agent
    permission: allow
    action: subscribe
    topics:
      - "sensors/#"
      - "status/#"
      - "telemetry/#"

  - username: claude-agent
    permission: allow
    action: publish
    topics:
      - "commands/+/request"  # Can request, not directly control

  - username: claude-agent
    permission: deny
    action: publish
    topics:
      - "commands/+/set"      # Cannot directly set state
      - "config/#"            # Cannot modify config
```

## Capabilities

| Capability | Description |
| ---------- | ----------- |
| `subscribe` | Subscribe to topic patterns |
| `unsubscribe` | Unsubscribe from topics |
| `publish` | Publish message to topic |
| `list_topics` | List active topics (EMQX API) |
| `get_retained` | Get retained messages |
| `query_clients` | List connected clients (EMQX API) |

## Topic Patterns

### Standard IoT Topic Structure

```text
{domain}/{device_type}/{device_id}/{data_type}

Examples:
sensors/temperature/living_room/state
sensors/motion/front_door/state
actuators/light/kitchen/set
actuators/light/kitchen/state
config/device123/settings
telemetry/device123/heartbeat
```

### Home Automation Topics

```text
# Zigbee2MQTT pattern
zigbee2mqtt/{device_name}
zigbee2mqtt/{device_name}/set
zigbee2mqtt/{device_name}/get

# Tasmota pattern
tele/{device}/STATE
cmnd/{device}/POWER
stat/{device}/RESULT

# ESPHome pattern
esphome/{device}/{sensor}/state
esphome/{device}/{switch}/command
```

## Query Patterns for Agents

### Device Monitoring

```python
# Subscribe to all temperature sensors
subscribe("sensors/temperature/+/state")

# Messages received:
# sensors/temperature/living_room/state: {"temperature": 21.5, "humidity": 45}
# sensors/temperature/bedroom/state: {"temperature": 19.2, "humidity": 52}
```

### Device Status Check

```python
# Get all device status
subscribe("status/+/online")

# Or query EMQX API for connected clients
GET /api/v5/clients
```

### Historical Data (with EMQX Rule Engine)

```sql
-- EMQX rule to store sensor data
SELECT
  payload.temperature as temperature,
  payload.humidity as humidity,
  clientid as device_id,
  timestamp
FROM "sensors/#"
-- Route to TimescaleDB/InfluxDB for agent queries
```

## Example Usage

### Environment Monitoring

```markdown
Agent task: "What's the current state of all temperature sensors?"

1. Subscribe to sensors/temperature/+/state
2. Wait for messages (or query retained)
3. Aggregate and report:

| Location | Temperature | Humidity | Last Update |
|----------|-------------|----------|-------------|
| Living Room | 21.5°C | 45% | 2 min ago |
| Bedroom | 19.2°C | 52% | 1 min ago |
| Kitchen | 22.1°C | 38% | 30 sec ago |
```

### Device Diagnostics

```markdown
Agent task: "Which devices haven't reported in the last hour?"

1. Query EMQX API for client list
2. Compare last_seen timestamps
3. Report offline devices:

Devices offline > 1 hour:
- motion_sensor_garage (last seen: 3 hours ago)
- temperature_basement (last seen: 2 hours ago)

Recommended actions:
- Check battery levels
- Verify network connectivity
- Check for firmware issues
```

### Automation Debugging

```markdown
Agent task: "Why didn't the lights turn on when motion was detected?"

1. Subscribe to relevant topics:
   - sensors/motion/hallway/state
   - actuators/light/hallway/set
   - actuators/light/hallway/state

2. Check message flow:
   - Motion detected at 10:30:15 ✓
   - Light command sent at 10:30:15 ✓
   - Light state unchanged ✗

3. Diagnosis:
   - Command was sent but device didn't respond
   - Check: Device online? Network issues? Hardware fault?
```

## EMQX API Access

### REST API Queries

```bash
# List all clients
curl -u admin:password "http://emqx:18083/api/v5/clients"

# Get client details
curl -u admin:password "http://emqx:18083/api/v5/clients/device123"

# List subscriptions
curl -u admin:password "http://emqx:18083/api/v5/subscriptions"

# Get topic metrics
curl -u admin:password "http://emqx:18083/api/v5/topics"

# Query retained messages
curl -u admin:password "http://emqx:18083/api/v5/mqtt/retainer/messages?topic=sensors/+"
```

### Useful EMQX Queries for Agents

```python
# Find disconnected devices
GET /api/v5/clients?status=disconnected

# Find devices with high message rate (possible issue)
GET /api/v5/clients?_order_by=send_msg&_order=desc&_limit=10

# Find topics with no subscribers (orphaned)
GET /api/v5/topics?match_type=filter&topic=sensors/#
# Compare with subscriptions
```

## Agents That Use This Skill

| Agent | Access | Purpose |
| ----- | ------ | ------- |
| `system/iot-monitor` | subscribe | Device health monitoring |
| `security/iot-security` | subscribe | Anomaly detection |
| `ops/home-automation` | publish | Automation debugging |

## Graceful Degradation

| If Missing | Fallback |
| ---------- | -------- |
| MQTT unavailable | Query Home Assistant API instead |
| Specific device offline | Check last known state, alert |
| Broker disconnected | Reconnect with backoff |

## Security Considerations

### Authentication

- **MUST** use TLS for all connections
- **MUST** use strong passwords or certificates
- **SHOULD** use client certificates for agents
- **MUST** use unique client IDs per agent

### Authorization

- **MUST** use ACLs to restrict topic access
- **MUST NOT** allow agents to publish to control topics by default
- **SHOULD** use request/response pattern for control actions
- **MUST** require human approval for device control

### Topic Security

```yaml
# Sensitive topics - agents should NOT access
restricted_topics:
  - "config/#"           # Device configuration
  - "firmware/#"         # Firmware updates
  - "admin/#"            # Administrative commands
  - "credentials/#"      # Any credential topics
```

### Rate Limiting

```yaml
# EMQX rate limiting
rate_limit:
  max_publish_rate: 10/s
  max_subscribe_rate: 5/s
  max_message_size: 64KB
```

## Message Formats

### Standard Sensor Message

```json
{
  "timestamp": "2025-01-02T10:30:00Z",
  "device_id": "temp_sensor_01",
  "type": "temperature",
  "value": 21.5,
  "unit": "celsius",
  "battery": 85,
  "rssi": -65
}
```

### Command Message

```json
{
  "timestamp": "2025-01-02T10:30:00Z",
  "command": "set_state",
  "parameters": {
    "state": "on",
    "brightness": 80
  },
  "source": "agent:ops/home-automation",
  "requires_approval": true
}
```

### Status Message

```json
{
  "timestamp": "2025-01-02T10:30:00Z",
  "device_id": "light_kitchen_01",
  "online": true,
  "state": "on",
  "brightness": 80,
  "firmware": "1.2.3",
  "uptime_seconds": 86400
}
```
