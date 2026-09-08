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

Keyset pagination selects the next page by comparing against the last row of
the previous page rather than by counting rows. Projects **MUST** order keyset
results by a tuple that is unique across the whole collection, and **MUST**
carry every component of that tuple in the cursor:

```sql
-- Don't: a non-unique sort key drops every row tied with the boundary value
SELECT id, created_at FROM users
WHERE created_at > :after_created_at
ORDER BY created_at
LIMIT :limit;

-- Do: order by and compare the unique tuple (created_at, id)
SELECT id, created_at FROM users
WHERE (created_at, id) > (:after_created_at, :after_id)
ORDER BY created_at, id
LIMIT :limit;
```

**Why**: `created_at` is not unique. Seed rows 1-4 where IDs 2 and 3 share
`2026-01-02T00:00:00Z`; a first page of two returns IDs 1 and 2. The
timestamp-only predicate then returns only ID 4, so ID 3 never appears on any
page and the loss is silent. The tuple predicate returns IDs 3 and 4.

Projects **MUST** use the expanded predicate where the database engine does
not support row-value comparison:

```sql
WHERE created_at > :after_created_at
   OR (created_at = :after_created_at AND id > :after_id)
```

Cursors **MUST** be a single opaque token, not a bare sort value, so that
clients cannot construct a boundary that omits part of the tuple:

```http
# Don't: a raw, partial boundary the client can edit
GET /users?limit=20&sort=created_at&after=2026-01-02T00:00:00Z HTTP/1.1

# Do: first page, then one opaque cursor carrying both tuple components
GET /users?limit=20&sort=created_at HTTP/1.1
GET /users?limit=20&after=eyJjcmVhdGVkX2F0IjoiMjAyNi0wMS0wMlQwMDowMDowMFoiLCJpZCI6Mn0 HTTP/1.1
```

```python
import base64
import json


def encode_cursor(row: dict) -> str:
    """Pack every ordering component into one opaque cursor."""
    payload = json.dumps(
        {"created_at": row["created_at"], "id": row["id"]},
        separators=(",", ":"),
    )
    return base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")


def decode_cursor(cursor: str) -> tuple[str, int]:
    """Reject anything that is not a well-formed cursor for this sort."""
    padded = cursor + "=" * (-len(cursor) % 4)
    payload = json.loads(base64.urlsafe_b64decode(padded))
    if set(payload) != {"created_at", "id"}:
        raise ValueError("invalid cursor")
    return payload["created_at"], payload["id"]
```

Base64 is an encoding, not a security boundary. Servers **MUST** validate
every decoded cursor and **MUST** reject cursors whose components do not match
the requested sort, returning `400 Bad Request`.

Projects **MUST** test keyset pagination against tied sort values, asserting
that every row is returned exactly once:

```python
def test_keyset_pagination_returns_tied_rows_exactly_once():
    seed_users([(1, "2026-01-01T00:00:00Z"), (2, "2026-01-02T00:00:00Z"),
                (3, "2026-01-02T00:00:00Z"), (4, "2026-01-03T00:00:00Z")])

    seen, cursor = [], None
    while True:
        page = client.get("/users", params={"limit": 2, "after": cursor}).json()
        seen.extend(user["id"] for user in page["data"])
        cursor = page["cursors"]["after"]
        if not page["meta"]["hasMore"]:
            break

    assert seen == [1, 2, 3, 4]
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

### Credentials, Token Formats and Delegated Authorisation

These three concerns are routinely conflated. Keep them separate:

| Concern                 | Examples                    | What it settles                       |
| ----------------------- | --------------------------- | ------------------------------------- |
| Credential              | API key, session cookie     | Who the caller claims to be           |
| Token format            | JWT, opaque reference token | How a bearer token is encoded and checked |
| Delegated authorisation | OAuth 2.0                   | How a user grants an application limited access |

**Why**: JWT is a token format, not an authentication scheme; a JWT is carried
with the `Bearer` scheme defined in RFC 6750. OAuth 2.0 can issue tokens in
either format. Treating "JWT" as an authentication method produces APIs that
verify a signature and then trust whatever the payload asserts.

### Authentication Methods

| Method                   | Use case             | Notes                                    |
| ------------------------ | -------------------- | ---------------------------------------- |
| API keys                 | Server-to-server     | Long-lived; scope, rotate and revoke them |
| Bearer tokens (RFC 6750) | Any client           | Short-lived; carries a JWT or opaque token |
| OAuth 2.0 (BCP 240)      | Third-party access   | Delegated, scoped, user-consented         |
| Session cookies          | Browser applications | Require `Secure`, `HttpOnly`, `SameSite` and CSRF defence |

### Credentials in URLs

Projects **MUST NOT** accept API keys, access tokens, refresh tokens, session
identifiers or passwords in a URL path or query string, and **MUST** reject
requests that supply them there:

```http
# Don't: the credential is now in access logs, browser history, proxy
# metadata, Referer headers, bookmarks and error-tracking payloads
GET /users?api_key=<key> HTTP/1.1

