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
- **Output**: Built-in default callback with YAML result format and task
  profiling
- **Plugins**: SOPS vars plugin enabled for secrets

Comments are kept on their own lines throughout. Ansible's INI parser treats
an inline `# ...` as part of the value: on an integer it aborts startup, and
on a boolean such as `host_key_checking` it evaluates to `False`, quietly
disabling the setting the comment claims to document.

The stdout callback is `ansible.builtin.default` with
`callback_result_format = yaml`, not the `yaml` callback. The
`community.general.yaml` callback has been removed, so a clean install that
resolves a current `community.general` cannot start a playbook configured to
use it. Aggregate callbacks are named by FQCN
(`ansible.posix.profile_tasks`, `ansible.posix.timer`).

### .ansible-lint

Production-profile linting with:

- Opt-in security rules (no-log-password, etc.)
- Task name prefix enforcement via `task_name_prefix` (a string template)
- FQCN requirements

Validated against ansible-lint 26.8.0. The configuration schema is closed:
unknown keys and wrong value types make ansible-lint exit 3 before it lints
anything. Declare the minimum ansible-core version in `meta/runtime.yml` as
`requires_ansible: ">=2.18.0"` — there is no `min_ansible_version` config key.

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
- Allow-list encryption: every value is encrypted except the metadata keys
  named in `unencrypted_regex`

Rules use `unencrypted_regex`, not `encrypted_regex`. A deny-list of key
names anchored with `^...$` leaves fields such as `database_password`,
`api_key`, and `ssl_private_key` in plaintext while `sops` still reports
success.

### requirements.yml

Essential collections, pinned to the current Galaxy releases:

- Core: ansible.posix, ansible.utils
- Community: general, docker, postgresql, crypto
- Database: ansible.mysql (community.mysql is deprecated)
- Security: community.sops
- Cloud: AWS, Azure, GCP, OpenStack, VMware
- Observability: prometheus.prometheus, community.grafana

Every dynamic inventory plugin listed in `ansible.cfg` has its collection
declared here. `enable_plugins` names a plugin; it does not install one.

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
