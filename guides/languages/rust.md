# Rust Style Guide

> [Doctrine](../../README.md) > [Languages](../README.md) > Rust

**The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document
are to be interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).**

This guide follows official Rust style conventions enforced by rustfmt[^1] and Clippy[^2].

## Quick Reference

| Task | Tool | Command |
| ---- | ---- | ------- |
| Lint | Clippy[^2] | `cargo clippy` |
| Format | rustfmt[^1] | `cargo fmt` |
| Type check | built-in | `cargo check` |
| Semantic | cargo-audit[^3] | `cargo audit` |
| Dead code | built-in | `#[warn(dead_code)]` |
| Coverage | cargo-tarpaulin[^4] | `cargo tarpaulin` |
| Complexity | - | - |
| Fuzz | cargo-fuzz[^5] | `cargo fuzz run` |
| Test perf | cargo test | `cargo test -- --test-threads=4` |

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

```toml
# Cargo.toml
[lints.clippy]
pedantic = "warn"
nursery = "warn"
unwrap_used = "deny"
expect_used = "deny"
panic = "deny"
```

Or in `clippy.toml`:

```toml
msrv = "1.88"
cognitive-complexity-threshold = 25
```

### Recommended Lint Groups

Projects **SHOULD** enable pedantic and nursery lint groups, and **MUST** deny
unwrap and expect in production code:

```rust
// In lib.rs or main.rs
#![warn(clippy::pedantic)]
#![warn(clippy::nursery)]
#![deny(clippy::unwrap_used)]
#![deny(clippy::expect_used)]
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

```toml
edition = "2021"
max_width = 100
tab_spaces = 4
use_small_heuristics = "Default"
imports_granularity = "Crate"
group_imports = "StdExternalCrate"
reorder_imports = true
```

## Common Trait Implementations

Types **MUST** eagerly implement common traits. Rust's orphan rule prevents
adding trait implementations later if you don't control both the trait and the
type.

### Why This Matters

- **Orphan rule lock-in**: Once your crate is published, users can't add
  `Debug` or `Clone` to your types
- **Ecosystem compatibility**: Types without `Debug` can't be used in `Result` error positions
- **User expectations**: Rust developers expect types to be debuggable, cloneable, and comparable

### Required Traits Checklist

All public types **MUST** implement these traits where applicable:

```rust
// MINIMUM: Every public type needs Debug
#[derive(Debug)]
pub struct Config {
    timeout: Duration,
    retries: u32,
}

// RECOMMENDED: Add Clone, PartialEq, Eq when semantically valid
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct UserId(pub u64);

// FOR HASH MAPS: Add Hash when type will be used as a key
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct CacheKey {
    namespace: String,
    id: u64,
}

// FOR VALUE OBJECTS: Add Copy when the type is small and Copy-safe
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Point {
    x: i32,
    y: i32,
}
```

### Trait Implementation Guide

| Trait | When to Implement | Notes |
| ----- | ----------------- | ----- |
| `Debug` | **Always** | Required for error messages and debugging |
| `Clone` | When duplication makes sense | Skip for types with unique ownership (file handles) |
| `PartialEq`, `Eq` | When equality is meaningful | `Eq` requires `PartialEq` |
| `Hash` | When used as HashMap/HashSet key | Requires `Eq` |
| `Default` | When there's a sensible default | Enables `..Default::default()` syntax |
| `Copy` | Small, stack-only types | Implies `Clone`, changes move semantics |
| `Send`, `Sync` | Usually automatic | Override only when unsafe is involved |

### Error Types

Error types have additional requirements:

```rust
use std::error::Error;
use std::fmt;

#[derive(Debug)]
pub struct ParseError {
    line: usize,
    message: String,
}

// Error types MUST implement Display
impl fmt::Display for ParseError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "parse error at line {}: {}", self.line, self.message)
    }
}

// Error types MUST implement std::error::Error
impl Error for ParseError {}

// Error types SHOULD be Send + Sync for use across threads
// (This is automatic if all fields are Send + Sync)
```

### Conversion Traits

Implement standard conversion traits for interoperability:

```rust
// From for infallible conversions
impl From<u16> for PortNumber {
    fn from(value: u16) -> Self {
        PortNumber(value)
    }
}

// TryFrom for fallible conversions
impl TryFrom<u32> for PortNumber {
    type Error = PortRangeError;

    fn try_from(value: u32) -> Result<Self, Self::Error> {
        if value > 65535 {
            Err(PortRangeError(value))
        } else {
            Ok(PortNumber(value as u16))
        }
    }
}

// NEVER implement Into or TryInto directly - use From/TryFrom instead
// The blanket impl provides Into automatically
```

### Serde Support

Libraries **SHOULD** provide Serde support behind a feature flag:

```toml
# Cargo.toml
[features]
default = []
serde = ["dep:serde"]

[dependencies]
serde = { version = "1.0", features = ["derive"], optional = true }
```

```rust
#[derive(Debug, Clone)]
#[cfg_attr(feature = "serde", derive(serde::Serialize, serde::Deserialize))]
pub struct Config {
    pub timeout_ms: u64,
    pub retries: u32,
}
```

## Procedural Macros

Projects **MAY** create procedural macros to reduce boilerplate. Procedural
macros **MUST** be defined in a separate crate with `proc-macro = true`.

### Why Procedural Macros

- **Code generation**: Generate boilerplate at compile time
- **Custom derives**: Implement traits automatically
- **DSLs**: Create domain-specific languages
- **Validation**: Enforce invariants at compile time

### Types of Procedural Macros

| Type | Syntax | Use Case |
| ---- | ------ | -------- |
| Derive macros | `#[derive(MyTrait)]` | Auto-implement traits |
| Attribute macros | `#[my_attr]` | Transform items |
| Function-like macros | `my_macro!(...)` | Custom syntax |

### Project Structure

```text
my_project/
├── Cargo.toml
├── src/
│   └── lib.rs
└── my_macro/           # Separate crate for proc-macro
    ├── Cargo.toml
    └── src/
        └── lib.rs
```

```toml
# my_macro/Cargo.toml
[package]
name = "my_macro"
version = "0.1.0"
edition = "2021"    # REQUIRED: an omitted edition defaults to 2015

[lib]
proc-macro = true

[dependencies]
syn = { version = "2.0", features = ["full"] }      # syn[^21]
quote = "1.0"                                        # quote[^22]
proc-macro2 = "1.0"                                  # proc-macro2[^23]
```

Every crate manifest **MUST** declare `package.edition`.

**Why**: Cargo defaults an omitted `edition` to 2015, where `use quote::quote;`
and `use syn::...;` do not resolve without an `extern crate` declaration. The
macro crate above fails to compile with "error[E0432]: unresolved import
quote" until the edition is declared.[^27]

### Derive Macro Example

