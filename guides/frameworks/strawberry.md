# Strawberry GraphQL Style Guide

> [Doctrine](../../README.md) > [Frameworks](../README.md) > Strawberry

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119][rfc2119].

[rfc2119]: https://datatracker.ietf.org/doc/html/rfc2119

Extends [Python style guide](../languages/python.md) with Strawberry GraphQL-specific conventions.

**Target Version**: Strawberry 0.287+ with Python 3.14

## Quick Reference

All Python tooling applies. Additional considerations:

| Task | Tool | Command |
| ---- | ---- | ------- |
| Install | uv | `uv add strawberry-graphql[fastapi]` |
| Run dev | Strawberry CLI | `strawberry server schema` |
| Test | pytest | `pytest` |
| Docs | Built-in | GraphiQL at `/graphql` |

## Why Strawberry?

Strawberry[^1] is a modern Python GraphQL library that uses Python's native type
hints and dataclasses to define schemas. Unlike schema-first approaches (like
Ariadne) or verbose class-based definitions (like Graphene), Strawberry
generates schemas directly from Python code.

**Key advantages**:

- Python-native schema definition using decorators and type hints
- Full async support for high-performance APIs
- Built-in Mypy plugin for static type checking
- First-class integrations with FastAPI, Django, and Flask
- DataLoader support for solving N+1 queries

Use Strawberry when building GraphQL APIs in Python, especially with FastAPI or
Django. For REST APIs, see [FastAPI](fastapi.md) or [Django REST
Framework](django.md).

## Project Structure

Projects **SHOULD** organize Strawberry applications by domain:

```text
my_app/
├── src/
│   └── myapp/
│       ├── __init__.py
│       ├── main.py              # FastAPI app with GraphQL router
│       ├── config.py            # Settings
│       ├── database.py          # Database setup
│       ├── graphql/
│       │   ├── __init__.py
│       │   ├── schema.py        # Root schema composition
│       │   ├── context.py       # GraphQL context
│       │   ├── dataloaders.py   # DataLoader definitions
│       │   ├── scalars.py       # Custom scalar types
│       │   └── types/
│       │       ├── __init__.py
│       │       ├── user.py      # User type + resolvers
│       │       └── order.py     # Order type + resolvers
│       ├── models/
│       │   ├── __init__.py
│       │   └── user.py          # SQLAlchemy models
│       └── services/
│           └── user.py          # Business logic
├── tests/
│   ├── conftest.py
│   └── graphql/
│       └── test_users.py
├── pyproject.toml
└── .env
```

**Why**: Separating GraphQL types from database models and business logic maintains clean
boundaries. The `graphql/types/` directory mirrors your domain, making navigation intuitive.

## Schema Definition

### Types

Projects **MUST** use `@strawberry.type` for GraphQL object types:

```python
# src/myapp/graphql/types/user.py
import strawberry
from datetime import datetime

@strawberry.type
class User:
    id: strawberry.ID
    email: str
    full_name: str
    created_at: datetime

    @strawberry.field
    def display_name(self) -> str:
        return self.full_name or self.email.split("@")[0]
```

**Why**: Strawberry leverages Python's type system for schema generation. The decorator pattern is
explicit and maintains Python's readability while generating accurate GraphQL schemas.

### Input Types

Projects **MUST** use `@strawberry.input` for mutation inputs:

```python
@strawberry.input
class CreateUserInput:
    email: str
    password: str
    full_name: str | None = None

@strawberry.input
class UpdateUserInput:
    email: str | None = None
    full_name: str | None = None
```

**Why**: Separate input types from output types. GraphQL requires this distinction, and it enables
different validation rules for creation vs. updates.

### Enums

Projects **MUST** use `@strawberry.enum` for enumeration types:

```python
import strawberry
from enum import Enum

@strawberry.enum
class OrderStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
```

## Resolvers

### Async Resolvers

Projects **MUST** use `async def` for resolvers that perform I/O:

```python
# src/myapp/graphql/types/user.py
import strawberry
from strawberry.types import Info
from myapp.graphql.context import Context
from myapp.models.user import User as UserModel

@strawberry.type
class Query:
    @strawberry.field
    async def user(self, info: Info[Context, None], id: strawberry.ID) -> User | None:
        db = info.context.db
        result = await db.execute(select(UserModel).where(UserModel.id == int(id)))
        user_model = result.scalar_one_or_none()
        if user_model:
            return User.from_model(user_model)
        return None

    @strawberry.field
    async def users(self, info: Info[Context, None]) -> list[User]:
        db = info.context.db
        result = await db.execute(select(UserModel))
        return [User.from_model(u) for u in result.scalars()]
```

**Why**: Strawberry documentation emphasizes: "It is recommended to use `async def` for all fields
if handling concurrent requests on a single worker." Synchronous functions block the entire worker
despite FastAPI's threadpool.

### Field Arguments

Projects **SHOULD** use type hints for field arguments:

```python
@strawberry.type
class Query:
    @strawberry.field
    async def users(
        self,
        info: Info[Context, None],
        limit: int = 10,
        offset: int = 0,
        status: OrderStatus | None = None,
    ) -> list[User]:
        query = select(UserModel)
        if status:
            query = query.where(UserModel.status == status.value)
        query = query.limit(limit).offset(offset)
        result = await info.context.db.execute(query)
        return [User.from_model(u) for u in result.scalars()]
```

## Mutations

Projects **MUST** organize mutations with clear naming and input types:

```python
# src/myapp/graphql/types/user.py
@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_user(
        self,
        info: Info[Context, None],
        input: CreateUserInput,
    ) -> User:
        service = UserService(info.context.db)
        user_model = await service.create_user(
            email=input.email,
            password=input.password,
            full_name=input.full_name,
        )
        return User.from_model(user_model)

    @strawberry.mutation
    async def update_user(
        self,
        info: Info[Context, None],
        id: strawberry.ID,
        input: UpdateUserInput,
    ) -> User:
        service = UserService(info.context.db)
        user_model = await service.update_user(
            user_id=int(id),
            **{k: v for k, v in input.__dict__.items() if v is not None},
        )
        return User.from_model(user_model)

    @strawberry.mutation
    async def delete_user(self, info: Info[Context, None], id: strawberry.ID) -> bool:
        service = UserService(info.context.db)
        return await service.delete_user(int(id))
```

**Why**: Use input types rather than multiple arguments for mutations with more than 2-3
parameters. This improves readability and makes schema evolution easier.

## DataLoaders

Projects **MUST** use DataLoaders to solve the N+1 query problem:

```python
# src/myapp/graphql/dataloaders.py
from collections.abc import Sequence
from strawberry.dataloader import DataLoader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from myapp.models.user import User as UserModel
from myapp.models.order import Order as OrderModel

async def load_users(keys: Sequence[int], db: AsyncSession) -> list[UserModel | None]:
    result = await db.execute(select(UserModel).where(UserModel.id.in_(keys)))
    users_by_id = {u.id: u for u in result.scalars()}
    return [users_by_id.get(key) for key in keys]

async def load_orders_by_user(
    keys: Sequence[int], db: AsyncSession
) -> list[list[OrderModel]]:
    result = await db.execute(select(OrderModel).where(OrderModel.user_id.in_(keys)))
    orders_by_user: dict[int, list[OrderModel]] = {key: [] for key in keys}
    for order in result.scalars():
        orders_by_user[order.user_id].append(order)
    return [orders_by_user[key] for key in keys]

def create_dataloaders(db: AsyncSession) -> dict[str, DataLoader]:
    return {
        "users": DataLoader(load_fn=lambda keys: load_users(keys, db)),
        "orders_by_user": DataLoader(load_fn=lambda keys: load_orders_by_user(keys, db)),
    }
```

