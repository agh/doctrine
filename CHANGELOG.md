# Changelog

All notable changes to the Doctrine Style Guide will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.8.0] - 2025-12-17

### Added

- `guides/docs/specifications.md` - Specification writing guide for engineering docs
- `scripts/validate_versions.py` - Tool version validation script
- `SUMMARY.md` - Repository summary

### Changed

- `guides/frameworks/django.md` - Django 5.1 updates, async views, improved testing patterns
- `guides/frameworks/README.md` - Updated framework navigation
- `guides/docs/README.md`, `guides/docs/markdown.md` - Documentation improvements
- `guides/languages/shell.md`, `guides/languages/sql.md` - Minor updates
- `configs/pre-commit/.pre-commit-config.yaml` - Updated hook versions
- `configs/prettier/.prettierrc` - Configuration refinements
- `CLAUDE.md` - Project instructions updates

## [2.7.0] - 2025-12-17

### Added

- **Infrastructure Guides** (NEW SECTION)
  - `guides/infrastructure/README.md` - Infrastructure overview
  - `guides/infrastructure/ansible.md` - Ansible automation and configuration management
  - `guides/infrastructure/docker.md` - Docker containerization best practices
- **Ansible Configuration Templates**
  - `configs/ansible/` - ansible.cfg, .ansible-lint, .yamllint, .sops.yaml, requirements.yml

## [2.6.0] - 2025-12-17

### Changed

- **C# Guide Updates**
  - C# 13 and .NET 9 features (params collections, partial properties, ref struct interfaces)
  - Enhanced pattern matching and collection expressions
  - Updated analyzer and formatting configurations
- **dotnet Guide Updates**
  - .NET 9 SDK tooling and configuration
  - Native AOT compilation guidance
  - Updated CI/CD patterns

## [2.5.0] - 2025-12-17

### Added

- **JavaScript/Frontend Framework Guides**
  - `guides/frameworks/react.md` - React 19 component patterns and hooks
  - `guides/frameworks/nextjs.md` - Next.js 15 App Router and server components
  - `guides/frameworks/tailwind.md` - Tailwind CSS 4.0 utility-first styling

## [2.4.0] - 2025-12-17

### Added

- **Go Framework Guide**
  - `guides/frameworks/gin.md` - Gin HTTP web framework
- **Rust Framework Guide**
  - `guides/frameworks/axum.md` - Axum async web framework

## [2.3.0] - 2025-12-17

### Added

- **Ruby Framework Guides**
  - `guides/frameworks/sinatra.md` - Sinatra DSL for lightweight web apps and APIs
  - `guides/frameworks/hanami.md` - Hanami clean architecture framework

### Changed

- `guides/frameworks/rails.md` - Rails 8.0 updates, Solid Queue/Cache/Cable, Kamal deployment

## [2.2.0] - 2025-12-17

### Added

- **Python 3.14 Support**
  - Updated `guides/languages/python.md` to target Python 3.14
  - PEP 695: Type parameter syntax (`class Box[T]:`)
  - PEP 742: `TypeIs` for type narrowing
  - PEP 750: Template strings (t-strings)
  - PEP 649: Deferred annotation evaluation
  - PEP 594: Dead batteries removal documentation
  - Free-threading and JIT compiler notes
- **Python Framework Guides**
  - `guides/frameworks/fastapi.md` - FastAPI 0.115+ async API framework
  - `guides/frameworks/flask.md` - Flask 3.x microframework
- **Ruby 4.0 Support**
  - Updated `guides/languages/ruby.md` to target Ruby 4.0
  - `it` keyword, frozen strings by default, Pathname/Set as core classes
  - Array#find/rfind, String#strip selectors, Prism parser
  - YJIT/ZJIT JIT compilers, Ractor::Port API
  - Breaking changes and migration guide

## [2.1.0] - 2025-12-17

### Added

- **Design Guides** (NEW SECTION)
  - `guides/design/README.md` - Design principles and process overview
  - `guides/design/design-systems.md` - Design tokens, typography, color systems, spacing, theming
  - `guides/design/components.md` - Reusable component patterns (buttons, inputs, cards, modals, tables)
  - `guides/design/accessibility.md` - WCAG 2.1 AA compliance, ARIA patterns, testing strategies
  - `guides/design/motion.md` - Animation principles, motion tokens, interaction feedback
- Design Guides section in README with navigation table

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

[Unreleased]: https://github.com/agh/doctrine/compare/v2.1.0...HEAD
[2.1.0]: https://github.com/agh/doctrine/compare/v2.0.1...v2.1.0
[2.0.1]: https://github.com/agh/doctrine/compare/v2.0.0...v2.0.1
[2.0.0]: https://github.com/agh/doctrine/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/agh/doctrine/releases/tag/v1.0.0
