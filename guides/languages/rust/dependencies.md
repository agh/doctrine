# Dependencies and Supply Chain

> [Doctrine](../../../README.md) > [Languages](../README.md) > [Rust](../rust.md) >
> Dependencies and Supply Chain

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in
BCP 14 [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119)
[RFC 8174](https://datatracker.ietf.org/doc/html/rfc8174) when, and only
when, they appear in all capitals, as shown here.

This guide covers choosing, constraining and auditing dependencies: cargo-audit
against the RustSec database, cargo-deny and cargo-vet policy, the Cargo.lock
decision table, version constraints, and Dependabot. The toolchain, lint,
formatting and pre-commit rules in the [Rust Style Guide](../rust.md) apply and
are not repeated here; every version quoted is listed in the [Tested Version
Matrix](versions.md) and was current on 8 September 2026.

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
expectations, lives in the [CI Guide](../../process/ci.md); the commands above are
the Rust-specific mechanism.

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

## References

[^3]: [cargo-audit](https://github.com/rustsec/rustsec/tree/main/cargo-audit) - Audit Cargo.lock for security vulnerabilities
[^7]: [RustSec Advisory Database](https://rustsec.org/) - Security advisory database for Rust crates
[^31]: [cargo-deny](https://github.com/EmbarkStudios/cargo-deny) - Advisory, licence, ban and source policy for Cargo dependencies
[^43]: [cargo-vet](https://mozilla.github.io/cargo-vet/) - Recording and enforcing dependency audits
[^45]: [Change in Guidance on Committing Lockfiles](https://blog.rust-lang.org/2023/08/29/committing-lockfiles/) - The Cargo team's 2023 reversal
[^46]: [Cargo.toml vs Cargo.lock](https://doc.rust-lang.org/cargo/guide/cargo-toml-vs-cargo-lock.html) - "When in doubt, check Cargo.lock into the version control system"

## See Also

- [Rust Style Guide](../rust.md) - Toolchain, lints, formatting and pre-commit
- [Rust topic guides](README.md) - The other Rust topic guides
