# Gin Style Guide

> [Doctrine](../../README.md) > [Frameworks](../README.md) > Gin

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119][rfc2119].

[rfc2119]: https://datatracker.ietf.org/doc/html/rfc2119

Extends [Go style guide](../languages/go.md) with Gin-specific conventions.

**Target Version**: Gin 1.11+ with Go 1.23

## Quick Reference

All Go tooling applies. Additional considerations:

| Task | Tool | Command |
| ---- | ---- | ------- |
| Install | go get | `go get -u github.com/gin-gonic/gin` |
| Run dev | go run | `go run main.go` |
| Test | go test + httptest | `go test -v ./...` |
| Build | go build | `go build -o bin/app` |

## Why Gin?

Gin[^1] is a high-performance HTTP web framework written in Go that provides:

- **High performance**: Up to 40x faster than Martini due to httprouter[^2] under the hood
- **Middleware ecosystem**: Rich selection of built-in and community middleware
- **Request validation**: Built-in binding and validation using struct tags
- **Error handling**: Centralized error management with custom error handlers
- **JSON rendering**: Fast JSON serialization with minimal allocations
- **Lightweight**: Minimal dependencies and small binary size

Use Gin for building RESTful APIs, microservices, and web applications requiring high throughput.
Choose Echo[^3] for similar performance with different API design, or Fiber[^4] for
Express.js-like syntax. Use the standard library net/http for maximum control and zero
dependencies.

## Project Structure

Projects **SHOULD** organize Gin applications using a layered architecture:

```text
my_app/
├── cmd/
│   └── server/
│       └── main.go           # Application entry point
├── internal/
│   ├── api/
│   │   ├── handler/          # HTTP handlers
│   │   │   ├── user.go
│   │   │   └── health.go
│   │   ├── middleware/       # Custom middleware
│   │   │   ├── auth.go
│   │   │   └── logging.go
│   │   └── router/           # Route definitions
│   │       └── router.go
│   ├── model/                # Domain models
│   │   └── user.go
│   ├── repository/           # Data access layer
│   │   └── user.go
│   ├── service/              # Business logic
│   │   └── user.go
│   └── config/               # Configuration
│       └── config.go
├── pkg/                      # Public libraries
│   └── validator/
├── migrations/               # Database migrations
├── go.mod
├── go.sum
└── .env
```

```go
// cmd/server/main.go
package main

import (
	"log"
	"myapp/internal/api/router"
	"myapp/internal/config"
)

func main() {
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("failed to load config: %v", err)
	}

	r := router.NewRouter(cfg)

	if err := r.Run(cfg.ServerAddress); err != nil {
		log.Fatalf("failed to start server: %v", err)
	}
}
```

**Why**: Separating concerns into handlers, services, and repositories improves testability,
enables dependency injection, and makes the codebase maintainable as it grows. The `internal/`
directory prevents accidental imports by other projects.

## Router Setup

Projects **MUST** configure the router in a dedicated function for testability:

```go
// internal/api/router/router.go
package router

import (
	"myapp/internal/api/handler"
	"myapp/internal/api/middleware"
	"myapp/internal/config"

	"github.com/gin-gonic/gin"
)

func NewRouter(cfg *config.Config) *gin.Engine {
	// Use release mode in production
	if cfg.Environment == "production" {
		gin.SetMode(gin.ReleaseMode)
	}

	r := gin.New()

	// Global middleware
	r.Use(gin.Recovery())
	r.Use(middleware.Logger())
	r.Use(middleware.CORS())

	// Health check (no auth required)
	r.GET("/health", handler.HealthCheck)

	// API v1 routes
	v1 := r.Group("/api/v1")
	{
		// Public routes
		v1.POST("/auth/login", handler.Login)
		v1.POST("/auth/register", handler.Register)

		// Protected routes
		authorized := v1.Group("")
		authorized.Use(middleware.Auth())
		{
			users := authorized.Group("/users")
			{
				users.GET("", handler.ListUsers)
				users.GET("/:id", handler.GetUser)
				users.POST("", handler.CreateUser)
				users.PUT("/:id", handler.UpdateUser)
				users.DELETE("/:id", handler.DeleteUser)
			}
		}
	}

	return r
}
```

**Why**: Centralizing route configuration improves discoverability and makes it easy to see the
entire API surface. Using route groups enables logical organization and scoped middleware
application.

## RESTful Routing Patterns

Projects **MUST** follow RESTful conventions for resource routing:

```go
// DO: Use standard HTTP methods and resource-based URLs
r.GET("/api/v1/posts", handler.ListPosts)          // List all posts
r.POST("/api/v1/posts", handler.CreatePost)        // Create new post
r.GET("/api/v1/posts/:id", handler.GetPost)        // Get specific post
r.PUT("/api/v1/posts/:id", handler.UpdatePost)     // Update entire post
r.PATCH("/api/v1/posts/:id", handler.PatchPost)    // Partial update
r.DELETE("/api/v1/posts/:id", handler.DeletePost)  // Delete post

// Nested resources
r.GET("/api/v1/posts/:id/comments", handler.ListPostComments)
r.POST("/api/v1/posts/:id/comments", handler.CreateComment)

// DON'T: Use verbs in URLs
r.GET("/api/v1/getPost/:id", handler.GetPost)      // Bad
r.POST("/api/v1/createPost", handler.CreatePost)   // Bad
r.DELETE("/api/v1/deletePost/:id", handler.DeletePost)  // Bad
```

## Handler Structure

Handlers **MUST** follow a consistent structure with clear separation of concerns:

```go
// internal/api/handler/user.go
package handler

import (
	"myapp/internal/model"
	"myapp/internal/service"
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
)

type UserHandler struct {
	userService service.UserService
}

func NewUserHandler(userService service.UserService) *UserHandler {
	return &UserHandler{
		userService: userService,
	}
}

// GetUser retrieves a user by ID
// @Summary Get user by ID
// @Description Get user details by user ID
// @Tags users
// @Accept json
// @Produce json
// @Param id path int true "User ID"
// @Success 200 {object} model.User
// @Failure 400 {object} ErrorResponse
// @Failure 404 {object} ErrorResponse
// @Router /api/v1/users/{id} [get]
func (h *UserHandler) GetUser(c *gin.Context) {
	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid user ID"})
		return
	}

	user, err := h.userService.GetByID(c.Request.Context(), id)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "user not found"})
		return
	}

	c.JSON(http.StatusOK, user)
}

// CreateUser creates a new user
func (h *UserHandler) CreateUser(c *gin.Context) {
	var req model.CreateUserRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	user, err := h.userService.Create(c.Request.Context(), &req)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, user)
}
```

**Why**: Dependency injection via handler structs enables testing with mock services. Using the
request context allows request-scoped cancellation and tracing. Swagger annotations[^5] enable
automatic API documentation generation.

## Middleware

### Built-in Middleware

Projects **MUST** use appropriate built-in middleware:

```go
import (
	"github.com/gin-gonic/gin"
)

func NewRouter() *gin.Engine {
	r := gin.New()

	// MUST: Recovery middleware prevents panics from crashing the server
	r.Use(gin.Recovery())

	// SHOULD: Logger middleware for request logging
	r.Use(gin.Logger())

	// MAY: Custom middleware for specific needs
	r.Use(CustomMiddleware())

	return r
}
```

**Why**: `gin.Recovery()` prevents panics from crashing the entire application. `gin.Logger()`
provides request logging but **SHOULD** be replaced with structured logging in production.

### Custom Middleware

Projects **SHOULD** implement custom middleware for cross-cutting concerns:

```go
// internal/api/middleware/auth.go
package middleware

import (
	"net/http"
	"strings"

	"github.com/gin-gonic/gin"
)

// Auth validates JWT tokens
func Auth() gin.HandlerFunc {
	return func(c *gin.Context) {
		authHeader := c.GetHeader("Authorization")
		if authHeader == "" {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "missing authorization header"})
			c.Abort()
			return
		}

		parts := strings.SplitN(authHeader, " ", 2)
		if len(parts) != 2 || parts[0] != "Bearer" {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "invalid authorization header"})
			c.Abort()
			return
		}

		token := parts[1]
		claims, err := validateToken(token)
		if err != nil {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "invalid token"})
			c.Abort()
			return
		}

		// Store user info in context for handlers
		c.Set("userID", claims.UserID)
		c.Set("email", claims.Email)

		c.Next()
	}
}
```

```go
// internal/api/middleware/logging.go
package middleware

import (
	"log/slog"
	"time"

	"github.com/gin-gonic/gin"
)

// Logger provides structured logging for requests
func Logger() gin.HandlerFunc {
	return func(c *gin.Context) {
		start := time.Now()
		path := c.Request.URL.Path
		method := c.Request.Method

		c.Next()

		latency := time.Since(start)
		status := c.Writer.Status()

		slog.Info("request completed",
			"method", method,
			"path", path,
			"status", status,
			"latency", latency,
			"ip", c.ClientIP(),
		)
	}
}
```

**Why**: Custom middleware enables consistent handling of authentication, logging, and CORS
across all routes. Using `c.Set()` and `c.Get()` allows middleware to pass data to handlers
without global state.

## Request Validation and Binding

Projects **MUST** use Gin's binding and validation features:

```go
// internal/model/user.go
package model

type CreateUserRequest struct {
	Email    string `json:"email" binding:"required,email"`
	Username string `json:"username" binding:"required,min=3,max=50"`
	Password string `json:"password" binding:"required,min=8"`
	Age      int    `json:"age" binding:"omitempty,gte=18,lte=120"`
}

type UpdateUserRequest struct {
	Email    string `json:"email" binding:"omitempty,email"`
	Username string `json:"username" binding:"omitempty,min=3,max=50"`
	Age      int    `json:"age" binding:"omitempty,gte=18,lte=120"`
}

type User struct {
	ID        int64     `json:"id"`
	Email     string    `json:"email"`
	Username  string    `json:"username"`
	Age       int       `json:"age,omitempty"`
	CreatedAt time.Time `json:"created_at"`
}
```

```go
// Binding examples
func (h *UserHandler) CreateUser(c *gin.Context) {
	var req model.CreateUserRequest

	// ShouldBindJSON validates and binds JSON
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "validation failed",
			"details": err.Error(),
		})
		return
	}

	// Request is now validated
	user, err := h.userService.Create(c.Request.Context(), &req)
	// ...
}

// Query parameter binding
type ListUsersQuery struct {
	Page     int    `form:"page" binding:"omitempty,gte=1"`
	PageSize int    `form:"page_size" binding:"omitempty,gte=1,lte=100"`
	Sort     string `form:"sort" binding:"omitempty,oneof=name email created_at"`
}

func (h *UserHandler) ListUsers(c *gin.Context) {
	var query ListUsersQuery
	if err := c.ShouldBindQuery(&query); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	// Use validated query parameters
}

// URI parameter binding
type UserIDParam struct {
	ID int64 `uri:"id" binding:"required,gte=1"`
}

func (h *UserHandler) GetUser(c *gin.Context) {
	var param UserIDParam
	if err := c.ShouldBindUri(&param); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	// Use param.ID
}
```

**Why**: Gin uses the validator package[^6] under the hood, providing comprehensive validation
rules via struct tags. This eliminates manual validation code and produces consistent error
messages.

### Custom Validators

Projects **MAY** register custom validation functions:

```go
// pkg/validator/custom.go
package validator

import (
	"regexp"

	"github.com/go-playground/validator/v10"
)

var phoneRegex = regexp.MustCompile(`^\+?[1-9]\d{1,14}$`)

// ValidatePhone checks if the value is a valid phone number
func ValidatePhone(fl validator.FieldLevel) bool {
	return phoneRegex.MatchString(fl.Field().String())
}

// RegisterCustomValidators registers all custom validators
func RegisterCustomValidators(v *validator.Validate) error {
	if err := v.RegisterValidation("phone", ValidatePhone); err != nil {
		return err
	}
	return nil
}
```

```go
// Usage in model
type CreateUserRequest struct {
	Phone string `json:"phone" binding:"required,phone"`
}
```

## Error Handling

Projects **MUST** implement consistent error handling with custom error types:

