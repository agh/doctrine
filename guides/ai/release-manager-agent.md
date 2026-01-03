# Release Manager Agent Specification

> [Doctrine](../../README.md) > [AI](README.md) > **Release Manager Agent**

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

## Table of Contents

1. [Introduction](#introduction)
2. [Architecture Overview](#architecture-overview)
3. [Signal Collectors](#signal-collectors)
4. [Analysis Engine](#analysis-engine)
   - [Outcome Tracking](#outcome-tracking)
   - [Predictive Intelligence](#predictive-intelligence)
5. [Decision Engine](#decision-engine)
6. [Changelog Generation](#changelog-generation)
7. [Release Workflows](#release-workflows)
8. [Integrations](#integrations)
9. [Configuration](#configuration)
10. [Security Considerations](#security-considerations)
11. [See Also](#see-also)

---

## Introduction

### Purpose

The Release Manager Agent is an AI-native tool that provides intelligent release
management, quality gate enforcement, and automated changelog generation. Unlike
traditional release automation tools that operate on rigid rules, this agent
uses LLM-powered analysis to understand context, assess readiness, and provide
actionable recommendations.

### Why

Existing release management tools fall into two categories:

1. **Fully Automated** (semantic-release, release-please): Execute mechanical
   workflows without understanding context or quality
2. **Fully Manual** (changesets): Require human decisions at every step without
   intelligent guidance

Neither approach provides what engineering teams actually need: **intelligent
decision support with automation capabilities**.

The Release Manager Agent bridges this gap by:

- Aggregating signals from tests, security scans, code reviews, and dependencies
- Providing confidence scores for release readiness
- Generating human-quality changelogs using LLM understanding
- Recommending actions while keeping humans in control

### Scope

This specification covers:

- Agent architecture and components
- Signal collection and analysis
- Release decision logic
- Changelog generation patterns
- Integration requirements
- Configuration options

### Audience

- Engineering teams implementing release automation
- DevOps engineers managing CI/CD pipelines
- Release managers overseeing software delivery
- Platform engineers building developer tooling

---

## Architecture Overview

### System Design

```text
┌─────────────────────────────────────────────────────────────────────┐
│                      RELEASE MANAGER AGENT                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                     Signal Collectors                          │ │
│  ├────────────┬────────────┬────────────┬────────────┬───────────┤ │
│  │   Git      │   CI/CD    │  Security  │   Code     │   Deps    │ │
│  │  Commits   │   Status   │   Scans    │  Reviews   │   Graph   │ │
│  └────────────┴────────────┴────────────┴────────────┴───────────┘ │
│                              │                                       │
│                              ▼                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                     Analysis Engine                            │ │
│  ├────────────────────────────────────────────────────────────────┤ │
│  │  • LLM Core (Claude/GPT)      • Pattern Matching               │ │
│  │  • Embeddings & RAG           • Historical Learning            │ │
│  │  • Semantic Understanding     • Impact Analysis                │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                              │                                       │
│                              ▼                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                     Decision Engine                            │ │
│  ├────────────────────────────────────────────────────────────────┤ │
│  │  • Confidence Scoring         • Version Calculation            │ │
│  │  • Blocker Detection          • Changelog Generation           │ │
│  │  • Risk Assessment            • Recommendations                │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                              │                                       │
│                              ▼                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    Output Handlers                             │ │
│  ├────────────┬────────────┬────────────┬────────────┬───────────┤ │
│  │  Release   │  Changelog │   Slack/   │   GitHub   │  Metrics  │ │
│  │   PR       │    File    │   Teams    │  Release   │  Export   │ │
│  └────────────┴────────────┴────────────┴────────────┴───────────┘ │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Core Principles

The agent MUST adhere to these principles:

1. **Intelligence Over Rules**: Use LLM understanding, not regex patterns
2. **Signals Over Guesses**: Base decisions on collected data
3. **Recommendations Over Mandates**: Suggest, don't force
4. **Transparency Over Magic**: Explain every decision
5. **Platform Agnostic**: Work with any tech stack

---

## Signal Collectors

Signal collectors gather information from various sources to inform release
decisions. Each collector MUST implement the `SignalCollector` interface.

### Git Collector

The Git Collector analyzes repository history since the last release.

#### Collected Signals

| Signal | Type | Description |
|--------|------|-------------|
| `commits` | `Commit[]` | All commits since last release |
| `authors` | `Author[]` | Contributors in this release |
| `files_changed` | `FileChange[]` | Modified files with change type |
| `breaking_changes` | `Commit[]` | Commits with breaking change indicators |
| `conventional_commits` | `ParsedCommit[]` | Commits parsed per Conventional Commits spec |

#### Configuration

```yaml
signal_collectors:
  git:
    enabled: true
    # Branch to analyze
    branch: main
    # Tag pattern for releases
    tag_pattern: "v*"
    # Conventional commit types to recognize
    commit_types:
      - feat
      - fix
      - docs
      - style
      - refactor
      - perf
      - test
      - build
      - ci
      - chore
    # Breaking change indicators
    breaking_indicators:
      - "BREAKING CHANGE:"
      - "BREAKING-CHANGE:"
      - "!:"
```

#### Example Output

```json
{
  "collector": "git",
  "signals": {
    "commits_count": 47,
    "authors_count": 8,
    "files_changed_count": 156,
    "breaking_changes_count": 2,
    "commit_types": {
      "feat": 12,
      "fix": 23,
      "docs": 5,
      "refactor": 4,
      "test": 3
    },
    "suggested_bump": "minor",
    "breaking_commits": [
      {
        "sha": "abc123",
        "message": "feat!: redesign authentication API",
        "author": "jane@example.com"
      }
    ]
  }
}
```

### CI/CD Collector

The CI/CD Collector gathers build and test status from CI systems.

#### Collected Signals

| Signal | Type | Description |
|--------|------|-------------|
| `workflow_runs` | `WorkflowRun[]` | Recent workflow executions |
| `test_results` | `TestSuite[]` | Test pass/fail/skip counts |
| `coverage` | `CoverageReport` | Code coverage metrics |
| `build_artifacts` | `Artifact[]` | Produced build outputs |
| `duration_trends` | `DurationTrend[]` | Build time analysis |

#### Supported Platforms

- GitHub Actions (native)
- GitLab CI (native)
- CircleCI (API)
- Jenkins (API)
- Azure Pipelines (API)

#### Configuration

```yaml
signal_collectors:
  cicd:
    enabled: true
    platform: github_actions
    # Required workflows for release
    required_workflows:
      - "CI"
      - "Security Scan"
      - "Integration Tests"
    # Minimum coverage threshold
    coverage_threshold: 80
    # Max allowed test failures
    max_test_failures: 0
    # Max allowed flaky tests
    max_flaky_tests: 5
```

### Security Collector

The Security Collector aggregates vulnerability and security scan data.

#### Collected Signals

| Signal | Type | Description |
|--------|------|-------------|
| `vulnerabilities` | `Vulnerability[]` | Known security issues |
| `dependency_audit` | `AuditResult` | Dependency vulnerability scan |
| `sast_results` | `SASTFinding[]` | Static analysis findings |
| `secrets_detected` | `SecretFinding[]` | Exposed secrets/credentials |
| `license_issues` | `LicenseIssue[]` | License compliance problems |

#### Severity Levels

```text
CRITICAL  → Blocks release, requires immediate fix
HIGH      → Blocks release by default, configurable
MEDIUM    → Warning, does not block
LOW       → Informational only
```

#### Configuration

```yaml
signal_collectors:
  security:
    enabled: true
    # Block release on these severities
    blocking_severities:
      - critical
      - high
    # Vulnerability sources
    sources:
      - dependabot
      - snyk
      - trivy
      - semgrep
    # Ignore specific CVEs
    ignore_cves:
      - CVE-2023-XXXXX  # False positive, documented
    # License blocklist
    blocked_licenses:
      - GPL-3.0
      - AGPL-3.0
```

### Code Review Collector

The Code Review Collector analyzes pull request review status.

#### Collected Signals

| Signal | Type | Description |
|--------|------|-------------|
| `prs_merged` | `PullRequest[]` | PRs included in release |
| `review_coverage` | `number` | Percentage of PRs reviewed |
| `approval_rate` | `number` | Average approvals per PR |
| `outstanding_comments` | `Comment[]` | Unresolved review comments |
| `review_latency` | `Duration` | Average time to review |

#### Configuration

```yaml
signal_collectors:
  code_review:
    enabled: true
    # Minimum approvals required
    min_approvals: 1
    # Require all comments resolved
    require_resolved_comments: true
    # Require review from code owners
    require_codeowner_review: true
    # Exempt paths from review requirement
    exempt_paths:
      - "docs/**"
      - "*.md"
```

### Dependency Collector

The Dependency Collector analyzes dependency changes and impacts.

#### Collected Signals

| Signal | Type | Description |
|--------|------|-------------|
| `added_deps` | `Dependency[]` | Newly added dependencies |
| `removed_deps` | `Dependency[]` | Removed dependencies |
| `updated_deps` | `DependencyUpdate[]` | Version changes |
| `breaking_updates` | `DependencyUpdate[]` | Major version bumps |
| `downstream_impact` | `Package[]` | Packages affected by changes |

#### Configuration

```yaml
signal_collectors:
  dependencies:
    enabled: true
    # Package managers to analyze
    package_managers:
      - npm
      - pip
      - cargo
      - go
    # Warn on major version bumps
    warn_major_bumps: true
    # Block on unreviewed new dependencies
    require_new_dep_review: true
```

---

## Analysis Engine

The Analysis Engine processes collected signals using LLM-powered understanding to derive insights.

### LLM Core

The agent MUST use an LLM for semantic understanding tasks.

#### Model Selection

| Task | Recommended Model | Rationale |
|------|-------------------|-----------|
| Changelog generation | Claude Sonnet / GPT-4o | Balance of quality and cost |
| Breaking change analysis | Claude Opus / GPT-4 | High-stakes decision |
| Commit classification | Claude Haiku / GPT-4o-mini | High volume, simpler task |
| Risk assessment | Claude Sonnet / GPT-4o | Requires reasoning |

#### System Prompt Template

```markdown
You are a Release Manager Agent analyzing software changes for release readiness.

Your responsibilities:
1. Analyze commits and changes for semantic meaning
2. Identify breaking changes even when not explicitly marked
3. Assess risk level of changes
4. Generate clear, user-focused changelog entries
5. Provide release recommendations with rationale

Context about this project:
{project_context}

Current release analysis:
{collected_signals}

Respond with structured analysis following the output schema.
```

### Semantic Understanding

The engine MUST perform semantic analysis on:

#### Commit Message Analysis

```python
def analyze_commit(commit: Commit) -> CommitAnalysis:
    """
    Analyze commit beyond conventional commit parsing.

    Identifies:
    - True intent (even if message is vague)
    - User-facing impact
    - Breaking change risk
    - Related components
    """
    pass
```

#### Code Change Analysis

```python
def analyze_changes(diff: Diff) -> ChangeAnalysis:
    """
    Analyze actual code changes for impact.

    Identifies:
    - API surface changes
    - Behavioral changes
    - Performance implications
    - Security considerations
    """
    pass
```

### Pattern Matching

The engine SHOULD use pattern matching for:

- Known vulnerability patterns
- Common breaking change indicators
- Security anti-patterns
- Performance regression patterns

### Historical Learning

The engine MAY learn from historical releases:

```yaml
historical_learning:
  enabled: true
  # Learn from past release patterns
  learn_from_releases: true
  # Learn from rollback incidents
  learn_from_rollbacks: true
  # Minimum data points before learning
  min_data_points: 10
```

### Outcome Tracking

The engine SHOULD systematically track what happens *after* each release to learn what actually matters.

#### Why Outcome Tracking

Traditional release tools only know if the release *happened*. They don't know:

- Did it cause production incidents?
- Was it rolled back?
- Did error rates increase?
- Did performance degrade?
- Were hotfixes needed?

Outcome tracking closes this loop, enabling the agent to learn which pre-release
signals actually predict post-release problems.

#### Tracked Outcomes

| Outcome | Source | Tracked Metrics |
|---------|--------|-----------------|
| **Incidents** | PagerDuty, Opsgenie, Incident.io | Count, severity, MTTR, related services |
| **Rollbacks** | Git, Deploy system | Time to rollback, reason, affected users |
| **Error Rates** | Sentry, Datadog, New Relic | Error count delta, new error types |
| **Performance** | APM, Prometheus | Latency p50/p95/p99, throughput |
| **Hotfixes** | Git, PRs | Count within 24h/72h/7d of release |
| **User Impact** | Analytics, Support | Ticket volume, NPS delta |

#### Outcome Collection

```yaml
outcome_tracking:
  enabled: true

  # Time windows for outcome collection
  windows:
    immediate: 1h      # Critical issues
    short_term: 24h    # Most issues surface here
    medium_term: 7d    # Slower-developing issues
    long_term: 30d     # Cumulative impact

  # Data sources
  sources:
    incidents:
      provider: pagerduty  # pagerduty | opsgenie | incident_io
      api_key: ${PAGERDUTY_API_KEY}
      service_filter: ["my-service", "my-service-*"]

    errors:
      provider: sentry
      dsn: ${SENTRY_DSN}
      project: my-project

    metrics:
      provider: datadog
      api_key: ${DATADOG_API_KEY}
      app_key: ${DATADOG_APP_KEY}

    deployments:
      provider: github  # or: argocd, spinnaker
```

#### Outcome Report

Generated for each release after outcome windows close:

```markdown
## Release Outcome Report: v1.2.0

### Release Context
- **Released**: 2025-01-01 10:30 UTC
- **Confidence Score**: 82/100
- **Changes**: 47 commits, 156 files

### Outcomes

#### Immediate (0-1h)
| Metric | Before | After | Delta | Status |
|--------|--------|-------|-------|--------|
| Error rate | 0.12% | 0.15% | +25% | ⚠️ Elevated |
| p95 latency | 145ms | 152ms | +5% | ✅ Normal |
| Incidents | 0 | 0 | - | ✅ Clear |

#### Short-term (0-24h)
| Metric | Before | After | Delta | Status |
|--------|--------|-------|-------|--------|
| Error rate | 0.12% | 0.13% | +8% | ✅ Stabilized |
| p95 latency | 145ms | 148ms | +2% | ✅ Normal |
| Incidents | 0 | 1 (P3) | +1 | ⚠️ Minor incident |
| Hotfixes | - | 0 | - | ✅ None needed |

#### Medium-term (0-7d)
| Metric | Before | After | Delta | Status |
|--------|--------|-------|-------|--------|
| Error rate | 0.12% | 0.11% | -8% | ✅ Improved |
| Support tickets | 12/day | 10/day | -17% | ✅ Improved |
| Rollback | No | No | - | ✅ Stable |

### Incident Analysis

#### INC-1234: Slow dashboard loading (P3)
- **Time to detect**: 4h 23m
- **Time to resolve**: 1h 12m
- **Root cause**: N+1 query in new analytics endpoint
- **Related commit**: `abc123` - "feat: add user analytics"
- **Learning**: Analytics features need query review

### Correlation Analysis

| Pre-Release Signal | Outcome Correlation |
|-------------------|---------------------|
| Test coverage: 78% | Incident occurred in uncovered code path |
| No perf tests | Performance regression detected |
| Security scan: clean | No security incidents |
| Review coverage: 100% | Logic error in reviewed code (false negative) |

### Learnings

1. **Query patterns in analytics code need explicit review**
   - This release: N+1 query caused P3 incident
   - Action: Add query count check to verification

2. **Coverage threshold should be enforced**
   - This release: 78% vs 80% target, incident in gap
   - Action: Raise coverage weight in confidence score

3. **Performance testing missing**
   - This release: Latency increase not caught pre-release
   - Action: Add performance benchmark to pipeline

### Updated Risk Factors

Based on this release, updating risk model:

| Factor | Previous Weight | New Weight | Reason |
|--------|----------------|------------|--------|
| Analytics changes | 1.0x | 1.5x | Higher incident correlation |
| Coverage below threshold | 1.2x | 1.5x | Confirmed predictor |
| Missing perf tests | 1.0x | 1.3x | New predictor |
```

#### Outcome Database Schema

```sql
-- Releases table
CREATE TABLE releases (
  id UUID PRIMARY KEY,
  version VARCHAR NOT NULL,
  released_at TIMESTAMP NOT NULL,
  confidence_score INTEGER,
  commit_count INTEGER,
  file_count INTEGER,
  breaking_changes BOOLEAN,
  signals JSONB
);

-- Outcomes table
CREATE TABLE outcomes (
  id UUID PRIMARY KEY,
  release_id UUID REFERENCES releases(id),
  window VARCHAR NOT NULL,  -- immediate, short_term, etc.
  collected_at TIMESTAMP NOT NULL,
  metrics JSONB,
  incidents JSONB,
  rollback BOOLEAN DEFAULT FALSE,
  hotfix_count INTEGER DEFAULT 0
);

-- Learnings table
CREATE TABLE learnings (
  id UUID PRIMARY KEY,
  release_id UUID REFERENCES releases(id),
  signal_type VARCHAR NOT NULL,
  signal_value JSONB,
  outcome_type VARCHAR NOT NULL,
  outcome_value JSONB,
  correlation_strength FLOAT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### Predictive Intelligence

The engine SHOULD use historical outcomes to predict release risk before release.

#### Why Prediction

Instead of reactive checks, predict problems before they occur:

- "PRs like this have 73% incident rate"
- "Friday releases have 2.1x rollback rate"
- "This author's changes to payment/ need extra review"

Prediction enables proactive intervention, not just reactive detection.

#### Prediction Model

```text
┌─────────────────────────────────────────────────────────────┐
│                   PREDICTION ENGINE                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Input Features                    Output Predictions        │
│  ─────────────                    ──────────────────        │
│  • Files changed                  • Incident probability     │
│  • Lines of code                  • Rollback probability     │
│  • Test coverage delta            • Error rate delta         │
│  • Authors involved               • Hotfix probability       │
│  • Time of day/week               • Confidence adjustment    │
│  • Commit patterns                                           │
│  • Dependency changes                                        │
│  • Historical outcomes                                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

#### Prediction Features

| Feature | Type | Predictive Signal |
|---------|------|-------------------|
| `files_changed_count` | Numeric | More files → higher risk |
| `files_changed_paths` | Categorical | payment/* → higher risk |
| `test_coverage_delta` | Numeric | Decrease → higher risk |
| `author_history` | Derived | Author's past incident rate |
| `time_of_release` | Temporal | Friday PM → higher risk |
| `dependency_changes` | Boolean | Major bumps → higher risk |
| `breaking_changes` | Boolean | Breaking → higher risk |
| `review_depth` | Numeric | More reviewers → lower risk |
| `ci_flakiness` | Numeric | Flaky tests → uncertainty |

#### Prediction Algorithm

```python
def predict_release_risk(
    release: PendingRelease,
    history: ReleaseHistory
) -> RiskPrediction:
    """
    Predict release risk based on historical patterns.

    Uses gradient boosting model trained on past releases
    with their outcomes.
    """

    # Extract features from pending release
    features = extract_features(release)

    # Get historical baseline for similar releases
    similar_releases = history.find_similar(
        files=release.files_changed,
        authors=release.authors,
        size=release.lines_changed
    )

    # Calculate base rates from history
    base_incident_rate = history.overall_incident_rate()
    base_rollback_rate = history.overall_rollback_rate()

    # Apply learned adjustments
    adjustments = []

    # Time-based adjustment
    if release.is_friday_afternoon():
        adjustments.append(("friday_release", 1.8))  # 80% higher risk

    # Path-based adjustment
    for path_pattern, multiplier in history.risky_paths():
        if release.touches_path(path_pattern):
            adjustments.append((path_pattern, multiplier))

    # Author-based adjustment
    for author in release.authors:
        author_history = history.author_stats(author)
        if author_history.incident_rate > base_incident_rate * 1.5:
            adjustments.append((f"author:{author}", 1.3))

    # Coverage-based adjustment
    if release.coverage_delta < 0:
        adjustments.append(("coverage_decrease", 1.4))

    # Calculate final predictions
    incident_prob = base_incident_rate
    for factor, multiplier in adjustments:
        incident_prob *= multiplier

    return RiskPrediction(
        incident_probability=min(incident_prob, 0.95),
        rollback_probability=calculate_rollback_prob(similar_releases),
        confidence_adjustment=calculate_confidence_adj(adjustments),
        risk_factors=adjustments,
        similar_releases=similar_releases[:5],
        recommendation=generate_recommendation(incident_prob)
    )
```

#### Prediction Output

```markdown
## Predictive Risk Assessment

### Overall Risk: ELEVATED (67th percentile)

This release is riskier than 67% of past releases based on:

### Risk Factors

| Factor | Impact | Historical Basis |
|--------|--------|------------------|
| 🔴 Changes to `payment/` | +50% risk | 73% incident rate for payment changes |
| 🟡 Friday 4pm release | +30% risk | 2.1x rollback rate for Fri PM releases |
| 🟡 Coverage decreased 3% | +20% risk | Uncovered code correlates with incidents |
| 🟢 All tests passing | -10% risk | Strong negative predictor |
| 🟢 3 reviewers approved | -15% risk | Review depth reduces incidents |

### Predicted Outcomes

| Outcome | Probability | Confidence |
|---------|-------------|------------|
| Incident within 24h | 23% | High (n=147 similar) |
| Rollback needed | 8% | Medium (n=52 similar) |
| Hotfix within 72h | 31% | High (n=147 similar) |
| Error rate increase >10% | 15% | Medium (n=89 similar) |

### Similar Past Releases

| Version | Similarity | Outcome |
|---------|------------|---------|
| v1.1.3 | 89% | ✅ Clean release |
| v1.0.8 | 85% | ⚠️ P3 incident, no rollback |
| v0.9.2 | 82% | ❌ Rolled back after 2h |
| v1.1.1 | 78% | ✅ Clean release |
| v0.8.5 | 75% | ⚠️ Hotfix needed day 2 |

### Recommendations

1. **Delay to Monday**: Friday PM releases have 2.1x rollback rate
   - Alternative: Deploy to staging only, release Monday AM

2. **Add payment integration tests**: `payment/` changes without integration tests have 73% incident rate
   - Specific: Add test for refund edge case in changed code

3. **Increase monitoring**: Set up dashboards before release
   - Watch: Error rates, payment success rate, latency p99

### Confidence Score Adjustment

Based on predictions, adjusting confidence score:

| Original Score | Adjustment | Final Score |
|----------------|------------|-------------|
| 82 | -12 (elevated risk) | 70 |

**New recommendation**: Release with review (was: auto-release eligible)
```

#### Prediction Configuration

```yaml
prediction:
  enabled: true

  # Minimum history before predictions
  min_releases: 20
  min_incidents: 5

  # Feature weights (learned, can override)
  feature_weights:
    path_risk: 0.25
    time_risk: 0.15
    author_risk: 0.10
    coverage_risk: 0.20
    dependency_risk: 0.15
    review_depth: 0.15

  # Risky paths (learned + configured)
  risky_paths:
    - pattern: "payment/**"
      base_multiplier: 1.5
    - pattern: "auth/**"
      base_multiplier: 1.4
    - pattern: "database/migrations/**"
      base_multiplier: 1.6

  # Risky times
  risky_times:
    - day: friday
      after: "14:00"
      multiplier: 1.8
    - day: "*"
      after: "17:00"
      multiplier: 1.3

  # Thresholds for recommendations
  thresholds:
    delay_release: 0.40      # >40% incident probability
    require_review: 0.25     # >25% incident probability
    enhanced_monitoring: 0.15 # >15% incident probability

  # Model retraining
  retrain:
    schedule: weekly
    min_new_outcomes: 10
```

#### Learning Loop

```text
┌─────────────────────────────────────────────────────────────┐
│                    LEARNING LOOP                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌─────────┐     ┌─────────┐     ┌─────────┐              │
│   │ Release │ ──▶ │ Predict │ ──▶ │ Deploy  │              │
│   └─────────┘     └─────────┘     └─────────┘              │
│        ▲                               │                    │
│        │                               ▼                    │
│   ┌─────────┐     ┌─────────┐     ┌─────────┐              │
│   │ Retrain │ ◀── │ Compare │ ◀── │ Observe │              │
│   └─────────┘     └─────────┘     └─────────┘              │
│                                                              │
│   1. Make prediction before release                         │
│   2. Deploy and observe outcomes                            │
│   3. Compare predictions vs actual outcomes                 │
│   4. Retrain model on new data                              │
│   5. Repeat with improved predictions                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Decision Engine

The Decision Engine synthesizes analysis into actionable outputs.

### Confidence Score

Every release assessment MUST include a confidence score.

#### Score Calculation

```text
Confidence Score = weighted_average(
  test_score      × 0.30,
  security_score  × 0.25,
  review_score    × 0.20,
  commit_score    × 0.15,
  deps_score      × 0.10
)
```

#### Score Interpretation

| Score | Interpretation | Recommended Action |
|-------|----------------|-------------------|
| 90-100 | High confidence | Auto-release eligible |
| 70-89 | Good confidence | Release with monitoring |
| 50-69 | Moderate confidence | Review recommended |
| 30-49 | Low confidence | Address issues first |
| 0-29 | Critical issues | Release blocked |

#### Score Output

```json
{
  "confidence_score": 82,
  "interpretation": "good",
  "breakdown": {
    "tests": { "score": 95, "weight": 0.30, "contribution": 28.5 },
    "security": { "score": 78, "weight": 0.25, "contribution": 19.5 },
    "reviews": { "score": 85, "weight": 0.20, "contribution": 17.0 },
    "commits": { "score": 70, "weight": 0.15, "contribution": 10.5 },
    "dependencies": { "score": 65, "weight": 0.10, "contribution": 6.5 }
  },
  "blockers": [],
  "warnings": [
    "2 dependencies have major version updates",
    "Code coverage decreased by 3%"
  ],
  "recommendation": "Release with enhanced monitoring"
}
```

### Blocker Detection

The engine MUST identify release blockers.

#### Blocker Categories

```yaml
blockers:
  critical:
    - failing_required_workflow
    - critical_vulnerability
    - unresolved_security_finding
    - missing_required_approval

  high:
    - high_vulnerability
    - failing_tests
    - coverage_below_threshold
    - unresolved_review_comments

  configurable:
    - major_dependency_update
    - new_unreviewed_dependency
    - missing_changelog_entry
```

#### Blocker Output

```json
{
  "blockers": [
    {
      "id": "SEC-001",
      "category": "security",
      "severity": "critical",
      "title": "Critical vulnerability in lodash",
      "description": "CVE-2021-XXXXX allows prototype pollution",
      "remediation": "Update lodash to 4.17.21 or later",
      "affected_files": ["package.json", "package-lock.json"],
      "auto_fixable": true
    }
  ],
  "blocker_count": 1,
  "release_blocked": true
}
```

### Version Calculation

The engine MUST calculate the appropriate semantic version.

#### Version Logic

```python
def calculate_version(
    current: SemVer,
    signals: Signals,
    config: Config
) -> VersionRecommendation:
    """
    Calculate next version based on changes.

    Rules:
    1. Breaking changes → Major bump
    2. New features → Minor bump
    3. Bug fixes only → Patch bump
    4. Pre-release handling
    5. Build metadata
    """

    if signals.has_breaking_changes:
        return VersionRecommendation(
            version=current.bump_major(),
            reason="Breaking changes detected",
            breaking_changes=signals.breaking_changes
        )

    if signals.has_features:
        return VersionRecommendation(
            version=current.bump_minor(),
            reason="New features added",
            features=signals.features
        )

    return VersionRecommendation(
        version=current.bump_patch(),
        reason="Bug fixes and improvements"
    )
```

---

## Changelog Generation

The agent MUST generate human-quality changelogs using LLM understanding.

### Changelog Format

#### Keep a Changelog Format (Default)

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.0] - 2025-01-02

### Added
- User profile editing with avatar upload support (#234)
- Rate limiting for API endpoints to prevent abuse (#256)

### Changed
- Improved error messages for authentication failures (#245)
- Updated dashboard layout for better mobile experience (#251)

### Fixed
- Resolved race condition in concurrent session handling (#242)
- Fixed timezone display in event scheduling (#248)

### Security
- Patched XSS vulnerability in comment rendering (#253)

## [1.1.0] - 2024-12-15
...
```

### Generation Process

```python
def generate_changelog(
    commits: List[Commit],
    prs: List[PullRequest],
    config: ChangelogConfig
) -> Changelog:
    """
    Generate changelog using LLM understanding.

    Process:
    1. Group changes by category
    2. Summarize each change for end users
    3. Link to PRs/issues
    4. Highlight breaking changes
    5. Format per configured style
    """

    # Use LLM for semantic grouping
    grouped = llm.group_changes(commits, prs)

    # Generate user-facing descriptions
    entries = []
    for group in grouped:
        entry = llm.generate_entry(
            changes=group.changes,
            audience=config.audience,  # "developers" | "users" | "both"
            style=config.style,        # "concise" | "detailed"
            max_length=config.max_entry_length
        )
        entries.append(entry)

    return Changelog(
        version=calculated_version,
        date=today(),
        entries=entries,
        breaking_changes=extract_breaking(entries),
        contributors=extract_contributors(commits)
    )
```

### LLM Changelog Prompt

```markdown
Generate a changelog entry for the following changes.

Audience: {audience}
Style: {style}

Changes:
{changes_json}

Requirements:
1. Write for end users, not developers (unless audience=developers)
2. Focus on what changed, not how it was implemented
3. Use active voice and present tense
4. Keep entries concise but informative
5. Group related changes together
6. Highlight breaking changes prominently
7. Include issue/PR references where relevant

Output format:
{format_template}
```

### Configuration

```yaml
changelog:
  # Output file path
  file: CHANGELOG.md

  # Format style
  format: keep-a-changelog  # or: conventional, github-releases, custom

  # Entry generation
  audience: users  # or: developers, both
  style: concise   # or: detailed
  max_entry_length: 200

  # Sections to include
  sections:
    - Added
    - Changed
    - Deprecated
    - Removed
    - Fixed
    - Security

  # Include contributor list
  include_contributors: true

  # Link format for issues/PRs
  link_format: "[#{number}]({url})"

  # Header template
  header_template: |
    ## [{version}] - {date}
```

---

## Release Workflows

The agent supports multiple release workflow patterns.

### Continuous Release

Automatically release on every qualifying merge to main.

```yaml
workflow: continuous
trigger:
  branches: [main]
  paths_ignore:
    - "docs/**"
    - "*.md"
conditions:
  min_confidence_score: 90
  require_all_checks_pass: true
  require_no_blockers: true
actions:
  - calculate_version
  - generate_changelog
  - create_git_tag
  - create_github_release
  - publish_packages
  - notify_slack
```

### Scheduled Release

Release on a defined schedule (e.g., weekly).

```yaml
workflow: scheduled
schedule:
  cron: "0 10 * * 1"  # Every Monday at 10 AM
conditions:
  min_changes: 1
  min_confidence_score: 70
actions:
  - create_release_pr
  - await_approval
  - execute_release
```

### Manual Release

Human-triggered release with AI assistance.

```yaml
workflow: manual
trigger:
  workflow_dispatch:
    inputs:
      version_override:
        description: "Override calculated version"
        required: false
      skip_checks:
        description: "Skip non-critical checks"
        required: false
        default: false
actions:
  - analyze_changes
  - present_report
  - await_confirmation
  - execute_release
```

### Release Train

Batched releases with multiple stages.

```yaml
workflow: release_train
stages:
  - name: staging
    auto_deploy: true
    duration: 24h
    rollback_threshold: 5  # % error rate

  - name: canary
    auto_deploy: true
    traffic_percentage: 10
    duration: 48h
    rollback_threshold: 2

  - name: production
    auto_deploy: false
    require_approval: true
    approvers:
      - "@release-team"
```

---

## Integrations

### GitHub Integration

Primary integration for GitHub-hosted repositories.

#### Required Permissions

```yaml
permissions:
  contents: write      # Create releases, tags
  pull-requests: write # Create release PRs
  issues: read         # Link issues in changelog
  actions: read        # Read workflow status
  security-events: read # Read security alerts
```

#### GitHub Actions Workflow

```yaml
name: Release Manager

on:
  push:
    branches: [main]
  workflow_dispatch:
    inputs:
      dry_run:
        description: "Perform dry run only"
        type: boolean
        default: false

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for changelog

      - name: Run Release Manager Agent
        uses: doctrine/release-manager-agent@v1
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          config_file: .release-manager.yml
          dry_run: ${{ inputs.dry_run }}
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

### GitLab Integration

```yaml
# .gitlab-ci.yml
release:
  stage: release
  image: doctrine/release-manager-agent:latest
  script:
    - release-manager analyze
    - release-manager release --if-ready
  only:
    - main
  variables:
    GITLAB_TOKEN: $CI_JOB_TOKEN
    ANTHROPIC_API_KEY: $ANTHROPIC_API_KEY
```

### Slack Integration

```yaml
notifications:
  slack:
    enabled: true
    webhook_url: ${SLACK_WEBHOOK_URL}
    channel: "#releases"
    events:
      - release_started
      - release_completed
      - release_failed
      - blocker_detected
    template: |
      :rocket: *{project}* {version} released!

      {changelog_summary}

      <{release_url}|View Release>
```

### JIRA Integration

```yaml
integrations:
  jira:
    enabled: true
    host: https://company.atlassian.net
    auth:
      type: api_token
      email: ${JIRA_EMAIL}
      token: ${JIRA_API_TOKEN}
    actions:
      - link_issues_to_release
      - transition_issues_on_release
      - add_release_comment
    transition_mapping:
      on_release: "Done"
```

---

## Configuration

### Configuration File

The agent MUST be configured via `.release-manager.yml` in the repository root.

#### Complete Configuration Reference

```yaml
# .release-manager.yml

# Agent version
version: "1.0"

# Project metadata
project:
  name: my-project
  type: library  # library | application | monorepo

# LLM configuration
llm:
  provider: anthropic  # anthropic | openai | azure
  model: claude-sonnet-4-5-20250329
  temperature: 0.3
  # Fallback model for simple tasks
  fallback_model: claude-haiku-3-5-20241022

# Signal collectors configuration
signal_collectors:
  git:
    enabled: true
    branch: main
    tag_pattern: "v*"

  cicd:
    enabled: true
    platform: github_actions
    required_workflows:
      - "CI"
      - "Tests"

  security:
    enabled: true
    blocking_severities: [critical, high]

  code_review:
    enabled: true
    min_approvals: 1

  dependencies:
    enabled: true
    package_managers: [npm]

# Decision engine configuration
decision:
  # Confidence score thresholds
  thresholds:
    auto_release: 90
    release_with_review: 70
    block_release: 30

  # Weight adjustments
  weights:
    tests: 0.30
    security: 0.25
    reviews: 0.20
    commits: 0.15
    dependencies: 0.10

# Changelog configuration
changelog:
  file: CHANGELOG.md
  format: keep-a-changelog
  audience: users
  style: concise
  include_contributors: true

# Release configuration
release:
  # Version file locations
  version_files:
    - package.json
    - VERSION

  # Git configuration
  git:
    tag_prefix: "v"
    sign_tags: false
    commit_message: "chore(release): {version}"

  # GitHub Release
  github_release:
    enabled: true
    draft: false
    prerelease_pattern: "*-*"  # e.g., 1.0.0-beta.1

  # Package publishing
  publish:
    npm:
      enabled: true
      registry: https://registry.npmjs.org
      access: public

# Workflow configuration
workflow:
  type: continuous  # continuous | scheduled | manual | release_train

  # Continuous workflow settings
  continuous:
    auto_release_threshold: 90
    create_pr_threshold: 70

# Notifications
notifications:
  slack:
    enabled: true
    webhook_url: ${SLACK_WEBHOOK_URL}
    channel: "#releases"

# Advanced settings
advanced:
  # Enable historical learning
  historical_learning: true

  # Cache LLM responses
  cache_responses: true
  cache_ttl: 3600

  # Dry run mode
  dry_run: false

  # Debug logging
  debug: false
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes* | Anthropic API key |
| `OPENAI_API_KEY` | Yes* | OpenAI API key |
| `GITHUB_TOKEN` | Yes | GitHub access token |
| `SLACK_WEBHOOK_URL` | No | Slack notification webhook |
| `JIRA_API_TOKEN` | No | JIRA integration token |

*One LLM provider key required

---

## Security Considerations

### Secrets Management

The agent MUST NOT:

- Log API keys or tokens
- Include secrets in changelogs
- Expose secrets in error messages
- Store secrets in plaintext

The agent MUST:

- Use environment variables for secrets
- Support secret managers (Vault, AWS Secrets Manager)
- Mask secrets in output
- Rotate tokens regularly

### LLM Data Privacy

When using LLM providers:

```yaml
llm:
  privacy:
    # Don't send actual code to LLM
    send_code: false  # Send summaries only

    # Exclude sensitive paths
    exclude_paths:
      - "**/secrets/**"
      - "**/*.env*"
      - "**/credentials*"

    # Redact patterns
    redact_patterns:
      - "password[=:].*"
      - "api[_-]?key[=:].*"
      - "secret[=:].*"
```

### Audit Logging

The agent SHOULD log all actions:

```yaml
audit:
  enabled: true
  destinations:
    - file: /var/log/release-manager/audit.log
    - syslog: true
  events:
    - release_started
    - release_completed
    - release_failed
    - config_changed
    - manual_override
```

---

## CLI Reference

### Commands

```bash
# Analyze release readiness
release-manager analyze [--output json|text|markdown]

# Generate changelog preview
release-manager changelog [--dry-run] [--since <tag>]

# Calculate next version
release-manager version [--bump major|minor|patch]

# Execute release
release-manager release [--dry-run] [--force]

# Show release report
release-manager report [--format html|json|markdown]

# Validate configuration
release-manager validate

# Initialize configuration
release-manager init [--preset minimal|standard|enterprise]
```

### Example Usage

```bash
# Quick release check
$ release-manager analyze
✓ Collected 47 commits since v1.1.0
✓ All CI checks passing
✓ No security blockers
✓ 12 PRs with required approvals

Release Readiness: 87/100 (Good)
Recommended Version: 1.2.0 (minor - new features)

Proceed with release? [y/N]

# Generate changelog preview
$ release-manager changelog --dry-run
## [1.2.0] - 2025-01-02

### Added
- User profile editing with avatar upload (#234)
- Rate limiting for API endpoints (#256)

### Fixed
- Race condition in session handling (#242)
- Timezone display in event scheduling (#248)

# Execute release
$ release-manager release
✓ Version bumped to 1.2.0
✓ CHANGELOG.md updated
✓ Git tag v1.2.0 created
✓ GitHub Release published
✓ Package published to npm
✓ Slack notification sent

Release v1.2.0 completed successfully!
```

---

## Metrics & Observability

### Exported Metrics

```yaml
metrics:
  enabled: true
  format: prometheus  # prometheus | statsd | cloudwatch

  # Available metrics
  # release_manager_releases_total
  # release_manager_confidence_score
  # release_manager_blockers_detected
  # release_manager_changelog_generation_seconds
  # release_manager_llm_tokens_used
  # release_manager_release_duration_seconds
```

### Dashboard Queries

```promql
# Release frequency
rate(release_manager_releases_total[7d])

# Average confidence score
avg_over_time(release_manager_confidence_score[30d])

# Blocker detection rate
sum(release_manager_blockers_detected) by (severity)
```

---

## See Also

- [AI Workflows](ai-workflows.md) - General AI development patterns
- [Claude Best Practices](claude.md) - LLM usage guidelines
- [Versioning Guide](../process/versioning.md) - Semantic versioning standards
- [CI Guide](../process/ci.md) - Continuous integration patterns
- [GitHub Templates](../process/github-templates.md) - PR and issue templates

---

## References

- [Semantic Versioning 2.0.0](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [semantic-release](https://github.com/semantic-release/semantic-release)
- [release-please](https://github.com/googleapis/release-please)
- [changesets](https://github.com/changesets/changesets)

---

*Version: 1.0.0*
*Last Updated: 2025-01-02*
*Status: Draft Specification*
