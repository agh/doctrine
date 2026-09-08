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

`sops exec-env` decrypts into the environment of one child process. Nothing is
written to disk, and a failed decryption stops the launch instead of starting
the agent with empty variables.

The file `exec-env` reads **MUST** be flat, one top-level key per variable.
SOPS rejects a nested document with `cannot use complex value in environment;
offending key <name>`, so keep the environment file separate from any nested
`secrets.yaml`:

```yaml
# secrets.env.yaml - one top-level key per environment variable
POSTGRES_PASSWORD: ENC[AES256_GCM,data:abc123...,type:str]
GITHUB_TOKEN: ENC[AES256_GCM,data:def456...,type:str]
DISCORD_WEBHOOK: ENC[AES256_GCM,data:ghi789...,type:str]
```

```bash
#!/usr/bin/env bash
# run-agent.sh - launch the agent with decrypted secrets

set -euo pipefail

SECRETS_FILE="${SECRETS_FILE:-secrets.env.yaml}"

if [[ -z "${AGENT_SECRETS_LOADED:-}" ]]; then
  # Re-exec this script inside the decrypted environment. sops exits
  # non-zero when decryption fails, so the agent never starts without
  # its secrets. printf %q preserves the original arguments.
  exec sops exec-env "${SECRETS_FILE}" \
    "AGENT_SECRETS_LOADED=1 $(printf '%q ' "$0" "$@")"
fi

exec claude "$@"
```

**Why**: `eval $(sops -d ...)` interprets decrypted values as shell source, and
both `eval` and `export NAME=$(...)` return the status of `eval`/`export`, not
of `sops`. A failed decryption therefore launches the agent with empty
credentials. `exec-env` passes the values as data to a single child.

**Don't** — every failure here is silent:

```bash
eval $(sops -d --output-type dotenv secrets.yaml)
export POSTGRES_PASSWORD=$(sops -d --extract '["database"]["password"]' \
  secrets.yaml)
```

`--pristine` clears every inherited variable, including `HOME`, so it **SHOULD
NOT** be used for tools that read a home directory, such as Claude Code.
Reserve it for a child process that needs nothing but its secrets.

#### Pattern 2: Wrapper Script for Skills

`exec-env` needs a flat file. To read one value out of a nested file, extract
it by path. The helper takes a dotted path and builds the SOPS extraction
expression from it:

```bash
#!/usr/bin/env bash
# sops-secret - print one secret from a nested SOPS file

set -euo pipefail

SECRET_PATH="${1:?usage: sops-secret <dotted.path>}"
SECRETS_FILE="${SECRETS_FILE:-secrets.yaml}"

extract=""
IFS='.' read -ra components <<< "${SECRET_PATH}"
for component in "${components[@]}"; do
  extract+="[\"${component}\"]"
done

sops -d --extract "${extract}" "${SECRETS_FILE}"
```

`sops-secret database.password` extracts `["database"]["password"]` and exits
non-zero, with the SOPS error, when the path is absent.

**Why**: a SOPS extraction expression addresses one component per bracket
pair. Wrapping the whole argument in a single pair asks for a key literally
named `database.password`, which fails with `error truncating tree: component
['database.password'] not found`.

**Don't**:

```bash
sops -d --extract "[\"${SECRET_PATH}\"]" "$SECRETS_FILE"
```

Usage in MCP config:

```json
{
  "mcpServers": {
    "postgres": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@bytebase/dbhub@1.2.3"],
      "env": {
        "DSN": "postgres://agent_readonly:${POSTGRES_PASSWORD}@db:5432/app"
      }
    }
  }
}
```

Claude Code expands `${VAR}` and `${VAR:-default}` in an MCP server's
`command`, `args`, `env`, `url`, and `headers`. It **MUST NOT** be given shell
command substitution: `"$(sops-secret database.password)"` reaches the server
as that literal string. Put the value in Claude Code's own environment first,
then reference it:

```bash
sops exec-env secrets.env.yaml claude
claude mcp get postgres   # ✔ Connected
```

**Don't**:

