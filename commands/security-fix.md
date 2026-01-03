# /security-fix Command

Generate secure code fixes for identified vulnerabilities.

## Usage

```text
/security-fix <finding-id or file:line>
```

## Examples

```bash
# Fix specific finding by ID
/security-fix CRIT-001

# Fix vulnerability at location
/security-fix src/api/users.ts:42

# Fix all critical findings
/security-fix --severity critical

# Fix with PR creation
/security-fix CRIT-001 --pr
```

## Options

| Option | Description |
| ------ | ----------- |
| `--severity <level>` | Fix all findings at this severity or above |
| `--dry-run` | Show fixes without applying |
| `--pr` | Create PR with fixes |
| `--batch` | Fix multiple findings together |

## Behavior

1. **Remediation Generator** analyzes the vulnerability
2. Generates minimal, correct fix
3. Creates security regression tests
4. Produces PR-ready patch

## Output

    # Security Fix: [Finding ID]

    ## Summary
    [What was vulnerable and how it's fixed]

    ## Changes

    ### `src/api/users.ts`
    - const query = `SELECT * FROM users WHERE id = '${id}'`;
    + const user = await db('users').where({ id }).first();

    ### `tests/security/sql-injection.test.ts` (NEW)
    // Security regression test

    ## Verification
    - [ ] Run `npm test`
    - [ ] Verify exploit no longer works
    - [ ] Check existing functionality

## Implementation

```markdown
You are the Remediation Generator. Fix this security vulnerability:

$ARGUMENTS

Generate:
1. Minimal fix that resolves the vulnerability
2. Security test to prevent regression
3. Git diff/patch format for changes

Follow project coding standards.
Preserve existing functionality.
```

## Related Commands

- `/security` - Identify vulnerabilities
- `/review` - General code review
