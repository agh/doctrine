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

```python
# Teams MUST use GPT-4o for:
- Code reviews requiring deep analysis
- Complex refactoring tasks
- Multi-file code generation
- Architectural decisions

# Teams SHOULD use GPT-4o for:
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

```python
# Teams MUST use GPT-4o-mini for:
- High-volume, low-complexity tasks
- Prototype development
- Cost-sensitive applications

# Teams SHOULD use GPT-4o-mini for:
- Simple CRUD operations
- Boilerplate generation
- Unit test scaffolding
```

#### o1-preview and o1-mini

**Use Cases:**

- Advanced reasoning tasks
- Complex problem-solving
- Mathematical computations
- Research and analysis

**Specifications (o1-preview):**

- Context window: 128,000 tokens
- Max output: 32,768 tokens
- Reasoning tokens: Internal (not visible)
- Training data: Up to October 2023

**Pricing (o1-preview)[^2]:**

- Input: $15.00 per 1M tokens
- Output: $60.00 per 1M tokens

**Pricing (o1-mini)[^2]:**

- Input: $3.00 per 1M tokens
- Output: $12.00 per 1M tokens

**Limitations:**

- No system messages support
- No streaming
- No function calling (as of December 2025)
- No temperature control
- Higher latency due to reasoning process

**Requirements:**

```python
# Teams SHOULD use o1-preview for:
- Complex algorithmic challenges
- Multi-step mathematical problems
- Deep code analysis requiring extended reasoning

# Teams MUST NOT use o1 models for:
- Real-time applications (high latency)
- Function calling scenarios
- Applications requiring streaming
```

### Model Selection Decision Tree

```text
START
  |
  +-- Need function calling? ----YES----> GPT-4o or GPT-4o-mini
  |                                        |
  NO                                       |
  |                                        +-- Complex reasoning? --YES--> GPT-4o
  |                                        |
  +-- Complex reasoning/math? --YES-----> o1-preview/o1-mini
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
4. Teams SHOULD NOT use o1 models for latency-sensitive applications
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
3. Teams MAY use longer timeouts for complex reasoning tasks with o1 models
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
3. Teams MUST NOT use streaming with o1 models (not supported)
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
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "user",
            "content": "Analyze the complexity of src/utils/parser.py and run its tests"
        }
    ],
    tools=tools,
    tool_choice="auto"  # Let model decide when to call functions
)

# Handle function calls
if response.choices[0].message.tool_calls:
    for tool_call in response.choices[0].message.tool_calls:
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)

        print(f"Calling {function_name} with args: {function_args}")

        # Execute function and get result
        if function_name == "get_code_metrics":
            result = get_code_metrics(**function_args)
        elif function_name == "run_tests":
            result = run_tests(**function_args)

        # Send result back to model
        messages = [
            {"role": "user", "content": "Analyze the complexity of src/utils/parser.py"},
            response.choices[0].message,  # Assistant's function call
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result)
            }
        ]

        # Get final response
        final_response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )

        print(final_response.choices[0].message.content)
