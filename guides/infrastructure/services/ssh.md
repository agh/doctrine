# SSH Configuration Guide

> [Doctrine](../../../README.md) > [Infrastructure](../README.md) > [Services](README.md) > SSH

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

## Quick Reference

| Task | Command |
| ---- | ------- |
| Test config syntax | `sshd -t` |
| Show effective config | `sshd -T` |
| Show config for one connection | `sshd -T -C user=deploy,addr=10.0.0.5,host=h` |
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
# /etc/ssh/sshd_config.d/00-site-hardening.conf

# Protocol
Protocol 2

# Port: this value MUST match the fail2ban jails, firewall rules and client
# config. Changing it requires the coordinated procedure in "Changing the
# Listening Port".
Port 22

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
AllowStreamLocalForwarding no
PermitTunnel no
GatewayPorts no
PermitUserEnvironment no
PermitUserRC no
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

### Drop-in Precedence

Drop-in files **MUST** be named so that site policy is read before any vendor
or cloud-init snippet. Projects **MUST NOT** rely on a `99-` prefix to override
earlier files.

**Why**: `sshd_config` is not last-wins. `sshd_config(5)` states that "for each
keyword, the first obtained value will be used", and `Include` splices matching
files in lexical order at the point of the `Include` directive. Debian, Ubuntu
and RHEL place `Include /etc/ssh/sshd_config.d/*.conf` at the top of
`/etc/ssh/sshd_config`, so `50-cloud-init.conf` is read before
`99-hardening.conf` and wins every directive both files set.

```bash
# Don't: 50-cloud-init.conf is read first, so this file changes nothing
# /etc/ssh/sshd_config.d/99-hardening.conf
PasswordAuthentication no

# Do: sorts before vendor snippets, so its values are the first obtained
# /etc/ssh/sshd_config.d/00-site-hardening.conf
PasswordAuthentication no
```

Inventory the include tree and prove the effective value before deployment:

```bash
# Every file that contributes settings, in the order sshd reads them
grep -rn '^[[:space:]]*Include' /etc/ssh/sshd_config
ls -1 /etc/ssh/sshd_config.d/

# The value sshd actually uses, not the value the last file requested
sshd -T | grep -iE '^(passwordauthentication|permitrootlogin|pubkeyauthentication)'
```

**Why**: `sshd -T` prints the effective configuration after all includes are
resolved. It is the only check that distinguishes a policy that is applied from
one that is merely present in a file.

### Validating and Rolling Out Changes

Projects **MUST** follow this order when changing authentication, allowlists,
the listening port or host keys. Every step **MUST** complete before the
original administrative session is closed.

```bash
# 1. Back up the whole configuration, including drop-ins
install -d -m 700 /root/ssh-backup
cp -a /etc/ssh/sshd_config /etc/ssh/sshd_config.d /root/ssh-backup/

# 2. Check syntax (exits non-zero and prints the offending line on failure)
sshd -t

# 3. Check the effective global policy
sshd -T | grep -iE '^(port|permitrootlogin|passwordauthentication|allowusers|allowgroups)'

# 4. Check every Match block that must apply, one connection profile at a time
sshd -T -C user=deploy,addr=10.0.0.5,host=deploy.example.com | grep -i forcecommand
sshd -T -C user=admin,addr=10.0.0.6,host=admin.example.com | grep -i permittty

# 5. Confirm the account you will log in with survives the new policy
grep -c '^[^#]' ~admin/.ssh/authorized_keys   # key present
sshd -T | grep -i '^allowusers'               # account listed

# 6. Arm a timed rollback that fires if verification fails
cat > /usr/local/sbin/sshd-rollback <<'EOF'
#!/bin/sh
cp -a /root/ssh-backup/sshd_config /root/ssh-backup/sshd_config.d /etc/ssh/
systemctl reload sshd
EOF
chmod 700 /usr/local/sbin/sshd-rollback
systemd-run --unit=sshd-rollback --on-active=10min /usr/local/sbin/sshd-rollback

# 7. Reload (not restart - keeps existing connections)
systemctl reload sshd

# 8. Confirm the daemon is listening where you expect
ss -tlnp | grep sshd

# 9. From a SECOND terminal, open a new connection and prove it authenticates
ssh -o BatchMode=yes admin@server.example.com true && echo "login OK"

# 10. Only after step 9 succeeds, cancel the rollback and close the first session
systemctl stop sshd-rollback.timer
```

