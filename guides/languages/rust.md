# Rust Style Guide

> [Doctrine](../../README.md) > [Languages](README.md) > Rust

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in
BCP 14 [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119)
[RFC 8174](https://datatracker.ietf.org/doc/html/rfc8174) when, and only
when, they appear in all capitals, as shown here.

This guide follows official Rust style conventions enforced by rustfmt[^1] and Clippy[^2].
It targets **Edition 2024** on **Rust 1.98.1**, the current stable release.[^30] Every
version quoted here is listed in [Tested Version Matrix](#tested-version-matrix) and was
current on 8 September 2026.

## Quick Reference

| Task | Tool | Command |
| ---- | ---- | ------- |
| Lint | Clippy[^2] | `cargo clippy --all-targets --all-features -- -D warnings` |
| Format | rustfmt[^1] | `cargo fmt --check` |
| Type check | built-in | `cargo check --all-targets` |
| Vulnerable dependencies | cargo-audit[^3] | `cargo audit` |
| Dependency policy | cargo-deny[^31] | `cargo deny check` |
| Unused dependencies | built-in | `cargo clippy` with `unused_crate_dependencies` in `[lints.rust]` |
| Coverage | cargo-llvm-cov[^8] | `cargo llvm-cov --all-features --fail-under-lines 80` |
| Cognitive complexity | Clippy[^2] | `cargo clippy`, threshold set in `clippy.toml` |
| Fuzz | cargo-fuzz[^5] | `cargo +nightly-2026-09-01 fuzz run my_target` |
| Property tests | proptest[^32] | `cargo test --test props` |
| Mutation tests | cargo-mutants[^33] | `cargo mutants --in-diff git.diff` |
| Public API compatibility | cargo-semver-checks[^34] | `cargo semver-checks` |
| Test suite throughput | cargo-nextest[^11] | `cargo nextest run --all-features` |
| Benchmarks | Criterion[^35] | `cargo bench` |
| Undefined behaviour | Miri[^26] | `cargo +nightly-2026-09-01 miri test` |

`cargo test -- --test-threads=N` controls libtest concurrency, not performance. Measure
performance with Criterion[^35] and suite wall-clock time with cargo-nextest[^11]; the two
concerns **MUST NOT** be conflated.

## Topic Guides

This guide holds the rules every Rust project needs. The topics below live in
their own guides so that a reader, human or agent, loads only the material a
task needs. Each topic guide assumes this one and does not repeat it.

| Topic | Read it when | Guide |
| ----- | ------------ | ----- |
| Rust API Design | designing or reviewing a public crate API, deriving traits, writing rustdoc | [rust/api-design.md](rust/api-design.md) |
| Async Runtimes | using Tokio or smol, writing async libraries, or migrating from async-std | [rust/async.md](rust/async.md) |
| Cargo Features | adding, testing or unifying Cargo features | [rust/features.md](rust/features.md) |
| Procedural Macros | writing or maintaining a proc-macro crate | [rust/macros.md](rust/macros.md) |
| Rust Testing Tools | writing tests, measuring coverage, fuzzing, benchmarking, or checking SemVer | [rust/testing.md](rust/testing.md) |
| Rust Testing Scenarios | adding E2E, resilience, compatibility, i18n or data-integrity tests | [rust/testing-scenarios.md](rust/testing-scenarios.md) |
| Unsafe Rust | writing or reviewing `unsafe` code, FFI bindings, or raw-pointer APIs | [rust/unsafe.md](rust/unsafe.md) |
| WebAssembly (WASM) | compiling to wasm32, using wasm-bindgen, or shipping a WASM package | [rust/wasm.md](rust/wasm.md) |

The [topic index](rust/README.md) lists the same guides.

## Toolchain, Edition and MSRV

New crates **MUST** use Edition 2024. Every crate **MUST** declare
`package.edition` and `package.rust-version`. Projects **MUST** pin the
development toolchain in `rust-toolchain.toml` and **MUST** test the declared
MSRV separately from current stable.

### Why

Cargo defaults an omitted `edition` to 2015, where `use quote::quote;` and
`use syn::...;` do not resolve without an `extern crate` declaration.[^27]
Edition 2024 has been stable since Rust 1.85.0 (20 February 2025) and is the
largest edition to date; it makes `extern` blocks and `no_mangle` explicitly
`unsafe`, changes `impl Trait` lifetime capture, and changes `if let`
temporary scopes.[^36]

The pinned toolchain and the MSRV answer different questions. `rust-toolchain.toml`
says which compiler contributors and CI use by default; `package.rust-version` is a
promise to downstream users about the oldest compiler that still builds the crate.
Conflating them either silently raises the MSRV or holds contributors on an old
compiler. Cargo enforces `rust-version` at resolution time, so an under-declared
MSRV surfaces as a dependency-resolution failure on a user's machine, not on yours.

### Configuration

```toml
# Cargo.toml
[package]
name = "my_crate"
version = "0.1.0"
edition = "2024"        # REQUIRED: an omitted edition defaults to 2015
rust-version = "1.94.0" # MSRV: a promise, not a preference
```

```toml
# rust-toolchain.toml — the development toolchain, not the MSRV
[toolchain]
channel = "1.98.1"
components = ["rustfmt", "clippy"]
targets = ["x86_64-unknown-linux-gnu", "wasm32-unknown-unknown"]
```

The MSRV **MUST** be at least the highest `rust-version` in the dependency
graph. For the crates this guide pins that floor is Rust 1.94.0, imposed by
SQLx 0.9.0; cucumber 0.23.0 requires 1.88, Criterion 0.8.2 requires 1.86, and
proptest 1.11.0 requires 1.85. A project that uses none of those can declare a
lower MSRV, but **MUST** compute it from its own graph rather than copying this
number.

```bash
# The MSRV floor imposed by the dependency graph
cargo metadata --format-version 1 --locked \
  | jq -r '.packages[] | select(.rust_version != null) | "\(.rust_version)\t\(.name)"' \
  | sort -V | tail -1
```

### CI Lanes

MSRV and stable **MUST** be separate jobs. A single "stable" lane proves
nothing about the MSRV, and an MSRV-only lane misses new lints and new
compiler behaviour.

```yaml
jobs:
  msrv:
    name: build (MSRV 1.94.0)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: dtolnay/rust-toolchain@6c977a6ca4077a0ceb28ffbe03f59d46e9ac8772 # v1
        with:
          toolchain: "1.94.0"   # exact, not `stable`
      - run: cargo check --locked --all-features

  stable:
    name: test (stable)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: dtolnay/rust-toolchain@6c977a6ca4077a0ceb28ffbe03f59d46e9ac8772 # v1
        with:
          toolchain: stable
      - run: cargo test --locked --all-features
```

```yaml
# BAD: one lane, no MSRV evidence. `stable` floats, so this job passes on the
# day the MSRV breaks and keeps passing until a user reports it.
jobs:
  test:
    steps:
      - uses: dtolnay/rust-toolchain@stable
      - run: cargo test
```

### Migrating an Existing Crate

```bash
# Report what the edition migration would change, then apply it
cargo fix --edition --allow-dirty
# Then set edition = "2024" in Cargo.toml and rebuild
cargo build --all-targets
```

Older editions remain fully supported and **MAY** be retained deliberately;
Edition 2021 is a compatibility choice, not a defect. A crate that stays on an
older edition **SHOULD** record why in its manifest or contributor
documentation.

## Linting: Clippy

Projects **MUST** use Clippy[^2] as the official Rust linter.

### Why Clippy

Clippy[^2] is the official Rust linter with 750+ lints. It's included with
rustup[^6], making it zero-cost to adopt. Unlike third-party linters, Clippy
has deep integration with the Rust compiler and is maintained by the Rust
team, ensuring compatibility with new language features and idiomatic Rust
patterns.

```bash
# Run Clippy
cargo clippy

# Treat warnings as errors
cargo clippy -- -D warnings

# Apply automatic fixes
cargo clippy --fix

# With all targets (including tests, examples)
cargo clippy --all-targets --all-features
```

### Configuration (Cargo.toml or clippy.toml)

Lint groups in `[lints.clippy]` **MUST** carry an explicit negative `priority`
when the same table also sets individual lints.

**Why**: Cargo ignores table order and resolves equal priorities as a conflict.
The configuration below without `priority = -1` fails the build outright:
"error: lint group `pedantic` has the same priority (0) as a lint ... note: the
order of the lints in the table is ignored by Cargo", emitted by the
`clippy::lint_groups_priority` lint, which is deny-by-default.[^2]

```toml
# Cargo.toml
[lints.clippy]
pedantic = { level = "warn", priority = -1 }
nursery = { level = "warn", priority = -1 }
unwrap_used = "deny"
expect_used = "deny"
panic = "deny"
```

```toml
# BAD: rejected by Cargo before any code is compiled.
[lints.clippy]
pedantic = "warn"
nursery = "warn"
unwrap_used = "deny"
```

Workspaces **SHOULD** declare the set once and inherit it:

```toml
# Workspace root Cargo.toml
[workspace.lints.clippy]
pedantic = { level = "warn", priority = -1 }
nursery = { level = "warn", priority = -1 }
unwrap_used = "deny"
expect_used = "deny"
panic = "deny"
```

```toml
# Member Cargo.toml
[lints]
workspace = true
```

Or in `clippy.toml`:

```toml
msrv = "1.94.0"
cognitive-complexity-threshold = 25
```

The `clippy.toml` `msrv` **MUST** equal `package.rust-version`. It is what
stops Clippy suggesting a replacement that the MSRV compiler does not have.

### Recommended Lint Groups

Projects **SHOULD** enable pedantic and nursery lint groups, and **MUST** deny
unwrap, expect and panic in production code. Test code **MUST** scope its
exception explicitly rather than relaxing the crate-wide policy:

```rust
// Unit tests: scope the allowance to the test module and say why.
#[cfg(test)]
#[allow(clippy::unwrap_used, clippy::expect_used, reason = "test-only allowance")]
mod tests {
    use super::*;

    #[test]
    fn parses_retries() {
        assert_eq!(parse_retries(" 3 ").unwrap(), 3);
    }
}
```

```rust
// Integration tests: `#[cfg(test)]` is not set for `tests/*.rs`, so the
// allowance goes at the top of the file.
#![allow(clippy::unwrap_used, clippy::expect_used, reason = "integration test")]
```

```rust
// BAD: crate-wide relaxation. Production code silently regains the right to
// panic, which is the thing the lint existed to prevent.
#![allow(clippy::unwrap_used)]
```

Production code **MUST** propagate errors instead:

```rust
// GOOD: the caller decides what to do about failure.
/// # Errors
///
/// Returns [`ParseError`] when `text` is not a decimal retry count.
pub fn parse_retries(text: &str) -> Result<u32, ParseError> {
    text.trim().parse().map_err(|_| ParseError::new(text))
}
```

```rust
// BAD: denied by `clippy::unwrap_used`, and aborts the process on bad input.
pub fn parse_retries(text: &str) -> u32 {
    text.trim().parse().unwrap()
}
```

## Formatting: rustfmt

Projects **MUST** use rustfmt[^1] for code formatting.

### Why rustfmt

rustfmt[^1] is the official Rust formatter, maintained by the Rust team. It
eliminates formatting debates and ensures consistent style across the entire
Rust ecosystem. Unlike other languages with competing formatters, rustfmt has
become the de facto standard with universal adoption.

```bash
# Format all code
cargo fmt

# Check formatting (CI)
cargo fmt -- --check
```

### Configuration (rustfmt.toml)

`rustfmt.toml` **MUST** contain only options that are stable on the channel CI
runs. Nightly-only options **MUST** be isolated in a separate, clearly labelled
configuration together with a pinned nightly toolchain.

**Why**: rustfmt silently degrades. Running `cargo fmt` on stable 1.9.0 with
`imports_granularity` and `group_imports` set prints
"Warning: can't set `imports_granularity = Crate`, unstable features are only
available in nightly channel" and exits **0**, so `cargo fmt --check` in CI
still passes while the imports are formatted differently from what the
configuration asks for. Both options are documented as **Stable: No** —
`imports_granularity` tracks rustfmt issue #4991 and `group_imports` tracks
rustfmt issue #5083.[^1]

```toml
# rustfmt.toml — stable-only. Every option here is Stable: Yes.
style_edition = "2024"
max_width = 100
tab_spaces = 4
use_small_heuristics = "Default"
reorder_imports = true
```

`style_edition` selects the Rust Style Guide edition and is inferred from
`edition` when omitted; setting it explicitly keeps formatting stable if the
crate's language edition later changes.[^1]

```toml
# BAD: two of these are nightly-only. Stable rustfmt warns and ignores them,
# and `cargo fmt --check` still exits 0.
edition = "2021"
imports_granularity = "Crate"
group_imports = "StdExternalCrate"
```

Projects that want merged and grouped imports **MUST** commit to nightly
rustfmt and pin it:

```toml
# rustfmt-nightly.toml — used only by the pinned nightly job below
unstable_features = true
imports_granularity = "Crate"
group_imports = "StdExternalCrate"
```

```bash
rustup toolchain install nightly-2026-09-01 --component rustfmt
cargo +nightly-2026-09-01 fmt -- --config-path rustfmt-nightly.toml --check
```

## Security Analysis: cargo-audit

Projects **MUST** run cargo-audit[^3] to check for known vulnerabilities in dependencies.

### Why cargo-audit

cargo-audit[^3] checks the crates in `Cargo.lock` against the RustSec Advisory
Database[^7]. It reports the advisory ID, the affected version range and the
first patched release for each finding, and exits non-zero, which is what makes
it usable as a CI gate. It reads the lockfile only, so it says nothing about
licences, duplicate versions or crate provenance — those belong to cargo-deny,
below.

```bash
# Install, pinned. --features=fix is REQUIRED for the `cargo audit fix`
# subcommand shown under "Vulnerability Scanning"; it is not in the default
# build.
cargo install cargo-audit --version 0.22.2 --locked --features=fix

# Check for vulnerabilities
cargo audit

# Generate lockfile and audit
cargo generate-lockfile
cargo audit
```

## Dependency Policy and Supply Chain

cargo-audit[^3] answers one question: are any dependencies subject to a
published advisory? Projects **MUST** also enforce a licence and provenance
policy. cargo-deny[^31] **MUST** be used for advisories, licences, banned
crates and permitted sources. cargo-vet[^43] **SHOULD** be used where audit
provenance is a requirement.

### Why

An advisory scan is a lower bound on supply-chain risk. It says nothing about a
GPL crate entering an MIT product, about two incompatible versions of the same
crate being linked in, or about a dependency being pulled from an unreviewed
git remote rather than crates.io. cargo-deny checks all four in one pass and
fails the build with a specific reason. cargo-vet goes further and records
which human or organisation audited each version, so an upgrade is a reviewable
event rather than a lockfile diff.

```bash
cargo install cargo-deny --version 0.20.2 --locked
cargo deny init
cargo deny check           # advisories, bans, licenses, sources
cargo deny check licenses  # one section at a time
```

```toml
# deny.toml
[advisories]
db-urls = ["https://github.com/RustSec/advisory-db"]
yanked = "deny"

[licenses]
allow = ["Apache-2.0", "MIT", "BSD-3-Clause", "Unicode-3.0"]
confidence-threshold = 0.93

[bans]
multiple-versions = "warn"
wildcards = "deny"       # `utils = "*"` never reaches a release build

[sources]
unknown-registry = "deny"
unknown-git = "deny"
allow-registry = ["https://github.com/rust-lang/crates.io-index"]
```

```bash
cargo install cargo-vet --version 0.10.2 --locked
cargo vet init           # records the current tree as the audit baseline
cargo vet                # fails on any unaudited new dependency
cargo vet suggest        # what still needs an audit
```

Repository-wide dependency policy, including update cadence and review
expectations, lives in the [CI Guide](../process/ci.md); the commands above are
the Rust-specific mechanism.

## Pre-commit Configuration

The canonical hook definitions are in
[`configs/pre-commit/.pre-commit-config.yaml`](../../configs/pre-commit/.pre-commit-config.yaml).
Projects **MUST** copy them from there rather than retyping them.

**Why**: a hook that differs from the canonical one by a flag produces a
different verdict locally and in review, and the difference is invisible until
a commit passes locally and fails in CI. `scripts/validate_versions.py` checks
that every local hook quoted in Doctrine matches the canonical entry, so drift
fails the repository's own checks.

```yaml
repos:
  - repo: local
    hooks:
      - id: cargo-fmt
        name: cargo fmt
        entry: cargo fmt --
        language: system
        types: [rust]
        pass_filenames: false

      - id: cargo-clippy
        name: cargo clippy
        entry: cargo clippy --all-targets --all-features -- -D warnings
        language: system
        types: [rust]
        pass_filenames: false
```

## CI Pipeline

Generic pipeline structure, caching and branch protection are in the
[CI Guide](../process/ci.md). This section covers only what is specific to
Rust: toolchain lanes, action pinning, and the audit job's permissions.

### Pinning Actions

Every action **MUST** be pinned to a full commit SHA with the human-readable
version in a trailing comment, and those pins **MUST** be kept current by
Dependabot or Renovate.

**Why**: a tag is a mutable pointer. `@v4` and `@stable` resolve to whatever
the owner has most recently pushed to that ref, so a compromised or simply
changed release runs in every workflow that references it, with the repository
token already in scope. A 40-character SHA is immutable; the version comment
keeps the pin reviewable, and an automated updater keeps it from rotting into a
years-old release.[^44]

Pinning by SHA also removes any default the tag carried.
`dtolnay/rust-toolchain` declares `toolchain` as a required input with no
default and fails with "'toolchain' is a required input" when it is missing —
`@stable` worked only because the branch name supplied the value. A SHA pin
**MUST** therefore pass `toolchain:` explicitly.

| Action | Pin | Version |
| ------ | --- | ------- |
| `actions/checkout` | `3d3c42e5aac5ba805825da76410c181273ba90b1` | v7.0.1 |
| `dtolnay/rust-toolchain` | `6c977a6ca4077a0ceb28ffbe03f59d46e9ac8772` | v1 |
| `Swatinem/rust-cache` | `6323deb102c322ba6fcbdcafc7e3dddab59af2b6` | v2.9.2 |
| `actions/cache` | `55cc8345863c7cc4c66a329aec7e433d2d1c52a9` | v6.1.0 |
| `actions/upload-artifact` | `043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` | v7.0.1 |

```yaml
# .github/dependabot.yml — keep the SHA pins current
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

```yaml
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
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: dtolnay/rust-toolchain@6c977a6ca4077a0ceb28ffbe03f59d46e9ac8772 # v1
        with:
          toolchain: stable
      - uses: Swatinem/rust-cache@6323deb102c322ba6fcbdcafc7e3dddab59af2b6 # v2.9.2
      - run: cargo test --locked --all-features
      - run: cargo test --locked --doc
      - run: cargo install cargo-llvm-cov --version 0.9.1 --locked
      - run: cargo llvm-cov --all-features --fail-under-lines 80

  audit:
    runs-on: ubuntu-latest
    permissions:
      contents: read   # no token is handed to a third party, so nothing more
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: dtolnay/rust-toolchain@6c977a6ca4077a0ceb28ffbe03f59d46e9ac8772 # v1
        with:
          toolchain: stable
      - run: cargo install --locked cargo-audit@0.22.2
      - run: cargo audit --file Cargo.lock
```

```yaml
# BAD: three mutable references. `@v4` and `@stable` are branches or moving
# tags, so what runs here is decided after review, by someone else.
steps:
  - uses: actions/checkout@v4
  - uses: dtolnay/rust-toolchain@stable
  - uses: rustsec/audit-check@v2
```

### Auditing Without a Token

The audit job **MUST** invoke `cargo audit` directly rather than through
`rustsec/audit-check`, and **MUST NOT** grant `checks: write` or
`issues: write` to run an advisory scan.

**Why**: `rustsec/audit-check` declares `token` as a required input with no
default, so using it means handing a write-capable `GITHUB_TOKEN` to a
third-party action on every run.[^28] The permissions are not separable per
event either: the Action reports through the Checks API for most events and
through the Issues API for `schedule` events, so a workflow that covers both
grants both writes on every run, and each individual run uses at most one of
them. `cargo audit` needs no token at all, exits non-zero when the advisory
database matches a locked crate, and therefore works unchanged on pull requests
from forks, where the workflow token is read-only. `--deny warnings` extends
the failure to unmaintained, unsound and yanked crates.

This matches the canonical Rust pipeline in the
[CI Guide](../process/ci.md#rust); the two **MUST NOT** diverge.

```yaml
# BAD: a write-capable token handed to a third-party action, with two write
# permissions granted so that one of them can be used per event.
permissions:
  checks: write
  issues: write
steps:
  - uses: rustsec/audit-check@69366f33c96575abad1ee0dba8212993eecbe998 # v2.0.0
    with:
      token: ${{ secrets.GITHUB_TOKEN }}
```

## Dependencies & Package Management

```bash
# Add dependencies
cargo add tokio
cargo add serde --features derive

# Update dependencies
cargo update
cargo update -p serde
```

### Cargo.lock Strategy

Projects **MUST** make a deliberate, documented choice. Committing
`Cargo.lock` **SHOULD** be the starting point for both binaries and libraries,
and every project that commits it **MUST** also test against latest
dependencies on a schedule.

**Why**: the old rule — binaries commit, libraries do not — was withdrawn by
the Cargo team on 29 August 2023. Their guidance is now "do what is best for
your project", with committing `Cargo.lock` as the suggested starting point,
and `cargo new` no longer ignores `Cargo.lock` for libraries. The reasoning is
that an ignored lockfile removes bisectable history, makes contributor CI fail
for reasons unrelated to the change under review whenever an upstream release
is yanked or broken, and leaves no place to pin a graph that still builds with
the declared MSRV — which pushed maintainers towards upper bounds on version
requirements, a worse outcome.[^45] The Cargo book states the same position:
"When in doubt, check `Cargo.lock` into the version control system".[^46]

| Concern | Commit `Cargo.lock` | Ignore `Cargo.lock` |
| ------- | ------------------- | ------------------- |
| Reproducible builds and bisecting | Yes | No |
| Contributor CI stability | Unaffected by upstream yanks | Breaks on upstream yanks |
| MSRV verification | A pinned graph that builds on the MSRV | Must be reconstructed each run |
| Latest-dependency coverage | Requires a scheduled `cargo update` job | Automatic, on every run |
| Binaries and reproducible artefacts | **Required** | Not acceptable |

```yaml
# The job a committed lockfile obliges you to add
jobs:
  latest-deps:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: dtolnay/rust-toolchain@6c977a6ca4077a0ceb28ffbe03f59d46e9ac8772 # v1
        with:
          toolchain: stable
      - run: cargo update            # ignore the committed lockfile
      - run: cargo test --all-features
```

```text
BAD: "libraries SHOULD NOT commit Cargo.lock". This was withdrawn in 2023
leaves the MSRV lane with no pinned graph to verify against.
```

`--locked` **MUST** be used in CI jobs that are meant to verify the committed
graph; without it Cargo silently updates the lockfile when a requirement no
longer resolves, and the job stops testing what the repository contains.

### Version Constraints

Library dependencies **SHOULD** use the default caret requirement. Executable
tools installed with `cargo install` **MUST** be pinned with `--version` and
`--locked`. Wildcard requirements **MUST NOT** be used.

**Why**: a caret requirement lets Cargo unify one copy of a dependency across
the graph; an upper bound or an exact pin in a library forces a second copy
into every consumer that wants a newer release, and two versions of a crate
that exposes types across an API boundary produce "expected struct `X`, found
struct `X`" errors. Wildcards are worse still: crates.io rejects a publish
that contains one, so `utils = "1.*"` blocks release. Executables are the
opposite case — nothing unifies them, and an unpinned `cargo install` in CI
means a new upstream release changes the build with no diff.

```toml
[dependencies]
# Caret (default): ^1.2.3 -> >=1.2.3 <2.0.0 — the right choice for a library
serde = "1.0"

# Tilde: ~1.2.3 -> >=1.2.3 <1.3.0 — only with a stated reason
tokio = "~1.53"

# Exact: =1.2.3 — only for a dependency with a known-broken newer release
critical-lib = "=1.2.3"
```

```toml
# BAD: crates.io rejects a publish containing a wildcard requirement.
utils = "1.*"
```

```bash
# GOOD: reproducible tool installs
cargo install cargo-nextest --version 0.9.143 --locked
```

```bash
# BAD: installs whatever is newest today
cargo install cargo-nextest
```

`--locked` uses the tool's own published `Cargo.lock`, so the build is the one
its author tested. Without it, a transitive dependency released an hour ago can
break the install.

### Vulnerability Scanning

`cargo audit fix --dry-run` **MUST** be run and its output reviewed before
`cargo audit fix`.

**Why**: `cargo audit fix` is not a report. Upstream states that it "will
modify `Cargo.toml` in place", and that the dry run is the way to "perform a
dry run instead, which shows a preview of what dependencies would be
upgraded".[^3] Running the mutating form first overwrites dependency
requirements before anyone has seen what it proposes; the change surfaces only
in the manifest diff or in the next failing build, and recovery depends on
version control or on retyping the requirements by hand. The feature is
labelled experimental upstream, which is a further reason to look before
writing.

```bash
# Install cargo-audit with the optional `fix` feature
cargo install cargo-audit --version 0.22.2 --locked --features=fix

# Run security audit
cargo audit

# ALWAYS preview first: this writes nothing
cargo audit fix --dry-run

# Only after reviewing the preview: this rewrites Cargo.toml in place
cargo audit fix
```

```bash
# BAD: rewrites Cargo.toml before anyone has seen the proposed change.
cargo audit fix
cargo audit fix --dry-run   # too late; the manifest is already modified
```

`cargo audit fix` **MUST NOT** be invoked from a default `cargo install
cargo-audit` build: the subcommand is compiled out unless the `fix` feature is
enabled, and the documented remediation step then fails with "error:
unrecognized subcommand 'fix'".[^3]

### Dependabot Configuration

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "cargo"
    directory: "/"
    schedule:
      interval: "weekly"
    groups:
      production:
        patterns:
          - "*"
```

## Tested Version Matrix

Every version below was current on crates.io, the Rust release channel or the
action's tag list on 8 September 2026, and the Rust examples in this guide were
compiled against them with `cargo check`, `cargo test` and
`cargo clippy -- -D warnings` on Rust 1.98.1.

Library requirements are written as caret ranges, which is what a manifest
**SHOULD** contain; the exact release tested is stated beside each. Executables
and actions are pinned exactly, because nothing unifies them.

### Toolchain

| Component | Tested | Notes |
| --------- | ------ | ----- |
| Rust stable | 1.98.1 (2026-09-01) | `rust-toolchain.toml` channel |
| Rust nightly | nightly-2026-09-01 | Miri, cargo-fuzz, nightly rustfmt |
| Edition | 2024 | Stable since Rust 1.85.0 |
| MSRV used in examples | 1.94.0 | Highest `rust-version` in the pinned graph (SQLx 0.9.0) |

### Libraries

| Crate | Requirement | Tested | Declared MSRV |
| ----- | ----------- | ------ | ------------- |
| serde | `1.0` | 1.0.229 | 1.56 |
| syn | `3.0.5` | 3.0.5 | 1.71 |
| quote | `1.0.47` | 1.0.47 | 1.71 |
| proc-macro2 | `1.0.107` | 1.0.107 | 1.71 |
| trybuild | `1.0.121` | 1.0.121 | 1.88 |
| darling | `0.24.1` | 0.24.1 | 1.88.0 |
| tokio | `1.53.1` | 1.53.1 | 1.71 |
| smol | `2.0.2` | 2.0.2 | 1.63 |
| cucumber | `0.23.0` | 0.23.0 | 1.88 |
| reqwest | `0.13.4` | 0.13.4 | 1.85.0 |
| loom | `0.7.2` | 0.7.2 | 1.65 |
| unicode-normalization | `0.1.25` | 0.1.25 (Unicode 17.0.0) | 1.36 |
| icu | `2.3.1` | 2.3.1 | 1.88 |
| sqlx | `0.9.0` | 0.9.0 | 1.94.0 |
| proptest | `1.11.0` | 1.11.0 | 1.85 |
| criterion | `0.8.2` | 0.8.2 | 1.86 |
| wasm-bindgen | `0.2.128` | 0.2.128 | 1.77 |
| wasm-bindgen-test | `0.3.78` | 0.3.78 | 1.77 |
| web-sys | `0.3.105` | 0.3.105 | 1.77 |
| js-sys | `0.3.105` | 0.3.105 | 1.77 |
| serde-wasm-bindgen | `0.6.5` | 0.6.5 | not declared |
| console_error_panic_hook | `0.1.7` | 0.1.7 | not declared |
| libfuzzer-sys | `0.4.13` | 0.4.13 | not declared |

### Executable Tools

Installed with `cargo install <tool> --version <exact> --locked`.

| Tool | Pin |
| ---- | --- |
| cargo-audit | 0.22.2 (`--features=fix`) |
| cargo-deny | 0.20.2 |
| cargo-vet | 0.10.2 |
| cargo-llvm-cov | 0.9.1 |
| cargo-tarpaulin | 0.37.2 |
| cargo-nextest | 0.9.143 |
| cargo-fuzz | 0.13.2 |
| afl | 0.18.2 |
| cargo-mutants | 27.1.0 |
| cargo-semver-checks | 0.50.0 |
| wasm-pack | 0.15.0 |
| wasm-opt | 0.116.1 |
| twiggy | 0.8.0 |

### GitHub Actions

Pinned by full commit SHA; see [Pinning Actions](#pinning-actions).

| Action | SHA | Version |
| ------ | --- | ------- |
| `actions/checkout` | `3d3c42e5aac5ba805825da76410c181273ba90b1` | v7.0.1 |
| `actions/cache` | `55cc8345863c7cc4c66a329aec7e433d2d1c52a9` | v6.1.0 |
| `actions/upload-artifact` | `043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` | v7.0.1 |
| `dtolnay/rust-toolchain` | `6c977a6ca4077a0ceb28ffbe03f59d46e9ac8772` | v1 |
| `Swatinem/rust-cache` | `6323deb102c322ba6fcbdcafc7e3dddab59af2b6` | v2.9.2 |

Maintaining this matrix is a scheduled task, not a one-off. Dependabot or
Renovate **MUST** cover both `cargo` and `github-actions` ecosystems so the
pins here are proposed for review rather than discovered when they break.

## References

[^1]: [rustfmt](https://github.com/rust-lang/rustfmt) - Official Rust code formatter
[^2]: [Clippy](https://github.com/rust-lang/rust-clippy) - Official Rust linter with 750+ lints
[^3]: [cargo-audit](https://github.com/rustsec/rustsec/tree/main/cargo-audit) - Audit Cargo.lock for security vulnerabilities
[^5]: [cargo-fuzz](https://github.com/rust-fuzz/cargo-fuzz) - Command-line wrapper for using libFuzzer
[^6]: [rustup](https://rustup.rs/) - Rust toolchain installer
[^7]: [RustSec Advisory Database](https://rustsec.org/) - Security advisory database for Rust crates
[^8]: [cargo-llvm-cov](https://github.com/taiki-e/cargo-llvm-cov) - Cargo subcommand for LLVM source-based code coverage
[^11]: [cargo-nextest](https://nexte.st/) - Next-generation test runner for Rust
[^26]: [Miri](https://github.com/rust-lang/miri) - Experimental interpreter for Rust's mid-level intermediate representation
[^27]: [The `edition` field](https://doc.rust-lang.org/cargo/reference/manifest.html#the-edition-field) - Cargo manifest reference
[^28]: [rustsec/audit-check action metadata](https://github.com/rustsec/audit-check/blob/v2/action.yml) - declares `token` with `required: true` and no default
[^30]: [Rust stable channel manifest](https://static.rust-lang.org/dist/channel-rust-stable.toml) - `[pkg.rust] version = "1.98.1 (48a229cea 2026-09-01)"`, manifest dated 2026-09-03
[^31]: [cargo-deny](https://github.com/EmbarkStudios/cargo-deny) - Advisory, licence, ban and source policy for Cargo dependencies
[^32]: [proptest](https://github.com/proptest-rs/proptest) - Hypothesis-style property testing with shrinking
[^33]: [cargo-mutants](https://github.com/sourcefrog/cargo-mutants) - Mutation testing for Rust
[^34]: [cargo-semver-checks](https://github.com/obi1kenobi/cargo-semver-checks) - Public API SemVer compliance checking
[^35]: [Criterion](https://github.com/criterion-rs/criterion.rs) - Statistics-driven benchmarking harness
[^36]: [Announcing Rust 1.85.0 and Rust 2024](https://blog.rust-lang.org/2025/02/20/Rust-1.85.0/) - Edition 2024 stabilisation, 20 February 2025; see the [Edition Guide](https://doc.rust-lang.org/edition-guide/rust-2024/index.html)
[^43]: [cargo-vet](https://mozilla.github.io/cargo-vet/) - Recording and enforcing dependency audits
[^44]: [Security hardening for GitHub Actions](https://docs.github.com/actions/security-for-github-actions) - Pinning actions to a full-length commit SHA
[^45]: [Change in Guidance on Committing Lockfiles](https://blog.rust-lang.org/2023/08/29/committing-lockfiles/) - The Cargo team's 2023 reversal
[^46]: [Cargo.toml vs Cargo.lock](https://doc.rust-lang.org/cargo/guide/cargo-toml-vs-cargo-lock.html) - "When in doubt, check Cargo.lock into the version control system"

## See Also

- [Rust API Guidelines](../../reference/rust/checklist.md) - The vendored
  upstream checklist this guide's API section is organised around
- [Testing Guide](../process/testing.md) - Test pyramid, coverage targets and
  flaky-test policy, which this guide does not repeat
- [CI Guide](../process/ci.md) - Pipeline structure, caching and branch
  protection
- [Versioning Guide](../process/versioning.md) - SemVer policy behind
  `cargo semver-checks`
- [Languages index](README.md) - The other language style guides
