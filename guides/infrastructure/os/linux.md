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

Projects **SHOULD** apply security hardening to all services.

Projects **MUST NOT** put explanatory comments on the same line as a directive.
systemd reads the whole remainder of the line as the value, so an annotated
assignment fails to parse and the setting is silently discarded. Comments
**MUST** occupy their own line:

```ini
# Don't: the comment becomes part of the value and the directive is ignored
NoNewPrivileges=yes          # Prevent privilege escalation
```

```ini
# Do: comment on its own line
# Prevent privilege escalation
NoNewPrivileges=yes
```

**Why**: `systemd-analyze verify` on the annotated form reports
`Failed to parse NoNewPrivileges=yes # Prevent privilege escalation, ignoring:
Invalid argument`. Because parsing is non-fatal, the unit still starts — with
the protection absent. Measured on Debian 13 (systemd 257) against the hardened
unit built from this guide: annotating its directives inline silently discarded
11 of them and raised the exposure level from 3.3 to 4.5.

```ini
[Service]
# Privilege restrictions
# Prevent privilege escalation
NoNewPrivileges=yes
# User namespace isolation
PrivateUsers=yes

# Filesystem restrictions
# Mount the whole file system hierarchy read-only
ProtectSystem=strict
# Hide /home, /root and /run/user
ProtectHome=yes
# Private /tmp and /var/tmp
PrivateTmp=yes
# Explicit write access
ReadWritePaths=/var/lib/app
# Deny module loading
ProtectKernelModules=yes
# Deny sysctl writes
ProtectKernelTunables=yes
# Deny cgroup modifications
ProtectControlGroups=yes

# Device restrictions
# Deny device access (except pseudo-devices)
PrivateDevices=yes
# Deny access to /dev nodes
DevicePolicy=closed

# Network restrictions (uncomment only if the service needs no network)
# Isolated network namespace
# PrivateNetwork=yes

# Capability restrictions: drop all, then grant only what is needed
CapabilityBoundingSet=
CapabilityBoundingSet=CAP_NET_BIND_SERVICE

# System call filtering
SystemCallFilter=@system-service
SystemCallFilter=~@privileged @resources
SystemCallErrorNumber=EPERM
```

Projects **MUST** run `systemd-analyze verify` on every unit before deploying
it, and **MUST** treat `Failed to parse` output as an error:

```bash
systemd-analyze verify /etc/systemd/system/myapp.service
```

### Analysing Service Security

`systemd-analyze security` reports an **exposure level** between 0.0 and 10.0.
**Lower is better**: 0.0 means the tightest sandboxing, and 10.0 means almost
no sandboxing is applied.

```bash
# Exposure level, 0.0-10.0, lower is better
systemd-analyze security --no-pager myapp.service

# Offline review of a unit file, without querying PID 1
systemd-analyze security --offline=yes --no-pager \
    /etc/systemd/system/myapp.service
```

Projects **MUST NOT** treat a high exposure level as a passing result.
Projects **SHOULD** gate CI on a documented maximum exposure with
`--threshold=`, which exits non-zero when the unit is above the limit:

```bash
# --threshold takes the internal 0-100 scale: 40 == an exposure level of 4.0
systemd-analyze security --offline=yes --threshold=40 \
    /etc/systemd/system/myapp.service
```

**Target**: an exposure level of **4.0 or lower** (`--threshold=40`) for
network-facing production services. A service that must keep broader
privileges **MUST** record the agreed maximum and the justification alongside
the unit.

**Why**: measured on Debian 13 (systemd 257), the directives above move a unit
from the "EXPOSED" band to the "OK" band:

| Unit | Exposure level | Rating |
| ---- | -------------- | ------ |
| The Service Unit Structure example above | 8.3 | EXPOSED |
| The same unit plus the full hardening block | 3.3 | OK |

The exposure level scores only the sandboxing systemd itself applies. It is
not a vulnerability rating: it says nothing about the application's own code,
its dependencies, or the operations it can request over D-Bus and other IPC.

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

Reverse-path filtering is deliberately absent from this baseline; it is
topology-dependent and is covered next.

### Reverse-Path Filtering

