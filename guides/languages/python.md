# Python Style Guide

> [Doctrine](../../README.md) > [Languages](../README.md) > Python

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

Extends [Google Python Style Guide](google/python.md).

## Quick Reference

| Task | Tool | Command |
| ---- | ---- | ------- |
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
| Password hash | argon2-cffi[^34] | `PasswordHasher().hash(password)` |
| Encryption | cryptography[^35] | `Fernet(key).encrypt(data)` |
| Rate limit | limits[^37] | `strategies.MovingWindowRateLimiter()` |
| Circuit break | pybreaker[^39] | `@CircuitBreaker(fail_max=5)` |
| Cache (memory) | cachetools[^41] | `@cached(TTLCache(maxsize=100, ttl=300))` |
| Cache (disk) | diskcache[^42] | `Cache("/path").memoize()` |

## Package Management: uv

Projects **MUST** use uv[^10] for all Python package management.

**Why**: uv is the world-class Python package manager, 10-100x faster than
pip[^11]. It provides deterministic dependency resolution, faster installs, and
a superior developer experience compared to pip, poetry, or pipenv.

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

All configuration **MUST** live in `pyproject.toml`. Projects **MUST NOT** use
`setup.py`, `setup.cfg`, `requirements.txt`, or tool-specific config files.

**Why**: Centralizing all project configuration in `pyproject.toml`
(PEP 518/621)[^12] eliminates configuration sprawl, reduces maintenance burden,
and aligns with modern Python packaging standards.

## Linting: Ruff

Projects **MUST** use Ruff[^1] for linting.

**Why**: Ruff replaces Flake8, isort, pyupgrade, and many other tools in a
single, fast implementation. Written in Rust, it's 10-100x faster than
alternatives[^13] while providing comprehensive Python linting rules.

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

**Why**: Ruff format is a drop-in replacement for Black[^14], but faster. Using
the same tool for both linting and formatting simplifies tooling and improves
performance.

```toml
[tool.ruff.format]
quote-style = "double"
indent-style = "space"
line-ending = "auto"
```

## Type Checking: Mypy + Pyright

Projects **MUST** use both Mypy[^2] and Pyright[^3] for type checking.

**Why**: Mypy and Pyright catch different classes of type errors due to their
different implementations and type inference strategies[^15]. Using both
provides maximum type safety coverage.

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

**Note**: As of Python 3.14, PEP 649 deferred annotation evaluation is enabled
by default. The `from __future__ import annotations` import is **no longer
required** for forward references or avoiding import cycles in type hints.

### PEP 695 Type Parameter Syntax (Python 3.12+)

Projects targeting Python 3.12+ **SHOULD** use the new type parameter syntax
for generics and type aliases.

**Why**: PEP 695 provides a cleaner, more concise syntax for defining generic
classes, functions, and type aliases. The new syntax eliminates boilerplate
imports and makes type parameters more explicit and easier to read.

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

Projects targeting Python 3.13+ **SHOULD** use `TypeIs` for user-defined type
guards that narrow types.

**Why**: `TypeIs` provides more accurate type narrowing than `TypeGuard`. It
correctly narrows the type in the else branch and works better with union
types, improving type checker accuracy.

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

Projects targeting Python 3.14+ **MAY** use template strings (t-strings) for
safe string interpolation.

**Why**: Template strings provide a safer alternative to f-strings for
user-generated content, enabling validation and escaping before interpolation.
They return `Template` objects rather than strings, allowing deferred
evaluation and security checks.

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

**PEP 594 "Dead Batteries" Removal**: Python 3.13 removed deprecated standard
library modules. Projects **MUST NOT** rely on removed modules and **SHOULD**
migrate to recommended alternatives:

- `aifc`, `audioop`, `chunk`, `cgi`, `cgitb`, `crypt`, `imghdr`, `mailcap`,
  `msilib`, `nis`, `nntplib`, `ossaudiodev`, `pipes`, `sndhdr`, `spwd`,
  `sunau`, `telnetlib`, `uu`, `xdrlib`

**New Modules**: Python 3.14 introduces new standard library modules:

- `annotationlib`: Low-level utilities for working with type annotations and
  introspection

