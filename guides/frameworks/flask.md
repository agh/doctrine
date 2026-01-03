# Flask Style Guide

> [Doctrine](../../README.md) > [Frameworks](../README.md) > Flask

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119][rfc2119].

[rfc2119]: https://datatracker.ietf.org/doc/html/rfc2119

Extends [Python style guide](../languages/python.md) with Flask-specific conventions.

**Target Version**: Flask 3.x with Python 3.14

## Quick Reference

All Python tooling applies. Additional considerations:

| Task | Tool | Command |
| ---- | ---- | ------- |
| Install | uv | `uv add flask` |
| Run dev | Flask CLI | `flask run --debug` |
| Test | pytest + Flask test client | `pytest` |
| Auth (session) | Flask-Login | `uv add flask-login` |
| Auth (OAuth) | Authlib | `uv add authlib` |
| Auth (JWT) | PyJWT | `uv add pyjwt[crypto]` |
| Permissions | Flask-Principal | `uv add flask-principal` |
| WebSocket | Flask-SocketIO | `uv add flask-socketio gevent` |
| Profiling | py-spy | `py-spy top --pid PID` |
| Metrics | prometheus_client | `uv add prometheus-client` |
| Background jobs | Celery | `uv add celery[redis]` |
| Simple queues | RQ | `uv add flask-rq2` |
| Async views | Flask 2.0+ | `uv add "flask[async]"` |
| Caching | Flask-Caching | `uv add flask-caching` |
| Rate limiting | Flask-Limiter | `uv add flask-limiter` |
| Circuit breaker | pybreaker | `uv add pybreaker` |
| Feature flags | Flask-FeatureFlags | `uv add flask-featureflags` |

## Why Flask?

Flask[^1] is a lightweight, flexible microframework ideal for small-to-medium
applications, APIs, and prototypes. It provides minimal abstractions while
allowing extension through a rich ecosystem.

Use Flask when you need simplicity and flexibility; consider Django[^2] for
larger, more structured applications with built-in admin, ORM, and
authentication. Consider FastAPI[^3] for high-performance async APIs.

## Project Structure

Projects **MUST** use the application factory pattern:

```python
# src/myapp/__init__.py
from flask import Flask

def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)

    if config:
        app.config.update(config)

    # Initialize extensions
    from myapp.extensions import db, migrate
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    from myapp.auth import auth_bp
    from myapp.api import api_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(api_bp, url_prefix="/api")

    return app
```

**Why**: The application factory pattern enables multiple app instances with
different configurations, facilitates testing, and defers extension
initialization until configuration is loaded.

### Recommended Structure

```text
my_app/
├── src/
│   └── myapp/
│       ├── __init__.py          # Application factory
│       ├── extensions.py        # Extension instances
│       ├── config.py            # Configuration classes
│       ├── models/
│       │   ├── __init__.py
│       │   └── user.py
│       ├── auth/
│       │   ├── __init__.py      # Blueprint definition
│       │   └── routes.py
│       ├── api/
│       │   ├── __init__.py
│       │   └── routes.py
│       └── templates/
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   └── test_api.py
├── pyproject.toml
└── .env
```

## Blueprints for Modularity

Projects **MUST** use blueprints[^4] to organize routes into logical modules:

```python
# src/myapp/auth/routes.py
from flask import Blueprint, request, jsonify

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["POST"])
def login() -> tuple[dict, int]:
    credentials = request.get_json()
    # Handle authentication
    return {"token": token}, 200

@auth_bp.route("/logout", methods=["POST"])
def logout() -> tuple[dict, int]:
    # Handle logout
    return {"message": "Logged out"}, 200
```

```python
# src/myapp/auth/__init__.py
from myapp.auth.routes import auth_bp

__all__ = ["auth_bp"]
```

**Why**: Blueprints organize code by feature, enable route prefixes and
middleware per module, and make large applications maintainable by separating
concerns.

## Configuration Management

Projects **MUST** use environment-based configuration:

```python
# src/myapp/config.py
import os

class Config:
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-key-change-in-prod")
    SQLALCHEMY_DATABASE_URI: str = os.environ["DATABASE_URL"]
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

class DevelopmentConfig(Config):
    DEBUG: bool = True

class ProductionConfig(Config):
    DEBUG: bool = False

class TestingConfig(Config):
    TESTING: bool = True
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///:memory:"
```