# Do: carry the credential in a request header
GET /users HTTP/1.1
Authorization: ApiKey <key>
```

**Why**: [RFC 9700](https://www.rfc-editor.org/rfc/rfc9700.html) section 4.3.2
states that clients **MUST NOT** pass access tokens in a URI query parameter.
The same exposure applies to proprietary API keys, which OWASP's
[REST Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html)
lists among the sensitive values that must be kept out of URLs and logs.
Whether the *operation* is sensitive is irrelevant: the *credential* is
reusable, and the URL is recorded by systems the API does not control.

Projects **MUST** redact credentials from telemetry:

- Redact `Authorization`, `Proxy-Authorization`, `Cookie` and `Set-Cookie`
  headers in application logs, access logs, traces and crash reports.
- Redact query strings by allowlist, not by pattern-matching known key
  prefixes; an unknown format is still a credential.
- Treat any credential that has reached a log as compromised and rotate it.

### Bearer Tokens

```http
GET /users HTTP/1.1
Authorization: Bearer <access-token>
```

The token may be a JWT or an opaque reference token. Opaque tokens **MUST** be
validated by introspection against the issuing server; JWTs **MUST** be
validated locally as below.

### Validating JWTs

Projects that accept JWTs **MUST** follow
[RFC 8725](https://www.rfc-editor.org/rfc/rfc8725.html) (BCP 225):

- Take the permitted algorithms from server configuration, never from the
  token's `alg` header, and reject `none`.
- Resolve the signing key from a configured issuer key set. Never fetch keys
  from a token-supplied `jku` or `x5u` URL; that is an SSRF vector.
- Reject a token whose `iss` is not the configured issuer.
- Reject a token whose `aud` does not name this API.
- Reject expired (`exp`) and not-yet-valid (`nbf`) tokens, and require `exp`
  and `iat` to be present.
- Reject tokens issued for another purpose, such as an ID token or a refresh
  token presented as an access token.

```python
# Don't: decoding is not validation
claims = jwt.decode(token, options={"verify_signature": False})

# Do: pin the algorithm, issuer and audience, and require claims
def validate_access_token(token: str) -> dict:
    return jwt.decode(
        token,
        key=jwks.signing_key_for(token),
        algorithms=["RS256"],
        issuer=ISSUER,
        audience=AUDIENCE,
        options={"require": ["exp", "iat", "iss", "aud", "sub"]},
    )
```

**Why**: A signature proves only that *someone* holding *a* key signed the
payload. Without pinned algorithms it is verified with an attacker-chosen
algorithm; without `iss` and `aud` checks, a valid token minted for a
different service is accepted here.

### OAuth 2.0

Projects using OAuth 2.0 **MUST** follow
[RFC 9700](https://www.rfc-editor.org/rfc/rfc9700.html) (BCP 240, January
2025), which updates RFCs 6749, 6750 and 6819:

- Authorisation servers **MUST** support PKCE (RFC 7636) and public clients
  **MUST** use it. `S256` is the only challenge method that does not expose
  the verifier in the authorisation request.
- The resource owner password credentials grant **MUST NOT** be used.
- Clients **SHOULD NOT** use the implicit grant or any other response type
  that returns an access token in the authorisation response.
- Access tokens **SHOULD** be audience-restricted, and a resource server
  **MUST** refuse a request whose token was not issued for it.
- Refresh tokens for public clients **MUST** be sender-constrained or
  rotated.

OAuth 2.1 consolidates these practices but is still an Internet-Draft
([`draft-ietf-oauth-v2-1-16`](https://datatracker.ietf.org/doc/draft-ietf-oauth-v2-1/),
3 September 2026). Projects **MAY** adopt its recommendations early but
**MUST NOT** cite it as a published standard, because its requirements can
still change.

### OAuth 2.0 Scopes

```http
GET /users HTTP/1.1
Authorization: Bearer <access-token>

