# OpenAI Best Practices

**Navigation:** [Home](../../README.md) > [AI Guides](README.md) > OpenAI Best Practices

**Version:** 1.0.0
**Last Updated:** 2025-12-07
**Status:** Active

---

## RFC 2119 Key Words

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in
[RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

---

## Table of Contents

1. [Overview](#overview)
2. [Model Selection](#model-selection)
3. [API Patterns](#api-patterns)
4. [System Prompts for Coding](#system-prompts-for-coding)
5. [Function Calling](#function-calling)
6. [Structured Outputs](#structured-outputs)
7. [Cost Optimization](#cost-optimization)
8. [Common Pitfalls](#common-pitfalls)
9. [Do/Don't Examples](#dodont-examples)
10. [References](#references)

---

## Overview

This document provides best practices for integrating OpenAI's API into
production systems. It focuses on practical patterns, cost optimization, and
reliability considerations for software engineering teams.

### Scope

This guide covers:

- Model selection and pricing
- API integration patterns
- Prompt engineering for code generation
- Function calling and structured outputs
- Cost optimization strategies
- Common pitfalls and their solutions

### Prerequisites

Teams implementing OpenAI integrations MUST have:

- Valid OpenAI API credentials
- Understanding of REST API concepts
- Token budget and monitoring infrastructure
- Error handling and retry logic

---

## Model Selection

### Available Models

OpenAI offers several models[^1] optimized for different use cases. Teams
**MUST** select models based on task complexity, latency requirements, and
budget constraints.

#### GPT-4o (Optimized)

**Use Cases:**

- Complex reasoning tasks
- Multi-step code generation
- Architecture design
- Code review and analysis
- Documentation generation

**Specifications:**

- Context window: 128,000 tokens
- Max output: 16,384 tokens
- Training data: Up to October 2023
- Multimodal: Text and vision

**Pricing (as of December 2025)[^2]:**

- Input: $2.50 per 1M tokens
- Output: $10.00 per 1M tokens
- Batch API Input: $1.25 per 1M tokens
- Batch API Output: $5.00 per 1M tokens

**Performance:**

- Latency: Moderate (2-5 seconds typical)
- Quality: Highest reasoning capability
- Reliability: Production-ready

**Requirements:**

```text
Teams MUST use GPT-4o for:
- Code reviews requiring deep analysis
- Complex refactoring tasks
- Multi-file code generation
- Architectural decisions

Teams SHOULD use GPT-4o for:
- High-stakes production code
- Security-sensitive operations
- Performance-critical implementations
```

#### GPT-4o-mini

**Use Cases:**

- Simple code completions
- Syntax corrections
- Documentation updates
- Test generation
- Code formatting

**Specifications:**

- Context window: 128,000 tokens
- Max output: 16,384 tokens
- Training data: Up to October 2023
- Multimodal: Text and vision

**Pricing (as of December 2025)[^2]:**

- Input: $0.15 per 1M tokens
- Output: $0.60 per 1M tokens
- Batch API Input: $0.075 per 1M tokens
- Batch API Output: $0.30 per 1M tokens

**Performance:**

- Latency: Low (1-2 seconds typical)
- Quality: Good for straightforward tasks
- Cost efficiency: 16x cheaper than GPT-4o

**Requirements:**

```text
Teams MUST use GPT-4o-mini for:
- High-volume, low-complexity tasks
- Prototype development
- Cost-sensitive applications

Teams SHOULD use GPT-4o-mini for:
- Simple CRUD operations
- Boilerplate generation
- Unit test scaffolding
```

#### Reasoning Models (o-series retirement and current targets)

Every o-series reasoning model that earlier revisions of this guide recommended
is retired or scheduled for shutdown. Teams **MUST NOT** target them in new
work, and **MUST** migrate existing integrations to the current reasoning
models listed below.

**Retirement timeline (checked 2026-09-08):**

| Model | Shutdown date | Replacement named at deprecation | Status of that replacement |
| ----- | ------------- | -------------------------------- | -------------------------- |
| `o1-preview` | 2025-07-28 | `o3` | Deprecated, shuts down 2026-12-11 |
| `o1-mini` | 2025-10-27 | `o4-mini` | Deprecated, shuts down 2026-10-23 |
| `o1` | 2026-10-23 | `gpt-5.6-sol` | Current |
| `o1-pro` | 2026-10-23 | `gpt-5.6-sol` (`reasoning.mode: pro`) | Current |
| `o3-mini` | 2026-10-23 | `gpt-5.6-sol` | Current |
| `o4-mini` | 2026-10-23 | `gpt-5.6-terra` | Current |
| `o3` | 2026-12-11 | `gpt-5.6-sol` | Current |
| `o3-pro` | 2026-12-11 | `gpt-5.6-sol` (`reasoning.mode: pro`) | Current |

##### Why the migration target is the current family

Migrating a retired model to the replacement named in its own deprecation
notice lands the integration on another deprecated model. `o1-preview` pointed
at `o3`, which shuts down on 2026-12-11; `o1-mini` pointed at `o4-mini`, which
shuts down on 2026-10-23. Both dates fall inside the support window of code
written today, so the migration target **MUST** be the current family rather
than the historical replacement.

**Current reasoning models (prices and limits checked 2026-09-08):**

| Model | Context window | Max output | Input / output per 1M tokens | `reasoning.effort` |
| ----- | -------------- | ---------- | ---------------------------- | ------------------ |
| `gpt-6-astra` | 1,050,000 | 128,000 | $10.00 / $50.00 | `low` to `max` |
| `gpt-5.6-sol` | 1,050,000 | 128,000 | $4.00 / $20.00 | `none` to `max` |
| `gpt-5.6-terra` | 1,050,000 | 128,000 | $2.00 / $12.00 | `none` to `max` |
| `gpt-5.6-luna` | 1,050,000 | 128,000 | $0.20 / $1.20 | `none` to `max` |

Prompts above 272,000 input tokens bill at 2x the input rate and 1.5x the
output rate for the whole request. GPT-5.6 Sol's $4.00/$20.00 rate is
promotional and holds at least until 2026-11-21.

**Requirements:**

1. Teams **MUST NOT** send requests to `o1-preview` or `o1-mini`; both
   endpoints were shut down in 2025
2. Teams **MUST** use `gpt-6-astra` for the hardest end-to-end reasoning,
   coding, and research work
3. Teams **SHOULD** use `gpt-5.6-sol` for flagship professional work,
   `gpt-5.6-terra` where cost matters, and `gpt-5.6-luna` for the lowest cost
   and latency
4. Teams **MUST** call the Responses API for tool calling with `gpt-6-astra`;
   Chat Completions does not support function calling for that model
5. Teams **MUST NOT** set `reasoning.effort` to `none` on `gpt-6-astra`; the
   request returns HTTP 400
6. Teams **MUST** re-check the deprecations page before pinning any model ID

##### Why the old capability limitations no longer apply

The earlier "no streaming, no function calling, no system messages" limitations
no longer describe any supported model. `gpt-6-astra`, `gpt-5.6-sol`,
`gpt-5.6-terra`, and `gpt-5.6-luna` all list streaming, structured outputs,
function calling, image input, and prompt caching as supported features. The one
real restriction is the API surface: GPT-6 Astra tool calling requires
Responses.

**Sources:**
[Deprecations](https://developers.openai.com/api/docs/deprecations.md),
[Reasoning](https://developers.openai.com/api/docs/guides/reasoning.md),
[GPT-6 Astra](https://developers.openai.com/api/docs/models/gpt-6-astra.md),
[GPT-5.6 Sol](https://developers.openai.com/api/docs/models/gpt-5.6-sol.md),
[GPT-5.6 Terra](https://developers.openai.com/api/docs/models/gpt-5.6-terra.md),
[GPT-5.6 Luna](https://developers.openai.com/api/docs/models/gpt-5.6-luna.md).

### Model Selection Decision Tree

```text
START
  |
  +-- Need function calling? ----YES----> GPT-4o or GPT-4o-mini
  |                                        |
  NO                                       |
  |                                        +-- Complex reasoning? --YES--> GPT-4o
  |                                        |
  +-- Complex reasoning/math? --YES-----> gpt-6-astra (Responses API)
  |                                        NO
  NO                                       |
  |                                        +-- High volume? --YES--> GPT-4o-mini
  |                                        |
  +-- High volume/cost sensitive? ------> GPT-4o-mini              NO
  |                                                                  |
  NO                                                                 |
  |                                                                  |
  +-- Default to GPT-4o <-----------------------------------------<-+
```

### Model Selection Requirements

1. Teams MUST benchmark models against representative tasks before production deployment
2. Teams SHOULD implement model fallback strategies (e.g., GPT-4o-mini -> GPT-4o on failure)
3. Teams MUST monitor per-model costs and performance metrics
4. Teams MUST NOT target the retired o-series models; for latency-sensitive
   reasoning work, teams SHOULD use `gpt-5.6-luna` or a lower `reasoning.effort`
5. Teams MUST use Batch API for non-time-sensitive workloads to reduce costs by 50%

---

## API Patterns

### Authentication

#### API Key Management

Teams MUST follow these security practices[^9]:

```python
# DO: Use environment variables
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)

# DON'T: Hardcode API keys
client = OpenAI(api_key="sk-proj-...")  # NEVER DO THIS
```

**Requirements:**

1. API keys MUST be stored in environment variables or secure secret management systems
2. API keys MUST NOT be committed to version control
3. API keys SHOULD be rotated every 90 days
4. Teams MUST use separate API keys for development, staging, and production
5. Teams SHOULD implement API key rotation without downtime

#### Organization and Project Headers

```python
# Teams SHOULD specify organization and project
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    organization=os.environ.get("OPENAI_ORG_ID"),
    project=os.environ.get("OPENAI_PROJECT_ID")
)
```

### Rate Limits

OpenAI enforces rate limits[^3] based on tokens per minute (TPM) and requests per minute (RPM).

#### Rate Limit Tiers

**Free Tier:**

- GPT-4o: 10,000 TPM, 3 RPM
- GPT-4o-mini: 20,000 TPM, 3 RPM

**Tier 1 ($5+ spent):**

- GPT-4o: 30,000 TPM, 500 RPM
- GPT-4o-mini: 200,000 TPM, 500 RPM

**Tier 2 ($50+ spent):**

- GPT-4o: 450,000 TPM, 5,000 RPM
- GPT-4o-mini: 2,000,000 TPM, 5,000 RPM

**Tier 3 ($100+ spent):**

- GPT-4o: 600,000 TPM, 5,000 RPM
- GPT-4o-mini: 4,000,000 TPM, 5,000 RPM

**Tier 4 ($250+ spent):**

- GPT-4o: 800,000 TPM, 10,000 RPM
- GPT-4o-mini: 10,000,000 TPM, 10,000 RPM

**Tier 5 ($1,000+ spent):**

- GPT-4o: 2,000,000 TPM, 10,000 RPM
- GPT-4o-mini: 30,000,000 TPM, 30,000 RPM

#### Rate Limit Handling

Teams MUST implement exponential backoff with jitter:

```python
import time
import random
from openai import OpenAI, RateLimitError

def call_openai_with_backoff(client, **kwargs):
    """
    Call OpenAI API with exponential backoff.

    Requirements:
    - MUST retry on rate limit errors
    - SHOULD use exponential backoff with jitter
    - MUST NOT exceed maximum retry attempts
    """
    max_retries = 5
    base_delay = 1  # seconds
    max_delay = 60  # seconds

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(**kwargs)
            return response
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise

            # Exponential backoff with jitter
            delay = min(base_delay * (2 ** attempt), max_delay)
            jitter = random.uniform(0, delay * 0.1)
            sleep_time = delay + jitter

            print(f"Rate limit hit. Retrying in {sleep_time:.2f}s...")
            time.sleep(sleep_time)
```

**Requirements:**

1. Teams MUST implement retry logic for rate limit errors (429 status)
2. Teams SHOULD use exponential backoff with jitter
3. Teams MUST respect the `Retry-After` header when provided
4. Teams SHOULD implement request queuing for high-volume applications
5. Teams MUST monitor rate limit usage and adjust tier as needed

### Error Handling

#### Error Types

```python
from openai import (  # OpenAI Python SDK[^10]
    OpenAI,
    APIError,
    APIConnectionError,
    RateLimitError,
    AuthenticationError,
    BadRequestError,
    APITimeoutError
)

def robust_api_call(client, **kwargs):
    """
    Robust OpenAI API call with comprehensive error handling.

    Requirements:
    - MUST handle all documented error types
    - SHOULD log errors with context
    - MUST provide meaningful error messages to users
    """
    try:
        response = client.chat.completions.create(**kwargs)
        return response

    except AuthenticationError as e:
        # Invalid API key or authentication failure
        # MUST NOT retry - requires configuration fix
        log_error("Authentication failed", e)
        raise RuntimeError("API authentication failed. Check credentials.") from e

    except RateLimitError as e:
        # Rate limit exceeded
        # SHOULD retry with backoff
        log_error("Rate limit exceeded", e)
        return call_openai_with_backoff(client, **kwargs)

    except BadRequestError as e:
        # Invalid request parameters
        # MUST NOT retry - requires request modification
        log_error("Invalid request", e)
        raise ValueError(f"Invalid API request: {e}") from e

    except APITimeoutError as e:
        # Request timed out
        # SHOULD retry with exponential backoff
        log_error("Request timeout", e)
        raise TimeoutError("OpenAI API request timed out") from e

    except APIConnectionError as e:
        # Network connection issues
        # SHOULD retry with backoff
        log_error("Connection error", e)
        raise ConnectionError("Failed to connect to OpenAI API") from e

    except APIError as e:
        # General API errors (500, 502, 503, 504)
        # SHOULD retry with backoff
        log_error("API error", e)
        raise RuntimeError(f"OpenAI API error: {e}") from e

def log_error(message, error):
    """Log error with context."""
    # Teams MUST implement structured logging
    print(f"ERROR: {message} - {str(error)}")
```

#### Timeout Configuration

```python
# Teams SHOULD configure appropriate timeouts
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    timeout=30.0,  # 30 second timeout
    max_retries=2  # Built-in retry logic
)

# Per-request timeout override
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}],
    timeout=60.0  # Override for this request
)
```

**Requirements:**

1. Teams MUST set appropriate timeouts based on use case
2. Teams SHOULD use 30-60 second timeouts for standard requests
3. Teams MAY use longer timeouts for complex work on reasoning models such as
   `gpt-6-astra`, which spend time on reasoning tokens before the first
   visible output token
4. Teams MUST handle timeout errors gracefully
5. Teams SHOULD log timeout occurrences for monitoring

### Request Patterns

#### Streaming Responses

Teams SHOULD use streaming[^4] for real-time user interfaces:

```python
def stream_completion(client, messages):
    """
    Stream completion for real-time display.

    Requirements:
    - SHOULD use streaming for chat interfaces
    - MUST handle stream interruption
    - SHOULD provide incremental updates to users
    """
    try:
        stream = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            stream=True
        )

        full_response = ""
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                full_response += content
                yield content  # Send to UI incrementally

        return full_response

    except Exception as e:
        log_error("Streaming error", e)
        raise
```

**Requirements:**

1. Teams SHOULD use streaming for chat interfaces and real-time applications
2. Teams MUST handle stream interruptions gracefully
3. Teams MUST NOT target the retired `o1-preview` and `o1-mini` models; the
   current `gpt-6-astra` and GPT-5.6 models all support streaming
4. Teams SHOULD buffer streamed content for logging and monitoring

#### Batch Requests

Teams SHOULD use Batch API[^5] for non-time-sensitive workloads:

```python
# Batch API provides 50% cost reduction
# Use for:
# - Overnight data processing
# - Bulk classification
# - Large-scale code analysis
# - Report generation

# Create batch file (JSONL format)
batch_requests = [
    {
        "custom_id": "request-1",
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": "Analyze this code..."}]
        }
    },
    {
        "custom_id": "request-2",
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": "Review this function..."}]
        }
    }
]

# Upload batch file
from openai import OpenAI
client = OpenAI()

# Write to JSONL file
with open("batch_requests.jsonl", "w") as f:
    for req in batch_requests:
        f.write(json.dumps(req) + "\n")

# Upload file
batch_input_file = client.files.create(
    file=open("batch_requests.jsonl", "rb"),
    purpose="batch"
)

# Create batch
batch = client.batches.create(
    input_file_id=batch_input_file.id,
    endpoint="/v1/chat/completions",
    completion_window="24h"
)

# Check status
batch_status = client.batches.retrieve(batch.id)
print(batch_status.status)  # validating, in_progress, completed, failed

# Retrieve results when completed
if batch_status.status == "completed":
    result_file_id = batch_status.output_file_id
    results = client.files.content(result_file_id)
```

**Requirements:**

1. Teams MUST use Batch API for workloads that can tolerate 24-hour latency
2. Teams SHOULD use Batch API to reduce costs by 50%
3. Teams MUST implement status polling with appropriate intervals
4. Teams SHOULD batch similar requests together for efficiency
5. Teams MUST handle batch failures and partial completions

---

## System Prompts for Coding

### Effective System Prompts

System prompts[^11] establish the AI's role, constraints, and behavior. For
code generation, they **MUST** be clear, specific, and comprehensive.

#### General Coding Assistant

```python
CODING_SYSTEM_PROMPT = """You are an expert software engineer assistant.

Your responsibilities:
- Write clean, maintainable, production-quality code
- Follow language-specific best practices and idioms
- Include comprehensive error handling
- Add clear comments for complex logic
- Consider edge cases and input validation
- Optimize for readability over cleverness

Code style requirements:
- Use consistent naming conventions (snake_case for Python, camelCase for JavaScript)
- Keep functions focused and single-purpose
- Limit function length to 50 lines when possible
- Include docstrings/JSDoc for all public functions
- Handle errors explicitly, never silently

When generating code:
1. Start with function signature and docstring
2. Implement core logic with error handling
3. Add input validation
4. Include usage examples
5. Note any assumptions or limitations

Never:
- Use deprecated APIs without noting them
- Ignore error conditions
- Generate code with security vulnerabilities
- Skip input validation
- Make assumptions about undefined behavior

If requirements are unclear, ask clarifying questions before generating code."""
```

#### Language-Specific Prompts

**Python:**

```python
PYTHON_SYSTEM_PROMPT = """You are an expert Python engineer following PEP 8 and modern Python best practices.

Requirements:
- Use Python 3.10+ features (match/case, type hints, etc.)
- Follow PEP 8 style guide strictly
- Include comprehensive type hints (typing module)
- Use dataclasses or Pydantic for data structures
- Implement proper exception handling (never bare except)
- Use context managers for resource management
- Prefer pathlib over os.path
- Use f-strings for string formatting

Code structure:
- One class/function per logical responsibility
- Maximum line length: 88 characters (Black formatter)
- Use absolute imports
- Group imports: standard library, third-party, local

Documentation:
- Google-style or NumPy-style docstrings
- Include type information in docstrings
- Document exceptions raised
- Provide usage examples

Testing considerations:
- Write code that's easy to test
- Avoid global state
- Use dependency injection
- Make side effects explicit"""
```

**TypeScript:**

```typescript
TYPESCRIPT_SYSTEM_PROMPT = """You are an expert TypeScript engineer following modern TypeScript and React best practices.

Requirements:
- Use TypeScript 5.0+ features
- Strict mode enabled (strict: true)
- Explicit return types for all functions
- Use interfaces for object shapes, types for unions/intersections
- Prefer const assertions and as const
- Use async/await over Promise chains
- Implement proper error handling with try/catch

Code structure:
- Functional components with hooks (React)
- Custom hooks for reusable logic
- Keep components under 200 lines
- Extract complex logic to utilities
- Use composition over inheritance

Type safety:
- Avoid 'any' type (use 'unknown' if necessary)
- Use generics for reusable components
- Leverage discriminated unions for state
- Use type guards for runtime checks

Modern patterns:
- Optional chaining (?.) and nullish coalescing (??)
- Template literal types where appropriate
- Use readonly for immutable data
- Leverage utility types (Pick, Omit, Partial, etc.)

Documentation:
- TSDoc comments for public APIs
- Inline comments for complex logic
- Document generic parameters
- Note browser compatibility if relevant"""
```

#### Code Review Prompt

```python
CODE_REVIEW_SYSTEM_PROMPT = """You are an expert code reviewer focusing on:

1. Correctness:
   - Logic errors and edge cases
   - Off-by-one errors
   - Null/undefined handling
   - Type safety issues

2. Security:
   - SQL injection vulnerabilities
   - XSS vulnerabilities
   - Authentication/authorization issues
   - Sensitive data exposure
   - Input validation

3. Performance:
   - Inefficient algorithms (O(n²) where O(n) possible)
   - Unnecessary database queries (N+1 problems)
   - Memory leaks
   - Blocking operations

4. Maintainability:
   - Code clarity and readability
   - DRY violations
   - Function/class size
   - Naming conventions
   - Documentation quality

5. Testing:
   - Test coverage gaps
   - Missing edge case tests
   - Brittle tests
   - Test clarity

Format your review as:
- 🔴 Critical: Security issues, bugs, breaking changes
- 🟡 Important: Performance, maintainability, best practices
- 🟢 Minor: Style, suggestions, improvements

For each issue:
1. Describe the problem
2. Explain the impact
3. Suggest a specific fix with code example
4. Provide relevant references (docs, articles)

Be constructive and specific. Praise good patterns."""
```

### Prompt Engineering Patterns

#### Few-Shot Examples

Teams SHOULD include examples for complex or ambiguous tasks:

```python
messages = [
    {
        "role": "system",
        "content": CODING_SYSTEM_PROMPT
    },
    {
        "role": "user",
        "content": "Create a function to validate email addresses."
    },
    {
        "role": "assistant",
        "content": """```python
import re
from typing import Optional

def validate_email(email: str) -> bool:
    \"\"\"
    Validate email address format.

    Args:
        email: Email address to validate

    Returns:
        True if email is valid, False otherwise

    Examples:
        >>> validate_email("user@example.com")
        True
        >>> validate_email("invalid.email")
        False
    \"\"\"
    if not email or not isinstance(email, str):
        return False

    # RFC 5322 simplified pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))
```"""
    },
    {
        "role": "user",
        "content": "Now create a function to validate URLs."
    }
]
```

#### Chain-of-Thought Prompting

For complex problems, teams SHOULD request step-by-step reasoning:

```python
user_prompt = """Create a function to find the longest palindromic substring.

Think through this step-by-step:
1. What algorithm should we use? (Brute force, expand around center, dynamic programming)
2. What's the time/space complexity?
3. What edge cases need handling?
4. How can we optimize?

Then implement the solution with clear comments explaining each step."""
```

#### Constraints and Guardrails

```python
user_prompt = """Create a REST API endpoint for user authentication.

Requirements:
- MUST use bcrypt for password hashing
- MUST implement rate limiting (5 attempts per minute)
- MUST use JWT tokens with 1-hour expiration
- MUST validate input (email format, password strength)
- MUST log authentication attempts
- MUST NOT store passwords in plain text
- SHOULD use environment variables for secrets

Framework: Express.js with TypeScript
Include comprehensive error handling and input validation."""
```

### System Prompt Requirements

1. Teams MUST define clear role and responsibilities
2. Teams SHOULD specify coding standards and style guides
3. Teams MUST include security requirements
4. Teams SHOULD provide examples for complex patterns
5. Teams MUST specify what NOT to do
6. Teams SHOULD include quality criteria (testing, documentation)
7. Teams MAY include language-specific best practices
8. Teams SHOULD be concise (keep under 1000 tokens)

---

## Function Calling

Function calling[^6] allows models to generate structured function calls to external APIs or tools.

### Basic Function Calling

```python
from openai import OpenAI
import json

client = OpenAI()

# Define functions
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_code_metrics",
            "description": "Analyze code file and return complexity metrics including cyclomatic complexity, lines of code, and maintainability index",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the code file to analyze"
                    },
                    "metrics": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["complexity", "loc", "maintainability", "coverage"]
                        },
                        "description": "List of metrics to calculate"
                    }
                },
                "required": ["file_path"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_tests",
            "description": "Execute test suite for specified module or file",
            "parameters": {
                "type": "object",
                "properties": {
                    "test_path": {
                        "type": "string",
                        "description": "Path to test file or directory"
                    },
                    "verbose": {
                        "type": "boolean",
                        "description": "Enable verbose output"
                    }
                },
                "required": ["test_path"],
                "additionalProperties": False
            }
        }
    }
]

# Make request with function calling
messages = [
    {
        "role": "user",
        "content": "Analyze the complexity of src/utils/parser.py and run its tests"
    }
]

response = client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=tools,
    tool_choice="auto"  # Let model decide when to call functions
)

assistant_message = response.choices[0].message

if not assistant_message.tool_calls:
    print(assistant_message.content)
else:
    # Keep the original prompt and the assistant's tool-call message
    messages.append(assistant_message)

    # Execute every returned call and record a result for each tool_call_id
    for tool_call in assistant_message.tool_calls:
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)

        print(f"Calling {function_name} with args: {function_args}")

        try:
            if function_name == "get_code_metrics":
                result = get_code_metrics(**function_args)
            elif function_name == "run_tests":
                result = run_tests(**function_args)
            else:
                raise ValueError(f"Unknown function: {function_name}")
            content = json.dumps(result)
        except (ValueError, TypeError, OSError) as exc:
            # A failed call still owes the model a result for its ID
            content = json.dumps({"error": type(exc).__name__})

        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": content
        })

    # One continuation, carrying a result for every requested call
    final_response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )

    print(final_response.choices[0].message.content)
```

**Requirements:**

1. Teams **MUST** append exactly one tool message for every `tool_call_id`
   present in the assistant message before requesting a continuation
2. Teams **MUST** send a single continuation after the loop, not one request
   per tool call
3. Teams **MUST** preserve the original user message in the continuation
4. Teams **MUST** convert a failed tool call into a tool result rather than
   omitting it

#### Why

A model response can contain zero, one, or several tool calls, so handling code
**MUST** assume there are several. Requesting a continuation inside the loop
sends an assistant message that asks for two calls alongside a single answer,
which leaves the remaining `tool_call_id` unanswered; the loop also sends one
request per call and pays for the whole conversation again each time. See
[handling function calls](https://developers.openai.com/api/docs/guides/function-calling#handling-function-calls).

### Function Definition Best Practices

**Requirements:**

1. Teams MUST provide clear, detailed function descriptions
2. Teams MUST specify all required parameters
3. Teams SHOULD use JSON Schema validation (enums, patterns, ranges)
4. Teams MUST set `additionalProperties: False` to prevent hallucination
5. Teams SHOULD include examples in descriptions for complex parameters

```python
# GOOD: Detailed, validated function definition
{
    "type": "function",
    "function": {
        "name": "create_database_migration",
        "description": "Generate a database migration file for schema changes. Supports adding tables, columns, indexes, and constraints. Migration files follow timestamp naming convention.",
        "parameters": {
            "type": "object",
            "properties": {
                "migration_type": {
                    "type": "string",
                    "enum": ["create_table", "add_column", "add_index", "drop_table"],
                    "description": "Type of migration to generate"
                },
                "table_name": {
                    "type": "string",
                    "pattern": "^[a-z][a-z0-9_]*$",
                    "description": "Table name in snake_case (e.g., 'user_profiles')"
                },
                "columns": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "type": {
                                "type": "string",
                                "enum": ["string", "integer", "boolean", "timestamp", "text"]
                            },
                            "nullable": {"type": "boolean"},
                            "default": {"type": "string"}
                        },
                        "required": ["name", "type"]
                    },
                    "description": "Column definitions for the table"
                }
            },
            "required": ["migration_type", "table_name"],
            "additionalProperties": False
        }
    }
}

# BAD: Vague, unvalidated function definition
{
    "type": "function",
    "function": {
        "name": "do_migration",
        "description": "Create migration",  # Too vague
        "parameters": {
            "type": "object",
            "properties": {
                "data": {"type": "string"}  # No validation
            }
            # Missing: required, additionalProperties
        }
    }
}
```

### Parallel Function Calling

GPT-4o supports calling multiple functions in a single response:

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_file_content",
            "description": "Read content of a source file",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"}
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_codebase",
            "description": "Search for pattern across codebase",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string"},
                    "file_type": {"type": "string"}
                },
                "required": ["pattern"]
            }
        }
    }
]

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "user",
            "content": "Read src/main.py and search for all TODO comments in Python files"
        }
    ],
    tools=tools,
    parallel_tool_calls=True  # Enable parallel calls (default)
)

# Model may call both functions simultaneously
# Handle all tool calls before sending results back
```

### Tool Choice Strategies

```python
# Auto: Let model decide whether to call functions
tool_choice="auto"  # Default, recommended

# Required: Force model to call at least one function
tool_choice="required"  # Use when function call is mandatory

# Specific function: Force model to call specific function
tool_choice={
    "type": "function",
    "function": {"name": "get_code_metrics"}
}

# None: Disable function calling for this request
tool_choice="none"
```

**Requirements:**

1. Teams SHOULD use `tool_choice="auto"` as default
2. Teams MAY use `tool_choice="required"` for validation/extraction tasks
3. Teams MUST handle cases where model doesn't call expected function
4. Teams MUST validate and authorise function arguments before execution
5. Teams MUST handle function execution errors gracefully

### Function Calling Error Handling

Tool arguments are model output, not trusted input. Every registered function
**MUST** be coupled to a typed validator and an authorisation policy that run
before the callable is invoked.

```python
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Literal

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

REPO_ROOT = Path("/srv/app").resolve()


class RunTestsArgs(BaseModel):
    """Typed, closed schema for the run_tests tool."""

    model_config = ConfigDict(extra="forbid", strict=True)

    test_path: str
    verbose: bool = False

    @field_validator("test_path")
    @classmethod
    def within_repository(cls, value: str) -> str:
        """Constrain the tool to paths inside the repository root."""
        candidate = (REPO_ROOT / value).resolve()
        if not candidate.is_relative_to(REPO_ROOT):
            raise ValueError("test_path resolves outside the repository root")
        return str(candidate)


class MigrationArgs(BaseModel):
    """Typed, closed schema for the create_database_migration tool."""

    model_config = ConfigDict(extra="forbid", strict=True)

    migration_type: Literal["create_table", "add_column", "add_index"]
    table_name: str


@dataclass(frozen=True)
class ToolPolicy:
    """Couple one callable to its validator and authorisation rules."""

    args_model: type[BaseModel]
    handler: Callable[..., dict]
    required_scope: str
    needs_approval: bool = False


TOOL_POLICIES = {
    "run_tests": ToolPolicy(
        args_model=RunTestsArgs,
        handler=run_tests,
        required_scope="ci:run_tests"
    ),
    "create_database_migration": ToolPolicy(
        args_model=MigrationArgs,
        handler=create_database_migration,
        required_scope="db:migrate",
        needs_approval=True
    )
}


def dispatch_tool_call(tool_call, principal, approved_call_ids) -> dict:
    """
    Validate, authorise, and execute a single tool call.

    Requirements:
    - MUST reject unknown tools, unknown fields, and mistyped values
    - MUST authorise the caller before execution
    - MUST require explicit approval for consequential actions
    - MUST NOT return raw exception text to the model
    """
    policy = TOOL_POLICIES.get(tool_call.function.name)
    if policy is None:
        return {"tool_call_id": tool_call.id, "error": "unknown_tool"}

    try:
        raw_args = json.loads(tool_call.function.arguments)
    except json.JSONDecodeError:
        return {"tool_call_id": tool_call.id, "error": "invalid_json"}

    try:
        args = policy.args_model.model_validate(raw_args)
    except ValidationError:
        return {"tool_call_id": tool_call.id, "error": "schema_violation"}

    if policy.required_scope not in principal.scopes:
        return {"tool_call_id": tool_call.id, "error": "not_authorised"}

    if policy.needs_approval and tool_call.id not in approved_call_ids:
        return {"tool_call_id": tool_call.id, "error": "approval_required"}

    try:
        result = policy.handler(**args.model_dump())
    except (OSError, RuntimeError, TimeoutError) as exc:
        log_error(f"tool {tool_call.function.name} failed", exc)
        return {"tool_call_id": tool_call.id, "error": "execution_failed"}

    return {"tool_call_id": tool_call.id, "content": json.dumps(result)}


def safe_function_calling(client, messages, tools, principal, approved_call_ids):
    """
    Run one function-calling turn with validation, authorisation, and
    a result for every returned tool call.
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )

    assistant_message = response.choices[0].message
    if not assistant_message.tool_calls:
        return assistant_message.content

    return [
        dispatch_tool_call(tool_call, principal, approved_call_ids)
        for tool_call in assistant_message.tool_calls
    ]
```

**Requirements:**

1. Teams **MUST** validate arguments against a typed model that forbids
   unknown fields and refuses type coercion before execution
2. Teams **MUST** authorise the calling principal for the specific tool, not
   only for the conversation
3. Teams **MUST** constrain filesystem, network, and database scope inside the
   validator rather than inside the tool implementation
4. Teams **MUST** require explicit human approval for consequential actions
   such as migrations, refunds, deletions, and outbound messages
5. Teams **MUST NOT** return raw exception text or stack traces to the model
6. Teams **MUST NOT** treat `strict: true` or `additionalProperties: false` as
   a substitute for application-side validation and authorisation

#### Why

Parsing JSON and finding the function name in a registry is not schema
validation. The previous helper claimed to "validate function arguments against
schema" while forwarding whatever the model produced straight into
`AVAILABLE_FUNCTIONS[name](**args)`: with two harmless-looking tool definitions
it accepted and executed
`{"test_path": "../../secrets", "verbose": "not-a-boolean", "unexpected": true}`.
Strict mode constrains the model's output to the declared schema, but it is a
generation-time guarantee, not an authorisation boundary, and it says nothing
about whether this caller may run this action on this path. See
[strict mode](https://developers.openai.com/api/docs/guides/function-calling#strict-mode)
and [agent safety](https://developers.openai.com/api/docs/guides/agent-builder-safety).

---

## Structured Outputs

Structured Outputs[^7] guarantee the model's response matches a specified JSON
schema. This is more reliable than function calling for pure data extraction.

### Basic Structured Output

```python
from openai import OpenAI
from pydantic import BaseModel  # Pydantic for schema validation[^12]

client = OpenAI()

# Define schema using Pydantic
class CodeAnalysis(BaseModel):
    language: str
    functions: list[str]
    complexity: str  # "low", "medium", "high"
    issues: list[str]
    suggestions: list[str]

response = client.beta.chat.completions.parse(
    model="gpt-4o",
    messages=[
        {
            "role": "system",
            "content": "You are a code analysis expert. Analyze code and return structured results."
        },
        {
            "role": "user",
            "content": """Analyze this code:

def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
"""
        }
    ],
    response_format=CodeAnalysis
)

# A parsed model exists only when the model neither refused nor stopped early
message = response.choices[0].message

if message.refusal:
    print(f"Request refused: {message.refusal}")
elif message.parsed is None:
    print("No parsed output returned")
else:
    analysis = message.parsed
    print(f"Language: {analysis.language}")
    print(f"Functions: {analysis.functions}")
    print(f"Complexity: {analysis.complexity}")
```

`message.parsed` is `None` whenever the model returns a refusal, so
dereferencing it unconditionally raises
`AttributeError: 'NoneType' object has no attribute 'language'` the first time
a request trips the content policy.

### Complex Nested Schemas

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class FunctionMetrics(BaseModel):
    name: str
    lines_of_code: int
    cyclomatic_complexity: int
    parameters: int
    returns: Optional[str]
    docstring_present: bool

class SecurityIssue(BaseModel):
    severity: Literal["critical", "high", "medium", "low"]
    category: Literal["injection", "xss", "auth", "crypto", "other"]
    line_number: int
    description: str
    remediation: str

class ComprehensiveCodeAnalysis(BaseModel):
    file_path: str
    language: str
    total_lines: int
    total_functions: int
    functions: List[FunctionMetrics]
    security_issues: List[SecurityIssue]
    code_smells: List[str]
    test_coverage_estimate: int = Field(ge=0, le=100)
    maintainability_score: Literal["A", "B", "C", "D", "F"]
    recommendations: List[str]

response = client.beta.chat.completions.parse(
    model="gpt-4o",
    messages=[
        {
            "role": "system",
            "content": "You are an expert code auditor. Provide comprehensive analysis."
        },
        {
            "role": "user",
            "content": f"Analyze this file:\n\n{code_content}"
        }
    ],
    response_format=ComprehensiveCodeAnalysis
)

analysis = response.choices[0].message.parsed
```

### Structured Output vs Function Calling

**Use Structured Outputs when:**

- Extracting data from text (parsing, analysis)
- Generating formatted reports
- Converting unstructured to structured data
- Schema validation is critical
- No external function execution needed

**Use Function Calling when:**

- Calling external APIs or tools
- Executing code or commands
- Multi-step workflows requiring decisions
- Interactive tool use
- Dynamic function selection

```python
# GOOD: Use Structured Output for data extraction
class BugReport(BaseModel):
    title: str
    severity: Literal["critical", "high", "medium", "low"]
    steps_to_reproduce: List[str]
    expected_behavior: str
    actual_behavior: str

response = client.beta.chat.completions.parse(
    model="gpt-4o",
    messages=[{"role": "user", "content": user_bug_description}],
    response_format=BugReport
)

# GOOD: Use Function Calling for tool execution
tools = [{
    "type": "function",
    "function": {
        "name": "create_jira_ticket",
        "description": "Create a new Jira ticket",
        "parameters": {...}
    }
}]

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Create a ticket for this bug"}],
    tools=tools
)
```

### Requirements for Structured Outputs

1. Teams MUST use Pydantic models or JSON Schema for schema definition
2. Teams SHOULD use Literal types for constrained string values
3. Teams MUST handle `refusal` field when content policy is triggered
4. Teams SHOULD use Field validators for numeric constraints
5. Teams MUST NOT use recursive schemas (not supported)
6. Teams SHOULD keep schemas under 20 nested levels
7. Teams MUST use `additionalProperties: false` to prevent extra fields

### Error Handling with Structured Outputs

```python
from openai import LengthFinishReasonError


class IncompleteStructuredOutput(RuntimeError):
    """Raised when a parse request produced no schema-valid result."""


def parse_with_schema(client, messages, schema, max_tokens=2048, retries=1):
    """
    Parse a completion into `schema`, or fail explicitly.

    Requirements:
    - MUST return a refusal as a result rather than crashing
    - MUST treat a length-limited completion as incomplete, never as data
    - MUST bound the number of retries
    """
    for attempt in range(retries + 1):
        try:
            response = client.beta.chat.completions.parse(
                model="gpt-4o",
                messages=messages,
                response_format=schema,
                max_tokens=max_tokens
            )
        except LengthFinishReasonError as exc:
            if attempt == retries:
                raise IncompleteStructuredOutput(
                    f"output truncated at max_tokens={max_tokens}"
                ) from exc
            max_tokens *= 2
            continue

        message = response.choices[0].message

        if message.refusal:
            return {"refusal": message.refusal}

        if message.parsed is None:
            raise IncompleteStructuredOutput("no parsed output returned")

        return message.parsed

    raise IncompleteStructuredOutput("retries exhausted")
```

**Requirements:**

1. Teams **MUST** check `refusal` and `parsed is None` before using a parsed
   model
2. Teams **MUST NOT** read `parsed` from the completion carried by
   `LengthFinishReasonError`
3. Teams **MUST** raise or return an explicit error when output is truncated
4. Teams **MUST** keep `return` statements inside a function

#### Why

The SDK raises `LengthFinishReasonError` from the parsing helper *before* it
builds any parsed choice, so the completion attached to the exception is a raw
`ChatCompletion`: reading `e.completion.choices[0].message.parsed` raises
`AttributeError: 'ChatCompletionMessage' object has no attribute 'parsed'`.
Even with the correct attribute, a non-streaming completion cut off at
`max_tokens` holds truncated JSON, so treating it as validated partial data
feeds a half-written record into the caller. Retry with a larger budget, or
surface the failure.

---

## Cost Optimization

### Token Management

#### Token Counting

Teams MUST monitor token usage to control costs:

```python
import tiktoken  # OpenAI's tokenizer library[^8]

def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """
    Count tokens in text for given model.

    Requirements:
    - MUST use correct encoding for model
    - SHOULD cache encoding object for performance
    """
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

def count_messages_tokens(messages: list, model: str = "gpt-4o") -> int:
    """
    Count tokens in message list including formatting overhead.

    OpenAI message formatting adds:
    - 3 tokens per message
    - 1 token per message for role
    - 2 tokens per message for formatting
    """
    encoding = tiktoken.encoding_for_model(model)
    num_tokens = 0

    for message in messages:
        num_tokens += 4  # Message formatting overhead
        for key, value in message.items():
            num_tokens += len(encoding.encode(str(value)))

    num_tokens += 2  # Conversation start/end
    return num_tokens

# Example usage
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Explain quantum computing"}
]

total_tokens = count_messages_tokens(messages)
print(f"Estimated cost: ${total_tokens * 2.50 / 1_000_000:.6f}")
```

#### Context Window Management

**Requirements:**

1. Teams MUST track cumulative token usage in conversations
2. Teams SHOULD implement context truncation strategies
3. Teams MUST NOT exceed model context limits
4. Teams SHOULD prioritize recent messages over older ones

```python
class ContextOverflowError(RuntimeError):
    """Raised when mandatory context alone exceeds the input budget."""


class ConversationManager:
    """
    Manage conversation context within an enforced token budget.

    Requirements:
    - MUST keep the system message and the newest message
    - MUST drop older turns before the budget is exceeded
    - MUST NOT return a conversation that exceeds the budget
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        context_window: int = 128_000,
        reserved_output_tokens: int = 16_384
    ):
        self.model = model
        self.input_budget = context_window - reserved_output_tokens
        self.system_message = None
        self.messages = []

    def add_message(self, role: str, content: str):
        """Add a message and re-establish the budget invariant."""
        self.messages.append({"role": role, "content": content})
        self._enforce_budget()

    def _enforce_budget(self):
        """Drop the oldest turns until the conversation fits, or fail."""
        while self.total_tokens() > self.input_budget:
            # The system message and the newest message are mandatory
            if len(self.messages) <= 1:
                raise ContextOverflowError(
                    f"{self.total_tokens()} tokens exceed the "
                    f"{self.input_budget}-token input budget for {self.model}; "
                    "compact or summarise the conversation before retrying"
                )

            # Remove oldest user-assistant pair
            self.messages.pop(0)
            if self.messages and self.messages[0]["role"] == "assistant":
                self.messages.pop(0)

    def total_tokens(self) -> int:
        """Count tokens across the system message and history."""
        return count_messages_tokens(self.get_messages(), self.model)

    def get_messages(self):
        """Get messages with system prompt."""
        if self.system_message:
            return [self.system_message] + self.messages
        return self.messages
```

**Requirements:**

1. Teams **MUST** derive the input budget from the model's context window minus
   the output tokens the request may actually generate
2. Teams **MUST** reserve at least 25,000 tokens for reasoning models, which
   spend reasoning tokens from the same window
3. Teams **MUST** raise an explicit error when the mandatory content alone
   exceeds the budget, rather than returning an oversized message list
4. Teams **SHOULD** compact or summarise long conversations instead of
   truncating them; the Responses API can compact server-side when the rendered
   token count crosses `compact_threshold`

##### Why

A guard that stops enforcing its own limit is worse than no guard, because
callers trust it. The previous loop broke out as soon as four messages
remained, whatever their size: four 40,000-token messages returned a 160,000
token conversation against a 96,000-token allowance, and a single oversized
mandatory message was enough on its own. The request then fails at the API with
a context-length error that the guard was meant to prevent. See
[compaction](https://developers.openai.com/api/docs/guides/compaction.md) and
[managing the context window](https://developers.openai.com/api/docs/guides/reasoning#managing-the-context-window).

### Model Selection for Cost

```python
class CostOptimizer:
    """
    Select optimal model based on task complexity and cost.

    Requirements:
    - SHOULD use GPT-4o-mini for simple tasks
    - SHOULD use GPT-4o for complex reasoning
    - MUST track actual costs
    """

    COSTS = {
        "gpt-4o": {"input": 2.50, "output": 10.00},  # per 1M tokens
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    }

    def select_model(self, task_complexity: str) -> str:
        """Select model based on task complexity."""
        complexity_map = {
            "simple": "gpt-4o-mini",     # Syntax, formatting, simple Q&A
            "moderate": "gpt-4o-mini",   # Standard code generation
            "complex": "gpt-4o",          # Architecture, review, refactoring
            "critical": "gpt-4o"          # Security, production code
        }
        return complexity_map.get(task_complexity, "gpt-4o")

    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        """Calculate estimated cost for request."""
        costs = self.COSTS[model]
        input_cost = (input_tokens / 1_000_000) * costs["input"]
        output_cost = (output_tokens / 1_000_000) * costs["output"]
        return input_cost + output_cost

    def should_use_mini(self, prompt: str) -> bool:
        """
        Determine if task is suitable for GPT-4o-mini.

        Use mini for:
        - Simple completions (< 100 tokens output)
        - Formatting/style fixes
        - Boilerplate generation
        - Simple Q&A
        """
        mini_keywords = [
            "format", "style", "fix typo", "add comment",
            "boilerplate", "scaffold", "simple", "basic"
        ]
        return any(keyword in prompt.lower() for keyword in mini_keywords)
```

### Response Optimization

**Requirements:**

1. Teams SHOULD set appropriate `max_tokens` limits
2. Teams SHOULD use `stop` sequences to terminate early
3. Teams MAY use `temperature=0` for deterministic outputs
4. Teams SHOULD request concise responses when appropriate

```python
# Request concise responses
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {
            "role": "system",
            "content": "Be concise. Provide code without lengthy explanations unless asked."
        },
        {
            "role": "user",
            "content": "Create a function to validate email addresses"
        }
    ],
    max_tokens=500,  # Limit output length
    temperature=0,    # Deterministic output
    stop=["\n\n\n"]  # Stop at triple newline
)
```

### Caching Strategies

Teams SHOULD implement response caching for repeated queries:

```python
import hashlib
import json
from datetime import datetime, timedelta

class ResponseCache:
    """
    Cache OpenAI responses to reduce costs.

    Requirements:
    - SHOULD cache identical requests
    - MUST invalidate stale cache entries
    - SHOULD NOT cache user-specific data
    """

    def __init__(self, ttl_hours: int = 24):
        self.cache = {}
        self.ttl = timedelta(hours=ttl_hours)

    def _hash_request(self, messages: list, model: str) -> str:
        """Create hash of request for cache key."""
        key_data = {
            "messages": messages,
            "model": model
        }
        return hashlib.sha256(
            json.dumps(key_data, sort_keys=True).encode()
        ).hexdigest()

    def get(self, messages: list, model: str):
        """Get cached response if available and fresh."""
        cache_key = self._hash_request(messages, model)

        if cache_key in self.cache:
            entry = self.cache[cache_key]
            if datetime.now() - entry["timestamp"] < self.ttl:
                return entry["response"]
            else:
                del self.cache[cache_key]

        return None

    def set(self, messages: list, model: str, response):
        """Cache response."""
        cache_key = self._hash_request(messages, model)
        self.cache[cache_key] = {
            "response": response,
            "timestamp": datetime.now()
        }

# Usage
cache = ResponseCache(ttl_hours=24)

def get_completion_with_cache(client, messages, model="gpt-4o"):
    # Check cache first
    cached = cache.get(messages, model)
    if cached:
        print("Cache hit!")
        return cached

    # Make API call
    response = client.chat.completions.create(
        model=model,
        messages=messages
    )

    # Cache response
    cache.set(messages, model, response)
    return response
```

### Batch Processing for Cost Reduction

```python
def process_bulk_analysis(files: list[str], use_batch: bool = True):
    """
    Process multiple files efficiently.

    Requirements:
    - SHOULD use Batch API when possible (50% cost reduction)
    - MUST handle batch failures gracefully
    - SHOULD provide progress updates
    """
    if use_batch and len(files) > 10:
        # Use Batch API for 50% cost savings
        return process_with_batch_api(files)
    else:
        # Use standard API for immediate results
        return process_with_standard_api(files)

def process_with_batch_api(files: list[str]):
    """Process files using Batch API (50% cheaper)."""
    client = OpenAI()

    # Create batch requests
    batch_requests = []
    for i, file_path in enumerate(files):
        with open(file_path) as f:
            content = f.read()

        batch_requests.append({
            "custom_id": f"file-{i}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "user",
                        "content": f"Analyze this code:\n\n{content}"
                    }
                ]
            }
        })

    # Write batch file
    with open("batch.jsonl", "w") as f:
        for req in batch_requests:
            f.write(json.dumps(req) + "\n")

    # Upload and create batch
    batch_file = client.files.create(
        file=open("batch.jsonl", "rb"),
        purpose="batch"
    )

    batch = client.batches.create(
        input_file_id=batch_file.id,
        endpoint="/v1/chat/completions",
        completion_window="24h"
    )

    print(f"Batch created: {batch.id}")
    print("Results will be available within 24 hours")
    print(f"Cost savings: ~50% vs standard API")

    return batch.id
```

### Cost Monitoring

```python
class CostTracker:
    """
    Track and report API costs.

    Requirements:
    - MUST track all API calls
    - SHOULD alert on budget thresholds
    - MUST provide cost breakdowns
    """

    def __init__(self, budget_limit: float = 100.0):
        self.calls = []
        self.budget_limit = budget_limit

    def track_call(self, model: str, input_tokens: int, output_tokens: int):
        """Track API call costs."""
        optimizer = CostOptimizer()
        cost = optimizer.estimate_cost(input_tokens, output_tokens, model)

        self.calls.append({
            "timestamp": datetime.now(),
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": cost
        })

        if self.get_total_cost() > self.budget_limit:
            self._alert_budget_exceeded()

    def get_total_cost(self) -> float:
        """Get total cost across all calls."""
        return sum(call["cost"] for call in self.calls)

    def get_breakdown(self) -> dict:
        """Get cost breakdown by model."""
        breakdown = {}
        for call in self.calls:
            model = call["model"]
            if model not in breakdown:
                breakdown[model] = {"calls": 0, "cost": 0.0, "tokens": 0}

            breakdown[model]["calls"] += 1
            breakdown[model]["cost"] += call["cost"]
            breakdown[model]["tokens"] += call["input_tokens"] + call["output_tokens"]

        return breakdown

    def _alert_budget_exceeded(self):
        """Alert when budget is exceeded."""
        print(f"WARNING: Budget exceeded! Total: ${self.get_total_cost():.2f}")
```

---

## Common Pitfalls

### 1. Not Handling Rate Limits

**Problem:** Making requests without retry logic leads to failures during high usage.

**Solution:**

```python
# BAD: No retry logic
response = client.chat.completions.create(...)  # Fails on 429

# GOOD: Exponential backoff with retries
response = call_openai_with_backoff(client, ...)
```

### 2. Ignoring Token Limits

**Problem:** Exceeding context window causes truncated responses or errors.

**Solution:**

```python
# BAD: No token tracking
messages.append(new_message)  # May exceed limit

# GOOD: Track and truncate
if count_messages_tokens(messages) > MAX_TOKENS:
    truncate_old_messages(messages)
messages.append(new_message)
```

### 3. Hardcoded API Keys

**Problem:** Committing API keys to version control exposes credentials.

**Solution:**

```python
# BAD: Hardcoded
client = OpenAI(api_key="sk-proj-...")

# GOOD: Environment variables
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
```

### 4. No Error Handling

**Problem:** Unhandled exceptions crash applications.

**Solution:**

```python
# BAD: No error handling
response = client.chat.completions.create(...)

# GOOD: Comprehensive error handling
try:
    response = client.chat.completions.create(...)
except RateLimitError:
    response = call_openai_with_backoff(client, **kwargs)
except APIError as exc:
    log_error("API error", exc)
    raise
```

### 5. Using Wrong Model for Task

**Problem:** Using expensive models for simple tasks wastes money.

**Solution:**

```python
# BAD: GPT-4o for simple formatting
response = client.chat.completions.create(
    model="gpt-4o",  # $2.50/1M input tokens
    messages=[{"role": "user", "content": "Format this JSON"}]
)

# GOOD: GPT-4o-mini for simple tasks
response = client.chat.completions.create(
    model="gpt-4o-mini",  # $0.15/1M input tokens (16x cheaper)
    messages=[{"role": "user", "content": "Format this JSON"}]
)
```

### 6. Vague Function Descriptions

**Problem:** Poor function definitions lead to incorrect function calls.

**Solution:**

```python
# BAD: Vague function definition
{
    "name": "get_data",
    "description": "Gets data",
    "parameters": {"type": "object", "properties": {}}
}

# GOOD: Detailed function definition
{
    "name": "get_user_profile",
    "description": "Retrieve user profile data including name, email, and preferences by user ID",
    "parameters": {
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "pattern": "^[0-9a-f]{24}$",
                "description": "MongoDB ObjectId of the user (24 hex characters)"
            }
        },
        "required": ["user_id"],
        "additionalProperties": False
    }
}
```

### 7. Not Validating Function Arguments

**Problem:** Executing untrusted function arguments can cause errors or security issues.

**Solution:**

```python
# BAD: Direct execution
args = json.loads(tool_call.function.arguments)
result = execute_function(**args)  # No validation

# GOOD: Validate, authorise, then execute
args = ToolArgs.model_validate_json(tool_call.function.arguments)
if not principal.may_call(tool_call.function.name, args):
    raise PermissionError("caller not authorised for this tool")
result = execute_function(**args.model_dump())
```

### 8. Excessive System Prompts

**Problem:** Very long system prompts waste tokens and increase costs.

**Solution:**

```python
# BAD: 2000-token system prompt for simple task
system_prompt = """[Very long prompt with unnecessary details...]"""

# GOOD: Concise, focused system prompt
system_prompt = """You are a Python expert. Write clean, PEP 8 compliant code with type hints."""
```

### 9. Not Using Streaming for Long Responses

**Problem:** Users wait for entire response before seeing anything.

**Solution:**

```python
# BAD: No streaming for chat UI
response = client.chat.completions.create(...)
display(response.choices[0].message.content)  # Users wait 10+ seconds

# GOOD: Stream for real-time updates
stream = client.chat.completions.create(..., stream=True)
for chunk in stream:
    if chunk.choices[0].delta.content:
        display_incremental(chunk.choices[0].delta.content)
```

### 10. Missing Cost Monitoring

**Problem:** No visibility into API costs leads to budget overruns.

**Solution:**

```python
# BAD: No cost tracking
client.chat.completions.create(...)

# GOOD: Track every call
tracker = CostTracker(budget_limit=100.0)
response = client.chat.completions.create(...)
tracker.track_call(
    model="gpt-4o",
    input_tokens=response.usage.prompt_tokens,
    output_tokens=response.usage.completion_tokens
)
```

### 11. Not Setting max_tokens

**Problem:** Runaway responses waste tokens and increase costs.

**Solution:**

```python
# BAD: No token limit
response = client.chat.completions.create(...)  # May generate 16K tokens

# GOOD: Set appropriate limit
response = client.chat.completions.create(
    ...,
    max_tokens=500  # Limit based on expected output
)
```

### 12. Ignoring Temperature Settings

**Problem:** Using default temperature for tasks requiring consistency.

**Solution:**

```python
# BAD: Random temperature for code generation
response = client.chat.completions.create(...)  # temperature=1.0 default

# GOOD: temperature=0 for deterministic code
response = client.chat.completions.create(
    ...,
    temperature=0  # Deterministic output
)
```

---

## Do/Don't Examples

### API Usage

```python
# DON'T: Store API key in code
api_key = "sk-proj-abc123..."
client = OpenAI(api_key=api_key)

# DO: Use environment variables
import os
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
```

```python
# DON'T: Ignore errors
response = client.chat.completions.create(...)

# DO: Handle all error types
try:
    response = client.chat.completions.create(...)
except RateLimitError:
    response = retry_with_backoff()
except APIError as e:
    log_error(e)
    raise
```

```python
# DON'T: Make blocking calls without timeout
response = client.chat.completions.create(...)

# DO: Set appropriate timeout
response = client.chat.completions.create(
    ...,
    timeout=30.0
)
```

### Model Selection

```python
# DON'T: Use GPT-4o for everything
def process_request(prompt):
    return client.chat.completions.create(
        model="gpt-4o",  # Expensive for simple tasks
        messages=[{"role": "user", "content": prompt}]
    )

# DO: Choose model based on complexity
def process_request(prompt, complexity="simple"):
    model = "gpt-4o-mini" if complexity == "simple" else "gpt-4o"
    return client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
```

```python
# DON'T: Send tool calls to a retired reasoning model
response = client.chat.completions.create(
    model="o1-preview",  # Shut down on 2025-07-28
    messages=messages,
    tools=tools
)

# DO: Use a current reasoning model
response = client.chat.completions.create(
    model="gpt-5.6-sol",
    messages=messages,
    tools=tools
)

# DO: Use the Responses API when the model is gpt-6-astra
response = client.responses.create(
    model="gpt-6-astra",  # Chat Completions cannot call tools here
    input=messages,
    tools=responses_tools
)
```

### System Prompts

```python
# DON'T: Vague system prompts
system = "You are helpful."

# DO: Specific, detailed system prompts
system = """You are an expert Python engineer.

Requirements:
- Write PEP 8 compliant code
- Include type hints
- Add docstrings for all functions
- Handle errors explicitly
- Optimize for readability

When writing code:
1. Start with function signature
2. Add comprehensive docstring
3. Implement with error handling
4. Include usage example"""
```

```python
# DON'T: Excessively long system prompts
system = """[5000 words of instructions...]"""  # Wastes tokens

# DO: Concise, focused instructions
system = """Expert TypeScript engineer. Write type-safe, modern TS code following React best practices. Use functional components and hooks."""
```

### Function Calling

```python
# DON'T: Unvalidated function definitions
{
    "name": "do_thing",
    "description": "Does a thing",
    "parameters": {
        "type": "object",
        "properties": {
            "data": {"type": "string"}
        }
    }
}

# DO: Detailed, validated function definitions
{
    "name": "create_user",
    "description": "Create a new user account with validated email and strong password",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "pattern": "^[^@]+@[^@]+\\.[^@]+$",
                "description": "Valid email address"
            },
            "password": {
                "type": "string",
                "minLength": 12,
                "description": "Password (min 12 characters)"
            }
        },
        "required": ["email", "password"],
        "additionalProperties": False
    }
}
```

```python
# DON'T: Execute function arguments blindly
args = json.loads(tool_call.function.arguments)
result = eval(args["code"])  # DANGEROUS!

