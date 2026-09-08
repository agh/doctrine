# FastAPI Style Guide

> [Doctrine](../../README.md) > [Frameworks](../README.md) > FastAPI

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119][rfc2119].

[rfc2119]: https://datatracker.ietf.org/doc/html/rfc2119

Extends [Python style guide](../languages/python.md) with FastAPI-specific conventions.

**Target Version**: FastAPI 0.115+ with Python 3.14

## Quick Reference

All Python tooling applies. Additional considerations:

| Task | Tool | Command |
| ---- | ---- | ------- |
| Install | uv | `uv add fastapi uvicorn` |
| Run dev | Uvicorn | `uvicorn myapp.main:app --reload` |
| Test | pytest + TestClient | `pytest` |
| Docs | Built-in | `/docs` (Swagger) or `/redoc` |
| Auth | PyJWT | `uv add pyjwt passlib[bcrypt]` |
| OAuth | Authlib | `uv add authlib httpx` |
| Metrics | prometheus-fastapi-instrumentator | `uv add prometheus-fastapi-instrumentator` |
| Tracing | OpenTelemetry | `uv add opentelemetry-instrumentation-fastapi` |
| Background Jobs | ARQ | `uv add arq` |
| Caching | redis-py | `uv add "redis[hiredis]==8.1.0"` |
| Rate Limiting | slowapi | `uv add slowapi` |
| Circuit Breaker | aiobreaker | `uv add aiobreaker` |
| Feature Flags | Unleash | `uv add UnleashClient` |

## Why FastAPI?

FastAPI[^1] is an async-first, high-performance web framework with automatic
OpenAPI documentation, built-in request validation via Pydantic, and excellent
type hint integration.

**Key advantages**:

- Async/await native support for high concurrency
- Automatic OpenAPI/Swagger documentation
- Pydantic validation with helpful error messages
- Performance comparable to Node.js and Go[^2]

Use FastAPI for APIs requiring high throughput, async I/O, or automatic API
documentation. Choose Flask for simpler synchronous applications or Django for
full-featured web applications with admin panels.

## Project Structure

Projects **SHOULD** organize FastAPI applications by feature:

```text
my_app/
├── src/
│   └── myapp/
│       ├── __init__.py
│       ├── main.py              # Application factory
│       ├── config.py            # Settings
│       ├── database.py          # Database setup
│       ├── dependencies.py      # Shared dependencies
│       ├── api/
│       │   ├── __init__.py
│       │   ├── users.py
│       │   └── items.py
│       ├── models/
│       │   ├── __init__.py
│       │   └── user.py
│       └── schemas/
│           ├── __init__.py
│           └── user.py
├── tests/
│   ├── conftest.py
│   └── test_users.py
├── pyproject.toml
└── .env
```

```python
# src/myapp/main.py
from fastapi import FastAPI
from myapp.api.users import router as users_router
from myapp.api.items import router as items_router
from myapp.config import settings

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json"
    )

    app.include_router(users_router, prefix="/api/users", tags=["users"])
    app.include_router(items_router, prefix="/api/items", tags=["items"])

    return app

app = create_app()
```

**Why**: Organizing by feature keeps related code together. Separating app
creation enables testing with different configurations and multiple app
instances.

## Dependency Injection

Projects **MUST** use FastAPI's dependency injection system[^3]:

```python
# src/myapp/dependencies.py
from collections.abc import Generator
from fastapi import Depends
from sqlalchemy.orm import Session
from myapp.database import SessionLocal

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

```python
# src/myapp/api/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from myapp.dependencies import get_db
from myapp.models.user import User
from myapp.schemas.user import UserResponse

router = APIRouter()

@router.get("/{user_id}", response_model=UserResponse)
async def read_user(user_id: int, db: Session = Depends(get_db)) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

**Why**: Dependency injection decouples route handlers from resource creation,
enables testing with mock dependencies, and manages resource lifecycle
automatically.

## Pydantic Models for Validation

Projects **MUST** use Pydantic models[^4] for request/response validation:

```python
# src/myapp/schemas/user.py
from pydantic import BaseModel, EmailStr, Field, SecretStr, field_validator

from myapp.security.passwords import screen_password

# SP 800-63B-4 §3.1.1.2: 15 characters minimum for password-only authentication.
MIN_PASSWORD_LENGTH = 15
# SP 800-63B-4 §3.1.1.2: at least 64 characters SHOULD be accepted. The cap
# bounds hashing cost; Argon2 and bcrypt both slow down on unbounded input.
MAX_PASSWORD_LENGTH = 128

class UserCreate(BaseModel):
    email: EmailStr
    password: SecretStr = Field(
        ..., min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH
    )
    full_name: str

    @field_validator("password")
    @classmethod
    def reject_compromised(cls, value: SecretStr) -> SecretStr:
        return SecretStr(screen_password(value.get_secret_value()))

class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = None

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str

    model_config = {"from_attributes": True}
```

```python
# src/myapp/api/users.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from myapp.dependencies import get_db
from myapp.models.user import User
from myapp.schemas.user import UserCreate, UserResponse

router = APIRouter()

@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(user: UserCreate, db: Session = Depends(get_db)) -> User:
    db_user = User(**user.model_dump(exclude={"password"}))
    db_user.set_password(user.password.get_secret_value())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
```

**Why**: Pydantic provides automatic validation, serialization, and helpful
error messages. Separate request/response models prevent exposing sensitive
fields and enable API evolution. `SecretStr` keeps the password out of
`repr()`, logs, and tracebacks; raising `ValueError` inside a `field_validator`
produces a 422 through Pydantic's own machinery rather than the application's
exception handlers.

### Password Policy

Endpoints that authenticate a user with a password alone **MUST** apply
NIST SP 800-63B-4[^22] §3.1.1.2:

| Rule | Requirement |
| ---- | ----------- |
| Minimum length | **MUST** be at least 15 characters for password-only authentication; 8 is permitted only when the password is one factor of a multi-factor authentication process |
| Maximum length | **SHOULD** permit at least 64 characters |
| Character set | **SHOULD** accept all printing ASCII, the space character, and Unicode |
| Truncation | **MUST** verify the entire submitted password without truncating it |
| Composition rules | **MUST NOT** require mixed case, digits, or symbols |
| Breach screening | **MUST** compare the whole password against a blocklist of commonly used, expected, or compromised values and **MUST** give the reason for rejection |
| Periodic rotation | **MUST NOT** be required without evidence of compromise |
| Normalisation | **SHOULD** apply Unicode NFC before hashing when Unicode is accepted |

```python
# src/myapp/security/passwords.py
import unicodedata
from pathlib import Path

MIN_PASSWORD_LENGTH = 15
BLOCKLIST_PATH = Path(__file__).with_name("breached_passwords.txt")
_BLOCKLIST = frozenset(
    line.strip().casefold()
    for line in BLOCKLIST_PATH.read_text(encoding="utf-8").splitlines()
    if line.strip()
)

def screen_password(password: str) -> str:
    """Normalise, then reject short or known-compromised values.

    SP 800-63B-4 §3.1.1.2 requires NFC normalisation before hashing, comparison
    of the whole password against a breach blocklist, and a stated reason for
    rejection. Load the corpus at import time, or query a k-anonymity range API
    so that the password itself never leaves the process.
    """
    normalised = unicodedata.normalize("NFC", password)
    if len(normalised) < MIN_PASSWORD_LENGTH:
        raise ValueError(
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
        )
    if normalised.casefold() in _BLOCKLIST:
        raise ValueError("This password appears in a breach corpus. Choose another.")
    return normalised
```

