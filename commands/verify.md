# /verify Command

Run all verification checks with optional self-healing, time-travel debugging, and contract verification.

## Usage

```text
/verify              # Standard verification
/verify --fix        # Self-healing mode (auto-fix issues)
/verify --quick      # Quick mode (restore + types + build only)
/verify --full       # Full mode (includes security + coverage)
/verify --pr         # PR mode (post results as PR comment)
/verify --bisect     # Find when a test started failing
/verify --contract   # Verify PR claims match code changes
```

## Flags

| Flag | Description |
| ---- | ----------- |
| `--fix` | Enable self-healing: automatically fix lint, format, and type errors |
| `--quick` | Run only: restore → types → build |
| `--full` | Run all checks including security scanning and coverage |
| `--pr` | Post results as PR comment with inline annotations |
| `--continue` | Don't stop on first failure |
| `--bisect` | Time-travel: binary search to find breaking commit |
| `--bisect --good <ref>` | Specify known good commit for bisect |
| `--bisect --test "<cmd>"` | Specific test command for bisect |
| `--contract` | Verify PR description claims match actual code |
| `--contract --strict` | Fail on any contract mismatch |

## Behavior

1. **Auto-detect** ecosystem from the manifest and package manager from the lockfile
2. **Run Stage 1** (sequential): Immutable dependency restore
3. **Run Stage 2** (parallel): Lint, Types, Format, Security*
4. **Run Stage 3** (sequential): Build → Tests → Coverage*
5. **Self-heal** (if `--fix`): Auto-fix, then re-run the whole affected stage
6. **Report** results in table format with timing

*Security and Coverage only run with `--full` flag

Stage 1 **MUST** complete before any other command runs. Linters, formatters,
type checkers and test runners are project dependencies, so invoking them in a
clean checkout exits 127 (`command not found`) and reports a tooling failure as
a code failure.

## Implementation

Use the verify-build agent with these instructions:

```markdown
Run verification checks on this codebase.

## Auto-Detection

Detect the ecosystem from the manifest and the package manager from the
lockfile. The manifest alone **MUST NOT** decide the package manager.

| Manifest | Lockfile | Ecosystem | Package manager |
| -------- | -------- | --------- | --------------- |
| `package.json` | `package-lock.json` | Node.js | npm |
| `package.json` | `pnpm-lock.yaml` | Node.js | pnpm |
| `package.json` | `yarn.lock` | Node.js | Yarn Berry |
| `pyproject.toml` | `uv.lock` | Python | uv |
| `Cargo.toml` | `Cargo.lock` | Rust | Cargo |
| `go.mod` | `go.sum` | Go | Go modules |
| `Gemfile` | `Gemfile.lock` | Ruby | Bundler |

A manifest with no matching lockfile **MUST** be reported as
`Dependencies: FAIL — no lockfile, cannot restore reproducibly` and the run
**MUST** stop. Never generate a lockfile to make the run proceed.

## Verification Pipeline

### Stage 1 - Restore (sequential, always first)

Run exactly one immutable restore before any other command.

| Package manager | Restore command |
| --------------- | --------------- |
| npm | `npm ci` |
| pnpm | `pnpm install --frozen-lockfile` |
| Yarn Berry | `yarn install --immutable` |
| uv | `uv sync --locked` |
| Cargo | `cargo fetch --locked` |
| Go modules | `go mod download && go mod verify` |
| Bundler | `bundle config set --local frozen true && bundle install` |

Why: each command refuses to rewrite the lockfile, so verification cannot
silently upgrade a dependency, and a manifest that has drifted from its
lockfile fails loudly instead of resolving to something the team never pinned.

After the restore, confirm the lockfile is untouched with
`git diff --exit-code -- <lockfile>`. A modified lockfile **MUST** fail the run.

### Stage 2 - Static checks (parallel, after Stage 1)

Prefer the project's own scripts. Fall back to the tool only when no script
exists, and always name the paths to inspect.

- **Lint**: `npm run lint` / `uv run ruff check .` / `cargo clippy --all-targets`
  / `go vet ./...`
- **Types**: `npm run typecheck` / `uv run pyright` / (compiler) / (compiler)
- **Format**: `npm run format:check` / `uv run ruff format --check .`
  / `cargo fmt --all --check` / `test -z "$(gofmt -l .)"`

Every formatter and linter invocation **MUST** name the paths it inspects and
**MUST** fail on a non-zero exit.

Do: `prettier --check "src/**/*.ts"` inspects the named files and exits 1 when
one of them is unformatted.

Don't: `prettier --check` has no path, prints
`No parser and no file path given, couldn't infer a parser.` and exits 0. It
inspects nothing and reports PASS.

