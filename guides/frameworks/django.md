# Django Style Guide

> [Doctrine](../../README.md) > [Frameworks](../README.md) > Django

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119][rfc2119].

[rfc2119]: https://datatracker.ietf.org/doc/html/rfc2119

Extends [Python style guide](python.md) with Django-specific conventions from
[Django coding style](https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/).

## Quick Reference

All Python tooling applies. Projects **MUST** use the additional
Django-specific tools:

| Task | Tool | Command |
| ---- | ---- | ------- |
| Lint | Ruff[^1] + django rules | `uv run ruff check .` |
| Format | Ruff[^1] | `uv run ruff format .` |
| Type check | django-stubs[^2] | `uv run mypy .` |
| Security | Built-in CSP (6.0+), bandit[^4] | `uv run bandit -r .` |
| Auth | django-allauth[^18] | Social OAuth2, MFA |
| JWT | djangorestframework-simplejwt[^19] | API token auth |
| Object perms | django-guardian[^20] | Object-level permissions |
| Test | pytest-django[^5] | `uv run pytest` |
| Coverage | pytest-cov[^6] | `uv run pytest --cov` |
| Migrations | squawk[^7] | `squawk migrations/*.sql` |
| Profiling | django-silk[^21] | Request/query profiling |
| Observability | OpenTelemetry[^22] | `opentelemetry-instrument` |
| Caching | django-redis[^23] | Redis cache backend |
| Rate limiting | django-ratelimit[^24] | View-level throttling |
| Circuit breaker | pybreaker[^25] | Fault tolerance |
| WebSocket | Django Channels[^26] | Real-time communication |

## Project Structure

```text
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

- Catches Django-specific anti-patterns (nullable string fields,
  model `__str__` methods)
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

- Provides accurate type stubs for Django's dynamic APIs
  (QuerySets, managers, model fields)
- Catches common errors: missing `null=True`, incorrect field types,
  invalid query methods
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

## Signals

Projects **MAY** use Django signals for decoupled event handling. Signals
**SHOULD** be used sparingly and only for cross-app communication.

### Why Signals

- **Decoupling**: Allow apps to react to events without hard dependencies
- **Cross-cutting concerns**: Handle logging, caching, notifications across apps
- **Framework hooks**: React to model lifecycle events (save, delete)

### When to Avoid Signals

- **Within the same app**: Use direct function calls or services instead
- **Business logic**: Keep critical logic explicit and traceable in services
- **Complex flows**: Signals make debugging harder due to implicit execution

### Built-in Signals

```python
# apps/orders/signals.py
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.core.cache import cache

from .models import Order

@receiver(post_save, sender=Order)
def order_saved(sender, instance, created, **kwargs):
    """Handle order save events."""
    if created:
        # New order created
        from apps.notifications.tasks import send_order_notification
        send_order_notification.delay(instance.id)
    else:
        # Order updated - invalidate cache
        cache.delete(f"order:{instance.id}")

@receiver(post_delete, sender=Order)
def order_deleted(sender, instance, **kwargs):
    """Clean up when order is deleted."""
    cache.delete(f"order:{instance.id}")
    cache.delete(f"user:{instance.user_id}:orders")

@receiver(pre_save, sender=Order)
def validate_order(sender, instance, **kwargs):
    """Validate order before saving."""
    if instance.total < 0:
        raise ValueError("Order total cannot be negative")
```

### Registering Signals

```python
# apps/orders/apps.py
from django.apps import AppConfig

class OrdersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.orders"

    def ready(self):
        # Import signals to register them
        from . import signals  # noqa: F401
```

### Custom Signals

```python
# apps/orders/signals.py
from django.dispatch import Signal

# Define custom signals
order_completed = Signal()  # Provides: order, user
payment_received = Signal()  # Provides: order, amount, transaction_id

# Emit signal from service
# apps/orders/services.py
from .signals import order_completed

def complete_order(order: Order) -> None:
    order.status = "completed"
    order.save()

    # Emit signal for other apps to react
    order_completed.send(
        sender=Order,
        order=order,
        user=order.user,
    )
```

```python
# apps/analytics/signals.py
from django.dispatch import receiver
from apps.orders.signals import order_completed

@receiver(order_completed)
def track_order_completion(sender, order, user, **kwargs):
    """Track order completion for analytics."""
    from .services import track_event

    track_event(
        event="order_completed",
        user_id=user.id,
        properties={"order_id": order.id, "total": order.total},
    )
```

### Request/Response Signals

```python
# apps/core/signals.py
from django.core.signals import request_started, request_finished
from django.dispatch import receiver
import time
import threading

_request_times = threading.local()

@receiver(request_started)
def log_request_start(sender, environ, **kwargs):
    """Track request start time."""
    _request_times.start = time.time()