# DO: Validate against a closed schema, then authorise the action
args = RunTestsArgs.model_validate_json(tool_call.function.arguments)
if "ci:run_tests" not in principal.scopes:
    raise PermissionError("caller not authorised for run_tests")
result = run_tests(**args.model_dump())
```

### Token Management

```python
# DON'T: Ignore token counts
messages.append(new_message)
response = client.chat.completions.create(messages=messages)

# DO: Track and manage tokens
token_count = count_messages_tokens(messages)
if token_count > 100000:
    messages = truncate_messages(messages, max_tokens=80000)
messages.append(new_message)
response = client.chat.completions.create(messages=messages)
```

```python
# DON'T: Let responses run unbounded
response = client.chat.completions.create(...)

# DO: Set max_tokens based on use case
response = client.chat.completions.create(
    ...,
    max_tokens=500  # Appropriate for expected output
)
```

### Cost Optimization

```python
# DON'T: Skip caching for repeated requests
def get_response(prompt):
    return client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )

# DO: Cache on the same messages and model the request uses
cache = ResponseCache()

def get_response(prompt, model="gpt-4o"):
    messages = [{"role": "user", "content": prompt}]

    cached = cache.get(messages, model)
    if cached:
        return cached

    response = client.chat.completions.create(
        model=model,
        messages=messages
    )
    cache.set(messages, model, response)
    return response
