---
name: test-writer-go
description: "Go test patterns: table-driven, testify, httptest, benchmarks"
model: sonnet
---

# Test Writer: Go Module

> [Test Writer Agent](../test-writer.md) > Go

Go-specific guidance for test generation.

## Quick Reference

| Task | Tool | Command |
| ---- | ---- | ------- |
| Run tests | go test | `go test ./...` |
| Verbose | go test | `go test -v ./...` |
| Coverage | go test | `go test -cover ./...` |
| Coverage profile | go test | `go test -coverprofile=coverage.out ./...` |
| View coverage | go tool | `go tool cover -html=coverage.out` |

## Test File Conventions

- Test files: `*_test.go`
- Test functions: `func TestXxx(t *testing.T)`
- Benchmark functions: `func BenchmarkXxx(b *testing.B)`
- Example functions: `func ExampleXxx()`
- Test packages: Same package or `package foo_test`

## Basic Test Structure

```go
package calculator

import "testing"

func TestAdd(t *testing.T) {
    result := Add(2, 3)
    if result != 5 {
        t.Errorf("Add(2, 3) = %d; want 5", result)
    }
}

func TestAddNegative(t *testing.T) {
    result := Add(-1, 1)
    if result != 0 {
        t.Errorf("Add(-1, 1) = %d; want 0", result)
    }
}
```

## Table-Driven Tests

```go
func TestCalculate(t *testing.T) {
    tests := []struct {
        name     string
        a, b     int
        op       string
        want     int
        wantErr  bool
    }{
        {
            name: "add positive numbers",
            a: 2, b: 3, op: "+",
            want: 5,
        },
        {
            name: "subtract",
            a: 5, b: 3, op: "-",
            want: 2,
        },
        {
            name: "divide by zero",
            a: 10, b: 0, op: "/",
            wantErr: true,
        },
        {
            name: "invalid operator",
            a: 1, b: 1, op: "invalid",
            wantErr: true,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got, err := Calculate(tt.a, tt.b, tt.op)

            if (err != nil) != tt.wantErr {
                t.Errorf("Calculate() error = %v, wantErr %v", err, tt.wantErr)
                return
            }

            if got != tt.want {
                t.Errorf("Calculate() = %v, want %v", got, tt.want)
            }
        })
    }
}
```

## Testify Assertions

```go
import (
    "testing"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
)

func TestUserService(t *testing.T) {
    // assert continues on failure
    assert.Equal(t, 5, Add(2, 3))
    assert.NotNil(t, user)
    assert.True(t, user.IsActive)
    assert.Contains(t, users, expectedUser)
    assert.Len(t, items, 3)

    // require stops on failure
    require.NoError(t, err)
    require.NotNil(t, result)
}

func TestErrorHandling(t *testing.T) {
    _, err := ParseConfig("")

    assert.Error(t, err)
    assert.ErrorIs(t, err, ErrInvalidConfig)
    assert.ErrorContains(t, err, "invalid")
}
```

## Mocking with Interfaces

```go
// Define interface for dependency
type UserRepository interface {
    FindByID(ctx context.Context, id int64) (*User, error)
    Save(ctx context.Context, user *User) error
}

// Mock implementation
type mockUserRepo struct {
    findByIDFunc func(ctx context.Context, id int64) (*User, error)
    saveFunc     func(ctx context.Context, user *User) error
}

func (m *mockUserRepo) FindByID(ctx context.Context, id int64) (*User, error) {
    return m.findByIDFunc(ctx, id)
}

func (m *mockUserRepo) Save(ctx context.Context, user *User) error {
    return m.saveFunc(ctx, user)
}

func TestUserService_GetUser(t *testing.T) {
    expectedUser := &User{ID: 1, Name: "Test User"}

    repo := &mockUserRepo{
        findByIDFunc: func(ctx context.Context, id int64) (*User, error) {
            if id == 1 {
                return expectedUser, nil
            }
            return nil, ErrNotFound
        },
    }

    service := NewUserService(repo)

    user, err := service.GetUser(context.Background(), 1)

    require.NoError(t, err)
    assert.Equal(t, expectedUser, user)
}
```