```go
// internal/api/handler/error.go
package handler

import (
	"errors"
	"net/http"

	"github.com/gin-gonic/gin"
)

type ErrorResponse struct {
	Error   string `json:"error"`
	Message string `json:"message,omitempty"`
	Code    string `json:"code,omitempty"`
}

// Custom error types
var (
	ErrNotFound          = errors.New("resource not found")
	ErrUnauthorized      = errors.New("unauthorized")
	ErrForbidden         = errors.New("forbidden")
	ErrValidation        = errors.New("validation failed")
	ErrInternalServer    = errors.New("internal server error")
)

// HandleError processes errors and returns appropriate HTTP responses
func HandleError(c *gin.Context, err error) {
	switch {
	case errors.Is(err, ErrNotFound):
		c.JSON(http.StatusNotFound, ErrorResponse{
			Error: "not_found",
			Message: err.Error(),
		})
	case errors.Is(err, ErrUnauthorized):
		c.JSON(http.StatusUnauthorized, ErrorResponse{
			Error: "unauthorized",
			Message: err.Error(),
		})
	case errors.Is(err, ErrValidation):
		c.JSON(http.StatusBadRequest, ErrorResponse{
			Error: "validation_error",
			Message: err.Error(),
		})
	default:
		// Don't expose internal errors to clients
		c.JSON(http.StatusInternalServerError, ErrorResponse{
			Error: "internal_error",
			Message: "an unexpected error occurred",
		})
	}
}
```

```go
// Usage in handlers
func (h *UserHandler) GetUser(c *gin.Context) {
	id := c.Param("id")

	user, err := h.userService.GetByID(c.Request.Context(), id)
	if err != nil {
		HandleError(c, err)
		return
	}

	c.JSON(http.StatusOK, user)
}
```

**Why**: Centralized error handling ensures consistent error responses across the API. Using
`errors.Is()` allows error wrapping while maintaining error type checking.

## Testing

Projects **MUST** test Gin handlers using httptest:

```go
// internal/api/handler/user_test.go
package handler

import (
	"bytes"
	"encoding/json"
	"errors"
	"myapp/internal/model"
	"myapp/internal/service/mocks"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

func TestGetUser(t *testing.T) {
	gin.SetMode(gin.TestMode)

	tests := []struct {
		name           string
		userID         string
		mockSetup      func(*mocks.UserService)
		expectedStatus int
		expectedBody   map[string]interface{}
	}{
		{
			name:   "success",
			userID: "1",
			mockSetup: func(m *mocks.UserService) {
				m.On("GetByID", mock.Anything, int64(1)).
					Return(&model.User{
						ID:       1,
						Email:    "test@example.com",
						Username: "testuser",
					}, nil)
			},
			expectedStatus: http.StatusOK,
		},
		{
			name:   "user not found",
			userID: "999",
			mockSetup: func(m *mocks.UserService) {
				m.On("GetByID", mock.Anything, int64(999)).
					Return(nil, ErrNotFound)
			},
			expectedStatus: http.StatusNotFound,
		},
		{
			name:           "invalid user ID",
			userID:         "abc",
			mockSetup:      func(m *mocks.UserService) {},
			expectedStatus: http.StatusBadRequest,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Setup
			mockService := new(mocks.UserService)
			tt.mockSetup(mockService)

			handler := NewUserHandler(mockService)
			router := gin.New()
			router.GET("/users/:id", handler.GetUser)

			// Execute
			req := httptest.NewRequest(http.MethodGet, "/users/"+tt.userID, nil)
			w := httptest.NewRecorder()
			router.ServeHTTP(w, req)

			// Assert
			assert.Equal(t, tt.expectedStatus, w.Code)
			mockService.AssertExpectations(t)
		})
	}
}

func TestCreateUser(t *testing.T) {
	gin.SetMode(gin.TestMode)

	t.Run("success", func(t *testing.T) {
		mockService := new(mocks.UserService)
		mockService.On("Create", mock.Anything, mock.AnythingOfType("*model.CreateUserRequest")).
			Return(&model.User{
				ID:       1,
				Email:    "test@example.com",
				Username: "testuser",
			}, nil)

		handler := NewUserHandler(mockService)
		router := gin.New()
		router.POST("/users", handler.CreateUser)

		reqBody := model.CreateUserRequest{
			Email:    "test@example.com",
			Username: "testuser",
			Password: "password123",
		}
		body, _ := json.Marshal(reqBody)

		req := httptest.NewRequest(http.MethodPost, "/users", bytes.NewBuffer(body))
		req.Header.Set("Content-Type", "application/json")
		w := httptest.NewRecorder()

		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusCreated, w.Code)
		mockService.AssertExpectations(t)
	})

	t.Run("validation error", func(t *testing.T) {
		mockService := new(mocks.UserService)
		handler := NewUserHandler(mockService)
		router := gin.New()
		router.POST("/users", handler.CreateUser)

		// Invalid request (missing required fields)
		reqBody := map[string]interface{}{
			"email": "invalid-email",
		}
		body, _ := json.Marshal(reqBody)

		req := httptest.NewRequest(http.MethodPost, "/users", bytes.NewBuffer(body))
		req.Header.Set("Content-Type", "application/json")
		w := httptest.NewRecorder()

		router.ServeHTTP(w, req)

		assert.Equal(t, http.StatusBadRequest, w.Code)
	})
}
```

**Why**: Using httptest allows testing handlers without starting a server. Mocking the service
layer isolates handler logic from business logic and database dependencies.

### Integration Testing

Projects **SHOULD** include integration tests for critical paths:

```go
// internal/api/integration_test.go
package api

import (
	"encoding/json"
	"myapp/internal/config"
	"myapp/internal/api/router"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestUserFlow(t *testing.T) {
	if testing.Short() {
		t.Skip("skipping integration test")
	}

	// Setup test database
	cfg := config.LoadTest()
	r := router.NewRouter(cfg)

	// Register user
	t.Run("register", func(t *testing.T) {
		reqBody := `{"email":"test@example.com","username":"testuser","password":"password123"}`
		req := httptest.NewRequest(http.MethodPost, "/api/v1/auth/register",
			bytes.NewBufferString(reqBody))
		req.Header.Set("Content-Type", "application/json")
		w := httptest.NewRecorder()

		r.ServeHTTP(w, req)

		assert.Equal(t, http.StatusCreated, w.Code)
	})

	// Login
	var token string
	t.Run("login", func(t *testing.T) {
		reqBody := `{"email":"test@example.com","password":"password123"}`
		req := httptest.NewRequest(http.MethodPost, "/api/v1/auth/login",
			bytes.NewBufferString(reqBody))
		req.Header.Set("Content-Type", "application/json")
		w := httptest.NewRecorder()

		r.ServeHTTP(w, req)

		require.Equal(t, http.StatusOK, w.Code)

		var resp map[string]string
		err := json.Unmarshal(w.Body.Bytes(), &resp)
		require.NoError(t, err)
		token = resp["token"]
		require.NotEmpty(t, token)
	})

	// Access protected resource
	t.Run("get user", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodGet, "/api/v1/users/1", nil)
		req.Header.Set("Authorization", "Bearer "+token)
		w := httptest.NewRecorder()

		r.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
	})
}
```

## Configuration

Projects **MUST** use environment-based configuration:

```go
// internal/config/config.go
package config

import (
	"fmt"
	"os"
	"strconv"

	"github.com/joho/godotenv"
)

type Config struct {
	Environment   string
	ServerAddress string
	DatabaseURL   string
	JWTSecret     string
	LogLevel      string
}

func Load() (*Config, error) {
	// Load .env file in development
	_ = godotenv.Load()

	cfg := &Config{
		Environment:   getEnv("ENVIRONMENT", "development"),
		ServerAddress: getEnv("SERVER_ADDRESS", ":8080"),
		DatabaseURL:   getEnv("DATABASE_URL", ""),
		JWTSecret:     getEnv("JWT_SECRET", ""),
		LogLevel:      getEnv("LOG_LEVEL", "info"),
	}

	if cfg.DatabaseURL == "" {
		return nil, fmt.Errorf("DATABASE_URL is required")
	}

	if cfg.JWTSecret == "" && cfg.Environment == "production" {
		return nil, fmt.Errorf("JWT_SECRET is required in production")
	}

	return cfg, nil
}

func LoadTest() *Config {
	return &Config{
		Environment:   "test",
		ServerAddress: ":8080",
		DatabaseURL:   "sqlite::memory:",
		JWTSecret:     "test-secret",
		LogLevel:      "debug",
	}
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getEnvInt(key string, defaultValue int) int {
	if value := os.Getenv(key); value != "" {
		if intVal, err := strconv.Atoi(value); err == nil {
			return intVal
		}
	}
	return defaultValue
}
```

**Why**: Environment-based configuration follows twelve-factor app principles, prevents secrets
in version control, and enables different settings per deployment environment.

## Logging and Observability

Projects **MUST** use Go's standard library `log/slog` package for structured logging. The
`slog` package (introduced in Go 1.21) provides structured, leveled logging with excellent
performance.

### Logger Setup

Configure the global logger at application startup:

```go
// internal/logger/logger.go
package logger

import (
	"log/slog"
	"os"
)

// Setup configures the global slog logger
func Setup(env string, level slog.Level) {
	var handler slog.Handler

	opts := &slog.HandlerOptions{
		Level: level,
		// Add source file information in debug mode
		AddSource: level == slog.LevelDebug,
	}

	if env == "production" {
		// JSON output for production (log aggregation systems)
		handler = slog.NewJSONHandler(os.Stdout, opts)
	} else {
		// Human-readable output for development
		handler = slog.NewTextHandler(os.Stdout, opts)
	}

	slog.SetDefault(slog.New(handler))
}

// ParseLevel converts a string to slog.Level
func ParseLevel(level string) slog.Level {
	switch level {
	case "debug":
		return slog.LevelDebug
	case "info":
		return slog.LevelInfo
	case "warn":
		return slog.LevelWarn
	case "error":
		return slog.LevelError
	default:
		return slog.LevelInfo
	}
}
```

```go
// cmd/server/main.go
package main

import (
	"myapp/internal/config"
	"myapp/internal/logger"
)

func main() {
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("failed to load config: %v", err)
	}

	// Initialize structured logging
	logger.Setup(cfg.Environment, logger.ParseLevel(cfg.LogLevel))

	slog.Info("starting server",
		"address", cfg.ServerAddress,
		"environment", cfg.Environment,
	)

	// ... rest of setup
}
```

### Request Logging Middleware

Projects **SHOULD** use structured logging with context propagation:

```go
// internal/api/middleware/logging.go
package middleware

import (
	"context"
	"log/slog"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

type contextKey string

const loggerKey contextKey = "logger"

// RequestID adds a unique request ID to each request
func RequestID() gin.HandlerFunc {
	return func(c *gin.Context) {
		requestID := c.GetHeader("X-Request-ID")
		if requestID == "" {
			requestID = uuid.New().String()
		}
		c.Set("requestID", requestID)
		c.Header("X-Request-ID", requestID)
		c.Next()
	}
}

// StructuredLogger provides structured logging with request context
func StructuredLogger() gin.HandlerFunc {
	return func(c *gin.Context) {
		start := time.Now()
		path := c.Request.URL.Path
		method := c.Request.Method
		requestID, _ := c.Get("requestID")

		// Create request-scoped logger with common attributes
		reqLogger := slog.With(
			"request_id", requestID,
			"method", method,
			"path", path,
		)

		// Store logger in context for use in handlers
		ctx := context.WithValue(c.Request.Context(), loggerKey, reqLogger)
		c.Request = c.Request.WithContext(ctx)

		c.Next()

		latency := time.Since(start)
		status := c.Writer.Status()
		errorMsg := c.Errors.ByType(gin.ErrorTypePrivate).String()

		attrs := []slog.Attr{
			slog.String("request_id", requestID.(string)),
			slog.String("method", method),
			slog.String("path", path),
			slog.Int("status", status),
			slog.Duration("latency", latency),
			slog.String("ip", c.ClientIP()),
			slog.String("user_agent", c.Request.UserAgent()),
			slog.Int("bytes_written", c.Writer.Size()),
		}

		if errorMsg != "" {
			attrs = append(attrs, slog.String("error", errorMsg))
		}

		level := slog.LevelInfo
		if status >= 500 {
			level = slog.LevelError
		} else if status >= 400 {
			level = slog.LevelWarn
		}

		slog.LogAttrs(c.Request.Context(), level, "request completed", attrs...)
	}
}

// LoggerFromContext retrieves the request-scoped logger
func LoggerFromContext(ctx context.Context) *slog.Logger {
	if logger, ok := ctx.Value(loggerKey).(*slog.Logger); ok {
		return logger
	}
	return slog.Default()
}
```

