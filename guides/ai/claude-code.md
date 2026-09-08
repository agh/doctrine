# Claude Code CLI Configuration

> [Doctrine](../../README.md) > [AI](README.md) > Claude Code CLI

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

## Overview

This guide covers Claude Code CLI[^1] configuration: hooks, permissions,
subagents, commands, and MCP. For universal AI workflows (Hero Flow, TDD,
Visual Iteration), see [AI Workflows](ai-workflows.md).

## Quick Reference

| Task | Command/File |
|------|--------------|
| Start session | `claude` |
| Plan mode | `/plan` |
| Headless mode | `claude -p "prompt"` |
| Permissions | `/permissions` |
| Clear context | `/clear` |
| Config file | `.claude/settings.json` |
| Subagents | `.claude/agents/*.md` |
| Commands | `.claude/commands/*.md` |
| MCP servers | `.mcp.json` |

---

## Table of Contents

1. [Configuration Files](#configuration-files)
2. [Hooks](#hooks)
3. [Permissions](#permissions)
4. [Subagents](#subagents)
5. [Custom Commands](#custom-commands)
6. [MCP Integration](#mcp-integration)
7. [Long-Running Sessions](#long-running-sessions)
8. [Syncing from Doctrine](#syncing-from-doctrine)

---

## Configuration Files

Claude Code uses several configuration files:

```text
project/
├── .claude/
│   ├── settings.json      # Permissions, hooks, preferences
│   ├── agents/            # Reusable subagent definitions
│   │   ├── code/          # Code quality agents
│   │   │   ├── architect.md
│   │   │   ├── reviewer.md
│   │   │   └── ...
│   │   ├── system/        # Infrastructure agents
│   │   │   ├── architect.md
│   │   │   ├── docker.md
│   │   │   └── ...
│   │   └── security/      # Security agents
│   │       └── ...
│   └── commands/          # Custom slash commands
│       ├── code.md
│       ├── system.md
│       └── ...
├── .mcp.json              # MCP server configuration
├── AGENTS.md              # Project context (see agents-md.md)
├── CLAUDE.md              # `@AGENTS.md` import
└── GEMINI.md              # `@./AGENTS.md` import
```

### settings.json Structure

```json
{
  "permissions": {
    "allow": [...],
    "deny": [...]
  },
  "hooks": {
    "PostToolUse": [...],
    "PreToolUse": [...],
    "Stop": [...]
  },
  "preferences": {
    "autoCompact": true,
    "compactThreshold": 100000
  }
}
```

See [configs/claude/settings.json](../../configs/claude/settings.json) for Doctrine's standard configuration.

---

## Hooks

Hooks automate quality checks and enable long-running sessions. They **MUST**
be configured for professional workflows.

### Hook Types

| Hook | When it Runs | Use Case |
|------|--------------|----------|
| `PostToolUse` | After Claude uses a tool | Auto-format, auto-lint |
| `PreToolUse` | Before Claude uses a tool | Validation, logging |
| `Stop` | When Claude stops | Verify completion, auto-resume |

### PostToolUse: Auto-Format

**MUST** auto-format after file changes. This catches the "last 10%" of style issues:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | { read -r f; npm run format -- --write \"$f\" || true; }"
          }
        ]
      }
    ]
  }
}
```

### PostToolUse: Auto-Lint

**SHOULD** lint after file changes:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | { read -r f; npm run lint:file -- \"$f\" || true; }"
          }
        ]
      }
    ]
  }
}
```

### Stop: Verify Completion

**MUST** verify before accepting completion on important tasks:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "npm test && npm run lint && npm run typecheck"
          }
        ]
      }
    ]
  }
}
```

If the Stop hook command fails, Claude is prompted to continue and fix issues.

### Hook Input

Hook commands receive a JSON payload on **stdin** (there are no
`$CLAUDE_*` environment variables for tool data). Extract fields with `jq`:

| JSON field | Value |
|------------|-------|
| `.tool_input.file_path` | Path to file being written/edited |
| `.tool_name` | Name of tool being used |

Example: `jq -r '.tool_input.file_path' | { read -r f; <formatter> "$f"; }`

---

## Permissions

**MUST** configure permissions to avoid prompt fatigue without sacrificing safety.

### Permission Syntax

```text
ToolName(pattern)
```

Examples:

- `Bash(npm run *)` — Allow any npm run command
- `Edit(src/**)` — Allow file writes/edits in src/ and subdirectories
  (file-tool path rules are matched as `Edit(path)`; `Write(path)` rules
  are not matched and are dead)
- `Read(*)` — Allow reading any file

### Doctrine's Standard Allowlist

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run *)",
      "Bash(npx *)",
      "Bash(bun run *)",
      "Bash(pnpm *)",
      "Bash(yarn *)",
      "Bash(uv run *)",
      "Bash(git status*)",
      "Bash(git diff*)",
      "Bash(git log*)",
      "Bash(git branch*)",
      "Bash(git checkout*)",
      "Bash(git add*)",
      "Bash(git commit*)",
      "Bash(cat *)",
      "Bash(ls *)",
      "Bash(find *)",
      "Bash(grep *)",
      "Bash(rg *)",
      "Read(*)",
      "Glob(*)",
      "Grep(*)",
      "Edit(src/**)",
      "Edit(tests/**)",
      "Edit(test/**)",
      "Edit(docs/**)"
    ]
  }
}
```

### Doctrine's Standard Denylist

```json
{
  "permissions": {
    "deny": [
      "Bash(rm -rf *)",
      "Bash(sudo *)",
      "Bash(curl * | bash)",
      "Bash(wget * | bash)",
      "Bash(chmod 777 *)",
      "Bash(> /dev/sd*)",
      "Edit(.env)",
      "Edit(.env.*)",
      "Edit(**/secrets/**)",
      "Edit(**/*secret*)",
      "Edit(**/*password*)",
      "Edit(**/*credential*)",
      "Edit(**/*token*)",
      "Edit(**/*.pem)",
      "Edit(**/*.key)",
      "Edit(**/id_rsa*)"
    ]
  }
}
```

### Managing Permissions

```bash
# Interactive permission management
/permissions

