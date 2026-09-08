# Google Gemini Best Practices Guide

> [Doctrine](../../README.md) > [Guides](../README.md) > [AI](./README.md) > Gemini

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

## Table of Contents

- [Introduction](#introduction)
- [Model Selection](#model-selection)
  - [Model Availability](#model-availability)
  - [Gemini 3.8 Flash](#gemini-38-flash)
  - [Gemini 3.1 Pro Preview](#gemini-31-pro-preview)
  - [Stable Fallbacks and Retired Models](#stable-fallbacks-and-retired-models)
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

### Model Availability

Model IDs are not stable over time: once a model is shut down its endpoint is
removed and requests fail outright rather than degrading. You MUST check the
Gemini API deprecations page[^6] and the Gemini Enterprise Agent Platform model
versions page[^21] before pinning a model, and you MUST record the shutdown or
retirement date next to every pinned ID in your own configuration.

**Why**: The two platforms run separate lifecycles. A model that the Gemini API
still serves can already have a retirement date on Vertex AI, so a single
"current model" list is wrong for at least one of the two audiences.

The following table was verified on 8 September 2026 against the Gemini API
deprecations page[^6] and the Gemini Enterprise Agent Platform model versions
page[^21]. "GEAP" is the Gemini Enterprise Agent Platform, the Vertex AI
surface for Gemini models.

| Model ID                 | Stage     | Released     | Gemini API shutdown | GEAP retirement | Replacement                             |
| ------------------------ | --------- | ------------ | ------------------- | --------------- | --------------------------------------- |
| `gemini-3.8-flash`       | GA        | 2 Sep 2026   | None announced      | None announced  | —                                       |
| `gemini-3.7-flash`       | GA        | 13 Aug 2026  | None announced      | None announced  | —                                       |
| `gemini-3.6-flash`       | GA        | 21 Jul 2026  | None announced      | None announced  | —                                       |
| `gemini-3.1-pro-preview` | Preview   | 19 Feb 2026  | None announced      | Not offered     | —                                       |
| `gemini-2.5-pro`         | GA        | 17 Jun 2025  | None announced      | 20 Oct 2026     | Gemini 3.5 Flash                        |
| `gemini-2.5-flash`       | GA        | 17 Jun 2025  | None announced      | 20 Oct 2026     | Gemini 3.5 or 3.1 Flash-Lite            |
| `gemini-2.0-flash`       | Shut down | 5 Feb 2025   | 1 Jun 2026          | 1 Jun 2026      | `gemini-3.6-flash` / `gemini-3.1-flash-lite` |
| `gemini-1.5-pro-002`     | Retired   | 24 Sep 2024  | Shut down           | 24 Sep 2025     | `gemini-2.5-flash`                      |
| `gemini-1.5-flash-002`   | Retired   | 24 Sep 2024  | Shut down           | 24 Sep 2025     | `gemini-2.5-flash-lite`                 |
| `gemini-1.5-pro-001`     | Retired   | 24 May 2024  | Shut down           | 24 May 2025     | `gemini-2.5-flash`                      |

You MUST NOT send traffic to `gemini-2.0-flash`, `gemini-1.5-pro`,
`gemini-1.5-flash`, or any `-001`/`-002` variant of those families: those
endpoints no longer exist on either platform[^6][^21].

On the Gemini Enterprise Agent Platform, the 3.6, 3.7, and 3.8 Flash models sit
in the short-availability tier: they retire 45 days after a replacement model
ships[^21]. Models in the 12-month tier, such as `gemini-3.5-flash`, are
guaranteed for at least a year from release[^21]. Choose the tier deliberately
if a migration costs you more than 45 days of notice.

You MUST pin an exact stable ID such as `gemini-3.8-flash` in production rather
than a `-latest` alias. Aliases are hot-swapped on each release of that model
variation, with only two weeks' notice of breaking changes[^1].

**Why**: An alias silently changes the model behind your evaluation baseline,
so regressions appear as unexplained quality drift rather than as a deploy.

### Gemini 3.8 Flash[^4]

**Model ID**: `gemini-3.8-flash` — GA, released 2 September 2026, no shutdown
date announced[^4][^6]

**Context Window**: 1,048,576 tokens (1M input), 65,536 tokens (64K output)[^4]

**Default thinking level**: `medium`, tunable to `low` or `high`. The `minimal`
level is not supported on this model[^4].

**Key Features**[^4]:

- Long-horizon software engineering across multi-file refactors
- Resilient multi-step planning and tool orchestration for autonomous agents
- Deterministic tool execution with the full built-in tool suite
- Default model for the Antigravity managed agent
- Flash-class latency and pricing

**Use Cases**:

- Interactive coding assistance and development environments
- Agentic workflows that call tools iteratively
- High-volume API calls with cost constraints
- Multimodal applications (code plus diagrams)

**Limitations**:

- Spends more tokens by design on long, complex tasks, because it takes smaller
  reasoning steps and verifies its own work[^4]
- Preview-only capabilities (for example Live audio) require a different model

You SHOULD use Gemini 3.8 Flash as the default for new work, and you SHOULD
lower `thinking_level` to `low` for latency-critical or high-throughput paths
rather than switching to an older family[^4].

### Gemini 3.1 Pro Preview[^5]

**Model ID**: `gemini-3.1-pro-preview` — preview, released 19 February 2026, no
shutdown date announced[^5][^6]

**Context Window**: 1,048,576 tokens (1M input), 65,536 tokens (64K output);
knowledge cutoff January 2025[^5]

**Default thinking level**: `high` (dynamic); `minimal` is not supported[^5]

**Key Features**[^5]:

- Strongest reasoning in the Gemini 3 family for broad world knowledge
- Improved token efficiency and factual consistency over Gemini 3 Pro
- Optimised for agentic workflows needing precise tool usage
- A companion `gemini-3.1-pro-preview-customtools` endpoint that prioritises
  caller-defined tools such as `view_file` or `search_code`[^5]

**Use Cases**:

- Cross-repository refactoring and architectural decision support
- Multi-file code review where reasoning quality dominates cost
- Long-form documentation generation from large sources

**Limitations**:

- Preview stage: deprecation needs only two weeks' notice[^1]
- Roughly 2.8x the cost of Gemini 3.8 Flash on a typical review workload (see
  [Cost-Performance Trade-offs](#cost-performance-trade-offs))
- Higher latency, because thinking defaults to `high`

You SHOULD use Gemini 3.1 Pro Preview when reasoning quality dominates cost,
and you MUST treat it as a preview dependency: pin the exact ID, subscribe to
the deprecations page[^6], and keep a tested fallback to `gemini-3.8-flash`.

**Why**: Preview models can be withdrawn on two weeks' notice[^1]. Without a
tested fallback that notice period becomes an unplanned migration.

### Stable Fallbacks and Retired Models

`gemini-2.5-pro` and `gemini-2.5-flash` are still served by the Gemini API with
no announced shutdown date[^6], but both retire on the Gemini Enterprise Agent
Platform on **20 October 2026**[^21].

If you run on Vertex AI you MUST migrate off the 2.5 series before
20 October 2026. If you run on the Gemini API you MAY keep 2.5 models for
workloads with a frozen evaluation baseline, and you MUST re-check the
deprecations page[^6] each quarter.

**Why**: Retirement dates may be extended but are never moved earlier[^21], so
a dated check is cheap insurance and an undated "current" list is not.

### Model Comparison Matrix

Verified 8 September 2026. Blank cells mean the figure is not published on the
cited pages; check the model page before relying on one.

| Feature                  | `gemini-3.8-flash`     | `gemini-3.1-pro-preview`      |
| ------------------------ | ---------------------- | ----------------------------- |
| **Stage**                | GA                     | Preview                       |
| **Input context**        | 1M tokens              | 1M tokens                     |
| **Output tokens**        | 65,536                 | 65,536                        |
| **Default thinking**     | `medium`               | `high` (dynamic)              |
| **`minimal` thinking**   | Not supported          | Not supported                 |
| **Cost (per 1M input)**  | $0.75                  | $2.00 (<200K), $4.00 (>200K)  |
| **Cost (per 1M output)** | $3.75                  | $12.00 (<200K), $18.00 (>200K)|
| **Knowledge cutoff**     | Not published          | January 2025                  |
| **Function calling**     | Yes                    | Yes                           |
| **Grounding**            | Yes                    | Yes                           |
| **Shutdown date**        | None announced         | None announced                |

Gemini 3.8 Flash prices are the introductory rates that apply through
31 December 2026; see [Pricing Structure](#pricing-structure).

### Pricing Structure

**Verified 8 September 2026**[^7][^5] (Google AI Studio and Gemini Enterprise
Agent Platform), per 1M tokens in USD, paid tier:

#### Gemini 3.8 Flash

- Input: $0.75 through 31 December 2026, then $1.50 from 1 January 2027
- Output (including thinking tokens): $3.75, then $7.50 from 1 January 2027
- Context caching: $0.075, then $0.15 from 1 January 2027
- Cache storage: $0.50 per 1M tokens per hour, then $1.00 from 1 January 2027
- Batch and Flex tiers: half the standard input and output rates
- Priority tier: $1.35 input, $6.75 output

Introductory pricing also covers Gemini 3.7 Flash and Gemini 3.6 Flash through
31 December 2026[^7].

#### Gemini 3.1 Pro Preview

- Input: $2.00 for requests under 200K tokens, $4.00 above 200K tokens
- Output: $12.00 under 200K tokens, $18.00 above 200K tokens

#### Grounding with Google Search

- 5,000 free search requests per month, shared across all Gemini 3.x models
- $14 per 1,000 requests thereafter[^7]

**Note**: Free-tier usage of the Gemini API MAY be used to improve Google's
products; paid-tier usage MAY NOT[^7]. See
[Data Handling](#data-handling) before sending any proprietary source code.

### Selection Guidelines

#### Decision Tree

```text
START
├─ Running a 2.5-series model on Vertex AI?
│  └─ YES → migrate before 20 Oct 2026 → gemini-3.8-flash
│  └─ NO → Continue
│
├─ Prompt larger than 1M tokens?
│  └─ YES → split or retrieve; no current model exceeds 1M input
│  └─ NO → Continue
│
├─ Reasoning quality dominates cost (architecture, cross-repo refactor)?
│  └─ YES → gemini-3.1-pro-preview (pin it; keep a Flash fallback)
│  └─ NO → Continue
│
├─ Latency- or throughput-critical, well-defined task?
│  └─ YES → gemini-3.8-flash with thinking_level="low"
│  └─ NO → Continue
│
└─ Default → gemini-3.8-flash (thinking_level="medium")
```

#### Cost-Performance Trade-offs

**Example Scenario**: Code review service processing 1,000 pull requests/day

Each PR analysis requires:

- Average input: 50,000 tokens
- Average output: 2,000 tokens

That is 1,500M input tokens and 60M output tokens per 30-day month.

**Monthly Costs** (introductory rates, through 31 December 2026):

Gemini 3.8 Flash:

- Input: 1,500M tokens × $0.75/1M = $1,125.00
- Output: 60M tokens × $3.75/1M = $225.00
- **Total: $1,350.00/month** (doubles to $2,700.00 from 1 January 2027)

Gemini 3.1 Pro Preview (requests under 200K tokens):

- Input: 1,500M tokens × $2.00/1M = $3,000.00
- Output: 60M tokens × $12.00/1M = $720.00
- **Total: $3,720.00/month**

**Cost Difference**: 2.8x more expensive for Pro

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

The Gemini API accepts two kinds of API key and they are not interchangeable[^22]:

- **Authorization (auth) keys** are bound to a Google Cloud service account.
  Requests run under that service account's identity, the key is restricted to
  the Gemini API by default, and Google's leaked-key enforcement disables it
  quickly when detection fires.
- **Standard keys** identify only the billing project. They name no caller, so
  they cannot carry granular permissions.

You MUST authenticate with an auth key. Every key created in Google AI Studio
today is an auth key, but keys created earlier MAY still be standard ones. The
Gemini API already rejects requests from unrestricted standard keys, and from
**September 2026** it rejects standard keys entirely[^22].

**Why**: A standard key proves only which project pays. An auth key carries a
service account identity, so IAM decides what the caller may do and a leaked
key can be revoked without disturbing every other consumer of the project.

**Migration checklist** — work through this for each environment[^22]:

1. Open the AI Studio API Keys page and read the **Key Type** column.
2. For every key marked **Standard**, click **Create API key**; new keys are
   created as auth keys automatically.
3. Update application code, environment variables, and deployment
   configuration to the new key.
4. Test the application against the new key.
5. Delete or revoke the old standard key once traffic has moved.

Creating an auth key requires these project IAM permissions[^22]:
`resourcemanager.projects.get`, `apikeys.keys.create`,
`serviceusage.services.enable`, `iam.serviceAccounts.create`, and
`iam.serviceAccountApiKeyBindings.create`.

Supply the key through the environment. The client libraries read
`GEMINI_API_KEY` or `GOOGLE_API_KEY`, and `GOOGLE_API_KEY` wins if both are
set[^22]:

```bash
export GEMINI_API_KEY="your-auth-key-here"
```

You MUST send the key in the `x-goog-api-key` header rather than a `key` query
parameter[^22]:

```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent" \
    -H "x-goog-api-key: ${GEMINI_API_KEY}" \
    -H "Content-Type: application/json" \
    -X POST \
    -d '{"contents": [{"parts": [{"text": "Explain recursion in one sentence"}]}]}'
```

**Why**: Query strings leak. They land in proxy and load-balancer access logs,
browser history, `Referer` headers, and shell history, none of which are
designed to hold credentials. A header is not logged by default.

You SHOULD NOT:

- Commit API keys to version control
- Share API keys across teams
- Use the same key for dev and production
- Ship a key in client-side web or mobile code; proxy through your backend[^22]

You MUST:

- Store keys in environment variables or a secret manager such as Google Cloud
  Secret Manager[^22]
- Apply application restrictions to every key; the API blocks unrestricted keys
  that have been dormant for an extended period since 7 May 2026[^22]
- Rotate keys regularly (every 90 days recommended)
- Use separate keys per environment

#### Basic REST API Example

```python
import os
import google.generativeai as genai

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

model = genai.GenerativeModel("gemini-3.8-flash")

response = model.generate_content(
    "Write a Python function to calculate factorial recursively"
)

print(response.text)
```

#### Endpoint Structure

```text
POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent
```

You **MUST** include:

- The auth key in an `x-goog-api-key` request header[^22]
- Content-Type header: `application/json`

You **MUST NOT** append the key as a `?key=` query parameter.

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

model = GenerativeModel("gemini-3.8-flash")

response = model.generate_content(
    "Write a Python function to calculate factorial recursively"
)

print(response.text)
```

#### Service Account Setup

Vertex AI uses Application Default Credentials (ADC): the client libraries find
credentials from the environment, so the same code runs locally and in
production without a credentials file[^23].

You MUST choose the credential source by environment, in this order[^25]:

1. **Running on Google Cloud** — attach a service account to the resource (or
   use Workload Identity Federation for GKE) and grant it `roles/aiplatform.user`
2. **Running outside Google Cloud with an external identity provider** —
   configure workload identity federation
3. **Local development** — `gcloud auth application-default login`, and
   impersonate a service account when you need to match production's identity
4. **Downloaded JSON key** — only when none of the above is possible

You MUST NOT download a service account key when an alternative applies.

**Why**: A downloaded key is a long-lived credential that never expires on its
own. Google's own guidance treats user-managed keys as an exception rather than
the norm, because they leak into repositories, buckets, inboxes, and CI logs,
and a leaked key authenticates with no further challenge[^24].

```bash
# Create service account
gcloud iam service-accounts create gemini-service \
    --display-name="Gemini API Service Account"

# Grant permissions
gcloud projects add-iam-policy-binding your-project-id \
    --member="serviceAccount:gemini-service@your-project-id.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

# Production on Google Cloud: attach the service account to the workload;
# no key material is created or stored.
gcloud run deploy gemini-app \
    --service-account=gemini-service@your-project-id.iam.gserviceaccount.com

# Local development: user credentials for ADC, impersonating the same
# service account so local and production authorisation match.
gcloud auth application-default login
gcloud config set auth/impersonate_service_account \
    gemini-service@your-project-id.iam.gserviceaccount.com
```

If you have an exception that genuinely requires a downloaded key, you MUST
write it straight to its destination, keep it out of source control and out of
the downloads folder, restrict its permissions, rotate it on a schedule, and
delete it once the workload can use a safer method[^24]:

```bash
# EXCEPTION ONLY: no attached identity and no federation available
gcloud iam service-accounts keys create /etc/gemini/key.json \
    --iam-account=gemini-service@your-project-id.iam.gserviceaccount.com
chmod 600 /etc/gemini/key.json
export GOOGLE_APPLICATION_CREDENTIALS="/etc/gemini/key.json"
```

You SHOULD block the exception from becoming the habit by setting the
organisation policy constraint that disables service account key creation, and
granting exemptions only to projects that have demonstrated they cannot use a
safer method[^24].

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
3. Create an API key; keys created in AI Studio are auth keys[^22]
4. Set the environment variable

```bash
export GEMINI_API_KEY="your-auth-key-here"
```

#### Vertex AI Setup

1. Create or select a GCP project
2. Enable the Vertex AI API, `aiplatform.googleapis.com`[^3]:

   ```bash
   gcloud services enable aiplatform.googleapis.com
   ```

3. Set up authentication (see Service Account Setup above)
4. Install the Vertex AI SDK, `google-cloud-aiplatform`[^12]:

   ```bash
   pip install google-cloud-aiplatform
   ```

Footnote markers MUST stay in the surrounding prose. A marker such as
`[^n]` inside a command changes what the command means: `pip` reads
`google-cloud-aiplatform[^n]` as a malformed extras group and refuses the
requirement, and a shell reads `aiplatform.googleapis.com[^n]` as a bracket
glob that can expand to a neighbouring filename.

#### SDK Installation

Install the Google AI Studio SDK (`google-generativeai`) or the Vertex AI SDK
(`google-cloud-aiplatform`[^12]) for Python:

```bash
# For Google AI Studio
pip install google-generativeai

# For Vertex AI
pip install google-cloud-aiplatform
```

For Node.js, install `@google/generative-ai` or `@google-cloud/vertexai`:

```bash
# For Google AI Studio
npm install @google/generative-ai

# For Vertex AI
npm install @google-cloud/vertexai
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
    model_name="gemini-3.8-flash",
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
    model_name="gemini-3.1-pro-preview",
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
    model_name="gemini-3.8-flash",
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
    model_name="gemini-3.8-flash",
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

# Collect the populated fields. "function_call" in part is a proto-plus
# presence check: hasattr() is always True on a Part, even for text.
function_calls = []
text_chunks = []
for part in response.candidates[0].content.parts:
    if "function_call" in part:
        function_calls.append(part.function_call)
    elif "text" in part:
        text_chunks.append(part.text)

if function_calls:
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
    print("".join(text_chunks))
```

A response MAY mix text and tool calls in one turn, and the tool call is not
always the first part. You MUST scan every part, and you MUST test which field
is populated rather than whether an attribute exists.

**Why**: On a `Part`, `hasattr(part, "function_call")` is always true. A
text-only part reports an empty `FunctionCall` whose `name` is `""`, so an
attribute check appends a phantom tool call, skips the text branch, and then
fails the dispatcher lookup on the empty name. `"function_call" in part` tests
which field of the `data` oneof is actually set, so text-only, tool-only, and
mixed responses all route correctly.

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

A string prefix test is not a read-only boundary. Enforce the boundary in the
database, let the model pick an allowlisted query by name, and bind its
arguments as parameters:

```sql
-- The role the tool connects as can read the analytics schema, nothing else.
CREATE ROLE gemini_readonly LOGIN;
REVOKE ALL ON SCHEMA analytics FROM gemini_readonly;
GRANT USAGE ON SCHEMA analytics TO gemini_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA analytics TO gemini_readonly;
ALTER ROLE gemini_readonly SET default_transaction_read_only = on;
ALTER ROLE gemini_readonly SET statement_timeout = '10s';
```

```python
# The model never authors SQL. It names a query and supplies parameters.
ALLOWED_QUERIES = {
    "orders_by_day": (
        "SELECT order_date, COUNT(*) AS orders "
        "FROM analytics.orders "
        "WHERE order_date BETWEEN %(start)s AND %(end)s "
        "GROUP BY order_date ORDER BY order_date"
    ),
    "top_products": (
        "SELECT product_id, SUM(quantity) AS units "
        "FROM analytics.order_items "
        "WHERE order_date >= %(start)s "
        "GROUP BY product_id ORDER BY units DESC"
    ),
}

REQUIRED_PARAMS = {
    "orders_by_day": frozenset({"start", "end"}),
    "top_products": frozenset({"start"}),
}

MAX_ROWS = 500
STATEMENT_TIMEOUT_MS = 10_000


def run_named_query(name: str, params: dict, *, principal: str) -> dict:
    """Run one allowlisted, parameterised query on a read-only connection."""
    sql = ALLOWED_QUERIES.get(name)
    if sql is None:
        return {
            "success": False,
            "error": "unknown_query",
            "allowed": sorted(ALLOWED_QUERIES),
        }

    expected = REQUIRED_PARAMS[name]
    missing = sorted(expected - params.keys())
    unexpected = sorted(params.keys() - expected)
    if missing or unexpected:
        return {
            "success": False,
            "error": "bad_parameters",
            "missing": missing,
            "unexpected": unexpected,
        }

    # Audit every call: who asked, which query, which arguments.
    audit_log.info(
        "tool_query", extra={"principal": principal, "query": name, "params": params}
    )

    with connect_read_only() as conn, conn.cursor() as cur:
        cur.execute(f"SET LOCAL statement_timeout = {STATEMENT_TIMEOUT_MS}")
        cur.execute(sql, {key: params[key] for key in expected})
        rows = cur.fetchmany(MAX_ROWS + 1)

    return {
        "success": True,
        "rows": rows[:MAX_ROWS],
        "truncated": len(rows) > MAX_ROWS,
    }
```

**Why**: `sql.strip().upper().startswith("SELECT")` accepts
`SELECT 1; DROP TABLE users`, `SELECT * FROM t; UPDATE t SET x = 1`, and
`SELECT pg_sleep(600)`. Whether those run depends on the driver's handling of
multiple statements and on the role's privileges, so the check enforces nothing
it claims to. Privileges, a fixed query text, bound parameters, a statement
timeout, and a row cap each hold on their own.

If a use case genuinely needs model-authored SQL, you MUST still connect as the
read-only role and you MUST parse the statement, requiring exactly one
statement with a `SELECT` root, using a real SQL parser rather than string
inspection.

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
    "gemini-3.8-flash",
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
    "gemini-3.1-pro-preview",
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
response = model.generate_content("Latest news about Gemini 3.8 Flash")

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

Gemini models support 1M-token context windows, enabling analysis of entire
codebases, long documents, and extensive conversations.

### Context Window Capabilities

Verified 8 September 2026; see [Model Availability](#model-availability) for
lifecycle dates.

| Model                    | Input Tokens | Output Tokens | Equivalent                 |
| ------------------------ | ------------ | ------------- | -------------------------- |
| `gemini-3.8-flash`[^4]   | 1,048,576    | 65,536        | ~800K words or ~3500 pages |
| `gemini-3.1-pro-preview`[^5] | 1,048,576 | 65,536        | ~800K words or ~3500 pages |

No current Gemini model accepts more than 1M input tokens. Inputs larger than
that MUST be split, summarised, or retrieved selectively; see
[Long Context Strategies](#long-context-strategies).

**Token Estimation**:

- 1 token ≈ 4 characters
- 1 token ≈ 0.75 words
- 1000 tokens ≈ 750 words
- 100K tokens ≈ 75,000 words ≈ 300 pages

### Effective Context Loading

#### Loading Multiple Files

Sending a repository to a third-party API is a disclosure event, so the loader
MUST decide what leaves the machine, not the caller's `rglob` pattern.

The loader below is manifest-first: it sends the paths you list, or, with no
manifest, only allowlisted file types under the repository root. It refuses
symlinks and paths outside the root, skips files whose contents match secret
patterns, enforces per-file and total budgets, and returns a report naming
every skipped path with its reason.

```python
import re
from dataclasses import dataclass, field
from pathlib import Path

ALLOWED_SUFFIXES = {".py", ".md", ".yaml", ".yml", ".toml"}
EXCLUDED_DIRS = {
    ".git", "node_modules", "__pycache__", "venv", ".venv",
    "dist", "build", ".next", "coverage",
}
# Files that carry credentials by convention, whatever their suffix.
EXCLUDED_NAMES = {
    ".env", ".env.local", ".npmrc", ".netrc", "id_rsa",
    "credentials.json", "service-account.json",
}
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b"),
    re.compile(r"\bgh[pousr]_[0-9A-Za-z]{36}\b"),
    re.compile(
        r"(?i)\b(api[_-]?key|secret|passwd|password|token)\s*[:=]\s*"
        r"['\"][^'\"]{8,}['\"]"
    ),
)

MAX_FILE_BYTES = 200_000
MAX_TOTAL_TOKENS = 400_000
CHARS_PER_TOKEN = 4  # See Token Estimation above


@dataclass
class LoadReport:
    included: list[str] = field(default_factory=list)
    skipped: list[tuple[str, str]] = field(default_factory=list)
    estimated_tokens: int = 0


def _candidates(root: Path, manifest: list[str] | None) -> list[Path]:
    if manifest is not None:
        return [root / entry for entry in manifest]
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix in ALLOWED_SUFFIXES
    )


def load_codebase(
    root_dir: str,
    manifest: list[str] | None = None,
) -> tuple[str, LoadReport]:
    """Load reviewed files into one context, reporting everything skipped."""
    root = Path(root_dir).resolve(strict=True)
    report = LoadReport()
    parts: list[str] = []

    for path in _candidates(root, manifest):
        label = str(path)

        if path.is_symlink():
            report.skipped.append((label, "symlink"))
            continue

        resolved = path.resolve()
        if root not in resolved.parents:
            report.skipped.append((label, "outside repository root"))
            continue
        if not resolved.is_file():
            report.skipped.append((label, "not a regular file"))
            continue

        relative = resolved.relative_to(root)
        if set(relative.parts) & EXCLUDED_DIRS:
            report.skipped.append((label, "excluded directory"))
            continue
        if resolved.name in EXCLUDED_NAMES:
            report.skipped.append((label, "credential filename"))
            continue
        if resolved.suffix not in ALLOWED_SUFFIXES:
            report.skipped.append((label, f"suffix not allowlisted: {resolved.suffix}"))
            continue
        if resolved.stat().st_size > MAX_FILE_BYTES:
            report.skipped.append((label, f"larger than {MAX_FILE_BYTES} bytes"))
            continue

        try:
            content = resolved.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as exc:
            report.skipped.append((label, f"unreadable: {type(exc).__name__}"))
            continue

        if any(pattern.search(content) for pattern in SECRET_PATTERNS):
            report.skipped.append((label, "matched a secret pattern"))
            continue

        tokens = len(content) // CHARS_PER_TOKEN
        if report.estimated_tokens + tokens > MAX_TOTAL_TOKENS:
            report.skipped.append((label, "token budget exhausted"))
            continue

        report.estimated_tokens += tokens
        report.included.append(str(relative))
        suffix = resolved.suffix.lstrip(".")
        parts.append(f"### File: {relative}\n\n```{suffix}\n{content}\n```\n")

    return "\n".join(parts), report


context, report = load_codebase("./src")

# Review the exclusions before sending anything.
for path, reason in report.skipped:
    print(f"skipped {path}: {reason}")
print(f"{len(report.included)} files, ~{report.estimated_tokens} tokens")

prompt = f"""Analyze this codebase for security vulnerabilities.

{context}

Provide a comprehensive security audit report."""

model = genai.GenerativeModel("gemini-3.1-pro-preview")
response = model.generate_content(prompt)
```

**Why**: A recursive load by file extension follows symlinks out of the tree,
picks up `.env` files and key material committed by accident, and grows without
bound. The failure is silent and one-way: once the content is in a request, you
cannot recall it.

A secret scan is a backstop, not a control: it catches known shapes only. You
MUST NOT rely on it in place of keeping credentials out of the repository.

Before the first request you MUST confirm that the platform's data terms match
the classification of the code. Free-tier Gemini API traffic MAY be used to
improve Google's products; paid-tier traffic MAY NOT[^7]. Logs are retained for
up to 55 days by default, and any log you contribute to a shared dataset is
processed under the unpaid-services terms[^26]. Use Vertex AI for code you
cannot expose to those terms; see [Data Handling](#data-handling).

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

Context caching[^9] reuses large context prefixes, cutting the price of repeated
input tokens and improving latency.

**How It Works**:

1. Implicit caching is enabled by default for Gemini 2.5 and newer models, in
   both stateful and stateless conversation modes; savings are passed on
   automatically when a request hits the cache[^9]
2. Minimum input for a cache hit: 4,096 tokens on Gemini 3.x models and 2,048
   tokens on Gemini 2.5 models[^9]
3. Cached input tokens on `gemini-3.8-flash` cost $0.075/1M against $0.75/1M
   for uncached input, a 90% discount on the cached portion[^7]
4. Explicit caches add a storage charge of $0.50 per 1M tokens per hour, so a
   cache you never reuse costs more than no cache at all[^7]
5. `usage.total_cached_tokens` on the response reports how many tokens hit the
   cache[^9]

To raise the implicit hit rate you SHOULD place large, stable content at the
start of the prompt and send similar-prefix requests close together in time[^9].

**Why**: Implicit caching needs no code, and prefix ordering is the only lever
that affects it. Explicit caches only pay for themselves once reuse exceeds the
hourly storage charge.

Explicit caching pins a prefix for a chosen TTL:

```python
from google.generativeai import caching
import datetime

# Create cached content
cache = caching.CachedContent.create(
    model='models/gemini-3.8-flash',
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

**Cost Example** (`gemini-3.8-flash`, introductory rates verified
8 September 2026[^7]):

- Codebase: 500K tokens
- First request: 500K tokens × $0.75/1M = $0.375
- Cached requests: 500K tokens × $0.075/1M = $0.0375 (90% off the input price)
- 10 queries: $0.375 + (9 × $0.0375) = $0.7125
- Explicit cache storage for one hour: 500K tokens × $0.50/1M/hour = $0.25
- Without caching: 10 × $0.375 = $3.75
- **Savings: 81% on tokens, 74% once the hour of cache storage is included**

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
    """Select a cost-effective model for a task.

    Model IDs verified 2026-09-08; re-check the deprecations page before
    pinning these in production.
    """
    if context_size > 1_000_000:
        raise ValueError(
            "No current Gemini model accepts more than 1M input tokens; "
            "split, summarise, or retrieve selectively"
        )

    if task_type in ["simple_qa", "classification", "extraction"]:
        return "gemini-3.8-flash"  # Lowest cost per token

    if task_type in ["complex_reasoning", "architecture", "refactoring"]:
        if context_size > 100_000:
            return "gemini-3.1-pro-preview"  # Preview: keep a Flash fallback
        return "gemini-3.8-flash"  # Try Flash first

    return "gemini-3.8-flash"  # Default to Flash
```

### Context Caching for Savings

**Rule of Thumb**: implicit caching already applies to every Gemini 3.x request
above 4,096 tokens. Create an explicit cache only when the same prefix is
reused often enough to beat the hourly storage charge.

```python
# Break-even analysis (gemini-3.8-flash, rates verified 2026-09-08)
# Uncached input:  500K tokens x $0.75/1M  = $0.375
# Cached input:    500K tokens x $0.075/1M = $0.0375
# Cache storage:   500K tokens x $0.50/1M/hour = $0.25 per hour held
# Savings per cached request: $0.375 - $0.0375 = $0.3375
# Break-even: 1 extra request per hour the cache is held

CACHE_MIN_TOKENS = 4_096  # Gemini 3.x implicit cache minimum


def should_use_caching(
    context_size: int,
    expected_queries: int,
    cache_hours: float = 1.0,
    input_cost_per_1m: float = 0.75,
    cached_cost_per_1m: float = 0.075,
    storage_cost_per_1m_hour: float = 0.50,
) -> bool:
    """Determine whether an explicit cache is cheaper than repeating input."""
    if context_size < CACHE_MIN_TOKENS:
        return False  # Below the documented cache minimum

    if expected_queries < 2:
        return False  # Nothing to reuse

    millions = context_size / 1_000_000
    without_cache = expected_queries * millions * input_cost_per_1m
    with_cache = (
        millions * input_cost_per_1m  # First request populates the cache
        + (expected_queries - 1) * millions * cached_cost_per_1m
        + millions * storage_cost_per_1m_hour * cache_hours
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
    "gemini-3.8-flash",
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

**Solution**: Configure safety settings appropriately. The `HarmCategory` and
`HarmBlockThreshold` enums come from the SDK's `types` module; see the safety
settings guide[^18].

```python
from google.generativeai.types import HarmCategory, HarmBlockThreshold

model = genai.GenerativeModel(
    "gemini-3.8-flash",
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

**Solution**: Load through the audited loader from
[Effective Context Loading](#effective-context-loading), which allowlists file
types, rejects symlinks and paths outside the repository root, skips
credential-shaped files, and caps both file size and total tokens.

```python
# GOOD - one guarded loader, and the skip report is reviewed before sending
context, report = load_codebase("./src")

for path, reason in report.skipped:
    print(f"skipped {path}: {reason}")

if report.estimated_tokens > MAX_TOTAL_TOKENS:
    raise RuntimeError("context budget exceeded; narrow the manifest")

response = model.generate_content(f"{context}\n\nReview for bugs.")
```

You MUST NOT reimplement the filtering per call site. One loader means one
place to audit and one place to fix.

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
    # Test the populated field, not attribute existence: every Part exposes
    # both `function_call` and `text` attributes.
    if chunk.candidates[0].content.parts:
        for part in chunk.candidates[0].content.parts:
            if "function_call" in part:
                function_calls.append(part.function_call)
            elif "text" in part:
                text_parts.append(part.text)

# Text and tool calls can arrive in the same response; keep both.
complete_text = ''.join(text_parts)

if function_calls:
    # Execute functions and continue conversation
    ...
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

#### DO: Constrain Database Tools by Privilege, Not by String Check

```python
# GOOD - allowlisted query text, bound parameters, read-only role
def execute_database_query(query_name: str, params: dict) -> dict:
    sql = ALLOWED_QUERIES.get(query_name)
    if sql is None:
        return {
            "success": False,
            "error": "unknown_query",
            "allowed": sorted(ALLOWED_QUERIES),
        }

    try:
        with connect_read_only() as conn, conn.cursor() as cur:
            cur.execute("SET LOCAL statement_timeout = 10000")
            cur.execute(sql, params)
            rows = cur.fetchmany(MAX_ROWS + 1)
    except TimeoutError:
        return {"success": False, "error": "Query timeout after 10 seconds"}

    return {
        "success": True,
        "data": rows[:MAX_ROWS],
        "truncated": len(rows) > MAX_ROWS,
    }
```

See [Function Calling Best Practices](#function-calling-best-practices) for the
full pattern, including the `GRANT`/`REVOKE` statements that make the read-only
boundary real.

#### DON'T: Treat a SELECT Prefix as a Read-Only Boundary

```python
# BAD - accepts "SELECT 1; DROP TABLE users"
def execute_database_query(sql: str, database: str) -> dict:
    if not sql.strip().upper().startswith('SELECT'):
        return {"success": False, "error": "Only SELECT queries allowed"}
    return {"success": True, "data": execute(sql, database)}
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
    model='models/gemini-3.8-flash',
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
import random
import time

import google.api_core.exceptions

MAX_BACKOFF_SECONDS = 60.0


def generate_with_retry(prompt: str, max_retries: int = 3):
    """Retry only on transient failures, with capped exponential backoff."""
    for attempt in range(max_retries):
        try:
            return model.generate_content(prompt)
        except (
            google.api_core.exceptions.ResourceExhausted,
            google.api_core.exceptions.ServiceUnavailable,
            google.api_core.exceptions.DeadlineExceeded,
        ) as exc:
            if attempt == max_retries - 1:
                raise
            # Full jitter, capped: spreads retries instead of synchronising
            # every client onto the same second.
            delay = min(MAX_BACKOFF_SECONDS, 2 ** attempt) * random.random()
            print(f"{type(exc).__name__}. Retrying in {delay:.1f}s...")
            time.sleep(delay)

    raise RuntimeError("unreachable: loop either returns or raises")
```

You MUST import every module a snippet uses, you MUST retry only retryable
status codes, and you MUST cap the delay.

**Why**: The earlier form of this example called `random.random()` while
importing only `time`, so the first rate-limit response raised
`NameError: name 'random' is not defined` — the recovery path failed harder
than the failure it was handling. Retrying non-transient errors such as
`InvalidArgument` wastes quota, and uncapped exponential backoff can push a
delay past any sensible request deadline.

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
model = genai.GenerativeModel("gemini-3.8-flash")
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
    "gemini-3.1-pro-preview",
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

The key you manage MUST be an authorization key bound to a service account, not
a standard key: the Gemini API rejects standard keys from September 2026[^22].
See [Authentication](#authentication) for the migration checklist.

```python
# DO: Use environment variables
import os

import requests

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable not set")

# DO: Use secret management services
from google.cloud import secretmanager

client = secretmanager.SecretManagerServiceClient()
name = "projects/PROJECT_ID/secrets/gemini-api-key/versions/latest"
response = client.access_secret_version(request={"name": name})
api_key = response.payload.data.decode("UTF-8")

# DO: Send the key in a header when calling REST directly
requests.post(
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-3.8-flash:generateContent",
    headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
    json={"contents": [{"parts": [{"text": "Explain recursion"}]}]},
    timeout=30,
)

# DON'T: Put the key in the URL; query strings land in proxy and access logs
url = f"https://generativelanguage.googleapis.com/v1beta/models/m:generateContent?key={api_key}"

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
    "gemini-3.8-flash",
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
    if "function_call" in part:
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

[^1]: [Gemini API Models](https://ai.google.dev/gemini-api/docs/models) - Model list and stable, preview, latest and experimental version naming
[^2]: [Google AI Studio](https://aistudio.google.com/) - Web-based IDE and API access for Gemini
[^3]: [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs) - Enterprise platform for Gemini deployment
[^4]: [Gemini 3.8 Flash (Latest model)](https://ai.google.dev/gemini-api/docs/latest-model) - Specifications, thinking levels and migration checklist for `gemini-3.8-flash`
[^5]: [Gemini 3 Developer Guide](https://ai.google.dev/gemini-api/docs/gemini-3) - Context windows, thinking levels and pricing for the Gemini 3 family
[^6]: [Gemini API Deprecations](https://ai.google.dev/gemini-api/docs/deprecations) - Release dates, shutdown dates and recommended replacements
[^7]: [Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing) - Per-model token, caching and grounding prices, including introductory rates
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
[^21]: [Gemini Enterprise Agent Platform model versions](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/model-versions) - Release and retirement dates for Gemini models on Vertex AI
[^22]: [Gemini API keys](https://ai.google.dev/gemini-api/docs/api-key) - Standard versus authorization keys, the September 2026 cut-off and key restrictions
[^23]: [Provide credentials to Application Default Credentials](https://docs.cloud.google.com/docs/authentication/provide-credentials-adc) - Setting up ADC per environment
[^24]: [Best practices for managing service account keys](https://docs.cloud.google.com/iam/docs/best-practices-for-managing-service-account-keys) - Threats from downloaded keys and safer alternatives
[^25]: [Choose an authentication method](https://docs.cloud.google.com/docs/authentication) - Decision tree covering attached service accounts and workload identity federation
[^26]: [Gemini API logs policy](https://ai.google.dev/gemini-api/docs/logs-policy) - Log retention, dataset sharing and data-use terms

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
