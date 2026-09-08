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
| WebSocket | Flask-SocketIO | `uv add flask-socketio simple-websocket gunicorn` |
| Profiling | py-spy | `py-spy top --pid PID` |
| Metrics | prometheus_client | `uv add prometheus-client` |
| Background jobs | Celery | `uv add celery[redis]` |
| Simple queues | RQ | `uv add rq` |
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
    from myapp.extensions import db, login_manager, migrate
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Register blueprints
    from myapp.auth import auth_bp
    from myapp.api import api_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(api_bp, url_prefix="/api")

    return app
```

**Why**: The application factory pattern enables multiple app instances with
different configurations, facilitates testing, and defers extension
initialization until configuration is loaded. Every extension instance
**MUST** be initialised here: an extension that is only constructed in
`extensions.py` is never attached to the app, and the first request that
depends on it fails at runtime.

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

Projects **MUST** use environment-based configuration, and **MUST NOT** give
`SECRET_KEY` a fallback value that a production configuration can inherit:

```python
# src/myapp/config.py
import os
import secrets

class Config:
    SECRET_KEY: str | None = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI: str = os.environ["DATABASE_URL"]
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

class DevelopmentConfig(Config):
    DEBUG: bool = True
    # Development-only: generated per process, so it is never a published
    # constant and ProductionConfig can never inherit it.
    SECRET_KEY: str = os.environ.get("SECRET_KEY") or secrets.token_urlsafe(32)

class ProductionConfig(Config):
    DEBUG: bool = False

class TestingConfig(Config):
    TESTING: bool = True
    SECRET_KEY: str = secrets.token_urlsafe(32)
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///:memory:"
```

The factory **MUST** refuse to build an application whose `SECRET_KEY` is
missing or shorter than 32 characters:

```python
# src/myapp/__init__.py
MINIMUM_SECRET_KEY_LENGTH = 32

def create_app(config_name: str = "development") -> Flask:
    app = Flask(__name__)

    configs = {
        "development": "myapp.config.DevelopmentConfig",
        "production": "myapp.config.ProductionConfig",
        "testing": "myapp.config.TestingConfig",
    }
    app.config.from_object(configs.get(config_name, configs["development"]))

    secret_key = app.config.get("SECRET_KEY") or ""
    if len(secret_key) < MINIMUM_SECRET_KEY_LENGTH:
        raise RuntimeError(
            "SECRET_KEY is missing or shorter than "
            f"{MINIMUM_SECRET_KEY_LENGTH} characters; supply a random value "
            "from the deployment environment or secret manager."
        )

    return app
```

Don't publish a fallback that production inherits:

```python
# Don't: every deployment that forgets SECRET_KEY signs sessions with a
# value that is printed in this guide.
class Config:
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-key-change-in-prod")

class ProductionConfig(Config):  # inherits the published key
    DEBUG: bool = False
```

**Why**: Environment-based configuration separates deployment concerns from
code, prevents secrets from being committed, and enables different settings
per environment. `SECRET_KEY` signs the session cookie that Flask-Login[^7]
uses to identify users, so a fallback shared by every reader of this guide
lets anyone forge a session for any account. Flask requires a long random
value that is never revealed[^26]; failing startup makes a missing secret a
deployment error instead of a silent authentication bypass. A development
value generated per process keeps local work convenient without creating a
constant that `ProductionConfig` can inherit.

Projects **MUST** test that a production configuration refuses to start
without a supplied secret:

```python
# tests/test_config.py
import importlib

import pytest

import myapp.config
from myapp import create_app

def test_production_refuses_to_start_without_a_secret(monkeypatch) -> None:
    monkeypatch.delenv("SECRET_KEY", raising=False)
    # Configuration classes read the environment when the module is imported.
    importlib.reload(myapp.config)

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app("production")

def test_production_never_inherits_the_development_secret(monkeypatch) -> None:
    monkeypatch.delenv("SECRET_KEY", raising=False)
    importlib.reload(myapp.config)

    assert myapp.config.ProductionConfig.SECRET_KEY is None
    assert len(myapp.config.DevelopmentConfig.SECRET_KEY) >= 32
```

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

def create_app(config_name: str = "development") -> Flask:
    app = Flask(__name__)
    # ... configuration ...

    # Required: without this call current_user and login_required raise
    # AttributeError: 'Flask' object has no attribute 'login_manager'.
    login_manager.init_app(app)

    # ... register blueprints ...
    return app
```

Routes establish and end the session with `login_user` and `logout_user`:

```python
# src/myapp/auth/routes.py
from flask import request
from flask_login import login_required, login_user, logout_user
from werkzeug.security import check_password_hash

from myapp.models.user import User

@auth_bp.route("/login", methods=["POST"])
def login() -> tuple[dict, int]:
    credentials = request.get_json()
    user = User.query.filter_by(email=credentials["email"]).first()
    if user is None or not check_password_hash(
        user.password_hash, credentials["password"]
    ):
        return {"error": "Invalid credentials"}, 401

    login_user(user)
    return {"message": "Logged in"}, 200

@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout() -> tuple[dict, int]:
    logout_user()
    return {"message": "Logged out"}, 200
```

**Why**: Flask-Login stores the value returned by `get_id()` in the signed
session cookie and rebuilds `current_user` from it through the `user_loader`.
Constructing `LoginManager()` in `extensions.py` only creates the object;
`init_app` is what attaches it to an application instance[^7]. An
uninitialised manager is not a login failure but a server error: every
`login_required` route returns 500 with `AttributeError: 'Flask' object has
no attribute 'login_manager'`.

Projects **MUST** cover both the anonymous and the authenticated path:

```python
# tests/test_auth.py
def test_anonymous_request_is_redirected_to_login(client) -> None:
    response = client.get("/private")

    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]

def test_authenticated_request_reaches_the_route(client, user) -> None:
    login = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    assert login.status_code == 200

    response = client.get("/private")

    assert response.status_code == 200
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

Projects **SHOULD** use Authlib for OAuth 2.0 and OpenID Connect integration,
and **MUST** enable PKCE with `S256`:

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
        client_kwargs={
            "scope": "openid email profile",
            # Authlib adds code_challenge and code_verifier for PKCE.
            "code_challenge_method": "S256",
        },
    )

    return app
```

The provider identity **MUST** be the issuer and subject pair, not the email
address, and it **MUST** be stored against a local account:

```python
# src/myapp/models/oauth.py
from myapp.extensions import db

class OAuthIdentity(db.Model):
    """A provider identity (issuer plus subject) linked to a local account."""

    __tablename__ = "oauth_identity"
    __table_args__ = (db.UniqueConstraint("issuer", "subject"),)

    id = db.Column(db.Integer, primary_key=True)
    issuer = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User")
```

```python
# src/myapp/auth/routes.py
import secrets

from authlib.integrations.base_client import OAuthError
from flask import abort, current_app, redirect, url_for
from flask_login import login_user
from werkzeug.security import generate_password_hash

from myapp.extensions import db, oauth
from myapp.models.oauth import OAuthIdentity
from myapp.models.user import User

@auth_bp.route("/login/google")
def google_login():
    redirect_uri = url_for("auth.google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@auth_bp.route("/callback/google")
def google_callback():
    try:
        token = oauth.google.authorize_access_token()
    except OAuthError as error:
        current_app.logger.warning("Google callback rejected: %s", error.error)
        abort(401, description="OAuth callback failed")

    claims = token.get("userinfo")
    if claims is None or "sub" not in claims or "iss" not in claims:
        abort(401, description="Provider returned no verifiable identity")
    if not claims.get("email_verified", False):
        abort(403, description="Provider has not verified this email address")

    login_user(link_local_user(claims))
    return redirect(url_for("main.index"))

def link_local_user(claims: dict) -> User:
    """Map a verified provider identity to a local account."""
    identity = OAuthIdentity.query.filter_by(
        issuer=claims["iss"], subject=claims["sub"]
    ).first()
    if identity is not None:
        return identity.user

    user = User.query.filter_by(email=claims["email"]).first()
    if user is None:
        user = User(
            email=claims["email"],
            # No local password: sign-in happens through the provider only.
            password_hash=generate_password_hash(secrets.token_urlsafe(32)),
            fs_uniquifier=secrets.token_urlsafe(32),
        )
        db.session.add(user)

    db.session.add(
        OAuthIdentity(issuer=claims["iss"], subject=claims["sub"], user=user)
    )
    db.session.commit()
    return user
```

Redirect URIs registered with the provider **MUST** match the value the
application sends exactly, and the callback **MUST NOT** be reachable through
an open redirector.

