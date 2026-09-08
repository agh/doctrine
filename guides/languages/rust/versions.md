# Tested Version Matrix

> [Doctrine](../../../README.md) > [Languages](../README.md) > [Rust](../rust.md) >
> Tested Version Matrix

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in
BCP 14 [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119)
[RFC 8174](https://datatracker.ietf.org/doc/html/rfc8174) when, and only
when, they appear in all capitals, as shown here.

This guide is the single table of the toolchain, crate, executable and action
versions that every Rust guide quotes, with the date they were verified. The
toolchain, lint, formatting and pre-commit rules in the [Rust Style
Guide](../rust.md) apply and are not repeated here. Every entry was current on 8
September 2026.

Every version below was current on crates.io, the Rust release channel or the
action's tag list on 8 September 2026, and the Rust examples across the Rust guides
were compiled against them with `cargo check`, `cargo test` and
`cargo clippy -- -D warnings` on Rust 1.98.1.

Library requirements are written as caret ranges, which is what a manifest
**SHOULD** contain; the exact release tested is stated beside each. Executables
and actions are pinned exactly, because nothing unifies them.

## Toolchain

| Component | Tested | Notes |
| --------- | ------ | ----- |
| Rust stable | 1.98.1 (2026-09-01) | `rust-toolchain.toml` channel |
| Rust nightly | nightly-2026-09-01 | Miri, cargo-fuzz, nightly rustfmt |
| Edition | 2024 | Stable since Rust 1.85.0 |
| MSRV used in examples | 1.94.0 | Highest `rust-version` in the pinned graph (SQLx 0.9.0) |

## Libraries

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

## Executable Tools

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

## GitHub Actions

Pinned by full commit SHA; see [Pinning Actions](ci.md#pinning-actions).

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

## See Also

- [Rust Style Guide](../rust.md) - Toolchain, lints, formatting and pre-commit
- [Rust topic guides](README.md) - The other Rust topic guides