**Why**: `sshd -t` proves only that the file parses. It cannot prove that the
intended administrator still matches `AllowUsers`, still has a usable key after
`PasswordAuthentication no`, or that the daemon is reachable on a changed port.
Ubuntu's OpenSSH documentation warns that losing the SSH server can mean losing
all access to the host, so the surviving session and the timed rollback are the
recovery path.

If step 9 fails, restore from `/root/ssh-backup` in the still-open session and
reload. If both sessions are lost, recovery requires console, serial or
hypervisor access.

```bash
# Don't: syntax check then reload, with no proof anyone can still log in
sshd -t && systemctl reload sshd
```

### Configuration Files

| Path | Purpose |
| ---- | ------- |
| `/etc/ssh/sshd_config` | Main server config |
| `/etc/ssh/sshd_config.d/*.conf` | Drop-in policy files, read in lexical order (Debian 12+) |
| `/etc/ssh/ssh_host_*_key` | Host private keys |
| `/etc/ssh/ssh_host_*_key.pub` | Host public keys |
| `/etc/ssh/banner` | Pre-login banner |

---

## Authentication

### Key-Only Authentication

Projects **MUST** disable password authentication:

```bash
# /etc/ssh/sshd_config.d/00-site-hardening.conf
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

Every `authorized_keys` record — options, key type, key material and comment —
**MUST** occupy one physical line. Restricted keys **MUST** be built from
`restrict`, re-enabling only the capabilities that key needs.

```bash
# Basic key
ssh-ed25519 AAAA... user@host

# Restrict to specific source IP
from="192.168.1.0/24,10.0.0.5",restrict ssh-ed25519 AAAA... user@host

# Force specific command (deploy key)
restrict,command="/usr/local/bin/deploy.sh" ssh-ed25519 AAAA... deploy-key

# Read-only SFTP: -R denies uploads, renames, deletes and permission changes
restrict,command="internal-sftp -R" ssh-ed25519 AAAA... sftp-only

# Combined restrictions
from="10.0.0.0/8",restrict,command="/usr/bin/rsync --server --sender ." ssh-ed25519 AAAA... backup
```

**Why**: `sshd(8)` specifies that each line of the file contains one key, with
the optional options field on the same line as the key. There is no line
continuation syntax. `restrict` (OpenSSH 7.2 and later) disables port, agent
and X11 forwarding, PTY allocation and `~/.ssh/rc` execution, and automatically
includes any restriction added by later releases; an explicit `no-*` list
silently omits whatever it does not name.

**Why (`-R`)**: `internal-sftp` and `sftp-server` allow writes wherever
filesystem permissions permit them. `sftp-server(8)` documents `-R` as the
option that places the server in read-only mode and denies operations that
change the state of the filesystem. A forced command without `-R` is not a
read-only service, whatever the key comment says.

```bash
# Don't: a backslash does not continue an authorized_keys record
command="internal-sftp",no-port-forwarding,no-agent-forwarding \
  ssh-ed25519 AAAA... sftp-only
```

The wrapped form is two records, not one. Line 1 is discarded as malformed and
line 2 is accepted as a plain, unrestricted key: it grants a shell, forwarding
and a PTY to anyone holding that private key.

Verify authorized keys after every edit:

```bash
# No record may end with a backslash
grep -n '\\$' ~/.ssh/authorized_keys && echo "BROKEN: wrapped record"

# Every key sshd will accept, one line per record
ssh-keygen -l -f ~/.ssh/authorized_keys

# Prove the read-only SFTP key: the download succeeds, the upload is refused
printf 'get readme.txt\nput local.txt\n' | sftp -b - sftp-only@server.example.com
# sftp> get readme.txt
# sftp> put local.txt
# dest open "/local.txt": Permission denied
```

### Certificate-Based Authentication

For larger deployments, projects **SHOULD** use SSH certificates. Projects
**MUST** use one CA for user keys and a separate CA for host keys, and **MUST**
complete the installation steps on both sides; a signed key that is never
installed and configured changes nothing.

**Why**: `TrustedUserCAKeys` must name the file the user CA public key was
actually copied to, `HostCertificate` must name the signed host certificate
because `sshd` loads no certificate by default, and clients must trust the host
CA through an `@cert-authority` line in `known_hosts`. Signing alone leaves the
estate on raw-key trust while appearing to be certificate-based.

#### User Certificates

```bash
# 1. On an offline CA host: create the user CA, protected by a passphrase
ssh-keygen -t ed25519 -f user_ca -C "user CA"

# 2. Sign a user key; principals MUST be the account names the holder may use
ssh-keygen -s user_ca -I alice@example.com -n alice -V +30d alice_ed25519.pub

