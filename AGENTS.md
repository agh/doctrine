# AGENTS.md - Doctrine Style Guide

This file is the canonical instruction file for every coding agent working on
Doctrine. OpenAI Codex and GitHub Copilot read `AGENTS.md` natively; Claude Code
reaches it through `CLAUDE.md`, which contains an `@AGENTS.md` import, and
Gemini CLI through `GEMINI.md`. Edit this file — never the importers.

## Overview

Doctrine is a comprehensive style guide repository covering 13+ programming
languages, frameworks, and AI-assisted development practices. All guides use
[RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119) language to clearly
distinguish requirements from recommendations.

## Commands

| Task | Command |
| ---- | ------- |
| Run every check below | `make check` |
| Lint Markdown | `npx --yes markdownlint-cli2@0.23.2 "**/*.md" "#reference"` |
| Check links | `npx --yes markdown-link-check@3.15.0 --quiet README.md` |
| Validate tool versions | `python3 scripts/validate_versions.py` |
| Check navigation coverage | `python3 scripts/gen_nav.py --check` |
| Regenerate `SUMMARY.md` | `python3 scripts/gen_nav.py` |

`make check` **MUST** pass before every commit. `scripts/gen_nav.py --check`
fails when a guide is missing from `README.md` or from its category
`README.md`, or when either lists a file that no longer exists; run
`python3 scripts/gen_nav.py` after adding or removing a guide to rewrite
`SUMMARY.md`.

## Repository Structure

```text
doctrine/
├── agents/            # 53 agent definitions, grouped by family
│   ├── code/          # Review, performance, accessibility, API, tests
│   ├── docs/          # Documentation planning, writing, review, publishing
│   ├── ops/           # Release management, changelog, deploy, rollback
│   ├── security/      # Threat modelling, compliance, detection, red team
│   ├── system/        # Docker, Ansible, Linux, networking, storage
│   └── test-writer/   # Per-language test generation
├── commands/          # Slash-command definitions (/code, /security, ...)
├── configs/           # Ready-to-copy configuration files
│   ├── agents/        # AGENTS.md.template
│   ├── ansible/       # ansible.cfg, ansible-lint, yamllint, SOPS
│   ├── claude/        # settings.json, skills, infrastructure context
│   ├── cursor/        # .cursorrules.template
│   ├── editorconfig/  # .editorconfig
│   ├── pre-commit/    # .pre-commit-config.yaml
│   └── prettier/      # .prettierrc
├── guides/
│   ├── ai/            # AI-assisted development practices
│   ├── api/           # GraphQL and REST API design
│   ├── design/        # Design systems, components, accessibility, motion
│   ├── docs/          # Documentation standards (Markdown, specifications)
│   ├── frameworks/    # Framework guides (Rails, Django, React, ...)
│   ├── infrastructure/# Operating systems, services, Ansible, Docker
│   ├── languages/     # Language style guides (Python, Go, Rust, ...)
│   └── process/       # Testing, CI, versioning, GitHub templates
├── reference/         # Vendored third-party guides, unmodified
├── scripts/           # Repository validators (gen_nav, validate_versions)
├── AGENTS.md          # Canonical agent instructions (this file)
├── CLAUDE.md          # `@AGENTS.md` import for Claude Code
├── GEMINI.md          # `@./AGENTS.md` import for Gemini CLI
├── README.md          # Landing page with full navigation
├── SUMMARY.md         # Generated navigation index
├── CHANGELOG.md       # Version history (Keep a Changelog format)
└── VERSION            # Current version number
```

## Vendored Reference Payloads

Everything under `reference/` except `reference/security/` is a verbatim
third-party document.

- **MUST NOT** run markdownlint, prettier or any other formatter or auto-fixer
  over `reference/`; the root `.markdownlint-cli2.jsonc` ignores it and CI lints
  with `#reference/**`
- **MUST NOT** apply Doctrine house style (breadcrumbs, RFC 2119 boilerplate,
  `Why` sections) to a payload
- **MUST** record any deliberate correction to upstream text in
  [`reference/ERRATA.md`](reference/ERRATA.md), with the command that
  demonstrates the defect
- **MUST** regenerate the digest register after any payload change:
  `python3 scripts/check_vendored_payloads.py --update`

