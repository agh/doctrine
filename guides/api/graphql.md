# GraphQL Best Practices

> [Doctrine](../../README.md) > [API Design](README.md) > GraphQL

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in
[RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

This guide covers language-agnostic GraphQL best practices for schema design,
queries, mutations, and API security. For framework-specific implementation,
see:

- [Strawberry (Python)](../frameworks/strawberry.md)
- Apollo Server (TypeScript) - Coming soon

## Why GraphQL?

GraphQL[^1] is a query language for APIs that gives clients the power to
request exactly the data they need. Unlike REST, GraphQL uses a single
endpoint and lets clients specify their data requirements through queries.

**Use GraphQL when**:

- Clients have diverse data needs (mobile vs. web)
- Reducing over-fetching and under-fetching improves performance
- You need real-time updates via subscriptions
- Strong typing and introspection benefit your developer experience

**Consider REST when**:

- Caching is critical (HTTP caching is simpler with REST)
- Your API is simple with predictable access patterns
- You're building public APIs where simplicity matters
- File uploads are the primary use case

## Schema Design

### Naming Conventions

Projects **MUST** follow GraphQL naming conventions:

| Element | Convention | Example |
| ------- | ---------- | ------- |
| Types | PascalCase | `User`, `OrderItem` |
| Fields | camelCase | `firstName`, `createdAt` |
| Arguments | camelCase | `userId`, `includeDeleted` |
| Enums | SCREAMING_SNAKE_CASE values | `ORDER_STATUS`, `PENDING` |
| Mutations | verbNoun | `createUser`, `deleteOrder` |
| Queries | noun or getNoun | `user`, `users`, `getOrderById` |

```graphql
# Good
type User {
  id: ID!
  firstName: String!
  lastName: String!
  createdAt: DateTime!
}

enum OrderStatus {
  PENDING
  PROCESSING
  SHIPPED
  DELIVERED
}

type Query {
  user(id: ID!): User
  users(status: UserStatus): [User!]!
}

type Mutation {
  createUser(input: CreateUserInput!): User!
  updateUser(id: ID!, input: UpdateUserInput!): User!
  deleteUser(id: ID!): Boolean!
}
```

**Why**: Consistent naming makes schemas predictable and self-documenting.
These conventions match the GraphQL specification examples and community
standards.

### Non-Nullable by Design

Projects **SHOULD** make fields non-nullable by default, using nullable only
when needed:

```graphql
# Good: Non-nullable by default
type User {
  id: ID!
  email: String!
  name: String!
  bio: String          # Nullable: users may not have a bio
  deletedAt: DateTime  # Nullable: null means not deleted
}

# Good: Non-nullable lists with non-nullable elements
type Query {
  users: [User!]!      # Never null, never contains null
}
```

**Why**: Non-nullable fields simplify client code by eliminating null checks.
Reserve nullability for fields that genuinely might not exist.

### List Nullability

Projects **MUST** understand list nullability patterns:

| Declaration | Meaning |
| ----------- | ------- |
| `[User!]!` | Non-null list of non-null users (recommended) |
| `[User]!` | Non-null list that may contain null users |
| `[User!]` | Nullable list of non-null users |
| `[User]` | Nullable list that may contain null users |

**Recommendation**: Use `[Type!]!` for most lists. Return empty arrays instead
of null.

### Input Types

Projects **MUST** use input types for mutations with complex arguments:

```graphql
# Good: Dedicated input type
input CreateUserInput {
  email: String!
  password: String!
  name: String!
  role: UserRole = USER
}

input UpdateUserInput {
  email: String
  name: String
  role: UserRole
}

type Mutation {
  createUser(input: CreateUserInput!): CreateUserPayload!
  updateUser(id: ID!, input: UpdateUserInput!): UpdateUserPayload!
}
```

**Why**: Input types group related arguments, enable reuse, and make schema
evolution easier. They also clarify which fields are required for creation vs.
optional for updates.

### Payload Types

Projects **SHOULD** return payload types from mutations:

```graphql
type CreateUserPayload {
  user: User
  errors: [UserError!]!
}

type UserError {
  field: String
  message: String!
  code: ErrorCode!
}

enum ErrorCode {
  VALIDATION_ERROR
  NOT_FOUND
  UNAUTHORIZED
  CONFLICT
}

type Mutation {
  createUser(input: CreateUserInput!): CreateUserPayload!
}
```

**Why**: Payload types allow returning both data and errors in a type-safe way.
This "errors as data" pattern gives clients structured error information
without relying on GraphQL's error array.

## Query Design

### Pagination

Projects **MUST** implement pagination for list queries. Projects **SHOULD**
use cursor-based pagination (Relay Connection spec)[^2]:

```graphql
type Query {
  users(
    first: Int
    after: String
    last: Int
    before: String
    filter: UserFilter
  ): UserConnection!
}

type UserConnection {
  edges: [UserEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type UserEdge {
  node: User!
  cursor: String!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}
```

**Why**: Cursor-based pagination is stable under insertions/deletions, unlike
offset-based pagination. The Connection pattern is a GraphQL community
standard supported by many client libraries.

**Alternative**: For simpler use cases, offset-based pagination is acceptable:

```graphql
type Query {
  users(limit: Int = 20, offset: Int = 0): UserPage!
}

type UserPage {
  items: [User!]!
  totalCount: Int!
  hasMore: Boolean!
}
```

### Filtering and Sorting

Projects **SHOULD** use input types for complex filtering:

```graphql
input UserFilter {
  status: UserStatus
  createdAfter: DateTime
  createdBefore: DateTime
  search: String
  roles: [UserRole!]
}

enum UserSortField {
  CREATED_AT
  NAME
  EMAIL
}

enum SortDirection {
  ASC
  DESC
}

input UserSort {
  field: UserSortField!
  direction: SortDirection = ASC
}

type Query {
  users(
    filter: UserFilter
    sort: UserSort
    first: Int = 20
    after: String
  ): UserConnection!
}
```

### Field Arguments

Projects **SHOULD** add arguments to fields when transformations are needed:

```graphql
type User {
  id: ID!
  name: String!
  avatarUrl(size: Int = 100): String!
  createdAt(format: DateFormat = ISO8601): String!
}

enum DateFormat {
  ISO8601
  UNIX_TIMESTAMP
  RELATIVE
}
```

## Mutation Design

### Verb-Noun Naming

Projects **MUST** name mutations with verb-noun format:

```graphql
# Good
type Mutation {
  createUser(input: CreateUserInput!): CreateUserPayload!
  updateUser(id: ID!, input: UpdateUserInput!): UpdateUserPayload!
  deleteUser(id: ID!): DeleteUserPayload!
  sendPasswordReset(email: String!): SendPasswordResetPayload!
  approveOrder(id: ID!): ApproveOrderPayload!
}

# Bad
type Mutation {
  user(input: UserInput!): User!        # Unclear action
  userUpdate(id: ID!): User!            # Wrong order
  doSendEmail(to: String!): Boolean!    # Redundant "do"
}
```

### Idempotency

Projects **SHOULD** design mutations to be idempotent where possible:

```graphql
type Mutation {
  # Idempotent: Setting to a specific state
  setOrderStatus(id: ID!, status: OrderStatus!): Order!

  # Idempotent: Using idempotency keys
  createPayment(
    input: CreatePaymentInput!
    idempotencyKey: String!
  ): CreatePaymentPayload!
}
```

**Why**: Idempotent mutations can be safely retried on network failures without
causing duplicate side effects.

### Batch Operations

Projects **MAY** provide batch mutations for performance:

```graphql
type Mutation {
  # Single operation
  deleteUser(id: ID!): DeleteUserPayload!

  # Batch operation
  deleteUsers(ids: [ID!]!): DeleteUsersPayload!
}

type DeleteUsersPayload {
  deletedIds: [ID!]!
  errors: [BatchError!]!
}

type BatchError {
  id: ID!
  message: String!
}
```

## Error Handling

### Errors as Data

Projects **SHOULD** use union types or payload types for expected errors:

```graphql
union CreateUserResult = User | ValidationErrors | EmailTakenError

type ValidationErrors {
  errors: [FieldError!]!
}

type FieldError {
  field: String!
  message: String!
}

type EmailTakenError {
  message: String!
  suggestedEmail: String
}

type Mutation {
  createUser(input: CreateUserInput!): CreateUserResult!
}
```

**Client handling**:

```graphql
mutation CreateUser($input: CreateUserInput!) {
  createUser(input: $input) {
    ... on User {
      id
      email
    }
    ... on ValidationErrors {
      errors {
        field
        message
      }
    }
    ... on EmailTakenError {
      message
      suggestedEmail
    }
  }
}
```

**Why**: Union types make error cases explicit and type-safe. Clients must
handle each case, preventing silent failures.

### GraphQL Errors

Reserve the GraphQL errors array for unexpected errors:

- Server errors (database down, network issues)
- Authentication failures (not logged in)
- Authorization failures (not permitted)
- Invalid queries (syntax errors, unknown fields)

```json
{
  "errors": [
    {
      "message": "Not authenticated",
      "extensions": {
        "code": "UNAUTHENTICATED"
      }
    }
  ]
}
```

## Security

### Query Depth Limiting

Projects **MUST** limit query depth to prevent deeply nested attacks:

```graphql
# Without depth limiting, this could be exploited:
query MaliciousQuery {
  users {
    orders {
      user {
        orders {
          user {
            orders {
              # ... infinite nesting
            }
          }
        }
      }
    }
  }
}
```

**Recommendation**: Set maximum depth to 10-15 for most applications.

### Query Complexity Analysis

Projects **SHOULD** implement query complexity analysis:

```graphql
# Assign costs to fields
type Query {
  user(id: ID!): User      # Cost: 1
  users(first: Int): [User!]!  # Cost: first * 1
}

type User {
  id: ID!                  # Cost: 0
  orders: [Order!]!        # Cost: 10 (expensive)
}
```

Reject queries exceeding a maximum cost threshold.

### Rate Limiting

Projects **MUST** implement rate limiting:

- Limit by IP address for unauthenticated requests
- Limit by user/API key for authenticated requests
- Consider query complexity in rate calculations

### Disable Introspection in Production

Projects **SHOULD** disable introspection in production environments:

**Why**: Introspection exposes your entire schema, making it easier for
attackers to find vulnerabilities. Provide schema documentation through other
means.

### Input Validation

Projects **MUST** validate all input data:

```graphql
input CreateUserInput {
  email: String!      # Validate: email format
  password: String!   # Validate: min length, complexity
  name: String!       # Validate: max length, no scripts
}
```

Validate at the GraphQL layer before business logic.

### Authentication and Authorization

Projects **MUST** implement authentication at the transport layer and
authorization at the field level:

```graphql
type Query {
  # Public
  publicPosts: [Post!]!

  # Requires authentication
  me: User! @authenticated

  # Requires specific permission
  adminUsers: [User!]! @hasRole(role: ADMIN)
}

type User {
  id: ID!
  email: String!

  # Only visible to user themselves or admins
  ssn: String @isOwnerOrAdmin
}
```

## Performance

### N+1 Query Problem

Projects **MUST** use DataLoaders (or equivalent batching) to prevent N+1 queries:

```graphql
# Without DataLoader: N+1 queries
query {
  users {       # 1 query
    orders {    # N queries (one per user)
      items {   # N*M queries
        product { }
      }
    }
  }
}
```

DataLoaders batch multiple loads into single queries and cache results within
a request.

### Field-Level Caching

Projects **MAY** implement field-level caching for expensive computations:

```graphql
type User {
  id: ID!
  # Cached for 5 minutes
  orderCount: Int! @cacheControl(maxAge: 300)

  # Never cached (real-time)
  currentBalance: Float! @cacheControl(maxAge: 0)
}
```

### Persisted Queries

Projects **SHOULD** use persisted queries in production:

**Benefits**:

- Smaller request payloads (send hash instead of full query)
- Prevents arbitrary queries from untrusted clients
- Enables query whitelisting

```graphql
# Instead of sending full query
POST /graphql
{
  "query": "query GetUser($id: ID!) { user(id: $id) { id name } }",
  "variables": { "id": "123" }
}

# Send query hash
POST /graphql
{
  "extensions": {
    "persistedQuery": {
      "sha256Hash": "abc123..."
    }
  },
  "variables": { "id": "123" }
}
```

## Schema Evolution

### Deprecation

Projects **MUST** deprecate fields before removal:

```graphql
type User {
  id: ID!
  name: String! @deprecated(reason: "Use firstName and lastName")
  firstName: String!
  lastName: String!
}
```

**Process**:

1. Add new field alongside old field
2. Mark old field as deprecated with reason
3. Monitor usage of deprecated field
4. Remove after deprecation period (e.g., 6 months)

### Additive Changes

Projects **SHOULD** prefer additive changes over breaking changes:

**Safe changes (additive)**:

- Adding new types
- Adding new fields to existing types
- Adding optional arguments to fields
- Adding new enum values

**Breaking changes (avoid)**:

- Removing types or fields
- Changing field types
- Making nullable fields non-nullable
- Removing enum values

### Versioning

Projects **SHOULD NOT** version GraphQL APIs. Instead:

- Use deprecation for field evolution
- Use feature flags for major changes
- Maintain backwards compatibility

**Why**: GraphQL's schema introspection and deprecation system provides
built-in evolution mechanisms. URL versioning (/v1/, /v2/) fragments your API.

## Subscriptions

### When to Use Subscriptions

Projects **SHOULD** use subscriptions for:

- Real-time notifications
- Live data feeds
- Collaborative features

Projects **SHOULD NOT** use subscriptions for:

- Data that changes infrequently
- One-time requests (use queries)
- Large data transfers (use pagination)

### Subscription Design

```graphql
type Subscription {
  # Filter by ID
  orderStatusChanged(orderId: ID!): Order!

  # Filter by type
  notificationReceived(types: [NotificationType!]): Notification!
}

enum NotificationType {
  MESSAGE
  MENTION
  SYSTEM
}
```

**Why**: Allow clients to filter subscriptions to relevant events, reducing
unnecessary data transfer.

## Documentation

### Schema Documentation

Projects **MUST** document types and fields:

```graphql
"""
A user in the system.
"""
type User {
  """
  Unique identifier for the user.
  """
  id: ID!

  """
  User's email address. Used for authentication and notifications.
  Must be unique across all users.
  """
  email: String!

  """
  User's display name. Maximum 100 characters.
  """
  name: String!
}
```

### Argument Documentation

```graphql
type Query {
  """
  Search for users matching the given criteria.
  Returns paginated results using cursor-based pagination.
  """
  users(
    """
    Filter users by status, date range, or search term.
    """
    filter: UserFilter

    """
    Maximum number of users to return. Default: 20, Max: 100.
    """
    first: Int = 20

    """
    Cursor for forward pagination.
    """
    after: String
  ): UserConnection!
}
```

## Testing

### Schema Testing

Projects **MUST** test schema validity:

```python
def test_schema_is_valid():
    # Schema should compile without errors
    assert schema is not None

def test_schema_has_required_types():
    type_names = [t.name for t in schema.type_map.values()]
    assert "User" in type_names
    assert "Query" in type_names
    assert "Mutation" in type_names
```

### Resolver Testing

Projects **MUST** test resolvers independently:

```python
async def test_create_user_resolver():
    result = await schema.execute(
        """
        mutation CreateUser($input: CreateUserInput!) {
          createUser(input: $input) {
            user { id email }
            errors { field message }
          }
        }
        """,
        variable_values={
            "input": {
                "email": "test@example.com",
                "password": "password123",
                "name": "Test"
            }
        },
        context_value=context,
    )
    assert result.errors is None
    assert result.data["createUser"]["user"]["email"] == "test@example.com"
```

### Integration Testing

Projects **SHOULD** test full query flows:

```python
async def test_user_with_orders_flow():
    # Create user
    create_result = await create_user(...)
    user_id = create_result.data["createUser"]["user"]["id"]

    # Create orders
    await create_order(user_id=user_id, ...)

    # Query user with orders
    query_result = await schema.execute(
        """
        query GetUserWithOrders($id: ID!) {
          user(id: $id) {
            orders {
              id
              status
            }
          }
        }
        """,
        variable_values={"id": user_id},
    )
    assert len(query_result.data["user"]["orders"]) > 0
```

## See Also

- [Strawberry Guide](../frameworks/strawberry.md) - Python GraphQL with Strawberry
- [FastAPI Guide](../frameworks/fastapi.md) - REST API patterns for Python
- [Testing Guide](../process/testing.md) - General testing practices

## References

[^1]: [GraphQL Specification](https://spec.graphql.org/) - Official GraphQL specification
[^2]: [Relay Connection Specification](https://relay.dev/graphql/connections.htm) - Cursor-based pagination standard
