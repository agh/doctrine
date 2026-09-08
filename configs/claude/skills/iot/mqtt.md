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

EMQX's file authoriser reads **Erlang terms**, not YAML. Feeding it the YAML
form is rejected outright:

```console
$ PUT /api/v5/authorization/sources/file   # with a YAML rules body
HTTP 400
{"code":"BAD_REQUEST",
 "message":"{bad_acl_file_content,{2,erl_parse,[\"syntax error before: \",\"'-'\"]}}"}
```

Write `acl.conf` as one `{Permission, Who, Action, Topics}.` term per line,
ending with an explicit catch-all deny:

```erlang
%% acl.conf — EMQX 6.3.0 file authoriser
{allow, {username, "claude-agent"}, subscribe,
        ["sensors/#", "status/#", "telemetry/#"]}.
{allow, {username, "claude-agent"}, publish, ["commands/+/request"]}.
{deny,  {username, "claude-agent"}, publish, ["commands/+/set", "config/#"]}.
{allow, {username, "device-pub"}, publish, ["sensors/#"]}.
{deny, all}.
```

Rules are evaluated top to bottom and the first match wins, so the deny rules
**MUST** precede any broader allow, and `{deny, all}.` **MUST** be last.

Register the file as an authorization source. A stock EMQX already has a
`file` source (its default `acl.conf`), so `POST` returns
`400 {duplicated_authz_source_type,[file]}`. Use `PUT`, which replaces it,
with an **administrator** API key — a `viewer` key gets
`403 UNAUTHORIZED_ROLE`:

```bash
jq -Rs '{type:"file",enable:true,rules:.}' acl.conf > source.json

curl -sS --fail-with-body -X PUT \
  "https://emqx.example:18083/api/v5/authorization/sources/file" \
  -u "${EMQX_ADMIN_KEY}:${EMQX_ADMIN_SECRET}" \
  -H 'Content-Type: application/json' \
  -d @source.json
# HTTP 204
```

