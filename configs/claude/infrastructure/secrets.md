# Agent Secrets Management

Secure credential access for AI agents using SOPS and other secret management
patterns.

## Overview

Agents need access to credentials for skills (database passwords, API tokens,
etc.) but this must be done securely:

```text
+---------------------------------------------------------------------------+
|                        SECRETS FLOW                                       |
+---------------------------------------------------------------------------+
|                                                                           |
|   +------------------+                                                    |
|   |  Encrypted       |    Decrypt at runtime                              |
|   |  secrets.yaml    | -------------------------+                         |
|   |  (in git)        |                          |                         |
|   +------------------+                          v                         |
|                                        +------------------+               |
|   +------------------+                 |   Environment    |               |
|   |  age/GPG keys    | --------------->|   Variables      |               |
|   |  (secure store)  |   Decryption    |                  |               |
|   +------------------+   key           +--------+---------+               |
|                                                 |                         |
|                                                 v                         |
|                                        +------------------+               |
|                                        |      Agent       |               |
|                                        |                  |               |
|                                        |  Uses secrets    |               |
|                                        |  via env vars    |               |
|                                        +------------------+               |
|                                                                           |
+---------------------------------------------------------------------------+
```

## SOPS Pattern

### What is SOPS?

SOPS (Secrets OPerationS) encrypts secrets in files that can be safely
committed to git:

```yaml
# secrets.yaml (encrypted with SOPS)
database:
    password: ENC[AES256_GCM,data:abc123...,type:str]
github:
    token: ENC[AES256_GCM,data:def456...,type:str]
discord:
    webhook_url: ENC[AES256_GCM,data:ghi789...,type:str]
sops:
    age:
        - age1ql3z7hjy54pw3hyww5...
    lastmodified: "2025-01-02T10:00:00Z"
    version: 3.7.3
```

### SOPS Setup

#### 1. Install SOPS and age

```bash
# macOS
brew install sops age

# Linux
# Download from https://github.com/getsops/sops/releases
# Download age from https://github.com/FiloSottile/age/releases
```

#### 2. Generate age key

```bash
# Generate key pair
age-keygen -o ~/.config/sops/age/keys.txt

# Output will show public key:
# Public key: age1ql3z7hjy54pw3hyww5...
```

#### 3. Configure SOPS

```yaml
# .sops.yaml (in repository root)
creation_rules:
  # Encrypt all secrets files with age
  - path_regex: secrets\.yaml$
    age: >-
      age1ql3z7hjy54pw3hyww5...,
      age1abc123...(team member 2),
      age1def456...(CI system)

  # Environment-specific keys
  - path_regex: secrets\.prod\.yaml$
    age: >-
      age1prod-key...

  - path_regex: secrets\.dev\.yaml$
    age: >-
      age1dev-key...,
      age1all-devs-key...
```

#### 4. Create Encrypted Secrets

```bash
# Create new encrypted file
sops secrets.yaml

# Editor opens with template:
database:
    password: your-password-here
github:
    token: ghp_xxxx

# Save and close - SOPS encrypts automatically

# Edit existing encrypted file
sops secrets.yaml

# Decrypt to stdout (for debugging)
sops -d secrets.yaml
```

### SOPS for Agent Access

#### Pattern 1: Environment Variable Injection

```bash
#!/bin/bash
# run-agent.sh - Launch agent with decrypted secrets

# Decrypt secrets and export as env vars
eval $(sops -d --output-type dotenv secrets.yaml)

# Or for specific secrets:
export POSTGRES_PASSWORD=$(sops -d --extract '["database"]["password"]' \
  secrets.yaml)
export GITHUB_TOKEN=$(sops -d --extract '["github"]["token"]' secrets.yaml)
export DISCORD_WEBHOOK=$(sops -d --extract '["discord"]["webhook_url"]' \
  secrets.yaml)

# Run agent with secrets in environment
claude "$@"
```

#### Pattern 2: Wrapper Script for Skills

```bash
#!/bin/bash
# sops-secret.sh - Fetch secret at runtime

SECRET_PATH="$1"
SECRETS_FILE="${SECRETS_FILE:-secrets.yaml}"

# Decrypt specific secret
sops -d --extract "[\"${SECRET_PATH}\"]" "$SECRETS_FILE"
```

Usage in MCP config:

```json
{
  "mcpServers": {
    "postgres": {
      "command": "mcp-postgres",
      "env": {
        "POSTGRES_PASSWORD": "$(sops-secret database.password)"
      }
    }
  }
}
```

#### Pattern 3: SOPS MCP Server

Create an MCP server that provides secret access:

```json
{
  "mcpServers": {
    "secrets": {
      "command": "mcp-sops-secrets",
      "env": {
        "SOPS_AGE_KEY_FILE": "${HOME}/.config/sops/age/keys.txt",
        "SECRETS_FILE": "secrets.yaml"
      }
    }
  }
}
```

**Capabilities:**

- `secrets.get` - Get a specific secret by path
- `secrets.list` - List available secret keys (not values)

**Security:** The MCP server logs all secret access to audit log.

### Secrets File Structure

```yaml
# secrets.yaml - Organized by skill/purpose

# Database credentials
databases:
  postgres:
    production:
      host: prod-db.example.com
      username: agent_readonly
      password: <encrypted>
    staging:
      host: staging-db.example.com
      username: agent_readonly
      password: <encrypted>

# Communication services
communication:
  github:
    token: <encrypted>
  discord:
    releases_webhook: <encrypted>
    alerts_webhook: <encrypted>

# Monitoring services
monitoring:
  prometheus:
    url: http://prometheus:9090
    # No auth needed for internal
  victorialogs:
    url: http://victorialogs:9428
  datadog:
    api_key: <encrypted>
    app_key: <encrypted>

# Cloud providers
cloud:
  aws:
    access_key_id: <encrypted>
    secret_access_key: <encrypted>
    region: us-east-1
```

