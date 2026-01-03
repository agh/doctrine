# Linux (Debian) Style Guide

> [Doctrine](../../../README.md) > [Infrastructure](../README.md) > [OS](README.md) > Linux

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

Targets Debian 13 (Trixie) and Debian 14, with notes for Ubuntu 24.04 LTS.

## Quick Reference

| Task | Command |
| ---- | ------- |
| Update packages | `apt update && apt upgrade` |
| Install package | `apt install nginx` |
| Check service | `systemctl status nginx` |
| View logs | `journalctl -u nginx -f` |
| Reload sysctl | `sysctl --system` |
| Check listening ports | `ss -tlnp` |
| Check AppArmor | `aa-status` |

---

## Table of Contents

1. [Package Management](#package-management)
2. [systemd Services](#systemd-services)
3. [systemd Timers](#systemd-timers)
4. [Kernel Tuning](#kernel-tuning)
5. [Security Hardening](#security-hardening)
6. [Automatic Updates](#automatic-updates)
7. [User Management](#user-management)
8. [Logging](#logging)

---

## Package Management

### APT Best Practices

Projects **MUST** update the package index before installing packages:

```bash
# Always update before install
apt update && apt install nginx

# Never just: apt install nginx (may use stale index)
```

### Sources Configuration

Debian 13+ uses DEB822 format in `/etc/apt/sources.list.d/`:

```bash
# /etc/apt/sources.list.d/debian.sources
Types: deb
URIs: https://deb.debian.org/debian
Suites: trixie trixie-updates
Components: main contrib non-free non-free-firmware
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg

Types: deb
URIs: https://security.debian.org/debian-security
Suites: trixie-security
Components: main contrib non-free non-free-firmware
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg
```

### Third-Party Repositories

Projects **MUST** use signed repositories with keys in `/usr/share/keyrings/`:

```bash
# Download GPG key
curl -fsSL https://example.com/gpg.key | \
    gpg --dearmor -o /usr/share/keyrings/example-archive-keyring.gpg

# Add repository (DEB822 format)
cat > /etc/apt/sources.list.d/example.sources << 'EOF'
Types: deb
URIs: https://packages.example.com/debian
Suites: stable
Components: main
Signed-By: /usr/share/keyrings/example-archive-keyring.gpg
EOF

apt update
```

**Why**: DEB822 format is clearer, supports per-repo signing keys, and is the
modern standard replacing one-line sources.list entries.

### Package Pinning

Projects **MAY** pin package versions to prevent unwanted upgrades:

```bash
# /etc/apt/preferences.d/nginx
Package: nginx
Pin: version 1.24.*
Pin-Priority: 1000
```

### Useful Commands

```bash
# Search packages
apt search nginx

# Show package info
apt show nginx

# List installed packages
apt list --installed

# Show package files
dpkg -L nginx

# Find which package owns a file
dpkg -S /usr/bin/nginx

# Clean package cache
apt clean

# Remove unused dependencies
apt autoremove
```

---

## systemd Services

### Service Unit Structure

Projects **MUST** follow this structure for service units:

```ini
# /etc/systemd/system/myapp.service
[Unit]
Description=My Application
Documentation=https://docs.example.com/myapp
After=network-online.target
Wants=network-online.target

[Service]
Type=exec
User=myapp
Group=myapp
WorkingDirectory=/opt/myapp
ExecStart=/opt/myapp/bin/myapp
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=5s

# Security hardening
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
ReadWritePaths=/var/lib/myapp

[Install]
WantedBy=multi-user.target
```

### Service Types

| Type | Description | Use When |
| ---- | ----------- | -------- |
| `simple` | Default, assumes process stays in foreground | Most services |
| `exec` | Like simple, but waits for exec() | Preferred over simple |
| `forking` | Process forks and parent exits | Legacy daemons |
| `oneshot` | Short-lived tasks | Scripts, setup tasks |
| `notify` | Service signals readiness via sd_notify | Systemd-aware services |

### Security Hardening Directives

Projects **SHOULD** apply security hardening to all services:

```ini
[Service]
# Privilege restrictions
NoNewPrivileges=yes          # Prevent privilege escalation
PrivateUsers=yes             # User namespace isolation

# Filesystem restrictions
ProtectSystem=strict         # Mount / as read-only
ProtectHome=yes              # Hide /home, /root, /run/user
PrivateTmp=yes               # Isolated /tmp
ReadWritePaths=/var/lib/app  # Explicit write access
ProtectKernelModules=yes     # Deny module loading
ProtectKernelTunables=yes    # Deny sysctl writes
ProtectControlGroups=yes     # Deny cgroup modifications

# Device restrictions
PrivateDevices=yes           # Deny device access (except pseudo-devices)
DevicePolicy=closed          # Deny access to /dev nodes

# Network restrictions (if no network needed)
PrivateNetwork=yes           # Isolated network namespace

# Capability restrictions
CapabilityBoundingSet=       # Drop all capabilities
# Or allow specific:
CapabilityBoundingSet=CAP_NET_BIND_SERVICE

# System call filtering
SystemCallFilter=@system-service
SystemCallFilter=~@privileged @resources
SystemCallErrorNumber=EPERM
```

### Analyzing Service Security

```bash
# Score service security (0-10, higher is better)
systemd-analyze security myapp.service

# Detailed breakdown
systemd-analyze security myapp.service --no-pager
```

**Target score**: 7.0+ for production services.

### Socket Activation

Projects **SHOULD** use socket activation for on-demand services:

```ini
# /etc/systemd/system/myapp.socket
[Unit]
Description=My Application Socket

[Socket]
ListenStream=8080
Accept=no

[Install]
WantedBy=sockets.target
```

```ini
# /etc/systemd/system/myapp.service
[Unit]
Description=My Application
Requires=myapp.socket

[Service]
Type=exec
ExecStart=/opt/myapp/bin/myapp
# Inherit socket from systemd
StandardInput=socket
```

**Why**: Socket activation allows zero-downtime restarts and reduces resource
usage for rarely-accessed services.

---

## systemd Timers

Projects **SHOULD** use systemd timers instead of cron:

### Timer Unit

```ini
# /etc/systemd/system/backup.timer
[Unit]
Description=Daily backup timer

[Timer]
OnCalendar=*-*-* 02:00:00
RandomizedDelaySec=1h
Persistent=yes

[Install]
WantedBy=timers.target
```

### Service Unit

```ini
# /etc/systemd/system/backup.service
[Unit]
Description=Daily backup

[Service]
Type=oneshot
ExecStart=/usr/local/bin/backup.sh
User=backup
```

### Timer Patterns

| Pattern | Meaning |
| ------- | ------- |
| `OnCalendar=hourly` | Every hour |
| `OnCalendar=daily` | Every day at midnight |
| `OnCalendar=weekly` | Every Monday at midnight |
| `OnCalendar=*-*-* 02:00:00` | Every day at 2 AM |
| `OnCalendar=Mon *-*-* 09:00:00` | Every Monday at 9 AM |
| `OnBootSec=5min` | 5 minutes after boot |
| `OnUnitActiveSec=1h` | 1 hour after last run |

### Timer Commands

```bash
# List active timers
systemctl list-timers

# Enable and start timer
systemctl enable --now backup.timer

# Run service immediately (test)
systemctl start backup.service

# Check timer status
systemctl status backup.timer
```

**Why**: Timers have better logging (journalctl), dependency management, resource
controls, and randomized delays to prevent thundering herd.

---

## Kernel Tuning

### sysctl Configuration

Projects **MUST** place sysctl settings in `/etc/sysctl.d/`:

```bash
# /etc/sysctl.d/99-custom.conf

# Network security
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.icmp_ignore_bogus_error_responses = 1
net.ipv4.tcp_syncookies = 1

# IPv6 (if not needed, disable)
# net.ipv6.conf.all.disable_ipv6 = 1

# Memory
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5

# File handles
fs.file-max = 2097152
fs.inotify.max_user_watches = 524288
```

### Network Performance Tuning

```bash
# /etc/sysctl.d/98-network-performance.conf

# TCP buffer sizes
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216

# Connection handling
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 65535
net.ipv4.tcp_max_syn_backlog = 65535

# TCP optimizations
net.ipv4.tcp_slow_start_after_idle = 0
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 15

# Keepalive
net.ipv4.tcp_keepalive_time = 600
net.ipv4.tcp_keepalive_intvl = 60
net.ipv4.tcp_keepalive_probes = 5
```

### Applying Changes

```bash
# Apply all sysctl.d settings
sysctl --system

# Apply specific file
sysctl -p /etc/sysctl.d/99-custom.conf

# Verify setting
sysctl net.ipv4.tcp_syncookies
```

---

## Security Hardening

### AppArmor

Debian uses AppArmor by default. Projects **SHOULD** create profiles for custom applications:

```bash
# Check AppArmor status
aa-status

# Generate profile skeleton
aa-genprof /usr/bin/myapp

# Set profile to complain mode (log but don't block)
aa-complain /etc/apparmor.d/usr.bin.myapp

# Set profile to enforce mode
aa-enforce /etc/apparmor.d/usr.bin.myapp

# Reload profiles
apparmor_parser -r /etc/apparmor.d/
```

### Example AppArmor Profile

```text
# /etc/apparmor.d/opt.myapp.bin.myapp
#include <tunables/global>

/opt/myapp/bin/myapp {
  #include <abstractions/base>
  #include <abstractions/nameservice>

  # Binary
  /opt/myapp/bin/myapp mr,

  # Libraries
  /opt/myapp/lib/** mr,

  # Configuration (read-only)
  /etc/myapp/** r,

  # Data directory (read-write)
  /var/lib/myapp/** rw,

  # Logs
  /var/log/myapp/** w,

  # Network
  network inet stream,
  network inet dgram,

  # Deny everything else implicitly
}
```

### SSH Hardening

See [SSH Service Guide](../services/ssh.md) for comprehensive SSH hardening.

Quick checklist:

- [ ] Disable root login
- [ ] Key-based authentication only
- [ ] Non-standard port (optional)
- [ ] AllowUsers/AllowGroups configured
- [ ] fail2ban installed

### Firewall (nftables)

Debian 13+ uses nftables. Projects **MUST** configure a default-deny firewall:

```bash
# /etc/nftables.conf
#!/usr/sbin/nft -f

flush ruleset

table inet filter {
    chain input {
        type filter hook input priority 0; policy drop;

        # Allow established/related
        ct state established,related accept

        # Allow loopback
        iif lo accept

        # Allow ICMP
        ip protocol icmp accept
        ip6 nexthdr icmpv6 accept

        # Allow SSH (adjust port as needed)
        tcp dport 22 accept

        # Allow HTTP/HTTPS
        tcp dport { 80, 443 } accept

        # Log dropped packets (optional, can be noisy)
        # log prefix "nftables dropped: " counter drop
    }

    chain forward {
        type filter hook forward priority 0; policy drop;
    }

    chain output {
        type filter hook output priority 0; policy accept;
    }
}
```

```bash
# Apply rules
nft -f /etc/nftables.conf

# Enable on boot
systemctl enable nftables

# List current rules
nft list ruleset
```

### File Integrity

Projects **SHOULD** use AIDE or similar for file integrity monitoring:

```bash
# Install AIDE
apt install aide

# Initialize database
aideinit

# Check for changes
aide --check
```

---

## Automatic Updates

### unattended-upgrades

Projects **MUST** enable automatic security updates:

```bash
apt install unattended-upgrades apt-listchanges

# Enable
dpkg-reconfigure -plow unattended-upgrades
```

### Configuration

```bash
# /etc/apt/apt.conf.d/50unattended-upgrades
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}";
    "${distro_id}:${distro_codename}-security";
    "${distro_id}:${distro_codename}-updates";
};

Unattended-Upgrade::Package-Blacklist {
    // "linux-";
    // "postgresql-";
};

Unattended-Upgrade::AutoFixInterruptedDpkg "true";
Unattended-Upgrade::MinimalSteps "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
Unattended-Upgrade::Automatic-Reboot-Time "02:00";

// Email notifications
Unattended-Upgrade::Mail "admin@example.com";
Unattended-Upgrade::MailReport "only-on-error";
```

```bash
# /etc/apt/apt.conf.d/20auto-upgrades
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::Download-Upgradeable-Packages "1";
APT::Periodic::AutocleanInterval "7";
```

### Testing

```bash
# Dry run
unattended-upgrades --dry-run --debug

# Check logs
cat /var/log/unattended-upgrades/unattended-upgrades.log
```

---

## User Management

### Creating Users

```bash
# Interactive user
useradd -m -s /bin/bash -G sudo username

# Service account (no shell, no home)
useradd --system --shell /usr/sbin/nologin --home-dir /nonexistent servicename
```

### sudo Configuration

Projects **MUST** use `/etc/sudoers.d/` for custom sudo rules:

```bash
# /etc/sudoers.d/admins
# Group-based sudo access
%admins ALL=(ALL:ALL) ALL

# Specific user, no password for specific commands
deploy ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart myapp
```

```bash
# Validate syntax before saving
visudo -c -f /etc/sudoers.d/admins
```

### Password Policy

Configure in `/etc/login.defs` and `/etc/security/pwquality.conf`:

```bash
# /etc/login.defs
PASS_MAX_DAYS   90
PASS_MIN_DAYS   1
PASS_WARN_AGE   14

# /etc/security/pwquality.conf
minlen = 14
minclass = 3
maxrepeat = 3
```

---

## Logging

### journald Configuration

```bash
# /etc/systemd/journald.conf
[Journal]
Storage=persistent
Compress=yes
SystemMaxUse=2G
SystemMaxFileSize=100M
MaxRetentionSec=90day
ForwardToSyslog=no
```

```bash
# Apply changes
systemctl restart systemd-journald
```

### Useful Journal Commands

```bash
# Follow all logs
journalctl -f

# Specific unit
journalctl -u nginx

# Since boot
journalctl -b

# Specific time range
journalctl --since "2024-01-01" --until "2024-01-02"

# Kernel messages
journalctl -k

# Priority filtering
journalctl -p err    # Errors and above

# JSON output
journalctl -o json-pretty

# Disk usage
journalctl --disk-usage

# Cleanup
journalctl --vacuum-time=30d
journalctl --vacuum-size=1G
```

### Remote Logging

For centralized logging, configure rsyslog or use systemd-journal-remote:

```bash
# /etc/systemd/journal-upload.conf
[Upload]
URL=https://logs.example.com:19532
```

---

## See Also

- [OS Fundamentals](README.md) — Cross-platform concepts
- [SSH](../services/ssh.md) — SSH server hardening
- [Ansible](../ansible.md) — Automated Linux configuration
- [Docker](../docker.md) — Container deployment
- [Shell Style Guide](../../languages/shell.md) — Shell scripting

---

## References

- [Debian Administrator's Handbook](https://debian-handbook.info/)
- [systemd Documentation](https://systemd.io/)
- [ArchWiki - Security](https://wiki.archlinux.org/title/Security) — Applicable to Debian
- [CIS Debian Benchmark](https://www.cisecurity.org/benchmark/debian_linux)
