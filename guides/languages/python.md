# Python Style Guide

> [Doctrine](../../README.md) > [Languages](../README.md) > Python

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

Extends [Google Python Style Guide](google/python.md).

## Quick Reference

| Task | Tool | Command |
|------|------|---------|
| Lint | Ruff[^1] | `uv run ruff check . --fix` |
| Format | Ruff[^1] | `uv run ruff format .` |
| Type check | Mypy[^2] | `uv run mypy src/` |
| Type check | Pyright[^3] | `uv run pyright` |
| Semantic | Semgrep[^4] | `uv run semgrep --config=p/python src/` |
| Dead code | Vulture[^5] | `uv run vulture src/` |
| Coverage | pytest-cov[^6] | `uv run pytest --cov=src` |
| Complexity | Radon[^7] | `uv run radon cc src/ -a` |
| Fuzz | Hypothesis[^8] | `uv run pytest` (with hypothesis tests) |
| Test perf | pytest-xdist[^9] | `uv run pytest -n auto` |

## Package Management: uv

Projects **MUST** use uv[^10] for all Python package management.

**Why**: uv is the world-class Python package manager, 10-100x faster than pip[^11]. It provides deterministic dependency resolution, faster installs, and a superior developer experience compared to pip, poetry, or pipenv.

```bash
# Create new project
uv init myproject
cd myproject

# Add dependencies
uv add requests pydantic

# Add dev dependencies
uv add --dev pytest ruff mypy

# Sync environment
uv sync

# Run commands in environment
uv run pytest
uv run ruff check .
```

### pyproject.toml

All configuration **MUST** live in `pyproject.toml`. Projects **MUST NOT** use `setup.py`, `setup.cfg`, `requirements.txt`, or tool-specific config files.

**Why**: Centralizing all project configuration in `pyproject.toml` (PEP 518/621)[^12] eliminates configuration sprawl, reduces maintenance burden, and aligns with modern Python packaging standards.

## Linting: Ruff

Projects **MUST** use Ruff[^1] for linting.

**Why**: Ruff replaces Flake8, isort, pyupgrade, and many other tools in a single, fast implementation. Written in Rust, it's 10-100x faster than alternatives[^13] while providing comprehensive Python linting rules.

```toml
[tool.ruff]
target-version = "py314"
line-length = 100
src = ["src", "tests"]

[tool.ruff.lint]
select = [
    "E", "F", "W",      # pycodestyle, Pyflakes
    "I",                # isort
    "UP",               # pyupgrade
    "B",                # flake8-bugbear
    "C4",               # flake8-comprehensions
    "SIM",              # flake8-simplify
    "S",                # flake8-bandit (security)
    "N",                # pep8-naming
    "D",                # pydocstyle
    "ANN",              # flake8-annotations
    "RUF",              # Ruff-specific
]

[tool.ruff.lint.pydocstyle]
convention = "google"
```

## Formatting: Ruff

Projects **MUST** use Ruff[^1] for code formatting.

**Why**: Ruff format is a drop-in replacement for Black[^14], but faster. Using the same tool for both linting and formatting simplifies tooling and improves performance.

```toml
[tool.ruff.format]
quote-style = "double"
indent-style = "space"
line-ending = "auto"
```

## Type Checking: Mypy + Pyright

Projects **MUST** use both Mypy[^2] and Pyright[^3] for type checking.

**Why**: Mypy and Pyright catch different classes of type errors due to their different implementations and type inference strategies[^15]. Using both provides maximum type safety coverage.

### Mypy (strict mode)

Projects **MUST** enable Mypy strict mode.

```toml
[tool.mypy]
strict = true
python_version = "3.14"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
```

### Pyright

Projects **MUST** enable Pyright strict mode.

```toml
[tool.pyright]
include = ["src"]
pythonVersion = "3.14"
typeCheckingMode = "strict"
```

### Type Hint Conventions