@receiver(request_finished)
def log_request_end(sender, **kwargs):
    """Log request duration."""
    if hasattr(_request_times, "start"):
        duration = time.time() - _request_times.start
        if duration > 1.0:  # Log slow requests
            import logging
            logging.warning(f"Slow request: {duration:.2f}s")
```

### Signal Best Practices

```python
# GOOD: Async signal handler for non-critical work
@receiver(post_save, sender=Order)
def handle_order_save(sender, instance, created, **kwargs):
    if created:
        # Offload to background task
        send_notification_task.delay(instance.id)

# BAD: Blocking work in signal handler
@receiver(post_save, sender=Order)
def bad_handle_order_save(sender, instance, created, **kwargs):
    if created:
        # This blocks the request!
        send_email_synchronously(instance)
        call_external_api(instance)

# GOOD: Use dispatch_uid to prevent duplicate registration
@receiver(post_save, sender=Order, dispatch_uid="order_post_save_unique")
def unique_handler(sender, instance, **kwargs):
    pass

# GOOD: Handle exceptions gracefully
@receiver(post_save, sender=Order)
def safe_handler(sender, instance, **kwargs):
    try:
        external_service.notify(instance)
    except Exception:
        import logging
        logging.exception("Failed to notify external service")
```

### Testing Signals

```python
# tests/test_signals.py
import pytest
from django.db.models.signals import post_save
from unittest.mock import patch, MagicMock

from apps.orders.models import Order
from apps.orders.signals import order_saved

@pytest.mark.django_db
def test_order_saved_signal_sends_notification():
    with patch("apps.notifications.tasks.send_order_notification.delay") as mock:
        Order.objects.create(user_id=1, total=100)
        mock.assert_called_once()

@pytest.mark.django_db
def test_signal_disabled_during_test():
    """Disconnect signal for isolated testing."""
    post_save.disconnect(order_saved, sender=Order)

    try:
        with patch("apps.notifications.tasks.send_order_notification.delay") as mock:
            Order.objects.create(user_id=1, total=100)
            mock.assert_not_called()
    finally:
        post_save.connect(order_saved, sender=Order)

# Using factory_boy's mute_signals
from factory.django import mute_signals

@pytest.mark.django_db
@mute_signals(post_save)
def test_with_muted_signals():
    # Signals won't fire during this test
    Order.objects.create(user_id=1, total=100)
```

## Custom Middleware

Projects **MAY** create custom middleware for cross-cutting concerns.
Middleware **SHOULD** be minimal and focused.

### Why Middleware

- **Request/response processing**: Modify all requests or responses uniformly
- **Cross-cutting concerns**: Authentication, logging, CORS, security headers
- **Global error handling**: Catch and process exceptions consistently

### Middleware Structure

```python
# apps/core/middleware.py
from django.http import HttpRequest, HttpResponse
from typing import Callable

class TimingMiddleware:
    """Add request timing to response headers."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        import time
        start = time.time()

        response = self.get_response(request)

        duration = time.time() - start
        response["X-Request-Duration"] = f"{duration:.4f}"
        return response
```

### Request Logging Middleware

```python
# apps/core/middleware.py
import logging
import uuid

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware:
    """Log all requests with correlation IDs."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Generate or extract correlation ID
        request.correlation_id = request.headers.get(
            "X-Correlation-ID",
            str(uuid.uuid4())
        )

        # Log request
        logger.info(
            "Request started",
            extra={
                "correlation_id": request.correlation_id,
                "method": request.method,
                "path": request.path,
                "user_id": getattr(request.user, "id", None),
            }
        )

        response = self.get_response(request)

        # Add correlation ID to response
        response["X-Correlation-ID"] = request.correlation_id

        # Log response
        logger.info(
            "Request completed",
            extra={
                "correlation_id": request.correlation_id,
                "status_code": response.status_code,
            }
        )

        return response
```

### JSON Exception Middleware

```python
# apps/core/middleware.py
import json
import logging
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404

logger = logging.getLogger(__name__)

