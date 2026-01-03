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
| Caching | fastapi-cache2 | `uv add fastapi-cache2[redis]` |
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
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str

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
    db_user.set_password(user.password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
```

**Why**: Pydantic provides automatic validation, serialization, and helpful
error messages. Separate request/response models prevent exposing sensitive
fields and enable API evolution.

## Async Database Access

Projects using async FastAPI **MUST** use async database libraries:

```python
# src/myapp/database.py
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from myapp.config import settings

engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
```

```python
# src/myapp/api/users.py
from fastapi import APIRouter, Depends
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

Projects **MUST** test FastAPI applications using `TestClient`:

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from myapp.main import create_app
from myapp.database import Base
from myapp.dependencies import get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine)

@pytest.fixture
def app():
    Base.metadata.create_all(bind=engine)
    application = create_app()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    application.dependency_overrides[get_db] = override_get_db
    yield application
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(app):
    return TestClient(app)
```

```python
# tests/test_users.py
from fastapi.testclient import TestClient

def test_create_user(client: TestClient) -> None:
    response = client.post("/api/users/", json={
        "email": "test@example.com",
        "password": "password123",
        "full_name": "Test User"
    })
    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"

def test_create_user_invalid_email(client: TestClient) -> None:
    response = client.post("/api/users/", json={
        "email": "not-an-email",
        "password": "password123",
        "full_name": "Test User"
    })
    assert response.status_code == 422
```

**Why**: `TestClient` provides synchronous testing of async endpoints without
running a server. Dependency overrides enable injecting test database sessions
and mocked dependencies.

## Error Handling

Projects **SHOULD** implement consistent error handling:

```python
# src/myapp/main.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

def create_app() -> FastAPI:
    app = FastAPI()

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc)}
        )

    return app