```

`ResponseCache.get()` and `ResponseCache.set()` key on the message list and the
model, because the same prompt returns different output from a different model.
Passing the bare prompt raises
`TypeError: ResponseCache.get() missing 1 required positional argument: 'model'`
on the first call.

```python
# DON'T: Use standard API for bulk processing
for file in files:
    process_file(file)  # Expensive

# DO: Use Batch API for 50% savings
create_batch_job(files)  # 50% cheaper
```

### Streaming

```python
# DON'T: Wait for full response in UI
response = client.chat.completions.create(...)
display(response.choices[0].message.content)

# DO: Stream for better UX
stream = client.chat.completions.create(..., stream=True)
for chunk in stream:
    if chunk.choices[0].delta.content:
        display_incremental(chunk.choices[0].delta.content)
```

### Structured Outputs

```python
# DON'T: Parse JSON from text response
response = client.chat.completions.create(
    messages=[{
        "role": "user",
        "content": "Return JSON with name and age"
    }]
)
data = json.loads(response.choices[0].message.content)  # May fail

# DO: Use Structured Outputs
class Person(BaseModel):
    name: str
    age: int

response = client.beta.chat.completions.parse(
    ...,
    response_format=Person
)
data = response.choices[0].message.parsed  # Guaranteed valid
```

### Temperature Settings

```python
# DON'T: Use high temperature for code generation
response = client.chat.completions.create(
    ...,
    temperature=1.5  # Too creative for code
)

