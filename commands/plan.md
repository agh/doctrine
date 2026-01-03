# /plan Command

Create an implementation plan before coding.

## Usage

```text
/plan [feature or task description]
```

## Examples

```text
/plan Add user authentication with OAuth
/plan Migrate database from Postgres to SQLite
/plan Refactor the API to use REST conventions
```

## Behavior

1. Explores codebase to understand current architecture
2. Identifies affected files and components
3. Creates step-by-step implementation plan
4. Lists risks, dependencies, and alternatives
5. Waits for approval before proceeding

## Implementation

```markdown
Create an implementation plan for:

$ARGUMENTS

Follow the Hero Flow - this is the PLAN phase:

1. **Explore**: Examine relevant code, understand current architecture
2. **Scope**: Define exactly what changes are needed
3. **Plan**: Create numbered implementation steps
4. **Risks**: Identify potential issues and mitigations
5. **Alternatives**: Note other approaches considered

Output format:
## Implementation Plan: [Title]

### Current State
[What exists now]

### Proposed Changes
1. [Step with specific files]
2. [Step with specific files]
...

### Risks
- [Risk]: [Mitigation]

### Alternatives Considered
- [Alternative]: [Why not chosen]

---
Awaiting approval to proceed with implementation.
```
