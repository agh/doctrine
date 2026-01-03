# /incident Command

Security incident response mode.

## Usage

```text
/incident <action> [details]
```

## Actions

| Action | Description |
| ------ | ----------- |
| `triage` | Initial severity assessment |
| `analyze <logs>` | Investigate evidence |
| `contain` | Generate containment actions |
| `remediate` | Create fix plan |
| `postmortem` | Generate post-incident report |

## Examples

```bash
# Initial triage
/incident triage "Unauthorized access alerts from SIEM"

# Analyze logs
/incident analyze logs/auth-failures.log

# Generate containment plan
/incident contain "Compromised user account user@example.com"

# Create remediation plan
/incident remediate "SQL injection in /api/users endpoint"

# Generate post-mortem
/incident postmortem
```

## Behavior

**Incident Response Lead** (Opus model) takes control:

1. **Triage**: Assess severity, scope, and immediate actions
2. **Analyze**: Investigate evidence, build timeline, find root cause
3. **Contain**: Generate immediate containment steps
4. **Remediate**: Create fix plan with verification steps
5. **Postmortem**: Document lessons learned

## Output

### Triage Output

```markdown
## Incident Triage

**Severity**: SEV-[1-4]
**Scope**: [Affected systems]
**Status**: [Active/Contained/Resolved]

### Immediate Actions Required
1. [Action with owner]
2. [Action with owner]

### Investigation Needed
- [Evidence to collect]
- [Systems to check]
```

### Postmortem Output

```markdown
## Post-Mortem Report

### Summary
[What happened in 2-3 sentences]

### Timeline
[Detailed timeline of events]

### Root Cause
[5 Whys analysis]

### What Went Well
[Positive observations]

### What Could Improve
[Areas for improvement]

### Action Items

| Item | Owner | Due | Status |
| ---- | ----- | --- | ------ |
```

## Implementation

```markdown
You are the Incident Response Lead. This is a security incident:

$ARGUMENTS

Action requested: $ACTION

For triage:
- Assess severity (SEV-1 to SEV-4)
- Identify scope and impact
- List immediate containment actions

For analysis:
- Build timeline from evidence
- Identify root cause
- Determine attack vector

For containment:
- Generate specific containment steps
- Identify what to preserve for forensics

For postmortem:
- Document complete incident lifecycle
- Apply 5 Whys for root cause
- Generate action items with owners
```

## Guidelines

- **MUST** preserve evidence before containment
- **MUST** document all actions taken
- **SHOULD** use war room for SEV-1/SEV-2
- **MUST NOT** speculate about impact without evidence
- **MUST NOT** communicate externally without approval

## Related Commands

- `/security` - Preventive security review
- `/security-fix` - Generate fixes