```python
# Using DataLoaders in resolvers
@strawberry.type
class User:
    id: strawberry.ID
    email: str

    @strawberry.field
    async def orders(self, info: Info[Context, None]) -> list[Order]:
        orders = await info.context.dataloaders["orders_by_user"].load(int(self.id))
        return [Order.from_model(o) for o in orders]
```

**Why**: DataLoaders batch multiple individual loads into a single query. Without them, fetching 10
users with their orders would be 11 queries (1 + N). With DataLoaders, it's 2 queries.

### DataLoader Best Practices

1. **Create loaders per-request**: Instantiate DataLoaders in context to prevent cross-request
   cache pollution
2. **Clear cache after mutations**: Use `loader.clear(key)` after modifying data
3. **Prime cache when available**: Use `loader.prime(key, value)` when data is already loaded

## Context

Projects **MUST** use a typed context for dependency injection:

```python
# src/myapp/graphql/context.py
from dataclasses import dataclass
from strawberry.fastapi import BaseContext
from sqlalchemy.ext.asyncio import AsyncSession
from strawberry.dataloader import DataLoader
from myapp.models.user import User

@dataclass
class Context(BaseContext):
    db: AsyncSession
    dataloaders: dict[str, DataLoader]
    current_user: User | None = None
```

```python
# src/myapp/main.py
from fastapi import FastAPI, Depends
from strawberry.fastapi import GraphQLRouter
from myapp.graphql.schema import schema
from myapp.graphql.context import Context
from myapp.graphql.dataloaders import create_dataloaders
from myapp.database import get_db
from myapp.auth import get_current_user

async def get_context(
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
) -> Context:
    return Context(
        db=db,
        dataloaders=create_dataloaders(db),
        current_user=current_user,
    )

graphql_app = GraphQLRouter(schema, context_getter=get_context)
app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")
```

**Why**: Typed context enables IDE autocompletion and type checking. Creating DataLoaders and
database sessions per-request ensures proper resource cleanup and cache isolation.

## Permissions

Projects **MUST** use Strawberry's permission system for authorization:

```python
# src/myapp/graphql/permissions.py
from strawberry.permission import BasePermission
from strawberry.types import Info
from myapp.graphql.context import Context

class IsAuthenticated(BasePermission):
    message = "User is not authenticated"

    def has_permission(self, source: object, info: Info[Context, None], **kwargs) -> bool:
        return info.context.current_user is not None

class IsAdmin(BasePermission):
    message = "User is not an admin"

    def has_permission(self, source: object, info: Info[Context, None], **kwargs) -> bool:
        user = info.context.current_user
        return user is not None and user.is_admin

class IsOwner(BasePermission):
    message = "User does not own this resource"

    def has_permission(self, source: object, info: Info[Context, None], **kwargs) -> bool:
        user = info.context.current_user
        if user is None:
            return False
        # Check ownership based on the source object
        if hasattr(source, "user_id"):
            return source.user_id == user.id
        return False
```

```python
# Applying permissions
@strawberry.type
class Mutation:
    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def create_order(self, info: Info[Context, None], input: CreateOrderInput) -> Order:
        ...

    @strawberry.mutation(permission_classes=[IsAdmin])
    async def delete_user(self, info: Info[Context, None], id: strawberry.ID) -> bool:
        ...
```

**Why**: Declarative permissions keep authorization logic separate from business logic. Permission
classes are reusable and testable in isolation.

## Schema Composition

Projects **SHOULD** compose schemas from domain-specific types:

```python
# src/myapp/graphql/schema.py
import strawberry
from strawberry.extensions import QueryDepthLimiter, MaxTokensLimiter
from myapp.graphql.types.user import Query as UserQuery, Mutation as UserMutation
from myapp.graphql.types.order import Query as OrderQuery, Mutation as OrderMutation

@strawberry.type
class Query(UserQuery, OrderQuery):
    pass

@strawberry.type
class Mutation(UserMutation, OrderMutation):
    pass

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[
        QueryDepthLimiter(max_depth=10),
        MaxTokensLimiter(max_token_count=1000),
    ],
)
```