```python
# DON'T: an eight-character minimum with no breach screening
password: str = Field(..., min_length=8)

# DON'T: composition rules push users towards predictable substitutions
password: str = Field(..., pattern=r"^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%]).{8,}$")

# DO: length floor, generous ceiling, breach screening, no composition rules
password: SecretStr = Field(..., min_length=15, max_length=128)
```

```python
# tests/test_password_policy.py
import pytest
from pydantic import ValidationError

from myapp.schemas.user import UserCreate

BASE = {"email": "test@example.com", "full_name": "Test User"}

@pytest.mark.parametrize("password", ["short-one", "password123"])
def test_weak_passwords_are_rejected(password: str) -> None:
    with pytest.raises(ValidationError):
        UserCreate(**BASE, password=password)

def test_sixty_four_character_passphrase_is_accepted() -> None:
    user = UserCreate(**BASE, password="m" * 64)
    assert len(user.password.get_secret_value()) == 64
```

**Why**: Length is the only password property that reliably resists offline
guessing; composition rules and forced rotation measurably reduce entropy by
pushing users towards predictable substitutions, which is why SP 800-63B-4
prohibits both. An eight-character password drawn from a human-chosen
distribution is recoverable in minutes against any hash. Breach screening blocks
the credential-stuffing lists that defeat length requirements outright.

Projects **SHOULD** state which factor the password is: SP 800-63B-4 permits an
eight-character minimum only where the password is used as part of a
multi-factor authentication process. The example above is password-only, so 15
applies.

## Async Database Access

Projects using async FastAPI **MUST** use async database libraries:

```python
# src/myapp/database.py
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from myapp.config import settings

class Base(DeclarativeBase):
    pass

engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
```

```python
# src/myapp/api/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from myapp.database import get_db
from myapp.models.user import User
from myapp.schemas.user import UserResponse

router = APIRouter()

@router.get("/{user_id}", response_model=UserResponse)
async def read_user(user_id: int, db: AsyncSession = Depends(get_db)) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

**Why**: Using async database access preserves FastAPI's async benefits and
prevents blocking the event loop.

### Database Library Recommendations

| Database | Sync | Async |
| -------- | ---- | ----- |
| PostgreSQL | `psycopg2` | `asyncpg` |
| MySQL | `pymysql` | `aiomysql` |
| SQLite | `sqlite3` | `aiosqlite` |

## Configuration with Settings

Projects **MUST** use Pydantic Settings for configuration:

```python
# src/myapp/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "My API"
    VERSION: str = "1.0.0"
    DATABASE_URL: str
    SECRET_KEY: str
    DEBUG: bool = False

    model_config = {"env_file": ".env"}

settings = Settings()
```

## Testing with TestClient

Projects **MUST** test FastAPI applications using `TestClient`, and **MUST**
override the exact dependency callable the route imports:

```python
# tests/conftest.py
import asyncio
from collections.abc import AsyncGenerator, Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from myapp.database import Base, get_db  # the same symbol the routers import
from myapp.main import create_app

@pytest.fixture
def session_factory(tmp_path) -> Iterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{tmp_path / 'test.db'}", poolclass=NullPool
    )

    async def create_schema() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(create_schema())
    yield async_sessionmaker(engine, expire_on_commit=False)
    asyncio.run(engine.dispose())

@pytest.fixture
def app(session_factory) -> Iterator[FastAPI]:
    application = create_app()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    application.dependency_overrides[get_db] = override_get_db
    yield application
    application.dependency_overrides.clear()

@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
```

```python
# tests/test_users.py
from unittest.mock import patch

from fastapi.testclient import TestClient

def test_create_user(client: TestClient) -> None:
    response = client.post("/api/users/", json={
        "email": "test@example.com",
        "password": "example-passphrase-2026",
        "full_name": "Test User"
    })
    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"

def test_create_user_invalid_email(client: TestClient) -> None:
    response = client.post("/api/users/", json={
        "email": "not-an-email",
        "password": "example-passphrase-2026",
        "full_name": "Test User"
    })
    assert response.status_code == 422

def test_application_session_factory_is_never_used(client: TestClient) -> None:
    """Prove the override replaced the configured database, not a lookalike."""
    tripwire = AssertionError("application session factory entered during tests")
    with patch("myapp.database.AsyncSessionLocal", side_effect=tripwire):
        response = client.get("/api/users/1")
    assert response.status_code == 404
```

**Why**: `TestClient` provides synchronous testing of async endpoints without
running a server. `dependency_overrides` is keyed by the function object, so
overriding `myapp.dependencies.get_db` has no effect on a route that depends on
`myapp.database.get_db`[^21]: the request silently falls through to the
application-configured database. Overriding the imported symbol and asserting
that the application session factory is never entered makes that mistake fail
the suite instead of corrupting real data.

Projects **MUST NOT** override a same-named dependency from a different module,
and **MUST NOT** substitute a synchronous `Session` for an `AsyncSession`:

```python
# DON'T: the route imports myapp.database.get_db, so this override is dead code
from myapp.dependencies import get_db          # sync Session dependency
application.dependency_overrides[get_db] = override_get_db

# DO: override the callable the route actually depends on
from myapp.database import get_db              # async AsyncSession dependency
application.dependency_overrides[get_db] = override_get_db
```

## Error Handling

Projects **SHOULD** implement consistent error handling, and **MUST NOT** map
broad built-in exception types to client error statuses:

```python
# src/myapp/errors.py
class DomainError(Exception):
    """A request failure that is safe to describe to the caller."""

    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code

class ItemLocked(DomainError):
    def __init__(self) -> None:
        super().__init__("item_locked", "This item is locked for editing.", 409)
```

```python
# src/myapp/main.py
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from myapp.errors import DomainError

logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    app = FastAPI()

    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.code, "detail": exc.message},
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        correlation_id = getattr(request.state, "correlation_id", "unknown")
        logger.exception("request.failed", extra={"correlation_id": correlation_id})
        return JSONResponse(
            status_code=500,
            content={
                "code": "internal_error",
                "detail": "Internal server error",
                "correlation_id": correlation_id,
            },
        )

    return app
```

```python
# DON'T: every ValueError becomes a 400 and leaks its message to the client
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})

# DO: raise an explicit domain exception where the client is at fault
if item.locked:
    raise ItemLocked()
```

```python
# tests/test_errors.py
from fastapi import FastAPI
from fastapi.testclient import TestClient

def test_domain_error_is_reported_to_the_client(client: TestClient) -> None:
    response = client.get("/api/items/1/edit")
    assert response.status_code == 409
    assert response.json()["code"] == "item_locked"