```rust
// my_macro/src/lib.rs
use proc_macro::TokenStream;
use quote::quote;
use syn::{parse_macro_input, DeriveInput};

#[proc_macro_derive(Builder)]
pub fn derive_builder(input: TokenStream) -> TokenStream {
    let input = parse_macro_input!(input as DeriveInput);
    let name = &input.ident;
    let builder_name = syn::Ident::new(
        &format!("{}Builder", name),
        name.span(),
    );

    let fields = match &input.data {
        syn::Data::Struct(s) => &s.fields,
        _ => panic!("Builder only works on structs"),
    };

    let field_names: Vec<_> = fields.iter().map(|f| &f.ident).collect();
    let field_types: Vec<_> = fields.iter().map(|f| &f.ty).collect();

    let expanded = quote! {
        pub struct #builder_name {
            #(#field_names: Option<#field_types>,)*
        }

        impl #builder_name {
            pub fn new() -> Self {
                Self {
                    #(#field_names: None,)*
                }
            }

            #(
                pub fn #field_names(mut self, value: #field_types) -> Self {
                    self.#field_names = Some(value);
                    self
                }
            )*

            pub fn build(self) -> Result<#name, &'static str> {
                Ok(#name {
                    #(#field_names: self.#field_names.ok_or(
                        concat!("missing field: ", stringify!(#field_names))
                    )?,)*
                })
            }
        }

        impl #name {
            pub fn builder() -> #builder_name {
                #builder_name::new()
            }
        }
    };

    TokenStream::from(expanded)
}
```

### Using the Derive Macro

```rust
use my_macro::Builder;

#[derive(Builder, Debug)]
struct Config {
    host: String,
    port: u16,
    timeout: u64,
}

fn main() {
    let config = Config::builder()
        .host("localhost".into())
        .port(8080)
        .timeout(30)
        .build()
        .unwrap();

    println!("{:?}", config);
}
```

### Attribute Macro Example

```rust
// my_macro/src/lib.rs
#[proc_macro_attribute]
pub fn log_calls(attr: TokenStream, item: TokenStream) -> TokenStream {
    let input = parse_macro_input!(item as syn::ItemFn);
    let fn_name = &input.sig.ident;
    let fn_block = &input.block;
    let fn_sig = &input.sig;
    let fn_vis = &input.vis;

    let expanded = quote! {
        #fn_vis #fn_sig {
            println!("[ENTER] {}", stringify!(#fn_name));
            let result = (|| #fn_block)();
            println!("[EXIT] {}", stringify!(#fn_name));
            result
        }
    };

    TokenStream::from(expanded)
}
```

```rust
use my_macro::log_calls;

#[log_calls]
fn process_data(x: i32) -> i32 {
    x * 2
}
```

### Function-like Macro Example

```rust
// my_macro/src/lib.rs
#[proc_macro]
pub fn sql(input: TokenStream) -> TokenStream {
    let input_str = input.to_string();

    // Validate SQL at compile time
    if !input_str.to_uppercase().starts_with("SELECT") {
        panic!("Only SELECT queries are allowed");
    }

    let expanded = quote! {
        #input_str
    };

    TokenStream::from(expanded)
}
```

```rust
use my_macro::sql;

let query = sql!(SELECT * FROM users WHERE id = 1);
```

### Testing Procedural Macros

```rust
// tests/derive_test.rs
use my_macro::Builder;

#[derive(Builder)]
struct TestStruct {
    field_a: String,
    field_b: i32,
}

#[test]
fn test_builder_success() {
    let result = TestStruct::builder()
        .field_a("test".into())
        .field_b(42)
        .build();

    assert!(result.is_ok());
    let s = result.unwrap();
    assert_eq!(s.field_a, "test");
    assert_eq!(s.field_b, 42);
}

#[test]
fn test_builder_missing_field() {
    let result = TestStruct::builder()
        .field_a("test".into())
        .build();

    assert!(result.is_err());
}
```

### Compile-fail Tests with trybuild

```toml
[dev-dependencies]
trybuild = "1.0"  # trybuild[^24]
```

```rust
// tests/compile_fail.rs
#[test]
fn compile_fail_tests() {
    let t = trybuild::TestCases::new();
    t.compile_fail("tests/compile-fail/*.rs");
}
```

```rust
// tests/compile-fail/invalid_usage.rs
use my_macro::Builder;

#[derive(Builder)]
enum InvalidEnum {  // Should fail: Builder only works on structs
    A,
    B,
}

fn main() {}
```

### Proc Macro Best Practices

```rust
// GOOD: Provide helpful error messages
use syn::spanned::Spanned;

#[proc_macro_derive(MyDerive)]
pub fn my_derive(input: TokenStream) -> TokenStream {
    let input = parse_macro_input!(input as DeriveInput);

    match &input.data {
        syn::Data::Struct(_) => { /* ... */ }
        syn::Data::Enum(e) => {
            return syn::Error::new(
                e.enum_token.span,
                "MyDerive cannot be derived for enums"
            ).to_compile_error().into();
        }
        syn::Data::Union(u) => {
            return syn::Error::new(
                u.union_token.span,
                "MyDerive cannot be derived for unions"
            ).to_compile_error().into();
        }
    }

    // ...
}

// GOOD: Use darling for attribute parsing
// darling[^25] provides declarative attribute parsing
```

## Security Analysis: cargo-audit

Projects **MUST** run cargo-audit[^3] to check for known vulnerabilities in dependencies.

### Why cargo-audit

cargo-audit[^3] checks your dependencies against the RustSec Advisory
Database[^7], which tracks security vulnerabilities in Rust crates. It
integrates seamlessly into CI pipelines and provides actionable remediation
steps for vulnerable dependencies.

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

## Code Coverage: cargo-tarpaulin

Projects **SHOULD** measure code coverage. cargo-tarpaulin[^4] or cargo-llvm-cov[^8] **MAY** be used.

```bash
# Install
cargo install cargo-tarpaulin

# Run with coverage
cargo tarpaulin

# HTML report
cargo tarpaulin --out Html

# Fail if below threshold
cargo tarpaulin --fail-under 80
```

Alternative: cargo-llvm-cov[^8] (uses LLVM instrumentation):

```bash
cargo install cargo-llvm-cov
cargo llvm-cov --html
```

## Fuzzing: cargo-fuzz

Projects handling untrusted input **SHOULD** use fuzzing. cargo-fuzz[^5] **SHOULD** be the default choice.

cargo-fuzz[^5] uses libFuzzer[^9] for coverage-guided fuzzing. Requires nightly Rust.

```bash
# Install
cargo install cargo-fuzz

# Initialize
cargo fuzz init

# Add a fuzz target
cargo fuzz add my_target
```

```rust
// fuzz/fuzz_targets/my_target.rs
#![no_main]
use libfuzzer_sys::fuzz_target;

fuzz_target!(|data: &[u8]| {
    if let Ok(s) = std::str::from_utf8(data) {
        let _ = my_crate::parse(s);
    }
});
```

```bash
# Run fuzzer
cargo +nightly fuzz run my_target

# Run for specific time
cargo +nightly fuzz run my_target -- -max_total_time=300
```

### AFL.rs Alternative

For American Fuzzy Lop[^10]:

```bash
cargo install afl
cargo afl build
cargo afl fuzz -i in -o out target/debug/my_target
```

## Test Performance

```bash
# Parallel tests
cargo test -- --test-threads=4

# Release mode tests (faster execution)
cargo test --release

# Only run specific tests
cargo test my_test_name

# Compile tests without running
cargo test --no-run
```

### Nextest (Faster Test Runner)

```bash
cargo install cargo-nextest
cargo nextest run
```

Nextest[^11] runs tests in parallel processes, not threads, avoiding test
interference and improving speed.

## Async Runtimes

Projects **SHOULD** use tokio[^14] as the default async runtime. Projects
**MAY** use async-std[^18] for simpler use cases or when tokio's complexity is
not needed.

### Why tokio