**Why**: Removing unmaintained modules reduces the standard library maintenance
burden and security surface. New modules like `annotationlib` provide better
tools for runtime type introspection and metaprogramming.

## Semantic Analysis: Semgrep

Projects **SHOULD** use Semgrep[^4] for semantic code analysis.

**Why**: Semgrep finds bugs, security issues, and anti-patterns using semantic
code analysis[^16]. It goes beyond syntax-level linting to understand code
patterns and detect complex issues that traditional linters miss.

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

**Why**: Dead code increases maintenance burden, confuses developers, and can
hide bugs. Vulture automatically identifies unused code with configurable
confidence levels[^17].

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

**Why**: Code coverage metrics help identify untested code paths[^18]. Branch
coverage ensures both sides of conditional logic are tested, catching bugs
that line coverage alone would miss.

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

Projects **SHOULD** monitor cyclomatic complexity and **SHOULD NOT** exceed
grade B (complexity > 10).

**Why**: High cyclomatic complexity indicates code that is difficult to test,
understand, and maintain[^19]. Keeping functions below complexity 10 ensures
code remains maintainable and testable.

```bash
# Show complexity grades (A=1-5, B=6-10, C=11-20, D=21-30, E=31-40, F=41+)
uv run radon cc src/ -a

# Fail if any function exceeds grade B
uv run radon cc src/ -a --fail B
```

## Fuzzing: Hypothesis + Atheris

Projects **SHOULD** use property-based testing with Hypothesis[^8] and **MAY**
use Atheris[^20] for coverage-guided fuzzing.

### Hypothesis (Property-Based Testing)

Projects **SHOULD** use Hypothesis[^8] for property-based testing.

**Why**: Hypothesis is the world-class property-based testing library. It
generates thousands of test cases automatically, finding edge cases that
manual testing would miss[^21].

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

Projects **MAY** use Atheris[^20] for coverage-guided fuzzing of native
extensions or complex parsing code.

**Why**: Atheris uses coverage-guided fuzzing to find crashes and security
issues in native extensions and complex parsing logic that property-based
testing alone might miss[^22].

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

**Why**: Running tests in parallel across CPU cores dramatically reduces test
suite execution time[^23], enabling faster feedback loops and more frequent
test runs.

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

**Why**: Locked dependencies ensure reproducible builds[^28]. Vulnerability
scanning catches security issues early. Automated updates reduce maintenance
burden while keeping dependencies current.

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

Projects with web interfaces **SHOULD** use Playwright[^29] for browser testing
and **MAY** use pytest-bdd[^30] for BDD-style acceptance tests.

**Why**: Playwright provides reliable, cross-browser end-to-end testing with
auto-waiting and built-in debugging[^31]. pytest-bdd enables collaboration
between technical and non-technical stakeholders using Gherkin syntax[^32].

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

**Why**: Concurrent code is prone to race conditions and deadlocks that only
manifest under specific timing conditions. Explicit thread safety testing
catches these issues before production.

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

**Why**: Idempotent operations can be safely retried without unintended side
effects. This is essential for reliability in distributed systems, API design,
and database operations where retries are common.

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

Projects **SHOULD** test resilience patterns such as circuit breakers, retries,
and fault tolerance.

**Why**: Testing resilience patterns ensures systems gracefully handle
failures. Chaos engineering and fault injection reveal weaknesses before they
cause production outages.

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

Projects **SHOULD** test across multiple Python versions and **SHOULD** test on
multiple operating systems if targeting diverse environments.

**Why**: Testing across Python versions ensures compatibility as the ecosystem
evolves. OS-specific testing catches platform-dependent bugs before users
encounter them.

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

**Note**: Python 3.13+ includes experimental support for free-threading
(PEP 703), removing the Global Interpreter Lock (GIL). Python 3.14 includes
JIT compilation improvements for performance gains. Consider testing with
free-threading enabled if your application has CPU-bound parallel workloads.

## Internationalization Testing

Projects with international users **SHOULD** test UTF-8 handling and **MAY** test locale-specific behavior.

**Why**: Unicode handling bugs can corrupt data or cause crashes. Testing with
diverse character sets ensures robust string handling across all languages and
locales.

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

