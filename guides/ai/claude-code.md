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
| Hook scripts | `.claude/hooks/*.sh` |
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
│   ├── hooks/             # Hook scripts invoked from settings.json
│   │   ├── check-file.sh
│   │   └── verify-complete.sh
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

### Hook Exit Codes

Exit codes decide whether a hook is a gate or a comment. Claude Code treats
exit 2 as the blocking status; every other non-zero code is a **non-blocking
error** that lets the action proceed[^3].

| Exit code | Effect on `PostToolUse` | Effect on `Stop` |
|-----------|-------------------------|------------------|
| `0` | Success. stderr goes to the debug log only; Claude never sees it | Claude stops |
| `1` (or any other non-zero) | Non-blocking error, stderr not shown to Claude | Claude stops anyway |
| `2` | Tool already ran, but Claude sees stderr | Blocks the stop; stderr becomes the reason to continue |

Hooks **MUST NOT** end a check with `|| true` and **MUST NOT** rely on exit
code 1 to gate anything.

#### Why

`|| true` replaces the check's status with 0, and exit 1 is non-blocking, so
both turn a failed check into a silent success:

```bash
# Don't: both of these report success to Claude Code
sh -c 'npm run lint || true'        # exits 0 even when lint fails
sh -c 'npm test && npm run lint'    # exits 1, which does not block Stop

# Do: report the reason on stderr and exit 2
printf 'lint failed on src/auth.ts\n' >&2
exit 2
```

### PostToolUse: Auto-Format

**MUST** auto-format after file changes. This catches the "last 10%" of style
issues, and **MUST** surface a formatter failure to Claude instead of
discarding it:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/check-file.sh",
            "args": ["npm", "run", "format", "--", "--write"]
          }
        ]
      }
    ]
  }
}
```

`check-file.sh` runs the command it is given against the file Claude just
wrote, and reports a failure the only way `PostToolUse` can — stderr plus
exit 2:

```bash
#!/usr/bin/env bash
# .claude/hooks/check-file.sh - run "<argv> <edited file>" after Write or Edit.
set -uo pipefail

file=$(jq -r '.tool_input.file_path // empty')
[ -n "$file" ] || exit 0

if ! output=$("$@" "$file" 2>&1); then
  printf '%s failed on %s:\n%s\n' "$*" "$file" "$(tail -n 20 <<<"$output")" >&2
  exit 2
fi

exit 0
```

Make it executable with `chmod +x .claude/hooks/check-file.sh`.

#### Why

`args` selects Claude Code's exec form, so the script path and each argument
are passed verbatim with no shell tokenisation — the correct form whenever a
command references a path placeholder such as `${CLAUDE_PROJECT_DIR}`[^3].
Reading `.tool_input.file_path` into a quoted variable keeps paths containing
spaces intact. Truncating to the last 20 lines keeps the feedback short enough
to be actionable.

### PostToolUse: Auto-Lint

**SHOULD** lint after file changes, using the same script:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/check-file.sh",
            "args": ["npm", "run", "lint:file", "--"]
          }
        ]
      }
    ]
  }
}
```

A per-file lint hook is a fast signal, not proof that the change is clean.
The whole-change gate below **MUST** still run.

### Stop: Verify Completion

**MUST** verify before accepting completion on important tasks. A `Stop` hook
that runs the gate commands directly does not work: the shell reports exit 1
on failure, which Claude Code treats as non-blocking. Call a script that exits
2 instead:

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

```bash
#!/usr/bin/env bash
# .claude/hooks/verify-complete.sh - Stop hook completion gate.
set -uo pipefail

hook_input=$(cat)

# Claude Code overrides the hook after 8 consecutive blocks; stop asking
# once a previous block already resumed the turn.
if [ "$(jq -r '.stop_hook_active // false' <<<"$hook_input")" = "true" ]; then
  exit 0
fi

failures=""

run_gate() {
  local label=$1
  shift
  local output
  if ! output=$("$@" 2>&1); then
    failures+="${label} failed:"$'\n'"$(tail -n 20 <<<"$output")"$'\n\n'
  fi
}

run_gate "npm test" npm test
run_gate "npm run lint" npm run lint
run_gate "npm run typecheck" npm run typecheck

if [ -n "$failures" ]; then
  printf '%s' "$failures" >&2
  exit 2
fi

exit 0
```

#### Why

Every gate runs, so one failing suite does not hide the next; the stderr text
becomes the reason Claude is shown for continuing. The `stop_hook_active`
check prevents a gate that can never pass from looping, and Claude Code caps
continuations at eight consecutive blocks regardless[^3]. A Stop hook is
therefore a strong gate, **not** a guarantee that Claude never stops early.

Hooks **MAY** instead exit 0 and print blocking JSON on stdout; Claude
receives the `reason` exactly as it receives exit-2 stderr[^3]:

```json
{
  "decision": "block",
  "reason": "npm test failed: 2 failing in src/auth.test.ts"
}
```

Make the script executable with `chmod +x .claude/hooks/verify-complete.sh`.
A gate whose script is missing or not executable exits 127, which Claude Code
reports as a non-blocking error — the session stops with the gate silently
disabled[^3].

