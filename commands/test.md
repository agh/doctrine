# /test Command

Generate comprehensive tests for the specified code.

## Usage

```text
/test [file or function]
```

## Examples

```text
/test src/utils/validate.ts
/test parseConfig
/test src/api/  # Tests all files in directory
```

## Behavior

1. Analyzes the target code to understand functionality
2. Identifies existing test patterns in the project
3. Generates unit tests covering happy path, errors, and edge cases
4. Places tests following project conventions

## Implementation

```markdown
Generate comprehensive tests for:

$ARGUMENTS

Use the test-writer agent guidelines:
- Follow existing test patterns in this project
- Cover: happy path, error cases, edge cases
- Edge cases: empty inputs, boundary values, invalid inputs, errors
- Use descriptive test names
- One assertion per test when possible
- Use arrange-act-assert pattern

First show a test plan, then generate complete runnable tests.
```
