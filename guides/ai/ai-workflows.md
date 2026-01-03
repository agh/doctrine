# AI-Assisted Development Workflows

> [Doctrine](../../README.md) > [AI](README.md) > AI Workflows

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

## Overview

This guide defines universal workflows for AI-assisted development that work across
all AI coding tools (Claude Code, Gemini, GitHub Copilot, Cursor, Aider, etc.).
Tool-specific configuration is covered in separate guides.

---

## Table of Contents

1. [The Hero Flow](#the-hero-flow)
2. [TDD and the 3-Way Compare](#tdd-and-the-3-way-compare)
3. [Visual Iteration](#visual-iteration)
4. [Long-Running Tasks](#long-running-tasks)
5. [Verification Loops](#verification-loops)

---

## The Hero Flow

Every significant AI-assisted task **MUST** follow the Hero Flow:

```text
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ EXPLORE │ → │  PLAN   │ → │  CODE   │ → │ VERIFY  │ → │ COMMIT  │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
```

### Why This Matters

| Skipped Step | Consequence |
| ------------ | ----------- |
| Explore | AI guesses at architecture, creates inconsistent code |
| Plan | AI takes wrong approach, requires rework |
| Verify | Bugs ship, CI fails, time wasted |
| Commit | Work lost, no documentation of changes |

Verification is the most impactful step — it **2-3x the quality** of results[^1].

### 1. Explore

**MUST** read and understand before writing any code.

```text
Read the authentication code in src/auth/ and explain:
1. How login currently works
2. Where tokens are stored
3. What middleware validates requests

Don't write any code yet.
```

**Trigger deeper analysis** with explicit thinking requests:

| Phrase | Depth |
| ------ | ----- |
| "think about" | Basic reasoning |
| "think step-by-step" | Structured analysis |
| "think hard" | Thorough consideration |
| "think very carefully" | Deep analysis |
| "analyze thoroughly" | Maximum depth |

```text
Think step-by-step about how we should add OAuth2 support
alongside the existing JWT auth. Consider:
- Backwards compatibility
- Session management
- Token refresh flows
```

### 2. Plan

**MUST** align on approach before implementation.

```text
Create a detailed plan for adding OAuth2 support.
Include:
1. Files to create/modify
2. Order of changes
3. Testing approach
4. Potential risks

Don't implement yet — let's align on the plan first.
```

**MUST** get explicit confirmation:

```text
Does this plan look right? Any concerns before I implement?
```

**Why planning matters:**

- Catches misunderstandings early (cheap to fix)
- Aligns AI's approach with your expectations
- Creates documentation of decisions
- Prevents wasted implementation effort

### 3. Code

Implement in focused iterations:

```text
Implement step 1 from our plan: Create the OAuth2 provider interface.
Follow the patterns in src/auth/providers/.
```

**Best practices:**

- Implement one step at a time
- Reference the plan explicitly
- Follow existing patterns
- Keep changes focused
- Don't let AI "improve" unrelated code

### 4. Verify

**This is the most important step.** Without verification, AI output quality is
inconsistent.

```text
Verify your implementation:
1. Run the tests
2. Run the linter
3. Check types
4. Try the happy path manually

Report any failures and fix them.
```

**Types of verification:**

- **Automated**: Tests, linters, type checkers
- **Visual**: Screenshots, UI inspection
- **Manual**: Try the feature yourself
- **Review**: Have AI (or human) review the changes

### 5. Commit

**MUST** document changes properly:

```text
Create a commit for this change. Include:
1. What changed and why
2. Any migration steps needed
3. Update relevant documentation
```

**Commit checklist:**

- [ ] All tests passing
- [ ] Linter passing
- [ ] Types checking
- [ ] Documentation updated
- [ ] Commit message explains "why"

---

## TDD and the 3-Way Compare

When working with AI, **MUST** maintain alignment between three artifacts:

```text
              ┌──────────────┐
              │     SPEC     │
              │  (What we    │
              │   want)      │
              └──────┬───────┘
                     │
             ┌───────┴───────┐
             │               │
             ▼               ▼
     ┌──────────────┐ ┌──────────────┐
     │    TESTS     │ │    CODE      │
     │  (How we     │ │  (How we     │
     │   verify)    │ │   build)     │
     └──────────────┘ └──────────────┘
```

### The 3-Way Compare

All three **MUST** align:

| Artifact   | Contains                          | Source of Truth For   |
| ---------- | --------------------------------- | --------------------- |
| **Spec**   | Requirements, acceptance criteria | *What* we're building |
| **Tests**  | Assertions, expected behavior     | *Whether* it works    |
| **Code**   | Implementation                    | *How* it works        |

### When They Diverge

| Mismatch     | Meaning                     | Fix                |
| ------------ | --------------------------- | ------------------ |
| Spec ≠ Tests | Tests verify wrong behavior | Fix tests          |
| Spec ≠ Code  | Code does wrong thing       | Fix code           |
| Tests ≠ Code | Tests fail                  | Fix code (usually) |

### TDD Workflow with AI

```text
# Step 1: Write the spec (in conversation or document)
I need a function that:
- Takes a list of products
- Filters to in-stock items
- Sorts by price ascending
- Returns top 5

# Step 2: Have AI write tests FIRST
Write tests for this function based on the spec above.
Include:
- Happy path with mixed stock status
- Empty list
- All out of stock
- Fewer than 5 items
- Price ties

Don't implement the function yet.

# Step 3: Verify tests fail
Run the tests and confirm they fail (function doesn't exist yet).

# Step 4: Implement to pass tests
Now implement the function to make all tests pass.

# Step 5: Verify alignment
Review: Does the implementation match the original spec?
Are there any edge cases in the spec not covered by tests?
```

### Why TDD with AI?

Without tests, you're trusting AI's interpretation blindly:

```text
# BAD: No verification possible
Write a function that filters products by stock status.

# AI writes code... but how do we know it's correct?
```

With tests, correctness is verifiable:

```text
# GOOD: Tests define correctness
Write tests for a function that filters products where inStock === true.
Then implement to pass the tests.
```

### Anti-Patterns

| Anti-Pattern                       | Problem                               | Fix                         |
| ---------------------------------- | ------------------------------------- | --------------------------- |
| Code first, tests later            | Tests written to match code, not spec | Write tests first           |
| Spec only in your head             | AI can't read your mind               | Write spec explicitly       |
| Tests without edge cases           | False confidence                      | List edge cases in spec     |
| Skipping failing test verification | Tests might not test anything         | Always verify failure first |

---

## Visual Iteration

Visual iteration is **essential** for UI development. AI cannot "see" rendered
output without explicit feedback.

```text
┌─────────────────────────────────────────────────────────┐
│                                                          │
│   Describe ──→ Implement ──→ Screenshot ──→ Compare     │
│       ▲                                        │        │
│       │                                        │        │
│       └────────────── Iterate ◄────────────────┘        │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Why Visual Iteration Matters

Without screenshots, AI cannot detect:

- CSS rendering issues
- Layout and spacing problems
- Design system violations
- Responsive breakpoint issues
- Visual regressions

### Visual Iteration Workflow

```text
# Step 1: Provide design reference
Here's a screenshot of our design mockup for the login page.
[paste screenshot or image]

# Step 2: Initial implementation
Implement this design using our component library.

# Step 3: Screenshot the result
Take a screenshot of http://localhost:3000/login
(or paste screenshot manually)

# Step 4: Compare and iterate
Compare the screenshot to the mockup. I see:
- Header alignment is off
- Button color doesn't match
- Spacing below form is too large

Fix these issues.

# Step 5: Screenshot again
Take another screenshot and verify the fixes.

# Step 6: Repeat until match
Continue iterating until the implementation matches the design.
```

### Minimum Iterations

**SHOULD** iterate at least 2-3 times:

| Pass | Focus                  |
| ---- | ---------------------- |
| 1st  | Structure and layout   |
| 2nd  | Styling and spacing    |
| 3rd  | Polish and edge cases  |

### Visual Context to Provide

| Context             | Purpose            |
| ------------------- | ------------------ |
| Design mockups      | Target to match    |
| Current screenshots | Starting point     |
| Similar components  | Pattern to follow  |
| Error states        | Edge case designs  |
| Mobile views        | Responsive targets |

### Tools for Visual Iteration

- **Manual**: Paste screenshots into conversation
- **Browser extensions**: Auto-capture tools
- **Puppeteer/Playwright**: Programmatic screenshots
- **Visual regression**: CI-based comparison

---

## Long-Running Tasks

AI can work on complex tasks for extended periods (hours to days) with proper
setup.

### Enabling Long-Running Tasks

**Requirements:**

1. **Clear completion criteria** — AI needs to know when it's done
2. **Verification loops** — Automated checks between steps
3. **Permission automation** — Avoid blocking on prompts
4. **Progress persistence** — Handle context limits

### Completion Criteria

**MUST** define explicit completion criteria:

```text
This task is complete when:
1. All tests pass (npm test exits 0)
2. Linter passes (npm run lint exits 0)
3. Type check passes (npm run typecheck exits 0)
4. The feature works end-to-end (manual verification)
5. Documentation is updated

Keep working until all criteria are met.
```

### Verification Between Steps

**SHOULD** verify after each significant change:

```text
After each file you modify:
1. Run relevant tests
2. Run linter on that file
3. Verify no type errors introduced

Only proceed if all checks pass.
```

### Handling Context Limits

Long tasks may exceed context windows. Strategies:

| Strategy             | When to Use                    |
| -------------------- | ------------------------------ |
| Periodic summaries   | "Summarize progress so far"    |
| Checkpoint files     | Write progress to PROGRESS.md  |
| Conversation forking | Branch for exploration         |
| Task decomposition   | Break into smaller tasks       |

### Long-Running Task Checklist

Before starting:

- [ ] Completion criteria defined
- [ ] Verification steps specified
- [ ] Permission prompts minimized
- [ ] Progress tracking planned
- [ ] Backup/checkpoint strategy

---

## Verification Loops

Verification loops are the single most important pattern for quality.

### The Verification Loop

```text
┌─────────────────────────────────────────┐
│                                          │
│   Implement ──→ Check ──→ Pass? ──→ Done │
│       ▲                     │            │
│       │                    No            │
│       └──────── Fix ◄───────┘            │
│                                          │
└─────────────────────────────────────────┘
```

### Types of Verification

| Type                | Examples                   | Automation      |
| ------------------- | -------------------------- | --------------- |
| **Tests**           | Unit, integration, E2E     | Fully automated |
| **Static analysis** | Linter, type checker       | Fully automated |
| **Visual**          | Screenshots, UI review     | Semi-automated  |
| **Manual**          | Try the feature            | Human required  |
| **Review**          | Code review, security scan | AI or human     |

### Verification Prompt Pattern

```text
After implementing, verify by:
1. Running: [specific commands]
2. Checking: [specific conditions]
3. Testing: [specific scenarios]

If any check fails:
1. Analyze the failure
2. Fix the issue
3. Re-run all checks
4. Repeat until all pass

Only report complete when all verification passes.
```

### Why Verification 2-3x Quality

Without verification:

- AI doesn't know if code works
- Errors compound across steps
- False confidence in completion

With verification:

- Immediate feedback on errors
- Self-correction capability
- Validated completion

---

## Tool-Specific Guides

For tool-specific configuration:

- [Claude Code CLI](claude-code.md) — Hooks, permissions, subagents, commands
- [AGENTS.md Patterns](agents-md.md) — Project context files

---

## See Also

- [Testing Guide](../process/testing.md) — TDD and testing strategies
- [Claude Best Practices](claude.md) — Claude-specific patterns

---

## References

[^1]: Boris Cherny (Claude Code creator) on verification: "probably the most
    important thing to get great results out of Claude Code — give Claude a way
    to verify its work. If Claude has that feedback loop, it will 2-3x the
    quality of the final result."