```

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
4. Teams SHOULD validate function arguments before execution
5. Teams MUST handle function execution errors gracefully

### Function Calling Error Handling

```python
def safe_function_calling(client, messages, tools):
    """
    Robust function calling with validation and error handling.

    Requirements:
    - MUST validate function arguments against schema
    - MUST handle function execution errors
    - SHOULD retry on validation errors with correction
    - MUST NOT execute untrusted code
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )

    if not response.choices[0].message.tool_calls:
        return response.choices[0].message.content

    results = []
    for tool_call in response.choices[0].message.tool_calls:
        function_name = tool_call.function.name

        try:
            # Validate JSON
            function_args = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError as e:
            results.append({
                "tool_call_id": tool_call.id,
                "error": f"Invalid JSON arguments: {e}"
            })
            continue

        # Validate against available functions
        if function_name not in AVAILABLE_FUNCTIONS:
            results.append({
                "tool_call_id": tool_call.id,
                "error": f"Unknown function: {function_name}"
            })
            continue

        # Execute function with error handling
        try:
            result = AVAILABLE_FUNCTIONS[function_name](**function_args)
            results.append({
                "tool_call_id": tool_call.id,
                "content": json.dumps(result)
            })
        except Exception as e:
            results.append({
                "tool_call_id": tool_call.id,
                "error": f"Function execution error: {str(e)}"
            })

    return results
```

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

# Guaranteed to match schema
analysis = response.choices[0].message.parsed
print(f"Language: {analysis.language}")
print(f"Functions: {analysis.functions}")
print(f"Complexity: {analysis.complexity}")
```

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
from openai import OpenAI, LengthFinishReasonError

try:
    response = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=messages,
        response_format=MySchema
    )

    # Check for refusal (content policy violation)
    if response.choices[0].message.refusal:
        print(f"Request refused: {response.choices[0].message.refusal}")
        return None

    # Access parsed data
    data = response.choices[0].message.parsed
    return data

except LengthFinishReasonError as e:
    # Output was truncated due to max_tokens
    print("Response truncated. Increase max_tokens.")
    partial_data = e.completion.choices[0].message.parsed
    return partial_data

except Exception as e:
    print(f"Parsing error: {e}")
    return None
```

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
class ConversationManager:
    """
    Manage conversation context within token limits.

    Requirements:
    - MUST maintain system message
    - SHOULD keep recent messages
    - MAY summarize older messages
    - MUST NOT exceed context window
    """

    def __init__(self, model: str = "gpt-4o", max_tokens: int = 120000):
        self.model = model
        self.max_tokens = max_tokens
        self.system_message = None
        self.messages = []

    def add_message(self, role: str, content: str):
        """Add message to conversation."""
        self.messages.append({"role": role, "content": content})
        self._truncate_if_needed()

    def _truncate_if_needed(self):
        """Truncate old messages if approaching token limit."""
        while True:
            total = count_messages_tokens(self.get_messages(), self.model)

            # Keep 20% buffer for response
            if total <= self.max_tokens * 0.8:
                break

            # Always keep system message and last 2 exchanges
            if len(self.messages) <= 4:
                break

            # Remove oldest user-assistant pair
            self.messages.pop(0)
            if self.messages and self.messages[0]["role"] == "assistant":
                self.messages.pop(0)

    def get_messages(self):
        """Get messages with system prompt."""
        if self.system_message:
            return [self.system_message] + self.messages
        return self.messages
```

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
    # Retry with backoff
except APIError:
    # Log and handle gracefully
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

# GOOD: Validate before execution
args = json.loads(tool_call.function.arguments)
if not validate_args(args, function_schema):
    raise ValueError("Invalid arguments")
result = execute_function(**args)
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
    max_tokens=500,  # Limit based on expected output
    ...
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
    temperature=0,  # Deterministic output
    ...
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
    timeout=30.0,
    ...
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
# DON'T: Use o1 for function calling
response = client.chat.completions.create(
    model="o1-preview",
    tools=tools  # Not supported!
)

# DO: Use GPT-4o for function calling
response = client.chat.completions.create(
    model="gpt-4o",
    tools=tools
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

# DO: Validate and sanitize
args = json.loads(tool_call.function.arguments)
if not is_safe_to_execute(args):
    raise SecurityError("Unsafe function arguments")
result = safe_execute(args)
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
    max_tokens=500,  # Appropriate for expected output
    ...
)
```

### Cost Optimization

```python
# DON'T: Skip caching for repeated requests
def get_response(prompt):
    return client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}]
    )

# DO: Cache identical requests
cache = ResponseCache()

def get_response(prompt):
    cached = cache.get(prompt)
    if cached:
        return cached

    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}]
    )
    cache.set(prompt, response)
    return response
```

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
stream = client.chat.completions.create(stream=True, ...)
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
    response_format=Person,
    ...
)
data = response.choices[0].message.parsed  # Guaranteed valid
```

### Temperature Settings

```python
# DON'T: Use high temperature for code generation
response = client.chat.completions.create(
    temperature=1.5,  # Too creative for code
    ...
)

# DO: Use temperature=0 for deterministic code
response = client.chat.completions.create(
    temperature=0,  # Consistent, reliable code
    ...
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