`rp_filter` discards packets whose source address does not pass a reverse
routing check. The kernel takes the **maximum** of
`conf/all/rp_filter` and `conf/<interface>/rp_filter`, so setting
`net.ipv4.conf.all.rp_filter = 1` forces strict mode on every interface and
**cannot** be relaxed per interface afterwards.

Projects **MUST** choose the mode from the host's routing topology rather than
applying a blanket value:

| Topology | Mode | Setting |
| -------- | ---- | ------- |
| Single uplink, symmetric routing | Strict | `rp_filter = 1` |
| Multihomed or multiple default routes | Loose | `rp_filter = 2` |
| Policy routing, VRF, `ip rule` marks | Loose | `rp_filter = 2` |
| VPN or tunnel with asymmetric return path | Loose | `rp_filter = 2` |
| Container or Kubernetes node with overlay networking | Loose | `rp_filter = 2` |

```bash
# Do: leave `all` permissive and set the mode per interface
# /etc/sysctl.d/99-rp-filter.conf
net.ipv4.conf.all.rp_filter = 0
net.ipv4.conf.default.rp_filter = 0
net.ipv4.conf.eth0.rp_filter = 1
net.ipv4.conf.wg0.rp_filter = 2
```

```bash
# Don't: this pins every present and future interface to strict mode
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
```

Where policy routing selects the return path by firewall mark, strict mode
**MUST** be paired with `src_valid_mark` so the mark is included in the reverse
lookup:

```bash
net.ipv4.conf.all.src_valid_mark = 1
```

Projects **MUST** verify routing after any `rp_filter` change, before the host
carries traffic:

```bash
# Confirm the effective value per interface
sysctl net.ipv4.conf.eth0.rp_filter net.ipv4.conf.all.rp_filter

# Which interface would the kernel use to reach a given source address?
# If it is not the interface the packet arrives on, strict mode drops it.
ip route get 203.0.113.10

# Input-path lookup for a packet arriving on a named interface
ip route get 198.51.100.10 from 203.0.113.10 iif eth0

# Count silently discarded martian and unroutable packets
nstat -az | grep -E 'IpInAddrErrors|IpExtInNoRoutes'
```

**Why**: strict mode drops a packet that arrives on a legitimate interface
which is not the best return path. The kernel documentation recommends strict
mode under RFC 3704 for symmetric networks but recommends loose mode "if using
asymmetric routing or other complicated routing". The kernel default is 0, so a
blanket `1` is a behaviour change, not a hardening of an existing default.

Measured on Linux 6.12 with a veth pair, sending packets whose source address
was routable only via a different interface:

| `conf.all` | `conf.veth0` | Packets reaching the input hook |
| ---------- | ------------ | ------------------------------- |
| 0 | 0 | 2 of 2 |
| 0 | 1 | 0 of 2 |
| 1 | 0 | 0 of 2 |
| 2 | 0 | 2 of 2 |

Row three is the trap: `all = 1` discarded the packets even though the arrival
interface was explicitly set to 0.

### Network Performance Tuning

Projects **MUST NOT** change kernel networking defaults without measurement.
The Linux defaults are auto-tuned and scale with available memory; a static
"performance" block frequently makes throughput worse. Three examples from the
values commonly copied between runbooks:

- `net.ipv4.tcp_rmem = 4096 87380 16777216` **lowers** the initial receive
  buffer from the kernel default of 131072 bytes and caps auto-tuning at 16 MiB,
  where the default maximum is between 131072 bytes and 32 MiB depending on RAM.
- `net.ipv4.tcp_tw_reuse = 1` widens the kernel default of 2 (loopback only) to
  all traffic. The kernel documentation states plainly: "It should not be
  changed without advice/request of technical experts."
- `net.ipv4.tcp_fin_timeout` governs orphaned `FIN_WAIT_2` connections, not
  `TIME_WAIT`. Lowering it does not shorten `TIME_WAIT`, which Linux fixes at
  the compile-time constant `TCP_TIMEWAIT_LEN` (60 seconds) and exposes no
  sysctl for.

Projects **MUST** follow this sequence before deploying any networking profile:

1. Record the keys the profile will change, so the change can be reverted
   exactly: `sysctl -a --pattern '^net\.(core|ipv4)\.' > baseline-sysctl.txt`