### Using the Logger in Handlers

Handlers **SHOULD** use the request-scoped logger for contextual logging:

```go
// internal/api/handler/user.go
package handler

import (
	"log/slog"
	"myapp/internal/api/middleware"
	"net/http"

	"github.com/gin-gonic/gin"
)

func (h *UserHandler) CreateUser(c *gin.Context) {
	logger := middleware.LoggerFromContext(c.Request.Context())

	var req model.CreateUserRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		logger.Warn("invalid request body", "error", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	logger.Debug("creating user", "email", req.Email)

	user, err := h.userService.Create(c.Request.Context(), &req)
	if err != nil {
		logger.Error("failed to create user",
			"error", err,
			"email", req.Email,
		)
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	logger.Info("user created",
		"user_id", user.ID,
		"email", user.Email,
	)

	c.JSON(http.StatusCreated, user)
}
```

### Logging in Services

Services **SHOULD** accept a logger or use context-based logging:

```go
// internal/service/user.go
package service

import (
	"context"
	"log/slog"
)

type UserService struct {
	repo   UserRepository
	logger *slog.Logger
}

func NewUserService(repo UserRepository) *UserService {
	return &UserService{
		repo:   repo,
		logger: slog.Default().With("service", "user"),
	}
}

func (s *UserService) Create(ctx context.Context, req *model.CreateUserRequest) (*model.User, error) {
	s.logger.DebugContext(ctx, "creating user in database", "email", req.Email)

	user, err := s.repo.Create(ctx, req)
	if err != nil {
		s.logger.ErrorContext(ctx, "database error creating user",
			"error", err,
			"email", req.Email,
		)
		return nil, fmt.Errorf("create user: %w", err)
	}

	s.logger.InfoContext(ctx, "user created successfully",
		"user_id", user.ID,
	)

	return user, nil
}
```

### Logging with Groups

Use `slog.Group` to organize related attributes:

```go
func (h *OrderHandler) CreateOrder(c *gin.Context) {
	logger := middleware.LoggerFromContext(c.Request.Context())

	// Log with grouped attributes for better organization
	logger.Info("order created",
		slog.Group("order",
			slog.String("id", order.ID),
			slog.Float64("total", order.Total),
			slog.Int("item_count", len(order.Items)),
		),
		slog.Group("customer",
			slog.String("id", order.CustomerID),
			slog.String("email", order.CustomerEmail),
		),
	)
}
```

**Why slog**: Go's standard library `log/slog` provides structured logging without external
dependencies. It offers excellent performance, type-safe attributes, log levels, and outputs
JSON for production log aggregation systems. Context propagation maintains request-scoped
logging attributes across service boundaries.

### Health Checks and Metrics

Projects **SHOULD** expose health check and metrics endpoints:

```go
// internal/api/handler/health.go
package handler

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

type HealthHandler struct {
	db DBHealthChecker
}

type DBHealthChecker interface {
	Ping() error
}

func NewHealthHandler(db DBHealthChecker) *HealthHandler {
	return &HealthHandler{db: db}
}

// HealthCheck returns the service health status
func (h *HealthHandler) HealthCheck(c *gin.Context) {
	health := map[string]string{
		"status": "healthy",
	}

	if err := h.db.Ping(); err != nil {
		health["status"] = "unhealthy"
		health["database"] = "down"
		c.JSON(http.StatusServiceUnavailable, health)
		return
	}

	health["database"] = "up"
	c.JSON(http.StatusOK, health)
}

// ReadinessCheck determines if the service is ready to serve traffic
func (h *HealthHandler) ReadinessCheck(c *gin.Context) {
	if err := h.db.Ping(); err != nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{
			"ready": false,
			"reason": "database not ready",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{"ready": true})
}
```

**Why**: Health checks enable orchestrators (Kubernetes, Docker) to monitor service health and
restart unhealthy instances. Separating liveness and readiness checks prevents cascading
failures during deployment.

## Security

### JWT Authentication

Projects **MUST** use golang-jwt/jwt[^7] v5 for JWT token handling. The library provides robust
token generation, parsing, and validation with support for multiple signing algorithms.

#### Why

JWT (JSON Web Tokens) provides stateless authentication suitable for APIs and microservices.
Using RS256 (asymmetric keys) allows public key distribution for token verification without
exposing signing credentials.

#### Token Generation

```go
// internal/auth/jwt.go
package auth

import (
	"crypto/rsa"
	"time"

	"github.com/golang-jwt/jwt/v5"
)

type Claims struct {
	jwt.RegisteredClaims
	UserID int64  `json:"user_id"`
	Email  string `json:"email"`
	Role   string `json:"role"`
}

type JWTService struct {
	privateKey *rsa.PrivateKey
	publicKey  *rsa.PublicKey
	issuer     string
}

func NewJWTService(privateKey *rsa.PrivateKey, publicKey *rsa.PublicKey, issuer string) *JWTService {
	return &JWTService{
		privateKey: privateKey,
		publicKey:  publicKey,
		issuer:     issuer,
	}
}

// GenerateToken creates a new JWT token for a user
func (s *JWTService) GenerateToken(userID int64, email, role string) (string, error) {
	claims := Claims{
		RegisteredClaims: jwt.RegisteredClaims{
			Issuer:    s.issuer,
			Subject:   email,
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(24 * time.Hour)),
			IssuedAt:  jwt.NewNumericDate(time.Now()),
			NotBefore: jwt.NewNumericDate(time.Now()),
		},
		UserID: userID,
		Email:  email,
		Role:   role,
	}

	token := jwt.NewWithClaims(jwt.SigningMethodRS256, claims)
	return token.SignedString(s.privateKey)
}

// ValidateToken parses and validates a JWT token
func (s *JWTService) ValidateToken(tokenString string) (*Claims, error) {
	token, err := jwt.ParseWithClaims(
		tokenString,
		&Claims{},
		func(token *jwt.Token) (interface{}, error) {
			// MUST verify the signing method matches expected algorithm
			if _, ok := token.Method.(*jwt.SigningMethodRSA); !ok {
				return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
			}
			return s.publicKey, nil
		},
		jwt.WithIssuer(s.issuer),
		jwt.WithExpirationRequired(),
	)
	if err != nil {
		return nil, fmt.Errorf("invalid token: %w", err)
	}

	claims, ok := token.Claims.(*Claims)
	if !ok || !token.Valid {
		return nil, errors.New("invalid token claims")
	}

	return claims, nil
}
```

#### JWT Middleware

```go
// internal/api/middleware/jwt.go
package middleware

import (
	"net/http"
	"strings"

	"myapp/internal/auth"

	"github.com/gin-gonic/gin"
)

func JWTAuth(jwtService *auth.JWTService) gin.HandlerFunc {
	return func(c *gin.Context) {
		authHeader := c.GetHeader("Authorization")
		if authHeader == "" {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "missing authorization header"})
			c.Abort()
			return
		}

		parts := strings.SplitN(authHeader, " ", 2)
		if len(parts) != 2 || parts[0] != "Bearer" {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "invalid authorization format"})
			c.Abort()
			return
		}

		claims, err := jwtService.ValidateToken(parts[1])
		if err != nil {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "invalid token"})
			c.Abort()
			return
		}

		// Store claims in context for handlers
		c.Set("claims", claims)
		c.Set("userID", claims.UserID)
		c.Set("email", claims.Email)
		c.Set("role", claims.Role)

		c.Next()
	}
}
```

**Why**: RS256 is preferred over HS256 for production because the private key stays on the auth
server while public keys can be distributed to all services needing to verify tokens. Always
validate the `alg` header to prevent algorithm confusion attacks.

### OAuth2 Integration

Projects **SHOULD** use golang.org/x/oauth2[^8] for OAuth2 flows when integrating with external
identity providers.

#### Why

OAuth2 provides standardized authentication flows for third-party integrations (Google, GitHub,
etc.). The official Go package supports all major grant types and handles token refresh
automatically.

```go
// internal/auth/oauth2.go
package auth

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"

	"golang.org/x/oauth2"
	"golang.org/x/oauth2/google"
)

type OAuth2Service struct {
	config *oauth2.Config
}

func NewGoogleOAuth2(clientID, clientSecret, redirectURL string) *OAuth2Service {
	return &OAuth2Service{
		config: &oauth2.Config{
			ClientID:     clientID,
			ClientSecret: clientSecret,
			RedirectURL:  redirectURL,
			Scopes:       []string{"openid", "email", "profile"},
			Endpoint:     google.Endpoint,
		},
	}
}

// GetAuthURL generates the OAuth2 authorization URL
func (s *OAuth2Service) GetAuthURL(state string) string {
	return s.config.AuthCodeURL(state, oauth2.AccessTypeOffline)
}

// Exchange exchanges an authorization code for tokens
func (s *OAuth2Service) Exchange(ctx context.Context, code string) (*oauth2.Token, error) {
	token, err := s.config.Exchange(ctx, code)
	if err != nil {
		return nil, fmt.Errorf("failed to exchange code: %w", err)
	}
	return token, nil
}

// GetUserInfo retrieves user information using the access token
func (s *OAuth2Service) GetUserInfo(ctx context.Context, token *oauth2.Token) (*GoogleUserInfo, error) {
	client := s.config.Client(ctx, token)

	resp, err := client.Get("https://www.googleapis.com/oauth2/v3/userinfo")
	if err != nil {
		return nil, fmt.Errorf("failed to get user info: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("user info request failed: %s", resp.Status)
	}

	var userInfo GoogleUserInfo
	if err := json.NewDecoder(resp.Body).Decode(&userInfo); err != nil {
		return nil, fmt.Errorf("failed to decode user info: %w", err)
	}

	return &userInfo, nil
}

type GoogleUserInfo struct {
	Sub           string `json:"sub"`
	Email         string `json:"email"`
	EmailVerified bool   `json:"email_verified"`
	Name          string `json:"name"`
	Picture       string `json:"picture"`
}
```

```go
// OAuth2 handlers
func (h *AuthHandler) GoogleLogin(c *gin.Context) {
	state := generateSecureState()
	// Store state in session/cookie for CSRF protection
	c.SetCookie("oauth_state", state, 600, "/", "", true, true)
	c.Redirect(http.StatusTemporaryRedirect, h.oauth2Service.GetAuthURL(state))
}

func (h *AuthHandler) GoogleCallback(c *gin.Context) {
	// Verify state parameter to prevent CSRF
	stateCookie, err := c.Cookie("oauth_state")
	if err != nil || stateCookie != c.Query("state") {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid state parameter"})
		return
	}

	code := c.Query("code")
	token, err := h.oauth2Service.Exchange(c.Request.Context(), code)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to exchange token"})
		return
	}

	userInfo, err := h.oauth2Service.GetUserInfo(c.Request.Context(), token)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to get user info"})
		return
	}

	// Create or update user in database, generate JWT, etc.
	jwtToken, err := h.createOrUpdateUser(c.Request.Context(), userInfo)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to process user"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"token": jwtToken})
}
```

### Authorization with Casbin

Projects **SHOULD** use Casbin[^9] for role-based access control (RBAC) and attribute-based
access control (ABAC).

#### Why

Casbin provides a declarative policy model that separates authorization logic from business
code. Policies can be stored in files or databases and updated at runtime without code changes.

```go
// internal/auth/casbin.go
package auth

import (
	"github.com/casbin/casbin/v2"
	gormadapter "github.com/casbin/gorm-adapter/v3"
	"gorm.io/gorm"
)

// NewCasbinEnforcer creates a Casbin enforcer with database storage
func NewCasbinEnforcer(db *gorm.DB, modelPath string) (*casbin.Enforcer, error) {
	adapter, err := gormadapter.NewAdapterByDB(db)
	if err != nil {
		return nil, fmt.Errorf("failed to create casbin adapter: %w", err)
	}

	enforcer, err := casbin.NewEnforcer(modelPath, adapter)
	if err != nil {
		return nil, fmt.Errorf("failed to create casbin enforcer: %w", err)
	}

	// Load policies from database
	if err := enforcer.LoadPolicy(); err != nil {
		return nil, fmt.Errorf("failed to load policies: %w", err)
	}

	return enforcer, nil
}
```