**Why**: Storing the email in `session` leaves `current_user` anonymous, so
every `login_required` route still rejects the user; `login_user` is what
establishes the Flask-Login session[^7]. An email address is not a stable
identifier — providers let users change it and reuse it — whereas the issuer
and subject pair is stable for the lifetime of the account, so linking on
`(iss, sub)` prevents one user inheriting another's account after an address
change. RFC 9700[^27] requires exact string matching of redirect URIs
(Section 2.1) and recommends PKCE for confidential clients with `S256` as the
only challenge method that does not expose the verifier (Section 2.1.1);
Authlib generates and verifies the challenge when `code_challenge_method` is
set in `client_kwargs`[^28]. Authlib validates the `state` value and parses
the ID token during `authorize_access_token()`[^28], which makes a forged or
replayed callback raise `OAuthError` rather than silently succeed — but only
the application can decide whether an unverified email may be linked.

Projects **MUST** test the state, replay, and rejected-claim paths:

```python
# tests/test_oauth.py
from urllib.parse import parse_qs, urlparse

from myapp.extensions import oauth
from myapp.models.user import User

ISSUER = "https://accounts.google.com"

def start_login(client) -> str:
    """Run the redirect leg and return the state Authlib stored in session."""
    response = client.get("/auth/login/google")
    assert response.status_code == 302
    query = parse_qs(urlparse(response.headers["Location"]).query)
    assert query["code_challenge_method"] == ["S256"]
    return query["state"][0]

def test_callback_rejects_an_unknown_state(client) -> None:
    response = client.get("/auth/callback/google?code=abc&state=forged")

    assert response.status_code == 401

def test_callback_replay_is_rejected(client, monkeypatch) -> None:
    state = start_login(client)
    monkeypatch.setattr(
        oauth.google,
        "fetch_access_token",
        lambda **kwargs: {
            "access_token": "provider-token",
            "userinfo": {
                "iss": ISSUER,
                "sub": "1234567890",
                "email": "person@example.com",
                "email_verified": True,
            },
        },
    )
    first = client.get(f"/auth/callback/google?code=abc&state={state}")
    assert first.status_code == 302

    replayed = client.get(f"/auth/callback/google?code=abc&state={state}")

    assert replayed.status_code == 401

def test_callback_rejects_an_unverified_email(client, monkeypatch) -> None:
    state = start_login(client)
    monkeypatch.setattr(
        oauth.google,
        "fetch_access_token",
        lambda **kwargs: {
            "access_token": "provider-token",
            "userinfo": {
                "iss": ISSUER,
                "sub": "2222",
                "email": "person@example.com",
                "email_verified": False,
            },
        },
    )

    response = client.get(f"/auth/callback/google?code=abc&state={state}")

    assert response.status_code == 403
    assert User.query.count() == 0
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

Projects **SHOULD** use Gunicorn's threaded worker with `simple-websocket`,
because eventlet is deprecated and the gevent WebSocket layer is archived:

| Server | Status | Use Case |
| ------ | ------ | -------- |
| Threading + simple-websocket | Recommended | Production default; best library compatibility |
| gevent + gevent-websocket | gevent-websocket archived | Existing greenlet stacks only |
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
        async_mode="threading",  # Must match the deployed Gunicorn worker
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

Projects **MUST** install the server they invoke, and **SHOULD** run
Flask-SocketIO behind Gunicorn's threaded worker:

```bash
# Install dependencies: the server is part of the dependency set
uv add "flask-socketio==5.6.1" "gunicorn==26.2.0" "simple-websocket==1.1.0"

# Run the threaded worker; simple-websocket supplies the WebSocket transport
gunicorn -w 1 --threads 100 --bind 0.0.0.0:5000 "myapp:create_app()"
```

The `async_mode` passed to `socketio.init_app` **MUST** match the deployed
worker: `"threading"` for the command above, `"gevent"` for a greenlet stack.

**Why**: The gevent WebSocket worker requires five packages that must all be
present — Flask-SocketIO, gevent, gevent-websocket, `packaging` and Gunicorn
itself — and its WebSocket layer, `gevent-websocket`, has been archived by its
author[^29], so it receives no compatibility fixes. Installing only
Flask-SocketIO, gevent and gevent-websocket leaves no `gunicorn` executable
and makes the documented worker import fail with `ModuleNotFoundError: No
module named 'gunicorn'`. The threaded worker with `simple-websocket` is a
maintained path documented by Flask-SocketIO[^13] and avoids monkey patching
entirely. Gunicorn's load balancer cannot do sticky sessions, so `-w 1` is
required in every variant; scale by running several single-worker instances
behind nginx.

Projects **MUST** smoke test the deployment command, not only the application:

```python
# tests/smoke/test_websocket.py — run against a started Gunicorn process
import socketio

