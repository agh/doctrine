# Django Style Guide

> [Doctrine](../../README.md) > [Frameworks](../README.md) > Django

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://tools.ietf.org/html/rfc2119).

Extends [Python style guide](python.md) with Django-specific conventions from
[Django coding style](https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/).

## Quick Reference

All Python tooling applies. Projects **MUST** use the additional Django-specific tools:

| Task | Tool | Command |
|------|------|---------|
| Lint | Ruff[^1] + django rules | `uv run ruff check .` |
| Format | Ruff[^1] | `uv run ruff format .` |
| Type check | django-stubs[^2] | `uv run mypy .` |
| Security | Built-in CSP (6.0+), bandit[^4] | `uv run bandit -r .` |
| Test | pytest-django[^5] | `uv run pytest` |
| Coverage | pytest-cov[^6] | `uv run pytest --cov` |
| Migrations | squawk[^7] | `squawk migrations/*.sql` |

## Project Structure

```
myproject/
├── config/                 # Project configuration
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   ├── production.py
│   │   └── test.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/                   # Django applications
│   ├── users/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── services.py     # Business logic
│   │   ├── selectors.py    # Query logic
│   │   └── tests/
│   └── orders/
├── core/                   # Shared utilities
│   ├── models.py          # Base models
│   └── exceptions.py
├── templates/
├── static/
├── manage.py
└── pyproject.toml
```

## Ruff Configuration for Django

Projects **MUST** enable Django-specific rules:

```toml
[tool.ruff.lint]
select = [
    "E", "F", "W", "I", "UP", "B", "C4", "SIM", "S", "N", "D", "ANN", "RUF",
    "DJ",   # flake8-django
]

[tool.ruff.lint.per-file-ignores]
"*/migrations/*.py" = ["E501", "D"]
"*/tests/*.py" = ["S101", "ANN"]
"config/settings/*.py" = ["F405"]
```

**Why Ruff with Django rules:**
- Catches Django-specific anti-patterns (nullable string fields, model `__str__` methods)
- Identifies security issues (raw SQL, deprecated features)
- Unifies linting and formatting in a single tool

## Type Checking: django-stubs

Projects **MUST** use django-stubs[^2] for type checking:

```bash
uv add --dev django-stubs django-stubs-ext
```

```toml
[tool.mypy]
plugins = ["mypy_django_plugin.main"]

[tool.django-stubs]
django_settings_module = "config.settings.development"
```

**Why django-stubs:**
- Provides accurate type stubs for Django's dynamic APIs (QuerySets, managers, model fields)
- Catches common errors: missing `null=True`, incorrect field types, invalid query methods
- Essential for type safety in Django projects

## Models

### Naming

Model names **MUST** be singular PascalCase:

```python
# Model names: singular PascalCase
class User(models.Model):
    pass

class OrderItem(models.Model):  # NOT OrderItems
    pass
```

### Field Order

Model fields **MUST** follow this order:

```python
class User(models.Model):
    # 1. Database fields
    id = models.BigAutoField(primary_key=True)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # 2. Relationships
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="users",
    )

    # 3. Meta class
    class Meta:
        db_table = "users"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["email"]),
        ]

    # 4. __str__
    def __str__(self) -> str:
        return self.email

    # 5. Properties
    @property
    def full_name(self) -> str:
        return self.name

    # 6. Methods
    def send_welcome_email(self) -> None:
        pass
```

### Related Name Convention

The `related_name` **MUST** be plural, describing the reverse relation:

```python
# related_name should be plural, describing the reverse relation
class Order(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="orders",  # user.orders.all()
    )
```

## Views

### First Parameter

The first parameter **MUST** always be named `request`:

```python
# Always name the first parameter "request"
def user_list(request: HttpRequest) -> HttpResponse:
    pass

# For class-based views
class UserListView(ListView):
    def get(self, request: HttpRequest) -> HttpResponse:
        pass
```

### Fat Models, Thin Views

```python
# BAD: Logic in view
def create_order(request):
    order = Order.objects.create(user=request.user)
    order.total = sum(item.price for item in order.items.all())
    order.apply_discount()
    order.save()
    send_order_email(order)
    return Response(...)

# GOOD: Logic in service
def create_order(request):
    order = order_create(user=request.user, items=request.data["items"])
    return Response(OrderSerializer(order).data)
```

## Services Pattern

Business logic **MUST** be in services, not views or models.

**Why use services:**
- Separates business logic from HTTP/presentation concerns
- Makes logic reusable across views, management commands, Celery tasks
- Easier to test without Django request/response machinery
- Enforces single responsibility principle

