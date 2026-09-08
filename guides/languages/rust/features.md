# Cargo Features

> [Doctrine](../../../README.md) > [Languages](../README.md) > [Rust](../rust.md) > Cargo Features

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in
BCP 14 [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119)
[RFC 8174](https://datatracker.ietf.org/doc/html/rfc8174) when, and only
when, they appear in all capitals, as shown here.

This guide covers Cargo features as additive conditional compilation: declaring
them, testing every combination, feature unification, and what they are not
(runtime A/B switches). The toolchain, lint, formatting, dependency and CI rules
in the [Rust Style Guide](../rust.md) apply and are not repeated here; every
version quoted is listed in its [Tested Version
Matrix](versions.md#tested-version-matrix) and was current on 8 September 2026.

Cargo features are **additive compile-time configuration**. They **MUST NOT**
be used for A/B testing, staged rollout or any experiment whose cohort is
decided per request. Runtime experiments **MUST** use runtime configuration.

## Why

A Cargo feature is resolved when the binary is built and is the same for every
user of that binary, so an "experiment" behind a feature requires a rebuild and
a redeploy to change cohort, and cannot be turned off without one. Features are
also *unioned*, not selected: if any crate in the graph, any
`--all-features` invocation, or feature unification across a workspace enables
`variant-b`, it is enabled for everyone. That is the opposite of what an
experiment needs.[^49] A feature that turns something *off* is a further
mistake, because a dependency enabling the feature can never be countermanded;
express the choice as an additive `no-foo`-free positive feature instead.

| Requirement | Mechanism |
| ----------- | --------- |
| Optional dependency or platform backend | Cargo feature |
| API surface that some consumers do not compile | Cargo feature |
| Per-request or per-user cohort | Runtime configuration |
| Kill switch that must work without redeploy | Runtime configuration |
| Gradual rollout by percentage | Runtime configuration |

```rust
// GOOD: a runtime experiment. Cohort assignment is data, not a build flag.
pub struct Experiments {
    rollout_percent: u8,
}

impl Experiments {
    #[must_use]
    pub fn use_new_ranker(&self, user_id: u64) -> bool {
        u8::try_from(user_id % 100).is_ok_and(|bucket| bucket < self.rollout_percent)
    }
}
```

```toml
# BAD: an experiment as a Cargo feature. Changing cohort means a rebuild, and
# any crate in the graph can switch it on for everybody.
[features]
new-ranker = []
```

## Feature Flags via Cargo Features

```toml
# Cargo.toml — additive, positive names, one dialect selected explicitly
[features]
default = ["postgres"]
postgres = []
sqlite = []
```

Overlapping features **MUST** have an explicit, documented precedence, and
every `cfg` arm **MUST** be reachable in exactly one configuration.

**Why**: Cargo features are additive. A dependency, `--all-features`, or
feature unification across a workspace can enable `postgres` and `sqlite`
together. Writing `#[cfg(feature = "postgres")]` against
`#[cfg(not(feature = "postgres"))]` in the implementation while the test
asserts on `postgres` and `sqlite` independently makes both assertions
compile at once, and `cargo test --all-features` fails with
`left: "$1", right: "?"`.

```rust
// GOOD: postgres takes precedence over sqlite; neither is a build error.
#[cfg(feature = "postgres")]
#[must_use]
pub fn placeholder(index: usize) -> String {
    format!("${index}")
}

#[cfg(all(feature = "sqlite", not(feature = "postgres")))]
#[must_use]
pub fn placeholder(_index: usize) -> String {
    "?".to_owned()
}

#[cfg(not(any(feature = "postgres", feature = "sqlite")))]
compile_error!("enable the `postgres` or `sqlite` feature to select a dialect");

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn placeholder_matches_the_selected_dialect() {
        // Exactly one arm is compiled in, mirroring the precedence above.
        #[cfg(feature = "postgres")]
        assert_eq!(placeholder(1), "$1");

        #[cfg(all(feature = "sqlite", not(feature = "postgres")))]
        assert_eq!(placeholder(1), "?");
    }
}
```

```rust
// BAD: with both features enabled, both assertions compile and contradict.
#[test]
fn placeholder_matches_the_selected_dialect() {
    let result = placeholder(1);  // "$1"

    #[cfg(feature = "postgres")]
    assert_eq!(result, "$1");

    #[cfg(feature = "sqlite")]
    assert_eq!(result, "?");  // fails under --all-features
}
```

## Feature Unification

A feature enabled anywhere in the graph is enabled for the whole build of that
crate. Libraries **MUST NOT** rely on a feature being off, and **MUST**
document which combinations are supported.

**Why**: if crate A depends on `my_crate` with `sqlite` and crate B depends on
`my_crate` with `postgres`, Cargo builds one `my_crate` with both. Code written
on the assumption that the two are alternatives is compiled with both enabled
and takes whichever arm is written first. Testing only the default feature set
never exercises that build.

## Feature Matrix in CI

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
          - ""                                       # default
          - "--all-features"                         # unified: both dialects
          - "--no-default-features --features sqlite"
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: dtolnay/rust-toolchain@6c977a6ca4077a0ceb28ffbe03f59d46e9ac8772 # v1
        with:
          toolchain: stable
      - run: cargo test ${{ matrix.features }}
```

`--no-default-features` on its own is deliberately absent: this crate has no
supported no-dialect build and says so with `compile_error!`. A matrix
**MUST** list only combinations the crate claims to support.

## Conditional Compilation with cfg Attributes

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
    // Assert the value, not merely that one exists. `!is_empty()` passes for
    // every arm, including a macOS build that wrongly returns "Windows".
    #[cfg(target_os = "linux")]
    assert_eq!(platform_specific(), "Linux");

    #[cfg(target_os = "macos")]
    assert_eq!(platform_specific(), "macOS");

    #[cfg(target_os = "windows")]
    assert_eq!(platform_specific(), "Windows");
}

// Testing multiple feature combinations
#[test]
#[cfg(all(feature = "postgres", not(feature = "sqlite")))]
fn placeholder_is_postgres_only() {
    // Only runs when postgres is enabled but sqlite is not
    assert_eq!(placeholder(1), "$1");
}
```

A `cfg`-gated test **MUST** assert the value the selected arm is supposed to
produce, not merely that some value exists.

**Why**: `assert!(!result.is_empty())` holds for every arm, so it cannot
distinguish a correct implementation from one whose arms are swapped. Copying
the `"Windows"` body into the `target_os = "macos"` arm keeps that test green
on a macOS runner; the value assertion above fails it with
`left: "Windows", right: "macOS"`. The same applies to feature-gated tests:
mirror the precedence in the assertions so exactly one is compiled and it names
the expected result.

## References

[^49]: [Cargo features](https://doc.rust-lang.org/cargo/reference/features.html) - Feature unification and additive semantics

## See Also

- [Rust Style Guide](../rust.md) - Toolchain, lints, formatting, dependencies and CI
- [Rust topic guides](README.md) - The other Rust topic guides
