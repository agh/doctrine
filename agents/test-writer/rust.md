---
name: test-writer-rust
description: "Rust testing: unit/integration, mockall, proptest, doc tests"
model: sonnet
---

# Test Writer: Rust Module

> [Test Writer Agent](../test-writer.md) > Rust

Rust-specific guidance for test generation.

## Quick Reference

| Task | Tool | Command |
| ---- | ---- | ------- |
| Run tests | cargo | `cargo test` |
| Run specific | cargo | `cargo test test_name` |
| Coverage | tarpaulin | `cargo tarpaulin` |
| Coverage | llvm-cov | `cargo llvm-cov` |
| Doc tests | cargo | `cargo test --doc` |

## Test Organization

### Unit Tests (In-Module)

```rust
// src/lib.rs or src/calculator.rs

pub fn add(a: i32, b: i32) -> i32 {
    a + b
}

pub fn divide(a: i32, b: i32) -> Result<i32, &'static str> {
    if b == 0 {
        Err("Cannot divide by zero")
    } else {
        Ok(a / b)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn add_positive_numbers() {
        assert_eq!(add(2, 3), 5);
    }

    #[test]
    fn add_negative_numbers() {
        assert_eq!(add(-2, -3), -5);
    }

    #[test]
    fn divide_valid_numbers() {
        assert_eq!(divide(10, 2), Ok(5));
    }

    #[test]
    fn divide_by_zero_returns_error() {
        assert_eq!(divide(10, 0), Err("Cannot divide by zero"));
    }
}
```

### Integration Tests

```rust
// tests/integration_test.rs

use my_crate::Calculator;

#[test]
fn calculator_full_workflow() {
    let calc = Calculator::new();

    calc.push(5);
    calc.push(3);
    let result = calc.add();

    assert_eq!(result, 8);
}
```

## Assertion Macros

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn basic_assertions() {
        // Equality
        assert_eq!(add(2, 2), 4);
        assert_ne!(add(2, 2), 5);

        // Boolean
        assert!(is_valid("test"));
        assert!(!is_empty("test"));

        // With custom message
        assert_eq!(
            result, expected,
            "Expected {} but got {} for input {:?}",
            expected, result, input
        );
    }

    #[test]
    fn float_comparison() {
        let result = calculate_pi();
        let epsilon = 0.0001;
        assert!((result - 3.14159).abs() < epsilon);
    }
}
```

## Testing Panics

```rust
#[test]
#[should_panic]
fn panics_on_invalid_input() {
    process(None); // Should panic
}

#[test]
#[should_panic(expected = "index out of bounds")]
fn panics_with_specific_message() {
    let v = vec![1, 2, 3];
    let _ = v[10];
}
```

## Testing Results

```rust
#[test]
fn parse_returns_result() -> Result<(), ParseError> {
    let config = parse_config("valid: true")?;
    assert_eq!(config.valid, true);
    Ok(())
}

#[test]
fn parse_error_contains_message() {
    let result = parse_config("invalid");

    assert!(result.is_err());
    let err = result.unwrap_err();
    assert!(err.to_string().contains("invalid"));
}
```

## Test Fixtures

```rust
struct TestContext {
    db: MockDatabase,
    service: UserService,
}

impl TestContext {
    fn new() -> Self {
        let db = MockDatabase::new();
        let service = UserService::new(db.clone());
        Self { db, service }
    }
}

#[test]
fn user_service_creates_user() {
    let ctx = TestContext::new();

    let user = ctx.service.create("Test User").unwrap();

    assert_eq!(user.name, "Test User");
    assert!(ctx.db.contains(user.id));
}
```

## Mocking with mockall

```rust
use mockall::{automock, predicate::*};

#[automock]
trait UserRepository {
    fn find_by_id(&self, id: u64) -> Option<User>;
    fn save(&self, user: &User) -> Result<(), Error>;
}

#[test]
fn service_returns_user_from_repo() {
    let mut mock_repo = MockUserRepository::new();
    mock_repo
        .expect_find_by_id()
        .with(eq(1))
        .times(1)
        .returning(|_| Some(User { id: 1, name: "Test".into() }));

    let service = UserService::new(Box::new(mock_repo));
    let user = service.get_user(1);

    assert!(user.is_some());
    assert_eq!(user.unwrap().name, "Test");
}

