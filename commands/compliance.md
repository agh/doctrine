# /compliance Command

Assess code and infrastructure against regulatory frameworks.

## Usage

```text
/compliance <framework> [scope]
```

## Frameworks

| Framework | Alias | Description |
| --------- | ----- | ----------- |
| `gdpr` | `privacy` | EU General Data Protection Regulation |
| `hipaa` | `healthcare` | US Health Insurance Portability and Accountability |
| `pci-dss` | `pci` | Payment Card Industry Data Security Standard |
| `soc2` | `soc` | Service Organization Control 2 |
| `iso27001` | `iso` | ISO 27001 Information Security |
| `nist` | `nist-csf` | NIST Cybersecurity Framework |
| `all` | - | Assess against all applicable frameworks |

## Examples

```bash
# GDPR compliance check
/compliance gdpr

# PCI-DSS for payment code
/compliance pci src/payments/

# SOC 2 audit preparation
/compliance soc2 --audit-prep

# All applicable frameworks
/compliance all
```

## Options

| Option | Description |
| ------ | ----------- |
| `--audit-prep` | Generate audit evidence checklist |
| `--gaps-only` | Show only compliance gaps |
| `--evidence` | Include evidence locations |

## Behavior

1. **Compliance Assessor** identifies applicable controls
2. Maps code/infrastructure to requirements
3. Assesses implementation against each control
4. Identifies gaps and evidence needs
5. Generates compliance matrix

## Output

```markdown
# Compliance Assessment: [Framework]

## Applicability
[Why this framework applies]

## Compliance Matrix

| Control | Requirement | Status | Evidence |
| ------- | ----------- | ------ | -------- |
| [ID] | [Description] | ✅/⚠️/❌ | [Link] |

## Gap Analysis
[Detailed gaps with remediation]

## Evidence Checklist
[For audit preparation]

## Recommendations
[Prioritized actions]
```

## Implementation

```markdown
You are the Compliance Assessor. Assess this code for $ARGUMENTS compliance:

$SCOPE

For each applicable control:
1. Check if requirement is implemented
2. Identify evidence of implementation
3. Note any gaps

Output a compliance matrix with gap analysis.
```

## Related Commands

- `/security` - Security review
- `/threat-model` - Threat modeling
