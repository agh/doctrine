# Changelog

All notable changes to the Doctrine Style Guide will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.11.0] - 2026-01-02

### Added

- **Security Reference Library** (`reference/security/`) - Vendored security
  knowledge base
  - OWASP: Top 10, ASVS, Cheat Sheets, API Security
  - MITRE: ATT&CK framework, CWE mappings
  - NIST: Cybersecurity Framework, 800-53 controls
  - CIS: Benchmarks for Docker, Linux, Kubernetes
  - SLSA, SBOM, OpenSSF Scorecard standards
  - CVE/KEV/EPSS integration patterns
- **Security Agent Family** - 16 specialized security AI agents
  - `configs/claude/agents/security/security-architect.md` - Opus coordinator
  - `configs/claude/agents/security/threat-modeler.md` - STRIDE/PASTA analysis
  - `configs/claude/agents/security/code-security-reviewer.md` - SAST patterns
  - `configs/claude/agents/security/compliance-assessor.md` - SOC2, HIPAA, PCI-DSS
  - `configs/claude/agents/security/supply-chain-auditor.md` - Dependency analysis
  - `configs/claude/agents/security/incident-response-lead.md` - IR coordination
  - `configs/claude/agents/security/red-team-operator.md` - Offensive testing
  - `configs/claude/agents/security/detection-engineering.md` - SIEM rules
  - Plus 8 additional specialist agents
  - `guides/ai/security-agents.md` - Comprehensive family guide
- **System Agent Family** - 14 infrastructure review agents
  - `configs/claude/agents/system/architect.md` - Opus coordinator
  - `configs/claude/agents/system/docker.md` - Container security
  - `configs/claude/agents/system/ansible.md` - Playbook review
  - `configs/claude/agents/system/linux.md` - OS hardening
  - `configs/claude/agents/system/secrets.md` - SOPS/vault patterns
  - `configs/claude/agents/system/backup.md` - 3-2-1 rule compliance
  - `configs/claude/agents/system/networking.md` - Firewall, DNS, VPN
  - `configs/claude/agents/system/monitoring.md` - Prometheus, Grafana
  - `configs/claude/agents/system/database.md` - PostgreSQL config
  - `configs/claude/agents/system/traefik.md` - Reverse proxy, TLS
  - `configs/claude/agents/system/identity.md` - Authentik, OIDC
  - `configs/claude/agents/system/storage.md` - Garage, ZFS
  - `configs/claude/agents/system/messaging.md` - EMQX, Kafka
  - `configs/claude/agents/system/verify.md` - Build verification
  - `guides/ai/system-agents.md` - Comprehensive family guide
- **Code Agent Family** - 8 code quality agents
  - `configs/claude/agents/code/architect.md` - Opus coordinator
  - `configs/claude/agents/code/reviewer.md` - Multi-mode review with confidence
  scoring
  - `configs/claude/agents/code/performance.md` - N+1, caching, pooling patterns
  - `configs/claude/agents/code/accessibility.md` - WCAG 2.1 AA compliance
  - `configs/claude/agents/code/api-rest.md` - REST design review
  - `configs/claude/agents/code/api-graphql.md` - GraphQL schema review
  - `configs/claude/agents/code/simplifier.md` - Complexity reduction
  - `configs/claude/agents/code/test-writer.md` - Mutation-first testing
  - `guides/ai/code-agents.md` - Comprehensive family guide
- **Test Writer Agent v2** - Comprehensive AI-powered test generation
  - `configs/claude/agents/test-writer.md` - Enhanced with coverage targeting,
    validation loop, mutation testing
  - `configs/claude/agents/test-writer/python.md` - pytest patterns,
    coverage.py, mutmut
  - `configs/claude/agents/test-writer/javascript.md` - Jest/Vitest, React
    Testing Library, c8
  - `configs/claude/agents/test-writer/go.md` - go test, testify, table-driven
    tests, tarpaulin
  - `configs/claude/agents/test-writer/java.md` - JUnit 5, Mockito, AssertJ,
    JaCoCo, Spring Boot
  - `configs/claude/agents/test-writer/rust.md` - cargo test, mockall, proptest,
    tarpaulin/llvm-cov
