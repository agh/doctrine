# Testing Guide

> [Doctrine](../../README.md) > [Process](../README.md) > Testing

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

Cross-cutting testing concepts. Language-specific implementations are in each
language guide.

## Core Principle: Local-First Testing

**All tests MUST run locally without external dependencies.**

- Unit tests: **MUST NOT** use network, Docker, or databases
- Integration tests: **MUST** use testcontainers or local services
- Tests **MUST NOT** require cloud accounts or remote APIs
- External services **MUST** be mocked; test data **MUST** use fixtures
- CI **MUST** reproduce local test environment exactly

## Testing Pyramid

The testing pyramid[^1] is a framework for balancing test types:

```text
          /\
         /  \           E2E (few, slow, expensive)
        /----\
       /      \         Acceptance (user journeys)
      /--------\
     /          \       Integration (component interactions)
    /------------\
   /              \     Unit (many, fast, cheap)
  /----------------\
```

## Test Types

### Unit Tests

Test individual functions/methods in isolation[^2].

- **MUST** be fast: Milliseconds per test
- **MUST** be isolated: No external dependencies, no I/O
- **MUST** be repeatable: Same result every time
- **MUST** be self-validating: Pass or fail, no manual checking

### Integration Tests

Test component interactions with real dependencies[^3].

- Database operations with testcontainers[^4]
- API endpoint testing with test clients
- Message queue interactions
- Cache layer behavior

### E2E Tests

Test complete user flows through the entire system[^5].

- Browser automation (Playwright[^6], Cypress[^7])
- Full stack deployed locally
- Happy path coverage
- Critical business flows only

### Acceptance Tests

Verify business requirements using BDD style[^8].

- Given/When/Then format[^9]
- Written in domain language
- Cucumber[^10], SpecFlow[^11], pytest-bdd[^12]
- Living documentation

### Performance Tests

Measure and validate performance characteristics[^13].

| Type      | Purpose                  | Tools                                                 |
| --------- | ------------------------ | ----------------------------------------------------- |
| Benchmark | Measure function speed   | pytest-benchmark[^14], criterion[^15], testing.B[^16] |
| Load      | Test under expected load | k6[^17], locust[^18], Gatling[^19]                    |
| Stress    | Find breaking points     | k6[^17], Artillery[^20]                               |
| Soak      | Detect memory leaks      | Extended load tests                                   |

### Thread Safety Tests

Verify concurrent access is safe[^21].

