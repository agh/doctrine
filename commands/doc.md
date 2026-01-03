# /doc Command

Generate documentation for the specified code.

## Usage

```text
/doc [file, function, or class]
```

## Examples

```text
/doc src/api/users.ts
/doc UserService
/doc --readme  # Generate README section
```

## Behavior

1. Analyzes the target code
2. Generates appropriate documentation type:
   - Functions: JSDoc/docstrings with parameters, returns, examples
   - Classes: Overview, constructor, properties, methods
   - Modules: Purpose, exports, usage examples
3. Outputs in project's existing documentation style

## Implementation

```markdown
Generate documentation for:

$ARGUMENTS

Use the doc-writer agent guidelines:
- For functions: signature, parameters, returns, throws, examples
- For classes: overview, constructor, properties, methods
- Write for developers using this code
- Include practical examples
- Document edge cases and limitations

Match the existing documentation style in this project.
```
