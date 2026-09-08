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

## Common Trait Implementations

Types **MUST** eagerly implement common traits. Rust's orphan rule means a
downstream crate cannot supply the implementation you left out.

### Why This Matters

- **Orphan rule**: a crate may implement a trait for a type only if it owns the
  trait or the type. If your crate publishes `Config` and a user wants
  `Display` for it, the user owns neither `Display` nor `Config` and cannot
  write that implementation at all; the vendored reference works the same
  example through with `webapp`, `url::Url` and `Display`.[^37]
- **You keep the ability, at a cost**: the defining crate *can* add
  implementations later, but adding one is a compatibility event — inherent
  method resolution, inference and downstream blanket implementations can all
  change — so adding `Debug` in 0.4 is not free either.
- **Ecosystem compatibility**: types without `Debug` cannot be used in `Result`
  error positions, and `#[derive(Debug)]` on a struct fails if any field is not
  `Debug`, so one missing implementation propagates outwards.
- **User expectations**: Rust developers expect types to be debuggable,
  cloneable and comparable.

```rust
// GOOD: derive the full set up front. Users who need `Display` for their own
// wrapper can newtype it, but they will never need to.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct CacheKey {
    namespace: String,
    id: u64,
}
```

```rust
// BAD: downstream cannot fix this. `impl Debug for CacheKey` in a user's crate
// is rejected: "only traits defined in the current crate can be implemented
// for types defined outside of the crate".
pub struct CacheKey {
    namespace: String,
    id: u64,
}
```

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

## API Design and Documentation

Public APIs **MUST** follow the Rust API Guidelines. Doctrine vendors the full
text under [`reference/rust/`](../../reference/rust/checklist.md); this section
carries the rules that apply to every crate and links to the detailed page for
each one.

### Why

The guidelines encode what the standard library and the wider ecosystem already
do. A crate that deviates costs its users on every call: they guess the wrong
method name, cannot find the error conditions, and discover breaking changes at
upgrade time. Following them is also cheaper than fixing them later, because
most are unfixable after 1.0 without a major version.

### Naming

Names **MUST** follow RFC 430 casing and the standard conversion prefixes.[^38]

| Convention | Rule | Example |
| ---------- | ---- | ------- |
| Casing (C-CASE) | `UpperCamelCase` types, `snake_case` values, `SCREAMING_SNAKE_CASE` constants | `struct CacheKey`, `fn parse_retries`, `const MAX_RETRIES` |
| Conversions (C-CONV) | `as_` borrowed, `to_` expensive, `into_` owned | `as_str`, `to_owned`, `into_bytes` |
| Getters (C-GETTER) | No `get_` prefix except for a single obvious accessor | `fn timeout(&self)`, not `fn get_timeout(&self)` |
| Iterators (C-ITER) | `iter`, `iter_mut`, `into_iter` | `fn iter(&self) -> Iter<'_, T>` |
| Iterator types (C-ITER-TY) | Type name matches the method | `iter()` returns `Iter` |
| Features (C-FEATURE) | No placeholder words | `serde`, not `use-serde` or `with-serde` |
| Word order (C-WORD-ORDER) | Consistent across the crate | `SocketAddrV4`/`SocketAddrV6`, not `V4SocketAddr` |

```rust
// GOOD: the prefix states the cost, and the getter has no `get_`.
impl Config {
    pub fn timeout(&self) -> Duration { self.timeout }
    pub fn as_str(&self) -> &str { &self.name }
    pub fn into_parts(self) -> (String, Duration) { (self.name, self.timeout) }
}
```

```rust
// BAD: `get_` prefix, and `to_parts` implies a cheap borrow of an owned value.
impl Config {
    pub fn get_timeout(&self) -> Duration { self.timeout }
    pub fn to_parts(self) -> (String, Duration) { (self.name, self.timeout) }
}
```

### Documentation

Every public item **MUST** carry rustdoc. Documentation **MUST** state error,
panic and safety conditions, and examples **MUST** use `?` rather than
`unwrap`.[^39]

```rust
/// Converts a port number, rejecting values outside the `u16` range.
///
/// # Errors
///
/// Returns [`PortRangeError`] when `value` exceeds `u16::MAX`.
///
/// # Examples
///
/// ```
/// use core_api::PortNumber;
///
/// let port = PortNumber::try_from(8080_u32)?;
/// assert_eq!(u16::from(port), 8080);
/// # Ok::<(), core_api::PortRangeError>(())
/// ```
fn try_from(value: u32) -> Result<Self, Self::Error> {
    u16::try_from(value).map(Self).map_err(|_| PortRangeError(value))
}
```

```rust
// BAD: no `# Errors`, and the example panics instead of propagating. A reader
// cannot tell what makes this fail, and `cargo test --doc` proves nothing
// about the error path.
/// Converts a port number.
///
/// ```
/// let port = PortNumber::try_from(8080u32).unwrap();
/// ```
```

Doc examples are tests. `cargo test --doc` **MUST** run in CI, so an example
that stops compiling fails the build rather than rotting in place.

Manifests **MUST** carry the full metadata set (C-METADATA): `description`,
`license`, `repository`, `documentation`, `homepage`, `keywords`, `categories`.
Items that are public only for macro expansion **MUST** be hidden with
`#[doc(hidden)]` (C-HIDDEN).

### Future-Proofing