# View current permissions
/permissions list

# Add permission for session
/permissions allow Bash(docker compose *)
```

---

## Subagents

Subagents are specialized Claude instances organized into agent families. Each
family has an Opus coordinator and Sonnet specialists.

### Agent Families

Doctrine provides three agent families:

| Family | Command | Coordinator | Purpose |
|--------|---------|-------------|---------|
| **Code** | `/code` | Code Architect (Opus) | Code quality review |
| **System** | `/system` | System Architect (Opus) | Infrastructure review |
| **Security** | `/security` | Security Architect (Opus) | Security analysis |

See the family guides for full details:

- [Code Agent Family](./code-agents.md)
- [System Agent Family](./system-agents.md)
- [Security Agent Family](./security-agents.md)

### Code Agent Family (`/code`)

| Agent | File | Purpose |
|-------|------|---------|
| Code Architect | `code/architect.md` | Opus coordinator |
| Code Reviewer | `code/reviewer.md` | General code review |
| Performance | `code/performance.md` | Deep performance analysis |
| Accessibility | `code/accessibility.md` | WCAG/A11y compliance |
| REST API | `code/api-rest.md` | REST API design |
| GraphQL API | `code/api-graphql.md` | GraphQL schema design |
| Test Writer | `code/test-writer.md` | Test generation |
| Simplifier | `code/simplifier.md` | Complexity reduction |

### System Agent Family (`/system`)

| Agent | File | Purpose |
|-------|------|---------|
| System Architect | `system/architect.md` | Opus coordinator |
| Docker | `system/docker.md` | Container security |
| Ansible | `system/ansible.md` | Playbook review |
| Linux | `system/linux.md` | OS hardening |
| Verify | `system/verify.md` | CI/CD validation |

### Unique Differentiators

Doctrine's agents are the **most comprehensive open-source option**:

1. **Tiered architecture** — Opus coordinators, Sonnet specialists, cost optimized
2. **Accessibility reviews** — No competitor offers WCAG/A11y analysis
3. **API design reviews** — REST and GraphQL specialists
4. **Infrastructure reviews** — Docker, Ansible, Linux specialists
5. **Doctrine integration** — References our style guides
6. **Multi-LLM compatible** — Works with Claude, GPT, Gemini
7. **Auto-fix suggestions** — Every issue includes fix, not just complaint

### Using Agents

```bash
# Full code assessment (Opus coordinates specialists)
/code src/auth/