```python
# src/myapp/__init__.py
def create_app(config_name: str = "development") -> Flask:
    app = Flask(__name__)

    configs = {
        "development": "myapp.config.DevelopmentConfig",
        "production": "myapp.config.ProductionConfig",
        "testing": "myapp.config.TestingConfig",
    }
    app.config.from_object(configs.get(config_name, configs["development"]))

    return app
```

**Why**: Environment-based configuration separates deployment concerns from
code, prevents secrets from being committed, and enables different settings
per environment.

## Testing with pytest

Projects **MUST** test Flask applications using pytest with Flask's test client:

```python
# tests/conftest.py
import pytest
from myapp import create_app
from myapp.extensions import db

@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()
```

```python
# tests/test_auth.py
def test_login_success(client) -> None:
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    assert "token" in response.json

def test_login_invalid_credentials(client) -> None:
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "wrong"
    })
    assert response.status_code == 401
```

**Why**: Flask's test client enables route testing without running a server.
pytest fixtures provide isolated test database state and reusable app instances.

## Extensions Ecosystem

Projects **SHOULD** use well-maintained Flask extensions:

| Extension | Purpose | Install |
| --------- | ------- | ------- |
| Flask-SQLAlchemy[^5] | ORM integration | `uv add flask-sqlalchemy` |
| Flask-Migrate[^6] | Database migrations | `uv add flask-migrate` |
| Flask-Login[^7] | User session management | `uv add flask-login` |
| Flask-WTF[^8] | Form validation | `uv add flask-wtf` |
| Flask-CORS[^9] | CORS handling | `uv add flask-cors` |

```python
# src/myapp/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
```

**Why**: Flask's extension ecosystem provides battle-tested solutions for
common needs while maintaining the framework's lightweight philosophy.

## Error Handling

Projects **SHOULD** implement consistent error handling:

```python
# src/myapp/__init__.py
from flask import jsonify

def create_app(config_name: str = "development") -> Flask:
    app = Flask(__name__)
    # ... configuration ...

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"error": "Bad request", "message": str(error)}), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Internal server error"}), 500

    return app
```

## Request Validation

Projects **SHOULD** validate request data:

```python
from flask import Blueprint, request, jsonify
from pydantic import BaseModel, EmailStr, ValidationError

api_bp = Blueprint("api", __name__)

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    age: int | None = None

@api_bp.route("/users", methods=["POST"])
def create_user():
    try:
        data = UserCreate(**request.get_json())
    except ValidationError as e:
        return jsonify({"errors": e.errors()}), 400

    # Create user with validated data
    return jsonify({"user": data.model_dump()}), 201
```

## Security

Projects **MUST** implement comprehensive security including authentication,
authorization, and token management.

### Why Security

Security is foundational for any production application. Flask-Login[^7]
handles session management, Authlib[^10] provides OAuth 2.0/OpenID Connect
integration, PyJWT[^11] enables stateless token authentication, and
Flask-Principal[^12] manages role-based permissions. Using established
libraries prevents common security vulnerabilities.

### Authentication with Flask-Login

Projects **MUST** use Flask-Login for session-based authentication:

```python
# src/myapp/extensions.py
from flask_login import LoginManager

login_manager = LoginManager()
login_manager.login_view = "auth.login"
```

```python
# src/myapp/models/user.py
from flask_login import UserMixin
from myapp.extensions import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    fs_uniquifier = db.Column(db.String(64), unique=True, nullable=False)

    def get_id(self) -> str:
        return self.fs_uniquifier  # Enables session invalidation without changing user ID
```

```python
# src/myapp/__init__.py
from myapp.extensions import login_manager
from myapp.models.user import User

@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    return User.query.filter_by(fs_uniquifier=user_id).first()
```

### JWT Token Authentication with PyJWT

Projects **SHOULD** use RS256 asymmetric signing for JWT tokens in distributed systems:

```python
# src/myapp/auth/tokens.py
import jwt
from datetime import datetime, timedelta, timezone
from flask import current_app

def create_access_token(user_id: int, expires_minutes: int = 15) -> str:
    """Create a short-lived access token using RS256."""
    payload = {
        "sub": str(user_id),
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=expires_minutes),
        "type": "access",
    }
    return jwt.encode(
        payload,
        current_app.config["JWT_PRIVATE_KEY"],
        algorithm="RS256",
    )

def verify_access_token(token: str) -> dict | None:
    """Verify token using public key."""
    try:
        return jwt.decode(
            token,
            current_app.config["JWT_PUBLIC_KEY"],
            algorithms=["RS256"],  # Explicitly restrict algorithm
        )
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
```

```python
# src/myapp/auth/decorators.py
from functools import wraps
from flask import request, jsonify
from myapp.auth.tokens import verify_access_token

def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing authorization header"}), 401

        token = auth_header.split(" ", 1)[1]
        payload = verify_access_token(token)
        if payload is None:
            return jsonify({"error": "Invalid or expired token"}), 401

        request.current_user_id = int(payload["sub"])
        return f(*args, **kwargs)
    return decorated
```

### OAuth 2.0 with Authlib

Projects **SHOULD** use Authlib for OAuth 2.0 and OpenID Connect integration:

```python
# src/myapp/extensions.py
from authlib.integrations.flask_client import OAuth

oauth = OAuth()
```

```python
# src/myapp/__init__.py
def create_app(config_name: str = "development") -> Flask:
    app = Flask(__name__)
    # ... configuration ...

    from myapp.extensions import oauth
    oauth.init_app(app)

    oauth.register(
        name="google",
        client_id=app.config["GOOGLE_CLIENT_ID"],
        client_secret=app.config["GOOGLE_CLIENT_SECRET"],
        server_metadata_url=(
            "https://accounts.google.com/.well-known/openid-configuration"
        ),
        client_kwargs={"scope": "openid email profile"},
    )

    return app
```

```python
# src/myapp/auth/routes.py
from flask import redirect, url_for, session
from myapp.extensions import oauth

@auth_bp.route("/login/google")
def google_login():
    redirect_uri = url_for("auth.google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@auth_bp.route("/callback/google")
def google_callback():
    token = oauth.google.authorize_access_token()
    userinfo = token.get("userinfo")
    # Create or update user from userinfo
    session["user_email"] = userinfo["email"]
    return redirect(url_for("main.index"))
```

### Role-Based Authorization with Flask-Principal

Projects **SHOULD** use Flask-Principal for permission management:

```python
# src/myapp/extensions.py
from flask_principal import Principal, Permission, RoleNeed

principals = Principal()
admin_permission = Permission(RoleNeed("admin"))
editor_permission = Permission(RoleNeed("editor"))
```

```python
# src/myapp/__init__.py
from flask_principal import identity_loaded, UserNeed, RoleNeed
from flask_login import current_user

def create_app(config_name: str = "development") -> Flask:
    app = Flask(__name__)
    # ... configuration ...

    from myapp.extensions import principals
    principals.init_app(app)

    @identity_loaded.connect_via(app)
    def on_identity_loaded(sender, identity):
        identity.user = current_user
        if hasattr(current_user, "id"):
            identity.provides.add(UserNeed(current_user.id))
        if hasattr(current_user, "roles"):
            for role in current_user.roles:
                identity.provides.add(RoleNeed(role.name))

    return app
```

```python
# src/myapp/admin/routes.py
from flask import abort
from myapp.extensions import admin_permission

@admin_bp.route("/dashboard")
@login_required
def admin_dashboard():
    if not admin_permission.can():
        abort(403)
    return render_template("admin/dashboard.html")

# Or use as decorator
@admin_bp.route("/users")
@login_required
@admin_permission.require(http_exception=403)
def manage_users():
    return render_template("admin/users.html")
```

## WebSocket

Projects requiring real-time communication **SHOULD** use Flask-SocketIO[^13].

### Why WebSocket

WebSocket enables bidirectional communication between client and server,
essential for chat applications, live updates, and collaborative features.
Flask-SocketIO provides a clean abstraction over WebSocket with fallback
support and room-based messaging.

### Server Selection

Projects **SHOULD** use gevent for production deployments as eventlet is now deprecated:

| Server | Status | Use Case |
| ------ | ------ | -------- |
| gevent | Active, recommended | Production with high concurrency |
| Threading mode | Stable | CPU-heavy apps, maximum library compatibility |
| eventlet | Deprecated | Legacy applications only |