## Testify Mock

```go
import (
    "github.com/stretchr/testify/mock"
)

type MockUserRepo struct {
    mock.Mock
}

func (m *MockUserRepo) FindByID(ctx context.Context, id int64) (*User, error) {
    args := m.Called(ctx, id)
    if args.Get(0) == nil {
        return nil, args.Error(1)
    }
    return args.Get(0).(*User), args.Error(1)
}

func TestWithTestifyMock(t *testing.T) {
    mockRepo := new(MockUserRepo)
    mockRepo.On("FindByID", mock.Anything, int64(1)).Return(&User{ID: 1}, nil)

    service := NewUserService(mockRepo)
    user, err := service.GetUser(context.Background(), 1)

    require.NoError(t, err)
    assert.Equal(t, int64(1), user.ID)
    mockRepo.AssertExpectations(t)
}
```

## HTTP Handler Testing

```go
import (
    "net/http"
    "net/http/httptest"
    "testing"
)

func TestGetUserHandler(t *testing.T) {
    req := httptest.NewRequest(http.MethodGet, "/users/1", nil)
    rec := httptest.NewRecorder()

    handler := NewUserHandler(mockService)
    handler.ServeHTTP(rec, req)

    assert.Equal(t, http.StatusOK, rec.Code)
    assert.Contains(t, rec.Body.String(), "Test User")
}

func TestCreateUserHandler(t *testing.T) {
    body := strings.NewReader(`{"name": "New User", "email": "new@example.com"}`)
    req := httptest.NewRequest(http.MethodPost, "/users", body)
    req.Header.Set("Content-Type", "application/json")
    rec := httptest.NewRecorder()

    handler.ServeHTTP(rec, req)

    assert.Equal(t, http.StatusCreated, rec.Code)
}
```

## Subtests and Parallel Execution

```go
func TestParallel(t *testing.T) {
    tests := []struct {
        name  string
        input int
        want  int
    }{
        {"positive", 5, 10},
        {"zero", 0, 0},
        {"negative", -3, -6},
    }

    for _, tt := range tests {
        tt := tt // capture range variable
        t.Run(tt.name, func(t *testing.T) {
            t.Parallel() // run subtests in parallel

            got := Double(tt.input)
            assert.Equal(t, tt.want, got)
        })
    }
}
```

## Coverage Commands

```bash
# Generate coverage profile
go test -coverprofile=coverage.out ./...

# View coverage in terminal
go tool cover -func=coverage.out

# Generate HTML report
go tool cover -html=coverage.out -o coverage.html

# Coverage with race detection
go test -race -coverprofile=coverage.out ./...

# Coverage for specific package
go test -coverprofile=coverage.out -coverpkg=./internal/... ./...
```

## Coverage Report Parsing

Parse `coverage.out`:

```text
mode: set
github.com/user/repo/pkg/calculator.go:10.32,12.2 1 1
github.com/user/repo/pkg/calculator.go:14.32,16.2 1 0
github.com/user/repo/pkg/calculator.go:18.32,20.2 1 1
```

Format: `file:startLine.startCol,endLine.endCol statements count`

## Benchmarks

```go
func BenchmarkCalculate(b *testing.B) {
    for i := 0; i < b.N; i++ {
        Calculate(100, 50, "+")
    }
}

func BenchmarkCalculateParallel(b *testing.B) {
    b.RunParallel(func(pb *testing.PB) {
        for pb.Next() {
            Calculate(100, 50, "+")
        }
    })
}
```

## See Also

- [Go Style Guide](../../../../guides/languages/go.md)
- [Testing Guide](../../../../guides/process/testing.md)