**Why**: Multiple inheritance for Query/Mutation types enables domain-driven organization while
producing a single coherent schema.

## Security Extensions

Projects **MUST** configure security extensions for production:

```python
from strawberry.extensions import (
    QueryDepthLimiter,
    MaxTokensLimiter,
    MaxAliasesLimiter,
    MaskErrors,
)

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[
        QueryDepthLimiter(max_depth=10),
        MaxTokensLimiter(max_token_count=1000),
        MaxAliasesLimiter(max_alias_count=15),
        MaskErrors(),  # Hide internal error details in production
    ],
)
```

| Extension | Purpose | Recommended Value |
|-----------|---------|-------------------|
| `QueryDepthLimiter` | Prevent deeply nested queries | 10-15 |
| `MaxTokensLimiter` | Limit query complexity | 1000-2000 |
| `MaxAliasesLimiter` | Prevent alias abuse | 10-20 |
| `MaskErrors` | Hide sensitive error info | Enable in production |

**Why**: GraphQL's flexibility can be exploited for denial-of-service attacks. These extensions
prevent abuse while allowing legitimate queries.

### Disabling Introspection

Projects **SHOULD** disable introspection in production:

```python
from strawberry.extensions import DisableIntrospection
from myapp.config import settings

extensions = [
    QueryDepthLimiter(max_depth=10),
]

if not settings.DEBUG:
    extensions.append(DisableIntrospection())

schema = strawberry.Schema(query=Query, mutation=Mutation, extensions=extensions)
```

## FastAPI Integration

Projects using FastAPI **MUST** follow this integration pattern:

```python
# src/myapp/main.py
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from myapp.graphql.schema import schema
from myapp.graphql.context import get_context
from myapp.config import settings

def create_app() -> FastAPI:
    app = FastAPI(title=settings.PROJECT_NAME)

    graphql_app = GraphQLRouter(
        schema,
        context_getter=get_context,
        graphql_ide="graphiql" if settings.DEBUG else None,
        allow_queries_via_get=False,  # Disable GET queries for security
    )

    app.include_router(graphql_app, prefix="/graphql")

    return app

app = create_app()
```

## Django Integration

Projects using Django **SHOULD** use Strawberry's Django integration:

```python
# myapp/schema.py
import strawberry
from strawberry_django import type as django_type
from myapp.models import User as UserModel

@django_type(UserModel)
class User:
    id: strawberry.auto
    email: strawberry.auto
    full_name: strawberry.auto
```

```python
# myapp/urls.py
from django.urls import path
from strawberry.django.views import AsyncGraphQLView
from myapp.schema import schema

urlpatterns = [
    path("graphql/", AsyncGraphQLView.as_view(schema=schema)),
]
```

## Type Checking with Mypy

Projects **MUST** enable Strawberry's Mypy plugin:

```toml
# pyproject.toml
[tool.mypy]
plugins = ["strawberry.ext.mypy_plugin"]
```

**Why**: The Mypy plugin validates that GraphQL types match their Python definitions, catching type
mismatches before runtime.

## Testing

Projects **MUST** test GraphQL operations using the schema directly:

```python
# tests/conftest.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from myapp.graphql.schema import schema
from myapp.graphql.context import Context
from myapp.graphql.dataloaders import create_dataloaders
from myapp.database import Base

@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        yield session

@pytest.fixture
def context(db_session: AsyncSession) -> Context:
    return Context(
        db=db_session,
        dataloaders=create_dataloaders(db_session),
        current_user=None,
    )
```