```

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

```python
# src/myapp/middleware.py
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests with timing and status."""

    async def dispatch(self, request: Request, call_next):
        import time
        start = time.perf_counter()

        # Get correlation ID if set
        correlation_id = getattr(request.state, "correlation_id", "unknown")

        logger.info(
            "Request started",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "query": str(request.query_params),
            }
        )

        response = await call_next(request)
        duration = time.perf_counter() - start

        logger.info(
            "Request completed",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration": f"{duration:.4f}",
            }
        )

        return response
```

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

Projects **MUST** implement object-level permission checks:

```python
# src/myapp/permissions.py
from fastapi import HTTPException, status

async def check_object_permission(user: User, obj: Any, action: str = "read") -> None:
    """Verify user has permission to perform action on object."""
    if hasattr(obj, "owner_id") and obj.owner_id != user.id:
        if not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not authorized to {action} this resource",
            )
```

```python
# src/myapp/api/items.py
from typing import Annotated

@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> Item:
    item = await db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    await check_object_permission(current_user, item, "read")
    return item
```

**Why**: Object-level permissions prevent horizontal privilege escalation where
authenticated users access other users' data. This is one of the OWASP Top 10
API security risks.

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

For multi-instance deployments, projects **SHOULD** use Redis Pub/Sub or broadcaster[^8]:

```python
# src/myapp/websocket_redis.py
import aioredis
from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = await aioredis.from_url("redis://localhost")
    app.state.pubsub = app.state.redis.pubsub()
    await app.state.pubsub.subscribe("broadcasts")
    yield
    await app.state.redis.close()

async def publish_message(redis, channel: str, message: str) -> None:
    await redis.publish(channel, message)
```

**Why**: In-memory connection managers only work within a single process. Redis
Pub/Sub enables message distribution across multiple server instances.

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

### fastapi-cache2

Projects **SHOULD** use fastapi-cache2[^15] with Redis backend:

```python
# src/myapp/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis

@asynccontextmanager
async def lifespan(app: FastAPI):
    redis = aioredis.from_url(
        "redis://localhost",
        encoding="utf-8",
        decode_responses=False,  # Required for fastapi-cache2
    )
    FastAPICache.init(RedisBackend(redis), prefix="myapp-cache")
    yield
    await redis.close()

app = FastAPI(lifespan=lifespan)
```

```python
# src/myapp/api/items.py
from fastapi_cache.decorator import cache

@router.get("/", response_model=list[ItemResponse])
@cache(expire=300)  # Cache for 5 minutes
async def list_items(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> list[Item]:
    result = await db.execute(select(Item).offset(skip).limit(limit))
    return result.scalars().all()
```

### Cache Invalidation

Projects **MUST** invalidate cache when underlying data changes:

```python
# src/myapp/cache.py
from fastapi_cache import FastAPICache

async def invalidate_item_cache(item_id: int) -> None:
    """Invalidate specific item cache."""
    await FastAPICache.clear(namespace=f"item:{item_id}")

async def invalidate_list_cache() -> None:
    """Invalidate list cache after create/update/delete."""
    await FastAPICache.clear(namespace="items")
```

```python
# src/myapp/api/items.py
@router.post("/", response_model=ItemResponse, status_code=201)
async def create_item(
    item: ItemCreate,
    db: AsyncSession = Depends(get_db),
) -> Item:
    db_item = Item(**item.model_dump())
    db.add(db_item)
    await db.commit()
    await invalidate_list_cache()  # Clear list cache
    return db_item

@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: int,
    item: ItemUpdate,
    db: AsyncSession = Depends(get_db),
) -> Item:
    db_item = await db.get(Item, item_id)
    for key, value in item.model_dump(exclude_unset=True).items():
        setattr(db_item, key, value)
    await db.commit()
    await invalidate_item_cache(item_id)
    await invalidate_list_cache()
    return db_item
```

**Why**: Stale cache data causes data consistency issues. Invalidate-on-write
ensures cache freshness while maintaining performance benefits for reads.

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

Projects **SHOULD** implement different limits per user tier:

```python
# src/myapp/limiter.py
def get_rate_limit_key(request: Request) -> str:
    """Return user ID for authenticated requests, IP for anonymous."""
    if user := getattr(request.state, "user", None):
        return f"user:{user.id}"
    return get_remote_address(request)

def dynamic_limit(request: Request) -> str:
    """Return rate limit based on user tier."""
    if user := getattr(request.state, "user", None):
        limits = {
            "free": "100/hour",
            "pro": "1000/hour",
            "enterprise": "10000/hour",
        }
        return limits.get(user.tier, "100/hour")
    return "50/hour"  # Anonymous users

@router.get("/")
@limiter.limit(dynamic_limit)
async def list_items(request: Request) -> list[Item]:
    ...
```

**Why**: User-based rate limiting ensures fair API access based on subscription
tiers while protecting against anonymous abuse.

## Circuit Breakers

Projects calling external services **SHOULD** implement circuit breakers.

### Why Circuit Breakers

Circuit breakers prevent cascading failures when external services become
unavailable. They fail fast, reduce load on struggling services, and enable
graceful degradation.

### aiobreaker

Projects **SHOULD** use aiobreaker[^17] for async circuit breakers:

```python
# src/myapp/breakers.py
from aiobreaker import CircuitBreaker, CircuitBreakerListener
import logging

logger = logging.getLogger(__name__)

class LoggingListener(CircuitBreakerListener):
    def state_change(self, cb: CircuitBreaker, old_state, new_state) -> None:
        logger.warning(f"Circuit breaker {cb.name}: {old_state.name} -> {new_state.name}")

# Configure circuit breaker
payment_breaker = CircuitBreaker(
    fail_max=5,           # Open after 5 failures
    timeout_duration=30,  # Try again after 30 seconds
    listeners=[LoggingListener()],
    name="payment_service",
)
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

**Why**: Circuit breakers prevent thread pool exhaustion from slow failing calls
and give external services time to recover without being overwhelmed by retry
storms.

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
[^15]: [fastapi-cache2](https://github.com/long2ice/fastapi-cache) - Caching for FastAPI with Redis/Memcached backends (v0.2.2+)
[^16]: [slowapi](https://github.com/laurentS/slowapi) - Rate limiting for FastAPI based on flask-limiter
[^17]: [aiobreaker](https://github.com/arlyon/aiobreaker) - Async circuit breaker implementation
[^18]: [Unleash](https://www.getunleash.io/) - Open source feature flag platform
[^19]: [LaunchDarkly](https://launchdarkly.com/) - Enterprise feature management platform
[^20]: [Flagsmith](https://www.flagsmith.com/) - Open source feature flag and remote config service
