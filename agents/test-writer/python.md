---
name: test-writer-python
description: "pytest fixtures, parametrize, mocking, async, FastAPI testing"
model: sonnet
---

# Test Writer: Python Module

> [Test Writer Agent](../test-writer.md) > Python

Python-specific guidance for test generation.

## Quick Reference

| Task | Tool | Command |
| ---- | ---- | ------- |
| Run tests | pytest | `pytest tests/` |
| Coverage | coverage.py | `pytest --cov=src --cov-report=xml` |
| Mutation | mutmut | `mutmut run` |
| Type check | mypy | `mypy src/` |

## Framework Detection

Detect testing framework from project files:

| Indicator | Framework |
| --------- | --------- |
| `pytest.ini`, `pyproject.toml [tool.pytest]` | pytest |
| `unittest` imports in existing tests | unittest |
| `conftest.py` present | pytest |
| No indicators | Default to pytest |

## pytest Patterns

### Basic Test Structure

```python
import pytest
from mymodule import calculate_total

class TestCalculateTotal:
    """Tests for calculate_total function."""

    def test_empty_list_returns_zero(self):
        """Empty input should return zero."""
        result = calculate_total([])
        assert result == 0

    def test_single_item_returns_item_value(self):
        """Single item list returns that item's value."""
        result = calculate_total([42])
        assert result == 42

    def test_multiple_items_returns_sum(self):
        """Multiple items should be summed."""
        result = calculate_total([1, 2, 3])
        assert result == 6
```

### Fixtures

```python
import pytest

@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    return User(name="Test User", email="test@example.com")

@pytest.fixture
def db_session(tmp_path):
    """Create a temporary database session."""
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
```

### Parametrized Tests

```python
import pytest

@pytest.mark.parametrize("input_val,expected", [
    (0, "zero"),
    (1, "one"),
    (-1, "negative"),
    (100, "large"),
])
def test_categorize_number(input_val, expected):
    """Test number categorization with various inputs."""
    assert categorize(input_val) == expected
```

### Exception Testing

```python
import pytest

def test_divide_by_zero_raises_error():
    """Division by zero should raise ValueError."""
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        divide(10, 0)
```

### Mocking

```python
from unittest.mock import Mock, patch, MagicMock

def test_fetch_user_calls_api():
    """Verify API is called with correct parameters."""
    with patch("mymodule.requests.get") as mock_get:
        mock_get.return_value.json.return_value = {"id": 1, "name": "Test"}

        result = fetch_user(1)

        mock_get.assert_called_once_with("https://api.example.com/users/1")
        assert result["name"] == "Test"

def test_service_with_mock_dependency():
    """Test service with mocked dependency."""
    mock_repo = Mock(spec=UserRepository)
    mock_repo.find_by_id.return_value = User(id=1, name="Test")

    service = UserService(repository=mock_repo)
    user = service.get_user(1)

    assert user.name == "Test"
    mock_repo.find_by_id.assert_called_once_with(1)
```

### Async Tests

```python
import pytest

@pytest.mark.asyncio
async def test_async_fetch():
    """Test async function."""
    result = await async_fetch_data("https://api.example.com")
    assert result is not None
```

## Coverage Commands

```bash
# Generate coverage report
pytest --cov=src --cov-report=xml --cov-report=term-missing

# Coverage with branch analysis
pytest --cov=src --cov-branch --cov-report=xml

# Fail if coverage below threshold
pytest --cov=src --cov-fail-under=80
```

## Coverage Report Parsing

Parse `coverage.xml` (Cobertura format):

```xml
<coverage line-rate="0.85" branch-rate="0.72">
  <packages>
    <package name="mymodule">
      <classes>
        <class filename="src/mymodule.py" line-rate="0.90">
          <lines>
            <line number="10" hits="0"/>  <!-- Uncovered -->
            <line number="15" hits="3"/>  <!-- Covered -->
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
```

## Mutation Testing

```bash
# Run mutation testing
mutmut run --paths-to-mutate=src/

# Show surviving mutants
mutmut results

# Generate HTML report
mutmut html
```

## Common Patterns

### Testing Classes

```python
class TestUserService:
    """Tests for UserService class."""

    @pytest.fixture
    def service(self, mock_repo):
        """Create service instance with mocked dependencies."""
        return UserService(repository=mock_repo)

    def test_create_user_saves_to_repository(self, service, mock_repo):
        """Creating user should persist to repository."""
        user_data = {"name": "Test", "email": "test@example.com"}

        service.create_user(user_data)

        mock_repo.save.assert_called_once()
```

### Testing APIs (FastAPI/Flask)

```python
from fastapi.testclient import TestClient

def test_get_users_returns_list(client: TestClient):
    """GET /users should return list of users."""
    response = client.get("/users")

    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_user_requires_auth(client: TestClient):
    """POST /users without auth should return 401."""
    response = client.post("/users", json={"name": "Test"})

    assert response.status_code == 401
```

## See Also

- [Python Style Guide](../../../../guides/languages/python.md)
- [Testing Guide](../../../../guides/process/testing.md)
