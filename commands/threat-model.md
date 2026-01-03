# /threat-model Command

Design-time security analysis using STRIDE methodology.

## Usage

```text
/threat-model <feature or architecture description>
```

## Examples

```bash
# New feature threat model
/threat-model "Add payment processing with Stripe integration"

# Architecture analysis
/threat-model "Microservices migration for user service"

# API design review
/threat-model "New public API for partner integrations"

# Analyze existing design document
/threat-model docs/architecture/auth-system.md
```

## Behavior

1. **Threat Modeler** analyzes the system/feature
2. Creates data flow diagram (Mermaid)
3. Identifies trust boundaries
4. Applies STRIDE analysis
5. Builds attack trees for critical assets
6. Generates security requirements

## Output

```markdown
# Threat Model: [Feature Name]

## Data Flow Diagram
[Mermaid diagram]

## Trust Boundaries
[Table of boundaries and protections]

## STRIDE Analysis
- Spoofing threats
- Tampering threats
- Repudiation threats
- Information Disclosure threats
- Denial of Service threats
- Elevation of Privilege threats

## Attack Trees
[For high-value assets]

## Security Requirements
[RFC 2119 requirements for implementation]

## Risk Assessment
[Prioritized risk matrix]
```

## Implementation

```markdown
You are the Threat Modeler. Analyze this system design for security threats:

$ARGUMENTS

Apply the STRIDE methodology:
1. Decompose the system into components
2. Create data flow diagram
3. Identify trust boundaries
4. Analyze each boundary for STRIDE threats
5. Build attack trees for critical assets
6. Generate security requirements

Output a comprehensive threat model document.
```

## Related Commands

- `/security` - Code-level security review
- `/compliance` - Compliance assessment
