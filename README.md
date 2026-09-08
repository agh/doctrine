![Doctrine Style Guide](banner.svg)

# Doctrine Style Guide

**Version: 2.11.0** | [Changelog](CHANGELOG.md) | [AGENTS.md](AGENTS.md)

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

Canonical style guide for all projects. Vendored from
[Google Style Guides](https://github.com/google/styleguide) with
project-specific tooling and conventions. Each tool was selected as the
best available option for its ecosystem as of September 2026, reviewed
quarterly.

**All projects MUST follow:**

- [Semantic Versioning 2.0.0](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
- [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)

See [versioning guide](guides/process/versioning.md) for details.

---

## Language Guides

| Language | Guide | Upstream |
| -------- | ----- | -------- |
| Overview | [guides/languages/README.md](guides/languages/README.md) | — |
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
| Overview | [guides/frameworks/README.md](guides/frameworks/README.md) | — |
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
| OpenAI | [guides/ai/openai.md](guides/ai/openai.md) | OpenAI GPT and Codex best practices |
| Gemini | [guides/ai/gemini.md](guides/ai/gemini.md) | Google Gemini best practices |
| **Claude Code** | [guides/ai/claude-code.md](guides/ai/claude-code.md) | CLI config: hooks, agents, commands |
| **Code Agents** | [guides/ai/code-agents.md](guides/ai/code-agents.md) | 8 agents: review, perf, a11y, API |
| **Security Agents** | [guides/ai/security-agents.md](guides/ai/security-agents.md) | 16 agents: threat modeling, compliance |
| **System Agents** | [guides/ai/system-agents.md](guides/ai/system-agents.md) | 14 agents: Docker, Ansible, networking |
| Release Manager | [guides/ai/release-manager-agent.md](guides/ai/release-manager-agent.md) | Release automation and quality gates |
| Local LLMs | [guides/ai/local-llms.md](guides/ai/local-llms.md) | Ollama, vLLM, Docker Model Runner |
| AGENTS.md | [guides/ai/agents-md.md](guides/ai/agents-md.md) | Project instruction files |
| Security | [guides/ai/security.md](guides/ai/security.md) | LLM security considerations |

## API Design Guides

| Protocol | Guide | Description |
| -------- | ----- | ----------- |
| Overview | [guides/api/README.md](guides/api/README.md) | API design index |
| GraphQL | [guides/api/graphql.md](guides/api/graphql.md) | Schema design, queries, mutations, security |
| REST | [guides/api/rest.md](guides/api/rest.md) | Resources, HTTP methods, status codes, pagination |

## Process Guides

| Topic | Guide |
| ----- | ----- |
| Overview | [guides/process/README.md](guides/process/README.md) |
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
| Fundamentals | [guides/infrastructure/os/README.md](guides/infrastructure/os/README.md) |
| Linux (Debian) | [guides/infrastructure/os/linux.md](guides/infrastructure/os/linux.md) |
| **Services** | |
| Services Overview | [guides/infrastructure/services/README.md](guides/infrastructure/services/README.md) |
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
| **Commands** | [commands/](commands/) | 18 slash commands (`/code`, `/security`, ...) |
| Ansible | [configs/ansible/](configs/ansible/) | Ansible configuration templates |
| AGENTS.md | [configs/agents/AGENTS.md.template](configs/agents/AGENTS.md.template) | AI assistant context |
| **Claude Code** | [configs/claude/](configs/claude/) | Hooks, settings, MCP config |
| EditorConfig | [configs/editorconfig/.editorconfig](configs/editorconfig/.editorconfig) | Editor settings |
| Pre-commit | [configs/pre-commit/.pre-commit-config.yaml](configs/pre-commit/.pre-commit-config.yaml) | Git hooks |
| Prettier | [configs/prettier/.prettierrc](configs/prettier/.prettierrc) | Code formatting |
| **Doctrine Sync** | [.github/workflows/sync-doctrine.yml](configs/github/workflows/sync-doctrine.yml) | Auto-sync configs to projects |

---

## Reference material

`reference/` holds third-party guides vendored verbatim for offline reading and
comparison. Doctrine does not modify them; report problems upstream. Google
style guides are licensed under CC-BY 3.0.

| Vendored file | Upstream project |
| ------------- | ---------------- |
| [reference/airbnb/css-in-javascript.md](reference/airbnb/css-in-javascript.md) | [airbnb/javascript](https://github.com/airbnb/javascript) |
| [reference/airbnb/javascript.md](reference/airbnb/javascript.md) | [airbnb/javascript](https://github.com/airbnb/javascript) |
| [reference/airbnb/react.md](reference/airbnb/react.md) | [airbnb/javascript](https://github.com/airbnb/javascript) |
| [reference/airbnb/ruby.md](reference/airbnb/ruby.md) | [airbnb/ruby](https://github.com/airbnb/ruby) |
| [reference/google/csharp.md](reference/google/csharp.md) | [google/styleguide](https://github.com/google/styleguide) |
| [reference/google/go-best-practices.md](reference/google/go-best-practices.md) | [google/styleguide](https://github.com/google/styleguide) |
| [reference/google/go-decisions.md](reference/google/go-decisions.md) | [google/styleguide](https://github.com/google/styleguide) |
| [reference/google/go.md](reference/google/go.md) | [google/styleguide](https://github.com/google/styleguide) |
| [reference/google/htmlcss.html](reference/google/htmlcss.html) | [google/styleguide](https://github.com/google/styleguide) |
| [reference/google/javascript.html](reference/google/javascript.html) | [google/styleguide](https://github.com/google/styleguide) |
| [reference/google/json.xml](reference/google/json.xml) | [google/styleguide](https://github.com/google/styleguide) |
| [reference/google/markdown.md](reference/google/markdown.md) | [google/styleguide](https://github.com/google/styleguide) |
| [reference/google/python.md](reference/google/python.md) | [google/styleguide](https://github.com/google/styleguide) |
| [reference/google/shell.md](reference/google/shell.md) | [google/styleguide](https://github.com/google/styleguide) |
| [reference/google/typescript.html](reference/google/typescript.html) | [google/styleguide](https://github.com/google/styleguide) |
| [reference/holywell/sql.md](reference/holywell/sql.md) | [treffynnon/sqlstyle.guide](https://github.com/treffynnon/sqlstyle.guide) |
| [reference/ietf/rfc2119.txt](reference/ietf/rfc2119.txt) | [IETF RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119) |
| [reference/rubocop/rails.adoc](reference/rubocop/rails.adoc) | [rubocop/rails-style-guide](https://github.com/rubocop/rails-style-guide) |
| [reference/rubocop/ruby.adoc](reference/rubocop/ruby.adoc) | [rubocop/ruby-style-guide](https://github.com/rubocop/ruby-style-guide) |
| [reference/rust/about.md](reference/rust/about.md) | [rust-lang/api-guidelines](https://github.com/rust-lang/api-guidelines) |
| [reference/rust/api-guidelines-summary.md](reference/rust/api-guidelines-summary.md) | [rust-lang/api-guidelines](https://github.com/rust-lang/api-guidelines) |
| [reference/rust/checklist.md](reference/rust/checklist.md) | [rust-lang/api-guidelines](https://github.com/rust-lang/api-guidelines) |
| [reference/rust/debuggability.md](reference/rust/debuggability.md) | [rust-lang/api-guidelines](https://github.com/rust-lang/api-guidelines) |
| [reference/rust/dependability.md](reference/rust/dependability.md) | [rust-lang/api-guidelines](https://github.com/rust-lang/api-guidelines) |
| [reference/rust/documentation.md](reference/rust/documentation.md) | [rust-lang/api-guidelines](https://github.com/rust-lang/api-guidelines) |
| [reference/rust/flexibility.md](reference/rust/flexibility.md) | [rust-lang/api-guidelines](https://github.com/rust-lang/api-guidelines) |
| [reference/rust/future-proofing.md](reference/rust/future-proofing.md) | [rust-lang/api-guidelines](https://github.com/rust-lang/api-guidelines) |
| [reference/rust/interoperability.md](reference/rust/interoperability.md) | [rust-lang/api-guidelines](https://github.com/rust-lang/api-guidelines) |
| [reference/rust/macros.md](reference/rust/macros.md) | [rust-lang/api-guidelines](https://github.com/rust-lang/api-guidelines) |
| [reference/rust/naming.md](reference/rust/naming.md) | [rust-lang/api-guidelines](https://github.com/rust-lang/api-guidelines) |
| [reference/rust/necessities.md](reference/rust/necessities.md) | [rust-lang/api-guidelines](https://github.com/rust-lang/api-guidelines) |
| [reference/rust/predictability.md](reference/rust/predictability.md) | [rust-lang/api-guidelines](https://github.com/rust-lang/api-guidelines) |
| [reference/rust/type-safety.md](reference/rust/type-safety.md) | [rust-lang/api-guidelines](https://github.com/rust-lang/api-guidelines) |
| [reference/shopify/ruby.md](reference/shopify/ruby.md) | [Shopify/ruby-style-guide](https://github.com/Shopify/ruby-style-guide) |
| [reference/uber/go.md](reference/uber/go.md) | [uber-go/guide](https://github.com/uber-go/guide) |

- [Airbnb](reference/airbnb/) - JavaScript, CSS-in-JS, Ruby; the
  [React snapshot](reference/airbnb/react.md) is historical (2021) and superseded by the
  [React style guide](guides/frameworks/react.md)
- [Uber](reference/uber/) - Go
- [RuboCop](reference/rubocop/) - Ruby, Rails
- [Shopify](reference/shopify/) - Ruby
- [Holywell](reference/holywell/) - SQL
- [Rust API Guidelines](reference/rust/) - Rust