class JSONExceptionMiddleware:
    """Convert exceptions to JSON responses for API endpoints."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        # Only handle API requests
        if not request.path.startswith("/api/"):
            return None

        if isinstance(exception, Http404):
            return JsonResponse({"error": "Not found"}, status=404)

        if isinstance(exception, PermissionDenied):
            return JsonResponse({"error": "Permission denied"}, status=403)

        if isinstance(exception, ValidationError):
            return JsonResponse(
                {"error": "Validation error", "details": exception.messages},
                status=400
            )

        # Log unexpected errors
        logger.exception("Unhandled exception", extra={
            "path": request.path,
            "user_id": getattr(request.user, "id", None),
        })

        return JsonResponse(
            {"error": "Internal server error"},
            status=500
        )
```

### Async Middleware

```python
# apps/core/middleware.py
from django.utils.decorators import sync_and_async_middleware

@sync_and_async_middleware
def hybrid_middleware(get_response):
    """Middleware that works in both sync and async contexts."""

    if asyncio.iscoroutinefunction(get_response):
        async def middleware(request):
            # Async-specific setup
            response = await get_response(request)
            return response
    else:
        def middleware(request):
            # Sync-specific setup
            response = get_response(request)
            return response

    return middleware
```

### Registering Middleware

```python
# config/settings/base.py
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # Custom middleware early for timing/logging
    "apps.core.middleware.RequestLoggingMiddleware",
    "apps.core.middleware.TimingMiddleware",
    # Standard Django middleware
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # Custom exception handling after auth
    "apps.core.middleware.JSONExceptionMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
```

### Middleware Best Practices

```python
# GOOD: Short-circuit early for specific paths
class ApiOnlyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith("/api/"):
            return self.get_response(request)

        # API-specific processing
        return self.get_response(request)

# GOOD: Use process_view for view-specific logic
class ViewSpecificMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Access view function and its attributes
        if hasattr(view_func, "skip_middleware"):
            return None
        # Return None to continue, or HttpResponse to short-circuit

# GOOD: Clean up in process_response
class ResourceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.resource = acquire_resource()
        try:
            return self.get_response(request)
        finally:
            release_resource(request.resource)
```

### Testing Middleware

```python
# tests/test_middleware.py
import pytest
from django.test import RequestFactory
from apps.core.middleware import TimingMiddleware

@pytest.fixture
def request_factory():
    return RequestFactory()

def test_timing_middleware_adds_header(request_factory):
    def get_response(request):
        from django.http import HttpResponse
        return HttpResponse("OK")

    middleware = TimingMiddleware(get_response)
    request = request_factory.get("/")

    response = middleware(request)

    assert "X-Request-Duration" in response
    assert float(response["X-Request-Duration"]) >= 0

@pytest.mark.django_db
def test_json_exception_middleware_handles_404(client):
    response = client.get("/api/nonexistent/")

    assert response.status_code == 404
    assert response.json()["error"] == "Not found"
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

**Why**: Django 6.0's built-in CSP support eliminates the need for third-party
packages and provides first-class integration with Django's security middleware.

## Authentication with django-allauth

Projects **SHOULD** use django-allauth[^18] for authentication when OAuth2/social login is required:

```bash
uv add django-allauth
```

```python
# config/settings/base.py
INSTALLED_APPS = [
    # ...
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.github",
    "allauth.mfa",  # Multi-factor authentication
]

MIDDLEWARE = [
    # ...
    "allauth.account.middleware.AccountMiddleware",
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

# Account settings
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_VERIFICATION = "mandatory"

# MFA settings
MFA_ADAPTER = "allauth.mfa.adapter.DefaultMFAAdapter"
MFA_FORMS = {
    "authenticate": "allauth.mfa.forms.AuthenticateForm",
    "reauthenticate": "allauth.mfa.forms.ReauthenticateForm",
}
```

```python
# config/urls.py
urlpatterns = [
    path("accounts/", include("allauth.urls")),
    # ...
]
```

### Why

- Provides OAuth2 social login for 50+ providers (Google, GitHub, Microsoft, etc.)
- Built-in MFA/2FA support with TOTP and recovery codes
- Handles email verification, password reset, and account management
- Extensible adapter pattern for customization
- Battle-tested in production at scale

## JWT Authentication for APIs

Projects using REST APIs **SHOULD** use djangorestframework-simplejwt[^19] for token-based authentication:

```bash
uv add djangorestframework-simplejwt
```

```python
# config/settings/base.py
from datetime import timedelta

INSTALLED_APPS = [
    # ...
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",  # For token revocation
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,  # Use a dedicated key in production
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
}
```

```python
# config/urls.py
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenBlacklistView,
)

urlpatterns = [
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/token/blacklist/", TokenBlacklistView.as_view(), name="token_blacklist"),
]
```

### Why SimpleJWT

- Stateless authentication suitable for microservices and mobile apps
- Short-lived access tokens with longer-lived refresh tokens
- Token blacklisting for logout and revocation
- Works seamlessly with Django REST Framework

## Object-Level Permissions with django-guardian

Projects requiring fine-grained permissions **SHOULD** use django-guardian[^20]:

```bash
uv add django-guardian
```

```python
# config/settings/base.py
INSTALLED_APPS = [
    # ...
    "guardian",
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "guardian.backends.ObjectPermissionBackend",
]

# Anonymous user for guardian
ANONYMOUS_USER_NAME = None  # Disable anonymous user
```

```python
# apps/projects/models.py
from django.db import models
from guardian.shortcuts import assign_perm

class Project(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey("users.User", on_delete=models.CASCADE)

    class Meta:
        permissions = [
            ("view_project", "Can view project"),
            ("edit_project", "Can edit project"),
            ("manage_members", "Can manage project members"),
        ]

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            # Assign all permissions to owner
            assign_perm("view_project", self.owner, self)
            assign_perm("edit_project", self.owner, self)
            assign_perm("manage_members", self.owner, self)
```

```python
# apps/projects/views.py
from guardian.mixins import PermissionRequiredMixin
from guardian.shortcuts import get_objects_for_user

class ProjectDetailView(PermissionRequiredMixin, DetailView):
    model = Project
    permission_required = "projects.view_project"
    raise_exception = True

# In services/selectors
def get_user_projects(user: User) -> QuerySet[Project]:
    """Get all projects the user has view permission for."""
    return get_objects_for_user(user, "projects.view_project", Project)
```

```python
# DRF integration
from rest_framework import permissions
from guardian.shortcuts import get_perms

class HasObjectPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        perms = get_perms(request.user, obj)
        if request.method in permissions.SAFE_METHODS:
            return "view_project" in perms
        return "edit_project" in perms
```

### Why django-guardian

- Enables per-object permissions (user A can edit project X but not Y)
- Essential for multi-tenant applications
- Integrates with Django's permission framework
- Works with Django admin and DRF

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

**Why**: For simple task queuing, Django's built-in framework reduces
dependencies. For complex workflows (retries, scheduling, priorities),
Celery remains the better choice.

| Use Case | Recommended |
| -------- | ----------- |
| Simple email sending | Django Tasks |
| Fire-and-forget jobs | Django Tasks |
| Complex retry logic | Celery |
| Scheduled/periodic tasks | Celery Beat |
| Task chaining/workflows | Celery |

## Production Background Tasks with Celery

Projects with complex async requirements **SHOULD** use Celery[^12] with django-celery-beat[^29]:

```bash
uv add celery redis django-celery-beat django-celery-results
```

```python
# config/celery.py
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

app = Celery("myproject")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Production-ready defaults
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes hard limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    worker_prefetch_multiplier=1,  # Disable prefetching for long tasks
    task_acks_late=True,  # Acknowledge after completion
    task_reject_on_worker_lost=True,
)
```

```python
# config/settings/base.py
INSTALLED_APPS = [
    # ...
    "django_celery_beat",
    "django_celery_results",
]

CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "django-db"
CELERY_CACHE_BACKEND = "django-cache"

CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
```

```python
# apps/orders/tasks.py
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

@shared_task(
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=5,
)
def process_payment(self, order_id: int) -> dict:
    """Process payment with automatic retry on transient failures."""
    try:
        order = Order.objects.get(id=order_id)
        result = payment_gateway.charge(order)
        order.mark_paid(transaction_id=result.id)
        return {"status": "success", "transaction_id": result.id}
    except SoftTimeLimitExceeded:
        # Clean up and re-raise
        order.mark_payment_timeout()
        raise

@shared_task(bind=True)
def send_bulk_emails(self, user_ids: list[int]) -> dict:
    """Send emails with progress tracking."""
    total = len(user_ids)
    for i, user_id in enumerate(user_ids):
        send_email_to_user(user_id)
        self.update_state(
            state="PROGRESS",
            meta={"current": i + 1, "total": total}
        )
    return {"sent": total}
```

### Celery Best Practices

Projects **MUST** follow these Celery patterns:

```python
# GOOD: Idempotent tasks with unique task IDs
from celery import shared_task
from django.core.cache import cache

@shared_task(bind=True)
def process_order(self, order_id: int) -> dict:
    lock_key = f"process_order_{order_id}"

    # Prevent duplicate processing
    if not cache.add(lock_key, self.request.id, timeout=3600):
        return {"status": "already_processing"}

    try:
        order = Order.objects.select_for_update().get(id=order_id)
        if order.processed:
            return {"status": "already_processed"}
        # Process order...
        order.processed = True
        order.save()
        return {"status": "success"}
    finally:
        cache.delete(lock_key)

# GOOD: Pass IDs, not objects (objects can't be serialized to JSON)
@shared_task
def notify_user(user_id: int, message: str) -> None:
    user = User.objects.get(id=user_id)
    send_notification(user, message)

# BAD: Passing model instances
@shared_task
def bad_notify_user(user: User, message: str) -> None:  # Will fail!
    send_notification(user, message)
```

### Periodic Tasks with django-celery-beat

```python
# Configure via Django admin or programmatically
from django_celery_beat.models import PeriodicTask, CrontabSchedule

# Run daily at midnight UTC
schedule, _ = CrontabSchedule.objects.get_or_create(
    minute="0",
    hour="0",
    day_of_week="*",
    day_of_month="*",
    month_of_year="*",
)

PeriodicTask.objects.create(
    crontab=schedule,
    name="Daily cleanup",
    task="apps.core.tasks.cleanup_old_records",
)
```

### Why Celery

- Robust retry mechanisms with exponential backoff and jitter
- Task result storage for monitoring and debugging
- Periodic task scheduling via django-celery-beat
- Horizontal scaling with multiple workers and queues
- Battle-tested in high-traffic production environments

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

**Why**: Template partials enable component-style reuse without separate files,
reducing template sprawl while maintaining clear boundaries.

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

**Why**: Composite primary keys are useful for join tables and entities with
natural multi-column identifiers. Use when the combination of fields is the
true identity.

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

**Why**: Mixing sync auth calls in async views causes performance issues.
Django 5.2+ provides native async variants for all authentication operations.

### Async Best Practices

Projects **MUST** follow these async patterns:

```python
# GOOD: Fully async view with async ORM operations
async def order_list(request):
    orders = [
        order async for order in
        Order.objects.filter(user=request.user).select_related("user")
    ]
    return JsonResponse({"orders": [serialize_order(o) for o in orders]})

# GOOD: Async pagination (Django 6.0+)
from django.core.paginator import AsyncPaginator

async def paginated_orders(request):
    queryset = Order.objects.filter(user=request.user)
    paginator = AsyncPaginator(queryset, per_page=25)
    page = await paginator.aget_page(request.GET.get("page", 1))
    return JsonResponse({
        "orders": [serialize_order(o) async for o in page],
        "has_next": await page.ahas_next(),
        "has_previous": await page.ahas_previous(),
    })

# BAD: Mixing sync ORM in async view (causes thread pool exhaustion)
async def bad_order_list(request):
    orders = list(Order.objects.filter(user=request.user))  # Blocks!
    return JsonResponse({"orders": orders})
```

### When to Use Async

| Use Case | Sync | Async |
| -------- | ---- | ----- |
| Simple CRUD | Preferred | Optional |
| I/O-bound (external APIs) | | Preferred |
| WebSocket/real-time | | Required |
| High concurrency (>1000 req/s) | | Preferred |
| CPU-bound processing | Preferred | |

## WebSocket with Django Channels

Projects requiring real-time communication **MUST** use Django Channels[^26]:

```bash
uv add channels channels-redis daphne
```

```python
# config/settings/base.py
INSTALLED_APPS = [
    "daphne",  # Must be first for ASGI
    "django.contrib.admin",
    # ...
    "channels",
]

ASGI_APPLICATION = "config.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
            "capacity": 1500,
            "expiry": 10,
        },
    },
}
```

```python
# config/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

django_asgi_app = get_asgi_application()

from apps.chat.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
```

```python
# apps/chat/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<room_name>\w+)/$", consumers.ChatConsumer.as_asgi()),
]
```

```python
# apps/chat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data["message"]

        # Broadcast to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat.message",
                "message": message,
                "user": self.scope["user"].email,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "message": event["message"],
            "user": event["user"],
        }))
```

### ASGI Server Selection

| Server | Use Case | Command |
| ------ | -------- | ------- |
| Daphne[^27] | WebSocket + HTTP, Django Channels | See below |
| Uvicorn[^28] | High-performance HTTP, optional WS | See below |
| Gunicorn + Uvicorn | Production with workers | See below |

```bash
# Daphne
daphne config.asgi:application

# Uvicorn
uvicorn config.asgi:application

# Gunicorn + Uvicorn
gunicorn config.asgi:application -k uvicorn.workers.UvicornWorker
```

### Why ASGI

- Django Channels extends Django to handle WebSocket, HTTP2, and other protocols
- Redis channel layer enables horizontal scaling across multiple server instances
- AsyncWebsocketConsumer provides clean async/await syntax
- Daphne auto-negotiates between HTTP and WebSocket on the same port

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

## Performance Profiling

### Development Profiling with django-silk

Projects **SHOULD** use django-silk[^21] for development and staging profiling:

```bash
uv add --dev django-silk
```

```python
# config/settings/development.py
INSTALLED_APPS = [
    # ...
    "silk",
]

MIDDLEWARE = [
    "silk.middleware.SilkyMiddleware",
    # ... other middleware
]

SILKY_PYTHON_PROFILER = True
SILKY_PYTHON_PROFILER_BINARY = True
SILKY_META = True  # Track silk's own overhead
SILKY_MAX_RECORDED_REQUESTS = 10000
SILKY_MAX_REQUEST_BODY_SIZE = -1  # No limit in dev
SILKY_INTERCEPT_PERCENT = 100  # Profile all requests
```

```python
# config/urls.py (development only)
if settings.DEBUG:
    urlpatterns += [path("silk/", include("silk.urls", namespace="silk"))]
```

```python
# Profile specific code blocks
from silk.profiling.profiler import silk_profile

@silk_profile(name="Complex calculation")
def calculate_order_totals(order_ids: list[int]) -> dict:
    # This function will be profiled
    return {oid: calculate_total(oid) for oid in order_ids}

# Or use as context manager
def process_batch(items: list):
    with silk_profile(name="Batch processing"):
        for item in items:
            process_item(item)
```

### Why django-silk

- Persists profiling data across requests (unlike django-debug-toolbar)
- Works with REST APIs and non-HTML responses
- Shows SQL query analysis, N+1 detection, and execution plans
- Python cProfile integration for CPU profiling

### Production Observability with OpenTelemetry

Projects **MUST** use OpenTelemetry[^22] for production observability:

```bash
uv add opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-django \
    opentelemetry-instrumentation-psycopg2 opentelemetry-instrumentation-redis \
    opentelemetry-exporter-otlp
```

```python
# config/settings/production.py
INSTALLED_APPS = [
    # ...
    "opentelemetry.instrumentation.django",
]

# OpenTelemetry configuration
OTEL_SERVICE_NAME = "myproject"
OTEL_EXPORTER_OTLP_ENDPOINT = "http://otel-collector:4317"
```

```python
# config/otel.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor

def configure_opentelemetry():
    resource = Resource.create({"service.name": "myproject"})
    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(OTLPSpanExporter())
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    # Auto-instrument Django, database, and Redis
    DjangoInstrumentor().instrument()
    Psycopg2Instrumentor().instrument()
    RedisInstrumentor().instrument()
```

```python
# apps/orders/services.py
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

def order_create(*, user: User, items: list[dict]) -> Order:
    with tracer.start_as_current_span("order_create") as span:
        span.set_attribute("user.id", user.id)
        span.set_attribute("items.count", len(items))

        with tracer.start_as_current_span("validate_items"):
            validated_items = validate_items(items)

        with tracer.start_as_current_span("create_order"):
            order = Order.objects.create(user=user)
            # ...

        span.set_attribute("order.id", order.id)
        return order
```

### Why OpenTelemetry

- Vendor-neutral observability standard (works with Jaeger, Datadog, Honeycomb, etc.)
- Distributed tracing across microservices
- Automatic instrumentation for Django, databases, and HTTP clients
- Production-safe with minimal overhead via sampling

## Caching with django-redis

Projects **SHOULD** use django-redis[^23] for caching:

```bash
uv add django-redis
```

```python
# config/settings/base.py
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
            "CONNECTION_POOL_KWARGS": {
                "max_connections": 50,
                "retry_on_timeout": True,
            },
            "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
        },
        "KEY_PREFIX": "myproject",
        "TIMEOUT": 300,  # 5 minutes default
    }
}

# Use Redis for sessions
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"
```

### Cache Patterns

```python
# apps/products/selectors.py
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

def get_product(product_id: int) -> Product | None:
    """Cache-aside pattern with automatic invalidation."""
    cache_key = f"product:{product_id}"
    product = cache.get(cache_key)

    if product is None:
        try:
            product = Product.objects.get(id=product_id)
            cache.set(cache_key, product, timeout=3600)
        except Product.DoesNotExist:
            return None

    return product

@receiver([post_save, post_delete], sender=Product)
def invalidate_product_cache(sender, instance, **kwargs):
    """Invalidate cache when product changes."""
    cache.delete(f"product:{instance.id}")
    cache.delete("products:list")  # Invalidate list cache too
```

### Cache Versioning

```python
# config/settings/base.py
CACHE_VERSION = 1  # Increment to invalidate all caches on deploy

CACHES = {
    "default": {
        # ...
        "VERSION": CACHE_VERSION,
    }
}

# Or use per-key versioning for rolling updates
def get_cached_report(report_id: int, version: int = 1) -> dict:
    cache_key = f"report:{report_id}:v{version}"
    report = cache.get(cache_key)
    if report is None:
        report = generate_report(report_id)
        cache.set(cache_key, report, timeout=86400)
    return report
```

### Preventing Cache Stampedes

```python
# apps/core/cache.py
import time
from django.core.cache import cache
from functools import wraps

def cache_with_stale(key: str, timeout: int, stale_timeout: int = 60):
    """Return stale data while refreshing in background."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            data = cache.get(key)
            if data is not None:
                value, expires_at = data
                if time.time() < expires_at:
                    return value
                # Stale but usable - refresh async
                if time.time() < expires_at + stale_timeout:
                    # Trigger background refresh (via Celery)
                    refresh_cache_async.delay(key, func.__name__, args, kwargs)
                    return value

            # Cache miss - compute synchronously
            value = func(*args, **kwargs)
            cache.set(key, (value, time.time() + timeout), timeout + stale_timeout)
            return value
        return wrapper
    return decorator
