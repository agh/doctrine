# Rust API Design

> [Doctrine](../../../README.md) > [Languages](../README.md) > [Rust](../rust.md) > Rust API Design

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in
BCP 14 [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119)
[RFC 8174](https://datatracker.ietf.org/doc/html/rfc8174) when, and only
when, they appear in all capitals, as shown here.

This guide covers the traits a public type **MUST** implement and the naming,
documentation and type-safety rules for a published Rust API, organised around
the vendored [Rust API Guidelines](../../../reference/rust/checklist.md). The
toolchain, lint, formatting, dependency and CI rules in the [Rust Style
Guide](../rust.md) apply and are not repeated here; every version quoted is
listed in the [Tested Version Matrix](versions.md#tested-version-matrix) and was
current on 8 September 2026.

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
text under [`reference/rust/`](../../../reference/rust/checklist.md); this section
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
[`reference/rust/checklist.md`](../../../reference/rust/checklist.md).

## References

[^37]: [Interoperability](../../../reference/rust/interoperability.md) - Rust API Guidelines, C-COMMON-TRAITS and the orphan rule
[^38]: [Naming](../../../reference/rust/naming.md) - Rust API Guidelines, RFC 430 casing and conversion prefixes
[^39]: [Documentation](../../../reference/rust/documentation.md) - Rust API Guidelines, rustdoc requirements
[^40]: [Flexibility](../../../reference/rust/flexibility.md) - Rust API Guidelines, C-OBJECT and generic API design
[^41]: [Type safety](../../../reference/rust/type-safety.md) - Rust API Guidelines, newtypes and custom argument types

## See Also

- [Rust Style Guide](../rust.md) - Toolchain, lints, formatting, dependencies and CI
- [Rust topic guides](README.md) - The other Rust topic guides