### Configuration

```python
# src/myapp/extensions.py
from flask_socketio import SocketIO

socketio = SocketIO()
```

```python
# src/myapp/__init__.py
def create_app(config_name: str = "development") -> Flask:
    app = Flask(__name__)
    # ... configuration ...

    from myapp.extensions import socketio
    socketio.init_app(
        app,
        message_queue=app.config.get("SOCKETIO_MESSAGE_QUEUE"),  # Redis for multi-process
        cors_allowed_origins=app.config.get("CORS_ORIGINS", "*"),
        logger=app.config.get("DEBUG", False),
        engineio_logger=app.config.get("DEBUG", False),
    )

    return app
```

```python
# src/myapp/realtime/events.py
from flask_socketio import emit, join_room, leave_room
from myapp.extensions import socketio

@socketio.on("connect")
def handle_connect():
    emit("status", {"message": "Connected"})

@socketio.on("join")
def handle_join(data: dict):
    room = data["room"]
    join_room(room)
    emit("status", {"message": f"Joined {room}"}, to=room)

@socketio.on("message")
def handle_message(data: dict):
    room = data.get("room", "general")
    emit("message", data, to=room, include_self=False)
```

### Production Deployment

Projects **MUST** use gevent workers with Gunicorn for production:

```bash
# Install dependencies
uv add flask-socketio gevent gevent-websocket

# Run with gevent worker
gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker \
    -w 1 --bind 0.0.0.0:5000 "myapp:create_app()"
```

Projects using multiple worker processes **MUST** configure a message queue:

```python
# src/myapp/config.py
class ProductionConfig(Config):
    SOCKETIO_MESSAGE_QUEUE = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
```

### Monkey Patching

Projects using gevent **MUST** apply monkey patching at the top of the entry point:

```python
# wsgi.py
from gevent import monkey
monkey.patch_all()

from myapp import create_app, socketio

app = create_app("production")

if __name__ == "__main__":
    socketio.run(app)
```

## Performance

Projects **SHOULD** implement performance monitoring and profiling.

### Why Performance Monitoring

Performance issues in production require visibility into application behavior.
Flask-Profiler[^14] provides request-level profiling with a web UI, py-spy[^15]
enables live process profiling without code changes, and prometheus_client[^16]
exposes metrics for monitoring infrastructure.

### Flask-Profiler for Development

Projects **MAY** use Flask-Profiler during development:

```python
# src/myapp/__init__.py
def create_app(config_name: str = "development") -> Flask:
    app = Flask(__name__)
    # ... configuration ...

    if app.config.get("PROFILING_ENABLED"):
        import flask_profiler
        app.config["flask_profiler"] = {
            "enabled": True,
            "storage": {"engine": "sqlite"},
            "basicAuth": {"enabled": True, "username": "admin", "password": "secret"},
            "ignore": ["^/static/.*"],
        }
        flask_profiler.init_app(app)

    return app
```

### py-spy for Production Profiling

Projects **SHOULD** use py-spy for production performance analysis:

```bash
# Attach to running Flask process (no code changes required)
py-spy top --pid $(pgrep -f "gunicorn.*myapp")

# Generate flame graph
py-spy record -o profile.svg --pid $(pgrep -f "gunicorn.*myapp")
```

### Prometheus Metrics

Projects **SHOULD** expose Prometheus metrics for production monitoring:

```python
# src/myapp/extensions.py
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter(
    "flask_request_total",
    "Total request count",
    ["method", "endpoint", "status"],
)
REQUEST_LATENCY = Histogram(
    "flask_request_latency_seconds",
    "Request latency",
    ["method", "endpoint"],
)
```

```python
# src/myapp/__init__.py
from time import time
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

def create_app(config_name: str = "development") -> Flask:
    app = Flask(__name__)
    # ... configuration ...

    from myapp.extensions import REQUEST_COUNT, REQUEST_LATENCY

    @app.before_request
    def before_request():
        request.start_time = time()

    @app.after_request
    def after_request(response):
        latency = time() - getattr(request, "start_time", time())
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.endpoint or "unknown",
            status=response.status_code,
        ).inc()
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.endpoint or "unknown",
        ).observe(latency)
        return response

    @app.route("/metrics")
    def metrics():
        return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}

    return app
```

