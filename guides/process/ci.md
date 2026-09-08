# CI/CD Guide

> [Doctrine](../../README.md) > [Process](../README.md) > CI/CD

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

Recommended GitHub Actions[^1] configurations per language/framework.

## General Principles

1. **Fast feedback**: **MUST** lint before test, fail fast
2. **Cache dependencies**: **SHOULD** use language-specific caching
3. **Matrix testing**: **SHOULD** test across OS/versions where relevant
4. **Security scanning**: **MUST** run on every PR
5. **Artifact preservation**: **SHOULD** save coverage reports, binaries

## Coverage Upload

Every workflow below uploads coverage with the same step. Only the report
path changes between languages.

- Uploads **MUST** authenticate with `CODECOV_TOKEN` or with OIDC. Codecov
  v4 and later removed ordinary tokenless uploading[^2].
- References **MUST** name a reviewed full commit SHA, because a moving
  major tag can be repointed at new code[^3].
- Uploads **MUST** set `fail_ci_if_error: true` wherever the project treats
  published coverage as required. The input defaults to `false`[^2].
- Uploads **SHOULD** name the report with `files` and set `disable_search:
  true`, so the step uploads exactly that report rather than whatever a
  recursive search happens to find. Combined with the default
  `handle_no_reports_found: false`, a renamed or missing report then fails
  the job[^2].

### Why

Codecov rejects an unauthenticated upload, but `fail_ci_if_error` defaults to
`false`, so the step still succeeds. The result is a green build whose
coverage was never published — the failure mode that coverage gating exists
to prevent. Authenticating and failing closed makes a missing report visible
at the point it is produced.

### Do

```yaml
- uses: codecov/codecov-action@fb8b3582c8e4def4969c97caa2f19720cb33a72f # v7.0.0
  with:
    files: coverage.xml
    disable_search: true
    fail_ci_if_error: true
    token: ${{ secrets.CODECOV_TOKEN }}
```

### Don't

```yaml
# Unauthenticated, moving tag, and fails open: publishes nothing, stays green
- uses: codecov/codecov-action@v4
  with:
    files: coverage.xml
```

### OIDC Instead of a Token

Repositories that prefer not to store an upload secret **MAY** authenticate
with OIDC. The action mints the token through `actions/github-script`, so the
job **MUST** grant `id-token: write`[^2].

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write
    steps:
      # ... checkout, build, test ...
      - uses: codecov/codecov-action@fb8b3582c8e4def4969c97caa2f19720cb33a72f # v7.0.0
        with:
          use_oidc: true
          files: coverage.xml
          disable_search: true
          fail_ci_if_error: true
```

Pull requests raised from a fork of a public repository upload without
credentials, so `secrets.CODECOV_TOKEN` being unavailable to forks does not
break them[^2]. Private repositories that accept fork pull requests **MUST**
guard the step with `if: github.event.pull_request.head.repo.fork != true`
rather than weakening `fail_ci_if_error`.

Where the test runner writes into a generated subdirectory, as .NET's
`--results-directory` does, set `directory` instead of `files` and leave
search enabled.

## Python

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync
      - run: uv run ruff check .
      - run: uv run ruff format --check .
      - run: uv run mypy src/

  test:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync
      - run: uv run pytest -n auto --cov=src --cov-report=xml
      - uses: codecov/codecov-action@fb8b3582c8e4def4969c97caa2f19720cb33a72f # v7.0.0
        with:
          files: coverage.xml
          disable_search: true
          fail_ci_if_error: true
          token: ${{ secrets.CODECOV_TOKEN }}

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync
      - run: uv run pip-audit
      - run: uv run semgrep --config=p/python --config=p/security-audit src/
```

### Django

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync
      - run: uv run ruff check .
      - run: uv run mypy .
      - run: uv run pytest --cov --reuse-db
        env:
          DATABASE_URL: postgres://postgres:postgres@localhost:5432/test