## Alternative: HashiCorp Vault

For more complex environments, use Vault:

```yaml
# vault-config.yaml
vault:
  address: https://vault.example.com
  auth:
    method: kubernetes  # or: token, approle, aws
    role: agent-role

# Secrets paths
secrets:
  postgres: secret/data/agents/postgres
  github: secret/data/agents/github
  discord: secret/data/agents/discord
```

### Vault MCP Server

```json
{
  "mcpServers": {
    "vault": {
      "command": "mcp-vault",
      "env": {
        "VAULT_ADDR": "${VAULT_ADDR}",
        "VAULT_TOKEN": "${VAULT_TOKEN}"
      }
    }
  }
}
```

## SSH Key Management

For agents that need SSH access:

### Pattern: SSH Agent Forwarding

```bash
#!/bin/bash
# run-agent-with-ssh.sh

# Start ssh-agent and add keys
eval $(ssh-agent)
ssh-add ~/.ssh/agent_key

# Run agent with SSH access
claude "$@"

# Kill ssh-agent when done
ssh-agent -k
```

### Pattern: SOPS-Encrypted SSH Key

```yaml
# secrets.yaml
ssh:
  private_key: |
    ENC[AES256_GCM,data:abc123...(encrypted key content)...,type:str]
```

```bash
#!/bin/bash
# Load SSH key from SOPS

# Decrypt key to temp file
TEMP_KEY=$(mktemp)
sops -d --extract '["ssh"]["private_key"]' secrets.yaml > "$TEMP_KEY"
chmod 600 "$TEMP_KEY"

# Use key
ssh -i "$TEMP_KEY" user@server "command"

# Clean up
rm -f "$TEMP_KEY"
```

## Access Levels for Secrets

```yaml
# Define which agents can access which secrets
access_control:
  secrets:
    databases.postgres.production:
      allowed_agents:
        - ops/release-manager
        - ops/deploy-validator
        - security/incident-response-lead
      access_level: readonly
      audit: true

    communication.github.token:
      allowed_agents:
        - ops/release-manager
        - ops/changelog
      access_level: read-write  # Can create PRs
      audit: true

    communication.discord:
      allowed_agents:
        - ops/*
      access_level: post
      audit: true
```

## Security Best Practices

### Key Rotation

```bash
#!/bin/bash
# rotate-secrets.sh

# 1. Generate new age key
NEW_KEY=$(age-keygen 2>&1 | grep "public key" | cut -d: -f2 | tr -d ' ')

# 2. Add new key to .sops.yaml
# (manual step - add to age recipients)

# 3. Re-encrypt with new key
sops updatekeys secrets.yaml

# 4. Rotate the actual secrets
sops secrets.yaml
# Update passwords, tokens, etc.

# 5. Remove old key from .sops.yaml after transition period
```

### Audit Secret Access

```yaml
# All secret access MUST be logged
audit:
  secrets:
    log_access: true
    log_destination: agent_audit_log

    # Log entry format
    entry:
      timestamp: iso8601
      agent_id: string
      secret_path: string
      access_type: read | write
      # Never log the actual secret value!
```

### Environment Separation

```text
secrets/
+-- secrets.dev.yaml      # Dev secrets, all devs can access
+-- secrets.staging.yaml  # Staging, ops team access
+-- secrets.prod.yaml     # Production, restricted access
+-- .sops.yaml            # Different keys per environment
```

### CI/CD Integration

```yaml
# GitHub Actions example
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install SOPS
        run: |
          curl -LO \
            https://github.com/getsops/sops/releases/download/v3.8.1/sops-v3.8.1.linux.amd64
          chmod +x sops-v3.8.1.linux.amd64
          sudo mv sops-v3.8.1.linux.amd64 /usr/local/bin/sops

      - name: Decrypt secrets
        env:
          SOPS_AGE_KEY: ${{ secrets.SOPS_AGE_KEY }}
        run: |
          sops -d secrets.prod.yaml > /tmp/secrets.yaml
          # Use secrets...
          rm /tmp/secrets.yaml
```

## CLI Access Patterns

For agents using SSH + CLI:

```bash
#!/bin/bash
# agent-ssh-command.sh - Run command on remote server with secrets

SERVER="$1"
COMMAND="$2"

# Get SSH key from SOPS
SSH_KEY=$(mktemp)
sops -d --extract '["ssh"]["private_key"]' secrets.yaml > "$SSH_KEY"
chmod 600 "$SSH_KEY"

# Get any needed env vars
DB_PASSWORD=$(sops -d \
  --extract '["databases"]["postgres"]["production"]["password"]' \
  secrets.yaml)

# Run command on remote server
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=accept-new "$SERVER" \
  "export DB_PASSWORD='$DB_PASSWORD'; $COMMAND"

# Clean up
rm -f "$SSH_KEY"
```

## Summary

| Pattern | Use Case | Complexity |
| ------- | -------- | ---------- |
| **SOPS + age** | Small-medium teams, git-based workflow | Low |
| **SOPS + GPG** | Existing GPG infrastructure | Medium |
| **HashiCorp Vault** | Enterprise, dynamic secrets | High |
| **Cloud KMS** | Cloud-native, managed service | Medium |

**Recommended**: Start with SOPS + age for simplicity, migrate to Vault if
you need dynamic secrets or fine-grained access control.
