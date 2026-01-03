# Code Agent Family Guide

> [Doctrine](../../README.md) > [AI](./README.md) > Code Agents

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

## Quick Reference

| Command | Agent | Model | Use Case |
|---------|-------|-------|----------|
| `/code` | Code Architect | Opus | Full code assessment |
| `/code quick` | Code Reviewer | Haiku | Fast scan, critical only |
| `/code review` | Code Reviewer | Sonnet | Standard code review |
| `/code perf` | Performance Reviewer | Sonnet | Performance analysis |
| `/code a11y` | Accessibility Reviewer | Sonnet | WCAG/A11y compliance |
| `/code api` | REST API Reviewer | Sonnet | REST API design |
| `/code api --graphql` | GraphQL API Reviewer | Sonnet | GraphQL schema design |
| `/code tests` | Test Writer | Sonnet | Test generation |
| `/code simplify` | Code Simplifier | Sonnet | Complexity reduction |
| `/code docs` | Doc Writer | Haiku | Documentation |

## Overview

The Doctrine Code Agent Family is a coordinated set of specialized AI agents
for comprehensive code analysis and generation. Unlike monolithic review tools,
this family provides:

1. **Specialized Expertise** - Each agent is an expert in its domain
2. **Cost Optimization** - Right model for each task (Haiku → Sonnet → Opus)
3. **Comprehensive Coverage** - From quick scans to deep architectural review
4. **Educational Focus** - Explains issues, not just flags them
5. **Auto-Fix Oriented** - Every issue includes remediation

## Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                       DOCTRINE CODE AGENT FAMILY                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                      ┌────────────────────────────┐                         │
│                      │     CODE ARCHITECT         │                         │
│                      │    (Opus - Coordinator)    │                         │
│                      └─────────────┬──────────────┘                         │
│                                    │                                         │
│  ┌──────────┬──────────┬──────────┼──────────┬──────────┬──────────┐       │
│  ▼          ▼          ▼          ▼          ▼          ▼          ▼       │
│ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌──────┐│
│ │ CODE   │ │PERFORM-│ │ACCESS- │ │  API   │ │  API   │ │ TEST   │ │SIMPL-││
│ │REVIEWER│ │ ANCE   │ │IBILITY │ │  REST  │ │GRAPHQL │ │ WRITER │ │IFIER ││
│ │(Sonnet)│ │(Sonnet)│ │(Sonnet)│ │(Sonnet)│ │(Sonnet)│ │(Sonnet)│ │(Son.)││
│ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └──────┘│
│                                                                              │
│ ┌────────────────────────────────────────────────────────────────────────┐  │
│ │                        SUPPORTING AGENTS                               │  │
│ │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │  │
│ │  │  DOC WRITER  │  │   VERIFY     │  │   (Future)   │                 │  │
│ │  │   (Haiku)    │  │    BUILD     │  │              │                 │  │
│ │  │              │  │  (Sonnet)    │  │              │                 │  │
│ │  └──────────────┘  └──────────────┘  └──────────────┘                 │  │
│ └────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Agent Specifications

### Tier 1: Strategic Coordinator

#### Code Architect

The **Code Architect** is the strategic coordinator for all code review efforts.

| Attribute | Value |
|-----------|-------|
| **Model** | Opus 4.5 |
| **Command** | `/code` |
| **File** | `configs/claude/agents/code/architect.md` |

**Responsibilities**:

- Assess overall code quality and architecture
- Route to appropriate specialist agents
- Synthesize findings across domains
- Provide prioritized remediation roadmap

**When to Use**:

- Comprehensive code review
- Cross-cutting concerns (security + performance + quality)
- Major feature reviews
- Pre-merge gates for critical code

---

### Tier 2: Domain Specialists

#### Code Reviewer

General-purpose code review with modes.

| Attribute | Value |
|-----------|-------|
| **Model** | Sonnet 4.5 (quick: Haiku) |
| **Command** | `/code review`, `/code quick` |
| **File** | `configs/claude/agents/code/reviewer.md` |

**Modes**:

- **Quick** (Haiku): Critical issues only, <50 LOC
- **Standard** (Sonnet): Security, performance, quality
- **Deep** (Sonnet→Opus): Architecture, patterns, edge cases

