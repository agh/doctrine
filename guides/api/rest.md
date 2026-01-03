# REST API Best Practices

> [Doctrine](../../README.md) > [API Design](README.md) > REST

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in
[RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

This guide covers language-agnostic REST API best practices for resource
design, HTTP semantics, error handling, and API security. For
framework-specific implementation, see:

- [FastAPI (Python)](../frameworks/fastapi.md)
- [Django REST Framework](../frameworks/django.md)
- [Flask (Python)](../frameworks/flask.md)
- [Gin (Go)](../frameworks/gin.md)
- [Rails (Ruby)](../frameworks/rails.md)
- [Axum (Rust)](../frameworks/axum.md)

## Why REST?

REST (Representational State Transfer)[^1] is an architectural style for
designing networked applications. RESTful APIs use HTTP methods and status
codes to perform CRUD operations on resources.

**Use REST when**:

- Your API has predictable, resource-oriented access patterns
- HTTP caching is important for performance
- You're building a public API where simplicity matters
- Clients have similar data needs (less over-fetching concern)
- You need broad ecosystem compatibility

**Consider GraphQL when**:

- Clients have diverse data needs requiring flexible queries
- Reducing round trips is critical (mobile, high latency)
- You need real-time subscriptions
- Strong typing and introspection are priorities

## Resource Design

### URL Structure

Projects **MUST** use nouns for resources, not verbs:

```text
# Good: Nouns represent resources
GET    /users
GET    /users/123
POST   /users
PUT    /users/123
DELETE /users/123

# Bad: Verbs in URLs
GET    /getUsers
POST   /createUser
POST   /deleteUser/123
```

**Why**: HTTP methods already express the action. URLs should identify
resources, not operations.

### Plural Resource Names

Projects **MUST** use plural nouns for collection resources:

```text
# Good: Plural nouns
GET /users
GET /users/123
GET /orders
GET /orders/456/items

# Bad: Singular nouns
GET /user
GET /user/123
```

**Why**: Collections contain multiple items. Plural names are consistent
whether accessing one or many.

### Hierarchical Resources

Projects **SHOULD** use nesting for resources with clear parent-child
relationships:

```text
# Good: Nested resources
GET /users/123/orders           # Orders belonging to user 123
GET /orders/456/items           # Items in order 456
GET /organizations/789/members  # Members of organization 789

# Limit nesting depth to 2-3 levels
GET /users/123/orders/456/items  # Acceptable
GET /a/1/b/2/c/3/d/4             # Too deep - flatten
```

**Alternative**: For deeply nested resources, use query parameters or
top-level endpoints:

```text
# Instead of deep nesting
GET /users/123/orders/456/items/789/notes

# Use top-level with filters
GET /notes?item_id=789
GET /items/789/notes
```

### URL Naming Conventions

Projects **MUST** follow these URL conventions:

| Convention             | Example        | Notes                               |
| ---------------------- | -------------- | ----------------------------------- |
| Lowercase              | `/users`       | Not `/Users`                        |
| Hyphens for multi-word | `/order-items` | Not `/orderItems` or `/order_items` |
| No trailing slashes    | `/users`       | Not `/users/`                       |
| No file extensions     | `/users/123`   | Not `/users/123.json`               |

```text
# Good
GET /api/v1/user-profiles
GET /api/v1/order-items/123

# Bad
GET /api/v1/userProfiles
GET /api/v1/order_items/123
GET /api/v1/users.json
```

## HTTP Methods

### Method Semantics

Projects **MUST** use HTTP methods according to their semantics:

| Method | Purpose | Idempotent | Safe | Request Body |
| ------ | ------- | ---------- | ---- | ------------ |
| GET | Retrieve resource(s) | Yes | Yes | No |
| POST | Create resource | No | No | Yes |
| PUT | Replace resource | Yes | No | Yes |
| PATCH | Partial update | No* | No | Yes |
| DELETE | Remove resource | Yes | No | Optional |
| HEAD | Get headers only | Yes | Yes | No |
| OPTIONS | Get allowed methods | Yes | Yes | No |

*PATCH can be idempotent depending on implementation.

### GET - Retrieve

```http
# Get collection
GET /users HTTP/1.1
Host: api.example.com

# Get single resource
GET /users/123 HTTP/1.1
Host: api.example.com

# Get with query parameters
GET /users?status=active&sort=created_at HTTP/1.1
Host: api.example.com
```

Projects **MUST NOT** use GET for operations with side effects.

### POST - Create

```http
POST /users HTTP/1.1
Host: api.example.com
Content-Type: application/json

{
  "email": "user@example.com",
  "name": "Jane Doe"
}
```

Response:

```http
HTTP/1.1 201 Created
Location: /users/124
Content-Type: application/json

{
  "id": 124,
  "email": "user@example.com",
  "name": "Jane Doe",
  "created_at": "2025-01-15T10:30:00Z"
}
```

Projects **MUST** return `201 Created` with a `Location` header for successful creation.

### PUT - Replace

```http
PUT /users/123 HTTP/1.1
Host: api.example.com
Content-Type: application/json

{
  "email": "newemail@example.com",
  "name": "Jane Smith"
}
```

Projects **MUST** treat PUT as a complete replacement. Omitted fields should
be cleared or set to defaults.

### PATCH - Partial Update

```http
PATCH /users/123 HTTP/1.1
Host: api.example.com
Content-Type: application/json

{
  "name": "Jane Smith"
}
```

Projects **SHOULD** use JSON Merge Patch (RFC 7396)[^2] or JSON Patch
(RFC 6902)[^3]:

```http
# JSON Merge Patch - simple partial updates
PATCH /users/123 HTTP/1.1
Content-Type: application/merge-patch+json

{
  "name": "Jane Smith",
  "phone": null
}

# JSON Patch - explicit operations
PATCH /users/123 HTTP/1.1
Content-Type: application/json-patch+json

[
  { "op": "replace", "path": "/name", "value": "Jane Smith" },
  { "op": "remove", "path": "/phone" }
]
```

### DELETE - Remove

```http
DELETE /users/123 HTTP/1.1
Host: api.example.com
```

Response:

```http
HTTP/1.1 204 No Content
```

Projects **SHOULD** return `204 No Content` for successful deletion.

## HTTP Status Codes

### Success Codes (2xx)

Projects **MUST** use appropriate success codes:

| Code | Meaning | Use Case |
| ---- | ------- | -------- |
| 200 OK | Request succeeded | GET, PUT, PATCH with response body |
| 201 Created | Resource created | POST creating new resource |
| 202 Accepted | Request accepted for processing | Async operations |
| 204 No Content | Success, no body | DELETE, PUT/PATCH without body |

### Client Error Codes (4xx)

| Code | Meaning | Use Case |
| ---- | ------- | -------- |
| 400 Bad Request | Malformed request | Invalid JSON, missing fields |
| 401 Unauthorized | Authentication required | Missing or invalid credentials |
| 403 Forbidden | Authorization failed | Valid creds, insufficient perms |
| 404 Not Found | Resource doesn't exist | Invalid ID, deleted resource |
| 405 Method Not Allowed | HTTP method not supported | POST to read-only endpoint |
| 409 Conflict | State conflict | Duplicate email, version mismatch |
| 410 Gone | Resource permanently removed | Deleted and won't return |
| 415 Unsupported Media Type | Content-Type not supported | XML when only JSON accepted |
| 422 Unprocessable Entity | Validation failed | Valid JSON but invalid data |
| 429 Too Many Requests | Rate limit exceeded | Include Retry-After header |

### Server Error Codes (5xx)

| Code | Meaning | Use Case |
| ---- | ------- | -------- |
| 500 Internal Server Error | Unexpected server error | Unhandled exceptions |
| 502 Bad Gateway | Upstream service failed | Database down, external API error |
| 503 Service Unavailable | Server temporarily unavailable | Maintenance, overload |
| 504 Gateway Timeout | Upstream timeout | Slow DB, external API timeout |

### Status Code Selection

```text
Is the request malformed?
  └─ Yes → 400 Bad Request

Is authentication required but missing/invalid?
  └─ Yes → 401 Unauthorized

Is the user authenticated but not authorized?
  └─ Yes → 403 Forbidden

Does the resource exist?
  └─ No → 404 Not Found

Is there a business rule conflict?
  └─ Yes → 409 Conflict

Did validation fail?
  └─ Yes → 422 Unprocessable Entity

Success?
  └─ Created → 201 Created
  └─ No content to return → 204 No Content
  └─ Content to return → 200 OK
```

## Request and Response Format

### Content Negotiation

Projects **MUST** support content negotiation:

```http
# Request specific format
GET /users/123 HTTP/1.1
Accept: application/json

# Specify request body format
POST /users HTTP/1.1
Content-Type: application/json
```

Projects **SHOULD** default to JSON when no Accept header is provided.

### JSON Conventions

Projects **MUST** use consistent JSON field naming:

| Convention | Example | Recommendation |
| ---------- | ------- | -------------- |
| camelCase | `firstName` | JavaScript ecosystems |
| snake_case | `first_name` | Python, Ruby ecosystems |

**Choose one and be consistent across the entire API.**

```json
{
  "id": 123,
  "email": "user@example.com",
  "firstName": "Jane",
  "lastName": "Doe",
  "createdAt": "2025-01-15T10:30:00Z",
  "isActive": true
}
```

### Date and Time

Projects **MUST** use ISO 8601 format for dates and times:

```json
{
  "createdAt": "2025-01-15T10:30:00Z",
  "updatedAt": "2025-01-15T14:45:30.123Z",
  "birthDate": "1990-05-20",
  "startTime": "09:00:00"
}
```

Projects **SHOULD** use UTC timezone (Z suffix) for timestamps.

### Envelope vs. Direct Response

Projects **SHOULD** return resources directly without envelope wrappers:

```json
// Good: Direct response
{
  "id": 123,
  "email": "user@example.com"
}

// Avoid: Unnecessary envelope
{
  "status": "success",
  "data": {
    "id": 123,
    "email": "user@example.com"
  }
}
```

Use HTTP status codes for success/failure indication.

**Exception**: Envelopes are acceptable for paginated collections:

```json
{
  "data": [...],
  "meta": {
    "total": 100,
    "page": 1,
    "perPage": 20
  }
}
```

## Pagination

### Offset-Based Pagination

Simple but has consistency issues with concurrent modifications:

```http
GET /users?page=2&per_page=20 HTTP/1.1

# Alternative parameter names
GET /users?offset=20&limit=20 HTTP/1.1
```

Response:

```json
{
  "data": [...],
  "meta": {
    "total": 150,
    "page": 2,
    "perPage": 20,
    "totalPages": 8
  },
  "links": {
    "self": "/users?page=2&per_page=20",
    "first": "/users?page=1&per_page=20",
    "prev": "/users?page=1&per_page=20",
    "next": "/users?page=3&per_page=20",
    "last": "/users?page=8&per_page=20"
  }
}
```

### Cursor-Based Pagination

Projects **SHOULD** use cursor-based pagination for large or frequently
changing datasets:

```http
GET /users?limit=20&after=eyJpZCI6MTIzfQ HTTP/1.1
```

Response:

```json
{
  "data": [...],
  "meta": {
    "hasMore": true
  },
  "cursors": {
    "after": "eyJpZCI6MTQzfQ",
    "before": "eyJpZCI6MTI0fQ"
  },
  "links": {
    "next": "/users?limit=20&after=eyJpZCI6MTQzfQ"
  }
}
```

**Why cursor-based**: Stable under insertions/deletions. Offset-based
pagination can skip or duplicate items when data changes between requests.

### Keyset Pagination

For sorted results, use the sort key as cursor:

```http
# First page
GET /users?limit=20&sort=created_at HTTP/1.1

# Next page using last item's created_at
GET /users?limit=20&sort=created_at&after=2025-01-15T10:30:00Z HTTP/1.1
```

### Pagination Defaults

Projects **MUST** set sensible defaults and limits:

| Parameter | Default | Maximum |
| --------- | ------- | ------- |
| `limit` / `per_page` | 20 | 100 |

```http
# Implicit defaults
GET /users HTTP/1.1
# Returns first 20 users

# Explicit limit (capped at max)
GET /users?limit=200 HTTP/1.1
# Returns 100 users (capped)
```

## Filtering and Sorting

### Query Parameter Filtering

```http
# Simple equality
GET /users?status=active HTTP/1.1

# Multiple values (OR)
GET /users?status=active,pending HTTP/1.1

# Multiple filters (AND)
GET /users?status=active&role=admin HTTP/1.1

# Range filters
GET /orders?created_after=2025-01-01&created_before=2025-02-01 HTTP/1.1
GET /products?price_min=10&price_max=100 HTTP/1.1

# Search
GET /users?search=jane HTTP/1.1
GET /users?q=jane HTTP/1.1
```

### Field Selection

Projects **MAY** support field selection to reduce payload size:

```http
# Return only specified fields
GET /users?fields=id,email,name HTTP/1.1

# Nested field selection
GET /orders?fields=id,total,user.name HTTP/1.1
```

### Sorting

```http
# Single field sort
GET /users?sort=created_at HTTP/1.1

# Descending order
GET /users?sort=-created_at HTTP/1.1

# Multiple sort fields
GET /users?sort=-created_at,name HTTP/1.1
```

**Alternative syntax**:

```http
GET /users?sort=created_at&order=desc HTTP/1.1
GET /users?sort_by=created_at&sort_order=desc HTTP/1.1
```

### Including Related Resources

Projects **MAY** support eager loading related resources:

```http
# Include related resources
GET /orders/123?include=user,items HTTP/1.1
GET /users?include=orders HTTP/1.1
```

Response:

```json
{
  "id": 123,
  "total": 99.99,
  "user": {
    "id": 456,
    "name": "Jane Doe"
  },
  "items": [...]
}
```

## Error Handling

### Error Response Format

Projects **MUST** return consistent error responses:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid data",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      },
      {
        "field": "password",
        "message": "Password must be at least 8 characters"
      }
    ]
  }
}
```

### Error Response Fields

| Field | Required | Description |
| ----- | -------- | ----------- |
| `error.code` | Yes | Machine-readable error code |
| `error.message` | Yes | Human-readable message |
| `error.details` | No | Additional error information |
| `error.details[].field` | No | Field that caused the error |
| `error.details[].message` | No | Field-specific error message |

### Error Codes

Projects **SHOULD** use consistent error codes:

```json
// Authentication errors
{ "error": { "code": "UNAUTHORIZED", "message": "Authentication required" }}
{ "error": { "code": "INVALID_TOKEN", "message": "Token has expired" }}