def test_internal_failure_is_a_500_without_internal_text(app: FastAPI) -> None:
    """A route raising ValueError("shard=3 token=abc") must not leak either."""
    # TestClient re-raises unhandled exceptions by default, which would bypass
    # the handler under test.
    with TestClient(app, raise_server_exceptions=False) as unsafe_client:
        response = unsafe_client.get("/api/items/broken")
    assert response.status_code == 500
    assert "shard=3" not in response.text
    assert "token=abc" not in response.text
```

**Why**: `ValueError` is raised throughout the standard library, Pydantic, and
most third-party packages. A handler registered for it reclassifies internal
invariant failures as client errors, so a genuine server bug returns 400,
escapes 5xx alerting, and returns `str(exc)` — which routinely carries table
names, identifiers, file paths, and configuration values — straight to the
caller. A narrow domain exception carries a stable machine-readable `code` and a
message written for disclosure, while everything unexpected stays a 500 whose
detail lives only in the logs, correlated by request.

Pydantic validation failures need no handler: FastAPI already converts them to
422 responses that describe the offending field without exposing internals.

## Middleware

Projects **SHOULD** use middleware for cross-cutting concerns like logging, timing, and request modification.

### Why Middleware

- **Request/response processing**: Intercept and modify all requests or responses uniformly
- **Cross-cutting concerns**: Logging, authentication, CORS, security headers
- **Performance monitoring**: Add timing headers, track request duration

### CORS Middleware

Projects exposing APIs to browsers **MUST** configure CORS appropriately:

```python
# src/myapp/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def create_app() -> FastAPI:
    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://example.com", "https://app.example.com"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
        max_age=600,  # Cache preflight for 10 minutes
    )

    return app
```

```python
# Development vs Production configuration
# src/myapp/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    CORS_ALLOW_CREDENTIALS: bool = True

    @property
    def cors_config(self) -> dict:
        return {
            "allow_origins": self.CORS_ORIGINS,
            "allow_credentials": self.CORS_ALLOW_CREDENTIALS,
            "allow_methods": ["GET", "POST", "PUT", "DELETE", "PATCH"],
            "allow_headers": ["*"],
        }

# src/myapp/main.py
app.add_middleware(CORSMiddleware, **settings.cors_config)
```

### Custom Middleware with BaseHTTPMiddleware

```python
# src/myapp/middleware.py
import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class TimingMiddleware(BaseHTTPMiddleware):
    """Add request timing to response headers."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        response.headers["X-Process-Time"] = f"{duration:.4f}"
        return response


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Add correlation IDs for request tracing."""

    async def dispatch(self, request: Request, call_next) -> Response:
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        request.state.correlation_id = correlation_id

        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response
```

```python
# src/myapp/main.py
from myapp.middleware import TimingMiddleware, CorrelationIdMiddleware

def create_app() -> FastAPI:
    app = FastAPI()

    # Middleware added in reverse order (last added runs first)
    app.add_middleware(TimingMiddleware)
    app.add_middleware(CorrelationIdMiddleware)

    return app
```

### Pure ASGI Middleware (Recommended for Performance)

For better performance, use pure ASGI middleware instead of `BaseHTTPMiddleware`:

```python
# src/myapp/middleware.py
import time
from typing import Callable
from starlette.types import ASGIApp, Message, Receive, Scope, Send

class PureTimingMiddleware:
    """High-performance timing middleware using pure ASGI."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start = time.perf_counter()

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                duration = time.perf_counter() - start
                headers = list(message.get("headers", []))
                headers.append((b"x-process-time", f"{duration:.4f}".encode()))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)


class SecurityHeadersMiddleware:
    """Add security headers to all responses."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend([
                    (b"x-content-type-options", b"nosniff"),
                    (b"x-frame-options", b"DENY"),
                    (b"x-xss-protection", b"1; mode=block"),
                    (b"referrer-policy", b"strict-origin-when-cross-origin"),
                ])
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)
```

```python
# src/myapp/main.py
from myapp.middleware import PureTimingMiddleware, SecurityHeadersMiddleware

def create_app() -> FastAPI:
    app = FastAPI()

    # Pure ASGI middleware
    app = SecurityHeadersMiddleware(app)
    app = PureTimingMiddleware(app)

    return app
```

### Request Logging Middleware

Request logs **MUST NOT** record raw query strings, request bodies, or
`Authorization` headers:

```python
# src/myapp/middleware.py
import logging
import time
from collections.abc import Mapping

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)

# Only these query parameters are ever written to logs. Everything else is
# redacted by name, so a new parameter cannot leak by being forgotten.
LOGGABLE_QUERY_PARAMS = frozenset({"page", "per_page", "sort", "order"})
REDACTED = "[redacted]"
_CONTROL_CHARS = {codepoint: None for codepoint in [*range(0x20), 0x7F]}
_MAX_LOGGED_VALUE = 64

def scrub(value: str) -> str:
    """Strip control characters and cap length to prevent log injection."""
    return value.translate(_CONTROL_CHARS)[:_MAX_LOGGED_VALUE]

def safe_query(params: Mapping[str, str]) -> dict[str, str]:
    return {
        scrub(key): scrub(value) if key in LOGGABLE_QUERY_PARAMS else REDACTED
        for key, value in params.items()
    }

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log allowlisted request metadata with timing and status."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        correlation_id = getattr(request.state, "correlation_id", "unknown")
        route = scrub(request.url.path)

        logger.info(
            "request.started",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "route": route,
                "query": safe_query(request.query_params),
            },
        )

        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "request.failed",
                extra={
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "route": route,
                    "duration": f"{time.perf_counter() - start:.4f}",
                },
            )
            raise

        logger.info(
            "request.completed",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "route": route,
                "status": response.status_code,
                "duration": f"{time.perf_counter() - start:.4f}",
            },
        )
        return response
```

```python
# DON'T: the whole query string, including tokens and personal data
"query": str(request.query_params),

# DO: allowlisted names only, every other value redacted
"query": safe_query(request.query_params),
```

```python
# tests/test_request_logging.py
import logging

def started_record(caplog) -> logging.LogRecord:
    return next(r for r in caplog.records if r.msg == "request.started")

def test_secret_query_parameters_are_not_logged(caplog, client) -> None:
    with caplog.at_level(logging.INFO, logger="myapp.middleware"):
        client.get("/api/items/?page=2&access_token=s3cret&email=a@example.com")
    assert started_record(caplog).query == {
        "page": "2", "access_token": "[redacted]", "email": "[redacted]"
    }

def test_control_characters_are_stripped(caplog, client) -> None:
    with caplog.at_level(logging.INFO, logger="myapp.middleware"):
        client.get("/api/items/", params={"sort": "name\r\nINJECTED"})
    assert started_record(caplog).query["sort"] == "nameINJECTED"
