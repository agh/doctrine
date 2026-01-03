# SQL Style Guide

> [Doctrine](../../README.md) > [Languages](../README.md) > SQL

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

Based on [SQL Style Guide](https://www.sqlstyle.guide/)[^1] with PostgreSQL focus.
Conventions work across PostgreSQL[^2], MySQL[^3], and SQLite[^4].

## Quick Reference

| Task | Tool | Command |
| ---- | ---- | ------- |
| Lint | SQLFluff[^5] | `sqlfluff lint` |
| Format | SQLFluff[^5] | `sqlfluff fix` |
| Type check | - | - |
| Semantic | - | - |
| Dead code | - | - |
| Coverage | - | - |
| Complexity | - | - |
| Fuzz | - | - |
| Test perf | - | - |

## Linting & Formatting: SQLFluff

SQLFluff[^5] is the world-class SQL linter, supporting 20+ dialects.

### Why SQLFluff

SQLFluff provides comprehensive linting and formatting for SQL with:

- Support for 20+ SQL dialects (PostgreSQL, MySQL, SQLite, etc.)
- Auto-fixing capabilities for common style violations
- Templating support (Jinja[^6], dbt[^7]) for SQL generation workflows
- Highly configurable rules matching project-specific style guides
- Active maintenance and community support

```bash
# Install
pip install sqlfluff

# Lint
sqlfluff lint .

# Fix automatically
sqlfluff fix .

# Specific dialect
sqlfluff lint --dialect postgres .
```

### Configuration (.sqlfluff)

```ini
[sqlfluff]
dialect = postgres
templater = jinja
max_line_length = 80
indent_unit = space

[sqlfluff:indentation]
indented_joins = true
indented_using_on = true
template_blocks_indent = true

[sqlfluff:layout:type:comma]
line_position = trailing

[sqlfluff:rules:capitalisation.keywords]
capitalisation_policy = upper

[sqlfluff:rules:capitalisation.identifiers]
capitalisation_policy = lower

[sqlfluff:rules:capitalisation.functions]
capitalisation_policy = upper

[sqlfluff:rules:aliasing.table]
aliasing = explicit

[sqlfluff:rules:aliasing.column]
aliasing = explicit
```

## Naming Conventions

### General Rules

- You **MUST** use `snake_case` for all identifiers
- You **SHOULD** avoid prefixes like `tbl_`, `vw_`, `sp_`
- You **MUST** keep names under 63 characters (PostgreSQL limit)
- You **MUST NOT** use SQL reserved keywords

### Tables

Table names **MUST** be plural nouns in `snake_case`.

```sql
-- Plural nouns
CREATE TABLE users (...);
CREATE TABLE order_items (...);
CREATE TABLE user_preferences (...);

-- NOT
CREATE TABLE user (...);
CREATE TABLE tbl_users (...);
```

### Columns

Column names **MUST** use descriptive `snake_case` and **SHOULD** avoid ambiguous single-word names.

```sql
-- Descriptive snake_case
CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    email_address TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    year_founded INTEGER  -- NOT just "year"
);
```

### Foreign Keys

Foreign key columns **MUST** follow the format: `referenced_table_singular_id`.

```sql
-- Format: referenced_table_singular_id
CREATE TABLE orders (
    id BIGINT PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),  -- NOT users_id
    shipping_address_id BIGINT REFERENCES addresses(id)
);
```

### Indexes

Index names **MUST** follow the format: `idx_table_column(s)` with optional `_unique` suffix.

```sql
-- Format: idx_table_column(s)
CREATE INDEX idx_users_email ON users(email_address);
CREATE INDEX idx_orders_user_created ON orders(user_id, created_at);
CREATE UNIQUE INDEX idx_users_email_unique ON users(email_address);
```

### Constraints

Constraint names **MUST** follow these formats:

- Primary keys: `table_pkey`
- Unique: `table_column_key`
- Foreign keys: `table_column_fkey`
- Check: `table_column_check`

```sql
ALTER TABLE users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id),
    ADD CONSTRAINT users_email_key UNIQUE (email_address),
    ADD CONSTRAINT users_age_check CHECK (age >= 0);

ALTER TABLE orders
    ADD CONSTRAINT orders_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id);
```

## Query Formatting

Queries **MUST** use consistent formatting with keywords in UPPERCASE and
identifiers in lowercase. SQL clauses **SHOULD** be on separate lines for
readability.

### SELECT Statements

```sql
SELECT
    u.id,
    u.email_address,
    u.created_at,
    COUNT(o.id) AS order_count
FROM users AS u
LEFT JOIN orders AS o
    ON u.id = o.user_id
WHERE u.is_active = true
    AND u.created_at >= '2024-01-01'
GROUP BY u.id, u.email_address, u.created_at
HAVING COUNT(o.id) > 0
ORDER BY u.created_at DESC
LIMIT 100;
```

### INSERT Statements

```sql
INSERT INTO users (
    email_address,
    display_name,
    is_active
)
VALUES (
    'user@example.com',
    'Example User',
    true
)
RETURNING id;
```

### UPDATE Statements

```sql
UPDATE users
SET
    display_name = 'New Name',
    updated_at = NOW()
WHERE id = 123
    AND is_active = true
RETURNING *;
```

## Data Types

### Prefer

You **SHOULD** prefer these data types:

```sql
-- Text
TEXT                    -- Variable length, no artificial limit
VARCHAR(255)            -- Only when limit is meaningful

-- Numbers
BIGINT                  -- IDs, counts
INTEGER                 -- Regular integers
NUMERIC(10,2)          -- Money, precise decimals
REAL, DOUBLE PRECISION -- Scientific, approximate

-- Dates
TIMESTAMP WITH TIME ZONE  -- Always use timezone-aware (MUST for timestamps)
DATE                      -- Date only
TIME WITH TIME ZONE       -- Time only

-- Other
UUID                    -- For distributed IDs
BOOLEAN                 -- MUST use for boolean values, NOT integers
JSONB                   -- JSON data (MUST use JSONB, NOT JSON)
```

### Avoid

You **SHOULD NOT** use these deprecated or problematic types:

```sql
-- CHAR(n)       -- Pads with spaces, no benefit
-- MONEY         -- PostgreSQL-specific, imprecise
-- SERIAL        -- Use IDENTITY instead
-- JSON          -- Use JSONB
```

## Migrations

### Naming

Migration files **MUST** follow the timestamp-based naming convention:

```text
YYYYMMDDHHMMSS_descriptive_name.sql
20240115143022_create_users_table.sql
20240115143523_add_email_index_to_users.sql
```

### Safe Patterns

You **SHOULD** use these safe migration patterns in production:

```sql
-- Add column (safe)
ALTER TABLE users ADD COLUMN phone_number TEXT;

-- Add NOT NULL column (safe with default)
ALTER TABLE users ADD COLUMN status TEXT NOT NULL DEFAULT 'active';

-- Add index concurrently (safe, no lock) - MUST use CONCURRENTLY in production
CREATE INDEX CONCURRENTLY idx_users_phone ON users(phone_number);

-- Rename column (breaks app if not coordinated) - MUST coordinate with app deployment
ALTER TABLE users RENAME COLUMN phone_number TO phone;
```

### Squawk (PostgreSQL Migration Linter)

```bash
# Install
pip install squawk

# Lint migrations
squawk migrations/*.sql
```

Squawk[^8] catches unsafe migration patterns specific to PostgreSQL.

### Why Squawk

Squawk provides PostgreSQL-specific migration safety analysis:

- Detects table-locking operations that cause downtime
- Identifies unsafe constraint additions
- Warns about missing CONCURRENTLY on index creation
- Prevents common PostgreSQL migration pitfalls
- Designed specifically for zero-downtime deployments

## Comments

You **SHOULD** add comments to tables and columns to document their purpose.
Comments **MUST** be updated when schema changes.

```sql
-- Table comments
COMMENT ON TABLE users IS 'Registered user accounts';

-- Column comments
COMMENT ON COLUMN users.email_address IS 'Primary email, used for login';

-- Update comments when schema changes!
```

## Pre-commit Configuration

```yaml
repos:
  - repo: https://github.com/sqlfluff/sqlfluff
    rev: 3.5.0
    hooks:
      - id: sqlfluff-lint
        args: [--dialect, postgres]
      - id: sqlfluff-fix
        args: [--dialect, postgres]
```

## CI Pipeline

```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install sqlfluff
      - run: sqlfluff lint --dialect postgres .
```

## Schema Anti-Patterns

These patterns cause real production problems that linters cannot catch.

### Entity-Attribute-Value (EAV) Tables

You **MUST NOT** use EAV tables for structured data. EAV destroys type safety,
prevents foreign keys, and makes queries complex.

```sql
-- BAD: EAV pattern - loses type safety, can't use foreign keys
CREATE TABLE product_attributes (
    product_id BIGINT,
    attribute_name TEXT,    -- "price", "weight", "color"
    attribute_value TEXT    -- Everything is a string!
);

-- Querying EAV is painful
SELECT
    p.name,
    MAX(CASE WHEN a.attribute_name = 'price' THEN a.attribute_value END) AS price,
    MAX(CASE WHEN a.attribute_name = 'color' THEN a.attribute_value END) AS color
FROM products AS p
LEFT JOIN product_attributes AS a ON p.id = a.product_id
GROUP BY p.id, p.name;

-- GOOD: Use proper columns with real types
CREATE TABLE products (
    id BIGINT PRIMARY KEY,
    name TEXT NOT NULL,
    price NUMERIC(10,2) NOT NULL,  -- Real type!
    weight_kg NUMERIC(8,3),
    color TEXT
);

-- Use JSONB for truly dynamic attributes
CREATE TABLE products (
    id BIGINT PRIMARY KEY,
    name TEXT NOT NULL,
    price NUMERIC(10,2) NOT NULL,
    custom_attributes JSONB DEFAULT '{}'  -- For genuinely variable data
);
```

### Time-Partitioned Table Names

You **MUST NOT** encode time periods in table names. This creates maintenance
burden and breaks queries when periods change.

```sql
-- BAD: Table names encode time
CREATE TABLE events_2024_01 (...);
CREATE TABLE events_2024_02 (...);
-- Now every query needs UNION ALL across all tables
-- Adding a new month requires schema changes

-- GOOD: Use database-native partitioning
CREATE TABLE events (
    id BIGINT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    event_type TEXT,
    payload JSONB
) PARTITION BY RANGE (created_at);

CREATE TABLE events_2024_q1 PARTITION OF events
    FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');
CREATE TABLE events_2024_q2 PARTITION OF events
    FOR VALUES FROM ('2024-04-01') TO ('2024-07-01');

-- Queries work on the parent table automatically
SELECT * FROM events WHERE created_at >= '2024-02-15';
```

### Separate Value and Unit Columns

You **SHOULD NOT** store numeric values separately from their units. This leads to unit mismatch bugs.

```sql
-- BAD: Unit stored separately - easy to mix up
CREATE TABLE measurements (
    id BIGINT PRIMARY KEY,
    value NUMERIC,
    unit TEXT  -- "kg", "lb", "g" - which is it?
);

-- GOOD: Unit in column name, single canonical unit
CREATE TABLE measurements (
    id BIGINT PRIMARY KEY,
    weight_kg NUMERIC(10,3),  -- Always kilograms
    distance_m NUMERIC(12,2)  -- Always meters
);

-- GOOD: For multi-unit storage, use composite type or normalize on write
CREATE TABLE shipments (
    id BIGINT PRIMARY KEY,
    weight_kg NUMERIC(10,3) NOT NULL,  -- Canonical unit
    weight_display_unit TEXT DEFAULT 'kg'  -- For UI only
);
```

## References

[^1]: SQL Style Guide - <https://www.sqlstyle.guide/>
[^2]: PostgreSQL Documentation - <https://www.postgresql.org/docs/>
[^3]: MySQL Documentation - <https://dev.mysql.com/doc/>
[^4]: SQLite Documentation - <https://www.sqlite.org/docs.html>
[^5]: SQLFluff - SQL Linter and Formatter - <https://www.sqlfluff.com/>
[^6]: Jinja - Template Engine for Python - <https://jinja.palletsprojects.com/>
[^7]: dbt - Data Build Tool - <https://www.getdbt.com/>
[^8]: Squawk - PostgreSQL Migration Linter - <https://github.com/sbdchd/squawk>

## See Also

- [Testing Guide](../testing.md) - Best practices for testing SQL queries and database interactions