```python
# apps/orders/services.py
from django.db import transaction

def order_create(*, user: User, items: list[dict]) -> Order:
    """Create an order with items.

    Args:
        user: The user placing the order.
        items: List of item dicts with product_id and quantity.

    Returns:
        The created Order instance.

    Raises:
        ValidationError: If items are invalid.
    """
    with transaction.atomic():
        order = Order.objects.create(user=user)
        for item in items:
            OrderItem.objects.create(
                order=order,
                product_id=item["product_id"],
                quantity=item["quantity"],
            )
        order.calculate_total()
        order.save()
    return order
```

## Selectors Pattern

Query logic **SHOULD** be in selectors.

**Why use selectors:**
- Centralizes query optimization (select_related, prefetch_related)
- Makes queries reusable and testable
- Separates data fetching from business logic
- Easier to maintain and optimize performance

```python
# apps/orders/selectors.py
from django.db.models import QuerySet

def order_list(*, user: User) -> QuerySet[Order]:
    return Order.objects.filter(user=user).select_related("user")

def order_get(*, order_id: int, user: User) -> Order:
    return Order.objects.select_related("user").get(id=order_id, user=user)
```

## Content Security Policy (Django 6.0+)

Projects **SHOULD** use Django's built-in CSP framework instead of django-csp:

```python
# config/settings/base.py
from django.utils.csp import CSP

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.csp.ContentSecurityPolicyMiddleware",
    # ...
]

SECURE_CSP = {
    "default-src": [CSP.SELF],
    "script-src": [CSP.SELF, CSP.NONCE],
    "style-src": [CSP.SELF, CSP.NONCE],
    "img-src": [CSP.SELF, "https:"],
    "connect-src": [CSP.SELF],
}

# Report-only mode for testing
SECURE_CSP_REPORT_ONLY = {
    "default-src": [CSP.SELF],
    "report-uri": "/csp-report/",
}
```

```html
<!-- templates/base.html - use nonce for inline scripts -->
{% load csp %}
<script nonce="{{ csp_nonce }}">
    // Inline script allowed by nonce
</script>
```

**Why**: Django 6.0's built-in CSP support eliminates the need for third-party packages and provides first-class integration with Django's security middleware.

## Background Tasks (Django 6.0+)

Projects **MAY** use Django's built-in task framework for simple background jobs:

```python
# apps/orders/tasks.py
from django.tasks import task

@task
def send_order_confirmation(order_id: int) -> None:
    order = Order.objects.get(id=order_id)
    send_email(order.user.email, "Order Confirmed", render_order_email(order))

@task
def process_refund(order_id: int, amount: int) -> dict:
    # Long-running task
    result = payment_gateway.refund(order_id, amount)
    return {"status": result.status, "refund_id": result.id}
```

```python
# apps/orders/views.py
from apps.orders.tasks import send_order_confirmation

def create_order(request):
    order = order_create(user=request.user, items=request.data["items"])
    send_order_confirmation.enqueue(order_id=order.id)  # Non-blocking
    return Response(OrderSerializer(order).data)
```

```python
# config/settings/production.py
TASKS = {
    "default": {
        "BACKEND": "django.tasks.backends.database.DatabaseBackend",
    }
}
```

**Why**: For simple task queuing, Django's built-in framework reduces dependencies. For complex workflows (retries, scheduling, priorities), Celery remains the better choice.

| Use Case | Recommended |
|----------|-------------|
| Simple email sending | Django Tasks |
| Fire-and-forget jobs | Django Tasks |
| Complex retry logic | Celery |
| Scheduled/periodic tasks | Celery Beat |
| Task chaining/workflows | Celery |

## Template Partials (Django 6.0+)

Projects **SHOULD** use template partials for reusable fragments:

```html
<!-- templates/components/card.html -->
{% partialdef card %}
<div class="card">
    <h3>{{ title }}</h3>
    <p>{{ content }}</p>
</div>
{% endpartialdef %}

<!-- Can define multiple partials in one file -->
{% partialdef card_header %}
<div class="card-header">{{ title }}</div>
{% endpartialdef %}
```

```html
<!-- templates/orders/list.html -->
{% for order in orders %}
    {% partial "components/card.html#card" with title=order.name content=order.description %}
{% endfor %}
```

**Why**: Template partials enable component-style reuse without separate files, reducing template sprawl while maintaining clear boundaries.

## Composite Primary Keys (Django 5.2+)

Projects **MAY** use composite primary keys for natural keys:

```python
class OrderItem(models.Model):
    pk = models.CompositePrimaryKey("order_id", "product_id")
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    class Meta:
        db_table = "order_items"
```

