# AGENTS.md - Doctrine Style Guide

## Overview

Doctrine is a comprehensive style guide repository covering 13+ programming
languages, frameworks, and AI-assisted development practices. All guides use
[RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119) language to clearly
distinguish requirements from recommendations.

## Repository Structure

```text
doctrine/
├── guides/
│   ├── languages/     # Language-specific style guides (Python, Go, Rust, etc.)
│   ├── frameworks/    # Framework guides (Rails, Django)
│   ├── ai/            # AI-assisted development practices
│   ├── docs/          # Documentation standards (Markdown)
│   └── process/       # Testing, CI, versioning, GitHub templates
├── configs/           # Ready-to-copy configuration files
├── reference/google/  # Vendored Google style guides (CC-BY 3.0)
├── README.md          # Landing page with full navigation
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
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).
```

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
6. Update `README.md` navigation tables
7. Update `CHANGELOG.md`

### Updating Tool Versions

When updating tool versions:

1. Search all guides for the tool name
2. Update version in all locations (configs, CI snippets, pre-commit hooks)
3. Test that commands still work
4. Update CHANGELOG.md

### Testing Changes Locally

```bash
# Verify markdown formatting
npx markdownlint-cli2 "**/*.md"

# Check for broken links
npx markdown-link-check README.md

# Preview with grip (GitHub-flavored markdown)
pip install grip && grip
```

## Key Files

| File | Purpose |
| ---- | ------- |
| `README.md` | Landing page, full navigation |
| `CHANGELOG.md` | Version history |
| `VERSION` | Current version (SemVer) |
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