```ini
# configs/casbin/rbac_model.conf
[request_definition]
r = sub, obj, act

[policy_definition]
p = sub, obj, act

[role_definition]
g = _, _

[policy_effect]
e = some(where (p.eft == allow))

[matchers]
m = g(r.sub, p.sub) && keyMatch2(r.obj, p.obj) && r.act == p.act
```

```go
// internal/api/middleware/authorization.go
package middleware

import (
	"net/http"

	"github.com/casbin/casbin/v2"
	"github.com/gin-gonic/gin"
)

// CasbinAuth enforces authorization using Casbin policies
func CasbinAuth(enforcer *casbin.Enforcer) gin.HandlerFunc {
	return func(c *gin.Context) {
		role, exists := c.Get("role")
		if !exists {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "no role found"})
			c.Abort()
			return
		}

		obj := c.Request.URL.Path
		act := c.Request.Method

		allowed, err := enforcer.Enforce(role.(string), obj, act)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "authorization check failed"})
			c.Abort()
			return
		}

		if !allowed {
			c.JSON(http.StatusForbidden, gin.H{"error": "permission denied"})
			c.Abort()
			return
		}

		c.Next()
	}
}
```

```go
// Router setup with Casbin
func NewRouter(cfg *config.Config, enforcer *casbin.Enforcer, jwtService *auth.JWTService) *gin.Engine {
	r := gin.New()
	r.Use(gin.Recovery())

	// Public routes
	r.POST("/api/v1/auth/login", handler.Login)

	// Protected routes with RBAC
	api := r.Group("/api/v1")
	api.Use(middleware.JWTAuth(jwtService))
	api.Use(middleware.CasbinAuth(enforcer))
	{
		api.GET("/users", handler.ListUsers)        // Requires: admin, /api/v1/users, GET
		api.POST("/users", handler.CreateUser)      // Requires: admin, /api/v1/users, POST
		api.GET("/users/:id", handler.GetUser)      // Requires: user, /api/v1/users/:id, GET
	}

	return r
}
```

**Why**: Casbin decouples authorization from code, enabling policy changes without redeployment.
The PERM model (Policy, Effect, Request, Matchers) supports complex scenarios like
multi-tenancy and hierarchical roles.

## WebSocket

Projects **SHOULD** use gorilla/websocket[^10] for production WebSocket implementations, or
coder/websocket[^11] (formerly nhooyr.io/websocket) for modern Go idioms and context support.

### Why

WebSocket enables bidirectional real-time communication for features like chat, notifications,
and live updates. gorilla/websocket is battle-tested with extensive documentation, while
coder/websocket offers a more idiomatic Go API with built-in context support.

### gorilla/websocket Integration

```go
// internal/api/handler/websocket.go
package handler

import (
	"log/slog"
	"net/http"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/gorilla/websocket"
)

var upgrader = websocket.Upgrader{
	ReadBufferSize:  1024,
	WriteBufferSize: 1024,
	CheckOrigin: func(r *http.Request) bool {
		// MUST validate origin in production
		origin := r.Header.Get("Origin")
		return origin == "https://yourdomain.com"
	},
}

type Client struct {
	conn   *websocket.Conn
	send   chan []byte
	userID int64
}

type Hub struct {
	clients    map[*Client]bool
	broadcast  chan []byte
	register   chan *Client
	unregister chan *Client
	mu         sync.RWMutex
}

func NewHub() *Hub {
	return &Hub{
		clients:    make(map[*Client]bool),
		broadcast:  make(chan []byte, 256),
		register:   make(chan *Client),
		unregister: make(chan *Client),
	}
}

func (h *Hub) Run() {
	for {
		select {
		case client := <-h.register:
			h.mu.Lock()
			h.clients[client] = true
			h.mu.Unlock()
			slog.Info("client connected", "user_id", client.userID)

		case client := <-h.unregister:
			h.mu.Lock()
			if _, ok := h.clients[client]; ok {
				delete(h.clients, client)
				close(client.send)
			}
			h.mu.Unlock()
			slog.Info("client disconnected", "user_id", client.userID)

		case message := <-h.broadcast:
			h.mu.RLock()
			for client := range h.clients {
				select {
				case client.send <- message:
				default:
					close(client.send)
					delete(h.clients, client)
				}
			}
			h.mu.RUnlock()
		}
	}
}

type WebSocketHandler struct {
	hub *Hub
}

func NewWebSocketHandler(hub *Hub) *WebSocketHandler {
	return &WebSocketHandler{hub: hub}
}

func (h *WebSocketHandler) HandleWebSocket(c *gin.Context) {
	userID, exists := c.Get("userID")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "unauthorized"})
		return
	}

	conn, err := upgrader.Upgrade(c.Writer, c.Request, nil)
	if err != nil {
		slog.Error("websocket upgrade failed", "error", err)
		return
	}

	client := &Client{
		conn:   conn,
		send:   make(chan []byte, 256),
		userID: userID.(int64),
	}

	h.hub.register <- client

	go h.writePump(client)
	go h.readPump(client)
}

func (h *WebSocketHandler) readPump(client *Client) {
	defer func() {
		h.hub.unregister <- client
		client.conn.Close()
	}()

	client.conn.SetReadLimit(512)
	client.conn.SetReadDeadline(time.Now().Add(60 * time.Second))
	client.conn.SetPongHandler(func(string) error {
		client.conn.SetReadDeadline(time.Now().Add(60 * time.Second))
		return nil
	})

	for {
		_, message, err := client.conn.ReadMessage()
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
				slog.Error("websocket read error", "error", err)
			}
			break
		}
		h.hub.broadcast <- message
	}
}

func (h *WebSocketHandler) writePump(client *Client) {
	ticker := time.NewTicker(54 * time.Second)
	defer func() {
		ticker.Stop()
		client.conn.Close()
	}()

	for {
		select {
		case message, ok := <-client.send:
			client.conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
			if !ok {
				client.conn.WriteMessage(websocket.CloseMessage, []byte{})
				return
			}

			if err := client.conn.WriteMessage(websocket.TextMessage, message); err != nil {
				return
			}

		case <-ticker.C:
			client.conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
			if err := client.conn.WriteMessage(websocket.PingMessage, nil); err != nil {
				return
			}
		}
	}
}
```

### coder/websocket Alternative

For projects preferring modern Go idioms with native context support:

```go
// internal/api/handler/websocket_coder.go
package handler

import (
	"context"
	"net/http"
	"time"

	"github.com/coder/websocket"
	"github.com/coder/websocket/wsjson"
	"github.com/gin-gonic/gin"
)

func (h *WebSocketHandler) HandleWebSocketCoder(c *gin.Context) {
	conn, err := websocket.Accept(c.Writer, c.Request, &websocket.AcceptOptions{
		OriginPatterns: []string{"yourdomain.com"},
	})
	if err != nil {
		slog.Error("websocket accept failed", "error", err)
		return
	}
	defer conn.CloseNow()

	ctx, cancel := context.WithTimeout(c.Request.Context(), 10*time.Minute)
	defer cancel()

	for {
		var msg Message
		err := wsjson.Read(ctx, conn, &msg)
		if err != nil {
			if websocket.CloseStatus(err) == websocket.StatusNormalClosure {
				return
			}
			slog.Error("websocket read error", "error", err)
			return
		}

		// Process message and respond
		response := processMessage(msg)
		if err := wsjson.Write(ctx, conn, response); err != nil {
			slog.Error("websocket write error", "error", err)
			return
		}
	}
}
```

**Why**: gorilla/websocket remains the standard for production deployments due to its maturity
and extensive testing. coder/websocket offers advantages for new projects needing context
cancellation, WASM support, or cleaner API patterns.

## Performance

### pprof Integration

Projects **MUST** enable pprof endpoints in development and **SHOULD** protect them in
production environments.

#### Why

Go's built-in pprof provides CPU profiling, memory profiling, goroutine analysis, and blocking
profiling essential for identifying performance bottlenecks.

```go
// cmd/server/main.go
package main

import (
	"net/http"
	_ "net/http/pprof" // Register pprof handlers
)

func main() {
	// ... application setup

	// Run pprof server on separate port (protected in production)
	if cfg.Environment != "production" {
		go func() {
			// pprof endpoints: /debug/pprof/
			if err := http.ListenAndServe(":6060", nil); err != nil {
				slog.Error("pprof server failed", "error", err)
			}
		}()
	}

	// Main application server
	if err := r.Run(cfg.ServerAddress); err != nil {
		log.Fatalf("server failed: %v", err)
	}
}
```

```bash
# CPU profiling (30 seconds)
go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30

# Memory profiling
go tool pprof http://localhost:6060/debug/pprof/heap

# Goroutine analysis
go tool pprof http://localhost:6060/debug/pprof/goroutine

# Generate flame graph
go tool pprof -http=:8080 http://localhost:6060/debug/pprof/profile?seconds=30
```

### Execution Tracing

Projects **SHOULD** use `go tool trace` for detailed execution analysis:

```go
// internal/api/handler/trace.go
package handler

import (
	"net/http"
	"os"
	"runtime/trace"
	"time"

	"github.com/gin-gonic/gin"
)

func StartTrace(c *gin.Context) {
	f, err := os.Create("trace.out")
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to create trace file"})
		return
	}

	if err := trace.Start(f); err != nil {
		f.Close()
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to start trace"})
		return
	}

	// Trace for 5 seconds
	go func() {
		time.Sleep(5 * time.Second)
		trace.Stop()
		f.Close()
	}()

	c.JSON(http.StatusOK, gin.H{"message": "trace started for 5 seconds"})
}
```

```bash
# Analyze trace
go tool trace trace.out
```

### Prometheus Metrics

Projects **MUST** expose Prometheus metrics[^12] for production monitoring:

```go
// internal/metrics/prometheus.go
package metrics

import (
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

var (
	HTTPRequestsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "http_requests_total",
			Help: "Total number of HTTP requests",
		},
		[]string{"method", "path", "status"},
	)

	HTTPRequestDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "http_request_duration_seconds",
			Help:    "HTTP request duration in seconds",
			Buckets: prometheus.DefBuckets,
		},
		[]string{"method", "path"},
	)

	ActiveConnections = promauto.NewGauge(
		prometheus.GaugeOpts{
			Name: "http_active_connections",
			Help: "Number of active HTTP connections",
		},
	)

	DatabaseQueryDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "database_query_duration_seconds",
			Help:    "Database query duration in seconds",
			Buckets: []float64{.001, .005, .01, .025, .05, .1, .25, .5, 1},
		},
		[]string{"query_type"},
	)
)
```

```go
// internal/api/middleware/prometheus.go
package middleware

import (
	"strconv"
	"time"

	"myapp/internal/metrics"

	"github.com/gin-gonic/gin"
)

// PrometheusMetrics records HTTP metrics for Prometheus
func PrometheusMetrics() gin.HandlerFunc {
	return func(c *gin.Context) {
		start := time.Now()
		path := c.FullPath() // Use route pattern, not actual path
		if path == "" {
			path = "unknown"
		}

		metrics.ActiveConnections.Inc()
		defer metrics.ActiveConnections.Dec()

		c.Next()

		duration := time.Since(start).Seconds()
		status := strconv.Itoa(c.Writer.Status())

		metrics.HTTPRequestsTotal.WithLabelValues(c.Request.Method, path, status).Inc()
		metrics.HTTPRequestDuration.WithLabelValues(c.Request.Method, path).Observe(duration)
	}
}
```

```go
// Router setup with Prometheus endpoint
import "github.com/prometheus/client_golang/prometheus/promhttp"

func NewRouter(cfg *config.Config) *gin.Engine {
	r := gin.New()
	r.Use(gin.Recovery())
	r.Use(middleware.PrometheusMetrics())

	// Prometheus metrics endpoint
	r.GET("/metrics", gin.WrapH(promhttp.Handler()))

	// ... other routes
	return r
}
```