```

**Why**: OWASP's logging guidance[^23] lists access tokens, session identifiers,
passwords, and sensitive personal data as values that **MUST NOT** be recorded.
Query strings carry all of them in practice — this guide's own WebSocket example
passes a bearer token as `?token=`, and password-reset and invitation links
routinely put single-use secrets there. Application logs are replicated to
aggregators, retained far longer than the tokens they contain, and readable by
staff who are not authorised to see the underlying data, so a raw
`str(request.query_params)` at INFO turns every such request into a durable
credential disclosure. An allowlist fails safe when new parameters appear;
a denylist does not. Stripping control characters stops an attacker-supplied
parameter from forging log lines.

### Middleware Ordering

Middleware executes in the order added (last added = first to run). Projects
**MUST** order middleware correctly:

```python
# src/myapp/main.py
def create_app() -> FastAPI:
    app = FastAPI()

    # 1. CORS (must be first to handle preflight)
    app.add_middleware(CORSMiddleware, **settings.cors_config)

    # 2. Request logging (after CORS to log actual requests)
    app.add_middleware(RequestLoggingMiddleware)

    # 3. Correlation ID (early, so other middleware can use it)
    app.add_middleware(CorrelationIdMiddleware)

    # 4. Timing (late, to measure actual request time)
    app.add_middleware(TimingMiddleware)

    # 5. Security headers (late, applied to all responses)
    app.add_middleware(SecurityHeadersMiddleware)

    return app
```

### Testing Middleware

```python
# tests/test_middleware.py
from fastapi.testclient import TestClient

def test_timing_header_present(client: TestClient) -> None:
    response = client.get("/api/items/")
    assert "X-Process-Time" in response.headers
    assert float(response.headers["X-Process-Time"]) >= 0

def test_correlation_id_generated(client: TestClient) -> None:
    response = client.get("/api/items/")
    assert "X-Correlation-ID" in response.headers
    assert len(response.headers["X-Correlation-ID"]) == 36  # UUID format

def test_correlation_id_preserved(client: TestClient) -> None:
    custom_id = "my-custom-correlation-id"
    response = client.get(
        "/api/items/",
        headers={"X-Correlation-ID": custom_id}
    )
    assert response.headers["X-Correlation-ID"] == custom_id

def test_security_headers_present(client: TestClient) -> None:
    response = client.get("/api/items/")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
```

### Middleware Best Practices

```python
# GOOD: Short-circuit early for health checks
class HealthCheckBypassMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/health":
            return await call_next(request)  # Skip all other middleware logic
        # Full processing for other paths
        return await call_next(request)

# GOOD: Handle exceptions in middleware
class SafeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            logger.exception("Unhandled error in middleware")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )

# BAD: Blocking operations in middleware
class BadMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # This blocks the event loop!
        time.sleep(0.1)  # Use asyncio.sleep() instead
        return await call_next(request)
```

**Why**: Middleware provides a clean separation of cross-cutting concerns from
business logic. Pure ASGI middleware avoids the overhead of `BaseHTTPMiddleware`
for performance-critical applications.

## Background Tasks

Projects **MAY** use FastAPI's background tasks for lightweight async work:

```python
from fastapi import APIRouter, BackgroundTasks
from myapp.services.email import send_welcome_email

router = APIRouter()

@router.post("/users/", status_code=201)
async def create_user(
    user: UserCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> User:
    db_user = User(**user.model_dump())
    db.add(db_user)
    await db.commit()

    background_tasks.add_task(send_welcome_email, db_user.email)
    return db_user
```

For heavier workloads, see the [Background Jobs](#background-jobs) section below.

## Security

Projects **MUST** implement proper authentication and authorization for API endpoints.

### Why Security

Security is foundational to any production API. OAuth2 with JWT tokens provides
stateless authentication that scales horizontally, while object-level
permissions ensure users can only access resources they own or have been
granted access to.

### Authentication with OAuth2 and JWT

Projects **SHOULD** use PyJWT[^5] for JWT token handling (FastAPI's recommended library as of 2025):

```python
# src/myapp/auth.py
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from pydantic import BaseModel

from myapp.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class TokenData(BaseModel):
    sub: str
    exp: datetime
    scopes: list[str] = []

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception

    user = await db.get(User, int(user_id))
    if user is None:
        raise credentials_exception
    return user
```

### OAuth2 with External Providers

Projects integrating with external OAuth providers (Google, GitHub) **SHOULD** use Authlib[^6]:

```python
# src/myapp/oauth.py
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config

config = Config(".env")
oauth = OAuth(config)

oauth.register(
    name="google",
    client_id=config("GOOGLE_CLIENT_ID"),
    client_secret=config("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)
```

### Object-Level Permissions

Projects **MUST** implement object-level permission checks that fail closed:
a resource with no registered policy **MUST** be denied.

```python
# src/myapp/permissions.py
from collections.abc import Callable
from enum import StrEnum
from typing import Any

from fastapi import HTTPException, status

from myapp.models.item import Item
from myapp.models.user import User

class Action(StrEnum):
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"

Policy = Callable[[User, Any, Action], bool]

def item_policy(user: User, item: Item, action: Action) -> bool:
    """Owners hold every right over their items; admins may only read them."""
    if item.owner_id == user.id:
        return True
    return user.is_admin and action is Action.READ

# Every protected resource type needs an entry. Types absent from this table
# are denied, so adding a model without a policy fails loudly rather than
# granting access.
POLICIES: dict[type, Policy] = {Item: item_policy}

def authorise(user: User, obj: object, action: Action) -> None:
    """Raise 403 unless an explicit policy grants `action` on `obj`."""
    policy = POLICIES.get(type(obj))
    if policy is None or not policy(user, obj, action):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorised to perform this action on this resource",
        )
```

```python
# src/myapp/api/items.py
from typing import Annotated

from myapp.permissions import Action, authorise

@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> Item:
    item = await db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    authorise(current_user, item, Action.READ)
    return item
```

```python
# DON'T: probing for an attribute grants access whenever the attribute is
# missing, so any model without owner_id is world-readable
if hasattr(obj, "owner_id") and obj.owner_id != user.id:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

# DO: look up an explicit policy and deny when none exists
authorise(user, obj, Action.READ)
```

```python
# tests/test_permissions.py
import pytest
from fastapi import HTTPException

from myapp.permissions import Action, authorise
from myapp.models.item import Item
from myapp.models.user import User

def test_owner_may_read_own_item() -> None:
    authorise(User(id=1), Item(id=1, owner_id=1), Action.READ)

@pytest.mark.parametrize("action", list(Action))
def test_cross_tenant_access_is_denied(action: Action) -> None:
    with pytest.raises(HTTPException) as excinfo:
        authorise(User(id=1), Item(id=2, owner_id=2), action)
    assert excinfo.value.status_code == 403

def test_resource_without_a_policy_is_denied() -> None:
    with pytest.raises(HTTPException):
        authorise(User(id=1), object(), Action.READ)

def test_admin_may_read_but_not_delete_another_users_item() -> None:
    admin = User(id=9, is_admin=True)
    authorise(admin, Item(id=2, owner_id=2), Action.READ)
    with pytest.raises(HTTPException):
        authorise(admin, Item(id=2, owner_id=2), Action.DELETE)
```

**Why**: Object-level permissions prevent horizontal privilege escalation where
authenticated users access other users' data. Broken object level authorization
is the first entry in the OWASP API Security Top 10[^24], which requires every
endpoint that receives an object identifier to validate the caller's permission
for that specific object.

Attribute probing inverts the safe default. `hasattr(obj, "owner_id")` returns
`False` for any resource that models ownership differently — through a
`team_id`, a join table, or a tenant column — and the check then falls through
to an unconditional allow. The failure is silent: no model is flagged, no test
fails, and the endpoint returns another tenant's record. A policy table keyed by
resource type inverts that: an unregistered type is denied, and a typed `Action`
enum means a mistyped or unknown action cannot match a permitted branch.

## WebSocket

Projects requiring real-time features **SHOULD** use FastAPI's native WebSocket support[^7].

### Why WebSockets

WebSockets enable bidirectional communication for real-time features like chat,
notifications, and live updates without polling overhead.

### Connection Management

```python
# src/myapp/websocket.py
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str) -> None:
        self.active_connections.pop(client_id, None)

    async def send_personal(self, message: str, client_id: str) -> None:
        if websocket := self.active_connections.get(client_id):
            await websocket.send_text(message)

    async def broadcast(self, message: str) -> None:
        for websocket in self.active_connections.values():
            await websocket.send_text(message)

manager = ConnectionManager()
```

### WebSocket with Authentication

Projects **MUST** authenticate WebSocket connections:

```python
# src/myapp/api/ws.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from myapp.auth import decode_token
from myapp.websocket import manager

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
) -> None:
    try:
        user = await decode_token(token)
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket, str(user.id))
    try:
        while True:
            data = await websocket.receive_text()
            # Process message with validation
            await manager.broadcast(f"User {user.id}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(str(user.id))
```

### Scaling WebSockets

For multi-instance deployments, projects **SHOULD** use Redis Pub/Sub or
broadcaster[^8]. Redis Pub/Sub uses `redis.asyncio` from redis-py 8.1.0:

```python
# src/myapp/websocket_redis.py
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI

from myapp.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    pubsub = client.pubsub()
    await pubsub.subscribe("broadcasts")
    app.state.redis = client
    app.state.pubsub = pubsub
    try:
        yield
    finally:
        await pubsub.unsubscribe("broadcasts")
        await pubsub.aclose()
        await client.aclose()

async def publish_message(client: redis.Redis, channel: str, message: str) -> None:
    await client.publish(channel, message)
```

Projects **MUST NOT** depend on the standalone `aioredis` package:

```python
# DON'T: aioredis was merged into redis-py at 4.2.0rc1 and is abandoned. Its
# last release (2.0.1) imports distutils, which was removed in Python 3.12, so
# `import aioredis` raises ModuleNotFoundError on any supported interpreter.
import aioredis
app.state.redis = await aioredis.from_url("redis://localhost")
await app.state.redis.close()

# DO: use the maintained async client shipped inside redis-py
import redis.asyncio as redis
app.state.redis = redis.from_url(settings.REDIS_URL)
await app.state.redis.aclose()
```

**Why**: In-memory connection managers only work within a single process. Redis
Pub/Sub enables message distribution across multiple server instances.
`redis.from_url()` in the async client is a plain constructor rather than a
coroutine, and redis-py documents `aclose()` as the explicit disconnect for the
async client; `close()` survives only as a backwards-compatibility alias[^25].

## Performance and Observability

Projects **MUST** implement observability for production deployments.

### Why Observability

Observability through metrics, traces, and logs enables proactive
identification of performance issues, capacity planning, and faster incident
resolution.

### Prometheus Metrics

Projects **SHOULD** use prometheus-fastapi-instrumentator[^9]:

```python
# src/myapp/main.py
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

def create_app() -> FastAPI:
    app = FastAPI()

    # Enable Prometheus metrics
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")

    return app
```

Default metrics include:

- `http_requests_total` - Counter with handler, status, method labels
- `http_request_duration_seconds` - Histogram of request latencies
- `http_request_size_bytes` / `http_response_size_bytes` - Request/response sizes

### OpenTelemetry Tracing

Projects **SHOULD** use OpenTelemetry[^10] for distributed tracing:

```python
# src/myapp/telemetry.py
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

def setup_telemetry(app: FastAPI) -> None:
    provider = TracerProvider()
    processor = BatchSpanProcessor(OTLPSpanExporter())
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app)
```

```toml
# pyproject.toml dependencies
[project.optional-dependencies]
observability = [
    "opentelemetry-api>=1.20.0",
    "opentelemetry-sdk>=1.20.0",
    "opentelemetry-exporter-otlp>=1.20.0",
    "opentelemetry-instrumentation-fastapi>=0.41b0",
    "prometheus-fastapi-instrumentator>=7.0.0",
]
```

### Profiling with py-spy

For CPU profiling in production, use py-spy[^11]:

```bash
# Profile running process
py-spy top --pid <PID>

