# Logging Style Guide

> [Doctrine](../../../README.md) > [Infrastructure](../README.md) > Logging

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

## Quick Reference

| Task | Tool | Command |
| ---- | ---- | ------- |
| View logs | journalctl | `journalctl -f` |
| Filter by unit | journalctl | `journalctl -u nginx` |
| Export logs | journalctl | `journalctl --output=json` |

## Overview

TODO: Centralized logging architecture for infrastructure.

## journald Configuration

TODO: `/etc/systemd/journald.conf`, storage, retention.

## Structured Logging

TODO: JSON logging, log levels, correlation IDs.

## Log Aggregation

TODO: Loki, Vector, or rsyslog forwarding.

## Log Retention

TODO: Rotation policies, compliance requirements.

## Security

TODO: Log integrity, tamper detection, access control.

## See Also

- [Linux Guide](../os/linux.md) — Base OS configuration
- [Monitoring Guide](../../process/README.md) — Metrics and alerting