Don't: `gofmt -l .` prints the unformatted files and still exits 0. Wrap it as
`test -z "$(gofmt -l .)"` so the check actually fails.

### Missing tools

After a successful Stage 1, a tool that is still absent **MUST** be reported
`SKIP (tool not installed)` and never `PASS`. If the manifest declares the
script or dependency but the binary is missing, report `FAIL`: the restore did
not deliver a declared dependency.

### Stage 3 - Build and test (sequential, after Stage 2)

1. **Build**: `npm run build` / `uv build` / `cargo build --locked`
   / `go build ./...`
2. **Tests**: `npm test` / `uv run pytest` / `cargo test --locked`
   / `go test ./...`

### Security (--full only)

- Dependency audit: `npm audit --audit-level=high` / `uv run pip-audit`
  / `cargo audit`
- Secret scan: `gitleaks git --redact .` in a git checkout, or
  `gitleaks dir --redact .` in an export with no history
- SAST: `semgrep scan --error --config auto`

Gitleaks **MUST** be v8.19.0 or newer, which is where `detect` and `protect`
were deprecated and hidden in favour of the `git`, `dir` and `stdin` modes;
v8.30.1 (released 2026-03-21) is the current release. Gitleaks exits 1 when it
finds a leak, so no extra exit-code handling is required.

### Coverage (--full only)

- `npm run test:coverage` / `uv run pytest --cov` / `cargo llvm-cov`

## Self-Healing (--fix mode)

When a check fails:
1. Capture error output
2. Analyse root cause
3. Apply fix (lint --fix, format, add types)
4. Re-run **every check in the affected stage**, not only the failed command
5. Loop until the stage passes OR max 3 attempts

Why: an auto-fix rewrites source files. A formatter write can break a lint
rule and a lint fix can break type inference, so re-running only the failed
command reports a pass that the full stage would not give.

**Guardrails**: NEVER modify test assertions, delete tests, suppress rules, or
edit a lockfile. Lockfile drift **MUST** fail the run and **MUST NOT** be
auto-fixed.

## Output Format

## Build Verification Report

### Status: [PASS/FAIL]

### Environment
- **Project**: [detected type]
- **Mode**: [verify/self-heal/quick/full/pr]
- **Time**: [total time]

### Results

| Check | Status | Time | Details |
| ----- | ------ | ---- | ------- |
| Dependencies | ✅/❌ | Xs | |
| Build | ✅/❌ | Xs | |
| Type Check | ✅/❌ | Xs | |
| Lint | ✅/⚠️→✅/❌ | Xs | [auto-fixed count] |
| Tests | ✅/❌ | Xs | X passed, Y failed |
| Format | ✅/❌ | Xs | |
| Security | ✅/⚠️/❌ | Xs | [vulnerability count] |
| Coverage | ✅/⚠️ | Xs | X% (target: Y%) |

### Self-Healing Actions (if --fix)

| File | Issue | Fix Applied | Result |
| ---- | ----- | ----------- | ------ |
| ... | ... | ... | ✅/❌ |

### Failures

[Specific errors with file:line and suggested fixes]

### Recommended Next Steps

1. [Actionable item]
2. [Actionable item]
```

## Examples

### Basic Verification

```text
> /verify
Running verification on Node.js project...

## Build Verification Report

### Status: PASS

| Check | Status | Time |
| ----- | ------ | ---- |
| Dependencies | ✅ | 2.1s |
| Build | ✅ | 4.8s |
| Type Check | ✅ | 1.3s |
| Lint | ✅ | 2.7s |
| Tests | ✅ | 6.2s |
| Format | ✅ | 0.9s |

All checks passed in 18.0s
```

### Self-Healing Mode

```text
> /verify --fix
Running verification with self-healing...

### Self-Healing Actions

| File | Issue | Fix Applied | Result |
| ---- | ----- | ----------- | ------ |
| src/api.ts | Missing semicolon | ESLint --fix | ✅ Fixed |
| src/utils.ts | Unused import | ESLint --fix | ✅ Fixed |

### Status: PASS (2 issues auto-fixed)
```

## See Also

- [verify-build agent](../agents/system/verify.md) — Full agent specification
- [AI Workflows](../guides/ai/ai-workflows.md) — Hero Flow patterns