2. Record the symptom with counters, not intuition: `ss -tin`,
   `nstat -az TcpExtListenOverflows TcpExtListenDrops TcpExtTCPBacklogDrop`,
   `nstat -az TcpRetransSegs`, and `ip -s link` for driver-level drops.
3. Change one profile at a time, in staging, under representative load.
4. Compare the same counters and the service's own latency percentiles.
5. Keep the change only if the metrics moved; otherwise revert to the baseline.

#### Profile: High Bandwidth-Delay Product Ingress

Applies **only** to a host that terminates many long-distance TCP connections
(for example a CDN origin or a cross-region reverse proxy) where step 2 showed
receive windows limited by buffer size rather than by congestion.

```bash
# /etc/sysctl.d/98-network-bdp-ingress.conf
# Prerequisite: measured window-limited transfers; >= 8 GiB RAM.
# Rollback: see below.

# Raise only the auto-tuning ceiling; leave min and default alone so that
# idle sockets keep the kernel's own footprint.
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 131072 16777216
net.ipv4.tcp_wmem = 4096 16384 16777216
```

#### Profile: High Connection Arrival Rate

Applies **only** where step 2 recorded a non-zero and growing
`TcpExtListenOverflows` or `TcpExtListenDrops`.

```bash
# /etc/sysctl.d/98-network-accept-queue.conf
# Prerequisite: measured listen-queue overflows.
# The application must also raise its own listen() backlog; this sysctl
# only raises the ceiling.
net.core.somaxconn = 16384
net.ipv4.tcp_max_syn_backlog = 16384
```

**Memory cost**: the middle value of `tcp_rmem`/`tcp_wmem` is committed per
socket. Raising `tcp_wmem`'s default from 16 KiB to 64 KiB costs an extra
48 KiB per connection — about 2.3 GiB at 50,000 concurrent connections. Neither
profile above raises those middle values for that reason.

**Rollback**: deleting a drop-in file does not restore the running kernel.
`sysctl --system` only re-applies the files that remain, so the keys the
profile set keep their value until they are reset explicitly or the host
reboots. Every profile **MUST** therefore ship the reset alongside it:

```bash
rm /etc/sysctl.d/98-network-bdp-ingress.conf

# Restore the recorded values for exactly the keys this profile changed
grep -E '^net\.(core\.[rw]mem_max|ipv4\.tcp_[rw]mem) ' baseline-sysctl.txt \
    | sysctl -p -

sysctl --system
```

**Why**: `tcp_tw_reuse`, `tcp_fin_timeout`, `tcp_slow_start_after_idle` and the
keepalive timers change TCP's correctness-relevant behaviour, not just its
buffer sizes, and the kernel documentation asks for expert justification before
they are touched. Publishing them as a default profile turns a workload-specific
experiment into an unreviewed change on every host.

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

Debian 13+ uses nftables (Debian 13 ships nftables 1.1.3). Projects **MUST**
configure a default-deny input policy.

Projects **MUST NOT** use `flush ruleset` in a host firewall file. Docker,
firewalld, libvirt and Kubernetes CNI plugins install and own their own
nftables tables; flushing destroys them, taking published container ports and
NAT rules with them. The host **MUST** own exactly one named table and
**MUST** leave every other table alone.

```bash
# /etc/nftables.conf
#!/usr/sbin/nft -f

# Replace only this file's own table. Never `flush ruleset`.
destroy table inet doctrine

table inet doctrine {
    chain input {
        type filter hook input priority filter; policy drop;

        # Allow established/related, drop invalid
        ct state established,related accept
        ct state invalid drop

        # Allow loopback
        iif lo accept

        # IPv4 ICMP
        meta l4proto icmp icmp type {
            echo-request, destination-unreachable,
            time-exceeded, parameter-problem
        } accept

        # IPv6 ICMP: `meta l4proto` matches through extension headers
        meta l4proto ipv6-icmp icmpv6 type {
            destination-unreachable, packet-too-big,
            time-exceeded, parameter-problem,
            echo-request, echo-reply,
            mld-listener-query, mld-listener-report,
            mld-listener-done, mld2-listener-report
        } accept

        # Neighbour and router discovery: link-local only
        meta l4proto ipv6-icmp icmpv6 type {
            nd-router-solicit, nd-router-advert,
            nd-neighbor-solicit, nd-neighbor-advert
        } ip6 hoplimit 255 accept

        # Allow SSH (adjust port as needed)
        tcp dport 22 accept

        # Allow HTTP/HTTPS
        tcp dport { 80, 443 } accept

        # Log dropped packets (optional, can be noisy)
        # log prefix "nftables dropped: " counter drop
    }

    chain output {
        type filter hook output priority filter; policy accept;
    }
}
```