**Why**: Database constraints prevent data corruption. Testing migrations
ensures schema changes can be safely deployed and rolled back. Backup/restore
testing verifies disaster recovery procedures actually work.

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

**Why**: Feature flags enable gradual rollouts and A/B testing, but untested
flag states can cause production failures. Testing both states ensures
features work correctly in all configurations.

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

## Profiling

Projects **SHOULD** profile code before optimizing and **MUST** profile
production workloads to identify actual bottlenecks.

**Why**: Premature optimization wastes time on non-critical paths. Profiling
identifies where time is actually spent, enabling targeted optimization with
measurable impact.

### CPU Profiling

```python
# Built-in cProfile
import cProfile
import pstats

with cProfile.Profile() as pr:
    expensive_function()

stats = pstats.Stats(pr)
stats.sort_stats("cumulative").print_stats(20)
```

```bash
# py-spy for production profiling (no code changes)
uv add --dev py-spy
py-spy top --pid 12345
py-spy record -o profile.svg --pid 12345  # Flame graph
```

### Memory Profiling

```python
from memory_profiler import profile

@profile
def memory_intensive() -> None:
    data = [i ** 2 for i in range(1000000)]
    return sum(data)
```

```bash
# Line-by-line memory usage
uv add --dev memory-profiler
python -m memory_profiler script.py

# Object tracking
uv add --dev objgraph
python -c "import objgraph; objgraph.show_most_common_types()"
```

### Async Profiling

```bash
# aiomonitor for async introspection
uv add --dev aiomonitor
```

```python
import aiomonitor

async def main() -> None:
    with aiomonitor.start_monitor():
        await run_server()
```

### Continuous Profiling

For production, **SHOULD** use continuous profiling services:

```python
# Pyroscope integration
import pyroscope

pyroscope.configure(
    application_name="myapp",
    server_address="http://pyroscope:4040",
)
```

## Async Patterns

Projects using async/await **MUST** follow these patterns to avoid common pitfalls.

### Event Loop Management

```python
import asyncio

# MUST use asyncio.run() at top level
async def main() -> None:
    await do_work()

if __name__ == "__main__":
    asyncio.run(main())

# MUST NOT create event loops manually in library code
# BAD: loop = asyncio.get_event_loop()
```

### Concurrent Execution

```python
import asyncio

async def fetch_all(urls: list[str]) -> list[Response]:
    # Use gather for concurrent execution
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, url) for url in urls]
        return await asyncio.gather(*tasks)

# Use TaskGroup (Python 3.11+) for structured concurrency
async def fetch_all_safe(urls: list[str]) -> list[Response]:
    results: list[Response] = []
    async with asyncio.TaskGroup() as tg:
        for url in urls:
            tg.create_task(fetch_and_append(url, results))
    return results
```

### Timeouts

```python
import asyncio

# MUST use timeouts for external calls
async def fetch_with_timeout(url: str) -> Response:
    async with asyncio.timeout(30):  # Python 3.11+
        return await fetch(url)

# Or with wait_for
result = await asyncio.wait_for(fetch(url), timeout=30)
```

### Resource Cleanup

```python
# MUST use async context managers for cleanup
async with aiohttp.ClientSession() as session:
    response = await session.get(url)

# MUST NOT leave connections open
# BAD: session = aiohttp.ClientSession()  # Never closed
```

### Blocking Code

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

# MUST NOT block the event loop
# BAD: time.sleep(1)  # Blocks entire loop

# Use run_in_executor for blocking operations
async def run_blocking() -> None:
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, blocking_function)
```

### Testing Async Code

```python
import pytest

# Use pytest-asyncio
@pytest.mark.asyncio
async def test_fetch() -> None:
    result = await fetch("https://example.com")
    assert result.status == 200

# Or anyio for backend-agnostic testing
@pytest.mark.anyio
async def test_with_anyio() -> None:
    async with asyncio.TaskGroup() as tg:
        tg.create_task(background_task())
```

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

## Security

Projects **MUST** follow secure coding practices for cryptography, secrets
management, and password hashing.

**Why**: Security vulnerabilities in cryptographic code can expose user data,
enable authentication bypass, and cause catastrophic breaches. Using
well-audited libraries with secure defaults prevents common cryptographic
mistakes.

### Secrets Generation

Projects **MUST** use the `secrets` module (standard library) for generating
cryptographically secure random values.

```python
import secrets

