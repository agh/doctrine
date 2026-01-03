# nftables Style Guide

> [Doctrine](../../../README.md) > [Infrastructure](../README.md) > nftables

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

## Quick Reference

| Task | Tool | Command |
| ---- | ---- | ------- |
| List rules | nft | `nft list ruleset` |
| Apply config | nft | `nft -f /etc/nftables.conf` |
| Flush rules | nft | `nft flush ruleset` |

## Overview

TODO: Linux firewall configuration with nftables (replacement for iptables).

## Base Configuration

TODO: `/etc/nftables.conf` structure, tables, chains, rules.

## Common Rulesets

TODO: Default deny, SSH access, web server, Docker integration.

## Rate Limiting

TODO: Connection rate limiting, SYN flood protection.

## Logging

TODO: Logging dropped packets, integration with rsyslog/journald.

## Persistence

TODO: systemd service, atomic rule loading.

## See Also

- [Linux Guide](../os/linux.md) — Base OS configuration
- [SSH Guide](ssh.md) — Secure remote access
- [Docker Guide](../docker.md) — Container networking
