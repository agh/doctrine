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

**MUST** verify before accepting completion on important tasks, and the hook
**MUST** report failure with exit code 2:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/verify-complete.sh",
            "args": []
          }
        ]
      }
    ]
  }
}
```

#### Why

A Stop hook keeps Claude working only when it exits 2 or returns a
`decision: "block"` JSON object. Every other non-zero status is a non-blocking
error: Claude Code shows the first stderr line in the transcript and lets the
turn end.[^3] Test runners exit 1, so an inline `npm test && npm run lint`
command ends the session with the build still broken — the opposite of the
gate it appears to be.

Loop control is the second requirement. Stop input carries `stop_hook_active`,
which is `true` when Claude Code is already continuing because of a Stop hook,
and Claude Code overrides the hook and ends the turn after eight consecutive
blocks.[^3] `stop_hook_active` is not evidence that verification passed, so a
hook **MUST NOT** exit 0 merely because it is `true`. Count attempts instead,
block a bounded number of times, and then surface the unresolved failure with
exit 1 so it is visible rather than silent.

`Stop` has no matcher support; a `matcher` field on it is ignored.[^3] Use
`args: []` so Claude Code spawns the script directly and substitutes
`${CLAUDE_PROJECT_DIR}` without a shell.[^3]

### The Verification Script

Save this as `.claude/hooks/verify-complete.sh`, make it executable with
`chmod +x .claude/hooks/verify-complete.sh`, and put `jq` on `PATH`:

```bash
#!/usr/bin/env bash
# .claude/hooks/verify-complete.sh
# Stop hook: keep Claude working until verification passes, then report an
# unresolved failure instead of looping forever.
set -uo pipefail

max_attempts=3
state_dir=${TMPDIR:-/tmp}/claude-verify

hook_input=$(cat)
session=$(printf '%s' "$hook_input" | jq -r '.session_id // "unknown"' | tr -cd 'A-Za-z0-9_-')
resumed=$(printf '%s' "$hook_input" | jq -r '.stop_hook_active // false')
mkdir -p "$state_dir"
attempts_file=$state_dir/${session:-unknown}

log=$(mktemp "$state_dir/log.XXXXXX")
trap 'rm -f "$log"' EXIT

# Replace these with your project's verification commands.
if npm test >"$log" 2>&1 &&
  npm run lint >>"$log" 2>&1 &&
  npm run typecheck >>"$log" 2>&1; then
  rm -f "$attempts_file"
  exit 0
fi

attempts=0
if [ "$resumed" = "true" ] && [ -r "$attempts_file" ]; then
  attempts=$(cat "$attempts_file")
fi
attempts=$((attempts + 1))
printf '%s\n' "$attempts" >"$attempts_file"

if [ "$attempts" -ge "$max_attempts" ]; then
  rm -f "$attempts_file"
  printf 'Verification still failing after %d attempts; stopping for review.\n' "$attempts" >&2
  tail -n 20 "$log" >&2
  exit 1
fi

printf 'Verification failed (attempt %d of %d). Fix this before finishing:\n' \
  "$attempts" "$max_attempts" >&2
