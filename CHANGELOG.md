# Changelog

All notable changes to the Doctrine Style Guide will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.1] - 2025-12-07

### Added

- Banner image (`banner.svg`) displayed at top of README

## [2.0.0] - 2025-12-06

### Added

- **AI-Assisted Development Guides** (NEW SECTION)
  - `guides/ai/README.md` - Overview of AI-assisted development
  - `guides/ai/claude.md` - Anthropic Claude best practices
  - `guides/ai/openai.md` - OpenAI GPT best practices
  - `guides/ai/gemini.md` - Google Gemini best practices
  - `guides/ai/local-llms.md` - Ollama, vLLM, Docker Model Runner
  - `guides/ai/prompt-engineering.md` - Prompt engineering patterns
  - `guides/ai/claude-md.md` - CLAUDE.md file patterns
  - `guides/ai/cursor-rules.md` - .cursorrules patterns
  - `guides/ai/security.md` - LLM security considerations
- `guides/languages/dotnet.md` - .NET framework guide (previously missing)
- `CLAUDE.md` - AI assistant instructions for this repository
- `configs/claude/CLAUDE.md.template` - Template for project CLAUDE.md files
- `configs/cursor/.cursorrules.template` - Template for Cursor rules
- RFC 2119 language throughout all guides
- Navigation breadcrumbs in all guides
- "Why" rationale sections for tool choices
- "See Also" cross-reference sections

### Changed

- **BREAKING**: Reorganized repository structure into `guides/` subdirectories
  - `guides/languages/` - Language-specific guides
  - `guides/frameworks/` - Framework guides (Rails, Django)
  - `guides/ai/` - AI-assisted development
  - `guides/docs/` - Documentation standards
  - `guides/process/` - Testing, CI, versioning
- Moved `google/` to `reference/google/`
- Reorganized `configs/` into subdirectories by tool
- Updated all internal links to reflect new structure
- Standardized all guides with RFC 2119 keywords (MUST, SHOULD, MAY)
- Updated README.md with comprehensive navigation tables

### Removed

- Flat file structure (replaced with organized directories)

## [1.0.0] - 2025-12-06

### Added

- Initial release of the Style Guide
- Language guides for Python, Ruby, Rails, Django, Go, Rust, C#, SQL,
  TypeScript, Shell, Markdown, CSS
- EditorConfig guide
- Testing guide (unit, integration, performance, regression)
- Dependencies and package management guide
- GitHub templates guide (CONTRIBUTING, SECURITY, PR templates, issue templates)
- Versioning guide (SemVer, Keep a Changelog, Conventional Commits)
- Configuration template files (.editorconfig, .prettierrc, pre-commit)
- Vendored Google style guides (Python, Markdown, Shell, C#, HTML/CSS, Go,
  TypeScript)

[Unreleased]: https://github.com/agh/doctrine/compare/v2.0.1...HEAD
[2.0.1]: https://github.com/agh/doctrine/compare/v2.0.0...v2.0.1
[2.0.0]: https://github.com/agh/doctrine/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/agh/doctrine/releases/tag/v1.0.0
