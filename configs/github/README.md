# GitHub Workflow Templates

> [Doctrine](../../README.md) > Configs > GitHub

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

Reusable GitHub Actions workflows for projects that adopt Doctrine. These are
**templates**: they live here rather than in `.github/workflows/` so GitHub
cannot schedule them inside Doctrine itself.

## Quick Reference

| Template | Purpose | Trigger | Needs |
| -------- | ------- | ------- | ----- |
| [`workflows/sync-doctrine.yml`](workflows/sync-doctrine.yml) | Mirror Doctrine's agents, commands and Claude settings into your project | Weekly cron, manual | `contents: write`, `pull-requests: write` |
| [`workflows/doc-sync.yml`](workflows/doc-sync.yml) | Remind pull-request authors which documents a source change touches | Pull requests touching `src/`, `lib/`, `app/` | `pull-requests: write` |

## Why these are templates, not live workflows

A workflow placed in `.github/workflows/` runs in the repository that holds
it. `sync-doctrine.yml` previously sat in Doctrine's own workflow directory
and therefore ran against Doctrine every Monday, copying `configs/claude/*`
into a second `.claude/` tree and attempting a self-referential pull request.
`doc-sync.yml` triggers on `src/**`, `lib/**` and `app/**`, none of which
exist in a documentation repository.

Templates **MUST NOT** be placed in `.github/workflows/` of the repository
that publishes them. Copy them into the consuming project instead.

## Adopting `sync-doctrine.yml`

Keeps a downstream project's `.claude/` tree in step with Doctrine.

### Install

```bash
mkdir -p .github/workflows
curl -fsSL -o .github/workflows/sync-doctrine.yml \
  https://raw.githubusercontent.com/agh/doctrine/main/configs/github/workflows/sync-doctrine.yml
```

### Configure

Edit the `SYNC_PATHS` block. Each line is `source:destination`, where
`source` is a path inside Doctrine and `destination` a path in your project:

```yaml
SYNC_PATHS: |
  agents:.claude/agents
  commands:.claude/commands
  configs/claude/settings.json:.claude/settings.json
```

Directories are mirrored with `rsync --archive --delete`. A destination
directory **MUST** contain only synced content: anything removed upstream is
removed locally, so project-specific files placed there **WILL** be deleted.
Keep local additions in a sibling directory.

### Repository settings

The workflow opens a pull request, so the project **MUST** enable
**Settings → Actions → General → Allow GitHub Actions to create and approve
pull requests**. Without it `peter-evans/create-pull-request` fails with a
permissions error — this is what caused all fourteen historical failures of
this workflow in Doctrine.

Pull requests authored with the default `GITHUB_TOKEN` deliberately do not
trigger further workflow runs. If the sync pull request must run your CI, set
a `DOCTRINE_SYNC_TOKEN` secret holding a fine-grained personal access token
with `contents: write` and `pull-requests: write` on the project; the
template prefers it when present.

### Dry runs

Run the workflow manually with **Preview changes without creating a pull
request** ticked. The dry run reports `git status --porcelain` to the job
summary and then restores the workspace. `dry_run` is a Boolean input, so the
conditions compare `inputs.dry_run == true`; comparing against the string
`'true'` — as the original did — is always false and lets a preview run open
a pull request anyway.

## Adopting `doc-sync.yml`

Posts one comment per pull request listing the documents that correspond to
the changed source files.

### Install

```bash
mkdir -p .github/workflows
curl -fsSL -o .github/workflows/doc-sync.yml \
  https://raw.githubusercontent.com/agh/doctrine/main/configs/github/workflows/doc-sync.yml
```

### Configure

Set `DOC_ROOT` to the directory holding your prose documentation, and adjust
the `paths` filter to match your source layout. The mapping strips any
extension, so `lib/parser.py` maps to `docs/lib/parser.md`; the original
template assumed TypeScript and produced `docs/lib/parser.py.md`.

### Scope

This check is advisory. It **MUST NOT** be treated as proof that
documentation is current — it only reports which documents exist for the
files that changed. It never fails the build.

## Pinning policy

Every `uses:` reference in these templates is pinned to a full commit SHA
with the release tag in a trailing comment, per
[GitHub's secure-use guidance](https://docs.github.com/en/actions/reference/security/secure-use-reference).
A tag is a mutable pointer; `tj-actions/changed-files` had its tags
retargeted during the March 2025 supply-chain incident, which a SHA pin would
have contained.

Doctrine's Dependabot configuration only scans `.github/workflows/`. These
templates are **not** updated automatically: when the pins in
`.github/workflows/` change, update them here in the same commit.

Current pins:

| Action | Version | SHA |
| ------ | ------- | --- |
| `actions/checkout` | v7.0.1 | `3d3c42e5aac5ba805825da76410c181273ba90b1` |
| `actions/github-script` | v9.0.0 | `3a2844b7e9c422d3c10d287c895573f7108da1b3` |
| `peter-evans/create-pull-request` | v8.1.1 | `5f6978faf089d4d20b00c7766989d076bb2fc7f1` |
| `tj-actions/changed-files` | v47.0.6 | `9426d40962ed5378910ee2e21d5f8c6fcbf2dd96` |

## See Also

- [CI/CD Style Guide](../../guides/process/ci.md)
- [GitHub Templates](../../guides/process/github-templates.md)
- [Claude Code Guide](../../guides/ai/claude-code.md)