**Why**: Prometheus is the industry standard for metrics collection in cloud-native applications.
Combined with pprof, it provides complete observability for performance debugging and capacity
planning.

## Background Jobs

Projects **SHOULD** use Asynq[^13] for Redis-backed background job processing.

### Why

Asynq provides reliable task queuing with at-least-once execution guarantees, automatic retries,
priority queues, scheduled tasks, and a web UI for monitoring. It outperforms alternatives like
Machinery in resource efficiency while providing comprehensive production features.

```go
// internal/worker/tasks.go
package worker

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"
	"time"

	"github.com/hibiken/asynq"
)

const (
	TypeEmailWelcome     = "email:welcome"
	TypeReportGenerate   = "report:generate"
	TypeNotificationPush = "notification:push"
)

// Task payloads
type EmailWelcomePayload struct {
	UserID int64  `json:"user_id"`
	Email  string `json:"email"`
	Name   string `json:"name"`
}

type ReportGeneratePayload struct {
	ReportID  int64     `json:"report_id"`
	UserID    int64     `json:"user_id"`
	StartDate time.Time `json:"start_date"`
	EndDate   time.Time `json:"end_date"`
}

// NewEmailWelcomeTask creates a welcome email task
func NewEmailWelcomeTask(userID int64, email, name string) (*asynq.Task, error) {
	payload, err := json.Marshal(EmailWelcomePayload{
		UserID: userID,
		Email:  email,
		Name:   name,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to marshal payload: %w", err)
	}

	return asynq.NewTask(
		TypeEmailWelcome,
		payload,
		asynq.MaxRetry(3),
		asynq.Timeout(30*time.Second),
		asynq.Queue("emails"),
	), nil
}

// NewReportGenerateTask creates a report generation task
func NewReportGenerateTask(reportID, userID int64, startDate, endDate time.Time) (*asynq.Task, error) {
	payload, err := json.Marshal(ReportGeneratePayload{
		ReportID:  reportID,
		UserID:    userID,
		StartDate: startDate,
		EndDate:   endDate,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to marshal payload: %w", err)
	}

	return asynq.NewTask(
		TypeReportGenerate,
		payload,
		asynq.MaxRetry(2),
		asynq.Timeout(5*time.Minute),
		asynq.Queue("reports"),
	), nil
}
```

```go
// internal/worker/handlers.go
package worker

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"

	"github.com/hibiken/asynq"
)

type TaskHandlers struct {
	emailService  EmailService
	reportService ReportService
}

func NewTaskHandlers(emailSvc EmailService, reportSvc ReportService) *TaskHandlers {
	return &TaskHandlers{
		emailService:  emailSvc,
		reportService: reportSvc,
	}
}

func (h *TaskHandlers) HandleEmailWelcome(ctx context.Context, t *asynq.Task) error {
	var payload EmailWelcomePayload
	if err := json.Unmarshal(t.Payload(), &payload); err != nil {
		return fmt.Errorf("failed to unmarshal payload: %w", err)
	}

	slog.InfoContext(ctx, "sending welcome email",
		"user_id", payload.UserID,
		"email", payload.Email,
	)

	if err := h.emailService.SendWelcome(ctx, payload.Email, payload.Name); err != nil {
		return fmt.Errorf("failed to send email: %w", err)
	}

	return nil
}

func (h *TaskHandlers) HandleReportGenerate(ctx context.Context, t *asynq.Task) error {
	var payload ReportGeneratePayload
	if err := json.Unmarshal(t.Payload(), &payload); err != nil {
		return fmt.Errorf("failed to unmarshal payload: %w", err)
	}

	slog.InfoContext(ctx, "generating report",
		"report_id", payload.ReportID,
		"user_id", payload.UserID,
	)

	if err := h.reportService.Generate(ctx, payload.ReportID, payload.StartDate, payload.EndDate); err != nil {
		return fmt.Errorf("failed to generate report: %w", err)
	}

	return nil
}
```

```go
// cmd/worker/main.go
package main

import (
	"log"
	"log/slog"

	"myapp/internal/config"
	"myapp/internal/worker"

	"github.com/hibiken/asynq"
)

func main() {
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("failed to load config: %v", err)
	}

	// Initialize services
	handlers := worker.NewTaskHandlers(emailService, reportService)

	srv := asynq.NewServer(
		asynq.RedisClientOpt{Addr: cfg.RedisAddr},
		asynq.Config{
			Concurrency: 10,
			Queues: map[string]int{
				"critical": 6, // Processed 60% of the time
				"emails":   3, // Processed 30% of the time
				"reports":  1, // Processed 10% of the time
			},
			ErrorHandler: asynq.ErrorHandlerFunc(func(ctx context.Context, task *asynq.Task, err error) {
				slog.ErrorContext(ctx, "task failed",
					"type", task.Type(),
					"error", err,
				)
			}),
		},
	)

	mux := asynq.NewServeMux()
	mux.HandleFunc(worker.TypeEmailWelcome, handlers.HandleEmailWelcome)
	mux.HandleFunc(worker.TypeReportGenerate, handlers.HandleReportGenerate)

	slog.Info("starting worker server")
	if err := srv.Run(mux); err != nil {
		log.Fatalf("worker server failed: %v", err)
	}
}
```

```go
// Enqueuing tasks from handlers
func (h *UserHandler) CreateUser(c *gin.Context) {
	// ... create user logic

	// Enqueue welcome email task
	task, err := worker.NewEmailWelcomeTask(user.ID, user.Email, user.Name)
	if err != nil {
		slog.Error("failed to create task", "error", err)
	} else {
		info, err := h.asynqClient.Enqueue(task)
		if err != nil {
			slog.Error("failed to enqueue task", "error", err)
		} else {
			slog.Info("task enqueued", "task_id", info.ID, "queue", info.Queue)
		}
	}

	c.JSON(http.StatusCreated, user)
}

// Scheduling tasks for later
func (h *ReportHandler) ScheduleReport(c *gin.Context) {
	// ... validation

	task, _ := worker.NewReportGenerateTask(reportID, userID, startDate, endDate)

	// Schedule for specific time
	info, err := h.asynqClient.Enqueue(task, asynq.ProcessAt(scheduledTime))

	// Or with delay
	info, err := h.asynqClient.Enqueue(task, asynq.ProcessIn(1*time.Hour))

	c.JSON(http.StatusAccepted, gin.H{"task_id": info.ID})
}
```

**Why**: Asynq provides the best balance of features and performance for Redis-backed task
queues. Its built-in retry logic, priority queues, and monitoring UI (Asynqmon) make it
production-ready without additional infrastructure.

## Async Patterns

Projects **MUST** use proper context propagation and cancellation for concurrent operations.

### Why

Go's concurrency primitives require careful handling to prevent goroutine leaks, race
conditions, and resource exhaustion. The `errgroup` package provides structured concurrency
with proper error propagation and cancellation.

### errgroup for Concurrent Operations

```go
// internal/service/aggregator.go
package service

import (
	"context"
	"fmt"

	"golang.org/x/sync/errgroup"
)

type AggregatorService struct {
	userRepo    UserRepository
	orderRepo   OrderRepository
	productRepo ProductRepository
}

type DashboardData struct {
	User     *User
	Orders   []*Order
	Products []*Product
}

// GetDashboardData fetches data from multiple sources concurrently
func (s *AggregatorService) GetDashboardData(ctx context.Context, userID int64) (*DashboardData, error) {
	g, ctx := errgroup.WithContext(ctx)

	var data DashboardData

	// Fetch user data
	g.Go(func() error {
		user, err := s.userRepo.GetByID(ctx, userID)
		if err != nil {
			return fmt.Errorf("failed to fetch user: %w", err)
		}
		data.User = user
		return nil
	})

	// Fetch orders
	g.Go(func() error {
		orders, err := s.orderRepo.GetByUserID(ctx, userID)
		if err != nil {
			return fmt.Errorf("failed to fetch orders: %w", err)
		}
		data.Orders = orders
		return nil
	})

	// Fetch products
	g.Go(func() error {
		products, err := s.productRepo.GetRecommended(ctx, userID)
		if err != nil {
			return fmt.Errorf("failed to fetch products: %w", err)
		}
		data.Products = products
		return nil
	})

	// Wait for all goroutines; first error cancels others
	if err := g.Wait(); err != nil {
		return nil, err
	}

	return &data, nil
}
```

### Bounded Concurrency with SetLimit

```go
// internal/service/batch.go
package service

import (
	"context"
	"fmt"

	"golang.org/x/sync/errgroup"
)

// ProcessBatch processes items with bounded concurrency
func (s *BatchService) ProcessBatch(ctx context.Context, items []Item) error {
	g, ctx := errgroup.WithContext(ctx)
	g.SetLimit(10) // Maximum 10 concurrent goroutines

	for _, item := range items {
		item := item // Capture loop variable
		g.Go(func() error {
			// Check context before processing
			if err := ctx.Err(); err != nil {
				return err
			}
			return s.processItem(ctx, item)
		})
	}

	return g.Wait()
}
```

### Context-Aware Long-Running Operations

```go
// internal/service/processor.go
package service

import (
	"context"
	"log/slog"
	"time"
)

// ProcessWithTimeout demonstrates context timeout handling
func (s *ProcessorService) ProcessWithTimeout(ctx context.Context, data []byte) error {
	// Create timeout context
	ctx, cancel := context.WithTimeout(ctx, 30*time.Second)
	defer cancel()

	resultCh := make(chan error, 1)

	go func() {
		resultCh <- s.doHeavyProcessing(ctx, data)
	}()

	select {
	case err := <-resultCh:
		return err
	case <-ctx.Done():
		return fmt.Errorf("processing timed out: %w", ctx.Err())
	}
}

// Worker demonstrates graceful shutdown with context
func (s *ProcessorService) Worker(ctx context.Context, jobs <-chan Job) {
	for {
		select {
		case <-ctx.Done():
			slog.Info("worker shutting down", "reason", ctx.Err())
			return
		case job, ok := <-jobs:
			if !ok {
				slog.Info("job channel closed, worker exiting")
				return
			}
			if err := s.processJob(ctx, job); err != nil {
				slog.Error("job processing failed", "job_id", job.ID, "error", err)
			}
		}
	}
}
```

### Fan-Out/Fan-In Pattern

```go
// internal/service/fanout.go
package service

import (
	"context"
	"sync"
)

// FetchAllURLs demonstrates fan-out/fan-in with proper cleanup
func (s *FetchService) FetchAllURLs(ctx context.Context, urls []string) ([]Result, error) {
	results := make(chan Result, len(urls))
	var wg sync.WaitGroup

	// Fan-out: spawn goroutines for each URL
	for _, url := range urls {
		wg.Add(1)
		go func(url string) {
			defer wg.Done()

			select {
			case <-ctx.Done():
				results <- Result{URL: url, Error: ctx.Err()}
				return
			default:
			}

			data, err := s.fetch(ctx, url)
			results <- Result{URL: url, Data: data, Error: err}
		}(url)
	}

	// Close results channel when all goroutines complete
	go func() {
		wg.Wait()
		close(results)
	}()

	// Fan-in: collect results
	var collected []Result
	for result := range results {
		collected = append(collected, result)
	}

	return collected, nil
}
```

**Why**: Proper context propagation ensures request-scoped cancellation flows through all
goroutines. Using `errgroup.WithContext` automatically cancels sibling goroutines when one
fails, preventing resource waste.

## Caching

Projects **SHOULD** implement multi-level caching using Ristretto[^14] for in-memory caching
and go-redis[^15] for distributed caching.

### Why

Multi-level caching reduces latency and database load. Ristretto provides high-performance local
caching with intelligent admission policies, while Redis enables cache sharing across
application instances.

### Ristretto In-Memory Cache

