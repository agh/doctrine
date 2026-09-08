# GitHub Skill

Provides access to GitHub repositories, issues, pull requests, and releases for
development workflow automation.

## Overview

| Attribute | Value |
| --------- | ----- |
| **Category** | Communication / Development |
| **MCP Server** | GitHub MCP Server (remote `https://api.githubcopilot.com/mcp/`, or `ghcr.io/github/github-mcp-server:v1.12.0`) |
| **Default Access** | readonly (`--read-only`) |
| **Risk Level** | Low (readonly) / Medium (read-write) |

## MCP Configuration

Agents **MUST NOT** use `@modelcontextprotocol/server-github`. npm marks it
`"Package no longer supported"` at `2025.4.8`, and its source is archived in
`modelcontextprotocol/servers-archived`. Use
[GitHub's own MCP server](https://github.com/github/github-mcp-server), pinned
at `v1.12.0`.

Its token variable is `GITHUB_PERSONAL_ACCESS_TOKEN`. `GITHUB_TOKEN` is not
read, so a configuration that sets only `GITHUB_TOKEN` authenticates as nobody.

### Basic Setup (remote server, recommended)

```json
{
  "mcpServers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/"
    }
  }
}
```

The remote endpoint performs an OAuth flow, so no token is stored on disk.

**Why**: an OAuth grant is revocable from GitHub's UI and is bound to the user's
own access, whereas a long-lived PAT in a settings file outlives the session and
is readable by anything running as that user.

### Local Setup (pinned container)

```json
{
  "mcpServers": {
    "github": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
        "-e", "GITHUB_READ_ONLY",
        "-e", "GITHUB_TOOLSETS",
        "ghcr.io/github/github-mcp-server:v1.12.0"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PAT}",
        "GITHUB_READ_ONLY": "1",
        "GITHUB_TOOLSETS": "repos,issues,pull_requests"
      }
    }
  }
}
```

### Restricting Scope

There is no `--repo` flag. The server rejects it and exits non-zero:

```console
$ docker run --rm ghcr.io/github/github-mcp-server:v1.12.0 stdio --repo owner/repo
Error: unknown flag: --repo
```

Repository scope is a property of the **credential**, not of the server
invocation, so there is no flag that could provide it.

Restrict access with the controls that exist:

| Control | Flag | Environment variable | Effect |
| ------- | ---- | -------------------- | ------ |
| Read-only | `--read-only` | `GITHUB_READ_ONLY=1` | Registers only read tools |
| Toolsets | `--toolsets` | `GITHUB_TOOLSETS` | Limits which tool groups load |
| Individual tools | `--tools` | — | Adds named tools to the selection |
| Lockdown | `--lockdown-mode` | `GITHUB_LOCKDOWN_MODE=1` | Filters untrusted public content |

Repository restriction **MUST** come from a fine-grained token scoped to the
selected repositories, or from a GitHub App installed on only those
repositories.

Read-only mode takes priority: write tools stay unregistered even when
`--tools` names one. Lockdown mode is a best-effort content filter against
prompt injection from public repository content, not an authorisation boundary —
it does not change what the credential can read or write.

## Access Levels

Fine-grained tokens and GitHub Apps express access as **permissions** with a
read or write level. Classic tokens express it as **scopes**, which are coarser.
The two vocabularies **MUST NOT** be mixed in one row.

| Level | Fine-grained permissions | Use Case |
| ----- | ------------------------ | -------- |
| `readonly` | Metadata: Read, Contents: Read, Issues: Read, Pull requests: Read | Analysis |
| `read-write` | above, plus Issues: Write, Pull requests: Write | Automation |
| `releases` | Metadata: Read, Contents: **Write** | Release mgmt |
| `admin` | Administration: Write (organisation or repository) | Rarely needed |

Releases are created through the Contents permission. `write:packages` is a
classic scope for publishing **packages**; it does not create releases, and
attaching it to a release token grants registry write access that release
management does not need.

There is no classic scope that grants read-only access to a private repository.
`repo` is all-or-nothing, and `public_repo` grants **write** access to public
repositories, so the pair `repo:status` + `public_repo` is not a readonly
credential.

**Why**: an agent credential should fail closed. A scope that silently carries
write access turns a review agent into an agent that can push.

### Creating Tokens

1. Prefer a **GitHub App** for anything long-lived. Installation tokens expire
   after one hour, are scoped to the installed repositories, and are not tied to
   a leaving employee's account.
2. Otherwise go to GitHub -> Settings -> Developer Settings -> Personal Access
   Tokens -> **Fine-grained tokens**.
3. Select the specific repositories, never "All repositories".
4. Set an expiry. 90 days or less is **REQUIRED**.

**For readonly analysis:**

```text
Repository access: Only select repositories
Permissions:
  - Metadata: Read-only        (mandatory for every fine-grained token)
  - Contents: Read-only
  - Issues: Read-only
  - Pull requests: Read-only
```

**For release management:**

```text
Repository access: Only select repositories
Permissions:
  - Metadata: Read-only
  - Contents: Read and write   (creates tags and releases)
  - Issues: Read and write
  - Pull requests: Read and write
```

## Capabilities

Tool names below are those registered by `github-mcp-server` v1.12.0. The
"Access" column shows the lowest level that registers the tool; everything
marked read-write or releases stays unregistered under `--read-only`.

| Capability | Toolset | Access | Description |
| ---------- | ------- | ------ | ----------- |
| `search_repositories` | `repos` | readonly | Find accessible repositories |
| `get_file_contents` | `repos` | readonly | Read a file or directory |
| `list_issues` | `issues` | readonly | List issues with filters |
| `issue_read` | `issues` | readonly | Issue detail, comments, sub-issues |
| `list_pull_requests` | `pull_requests` | readonly | List pull requests |
| `pull_request_read` | `pull_requests` | readonly | PR detail, diff, files, reviews |
| `list_releases` | `repos` | readonly | List releases |
| `get_latest_release` | `repos` | readonly | Newest published release |
| `list_commits` | `repos` | readonly | Commit history for a branch |
| `actions_list` | `actions` | readonly | Workflows, runs and job status |
| `issue_write` | `issues` | read-write | Create and update issues |
| `create_pull_request` | `pull_requests` | read-write | Open a pull request |
| `merge_pull_request` | `pull_requests` | read-write | Merge a pull request |
| `push_files` | `repos` | releases | Commit files, e.g. changelog updates |

There is no `create_release` tool. Release creation goes through the REST API
or `gh release create`; see [Release Workflow](#release-workflow).

## Example Usage

### Release Analysis

```markdown
Analyze the last 10 releases:
- Release frequency
- Breaking changes (major versions)
- Contributors per release
- Time between releases
```

### PR Review Status

```markdown
List all open PRs that:
- Have been open > 7 days
- Have no reviews
- Are not drafts
```

### Issue Triage

```markdown
Find issues labeled "bug" that:
- Were created in the last 30 days
- Have no assignee
- Have more than 3 comments (high engagement)
```

### Changelog Generation

```markdown
For version 1.2.0:
1. Find all PRs merged since v1.1.0 tag
2. Categorize by conventional commit type
3. Generate changelog entries
4. Create release with generated notes
```

### CI Status Check

```markdown
Check the status of the latest commit on main:
- All required checks passing?
- Any failed workflows?
- Time since last successful deploy?
```

## Agents That Use This Skill

| Agent | Access | Purpose |
| ----- | ------ | ------- |
| `ops/release-manager` | read-write | Create releases, manage changelog PRs |
| `ops/changelog` | readonly | Analyze PRs for release notes |
| `code/reviewer` | readonly | Fetch PR diff for review |
| `security/supply-chain-auditor` | readonly | Analyze dependency PRs |

## Graceful Degradation

When GitHub is unavailable, agents should:

| Scenario | Fallback |
| -------- | -------- |
| PR list | Use local git branches |
| Release history | Parse git tags locally |
| Issue context | Ask user for context |
| CI status | Check local test results |

## Security Considerations

### Token Security

- **MUST** use fine-grained tokens over classic tokens
- **MUST** scope tokens to specific repositories when possible
- **MUST** set token expiration (90 days recommended)
- **MUST NOT** commit tokens to repositories
- **SHOULD** use GitHub App tokens for production automation

### Rate Limiting

GitHub applies several independent limits. The values below were read from
`GET /rate_limit` on an authenticated token:

| Resource | Limit | Applies to |
| -------- | ----- | ---------- |
| `core` | 5,000/hour | REST, user-to-server and PAT requests |
| `graphql` | 5,000/hour | GraphQL API |
| `search` | 30/minute | Search API |
| `code_search` | 10/minute | Code search |
| `GITHUB_TOKEN` in Actions | 1,000/hour per repository | Workflow requests |

GitHub App installation tokens scale with installation size rather than using a
flat 5,000, so an App is also the answer when a fixed hourly ceiling is the
constraint.

Separately, **secondary rate limits** cap concurrency, per-minute request bursts
and content-creation actions such as opening issues or comments. They are not
reported by `GET /rate_limit` and they return `403` or `429`.

Agents **MUST**:

- Read `retry-after` first, then `x-ratelimit-reset`, and wait the stated time.
  Retrying sooner extends the block.
- Treat `403` and `429` with `x-ratelimit-remaining: 0` as rate limiting, not
  as authorisation failure.
- Use conditional requests (`If-None-Match`); `304` responses do not count
  against the primary limit.
- Serialise writes rather than issuing them concurrently.

**Why**: secondary limits punish retry storms. A client that backs off on the
server's own schedule recovers; one that retries immediately is blocked longer.

### API Versioning

The REST API is versioned by date. `GET /versions` currently lists
`2026-03-10` and `2022-11-28`, and a request that omits the header is served
`2022-11-28`, echoed back as `x-github-api-version-selected`.

```bash
curl -sS -H "X-GitHub-Api-Version: 2026-03-10" \
  -H "Authorization: Bearer $GITHUB_PAT" \
  https://api.github.com/repos/OWNER/REPO
```

Agents **SHOULD** send `X-GitHub-Api-Version` explicitly and assert the echoed
`x-github-api-version-selected`, so that a change to the server default cannot
alter response shapes silently.

### Sensitive Operations

| Operation | Risk | Mitigation |
| --------- | ---- | ---------- |
| Merge PR | Medium | Require CI passing, review approval |
| Create release | Medium | Validate version, changelog |
| Delete branch | High | Human approval required |
| Force push | Critical | Never allow via agent |

### Webhook Secrets

If using GitHub webhooks to trigger agents:

- **MUST** validate webhook signatures
- **MUST** use HTTPS endpoints
- **SHOULD** restrict to specific events
- **MUST** rotate webhook secrets regularly

## Integration Patterns

### Release Workflow

Every file a step reads **MUST** be produced by an earlier step in the same job.
This workflow writes `RELEASE_NOTES.md` before `gh release create` consumes it.

```yaml
# .github/workflows/release.yml
name: Release
on:
  push:
    tags: ['v*']

permissions:
  contents: write

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
        with:
          fetch-depth: 0

      - name: Generate release notes
        id: notes
        run: |
          set -euo pipefail
          previous=$(git describe --tags --abbrev=0 "${GITHUB_REF_NAME}^" 2>/dev/null || true)
          if [ -n "$previous" ]; then
            range="${previous}..${GITHUB_REF_NAME}"
          else
            range="${GITHUB_REF_NAME}"
          fi
          {
            echo "## Changes"
            echo
            git log --no-merges --pretty='- %s (%h)' "$range"
          } > RELEASE_NOTES.md
          test -s RELEASE_NOTES.md

      - name: Create release
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          set -euo pipefail
          gh release create "${GITHUB_REF_NAME}" \
            --title "${GITHUB_REF_NAME}" \
            --notes-file RELEASE_NOTES.md
```

`gh` is preinstalled on GitHub-hosted runners and reads `GH_TOKEN`, so no
install step is needed. `set -euo pipefail` and the `test -s` guard stop the
release being published from an empty notes file.

Where the notes should be written by an agent rather than by `git log`, use the
official action and give it credentials; a bare `claude` command fails with
`command not found` because no such binary exists on the runner.

```yaml
      - name: Draft release notes with Claude
        uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          prompt: |
            Summarise the commits in this release into RELEASE_NOTES.md,
            grouped by conventional commit type.
          claude_args: '--allowed-tools Bash(git log:*),Write'
```

### PR Analysis

```yaml
# .github/workflows/pr-analysis.yml
name: PR Analysis
on:
  pull_request:
    types: [opened, synchronize]

permissions:
  contents: read
  pull-requests: write

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
        with:
          fetch-depth: 0

      - name: Analyse PR
        uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          github_token: ${{ secrets.GITHUB_TOKEN }}
          prompt: |
            Review the diff in this pull request and post a summary comment.
```

Workflows triggered by `pull_request` from a fork receive a read-only
`GITHUB_TOKEN` regardless of the `permissions` block, so the comment step will
fail there. Use `pull_request_target` only with an explicit, reviewed checkout
of the base ref; it runs with repository secrets against untrusted code.

**Why**: `permissions` is declared per workflow because repository defaults
differ between organisations. Declaring it makes the job's authority explicit
and independent of a setting the workflow author cannot see.