- **Industry standard**: Most widely used async runtime with largest ecosystem
- **Feature-rich**: Built-in timers, I/O, sync primitives, and task scheduling
- **Performance**: Highly optimized work-stealing scheduler
- **Ecosystem**: Most async libraries (hyper, tonic, axum, sqlx) are built on tokio

### tokio Configuration

Feature sets **MUST** cover every tokio item the crate uses. tokio ships
almost everything behind a feature flag, and a missing flag is a compile error,
not a runtime fallback: a bare `#[tokio::main]` without `rt-multi-thread` fails
with "The default runtime flavor is `multi_thread`, but the `rt-multi-thread`
feature is disabled", `#[tokio::test(flavor = "multi_thread")]` fails with "The
runtime flavor `multi_thread` requires the `rt-multi-thread` feature", and
`Builder::new_multi_thread` fails with `error[E0599]`.[^14]

```toml
# Cargo.toml — application. `full` enables every runtime and utility feature,
# which is the right trade-off for a binary that controls its own dependency
# tree.
[dependencies]
tokio = { version = "1.53.1", features = ["full"] }
```

```toml
# Cargo.toml — library. Enable only what the library itself needs, and put
# test-only runtime features in dev-dependencies so downstream crates do not
# inherit them. Cargo unions both sets when building tests.
[dependencies]
tokio = { version = "1.53.1", default-features = false, features = [
    "rt",    # tokio::spawn, spawn_blocking, LocalSet
    "time",  # tokio::time::timeout, tokio::time::sleep
] }

[dev-dependencies]
tokio = { version = "1.53.1", features = [
    "macros",          # #[tokio::test], tokio::join!
    "rt-multi-thread", # flavor = "multi_thread", Builder::new_multi_thread
] }
```

```rust
// Application entry point. Requires the `macros` and `rt-multi-thread`
// features (both are in `full`).
#[tokio::main]
async fn main() {
    let result = fetch_data().await;
    println!("{result:?}");
}

// Configure runtime explicitly. Requires `rt-multi-thread`.
#[tokio::main(flavor = "multi_thread", worker_threads = 4)]
async fn main() {
    // Multi-threaded runtime with 4 workers
}

// Current-thread runtime for simpler apps. Requires `rt` and `macros`, but
// not `rt-multi-thread`.
#[tokio::main(flavor = "current_thread")]
async fn main() {
    // Single-threaded runtime
}
```

### async-std Alternative

```toml
[dependencies]
async-std = { version = "1.13", features = ["attributes"] }
```

```rust
#[async_std::main]
async fn main() {
    let result = fetch_data().await;
    println!("{:?}", result);
}
```

### Runtime-Agnostic Code

Libraries **SHOULD** be runtime-agnostic when possible:

```rust
// GOOD: Use async traits without runtime coupling
use std::future::Future;
use std::time::Duration;

pub trait DataSource {
    fn fetch(&self, id: u64) -> impl Future<Output = Result<Data, Error>> + Send;
}

// Every cfg configuration MUST produce a return path. Guard the item on the
// set of backends and fail explicitly when none is selected.
#[cfg(not(any(feature = "tokio", feature = "async-std")))]
compile_error!("enable the `tokio` or `async-std` feature to pick a backend");

// GOOD: Accept executor as parameter
#[cfg(any(feature = "tokio", feature = "async-std"))]
pub async fn process_with_timeout<F, T>(
    future: F,
    timeout: Duration,
) -> Result<T, TimeoutError>
where
    F: Future<Output = T>,
{
    // Cargo features are additive, so both backends can be enabled at once.
    // tokio takes precedence; the async-std arm is then compiled out.
    #[cfg(feature = "tokio")]
    return tokio::time::timeout(timeout, future)
        .await
        .map_err(|_| TimeoutError);

    #[cfg(all(feature = "async-std", not(feature = "tokio")))]
    return async_std::future::timeout(timeout, future)
        .await
        .map_err(|_| TimeoutError);
}
```

```rust
// BAD: no arm matches when neither feature is enabled, so the body evaluates
// to `()`:
//   error[E0308]: mismatched types
//   expected `Result<T, TimeoutError>`, found `()`
// The two arms are also not mutually exclusive: with both features enabled
// the first `return` wins silently.
pub async fn process_with_timeout<F, T>(future: F, timeout: Duration)
    -> Result<T, TimeoutError>
where
    F: Future<Output = T>,
{
    #[cfg(feature = "tokio")]
    return tokio::time::timeout(timeout, future).await.map_err(|_| TimeoutError);

    #[cfg(feature = "async-std")]
    return async_std::future::timeout(timeout, future).await.map_err(|_| TimeoutError);
}
```

### Spawning Tasks

```rust
// `tokio::spawn`, `spawn_blocking` and `LocalSet` require the `rt` feature.
use tokio::task;

// Spawn async task on runtime
let handle = tokio::spawn(async {
    expensive_async_operation().await
});

// Wait for result
let result = handle.await.unwrap();

// Spawn blocking task (for CPU-intensive or synchronous code)
let result = task::spawn_blocking(|| {
    expensive_sync_operation()
}).await.unwrap();

// Local tasks (for !Send futures)
let local = task::LocalSet::new();
local.run_until(async {
    task::spawn_local(async {
        // Can use !Send types here
    }).await.unwrap();
}).await;
```

### Async Testing

```rust
// Requires the `macros` and `rt` features.
#[tokio::test]
async fn test_async_operation() {
    let result = fetch_data().await;
    assert!(result.is_ok());
}

// Multi-threaded test. Requires `rt-multi-thread` in addition to `macros`;
// without it the attribute fails with "The runtime flavor `multi_thread`
// requires the `rt-multi-thread` feature".
#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn test_concurrent_operations() {
    let (a, b) = tokio::join!(
        operation_a(),
        operation_b()
    );
    assert!(a.is_ok());
    assert!(b.is_ok());
}

// Test with custom runtime. `Builder::new_multi_thread` requires
// `rt-multi-thread`.
#[test]
fn test_with_custom_runtime() {
    let rt = tokio::runtime::Builder::new_multi_thread()
        .worker_threads(2)
        .enable_all()
        .build()
        .unwrap();

    rt.block_on(async {
        // Test async code
    });
}
```

## Pre-commit Configuration

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

```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
        with:
          components: rustfmt, clippy
      - run: cargo fmt -- --check
      - run: cargo clippy --all-targets --all-features -- -D warnings

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      - run: cargo test --all-features
      - run: cargo install cargo-tarpaulin
      - run: cargo tarpaulin --fail-under 80

  audit:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      checks: write   # the Action reports findings as a check run
      issues: write   # ...and as an issue on `schedule` events
    steps:
      - uses: actions/checkout@v4
      - uses: rustsec/audit-check@v2.0.0
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
```

`rustsec/audit-check` declares `token` as a required input with no default, so
the step **MUST** pass `${{ secrets.GITHUB_TOKEN }}` explicitly. The Action
parses its inputs before running the audit, so omitting the token fails the job
outright. It reports via the Checks API for most events and via the Issues API
for `schedule` events, which is why both write permissions are granted.[^28]

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

- **Binaries/applications**: **MUST** commit `Cargo.lock` for reproducible builds
- **Libraries**: **SHOULD NOT** commit `Cargo.lock` (consumers use their own lock)

### Version Constraints

```toml
[dependencies]
# Caret (default): ^1.2.3 -> >=1.2.3 <2.0.0
serde = "1.0"

# Tilde: ~1.2.3 -> >=1.2.3 <1.3.0
tokio = "~1.35"

# Exact: =1.2.3 -> only 1.2.3
critical-lib = "=1.2.3"

# Wildcard: 1.* -> >=1.0.0 <2.0.0
utils = "1.*"
```