# Quick review (Haiku, critical only)
/code quick

# Specific specialist
/code perf src/services/

# Full infrastructure assessment
/system stacks/

# Specific system review
/system docker stacks/platform/
```

---

## Custom Commands

Custom slash commands are reusable prompt templates.

### Creating Commands

Store in `.claude/commands/`:

```markdown
# .claude/commands/code.md

Analyze the code at: $ARGUMENTS

Based on subcommand, route to appropriate agent:
- (none) → Full assessment with Code Architect
- quick → Critical issues only (Haiku)
- review → Standard code review (Sonnet)
- perf → Performance Reviewer
- a11y → Accessibility Reviewer
...
```

### Using Commands

```bash
/code src/auth/
# Full assessment with Code Architect

/code quick
# Quick review of staged changes

/code perf src/services/
# Performance-focused review
```

### Doctrine's Standard Commands

| Command | Purpose | Subcommands |
|---------|---------|-------------|
| `/code` | Code quality review | `quick`, `review`, `perf`, `a11y`, `api`, `tests`, `simplify`, `docs` |
| `/system` | Infrastructure review | `docker`, `ansible`, `linux`, `verify` |
| `/security` | Security analysis | See [Security Agent Family](./security-agents.md) |
| `/refactor` | Refactor code | `--explain`, `--metrics`, `--incremental`, `--safe` |
| `/explain` | Explain code | `--deep` |
| `/plan` | Create implementation plan | Feature description |

See [commands/](../../commands/) for full definitions.

---

## MCP Integration

Model Context Protocol (MCP)[^2] connects Claude to external tools.

### .mcp.json Configuration

```json
{
  "mcpServers": {
    "slack": {
      "type": "http",
      "url": "https://slack.mcp.anthropic.com/mcp"
    },
    "puppeteer": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-puppeteer"]
    }
  }
}
```

### Common MCP Servers

| Server | Purpose | Type |
|--------|---------|------|
| Puppeteer | Browser automation, screenshots | stdio |
| Slack | Search and post messages | http |
| Sentry | Error logs and debugging | http |
| PostgreSQL | Database queries | stdio |
| GitHub | Issues, PRs, actions | http |

### MCP for Visual Iteration

Puppeteer MCP enables automated screenshots:

```json
{
  "mcpServers": {
    "puppeteer": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-puppeteer"]
    }
  }
}
```

Then in conversation:

```text
Take a screenshot of http://localhost:3000/login
```

---

## Long-Running Sessions

Claude Code can run for hours or days with proper configuration.

### Permission Modes

| Mode | Flag | Use Case |
|------|------|----------|
| Normal | (default) | Interactive development |
| Don't Ask | `--permission-mode=dontAsk` | Long tasks, respects denylist |
| Skip All | `--dangerously-skip-permissions` | Sandboxed environments only |

### Stop Hooks for Auto-Resume

Stop hooks verify completion and auto-resume if criteria not met:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "npm test && npm run lint"
          }
        ]
      }
    ]
  }
}
```

### The ralph-wiggum Plugin

Keeps prompting Claude until real completion:

```bash
claude plugins install ralph-wiggum
```

### Long-Running Session Checklist

- [ ] Permissions allowlist configured
- [ ] PostToolUse hooks for auto-format/lint
- [ ] Stop hooks for verification
- [ ] Clear completion criteria defined
- [ ] Running in sandbox/container (if using skip-permissions)

---

## Syncing from Doctrine

Doctrine provides standard Claude Code configurations. Agents and commands live
at the repository root in `agents/` and `commands/`; `configs/claude/` holds
`settings.json`, skills, and infrastructure context. A sync **MUST** copy from
those four source paths directly.

### Source-to-Destination Map

