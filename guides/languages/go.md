# Go Style Guide

> [Doctrine](../../README.md) > [Languages](../README.md) > Go

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

Extends [Google Go Style Guide](google/go.md). See also
[Google Go Decisions](google/go-decisions.md) and
[Google Go Best Practices](google/go-best-practices.md).

## Quick Reference

| Task | Tool | Command |
| ---- | ---- | ------- |
| Lint | golangci-lint[^1] | `golangci-lint run` |
| Format | gofmt[^2] | `gofmt -w .` |
| Format | goimports[^3] | `goimports -w .` |
| Type check | built-in | `go build ./...` |
| Semantic | Staticcheck[^4] | via golangci-lint |
| Dead code | deadcode[^5] | `deadcode ./...` |
| Coverage | go test[^6] | `go test -cover ./...` |
| Complexity | gocyclo[^7] | via golangci-lint |
| Fuzz | native | `go test -fuzz=Fuzz` |
| Test perf | go test[^6] | `go test -parallel=4` |

## Linting: golangci-lint

Projects **MUST** use golangci-lint[^1] for linting Go code.

### Why golangci-lint?

- **Performance**: 5x faster than running linters separately through parallel execution and shared caching
- **Comprehensiveness**: Aggregates 120+ linters in a single tool
- **Industry standard**: De facto standard in the Go ecosystem with widespread adoption
- **Configuration**: Single YAML file for all linter settings
- **CI integration**: Official GitHub Actions support with automatic caching

```bash
# Install
go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest

# Run
golangci-lint run

# Run with auto-fix
golangci-lint run --fix
```

### Configuration (.golangci.yml)

```yaml
run:
  timeout: 5m

linters:
  enable:
    - staticcheck      # Comprehensive static analysis
    - gosimple         # Simplifications
    - govet            # Suspicious constructs
    - errcheck         # Unchecked errors
    - gosec            # Security issues
    - revive           # Opinionated linter
    - gocyclo          # Cyclomatic complexity
    - misspell         # Spelling
    - unconvert        # Unnecessary conversions
    - unparam          # Unused parameters
    - gocritic         # Highly extensible linter
    - prealloc         # Slice preallocation
    - exportloopref    # Loop variable capture

linters-settings:
  gocyclo:
    min-complexity: 15
  govet:
    enable-all: true
  revive:
    rules:
      - name: blank-imports
      - name: context-as-argument
      - name: error-return
      - name: error-strings
      - name: exported
```

## Formatting: gofmt + goimports

Projects **MUST** use gofmt[^2] or goimports[^3] for formatting Go code.
Projects **SHOULD** prefer goimports as it provides automatic import management
in addition to formatting.

### Why gofmt/goimports?

- **Zero configuration**: Eliminates formatting debates and bike-shedding
- **Consistency**: Single canonical format across the entire Go ecosystem
- **Tooling**: Built into the language toolchain, guaranteed compatibility
- **Automatic**: goimports adds/removes imports automatically, reducing manual work

```bash
# Format all files
gofmt -w .

# Format and organize imports
goimports -w .
```

There are no configuration options. This is intentional.

## Context Patterns

Projects **MUST** propagate context through the call stack. Context carries
deadlines, cancellation signals, and request-scoped values.

### Why Context Matters

- **Cancellation**: Allows graceful shutdown when requests are cancelled
- **Timeouts**: Prevents runaway operations from consuming resources
- **Tracing**: Carries request IDs and tracing information across service boundaries

### Context Rules

```go
// Context MUST be the first parameter, named ctx
func ProcessOrder(ctx context.Context, orderID string) error {
    // Check for cancellation before expensive operations
    select {
    case <-ctx.Done():
        return ctx.Err()
    default:
    }

    // Pass context to downstream calls
    user, err := fetchUser(ctx, orderID)
    if err != nil {
        return err
    }
    return chargePayment(ctx, user)
}
```

### Anti-patterns

```go
// BAD: Storing context in a struct
type Service struct {
    ctx context.Context  // Never do this
}

// BAD: Using context.Background() deep in the call stack
func deepFunction() {
    doSomething(context.Background())  // Loses cancellation signal
}

// GOOD: Accept context as parameter
func deepFunction(ctx context.Context) {
    doSomething(ctx)
}
```

## Error Wrapping

Projects **SHOULD** wrap errors with context using `fmt.Errorf` and `%w`. This
preserves the error chain for debugging while adding context.

### Why Wrap Errors

- **Debugging**: Stack of context shows where errors originated
- **Programmatic handling**: `errors.Is()` and `errors.As()` work through wrapped errors
- **User messages**: Can extract user-friendly messages at API boundaries

### Error Wrapping Patterns

```go
import (
    "errors"
    "fmt"
)

// Wrap with context using %w
func LoadConfig(path string) (*Config, error) {
    data, err := os.ReadFile(path)
    if err != nil {
        return nil, fmt.Errorf("load config %s: %w", path, err)
    }

    var cfg Config
    if err := json.Unmarshal(data, &cfg); err != nil {
        return nil, fmt.Errorf("parse config %s: %w", path, err)
    }
    return &cfg, nil
}

// Check wrapped errors with errors.Is()
if errors.Is(err, os.ErrNotExist) {
    // Handle missing file
}

// Extract typed errors with errors.As()
var pathErr *os.PathError
if errors.As(err, &pathErr) {
    log.Printf("path error on %s: %v", pathErr.Path, pathErr.Err)
}
```

### Sentinel Errors