```python
# tests/graphql/test_users.py
import pytest
from myapp.graphql.schema import schema

@pytest.mark.asyncio
async def test_create_user(context) -> None:
    query = """
        mutation CreateUser($input: CreateUserInput!) {
            createUser(input: $input) {
                id
                email
                fullName
            }
        }
    """
    result = await schema.execute(
        query,
        variable_values={
            "input": {
                "email": "test@example.com",
                "password": "password123",
                "fullName": "Test User",
            }
        },
        context_value=context,
    )
    assert result.errors is None
    assert result.data["createUser"]["email"] == "test@example.com"

@pytest.mark.asyncio
async def test_get_users(context, user_factory) -> None:
    await user_factory.create_batch(3)

    query = """
        query GetUsers {
            users {
                id
                email
            }
        }
    """
    result = await schema.execute(query, context_value=context)
    assert result.errors is None
    assert len(result.data["users"]) == 3
```

**Why**: Testing against the schema directly (rather than HTTP) isolates GraphQL logic from
transport concerns. Pass variables dynamically rather than hardcoding them in query strings.

### Testing Permissions

```python
@pytest.mark.asyncio
async def test_create_order_requires_auth(context) -> None:
    query = """
        mutation CreateOrder($input: CreateOrderInput!) {
            createOrder(input: $input) {
                id
            }
        }
    """
    result = await schema.execute(
        query,
        variable_values={"input": {"items": []}},
        context_value=context,  # No current_user
    )
    assert result.errors is not None
    assert "not authenticated" in result.errors[0].message.lower()
```

## Error Handling

Projects **SHOULD** use custom error types for domain errors:

```python
# src/myapp/graphql/errors.py
import strawberry

@strawberry.type
class ValidationError:
    field: str
    message: str

@strawberry.type
class NotFoundError:
    message: str = "Resource not found"

# Union type for mutation responses
UserResult = strawberry.union("UserResult", types=[User, ValidationError, NotFoundError])
```

```python
@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_user(
        self, info: Info[Context, None], input: CreateUserInput
    ) -> UserResult:
        # Check for existing user
        existing = await info.context.db.execute(
            select(UserModel).where(UserModel.email == input.email)
        )
        if existing.scalar_one_or_none():
            return ValidationError(field="email", message="Email already registered")

        user = await create_user_service(info.context.db, input)
        return User.from_model(user)
```

**Why**: Union types for results enable type-safe error handling in clients. This follows the
"errors as data" pattern preferred in GraphQL over throwing exceptions.

## Subscriptions

Projects **MAY** implement subscriptions for real-time updates:

```python
import asyncio
from collections.abc import AsyncGenerator
import strawberry
from strawberry.types import Info
from myapp.graphql.context import Context

@strawberry.type
class Subscription:
    @strawberry.subscription
    async def order_status_changed(
        self, info: Info[Context, None], order_id: strawberry.ID
    ) -> AsyncGenerator[Order, None]:
        pubsub = info.context.pubsub
        async for message in pubsub.subscribe(f"order:{order_id}"):
            yield Order.from_dict(message)
```

For production subscriptions, use Redis pub/sub or similar message brokers.

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
        additional_dependencies: [strawberry-graphql]
        args: [--strict]
```

## See Also

- [Python Style Guide](../languages/python.md) - Language-level Python conventions
- [FastAPI Style Guide](fastapi.md) - FastAPI-specific patterns
- [Django Style Guide](django.md) - Django-specific patterns
- [GraphQL Best Practices](../api/graphql.md) - General GraphQL design patterns

## References

[^1]: [Strawberry GraphQL](https://strawberry.rocks/) - Python GraphQL library
[^2]: [Strawberry FastAPI Integration](https://strawberry.rocks/docs/integrations/fastapi) - FastAPI setup guide
[^3]: [Strawberry DataLoaders](https://strawberry.rocks/docs/guides/dataloaders) - N+1 query solution
[^4]: [Strawberry Permissions](https://strawberry.rocks/docs/guides/permissions) - Authorization patterns
[^5]: [Strawberry Extensions](https://strawberry.rocks/docs/extensions) - Security and performance extensions
