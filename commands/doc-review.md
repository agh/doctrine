# /doc-review Command

Review documentation for accuracy, completeness, and clarity.

## Usage

```text
/doc-review [file]
/doc-review docs/api.md              # Review specific file
/doc-review docs/                    # Review all docs in directory
/doc-review --strict                 # Fail on any issues
```

## Behavior

1. Invokes the **doc-reviewer** agent
2. Reads documentation and corresponding source code
3. Verifies accuracy of signatures, examples, and behaviors
4. Assesses completeness and clarity
5. Outputs structured review with findings

## Output

Review report including:

- Overall assessment (Excellent/Good/Needs Work/Critical)
- Critical issues that MUST be fixed
- Improvements that SHOULD be made
- Suggestions that MAY enhance quality
- Coverage metrics

## Implementation

```markdown
Invoke the doc-reviewer agent to review:

$ARGUMENTS

Review against these criteria:
1. Accuracy - Do examples work? Are signatures correct?
2. Completeness - Are all public APIs documented?
3. Clarity - Is the language clear and unambiguous?
4. Currency - Does documentation match current code?
5. Audience fit - Is it appropriate for target readers?

Output a structured review with prioritized findings.
```

## Example

```text
> /doc-review docs/auth.md

## Documentation Review: docs/auth.md

### Summary: Needs Work

### Critical Issues
- [ ] Line 45: `login()` signature missing `rememberMe` parameter
- [ ] Line 78: Example uses deprecated `authToken` (now `accessToken`)

### Improvements
- [ ] Add error handling example for rate limiting
- [ ] Document the `refreshToken()` function

### Coverage
- Public APIs: 4/5 documented (80%)
- Examples provided: 3/5 (60%)

### Recommendation: Revise and re-review
```