Define sentinel errors for conditions callers need to check programmatically:

```go
var (
    ErrNotFound     = errors.New("not found")
    ErrUnauthorized = errors.New("unauthorized")
)

func GetUser(id string) (*User, error) {
    user := db.Find(id)
    if user == nil {
        return nil, fmt.Errorf("user %s: %w", id, ErrNotFound)
    }
    return user, nil
}

// Caller can check
if errors.Is(err, ErrNotFound) {
    return http.StatusNotFound
}
```

### Handle Errors Once

**MUST NOT** both log and return an error. Choose one:

```go
// BAD: Logs AND returns - error gets logged multiple times
func process() error {
    if err := doThing(); err != nil {
        log.Printf("failed: %v", err)  // Logged here
        return err                      // And logged by caller
    }
    return nil
}

// GOOD: Return with context, let caller decide
func process() error {
    if err := doThing(); err != nil {
        return fmt.Errorf("process: %w", err)
    }
    return nil
}

// GOOD: Log at the top level only
func main() {
    if err := process(); err != nil {
        log.Fatalf("fatal: %v", err)
    }
}
```

## Dead Code Detection

Projects **SHOULD** use deadcode[^5] to identify unused functions and methods.

```bash
# Install
go install golang.org/x/tools/cmd/deadcode@latest

# Run
deadcode ./...
```

## Code Coverage

Projects **MUST** track code coverage using Go's built-in coverage tools.
Projects **SHOULD** enforce minimum coverage thresholds in CI.

```bash
# Run tests with coverage
go test -cover ./...

# Generate coverage profile
go test -coverprofile=coverage.out ./...

# View in browser
go tool cover -html=coverage.out

# Check coverage threshold (via script)
go test -coverprofile=coverage.out ./...
COVERAGE=$(go tool cover -func=coverage.out | grep total | awk '{print $3}' | sed 's/%//')
if (( $(echo "$COVERAGE < 80" | bc -l) )); then
  echo "Coverage $COVERAGE% is below 80%"
  exit 1
fi
```

## Cyclomatic Complexity

Projects **SHOULD** monitor cyclomatic complexity using gocyclo[^7] (via
golangci-lint). Functions with complexity over 15 **SHOULD** be refactored.

Via golangci-lint with gocyclo enabled:

```yaml
linters-settings:
  gocyclo:
    min-complexity: 15  # Report functions with complexity > 15
```

Or standalone:

```bash
go install github.com/fzipp/gocyclo/cmd/gocyclo@latest
gocyclo -over 15 .
```

## Fuzzing: Native Go Fuzzing (1.18+)

Projects **SHOULD** use Go's native fuzzing for testing functions that parse
untrusted input or have complex edge cases.

### Why Native Go Fuzzing?

- **Built-in**: No external dependencies, part of the standard toolchain since Go 1.18
- **Integrated**: Works seamlessly with existing `go test` infrastructure
- **Coverage-guided**: Uses code coverage to discover new execution paths
- **Corpus management**: Automatically manages and minimizes test corpus

```go
func FuzzReverse(f *testing.F) {
    // Seed corpus
    f.Add("hello")
    f.Add("world")

    f.Fuzz(func(t *testing.T, s string) {
        rev := Reverse(s)
        doubleRev := Reverse(rev)
        if s != doubleRev {
            t.Errorf("double reverse mismatch: %q != %q", s, doubleRev)
        }
    })
}
```

```bash
# Run fuzzer
go test -fuzz=FuzzReverse -fuzztime=30s

# Run with specific corpus
go test -fuzz=FuzzReverse -fuzztime=1m ./...
```

## Benchmarking

Projects **SHOULD** write benchmarks for performance-critical code.

### Why Benchmarking Matters

- **Optimization validation**: Prove that optimizations actually improve performance
- **Regression detection**: Catch performance regressions in CI
- **Memory profiling**: Identify allocation-heavy code paths
- **Comparison**: Compare implementations objectively

### Writing Benchmarks

```go
func BenchmarkFibonacci(b *testing.B) {
    for i := 0; i < b.N; i++ {
        Fibonacci(20)
    }
}

// Benchmark with different input sizes
func BenchmarkSort(b *testing.B) {
    sizes := []int{100, 1000, 10000}
    for _, size := range sizes {
        b.Run(fmt.Sprintf("size=%d", size), func(b *testing.B) {
            data := generateRandomSlice(size)
            b.ResetTimer() // Exclude setup time
            for i := 0; i < b.N; i++ {
                sort.Ints(data)
            }
        })
    }
}

// Benchmark with memory allocation reporting
func BenchmarkConcat(b *testing.B) {
    b.ReportAllocs()
    for i := 0; i < b.N; i++ {
        concat("hello", "world")
    }
}
```

### Running Benchmarks

```bash
# Run all benchmarks
go test -bench=. ./...

# Run specific benchmark with memory stats
go test -bench=BenchmarkSort -benchmem ./...

# Run benchmarks for 10 seconds each
go test -bench=. -benchtime=10s ./...

# Run benchmarks multiple times for statistical validity
go test -bench=. -count=5 ./...

# Compare benchmarks with benchstat
go install golang.org/x/perf/cmd/benchstat@latest
go test -bench=. -count=10 > old.txt
# Make changes...
go test -bench=. -count=10 > new.txt
benchstat old.txt new.txt
```

### Benchmark Best Practices