// Authorization errors
{ "error": { "code": "FORBIDDEN", "message": "Insufficient permissions" }}

// Validation errors
{ "error": { "code": "VALIDATION_ERROR", "message": "Invalid input data" }}
{ "error": { "code": "INVALID_FORMAT", "message": "Email format is invalid" }}

// Resource errors
{ "error": { "code": "NOT_FOUND", "message": "User not found" }}
{ "error": { "code": "ALREADY_EXISTS", "message": "Email already registered" }}

// Rate limiting
{ "error": { "code": "RATE_LIMITED", "message": "Too many requests" }}

// Server errors
{ "error": { "code": "INTERNAL_ERROR", "message": "Unexpected error" }}
```

### Problem Details (RFC 9457)

Projects **MAY** use Problem Details format[^4]:

```http
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/problem+json

{
  "type": "https://api.example.com/errors/validation",
  "title": "Validation Error",
  "status": 422,
  "detail": "The email field contains an invalid email address",
  "instance": "/users",
  "errors": [
    {
      "field": "email",
      "message": "Invalid email format"
    }
  ]
}
```

## Versioning

### URL Path Versioning

Projects **SHOULD** use URL path versioning:

```http
GET /api/v1/users HTTP/1.1
GET /api/v2/users HTTP/1.1
```

**Why**: Clear, explicit, easy to route, works with any client.

### Header Versioning

Alternative approach using custom headers:

```http
GET /api/users HTTP/1.1
API-Version: 2
```

Or Accept header:

```http
GET /api/users HTTP/1.1
Accept: application/vnd.example.v2+json
```

### Versioning Strategy

Projects **SHOULD** follow these versioning principles:

1. **Don't break existing clients**: Additive changes don't require new versions
2. **Version only when necessary**: Breaking changes require new version
3. **Support multiple versions**: Maintain N-1 or N-2 versions
4. **Deprecate gracefully**: Announce deprecation timeline

**Non-breaking changes** (no version bump):

- Adding new endpoints
- Adding optional fields to responses
- Adding optional request parameters

**Breaking changes** (version bump):

- Removing or renaming fields
- Changing field types
- Removing endpoints
- Changing authentication

## Authentication

### Authentication Methods

| Method          | Use Case           | Notes                  |
| --------------- | ------------------ | ---------------------- |
| API Keys        | Server-to-server   | Simple, long-lived     |
| JWT             | Stateless auth     | Self-contained tokens  |
| OAuth 2.0       | Third-party access | Industry standard      |
| Session cookies | Web applications   | Browser-based          |

### API Key Authentication

```http
# Header-based (recommended)
GET /users HTTP/1.1
Authorization: ApiKey sk_live_abc123