| Rule | Mechanism |
| ---- | --------- |
| Sealed traits (C-SEALED) | Private supertrait blocks downstream implementations |
| Private fields (C-STRUCT-PRIVATE) | Accessors instead of public fields |
| Extensible enums and structs | `#[non_exhaustive]` |
| Encapsulation (C-NEWTYPE-HIDE) | Newtype over the concrete iterator or error |
| No duplicated bounds (C-STRUCT-BOUNDS) | Bound the `impl`, not the struct |

```rust
// GOOD: sealed. New methods on `Format` are not a breaking change, because
// nobody outside this crate can implement it.
mod sealed {
    pub trait Sealed {}
}

pub trait Format: sealed::Sealed {
    /// File extension, without the leading dot.
    fn extension(&self) -> &'static str;
}

pub struct Json;
impl sealed::Sealed for Json {}
impl Format for Json {
    fn extension(&self) -> &'static str { "json" }
}
```

```rust
// GOOD: adding a field later is a minor release, because downstream cannot
// construct or exhaustively destructure this type.
#[non_exhaustive]
pub struct Request {
    pub path: String,
    pub headers: HashMap<String, String>,
}
```

```rust
// BAD: every field is public and the struct is exhaustive, so adding
// `query: String` breaks every `Request { path, headers }` pattern downstream.
pub struct Request {
    pub path: String,
    pub headers: HashMap<String, String>,
}
```

### Dyn Compatibility

Traits that **MAY** usefully be used as `dyn Trait` **MUST** stay dyn-compatible
(the property formerly called object safety): no generic methods, no `Self`
return by value, no `Self: Sized` supertrait.[^40] Where both are wanted,
provide the generic API as a blanket extension over the dyn-compatible core.

```rust
// GOOD: dyn-compatible core, generics moved to a free function.
pub trait Sink {
    fn write_line(&mut self, line: &str) -> std::io::Result<()>;
}

pub fn write_all<S: Sink + ?Sized>(sink: &mut S, lines: &[&str]) -> std::io::Result<()> {
    lines.iter().try_for_each(|line| sink.write_line(line))
}

pub fn make(boxed: Box<dyn Sink>) -> Box<dyn Sink> { boxed }
```

```rust
// BAD: the generic method makes `dyn Sink` impossible:
// "the trait `Sink` is not dyn compatible".
pub trait Sink {
    fn write_all<I: IntoIterator<Item = &'static str>>(&mut self, lines: I);
}
```

### Type Safety

Arguments **MUST** convey meaning through types rather than bare `bool` or
`Option` (C-CUSTOM-TYPE), and newtypes **SHOULD** be used to make distinct
quantities distinct (C-NEWTYPE).[^41]

```rust
// GOOD: unmistakable at the call site.
pub enum Overwrite { Yes, No }
pub fn save(path: &Path, overwrite: Overwrite) -> io::Result<()> { /* ... */ }

save(path, Overwrite::Yes)?;
```

```rust
// BAD: `save(path, true, false)` is unreadable and silently swappable.
pub fn save(path: &Path, overwrite: bool, fsync: bool) -> io::Result<()> { /* ... */ }
```

The full checklist, including predictability, dependability and debuggability
rules not repeated here, is in
[`reference/rust/checklist.md`](../../reference/rust/checklist.md).

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
edition = "2024"        # REQUIRED: an omitted edition defaults to 2015
rust-version = "1.94.0"

[lib]
proc-macro = true