### Vulnerability Scanning

```bash
# Install cargo-audit with the optional `fix` feature
cargo install cargo-audit --version 0.22.2 --locked --features=fix

# Run security audit
cargo audit

# Fix vulnerabilities automatically (experimental; requires --features=fix)
cargo audit fix

# Preview the changes without writing Cargo.toml
cargo audit fix --dry-run
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

## E2E & Acceptance Testing

### Integration Tests

```rust
// tests/integration_test.rs
use my_crate::App;

#[test]
fn test_end_to_end_flow() {
    let app = App::new();
    let result = app.process_request("input");
    assert_eq!(result, "expected_output");
}
```

### BDD with cucumber-rs

```toml
[dev-dependencies]
cucumber = "0.23.0"  # cucumber-rs[^12]
tokio = { version = "1.53.1", features = ["macros", "rt-multi-thread"] }

# REQUIRED: a named test target with the libtest harness disabled, so that
# the `main` in tests/cucumber.rs is the entry point.
[[test]]
name = "cucumber"
harness = false
```

A Cucumber test target **MUST** set `harness = false`.

**Why**: with the default libtest harness, Cargo generates its own `main` and
the `#[tokio::main] async fn main` below is never called. `cargo test --test
cucumber` then reports "running 0 tests ... test result: ok" and the build goes
green having executed no scenarios at all.[^12]

```rust
// tests/cucumber.rs
use cucumber::{World as _, given, then, when};

#[derive(Debug, Default, cucumber::World)]
struct MyWorld {
    result: Option<String>,
}

#[given("a user is logged in")]
async fn given_logged_in(_world: &mut MyWorld) {
    // Setup
}

#[when(regex = r"^they request (.*)$")]
async fn when_request(world: &mut MyWorld, resource: String) {
    world.result = Some(fetch(&resource).await);
}

#[then(regex = r"^they receive (.*)$")]
async fn then_receive(world: &mut MyWorld, expected: String) {
    assert_eq!(world.result.as_deref(), Some(expected.as_str()));
}

#[tokio::main]
async fn main() {
    MyWorld::run("tests/features").await;
}
```

cucumber 0.23.0 requires Rust 1.88 or later, which sets the floor for the
`msrv` and `rust-toolchain.toml` values used elsewhere in this guide.[^12]

### API Testing Patterns

```rust
use reqwest::Client;  // reqwest[^13]

#[tokio::test]
async fn test_api_endpoint() {
    let client = Client::new();
    let response = client
        .get("http://localhost:8080/api/users")
        .send()
        .await
        .unwrap();

    assert_eq!(response.status(), 200);
    let users: Vec<User> = response.json().await.unwrap();
    assert!(!users.is_empty());
}
```

## Thread Safety Testing

Rust's ownership system prevents data races at compile time. Most thread safety is proven through types.

### Testing Send + Sync Bounds

```rust
#[test]
fn test_send_sync() {
    fn is_send<T: Send>() {}
    fn is_sync<T: Sync>() {}

    is_send::<MyType>();
    is_sync::<MyType>();
}
```

### Async Testing with tokio::test

```rust
#[tokio::test]  // tokio[^14]
async fn test_concurrent_access() {
    let counter = Arc::new(Mutex::new(0));
    let mut handles = vec![];

    for _ in 0..10 {
        let counter = Arc::clone(&counter);
        handles.push(tokio::spawn(async move {
            *counter.lock().await += 1;
        }));
    }

    for handle in handles {
        handle.await.unwrap();
    }

    assert_eq!(*counter.lock().await, 10);
}
```

### Concurrency Testing with loom

```toml
[dev-dependencies]
loom = "0.7"  # loom[^15]
```

```rust
#[cfg(loom)]
#[test]
fn test_concurrent_safety() {
    loom::model(|| {
        let v1 = Arc::new(AtomicUsize::new(0));
        let v2 = v1.clone();

        loom::thread::spawn(move || {
            v1.fetch_add(1, Ordering::SeqCst);
        });

        v2.fetch_add(1, Ordering::SeqCst);
    });
}
```

## Idempotence Testing

### Testing Retry-Safe Operations

```rust
#[test]
fn test_idempotent_create() {
    let db = setup_test_db();
    let id = uuid::Uuid::new_v4();

    // First call creates
    let result1 = db.create_user(id, "alice");
    assert!(result1.is_ok());

    // Second call with same ID is safe
    let result2 = db.create_user(id, "alice");
    assert!(result2.is_ok());

    // Only one user exists
    assert_eq!(db.count_users(), 1);
}
```

### Transaction Idempotence Patterns

```rust
#[tokio::test]
async fn test_transaction_idempotency() {
    let mut tx = db.begin().await.unwrap();

    // Use idempotency key
    let key = "txn_123";
    if !already_processed(&mut tx, key).await {
        process_payment(&mut tx, key, amount).await.unwrap();
        mark_processed(&mut tx, key).await.unwrap();
    }

    tx.commit().await.unwrap();

    // Retry is safe
    let mut tx2 = db.begin().await.unwrap();
    assert!(already_processed(&mut tx2, key).await);
}
```

## Reliability & Resilience Testing

### Testing with tokio Timeouts

```rust
use tokio::time::{timeout, Duration};

#[tokio::test]
async fn test_timeout_handling() {
    let result = timeout(
        Duration::from_millis(100),
        slow_operation()
    ).await;

    assert!(result.is_err(), "Should timeout");
}
```

### Fault Injection Patterns

```rust
#[cfg(test)]
mod tests {
    use std::sync::atomic::{AtomicU32, Ordering};

    static FAIL_COUNTER: AtomicU32 = AtomicU32::new(0);

    fn flaky_network_call() -> Result<String, Error> {
        if FAIL_COUNTER.fetch_add(1, Ordering::SeqCst) < 2 {
            Err(Error::NetworkError)
        } else {
            Ok("success".into())
        }
    }

    #[test]
    fn test_retry_logic() {
        let result = retry_with_backoff(|| flaky_network_call(), 3);
        assert!(result.is_ok());
    }
}
```

### Testing Error Recovery

```rust
#[tokio::test]
async fn test_circuit_breaker() {
    let breaker = CircuitBreaker::new(3, Duration::from_secs(60));

    // Cause failures to open circuit
    for _ in 0..3 {
        let _ = breaker.call(|| Err::<(), _>("fail")).await;
    }

    assert!(breaker.is_open());

    // Circuit should reject fast
    let start = Instant::now();
    let result = breaker.call(|| Ok(())).await;
    assert!(result.is_err());
    assert!(start.elapsed() < Duration::from_millis(10));
}
```

## Compatibility Testing

### Version Pinning with rust-toolchain.toml

```toml
# rust-toolchain.toml
[toolchain]
channel = "1.98.1"
components = ["rustfmt", "clippy"]
targets = ["x86_64-unknown-linux-gnu", "wasm32-unknown-unknown"]
```

The pinned channel **MUST** be at least the highest MSRV of any dependency.
cucumber 0.23.0 requires Rust 1.88, so a 1.75 pin cannot build this guide's
own BDD example.[^12]

### Cross-Compilation Testing

```bash
# Add targets
rustup target add x86_64-pc-windows-gnu
rustup target add aarch64-apple-darwin

