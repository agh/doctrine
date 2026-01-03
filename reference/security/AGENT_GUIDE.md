# Security Reference Agent Integration Guide

> How to effectively use vendored security references in AI agent pipelines

## Overview

This directory contains vendored security reference data designed for
**offline agent operation**. These references enable security-focused agents to
make informed decisions without requiring live API calls during execution.

## Quick Reference: When to Use What

| Task | Primary Reference | Supporting References |
| ---- | ----------------- | --------------------- |
| Code vulnerability review | `cwe/cwe-top-25-2025.json` | OWASP Top 10, CAPEC |
| Threat modeling | `mitre/capec/capec-summary.json` | ATT&CK, D3FEND |
| Incident response | `mitre/attack/techniques-summary.json` | D3FEND, KEV |
| Compliance assessment | `compliance/frameworks.json` | `compliance/technical-requirements.json` |
| Supply chain security | `slsa/slsa-levels.json` | OpenSSF Scorecard, SBOM formats |
| API security review | `owasp/top10-api-2023.json` | ASVS, CWE |
| Mobile app security | `owasp/top10-mobile-2024.json` | ASVS |
| LLM/AI security | `owasp/top10-llm-2025.json` | ATLAS |
| Defensive recommendations | `mitre/d3fend/d3fend-summary.json` | CIS Controls |
| Vulnerability prioritization | `epss/exploit-prediction.json` | KEV, CVE |

## Reference Relationships

```text
┌─────────────────────────────────────────────────────────────────┐
│                    OFFENSIVE KNOWLEDGE                          │
├─────────────────────────────────────────────────────────────────┤
│  ATT&CK ──────────────────┐                                     │
│  (Adversary TTPs)         │                                     │
│                           ▼                                     │
│  CAPEC ──────────────► CWE ◄────── OWASP Top 10s               │
│  (Attack Patterns)     (Weaknesses)    (Risk Categories)        │
│                           │                                     │
├───────────────────────────┼─────────────────────────────────────┤
│                    DEFENSIVE KNOWLEDGE                          │
├───────────────────────────┼─────────────────────────────────────┤
│                           ▼                                     │
│  D3FEND ◄─────────── Countermeasures                           │
│  (Defensive Techniques)   │                                     │
│                           ▼                                     │
│  CIS Controls ◄────── Control Mappings ──────► NIST 800-53     │
│                           │                                     │
│                           ▼                                     │
│  Compliance Frameworks (SOC 2, PCI-DSS, ISO 27001, etc.)       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    SUPPLY CHAIN SECURITY                        │
├─────────────────────────────────────────────────────────────────┤
│  SLSA Levels ─────► Build Integrity                             │
│       │                                                         │
│       ▼                                                         │
│  OpenSSF Scorecard ─────► Project Health                        │
│       │                                                         │
│       ▼                                                         │
│  SBOM Formats (CycloneDX, SPDX) ─────► Dependency Transparency │
└─────────────────────────────────────────────────────────────────┘
```

## Agent Integration Patterns

### Pattern 1: Security Code Review Agent

```python
# Pseudocode for a security code review agent
def security_review(code_file):
    # 1. Load relevant references
    cwe_top25 = load_json("reference/security/cwe/cwe-top-25-2025.json")
    owasp_web = load_json("reference/security/owasp/top10-web-2025.json")

    # 2. Get language-specific detection patterns
    language = detect_language(code_file)
    patterns = get_patterns_for_language(cwe_top25, language)

    # 3. Scan code against patterns
    findings = []
    for cwe in patterns:
        if matches_pattern(code_file, cwe["detection_patterns"]):
            finding = {
                "cwe_id": cwe["id"],
                "severity": cwe["severity"],
                "mitigation": cwe["mitigations"],
                "owasp_category": map_to_owasp(cwe["id"], owasp_web)
            }
            findings.append(finding)

    return findings
```

### Pattern 2: Threat Modeling Agent

