# /system Command

Comprehensive infrastructure assessment using the Doctrine System Agent Family.

## Usage

```text
/system [target] [subcommand] [options]
```

## Subcommands

| Subcommand | Agent | Model | Description |
| ---------- | ----- | ----- | ----------- |
| (none) | System Architect | Opus | Full infrastructure assessment |
| `docker` | Docker Reviewer | Sonnet | Container/Compose review |
| `ansible` | Ansible Reviewer | Sonnet | Playbook/role review |
| `linux` | Linux Reviewer | Sonnet | OS configuration review |
| `verify` | Verify Build | Sonnet | CI/CD validation |

## Examples

```text
/system                               # Full assessment of infrastructure
/system stacks/                       # Full assessment of stacks directory
/system docker stacks/platform/       # Docker review of platform stack
/system ansible roles/nginx/          # Ansible role review
/system linux /etc/ssh/               # Linux SSH config review
/system verify                        # Verify build and tests pass
```

## Behavior

1. **Target selection**:
   - If path provided: analyzes that file or directory
   - If no path: analyzes current directory for infrastructure files

2. **Agent selection**:
   - No subcommand: System Architect (Opus) coordinates full assessment
   - With subcommand: Routes directly to specialist agent

3. **Output**: Findings grouped by severity with remediation steps

## Review Modes

| Mode | Command | Focus | Cost |
| ---- | ------- | ----- | ---- |
| **Docker** | `/system docker` | Container security | ~$0.25 |
| **Ansible** | `/system ansible` | Playbook best practices | ~$0.25 |
| **Linux** | `/system linux` | OS hardening | ~$0.25 |
| **Full** | `/system` | All specialists, cross-system | ~$1.00 |

## Implementation

    Analyze the infrastructure at: $ARGUMENTS

    ## Mode Selection

    Based on subcommand:
    - (none) → Full assessment: Use System Architect to coordinate all
      relevant specialists
    - `docker` → Use Docker Reviewer
    - `ansible` → Use Ansible Reviewer
    - `linux` → Use Linux Reviewer
    - `verify` → Use Verify Build

    ## Output Format

    Start with metrics:

    | Metric | Value |
    | ------ | ----- |
    | **Review Effort** | [1-5] |
    | **Risk Level** | Low / Medium / High / Critical |
    | **Environment** | Development / Staging / Production |

    Then findings by severity:

    ### Critical (must fix before deployment)

    - [ ] **[Category]**: [description] (`file:line`)

      **Current**: [problematic config]

      **Recommended**: [fixed config]

      **Why**: [explanation with Doctrine reference]

    ### Warning (should fix)

    ### Suggestion (consider)

    ### Positive Observations

    ### Cross-System Observations (full assessment only)

    [Patterns across Docker, Ansible, Linux]

    ### Summary

    [1-2 sentence overall assessment]

## See Also

- [System Agent Family](../../guides/ai/system-agents.md) — Architecture overview
- [System Architect](../agents/system/architect.md) — Coordinator specification
- [Docker Reviewer](../agents/system/docker.md) — Container security
- [Ansible Reviewer](../agents/system/ansible.md) — Playbook review
- [Linux Reviewer](../agents/system/linux.md) — OS hardening
- [Verify Build](../agents/system/verify.md) — CI/CD validation