```

## Go

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: '1.23'
      - uses: golangci/golangci-lint-action@v6
        with:
          version: latest

  test:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: '1.23'
      - run: go test -race -coverprofile=coverage.out ./...
      - uses: codecov/codecov-action@fb8b3582c8e4def4969c97caa2f19720cb33a72f # v7.0.0
        with:
          files: coverage.out
          disable_search: true
          fail_ci_if_error: true
          token: ${{ secrets.CODECOV_TOKEN }}

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: '1.23'
      - run: go install golang.org/x/vuln/cmd/govulncheck@latest
      - run: govulncheck ./...
```

## Rust

Rust-specific lanes — MSRV, feature matrix, cross-target checks and fuzzing —
are in the [Rust Style Guide](../languages/rust.md). Actions are pinned to full
commit SHAs; see [Pinning Actions](../languages/rust/ci.md#pinning-actions).

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

env:
  CARGO_TERM_COLOR: always

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: dtolnay/rust-toolchain@6c977a6ca4077a0ceb28ffbe03f59d46e9ac8772 # v1
        with:
          toolchain: stable
          components: rustfmt, clippy
      - uses: Swatinem/rust-cache@6323deb102c322ba6fcbdcafc7e3dddab59af2b6 # v2.9.2
      - run: cargo fmt --check
      - run: cargo clippy --all-targets --all-features -- -D warnings

  test:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: dtolnay/rust-toolchain@6c977a6ca4077a0ceb28ffbe03f59d46e9ac8772 # v1
        with:
          toolchain: stable
      - uses: Swatinem/rust-cache@6323deb102c322ba6fcbdcafc7e3dddab59af2b6 # v2.9.2
      - run: cargo test --locked --all-features
      - run: cargo install --locked cargo-llvm-cov@0.9.1
      - run: cargo llvm-cov --locked --all-features --workspace
             --lcov --output-path lcov.info
      - uses: codecov/codecov-action@fb8b3582c8e4def4969c97caa2f19720cb33a72f # v7.0.0
        with:
          files: lcov.info
          disable_search: true
          fail_ci_if_error: true
          token: ${{ secrets.CODECOV_TOKEN }}

  security:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: dtolnay/rust-toolchain@6c977a6ca4077a0ceb28ffbe03f59d46e9ac8772 # v1
        with:
          toolchain: stable
      - run: cargo install --locked cargo-audit@0.22.2
      - run: cargo audit --file Cargo.lock
```

Rust security jobs **MUST** invoke `cargo audit` directly rather than through
`rustsec/audit-check`. That action declares `token` as a required input with
no default, so a step written without `with.token` aborts before the scan
runs with `Input required and not supplied: token`[^4].

### Why

`cargo audit` needs no GitHub token, so it works unchanged on pull requests
from forks, where the workflow token is read-only. It exits non-zero when the
advisory database matches a locked crate, which fails the job without extra
wiring. Add `--deny warnings` to fail on unmaintained, unsound, or yanked
crates as well.

Because no token is needed, the job also needs no `checks: write` or
`issues: write`; `contents: read` is sufficient, and every action above is
pinned to a full commit SHA so the workflow cannot change under a moving tag.

### Don't

```yaml
# Aborts before scanning: `token` is a required input with no default
- uses: rustsec/audit-check@v2
```

## Ruby

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ruby/setup-ruby@v1
        with:
          ruby-version: '3.3'
          bundler-cache: true
      - run: bundle exec standardrb

  test:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - uses: ruby/setup-ruby@v1
        with:
          ruby-version: '3.3'
          bundler-cache: true
      - run: bundle exec rspec
      - uses: codecov/codecov-action@fb8b3582c8e4def4969c97caa2f19720cb33a72f # v7.0.0
        with:
          files: coverage/coverage.xml
          disable_search: true
          fail_ci_if_error: true
          token: ${{ secrets.CODECOV_TOKEN }}

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ruby/setup-ruby@v1
        with:
          ruby-version: '3.3'
          bundler-cache: true
      - run: bundle exec bundler-audit check --update
```

SimpleCov's default output is `coverage/.resultset.json`, which Codecov's
uploader does not recognise as a coverage report. RSpec jobs **MUST**
therefore add the `simplecov-cobertura` gem[^5] and register its formatter so
the run also writes `coverage/coverage.xml`.

```ruby
# spec/spec_helper.rb
require 'simplecov'
require 'simplecov-cobertura'

SimpleCov.formatter = SimpleCov::Formatter::MultiFormatter.new([
  SimpleCov::Formatter::HTMLFormatter,
  SimpleCov::Formatter::CoberturaFormatter
])
SimpleCov.start do
  add_filter '/spec/'
  enable_coverage :branch
end
```

### Rails

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: postgres
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4
      - uses: ruby/setup-ruby@v1
        with:
          ruby-version: '3.3'
          bundler-cache: true
      - run: bundle exec standardrb
      - run: bundle exec brakeman --exit-on-warn --no-pager
      - run: bundle exec rails db:setup
        env:
          RAILS_ENV: test
          DATABASE_URL: postgres://postgres:postgres@localhost:5432/test
      - run: bundle exec rspec
```

## TypeScript / Node.js

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '22'
          cache: 'npm'
      - run: npm ci
      - run: npx biome ci .
      - run: npx tsc --noEmit

  test:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '22'
          cache: 'npm'
      - run: npm ci
      - run: npx vitest run --coverage --coverage.reporter=lcov
      - uses: codecov/codecov-action@fb8b3582c8e4def4969c97caa2f19720cb33a72f # v7.0.0
        with:
          files: coverage/lcov.info
          disable_search: true
          fail_ci_if_error: true
          token: ${{ secrets.CODECOV_TOKEN }}

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '22'
          cache: 'npm'
      - run: npm ci
      - run: npm audit --audit-level=high
```

## C# / .NET

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-dotnet@v4
        with:
          dotnet-version: '8.0.x'
      - run: dotnet restore
      - run: dotnet build --no-restore /p:TreatWarningsAsErrors=true
      - run: dotnet format --verify-no-changes

  test:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-dotnet@v4
        with:
          dotnet-version: '8.0.x'
      - run: dotnet test --collect:"XPlat Code Coverage" --results-directory ./coverage
      - uses: codecov/codecov-action@fb8b3582c8e4def4969c97caa2f19720cb33a72f # v7.0.0
        with:
          directory: ./coverage
          fail_ci_if_error: true
          token: ${{ secrets.CODECOV_TOKEN }}

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-dotnet@v4
        with:
          dotnet-version: '8.0.x'
      - run: dotnet list package --vulnerable --include-transitive
```

## Multi-Platform Matrix

For libraries/tools requiring cross-platform support:

```yaml
jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        # Add language version matrix as needed
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      # ... rest of steps
```

## Release Workflow

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    branches: [main]

permissions:
  contents: write
  pull-requests: write

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: googleapis/release-please-action@v4
        with:
          release-type: python  # or node, rust, go, etc.
```

## Dependabot

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    groups:
      python-deps:
        patterns:
          - "*"

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

## Branch Protection

Configure in repository settings:

- **MUST** require status checks to pass before merging
- **SHOULD** require branches to be up to date
- **SHOULD** require review from code owners
- **MUST NOT** allow bypassing the above settings

## See Also

- [Testing Guide](testing.md) - Testing strategy and best practices
- [Versioning Guide](versioning.md) - Semantic versioning and release automation
- [GitHub Templates](github-templates.md) - Issue and PR templates

## References

[^1]: [GitHub Actions Documentation](https://docs.github.com/en/actions)
[^2]: [codecov/codecov-action](https://github.com/codecov/codecov-action) - v7.0.0; documents that tokenless uploading is unsupported outside fork PRs to public repositories, that `fail_ci_if_error` defaults to `false`, and that `use_oidc` mints an Actions ID token
[^3]: [Security hardening for GitHub Actions](https://docs.github.com/en/actions/reference/security/secure-use) - pin third-party actions to a full-length commit SHA
[^4]: [rustsec/audit-check action metadata](https://github.com/rustsec/audit-check/blob/v2/action.yml) - declares `token` with `required: true` and no default
[^5]: [simplecov-cobertura](https://github.com/jessebs/simplecov-cobertura) - Cobertura XML formatter for SimpleCov
