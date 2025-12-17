# Rust Style Guide

> [Doctrine](../../README.md) > [Languages](../README.md) > Rust

**The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119.html).**

This guide follows official Rust style conventions enforced by rustfmt[^1] and Clippy[^2].

## Quick Reference

| Task | Tool | Command |
|------|------|---------|
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

Clippy[^2] is the official Rust linter with 750+ lints. It's included with rustup[^6], making it zero-cost to adopt. Unlike third-party linters, Clippy has deep integration with the Rust compiler and is maintained by the Rust team, ensuring compatibility with new language features and idiomatic Rust patterns.

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
msrv = "1.75"
cognitive-complexity-threshold = 25
```

### Recommended Lint Groups

Projects **SHOULD** enable pedantic and nursery lint groups, and **MUST** deny unwrap and expect in production code:

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

rustfmt[^1] is the official Rust formatter, maintained by the Rust team. It eliminates formatting debates and ensures consistent style across the entire Rust ecosystem. Unlike other languages with competing formatters, rustfmt has become the de facto standard with universal adoption.

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

Types **MUST** eagerly implement common traits. Rust's orphan rule prevents adding trait implementations later if you don't control both the trait and the type.

### Why This Matters

- **Orphan rule lock-in**: Once your crate is published, users can't add `Debug` or `Clone` to your types
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
|-------|-------------------|-------|
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

## Security Analysis: cargo-audit

Projects **MUST** run cargo-audit[^3] to check for known vulnerabilities in dependencies.

### Why cargo-audit

cargo-audit[^3] checks your dependencies against the RustSec Advisory Database[^7], which tracks security vulnerabilities in Rust crates. It integrates seamlessly into CI pipelines and provides actionable remediation steps for vulnerable dependencies.

```bash
# Install
cargo install cargo-audit

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
    steps:
      - uses: actions/checkout@v4
      - uses: rustsec/audit-check@v2
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
# Install cargo-audit
cargo install cargo-audit

# Run security audit
cargo audit

# Fix vulnerabilities automatically (when possible)
cargo audit fix
```

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
cucumber = "0.21"  # cucumber-rs[^12]
```

```rust
// tests/cucumber.rs
use cucumber::{given, when, then, World};

#[derive(Debug, Default, World)]
struct MyWorld {
    result: Option<String>,
}

#[given("a user is logged in")]
async fn given_logged_in(world: &mut MyWorld) {
    // Setup
}

#[when(regex = r"they request (.*)")]
async fn when_request(world: &mut MyWorld, resource: String) {
    world.result = Some(fetch(&resource).await);
}

#[then(regex = r"they receive (.*)")]
async fn then_receive(world: &mut MyWorld, expected: String) {
    assert_eq!(world.result.as_ref().unwrap(), &expected);
}

#[tokio::main]
async fn main() {
    MyWorld::run("tests/features").await;
}
```

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
channel = "1.75.0"
components = ["rustfmt", "clippy"]
targets = ["x86_64-unknown-linux-gnu", "wasm32-unknown-unknown"]
```

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

```yaml
jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        rust: [stable, beta, nightly]
        target:
          - x86_64-unknown-linux-gnu
          - x86_64-pc-windows-msvc
          - x86_64-apple-darwin
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@master
        with:
          toolchain: ${{ matrix.rust }}
          targets: ${{ matrix.target }}
      - run: cargo test --target ${{ matrix.target }}
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

```rust
use unic::normal::StrNormalForm;

#[test]
fn test_unicode_normalization() {
    let s1 = "café";  // NFC
    let s2 = "café";  // NFD

    assert_ne!(s1, s2);
    assert_eq!(s1.nfc().collect::<String>(), s2.nfc().collect::<String>());
}
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

```rust
#[cfg(feature = "feature-a")]
pub fn new_algorithm() -> String {
    "Algorithm A".into()
}

#[cfg(not(feature = "feature-a"))]
pub fn new_algorithm() -> String {
    "Algorithm B".into()
}

#[test]
fn test_feature_behavior() {
    let result = new_algorithm();

    #[cfg(feature = "feature-a")]
    assert_eq!(result, "Algorithm A");

    #[cfg(feature = "feature-b")]
    assert_eq!(result, "Algorithm B");
}
```

### Conditional Compilation with cfg Attributes

```rust
#[cfg(target_os = "linux")]
fn platform_specific() -> &'static str {
    "Linux"
}

#[cfg(target_os = "windows")]
fn platform_specific() -> &'static str {
    "Windows"
}

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
}
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

## See Also

- [Testing Guide](../testing.md) - Comprehensive testing strategies and best practices
- [CI Guide](../../ci.md) - Continuous integration configuration and workflows
