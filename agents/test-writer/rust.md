---
name: test-writer-rust
description: "Rust testing: unit/integration, mockall, proptest, doc tests"
model: sonnet
---

# Test Writer: Rust Module

> [Test Writer Agent](../code/test-writer.md) > Rust

Rust-specific guidance for test generation.

Sections headed **Complete example** contain whole files that compile and pass
as printed, against the versions pinned in
[Toolchain and Dev-Dependencies](#toolchain-and-dev-dependencies). Every other
code block is a fragment: it assumes the surrounding crate, its imports and
its fixtures, and **MUST NOT** be copied out on its own.

## Quick Reference

| Task | Tool | Command |
| ---- | ---- | ------- |
| Run tests | cargo 1.98.1 | `cargo test --locked` |
| Run one test | cargo 1.98.1 | `cargo test --locked test_name` |
| Doc tests | cargo 1.98.1 | `cargo test --locked --doc` |
| Coverage | cargo-llvm-cov 0.9.1 | `cargo llvm-cov --locked --json --output-path coverage/llvm-cov.json` |
| Line coverage only | cargo-tarpaulin 0.37.2 | `cargo tarpaulin --engine llvm --out Xml` |
| Benchmarks | Criterion 0.8.2 | `cargo bench --locked` |

Every version above was checked against crates.io and
[the stable release channel](https://static.rust-lang.org/dist/channel-rust-stable.toml)
on 2026-09-08.

## Toolchain and Dev-Dependencies

Generated suites **MUST** pin the compiler, every test crate and every
coverage tool, and **MUST** be run with `--locked` against a committed
`Cargo.lock`.

### Why

A floating requirement resolves to whatever is newest when the command runs.
A suite that passed yesterday can then fail today because a generator, a mock
expectation or a report format changed, not because the code under test
changed. Pinning makes a red run mean exactly one thing.

### Configuration

```toml
# Cargo.toml — every version verified on crates.io on 2026-09-08.
[package]
name = "my_crate"
version = "0.1.0"
edition = "2024"
rust-version = "1.98.1"

[dependencies]
serde = { version = "=1.0.229", features = ["derive"] }
serde_json = "=1.0.151"

[dev-dependencies]
criterion = "=0.8.2"
mockall = "=0.15.0"
proptest = "=1.11.0"
tokio = { version = "=1.53.1", features = [
  "macros",
  "rt-multi-thread",
  "test-util",
  "time",
] }

[[bench]]
name = "benchmark"
harness = false
```

```toml
# Do — the resolved version is the version the examples were tested against.
proptest = "=1.11.0"
```

```toml
# Don't — a new minor release can change shrinking or generator behaviour
# halfway through a sprint, with no change to the crate under test.
proptest = "1"
```

## Test Organization

### Unit Tests (In-Module)

```rust
// src/lib.rs or src/calculator.rs

pub fn add(a: i32, b: i32) -> i32 {
    a + b
}

pub fn divide(a: i32, b: i32) -> Result<i32, &'static str> {
    if b == 0 {
        Err("Cannot divide by zero")
    } else {
        Ok(a / b)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn add_positive_numbers() {
        assert_eq!(add(2, 3), 5);
    }

    #[test]
    fn add_negative_numbers() {
        assert_eq!(add(-2, -3), -5);
    }

    #[test]
    fn divide_valid_numbers() {
        assert_eq!(divide(10, 2), Ok(5));
    }

    #[test]
    fn divide_by_zero_returns_error() {
        assert_eq!(divide(10, 0), Err("Cannot divide by zero"));
    }
}
```

### Integration Tests

```rust
// tests/integration_test.rs

use my_crate::Calculator;

#[test]
fn calculator_full_workflow() {
    let calc = Calculator::new();

    calc.push(5);
    calc.push(3);
    let result = calc.add();

    assert_eq!(result, 8);
}
```

## Assertion Macros

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn basic_assertions() {
        // Equality
        assert_eq!(add(2, 2), 4);
        assert_ne!(add(2, 2), 5);

        // Boolean
        assert!(is_valid("test"));
        assert!(!is_empty("test"));

        // With custom message
        assert_eq!(
            result, expected,
            "Expected {} but got {} for input {:?}",
            expected, result, input
        );
    }

    #[test]
    fn float_comparison() {
        let result = calculate_pi();
        let epsilon = 0.0001;
        assert!((result - 3.14159).abs() < epsilon);
    }
}
```

## Testing Panics

```rust
#[test]
#[should_panic]
fn panics_on_invalid_input() {
    process(None); // Should panic
}

#[test]
#[should_panic(expected = "index out of bounds")]
fn panics_with_specific_message() {
    let v = vec![1, 2, 3];
    let _ = v[10];
}
```

## Testing Results

```rust
#[test]
fn parse_returns_result() -> Result<(), ParseError> {
    let config = parse_config("valid: true")?;
    assert_eq!(config.valid, true);
    Ok(())
}

#[test]
fn parse_error_contains_message() {
    let result = parse_config("invalid");

    assert!(result.is_err());
    let err = result.unwrap_err();
    assert!(err.to_string().contains("invalid"));
}
```

## Test Fixtures

```rust
struct TestContext {
    db: MockDatabase,
    service: UserService,
}

impl TestContext {
    fn new() -> Self {
        let db = MockDatabase::new();
        let service = UserService::new(db.clone());
        Self { db, service }
    }
}

#[test]
fn user_service_creates_user() {
    let ctx = TestContext::new();

    let user = ctx.service.create("Test User").unwrap();

    assert_eq!(user.name, "Test User");
    assert!(ctx.db.contains(user.id));
}
```

## Mocking with mockall

```rust
use mockall::{automock, predicate::*};

#[automock]
trait UserRepository {
    fn find_by_id(&self, id: u64) -> Option<User>;
    fn save(&self, user: &User) -> Result<(), Error>;
}

#[test]
fn service_returns_user_from_repo() {
    let mut mock_repo = MockUserRepository::new();
    mock_repo
        .expect_find_by_id()
        .with(eq(1))
        .times(1)
        .returning(|_| Some(User { id: 1, name: "Test".into() }));

    let service = UserService::new(Box::new(mock_repo));
    let user = service.get_user(1);

    assert!(user.is_some());
    assert_eq!(user.unwrap().name, "Test");
}

#[test]
fn service_handles_missing_user() {
    let mut mock_repo = MockUserRepository::new();
    mock_repo
        .expect_find_by_id()
        .returning(|_| None);

    let service = UserService::new(Box::new(mock_repo));
    let user = service.get_user(999);

    assert!(user.is_none());
}
```

## Async Tests

Unit tests **MUST NOT** open a socket. Inject the transport, stub it in the
test, and reserve real HTTP for integration tests backed by a local server.
Time-dependent tests **MUST** drive a paused clock rather than sleeping.

### Why

A unit test that dials `https://api.example.com` fails on an aeroplane, leaks
its result to whoever runs it, and turns an unrelated outage into a red build.
A test that waits five real seconds is both slow and flaky: the deadline it
asserts on depends on load. Tokio's `start_paused = true` auto-advances the
clock, so the same assertion runs in microseconds and never races.

### Complete example

`src/api.rs`, compiled and tested as shown:

```rust
//! Offline-testable HTTP client: the transport is injected, never constructed.

use std::future::Future;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Response {
    pub status: u16,
    pub body: String,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum FetchError {
    Transport(String),
    Status(u16),
}

pub trait Transport {
    fn get(&self, path: &str) -> impl Future<Output = Result<Response, FetchError>> + Send;
}

pub struct ApiClient<T> {
    transport: T,
}

impl<T: Transport> ApiClient<T> {
    pub fn new(transport: T) -> Self {
        Self { transport }
    }

    pub async fn fetch_data(&self) -> Result<Vec<String>, FetchError> {
        let response = self.transport.get("/data").await?;
        if response.status != 200 {
            return Err(FetchError::Status(response.status));
        }
        Ok(response.body.lines().map(str::to_owned).collect())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::Mutex;
    use std::time::Duration;

    struct StubTransport {
        reply: Result<Response, FetchError>,
        requested: Mutex<Vec<String>>,
    }

    impl StubTransport {
        fn new(reply: Result<Response, FetchError>) -> Self {
            Self {
                reply,
                requested: Mutex::new(Vec::new()),
            }
        }
    }

    impl Transport for StubTransport {
        async fn get(&self, path: &str) -> Result<Response, FetchError> {
            self.requested
                .lock()
                .expect("stub mutex is never poisoned")
                .push(path.to_owned());
            self.reply.clone()
        }
    }

    #[tokio::test]
    async fn fetch_data_splits_body_into_lines() {
        let transport = StubTransport::new(Ok(Response {
            status: 200,
            body: "alpha\nbeta".into(),
        }));
        let client = ApiClient::new(transport);

        let data = client.fetch_data().await.expect("stub returns 200");

        assert_eq!(data, vec!["alpha".to_owned(), "beta".to_owned()]);
        let requested = client.transport.requested.lock().expect("stub mutex");
        assert_eq!(requested.as_slice(), ["/data"]);
    }

    #[tokio::test]
    async fn fetch_data_maps_non_200_to_status_error() {
        let transport = StubTransport::new(Ok(Response {
            status: 503,
            body: String::new(),
        }));
        let client = ApiClient::new(transport);

        assert_eq!(client.fetch_data().await, Err(FetchError::Status(503)));
    }

    #[tokio::test]
    async fn fetch_data_propagates_transport_failure() {
        let transport = StubTransport::new(Err(FetchError::Transport("refused".into())));
        let client = ApiClient::new(transport);

        assert_eq!(
            client.fetch_data().await,
            Err(FetchError::Transport("refused".into()))
        );
    }

    #[tokio::test(start_paused = true)]
    async fn slow_operation_exceeds_its_budget() {
        let result = tokio::time::timeout(Duration::from_secs(5), async {
            tokio::time::sleep(Duration::from_secs(30)).await;
        })
        .await;

        assert!(
            result.is_err(),
            "the 5 s budget expires before the 30 s operation"
        );
    }
}
```

The stub asserts the request path as well as the response, so a client that
silently changes its route fails the test.

### Don't

```rust
// Don't — reaches a remote host, so the test result depends on the network
// and on somebody else's uptime.
#[tokio::test]
async fn async_fetch_returns_data() {
    let client = HttpClient::new();
    let result = client.fetch("https://api.example.com/data").await;
    assert!(result.is_ok());
}

// Don't — burns five wall-clock seconds and races under CI load.
#[tokio::test]
async fn async_with_timeout() {
    let result = tokio::time::timeout(Duration::from_secs(5), slow_operation()).await;
    assert!(result.is_ok());
}
```

Real HTTP belongs in `tests/`, against a server the test itself starts and
stops, and **SHOULD** be gated behind a feature so the default `cargo test`
stays offline. See the
[Testing Guide](../../guides/process/testing.md) for the project-wide rule.

## Property-Based Testing

A generated value **MUST** lie inside the domain of the function under test.
Where it cannot, the property **MUST** state the overflow semantics it is
checking. Regression seed files **MUST** be committed.

### Why

`proptest`'s default `i32` strategy covers the whole range, including
`i32::MAX`. Feeding that to an unchecked `a + b` panics with `attempt to add
with overflow` in the debug profile that `cargo test` uses, so the run fails
before the commutativity assertion is ever evaluated. The failure says nothing
about commutativity — it says the property was written over the wrong domain.
Reproduced against `add(a: i32, b: i32) -> i32 { a + b }` with proptest
1.11.0 and rustc 1.98.1:

```text
thread 'tests::add_is_commutative' panicked at src/lib.rs:2:5:
attempt to add with overflow
Test failed: attempt to add with overflow.
minimal failing input: a = -1819134462, b = -328349187
```

### Do

```rust
use proptest::prelude::*;

// Halving the range guarantees every generated sum fits in i32, so the
// property tests commutativity rather than the debug overflow check.
const HALF_MIN: i32 = i32::MIN / 2;
const HALF_MAX: i32 = i32::MAX / 2;

proptest! {
    #[test]
    fn add_is_commutative(a in HALF_MIN..=HALF_MAX, b in HALF_MIN..=HALF_MAX) {
        prop_assert_eq!(add(a, b), add(b, a));
    }

    // Alternative when the range is awkward to express: keep the full
    // strategy and discard out-of-domain pairs.
    #[test]
    fn add_matches_checked_add_in_domain(a: i32, b: i32) {
        prop_assume!(a.checked_add(b).is_some());
        prop_assert_eq!(add(a, b), a.checked_add(b).unwrap());
    }

    // The overflow semantics get their own property, stated explicitly.
    #[test]
    fn wrapping_add_is_commutative(a: i32, b: i32) {
        prop_assert_eq!(a.wrapping_add(b), b.wrapping_add(a));
    }
}
```

### Don't

```rust
proptest! {
    // Don't — the generator produces i32::MAX and 1, which panics in the
    // debug profile before prop_assert_eq! runs.
    #[test]
    fn add_is_commutative(a: i32, b: i32) {
        prop_assert_eq!(add(a, b), add(b, a));
    }
}
```

### Other strategies

```rust
proptest! {
    #[test]
    fn parse_roundtrip(s in "[a-z]{1,10}") {
        let parsed = parse(&s)?;
        let serialized = serialize(&parsed);
        prop_assert_eq!(s, serialized);
    }

    #[test]
    fn vec_length_preserved(v: Vec<i32>) {
        let processed = process(v.clone());
        prop_assert_eq!(v.len(), processed.len());
    }
}
```

### Regression seeds

On failure proptest writes the shrunk case to
`proptest-regressions/<module>.txt` and replays it before generating anything
new. That file **MUST** be committed, otherwise the next run starts from a
different random seed and the bug disappears from CI:

```text
# proptest-regressions/lib.txt
# Seeds for failure cases proptest has generated in the past. It is
# automatically read and these particular cases re-run before any
# novel cases are generated.
#
# It is recommended to check this file in to source control so that
# everyone who runs the test benefits from these saved cases.
cc 94387392d2c166ed52266f2979fadf84c0b40a30c34ea4869dbba1d1859a11f4 # shrinks to a = -1819134462, b = -328349187
```

## Test Attributes

```rust
#[test]
#[ignore] // Skip by default, run with `cargo test -- --ignored`
fn expensive_test() {
    // Long-running test
}

#[test]
#[cfg(feature = "integration")]
fn integration_test() {
    // Only runs when feature is enabled
}

#[test]
#[cfg(not(target_os = "windows"))]
fn unix_only_test() {
    // Platform-specific test
}
```

## Coverage Commands

cargo-llvm-cov **MUST** be the primary coverage tool. Coverage tools **MUST**
be installed with an explicit `--version` and `--locked`.

### Why

Two reasons, one per rule.

cargo-llvm-cov wraps rustc's `-C instrument-coverage`, so it reports line,
region and function coverage from the same instrumentation the compiler
emits, and it exports stable JSON. cargo-tarpaulin's own help text lists
`-b, --branch  Branch coverage: NOT IMPLEMENTED` in 0.37.2, and on Linux its
default backend is ptrace, restricted to `x86_64`. Tarpaulin remains useful
for line coverage; it **MUST NOT** be used to make a branch-coverage claim.

`cargo install cargo-tarpaulin` with no version installs whatever is newest
that day and resolves the tool's own dependency tree afresh, so the report
format can change under a pipeline that never changed. `--version` fixes the
tool; `--locked` makes it build from its published `Cargo.lock`.

### Commands

```bash
# Install, pinned. Versions current on crates.io on 2026-09-08.
cargo install cargo-llvm-cov --version 0.9.1 --locked
rustup component add llvm-tools-preview

# Machine-readable report, the form the agent parses.
cargo llvm-cov --locked --json --output-path coverage/llvm-cov.json

# Human-readable report.
cargo llvm-cov --locked --html --output-dir coverage/

# Which lines were never executed.
cargo llvm-cov report --summary-only --show-missing-lines

# Thresholds. Lines and regions are supported on stable.
cargo llvm-cov --locked --fail-under-lines 80 --fail-under-regions 70

# Coverage with specific features.
cargo llvm-cov --locked --features "feature1,feature2"
```

Branch coverage is **NOT** available on stable. `cargo llvm-cov --branch` is
documented as unstable and needs a nightly toolchain
([taiki-e/cargo-llvm-cov#8](https://github.com/taiki-e/cargo-llvm-cov/issues/8)),
and without it every `branches` counter in the JSON export is zero. Gate on
`--fail-under-regions` instead: regions are the stable proxy for branch
structure.

Line coverage only, when tarpaulin is already in the pipeline:

```bash
cargo install cargo-tarpaulin --version 0.37.2 --locked
cargo tarpaulin --engine llvm --out Xml --output-dir coverage/
cargo tarpaulin --engine llvm --fail-under 80
```

## Coverage Report Parsing

The agent **MUST** parse a machine-readable report and map uncovered records
back to source. It **MUST NOT** infer coverage from a rendered summary.

### Why

A pasted report fragment cannot be validated, cannot be diffed and cannot be
turned into a list of files that need tests. The `llvm-cov export` JSON has a
documented schema, a `type` discriminator and absolute filenames, so a parser
can reject the wrong file, normalise paths against the workspace root and
rank targets deterministically.

### Schema

`cargo llvm-cov --json` emits `llvm-cov export` output. The fields this
parser relies on, as produced by cargo-llvm-cov 0.9.1 and LLVM export
version `3.1.0`:

| Path | Meaning |
| ---- | ------- |
| `type` | Always `llvm.coverage.json.export`; reject anything else |
| `data[].totals` | Workspace counters |
| `data[].files[].filename` | Absolute path; normalise against the workspace root |
| `data[].files[].summary.lines` | `{count, covered, percent}` |
| `data[].files[].summary.regions` | `{count, covered, notcovered, percent}` |
| `data[].files[].summary.branches` | All zero unless built with nightly `--branch` |
| `data[].files[].segments[]` | `[line, column, count, has_count, is_region_entry, is_gap_region]` |

### Parser

```rust
//! Parse `cargo llvm-cov --json` output into ranked, source-mapped test targets.

use std::collections::BTreeSet;
use std::path::Path;

use serde::Deserialize;

/// `llvm-cov export` writes this discriminator; anything else is the wrong file.
const EXPECTED_TYPE: &str = "llvm.coverage.json.export";

#[derive(Debug, Deserialize)]
struct Export {
    #[serde(rename = "type")]
    kind: String,
    data: Vec<Datum>,
}

#[derive(Debug, Deserialize)]
struct Datum {
    files: Vec<FileEntry>,
    totals: Summary,
}

#[derive(Debug, Deserialize)]
struct FileEntry {
    filename: String,
    summary: Summary,
    #[serde(default)]
    segments: Vec<Segment>,
}

#[derive(Debug, Deserialize)]
struct Summary {
    lines: Counters,
    regions: Counters,
}

#[derive(Debug, Deserialize)]
struct Counters {
    count: u64,
    covered: u64,
}

/// One `segments` entry, exactly as `llvm-cov export` emits it:
/// `[line, column, count, has_count, is_region_entry, is_gap_region]`.
type Segment = (u32, u32, u64, bool, bool, bool);

#[derive(Debug, PartialEq, Eq)]
pub struct Target {
    pub path: String,
    pub uncovered_regions: u64,
    /// Lines that begin at least one uncovered region. A line listed here may
    /// still be partly executed, so this is a superset of the fully missed
    /// lines that `cargo llvm-cov --show-missing-lines` prints.
    pub region_entry_lines: Vec<u32>,
}

#[derive(Debug, PartialEq, Eq)]
pub enum ReportError {
    Malformed(String),
    NotAnLlvmCovExport(String),
    NoData,
    InconsistentCounters { path: String },
}

impl std::fmt::Display for ReportError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Malformed(why) => write!(f, "report is not valid llvm-cov JSON: {why}"),
            Self::NotAnLlvmCovExport(kind) => {
                write!(f, "expected type {EXPECTED_TYPE:?}, found {kind:?}")
            }
            Self::NoData => write!(f, "report contains no coverage data"),
            Self::InconsistentCounters { path } => {
                write!(f, "{path}: covered count exceeds total count")
            }
        }
    }
}

impl std::error::Error for ReportError {}

/// Rank source files by uncovered regions, most uncovered first.
///
/// `root` is stripped from every absolute filename so the result addresses
/// files the way the repository does.
pub fn uncovered_targets(json: &str, root: &Path) -> Result<Vec<Target>, ReportError> {
    let export: Export =
        serde_json::from_str(json).map_err(|e| ReportError::Malformed(e.to_string()))?;
    if export.kind != EXPECTED_TYPE {
        return Err(ReportError::NotAnLlvmCovExport(export.kind));
    }
    let datum = export.data.first().ok_or(ReportError::NoData)?;
    if datum.totals.lines.count == 0 {
        return Err(ReportError::NoData);
    }

    let mut targets = Vec::new();
    for file in &datum.files {
        let path = normalise(&file.filename, root);
        if file.summary.lines.covered > file.summary.lines.count
            || file.summary.regions.covered > file.summary.regions.count
        {
            return Err(ReportError::InconsistentCounters { path });
        }
        let uncovered_regions = file.summary.regions.count - file.summary.regions.covered;
        if uncovered_regions == 0 {
            continue;
        }
        let region_entry_lines: BTreeSet<u32> = file
            .segments
            .iter()
            .filter(
                |&&(_, _, count, has_count, is_region_entry, is_gap_region)| {
                    has_count && is_region_entry && !is_gap_region && count == 0
                },
            )
            .map(|&(line, ..)| line)
            .collect();
        targets.push(Target {
            path,
            uncovered_regions,
            region_entry_lines: region_entry_lines.into_iter().collect(),
        });
    }
    targets.sort_by(|a, b| {
        b.uncovered_regions
            .cmp(&a.uncovered_regions)
            .then_with(|| a.path.cmp(&b.path))
    });
    Ok(targets)
}

fn normalise(filename: &str, root: &Path) -> String {
    Path::new(filename)
        .strip_prefix(root)
        .unwrap_or(Path::new(filename))
        .to_string_lossy()
        .replace('\\', "/")
}
```

### Parser tests, including malformed input

```rust
#[cfg(test)]
mod tests {
    use super::*;

    const REPORT: &str = r#"{
      "type": "llvm.coverage.json.export",
      "version": "3.1.0",
      "data": [{
        "totals": {"lines": {"count": 10, "covered": 6}, "regions": {"count": 8, "covered": 5}},
        "files": [
          {
            "filename": "/repo/src/lib.rs",
            "summary": {"lines": {"count": 6, "covered": 3},
                        "regions": {"count": 5, "covered": 2}},
            "segments": [[12, 5, 0, true, true, false], [19, 9, 0, true, true, false],
                         [21, 1, 0, true, false, false], [23, 1, 0, true, true, true]]
          },
          {
            "filename": "/repo/src/ok.rs",
            "summary": {"lines": {"count": 4, "covered": 4},
                        "regions": {"count": 3, "covered": 3}},
            "segments": []
          }
        ]
      }]
    }"#;

    #[test]
    fn ranks_only_files_with_uncovered_regions() {
        let targets = uncovered_targets(REPORT, Path::new("/repo")).unwrap();

        assert_eq!(
            targets,
            vec![Target {
                path: "src/lib.rs".to_owned(),
                uncovered_regions: 3,
                region_entry_lines: vec![12, 19],
            }]
        );
    }

    #[test]
    fn rejects_malformed_json() {
        let error = uncovered_targets("{\"type\": ", Path::new("/repo")).unwrap_err();
        assert!(matches!(error, ReportError::Malformed(_)), "got {error:?}");
    }

    #[test]
    fn rejects_a_report_from_another_tool() {
        let json = r#"{"type": "cobertura", "data": []}"#;
        assert_eq!(
            uncovered_targets(json, Path::new("/repo")),
            Err(ReportError::NotAnLlvmCovExport("cobertura".to_owned()))
        );
    }

    #[test]
    fn rejects_an_empty_report() {
        let json = r#"{"type": "llvm.coverage.json.export", "data": []}"#;
        assert_eq!(
            uncovered_targets(json, Path::new("/repo")),
            Err(ReportError::NoData)
        );
    }

    #[test]
    fn rejects_counters_that_cannot_hold() {
        let json = REPORT.replace(
            "\"lines\": {\"count\": 6, \"covered\": 3}",
            "\"lines\": {\"count\": 6, \"covered\": 9}",
        );
        assert_eq!(
            uncovered_targets(&json, Path::new("/repo")),
            Err(ReportError::InconsistentCounters {
                path: "src/lib.rs".to_owned()
            })
        );
    }
}
```

### Tarpaulin's Cobertura output

If a pipeline already produces Cobertura XML from tarpaulin, read
`line-rate` only. The `branch-rate` attribute is emitted because the Cobertura
schema requires it, not because tarpaulin measured anything:

```xml
<!-- cargo tarpaulin (engine llvm, Xml output). The branch-rate attribute is
     not a measurement: branch coverage is reported as NOT IMPLEMENTED by
     cargo-tarpaulin 0.37.2, so it is omitted here. -->
<coverage line-rate="0.85" version="1.0">
  <packages>
    <package name="my_crate">
      <classes>
        <class filename="src/lib.rs" line-rate="0.90">
          <lines>
            <line number="10" hits="5"/>
            <line number="15" hits="0"/>
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
```

## Doc Tests

A doc example **MUST** compile and run under `cargo test --doc`. Bodies
elided with `// ...` do not, so the example **MUST** be backed by a real
implementation or hidden behind `#` lines.

### Why

`cargo test --doc` compiles every unmarked ` ``` ` block as its own crate. A
block that references a function whose body is `// ...` fails to build, so an
elided example is not an example — it is a broken test that ships in the
public documentation.

### Complete example

`src/config.rs`, compiled and tested as shown:

```rust
use std::collections::BTreeMap;
use std::error::Error;
use std::fmt;

#[derive(Debug, Default, PartialEq, Eq)]
pub struct Config {
    entries: BTreeMap<String, String>,
}

impl Config {
    pub fn get(&self, key: &str) -> Option<&str> {
        self.entries.get(key).map(String::as_str)
    }
}

#[derive(Debug, PartialEq, Eq)]
pub struct ConfigError {
    line: usize,
}

impl fmt::Display for ConfigError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "invalid configuration on line {}: expected key=value",
            self.line
        )
    }
}

impl Error for ConfigError {}

/// Parses a newline-separated `key=value` configuration string.
///
/// # Examples
///
/// ```
/// use my_crate::parse_config;
///
/// let config = parse_config("key=value")?;
/// assert_eq!(config.get("key"), Some("value"));
/// # Ok::<(), my_crate::ConfigError>(())
/// ```
///
/// ```should_panic
/// use my_crate::parse_config;
///
/// parse_config("invalid").unwrap(); // no '=', so this panics
/// ```
///
/// # Errors
///
/// Returns [`ConfigError`] for any line that does not contain `=`.
pub fn parse_config(input: &str) -> Result<Config, ConfigError> {
    let mut entries = BTreeMap::new();
    for (index, line) in input.lines().enumerate() {
        if line.trim().is_empty() {
            continue;
        }
        let (key, value) = line
            .split_once('=')
            .ok_or(ConfigError { line: index + 1 })?;
        entries.insert(key.trim().to_owned(), value.trim().to_owned());
    }
    Ok(Config { entries })
}
```

The `?` in the first example needs a return type, which the hidden
`# Ok::<(), my_crate::ConfigError>(())` line supplies without appearing in the
rendered documentation.

### Don't

```rust
/// # Examples
///
/// ```
/// # use my_crate::parse_config;
/// let config = parse_config("key=value").unwrap();
/// ```
// Don't — the doc test cannot build, because this body does not exist.
pub fn parse_config(s: &str) -> Result<Config, Error> {
    // ...
}
```

## Benchmarks

Benchmarks **MUST** import `black_box` from `std::hint`, not from Criterion.

### Why

Criterion 0.8.2 keeps `criterion::black_box` only as a deprecated re-export.
Its body is `std::hint::black_box(dummy)`, behind this attribute:

```rust
#[deprecated(note = "use `std::hint::black_box()` instead")]
pub fn black_box<T>(dummy: T) -> T {
    std::hint::black_box(dummy)
}
```

Importing it produces a deprecation warning that fails any build using
`-D warnings`. `std::hint::black_box` has been the stable primitive since Rust
1.66, so nothing here needs a nightly toolchain: Criterion runs on stable and
supplies only the harness, registration and statistics.

### Configuration

```toml
# Cargo.toml — Criterion replaces libtest's harness for this target.
[dev-dependencies]
criterion = "=0.8.2"

[[bench]]
name = "benchmark"
harness = false
```

### Complete example

```rust
// benches/benchmark.rs

use std::hint::black_box;

use criterion::{Criterion, criterion_group, criterion_main};
use my_crate::fibonacci;

fn bench_fibonacci(c: &mut Criterion) {
    c.bench_function("fib 20", |b| b.iter(|| fibonacci(black_box(20))));
}

criterion_group!(benches, bench_fibonacci);
criterion_main!(benches);
```

### Don't

```rust
// Don't — deprecated in Criterion 0.8.2 and a hard error under -D warnings.
use criterion::{black_box, criterion_group, criterion_main, Criterion};
```

## See Also

- [Rust Style Guide](rust.md)
- [Testing Guide](../../guides/process/testing.md)
