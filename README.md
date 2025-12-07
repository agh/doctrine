# Doctrine Style Guide

**Version: 2.0.0** | [Changelog](CHANGELOG.md) | [CLAUDE.md](CLAUDE.md)

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

Canonical style guide for all projects. Vendored from [Google Style Guides](https://github.com/google/styleguide) with project-specific tooling and conventions. Each tool was selected as the world-class option for its ecosystem in 2025.

**All projects MUST follow:**
- [Semantic Versioning 2.0.0](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
- [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)

See [versioning guide](guides/process/versioning.md) for details.

---

## Language Guides

| Language | Guide | Upstream |
|----------|-------|----------|
| Python | [guides/languages/python.md](guides/languages/python.md) | [Google](reference/google/python.md) |
| Ruby | [guides/languages/ruby.md](guides/languages/ruby.md) | Community |
| Go | [guides/languages/go.md](guides/languages/go.md) | [Google](reference/google/go.md) |
| Rust | [guides/languages/rust.md](guides/languages/rust.md) | Official |
| TypeScript | [guides/languages/typescript.md](guides/languages/typescript.md) | [Google](reference/google/typescript.html) |
| C# | [guides/languages/csharp.md](guides/languages/csharp.md) | [Google](reference/google/csharp.md) |
| .NET | [guides/languages/dotnet.md](guides/languages/dotnet.md) | Microsoft |
| SQL | [guides/languages/sql.md](guides/languages/sql.md) | Community |
| Shell | [guides/languages/shell.md](guides/languages/shell.md) | [Google](reference/google/shell.md) |
| CSS | [guides/languages/css.md](guides/languages/css.md) | [Google](reference/google/htmlcss.html) |

## Framework Guides

| Framework | Guide | Language |
|-----------|-------|----------|
| Rails | [guides/frameworks/rails.md](guides/frameworks/rails.md) | Ruby |
| Django | [guides/frameworks/django.md](guides/frameworks/django.md) | Python |

## AI-Assisted Development

| Topic | Guide | Description |
|-------|-------|-------------|
| Overview | [guides/ai/README.md](guides/ai/README.md) | When and how to use AI assistance |
| Claude | [guides/ai/claude.md](guides/ai/claude.md) | Anthropic Claude best practices |
| OpenAI | [guides/ai/openai.md](guides/ai/openai.md) | GPT-4 and OpenAI API patterns |
| Gemini | [guides/ai/gemini.md](guides/ai/gemini.md) | Google Gemini best practices |
| Local LLMs | [guides/ai/local-llms.md](guides/ai/local-llms.md) | Ollama, vLLM, Docker Model Runner |
| Prompts | [guides/ai/prompt-engineering.md](guides/ai/prompt-engineering.md) | Prompt engineering patterns |
| CLAUDE.md | [guides/ai/claude-md.md](guides/ai/claude-md.md) | Project instruction files |
| Cursor Rules | [guides/ai/cursor-rules.md](guides/ai/cursor-rules.md) | .cursorrules patterns |
| Security | [guides/ai/security.md](guides/ai/security.md) | LLM security considerations |

## Process Guides

| Topic | Guide |
|-------|-------|
| Testing | [guides/process/testing.md](guides/process/testing.md) |
| Versioning | [guides/process/versioning.md](guides/process/versioning.md) |
| CI/CD | [guides/process/ci.md](guides/process/ci.md) |
| GitHub Templates | [guides/process/github-templates.md](guides/process/github-templates.md) |

## Documentation

| Topic | Guide |
|-------|-------|
| Markdown | [guides/docs/markdown.md](guides/docs/markdown.md) |

---

## What Each Language Guide Covers

Every language guide **MUST** include:

| Category | Topics |
|----------|--------|
| **Code Quality** | Lint, Format, Type Check, Semantic Analysis, Dead Code |
| **Testing** | Unit, Integration, E2E, Acceptance, Performance |
| **Advanced Testing** | Thread Safety, Idempotence, Reliability, Compatibility |
| **Specialized** | i18n/UTF-8, Data Integrity, A/B Testing, Feature Flags |
| **Dependencies** | Package Manager, Lock Files, Vulnerability Scanning |

---

## Quick Reference: Tooling by Language

| Language | Lint | Format | Type Check | Coverage | Fuzz |
|----------|------|--------|------------|----------|------|
| Python | Ruff | Ruff | Mypy, Pyright | pytest-cov | Hypothesis |
| Ruby | StandardRB | StandardRB | Sorbet | SimpleCov | - |
| Go | golangci-lint | gofmt | built-in | go test -cover | native |
| Rust | Clippy | rustfmt | built-in | cargo-tarpaulin | cargo-fuzz |
| C# | Roslynator | dotnet format | built-in | coverlet | SharpFuzz |
| TypeScript | Biome | Biome | built-in | c8 | - |
| SQL | SQLFluff | SQLFluff | - | - | - |
| Shell | shellcheck | shfmt | - | bashcov | - |
| CSS | Stylelint | Prettier | - | - | - |

---

## Tool Selection Rationale

### Python: Ruff
Ruff is a Python linter and formatter written in Rust, 10-100x faster than alternatives. It replaces Flake8, isort, Black, and many other tools with a single binary. Combined with uv for package management, this is the modern Python toolchain.

### Ruby: StandardRB
StandardRB provides zero-config linting built on RuboCop. It eliminates bikeshedding debates and provides sensible defaults. For teams needing custom rules, use RuboCop directly with StandardRB's config as a base.

### Go: golangci-lint
golangci-lint is a meta-linter aggregating 120+ linters including Staticcheck, gosec, and govet. It's 5x faster than running linters separately and is the de facto standard used by Kubernetes, Prometheus, and Terraform.

### Rust: Clippy + rustfmt
Clippy is the official Rust linter with 750+ lints. rustfmt is the official formatter. Both are included with the Rust toolchain. No alternatives come close.

### C#/.NET: Roslynator + dotnet format
Roslynator provides 500+ analyzers and refactorings. dotnet format (built into .NET SDK 6+) handles formatting via EditorConfig. Add SonarAnalyzer.CSharp for security analysis.

### TypeScript: Biome
Biome is 20x faster than ESLint+Prettier and combines linting and formatting. For legacy projects or those needing extensive plugin ecosystems, ESLint remains viable.

### SQL: SQLFluff
SQLFluff is the most popular SQL linter, supporting PostgreSQL, MySQL, SQLite, and 20+ dialects. It parses SQL to catch syntax issues and auto-fixes most problems.

---

## Configuration Files

Ready-to-copy configuration files:

| Config | Path | Purpose |
|--------|------|---------|
| EditorConfig | [configs/editorconfig/.editorconfig](configs/editorconfig/.editorconfig) | Editor settings |
| Prettier | [configs/prettier/.prettierrc](configs/prettier/.prettierrc) | Code formatting |
| Pre-commit | [configs/pre-commit/.pre-commit-config.yaml](configs/pre-commit/.pre-commit-config.yaml) | Git hooks |
| CLAUDE.md | [configs/claude/CLAUDE.md.template](configs/claude/CLAUDE.md.template) | AI assistant context |
| Cursor | [configs/cursor/.cursorrules.template](configs/cursor/.cursorrules.template) | Cursor AI rules |

---

## Attribution

Google style guides are licensed under CC-BY 3.0. Vendored copies in `reference/google/`.
