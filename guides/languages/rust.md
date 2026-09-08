# Rust Style Guide

> [Doctrine](../../README.md) > [Languages](README.md) > Rust

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in
BCP 14 [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119)
[RFC 8174](https://datatracker.ietf.org/doc/html/rfc8174) when, and only
when, they appear in all capitals, as shown here.

This guide follows official Rust style conventions enforced by rustfmt[^1] and Clippy[^2]. It
targets **Edition 2024** on **Rust 1.98.1**, the current stable release.[^30] Every version quoted
here is listed in [Tested Version Matrix](rust/versions.md#tested-version-matrix) and was current on
8 September 2026.

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
| CI Pipeline | writing or reviewing a Rust CI workflow | [rust/ci.md](rust/ci.md) |
| Dependencies and Supply Chain | adding or updating a dependency, choosing a Cargo.lock strategy, or auditing the graph | [rust/dependencies.md](rust/dependencies.md) |
| Cargo Features | adding, testing or unifying Cargo features | [rust/features.md](rust/features.md) |
| Procedural Macros | writing or maintaining a proc-macro crate | [rust/macros.md](rust/macros.md) |
| Rust Testing Tools | writing tests, measuring coverage, fuzzing, benchmarking, or checking SemVer | [rust/testing.md](rust/testing.md) |
| Rust Testing Scenarios | adding E2E, resilience, compatibility, i18n or data-integrity tests | [rust/testing-scenarios.md](rust/testing-scenarios.md) |
| Unsafe Rust | writing or reviewing `unsafe` code, FFI bindings, or raw-pointer APIs | [rust/unsafe.md](rust/unsafe.md) |
| Tested Version Matrix | pinning or updating any version quoted in the Rust guides | [rust/versions.md](rust/versions.md) |
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

## References

[^1]: [rustfmt](https://github.com/rust-lang/rustfmt) - Official Rust code formatter
[^2]: [Clippy](https://github.com/rust-lang/rust-clippy) - Official Rust linter with 750+ lints
[^3]: [cargo-audit](https://github.com/rustsec/rustsec/tree/main/cargo-audit) - Audit Cargo.lock for security vulnerabilities
[^5]: [cargo-fuzz](https://github.com/rust-fuzz/cargo-fuzz) - Command-line wrapper for using libFuzzer
[^6]: [rustup](https://rustup.rs/) - Rust toolchain installer
[^8]: [cargo-llvm-cov](https://github.com/taiki-e/cargo-llvm-cov) - Cargo subcommand for LLVM source-based code coverage
[^11]: [cargo-nextest](https://nexte.st/) - Next-generation test runner for Rust
[^26]: [Miri](https://github.com/rust-lang/miri) - Experimental interpreter for Rust's mid-level intermediate representation
[^27]: [The `edition` field](https://doc.rust-lang.org/cargo/reference/manifest.html#the-edition-field) - Cargo manifest reference
[^30]: [Rust stable channel manifest](https://static.rust-lang.org/dist/channel-rust-stable.toml) - `[pkg.rust] version = "1.98.1 (48a229cea 2026-09-01)"`, manifest dated 2026-09-03
[^31]: [cargo-deny](https://github.com/EmbarkStudios/cargo-deny) - Advisory, licence, ban and source policy for Cargo dependencies
[^32]: [proptest](https://github.com/proptest-rs/proptest) - Hypothesis-style property testing with shrinking
[^33]: [cargo-mutants](https://github.com/sourcefrog/cargo-mutants) - Mutation testing for Rust
[^34]: [cargo-semver-checks](https://github.com/obi1kenobi/cargo-semver-checks) - Public API SemVer compliance checking
[^35]: [Criterion](https://github.com/criterion-rs/criterion.rs) - Statistics-driven benchmarking harness
[^36]: [Announcing Rust 1.85.0 and Rust 2024](https://blog.rust-lang.org/2025/02/20/Rust-1.85.0/) - Edition 2024 stabilisation, 20 February 2025; see the [Edition Guide](https://doc.rust-lang.org/edition-guide/rust-2024/index.html)

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
