# Infrastructure Services

> [Doctrine](../../../README.md) > [Infrastructure](../README.md) > Services

Configuration guides for common infrastructure services. Each guide covers
cross-platform setup with platform-specific sections where needed.

## Service Guides

| Service | Guide | Description |
| ------- | ----- | ----------- |
| SSH | [ssh.md](ssh.md) | SSH server hardening and configuration |
| NTP | *Coming soon* | Time synchronization (chrony, systemd-timesyncd) |
| DNS | *Coming soon* | Resolver configuration, local DNS |
| Firewall | *Coming soon* | nftables, pf, Windows Firewall |
| Logging | *Coming soon* | Centralized logging, log rotation |
| Certificates | *Coming soon* | TLS certificates, ACME/Let's Encrypt |

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
