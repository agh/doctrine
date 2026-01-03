![Doctrine Style Guide](banner.svg)

# Doctrine Style Guide

**Version: 2.11.0** | [Changelog](CHANGELOG.md) | [AGENTS.md](AGENTS.md)

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

Canonical style guide for all projects. Vendored from
[Google Style Guides](https://github.com/google/styleguide) with
project-specific tooling and conventions. Each tool was selected as the
world-class option for its ecosystem in 2025.

**All projects MUST follow:**

- [Semantic Versioning 2.0.0](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
- [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)

See [versioning guide](guides/process/versioning.md) for details.

---

## Language Guides

| Language | Guide | Upstream |
| -------- | ----- | -------- |
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
| --------- | ----- | -------- |
| Axum | [guides/frameworks/axum.md](guides/frameworks/axum.md) | Rust |
| Django | [guides/frameworks/django.md](guides/frameworks/django.md) | Python |
| FastAPI | [guides/frameworks/fastapi.md](guides/frameworks/fastapi.md) | Python |
| Flask | [guides/frameworks/flask.md](guides/frameworks/flask.md) | Python |
| Gin | [guides/frameworks/gin.md](guides/frameworks/gin.md) | Go |
| Hanami | [guides/frameworks/hanami.md](guides/frameworks/hanami.md) | Ruby |
| Next.js | [guides/frameworks/nextjs.md](guides/frameworks/nextjs.md) | TypeScript |
| Rails | [guides/frameworks/rails.md](guides/frameworks/rails.md) | Ruby |
| React | [guides/frameworks/react.md](guides/frameworks/react.md) | TypeScript |
| Sinatra | [guides/frameworks/sinatra.md](guides/frameworks/sinatra.md) | Ruby |
| Strawberry | [guides/frameworks/strawberry.md](guides/frameworks/strawberry.md) | Python (GraphQL) |
| Tailwind CSS | [guides/frameworks/tailwind.md](guides/frameworks/tailwind.md) | CSS |

## AI-Assisted Development

| Topic | Guide | Description |
| ----- | ----- | ----------- |
| Overview | [guides/ai/README.md](guides/ai/README.md) | When and how to use AI assistance |
| **AI Workflows** | [guides/ai/ai-workflows.md](guides/ai/ai-workflows.md) | Hero Flow, TDD, Visual Iteration |
| Claude | [guides/ai/claude.md](guides/ai/claude.md) | Anthropic Claude best practices |
| **Claude Code** | [guides/ai/claude-code.md](guides/ai/claude-code.md) | CLI config: hooks, agents, commands |
| **Code Agents** | [guides/ai/code-agents.md](guides/ai/code-agents.md) | 8 agents: review, perf, a11y, API |
| **Security Agents** | [guides/ai/security-agents.md](guides/ai/security-agents.md) | 16 agents: threat modeling, compliance |
| **System Agents** | [guides/ai/system-agents.md](guides/ai/system-agents.md) | 14 agents: Docker, Ansible, networking |
| Local LLMs | [guides/ai/local-llms.md](guides/ai/local-llms.md) | Ollama, vLLM, Docker Model Runner |
| AGENTS.md | [guides/ai/agents-md.md](guides/ai/agents-md.md) | Project instruction files |
| Security | [guides/ai/security.md](guides/ai/security.md) | LLM security considerations |

## API Design Guides

| Protocol | Guide | Description |
| -------- | ----- | ----------- |
| GraphQL | [guides/api/graphql.md](guides/api/graphql.md) | Schema design, queries, mutations, security |
| REST | [guides/api/rest.md](guides/api/rest.md) | Resources, HTTP methods, status codes, pagination |

## Process Guides

| Topic | Guide |
| ----- | ----- |
| Testing | [guides/process/testing.md](guides/process/testing.md) |
| Versioning | [guides/process/versioning.md](guides/process/versioning.md) |
| CI/CD | [guides/process/ci.md](guides/process/ci.md) |
| GitHub Templates | [guides/process/github-templates.md](guides/process/github-templates.md) |

## Design Guides

| Topic | Guide | Description |
| ----- | ----- | ----------- |
| Overview | [guides/design/README.md](guides/design/README.md) | Design principles and process |
| Design Systems | [guides/design/design-systems.md](guides/design/design-systems.md) | Tokens, typography, color, spacing |
| Components | [guides/design/components.md](guides/design/components.md) | Reusable component patterns |
| Accessibility | [guides/design/accessibility.md](guides/design/accessibility.md) | WCAG compliance and inclusive design |
| Motion | [guides/design/motion.md](guides/design/motion.md) | Animation and interaction feedback |

## Infrastructure Guides

| Topic | Guide |
| ----- | ----- |
| Overview | [guides/infrastructure/README.md](guides/infrastructure/README.md) |
| **Operating Systems** | |
| Linux (Debian) | [guides/infrastructure/os/linux.md](guides/infrastructure/os/linux.md) |
| **Services** | |
| SSH | [guides/infrastructure/services/ssh.md](guides/infrastructure/services/ssh.md) |
| NTP | [guides/infrastructure/services/ntp.md](guides/infrastructure/services/ntp.md) |
| DNS | [guides/infrastructure/services/dns.md](guides/infrastructure/services/dns.md) |
| Firewall (nftables) | [guides/infrastructure/services/nftables.md](guides/infrastructure/services/nftables.md) |
| Logging | [guides/infrastructure/services/logging.md](guides/infrastructure/services/logging.md) |
| **Infrastructure as Code** | |
| Ansible | [guides/infrastructure/ansible.md](guides/infrastructure/ansible.md) |
| Docker | [guides/infrastructure/docker.md](guides/infrastructure/docker.md) |

## Documentation

| Topic | Guide |
| ----- | ----- |
| Overview | [guides/docs/README.md](guides/docs/README.md) |
| Markdown | [guides/docs/markdown.md](guides/docs/markdown.md) |
| Specifications | [guides/docs/specifications.md](guides/docs/specifications.md) |

---

## What Each Language Guide Covers

Every language guide **MUST** include:

| Category | Topics |
| -------- | ------ |
| **Code Quality** | Lint, Format, Type Check, Semantic Analysis, Dead Code |
| **Testing** | Unit, Integration, E2E, Acceptance, Performance |
| **Advanced Testing** | Thread Safety, Idempotence, Reliability, Compatibility |
| **Specialized** | i18n/UTF-8, Data Integrity, A/B Testing, Feature Flags |
| **Dependencies** | Package Manager, Lock Files, Vulnerability Scanning |

---

## Quick Reference: Tooling by Language

| Language | Lint | Format | Type Check | Coverage | Fuzz |
| -------- | ---- | ------ | ---------- | -------- | ---- |
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

Ruff is a Python linter and formatter written in Rust, 10-100x faster than
alternatives. It replaces Flake8, isort, Black, and many other tools with a
single binary. Combined with uv for package management, this is the modern
Python toolchain.

### Ruby: StandardRB

StandardRB provides zero-config linting built on RuboCop. It eliminates
bikeshedding debates and provides sensible defaults. For teams needing custom
rules, use RuboCop directly with StandardRB's config as a base.

### Go: golangci-lint

golangci-lint is a meta-linter aggregating 120+ linters including Staticcheck,
gosec, and govet. It is 5x faster than running linters separately and is the
de facto standard used by Kubernetes, Prometheus, and Terraform.

### Rust: Clippy + rustfmt

Clippy is the official Rust linter with 750+ lints. rustfmt is the official
formatter. Both are included with the Rust toolchain. No alternatives come
close.

### C#/.NET: Roslynator + dotnet format

Roslynator provides 500+ analyzers and refactorings. dotnet format (built into
.NET SDK 6+) handles formatting via EditorConfig. Add SonarAnalyzer.CSharp for
security analysis.

### TypeScript: Biome

Biome is 20x faster than ESLint+Prettier and combines linting and formatting.
For legacy projects or those needing extensive plugin ecosystems, ESLint
remains viable.

### SQL: SQLFluff

SQLFluff is the most popular SQL linter, supporting PostgreSQL, MySQL, SQLite,
and 20+ dialects. It parses SQL to catch syntax issues and auto-fixes most
problems.

---

## Configuration Files

Ready-to-copy configuration files:

| Config | Path | Purpose |
| ------ | ---- | ------- |
| **Agents** | [agents/](agents/) | 53 agents across 6 families |
| Ansible | [configs/ansible/](configs/ansible/) | Ansible configuration templates |
| AGENTS.md | [configs/agents/AGENTS.md.template](configs/agents/AGENTS.md.template) | AI assistant context |
| **Claude Code** | [configs/claude/](configs/claude/) | Hooks, settings, MCP config |
| EditorConfig | [configs/editorconfig/.editorconfig](configs/editorconfig/.editorconfig) | Editor settings |
| Pre-commit | [configs/pre-commit/.pre-commit-config.yaml](configs/pre-commit/.pre-commit-config.yaml) | Git hooks |
| Prettier | [configs/prettier/.prettierrc](configs/prettier/.prettierrc) | Code formatting |
| **Doctrine Sync** | [.github/workflows/sync-doctrine.yml](.github/workflows/sync-doctrine.yml) | Auto-sync configs to projects |

---

## Attribution

Google style guides are licensed under CC-BY 3.0. Vendored copies in `reference/google/`.

Industry style guides vendored in `reference/` for comparison:

- [Airbnb](reference/airbnb/) - JavaScript, React, CSS-in-JS, Ruby
- [Uber](reference/uber/) - Go
- [RuboCop](reference/rubocop/) - Ruby, Rails
- [Shopify](reference/shopify/) - Ruby
- [Holywell](reference/holywell/) - SQL
- [Rust API Guidelines](reference/rust/) - Rust
