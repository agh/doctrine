# /refactor Command

Simplify and improve code while preserving functionality using comprehensive analysis.

## Usage

```text
/refactor [file or function] [options]
```

## Options

- `--explain` - Analyze only, don't apply changes
- `--metrics` - Show detailed complexity metrics
- `--incremental` - Apply changes one at a time with confirmation
- `--safe` - Only apply high-confidence (≥90%) changes

## Examples

```text
/refactor src/legacy/parser.ts
/refactor processData --explain
/refactor src/utils/ --metrics
/refactor auth-service.ts --incremental
/refactor payment.go --safe
```

## Behavior

1. **Analyze** - Calculate complexity metrics (cyclomatic, cognitive, maintainability)
2. **Trace** - Map dependencies and identify affected callers
3. **Validate** - Check test coverage and semantic contract
4. **Propose** - Show simplifications with confidence scores and risk levels
5. **Apply** - Make changes only after showing the plan

## Implementation

```markdown
Analyze and simplify the following code using the code-simplifier agent:

$ARGUMENTS

**Analysis Protocol:**
1. Calculate complexity metrics (cyclomatic, cognitive, Halstead, maintainability)
2. Trace dependencies across files
3. Identify test coverage for affected code
4. Document semantic contract (inputs, outputs, side effects)

**Simplification Targets:**
- Reduce complexity: guard clauses, Extract Method, Compose Method
- Remove redundancy: dead code, DRY violations, unused imports
- Improve readability: Intention-Revealing Names, Explaining Variable
- Modernize: language-specific idioms (see agent for patterns)

**Output Requirements:**
- Complexity metrics table (before/after)
- Semantic preservation checklist
- Dependency impact graph
- Each change with confidence score and risk level
- Fowler refactoring pattern names where applicable

**CRITICAL:** Preserve behavior exactly. Verify semantic contract maintained.
Show before/after for each change with explanation and confidence.
```

## See Also

- [Code Simplifier Agent](../agents/code-simplifier.md) - Full agent specification
- [Code Reviewer Agent](../agents/code-reviewer.md) - Post-refactor review