For a completion condition that applies to one session rather than every
session in the project, **SHOULD** use `/goal`[^4] instead of editing
`settings.json`.

### Hook Input

Hook commands receive a JSON payload on **stdin** (there are no
`$CLAUDE_*` environment variables for tool data). Extract fields with `jq`:

| JSON field | Value | Event |
|------------|-------|-------|
| `.tool_input.file_path` | Path to file being written/edited | `PostToolUse` |
| `.tool_name` | Name of tool being used | `PreToolUse`, `PostToolUse` |
| `.stop_hook_active` | `true` when a stop hook already resumed the turn | `Stop` |

Example: `file=$(jq -r '.tool_input.file_path // empty')`

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
      "args": ["-y", "@playwright/mcp@0.0.80"]
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

**SHOULD** use Claude Code's built-in Chrome integration[^5] for screenshots
and browser checks, because it needs no MCP server and drives the browser you
are already signed into:

```bash
claude --chrome
```

Prerequisites **MUST** be met before relying on it[^5]:

- Chrome, Edge, or another Chromium browser, plus the Claude in Chrome
  extension 1.0.36 or later
- Sign-in with `/login` on a direct Anthropic plan (Pro, Max, Team, or
  Enterprise) — API-key and `claude setup-token` sessions keep the
  integration off
- Not available under Windows Subsystem for Linux

Where those prerequisites do not hold, **SHOULD** use Microsoft's
`@playwright/mcp`, pinned to an exact version[^6]:

```json
{
  "mcpServers": {
    "playwright": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@playwright/mcp@0.0.80", "--isolated", "--headless"]
    }
  }
}
```

#### Why

`@anthropic/mcp-puppeteer` does not exist on the public registry, and
`@modelcontextprotocol/server-puppeteer` is marked deprecated ("Package no
longer supported")[^7], so both fail before browser automation starts.
`@playwright/mcp` 0.0.80 is the current release[^6] and requires Node.js 18 or
newer.

Pin the version: `@latest` re-resolves on every launch, so an unpinned `npx`
line runs whatever was published since the config was reviewed. `--isolated`
keeps the browser profile in memory, so a session cannot inherit or persist
cookies from a previous run, and lets several clients share one workspace
without fighting over the persistent profile[^6].

The server drives a real browser with network access. Treat any page it visits
as untrusted input: point it at your own development server, and **MUST NOT**
give it credentials that matter more than the task.

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

Stop hooks verify completion and auto-resume when criteria are not met. Use
the same enforcing gate as [Stop: Verify Completion](#stop-verify-completion)
— a plain `npm test && npm run lint` command exits 1 on failure, which Claude
Code treats as non-blocking:

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

Auto-resume is bounded: Claude Code ends the turn after eight consecutive
blocks[^3]. A long-running session **MUST NOT** be planned on the assumption
that the hook resumes indefinitely.

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

# Copy the contents of configs/claude into .claude, following the
# agents and commands symlinks
mkdir -p ./.claude
cp -rL ~/.doctrine/configs/claude/. ./.claude/
```

#### Why

Two details make this recipe work on GNU coreutils, which is what
`ubuntu-latest` runners use:

- **`configs/claude/.` rather than `configs/claude/`** — with GNU `cp -r`, a
  source directory copied into an existing destination is nested inside it, so
  `cp -r configs/claude/ ./.claude/` puts `settings.json` at
  `.claude/claude/settings.json` on the second run. The `/.` form copies the
  directory's *contents* and behaves identically whether `.claude` already
  exists or not.
- **`-L`** — `configs/claude/agents` and `configs/claude/commands` are
  relative symlinks into the Doctrine repository root. GNU `cp -r` copies them
  as symlinks, and they dangle at the destination, so no agent or command file
  is installed. `-L` dereferences them and materialises the real trees.

Verify a sync with the files the links are supposed to provide:

```bash
test -f .claude/settings.json
test -f .claude/agents/code/architect.md
test -f .claude/commands/code.md
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

#### Why a plain copy fails

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
          mkdir -p ./.claude
          cp -rL doctrine-main/configs/claude/. ./.claude/
          test -f .claude/settings.json
          test -f .claude/agents/code/architect.md
          test -f .claude/commands/code.md
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
    mkdir -p ./.claude
    cp -rL doctrine-2.11.0/configs/claude/. ./.claude/
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
[^3]: [Hooks reference](https://code.claude.com/docs/en/hooks) — Exit codes, `stop_hook_active`, the eight-block continuation cap, exec form vs shell form
[^4]: [Keep Claude working toward a goal](https://code.claude.com/docs/en/goal) — Session-scoped completion conditions with `/goal`
[^5]: [Use Claude Code with Chrome](https://code.claude.com/docs/en/chrome) — Built-in browser integration and its prerequisites
[^6]: [`@playwright/mcp` registry metadata](https://registry.npmjs.org/@playwright/mcp/latest) — Version 0.0.80, published 2026-09-01; Node.js 18+
[^7]: [`@modelcontextprotocol/server-puppeteer` registry metadata](https://registry.npmjs.org/@modelcontextprotocol/server-puppeteer/latest) — `deprecated: "Package no longer supported"`