def test_websocket_round_trip() -> None:
    client = socketio.Client()
    received: list[dict] = []
    client.on("pong_test", received.append)

    client.connect("http://127.0.0.1:5000", transports=["websocket"])
    client.emit("ping_test", {"hello": "world"})
    client.sleep(1)
    client.disconnect()

    assert client.transport() == "websocket"
    assert received == [{"echo": {"hello": "world"}}]
```

Projects that require a greenlet stack **MUST** install every dependency the
worker imports, including `packaging`, which Gunicorn's gevent worker needs
but does not declare:

```bash
uv add "flask-socketio==5.6.1" "gunicorn==26.2.0" "gevent==26.8.0" \
    "gevent-websocket==0.10.1" "packaging==25.0"

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

Projects with simpler requirements **MAY** use RQ[^18] directly, and
**MUST NOT** use Flask-RQ2:

```python
# src/myapp/config.py
class Config:
    RQ_REDIS_URL: str = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    RQ_QUEUE_NAME: str = os.environ.get("RQ_QUEUE_NAME", "default")
```

```python
# src/myapp/extensions.py
from flask import Flask
from redis import Redis
from rq import Queue

def rq_init_app(app: Flask) -> Queue:
    """Create this app instance's RQ queue and store it in app.extensions."""
    connection = Redis.from_url(app.config["RQ_REDIS_URL"])
    queue = Queue(app.config["RQ_QUEUE_NAME"], connection=connection)
    app.extensions["rq_queue"] = queue
    return queue
```

```python
# src/myapp/__init__.py
from myapp.extensions import rq_init_app

def create_app(config_name: str = "development") -> Flask:
    app = Flask(__name__)
    # ... configuration ...
    rq_init_app(app)
    return app
```

```python
# src/myapp/tasks.py
def process_upload(file_id: int) -> str:
    """Process an uploaded file in a worker process."""
    return f"processed {file_id}"
```

```python
# src/myapp/api/routes.py
from flask import current_app
from myapp.tasks import process_upload

@api_bp.route("/uploads/<int:file_id>/process", methods=["POST"])
def enqueue_processing(file_id: int) -> tuple[dict, int]:
    """Hand the slow work to a worker and return the job ID."""
    job = current_app.extensions["rq_queue"].enqueue(process_upload, file_id)
    return {"job_id": job.id}, 202
```

```bash
uv add "rq==2.12.0"

# Run an RQ 2.12 worker with the built-in scheduler
rq worker --url "$REDIS_URL" --path src --with-scheduler default
```

Jobs that need application configuration or the database **MUST** run under an
application context:

```python
# src/myapp/worker.py
from rq import Worker

from myapp import create_app

def main() -> None:
    app = create_app("production")
    with app.app_context():
        queue = app.extensions["rq_queue"]
        Worker([queue], connection=queue.connection).work(with_scheduler=True)

if __name__ == "__main__":
    main()
```

Run that worker with `python -m myapp.worker`.

**Why**: Flask-RQ2's last release was 18.3 in December 2018[^30] and it imports
`pkg_resources` at module scope, which current setuptools no longer ships, so
`from flask_rq2 import RQ` fails on Python 3.14 with `ModuleNotFoundError: No
module named 'pkg_resources'`. RQ itself is maintained, tests on Python 3.14,
and needs no Flask-specific wrapper: a `Queue` on `app.extensions` follows the
same factory-scoped pattern as Celery above, so each application instance owns
its own connection instead of sharing module state.

```python
# tests/test_rq.py
import fakeredis
from rq import Queue, SimpleWorker

from myapp.tasks import process_upload

def test_enqueue_and_run_a_job() -> None:
    connection = fakeredis.FakeRedis()
    queue = Queue("default", connection=connection)

    job = queue.enqueue(process_upload, 42)
    SimpleWorker([queue], connection=connection).work(burst=True)

    assert job.latest_result().return_value == "processed 42"
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

The limiter **MUST NOT** be keyed by a raw request header. Authentication
**MUST** resolve the credential to a stored identifier first:

```python
# src/myapp/models/api_key.py
from myapp.extensions import db

