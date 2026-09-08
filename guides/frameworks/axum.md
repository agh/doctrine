# Axum Style Guide

> [Doctrine](../../README.md) > [Frameworks](README.md) > Axum

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in
BCP 14 [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119)
[RFC 8174](https://datatracker.ietf.org/doc/html/rfc8174) when, and only
when, they appear in all capitals, as shown here.

Extends [Rust style guide](../languages/rust.md) with Axum-specific conventions.

**Target Version**: Axum 0.8.9 on the Rust 2024 edition, checked against Rust
1.98.1. Everything in the [Rust style guide](../languages/rust.md) applies
unchanged — formatting, linting, test invocation, error-type design and general
SQLx usage all live there. This guide adds only what Axum changes.

## Quick Reference

| Task | Tool | Command/Crate |
| ---- | ---- | ------------- |
| Test API | tower::ServiceExt | See [Testing](#testing) |
| Auth (sessions) | axum-login | See [Security](#security) |
| Auth (JWT) | jsonwebtoken | See [Security](#security) |
| Authorization | casbin-rs | See [Security](#security) |
| WebSocket | axum::extract::ws | See [WebSocket](#websocket) |
| Request tracing | tower-http TraceLayer | See [Observability](#performance-and-observability) |
| Metrics | axum-prometheus | See [Observability](#performance-and-observability) |
| Background Jobs | apalis | See [Background Jobs](#background-jobs) |
| In-Memory Cache | moka | See [Caching](#caching) |
| Distributed Cache | redis-rs + deadpool | See [Caching](#caching) |
| Rate Limiting | tower-governor | See [Rate Limiting](#rate-limiting) |
| Circuit Breaker | recloser | See [Circuit Breakers](#circuit-breakers) |
| Feature Flags | unleash-api-client | See [Feature Flags](#feature-flags) |

**Why**: `cargo fmt`, `cargo clippy`, `cargo test` and `cargo sqlx prepare` are
language-level tooling, specified once in the [Rust style
guide](../languages/rust.md#formatting-rustfmt). Restating them here creates two
places to update and two chances to drift apart.

## Dependencies

Projects **MUST** pin the crates below, and **MUST** enable exactly the features
the examples in this guide use. Every example in this guide was compiled against
this set on Rust 1.98.1.

```toml
# Cargo.toml
[package]
edition = "2024"
rust-version = "1.88"

[dependencies]
# Core HTTP
axum = { version = "0.8.9", features = ["ws", "macros"] }
axum-extra = { version = "0.12.6", features = ["typed-header"] }
tower = { version = "0.5.3", features = ["util"] }
tower-http = { version = "0.7.1", features = [
    "trace", "cors", "compression-full", "limit",
    "sensitive-headers", "request-id", "timeout",
] }
tokio = { version = "1.53.1", features = ["full"] }
tokio-util = { version = "0.7.19", features = ["rt"] }
futures-util = "0.3.34"

# Serialisation
serde = { version = "1.0.229", features = ["derive"] }
serde_json = "1.0.151"

# Errors
thiserror = "2.0.20"
anyhow = "1.0.104"

# Database. See the pinning note below before changing this.
sqlx = { version = "0.8.6", features = [
    "runtime-tokio", "tls-rustls-ring", "postgres", "chrono", "macros", "migrate",
] }

# Authentication and authorisation
axum-login = "0.18.0"
tower-sessions = "0.14.0"
tower-sessions-sqlx-store = { version = "0.15.0", features = ["postgres"] }
password-auth = "1.0.0"
jsonwebtoken = { version = "11.0.0", features = ["rust_crypto"] }
rsa = { version = "0.9.10", features = ["pem"] }
casbin = "2.20.0"

# Rate limiting
tower_governor = "0.8.0"
governor = "0.10.4"

# Caching
moka = { version = "0.12.16", features = ["future"] }
deadpool-redis = "0.23.1"

# OpenAPI
utoipa = { version = "5.5.0", features = ["axum_extras"] }
utoipa-swagger-ui = { version = "9.0.2", features = ["axum"] }
utoipa-redoc = { version = "6.0.0", features = ["axum"] }

# Observability
tracing = "0.1.44"
tracing-subscriber = { version = "0.3.23", features = ["env-filter", "json"] }
time = "0.3.55"
uuid = { version = "1.26.0", features = ["v4"] }
chrono = { version = "0.4.45", features = ["serde"] }

[dev-dependencies]
tokio = { version = "1.53.1", features = ["full", "test-util"] }
```

Sections with their own runtimes pin separately, because they pull independent
dependency trees:

| Section | Crates |
| ------- | ------ |
| [OpenTelemetry](#opentelemetry-integration) | `opentelemetry` 0.32.0, `opentelemetry_sdk` 0.32.1, `opentelemetry-otlp` 0.32.0, `tracing-opentelemetry` 0.33.0 |
| [Background jobs](#job-queues-with-apalis) | `apalis` 0.7.4, `apalis-redis` 0.7.4, `rusty-sidekiq` 0.14.2, `async-trait` 0.1.92 |
| [Circuit breakers](#circuit-breakers) | `recloser` 1.4.0, `failsafe` 1.3.0, `reqwest` 0.13.4 |
| [Feature flags](#feature-flags) | `unleash-api-client` 0.17.1 (feature `reqwest-client-rustls`), `enum-map` 2 |

### Why the SQLx pin is 0.8, not 0.9

SQLx 0.9.0 is the current release, but `tower-sessions-sqlx-store` 0.15.0 — the
newest release — links `sqlx` 0.8. Cargo compiles both majors side by side and
treats their `PgPool` types as unrelated, so handing the application pool to the
session store fails to compile:

```text
error[E0308]: mismatched types
   |     let store = PostgresStore::new(db);
   |                 ------------------ ^^ expected `Pool<Postgres>`,
   |                                       found `sqlx::Pool<sqlx::Postgres>`
note: there are multiple different versions of crate `sqlx_core` in the
      dependency graph
```

Pin the whole project to SQLx 0.8.6 while sharing a pool with the session store.
Projects that need SQLx 0.9 **MUST** use a session store that does not take an
`sqlx` pool, and **MUST NOT** try to bridge the two majors.

**Why**: More than thirty crates appear across this guide. Without one pinned
manifest a reader has to guess a version and a feature set for each, and the
common failures — a missing `ws` feature, a `TypedHeader` that will not resolve,
two SQLx majors in one graph — surface as opaque trait errors rather than as a
missing dependency. Features are listed explicitly rather than left to
`default`, so the build does not silently grow a TLS stack or a compression
codec nobody asked for.

## Why Axum?

Axum[^1] is a web framework built on Tower[^2] and Hyper[^3], designed
for the Tokio ecosystem with focus on type safety and ergonomics.

**Key advantages**:

- Native async/await with Tokio runtime integration
- Type-safe extractors with compile-time guarantees
- Ergonomic routing with minimal boilerplate
- Composable middleware via Tower
- Zero-cost abstractions with excellent performance[^4]

**When to use Axum**: Axum suits async Rust services that already sit in the
Tokio ecosystem and want their middleware to be ordinary Tower layers.

Choose between Axum, Actix-web[^5] and Rocket[^6] on criteria you can check
against your own workload:

| Criterion | Favours |
| --------- | ------- |
| The service already uses Tokio, Hyper, Tower or tonic | Axum — same runtime, same middleware, no bridging |
| Middleware must be shared with non-HTTP services (gRPC, queues) | Axum — Tower layers are transport-agnostic |
| The team wants routing and guards expressed as attribute macros | Rocket — `#[get]`, `#[launch]` and typed request guards |
| An actor model fits the domain | Actix-web — actor supervision is native |
| Latency and throughput must meet a stated budget | Whichever wins **your** benchmark against **your** payloads |

Rocket 0.5 is not a synchronous framework: launching "starts a multi-threaded
asynchronous server and dispatches requests to matching routes as they
arrive"[^6].

**Why**: Absolute rankings do not survive contact with a real workload. Public
suites measure a fixed set of synthetic endpoints on fixed hardware; the
TechEmpower project that this guide once cited published its final results as
Round 23 in March 2025 and archived the repository, so its numbers no longer
track any current release[^4]. Ecosystem fit and operational constraints, which
are checkable today, are better selection criteria than a number that was true
of a different version on someone else's machine.

## Project Structure

Projects **SHOULD** organise code by feature, so that everything one endpoint
needs is in one directory:

```text
my-api/
├── src/
│   ├── main.rs                # Application entry point
│   ├── app.rs                 # App factory and router assembly
│   ├── lib.rs
│   ├── features/
│   │   ├── mod.rs
│   │   ├── users/
│   │   │   ├── mod.rs         # Re-exports; nothing else
│   │   │   ├── routes.rs      # Router<AppState> for /users
│   │   │   ├── handlers.rs    # Handlers for those routes
│   │   │   ├── model.rs       # User, CreateUser, queries
│   │   │   └── tests.rs       # Unit tests for this feature
│   │   └── health/
│   │       ├── mod.rs
│   │       ├── routes.rs
│   │       └── handlers.rs
│   └── shared/                # Only what more than one feature uses
│       ├── mod.rs
│       ├── config.rs          # Configuration via environment
│       ├── error.rs           # AppError and IntoResponse
│       ├── state.rs           # AppState
│       ├── middleware.rs      # Cross-cutting layers
│       └── ...                # jwt.rs, authz.rs, cache.rs, telemetry.rs, ...
├── migrations/
├── tests/                     # Integration tests across features
├── Cargo.toml
└── .env
```

**Do**:

```text
src/features/users/{routes,handlers,model}.rs   # one feature, one directory
```

**Don't**:

```text
src/routes/users.rs
src/handlers/users.rs      # the same feature spread across three trees
src/models/user.rs
```

```rust
// src/main.rs
use my_api::app::create_app;
use my_api::shared::config::Config;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let config = Config::from_env()?;
    let app = create_app(config.clone()).await?;

    let listener = tokio::net::TcpListener::bind(&config.addr).await?;
    axum::serve(listener, app).await?;

    Ok(())
}
```

**Why**: Adding an endpoint under the layered tree touches `routes/`,
`handlers/`, `models/` and `tests/`, so every feature branch collides with every
other feature branch in the same four `mod.rs` files. Under the feature tree the
same change touches one directory, deleting a feature is `rm -r`, and the
compiler enforces the boundary: anything a feature needs from outside must be
imported from `shared/`, which makes accidental coupling visible in the import
list. Keeping app creation in `app.rs` separate from `main.rs` is what lets
tests build the router with a different configuration.

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
// src/features/users/routes.rs
use axum::{Router, routing::{get, post}};
use crate::handlers::users;
use crate::state::AppState;

pub fn routes() -> Router<AppState> {
    Router::new()
        .route("/", get(users::list).post(users::create))
        .route("/{id}", get(users::get).put(users::update).delete(users::delete))
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

### Path Parameter Syntax

Route paths **MUST** use the braced capture syntax: `{name}` for a single
segment and `{*name}` for a trailing wildcard.

**Do**:

```rust
Router::new()
    .route("/users/{id}", get(get_user))
    .route("/assets/{*path}", get(serve_asset))
```

**Don't**:

```rust
Router::new()
    .route("/users/:id", get(get_user))    // Axum 0.7 syntax
    .route("/assets/*path", get(serve_asset))
```

**Why**: Axum 0.8 replaced the `:param` and `*wildcard` spellings from 0.7.
The old forms are not silently accepted and are not merely deprecated: the
router rejects them while it is being built, with `Path segments must not
start with ':'. For capture groups, use '{capture}'.` Because routers are
usually built during start-up, a missed migration surfaces as a crash on
deploy rather than a compiler error, so pair the syntax rule with the
router-construction test in [Testing](#testing).

A path segment that must literally begin with `:` or `*` requires
`Router::without_v07_checks`, which disables the migration diagnostics for
the whole router. Prefer rewriting the route.

## Extractors

### Order of Extractors

A handler **MUST** place its single body-consuming extractor last. Every other
extractor **MAY** appear in any order, and **SHOULD** be ordered for
readability: path parameters first, then query, then state and request-scoped
guards.

```rust
use axum::{
    extract::{Path, Query, State},
    Json,
};
use serde::Deserialize;

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
    auth: JwtAuth,
    Json(payload): Json<UpdateUserRequest>,  // body extractor, last
) -> Result<Json<User>, AppError> {
    // Handler implementation
}
```

**Do**:

```rust
// Any arrangement of the parts extractors compiles; pick the readable one
pub async fn update_user(
    State(state): State<AppState>,
    auth: JwtAuth,
    Path(user_id): Path<i64>,
    Json(payload): Json<UpdateUserRequest>,
) -> Result<Json<User>, AppError>

// `Request` consumes the body too, so it also goes last
pub async fn audit(
    headers: HeaderMap,
    State(state): State<AppState>,
    request: Request,
) -> String
```

**Don't**:

```rust
// `Json` consumes the body, so nothing may follow it
pub async fn update_user(
    Json(payload): Json<UpdateUserRequest>,
    Extension(trace_id): Extension<TraceId>,   // will not compile
) -> Result<Json<User>, AppError>

// Two body extractors in one signature
pub async fn update_user(
    Json(payload): Json<UpdateUserRequest>,
    body: String,                              // will not compile
) -> Result<Json<User>, AppError>
```

**Why**: Axum splits extraction into two traits. `FromRequestParts` sees only
the head — method, URI, headers, extensions — and leaves the body untouched, so
`Path`, `Query`, `State`, `HeaderMap`, `Extension`, `TypedHeader` and custom
guards built on that trait impose no ordering constraints on each other.
`FromRequest` takes the whole request and consumes the body, which is why Axum
implements the handler traits with the `FromRequest` argument in the final
position only. Putting `Json` or `Form` anywhere else, or asking for two of
them, is a compile error rather than a style problem.

Parts extractors still run left to right, so ordering does decide *which*
rejection a bad request receives: a handler with `Path` before `TypedHeader`
answers `400` for an unparseable path parameter even when the `Authorization`
header is also missing. Order for readability, and let the tests in
[Testing](#testing) pin down the rejection each case produces.

### Custom Extractors

Projects **SHOULD** create custom extractors for common patterns:

```rust
// src/shared/extractors.rs
use std::sync::Arc;

use axum::{
    extract::{FromRef, FromRequestParts},
    http::{request::Parts, StatusCode},
    RequestPartsExt,
};
use axum_extra::headers::{authorization::Bearer, Authorization};
use axum_extra::TypedHeader;

pub struct AuthUser {
    pub user_id: String,
}

impl<S> FromRequestParts<S> for AuthUser
where
    S: Send + Sync,
    Arc<JwtKeys>: FromRef<S>,
{
    type Rejection = (StatusCode, &'static str);

    async fn from_request_parts(parts: &mut Parts, state: &S) -> Result<Self, Self::Rejection> {
        let TypedHeader(Authorization(bearer)) = parts
            .extract::<TypedHeader<Authorization<Bearer>>>()
            .await
            .map_err(|_| (StatusCode::UNAUTHORIZED, "Missing authorization header"))?;

        let keys = Arc::<JwtKeys>::from_ref(state);
        let claims = verify_token(&keys, bearer.token())
            .map_err(|_| (StatusCode::UNAUTHORIZED, "Invalid token"))?;

        Ok(AuthUser { user_id: claims.sub })
    }
}
```

```rust
// Usage in handlers
pub async fn protected_route(
    auth: AuthUser,  // Custom extractor
    State(state): State<AppState>,
) -> Result<Json<User>, AppError> {
    let user = state.db.get_user(&auth.user_id).await?;
    Ok(Json(user))
}
```

**Do**:

```rust
impl<S: Send + Sync> FromRequestParts<S> for AuthUser {
    type Rejection = (StatusCode, &'static str);

    async fn from_request_parts(parts: &mut Parts, state: &S)
        -> Result<Self, Self::Rejection>
    { /* ... */ }
}
```

**Don't**:

```rust
// `axum::async_trait` no longer exists in 0.8:
// error[E0432]: unresolved import `axum::async_trait`
use axum::async_trait;

#[async_trait]
impl<S: Send + Sync> FromRequestParts<S> for AuthUser { /* ... */ }
```

**Why**: Axum 0.8 dropped its `async_trait` re-export because
`FromRequestParts`, `FromRequest` and `Handler` now use native `async fn` in
traits. Importing the removed re-export fails to resolve, and applying
`#[async_trait]` to a trait that does not use it rewrites the method into a
boxed future whose signature no longer matches the trait. Write the plain
`async fn`.

Taking the key material through `FromRef` rather than a whole `AppState` keeps
the extractor usable from routers with different state types and stops the
extractor from reaching parts of the state it has no business seeing.

## Error Handling

### Unified Error Type

Projects **MUST** define one error type covering every failure the service can
return, and **MUST** implement `IntoResponse` for it. Every example in this
guide uses the variants below; a service that adds a failure mode adds a variant
here and nowhere else.

```rust
// src/shared/error.rs
use axum::{
    http::StatusCode,
    response::{IntoResponse, Response},
    Json,
};
use serde::Serialize;
use thiserror::Error;

#[derive(Debug, Error)]
pub enum AppError {
    #[error("resource not found")]
    NotFound,

    #[error("unauthorized: {0}")]
    Unauthorized(String),

    #[error("forbidden: {0}")]
    Forbidden(String),

    #[error("validation failed: {0}")]
    Validation(String),

    #[error("database error")]
    Database(#[from] sqlx::Error),

    #[error("upstream service failed: {0}")]
    External(String),

    #[error("service unavailable: {0}")]
    ServiceUnavailable(String),

    #[error("internal error: {0}")]
    Internal(String),
}

#[derive(Serialize)]
pub struct ErrorResponse {
    pub error: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub code: Option<String>,
}

impl AppError {
    /// The public face of the error: status, stable machine-readable code, and
    /// a message that is safe to show a caller.
    fn parts(&self) -> (StatusCode, &'static str, String) {
        match self {
            Self::NotFound => (StatusCode::NOT_FOUND, "NOT_FOUND", "Resource not found".into()),
            Self::Unauthorized(_) => {
                (StatusCode::UNAUTHORIZED, "UNAUTHORIZED", "Unauthorized".into())
            }
            Self::Forbidden(_) => (StatusCode::FORBIDDEN, "FORBIDDEN", "Forbidden".into()),
            Self::Validation(message) => {
                (StatusCode::BAD_REQUEST, "VALIDATION_FAILED", message.clone())
            }
            Self::Database(_) | Self::Internal(_) => (
                StatusCode::INTERNAL_SERVER_ERROR,
                "INTERNAL",
                "Internal server error".into(),
            ),
            Self::External(_) | Self::ServiceUnavailable(_) => (
                StatusCode::SERVICE_UNAVAILABLE,
                "UPSTREAM_UNAVAILABLE",
                "Upstream service unavailable".into(),
            ),
        }
    }
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        let (status, code, message) = self.parts();

        // Log the full error, including its source chain, at the boundary; send
        // the caller only the sanitised message.
        if status.is_server_error() {
            tracing::error!(error = ?self, "request failed");
        } else {
            tracing::debug!(error = %self, "request rejected");
        }

        let body = ErrorResponse { error: message, code: Some(code.to_string()) };
        (status, Json(body)).into_response()
    }
}

impl From<tokio::task::JoinError> for AppError {
    fn from(err: tokio::task::JoinError) -> Self {
        Self::Internal(format!("background task failed: {err}"))
    }
}

impl From<jsonwebtoken::errors::Error> for AppError {
    fn from(err: jsonwebtoken::errors::Error) -> Self {
        Self::Internal(format!("JWT key material rejected: {err}"))
    }
}
```

Mapping `sqlx::Error::RowNotFound` onto `NotFound` is tempting, but a missing
row is only a `404` when the handler was looking one up by identity; the same
error from a join or an aggregate is a bug. Decide at the call site:

```rust
let user = sqlx::query_as!(User, "SELECT * FROM users WHERE id = $1", id)
    .fetch_optional(&state.db)
    .await?
    .ok_or(AppError::NotFound)?;
```

**Do**:

```rust
// One variant per failure mode; sources kept, public message sanitised
Self::Database(_) => (StatusCode::INTERNAL_SERVER_ERROR, "INTERNAL",
                      "Internal server error".into()),
```

**Don't**:

```rust
// Leaks schema, table names and connection strings to the caller
Self::Database(err) => (StatusCode::INTERNAL_SERVER_ERROR, err.to_string()),

// Discards the cause, so the log says nothing useful either
Self::Database(_) => StatusCode::INTERNAL_SERVER_ERROR.into_response(),
```

**Why**: One error type is what lets `?` work in every handler, and one
`IntoResponse` is what makes the API answer consistently. Splitting the type —
one enum in the error module, other variants invented ad hoc in the
authentication, jobs and resilience code — produces handlers that will not
compile against the declared enum, which is exactly the drift this section
exists to prevent. `#[from]` on `sqlx::Error` and `JoinError` keeps the original
error as the source, so `tracing::error!(error = ?self)` records the whole
chain while the caller sees a fixed string.

For general guidance on designing error types with `thiserror` and `anyhow`, see
the [Rust style guide](../languages/rust.md#error-types). The rule specific to
Axum is that handler return types **MUST NOT** be `anyhow::Error`: it has no
`IntoResponse`, so there is nowhere to decide the status code.

### Problem Details (RFC 9457)

Projects that publish an API to other teams **SHOULD** serve errors as
`application/problem+json` in the RFC 9457[^33] shape rather than an ad-hoc
envelope:

```rust
// src/shared/problem.rs
use axum::{http::{header, StatusCode}, response::{IntoResponse, Response}, Json};
use serde::Serialize;
use utoipa::ToSchema;

#[derive(Serialize, ToSchema)]
pub struct ProblemDetails {
    /// Stable URI naming the problem kind. Dereferenceable, ideally.
    #[schema(example = "https://api.example.com/problems/validation-failed")]
    pub r#type: String,
    #[schema(example = "Validation failed")]
    pub title: String,
    #[schema(example = 400)]
    pub status: u16,
    #[schema(example = "email is not a valid address")]
    pub detail: String,
    /// This occurrence. Using the request id makes it greppable in the logs.
    #[schema(example = "/requests/018f3c2a")]
    pub instance: String,
    /// Extension members. Safe to expose, machine-readable.
    #[serde(skip_serializing_if = "Vec::is_empty")]
    pub errors: Vec<String>,
}

pub struct Problem(pub ProblemDetails);

impl IntoResponse for Problem {
    fn into_response(self) -> Response {
        let status =
            StatusCode::from_u16(self.0.status).unwrap_or(StatusCode::INTERNAL_SERVER_ERROR);

        (status, [(header::CONTENT_TYPE, "application/problem+json")], Json(self.0))
            .into_response()
    }
}
```

Reuse the same type in the OpenAPI document so the published contract and the
wire format cannot drift:

```rust
#[utoipa::path(
    get,
    path = "/api/users/{id}",
    responses(
        (status = 200, description = "User found", body = User),
        (status = 404, description = "User not found",
         body = ProblemDetails, content_type = "application/problem+json"),
    ),
)]
```

**Why**: The `{"error": "..."}` envelope above is valid HTTP and is adequate for
an API whose only consumer is your own front end. RFC 9457 earns its keep once
other teams write clients: `type` gives them a stable identifier to branch on
that survives message rewording, `instance` ties a report back to a specific
request, and the media type tells a generic client that the body is a problem
description rather than the resource it asked for. All members are optional in
the specification, so a service **MAY** omit `instance` or `errors`; what it
**MUST NOT** do is send problem details under `application/json`, because that
defeats the content-negotiation the media type exists for.

## Middleware

### Tower Layers

Projects **SHOULD** use Tower layers for cross-cutting concerns, and **MUST**
treat the declaration order inside `ServiceBuilder` as the request order:

```rust
use axum::{
    extract::{DefaultBodyLimit, Request},
    http::{header, HeaderName, HeaderValue, Method, StatusCode},
    middleware::{self, Next},
    response::Response,
    routing::{get, post},
    Router,
};
use std::time::Duration;
use tower::ServiceBuilder;
use tower_http::{
    compression::CompressionLayer,
    cors::CorsLayer,
    limit::RequestBodyLimitLayer,
    request_id::{MakeRequestUuid, PropagateRequestIdLayer, SetRequestIdLayer},
    sensitive_headers::{SetSensitiveRequestHeadersLayer, SetSensitiveResponseHeadersLayer},
    trace::TraceLayer,
};

const REQUEST_ID: HeaderName = HeaderName::from_static("x-request-id");
const GLOBAL_BODY_LIMIT: usize = 256 * 1024;      // 256 KiB
const UPLOAD_BODY_LIMIT: usize = 10 * 1024 * 1024; // 10 MiB

fn cors(allowed_origins: &[String]) -> Result<CorsLayer, AppError> {
    let origins = allowed_origins
        .iter()
        .map(|origin| {
            HeaderValue::from_str(origin)
                .map_err(|_| AppError::Validation(format!("invalid CORS origin: {origin}")))
        })
        .collect::<Result<Vec<_>, _>>()?;

    Ok(CorsLayer::new()
        .allow_origin(origins)
        .allow_methods([Method::GET, Method::POST, Method::PUT, Method::DELETE])
        .allow_headers([header::AUTHORIZATION, header::CONTENT_TYPE])
        .allow_credentials(true)
        .max_age(Duration::from_secs(600)))
}

pub fn create_app(state: AppState) -> Result<Router, AppError> {
    let sensitive = [header::AUTHORIZATION, header::COOKIE, header::SET_COOKIE];

    let uploads = Router::new()
        .route("/uploads", post(upload))
        // `RequestBodyLimitLayer` rewrites the request body type, so it must be
        // the innermost layer on the routes it guards.
        .route_layer(RequestBodyLimitLayer::new(UPLOAD_BODY_LIMIT))
        .route_layer(DefaultBodyLimit::disable());

    let app = Router::new()
        .route("/users", get(list_users))
        .merge(uploads)
        .layer(
            ServiceBuilder::new()
                .layer(SetRequestIdLayer::new(REQUEST_ID, MakeRequestUuid))
                .layer(SetSensitiveRequestHeadersLayer::new(sensitive.clone()))
                .layer(TraceLayer::new_for_http())
                .layer(SetSensitiveResponseHeadersLayer::new(sensitive))
                .layer(PropagateRequestIdLayer::new(REQUEST_ID))
                .layer(cors(&state.config.allowed_origins)?)
                .layer(CompressionLayer::new())
                .layer(middleware::from_fn(timeout_middleware))
                .layer(DefaultBodyLimit::max(GLOBAL_BODY_LIMIT)),
        )
        .with_state(state);

    Ok(app)
}

async fn timeout_middleware(req: Request, next: Next) -> Result<Response, StatusCode> {
    tokio::time::timeout(Duration::from_secs(30), next.run(req))
        .await
        .map_err(|_| StatusCode::REQUEST_TIMEOUT)
}
```

The stack above traverses like this:

```text
request  ──► SetRequestId ──► SetSensitiveRequestHeaders ──► Trace
         ──► SetSensitiveResponseHeaders ──► PropagateRequestId ──► Cors
         ──► Compression ──► timeout_middleware ──► DefaultBodyLimit ──► handler
response ◄── (the same layers in reverse) ◄────────────────────────────┘
```

**Do**:

```rust
// The layer that must see the request first is declared first
ServiceBuilder::new()
    .layer(SetRequestIdLayer::new(REQUEST_ID, MakeRequestUuid))
    .layer(TraceLayer::new_for_http())
```

**Don't**:

```rust
// Trace now runs before the request id exists, so no span carries it
ServiceBuilder::new()
    .layer(TraceLayer::new_for_http())
    .layer(SetRequestIdLayer::new(REQUEST_ID, MakeRequestUuid))

// Repeated `Router::layer` calls are the opposite order: the *last* call
// is the outermost layer. Don't mix the two styles in one router.
router.layer(TraceLayer::new_for_http()).layer(CompressionLayer::new())
```

**Why**: Tower documents that "layers that are added first will be called with
the request first"[^2], and demonstrates it with `buffer(100)` before
`concurrency_limit(10)`, which admits up to 110 in-flight requests, against the
reverse order, which admits 10. Request flow through a `ServiceBuilder` is
therefore outer to inner in declaration order, and the response travels back
through the same layers in reverse. That is why the request id is set before
`TraceLayer` — a span cannot record an identifier that does not exist yet — and
why the sensitive-header layers bracket it: the request headers are marked
before tracing reads them, and the response headers are marked on the way out.

`Router::layer` composes the other way round: each call wraps everything
registered so far, so the last `layer` call is the outermost. Both APIs are
correct; mixing them in one router is how ordering bugs get written.

### Production Hardening

Public deployments **MUST** allowlist CORS origins, **MUST** bound request
bodies, **MUST** mark credential-bearing headers sensitive before any tracing
layer, and **SHOULD** give every request a propagated identifier.

**Do**:

```rust
// Origins from configuration, per environment
CorsLayer::new()
    .allow_origin(origins)
    .allow_methods([Method::GET, Method::POST])
    .allow_credentials(true)
```

**Don't**:

```rust
// `permissive` sends `Access-Control-Allow-Origin: *`, which browsers refuse
// to combine with credentials — so cookie-authenticated calls fail, and the
// usual "fix" is to reflect the caller's own Origin instead
CorsLayer::permissive()
```

**Why**: `CorsLayer::permissive` is a development convenience. It allows any
origin, method and header, which is defensible for a public read-only API with
no credentials, and indefensible the moment a cookie or an `Authorization`
header is involved. Naming the origins in configuration keeps the policy
reviewable and per-environment.

Axum applies a 2 MiB `DefaultBodyLimit` unless it is disabled, so bodies are
not unbounded by default; the reason to set the limit explicitly is that 2 MiB
is rarely the right number for either a JSON endpoint or an upload endpoint, and
an explicit constant is what a reviewer can check against the deployment.
Streaming endpoints that must disable `DefaultBodyLimit` need
`RequestBodyLimitLayer` instead, and because that layer changes the body type
from `Body` to `Limited<Body>` it **MUST** be applied with `route_layer` on the
routes concerned rather than added to the global stack — any `from_fn`
middleware inside it stops compiling:

```text
error[E0277]: the trait bound `FromFn<...>: Service<...>` is not satisfied
   = help: the trait `Service<Request<Limited<Body>>>` is not implemented
```

`SetSensitiveRequestHeadersLayer` marks a header value so that `Debug` prints
`Sensitive` instead of the token. `TraceLayer`'s default span does not record
headers, so this is not a live leak in the stack above; it becomes one as soon
as anyone adds `DefaultMakeSpan::new().include_headers(true)` or writes their
own `on_request`, which is why the marking belongs in the stack from the start
rather than after the incident.

Request ids close the gap between an error a caller reports and the logs that
explain it. `SetRequestIdLayer` accepts an inbound `x-request-id` when one is
present and generates a UUID otherwise; `PropagateRequestIdLayer` copies it onto
the response so the caller can quote it back.

WebSocket connections need their own controls — origin checks, frame-size caps
and idle timeouts — because the middleware above only runs on the upgrade
request. See [WebSocket Security](#websocket-security).

### Custom Middleware

Custom middleware **SHOULD** use `middleware::from_fn` for simplicity, and
**MUST** take `axum::extract::Request` (or another `FromRequest` extractor)
as its second-to-last argument and the non-generic `Next` as its last:

```rust
use axum::{
    extract::{Request, State},
    http::{StatusCode, header},
    middleware::{self, Next},
    response::Response,
};

async fn auth_middleware(
    State(state): State<AppState>,
    req: Request,
    next: Next,
) -> Result<Response, StatusCode> {
    let token = req
        .headers()
        .get(header::AUTHORIZATION)
        .and_then(|value| value.to_str().ok())
        .and_then(|value| value.strip_prefix("Bearer "))
        .ok_or(StatusCode::UNAUTHORIZED)?;

    verify_token(&state.jwt_keys, token).map_err(|_| StatusCode::UNAUTHORIZED)?;

    Ok(next.run(req).await)
}

// Apply to specific routes. Middleware that extracts `State` must be
// registered with `from_fn_with_state`, which supplies that argument.
let protected = Router::new()
    .route("/admin", get(admin_handler))
    .layer(middleware::from_fn_with_state(state.clone(), auth_middleware))
    .with_state(state);
```

**Do**:

```rust
async fn middleware(req: Request, next: Next) -> Result<Response, StatusCode>
```

**Don't**:

```rust
// Axum 0.7 signature: `Next` no longer takes a body parameter
async fn middleware<B>(req: Request<B>, next: Next<B>) -> Result<Response, StatusCode>
```

**Why**: `from_fn` provides the simplest way to create middleware
without implementing `Layer` and `Service` traits manually. Axum 0.8's
`Next` is not generic and `Next::run` consumes an `axum::extract::Request`,
which is `http::Request<axum::body::Body>`; a middleware generic over the
body type therefore no longer compiles. Reading the header rather than
using a `TypedHeader` extractor keeps the request intact so it can be
forwarded to `next`.

## State Management

### Shared State

Projects **MUST** use `State` extractor for sharing state:

```rust
// src/shared/state.rs
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
// src/features/users/handlers.rs
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

### Negative and Lifecycle Tests

Happy-path tests prove the router is wired up. They prove nothing about the
contract a client actually depends on. Projects **MUST** test extractor
rejections, authentication failures and body limits, and **SHOULD** test
timeouts, rate limits, WebSocket lifecycle and shutdown.

Drive the rejection contract from a table, so adding a case is one line:

```rust
// tests/rejections.rs
use axum::body::Body;
use axum::http::{header, Request, StatusCode};
use tower::ServiceExt;

mod common;

async fn send(request: Request<Body>) -> StatusCode {
    common::test_app().await.oneshot(request).await.unwrap().status()
}

#[tokio::test]
async fn rejections_map_to_documented_statuses() {
    let cases: Vec<(&str, Request<Body>, StatusCode)> = vec![
        (
            "valid body",
            Request::post("/users")
                .header(header::CONTENT_TYPE, "application/json")
                .body(Body::from(r#"{"name":"Alice"}"#))
                .unwrap(),
            StatusCode::CREATED,
        ),
        (
            "malformed JSON",
            Request::post("/users")
                .header(header::CONTENT_TYPE, "application/json")
                .body(Body::from("{"))
                .unwrap(),
            StatusCode::BAD_REQUEST,
        ),
        (
            "missing field",
            Request::post("/users")
                .header(header::CONTENT_TYPE, "application/json")
                .body(Body::from("{}"))
                .unwrap(),
            StatusCode::UNPROCESSABLE_ENTITY,
        ),
        (
            "wrong content type",
            Request::post("/users")
                .header(header::CONTENT_TYPE, "text/plain")
                .body(Body::from(r#"{"name":"Alice"}"#))
                .unwrap(),
            StatusCode::UNSUPPORTED_MEDIA_TYPE,
        ),
        (
            "oversized body",
            Request::post("/users")
                .header(header::CONTENT_TYPE, "application/json")
                .body(Body::from(format!(r#"{{"name":"{}"}}"#, "a".repeat(512))))
                .unwrap(),
            StatusCode::PAYLOAD_TOO_LARGE,
        ),
        (
            "unknown route",
            Request::get("/nope").body(Body::empty()).unwrap(),
            StatusCode::NOT_FOUND,
        ),
        (
            "wrong method",
            Request::delete("/users").body(Body::empty()).unwrap(),
            StatusCode::METHOD_NOT_ALLOWED,
        ),
        (
            "missing credentials",
            Request::get("/protected").body(Body::empty()).unwrap(),
            StatusCode::UNAUTHORIZED,
        ),
        (
            "valid credentials",
            Request::get("/protected")
                .header(header::AUTHORIZATION, "Bearer valid-token")
                .body(Body::empty())
                .unwrap(),
            StatusCode::OK,
        ),
    ];

    for (name, request, expected) in cases {
        assert_eq!(send(request).await, expected, "case: {name}");
    }
}
```

Timeouts and other deadline behaviour belong on Tokio's paused clock, so the
suite does not spend the real duration waiting:

```rust
#[tokio::test(start_paused = true)]  // needs tokio feature "test-util"
async fn slow_handlers_hit_the_timeout() {
    let app = common::test_app().await;
    let request = Request::get("/slow").body(Body::empty()).unwrap();

    let result = tokio::time::timeout(Duration::from_secs(30), app.oneshot(request)).await;

    assert!(result.is_err(), "handler should not have completed inside the deadline");
}
```

Shutdown needs a test that the tracked work actually finishes, not merely that
the process exits:

```rust
#[tokio::test]
async fn shutdown_waits_for_tracked_work() {
    let tasks = TaskTracker::new();
    let cancel = CancellationToken::new();
    let done = Arc::new(AtomicBool::new(false));

    spawn_worker(&tasks, cancel.clone(), Arc::clone(&done));
    cancel.cancel();
    tasks.close();

    tokio::time::timeout(Duration::from_secs(5), tasks.wait())
        .await
        .expect("tracked work did not finish inside the shutdown deadline");

    assert!(done.load(Ordering::SeqCst), "worker did not run to completion");
}
```

Rate limiting has its own test in [Rate Limiting](#rate-limiting-with-tower-governor),
because Governor's clock does not respond to `tokio::time::pause`.

**Do**:

```rust
// Assert the status a client will actually see
assert_eq!(send(malformed_json).await, StatusCode::BAD_REQUEST);
```

**Don't**:

```rust
// "It didn't succeed" passes for a 400, a 500 and a routing typo alike
assert!(!response.status().is_success());
```

**Why**: A rejection is part of the published contract, and Axum's rejections
are not all the status a reader would guess: syntactically invalid JSON is
`400`, but JSON that parses and then fails to deserialise is `422`, and the
wrong `Content-Type` is `415` before the body is looked at. Those three are
easy to document wrongly and impossible to notice from a suite that only asserts
`201`. The table form matters because the interesting property is the *set* of
mappings: a change to a shared extractor or to the body limit moves several
cases at once, and a table shows which.

Deadline tests on the paused clock cost microseconds instead of the configured
timeout, which is what makes it reasonable to have one per deadline rather than
one for the whole service.

### Router Construction Tests

Projects **MUST** build the real router in a test:

```rust
// tests/router_test.rs
use axum::{body::Body, http::{Request, StatusCode}};
use tower::ServiceExt;

mod common;

#[tokio::test]
async fn router_builds_and_matches_path_parameters() {
    // Panics here are router-construction failures, not assertion failures.
    let app = common::create_test_app().await;

    let response = app
        .oneshot(
            Request::builder()
                .uri("/api/v1/users/1")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();

    assert_ne!(response.status(), StatusCode::NOT_FOUND);
}
```

**Why**: `Router::route` validates path syntax and rejects duplicate
method routes by panicking as the router is assembled, not by failing to
compile. Without a test that assembles the whole router — including
documentation and metrics routes merged in later — a stale `:id` capture
or a path registered twice reaches production and crashes the process on
start-up. Asserting the status is not `404` also proves the parameterised
route matched rather than merely existing.

## Database Integration

SQLx itself — `query_as!`, offline mode, connection tuning, type mapping — is
covered in the [Rust style guide](../languages/rust.md#sqlx-compile-time-checked-queries). This
section covers only what Axum adds: reaching the pool through `State`, turning
`sqlx::Error` into an HTTP response, and the transaction rules that handlers get
wrong.

### Pool Access from Handlers

Handlers **MUST** reach the pool through the `State` extractor rather than a
global:

```rust
// src/features/users/handlers.rs
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

**Why**: `PgPool` is `Clone` and internally reference-counted, so putting it in
`AppState` costs an atomic increment per request and keeps the pool a normal
value that a test can substitute. A `static` pool or a `OnceCell` cannot be
swapped per test, which forces the suite onto one shared database and makes
`sqlx::test`'s per-test rollback unusable.

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
    credits BIGINT NOT NULL DEFAULT 0 CHECK (credits >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
```

**Why**: SQLx migrations integrate with compile-time verification and
support offline mode via `cargo sqlx prepare`, enabling CI without a
running database.

### Transaction Patterns

Database operations **MUST** use a transaction whenever more than one
statement has to succeed or fail together, and **MUST** enforce every
invariant inside that transaction:

```rust
pub async fn transfer_credits(
    from_user_id: i64,
    to_user_id: i64,
    amount: i64,
    pool: &PgPool,
) -> Result<(), AppError> {
    if amount <= 0 {
        return Err(AppError::Validation("Transfer amount must be positive".into()));
    }
    if from_user_id == to_user_id {
        return Err(AppError::Validation("Cannot transfer to the same account".into()));
    }

    let mut tx = pool.begin().await?;

    // The `credits >= $1` predicate makes the balance check and the debit a
    // single atomic statement: no row is updated when the balance is short.
    let debited = sqlx::query!(
        "UPDATE users SET credits = credits - $1 WHERE id = $2 AND credits >= $1",
        amount,
        from_user_id
    )
    .execute(&mut *tx)
    .await?
    .rows_affected();

    if debited != 1 {
        tx.rollback().await?;
        return Err(AppError::Validation("Insufficient credits".into()));
    }

    let credited = sqlx::query!(
        "UPDATE users SET credits = credits + $1 WHERE id = $2",
        amount,
        to_user_id
    )
    .execute(&mut *tx)
    .await?
    .rows_affected();

    if credited != 1 {
        tx.rollback().await?;
        return Err(AppError::NotFound);
    }

    tx.commit().await?;
    Ok(())
}
```

**Do**:

```rust
// Check and mutate in one statement, then verify the row count
let debited = sqlx::query!(
    "UPDATE users SET credits = credits - $1 WHERE id = $2 AND credits >= $1",
    amount,
    from_user_id
)
.execute(&mut *tx)
.await?
.rows_affected();
```

**Don't**:

```rust
// Read-then-write: another transaction can spend the balance in between
let user = sqlx::query!("SELECT credits FROM users WHERE id = $1", from_user_id)
    .fetch_one(&mut *tx)
    .await?;
if user.credits >= amount {
    sqlx::query!("UPDATE users SET credits = credits - $1 WHERE id = $2", amount, from_user_id)
        .execute(&mut *tx)
        .await?;
}
```

**Why**: An unconditional `UPDATE ... SET credits = credits - $1` reports
success whether or not the row exists and whether or not the balance can
cover the amount. Run against a two-account fixture, the unguarded pair of
statements drives the sender to `-10`, credits the recipient from an absent
sender (total credits rise from 10 to 15), destroys credits when the
recipient is absent, and reverses the transfer for a negative amount —
committing in every case. Checking `rows_affected()` after each statement
turns each of those into a rollback.

Under PostgreSQL's default Read Committed isolation, a concurrent transfer
blocks on the row lock and then re-evaluates the `WHERE` clause against the
committed row version, so two simultaneous transfers cannot both pass the
`credits >= $1` test. Weaker guards belong at the schema level as well: the
`CHECK (credits >= 0)` constraint on the migration above rejects any path
that bypasses this function.

## Security

### Authentication with axum-login

Projects **SHOULD** use axum-login[^10] for session-based authentication:

```rust
// src/shared/auth.rs
use axum_login::{AuthUser, AuthnBackend, AuthSession, AuthManagerLayerBuilder, UserId};
use password_auth::verify_password;
use serde::Deserialize;
use sqlx::PgPool;

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

#[derive(Debug, thiserror::Error)]
pub enum BackendError {
    #[error("database error")]
    Database(#[from] sqlx::Error),

    #[error("password verification task failed")]
    TaskJoin(#[from] tokio::task::JoinError),
}

impl AuthnBackend for Backend {
    type User = User;
    type Credentials = Credentials;
    type Error = BackendError;

    async fn authenticate(
        &self,
        creds: Self::Credentials,
    ) -> Result<Option<Self::User>, Self::Error> {
        let user: Option<User> = sqlx::query_as!(
            User,
            "SELECT id, username, password_hash FROM users WHERE username = $1",
            creds.username
        )
        .fetch_optional(&self.db)
        .await?;

        // Argon2 is deliberately slow, so it must not run on a runtime worker.
        // `move` gives the closure ownership of the candidate password and the
        // row; a borrowing closure would not outlive this future.
        let verified = tokio::task::spawn_blocking(move || {
            user.filter(|user| verify_password(&creds.password, &user.password_hash).is_ok())
        })
        .await?;

        Ok(verified)
    }

    async fn get_user(&self, user_id: &UserId<Self>) -> Result<Option<Self::User>, Self::Error> {
        let user = sqlx::query_as!(
            User,
            "SELECT id, username, password_hash FROM users WHERE id = $1",
            user_id
        )
        .fetch_optional(&self.db)
        .await?;

        Ok(user)
    }
}
```

**Do**:

```rust
// The closure owns what it touches, and a join failure is its own error
let verified = tokio::task::spawn_blocking(move || {
    user.filter(|user| verify_password(&creds.password, &user.password_hash).is_ok())
})
.await?;
```

**Don't**:

```rust
// Borrows `creds` and `user` across a thread boundary, and reports a panicked
// verification thread as a closed SQL pool
task::spawn_blocking(|| {
    Ok(user.filter(|user| verify_password(&creds.password, &user.password_hash).is_ok()))
})
.await
.map_err(|_| sqlx::Error::PoolClosed)?
```

**Why**: `spawn_blocking` requires a `'static` closure, so a closure that
borrows `creds` from the surrounding `async fn` does not satisfy the bound;
`move` transfers both values instead. Mapping the resulting `JoinError` onto
`sqlx::Error::PoolClosed` is worse than losing the error: it tells whoever reads
the log that the database pool shut down, sending them to the wrong subsystem
when what actually happened is that the password-hashing thread panicked. A
dedicated error type keeps the two apart. `AuthnBackend` also declares
`get_user(&self, user_id: &UserId<Self>)`; for this backend `UserId<Self>` is
`i64`, so the body is unchanged, but writing the associated type keeps the
signature correct if `AuthUser::Id` ever changes.

```rust
// src/app.rs - Setting up the auth layer
use axum_login::tower_sessions::{
    cookie::SameSite, ExpiredDeletion, Expiry, SessionManagerLayer,
};
use axum_login::AuthManagerLayerBuilder;
use axum::http::StatusCode;
use time::Duration;
use tower_sessions_sqlx_store::PostgresStore;

pub async fn create_app(config: Config) -> anyhow::Result<Router> {
    let state = AppState::new(config).await?;
    let backend = Backend { db: state.db.clone() };

    // Sessions live in PostgreSQL: they survive a restart and every
    // instance behind the load balancer reads the same records.
    let session_store = PostgresStore::new(state.db.clone());
    session_store.migrate().await?;

    tokio::spawn(
        session_store
            .clone()
            .continuously_delete_expired(tokio::time::Duration::from_secs(60)),
    );

    let session_layer = SessionManagerLayer::new(session_store)
        .with_secure(true)
        .with_http_only(true)
        .with_same_site(SameSite::Strict)
        .with_expiry(Expiry::OnInactivity(Duration::minutes(30)));

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

// Logout deletes the session record, not just the cookie
pub async fn logout(mut auth_session: AuthSession<Backend>) -> Result<StatusCode, AppError> {
    auth_session
        .logout()
        .await
        .map_err(|e| AppError::Unauthorized(e.to_string()))?;

    Ok(StatusCode::NO_CONTENT)
}
```

```toml
# Cargo.toml - pinned to the versions this example was checked against.
# axum-login 0.18 depends on tower-sessions 0.14; declaring 0.15 here puts two
# incompatible `SessionManagerLayer` types in the graph.
axum-login = "0.18.0"
tower-sessions = "0.14.0"
tower-sessions-sqlx-store = { version = "0.15.0", features = ["postgres"] }
sqlx = { version = "0.8.6", features = ["runtime-tokio", "postgres"] }
time = "0.3.55"
```

Deployed services **MUST NOT** use `MemoryStore`. It is for tests and local
demonstrations, where losing every session on restart does not matter:

```rust
// tests/common/mod.rs - test-only session store
use axum_login::tower_sessions::{Expiry, MemoryStore, SessionManagerLayer};
use time::Duration;

pub fn test_session_layer() -> SessionManagerLayer<MemoryStore> {
    SessionManagerLayer::new(MemoryStore::default())
        .with_expiry(Expiry::OnInactivity(Duration::minutes(30)))
}
```

**Session lifecycle**: `AuthSession::login` calls `Session::cycle_id`, which
issues a new session identifier on sign-in and closes off session fixation.
`AuthSession::logout` calls `Session::flush`, which deletes the stored
record so a copied cookie is worthless afterwards. On every request
axum-login compares the stored `session_auth_hash` against the current one
in constant time and flushes the session when they differ; because the
`AuthUser` implementation above returns the password hash, changing a
password revokes that user's existing sessions everywhere. A service that
needs "sign out of all devices" without a password change **SHOULD** back
`session_auth_hash` with a separate per-user secret that it can rotate on
its own.

**Why**: axum-login provides a type-safe, Tower-based authentication
layer with support for arbitrary user types and backends. It integrates
seamlessly with Axum's extractor system and supports both
authentication and authorization via traits.

### JWT Authentication with jsonwebtoken

For stateless API authentication, projects **SHOULD** use jsonwebtoken[^11].
The signing algorithm **MUST** be chosen explicitly and stored alongside the
keys, and the verifier **MUST** check issuer, audience, expiry, and
not-before:

```toml
# Cargo.toml - `rust_crypto` or `aws_lc_rs` selects the crypto provider;
# jsonwebtoken 11 panics at runtime when neither is enabled. `rsa` is a direct
# dependency because the key-size check below parses the modulus itself.
jsonwebtoken = { version = "11.0.0", features = ["rust_crypto"] }
rsa = { version = "0.9.10", features = ["pem"] }
```

```rust
// src/shared/jwt.rs
use jsonwebtoken::{decode, encode, Algorithm, DecodingKey, EncodingKey, Header, Validation};
use rsa::pkcs1::DecodeRsaPublicKey;
use rsa::pkcs8::DecodePublicKey;
use rsa::traits::PublicKeyParts;
use rsa::RsaPublicKey;
use serde::{Deserialize, Serialize};
use std::time::{SystemTime, UNIX_EPOCH};

/// Minimum modulus size this service accepts for RS256.
pub const MIN_RSA_MODULUS_BITS: usize = 4096;

/// The token profile. Every claim here is required by the verifier.
#[derive(Debug, Serialize, Deserialize)]
pub struct Claims {
    pub sub: String,        // Subject (user ID)
    pub iss: String,        // Issuer (the service that minted the token)
    pub aud: String,        // Audience (the API the token is for)
    pub exp: u64,           // Expiration time
    pub nbf: u64,           // Not before
    pub iat: u64,           // Issued at
    pub roles: Vec<String>, // User roles
}

/// `jsonwebtoken` accepts any well-formed RSA key, so the size has to be
/// checked against the parsed modulus before the key is used.
fn rsa_modulus_bits(public_key_pem: &[u8]) -> Result<usize, AppError> {
    let pem = std::str::from_utf8(public_key_pem)
        .map_err(|_| AppError::Validation("public key PEM is not valid UTF-8".into()))?;

    // SPKI ("BEGIN PUBLIC KEY") first, then PKCS#1 ("BEGIN RSA PUBLIC KEY").
    let key = RsaPublicKey::from_public_key_pem(pem)
        .or_else(|_| RsaPublicKey::from_pkcs1_pem(pem))
        .map_err(|e| AppError::Validation(format!("public key is not RSA: {e}")))?;

    Ok(key.n().bits())
}

pub struct JwtKeys {
    algorithm: Algorithm,
    encoding: EncodingKey,
    decoding: DecodingKey,
    issuer: String,
    audience: String,
}

impl JwtKeys {
    /// RS256 with an RSA key pair. Preferred in production: only the issuing
    /// service needs the private key. The 4096-bit minimum is enforced below,
    /// not merely documented.
    pub fn rs256(
        private_key_pem: &[u8],
        public_key_pem: &[u8],
        issuer: impl Into<String>,
        audience: impl Into<String>,
    ) -> Result<Self, AppError> {
        let bits = rsa_modulus_bits(public_key_pem)?;
        if bits < MIN_RSA_MODULUS_BITS {
            return Err(AppError::Validation(format!(
                "RSA modulus is {bits} bits; {MIN_RSA_MODULUS_BITS} is the minimum"
            )));
        }

        Ok(Self {
            algorithm: Algorithm::RS256,
            encoding: EncodingKey::from_rsa_pem(private_key_pem)?,
            decoding: DecodingKey::from_rsa_pem(public_key_pem)?,
            issuer: issuer.into(),
            audience: audience.into(),
        })
    }

    /// HS256 with a shared secret of at least 32 bytes from a CSPRNG. Use
    /// only where the same service both mints and verifies the token: every
    /// holder of the secret can forge tokens.
    pub fn hs256(
        secret: &[u8],
        issuer: impl Into<String>,
        audience: impl Into<String>,
    ) -> Result<Self, AppError> {
        if secret.len() < 32 {
            return Err(AppError::Validation("JWT secret must be >= 32 bytes".into()));
        }

        Ok(Self {
            algorithm: Algorithm::HS256,
            encoding: EncodingKey::from_secret(secret),
            decoding: DecodingKey::from_secret(secret),
            issuer: issuer.into(),
            audience: audience.into(),
        })
    }
}

pub fn create_token(keys: &JwtKeys, user_id: &str, roles: Vec<String>) -> Result<String, AppError> {
    // A clock before the Unix epoch is the only failure here, and it MUST NOT
    // become a panic: the guide's own Clippy configuration denies `expect`.
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_err(|_| AppError::Internal("system clock is before the Unix epoch".into()))?
        .as_secs();

    let claims = Claims {
        sub: user_id.to_string(),
        iss: keys.issuer.clone(),
        aud: keys.audience.clone(),
        exp: now + 900, // 15 minutes for access tokens
        nbf: now,
        iat: now,
        roles,
    };

    encode(&Header::new(keys.algorithm), &claims, &keys.encoding)
        .map_err(|e| AppError::Internal(format!("Token creation failed: {}", e)))
}

pub fn verify_token(keys: &JwtKeys, token: &str) -> Result<Claims, AppError> {
    let mut validation = Validation::new(keys.algorithm);
    validation.set_issuer(&[keys.issuer.as_str()]);
    validation.set_audience(&[keys.audience.as_str()]);
    validation.set_required_spec_claims(&["exp", "nbf", "iss", "aud", "sub"]);
    validation.validate_nbf = true;
    validation.leeway = 30;

    decode::<Claims>(token, &keys.decoding, &validation)
        .map(|data| data.claims)
        .map_err(|e| AppError::Unauthorized(format!("Invalid token: {}", e)))
}
```

Projects **MUST** test that the verifier rejects a token signed with a
different algorithm:

```rust
// tests/jwt_test.rs
use jsonwebtoken::{encode, Algorithm, EncodingKey, Header};

const PRIVATE_PEM: &[u8] = include_bytes!("fixtures/jwt-private.pem");
const PUBLIC_PEM: &[u8] = include_bytes!("fixtures/jwt-public.pem");

#[test]
fn rsa_verifier_rejects_hs256_tokens() {
    let keys = JwtKeys::rs256(PRIVATE_PEM, PUBLIC_PEM, "https://auth.example.com", "my-api")
        .unwrap();

    // Algorithm confusion: sign with HS256 using the public key as the
    // HMAC secret, which an attacker can read.
    let forged = encode(
        &Header::new(Algorithm::HS256),
        &admin_claims(),
        &EncodingKey::from_secret(PUBLIC_PEM),
    )
    .unwrap();

    assert!(verify_token(&keys, &forged).is_err());
}

/// The size promise in the docstring is only worth anything if it is checked.
#[test]
fn undersized_rsa_keys_are_refused() {
    // 2048-bit fixture: well-formed, parses cleanly, below the stated minimum.
    let result = JwtKeys::rs256(
        RSA_2048_PRIVATE_PEM,
        RSA_2048_PUBLIC_PEM,
        "https://auth.example.com",
        "my-api",
    );

    let message = match result {
        Ok(_) => panic!("2048-bit key accepted"),
        Err(e) => e.to_string(),
    };
    assert!(message.contains("2048 bits"), "unexpected message: {message}");
}
```

```rust
// src/shared/extractors.rs - JWT extractor
use std::sync::Arc;

use axum::{
    extract::{FromRef, FromRequestParts},
    http::request::Parts,
    RequestPartsExt,
};
use axum_extra::headers::{authorization::Bearer, Authorization};
use axum_extra::TypedHeader;

pub struct JwtAuth {
    pub user_id: String,
    pub roles: Vec<String>,
}

impl<S> FromRequestParts<S> for JwtAuth
where
    S: Send + Sync,
    Arc<JwtKeys>: FromRef<S>,
{
    type Rejection = AppError;

    async fn from_request_parts(parts: &mut Parts, state: &S) -> Result<Self, Self::Rejection> {
        let TypedHeader(Authorization(bearer)) = parts
            .extract::<TypedHeader<Authorization<Bearer>>>()
            .await
            .map_err(|_| AppError::Unauthorized("Missing authorization header".into()))?;

        let keys = Arc::<JwtKeys>::from_ref(state);
        let claims = verify_token(&keys, bearer.token())?;

        Ok(JwtAuth { user_id: claims.sub, roles: claims.roles })
    }
}
```

**Do**:

```rust
// Bind the algorithm to the key material and check who the token is for
let keys = JwtKeys::rs256(&private_key, &public_key, issuer, audience)?;

// Inside src/jwt.rs, where the algorithm travels with the key
encode(&Header::new(keys.algorithm), &claims, &keys.encoding)?;

let mut validation = Validation::new(keys.algorithm);
validation.set_issuer(&[keys.issuer.as_str()]);
validation.set_audience(&[keys.audience.as_str()]);
```

**Don't**:

```rust
// `Header::default()` and `Validation::default()` are both HS256, so this
// combination fails outright with an RSA key: `InvalidAlgorithm`
encode(&Header::default(), &claims, &EncodingKey::from_rsa_pem(&private_key)?)?;
decode::<Claims>(token, &keys.decoding, &Validation::default())?;

// Don't use weak secrets
let keys = JwtKeys::hs256(b"secret", issuer, audience)?;  // Too short

// Don't state a key-size minimum you never check: `from_rsa_pem` parses a
// 2048-bit key just as happily as a 4096-bit one
/// RS256 with an RSA key pair (4096-bit minimum).
pub fn rs256(private_key_pem: &[u8], public_key_pem: &[u8]) -> Result<Self, AppError> {
    Ok(Self {
        encoding: EncodingKey::from_rsa_pem(private_key_pem)?,
        decoding: DecodingKey::from_rsa_pem(public_key_pem)?,
        // ...
    })
}

// Don't set very long expiration
let claims = Claims {
    exp: now + 86400 * 365,  // 1 year - too long for access tokens
    // ...
};
```

**Why**: JWT provides stateless authentication suitable for APIs and
microservices. Both `Header::default()` and `Validation::default()` select
HS256, so pairing them with the recommended RSA keys does not produce the
RS256 flow the comment promises — it produces an `InvalidAlgorithm` error
at signing time, which invites a rushed revert to symmetric keys.
`Validation::new(alg)` restricts the accepted algorithms to that one
algorithm, which is what rejects a token forged with HS256 over the RSA
public key.

`Validation` on its own only enforces `exp`. Issuer and audience are
unchecked until `set_issuer` and `set_audience` are called, and `nbf` is
unchecked until `validate_nbf` is set, so a token minted for a different
service is otherwise accepted. `set_required_spec_claims` recognises
`exp`, `nbf`, `aud`, `iss` and `sub` only; any other required claim, such
as `jti` for replay tracking, has to be checked by the application. Use
short-lived access tokens with refresh-token rotation.

A docstring is not a constraint. `EncodingKey::from_rsa_pem` and
`DecodingKey::from_rsa_pem` validate PEM structure and nothing else, so a
constructor that promises a 4096-bit minimum and then only parses the key
accepts a 2048-bit one without comment — and the operator who generated it has
every reason to believe the guide's minimum was applied. `jsonwebtoken` exposes
no accessor for the modulus, so the check needs the key parsed independently;
`rsa::RsaPublicKey` is already in the dependency graph through the
`rust_crypto` feature, so making it a direct dependency adds a version pin
rather than a new tree. Check the public key, since that is the half the
verifier uses and the half a rotation is most likely to get wrong.

### Authorization with Casbin

Projects **SHOULD** use casbin-rs[^12] for flexible authorization (RBAC, ABAC):

```rust
// src/shared/authz.rs
use casbin::{CoreApi, Enforcer, RbacApi};
use std::sync::Arc;
use tokio::sync::RwLock;

pub type SharedEnforcer = Arc<RwLock<Enforcer>>;

pub async fn create_enforcer() -> Result<SharedEnforcer, AppError> {
    // Model defines access control rules structure
    let enforcer = Enforcer::new("config/rbac_model.conf", "config/policy.csv")
        .await
        .map_err(|e| AppError::Internal(format!("authorization model failed to load: {e}")))?;
    Ok(Arc::new(RwLock::new(enforcer)))
}

// Check if user has permission. `Ok(false)` is a denial; `Err` is an
// operational failure, and the two MUST NOT be conflated.
pub async fn check_permission(
    enforcer: &SharedEnforcer,
    subject: &str,
    object: &str,
    action: &str,
) -> Result<bool, AppError> {
    let e = enforcer.read().await;
    e.enforce((subject, object, action)).map_err(|err| {
        tracing::error!(%subject, %object, %action, error = ?err, "policy enforcement failed");
        AppError::ServiceUnavailable("Authorization unavailable".into())
    })
}

// Add role to user
pub async fn add_role_for_user(
    enforcer: &SharedEnforcer,
    user: &str,
    role: &str,
) -> Result<bool, AppError> {
    let mut e = enforcer.write().await;
    e.add_role_for_user(user, role, None)
        .await
        .map_err(|err| AppError::Internal(format!("role assignment failed: {err}")))
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
use axum::extract::Request;
use axum::http::Method;
use axum::middleware::Next;

pub async fn require_permission(
    State(state): State<AppState>,
    auth: JwtAuth,
    req: Request,
    next: Next,
) -> Result<Response, AppError> {
    let path = req.uri().path().to_owned();
    let action = match *req.method() {
        Method::GET | Method::HEAD => "read",
        Method::POST | Method::PUT | Method::PATCH => "write",
        Method::DELETE => "delete",
        _ => "read",
    };

    // `?` propagates an enforcement failure as 503; only `Ok(false)` is a
    // genuine authorisation denial.
    if !check_permission(&state.enforcer, &auth.user_id, &path, action).await? {
        return Err(AppError::Forbidden("Insufficient permissions".into()));
    }

    Ok(next.run(req).await)
}
```

**Do**:

```rust
e.enforce((subject, object, action)).map_err(|err| {
    tracing::error!(error = ?err, "policy enforcement failed");
    AppError::ServiceUnavailable("Authorization unavailable".into())
})
```

**Don't**:

```rust
// A corrupt model, an unreadable policy file and a genuine denial all become
// the same silent `403`
e.enforce((subject, object, action)).unwrap_or(false)
```

**Why**: Casbin provides a flexible, policy-based authorization system
supporting ACL, RBAC, and ABAC models. Policies can be stored in files or
databases and modified at runtime without code changes.

`unwrap_or(false)` fails closed, so it is not an authorisation bypass — but it
is undiagnosable. A policy file that no longer parses, a matcher that refers to
a removed attribute, or an adapter that cannot reach its store all present to
the operator as users being denied access they should have, with nothing in the
logs to say why. Returning `Result<bool, AppError>` keeps the safe default while
recording the cause, and lets the boundary answer `503` — "ask again" — rather
than `403` — "you are not allowed" — which is the accurate statement when the
service could not evaluate the policy at all.

Note that `enforce` on a loaded, in-memory model rarely fails; the failures this
guards against arrive with database adapters, watchers and runtime policy
reloads, which is precisely when a silent denial is hardest to trace.

### Tower-HTTP Auth Layers

Projects **MAY** use tower-http[^13] layers to authorise requests before they
reach a handler. Credentials **MUST** come from configuration or application
state, never from a literal in the source:

```rust
use std::sync::Arc;

use axum::{
    extract::Request,
    http::{header, StatusCode},
    response::IntoResponse,
};
use tower_http::auth::AsyncRequireAuthorizationLayer;
use tower_http::validate_request::ValidateRequestHeaderLayer;

// Machine-to-machine endpoint: a fixed, high-entropy header value read from
// configuration. `has_header_value` answers 403 when it does not match.
let admin_routes = Router::new()
    .route("/admin/metrics", get(metrics))
    .layer(ValidateRequestHeaderLayer::has_header_value(
        "x-internal-api-key",
        &config.internal_api_key,
    )?);

// Real authorisation: validate the presented token against application state.
let keys = Arc::clone(&state.jwt_keys);
let api_routes = Router::new()
    .route("/api/data", get(get_data))
    .layer(AsyncRequireAuthorizationLayer::new(move |request: Request| {
        let keys = Arc::clone(&keys);
        async move {
            let token = request
                .headers()
                .get(header::AUTHORIZATION)
                .and_then(|value| value.to_str().ok())
                .and_then(|value| value.strip_prefix("Bearer "));

            match token.map(|token| verify_token(&keys, token)) {
                Some(Ok(_)) => Ok(request),
                _ => Err(StatusCode::UNAUTHORIZED.into_response()),
            }
        }
    }));
```

**Don't**:

```rust
// Removed: "error[E0432]: unresolved import `tower_http::auth::
// RequireAuthorizationLayer` ... no `RequireAuthorizationLayer` in `auth`"
use tower_http::auth::RequireAuthorizationLayer;

// Still resolves, but deprecated, and bakes a credential into the binary
ValidateRequestHeaderLayer::basic("admin", "hunter2");
```

**Why**: `RequireAuthorizationLayer` was removed from `tower_http::auth`.
The surviving `ValidateRequestHeaderLayer::basic` and `::bearer`
constructors live in the `auth::require_authorization` module, deprecated
since tower-http 0.6.7 as "too basic to be useful in real applications".
Both compare against a compile-time constant, so the credential ends up in
the binary and in version control and cannot be rotated without a
redeploy. `AsyncRequireAuthorizationLayer` runs an async closure per
request, so the check can consult keys, a database, or a token
introspection endpoint. For session-based authentication, use axum-login
or a custom extractor instead.

## WebSocket

### Native Axum WebSocket Support

Projects **MUST** use Axum's built-in WebSocket support[^14] for real-time communication:

```rust
// src/features/chat/ws.rs
use axum::{
    extract::{
        ws::{Message, Utf8Bytes, WebSocket, WebSocketUpgrade},
        State,
    },
    response::Response,
};
use futures_util::{SinkExt, StreamExt};
use tokio::sync::broadcast::error::RecvError;
use tokio_util::sync::CancellationToken;

pub async fn ws_handler(
    ws: WebSocketUpgrade,
    State(state): State<AppState>,
) -> Response {
    let cancel = state.shutdown.clone();
    ws.on_upgrade(move |socket| handle_socket(socket, state, cancel))
}

async fn handle_socket(socket: WebSocket, state: AppState, cancel: CancellationToken) {
    let (mut sender, mut receiver) = socket.split();

    // Subscribe to broadcast channel
    let mut rx = state.broadcast_tx.subscribe();
    let send_cancel = cancel.clone();

    // Forward broadcast messages to the client
    let mut send_task = tokio::spawn(async move {
        loop {
            let message = tokio::select! {
                () = send_cancel.cancelled() => break,
                received = rx.recv() => received,
            };

            match message {
                // Axum 0.8 carries text as `Utf8Bytes`.
                Ok(text) => {
                    if sender.send(Message::Text(text)).await.is_err() {
                        break;
                    }
                }
                Err(RecvError::Lagged(skipped)) => {
                    // The consumer fell behind. Tell the client to resynchronise
                    // rather than silently dropping the connection.
                    tracing::warn!(skipped, "websocket consumer lagged; resynchronising");
                    let notice = Utf8Bytes::from_static(r#"{"type":"resync"}"#);
                    if sender.send(Message::Text(notice)).await.is_err() {
                        break;
                    }
                }
                Err(RecvError::Closed) => break,
            }
        }

        let _ = sender.close().await;
    });

    // Receive messages from client
    let mut recv_task = tokio::spawn(async move {
        loop {
            let next = tokio::select! {
                () = cancel.cancelled() => break,
                next = tokio::time::timeout(IDLE_TIMEOUT, receiver.next()) => next,
            };

            let Ok(Some(Ok(message))) = next else { break };

            match message {
                Message::Text(text) => {
                    tracing::debug!(bytes = text.len(), "text frame");
                }
                Message::Binary(data) => {
                    tracing::debug!(bytes = data.len(), "binary frame");
                }
                Message::Close(_) => break,
                // Axum answers Ping automatically; Pong needs no handling.
                Message::Ping(_) | Message::Pong(_) => {}
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
// src/shared/state.rs - Broadcast channel for WebSocket
use axum::extract::ws::Utf8Bytes;
use tokio::sync::broadcast;

#[derive(Clone)]
pub struct AppState {
    pub db: PgPool,
    /// Publish `Utf8Bytes` rather than `String`: the conversion then happens
    /// once at publish time instead of once per subscriber.
    pub broadcast_tx: broadcast::Sender<Utf8Bytes>,
    pub shutdown: CancellationToken,
}

impl AppState {
    pub async fn new(config: Config) -> anyhow::Result<Self> {
        let db = PgPool::connect(&config.database_url).await?;
        let (broadcast_tx, _) = broadcast::channel(100);

        Ok(Self { db, broadcast_tx, shutdown: CancellationToken::new() })
    }
}
```

**Do**:

```rust
// Channel already carries the wire type
let (broadcast_tx, _) = broadcast::channel::<Utf8Bytes>(100);
sender.send(Message::Text(text)).await

// Or convert at the boundary when the channel carries String
sender.send(Message::Text(msg.into())).await
```

**Don't**:

```rust
// error[E0308]: expected `Utf8Bytes`, found `String`
let mut rx: broadcast::Receiver<String> = state.broadcast_tx.subscribe();
sender.send(Message::Text(msg)).await

// A lagging consumer silently kills the sender task, so the client sits on a
// half-open socket receiving nothing
while let Ok(msg) = rx.recv().await { /* ... */ }
```

```rust
// src/features/chat/routes.rs
use axum::{routing::get, Router};

pub fn routes() -> Router<AppState> {
    Router::new().route("/ws", get(ws_handler))
}
```

**Why**: Axum 0.8 changed `Message::Text` to carry `Utf8Bytes` and
`Message::Binary` to carry `Bytes`, so that cloning a frame for several
subscribers is a reference-count bump rather than a copy. Enum construction does
not apply `From`, so passing a `String` straight into `Message::Text` is a type
error rather than an implicit conversion; either publish `Utf8Bytes` on the
channel or convert with `.into()` at the send site.

`while let Ok(msg) = rx.recv().await` ends the loop on *any* error, and
`broadcast::Receiver` returns `RecvError::Lagged` — a recoverable condition —
whenever a slow consumer falls behind the channel capacity. Treating that as
termination drops the client mid-session with no close frame and no log line.
Matching the two error variants separately keeps a lagging client connected and
tells it to resynchronise, and reserves disconnection for `Closed`.

Axum's WebSocket support is built on tokio-tungstenite[^15] but exposes a stable
API that will not break with internal updates. Use `socket.split()` to handle
send and receive concurrently in separate tasks, and pass both tasks the same
`CancellationToken` so [graceful shutdown](#graceful-shutdown) can close them.

### WebSocket Security

Connections **MUST** be authenticated during the upgrade, **MUST** have their
`Origin` validated, and **MUST** be bounded by frame size and idle timeout.
Services **SHOULD** authenticate with a same-site cookie, or with a single-use
handshake ticket, and **SHOULD NOT** put a reusable token in the URL.

```rust
use axum::{
    extract::{ws::WebSocketUpgrade, State},
    http::{header, HeaderMap, StatusCode},
    response::Response,
};

const MAX_FRAME_BYTES: usize = 64 * 1024;
const IDLE_TIMEOUT: Duration = Duration::from_secs(60);

fn origin_allowed(headers: &HeaderMap, allowed: &[String]) -> bool {
    headers
        .get(header::ORIGIN)
        .and_then(|value| value.to_str().ok())
        .is_some_and(|origin| allowed.iter().any(|candidate| candidate == origin))
}

/// Minted by an ordinary authenticated HTTP request, single use, short lived.
pub async fn issue_ws_ticket(
    State(state): State<AppState>,
    auth: JwtAuth,
) -> Result<(StatusCode, String), AppError> {
    let ticket = state.tickets.mint(&auth.user_id, Duration::from_secs(30)).await?;
    Ok((StatusCode::CREATED, ticket))
}

pub async fn authenticated_ws_handler(
    ws: WebSocketUpgrade,
    headers: HeaderMap,
    State(state): State<AppState>,
) -> Result<Response, AppError> {
    if !origin_allowed(&headers, &state.config.allowed_origins) {
        return Err(AppError::Forbidden("Origin not allowed".into()));
    }

    // The browser WebSocket API cannot set headers, but it can set
    // subprotocols, and those are not written to access logs or Referer.
    let ticket = headers
        .get("sec-websocket-protocol")
        .and_then(|value| value.to_str().ok())
        .and_then(|value| value.split(',').map(str::trim).nth(1))
        .unwrap_or_default()
        .to_owned();

    // Redeeming deletes the ticket, so a captured handshake cannot be replayed.
    let user_id = state.tickets.redeem(&ticket).await?;
    let cancel = state.shutdown.clone();

    Ok(ws
        .max_frame_size(MAX_FRAME_BYTES)
        .max_message_size(MAX_FRAME_BYTES)
        .protocols(["bearer-ticket"])
        .on_upgrade(move |socket| handle_authenticated_socket(socket, state, user_id, cancel)))
}
```

Services **MUST** also:

- serve WebSockets over `wss://` only, so the ticket and the frames are
  encrypted in transit;
- re-check authorisation per message for anything privileged, because the
  connection outlives the token that opened it;
- close connections whose session has expired or been logged out, rather than
  letting an open socket outlive its session record;
- rate-limit both connection attempts and messages per connection, since the
  HTTP rate limiter only sees the single upgrade request.

**Do**:

```rust
// One-time ticket, carried in the subprotocol, redeemed and destroyed
ws.protocols(["bearer-ticket"]).max_frame_size(MAX_FRAME_BYTES)
```

**Don't**:

```rust
// A reusable access token in the query string: it reaches access logs, proxy
// logs, browser history and the Referer header of anything the page loads next
#[derive(Deserialize)]
pub struct WsQuery { token: String }

pub async fn authenticated_ws_handler(
    ws: WebSocketUpgrade,
    Query(query): Query<WsQuery>,
    State(state): State<AppState>,
) -> Result<Response, AppError> {
    let claims = verify_token(&state.jwt_keys, &query.token)?;
    // ...
}
```

**Why**: WebSocket clients in the browser cannot set request headers on the
upgrade, so the token has to travel some other way. A URL is the worst of the
options: this guide recommends `TraceLayer`, whose default span records the
request URI, so a 15-minute access token in the query string is written to the
service's own logs, and from there to whatever aggregates them — plus the
proxy's access log, the browser's history, and the `Referer` of any subsequent
request. The token is reusable for its whole lifetime, so anyone who reads any
of those logs holds a working credential.

This is a property of *reusable* tokens in URLs, not of query parameters as
such. A ticket that is single-use, valid for seconds, and bound to one account
is not much use to a log reader, so a redacted or one-time query token remains a
legitimate design; OWASP's guidance is against putting ordinary credentials
there[^34]. Prefer the subprotocol or a `SameSite=Strict` cookie, and where a
cookie authenticates the handshake, validate `Origin` explicitly: the browser
sends the cookie cross-site on a WebSocket upgrade, and there is no CORS
preflight to stop it.

Frame and message size caps bound the memory a single connection can force the
server to allocate, and the idle timeout reclaims connections from clients that
vanished without a close frame — neither of which the HTTP middleware stack can
do, because it only ever sees the upgrade.

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
// src/features/users/handlers.rs - Instrumented handler
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

For distributed tracing, projects **MAY** use tracing-opentelemetry[^21]. The
four crates below share a version train and **MUST** be upgraded together:

```toml
# Cargo.toml
opentelemetry = "0.32.0"
opentelemetry_sdk = { version = "0.32.1", features = ["rt-tokio"] }
opentelemetry-otlp = { version = "0.32.0", features = ["grpc-tonic"] }
tracing-opentelemetry = "0.33.0"
```

```rust
// src/shared/telemetry.rs
use opentelemetry::{global, trace::TracerProvider as _, KeyValue};
use opentelemetry_otlp::WithExportConfig as _;
use opentelemetry_sdk::{
    propagation::TraceContextPropagator,
    trace::{Sampler, SdkTracerProvider},
    Resource,
};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt, EnvFilter};

/// Returns the provider so `main` can shut it down; dropping it silently
/// discards whatever the batch processor has not yet exported.
pub fn init_telemetry(service_name: &'static str) -> anyhow::Result<SdkTracerProvider> {
    // W3C `traceparent`, so spans join a trace that started upstream.
    global::set_text_map_propagator(TraceContextPropagator::new());

    let exporter = opentelemetry_otlp::SpanExporter::builder()
        .with_tonic()
        .with_endpoint("http://localhost:4317")
        .build()?;

    let provider = SdkTracerProvider::builder()
        .with_batch_exporter(exporter)
        .with_sampler(Sampler::ParentBased(Box::new(Sampler::TraceIdRatioBased(0.1))))
        .with_resource(
            Resource::builder()
                .with_service_name(service_name)
                .with_attributes([KeyValue::new("deployment.environment.name", "production")])
                .build(),
        )
        .build();

    let tracer = provider.tracer(service_name);
    global::set_tracer_provider(provider.clone());

    tracing_subscriber::registry()
        .with(EnvFilter::try_from_default_env().unwrap_or_else(|_| "info".into()))
        .with(tracing_opentelemetry::OpenTelemetryLayer::new(tracer))
        .with(tracing_subscriber::fmt::layer().json())
        .init();

    Ok(provider)
}

pub fn shutdown_telemetry(provider: SdkTracerProvider) {
    if let Err(error) = provider.shutdown() {
        tracing::error!(%error, "tracer provider shutdown failed");
    }
}
```

Shut the provider down as the last step of [graceful
shutdown](#graceful-shutdown), after the tracked tasks have finished, so the
spans they emit on the way out are exported.

**Do**:

```rust
let exporter = opentelemetry_otlp::SpanExporter::builder().with_tonic().build()?;
let provider = SdkTracerProvider::builder().with_batch_exporter(exporter).build();
```

**Don't**:

```rust
// 0.32 removed all of these: `new_exporter`, the `TracerProvider` name, and the
// runtime argument to `with_batch_exporter`
let exporter = opentelemetry_otlp::new_exporter().tonic().with_endpoint(endpoint);
let provider = TracerProvider::builder()
    .with_batch_exporter(exporter.build_span_exporter()?, opentelemetry_sdk::runtime::Tokio)
    .build();
```

**Why**: OpenTelemetry enables distributed tracing across microservices with
unique trace IDs, essential for debugging request flows in distributed systems.

The 0.32 API differs from the pipeline builders in earlier releases: exporters
are built per signal with `SpanExporter::builder()`, the SDK type is
`SdkTracerProvider`, and `with_batch_exporter` no longer takes a runtime because
the processor uses a dedicated thread. Installing `TraceContextPropagator` is
what makes a span join an upstream trace; without it every service starts a new
trace and the distributed part of distributed tracing does not happen.

Holding the provider matters as much as building it. `global::set_tracer_provider`
takes a clone, so nothing else keeps the batch processor alive at shutdown, and
a process that exits without calling `shutdown` loses the spans still sitting in
the batch queue — which are exactly the spans describing whatever went wrong
just before it exited.

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

```toml
# Cargo.toml
apalis = { version = "0.7.4", features = ["retry", "catch-panic", "limit"] }
apalis-redis = "0.7.4"
```

```rust
// src/shared/jobs/mod.rs
use std::time::Duration;

use apalis::layers::retry::RetryPolicy;
use apalis::prelude::*;
use apalis_redis::{Config as RedisConfig, RedisStorage};
use serde::{Deserialize, Serialize};

/// Apalis 0.7 needs no `Job` trait: a task is an ordinary serialisable struct,
/// and the queue namespace comes from the storage configuration.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SendEmail {
    /// Delivery is at-least-once, so the handler must be idempotent. Persist
    /// this key on first success and skip the send when it is already present.
    pub idempotency_key: String,
    pub to: String,
    pub subject: String,
    pub body: String,
}

async fn send_email(
    job: SendEmail,
    worker: Worker<Context>,
    attempt: Attempt,
    email_client: Data<EmailClient>,
) -> Result<(), Error> {
    tracing::info!(
        worker = %worker.id(),
        attempt = attempt.current(),
        to = %job.to,
        "sending email"
    );

    email_client
        .send(&job.to, &job.subject, &job.body)
        .await
        .map_err(|e| Error::Failed(std::sync::Arc::new(Box::new(e))))
}

pub async fn start_worker(redis_url: &str, email_client: EmailClient) -> anyhow::Result<()> {
    let conn = apalis_redis::connect(redis_url).await?;

    // Tasks whose worker dies mid-flight are re-enqueued after this timeout
    // rather than being lost; tasks that exhaust the retry policy land on the
    // backend's dead-job set, where they can be inspected and replayed.
    let config = RedisConfig::default()
        .set_namespace("send-email")
        .set_enqueue_scheduled(Duration::from_secs(30))
        .set_reenqueue_orphaned_after(Duration::from_secs(300));

    let storage: RedisStorage<SendEmail> = RedisStorage::new_with_config(conn, config);

    Monitor::new()
        .register(
            WorkerBuilder::new("email-worker")
                .catch_panic()
                .retry(RetryPolicy::retries(5))
                .concurrency(4)
                .data(email_client)
                .backend(storage)
                .build_fn(send_email),
        )
        .run()
        .await?;

    Ok(())
}

/// `Storage::push` takes `&mut self`. `RedisStorage` is cheap to clone, so
/// handlers keep a clone in `AppState` rather than a shared reference.
pub async fn enqueue_email(
    storage: &RedisStorage<SendEmail>,
    job: SendEmail,
) -> anyhow::Result<TaskId> {
    let mut storage = storage.clone();
    let parts = storage.push(job).await?;
    Ok(parts.task_id)
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
    enqueue_email(
        &state.job_storage,
        SendEmail {
            idempotency_key: format!("welcome:{}", user.id),
            to: user.email.clone(),
            subject: "Welcome!".into(),
            body: "Thanks for signing up.".into(),
        },
    )
    .await?;

    Ok(Json(user))
}
```

**Do**:

```rust
let conn = apalis_redis::connect(redis_url).await?;
let storage: RedisStorage<SendEmail> = RedisStorage::new(conn);

let mut storage = storage.clone();   // push needs &mut self
storage.push(job).await?;
```

**Don't**:

```rust
// None of this exists in the stable API: no `Job` trait, no `JobContext`,
// no `RedisStorage::connect`, and `push` cannot take `&self`
impl Job for SendEmailJob { const NAME: &'static str = "send_email"; }
async fn handler(job: SendEmailJob, ctx: JobContext) -> Result<(), Error>
let storage = RedisStorage::<SendEmailJob>::connect(redis_url).await?;
storage.push(job).await?;
```

**Why**: Apalis provides type-safe, Tower-based job processing with support for
Redis, PostgreSQL and other backends, and because a worker *is* a Tower service,
retries, panic recovery and concurrency limits are layers rather than bespoke
code.

The named `Job` trait, `JobContext` and `RedisStorage::connect` belong to a
pre-0.7 API and no longer resolve. In 0.7 the handler's extra arguments are
extractors — `Data<T>` for shared state, `Worker<Context>` for worker identity,
`Attempt` for the retry count — and connection setup is split between
`apalis_redis::connect`, which yields a connection manager, and
`RedisStorage::new`, which wraps it. `Storage::push` takes `&mut self`, so the
enqueue path needs an owned clone; passing `&RedisStorage` will not compile.

Retry configuration is a layer (`RetryPolicy`), not storage configuration:
`apalis_redis::Config` has no `set_max_retries`. What the storage configures is
recovery — `set_reenqueue_orphaned_after` decides how long a task claimed by a
dead worker waits before another worker may take it, which is the difference
between a lost job and a late one.

### Alternative: rusty-sidekiq

For interoperability with Ruby Sidekiq, projects **MAY** use rusty-sidekiq[^23]:

```toml
# Cargo.toml - the package is `rusty-sidekiq`; its library is `sidekiq`.
# The unrelated crate published as `sidekiq` is not this one.
rusty-sidekiq = { version = "0.14.2", default-features = false }
async-trait = "0.1.92"
```

```rust
use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use sidekiq::{RedisPool, Worker};

#[derive(Clone, Debug, Deserialize, Serialize)]
struct WelcomeEmailArgs {
    user_id: i64,
}

struct WelcomeEmailWorker;

// rusty-sidekiq still declares `Worker` with `#[async_trait]`, so
// implementations must carry the same attribute.
#[async_trait]
impl Worker<WelcomeEmailArgs> for WelcomeEmailWorker {
    async fn perform(&self, _args: WelcomeEmailArgs) -> sidekiq::Result<()> {
        // Send email
        Ok(())
    }
}

// Typed helper: the queue comes from the worker's own options.
WelcomeEmailWorker::opts()
    .queue("mailers")
    .perform_async(&redis_pool, WelcomeEmailArgs { user_id: 123 })
    .await?;

// Crate-level helper, for enqueueing to a Ruby worker that has no Rust type.
// Class and queue are both owned `String`s.
sidekiq::perform_async(
    &redis_pool,
    "WelcomeEmailWorker".to_string(),
    "mailers".to_string(),
    WelcomeEmailArgs { user_id: 123 },
)
.await?;
```

**Do**:

```rust
sidekiq::perform_async(&redis_pool, class, queue, args).await?;
```

**Don't**:

```rust
// error[E0061]: this function takes 4 arguments but 3 arguments were supplied
sidekiq::perform_async(
    &redis_pool,
    "WelcomeEmailWorker",              // also &str, not String
    WelcomeEmailWorker { user_id: 123 },
).await?;
```

**Why**: rusty-sidekiq is compatible with Ruby Sidekiq for mixed Ruby/Rust
environments. Use apalis for pure Rust applications.

Sidekiq routes work by queue name, so the crate-level
`perform_async(redis, class, queue, args)` requires the queue explicitly — there
is no default. Omitting it is a compile error rather than a silent enqueue to
`default`, which is the right trade: a job pushed to the wrong queue is picked
up by no worker and discovered days later. The typed
`Worker::opts().queue(..).perform_async(..)` path is preferable in Rust-to-Rust
code because the class name is derived from the type and cannot drift from it.

Keeping the argument struct separate from the worker type — rather than a struct
that is both — is what lets `class_name()` name a Ruby class that has no Rust
equivalent.

## Caching

### In-Memory Caching with Moka

Projects **SHOULD** use moka[^24] for high-performance in-memory caching:

```rust
// src/shared/cache.rs
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
// src/shared/redis.rs
use deadpool_redis::redis::AsyncCommands;
use deadpool_redis::{Config, Pool, Runtime};
use thiserror::Error;

pub async fn create_redis_pool(url: &str) -> anyhow::Result<Pool> {
    let cfg = Config::from_url(url);
    let pool = cfg.create_pool(Some(Runtime::Tokio1))?;
    Ok(pool)
}

#[derive(Debug, Error)]
pub enum CacheError {
    #[error("cache pool exhausted or unavailable")]
    Pool(#[from] deadpool_redis::PoolError),

    #[error("redis command failed")]
    Redis(#[from] deadpool_redis::redis::RedisError),

    #[error("cached value could not be decoded")]
    Decode(#[from] serde_json::Error),
}

#[derive(Clone)]
pub struct RedisCache {
    pool: Pool,
}

impl RedisCache {
    pub fn new(pool: Pool) -> Self {
        Self { pool }
    }

    /// `Ok(None)` means the key is genuinely absent. Connection, protocol and
    /// decoding failures are returned as errors, so the caller decides.
    pub async fn get<T: serde::de::DeserializeOwned>(
        &self,
        key: &str,
    ) -> Result<Option<T>, CacheError> {
        let mut conn = self.pool.get().await?;
        let raw: Option<String> = conn.get(key).await?;

        match raw {
            None => Ok(None),
            Some(raw) => Ok(Some(serde_json::from_str(&raw)?)),
        }
    }

    pub async fn set<T: serde::Serialize + Sync>(
        &self,
        key: &str,
        value: &T,
        ttl_secs: u64,
    ) -> Result<(), CacheError> {
        let mut conn = self.pool.get().await?;
        let data = serde_json::to_string(value)?;
        let _: () = conn.set_ex(key, data, ttl_secs).await?;
        Ok(())
    }

    pub async fn delete(&self, key: &str) -> Result<(), CacheError> {
        let mut conn = self.pool.get().await?;
        let _: () = conn.del(key).await?;
        Ok(())
    }

    pub async fn set_nx<T: serde::Serialize + Sync>(
        &self,
        key: &str,
        value: &T,
        ttl_secs: u64,
    ) -> Result<bool, CacheError> {
        let mut conn = self.pool.get().await?;
        let data = serde_json::to_string(value)?;
        let result: bool = deadpool_redis::redis::cmd("SET")
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

Fail-open is a policy, and it belongs at the boundary, stated once and
instrumented:

```rust
/// The bounds are also what make the future `Send`, and therefore usable from
/// an Axum handler.
pub async fn cached_or_fresh<T, F, Fut>(
    cache: &RedisCache,
    key: &str,
    load: F,
) -> Result<T, AppError>
where
    T: serde::Serialize + serde::de::DeserializeOwned + Send + Sync,
    F: FnOnce() -> Fut + Send,
    Fut: Future<Output = Result<T, AppError>> + Send,
{
    match cache.get::<T>(key).await {
        Ok(Some(hit)) => return Ok(hit),
        Ok(None) => tracing::debug!(key, "cache miss"),
        Err(error) => {
            // Explicit policy: serve from the source of truth, but record it,
            // so a dead cache shows up as a rate rather than as latency.
            metrics::counter!("cache_errors_total").increment(1);
            tracing::warn!(key, %error, "cache read failed; falling back to origin");
        }
    }

    let value = load().await?;

    if let Err(error) = cache.set(key, &value, 300).await {
        tracing::warn!(key, %error, "cache write failed");
    }

    Ok(value)
}
```

**Do**:

```rust
// A miss and a failure are different values
pub async fn get<T: DeserializeOwned>(&self, key: &str) -> Result<Option<T>, CacheError>
```

**Don't**:

```rust
// A dead Redis, a corrupt entry and an absent key are indistinguishable
pub async fn get<T: DeserializeOwned>(&self, key: &str) -> Option<T> {
    let mut conn = self.pool.get().await.ok()?;
    let data: Option<String> = conn.get(key).await.ok()?;
    data.and_then(|s| serde_json::from_str(&s).ok())
}
```

**Why**: Redis provides distributed caching that survives application restarts
and can be shared across multiple instances. deadpool-redis offers an async
connection pool optimised for Tokio.

Collapsing failures into `None` is a defensible *policy* — an optional cache
that is unreachable should not take the service down — but making it the
signature's only option removes the choice. With `Option<T>`, a Redis outage
looks exactly like a cold cache: the hit rate falls to zero, every request goes
to the database, and nothing in the logs or metrics says why. A corrupt or
schema-drifted entry is worse, because it re-serialises on every write and never
recovers. Returning `Result<Option<T>, CacheError>` keeps the same runtime
behaviour when the caller wants it, while making the fail-open decision explicit
at one place and countable.

Import the Redis traits through `deadpool_redis::redis` rather than a separate
`redis` dependency. The re-export is guaranteed to be the version deadpool was
built against; a separately declared `redis` can resolve to a different major,
and `AsyncCommands` from the wrong one simply will not apply to the pooled
connection.

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

    // L2: Redis. A cache failure is logged and treated as a miss here, at the
    // boundary, rather than being hidden inside the cache API.
    let redis_key = format!("user:{}", id);
    match redis_cache.get::<User>(&redis_key).await {
        Ok(Some(user)) => {
            local_cache.set_user(id, user.clone()).await;
            return Ok(user);
        }
        Ok(None) => {}
        Err(error) => tracing::warn!(%error, key = %redis_key, "L2 read failed"),
    }

    // L3: Database
    let user = sqlx::query_as!(User, "SELECT * FROM users WHERE id = $1", id)
        .fetch_one(db)
        .await?;

    // Populate caches
    if let Err(error) = redis_cache.set(&redis_key, &user, 3600).await {
        tracing::warn!(%error, key = %redis_key, "L2 write failed");
    }
    local_cache.set_user(id, user.clone()).await;

    Ok(user)
}
```

**Why**: Multi-level caching reduces latency (L1 is fastest) while maintaining consistency across
distributed instances (L2 provides shared state).

## Rate Limiting

### Rate Limiting with tower-governor

Projects **SHOULD** use tower-governor[^27] for rate limiting:

```toml
# Cargo.toml - the crate name uses an underscore; `governor` types appear
# in the layer signature, so it is a direct dependency too
tower_governor = "0.8.0"
governor = "0.10"
```

```rust
// src/shared/rate_limit.rs
use std::time::Duration;

use axum::body::Body;
use governor::middleware::NoOpMiddleware;
use tower_governor::{
    governor::{GovernorConfig, GovernorConfigBuilder},
    key_extractor::PeerIpKeyExtractor,
    GovernorLayer,
};

/// Sustained 10 requests per second per client, absorbing bursts of 30.
///
/// `period` is the time needed to replenish **one** request, so ten requests
/// per second is a 100 ms period. `per_second(10)` would mean the opposite:
/// one request every ten seconds.
pub fn api_quota() -> GovernorConfig<PeerIpKeyExtractor, NoOpMiddleware> {
    GovernorConfigBuilder::default()
        .period(Duration::from_millis(100))
        .burst_size(30)
        .finish()
        .expect("period and burst size are both non-zero")
}

/// One request every two seconds for sign-in and registration, burst of 5.
pub fn auth_quota() -> GovernorConfig<PeerIpKeyExtractor, NoOpMiddleware> {
    GovernorConfigBuilder::default()
        .period(Duration::from_secs(2))
        .burst_size(5)
        .finish()
        .expect("period and burst size are both non-zero")
}

pub fn rate_limiter(
    config: GovernorConfig<PeerIpKeyExtractor, NoOpMiddleware>,
) -> GovernorLayer<PeerIpKeyExtractor, NoOpMiddleware, Body> {
    GovernorLayer::new(config)
}
```

```rust
// src/app.rs - Apply rate limiting
use std::net::SocketAddr;

pub async fn create_app(config: Config) -> anyhow::Result<Router> {
    let state = AppState::new(config).await?;

    let api_routes = Router::new()
        .nest("/users", users::routes())
        .layer(rate_limiter(api_quota()));

    let auth_routes = Router::new()
        .route("/login", post(login))
        .route("/register", post(register))
        .layer(rate_limiter(auth_quota()));

    let app = Router::new()
        .nest("/api", api_routes)
        .nest("/auth", auth_routes)
        .with_state(state);

    Ok(app)
}

// REQUIRED for PeerIpKeyExtractor: without connect info there is no peer
// address to key on, and every request is rejected.
let listener = tokio::net::TcpListener::bind(&addr).await?;
axum::serve(
    listener,
    app.into_make_service_with_connect_info::<SocketAddr>(),
).await?;
```

**Do**:

```rust
// 10 requests per second: one replenished every 100 ms
GovernorConfigBuilder::default()
    .period(Duration::from_millis(100))
    .burst_size(30)

// The layer is constructed, not built from a struct literal
GovernorLayer::new(config)
```

**Don't**:

```rust
// One request every 10 seconds - 100x slower than "10 per second"
GovernorConfigBuilder::default()
    .per_second(10)
    .burst_size(30)

// `GovernorLayer`'s fields are private
GovernorLayer { config: Box::new(config) }
```

**Why**: tower-governor uses the GCRA (Generic Cell Rate Algorithm) for
fair, efficient rate limiting. Its quota is expressed as a replenishment
*period* per request, not as a rate: `finish` passes the period straight to
`Quota::with_period`, so `per_second(10)` yields one request every ten
seconds. Reading it as "ten requests per second" overstates the sustained
allowance a hundredfold, and the mistake only shows up under sustained
load, after the burst is spent. `GovernorLayer` also holds private fields
behind three generic parameters — the key extractor, the governor
middleware, and the response body — so it must be built with
`GovernorLayer::new` and annotated with the body type the router uses.

Projects **MUST** cover the quota with a test:

```rust
// tests/rate_limit_test.rs
use std::net::{IpAddr, Ipv4Addr};
use std::time::Duration;

#[test]
fn burst_is_exhausted_then_replenished() {
    let config = api_quota();
    let key = IpAddr::V4(Ipv4Addr::new(203, 0, 113, 7));

    for request in 0..30 {
        assert!(config.limiter().check_key(&key).is_ok(), "burst request {request}");
    }
    assert!(config.limiter().check_key(&key).is_err(), "burst not exhausted");

    // One request replenishes every 100 ms.
    std::thread::sleep(Duration::from_millis(150));
    assert!(config.limiter().check_key(&key).is_ok(), "nothing replenished");
}
```

**Why**: The quota only fails visibly under sustained traffic, which no
unit test produces by accident. Driving `config.limiter()` directly checks
the configured numbers without a server or client addresses. Governor
measures time with a Quanta clock, so `tokio::time::pause` does not move
it: the test must sleep for real, which argues for short periods in tests.

### Client Identification and Proxy Trust

The key extractor decides *who* is being limited, so it **MUST** match the
deployment:

| Deployment | Key extractor |
| ---------- | ------------- |
| Service exposed directly | `PeerIpKeyExtractor` (builder default) |
| Behind a proxy that overwrites forwarded headers | `SmartIpKeyExtractor` |
| Authenticated API | Custom extractor over the account or API key |

```rust
// Only when a trusted reverse proxy overwrites X-Forwarded-For and
// X-Real-IP on every inbound request.
use tower_governor::key_extractor::SmartIpKeyExtractor;

pub fn proxied_quota() -> GovernorConfig<SmartIpKeyExtractor, NoOpMiddleware> {
    GovernorConfigBuilder::default()
        .period(Duration::from_millis(100))
        .burst_size(30)
        .key_extractor(SmartIpKeyExtractor)
        .finish()
        .expect("period and burst size are both non-zero")
}
```

**Why**: `SmartIpKeyExtractor` reads `X-Forwarded-For` and `X-Real-IP`,
which are client-supplied unless something at the edge overwrites them. On
a directly exposed service the limiter then keys on a value the caller
chooses: a request carrying `X-Forwarded-For: 198.51.100.1` is limited,
and the next request with `198.51.100.2` starts a fresh bucket, so a
single client walks past any per-IP quota by incrementing a header. Use it
only when the proxy strips inbound copies and writes its own, and pin the
number of hops it appends so an attacker cannot prepend a spoofed entry.

Note also that tower-governor keeps its state in the process. Each replica
enforces the quota separately, so a service behind a load balancer allows
roughly the configured rate multiplied by the number of replicas. Where a
global quota matters, enforce it at the edge or in a shared store, and
treat the in-process limiter as a local safety valve.

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
// src/shared/resilience.rs
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

                // Classify the status inside the protected future, before the
                // body is read: an upstream 500 must count as a failure.
                let response = response
                    .error_for_status()
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

**Do**:

```rust
// error_for_status turns 4xx/5xx into Err, so the breaker records a failure
let response = response.error_for_status()?;
response.text().await
```

**Don't**:

```rust
// A cleanly delivered 503 body resolves to Ok, which *resets* the breaker's
// failure history: the circuit never opens while the upstream is down
let response = client.get(url).send().await?;
response.text().await
```

**Why**: Circuit breakers prevent cascading failures by temporarily rejecting
requests to failing services. Recloser uses a ring buffer for efficient failure
tracking with configurable thresholds.

The classification step is what makes the breaker measure the right thing.
`Response::text` collects the body and never inspects the status, so a service
returning `503` as fast as it can returns `Ok` every time; recloser records
`Poll::Ready(Ok(_))` with `on_success`, so a total upstream outage that is
politely reported looks like a perfectly healthy dependency and the circuit stays
closed. `error_for_status` classifies any `4xx` or `5xx` as an error. Where the
policy needs to be finer — treat `429` and `503` as failures but pass `404`
through as an ordinary answer — match on `response.status()` explicitly, but
make the decision inside the protected future either way.

### Alternative: failsafe-rs

Projects **MAY** use failsafe-rs[^29] where the failure policy needs a
configurable backoff between probe attempts, rather than recloser's single
`open_wait` interval:

```toml
# Cargo.toml
failsafe = "1.3.0"
```

```rust
use std::time::Duration;

// `failsafe::futures::CircuitBreaker` is the async-aware trait; the root
// `failsafe::CircuitBreaker` takes a synchronous `FnOnce() -> Result`.
use failsafe::futures::CircuitBreaker as _;
use failsafe::{backoff, failure_policy, Config, StateMachine};

// `Config::build` returns a `StateMachine`, not a `CircuitBreaker`: the latter
// is a trait, and `failsafe::backoff::Backoff` is a `dyn` alias, so neither can
// be written as `CircuitBreaker<impl Backoff>`.
type ApiBreaker = StateMachine<failure_policy::ConsecutiveFailures<backoff::Exponential>, ()>;

pub fn create_circuit_breaker() -> ApiBreaker {
    let backoff = backoff::exponential(Duration::from_secs(5), Duration::from_secs(60));

    Config::new()
        .failure_policy(failure_policy::consecutive_failures(5, backoff))
        .build()
}

pub async fn call_with_failsafe<F, T, E>(
    breaker: &ApiBreaker,
    future: F,
) -> Result<T, failsafe::Error<E>>
where
    F: Future<Output = Result<T, E>>,
{
    breaker.call(future).await
}
```

**Do**:

```rust
use failsafe::futures::CircuitBreaker as _;   // for futures

failure_policy::consecutive_failures(5, backoff::exponential(
    Duration::from_secs(5),
    Duration::from_secs(60),
))
```

**Don't**:

```rust
// `CircuitBreaker` is a non-generic trait, `consecutive_failures` takes two
// arguments, `Config` has no `success_policy`, and the root trait's `call`
// takes a closure rather than a future
fn create_circuit_breaker() -> CircuitBreaker<impl failsafe::backoff::Backoff> {
    Config::new()
        .failure_policy(failsafe::failure_policy::consecutive_failures(5))
        .success_policy(failsafe::success_policy::consecutive_successes(2))
        .build()
}
```

**Why**: failsafe-rs separates the failure policy from the state machine, so the
half-open probe interval can grow while an upstream stays down instead of
retrying on a fixed timer — which is the reason to reach for it over recloser.

Its API does not match the shape the name suggests. `CircuitBreaker` is a trait,
implemented by the `StateMachine` that `Config::build` returns, and it exists
twice: the root trait wraps a synchronous `FnOnce() -> Result<R, E>`, and
`failsafe::futures::CircuitBreaker` wraps a `TryFuture`. Async callers must
import the second. `consecutive_failures` takes the failure count *and* a
backoff, and there is no `success_policy` on `Config` at all: the number of
successful probes needed to close the circuit is part of the state machine, not
a configurable policy in 1.3.

## Feature Flags

### Runtime Feature Flags with Unleash

Projects **SHOULD** use unleash-api-client[^30] for runtime feature flags:

```toml
# Cargo.toml - a transport feature is REQUIRED; without one there is no
# `default_transport` and the client cannot be built.
unleash-api-client = { version = "0.17.1", features = ["reqwest-client-rustls"] }
enum-map = "2"
```

```rust
// src/shared/feature_flags.rs
use std::sync::Arc;

use enum_map::Enum;
use unleash_api_client::client::{Client, ClientBuilder, FeatureKey};
use unleash_api_client::context::Context;
use tokio_util::{sync::CancellationToken, task::TaskTracker};

/// Feature names are a closed set. The client is generic over the key type, so
/// a mistyped flag is a compile error rather than a silent `false`.
#[allow(non_camel_case_types)]
#[derive(Debug, Clone, Copy, Enum)]
pub enum Features {
    new_dashboard,
    beta_api,
}

impl FeatureKey for Features {
    fn name(self) -> &'static str {
        match self {
            Features::new_dashboard => "new_dashboard",
            Features::beta_api => "beta_api",
        }
    }
}

pub type FeatureClient = Arc<Client<Features>>;

pub fn create_feature_client(
    api_url: &str,
    api_key: &str,
    app_name: &str,
) -> anyhow::Result<FeatureClient> {
    let client = ClientBuilder::default().into_client::<Features>(
        api_url,
        app_name,
        &uuid::Uuid::new_v4().to_string(),
        Some(api_key.to_string()),
    )?;

    Ok(Arc::new(client))
}

/// Registration and polling are separate operations. `poll_for_updates` runs
/// until `stop_poll`, so it belongs on its own tracked task, cancelled during
/// graceful shutdown so the final metrics batch is submitted.
pub async fn start_feature_client(
    client: FeatureClient,
    tasks: &TaskTracker,
    cancel: CancellationToken,
) -> anyhow::Result<()> {
    client
        .register()
        .await
        .map_err(|e| anyhow::anyhow!("Unleash registration failed: {e}"))?;

    let polling = Arc::clone(&client);
    tasks.spawn(async move {
        tokio::select! {
            () = polling.poll_for_updates() => {}
            () = cancel.cancelled() => polling.stop_poll().await,
        }
    });

    Ok(())
}

// Check feature flag
pub fn is_enabled(client: &FeatureClient, feature: Features) -> bool {
    client.is_enabled(feature, None, false)
}

// Check with context (for gradual rollouts, A/B tests)
pub fn is_enabled_for_user(client: &FeatureClient, feature: Features, user_id: &str) -> bool {
    let context = Context { user_id: Some(user_id.to_string()), ..Default::default() };
    client.is_enabled(feature, Some(&context), false)
}
```

```rust
// Usage in handlers
pub async fn get_dashboard(
    State(state): State<AppState>,
    auth: JwtAuth,
) -> Result<Json<Dashboard>, AppError> {
    let dashboard =
        if is_enabled_for_user(&state.features, Features::new_dashboard, &auth.user_id) {
            build_new_dashboard(&state, &auth.user_id).await?
        } else {
            build_legacy_dashboard(&state, &auth.user_id).await?
        };

    Ok(Json(dashboard))
}
```

**Do**:

```rust
let client = ClientBuilder::default()
    .into_client::<Features>(api_url, app_name, &instance_id, Some(api_key.into()))?;
client.register().await?;
tasks.spawn(async move { client.poll_for_updates().await });
```

**Don't**:

```rust
// None of these setters exist, `Client` is generic over its key type, and
// there is no `start`
let client = ClientBuilder::default()
    .api_url(api_url)
    .api_key(api_key)
    .app_name(app_name)
    .build()
    .await?;
client.start().await?;
```

**Why**: Unleash provides runtime feature toggles with gradual rollouts, A/B
testing and user targeting, so a flag can be flipped without a deployment.

The 0.17 client is constructed by converting the builder — `into_client::<F>`
takes the API URL, application name, instance id and optional authorisation in
one call — and it is generic over a `FeatureKey` type, so `Client` alone is not
a type. Startup is two steps that the removed `start` used to hide:
`register()` announces the instance and its strategies once, and
`poll_for_updates()` is a loop that refreshes the toggle set and submits usage
metrics until `stop_poll()` is called. Spawning it without registering means the
server never learns the instance exists; registering without polling means the
flags never change after start-up. Both need to happen, and the polling task
needs cancelling at shutdown or the last metrics window is lost.

A transport feature must be selected explicitly: `default_transport` is
`#[cfg]`-gated on one of the `reqwest-client*` features, so a bare
`unleash-api-client = "0.17.1"` does not compile against this example.

### Environment Feature Flags

Projects whose flags change only at deploy time — a killswitch, a migration
toggle, a maintenance mode — **MAY** read them from the environment instead, and
avoid the network dependency:

```rust
// src/shared/config.rs
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

### Signal Handling

```rust
// src/shared/shutdown.rs
use anyhow::Context as _;
use tokio::signal;

pub async fn shutdown_signal() -> anyhow::Result<()> {
    let ctrl_c = async {
        signal::ctrl_c().await.context("failed to install the Ctrl+C handler")
    };

    #[cfg(unix)]
    let terminate = async {
        // `Signal::recv` takes `&mut self`, so the handler must be mutable and
        // must outlive the `.recv()` call.
        let mut sigterm = signal::unix::signal(signal::unix::SignalKind::terminate())
            .context("failed to install the SIGTERM handler")?;
        sigterm.recv().await;
        anyhow::Ok(())
    };

    #[cfg(not(unix))]
    let terminate = std::future::pending::<anyhow::Result<()>>();

    tokio::select! {
        result = ctrl_c => {
            result?;
            tracing::info!("received SIGINT, starting graceful shutdown");
        }
        result = terminate => {
            result?;
            tracing::info!("received SIGTERM, starting graceful shutdown");
        }
    }

    Ok(())
}
```

**Do**:

```rust
let mut sigterm = signal::unix::signal(SignalKind::terminate())?;
sigterm.recv().await;
```

**Don't**:

```rust
// error[E0596]: cannot borrow `terminate` as mutable, as it is not declared
// as mutable
let terminate = signal::unix::signal(SignalKind::terminate())
    .expect("Failed to install SIGTERM handler");
tokio::select! { _ = terminate.recv() => {} }
```

**Why**: `tokio::signal::unix::Signal::recv` takes `&mut self`, so binding the
handler immutably does not compile. Registering the handler is also fallible —
it fails when the signal cannot be trapped — and `expect` at that point turns a
recoverable start-up problem into a panic inside a shutdown path, where the
stack trace is least useful.

### Coordinated Shutdown

Shutdown **MUST** fail readiness before it stops accepting, **MUST** cancel
every spawned task, and **MUST** bound the wait on outstanding work:

```rust
// src/shared/shutdown.rs
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::time::Duration;

use anyhow::Context as _;
use tokio_util::sync::CancellationToken;
use tokio_util::task::TaskTracker;

pub struct Lifecycle {
    pub health: Arc<HealthState>,
    /// Handed to every worker, WebSocket and poller.
    pub cancel: CancellationToken,
    /// Every long-lived task is spawned through this.
    pub tasks: TaskTracker,
    /// Time the load balancer needs to observe the failing readiness probe.
    pub deregistration_delay: Duration,
    /// Hard ceiling on the whole drain.
    pub shutdown_deadline: Duration,
}

pub async fn run(
    app: axum::Router,
    listener: tokio::net::TcpListener,
    lifecycle: Lifecycle,
) -> anyhow::Result<()> {
    let Lifecycle { health, cancel, tasks, deregistration_delay, shutdown_deadline } = lifecycle;

    let signal_health = Arc::clone(&health);
    let signal_cancel = cancel.clone();

    let server = axum::serve(listener, app).with_graceful_shutdown(async move {
        if let Err(error) = shutdown_signal().await {
            tracing::error!(%error, "signal handling failed; shutting down anyway");
        }

        // 1. Fail readiness so the load balancer stops routing new work.
        signal_health.start_shutdown();
        tokio::time::sleep(deregistration_delay).await;

        // 2. Only now stop accepting. `with_graceful_shutdown` still waits for
        //    in-flight HTTP requests after this future resolves.
        signal_cancel.cancel();
    });

    server.await.context("HTTP server failed")?;

    // 3. Workers and WebSockets saw the same token. Wait for the work actually
    //    to finish, but never past the deadline.
    tasks.close();
    match tokio::time::timeout(shutdown_deadline, tasks.wait()).await {
        Ok(()) => tracing::info!("all tracked tasks completed"),
        Err(_) => tracing::warn!(
            ?shutdown_deadline,
            outstanding = tasks.len(),
            "shutdown deadline reached with tasks still running"
        ),
    }

    // 4. Close resources last, once nothing can still be using them.
    Ok(())
}

pub fn spawn_worker(tasks: &TaskTracker, cancel: CancellationToken) {
    tasks.spawn(async move {
        loop {
            tokio::select! {
                () = cancel.cancelled() => break,
                () = tokio::time::sleep(Duration::from_secs(5)) => {
                    tracing::debug!("worker tick");
                }
            }
        }
    });
}
```

**Do**:

```rust
// Wait for the work, with a ceiling
tasks.close();
tokio::time::timeout(shutdown_deadline, tasks.wait()).await
```

**Don't**:

```rust
// A fixed sleep neither drains anything nor bounds anything: background tasks
// keep running, and every deployment costs the full five seconds
health.start_shutdown();
tokio::time::sleep(Duration::from_secs(5)).await;

// Discards a send failure, a panicked server task and the server's own error
let _ = shutdown_tx.send(());
let _ = server_handle.await;
```

**Why**: The two waits in a shutdown do different jobs and neither substitutes
for the other.

`axum::serve(..).with_graceful_shutdown(..)` already drains HTTP: once the
supplied future resolves, the server stops accepting new connections and then
waits for the requests already in flight. That mechanism is sound and should be
kept. What the sleep before it buys is different — it is deregistration time,
the gap between the readiness probe starting to fail and the load balancer
noticing, during which the process must keep accepting or clients see connection
refusals. Calling that sleep "waiting for in-flight requests to complete" is
what makes people delete it, or set it to the request timeout, both of which are
wrong.

Nothing in that mechanism touches spawned tasks. Background workers, WebSocket
send and receive loops, the Unleash poller and the session-expiry sweeper all
outlive the server future, so a process can report a clean shutdown while a job
is halfway through a database transaction. A `CancellationToken` shared by all
of them makes cancellation a single call, and `TaskTracker` turns "did they
finish?" into an awaitable rather than a guess. Wrapping that in `timeout` is
what stops one stuck task from holding the pod past its
`terminationGracePeriodSeconds`, at which point the runtime sends `SIGKILL` and
none of the cleanup runs at all.

Failures during shutdown are worth surfacing rather than discarding with `let _
=`. A server task that panicked, a channel with no receivers, a database that
refused to close: each of them changes what the operator should do next, and
each of them is invisible if the result is dropped.

### Kubernetes Health Probes

```rust
// src/features/health/handlers.rs
use axum::{extract::State, http::StatusCode, routing::get, Router};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;

pub struct HealthState {
    pub ready: AtomicBool,
    pub live: AtomicBool,
}

impl HealthState {
    pub fn new() -> Arc<Self> {
        Arc::new(Self { ready: AtomicBool::new(true), live: AtomicBool::new(true) })
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

**Why**: Liveness and readiness answer different questions, and conflating them
is how a rolling deployment turns into an outage. Liveness failing gets the pod
restarted; readiness failing only removes it from the load balancer. During
shutdown exactly one of them must change: readiness goes false so traffic drains
away, while liveness stays true so the orchestrator does not kill the process
that is trying to finish its work. Set `deregistration_delay` from the
platform's probe interval — with a 2-second `periodSeconds` and a
`failureThreshold` of 2, five seconds is enough; a longer interval needs a
longer delay.

Give the process the whole grace period to work with:
`terminationGracePeriodSeconds` **MUST** exceed `deregistration_delay` plus
`shutdown_deadline`, or the platform sends `SIGKILL` in the middle of the drain
that the code carefully arranged.

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
utoipa = { version = "5.5.0", features = ["axum_extras"] }
utoipa-swagger-ui = { version = "9.0.2", features = ["axum"] }
utoipa-redoc = { version = "6.0.0", features = ["axum"] }
```

**Do**:

```toml
utoipa-swagger-ui = { version = "9.0.2", features = ["axum"] }
utoipa-redoc = { version = "6.0.0", features = ["axum"] }
```

**Don't**:

```toml
# Both majors integrate with Axum 0.7, not the 0.8 this guide targets
utoipa-swagger-ui = { version = "8", features = ["axum"] }
utoipa-redoc = { version = "5", features = ["axum"] }
```

**Why**: The three crates version independently. utoipa is on 5.5.0, but its
Swagger UI and ReDoc companions have each had a major release since: the `"8"`
range resolves to `utoipa-swagger-ui` 8.1.0, which declares `axum ^0.7`, and the
`"5"` range does the same for ReDoc. Cargo does not report that as an error — it
compiles Axum 0.7 alongside 0.8 and then fails when the `Router` returned by
`SwaggerUi` cannot be merged into the 0.8 router, because the two `Router` types
are unrelated. Swagger UI 9.0.2 and ReDoc 6.0.0 depend on Axum 0.8, which is
what makes `.merge()` type-check.

Note also that `utoipa-swagger-ui` 8.1.1 is yanked. Yanking does not remove the
whole major — Cargo still selects 8.1.0 from a `"8"` range — so the yank is not
what fixes this; the major upgrade is.

### Documenting Handlers

```rust
// src/features/users/handlers.rs
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
    /// Validated at the type level; see Documenting Password Rules below.
    #[schema(example = "a wandering albatross")]
    pub password: Password,
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

#### Documenting Password Rules

A `min_length` annotation documents the contract; it does not enforce it. A
handler whose field is a plain `String` accepts a five-character password no
matter what the schema says, and the OpenAPI document then advertises a rule
the API does not apply.

The rule and its enforcement **MUST** therefore live in one place. Projects
**MUST** parse the password into a validated type at the edge, and **MUST NOT**
carry an unvalidated `String` past the deserialiser:

```rust
// src/shared/password.rs
use std::fmt;

use serde::{Deserialize, Deserializer};

/// Single-factor minimum from NIST SP 800-63B.
pub const MIN_PASSWORD_CHARS: usize = 15;
/// A floor on what the verifier accepts, not a cap imposed on the user.
pub const MAX_PASSWORD_CHARS: usize = 256;

#[derive(Debug, thiserror::Error, PartialEq, Eq)]
pub enum PasswordError {
    #[error("password must be at least {MIN_PASSWORD_CHARS} characters")]
    TooShort,

    #[error("password must be at most {MAX_PASSWORD_CHARS} characters")]
    TooLong,

    #[error("password appears on a blocklist of breached or guessable values")]
    Blocked,
}

/// A password that has passed every rule below. There is no way to build one
/// that has not: the only constructor is `new`, and `Deserialize` routes
/// through it.
#[derive(Clone)]
pub struct Password(String);

impl Password {
    pub fn new(raw: impl Into<String>, context: &[&str]) -> Result<Self, PasswordError> {
        let raw: String = raw.into();

        // Count code points, not bytes: "pässwörtchen-ährenlese" is 22
        // characters but 25 bytes, and byte counting would reject valid input.
        let chars = raw.chars().count();

        if chars < MIN_PASSWORD_CHARS {
            return Err(PasswordError::TooShort);
        }
        if chars > MAX_PASSWORD_CHARS {
            return Err(PasswordError::TooLong);
        }
        if is_blocked(&raw, context) {
            return Err(PasswordError::Blocked);
        }

        Ok(Self(raw))
    }

    /// Deliberately not `Deref` or `AsRef`: the secret leaves only for hashing.
    pub fn expose(&self) -> &str {
        &self.0
    }
}

// Neither `Debug` nor `Display` may print the secret, or it reaches a log the
// moment anyone derives `Debug` on a struct that contains it.
impl fmt::Debug for Password {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("Password(<redacted>)")
    }
}

impl<'de> Deserialize<'de> for Password {
    fn deserialize<D: Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        let raw = String::deserialize(deserializer)?;
        // Axum's `Json` rejection turns this into 422 with the message above.
        Password::new(raw, &[]).map_err(serde::de::Error::custom)
    }
}

fn is_blocked(candidate: &str, context: &[&str]) -> bool {
    // In production this queries a breached-password set, not a literal.
    const BREACHED: &[&str] = &["password123456789", "qwertyuiopasdfgh"];

    let lowered = candidate.to_lowercase();
    BREACHED.iter().any(|entry| *entry == lowered)
        || context
            .iter()
            .any(|term| !term.is_empty() && lowered.contains(&term.to_lowercase()))
}
```

Generate the published schema from the same constants, so the document and the
check cannot drift:

```rust
impl utoipa::PartialSchema for Password {
    fn schema() -> utoipa::openapi::RefOr<utoipa::openapi::schema::Schema> {
        utoipa::openapi::ObjectBuilder::new()
            .schema_type(utoipa::openapi::schema::SchemaType::Type(
                utoipa::openapi::Type::String,
            ))
            .format(Some(utoipa::openapi::SchemaFormat::KnownFormat(
                utoipa::openapi::KnownFormat::Password,
            )))
            .min_length(Some(MIN_PASSWORD_CHARS))
            .max_length(Some(MAX_PASSWORD_CHARS))
            .description(Some("Single-factor password; NIST SP 800-63B rules apply"))
            .into()
    }
}

impl utoipa::ToSchema for Password {}
```

**Do**:

```rust
// The type carries the contract; the handler cannot forget to check
pub struct CreateUserRequest {
    pub password: Password,
}
```

**Don't**:

```rust
// The annotation is documentation. `"short"` deserialises and is persisted.
pub struct CreateUserRequest {
    #[schema(min_length = 15)]
    pub password: String,
}
```

The documented minimum **MUST** be at least 15 characters where a
password is the only authentication factor; 8 characters is acceptable
only when the password is one factor of multi-factor authentication.

Password handling **MUST** also:

- accept at least 64 characters, and all printable ASCII, the space
  character, and Unicode, counting each code point as one character;
- reject passwords found on a blocklist of breached, common, and
  context-specific values, such as the service or account name;
- verify the password in full, without truncation;
- impose no composition rules and no periodic expiry, forcing a change
  only on evidence of compromise.

Projects **MUST** test the boundary rather than trusting the annotation:

```rust
// tests/password.rs
#[test]
fn five_character_password_is_rejected() {
    let body = r#"{"email":"a@example.com","name":"Alice","password":"short"}"#;

    let result: Result<CreateUserRequest, _> = serde_json::from_str(body);

    assert!(result.is_err(), "five-character password still deserialised");
}

#[test]
fn boundary_is_exactly_the_documented_minimum() {
    assert!(Password::new("a".repeat(14), &[]).is_err());
    assert!(Password::new("a".repeat(15), &[]).is_ok());
}

#[test]
fn debug_never_prints_the_secret() {
    let password = Password::new("a wandering albatross", &[]).unwrap();
    assert_eq!(format!("{password:?}"), "Password(<redacted>)");
}
```

**Why**: NIST SP 800-63B requires a 15-character minimum for single-factor
passwords and permits 8 only within multi-factor authentication[^32]. An
undifferentiated `min 8` reads as an endorsement of an eight-character
single-factor password. The 64-character figure is a floor on what
verifiers should accept, not a cap that must be imposed; capping shorter
than that breaks password managers and passphrases. Composition rules and
scheduled rotation are prohibited rather than merely discouraged, because
both push users towards predictable variants.

Stating the rule in prose and annotating the schema does not implement it.
Deserialising into `String` and validating later gives every future handler a
chance to forget, and the compiler cannot help, because an unchecked password
and a checked one have the same type. Parsing into `Password` moves the rule
into the type: a handler that receives one is holding a value that has already
passed, and there is no constructor that skips the check. Counting `chars()`
rather than `len()` is what makes the Unicode requirement true rather than
aspirational — `len()` would reject a 22-character German passphrase as though
it were 25 characters.

### OpenAPI Specification

```rust
// src/shared/openapi.rs
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
        // Swagger UI at /swagger-ui, serving the document at the URL below
        .merge(SwaggerUi::new("/swagger-ui")
            .url("/api-docs/openapi.json", ApiDoc::openapi()))
        // ReDoc at /redoc
        .merge(Redoc::with_url("/redoc", ApiDoc::openapi()))
        .with_state(state);

    Ok(app)
}
```

**Why**: `SwaggerUi::url` registers a `GET` route that serves the supplied
document at that path, so adding `.route("/api-docs/openapi.json", get(...))`
registers a second handler for the same method and path. Axum rejects that
while the router is assembled: `Overlapping method route. Handler for
'GET /api-docs/openapi.json' already exists`. Register the document once,
through Swagger UI or through an explicit route, never both — the
[router construction test](#router-construction-tests) catches the
regression before deployment.

### Error Response Schemas

```rust
// src/shared/error.rs
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

[^2]: [Tower `ServiceBuilder`: Order](https://docs.rs/tower/0.5.3/tower/struct.ServiceBuilder.html#order) - "Layers that are added first will be called with the request first"

[^3]: [Hyper](https://hyper.rs/) - Fast and safe HTTP implementation for Rust

[^4]: [TechEmpower Framework Benchmarks](https://github.com/TechEmpower/FrameworkBenchmarks/releases/tag/R23) - Round 23, published March 2025; the repository was archived in 2026 and no further rounds will be published

[^5]: [Actix-web](https://actix.rs/) - Powerful, pragmatic, and extremely fast web framework for Rust

[^6]: [Rocket: Launching](https://rocket.rs/guide/v0.5/overview/#launching) - Rocket 0.5 starts a multi-threaded asynchronous server

[^7]: [thiserror](https://github.com/dtolnay/thiserror) - Derive macros for the standard library's `std::error::Error` trait

[^8]: [anyhow](https://github.com/dtolnay/anyhow) - Flexible concrete Error type built on `std::error::Error`

[^9]: [SQLx](https://github.com/transact-rs/sqlx) - Async, pure Rust SQL crate with compile-time checked queries (the `launchbadge/sqlx` URL now redirects here)

[^10]: [axum-login](https://github.com/maxcountryman/axum-login) - User identification, authentication, and authorization for Axum

[^11]: [jsonwebtoken](https://github.com/Keats/jsonwebtoken) - JWT library for Rust with support for all standard algorithms

[^12]: [casbin-rs](https://github.com/apache/casbin-rs) - Authorization library supporting ACL, RBAC, ABAC models (the `casbin/casbin-rs` URL now redirects here)

[^13]: [tower-http](https://github.com/tower-rs/tower-http) - HTTP-specific Tower middleware including auth, compression, and tracing

[^14]: [Axum WebSocket](https://docs.rs/axum/0.8.9/axum/extract/ws/index.html) - Native WebSocket support in Axum

[^15]: [tokio-tungstenite](https://github.com/snapview/tokio-tungstenite) - Tokio bindings for the Tungstenite WebSocket library

[^16]: [tracing](https://github.com/tokio-rs/tracing) - Application-level tracing for Rust with structured, contextual logging

[^17]: [tracing-subscriber](https://docs.rs/tracing-subscriber/0.3.23/tracing_subscriber/) - Utilities for implementing and composing tracing subscribers

[^18]: [axum-prometheus](https://crates.io/crates/axum-prometheus) - Prometheus metrics middleware for Axum

[^19]: [metrics](https://github.com/metrics-rs/metrics) - High-quality, batteries-included metrics library for Rust

[^20]: [metrics-exporter-prometheus](https://docs.rs/metrics-exporter-prometheus/0.18.3/metrics_exporter_prometheus/) - Prometheus exporter for the metrics crate

[^21]: [tracing-opentelemetry](https://docs.rs/tracing-opentelemetry/0.33.0/tracing_opentelemetry/) - OpenTelemetry integration for tracing

[^22]: [apalis](https://github.com/apalis-dev/apalis) - Type-safe, extensible background job processing library for Rust (the `geofmureithi/apalis` URL now redirects here)

[^23]: [rusty-sidekiq](https://github.com/film42/sidekiq-rs) - Sidekiq-compatible job processing for Rust

[^24]: [moka](https://github.com/moka-rs/moka) - High-performance concurrent caching library for Rust

[^25]: [redis-rs](https://github.com/redis-rs/redis-rs) - Redis client library for Rust

[^26]: [deadpool-redis](https://docs.rs/deadpool-redis/0.23.1/deadpool_redis/) - Async Redis connection pool for Tokio

[^27]: [tower-governor](https://github.com/benwis/tower-governor) - Rate limiting middleware for Tower/Axum using the governor crate

[^28]: [recloser](https://github.com/lerouxrgd/recloser) - Concurrent circuit breaker implemented with ring buffers

[^29]: [failsafe-rs](https://github.com/dmexe/failsafe-rs) - Circuit breaker implementation with configurable failure policies

[^30]: [unleash-api-client](https://github.com/Unleash/unleash-rust-sdk) - Unleash feature flag client SDK for Rust

[^31]: [utoipa](https://github.com/juhaku/utoipa) - Auto-generate OpenAPI documentation from Rust code with compile-time validation

[^32]: [NIST SP 800-63B, Authenticator and Verifier Requirements](https://pages.nist.gov/800-63-4/sp800-63b/authenticators/#passwordver) - Password length, blocklist, and composition requirements

[^33]: [RFC 9457, Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457.html) - Standard `application/problem+json` error representation

[^34]: [OWASP WebSocket Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/WebSocket_Security_Cheat_Sheet.html) - Handshake authentication, origin validation, and message controls