**Why**: a vendored payload is evidence of what upstream says, so it is only
useful while it is byte-identical to upstream. Commit `b6f870a` auto-fixed the
tree and stripped the whitespace after 474 list markers in the Google guides,
turning `1.  Foo` into `1.Foo`; the Markdown style guide then demonstrated
syntax that renders no list at all.

## Writing Style

When editing or creating guides:

- **MUST** use RFC 2119 keywords (MUST, SHOULD, MAY) in **bold uppercase**
- **MUST** include rationale ("Why" sections) for every major recommendation
- **MUST** provide Do/Don't code examples for style rules
- **SHOULD** keep code block line length ≤100 characters
- **SHOULD** use consistent heading hierarchy (H1 for title, H2 for sections)
- **MUST** include Quick Reference table at top of language guides
- **MUST** include navigation breadcrumb after title

## RFC 2119 Boilerplate

Every guide **MUST** include this after the title:

```markdown
The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in
BCP 14 [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119)
[RFC 8174](https://datatracker.ietf.org/doc/html/rfc8174) when, and only
when, they appear in all capitals, as shown here.
```

This is the full BCP 14 form from [RFC 8174 section
2](https://datatracker.ietf.org/doc/html/rfc8174#section-2). It supersedes the
bare RFC 2119 sentence still present in most guides; those are migrated
separately rather than piecemeal.

## Guide Template Structure

```markdown
# {Language/Topic} Style Guide

> [Doctrine](../../README.md) > [{Category}](../README.md) > {Topic}

The key words "MUST", "MUST NOT"... [RFC 2119 boilerplate]

## Quick Reference
| Task | Tool | Command |
|------|------|---------|

## {Tool/Section}
### Why
Rationale for this choice.

### Configuration
Code examples.

## See Also
- Links to related guides
```

## Common Tasks

### Adding a New Language Guide

1. Copy structure from existing guide (e.g., `guides/languages/python.md`)
2. Add RFC 2119 boilerplate
3. Include Quick Reference table
4. Add navigation breadcrumb
5. Include "See Also" section
6. Update `README.md` navigation tables and the category `README.md`
7. Run `python3 scripts/gen_nav.py` to rewrite `SUMMARY.md`
8. Update `CHANGELOG.md`

### Updating Tool Versions

When updating tool versions:

1. Search all guides for the tool name
2. Update version in all locations (configs, CI snippets, pre-commit hooks)
3. Test that commands still work
4. Update CHANGELOG.md

### Testing Changes Locally

Run `make check`, or the individual commands from
[Commands](#commands) above. To preview GitHub-flavoured rendering:

```bash
pipx run grip==4.6.2
```

## Key Files

| File | Purpose |
| ---- | ------- |
| `README.md` | Landing page, full navigation |
| `SUMMARY.md` | Generated navigation index (`scripts/gen_nav.py`) |
| `CHANGELOG.md` | Version history |
| `VERSION` | Current version (SemVer) |
| `agents/`, `commands/` | Agent and slash-command definitions |
| `configs/` | Copy-paste config files |
| `reference/google/` | Upstream Google guides |
| `reference/ERRATA.md` | Register of local corrections to vendored payloads |
| `scripts/check_vendored_payloads.py` | Vendored payload integrity check |

## Conventions

### Versioning

- Follow [Semantic Versioning 2.0.0](https://semver.org/)
- MAJOR: Breaking changes to guide structure
- MINOR: New guides or significant additions
- PATCH: Fixes, clarifications, tool updates

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```text
feat(python): add Hypothesis fuzzing section
fix(go): correct golangci-lint config syntax
docs(readme): update navigation table
chore: bump tool versions for Q4 2025
```

## Time-Sensitive Information

- **MUST** use Web Search for "current date and time" at the start of each
  session
- **MUST** use Web Search to verify release dates, version status, and
  deprecation timelines
- **MUST NOT** rely on model knowledge for current tool versions or release
  schedules
- **SHOULD** search before making recommendations about "latest" or "current"
  versions

**Why**: LLM training data has knowledge cutoffs and date/time awareness is
unreliable. Always verify time-sensitive claims against current sources.

## Do Not

- **MUST NOT** use vague language ("consider", "you might want to")
- **MUST NOT** omit rationale for recommendations
- **MUST NOT** include tool-specific config without version pinning
- **MUST NOT** reformat or lint-fix anything under `reference/`
- **SHOULD NOT** duplicate content across guides (link instead)
- **SHOULD NOT** recommend deprecated tools without migration path
