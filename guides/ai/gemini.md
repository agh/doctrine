# Google Gemini Best Practices Guide

> [Doctrine](../../README.md) > [Guides](../README.md) > [AI](./README.md) > Gemini

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

## Table of Contents

- [Introduction](#introduction)
- [Model Selection](#model-selection)
  - [Gemini 2.0 Flash](#gemini-20-flash)
  - [Gemini 1.5 Pro](#gemini-15-pro)
  - [Gemini 1.5 Flash](#gemini-15-flash)
  - [Model Comparison Matrix](#model-comparison-matrix)
  - [Pricing Structure](#pricing-structure)
  - [Selection Guidelines](#selection-guidelines)
- [API Access Patterns](#api-access-patterns)
  - [Google AI Studio](#google-ai-studio)
  - [Vertex AI](#vertex-ai)
  - [Platform Comparison](#platform-comparison)
  - [Authentication and Setup](#authentication-and-setup)
- [System Instructions for Coding](#system-instructions-for-coding)
  - [Effective System Instructions](#effective-system-instructions)
  - [Code Review Instructions](#code-review-instructions)
  - [Documentation Generation](#documentation-generation)
  - [Testing and Quality Assurance](#testing-and-quality-assurance)
  - [System Instruction Best Practices](#system-instruction-best-practices)
- [Function Calling](#function-calling)
  - [Function Declaration](#function-declaration)
  - [Function Call Flow](#function-call-flow)
  - [Parallel Function Calling](#parallel-function-calling)
  - [Error Handling](#error-handling)
  - [Function Calling Best Practices](#function-calling-best-practices)
- [Grounding with Google Search](#grounding-with-google-search)
  - [Search Grounding Configuration](#search-grounding-configuration)
  - [Dynamic Retrieval](#dynamic-retrieval)
  - [Grounding Metadata](#grounding-metadata)
  - [Use Cases for Grounding](#use-cases-for-grounding)
- [Large Context Window Usage](#large-context-window-usage)
  - [Context Window Capabilities](#context-window-capabilities)
  - [Effective Context Loading](#effective-context-loading)
  - [Context Caching](#context-caching)
  - [Long Context Strategies](#long-context-strategies)
  - [Context Window Limitations](#context-window-limitations)
- [Cost Optimization](#cost-optimization)
  - [Model Selection for Cost](#model-selection-for-cost)
  - [Context Caching for Savings](#context-caching-for-savings)
  - [Prompt Engineering for Efficiency](#prompt-engineering-for-efficiency)
  - [Batch Processing](#batch-processing)
  - [Rate Limiting and Quotas](#rate-limiting-and-quotas)
- [Common Pitfalls](#common-pitfalls)
  - [Safety Settings Issues](#safety-settings-issues)
  - [Context Window Misuse](#context-window-misuse)
  - [Function Calling Errors](#function-calling-errors)
  - [JSON Mode Mistakes](#json-mode-mistakes)
  - [Streaming Complications](#streaming-complications)
- [Do and Don't Examples](#do-and-dont-examples)
  - [Prompt Engineering](#prompt-engineering)
  - [API Usage](#api-usage)
  - [Function Calling](#function-calling-1)
  - [Context Management](#context-management)
  - [Error Handling](#error-handling-1)
- [Advanced Techniques](#advanced-techniques)
  - [Multi-Turn Conversations](#multi-turn-conversations)
  - [Code Execution](#code-execution)
  - [Multimodal Capabilities](#multimodal-capabilities)
  - [Controlled Generation](#controlled-generation)
- [Security and Privacy](#security-and-privacy)
  - [Data Handling](#data-handling)
  - [API Key Management](#api-key-management)
  - [Content Filtering](#content-filtering)
  - [Compliance Considerations](#compliance-considerations)
- [Monitoring and Debugging](#monitoring-and-debugging)
  - [Response Quality Metrics](#response-quality-metrics)
  - [Performance Monitoring](#performance-monitoring)
  - [Debugging Techniques](#debugging-techniques)
- [References](#references)

---

## Introduction

Google Gemini[^1] is a family of large language models designed for multimodal
understanding and generation. This guide establishes best practices for
integrating Gemini models into development workflows, with a focus on coding
assistance, function calling, and leveraging Gemini's unique capabilities like
massive context windows and grounding with Google Search.

Gemini models are available through two primary platforms:

1. **Google AI Studio[^2]** - Simplified API access for prototyping and small-scale applications
2. **Vertex AI[^3]** - Enterprise-grade deployment with advanced features and SLA guarantees

This guide covers both platforms and provides prescriptive guidance on model
selection, API patterns, cost optimization, and common pitfalls.

### Who Should Use This Guide

This guide is REQUIRED reading for:

- Developers integrating Gemini into applications
- Teams building AI-powered coding tools
- Engineers optimizing LLM costs
- Architects designing AI-assisted workflows

### Prerequisites

Readers SHOULD have:

- Basic understanding of REST APIs or gRPC
- Familiarity with JSON data structures
- Experience with API authentication mechanisms
- Knowledge of Python or Node.js (for code examples)

---

## Model Selection

### Gemini 2.0 Flash[^4]

**Release**: December 2024[^4]

**Context Window**: 1,048,576 tokens (1M input), 8,192 tokens (output)[^4]

**Key Features**[^4]:

- Multimodal live API support (audio and video streaming)
- Native image generation
- Native tool use and function calling
- Multilingual text-to-speech
- Fastest inference in the Gemini family
- Best price-to-performance ratio

**Use Cases**:

- Real-time coding assistance
- Interactive development environments
- Chat applications requiring low latency
- High-volume API calls with cost constraints
- Multimodal applications (code + diagrams)

**Limitations**:

- Smaller maximum output tokens compared to Pro models
- May require more careful prompt engineering for complex tasks

You SHOULD use Gemini 2.0 Flash when:

- Response time is critical (< 1 second)
- Processing millions of requests per day
- Budget constraints are primary concern
- Tasks are well-defined and structured

You SHOULD NOT use Gemini 2.0 Flash when:

- Generating very long-form content (> 4K tokens)
- Requiring highest possible reasoning quality
- Complex multi-step planning is needed

### Gemini 1.5 Pro[^5]

**Current Version**: 1.5 Pro (002)[^5]

**Context Window**: 2,097,152 tokens (2M input), 8,192 tokens (output)[^5]

**Key Features**[^5]:

- Largest context window available (2M tokens)
- Superior reasoning on complex tasks
- Better code understanding and generation
- Enhanced multilingual capabilities
- Audio understanding (speech, music, ambient sounds)
- Video understanding

**Use Cases**:

- Analyzing entire codebases (up to ~1M lines)
- Complex refactoring tasks
- Architectural decision support
- Long-form documentation generation
- Multi-file code reviews
- Processing large log files or data dumps

**Limitations**:

- Higher latency than Flash models
- Significantly higher cost per token
- Slower experimental releases for new features

You MUST use Gemini 1.5 Pro when:

- Analyzing codebases exceeding 500K tokens
- Maximum reasoning quality is required
- Complex multi-step tasks with dependencies
- Processing extensive documentation sets

You SHOULD use Gemini 1.5 Pro when:

- Code generation requires deep contextual understanding
- Performing complex refactoring operations
- Generating comprehensive test suites
- Quality is more important than cost

### Gemini 1.5 Flash[^6]

**Current Version**: 1.5 Flash (002)[^6]

**Context Window**: 1,048,576 tokens (1M input), 8,192 tokens (output)[^6]

**Key Features**[^6]:

- Balanced performance and cost
- Fast inference speeds
- Multimodal capabilities
- Good code understanding
- Reliable function calling

**Use Cases**:

- General-purpose coding assistance
- Moderate-complexity tasks
- API integrations with balanced requirements
- Development tools with moderate context needs

**Status**: Being superseded by Gemini 2.0 Flash

You **SHOULD** consider Gemini 2.0 Flash instead of 1.5 Flash for new projects
due to improved capabilities and similar pricing.

### Model Comparison Matrix

| Feature                 | Gemini 2.0 Flash | Gemini 1.5 Pro | Gemini 1.5 Flash |
| ----------------------- | ---------------- | -------------- | ---------------- |
| **Input Context**       | 1M tokens        | 2M tokens      | 1M tokens        |
| **Output Tokens**       | 8,192            | 8,192          | 8,192            |
| **Latency**             | Fastest          | Moderate       | Fast             |
| **Reasoning Quality**   | Good             | Excellent      | Good             |
| **Code Generation**     | Good             | Excellent      | Good             |
| **Cost (per 1M input)** | $0.15            | $1.25          | $0.15            |
| **Cost (per 1M output)**| $0.60            | $5.00          | $0.60            |
| **Multimodal**          | Yes (advanced)   | Yes            | Yes              |
| **Function Calling**    | Yes (native)     | Yes            | Yes              |
| **Grounding**           | Yes              | Yes            | Yes              |
| **Audio I/O**           | Yes              | Yes (input)    | Yes (input)      |
| **Video Understanding** | Yes              | Yes            | Yes              |
| **Image Generation**    | Yes              | No             | No               |

### Pricing Structure

**As of December 2024**[^7] (Google AI Studio / Vertex AI pricing):

#### Gemini 2.0 Flash

- Input tokens (≤128K): $0.00 / 1M tokens (free tier)
- Input tokens (>128K): $0.15 / 1M tokens
- Output tokens: $0.60 / 1M tokens
- Cached tokens: $0.0375 / 1M tokens (75% discount)
- Audio input: $0.15 / 1M tokens
- Video input: $0.15 / 1M tokens

#### Gemini 1.5 Pro

- Input tokens (≤128K): $1.25 / 1M tokens
- Input tokens (>128K): $2.50 / 1M tokens
- Output tokens: $5.00 / 1M tokens
- Cached tokens: $0.3125 / 1M tokens (75% discount)
- Audio input: $2.50 / 1M tokens
- Video input: $2.50 / 1M tokens

#### Gemini 1.5 Flash

- Input tokens (≤128K): $0.075 / 1M tokens
- Input tokens (>128K): $0.15 / 1M tokens
- Output tokens: $0.30 / 1M tokens
- Cached tokens: $0.01875 / 1M tokens (75% discount)
- Audio input: $0.15 / 1M tokens
- Video input: $0.15 / 1M tokens

**Note**: Pricing **MAY** vary between Google AI Studio and Vertex AI. Always
verify current pricing in the official documentation.

### Selection Guidelines

#### Decision Tree

```text
START
├─ Need 2M+ token context?
│  └─ YES → Gemini 1.5 Pro
│  └─ NO → Continue
│
├─ Processing > 10M requests/month?
│  └─ YES → Gemini 2.0 Flash
│  └─ NO → Continue
│
├─ Complex reasoning required?
│  └─ YES → Gemini 1.5 Pro
│  └─ NO → Gemini 2.0 Flash
│
├─ Need < 500ms response time?
│  └─ YES → Gemini 2.0 Flash
│  └─ NO → Continue
│
├─ Budget < $100/month?
│  └─ YES → Gemini 2.0 Flash
│  └─ NO → Gemini 1.5 Pro
│
└─ Default → Gemini 2.0 Flash
```

#### Cost-Performance Trade-offs

**Example Scenario**: Code review service processing 1,000 pull requests/day

Each PR analysis requires:

- Average input: 50,000 tokens
- Average output: 2,000 tokens

**Monthly Costs**:

Gemini 2.0 Flash:

- Input: 30 days × 1,000 PRs × 50K tokens × $0.15/1M = $22.50
- Output: 30 days × 1,000 PRs × 2K tokens × $0.60/1M = $36.00
- **Total: $58.50/month**

Gemini 1.5 Pro:

- Input: 30 days × 1,000 PRs × 50K tokens × $1.25/1M = $187.50
- Output: 30 days × 1,000 PRs × 2K tokens × $5.00/1M = $300.00
- **Total: $487.50/month**

**Cost Difference**: 8.3x more expensive for Pro

**When Pro is Worth It**:

- Critical path reviews (security, compliance)
- Complex architectural changes
- Cross-repository refactoring
- Quality > cost in business requirements

---

## API Access Patterns

### Google AI Studio

**Overview**: Google AI Studio[^2] provides a simplified REST API for accessing
Gemini models with minimal setup.

**Best For**:

- Rapid prototyping
- Individual developers
- Small applications (< 100K requests/month)
- Educational projects
- Quick experiments

**Limitations**:

- No SLA guarantees
- Limited enterprise features
- Fewer regional deployment options
- No VPC integration
- Basic quota management

#### Authentication

You MUST use API keys for authentication:

```bash
export GOOGLE_API_KEY="your-api-key-here"
```

You SHOULD NOT:

- Commit API keys to version control
- Share API keys across teams
- Use the same key for dev and production

You MUST:

- Store keys in environment variables or secret managers
- Rotate keys regularly (every 90 days recommended)
- Use separate keys per environment

#### Basic REST API Example

```python
import os
import google.generativeai as genai

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

model = genai.GenerativeModel("gemini-2.0-flash")

response = model.generate_content(
    "Write a Python function to calculate factorial recursively"
)

print(response.text)
```

#### Endpoint Structure

```text
POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent[^15]
```

You **MUST** include:

- API key as query parameter: `?key=YOUR_API_KEY`
- Content-Type header: `application/json`

### Vertex AI

**Overview**: Vertex AI[^3] provides enterprise-grade access to Gemini with
advanced features, SLAs, and integration with Google Cloud services.

**Best For**:

- Production applications
- Enterprise deployments
- High-volume processing
- Compliance requirements (HIPAA, SOC 2)
- Multi-region deployment
- Integration with GCP ecosystem

**Advantages**:

- 99.9% SLA availability
- VPC Service Controls
- CMEK (Customer-Managed Encryption Keys)
- Cloud Logging and Monitoring integration
- IAM-based access control
- Private endpoints
- Batch prediction support

#### Authentication

You MUST use Google Cloud authentication:

```python
from google.cloud import aiplatform
from vertexai.preview.generative_models import GenerativeModel

# Initialize Vertex AI
aiplatform.init(
    project="your-project-id",
    location="us-central1"
)

model = GenerativeModel("gemini-2.0-flash")

response = model.generate_content(
    "Write a Python function to calculate factorial recursively"
)

print(response.text)
```

#### Service Account Setup

You MUST:

1. Create a service account with appropriate permissions
2. Grant `Vertex AI User` role minimum
3. Download and secure the JSON key file
4. Set GOOGLE_APPLICATION_CREDENTIALS environment variable

```bash
# Create service account
gcloud iam service-accounts create gemini-service \
    --display-name="Gemini API Service Account"

# Grant permissions
gcloud projects add-iam-policy-binding your-project-id \
    --member="serviceAccount:gemini-service@your-project-id.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

# Create key
gcloud iam service-accounts keys create key.json \
    --iam-account=gemini-service@your-project-id.iam.gserviceaccount.com

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
```

#### Regional Endpoints

Vertex AI supports multiple regions. You SHOULD choose regions based on:

1. **Latency requirements** - Select region closest to users
2. **Data residency** - Comply with local regulations
3. **Availability** - Some models may not be available in all regions

Available regions (as of December 2024)[^3]:

- `us-central1` (Iowa)
- `us-east4` (Virginia)
- `us-west1` (Oregon)
- `europe-west1` (Belgium)
- `europe-west4` (Netherlands)
- `asia-northeast1` (Tokyo)
- `asia-southeast1` (Singapore)

```python
aiplatform.init(
    project="your-project-id",
    location="europe-west1"  # Choose appropriate region
)
```

### Platform Comparison

| Feature                 | Google AI Studio         | Vertex AI               |
| ----------------------- | ------------------------ | ----------------------- |
| **Authentication**      | API Key                  | Service Account / OAuth |
| **SLA**                 | None                     | 99.9%                   |
| **Pricing**             | Same as Vertex           | Same as AI Studio       |
| **Setup Complexity**    | Low                      | Moderate                |
| **Enterprise Features** | Limited                  | Full                    |
| **VPC Integration**     | No                       | Yes                     |
| **Logging**             | Basic                    | Cloud Logging           |
| **Monitoring**          | Basic                    | Cloud Monitoring        |
| **Batch Predictions**   | No                       | Yes                     |
| **Model Garden**        | Limited                  | Full Access             |
| **Custom Models**       | No                       | Yes                     |
| **Data Residency**      | Limited                  | Full Control            |

### Authentication and Setup

#### Google AI Studio Setup

1. Visit [Google AI Studio](https://aistudio.google.com/)[^2]
2. Sign in with Google account
3. Create API key[^2]
4. Set environment variable

```bash
export GOOGLE_API_KEY="AIza..."
```

#### Vertex AI Setup

1. Create or select GCP project
2. Enable Vertex AI API[^3]

```bash
gcloud services enable aiplatform.googleapis.com[^3]
```

1. Set up authentication (see Service Account Setup above)
2. Install SDK[^12]

```bash
pip install google-cloud-aiplatform[^12]
```

#### SDK Installation

**Python**:

```bash
# For Google AI Studio
pip install google-generativeai  # [^11]

# For Vertex AI
pip install google-cloud-aiplatform  # [^12]
```

**Node.js**:

```bash
# For Google AI Studio
npm install @google/generative-ai  # [^13]

# For Vertex AI
npm install @google-cloud/vertexai  # [^14]
```

---

## System Instructions for Coding

System instructions provide persistent context that applies to all messages in
a conversation. They are **CRITICAL** for consistent coding assistance.

### Effective System Instructions

System instructions SHOULD:

- Define the assistant's role and expertise
- Specify output format and structure
- Establish code style preferences
- Set constraints and boundaries
- Include examples of desired behavior

System instructions MUST:

- Be clear and unambiguous
- Avoid contradictions
- Stay under 10,000 tokens for performance
- Be tested thoroughly before deployment

#### Basic Coding Assistant

```python
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    system_instruction="""You are an expert software engineer specializing in Python, JavaScript, and Go.

Your responses MUST:
- Provide working, tested code
- Include inline comments for complex logic
- Follow language-specific style guides (PEP 8 for Python, Airbnb for JavaScript)
- Include error handling
- Consider edge cases

Your responses MUST NOT:
- Include placeholder code or TODOs
- Assume undefined variables or functions
- Ignore security considerations
- Skip input validation

When suggesting refactoring:
1. Explain the problem with current code
2. Show the refactored version
3. Explain why the refactoring improves the code
4. Note any trade-offs or considerations
"""
)
```

#### Production-Grade System Instructions

```python
system_instruction = """You are a senior software engineer conducting code reviews for a production system.

# Role and Expertise
- 10+ years experience in distributed systems
- Expert in Python, TypeScript, and cloud architecture
- Familiar with microservices, Docker, Kubernetes

# Code Review Standards
Your reviews MUST check for:

1. **Correctness**
   - Logic errors and edge cases
   - Type safety
   - Null/undefined handling
   - Off-by-one errors

2. **Security**
   - SQL injection vulnerabilities
   - XSS vulnerabilities
   - Authentication/authorization issues
   - Secrets in code
   - Input validation

3. **Performance**
   - O(n²) or worse algorithms
   - N+1 query problems
   - Memory leaks
   - Unnecessary allocations

4. **Maintainability**
   - Code complexity (cyclomatic complexity < 10)
   - Function length (< 50 lines)
   - Single Responsibility Principle
   - Clear naming conventions

5. **Testing**
   - Test coverage > 80%
   - Edge cases covered
   - Integration tests for critical paths
   - Mocking external dependencies

# Output Format
For each issue found:

**Severity**: [CRITICAL|HIGH|MEDIUM|LOW]
**Category**: [Correctness|Security|Performance|Maintainability|Testing]
**Location**: File:Line
**Issue**: Clear description of the problem
**Recommendation**: Specific fix with code example
**Rationale**: Why this matters

# Constraints
- Focus on substantive issues, not style nitpicks
- Provide actionable feedback with code examples
- Consider the broader system context
- Balance idealism with pragmatism
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    system_instruction=system_instruction
)
```

### Code Review Instructions

```python
code_review_instruction = """You are an automated code review assistant for a team using:
- Language: Python 3.11+
- Framework: FastAPI
- Database: PostgreSQL with SQLAlchemy
- Testing: pytest
- Style: Black formatter, flake8 linter, mypy type checker

# Review Checklist

## FastAPI Specific
- [ ] Proper dependency injection usage
- [ ] Response model validation
- [ ] HTTP status codes match REST conventions
- [ ] Async/await used correctly
- [ ] Background tasks for long operations

## Database
- [ ] No raw SQL (use SQLAlchemy ORM)
- [ ] Proper transaction handling
- [ ] Connection pooling configured
- [ ] Migrations included for schema changes
- [ ] Indexes on foreign keys and frequently queried columns

## Testing
- [ ] Unit tests for business logic
- [ ] Integration tests for endpoints
- [ ] Test database fixtures used
- [ ] Mocking external API calls
- [ ] Edge cases covered (empty lists, None values, etc.)

## Security
- [ ] Input validation with Pydantic
- [ ] SQL injection prevention (ORM usage)
- [ ] Authentication on protected endpoints
- [ ] Rate limiting on public endpoints
- [ ] Secrets in environment variables, not code

# Output Format
Provide a structured review with:
1. Summary (2-3 sentences)
2. Critical Issues (blocking PR merge)
3. Important Issues (should fix before merge)
4. Suggestions (nice to have improvements)
5. Positive Feedback (what was done well)

Keep feedback specific, actionable, and constructive.
"""
```

### Documentation Generation

````python
docs_instruction = """You are a technical documentation specialist.

# Documentation Standards

## Function Documentation
Use Google-style docstrings:

```python
def example_function(param1: str, param2: int) -> bool:
    \"\"\"Brief one-line summary.

    Detailed description of what the function does, including any
    important implementation details or algorithms used.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When and why this is raised
        TypeError: When and why this is raised

    Example:
        >>> example_function("test", 42)
        True
    \"\"\"
```

## Class Documentation

Include:

- Purpose of the class
- Key attributes
- Important methods
- Usage examples
- Thread safety notes (if applicable)

## Module Documentation

At the top of each module:

- Module purpose
- Key classes/functions
- Dependencies
- Usage examples

# Tone and Style

- Use present tense ("Returns" not "Will return")
- Be concise but complete
- Include examples for complex behavior
- Link to related functions/classes
- Note any deprecations or future changes
"""
````

### Testing and Quality Assurance

````python
testing_instruction = """You are a test engineering specialist.

# Testing Philosophy
- Test behavior, not implementation
- Each test should verify one behavior
- Tests should be independent and isolated
- Use descriptive test names: test_<method>_<scenario>_<expected>

# Test Structure (Arrange-Act-Assert)
```python
def test_user_creation_with_valid_data_creates_user():
    # Arrange
    user_data = {"email": "test@example.com", "name": "Test User"}

    # Act
    user = User.create(user_data)

    # Assert
    assert user.email == "test@example.com"
    assert user.name == "Test User"
    assert user.id is not None
```

# Coverage Requirements

- Unit tests: 80%+ coverage
- Integration tests: Critical paths must be covered
- Edge cases: Empty inputs, None, boundary values
- Error cases: Invalid inputs, network failures, etc.

# Mocking Guidelines

- Mock external services (APIs, databases in unit tests)
- Use fixtures for test data
- Reset mocks between tests
- Verify mock calls when behavior matters

# Test Generation

When generating tests:

1. Cover happy path first
2. Add edge cases
3. Add error cases
4. Add integration tests for critical flows
5. Include performance tests for hot paths (> 1000 calls/sec)

# Output Format

Provide complete, runnable test files with:

- Necessary imports
- Fixtures and setup
- Complete test functions
- Teardown if needed
- Comments explaining complex assertions
"""
````

### System Instruction Best Practices

#### DO

1. **Be Specific About Output Format**

```python
system_instruction = """
# Output Format
Your responses MUST be valid JSON with this structure:
{
    "analysis": "Brief description",
    "issues": [
        {
            "severity": "HIGH|MEDIUM|LOW",
            "file": "path/to/file.py",
            "line": 42,
            "description": "Issue description",
            "fix": "Suggested fix"
        }
    ]
}
"""
```

1. **Include Concrete Examples**

````python
system_instruction = """
When suggesting refactoring, use this format:

**Before**:
```python
def bad_example():
    x = get_value()
    if x:
        return x
    else:
        return None
```

**After**:

```python
def good_example():
    return get_value()
```

**Reason**: The else clause is unnecessary; Python functions return None by default.
"""
````

1. **Set Clear Boundaries**

```python
system_instruction = """
You MUST NOT:
- Suggest removing error handling
- Recommend using deprecated APIs
- Propose changes that break backward compatibility
- Suggest optimizations without profiling data

You MUST:
- Preserve existing error handling
- Recommend current stable APIs
- Note when changes are breaking
- Suggest profiling before optimization
"""
```

#### DON'T

1. **Don't Be Vague**

```python
# BAD
system_instruction = "You are a helpful coding assistant."

# GOOD
system_instruction = """You are a Python expert specializing in Django web development.
You provide code that follows Django best practices and the project's coding standards."""
```

1. **Don't Contradict Yourself**

```python
# BAD
system_instruction = """
Always include comprehensive error handling.
Keep functions under 10 lines for readability.
"""
# These may conflict for complex error handling
```

1. **Don't Overload with Information**

```python
# BAD - Too much information
system_instruction = """
[5000 lines of detailed coding standards, architecture docs, and examples]
"""

# GOOD - Reference documentation, provide essentials
system_instruction = """
Follow the Python style guide at: docs/python-style.md

Key requirements:
- Type hints on all functions
- Docstrings on public APIs
- Error handling for external calls
- Unit tests for business logic
"""
```

---

## Function Calling

Function calling[^16] enables Gemini to interact with external systems, APIs,
and tools. This is **ESSENTIAL** for building AI agents and assistants that
take actions.

### Function Declaration

Functions MUST be declared with JSON Schema[^16]:

```python
get_weather_function = {
    "name": "get_weather",
    "description": "Get current weather for a location. Use this when users ask about weather conditions.",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City name or zip code, e.g. 'San Francisco' or '94102'"
            },
            "unit": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"],
                "description": "Temperature unit",
                "default": "fahrenheit"
            }
        },
        "required": ["location"]
    }
}

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    tools=[get_weather_function]
)
```

#### Complete Example with Implementation

```python
import google.generativeai as genai
import json

# Define functions
def get_current_weather(location: str, unit: str = "fahrenheit") -> dict:
    """Actual implementation of weather fetching"""
    # In production, call a real weather API
    return {
        "location": location,
        "temperature": 72,
        "unit": unit,
        "conditions": "sunny"
    }

def get_stock_price(symbol: str) -> dict:
    """Get stock price for a symbol"""
    # In production, call a real stock API
    return {
        "symbol": symbol,
        "price": 150.25,
        "change": 2.5,
        "change_percent": 1.7
    }

# Declare functions for Gemini
tools = [
    {
        "name": "get_current_weather",
        "description": "Get the current weather for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name, e.g. 'San Francisco, CA'"
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "default": "fahrenheit"
                }
            },
            "required": ["location"]
        }
    },
    {
        "name": "get_stock_price",
        "description": "Get current stock price for a ticker symbol",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Stock ticker symbol, e.g. 'GOOGL'"
                }
            },
            "required": ["symbol"]
        }
    }
]

# Create model with tools
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    tools=tools
)

# Function call dispatcher
function_map = {
    "get_current_weather": get_current_weather,
    "get_stock_price": get_stock_price
}

# Start conversation
chat = model.start_chat()

# User message
user_message = "What's the weather in New York and the stock price of GOOGL?"
response = chat.send_message(user_message)

# Check if model wants to call functions
if response.candidates[0].content.parts[0].function_call:
    # Process function calls
    function_calls = []
    for part in response.candidates[0].content.parts:
        if hasattr(part, 'function_call'):
            fc = part.function_call
            function_calls.append(fc)

    # Execute functions
    function_responses = []
    for fc in function_calls:
        function_name = fc.name
        function_args = dict(fc.args)

        # Call the actual function
        result = function_map[function_name](**function_args)

        function_responses.append({
            "name": function_name,
            "response": result
        })

    # Send function results back to model
    response = chat.send_message(
        genai.protos.Content(
            parts=[
                genai.protos.Part(
                    function_response=genai.protos.FunctionResponse(
                        name=fr["name"],
                        response={"result": fr["response"]}
                    )
                )
                for fr in function_responses
            ]
        )
    )

    print(response.text)
else:
    print(response.text)
```

### Function Call Flow

```text
User Message
    ↓
Gemini Processes Input
    ↓
Decision: Need External Data?
    ├─ No → Generate text response
    └─ Yes → Generate function call(s)
         ↓
Client receives function call instructions
    ↓
Client executes actual functions
    ↓
Client sends function results to Gemini
    ↓
Gemini processes results
    ↓
Gemini generates final response
    ↓
User receives answer
```

### Parallel Function Calling

Gemini CAN call multiple functions in parallel:

```python
# User asks: "What's the weather in SF and NYC, and GOOGL stock price?"

# Gemini may return multiple function calls:
# 1. get_current_weather(location="San Francisco")
# 2. get_current_weather(location="New York City")
# 3. get_stock_price(symbol="GOOGL")

# You SHOULD execute these in parallel for performance:
import asyncio

async def execute_function(name: str, args: dict):
    function = function_map[name]
    # Wrap sync functions if needed
    return await asyncio.to_thread(function, **args)

async def execute_all_functions(function_calls):
    tasks = [
        execute_function(fc.name, dict(fc.args))
        for fc in function_calls
    ]
    return await asyncio.gather(*tasks)

# Execute all function calls concurrently
results = asyncio.run(execute_all_functions(function_calls))
```

### Error Handling

Functions SHOULD return error information in the response:

```python
def get_weather(location: str, unit: str = "fahrenheit") -> dict:
    try:
        # Call weather API
        result = call_weather_api(location, unit)
        return {
            "success": True,
            "data": result
        }
    except LocationNotFound as e:
        return {
            "success": False,
            "error": "location_not_found",
            "message": f"Could not find location: {location}"
        }
    except APIError as e:
        return {
            "success": False,
            "error": "api_error",
            "message": "Weather service temporarily unavailable"
        }
```

Gemini will incorporate error information into its response:

```text
User: What's the weather in Atlantis?
Gemini: I couldn't find weather information for Atlantis as it's not a recognized location.
Could you provide a valid city name?
```

### Function Calling Best Practices

#### DO

1. **Provide Detailed Descriptions**

```python
# GOOD
{
    "name": "search_codebase",
    "description": """Search the codebase for matching files or code patterns.

    Use this when users ask to:
    - Find files by name or pattern
    - Locate function or class definitions
    - Search for specific code patterns
    - Find usage examples

    Examples:
    - "Find all Python files in the src directory"
    - "Where is the User class defined?"
    - "Show me examples of database queries"
    """,
    "parameters": {...}
}
```

1. **Use Enums for Constrained Values**

```python
{
    "name": "create_file",
    "parameters": {
        "type": "object",
        "properties": {
            "file_type": {
                "type": "string",
                "enum": ["python", "javascript", "typescript", "markdown"],
                "description": "Type of file to create"
            }
        }
    }
}
```

1. **Validate Function Arguments**

```python
def execute_query(sql: str, database: str) -> dict:
    # Validate before execution
    if not sql.strip().upper().startswith("SELECT"):
        return {
            "success": False,
            "error": "Only SELECT queries are allowed"
        }

    if database not in ALLOWED_DATABASES:
        return {
            "success": False,
            "error": f"Database '{database}' not accessible"
        }

    # Proceed with execution
    ...
```

1. **Return Structured Data**

```python
# GOOD - Structured response
def search_code(pattern: str) -> dict:
    return {
        "total_matches": 5,
        "matches": [
            {
                "file": "src/user.py",
                "line": 42,
                "context": "def authenticate_user(username, password):"
            },
            ...
        ]
    }

# BAD - Unstructured string
def search_code(pattern: str) -> str:
    return "Found 5 matches:\n1. src/user.py line 42\n..."
```

#### DON'T

1. **Don't Use Generic Descriptions**

```python
# BAD
{
    "name": "query",
    "description": "Runs a query",
    ...
}

# GOOD
{
    "name": "execute_database_query",
    "description": "Execute a read-only SQL SELECT query against the analytics database",
    ...
}
```

1. **Don't Allow Dangerous Operations Without Safeguards**

```python
# BAD - No validation
def execute_code(code: str):
    exec(code)  # Dangerous!

# GOOD - Sandboxed execution
def execute_code(code: str, timeout: int = 5):
    # Run in restricted environment
    # Set timeout
    # Validate code before execution
    # Return results safely
    ...
```

1. **Don't Return Raw Exceptions**

```python
# BAD
def get_file_contents(path: str):
    return open(path).read()  # Raises exception on error

# GOOD
def get_file_contents(path: str) -> dict:
    try:
        with open(path) as f:
            return {
                "success": True,
                "content": f.read()
            }
    except FileNotFoundError:
        return {
            "success": False,
            "error": "file_not_found",
            "message": f"File not found: {path}"
        }
```

---

## Grounding with Google Search

Grounding[^8] allows Gemini to retrieve up-to-date information from Google
Search, reducing hallucinations and providing current data.

### Search Grounding Configuration

**Availability**: Vertex AI only (not available in Google AI Studio)

```python
from vertexai.preview.generative_models import (
    GenerativeModel,
    Tool,
    grounding
)

# Create grounding tool
google_search_tool = Tool.from_google_search_retrieval(
    grounding.GoogleSearchRetrieval()
)

model = GenerativeModel(
    "gemini-2.0-flash",
    tools=[google_search_tool]
)

response = model.generate_content(
    "What are the latest Python 3.13 features released in 2024?"
)

print(response.text)

# Access grounding metadata
if response.candidates[0].grounding_metadata:
    metadata = response.candidates[0].grounding_metadata
    print(f"\nGrounding sources: {len(metadata.grounding_chunks)}")
    for chunk in metadata.grounding_chunks:
        print(f"- {chunk.web.uri}")
```

### Dynamic Retrieval

You can control when grounding is applied:

```python
from vertexai.preview.generative_models import grounding

# Configure dynamic retrieval threshold
google_search_tool = Tool.from_google_search_retrieval(
    grounding.GoogleSearchRetrieval(
        disable_attribution=False  # Include source attribution
    )
)

model = GenerativeModel(
    "gemini-1.5-pro",
    tools=[google_search_tool]
)

# Gemini decides when to use search based on query needs
response = model.generate_content(
    """Compare the performance characteristics of Python 3.13 vs 3.12.
    Include benchmarks if available."""
)
```

### Grounding Metadata

Grounding responses include metadata about sources:

```python
response = model.generate_content("Latest news about Gemini 2.0")

metadata = response.candidates[0].grounding_metadata

# Grounding support score (0.0 to 1.0)
print(f"Support score: {metadata.grounding_support.support_score}")

# Search entry point (the query used)
if metadata.search_entry_point:
    print(f"Search query: {metadata.search_entry_point.rendered_content}")

# Retrieved chunks and sources
for chunk in metadata.grounding_chunks:
    if chunk.web:
        print(f"Source: {chunk.web.title}")
        print(f"URL: {chunk.web.uri}")
```

### Use Cases for Grounding

#### Ideal Use Cases

1. **Current Events and News**

```python
prompt = "What are the major tech announcements from CES 2025?"
# Grounding ensures up-to-date information
```

1. **Recent API Documentation**

```python
prompt = "How do I use the new React Server Components in Next.js 15?"
# Gets latest documentation and examples
```

1. **Version-Specific Information**

```python
prompt = "What breaking changes were introduced in TypeScript 5.3?"
# Retrieves accurate version-specific details
```

1. **Factual Verification**

```python
prompt = "What is the current market cap of NVIDIA?"
# Grounds answer in current data
```

#### Poor Use Cases

1. **Creative Writing** - Grounding not needed
2. **Code Generation from Requirements** - Internal knowledge sufficient
3. **General Programming Concepts** - Model knowledge adequate
4. **Refactoring Existing Code** - Context-based task

You SHOULD use grounding when:

- Information changes frequently
- Accuracy of current data is critical
- User asks about recent events (last 6 months)
- Factual verification is needed

You SHOULD NOT use grounding when:

- Question is about established concepts
- Speed is more important than currency
- User's codebase context is more relevant than web search
- Privacy concerns with query content

---

## Large Context Window Usage

Gemini models support massive context windows (1M-2M tokens), enabling analysis
of entire codebases, long documents, and extensive conversations.

### Context Window Capabilities

| Model             | Input Tokens | Output Tokens | Equivalent                 |
| ----------------- | ------------ | ------------- | -------------------------- |
| Gemini 2.0 Flash  | 1,048,576    | 8,192         | ~800K words or ~3500 pages |
| Gemini 1.5 Pro    | 2,097,152    | 8,192         | ~1.6M words or ~7000 pages |
| Gemini 1.5 Flash  | 1,048,576    | 8,192         | ~800K words or ~3500 pages |

**Token Estimation**:

- 1 token ≈ 4 characters
- 1 token ≈ 0.75 words
- 1000 tokens ≈ 750 words
- 100K tokens ≈ 75,000 words ≈ 300 pages

### Effective Context Loading

#### Loading Multiple Files

```python
import os
from pathlib import Path

def load_codebase(root_dir: str, extensions: list[str]) -> str:
    """Load all files with specified extensions into a single context"""
    context_parts = []

    for ext in extensions:
        for file_path in Path(root_dir).rglob(f"*.{ext}"):
            relative_path = file_path.relative_to(root_dir)
            try:
                content = file_path.read_text()
                context_parts.append(
                    f"### File: {relative_path}\n\n```{ext}\n{content}\n```\n"
                )
            except Exception as e:
                print(f"Error loading {file_path}: {e}")

    return "\n".join(context_parts)

# Load entire Python codebase
codebase_context = load_codebase(
    root_dir="./src",
    extensions=["py", "yaml", "md"]
)

# Create prompt with full codebase
prompt = f"""Analyze this codebase for security vulnerabilities.

{codebase_context}

Provide a comprehensive security audit report."""

model = genai.GenerativeModel("gemini-1.5-pro")
response = model.generate_content(prompt)
```

#### Structured Context Organization

```python
def create_structured_context(
    files: dict[str, str],
    docs: str,
    requirements: list[str]
) -> str:
    """Create well-organized context for better understanding"""

    context = """# Project Context

## Requirements
"""
    for i, req in enumerate(requirements, 1):
        context += f"{i}. {req}\n"

    context += "\n## Documentation\n\n"
    context += docs

    context += "\n## Source Code\n\n"
    for file_path, content in files.items():
        context += f"### {file_path}\n\n```python\n{content}\n```\n\n"

    return context

# Usage
context = create_structured_context(
    files={
        "app/models.py": models_code,
        "app/views.py": views_code,
        "app/tests.py": tests_code
    },
    docs=readme_content,
    requirements=[
        "Add user authentication",
        "Implement rate limiting",
        "Add comprehensive logging"
    ]
)
```

### Context Caching

Context caching[^9] allows you to reuse large context prefixes, reducing costs
by up to 75% and improving latency.

**How It Works**:

1. First request: Full context is processed and cached
2. Subsequent requests: Cached portion is reused (at 75% discount)
3. Cache TTL: 1 hour (refreshed on each use)
4. Minimum cacheable size: 32,768 tokens (~24K words)

```python
from google.generativeai import caching
import datetime

# Create cached content
cache = caching.CachedContent.create(
    model='models/gemini-1.5-pro-001',
    system_instruction="""You are a code review expert familiar with this codebase.""",
    contents=[{
        'role': 'user',
        'parts': [{
            'text': codebase_context  # Large codebase context
        }]
    }],
    ttl=datetime.timedelta(hours=1),
)

# Use cached context
model = genai.GenerativeModel.from_cached_content(cache)

# First query (uses cache)
response1 = model.generate_content(
    "Review the authentication module for security issues"
)

# Second query (reuses cache, much cheaper)
response2 = model.generate_content(
    "Check for SQL injection vulnerabilities"
)

# Third query (still using cache)
response3 = model.generate_content(
    "Analyze error handling patterns"
)

# Delete cache when done (optional - will expire after TTL)
cache.delete()
```

**Cost Example**:

- Codebase: 500K tokens
- First request: 500K tokens × $1.25/1M = $0.625
- Cached requests: 500K tokens × $0.3125/1M = $0.156 (75% savings)
- 10 queries: $0.625 + (9 × $0.156) = $2.029
- Without caching: 10 × $0.625 = $6.25
- **Savings: 67.5%**

### Long Context Strategies

#### 1. Progressive Context Building

For very large codebases, build context progressively:

```python
# Phase 1: High-level overview
overview_prompt = """Analyze this project structure and identify the main components:

{directory_tree}
{readme_content}
"""

overview = model.generate_content(overview_prompt)

# Phase 2: Detailed analysis of specific areas
detail_prompt = f"""Based on this overview:
{overview.text}

Now analyze these specific files in detail:
{relevant_files_context}
"""

detailed_analysis = model.generate_content(detail_prompt)
```

#### 2. Hierarchical Context

```python
def create_hierarchical_context(project_root: str) -> str:
    """Create context with hierarchical detail levels"""

    context = "# Codebase Overview\n\n"

    # Level 1: Directory structure
    context += "## Structure\n"
    context += get_directory_tree(project_root)

    # Level 2: File summaries
    context += "\n## File Summaries\n"
    for file in get_source_files(project_root):
        summary = get_file_summary(file)  # First 10 lines + function signatures
        context += f"### {file}\n{summary}\n\n"

    # Level 3: Full code for key files
    context += "\n## Key Files (Full Content)\n"
    key_files = ["main.py", "models.py", "api.py"]
    for file in key_files:
        content = read_file(file)
        context += f"### {file}\n```python\n{content}\n```\n\n"

    return context
```

#### 3. Selective Context

```python
def get_relevant_context(query: str, codebase_index: dict) -> str:
    """Retrieve only relevant files based on query"""

    # Use semantic search or keyword matching to find relevant files
    relevant_files = search_codebase(query, codebase_index)

    context = "# Relevant Code\n\n"
    for file, relevance_score in relevant_files[:20]:  # Top 20 files
        content = read_file(file)
        context += f"### {file} (relevance: {relevance_score:.2f})\n"
        context += f"```\n{content}\n```\n\n"

    return context
```

### Context Window Limitations

#### What Works Well

1. **Code Analysis** (up to 1M lines)
2. **Documentation Review** (thousands of pages)
3. **Log Analysis** (gigabytes of logs)
4. **Multi-file Refactoring**
5. **Comprehensive Testing**

#### What Doesn't Work Well

1. **Extremely Dense Technical Content** - Model may struggle with highly compressed information
2. **Repetitive Content** - Redundant information wastes context
3. **Binary or Encoded Data** - Not suitable for large context
4. **Poorly Structured Data** - Difficult to extract value

#### Best Practices

You MUST:

- Structure context clearly with headers and sections
- Include file paths and line numbers for code
- Remove irrelevant files (build artifacts, dependencies)
- Use markdown formatting for readability

You SHOULD:

- Prioritize important files at the beginning
- Include README and architecture docs early
- Use context caching for repeated queries
- Compress whitespace and empty lines

You SHOULD NOT:

- Include generated code (build outputs)
- Include binary files or images as text
- Include entire dependency code
- Duplicate information unnecessarily

---

## Cost Optimization

### Model Selection for Cost

Choose the right model based on task complexity:

```python
def select_model(task_type: str, context_size: int) -> str:
    """Select cost-effective model for task"""

    if context_size > 1_000_000:
        return "gemini-1.5-pro"  # Only option for 2M context

    if task_type in ["simple_qa", "classification", "extraction"]:
        return "gemini-2.0-flash"  # Fast and cheap

    if task_type in ["complex_reasoning", "architecture", "refactoring"]:
        if context_size > 100_000:
            return "gemini-1.5-pro"  # Better for complex + large context
        return "gemini-2.0-flash"  # Try flash first

    return "gemini-2.0-flash"  # Default to flash
```

### Context Caching for Savings

**Rule of Thumb**: Use caching when you'll make 4+ requests with the same large context.

```python
# Break-even analysis
# Cache creation: 500K tokens × $1.25/1M = $0.625
# Cache usage: 500K tokens × $0.3125/1M = $0.156
# Savings per cached request: $0.625 - $0.156 = $0.469
# Break-even: ~2 requests (pays for itself quickly)

def should_use_caching(
    context_size: int,
    expected_queries: int,
    model: str = "gemini-1.5-pro"
) -> bool:
    """Determine if caching is cost-effective"""

    if context_size < 32_768:
        return False  # Below minimum cache size

    if expected_queries < 2:
        return False  # Not enough queries to benefit

    # Calculate costs
    base_cost_per_token = 1.25 / 1_000_000  # Gemini 1.5 Pro
    cache_cost_per_token = 0.3125 / 1_000_000

    without_cache = expected_queries * context_size * base_cost_per_token
    with_cache = (
        context_size * base_cost_per_token +  # First request
        (expected_queries - 1) * context_size * cache_cost_per_token
    )

    return with_cache < without_cache
```

### Prompt Engineering for Efficiency

#### 1. Be Specific to Reduce Output Tokens

```python
# EXPENSIVE - Generates long response
prompt = "Tell me about this codebase."

# CHEAPER - Targeted response
prompt = """List the 5 most critical security issues in this codebase.
For each, provide:
1. Issue description (1 line)
2. Location (file:line)
3. Fix (1 line)

Use this format:
- Issue | Location | Fix
"""
```

#### 2. Use Structured Output

```python
# Request JSON for predictable token usage
prompt = """Analyze code quality. Return JSON only:
{
    "score": 0-100,
    "issues": [
        {"severity": "HIGH|MED|LOW", "description": "...", "file": "...", "line": 0}
    ],
    "summary": "One sentence"
}
"""
```

#### 3. Avoid Unnecessary Examples

```python
# EXPENSIVE - Many examples in every request
prompt = f"""Refactor this code. Follow these examples:
{example1}
{example2}
{example3}

Code to refactor:
{code}
"""

# CHEAPER - Use system instructions for examples (one-time cost)
system_instruction = f"""When refactoring, follow these patterns:
{example1}
{example2}
"""

model = genai.GenerativeModel(
    "gemini-2.0-flash",
    system_instruction=system_instruction
)

# Now prompts can be simple
prompt = f"Refactor this code:\n{code}"
```

### Batch Processing

Group requests to amortize fixed costs:

```python
async def batch_analyze_files(files: list[str], batch_size: int = 10):
    """Analyze files in batches to reduce overhead"""

    results = []

    for i in range(0, len(files), batch_size):
        batch = files[i:i + batch_size]

        # Single request for batch
        prompt = "Analyze these files for bugs:\n\n"
        for j, file_path in enumerate(batch, 1):
            content = read_file(file_path)
            prompt += f"## File {j}: {file_path}\n```\n{content}\n```\n\n"

        prompt += "\nReturn JSON array: [{\"file\": \"...\", \"issues\": [...]}]"

        response = await model.generate_content_async(prompt)
        results.extend(json.loads(response.text))

    return results
```

### Rate Limiting and Quotas

**Google AI Studio** quotas (free tier)[^2]:

- 15 requests per minute
- 1,500 requests per day
- 1 million tokens per minute

**Vertex AI** quotas (default, can request increases)[^3]:

- 300 requests per minute
- 10,000 requests per hour
- 4 million tokens per minute

Implement rate limiting:

```python
import time
from collections import deque

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = deque()

    def wait_if_needed(self):
        now = time.time()
        minute_ago = now - 60

        # Remove requests older than 1 minute
        while self.requests and self.requests[0] < minute_ago:
            self.requests.popleft()

        # Check if we need to wait
        if len(self.requests) >= self.requests_per_minute:
            sleep_time = 60 - (now - self.requests[0])
            if sleep_time > 0:
                time.sleep(sleep_time)

        self.requests.append(time.time())

# Usage
limiter = RateLimiter(requests_per_minute=50)

for prompt in prompts:
    limiter.wait_if_needed()
    response = model.generate_content(prompt)
```

---

## Common Pitfalls

### Safety Settings Issues

**Problem**: Requests blocked by safety filters

```python
# Default safety settings may block legitimate requests
response = model.generate_content("Analyze this SQL injection vulnerability")
# May be blocked as "dangerous content"
```

**Solution**: Configure safety settings appropriately

```python
from google.generativeai.types import HarmCategory, HarmBlockThreshold[^11]

model = genai.GenerativeModel(
    "gemini-2.0-flash",
    safety_settings={
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    }
)

# For security analysis, you may need BLOCK_ONLY_HIGH
# For public-facing apps, use BLOCK_MEDIUM_AND_ABOVE
```

**Best Practice**:

- Development: BLOCK_ONLY_HIGH for flexibility
- Production: BLOCK_MEDIUM_AND_ABOVE for safety
- Security tools: BLOCK_NONE with explicit disclaimers

### Context Window Misuse

**Problem**: Exceeding context limits or inefficient context usage

```python
# BAD - Loading unnecessary files
context = load_all_files("./")  # Includes node_modules, .git, etc.
```

**Solution**: Filter and optimize context

```python
# GOOD - Selective loading
def load_source_files(root_dir: str) -> str:
    exclude_dirs = {
        'node_modules', '.git', '__pycache__', 'venv',
        'dist', 'build', '.next', 'coverage'
    }

    exclude_extensions = {
        '.pyc', '.so', '.dylib', '.bin', '.lock',
        '.jpg', '.png', '.gif', '.mp4'
    }

    context = []
    for file_path in Path(root_dir).rglob("*"):
        # Skip excluded directories
        if any(excl in file_path.parts for excl in exclude_dirs):
            continue

        # Skip excluded extensions
        if file_path.suffix in exclude_extensions:
            continue

        # Skip large files (> 1MB)
        if file_path.stat().st_size > 1_000_000:
            continue

        try:
            content = file_path.read_text()
            context.append(f"### {file_path}\n```\n{content}\n```\n")
        except:
            pass

    return "\n".join(context)
```

### Function Calling Errors

**Problem**: Infinite loops or failed function calls

```python
# BAD - Model keeps calling function that fails
def buggy_function(arg):
    raise Exception("Always fails")

# Model calls function → Error → Model tries again → Error → ...
```

**Solution**: Implement retry limits and error feedback

```python
MAX_FUNCTION_RETRIES = 3

def execute_function_with_retry(fc, attempt=1):
    try:
        result = function_map[fc.name](**dict(fc.args))
        return {"success": True, "result": result}
    except Exception as e:
        if attempt >= MAX_FUNCTION_RETRIES:
            return {
                "success": False,
                "error": "max_retries_exceeded",
                "message": f"Function failed after {MAX_FUNCTION_RETRIES} attempts: {str(e)}"
            }

        # Return error to model for adjustment
        return {
            "success": False,
            "error": "function_error",
            "message": str(e),
            "retry_available": True
        }
```

### JSON Mode Mistakes

**Problem**: Expecting perfect JSON without configuration

```python
# BAD - Hoping for JSON without specifying
prompt = "Return user data as JSON"
response = model.generate_content(prompt)
data = json.loads(response.text)  # May fail
```

**Solution**: Use structured output configuration

```python
# GOOD - Explicit JSON mode (when available) or strict prompting
prompt = """Return ONLY valid JSON, no markdown, no explanation:
{
    "name": "...",
    "email": "...",
    "role": "..."
}

Extract user data from: {user_text}
"""

response = model.generate_content(prompt)

# Robust parsing
try:
    # Remove markdown code blocks if present
    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]

    data = json.loads(text)
except json.JSONDecodeError as e:
    # Handle parse error
    print(f"JSON parse error: {e}")
    print(f"Response was: {response.text}")
```

### Streaming Complications

**Problem**: Improper handling of streaming responses

```python
# BAD - Not handling streaming properly
response = model.generate_content(prompt, stream=True)
print(response.text)  # Error! No .text attribute on streaming response
```

**Solution**: Iterate over streaming chunks[^19]

```python
# GOOD - Proper streaming
response = model.generate_content(prompt, stream=True)

full_response = []
for chunk in response:
    if chunk.text:
        print(chunk.text, end='', flush=True)
        full_response.append(chunk.text)

complete_text = ''.join(full_response)
```

**For Function Calling with Streaming**:

```python
response = model.generate_content(prompt, stream=True)

function_calls = []
text_parts = []

for chunk in response:
    # Check for function calls
    if chunk.candidates[0].content.parts:
        for part in chunk.candidates[0].content.parts:
            if hasattr(part, 'function_call'):
                function_calls.append(part.function_call)
            elif hasattr(part, 'text'):
                text_parts.append(part.text)

# Process function calls if any
if function_calls:
    # Execute functions and continue conversation
    ...
else:
    # Just text response
    complete_text = ''.join(text_parts)
```

---

## Do and Don't Examples

### Prompt Engineering

#### DO: Be Specific and Structured

````python
# GOOD
prompt = """Refactor this Python function following these requirements:

1. Convert to async/await
2. Add type hints
3. Add error handling for network failures
4. Add docstring with Google style

Original function:
```python
def fetch_data(url):
    response = requests.get(url)
    return response.json()
```

Return only the refactored code with brief explanation of changes.
"""
````

#### DON'T: Be Vague

```python
# BAD
prompt = "Make this code better: {code}"
```

#### DO: Provide Examples for Complex Tasks

````python
# GOOD
prompt = """Convert these API endpoint descriptions to OpenAPI spec.

Example:
Input: "GET /users/{id} - Returns user by ID"
Output:
```yaml
/users/{id}:
  get:
    summary: Get user by ID
    parameters:
      - name: id
        in: path
        required: true
        schema:
          type: integer
```

Now convert:
{api_descriptions}
"""
````

#### DON'T: Assume Model Knows Your Format

```python
# BAD
prompt = f"Convert to OpenAPI: {descriptions}"
# Model may use different OpenAPI version or structure
```

### API Usage

#### DO: Handle Errors Gracefully

```python
# GOOD
import google.api_core.exceptions

try:
    response = model.generate_content(prompt)
    print(response.text)
except google.api_core.exceptions.ResourceExhausted:
    print("Quota exceeded. Please wait and retry.")
    # Implement exponential backoff
except google.api_core.exceptions.InvalidArgument as e:
    print(f"Invalid request: {e}")
    # Log and fix the request
except Exception as e:
    print(f"Unexpected error: {e}")
    # Log for investigation
```

#### DON'T: Ignore Error Handling

```python
# BAD
response = model.generate_content(prompt)
print(response.text)
# Will crash on any error
```

#### DO: Use Streaming for Long Responses

```python
# GOOD - Streaming for better UX
response = model.generate_content(long_prompt, stream=True)

for chunk in response:
    print(chunk.text, end='', flush=True)
    # User sees progressive output
```

#### DON'T: Block on Large Responses

```python
# BAD - User waits 30 seconds for complete response
response = model.generate_content(long_prompt)
# ... long wait ...
print(response.text)
```

### Function Calling

#### DO: Validate Function Arguments

```python
# GOOD
def execute_database_query(sql: str, database: str) -> dict:
    # Validate SQL
    if not sql.strip().upper().startswith('SELECT'):
        return {
            "success": False,
            "error": "Only SELECT queries allowed"
        }

    # Validate database
    allowed_dbs = ['analytics', 'reporting']
    if database not in allowed_dbs:
        return {
            "success": False,
            "error": f"Database must be one of {allowed_dbs}"
        }

    # Execute with timeout
    try:
        result = execute_with_timeout(sql, database, timeout=10)
        return {"success": True, "data": result}
    except TimeoutError:
        return {
            "success": False,
            "error": "Query timeout after 10 seconds"
        }
```

#### DON'T: Execute Unchecked Functions

```python
# BAD - Security nightmare
def execute_code(code: str):
    return eval(code)  # Never do this!
```

#### DO: Provide Rich Error Context

```python
# GOOD
def search_codebase(pattern: str, file_type: str = None) -> dict:
    try:
        results = perform_search(pattern, file_type)
        return {
            "success": True,
            "matches": len(results),
            "results": results[:50]  # Limit results
        }
    except re.error as e:
        return {
            "success": False,
            "error": "invalid_regex",
            "message": f"Invalid regex pattern: {str(e)}",
            "suggestion": "Try a simpler pattern or escape special characters"
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": "directory_not_found",
            "message": "Source directory not found",
            "suggestion": "Check that the project is properly initialized"
        }
```

#### DON'T: Return Generic Errors

```python
# BAD
def search_codebase(pattern: str) -> dict:
    try:
        return perform_search(pattern)
    except:
        return {"error": "Something went wrong"}
```

### Context Management

#### DO: Organize Context Hierarchically

```python
# GOOD
context = f"""# Project: E-commerce API

## Architecture
{architecture_doc}

## Key Files

### Core Models
{models_code}

### API Endpoints
{api_code}

### Database Schema
{schema_sql}

## Configuration
{config_yaml}

## Recent Changes
{git_log}
"""
```

#### DON'T: Dump Unstructured Content

```python
# BAD
context = all_files_concatenated
# Model struggles to understand structure
```

#### DO: Use Context Caching for Repeated Queries

```python
# GOOD - Cache large static context
cache = caching.CachedContent.create(
    model='models/gemini-1.5-pro-001',
    contents=[{
        'role': 'user',
        'parts': [{'text': large_codebase_context}]
    }],
    ttl=datetime.timedelta(hours=1),
)

model = genai.GenerativeModel.from_cached_content(cache)

# Multiple queries reuse cached context
for query in queries:
    response = model.generate_content(query)
```

#### DON'T: Repeat Large Context on Every Request

```python
# BAD - Paying full price every time
for query in queries:
    prompt = f"{large_codebase_context}\n\nQuery: {query}"
    response = model.generate_content(prompt)
    # Expensive!
```

### Error Handling

#### DO: Implement Exponential Backoff

```python
# GOOD
import time

def generate_with_retry(prompt: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            return model.generate_content(prompt)
        except google.api_core.exceptions.ResourceExhausted:
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + (random.random() * 0.1)
                print(f"Rate limited. Retrying in {wait_time:.1f}s...")
                time.sleep(wait_time)
            else:
                raise
        except google.api_core.exceptions.ServiceUnavailable:
            if attempt < max_retries - 1:
                wait_time = 5 * (attempt + 1)
                print(f"Service unavailable. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
```

#### DON'T: Retry Immediately Without Backoff

```python
# BAD
for attempt in range(3):
    try:
        return model.generate_content(prompt)
    except:
        continue  # Immediate retry hammers the API
```

---

## Advanced Techniques

### Multi-Turn Conversations

Maintain conversation state for complex interactions:

```python
model = genai.GenerativeModel("gemini-2.0-flash")
chat = model.start_chat(history=[])

# Turn 1
response1 = chat.send_message("Analyze this function for bugs: {code}")
print(response1.text)

# Turn 2 - Model remembers previous context
response2 = chat.send_message("Now refactor it to fix those bugs")
print(response2.text)

# Turn 3 - Model remembers both previous turns
response3 = chat.send_message("Add unit tests for the refactored version")
print(response3.text)

# Access conversation history
for message in chat.history:
    print(f"{message.role}: {message.parts[0].text[:100]}...")
```

### Code Execution

Gemini can execute Python code[^10] (Vertex AI only):

```python
from vertexai.preview.generative_models import Tool

# Enable code execution
code_execution_tool = Tool.from_code_execution()

model = GenerativeModel(
    "gemini-1.5-pro",
    tools=[code_execution_tool]
)

response = model.generate_content(
    """Calculate the first 10 Fibonacci numbers and plot them.
    Show both the numbers and a line graph."""
)

print(response.text)
# Model writes Python code, executes it, and returns results + visualization
```

### Multimodal Capabilities

Process images, videos, and audio alongside text[^17]:

```python
import PIL.Image

# Analyze code screenshot
image = PIL.Image.open("screenshot.png")

response = model.generate_content([
    "What does this code do? Identify any bugs.",
    image
])

# Analyze architecture diagram
diagram = PIL.Image.open("architecture.png")

response = model.generate_content([
    "Convert this architecture diagram to a text description and mermaid diagram",
    diagram
])

# Analyze video walkthrough
video_file = genai.upload_file("code_review.mp4")

response = model.generate_content([
    "Summarize the key points from this code review video",
    video_file
])
```

### Controlled Generation

Control output format and structure[^20]:

```python
# JSON schema for structured output
json_schema = {
    "type": "object",
    "properties": {
        "vulnerabilities": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "severity": {"type": "string", "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW"]},
                    "category": {"type": "string"},
                    "location": {"type": "string"},
                    "description": {"type": "string"},
                    "fix": {"type": "string"}
                },
                "required": ["severity", "category", "location", "description", "fix"]
            }
        },
        "summary": {"type": "string"}
    },
    "required": ["vulnerabilities", "summary"]
}

prompt = f"""Analyze this code for security vulnerabilities.

Return a JSON object matching this schema:
{json.dumps(json_schema, indent=2)}

Code:
{code}
"""
```

---

## Security and Privacy

### Data Handling

**Google's Data Usage Policies**:

**Google AI Studio**:

- Prompts and responses MAY be used to improve models
- NOT suitable for sensitive or private data
- No data residency guarantees
- Not covered by Google Cloud SLAs

**Vertex AI**:

- Your data is NOT used to train models (with standard agreement)
- Suitable for sensitive business data
- Data residency controls available
- Covered by Google Cloud SLAs and compliance certifications

You MUST:

- Use Vertex AI for production and sensitive data
- Never include PII, credentials, or secrets in prompts
- Implement data sanitization before sending to API
- Review Google's data usage policies for your use case

You SHOULD:

- Use environment variables for all API keys
- Implement access controls on API endpoints
- Log API usage for audit trails
- Redact sensitive information from logs

### API Key Management

```python
# DO: Use environment variables
import os
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY environment variable not set")

# DO: Use secret management services
from google.cloud import secretmanager
client = secretmanager.SecretManagerServiceClient()
name = "projects/PROJECT_ID/secrets/gemini-api-key/versions/latest"
response = client.access_secret_version(request={"name": name})
api_key = response.payload.data.decode("UTF-8")

# DON'T: Hardcode API keys
api_key = "AIzaSy..."  # Never do this!

# DON'T: Commit to version control
# .env file with API_KEY=... committed to git  # Never!
```

### Content Filtering

Configure appropriate safety settings[^18] for your use case:

```python
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# For public-facing applications
public_safety_settings = {
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
}

# For security analysis tools
security_tool_settings = {
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
}

model = genai.GenerativeModel(
    "gemini-2.0-flash",
    safety_settings=public_safety_settings
)
```

### Compliance Considerations

**Certifications** (Vertex AI)[^3]:

- SOC 2/3
- ISO 27001
- HIPAA (with BAA)
- PCI DSS
- GDPR compliant

**Required for Compliance**:

1. Use Vertex AI (not Google AI Studio)
2. Enable VPC Service Controls
3. Use customer-managed encryption keys (CMEK)
4. Enable Cloud Audit Logs
5. Implement data retention policies
6. Configure appropriate regional endpoints

---

## Monitoring and Debugging

### Response Quality Metrics

Track key quality indicators:

```python
class ResponseMetrics:
    def __init__(self):
        self.total_requests = 0
        self.successful_requests = 0
        self.blocked_by_safety = 0
        self.function_call_errors = 0
        self.latencies = []

    def record_request(
        self,
        success: bool,
        latency_ms: float,
        blocked: bool = False,
        function_error: bool = False
    ):
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        if blocked:
            self.blocked_by_safety += 1
        if function_error:
            self.function_call_errors += 1
        self.latencies.append(latency_ms)

    def get_summary(self):
        return {
            "success_rate": self.successful_requests / self.total_requests,
            "safety_block_rate": self.blocked_by_safety / self.total_requests,
            "function_error_rate": self.function_call_errors / self.total_requests,
            "avg_latency_ms": sum(self.latencies) / len(self.latencies),
            "p95_latency_ms": sorted(self.latencies)[int(len(self.latencies) * 0.95)],
            "p99_latency_ms": sorted(self.latencies)[int(len(self.latencies) * 0.99)],
        }
```

### Performance Monitoring

```python
import time
import logging

def monitored_generate(prompt: str, **kwargs):
    start_time = time.time()

    try:
        response = model.generate_content(prompt, **kwargs)
        latency = (time.time() - start_time) * 1000

        # Log metrics
        logging.info(
            "gemini_request",
            extra={
                "latency_ms": latency,
                "model": model.model_name,
                "prompt_length": len(prompt),
                "response_length": len(response.text),
                "success": True
            }
        )

        return response

    except Exception as e:
        latency = (time.time() - start_time) * 1000

        logging.error(
            "gemini_request_failed",
            extra={
                "latency_ms": latency,
                "error": str(e),
                "error_type": type(e).__name__,
                "success": False
            }
        )
        raise
```

### Debugging Techniques

#### 1. Inspect Full Response

```python
response = model.generate_content(prompt)

# Check safety ratings
for rating in response.candidates[0].safety_ratings:
    print(f"{rating.category}: {rating.probability}")

# Check finish reason
print(f"Finish reason: {response.candidates[0].finish_reason}")
# Possible values:
# - FINISH_REASON_STOP: Natural completion
# - FINISH_REASON_MAX_TOKENS: Hit output limit
# - FINISH_REASON_SAFETY: Blocked by safety filters
# - FINISH_REASON_RECITATION: Blocked for recitation

# Check token usage (if available)
if hasattr(response, 'usage_metadata'):
    print(f"Prompt tokens: {response.usage_metadata.prompt_token_count}")
    print(f"Candidates tokens: {response.usage_metadata.candidates_token_count}")
    print(f"Total tokens: {response.usage_metadata.total_token_count}")
```

#### 2. Debug Function Calling

```python
# Enable verbose logging
import logging
logging.basicConfig(level=logging.DEBUG)

response = model.generate_content(prompt)

# Inspect function calls
for part in response.candidates[0].content.parts:
    if hasattr(part, 'function_call'):
        fc = part.function_call
        print(f"Function: {fc.name}")
        print(f"Arguments: {dict(fc.args)}")
        print(f"Arguments JSON: {json.dumps(dict(fc.args), indent=2)}")
```

#### 3. Test Safety Filters

```python
def test_safety_filter(prompt: str):
    try:
        response = model.generate_content(prompt)
        print(f"✓ Passed: {response.text[:100]}...")
    except Exception as e:
        print(f"✗ Blocked: {str(e)}")

    # Check detailed safety ratings
    if 'response' in locals():
        print("\nSafety Ratings:")
        for rating in response.candidates[0].safety_ratings:
            print(f"  {rating.category}: {rating.probability}")

test_safety_filter("Analyze this SQL injection vulnerability: {code}")
```

---

## References

[^1]: [Google Gemini Models Overview](https://ai.google.dev/gemini-api/docs/models/gemini) - Official documentation for Gemini model family
[^2]: [Google AI Studio](https://aistudio.google.com/) - Web-based IDE and API access for Gemini
[^3]: [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs) - Enterprise platform for Gemini deployment
[^4]: [Gemini 2.0 Flash Documentation](https://ai.google.dev/gemini-api/docs/models/gemini-v2) - Latest Flash model specifications
[^5]: [Gemini 1.5 Pro Documentation](https://ai.google.dev/gemini-api/docs/models/gemini-v1.5) - Pro model with 2M token context window
[^6]: [Gemini 1.5 Flash Documentation](https://ai.google.dev/gemini-api/docs/models/gemini-v1.5) - Balanced Flash model specifications
[^7]: [Google AI Pricing](https://ai.google.dev/pricing) - Current pricing for Google AI Studio and Vertex AI
[^8]: [Grounding with Google Search](https://cloud.google.com/vertex-ai/docs/generative-ai/grounding/ground-with-google-search) - Search grounding documentation
[^9]: [Context Caching](https://ai.google.dev/gemini-api/docs/caching) - Prompt caching guide for cost optimization
[^10]: [Code Execution](https://cloud.google.com/vertex-ai/docs/generative-ai/code/code-execution-overview) - Python code execution feature
[^12]: [Vertex AI Python SDK](https://cloud.google.com/python/docs/reference/aiplatform/latest) - Google Cloud AI Platform SDK
[^16]: [Function Calling Guide](https://ai.google.dev/gemini-api/docs/function-calling) -
    Function calling documentation and best practices
[^17]: [Multimodal Prompting](https://ai.google.dev/gemini-api/docs/vision) - Guide to using images, video, and audio with Gemini
[^18]: [Safety Settings](https://ai.google.dev/gemini-api/docs/safety-settings) - Content filtering and safety configuration guide
[^19]: [Streaming Responses](https://ai.google.dev/gemini-api/docs/streaming) -
    Guide to streaming API responses
[^20]: [JSON Mode](https://ai.google.dev/gemini-api/docs/json-mode) - Controlled generation with JSON schema

### Additional Resources

**Official Documentation**:

- [Gemini API Reference](https://ai.google.dev/api) - Complete API reference
- [Generative AI on Vertex AI](https://cloud.google.com/vertex-ai/docs/generative-ai/learn/overview)
  - Enterprise features and capabilities

**Security and Compliance**:

- [Vertex AI Security](https://cloud.google.com/vertex-ai/docs/general/security) - Security
  features and best practices
- [Data Usage FAQ](https://ai.google.dev/gemini-api/docs/faq) - Privacy and data usage
  policies
- [Google Cloud Compliance](https://cloud.google.com/security/compliance) - Compliance
  certifications

**Best Practices**:

- [Prompt Engineering Guide](https://ai.google.dev/docs/prompt_best_practices) - Effective
  prompting strategies
- [System Instructions](https://ai.google.dev/gemini-api/docs/system-instructions) - Using
  system instructions
- [Safety Settings](https://ai.google.dev/gemini-api/docs/safety-settings) - Content
  filtering configuration
- [Function Calling Guide](https://ai.google.dev/gemini-api/docs/function-calling) - Function
  calling documentation

**Community and Support**:

- [Google AI Discord](https://discord.gg/google-ai-dev) - Community discussions
- [Stack Overflow](https://stackoverflow.com/questions/tagged/google-gemini) - Q&A tagged with google-gemini
- [GitHub Discussions](https://github.com/google/generative-ai-python/discussions) - Python SDK discussions

---

**Document Version**: 1.0
**Last Updated**: December 2024
**Status**: Active