Loading an ACL is administrative. The read-only key an agent uses for the
queries in [EMQX API Access](#emqx-api-access) **MUST NOT** be able to perform
it.

Verified against EMQX 6.3.0: with the rules above loaded, publishes to
`sensors/kitchen/temperature` and `commands/light1/request` were stored, while
`commands/light1/set` and `config/device1` were not.

Denied publishes are **silent**. EMQX 6.3 defaults to
`authorization.deny_action = ignore`, so the broker drops the message and still
returns `PUBACK`; a QoS 1 publisher sees success. Agents **MUST NOT** treat a
`PUBACK` as proof that a message was accepted, and **SHOULD** confirm through
the retained-message or subscription APIs when it matters.

A stock broker fails **open**, and replacing the default ACL is what closes it.
The shipped `acl.conf` ends with:

```erlang
{allow, {security_profile, legacy}}.
```

`EMQX_SECURITY_PROFILE` defaults to `legacy` in the container entrypoint
(`export EMQX_SECURITY_PROFILE="${EMQX_SECURITY_PROFILE:-legacy}"`), so that
final rule matches and permits everything the earlier rules did not decide —
including `config/#`, `firmware/#` and `admin/#`.

**Why**: an operator who loads no ACL, or whose `PUT` silently failed, has a
broker that accepts every publish from every anonymous client. Replacing the
last rule with `{deny, all}.` and confirming `authorization.no_match = deny` is
what makes the deny-by-default claim true:

```bash
curl -sS --fail-with-body -u "${EMQX_API_KEY}:${EMQX_API_SECRET}" \
  "https://emqx.example:18083/api/v5/authorization/settings" \
  | jq '{no_match, deny_action}'
# {"no_match": "deny", "deny_action": "ignore"}
```

Agents **MUST** verify enforcement after loading an ACL by publishing to a
topic that should be denied and confirming it did not arrive.

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

### Authentication

Dashboard credentials **MUST NOT** be used as HTTP Basic auth. EMQX rejects
them on ordinary API calls:

```bash
curl -u "dashboard_user:password" "https://emqx.example:18083/api/v5/clients"
# HTTP 401
```

Use an API key and secret, created under Dashboard -> System -> API Key with
the narrowest role that works (`viewer` for read-only agents). Administrative
changes need a separate `administrator` key, referred to below as
`EMQX_ADMIN_KEY`:

```bash
curl -sS --fail-with-body \
  -u "${EMQX_API_KEY}:${EMQX_API_SECRET}" \
  "https://emqx.example:18083/api/v5/clients"
# HTTP 200
```

A `viewer` key is refused on writes, so the role is a real boundary:

```bash
curl -u "${EMQX_API_KEY}:${EMQX_API_SECRET}" -X PUT \
  "https://emqx.example:18083/api/v5/listeners/tcp:default" \
  -H 'Content-Type: application/json' -d '{"id":"tcp:default"}'
# HTTP 403 {"code":"UNAUTHORIZED_ROLE",...}
```

A role refusal is `403 UNAUTHORIZED_ROLE`. Agents **MUST NOT** treat `401` as
role denial: `/api/v5/api_key` returns `401 API_KEY_NOT_ALLOW` to *every* API
key regardless of role, because that path accepts bearer tokens only.

Dashboard credentials are valid in exactly one place: the JSON body of
`POST /api/v5/login`, which returns a short-lived bearer token.

```bash
TOKEN=$(curl -sS --fail-with-body -X POST \
  "https://emqx.example:18083/api/v5/login" \
  -H 'Content-Type: application/json' \
  -d "{\"username\":\"${EMQX_USER}\",\"password\":\"${EMQX_PASS}\"}" \
  | jq -r .token)

curl -sS --fail-with-body -H "Authorization: Bearer ${TOKEN}" \
  "https://emqx.example:18083/api/v5/clients"
```

**Why**: an API key is scoped by role and revocable on its own, whereas a
Dashboard account is a human login. All of the above **MUST** run over TLS;
Basic auth and bearer tokens are both replayable in clear text otherwise.

### REST API Queries

```bash
EMQX="https://emqx.example:18083/api/v5"
AUTH=(-u "${EMQX_API_KEY}:${EMQX_API_SECRET}")

# List all clients
curl -sS --fail-with-body "${AUTH[@]}" "${EMQX}/clients"

# Get client details
curl -sS --fail-with-body "${AUTH[@]}" "${EMQX}/clients/device123"

# List subscriptions
curl -sS --fail-with-body "${AUTH[@]}" "${EMQX}/subscriptions"

# Topic metrics for one topic
curl -sS --fail-with-body "${AUTH[@]}" "${EMQX}/topics?topic=sensors/kitchen"

# Retained messages: list returns metadata only
curl -sS --fail-with-body "${AUTH[@]}" \
  "${EMQX}/mqtt/retainer/messages?topic=sensors/%2B/temperature"

# Retained payload: use the detail endpoint (payload is base64)
curl -sS --fail-with-body "${AUTH[@]}" \
  "${EMQX}/mqtt/retainer/message/sensors%2Fkitchen%2Ftemperature" \
  | jq -r '.payload | @base64d'
```

### Useful EMQX Queries for Agents

Parameter names below come from the broker's own OpenAPI document
(`GET /api-docs/swagger.json` on EMQX 6.3.0).

```bash
# Find disconnected devices
GET /api/v5/clients?conn_state=disconnected

# Page size (limit, not _limit)
GET /api/v5/clients?limit=10&page=1

# Inspect one topic
GET /api/v5/topics?topic=sensors/kitchen/temperature
```

Unsupported query parameters are **silently ignored**, not rejected. EMQX
returns `HTTP 200` and the unfiltered result set:

| Invalid parameter | Real parameter | Observed effect |
| ----------------- | -------------- | --------------- |
| `status=disconnected` | `conn_state=disconnected` | No filtering applied |
| `_limit=10` | `limit=10` | `meta.limit` stayed at `100` |
| `_order_by=`, `_order=` | none | No ordering applied |
| `match_type=filter` | none | No wildcard matching |

`GET /clients` supports `node`, `username`, `ip_address`, `conn_state`,
`clean_start`, `proto_ver`, `like_clientid`, `like_username`, `clientid` and
the `gte_`/`lte_` time bounds. `GET /topics` supports only `topic` and `node`.

There is no server-side ordering parameter. Agents needing "top N by message
rate" **MUST** page through the result set and sort client-side.

**Why**: a silently ignored filter is worse than an error. An agent asking for
disconnected devices with `status=` receives every client and reports them all
as disconnected.

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

`max_publish_rate`, `max_subscribe_rate` and `max_message_size` are not EMQX
settings. Sending them returns `HTTP 400`:

```json
{
  "code": "BAD_REQUEST",
  "message": "{\"unknown\":\"max_message_size,max_publish_rate\",\"reason\":\"unknown_fields\"}"
}
```

Rate limits are listener properties. Set them on the listener:

```bash
curl -sS --fail-with-body -X PUT \
  "https://emqx.example:18083/api/v5/listeners/tcp:default" \
  -u "${EMQX_ADMIN_KEY}:${EMQX_ADMIN_SECRET}" \
  -H 'Content-Type: application/json' \
  -d '{"id":"tcp:default","type":"tcp","bind":"0.0.0.0:1883","enable":true,
       "messages_rate":"10/s","bytes_rate":"64KB/s","max_conn_rate":"500/s"}'
# HTTP 200; reads back as
# {"messages_rate":"10/s","bytes_rate":"64KB/s","max_conn_rate":"500/s"}
```

| Setting | Where | Meaning |
| ------- | ----- | ------- |
| `messages_rate` | listener | Inbound messages per client per node |
| `messages_burst` | listener | Burst allowance above `messages_rate` |
| `bytes_rate` | listener | Inbound bytes per client per node |
| `subscribes_rate` | listener | Subscribe operations per client |
| `max_conn_rate` | listener | Connection acceptance rate |
| `max_packet_size` | zone `mqtt` | Largest accepted packet (default `1MB`) |

Message size is capped by `max_packet_size` on the zone, not on the listener.
`PUT /configs/global_zone` replaces the entire document and rejects a partial
body with `400 {"reason":"required_field","path":"flapping_detect"}`, so read
the current configuration, modify it, and write it back:

```bash
EMQX="https://emqx.example:18083/api/v5"
AUTH=(-u "${EMQX_ADMIN_KEY}:${EMQX_ADMIN_SECRET}")

curl -sS --fail-with-body "${AUTH[@]}" "${EMQX}/configs/global_zone" \
  | jq '.mqtt.max_packet_size = "64KB"' > zone.json

curl -sS --fail-with-body -X PUT "${EMQX}/configs/global_zone" \
  "${AUTH[@]}" -H 'Content-Type: application/json' -d @zone.json
# HTTP 200

curl -sS --fail-with-body "${AUTH[@]}" "${EMQX}/configs/global_zone" \
  | jq -r '.mqtt.max_packet_size'
# 64KB
```

**Why**: EMQX rejects unknown listener fields outright, so an invented key is
not a silent no-op here — the whole update fails and the limit that was meant
to be applied is never applied.

Once `messages_rate` or `bytes_rate` is exceeded, EMQX drops QoS 0 messages and
rejects QoS 1 and QoS 2 with reason code `0x97` (Quota Exceeded).

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