```

### Why django-redis

- Native Redis features (pub/sub, Lua scripts, pipelining)
- Connection pooling for high concurrency
- Compression support for large objects
- Seamless integration with Django's cache framework

## Rate Limiting

### View-Level Rate Limiting with django-ratelimit

Projects **SHOULD** use django-ratelimit[^24] for view-level throttling:

```bash
uv add django-ratelimit
```

```python
# apps/api/views.py
from django_ratelimit.decorators import ratelimit
from django_ratelimit.exceptions import Ratelimited

@ratelimit(key="user_or_ip", rate="100/h", method="POST", block=True)
def create_order(request):
    # Limited to 100 POST requests per hour per user/IP
    return order_create(...)

@ratelimit(key="ip", rate="10/m", method="GET", block=True)
def expensive_report(request):
    # Limited to 10 requests per minute per IP
    return generate_report(...)

# Custom key function
def get_api_key(group, request):
    return request.headers.get("X-API-Key", request.META.get("REMOTE_ADDR"))

@ratelimit(key=get_api_key, rate="1000/d", block=True)
def api_endpoint(request):
    return process_request(...)
```

```python
# config/settings/base.py
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = "default"  # Use Redis cache
RATELIMIT_VIEW = "apps.core.views.rate_limited"  # Custom 429 handler
```

### DRF Throttling for APIs

Projects using Django REST Framework **SHOULD** use built-in throttling:

```python
# config/settings/base.py
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/day",
        "user": "1000/day",
        "uploads": "20/day",
        "burst": "60/min",
    },
}
```

```python
# apps/api/views.py
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

