# GitHub Skill

Provides access to GitHub repositories, issues, pull requests, and releases for
development workflow automation.

## Overview

| Attribute | Value |
| --------- | ----- |
| **Category** | Communication / Development |
| **MCP Server** | `@modelcontextprotocol/server-github` |
| **Default Access** | readonly |
| **Risk Level** | Low (readonly) / Medium (read-write) |

## MCP Configuration

### Basic Setup

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

### With Specific Repository Scope

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-github",
        "--repo", "owner/repo"
      ],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

## Access Levels

| Level | Token Scopes | Permissions | Use Case |
| ----- | ------------ | ----------- | -------- |
| `readonly` | `repo:status`, `public_repo` | Read issues, PRs, releases | Analysis |
| `read-write` | `repo`, `write:discussion` | Create/update issues, PRs | Automation |
| `releases` | `repo`, `write:packages` | Manage releases, packages | Release mgmt |
| `admin` | `repo`, `admin:org` | Full repository control | Rarely needed |

### Creating Tokens

1. Go to GitHub -> Settings -> Developer Settings -> Personal Access Tokens
2. Choose "Fine-grained tokens" (recommended) or "Classic"
3. Select minimal required scopes:

**For readonly analysis:**

```text
Repository access: Public Repositories (or specific repos)
Permissions:
  - Issues: Read-only
  - Pull requests: Read-only
  - Contents: Read-only
  - Metadata: Read-only
```

**For release management:**

```text
Repository access: Select repositories
Permissions:
  - Issues: Read and write
  - Pull requests: Read and write
  - Contents: Read and write
  - Metadata: Read-only
```

## Capabilities

| Capability | Access | Description |
| ---------- | ------ | ----------- |
| `list_repos` | readonly | List accessible repositories |
| `get_repo` | readonly | Get repository details |
| `list_issues` | readonly | List issues with filters |
| `get_issue` | readonly | Get issue details and comments |
| `list_prs` | readonly | List pull requests |
| `get_pr` | readonly | Get PR details, diff, reviews |
| `list_releases` | readonly | List releases |
| `create_issue` | read-write | Create new issue |
| `update_issue` | read-write | Update issue, add labels |
| `create_pr` | read-write | Create pull request |
| `create_release` | releases | Create GitHub release |
| `merge_pr` | read-write | Merge pull request |

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

GitHub API has rate limits:

- Authenticated: 5,000 requests/hour
- Search API: 30 requests/minute

Agents **SHOULD**:

- Cache responses where appropriate
- Use conditional requests (If-None-Match)
- Batch operations when possible
- Implement exponential backoff on 429 responses

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

```yaml
# .github/workflows/release.yml
name: Release
on:
  push:
    tags: ['v*']

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Generate Release Notes
        run: |
          # Agent generates changelog from PRs
          claude /changelog --since $(git describe --tags --abbrev=0 HEAD^)

      - name: Create Release
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh release create ${{ github.ref_name }} \
            --title "${{ github.ref_name }}" \
            --notes-file RELEASE_NOTES.md
```

### PR Analysis

```yaml
# .github/workflows/pr-analysis.yml
name: PR Analysis
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Analyze PR
        run: |
          # Agent reviews PR for issues
          claude /review --pr ${{ github.event.pull_request.number }}
```