# Query parameter (less secure, avoid for sensitive operations)
GET /users?api_key=sk_live_abc123 HTTP/1.1
```

### Bearer Token (JWT)

```http
GET /users HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### OAuth 2.0 Scopes

```http
# Token with specific scopes
GET /users HTTP/1.1
Authorization: Bearer <token>

# Token represents: read:users write:orders
```

## Security

### HTTPS

Projects **MUST** use HTTPS for all API endpoints.

### Rate Limiting

Projects **MUST** implement rate limiting:

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1673789430

# When rate limited
HTTP/1.1 429 Too Many Requests
Retry-After: 60
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1673789430
```

### Rate Limiting Headers

| Header                  | Description                       |
| ----------------------- | --------------------------------- |
| `X-RateLimit-Limit`     | Maximum requests per window       |
| `X-RateLimit-Remaining` | Requests remaining in window      |
| `X-RateLimit-Reset`     | Unix timestamp when window resets |
| `Retry-After`           | Seconds to wait before retrying   |

### Input Validation

Projects **MUST** validate all input:

- Validate content types
- Validate and sanitize all user input
- Reject unexpected fields (strict mode)
- Enforce size limits on request bodies
- Validate file uploads (type, size, content)

### Security Headers

Projects **SHOULD** include security headers:

```http
HTTP/1.1 200 OK
Content-Type: application/json
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Cache-Control: no-store
```

### CORS

Projects **MUST** configure CORS appropriately:

```http
# Preflight request
OPTIONS /users HTTP/1.1
Origin: https://app.example.com
Access-Control-Request-Method: POST
Access-Control-Request-Headers: Content-Type, Authorization