Projects **MUST** follow these type hint conventions:

```python
from collections.abc import Sequence, Mapping

# MUST use X | None, not Optional[X]
def get_user(id: int) -> User | None: ...

# MUST use collections.abc, not typing
def process(items: Sequence[str]) -> Mapping[str, int]: ...
```

**Note**: As of Python 3.14, PEP 649 deferred annotation evaluation is enabled by default. The `from __future__ import annotations` import is **no longer required** for forward references or avoiding import cycles in type hints.

### PEP 695 Type Parameter Syntax (Python 3.12+)

Projects targeting Python 3.12+ **SHOULD** use the new type parameter syntax for generics and type aliases.

**Why**: PEP 695 provides a cleaner, more concise syntax for defining generic classes, functions, and type aliases. The new syntax eliminates boilerplate imports and makes type parameters more explicit and easier to read.

```python
# Old style (pre-3.12)
from typing import TypeVar, Generic

T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')

class Box(Generic[T]):
    def __init__(self, value: T) -> None:
        self.value = value

def first(items: list[T]) -> T:
    return items[0]

# New style (3.12+) - RECOMMENDED
class Box[T]:
    def __init__(self, value: T) -> None:
        self.value = value

def first[T](items: list[T]) -> T:
    return items[0]

def process_mapping[K, V](data: dict[K, V]) -> list[V]:
    return list(data.values())

# Type aliases with type parameters
type Point[T] = tuple[T, T]
type JSONDict = dict[str, str | int | float | bool | None]
type Result[T, E] = T | Exception
```

### PEP 742 TypeIs for Type Narrowing (Python 3.13+)

Projects targeting Python 3.13+ **SHOULD** use `TypeIs` for user-defined type guards that narrow types.

**Why**: `TypeIs` provides more accurate type narrowing than `TypeGuard`. It correctly narrows the type in the else branch and works better with union types, improving type checker accuracy.

```python
from typing import TypeIs

def is_string(val: object) -> TypeIs[str]:
    return isinstance(val, str)

def process(value: str | int) -> None:
    if is_string(value):
        # Type checker knows value is str here
        print(value.upper())
    else:
        # Type checker knows value is int here
        print(value + 1)

# More complex example
def is_non_empty_list[T](val: list[T] | None) -> TypeIs[list[T]]:
    return val is not None and len(val) > 0
```

### PEP 750 Template Strings (Python 3.14+)

Projects targeting Python 3.14+ **MAY** use template strings (t-strings) for safe string interpolation.

**Why**: Template strings provide a safer alternative to f-strings for user-generated content, enabling validation and escaping before interpolation. They return `Template` objects rather than strings, allowing deferred evaluation and security checks.

```python
from string.templatelib import Template

name = "world"
template = t"Hello {name}"  # Returns Template, not str

# Template can be validated before interpolation
if template.is_safe():
    result = str(template)  # "Hello world"

# Useful for SQL query building, HTML generation, etc.
user_input = get_user_input()
query_template = t"SELECT * FROM users WHERE name = {user_input}"
# Can validate/escape before converting to string
```

### Standard Library Changes (Python 3.13+)

**PEP 594 "Dead Batteries" Removal**: Python 3.13 removed deprecated standard library modules. Projects **MUST NOT** rely on removed modules and **SHOULD** migrate to recommended alternatives:

- `aifc`, `audioop`, `chunk`, `cgi`, `cgitb`, `crypt`, `imghdr`, `mailcap`, `msilib`, `nis`, `nntplib`, `ossaudiodev`, `pipes`, `sndhdr`, `spwd`, `sunau`, `telnetlib`, `uu`, `xdrlib`

**New Modules**: Python 3.14 introduces new standard library modules:
- `annotationlib`: Low-level utilities for working with type annotations and introspection

**Why**: Removing unmaintained modules reduces the standard library maintenance burden and security surface. New modules like `annotationlib` provide better tools for runtime type introspection and metaprogramming.

