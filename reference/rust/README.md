# Rust API Guidelines — Vendored Snapshot and 2024 Supplement

> [Doctrine](../../README.md) > [Reference material](../../README.md#reference-material) > Rust

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in
BCP 14 [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119)
[RFC 8174](https://datatracker.ietf.org/doc/html/rfc8174) when, and only
when, they appear in all capitals, as shown here.

This file is Doctrine-authored. Everything else in this directory is a
vendored copy of the upstream [Rust API
Guidelines](https://github.com/rust-lang/api-guidelines) and **MUST NOT** be
edited here; report problems upstream.

## Contents

| File | Chapter |
| ---- | ------- |
| [SUMMARY.md](SUMMARY.md) | Upstream table of contents |
| [about.md](about.md) | About the guidelines |
| [checklist.md](checklist.md) | The full checklist, every `C-*` item |
| [naming.md](naming.md) | Naming (`C-CASE`, `C-CONV`, `C-GETTER`, …) |
| [interoperability.md](interoperability.md) | Interoperability (`C-COMMON-TRAITS`, `C-SERDE`, …) |
| [macros.md](macros.md) | Macros (`C-EVOCATIVE`, `C-MACRO-ATTR`, …) |
| [documentation.md](documentation.md) | Documentation (`C-EXAMPLE`, `C-FAILURE`, …) |
| [predictability.md](predictability.md) | Predictability (`C-SMART-PTR`, `C-CTOR`, …) |
| [flexibility.md](flexibility.md) | Flexibility (`C-INTERMEDIATE`, `C-GENERIC`, …) |
| [type-safety.md](type-safety.md) | Type safety (`C-NEWTYPE`, `C-BUILDER`, …) |
| [dependability.md](dependability.md) | Dependability (`C-VALIDATE`, `C-DTOR-FAIL`, …) |
| [debuggability.md](debuggability.md) | Debuggability (`C-DEBUG`, `C-DEBUG-NONEMPTY`) |
| [future-proofing.md](future-proofing.md) | Future proofing (`C-SEALED`, `C-STRUCT-PRIVATE`, …) |
| [necessities.md](necessities.md) | Necessities (`C-STABLE`, `C-PERMISSIVE`) |
| [external-links.md](external-links.md) | Upstream reading list |
| [LICENSE-APACHE](LICENSE-APACHE), [LICENSE-MIT](LICENSE-MIT) | Upstream licences |
| [NOTICE](NOTICE) | Attribution and change notice |

## Provenance

Vendored from `rust-lang/api-guidelines`, branch `master`, retrieved
2026-09-08 when its HEAD was
[`97a0969`](https://github.com/rust-lang/api-guidelines/commit/97a0969cb07fe4cabb0eed8a56234053f47d83dc)
(2025-07-08). Every file, its upstream URL, the commit that last touched it,
its digests and its licence are recorded in
[reference/UPSTREAM.json](../UPSTREAM.json); verify with
`python3 scripts/check_vendored.py`.

Two deterministic transforms are applied at import and declared per file in
the manifest. Both are implemented in
[scripts/check_vendored.py](../../scripts/check_vendored.py), so `--refresh`
reproduces them rather than reverting them:

- `mdbook-chapter-links` rewrites the 59 cross-chapter links that mdBook
  generates as `naming.html#c-case` into `naming.md#c-case`. Read as plain
  files, the `.html` targets do not exist. Rustdoc illustrations inside code
  fences, such as `trait.Deserialize.html`, are left untouched.
- `rustdoc-std-relocations` repoints two links in `naming.md` from
  `std/sync/atomic/struct.AtomicBool.html` to
  `std/sync/atomic/struct.Atomic.html`. `AtomicBool` is now
  `pub type AtomicBool = Atomic<bool>`, so the old page returns 404 and the
  `#method.into_inner` and `#method.get_mut` anchors live on `Atomic<T>`
  (checked 2026-09-08).

The `upstream_sha256` field in the manifest records the untouched download,
so the transform can always be audited against the original.

One upstream defect is left in place: `checklist.md` defines
`[C-HTML-ROOT]: documentation.md#c-html-root`, but that anchor no longer
exists and the label is never referenced, so nothing renders from it.

## Doctrine supplement: Rust 2024 API contracts

Checked against Rust 1.98.1 (2026-09-01) on 2026-09-08.

Most upstream chapters last changed between 2017 and 2023 and predate the
language and Cargo features below. They remain correct: nothing here
contradicts a `C-*` guideline. This section adds the API stability and
ecosystem contracts a crate published today also has to meet, and names the
upstream guideline each one extends.

### Declare an MSRV

A published crate **MUST** set `rust-version` in `Cargo.toml`.

#### Why

Without it, a consumer on an older toolchain gets a syntax error or a missing
standard-library item instead of a statement about support. With it, Cargo
reports the unsupported toolchain directly, `cargo add` selects a compatible
requirement, the resolver can take it into account, and Clippy's
`incompatible_msrv` lint can fire. This is `C-STABLE` — a stable crate makes
its public commitments explicit — extended from dependencies to the compiler.

```toml
# Do
[package]
name = "my-crate"
version = "1.0.0"
edition = "2024"
rust-version = "1.85"     # the oldest toolchain CI actually builds
```

```toml
# Don't — the supported range is whatever happens to compile today.
[package]
name = "my-crate"
version = "1.0.0"
edition = "2024"
```

The declared MSRV **MUST** be built in CI. A number nobody tests is a guess.
Raising it is a minor version bump at least; crates whose consumers pin
conservatively **SHOULD** treat it as breaking.

### Choose an edition deliberately

A crate **SHOULD** state its edition explicitly. Adopting edition 2024 is
**OPTIONAL**: editions are per-crate and interoperate, so a 2015 or 2018
crate is not thereby wrong.

#### Why

Edition 2024 shipped in Rust 1.85.0. It changes defaults that affect API
surface, most visibly by making `unsafe_op_in_unsafe_fn` warn by default.
Moving editions is a decision with a cost and a payoff; inheriting one by
omission is neither.

### Resolver v3 and MSRV-aware resolution

A workspace on edition 2024 **SHOULD NOT** override the resolver.

#### Why

`resolver = "3"` is the edition 2024 default and requires Rust 1.84 or later.
It flips `resolver.incompatible-rust-versions` from `allow` to `fallback`, so
Cargo prefers a dependency version compatible with your `rust-version`
instead of the newest one. Pinning the resolver back to `"2"` silently
re-enables upgrades that break your declared MSRV.

```toml
# Do — a virtual workspace on edition 2024 inherits resolver 3.
[workspace]
members = ["crate-a", "crate-b"]
resolver = "3"
```

```toml
# Don't — reintroduces MSRV-blind resolution under an edition-2024 crate.
[workspace]
members = ["crate-a", "crate-b"]
resolver = "2"
```

### Traits that return futures or opaque types

A public trait that returns a future **SHOULD** desugar `async fn` to
`-> impl Future<Output = …> + Send`.

#### Why

`async fn` and return-position `impl Trait` in traits both stabilised in Rust
1.75, after the upstream chapters were written, so no `C-*` guideline covers
them. `async fn` in a public trait triggers the `async_fn_in_trait` lint:
callers cannot name the returned future, so they cannot require `Send`, and a
generic wrapper that spawns onto a multi-threaded executor will not compile.
Adding `+ Send` later is a breaking change, so the choice **MUST** be made
before publishing. This extends `C-SEND-SYNC`.

```rust
use std::future::Future;

// Do — callers can spawn the future on a multi-threaded runtime.
pub trait Transport {
    fn get(&self, path: &str) -> impl Future<Output = Result<Response, Error>> + Send;
}

// Don't — `async fn` in a public trait leaves the auto traits unspecified.
pub trait Transport {
    async fn get(&self, path: &str) -> Result<Response, Error>;
}
```

Returning `impl Trait` from a trait method also makes the trait
dyn-incompatible. Where callers need `dyn`, return `Pin<Box<dyn Future<…>>>`
instead and say so in the documentation.

### Diagnostic attributes

A trait whose bound is commonly unsatisfied **SHOULD** carry
`#[diagnostic::on_unimplemented]`.

#### Why

The `#[diagnostic]` namespace and `on_unimplemented` stabilised in Rust 1.78,
`#[diagnostic::do_not_recommend]` in Rust 1.85. Both are hints: a compiler
that does not understand them ignores them, and malformed input is not an
error, so using them costs no compatibility. They turn an unsatisfied bound
from a trait-solver trace into a sentence about your API, which is the same
goal as `C-GOOD-ERR`.

```rust
#[diagnostic::on_unimplemented(
    message = "`{Self}` cannot be stored in a Config",
    label = "not a configuration value",
    note = "implement `ConfigValue` or convert to `String` first"
)]
pub trait ConfigValue {
    fn encode(&self) -> String;
}
```

Use `#[diagnostic::do_not_recommend]` on a blanket impl that the compiler
would otherwise suggest as the cause of an unrelated failure.

### Unsafe API contracts

Upstream `C-FAILURE` already requires a `# Safety` section on every `unsafe`
function. Edition 2024 adds one obligation: the body of an `unsafe fn`
**MUST** wrap its unsafe operations in an explicit `unsafe {}` block.

#### Why

Before edition 2024, `unsafe fn` served two roles — declaring an obligation on
the caller, and granting unsafe powers to the whole body. The
`unsafe_op_in_unsafe_fn` lint, warn-by-default from edition 2024, separates
them, so the block marks exactly which operations rely on the documented
precondition.

```rust
// Do
/// # Safety
///
/// `i` must be less than `x.len()`.
pub unsafe fn get_unchecked<T>(x: &[T], i: usize) -> &T {
    unsafe { x.get_unchecked(i) }
}

// Don't — warns under edition 2024, and the unsafe region is unbounded.
pub unsafe fn get_unchecked<T>(x: &[T], i: usize) -> &T {
    x.get_unchecked(i)
}
```

### Check semver mechanically

A published crate **SHOULD** run `cargo-semver-checks` in CI.

#### Why

The whole `future-proofing` chapter is about changes that break downstream
crates without breaking your own build: removing a trait method, adding a
field to a public struct, sealing a trait. Review catches some of them.
`cargo-semver-checks` compares the built rustdoc of the working tree against
the last published release and fails on a change the version bump does not
allow, so `C-STRUCT-PRIVATE` and `C-SEALED` stop depending on whoever is
reviewing.

```yaml
# .github/workflows/semver.yml
name: semver
on: [pull_request]
jobs:
  semver:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: dtolnay/rust-toolchain@6bed0761d98439e5a578e2877258200ad565ba87 # stable
      - run: cargo install cargo-semver-checks --version 0.50.0 --locked
      - run: cargo semver-checks check-release
```

`cargo-semver-checks` 0.50.0 is the current release on crates.io as of
2026-09-08, and both actions are pinned to the commit their tag pointed at on
that date. Pin all three: an unpinned install changes the lint set under a
pipeline that never changed.

## Sources

Every claim above was checked on 2026-09-08 against:

- [Rust stable release channel](https://static.rust-lang.org/dist/channel-rust-stable.toml)
- [Rust 2024 edition guide](https://doc.rust-lang.org/edition-guide/rust-2024/)
- [`unsafe_op_in_unsafe_fn` in edition 2024](https://doc.rust-lang.org/edition-guide/rust-2024/unsafe-op-in-unsafe-fn.html)
- [The `rust-version` field](https://doc.rust-lang.org/cargo/reference/rust-version.html)
- [Cargo resolver versions](https://doc.rust-lang.org/cargo/reference/resolver.html#resolver-versions)
- [Diagnostic attributes](https://doc.rust-lang.org/reference/attributes/diagnostics.html)
- [`rust-lang/rust` release notes](https://github.com/rust-lang/rust/blob/master/RELEASES.md)
  for the 1.75, 1.78 and 1.85 stabilisations
- [cargo-semver-checks on crates.io](https://crates.io/crates/cargo-semver-checks)

## See Also

- [Rust Style Guide](../../guides/languages/rust.md)
- [Test Writer: Rust Module](../../agents/test-writer/rust.md)
- [Versioning Guide](../../guides/process/versioning.md)