#### Matching ICMPv6

Projects **MUST NOT** match ICMPv6 with `ip6 nexthdr icmpv6`. `nexthdr` reads
only the first Next Header field, so any ICMPv6 message carrying an extension
header — including the hop-by-hop header that MLD queries and reports use —
misses the rule and reaches the drop policy.

```text
# Don't
ip6 nexthdr icmpv6 accept

# Do
meta l4proto ipv6-icmp accept
```

**Why**: measured on Linux 6.12 with nftables 1.1.3, two counters in the same
input chain saw different traffic. Three plain ICMPv6 echo requests plus their
replies matched both rules (6 packets each). Three echo requests carrying a
hop-by-hop header matched `meta l4proto ipv6-icmp` 6 times but
`ip6 nexthdr icmpv6` only 3 — the requests were missed. Under the default-deny
policy above, sending the hop-by-hop request across a veth pair produced no
reply with `nexthdr`, and a normal reply with `meta l4proto`.

#### No Blanket Forward Chain

The example above has no `forward` base chain. Projects **MUST NOT** add a
forwarding drop policy to a host that runs a container engine.

**Why**: nftables runs *every* base chain registered at a hook. An accept in
one table does not stop another table's chain from dropping the packet, and
Docker's own documentation states that "an 'accept' rule is not final. It
terminates processing for its base chain, but the accepted packet will still be
processed by other base chains, which may drop it." Measured on Linux 6.12: with
a single accept-policy input chain, `ping 127.0.0.1` succeeded; after adding an
empty second table whose input chain had `policy drop` at the same hook, the
same ping was blocked.

A host that genuinely routes between interfaces and runs no container engine
**MAY** add a forward chain to its own table:

```bash
    chain forward {
        type filter hook forward priority filter; policy drop;
        ct state established,related accept
        iifname "eth0" oifname "eth1" accept
    }
```

#### Container and Firewall Manager Variants

| Host | Doctrine table | Forwarding rules |
| ---- | -------------- | ---------------- |
| Native nftables, no containers | `inet doctrine` as above | Optional forward chain |
| Docker, iptables backend (default) | `inet doctrine`, input chain only | Use the `DOCKER-USER` iptables chain |
| Docker 29+, nftables backend | `inet doctrine`, input chain only | Own table at the forward hook, plus `--bridge-accept-fwmark` |
| Docker Swarm | `inet doctrine`, input chain only | iptables backend only; Swarm cannot use nftables |
| firewalld | Manage zones with `firewall-cmd` | Do not hand-write `/etc/nftables.conf` |

Docker's nftables backend, introduced in Docker 29.0.0, is **experimental** and
**cannot** be enabled while the daemon runs in Swarm mode. It owns the
`ip docker-bridges` and `ip6 docker-bridges` tables, which **MUST NOT** be
edited directly. There is no `DOCKER-USER` chain in that mode; host rules go in
a separate table with base chains at the same hooks, ordered by base chain
priority. Because Docker's drop rules are final, overriding them requires a
firewall mark and the daemon option `--bridge-accept-fwmark`.

With the iptables backend, Docker sets the iptables `FORWARD` policy to `DROP`
and provides the `DOCKER-USER` chain, which is processed before Docker's own
rules:

```bash
# Restrict which sources may reach published container ports
iptables -I DOCKER-USER -i eth0 ! -s 192.0.2.0/24 -j DROP
```

#### Applying Rules Safely

Projects **MUST** validate before applying, and **MUST** keep a way back in.

