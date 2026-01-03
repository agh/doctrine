# NTP Style Guide

> [Doctrine](../../../README.md) > [Infrastructure](../README.md) > NTP

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

## Quick Reference

| Task | Tool | Command |
| ---- | ---- | ------- |
| Install | apt | `apt install chrony` |
| Check sync | chronyc | `chronyc tracking` |
| List sources | chronyc | `chronyc sources -v` |

## Overview

TODO: Time synchronization with chrony for Debian systems.

## Configuration

TODO: `/etc/chrony/chrony.conf` configuration.

## Hardening

TODO: NTS (Network Time Security), access control.

## Monitoring

TODO: Prometheus chrony exporter, alerting on drift.

## See Also

- [Linux Guide](../os/linux.md) — Base OS configuration
- [SSH Guide](ssh.md) — Secure remote access
