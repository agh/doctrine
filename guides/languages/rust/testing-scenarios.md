# Rust Testing Scenarios

> [Doctrine](../../../README.md) > [Languages](../README.md) > [Rust](../rust.md) > Rust Testing Scenarios

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in
BCP 14 [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119)
[RFC 8174](https://datatracker.ietf.org/doc/html/rfc8174) when, and only
when, they appear in all capitals, as shown here.

This guide covers test patterns for behaviours that unit tests miss: end-to-end
acceptance, idempotence, reliability under failure, compatibility across
versions and platforms, internationalisation, and data integrity. The toolchain,
lint, formatting, dependency and CI rules in the [Rust Style Guide](../rust.md)
apply and are not repeated here; every version quoted is listed in its [Tested
Version Matrix](versions.md#tested-version-matrix) and was current on 8 September
2026.

## E2E & Acceptance Testing

Crates **SHOULD** exercise their public API from `tests/`, not only from unit
tests in `src/`.

### Why

A file under `tests/` is compiled as a separate crate that links the library
the way a user does, so it can only reach `pub` items. That makes it the only
place where a missing `pub`, a private type leaking through a public signature,
or a feature that is only enabled by a dev-dependency shows up. Unit tests in
`src/` see private items and therefore cannot detect any of it.

```rust
// GOOD: tests/api.rs — the crate is linked, so only the public API is visible
use my_crate::App;

#[test]
fn public_api_is_usable() {
    assert_eq!(App::new().process_request("input"), "expected_output");
}
```

```rust
// BAD: the same assertion inside src/lib.rs. It passes whether or not `App`
// and `process_request` are public.
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn works() {
        assert_eq!(App::new().process_request("input"), "expected_output");
    }
}
```

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

cucumber 0.23.0 requires Rust 1.88 or later, below the MSRV of 1.94.0 that the
[Rust Style Guide](../rust.md#toolchain-edition-and-msrv) declares, so it adds
no constraint of its own.[^12]

### API Testing Patterns

```toml
[dev-dependencies]
reqwest = { version = "0.13.4", features = ["json"] }  # reqwest[^13]
tokio = { version = "1.53.1", features = ["macros", "rt-multi-thread"] }
```

**Why the `json` feature**: `Response::json` is feature-gated. Without it the
call fails with "error[E0599]: no method named `json` found for struct
`Response`", which reads as a version problem rather than a missing feature.

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

## Idempotence Testing

Operations that a client **MAY** retry — anything behind a network, a queue or
a timeout — **MUST** be tested by invoking them twice and asserting on the
resulting state, not on the second return value.

### Why

A retried request is indistinguishable, at the server, from a duplicate. If the
second call succeeds but creates a second row, the operation is not idempotent
and the test that asserted only `result2.is_ok()` said nothing. Rust's type
system does not help here: idempotence is a property of the effect, so only an
assertion on the observable state can detect it.

```rust
// GOOD: asserts on the state after the retry.
assert!(db.create_user(id, "alice").is_ok());
assert!(db.create_user(id, "alice").is_ok());
assert_eq!(db.count_users(), 1);
```

```rust
// BAD: passes for a non-idempotent implementation that inserts twice.
assert!(db.create_user(id, "alice").is_ok());
assert!(db.create_user(id, "alice").is_ok());
```

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

Failure paths **MUST** be tested by injecting the failure, not by waiting for
it to occur naturally.

### Why

Timeouts, partial failures and circuit-breaker transitions are the code paths
least covered by ordinary tests and most likely to be wrong, because they only
execute when something is already going badly. A test that depends on a real
slow dependency is also the classic flaky test: it passes on a fast machine and
fails in CI. Injecting the failure — a counter that returns errors for the
first N calls, a future that never completes — makes the path deterministic.

```rust
// GOOD: deterministic. The future never completes, so the timeout must fire.
#[tokio::test]
async fn times_out() {
    let result = timeout(Duration::from_millis(10), std::future::pending::<()>()).await;
    assert!(result.is_err());
}
```

```rust
// BAD: depends on a real dependency being slower than 100 ms today.
#[tokio::test]
async fn times_out() {
    let result = timeout(Duration::from_millis(100), fetch_from_upstream()).await;
    assert!(result.is_err());
}
```

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

Crates **MUST** verify every platform and toolchain they claim to support.

### Why

A crate's supported set is whatever CI proves, not whatever the README says.
Conditional compilation, C dependencies and integer widths all differ by
target, so a `cfg`-gated item that is missing on macOS or a `usize` assumption
that breaks on `wasm32` compiles cleanly everywhere except the platform nobody
built. The MSRV is the same claim in the time dimension and is verified the
same way — with a lane that uses the exact version.

### Version Pinning with rust-toolchain.toml

The toolchain pin, the MSRV declaration and the two CI lanes are specified in
[Toolchain, Edition and MSRV](../rust.md#toolchain-edition-and-msrv). The pinned channel
**MUST** be at least the highest `rust-version` in the dependency graph:
cucumber 0.23.0 requires Rust 1.88 and SQLx 0.9.0 requires 1.94.0, so a 1.75
pin cannot build this guide's own examples.[^12][^17]

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
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: dtolnay/rust-toolchain@6c977a6ca4077a0ceb28ffbe03f59d46e9ac8772 # v1
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
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: dtolnay/rust-toolchain@6c977a6ca4077a0ceb28ffbe03f59d46e9ac8772 # v1
        with:
          toolchain: stable
          targets: ${{ matrix.target }}
      - run: cargo check --target ${{ matrix.target }}
```

`macos-latest` is an arm64 image, so `aarch64-apple-darwin` is its native
target; `x86_64-apple-darwin` would need Rosetta to run the resulting test
binary.[^29]

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

### Unicode Normalisation

unic **MUST NOT** be used. Normalisation-only work **SHOULD** use
unicode-normalization[^16]; locale-aware formatting, collation, segmentation
and case mapping **SHOULD** use ICU4X[^47].

**Why**: unic 0.9.0 was published on 3 March 2019 and carries Unicode 10 data.
The current standard is Unicode 17.0.0, so unic classifies every character
assigned since 2017 as unassigned and normalises them incorrectly or not at
all. unicode-normalization 0.1.25 exposes
`unicode_normalization::UNICODE_VERSION == (17, 0, 0)`, matching the current
standard, and does one job well. ICU4X is the choice when the requirement is
internationalisation rather than normalisation: it carries CLDR locale data,
which no normalisation crate does.[^48][^16][^47]

```toml
[dependencies]
unicode-normalization = "0.1.25"  # Unicode 17.0.0 data
```

```toml
# For locale-aware i18n rather than normalisation
[dependencies]
icu = "2.3.1"  # ICU4X[^47]
```

Normalisation fixtures **MUST** be written with explicit Unicode escapes.
Editors and clipboards silently normalise pasted text, so two literals that
look different on screen can hold identical code points, which turns the
assertion into a no-op or an outright failure.

```rust
use unicode_normalization::UnicodeNormalization as _;

#[must_use]
pub fn nfc(text: &str) -> String {
    text.nfc().collect()
}

#[test]
fn normalisation_makes_the_two_spellings_equal() {
    // "café" with a precomposed U+00E9, versus "e" + U+0301 combining acute.
    let precomposed = "caf\u{e9}";  // NFC
    let decomposed = "cafe\u{301}"; // NFD

    // Different code points before normalisation.
    assert_ne!(precomposed, decomposed);
    assert_eq!(precomposed.chars().count(), 4);
    assert_eq!(decomposed.chars().count(), 5);

    // Equal after normalisation.
    assert_eq!(nfc(precomposed), nfc(decomposed));
}

#[test]
fn unicode_data_version_is_current() {
    assert_eq!(unicode_normalization::UNICODE_VERSION, (17, 0, 0));
}
```

```rust
// BAD: both literals are precomposed, so `assert_ne!` fails immediately.
let s1 = "café";  // claims NFC
let s2 = "café";  // claims NFD, but holds the same U+00E9
```

```toml
# BAD: unreleased since 2019, Unicode 10 data.
unic = "0.9"
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

SQLx[^17] 0.9 **MUST** be used, and the runtime and TLS backends **MUST** be
selected explicitly. The repository moved from `launchbadge/sqlx` to
`transact-rs/sqlx`; the old URL redirects but **MUST NOT** be used in new
links.

**Why**: SQLx has no default runtime or TLS backend. `runtime-tokio`,
`runtime-smol` and `runtime-async-global-executor` are mutually exclusive
choices, and TLS is a separate axis: `tls-none`, `tls-native-tls`, or one of
the `tls-rustls-*` variants which differ in cryptographic provider and
certificate store. Leaving TLS unstated works locally over a Unix socket and
fails on a managed database that requires TLS. `default-features = false` makes
the choice explicit rather than inheriting `any`, `macros`, `migrate` and
`json`.[^17]

```toml
[dependencies]
sqlx = { version = "0.9.0", default-features = false, features = [
    "runtime-tokio",             # runtime: exactly one
    "tls-rustls-ring-webpki",    # TLS: pick explicitly, or tls-none
    "postgres",
    "macros",                    # query_as!, query_scalar!, sqlx::test
    "migrate",
] }
```

```toml
# BAD: SQLx 0.7, the pre-0.9 combined feature name, and no TLS decision.
sqlx = { version = "0.7", features = ["runtime-tokio-rustls", "postgres"] }
```

The checked macros need schema access at **compile** time. Either
`DATABASE_URL` **MUST** be set when building, or offline metadata **MUST** be
committed:

```bash
cargo install sqlx-cli --version 0.9.0 --locked --no-default-features \
  --features postgres,rustls
cargo sqlx prepare        # writes .sqlx/, which MUST be committed
SQLX_OFFLINE=true cargo check
```

**Why**: without one of the two, `cargo check` fails with
"error: set `DATABASE_URL` to use query macros online, or run
`cargo sqlx prepare` to update the query cache" — including in CI, where the
database usually does not exist. Committing `.sqlx/` keeps the check
reproducible and makes a schema change visible in review.

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

Where compile-time checking is not wanted, the runtime API needs neither a
database at build time nor offline metadata:

```rust
use sqlx::PgPool;

#[derive(Debug, sqlx::FromRow)]
pub struct User {
    pub id: i64,
    pub name: String,
    pub email: String,
}

/// Loads one user by primary key.
///
/// # Errors
///
/// Returns the driver error when the row is missing or the query fails.
pub async fn fetch_user(pool: &PgPool, id: i64) -> sqlx::Result<User> {
    sqlx::query_as::<_, User>("SELECT id, name, email FROM users WHERE id = $1")
        .bind(id)
        .fetch_one(pool)
        .await
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

## References

[^12]: [cucumber-rs](https://github.com/cucumber-rs/cucumber) - Cucumber testing framework for Rust
[^13]: [reqwest](https://github.com/seanmonstar/reqwest) - Ergonomic HTTP client for Rust
[^16]: [unicode-normalization](https://github.com/unicode-rs/unicode-normalization) - Unicode normalisation for Rust, Unicode 17.0.0 data
[^17]: [sqlx](https://github.com/transact-rs/sqlx) - Async SQL toolkit with compile-time checked queries
[^29]: [GitHub Actions runner images](https://github.com/actions/runner-images) - Runner image labels and architectures
[^47]: [ICU4X](https://unicode-org.github.io/icu4x/) - Unicode's internationalisation library for Rust
[^48]: [Unicode 17.0.0](https://www.unicode.org/versions/latest/) - The current version of the Unicode Standard

## See Also

- [Rust Style Guide](../rust.md) - Toolchain, lints, formatting, dependencies and CI
- [Rust topic guides](README.md) - The other Rust topic guides