# Token scopes: read:users write:orders
```

Projects **MUST** enforce scope on the server for every request. A scope in a
token records what the user granted the client; it is not evidence that this
request is permitted. See [Function-Level Authorisation](#function-level-authorisation).

## Security

### Threat Model

Projects **MUST** address every risk in the
[OWASP API Security Top 10 (2023)](https://owasp.org/API-Security/editions/2023/en/0x11-t10/),
vendored in this repository at
`reference/security/owasp/top10-api-2023.json`:

| Risk                                                 | Where this guide addresses it |
| ---------------------------------------------------- | ----------------------------- |
| API1 Broken object level authorization               | [Object-Level Authorisation](#object-level-authorisation) |
| API2 Broken authentication                           | [Authentication](#authentication) |
| API3 Broken object property level authorization      | [Property-Level Authorisation](#property-level-authorisation) |
| API4 Unrestricted resource consumption               | [Rate Limiting](#rate-limiting), [Pagination Defaults](#pagination-defaults), [Resource Consumption](#resource-consumption) |
| API5 Broken function level authorization             | [Function-Level Authorisation](#function-level-authorisation) |
| API6 Unrestricted access to sensitive business flows | [Sensitive Business Flows](#sensitive-business-flows) |
| API7 Server side request forgery                     | [Server-Side Request Forgery](#server-side-request-forgery) |
| API8 Security misconfiguration                       | [HTTPS](#https), [Security Headers](#security-headers), [CORS](#cors) |
| API9 Improper inventory management                   | [API Inventory](#api-inventory) |
| API10 Unsafe consumption of APIs                     | [Consuming Upstream APIs](#consuming-upstream-apis) |

**Why**: Authenticating a request settles who is calling. It does not settle
whether that caller may read this object, write this property or invoke this
function. Those are the top three risks in the list, and each needs its own
check.

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

### Object-Level Authorisation

Every endpoint that accepts an object identifier **MUST** verify, on every
request, that the authenticated caller may act on that specific object, using
the server's own record of ownership rather than any client-supplied value:

```python
# Don't: the identifier comes from the caller, so any authenticated user
# can read any order
def get_order_unsafe(order_id, actor):
    return db.orders[order_id]


# Do: authorise the object itself, and do not confirm that it exists
def get_order(order_id, actor):
    order = db.orders.get(order_id)
    if order is None or order.owner_id != actor.id:
        raise NotFound()
    return order
```

**Why**: Authentication establishes that the caller is a valid user, not that
they own order 1. Returning `404` rather than `403` for an object the caller
may not see avoids confirming that the identifier exists.

Projects **MUST NOT** rely on identifiers being unguessable. Random UUIDs
raise the cost of enumeration; they are not an authorisation control.

### Property-Level Authorisation

Projects **MUST** allowlist the properties each caller may write, and the
properties serialised into each response:

```python
WRITABLE_BY_OWNER = {"name", "email"}
READABLE_BY_OWNER = {"id", "name", "email", "status"}


def update_user(user_id, body, actor):
    rejected = set(body) - WRITABLE_BY_OWNER
    if rejected:
        raise UnprocessableContent(sorted(rejected))
    return db.users.update_row(user_id, **body)


def serialise_user(user, actor):
    fields = set(READABLE_BY_OWNER)
    if actor.is_admin:
        fields |= {"credit_limit"}
    return {name: getattr(user, name) for name in sorted(fields)}
```

**Why**: Rejecting unknown fields catches typos, not privilege escalation: a
writable-but-privileged field such as `credit_limit` or `is_admin` is a known
field. Serialising the whole record leaks properties the caller is not
entitled to read, even when the client never displays them.

### Function-Level Authorisation

Projects **MUST** deny by default. Every route declares the permission it
requires, and a route with no declared permission is unreachable:

```python
ROUTE_PERMISSIONS = {
    ("GET", "/users/{id}"): "users:read",
    ("DELETE", "/users/{id}"): "users:delete",
}