- Race condition detection (Go's `-race`[^22], TSAN[^23])
- Deadlock detection
- Concurrent access patterns
- Lock contention testing

### Idempotence Tests

Verify operations can be safely retried[^24].

- Same result on repeated calls
- No duplicate side effects
- Database upsert patterns
- API idempotency keys

### Reliability & Resilience Tests

Verify behavior under failure conditions[^25].

- **Chaos engineering**[^26]: Random failure injection
- **Fault injection**: Network delays, timeouts, errors
- **Circuit breaker testing**[^27]: Verify fallback behavior
- **Retry testing**: Backoff and recovery

### Compatibility Tests

Verify across environments and versions[^28].

- Language version matrix (Python 3.12, 3.13, 3.14)
- OS matrix (Linux, macOS, Windows)
- Browser matrix (Chrome, Firefox, Safari)
- API version compatibility
- Database version compatibility

### Internationalization Tests

Verify i18n/l10n correctness[^29].

- UTF-8 handling throughout
- Unicode edge cases (emoji, RTL, combining chars)
- Locale-specific formatting (dates, numbers, currency)
- Translation string coverage
- Timezone handling

### Data Integrity Tests

Verify data correctness and consistency[^30].

- Database constraint enforcement
- Migration up/down testing
- Referential integrity
- Backup/restore verification
- Transaction isolation

### A/B Testing & Feature Flags

Test feature flag behavior[^31].

- Both flag states (on/off)
- Gradual rollout percentages
- User segment targeting
- Flag cleanup tracking

## Test Organization

### Directory Structure

```text
tests/
├── unit/              # Fast, isolated tests
├── integration/       # Component interaction tests
├── e2e/               # End-to-end browser tests
├── acceptance/        # BDD feature tests
├── performance/       # Benchmarks, load tests
├── fixtures/          # Shared test data
└── conftest.py        # Shared fixtures (Python)
```

### Test Markers/Tags

Use markers to categorize and selectively run tests:

```bash
# Python
pytest -m unit
pytest -m "not slow"

# Go
go test -run TestUnit
go test -short

# JavaScript
vitest --grep "unit"
```

## CI Strategy

```yaml
jobs:
  # Fast feedback first
  lint:
    runs-on: ubuntu-latest
    steps:
      - run: ruff check .

  unit:
    needs: lint
    runs-on: ubuntu-latest
    steps:
      - run: pytest -m unit -n auto

  integration:
    needs: unit
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
    steps:
      - run: pytest -m integration

  e2e:
    needs: integration
    runs-on: ubuntu-latest
    steps:
      - run: playwright test

  # Slow tests on main only
  performance:
    if: github.ref == 'refs/heads/main'
    needs: e2e
    steps:
      - run: pytest tests/performance/
```

## Coverage Goals

| Type        | Target         | Notes                   |
| ----------- | -------------- | ----------------------- |
| Unit        | 80%+           | Focus on business logic |
| Integration | Critical paths | Database, APIs          |
| E2E         | Happy paths    | Don't over-invest       |
| Regression  | All fixed bugs | Prevent recurrence      |

**Coverage is a metric, not a goal.**[^32] Focus on testing behavior, not hitting
arbitrary numbers. 100% coverage doesn't mean 100% correct.

## Flaky Test Policy

Flaky tests[^33] undermine confidence. Handle them aggressively:

1. **MUST** quarantine immediately: Move to separate suite
2. **MUST** fix within 48 hours or delete
3. **MUST NOT** ignore: A flaky test is worse than no test
4. **SHOULD** track patterns: Network? Timing? Order-dependent?

## Test Data Management

- **Fixtures**[^34]: Static data files for deterministic tests
- **Factories**[^35]: Generate test data programmatically
- **Builders**[^36]: Fluent API for complex objects
- **Fakers**[^37]: Random but realistic data

You **SHOULD** prefer factories over fixtures for flexibility. You **SHOULD** use
fixtures for complex scenarios that need exact reproduction.

## See Also

- [CI/CD Guide](ci.md) - CI workflow configuration and best practices
- [Versioning Guide](versioning.md) - Semantic versioning and changelog management
- [GitHub Templates](github-templates.md) - Issue and PR templates

## References

[^1]: **Testing Pyramid** - Cohn, M. (2009). *Succeeding with Agile: Software Development Using Scrum*. Addison-Wesley. Also see [Martin Fowler's Test Pyramid](https://martinfowler.com/bliki/TestPyramid.html)

[^2]: **Unit Testing** - [Unit Testing - Martin Fowler](https://martinfowler.com/bliki/UnitTest.html)

[^3]: **Integration Testing** - [Integration Testing - Software Testing Fundamentals](https://softwaretestingfundamentals.com/integration-testing/)

[^4]: **Testcontainers** - [Testcontainers](https://testcontainers.com/) - Docker containers for integration testing

[^5]: **End-to-End Testing** - [E2E Testing Guide - Cypress Documentation](https://docs.cypress.io/guides/core-concepts/testing-types#What-is-E2E-Testing)

[^6]: **Playwright** - [Playwright](https://playwright.dev/) - Microsoft's end-to-end testing framework

[^7]: **Cypress** - [Cypress](https://www.cypress.io/) - JavaScript E2E testing framework

[^8]: **Behavior-Driven Development (BDD)** - North, D. (2006). [Introducing BDD](https://dannorth.net/introducing-bdd/)

[^9]: **Given-When-Then** - [Given-When-Then - Martin Fowler](https://martinfowler.com/bliki/GivenWhenThen.html)

[^10]: **Cucumber** - [Cucumber BDD Framework](https://cucumber.io/)

[^11]: **SpecFlow** - [SpecFlow - BDD for .NET](https://specflow.org/)

[^12]: **pytest-bdd** - [pytest-bdd](https://pytest-bdd.readthedocs.io/) - BDD library for pytest

[^13]: **Performance Testing** - [Performance Testing Guidance - Microsoft Docs](https://learn.microsoft.com/en-us/azure/architecture/best-practices/performance-testing)

[^14]: **pytest-benchmark** - [pytest-benchmark](https://pytest-benchmark.readthedocs.io/) - Python benchmarking plugin

[^15]: **Criterion** - [Criterion.rs](https://github.com/bheisler/criterion.rs) - Rust benchmarking library

[^16]: **testing.B** - [Go Benchmarks](https://pkg.go.dev/testing#hdr-Benchmarks) - Go's built-in benchmarking

[^17]: **k6** - [k6](https://k6.io/) - Modern load testing tool

[^18]: **Locust** - [Locust](https://locust.io/) - Python load testing framework

[^19]: **Gatling** - [Gatling](https://gatling.io/) - Load testing tool for web applications

[^20]: **Artillery** - [Artillery](https://www.artillery.io/) - Modern load testing toolkit

[^21]: **Thread Safety Testing** - [ThreadSanitizer - Google's Race Detector](https://github.com/google/sanitizers/wiki/ThreadSanitizerCppManual)

[^22]: **Go Race Detector** - [Data Race Detector - Go Documentation](https://go.dev/doc/articles/race_detector)

[^23]: **ThreadSanitizer (TSAN)** - [ThreadSanitizer](https://clang.llvm.org/docs/ThreadSanitizer.html) - Clang's thread safety tool

[^24]: **Idempotence** - [Idempotence - RESTful API Design](https://restfulapi.net/idempotent-rest-apis/)

[^25]: **Resilience Testing** - [Chaos Engineering Principles](https://principlesofchaos.org/)

[^26]: **Chaos Engineering** - Basiri, A., et al. (2016). [Chaos Engineering - Netflix Technology Blog](https://netflixtechblog.com/tagged/chaos-engineering)

[^27]: **Circuit Breaker Pattern** - [Circuit Breaker - Martin Fowler](https://martinfowler.com/bliki/CircuitBreaker.html)

[^28]: **Compatibility Testing** - [Compatibility Testing Guide - Software Testing Help](https://www.softwaretestinghelp.com/what-is-compatibility-testing/)

[^29]: **Internationalization (i18n) Testing** - [Internationalization Testing - W3C](https://www.w3.org/International/questions/qa-i18n)

[^30]: **Data Integrity Testing** - [Database Testing Best Practices](https://www.sqlshack.com/database-unit-testing-best-practices/)

[^31]: **Feature Flag Testing** - [Feature Toggles - Martin Fowler](https://martinfowler.com/articles/feature-toggles.html)

[^32]: **Test Coverage** - Marick, B. (1999). [How to Misuse Code Coverage](http://www.exampler.com/testing-com/writings/coverage.pdf)

[^33]: **Flaky Tests** - [Eradicating Non-Determinism in Tests - Martin Fowler](https://martinfowler.com/articles/nonDeterminism.html)

[^34]: **Test Fixtures** - [Test Fixture - xUnit Patterns](http://xunitpatterns.com/test%20fixture%20-%20xUnit.html)

[^35]: **Test Factories** - [Factory Pattern for Test Data](https://thoughtbot.com/blog/factories-should-be-the-bare-minimum)

[^36]: **Builder Pattern** - Gamma, E., et al. (1994). *Design Patterns: Elements of Reusable Object-Oriented Software*. [Builder Pattern](https://refactoring.guru/design-patterns/builder)

[^37]: **Faker Libraries** - [Faker](https://fakerjs.dev/) (JavaScript), [Faker](https://faker.readthedocs.io/) (Python) - Generate realistic fake data for testing