# Generate flame graph
py-spy record -o profile.svg --pid <PID>
```

**Why**: py-spy is a sampling profiler that attaches to running Python processes
without code changes or performance overhead, making it safe for production
debugging.

## Background Jobs

Projects requiring heavy or distributed task processing **MUST** use a dedicated task queue.

### Why Task Queues

FastAPI's built-in `BackgroundTasks` runs in the same process as the web
server, lacks status tracking, and loses tasks on server restart. Dedicated
task queues provide persistence, retries, monitoring, and horizontal scaling.

### Choosing a Task Queue

| Use Case | Recommendation |
| -------- | -------------- |
| Async-native, I/O-bound tasks | ARQ[^12] |
| CPU-bound or mixed workloads | Celery[^13] |
| Simple async queues | SAQ[^14] |

### ARQ (Async Redis Queue)

Projects with async workloads **SHOULD** use ARQ:

```python
# src/myapp/tasks.py
from arq import create_pool
from arq.connections import RedisSettings

async def send_email(ctx: dict, to: str, subject: str, body: str) -> None:
    """Background task to send email."""
    # ctx contains the Redis connection pool
    await email_service.send(to=to, subject=subject, body=body)

class WorkerSettings:
    functions = [send_email]
    redis_settings = RedisSettings(host="localhost", port=6379)
    max_jobs = 10
    job_timeout = 300  # 5 minutes
```

```python
# src/myapp/api/users.py
from arq import ArqRedis

@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
    arq: ArqRedis = Depends(get_arq_pool),
) -> User:
    db_user = User(**user.model_dump(exclude={"password"}))
    db.add(db_user)
    await db.commit()

    # Queue background job with retry support
    await arq.enqueue_job(
        "send_email",
        to=db_user.email,
        subject="Welcome!",
        body="Thank you for signing up.",
        _defer_by=timedelta(seconds=5),  # Delay execution
    )
    return db_user
```

Run the worker:

```bash
arq myapp.tasks.WorkerSettings
```

### Celery for Heavy Workloads

For CPU-bound tasks or complex workflows:

```python
# src/myapp/celery_app.py
from celery import Celery

celery = Celery(
    "myapp",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    task_time_limit=600,
)

@celery.task(bind=True, max_retries=3)
def process_report(self, report_id: int) -> dict:
    try:
        # CPU-intensive processing
        return {"status": "completed", "report_id": report_id}
    except Exception as exc:
        self.retry(exc=exc, countdown=60)
```

## Caching

Projects **SHOULD** implement caching for frequently accessed, expensive operations.

### Why Caching

Caching reduces database load, decreases response latency, and improves API
throughput. Redis provides distributed caching that works across multiple
application instances.

### Redis Cache Service

Projects **SHOULD** cache through a typed service built on `redis.asyncio`
(redis-py 8.1.0)[^15]:

```python
# src/myapp/cache.py
import json
from datetime import timedelta
from typing import Any