# Preflight response
HTTP/1.1 204 No Content
Access-Control-Allow-Origin: https://app.example.com
Access-Control-Allow-Methods: GET, POST, PUT, DELETE
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Max-Age: 86400
```

## Caching

### Cache-Control Header

```http
# Cacheable for 1 hour
HTTP/1.1 200 OK
Cache-Control: public, max-age=3600

# Private cache only (user-specific data)
HTTP/1.1 200 OK
Cache-Control: private, max-age=300

# No caching
HTTP/1.1 200 OK
Cache-Control: no-store
```

### ETag Conditional Requests

```http
# Initial request
GET /users/123 HTTP/1.1

HTTP/1.1 200 OK
ETag: "abc123"
Content-Type: application/json

{"id": 123, "name": "Jane"}

# Conditional request
GET /users/123 HTTP/1.1
If-None-Match: "abc123"

HTTP/1.1 304 Not Modified
```

### Last-Modified Conditional Requests

```http
# Initial request
GET /users/123 HTTP/1.1

HTTP/1.1 200 OK
Last-Modified: Wed, 15 Jan 2025 10:30:00 GMT

# Conditional request
GET /users/123 HTTP/1.1
If-Modified-Since: Wed, 15 Jan 2025 10:30:00 GMT

HTTP/1.1 304 Not Modified
```

### Conditional Updates

```http
# Update only if ETag matches
PUT /users/123 HTTP/1.1
If-Match: "abc123"
Content-Type: application/json