# Test compilation
cargo check --target x86_64-pc-windows-gnu
cargo check --target aarch64-apple-darwin
```

### CI Matrix for Multiple Targets

Matrices **MUST** pair each target with a host that can build and run it. A
Cartesian product of `os` and `target` produces combinations such as
`windows-latest` building `x86_64-unknown-linux-gnu`, for which no linker or
runner is installed. Native test runs **MUST** be expressed as explicit
`include` tuples; cross-compilation **MUST** use `cargo check`, which does not
link or execute.[^29]

```yaml
jobs:
  # Native: host and target agree, so binaries link and run.
  test:
    name: test (${{ matrix.rust }}, ${{ matrix.target }})
    strategy:
      fail-fast: false
      matrix:
        include:
          - os: ubuntu-latest      # x64 Linux
            target: x86_64-unknown-linux-gnu
            rust: stable
          - os: windows-latest     # x64 Windows
            target: x86_64-pc-windows-msvc
            rust: stable
          - os: macos-latest       # arm64 macOS
            target: aarch64-apple-darwin
            rust: stable
          - os: ubuntu-latest
            target: x86_64-unknown-linux-gnu
            rust: beta
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@master
        with:
          toolchain: ${{ matrix.rust }}
          targets: ${{ matrix.target }}
      - run: cargo test --target ${{ matrix.target }}

  # Cross: compile only. `cargo check` never links, so no cross linker or
  # emulator is required.
  cross-check:
    name: cross-check (${{ matrix.target }})
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        target:
          - aarch64-unknown-linux-gnu
          - x86_64-pc-windows-gnu
          - wasm32-unknown-unknown
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
        with:
          targets: ${{ matrix.target }}
      - run: cargo check --target ${{ matrix.target }}
```

`macos-latest` is an arm64 image, so `aarch64-apple-darwin` is its native
target; `x86_64-apple-darwin` would need Rosetta to run the resulting test
binary.[^29]

## WebAssembly (WASM)

Projects **MAY** compile Rust to WebAssembly for browser or edge runtime
deployment. wasm-pack[^19] **SHOULD** be used for building WASM packages.

### Why Rust for WASM

- **Performance**: Near-native speed in the browser
- **Safety**: Memory-safe without garbage collection
- **Size**: Small binary sizes with aggressive optimization
- **Interop**: Excellent JavaScript interoperability via wasm-bindgen

### Setup

```bash
# Install wasm target
rustup target add wasm32-unknown-unknown

# Install wasm-pack
cargo install wasm-pack

# Install wasm-opt (optional, for size optimization)
cargo install wasm-opt
```

### Project Structure

```toml
# Cargo.toml
[lib]
crate-type = ["cdylib", "rlib"]

[dependencies]
wasm-bindgen = "0.2"  # wasm-bindgen[^20]

[dev-dependencies]
wasm-bindgen-test = "0.3"

[profile.release]
opt-level = "s"      # Optimize for size
lto = true           # Link-time optimization
```

### Basic WASM Module

```rust
use wasm_bindgen::prelude::*;

// Export function to JavaScript
#[wasm_bindgen]
pub fn greet(name: &str) -> String {
    format!("Hello, {}!", name)
}

// Export struct to JavaScript
#[wasm_bindgen]
pub struct Counter {
    value: i32,
}

#[wasm_bindgen]
impl Counter {
    #[wasm_bindgen(constructor)]
    pub fn new() -> Counter {
        Counter { value: 0 }
    }

    pub fn increment(&mut self) {
        self.value += 1;
    }

    pub fn value(&self) -> i32 {
        self.value
    }
}

// Import JavaScript function
#[wasm_bindgen]
extern "C" {
    fn alert(s: &str);

    #[wasm_bindgen(js_namespace = console)]
    fn log(s: &str);
}

#[wasm_bindgen]
pub fn show_alert(message: &str) {
    alert(message);
}
```

### Building WASM

```bash
# Build for bundlers (webpack, vite)
wasm-pack build --target bundler

# Build for Node.js
wasm-pack build --target nodejs

# Build for web (no bundler)
wasm-pack build --target web

# Build with optimizations
wasm-pack build --release --target web

# Further optimize with wasm-opt
wasm-opt -Os -o pkg/optimized.wasm pkg/app_bg.wasm
```

### Using in JavaScript

The import shape **MUST** match the `--target` the package was built with.
`--target bundler` output re-exports named bindings only and starts the module
itself; it has no default export, so `import init from './pkg/my_crate.js'`
fails to link with "SyntaxError: The requested module does not provide an
export named 'default'". Only `--target web` exports the asynchronous
initialiser as the default.[^20]

```javascript
// GOOD: `wasm-pack build --target bundler` — named exports, no init call.
// The bundler resolves and instantiates the .wasm import for you.
import { greet, Counter } from './pkg/my_crate.js';

console.log(greet('World'));

const counter = new Counter();
counter.increment();
console.log(counter.value()); // 1
```

```javascript
// GOOD: `wasm-pack build --target web` — default export is the initialiser
// and MUST be awaited before any other export is called.
import init, { greet, Counter } from './pkg/my_crate.js';

async function run() {
  await init();
  console.log(greet('World'));

  const counter = new Counter();
  counter.increment();
  console.log(counter.value()); // 1
}

run();
```

```javascript
// BAD: bundler output has no default export; this is a link-time SyntaxError.
import init, { greet } from './pkg/my_crate.js';  // built with --target bundler
```

```html
<!-- Without bundler: built with `wasm-pack build --target web` -->
<script type="module">
  import init, { greet } from './pkg/my_crate.js';

  async function run() {
    await init();
    document.body.textContent = greet('WASM');
  }

  run();
</script>
```

### WASM Testing

```rust
use wasm_bindgen_test::*;

wasm_bindgen_test_configure!(run_in_browser);

#[wasm_bindgen_test]
fn test_greet() {
    assert_eq!(greet("Test"), "Hello, Test!");
}

#[wasm_bindgen_test]
fn test_counter() {
    let mut counter = Counter::new();
    assert_eq!(counter.value(), 0);
    counter.increment();
    assert_eq!(counter.value(), 1);
}
```

```bash
# Run WASM tests in headless browser
wasm-pack test --headless --firefox
wasm-pack test --headless --chrome

# Run in Node.js
wasm-pack test --node
```

### WASM Best Practices

```rust
// GOOD: Use web-sys for DOM access
use web_sys::{Document, Element, Window};

#[wasm_bindgen]
pub fn create_element(tag: &str) -> Result<Element, JsValue> {
    let window = web_sys::window().unwrap();
    let document = window.document().unwrap();
    document.create_element(tag)
}

// GOOD: Handle panics gracefully
use console_error_panic_hook;

#[wasm_bindgen(start)]
pub fn init() {
    console_error_panic_hook::set_once();
}

// GOOD: Use serde for complex data
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize)]
pub struct Config {
    pub name: String,
    pub value: i32,
}