```go
// internal/cache/ristretto.go
package cache

import (
	"time"

	"github.com/dgraph-io/ristretto/v2"
)

type LocalCache struct {
	cache *ristretto.Cache[string, any]
}

func NewLocalCache() (*LocalCache, error) {
	cache, err := ristretto.NewCache(&ristretto.Config[string, any]{
		NumCounters: 1e7,     // 10M counters for admission policy
		MaxCost:     1 << 30, // 1GB maximum cache size
		BufferItems: 64,      // Keys per Get buffer
	})
	if err != nil {
		return nil, fmt.Errorf("failed to create cache: %w", err)
	}

	return &LocalCache{cache: cache}, nil
}

func (c *LocalCache) Get(key string) (any, bool) {
	return c.cache.Get(key)
}

func (c *LocalCache) Set(key string, value any, cost int64) {
	c.cache.Set(key, value, cost)
}

func (c *LocalCache) SetWithTTL(key string, value any, cost int64, ttl time.Duration) {
	c.cache.SetWithTTL(key, value, cost, ttl)
}

func (c *LocalCache) Delete(key string) {
	c.cache.Del(key)
}

func (c *LocalCache) Clear() {
	c.cache.Clear()
}

func (c *LocalCache) Close() {
	c.cache.Close()
}
```

### Redis Distributed Cache

```go
// internal/cache/redis.go
package cache

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/redis/go-redis/v9"
)

type RedisCache struct {
	client *redis.Client
}

func NewRedisCache(addr, password string, db int) *RedisCache {
	client := redis.NewClient(&redis.Options{
		Addr:         addr,
		Password:     password,
		DB:           db,
		PoolSize:     10,
		MinIdleConns: 5,
	})

	return &RedisCache{client: client}
}

func (c *RedisCache) Get(ctx context.Context, key string, dest any) error {
	data, err := c.client.Get(ctx, key).Bytes()
	if err != nil {
		if err == redis.Nil {
			return ErrCacheMiss
		}
		return fmt.Errorf("redis get failed: %w", err)
	}

	if err := json.Unmarshal(data, dest); err != nil {
		return fmt.Errorf("failed to unmarshal cache data: %w", err)
	}

	return nil
}

func (c *RedisCache) Set(ctx context.Context, key string, value any, ttl time.Duration) error {
	data, err := json.Marshal(value)
	if err != nil {
		return fmt.Errorf("failed to marshal cache data: %w", err)
	}

	if err := c.client.Set(ctx, key, data, ttl).Err(); err != nil {
		return fmt.Errorf("redis set failed: %w", err)
	}

	return nil
}

func (c *RedisCache) Delete(ctx context.Context, keys ...string) error {
	if err := c.client.Del(ctx, keys...).Err(); err != nil {
		return fmt.Errorf("redis delete failed: %w", err)
	}
	return nil
}

func (c *RedisCache) Close() error {
	return c.client.Close()
}

var ErrCacheMiss = errors.New("cache miss")
```

### Multi-Level Cache

```go
// internal/cache/multilevel.go
package cache

import (
	"context"
	"log/slog"
	"time"
)

type MultiLevelCache struct {
	local  *LocalCache
	remote *RedisCache
}

func NewMultiLevelCache(local *LocalCache, remote *RedisCache) *MultiLevelCache {
	return &MultiLevelCache{
		local:  local,
		remote: remote,
	}
}

// Get checks local cache first, then remote cache
func (c *MultiLevelCache) Get(ctx context.Context, key string, dest any) error {
	// Check local cache first (L1)
	if value, found := c.local.Get(key); found {
		// Type assert and copy to dest
		if data, ok := value.([]byte); ok {
			return json.Unmarshal(data, dest)
		}
	}

	// Check remote cache (L2)
	if err := c.remote.Get(ctx, key, dest); err != nil {
		return err
	}

	// Backfill local cache
	if data, err := json.Marshal(dest); err == nil {
		c.local.SetWithTTL(key, data, int64(len(data)), 5*time.Minute)
	}

	return nil
}

// Set writes to both cache levels
func (c *MultiLevelCache) Set(ctx context.Context, key string, value any, ttl time.Duration) error {
	data, err := json.Marshal(value)
	if err != nil {
		return err
	}

	// Set in local cache
	c.local.SetWithTTL(key, data, int64(len(data)), ttl)

	// Set in remote cache
	return c.remote.Set(ctx, key, value, ttl)
}

// Delete removes from both cache levels
func (c *MultiLevelCache) Delete(ctx context.Context, key string) error {
	c.local.Delete(key)
	return c.remote.Delete(ctx, key)
}
```

```go
// Usage in service layer
func (s *UserService) GetByID(ctx context.Context, id int64) (*User, error) {
	cacheKey := fmt.Sprintf("user:%d", id)

	// Try cache first
	var user User
	if err := s.cache.Get(ctx, cacheKey, &user); err == nil {
		return &user, nil
	}

	// Fetch from database
	dbUser, err := s.repo.GetByID(ctx, id)
	if err != nil {
		return nil, err
	}

	// Cache for future requests
	if err := s.cache.Set(ctx, cacheKey, dbUser, 15*time.Minute); err != nil {
		slog.Warn("failed to cache user", "user_id", id, "error", err)
	}

	return dbUser, nil
}
```

**Why**: Multi-level caching combines the speed of local memory access with the consistency of
distributed caching. Ristretto's admission policy ensures high-value items remain cached, while
Redis provides durability and cross-instance sharing.

## Rate Limiting

Projects **MUST** implement rate limiting for API endpoints to prevent abuse and ensure fair
resource usage.

### Why

Rate limiting protects services from abuse, prevents cascading failures, and ensures fair
access for all clients. Different strategies suit different use cases: token bucket for bursty
traffic, sliding window for smooth rate limiting.

### Tollbooth Middleware

```go
// internal/api/middleware/ratelimit.go
package middleware

import (
	"net/http"
	"time"

	"github.com/didip/tollbooth/v8"
	"github.com/didip/tollbooth/v8/limiter"
	"github.com/gin-gonic/gin"
)

// RateLimitByIP creates a rate limiter based on client IP
func RateLimitByIP(requestsPerSecond float64) gin.HandlerFunc {
	lmt := tollbooth.NewLimiter(requestsPerSecond, &limiter.ExpirableOptions{
		DefaultExpirationTTL: time.Hour,
	})

	lmt.SetIPLookup(limiter.IPLookup{
		Name:           "X-Forwarded-For",
		IndexFromRight: 0,
	})

	lmt.SetMessage("Rate limit exceeded. Please try again later.")
	lmt.SetMessageContentType("application/json")

	return func(c *gin.Context) {
		httpError := tollbooth.LimitByRequest(lmt, c.Writer, c.Request)
		if httpError != nil {
			c.JSON(httpError.StatusCode, gin.H{
				"error":       "rate_limit_exceeded",
				"message":     httpError.Message,
				"retry_after": lmt.GetMax(),
			})
			c.Abort()
			return
		}
		c.Next()
	}
}

// RateLimitByUser creates a rate limiter based on user ID
func RateLimitByUser(requestsPerSecond float64) gin.HandlerFunc {
	lmt := tollbooth.NewLimiter(requestsPerSecond, &limiter.ExpirableOptions{
		DefaultExpirationTTL: time.Hour,
	})

	return func(c *gin.Context) {
		userID, exists := c.Get("userID")
		if !exists {
			c.Next()
			return
		}

		key := fmt.Sprintf("user:%v", userID)
		httpError := tollbooth.LimitByKeys(lmt, []string{key})
		if httpError != nil {
			c.JSON(http.StatusTooManyRequests, gin.H{
				"error":   "rate_limit_exceeded",
				"message": "Too many requests for this user",
			})
			c.Abort()
			return
		}
		c.Next()
	}
}
```

### uber-go/ratelimit for Internal Services

```go
// internal/ratelimit/leakybucket.go
package ratelimit

import (
	"go.uber.org/ratelimit"
)

type LeakyBucketLimiter struct {
	limiter ratelimit.Limiter
}

// NewLeakyBucketLimiter creates a rate limiter with smooth request distribution
func NewLeakyBucketLimiter(rps int) *LeakyBucketLimiter {
	return &LeakyBucketLimiter{
		limiter: ratelimit.New(rps),
	}
}

// Take blocks until a request can proceed
func (l *LeakyBucketLimiter) Take() {
	l.limiter.Take()
}
```

```go
// Usage for external API calls
type ExternalAPIClient struct {
	httpClient *http.Client
	limiter    *LeakyBucketLimiter
}

func (c *ExternalAPIClient) Call(ctx context.Context, endpoint string) (*Response, error) {
	// Rate limit outgoing requests
	c.limiter.Take()

	req, err := http.NewRequestWithContext(ctx, "GET", endpoint, nil)
	if err != nil {
		return nil, err
	}

	resp, err := c.httpClient.Do(req)
	// ... handle response
}
```

### Redis-Based Distributed Rate Limiting

```go
// internal/ratelimit/redis.go
package ratelimit

import (
	"context"
	"fmt"
	"time"

	"github.com/redis/go-redis/v9"
)

type RedisRateLimiter struct {
	client *redis.Client
	limit  int
	window time.Duration
}

func NewRedisRateLimiter(client *redis.Client, limit int, window time.Duration) *RedisRateLimiter {
	return &RedisRateLimiter{
		client: client,
		limit:  limit,
		window: window,
	}
}

// Allow checks if a request is allowed using sliding window
func (r *RedisRateLimiter) Allow(ctx context.Context, key string) (bool, error) {
	now := time.Now().UnixMilli()
	windowStart := now - r.window.Milliseconds()

	pipe := r.client.Pipeline()

	// Remove old entries outside the window
	pipe.ZRemRangeByScore(ctx, key, "0", fmt.Sprintf("%d", windowStart))

	// Count current entries
	countCmd := pipe.ZCard(ctx, key)

	// Add current request
	pipe.ZAdd(ctx, key, redis.Z{Score: float64(now), Member: now})

	// Set expiry on the key
	pipe.Expire(ctx, key, r.window)

	_, err := pipe.Exec(ctx)
	if err != nil {
		return false, fmt.Errorf("redis pipeline failed: %w", err)
	}

	count := countCmd.Val()
	return count < int64(r.limit), nil
}
```

```go
// Router setup with rate limiting
func NewRouter(cfg *config.Config) *gin.Engine {
	r := gin.New()
	r.Use(gin.Recovery())

	// Global rate limit: 100 requests per second per IP
	r.Use(middleware.RateLimitByIP(100))

	// Public routes with stricter limits
	auth := r.Group("/api/v1/auth")
	auth.Use(middleware.RateLimitByIP(5)) // 5 req/sec for auth endpoints
	{
		auth.POST("/login", handler.Login)
		auth.POST("/register", handler.Register)
	}

	// Protected routes with per-user limits
	api := r.Group("/api/v1")
	api.Use(middleware.JWTAuth(jwtService))
	api.Use(middleware.RateLimitByUser(50)) // 50 req/sec per user
	{
		// ... routes
	}

	return r
}
```

**Why**: Rate limiting at multiple levels (global, per-IP, per-user) provides defense in depth.
Redis-based limiting enables consistent enforcement across multiple application instances.

## Circuit Breakers

Projects **SHOULD** use sony/gobreaker[^16] for circuit breaker patterns when calling external services.

### Why

Circuit breakers prevent cascading failures by temporarily stopping requests to failing
services. This allows the failing service time to recover while maintaining system stability.

```go
// internal/circuitbreaker/breaker.go
package circuitbreaker

import (
	"fmt"
	"log/slog"
	"time"

	"github.com/sony/gobreaker/v2"
)

type CircuitBreakers struct {
	breakers map[string]*gobreaker.CircuitBreaker[any]
}

func NewCircuitBreakers() *CircuitBreakers {
	return &CircuitBreakers{
		breakers: make(map[string]*gobreaker.CircuitBreaker[any]),
	}
}

// GetBreaker returns or creates a circuit breaker for a service
func (cb *CircuitBreakers) GetBreaker(serviceName string) *gobreaker.CircuitBreaker[any] {
	if breaker, exists := cb.breakers[serviceName]; exists {
		return breaker
	}

	settings := gobreaker.Settings{
		Name:        serviceName,
		MaxRequests: 3,                // Requests allowed in half-open state
		Interval:    60 * time.Second, // Interval to clear counts in closed state
		Timeout:     30 * time.Second, // Time in open state before half-open

		ReadyToTrip: func(counts gobreaker.Counts) bool {
			// Trip when failure ratio exceeds 60% with at least 5 requests
			failureRatio := float64(counts.TotalFailures) / float64(counts.Requests)
			return counts.Requests >= 5 && failureRatio >= 0.6
		},

		OnStateChange: func(name string, from gobreaker.State, to gobreaker.State) {
			slog.Warn("circuit breaker state change",
				"service", name,
				"from", from.String(),
				"to", to.String(),
			)
		},

		IsSuccessful: func(err error) bool {
			// Consider certain errors as non-failures
			if err == nil {
				return true
			}
			// Don't count client errors (4xx) as failures
			var httpErr *HTTPError
			if errors.As(err, &httpErr) && httpErr.StatusCode >= 400 && httpErr.StatusCode < 500 {
				return true
			}
			return false
		},
	}

	breaker := gobreaker.NewCircuitBreaker[any](settings)
	cb.breakers[serviceName] = breaker
	return breaker
}
```