- **Mutation-First Testing Philosophy** - Coverage is a byproduct, mutation
  score is the goal
  - Mutation score targets: 70% minimum, 80% standard, 90% critical,
    95% comprehensive
  - Mutation tools by language: mutmut, Stryker, go-mutesting, PIT,
    cargo-mutants
  - Mutation targeting workflow diagram with iterative mutant killing
- **Property-Based Testing Integration** - Cross-language property testing
  patterns
  - Common properties: Roundtrip, Idempotence, Commutativity, Associativity,
    Identity, Monotonicity
  - Libraries: Hypothesis (Python), proptest (Rust), fast-check (JS),
    gopter (Go), jqwik (Java)
- **Agent Composition** - Test-writer integrates with verify-build,
  code-reviewer, code-simplifier
- **Documentation Agent Suite** - Multi-agent documentation system
  - `configs/claude/agents/doc-architect.md` - Analyze codebase, create
    documentation plans
  - `configs/claude/agents/doc-writer.md` - Enhanced with Mermaid diagram
    generation
  - `configs/claude/agents/doc-reviewer.md` - Review docs for accuracy and
    completeness
  - `configs/claude/agents/doc-sync.md` - Detect stale documentation
  - `configs/claude/agents/doc-publisher.md` - Multi-format output (llms.txt,
    MCP, Mermaid)
- **Documentation Commands**
  - `/doc-plan` - Create prioritized documentation plan
  - `/doc-review` - Review documentation for accuracy
  - `/doc-sync` - Check documentation freshness
  - `/doc-publish` - Generate multi-format documentation
  - `/doc-status` - Show documentation coverage metrics
- **CI/CD Documentation Automation**
  - `.github/workflows/doc-sync.yml` - PR documentation sync checking
  - `.github/workflows/doc-lint.yml` - Documentation linting and validation
- **Documentation Quick Wins** (God Tier foundations)
  - Executable code examples in CI - validates Python, JS/TS, Shell code blocks
    with `# doctest: verify`
  - Version drift detection - compares documented versions vs package manifests
  - Documentation debt inventory - prioritized backlog with P0/P1/P2 classification
  - Self-healing documentation - `--fix` mode auto-repairs stale docs, creates PRs
  - Trend tracking - 90-day metrics history with ASCII charts
- **Documentation Agent Suite section** in AI guides README
- **Ops Agent Family** - 5 release and deployment agents
  - `configs/claude/agents/ops/architect.md` - Deployment coordinator
  - `configs/claude/agents/ops/changelog.md` - Changelog generation
  - `configs/claude/agents/ops/deploy-validator.md` - Pre-deploy checks
  - `configs/claude/agents/ops/rollback-advisor.md` - Rollback decisions
  - `configs/claude/agents/ops/release-manager.md` - Release automation
  - `guides/ai/release-manager-agent.md` - Comprehensive specification
- **Claude Skills** - Domain-specific knowledge modules
  - IoT: Home Assistant, ESPHome, Zigbee2MQTT, Tasmota, MQTT patterns
  - Databases: PostgreSQL optimization and patterns
  - Monitoring: Prometheus, VictoriaLogs configuration
  - Communication: GitHub, Discord integration patterns
- **AI Workflow Guides** - Comprehensive AI development patterns
  - `guides/ai/ai-workflows.md` - Hero Flow, TDD with AI, Visual Iteration
  - `guides/ai/claude-code.md` - CLI configuration, hooks, agents, MCP
  - Enhanced `guides/ai/agents-md.md` with advanced patterns