tail -n 20 "$log" >&2
exit 2
```

Exit codes the script produces:

| Situation | Exit | Effect |
|-----------|------|--------|
| Verification passed | 0 | Claude stops; attempt counter cleared |
| Verification failed, attempts 1–2 | 2 | Claude keeps working; stderr is the reason |
| Verification failed, attempt 3 | 1 | Turn ends; failure shown in the transcript |

**Don't** — an inline command that exits 1 does not block:

```json
{ "type": "command", "command": "npm test && npm run lint" }
```

**Do** — a script that converts failure into exit 2 and bounds its own retries:

```json
{
  "type": "command",
  "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/verify-complete.sh",
  "args": []
}
```

### Hook Input

Hook commands receive a JSON payload on **stdin** (there are no
`$CLAUDE_*` environment variables for tool data). Extract fields with `jq`:

| JSON field | Value |
|------------|-------|
| `.tool_input.file_path` | Path to file being written/edited |
| `.tool_name` | Name of tool being used |
| `.session_id` | Current session identifier |
| `.stop_hook_active` | `true` on `Stop` when a Stop hook is already resuming |

Example: `jq -r '.tool_input.file_path' | { read -r f; <formatter> "$f"; }`

---

## Permissions

**MUST** configure permissions to avoid prompt fatigue without sacrificing safety.

### Permission Syntax

```text
ToolName(pattern)
```

Examples:

- `Bash(npm run build)` — Allow exactly `npm run build`
- `Bash(npm run *)` — Allow every script `package.json` defines
- `Edit(src/**)` — Allow file writes/edits in src/ and subdirectories
  (file-tool path rules are matched as `Edit(path)`; `Write(path)` rules
  are not matched and are dead)
- `Read(~/.ssh/**)` — Match everything under the home directory's `.ssh`

Rules are evaluated deny, then ask, then allow, and the first match wins. A
deny rule therefore cannot carry allowlist exceptions, and an ask rule prompts
even when a narrower allow rule also matches.[^4]

### Doctrine's Standard Allowlist

Allow rules **MUST** name reviewed commands. They **MUST NOT** pre-approve a
package runner or environment runner, because those execute whatever argument
follows them:

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run build)",
      "Bash(npm run lint)",
      "Bash(npm run typecheck)",
      "Bash(npm test *)",
      "Bash(git status *)",
      "Bash(git diff *)",
      "Bash(git log *)",
      "Bash(git show *)",
      "Bash(git branch *)",
      "Bash(rg *)",
      "Edit(src/**)",
      "Edit(tests/**)",
      "Edit(test/**)",
      "Edit(docs/**)"
    ]
  }
}
```

#### Why

**No blanket `npx`.** Claude Code strips a fixed set of wrappers before
matching a Bash rule, and environment runners such as `npx`, `docker exec`,
and `devbox run` are deliberately not in that set: a rule matches whatever
follows the runner, so `Bash(npx *)` pre-approves any package the registry
will serve.[^4] Approve the inner command instead, one rule per command.

**Package scripts belong to the repository.** `Bash(npm run *)` approves every
script `package.json` defines now and every script a branch, a dependency
bump, or a pull request adds later. Name the scripts you reviewed. A team
**MAY** widen this to `Bash(npm run *)` for a repository whose manifest it
owns and reviews; it **MUST NOT** do so for code it has not reviewed.

**No blanket `Read`, `Glob`, or `Grep`.** Read-only tools already run without
approval inside the working directory and additional directories,[^4] so
`Read(*)` adds nothing there and grants the rest of the filesystem, including
`~/.aws` and `~/.ssh`.

**Narrow git mutations.** `Bash(git *)` matches every subcommand and every
option before it, including `git -c core.fsmonitor=<script> diff`, which runs
a program of the caller's choosing.[^4] Allow read-only subcommands; route
`add`, `commit`, `checkout`, and `push` through ask rules.

### Ask Rules for Mutation and Network

Commands that change history or reach the network **SHOULD** prompt rather
than run unattended:

```json
{
  "permissions": {
    "ask": [
      "Bash(git add *)",
      "Bash(git commit *)",
      "Bash(git checkout *)",
      "Bash(git push *)",
      "Bash(npm install *)",
      "Bash(npx *)",
      "Bash(curl *)",
      "Bash(wget *)",
      "Bash(ssh *)"
    ]
  }
}
```

Argument-level Bash patterns are fragile — `Bash(curl https://github.com/ *)`
misses `curl -X GET`, a redirect, or `URL=… && curl $URL` — so gate the tool
and use `WebFetch(domain:example.com)` for reviewed domains instead of trying
to constrain URLs inside a shell rule.[^4]

### Doctrine's Standard Denylist

Secret material **MUST** be denied for reads as well as edits:

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
      "Read(.env)",
      "Read(.env.*)",
      "Read(**/secrets/**)",
      "Read(**/*secret*)",
      "Read(**/*password*)",
      "Read(**/*credential*)",
      "Read(**/*token*)",
      "Read(**/*.pem)",
      "Read(**/*.key)",
      "Read(**/id_rsa*)",
      "Read(~/.aws/**)",
      "Read(~/.ssh/**)",
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

#### Why

A `Read` deny rule blocks Claude's file tools, the file commands Claude Code
recognises in Bash such as `cat`, `head`, and `sed`, and Bash redirection
targets. It also blocks Edit from v2.1.208 and Write from v2.1.228, but it
never covers NotebookEdit, so keep the paired `Edit` denies.[^4] Bare
filenames follow gitignore semantics: `Read(.env)` and `Read(**/.env)` are
equivalent and match at any depth under the current directory.[^4]

