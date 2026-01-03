# DNS Style Guide

> [Doctrine](../../../README.md) > [Infrastructure](../README.md) > DNS

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

## Quick Reference

| Task | Tool | Command |
| ---- | ---- | ------- |
| Query | dig | `dig example.com` |
| Trace | dig | `dig +trace example.com` |
| Check resolver | resolvectl | `resolvectl status` |

## Overview

TODO: DNS resolver configuration and local DNS services.

## Resolver Configuration

TODO: systemd-resolved, `/etc/resolv.conf` management.

## DNS-over-TLS / DNS-over-HTTPS

TODO: Encrypted DNS configuration.

## Local DNS Server

TODO: Unbound or dnsmasq for local caching/resolution.

## Split-Horizon DNS

TODO: Internal vs external resolution.

## See Also

- [Linux Guide](../os/linux.md) — Base OS configuration
- [Networking Guide](../../process/README.md) — Network fundamentals
