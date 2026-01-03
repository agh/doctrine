# /verify Command

Run all verification checks with optional self-healing, time-travel debugging, and contract verification.

## Usage

```text
/verify              # Standard verification
/verify --fix        # Self-healing mode (auto-fix issues)
/verify --quick      # Quick mode (deps + build + types only)
/verify --full       # Full mode (includes security + coverage)
/verify --pr         # PR mode (post results as PR comment)
/verify --bisect     # Find when a test started failing
/verify --contract   # Verify PR claims match code changes
```

## Flags

| Flag | Description |
| ---- | ----------- |
| `--fix` | Enable self-healing: automatically fix lint, format, and type errors |
| `--quick` | Run only: dependencies → build → types |
| `--full` | Run all checks including security scanning and coverage |
| `--pr` | Post results as PR comment with inline annotations |
| `--continue` | Don't stop on first failure |
| `--bisect` | Time-travel: binary search to find breaking commit |
| `--bisect --good <ref>` | Specify known good commit for bisect |
| `--bisect --test "<cmd>"` | Specific test command for bisect |
| `--contract` | Verify PR description claims match actual code |
| `--contract --strict` | Fail on any contract mismatch |

## Behavior

1. **Auto-detect** project type (Node.js, Python, Rust, Go, Ruby, etc.)
2. **Run Stage 1** (parallel): Lint, Types, Format, Security*
3. **Run Stage 2** (sequential): Dependencies → Build → Tests → Coverage*
4. **Self-heal** (if `--fix`): Auto-fix failures and re-verify
5. **Report** results in table format with timing

*Security and Coverage only run with `--full` flag

## Implementation

Use the verify-build agent with these instructions:

```markdown
Run verification checks on this codebase.

## Auto-Detection

First, detect project type:
- `package.json` → Node.js
- `pyproject.toml` → Python
- `Cargo.toml` → Rust
- `go.mod` → Go
- `Gemfile` → Ruby

## Verification Pipeline

### Stage 1 (Parallel)
Run these concurrently:
- **Lint**: `npm run lint` / `ruff check` / `cargo clippy`
- **Types**: `tsc --noEmit` / `pyright` / (built-in)
- **Format**: `prettier --check` / `ruff format --check` / `cargo fmt --check`

### Stage 2 (Sequential)
1. **Dependencies**: `npm install` / `uv sync` / `cargo fetch`
2. **Build**: `npm run build` / `uv build` / `cargo build`
3. **Tests**: `npm test` / `pytest` / `cargo test`

### Security (--full only)
- `npm audit` / `pip-audit` / `cargo audit`
- `gitleaks detect`
- `semgrep scan`

### Coverage (--full only)
- `npm run test:coverage` / `pytest --cov` / `cargo llvm-cov`

## Self-Healing (--fix mode)

When a check fails:
1. Capture error output
2. Analyze root cause
3. Apply fix (lint --fix, format, add types)
4. Re-run failed check
5. Loop until pass OR max 3 attempts

**Guardrails**: NEVER modify test assertions, delete tests, or suppress rules.

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

- [verify-build agent](../agents/verify-build.md) — Full agent specification
- [AI Workflows](../../guides/ai/ai-workflows.md) — Hero Flow patterns
