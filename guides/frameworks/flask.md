# Flask Style Guide

> [Doctrine](../../README.md) > [Frameworks](../README.md) > Flask

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119.txt).

Extends [Python style guide](../languages/python.md) with Flask-specific conventions.

**Target Version**: Flask 3.x with Python 3.14

## Quick Reference

All Python tooling applies. Additional considerations:

| Task | Tool | Command |
|------|------|---------|
| Install | uv | `uv add flask` |
| Run dev | Flask CLI | `flask run --debug` |
| Test | pytest + Flask test client | `pytest` |

## Why Flask?

Flask[^1] is a lightweight, flexible microframework ideal for small-to-medium applications, APIs, and prototypes. It provides minimal abstractions while allowing extension through a rich ecosystem.

Use Flask when you need simplicity and flexibility; consider Django[^2] for larger, more structured applications with built-in admin, ORM, and authentication. Consider FastAPI[^3] for high-performance async APIs.

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

**Why**: The application factory pattern enables multiple app instances with different configurations, facilitates testing, and defers extension initialization until configuration is loaded.

### Recommended Structure

```
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

**Why**: Blueprints organize code by feature, enable route prefixes and middleware per module, and make large applications maintainable by separating concerns.

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

**Why**: Environment-based configuration separates deployment concerns from code, prevents secrets from being committed, and enables different settings per environment.

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

**Why**: Flask's test client enables route testing without running a server. pytest fixtures provide isolated test database state and reusable app instances.

## Extensions Ecosystem

Projects **SHOULD** use well-maintained Flask extensions:

| Extension | Purpose | Install |
|-----------|---------|---------|
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

**Why**: Flask's extension ecosystem provides battle-tested solutions for common needs while maintaining the framework's lightweight philosophy.

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