**Coverage**:

- Security (OWASP Top 10 basics)
- Performance (N+1, memory, algorithms)
- Quality (complexity, duplication, naming)
- Tests (coverage, edge cases)

---

#### Performance Reviewer

Deep performance analysis.

| Attribute | Value |
|-----------|-------|
| **Model** | Sonnet 4.5 |
| **Command** | `/code perf` |
| **File** | `configs/claude/agents/code/performance.md` |

**Coverage**:

- Database queries (N+1, missing indexes)
- Memory patterns (leaks, allocation)
- Algorithmic complexity
- Caching strategies
- Connection pooling
- Async/queue patterns
- Observability instrumentation

---

#### Accessibility Reviewer

WCAG/A11y compliance specialist.

| Attribute | Value |
|-----------|-------|
| **Model** | Sonnet 4.5 |
| **Command** | `/code a11y` |
| **File** | `configs/claude/agents/code/accessibility.md` |

**Coverage**:

- WCAG 2.1 AA compliance
- ARIA patterns
- Keyboard navigation
- Screen reader compatibility
- Color contrast
- Focus management

**Unique Value**: Only AI tool with deep A11y analysis.

---

#### REST API Reviewer

REST API design specialist.

| Attribute | Value |
|-----------|-------|
| **Model** | Sonnet 4.5 |
| **Command** | `/code api` |
| **File** | `configs/claude/agents/code/api-rest.md` |

**Coverage**:

- RESTful conventions
- HTTP methods and status codes
- Pagination patterns
- Error response format
- Versioning strategy
- Rate limiting

---

#### GraphQL API Reviewer

GraphQL schema design specialist.

| Attribute | Value |
|-----------|-------|
| **Model** | Sonnet 4.5 |
| **Command** | `/code api --graphql` |
| **File** | `configs/claude/agents/code/api-graphql.md` |

**Coverage**:

- Schema design
- Query complexity
- N+1 prevention (DataLoader)
- Authorization patterns
- Naming conventions
- Deprecation strategy

---

#### Test Writer

Comprehensive test generation.

| Attribute | Value |
|-----------|-------|
| **Model** | Sonnet 4.5 |
| **Command** | `/code tests` |
| **File** | `configs/claude/agents/code/test-writer.md` |

**Coverage**:

- Mutation-first approach
- Property-based testing
- Visual regression testing
- Contract testing (Pact)
- E2E patterns
- Test data generation

---

#### Code Simplifier

Complexity reduction specialist.

| Attribute | Value |
|-----------|-------|
| **Model** | Sonnet 4.5 |
| **Command** | `/code simplify` |
| **File** | `configs/claude/agents/code/simplifier.md` |

**Coverage**:

- Cyclomatic complexity reduction
- Extract method opportunities
- Dead code removal
- Abstraction simplification
- Before/after metrics

---

### Tier 3: Supporting Agents

#### Doc Writer

Documentation generation.

| Attribute | Value |
|-----------|-------|
| **Model** | Haiku 3.5 |
| **Command** | `/code docs` |
| **File** | `configs/claude/agents/code/doc-writer.md` |

**Output**:

- API documentation
- README sections
- Code comments
- Architecture diagrams

---

## Language-Specific Review Checklists

Code agents **MUST** apply language-specific checks based on the file type being reviewed.

### Python Review Checklist

| Category | Check | Severity |
|----------|-------|----------|
| **Type Safety** | Type hints on public APIs | SHOULD |
| **Type Safety** | `typing.Optional` for nullable params | SHOULD |
| **Type Safety** | `from __future__ import annotations` (3.7+) | MAY |
| **Async** | `async def` without `await` calls | High |
| **Async** | Blocking calls in async functions | High |
| **Async** | `asyncio.run()` inside running event loop | Critical |
| **Resource Mgmt** | Context managers for file/DB handles | MUST |
| **Resource Mgmt** | Unclosed resources in exception paths | High |
| **Performance** | Mutable default arguments | High |
| **Performance** | String concatenation in loops | Medium |
| **Performance** | `list()` where generator sufficient | Low |
| **Security** | `pickle` with untrusted data | Critical |
| **Security** | `eval()` or `exec()` with user input | Critical |
| **Security** | SQL string formatting (not parameterized) | Critical |
| **Testing** | Missing `pytest.mark.asyncio` for async tests | Medium |
| **Testing** | `mock.patch` without `autospec=True` | Low |