## Background Jobs

Projects with long-running tasks **MUST** use a task queue.

### Why Task Queues

HTTP requests should complete quickly. Background task queues offload expensive
operations like sending emails, processing files, or calling external APIs.
This prevents request timeouts and improves user experience.

### Task Queue Comparison

| Feature | Celery[^17] | RQ[^18] | Huey[^19] |
| ------- | ----------- | ------- | --------- |
| Complexity | Higher | Lower | Lower |
| Brokers | Redis, RabbitMQ, etc. | Redis only | Redis |
| Scheduling | Full crontab | Basic | Crontab-like |
| Monitoring | Flower UI | rq-dashboard | Built-in |
| Best for | Large scale, complex workflows | Simple queues | Lightweight apps |

### Celery with Application Factory

Projects using Celery **MUST** integrate with the application factory pattern:

```python
# src/myapp/extensions.py
from celery import Celery, Task

def celery_init_app(app) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app
```

```python
# src/myapp/config.py
class Config:
    CELERY = {
        "broker_url": os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0"),
        "result_backend": os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
        "task_ignore_result": True,
        "task_serializer": "json",
        "result_serializer": "json",
        "accept_content": ["json"],
    }
```

```python
# src/myapp/__init__.py
from myapp.extensions import celery_init_app

def create_app(config_name: str = "development") -> Flask:
    app = Flask(__name__)
    app.config.from_object(configs[config_name])
    celery_init_app(app)
    return app
```

```python
# src/myapp/tasks.py
from celery import shared_task

@shared_task(bind=True, max_retries=3)
def send_email(self, to: str, subject: str, body: str) -> None:
    """Send email in background with retry logic."""
    try:
        # Send email logic
        pass
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
```

### RQ for Simpler Queues

Projects with simpler requirements **MAY** use RQ:

```python
# src/myapp/extensions.py
from flask_rq2 import RQ

rq = RQ()
```

```python
# src/myapp/tasks.py
from myapp.extensions import rq

@rq.job
def process_upload(file_id: int) -> None:
    """Process uploaded file in background."""
    # Processing logic
    pass
```

```bash
# Run RQ worker
rq worker --with-scheduler
```

## Async Views

Projects using Flask 2.0+ **MAY** use async views for I/O-bound operations.

### Why Async Views

Async views enable concurrent I/O operations within a single request, improving
throughput for requests that call multiple external services. However, Flask
remains WSGI-based; for fully async applications, consider Quart[^20] or
FastAPI[^3].

### Installation

```bash
uv add "flask[async]"
```

### Basic Async Views

```python
# src/myapp/api/routes.py
import asyncio
import aiohttp
from flask import Blueprint, jsonify

api_bp = Blueprint("api", __name__)

@api_bp.route("/aggregate")
async def aggregate_data():
    """Fetch data from multiple sources concurrently."""
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_service(session, "https://api.service1.com/data"),
            fetch_service(session, "https://api.service2.com/data"),
            fetch_service(session, "https://api.service3.com/data"),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    return jsonify({"results": [r for r in results if not isinstance(r, Exception)]})

async def fetch_service(session: aiohttp.ClientSession, url: str) -> dict:
    async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
        return await resp.json()
```

### Limitations

Projects **SHOULD** be aware of async limitations in Flask:

- Flask extensions may not be async-compatible
- Performance is lower than async-first frameworks (Quart, FastAPI)
- Background tasks should use task queues, not `asyncio.create_task()`
- Only `asyncio` is supported (not `trio` or `curio`)

```python
# Do: Use task queue for background work
@api_bp.route("/process")
async def process_request():
    data = await fetch_external_data()
    send_notification.delay(data)  # Celery task
    return jsonify({"status": "processing"})

# Don't: Spawn background tasks directly
@api_bp.route("/process")
async def process_request_wrong():
    data = await fetch_external_data()
    asyncio.create_task(send_notification(data))  # Task may be cancelled!
    return jsonify({"status": "processing"})
```

## Caching

Projects **SHOULD** implement caching for frequently accessed data.

### Why Caching

Caching reduces database load and improves response times. Flask-Caching[^21]
provides a unified interface with multiple backends. Redis is recommended for
production due to its persistence, atomic operations, and distributed support.

### Configuration