# Generate secure random token
token = secrets.token_urlsafe(32)  # 256 bits of entropy

# Generate secure random bytes
random_bytes = secrets.token_bytes(32)

# Generate secure random hex string
hex_token = secrets.token_hex(32)

# Compare secrets in constant time to prevent timing attacks
if secrets.compare_digest(user_token, stored_token):
    authenticate_user()
```

**Why**: The `random` module is **NOT** cryptographically secure and **MUST
NOT** be used for security-sensitive values like tokens, passwords, or API
keys. The `secrets` module[^33] provides cryptographically strong random
numbers suitable for security purposes.

### Password Hashing

Projects **MUST** use argon2-cffi[^34] for password hashing.

```python
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher(
    time_cost=3,        # Number of iterations
    memory_cost=65536,  # 64 MB memory
    parallelism=4,      # Parallel threads
)

# Hash password
hash = ph.hash("user_password")

# Verify password
try:
    ph.verify(hash, "user_password")
except VerifyMismatchError:
    raise AuthenticationError("Invalid password")

# Check if rehash needed (parameters changed)
if ph.check_needs_rehash(hash):
    new_hash = ph.hash("user_password")
```

**Why**: Argon2 won the Password Hashing Competition and provides memory-hard
hashing that resists GPU and ASIC attacks. The argon2-cffi library wraps the
official Argon2 C implementation with a safe Python API.

### Cryptographic Operations

Projects **SHOULD** use the cryptography library[^35] for encryption, signing, and key management.

```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

# Symmetric encryption with Fernet (AES-128-CBC + HMAC)
key = Fernet.generate_key()
fernet = Fernet(key)

# Encrypt
encrypted = fernet.encrypt(b"secret message")

# Decrypt
decrypted = fernet.decrypt(encrypted)

# Key derivation from password
salt = os.urandom(16)
kdf = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,
    salt=salt,
    iterations=600_000,  # OWASP 2023 recommendation
)
key = base64.urlsafe_b64encode(kdf.derive(b"password"))
```

### Security Anti-Patterns

```python
# BAD: Using random for security
import random
token = random.randint(0, 999999)  # Predictable!

# GOOD: Using secrets
import secrets
token = secrets.randbelow(1000000)

# BAD: Rolling your own crypto
import hashlib
hash = hashlib.sha256(password.encode()).hexdigest()  # No salt, too fast!

# GOOD: Using argon2
from argon2 import PasswordHasher
hash = PasswordHasher().hash(password)

# BAD: Hardcoding secrets
API_KEY = "sk-1234567890abcdef"  # Never commit secrets!

# GOOD: Environment variables
import os
API_KEY = os.environ["API_KEY"]
```

## WebSocket Patterns

Projects using WebSockets **SHOULD** use the websockets library[^36] for async WebSocket communication.

**Why**: The websockets library is built on asyncio, provides a simple
coroutine-based API, handles connection management automatically, and includes
production-ready features like ping/pong, compression, and proper close
handling.

### Server Implementation

```python
import asyncio
import websockets
from websockets.server import serve

async def handler(websocket):
    async for message in websocket:
        # Echo back with processing
        response = process_message(message)
        await websocket.send(response)

async def main():
    async with serve(handler, "localhost", 8765):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
```

### Client Implementation

```python
import asyncio
import websockets

async def client():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        await websocket.send("Hello, Server!")
        response = await websocket.recv()
        print(f"Received: {response}")

asyncio.run(client())
```

### Broadcast Pattern

```python
import asyncio
import websockets
from websockets.server import serve

CLIENTS: set[websockets.WebSocketServerProtocol] = set()

async def register(websocket):
    CLIENTS.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        CLIENTS.discard(websocket)

async def broadcast(message: str):
    websockets.broadcast(CLIENTS, message)

async def handler(websocket):
    await register(websocket)
```

### Connection Management

```python
import asyncio
import websockets

