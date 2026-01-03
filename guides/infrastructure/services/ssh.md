# SSH Configuration Guide

> [Doctrine](../../../README.md) > [Infrastructure](../README.md) > [Services](README.md) > SSH

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

## Quick Reference

| Task | Command |
| ---- | ------- |
| Test config | `sshd -t` |
| Reload config | `systemctl reload sshd` |
| Check auth log | `journalctl -u ssh -f` |
| Generate key | `ssh-keygen -t ed25519` |
| Copy key | `ssh-copy-id user@host` |

---

## Table of Contents

1. [Server Configuration](#server-configuration)
2. [Authentication](#authentication)
3. [Access Control](#access-control)
4. [Cryptographic Settings](#cryptographic-settings)
5. [Client Configuration](#client-configuration)
6. [Key Management](#key-management)
7. [fail2ban](#fail2ban)
8. [Monitoring](#monitoring)

---

## Server Configuration

### Hardened sshd_config

Projects **MUST** apply these security settings:

```bash
# /etc/ssh/sshd_config.d/99-hardening.conf

# Protocol
Protocol 2

# Port (change from default if desired)
Port 22
# Port 2222  # Non-standard port reduces noise

# Listen address (bind to specific interface if needed)
# ListenAddress 192.168.1.1
# ListenAddress 100.64.0.1  # Tailscale only

# Authentication
PermitRootLogin no
PubkeyAuthentication yes
PasswordAuthentication no
PermitEmptyPasswords no
ChallengeResponseAuthentication no
KbdInteractiveAuthentication no
UsePAM yes

# Access control
AllowUsers deploy admin
# Or by group:
# AllowGroups ssh-users admins

# Security
X11Forwarding no
AllowTcpForwarding no
AllowAgentForwarding no
PermitTunnel no
GatewayPorts no
PermitUserEnvironment no
StrictModes yes

# Session
ClientAliveInterval 300
ClientAliveCountMax 2
MaxAuthTries 3
MaxSessions 2
LoginGraceTime 60

# Logging
LogLevel VERBOSE
SyslogFacility AUTH

# Banners
Banner /etc/ssh/banner
PrintMotd no
PrintLastLog yes
```

### Testing Configuration

```bash
# Validate syntax before reloading
sshd -t

# Test with verbose output
sshd -t -d

# Reload (not restart - keeps existing connections)
systemctl reload sshd
```

### Configuration Files

| Path | Purpose |
| ---- | ------- |
| `/etc/ssh/sshd_config` | Main server config |
| `/etc/ssh/sshd_config.d/*.conf` | Drop-in overrides (Debian 12+) |
| `/etc/ssh/ssh_host_*_key` | Host private keys |
| `/etc/ssh/ssh_host_*_key.pub` | Host public keys |
| `/etc/ssh/banner` | Pre-login banner |

---

## Authentication

### Key-Only Authentication

Projects **MUST** disable password authentication:

```bash
# /etc/ssh/sshd_config.d/99-hardening.conf
PasswordAuthentication no
KbdInteractiveAuthentication no
ChallengeResponseAuthentication no
```

### Authorized Keys

```bash
# User's authorized keys
~/.ssh/authorized_keys

# Permissions (critical!)
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

### Key Options

Restrict key capabilities in `authorized_keys`:

```bash
# Basic key
ssh-ed25519 AAAA... user@host

# Restrict to specific source IP
from="192.168.1.0/24,10.0.0.5" ssh-ed25519 AAAA... user@host

# Force specific command (deploy key)
command="/usr/local/bin/deploy.sh",no-port-forwarding,no-agent-forwarding \
  ssh-ed25519 AAAA... deploy-key

# Read-only SFTP (file transfer only)
command="internal-sftp",no-port-forwarding,no-agent-forwarding,no-X11-forwarding \
  ssh-ed25519 AAAA... sftp-only

# Combined restrictions
from="10.0.0.0/8",command="/usr/bin/rsync --server --sender .",no-pty \
  ssh-ed25519 AAAA... backup-key
```

### Certificate-Based Authentication

For larger deployments, projects **SHOULD** use SSH certificates:

```bash
# Generate CA key (keep secure!)
ssh-keygen -t ed25519 -f ssh-ca -C "SSH CA"

# Sign user key (valid 30 days)
ssh-keygen -s ssh-ca -I "user@example.com" -n username -V +30d user-key.pub

# Sign host key
ssh-keygen -s ssh-ca -I "server.example.com" -h -n server.example.com \
  /etc/ssh/ssh_host_ed25519_key.pub
```

Server configuration for CA:

```bash
# /etc/ssh/sshd_config.d/99-ca.conf
TrustedUserCAKeys /etc/ssh/ca.pub
```

---

## Access Control

### AllowUsers / AllowGroups

Projects **MUST** explicitly allow users or groups:

```bash
# Allow specific users
AllowUsers alice bob deploy

# Allow by group (preferred for larger teams)
AllowGroups ssh-users admins

# Combined: user from specific host
AllowUsers deploy@10.0.0.*
```

**Why**: Default SSH allows all local users. Explicit allowlists prevent
unauthorized access if a new user is created.

### DenyUsers / DenyGroups

```bash
# Deny specific users (in addition to allow)
DenyUsers guest test

# Deny groups
DenyGroups no-ssh
```

### Match Blocks

Apply settings to specific users/groups/hosts:

```bash
# /etc/ssh/sshd_config.d/99-match.conf

# SFTP-only users
Match Group sftp-only
    ForceCommand internal-sftp
    ChrootDirectory /srv/sftp/%u
    AllowTcpForwarding no
    X11Forwarding no

# Restricted deploy user
Match User deploy
    AllowTcpForwarding no
    X11Forwarding no
    PermitTTY no
    ForceCommand /usr/local/bin/deploy.sh

# Allow forwarding for specific user
Match User tunnel-user
    AllowTcpForwarding yes
```

---

## Cryptographic Settings

### Modern Algorithms Only

Projects **MUST** disable legacy algorithms:

```bash
# /etc/ssh/sshd_config.d/99-crypto.conf

# Key exchange (most secure first)
KexAlgorithms sntrup761x25519-sha512@openssh.com,curve25519-sha256,curve25519-sha256@libssh.org

# Host key algorithms
HostKeyAlgorithms ssh-ed25519-cert-v01@openssh.com,ssh-ed25519,rsa-sha2-512-cert-v01@openssh.com,rsa-sha2-512

# Ciphers
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com

# MACs
MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com
```

### Host Keys

Regenerate host keys if needed:

```bash
# Remove old keys
rm /etc/ssh/ssh_host_*

# Regenerate (Ed25519 and RSA only)
ssh-keygen -t ed25519 -f /etc/ssh/ssh_host_ed25519_key -N ""
ssh-keygen -t rsa -b 4096 -f /etc/ssh/ssh_host_rsa_key -N ""

# Remove DSA and ECDSA (if present)
rm -f /etc/ssh/ssh_host_dsa_key* /etc/ssh/ssh_host_ecdsa_key*
```

Configure which keys to use:

```bash
# /etc/ssh/sshd_config.d/99-hostkeys.conf
HostKey /etc/ssh/ssh_host_ed25519_key
HostKey /etc/ssh/ssh_host_rsa_key
```

---

## Client Configuration

### User SSH Config

```bash
# ~/.ssh/config

# Defaults for all hosts
Host *
    AddKeysToAgent yes
    IdentitiesOnly yes
    ServerAliveInterval 60
    ServerAliveCountMax 3

# Specific host
Host prod
    HostName prod.example.com
    User deploy
    IdentityFile ~/.ssh/deploy_ed25519
    Port 2222

# Jump host (bastion)
Host internal-*
    ProxyJump bastion.example.com
    User admin

Host bastion.example.com
    User admin
    IdentityFile ~/.ssh/bastion_ed25519

# Git hosting
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/github_ed25519

Host gitlab.com
    HostName gitlab.com
    User git
    IdentityFile ~/.ssh/gitlab_ed25519
```

### ProxyJump (Bastion)

```bash
# Direct command
ssh -J bastion.example.com internal-server

# Via config (above)
ssh internal-server

# Multiple jumps
ssh -J bastion1,bastion2 internal-server
```

---

## Key Management

### Generate Keys

Projects **MUST** use Ed25519 for new keys:

```bash
# Ed25519 (recommended)
ssh-keygen -t ed25519 -C "user@example.com" -f ~/.ssh/id_ed25519

# RSA (for legacy systems)
ssh-keygen -t rsa -b 4096 -C "user@example.com" -f ~/.ssh/id_rsa

# With specific filename
ssh-keygen -t ed25519 -C "deploy@prod" -f ~/.ssh/deploy_ed25519
```

### Key Types

| Type | Key Size | Security | Use Case |
| ---- | -------- | -------- | -------- |
| Ed25519 | 256-bit | Excellent | Default choice |
| RSA | 4096-bit | Good | Legacy compatibility |
| ECDSA | 256-bit | Good | Avoid (NSA curve concerns) |
| DSA | 1024-bit | Weak | **Never use** |

### SSH Agent

```bash
# Start agent
eval "$(ssh-agent -s)"

# Add key (with passphrase prompt)
ssh-add ~/.ssh/id_ed25519

# List loaded keys
ssh-add -l

# Add with timeout (1 hour)
ssh-add -t 3600 ~/.ssh/id_ed25519

# macOS: Use Keychain
ssh-add --apple-use-keychain ~/.ssh/id_ed25519
```

### Key Rotation

Projects **SHOULD** rotate keys annually:

1. Generate new key
2. Add new public key to `authorized_keys`
3. Test new key
4. Remove old public key from `authorized_keys`
5. Archive or destroy old private key

---

## fail2ban

### Installation

```bash
apt install fail2ban
```

### SSH Jail Configuration

```bash
# /etc/fail2ban/jail.d/sshd.local
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
findtime = 600
bantime = 3600
ignoreip = 127.0.0.1/8 10.0.0.0/8 192.168.0.0/16
```

### Aggressive Mode

```bash
# /etc/fail2ban/jail.d/sshd-aggressive.local
[sshd-aggressive]
enabled = true
port = ssh
filter = sshd[mode=aggressive]
logpath = /var/log/auth.log
maxretry = 1
findtime = 86400
bantime = 604800
```

### Management Commands

```bash
# Status
fail2ban-client status sshd

# Unban IP
fail2ban-client set sshd unbanip 192.168.1.100

# Ban IP manually
fail2ban-client set sshd banip 192.168.1.100

# Reload config
fail2ban-client reload
```

---

## Monitoring

### Log Locations

| Distribution | Auth Log |
| ------------ | -------- |
| Debian/Ubuntu | `/var/log/auth.log` |
| RHEL/Fedora | `/var/log/secure` |
| systemd | `journalctl -u ssh` |

### Useful Commands

```bash
# Recent SSH logins
journalctl -u ssh --since "1 hour ago"

# Failed login attempts
grep "Failed password" /var/log/auth.log | tail -20

# Successful logins
grep "Accepted" /var/log/auth.log | tail -20

# Connection attempts by IP
grep "sshd" /var/log/auth.log | grep -oP '\d+\.\d+\.\d+\.\d+' | \
  sort | uniq -c | sort -rn | head

# Currently connected
who
w

# Active SSH sessions
ss -tnp | grep ssh
```

### Log Verbosity

For debugging:

```bash
# /etc/ssh/sshd_config
LogLevel DEBUG3  # Very verbose
LogLevel VERBOSE # Recommended for production
LogLevel INFO    # Default
```

---

## Quick Hardening Checklist

- [ ] `PermitRootLogin no`
- [ ] `PasswordAuthentication no`
- [ ] `PubkeyAuthentication yes`
- [ ] `AllowUsers` or `AllowGroups` configured
- [ ] Modern ciphers/MACs/KEX only
- [ ] `X11Forwarding no`
- [ ] `AllowTcpForwarding no` (unless needed)
- [ ] `MaxAuthTries 3`
- [ ] `LoginGraceTime 60`
- [ ] fail2ban installed and enabled
- [ ] Host keys are Ed25519/RSA only
- [ ] `LogLevel VERBOSE`

---

## See Also

- [Linux Guide](../os/linux.md) — System hardening
- [Ansible Guide](../ansible.md) — Automated SSH configuration
- [OS Fundamentals](../os/README.md) — User and permission basics

---

## References

- [OpenSSH Manual](https://www.openssh.com/manual.html)
- [Mozilla SSH Guidelines](https://infosec.mozilla.org/guidelines/openssh)
- [SSH Audit](https://github.com/jtesta/ssh-audit) - SSH configuration auditing
- [CIS Benchmark - SSH](https://www.cisecurity.org/benchmark/distribution_independent_linux)