{"name": "Jane Smith"}

# Success: ETag matched
HTTP/1.1 200 OK

# Conflict: Resource changed
HTTP/1.1 412 Precondition Failed
```

## Idempotency

### Idempotent Methods

| Method  | Idempotent | Safe |
| ------- | ---------- | ---- |
| GET     | Yes        | Yes  |
| HEAD    | Yes        | Yes  |
| OPTIONS | Yes        | Yes  |
| PUT     | Yes        | No   |
| DELETE  | Yes        | No   |
| POST    | No         | No   |
| PATCH   | No*        | No   |

### Idempotency Keys

Projects **SHOULD** support idempotency keys for non-idempotent operations:

```http
POST /payments HTTP/1.1
Idempotency-Key: a1b2c3d4-e5f6-7890-abcd-ef1234567890
Content-Type: application/json

{
  "amount": 100,
  "currency": "USD"
}
```

**How it works**:

1. Client generates unique idempotency key
2. Server stores key with response
3. Repeated requests with same key return cached response
4. Keys expire after 24 hours (typical)

## Bulk Operations

### Batch Create

```http
POST /users/batch HTTP/1.1
Content-Type: application/json

{
  "items": [
    {"email": "user1@example.com", "name": "User 1"},
    {"email": "user2@example.com", "name": "User 2"}
  ]
}
```

Response:

```json
{
  "succeeded": [
    {"id": 1, "email": "user1@example.com"}
  ],
  "failed": [
    {
      "index": 1,
      "error": {
        "code": "ALREADY_EXISTS",
        "message": "Email already registered"
      }
    }
  ]
}
```

### Batch Update/Delete

```http
PATCH /users/batch HTTP/1.1
Content-Type: application/json