import redis.asyncio as redis
from fastapi import Request

NAMESPACE = "myapp:v1"

class Cache:
    """Namespaced JSON cache with explicit keys, TTLs, and invalidation."""

    def __init__(self, client: redis.Redis, namespace: str = NAMESPACE) -> None:
        self._client = client
        self._namespace = namespace

    def key(self, *parts: object) -> str:
        return ":".join([self._namespace, *(str(part) for part in parts)])

    async def get_json(self, key: str) -> Any | None:
        raw = await self._client.get(key)
        return None if raw is None else json.loads(raw)

    async def set_json(self, key: str, value: Any, ttl: timedelta) -> None:
        await self._client.set(key, json.dumps(value), ex=ttl)

    async def delete(self, *keys: str) -> None:
        if keys:
            await self._client.unlink(*keys)

    async def collection_version(self, collection: str) -> int:
        raw = await self._client.get(self.key(collection, "version"))
        return int(raw) if raw is not None else 0

    async def bump_collection(self, collection: str) -> int:
        """Invalidate every cached page of a collection in one round trip."""
        return await self._client.incr(self.key(collection, "version"))

def get_cache(request: Request) -> Cache:
    return request.app.state.cache
```

```python
# src/myapp/main.py
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI

from myapp.cache import Cache
from myapp.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    app.state.cache = Cache(client)
    try:
        yield
    finally:
        await client.aclose()

app = FastAPI(lifespan=lifespan)
```

```python
# src/myapp/api/items.py
from datetime import timedelta

from myapp.cache import Cache, get_cache

CACHE_TTL = timedelta(minutes=5)

@router.get("/", response_model=list[ItemResponse])
async def list_items(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    cache: Cache = Depends(get_cache),
) -> list[ItemResponse]:
    version = await cache.collection_version("items")
    key = cache.key("items", version, skip, limit)
    if (cached := await cache.get_json(key)) is not None:
        return [ItemResponse.model_validate(row) for row in cached]

    result = await db.execute(select(Item).offset(skip).limit(limit))
    items = [ItemResponse.model_validate(row) for row in result.scalars()]
    await cache.set_json(key, [item.model_dump(mode="json") for item in items], CACHE_TTL)
    return items
```

Projects **MUST NOT** build cache keys from injected infrastructure, and
**MUST NOT** install `fastapi-cache2` alongside redis-py 8:

```python
# DON'T: fastapi-cache2 0.2.2 imports Starlette's private _TemplateResponse, so
# `import fastapi_cache` raises "jinja2 must be installed to use
# Jinja2Templates" on the documented dependency set, and its [redis] extra pins
# redis<5.0.0, which cannot resolve against the redis 8.1.0 used elsewhere here.
from fastapi_cache.decorator import cache

@cache(expire=300)                      # default key builder hashes every argument,
async def list_items(db: AsyncSession = Depends(get_db)): ...  # including `db`

# DO: derive the key from the query inputs alone
key = cache.key("items", version, skip, limit)
```

### Cache Invalidation

Projects **MUST** invalidate cache when underlying data changes:

```python
# src/myapp/api/items.py
@router.post("/", response_model=ItemResponse, status_code=201)
async def create_item(
    item: ItemCreate,
    db: AsyncSession = Depends(get_db),
    cache: Cache = Depends(get_cache),
) -> Item:
    db_item = Item(**item.model_dump())
    db.add(db_item)
    await db.commit()
    await cache.bump_collection("items")
    return db_item

@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: int,
    item: ItemUpdate,
    db: AsyncSession = Depends(get_db),
    cache: Cache = Depends(get_cache),
) -> Item:
    db_item = await db.get(Item, item_id)
    for key, value in item.model_dump(exclude_unset=True).items():
        setattr(db_item, key, value)
    await db.commit()
    await cache.delete(cache.key("item", item_id))
    await cache.bump_collection("items")
    return db_item
```

```python
# tests/test_cache.py
from datetime import timedelta

import pytest
from fakeredis import aioredis as fakeredis

from myapp.cache import Cache

@pytest.mark.asyncio
async def test_invalidation_forces_a_reload() -> None:
    client = fakeredis.FakeRedis(decode_responses=True)
    cache = Cache(client)
    key = cache.key("items", await cache.collection_version("items"), 0, 100)
    await cache.set_json(key, [{"id": 1}], timedelta(minutes=5))

    await cache.bump_collection("items")
    fresh = cache.key("items", await cache.collection_version("items"), 0, 100)
    assert await cache.get_json(fresh) is None
    await client.aclose()
```

**Why**: Stale cache data causes data consistency issues. Invalidate-on-write
ensures cache freshness while maintaining performance benefits for reads.

Keys are built by hand for two reasons. A decorator's automatic key builder
hashes the endpoint's arguments, which include the `AsyncSession` injected for
that request; a fresh session object per request means a fresh key, so the cache
never hits. Writing the key from `skip` and `limit` alone keeps it stable across
requests and makes it reproducible from the write path. The version counter then
invalidates every page of a collection with a single `INCR`, avoiding a `SCAN`
over the keyspace and guaranteeing that reads and writes agree on the namespace.

## Rate Limiting

Projects **MUST** implement rate limiting for public APIs.

### Why Rate Limiting

Rate limiting protects APIs from abuse, ensures fair resource allocation among
users, and prevents cascading failures from traffic spikes.

### slowapi

Projects **SHOULD** use slowapi[^16] for rate limiting:

```python
# src/myapp/limiter.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
    storage_uri="redis://localhost:6379",
)
```

```python
# src/myapp/main.py
from fastapi import FastAPI
from myapp.limiter import limiter, RateLimitExceeded, _rate_limit_exceeded_handler

def create_app() -> FastAPI:
    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
    return app
```

```python
# src/myapp/api/items.py
from myapp.limiter import limiter

@router.get("/")
@limiter.limit("10/minute")
async def list_items(request: Request) -> list[Item]:
    # Rate limited to 10 requests per minute per IP
    ...
```

### User-Based Rate Limits

Projects **SHOULD** implement different limits per user tier. SlowAPI calls a
dynamic limit provider with **no arguments**, or with the key string when the
provider declares a parameter named `key`; it never passes the `Request`[^26]:

```python
# src/myapp/limiter.py
from dataclasses import dataclass

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

TIER_LIMITS = {"free": "100/hour", "pro": "1000/hour", "enterprise": "10000/hour"}
ANONYMOUS_LIMIT = "50/hour"

@dataclass(frozen=True)
class Identity:
    user_id: str
    tier: str

def get_rate_limit_key(request: Request) -> str:
    """Encode the caller's identity and tier into the limiter key."""
    identity: Identity | None = getattr(request.state, "identity", None)
    if identity is None:
        return f"anon:{get_remote_address(request)}"
    return f"user:{identity.user_id}:{identity.tier}"

def dynamic_limit(key: str) -> str:
    """Return the limit for the identity that get_rate_limit_key produced."""
    scope, _, remainder = key.partition(":")
    if scope != "user":
        return ANONYMOUS_LIMIT
    _, _, tier = remainder.partition(":")
    return TIER_LIMITS.get(tier, TIER_LIMITS["free"])

