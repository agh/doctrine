# Security Policy

> [Doctrine](README.md) > Security Policy

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

## What This Policy Covers

Doctrine is documentation. It ships no service, no library and no binary, so
there is nothing here to compromise at runtime. The security surface is the
material Doctrine tells people to copy into their own projects:

- configuration files under `configs/`
- GitHub Actions workflows under `.github/workflows/`
- agent definitions under `agents/` and `commands/`
- shell commands, install instructions and pinned versions inside the guides
- the vendored security reference data under `reference/security/`

A dangerous default, an insecure command, a workflow that leaks a token, a
compromised or typo-squatted package name, or a pinned action pointing at a
malicious revision are all in scope. So is security advice in a guide that is
wrong in a way that would make a reader's system less safe.

Out of scope: vulnerabilities in the upstream tools Doctrine recommends.
Report those to the tool's own maintainers.

## Supported Versions

| Version | Supported |
| ------- | --------- |
| Latest commit on `main` | Yes |
| Any tagged release older than `main` | No |

Doctrine is a single moving document set. Fixes land on `main`; older tags are
historical records and are not patched. Pull the current `main` before
reporting.

## Reporting a Vulnerability

**Do not open a public issue for a security problem.**

Report privately through GitHub:

1. Go to <https://github.com/agh/doctrine/security/advisories/new>.
2. Describe the problem, where it is (file and line), and what an attacker
   could do with it.
3. Include the steps you took to confirm it.

This uses GitHub's private vulnerability reporting, so the report stays
between you and the maintainer until a fix is published.

If private reporting is unavailable to you, open a public issue that says only
that you have a security report and gives no details, and the maintainer will
open a private channel.

## What to Expect

Doctrine has one maintainer working on it in their own time. Handling is best
effort:

- Reports are acknowledged when the maintainer next picks up the repository.
- There is no service level agreement, no fixed response window and no
  guaranteed fix date. Anyone who needs one of those needs a commercial
  vendor, not this repository.
- Progress is communicated in the private advisory thread.
- Reporters are credited in the advisory and the changelog unless they ask not
  to be.

Coordinated disclosure is expected: please give the maintainer a reasonable
chance to fix the problem before publishing. No legal action will be taken
against anyone reporting in good faith.

## Using Doctrine Safely

- **MUST** review any configuration, workflow or command before copying it
  into a project. Doctrine's material is a starting point, not an audited
  artefact.
- **MUST** re-pin GitHub Actions to a commit SHA you have verified yourself
  rather than trusting a tag.
- **MUST NOT** treat `reference/security/` as live threat intelligence. It is
  a periodically refreshed snapshot; check `reference/security/manifest.json`
  for `last_updated` and `next_review` before relying on it.
- **MUST NOT** commit secrets, tokens or credentials to this repository. Some
  guides contain deliberate "never do this" examples that look like
  credentials; they are illustrative and contain no real values.

## See Also

- [CONTRIBUTING.md](CONTRIBUTING.md) — how to propose changes
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) — community expectations
- [guides/ai/security.md](guides/ai/security.md) — LLM security considerations