class UploadView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "uploads"

    def post(self, request):
        # Limited to 20 uploads per day per user
        return handle_upload(request.data)

# Custom throttle for API keys
class APIKeyThrottle(UserRateThrottle):
    scope = "api_key"

    def get_cache_key(self, request, view):
        api_key = request.headers.get("Authorization", "").replace("Bearer ", "")
        if api_key:
            return f"throttle_{self.scope}_{api_key}"
        return None
```

### Why Rate Limiting

- Prevents abuse and denial-of-service attacks
- Ensures fair resource distribution among users
- Protects expensive endpoints from overuse
- Required for public APIs and SaaS applications

## Circuit Breakers with pybreaker

Projects calling external services **SHOULD** use pybreaker[^25]:

```bash
uv add pybreaker
```

```python
# apps/core/circuit_breakers.py
import pybreaker
from django_redis import get_redis_connection

# Redis-backed circuit breaker for distributed state
redis_conn = get_redis_connection("default")

payment_breaker = pybreaker.CircuitBreaker(
    fail_max=5,  # Open after 5 failures
    reset_timeout=60,  # Try again after 60 seconds
    state_storage=pybreaker.CircuitRedisStorage(
        pybreaker.STATE_CLOSED,
        redis_conn,
        namespace="payment_service",
    ),
    listeners=[pybreaker.CircuitBreakerListener()],
)

