# FastAPI Style Guide

> [Doctrine](../../README.md) > [Frameworks](../README.md) > FastAPI

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119.txt).

Extends [Python style guide](../languages/python.md) with FastAPI-specific conventions.

**Target Version**: FastAPI 0.115+ with Python 3.14

## Quick Reference

All Python tooling applies. Additional considerations:

| Task | Tool | Command |
|------|------|---------|
| Install | uv | `uv add fastapi uvicorn` |
| Run dev | Uvicorn | `uvicorn myapp.main:app --reload` |
| Test | pytest + TestClient | `pytest` |
| Docs | Built-in | `/docs` (Swagger) or `/redoc` |

## Why FastAPI?

FastAPI[^1] is an async-first, high-performance web framework with automatic OpenAPI documentation, built-in request validation via Pydantic, and excellent type hint integration.

**Key advantages**:
- Async/await native support for high concurrency
- Automatic OpenAPI/Swagger documentation
- Pydantic validation with helpful error messages
- Performance comparable to Node.js and Go[^2]

Use FastAPI for APIs requiring high throughput, async I/O, or automatic API documentation. Choose Flask for simpler synchronous applications or Django for full-featured web applications with admin panels.

## Project Structure

Projects **SHOULD** organize FastAPI applications by feature:

```
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

**Why**: Organizing by feature keeps related code together. Separating app creation enables testing with different configurations and multiple app instances.

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

**Why**: Dependency injection decouples route handlers from resource creation, enables testing with mock dependencies, and manages resource lifecycle automatically.

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

**Why**: Pydantic provides automatic validation, serialization, and helpful error messages. Separate request/response models prevent exposing sensitive fields and enable API evolution.

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

**Why**: Using async database access preserves FastAPI's async benefits and prevents blocking the event loop.

### Database Library Recommendations

| Database | Sync | Async |
|----------|------|-------|
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

**Why**: `TestClient` provides synchronous testing of async endpoints without running a server. Dependency overrides enable injecting test database sessions and mocked dependencies.

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

For heavier workloads, use Celery or similar task queues.

## See Also

- [Python Style Guide](../languages/python.md) - Language-level Python conventions
- [Flask Style Guide](flask.md) - Lightweight sync framework
- [Django Style Guide](django.md) - Full-featured web framework

## References

[^1]: [FastAPI](https://fastapi.tiangolo.com/) - Modern, fast web framework for building APIs
[^2]: [FastAPI Benchmarks](https://fastapi.tiangolo.com/#performance) - Performance comparisons
[^3]: [FastAPI Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/) - Dependency injection system
[^4]: [Pydantic](https://docs.pydantic.dev/) - Data validation using Python type hints
