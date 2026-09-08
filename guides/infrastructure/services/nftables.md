# nftables Style Guide

> [Doctrine](../../../README.md) > [Infrastructure](../README.md) > nftables

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

## Quick Reference

| Task | Tool | Command |
| ---- | ---- | ------- |
| List the active ruleset | nft | `nft list ruleset` |
| List table names only | nft | `nft list tables` |
| Snapshot the owned table | nft | `nft list table inet filter > rollback.nft` |
| Validate a file, change nothing | nft | `nft --check --file /etc/nftables.conf` |
| Load a file atomically | nft | `nft --file /etc/nftables.conf` |
| Arm a timed rollback | systemd-run | `systemd-run --unit=nft-rollback --collect --on-active=5min --timer-property=AccuracySec=1s /usr/sbin/nft --file rollback.nft` |
| Cancel the rollback | systemctl | `systemctl stop nft-rollback.timer` |
| Deploy a change end to end | nft-deploy | `nft-deploy /etc/nftables.conf` (see [Safe Rule Deployment](#safe-rule-deployment)) |

This table has no "flush rules" entry. `nft flush ruleset` deletes every table
on the host and leaves an empty ruleset in which no packet filtering happens at
all, so it **MUST NOT** be run as a standalone command. Clear a ruleset only
inside a complete replacement file (see
[Own One Table, Not the Whole Ruleset](#own-one-table-not-the-whole-ruleset))
or through [Break-Glass Recovery](#break-glass-recovery).

## Overview

TODO: Linux firewall configuration with nftables (replacement for iptables).

## Safe Rule Deployment

### Why

`nft` writes directly to the running kernel, and a firewall change travels the
same network path it may remove. A candidate ruleset that omits the rule
permitting the administrator's own session ends that session the moment it
loads, and the connection needed to undo the change is the connection the change
just dropped. The remedies are physical access, out-of-band management, or a
rollback armed before the change that fires without operator action.

Three `nft` properties make a safe procedure possible:

- `nft --check --file FILE` validates a file against the running kernel and
  applies nothing, so a typo is caught before it reaches the packet path.
- `nft --file FILE` is a single transaction. The kernel builds the new ruleset
  alongside the old one and swaps them in one step, so the host is never
  half-configured, and a file that fails on its last line changes nothing.
- `nft list ruleset` output is valid `nft --file` input, so the previous state
  can be captured as a loadable rollback file.

### Rules

- Rule changes **MUST** be applied from a serial console, an out-of-band
  management interface, or a session that does not traverse the firewall being
  changed. Where none of those exists, a timed rollback **MUST** be armed before
  the candidate is loaded.
- Every candidate file **MUST** pass `nft --check --file FILE` before it is
  loaded.
- Every rule change **MUST** be a single `nft --file` transaction. Shell scripts
  that issue a sequence of `nft add` commands leave the host partially
  configured between commands.
- A configuration file **MUST** replace only the tables it owns.
- `flush ruleset` **MUST NOT** appear in any file loaded on a host where Docker,
  firewalld, libvirt, podman, or a CNI plugin manages its own tables.
- `nft flush ruleset` **MUST NOT** be run as a standalone command outside
  [Break-Glass Recovery](#break-glass-recovery).
- The rollback **MUST** be armed before the candidate is loaded, and cancelled
  only after management access has been reverified from a new session.
- Rollback files **SHOULD** be kept in `/var/lib/nftables-rollback` with mode
  `0600`, because a captured ruleset discloses the host's entire access policy.

### Own One Table, Not the Whole Ruleset

Docker creates the `ip docker-bridges` and `ip6 docker-bridges` tables and
"expects to have full ownership of its tables"; firewalld, libvirt, and podman
manage their own tables the same way. A file beginning `flush ruleset` deletes
all of them, which silently removes container and virtual-machine connectivity
along with the policy that was being replaced.

Replace one named table instead. `destroy table` removes the table if it is
present and succeeds if it is not, so the file is idempotent and needs no
guard:

```text
# GOOD: /etc/nftables.conf replaces only the table this host owns.
#!/usr/sbin/nft -f
destroy table inet filter

table inet filter {
  chain input {
    type filter hook input priority filter; policy drop;

    iif "lo" accept
    ct state established,related accept
    ct state invalid drop

    meta l4proto ipv6-icmp accept
    icmp type { echo-request, destination-unreachable, time-exceeded } accept

    tcp dport 22 accept
  }
}
```

```text
# BAD: destroys every table on the host, including docker-bridges.
#!/usr/sbin/nft -f
flush ruleset

table inet filter {
  chain input {
    type filter hook input priority filter; policy drop;
    tcp dport 22 accept
  }
}
```

`flush ruleset` is acceptable in exactly one routine case: a host that owns its
entire ruleset, where the file that flushes also defines every table the host
needs. On any host running Docker, firewalld, libvirt, or podman, that condition
does not hold.

`destroy` is version-sensitive. Debian 13's nftables `1.1.3-1` accepts
`destroy table`; Debian 12's nftables 1.0.6 rejects it with `syntax error,
unexpected table`. Upstream stable is 1.1.7. On 1.0.x, open the file with the
create-then-delete pair instead, which cannot fail whether or not the table
already exists:

```text
table inet filter
delete table inet filter

table inet filter {
  # ...
}
```

### Deploy With an Armed Rollback

`nft-deploy` captures the current definition of the owned table, validates the
candidate, arms a rollback, and only then loads the candidate. Install it as
`/usr/local/sbin/nft-deploy` with mode `0750`:

```bash
#!/usr/bin/env bash
# /usr/local/sbin/nft-deploy - load a candidate ruleset with an armed rollback.
# Run from a serial console, out-of-band management, or a session that does
# not traverse the firewall being changed.
set -euo pipefail

candidate=${1:-/etc/nftables.conf}
family=${NFT_FAMILY:-inet}
table=${NFT_TABLE:-filter}
window=${NFT_ROLLBACK_WINDOW:-5min}

state=/var/lib/nftables-rollback
rollback="$state/rollback-$(date -u +%Y%m%dT%H%M%SZ).nft"

umask 077
mkdir -p "$state"

# 1. Capture the live definition of the table this host owns. The destroy
#    line makes the rollback file a complete replacement for that table and
#    leaves tables owned by Docker, firewalld or libvirt untouched.
printf 'destroy table %s %s\n' "$family" "$table" > "$rollback"
nft list table "$family" "$table" >> "$rollback" 2>/dev/null || true

# 2. Reject a rollback file or a candidate that does not parse. --check
#    validates against the running kernel without changing anything.
nft --check --file "$rollback"
nft --check --file "$candidate"

# 3. Arm the rollback BEFORE the candidate is loaded. AccuracySec is pinned
#    because systemd timers default to AccuracySec=1min.
systemd-run --unit=nft-rollback --collect \
  --on-active="$window" --timer-property=AccuracySec=1s \
  /usr/sbin/nft --file "$rollback"

# 4. Load the candidate atomically.
nft --file "$candidate"

cat <<MSG
Candidate loaded. Rollback to $rollback fires in $window.
Verify management access from a NEW, independent session, then cancel:
  systemctl stop nft-rollback.timer
MSG
```

The candidate **MUST** define only the table named by `NFT_TABLE`. The rollback
restores that one table; a table created by a stray candidate is outside its
reach.

`--timer-property=AccuracySec=1s` is **REQUIRED**. systemd timers default to
`AccuracySec=1min`, and a rollback that drifts by up to a minute is a minute of
lost management access.

### Verify Before Cancelling the Rollback

Health checks **MUST** run in a connection opened after the change, not in the
session that applied it: an established connection survives on the conntrack
`established,related` rule and proves nothing about new ones.

```bash
# From a workstation, on a NEW connection - not the deploy session.
ssh -o BatchMode=yes -o ConnectTimeout=5 admin@host true \
  && echo "management access OK"

# Confirm the intended policy is the live policy.
ssh admin@host nft list chain inet filter input
```

Cancel the rollback only once those checks pass:

```bash
systemctl stop nft-rollback.timer
```

If they fail, change nothing and wait: the armed timer restores the previous
ruleset without any further access to the host.

### Break-Glass Recovery

This is the only place `flush ruleset` belongs in a command an operator types.
It **MUST** be used from a console or out-of-band session, and only when the
host is unreachable and the rollback timer has already been lost.

Keep the recovery ruleset on disk as a complete replacement file rather than
clearing the ruleset and leaving the host unprotected:

```text
#!/usr/sbin/nft -f
# /etc/nftables.d/break-glass.nft
# BREAK GLASS ONLY. Replaces every table on this host with a minimal
# management-only policy. Tables owned by Docker, firewalld, libvirt and
# podman are destroyed; restart those services afterwards to rebuild them.
flush ruleset

table inet break-glass {
  chain input {
    type filter hook input priority filter; policy drop;

    iif "lo" accept
    ct state established,related accept
    meta l4proto ipv6-icmp accept

    ip saddr 203.0.113.0/24 tcp dport 22 accept
  }

  chain forward {
    type filter hook forward priority filter; policy drop;
  }

  chain output {
    type filter hook output priority filter; policy accept;
  }
}
```

Replace `203.0.113.0/24` with the administrative network. Then, at the console:

```bash
# Capture what is live before replacing it, for the incident record.
install -d -m 0700 /var/lib/nftables-rollback
install -m 0600 /dev/null /var/lib/nftables-rollback/pre-break-glass.nft
nft list ruleset > /var/lib/nftables-rollback/pre-break-glass.nft

nft --check --file /etc/nftables.d/break-glass.nft
nft --file /etc/nftables.d/break-glass.nft
```

A bare `nft flush ruleset` **MUST NOT** be used in its place. It leaves the host
with no packet filtering at all rather than a reduced policy, and the difference
is the whole exposure window until a real ruleset is loaded.

## Base Configuration

TODO: `/etc/nftables.conf` structure, tables, chains, rules.

## Common Rulesets

TODO: Default deny, SSH access, web server, Docker integration.

## Rate Limiting

TODO: Connection rate limiting, SYN flood protection.

## Logging

TODO: Logging dropped packets, integration with rsyslog/journald.

## Persistence

Atomic rule loading is covered in
[Safe Rule Deployment](#safe-rule-deployment).

TODO: `nftables.service`, boot ordering, configuration management.

## See Also

- [Linux Guide](../os/linux.md) — Base OS configuration
- [SSH Guide](ssh.md) — Secure remote access
- [Docker Guide](../docker.md) — Container networking