## Semantic Analysis: Semgrep

Projects **SHOULD** use Semgrep[^4] for semantic code analysis.

**Why**: Semgrep finds bugs, security issues, and anti-patterns using semantic code analysis[^16]. It goes beyond syntax-level linting to understand code patterns and detect complex issues that traditional linters miss.

```bash
# Security audit
uv run semgrep --config=p/security-audit src/

# Python best practices
uv run semgrep --config=p/python src/

# OWASP Top 10
uv run semgrep --config=p/owasp-top-ten src/
```

## Dead Code Detection: Vulture

Projects **SHOULD** use Vulture[^5] to detect dead code.

**Why**: Dead code increases maintenance burden, confuses developers, and can hide bugs. Vulture automatically identifies unused code with configurable confidence levels[^17].

```bash
uv run vulture src/ --min-confidence=80
```

```toml
[tool.vulture]
paths = ["src/"]
min_confidence = 80
```

## Code Coverage: pytest-cov

Projects **MUST** measure code coverage and **SHOULD** maintain at least 80% coverage.

**Why**: Code coverage metrics help identify untested code paths[^18]. Branch coverage ensures both sides of conditional logic are tested, catching bugs that line coverage alone would miss.

```bash
# Run with coverage
uv run pytest --cov=src --cov-branch --cov-report=html

# Fail if coverage drops below threshold
uv run pytest --cov=src --cov-fail-under=80
```

```toml
[tool.coverage.run]
source = ["src"]
branch = true

[tool.coverage.report]
fail_under = 80
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "@abstractmethod",
]
```

## Cyclomatic Complexity: Radon

Projects **SHOULD** monitor cyclomatic complexity and **SHOULD NOT** exceed grade B (complexity > 10).

**Why**: High cyclomatic complexity indicates code that is difficult to test, understand, and maintain[^19]. Keeping functions below complexity 10 ensures code remains maintainable and testable.

```bash
# Show complexity grades (A=1-5, B=6-10, C=11-20, D=21-30, E=31-40, F=41+)
uv run radon cc src/ -a

# Fail if any function exceeds grade B
uv run radon cc src/ -a --fail B
```

## Fuzzing: Hypothesis + Atheris

Projects **SHOULD** use property-based testing with Hypothesis[^8] and **MAY** use Atheris[^20] for coverage-guided fuzzing.

### Hypothesis (Property-Based Testing)

Projects **SHOULD** use Hypothesis[^8] for property-based testing.

**Why**: Hypothesis is the world-class property-based testing library. It generates thousands of test cases automatically, finding edge cases that manual testing would miss[^21].

```python
from hypothesis import given, strategies as st

@given(st.lists(st.integers()))
def test_sort_is_idempotent(xs: list[int]) -> None:
    assert sorted(sorted(xs)) == sorted(xs)

@given(st.text())
def test_encode_decode_roundtrip(s: str) -> None:
    assert s.encode().decode() == s
```

### Atheris (Coverage-Guided Fuzzing)

Projects **MAY** use Atheris[^20] for coverage-guided fuzzing of native extensions or complex parsing code.

**Why**: Atheris uses coverage-guided fuzzing to find crashes and security issues in native extensions and complex parsing logic that property-based testing alone might miss[^22].

```python
import atheris
import sys

def TestOneInput(data: bytes) -> None:
    try:
        my_parser(data.decode("utf-8", errors="ignore"))
    except ValueError:
        pass  # Expected

atheris.Setup(sys.argv, TestOneInput)
atheris.Fuzz()
```

## Test Performance: pytest-xdist

Projects **SHOULD** use pytest-xdist[^9] to run tests in parallel.

**Why**: Running tests in parallel across CPU cores dramatically reduces test suite execution time[^23], enabling faster feedback loops and more frequent test runs.