# 3. Check what you signed before shipping it
ssh-keygen -L -f alice_ed25519-cert.pub

# 4. Install the CA public key on every server, at the configured path
install -o root -g root -m 644 user_ca.pub /etc/ssh/trusted_user_ca.pub
```

```bash
# /etc/ssh/sshd_config.d/00-site-ca.conf
TrustedUserCAKeys /etc/ssh/trusted_user_ca.pub
```

The client offers `alice_ed25519-cert.pub` automatically when it sits beside
the private key `alice_ed25519`.

#### Host Certificates

```bash
# 1. On the CA host: create the host CA
ssh-keygen -t ed25519 -f host_ca -C "host CA"

# 2. Sign the server's public host key; principals MUST cover every name and
#    address clients use to reach it
ssh-keygen -s host_ca -I server.example.com -h \
  -n server.example.com,10.0.0.10 -V +52w ssh_host_ed25519_key.pub

# 3. Install the certificate beside its private key on the server
install -o root -g root -m 644 ssh_host_ed25519_key-cert.pub /etc/ssh/
```

```bash
# /etc/ssh/sshd_config.d/00-site-hostkeys.conf
HostKey /etc/ssh/ssh_host_ed25519_key
HostCertificate /etc/ssh/ssh_host_ed25519_key-cert.pub
```

```bash
# On every client: trust the host CA for the estate, on one physical line
# ~/.ssh/known_hosts
@cert-authority *.example.com ssh-ed25519 AAAA... host CA
```

Validate before and after reloading:

```bash
# Silent means the certificate pairs with its private key; "No matching private
# key for certificate" means the wrong file is configured
sshd -t

# Confirm both trust anchors are loaded
sshd -T | grep -iE '^(hostkey|hostcertificate|trusteduserca)'

# Confirm the client trusts the host CA for this name
ssh-keygen -F server.example.com -f ~/.ssh/known_hosts

# Connect; -v reports the certificate the client accepted
ssh -v alice@server.example.com true 2>&1 | grep -i 'host certificate'
```

```bash
# Don't: sign keys, configure a path that was never created, and stop there
ssh-keygen -t ed25519 -f ssh-ca -C "SSH CA"
# TrustedUserCAKeys /etc/ssh/ca.pub   # ssh-ca.pub was never installed here,
# so every user certificate is rejected and the host certificate is unused
```

---

## Access Control

### AllowUsers / AllowGroups

Projects **MUST** explicitly allow users or groups. Each policy below is a
complete alternative and **MUST** be deployed on its own; they are not
interchangeable fragments of one block.

```bash
# Do: user allowlist only. Any listed account may log in from anywhere.
AllowUsers alice bob deploy
```

```bash
# Do: group allowlist only (preferred for larger teams). Membership of
# ssh-users or admins is sufficient; no per-user list is consulted.
AllowGroups ssh-users admins
```

```bash
# Do: deliberate intersection. alice and bob MUST also be in ssh-users or
# admins, and deploy MUST additionally connect from 10.0.0.*
AllowUsers alice bob deploy@10.0.0.*
AllowGroups ssh-users admins
```

```bash
# Don't: three policies in one file. Repeated AllowUsers appends patterns, so
# the bare "deploy" entry still permits deploy from any address, and alice is
# locked out unless she is also in ssh-users or admins.
AllowUsers alice bob deploy
AllowGroups ssh-users admins
AllowUsers deploy@10.0.0.*
```

**Why**: default SSH allows all local users, so an explicit allowlist prevents
access when a new account is created. `AllowUsers` and `AllowGroups` are
evaluated as separate gates and a login must pass every gate that is set, but
the patterns *within* one keyword are alternatives, and a repeated keyword
appends to the list rather than narrowing it. `sshd` checks `DenyUsers`, then
`AllowUsers`, then `DenyGroups`, then `AllowGroups`; a user matched by a Deny
list is rejected before any Allow list is consulted.

Prove the policy before closing the session that deployed it:

```bash
# Every pattern sshd holds, expanded one per line
sshd -T | grep -iE '^(allowusers|allowgroups|denyusers|denygroups)'

# One live login per intended account, from a second terminal
ssh -o BatchMode=yes alice@server.example.com true && echo "alice OK"
ssh -o BatchMode=yes deploy@server.example.com true && echo "deploy OK"
```

### DenyUsers / DenyGroups

```bash
# Deny specific users (checked before AllowUsers)
DenyUsers guest test

# Deny groups (checked before AllowGroups)
DenyGroups no-ssh
```

### Match Blocks

Apply settings to specific users/groups/hosts:

```bash
# /etc/ssh/sshd_config.d/00-site-match.conf