async def robust_client(uri: str):
    """Reconnecting WebSocket client with exponential backoff."""
    backoff = 1
    while True:
        try:
            async with websockets.connect(uri) as ws:
                backoff = 1  # Reset on successful connection
                async for message in ws:
                    await process_message(message)
        except websockets.ConnectionClosed:
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60)  # Max 60 seconds
```

## Rate Limiting

Projects making external API calls or exposing APIs **SHOULD** implement rate
limiting using the limits library[^37] or pyrate-limiter[^38].

**Why**: Rate limiting prevents API abuse, protects against denial of service,
ensures fair resource usage, and helps comply with upstream API provider
limits.

### Using limits Library

```python
from limits import storage, strategies, parse

# In-memory storage (use Redis for distributed systems)
memory_storage = storage.MemoryStorage()
moving_window = strategies.MovingWindowRateLimiter(memory_storage)

# Define rate limit: 100 requests per minute
rate_limit = parse("100/minute")

def check_rate_limit(user_id: str) -> bool:
    """Check if request is allowed."""
    if moving_window.hit(rate_limit, user_id):
        return True
    return False

# With Redis storage for distributed systems
# redis_storage = storage.RedisStorage("redis://localhost:6379")
```

### Token Bucket Implementation

```python
import time
from dataclasses import dataclass, field

@dataclass
class TokenBucket:
    """Thread-safe token bucket rate limiter."""
    capacity: int
    refill_rate: float  # tokens per second
    tokens: float = field(init=False)
    last_refill: float = field(init=False)

    def __post_init__(self):
        self.tokens = float(self.capacity)
        self.last_refill = time.monotonic()

    def acquire(self, tokens: int = 1) -> bool:
        """Try to acquire tokens. Returns True if successful."""
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

# Usage: 10 requests per second with burst of 20
bucket = TokenBucket(capacity=20, refill_rate=10)
if bucket.acquire():
    make_api_call()
else:
    raise RateLimitExceeded()
```

### Async Rate Limiting with pyrate-limiter

```python
from pyrate_limiter import Duration, Limiter, Rate

# 5 requests per second, 100 per minute
limiter = Limiter(
    Rate(5, Duration.SECOND),
    Rate(100, Duration.MINUTE),
)

async def rate_limited_call(user_id: str):
    # Blocks until rate limit allows
    async with limiter.ratelimit(user_id, delay=True):
        return await make_api_call()
```

### Decorator Pattern

```python
from functools import wraps
from limits import storage, strategies, parse

memory = storage.MemoryStorage()
limiter = strategies.FixedWindowRateLimiter(memory)

def rate_limit(limit_string: str):
    """Decorator for rate limiting functions."""
    rate = parse(limit_string)

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = func.__name__
            if not limiter.hit(rate, key):
                raise Exception("Rate limit exceeded")
            return func(*args, **kwargs)
        return wrapper
    return decorator

@rate_limit("10/minute")
def send_email(to: str, subject: str):
    # Limited to 10 emails per minute
    ...
```

## Circuit Breakers

Projects calling external services **SHOULD** implement circuit breakers using
pybreaker[^39] to prevent cascading failures.

**Why**: Circuit breakers prevent your application from repeatedly calling a
failing service, allowing it to recover and preventing resource exhaustion.
They enable graceful degradation and faster failure detection.

### Basic Usage

```python
import pybreaker

# Create circuit breaker with 5 failure threshold
breaker = pybreaker.CircuitBreaker(
    fail_max=5,              # Open after 5 failures
    reset_timeout=60,        # Try again after 60 seconds
    exclude=[ValueError],    # Don't count these as failures
)

@breaker
def call_external_service(data: dict) -> dict:
    response = requests.post("https://api.example.com/v1/data", json=data)
    response.raise_for_status()
    return response.json()

# Handle circuit breaker state
try:
    result = call_external_service({"key": "value"})
except pybreaker.CircuitBreakerError:
    # Circuit is open, use fallback
    result = get_cached_response()
except requests.RequestException:
    # Request failed but circuit may still be closed
    result = handle_failure()
```

### With Listeners for Monitoring

```python
import pybreaker
import logging

class LoggingListener(pybreaker.CircuitBreakerListener):
    def state_change(self, cb, old_state, new_state):
        logging.warning(
            f"Circuit {cb.name}: {old_state.name} -> {new_state.name}"
        )

    def failure(self, cb, exc):
        logging.error(f"Circuit {cb.name} failure: {exc}")

    def success(self, cb):
        logging.debug(f"Circuit {cb.name} success")