Permission rules are not an OS boundary. They do not constrain a subprocess
that opens a file itself — a Python or Node script Claude runs reads
`~/.aws/credentials` regardless of any `Read` deny. Pair this policy with the
sandbox, which enforces filesystem and network limits at the OS level.[^5]

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
      "url": "https://mcp.slack.com/mcp"
    },
    "playwright": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@playwright/mcp@0.0.80", "--headless", "--isolated"]
    }
  }
}
```

Every entry **MUST** declare a `type`. Claude Code reads an entry that has a
`url` but no `type` as a stdio server, skips it, and reports the
misconfiguration.[^6]

### Slack

Slack serves MCP over JSON-RPC 2.0 on Streamable HTTP at
`https://mcp.slack.com/mcp`. SSE connections and Dynamic Client Registration
are not supported.[^7] A bare URL is not an authenticated configuration:

- **Registered app.** Every MCP client **MUST** be backed by a registered
  Slack app with a fixed app ID, and only Marketplace-published or internal
  apps may use MCP.[^7] Claude Code is one of Slack's listed partner clients,
  so a team **MAY** connect through it without building an app of its own.
- **Admin approval.** Workspace admins approve MCP clients through the
  standard Slack app approval process, and an app's allowed IP ranges apply to
  MCP traffic too.[^7]
- **Confidential OAuth.** A client of your own authenticates with its
  `client_id` and `client_secret` against
  `https://slack.com/oauth/v2_user/authorize` and
  `https://slack.com/api/oauth.v2.user.access`, or discovers them from
  `https://mcp.slack.com/.well-known/oauth-authorization-server`. Desktop
  clients **SHOULD** use PKCE.[^7]
- **Least-privilege scopes.** Grant only the user-token scopes the tools you
  actually call: `search:read.public` to search public messages,
  `channels:history` to read a channel, `chat:write` to post.[^7] A read-only
  workflow **MUST NOT** request write scopes.

```bash
claude mcp add --transport http slack https://mcp.slack.com/mcp
```

Then run `/mcp` inside the session: it runs the OAuth flow for remote servers
and shows each server's connection state.[^6]

### Common MCP Servers

| Server | Purpose | Type |
|--------|---------|------|
| Playwright | Browser automation, screenshots | stdio |
| Slack | Search and post messages | http |
| Sentry | Error logs and debugging | http |
| PostgreSQL | Database queries | stdio |
| GitHub | Issues, PRs, actions | http |

### MCP for Visual Iteration

Browser automation **MUST** use Microsoft's maintained `@playwright/mcp`,
pinned to an exact version. `@anthropic/mcp-puppeteer` does not exist — the
registry returns 404 for it — and the older
`@modelcontextprotocol/server-puppeteer` is marked deprecated on npm, with no
release since `2025.5.12`:

```json
{
  "mcpServers": {
    "playwright": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@playwright/mcp@0.0.80", "--headless", "--isolated"]
    }
  }
}
```

Or add it from the CLI:

```bash
claude mcp add playwright -- npx -y @playwright/mcp@0.0.80 --headless --isolated
```

Then in conversation:

```text
Take a screenshot of http://localhost:3000/login
```

#### Why

**Prerequisite.** `@playwright/mcp` 0.0.80 requires Node.js 18 or newer.[^8]

**Pin the version.** `@playwright/mcp@latest` re-resolves on every start, so a
release can change agent behaviour between two runs of the same task. Pin the
version and bump it deliberately. `--isolated` keeps the browser profile in
memory, and `--headless` overrides the headed default.[^8]

**MCP or CLI.** Microsoft notes that CLI invocations exposed as Skills are
more token-efficient for coding agents, because they avoid loading large tool
schemas and accessibility trees into context, and keeps MCP for work that
benefits from persistent browser state and iterative reasoning over page
structure, such as exploratory automation and self-healing tests.[^8] Visual
iteration is that second case, so this guide configures MCP; a team whose
browser work is scripted **SHOULD** compare the pinned Playwright CLI Skill.

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

Long sessions **MUST** use the same checked Stop hook as
[Stop: Verify Completion](#stop-verify-completion) — one script, one exit-code
contract, one attempt budget:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/verify-complete.sh",
            "args": []
          }
        ]
      }
    ]
  }
}
```

Auto-resume is bounded from both ends: the script stops blocking after its
own attempt budget, and Claude Code ends the turn after eight consecutive
blocks whatever the hook returns.[^3] A hook that blocks on a failure it
cannot resolve wastes those eight turns and then stops anyway, so keep the
script's budget well below the cap.

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

Doctrine provides standard Claude Code configurations. Both sync paths
**MUST** use `scripts/sync-claude-config.sh`, the one implementation this
guide tests.

### Manual Sync

```bash
# Clone Doctrine once
git clone https://github.com/agh/doctrine.git ~/.doctrine