def authorise_route(method, route, actor):
    required = ROUTE_PERMISSIONS.get((method, route))
    if required is None or required not in granted_permissions(actor):
        raise Forbidden()
```

**Why**: Administrative endpoints are commonly protected only by being
undocumented or hidden in the client. Neither stops a caller from sending
`DELETE /users/123`. Deny-by-default also stops a newly added route from
shipping with no check at all.

### Resource Consumption

[Rate Limiting](#rate-limiting) and [Pagination Defaults](#pagination-defaults)
bound request volume and page size. Projects **MUST** additionally bound:

- Request body size, upload size and decompressed size
- Execution time and memory per request
- Fan-out per request: records returned, joins performed, upstream calls made
- Operations that spend money or a third-party quota — email, SMS, telephone
  calls, biometric checks — under their own per-identity quota, separate from
  the general request rate

**Why**: One request inside the rate limit can cost more than the entire
limit. A password-reset endpoint that sends an SMS is bounded by the cost of
the SMS, not by requests per minute.

### Sensitive Business Flows

Projects **MUST** identify the flows whose automated abuse harms the business
— purchase, booking, referral, voucher redemption, posting — and **MUST**
apply controls proportionate to that harm:

- Per-identity and per-flow quotas stricter than the general rate limit
- Detection of non-human usage patterns, such as request timing and
  device or client consistency
- Step-up verification before an irreversible or high-value step

**Why**: This risk does not come from a defect. Every request is individually
valid and individually authorised; the harm comes from volume and timing, so
only a flow-level control sees it.

### Server-Side Request Forgery

Where an endpoint fetches a caller-supplied URL — webhooks, avatar imports,
document conversion — projects **MUST** validate the destination before
connecting:

```python
ALLOWED_WEBHOOK_HOSTS = {"hooks.example.com"}


def check_webhook_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_WEBHOOK_HOSTS:
        raise UnprocessableContent("destination not allowed")
    for *_ignored, address in socket.getaddrinfo(parsed.hostname, 443,
                                                 socket.AF_INET):
        if not ipaddress.ip_address(address[0]).is_global:
            raise UnprocessableContent("destination not allowed")
    return url
```

Projects **MUST** also:

- Connect to the address that was validated, or delegate the fetch to a proxy
  that enforces the allowlist; resolving and then connecting by name leaves a
  DNS-rebinding window
- Disable redirect following, or revalidate every redirect target
- Apply a dedicated timeout and response size limit to the fetch
- Send no credentials, cookies or instance-metadata tokens with the fetch
- Return a fixed error, never the upstream body, status or connection error

**Why**: Checking the URL string alone is not enough, because a permitted
hostname can resolve to a private or link-local address such as the cloud
instance metadata endpoint at `169.254.169.254`. Echoing the upstream response
turns the fetch into a read primitive for the internal network.

### API Inventory

Projects **MUST** maintain an inventory of every deployed API, recording:

- Every host and environment, including staging, debug and internal
  deployments
- Every version in service, its owner and its retirement date
- The data classes each version exposes

Projects **MUST NOT** leave a superseded version running past its announced
retirement date, and **MUST NOT** expose non-production environments to the
public internet. See [Versioning Strategy](#versioning-strategy).

**Why**: A retired version still carries the defects that were fixed in the
current one, and non-production hosts usually combine weaker controls with
real data.

### Consuming Upstream APIs

Projects **MUST** treat responses from third-party and internal upstream APIs
as untrusted input:

- Validate every response against a schema before use, exactly as for client
  input
- Use TLS for every upstream call, including internal ones, and verify
  certificates
- Apply timeouts, response size limits and circuit breaking
- Do not follow redirects returned by an upstream without revalidating the
  target

**Why**: Data arriving from an integration is usually trusted more than data
arriving from a client, so an attacker who compromises the integration
inherits that trust.

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

Projects **MUST** document APIs using OpenAPI (Swagger)[^5]. Every published
description **MUST** resolve all of its own references and **MUST** pass a
pinned validator in CI, so that readers can copy it and generate working
clients:

```yaml
openapi: 3.1.0
info:
  title: User API
  version: 1.0.0
  description: API for managing users.
  license:
    name: Apache-2.0
    identifier: Apache-2.0