limiter = Limiter(
    key_func=get_rate_limit_key,          # wire the identity-aware key function
    default_limits=[ANONYMOUS_LIMIT],
    storage_uri="redis://localhost:6379",
)
```

```python
# src/myapp/middleware.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from myapp.auth import decode_token
from myapp.limiter import Identity

class IdentityMiddleware(BaseHTTPMiddleware):
    """Resolve the caller before any rate limit is evaluated."""

    async def dispatch(self, request: Request, call_next) -> Response:
        header = request.headers.get("Authorization", "")
        token = header.removeprefix("Bearer ") if header.startswith("Bearer ") else ""
        claims = await decode_token(token) if token else None
        request.state.identity = (
            Identity(user_id=claims["sub"], tier=claims["tier"]) if claims else None
        )
        return await call_next(request)
```

```python
# src/myapp/main.py
# Middleware runs in reverse order of registration, so identity resolution
# must be added after SlowAPIMiddleware to run before it.
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(IdentityMiddleware)
```

```python
# src/myapp/api/items.py
@router.get("/")
@limiter.limit(dynamic_limit)
async def list_items(request: Request) -> list[Item]:
    ...
```

```python
# DON'T: SlowAPI inspects the signature and finds no `key` parameter, so it
# calls dynamic_limit() with no arguments and every request becomes a 500:
# TypeError: dynamic_limit() missing 1 required positional argument: 'request'
def dynamic_limit(request: Request) -> str: ...

# DO: accept the key SlowAPI supplies from the limiter's key_func
def dynamic_limit(key: str) -> str: ...
```

```python
# tests/test_rate_limits.py
from types import SimpleNamespace

from myapp.limiter import (
    ANONYMOUS_LIMIT,
    TIER_LIMITS,
    Identity,
    dynamic_limit,
    get_rate_limit_key,
)

def request_from(identity: Identity | None) -> SimpleNamespace:
    return SimpleNamespace(
        state=SimpleNamespace(identity=identity),
        client=SimpleNamespace(host="203.0.113.7"),
    )

def test_anonymous_callers_are_keyed_by_ip() -> None:
    key = get_rate_limit_key(request_from(None))
    assert key == "anon:203.0.113.7"
    assert dynamic_limit(key) == ANONYMOUS_LIMIT

def test_two_users_behind_one_ip_get_separate_buckets() -> None:
    """A free customer must not exhaust a paid neighbour's budget."""
    alice = get_rate_limit_key(request_from(Identity("alice", "free")))
    bob = get_rate_limit_key(request_from(Identity("bob", "pro")))
    assert alice != bob
    assert dynamic_limit(alice) == TIER_LIMITS["free"]
    assert dynamic_limit(bob) == TIER_LIMITS["pro"]
```

**Why**: User-based rate limiting ensures fair API access based on subscription
tiers while protecting against anonymous abuse. Wiring `get_rate_limit_key` into
`Limiter(key_func=...)` is what makes the tier reachable: SlowAPI derives the
counter bucket and the dynamic limit from the same key, so two customers behind
one NAT gateway no longer share a budget, and a paid tier cannot be exhausted by
an anonymous neighbour.

Resolve the identity in middleware rather than an endpoint dependency.
`SlowAPIMiddleware` evaluates the default limits before routing, so a dependency
that sets `request.state.identity` has not yet run and every caller is counted
as anonymous. Decorated routes do observe a dependency's identity, because
`@limiter.limit` wraps the endpoint itself — which means the two paths key the
same caller differently unless the identity is established in middleware.

## Circuit Breakers

Projects calling external services **SHOULD** implement circuit breakers.

### Why Circuit Breakers

Circuit breakers prevent cascading failures when external services become
unavailable. They fail fast, reduce load on struggling services, and enable
graceful degradation.

### aiobreaker

Projects **SHOULD** use aiobreaker[^17] for async circuit breakers.
`timeout_duration` **MUST** be a `datetime.timedelta`, and listeners receive
state objects whose enum is exposed as `.state`[^27]:

```python
# src/myapp/breakers.py
import logging
from datetime import timedelta

from aiobreaker import CircuitBreaker, CircuitBreakerListener
from aiobreaker.state import CircuitBreakerBaseState

logger = logging.getLogger(__name__)

class LoggingListener(CircuitBreakerListener):
    def state_change(
        self,
        breaker: CircuitBreaker,
        old: CircuitBreakerBaseState | None,
        new: CircuitBreakerBaseState,
    ) -> None:
        # aiobreaker passes state objects, not enum members; the enum is .state
        previous = old.state.name if old is not None else "NONE"
        logger.warning(
            "circuit_breaker_state_change breaker=%s from=%s to=%s",
            breaker.name,
            previous,
            new.state.name,
        )

# Configure circuit breaker
payment_breaker = CircuitBreaker(
    fail_max=5,                             # Open after 5 failures
    timeout_duration=timedelta(seconds=30),  # Try again after 30 seconds
    listeners=[LoggingListener()],
    name="payment_service",
)
```

```python
# DON'T: timeout_duration is added to a datetime, so an int raises
# TypeError: unsupported operand type(s) for +: 'datetime.datetime' and 'int'
timeout_duration=30

# DON'T: state objects have no .name, so the listener raises AttributeError
# from inside the transition and the breaker silently stays CLOSED for ever
f"{old_state.name} -> {new_state.name}"

# DO: pass a timedelta and read the enum through .state
timeout_duration=timedelta(seconds=30)
f"{old.state.name} -> {new.state.name}"
```

```python
# src/myapp/services/payment.py
from myapp.breakers import payment_breaker
from aiobreaker import CircuitBreakerError
import httpx