```bash
# Auto-detect cores
uv run pytest -n auto

# Specific number of workers
uv run pytest -n 4

# Distribute by load
uv run pytest -n auto --dist=loadgroup
```

```toml
[tool.pytest.ini_options]
addopts = ["-n", "auto", "--dist", "loadgroup"]
```

### Additional Performance Tips

```toml
[tool.pytest.ini_options]
# Reuse test database
addopts = ["--reuse-db"]

# Only run tests affected by changes
# (requires pytest-testmon)
addopts = ["--testmon"]

# Cache test results
cache_dir = ".pytest_cache"
```

## Pre-commit Configuration

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
      - id: mypy
        args: [--strict]

  - repo: https://github.com/returntocorp/semgrep
    rev: v1.102.0
    hooks:
      - id: semgrep
        args: [--config=p/python, --config=p/security-audit, --error]

  - repo: https://github.com/jendrikseipp/vulture
    rev: v2.14
    hooks:
      - id: vulture
        args: [src/, --min-confidence=90]
```

## CI Pipeline

```yaml
# .github/workflows/ci.yml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync
      - run: uv run ruff check .
      - run: uv run ruff format --check .
      - run: uv run mypy src/
      - run: uv run semgrep --config=p/python src/

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync
      - run: uv run pytest -n auto --cov=src --cov-fail-under=80
```

## Dependencies & Package Management

Projects **MUST**:
- Use uv[^10] for package management (uv sync, uv add, uv lock)
- Commit lock files (uv.lock) with SHA256 hashes
- Specify version constraints in pyproject.toml
- Scan for vulnerabilities using pip-audit[^24] or safety[^25]
- Configure Dependabot[^26] or Renovate[^27] for automated dependency updates

**Why**: Locked dependencies ensure reproducible builds[^28]. Vulnerability scanning catches security issues early. Automated updates reduce maintenance burden while keeping dependencies current.

```bash
# Lock dependencies
uv lock

# Update dependencies
uv sync --upgrade
```

```toml
[project]
dependencies = ["requests>=2.32.0,<3"]

[tool.uv]
# Regenerate lock on sync
locked = true
```

```bash
# Security scanning
uv run pip-audit
uv run safety check
```

## E2E & Acceptance Testing

Projects with web interfaces **SHOULD** use Playwright[^29] for browser testing and **MAY** use pytest-bdd[^30] for BDD-style acceptance tests.

**Why**: Playwright provides reliable, cross-browser end-to-end testing with auto-waiting and built-in debugging[^31]. pytest-bdd enables collaboration between technical and non-technical stakeholders using Gherkin syntax[^32].

```python
from playwright.sync_api import Page, expect

def test_user_login(page: Page) -> None:
    page.goto("https://example.com/login")
    page.fill("#username", "test@example.com")
    page.click("button[type=submit]")
    expect(page.locator(".welcome")).to_be_visible()
```

```python
# pytest-bdd example
from pytest_bdd import scenario, given, when, then

@scenario("features/login.feature", "User logs in successfully")
def test_login(): ...

@given("I am on the login page")
def on_login_page(page: Page) -> None:
    page.goto("/login")
```

## Thread Safety Testing

Projects with concurrent code **MUST** test for thread safety and race conditions.

**Why**: Concurrent code is prone to race conditions and deadlocks that only manifest under specific timing conditions. Explicit thread safety testing catches these issues before production.

```python
from concurrent.futures import ThreadPoolExecutor

def test_concurrent_access() -> None:
    counter = Counter()
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(counter.increment) for _ in range(100)]
        assert counter.value == 100  # Should be thread-safe
```

```bash
# Run tests in parallel threads
uv run pytest --workers=4
```

## Idempotence Testing

Projects **SHOULD** test that critical operations are idempotent.

**Why**: Idempotent operations can be safely retried without unintended side effects. This is essential for reliability in distributed systems, API design, and database operations where retries are common.

```python
def test_create_user_idempotent(db: Session) -> None:
    user_id = create_user(db, email="test@example.com")
    same_id = create_user(db, email="test@example.com")
    assert user_id == same_id
    assert db.query(User).count() == 1