```go
// GOOD: Reset timer after expensive setup
func BenchmarkProcessFile(b *testing.B) {
    data, err := os.ReadFile("testdata/large.json")
    if err != nil {
        b.Fatal(err)
    }
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        processJSON(data)
    }
}

// GOOD: Use b.RunParallel for concurrent benchmarks
func BenchmarkConcurrentMap(b *testing.B) {
    m := &sync.Map{}
    b.RunParallel(func(pb *testing.PB) {
        for pb.Next() {
            m.Store("key", "value")
            m.Load("key")
        }
    })
}

// BAD: Setup cost included in benchmark
func BenchmarkBad(b *testing.B) {
    for i := 0; i < b.N; i++ {
        data, _ := os.ReadFile("large.json") // Setup in loop!
        processJSON(data)
    }
}
```

## Test Performance

Projects **SHOULD** run tests in parallel mode. Projects **MUST** run tests
with the race detector in CI.

```bash
# Parallel tests (default: GOMAXPROCS)
go test -parallel=8 ./...

# Run specific benchmarks
go test -bench=. -benchmem ./...

# Short mode for CI
go test -short ./...

# Race detector (slower but catches data races)
go test -race ./...

# Compile tests once, run many times
go test -c -o test.exe ./mypackage
./test.exe -test.v
```

### Caching

Go caches test results by default. Force re-run:

```bash
go clean -testcache
go test ./...
```

## Pre-commit Configuration

Projects **SHOULD** use pre-commit hooks to enforce formatting and linting before commits.

```yaml
repos:
  - repo: https://github.com/golangci/golangci-lint
    rev: v1.62.0
    hooks:
      - id: golangci-lint

  - repo: https://github.com/dnephin/pre-commit-golang
    rev: v0.5.1
    hooks:
      - id: go-fmt
      - id: go-imports
      - id: go-vet
```

## CI Pipeline

Projects **MUST** run linting and tests in CI. Projects **MUST** include race
detection in CI test runs.

```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: '1.23'
      - uses: golangci/golangci-lint-action@v6

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: '1.23'
      - run: go test -race -coverprofile=coverage.out ./...
      - run: go tool cover -func=coverage.out
```

## Dependencies & Package Management

Projects **MUST** use Go modules (go mod) for dependency management.
Projects **MUST** commit both `go.mod` and `go.sum` to version control.

### Why Go Modules?

- **Official**: Standard dependency management system since Go 1.11
- **Reproducible**: MVS algorithm ensures consistent builds across environments
- **Cryptographic verification**: go.sum checksums prevent supply chain attacks
- **Version selection**: Automatic minimum version selection prevents dependency conflicts
- **No external tools**: Built into the Go toolchain

```bash
# Initialize a new module
go mod init github.com/user/repo

# Add dependencies (automatically updates go.mod)
go get github.com/pkg/errors@latest
go get github.com/pkg/errors@v0.9.1

# Update dependencies
go get -u ./...

# Tidy up (remove unused, add missing)
go mod tidy

# Verify dependencies
go mod verify

# Download dependencies to local cache
go mod download
```

### go.mod and go.sum

Both files **MUST** be committed to version control.

```go
// go.mod
module github.com/user/repo

go 1.23

require (
    github.com/pkg/errors v0.9.1
    golang.org/x/sync v0.8.0
)
```

`go.sum` contains cryptographic checksums for dependency verification.

### Minimum Version Selection (MVS)

Go uses MVS algorithm: always selects the minimum required version that
satisfies all constraints. This ensures reproducible builds.

```bash
# View dependency graph
go mod graph

# See why a dependency is needed
go mod why github.com/pkg/errors
```

### Vulnerability Scanning

Projects **SHOULD** use govulncheck[^8] to scan for known vulnerabilities.
Projects **SHOULD** run vulnerability scans in CI.

```bash
# Install govulncheck
go install golang.org/x/vuln/cmd/govulncheck@latest

# Scan for vulnerabilities
govulncheck ./...

# JSON output for CI
govulncheck -json ./...
```

### Dependabot Configuration

Projects **SHOULD** use Dependabot[^9] or similar tools for automated dependency updates.

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "gomod"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
    groups:
      minor-updates:
        update-types:
          - "minor"
          - "patch"
```

## E2E & Acceptance Testing

Projects **SHOULD** use appropriate testing tools based on their needs:
httptest[^10] for HTTP APIs, chromedp[^11] for browser automation, or
godog[^12] for BDD.

### httptest for API Testing

```go
func TestUserHandler(t *testing.T) {
    req := httptest.NewRequest("GET", "/users/123", nil)
    w := httptest.NewRecorder()

    handler := NewUserHandler()
    handler.ServeHTTP(w, req)

    if w.Code != http.StatusOK {
        t.Errorf("got %d, want %d", w.Code, http.StatusOK)
    }

    var user User
    json.NewDecoder(w.Body).Decode(&user)
    if user.ID != 123 {
        t.Errorf("got ID %d, want 123", user.ID)
    }
}
```

### chromedp for Browser Testing

```go
import "github.com/chromedp/chromedp"[^11]

func TestLoginFlow(t *testing.T) {
    ctx, cancel := chromedp.NewContext(context.Background())
    defer cancel()

    var title string
    err := chromedp.Run(ctx,
        chromedp.Navigate("http://localhost:8080/login"),
        chromedp.SendKeys(`input[name="email"]`, "user@example.com"),
        chromedp.SendKeys(`input[name="password"]`, "secret"),
        chromedp.Click(`button[type="submit"]`),
        chromedp.WaitVisible(`#dashboard`),
        chromedp.Title(&title),
    )

    if err != nil {
        t.Fatal(err)
    }
    if title != "Dashboard" {
        t.Errorf("got title %q, want Dashboard", title)
    }
}
```

### godog for BDD/Cucumber

```go
// features/login.feature
// Feature: User Login
//   Scenario: Valid credentials
//     Given I am on the login page
//     When I enter valid credentials
//     Then I should see the dashboard