### Go Review Checklist

| Category | Check | Severity |
|----------|-------|----------|
| **Errors** | Ignoring error returns (`_ = fn()`) | High |
| **Errors** | Naked `panic()` in library code | Critical |
| **Errors** | `log.Fatal()` in library code | High |
| **Concurrency** | Data races (shared state without sync) | Critical |
| **Concurrency** | Goroutine leaks (unbounded spawning) | High |
| **Concurrency** | Sending on closed channel | Critical |
| **Concurrency** | Missing `defer mu.Unlock()` pattern | High |
| **Resource Mgmt** | Missing `defer resp.Body.Close()` | High |
| **Resource Mgmt** | Missing `defer rows.Close()` | High |
| **Performance** | Passing large structs by value | Medium |
| **Performance** | String concatenation in loops | Medium |
| **Performance** | `append()` without pre-allocation hint | Low |
| **Security** | Unvalidated user input in `sql.Query` | Critical |
| **Security** | `unsafe` package without justification | High |
| **Testing** | `t.Parallel()` missing for independent tests | Low |
| **Testing** | Table-driven tests without subtests | Low |

### Rust Review Checklist

| Category | Check | Severity |
|----------|-------|----------|
| **Safety** | `unsafe` without safety comment | MUST FIX |
| **Safety** | `unwrap()` in library code | High |
| **Safety** | `expect()` without context message | Medium |
| **Safety** | Raw pointer dereference patterns | Critical |
| **Async** | Holding `Mutex` across `.await` | Critical |
| **Async** | Blocking in async context | High |
| **Async** | `tokio::spawn` without error handling | Medium |
| **Lifetimes** | Unnecessary `'static` bounds | Medium |
| **Lifetimes** | Missing lifetime elision opportunities | Low |
| **Performance** | `clone()` where borrow sufficient | Medium |
| **Performance** | `collect()` before `filter()` | Medium |
| **Performance** | `Box<dyn Trait>` where generic sufficient | Low |
| **Error Handling** | `anyhow` in library (vs `thiserror`) | Medium |
| **Error Handling** | Unused `Result` (missing `?` or handling) | High |
| **Testing** | Missing `#[should_panic]` for panic tests | Low |
| **Testing** | No `proptest` for invariant-heavy code | MAY |

### TypeScript Review Checklist

| Category | Check | Severity |
|----------|-------|----------|
| **Type Safety** | `any` type usage | High |
| **Type Safety** | Non-null assertions (`!`) without justification | Medium |
| **Type Safety** | Missing return types on public APIs | SHOULD |
| **Type Safety** | `as` casts without type guards | Medium |
| **Async** | Missing `await` on Promise | Critical |
| **Async** | Floating Promises (not awaited or `.catch`) | High |
| **Async** | `async` function without `await` | Medium |
| **React** | Missing dependency in `useEffect` deps array | High |
| **React** | State mutation instead of `setState` | Critical |
| **React** | Missing `key` prop in lists | High |
| **React** | `useCallback`/`useMemo` without dependencies | High |
| **Performance** | Inline function in JSX props | Low |
| **Performance** | Re-renders from new object/array literals | Medium |
| **Security** | `dangerouslySetInnerHTML` without sanitization | Critical |
| **Security** | `eval()` or `Function()` usage | Critical |
| **Testing** | Missing `act()` wrapper for state updates | Medium |
| **Testing** | `waitFor` without assertion inside | Medium |

---

## Severity Levels

All findings use RFC 2119 severity levels:

| Level | Keyword | Meaning | Action Required |
|-------|---------|---------|-----------------|
| **Critical** | **MUST FIX** | Security vulnerability, data loss risk | Block merge |
| **High** | **MUST** | Significant bug or issue | Fix before merge |
| **Medium** | **SHOULD** | Improvement needed | Fix soon |
| **Low** | **MAY** | Minor enhancement | Consider |
| **Info** | N/A | Observation only | Awareness |