```go
// internal/client/external.go
package client

import (
	"context"
	"fmt"
	"io"
	"net/http"

	"myapp/internal/circuitbreaker"

	"github.com/sony/gobreaker/v2"
)

type ExternalServiceClient struct {
	httpClient      *http.Client
	baseURL         string
	circuitBreakers *circuitbreaker.CircuitBreakers
}

func NewExternalServiceClient(baseURL string, cbs *circuitbreaker.CircuitBreakers) *ExternalServiceClient {
	return &ExternalServiceClient{
		httpClient: &http.Client{
			Timeout: 10 * time.Second,
		},
		baseURL:         baseURL,
		circuitBreakers: cbs,
	}
}

// GetData fetches data with circuit breaker protection
func (c *ExternalServiceClient) GetData(ctx context.Context, endpoint string) ([]byte, error) {
	breaker := c.circuitBreakers.GetBreaker("external-service")

	result, err := breaker.Execute(func() (any, error) {
		req, err := http.NewRequestWithContext(ctx, "GET", c.baseURL+endpoint, nil)
		if err != nil {
			return nil, fmt.Errorf("failed to create request: %w", err)
		}

		resp, err := c.httpClient.Do(req)
		if err != nil {
			return nil, fmt.Errorf("request failed: %w", err)
		}
		defer resp.Body.Close()

		if resp.StatusCode >= 500 {
			return nil, &HTTPError{StatusCode: resp.StatusCode, Message: "server error"}
		}

		body, err := io.ReadAll(resp.Body)
		if err != nil {
			return nil, fmt.Errorf("failed to read response: %w", err)
		}

		return body, nil
	})

	if err != nil {
		if err == gobreaker.ErrOpenState {
			return nil, fmt.Errorf("service unavailable: circuit breaker is open")
		}
		return nil, err
	}

	return result.([]byte), nil
}

type HTTPError struct {
	StatusCode int
	Message    string
}

func (e *HTTPError) Error() string {
	return fmt.Sprintf("HTTP %d: %s", e.StatusCode, e.Message)
}
```

```go
// Usage with fallback
func (s *ProductService) GetExternalProductData(ctx context.Context, productID string) (*ProductData, error) {
	data, err := s.externalClient.GetData(ctx, "/products/"+productID)
	if err != nil {
		slog.Warn("external service call failed, using fallback",
			"product_id", productID,
			"error", err,
		)
		// Return cached/default data as fallback
		return s.getCachedProductData(ctx, productID)
	}

	var product ProductData
	if err := json.Unmarshal(data, &product); err != nil {
		return nil, fmt.Errorf("failed to parse product data: %w", err)
	}

	return &product, nil
}
```

**Why**: Circuit breakers implement the fail-fast pattern, preventing threads from blocking on
failing services. The half-open state allows automatic recovery detection without manual
intervention.

## Feature Flags

Projects **SHOULD** use Unleash[^17] for feature flag management in production environments.

### Why

Feature flags enable progressive rollouts, A/B testing, and quick rollbacks without
deployments. Unleash provides a centralized feature management platform with SDKs for multiple
languages.

```go
// internal/featureflags/unleash.go
package featureflags

import (
	"context"
	"log/slog"

	"github.com/Unleash/unleash-go-sdk/v5"
)

type FeatureFlags struct {
	client *unleash.Client
}

func NewFeatureFlags(apiURL, apiToken, appName string) (*FeatureFlags, error) {
	err := unleash.Initialize(
		unleash.WithUrl(apiURL),
		unleash.WithCustomHeaders(map[string]string{
			"Authorization": apiToken,
		}),
		unleash.WithAppName(appName),
		unleash.WithListener(&UnleashListener{}),
	)
	if err != nil {
		return nil, fmt.Errorf("failed to initialize unleash: %w", err)
	}

	return &FeatureFlags{}, nil
}

// IsEnabled checks if a feature is enabled
func (f *FeatureFlags) IsEnabled(featureName string) bool {
	return unleash.IsEnabled(featureName)
}

// IsEnabledForUser checks if a feature is enabled for a specific user
func (f *FeatureFlags) IsEnabledForUser(featureName string, userID string, sessionID string) bool {
	ctx := unleash.WithContext(context.Background(), unleash.Context{
		UserId:    userID,
		SessionId: sessionID,
	})
	return unleash.IsEnabled(featureName, unleash.WithContext(ctx))
}

// GetVariant gets the feature variant for A/B testing
func (f *FeatureFlags) GetVariant(featureName string, userID string) *unleash.Variant {
	ctx := unleash.WithContext(context.Background(), unleash.Context{
		UserId: userID,
	})
	return unleash.GetVariant(featureName, unleash.WithContext(ctx))
}

func (f *FeatureFlags) Close() {
	unleash.Close()
}

type UnleashListener struct{}

func (l *UnleashListener) OnError(err error) {
	slog.Error("unleash error", "error", err)
}

func (l *UnleashListener) OnWarning(warning error) {
	slog.Warn("unleash warning", "warning", warning)
}

func (l *UnleashListener) OnReady() {
	slog.Info("unleash client ready")
}

func (l *UnleashListener) OnCount(name string, enabled bool) {}
func (l *UnleashListener) OnSent(payload interface{})        {}
func (l *UnleashListener) OnRegistered(payload interface{})  {}
```

```go
// internal/api/middleware/featureflags.go
package middleware

import (
	"myapp/internal/featureflags"

	"github.com/gin-gonic/gin"
)

// FeatureFlagMiddleware injects feature flag context into requests
func FeatureFlagMiddleware(ff *featureflags.FeatureFlags) gin.HandlerFunc {
	return func(c *gin.Context) {
		c.Set("featureFlags", ff)
		c.Next()
	}
}

// RequireFeature blocks requests if a feature is not enabled
func RequireFeature(ff *featureflags.FeatureFlags, featureName string) gin.HandlerFunc {
	return func(c *gin.Context) {
		userID, _ := c.Get("userID")
		userIDStr := fmt.Sprintf("%v", userID)

		if !ff.IsEnabledForUser(featureName, userIDStr, c.GetHeader("X-Session-ID")) {
			c.JSON(http.StatusNotFound, gin.H{"error": "endpoint not found"})
			c.Abort()
			return
		}
		c.Next()
	}
}
```

```go
// Usage in handlers
func (h *ProductHandler) GetRecommendations(c *gin.Context) {
	ff := c.MustGet("featureFlags").(*featureflags.FeatureFlags)
	userID := c.GetString("userID")

	var recommendations []Product

	if ff.IsEnabledForUser("new-recommendation-algorithm", userID, "") {
		// Use new algorithm
		recommendations = h.recommendationService.GetRecommendationsV2(c.Request.Context(), userID)
	} else {
		// Use existing algorithm
		recommendations = h.recommendationService.GetRecommendations(c.Request.Context(), userID)
	}

	c.JSON(http.StatusOK, recommendations)
}

// A/B testing with variants
func (h *CheckoutHandler) GetCheckoutPage(c *gin.Context) {
	ff := c.MustGet("featureFlags").(*featureflags.FeatureFlags)
	userID := c.GetString("userID")

	variant := ff.GetVariant("checkout-redesign", userID)

	switch variant.Name {
	case "variant-a":
		c.JSON(http.StatusOK, gin.H{"template": "checkout-v2a"})
	case "variant-b":
		c.JSON(http.StatusOK, gin.H{"template": "checkout-v2b"})
	default:
		c.JSON(http.StatusOK, gin.H{"template": "checkout-v1"})
	}
}
```

### Simple Local Feature Flags

For simpler needs, projects **MAY** implement local feature flags:

```go
// internal/featureflags/local.go
package featureflags

import (
	"os"
	"strconv"
	"strings"
	"sync"
)

type LocalFeatureFlags struct {
	flags map[string]bool
	mu    sync.RWMutex
}

func NewLocalFeatureFlags() *LocalFeatureFlags {
	ff := &LocalFeatureFlags{
		flags: make(map[string]bool),
	}
	ff.loadFromEnv()
	return ff
}

func (f *LocalFeatureFlags) loadFromEnv() {
	// Load from FEATURE_FLAGS env var: "flag1=true,flag2=false"
	envFlags := os.Getenv("FEATURE_FLAGS")
	if envFlags == "" {
		return
	}

	for _, pair := range strings.Split(envFlags, ",") {
		parts := strings.SplitN(pair, "=", 2)
		if len(parts) == 2 {
			enabled, _ := strconv.ParseBool(parts[1])
			f.flags[parts[0]] = enabled
		}
	}
}

func (f *LocalFeatureFlags) IsEnabled(name string) bool {
	f.mu.RLock()
	defer f.mu.RUnlock()
	return f.flags[name]
}

func (f *LocalFeatureFlags) SetEnabled(name string, enabled bool) {
	f.mu.Lock()
	defer f.mu.Unlock()
	f.flags[name] = enabled
}
```

**Why**: Feature flags enable trunk-based development and reduce deployment risk. Unleash
provides enterprise features like gradual rollouts, user targeting, and metrics. For simpler
needs, environment-based flags provide a low-overhead alternative.

## Graceful Shutdown

Projects **MUST** implement graceful shutdown to handle in-flight requests during deployments.

### Why Graceful Shutdown

- **Zero downtime deployments**: Complete in-flight requests before terminating
- **Data integrity**: Allow database transactions to complete
- **Connection cleanup**: Properly close database connections and external resources
- **Kubernetes readiness**: Required for proper pod lifecycle management

### Basic Graceful Shutdown

```go
// cmd/server/main.go
package main

import (
	"context"
	"errors"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"myapp/internal/api/router"
	"myapp/internal/config"
)

func main() {
	cfg, err := config.Load()
	if err != nil {
		slog.Error("failed to load config", "error", err)
		os.Exit(1)
	}

	r := router.NewRouter(cfg)

	srv := &http.Server{
		Addr:         cfg.ServerAddress,
		Handler:      r,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	// Start server in goroutine
	go func() {
		slog.Info("server starting", "addr", cfg.ServerAddress)
		if err := srv.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			slog.Error("server failed", "error", err)
			os.Exit(1)
		}
	}()

	// Wait for interrupt signal
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	slog.Info("shutdown signal received, starting graceful shutdown")

	// Create context with timeout for shutdown
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		slog.Error("forced shutdown", "error", err)
		os.Exit(1)
	}

	slog.Info("server shutdown complete")
}
```

### Shutdown with Resource Cleanup

```go
// cmd/server/main.go
package main

import (
	"context"
	"errors"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"
)

func main() {
	cfg, err := config.Load()
	if err != nil {
		slog.Error("failed to load config", "error", err)
		os.Exit(1)
	}

	// Initialize resources
	db, err := initDatabase(cfg)
	if err != nil {
		slog.Error("failed to init database", "error", err)
		os.Exit(1)
	}

	cache, err := initCache(cfg)
	if err != nil {
		slog.Error("failed to init cache", "error", err)
		os.Exit(1)
	}

	r := router.NewRouter(cfg, db, cache)

	srv := &http.Server{
		Addr:    cfg.ServerAddress,
		Handler: r,
	}

	// Start server
	go func() {
		if err := srv.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			slog.Error("server failed", "error", err)
		}
	}()

	// Wait for shutdown signal
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	slog.Info("starting graceful shutdown")

	// Shutdown server first (stops accepting new requests)
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	var wg sync.WaitGroup

	// Shutdown HTTP server
	wg.Add(1)
	go func() {
		defer wg.Done()
		if err := srv.Shutdown(ctx); err != nil {
			slog.Error("server shutdown failed", "error", err)
		}
		slog.Info("http server shutdown complete")
	}()

	// Wait for server shutdown
	wg.Wait()

	// Close resources after server is done
	slog.Info("closing database connections")
	if err := db.Close(); err != nil {
		slog.Error("database close failed", "error", err)
	}

	slog.Info("closing cache connections")
	cache.Close()

	slog.Info("shutdown complete")
}
```

