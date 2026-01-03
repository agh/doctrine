# /doc-plan Command

Analyze codebase and create a prioritized documentation plan.

## Usage

```text
/doc-plan [directory]
/doc-plan                    # Analyze entire project
/doc-plan src/               # Analyze specific directory
/doc-plan --output plan.md   # Save plan to file
```

## Behavior

1. Invokes the **doc-architect** agent
2. Analyzes codebase structure, data flow, and dependencies
3. Identifies all documentable components
4. Prioritizes based on importance and dependencies
5. Outputs structured documentation plan

## Output

Documentation plan including:

- Priority-ordered list of components to document
- Documentation type per component (API, tutorial, reference)
- Cross-reference map showing relationships
- Estimated scope for planning

## Implementation

```markdown
Invoke the doc-architect agent to analyze:

$ARGUMENTS

Create a documentation plan covering:
1. Structure analysis - directory layout, entry points
2. API surface - public interfaces to document
3. Data flow - how data moves through the system
4. Dependencies - what depends on what
5. Complexity - areas needing detailed explanation

Output a prioritized documentation plan with recommended order.
```

## Example

```text
> /doc-plan src/services/

## Documentation Plan: src/services/

### Priority Order

| Priority | Component | Type | Scope |
| -------- | --------- | ---- | ----- |
| P0 | auth-service.ts | API Reference | Large |
| P0 | user-service.ts | API + Tutorial | Large |
| P1 | email-service.ts | API Reference | Medium |
| P2 | utils/ | Utility Reference | Small |

### Cross-References
auth-service → user-service (authentication flow)
user-service → email-service (notifications)

### Recommended Order
1. auth-service - Core dependency for all protected routes
2. user-service - Depends on auth, used by most features
3. email-service - Used by user-service for notifications
```