```

```python
def test_payment_idempotent(api_client: Client) -> None:
    response1 = api_client.post("/pay", json={"amount": 100}, headers={"Idempotency-Key": "key1"})
    response2 = api_client.post("/pay", json={"amount": 100}, headers={"Idempotency-Key": "key1"})
    assert response1.json()["id"] == response2.json()["id"]
```

## Reliability & Resilience Testing

Projects **SHOULD** test resilience patterns such as circuit breakers, retries, and fault tolerance.

**Why**: Testing resilience patterns ensures systems gracefully handle failures. Chaos engineering and fault injection reveal weaknesses before they cause production outages.

```python
def test_circuit_breaker_opens(mocker) -> None:
    service = mocker.patch("external_service.call", side_effect=TimeoutError)
    circuit = CircuitBreaker()
    for _ in range(5):
        with pytest.raises(TimeoutError):
            circuit.call(service)
    assert circuit.state == "open"
```

```json
{
  "title": "Database failure",
  "method": [{
    "type": "action",
    "name": "terminate-db",
    "provider": {"type": "python", "module": "db.kill"}
  }]
}
```

## Compatibility Testing

Projects **SHOULD** test across multiple Python versions and **SHOULD** test on multiple operating systems if targeting diverse environments.

**Why**: Testing across Python versions ensures compatibility as the ecosystem evolves. OS-specific testing catches platform-dependent bugs before users encounter them.

```toml
[tool.tox]
env_list = ["py312", "py313", "py314"]

[testenv]
deps = ["pytest", "pytest-cov"]
commands = ["pytest"]
```

```yaml
# GitHub Actions matrix
strategy:
  matrix:
    python-version: ["3.12", "3.13", "3.14"]
    os: [ubuntu-latest, macos-latest, windows-latest]
```

**Note**: Python 3.13+ includes experimental support for free-threading (PEP 703), removing the Global Interpreter Lock (GIL). Python 3.14 includes JIT compilation improvements for performance gains. Consider testing with free-threading enabled if your application has CPU-bound parallel workloads.

## Internationalization Testing

Projects with international users **SHOULD** test UTF-8 handling and **MAY** test locale-specific behavior.

**Why**: Unicode handling bugs can corrupt data or cause crashes. Testing with diverse character sets ensures robust string handling across all languages and locales.

```python
@pytest.mark.parametrize("text", ["Hello", "مرحبا", "你好", "🚀"])
def test_unicode_handling(text: str) -> None:
    result = process_text(text)
    assert result.encode("utf-8").decode("utf-8") == result
```

```python
import babel.support

def test_translation() -> None:
    trans = babel.support.Translations.load("locale", ["es"])
    assert trans.gettext("Hello") == "Hola"
```

## Data Integrity Testing

Projects with databases **MUST** test data integrity constraints and **SHOULD** test migration reversibility.

**Why**: Database constraints prevent data corruption. Testing migrations ensures schema changes can be safely deployed and rolled back. Backup/restore testing verifies disaster recovery procedures actually work.

```python
def test_unique_constraint(db: Session) -> None:
    db.add(User(email="test@example.com"))
    db.commit()
    with pytest.raises(IntegrityError):
        db.add(User(email="test@example.com"))
        db.commit()
```

```python
def test_migration_reversible(db_engine) -> None:
    alembic.upgrade("head")
    alembic.downgrade("base")
    alembic.upgrade("head")  # Should succeed