```bash
# 1. Syntax and semantic check; makes no change to the running ruleset
nft --check -f /etc/nftables.conf

# 2. Snapshot the current state of the Doctrine table as a replayable file
{ echo 'destroy table inet doctrine'
  nft list table inet doctrine 2>/dev/null || true
} > /root/nftables-rollback.conf

# 3. Schedule an automatic rollback before applying, in case SSH is cut off
systemd-run --on-active=120 --unit=nft-rollback \
    /usr/sbin/nft -f /root/nftables-rollback.conf

# 4. Apply
nft -f /etc/nftables.conf

# 5. Confirm the session still works, then cancel the rollback
systemctl stop nft-rollback.timer

# Enable on boot
systemctl enable nftables

# List current rules
nft list ruleset
```

**Why**: `destroy table` is idempotent, so re-running the file replaces only
the Doctrine table. Verified on Debian 13: with simulated `ip docker` and
`ip firewalld_sim` tables present, applying a file that begins with
`flush ruleset` left only `inet filter`, whereas the file above left both
application tables intact and could be re-applied without error.

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

Projects **MUST** select repositories with `Origins-Pattern` and match on
`codename`, not on `archive`. The legacy `Allowed-Origins` shorthand
`"${distro_id}:${distro_codename}"` expands to `o=Debian,a=trixie`, but
Debian's archive field carries the suite name (`stable`, `stable-security`,
`stable-updates`) and the codename lives in a separate field. The shorthand
therefore matches nothing.

```bash
# Don't: matches no Debian repository, including security
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}";
    "${distro_id}:${distro_codename}-security";
    "${distro_id}:${distro_codename}-updates";
};
```

```bash
# /etc/apt/apt.conf.d/50unattended-upgrades
# Do: codename-based selectors, tested against the live archive.
Unattended-Upgrade::Origins-Pattern {
    // Security updates. Both entries are required: the security archive
    // has used both the base codename and the -security codename.
    "origin=Debian,codename=${distro_codename},label=Debian-Security";
    "origin=Debian,codename=${distro_codename}-security,label=Debian-Security";

    // Point releases and stable-updates. Remove these two lines to apply
    // security fixes only; that choice MUST be deliberate and recorded.
    "origin=Debian,codename=${distro_codename},label=Debian";
    "origin=Debian,codename=${distro_codename}-updates,label=Debian";
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

This file replaces the one Debian ships, which contains the only
`Origins-Pattern` entries on a default install. Any pattern removed here is
removed from the system; nothing else re-adds it.

**Why**: the archive metadata and the codename metadata are different fields.
On Debian 13 the three repositories publish
`a=stable,n=trixie,l=Debian`, `a=stable-updates,n=trixie-updates,l=Debian` and
`a=stable-security,n=trixie-security,l=Debian-Security`. Archive-based
selectors also follow the suite rather than the release, so `a=stable` silently
starts upgrading to Debian 14 when trixie stops being stable.

```bash
# Read the metadata this host actually publishes
apt-cache policy
```

```text
 500 http://deb.debian.org/debian-security trixie-security/main arm64 Packages
     release v=13,o=Debian,a=stable-security,n=trixie-security,l=Debian-Security
 500 http://deb.debian.org/debian trixie/main arm64 Packages
     release v=13.6,o=Debian,a=stable,n=trixie,l=Debian
```

```bash
# /etc/apt/apt.conf.d/20auto-upgrades
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::Download-Upgradeable-Packages "1";
APT::Periodic::AutocleanInterval "7";
```

### Testing

Projects **MUST** confirm the configured origins actually match a repository
before relying on unattended upgrades:

```bash
# Dry run
unattended-upgrades --dry-run --debug

# Check logs
cat /var/log/unattended-upgrades/unattended-upgrades.log
```

Read two things in that output. `Allowed origins are:` echoes the expanded
patterns, and any repository that failed to match is reported as
`Marking not allowed <...> with -32768 pin`. A correct configuration produces
no `Marking not allowed` line for a repository that should be upgraded:

```text
Allowed origins are: origin=Debian,codename=trixie,label=Debian-Security,
  origin=Debian,codename=trixie-security,label=Debian-Security,
  origin=Debian,codename=trixie,label=Debian,
  origin=Debian,codename=trixie-updates,label=Debian
```

With the legacy shorthand, the same host instead reports every repository as
excluded:

```text
Allowed origins are: o=Debian,a=trixie, o=Debian,a=trixie-security,
  o=Debian,a=trixie-updates
