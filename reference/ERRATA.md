# Vendored Reference Errata

> [Doctrine](../README.md) > Reference errata

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

Everything under `reference/` except `reference/security/` is a verbatim copy of
a third-party document. Payloads **MUST NOT** be reformatted, linted or
auto-fixed; `scripts/check_vendored_payloads.py` fails the build when a payload
changes without a matching update to `reference/CHECKSUMS.sha256`.

**Why**: upstream text is evidence of what the upstream project says. Local
formatting passes destroy that: commit `b6f870a` ran a Markdown auto-fixer over
`reference/` and stripped the whitespace after 474 list markers in the Google
guides, so `1.  Foo` became `1.Foo` and stopped rendering as a list.

This file is the complete register of deliberate local divergence from upstream.
Every entry **MUST** record the upstream text, the correction, the reason, and
the command that demonstrates the defect.

## Corrections

| Payload | Upstream text | Doctrine text | Defect |
| ------- | ------------- | ------------- | ------ |
| `google/csharp.md` | `int SomeProperty => _someProperty` | `int SomeProperty => _someProperty;` | Does not compile |
| `google/shell.md` | `=~ foo:(\d+)` | `=~ foo:([0-9]+)` | Matches the wrong strings |
| `google/javascript.html` | `export = {` | `exports = {` | Not valid JavaScript |
| `google/json.xml` | `"etag": "W/"C0QB….""` | `"etag": "W/\"C0QB….\""` | Not valid JSON |
| `airbnb/ruby.md` | `rescue Errno:ENOENT => ex` | `rescue Errno::ENOENT => ex` | Does not parse |
| `airbnb/react.md` | — | Historical-snapshot notice added | Guide predates React 19 |
| `holywell/sql.md` | prefer `ABSOLUTE` to `ABS` | prefer `INTEGER` to `INT` | `ABSOLUTE` is not `ABS` |
| `uber/go.md` | `readFile` without `Close` | `defer f.Close()` added | Leaks file descriptors |

All eight defects are still present upstream, so a vendor resync will not repair
them and will reintroduce them. They **SHOULD** be reported upstream.

### `reference/google/csharp.md` — expression-bodied property

The expression-bodied property example under "Expression body syntax" has no
terminating semicolon. `dotnet build` (SDK 10.0.400, `net10.0`) rejects it with
`error CS1002: ; expected`; the same declaration with `;` builds cleanly.

### `reference/google/shell.md` — regular expression digit class

The preferred builtin example under "Builtin Commands vs. External Commands"
used `[[ "${string}" =~ foo:(\d+) ]]`. Bash's `=~` takes POSIX extended regular
expressions, which have no `\d`: under `bash` 5.3.15 the original rejects
`foo:123` and captures `ddd` from `foo:ddd`, while `foo:([0-9]+)` captures `123`
and rejects `foo:ddd`.

### `reference/google/javascript.html` — `goog.module` exports

The positive namespace example under "5.4.12 Do not define nested namespaces"
assigned `export = {...}` inside a `goog.module` file. `node --check` (Node
26.8.1) rejects it as `SyntaxError: Unexpected token 'export'` in both CommonJS
and module modes; `exports = {...}`, which is the form the same document uses in
section 3.3.3, parses in both.

### `reference/google/json.xml` — `data.etag` example

The `data.etag` example embedded unescaped quotation marks in a JSON string, so
`json.loads` raises `JSONDecodeError: Expecting ',' delimiter`. Escaping the two
quotation marks inside the weak ETag preserves the value `W/"C0QBRXcycSp7ImA9WxRVFUk."`
and parses.

### `reference/airbnb/ruby.md` — `rescue` constant

The good example under "Exceptions" used `rescue Errno:ENOENT => ex`. Ruby
namespaces constants with `::`; `ruby -wc` (3.3.9) reports a `SyntaxError` on the
original and `Syntax OK` on `Errno::ENOENT`.

### `reference/airbnb/react.md` — historical snapshot

The file is Airbnb's React/JSX guide at upstream commit `7a6ef3e`
(17 February 2021). It positively recommends `defaultProps` on function
components, which React 19 removed in favour of ES6 default parameters, and it
predates Hooks, Suspense, Server Components, the automatic JSX transform and the
React Compiler. A status notice at the top of the file, plus a note beside the
`defaultProps` rule, direct readers to `guides/frameworks/react.md`. No upstream
rule text was rewritten.

### `reference/holywell/sql.md` — abbreviated keywords

The reserved-word section told readers to prefer `ABSOLUTE` to `ABS`. They are
unrelated keywords: `ABS` is the absolute-value function, while `ABSOLUTE` is a
cursor `FETCH` direction. Against SQLite 3.53.4, `SELECT ABS(-5)` returns `5`
and `SELECT ABSOLUTE(-5)` fails with `no such function: ABSOLUTE`. The example
now uses a genuine abbreviation pair, `INTEGER` and `INT`, which the SQL standard
defines as the same type.

### `reference/uber/go.md` — `readFile` in "Exit in Main"

The good `readFile` opened a file and never closed it. Compiled with Go 1.27.1
and run with garbage collection disabled under `ulimit -n 128`, the original
fails after 124 reads with `too many open files`; with `defer f.Close()` the same
loop completes 256 reads. The example's lesson — return errors instead of calling
`log.Fatal` outside `main` — is unchanged.

## Outstanding upstream drift

The Markdown auto-fixer in commit `b6f870a` also normalised list-marker spacing,
table pipes and blank lines in `reference/airbnb/`, `reference/holywell/`,
`reference/rubocop/`, `reference/rust/`, `reference/shopify/` and
`reference/uber/`. Those payloads still render correctly, so they are not errata,
but they are no longer byte-identical to upstream and **SHOULD** be restored when
the vendor tree is next resynchronised.

## See Also

- [`check_vendored_payloads.py`](../scripts/check_vendored_payloads.py) - payload integrity check
- [`reference/CHECKSUMS.sha256`](CHECKSUMS.sha256) - recorded payload digests
- [AGENTS.md](../AGENTS.md) - repository house rules
