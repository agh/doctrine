# Axum Style Guide

> [Doctrine](../../README.md) > [Frameworks](../README.md) > Axum

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in
[RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

Extends [Rust style guide](../languages/rust.md) with Axum-specific conventions.

**Target Version**: Axum 0.8+ with Rust 2024 edition

## Quick Reference

All Rust tooling applies. Additional tools:

| Task | Tool | Command/Crate |
| ---- | ---- | ------------- |
| Format | rustfmt | `cargo fmt` |
| Lint | Clippy | `cargo clippy` |
| Test | cargo test | `cargo test` |
| Test API | tower::ServiceExt | See Testing section |
| Database | SQLx | `cargo sqlx prepare` |
| Auth (sessions) | axum-login | See Security section |
| Auth (JWT) | jsonwebtoken | See Security section |
| Authorization | casbin-rs | See Security section |
| WebSocket | axum::extract::ws | See WebSocket section |
| Logging | tracing | See Observability section |
| Metrics | axum-prometheus | See Observability section |
| Background Jobs | apalis | See Background Jobs section |
| In-Memory Cache | moka | See Caching section |
| Distributed Cache | redis-rs + deadpool | See Caching section |
| Rate Limiting | tower-governor | See Rate Limiting section |
| Circuit Breaker | recloser | See Circuit Breakers section |
| Feature Flags | unleash-api-client | See Feature Flags section |

## Why Axum?

Axum[^1] is a web framework built on Tower[^2] and Hyper[^3], designed
for the Tokio ecosystem with focus on type safety and ergonomics.

**Key advantages**:

- Native async/await with Tokio runtime integration
- Type-safe extractors with compile-time guarantees
- Ergonomic routing with minimal boilerplate
- Composable middleware via Tower
- Zero-cost abstractions with excellent performance[^4]

**When to use Axum**: Choose Axum for greenfield async Rust services
requiring type safety, high performance, and composability. Consider
Actix-web[^5] for maximum performance or Rocket[^6] for simpler
synchronous applications.

## Project Structure

Projects **SHOULD** organize code by feature:

```text
my-api/
├── src/
│   ├── main.rs           # Application entry point
│   ├── app.rs            # App factory and router setup
│   ├── config.rs         # Configuration via environment
│   ├── error.rs          # Error types and handlers
│   ├── state.rs          # Shared application state
│   ├── routes/
│   │   ├── mod.rs
│   │   ├── users.rs
│   │   └── health.rs
│   ├── handlers/
│   │   ├── mod.rs
│   │   └── users.rs
│   ├── models/
│   │   ├── mod.rs
│   │   └── user.rs
│   └── middleware/
│       ├── mod.rs
│       └── auth.rs
├── migrations/
├── tests/
├── Cargo.toml
└── .env
```

```rust
// src/main.rs
use my_api::app::create_app;
use my_api::config::Config;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let config = Config::from_env()?;
    let app = create_app(config.clone()).await?;

    let listener = tokio::net::TcpListener::bind(&config.addr).await?;
    axum::serve(listener, app).await?;

    Ok(())
}
```

**Why**: Feature-based organization scales better than layer-based
organization. Keeping app creation separate enables testing with
different configurations.

## Routing

### Router Composition

Projects **MUST** compose routes using `Router::merge` and `Router::nest`:

```rust
// src/app.rs
use axum::Router;
use crate::routes::{users, health};
use crate::state::AppState;

pub async fn create_app(config: Config) -> anyhow::Result<Router> {
    let state = AppState::new(config).await?;

    let app = Router::new()
        .merge(health::routes())
        .nest("/api/v1", api_routes())
        .with_state(state);

    Ok(app)
}

fn api_routes() -> Router<AppState> {
    Router::new()
        .nest("/users", users::routes())
        .nest("/posts", posts::routes())
}
```

**Why**: Composition via `merge` and `nest` provides better modularity
and enables mounting sub-routers at different paths. This pattern
allows feature modules to define their own routes independently.

### Method Routing

Routes **SHOULD** use method routing for clarity:

```rust
// src/routes/users.rs
use axum::{Router, routing::{get, post}};
use crate::handlers::users;
use crate::state::AppState;

pub fn routes() -> Router<AppState> {
    Router::new()
        .route("/", get(users::list).post(users::create))
        .route("/:id", get(users::get).put(users::update).delete(users::delete))
}
```

**Do**:

```rust
Router::new()
    .route("/users", get(list_users).post(create_user))
```

**Don't**:

```rust
Router::new()
    .route("/users", get(list_users))
    .route("/users", post(create_user))  // Redundant
```

## Extractors

### Order of Extractors

Extractors **MUST** appear in this order in handler function signatures:

1. `Path` (URL path parameters)
2. `Query` (query string parameters)
3. `State` (application state)
4. `Json` / `Form` (request body)
5. `Extension` (request extensions)
6. `Request` (full request, consumes body)

```rust
use axum::{
    extract::{Path, Query, State},
    Json,
};
use serde::{Deserialize, Serialize};

#[derive(Deserialize)]
pub struct Pagination {
    page: Option<u32>,
    per_page: Option<u32>,
}

#[derive(Deserialize)]
pub struct UpdateUserRequest {
    name: Option<String>,
    email: Option<String>,
}

pub async fn update_user(
    Path(user_id): Path<i64>,
    Query(params): Query<Pagination>,
    State(state): State<AppState>,
    Json(payload): Json<UpdateUserRequest>,
) -> Result<Json<User>, AppError> {
    // Handler implementation
}
```

**Why**: This order matches Axum's extractor precedence and makes
handlers more readable by placing path parameters first (most specific)
and body last (most complex).

### Custom Extractors

Projects **SHOULD** create custom extractors for common patterns:

```rust
// src/extractors/auth.rs
use axum::{
    async_trait,
    extract::FromRequestParts,
    http::{request::Parts, StatusCode},
    RequestPartsExt,
};
use axum_extra::headers::{Authorization, authorization::Bearer};
use axum_extra::TypedHeader;

pub struct AuthUser {
    pub user_id: i64,
}

#[async_trait]
impl<S> FromRequestParts<S> for AuthUser
where
    S: Send + Sync,
{
    type Rejection = (StatusCode, &'static str);

    async fn from_request_parts(parts: &mut Parts, _state: &S) -> Result<Self, Self::Rejection> {
        let TypedHeader(Authorization(bearer)) = parts
            .extract::<TypedHeader<Authorization<Bearer>>>()
            .await
            .map_err(|_| (StatusCode::UNAUTHORIZED, "Missing authorization header"))?;

        let user_id = verify_token(bearer.token())
            .map_err(|_| (StatusCode::UNAUTHORIZED, "Invalid token"))?;

        Ok(AuthUser { user_id })
    }
}
```

```rust
// Usage in handlers
pub async fn protected_route(
    auth: AuthUser,  // Custom extractor
    State(state): State<AppState>,
) -> Result<Json<User>, AppError> {
    let user = state.db.get_user(auth.user_id).await?;
    Ok(Json(user))
}
```

**Why**: Custom extractors encapsulate common authentication and
validation logic, reducing boilerplate and ensuring consistent error
handling across routes.

## Error Handling

### Unified Error Type

Projects **MUST** define a unified error type implementing `IntoResponse`:

```rust
// src/error.rs
use axum::{
    response::{IntoResponse, Response},
    http::StatusCode,
    Json,
};
use serde::Serialize;

#[derive(Debug)]
pub enum AppError {
    NotFound,
    Unauthorized,
    Database(sqlx::Error),
    Validation(String),
}

#[derive(Serialize)]
struct ErrorResponse {
    error: String,
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        let (status, message) = match self {
            Self::NotFound => (StatusCode::NOT_FOUND, "Resource not found"),
            Self::Unauthorized => (StatusCode::UNAUTHORIZED, "Unauthorized"),
            Self::Database(_) => (StatusCode::INTERNAL_SERVER_ERROR, "Database error"),
            Self::Validation(msg) => return (
                StatusCode::BAD_REQUEST,
                Json(ErrorResponse { error: msg }),
            ).into_response(),
        };

        (status, Json(ErrorResponse { error: message.to_string() })).into_response()
    }
}

impl From<sqlx::Error> for AppError {
    fn from(err: sqlx::Error) -> Self {
        match err {
            sqlx::Error::RowNotFound => Self::NotFound,
            _ => Self::Database(err),
        }
    }
}
```

**Why**: A unified error type provides consistent API responses and
enables using `?` operator in handlers. Implementing `IntoResponse`
allows returning errors directly from handlers.

### Using thiserror and anyhow

Projects **SHOULD** use thiserror[^7] for library errors and anyhow[^8] for application errors:

```rust
// src/error.rs
use thiserror::Error;

#[derive(Error, Debug)]
pub enum AppError {
    #[error("Resource not found")]
    NotFound,

    #[error("Unauthorized: {0}")]
    Unauthorized(String),

    #[error("Database error: {0}")]
    Database(#[from] sqlx::Error),

    #[error("Validation failed: {0}")]
    Validation(String),
}
```

**Do**:

```rust
use thiserror::Error;  // For typed errors

#[derive(Error, Debug)]
pub enum AppError {
    #[error("User not found")]
    NotFound,
}
```

**Don't**:

```rust
use anyhow::Error;  // Too generic for API errors

pub async fn handler() -> Result<Json<User>, Error> {
    // Don't use anyhow for handler return types
}
```

## Middleware

### Tower Layers

Projects **SHOULD** use Tower layers for cross-cutting concerns:

```rust
use axum::{
    Router,
    middleware::{self, Next},
    http::Request,
    response::Response,
};
use tower_http::{
    trace::TraceLayer,
    cors::CorsLayer,
    compression::CompressionLayer,
};
use std::time::Duration;

pub fn create_app() -> Router {
    Router::new()
        .nest("/api", api_routes())
        .layer(
            ServiceBuilder::new()
                .layer(TraceLayer::new_for_http())
                .layer(CompressionLayer::new())
                .layer(CorsLayer::permissive())
                .layer(middleware::from_fn(timeout_middleware))
        )
}

async fn timeout_middleware<B>(
    req: Request<B>,
    next: Next<B>,
) -> Result<Response, StatusCode> {
    tokio::time::timeout(
        Duration::from_secs(30),
        next.run(req)
    )
    .await
    .map_err(|_| StatusCode::REQUEST_TIMEOUT)
}
```

**Why**: Tower's layer system provides composable, reusable middleware.
Using `ServiceBuilder` ensures middleware is applied in the correct
order (inner to outer).

### Custom Middleware

Custom middleware **SHOULD** use `middleware::from_fn` for simplicity:

```rust
use axum::{
    middleware::{self, Next},
    http::Request,
    response::Response,
};

async fn auth_middleware<B>(
    req: Request<B>,
    next: Next<B>,
) -> Result<Response, StatusCode> {
    let auth_header = req.headers()
        .get("authorization")
        .and_then(|h| h.to_str().ok());

    match auth_header {
        Some(token) if verify_token(token) => Ok(next.run(req).await),
        _ => Err(StatusCode::UNAUTHORIZED),
    }
}

// Apply to specific routes
let protected = Router::new()
    .route("/admin", get(admin_handler))
    .layer(middleware::from_fn(auth_middleware));
```

**Why**: `from_fn` provides the simplest way to create middleware
without implementing `Layer` and `Service` traits manually.

## State Management

### Shared State

Projects **MUST** use `State` extractor for sharing state:

```rust
// src/state.rs
use sqlx::PgPool;

#[derive(Clone)]
pub struct AppState {
    pub db: PgPool,
    pub config: Config,
}

impl AppState {
    pub async fn new(config: Config) -> anyhow::Result<Self> {
        let db = PgPool::connect(&config.database_url).await?;
        Ok(Self { db, config })
    }
}
```

```rust
// src/app.rs
use axum::Router;

pub async fn create_app(config: Config) -> anyhow::Result<Router> {
    let state = AppState::new(config).await?;

    let app = Router::new()
        .route("/users", get(list_users))
        .with_state(state);  // Attach state to router

    Ok(app)
}
```

```rust
// src/handlers/users.rs
pub async fn list_users(
    State(state): State<AppState>,
) -> Result<Json<Vec<User>>, AppError> {
    let users = sqlx::query_as!(User, "SELECT * FROM users")
        .fetch_all(&state.db)
        .await?;

    Ok(Json(users))
}
```

**Why**: `State` is the recommended way to share data across handlers.
The state type must implement `Clone`, which is efficient when wrapping
`Arc` or connection pools.

### State Guidelines

State types **MUST** implement `Clone` and **SHOULD** use `Arc` for non-Clone fields:

```rust
use std::sync::Arc;

#[derive(Clone)]
pub struct AppState {
    pub db: PgPool,              // Clone implemented (uses Arc internally)
    pub config: Arc<Config>,     // Wrap in Arc for cheap cloning
}
```

**Do**:

```rust
#[derive(Clone)]
pub struct AppState {
    pub pool: PgPool,  // Already uses Arc internally
}
```

**Don't**:

```rust
pub struct AppState {
    pub pool: PgPool,  // Missing Clone derive
}
```

## Testing

### Testing with tower::ServiceExt

Projects **MUST** test handlers using `tower::ServiceExt::oneshot`:

```rust
// tests/users_test.rs
use axum::{
    body::Body,
    http::{Request, StatusCode},
};
use tower::ServiceExt;
use serde_json::json;

#[tokio::test]
async fn test_create_user() {
    let app = create_test_app().await;

    let response = app
        .oneshot(
            Request::builder()
                .method("POST")
                .uri("/api/users")
                .header("content-type", "application/json")
                .body(Body::from(
                    serde_json::to_string(&json!({
                        "name": "Alice",
                        "email": "alice@example.com"
                    })).unwrap()
                ))
                .unwrap()
        )
        .await
        .unwrap();

    assert_eq!(response.status(), StatusCode::CREATED);

    let body = axum::body::to_bytes(response.into_body(), usize::MAX)
        .await
        .unwrap();
    let user: User = serde_json::from_slice(&body).unwrap();

    assert_eq!(user.name, "Alice");
}
```

**Why**: `tower::ServiceExt` allows testing the router as a `Service`
without running an HTTP server, enabling fast, isolated unit tests.

### Test Fixtures

Projects **SHOULD** create test helpers for common patterns:

```rust
// tests/common/mod.rs
use axum::Router;
use sqlx::PgPool;

pub async fn create_test_app() -> Router {
    let config = Config::test();
    let pool = PgPool::connect(&config.database_url).await.unwrap();

    // Run migrations
    sqlx::migrate!().run(&pool).await.unwrap();

    let state = AppState { db: pool, config: Arc::new(config) };
    create_app_with_state(state)
}

pub async fn create_test_user(pool: &PgPool, name: &str) -> User {
    sqlx::query_as!(
        User,
        "INSERT INTO users (name, email) VALUES ($1, $2) RETURNING *",
        name,
        format!("{}@example.com", name)
    )
    .fetch_one(pool)
    .await
    .unwrap()
}
```

## Database Integration

### SQLx with Compile-Time Verification

Projects **MUST** use SQLx[^9] with compile-time query verification:

```rust
// src/models/user.rs
use sqlx::FromRow;
use serde::{Deserialize, Serialize};

#[derive(Debug, FromRow, Serialize, Deserialize)]
pub struct User {
    pub id: i64,
    pub name: String,
    pub email: String,
    pub created_at: chrono::DateTime<chrono::Utc>,
}

#[derive(Deserialize)]
pub struct CreateUser {
    pub name: String,
    pub email: String,
}
```

```rust
// src/handlers/users.rs
use sqlx::PgPool;
use axum::{extract::State, Json};

pub async fn create_user(
    State(state): State<AppState>,
    Json(payload): Json<CreateUser>,
) -> Result<Json<User>, AppError> {
    let user = sqlx::query_as!(
        User,
        r#"
        INSERT INTO users (name, email)
        VALUES ($1, $2)
        RETURNING id, name, email, created_at
        "#,
        payload.name,
        payload.email
    )
    .fetch_one(&state.db)
    .await?;

    Ok(Json(user))
}

pub async fn get_user(
    Path(id): Path<i64>,
    State(state): State<AppState>,
) -> Result<Json<User>, AppError> {
    let user = sqlx::query_as!(
        User,
        r#"
        SELECT id, name, email, created_at
        FROM users
        WHERE id = $1
        "#,
        id
    )
    .fetch_one(&state.db)
    .await?;

    Ok(Json(user))
}
```

**Why**: SQLx's `query_as!` macro provides compile-time verification of
SQL queries against the database schema, catching errors before
runtime. It also generates type-safe bindings automatically.

### Migrations

Projects **MUST** use SQLx migrations:

```bash
# Create migration
sqlx migrate add create_users_table

# Run migrations
sqlx migrate run

# Prepare for offline mode (CI)
cargo sqlx prepare
```

```sql
-- migrations/20240101000000_create_users_table.sql
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
```

**Why**: SQLx migrations integrate with compile-time verification and
support offline mode via `cargo sqlx prepare`, enabling CI without a
running database.

### Transaction Patterns

Database operations **SHOULD** use transactions for consistency:

```rust
pub async fn transfer_credits(
    from_user_id: i64,
    to_user_id: i64,
    amount: i64,
    pool: &PgPool,
) -> Result<(), AppError> {
    let mut tx = pool.begin().await?;

    sqlx::query!(
        "UPDATE users SET credits = credits - $1 WHERE id = $2",
        amount,
        from_user_id
    )
    .execute(&mut *tx)
    .await?;

    sqlx::query!(
        "UPDATE users SET credits = credits + $1 WHERE id = $2",
        amount,
        to_user_id
    )
    .execute(&mut *tx)
    .await?;

    tx.commit().await?;
    Ok(())
}
```

## Security

### Authentication with axum-login

Projects **SHOULD** use axum-login[^10] for session-based authentication:

```rust
// src/auth.rs
use axum_login::{
    AuthUser, AuthnBackend, AuthSession, AuthManagerLayerBuilder,
};
use async_trait::async_trait;
use password_auth::verify_password;
use tokio::task;

#[derive(Clone, Debug)]
pub struct User {
    pub id: i64,
    pub username: String,
    pub password_hash: String,
}

impl AuthUser for User {
    type Id = i64;

    fn id(&self) -> Self::Id {
        self.id
    }

    fn session_auth_hash(&self) -> &[u8] {
        self.password_hash.as_bytes()
    }
}

#[derive(Clone)]
pub struct Backend {
    db: PgPool,
}

#[derive(Clone, Deserialize)]
pub struct Credentials {
    pub username: String,
    pub password: String,
}

#[async_trait]
impl AuthnBackend for Backend {
    type User = User;
    type Credentials = Credentials;
    type Error = sqlx::Error;

    async fn authenticate(
        &self,
        creds: Self::Credentials,
    ) -> Result<Option<Self::User>, Self::Error> {
        let user = sqlx::query_as!(
            User,
            "SELECT id, username, password_hash FROM users WHERE username = $1",
            creds.username
        )
        .fetch_optional(&self.db)
        .await?;

        // Verify password in blocking task to avoid blocking async runtime
        task::spawn_blocking(|| {
            Ok(user.filter(|user| {
                verify_password(&creds.password, &user.password_hash).is_ok()
            }))
        })
        .await
        .map_err(|_| sqlx::Error::PoolClosed)?
    }

    async fn get_user(&self, user_id: &i64) -> Result<Option<Self::User>, Self::Error> {
        sqlx::query_as!(User, "SELECT * FROM users WHERE id = $1", user_id)
            .fetch_optional(&self.db)
            .await
    }
}
```

```rust
// src/app.rs - Setting up the auth layer
use axum_login::tower_sessions::{MemoryStore, SessionManagerLayer};
use axum_login::AuthManagerLayerBuilder;

pub async fn create_app(config: Config) -> anyhow::Result<Router> {
    let state = AppState::new(config).await?;
    let backend = Backend { db: state.db.clone() };

    let session_store = MemoryStore::default();
    let session_layer = SessionManagerLayer::new(session_store)
        .with_secure(true)
        .with_same_site(tower_sessions::cookie::SameSite::Strict);

    let auth_layer = AuthManagerLayerBuilder::new(backend, session_layer).build();

    let app = Router::new()
        .merge(protected_routes())
        .merge(public_routes())
        .layer(auth_layer)
        .with_state(state);

    Ok(app)
}

// Protected route handler
pub async fn profile(auth_session: AuthSession<Backend>) -> Result<Json<User>, AppError> {
    auth_session
        .user
        .ok_or(AppError::Unauthorized("Not logged in".into()))
        .map(Json)
}
```

**Why**: axum-login provides a type-safe, Tower-based authentication
layer with support for arbitrary user types and backends. It integrates
seamlessly with Axum's extractor system and supports both
authentication and authorization via traits.

### JWT Authentication with jsonwebtoken

For stateless API authentication, projects **SHOULD** use jsonwebtoken[^11]:

```rust
// src/jwt.rs
use jsonwebtoken::{decode, encode, DecodingKey, EncodingKey, Header, Validation};
use serde::{Deserialize, Serialize};
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Debug, Serialize, Deserialize)]
pub struct Claims {
    pub sub: String,        // Subject (user ID)
    pub exp: u64,           // Expiration time
    pub iat: u64,           // Issued at
    pub roles: Vec<String>, // User roles
}

pub struct JwtKeys {
    encoding: EncodingKey,
    decoding: DecodingKey,
}

impl JwtKeys {
    /// Create keys from a secret. For production, use RS256 with RSA keys (4096-bit minimum).
    pub fn new(secret: &[u8]) -> Self {
        Self {
            encoding: EncodingKey::from_secret(secret),
            decoding: DecodingKey::from_secret(secret),
        }
    }

    pub fn from_rsa_pem(private_key: &[u8], public_key: &[u8]) -> Result<Self, AppError> {
        Ok(Self {
            encoding: EncodingKey::from_rsa_pem(private_key)?,
            decoding: DecodingKey::from_rsa_pem(public_key)?,
        })
    }
}

pub fn create_token(keys: &JwtKeys, user_id: &str, roles: Vec<String>) -> Result<String, AppError> {
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .expect("Time went backwards")
        .as_secs();

    let claims = Claims {
        sub: user_id.to_string(),
        exp: now + 3600, // 1 hour expiration
        iat: now,
        roles,
    };

    encode(&Header::default(), &claims, &keys.encoding)
        .map_err(|e| AppError::Internal(format!("Token creation failed: {}", e)))
}

pub fn verify_token(keys: &JwtKeys, token: &str) -> Result<Claims, AppError> {
    let validation = Validation::default();

    decode::<Claims>(token, &keys.decoding, &validation)
        .map(|data| data.claims)
        .map_err(|e| AppError::Unauthorized(format!("Invalid token: {}", e)))
}
```

```rust
// src/extractors/jwt_auth.rs - JWT extractor
use axum::{
    async_trait,
    extract::FromRequestParts,
    http::{request::Parts, StatusCode},
    RequestPartsExt,
};
use axum_extra::headers::{Authorization, authorization::Bearer};
use axum_extra::TypedHeader;

pub struct JwtAuth {
    pub user_id: String,
    pub roles: Vec<String>,
}

#[async_trait]
impl<S> FromRequestParts<S> for JwtAuth
where
    S: Send + Sync,
    AppState: FromRef<S>,
{
    type Rejection = AppError;

    async fn from_request_parts(parts: &mut Parts, state: &S) -> Result<Self, Self::Rejection> {
        let TypedHeader(Authorization(bearer)) = parts
            .extract::<TypedHeader<Authorization<Bearer>>>()
            .await
            .map_err(|_| AppError::Unauthorized("Missing authorization header".into()))?;

        let state = AppState::from_ref(state);
        let claims = verify_token(&state.jwt_keys, bearer.token())?;

        Ok(JwtAuth {
            user_id: claims.sub,
            roles: claims.roles,
        })
    }
}
```

**Do**:

```rust
// Use asymmetric keys (RS256) in production
let keys = JwtKeys::from_rsa_pem(&private_key, &public_key)?;

// Set reasonable expiration times
let claims = Claims {
    exp: now + 3600,  // 1 hour for access tokens
    // ...
};
```

**Don't**:

```rust
// Don't use weak secrets
let keys = JwtKeys::new(b"secret");  // Too short and predictable

// Don't set very long expiration
let claims = Claims {
    exp: now + 86400 * 365,  // 1 year - too long for access tokens
    // ...
};
```

**Why**: JWT provides stateless authentication suitable for APIs and microservices. The
jsonwebtoken crate supports all standard algorithms. Use short-lived tokens with refresh token
rotation for enhanced security.

### Authorization with Casbin

Projects **SHOULD** use casbin-rs[^12] for flexible authorization (RBAC, ABAC):

```rust
// src/authz.rs
use casbin::{CoreApi, Enforcer, MgmtApi};
use std::sync::Arc;
use tokio::sync::RwLock;

pub type SharedEnforcer = Arc<RwLock<Enforcer>>;

pub async fn create_enforcer() -> anyhow::Result<SharedEnforcer> {
    // Model defines access control rules structure
    let enforcer = Enforcer::new("config/rbac_model.conf", "config/policy.csv").await?;
    Ok(Arc::new(RwLock::new(enforcer)))
}

// Check if user has permission
pub async fn check_permission(
    enforcer: &SharedEnforcer,
    subject: &str,
    object: &str,
    action: &str,
) -> bool {
    let e = enforcer.read().await;
    e.enforce((subject, object, action)).unwrap_or(false)
}

// Add role to user
pub async fn add_role_for_user(
    enforcer: &SharedEnforcer,
    user: &str,
    role: &str,
) -> anyhow::Result<bool> {
    let mut e = enforcer.write().await;
    Ok(e.add_role_for_user(user, role, None).await?)
}
```

```ini
# config/rbac_model.conf
[request_definition]
r = sub, obj, act

[policy_definition]
p = sub, obj, act

[role_definition]
g = _, _

[policy_effect]
e = some(where (p.eft == allow))

[matchers]
m = g(r.sub, p.sub) && r.obj == p.obj && r.act == p.act
```

```csv
# config/policy.csv
p, admin, /users, read
p, admin, /users, write
p, admin, /users, delete
p, editor, /posts, read
p, editor, /posts, write
p, viewer, /posts, read

g, alice, admin
g, bob, editor
```

```rust
// Authorization middleware
use axum::middleware::Next;
use axum::http::Request;

pub async fn require_permission(
    State(state): State<AppState>,
    auth: JwtAuth,
    req: Request<Body>,
    next: Next,
) -> Result<Response, AppError> {
    let path = req.uri().path();
    let method = match req.method() {
        &Method::GET => "read",
        &Method::POST | &Method::PUT | &Method::PATCH => "write",
        &Method::DELETE => "delete",
        _ => "read",
    };

    if !check_permission(&state.enforcer, &auth.user_id, path, method).await {
        return Err(AppError::Forbidden("Insufficient permissions".into()));
    }

    Ok(next.run(req).await)
}
```

**Why**: Casbin provides a flexible, policy-based authorization system supporting ACL, RBAC, and
ABAC models. Policies can be stored in files or databases and modified at runtime without code
changes.

### Tower-HTTP Auth Layers

Projects **SHOULD** use tower-http[^13] for common authentication patterns:

```rust
use tower_http::validate_request::ValidateRequestHeaderLayer;
use tower_http::auth::RequireAuthorizationLayer;

// Basic auth for internal endpoints
let admin_routes = Router::new()
    .route("/admin/metrics", get(metrics))
    .layer(ValidateRequestHeaderLayer::basic("admin", "secret"));

// Bearer token validation
let api_routes = Router::new()
    .route("/api/data", get(get_data))
    .layer(RequireAuthorizationLayer::bearer("expected-token"));
```

**Why**: tower-http provides pre-built authentication layers that integrate directly with Tower's
middleware system. Use these for simple authentication needs; use axum-login or custom extractors
for more complex requirements.

## WebSocket

### Native Axum WebSocket Support

Projects **MUST** use Axum's built-in WebSocket support[^14] for real-time communication:

```rust
// src/handlers/ws.rs
use axum::{
    extract::{
        ws::{Message, WebSocket, WebSocketUpgrade},
        State,
    },
    response::Response,
};
use futures_util::{SinkExt, StreamExt};
use tokio::sync::broadcast;

pub async fn ws_handler(
    ws: WebSocketUpgrade,
    State(state): State<AppState>,
) -> Response {
    ws.on_upgrade(|socket| handle_socket(socket, state))
}

async fn handle_socket(socket: WebSocket, state: AppState) {
    let (mut sender, mut receiver) = socket.split();

    // Subscribe to broadcast channel
    let mut rx = state.broadcast_tx.subscribe();

    // Spawn task to forward broadcast messages to client
    let mut send_task = tokio::spawn(async move {
        while let Ok(msg) = rx.recv().await {
            if sender.send(Message::Text(msg)).await.is_err() {
                break;
            }
        }
    });

    // Receive messages from client
    let mut recv_task = tokio::spawn(async move {
        while let Some(Ok(msg)) = receiver.next().await {
            match msg {
                Message::Text(text) => {
                    tracing::info!("Received: {}", text);
                    // Handle text message
                }
                Message::Binary(data) => {
                    tracing::info!("Received {} bytes", data.len());
                    // Handle binary message
                }
                Message::Ping(data) => {
                    // Axum handles Pong automatically
                    tracing::debug!("Ping received");
                }
                Message::Close(_) => {
                    tracing::info!("Client disconnected");
                    break;
                }
                _ => {}
            }
        }
    });

    // Wait for either task to finish
    tokio::select! {
        _ = &mut send_task => recv_task.abort(),
        _ = &mut recv_task => send_task.abort(),
    }
}
```

```rust
// src/state.rs - Broadcast channel for WebSocket
use tokio::sync::broadcast;

#[derive(Clone)]
pub struct AppState {
    pub db: PgPool,
    pub broadcast_tx: broadcast::Sender<String>,
}

impl AppState {
    pub async fn new(config: Config) -> anyhow::Result<Self> {
        let db = PgPool::connect(&config.database_url).await?;
        let (broadcast_tx, _) = broadcast::channel(100);

        Ok(Self { db, broadcast_tx })
    }
}
```

```rust
// src/routes/ws.rs
use axum::{Router, routing::get};

pub fn routes() -> Router<AppState> {
    Router::new()
        .route("/ws", get(ws_handler))
}
```

**Why**: Axum's WebSocket support is built on tokio-tungstenite[^15] but exposes a stable API
that won't break with internal updates. Use `socket.split()` to handle send and receive
concurrently in separate tasks.

### WebSocket with Authentication

Projects **SHOULD** authenticate WebSocket connections during upgrade:

```rust
use axum::extract::Query;

#[derive(Deserialize)]
pub struct WsQuery {
    token: String,
}

pub async fn authenticated_ws_handler(
    ws: WebSocketUpgrade,
    Query(query): Query<WsQuery>,
    State(state): State<AppState>,
) -> Result<Response, AppError> {
    // Verify token before upgrading
    let claims = verify_token(&state.jwt_keys, &query.token)?;

    Ok(ws.on_upgrade(move |socket| {
        handle_authenticated_socket(socket, state, claims.sub)
    }))
}
```

**Why**: WebSocket connections cannot use standard HTTP headers after the initial handshake. Pass
authentication tokens via query parameters during the upgrade request.

## Performance and Observability

### Structured Logging with Tracing

Projects **MUST** use tracing[^16] and tracing-subscriber[^17] for structured logging:

```rust
// src/main.rs
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt, EnvFilter};

fn init_tracing() {
    tracing_subscriber::registry()
        .with(EnvFilter::try_from_default_env().unwrap_or_else(|_| {
            "my_api=debug,tower_http=debug,axum=trace".into()
        }))
        .with(tracing_subscriber::fmt::layer().json())
        .init();
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    init_tracing();

    tracing::info!("Starting server");
    // ...
}
```

```rust
// src/handlers/users.rs - Instrumented handler
use tracing::instrument;

#[instrument(skip(state), fields(user_id = %id))]
pub async fn get_user(
    Path(id): Path<i64>,
    State(state): State<AppState>,
) -> Result<Json<User>, AppError> {
    tracing::debug!("Fetching user from database");

    let user = sqlx::query_as!(User, "SELECT * FROM users WHERE id = $1", id)
        .fetch_one(&state.db)
        .await?;

    tracing::info!(username = %user.username, "User retrieved successfully");
    Ok(Json(user))
}
```

**Why**: Tracing provides structured, contextual logging that integrates with async Rust. The
`#[instrument]` macro automatically creates spans with function arguments. JSON output enables
log aggregation in tools like Elasticsearch or Loki.

### HTTP Request Tracing

Projects **SHOULD** use tower-http's TraceLayer for request logging:

```rust
use tower_http::trace::{TraceLayer, DefaultMakeSpan, DefaultOnResponse};
use tracing::Level;

let app = Router::new()
    .nest("/api", api_routes())
    .layer(
        TraceLayer::new_for_http()
            .make_span_with(DefaultMakeSpan::new().level(Level::INFO))
            .on_response(DefaultOnResponse::new().level(Level::INFO))
    );
```

### Metrics with Prometheus

Projects **SHOULD** use axum-prometheus[^18] or metrics[^19] with
metrics-exporter-prometheus[^20] for metrics:

```rust
// Using axum-prometheus for automatic HTTP metrics
use axum_prometheus::PrometheusMetricLayer;

let (prometheus_layer, metric_handle) = PrometheusMetricLayer::pair();

let app = Router::new()
    .nest("/api", api_routes())
    .route("/metrics", get(|| async move { metric_handle.render() }))
    .layer(prometheus_layer);
```

```rust
// Custom metrics with metrics crate
use metrics::{counter, gauge, histogram};
use metrics_exporter_prometheus::PrometheusBuilder;

fn init_metrics() -> PrometheusHandle {
    PrometheusBuilder::new()
        .install_recorder()
        .expect("Failed to install Prometheus recorder")
}

// In handlers
pub async fn create_user(/* ... */) -> Result<Json<User>, AppError> {
    let start = std::time::Instant::now();

    // ... create user logic ...

    counter!("users_created_total").increment(1);
    histogram!("user_creation_duration_seconds").record(start.elapsed().as_secs_f64());

    Ok(Json(user))
}

// Track active connections
pub async fn ws_handler(ws: WebSocketUpgrade, /* ... */) -> Response {
    gauge!("websocket_connections_active").increment(1.0);

    ws.on_upgrade(|socket| async move {
        handle_socket(socket).await;
        gauge!("websocket_connections_active").decrement(1.0);
    })
}
```

**Why**: axum-prometheus provides automatic HTTP metrics (requests total, duration, pending) with
minimal configuration. The metrics crate offers a facade for custom metrics that can be exported
to various backends.

### OpenTelemetry Integration

For distributed tracing, projects **MAY** use tracing-opentelemetry[^21]:

```rust
use opentelemetry::global;
use opentelemetry_sdk::trace::TracerProvider;
use tracing_opentelemetry::OpenTelemetryLayer;

fn init_telemetry() -> anyhow::Result<()> {
    let exporter = opentelemetry_otlp::new_exporter()
        .tonic()
        .with_endpoint("http://localhost:4317");

    let provider = TracerProvider::builder()
        .with_batch_exporter(exporter.build_span_exporter()?, opentelemetry_sdk::runtime::Tokio)
        .build();

    global::set_tracer_provider(provider);

    let tracer = global::tracer("my-api");
    let telemetry_layer = OpenTelemetryLayer::new(tracer);

    tracing_subscriber::registry()
        .with(telemetry_layer)
        .with(tracing_subscriber::fmt::layer())
        .init();

    Ok(())
}
```

**Why**: OpenTelemetry enables distributed tracing across microservices with unique trace IDs,
essential for debugging request flows in distributed systems.

## Background Jobs

### Simple Background Tasks with tokio::spawn

For simple, fire-and-forget tasks, projects **SHOULD** use `tokio::spawn`:

```rust
pub async fn create_user(
    State(state): State<AppState>,
    Json(payload): Json<CreateUser>,
) -> Result<Json<User>, AppError> {
    let user = sqlx::query_as!(User, /* ... */)
        .fetch_one(&state.db)
        .await?;

    // Fire-and-forget email task
    let email_client = state.email_client.clone();
    let user_email = user.email.clone();
    tokio::spawn(async move {
        if let Err(e) = email_client.send_welcome_email(&user_email).await {
            tracing::error!(?e, "Failed to send welcome email");
        }
    });

    Ok(Json(user))
}
```

**Why**: `tokio::spawn` is ideal for simple background tasks that don't require persistence or
retry logic. For tasks that must survive restarts or need guaranteed delivery, use a job queue.

### Blocking Tasks with spawn_blocking

For CPU-intensive or blocking operations, projects **MUST** use `spawn_blocking`:

```rust
pub async fn hash_password(password: String) -> Result<String, AppError> {
    tokio::task::spawn_blocking(move || {
        password_auth::generate_hash(&password)
    })
    .await
    .map_err(|e| AppError::Internal(format!("Task failed: {}", e)))
}

pub async fn process_image(data: Vec<u8>) -> Result<Vec<u8>, AppError> {
    tokio::task::spawn_blocking(move || {
        // CPU-intensive image processing
        image::load_from_memory(&data)
            .map(|img| img.resize(800, 600, image::imageops::FilterType::Lanczos3))
            .map(|img| {
                let mut buf = Vec::new();
                img.write_to(&mut std::io::Cursor::new(&mut buf), image::ImageFormat::Jpeg)
                    .expect("Failed to encode");
                buf
            })
            .map_err(|e| AppError::Internal(e.to_string()))
    })
    .await
    .map_err(|e| AppError::Internal(format!("Task panicked: {}", e)))?
}
```

**Why**: Blocking the async runtime thread prevents other tasks from executing. `spawn_blocking`
runs blocking code on a dedicated thread pool, keeping the async runtime responsive.

### Job Queues with Apalis

For persistent, retriable background jobs, projects **SHOULD** use apalis[^22]:

```rust
// src/jobs/mod.rs
use apalis::prelude::*;
use apalis_redis::RedisStorage;
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct SendEmailJob {
    pub to: String,
    pub subject: String,
    pub body: String,
}

impl Job for SendEmailJob {
    const NAME: &'static str = "send_email";
}

async fn send_email_handler(job: SendEmailJob, ctx: JobContext) -> Result<(), Error> {
    tracing::info!(to = %job.to, subject = %job.subject, "Sending email");

    // Simulate email sending
    let email_client = ctx.data::<EmailClient>().unwrap();
    email_client
        .send(&job.to, &job.subject, &job.body)
        .await
        .map_err(|e| Error::Failed(e.into()))?;

    Ok(())
}

pub async fn start_worker(redis_url: &str, email_client: EmailClient) -> anyhow::Result<()> {
    let storage = RedisStorage::<SendEmailJob>::connect(redis_url).await?;

    Monitor::new()
        .register({
            WorkerBuilder::new("email-worker")
                .data(email_client)
                .backend(storage)
                .build_fn(send_email_handler)
        })
        .run()
        .await?;

    Ok(())
}

// Enqueue a job
pub async fn enqueue_email(
    storage: &RedisStorage<SendEmailJob>,
    job: SendEmailJob,
) -> anyhow::Result<()> {
    storage.push(job).await?;
    Ok(())
}
```

```rust
// Usage in handlers
pub async fn create_user(
    State(state): State<AppState>,
    Json(payload): Json<CreateUser>,
) -> Result<Json<User>, AppError> {
    let user = /* create user */;

    // Enqueue welcome email job (persisted, retriable)
    state.job_storage.push(SendEmailJob {
        to: user.email.clone(),
        subject: "Welcome!".into(),
        body: "Thanks for signing up.".into(),
    }).await?;

    Ok(Json(user))
}
```

**Why**: Apalis provides type-safe, Tower-based job processing with support for Redis, PostgreSQL,
and other backends. Jobs are persisted and can be retried on failure, with built-in concurrency
control and monitoring.

### Alternative: rusty-sidekiq

For interoperability with Ruby Sidekiq, projects **MAY** use rusty-sidekiq[^23]:

```rust
use sidekiq::{Job, Worker, RedisPool};
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Deserialize, Serialize)]
struct WelcomeEmailWorker {
    user_id: i64,
}

#[async_trait]
impl Worker<WelcomeEmailWorker> for WelcomeEmailWorker {
    async fn perform(&self, _args: WelcomeEmailWorker) -> Result<(), Box<dyn std::error::Error>> {
        // Send email
        Ok(())
    }
}

// Enqueue job (compatible with Ruby Sidekiq)
sidekiq::perform_async(
    &redis_pool,
    "WelcomeEmailWorker",
    WelcomeEmailWorker { user_id: 123 },
).await?;
```

**Why**: rusty-sidekiq is compatible with Ruby Sidekiq for mixed Ruby/Rust environments. Use
apalis for pure Rust applications.

## Caching

### In-Memory Caching with Moka

Projects **SHOULD** use moka[^24] for high-performance in-memory caching:

```rust
// src/cache.rs
use moka::future::Cache;
use std::time::Duration;

#[derive(Clone)]
pub struct AppCache {
    users: Cache<i64, User>,
    settings: Cache<String, String>,
}

impl AppCache {
    pub fn new() -> Self {
        Self {
            users: Cache::builder()
                .max_capacity(10_000)
                .time_to_live(Duration::from_secs(300))      // 5 min TTL
                .time_to_idle(Duration::from_secs(60))       // 1 min idle
                .build(),
            settings: Cache::builder()
                .max_capacity(1_000)
                .time_to_live(Duration::from_secs(3600))
                .build(),
        }
    }

    pub async fn get_user(&self, id: i64) -> Option<User> {
        self.users.get(&id).await
    }

    pub async fn set_user(&self, id: i64, user: User) {
        self.users.insert(id, user).await;
    }

    pub async fn invalidate_user(&self, id: i64) {
        self.users.invalidate(&id).await;
    }
}
```

```rust
// Cache-aside pattern in handlers
pub async fn get_user(
    Path(id): Path<i64>,
    State(state): State<AppState>,
) -> Result<Json<User>, AppError> {
    // Check cache first
    if let Some(user) = state.cache.get_user(id).await {
        tracing::debug!(user_id = id, "Cache hit");
        return Ok(Json(user));
    }

    tracing::debug!(user_id = id, "Cache miss");

    // Fetch from database
    let user = sqlx::query_as!(User, "SELECT * FROM users WHERE id = $1", id)
        .fetch_one(&state.db)
        .await?;

    // Populate cache
    state.cache.set_user(id, user.clone()).await;

    Ok(Json(user))
}
```

**Why**: Moka provides a concurrent, async-aware cache with LRU eviction, TTL/TTI expiration, and
excellent performance. It uses algorithms inspired by Caffeine (Java) for near-optimal hit
ratios.

### Distributed Caching with Redis

For distributed caching, projects **SHOULD** use redis-rs[^25] with deadpool-redis[^26]:

```rust
// src/redis.rs
use deadpool_redis::{Config, Pool, Runtime};
use redis::AsyncCommands;

pub async fn create_redis_pool(url: &str) -> anyhow::Result<Pool> {
    let cfg = Config::from_url(url);
    let pool = cfg.create_pool(Some(Runtime::Tokio1))?;
    Ok(pool)
}

#[derive(Clone)]
pub struct RedisCache {
    pool: Pool,
}

impl RedisCache {
    pub fn new(pool: Pool) -> Self {
        Self { pool }
    }

    pub async fn get<T: serde::de::DeserializeOwned>(&self, key: &str) -> Option<T> {
        let mut conn = self.pool.get().await.ok()?;
        let data: Option<String> = conn.get(key).await.ok()?;
        data.and_then(|s| serde_json::from_str(&s).ok())
    }

    pub async fn set<T: serde::Serialize>(
        &self,
        key: &str,
        value: &T,
        ttl_secs: u64,
    ) -> anyhow::Result<()> {
        let mut conn = self.pool.get().await?;
        let data = serde_json::to_string(value)?;
        conn.set_ex(key, data, ttl_secs).await?;
        Ok(())
    }

    pub async fn delete(&self, key: &str) -> anyhow::Result<()> {
        let mut conn = self.pool.get().await?;
        conn.del(key).await?;
        Ok(())
    }

    pub async fn set_nx<T: serde::Serialize>(
        &self,
        key: &str,
        value: &T,
        ttl_secs: u64,
    ) -> anyhow::Result<bool> {
        let mut conn = self.pool.get().await?;
        let data = serde_json::to_string(value)?;
        let result: bool = redis::cmd("SET")
            .arg(key)
            .arg(data)
            .arg("NX")
            .arg("EX")
            .arg(ttl_secs)
            .query_async(&mut *conn)
            .await?;
        Ok(result)
    }
}
```

**Why**: Redis provides distributed caching that survives application restarts and can be shared
across multiple instances. deadpool-redis offers an async connection pool optimized for Tokio.

### Multi-Level Caching

Projects **MAY** combine Moka (L1) and Redis (L2) for optimal performance:

```rust
pub async fn get_user_multilevel(
    id: i64,
    local_cache: &AppCache,
    redis_cache: &RedisCache,
    db: &PgPool,
) -> Result<User, AppError> {
    // L1: Local memory cache
    if let Some(user) = local_cache.get_user(id).await {
        return Ok(user);
    }

    // L2: Redis
    let redis_key = format!("user:{}", id);
    if let Some(user) = redis_cache.get::<User>(&redis_key).await {
        local_cache.set_user(id, user.clone()).await;
        return Ok(user);
    }

    // L3: Database
    let user = sqlx::query_as!(User, "SELECT * FROM users WHERE id = $1", id)
        .fetch_one(db)
        .await?;

    // Populate caches
    redis_cache.set(&redis_key, &user, 3600).await?;
    local_cache.set_user(id, user.clone()).await;

    Ok(user)
}
```

**Why**: Multi-level caching reduces latency (L1 is fastest) while maintaining consistency across
distributed instances (L2 provides shared state).

## Rate Limiting

### Rate Limiting with tower-governor

Projects **SHOULD** use tower-governor[^27] for rate limiting:

```rust
// src/middleware/rate_limit.rs
use tower_governor::{
    governor::GovernorConfigBuilder,
    key_extractor::{SmartIpKeyExtractor, KeyExtractor},
    GovernorLayer,
};
use std::time::Duration;

/// Create a rate limiter: 10 requests per second with burst of 30
pub fn create_rate_limiter() -> GovernorLayer<SmartIpKeyExtractor, NoOpMiddleware> {
    let config = GovernorConfigBuilder::default()
        .per_second(10)
        .burst_size(30)
        .finish()
        .expect("Failed to build governor config");

    GovernorLayer {
        config: Box::new(config),
    }
}

/// Create a stricter rate limiter for sensitive endpoints
pub fn create_auth_rate_limiter() -> GovernorLayer<SmartIpKeyExtractor, NoOpMiddleware> {
    let config = GovernorConfigBuilder::default()
        .per_second(1)
        .burst_size(5)
        .finish()
        .expect("Failed to build governor config");

    GovernorLayer {
        config: Box::new(config),
    }
}
```

```rust
// src/app.rs - Apply rate limiting
use axum::extract::connect_info::ConnectInfo;
use std::net::SocketAddr;

pub async fn create_app(config: Config) -> anyhow::Result<Router> {
    let state = AppState::new(config).await?;

    let api_routes = Router::new()
        .nest("/users", users::routes())
        .layer(create_rate_limiter());

    let auth_routes = Router::new()
        .route("/login", post(login))
        .route("/register", post(register))
        .layer(create_auth_rate_limiter());

    let app = Router::new()
        .nest("/api", api_routes)
        .nest("/auth", auth_routes)
        .with_state(state);

    Ok(app)
}

// IMPORTANT: Use into_make_service_with_connect_info for IP extraction
let listener = tokio::net::TcpListener::bind(&addr).await?;
axum::serve(
    listener,
    app.into_make_service_with_connect_info::<SocketAddr>(),
).await?;
```

**Why**: tower-governor uses the GCRA (Generic Cell Rate Algorithm) for fair, efficient rate
limiting. The `SmartIpKeyExtractor` handles common proxy headers (X-Forwarded-For, X-Real-IP)
for accurate client identification.

### Custom Rate Limiting Key

For user-based rate limiting, projects **MAY** implement custom key extractors:

```rust
use tower_governor::key_extractor::KeyExtractor;
use axum::http::Request;

#[derive(Clone)]
pub struct UserKeyExtractor;

impl KeyExtractor for UserKeyExtractor {
    type Key = String;

    fn extract<B>(&self, req: &Request<B>) -> Result<Self::Key, GovernorError> {
        req.headers()
            .get("x-user-id")
            .and_then(|v| v.to_str().ok())
            .map(|s| s.to_string())
            .ok_or(GovernorError::UnableToExtractKey)
    }
}
```

**Why**: Custom key extractors enable rate limiting by user ID, API key, or other identifiers
beyond IP address.

## Circuit Breakers

### Circuit Breaker with Recloser

Projects **SHOULD** use recloser[^28] for circuit breaker patterns:

```rust
// src/resilience.rs
use recloser::{AsyncRecloser, Recloser};
use std::time::Duration;

#[derive(Clone)]
pub struct ResilientClient {
    http_client: reqwest::Client,
    circuit_breaker: AsyncRecloser,
}

impl ResilientClient {
    pub fn new() -> Self {
        // Circuit breaker: 50% failure threshold, 10 sample size, 30s recovery
        let recloser = Recloser::custom()
            .error_rate(0.5)
            .closed_len(10)
            .half_open_len(5)
            .open_wait(Duration::from_secs(30))
            .build();

        Self {
            http_client: reqwest::Client::new(),
            circuit_breaker: recloser.into(),
        }
    }

    pub async fn call_external_api(&self, url: &str) -> Result<String, AppError> {
        self.circuit_breaker
            .call(async {
                let response = self
                    .http_client
                    .get(url)
                    .timeout(Duration::from_secs(5))
                    .send()
                    .await
                    .map_err(|e| AppError::External(e.to_string()))?;

                response
                    .text()
                    .await
                    .map_err(|e| AppError::External(e.to_string()))
            })
            .await
            .map_err(|e| match e {
                recloser::Error::Rejected => {
                    AppError::ServiceUnavailable("Circuit breaker open".into())
                }
                recloser::Error::Inner(e) => e,
            })
    }
}
```

**Why**: Circuit breakers prevent cascading failures by temporarily rejecting requests to failing
services. Recloser uses a ring buffer for efficient failure tracking with configurable
thresholds.

### Alternative: failsafe-rs

For more sophisticated failure policies, projects **MAY** use failsafe-rs[^29]:

```rust
use failsafe::{Config, CircuitBreaker, Error};
use std::time::Duration;

fn create_circuit_breaker() -> CircuitBreaker<impl failsafe::backoff::Backoff> {
    Config::new()
        .failure_policy(failsafe::failure_policy::consecutive_failures(5))
        .success_policy(failsafe::success_policy::consecutive_successes(2))
        .build()
}

async fn call_with_failsafe<F, T, E>(
    cb: &CircuitBreaker<impl failsafe::backoff::Backoff>,
    f: F,
) -> Result<T, Error<E>>
where
    F: Future<Output = Result<T, E>>,
{
    cb.call(f).await
}
```

**Why**: failsafe-rs provides more configurable failure/success policies and backoff strategies
for complex resilience requirements.

## Feature Flags

### Runtime Feature Flags with Unleash

Projects **SHOULD** use unleash-api-client[^30] for runtime feature flags:

```rust
// src/features.rs
use unleash_api_client::{client::ClientBuilder, Client};
use std::sync::Arc;

pub type FeatureClient = Arc<Client>;

pub async fn create_feature_client(
    api_url: &str,
    api_key: &str,
    app_name: &str,
) -> anyhow::Result<FeatureClient> {
    let client = ClientBuilder::default()
        .api_url(api_url)
        .api_key(api_key)
        .app_name(app_name)
        .instance_id(uuid::Uuid::new_v4().to_string())
        .build()
        .await?;

    // Start background polling
    client.start().await?;

    Ok(Arc::new(client))
}

// Check feature flag
pub fn is_enabled(client: &FeatureClient, feature: &str) -> bool {
    client.is_enabled(feature, None, false)
}

// Check with context (for gradual rollouts, A/B tests)
pub fn is_enabled_for_user(client: &FeatureClient, feature: &str, user_id: &str) -> bool {
    let context = unleash_api_client::context::Context {
        user_id: Some(user_id.to_string()),
        ..Default::default()
    };
    client.is_enabled(feature, Some(&context), false)
}
```

```rust
// Usage in handlers
pub async fn get_dashboard(
    State(state): State<AppState>,
    auth: JwtAuth,
) -> Result<Json<Dashboard>, AppError> {
    let dashboard = if is_enabled_for_user(&state.features, "new_dashboard", &auth.user_id) {
        build_new_dashboard(&state, &auth.user_id).await?
    } else {
        build_legacy_dashboard(&state, &auth.user_id).await?
    };

    Ok(Json(dashboard))
}
```

**Why**: Unleash provides runtime feature toggles with gradual rollouts, A/B testing, and user
targeting. Features can be enabled/disabled without code deployments.

### Simple Feature Flags

For simpler needs, projects **MAY** use environment-based feature flags:

```rust
// src/config.rs
use std::env;

#[derive(Clone)]
pub struct Features {
    pub new_dashboard: bool,
    pub beta_api: bool,
    pub maintenance_mode: bool,
}

impl Features {
    pub fn from_env() -> Self {
        Self {
            new_dashboard: env::var("FEATURE_NEW_DASHBOARD")
                .map(|v| v == "true")
                .unwrap_or(false),
            beta_api: env::var("FEATURE_BETA_API")
                .map(|v| v == "true")
                .unwrap_or(false),
            maintenance_mode: env::var("FEATURE_MAINTENANCE")
                .map(|v| v == "true")
                .unwrap_or(false),
        }
    }
}
```

**Why**: Environment-based flags work for simple on/off features that change with deployments.
Use Unleash for runtime toggles without redeployment.

## Graceful Shutdown

Projects **MUST** implement graceful shutdown to handle in-flight requests during deployments.

### Why Graceful Shutdown

- **Zero downtime deployments**: Complete in-flight requests before terminating
- **Data integrity**: Allow transactions to complete, preventing data corruption
- **Connection cleanup**: Properly close database connections and external resources
- **Kubernetes readiness**: Required for proper pod lifecycle management

### Basic Graceful Shutdown

```rust
// src/main.rs
use tokio::signal;
use std::net::SocketAddr;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let config = Config::from_env()?;
    let app = create_app(config.clone()).await?;

    let addr: SocketAddr = config.addr.parse()?;
    let listener = tokio::net::TcpListener::bind(addr).await?;

    tracing::info!("Server listening on {}", addr);

    axum::serve(listener, app)
        .with_graceful_shutdown(shutdown_signal())
        .await?;

    tracing::info!("Server shutdown complete");
    Ok(())
}

async fn shutdown_signal() {
    let ctrl_c = async {
        signal::ctrl_c()
            .await
            .expect("Failed to install Ctrl+C handler");
    };

    #[cfg(unix)]
    let terminate = async {
        signal::unix::signal(signal::unix::SignalKind::terminate())
            .expect("Failed to install SIGTERM handler")
            .recv()
            .await;
    };

    #[cfg(not(unix))]
    let terminate = std::future::pending::<()>();

    tokio::select! {
        _ = ctrl_c => {
            tracing::info!("Received Ctrl+C, initiating graceful shutdown");
        }
        _ = terminate => {
            tracing::info!("Received SIGTERM, initiating graceful shutdown");
        }
    }
}
```

### Shutdown with Resource Cleanup

```rust
// src/main.rs
use std::sync::Arc;
use tokio::sync::broadcast;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let config = Config::from_env()?;

    // Create shutdown channel
    let (shutdown_tx, _) = broadcast::channel::<()>(1);
    let shutdown_rx = shutdown_tx.subscribe();

    // Initialize resources
    let db = PgPool::connect(&config.database_url).await?;
    let redis = create_redis_pool(&config.redis_url).await?;

    let state = AppState {
        db: db.clone(),
        redis: redis.clone(),
        shutdown: shutdown_tx.clone(),
    };

    let app = create_app(state).await?;

    let listener = tokio::net::TcpListener::bind(&config.addr).await?;

    // Spawn server
    let server_handle = tokio::spawn(async move {
        axum::serve(listener, app)
            .with_graceful_shutdown(async move {
                let mut rx = shutdown_rx;
                let _ = rx.recv().await;
            })
            .await
    });

    // Wait for shutdown signal
    shutdown_signal().await;

    // Notify all components
    let _ = shutdown_tx.send(());

    // Wait for server to finish
    let _ = server_handle.await;

    // Cleanup resources
    tracing::info!("Closing database connections...");
    db.close().await;

    tracing::info!("Shutdown complete");
    Ok(())
}
```

### Kubernetes Health Probes with Shutdown

```rust
// src/routes/health.rs
use axum::{extract::State, http::StatusCode, routing::get, Router};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;

pub struct HealthState {
    pub ready: AtomicBool,
    pub live: AtomicBool,
}

impl HealthState {
    pub fn new() -> Arc<Self> {
        Arc::new(Self {
            ready: AtomicBool::new(true),
            live: AtomicBool::new(true),
        })
    }

    pub fn start_shutdown(&self) {
        self.ready.store(false, Ordering::SeqCst);
    }
}

pub fn routes() -> Router<AppState> {
    Router::new()
        .route("/health/live", get(liveness))
        .route("/health/ready", get(readiness))
}

async fn liveness(State(state): State<AppState>) -> StatusCode {
    if state.health.live.load(Ordering::SeqCst) {
        StatusCode::OK
    } else {
        StatusCode::SERVICE_UNAVAILABLE
    }
}

async fn readiness(State(state): State<AppState>) -> StatusCode {
    if state.health.ready.load(Ordering::SeqCst) {
        StatusCode::OK
    } else {
        StatusCode::SERVICE_UNAVAILABLE
    }
}
```

```rust
// src/main.rs - Integration with shutdown
async fn shutdown_signal(health: Arc<HealthState>) {
    let ctrl_c = signal::ctrl_c();
    let terminate = signal::unix::signal(signal::unix::SignalKind::terminate())
        .expect("Failed to install SIGTERM handler");

    tokio::select! {
        _ = ctrl_c => {},
        _ = terminate.recv() => {},
    }

    tracing::info!("Shutdown signal received, marking as not ready");
    health.start_shutdown();

    // Wait for load balancer to drain connections (k8s terminationGracePeriodSeconds)
    tokio::time::sleep(Duration::from_secs(5)).await;
}
```

### Draining Connections

```rust
// src/main.rs
use std::time::Duration;

async fn graceful_shutdown(
    health: Arc<HealthState>,
    drain_timeout: Duration,
) {
    shutdown_signal(health.clone()).await;

    tracing::info!("Starting connection drain ({:?})...", drain_timeout);

    // Mark as not ready (stops receiving new connections from LB)
    health.start_shutdown();

    // Wait for in-flight requests to complete
    tokio::time::sleep(drain_timeout).await;

    tracing::info!("Connection drain complete");
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let health = HealthState::new();
    let drain_timeout = Duration::from_secs(30);

    let app = create_app(state).await?;

    axum::serve(listener, app)
        .with_graceful_shutdown(graceful_shutdown(health, drain_timeout))
        .await?;

    Ok(())
}
```

**Why**: Graceful shutdown ensures zero-downtime deployments by completing in-flight requests
before terminating. The readiness probe integration ensures load balancers stop sending new
traffic before the server shuts down.

## OpenAPI Documentation

Projects **SHOULD** generate OpenAPI specifications from code using utoipa[^31].

### Why OpenAPI

- **API documentation**: Auto-generate interactive API docs (Swagger UI, ReDoc)
- **Client generation**: Generate type-safe clients in any language
- **Contract-first**: Define API contracts for frontend/mobile teams
- **Testing**: Use OpenAPI specs for automated API testing

### utoipa Setup

```toml
# Cargo.toml
[dependencies]
utoipa = { version = "5", features = ["axum_extras"] }
utoipa-swagger-ui = { version = "8", features = ["axum"] }
utoipa-redoc = { version = "5", features = ["axum"] }
```

### Documenting Handlers

```rust
// src/handlers/users.rs
use axum::{extract::Path, Json};
use utoipa::ToSchema;
use utoipa::OpenApi;

#[derive(ToSchema, serde::Serialize)]
pub struct User {
    /// Unique identifier
    #[schema(example = 1)]
    pub id: i64,
    /// User's email address
    #[schema(example = "alice@example.com")]
    pub email: String,
    /// Display name
    #[schema(example = "Alice Smith")]
    pub name: String,
}

#[derive(ToSchema, serde::Deserialize)]
pub struct CreateUserRequest {
    /// User's email address
    #[schema(example = "alice@example.com")]
    pub email: String,
    /// Display name
    #[schema(example = "Alice Smith")]
    pub name: String,
    /// Password (min 8 characters)
    #[schema(example = "password123", min_length = 8)]
    pub password: String,
}

/// List all users
#[utoipa::path(
    get,
    path = "/api/users",
    tag = "users",
    responses(
        (status = 200, description = "List of users", body = Vec<User>),
        (status = 401, description = "Unauthorized"),
    ),
    security(("bearer_token" = []))
)]
pub async fn list_users(
    State(state): State<AppState>,
) -> Result<Json<Vec<User>>, AppError> {
    let users = state.db.get_all_users().await?;
    Ok(Json(users))
}

/// Get a user by ID
#[utoipa::path(
    get,
    path = "/api/users/{id}",
    tag = "users",
    params(
        ("id" = i64, Path, description = "User ID")
    ),
    responses(
        (status = 200, description = "User found", body = User),
        (status = 404, description = "User not found"),
    ),
)]
pub async fn get_user(
    Path(id): Path<i64>,
    State(state): State<AppState>,
) -> Result<Json<User>, AppError> {
    let user = state.db.get_user(id).await?;
    Ok(Json(user))
}

/// Create a new user
#[utoipa::path(
    post,
    path = "/api/users",
    tag = "users",
    request_body = CreateUserRequest,
    responses(
        (status = 201, description = "User created", body = User),
        (status = 400, description = "Validation error"),
        (status = 409, description = "Email already exists"),
    ),
)]
pub async fn create_user(
    State(state): State<AppState>,
    Json(payload): Json<CreateUserRequest>,
) -> Result<(StatusCode, Json<User>), AppError> {
    let user = state.db.create_user(payload).await?;
    Ok((StatusCode::CREATED, Json(user)))
}
```

### OpenAPI Specification

```rust
// src/openapi.rs
use utoipa::OpenApi;

#[derive(OpenApi)]
#[openapi(
    info(
        title = "My API",
        version = "1.0.0",
        description = "REST API for My Application",
        license(name = "MIT", url = "https://opensource.org/licenses/MIT"),
        contact(name = "API Support", email = "support@example.com")
    ),
    servers(
        (url = "https://api.example.com", description = "Production"),
        (url = "http://localhost:3000", description = "Development")
    ),
    paths(
        crate::handlers::users::list_users,
        crate::handlers::users::get_user,
        crate::handlers::users::create_user,
    ),
    components(
        schemas(
            crate::handlers::users::User,
            crate::handlers::users::CreateUserRequest,
        )
    ),
    modifiers(&SecurityAddon),
    tags(
        (name = "users", description = "User management endpoints"),
        (name = "health", description = "Health check endpoints")
    )
)]
pub struct ApiDoc;

struct SecurityAddon;

impl utoipa::Modify for SecurityAddon {
    fn modify(&self, openapi: &mut utoipa::openapi::OpenApi) {
        if let Some(components) = openapi.components.as_mut() {
            components.add_security_scheme(
                "bearer_token",
                utoipa::openapi::security::SecurityScheme::Http(
                    utoipa::openapi::security::Http::new(
                        utoipa::openapi::security::HttpAuthScheme::Bearer
                    )
                ),
            );
        }
    }
}
```

### Serving API Documentation

```rust
// src/app.rs
use utoipa::OpenApi;
use utoipa_swagger_ui::SwaggerUi;
use utoipa_redoc::{Redoc, Servable};

pub async fn create_app(config: Config) -> anyhow::Result<Router> {
    let state = AppState::new(config).await?;

    let app = Router::new()
        .merge(health::routes())
        .nest("/api", api_routes())
        // Swagger UI at /swagger-ui
        .merge(SwaggerUi::new("/swagger-ui")
            .url("/api-docs/openapi.json", ApiDoc::openapi()))
        // ReDoc at /redoc
        .merge(Redoc::with_url("/redoc", ApiDoc::openapi()))
        // Raw OpenAPI JSON
        .route("/api-docs/openapi.json", get(|| async {
            Json(ApiDoc::openapi())
        }))
        .with_state(state);

    Ok(app)
}
```

### Error Response Schemas

```rust
// src/error.rs
use utoipa::ToSchema;

#[derive(ToSchema, serde::Serialize)]
pub struct ErrorResponse {
    /// Error message
    #[schema(example = "Resource not found")]
    pub error: String,
    /// Error code for programmatic handling
    #[schema(example = "NOT_FOUND")]
    pub code: Option<String>,
}

// Use in handler documentation
#[utoipa::path(
    get,
    path = "/api/users/{id}",
    responses(
        (status = 200, description = "Success", body = User),
        (status = 404, description = "Not found", body = ErrorResponse),
        (status = 500, description = "Internal error", body = ErrorResponse),
    ),
)]
pub async fn get_user(/* ... */) { /* ... */ }
```

### Conditional Documentation

```rust
// src/main.rs
use std::env;

pub async fn create_app(config: Config) -> anyhow::Result<Router> {
    let mut app = Router::new()
        .nest("/api", api_routes())
        .with_state(state);

    // Only expose docs in non-production
    if env::var("ENVIRONMENT").unwrap_or_default() != "production" {
        app = app
            .merge(SwaggerUi::new("/swagger-ui")
                .url("/api-docs/openapi.json", ApiDoc::openapi()))
            .merge(Redoc::with_url("/redoc", ApiDoc::openapi()));
    }

    Ok(app)
}
```

**Why**: utoipa provides compile-time OpenAPI spec generation from Rust types and handler
annotations. This keeps documentation in sync with code and catches mismatches at compile time.

## See Also

- [Rust Style Guide](../languages/rust.md) - Language-level Rust conventions
- [Testing Guide](../process/testing.md) - General testing principles and patterns
- [CI Guide](../process/ci.md) - Continuous integration best practices

## References

[^1]: [Axum](https://github.com/tokio-rs/axum) - Ergonomic and modular web framework built with Tokio, Tower, and Hyper

[^2]: [Tower](https://github.com/tower-rs/tower) - Modular and reusable components for building robust networking clients and servers

[^3]: [Hyper](https://hyper.rs/) - Fast and safe HTTP implementation for Rust

[^4]: [Axum Performance](https://www.techempower.com/benchmarks/#section=data-r21) - TechEmpower benchmarks showing Axum's performance

[^5]: [Actix-web](https://actix.rs/) - Powerful, pragmatic, and extremely fast web framework for Rust

[^6]: [Rocket](https://rocket.rs/) - Web framework for Rust with focus on ease-of-use, expressiveness, and speed

[^7]: [thiserror](https://github.com/dtolnay/thiserror) - Derive macros for the standard library's `std::error::Error` trait

[^8]: [anyhow](https://github.com/dtolnay/anyhow) - Flexible concrete Error type built on `std::error::Error`

[^9]: [SQLx](https://github.com/launchbadge/sqlx) - Async, pure Rust SQL crate with compile-time checked queries

[^10]: [axum-login](https://github.com/maxcountryman/axum-login) - User identification, authentication, and authorization for Axum

[^11]: [jsonwebtoken](https://github.com/Keats/jsonwebtoken) - JWT library for Rust with support for all standard algorithms

[^12]: [casbin-rs](https://github.com/casbin/casbin-rs) - Authorization library supporting ACL, RBAC, ABAC models

[^13]: [tower-http](https://github.com/tower-rs/tower-http) - HTTP-specific Tower middleware including auth, compression, and tracing

[^14]: [Axum WebSocket](https://docs.rs/axum/latest/axum/extract/ws/index.html) - Native WebSocket support in Axum

[^15]: [tokio-tungstenite](https://github.com/snapview/tokio-tungstenite) - Tokio bindings for the Tungstenite WebSocket library

[^16]: [tracing](https://github.com/tokio-rs/tracing) - Application-level tracing for Rust with structured, contextual logging

[^17]: [tracing-subscriber](https://docs.rs/tracing-subscriber) - Utilities for implementing and composing tracing subscribers

[^18]: [axum-prometheus](https://lib.rs/crates/axum-prometheus) - Prometheus metrics middleware for Axum

[^19]: [metrics](https://github.com/metrics-rs/metrics) - High-quality, batteries-included metrics library for Rust

[^20]: [metrics-exporter-prometheus](https://docs.rs/metrics-exporter-prometheus) - Prometheus exporter for the metrics crate

[^21]: [tracing-opentelemetry](https://docs.rs/tracing-opentelemetry) - OpenTelemetry integration for tracing

[^22]: [apalis](https://github.com/geofmureithi/apalis) - Type-safe, extensible background job processing library for Rust

[^23]: [rusty-sidekiq](https://github.com/film42/sidekiq-rs) - Sidekiq-compatible job processing for Rust

[^24]: [moka](https://github.com/moka-rs/moka) - High-performance concurrent caching library for Rust

[^25]: [redis-rs](https://github.com/redis-rs/redis-rs) - Redis client library for Rust

[^26]: [deadpool-redis](https://docs.rs/deadpool-redis) - Async Redis connection pool for Tokio

[^27]: [tower-governor](https://github.com/benwis/tower-governor) - Rate limiting middleware for Tower/Axum using the governor crate

[^28]: [recloser](https://github.com/lerouxrgd/recloser) - Concurrent circuit breaker implemented with ring buffers

[^29]: [failsafe-rs](https://github.com/dmexe/failsafe-rs) - Circuit breaker implementation with configurable failure policies

[^30]: [unleash-api-client](https://github.com/Unleash/unleash-rust-sdk) - Unleash feature flag client SDK for Rust

[^31]: [utoipa](https://github.com/juhaku/utoipa) - Auto-generate OpenAPI documentation from Rust code with compile-time validation