```python
# src/myapp/extensions.py
from flask_caching import Cache

cache = Cache()
```

```python
# src/myapp/config.py
class Config:
    CACHE_TYPE = "RedisCache"
    CACHE_REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    CACHE_DEFAULT_TIMEOUT = 300
    CACHE_KEY_PREFIX = "myapp_"

class DevelopmentConfig(Config):
    CACHE_TYPE = "SimpleCache"  # In-memory for development

class TestingConfig(Config):
    CACHE_TYPE = "NullCache"  # Disable caching in tests
```

```python
# src/myapp/__init__.py
from myapp.extensions import cache

def create_app(config_name: str = "development") -> Flask:
    app = Flask(__name__)
    # ... configuration ...
    cache.init_app(app)
    return app
```

### Usage Patterns

```python
# src/myapp/api/routes.py
from myapp.extensions import cache

@api_bp.route("/products")
@cache.cached(timeout=60, query_string=True)
def list_products():
    """Cache product list for 60 seconds, varying by query string."""
    products = Product.query.all()
    return jsonify([p.to_dict() for p in products])

@api_bp.route("/products/<int:product_id>")
@cache.cached(timeout=300)
def get_product(product_id: int):
    """Cache individual product for 5 minutes."""
    product = Product.query.get_or_404(product_id)
    return jsonify(product.to_dict())

@api_bp.route("/products/<int:product_id>", methods=["PUT"])
def update_product(product_id: int):
    """Invalidate cache on update."""
    product = Product.query.get_or_404(product_id)
    # ... update logic ...
    cache.delete(f"view//api/products/{product_id}")
    cache.delete_memoized(list_products)
    return jsonify(product.to_dict())
```

### Memoization for Functions

```python
# src/myapp/services/analytics.py
from myapp.extensions import cache

@cache.memoize(timeout=3600)
def compute_user_stats(user_id: int) -> dict:
    """Cache expensive computation per user for 1 hour."""
    # Expensive computation
    return {"user_id": user_id, "stats": computed_stats}

# Invalidate when needed
cache.delete_memoized(compute_user_stats, user_id)
```

## Rate Limiting

Projects exposing APIs **SHOULD** implement rate limiting.

### Why Rate Limiting

Rate limiting protects against abuse, prevents resource exhaustion, and ensures
fair access. Flask-Limiter[^22] provides decorators and configuration for
per-route limits with multiple storage backends.

### Configuration

```python
# src/myapp/extensions.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="redis://localhost:6379/1",
    storage_options={"socket_connect_timeout": 30},
    strategy="fixed-window",
)
```

```python
# src/myapp/__init__.py
from myapp.extensions import limiter

def create_app(config_name: str = "development") -> Flask:
    app = Flask(__name__)
    # ... configuration ...

    limiter.init_app(app)

    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify({
            "error": "Rate limit exceeded",
            "message": str(e.description),
        }), 429

    return app
```

### Route-Specific Limits

```python
# src/myapp/api/routes.py
from myapp.extensions import limiter

@api_bp.route("/search")
@limiter.limit("30 per minute")
def search():
    """Limit search to 30 requests per minute."""
    return jsonify({"results": []})

@api_bp.route("/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    """Strict limit on login attempts."""
    return jsonify({"token": "..."})

@api_bp.route("/health")
@limiter.exempt
def health_check():
    """Exempt health checks from rate limiting."""
    return jsonify({"status": "healthy"})
```

### API Key-Based Limiting

```python
# src/myapp/extensions.py
from flask import request

def get_api_key() -> str:
    """Rate limit by API key when present, otherwise by IP."""
    return request.headers.get("X-API-Key", get_remote_address())

limiter = Limiter(
    key_func=get_api_key,
    default_limits=["1000 per hour"],
    storage_uri=os.environ.get("REDIS_URL", "redis://localhost:6379/1"),
)
```

## Circuit Breakers

Projects calling external services **SHOULD** implement circuit breakers.

### Why Circuit Breakers

Circuit breakers prevent cascading failures when external services become
unavailable. They "open" after repeated failures, failing fast instead of
waiting for timeouts, and periodically "test" if the service has recovered.
pybreaker[^23] provides a Python implementation of this pattern.

### Configuration