class ApiKey(db.Model):
    """A hashed API credential; the raw key is shown once at creation."""

    __tablename__ = "api_key"

    id = db.Column(db.Integer, primary_key=True)
    key_digest = db.Column(db.String(64), unique=True, nullable=False)
    revoked = db.Column(db.Boolean, nullable=False, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
```

```python
# src/myapp/auth/api_keys.py
import hashlib
from collections.abc import Callable
from functools import wraps

from flask import abort, g, request

from myapp.models.api_key import ApiKey

def digest_api_key(raw_key: str) -> str:
    """Hash a raw API key for storage and lookup."""
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

def authenticate_api_key() -> None:
    """Resolve X-API-Key to a stored key ID before any limit is applied."""
    g.api_key_id = None
    presented = request.headers.get("X-API-Key")
    if presented is None:
        return

    api_key = ApiKey.query.filter_by(key_digest=digest_api_key(presented)).first()
    if api_key is not None and not api_key.revoked:
        g.api_key_id = str(api_key.id)

def api_key_required(view: Callable) -> Callable:
    """Reject unknown or revoked credentials after the limit is applied."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        if g.get("api_key_id") is None:
            abort(401, description="Valid X-API-Key required")
        return view(*args, **kwargs)

    return wrapper
```

```python
# src/myapp/extensions.py
from flask import g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

def api_key_or_address() -> str:
    """Key limits by the authenticated API key, falling back to the address."""
    key_id = g.get("api_key_id")
    if key_id is not None:
        return f"key:{key_id}"
    return f"ip:{get_remote_address()}"

limiter = Limiter(
    key_func=api_key_or_address,
    default_limits=["1000 per hour"],
    storage_uri=os.environ.get("REDIS_URL", "redis://localhost:6379/1"),
)
```

Authentication **MUST** be registered before `limiter.init_app`, and the
application **MUST** apply `ProxyFix` with the exact number of trusted proxies
when it runs behind one:

```python
# src/myapp/__init__.py
from werkzeug.middleware.proxy_fix import ProxyFix

from myapp.auth.api_keys import authenticate_api_key
from myapp.extensions import limiter

def create_app(config_name: str = "development") -> Flask:
    app = Flask(__name__)
    # ... configuration ...

    if app.config.get("TRUSTED_PROXY_COUNT"):
        app.wsgi_app = ProxyFix(
            app.wsgi_app,
            x_for=app.config["TRUSTED_PROXY_COUNT"],
            x_proto=app.config["TRUSTED_PROXY_COUNT"],
            x_host=0,
            x_prefix=0,
        )

    app.before_request(authenticate_api_key)  # populates g.api_key_id
    limiter.init_app(app)                     # keys on the trusted identity

    return app
```

```python
# src/myapp/api/routes.py
from myapp.auth.api_keys import api_key_required
from myapp.extensions import limiter

@api_bp.route("/reports")
@limiter.limit("3 per minute")
@api_key_required
def reports():
    """The limiter counts the request before the credential is rejected."""
    return jsonify({"reports": []})
```

**Why**: `request.headers.get("X-API-Key", ...)` lets an unauthenticated caller
choose its own quota bucket, so rotating the header gives an attacker an
unlimited number of fresh buckets and the limit protects nothing. Keying on a
database identifier the caller cannot influence removes that choice, and the
address fallback is applied only to callers that presented no credential.
Ordering matters twice: `authenticate_api_key` must run before
`limiter.init_app` registers its own `before_request`, or `g.api_key_id` is
still unset when `key_func` runs; and rejection must happen inside the view
chain, below `limiter.limit`, or an aborted request never reaches the limiter
and an attacker can spend unlimited invalid credentials. `get_remote_address`
reads `request.remote_addr`, which is the proxy's address unless `ProxyFix` is
configured with the exact hop count[^31] — a guessed count lets clients spoof
`X-Forwarded-For` and forge the fallback bucket.

```python
# tests/test_rate_limit.py
def test_rotating_invalid_keys_cannot_reset_the_bucket(client) -> None:
    """An attacker rotating X-API-Key stays in one address bucket."""
    statuses = [
        client.get(
            "/api/reports", headers={"X-API-Key": f"attacker-key-{n}"}
        ).status_code
        for n in range(1, 5)
    ]

    assert statuses == [401, 401, 401, 429]

def test_authenticated_key_shares_one_bucket_across_addresses(
    client, api_key
) -> None:
    """Spoofed forwarding headers give an authenticated key no new bucket."""
    statuses = [
        client.get(
            "/api/reports",
            headers={"X-API-Key": api_key, "X-Forwarded-For": f"10.0.0.{n}"},
        ).status_code
        for n in range(1, 5)
    ]

    assert statuses == [200, 200, 200, 429]
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

Exclusions **MUST** inspect the response status, because `raise_for_status()`
raises the same `HTTPError` for 4xx and 5xx:

```python
# src/myapp/services/payment.py
import pybreaker
import requests
from flask import current_app

def is_client_error(exc: BaseException) -> bool:
    """Return True for 4xx responses, which are caller errors, not outages."""
    response = getattr(exc, "response", None)
    return response is not None and 400 <= response.status_code < 500

payment_breaker = pybreaker.CircuitBreaker(
    fail_max=3,
    reset_timeout=60,
    # 5xx responses and transport failures still count towards fail_max.
    exclude=[is_client_error],
)

class PaymentService:
    @payment_breaker
    def process_payment(
        self, amount: float, token: str, idempotency_key: str
    ) -> dict:
        """Process payment with circuit breaker protection."""
        response = requests.post(
            current_app.config["PAYMENT_API_URL"],
            json={"amount": amount, "token": token},
            headers={"Idempotency-Key": idempotency_key},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def process_payment_safe(
        self, amount: float, token: str, idempotency_key: str
    ) -> dict | None:
        """Process payment with fallback handling."""
        try:
            return self.process_payment(amount, token, idempotency_key)
        except pybreaker.CircuitBreakerError:
            current_app.logger.warning(
                "Payment service circuit open, queuing for retry"
            )
            queue_payment_retry.delay(amount, token, idempotency_key)
            return None
```

Don't exclude the exception class:

```python
# Don't: raise_for_status() raises HTTPError for 500s too, so a total
# outage leaves the breaker closed with fail_counter at 0.
payment_breaker = pybreaker.CircuitBreaker(
    fail_max=3,
    exclude=[requests.exceptions.HTTPError],
)
```

Retries queued while the circuit is open **MUST** carry the idempotency key of
the original attempt.

**Why**: pybreaker treats an excluded exception as a business outcome rather
than a system failure[^23], and `requests` signals both "the caller sent bad
data" and "the service is broken" with `HTTPError`. Excluding the class means
five consecutive 500 responses leave the breaker closed with `fail_counter`
at 0, so the breaker never opens and every request keeps paying the full
timeout. A predicate that reads `exc.response.status_code` excludes only the
4xx range and leaves 5xx, `ConnectionError` and `Timeout` counting. Because a
payment request may have been processed before the response failed, replaying
it without the original idempotency key can charge the customer twice; the
key makes the retry safe to repeat.

```python
# tests/test_payment_breaker.py
import requests

from myapp.services import payment
from myapp.services.payment import PaymentService, payment_breaker

class FakeResponse:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(
                f"{self.status_code} Error", response=self
            )

    def json(self) -> dict:
        return {"status": "ok"}

def call_five_times(monkeypatch, behaviour) -> None:
    monkeypatch.setattr(payment.requests, "post", behaviour)
    service = PaymentService()
    for attempt in range(5):
        try:
            service.process_payment(10.0, "card-token", f"key-{attempt}")
        except Exception:
            pass

def test_client_errors_do_not_trip_the_breaker(app, monkeypatch) -> None:
    call_five_times(monkeypatch, lambda *a, **k: FakeResponse(404))

    assert payment_breaker.current_state == "closed"
    assert payment_breaker.fail_counter == 0

def test_server_errors_trip_the_breaker(app, monkeypatch) -> None:
    call_five_times(monkeypatch, lambda *a, **k: FakeResponse(500))

    assert payment_breaker.current_state == "open"

def test_transport_failures_trip_the_breaker(app, monkeypatch) -> None:
    def explode(*args, **kwargs):
        raise requests.exceptions.ConnectionError("refused")

    call_five_times(monkeypatch, explode)

    assert payment_breaker.current_state == "open"
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
[^26]: [Flask SECRET_KEY](https://flask.palletsprojects.com/en/stable/config/#SECRET_KEY) - Session signing key requirements
[^27]: [RFC 9700](https://www.rfc-editor.org/rfc/rfc9700.html) - Best Current Practice for OAuth 2.0 Security
[^28]: [Authlib Flask OAuth client](https://docs.authlib.org/en/latest/oauth2/client/web/flask.html) - Flask integration and PKCE configuration
[^29]: [gevent-websocket](https://github.com/jgelens/gevent-websocket) - Archived WebSocket library for gevent
[^30]: [Flask-RQ2 on PyPI](https://pypi.org/project/Flask-RQ2/) - Release history for the unmaintained RQ integration
[^31]: [Werkzeug ProxyFix](https://flask.palletsprojects.com/en/stable/deploying/proxy_fix/) - Trusting forwarded client addresses