email_breaker = pybreaker.CircuitBreaker(
    fail_max=3,
    reset_timeout=120,
    state_storage=pybreaker.CircuitRedisStorage(
        pybreaker.STATE_CLOSED,
        redis_conn,
        namespace="email_service",
    ),
)
```

```python
# apps/orders/services.py
import pybreaker
from apps.core.circuit_breakers import payment_breaker

class PaymentServiceUnavailable(Exception):
    pass

@payment_breaker
def process_payment(order: Order) -> PaymentResult:
    """Process payment with circuit breaker protection."""
    response = requests.post(
        "https://payment.example.com/charge",
        json={"order_id": order.id, "amount": order.total},
        timeout=10,
    )
    response.raise_for_status()
    return PaymentResult(**response.json())

def create_order_with_payment(user: User, items: list) -> Order:
    order = order_create(user=user, items=items)

    try:
        result = process_payment(order)
        order.mark_paid(transaction_id=result.id)
    except pybreaker.CircuitBreakerError:
        # Circuit is open - fail fast
        order.mark_payment_pending()
        enqueue_retry_payment.delay(order.id)
        raise PaymentServiceUnavailable("Payment service temporarily unavailable")

    return order
```

```python
# Health check integration
from apps.core.circuit_breakers import payment_breaker, email_breaker