```python
# src/myapp/services/external.py
import pybreaker
import requests

# Create circuit breaker with Redis storage for distributed state
external_api_breaker = pybreaker.CircuitBreaker(
    fail_max=5,
    reset_timeout=30,
    state_storage=pybreaker.CircuitRedisStorage(
        pybreaker.STATE_CLOSED,
        redis_object=redis_client,
        namespace="external_api",
    ),
)
```

### Usage Patterns

```python
# src/myapp/services/payment.py
import pybreaker
import requests
from flask import current_app

payment_breaker = pybreaker.CircuitBreaker(
    fail_max=3,
    reset_timeout=60,
    exclude=[requests.exceptions.HTTPError],  # Don't trip on 4xx errors
)

class PaymentService:
    @payment_breaker
    def process_payment(self, amount: float, token: str) -> dict:
        """Process payment with circuit breaker protection."""
        response = requests.post(
            current_app.config["PAYMENT_API_URL"],
            json={"amount": amount, "token": token},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def process_payment_safe(self, amount: float, token: str) -> dict | None:
        """Process payment with fallback handling."""
        try:
            return self.process_payment(amount, token)
        except pybreaker.CircuitBreakerError:
            current_app.logger.warning("Payment service circuit open, queuing for retry")
            queue_payment_retry.delay(amount, token)
            return None
```

### Monitoring Circuit State

```python
# src/myapp/api/routes.py
from myapp.services.payment import payment_breaker

@api_bp.route("/health/dependencies")
def dependency_health():
    """Report circuit breaker states for monitoring."""
    return jsonify({
        "payment_service": {
            "state": payment_breaker.current_state,
            "fail_count": payment_breaker.fail_counter,
        },
    })
```

### Listener for Observability

```python
# src/myapp/services/external.py
import pybreaker

class CircuitBreakerListener(pybreaker.CircuitBreakerListener):
    def state_change(self, cb, old_state, new_state):
        current_app.logger.warning(
            f"Circuit breaker {cb.name} changed from {old_state} to {new_state}"
        )
        # Send metric to monitoring system
        CIRCUIT_STATE.labels(breaker=cb.name, state=new_state.name).set(1)

    def failure(self, cb, exc):
        current_app.logger.error(f"Circuit breaker {cb.name} recorded failure: {exc}")

payment_breaker = pybreaker.CircuitBreaker(
    fail_max=3,
    reset_timeout=60,
    listeners=[CircuitBreakerListener()],
)
```

## Feature Flags

Projects requiring controlled rollouts **SHOULD** implement feature flags.

### Why Feature Flags

Feature flags enable gradual rollouts, A/B testing, and quick feature disabling
without deployments. Flask-FeatureFlags[^24] provides simple configuration-based
flags, while Unleash[^25] offers a full-featured management platform for larger
teams.

### Flask-FeatureFlags for Simple Cases

```python
# src/myapp/__init__.py
from flask_featureflags import FeatureFlag

feature_flags = FeatureFlag()

def create_app(config_name: str = "development") -> Flask:
    app = Flask(__name__)
    # ... configuration ...

    app.config["FEATURE_FLAGS"] = {
        "new_checkout": True,
        "dark_mode": False,
        "beta_api": os.environ.get("ENABLE_BETA_API", "false").lower() == "true",
    }
    feature_flags.init_app(app)

    return app
```

```python
# src/myapp/api/routes.py
from flask_featureflags import is_active

@api_bp.route("/checkout")
def checkout():
    if is_active("new_checkout"):
        return new_checkout_flow()
    return legacy_checkout_flow()
```

```html
<!-- templates/base.html -->
{% if 'dark_mode' is active_feature %}
<link rel="stylesheet" href="/static/dark.css">
{% endif %}
```

### Unleash for Enterprise Feature Management

Projects with complex flag requirements **SHOULD** use Unleash:

```python
# src/myapp/extensions.py
from UnleashClient import UnleashClient

unleash = None

def init_unleash(app) -> UnleashClient:
    global unleash
    unleash = UnleashClient(
        url=app.config["UNLEASH_URL"],
        app_name="myapp",
        instance_id=app.config.get("INSTANCE_ID", "default"),
        custom_headers={"Authorization": app.config["UNLEASH_API_TOKEN"]},
    )
    unleash.initialize_client()
    return unleash
```

