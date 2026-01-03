# AI-Assisted Development Overview

## RFC 2119 Key Words

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

## Table of Contents

1. [Introduction](#introduction)
2. [When to Use AI Assistance](#when-to-use-ai-assistance)
3. [Model Selection Guide](#model-selection-guide)
4. [Provider Comparison](#provider-comparison)
5. [Model Recommendations by Task Type](#model-recommendations-by-task-type)
6. [Workflow Patterns](#workflow-patterns)
7. [Context Management Strategies](#context-management-strategies)
8. [Cost Optimization Patterns](#cost-optimization-patterns)
9. [Quality Assurance for AI Output](#quality-assurance-for-ai-output)
10. [Team Adoption Strategies](#team-adoption-strategies)
11. [References](#references)

## Introduction

This guide provides comprehensive guidance on effectively integrating AI
assistance into software development workflows. Organizations and individual
developers MUST use this guide to establish consistent, efficient, and
cost-effective AI-assisted development practices.

AI-assisted development tools have evolved rapidly, offering capabilities ranging
from code completion to complex architectural analysis. This guide helps teams
navigate the landscape of AI tools, select appropriate models for specific
tasks, and implement workflows that maximize productivity while maintaining
code quality.

### Scope

This guide covers:

- Strategic selection of AI models and providers
- Tactical workflow patterns for different development tasks
- Cost management and optimization strategies
- Quality assurance practices for AI-generated content
- Team adoption and scaling considerations

For provider-specific best practices, see the Claude/Anthropic guide[^1].

### Audience

This guide is intended for:

- Software engineers using AI coding assistants
- Engineering managers establishing team AI practices
- DevOps engineers optimizing AI infrastructure
- Technical leads evaluating AI tooling investments

## When to Use AI Assistance

### Task Types Suitable for AI Assistance

Teams MUST evaluate tasks against the following criteria before engaging AI assistance:

#### High-Value AI Tasks

AI assistance SHOULD be used for the following task types:

1. **Boilerplate Code Generation**
   - CRUD operations
   - API endpoint scaffolding
   - Database model definitions
   - Configuration file templates
   - Test fixtures and mock data

2. **Code Translation and Migration**
   - Language-to-language translation
   - Framework migration (e.g., Class components to Hooks)
   - API version upgrades
   - Legacy code modernization

3. **Documentation Generation**
   - Function and class docstrings
   - API documentation
   - README files
   - Changelog generation from commits
   - Architecture diagrams (via markup languages)

4. **Test Generation**
   - Unit test scaffolding
   - Edge case identification
   - Test data generation
   - Integration test templates
   - Regression test creation

5. **Code Review and Analysis**
   - Security vulnerability detection
   - Performance bottleneck identification
   - Code smell detection
   - Complexity analysis
   - Dependency impact assessment

6. **Refactoring Assistance**
   - Extract method/class refactoring
   - Rename refactoring across files
   - Pattern implementation (e.g., applying Strategy pattern)
   - Dead code identification
   - Duplicate code detection

7. **Problem Solving and Debugging**
   - Error message interpretation
   - Stack trace analysis
   - Algorithm optimization suggestions
   - Third-party library usage examples
   - Configuration troubleshooting

#### Medium-Value AI Tasks

AI assistance MAY be used for these tasks with appropriate oversight:

1. **Architecture Design**
   - System design exploration
   - Trade-off analysis
   - Pattern recommendations
   - Scalability planning

2. **Complex Algorithm Implementation**
   - Search and sort algorithms
   - Graph algorithms
   - Optimization problems
   - Data structure implementation

3. **Integration Code**
   - Third-party API integration
   - Database query optimization
   - Message queue patterns
   - Caching strategies

#### Low-Value AI Tasks

AI assistance SHOULD NOT be the primary approach for:

1. **Domain-Specific Business Logic**
   - Core business rules
   - Complex state machines
   - Financial calculations
   - Regulatory compliance logic

2. **Critical Security Components**
   - Authentication systems
   - Authorization logic
   - Cryptographic implementations
   - Security-sensitive data handling

3. **Performance-Critical Code**
   - Hot path optimizations
   - Low-latency systems
   - Real-time processing
   - Hardware-specific optimizations

### Complexity Level Guidelines

#### Simple Tasks (< 100 LOC, < 30 minutes)

- MUST use AI for initial generation
- SHOULD use faster, cheaper models
- MAY skip detailed code review for non-critical paths
- Examples: utility functions, simple data transformations, basic CRUD

#### Moderate Tasks (100-500 LOC, 30 minutes - 4 hours)

- SHOULD use AI for scaffolding and structure
- MUST conduct thorough code review
- SHOULD iterate with AI on refinements
- Examples: feature implementation, service integration, component development

#### Complex Tasks (500+ LOC, > 4 hours)

- SHOULD use AI for exploration and planning phases
- MUST break down into smaller sub-tasks
- MUST have senior review of AI-generated architecture
- SHOULD use multiple AI interactions with context refinement
- Examples: new service creation, major refactoring, architectural changes

### Decision Tree: Should I Use AI for This Task?

```text
Is the task well-defined with clear requirements?
├─ YES: Continue
└─ NO: Define requirements first, then consider AI

Is similar code already in the codebase?
├─ YES: Use AI with codebase context
└─ NO: Continue

Does the task involve critical security/business logic?
├─ YES: Use AI for exploration only, implement manually
└─ NO: Continue

Is the expected output > 500 LOC?
├─ YES: Break into smaller tasks, use AI for each
└─ NO: Continue

Is this a well-known pattern or common task?
├─ YES: Use AI with high confidence
└─ NO: Use AI with extensive validation

Does your team have expertise to validate the output?
├─ YES: Proceed with AI assistance
└─ NO: Use AI for learning, but seek expert review
```

## Model Selection Guide

### Capability vs Cost Matrix

The following matrix MUST be used as a reference for model selection decisions:

```text
Capability Level vs Cost (per 1M tokens)

High Capability, High Cost ($10-30/1M input)
┌─────────────────────────────────────────┐
│ - Claude Opus 4.5[^2]                   │
│ - GPT-4 Turbo[^3]                       │
│ - Gemini 1.5 Pro[^4]                    │
│                                         │
│ Use for: Complex reasoning, architecture│
│ decisions, security analysis            │
└─────────────────────────────────────────┘

High Capability, Medium Cost ($3-10/1M input)
┌─────────────────────────────────────────┐
│ - Claude Sonnet 4.5[^2]                 │
│ - GPT-4o[^3]                            │
│ - Gemini 1.5 Flash[^4]                  │
│                                         │
│ Use for: Most coding tasks, reviews,   │
│ complex refactoring                     │
└─────────────────────────────────────────┘

Medium Capability, Low Cost ($0.10-3/1M input)
┌─────────────────────────────────────────┐
│ - Claude Haiku 3.5[^2]                  │
│ - GPT-4o mini[^3]                       │
│ - Gemini 1.5 Flash-8B[^4]               │
│                                         │
│ Use for: Code completion, simple tasks, │
│ documentation generation                │
└─────────────────────────────────────────┘

Specialized Models (Variable Cost)
┌─────────────────────────────────────────┐
│ - Codex variants[^3]                    │
│ - CodeLlama[^5]                         │
│ - StarCoder[^6]                         │
│ - Self-hosted models                    │
│                                         │
│ Use for: High-volume tasks, privacy     │
│ requirements, custom fine-tuning        │
└─────────────────────────────────────────┘
```

### Model Characteristics Reference

Teams MUST consider the following characteristics when selecting models:

| Characteristic | Opus/GPT-4 Class | Sonnet/GPT-4o Class | Haiku/Mini Class | Self-Hosted |
|----------------|------------------|---------------------|------------------|-------------|
| **Context Window** | 128K-200K tokens | 128K-200K tokens | 128K-200K tokens | 4K-32K tokens |
| **Response Speed** | Slower (3-10s) | Medium (1-5s) | Fast (<1s) | Variable |
| **Code Quality** | Excellent | Very Good | Good | Variable |
| **Reasoning Depth** | Deep | Moderate-Deep | Basic | Variable |
| **Cost per 1M input** | $10-30 | $3-10 | $0.10-3 | Hardware cost |
| **Cost per 1M output** | $30-90 | $10-30 | $0.30-10 | Hardware cost |
| **Best For** | Architecture, security | General development | Autocomplete, docs | Privacy, volume |

### Selection Criteria

#### When to Use Premium Models (Opus, GPT-4)

Teams MUST use premium models when:

1. **High-Stakes Decisions**
   - Architectural choices affecting multiple teams
   - Security-sensitive code review
   - Performance-critical algorithm design
   - Database schema design for core systems

2. **Complex Reasoning Required**
   - Multi-step refactoring across many files
   - Debugging complex race conditions
   - Analyzing intricate business logic
   - Evaluating multiple solution approaches

3. **Quality Over Speed Priority**
   - Production code generation
   - Customer-facing feature implementation
   - Critical path optimization
   - Regulatory compliance code

#### When to Use Mid-Tier Models (Sonnet, GPT-4o)

Teams SHOULD use mid-tier models for:

1. **Standard Development Tasks**
   - Feature implementation
   - Bug fixes
   - Code reviews
   - Test generation
   - API integration

2. **Balanced Requirements**
   - Good quality needed but not critical
   - Moderate complexity
   - Regular development velocity
   - Standard refactoring tasks

3. **Most Daily Development Work**
   - This SHOULD be the default choice for 70-80% of AI-assisted tasks

#### When to Use Budget Models (Haiku, GPT-4o mini)

Teams MAY use budget models for:

1. **High-Volume, Low-Complexity Tasks**
   - Code completion suggestions
   - Simple documentation generation
   - Formatting and style fixes
   - Straightforward CRUD operations

2. **Exploratory Work**
   - Initial code sketches
   - Brainstorming session notes
   - Quick prototypes
   - Learning exercises

3. **Non-Critical Paths**
   - Internal tooling
   - Script automation
   - Development utilities
   - Test data generation

#### When to Use Self-Hosted Models

Organizations SHOULD consider self-hosted models when:

1. **Privacy Requirements**
   - Proprietary code must not leave infrastructure
   - Regulatory compliance prohibits external AI services
   - Intellectual property concerns
   - Customer data confidentiality

2. **Cost at Scale**
   - Token usage exceeds 100M tokens/month
   - Predictable high-volume usage
   - Long-term cost optimization
   - Budget constraints with high usage

3. **Customization Needs**
   - Domain-specific fine-tuning required
   - Internal coding standards enforcement
   - Custom tooling integration
   - Specialized language or framework focus

## Provider Comparison

### Comprehensive Provider Analysis

Organizations MUST evaluate providers based on the following detailed comparison:

| Feature | Anthropic Claude[^2] | OpenAI GPT[^3] | Google Gemini[^4] | Self-Hosted (Llama/CodeLlama)[^5][^6] |
|---------|-----------------|------------|---------------|-------------------------------|
| **Latest Models** | Opus 4.5, Sonnet 4.5, Haiku 3.5 | GPT-4 Turbo, GPT-4o, GPT-4o mini | Gemini 1.5 Pro, Flash, Flash-8B | Llama 3.1, CodeLlama 34B, StarCoder2 |
| **Context Window** | 200K tokens | 128K tokens | 1M tokens (Gemini Pro) | 4K-128K depending on model |
| **Coding Strength** | Excellent (especially Sonnet/Opus) | Excellent | Very Good | Good (code-specific models) |
| **Response Speed** | Fast (Sonnet/Haiku), Slower (Opus) | Fast (GPT-4o), Medium (GPT-4) | Fast (Flash), Medium (Pro) | Variable (depends on hardware) |
| **API Reliability** | Excellent (99.9% uptime) | Excellent (99.9% uptime) | Very Good (99.5% uptime) | Depends on infrastructure |
| **Pricing Model** | Token-based, clear tiers | Token-based, clear tiers | Token-based, generous free tier | Hardware + operational costs |
| **Privacy/Data Use** | Not used for training | Not used for training (API) | Not used for training | Complete control |
| **Tool/Function Calling** | Excellent | Excellent | Good | Limited (depends on model) |
| **Structured Output** | Good (via prompting) | Excellent (JSON mode) | Good | Limited |
| **System Prompts** | Excellent support | Good support | Good support | Variable |
| **Rate Limits** | Tier-based (generous) | Tier-based | Generous (especially free tier) | Hardware-limited |
| **Regional Availability** | Global (some restrictions) | Global (some restrictions) | Limited (expanding) | No restrictions |
| **Enterprise Features** | Available | Comprehensive | Growing | Full control |
| **Compliance** | SOC2, GDPR, HIPAA available | SOC2, GDPR, HIPAA available | SOC2, GDPR | Self-managed |
| **Support Quality** | Excellent (email, docs) | Excellent (email, docs, forum) | Good (docs, community) | Community-based |
| **Integration Ecosystem** | Growing rapidly | Extensive | Growing | Depends on implementation |
| **Multimodal** | Yes (images in, text out) | Yes (images, audio, text) | Yes (comprehensive) | Limited |
| **Code Execution** | No (tool use) | Limited | Limited | Can be implemented |
| **Best Use Case** | Thoughtful coding, complex reasoning | General purpose, established ecosystem | Long context, cost-conscious | Privacy, customization, volume |

### Provider-Specific Strengths

#### Anthropic Claude

Claude SHOULD be selected when:

- **Code Quality Priority**: Claude Sonnet 4.5 and Opus 4.5 excel at producing clean, idiomatic code
- **Safety and Reasoning**: Superior at considering edge cases and security implications
- **Long-form Analysis**: Extended code review and architectural analysis
- **Context Understanding**: Excellent at maintaining context across long conversations
- **Tool Use**: Superior function calling and tool integration capabilities

**Pricing (as of 2025)**[^7]:

- Opus 4.5: $15/1M input tokens, $75/1M output tokens
- Sonnet 4.5: $3/1M input tokens, $15/1M output tokens
- Haiku 3.5: $0.25/1M input tokens, $1.25/1M output tokens

**Rate Limits**[^8]: Scale 1 tier starts at 50K requests/day, Scale 2 at 1M requests/day

#### OpenAI GPT

GPT SHOULD be selected when:

- **Established Ecosystem**: Extensive library of tools, plugins, and integrations
- **Structured Output**: JSON mode and function calling are critical requirements
- **Multimodal Needs**: Vision, audio, and text processing in one model
- **Broad Capability**: General-purpose tasks beyond coding
- **Community Resources**: Largest community with extensive examples and patterns

**Pricing (as of 2025)**[^9]:

- GPT-4 Turbo: $10/1M input tokens, $30/1M output tokens
- GPT-4o: $5/1M input tokens, $15/1M output tokens
- GPT-4o mini: $0.15/1M input tokens, $0.60/1M output tokens

**Rate Limits**[^10]: Tier-based from 500 requests/day (free) to millions (enterprise)

#### Google Gemini

Gemini SHOULD be selected when:

- **Long Context**: Tasks requiring 1M+ token context windows
- **Cost Optimization**: Free tier available for experimentation and low-volume use
- **Google Ecosystem**: Integration with Google Cloud services
- **Multimodal Tasks**: Vision and document understanding
- **Rapid Iteration**: Fast Flash models for quick feedback loops

**Pricing (as of 2025)**[^11]:

- Gemini 1.5 Pro: $3.50/1M input tokens, $10.50/1M output tokens
- Gemini 1.5 Flash: $0.075/1M input tokens, $0.30/1M output tokens
- Gemini 1.5 Flash-8B: $0.0375/1M input tokens, $0.15/1M output tokens

**Rate Limits**[^11]: 2M tokens/minute on free tier, higher for paid

#### Self-Hosted Solutions

Self-hosted models MUST be considered when:

- **Data Privacy**: Absolute requirement that code never leaves infrastructure
- **Cost at Scale**: Processing 500M+ tokens/month
- **Customization**: Fine-tuning on proprietary codebase required
- **Control**: Need for complete control over model behavior and updates
- **Compliance**: Regulatory requirements prevent external AI services

**Popular Options**:

1. **Meta Llama 3.1 (70B/405B)**[^5]
   - General purpose, good coding capability
   - Requires significant GPU resources (A100 or H100)
   - Inference cost: ~$0.10-0.50/1M tokens depending on infrastructure

2. **CodeLlama 34B**[^5]
   - Code-specialized variant of Llama
   - Lower resource requirements than Llama 3.1 405B
   - Good for code completion and generation

3. **StarCoder2**[^6]
   - Trained specifically on code
   - Efficient for code completion tasks
   - Available in 3B, 7B, 15B variants

4. **DeepSeek Coder**[^12]
   - Excellent code generation capability
   - Competitive with GPT-4 on coding tasks
   - Available in 1.3B to 33B sizes

**Infrastructure Considerations**:

- MUST have GPU resources (minimum 1x A100 for 34B models)
- SHOULD implement caching and batching for efficiency
- MUST have robust monitoring and fallback strategies
- SHOULD plan for model update and maintenance cycles

## Model Recommendations by Task Type

### Coding Tasks

#### Feature Implementation

**Primary Recommendation**: Claude Sonnet 4.5 or GPT-4o

These models SHOULD be used because:

- Balanced cost-to-quality ratio
- Fast enough for iterative development
- Good at understanding requirements and context
- Produce production-quality code

**Example Workflow**:

```text
1. Describe feature requirements to AI
2. Request implementation with tests
3. Review and iterate on design
4. Request specific refinements
5. Final human review before merge
```

**Estimated Cost**: $0.05-0.20 per feature (moderate complexity)

#### Bug Fixing

**Primary Recommendation**: Claude Sonnet 4.5 or GPT-4o
**Budget Alternative**: Claude Haiku 3.5 or GPT-4o mini (for simple bugs)

Bug fixing workflow SHOULD:

1. Provide error message and stack trace
2. Include relevant code context (50-200 lines)
3. Request explanation before fix
4. Review AI's understanding
5. Request fix with test case

**Example Prompt Structure**:

```text
I'm getting this error: [error message]

Stack trace:
[stack trace]

Here's the relevant code:
[code snippet]

Please:
1. Explain what's causing this error
2. Suggest a fix
3. Provide a test case to prevent regression
```

**Estimated Cost**: $0.01-0.05 per bug fix

#### Refactoring

**Primary Recommendation**: Claude Opus 4.5 or GPT-4 Turbo (complex), Sonnet/GPT-4o (standard)

Large refactoring tasks MUST:

- Use premium models for planning phase
- Break down into smaller chunks
- Validate each step before proceeding
- Include comprehensive test coverage

**Refactoring Workflow**:

```text
Phase 1 (Opus/GPT-4): Analysis and Planning
- Analyze current structure
- Identify problems and code smells
- Propose refactoring approach
- Estimate impact and risk

Phase 2 (Sonnet/GPT-4o): Incremental Changes
- Implement step 1 with tests
- Validate and commit
- Implement step 2 with tests
- Validate and commit
- Continue until complete

Phase 3 (Sonnet/GPT-4o): Cleanup
- Remove dead code
- Update documentation
- Final integration tests
```

**Estimated Cost**: $0.50-5.00 for major refactoring

#### Code Generation (Boilerplate)

**Primary Recommendation**: Claude Haiku 3.5 or GPT-4o mini
**High-Volume Alternative**: Self-hosted CodeLlama

Boilerplate generation SHOULD use budget models because:

- Tasks are well-defined and simple
- Cost savings are significant at scale
- Quality is sufficient for standard patterns
- Fast response time improves developer experience

**Common Boilerplate Tasks**:

- CRUD endpoints
- Database models
- API clients
- Configuration files
- DTO/Entity mappings
- Test fixtures

**Estimated Cost**: $0.002-0.01 per generation

### Code Review Tasks

#### Security Review

**Primary Recommendation**: Claude Opus 4.5 or GPT-4 Turbo
**MUST NOT**: Use budget models for security-sensitive reviews

Security review workflow MUST:

1. Use premium models exclusively
2. Request specific vulnerability categories
3. Include threat model context
4. Validate findings with security team
5. Never auto-merge based on AI approval alone

**Review Prompt Template**:

```text
Please perform a security review of this code:

[code]

Specifically check for:
1. SQL injection vulnerabilities
2. XSS vulnerabilities
3. Authentication/authorization issues
4. Sensitive data exposure
5. CSRF vulnerabilities
6. Insecure dependencies
7. Cryptographic weaknesses
8. Input validation gaps

For each finding, provide:
- Severity (Critical/High/Medium/Low)
- Explanation
- Specific code location
- Remediation steps
```

**Estimated Cost**: $0.10-0.50 per review (depending on codebase size)

#### General Code Review

**Primary Recommendation**: Claude Sonnet 4.5 or GPT-4o

Standard code reviews SHOULD check:

- Code style and conventions
- Logic errors
- Edge cases
- Performance concerns
- Test coverage
- Documentation completeness

**Review Workflow**:

```text
1. Submit PR diff to AI
2. Provide coding standards/guidelines
3. Request structured review
4. Address findings
5. Human reviewer validates AI feedback
6. Merge after both AI and human approval
```

**Estimated Cost**: $0.03-0.15 per PR

#### Performance Review

**Primary Recommendation**: Claude Opus 4.5 or GPT-4 Turbo (critical paths), Sonnet/GPT-4o (general)

Performance review SHOULD:

- Include performance requirements (latency, throughput)
- Provide profiling data if available
- Request specific optimization suggestions
- Consider algorithmic complexity
- Evaluate database query efficiency

**Estimated Cost**: $0.05-0.30 per review

### Documentation Tasks

#### API Documentation

**Primary Recommendation**: Claude Sonnet 4.5 or GPT-4o
**Budget Alternative**: Claude Haiku 3.5 (for simple endpoints)

API documentation generation SHOULD:

- Include code context
- Request OpenAPI/Swagger format
- Generate examples for each endpoint
- Include error cases
- Document authentication/authorization

**Example Workflow**:

```text
Input: API endpoint code
Output:
- Endpoint description
- Parameters (path, query, body)
- Request/response examples
- Error codes and meanings
- Authentication requirements
- Rate limiting information
```

**Estimated Cost**: $0.02-0.08 per endpoint

#### Code Documentation (Docstrings)

**Primary Recommendation**: Claude Haiku 3.5 or GPT-4o mini

Docstring generation SHOULD:

- Use budget models (simple, repetitive task)
- Follow language-specific conventions
- Include parameter types
- Document exceptions/errors
- Provide usage examples for public APIs

**Batch Processing Approach**:

```text
Process multiple functions in single request:
- Submit 10-20 functions at once
- Request consistent format
- Review and commit in batches
- Significant cost savings vs. per-function
```

**Estimated Cost**: $0.001-0.005 per function

#### Architecture Documentation

**Primary Recommendation**: Claude Opus 4.5 or GPT-4 Turbo

Architecture documentation MUST:

- Use premium models for accuracy
- Include comprehensive codebase context
- Generate diagrams (via Mermaid, PlantUML)
- Document design decisions
- Explain trade-offs

**Documentation Workflow**:

```text
Phase 1: Analysis
- Analyze codebase structure
- Identify main components
- Map dependencies
- Understand data flow

Phase 2: Generation
- Write architecture overview
- Create system diagrams
- Document component interactions
- Explain design patterns used

Phase 3: Validation
- Review with architecture team
- Update based on feedback
- Maintain as living document
```

**Estimated Cost**: $0.50-3.00 per major documentation effort

#### README and Guides

**Primary Recommendation**: Claude Sonnet 4.5 or GPT-4o

README generation SHOULD include:

- Project overview
- Installation instructions
- Quick start guide
- Configuration options
- Usage examples
- Contributing guidelines
- License information

**Estimated Cost**: $0.05-0.20 per README

### Testing Tasks

#### Unit Test Generation

**Primary Recommendation**: Claude Sonnet 4.5 or GPT-4o
**Budget Alternative**: Claude Haiku 3.5 (for simple functions)

Unit test generation SHOULD:

- Cover happy path
- Include edge cases
- Test error conditions
- Follow existing test patterns
- Use appropriate assertions

**Test Generation Prompt**:

```text
Generate unit tests for this function:

[function code]

Requirements:
- Use [testing framework]
- Test happy path
- Test edge cases: [list specific cases]
- Test error conditions
- Achieve >90% code coverage
- Follow existing test patterns in: [example test file]
```

**Estimated Cost**: $0.02-0.10 per test suite

#### Integration Test Generation

**Primary Recommendation**: Claude Sonnet 4.5 or GPT-4o

Integration tests SHOULD:

- Use real or realistic test doubles
- Cover main user flows
- Include setup and teardown
- Test component interactions
- Validate data consistency

**Estimated Cost**: $0.05-0.25 per integration test

#### Test Data Generation

**Primary Recommendation**: Claude Haiku 3.5 or GPT-4o mini
**High-Volume Alternative**: Self-hosted model

Test data generation SHOULD:

- Use budget models (cost-effective for high volume)
- Include realistic variations
- Cover boundary conditions
- Respect data constraints
- Generate large datasets efficiently

**Example Use Cases**:

- Mock API responses
- Database seed data
- User profiles
- Transaction records
- Event streams

**Estimated Cost**: $0.001-0.01 per dataset

#### End-to-End Test Generation

**Primary Recommendation**: Claude Sonnet 4.5 or GPT-4o

E2E tests SHOULD:

- Cover critical user journeys
- Include realistic scenarios
- Handle async operations
- Include proper wait conditions
- Validate UI and data state

**Estimated Cost**: $0.10-0.40 per E2E test scenario

## Workflow Patterns

### Explore-Plan-Code-Commit Pattern

This workflow pattern SHOULD be the default approach for medium to complex tasks.

#### Phase 1: Explore (Model: Opus/GPT-4 or Sonnet/GPT-4o)

**Objective**: Understand the problem space and existing codebase

**Steps**:

1. Describe the task to AI
2. Ask AI to analyze relevant existing code
3. Request potential approaches
4. Discuss trade-offs
5. Identify potential challenges

**Example Session**:

```text
Developer: I need to add rate limiting to our API. Here's our current
middleware structure: [code]. What approaches should I consider?

AI: [Analysis of existing code]
[Presents 3 approaches with trade-offs]
[Identifies integration points]
[Highlights potential issues]

Developer: Approach 2 looks good. What about distributed rate limiting
across multiple servers?

AI: [Discusses Redis-based approach]
[Provides implementation considerations]
[Suggests libraries]
```

**Time Investment**: 10-30 minutes
**Cost**: $0.05-0.30
**Value**: Prevents costly mistakes, considers more alternatives

#### Phase 2: Plan (Model: Opus/GPT-4 or Sonnet/GPT-4o)

**Objective**: Create detailed implementation plan

**Steps**:

1. Break down task into subtasks
2. Identify files to modify
3. Determine test strategy
4. Plan commit strategy
5. Estimate effort

**Example Output**:

```text
Implementation Plan: API Rate Limiting

Subtasks:
1. Add Redis dependency and configuration
2. Create RateLimitMiddleware class
3. Implement token bucket algorithm
4. Add rate limit headers to responses
5. Create integration tests
6. Update API documentation
7. Add monitoring/logging

Files to Modify:
- src/middleware/index.ts (add middleware)
- src/config/redis.ts (new file)
- src/types/middleware.ts (add types)
- tests/integration/rateLimit.test.ts (new file)
- docs/api.md (update)

Test Strategy:
- Unit tests for token bucket logic
- Integration tests for middleware behavior
- Load tests for performance validation

Commits:
1. Add Redis configuration
2. Implement rate limit middleware
3. Add tests
4. Update documentation

Estimated Effort: 4-6 hours
```

**Time Investment**: 10-20 minutes
**Cost**: $0.03-0.15
**Value**: Clear roadmap, better estimates, fewer iterations

#### Phase 3: Code (Model: Sonnet/GPT-4o or Haiku/mini)

**Objective**: Implement planned changes

**Steps**:

1. Implement subtasks in order
2. Generate code for each subtask
3. Review and refine each piece
4. Run tests continuously
5. Iterate based on failures

**Implementation Approach**:

```text
For each subtask:
1. Request implementation from AI
2. Review generated code
3. Request modifications if needed
4. Run tests locally
5. Fix any issues
6. Move to next subtask
```

**Model Selection**:

- Complex logic: Sonnet/GPT-4o
- Boilerplate: Haiku/mini
- Critical sections: Opus/GPT-4

**Time Investment**: Varies by task size
**Cost**: $0.10-2.00 for moderate features
**Value**: Faster implementation, fewer bugs

#### Phase 4: Commit (Model: Haiku/mini for messages)

**Objective**: Create clean, reviewable commits

**Steps**:

1. Review all changes
2. Group related changes
3. Generate commit messages
4. Create PR description
5. Request review

**Commit Message Generation**:

```text
Developer: Generate a commit message for these changes: [diff]

AI:
feat: Add Redis-based rate limiting middleware

- Implement token bucket algorithm for rate limiting
- Add configurable limits per endpoint
- Include rate limit headers in responses
- Add integration tests for rate limit behavior

This allows us to protect the API from abuse while providing
clear feedback to clients about their rate limit status.
```

**Time Investment**: 5-10 minutes
**Cost**: $0.01-0.05
**Value**: Better commit history, clearer communication

### TDD with AI Pattern

Test-Driven Development with AI assistance SHOULD follow this workflow:

#### Step 1: Generate Test Cases (Model: Sonnet/GPT-4o)

**Process**:

```text
Developer: I need to implement a function that validates email addresses.
Generate comprehensive test cases.

AI: [Provides test cases]
- Valid standard email
- Valid email with subdomain
- Valid email with plus addressing
- Invalid: no @ symbol
- Invalid: multiple @ symbols
- Invalid: no domain
- Invalid: invalid domain format
- Invalid: no TLD
- Invalid: spaces in email
- Edge case: very long email
- Edge case: international characters
```

**Output**: List of test cases covering happy path, edge cases, and error conditions

#### Step 2: Write Tests First (Model: Sonnet/GPT-4o or Haiku/mini)

**Process**:

```text
Developer: Write tests for these cases using Jest:
[List of test cases]

AI: [Generates test code]

describe('validateEmail', () => {
  it('should accept valid standard email', () => {
    expect(validateEmail('user@example.com')).toBe(true);
  });

  it('should accept valid email with subdomain', () => {
    expect(validateEmail('user@mail.example.com')).toBe(true);
  });

  // ... more tests

  it('should reject email with no @ symbol', () => {
    expect(validateEmail('userexample.com')).toBe(false);
  });

  // ... more tests
});
```

**Validation**: Developer MUST review tests before proceeding

#### Step 3: Implement to Pass Tests (Model: Sonnet/GPT-4o)

**Process**:

```text
Developer: Implement validateEmail function to pass these tests:
[Test code]

AI: [Generates implementation]

function validateEmail(email: string): boolean {
  // Implementation that passes all tests
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  if (!email || typeof email !== 'string') {
    return false;
  }

  // Additional validation logic

  return emailRegex.test(email);
}
```

#### Step 4: Refactor (Model: Sonnet/GPT-4o)

**Process**:

```text
Developer: The function works but is hard to read. Refactor for clarity
while keeping all tests passing.

AI: [Provides refactored version]

function validateEmail(email: string): boolean {
  if (!isString(email)) return false;
  if (hasWhitespace(email)) return false;
  if (!hasAtSymbol(email)) return false;
  if (hasMultipleAtSymbols(email)) return false;
  if (!hasValidDomain(email)) return false;

  return true;
}

// Helper functions with clear purposes
function isString(value: any): boolean { ... }
function hasWhitespace(str: string): boolean { ... }
// ... etc
```

**Benefits of TDD with AI**:

- AI excels at generating comprehensive test cases
- Tests serve as specification for AI implementation
- Reduces debugging time
- Ensures edge cases are covered
- Produces more maintainable code

### Pair Programming with AI Pattern

This pattern treats AI as a pair programming partner for real-time development.

#### Continuous Collaboration Mode

**Setup**:

- Keep AI session open during development
- Share context continuously
- Get instant feedback
- Iterate rapidly

**Example Session**:

```text
Developer: I'm starting work on user authentication. Here's the user model:
[code]

AI: I see you have username and passwordHash fields. For authentication,
you'll want to consider:
1. Password validation rules
2. Rate limiting on login attempts
3. Session management
4. Password reset flow

Would you like to start with the login endpoint or password validation?

Developer: Let's start with password validation. Company policy requires
8+ characters, one uppercase, one number, one special character.

AI: Here's a password validation function:
[code]

Developer: Good, but I need it to return specific error messages for each
requirement that fails.

AI: Updated version with detailed error messages:
[code]

Developer: Perfect. Now let's do the login endpoint.

[Continues...]
```

**Benefits**:

- Immediate feedback
- Course correction before investing time
- Knowledge sharing
- Faster problem resolution

**Best Practices**:

- Share context upfront
- Ask for explanations, not just code
- Challenge AI suggestions
- Maintain conversation history
- Take breaks to review independently

### Code Review with AI Pattern

AI-assisted code review SHOULD complement, not replace, human review.

#### Pre-Human Review Pattern

**Workflow**:

```text
1. Developer completes implementation
2. Run AI code review first
3. Address AI feedback
4. Submit for human review
5. Human reviewer sees cleaner code
```

**AI Review Prompt Template**:

```text
Please review this pull request:

Files changed:
[File 1]: [diff]
[File 2]: [diff]

Our coding standards:
- [Standard 1]
- [Standard 2]
- [Standard 3]

Please check for:
1. Code style violations
2. Potential bugs
3. Edge cases not handled
4. Performance issues
5. Security concerns
6. Test coverage gaps
7. Documentation completeness

Provide specific line numbers and suggestions.
```

**AI Review Output Format**:

```text
## Critical Issues
- [File:Line] Security: SQL injection vulnerability in user input handling
- [File:Line] Bug: Potential null pointer exception when user is undefined

## Important Issues
- [File:Line] Performance: N+1 query problem in user data fetching
- [File:Line] Edge case: No validation for empty array input

## Suggestions
- [File:Line] Style: Consider extracting this logic to a separate function
- [File:Line] Readability: Complex conditional could be simplified

## Positive Observations
- Good test coverage (95%)
- Clear error messages
- Proper input validation
```

**Benefits**:

- Catches obvious issues before human review
- Frees human reviewers for higher-level concerns
- Faster review cycles
- More consistent standards enforcement

#### Parallel Review Pattern

**Workflow**:

```text
1. Submit PR
2. Both AI and human review simultaneously
3. Compare findings
4. Address all unique issues from both
5. Learn from differences
```

**Value**: AI may catch mechanical issues while humans catch design issues

### Iterative Refinement Pattern

For complex implementations, iterative refinement SHOULD be used:

#### Iteration Cycle

**Round 1: Basic Implementation**

- Model: Sonnet/GPT-4o
- Goal: Working solution
- Quality: Acceptable
- Cost: Low

**Round 2: Improvement**

- Model: Same or upgrade to Opus/GPT-4
- Goal: Handle edge cases
- Quality: Good
- Cost: Medium

**Round 3: Polish**

- Model: Opus/GPT-4 for critical, Sonnet/GPT-4o otherwise
- Goal: Production-ready
- Quality: Excellent
- Cost: Higher

**Example**:

```text
Round 1:
Developer: Implement a caching layer for API responses
AI: [Provides basic in-memory cache]
Result: Works but not production-ready

Round 2:
Developer: Update to handle cache expiration and memory limits
AI: [Adds TTL and LRU eviction]
Result: Better but needs distribution support

Round 3:
Developer: Make it work across multiple server instances using Redis
AI: [Implements distributed caching with Redis]
Result: Production-ready solution

Total cost: $0.15 vs $0.40 if started with premium model
Total time: 45 min vs potentially more with wrong initial approach
```

## Context Management Strategies

Effective context management is CRITICAL for AI assistance quality. Poor context leads to:

- Incorrect assumptions
- Inappropriate solutions
- Style inconsistencies
- Integration problems

### Context Window Optimization

#### Understanding Context Limits

Teams MUST understand and respect context window limits:

| Model | Context Window | Practical Limit | Files (avg 500 lines) |
|-------|---------------|-----------------|----------------------|
| Claude Opus/Sonnet | 200K tokens | ~150K tokens | ~100-120 files |
| GPT-4 Turbo/4o | 128K tokens | ~100K tokens | ~60-80 files |
| Gemini 1.5 Pro | 1M tokens | ~800K tokens | ~500-600 files |
| Budget models | 128-200K tokens | ~100K tokens | ~60-80 files |
| Self-hosted | 4-32K tokens | ~3-25K tokens | ~2-15 files |

**Note**: Actual capacity varies based on code density and comment ratio

#### Prioritizing Context

When context limits are approached, prioritize in this order:

1. **MUST Include** (Priority 1):
   - Current file being modified
   - Direct dependencies
   - Interface definitions
   - Type definitions
   - Configuration relevant to task

2. **SHOULD Include** (Priority 2):
   - Similar existing implementations
   - Test files for context
   - Related utility functions
   - Relevant documentation

3. **MAY Include** (Priority 3):
   - Broader codebase structure
   - Distantly related files
   - Historical context
   - General documentation

### Context Assembly Strategies

#### File-Level Context

**For Single-File Tasks**:

```text
Provide:
- Complete file content
- Import dependencies (interfaces/types)
- Related test file
- Relevant documentation

Example:
"""
I need to modify this function:

[complete file content]

Here are the type definitions it uses:
[type definitions]

Here's how it's currently tested:
[test file]

Task: [specific task]
"""
```

**Estimated tokens**: 2K-10K

#### Module-Level Context

**For Feature Development**:

```text
Provide:
- Main files in module (3-5 files)
- Shared types/interfaces
- Module README or documentation
- Example usage

Structure:
"""
I'm working on the [module name] module.

Main files:
--- src/module/file1.ts ---
[content]

--- src/module/file2.ts ---
[content]

Shared types:
--- src/types/module.ts ---
[content]

Current usage example:
[example code]

Task: [specific task]
"""
```

**Estimated tokens**: 10K-30K

#### System-Level Context

**For Architectural Tasks**:

```text
Provide:
- High-level architecture diagram (text/Mermaid)
- Key component interfaces
- Data flow description
- Integration points
- Critical constraints

Example:
"""
System architecture:
[Mermaid diagram or text description]

Key components:
1. [Component]: [brief description + interface]
2. [Component]: [brief description + interface]

Data flow:
[Sequence of operations]

Constraints:
- [Performance requirement]
- [Security requirement]
- [Scalability requirement]

Task: [architectural decision needed]
"""
```

**Estimated tokens**: 5K-20K

### Context Caching Strategies

Some providers offer context caching to reduce costs and latency:

#### Claude Prompt Caching

Claude SHOULD use prompt caching when:

- Reusing same codebase context across multiple requests
- Iterating on implementation with stable context
- Processing multiple related tasks

**How it works**:

- First request: Full cost
- Subsequent requests (within 5 minutes): 90% discount on cached portion
- Automatically applies to prompts >1024 tokens

**Example usage**:

```text
Request 1:
Context (cached): [10K tokens of codebase - costs full price]
Task: Implement feature A
Response: [implementation]

Request 2 (within 5 min):
Context (cached): [same 10K tokens - costs 10% of original]
Task: Now add tests for feature A
Response: [tests]

Request 3 (within 5 min):
Context (cached): [same 10K tokens - costs 10% of original]
Task: Update documentation
Response: [docs]

Cost savings: ~60% vs. non-cached
```

**Best practices**:

- Structure prompts with stable context first
- Make multiple related requests in succession
- Batch related tasks together

#### OpenAI Context Management

GPT-4 does not offer automatic caching, but SHOULD:

- Use conversation history efficiently
- Reference previous responses rather than repeating
- Break long sessions into focused conversations

### Dynamic Context Selection

For large codebases, teams SHOULD implement dynamic context selection:

#### Similarity-Based Selection

**Process**:

1. Index codebase with embeddings
2. For each task, find most relevant files
3. Include top N most similar files
4. Add explicit dependencies

**Tools**:

- `code2vec` for code embeddings
- Vector databases (Pinecone, Weaviate)
- Custom similarity scoring

**Example**:

```text
Task: Add authentication to API endpoint

Similarity search finds:
1. existing-auth-middleware.ts (0.95 similarity)
2. user-service.ts (0.87 similarity)
3. auth-types.ts (0.85 similarity)
4. another-protected-endpoint.ts (0.78 similarity)

Include top 3 + explicit dependency (express types)
```

#### Dependency Graph Context

**Process**:

1. Build dependency graph of codebase
2. For target file, include:
   - File itself
   - Direct dependencies
   - Dependents (who uses it)
   - Shared utilities

**Example**:

```text
Target: user-controller.ts

Dependency graph:
user-controller.ts
├── Dependencies:
│   ├── user-service.ts
│   ├── auth-middleware.ts
│   └── types/user.ts
└── Dependents:
    ├── routes/api.ts
    └── tests/user-controller.test.ts

Include all these files as context
```

### Context Documentation Patterns

Teams SHOULD maintain context documentation to improve AI assistance:

#### Codebase Overview Document

**Location**: `.ai/codebase-overview.md`

**Contents**:

```markdown
# Codebase Overview

## Architecture
[High-level architecture description]

## Directory Structure
- `/src/api` - REST API endpoints
- `/src/services` - Business logic
- `/src/models` - Data models
- `/src/utils` - Utility functions

## Key Technologies
- Framework: Express.js
- Database: PostgreSQL
- ORM: TypeORM
- Testing: Jest

## Coding Standards
- Style guide: Airbnb
- Naming: camelCase for variables, PascalCase for classes
- File structure: One class per file

## Common Patterns
- Service layer pattern for business logic
- Repository pattern for data access
- Dependency injection using tsyringe
```

**Usage**:

```text
Include in context for new team members or AI:
"Here's our codebase overview: [content]
Now help me implement [feature]"
```

#### Decision Log

**Location**: `.ai/decisions.md`

**Contents**:

```markdown
# Architecture Decision Log

## ADR-001: Use TypeORM for database access
Date: 2024-01-15
Status: Accepted

Context: Need ORM for PostgreSQL access
Decision: Use TypeORM
Alternatives considered: Prisma, Sequelize
Rationale: Team familiarity, TypeScript support

## ADR-002: Implement JWT-based authentication
Date: 2024-02-01
Status: Accepted

Context: Need stateless authentication
Decision: JWT with RS256 signing
Alternatives considered: Sessions, OAuth only
Rationale: Scalability, microservices compatibility
```

**Usage**: Helps AI understand why things are done certain ways

### Multi-Turn Conversation Management

For complex tasks, maintain conversation continuity:

#### Conversation Structuring

**Pattern**:

```text
Turn 1: Set context and explore
Turn 2: Plan approach
Turn 3: Implement part 1
Turn 4: Implement part 2
Turn 5: Integrate and test
Turn 6: Documentation
```

**Benefits**:

- Build shared understanding
- Leverage conversation memory
- Avoid repeating context
- Natural refinement process

#### Conversation Splitting

When to start new conversation:

- Context has drifted from original task
- Conversation becomes too long (>20 turns)
- Switching to unrelated task
- AI responses become inconsistent

**Best practice**: Summarize previous conversation when starting new one

### Context Templates

Teams SHOULD create templates for common context scenarios:

#### Bug Fix Template

```markdown
# Bug Fix Context

## Error Information
Error message: [error]
Stack trace: [trace]
Frequency: [how often]
Environment: [dev/staging/prod]

## Relevant Code
[affected files]

## Recent Changes
[recent commits to area]

## Expected vs Actual
Expected: [behavior]
Actual: [behavior]

## Steps to Reproduce
1. [step]
2. [step]

## Task
[what needs to be done]
```

#### Feature Implementation Template

```markdown
# Feature Implementation Context

## Requirements
[user story or spec]

## Acceptance Criteria
- [ ] [criterion 1]
- [ ] [criterion 2]

## Relevant Existing Code
[similar features or related code]

## Technical Constraints
- [constraint 1]
- [constraint 2]

## Design Decisions Needed
- [decision 1]
- [decision 2]

## Task
[implementation request]
```

## Cost Optimization Patterns

Managing AI costs is essential for sustainable adoption. Teams MUST implement cost optimization strategies.

### Cost Monitoring

#### Establishing Baselines

Teams MUST track:

- Cost per developer per month
- Cost per task type
- Cost per project phase
- Token usage patterns

**Example Metrics Dashboard**:

```text
Monthly AI Costs by Task Type:
- Code generation: $45 (12K requests)
- Code review: $30 (8K requests)
- Documentation: $15 (3K requests)
- Debugging: $25 (5K requests)
Total: $115/developer/month

Cost by Model:
- Opus/GPT-4: $35 (30% of cost, 5% of requests)
- Sonnet/GPT-4o: $60 (52% of cost, 60% of requests)
- Haiku/mini: $20 (18% of cost, 35% of requests)
```

#### Setting Budgets

**Recommended approach**:

1. Track costs for 1-2 months
2. Calculate average per developer
3. Set budget at 120% of average
4. Review monthly, adjust quarterly

**Typical ranges** (per developer per month):

- Light usage: $20-50
- Moderate usage: $50-150
- Heavy usage: $150-400
- Team leads/architects: $300-800

### Model Tiering Strategy

Implement automatic model selection based on task characteristics:

#### Decision Matrix

```text
Task Complexity: [Low | Medium | High]
Task Criticality: [Low | Medium | High]
Context Size: [Small | Medium | Large]
→ Model Selection

Examples:

Low complexity + Low criticality + Small context
→ Haiku/GPT-4o mini
Example: Simple docstring, basic CRUD

Medium complexity + Medium criticality + Medium context
→ Sonnet/GPT-4o
Example: Feature implementation, standard refactoring

High complexity + High criticality + Large context
→ Opus/GPT-4
Example: Architecture design, security review

Low complexity + High criticality + Small context
→ Sonnet/GPT-4o (not Opus - unnecessary cost)
Example: Fixing critical bug with clear cause
```

#### Automatic Routing

**Implementation**:

```typescript
function selectModel(task: Task): Model {
  const complexity = assessComplexity(task);
  const criticality = assessCriticality(task);
  const contextSize = calculateContextSize(task);

  // High criticality always uses at least mid-tier
  if (criticality === 'high') {
    if (complexity === 'high') return Model.OPUS;
    return Model.SONNET;
  }

  // Low criticality can use budget models
  if (criticality === 'low') {
    if (complexity === 'low') return Model.HAIKU;
    if (complexity === 'medium') return Model.SONNET;
    return Model.SONNET; // Even high complexity, low criticality
  }

  // Medium criticality
  if (complexity === 'high') return Model.OPUS;
  if (complexity === 'medium') return Model.SONNET;
  return Model.HAIKU;
}
```

### Batching Strategies

Batching multiple operations reduces per-request overhead:

#### Batch Processing Pattern

**Instead of**:

```text
Request 1: Generate docstring for function A
Request 2: Generate docstring for function B
Request 3: Generate docstring for function C
Cost: 3 × overhead + 3 × generation cost
```

**Do this**:

```text
Single Request: Generate docstrings for functions A, B, and C

Functions:
[Function A code]
[Function B code]
[Function C code]

Please generate docstrings for all three functions.

Cost: 1 × overhead + 1 × generation cost
Savings: ~60% vs individual requests
```

**Optimal batch sizes**:

- Documentation: 10-20 items
- Simple code generation: 5-10 items
- Code review: 3-5 files
- Refactoring: 2-3 related changes

#### Batch Timing

**Schedule batch operations for**:

- Off-peak hours (lower rate limits hit)
- End of day cleanup
- Weekly documentation updates
- Monthly codebase analysis

### Caching Strategies

#### Response Caching

For deterministic tasks, cache AI responses:

**Implementation**:

```typescript
interface CacheKey {
  taskType: string;
  codeHash: string;
  modelVersion: string;
}

async function getAIResponse(
  task: string,
  code: string
): Promise<string> {
  const key = createCacheKey(task, code);

  // Check cache first
  const cached = await cache.get(key);
  if (cached) {
    return cached;
  }

  // Call AI
  const response = await callAI(task, code);

  // Cache for future
  await cache.set(key, response, TTL_7_DAYS);

  return response;
}
```

**Good candidates for caching**:

- Documentation generation (rarely changes)
- Test generation (for stable code)
- Code review of common patterns
- Error explanations (same error = same explanation)

**Poor candidates**:

- Exploratory conversations
- Context-dependent tasks
- Rapidly changing code
- Personalized responses

#### Prompt Template Caching

Reuse prompt structures:

```typescript
const templates = {
  codeReview: `Review this code for:
- Style issues
- Bugs
- Performance
- Security

Code:
{CODE}`,

  testGeneration: `Generate tests for:
{CODE}

Requirements:
- Use {FRAMEWORK}
- Cover edge cases
- Achieve >90% coverage`,
};

// Reuse template, just replace variables
const prompt = templates.codeReview.replace('{CODE}', actualCode);
```

### Request Optimization

#### Token Reduction Techniques

**Minify context without losing meaning**:

1. **Remove comments for AI context**:

```typescript
// Before: 1500 tokens
function calculateTotal(items: Item[]): number {
  // Sum up all item prices
  // Apply any discounts
  // Add tax if applicable
  return items.reduce((sum, item) => {
    // ... implementation
  }, 0);
}

// After: 800 tokens (same meaning for AI)
function calculateTotal(items: Item[]): number {
  return items.reduce((sum, item) => {
    // ... implementation
  }, 0);
}
```

1. **Use file summaries for distant context**:

```typescript
// Instead of including full file:
--- services/user-service.ts (300 tokens) ---
[full file content]

// Use summary:
--- services/user-service.ts ---
// Handles user CRUD operations
// Key methods: createUser, getUser, updateUser, deleteUser
// Uses UserRepository for data access
// Includes validation and error handling
```

1. **Selective imports**:

```typescript
// Don't include full dependency files
// Instead, include just the interface:

// From: (showing full implementation - 2000 tokens)
--- node_modules/@types/express/index.d.ts ---
[entire file]

// To: (just what's needed - 100 tokens)
--- Types from Express ---
interface Request { body: any; params: any; query: any; }
interface Response { json(data: any): void; status(code: number): Response; }
```

#### Streaming for Long Responses

Use streaming responses to:

- Start processing sooner
- Reduce perceived latency
- Cancel early if direction is wrong
- Provide progress feedback

```typescript
async function generateWithStreaming(prompt: string) {
  const stream = await openai.chat.completions.create({
    model: 'gpt-4o',
    messages: [{ role: 'user', content: prompt }],
    stream: true,
  });

  for await (const chunk of stream) {
    const content = chunk.choices[0]?.delta?.content || '';
    process.stdout.write(content); // Show immediately

    // Can cancel if output is going wrong direction
    if (shouldCancel(content)) {
      stream.controller.abort();
      break;
    }
  }
}
```

### Cost-Aware Development Practices

#### Developer Education

Teams MUST educate developers on:

- Cost per request for different models
- How to choose appropriate models
- Impact of context size on cost
- Batching opportunities

**Example training**:

```text
Cost Awareness 101:

1. Model costs (per 1M tokens input):
   - Haiku: $0.25 (cheapest)
   - Sonnet: $3 (12x more)
   - Opus: $15 (60x more)

2. Average request sizes:
   - Simple task: 1K-5K tokens
   - Medium task: 5K-20K tokens
   - Complex task: 20K-100K tokens

3. Quick math:
   - 100 simple tasks with Haiku: ~$0.03
   - 100 simple tasks with Opus: ~$1.80
   - Same output quality for simple tasks!

4. Rule of thumb:
   - Use cheapest model that produces acceptable results
   - Upgrade only when necessary
   - Batch similar operations
   - Monitor your personal usage
```

#### Usage Analytics

Provide developers with personal usage dashboards:

```text
Your AI Usage This Month:

Requests: 847
Total tokens: 12.3M input, 3.1M output
Cost: $127.50

Breakdown by model:
- Opus: 23 requests (3%), $45.20 (35%)
- Sonnet: 512 requests (60%), $68.30 (54%)
- Haiku: 312 requests (37%), $14.00 (11%)

Recommendations:
- You used Opus for 8 documentation tasks - try Sonnet
- Good use of Haiku for code completion
- Average context size: 18K tokens - consider reducing
```

### Free Tier Maximization

For teams with budget constraints:

#### Free Tier Limits (2025)

| Provider | Free Tier | Limits |
|----------|-----------|--------|
| Claude | Limited trial | ~50 requests/day on free |
| OpenAI | $5 credit (new users) | Expires after 3 months |
| Gemini | Generous free tier | 60 requests/minute |
| Groq | Free tier available | Rate limited |

#### Strategy for Free Tiers

1. **Use Gemini for exploration**: Generous free tier for learning
2. **Reserve paid tier for production**: Use Claude/OpenAI for critical work
3. **Self-host for volume**: Once usage exceeds free tiers significantly
4. **Rotate accounts carefully**: Check ToS, many prohibit multiple accounts

### ROI Monitoring

Teams MUST track return on investment:

#### Metrics to Track

**Time Savings**:

```text
Task: Implement authentication feature

Without AI:
- Research: 1 hour
- Implementation: 4 hours
- Testing: 1 hour
- Documentation: 0.5 hour
Total: 6.5 hours

With AI:
- Research (with AI): 0.5 hour
- Implementation (with AI): 2 hours
- Testing (with AI): 0.5 hour
- Documentation (with AI): 0.25 hour
Total: 3.25 hours

Time saved: 3.25 hours
AI cost: $2.50
Developer cost: $150/hour (loaded)
ROI: $487.50 saved / $2.50 cost = 195:1
```

**Quality Improvements**:

- Bugs prevented (AI review caught)
- Security issues identified
- Test coverage increase
- Documentation completeness

**Velocity Improvement**:

- Story points per sprint before/after
- Features delivered per quarter
- Time to production

## Quality Assurance for AI Output

AI-generated code MUST undergo rigorous quality assurance. Teams MUST NOT merge
AI-generated code without validation.

### Multi-Level Review Process

#### Level 1: Automated Validation (MUST)

All AI-generated code MUST pass:

1. **Linting**:

```bash
# Run linter
npm run lint

# Auto-fix where possible
npm run lint:fix

# Fail CI if lint errors remain
```

1. **Type Checking**:

```bash
# TypeScript
tsc --noEmit

# Python
mypy src/

# Go
go vet ./...
```

1. **Unit Tests**:

```bash
# Run existing tests
npm test

# Check coverage
npm run test:coverage

# Require minimum coverage (e.g., 80%)
```

1. **Security Scanning**:

```bash
# Dependency vulnerabilities
npm audit

# Static security analysis
semgrep --config=auto

# Secret detection
gitleaks detect
```

1. **Formatting**:

```bash
# Ensure consistent formatting
prettier --check .

# Auto-format
prettier --write .
```

**CI Pipeline Example**:

```yaml
# .github/workflows/ai-code-validation.yml
name: AI Code Validation

on: [pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Lint
        run: npm run lint

      - name: Type Check
        run: npm run type-check

      - name: Test
        run: npm test

      - name: Security Scan
        run: npm audit && semgrep --config=auto

      - name: Format Check
        run: prettier --check .
```

#### Level 2: Code Review (MUST)

Human review MUST check:

1. **Logic Correctness**:
   - Does it solve the actual problem?
   - Are edge cases handled?
   - Is error handling appropriate?

2. **Integration**:
   - Does it fit with existing architecture?
   - Are patterns consistent with codebase?
   - Does it respect boundaries?

3. **Performance**:
   - Are there obvious performance issues?
   - Is complexity reasonable (O(n) vs O(n²))?
   - Are resources properly managed?

4. **Security**:
   - Input validation present?
   - No injection vulnerabilities?
   - Authentication/authorization correct?
   - Sensitive data handled properly?

5. **Maintainability**:
   - Is code readable?
   - Are names meaningful?
   - Is complexity justified?
   - Is documentation sufficient?

**Review Checklist**:

```markdown
## AI-Generated Code Review Checklist

### Correctness
- [ ] Solves the stated problem
- [ ] Handles edge cases
- [ ] Error handling is appropriate
- [ ] No logical errors

### Integration
- [ ] Follows existing patterns
- [ ] Consistent with codebase style
- [ ] Respects module boundaries
- [ ] Doesn't duplicate existing functionality

### Performance
- [ ] No obvious performance issues
- [ ] Appropriate data structures
- [ ] Efficient algorithms
- [ ] Resources properly cleaned up

### Security
- [ ] Input validation present
- [ ] No injection vulnerabilities
- [ ] Auth/authz correct
- [ ] No hardcoded secrets
- [ ] Sensitive data protected

### Maintainability
- [ ] Code is readable
- [ ] Names are meaningful
- [ ] Comments explain why, not what
- [ ] Complexity is justified
- [ ] Tests are comprehensive

### AI-Specific Checks
- [ ] Verified AI didn't hallucinate APIs
- [ ] Checked for common AI mistakes
- [ ] Validated assumptions made by AI
- [ ] Confirmed best practices followed
```

#### Level 3: Testing in Context (SHOULD)

Beyond unit tests, SHOULD verify:

1. **Integration Tests**:

```typescript
// Test AI-generated component integrates correctly
describe('AI-generated UserAuth integration', () => {
  it('should integrate with existing auth flow', async () => {
    const result = await fullAuthenticationFlow();
    expect(result).toBeDefined();
  });

  it('should work with all user types', async () => {
    for (const userType of USER_TYPES) {
      const result = await authenticateUser(userType);
      expect(result.authenticated).toBe(true);
    }
  });
});
```

1. **Manual Testing**:
   - Run feature locally
   - Test happy path
   - Try to break it
   - Verify error messages

2. **Performance Testing** (for critical paths):

```typescript
// Load test AI-generated endpoint
describe('Performance', () => {
  it('should handle 1000 req/s', async () => {
    const results = await loadTest({
      url: '/api/endpoint',
      requestsPerSecond: 1000,
      duration: 60,
    });

    expect(results.p95).toBeLessThan(100); // 95th percentile < 100ms
    expect(results.errorRate).toBeLessThan(0.01); // < 1% errors
  });
});
```

### Common AI Mistakes to Watch For

#### Hallucinated APIs

**Problem**: AI invents functions or methods that don't exist

**Example**:

```typescript
// AI might generate:
import { validateEmail } from '@utils/validation';

// But @utils/validation doesn't export validateEmail
```

**Detection**:

- Run type checking
- Verify imports exist
- Check API documentation

**Prevention**:

- Provide actual API documentation in context
- Include real import examples
- Use AI with codebase knowledge

#### Outdated Patterns

**Problem**: AI uses deprecated or outdated approaches

**Example**:

```javascript
// AI might generate React class component:
class UserProfile extends React.Component {
  constructor(props) {
    super(props);
    this.state = { user: null };
  }
  // ...
}

// When codebase uses hooks:
function UserProfile() {
  const [user, setUser] = useState(null);
  // ...
}
```

**Detection**:

- Code review for outdated patterns
- Linting rules for deprecated features
- Compare with existing codebase

**Prevention**:

- Specify framework version in prompt
- Provide current pattern examples
- Include recent code as context

#### Over-Engineering

**Problem**: AI creates unnecessarily complex solutions

**Example**:

```typescript
// AI might generate full factory pattern for simple task:
interface UserFactory {
  createUser(type: string): User;
}

class ConcreteUserFactory implements UserFactory {
  createUser(type: string): User {
    // Complex factory logic
  }
}

// When simple function would suffice:
function createUser(type: string): User {
  return new User(type);
}
```

**Detection**:

- Review complexity vs requirements
- Check if simpler solution exists
- Validate design patterns are necessary

**Prevention**:

- Specify "simple" or "minimal" in prompts
- Provide simple examples as templates
- Request explanation of design choices

#### Security Oversights

**Problem**: AI misses security considerations

**Example**:

```typescript
// AI might generate:
app.post('/api/user', (req, res) => {
  const user = req.body;
  db.query(`INSERT INTO users VALUES ('${user.name}', '${user.email}')`);
  // SQL injection vulnerability!
});

// Should be:
app.post('/api/user', (req, res) => {
  const { name, email } = validateUserInput(req.body);
  db.query('INSERT INTO users VALUES (?, ?)', [name, email]);
});
```

**Detection**:

- Security scanning tools (Semgrep, Snyk)
- Manual security review
- Penetration testing

**Prevention**:

- Explicitly request security considerations
- Provide secure examples
- Use security-focused prompts

### Validation Checklists by Task Type

#### Feature Implementation Validation

```markdown
## Feature Implementation Checklist

### Requirements
- [ ] Implements all acceptance criteria
- [ ] Handles specified edge cases
- [ ] Includes error scenarios

### Code Quality
- [ ] Passes linting
- [ ] Passes type checking
- [ ] Follows style guide
- [ ] No code smells

### Testing
- [ ] Unit tests present
- [ ] Integration tests present (if needed)
- [ ] All tests pass
- [ ] Coverage >80% of new code

### Security
- [ ] Input validation
- [ ] Output encoding
- [ ] Auth/authz checks
- [ ] No secrets in code

### Performance
- [ ] No N+1 queries
- [ ] Appropriate complexity
- [ ] Efficient data structures
- [ ] Resources cleaned up

### Documentation
- [ ] Code comments for complex logic
- [ ] API docs updated
- [ ] README updated (if needed)
- [ ] CHANGELOG updated
```

#### Refactoring Validation

```markdown
## Refactoring Checklist

### Behavior Preservation
- [ ] All existing tests still pass
- [ ] No new test failures
- [ ] Manual testing confirms same behavior
- [ ] No breaking changes (or documented)

### Improvement Verification
- [ ] Complexity reduced (measurable)
- [ ] Duplication removed
- [ ] Performance maintained or improved
- [ ] Readability improved

### Safety
- [ ] No subtle behavior changes
- [ ] Error handling preserved
- [ ] Edge cases still handled
- [ ] Logging maintained
```

#### Bug Fix Validation

```markdown
## Bug Fix Checklist

### Fix Verification
- [ ] Bug no longer reproduces
- [ ] Root cause addressed (not symptom)
- [ ] Regression test added
- [ ] Related issues checked

### Safety
- [ ] Doesn't introduce new bugs
- [ ] Doesn't break other functionality
- [ ] All tests pass
- [ ] Code review approved

### Documentation
- [ ] Bug report updated
- [ ] CHANGELOG entry added
- [ ] Code comments explain fix (if not obvious)
```

## Team Adoption Strategies

Successful AI adoption requires careful planning and change management.

### Adoption Phases

#### Phase 1: Pilot (Weeks 1-4)

**Objectives**:

- Validate value with small group
- Identify workflows and best practices
- Build internal expertise
- Establish baselines

**Approach**:

```text
Week 1-2: Setup and Training
- Select 2-3 enthusiastic early adopters
- Provide AI tool access
- Conduct training session
- Share this guide

Week 3-4: Guided Usage
- Early adopters use AI for real work
- Daily standup: share experiences
- Document successes and challenges
- Collect metrics (time saved, cost, quality)

Deliverables:
- Usage metrics
- Best practices document
- ROI analysis
- Recommendation for broader rollout
```

**Success Criteria**:

- 20%+ time savings on AI-suitable tasks
- No reduction in code quality
- Positive feedback from pilot users
- Clear ROI (>5:1)

#### Phase 2: Team Rollout (Weeks 5-12)

**Objectives**:

- Expand to full team
- Establish standards and guidelines
- Build team capability
- Monitor and optimize

**Approach**:

```text
Week 5-6: Preparation
- Create team guidelines
- Setup cost monitoring
- Prepare training materials
- Establish support channel

Week 7-8: Training and Onboarding
- Team training session (2 hours)
- Hands-on workshop (2 hours)
- Assign mentors (early adopters)
- Provide quick reference guide

Week 9-12: Active Usage
- Daily AI standups (first 2 weeks)
- Weekly metrics review
- Bi-weekly retrospective
- Continuous refinement of practices

Deliverables:
- Team-wide adoption (>80%)
- Documented patterns and anti-patterns
- Cost and productivity metrics
- Refined guidelines
```

**Success Criteria**:
>
- >80% of team actively using AI
- Consistent quality maintained
- Positive team sentiment
- Measurable productivity gains

#### Phase 3: Optimization (Week 13+)

**Objectives**:

- Optimize costs and workflows
- Advanced technique adoption
- Share learnings across organization
- Continuous improvement

**Approach**:

```text
Ongoing Activities:
- Monthly metrics review
- Quarterly workflow optimization
- Share success stories
- Update guidelines based on learnings
- Advanced training sessions

Advanced Techniques:
- Custom prompt libraries
- Automated context assembly
- Integration with dev tools
- Team-specific optimizations
```

### Training Program

#### Initial Training (2 hours)

**Module 1: Introduction (30 min)**

- Why AI for development
- Overview of capabilities
- When to use (and not use) AI
- Cost structure and budgets

**Module 2: Hands-On Basics (45 min)**

- Tool setup and access
- First AI-assisted task
- Code generation exercise
- Code review exercise
- Q&A

**Module 3: Workflows and Best Practices (30 min)**

- Common workflows
- Context management
- Quality assurance
- Cost optimization
- Team standards

**Module 4: Practice Session (15 min)**

- Real task from backlog
- Guided AI assistance
- Review and discuss

#### Ongoing Learning

**Weekly Tips** (Slack/Email):

```text
Week 1: Use batching for documentation tasks
Week 2: Try the explore-plan-code workflow
Week 3: Use cheaper models for simple tasks
Week 4: Cache responses for repeated tasks
```

**Monthly Workshops** (1 hour):

```text
Month 1: Advanced prompting techniques
Month 2: Complex refactoring with AI
Month 3: Security review patterns
Month 4: Architecture and design with AI
```

**Quarterly Reviews**:

- Share metrics and ROI
- Showcase best examples
- Update guidelines
- Plan improvements

### Standards and Guidelines

Teams MUST establish clear standards:

#### When AI Use is Required

AI assistance SHOULD be used for:

- All documentation generation
- Initial code review (before human)
- Test case generation
- Boilerplate code

#### When AI Use is Prohibited

AI assistance MUST NOT be used for:

- Direct production deployment (without review)
- Security-sensitive logic (without expert review)
- Regulatory/compliance code (without legal review)
- Customer data processing (without privacy review)

#### Quality Standards

All AI-generated code MUST:

- Pass automated checks (lint, test, security)
- Undergo human code review
- Include tests
- Meet team coding standards

AI-generated code SHOULD:

- Be reviewed by senior developer (for complex tasks)
- Include performance testing (for critical paths)
- Be documented with comments explaining complex logic

### Measuring Success

#### Quantitative Metrics

Teams SHOULD track:

**Productivity Metrics**:

- Time saved per task type
- Story points per sprint (before/after)
- Features delivered per quarter
- Time to production (design to deploy)

**Quality Metrics**:

- Bug rate (AI-generated vs manual)
- Test coverage
- Code review feedback volume
- Production incidents

**Cost Metrics**:

- AI cost per developer per month
- AI cost per feature delivered
- ROI (time saved × developer cost / AI cost)
- Cost trend over time

**Adoption Metrics**:

- % developers actively using AI
- Requests per developer per week
- Variety of use cases
- Power user vs casual user ratio

#### Qualitative Metrics

Teams SHOULD collect:

**Developer Satisfaction**:

```text
Monthly Survey (1-5 scale):
1. AI tools improve my productivity
2. AI-generated code quality is acceptable
3. I feel confident reviewing AI code
4. Cost/benefit ratio is positive
5. I would recommend AI tools to others

Open questions:
- Best AI experience this month?
- Biggest challenge with AI?
- Feature request or improvement idea?
```

**Code Review Feedback**:

- Track comments on AI-generated code
- Compare to manually written code
- Identify common issues
- Adjust training and guidelines

### Change Management

#### Addressing Resistance

**Common concerns and responses**:

**"AI will replace developers"**
Response: AI is a tool that augments, not replaces. It handles repetitive tasks,
freeing developers for creative problem-solving, architecture, and complex
challenges.

**"AI-generated code is low quality"**
Response: With proper use and review, AI code quality is high. We maintain same
standards for all code. Pilot showed equivalent or better quality.

**"It's too expensive"**
Response: ROI analysis shows 10-50:1 return. A $100/month AI cost saves 10-20
hours of developer time worth $1500-3000.

**"I don't trust AI"**
Response: Trust through verification. All AI code goes through same review
process. You're the expert ensuring correctness.

**"It's faster to code myself"**
Response: For some tasks, yes. Use AI where it shines (boilerplate, docs,
exploration) and skip it where you're faster.

#### Building Champions

**Identify and empower champions**:

- Early adopters from pilot
- Respected team members
- Different seniority levels
- Different specializations

**Champion responsibilities**:

- Mentor others
- Share successes
- Solve problems
- Provide feedback
- Represent team in AI discussions

**Support champions with**:

- Advanced training
- Direct line to leadership
- Recognition and rewards
- Time allocated for mentoring
- Input on tool selection

### Scaling Across Organization

#### Multi-Team Rollout

**Stagger rollout**:

```text
Month 1-2: Team A (pilot team)
Month 3-4: Team B and C
Month 5-6: Team D, E, F
Month 7+: Remaining teams
```

**Centralize learning**:

- Shared documentation repository
- Cross-team workshops
- Community of practice
- Shared metrics dashboard

**Customize by team**:

- Team-specific guidelines
- Different tool selections (if needed)
- Team-specific prompt libraries
- Adapted workflows

#### Governance

**Establish governance structure**:

**AI Working Group**:

- Representatives from each team
- Meets monthly
- Shares learnings
- Proposes standards
- Evaluates tools

**Responsibilities**:

- Maintain AI usage guidelines
- Manage tool licenses and costs
- Evaluate new AI capabilities
- Ensure security and compliance
- Track organization-wide metrics

**Decision-making**:

- Tool selection
- Budget allocation
- Standard updates
- Training requirements
- Compliance policies

### Long-Term Success Factors

#### Continuous Improvement

Teams MUST:

- Review metrics monthly
- Update guidelines quarterly
- Retrain on new capabilities
- Optimize workflows continuously
- Share learnings widely

#### Staying Current

AI landscape evolves rapidly. Teams SHOULD:

- Monitor new model releases
- Evaluate new capabilities quarterly
- Test new tools in pilot
- Update training materials
- Adjust cost models

#### Knowledge Sharing

Organizations SHOULD establish:

- Internal wiki with AI patterns
- Success story repository
- Prompt library (team-specific)
- Regular knowledge sharing sessions
- External community participation

---

## Conclusion

AI-assisted development is a powerful multiplier when used appropriately. Success requires:

1. **Strategic model selection** based on task characteristics and cost
2. **Structured workflows** that leverage AI strengths
3. **Rigorous quality assurance** to maintain code standards
4. **Cost optimization** to ensure sustainable adoption
5. **Thoughtful team adoption** with proper training and support

Teams that follow these guidelines can expect:

- 20-40% productivity improvement on suitable tasks
- Maintained or improved code quality
- Positive ROI (typically 10-50:1)
- High developer satisfaction
- Competitive advantage in delivery speed

**Remember**: AI is a tool that augments human intelligence, not a replacement.
The developer remains responsible for all code, whether AI-assisted or not.

## Appendix: Quick Reference

### Model Selection Cheat Sheet

```text
Simple, non-critical → Haiku/GPT-4o mini
Standard development → Sonnet/GPT-4o
Complex reasoning → Opus/GPT-4
High volume, privacy → Self-hosted
```

### Cost Cheat Sheet

```text
Haiku: ~$0.001 per request
Sonnet: ~$0.01 per request
Opus: ~$0.05 per request
(Based on average 5K token request)
```

### Prompt Templates

**Code Generation**:

```text
Generate [language] code for [task].

Requirements:
- [requirement 1]
- [requirement 2]

Context:
[relevant code or architecture]

Please include:
- Implementation
- Error handling
- Tests
- Documentation
```

**Code Review**:

```text
Review this code:

[code]

Check for:
- Bugs
- Security issues
- Performance problems
- Style violations
- Edge cases

Provide specific feedback with line numbers.
```

**Bug Fix**:

```text
Fix this bug:

Error: [error message]
Stack: [stack trace]
Code: [relevant code]

Please:
1. Explain root cause
2. Suggest fix
3. Provide regression test
```

---

## Documentation Agent Suite

Doctrine includes a comprehensive multi-agent documentation system - the most
advanced open-source AI documentation suite available.

### Agent Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                   Documentation Agent Suite                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ doc-architect│ →  │  doc-writer  │ →  │ doc-reviewer │      │
│  │  (planning)  │    │ (generation) │    │ (validation) │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                   │               │
│         ▼                   ▼                   ▼               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   doc-sync   │ ←  │doc-publisher │ ←  │  Feedback    │      │
│  │  (freshness) │    │  (formats)   │    │    Loop      │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Agents

| Agent | Purpose | Invocation |
|-------|---------|------------|
| **doc-architect** | Analyze codebase, create documentation plan | `/doc-plan` |
| **doc-writer** | Generate documentation with diagrams | `/doc` |
| **doc-reviewer** | Review docs for accuracy and completeness | `/doc-review` |
| **doc-sync** | Detect stale documentation | `/doc-sync` |
| **doc-publisher** | Transform to llms.txt, MCP, Mermaid | `/doc-publish` |

### Commands

| Command | Description |
|---------|-------------|
| `/doc [target]` | Generate documentation for file, function, or class |
| `/doc-plan [dir]` | Create prioritized documentation plan |
| `/doc-review [file]` | Review documentation for accuracy |
| `/doc-sync` | Check if docs are synchronized with code |
| `/doc-sync --pr` | Check docs for files in current PR |
| `/doc-publish --all` | Generate llms.txt, MCP, and diagrams |
| `/doc-status` | Show documentation coverage metrics |

### Output Formats

The doc-publisher agent generates documentation in multiple formats:

- **Markdown** - Standard GitHub-flavored for human developers
- **llms.txt** - Token-efficient format for AI assistants
- **MCP** - Model Context Protocol for AI tool integration
- **Mermaid** - Architecture, sequence, state, and ER diagrams

### CI Integration

Documentation workflows integrate with GitHub Actions:

```yaml
# .github/workflows/doc-sync.yml
# Automatically checks documentation freshness on every PR
```

### Configuration

Agents are configured in `configs/claude/agents/`:

```text
configs/claude/
├── agents/
│   ├── doc-architect.md   # Documentation planning
│   ├── doc-writer.md      # Documentation generation
│   ├── doc-reviewer.md    # Documentation review
│   ├── doc-sync.md        # Staleness detection
│   └── doc-publisher.md   # Multi-format output
├── commands/
│   ├── doc.md             # /doc command
│   ├── doc-plan.md        # /doc-plan command
│   ├── doc-review.md      # /doc-review command
│   ├── doc-sync.md        # /doc-sync command
│   ├── doc-publish.md     # /doc-publish command
│   └── doc-status.md      # /doc-status command
└── settings.json          # Claude Code configuration
```

## See Also

- **[AI Workflows](./ai-workflows.md)** - Hero Flow, TDD/3-Way Compare, Visual
  Iteration, Long-Running Tasks
- **[Claude Code Configuration](./claude-code.md)** - Hooks, Permissions,
  Subagents, Commands, MCP
- **[AGENTS.md Guide](./agents-md.md)** - Project instruction files for AI
  assistants
- **[Release Manager Agent](./release-manager-agent.md)** - AI-powered release
  management, quality gates, changelog generation

## References

[^1]: [Claude/Anthropic Best Practices Guide](./claude.md)
[^2]: [Anthropic Claude Models Documentation](https://docs.anthropic.com/claude/docs/models-overview)
[^3]: [OpenAI GPT Models Documentation](https://platform.openai.com/docs/models)
[^4]: [Google Gemini Models Documentation](https://ai.google.dev/gemini-api/docs/models/gemini)
[^5]: [Meta Llama Models](https://www.llama.com/)
[^6]: [StarCoder Models - Hugging Face](https://huggingface.co/bigcode/starcoder2-15b)
[^7]: [Anthropic Pricing](https://www.anthropic.com/pricing)
[^8]: [Anthropic Rate Limits](https://docs.anthropic.com/claude/reference/rate-limits)
[^9]: [OpenAI Pricing](https://openai.com/pricing)
[^10]: [OpenAI Rate Limits](https://platform.openai.com/docs/guides/rate-limits)
[^11]: [Google AI Pricing and Quotas](https://ai.google.dev/pricing)
[^12]: [DeepSeek Coder](https://github.com/deepseek-ai/DeepSeek-Coder)

---

*Last Updated: 2025-12-07*
*Version: 1.0.0*
*Maintainer: Engineering Team*
