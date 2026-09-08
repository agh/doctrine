# Go Style Guide

> [Doctrine](../../README.md) > [Languages](README.md) > Go

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

Extends [Google Go Style Guide](../../reference/google/go.md). See also
[Google Go Decisions](../../reference/google/go-decisions.md) and
[Google Go Best Practices](../../reference/google/go-best-practices.md).

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

Active fuzzing **MUST** name exactly one package and one fuzz target. `go test`
rejects `-fuzz` with a multi-package pattern such as `./...`, failing with
`cannot use -fuzz flag with multiple packages`.

```bash
# Fuzz the target in the current package
go test -fuzz=FuzzReverse -fuzztime=30s .

# Fuzz a target in another package: name that package, never ./...
go test -fuzz=FuzzReverse -fuzztime=1m ./internal/strutil

# Replay the seed and failure corpus in every package without fuzzing
go test ./...
```

### Why One Package at a Time

- **Tool constraint**: `-fuzz` mutates inputs for a single target, so the
  toolchain refuses ambiguous package patterns
- **Corpus locality**: seed inputs live in `testdata/fuzz/<FuzzTarget>/` beside
  the test; failing inputs are written back there for replay
- **Regression replay**: a plain `go test ./...` still runs every stored corpus
  entry as an ordinary test case across all packages

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

chromedp[^11] drives a real Chrome instance over the DevTools Protocol.

```go
import "github.com/chromedp/chromedp"

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

godog[^12] executes Gherkin feature files against Go step definitions.

```go
// features/login.feature
// Feature: User Login
//   Scenario: Valid credentials
//     Given I am on the login page
//     When I enter valid credentials
//     Then I should see the dashboard

import "github.com/cucumber/godog"

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

func (s *UserService) GetUser(ctx context.Context, id string) (*User, error) {
    return s.repo.FindByID(ctx, id)
}

func (s *UserService) SaveUser(ctx context.Context, user *User) error {
    return s.repo.Save(ctx, user)
}

// Rename loads the user, persists the new name, then reloads it so that
// callers observe the stored record rather than the in-memory copy.
func (s *UserService) Rename(ctx context.Context, id, name string) (*User, error) {
    user, err := s.repo.FindByID(ctx, id)
    if err != nil {
        return nil, err
    }

    user.Name = name
    if err := s.repo.Save(ctx, user); err != nil {
        return nil, err
    }

    return s.repo.FindByID(ctx, id)
}

