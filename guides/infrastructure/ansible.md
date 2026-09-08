# Ansible Style Guide

> [Doctrine](../../README.md) > [Infrastructure](README.md) > Ansible

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in
[RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

**Target Version**: Ansible Core 2.18+ with Python 3.12+

## Quick Reference

| Task | Tool | Command |
| ---- | ---- | ------- |
| Install | pipx | `pipx install --include-deps ansible-core` |
| Install dev tools | pipx | `pipx install ansible-dev-tools` |
| Lint | ansible-lint[^1] | `ansible-lint` |
| YAML lint | yamllint[^2] | `yamllint .` |
| Test roles | Molecule[^3] | `molecule test` |
| Syntax check | ansible-playbook | `ansible-playbook --syntax-check playbook.yml` |
| Dry run | ansible-playbook | `ansible-playbook --check playbook.yml` |
| List tasks | ansible-playbook | `ansible-playbook --list-tasks playbook.yml` |
| Vault encrypt | ansible-vault | `ansible-vault encrypt vars/secrets.yml` |
| SOPS encrypt | sops[^4] | `sops -e vars/secrets.yml` |
| Galaxy install | ansible-galaxy | `ansible-galaxy collection install -r requirements.yml` |

## Why Ansible

**Why Ansible for infrastructure automation?**

- **Agentless**: No software required on managed nodes (uses SSH/WinRM)
- **YAML-based**: Human-readable, declarative configuration
- **Idempotent**: Safe to run multiple times without side effects
- **Extensive modules**: 6,000+ built-in modules across collections
- **Low barrier to entry**: Simple syntax with powerful capabilities
- **Strong ecosystem**: Large community, Ansible Galaxy collections, Red Hat
  support

Ansible excels at configuration management, application deployment, and
orchestration across infrastructure fleets without the complexity of
agent-based solutions like Puppet or Chef.

## Python Version Requirements

Ansible Core 2.18 **MUST** use Python 3.11+ for the control node (where
Ansible runs) and Python 3.8+ for managed nodes (targets)[^5].

**Why these requirements?** Python 3.10 reached end-of-life in 2024, and
Ansible 2.18 leverages newer Python features for improved performance and
maintainability. Target nodes running Python 3.7 are no longer supported.

```bash
# Verify Python version on control node
python3 --version  # Should be 3.12+

# Install Ansible Core with pipx (recommended)
pipx install --include-deps ansible-core

# Or install ansible-dev-tools (includes ansible-lint, molecule, etc.)
pipx install ansible-dev-tools
```

## Project Structure

Projects **MUST** follow this directory layout for maintainability and clarity:

```text
ansible-project/
├── ansible.cfg                 # Ansible configuration
├── .ansible-lint               # Linting configuration
├── requirements.yml            # Galaxy collections/roles
├── inventories/
│   ├── production/
│   │   ├── hosts.yml           # Production inventory (YAML format)
│   │   ├── group_vars/         # Loaded: adjacent to this inventory
│   │   │   ├── all.yml
│   │   │   └── webservers.yml
│   │   └── host_vars/
│   │       └── web01.yml       # Host-specific variables
│   └── staging/
│       ├── hosts.yml
│       └── group_vars/
│           └── all.yml
├── playbooks/
│   ├── site.yml                # Master playbook
│   ├── webservers.yml          # Server-specific playbooks
│   ├── deploy.yml
│   └── group_vars/             # Loaded: adjacent to these playbooks
│       └── all.yml
├── roles/
│   ├── common/                 # Shared base configuration
│   │   ├── tasks/
│   │   │   └── main.yml
│   │   ├── handlers/
│   │   │   └── main.yml
│   │   ├── templates/
│   │   ├── files/
│   │   ├── vars/
│   │   │   └── main.yml
│   │   ├── defaults/
│   │   │   └── main.yml
│   │   ├── meta/
│   │   │   └── main.yml
│   │   ├── molecule/           # Molecule testing
│   │   │   └── default/
│   │   │       ├── molecule.yml
│   │   │       ├── converge.yml
│   │   │       └── verify.yml
│   │   └── README.md
│   ├── nginx/
│   └── postgresql/
├── collections/
│   └── requirements.yml        # Collection dependencies
├── filter_plugins/             # Custom Jinja2 filters
├── vault/
│   └── secrets.yml             # Encrypted secrets (ansible-vault)
└── .github/
    └── workflows/
        └── ansible-lint.yml    # CI/CD integration
```

**Why this structure?**

- Clear separation between environments (`inventories/`)
- Reusable roles for common configurations (`roles/`)
- Variables live beside the inventory that owns them (`inventories/*/group_vars/`)
- Logical grouping of playbooks by purpose
- Integrated testing with Molecule
- CI/CD ready with GitHub Actions

### Where Ansible Loads group_vars and host_vars

`group_vars/` and `host_vars/` directories **MUST** be placed next to the
selected inventory source or next to the playbook. Ansible loads them from
exactly those two locations[^16] and nowhere else.

**Why?** A `group_vars/` directory in the project root is loaded only when
the playbook itself is in the project root. If playbooks live in
`playbooks/`, a root-level `group_vars/all.yml` is silently ignored — the
variables are simply undefined at run time, so a task either fails with an
undefined-variable error or, worse, falls back to a `default()` value.

```text
# Loaded when running:
#   ansible-playbook -i inventories/production/hosts.yml playbooks/site.yml

inventories/production/group_vars/all.yml   # inventory-adjacent: loaded
playbooks/group_vars/all.yml                # playbook-adjacent:  loaded
group_vars/all.yml                          # project root:       IGNORED
```

Variables shared by every environment **SHOULD** live in role
`defaults/main.yml`, or be duplicated deliberately per inventory. Ansible
provides no project-wide "global" variable directory.

## Linting & Formatting

### ansible-lint

All playbooks and roles **MUST** pass ansible-lint[^1] checks. Ansible-lint
promotes proven practices and prevents common pitfalls.

```bash
# Install (comes with ansible-dev-tools)
pipx install ansible-lint

# Run on entire project
ansible-lint

# Run on specific playbook
ansible-lint playbooks/webservers.yml

# Run with auto-fix
ansible-lint --fix
```

**Configuration** (`.ansible-lint`):

```yaml
---
# ansible-lint configuration
# Schema: https://docs.ansible.com/projects/lint/configuring/

# Enable all rules by default, opt-out problematic ones
skip_list:
  - yaml[line-length]  # Allow longer lines for readability
  - role-name[path]    # Allow flexible role naming

# Enable opt-in rules
enable_list:
  - args                 # Check task arguments
  - empty-string-compare # Avoid comparing to empty strings
  - no-log-password     # Ensure no_log for passwords
  - no-same-owner       # Avoid redundant owner/group
  - name[prefix]        # Require task name prefixes

# Use production profile (strictest)
profile: production

# Exclude paths
exclude_paths:
  - .github/
  - .ansible_cache/
  - molecule/
  - vault/

# Prefix template for name[prefix]; {stem} is the task file name
task_name_prefix: "{stem} | "

# Offline mode (don't check Galaxy)
offline: false
```

Every key **MUST** exist in the ansible-lint configuration schema, and every
value **MUST** use the type that schema declares. ansible-lint 26.8.0
validates `.ansible-lint` against a closed JSON schema and exits 3 on any
unknown key or wrong value type, so a typo stops the linter rather than
loosening a rule.

The minimum ansible-core version **MUST NOT** be set here; there is no
`min_ansible_version` key. Declare it in `meta/runtime.yml` instead, which is
what the `meta-runtime` rule checks:

```yaml
# meta/runtime.yml
---
requires_ansible: ">=2.18.0"
```

**Why?** `.ansible-lint` configures the linter; `meta/runtime.yml` declares
what the content itself supports. Only the latter travels with the role or
collection when it is published to Galaxy.

**Why ansible-lint?** It catches common mistakes like missing task names,
deprecated syntax, security issues (exposed passwords), and non-idempotent
operations before they cause production problems.

### yamllint

All YAML files **MUST** pass yamllint[^2] checks for consistency.

```bash
# Install
pipx install yamllint

# Lint all YAML files
yamllint .
```

**Configuration** (`.yamllint`):

```yaml
---
extends: default

rules:
  line-length:
    max: 120
    level: warning
  indentation:
    spaces: 2
    indent-sequences: true
  comments:
    min-spaces-from-content: 1
  braces:
    max-spaces-inside: 1
  brackets:
    max-spaces-inside: 1
  truthy:
    allowed-values: ['true', 'false', 'yes', 'no']

ignore: |
  .github/
  .ansible_cache/
  vault/
```

### Pre-commit Hooks

Projects **SHOULD** use pre-commit hooks to enforce quality standards:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/ansible/ansible-lint
    rev: v25.11.1
    hooks:
      - id: ansible-lint
        args: [--profile=production]

  - repo: https://github.com/adrienverge/yamllint
    rev: v1.35.1
    hooks:
      - id: yamllint
        args: [-c=.yamllint]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
        args: [--unsafe]  # Allow ansible-vault encrypted files
      - id: check-added-large-files
```

```bash
# Install pre-commit
pipx install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Inventory Management

### Static Inventory (YAML Format)

Static inventories **SHOULD** use YAML format for clarity and consistency:

```yaml
# inventories/production/hosts.yml
---
all:
  vars:
    # Global variables for all hosts
    ansible_user: deploy
    ansible_become: true
    domain: example.com

  children:
    webservers:
      hosts:
        web01.example.com:
          ansible_host: 192.168.1.10
          http_port: 80
        web02.example.com:
          ansible_host: 192.168.1.11
          http_port: 80
      vars:
        nginx_worker_processes: 4
        nginx_max_clients: 200

    databases:
      hosts:
        db01.example.com:
          ansible_host: 192.168.1.20
          # Pin the major explicitly; see the platform support matrix below
          postgresql_version: "16"
      vars:
        postgresql_max_connections: 100

    # Group of groups: every child MUST be a mapping key, not a bare scalar
    production:
      children:
        webservers:
        databases:
      vars:
        environment: production
```

Child group names under `children` **MUST** be written as mapping keys with a
trailing colon. Consecutive bare scalars are folded by the YAML parser into a
single multi-word string, so `webservers` and `databases` become one child
group literally named `webservers databases`.

**Why does this matter?** `ansible-inventory` exits successfully either way.
The damage is silent: `production` ends up with one child group that contains
no hosts, so `ansible-playbook --limit production` reports zero matched hosts
and the deployment quietly skips every server it was supposed to reach. Run
every inventory through `ansible-inventory --graph` and assert the expected
hosts appear under each group.

**Why YAML over INI?** YAML supports nested structures, lists, and complex
data types, making it more suitable for modern infrastructure-as-code
practices.

### Dynamic Inventory

Dynamic inventories **SHOULD** be used for cloud environments to automatically
discover hosts:

```yaml
# inventories/aws_ec2.yml (AWS dynamic inventory)
---
plugin: amazon.aws.aws_ec2
regions:
  - us-east-1
  - us-west-2
filters:
  tag:Environment: production
  instance-state-name: running
keyed_groups:
  # Group by instance type
  - key: instance_type
    prefix: instance_type
  # Group by tag Role
  - key: tags.Role
    prefix: role
  # Group by availability zone
  - key: placement.availability_zone
    prefix: az
hostnames:
  - dns-name
  - private-ip-address
compose:
  ansible_host: public_ip_address
  ansible_user: "'ubuntu' if platform_details.endswith('Ubuntu') else 'ec2-user'"
```

```bash
# List dynamic inventory
ansible-inventory -i inventories/aws_ec2.yml --list

# Use in playbook
ansible-playbook -i inventories/aws_ec2.yml playbooks/webservers.yml
```

**Supported dynamic inventory plugins**[^6]. Each plugin ships in a collection
that **MUST** be declared in `requirements.yml` before the plugin is used:

| Plugin | Collection | Pinned version |
| ------ | ---------- | -------------- |
| `amazon.aws.aws_ec2` | `amazon.aws` | 11.4.0 |
| `azure.azcollection.azure_rm` | `azure.azcollection` | 4.0.0 |
| `google.cloud.gcp_compute` | `google.cloud` | 1.14.0 |
| `openstack.cloud.openstack` | `openstack.cloud` | 2.6.0 |
| `community.vmware.vmware_vm_inventory` | `community.vmware` | 6.3.0 |

**Why declare the collection?** `enable_plugins` in `ansible.cfg` names a
plugin, it does not install one. An inventory plugin whose collection is
absent makes `ansible-inventory` fall through to the next parser and report an
empty inventory, so a playbook targets nothing instead of failing loudly.

### Group Structure Best Practices

Groups **SHOULD** be organized by:

- **Environment** (production, staging, development)
- **Function** (webservers, databases, loadbalancers)
- **Location** (us-east, eu-west)
- **Provider** (aws, azure, on-prem)

```yaml
# Multi-dimensional grouping
all:
  children:
    # By environment
    production:
      children:
        prod_webservers:
        prod_databases:
    staging:
      children:
        staging_webservers:

    # By function
    webservers:
      children:
        prod_webservers:
        staging_webservers:

    # By location
    us_east:
      children:
        us_east_webservers:
        us_east_databases:
```

## Playbook Best Practices

### Playbook Structure

Playbooks **MUST** include descriptive names and follow this structure:

```yaml
---
# playbooks/webservers.yml
- name: Configure web servers
  hosts: webservers
  become: true
  gather_facts: true

  vars:
    http_port: 80
    max_clients: 200

  pre_tasks:
    - name: Update apt cache
      ansible.builtin.apt:
        update_cache: true
        cache_valid_time: 3600
      when: ansible_os_family == "Debian"

  roles:
    - role: common
    - role: nginx
      vars:
        nginx_port: "{{ http_port }}"

  tasks:
    - name: Ensure nginx service is running
      ansible.builtin.service:
        name: nginx
        state: started
        enabled: true

  post_tasks:
    - name: Verify web server is responding
      ansible.builtin.uri:
        url: "http://{{ inventory_hostname }}"
        status_code: 200
      delegate_to: localhost

  handlers:
    - name: Restart nginx
      ansible.builtin.service:
        name: nginx
        state: restarted
```

### Task Formatting

All tasks **MUST**:

- Include a descriptive `name` field
- Use Fully Qualified Collection Names (FQCN)[^7]
- Use YAML dictionary format (not inline `key=value`)

```yaml
# GOOD: FQCN with descriptive name and dict format
- name: Install nginx web server
  ansible.builtin.apt:
    name: nginx
    state: present
    update_cache: true

# BAD: No FQCN, missing name, inline format
- apt: name=nginx state=present
```

**Why FQCN?** Fully Qualified Collection Names (e.g., `ansible.builtin.copy`
instead of `copy`) eliminate ambiguity about which module is being used,
especially when multiple collections provide similar modules. Required in
Ansible 2.10+.

### Task Naming Conventions

Task names **MUST** be descriptive and follow these conventions:

```yaml
# GOOD: Clear, action-oriented names
- name: Install PostgreSQL 16 server
- name: Deploy application configuration to /etc/app/config.yml
- name: Restart nginx service after config change
- name: Verify database connection is responding

# BAD: Vague or missing names
- name: Install package
- name: Copy file
- name: Run command
- apt: name=nginx state=present  # No name at all
```

**Naming pattern**: `<Action> <What> [to/from/in <Where>] [<Additional context>]`

### Tags and Selective Execution

Tasks **SHOULD** use tags for selective playbook execution:

```yaml
- name: Install nginx package
  ansible.builtin.apt:
    name: nginx
    state: present
  tags:
    - nginx
    - install
    - packages

- name: Deploy nginx configuration
  ansible.builtin.template:
    src: nginx.conf.j2
    dest: /etc/nginx/nginx.conf
  notify: Reload nginx
  tags:
    - nginx
    - config
```

```bash
# Run only tasks tagged 'config'
ansible-playbook playbooks/webservers.yml --tags config

# Skip tasks tagged 'install'
ansible-playbook playbooks/webservers.yml --skip-tags install

# Run multiple tags
ansible-playbook playbooks/webservers.yml --tags "nginx,config"
```

**Standard tag conventions**:

- `install` - Package installation
- `config` - Configuration file deployment
- `service` - Service management
- `verify` - Verification/testing tasks
- `never` - Tasks that only run when explicitly requested

### Handlers and Notifications

Handlers **SHOULD** be used for service restarts and one-time operations
triggered by changes:

```yaml
# tasks/main.yml
- name: Deploy nginx configuration
  ansible.builtin.template:
    src: nginx.conf.j2
    dest: /etc/nginx/nginx.conf
    validate: 'nginx -t -c %s'
  notify:
    - Reload nginx
    - Clear nginx cache

# handlers/main.yml
- name: Reload nginx
  ansible.builtin.service:
    name: nginx
    state: reloaded

- name: Clear nginx cache
  ansible.builtin.file:
    path: /var/cache/nginx
    state: absent
```

**Why handlers?** Handlers ensure services are restarted only once even if
multiple tasks trigger changes, and they run at the end of the play for
efficiency.

### Error Handling (block/rescue/always)

Complex error handling **SHOULD** use `block/rescue/always`:

```yaml
- name: Deploy application with rollback capability
  block:
    - name: Stop application service
      ansible.builtin.service:
        name: myapp
        state: stopped

    - name: Backup current version
      ansible.builtin.copy:
        src: /opt/myapp/app.jar
        dest: /opt/myapp/app.jar.backup
        remote_src: true

    - name: Deploy new version
      ansible.builtin.copy:
        src: app-v2.jar
        dest: /opt/myapp/app.jar

    - name: Start application service
      ansible.builtin.service:
        name: myapp
        state: started

    - name: Verify application health
      ansible.builtin.uri:
        url: http://localhost:8080/health
        status_code: 200
      retries: 5
      delay: 10

  rescue:
    - name: Rollback to previous version
      ansible.builtin.copy:
        src: /opt/myapp/app.jar.backup
        dest: /opt/myapp/app.jar
        remote_src: true

    # MUST be restarted, not started: the service is already running the
    # failed version, and `started` is a no-op on a running service
    - name: Restart application with previous version
      ansible.builtin.service:
        name: myapp
        state: restarted

    - name: Verify the restored version is healthy
      ansible.builtin.uri:
        url: http://localhost:8080/health
        status_code: 200
      retries: 5
      delay: 10

    - name: Fail deployment
      ansible.builtin.fail:
        msg: "Deployment failed, rolled back to previous version"

  always:
    # ansible.builtin.file does NOT expand shell globs; find the paths first
    - name: Find temporary deployment directories
      ansible.builtin.find:
        paths: /tmp
        patterns: 'deploy-*'
        file_type: any
      register: deploy_scratch

    - name: Clean up temporary files
      ansible.builtin.file:
        path: "{{ item.path }}"
        state: absent
      loop: "{{ deploy_scratch.files }}"
      loop_control:
        label: "{{ item.path }}"
```

**Why `restarted` in the rescue block?** `ansible.builtin.service` treats
`started` as an idempotent action that runs no command when the service is
already up[^17]. The health check only fails *after* the service has started,
so at rescue time the failed version is still running. Restoring the previous
artefact on disk and then asking for `started` reports `changed=0` and leaves
the broken build serving traffic — the rollback appears to succeed while
changing nothing. `restarted` always bounces the service, and the follow-up
health check proves the restored version actually works.

**Why `find` instead of a wildcard path?** `ansible.builtin.file` receives a
literal pathname and performs no glob expansion. Passing `/tmp/deploy-*`
makes Ansible look for a file whose name contains an asterisk, find nothing,
and report `ok` with `changed=0` while every matching directory survives.

**When to use**:

- `block` - Group related tasks that should succeed together
- `rescue` - Handle failures with recovery actions (like rollbacks)
- `always` - Cleanup tasks that run regardless of success/failure

### Retries for Transient Failures

Tasks prone to transient failures **SHOULD** use retries:

```yaml
- name: Download package from internet
  ansible.builtin.get_url:
    url: https://example.com/package.tar.gz
    dest: /tmp/package.tar.gz
  retries: 3
  delay: 5
  register: download_result
  until: download_result is succeeded

- name: Wait for service to be ready
  ansible.builtin.uri:
    url: http://localhost:8080/health
    status_code: 200
  retries: 30
  delay: 10
  until: result.status == 200
  register: result
```

## Role Development

### When to Create Roles

Roles **SHOULD** be created when:

- Configuration is reusable across multiple playbooks
- Task complexity exceeds 20-30 lines
- Multiple related configuration files exist
- You need to test configurations independently

Roles **SHOULD NOT** be created for:

- Single-use tasks (use playbook tasks instead)
- Very simple configurations (2-3 tasks)

### Role Structure

Roles **MUST** follow Ansible's standard directory structure[^8]:

```text
roles/nginx/
├── tasks/
│   └── main.yml           # Primary task entry point
├── handlers/
│   └── main.yml           # Event handlers (service restarts, etc.)
├── templates/
│   └── nginx.conf.j2      # Jinja2 templates
├── files/
│   └── index.html         # Static files
├── vars/
│   └── main.yml           # Internal variables (high priority)
├── defaults/
│   └── main.yml           # Default variables (low priority)
├── meta/
│   └── main.yml           # Role metadata and dependencies
├── molecule/              # Testing configuration
│   └── default/
│       ├── molecule.yml
│       ├── converge.yml
│       └── verify.yml
└── README.md              # Role documentation
```

### Defaults vs Vars

**defaults/main.yml** **SHOULD** contain:

- User-configurable parameters
- Sensible default values
- Variables meant to be overridden by users

**vars/main.yml** **SHOULD** contain:

- Internal implementation details
- Constants that shouldn't be overridden
- Platform-specific values

```yaml
# roles/nginx/defaults/main.yml (user-facing, overridable)
---
nginx_port: 80
nginx_worker_processes: auto
nginx_worker_connections: 1024
nginx_max_clients: 200
nginx_enable_ssl: false
nginx_ssl_protocols: "TLSv1.2 TLSv1.3"

# roles/nginx/vars/main.yml (internal, not meant to be changed)
---
nginx_config_path: /etc/nginx/nginx.conf
nginx_pid_file: /var/run/nginx.pid
nginx_log_dir: /var/log/nginx
nginx_package_name: nginx
```

**Why?** Ansible's variable precedence[^9] makes `defaults` the lowest
priority (easily overridden by users) while `vars` has higher priority
(protected from accidental override).

### Role Dependencies

Role dependencies **SHOULD** be declared in `meta/main.yml`:

```yaml
# roles/nginx/meta/main.yml
---
dependencies:
  - role: common
    vars:
      common_packages:
        - curl
        - vim

galaxy_info:
  author: Your Name
  description: Nginx web server configuration
  company: Your Company
  license: MIT
  min_ansible_version: "2.18"
  platforms:
    - name: Ubuntu
      versions:
        - jammy    # 22.04 LTS, compatibility target
        - noble    # 24.04 LTS
        - resolute # 26.04 LTS, current
    - name: Debian
      versions:
        - bookworm # 12, oldstable LTS, compatibility target
        - trixie   # 13, current stable
  galaxy_tags:
    - web
    - nginx
```

### Platform Support Matrix

Role metadata, Molecule platforms, and CI matrices **MUST** agree, and
**MUST NOT** list a release that is past its free security-support date.

| Platform | Status on 2026-09-08 | Support ends | Include? |
| -------- | -------------------- | ------------ | -------- |
| Debian 13 (trixie) | Current stable | 2028-08-09 (LTS 2030-06-30) | Yes, default |
| Debian 12 (bookworm) | Oldstable, LTS | 2028-06-30 | Yes, compatibility |
| Debian 11 (bullseye) | LTS ended 2026-08-31 | Expired | No |
| Ubuntu 26.04 (resolute) | Current LTS | 2031-04 | Yes, default |
| Ubuntu 24.04 (noble) | LTS | 2029-04 | Yes |
| Ubuntu 22.04 (jammy) | LTS | 2027-04 | Yes, compatibility |
| Ubuntu 20.04 (focal) | Standard support ended 2025-05-31 | ESM only | No |

**Why drop Bullseye and Focal?** Debian 11 left LTS on 31 August 2026 and
Ubuntu 20.04 left standard support on 31 May 2025; both now need a paid
extended-support subscription for security updates[^18]. Advertising them in
`platforms` tells Galaxy users the role is tested on a distribution that no
longer receives free patches.

Database majors follow their own policy. PostgreSQL supports each major for
five years, so 16 remains supported until 9 November 2028 while 18 is
current[^19]. Pin a major deliberately and track the **current minor** within
it; do not treat "not the newest major" as an upgrade defect.

### Argument Specs and Validation

Roles **SHOULD** define argument specs for validation and documentation[^10]:

```yaml
# roles/nginx/meta/argument_specs.yml
---
argument_specs:
  main:
    short_description: Nginx web server role
    description: Installs and configures Nginx web server
    author: Your Name
    options:
      nginx_port:
        type: int
        required: false
        default: 80
        description: Port for Nginx to listen on
      nginx_worker_processes:
        type: str
        required: false
        default: "auto"
        description: Number of worker processes (or 'auto')
        choices:
          - "auto"
          - "1"
          - "2"
          - "4"
      nginx_enable_ssl:
        type: bool
        required: false
        default: false
        description: Enable SSL/TLS support
      nginx_ssl_certificate:
        type: path
        required: false
        description: Path to SSL certificate file
      nginx_ssl_key:
        type: path
        required: false
        description: Path to SSL private key file
```

**Benefits**:

- Automatic validation of role variables
- Self-documenting roles
- Better error messages for invalid inputs
- IDE autocomplete support

## Collections

### Using Collections

Collections **SHOULD** be installed from Galaxy or Git:

```yaml
# collections/requirements.yml
---
collections:
  # From Ansible Galaxy
  - name: community.general
    version: ">=9.0.0"

  - name: community.sops
    version: ">=1.8.0"

  - name: ansible.posix
    version: ">=1.6.0"

  # From Git repository
  - name: https://github.com/organization/collection.git
    type: git
    version: main
```

```bash
# Install collections
ansible-galaxy collection install -r collections/requirements.yml

# Install to specific path
ansible-galaxy collection install -r collections/requirements.yml -p ./collections
```

### Collection-based Project Organization

Large projects **MAY** use collection structure for better organization:

```text
my_namespace/my_collection/
├── plugins/
│   ├── modules/
│   ├── inventory/
│   └── filter/
├── roles/
│   ├── role1/
│   └── role2/
├── playbooks/
├── docs/
├── tests/
├── galaxy.yml
└── README.md
```

## Idempotency

All tasks **MUST** be idempotent - safe to run multiple times without
changing the result beyond the initial run.

### Ensuring Idempotency

```yaml
# GOOD: Idempotent - running multiple times has same effect
- name: Ensure nginx is installed
  ansible.builtin.apt:
    name: nginx
    state: present

- name: Ensure log directory exists with correct permissions
  ansible.builtin.file:
    path: /var/log/myapp
    state: directory
    mode: '0755'
    owner: appuser
    group: appuser

# BAD: Not idempotent - appends line every time
- name: Add log entry
  ansible.builtin.shell: echo "Deployed at $(date)" >> /var/log/deploy.log

# GOOD: Idempotent - the line content is stable, so lineinfile matches it
# on the second run and reports no change
- name: Record the deployed release
  ansible.builtin.lineinfile:
    path: /var/log/deploy.log
    line: "Deployed {{ app_version }}"
    create: true
    mode: '0644'

# INTENTIONALLY CHANGING: a timestamp differs on every run, so it can never
# be idempotent. Use regexp so the single marker line is replaced rather
# than accumulated, and accept that the task always reports changed.
- name: Update the deployment timestamp marker
  ansible.builtin.lineinfile:
    path: /var/run/myapp/last-deploy
    regexp: '^Deployed '
    line: "Deployed {{ ansible_facts.date_time.iso8601 }}"
    create: true
    mode: '0644'

# BAD: Not idempotent - adds user to group every time
- name: Add user to docker group
  ansible.builtin.command: usermod -aG docker myuser

# GOOD: Idempotent version
- name: Ensure user is in docker group
  ansible.builtin.user:
    name: myuser
    groups: docker
    append: true
```

### changed_when and failed_when

Use `changed_when` to control when tasks report changes:

```yaml
- name: Check if reboot is required
  ansible.builtin.stat:
    path: /var/run/reboot-required
  register: reboot_required
  changed_when: false  # Never report as changed

- name: Get current kernel version
  ansible.builtin.command: uname -r
  register: kernel_version
  changed_when: false

- name: Run database migration
  ansible.builtin.command: ./manage.py migrate
  register: migration_result
  changed_when: '"No migrations to apply" not in migration_result.stdout'
  failed_when:
    - migration_result.rc != 0
    - '"already exists" not in migration_result.stderr'
```

**Why?** Properly using `changed_when` and `failed_when` makes playbook
output accurate and prevents false positives in CI/CD pipelines.

### Timestamps Are Never Idempotent

A task that writes the current time **MUST NOT** be presented as idempotent.
`lineinfile` matches on the rendered line, so a fresh timestamp never matches
the previous one: the file grows by one line per run and the task reports
`changed` every time.

Record a value that is stable between deployments — a release version, a
commit SHA — or, when the timestamp itself is the point, add `regexp` so the
marker line is replaced in place and label the task as intentionally
changing.

Facts **MUST** be read through `ansible_facts` rather than the injected
top-level `ansible_date_time` variable. `INJECT_FACTS_AS_VARS` defaulting to
`True` is deprecated and the top-level names are removed in ansible-core
2.24.

## Security

### Secrets Management

#### Ansible Vault

All secrets **MUST** be encrypted with ansible-vault or SOPS. For simple use
cases, use ansible-vault[^11]:

```bash
# Create encrypted file
ansible-vault create vault/production.yml

# Edit encrypted file
ansible-vault edit vault/production.yml

# Encrypt existing file
ansible-vault encrypt group_vars/production.yml

# View encrypted file
ansible-vault view vault/production.yml

# Rekey (change password)
ansible-vault rekey vault/production.yml
```

```yaml
# vault/production.yml (encrypted)
---
database_password: "SuperSecretPassword123"
api_key: "sk-1234567890abcdef"
ssl_private_key: |
  -----BEGIN PRIVATE KEY-----
  ...
  -----END PRIVATE KEY-----
```

Vault password **MUST** be stored securely (never committed to git):

```bash
# Store in password manager, use --vault-password-file
ansible-playbook playbook.yml --vault-password-file ~/.ansible-vault-pass

# Or use environment variable
export ANSIBLE_VAULT_PASSWORD_FILE=~/.ansible-vault-pass

# Use multiple vault IDs for different environments
ansible-playbook playbook.yml \
  --vault-id prod@~/.vault-prod \
  --vault-id staging@~/.vault-staging
```

#### SOPS for GitOps

For GitOps workflows and multi-cloud environments, **SOPS** (Secrets
OPerationS)[^4] is **RECOMMENDED** over ansible-vault:

```bash
# macOS: Homebrew tracks the current release
brew install sops

# Linux: pin the version, select the architecture, verify the checksum.
# -f makes curl exit non-zero on an HTTP error instead of saving the
# error page as the binary.
SOPS_VERSION=3.13.3
SOPS_ARCH=amd64  # or arm64
SOPS_BASE="https://github.com/getsops/sops/releases/download/v${SOPS_VERSION}"

curl -fsSLO "${SOPS_BASE}/sops-v${SOPS_VERSION}.linux.${SOPS_ARCH}"
curl -fsSLO "${SOPS_BASE}/sops-v${SOPS_VERSION}.checksums.txt"
sha256sum --check --ignore-missing "sops-v${SOPS_VERSION}.checksums.txt"

sudo install -m 0755 "sops-v${SOPS_VERSION}.linux.${SOPS_ARCH}" /usr/local/bin/sops

# Optionally verify the Sigstore bundle published with the release
cosign verify-blob \
  --bundle "sops-v${SOPS_VERSION}.checksums.sigstore.json" \
  --certificate-identity-regexp 'https://github\.com/getsops/sops/.*' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  "sops-v${SOPS_VERSION}.checksums.txt"

# Install community.sops collection
ansible-galaxy collection install community.sops:2.4.0
```

Release artefacts **MUST** be pinned to a version and verified before
installation. The unversioned `releases/latest/download/sops-linux-amd64`
path returns HTTP 404: SOPS renamed its assets to include the version and
platform, so the old name no longer exists in any current release. Without
`-f`, `curl` cheerfully writes GitHub's 404 page to disk and `chmod +x` makes
it executable.

**Why SOPS over ansible-vault?**[^12]

- Supports multiple key management systems (AWS KMS, GCP KMS, Azure Key
  Vault, PGP, age)
- Encrypts only values, leaving keys visible for diff/grep
- Not tied to Ansible ecosystem (works with Terraform, Kubernetes, etc.)
- Better suited for multi-cloud DevSecOps pipelines
- Native GitOps support

**SOPS Configuration** (`.sops.yaml`):

Creation rules **MUST** encrypt every value except an explicit metadata
allow-list. Use `unencrypted_regex` to name the handful of keys that stay
readable, rather than `encrypted_regex` to name the keys that get protected.

```yaml
---
creation_rules:
  # Production secrets use AWS KMS
  - path_regex: vault/production\.ya?ml$
    kms: arn:aws:kms:us-east-1:123456789:key/abc-def-123
    unencrypted_regex: "^(app_name|environment|sops)$"

  # Staging secrets use PGP
  - path_regex: vault/staging\.ya?ml$
    pgp: "FBC7B9E2A4F9289AC0C1D4843D16CEE4A27381B4"
    unencrypted_regex: "^(app_name|environment|sops)$"

  # Development secrets use age
  - path_regex: vault/dev\.ya?ml$
    age: age1ql3z7hjy54pw3hyww5ayyfg7zqgvc7w3j2elw8zmrj2kg5sfn9aqmcac8p
    unencrypted_regex: "^(app_name|environment|sops)$"
```

**Why an allow-list rather than a deny-list?** `encrypted_regex` protects
only the key names it happens to enumerate, and it anchors on the whole key.
The obvious pattern `^(password|secret|key|token)$` leaves
`database_password`, `api_key`, and `ssl_private_key` — the three fields in
the vault example above — entirely in plaintext, because none of them is
*exactly* `password`, `secret`, `key`, or `token`. The file looks encrypted,
`sops` reports success, and the secrets are committed in the clear. An
allow-list fails the other way: a newly added field is encrypted by default,
and the worst outcome of a mistake is an unnecessarily encrypted piece of
metadata.

CI **MUST** assert the outcome rather than the exit status. After encrypting
a fixture that contains the documented key names, grep the ciphertext for
each known plaintext value and fail if any is found.

**Using SOPS with Ansible**:

The `community.sops.sops` vars plugin loads encrypted files from `group_vars/`
and `host_vars/` only, and only those whose extension is `.sops.yaml`,
`.sops.yml`, or `.sops.json`[^20]. It is not a general interception hook for
`vars_files`.

```bash
# Encrypt into a path the vars plugin actually reads
sops -e vault/production.yml \
  > inventories/production/group_vars/production/secrets.sops.yml
```

```yaml
# Variables from group_vars/production/secrets.sops.yml are decrypted
# automatically for every host in the production group
- name: Deploy with SOPS-encrypted secrets
  hosts: production

  tasks:
    - name: Configure database connection
      ansible.builtin.template:
        src: database.yml.j2
        dest: /etc/app/database.yml
        owner: root
        group: app
        mode: '0640'
      no_log: true
```

To decrypt a file at an arbitrary path, load it explicitly:

```yaml
- name: Load the SOPS-encrypted production secrets
  community.sops.load_vars:
    file: vault/production.enc.yml
    expressions: ignore
  no_log: true
```

**Why not `vars_files`?** `vars_files` bypasses the vars plugin entirely and
parses the file as ordinary YAML. The play still succeeds — but every value
is loaded as the literal ciphertext string, so `database_password` becomes
`ENC[AES256_GCM,data:...]` and that string is rendered straight into the
generated configuration file. The failure is silent at deploy time and only
surfaces when the application cannot authenticate.

**Why set `owner`, `group`, and `mode` on a rendered secret?** `no_log`
controls what Ansible prints; it has no effect on the filesystem. Without an
explicit `mode`, `template` creates the file under the remote user's umask —
typically `0644` — so a decrypted credential lands world-readable and any
local account on the host can read it. Log suppression is not access control.

**Enable SOPS vars plugin** (`ansible.cfg`):

```ini
[defaults]
vars_plugins_enabled = host_group_vars,community.sops.sops
```

### no_log Directive

Tasks handling sensitive data **MUST** use `no_log`:

```yaml
- name: Set database password
  ansible.builtin.user:
    name: postgres
    password: "{{ db_password | password_hash('sha512') }}"
  no_log: true  # Prevent password from appearing in logs

- name: Create API key
  ansible.builtin.uri:
    url: https://api.example.com/keys
    method: POST
    body_format: json
    body:
      name: "Production API Key"
      secret: "{{ api_secret }}"
  no_log: true
  register: api_result

- name: Debug without sensitive data
  ansible.builtin.debug:
    msg: "API key created: {{ api_result.json.id }}"
```

**Why no_log?** Prevents sensitive data from being logged to console, log
files, or CI/CD systems.

### become Best Practices

Use `become` judiciously - only when needed:

```yaml
# GOOD: become only when needed
- name: Configure application (non-root tasks)
  hosts: webservers
  become: false

  tasks:
    - name: Create app config in user home directory
      ansible.builtin.copy:
        src: app.conf
        dest: ~/.app/config

    - name: Install system package (requires root)
      ansible.builtin.apt:
        name: nginx
        state: present
      become: true  # Escalate only for this task

# Configure become user and method
- name: Run application as specific user
  ansible.builtin.command: /usr/local/bin/app-command
  become: true
  become_user: appuser
  become_method: sudo
```

```ini
# ansible.cfg - Security hardening
# Comments MUST be on their own line: Ansible's INI parser keeps an inline
# "# ..." as part of the value, so `host_key_checking = True  # comment`
# fails to parse as a boolean and silently evaluates to False.
[defaults]
# Verify SSH host keys
host_key_checking = True

[privilege_escalation]
# Don't become by default
become = False
# Use sudoers NOPASSWD
become_ask_pass = False
```

**Why does this matter more than it looks?** An inline hash comment on a
typed value is not a style problem. On an integer, Ansible raises
`Invalid value provided for 'integer'` and refuses to start — noisy, but
safe. On a boolean it is worse: the value `True      # Verify SSH host keys`
is not truthy, so `ansible-config dump` reports
`HOST_KEY_CHECKING = False`. The configuration loads, the playbook runs, and
host-key verification is off — the exact opposite of what the line says it
does. Assert the effective configuration with
`ansible-config dump --only-changed`, not merely that the file parses.

### File Permissions

Always set explicit file permissions:

```yaml
# GOOD: Explicit permissions
- name: Deploy application configuration file
  ansible.builtin.copy:
    src: app.conf
    dest: /etc/app/app.conf
    owner: root
    group: root
    mode: '0644'

- name: Deploy secret key file
  ansible.builtin.copy:
    src: secret.key
    dest: /etc/app/secret.key
    owner: appuser
    group: appuser
    mode: '0600'  # Only owner can read/write

- name: Create directory with sticky bit
  ansible.builtin.file:
    path: /var/tmp/shared
    state: directory
    mode: '1777'  # rwxrwxrwt (sticky bit)

# BAD: No permissions specified (relies on umask)
- name: Deploy file
  ansible.builtin.copy:
    src: app.conf
    dest: /etc/app/app.conf
```

### SSH Security

Configure secure SSH connections:

```ini
# ansible.cfg
[defaults]
host_key_checking = True
private_key_file = ~/.ssh/ansible_ed25519

[ssh_connection]
ssh_args = -o ControlMaster=auto -o ControlPersist=60s -o StrictHostKeyChecking=yes
pipelining = True
```

**Why?** Strict host key checking prevents man-in-the-middle attacks, and
SSH key authentication is more secure than password authentication.

## Testing

### Molecule for Role Testing

Roles **SHOULD** be tested with Molecule[^3]:

```bash
# Install Molecule with Docker driver
pipx install molecule molecule-plugins[docker]

# Or install as part of ansible-dev-tools
pipx install ansible-dev-tools

# Initialize molecule in role
cd roles/nginx
molecule init scenario

# Run full test sequence
molecule test

# Individual steps
molecule create    # Create test instance
molecule converge  # Run playbook
molecule verify    # Run verification tests
molecule destroy   # Cleanup
```

**Molecule Configuration** (`molecule/default/molecule.yml`):

```yaml
---
dependency:
  name: galaxy
  options:
    requirements-file: requirements.yml

driver:
  name: docker

platforms:
  - name: ubuntu-26-04
    image: geerlingguy/docker-ubuntu2604-ansible:latest
    pre_build_image: true
    privileged: true
    command: /lib/systemd/systemd
    volumes:
      - /sys/fs/cgroup:/sys/fs/cgroup:rw
    cgroupns_mode: host

  - name: ubuntu-24-04
    image: geerlingguy/docker-ubuntu2404-ansible:latest
    pre_build_image: true
    privileged: true
    command: /lib/systemd/systemd
    volumes:
      - /sys/fs/cgroup:/sys/fs/cgroup:rw
    cgroupns_mode: host

  - name: debian-13
    image: geerlingguy/docker-debian13-ansible:latest
    pre_build_image: true
    privileged: true
    command: /lib/systemd/systemd

  - name: debian-12
    image: geerlingguy/docker-debian12-ansible:latest
    pre_build_image: true
    privileged: true
    command: /lib/systemd/systemd

provisioner:
  name: ansible
  config_options:
    defaults:
      callbacks_enabled: ansible.posix.profile_tasks
  playbooks:
    converge: converge.yml
    verify: verify.yml

verifier:
  name: ansible
```

The Molecule platform list **MUST** match the `platforms` block in
`meta/main.yml`. A role that advertises Debian 13 but only tests Debian 12
is making a claim its test suite never checks.

**Converge Playbook** (`molecule/default/converge.yml`):

```yaml
---
- name: Converge
  hosts: all
  become: true

  roles:
    - role: nginx
      vars:
        nginx_port: 8080
        nginx_worker_processes: 2
```

**Verify Playbook** (`molecule/default/verify.yml`):

```yaml
---
- name: Verify
  hosts: all
  gather_facts: false

  tasks:
    - name: Verify nginx package is installed
      ansible.builtin.package:
        name: nginx
        state: present
      check_mode: true
      register: nginx_package
      failed_when: nginx_package.changed

    - name: Verify nginx service is running
      ansible.builtin.service:
        name: nginx
        state: started
      check_mode: true
      register: nginx_service
      failed_when: nginx_service.changed

    - name: Verify nginx responds to HTTP requests
      ansible.builtin.uri:
        url: http://localhost:8080
        status_code: 200
```

**Why Molecule?** Molecule provides a standardized testing framework for
Ansible roles, enabling test-driven development and CI integration across
multiple platforms.

### Testinfra for Verification

Molecule **MAY** use Testinfra[^13] for more complex verification:

```python
# molecule/default/tests/test_default.py
import os
import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']
).get_hosts('all')

def test_nginx_is_installed(host):
    nginx = host.package("nginx")
    assert nginx.is_installed

def test_nginx_running_and_enabled(host):
    nginx = host.service("nginx")
    assert nginx.is_running
    assert nginx.is_enabled

def test_nginx_config_file(host):
    config = host.file("/etc/nginx/nginx.conf")
    assert config.exists
    assert config.user == "root"
    assert config.group == "root"
    assert config.mode == 0o644

def test_nginx_listening_on_port(host):
    assert host.socket("tcp://0.0.0.0:8080").is_listening
```

Update `molecule.yml` to use Testinfra:

```yaml
verifier:
  name: testinfra
  options:
    v: 1
```

## Performance Optimization

### SSH Pipelining and Multiplexing

Enable SSH pipelining for faster execution:

```ini
# ansible.cfg
[ssh_connection]
pipelining = True
ssh_args = -o ControlMaster=auto -o ControlPersist=60s
```

**Why pipelining?** Reduces the number of SSH operations by sending multiple
commands over a single SSH connection, improving performance by 2-5x.

### Parallelism with Forks

Increase parallelism with forks[^14]:

```ini
# ansible.cfg
[defaults]
# Default is 5
forks = 20
```

```bash
# Or via command line
ansible-playbook -f 50 playbook.yml
```

**Why more forks?** Higher fork count enables Ansible to manage more hosts
simultaneously, drastically reducing playbook execution time for large
inventories.

### Fact Caching

Enable fact caching to avoid gathering facts repeatedly:

```ini
# ansible.cfg
[defaults]
gathering = smart
fact_caching = jsonfile
fact_caching_connection = .ansible_cache
# 24 hours, in seconds
fact_caching_timeout = 86400
```

Typed values **MUST** stand alone on their line. `fact_caching_timeout` is an
integer, and Ansible's INI parser does not strip a trailing `# 24 hours`, so
`ansible-config dump` aborts with
`Invalid value provided for 'integer': '86400  # 24 hours'` and no playbook
runs until the comment is moved.

**Alternative: Redis fact caching**:

```ini
[defaults]
gathering = smart
fact_caching = community.general.redis
fact_caching_connection = localhost:6379:0
fact_caching_timeout = 86400
```

### Async Tasks for Long-Running Operations

Long-running tasks **SHOULD** use async execution:

```yaml
- name: Run long database backup
  ansible.builtin.command: /usr/bin/backup-database.sh
  async: 3600  # Maximum runtime (1 hour)
  poll: 0      # Fire and forget
  register: backup_job

# Continue with other tasks...

# A launch task with no loop registers a single job record, so poll it
# through backup_job.ansible_job_id
- name: Check backup completion
  ansible.builtin.async_status:
    jid: "{{ backup_job.ansible_job_id }}"
  register: job_result
  until: job_result.finished
  retries: 360
  delay: 10

# Several jobs per host: the launch task MUST loop, which is what gives the
# registered result a .results list to poll
- name: Deploy each component in parallel
  ansible.builtin.command: "/usr/local/bin/deploy.sh {{ item }}"
  async: 600
  poll: 0
  register: deploy_jobs
  loop: "{{ deploy_components }}"

- name: Wait for all deployments to complete
  ansible.builtin.async_status:
    jid: "{{ item.ansible_job_id }}"
  register: deploy_results
  until: deploy_results.finished
  retries: 60
  delay: 10
  loop: "{{ deploy_jobs.results }}"
  loop_control:
    label: "{{ item.item }}"
```

**Why does the launch task need the loop?** `register` stores one result per
host, not one per host in a list. Without a loop on the launch task,
`deploy_jobs` is a plain dictionary holding a single `ansible_job_id`, and
referencing `deploy_jobs.results` fails the play with
`object of type 'dict' has no attribute 'results'`. Ansible already runs the
launch task across hosts in parallel according to `forks`; the loop is only
needed when one host launches several jobs.

### Mitogen (Optional Accelerator)

For maximum performance, **MAY** use Mitogen[^15]:

```bash
# Install
pip install mitogen
```

```ini
# ansible.cfg
[defaults]
strategy_plugins = /path/to/mitogen/ansible_mitogen/plugins/strategy
strategy = mitogen_linear

[ssh_connection]
pipelining = True
```

**Why Mitogen?** Mitogen reduces playbook execution time by 1.25x to 7x
through optimized SSH connection pooling and reduced Python interpreter
startup overhead.

### Free Strategy for Independent Hosts

For independent host configurations, use the `free` strategy:

```yaml
- name: Configure hosts independently
  hosts: all
  strategy: free  # Don't wait for all hosts to complete each task
  gather_facts: true

  tasks:
    - name: Install packages
      ansible.builtin.apt:
        name: nginx
        state: present
```

**Why free strategy?** Allows faster hosts to proceed without waiting for
slower ones, reducing overall playbook execution time.

### Profiling and Optimization

Enable profiling to identify slow tasks:

```ini
# ansible.cfg
[defaults]
callbacks_enabled = profile_tasks, timer
```

```bash
# Run playbook with profiling
ansible-playbook playbooks/webservers.yml

# Example output:
# PLAY RECAP *********************************************************************
# web01 : ok=15 changed=3 unreachable=0 failed=0 skipped=2 rescued=0 ignored=0
#
# Sunday 07 December 2025  14:32:18 -0800 (0:00:02.345)       0:01:23.456 ******
# ===============================================================================
# Install nginx package ------------------------------------------------- 15.234s
# Deploy nginx configuration -------------------------------------------- 8.123s
# Update apt cache ------------------------------------------------------ 5.678s
```

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/ansible-lint.yml
name: Ansible Lint

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    name: Lint Ansible playbooks and roles
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install ansible-lint
        run: |
          pip install ansible-dev-tools

      - name: Run ansible-lint
        run: |
          ansible-lint --profile=production

      - name: Run yamllint
        run: |
          yamllint .

  molecule:
    name: Test roles with Molecule
    runs-on: ubuntu-latest
    strategy:
      matrix:
        role: [nginx, postgresql, common]

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install Molecule and dependencies
        run: |
          pip install ansible-dev-tools molecule-plugins[docker]

      - name: Run Molecule tests
        run: |
          cd roles/${{ matrix.role }}
          molecule test
```

## See Also

- [YAML Guide](../docs/markdown.md) - YAML syntax and best practices
- [Shell Guide](../languages/shell.md) - Shell scripting for Ansible modules
- [Python Guide](../languages/python.md) - Python for custom Ansible modules
- [Testing Guide](../process/testing.md) - General testing principles
- [CI/CD Guide](../process/ci.md) - Integrating Ansible in pipelines

## References

[^1]: [ansible-lint](https://ansible.readthedocs.io/projects/lint/) - Best practices checker for Ansible. Identifies common mistakes and enforces style guidelines. [GitHub](https://github.com/ansible/ansible-lint)

[^2]: [yamllint](https://yamllint.readthedocs.io/) - Linter for YAML files. Ensures consistent YAML formatting across playbooks and roles.

[^3]: [Molecule](https://molecule.readthedocs.io/) - Testing framework for Ansible roles. Enables test-driven development and CI integration. [GitHub](https://github.com/ansible/molecule)

[^4]: [SOPS](https://github.com/getsops/sops) - Secrets OPerationS by Mozilla/CNCF. Editor of encrypted files supporting YAML, JSON, ENV, INI. [Ansible SOPS Guide](https://docs.ansible.com/ansible/latest/collections/community/sops/docsite/guide.html)

[^5]: [Ansible Core 2.18 Porting Guide](https://docs.ansible.com/ansible/latest/porting_guides/porting_guide_core_2.18.html) - Python 3.11+ required for control node, Python 3.8+ for managed nodes

[^6]: [Ansible Dynamic Inventory](https://docs.ansible.com/ansible/latest/inventory_guide/intro_dynamic_inventory.html) - Automatically generated inventory from external sources (cloud providers, CMDBs)

[^7]: [Fully Qualified Collection Names (FQCN)](https://docs.ansible.com/ansible/latest/collections_guide/index.html) - Using complete module names like `ansible.builtin.copy` instead of `copy`. Required in Ansible 2.10+

[^8]: [Ansible Role Structure](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_reuse_roles.html) - Standard directory layout for roles

[^9]: [Variable Precedence](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_variables.html#variable-precedence-where-should-i-put-a-variable) - Order in which Ansible evaluates variables

[^10]: [Role Argument Specs](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_reuse_roles.html#role-argument-validation) - Define and validate role input with argument specifications

[^11]: [ansible-vault](https://docs.ansible.com/ansible/latest/vault_guide/index.html) - Tool for encrypting sensitive data in Ansible. Supports file and variable encryption

[^12]: [SOPS vs Ansible Vault Comparison](https://blog.gitguardian.com/a-comprehensive-guide-to-sops/) - SOPS supports multiple KMS, encrypts only values (not keys), and works across ecosystems

[^13]: [Testinfra](https://testinfra.readthedocs.io/) - Python library for testing infrastructure. Integrates with Molecule for comprehensive role testing

[^14]: [Ansible Forks](https://docs.ansible.com/ansible/latest/reference_appendices/config.html#default-forks) - Number of parallel processes Ansible uses. Higher values enable faster execution

[^15]: [Mitogen for Ansible](https://mitogen.networkgenomics.com/ansible_detailed.html) - Performance optimization that dramatically speeds up playbook execution through connection pooling. [GitHub](https://github.com/mitogen-hq/mitogen)

[^16]: [Organizing host and group variables](https://docs.ansible.com/ansible/latest/inventory_guide/intro_inventory.html#organizing-host-and-group-variables) - Ansible loads `group_vars/` and `host_vars/` from the directory containing the inventory file or the directory containing the playbook

[^17]: [ansible.builtin.service module](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/service_module.html) - `started`/`stopped` are idempotent and run no command unless necessary; `restarted` always bounces the service

[^18]: [Debian releases](https://www.debian.org/releases/) and [Ubuntu release cycle](https://ubuntu.com/about/release-cycle) - Debian 11 (bullseye) LTS ended 2026-08-31; Ubuntu 20.04 standard support ended 2025-05-31 and continues under Ubuntu Pro ESM only

[^19]: [PostgreSQL Versioning Policy](https://www.postgresql.org/support/versioning/) - Each major is supported for five years; 16 is supported until 2028-11-09 and 18 is current. Always run the current minor release of the chosen major

[^20]: [community.sops.sops vars plugin](https://docs.ansible.com/ansible/latest/collections/community/sops/sops_vars.html) - Loads encrypted files from `group_vars/` and `host_vars/`, restricted by default to `.sops.yaml`, `.sops.yml`, and `.sops.json` extensions
