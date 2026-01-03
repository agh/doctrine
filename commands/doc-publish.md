# /doc-publish Command

Generate documentation in multiple output formats.

## Usage

```text
/doc-publish [source]
/doc-publish docs/               # Publish all docs
/doc-publish --llms              # Generate llms.txt only
/doc-publish --mcp               # Generate MCP config only
/doc-publish --diagrams          # Generate Mermaid diagrams only
/doc-publish --all               # Generate all formats
```

## Behavior

1. Invokes the **doc-publisher** agent
2. Reads source documentation
3. Transforms to requested output formats
4. Validates format correctness
5. Outputs all generated formats

## Output Formats

### llms.txt

Optimized for AI assistant consumption:

- Dense, information-rich
- Minimal formatting overhead
- Executable examples
- Token-efficient

### MCP (Model Context Protocol)

Structured JSON for AI tool integration:

- Function signatures
- Parameter schemas
- Tool descriptions

### Mermaid Diagrams

Visual documentation as code:

- Architecture flowcharts
- Sequence diagrams
- State machines
- ER diagrams

## Implementation

```markdown
Invoke the doc-publisher agent to transform:

$ARGUMENTS

Generate documentation in requested formats:
1. llms.txt - AI-optimized, token-efficient
2. MCP - Tool integration schemas
3. Mermaid - Visual diagrams

Validate each output format and include all in response.
```

## Example

    > /doc-publish docs/auth.md --all

    ## Published: docs/auth.md

    ### llms.txt

        # Authentication API
        > JWT-based authentication with refresh tokens

        ## Functions
        login(email: string, password: string): Promise<TokenPair>
          Authenticate user, returns access + refresh tokens.
          Throws: AuthError (invalid credentials), RateLimitError (too many attempts)

        refresh(token: string): Promise<TokenPair>
          Exchange refresh token for new token pair.

        logout(token: string): Promise<void>
          Invalidate refresh token.

    ### MCP Tools

        {
          "tools": [
            {
              "name": "login",
              "description": "Authenticate user with credentials",
              "parameters": {
                "email": {"type": "string"},
                "password": {"type": "string"}
              }
            }
          ]
        }

    ### Architecture Diagram

        sequenceDiagram
            Client->>+API: POST /login
            API->>+Auth: validate(credentials)
            Auth->>+DB: findUser(email)
            DB-->>-Auth: user
            Auth-->>-API: tokens
            API-->>-Client: 200 + TokenPair
