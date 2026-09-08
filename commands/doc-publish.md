# /doc-publish Command

Generate documentation in multiple output formats.

## Usage

```text
/doc-publish [source]
/doc-publish docs/               # Publish all docs
/doc-publish --llms              # Generate llms.txt only
/doc-publish --mcp              # Generate MCP tool declarations only
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

Tool declarations for MCP protocol revision **2026-07-28**, the current
revision. Each declaration **MUST** contain:

- `name` — unique tool identifier
- `inputSchema` — a valid JSON Schema object, never `null`
- `description` — human-readable summary of what the tool does

`title`, `outputSchema`, `annotations`, and `icons` are **OPTIONAL**.

#### Why

`inputSchema` is a required property of `Tool` in the published schema. A tool
object that carries a bare `parameters` map instead fails validation, so the
declaration cannot be consumed as an integration schema.

#### Do

```json
{
  "name": "login",
  "description": "Authenticate a user and return a token pair.",
  "inputSchema": {
    "type": "object",
    "properties": {"email": {"type": "string"}},
    "required": ["email"]
  }
}
```

#### Don't

```json
{
  "name": "login",
  "description": "Authenticate a user and return a token pair.",
  "parameters": {"email": {"type": "string"}}
}
```

#### Artefact boundaries

This command emits tool declarations only. It **MUST NOT** label its output an
"MCP config", because three distinct artefacts exist:

| Artefact | Shape | Produced by |
| -------- | ----- | ----------- |
| Tool declaration | `Tool` object | `/doc-publish --mcp` |
| `tools/list` result | `resultType`, `tools`, `ttlMs`, `cacheScope` | MCP server |
| Server configuration | `mcpServers` entry naming a command or URL | MCP host |

Every generated declaration **MUST** be validated against
[`schema/2026-07-28/schema.json`][mcp-schema] before publication.

[mcp-schema]: https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/schema/2026-07-28/schema.json

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
2. MCP - Tool declarations for protocol revision 2026-07-28, each with a
   valid `inputSchema` JSON Schema object
3. Mermaid - Visual diagrams

Validate each output format before returning it. Validate MCP declarations
against schema/2026-07-28/schema.json and include all formats in response.
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

    Tool declaration, MCP protocol revision 2026-07-28:

        {
          "name": "login",
          "title": "Log In",
          "description": "Authenticate a user and return an access/refresh token pair.",
          "inputSchema": {
            "type": "object",
            "properties": {
              "email": {"type": "string", "format": "email"},
              "password": {"type": "string", "minLength": 1}
            },
            "required": ["email", "password"],
            "additionalProperties": false
          },
          "outputSchema": {
            "type": "object",
            "properties": {
              "accessToken": {"type": "string"},
              "refreshToken": {"type": "string"},
              "expiresIn": {"type": "integer"}
            },
            "required": ["accessToken", "refreshToken", "expiresIn"]
          }
        }

    Validated against schema/2026-07-28/schema.json #/$defs/Tool.
    A server returns these inside a tools/list result, which additionally
    requires resultType, ttlMs, and cacheScope.

    ### Architecture Diagram

        sequenceDiagram
            Client->>+API: POST /login
            API->>+Auth: validate(credentials)
            Auth->>+DB: findUser(email)
            DB-->>-Auth: user
            Auth-->>-API: tokens
            API-->>-Client: 200 + TokenPair