#[test]
fn service_handles_missing_user() {
    let mut mock_repo = MockUserRepository::new();
    mock_repo
        .expect_find_by_id()
        .returning(|_| None);

    let service = UserService::new(Box::new(mock_repo));
    let user = service.get_user(999);

    assert!(user.is_none());
}
```

## Async Tests

```rust
use tokio;

#[tokio::test]
async fn async_fetch_returns_data() {
    let client = HttpClient::new();

    let result = client.fetch("https://api.example.com/data").await;

    assert!(result.is_ok());
}

#[tokio::test]
async fn async_with_timeout() {
    let result = tokio::time::timeout(
        Duration::from_secs(5),
        slow_operation()
    ).await;

    assert!(result.is_ok());
}
```

## Property-Based Testing

```rust
use proptest::prelude::*;

proptest! {
    #[test]
    fn add_is_commutative(a: i32, b: i32) {
        prop_assert_eq!(add(a, b), add(b, a));
    }

    #[test]
    fn parse_roundtrip(s in "[a-z]{1,10}") {
        let parsed = parse(&s)?;
        let serialized = serialize(&parsed);
        prop_assert_eq!(s, serialized);
    }

    #[test]
    fn vec_length_preserved(v: Vec<i32>) {
        let processed = process(v.clone());
        prop_assert_eq!(v.len(), processed.len());
    }
}
```

## Test Attributes

```rust
#[test]
#[ignore] // Skip by default, run with `cargo test -- --ignored`
fn expensive_test() {
    // Long-running test
}

#[test]
#[cfg(feature = "integration")]
fn integration_test() {
    // Only runs when feature is enabled
}

#[test]
#[cfg(not(target_os = "windows"))]
fn unix_only_test() {
    // Platform-specific test
}
```

## Coverage Commands

```bash
# Using cargo-tarpaulin
cargo install cargo-tarpaulin
cargo tarpaulin --out Html --output-dir coverage/

# Using cargo-llvm-cov
cargo install cargo-llvm-cov
cargo llvm-cov --html --output-dir coverage/

# Coverage with specific features
cargo tarpaulin --features "feature1,feature2"

# Fail if below threshold
cargo tarpaulin --fail-under 80
```

## Coverage Report Parsing

Parse Cobertura XML from tarpaulin:

```xml
<coverage line-rate="0.85" branch-rate="0.70" version="1.0">
  <packages>
    <package name="my_crate">
      <classes>
        <class filename="src/lib.rs" line-rate="0.90">
          <lines>
            <line number="10" hits="5"/>
            <line number="15" hits="0"/>
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
```

## Doc Tests

```rust
/// Adds two numbers together.
///
/// # Examples
///
/// ```
/// use my_crate::add;
///
/// assert_eq!(add(2, 3), 5);
/// assert_eq!(add(-1, 1), 0);
/// ```
///
/// # Panics
///
/// This function does not panic.
pub fn add(a: i32, b: i32) -> i32 {
    a + b
}

/// Parses a configuration string.
///
/// # Examples
///
/// ```
/// # use my_crate::parse_config;
/// let config = parse_config("key=value").unwrap();
/// assert_eq!(config.get("key"), Some("value"));
/// ```
///
/// ```should_panic
/// # use my_crate::parse_config;
/// parse_config("invalid").unwrap(); // This panics
/// ```
pub fn parse_config(s: &str) -> Result<Config, Error> {
    // ...
}
```

## Benchmarks

```rust
// benches/benchmark.rs (requires nightly or criterion)

use criterion::{black_box, criterion_group, criterion_main, Criterion};
use my_crate::fibonacci;

fn bench_fibonacci(c: &mut Criterion) {
    c.bench_function("fib 20", |b| {
        b.iter(|| fibonacci(black_box(20)))
    });
}

criterion_group!(benches, bench_fibonacci);
criterion_main!(benches);
```

## See Also

- [Rust Style Guide](../../../../guides/languages/rust.md)
- [Testing Guide](../../../../guides/process/testing.md)
