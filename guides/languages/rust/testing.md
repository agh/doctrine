# Rust Testing Tools

> [Doctrine](../../../README.md) > [Languages](../README.md) > [Rust](../rust.md) > Rust Testing Tools

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in
BCP 14 [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119)
[RFC 8174](https://datatracker.ietf.org/doc/html/rfc8174) when, and only
when, they appear in all capitals, as shown here.

This guide covers the tools that make a Rust test suite trustworthy: coverage,
fuzzing, property and mutation testing, public-API compatibility checks,
benchmarking, suite throughput and concurrency permutation testing with Loom.
The toolchain, lint, formatting and pre-commit rules in the
[Rust Style Guide](../rust.md) apply and are not repeated here, and so do the
[dependency](dependencies.md) and [CI](ci.md) rules; every version quoted is
listed in the [Tested Version Matrix](versions.md#tested-version-matrix) and was
current on 8 September 2026.

## Code Coverage

Projects **SHOULD** measure code coverage. cargo-llvm-cov[^8] **SHOULD** be the
default; cargo-tarpaulin[^4] **MAY** be used where its report formats are
required.

### Why cargo-llvm-cov

cargo-llvm-cov drives the compiler's own source-based instrumentation
(`-C instrument-coverage`), so it reports on every target the toolchain
supports rather than on the platforms a separate tracing engine has been ported
to, and it counts branches the way the compiler sees them. tarpaulin's default
ptrace engine is Linux/x86-64 only.[^4][^8]

```bash
cargo install cargo-llvm-cov --version 0.9.1 --locked

cargo llvm-cov --all-features --workspace            # summary
cargo llvm-cov --all-features --html                 # HTML report
cargo llvm-cov --all-features --lcov --output-path lcov.info
cargo llvm-cov --all-features --fail-under-lines 80  # CI gate
```

```bash
# Alternative: cargo-tarpaulin
cargo install cargo-tarpaulin --version 0.37.2 --locked
cargo tarpaulin --out Html --fail-under 80
```

Coverage targets and the reasoning behind them are in the
[Testing Guide](../../process/testing.md); this guide covers only the Rust tooling.

## Fuzzing: cargo-fuzz

Projects handling untrusted input **SHOULD** use fuzzing. cargo-fuzz[^5]
**SHOULD** be the default choice.

### Platform Requirements

cargo-fuzz drives libFuzzer[^9], which needs LLVM sanitizer support. Projects
**MUST** confirm the environment before adopting it:

| Requirement | Supported |
| ----------- | --------- |
| Architecture | x86-64 and AArch64 only |
| Operating system | Unix-like only — **not Windows** |
| Toolchain | nightly, because the flags it passes are unstable |
| Host tooling | a C++ compiler with C++11 support |

**Why**: these are libFuzzer's constraints, not cargo-fuzz's, and they are not
detected until link time. A Windows CI job added to a fuzzing matrix fails
after the whole dependency tree has been built. Fuzzing jobs **MUST** be
restricted to Linux or macOS runners.[^5]

### Setup

```bash
rustup toolchain install nightly-2026-09-01
cargo install cargo-fuzz --version 0.13.2 --locked

cargo fuzz init
cargo fuzz add my_target
```

```toml
# fuzz/Cargo.toml
[package]
name = "my_crate-fuzz"
version = "0.0.0"
edition = "2024"
publish = false

[package.metadata]
cargo-fuzz = true

[dependencies]
libfuzzer-sys = "0.4.13"

[dependencies.my_crate]
path = ".."

[[bin]]
name = "my_target"
path = "fuzz_targets/my_target.rs"
test = false
doc = false
bench = false
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
# Time-boxed run against a persisted corpus
cargo +nightly-2026-09-01 fuzz run my_target fuzz/corpus/my_target \
  -- -max_total_time=300 -rss_limit_mb=2048 -timeout=10
```

### Fuzzing in CI

The nightly toolchain **MUST** be pinned by date, the corpus **MUST** be
persisted between runs, and crash artefacts **MUST** be uploaded.

**Why**: an unpinned `+nightly` makes the job fail on unrelated compiler
changes with no diff to explain it. A corpus that is discarded each run
restarts coverage exploration from zero, so a scheduled job repeatedly
re-finds shallow inputs and never reaches the deep ones. A crash that is not
uploaded cannot be reproduced.

```yaml
jobs:
  fuzz:
    runs-on: ubuntu-latest   # libFuzzer does not support Windows
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: dtolnay/rust-toolchain@6c977a6ca4077a0ceb28ffbe03f59d46e9ac8772 # v1
        with:
          toolchain: nightly-2026-09-01
      - uses: actions/cache@55cc8345863c7cc4c66a329aec7e433d2d1c52a9 # v6.1.0
        with:
          path: fuzz/corpus
          key: fuzz-corpus-${{ github.sha }}
          restore-keys: fuzz-corpus-
      - run: cargo install cargo-fuzz --version 0.13.2 --locked
      - run: |
          cargo fuzz run my_target fuzz/corpus/my_target \
            -- -max_total_time=300 -rss_limit_mb=2048
      - if: failure()
        uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7.0.1
        with:
          name: fuzz-artifacts
          path: fuzz/artifacts
```

### AFL.rs Alternative

For American Fuzzy Lop[^10]:

```bash
cargo install afl --version 0.18.2 --locked
cargo afl build
cargo afl fuzz -i in -o out target/debug/my_target
```

## Property Testing

Projects **SHOULD** state invariants as property tests where a round trip, an
ordering or an algebraic law can be expressed. proptest[^32] **SHOULD** be
used.

### Why

An example test asserts one point; a property test asserts a rule over a
generated domain and shrinks any counterexample to a minimal failing input,
which is usually the whole diagnosis. Round trips, idempotence and ordering
laws are the highest-value candidates because they hold for every input by
construction.

```toml
[dev-dependencies]
proptest = "1.11.0"  # proptest[^32]
```

```rust
// tests/props.rs
use proptest::prelude::*;

proptest! {
    #[test]
    fn render_then_parse_round_trips(values in prop::collection::vec(any::<u32>(), 0..32)) {
        let text = bench_props::render_list(&values);
        prop_assert_eq!(bench_props::parse_list(&text), Ok(values));
    }
}
```

Failing cases are written to `proptest-regressions/` and **MUST** be committed,
so the shrunk counterexample becomes a permanent regression test.

## Mutation Testing

Projects **SHOULD** run cargo-mutants[^33] to measure whether the test suite
actually detects changed behaviour.

### Why

Coverage says a line ran; it does not say an assertion would have failed had
that line been wrong. cargo-mutants replaces function bodies with plausible
alternatives and reports the ones the suite still passes with — a missed
mutant is a concrete, addressable gap.

```bash
cargo install cargo-mutants --version 27.1.0 --locked

cargo mutants --in-diff git.diff   # pull-request scope: only changed code
cargo mutants --package my_crate   # full run, scheduled
```

A full run is slow because it rebuilds and retests per mutant. Pull requests
**SHOULD** use `--in-diff`; whole-crate runs **SHOULD** be scheduled.

## Public API Compatibility

Library crates **MUST** check public API compatibility before publishing.
cargo-semver-checks[^34] **MUST** run in CI for every published library.

### Why

SemVer breakage in Rust is easy to introduce and hard to see in review: adding
a variant to a public enum, a field to a public struct, a method to a public
trait, or tightening a bound are all breaking, and none of them looks like a
removal in the diff. cargo-semver-checks compares the rustdoc JSON of the
working tree against the published version and names the rule that was
violated.

```bash
cargo install cargo-semver-checks --version 0.50.0 --locked

cargo semver-checks                             # against the latest release
cargo semver-checks --baseline-version 1.2.3    # against a specific version
```

```yaml
jobs:
  semver:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: dtolnay/rust-toolchain@6c977a6ca4077a0ceb28ffbe03f59d46e9ac8772 # v1
        with:
          toolchain: stable
      - run: cargo install cargo-semver-checks --version 0.50.0 --locked
      - run: cargo semver-checks
```

Version numbering policy is in the
[Versioning Guide](../../process/versioning.md).

## Benchmarking

Performance claims **MUST** be backed by a benchmark harness. Criterion[^35]
**SHOULD** be used.

### Why

`cargo bench` on stable has no built-in harness — `#[bench]` remains nightly
only — so a stable project without Criterion has no measurement at all.
Criterion runs a warm-up, collects a sample distribution, and reports a
confidence interval against the previous run, which distinguishes a real
regression from runner noise. A single wall-clock timing does not.

```toml
[dev-dependencies]
criterion = "0.8.2"  # Criterion[^35]

[[bench]]
name = "parse"
harness = false      # REQUIRED: Criterion supplies its own main
```

**Why `harness = false`**: without it Cargo links libtest's harness, which owns
`main`, and `criterion_main!` is never called. The benchmark target then builds
and runs zero benchmarks while reporting success.

```rust
// benches/parse.rs
use criterion::{Criterion, criterion_group, criterion_main};
use std::hint::black_box;

fn parse_benchmark(c: &mut Criterion) {
    let input = bench_props::render_list(&(0..256).collect::<Vec<_>>());
    c.bench_function("parse_list/256", |b| {
        b.iter(|| bench_props::parse_list(black_box(&input)));
    });
}

criterion_group!(benches, parse_benchmark);
criterion_main!(benches);
```

```bash
cargo bench                       # measure, compare against the last run
cargo bench -- --save-baseline pr # named baseline for a comparison run
```

## Test Performance

Test *throughput* and code *performance* are separate concerns and **MUST NOT**
be measured with the same tool. `--test-threads` changes libtest concurrency;
it does not measure anything.

### Why

`cargo test -- --test-threads=4` sets how many tests run at once. It produces
no timing, no distribution and no comparison, so quoting it as a performance
figure measures the runner's scheduling rather than the code. Worse, lowering
it is the standard workaround for tests that share global state, so a project
that treats the flag as a performance knob usually ends up hiding a real
isolation bug behind it. Suite wall-clock belongs to cargo-nextest[^11], which
runs tests in separate processes; code performance belongs to Criterion[^35],
which reports a confidence interval.

```bash
# Suite wall-clock: run tests in parallel processes
cargo nextest run --all-features

# Reduce interference for a flaky test, not a performance measurement
cargo test -- --test-threads=1

# Optimised build: relevant when the code under test is compute-bound
cargo test --release

# Compile tests without running them
cargo test --no-run
```

### Nextest

```bash
cargo install cargo-nextest --version 0.9.143 --locked
cargo nextest run --all-features
```

Nextest[^11] runs each test in its own process rather than its own thread, so
one test cannot corrupt another's global state, a panicking test cannot take
the runner down with it, and per-test timeouts and retries become possible.
Nextest does not run doc tests; `cargo test --doc` **MUST** still run
separately.

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

Loom[^15] **MUST** be declared as a `cfg(loom)` target dependency, the model
**MUST** use Loom's instrumented synchronisation types, and the test **MUST**
be run with `--cfg loom` set.

**Why**: Loom cannot observe `std::sync::atomic` or `std::thread`. It permutes
executions only through its own replacements, so a model written against the
standard types compiles, runs once, passes, and proves nothing. Declaring the
dependency under `[target.'cfg(loom)'.dependencies]` keeps Loom and its
tracing stack out of ordinary `cargo test` builds, and gating the test file on
`cfg(loom)` means a normal run reports "0 tests" rather than a false pass.
Nothing sets `--cfg loom` for you.[^15]

```toml
# Cargo.toml
[target.'cfg(loom)'.dependencies]
loom = "0.7.2"  # loom[^15]

[lints.rust]
unexpected_cfgs = { level = "warn", check-cfg = ['cfg(loom)'] }
```

**Why `check-cfg`**: `loom` is not a known cfg, so without this declaration
every `#[cfg(loom)]` raises an `unexpected_cfgs` warning, and under
`-D warnings` the ordinary build fails.

```rust
// tests/concurrent.rs
#![cfg(loom)]
#![allow(clippy::unwrap_used, reason = "loom model test")]

use loom::sync::Arc;
use loom::sync::atomic::AtomicUsize;
use loom::sync::atomic::Ordering::{Acquire, Relaxed, Release};
use loom::thread;

#[test]
fn increment_is_atomic() {
    loom::model(|| {
        let num = Arc::new(AtomicUsize::new(0));
        let threads: Vec<_> = (0..2)
            .map(|_| {
                let num = Arc::clone(&num);
                thread::spawn(move || {
                    num.fetch_add(1, Release);
                })
            })
            .collect();

        for t in threads {
            t.join().unwrap();
        }

        assert_eq!(2, num.load(Acquire));
        assert_eq!(2, num.load(Relaxed));
    });
}
```

```bash
# Loom runs nothing unless the cfg is set. --release keeps the permutation
# search tractable.
RUSTFLAGS="--cfg loom" cargo test --test concurrent --release
```

```rust
// BAD: std types, no cfg gate, plain `cargo test`. This runs the closure once,
// explores no interleavings, and passes whatever the code does.
#[test]
fn test_concurrent_safety() {
    loom::model(|| {
        let v1 = std::sync::Arc::new(std::sync::atomic::AtomicUsize::new(0));
        let v2 = v1.clone();
        std::thread::spawn(move || { v1.fetch_add(1, SeqCst); });
        v2.fetch_add(1, SeqCst);
    });
}
```

Loom does not implement the whole C11 model: `SeqCst` accesses are treated as
`AcqRel`, which can produce false alarms, and some load-buffering executions
are not explored, so a clean Loom run is not a proof.[^15]

## References

[^4]: [cargo-tarpaulin](https://github.com/xd009642/tarpaulin) - Code coverage tool for Rust; the default ptrace engine is Linux/x86-64 only
[^5]: [cargo-fuzz](https://github.com/rust-fuzz/cargo-fuzz) - Command-line wrapper for using libFuzzer
[^8]: [cargo-llvm-cov](https://github.com/taiki-e/cargo-llvm-cov) - Cargo subcommand for LLVM source-based code coverage
[^9]: [libFuzzer](https://llvm.org/docs/LibFuzzer.html) - Library for coverage-guided fuzz testing
[^10]: [AFL.rs](https://github.com/rust-fuzz/afl.rs) - Rust bindings for American Fuzzy Lop
[^11]: [cargo-nextest](https://nexte.st/) - Next-generation test runner for Rust
[^14]: [tokio](https://tokio.rs/) - Asynchronous runtime for Rust
[^15]: [loom](https://github.com/tokio-rs/loom) - Concurrency permutation testing tool
[^32]: [proptest](https://github.com/proptest-rs/proptest) - Hypothesis-style property testing with shrinking
[^33]: [cargo-mutants](https://github.com/sourcefrog/cargo-mutants) - Mutation testing for Rust
[^34]: [cargo-semver-checks](https://github.com/obi1kenobi/cargo-semver-checks) - Public API SemVer compliance checking
[^35]: [Criterion](https://github.com/criterion-rs/criterion.rs) - Statistics-driven benchmarking harness

## See Also

- [Rust Style Guide](../rust.md) - Toolchain, lints, formatting, dependencies and CI
- [Rust topic guides](README.md) - The other Rust topic guides
