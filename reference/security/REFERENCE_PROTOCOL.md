# Security Reference Loading Protocol

> Standard pattern for security agents to load and use vendored reference data

## The Problem

Security agents historically duplicated reference data (OWASP, CWE, etc.)
directly in their prompts. This causes:

1. **Data staleness** - Agent prompts have 2021/2024 versions while JSON has 2025
2. **Maintenance burden** - Updates must be made in multiple places
3. **Inconsistency** - Different agents may have different versions
4. **Wasted context** - Large tables consume prompt tokens

## The Solution: DRY References

Agents **MUST** reference vendored JSON files instead of duplicating data.

### Pattern 1: Explicit File Loading

Instead of hardcoding:

```markdown
### OWASP Top 10 (2021)
| ID | Category |
| A01 | Broken Access Control |
...
```

Reference the vendored data:

```markdown
### Reference Data

For vulnerability classification, load and use:

- **OWASP Top 10**: `reference/security/owasp/top10-web-2025.json`
- **CWE Top 25**: `reference/security/cwe/cwe-top-25-2025.json`
- **MITRE ATT&CK**: `reference/security/mitre/attack/techniques-summary.json`

When analyzing findings:
1. Read the relevant JSON file
2. Use `detection_patterns` for pattern matching
3. Use `mitigations` for fix recommendations
4. Reference `cross_references` for related standards
```

### Pattern 2: Manifest-Driven Discovery

Agents should check `manifest.json` for current versions:

```markdown
### Reference Loading

1. First, read `reference/security/manifest.json` to get:
   - Current versions of all reference data
   - File paths for each reference type
   - Last update timestamps

2. Load specific references based on task:
   - Code review → CWE, OWASP Web
   - Threat modeling → CAPEC, ATT&CK, D3FEND
   - Compliance → `compliance/frameworks.json`
   - Supply chain → SLSA, OpenSSF Scorecard, SBOM
```

### Pattern 3: Cross-Reference Navigation

Each JSON file has `cross_references` for related data:

```markdown
### Cross-Reference Usage

When a finding maps to CWE-89 (SQL Injection):
1. Lookup CWE-89 in `cwe/cwe-top-25-2025.json`
2. Follow `owasp_mapping` to get OWASP category
3. Use `mitigations` for fix recommendations
4. Reference `capec_patterns` for attack context
```

## Reference Matrix by Agent Type

| Agent | Primary References | Supporting References |
| ----- | ------------------ | --------------------- |
| Code Security Reviewer | `cwe/cwe-top-25-2025.json` | `owasp/top10-web-2025.json` |
| Threat Modeler | `mitre/capec/capec-summary.json` | `mitre/attack/techniques-summary.json`, `mitre/d3fend/d3fend-summary.json` |
| Compliance Assessor | `compliance/frameworks.json` | `compliance/control-mappings.json`, `compliance/technical-requirements.json` |
| Supply Chain Auditor | `slsa/slsa-levels.json` | `openssf/scorecard.json`, `sbom/sbom-formats.json` |
| Infrastructure Analyst | `containers/container-security.json` | `cis/controls-v8.json` |
| Incident Response | `mitre/attack/techniques-summary.json` | `mitre/d3fend/d3fend-summary.json`, `kev/known-exploited-vulnerabilities.json` |
| Vulnerability Prioritizer | `kev/known-exploited-vulnerabilities.json` | `epss/exploit-prediction.json`, `exploits/exploit-availability.json` |

## Agent Prompt Template

Replace hardcoded tables with this pattern:

```markdown
## Reference Data Loading

**CRITICAL**: Do NOT rely on training data for security standards. Always load current vendored references.

### Required References for This Agent

Load these files at the start of each task:

1. **Primary Reference**: `reference/security/[path]`
   - Use for: [specific purpose]

2. **Supporting References**: `reference/security/[paths]`
   - Use for: [specific purposes]

### Version Verification

Before using any reference:
1. Check `reference/security/manifest.json` for `last_updated`
2. If references are >90 days old, note this in findings
3. Use `staleness_policy` to assess risk of outdated data

### Lookup Patterns

Each JSON file includes:
- `detection_patterns`: Regex/patterns for finding issues
- `mitigations`: Recommended fixes
- `cross_references`: Related standards
- `agent_usage`: Task-specific hints
```

## Migration Checklist

For each security agent:

- [ ] Remove all hardcoded OWASP/CWE/MITRE tables
- [ ] Add "Reference Data Loading" section
- [ ] Specify which JSON files to load
- [ ] Add version verification step
- [ ] Update output format to cite JSON source versions
- [ ] Test that agent reads files correctly

## Benefits

1. **Single Source of Truth**: Update JSON once, all agents get current data
2. **Reduced Prompt Size**: No more 100-line tables in prompts
3. **Version Awareness**: Agents know which version they're using
4. **Auditability**: Findings cite specific reference versions
5. **Automated Updates**: CI/CD updates JSON, agents automatically current