[dependencies]
syn = { version = "3.0.5", features = ["full"] }     # syn[^21]
quote = "1.0.47"                                      # quote[^22]
proc-macro2 = "1.0.107"                               # proc-macro2[^23]
```

Every crate manifest **MUST** declare `package.edition`.

**Why**: Cargo defaults an omitted `edition` to 2015, where `use quote::quote;`
and `use syn::...;` do not resolve without an `extern crate` declaration. The
macro crate above fails to compile with "error[E0432]: unresolved import
quote" until the edition is declared.[^27]

### Migrating from syn 2 to syn 3

New macro crates **MUST** use syn 3. syn 3.0.0 reshaped the syntax tree to
absorb three years of language evolution: `Type::BareFn` became `Type::FnPtr`,
`Signature::unsafety` became a three-way `Safety` enum, `Arm::guard` moved to a
`Pat::Guard` variant, and ten new non-exhaustive `*Modifiers` structs were
added to reserve room for future syntax.[^42]

Macros **MUST** round-trip parsed items rather than reassembling them field by
field.

**Why**: field-by-field reassembly drops whatever the macro does not name, and
breaks outright when a syntax tree node gains a field. Destructuring
`syn::ItemFn` exhaustively against syn 3 fails with
"error[E0027]: pattern does not mention field `modifiers`"; the same code
written against syn 2 compiled, and silently discarded any modifier syntax the
node did not yet model.

```rust
// GOOD: mutate the parsed item and print it back. Attributes, visibility,
// generics, `async`, `const`, `unsafe` and modifiers all survive untouched.
let mut func = parse_macro_input!(item as ItemFn);
let body = &func.block;
let wrapped: Block = parse_quote! {{ /* ... */ #body }};
*func.block = wrapped;
quote! { #func }
```

```rust
// BAD: names four of the five fields. Rejected by syn 3, and lossy under
// syn 2.
let ItemFn { attrs, vis, sig, block } = parse_macro_input!(item as ItemFn);
quote! { #(#attrs)* #vis #sig { /* ... */ #block } }
```

Where a macro must reject syntax it does not understand, call
`.require_empty()` on the relevant `*Modifiers` value: it returns a spanned
error naming the unsupported construct instead of silently ignoring it.[^42]

### Derive Macro Example

A derive macro **MUST** handle every shape of the item it accepts — named,
tuple and unit structs, and generics — or reject the rest with a spanned
error. It **MUST NOT** `panic!`.

**Why**: `panic!` in a proc macro surfaces as
"error: proc-macro derive panicked" pointing at the derive attribute, with the
message relegated to a note and no span for the offending item. A returned
`syn::Error` points at the token that is wrong. Ignoring tuple and unit structs
is worse than rejecting them: `#[derive(Builder)]` on a tuple struct silently
generates a builder whose `build()` cannot name any field, and the failure
appears deep inside the expansion.

```rust
// my_macro/src/lib.rs
use proc_macro::TokenStream;
use proc_macro2::Span;
use quote::{format_ident, quote};
use syn::spanned::Spanned;
use syn::{
    Block, Data, DeriveInput, Error, Fields, Ident, ItemFn, Result, Type, parse_macro_input,
    parse_quote,
};

#[proc_macro_derive(Builder)]
pub fn derive_builder(input: TokenStream) -> TokenStream {
    let input = parse_macro_input!(input as DeriveInput);
    expand_builder(&input)
        .unwrap_or_else(Error::into_compile_error)
        .into()
}

struct Field {
    /// `None` for a tuple struct: the accessor is positional.
    ident: Option<Ident>,
    setter: Ident,
    ty: Type,
}

fn collect_fields(data: &Data) -> Result<Vec<Field>> {
    let fields = match data {
        Data::Struct(s) => &s.fields,
        Data::Enum(e) => {
            return Err(Error::new(e.enum_token.span, "Builder supports structs only"));
        }
        Data::Union(u) => {
            return Err(Error::new(u.union_token.span, "Builder supports structs only"));
        }
    };
    let out = match fields {
        Fields::Named(named) => named
            .named
            .iter()
            .map(|f| {
                let ident = f.ident.clone().ok_or_else(|| {
                    Error::new(f.span(), "named field without an identifier")
                })?;
                Ok(Field { setter: ident.clone(), ident: Some(ident), ty: f.ty.clone() })
            })
            .collect::<Result<Vec<_>>>()?,
        Fields::Unnamed(unnamed) => unnamed
            .unnamed
            .iter()
            .enumerate()
            .map(|(i, f)| Field {
                ident: None,
                setter: format_ident!("field_{i}", span = f.span()),
                ty: f.ty.clone(),
            })
            .collect(),
        Fields::Unit => Vec::new(),
    };
    Ok(out)
}

fn expand_builder(input: &DeriveInput) -> Result<proc_macro2::TokenStream> {
    let name = &input.ident;
    let builder = format_ident!("{name}Builder");
    let error = format_ident!("{name}BuilderError");
    let fields = collect_fields(&input.data)?;
    let (impl_generics, ty_generics, where_clause) = input.generics.split_for_impl();

    let decls = fields.iter().map(|f| {
        let (setter, ty) = (&f.setter, &f.ty);
        quote! { #setter: ::core::option::Option<#ty> }
    });
    let inits = fields.iter().map(|f| {
        let setter = &f.setter;
        quote! { #setter: ::core::option::Option::None }
    });
    let setters = fields.iter().map(|f| {
        let (setter, ty) = (&f.setter, &f.ty);
        quote! {
            pub fn #setter(mut self, value: #ty) -> Self {
                self.#setter = ::core::option::Option::Some(value);
                self
            }
        }
    });
    let takes = fields.iter().map(|f| {
        let setter = &f.setter;
        let label = setter.to_string();
        let value = quote! {
            self.#setter.ok_or(#error { field: #label })?
        };
        match &f.ident {
            Some(ident) => quote! { #ident: #value },
            None => value,
        }
    });
    let ctor = match fields.first().map(|f| f.ident.is_some()) {
        Some(true) => quote! { #name { #(#takes,)* } },
        Some(false) => quote! { #name(#(#takes,)*) },
        None => quote! { #name },
    };

    Ok(quote! {
        /// Error returned when a required field was never set.
        #[derive(Debug, Clone, Copy, PartialEq, Eq)]
        pub struct #error {
            /// Name of the field that was left unset.
            pub field: &'static str,
        }

        impl ::core::fmt::Display for #error {
            fn fmt(&self, f: &mut ::core::fmt::Formatter<'_>) -> ::core::fmt::Result {
                ::core::write!(f, "missing field: {}", self.field)
            }
        }

        impl ::core::error::Error for #error {}

        pub struct #builder #impl_generics #where_clause {
            #(#decls,)*
        }

        impl #impl_generics #builder #ty_generics #where_clause {
            #[must_use]
            pub fn new() -> Self {
                Self { #(#inits,)* }
            }

            #(#setters)*

            pub fn build(self) -> ::core::result::Result<#name #ty_generics, #error> {
                ::core::result::Result::Ok(#ctor)
            }
        }

        impl #impl_generics ::core::default::Default for #builder #ty_generics #where_clause {
            fn default() -> Self {
                Self::new()
            }
        }

        impl #impl_generics #name #ty_generics #where_clause {
            #[must_use]
            pub fn builder() -> #builder #ty_generics {
                #builder::new()
            }
        }
    })
}
```

### Attribute Macro Example

An attribute macro **MUST** preserve the item it decorates: attributes,
visibility, generics, `async` and `where` clauses. Wrapping a body in a
closure **MUST NOT** be used.

**Why**: `let result = (|| { #body })();` changes the meaning of the function.
`?` and `return` inside the body then leave the closure rather than the
function, `.await` is rejected because the closure is not `async`, and the
closure captures `self` by inference. Assigning the block back onto the parsed
`ItemFn` keeps the original control flow, and a `Drop` guard logs the exit on
every path including `?` and early `return`.

```rust
// my_macro/src/lib.rs
#[proc_macro_attribute]
pub fn log_calls(attr: TokenStream, item: TokenStream) -> TokenStream {
    if !attr.is_empty() {
        let span = proc_macro2::TokenStream::from(attr).span();
        return Error::new(span, "log_calls takes no arguments")
            .into_compile_error()
            .into();
    }
    // Mutate the parsed item and print it back. Reassembling the pieces by
    // hand silently drops anything the macro does not name.
    let mut func = parse_macro_input!(item as ItemFn);
    let name = func.sig.ident.to_string();
    let body = &func.block;
    let wrapped: Block = parse_quote! {{
        struct __LogExit(&'static str);
        impl ::core::ops::Drop for __LogExit {
            fn drop(&mut self) {
                ::std::println!("[EXIT] {}", self.0);
            }
        }
        let __log_exit = __LogExit(#name);
        ::std::println!("[ENTER] {}", #name);
        #body
    }};
    *func.block = wrapped;
    quote! { #func }.into()
}
```

### Function-like Macro Example

A macro **MUST** validate only what its documentation and its error message
claim. A prefix check is a prefix check, not SQL validation.

**Why**: naming a macro `sql!` and checking `starts_with("SELECT")` promises
compile-time SQL checking and delivers none: `sql!(SELECT nonexistent FROM
missing)` is accepted. If compile-time SQL verification is the goal, use SQLx's
checked macros against a real schema; see
[Data Integrity Testing](#sqlx-compile-time-checked-queries).

```rust
// my_macro/src/lib.rs
#[proc_macro]
pub fn select(input: TokenStream) -> TokenStream {
    let tokens = proc_macro2::TokenStream::from(input);
    let leading = tokens.clone().into_iter().next();
    let ok = matches!(
        &leading,
        Some(proc_macro2::TokenTree::Ident(i)) if i.to_string().eq_ignore_ascii_case("select")
    );
    if !ok {
        let span = leading.map_or_else(Span::call_site, |t| t.span());
        return Error::new(span, "select! accepts SELECT statements only")
            .into_compile_error()
            .into();
    }
    let text = tokens.to_string();
    quote! { #text }.into()
}
```

### Using the Macros

```rust
// src/lib.rs — the consumer crate
pub use my_macro::{Builder, log_calls, select};

#[derive(Builder, Debug, PartialEq, Eq)]
pub struct Config {
    pub host: String,
    pub port: u16,
}

#[derive(Builder, Debug, PartialEq, Eq)]
pub struct Pair<T>(pub T, pub T)
where
    T: Clone;

#[derive(Builder, Debug, PartialEq, Eq)]
pub struct Marker;

#[log_calls]
pub fn double(x: i32) -> i32 {
    x * 2
}

#[log_calls]
pub async fn fetch(id: u64) -> Result<u64, ConfigBuilderError> {
    if id == 0 {
        return Err(ConfigBuilderError { field: "id" });
    }
    Ok(id)
}

pub const QUERY: &str = select!(SELECT * FROM users WHERE id = 1);
```

### Testing Procedural Macros

```rust
// tests/builder.rs
#![allow(clippy::unwrap_used, clippy::expect_used, clippy::panic)]

use macro_user::{Config, Marker, Pair};

#[test]
fn named_struct_builds() {
    let config = Config::builder()
        .host("localhost".into())
        .port(8080)
        .build()
        .expect("all fields set");
    assert_eq!(config.host, "localhost");
    assert_eq!(config.port, 8080);
}

#[test]
fn missing_field_names_itself() {
    let err = Config::builder().host("localhost".into()).build().unwrap_err();
    assert_eq!(err.field, "port");
}

#[test]
fn tuple_struct_builds_positionally() {
    let pair = Pair::builder().field_0(1u8).field_1(2u8).build().expect("both set");
    assert_eq!(pair, Pair(1, 2));
}

#[test]
fn unit_struct_builds() {
    assert_eq!(Marker::builder().build().expect("no fields"), Marker);
}

#[test]
fn attribute_macro_preserves_async_and_early_return() {
    let rt = std::thread::spawn(|| {
        futures_lite::future::block_on(async { macro_user::fetch(7).await })
    })
    .join()
    .expect("thread");
    assert_eq!(rt.expect("id 7 is accepted"), 7);
    assert_eq!(macro_user::double(21), 42);
    assert_eq!(macro_user::QUERY, "SELECT * FROM users WHERE id = 1");
}
```

### Compile-fail Tests with trybuild

Compile-fail fixtures **MUST** ship the expected `.stderr`.

**Why**: without a golden file, `trybuild` records whatever the macro currently
prints and passes. The test then asserts only that compilation failed, not that
it failed for the stated reason, so a macro that starts rejecting valid input
still passes. Generate the goldens once with `TRYBUILD=overwrite cargo test`
and review them like any other source.

```toml
[dev-dependencies]
trybuild = "1.0.121"  # trybuild[^24]
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
// tests/compile-fail/builder_on_enum.rs
use macro_user::Builder;

#[derive(Builder)]
enum Invalid {
    A,
    B,
}

fn main() {}
```

```text
// tests/compile-fail/builder_on_enum.stderr
error: Builder supports structs only
 --> tests/compile-fail/builder_on_enum.rs:4:1
  |
4 | enum Invalid {
  | ^^^^
```

```rust
// tests/compile-fail/select_rejects_insert.rs
use macro_user::select;

fn main() {
    let _ = select!(INSERT INTO users VALUES (1));
}
```

```text
// tests/compile-fail/select_rejects_insert.stderr
error: select! accepts SELECT statements only
 --> tests/compile-fail/select_rejects_insert.rs:4:21
  |
4 |     let _ = select!(INSERT INTO users VALUES (1));
  |                     ^^^^^^
```

### Proc Macro Best Practices

Errors **MUST** be returned as `syn::Error` with the narrowest useful span:

```rust
// GOOD: the diagnostic points at the `enum` keyword.
Data::Enum(e) => {
    return Err(Error::new(e.enum_token.span, "Builder supports structs only"));
}
```

```rust
// BAD: no span, and the message is buried under
// "error: proc-macro derive panicked".
_ => panic!("Builder only works on structs"),
```

Attribute parsing **SHOULD** use darling[^25] rather than hand-written
`Meta` walking:

```toml
[dependencies]
darling = "0.24.1"  # darling[^25]
```

**Why**: darling derives the parser from a struct definition, so unknown keys,
missing required keys and wrong value types all produce spanned errors for
free. Hand-written `Meta` traversal typically accumulates one `if` per key and
degrades to ignoring anything unrecognised.

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
[Testing Guide](../process/testing.md); this guide covers only the Rust tooling.

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
[Versioning Guide](../process/versioning.md).

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

## Async Runtimes

Projects **SHOULD** use tokio[^14] as the default async runtime. Projects that
need a smaller runtime **SHOULD** use smol[^18]. async-std **MUST NOT** be used
in new code.

### Why Not async-std

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

### smol Alternative

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

### Runtime-Agnostic Code

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

### Selecting a Backend with cfg

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

### Spawning Tasks

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

### Async Testing

Test snippets in this guide assume the scoped allowance from
[Recommended Lint Groups](#recommended-lint-groups); `unwrap` in a test is a
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

cucumber 0.23.0 requires Rust 1.88 or later, which sets the floor for the
`msrv` and `rust-toolchain.toml` values used elsewhere in this guide.[^12]

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
[Toolchain, Edition and MSRV](#toolchain-edition-and-msrv). The pinned channel
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

## WebAssembly (WASM)

Projects **MAY** compile Rust to WebAssembly for browser or edge runtime
deployment. wasm-pack[^19] **SHOULD** be used for building WASM packages.

### Why Rust for WASM

- **Performance**: Near-native speed in the browser
- **Safety**: Memory-safe without garbage collection
- **Size**: Small binary sizes with aggressive optimization
- **Interop**: Excellent JavaScript interoperability via wasm-bindgen

### Target Selection

`wasm32-unknown-unknown` and the WASI targets are not interchangeable and
**MUST** be chosen deliberately.

| Target | Use | Host API |
| ------ | --- | -------- |
| `wasm32-unknown-unknown` | Browser, bundler, wasm-bindgen | JavaScript via wasm-bindgen; no filesystem, no sockets |
| `wasm32-wasip1` | Edge and server runtimes (Wasmtime, Wasmer) | WASI preview 1: files, clocks, stdio |
| `wasm32-wasip2` | Component-model runtimes | WASI preview 2 interfaces |

**Why**: `wasm32-unknown-unknown` has no operating system behind it. `std::fs`,
`std::net` and `std::time::SystemTime::now` compile and then fail or panic at
run time, and `wasm-bindgen` is unavailable on WASI targets because there is no
JavaScript host to bind to. Code shared between the two **MUST** be gated on
`target_os`, not merely on `target_arch = "wasm32"`.

### Setup

```bash
# Install the browser target
rustup target add wasm32-unknown-unknown

# Install wasm-pack, pinned
cargo install wasm-pack --version 0.15.0 --locked

# Optional: wasm-opt for size optimisation
cargo install wasm-opt --version 0.116.1 --locked
```

### Project Structure

The manifest **MUST** list every crate and every `web-sys` feature the code
uses.

**Why**: `web-sys` gates each Web IDL interface behind a Cargo feature to keep
compile times and binary size down, so an unlisted feature is a
`error[E0432]: unresolved import 'web_sys::Document'`, not a smaller binary.
The same applies to the crates that examples reach for without declaring:
`console_error_panic_hook`, `serde` and `serde-wasm-bindgen`.

```toml
# Cargo.toml
[package]
name = "my_crate"
version = "0.1.0"
edition = "2024"
rust-version = "1.94.0"

[lib]
crate-type = ["cdylib", "rlib"]

[dependencies]
console_error_panic_hook = "0.1.7"
js-sys = "0.3.105"
serde = { version = "1.0.229", features = ["derive"] }
serde-wasm-bindgen = "0.6.5"
wasm-bindgen = "0.2.128"  # wasm-bindgen[^20]

[dependencies.web-sys]
version = "0.3.105"
features = ["Document", "Element", "Window"]  # one feature per interface used

[dev-dependencies]
wasm-bindgen-test = "0.3.78"

[profile.release]
opt-level = "z"      # Optimise for size
lto = true           # Link-time optimisation
codegen-units = 1
panic = "abort"
strip = true
```

```toml
# BAD: the code below calls web_sys::window(), sets a panic hook and
# round-trips serde values, none of which this manifest can compile.
[dependencies]
wasm-bindgen = "0.2"

[dev-dependencies]
wasm-bindgen-test = "0.3"
```

### Basic WASM Module

```rust
// src/lib.rs
use serde::{Deserialize, Serialize};
use wasm_bindgen::prelude::*;
use web_sys::Element;

#[wasm_bindgen(start)]
pub fn start() {
    console_error_panic_hook::set_once();
}

#[wasm_bindgen]
#[must_use]
pub fn greet(name: &str) -> String {
    format!("Hello, {name}!")
}

#[wasm_bindgen]
#[derive(Default)]
pub struct Counter {
    value: i32,
}

#[wasm_bindgen]
#[allow(clippy::missing_const_for_fn, reason = "#[wasm_bindgen] rejects const fn")]
impl Counter {
    #[wasm_bindgen(constructor)]
    #[must_use]
    pub fn new() -> Self {
        Self::default()
    }

    pub fn increment(&mut self) {
        self.value += 1;
    }

    #[must_use]
    pub fn value(&self) -> i32 {
        self.value
    }
}

/// Creates a detached element of type `tag`.
///
/// # Errors
///
/// Returns the JavaScript error when there is no window or document, or when
/// `tag` is not a valid element name.
#[wasm_bindgen]
pub fn create_element(tag: &str) -> Result<Element, JsValue> {
    let window = web_sys::window().ok_or_else(|| JsValue::from_str("no window"))?;
    let document = window.document().ok_or_else(|| JsValue::from_str("no document"))?;
    document.create_element(tag)
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Config {
    pub name: String,
    pub value: i32,
}

/// Round-trips a configuration object through Rust.
///
/// # Errors
///
/// Returns the JavaScript error when `config` does not deserialise into
/// [`Config`].
#[wasm_bindgen]
pub fn process_config(config: JsValue) -> Result<JsValue, JsValue> {
    let mut config: Config = serde_wasm_bindgen::from_value(config)?;
    config.value += 1;
    Ok(serde_wasm_bindgen::to_value(&config)?)
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
// tests/web.rs
#![cfg(target_arch = "wasm32")]

use wasm_bindgen_test::{wasm_bindgen_test, wasm_bindgen_test_configure};
use wasmdemo::{Counter, greet};

wasm_bindgen_test_configure!(run_in_browser);

#[wasm_bindgen_test]
fn greet_interpolates() {
    assert_eq!(greet("Test"), "Hello, Test!");
}

#[wasm_bindgen_test]
fn counter_increments() {
    let mut counter = Counter::new();
    assert_eq!(counter.value(), 0);
    counter.increment();
    assert_eq!(counter.value(), 1);
}
```

**Why `#![cfg(target_arch = "wasm32")]`**: `wasm_bindgen_test` targets a
browser or Node host. Without the gate, `cargo test` on the development machine
tries to build the file for the host target and fails on the missing
JavaScript environment.

```bash
# Run WASM tests in a headless browser
wasm-pack test --headless --firefox
wasm-pack test --headless --chrome

# Run in Node.js
wasm-pack test --node
```

### WASM Best Practices

Exported functions **MUST NOT** unwrap host lookups. `web_sys::window()`
returns `None` in a worker or in Node, and `unwrap` there aborts the module
with an unhelpful "unreachable executed" trap rather than a JavaScript
exception the caller can catch.

```rust
// GOOD: the host failure becomes a rejected promise or a thrown JsValue.
let window = web_sys::window().ok_or_else(|| JsValue::from_str("no window"))?;
```

```rust
// BAD: traps the whole module in a worker context.
let window = web_sys::window().unwrap();
```

`console_error_panic_hook::set_once()` **SHOULD** be installed from
`#[wasm_bindgen(start)]` so that any panic that does occur prints a Rust stack
trace to the browser console instead of "unreachable executed".

### WASM Size Optimisation

The release profile in [Project Structure](#project-structure) is the size
configuration; the settings **MUST** be at the workspace root when the crate is
a workspace member, because Cargo ignores `[profile]` in a non-root manifest
and says so: "profiles for the non root package will be ignored".

```bash
# Check WASM size
ls -lh pkg/*.wasm

# Analyse with twiggy
cargo install twiggy --version 0.8.0 --locked
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

## Conditional Compilation with Cargo Features

Cargo features are **additive compile-time configuration**. They **MUST NOT**
be used for A/B testing, staged rollout or any experiment whose cohort is
decided per request. Runtime experiments **MUST** use runtime configuration.

### Why

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

### Feature Flags via Cargo Features

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

### Feature Unification

A feature enabled anywhere in the graph is enabled for the whole build of that
crate. Libraries **MUST NOT** rely on a feature being off, and **MUST**
document which combinations are supported.

**Why**: if crate A depends on `my_crate` with `sqlite` and crate B depends on
`my_crate` with `postgres`, Cargo builds one `my_crate` with both. Code written
on the assumption that the two are alternatives is compiled with both enabled
and takes whichever arm is written first. Testing only the default feature set
never exercises that build.

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
#[must_use]
pub fn get(slice: &[u8], index: usize) -> Option<u8> {
    slice.get(index).copied()
}

// GOOD: the obligation is in the signature and documented
/// Reads `slice[index]` without a bounds check.
///
/// # Safety
///
/// `index` must be strictly less than `slice.len()`. Violating this reads out
/// of bounds, which is undefined behaviour.
#[must_use]
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
use std::alloc::{Layout, alloc_zeroed, dealloc, handle_alloc_error};
use std::ptr::NonNull;

pub struct ZeroedBuffer {
    ptr: NonNull<u8>,
    layout: Layout,
}

impl ZeroedBuffer {
    /// Allocates `len` zeroed bytes. Returns `None` for `len == 0`, which is
    /// not a valid allocation size.
    #[must_use]
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

    #[must_use]
    pub const fn len(&self) -> usize {
        self.layout.size()
    }

    #[must_use]
    pub const fn is_empty(&self) -> bool {
        false
    }

    #[must_use]
    pub const fn get(&self, index: usize) -> Option<u8> {
        if index >= self.len() {
            return None;
        }
        // SAFETY: `index < self.len()`, so the offset stays inside the
        // allocation, and `alloc_zeroed` initialised every byte of it.
        Some(unsafe { self.ptr.as_ptr().add(index).read() })
    }

    pub const fn set(&mut self, index: usize, value: u8) -> bool {
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

In Edition 2024 an `extern` block is itself unsafe and **MUST** be written
`unsafe extern "C"`. Attributes that affect linkage — `no_mangle`,
`link_section`, `export_name` — **MUST** be written in the `unsafe(...)` form.

**Why**: nothing checks that a declaration matches the library actually linked.
Declaring `fn strlen(s: *const c_char) -> usize` with the wrong signature is
undefined behaviour at every call site, and before Edition 2024 the declaration
itself needed no `unsafe`. Plain `extern "C" { ... }` in an Edition 2024 crate
fails with "error: extern blocks must be unsafe", and `#[no_mangle]` with
"error: unsafe attribute used without unsafe".[^36]

A wrapper **MUST NOT** hide a failure mode behind `expect`. `CString::new`
fails on an interior null byte, which is ordinary caller input.

```rust
use std::ffi::{CStr, CString, NulError};
use std::os::raw::c_char;

// Edition 2024: the extern block is unsafe, because nothing checks that these
// declarations match the library that is linked in.
unsafe extern "C" {
    fn strlen(s: *const c_char) -> usize;
    fn malloc(size: usize) -> *mut u8;
    fn free(ptr: *mut u8);
}

// GOOD: safe wrapper; the interior-null case is a Result, not a panic.
/// # Errors
///
/// Returns [`NulError`] when `s` contains an interior null byte and therefore
/// has no C string representation.
pub fn safe_strlen(s: &str) -> Result<usize, NulError> {
    let c_string = CString::new(s)?;
    // SAFETY: `c_string` is a valid, null-terminated C string that outlives
    // the call.
    Ok(unsafe { strlen(c_string.as_ptr()) })
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

// GOOD: Edition 2024 form for a symbol exported to C
#[unsafe(no_mangle)]
pub extern "C" fn my_crate_version() -> u32 {
    env!("CARGO_PKG_VERSION_MAJOR").parse().unwrap_or(0)
}
```

```rust
// BAD: Edition 2024 rejects both of these.
//   error: extern blocks must be unsafe
//   error: unsafe attribute used without unsafe
extern "C" {
    fn strlen(s: *const c_char) -> usize;
}

#[no_mangle]
pub extern "C" fn my_crate_version() -> u32 { 1 }
```

### Testing Unsafe Code

```rust
#[cfg(test)]
#[allow(clippy::unwrap_used, clippy::expect_used, reason = "test-only allowance")]
mod tests {
    use super::*;

    #[test]
    fn checked_access() {
        let data = [1_u8, 2, 3];
        assert_eq!(get(&data, 0), Some(1));
        assert_eq!(get(&data, 3), None);

        // SAFETY: 2 < data.len().
        assert_eq!(unsafe { get_unchecked(&data, 2) }, 3);
    }

    #[test]
    fn safe_wrapper() {
        let buffer = ZeroedBuffer::new(100).expect("100 > 0");
        assert_eq!(buffer.get(0), Some(0));
        assert_eq!(buffer.get(99), Some(0));
        assert_eq!(buffer.get(100), None);
    }

    #[test]
    fn edge_cases() {
        assert!(ZeroedBuffer::new(0).is_none());

        let mut buffer = ZeroedBuffer::new(1).expect("1 > 0");
        assert_eq!(buffer.get(0), Some(0));
        assert!(buffer.set(0, 42));
        assert_eq!(buffer.get(0), Some(42));
        assert_eq!(buffer.get(1), None);
        assert!(!buffer.set(1, 42));
    }

    #[test]
    #[cfg_attr(miri, ignore = "calls into C")]
    fn ffi_wrapper_reports_interior_nul() {
        assert_eq!(safe_strlen("abc"), Ok(3));
        assert!(safe_strlen("a\0b").is_err());
    }
}
```

Tests over `unsafe` code **MUST** assert on values, not merely on
`is_some()`. `assert!(buffer.get(0).is_some())` passes just as happily when the
byte behind it is uninitialised, so it cannot distinguish a sound
implementation from an unsound one; only Miri or a value assertion can.

### Miri for Undefined Behaviour Detection

Projects with `unsafe` code **SHOULD** run Miri[^26] to detect undefined
behaviour. The nightly toolchain **MUST** be pinned by date, exactly as for
fuzzing.

**Why**: Miri ships only on nightly and is occasionally missing from a given
night's build, so an unpinned `+nightly` job fails intermittently for reasons
unrelated to the code. `rustup component add miri --toolchain <date>` fails
loudly when the component is absent, which is the failure you want.

```bash
rustup toolchain install nightly-2026-09-01 --component miri

# Run the whole suite under Miri
cargo +nightly-2026-09-01 miri test

# Run one test
cargo +nightly-2026-09-01 miri test safe_wrapper

# Stricter aliasing model, and check for leaks
MIRIFLAGS="-Zmiri-tree-borrows -Zmiri-strict-provenance" \
  cargo +nightly-2026-09-01 miri test
```

Miri interprets Rust; it **MUST NOT** be expected to run tests that call into
C. A test that reaches an `extern "C"` function aborts with "unsupported
operation: can't call foreign function". FFI wrappers **SHOULD** therefore be
tested under Miri with the foreign call behind `#[cfg(not(miri))]`, leaving the
pure-Rust invariants covered.

```rust
#[test]
#[cfg_attr(miri, ignore = "calls into C")]
fn ffi_wrapper_reports_interior_nul() {
    assert_eq!(safe_strlen("abc"), Ok(3));
}
```

Miri is slow — typically 10× to 100× native — so it **SHOULD** run on a
schedule or on changes to `unsafe` code rather than on every push.

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
[^4]: [cargo-tarpaulin](https://github.com/xd009642/tarpaulin) - Code coverage tool for Rust; the default ptrace engine is Linux/x86-64 only
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
[^16]: [unicode-normalization](https://github.com/unicode-rs/unicode-normalization) - Unicode normalisation for Rust, Unicode 17.0.0 data
[^17]: [sqlx](https://github.com/transact-rs/sqlx) - Async SQL toolkit with compile-time checked queries
[^18]: [smol](https://github.com/smol-rs/smol) - Small and fast async runtime; the maintainer-nominated successor to [async-std](https://github.com/async-rs/async-std)
[^19]: [wasm-pack](https://wasm-bindgen.github.io/wasm-pack/) - Tool for building Rust WASM packages
[^20]: [wasm-bindgen](https://github.com/wasm-bindgen/wasm-bindgen) - Facilitating high-level interactions between Wasm modules and JavaScript
[^21]: [syn](https://github.com/dtolnay/syn) - Parser for Rust source code
[^22]: [quote](https://github.com/dtolnay/quote) - Rust quasi-quoting for code generation
[^23]: [proc-macro2](https://github.com/dtolnay/proc-macro2) - Wrapper around the proc-macro API
[^24]: [trybuild](https://github.com/dtolnay/trybuild) - Test harness for ui tests of compiler diagnostics
[^25]: [darling](https://github.com/TedDriggs/darling) - Declarative attribute parser for Rust proc macros
[^26]: [Miri](https://github.com/rust-lang/miri) - Experimental interpreter for Rust's mid-level intermediate representation
[^27]: [The `edition` field](https://doc.rust-lang.org/cargo/reference/manifest.html#the-edition-field) - Cargo manifest reference
[^28]: [rustsec/audit-check action metadata](https://github.com/rustsec/audit-check/blob/v2/action.yml) - declares `token` with `required: true` and no default
[^29]: [GitHub Actions runner images](https://github.com/actions/runner-images) - Runner image labels and architectures
[^30]: [Rust stable channel manifest](https://static.rust-lang.org/dist/channel-rust-stable.toml) - `[pkg.rust] version = "1.98.1 (48a229cea 2026-09-01)"`, manifest dated 2026-09-03
[^31]: [cargo-deny](https://github.com/EmbarkStudios/cargo-deny) - Advisory, licence, ban and source policy for Cargo dependencies
[^32]: [proptest](https://github.com/proptest-rs/proptest) - Hypothesis-style property testing with shrinking
[^33]: [cargo-mutants](https://github.com/sourcefrog/cargo-mutants) - Mutation testing for Rust
[^34]: [cargo-semver-checks](https://github.com/obi1kenobi/cargo-semver-checks) - Public API SemVer compliance checking
[^35]: [Criterion](https://github.com/criterion-rs/criterion.rs) - Statistics-driven benchmarking harness
[^36]: [Announcing Rust 1.85.0 and Rust 2024](https://blog.rust-lang.org/2025/02/20/Rust-1.85.0/) - Edition 2024 stabilisation, 20 February 2025; see the [Edition Guide](https://doc.rust-lang.org/edition-guide/rust-2024/index.html)
[^37]: [Interoperability](../../reference/rust/interoperability.md) - Rust API Guidelines, C-COMMON-TRAITS and the orphan rule
[^38]: [Naming](../../reference/rust/naming.md) - Rust API Guidelines, RFC 430 casing and conversion prefixes
[^39]: [Documentation](../../reference/rust/documentation.md) - Rust API Guidelines, rustdoc requirements
[^40]: [Flexibility](../../reference/rust/flexibility.md) - Rust API Guidelines, C-OBJECT and generic API design
[^41]: [Type safety](../../reference/rust/type-safety.md) - Rust API Guidelines, newtypes and custom argument types
[^42]: [syn 3.0.0 release notes](https://github.com/dtolnay/syn/releases/tag/3.0.0) - Breaking syntax-tree changes and the `*Modifiers` structs
[^43]: [cargo-vet](https://mozilla.github.io/cargo-vet/) - Recording and enforcing dependency audits
[^44]: [Security hardening for GitHub Actions](https://docs.github.com/actions/security-for-github-actions) - Pinning actions to a full-length commit SHA
[^45]: [Change in Guidance on Committing Lockfiles](https://blog.rust-lang.org/2023/08/29/committing-lockfiles/) - The Cargo team's 2023 reversal
[^46]: [Cargo.toml vs Cargo.lock](https://doc.rust-lang.org/cargo/guide/cargo-toml-vs-cargo-lock.html) - "When in doubt, check Cargo.lock into the version control system"
[^47]: [ICU4X](https://unicode-org.github.io/icu4x/) - Unicode's internationalisation library for Rust
[^48]: [Unicode 17.0.0](https://www.unicode.org/versions/latest/) - The current version of the Unicode Standard
[^49]: [Cargo features](https://doc.rust-lang.org/cargo/reference/features.html) - Feature unification and additive semantics

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