import "github.com/cucumber/godog"[^12]

func InitializeScenario(ctx *godog.ScenarioContext) {
    ctx.Step(`^I am on the login page$`, iAmOnLoginPage)
    ctx.Step(`^I enter valid credentials$`, iEnterValidCredentials)
    ctx.Step(`^I should see the dashboard$`, iShouldSeeDashboard)
}

func TestFeatures(t *testing.T) {
    suite := godog.TestSuite{
        ScenarioInitializer: InitializeScenario,
        Options: &godog.Options{
            Format: "pretty",
            Paths:  []string{"features"},
        },
    }

    if suite.Run() != 0 {
        t.Fatal("non-zero status returned")
    }
}
```

## Mocking with gomock

Projects **SHOULD** use gomock[^16] for generating mock implementations of
interfaces in unit tests.

### Why gomock?

- **Type-safe**: Generated mocks are type-checked at compile time
- **Interface-based**: Works with Go's interface system, promoting testable design
- **Flexible expectations**: Support for exact, any, and custom matchers
- **Ordered verification**: Can verify call order when needed
- **Official**: Maintained by the Go team (uber-go/mock fork is also popular)

### Installation and Code Generation

```bash
# Install mockgen
go install go.uber.org/mock/mockgen@latest

# Generate mocks from interface (source mode)
mockgen -source=repository.go -destination=mocks/repository_mock.go -package=mocks

# Generate mocks from package (reflect mode)
mockgen -destination=mocks/client_mock.go -package=mocks github.com/user/app Client
```

### Interface Design for Testability

```go
// Define interfaces for dependencies
type UserRepository interface {
    FindByID(ctx context.Context, id string) (*User, error)
    Save(ctx context.Context, user *User) error
}

type EmailSender interface {
    Send(ctx context.Context, to, subject, body string) error
}

// Service depends on interfaces, not implementations
type UserService struct {
    repo   UserRepository
    mailer EmailSender
}

func NewUserService(repo UserRepository, mailer EmailSender) *UserService {
    return &UserService{repo: repo, mailer: mailer}
}
```

### Using Generated Mocks

```go
import (
    "testing"
    "go.uber.org/mock/gomock"
    "github.com/user/app/mocks"
)

func TestUserService_GetUser(t *testing.T) {
    ctrl := gomock.NewController(t)
    defer ctrl.Finish()

    // Create mock
    mockRepo := mocks.NewMockUserRepository(ctrl)

    // Set expectations
    mockRepo.EXPECT().
        FindByID(gomock.Any(), "user-123").
        Return(&User{ID: "user-123", Name: "Alice"}, nil)

    // Create service with mock
    svc := NewUserService(mockRepo, nil)

    // Test
    user, err := svc.GetUser(context.Background(), "user-123")
    if err != nil {
        t.Fatal(err)
    }
    if user.Name != "Alice" {
        t.Errorf("got name %q, want Alice", user.Name)
    }
}

func TestUserService_SendWelcomeEmail(t *testing.T) {
    ctrl := gomock.NewController(t)
    defer ctrl.Finish()

    mockRepo := mocks.NewMockUserRepository(ctrl)
    mockMailer := mocks.NewMockEmailSender(ctrl)

    // Expect repo lookup
    mockRepo.EXPECT().
        FindByID(gomock.Any(), "user-123").
        Return(&User{ID: "user-123", Email: "alice@example.com"}, nil)

    // Expect email to be sent with specific arguments
    mockMailer.EXPECT().
        Send(gomock.Any(), "alice@example.com", "Welcome!", gomock.Any()).
        Return(nil)

    svc := NewUserService(mockRepo, mockMailer)
    err := svc.SendWelcomeEmail(context.Background(), "user-123")
    if err != nil {
        t.Fatal(err)
    }
}
```

### Advanced Matchers

```go
func TestAdvancedMatchers(t *testing.T) {
    ctrl := gomock.NewController(t)
    defer ctrl.Finish()

    mockRepo := mocks.NewMockUserRepository(ctrl)

    // gomock.Any() matches any value
    mockRepo.EXPECT().
        FindByID(gomock.Any(), gomock.Any()).
        Return(&User{}, nil)

    // Custom matcher
    mockRepo.EXPECT().
        Save(gomock.Any(), gomock.Cond(func(u any) bool {
            user := u.(*User)
            return user.Email != "" && user.Name != ""
        })).
        Return(nil)

    // Times() for call count expectations
    mockRepo.EXPECT().
        FindByID(gomock.Any(), "user-456").
        Return(&User{}, nil).
        Times(3)

    // AnyTimes() for optional calls
    mockRepo.EXPECT().
        FindByID(gomock.Any(), "cached-user").
        Return(&User{}, nil).
        AnyTimes()
}
```

### Call Order Verification

```go
func TestCallOrder(t *testing.T) {
    ctrl := gomock.NewController(t)
    defer ctrl.Finish()

    mockRepo := mocks.NewMockUserRepository(ctrl)

    // InOrder ensures calls happen in sequence
    gomock.InOrder(
        mockRepo.EXPECT().FindByID(gomock.Any(), "1").Return(&User{}, nil),
        mockRepo.EXPECT().Save(gomock.Any(), gomock.Any()).Return(nil),
        mockRepo.EXPECT().FindByID(gomock.Any(), "1").Return(&User{}, nil),
    )

    // Test code that should make calls in this order
}
```

### go:generate for Mock Generation

```go
//go:generate mockgen -source=repository.go -destination=mocks/repository_mock.go -package=mocks