{
  "ids": [1, 2, 3],
  "update": {
    "status": "inactive"
  }
}

DELETE /users/batch HTTP/1.1
Content-Type: application/json

{
  "ids": [1, 2, 3]
}
```

## Asynchronous Operations

### Long-Running Operations

For operations that can't complete immediately:

```http
POST /reports HTTP/1.1
Content-Type: application/json

{"type": "annual", "year": 2024}
```

Response:

```http
HTTP/1.1 202 Accepted
Location: /jobs/abc123

{
  "jobId": "abc123",
  "status": "pending",
  "links": {
    "self": "/jobs/abc123",
    "cancel": "/jobs/abc123/cancel"
  }
}
```

### Polling for Status

```http
GET /jobs/abc123 HTTP/1.1

HTTP/1.1 200 OK
Retry-After: 5

{
  "jobId": "abc123",
  "status": "processing",
  "progress": 45,
  "estimatedCompletion": "2025-01-15T11:00:00Z"
}
```

### Completion

```http
GET /jobs/abc123 HTTP/1.1

HTTP/1.1 200 OK

{
  "jobId": "abc123",
  "status": "completed",
  "result": {
    "reportUrl": "/reports/def456"
  }
}
```

## Documentation

### OpenAPI Specification

Projects **MUST** document APIs using OpenAPI (Swagger)[^5]:

```yaml
openapi: 3.1.0
info:
  title: User API
  version: 1.0.0
  description: API for managing users