servers:
  - url: https://api.example.com/v1
    description: Production
security:
  - bearerAuth: []
paths:
  /users:
    get:
      operationId: listUsers
      summary: List users
      description: Returns one page of users, oldest first.
      parameters:
        - name: status
          in: query
          description: Filter by account status.
          schema:
            type: string
            enum: [active, inactive]
        - name: limit
          in: query
          description: Page size. Larger values are capped at the maximum.
          schema:
            type: integer
            default: 20
            maximum: 100
      responses:
        '200':
          description: One page of users.
          headers:
            X-RateLimit-Limit:
              $ref: '#/components/headers/RateLimitLimit'
            X-RateLimit-Remaining:
              $ref: '#/components/headers/RateLimitRemaining'
            X-RateLimit-Reset:
              $ref: '#/components/headers/RateLimitReset'
          content:
            application/json:
              schema:
                type: object
                required: [data, meta]
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/User'
                  meta:
                    $ref: '#/components/schemas/PageMeta'
              examples:
                firstPage:
                  summary: A single-user page
                  value:
                    data:
                      - id: 123
                        email: jane@example.com
                        status: active
                    meta:
                      hasMore: false
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/RateLimited'
    post:
      operationId: createUser
      summary: Create a user
      description: Registers a user and returns the created resource.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/NewUser'
            examples:
              minimal:
                summary: Minimum required fields
                value:
                  email: jane@example.com
      responses:
        '201':
          description: The created user.
          headers:
            Location:
              description: URL of the created user.
              schema:
                type: string
                format: uri-reference
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '422':
          $ref: '#/components/responses/ValidationFailed'
        '429':
          $ref: '#/components/responses/RateLimited'
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: OAuth 2.0 access token. Never accepted in a query string.
  headers:
    RateLimitLimit:
      description: Maximum requests per window.
      schema:
        type: integer
    RateLimitRemaining:
      description: Requests remaining in the current window.
      schema:
        type: integer
    RateLimitReset:
      description: Unix timestamp at which the window resets.
      schema:
        type: integer
  schemas:
    User:
      type: object
      required: [id, email, status]
      properties:
        id:
          type: integer
        email:
          type: string
          format: email
        status:
          type: string
          enum: [active, inactive]
    NewUser:
      type: object
      required: [email]
      properties:
        email:
          type: string
          format: email
        name:
          type: string
          maxLength: 200
    PageMeta:
      type: object
      required: [hasMore]
      properties:
        hasMore:
          type: boolean
        cursor:
          type: string
          description: Opaque cursor for the next page.
    Error:
      type: object
      required: [error]
      properties:
        error:
          type: object
          required: [code, message]
          properties:
            code:
              type: string
            message:
              type: string
            details:
              type: array
              items:
                type: object
                properties:
                  field:
                    type: string
                  message:
                    type: string
  responses:
    Unauthorized:
      description: Authentication is missing or invalid.
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          examples:
            unauthorized:
              value:
                error:
                  code: UNAUTHORIZED
                  message: Authentication required
    ValidationFailed:
      description: The request was well formed but semantically invalid.
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          examples:
            invalidEmail:
              value:
                error:
                  code: VALIDATION_ERROR
                  message: The request contains invalid data
                  details:
                    - field: email
                      message: Invalid email format
    RateLimited:
      description: The client exceeded its rate limit.
      headers:
        Retry-After:
          description: Seconds to wait before retrying.
          schema:
            type: integer
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          examples:
            rateLimited:
              value:
                error:
                  code: RATE_LIMITED
                  message: Too many requests
```

### Documentation Requirements

Projects **MUST** document:

- All endpoints with descriptions
- Request/response schemas
- Authentication requirements
- Error responses
- Rate limits
- Examples

### Validating the Description

Projects **MUST** validate the description in CI with a pinned validator:

```bash
npx --yes @redocly/cli@2.51.2 lint openapi.yaml
```

**Why**: An unresolvable `$ref`, an undeclared security scheme or a missing
error response is easy to miss in review and breaks every generated client.
Pinning the validator version keeps the gate reproducible.

The description above passes with no errors. It reports one warning,
`no-server-example.com`, because [RFC 2606](https://datatracker.ietf.org/doc/html/rfc2606)
reserves `example.com` for documentation; production descriptions name a real
host.

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