| Doctrine source | Project destination | Managed by Doctrine |
| --------------- | ------------------- | ------------------- |
| `agents/` | `.claude/agents/` | Yes — do not add project-local files |
| `commands/` | `.claude/commands/` | Yes — do not add project-local files |
| `configs/claude/skills/` | `.claude/skills/` | No — merged, project skills preserved |
| `configs/claude/settings.json` | `.claude/settings.json` | Yes — overwritten |

### Manual Sync

```bash
# Clone Doctrine once
git clone https://github.com/agh/doctrine.git ~/.doctrine

# Install into the current project
mkdir -p .claude
rsync -aL --delete ~/.doctrine/agents/   .claude/agents/
rsync -aL --delete ~/.doctrine/commands/ .claude/commands/
rsync -aL ~/.doctrine/configs/claude/skills/ .claude/skills/
cp ~/.doctrine/configs/claude/settings.json .claude/settings.json

# Verify the install materialised real files, not links
find .claude -type l -print   # MUST print nothing
test -f .claude/agents/code/reviewer.md && test -f .claude/commands/code.md
```

The trailing slash on each source path is significant: it copies the directory
**contents** rather than nesting a second directory inside the destination.
`-L` dereferences any symlink so the installed tree contains regular files on
every platform, including Windows checkouts made without `core.symlinks=true`.
`--delete` removes agents and commands withdrawn upstream, so those two
destinations **MUST NOT** hold project-local files.

### GitHub Action for Auto-Sync

Use the maintained template at
[`.github/workflows/sync-doctrine.yml`](../../configs/github/workflows/sync-doctrine.yml)
rather than hand-rolling a workflow. Copy it into your project's
`.github/workflows/`, then customise `SYNC_PATHS`:

```yaml
env:
  DOCTRINE_REPO: agh/doctrine
  DOCTRINE_BRANCH: main
  SYNC_PATHS: |
    configs/claude/settings.json:.claude/settings.json
    agents:.claude/agents
    commands:.claude/commands
```

### Version Pinning

Pin to a release tag so config changes arrive on your schedule rather than
upstream's. **The source paths differ by release**: `agents/` and `commands/`
sit at the repository root only in releases *after* v2.11.0; in v2.11.0 and
earlier they live under `configs/claude/`. Match `SYNC_PATHS` to the release
you pin, or the sync step reports `Source not found` and copies nothing:

```yaml
env:
  DOCTRINE_REPO: agh/doctrine
  DOCTRINE_BRANCH: v2.11.0
  SYNC_PATHS: |
    configs/claude/settings.json:.claude/settings.json
    configs/claude/agents:.claude/agents
    configs/claude/commands:.claude/commands
```

For a manual install from a pinned tarball (paths shown for v2.11.0):

```bash
DOCTRINE_VERSION=2.11.0
curl -sL "https://github.com/agh/doctrine/archive/refs/tags/v${DOCTRINE_VERSION}.tar.gz" | tar xz
mkdir -p .claude
rsync -aL --delete "doctrine-${DOCTRINE_VERSION}/configs/claude/agents/"   .claude/agents/
rsync -aL --delete "doctrine-${DOCTRINE_VERSION}/configs/claude/commands/" .claude/commands/
rsync -aL "doctrine-${DOCTRINE_VERSION}/configs/claude/skills/" .claude/skills/
cp "doctrine-${DOCTRINE_VERSION}/configs/claude/settings.json" .claude/settings.json
rm -rf "doctrine-${DOCTRINE_VERSION}"
```

GitHub's tag archives preserve symlinks, so `-L` matters here: it turns any
link in the archive into a regular file at the destination.

---

## See Also

- [Code Agent Family](code-agents.md) — Code quality review agents
- [System Agent Family](system-agents.md) — Infrastructure review agents
- [Security Agent Family](security-agents.md) — Security analysis agents
- [AI Workflows](ai-workflows.md) — Hero Flow, TDD, Visual Iteration
- [AGENTS.md Patterns](agents-md.md) — Project context files
- [Claude Best Practices](claude.md) — Model selection, API usage

---

## References

[^1]: [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code) — Official CLI documentation
[^2]: [MCP Documentation](https://modelcontextprotocol.io/) — Model Context Protocol specification