paths:
  /users:
    get:
      summary: List users
      parameters:
        - name: status
          in: query
          schema:
            type: string
            enum: [active, inactive]
        - name: limit
          in: query
          schema:
            type: integer
            default: 20
            maximum: 100
      responses:
        '200':
          description: List of users
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/User'
```

### Documentation Requirements

Projects **MUST** document:

- All endpoints with descriptions
- Request/response schemas
- Authentication requirements
- Error responses
- Rate limits
- Examples

## HATEOAS

Projects **MAY** implement HATEOAS (Hypermedia as the Engine of Application State):

```json
{
  "id": 123,
  "email": "user@example.com",
  "status": "active",
  "links": {
    "self": "/users/123",
    "orders": "/users/123/orders",
    "deactivate": "/users/123/deactivate"
  }
}
```

**Benefits**:

- Discoverable API
- Decouples clients from URL structure
- Enables API evolution

**Considerations**:

- Increased payload size
- Complexity for simple APIs
- Not universally adopted

## Testing

### Contract Testing

Projects **SHOULD** test API contracts:

```python
def test_get_user_contract():
    response = client.get("/users/123")

    assert response.status_code == 200
    data = response.json()

    # Validate schema
    assert "id" in data
    assert "email" in data
    assert isinstance(data["id"], int)
    assert "@" in data["email"]
```

### Status Code Testing

```python
def test_create_user_returns_201():
    response = client.post("/users", json={"email": "test@example.com"})
    assert response.status_code == 201
    assert "Location" in response.headers

def test_get_nonexistent_user_returns_404():
    response = client.get("/users/999999")
    assert response.status_code == 404

def test_invalid_input_returns_422():
    response = client.post("/users", json={"email": "not-an-email"})
    assert response.status_code == 422
```

### Integration Testing

```python
def test_user_lifecycle():
    # Create
    create_response = client.post("/users", json={
        "email": "test@example.com",
        "name": "Test User"
    })
    assert create_response.status_code == 201
    user_id = create_response.json()["id"]

    # Read
    get_response = client.get(f"/users/{user_id}")
    assert get_response.status_code == 200
    assert get_response.json()["email"] == "test@example.com"

    # Update
    update_response = client.patch(f"/users/{user_id}", json={
        "name": "Updated Name"
    })
    assert update_response.status_code == 200

    # Delete
    delete_response = client.delete(f"/users/{user_id}")
    assert delete_response.status_code == 204

    # Verify deletion
    verify_response = client.get(f"/users/{user_id}")
    assert verify_response.status_code == 404
```

## See Also

- [GraphQL Best Practices](graphql.md) - Alternative API paradigm
- [FastAPI Guide](../frameworks/fastapi.md) - Python REST APIs with FastAPI
- [Django Guide](../frameworks/django.md) - Django REST Framework
- [Testing Guide](../process/testing.md) - General testing practices

## References

[^1]: [REST Architectural Style](https://ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm) - Roy Fielding's dissertation
[^2]: [RFC 7396 - JSON Merge Patch](https://datatracker.ietf.org/doc/html/rfc7396) - Simple partial updates
[^3]: [RFC 6902 - JSON Patch](https://datatracker.ietf.org/doc/html/rfc6902) - Explicit patch operations
[^4]: [RFC 9457 - Problem Details](https://datatracker.ietf.org/doc/html/rfc9457) - Standard error format
[^5]: [OpenAPI Specification](https://spec.openapis.org/oas/latest.html) - API documentation standard