# Install into the current project
~/.doctrine/scripts/sync-claude-config.sh .
```

The script replaces `.claude/agents`, `.claude/commands`, `.claude/skills`,
and `.claude/infrastructure` from Doctrine, installs `.claude/settings.json`
only when the project has none, and then verifies representative installed
files. Pass `--overwrite-settings` to adopt Doctrine's settings over a
project's own.

Doctrine owns those four directories: the sync deletes each one before
reinstalling it, so anything a project keeps there is removed. Claude Code
loads project subagents from `.claude/agents/` and personal ones from
`~/.claude/agents/`,[^9] so keep project-specific agents and commands in the
user directory, contribute them to Doctrine, or install them from your own
source directory in a step that runs after the sync.

#### Why

**`cp -r configs/claude/ ./.claude/` does not install a usable configuration.**
In the Doctrine checkout, `configs/claude/agents` and
`configs/claude/commands` are symlinks to `../../agents` and `../../commands`.
GNU `cp -r` copies the links verbatim, so the target project gets
`.claude/agents -> ../../agents`, which resolves outside the project and does
not exist; `test -e .claude/agents` fails. The script passes `-L` and explicit
per-component destinations, so both arrive as real directories of files.

**The same command behaves differently when `.claude` already exists.** With
GNU `cp`, a directory operand copied into an existing directory lands inside
it: the tree appears at `.claude/claude/`, the project's `.claude/settings.json`
is left untouched, and Claude Code loads none of the new configuration while
the sync still reports success. macOS `cp` instead merges the contents and
overwrites the project's `settings.json`. The script names every source and
destination path explicitly, so fresh and existing projects get the same
result on both platforms.

**Verify what was installed, not what was copied.** The script exits non-zero
unless `.claude/settings.json`, `.claude/agents/code/reviewer.md`,
`.claude/commands/code.md`, and `.claude/skills/README.md` exist as regular
files at the paths Claude Code loads.[^9]

### GitHub Action for Auto-Sync

Use the maintained template at
[`.github/workflows/sync-doctrine.yml`](../../configs/github/workflows/sync-doctrine.yml)
rather than hand-rolling a workflow. Copy it into your project's
`.github/workflows/`, then customise `SYNC_PATHS`:

```yaml
# .github/workflows/sync-doctrine.yml
name: Sync Doctrine Configs

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly
  workflow_dispatch:

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Fetch Doctrine configs
        run: |
          curl -sL https://github.com/agh/doctrine/archive/main.tar.gz | tar xz
          doctrine-main/scripts/sync-claude-config.sh .
          rm -rf doctrine-main

      - name: Create PR if changes
        uses: peter-evans/create-pull-request@v5
        with:
          title: "chore: sync Claude configs from Doctrine"
          commit-message: "chore: sync Claude configs from Doctrine"
          branch: sync-doctrine-configs
          body: |
            Automated sync of Claude Code configs from [Doctrine](https://github.com/agh/doctrine).
```

### Version Pinning

Pin to a release tag so config changes arrive on your schedule rather than
upstream's. **The source paths differ by release**: `agents/` and `commands/`
sit at the repository root only in releases *after* v2.11.0; in v2.11.0 and
earlier they live under `configs/claude/`. Match `SYNC_PATHS` to the release
you pin, or the sync step reports `Source not found` and copies nothing:

```yaml
- name: Fetch Doctrine configs (pinned to v2.11.0)
  run: |
    curl -sL https://github.com/agh/doctrine/archive/refs/tags/v2.11.0.tar.gz | tar xz
    doctrine-2.11.0/scripts/sync-claude-config.sh .
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
[^3]: [Claude Code Hooks Reference](https://code.claude.com/docs/en/hooks) — Hook events, exit codes, and `Stop` input fields
[^4]: [Claude Code Permissions](https://code.claude.com/docs/en/permissions) — Rule syntax, evaluation order, and tool-specific matching
[^5]: [Claude Code Sandboxing](https://code.claude.com/docs/en/sandboxing) — OS-level filesystem and network isolation for Bash
[^6]: [Claude Code MCP Guide](https://code.claude.com/docs/en/mcp) — Server transports, configuration, and OAuth authentication
[^7]: [Slack MCP Server](https://docs.slack.dev/ai/slack-mcp-server/) — Endpoint, app registration, OAuth, and scopes
[^8]: [Playwright MCP](https://github.com/microsoft/playwright-mcp) — Configuration flags, Node.js requirement, and the CLI/Skills trade-off
[^9]: [Claude Code Subagents](https://code.claude.com/docs/en/sub-agents) — Where Claude Code loads project and personal subagent files