```

## A/B Testing & Feature Flags

Projects using feature flags **MUST** test both enabled and disabled states.

**Why**: Feature flags enable gradual rollouts and A/B testing, but untested flag states can cause production failures. Testing both states ensures features work correctly in all configurations.

```python
@pytest.mark.parametrize("flag_enabled", [True, False])
def test_new_feature(flag_enabled: bool, mocker) -> None:
    mocker.patch("flags.is_enabled", return_value=flag_enabled)
    result = feature_under_test()
    assert result.uses_new_behavior == flag_enabled
```

```python
from flagsmith import Flagsmith

flags = Flagsmith(environment_key="test")
if flags.has_feature("new_checkout"):
    return new_checkout_flow()
```

## See Also

- [Django Guide](../frameworks/django.md) - Full-featured Python web framework
- [Flask Guide](../frameworks/flask.md) - Lightweight microframework for web apps
- [FastAPI Guide](../frameworks/fastapi.md) - High-performance async API framework
- [Testing Guide](../process/testing.md) - Comprehensive testing strategies and patterns
- [CI Guide](../process/ci.md) - Continuous integration setup and configuration

## References

[^1]: [Ruff Documentation](https://docs.astral.sh/ruff/)
[^2]: [Mypy Documentation](https://mypy.readthedocs.io/)
[^3]: [Pyright Documentation](https://github.com/microsoft/pyright)
[^4]: [Semgrep Documentation](https://semgrep.dev/docs/)
[^5]: [Vulture Documentation](https://github.com/jendrikseipp/vulture)
[^6]: [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
[^7]: [Radon Documentation](https://radon.readthedocs.io/)
[^8]: [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
[^9]: [pytest-xdist Documentation](https://pytest-xdist.readthedocs.io/)
[^10]: [uv Documentation](https://docs.astral.sh/uv/)
[^11]: [uv Performance Benchmarks](https://github.com/astral-sh/uv#performance)
[^12]: [PEP 518 - pyproject.toml](https://peps.python.org/pep-0518/) and [PEP 621 - Project Metadata](https://peps.python.org/pep-0621/)
[^13]: [Ruff Performance Benchmarks](https://github.com/astral-sh/ruff#performance)
[^14]: [Black - The Uncompromising Code Formatter](https://github.com/psf/black)
[^15]: [Mypy vs Pyright Comparison](https://github.com/microsoft/pyright/blob/main/docs/mypy-comparison.md)
[^16]: [Semgrep - Lightweight Static Analysis](https://semgrep.dev/docs/writing-rules/overview/)
[^17]: [Vulture - Find Dead Code](https://github.com/jendrikseipp/vulture#confidence)
[^18]: [Code Coverage Best Practices](https://coverage.readthedocs.io/en/latest/)
[^19]: [Cyclomatic Complexity - Wikipedia](https://en.wikipedia.org/wiki/Cyclomatic_complexity)
[^20]: [Atheris - Coverage-Guided Fuzzer](https://github.com/google/atheris)
[^21]: [Hypothesis - Property-Based Testing](https://hypothesis.works/)
[^22]: [Atheris Documentation](https://github.com/google/atheris#atheris-a-coverage-guided-python-fuzzer)
[^23]: [pytest-xdist - Distributed Testing](https://pytest-xdist.readthedocs.io/en/stable/)
[^24]: [pip-audit Documentation](https://github.com/pypa/pip-audit)
[^25]: [Safety Documentation](https://github.com/pyupio/safety)
[^26]: [Dependabot Documentation](https://docs.github.com/en/code-security/dependabot)
[^27]: [Renovate Documentation](https://docs.renovatebot.com/)
[^28]: [Reproducible Builds](https://reproducible-builds.org/)
[^29]: [Playwright for Python](https://playwright.dev/python/)
[^30]: [pytest-bdd Documentation](https://pytest-bdd.readthedocs.io/)
[^31]: [Playwright - Reliable End-to-End Testing](https://playwright.dev/python/docs/intro)
[^32]: [Gherkin Syntax Reference](https://cucumber.io/docs/gherkin/reference/)
