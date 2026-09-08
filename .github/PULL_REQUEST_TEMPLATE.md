<!-- markdownlint-disable MD041 -->

## Summary

What this changes, in one or two sentences.

## Motivation

What was wrong, missing or out of date. Link the issue if there is one:
`Fixes #`.

## Type of Change

- [ ] Fix — a rule, example, command or link that was wrong
- [ ] Version update — a pinned tool, action or reference version
- [ ] New guide or new section
- [ ] Provenance — licence, attribution or notice for vendored material
- [ ] Repository maintenance — CI, templates, tooling

## Sources

Every version number, release date and time-sensitive claim in this PR, with
the URL it was verified against and the date checked. Write "none" if the
change makes no such claim.

| Claim | Source URL | Checked on |
| ----- | ---------- | ---------- |
|       |            |            |

## House Rules

- [ ] RFC 2119 keywords are in **bold uppercase**, and new guides carry the
      RFC 2119 boilerplate after the title
- [ ] Every major recommendation has a "Why"
- [ ] Style rules have Do/Don't examples
- [ ] Every tool reference is version-pinned
- [ ] New guides have a Quick Reference table, a navigation breadcrumb and a
      "See Also" section
- [ ] No vague language ("consider", "you might want to")
- [ ] No deprecated tool recommended without a migration path
- [ ] Lines are at or below 100 characters
- [ ] Content is linked, not duplicated across guides
- [ ] British English in prose

## Vendored Material

Tick if this PR touches anything under `reference/`, then confirm:

- [ ] Not applicable
- [ ] Upstream URL, licence, licence URL and required attribution are recorded
      in `THIRD_PARTY_NOTICES.md`
- [ ] Licence text is present in the vendor directory where the licence
      requires it
- [ ] Modifications are recorded in the vendor directory's `NOTICE`
- [ ] `reference/security/cis/` is untouched (CC BY-NC-ND 4.0, no derivatives)

## Checks

- [ ] `make check` passes locally
- [ ] `CHANGELOG.md` has an entry under `## [Unreleased]`
- [ ] `VERSION` is unchanged
- [ ] Commits follow Conventional Commits and are signed off

## Notes for the Reviewer

Anything that needs explaining: trade-offs considered, what this deliberately
does not do, follow-up work.