## Output Format

All code agents **MUST** use this output format:

````markdown
## Code Review: [Brief Title]

| Metric | Value |
|--------|-------|
| **Review Effort** | [1-5] |
| **Risk Level** | Low / Medium / High / Critical |
| **Change Size** | XS / S / M / L / XL |

### 🔴 Critical (must fix before merge)

- [ ] **[Category]**: [description] (`file:line`) — **[confidence]%**

  **Evidence**: [how we know this is an issue]

  **Before**:
  ```[lang]
  [problematic code]
  ```

  **After**:

  ```[lang]
  [fixed code]
  ```

  **Why**: [explanation]

### 🟡 Warning (should fix)

### 🔵 Suggestion (consider)

### ✅ Positive Observations

### Summary

[1-2 sentence overall assessment]

````

## Cost Optimization

| Agent | Model | Est. Cost/Invocation | Volume |
|-------|-------|---------------------|--------|
| Code Architect | Opus | $0.50 | Per PR (major) |
| Code Reviewer | Sonnet | $0.20 | Per PR |
| Code Reviewer Quick | Haiku | $0.02 | Per commit |
| Performance Reviewer | Sonnet | $0.25 | On request |
| Accessibility Reviewer | Sonnet | $0.20 | Frontend PRs |
| API Reviewers | Sonnet | $0.20 | API changes |
| Test Writer | Sonnet | $0.30 | On request |
| Code Simplifier | Sonnet | $0.25 | Post-feature |
| Doc Writer | Haiku | $0.02 | On request |

**Cost by Mode**:

| Mode | Typical Cost | Use Case |
|------|--------------|----------|
| `/code quick` | ~$0.02 | Every commit |
| `/code review` | ~$0.20 | PR review |
| `/code` | ~$0.80 | Full assessment |

## Workflow Examples

### Example 1: Standard PR Review

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant CA as Code Architect
    participant CR as Code Reviewer
    participant PR as Performance
    participant TW as Test Writer

    Dev->>CA: Opens PR
    CA->>CA: Analyze changes
    CA->>CR: Route to Code Reviewer
    CA->>PR: Performance-sensitive code detected
    CR-->>CA: 1 High, 3 Medium findings
    PR-->>CA: 1 N+1 query warning
    CA->>Dev: Consolidated Report
    Dev->>TW: "/code tests"
    TW-->>Dev: Generated tests
    Dev->>CA: Re-review
    CA-->>Dev: ✅ Approved
```

### Example 2: Frontend Review with A11y

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant CA as Code Architect
    participant CR as Code Reviewer
    participant A11y as Accessibility

    Dev->>CA: PR with React components
    CA->>CR: Code review
    CA->>A11y: Frontend detected
    CR-->>CA: Code quality OK
    A11y-->>CA: Missing ARIA labels
    CA->>Dev: A11y findings
    Dev->>Dev: Fix issues
    Dev->>CA: Re-review
    CA-->>Dev: ✅ Approved
```

## Configuration

### Enable Code Agents

Add to your project's `.claude/settings.json`:

```json
{
  "agents": {
    "code": {
      "enabled": true,
      "autoReview": true,
      "defaultMode": "standard",
      "a11yForFrontend": true
    }
  }
}
```

## Best Practices

### DO

- **MUST** run `/code review` on all PRs
- **MUST** run `/code a11y` on frontend changes
- **MUST** address Critical and High findings before merge
- **SHOULD** use `/code quick` for rapid iteration
- **SHOULD** run `/code tests` for new features
- **MAY** use `/code simplify` after feature completion

### DON'T

- **MUST NOT** ignore Critical findings
- **MUST NOT** skip review for "small" changes
- **SHOULD NOT** rely solely on quick mode for final review
- **SHOULD NOT** skip A11y review for user-facing changes

## See Also

- [Security Agent Family](./security-agents.md) — Security-focused agents
- [System Agent Family](./system-agents.md) — Infrastructure review agents
- [Claude Code CLI](./claude-code.md) — CLI configuration

---

*Last Updated: 2025-01-02*
*Version: 1.0.0*
