# /doc-status Command

Show documentation coverage, health metrics, and documentation debt inventory.

## Usage

```text
/doc-status
/doc-status src/                 # Check specific directory
/doc-status --detailed           # Show per-file breakdown
/doc-status --debt               # Show documentation debt inventory
/doc-status --trends             # Show metrics over time (if git history)
/doc-status --export json        # Export metrics as JSON
```

## Behavior

1. Scans codebase for documentable components
2. Maps existing documentation to source files
3. Calculates coverage metrics
4. Identifies gaps and staleness
5. Outputs health dashboard

## Output

Status dashboard including:

- Overall documentation coverage percentage
- Coverage by component type (APIs, modules, functions)
- Stale documentation count
- Undocumented public APIs
- Documentation health score

## Implementation

```markdown
Analyze documentation status for:

$ARGUMENTS

Calculate and report:
1. Coverage - What percentage of public APIs are documented?
2. Staleness - How many docs may be out of date?
3. Gaps - What important code lacks documentation?
4. Health - Overall documentation health score

Present as a dashboard with actionable insights.
```

## Example

```text
> /doc-status

## Documentation Status Dashboard

### Overall Health: 73% (Good)

┌─────────────────────────────────────────┐
│ Coverage      ████████████░░░░ 75%     │
│ Freshness     ██████████████░░ 85%     │
│ Completeness  ██████████░░░░░░ 60%     │
└─────────────────────────────────────────┘

### Coverage by Type

| Type | Documented | Total | Coverage |
| ---- | ---------- | ----- | -------- |
| API endpoints | 12 | 15 | 80% |
| Services | 5 | 7 | 71% |
| Utilities | 8 | 15 | 53% |

### Needs Attention

#### Undocumented (P0)
- `src/services/payment-service.ts` - Critical business logic
- `src/api/webhooks/` - External integration

#### Potentially Stale
- `docs/auth.md` - Source modified 15 days after doc
- `README.md` - Config section may be outdated

### Recommendations
1. Document payment-service.ts (high business impact)
2. Review auth.md against recent changes
3. Add examples to utility functions
```

## Health Score Calculation

```text
Health = (Coverage × 0.4) + (Freshness × 0.3) + (Completeness × 0.3)

Coverage = documented_public_apis / total_public_apis
Freshness = fresh_docs / total_docs
Completeness = docs_with_examples / total_docs
```

## Example: Debt Inventory

```text
> /doc-status --debt

## Documentation Debt Inventory

### Summary
- Total debt items: 47
- Critical (P0): 5
- Important (P1): 18
- Nice-to-have (P2): 24
- Estimated effort: 12-16 hours

### Critical Debt (P0) - Blocking Issues

| Item | Type | Impact | Age |
| ---- | ---- | ------ | --- |
| `PaymentService` | No docs | Revenue-critical | 45d |
| `auth/oauth2.ts` | Outdated | Security risk | 30d |
| `API rate limits` | Missing | Support tickets | 60d |
| `Error codes` | Incomplete | Developer friction | 22d |
| `Webhook events` | No examples | Integration failures | 38d |

### Important Debt (P1) - Should Fix

| Item | Type | Impact | Age |
| ---- | ---- | ------ | --- |
| 12 utility functions | No docstrings | Discoverability | varies |
| `DatabaseConfig` | Missing options | Setup confusion | 15d |
| Test utilities | No docs | Onboarding slow | 20d |
| ... | | | |

### Debt by Category

| Category | Count | % of Total |
| -------- | ----- | ---------- |
| Missing docs | 23 | 49% |
| Stale docs | 12 | 26% |
| Missing examples | 8 | 17% |
| Incomplete | 4 | 8% |

### Debt Trend (Last 90 Days)

```text
Debt Items
60 ┤
50 ┤     ╭──╮
40 ┤────╯  ╰────────
30 ┤
   └────────────────
     -90d        now

Debt reduced 17% this quarter

### Recommended Sprint Goals

1. Document PaymentService (P0, ~2 hours)
2. Update OAuth2 docs (P0, ~1 hour)
3. Add API rate limit docs (P0, ~30 min)
```

## Example: Trends

    > /doc-status --trends

    ## Documentation Metrics Trends

    ### Coverage (90 Days)

    100% ┤
     90% ┤          ╭────────
     80% ┤    ╭────╯
     70% ┤───╯
         └───────────────────
           -90d          now

    Current: 87% (+12% from 90d ago)

    ### Freshness (90 Days)

    100% ┤────╮
     90% ┤    ╰──────────────
     80% ┤
         └───────────────────
           -90d          now

    Current: 92% (-3% from 90d ago)
    Freshness declining - review stale docs

    ### Key Events

    | Date | Event | Impact |
    | ---- | ----- | ------ |
    | Dec 15 | Auth docs rewrite | +8% coverage |
    | Dec 01 | API v2 launch | -5% freshness |
    | Nov 20 | Doc sprint | +15% coverage |

    ### Velocity

    - Docs added this month: 12
    - Docs updated this month: 23
    - Average time to document new features: 3.2 days