# DO: Use temperature=0 for deterministic code
response = client.chat.completions.create(
    ...,
    temperature=0  # Consistent, reliable code
)
```

```python
# DON'T: Use temperature=0 for brainstorming
response = client.chat.completions.create(
    temperature=0,  # Too rigid for creative tasks
    messages=[{"role": "user", "content": "Brainstorm feature ideas"}]
)

# DO: Use higher temperature for creative tasks
response = client.chat.completions.create(
    temperature=0.8,  # More creative, varied responses
    messages=[{"role": "user", "content": "Brainstorm feature ideas"}]
)
```

---

## References

This section contains all footnoted references to OpenAI documentation and
external resources cited throughout this guide.

### Footnotes

[^1]: **OpenAI Models**: Comprehensive information about available models, capabilities, and specifications.

    - [Model Documentation](https://platform.openai.com/docs/models)
    - [GPT-4 and GPT-4 Turbo](https://platform.openai.com/docs/models/gpt-4-and-gpt-4-turbo)
    - [GPT-3.5](https://platform.openai.com/docs/models/gpt-3-5)

[^2]: **OpenAI Pricing**: Current pricing information for all models including input/output tokens and batch API rates.

    - [Official Pricing Page](https://openai.com/api/pricing/)
    - [Pricing FAQ](https://help.openai.com/en/articles/7127956-how-much-does-gpt-4-cost)

[^3]: **Rate Limits**: Documentation on rate limiting, usage tiers, and how to handle rate limit errors.

    - [Rate Limits Guide](https://platform.openai.com/docs/guides/rate-limits)
    - [Rate Limit Error Handling](https://platform.openai.com/docs/guides/rate-limits/error-mitigation)
    - [Usage Tiers](https://platform.openai.com/docs/guides/rate-limits/usage-tiers)

[^4]: **Streaming**: Documentation on streaming API responses for real-time user experiences.

    - [Streaming Guide](https://platform.openai.com/docs/api-reference/streaming)
    - [Chat Completions Streaming](https://platform.openai.com/docs/api-reference/chat/create#chat-create-stream)

[^5]: **Batch API**: Documentation for the Batch API which offers 50% cost savings for asynchronous workloads.

    - [Batch API Guide](https://platform.openai.com/docs/guides/batch)
    - [Batch API Reference](https://platform.openai.com/docs/api-reference/batch)

[^6]: **Function Calling**: Comprehensive guide to function calling for tool use and structured outputs.

    - [Function Calling Guide](https://platform.openai.com/docs/guides/function-calling)
    - [Function Calling API Reference](https://platform.openai.com/docs/api-reference/chat/create#chat-create-tools)
    - [Function Calling Examples](https://cookbook.openai.com/examples/how_to_call_functions_with_chat_models)

[^7]: **Structured Outputs**: Documentation on guaranteed JSON schema compliance
    in API responses. See
    [Structured Outputs Guide](https://platform.openai.com/docs/guides/structured-outputs)
    and [JSON Mode](https://platform.openai.com/docs/guides/text-generation/json-mode).

[^9]: **API Authentication and Security**: Best practices for securing API keys
    and managing authentication. See
    [API Keys Documentation](https://platform.openai.com/docs/api-reference/authentication)
    and [Best Practices for API Key Safety](https://help.openai.com/en/articles/5112595-best-practices-for-api-key-safety).

[^11]: **Prompt Engineering and System Prompts**: Techniques for crafting
    effective prompts and system messages. See
    [Prompt Engineering Guide](https://platform.openai.com/docs/guides/prompt-engineering)
    and [Best Practices for Prompting](https://help.openai.com/en/articles/6654000-best-practices-for-prompt-engineering-with-openai-api).

### Additional Official Documentation

- [OpenAI API Reference](https://platform.openai.com/docs/api-reference) - Complete API documentation
- [OpenAI Cookbook](https://cookbook.openai.com/) - Code examples and guides
- [OpenAI Python SDK](https://github.com/openai/openai-python) - Official Python library
- [Safety Best Practices](https://platform.openai.com/docs/guides/safety-best-practices) -
  Security and safety guidelines
- [Production Best Practices](https://platform.openai.com/docs/guides/production-best-practices) -
  Production deployment guidelines

### Model Information

- [GPT-4o System Card](https://openai.com/research/gpt-4o-system-card) -
  Technical details and safety analysis
- [Model Deprecation Policy](https://platform.openai.com/docs/deprecations) -
  Model lifecycle information

### External Resources

- [Pydantic](https://docs.pydantic.dev/) - Data validation library for Structured Outputs
- [Prompt Engineering Guide](https://www.promptingguide.ai/) -
  Comprehensive prompt engineering techniques
- [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119) -
  Key words for use in RFCs to indicate requirement levels

---

## Version History

| Version | Date       | Changes                                     |
| ------- | ---------- | ------------------------------------------- |
| 1.0.0   | 2025-12-07 | Initial release with comprehensive coverage |

---

**Maintained by:** Engineering Team
**Last Review:** 2025-12-07
**Next Review:** 2025-03-07