breaker = pybreaker.CircuitBreaker(
    fail_max=5,
    reset_timeout=60,
    listeners=[LoggingListener()],
    name="payment_service",
)
```

### Async Circuit Breaker

For async code, use aiobreaker[^40]:

```python
from aiobreaker import CircuitBreaker

breaker = CircuitBreaker(fail_max=5, timeout_duration=60)

@breaker
async def async_external_call(data: dict) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data) as response:
            return await response.json()
```

### Redis State Storage (Distributed)

```python
import pybreaker
import redis

redis_client = redis.Redis(host="localhost", port=6379, db=0)

breaker = pybreaker.CircuitBreaker(
    fail_max=5,
    reset_timeout=60,
    state_storage=pybreaker.CircuitRedisStorage(
        pybreaker.STATE_CLOSED,
        redis_client,
        namespace="payment_breaker",
    ),
)
```

## Caching

Projects **SHOULD** implement caching for expensive operations using
cachetools[^41] for in-memory caching, diskcache[^42] for persistent caching,
or aiocache[^43] for async caching.

**Why**: Caching reduces latency, decreases load on databases and external
services, and improves application throughput. Choosing the right caching
strategy depends on data freshness requirements, memory constraints, and
whether caching needs to persist across restarts.

### In-Memory Caching with cachetools

```python
from cachetools import TTLCache, LRUCache, cached
from cachetools.keys import hashkey
import threading

# TTL cache: expire after 300 seconds, max 1000 items
cache = TTLCache(maxsize=1000, ttl=300)
lock = threading.Lock()  # cachetools is not thread-safe by default

@cached(cache, lock=lock)
def get_user(user_id: int) -> User:
    return db.query(User).filter_by(id=user_id).first()

# LRU cache with custom key function
@cached(LRUCache(maxsize=100), key=lambda x, y: hashkey(x.id, y))
def compute_score(user: User, category: str) -> float:
    return expensive_calculation(user, category)

# Manual cache operations
cache["custom_key"] = expensive_result
if "custom_key" in cache:
    result = cache["custom_key"]
```

### Persistent Caching with diskcache

```python
import diskcache

# File-backed cache (persists across restarts)
cache = diskcache.Cache("/tmp/my_cache")

# Store with TTL
cache.set("api_response", response_data, expire=3600)

# Memoization decorator
@cache.memoize(expire=600)
def fetch_data(url: str) -> dict:
    return requests.get(url).json()

# Atomic operations
with cache.transact():
    cache["key1"] = value1
    cache["key2"] = value2

# Cleanup
cache.expire()  # Remove expired items
cache.close()
```

### Async Caching with aiocache

```python
from aiocache import cached, Cache
from aiocache.serializers import JsonSerializer

# Simple async caching
@cached(ttl=300, cache=Cache.MEMORY)
async def get_user_async(user_id: int) -> dict:
    return await db.fetch_user(user_id)

