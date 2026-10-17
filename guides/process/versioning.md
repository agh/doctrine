# Versioning Guide

> [crefft](../../README.md) > [Process](../README.md) > Versioning

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in
BCP 14 [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119)
[RFC 8174](https://datatracker.ietf.org/doc/html/rfc8174) when, and only
when, they appear in all capitals, as shown here.

Libraries **MUST** use Semantic Versioning 2.0.0[^2]. A library is a package
published for other code to depend on through a package manager or module
system, including npm, crates.io, PyPI, RubyGems, NuGet, Maven, Go modules,
and similar ecosystems. A project that ships both a command and importable
packages is a library.

Everything else — applications, services, sites, command-line tools,
documentation standards such as crefft itself, and configuration — **MUST**
use calendar versioning (CalVer[^1]) in the `YYYY.M.N` format.

## Quick Reference

| Task | Rule | Example |
| ---- | ---- | ------- |
| Release a library in any ecosystem | Semantic Versioning 2.0.0 | `1.4.2` |
| Release anything else | Calendar versioning | `2026.10.0` |
| Ship both a command and importable packages | Treat the project as a library | `1.4.2` |
| First release of a month | Four-digit year, unpadded month, counter 0 | `2026.10.0` |
| Further release that month | Highest counter already released that month + 1 | `2026.10.1` |
| First release of a new month | Use the new year/month and reset the counter | `2026.11.0` |
| Tag a release | Prefix the version with `v` | `v2026.10.0` |
| Record incompatibility | First changelog section: `### Breaking` | Migration instructions |
| Mark a breaking commit | Conventional Commits `!` or footer | `feat!: remove legacy API` |
| Release a Go library | SemVer; `/vN` module path suffix at major 2 or higher | `v1.4.2` |

## Semantic Versioning for Libraries

Libraries **MUST** use `MAJOR.MINOR.PATCH`: increment MAJOR for breaking
changes, MINOR for backward-compatible features, and PATCH for fixes.
Reset lower components to 0 when incrementing MAJOR or MINOR.
Breaking changes **MUST** still appear under `### Breaking`, first in the
changelog release section, with migration instructions.

### Why

Dependency resolvers in these ecosystems assume SemVer ranges. Under
CalVer the leading number is the year, so a caret range such as
`^2026.10.0` would admit every later release that year, including breaking
ones. Library versions must communicate compatibility so dependency updates
do not silently admit incompatible code.

```text
Do:    library 1.4.2 -> 2.0.0 for a breaking change
       library 1.4.2 -> 1.5.0 for a compatible feature
       library 1.4.2 -> 1.4.3 for a fix
Don't: library 2026.10.0 -> 2026.10.1 for a breaking change
       library 1.4.2 -> 1.5.0 after removing a public API
```

### Go Modules

Go libraries use SemVer tags such as `v0.x.y` or `v1.x.y`, not
`vYYYY.M.N`. At major version 2 or higher, their module paths **MUST**
end in `/vN` with the matching major number.

#### Why

The Go module reference[^3] states: "If the module is released at major
version 2 or higher, the module path must end with a major version suffix
like /v2". A calendar year in the leading position would therefore require
a path such as `/v2026`.

A Go command-line tool that publishes no importable packages **MUST** use
CalVer, with `vYYYY.M.N` tags. Such a tool **MUST** be built from its
checkout or distributed as release artifacts:
`go install module@v2026.10.0` fails when the module path has no `/v2026`
suffix. A Go module that ships a command and importable packages is a
library and **MUST** use SemVer instead.

```bash
# Do: build a command-only tool from its checked-out release.
git checkout v2026.10.0
go build ./cmd/mytool

# Don't: request a year-major tag through an unsuffixed module path.
go install example.com/team/mytool/cmd/mytool@v2026.10.0
```

## Calendar Versioning

Release numbers **MUST** have exactly three dot-separated components:

```text
YYYY.M.N
```

`YYYY` is the four-digit release year. `M` is the release month, from 1 to
12. `N` is the release's number within that month, counting from 0.
The month and counter **MUST NOT** contain leading zeros.

### Why

A release number identifies when a release was made and its order within
that month. It does not encode a judgment about compatibility. The format
also has valid SemVer syntax[^2]: npm, Cargo, PEP 440, and Homebrew accept
`2026.10.0`. npm, Cargo, and Go reject leading zeros, so `2026.03.001`
is not a portable alternative.

```text
Do:    2026.3.0, 2026.3.1, 2026.10.0
Don't: 2026.03.001, 26.10.0, 2026.13.0
```

### Choosing the Next Number

For the release's year and month, projects **MUST** inspect the versions
already released. If none exists for that month, the counter **MUST** be 0;
otherwise it **MUST** be one greater than the highest counter already
released in that month. Commit types and breaking changes **MUST NOT**
change this calculation.

#### Why

Using the release history prevents duplicate numbers. Resetting the
counter at each new month makes the first release distinguishable without
assigning compatibility meaning to any component.

| Release date | Change | Version |
| ------------ | ------ | ------- |
| 2026-03-02 | First release of March | `2026.3.0` |
| 2026-03-09 | Bug fix | `2026.3.1` |
| 2026-03-27 | Breaking change | `2026.3.2` |
| 2026-04-01 | First release of April | `2026.4.0` |
| 2026-10-17 | First release of October | `2026.10.0` |
| 2026-10-20 | Next release of October | `2026.10.1` |
| 2027-01-03 | First release of January | `2027.1.0` |

```text
Do:    2026.10.0 -> 2026.10.1 for any second October release
Don't: 2026.10.0 -> 2027.0.0 because a commit is breaking
```

### Compatibility and Dependency Ranges

A CalVer number does not signal compatibility. Breaking changes
**MUST** be documented under [Breaking Changes](#breaking-changes),
independently of the release number.

#### Why

Two releases in one month can be incompatible, while releases in different
years can remain compatible. Users need the changelog and migration notes,
not an inferred promise from the leading number.

Libraries use the [SemVer rule](#semantic-versioning-for-libraries) instead
of CalVer. Pre-release suffix policy for CalVer remains undecided.

## Migration from Semantic Versioning

Non-library projects migrating to CalVer **MUST** simply follow their last
SemVer release with the first CalVer release. Libraries **MUST NOT** migrate
to CalVer.
Previously published versions and tags **MUST NOT** be rewritten or
re-tagged. Projects **MUST** update their version files, release templates,
tag references, and changelog comparison links together.

### Why

Existing tags identify immutable releases used by downstream consumers.
`2026.10.0` sorts after `2.11.0`, so a migration needs no intermediate
release and no alteration to history.

```text
Do:    v2.11.0 -> v2026.10.0; leave v2.11.0 pointing at its original commit
Don't: re-tag v2.11.0 or insert an intermediate compatibility-major release
```

## Changelogs

Every project **MUST** maintain `CHANGELOG.md` following Keep a
Changelog[^4], extended with `### Breaking` as the first subsection of
each release that contains breaking changes.

### Why

A changelog describes the user-facing effect of a release. Putting breaking
changes first makes the migration work visible even when a release number
does not communicate compatibility.

### Format

The example below is for a CalVer project. Library changelogs **MUST**
declare Semantic Versioning 2.0.0 instead and use SemVer release headings
and comparison links.

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog,
and this project adheres to calendar versioning (`YYYY.M.N`).

## [Unreleased]

## [2026.10.1] - 2026-10-20

### Breaking
- Removed the legacy login endpoint; use `/api/v2/login`.

### Added
- Added profile editing.

### Changed
- Updated the dashboard layout.

### Deprecated
- Deprecated the old export format in favour of JSON.

### Removed
- Removed an unused example file.

### Fixed
- Fixed concurrent-session handling.

### Security
- Fixed an authentication bypass.

## [2026.10.0] - 2026-10-17

### Added
- First release of October.

[Unreleased]: https://github.com/user/repo/compare/v2026.10.1...HEAD
[2026.10.1]: https://github.com/user/repo/compare/v2026.10.0...v2026.10.1
```

### Change Types

| Section | Content |
| ------- | ------- |
| Breaking | Incompatible changes, impact, and migration instructions; first when present |
| Added | New features |
| Changed | Changes to existing functionality |
| Deprecated | Features due for removal |
| Removed | Removed features |
| Fixed | Bug fixes |
| Security | Vulnerability fixes |

```markdown
<!-- Do: make an incompatible change visible first. -->
### Breaking
- Renamed `getUserProfile()` to `getProfile()`; update callers.
```

```markdown
<!-- Don't: bury an incompatible change among routine changes. -->
### Changed
- Renamed `getUserProfile()` to `getProfile()`.
```

## Git Tags

Release tags **MUST** be the version prefixed with `v`:

```bash
# Do
git tag v2026.10.0

# Don't
git tag 2026.10.0
```

### Why

One spelling lets release workflows, archives, and comparison links identify
the same release. The `VERSION` file and package metadata contain
`2026.10.0`; the tag contains `v2026.10.0`.

## Conventional Commits

Projects **SHOULD** use Conventional Commits[^5] for commit messages.
Types classify changes for release notes. For libraries, `feat` selects
MINOR, `fix` selects PATCH, and a breaking marker takes precedence and
selects MAJOR. For CalVer projects, commit types **MUST NOT** affect
release-number arithmetic:

```text
type(scope): description

[optional body]

[optional footer]
```

### Why

Consistent commit metadata supports changelog generation and review.
Libraries also use it to select a compatibility bump; CalVer projects
calculate calendar order independently.

| Type | Description |
| ---- | ----------- |
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting |
| `refactor` | Code change without a feature or fix |
| `perf` | Performance improvement |
| `test` | Tests |
| `chore` | Maintenance |

### Breaking Changes

A breaking commit **MUST** retain the Conventional Commits `!` marker or
`BREAKING CHANGE:` footer. Its changelog entry **MUST** appear under
`### Breaking`, first in the release section, and state the migration.

#### Why

The commit marker supports automated detection; the dedicated changelog
heading gives consumers a human-readable migration path.

```text
# Do
feat!: remove deprecated API endpoint

BREAKING CHANGE: The /api/v1/users endpoint has been removed.
Use /api/v2/users instead.

# Don't
feat: remove deprecated API endpoint
```

## Release Automation

Release automation **MUST** first classify the project: a library uses a
SemVer bump from breaking, feature, or fix changes; anything else uses the
next `YYYY.M.N` from the release date and release history. It **MUST**
update version files, the changelog, and tag references consistently and
put breaking changes under `### Breaking` in both cases.

### Why

A commit analyzer that always maps `feat` to a minor bump or always selects
a calendar number cannot implement both policies. Project classification
determines the calculation; compatibility reporting is required for both.

```text
Do:    library + breaking/feature/fix changes -> next MAJOR.MINOR.PATCH
       anything else + release date + released versions -> next YYYY.M.N
       either policy + breaking changes -> ### Breaking and migration notes
Don't: use CalVer for a library or commit-driven bumps for an application
```

## API and Package Versions

API URL or header versions identify contracts, not calendar releases:

```text
/api/v1/users
/api/v2/users
Accept: application/vnd.myapi.v1+json
```

Projects **SHOULD** maintain at most two API contract versions simultaneously
and **MUST** give at least six months' notice before removing an old one.

### Why

An API contract can survive many releases. Changing its URL every month
would force migrations without any corresponding contract change.

Package metadata **MUST** carry the project's release version: SemVer for
libraries and CalVer for everything else. Publishing an application through
a package manager does not make it a library unless other code can depend
on its importable packages.

| Language | Version location |
| -------- | ---------------- |
| Python | `pyproject.toml`, `__version__` |
| Ruby | `version.rb`, `.gemspec` |
| Go | Git tags; `go.mod` declares the module path |
| Rust | `Cargo.toml` |
| C# | `.csproj`, `AssemblyInfo.cs` |
| TypeScript | `package.json` |

## Enforcement Tools

### Conventional Commits

The pinned conventional-pre-commit hook[^6] checks commit messages:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/compilerla/conventional-pre-commit
    rev: v3.6.0
    hooks:
      - id: conventional-pre-commit
        stages: [commit-msg]
```

```bash
pre-commit install --hook-type commit-msg
```

### Keep a Changelog

A changelog validator **MUST** accept the additional `Breaking` section
and the project's SemVer or CalVer preamble. With kacl-cli[^7], commit
`.kacl.yml` alongside `CHANGELOG.md`; this example configures CalVer,
while libraries **MUST** use their Semantic Versioning 2.0.0 preamble:

```yaml
# .kacl.yml
kacl:
  allowed_header_titles: [Changelog]
  allowed_version_sections: [Breaking, Added, Changed, Deprecated, Removed, Fixed, Security]
  default_content:
    - All notable changes to this project will be documented in this file.
    - "The format is based on Keep a Changelog,"
    - "and this project adheres to calendar versioning (`YYYY.M.N`)."
```

The validator image **MUST** be pinned, and local checks and CI **MUST**
use the same command and working directory:

```bash
# Do: the tool reads CHANGELOG.md and .kacl.yml from /workdir.
docker run --rm -v "$(pwd)":/workdir:ro -w /workdir mschmieder/kacl-cli:0.7.4 verify

# Don't: the tool cannot find CHANGELOG.md in its working directory.
docker run --rm -v "$(pwd)":/src mschmieder/kacl-cli:0.7.4 verify
```

#### Why

The preamble and allowed sections are part of the validator's grammar.
Without matching configuration, a valid changelog can fail a checker
that still expects a different preamble or rejects `Breaking`.

## References

[^1]: [Calendar Versioning](https://calver.org/) - Calendar-based version conventions
[^2]: [Semantic Versioning 2.0.0](https://semver.org/) - Library compatibility and version syntax
[^3]: [Go module reference: major version suffixes](https://go.dev/ref/mod#major-version-suffixes)
[^4]: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
[^5]: [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)
[^6]: [conventional-pre-commit](https://github.com/compilerla/conventional-pre-commit)
[^7]: [kacl-cli](https://gitlab.com/schmieder.matthias/python-kacl) - Changelog validation

## See Also

- [CI/CD Guide](ci.md) - Release workflow checks
- [Testing Guide](testing.md) - Testing strategy and best practices
- [GitHub Templates](github-templates.md) - Issue and PR templates
- [Release Manager](../ai/release-manager-agent.md) - Release-number calculation and breaking flags
