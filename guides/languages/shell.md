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
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Cleanup
cleanup() {
  local exit_code=$?
  # Add cleanup logic here
  exit "$exit_code"
}
trap cleanup EXIT ERR

# Functions
log() {
  echo "[$(date +'%Y-%m-%dT%H:%M:%S%z')] $*"
}

err() {
  echo "[$(date +'%Y-%m-%dT%H:%M:%S%z')] ERROR: $*" >&2
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

  if [[ "$verbose" == true ]]; then
    log "Processing: ${input}"
  fi

  # Main logic here
}

main "$@"
```

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
cleanup() {
  local exit_code=$?
  # Cleanup logic here
  rm -rf -- "${TMPDIR:-}"
  exit "$exit_code"
}

trap cleanup EXIT ERR
```

### Why

The `-E` flag in `set -Eeuo pipefail` ensures ERR traps propagate into
functions. Without cleanup traps, scripts may leak temporary files, leave
processes running, or fail to release locks when errors occur.

### Safe Temporary Files

You **SHOULD** use `mktemp` with cleanup traps for temporary files:

```bash
TMPDIR="$(mktemp -d)" || { err "Failed to create temp dir"; exit 1; }
trap 'rm -rf -- "$TMPDIR"' EXIT
```

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
│   └── script.sh
├── tests/
│   ├── script.bats
│   ├── test_helper.sh
│   └── fixtures/
└── README.md
```

### Basic Test File

```bash
#!/usr/bin/env bats

setup() {
  # Runs before each test
  source "${BATS_TEST_DIRNAME}/../bin/script.sh"
}

teardown() {
  # Runs after each test
  rm -rf "${BATS_TEST_TMPDIR:-}"
}

@test "script prints usage with --help" {
  run script.sh --help
  [ "$status" -eq 0 ]
  [[ "$output" == *"Usage:"* ]]
}

@test "script fails with missing argument" {
  run script.sh
  [ "$status" -ne 0 ]
  [[ "$output" == *"Missing"* ]]
}
```

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

```yaml
# .github/workflows/test.yml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install bats
        run: npm install --global bats
      - name: Run tests
        run: bats tests/
```

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
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: shellcheck
        uses: ludeeus/action-shellcheck@master
        with:
          scandir: './scripts'
      - name: shfmt
        uses: mvdan/sh@v0.7
        with:
          shfmt: true
```

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