#[wasm_bindgen]
pub fn process_config(config: JsValue) -> Result<JsValue, JsValue> {
    let config: Config = serde_wasm_bindgen::from_value(config)?;
    let result = process(config);
    Ok(serde_wasm_bindgen::to_value(&result)?)
}
```

### WASM Size Optimization

```toml
# Cargo.toml
[profile.release]
opt-level = "z"          # Optimize for size (aggressive)
lto = true               # Enable LTO
codegen-units = 1        # Single codegen unit
panic = "abort"          # No unwinding
strip = true             # Strip symbols
```

```bash
# Check WASM size
ls -lh pkg/*.wasm

# Analyze with twiggy
cargo install twiggy
twiggy top pkg/app_bg.wasm
twiggy paths pkg/app_bg.wasm
```

## Internationalization Testing

Rust's `String` type is UTF-8 by default, providing native Unicode support.

```rust
#[test]
fn test_unicode_handling() {
    let text = "Hello, 世界! 🦀";
    assert_eq!(text.chars().count(), 12);
    assert!(text.contains("世界"));
}
```

### Unicode Normalization with unic

```toml
[dependencies]
unic = "0.9"  # unic[^16]
```

Normalisation fixtures **MUST** be written with explicit Unicode escapes.
Editors and clipboards silently normalise pasted text, so two literals that
look different on screen can hold identical code points, which turns the
assertion into a no-op or an outright failure.

```rust
use unic::normal::StrNormalForm;

#[test]
fn test_unicode_normalization() {
    // "café" with a precomposed U+00E9, versus "e" + U+0301 combining acute.
    let precomposed = "caf\u{e9}";  // NFC
    let decomposed = "cafe\u{301}"; // NFD

    // Different code points before normalisation.
    assert_ne!(precomposed, decomposed);
    assert_eq!(precomposed.chars().count(), 4);
    assert_eq!(decomposed.chars().count(), 5);

    // Equal after normalisation.
    let normalised_precomposed: String = precomposed.nfc().collect();
    let normalised_decomposed: String = decomposed.nfc().collect();
    assert_eq!(normalised_precomposed, normalised_decomposed);
}
```

```rust
// BAD: both literals are precomposed, so `assert_ne!` fails immediately.
let s1 = "café";  // claims NFC
let s2 = "café";  // claims NFD, but holds the same U+00E9
```

### Testing with Non-ASCII Fixtures

```rust
#[test]
fn test_multilingual_input() {
    let fixtures = [
        ("English", "Hello"),
        ("日本語", "こんにちは"),
        ("한국어", "안녕하세요"),
        ("العربية", "مرحبا"),
        ("Emoji", "👋🌍"),
    ];

    for (lang, greeting) in fixtures {
        let result = process_text(greeting);
        assert!(result.is_ok(), "Failed for {}", lang);
    }
}
```

## Data Integrity Testing

### sqlx Compile-Time Checked Queries

```toml
[dependencies]
sqlx = { version = "0.7", features = ["runtime-tokio", "postgres", "macros"] }  # sqlx[^17]
```

```rust
use sqlx::PgPool;

#[sqlx::test]
async fn test_query_correctness(pool: PgPool) -> sqlx::Result<()> {
    // Compile-time verified query
    let user = sqlx::query_as!(
        User,
        "SELECT id, name, email FROM users WHERE id = $1",
        1
    )
    .fetch_one(&pool)
    .await?;

    assert_eq!(user.id, 1);
    Ok(())
}
```

### Migration Testing

```rust
#[sqlx::test]
async fn test_migrations(pool: PgPool) -> sqlx::Result<()> {
    // Migrations run automatically with sqlx::test

    let count: i64 = sqlx::query_scalar("SELECT COUNT(*) FROM users")
        .fetch_one(&pool)
        .await?;

    assert_eq!(count, 0);
    Ok(())
}

#[sqlx::test(migrations = false)]
async fn test_without_migrations(pool: PgPool) -> sqlx::Result<()> {
    // Test with clean database
    Ok(())
}
```

## A/B Testing & Feature Flags

### Feature Flags via Cargo Features

```toml
# Cargo.toml
[features]
default = ["feature-a"]
feature-a = []
feature-b = []
experimental = ["feature-b"]
```

Overlapping features **MUST** have an explicit, documented precedence, and
every `cfg` arm **MUST** be reachable in exactly one configuration.

**Why**: Cargo features are additive. A dependency, `--all-features`, or
feature unification across a workspace can enable `feature-a` and `feature-b`
together. Writing `#[cfg(feature = "feature-a")]` against
`#[cfg(not(feature = "feature-a"))]` in the implementation while the test
asserts on `feature-a` and `feature-b` independently makes both assertions
compile at once, and `cargo test --all-features` fails with
`left: "Algorithm A", right: "Algorithm B"`.

```rust
// GOOD: feature-a takes precedence over feature-b; neither means baseline.
#[cfg(feature = "feature-a")]
pub fn new_algorithm() -> String {
    "Algorithm A".into()
}

#[cfg(all(feature = "feature-b", not(feature = "feature-a")))]
pub fn new_algorithm() -> String {
    "Algorithm B".into()
}

#[cfg(not(any(feature = "feature-a", feature = "feature-b")))]
pub fn new_algorithm() -> String {
    "Baseline".into()
}

#[test]
fn test_feature_behavior() {
    let result = new_algorithm();

    // Exactly one of these assertions is compiled in, mirroring the
    // precedence above.
    #[cfg(feature = "feature-a")]
    assert_eq!(result, "Algorithm A");

    #[cfg(all(feature = "feature-b", not(feature = "feature-a")))]
    assert_eq!(result, "Algorithm B");

    #[cfg(not(any(feature = "feature-a", feature = "feature-b")))]
    assert_eq!(result, "Baseline");
}
```

```rust
// BAD: with both features enabled, both assertions compile and contradict.
#[test]
fn test_feature_behavior() {
    let result = new_algorithm();  // "Algorithm A"

    #[cfg(feature = "feature-a")]
    assert_eq!(result, "Algorithm A");

    #[cfg(feature = "feature-b")]
    assert_eq!(result, "Algorithm B");  // fails under --all-features
}
```

### Feature Matrix in CI

Projects with optional features **MUST** test the combinations they support,
not only the default set:

```yaml
jobs:
  features:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        features:
          - "--no-default-features"
          - ""
          - "--no-default-features --features feature-b"
          - "--all-features"
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      - run: cargo test ${{ matrix.features }}
```

### Conditional Compilation with cfg Attributes

Every `cfg`-gated item that unconditional code calls **MUST** be defined for
every target the CI matrix builds, or the build **MUST** fail with an explicit
message.

**Why**: `target_os` arms for Linux and Windows alone leave the item undefined
on the `macos-latest` runner, and the unconditional test call fails with
`error[E0425]: cannot find function 'platform_specific' in this scope`. A
`compile_error!` in the fallback arm turns a confusing name-resolution error
into a statement of what is missing.

```rust
#[cfg(target_os = "linux")]
fn platform_specific() -> &'static str {
    "Linux"
}

#[cfg(target_os = "macos")]
fn platform_specific() -> &'static str {
    "macOS"
}

#[cfg(target_os = "windows")]
fn platform_specific() -> &'static str {
    "Windows"
}

#[cfg(not(any(
    target_os = "linux",
    target_os = "macos",
    target_os = "windows"
)))]
compile_error!("platform_specific() has no implementation for this target_os");

#[test]
fn test_platform_behavior() {
    let result = platform_specific();
    assert!(!result.is_empty());
}

// Testing multiple feature combinations
#[test]
#[cfg(all(feature = "feature-a", not(feature = "feature-b")))]
fn test_feature_combination_a_only() {
    // Only runs when feature-a is enabled but feature-b is not
    assert_eq!(new_algorithm(), "Algorithm A");
}
```

## Unsafe Rust

Projects **SHOULD** minimize usage of `unsafe`. When `unsafe` is required, it
**MUST** be carefully documented and isolated.

### Why Minimize Unsafe

- **Compiler guarantees**: Safe Rust provides memory safety guarantees that `unsafe` bypasses
- **Bug surface**: Unsafe code is where memory bugs hide
- **Review burden**: Unsafe code requires more careful review
- **Soundness**: Incorrect unsafe code can cause undefined behavior

### When Unsafe is Necessary

| Use Case | Example |
| -------- | ------- |
| FFI (Foreign Function Interface) | Calling C libraries |
| Raw pointer manipulation | Custom data structures |
| Performance-critical code | SIMD, avoiding bounds checks |
| Hardware access | Memory-mapped I/O |
| Implementing low-level abstractions | `Arc`, `Mutex` internals |

### Unsafe Best Practices

A function that cannot uphold an unsafe operation's preconditions itself
**MUST** be declared `unsafe fn` with a `# Safety` section. A `// SAFETY:`
comment **MUST NOT** be used to push an obligation onto callers of a safe
function.

**Why**: safety is part of the signature, not of a comment. A safe
`get_unchecked` can be called from entirely safe code with any index; under
Miri, `get_unchecked(&[], 0)` aborts with "unsafe precondition(s) violated:
slice::get_unchecked requires that the index is within the slice".[^26]

```rust
// GOOD: bounds-checked, safe to call with any index
pub fn get(slice: &[u8], index: usize) -> Option<u8> {
    slice.get(index).copied()
}

// GOOD: the obligation is in the signature and documented
/// Reads `slice[index]` without a bounds check.
///
/// # Safety
///
/// `index` must be strictly less than `slice.len()`. Violating this reads
/// out of bounds, which is undefined behaviour.
pub unsafe fn get_unchecked(slice: &[u8], index: usize) -> u8 {
    debug_assert!(index < slice.len());
    // SAFETY: the caller guarantees `index < slice.len()`.
    unsafe { *slice.get_unchecked(index) }
}
```

```rust
// BAD: safe fn, unchecked index. The comment transfers nothing; safe callers
// can pass any index and cause undefined behaviour.
pub fn get_unchecked(slice: &[u8], index: usize) -> u8 {
    // SAFETY: Caller must ensure index < slice.len()
    unsafe { *slice.get_unchecked(index) }
}
```

An abstraction over a raw allocation **MUST** handle allocation failure,
initialise memory before it is read, and free the allocation in `Drop`.

**Why**: `std::alloc::alloc` returns uninitialised memory and a null pointer on
failure, and it never frees anything. Reading such a byte through a safe method
is undefined behaviour even when the allocation succeeds: on the `SafeBuffer`
shown below, Miri reports "Undefined Behavior: reading memory ..., but memory is
uninitialized ..., and this operation requires initialized memory" for
`SafeBuffer::new(1).get(0)`.[^26]
`alloc_zeroed` initialises the whole block, `handle_alloc_error` reports failure
without producing a dangling `NonNull`, and `Drop` returns the memory.

```rust
// GOOD: Encapsulate unsafe in a safe API with a complete set of invariants
use std::alloc::{alloc_zeroed, dealloc, handle_alloc_error, Layout};
use std::ptr::NonNull;

pub struct ZeroedBuffer {
    ptr: NonNull<u8>,
    layout: Layout,
}

impl ZeroedBuffer {
    /// Allocates `len` zeroed bytes. Returns `None` for `len == 0`, which is
    /// not a valid allocation size.
    pub fn new(len: usize) -> Option<Self> {
        if len == 0 {
            return None;
        }
        let layout = Layout::array::<u8>(len).ok()?;

        // SAFETY: `layout` has non-zero size because `len > 0`.
        let ptr = unsafe { alloc_zeroed(layout) };

        // The allocator returns null on failure; it must never be
        // dereferenced or wrapped in `NonNull`.
        let Some(ptr) = NonNull::new(ptr) else {
            handle_alloc_error(layout)
        };
        Some(Self { ptr, layout })
    }

    pub fn len(&self) -> usize {
        self.layout.size()
    }

    pub fn is_empty(&self) -> bool {
        false
    }

    pub fn get(&self, index: usize) -> Option<u8> {
        if index >= self.len() {
            return None;
        }
        // SAFETY: `index < self.len()`, so the offset stays inside the
        // allocation, and `alloc_zeroed` initialised every byte of it.
        Some(unsafe { self.ptr.as_ptr().add(index).read() })
    }

    pub fn set(&mut self, index: usize, value: u8) -> bool {
        if index >= self.len() {
            return false;
        }
        // SAFETY: `index < self.len()` and `&mut self` rules out aliasing.
        unsafe { self.ptr.as_ptr().add(index).write(value) };
        true
    }
}

impl Drop for ZeroedBuffer {
    fn drop(&mut self) {
        // SAFETY: `ptr` came from `alloc_zeroed` with exactly `self.layout`
        // and has not been freed; `Drop` runs at most once.
        unsafe { dealloc(self.ptr.as_ptr(), self.layout) };
    }
}
```

```rust
// BAD: unwraps the layout, ignores allocation failure, reads uninitialised
// bytes through a safe method, and leaks the allocation.
pub struct SafeBuffer {
    ptr: *mut u8,
    len: usize,
}

impl SafeBuffer {
    pub fn new(size: usize) -> Self {
        let ptr = unsafe {
            // SAFETY: size is non-zero, layout is valid   <- neither is checked
            std::alloc::alloc(std::alloc::Layout::array::<u8>(size).unwrap())
        };
        Self { ptr, len: size }
    }

    pub fn get(&self, index: usize) -> Option<u8> {
        if index < self.len {
            // SAFETY: index is bounds-checked   <- but the byte is uninitialised
            Some(unsafe { *self.ptr.add(index) })
        } else {
            None
        }
    }
}
// No `Drop`: every SafeBuffer leaks its allocation.
```

Prefer a safe owner where one exists. `vec![0u8; len]` gives the same
guarantees with no `unsafe` at all; reach for raw allocation only when the
layout or ownership cannot be expressed with `Vec` or `Box`.

```rust
// GOOD: no unsafe needed for a zeroed byte buffer
let buffer = vec![0u8; 100];
assert_eq!(buffer.get(100), None);
```

```rust
// GOOD: Document invariants
/// A non-null pointer to a valid T.
///
/// # Safety
///
/// The pointer must:
/// - Be properly aligned for T
/// - Point to a valid, initialized T
/// - Not be aliased by any mutable reference
pub struct NonNullPtr<T> {
    ptr: *const T,
}
```

### SAFETY Comments

All `unsafe` blocks **MUST** include a `// SAFETY:` comment explaining why the code is sound:

```rust
// GOOD: Explains why this is safe
let value = unsafe {
    // SAFETY: We verified ptr is non-null and properly aligned above.
    // The lifetime is tied to 'a, ensuring the reference remains valid.
    &*ptr
};

// BAD: No safety justification
let value = unsafe { &*ptr };

// BAD: Insufficient explanation
let value = unsafe {
    // SAFETY: It's fine
    &*ptr
};
```

### FFI Guidelines

```rust
use std::ffi::{CStr, CString};
use std::os::raw::c_char;

// Declare external C functions
extern "C" {
    fn strlen(s: *const c_char) -> usize;
    fn malloc(size: usize) -> *mut u8;
    fn free(ptr: *mut u8);
}

// GOOD: Safe wrapper around unsafe FFI
pub fn safe_strlen(s: &str) -> usize {
    let c_string = CString::new(s).expect("string contains null byte");
    // SAFETY: c_string is a valid null-terminated string
    unsafe { strlen(c_string.as_ptr()) }
}

// GOOD: RAII wrapper for C resources
pub struct CBuffer {
    ptr: *mut u8,
    len: usize,
}

impl CBuffer {
    pub fn new(size: usize) -> Option<Self> {
        // SAFETY: malloc returns null on failure, checked below
        let ptr = unsafe { malloc(size) };
        if ptr.is_null() {
            None
        } else {
            Some(Self { ptr, len: size })
        }
    }
}

impl Drop for CBuffer {
    fn drop(&mut self) {
        // SAFETY: ptr was allocated by malloc and has not been freed
        unsafe { free(self.ptr) };
    }
}
```

### Testing Unsafe Code

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_checked_access() {
        let data = [1u8, 2, 3];
        assert_eq!(get(&data, 0), Some(1));
        assert_eq!(get(&data, 3), None);

        // SAFETY: 2 < data.len().
        assert_eq!(unsafe { get_unchecked(&data, 2) }, 3);
    }

    #[test]
    fn test_safe_wrapper() {
        let buffer = ZeroedBuffer::new(100).expect("100 > 0");
        assert_eq!(buffer.get(0), Some(0));
        assert_eq!(buffer.get(99), Some(0));
        assert_eq!(buffer.get(100), None);
    }

    #[test]
    fn test_edge_cases() {
        // Zero-sized allocations are rejected, not silently allowed.
        assert!(ZeroedBuffer::new(0).is_none());

        let mut buffer = ZeroedBuffer::new(1).expect("1 > 0");
        assert_eq!(buffer.get(0), Some(0));
        assert!(buffer.set(0, 42));
        assert_eq!(buffer.get(0), Some(42));
        assert_eq!(buffer.get(1), None);
        assert!(!buffer.set(1, 42));
    }
}

// Use Miri for detecting undefined behaviour
// cargo +nightly miri test
```

Tests over `unsafe` code **MUST** assert on values, not merely on
`is_some()`. `assert!(buffer.get(0).is_some())` passes just as happily when the
byte behind it is uninitialised, so it cannot distinguish a sound
implementation from an unsound one; only Miri or a value assertion can.

### Miri for Undefined Behavior Detection

Projects with `unsafe` code **SHOULD** run Miri[^26] to detect undefined behavior:

```bash
# Install Miri
rustup +nightly component add miri

# Run tests under Miri
cargo +nightly miri test

# Run specific test
cargo +nightly miri test test_safe_wrapper
```

### Unsafe Antipatterns

```rust
// BAD: Unnecessary unsafe
let x: i32 = unsafe { 5 };  // Nothing unsafe here!

// BAD: Unsafe impl without necessity
unsafe impl Send for MyType {}  // Only if truly needed

// BAD: Transmute for type conversion
let x: u32 = unsafe { std::mem::transmute(1.0f32) };
// GOOD: Use to_bits() instead
let x: u32 = 1.0f32.to_bits();

// BAD: Unchecked indexing without bounds verification
let value = unsafe { *slice.get_unchecked(user_input) };
// GOOD: Bounds check first
if user_input < slice.len() {
    let value = unsafe { *slice.get_unchecked(user_input) };
}
```

### Unsafe Trait Implementations

```rust
// Manually implementing Send/Sync requires careful thought
struct MyWrapper<T> {
    data: *mut T,
}

// SAFETY: MyWrapper can be sent across threads because:
// 1. The pointer is not shared (unique ownership)
// 2. T itself is Send
unsafe impl<T: Send> Send for MyWrapper<T> {}

// SAFETY: MyWrapper can be shared across threads because:
// 1. All access to data is synchronized (not shown)
// 2. T itself is Sync
unsafe impl<T: Sync> Sync for MyWrapper<T> {}
```

## References

[^1]: [rustfmt](https://github.com/rust-lang/rustfmt) - Official Rust code formatter
[^2]: [Clippy](https://github.com/rust-lang/rust-clippy) - Official Rust linter with 750+ lints
[^3]: [cargo-audit](https://github.com/rustsec/rustsec/tree/main/cargo-audit) - Audit Cargo.lock for security vulnerabilities
[^4]: [cargo-tarpaulin](https://github.com/xd009642/tarpaulin) - Code coverage tool for Rust
[^5]: [cargo-fuzz](https://github.com/rust-fuzz/cargo-fuzz) - Command-line wrapper for using libFuzzer
[^6]: [rustup](https://rustup.rs/) - Rust toolchain installer
[^7]: [RustSec Advisory Database](https://rustsec.org/) - Security advisory database for Rust crates
[^8]: [cargo-llvm-cov](https://github.com/taiki-e/cargo-llvm-cov) - Cargo subcommand for LLVM source-based code coverage
[^9]: [libFuzzer](https://llvm.org/docs/LibFuzzer.html) - Library for coverage-guided fuzz testing
[^10]: [AFL.rs](https://github.com/rust-fuzz/afl.rs) - Rust bindings for American Fuzzy Lop
[^11]: [cargo-nextest](https://nexte.st/) - Next-generation test runner for Rust
[^12]: [cucumber-rs](https://github.com/cucumber-rs/cucumber) - Cucumber testing framework for Rust
[^13]: [reqwest](https://github.com/seanmonstar/reqwest) - Ergonomic HTTP client for Rust
[^14]: [tokio](https://tokio.rs/) - Asynchronous runtime for Rust
[^15]: [loom](https://github.com/tokio-rs/loom) - Concurrency permutation testing tool
[^16]: [unic](https://github.com/open-i18n/rust-unic) - Unicode and Internationalization crates for Rust
[^17]: [sqlx](https://github.com/launchbadge/sqlx) - Async SQL toolkit with compile-time checked queries
[^18]: [async-std](https://async.rs/) - Async version of Rust standard library
[^19]: [wasm-pack](https://rustwasm.github.io/wasm-pack/) - Tool for building Rust WASM packages
[^20]: [wasm-bindgen](https://github.com/rustwasm/wasm-bindgen) - Facilitating high-level interactions between Wasm modules and JavaScript
[^21]: [syn](https://github.com/dtolnay/syn) - Parser for Rust source code
[^22]: [quote](https://github.com/dtolnay/quote) - Rust quasi-quoting for code generation
[^23]: [proc-macro2](https://github.com/dtolnay/proc-macro2) - Wrapper around the proc-macro API
[^24]: [trybuild](https://github.com/dtolnay/trybuild) - Test harness for ui tests of compiler diagnostics
[^25]: [darling](https://github.com/TedDriggs/darling) - Declarative attribute parser for Rust proc macros
[^26]: [Miri](https://github.com/rust-lang/miri) - Experimental interpreter for Rust's mid-level intermediate representation
[^27]: [The `edition` field](https://doc.rust-lang.org/cargo/reference/manifest.html#the-edition-field) - Cargo manifest reference
[^28]: [rustsec/audit-check](https://github.com/rustsec/audit-check) - GitHub Action running cargo-audit
[^29]: [GitHub Actions runner images](https://github.com/actions/runner-images) - Runner image labels and architectures

## See Also

- [Testing Guide](../process/testing.md) - Comprehensive testing strategies and best practices
- [CI Guide](../process/ci.md) - Continuous integration configuration and workflows
