# /code Command

Comprehensive code quality assessment using the Doctrine Code Agent Family.

## Usage

```text
/code [target] [subcommand] [options]
```

## Subcommands

| Subcommand | Agent | Model | Description |
| ---------- | ----- | ----- | ----------- |
| (none) | Code Architect | Opus | Full code assessment |
| `quick` | Code Reviewer | Haiku | Fast scan, critical only |
| `review` | Code Reviewer | Sonnet | Standard code review |
| `perf` | Performance Reviewer | Sonnet | Performance analysis |
| `a11y` | Accessibility Reviewer | Sonnet | WCAG/A11y compliance |
| `api` | REST API Reviewer | Sonnet | REST API design |
| `api --graphql` | GraphQL API Reviewer | Sonnet | GraphQL schema design |
| `tests` | Test Writer | Sonnet | Test generation |
| `simplify` | Code Simplifier | Sonnet | Complexity reduction |
| `docs` | Doc Writer | Haiku | Documentation |

## Examples

```text
/code src/auth/                       # Full assessment of auth module
/code quick                           # Quick review of staged changes
/code review src/auth.ts              # Standard review of file
/code perf src/services/              # Performance analysis
/code a11y src/components/            # Accessibility review
/code api api/routes/                 # REST API design review
/code api --graphql schema.graphql    # GraphQL schema review
/code tests src/auth/login.ts         # Generate tests for file
/code simplify src/utils/parser.ts    # Simplify complex code
/code docs src/services/              # Generate documentation
```

## Behavior

1. **Target selection**:
   - If path provided: analyzes that file or directory
   - If no path: analyzes `git diff --staged`

2. **Agent selection**:
   - No subcommand: Code Architect (Opus) coordinates full assessment
   - With subcommand: Routes directly to specialist agent

3. **Output**: Findings grouped by severity with auto-fix suggestions

## Review Modes

| Mode | Command | Focus | Cost |
| ---- | ------- | ----- | ---- |
| **Quick** | `/code quick` | Critical issues only | ~$0.02 |
| **Standard** | `/code review` | Security, performance, quality | ~$0.20 |
| **Full** | `/code` | All specialists, comprehensive | ~$0.80 |

## Implementation

    Analyze the code at: $ARGUMENTS

    ## Mode Selection

    Based on subcommand:
    - (none) → Full assessment: Use Code Architect to coordinate all relevant
      specialists
    - `quick` → Quick mode: Critical issues only (Haiku)
    - `review` → Standard mode: Security, performance, quality (Sonnet)
    - `perf` → Use Performance Reviewer
    - `a11y` → Use Accessibility Reviewer
    - `api` → Use REST API Reviewer (or GraphQL if --graphql)
    - `tests` → Use Test Writer
    - `simplify` → Use Code Simplifier
    - `docs` → Use Doc Writer

    ## Output Format

    Start with metrics:

    | Metric | Value |
    |--------|-------|
    | **Review Effort** | [1-5] |
    | **Risk Level** | Low / Medium / High / Critical |
    | **Change Size** | XS / S / M / L / XL |

    Then findings by severity:

    ### Critical (must fix before merge)

    - [ ] **[Category]**: [description] (`file:line`) — **[confidence]%**

      **Before**: [problematic code]

      **After**: [fixed code]

      **Why**: [explanation]

    ### Warning (should fix)

    ### Suggestion (consider)

    ### Positive Observations

    ### Summary

    [1-2 sentence overall assessment]

## See Also

- [Code Agent Family](../../guides/ai/code-agents.md) — Architecture overview
- [Code Architect](../agents/code/architect.md) — Coordinator specification
- [Code Reviewer](../agents/code/reviewer.md) — Standard review
- [Performance Reviewer](../agents/code/performance.md) — Performance specialist
- [Accessibility Reviewer](../agents/code/accessibility.md) — A11y specialist
- [REST API Reviewer](../agents/code/api-rest.md) — REST API design
- [GraphQL API Reviewer](../agents/code/api-graphql.md) — GraphQL design
- [Test Writer](../agents/code/test-writer.md) — Test generation
- [Code Simplifier](../agents/code/simplifier.md) — Complexity reduction
