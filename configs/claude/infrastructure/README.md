# Agent Infrastructure

Infrastructure patterns for running AI agents in production environments.

## Overview

```text
+---------------------------------------------------------------------------+
|                        AGENT INFRASTRUCTURE                               |
+---------------------------------------------------------------------------+
|                                                                           |
|   +-------------+  +-------------+  +-------------+  +-------------+      |
|   |   Agents    |  |   Skills    |  |   Secrets   |  |   Audit     |      |
|   |             |  |             |  |             |  |             |      |
|   | - ops/      |  | - postgres  |  | - SOPS      |  | - Actions   |      |
|   | - security/ |  | - github    |  | - Vault     |  | - Decisions |      |
|   | - code/     |  | - discord   |  | - env vars  |  | - Outcomes  |      |
|   | - docs/     |  | - prometheus|  |             |  |             |      |
|   +------+------+  +------+------+  +------+------+  +------+------+      |
|          |                |                |                |             |
|          +----------------+----------------+----------------+             |
|                                    |                                      |
|                          +---------v---------+                            |
|                          |   Coordination    |                            |
|                          |                   |                            |
|                          | - Shared State    |                            |
|                          | - Message Bus     |                            |
|                          | - Task Queue      |                            |
|                          +-------------------+                            |
|                                                                           |
+---------------------------------------------------------------------------+
```

## Components

| Component | Purpose | Document |
| --------- | ------- | -------- |
| **Coordination** | Multi-agent state sharing and task distribution | [coordination.md](coordination.md) |
| **Audit** | Log all agent actions for compliance and learning | [audit.md](audit.md) |
| **Secrets** | Secure credential access for agents | [secrets.md](secrets.md) |

## Access Patterns

Agents interact with infrastructure through multiple mechanisms:

```text
+---------------------------------------------------------------------------+
|                        ACCESS PATTERNS                                    |
+---------------------------------------------------------------------------+
|                                                                           |
|   MCP SERVERS              API CALLS               CLI / SSH              |
|   -----------              ---------               ---------              |
|   - Structured tools       - Direct HTTP           - Shell commands       |
|   - Type-safe              - Flexible              - Full system access   |
|   - Sandboxed              - Rate-limited          - Requires trust       |
|                                                                           |
|   Best for:                Best for:               Best for:              |
|   - Database queries       - Web services          - Server admin         |
|   - File operations        - Cloud APIs            - Package management   |
|   - Standard integrations  - Custom services       - System diagnostics   |
|                                                                           |
|   Examples:                Examples:               Examples:              |
|   - postgres MCP           - Prometheus API        - systemctl status     |
|   - github MCP             - Discord webhooks      - docker ps            |
|   - filesystem MCP         - AWS SDK calls         - journalctl           |
|                                                                           |
+---------------------------------------------------------------------------+
```

## Security Model

All infrastructure components share a security model:

### Principle of Least Privilege

- Agents receive minimum required permissions
- Permissions scoped to specific resources
- Time-bounded access where possible

### Defense in Depth

- Multiple layers of access control
- Audit logging at every layer
- Anomaly detection on agent behavior

### Human Oversight

- High-risk actions require approval
- Escalation paths defined
- Kill switches available