type UserRepository interface {
    FindByID(ctx context.Context, id string) (*User, error)
    Save(ctx context.Context, user *User) error
}
```

```bash
# Regenerate all mocks
go generate ./...
```

## Thread Safety Testing

### Race Detector

Projects **MUST** use the race detector when testing concurrent code. The race
detector **MUST** be run in CI for all projects with goroutines.

```bash
# Run tests with race detector
go test -race ./...

# Build binary with race detector
go build -race

# Run benchmarks with race detection
go test -race -bench=. ./...
```

### Testing Goroutines and Channels

```go
func TestConcurrentWrites(t *testing.T) {
    cache := NewCache()

    var wg sync.WaitGroup
    for i := 0; i < 100; i++ {
        wg.Add(1)
        go func(n int) {
            defer wg.Done()
            cache.Set(fmt.Sprintf("key%d", n), n)
        }(i)
    }

    wg.Wait()

    if cache.Len() != 100 {
        t.Errorf("got %d items, want 100", cache.Len())
    }
}

func TestChannelClose(t *testing.T) {
    ch := make(chan int)

    go func() {
        defer close(ch)
        for i := 0; i < 10; i++ {
            ch <- i
        }
    }()

    sum := 0
    for v := range ch {
        sum += v
    }

    if sum != 45 {
        t.Errorf("got sum %d, want 45", sum)
    }
}
```

### sync Package Testing Patterns

```go
func TestMutexProtection(t *testing.T) {
    var mu sync.Mutex
    counter := 0

    var wg sync.WaitGroup
    for i := 0; i < 1000; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            mu.Lock()
            counter++
            mu.Unlock()
        }()
    }

    wg.Wait()
    if counter != 1000 {
        t.Errorf("race condition: got %d, want 1000", counter)
    }
}

func TestOnce(t *testing.T) {
    var once sync.Once
    count := 0

    increment := func() { count++ }

    var wg sync.WaitGroup
    for i := 0; i < 100; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            once.Do(increment)
        }()
    }

    wg.Wait()
    if count != 1 {
        t.Errorf("Once failed: got %d executions, want 1", count)
    }
}
```

## Idempotence Testing

### Testing Retry-Safe Handlers

```go
func TestIdempotentCreate(t *testing.T) {
    handler := NewUserHandler()
    user := User{ID: "123", Email: "test@example.com"}

    // First request
    req1 := newCreateRequest(user, "request-id-1")
    w1 := httptest.NewRecorder()
    handler.ServeHTTP(w1, req1)

    if w1.Code != http.StatusCreated {
        t.Fatalf("first request failed: %d", w1.Code)
    }

    // Retry with same idempotency key
    req2 := newCreateRequest(user, "request-id-1")
    w2 := httptest.NewRecorder()
    handler.ServeHTTP(w2, req2)

    if w2.Code != http.StatusOK {
        t.Errorf("retry should return 200, got %d", w2.Code)
    }

    // Verify only one user created
    count := countUsers(t)
    if count != 1 {
        t.Errorf("expected 1 user, got %d", count)
    }
}
```

### Database Operation Idempotence

```go
func TestIdempotentUpdate(t *testing.T) {
    db := setupTestDB(t)
    repo := NewRepository(db)

    initial := &User{ID: 1, Version: 1, Name: "Alice"}
    repo.Create(initial)

    // Multiple identical updates
    update := &User{ID: 1, Version: 1, Name: "Bob"}

    for i := 0; i < 5; i++ {
        err := repo.Update(update)
        if err != nil {
            t.Fatalf("update %d failed: %v", i, err)
        }
    }

    // Verify final state
    result := repo.FindByID(1)
    if result.Name != "Bob" {
        t.Errorf("got name %q, want Bob", result.Name)
    }
    if result.Version != 2 {
        t.Errorf("got version %d, want 2", result.Version)
    }
}
```

## Reliability & Resilience Testing

### Chaos Testing Patterns

```go
func TestFailureRecovery(t *testing.T) {
    failureRate := 0.3
    service := &UnreliableService{
        FailureRate: failureRate,
        Random:      rand.New(rand.NewSource(42)),
    }

    client := NewRetryClient(service, 3)

    successes := 0
    attempts := 100

    for i := 0; i < attempts; i++ {
        err := client.Call(context.Background())
        if err == nil {
            successes++
        }
    }

    // With retries, success rate should be high
    successRate := float64(successes) / float64(attempts)
    if successRate < 0.95 {
        t.Errorf("success rate %.2f too low", successRate)
    }
}
```

### Testing with Context Cancellation

```go
func TestGracefulCancellation(t *testing.T) {
    ctx, cancel := context.WithCancel(context.Background())

    done := make(chan struct{})
    var processed int32

    go func() {
        defer close(done)
        worker(ctx, &processed)
    }()

    time.Sleep(100 * time.Millisecond)
    cancel()

    select {
    case <-done:
        // Worker stopped gracefully
    case <-time.After(time.Second):
        t.Fatal("worker did not stop after context cancellation")
    }

    if atomic.LoadInt32(&processed) == 0 {
        t.Error("worker should have processed some items")
    }
}

