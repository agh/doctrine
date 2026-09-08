# AGENTS.md Patterns Guide

> [Doctrine](../../README.md) > [AI](../README.md) > AGENTS.md Patterns

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in
[RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

## Table of Contents

1. [What is AGENTS.md](#what-is-agentsmd)
2. [Tool Compatibility via Symlinks](#tool-compatibility-via-symlinks)
3. [DRY Pattern: Reference Doctrine](#dry-pattern-reference-doctrine)
4. [File Placement Strategies](#file-placement-strategies)
5. [Essential Sections](#essential-sections)
6. [Templates by Project Type](#templates-by-project-type)
7. [Integration with Other Tools](#integration-with-other-tools)
8. [Maintenance Best Practices](#maintenance-best-practices)
9. [Anti-Patterns](#anti-patterns)
10. [Complete Example Templates](#complete-example-templates)

---

## What is AGENTS.md

### Definition

AGENTS.md is a markdown file that serves as a structured briefing document
for AI assistants working with a codebase[^9]. It provides essential context
that AI assistants cannot easily infer from code alone.

### Core Principles

An AGENTS.md file **MUST**:

1. **Be concise** - Provide necessary context without overwhelming detail
   (200-500 lines ideal)
2. **Be actionable** - Include concrete commands and examples
3. **Be discoverable** - Placed where AI assistants can find it
   (repository root)
4. **Be version-controlled** - Tracked in git alongside code
5. **Be current** - Updated as the project evolves

An AGENTS.md file **MUST NOT**:

1. **Replace comprehensive documentation** - It's a briefing, not a manual
2. **Include secrets** - Never include credentials or sensitive data
3. **Be auto-generated** - Manual curation ensures quality
4. **Duplicate style guides** - Link to external guides instead

### Why AGENTS.md Matters

**The Context Problem:** AI assistants lack persistent memory. Without
AGENTS.md, they must infer project structure, guess at conventions, and
discover commands through trial and error. This wastes time, introduces
errors, and creates inconsistency.

**The Solution:** A well-crafted AGENTS.md accelerates onboarding, ensures
consistency, prevents mistakes, and preserves tribal knowledge.

---

## Tool Compatibility via Symlinks

AI coding tools disagree about filenames. Codex, GitHub Copilot, and Cursor
read `AGENTS.md` natively[^4][^5][^2]; Claude Code reads `CLAUDE.md`[^1],
Gemini CLI reads `GEMINI.md`[^6], and Aider reads nothing it has not been
told to read[^3]. To support multiple tools with a single source of truth,
**MUST** use symlinks:

### Recommended Setup

```bash
# AGENTS.md is the canonical file
# Codex, GitHub Copilot and Cursor already discover it - no symlink needed
# Symlink only for tools whose default filename differs

ln -s AGENTS.md CLAUDE.md   # Claude Code
ln -s AGENTS.md GEMINI.md   # Gemini CLI
```

On Windows a symlink needs Administrator rights or Developer Mode, so a
`CLAUDE.md` whose only content is the import `@AGENTS.md` **MUST** be used
there instead[^1]. Aider is not covered by either file: it **MUST** be
pointed at the file explicitly, as described under
[Aider](#aider).

### Repository Structure

```text
my-project/
├── AGENTS.md          <- Canonical file (edit this one)
├── CLAUDE.md          <- Symlink -> AGENTS.md
├── GEMINI.md          <- Symlink -> AGENTS.md
├── README.md          <- Human documentation
├── src/
└── tests/
```

### Why Symlinks

| Approach | Pros | Cons |
| -------- | ---- | ---- |
| Symlinks | Single source of truth, no drift | Requires symlink support |
| Duplicates | Works everywhere | Content drift, maintenance burden |
| Single name | Simple | Some tools won't find it |

**Symlinks are the recommended approach** because they ensure all tools read
identical instructions while requiring only one file to maintain.

### Tool Discovery

Each tool has one default filename, its own hierarchy, and its own way of
being pointed at a different file. The table below was checked against vendor
documentation on 2026-09-08.

| Tool | Loaded by default | `AGENTS.md` support | Hierarchy and precedence | Imports | How to inspect what loaded |
| ---- | ----------------- | ------------------- | ------------------------ | ------- | -------------------------- |
| Codex[^4] | `AGENTS.override.md`, else `AGENTS.md` | Native | `~/.codex` first, then project root down to the working directory; nearer files override; truncated at `project_doc_max_bytes` (32 KiB) | No | `codex --ask-for-approval never "Summarize the current instructions."` |
| GitHub Copilot[^5] | `.github/copilot-instructions.md` | Native, in any directory | Nearest `AGENTS.md` in the directory tree wins; `.github/instructions/*.instructions.md` add path-scoped rules | No | Expand the references list on a Copilot Chat response |
| Cursor[^2] | `AGENTS.md`, `.cursor/rules/*.mdc` | Native, project root and subdirectories | Team → Project → User rules; nested `AGENTS.md` files combine, nearer files take precedence | `@file` references | **Customize → Rules** lists every rule and its status |
| Claude Code[^1] | `CLAUDE.md`, `.claude/CLAUDE.md`, `CLAUDE.local.md`, `.claude/rules/*.md` | Not read; import or symlink it | Root down to the working directory, concatenated; subdirectory files load when Claude reads those directories | `@AGENTS.md` | `/context`, then read **Memory files** |
| Gemini CLI[^6] | `GEMINI.md` | Add `AGENTS.md` to `context.fileName` in `settings.json` | `~/.gemini/GEMINI.md`, then workspace directories and their parents, then just-in-time files as tools touch directories | `@file.md` | `/memory show` |
| Aider[^3] | Nothing | `aider --read AGENTS.md`, or `read:` in `.aider.conf.yml` | Not applicable; every file is loaded explicitly | No | Aider prints `Added AGENTS.md to the chat` on start-up |

#### Why This Matters

A wrong entry in this table fails silently: the file is committed, the team
believes the tool is reading it, and the tool never loads it. Creating
`CLAUDE.md` does nothing for Aider, and creating `AGENTS.md` does nothing for
Claude Code or for an unconfigured Gemini CLI. **MUST** confirm discovery with
the inspection command in the last column before relying on a file.

---

## DRY Pattern: Reference Doctrine

Project AGENTS.md files **MUST** reference
[Doctrine](https://github.com/agh/doctrine) as the source of
truth for coding standards. This creates a "DRY for AI" pattern where:

- **Doctrine** contains canonical style guides, tooling choices, and
  conventions
- **Project AGENTS.md** contains only project-specific context

### Why This Matters

Without central standards, each project's AGENTS.md would duplicate:

- Language style guides (naming, formatting, patterns)
- Framework conventions (architecture, testing approaches)
- Tooling configuration (linters, formatters, CI)

This leads to drift, inconsistency, and maintenance burden.

### Required Standards Section

Every project AGENTS.md **MUST** begin with a Standards section:

```markdown
## Standards

This project follows [Doctrine](https://github.com/agh/doctrine):

| Concern | Guide |
| ------- | ----- |
| Python | [guides/languages/python.md][python] |
| Django | [guides/frameworks/django.md][django] |
| Testing | [guides/process/testing.md][testing] |

[python]: https://github.com/agh/doctrine/blob/main/guides/languages/python.md
[django]: https://github.com/agh/doctrine/blob/main/guides/frameworks/django.md
[testing]: https://github.com/agh/doctrine/blob/main/guides/process/testing.md

**Do not duplicate Doctrine guidance here.** This file contains only
project-specific context.
```

### What Belongs in Doctrine vs Project AGENTS.md

| In Doctrine | In Project AGENTS.md |
| ----------- | -------------------- |
| Python naming conventions | This project's directory structure |
| Django architecture patterns | Commands to run this project |
| Testing strategies | Environment variables needed |
| Tool versions and configs | Project-specific pitfalls |
| RFC 2119 requirements | Architecture decisions unique to this project |

### Benefits

1. **Single source of truth** - Update once, benefit everywhere
2. **Reduced maintenance** - Project files stay small and focused
3. **Consistency** - All projects follow identical standards
4. **AI efficiency** - AI can learn Doctrine once, apply everywhere

---

## File Placement Strategies

### Single Project Repository

For a single project, **MUST** place AGENTS.md at repository root:

```text
my-project/
├── AGENTS.md          <- AI context here
├── CLAUDE.md          <- Symlink
├── GEMINI.md          <- Symlink
├── README.md          <- Human documentation
├── src/
└── tests/
```

### Monorepo with Multiple Projects

For monorepos, **MUST** use hierarchical placement:

```text
monorepo/
├── AGENTS.md          <- Monorepo-level context
├── CLAUDE.md          <- Symlink
├── GEMINI.md          <- Symlink
├── services/
│   ├── api/
│   │   └── AGENTS.md  <- API-specific context
│   └── worker/
│       └── AGENTS.md  <- Worker-specific context
└── libs/
    └── shared/
        └── AGENTS.md  <- Shared library context
```

**Hierarchical Rules:**

- **Root AGENTS.md** contains: Monorepo structure, cross-cutting commands,
  shared conventions
- **Child AGENTS.md** contains: Service-specific context, commands,
  conventions
- **Child files** link back to parent for shared information

### Microservices Architecture

Each repository **MUST** have its own AGENTS.md. Include cross-service
references:

```markdown
## Related Services

- **user-service**: Authentication/authorization
  - Repository: https://github.com/org/user-service
  - Dependencies: We depend on their User model
```

---

## Essential Sections

Every AGENTS.md **MUST** contain these sections:

### 1. Overview

Provide high-level context in 3-5 lines:

```markdown
## Overview

API gateway for e-commerce platform. Routes requests to microservices,
handles authentication, and provides rate limiting.

**Stack:** Node.js 20, TypeScript 5.3, Express 4.18, Redis 7.2
**Purpose:** Centralized entry point for web, mobile, and third-party clients
```

### 2. Commands

Provide executable commands with expected outcomes:

````markdown
## Commands

### Development

```bash
npm install                    # Install dependencies
npm run dev                    # Start dev server (port 3000, hot reload)
npm run typecheck              # Type checking (strict mode)
```

### Testing

```bash
npm test                       # Run all tests
npm test -- --coverage         # Coverage report (requires 80%)
```
````

**MUST** include actual runnable commands with prerequisites.

### 3. Project Structure

Explain non-obvious directory organization:

````markdown
## Project Structure

```text
src/
├── api/           # Express route handlers
├── services/      # Business logic (DI-injectable)
├── models/        # TypeORM entities
└── middleware/    # Express middleware

tests/
├── unit/          # Unit tests (fast, isolated)
└── integration/   # Integration tests (DB required)
```

**Key Files:**

- `src/server.ts` - Application entry point
- `.env.example` - Required environment variables
````

### 4. Architecture

Document patterns and decisions:

````markdown
## Architecture

**Dependency Injection:** Using tsyringe. All services **MUST** be
injectable.

**Repository Pattern:** All database access **MUST** go through repositories.

**Data Flow:**

```text
Client -> Middleware -> Controller -> Service -> Repository -> Database
```
````

### 5. Code Style

Document conventions not captured in linters:

````markdown
## Code Style

Follows [Doctrine TypeScript Guide](../../guides/languages/typescript.md)

**Naming:**

- Files: `kebab-case.ts`
- Classes: `PascalCase`
- Functions: `camelCase`

**Import Ordering:**

```typescript
// 1. Node built-ins
// 2. External dependencies
// 3. Internal modules
// 4. Types
```
````

### 6. Common Pitfalls

Warn about known issues:

````markdown
## Common Pitfalls

### Database Connections

**ISSUE:** TypeORM doesn't automatically release connections

**SOLUTION:**

```typescript
const queryRunner = dataSource.createQueryRunner();
try {
  await queryRunner.startTransaction();
  // ... queries
  await queryRunner.commitTransaction();
} finally {
  await queryRunner.release();  // Always release!
}
```
````

### 7. Testing Strategy

Guide AI in writing tests:

````markdown
## Testing Strategy

- **Unit:** Jest with mocked dependencies (80% coverage minimum)
- **Integration:** Testcontainers for database tests
- **E2E:** Supertest for API tests (critical paths only)

**Example:**

```typescript
describe('UserService', () => {
  it('should hash password on creation', async () => {
    const user = await service.create({ password: 'secret' });
    expect(user.password).not.toBe('secret');
  });
});
```
````

### 8. Environment Configuration

Document required variables:

````markdown
## Environment Configuration

```bash
# Required
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
JWT_SECRET=your-secret-key-min-32-chars

# Optional
LOG_LEVEL=info              # debug | info | warn | error
FEATURE_NEW_UI=false        # Feature flags
```

**Secrets Management:** Use AWS Secrets Manager in production. Never commit
secrets.
````

---

## Templates by Project Type

### Python (FastAPI)

````markdown
# AGENTS.md - [Project Name]

## Overview

[1-2 sentence description]

**Stack:** Python 3.12, FastAPI 0.109, SQLAlchemy 2.0, PostgreSQL 16

## Commands

```bash
# Development
uv sync
uv run uvicorn app.main:app --reload

# Testing
uv run pytest --cov=src --cov-fail-under=80

# Database
uv run alembic upgrade head
```

## Structure

```text
src/
├── api/          # FastAPI routers
├── models/       # SQLAlchemy models
├── schemas/      # Pydantic schemas
└── services/     # Business logic
```

## Code Style

Follows [Doctrine Python Guide](../../guides/languages/python.md)

**Type Hints:** **MUST** use on all functions with
`from __future__ import annotations`

## Common Pitfalls

**Async/Await:** Never mix sync and async code. Use `AsyncSession` not
`Session`.

## Environment

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/dbname
SECRET_KEY=your-secret-key
```
````

### TypeScript (Express)

````markdown
# AGENTS.md - [Project Name]

## Overview

[1-2 sentence description]

**Stack:** Node.js 20, TypeScript 5.3, Express 4.18, PostgreSQL 16

## Commands

```bash
# Development
npm install
npm run dev

# Testing
npm test -- --coverage
```

## Structure

```text
src/
├── controllers/  # Request handlers
├── services/     # Business logic
├── models/       # TypeORM entities
└── middleware/   # Express middleware
```

## Code Style

Follows [Doctrine TypeScript Guide](../../guides/languages/typescript.md)

**Naming:** Files: `kebab-case.ts`, Classes: `PascalCase`, Functions:
`camelCase`

## Common Pitfalls

**Promise Handling:** Always use try/catch in async route handlers and pass
errors to `next()`.

## Environment

```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
JWT_SECRET=your-secret-key
```
````

### Go (Gin)

````markdown
# AGENTS.md - [Project Name]

## Overview

[1-2 sentence description]

**Stack:** Go 1.22, Gin 1.9, PostgreSQL 16, GORM 1.25

## Commands

```bash
# Development
go mod download
go run cmd/server/main.go

# Testing
go test ./...
go test -race ./...  # Race detection
```

## Structure

```text
cmd/server/       # Application entrypoint
internal/
├── api/          # HTTP handlers
├── service/      # Business logic
└── repository/   # Data access
```

## Code Style

Follows [Doctrine Go Guide](../../guides/languages/go.md)

**Error Handling:** Always wrap errors: `fmt.Errorf("get user: %w", err)`

## Common Pitfalls

**Goroutine Leaks:** Use context cancellation. **Pointer Receivers:** Use for
methods that modify state.

## Environment

```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
JWT_SECRET=your-secret-key
```
````

### Rails

````markdown
# AGENTS.md - [Project Name]

## Overview

[1-2 sentence description]

**Stack:** Ruby 3.3, Rails 7.1, PostgreSQL 16, Sidekiq 7

## Commands

```bash
# Development
bundle install
rails db:setup
rails server

# Testing
rails test
COVERAGE=true rails test
```

## Structure

```text
app/
├── controllers/  # Request handlers
├── models/       # ActiveRecord models
├── services/     # Service objects
└── jobs/         # Background jobs
```

## Code Style

Follows [Doctrine Rails Guide](../../guides/frameworks/rails.md)

**Service Objects:** Use for complex business logic outside controllers.

## Common Pitfalls

**N+1 Queries:** Use `includes()` for eager loading. **Mass Assignment:** Use
strong parameters.

## Environment

```bash
DATABASE_URL=postgresql://user:pass@localhost/dbname
REDIS_URL=redis://localhost:6379/0
SECRET_KEY_BASE=your-secret-key
```
````

### Django

````markdown
# AGENTS.md - [Project Name]

## Overview

[1-2 sentence description]

**Stack:** Python 3.12, Django 5.1, PostgreSQL 16, Celery 5.4, Redis 7

## Commands

```bash
# Development
uv sync
uv run python manage.py migrate
uv run python manage.py runserver

# Testing
uv run pytest --cov=apps --cov-fail-under=80

# Linting
uv run ruff check . --fix
uv run mypy apps/
```

## Structure

```text
config/
├── settings/         # Split settings (base, local, production)
│   ├── base.py
│   └── local.py
└── urls.py

apps/
├── users/            # User management app
│   ├── models.py
│   ├── views.py
│   ├── services.py   # Business logic
│   └── selectors.py  # Query logic
└── core/             # Shared utilities
```

## Code Style

Follows [Doctrine Django Guide](../../guides/frameworks/django.md)

**Fat Models, Thin Views:** Business logic in services, not views.

**Selectors Pattern:** Query logic in selectors, not views or models.

## Common Pitfalls

**N+1 Queries:** Use `select_related()` and `prefetch_related()`. Check with
django-debug-toolbar.

**Signals:** Use sparingly. Prefer explicit service calls for business logic.

**Async Views:** Use `async def` only with async ORM operations. Don't mix
sync/async.

## Environment

```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
SECRET_KEY=your-secret-key-min-50-chars
CELERY_BROKER_URL=redis://localhost:6379/0
```
````

### Flask

````markdown
# AGENTS.md - [Project Name]

## Overview

[1-2 sentence description]

**Stack:** Python 3.12, Flask 3.1, SQLAlchemy 2.0, PostgreSQL 16, Celery 5.4

## Commands

```bash
# Development
uv sync
uv run flask db upgrade
uv run flask run --debug

# Testing
uv run pytest --cov=src --cov-fail-under=80

# Linting
uv run ruff check . --fix
```

## Structure

```text
src/
├── __init__.py       # Application factory
├── models/           # SQLAlchemy models
├── routes/           # Blueprint route handlers
├── services/         # Business logic
├── schemas/          # Marshmallow/Pydantic schemas
└── extensions.py     # Flask extensions (db, migrate, etc.)

tests/
├── conftest.py       # Fixtures
└── test_*.py
```

## Code Style

Follows [Doctrine Flask Guide](../../guides/frameworks/flask.md)

**Application Factory:** Always use `create_app()` pattern.

**Blueprints:** Organize routes by domain (auth, users, api).

## Common Pitfalls

**Circular Imports:** Use application factory and import extensions from
`extensions.py`.

**Request Context:** Access `current_app` and `g` only within request context.

**SQLAlchemy Sessions:** Use `db.session` from Flask-SQLAlchemy, not raw
sessions.

## Environment

```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
SECRET_KEY=your-secret-key
FLASK_ENV=development
```
````

### Rust (Axum)

````markdown
# AGENTS.md - [Project Name]

## Overview

[1-2 sentence description]

**Stack:** Rust 1.83, Axum 0.8, SQLx 0.8, PostgreSQL 16, Tokio 1.43

## Commands

```bash
# Development
cargo build
cargo run

# Testing
cargo test
cargo test -- --nocapture  # See output

# Linting
cargo clippy -- -D warnings
cargo fmt --check

# Database
sqlx database create
sqlx migrate run
```

## Structure

```text
src/
├── main.rs           # Entry point, server setup
├── app.rs            # Router and state setup
├── config.rs         # Configuration loading
├── handlers/         # Request handlers
│   ├── mod.rs
│   └── users.rs
├── models/           # Domain models
├── repositories/     # Database access (SQLx)
├── services/         # Business logic
└── error.rs          # Error types and handling

migrations/           # SQLx migrations
tests/                # Integration tests
```

## Code Style

Follows [Doctrine Axum Guide](../../guides/frameworks/axum.md)

**Extractors:** Use typed extractors for request data. Validate with
`validator` crate.

**Error Handling:** Use `thiserror` for domain errors, implement
`IntoResponse`.

**State:** Use `AppState` with `Arc` for shared state.

## Common Pitfalls

**Async Runtime:** Always use `#[tokio::main]`. Don't block the runtime with
sync I/O.

**SQLx Compile-Time Checks:** Run `cargo sqlx prepare` before CI builds
without database.

**Ownership in Handlers:** Clone `Arc<AppState>` fields, don't fight the
borrow checker.

**Tower Middleware Order:** Middleware wraps in reverse order. Add logging
last (runs first).

## Environment

```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
JWT_SECRET=your-secret-key-min-32-chars
RUST_LOG=info,tower_http=debug
```
````

### Next.js

````markdown
# AGENTS.md - [Project Name]

## Overview

[1-2 sentence description]

**Stack:** Next.js 15, React 19, TypeScript 5.7, PostgreSQL 16, Prisma 6

## Commands

```bash
# Development
pnpm install
pnpm dev

# Testing
pnpm test
pnpm test:e2e

# Linting
pnpm lint
pnpm typecheck

# Database
pnpm prisma migrate dev
pnpm prisma generate
```

## Structure

```text
app/
├── (auth)/           # Auth route group (shared layout)
│   ├── login/
│   └── register/
├── (dashboard)/      # Dashboard route group
│   └── settings/
├── api/              # API routes
│   └── users/
├── layout.tsx        # Root layout
└── page.tsx          # Home page

components/
├── ui/               # Shadcn/UI components
└── features/         # Feature-specific components

lib/
├── db.ts             # Prisma client
├── auth.ts           # Auth.js config
└── actions/          # Server Actions
```

## Code Style

Follows [Doctrine Next.js Guide](../../guides/frameworks/nextjs.md)

**Server Components:** Default. Only add `'use client'` when needed.

**Server Actions:** Use for mutations. Validate with Zod.

**Data Fetching:** Fetch in Server Components, not useEffect.

## Common Pitfalls

**Hydration Mismatch:** Don't use `Date.now()` or `Math.random()` in Server
Components.

**Client/Server Boundary:** Can't pass functions or classes from Server to
Client Components.

**Caching:** `fetch()` caches by default. Use `{ cache: 'no-store' }` for
dynamic data.

**Server Actions Security:** Always validate input. Actions are public
endpoints.

## Environment

```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
NEXTAUTH_SECRET=your-secret-key
NEXTAUTH_URL=http://localhost:3000
```
````

---

## Integration with Other Tools

### Cursor

Cursor reads `AGENTS.md` from the project root and from subdirectories, and
combines nested files with parent files, so no Cursor-specific file is needed
for project context[^2]. Reach for `.cursor/rules/*.mdc` only when a rule must
be scoped rather than always applied:

- **AGENTS.md:** project context, commands, architecture; the root file
  applies broadly, a nested file applies when working in its directory tree
- **.cursor/rules/*.mdc:** rules attached by glob, selected by description, or
  invoked manually with `@rule-name`

A project rule is an `.mdc` file with frontmatter. A plain `.md` file in
`.cursor/rules/` is ignored because it carries no frontmatter[^2]:

```markdown
---
globs: src/components/**/*.tsx
alwaysApply: false
---

- Use named exports, not default exports
- See AGENTS.md for project-wide conventions
```

**`.cursorrules` is legacy.** Cursor still reads a root `.cursorrules`, but
documents it as pending deprecation and gives a migration path: copy the
content into a rule, set the rule type to **Always Apply**, and delete the
file[^7]. New projects **MUST NOT** create `.cursorrules`. Start from
[configs/cursor/rules/project-rules.mdc.template](../../configs/cursor/rules/project-rules.mdc.template)
instead.

### Aider

Aider discovers no instruction file by filename. Conventions **MUST** be
loaded explicitly, either per invocation or once in configuration[^3]:

```bash
aider --read AGENTS.md src/users/service.ts
```

```yaml
# .aider.conf.yml
read: AGENTS.md

# Multiple files
# read: [AGENTS.md, CONVENTIONS.md]
```

`--read` and `read:` mark the file read-only and let it be cached when prompt
caching is enabled[^3]. Aider prints `Added AGENTS.md to the chat` at start-up;
if that line is missing, nothing was loaded. Keep AGENTS.md concise
(< 1000 lines) so it fits in context alongside the files being edited.

### IDE Integration

Add to `.vscode/settings.json`:

```json
{
  "files.associations": {
    "AGENTS.md": "markdown",
    "CLAUDE.md": "markdown",
    "GEMINI.md": "markdown"
  }
}
```

---

## Maintenance Best Practices

### When to Update

**MUST** update when:

- Architecture changes (new patterns, refactoring)
- Commands change (new scripts, tool updates)
- Conventions change (style guide updates)
- New pitfalls discovered (production issues)
- Major dependencies change (framework upgrades)

### Update Process

1. **Review quarterly** - Schedule regular reviews
2. **Track in git** - Commit AGENTS.md changes with code changes
3. **Test with AI** - Verify AI assistants understand updates
4. **Keep concise** - Remove outdated content, don't just append

### Automated Checks

Add to CI/CD:

```yaml
# .github/workflows/lint.yml
- name: Check AGENTS.md exists
  run: |
    if [ ! -f AGENTS.md ]; then
      echo "AGENTS.md not found"
      exit 1
    fi

- name: Validate markdown
  run: npx markdownlint-cli2 AGENTS.md

- name: Check for secrets
  env:
    GITLEAKS_VERSION: 8.30.1
  run: |
    base="https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}"
    curl -sSfL -O "${base}/gitleaks_${GITLEAKS_VERSION}_linux_x64.tar.gz"
    curl -sSfL -O "${base}/gitleaks_${GITLEAKS_VERSION}_checksums.txt"
    sha256sum --check --ignore-missing "gitleaks_${GITLEAKS_VERSION}_checksums.txt"
    tar -xzf "gitleaks_${GITLEAKS_VERSION}_linux_x64.tar.gz" gitleaks
    ./gitleaks dir AGENTS.md --redact --no-banner --exit-code 1

- name: Verify symlinks
  run: |
    if [ -f CLAUDE.md ] && [ ! -L CLAUDE.md ]; then
      echo "CLAUDE.md should be a symlink to AGENTS.md"
      exit 1
    fi
```

Locally the same scan runs from the pinned Gitleaks pre-commit hook in
[configs/pre-commit/.pre-commit-config.yaml](../../configs/pre-commit/.pre-commit-config.yaml)[^8].

#### Why a Scanner, Not grep

A hand-written pattern such as `grep -r "password.*=.*[^example]" AGENTS.md`
does not do what it appears to do. `[^example]` is a negated *character* class:
one character that is not `e`, `x`, `a`, `m`, `p` or `l`. It never means "not
the word example". The pattern is also case-sensitive and knows only the word
`password`, so it misses every other credential shape.

Measured on the same fixtures, `grep` against Gitleaks v8.30.1[^8]:

| `AGENTS.md` content | `grep` | Gitleaks |
| ------------------- | ------ | -------- |
| `PASSWORD=` with a high-entropy value | missed | flagged |
| `api_token=ghp_...` GitHub token | missed | flagged |
| Live-shaped AWS key pair | missed | flagged |
| `-----BEGIN RSA PRIVATE KEY-----` block | missed | flagged |
| `password="example"` | false positive | clean |
| `password=example-value` | false positive | clean |
| `DATABASE_URL=postgresql://user:password@host:5432/db` | clean | clean |
| AWS documentation keys (`AKIAIOSFODNN7EXAMPLE`) | missed | clean |
| Token line ending `# gitleaks:allow` | missed | clean |

Two consequences follow. Intentional placeholders **MUST** be marked with a
trailing `# gitleaks:allow` comment or listed in `.gitleaksignore`, rather than
worded to dodge a regex. And `--redact` **MUST** stay on: without it a detected
credential is printed in full into CI logs that are often world-readable.

No scanner is complete. Gitleaks scores generic assignments on entropy, so a
short weak literal such as `password=hunter2` passes. Scanning is a backstop;
the rule that credentials never enter AGENTS.md still belongs to review.

---

## Anti-Patterns

### 1. The Novel (15,000 lines)

**Problem:** AGENTS.md becomes comprehensive documentation replacement

**Solution:**

- Keep under 1000 lines (200-500 ideal)
- Link to comprehensive docs
- Focus on what AI needs to know

### 2. The Stale Guide

**Problem:** Outdated commands and information

**Solution:**

- Review quarterly
- Update with major changes
- Add to PR checklist

### 3. The Secret Leaker

**Problem:** Contains credentials or sensitive data

**Solution:**

- Use placeholder values
- Reference `.env.example`
- Never commit secrets

### 4. The Copy-Paste Disaster

**Problem:** Duplicates README, docs, style guides

**Solution:**

- Link to external guides
- Summarize key points
- Document only deviations

### 5. The Vague Guide

**Problem:** Lacks specific, actionable information

**Solution:**

- Provide specific commands
- Include code examples
- Be concrete and actionable

### 6. The Assumed Knowledge

**Problem:** Assumes AI knows project-specific context

**Solution:**

- Be explicit about patterns
- Include examples
- Don't assume shared context

### 7. The Auto-Generated Mess

**Problem:** Auto-generated from code comments

**Solution:**

- Manually curate AGENTS.md
- Focus on high-level patterns
- Link to API docs for details

### 8. The Kitchen Sink

**Problem:** Includes everything tangentially related

**Solution:**

- Be selective
- Include only essential information
- Link to comprehensive sources

### 9. The Duplicate Files

**Problem:** Separate CLAUDE.md, GEMINI.md, etc. with different content

**Solution:**

- Use single AGENTS.md as source of truth
- Create symlinks for tool compatibility
- Never duplicate content across files

---

## Complete Example Templates

### Minimal Example (200 lines)

````markdown
# AGENTS.md - Todo API

## Overview

Simple REST API for todo list management. FastAPI backend with SQLite
database.

**Stack:** Python 3.12, FastAPI 0.109, SQLAlchemy 2.0, SQLite

## Commands

```bash
# Development
uv sync
uv run uvicorn app.main:app --reload  # Port 8000

# Testing
uv run pytest

# Linting
uv run ruff check . --fix
```

## Structure

```text
app/
├── main.py       # FastAPI entry point
├── models.py     # SQLAlchemy models
├── schemas.py    # Pydantic schemas
└── database.py   # DB connection

tests/            # Pytest tests
```

## Key Patterns

**Async by default:**

```python
@app.get("/todos")
async def get_todos(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Todo))
    return result.scalars().all()
```

**Validation:** All inputs use Pydantic schemas. Never accept raw dicts.

## Common Issues

**Database locking:** SQLite doesn't handle concurrent writes. Use PostgreSQL
for production.

**Async session:** Always use `AsyncSession`, not `Session`.

## Environment

```bash
DATABASE_URL=sqlite:///./todos.db
ENVIRONMENT=development
```
````

### Medium Example (500 lines)

See complete microservices e-commerce example in
[Python Template](#python-fastapi) section.

Key additions for medium projects:

- **Service Dependencies:** Document how services interact
- **Event Flow:** Show event-driven communication
- **Common Pitfalls:** More detailed with distributed systems issues
- **Testing Strategy:** Contract tests, integration tests
- **Monitoring:** Metrics, logs, tracing

### Large Projects

For large projects (> 5 services), split into:

1. **Main AGENTS.md** (500 lines) - Overview, quick start, architecture
2. **Service-specific AGENTS.md** (200-300 lines each)
3. **External docs links**

**Main AGENTS.md structure:**

````markdown
# AGENTS.md - [Platform Name]

## Overview

[High-level description]

## Quick Start

```bash
docker-compose up -d
npm run dev:all
```

## Architecture

[System-level architecture diagram]

## Service Navigation

- **API Gateway:** [services/api-gateway/AGENTS.md](services/api-gateway/AGENTS.md)
- **User Service:** [services/users/AGENTS.md](services/users/AGENTS.md)
- **Order Service:** [services/orders/AGENTS.md](services/orders/AGENTS.md)

## Cross-Cutting Concerns

[Shared patterns, auth, logging, monitoring]

## External Documentation

- [Full Docs](https://docs.example.com)
- [API Reference](https://api.example.com/docs)
````

---

## See Also

- [Testing Guide](../process/testing.md) - Testing strategies
- [CI/CD Guide](../process/ci.md) - Continuous integration
- [Markdown Guide](../docs/markdown.md) - Markdown style guide
- [Language Guides](../languages/README.md) - Python, TypeScript, Go, Ruby

---

## References

[^1]: [Claude Code memory](https://code.claude.com/docs/en/memory) - How
    Claude Code discovers `CLAUDE.md`, `.claude/rules/`, and `@AGENTS.md`
    imports
[^2]: [Cursor rules](https://cursor.com/docs/rules) - Project rules,
    `AGENTS.md` support, and rule precedence
[^3]: [Aider conventions](https://aider.chat/docs/usage/conventions.html) -
    Loading a conventions file with `--read` or `read:` in
    [`.aider.conf.yml`](https://aider.chat/docs/config/aider_conf.html)
[^4]: [Codex AGENTS.md](https://developers.openai.com/codex/guides/agents-md) -
    Instruction chain, override files, and discovery precedence
[^5]: [GitHub Copilot repository instructions](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/add-custom-instructions/add-repository-instructions) -
    `copilot-instructions.md`, path-specific instructions, and `AGENTS.md`
[^6]: [Gemini CLI context files](https://geminicli.com/docs/cli/gemini-md/) -
    Hierarchical `GEMINI.md` loading and the `context.fileName` setting
[^7]: [Cursor rules help](https://cursor.com/help/customization/rules) -
    Migration path from the legacy `.cursorrules` file
[^8]: [Gitleaks](https://github.com/gitleaks/gitleaks) - Secret scanner used
    by Doctrine's pre-commit configuration
[^9]: [AGENTS.md](https://agents.md) - The cross-tool convention this guide
    documents