def get_circuit_breaker_status() -> dict:
    return {
        "payment": {
            "state": payment_breaker.current_state,
            "fail_count": payment_breaker.fail_counter,
        },
        "email": {
            "state": email_breaker.current_state,
            "fail_count": email_breaker.fail_counter,
        },
    }
```

### Circuit Breaker States

| State | Behavior |
| ----- | -------- |
| Closed | Normal operation, requests pass through |
| Open | Requests fail immediately, no external calls |
| Half-Open | Limited requests to test if service recovered |

### Why Circuit Breakers

- Prevents cascade failures when external services are down
- Fails fast instead of waiting for timeouts
- Gives failing services time to recover
- Redis-backed state enables distributed circuit breakers

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

## Feature Flags with django-waffle

Projects **SHOULD** use django-waffle[^17] for feature flags and A/B testing:

```bash
uv add django-waffle
```

```python
# config/settings/base.py
INSTALLED_APPS = [
    # ...
    "waffle",
]

MIDDLEWARE = [
    # ...
    "waffle.middleware.WaffleMiddleware",
]

# Auto-create missing flags in database (development only)
WAFFLE_CREATE_MISSING_FLAGS = DEBUG

# Cache flag lookups
WAFFLE_CACHE_PREFIX = "waffle:"
```

### Flag Types

| Type | Use Case | Example |
| ---- | -------- | ------- |
| Flag | Gradual rollout, user targeting | "new_checkout_flow" |
| Switch | Global on/off toggle | "maintenance_mode" |
| Sample | Random percentage of requests | "analytics_sampling" |

### Using Flags in Views and Templates

```python
# apps/checkout/views.py
import waffle

