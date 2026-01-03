# GitHub Templates Guide

> [Doctrine](../../README.md) > [Process](../README.md) > GitHub Templates

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

Standardized templates for all @agh projects.

## Directory Structure

```text
.github/
├── ISSUE_TEMPLATE/
│   ├── bug_report.yml
│   ├── feature_request.yml
│   └── config.yml
├── PULL_REQUEST_TEMPLATE.md
├── CODEOWNERS
├── FUNDING.yml (optional)
└── workflows/
    └── ci.yml
CONTRIBUTING.md
SECURITY.md
LICENSE
```

## CONTRIBUTING.md

All @agh projects **SHOULD** include a CONTRIBUTING.md file. It **MUST** be
based on best practices from major open source projects.

````markdown
# Contributing to [Project Name]

Thank you for considering contributing! This document explains how to
contribute.

## Code of Conduct

This project follows the [Contributor Covenant](https://www.contributor-covenant.org/).
Be respectful and constructive.

## Getting Started

1. Fork the repository
2. Clone your fork
3. Set up the development environment (see README.md)
4. Create a branch for your changes

## Development Workflow

### Before You Start

- Check existing issues and PRs to avoid duplicates
- For significant changes, open an issue first to discuss

### Making Changes

1. Create a feature branch:

   ```bash
   git checkout -b feature/your-feature-name
   ```

1. Make your changes following our style guide

1. Write or update tests

1. Run the test suite:

   ```bash
   # Language-specific command
   ```

1. Run linting:

   ```bash
   # Language-specific command
   ```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```text
type(scope): description

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:

- `feat(auth): add OAuth2 support`
- `fix(api): handle null response from server`
- `docs: update installation instructions`

### Pull Requests

1. Push your branch to your fork
2. Open a PR against the `main` branch
3. Fill out the PR template completely
4. Wait for CI to pass
5. Address review feedback

## Reporting Issues

### Bug Reports

Use the bug report template. Include:

- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, version, etc.)
- Logs or error messages

### Feature Requests

Use the feature request template. Include:

- Problem you're trying to solve
- Proposed solution
- Alternatives you've considered

## Questions?

- Check existing documentation
- Search closed issues
- Open a discussion (if enabled) or issue

````

## SECURITY.md

All @agh projects **MUST** include a SECURITY.md file with vulnerability reporting procedures.

```markdown
# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x     | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to: security@example.com

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### What to Expect

- **Response**: Within 48 hours acknowledging receipt
- **Updates**: Every 5 business days on progress
- **Resolution**: Target 90 days for fix

### Disclosure Policy

- We follow coordinated disclosure
- Credit will be given to reporters (unless anonymity requested)
- We will not pursue legal action against good-faith reporters

## Security Best Practices

When contributing:
- Never commit secrets, tokens, or credentials
- Use environment variables for configuration
- Follow OWASP guidelines
- Report suspicious behavior
```

## CODEOWNERS

Projects **SHOULD** define code ownership using a CODEOWNERS[^1] file for automated review assignment.

```text
# Default owners for everything
*       @org/maintainers

# Specific paths
/docs/                    @org/docs-team
/.github/                 @org/devops
/src/api/                 @org/api-team
/src/frontend/            @org/frontend-team

# Specific files
/SECURITY.md              @org/security
```

## Issue Templates

All @agh projects **SHOULD** use structured issue templates[^2] to ensure
consistent bug reports and feature requests.

### .github/ISSUE_TEMPLATE/config.yml[^10]

```yaml
blank_issues_enabled: false
contact_links:
  - name: Documentation
    url: https://docs.example.com
    about: Check our documentation first
  - name: Discussions
    url: https://github.com/org/repo/discussions
    about: Ask questions here
```

### .github/ISSUE_TEMPLATE/bug_report.yml

```yaml
name: Bug Report
description: Report a bug
labels: ["bug", "triage"]
body:
  - type: markdown
    attributes:
      value: |
        Thanks for reporting! Please fill out the form below.

  - type: textarea
    id: description
    attributes:
      label: Description
      description: Clear description of the bug
    validations:
      required: true

  - type: textarea
    id: reproduction
    attributes:
      label: Steps to Reproduce
      description: Steps to reproduce the behavior
      placeholder: |
        1. Go to '...'
        2. Click on '...'
        3. See error
    validations:
      required: true

  - type: textarea
    id: expected
    attributes:
      label: Expected Behavior
      description: What did you expect to happen?
    validations:
      required: true

  - type: textarea
    id: actual
    attributes:
      label: Actual Behavior
      description: What actually happened?
    validations:
      required: true

  - type: input
    id: version
    attributes:
      label: Version
      description: What version are you using?
    validations:
      required: true

  - type: dropdown
    id: os
    attributes:
      label: Operating System
      options:
        - Linux
        - macOS
        - Windows
        - Other
    validations:
      required: true

  - type: textarea
    id: logs
    attributes:
      label: Relevant Logs
      description: Paste any relevant logs
      render: shell
```

### .github/ISSUE_TEMPLATE/feature_request.yml

```yaml
name: Feature Request
description: Suggest a new feature
labels: ["enhancement"]
body:
  - type: textarea
    id: problem
    attributes:
      label: Problem Statement
      description: What problem does this solve?
    validations:
      required: true

  - type: textarea
    id: solution
    attributes:
      label: Proposed Solution
      description: How should it work?
    validations:
      required: true

  - type: textarea
    id: alternatives
    attributes:
      label: Alternatives Considered
      description: What other solutions have you considered?

  - type: textarea
    id: context
    attributes:
      label: Additional Context
      description: Any other context or screenshots
```

## Pull Request Template

All @agh projects **MUST** include a pull request template[^3] to ensure comprehensive change documentation.

### .github/PULL_REQUEST_TEMPLATE.md

```markdown
## Summary

Brief description of changes.

## Related Issues

Fixes #(issue number)

## Type of Change

- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Documentation update
- [ ] Refactoring (no functional changes)

## Changes Made

- Change 1
- Change 2

## Testing

- [ ] Tests pass locally
- [ ] New tests added for new functionality
- [ ] Existing tests updated as needed

## Checklist

- [ ] Code follows the project's style guide
- [ ] Self-review completed
- [ ] Documentation updated (if applicable)
- [ ] No new warnings introduced
- [ ] Breaking changes documented

## Screenshots (if applicable)

## Additional Notes

Any additional context for reviewers.
```

## Git Configuration Files

### .gitignore

All projects **MUST** include a .gitignore file. You **SHOULD** create
language-specific ignores. Use [gitignore.io](https://gitignore.io)[^4]
as a starting point.

### .gitattributes

All projects **SHOULD** include a .gitattributes file[^5] to ensure consistent
line endings and file handling across platforms.

```gitattributes
# Auto detect text files and normalize line endings
* text=auto eol=lf

# Force specific file types
*.sh text eol=lf
*.py text eol=lf
*.rb text eol=lf
*.go text eol=lf
*.rs text eol=lf

# Binary files
*.png binary
*.jpg binary
*.gif binary
*.ico binary
*.pdf binary
*.zip binary

# Lock files - exact format matters
*.lock linguist-generated
package-lock.json linguist-generated
yarn.lock linguist-generated
Gemfile.lock linguist-generated
poetry.lock linguist-generated
uv.lock linguist-generated
Cargo.lock linguist-generated

# Vendored files
vendor/* linguist-vendored
node_modules/* linguist-vendored
```

### .dockerignore

Projects using Docker **SHOULD** include a .dockerignore file[^6] to reduce
build context size and improve build performance.

```dockerignore
# Git
.git
.gitignore

# CI/CD
.github
.gitlab-ci.yml

# IDE
.idea
.vscode
*.swp
*.swo

# Documentation
*.md
docs/
LICENSE

# Tests
tests/
test/
*_test.go
*.test.js

# Development
.env
.env.*
*.local

# Build artifacts (language-specific)
__pycache__/
*.pyc
node_modules/
target/
dist/
build/
```

## References

[^1]: [CODEOWNERS - GitHub Documentation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
[^2]: [Issue Templates - GitHub Documentation](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/configuring-issue-templates-for-your-repository)
[^3]: [Pull Request Templates - GitHub Documentation](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/creating-a-pull-request-template-for-your-repository)
[^4]: [gitignore.io](https://gitignore.io) - Generate .gitignore files for your project
[^5]: [.gitattributes - Git Documentation](https://git-scm.com/docs/gitattributes)
[^6]: [.dockerignore - Docker Documentation](https://docs.docker.com/build/building/context/#dockerignore-files)
[^10]: [Issue Template Configuration - GitHub Documentation](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms)

## See Also

- [CI/CD Guide](ci.md) - CI workflow configuration and automation
- [Versioning Guide](versioning.md) - Semantic versioning and changelog management
- [Testing Guide](testing.md) - Testing strategy and best practices