# With Redis backend
@cached(
    ttl=300,
    cache=Cache.REDIS,
    serializer=JsonSerializer(),
    endpoint="localhost",
    port=6379,
)
async def get_external_data(key: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.example.com/{key}") as resp:
            return await resp.json()
```

### Cache Invalidation Patterns

```python
from cachetools import TTLCache

cache = TTLCache(maxsize=1000, ttl=300)

def invalidate_user_cache(user_id: int):
    """Invalidate specific cache entry."""
    cache.pop(f"user:{user_id}", None)

def invalidate_by_prefix(prefix: str):
    """Invalidate all entries matching prefix."""
    keys_to_delete = [k for k in cache if k.startswith(prefix)]
    for key in keys_to_delete:
        del cache[key]

# Event-driven invalidation
def on_user_updated(user_id: int):
    invalidate_user_cache(user_id)
    invalidate_by_prefix(f"user_scores:{user_id}")
```

## Background Jobs

Projects **SHOULD** use `concurrent.futures`[^44] for simple parallelism and
`multiprocessing`[^45] for CPU-bound work.

**Why**: Background jobs enable non-blocking execution of long-running tasks.
Using standard library tools provides framework-agnostic patterns that work
across all Python applications without external dependencies.

### Thread Pool for I/O-Bound Work

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable

def process_urls(urls: list[str]) -> list[dict]:
    """Fetch multiple URLs in parallel."""
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_url, url): url for url in urls}
        for future in as_completed(futures):
            url = futures[future]
            try:
                result = future.result(timeout=30)
                results.append({"url": url, "data": result})
            except Exception as e:
                results.append({"url": url, "error": str(e)})
    return results

def run_with_timeout(fn: Callable, timeout: float, *args, **kwargs):
    """Run function with timeout."""
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(fn, *args, **kwargs)
        return future.result(timeout=timeout)
```

### Process Pool for CPU-Bound Work

```python
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

def cpu_intensive_task(data: bytes) -> bytes:
    """CPU-bound processing (runs in separate process)."""
    return heavy_computation(data)

def process_batch(items: list[bytes]) -> list[bytes]:
    """Process items in parallel across CPU cores."""
    # Use number of CPUs minus 1 to leave headroom
    max_workers = max(1, multiprocessing.cpu_count() - 1)

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(cpu_intensive_task, items))
    return results
```

### Async Background Tasks

```python
import asyncio
from typing import Coroutine, Any

class BackgroundTasks:
    """Manager for fire-and-forget async tasks."""

    def __init__(self):
        self._tasks: set[asyncio.Task] = set()

    def add(self, coro: Coroutine[Any, Any, Any]) -> asyncio.Task:
        """Add background task with automatic cleanup."""
        task = asyncio.create_task(coro)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task

    async def shutdown(self, timeout: float = 30):
        """Wait for all tasks to complete."""
        if self._tasks:
            await asyncio.wait(self._tasks, timeout=timeout)

# Usage
background = BackgroundTasks()

async def handle_request(data: dict):
    # Fire and forget
    background.add(send_notification(data["user_id"]))
    return {"status": "accepted"}

async def shutdown():
    await background.shutdown()
```

### Work Queue Pattern

```python
import asyncio
from collections.abc import Callable, Coroutine
from typing import Any

class WorkQueue:
    """Async work queue with configurable concurrency."""

    def __init__(self, max_workers: int = 10):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._workers: list[asyncio.Task] = []
        self._max_workers = max_workers

    async def start(self):
        """Start worker tasks."""
        for _ in range(self._max_workers):
            task = asyncio.create_task(self._worker())
            self._workers.append(task)

    async def _worker(self):
        while True:
            func, args, kwargs = await self._queue.get()
            try:
                await func(*args, **kwargs)
            except Exception as e:
                logging.error(f"Worker error: {e}")
            finally:
                self._queue.task_done()

    async def submit(
        self,
        func: Callable[..., Coroutine[Any, Any, Any]],
        *args,
        **kwargs,
    ):
        """Submit work to the queue."""
        await self._queue.put((func, args, kwargs))

    async def shutdown(self):
        """Wait for queue to drain and stop workers."""
        await self._queue.join()
        for worker in self._workers:
            worker.cancel()
```

## Feature Flags

Projects **SHOULD** implement feature flags for gradual rollouts and A/B
testing using a provider-agnostic pattern.

**Why**: Feature flags enable controlled rollouts, quick rollbacks, and A/B
testing without deployment. A provider-agnostic interface allows switching
between services (LaunchDarkly, PostHog, Flagsmith)[^46] without code changes.

### Abstract Interface

```python
from abc import ABC, abstractmethod
from typing import Any

class FeatureFlagProvider(ABC):
    """Abstract interface for feature flag providers."""

    @abstractmethod
    def is_enabled(
        self,
        flag_name: str,
        user_id: str | None = None,
        default: bool = False,
    ) -> bool:
        """Check if feature flag is enabled."""
        ...

    @abstractmethod
    def get_value(
        self,
        flag_name: str,
        user_id: str | None = None,
        default: Any = None,
    ) -> Any:
        """Get feature flag value (for multivariate flags)."""
        ...
```

### Simple Implementation

```python
import os
import json
from pathlib import Path

class EnvFeatureFlags(FeatureFlagProvider):
    """Environment variable-based feature flags."""

    def __init__(self, prefix: str = "FEATURE_"):
        self._prefix = prefix

    def is_enabled(
        self,
        flag_name: str,
        user_id: str | None = None,
        default: bool = False,
    ) -> bool:
        env_name = f"{self._prefix}{flag_name.upper()}"
        value = os.environ.get(env_name, "").lower()
        if value in ("1", "true", "yes", "on"):
            return True
        if value in ("0", "false", "no", "off"):
            return False
        return default

    def get_value(
        self,
        flag_name: str,
        user_id: str | None = None,
        default: Any = None,
    ) -> Any:
        env_name = f"{self._prefix}{flag_name.upper()}"
        value = os.environ.get(env_name)
        if value is None:
            return default
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

# Usage
flags = EnvFeatureFlags()
if flags.is_enabled("new_checkout"):
    return new_checkout_flow()
else:
    return legacy_checkout_flow()
```

### Percentage Rollout

```python
import hashlib

class RolloutFeatureFlags(FeatureFlagProvider):
    """Feature flags with percentage-based rollout."""

    def __init__(self, config: dict[str, dict]):
        # Config: {"flag_name": {"enabled": True, "percentage": 50}}
        self._config = config

    def _get_bucket(self, flag_name: str, user_id: str) -> int:
        """Deterministic bucket assignment (0-99)."""
        key = f"{flag_name}:{user_id}"
        hash_value = hashlib.sha256(key.encode()).hexdigest()
        return int(hash_value[:8], 16) % 100

    def is_enabled(
        self,
        flag_name: str,
        user_id: str | None = None,
        default: bool = False,
    ) -> bool:
        config = self._config.get(flag_name, {})
        if not config.get("enabled", False):
            return False

        percentage = config.get("percentage", 100)
        if percentage >= 100:
            return True
        if percentage <= 0 or user_id is None:
            return False

        bucket = self._get_bucket(flag_name, user_id)
        return bucket < percentage

    def get_value(
        self,
        flag_name: str,
        user_id: str | None = None,
        default: Any = None,
    ) -> Any:
        config = self._config.get(flag_name, {})
        return config.get("value", default)
```

### Testing with Feature Flags

```python
import pytest
from unittest.mock import patch

@pytest.fixture
def feature_flags():
    """Fixture for testing with feature flags."""
    return {"new_checkout": True, "beta_feature": False}

@pytest.mark.parametrize("flag_enabled", [True, False])
def test_feature_behavior(flag_enabled: bool, mocker):
    mocker.patch.object(flags, "is_enabled", return_value=flag_enabled)
    result = feature_under_test()
    assert result.uses_new_behavior == flag_enabled
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
[^33]: [secrets - Generate Secure Random Numbers](https://docs.python.org/3/library/secrets.html)
[^34]: [argon2-cffi - Secure Password Hashing](https://argon2-cffi.readthedocs.io/)
[^35]: [cryptography - Cryptographic Recipes](https://cryptography.io/)
[^36]: [websockets - WebSocket Library](https://websockets.readthedocs.io/)
[^37]: [limits - Rate Limiting Utilities](https://limits.readthedocs.io/)
[^38]: [pyrate-limiter - Leaky Bucket Rate Limiter](https://github.com/vutran1710/PyrateLimiter)
[^39]: [pybreaker - Circuit Breaker Pattern](https://github.com/danielfm/pybreaker)
[^40]: [aiobreaker - Async Circuit Breaker](https://github.com/arlyon/aiobreaker)
[^41]: [cachetools - Extensible Memoizing Collections](https://cachetools.readthedocs.io/)
[^42]: [diskcache - Disk and File Backed Cache](https://grantjenks.com/docs/diskcache/)
[^43]: [aiocache - Async Cache Library](https://aiocache.readthedocs.io/)
[^44]: [concurrent.futures - Launching Parallel Tasks](https://docs.python.org/3/library/concurrent.futures.html)
[^45]: [multiprocessing - Process-Based Parallelism](https://docs.python.org/3/library/multiprocessing.html)
[^46]: [Feature Flag Providers - LaunchDarkly](https://launchdarkly.com/), [PostHog](https://posthog.com/feature-flags), [Flagsmith](https://flagsmith.com/)
