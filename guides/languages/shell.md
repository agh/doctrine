# Shell Style Guide

> [Doctrine](../../README.md) > [Languages](../README.md) > Shell

The key words "**MUST**", "**MUST NOT**", "**REQUIRED**", "**SHALL**",
"**SHALL NOT**", "**SHOULD**", "**SHOULD NOT**", "**RECOMMENDED**", "**MAY**",
and "**OPTIONAL**" in this document are to be interpreted as described in
[RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

Extends [Google Shell Style Guide](google/shell.md)[^1].

## Quick Reference

| Task | Tool | Command |
| ---- | ---- | ------- |
| Lint | shellcheck[^2] | `shellcheck *.sh` |
| Format | shfmt[^3] | `shfmt -w *.sh` |
| Test | bats[^4] | `bats tests/` |
| Type check | - | - |
| Semantic | - | - |
| Dead code | - | - |
| Coverage | bashcov[^5] | `bashcov bats tests/` |
| Complexity | - | - |
| Fuzz | - | - |
| Test perf | - | - |

## When to Use Shell

Shell **MAY** be appropriate for:

- Small utilities under 100 lines
- Simple wrapper scripts
- Glue between other programs
- Build/CI scripts

Scripts **MUST NOT** exceed 100 lines. If your script grows beyond 100 lines
or needs complex logic, you **MUST** rewrite it in Python.

## Linting: shellcheck

You **MUST** use shellcheck[^2] for linting shell scripts.

### Why shellcheck

shellcheck is the world-class shell linter, catching bugs and suggesting best
practices. It identifies common pitfalls like unquoted variables, incorrect
conditionals, and portability issues before they cause runtime failures.

```bash
# Install
# macOS
brew install shellcheck

# Ubuntu/Debian
apt install shellcheck

# Run
shellcheck script.sh

# All files
shellcheck **/*.sh
```

### Configuration

You **SHOULD** create a `.shellcheckrc` file:

```ini
# Enable all checks
enable=all

# Exclude specific rules if needed
# disable=SC2086
```

## Formatting: shfmt

You **MUST** use shfmt[^3] for formatting shell scripts.

### Why shfmt

shfmt provides consistent, automated formatting for shell scripts, eliminating
style debates and ensuring readability across your codebase. It handles
complex cases like heredocs and pipeline formatting correctly.

```bash
# Install
go install mvdan.cc/sh/v3/cmd/shfmt@latest

# Format
shfmt -w script.sh

# Format with specific style
shfmt -i 2 -ci -bn -w script.sh
```

You **MUST** use these options:

- `-i 2`: 2-space indent
- `-ci`: Indent switch cases
- `-bn`: Binary ops on newline

## Script Template

All scripts **MUST** follow this template structure:

```bash
#!/bin/bash
#
# Brief description of what this script does.

set -Eeuo pipefail

# Constants
# Assign first, then mark readonly: a combined `readonly x="$(...)"` reports
# readonly's own status and hides a failed substitution from `set -e`.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_DIR

# Cleanup
cleanup() {
  local exit_code=$?
  # Add cleanup logic here
  exit "${exit_code}"
}
trap cleanup EXIT ERR

# Functions
log() {
  local timestamp
  timestamp="$(date +'%Y-%m-%dT%H:%M:%S%z')"
  echo "[${timestamp}] $*"
}

err() {
  local timestamp
  timestamp="$(date +'%Y-%m-%dT%H:%M:%S%z')"
  echo "[${timestamp}] ERROR: $*" >&2
}

usage() {
  cat <<EOF
Usage: $(basename "$0") [OPTIONS] <argument>

Description of what this script does.

Options:
  -h, --help     Show this help message
  -v, --verbose  Enable verbose output

Examples:
  $(basename "$0") input.txt
  $(basename "$0") -v input.txt
EOF
}

main() {
  local verbose=false

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -h | --help)
        usage
        exit 0
        ;;
      -v | --verbose)
        verbose=true
        shift
        ;;
      *)
        break
        ;;
    esac
  done

  if [[ $# -lt 1 ]]; then
    err "Missing required argument"
    usage
    exit 1
  fi

  local input="$1"

  if [[ "${verbose}" == true ]]; then
    log "Running from: ${SCRIPT_DIR}"
    log "Processing: ${input}"
  fi

  # Main logic here
}

main "$@"
```

The template is executable documentation: it **MUST** pass `shellcheck` under
the `enable=all` configuration above and `shfmt -i 2 -ci -bn -d` unmodified.
Copy it verbatim and delete what you do not need.

### Why

`readonly NAME="$(command)"`, `local name="$(command)"` and
`declare -r NAME="$(command)"` return the status of `readonly`, `local` or
`declare`, never the status of `command`. A failed substitution is therefore
invisible to `set -e`
([SC2155](https://www.shellcheck.net/wiki/SC2155)). Under Bash 5.3.15,
`set -e; readonly X="$(false)"` continues and exits 0, while
`set -e; X="$(false)"; readonly X` aborts with status 1. Splitting the
assignment is what makes a failed `cd` in `SCRIPT_DIR` stop the script.

`log` and `err` assign `timestamp` before printing for the same reason:
embedding `$(date ...)` directly in `echo` discards `date`'s exit status
([SC2312](https://www.shellcheck.net/wiki/SC2312)). Braces around every named
variable satisfy [SC2250](https://www.shellcheck.net/wiki/SC2250), which
`enable=all` turns on.

## Key Conventions

### Shebang and Options

All scripts **MUST** include:

```bash
#!/bin/bash
set -Eeuo pipefail
```

- `set -E`: Inherit ERR trap in functions (**REQUIRED**)
- `set -e`: Exit on error (**REQUIRED**)
- `set -u`: Error on undefined variables (**REQUIRED**)
- `set -o pipefail`: Pipelines fail on first error (**REQUIRED**)

### Variables

You **MUST** follow these variable conventions:

```bash
# Use braces and quotes (REQUIRED)
echo "${variable}"

# Local variables in functions (REQUIRED)
my_function() {
  local my_var="value"
}

# Constants are uppercase (REQUIRED)
readonly MAX_RETRIES=3
declare -r CONFIG_FILE="/etc/myapp.conf"
```

### Tests

You **MUST** use `[[ ]]` for tests, not `[ ]`:

```bash
# Use [[ ]] not [ ] (REQUIRED)
if [[ "${var}" == "value" ]]; then
  echo "match"
fi

# String tests
if [[ -z "${var}" ]]; then  # Empty
if [[ -n "${var}" ]]; then  # Not empty

# File tests
if [[ -f "${file}" ]]; then  # File exists
if [[ -d "${dir}" ]]; then   # Directory exists
```

### Command Substitution

You **MUST** use `$()` for command substitution, not backticks:

```bash
# Use $() not backticks (REQUIRED)
result="$(command)"
nested="$(command "$(other_command)")"
```

### Arrays

```bash
# Declare arrays
declare -a files
files=("one.txt" "two.txt" "three.txt")

# Append
files+=("four.txt")

# Iterate
for file in "${files[@]}"; do
  echo "${file}"
done

# Length
echo "${#files[@]}"
```

### Error Handling

```bash
# Check return values
if ! command; then
  err "Command failed"
  exit 1
fi

# Or with ||
command || { err "Failed"; exit 1; }
```

## Defensive Patterns

### Trap-Based Cleanup

Scripts **SHOULD** implement cleanup handlers for reliable resource management:

```bash
# Holds only this script's own temporary directory; empty until mktemp succeeds.
tmp_dir=''

cleanup() {
  local exit_code=$?
  if [[ -n "${tmp_dir}" && -d "${tmp_dir}" ]]; then
    rm -rf -- "${tmp_dir}"
  fi
  exit "${exit_code}"
}

trap cleanup EXIT ERR
```

A cleanup handler **MUST** delete only paths the script itself created, and
**MUST NOT** recursively delete `TMPDIR` or any other inherited path:

```bash
# Don't: TMPDIR is the caller's temporary root, which the script did not create
rm -rf -- "${TMPDIR:-}"

# Do: delete only the allocation this script owns
if [[ -n "${tmp_dir}" && -d "${tmp_dir}" ]]; then
  rm -rf -- "${tmp_dir}"
fi
```

### Why

The `-E` flag in `set -Eeuo pipefail` ensures ERR traps propagate into
functions. Without cleanup traps, scripts may leak temporary files, leave
processes running, or fail to release locks when errors occur.

`TMPDIR` is an inherited environment variable naming a *shared* temporary
root. `rm -rf -- "${TMPDIR:-}"` therefore destroys whatever the caller pointed
at, including other processes' work, even when the script allocated nothing:
running that handler with `TMPDIR` set to a populated directory removed the
whole tree. Guarding on a private `tmp_dir` that is empty until `mktemp -d`
succeeds means the failure path deletes nothing.

### Safe Temporary Files

You **SHOULD** use `mktemp` with the cleanup trap above for temporary files.
Register the trap first, then allocate, so an allocation failure leaves
`tmp_dir` empty and cleanup inert:

```bash
tmp_dir="$(mktemp -d)" || {
  err "Failed to create temp dir"
  exit 1
}
```

### Why a private variable

Assigning the allocation to `TMPDIR` instead of a private variable overwrites
the caller's setting, redirects every later `mktemp` in the process, and makes
the cleanup target ambient state rather than an owned one.

### Dependency Checking

Scripts **SHOULD** verify required commands exist before use:

```bash
check_deps() {
  local -a missing=()
  for cmd in "$@"; do
    command -v "$cmd" >/dev/null 2>&1 || missing+=("$cmd")
  done
  if [[ ${#missing[@]} -gt 0 ]]; then
    err "Missing dependencies: ${missing[*]}"
    exit 1
  fi
}

check_deps jq curl git
```

**Note**: Use `command -v` instead of `which`—it's a shell builtin and more portable.

## Testing: bats

You **SHOULD** use bats[^4] (Bash Automated Testing System) for testing shell scripts.

### Why bats

bats provides a simple, TAP-compliant testing framework purpose-built for
shell scripts. It offers clean syntax, setup/teardown hooks, and integrates
with CI systems out of the box.

```bash
# Install
# macOS
brew install bats-core

# npm
npm install --global bats

# Verify
bats --version
```

### Project Structure

```text
project/
├── bin/
│   └── script.sh      # executable; ends with main "$@", never sourced
├── lib/
│   └── helpers.sh     # sourceable functions only, no main call
├── tests/
│   ├── script.bats
│   ├── test_helper.sh
│   └── fixtures/
└── README.md
```

Executables and libraries **MUST** be separate files. An executable that ends
with `main "$@"` **MUST NOT** be sourced by a test; only files that define
functions and call nothing **MAY** be sourced.

```bash
# lib/helpers.sh
slugify() {
  local text="$1"
  printf '%s' "${text,,}" | tr -cs 'a-z0-9' '-'
}
```

### Why

Sourcing `bin/script.sh` runs `main` with the test runner's arguments. Under
the mandatory `set -Eeuo pipefail`, the missing-argument branch calls
`exit 1` and terminates the enclosing Bats process before any `@test` runs:
sourcing the template from a wrapper printed its usage text and exited 1
without reaching the following statement.

### Basic Test File

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
  # Runs before each test. Resolve the executable; never source it.
  script="${BATS_TEST_DIRNAME}/../bin/script.sh"
  # Libraries define functions only, so sourcing them is safe.
  source "${BATS_TEST_DIRNAME}/../lib/helpers.sh"
}

@test "script prints usage with --help" {
  run -0 "${script}" --help
  [[ "${output}" == *"Usage:"* ]]
}

@test "script fails with missing argument" {
  run ! "${script}"
  [[ "${output}" == *"Missing"* ]]
}

@test "slugify lowercases and hyphenates" {
  run -0 slugify 'Release Notes v2'
  [ "${output}" = "release-notes-v2" ]
}
```

### Why resolved paths

`bin/` is not on `PATH` inside a test, so bare `run script.sh` exits 127 with
`Command not found`, and Bats then reports that it executed 0 of the expected
tests. Resolving the path from `BATS_TEST_DIRNAME` makes the invocation
independent of the working directory. `run -0` and `run !` assert the exit
status inside `run` itself, so an unexpected 127 fails the test instead of
silently satisfying `[ "$status" -ne 0 ]`; both forms require the
`bats_require_minimum_version 1.5.0` declaration.

There is no `teardown` deleting `BATS_TEST_TMPDIR`: Bats creates that directory
per test and removes it after the run. Recording the path from inside a test
and checking it afterwards showed the directory already gone.

### Assertions

```bash
# Exit code
[ "$status" -eq 0 ]      # Success
[ "$status" -ne 0 ]      # Failure
[ "$status" -eq 1 ]      # Specific code

# Output matching
[ "$output" = "exact match" ]
[[ "$output" == *"substring"* ]]
[[ "$output" =~ ^pattern$ ]]

# Line-by-line output
[ "${lines[0]}" = "first line" ]
[ "${#lines[@]}" -eq 3 ]  # Line count

# File assertions
[ -f "$file" ]            # Exists
[ -s "$file" ]            # Non-empty
diff "$file" expected.txt # Content match
```

### Mocking Commands

```bash
@test "handles curl failure" {
  # Mock curl to fail
  curl() { return 1; }
  export -f curl

  run fetch_data
  [ "$status" -ne 0 ]
  [[ "$output" == *"fetch failed"* ]]
}
```

### Skipping Tests

```bash
@test "requires jq" {
  command -v jq >/dev/null 2>&1 || skip "jq not installed"
  run process_json
  [ "$status" -eq 0 ]
}
```

### CI Integration

Workflow examples in this guide are complete files. Each **MUST** declare an
`on` trigger, grant only `permissions: contents: read`, set a finite
`timeout-minutes`, and cancel superseded runs through `concurrency`:

```yaml
# .github/workflows/test.yml
name: Shell Tests

on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
      - name: Install bats
        run: npm install --global bats
      - name: Run tests
        run: bats tests/
```

### Why complete workflows

A file under `.github/workflows/` without `on` is not a workflow: GitHub's
workflow syntax defines `on` as the event configuration[^8], and actionlint
1.7.12 rejects a trigger-less body with `"on" section is missing in workflow`.
GitHub's secure-use reference asks for the `GITHUB_TOKEN` default to be read
access to repository contents only[^9]; linting and testing need nothing more.
`timeout-minutes` bounds a hung step, which would otherwise hold a runner until
the platform's own job execution limit expires, and `cancel-in-progress` stops
superseded pushes queueing behind each other.

### Pipelines

```bash
# Split long pipelines
command1 \
  | command2 \
  | command3
```

## Coverage: bashcov

You **MAY** use bashcov[^5] for code coverage of shell scripts.

```bash
# Install
gem install bashcov

# Run with bats
bashcov bats tests/

# With simplecov output
bashcov --root . bats tests/
```

## Pre-commit Configuration

You **SHOULD** configure pre-commit hooks[^6]:

```yaml
repos:
  - repo: https://github.com/shellcheck-py/shellcheck-py
    rev: v0.11.0.1
    hooks:
      - id: shellcheck

  - repo: https://github.com/scop/pre-commit-shfmt
    rev: v3.12.0-2
    hooks:
      - id: shfmt
        args: [-i, "2", -ci, -bn]
```

## CI Pipeline

You **SHOULD** integrate shell linting into your CI pipeline[^7]:

```yaml
# .github/workflows/lint.yml
name: Shell Lint

on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  lint:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
      - name: shellcheck
        uses: ludeeus/action-shellcheck@master
        with:
          scandir: './scripts'
      - name: Install shfmt
        env:
          SHFMT_VERSION: 3.14.1
          SHFMT_SHA256: 76e77641faa025814b77f153b29796b8e6fa2fca03e0c76a691608b86c7ea7bf
        run: |
          base=https://github.com/mvdan/sh/releases/download
          curl -fsSL -o /tmp/shfmt \
            "${base}/v${SHFMT_VERSION}/shfmt_v${SHFMT_VERSION}_linux_amd64"
          echo "${SHFMT_SHA256}  /tmp/shfmt" | sha256sum --check --strict
          mkdir -p "${HOME}/.local/bin"
          install -m 0755 /tmp/shfmt "${HOME}/.local/bin/shfmt"
          echo "${HOME}/.local/bin" >> "${GITHUB_PATH}"
      - name: shfmt
        run: shfmt -i 2 -ci -bn -d .
```

You **MUST NOT** use `uses: mvdan/sh@v0.7`. The `mvdan/sh` repository publishes
no action at any tag, and `v0.7` does not exist, so the step fails to resolve
before it runs.

### Why

shfmt ships as a single static binary per release[^3]. Downloading the pinned
`v3.14.1` asset and checking its SHA-256 gives an immutable dependency without
trusting a third-party action, and the checksum step fails loudly if the asset
ever changes. `-d` reports differences and exits non-zero rather than
rewriting files in CI, and the flags match those the guide mandates for local
formatting.

## See Also

- [CI Guide](../ci.md) - Comprehensive CI/CD pipeline configuration
- [Google Shell Style Guide](google/shell.md) - Extended style guide
- [Testing Guide](../testing.md) - Testing practices and patterns

## References

[^1]: [Google Shell Style Guide](https://google.github.io/styleguide/shellguide.html) - Google's comprehensive shell scripting style guide
[^2]: [ShellCheck](https://www.shellcheck.net/) - A shell script static analysis tool
[^3]: [shfmt](https://github.com/mvdan/sh) - A shell parser, formatter, and interpreter with bash support
[^4]: [bats-core](https://github.com/bats-core/bats-core) - Bash Automated Testing System
[^5]: [bashcov](https://github.com/infertux/bashcov) - Code coverage tool for Bash
[^6]: [pre-commit](https://pre-commit.com/) - A framework for managing and maintaining multi-language pre-commit hooks
[^7]: [GitHub Actions](https://docs.github.com/en/actions) - GitHub's CI/CD platform documentation
[^8]: [Workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax) - `on`, `permissions`, `concurrency`, timeouts
[^9]: [Secure use](https://docs.github.com/en/actions/reference/security/secure-use) - Least-privilege `GITHUB_TOKEN` guidance
