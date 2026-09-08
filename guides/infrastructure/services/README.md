# Infrastructure Services

> [Doctrine](../../../README.md) > [Infrastructure](../README.md) > Services

Configuration guides for common infrastructure services. Each guide covers
cross-platform setup with platform-specific sections where needed.

## Service Guides

| Service | Guide | Status | Description |
| ------- | ----- | ------ | ----------- |
| SSH | [ssh.md](ssh.md) | Complete | SSH server hardening and configuration |
| NTP | [ntp.md](ntp.md) | Draft | Time synchronisation with chrony |
| DNS | [dns.md](dns.md) | Draft | Resolver configuration, local DNS |
| Firewall | [nftables.md](nftables.md) | Draft | nftables firewall configuration |
| Logging | [logging.md](logging.md) | Draft | Centralised logging and log rotation |

**Draft** means the guide has a Quick Reference table and section headings but
unwritten bodies marked `TODO`. Draft guides **MUST NOT** be treated as
normative until the TODOs are resolved.

TLS certificates (ACME/Let's Encrypt) have no guide and none is drafted; see
[Roadmap](#roadmap).

## Roadmap

| Service | Planned coverage |
| ------- | ---------------- |
| Certificates | TLS certificate issuance and renewal, ACME/Let's Encrypt, internal CAs |

## Common Patterns

### Service Checklist

Every service deployment **SHOULD** address:

- [ ] **Authentication**: How is access controlled?
- [ ] **Encryption**: Is traffic encrypted in transit?
- [ ] **Logging**: Are security events logged?
- [ ] **Monitoring**: Are health checks configured?
- [ ] **Backup**: Is configuration backed up?
- [ ] **Updates**: How are security updates applied?

### Configuration Management

- **MUST** use Ansible, Puppet, or similar for production config
- **MUST** version control all configuration
- **SHOULD** test changes in staging before production
- **SHOULD** use templates with environment-specific values

### Documentation

Each service **SHOULD** have:

- Purpose and scope
- Upstream documentation link
- Configuration file locations
- Relevant log files
- Troubleshooting commands

## See Also

- [OS Fundamentals](../os/README.md) — Operating system concepts
- [Linux Guide](../os/linux.md) — Debian-specific configuration
- [Ansible Guide](../ansible.md) — Automated service configuration