```python
def threat_model(system_description):
    # 1. Load attack knowledge
    attack = load_json("reference/security/mitre/attack/techniques-summary.json")
    capec = load_json("reference/security/mitre/capec/capec-summary.json")

    # 2. Identify applicable attack surfaces
    surfaces = identify_attack_surfaces(system_description)

    # 3. Map surfaces to attack patterns
    threats = []
    for surface in surfaces:
        applicable_patterns = filter_patterns(capec, surface)
        for pattern in applicable_patterns:
            threat = {
                "attack_pattern": pattern["id"],
                "attack_name": pattern["name"],
                "mitre_techniques": pattern["attack_techniques"],
                "weaknesses": pattern["cwes"]
            }
            threats.append(threat)

    # 4. Get defensive recommendations
    d3fend = load_json("reference/security/mitre/d3fend/d3fend-summary.json")
    for threat in threats:
        threat["countermeasures"] = get_countermeasures(d3fend, threat["mitre_techniques"])

    return threats
```

### Pattern 3: Compliance Assessment Agent

```python
def assess_compliance(target_frameworks, evidence):
    # 1. Load compliance mappings
    frameworks = load_json("reference/security/compliance/frameworks.json")
    mappings = load_json("reference/security/compliance/control-mappings.json")
    tech_reqs = load_json("reference/security/compliance/technical-requirements.json")

    # 2. Get unified control requirements
    required_controls = []
    for framework in target_frameworks:
        controls = get_framework_controls(frameworks, framework)
        required_controls.extend(controls)

    # 3. Deduplicate via control mappings
    unified_controls = deduplicate_controls(required_controls, mappings)

    # 4. Assess each control
    results = []
    for control in unified_controls:
        tech_check = get_technical_check(tech_reqs, control)
        status = assess_control(evidence, tech_check)
        results.append({
            "control": control,
            "status": status,
            "frameworks_satisfied": get_mapped_frameworks(mappings, control)
        })

    return results
```

### Pattern 4: Vulnerability Prioritization Agent

```python
def prioritize_vulnerabilities(cve_list):
    # 1. Load prioritization data
    kev = load_json("reference/security/kev/known-exploited-vulnerabilities.json")
    epss = load_json("reference/security/epss/exploit-prediction.json")
    exploits = load_json("reference/security/exploits/exploit-availability.json")

    # 2. Enrich each CVE
    prioritized = []
    for cve in cve_list:
        priority = {
            "cve_id": cve,
            "in_kev": cve in kev["vulnerabilities"],
            "epss_score": get_epss_score(epss, cve),
            "exploit_available": check_exploit(exploits, cve)
        }

        # 3. Calculate priority score
        priority["score"] = calculate_priority(
            kev_bonus=10 if priority["in_kev"] else 0,
            epss_weight=priority["epss_score"] * 5,
            exploit_bonus=3 if priority["exploit_available"] else 0
        )
        prioritized.append(priority)

    # 4. Sort by priority
    return sorted(prioritized, key=lambda x: x["score"], reverse=True)
```

### Pattern 5: Supply Chain Security Agent

```python
def assess_supply_chain(project_path):
    # 1. Load supply chain references
    slsa = load_json("reference/security/slsa/slsa-levels.json")
    scorecard = load_json("reference/security/openssf/scorecard.json")
    sbom_formats = load_json("reference/security/sbom/sbom-formats.json")

    # 2. Check SLSA compliance
    slsa_level = assess_slsa_level(project_path, slsa)

    # 3. Run Scorecard checks
    scorecard_results = []
    for check in scorecard["checks"]:
        result = evaluate_check(project_path, check)
        scorecard_results.append(result)

    # 4. Analyze SBOM
    sbom = find_sbom(project_path)
    if sbom:
        format_type = detect_sbom_format(sbom, sbom_formats)
        components = parse_sbom(sbom, format_type)
        dependency_risks = assess_dependencies(components)

    return {
        "slsa_level": slsa_level,
        "scorecard_score": calculate_score(scorecard_results),
        "dependency_risks": dependency_risks
    }
```

## Lookup Utilities

### CWE Quick Lookup

The `cwe-top-25-2025.json` includes a `quick_lookup` section for fast access:

```json
{
  "quick_lookup": {
    "injection": ["CWE-89", "CWE-78", "CWE-77", "CWE-94"],
    "memory": ["CWE-787", "CWE-416", "CWE-125", "CWE-119", "CWE-476", "CWE-190"],
    "auth": ["CWE-287", "CWE-306", "CWE-862", "CWE-863", "CWE-269"],
    "web": ["CWE-79", "CWE-352", "CWE-918", "CWE-22", "CWE-434"],
    "crypto": ["CWE-798", "CWE-502"]
  }
}
```

### Cross-Reference Navigation

Each reference file includes a `cross_references` section pointing to related files:

