# /security Command

The **single entry point** for all security analysis. Routes automatically to specialist agents.

## Quick Start

```bash
/security                    # Analyze staged changes
/security quick              # Fast scan (Haiku, ~5 seconds)
/security full               # Comprehensive assessment (all agents)
```

## Usage

```text
/security [mode] [scope] [options]
```

## Modes

| Mode | Speed | Model | Use Case |
| ---- | ----- | ----- | -------- |
| (default) | Medium | Sonnet | Staged changes, balanced analysis |
| `quick` | Fast | Haiku | Rapid iteration, pre-commit check |
| `full` | Slow | Opus | Pre-merge gate, comprehensive review |

## Domains

Route to specialized analysis with domain keywords:

```bash
# Core Security
/security code <path>        # Code security review (OWASP, CWE)
/security deps               # Dependency audit + SLSA assessment
/security infra <path>       # Infrastructure/IaC security

# Specialized Analysis
/security threat <feature>   # Threat model a design/feature
/security network            # Zero trust, segmentation, DNS
/security detect             # Detection engineering, fingerprinting
/security emerging           # AI/ML, quantum, confidential computing

# Offensive/Defensive
/security redteam <target>   # Attack path analysis
/security siem               # SIEM/SOAR integration guidance

# Compliance
/security compliance <framework>  # GDPR, HIPAA, PCI-DSS, SOC 2
```

## Examples

```bash
# Quick pre-commit check
/security quick

# Full review before merge
/security full src/

# Specific file security review
/security code src/api/auth.ts

# Dependency audit with SLSA assessment
/security deps

# Threat model new payment feature
/security threat "payment processing integration"

# Network security assessment
/security network zerotrust

# AI/ML security for LLM integration
/security emerging ai

# Red team attack path analysis
/security redteam "external attacker → domain admin"

# Detection coverage assessment
/security detect coverage

# Compliance gap analysis
/security compliance gdpr
```

## Auto-Routing

When run without a domain, the Security Architect analyzes changes and routes:

| Change Type | Auto-Routed To |
| ----------- | -------------- |
| `.ts`, `.js`, `.py`, etc. | Code Security Reviewer |
| `package.json`, `go.mod`, etc. | Supply Chain Auditor |
| `.tf`, `k8s.yaml`, `Dockerfile` | Infrastructure Security |
| `*auth*`, `*crypto*`, `*secret*` | Code Reviewer (elevated) |
| Design docs, PRDs | Threat Modeler |

## Options

| Option | Description |
| ------ | ----------- |
| `--format json` | Output as JSON |
| `--severity <level>` | Filter minimum severity (critical/high/medium/low) |
| `--fix` | Auto-generate fixes with Remediation Generator |
| `--explain` | Include educational content for findings |

## Output Format

All findings include:

- **Severity**: RFC 2119 keywords (MUST FIX, MUST, SHOULD, MAY)
- **Standards**: OWASP Top 10, CWE IDs, MITRE ATT&CK
- **Location**: `file:line` reference
- **Confidence**: 0.0-1.0 score
- **Fix**: Suggested remediation

## Agent Routing

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                         /security                                        │
│                    Security Architect                                    │
│                        (Opus 4.5)                                        │
├─────────────────────────────────────────────────────────────────────────┤
│                              │                                           │
│     ┌────────────────────────┼────────────────────────┐                 │
│     │                        │                        │                 │
│     ▼                        ▼                        ▼                 │
│ ┌─────────┐            ┌─────────┐            ┌─────────┐              │
│ │  Code   │            │ Supply  │            │ Infra   │              │
│ │ Review  │            │ Chain   │            │Security │              │
│ │(Sonnet) │            │(Haiku+) │            │(Sonnet) │              │
│ └─────────┘            └─────────┘            └─────────┘              │
│                                                                          │
│ ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│ │ Threat  │  │ Network │  │Detection│  │Emerging │  │Red Team │       │
│ │ Model   │  │Security │  │Engineer │  │  Tech   │  │Operator │       │
│ │(Sonnet) │  │(Sonnet) │  │(Sonnet) │  │(Sonnet) │  │ (Opus)  │       │
│ └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘       │
│                                                                          │
│ ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐                     │
│ │SIEM/SOAR│  │Compliance│  │Remediate│  │ Report  │                     │
│ │(Sonnet) │  │(Sonnet) │  │(Sonnet) │  │ (Haiku) │                     │
│ └─────────┘  └─────────┘  └─────────┘  └─────────┘                     │
└─────────────────────────────────────────────────────────────────────────┘
```

## Cost Optimization

| Mode | Typical Cost | Use When |
| ---- | ------------ | -------- |
| `quick` | ~$0.02 | Every commit, rapid iteration |
| (default) | ~$0.20 | PR review, focused analysis |
| `full` | ~$1.00 | Pre-merge, release review |

## Related Commands

| Command | Shortcut | Description |
| ------- | -------- | ----------- |
| `/threat-model` | `/security threat` | Design-time threat analysis |
| `/compliance` | `/security compliance` | Regulatory compliance |
| `/incident` | - | Incident response mode |
| `/security-fix` | `/security --fix` | Generate remediation code |

## Implementation

```markdown
You are the Security Architect, coordinating the Doctrine Security Agent Family.

Analyze the scope provided and:

1. **Assess** - Identify what types of security analysis are needed
2. **Route** - Delegate to appropriate specialist agents
3. **Synthesize** - Combine findings into unified report
4. **Prioritize** - Create remediation roadmap by severity

Specialist agents available:
- Code Security Reviewer: OWASP/CWE code analysis
- Supply Chain Auditor: Dependencies, CVEs, SLSA, licenses
- Infrastructure Security: IaC, cloud, containers
- Threat Modeler: STRIDE, attack trees, DFDs
- Network Security: Zero trust, segmentation, DNS
- Detection Engineering: Fingerprinting, behavioral detection, hunting
- Emerging Tech Security: AI/ML, quantum, confidential computing
- Red Team Operator: Attack paths, adversary simulation
- SIEM/SOAR Integration: Detection rules, playbooks, SOC metrics
- Compliance Assessor: GDPR, HIPAA, PCI-DSS, SOC 2, ISO 27001
- Remediation Generator: Auto-fix with tests
- Security Reporter: Multi-audience reports

$ARGUMENTS
```
