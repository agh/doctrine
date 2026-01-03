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
| Syntax check | ansible-playbook | `ansible-playbook --syntax-check` |
| Dry run | ansible-playbook | `ansible-playbook --check playbook.yml` |
| List tasks | ansible-playbook | `ansible-playbook --list-tasks playbook.yml` |
| Vault encrypt | ansible-vault | `ansible-vault encrypt vars/secrets.yml` |
| SOPS encrypt | sops[^4] | `sops -e vars/secrets.yml` |
| Galaxy install | ansible-galaxy | `ansible-galaxy collection install` |

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
│   │   └── group_vars/
│   │       ├── all.yml
│   │       └── webservers.yml
│   └── staging/
│       ├── hosts.yml
│       └── group_vars/
│           └── all.yml
├── playbooks/
│   ├── site.yml                # Master playbook
│   ├── webservers.yml          # Server-specific playbooks
│   └── deploy.yml
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
├── group_vars/
│   ├── all.yml                 # Global variables
│   └── production.yml
├── host_vars/
│   └── web01.yml               # Host-specific variables
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
- Centralized variable management (`group_vars/`, `host_vars/`)
- Logical grouping of playbooks by purpose
- Integrated testing with Molecule
- CI/CD ready with GitHub Actions

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
# https://ansible-lint.readthedocs.io/

# Require minimum ansible-core version
min_ansible_version: "2.18"

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

# Task name prefix rules
task_name_prefix:
  add_at_start: true

# Offline mode (don't check Galaxy)
offline: false
```

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
          postgresql_version: "16"
      vars:
        postgresql_max_connections: 100

    # Group of groups
    production:
      children:
        webservers
        databases
      vars:
        environment: production
```

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

**Supported dynamic inventory plugins**[^6]:

- `amazon.aws.aws_ec2` - AWS EC2
- `azure.azcollection.azure_rm` - Azure
- `google.cloud.gcp_compute` - Google Cloud
- `openstack.cloud.openstack` - OpenStack
- `community.vmware.vmware_vm_inventory` - VMware

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
        prod_webservers
        prod_databases
    staging:
      children:
        staging_webservers

    # By function
    webservers:
      children:
        prod_webservers
        staging_webservers

    # By location
    us_east:
      children:
        us_east_webservers
        us_east_databases
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

    - name: Restart application with previous version
      ansible.builtin.service:
        name: myapp
        state: started

    - name: Fail deployment
      ansible.builtin.fail:
        msg: "Deployment failed, rolled back to previous version"

  always:
    - name: Clean up temporary files
      ansible.builtin.file:
        path: /tmp/deploy-*
        state: absent
```

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
        - focal
        - jammy
    - name: Debian
      versions:
        - bullseye
        - bookworm
  galaxy_tags:
    - web
    - nginx
```

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

# GOOD: Idempotent version using lineinfile
- name: Record deployment
  ansible.builtin.lineinfile:
    path: /var/log/deploy.log
    line: "Deployed {{ ansible_date_time.iso8601 }}"
    create: true

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
# Install SOPS
brew install sops  # macOS
# or
curl -LO https://github.com/getsops/sops/releases/latest/download/sops-linux-amd64
sudo mv sops-linux-amd64 /usr/local/bin/sops
sudo chmod +x /usr/local/bin/sops

# Install community.sops collection
ansible-galaxy collection install community.sops
```

**Why SOPS over ansible-vault?**[^12]

- Supports multiple key management systems (AWS KMS, GCP KMS, Azure Key
  Vault, PGP, age)
- Encrypts only values, leaving keys visible for diff/grep
- Not tied to Ansible ecosystem (works with Terraform, Kubernetes, etc.)
- Better suited for multi-cloud DevSecOps pipelines
- Native GitOps support

**SOPS Configuration** (`.sops.yaml`):

```yaml
---
creation_rules:
  # Production secrets use AWS KMS
  - path_regex: vault/production\.yml$
    kms: arn:aws:kms:us-east-1:123456789:key/abc-def-123
    encrypted_regex: "^(password|secret|key|token)$"

  # Staging secrets use PGP
  - path_regex: vault/staging\.yml$
    pgp: "FBC7B9E2A4F9289AC0C1D4843D16CEE4A27381B4"

  # Development secrets use age
  - path_regex: vault/dev\.yml$
    age: age1ql3z7hjy54pw3hyww5ayyfg7zqgvc7w3j2elw8zmrj2kg5sfn9aqmcac8p
```

**Using SOPS with Ansible**:

```yaml
# Encrypt secrets
sops -e vault/production.yml > vault/production.enc.yml

# Use in playbook with community.sops.sops vars plugin
- name: Deploy with SOPS-encrypted secrets
  hosts: production
  vars_files:
    - vault/production.enc.yml  # Automatically decrypted by vars plugin

  tasks:
    - name: Configure database connection
      ansible.builtin.template:
        src: database.yml.j2
        dest: /etc/app/database.yml
      no_log: true
```

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
[defaults]
host_key_checking = True      # Verify SSH host keys

[privilege_escalation]
become = False                # Don't become by default
become_ask_pass = False       # Use sudoers NOPASSWD
```

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
  - name: ubuntu-22-04
    image: geerlingguy/docker-ubuntu2204-ansible:latest
    pre_build_image: true
    privileged: true
    command: /lib/systemd/systemd
    volumes:
      - /sys/fs/cgroup:/sys/fs/cgroup:rw
    cgroupns_mode: host

  - name: debian-12
    image: geerlingguy/docker-debian12-ansible:latest
    pre_build_image: true
    privileged: true
    command: /lib/systemd/systemd

provisioner:
  name: ansible
  config_options:
    defaults:
      callbacks_enabled: profile_tasks
  playbooks:
    converge: converge.yml
    verify: verify.yml

verifier:
  name: ansible
```

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
forks = 20  # Default is 5
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
fact_caching_timeout = 86400  # 24 hours
```

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

- name: Check backup completion
  ansible.builtin.async_status:
    jid: "{{ backup_job.ansible_job_id }}"
  register: job_result
  until: job_result.finished
  retries: 360
  delay: 10

# Parallel async tasks
- name: Deploy to all servers in parallel
  ansible.builtin.command: /usr/local/bin/deploy.sh
  async: 600
  poll: 0
  register: deploy_jobs

- name: Wait for all deployments to complete
  ansible.builtin.async_status:
    jid: "{{ item.ansible_job_id }}"
  register: deploy_results
  until: deploy_results.finished
  retries: 60
  delay: 10
  loop: "{{ deploy_jobs.results }}"
```

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
