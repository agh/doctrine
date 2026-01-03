# Ansible Configuration Templates

Ready-to-use configuration files for Ansible projects following
[Doctrine Ansible Style Guide](../../guides/infrastructure/ansible.md).

## Files

| File | Description | Copy to |
| ---- | ----------- | ------- |
| `ansible.cfg` | Main Ansible config with performance optimizations | Project root |
| `.ansible-lint` | Linting config for ansible-lint (production profile) | Project root |
| `.yamllint` | YAML linting configuration for Ansible projects | Project root |
| `.sops.yaml` | SOPS config for secrets management (multi-cloud) | Project root |
| `requirements.yml` | Galaxy collections requirements (core + community) | `collections/` |

## Quick Start

```bash
# Copy all configs to your Ansible project
cp configs/ansible/ansible.cfg .
cp configs/ansible/.ansible-lint .
cp configs/ansible/.yamllint .
cp configs/ansible/.sops.yaml .
cp configs/ansible/requirements.yml collections/requirements.yml

# Install collections
ansible-galaxy collection install -r collections/requirements.yml

# Install linting tools
pipx install ansible-dev-tools

# Lint your playbooks
ansible-lint
yamllint .
```

## Configuration Details

### ansible.cfg

Optimized configuration with:

- **Performance**: 20 forks, SSH pipelining, fact caching
- **Security**: Host key checking enabled, strict SSH settings
- **Output**: YAML output with task profiling
- **Plugins**: SOPS vars plugin enabled for secrets

### .ansible-lint

Production-profile linting with:

- Minimum Ansible Core 2.18
- Opt-in security rules (no-log-password, etc.)
- Task name prefix enforcement
- FQCN requirements

### .yamllint

Ansible-optimized YAML linting:

- 120 character line length (warning level)
- 2-space indentation with sequence indent
- Allows octal file modes (0644, 0755, etc.)
- Excludes common directories (vault/, .github/, etc.)

### .sops.yaml

Multi-cloud secrets management:

- Production: AWS KMS
- Staging: PGP
- Development: age (modern PGP alternative)
- Encrypted regex patterns for sensitive keys

### requirements.yml

Essential collections:

- Core: ansible.posix, ansible.utils
- Community: general, docker, postgresql, mysql
- Security: community.sops
- Cloud: AWS, Azure, GCP
- Observability: Prometheus, Grafana

## Customization

1. **ansible.cfg**: Update `inventory` path and `forks` count for your
   infrastructure size
2. **.sops.yaml**: Replace KMS ARNs, PGP fingerprints, and age keys with
   your own
3. **requirements.yml**: Add/remove collections based on your tech stack

## See Also

- [Ansible Style Guide](../../guides/infrastructure/ansible.md)
- [Ansible Documentation](https://docs.ansible.com/)
- [ansible-lint Documentation](https://ansible-lint.readthedocs.io/)
- [SOPS Documentation](https://github.com/getsops/sops)