def checkout(request):
    if waffle.flag_is_active(request, "new_checkout_flow"):
        return render(request, "checkout/new.html")
    return render(request, "checkout/legacy.html")

# Or use the decorator
from waffle.decorators import waffle_flag

@waffle_flag("new_checkout_flow")
def new_checkout(request):
    return render(request, "checkout/new.html")

# Switch for global toggles
def api_endpoint(request):
    if waffle.switch_is_active("maintenance_mode"):
        return JsonResponse({"error": "Under maintenance"}, status=503)
    return process_request(request)
```

```html
<!-- templates/checkout.html -->
{% load waffle_tags %}

{% flag "new_checkout_flow" %}
    <!-- New checkout UI -->
{% else %}
    <!-- Legacy checkout UI -->
{% endflag %}

{% switch "show_banner" %}
    <div class="promo-banner">Special offer!</div>
{% endswitch %}
```

### Gradual Rollout Pattern

```python
# Rollout to percentage of users
from waffle.models import Flag

# Create flag via admin or programmatically
flag = Flag.objects.create(
    name="new_feature",
    percent=10.0,  # 10% of users
    rollout=True,  # Sticky - user stays in same bucket
    superusers=True,  # Always on for superusers
)

# Increase rollout gradually
flag.percent = 25.0  # Now 25%
flag.save()

# Full rollout
flag.percent = 100.0
flag.everyone = True  # Or just flip to everyone
flag.save()
```

### Testing Feature Flags

```python
# tests/test_checkout.py
from waffle.testutils import override_flag, override_switch

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

@pytest.mark.django_db
@override_switch("maintenance_mode", active=True)
def test_maintenance_mode(client):
    response = client.get("/api/endpoint/")
    assert response.status_code == 503

# Testing percentage rollout
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

### Why django-waffle

- Gradual rollouts with percentage-based targeting
- User and group targeting for beta features
- Sticky flags ensure consistent user experience
- Admin UI for non-developer flag management
- Audit trail via Django admin logs

## See Also

- [Python Guide](../python.md) - Base Python conventions and tooling
- [Testing Guide](../testing.md) - General testing principles and patterns
- [CI Guide](../ci.md) - Continuous integration best practices

## References

[^1]: [Ruff](https://docs.astral.sh/ruff/) - An extremely fast Python linter and code formatter, written in Rust
[^2]: [django-stubs](https://github.com/typeddjango/django-stubs) - Type stubs and mypy plugin for Django
[^4]: [Bandit](https://bandit.readthedocs.io/) - Security linter for Python
[^5]: [pytest-django](https://pytest-django.readthedocs.io/) - A Django plugin for pytest
[^6]: [pytest-cov](https://pytest-cov.readthedocs.io/) - Coverage plugin for pytest
[^7]: [Squawk](https://squawkhq.com/) - Linter for PostgreSQL migrations
[^8]: [pytest-xdist](https://pytest-xdist.readthedocs.io/) - pytest plugin for distributed testing
[^12]: [Celery](https://docs.celeryq.dev/) - Distributed task queue for Python
[^17]: [django-waffle](https://waffle.readthedocs.io/) - Feature flags for Django
[^18]: [django-allauth](https://docs.allauth.org/) - Authentication, registration, and account management with social login support
[^19]: [djangorestframework-simplejwt](https://django-rest-framework-simplejwt.readthedocs.io/) - JSON Web Token authentication for Django REST Framework
[^20]: [django-guardian](https://django-guardian.readthedocs.io/) - Per-object permissions for Django
[^21]: [django-silk](https://github.com/jazzband/django-silk) - Silky smooth profiling for Django
[^22]: [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/) - Observability framework for cloud-native software
[^23]: [django-redis](https://github.com/jazzband/django-redis) - Full-featured Redis cache backend for Django
[^24]: [django-ratelimit](https://django-ratelimit.readthedocs.io/) - Rate limiting for Django views
[^25]: [pybreaker](https://github.com/danielfm/pybreaker) - Python implementation of the Circuit Breaker pattern
[^26]: [Django Channels](https://channels.readthedocs.io/) - Async support for Django, including WebSocket
[^27]: [Daphne](https://github.com/django/daphne) - HTTP, HTTP2, and WebSocket protocol server for ASGI
[^28]: [Uvicorn](https://www.uvicorn.org/) - Lightning-fast ASGI server
[^29]: [django-celery-beat](https://django-celery-beat.readthedocs.io/) - Database-backed periodic task scheduler for Celery