- **Framework Guide Expansions** - Production patterns for 7 frameworks
  - Axum: Auth (axum-login, JWT), WebSocket, rate limiting, caching
    (+1,853 lines)
  - Django: Async views, Celery, caching, security middleware (+1,585 lines)
  - FastAPI: Background tasks, caching, rate limiting, WebSocket
    (+1,079 lines)
  - Flask: Blueprints, extensions, caching, background jobs (+1,027 lines)
  - Gin: Middleware, auth, caching, rate limiting, WebSocket (+2,643 lines)
  - Next.js: Server components, caching, middleware, auth (+1,157 lines)
  - Rails: Hotwire, caching, background jobs, security (+963 lines)
- **Language Guide Expansions** - Advanced patterns for 4 languages
  - Go: Concurrency, error handling, testing patterns (+493 lines)
  - Python: Async, type hints, testing, performance (+825 lines)
  - Rust: Async, error handling, unsafe patterns (+904 lines)
  - TypeScript: Type utilities, React patterns, testing (+500 lines)
- **Infrastructure Guides** - OS and service hardening
  - `guides/infrastructure/os/linux.md` - Kernel, filesystem, audit hardening
  - `guides/infrastructure/services/ssh.md` - SSH security configuration
  - Enhanced Docker guide with security scanning, multi-stage builds

### Changed

- **README.md** - Updated agent inventory
  - Corrected count from "9 review agents" to "53 agents across 6 families"
  - Added Code Agents, Security Agents, System Agents to AI-Assisted
    Development table
- **Code Reviewer Agent** (`configs/claude/agents/code-reviewer.md`) - Mutation
  score integration
  - Added mutation score to review metrics header
  - Mutation score thresholds: <70% blocks merge, 70-79% warning,
    >=80% acceptable, >=90% for critical
  - Example review updated with mutation score analysis and surviving mutant
    details
- `configs/claude/agents/doc-writer.md` - Added diagram generation, tutorials,
  enhanced templates
- `configs/claude/agents/doc-sync.md` - Added version drift detection,
  self-healing protocol, `--fix` mode
- `configs/claude/commands/doc-sync.md` - Added `--versions`, `--fix`,
  `--dry-run` options with examples
- `configs/claude/commands/doc-status.md` - Added `--debt`, `--trends`,
  `--export` options with dashboards
- `.github/workflows/doc-lint.yml` - Added code example validation, version
  drift detection jobs
- **Code Simplifier Agent** (`configs/claude/agents/code-simplifier.md`) -
  Major enhancement
  - Comprehensive complexity metrics (cyclomatic, cognitive, Halstead,
    maintainability index)
  - Semantic preservation verification (I/O contracts, side effects,
    exceptions)
  - Confidence scoring (High/Medium/Low with percentages) and risk assessment
  - Fowler refactoring pattern catalog (Extract Method, Compose Method, etc.)
  - Multi-file dependency analysis with impact graphs
  - Test validation protocol (pre/post verification)
  - Language-specific modernization (Python, TypeScript, Go, Ruby, Rust)
  - Multi-agent integration (chains with code-reviewer, test-writer)
- **Refactor Command** (`configs/claude/commands/refactor.md`) - Enhanced options
  - Added `--explain`, `--metrics`, `--incremental`, `--safe` flags
  - Added comprehensive analysis protocol

## [2.10.0] - 2025-12-17

### Added

- **Vendored Industry Style Guides** (`reference/`)
  - Airbnb: JavaScript (148k stars), React, CSS-in-JS, Ruby
  - Uber: Go style guide (17.2k stars)
  - RuboCop: Ruby and Rails community guides
  - Shopify: Ruby style guide
  - Holywell: SQL style guide
  - Rust API Guidelines (14 files)
  - Google: JavaScript, JSON
- **Critical Guide Sections** (patterns linters cannot catch)
  - Go: Context propagation and error wrapping patterns
  - Ruby: Time zone handling (`Time.zone.now` vs `Time.now`)
  - Rust: Common trait implementations (orphan rule awareness)
  - SQL: Schema anti-patterns (EAV tables, time-partitioned names, unit
    separation)

## [2.9.0] - 2025-12-17

### Added

