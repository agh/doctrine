# /doc-sync Command

Check if documentation is in sync with code changes. Supports auto-fix mode.

## Usage

```text
/doc-sync
/doc-sync --pr                   # Check files in current PR
/doc-sync src/auth/              # Check specific directory
/doc-sync --since HEAD~5         # Check recent commits
/doc-sync --versions             # Check version drift only
/doc-sync --fix                  # Auto-fix detected issues
/doc-sync --fix --dry-run        # Show what would be fixed
```

## Behavior

1. Invokes the **doc-sync** agent
2. Maps documentation files to source files
3. Detects signature and behavioral changes
4. Reports staleness with confidence levels
5. Suggests specific updates needed

## Output

Sync report including:

- Files analyzed and documentation coverage
- High-confidence staleness (code definitely changed)
- Medium-confidence staleness (likely needs review)
- Version drift (documented vs actual versions)
- Recommended actions
- Untracked code needing documentation

### With `--fix` Flag

Self-healing report including:

- Fixes applied automatically
- Issues requiring manual review
- PR created with changes (if any fixes applied)

## Implementation

```markdown
Invoke the doc-sync agent to check:

$ARGUMENTS

Analyze for documentation drift:
1. Map documentation to source files
2. Compare documented APIs to actual code
3. Detect signature changes (params, returns, errors)
4. Detect behavioral changes (new features, modified logic)
5. Identify undocumented code

Report staleness with confidence levels and specific fixes.
```

## Example

```text
> /doc-sync --pr

## Documentation Sync Report

### Summary
- Files changed in PR: 3
- Documentation affected: 2
- Staleness detected: 1 high, 1 medium

### High Confidence (MUST update)

| Doc File | Source | Change |
| -------- | ------ | ------ |
| docs/auth.md | src/auth.ts | New param: `mfaCode` |

### Medium Confidence (SHOULD review)

| Doc File | Source | Change |
| -------- | ------ | ------ |
| README.md | src/config.ts | New env var: `MFA_ENABLED` |

### Recommended Actions
1. Update docs/auth.md: Add `mfaCode` parameter to login()
2. Review README.md: Document MFA_ENABLED environment variable
```

## Example: Version Drift

```text
> /doc-sync --versions

## Version Drift Report

### Drift Detected

| File | Location | Documented | Actual | Source |
| ---- | -------- | ---------- | ------ | ------ |
| README.md | Line 15 | Node 18 | Node 20 | .nvmrc |
| docs/install.md | Line 32 | Python 3.10 | Python 3.12 | pyproject.toml |

### Consistent
- React: 18.2.0 (3 files)
- TypeScript: 5.3 (5 files)

### Recommendation
Run `/doc-sync --fix` to auto-update version numbers.
```

## Example: Self-Healing

```text
> /doc-sync --fix

## Self-Healing Report

### Fixes Applied

| File | Change | Confidence |
| ---- | ------ | ---------- |
| README.md:15 | Node 18 → Node 20 | 100% |
| docs/api.md:45 | Added `timeout` param to `fetch()` | 92% |
| docs/config.md:78 | Fixed broken link → guides/setup.md | 100% |

### Manual Review Required

| File | Issue | Reason |
| ---- | ----- | ------ |
| docs/auth.md | New OAuth2 flow | Needs architectural docs |

### PR Created
- Branch: `docs/auto-sync-2025-01-02`
- Title: "docs: auto-sync stale documentation"
- Changes: 3 files, 8 insertions, 4 deletions
```