```python
# src/myapp/__init__.py
from myapp.extensions import init_unleash

def create_app(config_name: str = "development") -> Flask:
    app = Flask(__name__)
    # ... configuration ...

    if app.config.get("UNLEASH_URL"):
        init_unleash(app)

    return app
```

```python
# src/myapp/api/routes.py
from myapp.extensions import unleash

@api_bp.route("/feature")
def feature_endpoint():
    context = {
        "userId": str(current_user.id),
        "properties": {"plan": current_user.subscription_plan},
    }

    if unleash and unleash.is_enabled("premium_feature", context):
        return premium_feature_response()
    return standard_feature_response()
```

### Custom Feature Flag Handler

Projects **MAY** implement custom handlers for database-backed or percentage-based flags:

```python
# src/myapp/flags.py
import random
from flask import request
from flask_featureflags import FeatureFlag

def percentage_rollout(feature_name: str) -> bool | None:
    """Roll out feature to a percentage of users."""
    rollout_config = {
        "new_algorithm": 25,  # 25% of users
        "redesign": 50,       # 50% of users
    }
    if feature_name not in rollout_config:
        return None  # Let other handlers decide

    user_id = getattr(request, "user_id", random.random())
    return (hash(f"{feature_name}:{user_id}") % 100) < rollout_config[feature_name]

def create_app(config_name: str = "development") -> Flask:
    app = Flask(__name__)
    feature_flags = FeatureFlag(app)
    feature_flags.add_handler(percentage_rollout)
    return app
```

## See Also

- [Python Style Guide](../languages/python.md) - Language-level Python conventions
- [FastAPI Style Guide](fastapi.md) - Async-first API framework
- [Django Style Guide](django.md) - Full-featured web framework

## References

[^1]: [Flask](https://flask.palletsprojects.com/) - Lightweight WSGI web application framework
[^2]: [Django](https://www.djangoproject.com/) - High-level Python web framework
[^3]: [FastAPI](https://fastapi.tiangolo.com/) - Modern, fast web framework for building APIs
[^4]: [Flask Blueprints](https://flask.palletsprojects.com/en/latest/blueprints/) - Modular applications
[^5]: [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/) - SQLAlchemy support for Flask
[^6]: [Flask-Migrate](https://flask-migrate.readthedocs.io/) - Database migrations with Alembic
[^7]: [Flask-Login](https://flask-login.readthedocs.io/) - User session management
[^8]: [Flask-WTF](https://flask-wtf.readthedocs.io/) - WTForms integration
[^9]: [Flask-CORS](https://flask-cors.readthedocs.io/) - Cross-Origin Resource Sharing
[^10]: [Authlib](https://authlib.org/) - OAuth and OpenID Connect client/server library
[^11]: [PyJWT](https://pyjwt.readthedocs.io/) - JSON Web Token implementation in Python
[^12]: [Flask-Principal](https://pythonhosted.org/Flask-Principal/) - Identity management for Flask
[^13]: [Flask-SocketIO](https://flask-socketio.readthedocs.io/) - WebSocket support for Flask
[^14]: [Flask-Profiler](https://pypi.org/project/flask_profiler/) - Endpoint profiler with web UI
[^15]: [py-spy](https://github.com/benfred/py-spy) - Sampling profiler for Python programs
[^16]: [prometheus_client](https://github.com/prometheus/client_python) - Prometheus instrumentation library
[^17]: [Celery](https://docs.celeryq.dev/) - Distributed task queue
[^18]: [RQ (Redis Queue)](https://python-rq.org/) - Simple Python queuing with Redis
[^19]: [Huey](https://huey.readthedocs.io/) - Lightweight task queue for Python
[^20]: [Quart](https://quart.palletsprojects.com/) - Async reimplementation of Flask
[^21]: [Flask-Caching](https://flask-caching.readthedocs.io/) - Caching support for Flask
[^22]: [Flask-Limiter](https://flask-limiter.readthedocs.io/) - Rate limiting extension for Flask
[^23]: [pybreaker](https://github.com/danielfm/pybreaker) - Python circuit breaker implementation
[^24]: [Flask-FeatureFlags](https://flask-featureflags.readthedocs.io/) - Feature flags for Flask
[^25]: [Unleash](https://docs.getunleash.io/) - Open-source feature management platform