- **API Design Guides** (NEW SECTION)
  - `guides/api/README.md` - API design patterns overview
  - `guides/api/graphql.md` - GraphQL best practices (schema design, queries,
    mutations, security, performance)
  - `guides/api/rest.md` - REST best practices (resources, HTTP methods, status
    codes, pagination, caching)
- **Strawberry GraphQL Framework Guide**
  - `guides/frameworks/strawberry.md` - Python GraphQL with Strawberry
    (schemas, resolvers, DataLoaders, permissions, FastAPI/Django integration)

## [2.8.0] - 2025-12-17

### Added

- `guides/docs/specifications.md` - Specification writing guide for engineering
  docs
- `scripts/validate_versions.py` - Tool version validation script
- `SUMMARY.md` - Repository summary

### Changed

- `guides/frameworks/django.md` - Django 5.1 updates, async views, improved
  testing patterns
- `guides/frameworks/README.md` - Updated framework navigation
- `guides/docs/README.md`, `guides/docs/markdown.md` - Documentation
  improvements
- `guides/languages/shell.md`, `guides/languages/sql.md` - Minor updates
- `configs/pre-commit/.pre-commit-config.yaml` - Updated hook versions
- `configs/prettier/.prettierrc` - Configuration refinements
- `CLAUDE.md` - Project instructions updates

## [2.7.0] - 2025-12-17

### Added

- **Infrastructure Guides** (NEW SECTION)
  - `guides/infrastructure/README.md` - Infrastructure overview
  - `guides/infrastructure/ansible.md` - Ansible automation and configuration
    management
  - `guides/infrastructure/docker.md` - Docker containerization best practices
- **Ansible Configuration Templates**
  - `configs/ansible/` - ansible.cfg, .ansible-lint, .yamllint, .sops.yaml,
    requirements.yml

## [2.6.0] - 2025-12-17

### Changed

- **C# Guide Updates**
  - C# 13 and .NET 9 features (params collections, partial properties, ref
    struct interfaces)
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

- `guides/frameworks/rails.md` - Rails 8.0 updates, Solid Queue/Cache/Cable,
  Kamal deployment

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
  - `guides/design/design-systems.md` - Design tokens, typography, color
    systems, spacing, theming
  - `guides/design/components.md` - Reusable component patterns (buttons,
    inputs, cards, modals, tables)
  - `guides/design/accessibility.md` - WCAG 2.1 AA compliance, ARIA patterns,
    testing strategies
  - `guides/design/motion.md` - Animation principles, motion tokens,
    interaction feedback
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

[Unreleased]: https://github.com/welshwandering/doctrine/compare/v2.11.0...HEAD
[2.11.0]: https://github.com/welshwandering/doctrine/compare/v2.10.0...v2.11.0
[2.10.0]: https://github.com/welshwandering/doctrine/compare/v2.9.0...v2.10.0
[2.9.0]: https://github.com/welshwandering/doctrine/compare/v2.8.0...v2.9.0
[2.8.0]: https://github.com/welshwandering/doctrine/compare/v2.7.0...v2.8.0
[2.7.0]: https://github.com/welshwandering/doctrine/compare/v2.6.0...v2.7.0
[2.6.0]: https://github.com/welshwandering/doctrine/compare/v2.5.0...v2.6.0
[2.5.0]: https://github.com/welshwandering/doctrine/compare/v2.4.0...v2.5.0
[2.4.0]: https://github.com/welshwandering/doctrine/compare/v2.3.0...v2.4.0
[2.3.0]: https://github.com/welshwandering/doctrine/compare/v2.2.0...v2.3.0
[2.2.0]: https://github.com/welshwandering/doctrine/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/welshwandering/doctrine/compare/v2.0.1...v2.1.0
[2.0.1]: https://github.com/welshwandering/doctrine/compare/v2.0.0...v2.0.1
[2.0.0]: https://github.com/welshwandering/doctrine/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/welshwandering/doctrine/releases/tag/v1.0.0