func (s *UserService) SendWelcomeEmail(ctx context.Context, id string) error {
    user, err := s.repo.FindByID(ctx, id)
    if err != nil {
        return err
    }

    return s.mailer.Send(ctx, user.Email, "Welcome!", "Welcome aboard, "+user.Name)
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

Every expectation registered without `AnyTimes()` is required, so each test
**MUST** call the system under test until the declared counts are satisfied.
Independent matcher demonstrations **MUST** live in separate subtests with
their own controller: a broad matcher such as `gomock.Any()` otherwise
consumes a call intended for a narrower expectation. `gomock.NewController(t)`
registers the final verification through `t.Cleanup`, so `ctrl.Finish()` is
not called explicitly.

```go
func TestAdvancedMatchers(t *testing.T) {
    ctx := context.Background()

    t.Run("any argument", func(t *testing.T) {
        ctrl := gomock.NewController(t)
        mockRepo := mocks.NewMockUserRepository(ctrl)

        // gomock.Any() matches any value
        mockRepo.EXPECT().
            FindByID(gomock.Any(), gomock.Any()).
            Return(&User{ID: "user-123"}, nil)

        svc := NewUserService(mockRepo, nil)
        if _, err := svc.GetUser(ctx, "user-123"); err != nil {
            t.Fatalf("GetUser: %v", err)
        }
    })

    t.Run("custom matcher", func(t *testing.T) {
        ctrl := gomock.NewController(t)
        mockRepo := mocks.NewMockUserRepository(ctrl)

        // gomock.Cond is generic: the function only receives values of the
        // declared type, so no unchecked type assertion is needed.
        mockRepo.EXPECT().
            Save(gomock.Any(), gomock.Cond(func(u *User) bool {
                return u.Email != "" && u.Name != ""
            })).
            Return(nil)

        svc := NewUserService(mockRepo, nil)
        user := &User{ID: "user-123", Name: "Alice", Email: "alice@example.com"}
        if err := svc.SaveUser(ctx, user); err != nil {
            t.Fatalf("SaveUser: %v", err)
        }
    })

    t.Run("exact call count", func(t *testing.T) {
        ctrl := gomock.NewController(t)
        mockRepo := mocks.NewMockUserRepository(ctrl)

        // Times() for call count expectations
        mockRepo.EXPECT().
            FindByID(gomock.Any(), "user-456").
            Return(&User{ID: "user-456"}, nil).
            Times(3)

        svc := NewUserService(mockRepo, nil)
        for i := 0; i < 3; i++ {
            if _, err := svc.GetUser(ctx, "user-456"); err != nil {
                t.Fatalf("GetUser call %d: %v", i, err)
            }
        }
    })

    t.Run("optional calls", func(t *testing.T) {
        ctrl := gomock.NewController(t)
        mockRepo := mocks.NewMockUserRepository(ctrl)

        // AnyTimes() for optional calls: zero calls also satisfy it
        mockRepo.EXPECT().
            FindByID(gomock.Any(), "cached-user").
            Return(&User{ID: "cached-user"}, nil).
            AnyTimes()

        svc := NewUserService(mockRepo, nil)
        for i := 0; i < 2; i++ {
            if _, err := svc.GetUser(ctx, "cached-user"); err != nil {
                t.Fatalf("GetUser call %d: %v", i, err)
            }
        }
    })
}
```

### Call Order Verification

```go
func TestCallOrder(t *testing.T) {
    ctrl := gomock.NewController(t)
    mockRepo := mocks.NewMockUserRepository(ctrl)

    // InOrder ensures calls happen in sequence
    gomock.InOrder(
        mockRepo.EXPECT().FindByID(gomock.Any(), "1").Return(&User{ID: "1"}, nil),
        mockRepo.EXPECT().Save(gomock.Any(), gomock.Any()).Return(nil),
        mockRepo.EXPECT().
            FindByID(gomock.Any(), "1").
            Return(&User{ID: "1", Name: "Alice"}, nil),
    )

    // Rename issues FindByID, Save, then FindByID, satisfying the sequence.
    svc := NewUserService(mockRepo, nil)
    user, err := svc.Rename(context.Background(), "1", "Alice")
    if err != nil {
        t.Fatalf("Rename: %v", err)
    }
    if user.Name != "Alice" {
        t.Errorf("got name %q, want Alice", user.Name)
    }
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

gobreaker[^15] v2 (`github.com/sony/gobreaker/v2` v2.4.0) is generic over the
request result. Tests **MUST** configure `ReadyToTrip` for the threshold they
assert: `MaxRequests` bounds half-open admission, not closed-state failures,
and the default `ReadyToTrip` needs more than five consecutive failures. Calls
up to the threshold return the service error; only the call after the breaker
opens returns `ErrOpenState`.

```go
import (
    "errors"
    "testing"
    "time"

    "github.com/sony/gobreaker/v2"
)

var errUnavailable = errors.New("service unavailable")

func TestCircuitBreaker(t *testing.T) {
    const threshold = 3

    cb := gobreaker.NewCircuitBreaker[string](gobreaker.Settings{
        Name:        "downstream",
        MaxRequests: 1,
        Interval:    time.Second,
        Timeout:     time.Second,
        ReadyToTrip: func(counts gobreaker.Counts) bool {
            return counts.ConsecutiveFailures >= threshold
        },
    })

    failingService := func() (string, error) {
        return "", errUnavailable
    }

    // The breaker stays closed until ReadyToTrip fires, so every call up to
    // the threshold returns the service error, not ErrOpenState.
    for i := 1; i <= threshold; i++ {
        if _, err := cb.Execute(failingService); !errors.Is(err, errUnavailable) {
            t.Fatalf("call %d: got error %v, want %v", i, err, errUnavailable)
        }
    }

    if state := cb.State(); state != gobreaker.StateOpen {
        t.Fatalf("got state %v, want %v", state, gobreaker.StateOpen)
    }

    // Only the call after the breaker opened is rejected without dialling out.
    if _, err := cb.Execute(failingService); !errors.Is(err, gobreaker.ErrOpenState) {
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
#cgo linux LDFLAGS: -lm

#include <math.h>
#include <stdlib.h>

// C function definition
static int add(int a, int b) {
    return a + b;
}
*/
import "C"
import "fmt"

func main() {
    // Call C function
    result := C.add(40, 2)
    fmt.Println("40 + 2 =", result)

    // Call standard library
    sqrt := C.sqrt(16.0)
    fmt.Println("sqrt(16) =", sqrt)
}
```

Preamble helpers **MUST** be declared `static`. cgo compiles the preamble once
per Go file, so a package with two cgo files that both define `int add(...)`
fails to link with `duplicate symbol '_add'`; `static` gives the helper
internal linkage. Platform linker flags **MUST** be declared with `#cgo`:
glibc needs `-lm` for `math.h` symbols, whereas macOS resolves them from
libSystem.

### Memory Management

Every C symbol a fence calls **MUST** be declared in that fence's preamble;
`C.some_c_function` and `C.process_buffer` below stand in for a real library.

```go
package clib

/*
#include <ctype.h>
#include <stdlib.h>
#include <string.h>

// Returns a newly allocated upper-cased copy that the caller owns.
static char *some_c_function(const char *in) {
    size_t n = strlen(in);
    char *out = malloc(n + 1);
    if (out == NULL) {
        return NULL;
    }
    for (size_t i = 0; i < n; i++) {
        out[i] = (char)toupper((unsigned char)in[i]);
    }
    out[n] = '\0';
    return out;
}

// Transforms a caller-owned buffer in place.
static void process_buffer(char *data, int len) {
    for (int i = 0; i < len; i++) {
        data[i] = (char)toupper((unsigned char)data[i]);
    }
}
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
    if cOutput == nil {
        return ""
    }
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

Each snippet below is a complete file that compiles only where the named
library and headers are installed. A Go file **MUST** contain exactly one
preamble, and that comment block **MUST** sit immediately above its own
`import "C"`: cgo treats every comment line adjacent to `import "C"` as C
source, so descriptive `//` labels belong in prose, not directly above the
preamble.

Absolute include and library search paths:

```go
package clib

/*
#cgo CFLAGS: -I/usr/local/include
#cgo LDFLAGS: -L/usr/local/lib -lmylibrary

#include <mylibrary.h>
*/
import "C"
```

Platform-specific flags, applied per `GOOS`:

```go
package clib

/*
#cgo linux LDFLAGS: -lm -lpthread
#cgo darwin LDFLAGS: -framework CoreFoundation
#cgo windows LDFLAGS: -lws2_32
*/
import "C"
```

`pkg-config` resolving flags at build time:

```go
package clib

/*
#cgo pkg-config: libpng openssl
#include <png.h>
#include <openssl/ssl.h>
*/
import "C"
```

### Error Handling

A cgo call's second result carries `errno`, which is only meaningful once the
C status has reported failure. Code **MUST** test the status first, then the
`errno` value.

```go
package cerr

/*
#include <errno.h>
#include <stdlib.h>

static int divide(int a, int b, int *result) {
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

    status, errno := C.divide(C.int(a), C.int(b), &result)
    if status != 0 {
        if errno != nil {
            return 0, fmt.Errorf("divide: %w", errno)  // wraps syscall.EINVAL
        }
        return 0, errors.New("divide: failed without setting errno")
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

golang.org/x/text[^13] (v0.41.0) supplies locale-aware formatting.
`message.Printer` localises number formatting and looks translations up in a
catalogue; it does **not** infer plural forms from a source string such as
`"%d item(s)"`. Plural selection **MUST** be registered explicitly with
`plural.Selectf`, otherwise the printer falls back to the untranslated format
string and returns `"1 item(s)"` for every count.

```go
import (
    "golang.org/x/text/feature/plural"
    "golang.org/x/text/language"
    "golang.org/x/text/message"
)

func TestMessageFormatting(t *testing.T) {
    p := message.NewPrinter(language.English)
    msg := p.Sprintf("You have %d new messages", 42)

    want := "You have 42 new messages"
    if msg != want {
        t.Errorf("got %q, want %q", msg, want)
    }
}

// registerMessages installs plural-aware translations for the "%d item(s)"
// key. The printer then selects the CLDR plural form for its locale.
func registerMessages() error {
    err := message.Set(language.English, "%d item(s)",
        plural.Selectf(1, "%d",
            plural.One, "%d item",
            plural.Other, "%d items",
        ))
    if err != nil {
        return err
    }

    return message.Set(language.French, "%d item(s)",
        plural.Selectf(1, "%d",
            plural.One, "%d article",
            plural.Other, "%d articles",
        ))
}

func TestPluralization(t *testing.T) {
    if err := registerMessages(); err != nil {
        t.Fatalf("register messages: %v", err)
    }

    tests := []struct {
        lang  language.Tag
        count int
        want  string
    }{
        {language.English, 0, "0 items"},
        {language.English, 1, "1 item"},
        {language.English, 5, "5 items"},
        // French uses the "one" form for both 0 and 1.
        {language.French, 0, "0 article"},
        {language.French, 1, "1 article"},
        {language.French, 5, "5 articles"},
    }

    for _, tt := range tests {
        p := message.NewPrinter(tt.lang)
        got := p.Sprintf("%d item(s)", tt.count)
        if got != tt.want {
            t.Errorf("%v/%d: got %q, want %q", tt.lang, tt.count, got, tt.want)
        }
    }
}
```

### Unicode Normalization Tests

`golang.org/x/text/unicode/norm`[^13] converts between the composed and
decomposed forms.

```go
import "golang.org/x/text/unicode/norm"

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

golang-migrate[^14] (v4.19.1) resolves `file://` and `postgres://` URLs through
a driver registry. Source and database drivers **MUST** therefore be imported
for their side effects, or `migrate.New` fails with
`unknown driver 'file' (forgotten import?)`. The database driver is imported by
name below because `TestMigrationIdempotence` calls `postgres.WithInstance`;
a package that only uses URL construction **MUST** import it blank
(`_ "github.com/golang-migrate/migrate/v4/database/postgres"`).

Migration tests **MUST** run against a database of their own, since `Up` and
`Down` rewrite the whole schema, and **MUST** check every `Up`, `Down`,
`Version` and `Close` result. Only the first `Up` may legitimately return
`migrate.ErrNoChange`. The `database/sql` driver lib/pq[^18] (v1.12.3) is
imported explicitly rather than relied on transitively through
`database/postgres`.

```go
import (
    "database/sql"
    "errors"
    "fmt"
    "net/url"
    "os"
    "testing"
    "time"

    "github.com/golang-migrate/migrate/v4"
    "github.com/golang-migrate/migrate/v4/database/postgres"
    _ "github.com/golang-migrate/migrate/v4/source/file"
    _ "github.com/lib/pq"
)

// newTestDB creates a throwaway database for a single test and drops it
// afterwards, so migrations never run against a shared schema.
func newTestDB(t *testing.T) (*sql.DB, string) {
    t.Helper()

    adminURL := os.Getenv("TEST_DATABASE_URL")
    if adminURL == "" {
        t.Skip("TEST_DATABASE_URL is not set")
    }

    admin, err := sql.Open("postgres", adminURL)
    if err != nil {
        t.Fatalf("open admin connection: %v", err)
    }
    t.Cleanup(func() { _ = admin.Close() })

    // The name is generated here rather than taken from input; PostgreSQL
    // does not accept placeholders in CREATE DATABASE.
    name := fmt.Sprintf("migrate_test_%d", time.Now().UnixNano())
    if _, err := admin.Exec(`CREATE DATABASE "` + name + `"`); err != nil {
        t.Fatalf("create database %s: %v", name, err)
    }

    dsn, err := url.Parse(adminURL)
    if err != nil {
        t.Fatalf("parse TEST_DATABASE_URL: %v", err)
    }
    dsn.Path = "/" + name

    db, err := sql.Open("postgres", dsn.String())
    if err != nil {
        t.Fatalf("open %s: %v", name, err)
    }
    t.Cleanup(func() {
        _ = db.Close()
        if _, err := admin.Exec(`DROP DATABASE "` + name + `"`); err != nil {
            t.Errorf("drop database %s: %v", name, err)
        }
    })

    return db, dsn.String()
}

func TestMigrations(t *testing.T) {
    db, dsn := newTestDB(t)

    m, err := migrate.New("file://migrations", dsn)
    if err != nil {
        t.Fatalf("new migrator: %v", err)
    }
    t.Cleanup(func() {
        if srcErr, dbErr := m.Close(); srcErr != nil || dbErr != nil {
            t.Errorf("close migrator: source=%v database=%v", srcErr, dbErr)
        }
    })

    // Migrate up
    if err := m.Up(); err != nil && !errors.Is(err, migrate.ErrNoChange) {
        t.Fatalf("migrate up: %v", err)
    }

    // Verify schema
    var tableCount int
    err = db.QueryRow(
        `SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'`,
    ).Scan(&tableCount)
    if err != nil {
        t.Fatalf("count tables: %v", err)
    }
    if tableCount == 0 {
        t.Error("no tables created")
    }

    // Test rollback
    if err := m.Down(); err != nil && !errors.Is(err, migrate.ErrNoChange) {
        t.Fatalf("migrate down: %v", err)
    }
}

func TestMigrationIdempotence(t *testing.T) {
    db, _ := newTestDB(t)

    // NewWithDatabaseInstance reuses the test's *sql.DB instead of opening a
    // second connection pool from a URL.
    driver, err := postgres.WithInstance(db, &postgres.Config{})
    if err != nil {
        t.Fatalf("postgres driver: %v", err)
    }

    m, err := migrate.NewWithDatabaseInstance("file://migrations", "postgres", driver)
    if err != nil {
        t.Fatalf("new migrator: %v", err)
    }
    t.Cleanup(func() {
        if srcErr, dbErr := m.Close(); srcErr != nil || dbErr != nil {
            t.Errorf("close migrator: source=%v database=%v", srcErr, dbErr)
        }
    })

    if err := m.Up(); err != nil && !errors.Is(err, migrate.ErrNoChange) {
        t.Fatalf("first up: %v", err)
    }
    version1, dirty, err := m.Version()
    if err != nil {
        t.Fatalf("first version: %v", err)
    }
    if dirty {
        t.Fatal("schema is dirty after the first migration")
    }

    // A second run must report ErrNoChange rather than advancing the version.
    if err := m.Up(); !errors.Is(err, migrate.ErrNoChange) {
        t.Fatalf("second up: got %v, want ErrNoChange", err)
    }
    version2, dirty, err := m.Version()
    if err != nil {
        t.Fatalf("second version: %v", err)
    }
    if dirty {
        t.Fatal("schema is dirty after the second migration")
    }

    if version1 != version2 {
        t.Errorf("version moved from %d to %d; migrations must be idempotent",
            version1, version2)
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
[^15]: [gobreaker](https://github.com/sony/gobreaker) - Circuit breaker implementation for Go; current major is `github.com/sony/gobreaker/v2`
[^16]: [gomock](https://github.com/uber-go/mock) - Mock framework for Go interfaces (uber-go fork of official golang/mock)
[^17]: [cgo](https://pkg.go.dev/cmd/cgo) - Go tool for calling C code from Go programs
[^18]: [lib/pq](https://github.com/lib/pq) - Pure Go PostgreSQL driver for database/sql

## See Also

- [Testing Guide](../process/testing.md) - General testing principles and practices
- [CI Guide](../process/ci.md) - Continuous Integration setup and best practices
