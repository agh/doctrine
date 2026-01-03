# /explain Command

Explain how code works in plain language.

## Usage

```text
/explain [file, function, or code block]
```

## Examples

```text
/explain src/auth/oauth.ts
/explain handleWebhook
/explain --deep src/core/  # Deep dive with diagrams
```

## Behavior

1. Reads and analyzes the target code
2. Explains purpose, flow, and key decisions
3. Identifies patterns, dependencies, and edge cases
4. Optionally generates diagrams for complex flows

## Implementation

```markdown
Explain the following code in plain language:

$ARGUMENTS

Provide:
1. **Purpose**: What does this code do and why does it exist?
2. **How it works**: Step-by-step explanation of the logic
3. **Key decisions**: Why was it written this way?
4. **Dependencies**: What does this code rely on?
5. **Edge cases**: What special cases does it handle?

Use clear, jargon-free language. Include code snippets to illustrate key points.
```
