# Versioning Guide

> [Doctrine](../../README.md) > [Process](../README.md) > Versioning

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in RFC 2119[^1].

All @agh projects **MUST** follow Semantic Versioning 2.0.0[^2].

## Semantic Versioning

```text
MAJOR.MINOR.PATCH
```

- **MAJOR**: Incompatible API changes
- **MINOR**: Backward-compatible new functionality
- **PATCH**: Backward-compatible bug fixes

### Examples

| Change                    | Version Bump    |
| ------------------------- | --------------- |
| Fix a bug                 | 1.0.0 -> 1.0.1  |
| Add a new feature         | 1.0.1 -> 1.1.0  |
| Remove a feature          | 1.1.0 -> 2.0.0  |
| Change function signature | 1.1.0 -> 2.0.0  |
| Add optional parameter    | 1.1.0 -> 1.2.0  |
| Security fix              | 1.2.0 -> 1.2.1  |

### Pre-release Versions

```text
1.0.0-alpha.1
1.0.0-beta.1
1.0.0-rc.1
```

### Build Metadata

```text
1.0.0+20240115
1.0.0+build.123
```

## Version 0.x.y

During initial development (0.x.y):

- API is unstable
- Any change may be breaking
- 0.1.0 -> 0.2.0 may break compatibility

**Rule**: You **SHOULD** stay at 0.x.y until you're confident in API stability.

## Changelogs

Every project **MUST** maintain a `CHANGELOG.md` following
Keep a Changelog[^3].

### Format

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog,
and this project adheres to Semantic Versioning.

## [Unreleased]

### Added
- New feature X

### Changed
- Updated dependency Y

### Deprecated
- Old feature Z (use W instead)

### Removed
- Legacy feature removed

### Fixed
- Bug in component A

### Security
- Fixed vulnerability CVE-XXXX

## [1.2.0] - 2024-01-15

### Added
- Feature description

[Unreleased]: https://github.com/user/repo/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/user/repo/compare/v1.1.0...v1.2.0
```

### Change Types

- **Added**: New features
- **Changed**: Changes to existing functionality
- **Deprecated**: Soon-to-be-removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Vulnerability fixes

## Git Tags

Tag releases with `v` prefix:

```bash
git tag v1.0.0
git push origin v1.0.0
```

## Conventional Commits

You **SHOULD** use Conventional Commits[^4] for commit
messages. This enables automated changelog generation and version bumping.

```text
type(scope): description

[optional body]

[optional footer]
```

### Types

| Type       | Description                  | Version Bump |
| ---------- | ---------------------------- | ------------ |
| `feat`     | New feature                  | MINOR        |
| `fix`      | Bug fix                      | PATCH        |
| `docs`     | Documentation only           | None         |
| `style`    | Code style (formatting)      | None         |
| `refactor` | Code change (no feature/fix) | None         |
| `perf`     | Performance improvement      | PATCH        |
| `test`     | Adding tests                 | None         |
| `chore`    | Maintenance                  | None         |

### Breaking Changes

Indicate breaking changes with `!` or `BREAKING CHANGE:`:

```text
feat!: remove deprecated API endpoint

BREAKING CHANGE: The /v1/users endpoint has been removed.
Use /v2/users instead.
```

Breaking changes always bump MAJOR version.

## Automated Releases

### release-please (Google)

```yaml
# .github/workflows/release.yml
name: Release
on:
  push:
    branches: [main]

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: googleapis/release-please-action@v4
        with:
          release-type: python  # or node, rust, go, etc.
```

release-please[^5]:

- Creates release PRs based on conventional commits
- Updates CHANGELOG.md automatically
- Bumps version numbers
- Creates GitHub releases

### semantic-release

Alternative for Node.js projects[^6]:

```json
{
  "release": {
    "branches": ["main"],
    "plugins": [
      "@semantic-release/commit-analyzer",
      "@semantic-release/release-notes-generator",
      "@semantic-release/changelog",
      "@semantic-release/npm",
      "@semantic-release/github"
    ]
  }
}
```

## API Versioning

For APIs, version in the URL or header:

```text
# URL versioning (preferred)
/api/v1/users
/api/v2/users

# Header versioning
Accept: application/vnd.myapi.v1+json
```

You **SHOULD** maintain at most 2 major versions simultaneously. You **MUST**
deprecate old versions with at least 6 months notice.

## Library Versioning

For libraries, follow language-specific conventions:

| Language   | Version Location                |
| ---------- | ------------------------------- |
| Python     | `pyproject.toml`, `__version__` |
| Ruby       | `version.rb`, `.gemspec`        |
| Go         | `go.mod`, git tags              |
| Rust       | `Cargo.toml`                    |
| C#         | `.csproj`, `AssemblyInfo.cs`    |
| TypeScript | `package.json`                  |

## Enforcement Tools

### Conventional Commits: commitlint

commitlint[^7] enforces conventional commit standards:

```bash
# Install
npm install --save-dev @commitlint/cli @commitlint/config-conventional

# Configure
echo "export default { extends: ['@commitlint/config-conventional'] };" > commitlint.config.js
```

Add to `.husky/commit-msg`:

```bash
npx --no -- commitlint --edit $1
```

Or with pre-commit (Python) using conventional-pre-commit[^8]:

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

### Keep a Changelog: changelog-lint

Validate CHANGELOG.md format using parse-a-changelog[^9] or changelog-lint[^10]:

```bash
# Using parse-a-changelog (Docker)
docker run --rm -v $(pwd):/src cyberark/parse-a-changelog

# Using changelog-lint (Go)
go install github.com/chavacava/changelog-lint@latest
changelog-lint CHANGELOG.md
```

### CI Validation

```yaml
# .github/workflows/validate.yml
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      # Validate commit messages
      - uses: wagoid/commitlint-github-action@v6

      # Validate changelog format
      - name: Validate CHANGELOG
        run: |
          docker run --rm -v $(pwd):/src cyberark/parse-a-changelog
```

### commitsar (Go Alternative)

For CI without Node.js, use commitsar[^11]:

```yaml
- uses: aevea/commitsar@v0.20.2
```

## References

[^1]: RFC 2119 - Key words for use in RFCs to Indicate Requirement Levels
<https://datatracker.ietf.org/doc/html/rfc2119>

[^2]: Semantic Versioning 2.0.0
<https://semver.org/>

[^3]: Keep a Changelog
<https://keepachangelog.com/>

[^4]: Conventional Commits 1.0.0
<https://www.conventionalcommits.org/>

[^5]: release-please - Automated Release PRs and Releases
<https://github.com/googleapis/release-please>

[^6]: semantic-release - Fully automated version management and package publishing
<https://github.com/semantic-release/semantic-release>

[^7]: commitlint - Lint commit messages
<https://commitlint.js.org/>

[^8]: conventional-pre-commit - A pre-commit hook for Conventional Commits
<https://github.com/compilerla/conventional-pre-commit>

[^9]: parse-a-changelog - Changelog parser and validator
<https://github.com/cyberark/parse-a-changelog>

[^10]: changelog-lint - Linter for CHANGELOG files
<https://github.com/chavacava/changelog-lint>

[^11]: commitsar - Conventional commit compliance checker
<https://github.com/aevea/commitsar>

## See Also

- [CI/CD Guide](ci.md) - CI workflow configuration and automation
- [Testing Guide](testing.md) - Testing strategy and best practices
- [GitHub Templates](github-templates.md) - Issue and PR templates