### Kubernetes Health Probes

```go
// internal/api/handler/health.go
package handler

import (
	"net/http"
	"sync/atomic"

	"github.com/gin-gonic/gin"
)

type HealthHandler struct {
	ready    atomic.Bool
	shutdown atomic.Bool
	db       *sql.DB
}

func NewHealthHandler(db *sql.DB) *HealthHandler {
	h := &HealthHandler{db: db}
	h.ready.Store(true)
	return h
}

// StartShutdown marks the service as not ready
func (h *HealthHandler) StartShutdown() {
	h.ready.Store(false)
	h.shutdown.Store(true)
}

// Liveness checks if the process is alive
func (h *HealthHandler) Liveness(c *gin.Context) {
	if h.shutdown.Load() {
		c.Status(http.StatusServiceUnavailable)
		return
	}
	c.JSON(http.StatusOK, gin.H{"status": "alive"})
}

// Readiness checks if the service can handle requests
func (h *HealthHandler) Readiness(c *gin.Context) {
	if !h.ready.Load() {
		c.JSON(http.StatusServiceUnavailable, gin.H{
			"status": "not ready",
			"reason": "shutdown in progress",
		})
		return
	}

	// Check database connectivity
	if err := h.db.Ping(); err != nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{
			"status": "not ready",
			"reason": "database unavailable",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "ready"})
}
```

```go
// cmd/server/main.go integration
func main() {
	// ... setup code ...

	healthHandler := handler.NewHealthHandler(db)

	r := router.NewRouter(cfg, db, cache)
	r.GET("/health/live", healthHandler.Liveness)
	r.GET("/health/ready", healthHandler.Readiness)

	// ... server setup ...

	// On shutdown signal
	<-quit

	// Mark as not ready immediately (stops k8s from sending traffic)
	healthHandler.StartShutdown()

	// Wait for k8s to update endpoints (terminationGracePeriodSeconds)
	time.Sleep(5 * time.Second)

	// Then shutdown server
	ctx, cancel := context.WithTimeout(context.Background(), 25*time.Second)
	defer cancel()
	srv.Shutdown(ctx)
}
```

**Why**: Graceful shutdown ensures zero-downtime deployments by completing in-flight requests
before terminating. The readiness probe integration ensures load balancers stop sending new
traffic before the server shuts down.

## Middleware Chaining

Projects **SHOULD** understand middleware execution order and use composition for complex
middleware scenarios.

### Middleware Execution Order

Gin middleware executes in the order they are added. Use `c.Next()` to pass control to the next middleware:

```go
// internal/api/middleware/example.go
package middleware

import (
	"log/slog"
	"time"

	"github.com/gin-gonic/gin"
)

func Middleware1() gin.HandlerFunc {
	return func(c *gin.Context) {
		slog.Info("Middleware1: before") // 1. First
		c.Next()                          // Pass to next
		slog.Info("Middleware1: after")  // 6. Last
	}
}

func Middleware2() gin.HandlerFunc {
	return func(c *gin.Context) {
		slog.Info("Middleware2: before") // 2. Second
		c.Next()                          // Pass to next
		slog.Info("Middleware2: after")  // 5. Fifth
	}
}

func Handler(c *gin.Context) {
	slog.Info("Handler")               // 3. Third
	c.JSON(200, gin.H{"ok": true})     // 4. Fourth
}

// Output order:
// Middleware1: before
// Middleware2: before
// Handler
// Middleware2: after
// Middleware1: after
```

### Composing Multiple Middleware

```go
// internal/api/middleware/composed.go
package middleware

import (
	"github.com/gin-gonic/gin"
)

// ComposeMiddleware combines multiple middleware into one
func ComposeMiddleware(middlewares ...gin.HandlerFunc) gin.HandlerFunc {
	return func(c *gin.Context) {
		// Create handler chain
		for _, m := range middlewares {
			m(c)
			if c.IsAborted() {
				return
			}
		}
	}
}

// APIMiddleware bundles common API middleware
func APIMiddleware(cfg *config.Config) gin.HandlersChain {
	return gin.HandlersChain{
		Logger(),
		Recovery(),
		CORS(cfg),
		RequestID(),
		PrometheusMetrics(),
	}
}

// SecureMiddleware bundles security-focused middleware
func SecureMiddleware() gin.HandlersChain {
	return gin.HandlersChain{
		SecurityHeaders(),
		RateLimiter(),
		Auth(),
	}
}
```

```go
// internal/api/router/router.go
func NewRouter(cfg *config.Config) *gin.Engine {
	r := gin.New()

	// Apply bundled middleware
	r.Use(middleware.APIMiddleware(cfg)...)

	// Public routes
	public := r.Group("/api/v1")
	{
		public.POST("/auth/login", handler.Login)
	}

	// Protected routes with additional security middleware
	protected := r.Group("/api/v1")
	protected.Use(middleware.SecureMiddleware()...)
	{
		protected.GET("/users", handler.ListUsers)
	}

	return r
}
```

### Conditional Middleware

```go
// internal/api/middleware/conditional.go
package middleware

import (
	"strings"

	"github.com/gin-gonic/gin"
)

// SkipPaths returns middleware that skips specified paths
func SkipPaths(m gin.HandlerFunc, paths ...string) gin.HandlerFunc {
	return func(c *gin.Context) {
		for _, path := range paths {
			if strings.HasPrefix(c.Request.URL.Path, path) {
				c.Next()
				return
			}
		}
		m(c)
	}
}

// OnlyPaths returns middleware that only runs on specified paths
func OnlyPaths(m gin.HandlerFunc, paths ...string) gin.HandlerFunc {
	return func(c *gin.Context) {
		for _, path := range paths {
			if strings.HasPrefix(c.Request.URL.Path, path) {
				m(c)
				return
			}
		}
		c.Next()
	}
}

// ConditionalMiddleware runs middleware based on a condition
func ConditionalMiddleware(m gin.HandlerFunc, condition func(*gin.Context) bool) gin.HandlerFunc {
	return func(c *gin.Context) {
		if condition(c) {
			m(c)
		} else {
			c.Next()
		}
	}
}
```

```go
// Usage
func NewRouter(cfg *config.Config) *gin.Engine {
	r := gin.New()

	// Skip auth for health endpoints
	r.Use(middleware.SkipPaths(
		middleware.Auth(),
		"/health",
		"/api/v1/auth",
	))

	// Rate limit only API paths
	r.Use(middleware.OnlyPaths(
		middleware.RateLimiter(),
		"/api/",
	))

	// Conditional logging in non-production
	r.Use(middleware.ConditionalMiddleware(
		middleware.VerboseLogger(),
		func(c *gin.Context) bool {
			return cfg.Environment != "production"
		},
	))

	return r
}
```

### Short-Circuiting Middleware

```go
// internal/api/middleware/shortcircuit.go
package middleware

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

// MaintenanceMode short-circuits all requests when enabled
func MaintenanceMode(enabled func() bool) gin.HandlerFunc {
	return func(c *gin.Context) {
		if enabled() {
			c.JSON(http.StatusServiceUnavailable, gin.H{
				"error":   "service temporarily unavailable",
				"message": "scheduled maintenance in progress",
			})
			c.Abort() // Stops all subsequent middleware
			return
		}
		c.Next()
	}
}

// RequireHeader short-circuits if required header is missing
func RequireHeader(header string) gin.HandlerFunc {
	return func(c *gin.Context) {
		if c.GetHeader(header) == "" {
			c.JSON(http.StatusBadRequest, gin.H{
				"error": "missing required header: " + header,
			})
			c.Abort()
			return
		}
		c.Next()
	}
}
```

**Why**: Understanding middleware chaining enables proper request/response processing order,
efficient middleware composition, and conditional execution for complex routing scenarios.

## See Also

- [Go Style Guide](../languages/go.md) - Base Go conventions and tooling
- [Echo](https://echo.labstack.com/) - Alternative high-performance Go web framework
- [Fiber](https://gofiber.io/) - Express.js-inspired Go web framework

## References

[^1]: **Gin Web Framework** - High-performance HTTP web framework written in Go. Features martini-like API with 40x better performance. [https://gin-gonic.com/](https://gin-gonic.com/) | [GitHub](https://github.com/gin-gonic/gin)

[^2]: **httprouter** - High performance HTTP request router. Used as Gin's routing engine. [GitHub](https://github.com/julienschmidt/httprouter)

[^3]: **Echo** - High performance, minimalist Go web framework. Alternative to Gin with different design philosophy. [https://echo.labstack.com/](https://echo.labstack.com/) | [GitHub](https://github.com/labstack/echo)

[^4]: **Fiber** - Express.js-inspired web framework built on top of Fasthttp. Fastest HTTP engine for Go. [https://gofiber.io/](https://gofiber.io/) | [GitHub](https://github.com/gofiber/fiber)

[^5]: **swaggo/swag** - Automatically generate RESTful API documentation with Swagger 2.0 for Go. [GitHub](https://github.com/swaggo/swag)

[^6]: **go-playground/validator** - Go Struct and Field validation, including Cross Field, Cross Struct, Map, Slice and Array diving. [GitHub](https://github.com/go-playground/validator)

[^7]: **golang-jwt/jwt** - Go implementation of JSON Web Tokens (JWT). v5 is the current stable version with improved validation and security. [GitHub](https://github.com/golang-jwt/jwt) | [pkg.go.dev](https://pkg.go.dev/github.com/golang-jwt/jwt/v5)

[^8]: **golang.org/x/oauth2** - Official Go OAuth2 client library. Supports all major grant types and providers. [pkg.go.dev](https://pkg.go.dev/golang.org/x/oauth2)

[^9]: **Casbin** - Authorization library supporting ACL, RBAC, ABAC access control models. Policies stored in files or databases. [https://casbin.org/](https://casbin.org/) | [GitHub](https://github.com/casbin/casbin)

[^10]: **gorilla/websocket** - Fast, well-tested WebSocket implementation for Go. De facto standard for production WebSocket applications. [GitHub](https://github.com/gorilla/websocket)

[^11]: **coder/websocket** - Minimal and idiomatic WebSocket library for Go (formerly nhooyr.io/websocket). Features context support and WASM compilation. [GitHub](https://github.com/coder/websocket)

[^12]: **prometheus/client_golang** - Official Prometheus instrumentation library for Go applications. Provides metrics collection and exposition. [GitHub](https://github.com/prometheus/client_golang) | [Prometheus Guide](https://prometheus.io/docs/guides/go-application/)

[^13]: **Asynq** - Simple, reliable distributed task queue backed by Redis. Features retries, scheduling, priority queues, and web UI (Asynqmon). [GitHub](https://github.com/hibiken/asynq)

[^14]: **Ristretto** - High-performance, concurrent cache library for Go by Dgraph. Features LFU eviction and memory-bounded caching. [GitHub](https://github.com/dgraph-io/ristretto) | [Blog Post](https://dgraph.io/blog/post/introducing-ristretto-high-perf-go-cache/)

[^15]: **go-redis** - Type-safe Redis client for Go. Supports Redis 7+ features, clustering, and sentinel. [GitHub](https://github.com/redis/go-redis) | [pkg.go.dev](https://pkg.go.dev/github.com/redis/go-redis/v9)

[^16]: **sony/gobreaker** - Circuit Breaker implementation in Go. v2 adds generics support and distributed circuit breakers. [GitHub](https://github.com/sony/gobreaker) | [pkg.go.dev](https://pkg.go.dev/github.com/sony/gobreaker/v2)

[^17]: **Unleash** - Open-source feature management platform. Go SDK supports all activation strategies and variants. [https://www.getunleash.io/](https://www.getunleash.io/) | [GitHub](https://github.com/Unleash/unleash-client-go) | [Documentation](https://docs.getunleash.io/reference/sdks/go)
