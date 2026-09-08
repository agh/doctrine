# Contributing to Doctrine

> [Doctrine](README.md) > Contributing

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

Doctrine is a style-guide repository. Contributions are prose, tables, code
examples and configuration files — not application code. This document
explains how to propose a change and what a change **MUST** satisfy before it
is merged.

Participation is governed by the [Code of Conduct](CODE_OF_CONDUCT.md).

## Quick Reference

| Task | Command |
| ---- | ------- |
| Run every check | `make check` |
| Lint Markdown | `npx markdownlint-cli2@0.23.2 "**/*.md"` |
| Validate tool versions | `python3 scripts/validate_versions.py` |
| Validate a JSON file | `jq . reference/security/manifest.json` |

## What Belongs Here

Doctrine covers language guides, framework guides, process guides, AI-assisted
development practices, ready-to-copy configuration files, and vendored
upstream reference material.

A proposal **SHOULD** fall into one of four shapes:

1. **Fix a guide** — a rule that is wrong, an example that does not run, a
   command that no longer exists, a broken link.
2. **Update a version** — a pinned tool version that has moved on, or a tool
   that is now deprecated.
3. **Add a guide** — a language, framework or topic Doctrine does not cover.
4. **Correct provenance** — attribution, licence or notice problems in
   `reference/` or [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

Open an issue first for anything larger than a fix. The issue forms in
`.github/ISSUE_TEMPLATE/` map onto the shapes above.

## House Rules

These are the rules a reviewer will check. They are not negotiable.

- **MUST** use [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119)
  keywords (MUST, MUST NOT, SHOULD, SHOULD NOT, MAY) in **bold uppercase**,
  and **MUST** include the RFC 2119 boilerplate after the title of every
  guide.
- **MUST** include a rationale ("Why") for every major recommendation. A rule
  without a reason is an opinion.
- **MUST** provide Do/Don't code examples for style rules.
- **MUST** pin every tool version. No guide may reference a tool without
  stating the version it was verified against.
- **MUST** include a Quick Reference table at the top of every language guide,
  and a navigation breadcrumb immediately after the title.
- **MUST NOT** use vague language: "consider", "you might want to", "it is
  generally recommended".
- **MUST NOT** recommend a deprecated tool without a migration path.
- **SHOULD** keep lines at or below 100 characters, including code blocks.
- **SHOULD** link to an existing guide rather than duplicating its content.
- **SHOULD** use British English in prose. Tool names, flags and code keep
  their upstream spelling.

### Verifying Time-Sensitive Claims

Version numbers, release dates and deprecation timelines **MUST** be checked
against a current source before they are written down, and the source
**SHOULD** be cited in the pull request. Model knowledge and memory are not
evidence. This applies to human and AI contributors alike.

### Vendored Material

`reference/` holds third-party work under third-party licences.

- **MUST NOT** add material to `reference/` without also recording its
  upstream URL, licence, licence URL and required attribution in
  [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md), and copying the licence
  text into the vendor directory where the licence requires it.
- **MUST NOT** edit `reference/security/cis/` — that material is
  CC BY-NC-ND 4.0 and carries a NoDerivatives condition. See
  [`reference/security/cis/NOTICE`](reference/security/cis/NOTICE).
- **MUST** record modifications to CC BY, CC BY-SA and Apache-2.0 material in
  the vendor directory's `NOTICE` file.

## Development Workflow

1. Fork the repository and clone your fork.
2. Create a branch: `git checkout -b fix/python-ruff-version`.
3. Make the change.
4. Run `make check` and fix everything it reports.
5. Commit using [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).
6. Open a pull request against `main` and fill in the template.

### Checks

`make check` runs Markdown linting, JSON validation and the tool-version
validator. Run it before every push. If you do not have `make`, run the
underlying commands:

```bash
npx markdownlint-cli2@0.23.2 "**/*.md"
python3 scripts/validate_versions.py
find . -name '*.json' -not -path './node_modules/*' -exec jq -e . {} \; > /dev/null
```

Markdown lint configuration lives in `.markdownlint.json` and
`reference/security/.markdownlint.json`. Do not relax a rule to make a lint
error go away; fix the content.

### Commit Messages

```text
type(scope): description

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `ci`.
Scope is the guide or area touched.

Examples:

- `feat(python): add Hypothesis fuzzing section`
- `fix(go): correct golangci-lint config syntax`
- `docs(readme): update navigation table`
- `chore(reference): record Uber Go guide modifications in NOTICE`

The subject line **MUST** be imperative mood and at most 72 characters.

### Changelog and Version

Every user-visible change **MUST** add an entry to [CHANGELOG.md](CHANGELOG.md)
under `## [Unreleased]`, following
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Do not edit `VERSION`
in a pull request; releases are cut separately following
[Semantic Versioning 2.0.0](https://semver.org/).

## Adding a New Guide

1. Copy the structure of an existing guide of the same kind — for example
   [`guides/languages/python.md`](guides/languages/python.md).
2. Add the navigation breadcrumb and the RFC 2119 boilerplate.
3. Add the Quick Reference table.
4. Write a "Why" for every tool choice, with the version pinned and the source
   for that version cited in the pull request.
5. Add a "See Also" section linking related guides.
6. Add the guide to the navigation tables in [README.md](README.md).
7. Add a `CHANGELOG.md` entry.

## Reporting Problems

Use the issue forms:

- **Bug in a guide** — a rule, example or command that is wrong.
- **Outdated version** — a pinned version that has moved on. Include the
  current version and the URL you checked.
- **New guide proposal** — a language, framework or topic Doctrine should
  cover.

Security vulnerabilities **MUST NOT** be reported in public issues. See
[SECURITY.md](SECURITY.md).

## Review

Doctrine has one maintainer. Review is best effort, in the maintainer's own
time. A pull request that follows the house rules, cites its sources and
passes `make check` will be reviewed faster than one that does not.
