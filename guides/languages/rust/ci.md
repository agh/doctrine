# CI Pipeline

> [Doctrine](../../../README.md) > [Languages](../README.md) > [Rust](../rust.md) > CI Pipeline

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in
BCP 14 [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119)
[RFC 8174](https://datatracker.ietf.org/doc/html/rfc8174) when, and only
when, they appear in all capitals, as shown here.

This guide covers the GitHub Actions workflow for a Rust project: the lint,
test, coverage and security lanes, pinning every action to a commit SHA, and
auditing without handing a token to a third-party action. The toolchain, lint,
formatting and pre-commit rules in the [Rust Style Guide](../rust.md) apply and
are not repeated here; every version quoted is listed in the [Tested Version
Matrix](versions.md) and was current on 8 September 2026.

Generic pipeline structure, caching and branch protection are in the
[CI Guide](../../process/ci.md). This section covers only what is specific to
Rust: toolchain lanes, action pinning, and the audit job's permissions.

## Pinning Actions

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

## Auditing Without a Token

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
[CI Guide](../../process/ci.md#rust); the two **MUST NOT** diverge.

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

## References

[^28]: [rustsec/audit-check action metadata](https://github.com/rustsec/audit-check/blob/v2/action.yml) - declares `token` with `required: true` and no default
[^44]: [Security hardening for GitHub Actions](https://docs.github.com/actions/security-for-github-actions) - Pinning actions to a full-length commit SHA

## See Also

- [Rust Style Guide](../rust.md) - Toolchain, lints, formatting and pre-commit
- [Rust topic guides](README.md) - The other Rust topic guides