Marking not allowed <... a=stable-security,l=Debian-Security ...> with -32768 pin
Marking not allowed <... a=stable-updates,l=Debian ...> with -32768 pin
Marking not allowed <... a=stable,l=Debian ...> with -32768 pin
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

Projects **MUST NOT** impose composition rules or scheduled password expiry.
Both were removed from NIST SP 800-63B, which now requires a 15-character
minimum for single-factor passwords, forbids other composition rules, forbids
periodic rotation, and requires a compromised-password blocklist plus
rate limiting.

Enable the PAM module first. Editing `pwquality.conf` alone changes nothing:
the settings are only read when `pam_pwquality.so` is in the password stack.

```bash
apt install libpam-pwquality libpwquality-tools cracklib-runtime

# Debian's pam-auth-update adds pam_pwquality to the password stack
pam-auth-update

# Verify the module is actually active
grep pam_pwquality /etc/pam.d/common-password
```

```bash
# /etc/security/pwquality.conf
minlen = 15         # single-factor minimum; 8 is permitted only with MFA
maxrepeat = 0       # disabled: repeat limits are a composition rule
minclass = 0        # disabled: character-class rules are forbidden
dcredit = 0
ucredit = 0
lcredit = 0
ocredit = 0
dictcheck = 1       # reject blocklisted and dictionary passwords
usercheck = 1       # reject passwords derived from the username
enforcing = 1
retry = 3
```

Maintain the blocklist as a cracklib dictionary. On Debian, `update-cracklib`
rebuilds the dictionary from every text file under `/usr/share/dict`, so the
breach corpus is merged with the standard word lists rather than replacing
them:

```bash
# One password per line, from a maintained compromised-password corpus
install -m 0644 compromised-passwords /usr/share/dict/compromised-passwords
update-cracklib

# Confirm the policy rejects a blocklisted value and accepts a passphrase
echo 'correcthorsebatterystaple' | pwscore
echo 'gorse-lintel-quarry-pelican' | pwscore
```

Rate-limit authentication failures with `pam_faillock`. Debian ships the module
but does not enable it, so `/etc/pam.d/common-auth` **MUST** be edited to
bracket the authentication modules:

```text
# /etc/pam.d/common-auth
auth    required                        pam_faillock.so preauth
auth    [success=1 default=ignore]      pam_unix.so nullok
auth    [default=die]                   pam_faillock.so authfail
auth    sufficient                      pam_faillock.so authsucc
auth    requisite                       pam_deny.so
auth    required                        pam_permit.so
```

```bash
# /etc/security/faillock.conf
deny = 5
fail_interval = 900
unlock_time = 900
even_deny_root
root_unlock_time = 60
```

```bash
# Inspect and clear lockouts
faillock --user alice
faillock --user alice --reset
```

Disable scheduled expiry, and force a change only on evidence of compromise:

```bash
# /etc/login.defs — applies to accounts created after this change
PASS_MAX_DAYS   99999
PASS_MIN_DAYS   0
PASS_WARN_AGE   7
```

```bash
# login.defs is NOT retroactive; existing accounts keep their own aging
chage --maxdays 99999 --mindays 0 alice

# Force a change after evidence of compromise
chage -d 0 alice
```

**Why**: verified on Debian 13 with libpwquality 1.4.5. Under the previous
`minlen = 14, minclass = 3` policy, `pwscore` rejected both
`correcthorsebatterystaple` and `gorse-lintel-quarry-pelican` for containing
"less than 3 character classes" while accepting `Summer2026!London` — the
policy rejected strong passphrases and admitted a guessable pattern. Under the
policy above, the two passphrases score 100 unless they appear in the
blocklist, and blocklisted values are rejected with "the password fails the
dictionary check". `pam_faillock` was confirmed to reject the correct password
after five failures with "15 minutes left to unlock", and `chage -l` confirmed
that changing `login.defs` left an existing account's 90-day maximum untouched
until `chage` was run explicitly.

`PASS_MIN_DAYS 1` is deliberately dropped: a minimum age prevents a user from
changing a password twice in one day, which blocks remediation immediately
after a forced reset.

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