func TestTimeout(t *testing.T) {
    ctx, cancel := context.WithTimeout(context.Background(), 50*time.Millisecond)
    defer cancel()

    err := slowOperation(ctx)
    if err != context.DeadlineExceeded {
        t.Errorf("got error %v, want DeadlineExceeded", err)
    }
}
```

### Circuit Breaker Testing

```go
import "github.com/sony/gobreaker"[^15]

func TestCircuitBreaker(t *testing.T) {
    cb := gobreaker.NewCircuitBreaker(gobreaker.Settings{
        MaxRequests: 3,
        Interval:    time.Second,
        Timeout:     time.Second,
    })

    failingService := func() (interface{}, error) {
        return nil, errors.New("service unavailable")
    }

    // Trigger circuit breaker to open
    for i := 0; i < 5; i++ {
        cb.Execute(failingService)
    }

    // Circuit should be open now
    _, err := cb.Execute(failingService)
    if err != gobreaker.ErrOpenState {
        t.Errorf("got error %v, want ErrOpenState", err)
    }
}
```

## Compatibility Testing

### Multi-Version Testing with CI Matrix

```yaml
# .github/workflows/test.yml
jobs:
  test:
    strategy:
      matrix:
        go-version: ['1.22', '1.23', '1.24']
        os: [ubuntu-latest, macos-latest, windows-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: ${{ matrix.go-version }}
      - run: go test ./...
```

### GOOS/GOARCH Cross-Compilation Testing

```bash
# Test builds for different platforms
GOOS=linux GOARCH=amd64 go build -o build/app-linux-amd64
GOOS=darwin GOARCH=arm64 go build -o build/app-darwin-arm64
GOOS=windows GOARCH=amd64 go build -o build/app-windows-amd64.exe

# Test all supported platforms
for GOOS in darwin linux windows; do
  for GOARCH in amd64 arm64; do
    echo "Building $GOOS/$GOARCH"
    GOOS=$GOOS GOARCH=$GOARCH go build -o /dev/null
  done
done
```

```go
// Platform-specific tests
//go:build linux
// +build linux

func TestLinuxSpecific(t *testing.T) {
    // Linux-only test
}
```

```go
//go:build windows
// +build windows

func TestWindowsSpecific(t *testing.T) {
    // Windows-only test
}
```

## cgo: C Interoperability

Projects **MAY** use cgo[^17] to call C code from Go when necessary, but
**SHOULD** prefer pure Go alternatives when available.

### Why cgo?

- **Legacy integration**: Interface with existing C libraries and system APIs
- **Performance**: Call highly optimized C code for compute-intensive operations
- **System access**: Access platform-specific functionality not exposed in Go

### When to Avoid cgo

- **Cross-compilation**: cgo requires a C compiler for the target platform
- **Complexity**: Debugging across Go/C boundary is harder
- **Performance cost**: Each cgo call has ~150ns overhead vs pure Go calls
- **CGO_ENABLED=0**: Many deployments (scratch containers) disable cgo

### Basic cgo Usage

```go
package main

/*
#include <stdlib.h>
#include <string.h>

// C function definition
int add(int a, int b) {
    return a + b;
}

// Using system headers
#include <math.h>
*/
import "C"
import (
    "fmt"
    "unsafe"
)

func main() {
    // Call C function
    result := C.add(40, 2)
    fmt.Println("40 + 2 =", result)

    // Call standard library
    sqrt := C.sqrt(16.0)
    fmt.Println("sqrt(16) =", sqrt)
}
```

### Memory Management

```go
/*
#include <stdlib.h>
#include <string.h>
*/
import "C"
import "unsafe"

// String conversion - MUST free C strings
func goStringToC(s string) *C.char {
    return C.CString(s)  // Caller must free!
}

func cStringToGo(cs *C.char) string {
    return C.GoString(cs)
}

func processString(input string) string {
    // Convert Go string to C string
    cInput := C.CString(input)
    defer C.free(unsafe.Pointer(cInput))  // MUST free

    // Call C function that returns new string
    cOutput := C.some_c_function(cInput)
    defer C.free(unsafe.Pointer(cOutput))

    // Convert back to Go string
    return C.GoString(cOutput)
}

// Passing slices to C
func processBytes(data []byte) {
    if len(data) == 0 {
        return
    }
    // Get pointer to first element
    cData := (*C.char)(unsafe.Pointer(&data[0]))
    cLen := C.int(len(data))

    C.process_buffer(cData, cLen)
}
```

### Linking External Libraries

```go
/*
#cgo CFLAGS: -I/usr/local/include
#cgo LDFLAGS: -L/usr/local/lib -lmylibrary

#include <mylibrary.h>
*/
import "C"

// Platform-specific flags
/*
#cgo linux LDFLAGS: -lm -lpthread
#cgo darwin LDFLAGS: -framework CoreFoundation
#cgo windows LDFLAGS: -lws2_32
*/
import "C"

// pkg-config integration
/*
#cgo pkg-config: libpng openssl
#include <png.h>
#include <openssl/ssl.h>
*/
import "C"
```

### Error Handling

```go
/*
#include <errno.h>
#include <stdlib.h>

int divide(int a, int b, int* result) {
    if (b == 0) {
        errno = EINVAL;
        return -1;
    }
    *result = a / b;
    return 0;
}
*/
import "C"
import (
    "errors"
    "fmt"
)

func Divide(a, b int) (int, error) {
    var result C.int
    _, err := C.divide(C.int(a), C.int(b), &result)
    if err != nil {
        return 0, fmt.Errorf("divide: %w", err)
    }
    return int(result), nil
}
```

### cgo Best Practices

```go
// GOOD: Minimize cgo calls by batching work
func ProcessBatch(items []Item) {
    cItems := convertToCArray(items)
    defer freeCArray(cItems)
    C.process_batch(cItems, C.int(len(items)))  // One cgo call
}

// BAD: Many small cgo calls
func ProcessBatchSlow(items []Item) {
    for _, item := range items {
        C.process_single(convertToC(item))  // N cgo calls
    }
}

// GOOD: Keep cgo isolated to specific packages
// internal/clib/wrapper.go
package clib

/*
#include <mylib.h>
*/
import "C"

func DoThing() { C.do_thing() }

// GOOD: Provide pure Go fallback with build tags
//go:build !cgo

package mylib

func DoThing() {
    // Pure Go implementation
}
```

### Build and Test with cgo

```bash
# Enable cgo (default on most platforms)
CGO_ENABLED=1 go build

# Disable cgo for static binary
CGO_ENABLED=0 go build

# Cross-compile with cgo requires C cross-compiler
CC=x86_64-linux-musl-gcc CGO_ENABLED=1 GOOS=linux go build

# Test with race detector (requires cgo on some platforms)
CGO_ENABLED=1 go test -race ./...
```

## Internationalization Testing

### UTF-8 String Handling (Runes)

```go
func TestUnicodeHandling(t *testing.T) {
    tests := []struct {
        input string
        want  int
    }{
        {"hello", 5},
        {"世界", 2},        // Chinese characters
        {"🚀🌟", 2},        // Emoji
        {"café", 4},       // Accented characters
    }

    for _, tt := range tests {
        got := len([]rune(tt.input))
        if got != tt.want {
            t.Errorf("len(%q) = %d, want %d", tt.input, got, tt.want)
        }
    }
}

func TestRuneIteration(t *testing.T) {
    s := "Go语言"

    // Wrong: iterates over bytes
    byteCount := 0
    for i := 0; i < len(s); i++ {
        byteCount++
    }

    // Correct: iterates over runes
    runeCount := 0
    for range s {
        runeCount++
    }

    if runeCount != 4 {
        t.Errorf("got %d runes, want 4", runeCount)
    }
}
```

### golang.org/x/text for i18n

```go
import (
    "golang.org/x/text/language"[^13]
    "golang.org/x/text/message"[^13]
)

func TestMessageFormatting(t *testing.T) {
    p := message.NewPrinter(language.English)
    msg := p.Sprintf("You have %d new messages", 42)

    want := "You have 42 new messages"
    if msg != want {
        t.Errorf("got %q, want %q", msg, want)
    }
}

func TestPluralization(t *testing.T) {
    tests := []struct {
        lang  language.Tag
        count int
        want  string
    }{
        {language.English, 1, "1 item"},
        {language.English, 5, "5 items"},
    }

    for _, tt := range tests {
        p := message.NewPrinter(tt.lang)
        got := p.Sprintf("%d item(s)", tt.count)
        if got != tt.want {
            t.Errorf("%v: got %q, want %q", tt.lang, got, tt.want)
        }
    }
}
```

### Unicode Normalization Tests

```go
import "golang.org/x/text/unicode/norm"[^13]

func TestNormalization(t *testing.T) {
    // "é" can be represented two ways
    composed := "\u00e9"     // Single codepoint
    decomposed := "e\u0301" // e + combining accent

    if composed == decomposed {
        t.Error("strings should not be equal before normalization")
    }

    // Normalize to NFC (composed form)
    nfc1 := norm.NFC.String(composed)
    nfc2 := norm.NFC.String(decomposed)

    if nfc1 != nfc2 {
        t.Error("normalized strings should be equal")
    }
}
```

## Data Integrity Testing

### Database Transaction Testing

```go
func TestTransactionRollback(t *testing.T) {
    db := setupTestDB(t)

    tx, err := db.Begin()
    if err != nil {
        t.Fatal(err)
    }

    // Create user in transaction
    _, err = tx.Exec("INSERT INTO users (name) VALUES (?)", "Alice")
    if err != nil {
        t.Fatal(err)
    }

    // Rollback
    tx.Rollback()

    // Verify user was not created
    var count int
    db.QueryRow("SELECT COUNT(*) FROM users WHERE name = ?", "Alice").Scan(&count)
    if count != 0 {
        t.Error("user should not exist after rollback")
    }
}

func TestTransactionCommit(t *testing.T) {
    db := setupTestDB(t)

    err := withTransaction(db, func(tx *sql.Tx) error {
        _, err := tx.Exec("INSERT INTO users (name) VALUES (?)", "Bob")
        if err != nil {
            return err
        }

        _, err = tx.Exec("INSERT INTO posts (user_id, title) VALUES (?, ?)", 1, "Hello")
        return err
    })

    if err != nil {
        t.Fatal(err)
    }

    // Verify both inserts succeeded
    var userCount, postCount int
    db.QueryRow("SELECT COUNT(*) FROM users").Scan(&userCount)
    db.QueryRow("SELECT COUNT(*) FROM posts").Scan(&postCount)

    if userCount != 1 || postCount != 1 {
        t.Error("transaction did not commit both operations")
    }
}
```

### Migration Testing

```go
import "github.com/golang-migrate/migrate/v4"[^14]

func TestMigrations(t *testing.T) {
    db := setupTestDB(t)

    m, err := migrate.New(
        "file://migrations",
        "postgres://localhost/testdb",
    )
    if err != nil {
        t.Fatal(err)
    }

    // Migrate up
    if err := m.Up(); err != nil && err != migrate.ErrNoChange {
        t.Fatal(err)
    }

    // Verify schema
    var tableCount int
    db.QueryRow("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'").Scan(&tableCount)
    if tableCount == 0 {
        t.Error("no tables created")
    }

    // Test rollback
    if err := m.Down(); err != nil {
        t.Fatal(err)
    }
}

func TestMigrationIdempotence(t *testing.T) {
    db := setupTestDB(t)
    m := setupMigrate(t)

    // Run migrations twice
    m.Up()
    version1, _, _ := m.Version()

    m.Up()
    version2, _, _ := m.Version()

    if version1 != version2 {
        t.Error("migrations should be idempotent")
    }
}
```

## A/B Testing & Feature Flags

### Feature Flag Patterns

```go
type FeatureFlags struct {
    mu    sync.RWMutex
    flags map[string]bool
}

func (f *FeatureFlags) IsEnabled(flag string, userID string) bool {
    f.mu.RLock()
    defer f.mu.RUnlock()
    return f.flags[flag]
}

func TestFeatureFlag(t *testing.T) {
    flags := &FeatureFlags{
        flags: map[string]bool{
            "new_checkout": true,
            "beta_ui":      false,
        },
    }

    if !flags.IsEnabled("new_checkout", "user123") {
        t.Error("new_checkout should be enabled")
    }

    if flags.IsEnabled("beta_ui", "user123") {
        t.Error("beta_ui should be disabled")
    }
}

// Percentage-based rollout
func TestGradualRollout(t *testing.T) {
    rollout := NewPercentageRollout("feature_x", 20) // 20% of users

    enabled := 0
    total := 1000

    for i := 0; i < total; i++ {
        userID := fmt.Sprintf("user%d", i)
        if rollout.IsEnabled(userID) {
            enabled++
        }
    }

    percentage := float64(enabled) / float64(total) * 100
    if percentage < 15 || percentage > 25 {
        t.Errorf("got %.1f%% enabled, want ~20%%", percentage)
    }
}
```

### Testing with Build Tags

```go
//go:build feature_x
// +build feature_x

func NewHandler() http.Handler {
    return &NewHandlerV2{} // Feature flag enabled
}
```

```go
//go:build !feature_x
// +build !feature_x

func NewHandler() http.Handler {
    return &OldHandler{} // Feature flag disabled
}
```

```bash
# Build with feature enabled
go build -tags=feature_x

# Test with feature enabled
go test -tags=feature_x ./...

# Test both configurations in CI
go test ./...
go test -tags=feature_x ./...
```

```go
func TestFeatureBehavior(t *testing.T) {
    handler := NewHandler()

    req := httptest.NewRequest("GET", "/", nil)
    w := httptest.NewRecorder()

    handler.ServeHTTP(w, req)

    // Behavior differs based on build tag
    // Assert based on expected variant
}
```

## References

[^1]: [golangci-lint](https://golangci-lint.run/) - Fast Go linters aggregator with parallel execution and shared caching
[^2]: [gofmt](https://pkg.go.dev/cmd/gofmt) - Official Go code formatter, part of the Go toolchain
[^3]: [goimports](https://pkg.go.dev/golang.org/x/tools/cmd/goimports) - Go formatter that also manages imports automatically
[^4]: [Staticcheck](https://staticcheck.io/) - Advanced Go static analysis tool for finding bugs and improving code quality
[^5]: [deadcode](https://pkg.go.dev/golang.org/x/tools/cmd/deadcode) - Tool to detect unused functions and methods in Go code
[^6]: [go test](https://pkg.go.dev/cmd/go#hdr-Test_packages) - Built-in Go testing command with coverage, benchmarking, and fuzzing support
[^7]: [gocyclo](https://github.com/fzipp/gocyclo) - Cyclomatic complexity analyzer for Go code
[^8]: [govulncheck](https://pkg.go.dev/golang.org/x/vuln/cmd/govulncheck) - Go vulnerability scanner from the Go security team
[^9]: [Dependabot](https://docs.github.com/en/code-security/dependabot) - GitHub's automated dependency update tool
[^10]: [httptest](https://pkg.go.dev/net/http/httptest) - Built-in Go package for testing HTTP handlers
[^11]: [chromedp](https://github.com/chromedp/chromedp) - Chrome DevTools Protocol driver for browser automation in Go
[^12]: [godog](https://github.com/cucumber/godog) - Cucumber/BDD framework for Go with Gherkin support
[^13]: [golang.org/x/text](https://pkg.go.dev/golang.org/x/text) - Go supplementary text processing packages for internationalization
[^14]: [golang-migrate](https://github.com/golang-migrate/migrate) - Database migration tool with support for multiple databases
[^15]: [gobreaker](https://github.com/sony/gobreaker) - Circuit breaker implementation for Go
[^16]: [gomock](https://github.com/uber-go/mock) - Mock framework for Go interfaces (uber-go fork of official golang/mock)
[^17]: [cgo](https://pkg.go.dev/cmd/cgo) - Go tool for calling C code from Go programs

## See Also

- [Testing Guide](../testing.md) - General testing principles and practices
- [CI Guide](../ci.md) - Continuous Integration setup and best practices
