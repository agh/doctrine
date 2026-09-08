# Async Runtimes

> [Doctrine](../../../README.md) > [Languages](../README.md) > [Rust](../rust.md) > Async Runtimes

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in
BCP 14 [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119)
[RFC 8174](https://datatracker.ietf.org/doc/html/rfc8174) when, and only
when, they appear in all capitals, as shown here.

This guide covers choosing and configuring an async runtime, Tokio feature
selection for applications and libraries, runtime-agnostic library design, and
the migration away from the discontinued async-std. The toolchain, lint,
formatting, dependency and CI rules in the [Rust Style Guide](../rust.md) apply
and are not repeated here; every version quoted is listed in its [Tested Version
Matrix](versions.md#tested-version-matrix) and was current on 8 September 2026.

Projects **SHOULD** use tokio[^14] as the default async runtime. Projects that
need a smaller runtime **SHOULD** use smol[^18]. async-std **MUST NOT** be used
in new code.

## Why Not async-std

async-std is discontinued. Its repository README opens with
"`async-std` has been discontinued; use `smol` instead", its maintainers
"recommend that all users of `async-std`, and all libraries built on
`async-std`, switch to `smol` instead", and the crates.io description of the
final release, 1.13.2, reads "Deprecated in favor of `smol`".[^18]

Existing code **SHOULD** migrate. The mapping is direct for the common cases:

| async-std | smol |
| --------- | ---- |
| `#[async_std::main]` | `fn main() { smol::block_on(async { ... }) }` |
| `#[async_std::test]` | `#[test]` + `smol::block_on` |
| `async_std::task::spawn` | `smol::spawn` |
| `async_std::future::timeout` | `smol::Timer::after` combined with `FutureExt::or` |
| `async_std::fs`, `async_std::net` | `smol::fs`, `smol::net` |

## Why tokio

- **Industry standard**: Most widely used async runtime with largest ecosystem
- **Feature-rich**: Built-in timers, I/O, sync primitives, and task scheduling
- **Performance**: Highly optimized work-stealing scheduler
- **Ecosystem**: Most async libraries (hyper, tonic, axum, sqlx) are built on tokio

## tokio Configuration

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

## smol Alternative

```toml
[dependencies]
smol = "2.0.2"  # smol[^18]
```

```rust
fn main() {
    let result = smol::block_on(async { fetch_data().await });
    println!("{result:?}");
}
```

smol has no attribute macros; the runtime is entered explicitly with
`smol::block_on`, which is also how a smol test is written.

## Runtime-Agnostic Code

A library is runtime-agnostic only when it names no runtime and links none.
Libraries **SHOULD** take the runtime capability they need as a parameter and
let the application supply it. Selecting a runtime with `cfg` **MUST NOT** be
described as runtime-agnostic.

**Why**: `#[cfg(feature = "tokio")] tokio::time::timeout(..)` is a compile-time
choice between two hard-coded runtimes. The crate still depends on one of them,
still fails to build when neither feature is on, and a caller running a third
executor — `async-global-executor`, `glommio`, an embedded one — cannot use it
at all. Injecting the capability inverts that: the library depends on neither
runtime, so every executor works, including ones that did not exist when the
library was written, and tests need no runtime at all.

```toml
# Cargo.toml — the library depends on no runtime. futures-lite supplies future
# combinators only; it contains no executor.
[dependencies]
futures-lite = { version = "2.6.1", default-features = false, features = ["alloc"] }

# Optional convenience implementations, off by default.
[features]
default = []
tokio = ["dep:tokio"]
smol = ["dep:smol"]

[dependencies.tokio]
version = "1.53.1"
default-features = false
features = ["rt", "time"]
optional = true

[dependencies.smol]
version = "2.0.2"
optional = true
```

`cargo tree -e normal` on the default build shows the whole dependency set:

```text
asyncrt v0.1.0
└── futures-lite v2.6.1
    ├── futures-core v0.3.34
    └── pin-project-lite v0.2.17
```

No runtime appears, which is the property "runtime-agnostic" names.

```rust
// GOOD: the capability is a parameter. This compiles and passes its tests
// with no runtime feature enabled at all.
use std::future::Future;
use std::time::Duration;

/// The one capability this library needs from a runtime.
///
/// Implemented by the application, which has already chosen an executor. This
/// crate names no runtime and links none.
pub trait Timer {
    fn sleep(&self, duration: Duration) -> impl Future<Output = ()> + Send;
}

/// Runs `future`, giving up after `timeout`.
///
/// # Errors
///
/// Returns [`TimeoutError`] when `future` has not completed within `timeout`.
pub async fn with_timeout<T, K, F>(
    timer: &K,
    timeout: Duration,
    future: F,
) -> Result<T, TimeoutError>
where
    K: Timer + Sync,
    F: Future<Output = T>,
{
    use futures_lite::FutureExt as _;

    let work = async move { Ok(future.await) };
    let expiry = async move {
        timer.sleep(timeout).await;
        Err(TimeoutError)
    };
    work.or(expiry).await
}
```

Convenience implementations **MAY** ship behind optional features, so that the
common cases need no boilerplate, while the core path stays independent:

```rust
/// Tokio implementation, behind the optional `tokio` feature.
#[cfg(feature = "tokio")]
#[derive(Debug, Clone, Copy, Default)]
pub struct TokioTimer;

#[cfg(feature = "tokio")]
impl Timer for TokioTimer {
    fn sleep(&self, duration: Duration) -> impl Future<Output = ()> + Send {
        tokio::time::sleep(duration)
    }
}

/// smol implementation, behind the optional `smol` feature.
#[cfg(feature = "smol")]
#[derive(Debug, Clone, Copy, Default)]
pub struct SmolTimer;

#[cfg(feature = "smol")]
impl Timer for SmolTimer {
    // `async fn` satisfies the trait's `-> impl Future` signature.
    async fn sleep(&self, duration: Duration) {
        smol::Timer::after(duration).await;
    }
}
```

Because the capability is injected, the tests need neither runtime nor
wall-clock time, and both outcomes are exercised deterministically:

```rust
    /// A deterministic Timer: no runtime, no wall-clock sleeping.
    struct Immediate;

    impl Timer for Immediate {
        fn sleep(&self, _duration: Duration) -> impl Future<Output = ()> + Send {
            std::future::ready(())
        }
    }

    /// A Timer that never fires, so the work future always wins.
    struct Never;

    impl Timer for Never {
        fn sleep(&self, _duration: Duration) -> impl Future<Output = ()> + Send {
            std::future::pending()
        }
    }

    #[tokio::test]
    async fn completes_before_the_deadline() {
        let out = with_timeout(&Never, Duration::from_secs(30), async { 7_u8 }).await;
        assert_eq!(out, Ok(7));
    }

    #[tokio::test]
    async fn expires_when_the_timer_fires_first() {
        let out: Result<u8, _> =
            with_timeout(&Immediate, Duration::ZERO, std::future::pending()).await;
        assert_eq!(out, Err(TimeoutError));
    }
```

```rust
// BAD: labelled runtime-agnostic, but it names two runtimes and links one.
// A caller on async-global-executor or glommio cannot use it, and with no
// feature enabled it does not build.
#[cfg(feature = "tokio")]
pub async fn process_with_timeout<F, T>(future: F, timeout: Duration)
    -> Result<T, TimeoutError>
where
    F: Future<Output = T>,
{
    tokio::time::timeout(timeout, future).await.map_err(|_| TimeoutError)
}
```

## Selecting a Backend with cfg

Where a library genuinely must call runtime-specific APIs — spawning, file or
socket I/O — injection is not enough and a `cfg` selection is the remaining
option. Such a crate is *multi-runtime*, not runtime-agnostic, and **MUST** say
so. Every `cfg` configuration **MUST** then produce a return path, and the
backends **MUST** have a documented precedence.

**Why**: Cargo features are additive, so a workspace, a transitive dependency
or `--all-features` can enable both backends at once. Arms written as mutually
exclusive alternatives are then both compiled, and the first `return` silently
wins. With neither feature enabled the body evaluates to `()` and the function
fails to compile with a type error that never names the missing feature.

```rust
// GOOD: an explicit failure when no backend is selected, and a stated
// precedence when both are. Note the name: this is multi-runtime.
#[cfg(not(any(feature = "tokio", feature = "smol")))]
compile_error!("enable the `tokio` or `smol` feature to pick a backend");

#[cfg(any(feature = "tokio", feature = "smol"))]
pub fn spawn_detached<F>(future: F)
where
    F: Future<Output = ()> + Send + 'static,
{
    // Cargo features are additive, so both backends can be enabled at once.
    // tokio takes precedence; the smol arm is then compiled out.
    #[cfg(feature = "tokio")]
    {
        tokio::spawn(future);
    }

    #[cfg(all(feature = "smol", not(feature = "tokio")))]
    {
        smol::spawn(future).detach();
    }
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

    #[cfg(feature = "smol")]
    return smol_timeout(timeout, future).await;
}
```

## Spawning Tasks

A `JoinHandle` resolves to `Result<T, JoinError>`. Production code **MUST**
handle that error rather than unwrapping it.

**Why**: `JoinError` means the task panicked or was cancelled. Unwrapping it
turns one task's panic into the caller's panic, which in an `async fn` running
on a shared runtime takes down the request that happened to be awaiting it and
loses the original panic message.

```rust
// `tokio::spawn`, `spawn_blocking` and `LocalSet` require the `rt` feature.
use tokio::task::{self, JoinError};

/// # Errors
///
/// Returns [`JoinError`] when the spawned task panicked or was cancelled.
async fn run_off_thread() -> Result<Output, JoinError> {
    // Spawn async task on the runtime
    let handle = tokio::spawn(async { expensive_async_operation().await });
    let from_async = handle.await?;

    // Spawn blocking task (for CPU-intensive or synchronous code)
    let from_blocking = task::spawn_blocking(expensive_sync_operation).await?;

    Ok(combine(from_async, from_blocking))
}

// Local tasks (for !Send futures)
let local = task::LocalSet::new();
local
    .run_until(async {
        task::spawn_local(async {
            // Can use !Send types here
        })
        .await
    })
    .await?;
```

```rust
// BAD: denied by `clippy::unwrap_used`, and converts a background panic into a
// panic in whichever task happened to await the handle.
let result = handle.await.unwrap();
```

## Async Testing

Test snippets in this guide assume the scoped allowance from
[Recommended Lint Groups](../rust.md#recommended-lint-groups); `unwrap` in a test is a
deliberate, narrowly scoped exception, not a relaxation of the crate policy.

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
// `rt-multi-thread`. A test that returns `Result` can use `?` instead.
#[test]
fn test_with_custom_runtime() -> Result<(), Box<dyn std::error::Error>> {
    let rt = tokio::runtime::Builder::new_multi_thread()
        .worker_threads(2)
        .enable_all()
        .build()?;

    rt.block_on(async {
        // Test async code
    });
    Ok(())
}
```

## References

[^14]: [tokio](https://tokio.rs/) - Asynchronous runtime for Rust
[^18]: [smol](https://github.com/smol-rs/smol) - Small and fast async runtime; the maintainer-nominated successor to [async-std](https://github.com/async-rs/async-std)

## See Also

- [Rust Style Guide](../rust.md) - Toolchain, lints, formatting, dependencies and CI
- [Rust topic guides](README.md) - The other Rust topic guides