# SFTP-only users
Match Group sftp-only
    ForceCommand internal-sftp
    ChrootDirectory /srv/sftp/%u
    DisableForwarding yes
    PermitTTY no
    PermitUserRC no

# Restricted deploy user
Match User deploy
    ForceCommand /usr/local/bin/deploy.sh
    DisableForwarding yes
    PermitTTY no
    PermitUserRC no

# Allow forwarding for specific user
Match User tunnel-user
    AllowTcpForwarding yes
```

**Why**: `ForceCommand` restricts the command, not the channels around it.
Forwarding stays available unless it is disabled explicitly, and
`AllowStreamLocalForwarding` (Unix-domain sockets) and `PermitUserRC` both
default to `yes`. `DisableForwarding yes` closes TCP, Unix-socket, agent, X11
and tunnel forwarding in one directive, and covers any forwarding type added by
a later release.

**Version note**: `DisableForwarding` exists from OpenSSH 7.4, but until
OpenSSH 10.0 it failed to disable X11 and agent forwarding as documented. On
releases before 10.0, set `X11Forwarding no` and `AllowAgentForwarding no`
alongside it — as the baseline in
[Hardened sshd\_config](#hardened-sshd_config) already does.

Restrictions **MUST** be applied per role. Do not add `DisableForwarding yes`
to a bastion account: `ProxyJump` needs TCP forwarding on the jump host.

Verify each role from its own connection profile:

```bash
sshd -T -C user=deploy,addr=10.0.0.5,host=deploy.example.com | \
  grep -iE '^(forcecommand|disableforwarding|permittty|permituserrc)'
```

---

## Cryptographic Settings

### Modern Algorithms Only

Projects **MUST** disable legacy algorithms:

```bash
# /etc/ssh/sshd_config.d/00-site-crypto.conf

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

Configure which keys the daemon offers:

```bash
# /etc/ssh/sshd_config.d/00-site-hostkeys.conf
HostKey /etc/ssh/ssh_host_ed25519_key
HostKey /etc/ssh/ssh_host_rsa_key
```

A host key is a trust anchor that every existing client has already recorded.
Rotation **MUST** be staged: advertise the replacement alongside the current
key, let clients learn it, then retire the old key. Projects **MUST NOT** delete
host keys before replacements are generated, configured and verified.

**Why**: `ssh_config(5)` documents `UpdateHostKeys` — enabled by default for
clients that have not overridden `UserKnownHostsFile` — as the option that
"supports graceful key rotation by allowing a server to send replacement public
keys before old ones are removed". `sshd` advertises every configured `HostKey`
to the client after authentication, so the overlap period is what makes
rotation invisible to clients. Deleting first removes the anchor before any
replacement has been advertised: clients get a host key verification failure
that is indistinguishable from an attack, and a failed regeneration leaves the
daemon with no key to start with.

```bash
# Don't: this destroys every trust anchor before a replacement exists
rm /etc/ssh/ssh_host_*
ssh-keygen -t ed25519 -f /etc/ssh/ssh_host_ed25519_key -N ""
```

Staged rotation:

```bash
# 1. Record the current fingerprints through an out-of-band channel
ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub

# 2. Generate the replacement alongside the existing key, never over it
ssh-keygen -t ed25519 -N "" -C "server.example.com 2026-09" \
  -f /etc/ssh/ssh_host_ed25519_key.new
```

```bash
# 3. Advertise both. The current key stays first, so it remains the key
#    offered during negotiation while clients learn the replacement.
# /etc/ssh/sshd_config.d/00-site-hostkeys.conf
HostKey /etc/ssh/ssh_host_ed25519_key
HostKey /etc/ssh/ssh_host_ed25519_key.new
HostKey /etc/ssh/ssh_host_rsa_key
```

```bash
# 4. Validate, reload and confirm both keys are loaded
sshd -t && systemctl reload sshd
sshd -T | grep -i '^hostkey '

# 5. Publish the replacement fingerprint on the same out-of-band channel
ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.new.pub

# 6. Let every client connect at least once during the overlap window; clients
#    with UpdateHostKeys enabled record the replacement automatically
ssh -o UpdateHostKeys=yes admin@server.example.com true
```

```bash
# 7. Retire only after the window has covered every client: drop the old
#    HostKey line, reload, then archive rather than delete the old files
# /etc/ssh/sshd_config.d/00-site-hostkeys.conf
HostKey /etc/ssh/ssh_host_ed25519_key.new
HostKey /etc/ssh/ssh_host_rsa_key
```

