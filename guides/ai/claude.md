# Claude/Anthropic Best Practices Guide

[AI Overview](README.md) → **Claude Best Practices**

## RFC 2119 Key Words

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

## Table of Contents

1. [Introduction](#introduction)
2. [Model Selection and Capabilities](#model-selection-and-capabilities)
3. [Claude Code CLI Patterns](#claude-code-cli-patterns)
4. [API Usage Patterns](#api-usage-patterns)
5. [Extended Thinking and Reasoning](#extended-thinking-and-reasoning)
6. [Multi-Agent Workflows](#multi-agent-workflows)
7. [Context and Prompt Engineering](#context-and-prompt-engineering)
8. [Common Pitfalls and Solutions](#common-pitfalls-and-solutions)
9. [Best Practices Summary](#best-practices-summary)
10. [Do/Don't Quick Reference](#dodont-quick-reference)

---

## Introduction

This guide provides comprehensive best practices for working with Anthropic's
Claude models[^1], including model selection, Claude Code CLI usage, API
patterns, and advanced techniques like extended thinking and multi-agent
workflows. Teams and individual developers MUST follow these guidelines to
maximize effectiveness, minimize costs, and ensure consistent high-quality
results when working with Claude.

### Scope

This guide covers:

- Strategic model selection across Opus, Sonnet, and Haiku tiers
- Claude Code CLI patterns and AGENTS.md conventions
- API usage including system prompts, temperature settings, and token management
- Extended thinking triggers and reasoning patterns
- Multi-agent workflow design and orchestration
- Common pitfalls and their solutions
- Concrete do/don't examples

### Audience

This guide is intended for:

- Software engineers using Claude for development
- DevOps engineers integrating Claude APIs
- Engineering managers establishing Claude usage standards
- AI/ML engineers building Claude-powered applications

---

## Model Selection and Capabilities

### Model Tiers Overview

Anthropic's Claude models are organized into three tiers, each optimized for
different use cases and cost profiles. Teams MUST understand these tiers to
make informed selection decisions.

#### Claude Opus 4.5

**Capabilities**:

- **Top-tier reasoning**: Most advanced analytical and reasoning capabilities
- **Complex problem-solving**: Multi-step reasoning, architectural decisions
- **Superior code quality**: Produces highest quality, most idiomatic code
- **Extended context mastery**: Excellent at utilizing full 200K token context
- **Nuanced understanding**: Best at understanding subtle requirements and edge cases

**Specifications**[^2]:

- Context window: 200K tokens
- Output limit: 16K tokens
- Latency: 3-10 seconds typical
- Cost (as of 2025): $15/1M input tokens, $75/1M output tokens

**Ideal Use Cases**:

- Architecture and system design decisions
- Security-critical code review and analysis
- Complex refactoring across multiple interconnected files
- High-stakes debugging of production issues
- Critical algorithm design and optimization
- Comprehensive security audits
- Mission-critical feature implementation

**When to Use Opus**:

```text
Use Opus when:
✓ Decision has high organizational impact
✓ Code affects security, compliance, or core business logic
✓ Problem requires deep multi-step reasoning
✓ Cost of error significantly exceeds cost of premium model
✓ Quality is paramount over speed
✓ Complex architectural trade-offs require evaluation

Typical scenarios:
- Designing microservices architecture
- Reviewing authentication/authorization code
- Analyzing race conditions in concurrent systems
- Refactoring core business logic
- Evaluating multiple technical approaches
- Creating comprehensive test strategies
```

#### Claude Sonnet 4.5

**Capabilities**:

- **Balanced performance**: Excellent quality-to-cost ratio
- **Fast response**: 2-5 second typical latency
- **Strong code generation**: Production-quality code for most tasks
- **Good reasoning**: Handles moderate complexity well
- **Versatile**: Suitable for 70-80% of development tasks

**Specifications**[^2]:

- Context window: 200K tokens
- Output limit: 16K tokens
- Latency: 1-5 seconds typical
- Cost (as of 2025): $3/1M input tokens, $15/1M output tokens

**Ideal Use Cases**:

- Feature implementation (standard complexity)
- Bug fixing and debugging
- Code reviews (non-security-critical)
- Test generation
- API integration
- Documentation generation
- Refactoring (standard patterns)
- General development assistance

**When to Use Sonnet**:

```text
Use Sonnet when:
✓ Standard development task with clear requirements
✓ Good quality needed but not mission-critical
✓ Balance of speed and quality is optimal
✓ Moderate complexity (most common case)
✓ Cost efficiency matters
✓ Iterative development with fast feedback

Typical scenarios:
- Implementing CRUD endpoints
- Adding validation logic
- Writing integration tests
- Updating API documentation
- Refactoring for readability
- Fixing non-critical bugs
- Generating boilerplate code
```

**Default Recommendation**: Sonnet SHOULD be the default choice for most
development work. It provides excellent results at a fraction of Opus cost,
making it ideal for daily development tasks.

#### Claude Haiku 3.5

**Capabilities**:

- **Ultra-fast responses**: Sub-second latency
- **Cost-effective**: Lowest cost per request
- **Good for simple tasks**: Handles straightforward, well-defined tasks
- **High throughput**: Ideal for batch processing

**Specifications**[^2]:

- Context window: 200K tokens
- Output limit: 8K tokens
- Latency: <1 second typical
- Cost (as of 2025): $0.25/1M input tokens, $1.25/1M output tokens

**Ideal Use Cases**:

- Code completion and autocomplete
- Simple documentation generation (docstrings, comments)
- Formatting and style fixes
- Straightforward CRUD generation
- Simple test data generation
- Quick code explanations
- High-volume processing tasks

**When to Use Haiku**:

```text
Use Haiku when:
✓ Task is simple and well-defined
✓ Speed is more important than perfection
✓ Processing high volume of similar requests
✓ Cost optimization is critical
✓ Task is repetitive or follows clear patterns
✓ Quick iteration is valuable

Typical scenarios:
- Generating 100 docstrings in batch
- Adding JSDoc comments to functions
- Creating simple test fixtures
- Formatting code snippets
- Generating mock data
- Code completion suggestions
```

### Model Selection Decision Matrix

Teams MUST use this decision matrix to select appropriate models:

```text
┌─────────────────────────────────────────────────────────────┐
│ DECISION MATRIX: CLAUDE MODEL SELECTION                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ Task Complexity:        [Low|Medium|High]                   │
│ Business Criticality:   [Low|Medium|High]                   │
│ Required Quality:       [Good|Excellent|Perfect]            │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Low Complexity + Low Criticality = HAIKU             │   │
│ │ Examples: Docstrings, formatting, simple CRUD        │   │
│ │ Cost per task: ~$0.001-0.01                          │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Medium Complexity + Medium Criticality = SONNET      │   │
│ │ Examples: Features, tests, refactoring, reviews      │   │
│ │ Cost per task: ~$0.01-0.20                           │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ High Complexity + High Criticality = OPUS            │   │
│ │ Examples: Architecture, security, critical bugs      │   │
│ │ Cost per task: ~$0.10-1.00                           │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ Exception Cases:                                             │
│ • High Criticality + Low Complexity → SONNET (not Opus)    │
│ • Low Criticality + High Complexity → SONNET (cost control)│
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Pricing Guidance and Cost Optimization

#### Understanding Token Costs

Teams MUST understand token economics to optimize spending:

**Input Token Costs (per 1M tokens)**:

- Haiku: $0.25 (baseline)
- Sonnet: $3.00 (12× Haiku)
- Opus: $15.00 (60× Haiku, 5× Sonnet)

**Output Token Costs (per 1M tokens)**:

- Haiku: $1.25 (baseline)
- Sonnet: $15.00 (12× Haiku)
- Opus: $75.00 (60× Haiku, 5× Sonnet)

**Practical Examples**:

```text
Scenario 1: Generate docstrings for 50 functions
Input: 25K tokens (function signatures + context)
Output: 10K tokens (docstrings)

Haiku cost:   ($0.25 × 0.025) + ($1.25 × 0.010) = $0.019
Sonnet cost:  ($3.00 × 0.025) + ($15.00 × 0.010) = $0.225
Opus cost:    ($15.00 × 0.025) + ($75.00 × 0.010) = $1.125

Recommendation: Haiku (quality sufficient for docstrings)
Savings: 91% vs Sonnet, 98% vs Opus

---

Scenario 2: Complex security audit of authentication system
Input: 100K tokens (full auth codebase)
Output: 20K tokens (detailed findings)

Haiku cost:   ($0.25 × 0.100) + ($1.25 × 0.020) = $0.050
Sonnet cost:  ($3.00 × 0.100) + ($15.00 × 0.020) = $0.600
Opus cost:    ($15.00 × 0.100) + ($75.00 × 0.020) = $3.000

Recommendation: Opus (security-critical requires best quality)
Cost justified: Finding one security bug worth 100× the cost

---

Scenario 3: Implement standard API endpoint
Input: 15K tokens (context + specs)
Output: 8K tokens (implementation + tests)

Haiku cost:   ($0.25 × 0.015) + ($1.25 × 0.008) = $0.014
Sonnet cost:  ($3.00 × 0.015) + ($15.00 × 0.008) = $0.165
Opus cost:    ($15.00 × 0.015) + ($75.00 × 0.008) = $0.825

Recommendation: Sonnet (balanced quality-cost for production code)
```

#### Cost Optimization Strategies

**Strategy 1: Model Cascading**

```text
Start with lower-tier model, escalate if needed:

1. Initial attempt with Sonnet
2. If result unsatisfactory, retry with Opus
3. Total cost often less than starting with Opus

Example:
- Sonnet attempt: $0.20 (70% success rate)
- Opus retry: $1.00 (30% of cases)
- Average cost: $0.50
- vs always using Opus: $1.00
Savings: 50%
```

**Strategy 2: Prompt Caching**[^3]

```text
Claude offers prompt caching for repeated context:

First request:
- Input: 50K tokens @ $3.00/1M = $0.15
- Output: 5K tokens @ $15.00/1M = $0.075
- Total: $0.225

Subsequent requests (within 5 minutes):
- Cached input: 50K tokens @ $0.30/1M = $0.015 (90% discount!)
- Output: 5K tokens @ $15.00/1M = $0.075
- Total: $0.090

Savings: 60% on subsequent requests

Best practices:
✓ Batch related tasks within 5-minute window
✓ Place stable context at beginning of prompt
✓ Reuse same system prompts
✓ Structure prompts with caching in mind
```

**Strategy 3: Context Minimization**

```text
Reduce input tokens without losing essential context:

Before optimization (60K tokens):
- Full file contents
- Extensive comments
- All imports
Cost: $0.18 input + output

After optimization (20K tokens):
- Relevant functions only
- Key type definitions
- Essential context
Cost: $0.06 input + output

Savings: 67% while maintaining quality

Techniques:
• Remove verbose comments for AI consumption
• Include only relevant code sections
• Summarize distant context
• Use file structure descriptions vs full files
```

### Model Upgrade/Downgrade Decision Framework

Teams SHOULD establish clear criteria for when to upgrade or downgrade models:

#### When to Upgrade from Haiku to Sonnet

```text
Upgrade if any condition is true:
□ Output quality is insufficient (requires rework)
□ Code generated has logical errors
□ Nuanced requirements are misunderstood
□ Task complexity was underestimated
□ Cost of fixing errors > cost of better model

Example:
Haiku generates function with bug → 10 min debugging
Sonnet generates correct function on first try
Time saved (10 min @ $150/hr) = $25
Cost difference (Sonnet - Haiku) = $0.15
ROI: 166:1 for using Sonnet
```

#### When to Upgrade from Sonnet to Opus

```text
Upgrade if any condition is true:
□ Security or compliance requirements
□ Complex multi-step reasoning required
□ Architectural decisions with broad impact
□ Debugging elusive production issues
□ Cost of error significantly exceeds model cost
□ Multiple Sonnet attempts have failed

Example:
Debugging race condition in payment system
3 Sonnet attempts: 3 × $0.60 = $1.80 (unsuccessful)
1 Opus attempt: $3.00 (identifies root cause)
Total: $4.80 with solution
vs continuing with Sonnet: diminishing returns
```

#### When to Downgrade from Sonnet to Haiku

```text
Downgrade if all conditions are true:
□ Task is simpler than initially assessed
□ Pattern is clear and well-defined
□ Quality requirements are flexible
□ Processing high volume of similar tasks
□ Speed is more valuable than perfection

Example:
Adding TypeScript types to 200 existing functions
Initial thought: Use Sonnet for quality
Actual: Pattern is consistent, types are simple
Haiku cost: 200 × $0.01 = $2.00
Sonnet cost: 200 × $0.15 = $30.00
Savings: 93% without quality impact
```

---

## Claude Code CLI Patterns

The Claude Code CLI[^4] is Anthropic's official command-line interface for
Claude, providing a powerful development environment. This section establishes
best practices for using Claude Code effectively.

### Core Concepts

#### What is Claude Code

Claude Code is:

- Official CLI tool from Anthropic
- Designed specifically for software development workflows
- Optimized for codebase understanding and manipulation
- Integrated with file system operations
- Supports extended thinking mode
- Enables structured multi-turn conversations

#### Key Features

**Codebase Awareness**:

```bash
# Claude Code can:
- Search across entire codebase
- Understand file relationships
- Maintain context across multiple files
- Execute terminal commands
- Read and write files directly
- Navigate project structure
```

**Extended Thinking**:

```bash
# Enable deeper reasoning for complex tasks
claude --extended-thinking "Design authentication system"

# Claude will:
1. Think through problem deeply before responding
2. Show reasoning process
3. Produce more thoughtful solutions
4. Consider edge cases more thoroughly
```

**Context Persistence**:

```bash
# Context is maintained across commands in a session
claude "Review authentication code"
# (Claude reads and analyzes auth files)

claude "Now add rate limiting to those endpoints"
# (Claude remembers previous analysis, no re-reading needed)
```

### AGENTS.md Pattern

The AGENTS.md file is a critical component of Claude Code workflow. It MUST be
used to provide essential codebase context. For Claude Code compatibility,
create a `CLAUDE.md` symlink pointing to `AGENTS.md`.

#### What is AGENTS.md

AGENTS.md is a markdown file at the root of your repository that provides:

1. **Project overview**: What the project does and why
2. **Technical stack**: Languages, frameworks, key dependencies
3. **Development commands**: Build, test, run, deploy
4. **Code conventions**: Style guide, patterns, preferences
5. **Architecture notes**: Key design decisions and structure
6. **Gotchas**: Common pitfalls and known issues

#### AGENTS.md Structure

A well-structured AGENTS.md MUST include these sections:

````markdown
# Project Name

## Overview
Brief description of what this project does and its purpose.

## Technical Stack
- **Language**: TypeScript 5.x
- **Framework**: Next.js 14
- **Database**: PostgreSQL 15
- **ORM**: Prisma
- **Testing**: Jest + React Testing Library
- **Deployment**: Vercel

## Getting Started

### Prerequisites
- Node.js 20+
- PostgreSQL 15+
- pnpm 8+

### Development Commands
```bash
# Install dependencies
pnpm install

# Start dev server
pnpm dev

# Run tests
pnpm test

# Build for production
pnpm build

# Run linter
pnpm lint
```

## Code Organization

```text
src/
├── app/           # Next.js app directory
├── components/    # React components
├── lib/           # Utility functions
├── services/      # Business logic
└── types/         # TypeScript types
```

## Code Conventions

### Style Guide

- Follow Airbnb TypeScript style guide
- Use functional components with hooks
- Prefer named exports over default exports
- Use absolute imports (e.g., @/components/...)

### Naming Conventions

- Components: PascalCase (e.g., UserProfile.tsx)
- Functions: camelCase (e.g., fetchUserData)
- Constants: UPPER_SNAKE_CASE (e.g., MAX_RETRY_COUNT)
- Files: kebab-case for non-components (e.g., user-service.ts)

### Testing Patterns

- Test files: *.test.ts or*.test.tsx
- Use describe/it for test structure
- Mock external dependencies
- Aim for >80% coverage

## Architecture Notes

### Authentication

Uses NextAuth.js with JWT strategy. Session tokens expire after 24 hours.
Refresh token rotation is enabled.

### Database Access

All database access MUST go through Prisma client. Direct SQL queries are
prohibited except in migrations.

### API Design

- RESTful endpoints under /api/v1/
- All responses include { success: boolean, data?: any, error?: string }
- Use HTTP status codes correctly (200, 201, 400, 401, 404, 500)

## Common Pitfalls

### Database Connections

DO NOT create new Prisma clients. Use the singleton from lib/db.ts

### Environment Variables

All env vars MUST be prefixed with NEXT_PUBLIC_ for client-side access

### Server Components

Be careful with 'use client' directive. Only use for interactive components.

## Known Issues

- Prisma client generation must run after schema changes
- Vercel edge functions have 1MB size limit
- WebSocket connections not supported on Vercel

## Additional Resources

- [API Documentation](./docs/api.md)
- [Architecture Decisions](./docs/adr/)
- [Contributing Guide](./CONTRIBUTING.md)
````

#### AGENTS.md Best Practices

**DO**:

```markdown
✓ Keep it under 500-1000 lines
✓ Include actual commands that work
✓ Provide code examples for conventions
✓ Update when project changes
✓ Version control the file
✓ Review with team for accuracy
✓ Link to detailed docs for deep dives
✓ Include ASCII diagrams for architecture
```

**DON'T**:

```markdown
✗ Include exhaustive documentation (link instead)
✗ Duplicate information from README
✗ Let it become outdated
✗ Include sensitive information
✗ Make it overly long or verbose
✗ Use it as a substitute for code comments
```

### Claude Code Usage Patterns

#### Pattern 1: Feature Implementation

```bash
# Step 1: Provide context via AGENTS.md (already in repo)
# Step 2: Start implementation conversation

claude "I need to add user profile editing functionality. \
Should include:
- Form to edit name, email, bio
- Avatar upload
- Validation
- API endpoint
- Tests

Start by analyzing existing user profile code and \
suggesting the implementation approach."

# Claude will:
1. Read AGENTS.md for context
2. Search for existing user profile code
3. Analyze current patterns
4. Propose implementation approach
5. Ask clarifying questions

# Step 3: Request implementation

claude "Implement the profile editing feature following \
the approach we discussed. Include all files needed."

# Step 4: Review and iterate

claude "The validation logic should also check for \
profanity in bio field"

# Step 5: Generate tests

claude "Generate comprehensive tests for the profile \
editing feature"
```

#### Pattern 2: Debugging with Context

```bash
# Provide error context to Claude

claude "Users are reporting 500 errors when updating \
their profiles. Here's the error from logs:

Error: Unique constraint violation on User.email
  at PrismaClient.user.update
  at updateUserProfile (services/user.ts:45)

Debug this issue and suggest a fix."

# Claude will:
1. Search for relevant code (services/user.ts)
2. Analyze the error pattern
3. Identify root cause
4. Suggest fix with explanation
5. Recommend tests to prevent regression
```

#### Pattern 3: Code Review

```bash
# Review code before committing

claude "Review the changes I just made to the authentication \
system. Check for:
- Security issues
- Edge cases not handled
- Performance concerns
- Code quality

Files changed:
- src/services/auth-service.ts
- src/app/api/auth/login/route.ts
- tests/auth.test.ts"

# Claude will:
1. Read all changed files
2. Analyze against security best practices
3. Identify potential issues
4. Suggest improvements
5. Validate tests are comprehensive
```

#### Pattern 4: Refactoring

```bash
# Request refactoring with extended thinking

claude --extended-thinking "The user-service.ts file has \
grown to 800 lines and is becoming hard to maintain. \
Refactor it following SOLID principles while maintaining \
all existing functionality."

# Extended thinking helps Claude:
1. Deeply analyze current structure
2. Identify cohesive responsibilities
3. Plan refactoring strategy
4. Consider migration path
5. Produce thoughtful refactoring
```

### Extended Thinking Triggers

Extended thinking mode causes Claude to show its reasoning process before
responding. This SHOULD be used for complex tasks requiring deep analysis.

#### When to Use Extended Thinking

```text
Use --extended-thinking flag when:
✓ Problem requires multi-step reasoning
✓ Architectural decisions needed
✓ Complex debugging scenarios
✓ Trade-off analysis required
✓ Security or performance critical
✓ Unfamiliar problem domain
✓ High cost of getting it wrong

Examples:
• "Design the database schema for our new feature"
• "Debug this race condition in our payment processing"
• "Evaluate whether to use GraphQL or REST for our API"
• "Refactor this module to improve testability"
• "Analyze the security implications of this auth change"
```

#### Extended Thinking Example

```bash
claude --extended-thinking "Should we use Redis or Memcached \
for caching user sessions in our high-traffic application?"

# Claude's thinking process (shown to user):
<thinking>
Let me analyze this caching decision systematically.

Current context from AGENTS.md:
- Next.js 14 application
- PostgreSQL database
- Deployed on Vercel
- High traffic mentioned

Key considerations:
1. Data structures needed for sessions
2. Performance requirements
3. Deployment environment constraints
4. Feature requirements

Redis advantages:
- Supports complex data structures (sessions often need hash maps)
- Built-in pub/sub (useful for session invalidation)
- Persistence options (session durability)
- Better for Vercel edge deployment

Memcached advantages:
- Simpler architecture
- Slightly faster for pure key-value
- Lower memory overhead

For session storage specifically:
- Sessions typically need hash-like structure (user data)
- May need pub/sub for multi-instance invalidation
- Persistence valuable to survive restarts
- Redis is better fit

Deployment consideration:
- Vercel works well with Upstash Redis (serverless Redis)
- Memcached less common in serverless environments

Recommendation: Redis
Primary reasons: Better data structures, pub/sub support,
serverless-friendly options
</thinking>

# Then Claude provides final answer:
[Detailed recommendation with code examples]
```

### Context Management in Claude Code

#### Automatic Context Assembly

Claude Code automatically provides context about:

```text
• File structure (via directory listing)
• File contents (when referenced or searched)
• Recent changes (via git if available)
• Terminal output (from executed commands)
• Conversation history (within session)
```

#### Explicit Context Provision

For optimal results, explicitly provide context:

```bash
# Method 1: Reference specific files
claude "Review src/services/auth-service.ts for security issues"

# Method 2: Provide code snippets in prompt
claude "Fix this function:
\`\`\`typescript
async function login(email: string, password: string) {
  const user = await db.query('SELECT * FROM users WHERE email = ' + email);
  // ...
}
\`\`\`
"

# Method 3: Specify scope
claude "Search all files in src/services/ for uses of deprecated
crypto library and update to new API"

# Method 4: Reference external context
claude "Implement the feature described in docs/feature-specs/
user-profiles.md following our patterns in AGENTS.md"
```

#### Context Optimization

To avoid exceeding context limits:

```bash
# DON'T: Overly broad requests
claude "Analyze the entire codebase and suggest improvements"
# Problem: May exceed context window, unfocused

# DO: Focused, scoped requests
claude "Analyze src/services/ directory for code duplication
and suggest consolidation opportunities"
# Better: Specific scope, clear goal

# DON'T: Repeated large context
claude "Review all authentication code" # First request
claude "Review all authentication code for security" # Repeat
# Problem: Re-reads same context unnecessarily

# DO: Build on previous context
claude "Review all authentication code" # First request
claude "Now focus on the security aspects we just discussed"
# Better: Leverages existing context
```

---

## API Usage Patterns

For teams integrating Claude via API[^5] rather than CLI, these patterns
establish best practices for system prompts, temperature settings, token
management, and more.

### System Prompts

System prompts set the behavior and expertise level of Claude. They MUST be
used to establish consistent behavior.

#### System Prompt Structure

```python
system_prompt = """You are an expert software engineer specializing in {domain}.

Your role:
- Write production-quality code following {style_guide}
- Prioritize security, performance, and maintainability
- Explain your reasoning and trade-offs
- Ask clarifying questions when requirements are ambiguous

Technical context:
- Primary language: {language}
- Framework: {framework}
- Code style: {conventions}

Constraints:
- Always include error handling
- Write comprehensive tests
- Document complex logic
- Follow {architecture_pattern} architecture

Response format:
- Provide code first, then explanation
- Include usage examples
- Highlight potential issues or edge cases
"""
```

#### System Prompt Best Practices

**DO**:

```python
# ✓ Be specific about role and expertise
system_prompt = "You are a senior Python developer specializing in
data processing pipelines using Apache Spark."

# ✓ Specify output format expectations
system_prompt += "\nAlways provide code with docstrings following
Google style guide."

# ✓ Include relevant constraints
system_prompt += "\nCode must be compatible with Python 3.11 and
handle PySpark DataFrame operations efficiently."

# ✓ Set quality expectations
system_prompt += "\nPrioritize code readability and maintainability.
Include error handling for edge cases."
```

**DON'T**:

```python
# ✗ Too vague
system_prompt = "You are a helpful assistant."

# ✗ Contradictory instructions
system_prompt = "Be extremely concise. Provide extensive explanations."

# ✗ Overly restrictive
system_prompt = "Never use any external libraries. Only use built-in
Python functions."
# Problem: Unnecessarily limits useful solutions

# ✗ Too long (wastes tokens)
system_prompt = """[5000 words of detailed instructions]"""
# Problem: Expensive and may reduce effectiveness
```

#### Domain-Specific System Prompts

**For Security Reviews**:

```python
security_review_prompt = """You are a security engineer conducting
code reviews for vulnerabilities.

Focus areas:
- SQL injection, XSS, CSRF vulnerabilities
- Authentication and authorization flaws
- Sensitive data exposure
- Insecure dependencies
- Cryptographic weaknesses

For each finding, provide:
1. Severity (Critical/High/Medium/Low)
2. Specific code location
3. Exploitation scenario
4. Remediation steps
5. Secure code example

Be thorough but avoid false positives. Only report actual vulnerabilities.
"""
```

**For Code Generation**:

```python
code_generation_prompt = """You are an expert {language} developer.

Generate code that:
- Follows {style_guide} conventions
- Includes comprehensive error handling
- Has type hints/annotations where applicable
- Includes docstrings/comments for public APIs
- Is production-ready and tested

When generating code:
1. First show the implementation
2. Then provide usage example
3. List any assumptions made
4. Highlight edge cases handled
"""
```

**For Refactoring**:

```python
refactoring_prompt = """You are a software engineer specializing in
code refactoring and technical debt reduction.

When refactoring:
- Preserve exact existing behavior
- Improve readability and maintainability
- Reduce complexity where possible
- Follow SOLID principles
- Maintain or improve performance

Always:
- Explain what changed and why
- Identify potential risks in the refactoring
- Suggest tests to validate behavior preservation
"""
```

### Temperature Settings

Temperature controls randomness in Claude's responses. Teams MUST use
appropriate temperature settings for different task types.

#### Temperature Guidelines

```python
# Temperature range: 0.0 to 1.0

# Temperature: 0.0-0.3 (Deterministic)
# Use for: Code generation, security reviews, factual Q&A
# Behavior: Highly consistent, focused on most likely correct answer
temperature = 0.0
response = client.messages.create(
    model="claude-sonnet-4-5-20250329",
    max_tokens=4096,
    temperature=0.0,  # Deterministic code generation
    messages=[{"role": "user", "content": "Generate login function"}]
)

# Temperature: 0.4-0.7 (Balanced)
# Use for: Refactoring, documentation, general assistance
# Behavior: Some variation, good balance of consistency and creativity
temperature = 0.5
response = client.messages.create(
    model="claude-sonnet-4-5-20250329",
    max_tokens=4096,
    temperature=0.5,  # Balanced refactoring suggestions
    messages=[{"role": "user", "content": "Suggest refactorings"}]
)

# Temperature: 0.8-1.0 (Creative)
# Use for: Brainstorming, multiple approaches, creative solutions
# Behavior: More varied responses, explores alternatives
temperature = 0.9
response = client.messages.create(
    model="claude-sonnet-4-5-20250329",
    max_tokens=4096,
    temperature=0.9,  # Creative architecture ideas
    messages=[{"role": "user", "content": "Suggest system architectures"}]
)
```

#### Temperature by Task Type

```python
TEMPERATURE_SETTINGS = {
    # Deterministic tasks (0.0-0.2)
    "code_generation": 0.0,
    "bug_fixing": 0.0,
    "security_review": 0.0,
    "test_generation": 0.1,
    "type_checking_fixes": 0.0,

    # Balanced tasks (0.3-0.6)
    "code_review": 0.4,
    "refactoring": 0.5,
    "documentation": 0.3,
    "api_design": 0.5,
    "optimization": 0.4,

    # Creative tasks (0.7-1.0)
    "architecture_design": 0.7,
    "brainstorming": 0.9,
    "naming_suggestions": 0.8,
    "alternative_approaches": 0.8,
    "creative_problem_solving": 0.7,
}

def get_temperature(task_type: str) -> float:
    """Get appropriate temperature for task type."""
    return TEMPERATURE_SETTINGS.get(task_type, 0.5)  # Default: balanced
```

### Token Management

Effective token management is critical for cost control and staying within limits.

#### Token Estimation

```python
import anthropic

def estimate_tokens(text: str) -> int:
    """
    Rough estimation: ~4 characters per token for English text.
    For code: ~3.5 characters per token (more dense).

    For exact count, use the tokenizer.
    """
    # Simple estimation
    return len(text) // 4

def count_tokens_exact(text: str, model: str) -> int:
    """
    Get exact token count using Anthropic's tokenizer.
    """
    client = anthropic.Anthropic()
    # Use the actual tokenizer when available
    # For now, use estimation
    return estimate_tokens(text)

# Example usage
code_snippet = """
def calculate_total(items: list[Item]) -> Decimal:
    return sum(item.price for item in items)
"""

estimated_tokens = estimate_tokens(code_snippet)
print(f"Estimated tokens: {estimated_tokens}")  # ~30 tokens
```

#### Context Window Management

```python
# Claude models have 200K token context windows
# Reserve tokens for output

MAX_CONTEXT_TOKENS = 200_000
RESERVED_OUTPUT_TOKENS = 16_000  # Max output for Opus/Sonnet
SAFE_INPUT_LIMIT = MAX_CONTEXT_TOKENS - RESERVED_OUTPUT_TOKENS  # 184K

def prepare_context(
    system_prompt: str,
    user_message: str,
    code_files: list[str],
    max_tokens: int = SAFE_INPUT_LIMIT
) -> tuple[str, list[str]]:
    """
    Prepare context within token budget.
    Priority: system prompt > user message > code files
    """
    tokens_used = 0

    # System prompt (highest priority, MUST include)
    system_tokens = estimate_tokens(system_prompt)
    tokens_used += system_tokens

    # User message (high priority, MUST include)
    user_tokens = estimate_tokens(user_message)
    tokens_used += user_tokens

    # Code files (include as many as fit)
    included_files = []
    for file_content in code_files:
        file_tokens = estimate_tokens(file_content)
        if tokens_used + file_tokens <= max_tokens:
            included_files.append(file_content)
            tokens_used += file_tokens
        else:
            break

    print(f"Total tokens: {tokens_used}/{max_tokens}")
    return system_prompt, included_files
```

#### Prompt Caching for Cost Savings

```python
from anthropic import Anthropic

client = Anthropic()

# Prompt caching[^3]: 90% discount on cached portions
# Cache duration: 5 minutes
# Minimum cache size: 1024 tokens

# Structure your prompt with cacheable content first
def create_cached_request(codebase_context: str, user_query: str):
    """
    Use prompt caching for repeated codebase context.
    """
    response = client.messages.create(
        model="claude-sonnet-4-5-20250329",
        max_tokens=4096,
        system=[
            {
                "type": "text",
                "text": "You are an expert code reviewer.",
            },
            {
                "type": "text",
                "text": codebase_context,  # Large, stable context
                "cache_control": {"type": "ephemeral"}  # Mark for caching
            }
        ],
        messages=[
            {"role": "user", "content": user_query}
        ]
    )

    # First request: Full cost for codebase_context
    # Subsequent requests (within 5 min): 90% discount on codebase_context

    return response

# Example: Review multiple files with same codebase context
codebase = """
[50K tokens of project structure, conventions, patterns]
"""

# First review: Full cost
review1 = create_cached_request(codebase, "Review auth-service.ts")
# Cost: ~$0.15 input + output

# Second review (within 5 min): 90% discount on codebase context
review2 = create_cached_request(codebase, "Review user-service.ts")
# Cost: ~$0.025 input (cached) + output

# Savings: ~60% on multi-file reviews
```

### Streaming Responses

Streaming[^6] provides immediate feedback and allows early termination.

```python
from anthropic import Anthropic

client = Anthropic()

def stream_response(prompt: str):
    """
    Stream Claude's response for immediate feedback.
    """
    with client.messages.stream(
        model="claude-sonnet-4-5-20250329",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)

    print()  # New line after stream completes

# Benefits:
# 1. Show progress to users immediately
# 2. Can cancel if response goes wrong direction
# 3. Better UX for long responses
# 4. No wait time for first token

# Example usage
stream_response("Implement user authentication system with JWT")
```

### Error Handling and Retry Logic

```python
import time
from anthropic import Anthropic, APIError, RateLimitError

client = Anthropic()

def call_claude_with_retry(
    prompt: str,
    max_retries: int = 3,
    backoff_factor: float = 2.0
) -> str:
    """
    Call Claude with exponential backoff retry logic.
    """
    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model="claude-sonnet-4-5-20250329",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text

        except RateLimitError as e:
            if attempt < max_retries - 1:
                wait_time = backoff_factor ** attempt
                print(f"Rate limited. Waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise

        except APIError as e:
            if attempt < max_retries - 1 and e.status_code >= 500:
                # Retry on server errors
                wait_time = backoff_factor ** attempt
                print(f"Server error. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise

    raise Exception("Max retries exceeded")

# Usage
try:
    result = call_claude_with_retry("Generate login function")
    print(result)
except Exception as e:
    print(f"Failed after retries: {e}")
```

---

## Extended Thinking and Reasoning

Extended thinking[^7] is a powerful feature that causes Claude to show its
reasoning process before providing an answer. This section covers when and
how to use it effectively.

### Understanding Extended Thinking

Extended thinking causes Claude to:

1. **Analyze the problem deeply** before responding
2. **Show its reasoning process** in `<thinking>` tags
3. **Consider multiple approaches** and trade-offs
4. **Identify edge cases** more thoroughly
5. **Produce more thoughtful solutions**

### When to Enable Extended Thinking

```text
Enable extended thinking for:
✓ Complex architectural decisions
✓ Security analysis and threat modeling
✓ Performance optimization strategies
✓ Debugging elusive or complex bugs
✓ Trade-off analysis between approaches
✓ Design pattern selection
✓ Algorithm design and optimization
✓ Refactoring complex legacy code

Skip extended thinking for:
✗ Simple code generation
✗ Straightforward bug fixes
✗ Documentation generation
✗ Formatting and style fixes
✗ Simple refactoring
✗ Well-defined, simple tasks
```

### Extended Thinking Examples

#### Example 1: Architecture Decision

```python
# Without extended thinking
response = client.messages.create(
    model="claude-opus-4-5-20250329",
    max_tokens=8192,
    messages=[{
        "role": "user",
        "content": "Should we use microservices or monolith for our e-commerce platform?"
    }]
)
# Response: Direct answer, may miss important considerations

# With extended thinking (via system prompt pattern)
response = client.messages.create(
    model="claude-opus-4-5-20250329",
    max_tokens=8192,
    system="Before answering, think step-by-step through the problem, considering all relevant factors, trade-offs, and implications. Show your reasoning in <thinking> tags before providing your final recommendation.",
    messages=[{
        "role": "user",
        "content": """Should we use microservices or monolith for our e-commerce platform?

Context:
- Team of 8 developers
- Expected 100K daily users
- Need to scale for holiday traffic
- Multiple product categories
- Payment processing integration required
"""
    }]
)

# Claude's response includes:
# <thinking>
# Let me analyze this systematically...
# Team size: 8 developers - small team, monolith may be easier to coordinate
# Scale: 100K daily users - moderate scale, monolith can handle this
# Holiday traffic: Need elasticity - both can scale but microservices more flexible
# Payment: Isolated concern - microservice could isolate risk
# ... [detailed analysis of trade-offs]
# </thinking>
#
# Recommendation: Start with modular monolith...
# [Detailed, well-reasoned answer based on analysis]
```

#### Example 2: Debugging Complex Issue

```python
# Trigger extended thinking for debugging
response = client.messages.create(
    model="claude-opus-4-5-20250329",
    max_tokens=8192,
    system="You are a senior debugging expert. Think through problems systematically, considering all possible causes before suggesting solutions. Show your reasoning process.",
    messages=[{
        "role": "user",
        "content": """We're experiencing intermittent 500 errors in production, approximately 2-3% of requests. The errors don't appear in our staging environment.

Symptoms:
- Random endpoints affected (not specific to one route)
- More frequent during peak hours (9am-5pm)
- Error logs show "Database connection timeout"
- Database CPU usage normal (<40%)
- Application server CPU normal (<50%)
- Happens more on certain app servers (servers 3 and 7)

Stack:
- Node.js application
- PostgreSQL database
- 8 application servers behind load balancer
- Connection pooling with max 20 connections per server

Analyze the root cause and suggest solutions.
"""
    }]
)

# Claude's thinking process will:
# 1. Analyze each symptom systematically
# 2. Form hypotheses about root cause
# 3. Consider how symptoms support/refute each hypothesis
# 4. Identify most likely cause
# 5. Suggest diagnostic steps
# 6. Provide solution with rationale
```

### Triggering Extended Thinking

#### Method 1: System Prompt (Recommended)

```python
extended_thinking_system = """Before providing your answer, think through the problem step-by-step in <thinking> tags. Consider:
- All relevant factors and constraints
- Multiple possible approaches
- Trade-offs of each approach
- Edge cases and potential issues
- Long-term implications

Then provide your final answer with clear reasoning.
"""

response = client.messages.create(
    model="claude-opus-4-5-20250329",
    max_tokens=8192,
    system=extended_thinking_system,
    messages=[{"role": "user", "content": "Your complex question here"}]
)
```

#### Method 2: User Prompt Pattern

```python
response = client.messages.create(
    model="claude-opus-4-5-20250329",
    max_tokens=8192,
    messages=[{
        "role": "user",
        "content": """Let's think through this step-by-step.

Question: [Your complex question]

Please:
1. First, analyze the problem systematically
2. Consider multiple approaches
3. Evaluate trade-offs
4. Then provide your recommendation

Show your reasoning process.
"""
    }]
)
```

#### Method 3: CLI Flag (Claude Code)

```bash
# Use --extended-thinking flag
claude --extended-thinking "Design a caching strategy for our API"
```

### Interpreting Extended Thinking Output

```xml
<!-- Claude's response format with extended thinking -->

<thinking>
Let me analyze this caching strategy design systematically.

Current requirements:
- API serves 1000 req/s
- Data changes infrequently (every 5-10 minutes)
- Need to support cache invalidation
- Must work across 8 application servers

Caching options to consider:
1. In-memory cache (per server)
   Pros: Fastest, no network overhead
   Cons: Inconsistency across servers, harder to invalidate

2. Redis (centralized)
   Pros: Consistent, easy invalidation, pub/sub support
   Cons: Network latency, single point of failure (without replication)

3. CDN (for static responses)
   Pros: Geographic distribution, handles load
   Cons: Not suitable for dynamic/user-specific data

For this use case:
- 1000 req/s is moderate load
- Infrequent changes favor caching
- Multi-server deployment needs consistency
- Invalidation requirement is critical

Redis appears optimal because:
- Consistency across servers (critical)
- Pub/sub enables instant invalidation
- Can use Redis Cluster for HA
- Network latency acceptable for 5-10 min cache lifetime

Alternative: Hybrid approach
- Redis for shared cache
- In-memory L1 cache with short TTL (30s)
- Reduces Redis load while maintaining consistency
</thinking>

Based on the analysis above, I recommend a hybrid caching strategy:

1. **Primary cache**: Redis with 5-minute TTL
   - Consistent across all servers
   - Easy invalidation via pub/sub

2. **L1 cache**: In-memory with 30-second TTL
   - Reduces Redis load by 90%+
   - Brief inconsistency window acceptable

[Detailed implementation guidance follows...]
```

**Interpreting the thinking**:

- Shows Claude considered multiple options
- Evaluated trade-offs systematically
- Reached decision based on specific requirements
- More reliable than direct answer without reasoning

### Extended Thinking Best Practices

**DO**:

```text
✓ Use for high-stakes decisions
✓ Use Opus model for best thinking quality
✓ Provide comprehensive context
✓ Allow sufficient tokens for thinking + answer (8K-16K)
✓ Review the thinking process, not just final answer
✓ Learn from Claude's reasoning approach
```

**DON'T**:

```text
✗ Use for every simple query (wastes tokens/cost)
✗ Ignore the thinking section (valuable insights)
✗ Provide insufficient context (garbage in, garbage out)
✗ Use with token-limited models (thinking needs space)
✗ Expect extended thinking from Haiku (use Sonnet/Opus)
```

---

## Multi-Agent Workflows

Multi-agent workflows involve orchestrating multiple Claude instances (or
multiple calls) with specialized roles to solve complex problems. This pattern
is powerful for large-scale tasks.

### Core Concepts

#### What is a Multi-Agent Workflow

A multi-agent workflow:

- Uses multiple Claude instances or calls with **different specialized roles**
- Each "agent" focuses on a specific aspect of the problem
- Agents can **pass results to each other** in sequence or parallel
- Enables **separation of concerns** and specialization
- Allows **iterative refinement** through multiple passes

#### When to Use Multi-Agent Workflows

```text
Use multi-agent workflows for:
✓ Large codebases requiring analysis + generation + review
✓ Tasks needing specialized expertise (security, performance, etc.)
✓ Complex problems requiring multiple perspectives
✓ Quality-critical work benefiting from review stages
✓ Tasks with distinct phases (analysis → design → implementation)

Examples:
• Large refactoring: Analyze → Plan → Implement → Review
• Security audit: Scan → Deep analysis → Remediation → Verification
• Feature implementation: Design → Code → Test → Document → Review
```

### Multi-Agent Patterns

#### Pattern 1: Sequential Specialists

Each agent specializes in one phase, passing results to the next.

```python
from anthropic import Anthropic

client = Anthropic()

def sequential_specialists_workflow(feature_requirements: str):
    """
    Multi-agent workflow: Architect → Developer → Tester → Reviewer
    """

    # Agent 1: Architect (Opus for design)
    architect_response = client.messages.create(
        model="claude-opus-4-5-20250329",
        max_tokens=4096,
        system="""You are a software architect. Design the technical approach
        for implementing features. Provide:
        - Architecture overview
        - Component breakdown
        - Data flow
        - Technology choices
        - Implementation plan""",
        messages=[{
            "role": "user",
            "content": f"Design the architecture for: {feature_requirements}"
        }]
    )

    architecture_plan = architect_response.content[0].text
    print("📐 Architecture designed")

    # Agent 2: Developer (Sonnet for implementation)
    developer_response = client.messages.create(
        model="claude-sonnet-4-5-20250329",
        max_tokens=8192,
        system="""You are an expert developer. Implement features based on
        architectural plans. Write production-quality code with error handling.""",
        messages=[
            {
                "role": "user",
                "content": f"""Implement this feature based on the architecture:

Architecture Plan:
{architecture_plan}

Original Requirements:
{feature_requirements}

Provide complete, working code."""
            }
        ]
    )

    implementation = developer_response.content[0].text
    print("💻 Code implemented")

    # Agent 3: Tester (Sonnet for tests)
    tester_response = client.messages.create(
        model="claude-sonnet-4-5-20250329",
        max_tokens=4096,
        system="""You are a QA engineer. Generate comprehensive tests for code.
        Include unit tests, integration tests, and edge cases.""",
        messages=[
            {
                "role": "user",
                "content": f"""Generate comprehensive tests for this code:

{implementation}

Include:
- Unit tests for each function
- Integration tests
- Edge case tests
- Error scenario tests"""
            }
        ]
    )

    tests = tester_response.content[0].text
    print("🧪 Tests generated")

    # Agent 4: Reviewer (Opus for quality review)
    reviewer_response = client.messages.create(
        model="claude-opus-4-5-20250329",
        max_tokens=4096,
        system="""You are a senior code reviewer. Review code for:
        - Correctness and bugs
        - Security vulnerabilities
        - Performance issues
        - Code quality and maintainability
        Provide specific feedback.""",
        messages=[
            {
                "role": "user",
                "content": f"""Review this implementation:

Code:
{implementation}

Tests:
{tests}

Provide detailed feedback on any issues found."""
            }
        ]
    )

    review_feedback = reviewer_response.content[0].text
    print("👀 Code reviewed")

    return {
        "architecture": architecture_plan,
        "code": implementation,
        "tests": tests,
        "review": review_feedback
    }

# Usage
result = sequential_specialists_workflow(
    "User authentication system with JWT, password reset, and 2FA"
)
```

**Benefits**:

- Each agent specializes in what it does best
- Quality improves through multi-stage refinement
- Clear separation of concerns
- Can use different models for different stages (Opus for design/review, Sonnet for implementation)

**Cost Consideration**:

```text
Example feature implementation:
- Architect (Opus): $0.50
- Developer (Sonnet): $0.30
- Tester (Sonnet): $0.20
- Reviewer (Opus): $0.40
Total: $1.40

vs single-agent (Opus): $1.20

Trade-off: 17% higher cost for 40%+ better quality
```

#### Pattern 2: Parallel Specialists

Multiple agents work on different aspects simultaneously, then results are merged.

```python
import asyncio
from anthropic import AsyncAnthropic

client = AsyncAnthropic()

async def parallel_specialists_workflow(codebase: str):
    """
    Multi-agent workflow: Security + Performance + Code Quality in parallel
    """

    # Define specialist tasks
    async def security_audit(code: str):
        response = await client.messages.create(
            model="claude-opus-4-5-20250329",
            max_tokens=4096,
            system="""You are a security auditor. Find vulnerabilities:
            - SQL injection, XSS, CSRF
            - Auth/authz issues
            - Sensitive data exposure
            - Crypto weaknesses""",
            messages=[{
                "role": "user",
                "content": f"Audit this code for security issues:\n\n{code}"
            }]
        )
        return response.content[0].text

    async def performance_analysis(code: str):
        response = await client.messages.create(
            model="claude-sonnet-4-5-20250329",
            max_tokens=4096,
            system="""You are a performance engineer. Analyze:
            - Algorithmic complexity
            - Database query efficiency
            - Memory usage
            - Optimization opportunities""",
            messages=[{
                "role": "user",
                "content": f"Analyze performance of this code:\n\n{code}"
            }]
        )
        return response.content[0].text

    async def quality_review(code: str):
        response = await client.messages.create(
            model="claude-sonnet-4-5-20250329",
            max_tokens=4096,
            system="""You are a code quality expert. Review:
            - Code smells and anti-patterns
            - Maintainability issues
            - Documentation gaps
            - Test coverage""",
            messages=[{
                "role": "user",
                "content": f"Review code quality:\n\n{code}"
            }]
        )
        return response.content[0].text

    # Run all analyses in parallel
    security, performance, quality = await asyncio.gather(
        security_audit(codebase),
        performance_analysis(codebase),
        quality_review(codebase)
    )

    # Agent 4: Synthesizer combines all feedback
    synthesizer_response = await client.messages.create(
        model="claude-opus-4-5-20250329",
        max_tokens=4096,
        system="""You are a tech lead synthesizing code review feedback.
        Combine inputs from security, performance, and quality reviews into
        a prioritized action plan.""",
        messages=[{
            "role": "user",
            "content": f"""Synthesize this feedback into an action plan:

Security Audit:
{security}

Performance Analysis:
{performance}

Quality Review:
{quality}

Provide prioritized recommendations."""
        }]
    )

    return {
        "security": security,
        "performance": performance,
        "quality": quality,
        "action_plan": synthesizer_response.content[0].text
    }

# Usage
result = asyncio.run(parallel_specialists_workflow(codebase_code))
```

**Benefits**:

- Faster than sequential (parallel execution)
- Specialized expertise in each domain
- Comprehensive coverage
- Final synthesis provides holistic view

#### Pattern 3: Iterative Refinement

Agent produces output, another agent critiques, first agent improves.

```python
def iterative_refinement_workflow(task: str, iterations: int = 3):
    """
    Multi-agent workflow: Generator ↔ Critic iterative loop
    """

    current_solution = ""

    for i in range(iterations):
        # Generator agent
        generator_response = client.messages.create(
            model="claude-sonnet-4-5-20250329",
            max_tokens=4096,
            system="You are a code generator. Create high-quality implementations.",
            messages=[
                {
                    "role": "user",
                    "content": f"""Task: {task}

{f"Previous attempt: {current_solution}" if current_solution else ""}
{f"Feedback to address: {critique}" if i > 0 else ""}

{"Improve the previous implementation based on feedback." if i > 0 else "Provide initial implementation."}"""
                }
            ]
        )

        current_solution = generator_response.content[0].text
        print(f"🔄 Iteration {i+1}: Generated solution")

        # Critic agent
        critic_response = client.messages.create(
            model="claude-opus-4-5-20250329",
            max_tokens=2048,
            system="""You are a critical code reviewer. Find flaws:
            - Logic errors
            - Edge cases not handled
            - Performance issues
            - Security concerns
            Be specific and constructive.""",
            messages=[{
                "role": "user",
                "content": f"Review this code and suggest improvements:\n\n{current_solution}"
            }]
        )

        critique = critic_response.content[0].text
        print(f"🔍 Iteration {i+1}: Received critique")

        # Check if critic is satisfied
        if "no significant issues" in critique.lower() or i == iterations - 1:
            print(f"✅ Converged after {i+1} iterations")
            break

    return {
        "final_solution": current_solution,
        "final_critique": critique,
        "iterations": i + 1
    }

# Usage
result = iterative_refinement_workflow(
    "Implement a thread-safe LRU cache in Python"
)
```

**Benefits**:

- Solution improves with each iteration
- Catches and fixes issues systematically
- Converges toward high-quality solution
- Balances cost (stops when good enough)

### Multi-Agent Orchestration

#### Workflow Orchestration Framework

```python
from dataclasses import dataclass
from typing import Callable, List, Dict, Any
from enum import Enum

class AgentRole(Enum):
    ARCHITECT = "architect"
    DEVELOPER = "developer"
    TESTER = "tester"
    REVIEWER = "reviewer"
    SECURITY = "security"
    PERFORMANCE = "performance"

@dataclass
class Agent:
    role: AgentRole
    model: str
    system_prompt: str
    temperature: float = 0.5

@dataclass
class WorkflowStep:
    agent: Agent
    depends_on: List[str]  # IDs of previous steps
    output_name: str

class MultiAgentOrchestrator:
    def __init__(self, client: Anthropic):
        self.client = client
        self.agents: Dict[AgentRole, Agent] = {}
        self.results: Dict[str, str] = {}

    def register_agent(self, agent: Agent):
        self.agents[agent.role] = agent

    async def execute_step(
        self,
        step: WorkflowStep,
        user_prompt: str
    ) -> str:
        # Gather dependencies
        context = "\n\n".join([
            f"Input from {dep}:\n{self.results[dep]}"
            for dep in step.depends_on
            if dep in self.results
        ])

        full_prompt = f"{context}\n\n{user_prompt}" if context else user_prompt

        # Execute agent
        response = await self.client.messages.create(
            model=step.agent.model,
            max_tokens=4096,
            temperature=step.agent.temperature,
            system=step.agent.system_prompt,
            messages=[{"role": "user", "content": full_prompt}]
        )

        result = response.content[0].text
        self.results[step.output_name] = result

        return result

    async def execute_workflow(self, steps: List[WorkflowStep], initial_prompt: str):
        for step in steps:
            print(f"Executing: {step.agent.role.value}")
            await self.execute_step(step, initial_prompt)

        return self.results

# Define agents
architect = Agent(
    role=AgentRole.ARCHITECT,
    model="claude-opus-4-5-20250329",
    system_prompt="You are a software architect...",
    temperature=0.7
)

developer = Agent(
    role=AgentRole.DEVELOPER,
    model="claude-sonnet-4-5-20250329",
    system_prompt="You are an expert developer...",
    temperature=0.3
)

reviewer = Agent(
    role=AgentRole.REVIEWER,
    model="claude-opus-4-5-20250329",
    system_prompt="You are a senior code reviewer...",
    temperature=0.4
)

# Define workflow
workflow = [
    WorkflowStep(
        agent=architect,
        depends_on=[],
        output_name="architecture"
    ),
    WorkflowStep(
        agent=developer,
        depends_on=["architecture"],
        output_name="implementation"
    ),
    WorkflowStep(
        agent=reviewer,
        depends_on=["architecture", "implementation"],
        output_name="review"
    )
]

# Execute
orchestrator = MultiAgentOrchestrator(client)
for agent in [architect, developer, reviewer]:
    orchestrator.register_agent(agent)

results = await orchestrator.execute_workflow(
    workflow,
    "Build a REST API for user management"
)
```

### Multi-Agent Best Practices

**DO**:

```text
✓ Use Opus for critical roles (architect, security, final review)
✓ Use Sonnet for implementation and generation
✓ Run independent analyses in parallel (faster, cheaper)
✓ Synthesize parallel results with final agent
✓ Provide clear role definitions in system prompts
✓ Pass relevant context between agents
✓ Stop iteration when quality threshold met
✓ Monitor total cost across all agents
```

**DON'T**:

```text
✗ Use multi-agent for simple tasks (overkill, expensive)
✗ Create circular dependencies between agents
✗ Pass excessive context between agents (token waste)
✗ Use too many iterations (diminishing returns)
✗ Ignore failed agents in chain (validate each step)
✗ Use same model for all agents (miss specialization benefits)
```

---

## Context and Prompt Engineering

Effective context management and prompt engineering are critical for Claude's
performance. This section covers advanced techniques.

### Context Assembly Strategies

#### Hierarchical Context Structuring

```python
def build_hierarchical_context(
    project_overview: str,
    relevant_files: List[str],
    specific_focus: str
) -> str:
    """
    Structure context hierarchically: broad → narrow → specific
    """
    context = f"""
# Project Context

{project_overview}

# Relevant Code

{chr(10).join(relevant_files)}

# Specific Focus

{specific_focus}
"""
    return context

# Example
context = build_hierarchical_context(
    project_overview="E-commerce platform built with Next.js and PostgreSQL",
    relevant_files=[
        "--- auth-service.ts ---\n[code]",
        "--- user-model.ts ---\n[code]"
    ],
    specific_focus="Add OAuth2 authentication alongside existing JWT auth"
)
```

#### Smart File Selection

```python
import os
from pathlib import Path

def select_relevant_files(
    target_file: str,
    max_files: int = 10,
    max_tokens: int = 50000
) -> List[str]:
    """
    Select most relevant files based on:
    1. Direct imports/dependencies
    2. Same directory files
    3. Similar names
    4. Recent modifications
    """
    relevant = []
    tokens_used = 0

    # 1. Direct dependencies (highest priority)
    deps = extract_imports(target_file)
    for dep in deps:
        if os.path.exists(dep):
            content = read_file(dep)
            file_tokens = estimate_tokens(content)
            if tokens_used + file_tokens <= max_tokens:
                relevant.append(content)
                tokens_used += file_tokens

    # 2. Same directory (medium priority)
    dir_files = get_directory_files(os.path.dirname(target_file))
    for f in dir_files:
        if len(relevant) >= max_files:
            break
        content = read_file(f)
        file_tokens = estimate_tokens(content)
        if tokens_used + file_tokens <= max_tokens:
            relevant.append(content)
            tokens_used += file_tokens

    return relevant
```

### Prompt Engineering Patterns

#### Chain-of-Thought Prompting

```python
# Instead of:
prompt = "Fix this bug: [code]"

# Use chain-of-thought:
prompt = """Fix this bug by thinking step-by-step:

1. First, analyze what the code is trying to do
2. Identify where the bug is occurring
3. Explain why the bug happens
4. Suggest the fix
5. Explain why the fix works
6. Provide the corrected code

Code:
[code]
"""
```

#### Few-Shot Examples

````python
# Provide examples of desired behavior
prompt = f"""Generate a API endpoint following our patterns.

Example 1:
Task: Create endpoint for fetching user profile
Output:
```typescript
export async function GET(req: Request) {{
  const userId = req.params.id;
  const user = await db.user.findUnique({{ where: {{ id: userId }} }});

  if (!user) {{
    return Response.json({{ error: "User not found" }}, {{ status: 404 }});
  }}

  return Response.json({{ data: user }});
}}
```

Example 2:
Task: Create endpoint for updating user email
Output:

```typescript
export async function PATCH(req: Request) {{
  const {{ email }} = await req.json();
  const userId = req.params.id;

  const updated = await db.user.update({{
    where: {{ id: userId }},
    data: {{ email }}
  }});

  return Response.json({{ data: updated }});
}}
```

Now generate:
Task: Create endpoint for deleting user account
"""
````

#### Structured Output Requests

```python
prompt = """Analyze this code for security issues.

Provide response in this exact JSON format:
{
  "critical_issues": [
    {
      "line": <line number>,
      "issue": "<description>",
      "severity": "critical",
      "fix": "<how to fix>"
    }
  ],
  "warnings": [...],
  "suggestions": [...]
}

Code:
[code]
"""
```

---

## Common Pitfalls and Solutions

### Pitfall 1: Hallucinated APIs

**Problem**: Claude invents functions or methods that don't exist.

**Example**:

```typescript
// Claude might generate:
import { validateEmail } from '@/lib/validators';
// But @/lib/validators doesn't export validateEmail!
```

**Solutions**:

```python
# ✓ Solution 1: Provide actual API documentation
prompt = f"""
Available validation functions in @/lib/validators:
- validateUsername(username: string): boolean
- validatePassword(password: string): boolean
- sanitizeInput(input: string): string

Generate validation code using ONLY these functions.
"""

# ✓ Solution 2: Request Claude to verify
prompt = """
Generate the code, and before finalizing, verify that all imported
functions actually exist in the codebase. If uncertain, ask me.
"""

# ✓ Solution 3: Use AGENTS.md to document APIs
# Include in AGENTS.md:
## Available Utilities

### Validators (@/lib/validators)
- validateUsername(username: string): boolean
- validatePassword(password: string): boolean
```

### Pitfall 2: Inconsistent Code Style

**Problem**: Generated code doesn't match project conventions.

**Solutions**:

````python
# ✓ Solution 1: Explicit style instructions
system_prompt = """
Code style requirements:
- Use single quotes, not double quotes
- 2-space indentation
- Named exports only (no default exports)
- Functional components with hooks (no class components)
- camelCase for variables, PascalCase for components
"""

# ✓ Solution 2: Provide style examples
prompt = """
Generate code following this style:

Example from our codebase:
```typescript
export const UserProfile = ({ userId }: Props) => {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    fetchUser(userId).then(setUser);
  }, [userId]);

  return <div>{user?.name}</div>;
};
```

Now generate: [your request]
"""

# ✓ Solution 3: Post-process with linter

generated_code = get_claude_response(prompt)
formatted_code = run_prettier(generated_code)
````

### Pitfall 3: Over-Engineering

**Problem**: Claude creates unnecessarily complex solutions.

**Solutions**:

```python
# ✓ Solution 1: Emphasize simplicity
prompt = """
Implement a simple user login function.

Requirements:
- KEEP IT SIMPLE - no unnecessary abstractions
- Use direct, straightforward approach
- Only add complexity if absolutely necessary
- Prefer fewer lines of clear code over elaborate patterns
"""

# ✓ Solution 2: Specify constraints
prompt = """
Implement in <50 lines of code, using only built-in libraries.
No design patterns unless truly necessary.
"""

# ✓ Solution 3: Ask for simple version first
prompt = """
First provide the simplest possible implementation.
Then, if needed, suggest more sophisticated versions.
"""
```

### Pitfall 4: Ignoring Edge Cases

**Problem**: Generated code doesn't handle edge cases.

**Solutions**:

```python
# ✓ Solution 1: Explicitly request edge case handling
prompt = """
Generate user profile update function.

MUST handle these edge cases:
- User not found
- Invalid email format
- Email already taken by another user
- Database connection failure
- Missing required fields
"""

# ✓ Solution 2: Use extended thinking for complex scenarios
system_prompt = """
Before generating code, think through all possible edge cases.
List them explicitly, then ensure code handles each one.
"""

# ✓ Solution 3: Request separate edge case analysis
prompt_1 = "What edge cases should be handled for user login?"
edge_cases = get_claude_response(prompt_1)

prompt_2 = f"Implement login handling these edge cases: {edge_cases}"
```

### Pitfall 5: Security Vulnerabilities

**Problem**: Generated code has security flaws.

**Solutions**:

```python
# ✓ Solution 1: Security-focused system prompt
security_system_prompt = """
You are a security-conscious developer.

ALWAYS:
- Validate and sanitize all inputs
- Use parameterized queries (never string concatenation)
- Implement proper authentication/authorization
- Handle sensitive data securely
- Use secure cryptographic functions

NEVER:
- Trust user input without validation
- Expose sensitive information in errors
- Use deprecated crypto functions
- Store passwords in plain text
"""

# ✓ Solution 2: Separate security review
code = get_claude_response(implementation_prompt)

security_review = get_claude_response(f"""
Review this code for security vulnerabilities:
{code}

Check for:
- SQL injection
- XSS
- CSRF
- Auth bypasses
- Sensitive data exposure
""")

# ✓ Solution 3: Use Opus for security-critical code
response = client.messages.create(
    model="claude-opus-4-5-20250329",  # Use best model for security
    system=security_system_prompt,
    messages=[{"role": "user", "content": security_critical_task}]
)
```

### Pitfall 6: Context Window Overflow

**Problem**: Exceeding 200K token context limit.

**Solutions**:

```python
# ✓ Solution 1: Prioritize context
def prioritize_context(files: List[str], max_tokens: int) -> List[str]:
    """Include most relevant files first, stop when limit reached."""
    priority_order = [
        "target_file",  # File being modified (highest priority)
        "direct_dependencies",  # Files it imports
        "type_definitions",  # Types it uses
        "similar_files",  # Files with similar functionality
        "tests"  # Existing tests
    ]

    included = []
    tokens = 0

    for category in priority_order:
        for file in files[category]:
            file_tokens = estimate_tokens(file)
            if tokens + file_tokens <= max_tokens:
                included.append(file)
                tokens += file_tokens

    return included

# ✓ Solution 2: Summarize distant context
# Instead of including full files, provide summaries
context = f"""
Files in src/services/:
- auth-service.ts: Handles authentication with JWT
- user-service.ts: CRUD operations for users
- email-service.ts: Sends transactional emails

[Only include full code for auth-service.ts since that's relevant]
"""

# ✓ Solution 3: Split into multiple requests
# For large refactoring:
step_1 = "Analyze src/services/ and suggest refactoring approach"
plan = get_claude_response(step_1)

step_2 = f"Implement step 1 of plan: {plan}"
# Each step has smaller context needs
```

### Pitfall 7: Outdated Package Usage

**Problem**: Claude suggests deprecated or outdated packages.

**Solutions**:

```python
# ✓ Solution 1: Specify versions in prompt
prompt = """
Generate authentication code for:
- Next.js 14 (app router, not pages)
- NextAuth.js v5 (not v4)
- React 18 (use modern hooks)

Use latest stable APIs for these versions.
"""

# ✓ Solution 2: Provide current package.json
prompt = f"""
Our current dependencies:
{json.dumps(package_json['dependencies'], indent=2)}

Generate code compatible with these exact versions.
"""

# ✓ Solution 3: Review and update
code = get_claude_response(prompt)

review = get_claude_response(f"""
Review this code for deprecated APIs or outdated patterns:
{code}

Our tech stack uses latest versions as of 2025.
Flag any outdated usage.
""")
```

### Pitfall 8: Incomplete Error Handling

**Problem**: Missing try-catch blocks or error scenarios.

**Solutions**:

```python
# ✓ Solution 1: Explicit error handling requirements
prompt = """
Generate user registration function.

Error handling requirements:
- Wrap all async operations in try-catch
- Handle network failures gracefully
- Provide user-friendly error messages
- Log errors for debugging
- Never expose internal errors to users
- Return proper HTTP status codes
"""

# ✓ Solution 2: Provide error handling template
prompt = f"""
Follow this error handling pattern:

{example_error_handling_code}

Now generate: [your request]
"""

# ✓ Solution 3: Request explicit error scenarios
prompt = """
Generate the implementation, then separately list all error
scenarios and show how each is handled in the code.
"""
```

---

## Best Practices Summary

### Model Selection Summary

```text
┌─────────────────────────────────────────────────┐
│ QUICK REFERENCE: MODEL SELECTION               │
├─────────────────────────────────────────────────┤
│                                                  │
│ Simple + Non-Critical = HAIKU                   │
│   • Docstrings, formatting, simple CRUD         │
│   • Cost: ~$0.001-0.01/task                     │
│                                                  │
│ Standard Development = SONNET (DEFAULT)         │
│   • Features, tests, refactoring, reviews       │
│   • Cost: ~$0.01-0.20/task                      │
│                                                  │
│ Complex + Critical = OPUS                       │
│   • Architecture, security, critical debugging  │
│   • Cost: ~$0.10-1.00/task                      │
│                                                  │
└─────────────────────────────────────────────────┘
```

### Prompt Engineering Summary

```markdown
## Effective Prompts

1. **Be Specific**: Provide clear requirements and constraints
2. **Give Context**: Include relevant code, architecture, conventions
3. **Show Examples**: Demonstrate desired output format
4. **Request Reasoning**: Ask Claude to explain its approach
5. **Iterate**: Refine based on initial results

## Prompt Template

Task: [What needs to be done]

Context:
- [Relevant information]
- [Technical constraints]
- [Existing patterns to follow]

Requirements:
- [Specific requirement 1]
- [Specific requirement 2]

Example:
[Show desired output format]

Output:
[Specify what you want back]
```

### Cost Optimization Summary

```text
1. Use lowest tier that produces acceptable quality
2. Batch similar operations together
3. Use prompt caching for repeated context
4. Minimize input tokens via smart context selection
5. Stop iteration when quality threshold is met
6. Monitor usage and costs regularly
7. Educate team on cost-aware practices
```

---

## Do/Don't Quick Reference

### Model Selection

**DO**:

```text
✓ Use Haiku for simple, high-volume tasks (docstrings, formatting)
✓ Use Sonnet as default for standard development
✓ Use Opus for security, architecture, and critical decisions
✓ Match model capability to task complexity
✓ Monitor costs and adjust model selection based on ROI
✓ Use model cascading (try Sonnet first, upgrade if needed)
```

**DON'T**:

```text
✗ Use Opus for simple tasks (waste of money)
✗ Use Haiku for complex reasoning (poor results)
✗ Ignore cost metrics and always use highest tier
✗ Assume one model fits all use cases
✗ Skip model selection evaluation
```

### AGENTS.md Files

**DO**:

```text
✓ Create AGENTS.md at repository root (with CLAUDE.md symlink)
✓ Include: project overview, tech stack, commands, conventions
✓ Keep under 500-1000 lines
✓ Update when project changes
✓ Include code examples for conventions
✓ Document common pitfalls and gotchas
✓ Link to detailed docs for deep dives
```

**DON'T**:

```text
✗ Include exhaustive documentation (link instead)
✗ Let it become outdated
✗ Include sensitive information (secrets, credentials)
✗ Duplicate README content
✗ Make it overly verbose
✗ Skip team review of accuracy
```

### Extended Thinking

**DO**:

```text
✓ Use for complex architectural decisions
✓ Use for security analysis
✓ Use for debugging elusive issues
✓ Use for trade-off analysis
✓ Review the thinking process, not just answer
✓ Allow sufficient tokens (8K-16K)
✓ Use Opus model for best thinking quality
```

**DON'T**:

```text
✗ Use for every simple query (wastes tokens/cost)
✗ Ignore the thinking section (valuable insights there)
✗ Use with insufficient context
✗ Expect extended thinking from Haiku
✗ Use when simple answer suffices
```

### Multi-Agent Workflows

**DO**:

```text
✓ Use for large, complex tasks needing multiple perspectives
✓ Assign specialized roles (architect, developer, reviewer)
✓ Run independent analyses in parallel
✓ Use Opus for critical roles, Sonnet for implementation
✓ Synthesize parallel results with final agent
✓ Monitor total cost across all agents
```

**DON'T**:

```text
✗ Use for simple tasks (overkill and expensive)
✗ Create circular dependencies
✗ Pass excessive context between agents
✗ Use too many iterations (diminishing returns)
✗ Use same model for all agents (miss specialization)
```

### Context Management

**DO**:

```text
✓ Prioritize context: target file > dependencies > similar files
✓ Use hierarchical structuring (broad → narrow → specific)
✓ Leverage prompt caching for repeated context
✓ Provide AGENTS.md for project-wide context
✓ Include relevant code examples
✓ Summarize distant context instead of full inclusion
```

**DON'T**:

```text
✗ Include entire codebase (exceeds limits, expensive)
✗ Provide irrelevant files (wastes tokens)
✗ Repeat same large context in consecutive requests
✗ Include verbose comments for AI consumption
✗ Omit critical dependencies
```

### Prompt Engineering

**DO**:

```text
✓ Be specific about requirements and constraints
✓ Provide examples of desired output
✓ Request step-by-step reasoning for complex tasks
✓ Specify error handling requirements explicitly
✓ Include relevant conventions and patterns
✓ Ask clarifying questions before implementation
```

**DON'T**:

```text
✗ Be vague ("make it better")
✗ Omit critical context
✗ Request overly broad analysis
✗ Ignore output format specification
✗ Assume Claude knows your conventions
```

### Security

**DO**:

```text
✓ Use Opus for security-critical code
✓ Explicitly request security considerations
✓ Review generated code for vulnerabilities
✓ Use security-focused system prompts
✓ Validate inputs, use parameterized queries
✓ Conduct separate security review pass
```

**DON'T**:

```text
✗ Trust generated security code without review
✗ Use Haiku for authentication/authorization
✗ Skip security review for public-facing features
✗ Assume Claude catches all vulnerabilities
✗ Deploy security code without human expert review
```

### Cost Optimization

**DO**:

```text
✓ Track costs per developer, per task type
✓ Use prompt caching for repeated context
✓ Batch similar operations
✓ Start with lower-tier model, upgrade if needed
✓ Minimize context through smart file selection
✓ Stop iteration when quality threshold met
```

**DON'T**:

```text
✗ Ignore cost metrics
✗ Always use highest-tier model
✗ Repeat large context unnecessarily
✗ Continue iteration indefinitely
✗ Include irrelevant files in context
```

### Error Handling

**DO**:

```text
✓ Implement retry logic with exponential backoff
✓ Handle rate limits gracefully
✓ Validate outputs before using
✓ Catch and log API errors
✓ Have fallback strategies
```

**DON'T**:

```text
✗ Assume API calls always succeed
✗ Ignore rate limit errors
✗ Skip output validation
✗ Fail silently on errors
✗ Retry indefinitely without backoff
```

---

## Conclusion

Claude's models (Opus, Sonnet, Haiku) provide powerful capabilities when used correctly. Success requires:

1. **Strategic Model Selection**: Match model tier to task complexity and criticality
2. **Effective Context**: Use AGENTS.md, prioritize relevant files, leverage caching
3. **Smart Prompting**: Be specific, provide examples, request reasoning
4. **Extended Thinking**: Use for complex problems requiring deep analysis
5. **Multi-Agent Workflows**: Orchestrate specialized agents for large tasks
6. **Security Mindset**: Always review for vulnerabilities, use Opus for critical code
7. **Cost Awareness**: Monitor usage, optimize context, use appropriate tiers

Following these best practices enables teams to:

- Achieve 20-40% productivity gains on suitable tasks
- Maintain or improve code quality
- Optimize costs (10-50:1 ROI typical)
- Scale AI assistance across organization
- Build secure, maintainable systems

**Remember**: Claude is a powerful assistant, but the developer remains
responsible for all code quality, security, and correctness.

---

**Version**: 1.0.0
**Last Updated**: 2025-12-07
**Maintainer**: Engineering Team
**Feedback**: Submit issues or improvements via PR

---

## References

[^1]: [Claude Models Overview](https://docs.anthropic.com/en/docs/models-overview) - Official Anthropic documentation on Claude model families and capabilities
[^2]: [Claude Model Pricing](https://www.anthropic.com/pricing#anthropic-api) - Current pricing for Claude Opus, Sonnet, and Haiku models
[^3]: [Prompt Caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching) - Guide to using prompt caching to reduce costs and latency
[^4]: [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) - Official documentation for the Claude Code command-line interface
[^5]: [Anthropic API Reference](https://docs.anthropic.com/en/api/getting-started) - Complete API documentation for integrating Claude
[^6]: [Streaming Messages](https://docs.anthropic.com/en/api/streaming) - API documentation for streaming responses
[^7]: [Extended Thinking](https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking) - Guide to using extended thinking mode for complex reasoning tasks