@payment_breaker
async def process_payment(amount: float, token: str) -> dict:
    """Call external payment service with circuit breaker protection."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.payment.example/charge",
            json={"amount": amount, "token": token},
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()
```

```python
# src/myapp/api/payments.py
from aiobreaker import CircuitBreakerError
from myapp.services.payment import process_payment

@router.post("/charge")
async def charge_payment(payment: PaymentRequest) -> PaymentResponse:
    try:
        result = await process_payment(payment.amount, payment.token)
        return PaymentResponse(**result)
    except CircuitBreakerError:
        raise HTTPException(
            status_code=503,
            detail="Payment service temporarily unavailable. Please try again later.",
        )
```

### Circuit Breaker States

| State | Behavior |
| ----- | -------- |
| Closed | Normal operation, requests pass through |
| Open | Requests fail immediately without calling service |
| Half-Open | Limited requests allowed to test recovery |

```python
# tests/test_breakers.py
import asyncio
from datetime import timedelta

import pytest
from aiobreaker import CircuitBreaker, CircuitBreakerError
from aiobreaker.state import CircuitBreakerState

from myapp.breakers import LoggingListener

@pytest.mark.asyncio
async def test_breaker_opens_times_out_and_closes_again() -> None:
    breaker = CircuitBreaker(
        fail_max=5,
        timeout_duration=timedelta(seconds=1),
        listeners=[LoggingListener()],
        name="test",
    )
    failing = True

    @breaker
    async def call_upstream() -> str:
        if failing:
            raise RuntimeError("upstream down")
        return "ok"

    for _ in range(5):
        with pytest.raises((RuntimeError, CircuitBreakerError)):
            await call_upstream()
    assert breaker.current_state is CircuitBreakerState.OPEN

    with pytest.raises(CircuitBreakerError):
        await call_upstream()          # fails fast without calling upstream

    await asyncio.sleep(1.1)           # breaker moves to HALF_OPEN
    failing = False
    assert await call_upstream() == "ok"
    assert breaker.current_state is CircuitBreakerState.CLOSED
```

The failure that trips the breaker surfaces as `CircuitBreakerError` rather than
the underlying exception, so callers **MUST** handle both.

**Why**: Circuit breakers prevent thread pool exhaustion from slow failing calls
and give external services time to recover without being overwhelmed by retry
storms. Both defects above are silent: an integer `timeout_duration` only fails
when the breaker first tries to open, and a listener that raises during a
transition aborts that transition, so the breaker reports CLOSED indefinitely
and keeps hammering the failing dependency. Exercising the full
CLOSED → OPEN → HALF\_OPEN → CLOSED cycle with the real listener attached is the
only way to catch either.

## Feature Flags

Projects **MAY** use feature flags for controlled rollouts and A/B testing.

### Why Feature Flags

Feature flags enable gradual rollouts, instant rollbacks, A/B testing, and
environment-specific configurations without code deployments.

### Provider Options

| Provider | Type | Best For |
| -------- | ---- | -------- |
| Unleash[^18] | Open source (self-hosted/cloud) | Teams needing full control |
| LaunchDarkly[^19] | SaaS | Enterprise with complex targeting |
| Flagsmith[^20] | Open source (self-hosted/cloud) | Flexible deployment options |

### Unleash Integration

```python
# src/myapp/features.py
from UnleashClient import UnleashClient

unleash = UnleashClient(
    url="http://localhost:4242/api",
    app_name="myapp",
    custom_headers={"Authorization": "default:development.unleash-insecure-api-token"},
)
unleash.initialize_client()
```

```python
# src/myapp/api/items.py
from myapp.features import unleash

@router.get("/")
async def list_items(
    current_user: User = Depends(get_current_user),
) -> list[Item]:
    context = {"userId": str(current_user.id), "properties": {"tier": current_user.tier}}

    if unleash.is_enabled("new-recommendation-algorithm", context):
        return await get_items_with_recommendations()
    return await get_items_legacy()
```

### Flagsmith Integration

```python
# src/myapp/features.py
from flagsmith import Flagsmith

flagsmith = Flagsmith(
    environment_key="your-environment-key",
)

def is_feature_enabled(feature_name: str, user_id: str | None = None) -> bool:
    if user_id:
        flags = flagsmith.get_identity_flags(user_id)
    else:
        flags = flagsmith.get_environment_flags()
    return flags.is_feature_enabled(feature_name)
```

### Dependency Injection Pattern

Projects **SHOULD** use dependency injection for feature flag checks:

```python
# src/myapp/dependencies.py
from fastapi import Depends
from myapp.features import unleash

def require_feature(feature_name: str):
    """Dependency that checks if feature is enabled."""
    async def check_feature(
        current_user: User = Depends(get_current_user),
    ) -> bool:
        context = {"userId": str(current_user.id)}
        if not unleash.is_enabled(feature_name, context):
            raise HTTPException(
                status_code=404,
                detail="Feature not available",
            )
        return True
    return check_feature

@router.get("/beta-feature", dependencies=[Depends(require_feature("beta-api"))])
async def beta_endpoint() -> dict:
    return {"message": "You have access to the beta feature!"}
```

**Why**: Feature flags separate deployment from release, reducing risk and
enabling experimentation without code changes.

## See Also

- [Python Style Guide](../languages/python.md) - Language-level Python conventions
- [Flask Style Guide](flask.md) - Lightweight sync framework
- [Django Style Guide](django.md) - Full-featured web framework

## References

[^1]: [FastAPI](https://fastapi.tiangolo.com/) - Modern, fast web framework for building APIs
[^2]: [FastAPI Benchmarks](https://fastapi.tiangolo.com/#performance) - Performance comparisons
[^3]: [FastAPI Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/) - Dependency injection system
[^4]: [Pydantic](https://docs.pydantic.dev/) - Data validation using Python type hints
[^5]: [PyJWT](https://pyjwt.readthedocs.io/) - JSON Web Token implementation in Python (FastAPI recommended as of 2025)
[^6]: [Authlib](https://docs.authlib.org/) - Ultimate Python library for OAuth and OpenID Connect
[^7]: [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/) - Native WebSocket support
[^8]: [broadcaster](https://github.com/encode/broadcaster) - Scalable WebSocket broadcasting with Redis/Postgres backends
[^9]: [prometheus-fastapi-instrumentator](https://github.com/trallnag/prometheus-fastapi-instrumentator) - Prometheus metrics for FastAPI (v7.1.0+)
[^10]: [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/) - Vendor-neutral observability framework
[^11]: [py-spy](https://github.com/benfred/py-spy) - Sampling profiler for Python programs
[^12]: [ARQ](https://arq-docs.helpmanual.io/) - Async Redis Queue for Python
[^13]: [Celery](https://docs.celeryq.dev/) - Distributed task queue
[^14]: [SAQ](https://github.com/tobymao/saq) - Simple Async Queue with web UI
[^15]: [redis-py](https://redis.readthedocs.io/en/stable/examples/asyncio_examples.html) - Async Redis client shipped with redis-py (v8.1.0)
[^16]: [slowapi](https://github.com/laurentS/slowapi) - Rate limiting for FastAPI based on flask-limiter
[^17]: [aiobreaker](https://github.com/arlyon/aiobreaker) - Async circuit breaker implementation
[^18]: [Unleash](https://www.getunleash.io/) - Open source feature flag platform
[^19]: [LaunchDarkly](https://launchdarkly.com/) - Enterprise feature management platform
[^20]: [Flagsmith](https://www.flagsmith.com/) - Open source feature flag and remote config service
[^21]: [FastAPI Testing Dependencies](https://fastapi.tiangolo.com/advanced/testing-dependencies/) - `dependency_overrides` is keyed by the original function object
[^22]: [NIST SP 800-63B-4](https://pages.nist.gov/800-63-4/sp800-63b.html) - Digital Identity Guidelines: Authentication and Authenticator Management ([change log](https://pages.nist.gov/800-63-4/sp800-63b/changelog/))
[^23]: [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html) - Data to exclude from application logs
[^24]: [OWASP API1:2023](https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/) - Broken Object Level Authorization
[^25]: [redis-py asyncio examples](https://redis.readthedocs.io/en/stable/examples/asyncio_examples.html) - `Redis.aclose()` is the explicit async disconnect
[^26]: [SlowAPI LimitGroup](https://github.com/laurentS/slowapi/blob/master/slowapi/wrappers.py) - Dynamic limit providers are called with no arguments, or with the key when the parameter is named `key`
[^27]: [aiobreaker state module](https://github.com/arlyon/aiobreaker/blob/master/aiobreaker/state.py) - Listeners receive state objects whose enum is exposed as `.state`