**Why**: Composite primary keys are useful for join tables and entities with natural multi-column identifiers. Use when the combination of fields is the true identity.

## Async Views and Authentication (Django 5.2+)

Projects using async views **SHOULD** use async authentication methods:

```python
# Async view with async auth
from django.contrib.auth import aauthenticate, alogin

async def login_view(request):
    user = await aauthenticate(
        request,
        username=request.POST["username"],
        password=request.POST["password"],
    )
    if user:
        await alogin(request, user)
        return JsonResponse({"status": "ok"})
    return JsonResponse({"status": "error"}, status=401)

# Async permission checking
async def protected_view(request):
    if not await request.user.ahas_perm("orders.view_order"):
        return HttpResponseForbidden()
    orders = [o async for o in Order.objects.filter(user=request.user)]
    return JsonResponse({"orders": orders})
```

**Why**: Mixing sync auth calls in async views causes performance issues. Django 5.2+ provides native async variants for all authentication operations.

## Imports

```python
# Order: stdlib, third-party, Django, local Django, relative
import logging
from datetime import datetime

import requests
from rest_framework import serializers

from django.conf import settings
from django.db import models

from apps.users.models import User

from .services import order_create
```

**Note**: `from __future__ import annotations` is no longer needed in Python 3.14+ (see [Python Guide](../languages/python.md#type-hint-conventions)).

## Testing with pytest-django

Projects **MUST** use pytest-django[^5] for testing.

**Why pytest-django:**
- Superior fixture system compared to Django's TestCase
- Parallel test execution for faster CI
- Better integration with pytest ecosystem (pytest-cov[^6], pytest-xdist[^8])
- Cleaner test syntax and better error reporting

```python
# conftest.py
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture
def user(db) -> User:
    return User.objects.create_user(
        email="test@example.com",
        password="testpass123",
    )

@pytest.fixture
def api_client():
    from rest_framework.test import APIClient  # Django REST Framework[^9]
    return APIClient()

@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client
```

```python
# tests/test_orders.py
import pytest
from apps.orders.services import order_create

@pytest.mark.django_db
def test_order_create(user):
    order = order_create(user=user, items=[{"product_id": 1, "quantity": 2}])
    assert order.user == user
    assert order.items.count() == 1
```

## Test Performance

Tests **SHOULD** use these performance optimizations:

```toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings.test"
addopts = [
    "-n", "auto",          # Parallel
    "--reuse-db",          # Reuse test database
    "--no-migrations",     # Skip migrations in tests
]
```

## CI Pipeline

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:18
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync
      - run: uv run ruff check .
      - run: uv run mypy .
      - run: uv run pytest --cov --cov-fail-under=80
        env:
          DATABASE_URL: postgres://postgres:postgres@localhost/test
```

## E2E & Acceptance Testing

```python
# tests/test_e2e.py
import pytest
from django.test import Client

# Django test client for API E2E
@pytest.mark.django_db
def test_order_flow_e2e(client: Client, user):
    client.force_login(user)
    response = client.post("/api/orders/", {
        "items": [{"product_id": 1, "quantity": 2}]
    })
    assert response.status_code == 201
    order_id = response.json()["id"]

    response = client.get(f"/api/orders/{order_id}/")
    assert response.json()["status"] == "pending"

# pytest-bdd[^10] for BDD acceptance
# features/order.feature
"""
Feature: Order creation
  Scenario: User creates order
    Given a logged in user
    When the user creates an order with 2 items
    Then the order should be created
    And the order should have 2 items
"""

from pytest_bdd import scenarios, given, when, then

scenarios("features/order.feature")

@given("a logged in user")
def logged_in_user(user, client):
    client.force_login(user)
    return user

@when("the user creates an order with 2 items")
def create_order(client):
    return client.post("/api/orders/", {"items": [{"product_id": 1, "quantity": 2}]})

@then("the order should be created")
def order_created(create_order):
    assert create_order.status_code == 201
```

```python
# Playwright[^11] for browser testing
# tests/test_browser.py
from playwright.sync_api import Page, expect

def test_order_creation_ui(page: Page, live_server):
    page.goto(f"{live_server.url}/orders/new/")
    page.fill("#product-search", "Widget")
    page.click("button[type=submit]")
    expect(page.locator(".success-message")).to_be_visible()
```

## Thread Safety Testing

```python
# Testing Celery[^12] task concurrency
from unittest.mock import patch
from apps.orders.tasks import process_order

@pytest.mark.django_db(transaction=True)
def test_concurrent_order_processing(order):
    with patch("apps.orders.tasks.send_email") as mock_send:
        # Simulate concurrent task execution
        process_order.apply(args=[order.id])
        process_order.apply(args=[order.id])

        order.refresh_from_db()
        assert order.processed_count == 1  # Should only process once

# select_for_update testing
@pytest.mark.django_db(transaction=True)
def test_inventory_decrement_thread_safe():
    from django.db import transaction
    from apps.inventory.models import Product

    product = Product.objects.create(stock=10)

    with transaction.atomic():
        locked_product = Product.objects.select_for_update().get(id=product.id)
        locked_product.stock -= 1
        locked_product.save()

    product.refresh_from_db()
    assert product.stock == 9

# Database connection pool testing
@pytest.mark.django_db(transaction=True)
def test_connection_pool_exhaustion():
    from django.db import connection, connections

    # Test that connections are properly returned to pool
    for _ in range(10):
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

    assert len(connections["default"].queries) <= 10
```

## Idempotence Testing

```python
# Celery task idempotence (django-celery-results[^13])
from apps.orders.tasks import send_order_confirmation

@pytest.mark.django_db
def test_order_confirmation_idempotent(order):
    # Multiple executions should have same result
    task_id = "unique-task-id"
    send_order_confirmation.apply(args=[order.id], task_id=task_id)
    send_order_confirmation.apply(args=[order.id], task_id=task_id)

    from django_celery_results.models import TaskResult
    assert TaskResult.objects.filter(task_id=task_id).count() == 1

# API idempotency keys
@pytest.mark.django_db
def test_api_idempotency(authenticated_client):
    headers = {"HTTP_IDEMPOTENCY_KEY": "test-key-123"}

    response1 = authenticated_client.post("/api/orders/",
        {"items": [{"product_id": 1, "quantity": 1}]}, **headers)
    response2 = authenticated_client.post("/api/orders/",
        {"items": [{"product_id": 1, "quantity": 1}]}, **headers)

    assert response1.json()["id"] == response2.json()["id"]
    assert Order.objects.count() == 1

# get_or_create patterns
@pytest.mark.django_db
def test_user_profile_get_or_create(user):
    profile1, created1 = UserProfile.objects.get_or_create(user=user)
    profile2, created2 = UserProfile.objects.get_or_create(user=user)

    assert created1 is True
    assert created2 is False
    assert profile1.id == profile2.id
```

## Reliability & Resilience Testing

```python
# Testing with django-health-check[^14]
from django.urls import reverse

@pytest.mark.django_db
def test_health_check(client):
    response = client.get(reverse("health_check:health_check_home"))
    assert response.status_code == 200

# Circuit breaker patterns
from unittest.mock import patch, Mock

@pytest.mark.django_db
def test_circuit_breaker_opens_on_failure():
    from apps.core.circuit_breaker import circuit_breaker

    with patch("apps.external.api.call") as mock_call:
        mock_call.side_effect = Exception("Service down")

        # Should fail 5 times and open circuit
        for _ in range(5):
            with pytest.raises(Exception):
                circuit_breaker.call(mock_call)

        assert circuit_breaker.is_open

# Celery[^12] retry testing
from celery.exceptions import Retry

@pytest.mark.django_db
def test_task_retries_on_failure():
    with patch("apps.orders.tasks.send_email") as mock_send:
        mock_send.side_effect = [Exception("Failed"), None]

        from apps.orders.tasks import send_order_email
        send_order_email.retry = Mock(side_effect=Retry())

        with pytest.raises(Retry):
            send_order_email(order_id=1)

        assert send_order_email.retry.called
```

## Compatibility Testing

```toml
# tox.ini[^15] - Django/Python version matrix
[tox]
envlist = py{314}-django{52,60}

[testenv]
deps =
    django52: Django>=5.2,<5.3
    django60: Django>=6.0,<6.1
commands = pytest {posargs}
```

```python
# Database backend testing (SQLite, PostgreSQL)
@pytest.mark.parametrize("database", ["default", "sqlite"])
@pytest.mark.django_db
def test_query_works_on_all_backends(database, user):
    from django.db import connections

    with connections[database].cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM users WHERE id = %s", [user.id])
        count = cursor.fetchone()[0]

    assert count == 1
```

## Internationalization Testing

```python
# Django i18n testing
from django.utils import translation

@pytest.mark.django_db
def test_order_status_translated():
    order = Order.objects.create(status="pending")

    with translation.override("es"):
        assert str(order.get_status_display()) == "Pendiente"

    with translation.override("en"):
        assert str(order.get_status_display()) == "Pending"

# Translation string coverage
def test_all_strings_have_translations():
    from django.conf import settings
    from django.utils.translation import gettext as _

    strings = ["Order created", "Order cancelled"]

    for lang_code, _ in settings.LANGUAGES:
        with translation.override(lang_code):
            for string in strings:
                translated = _(string)
                assert translated != string or lang_code == "en"

# Timezone testing with freezegun[^16]
from freezegun import freeze_time
from django.utils import timezone

@pytest.mark.django_db
@freeze_time("2025-01-15 12:00:00", tz_offset=0)
def test_order_creation_time():
    order = Order.objects.create()
    assert order.created_at == timezone.now()
    assert order.created_at.strftime("%Y-%m-%d") == "2025-01-15"
```

## Data Integrity Testing

```python
# Migration testing
import pytest
from django.core.management import call_command
from django.db import connection

def test_migrations_apply_cleanly():
    call_command("migrate", verbosity=0, interactive=False)

    # Check migrations are applied
    from django.db.migrations.recorder import MigrationRecorder
    recorder = MigrationRecorder(connection)
    applied = recorder.applied_migrations()
    assert len(applied) > 0

# Constraint testing
@pytest.mark.django_db
def test_unique_constraint_enforced():
    from django.db import IntegrityError

    User.objects.create(email="test@example.com", password="pass")

    with pytest.raises(IntegrityError):
        User.objects.create(email="test@example.com", password="pass2")

# Transaction.atomic testing
@pytest.mark.django_db
def test_transaction_rollback_on_error():
    from django.db import transaction

    initial_count = Order.objects.count()

    with pytest.raises(ValueError):
        with transaction.atomic():
            Order.objects.create()
            raise ValueError("Rollback")

    assert Order.objects.count() == initial_count
```

## A/B Testing & Feature Flags

```python
# django-waffle[^17] for feature flags
from waffle.testutils import override_flag

@pytest.mark.django_db
@override_flag("new_checkout_flow", active=True)
def test_new_checkout_flow_enabled(authenticated_client):
    response = authenticated_client.get("/checkout/")
    assert b"new-checkout" in response.content

@pytest.mark.django_db
@override_flag("new_checkout_flow", active=False)
def test_old_checkout_flow_enabled(authenticated_client):
    response = authenticated_client.get("/checkout/")
    assert b"old-checkout" in response.content

# Testing flag states
@pytest.mark.django_db
def test_feature_flag_percentage_rollout():
    from waffle.models import Flag

    flag = Flag.objects.create(name="beta_feature", percent=50.0)

    enabled_count = 0
    for i in range(100):
        user = User.objects.create(email=f"user{i}@example.com")
        if flag.is_active_for_user(user):
            enabled_count += 1

    # Should be roughly 50% enabled
    assert 40 <= enabled_count <= 60
```

## See Also

- [Python Guide](../python.md) - Base Python conventions and tooling
- [Testing Guide](../testing.md) - General testing principles and patterns
- [CI Guide](../ci.md) - Continuous integration best practices

## References

[^1]: [Ruff](https://docs.astral.sh/ruff/) - An extremely fast Python linter and code formatter, written in Rust
[^2]: [django-stubs](https://github.com/typeddjango/django-stubs) - Type stubs and mypy plugin for Django
[^3]: [django-csp](https://django-csp.readthedocs.io/) - Content Security Policy for Django (legacy; use built-in CSP in Django 6.0+)
[^4]: [Bandit](https://bandit.readthedocs.io/) - Security linter for Python
[^5]: [pytest-django](https://pytest-django.readthedocs.io/) - A Django plugin for pytest
[^6]: [pytest-cov](https://pytest-cov.readthedocs.io/) - Coverage plugin for pytest
[^7]: [Squawk](https://squawkhq.com/) - Linter for PostgreSQL migrations
[^8]: [pytest-xdist](https://pytest-xdist.readthedocs.io/) - pytest plugin for distributed testing
[^9]: [Django REST Framework](https://www.django-rest-framework.org/) - Powerful and flexible toolkit for building Web APIs
[^10]: [pytest-bdd](https://pytest-bdd.readthedocs.io/) - BDD library for pytest
[^11]: [Playwright](https://playwright.dev/python/) - Browser automation library
[^12]: [Celery](https://docs.celeryq.dev/) - Distributed task queue for Python
[^13]: [django-celery-results](https://django-celery-results.readthedocs.io/) - Celery result backend using Django ORM
[^14]: [django-health-check](https://django-health-check.readthedocs.io/) - Django health check endpoint
[^15]: [tox](https://tox.wiki/) - Generic virtualenv management and test command line tool
[^16]: [freezegun](https://github.com/spulec/freezegun) - Library for mocking the datetime module
[^17]: [django-waffle](https://waffle.readthedocs.io/) - Feature flags for Django