```json
{ "env": { "POSTGRES_PASSWORD": "$(sops-secret database.password)" } }
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
#!/usr/bin/env bash
# rotate-age-key.sh - replace the age identity that decrypts secrets.yaml

set -euo pipefail
umask 077

NEW_KEY_FILE="${1:?usage: rotate-age-key.sh <new-identity-file>}"

# 1. Generate and persist the new identity (mode 0600 from the umask)
age-keygen -o "${NEW_KEY_FILE}"

# 2. Derive the recipient that belongs in .sops.yaml
NEW_RECIPIENT="$(age-keygen -y "${NEW_KEY_FILE}")"
echo "Add this recipient to .sops.yaml next to the current one:"
echo "  ${NEW_RECIPIENT}"
read -r -p "Press enter once .sops.yaml lists both recipients: " _

# 3. Re-encrypt the data key to both recipients (overlap period)
sops updatekeys --yes secrets.yaml

# 4. Prove the new identity works before anything is retired
SOPS_AGE_KEY_FILE="${NEW_KEY_FILE}" sops -d secrets.yaml > /dev/null
echo "New identity verified against secrets.yaml."

# 5. Rotate the secret values themselves
sops secrets.yaml

# 6. Remove the old recipient from .sops.yaml, then run
#    sops updatekeys --yes secrets.yaml again to retire it
```

**Why**: `age-keygen` writes the private identity to stdout, or to the `-o`
file, and prints only the public recipient to stderr. A pipeline that greps
stderr for the public key therefore keeps the recipient and throws the
identity away. Existing recipients still decrypt during the overlap, so the
loss stays hidden until the old key is retired — at which point the file is
unreadable.

**Don't** — this persists no private key:

```bash
NEW_KEY=$(age-keygen 2>&1 | grep "public key" | cut -d: -f2 | tr -d ' ')
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

      - name: Run the deploy with secrets in its environment
        env:
          SOPS_AGE_KEY: ${{ secrets.SOPS_AGE_KEY }}
        run: sops exec-env secrets.env.yaml ./deploy.sh

      - name: Run a tool that needs a secrets file
        env:
          SOPS_AGE_KEY: ${{ secrets.SOPS_AGE_KEY }}
        run: sops exec-file secrets.prod.yaml './deploy.sh --config {}'
```

**Why**: a shell redirection writes plaintext to disk before the consumer
runs, and `rm` on the success path never executes when decryption or the
consumer fails — under the common `umask 022` the leftover file is mode 0644
on a runner whose workspace other steps and caches can read. `exec-env` keeps
the values in one child's environment; `exec-file` passes them through a FIFO,
so the plaintext never reaches disk and disappears when the child exits. Both
abort the step when decryption fails.

**Don't**:

```yaml
        run: |
          sops -d secrets.prod.yaml > /tmp/secrets.yaml
          # Use secrets...
          rm /tmp/secrets.yaml
```

## CLI Access Patterns

For agents using SSH + CLI:

```bash
#!/usr/bin/env bash
# agent-ssh-command.sh - run a named task on a remote server

set -euo pipefail

SERVER="${1:?usage: agent-ssh-command.sh <server> <task>}"
TASK="${2:?usage: agent-ssh-command.sh <server> <task>}"

SSH_KEY="$(mktemp)"
trap 'rm -f "${SSH_KEY}"' EXIT INT TERM
chmod 600 "${SSH_KEY}"
sops -d --extract '["ssh"]["private_key"]' secrets.yaml > "${SSH_KEY}"

# The remote task fetches its own credentials, so no secret crosses the
# wire and none appears in the remote command line
ssh -i "${SSH_KEY}" -o StrictHostKeyChecking=accept-new "${SERVER}" \
  /usr/local/bin/agent-task "${TASK}"
```

When a remote host genuinely cannot reach a secret store, send the value on
stdin and let the remote shell read it as data:

```bash
DB_PASSWORD="$(sops -d \
  --extract '["databases"]["postgres"]["production"]["password"]' \
  secrets.yaml)"

printf '%s\n' "${DB_PASSWORD}" |
  ssh -i "${SSH_KEY}" -o StrictHostKeyChecking=accept-new "${SERVER}" \
    'IFS= read -r DB_PASSWORD; export DB_PASSWORD; exec /usr/local/bin/agent-task'
```

**Why**: `ssh` joins its command arguments into one string that the remote
login shell re-parses, so an interpolated secret becomes remote shell source.
A password containing `'` ends the quoting and the command dies with
`unexpected EOF while looking for matching "'"` before the task runs; a
password containing `$(...)` would be executed. Values read from stdin are
never parsed and never appear in `ps` output on either host. `TASK` **MUST**
come from a fixed set of task names, because it is re-parsed remotely too.
`read` consumes one line, so a secret that contains a newline **MUST** be
encoded, for example with `base64`, before it is sent.

**Don't**:

```bash
ssh -i "$SSH_KEY" "$SERVER" "export DB_PASSWORD='$DB_PASSWORD'; $COMMAND"
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