```json
{
  "cross_references": {
    "owasp_api_2023": "reference/security/owasp/top10-api-2023.json",
    "cwe_top25": "reference/security/cwe/cwe-top-25-2025.json",
    "nist_800_53": "reference/security/nist/sp800-53-controls.json"
  }
}
```

### Agent Usage Hints

Each file includes an `agent_usage` section with task-specific guidance:

```json
{
  "agent_usage": {
    "code_review": "Use detection_patterns for static analysis",
    "threat_modeling": "Map findings to CAPEC attack patterns",
    "remediation": "Reference mitigation strategies by severity"
  }
}
```

## Best Practices for Agent Integration

### 1. Load References at Agent Initialization

```python
class SecurityAgent:
    def __init__(self):
        # Load all references once at startup
        self.references = {
            "cwe": load_json("reference/security/cwe/cwe-top-25-2025.json"),
            "owasp_web": load_json("reference/security/owasp/top10-web-2025.json"),
            # ... other references
        }
```

### 2. Use Manifest for Discovery

```python
def get_available_references():
    manifest = load_json("reference/security/manifest.json")
    return {
        source: info["files"]
        for source, info in manifest["sources"].items()
    }
```

### 3. Check Version Before Decisions

```python
def validate_reference_currency(reference):
    manifest = load_json("reference/security/manifest.json")
    staleness = manifest["staleness_policy"]["max_age_days"]
    # Warn if reference is approaching staleness threshold
```

### 4. Chain References for Context

```python
def enrich_finding(cwe_id):
    """Chain references to provide full context for a finding."""
    cwe = lookup_cwe(cwe_id)

    return {
        "weakness": cwe,
        "attack_patterns": lookup_capec_by_cwe(cwe_id),
        "owasp_category": lookup_owasp_by_cwe(cwe_id),
        "countermeasures": lookup_d3fend_by_attack(cwe["related_attacks"]),
        "compliance_controls": lookup_controls_by_cwe(cwe_id)
    }
```

## File Structure Summary

```text
reference/security/
├── manifest.json                    # Central catalog with versions
├── AGENT_GUIDE.md                   # This file
│
├── mitre/
│   ├── attack/
│   │   └── techniques-summary.json  # ATT&CK v18.1 techniques
│   ├── atlas/
│   │   └── atlas-summary.json       # ATLAS v5.0 AI/ML attacks
│   ├── d3fend/
│   │   └── d3fend-summary.json      # D3FEND v1.0 defenses
│   └── capec/
│       └── capec-summary.json       # CAPEC v3.9 attack patterns
│
├── cwe/
│   └── cwe-top-25-2025.json         # CWE Top 25 (v4.19)
│
├── owasp/
│   ├── top10-web-2025.json          # OWASP Top 10 Web 2025
│   ├── top10-api-2023.json          # OWASP Top 10 API 2023
│   ├── top10-llm-2025.json          # OWASP Top 10 LLM 2025
│   ├── top10-mobile-2024.json       # OWASP Mobile Top 10 2024
│   └── asvs-5.0.json                # ASVS v5.0 requirements
│
├── slsa/
│   └── slsa-levels.json             # SLSA v1.2 levels
│
├── openssf/
│   └── scorecard.json               # OpenSSF Scorecard checks
│
├── sbom/
│   └── sbom-formats.json            # CycloneDX, SPDX, SWID
│
├── compliance/
│   ├── frameworks.json              # 20+ compliance frameworks
│   ├── control-mappings.json        # Cross-framework mappings
│   └── technical-requirements.json  # Actionable checks
│
├── cis/
│   └── controls-v8.json             # CIS Controls v8.1
│
├── nist/
│   ├── csf-2.0-summary.json         # NIST CSF 2.0
│   └── sp800-53-controls.json       # NIST 800-53 r5
│
├── kev/
│   └── known-exploited-vulnerabilities.json  # CISA KEV
│
├── epss/
│   └── exploit-prediction.json      # EPSS scores
│
└── crypto/
    └── cryptographic-standards.json # Crypto guidance
```

## Versioning and Updates

- **Manifest version**: Check `manifest.json` version field (currently 3.1.0)
- **Update automation**: `.github/workflows/check-security-refs.yml` runs monthly
- **Staleness policy**: See `manifest.json` `staleness_policy` for max ages
- **Next review**: Quarterly review scheduled (see `next_review` in manifest)