```bash
sshd -t && systemctl reload sshd
install -d -m 700 /root/ssh-hostkey-archive
mv /etc/ssh/ssh_host_ed25519_key /etc/ssh/ssh_host_ed25519_key.pub \
  /root/ssh-hostkey-archive/

# 8. Optional: restore the canonical filename. This renames the same key
#    material, so no client has to learn anything again.
mv /etc/ssh/ssh_host_ed25519_key.new /etc/ssh/ssh_host_ed25519_key
mv /etc/ssh/ssh_host_ed25519_key.new.pub /etc/ssh/ssh_host_ed25519_key.pub
# then point HostKey back at /etc/ssh/ssh_host_ed25519_key, sshd -t, reload
```

**Rollback**: while the archived files exist, restoring the old `HostKey` line
and reloading restores the previous identity. Repeat the procedure for every
host key type in use. Retire unwanted DSA or ECDSA host keys the same way —
remove the `HostKey` line, reload, then archive the files — rather than
deleting them from a running server.

For a client that missed the overlap window, verify the published fingerprint
before trusting the new key:

```bash
ssh-keyscan -t ed25519 server.example.com | ssh-keygen -lf -   # compare by eye
ssh-keygen -R server.example.com                               # drop stale entry
```

**Certificate variant**: where the host is authenticated by a host certificate,
clients trust the CA rather than the key, so sign the replacement host key with
the host CA and install the new certificate (see
[Host Certificates](#host-certificates)). `UpdateHostKeys` is not used for
connections authenticated by a certificate.

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

The jail's `port` **MUST** be the numeric port `sshd` actually listens on.

```bash
# /etc/fail2ban/jail.d/sshd.local
[sshd]
enabled = true
port = 22
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
findtime = 600
bantime = 3600
ignoreip = 127.0.0.1/8 10.0.0.0/8 192.168.0.0/16
```

**Why**: Fail2Ban passes the jail's `port` straight into the banning action, so
the firewall rule it installs blocks that port and no other. The upstream
default `port = ssh` resolves through `/etc/services` to 22; on a host moved to
another port, detection still works while every ban lands on port 22 and the
attacker keeps connecting.

### Aggressive Mode

```bash
# /etc/fail2ban/jail.d/sshd-aggressive.local
[sshd-aggressive]
enabled = true
port = 22
filter = sshd[mode=aggressive]
logpath = /var/log/auth.log
maxretry = 1
findtime = 86400
bantime = 604800
```

### Changing the Listening Port

A non-standard port reduces log noise but does not add security. Projects that
change it **MUST** change every dependent setting in the same maintenance
window, using the rollout procedure in
[Validating and Rolling Out Changes](#validating-and-rolling-out-changes).

```bash
# 1. Server: /etc/ssh/sshd_config.d/00-site-hardening.conf
Port 2222

# 2. Firewall: allow the new port BEFORE reloading sshd; withdraw the old
#    allowance only after step 5 of the rollout procedure has succeeded
ufw allow 2222/tcp

# 3. RHEL/Fedora only: label the port for SELinux
semanage port -a -t ssh_port_t -p tcp 2222

# 4. Every fail2ban jail for this service
sed -i 's/^port = 22$/port = 2222/' /etc/fail2ban/jail.d/sshd*.local

# 5. Clients: ~/.ssh/config
#    Host prod
#        Port 2222
```

Verify every step before closing the session that made the change:

```bash
sshd -T | grep -i '^port'                          # daemon policy
ss -tlnp | grep sshd                               # daemon is listening
fail2ban-client -d | grep -o "\['port', '[^']*'\]" # jail action port
nft list chain inet f2b-table f2b-chain            # rule installed by the action
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
- [ ] `AllowUsers` or `AllowGroups` configured — one policy, not both by accident
- [ ] Site policy in a drop-in that sorts before vendor snippets (`00-*.conf`)
- [ ] Effective values confirmed with `sshd -T` and `sshd -T -C user=...`
- [ ] Modern ciphers/MACs/KEX only
- [ ] `X11Forwarding no`
- [ ] `AllowTcpForwarding no` (unless needed)
- [ ] `AllowStreamLocalForwarding no` and `PermitUserRC no`
- [ ] Every `authorized_keys` record on one physical line, starting from `restrict`
- [ ] `MaxAuthTries 3`
- [ ] `LoginGraceTime 60`
- [ ] fail2ban installed and enabled, with `port` equal to the SSH listener
- [ ] Host keys are Ed25519/RSA only
- [ ] `LogLevel VERBOSE`
- [ ] Second session verified before the deploying session is closed

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
