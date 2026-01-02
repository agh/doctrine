# .cursorrules Style Guide

> [Doctrine](../../README.md) > [AI](README.md) > Cursor Rules

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

## Quick Reference

| Task | Description |
|------|-------------|
| **Create** | Add `.cursorrules` file to project root |
| **Scope** | Project-wide AI coding assistant rules |
| **Format** | Plain text, markdown-like structure |
| **Size** | 200-1000 lines recommended |
| **Update** | When project conventions change |
| **Priority** | Lower precedence than AGENTS.md |

## What is .cursorrules

### Definition

`.cursorrules` is a configuration file used by Cursor[^1], the AI-first code editor, to provide
context-specific instructions to its integrated language models. The file **MUST** be placed
in the project root directory and contains rules, conventions, and preferences that guide
AI-assisted code generation, refactoring, and debugging.

### Purpose

`.cursorrules` serves three primary functions:

1. **Code Generation Guidance**: Instructs AI models on preferred patterns, libraries, and idioms
2. **Style Enforcement**: Defines formatting, naming, and structural conventions
3. **Context Provision**: Supplies project-specific knowledge that AI models lack

### When to Use

Projects **SHOULD** include a `.cursorrules` file when:

- Team has established coding conventions beyond what linters enforce
- Project uses domain-specific terminology or patterns
- Codebase has architectural decisions that AI should respect
- Framework or library usage follows non-standard patterns
- Testing strategies require specific approaches

Projects **MAY** omit `.cursorrules` when:

- Codebase strictly follows well-known style guides (e.g., Google[^2], Airbnb[^3])
- Project is small (< 1000 lines) with straightforward structure
- Team relies exclusively on AGENTS.md for AI instructions

### Relationship to AGENTS.md

`.cursorrules` and `AGENTS.md` serve complementary but distinct purposes:

| Aspect | .cursorrules | AGENTS.md |
|--------|-------------|-----------|
| **Scope** | Cursor editor only | All AI assistants |
| **Audience** | Code completion, inline edits | Chat, code review, planning |
| **Length** | 200-1000 lines | 50-500 lines |
| **Detail** | Specific patterns, syntax | High-level architecture |
| **Priority** | Lower (tool-specific) | Higher (universal context) |
| **Format** | Imperative rules | Descriptive overview |

Projects **SHOULD** maintain both files:

- **AGENTS.md**: Project overview, architecture, key decisions
- **.cursorrules**: Detailed coding conventions and patterns

When instructions conflict, `AGENTS.md` takes precedence as the source of truth.

## File Structure and Format

### Location

The `.cursorrules` file **MUST** be placed in the project root directory:

```
myproject/
├── .cursorrules          # AI rules (this file)
├── AGENTS.md             # Project context (canonical)
├── CLAUDE.md             # Symlink → AGENTS.md
├── GEMINI.md             # Symlink → AGENTS.md
├── .gitignore
├── README.md
└── src/
```

### Basic Structure

A `.cursorrules` file **SHOULD** follow this structure:

```
# Project Context (optional header)

## Code Style
[Style conventions]

## Framework/Library Usage
[Preferred patterns]

## Testing
[Testing conventions]

## Architecture
[Structural rules]

## Anti-patterns
[What to avoid]
```

### Format

The file format **SHOULD** be:

- Plain text with markdown-like headings
- No strict schema or YAML/JSON structure
- Imperative voice ("Use X", "Avoid Y")
- Bullet points for lists
- Code blocks for examples

**Why**: Cursor's AI models parse natural language instructions effectively. Rigid schemas
add complexity without improving comprehension.

### Length Guidelines

| File Size | Use Case |
|-----------|----------|
| < 200 lines | Minimal projects with few conventions |
| 200-500 lines | Standard projects with established patterns |
| 500-1000 lines | Large projects with multiple languages/frameworks |
| > 1000 lines | Split into multiple files or consolidate |

Files exceeding 1000 lines **SHOULD** be refactored by:

1. Moving language-specific rules to separate files
2. Removing examples covered by linked style guides
3. Consolidating redundant instructions

## Core Sections

### 1. Code Style

The Code Style section **MUST** define formatting, naming, and structural conventions.

**Example**:

```markdown
## Code Style

### Formatting
- Use 2 spaces for indentation (TypeScript, YAML)
- Use 4 spaces for indentation (Python)
- Maximum line length: 100 characters
- Use trailing commas in multi-line structures

### Naming Conventions
- Classes: PascalCase (e.g., UserRepository)
- Functions/methods: camelCase (e.g., getUserById)
- Constants: SCREAMING_SNAKE_CASE (e.g., MAX_RETRY_COUNT)
- Files: kebab-case (e.g., user-repository.ts)

### Comments
- Use JSDoc for public APIs
- Prefer self-documenting code over inline comments
- Include TODO comments with ticket references
```

**What to Include**:

- Indentation (spaces vs tabs, width)
- Line length limits
- Naming conventions (cases for different identifier types)
- Comment style
- Import organization
- File structure

**What to Omit**:

- Rules already enforced by formatters (Prettier, Black, rustfmt)
- Language-standard conventions (e.g., Go's gofmt)

### 2. Framework and Library Usage

This section **MUST** specify preferred libraries and usage patterns.

**Example**:

```markdown
## Framework Usage

### React
- Use functional components with hooks (no class components)
- Prefer composition over HOCs
- Use TypeScript for all components
- Store component-specific styles in CSS modules

### State Management
- Use Zustand for global state (not Redux)
- Use React Query for server state
- Avoid prop drilling beyond 2 levels

### Data Fetching
- Use React Query for all API calls
- Define API client in src/lib/api.ts
- Handle loading/error states consistently
```

**What to Include**:

- Preferred libraries for common tasks
- Framework-specific patterns
- State management approach
- Data fetching conventions
- Authentication/authorization patterns

### 3. Testing

The Testing section **SHOULD** define test structure, coverage, and naming.

**Example**:

```markdown
## Testing

### Test Structure
- Place tests in __tests__ directory adjacent to source
- Use .test.ts suffix for unit tests
- Use .spec.ts suffix for integration tests

### Naming
- Describe blocks: "Component/Function name"
- It blocks: "should [expected behavior] when [condition]"

### Coverage
- Maintain minimum 80% line coverage
- 100% coverage for utility functions
- Focus on critical paths over coverage percentage

### Testing Library
- Use Vitest for unit tests
- Use Playwright for E2E tests
- Use React Testing Library for component tests
```

**What to Include**:

- Test file location and naming
- Testing libraries and frameworks
- Coverage requirements
- Test structure conventions
- Mocking strategies

### 4. Architecture

This section **SHOULD** define structural patterns and organization.

**Example**:

```markdown
## Architecture

### Directory Structure
- src/components: Reusable UI components
- src/pages: Page-level components
- src/lib: Utility functions and helpers
- src/hooks: Custom React hooks
- src/types: TypeScript type definitions

### Dependency Rules
- Pages may import from components, lib, hooks
- Components may import from lib, hooks
- Lib and hooks must not import from components/pages
- No circular dependencies

### API Design
- Use RESTful conventions
- Version APIs (e.g., /api/v1/users)
- Return consistent error shapes
```

**What to Include**:

- Directory structure
- Dependency rules
- Layered architecture constraints
- Module boundaries
- API design patterns

## Language-Specific Templates

### Python Template

Projects using Python **SHOULD** include these conventions:

```markdown
## Python Conventions

### Package Management
- Use uv for dependency management
- Pin all dependencies in pyproject.toml
- Use uv run for all commands

### Code Style
- Follow Google Python Style Guide[^2]
- Use Ruff[^4] for linting and formatting
- Type hint all function signatures
- Use Pydantic[^5] for data validation

### Testing
- Use pytest[^6] for all tests
- Place tests in tests/ directory
- Name test files test_*.py
- Use fixtures for setup/teardown
- Aim for 90%+ coverage

### Error Handling
- Use custom exceptions (inherit from Exception)
- Catch specific exceptions, not bare except
- Log errors before re-raising
- Include error context in exception messages

### Async Code
- Use asyncio for async operations
- Prefix async functions with async_
- Use httpx (not requests) for async HTTP

### Example
```python
from typing import Optional
from pydantic import BaseModel

class User(BaseModel):
    """User model with validation.

    Attributes:
        id: Unique user identifier
        email: User email address
        name: Optional user display name
    """
    id: int
    email: str
    name: Optional[str] = None

async def async_get_user(user_id: int) -> User:
    """Fetch user by ID.

    Args:
        user_id: User identifier

    Returns:
        User instance

    Raises:
        UserNotFoundError: If user doesn't exist
    """
    # Implementation
    pass
```
```

### TypeScript Template

Projects using TypeScript **SHOULD** include these conventions:

```markdown
## TypeScript Conventions

### Tooling
- Use Biome[^7] for linting and formatting
- Use tsc[^8] for type checking
- Use Vitest[^9] for testing
- Use pnpm[^10] for package management

### Type Safety
- Enable strict mode in tsconfig.json
- Avoid any type (use unknown instead)
- Prefer interfaces over type aliases for objects
- Use const assertions for literal types
- Export types alongside implementations

### Naming
- Interfaces: PascalCase without I prefix (e.g., User not IUser)
- Type aliases: PascalCase (e.g., UserId)
- Enums: PascalCase for name, SCREAMING_SNAKE_CASE for values
- Generics: Single capital letter or descriptive PascalCase

### React Patterns
- Use function declarations for components
- Props type: ComponentNameProps
- Export component and props type
- Use React.FC sparingly (prefer explicit typing)

### Error Handling
- Use Result<T, E> pattern for operations that may fail
- Throw exceptions only for exceptional circumstances
- Define error types in src/lib/errors.ts

### Example
```typescript
interface User {
  id: string;
  email: string;
  name?: string;
}

interface UserRepositoryProps {
  apiClient: ApiClient;
}

export function UserRepository({ apiClient }: UserRepositoryProps) {
  const fetchUser = async (userId: string): Promise<User> => {
    const response = await apiClient.get(`/users/${userId}`);
    return response.data;
  };

  return { fetchUser };
}
```
```

### Go Template

Projects using Go **SHOULD** include these conventions:

```markdown
## Go Conventions

### Tooling
- Use golangci-lint[^11] for linting
- Use goimports[^12] for formatting
- Use go test for testing
- Use govulncheck[^13] for security scanning

### Code Organization
- One package per directory
- Package name matches directory name
- Keep main package minimal
- Group related functionality in packages

### Naming
- Use MixedCaps, not underscores
- Acronyms: all caps (HTTP, ID, URL)
- Interface names: often single method + "er" (Reader, Writer)
- Getters: omit Get prefix (User(), not GetUser())

### Error Handling
- Return errors explicitly
- Check errors immediately
- Wrap errors with context using fmt.Errorf
- Define sentinel errors as package-level vars
- Use custom error types for structured errors

### Testing
- Place tests in same package (_test.go suffix)
- Use table-driven tests
- Name test functions TestXxx
- Use t.Helper() for test helpers
- Use testify/assert[^14] for assertions

### Concurrency
- Use channels for communication
- Use sync.Mutex for shared state
- Avoid goroutine leaks (always have exit path)
- Use context for cancellation

### Example
```go
package user

import (
    "context"
    "fmt"
)

// Repository handles user data operations.
type Repository struct {
    db Database
}

// User represents a user entity.
type User struct {
    ID    string
    Email string
    Name  string
}

// ErrUserNotFound indicates user was not found.
var ErrUserNotFound = fmt.Errorf("user not found")

// GetByID retrieves user by ID.
func (r *Repository) GetByID(ctx context.Context, id string) (*User, error) {
    user, err := r.db.QueryUser(ctx, id)
    if err != nil {
        return nil, fmt.Errorf("get user %s: %w", id, err)
    }
    if user == nil {
        return nil, ErrUserNotFound
    }
    return user, nil
}
```
```

## Framework-Specific Templates

### React + TypeScript Template

```markdown
## React + TypeScript Conventions

### Component Structure
- Use functional components exclusively
- One component per file
- Export component as default
- Export props interface as named export

### Hooks
- Custom hooks in src/hooks/
- Prefix custom hooks with "use"
- Extract complex state logic to custom hooks
- Use useMemo/useCallback for expensive computations

### Props
- Destructure props in function signature
- Use optional chaining for optional props
- Avoid spreading props unnecessarily

### State Management
- Use useState for local component state
- Use useReducer for complex state logic
- Use Zustand for global state
- Derive state when possible (don't duplicate)

### Styling
- CSS Modules for component styles
- Tailwind[^15] for utility classes
- Avoid inline styles except for dynamic values

### File Structure
```
src/
├── components/
│   ├── Button/
│   │   ├── Button.tsx
│   │   ├── Button.module.css
│   │   └── Button.test.tsx
│   └── index.ts
├── hooks/
│   ├── useAuth.ts
│   └── index.ts
├── pages/
├── lib/
└── types/
```

### Component Example
```typescript
import { useState } from 'react';
import styles from './Button.module.css';

export interface ButtonProps {
  label: string;
  onClick: () => void;
  variant?: 'primary' | 'secondary';
  disabled?: boolean;
}

export default function Button({
  label,
  onClick,
  variant = 'primary',
  disabled = false,
}: ButtonProps) {
  const [isLoading, setIsLoading] = useState(false);

  const handleClick = async () => {
    setIsLoading(true);
    try {
      await onClick();
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <button
      className={`${styles.button} ${styles[variant]}`}
      onClick={handleClick}
      disabled={disabled || isLoading}
    >
      {isLoading ? 'Loading...' : label}
    </button>
  );
}
```
```

### Django Template

```markdown
## Django Conventions

### Project Structure
- Keep apps small and focused
- Use django-admin startapp for new apps
- Place apps in apps/ directory
- Keep settings in config/ directory

### Models
- One model per logical entity
- Use Django's built-in fields
- Define __str__ method for all models
- Use Meta class for ordering, indexes
- Add help_text to fields

### Views
- Prefer class-based views
- Use Django REST Framework[^16] for APIs
- Keep business logic in models/services
- Views handle HTTP concerns only

### URLs
- One urls.py per app
- Use path() not url()
- Name all URL patterns
- Use app_name for namespacing

### Testing
- Place tests in tests/ directory within each app
- Use Django's TestCase
- Use factory_boy[^17] for test data
- Test all custom model methods
- Test API endpoints thoroughly

### Security
- Never commit SECRET_KEY
- Use environment variables for secrets
- Enable CSRF protection
- Use Django's built-in authentication
- Validate and sanitize user input

### Model Example
```python
from django.db import models
from django.contrib.auth.models import User

class Article(models.Model):
    """Article model for blog posts.

    Attributes:
        title: Article title
        content: Article body content
        author: User who created article
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """
    title = models.CharField(
        max_length=200,
        help_text="Article title (max 200 characters)"
    )
    content = models.TextField(help_text="Article body content")
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='articles'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['author', '-created_at']),
        ]

    def __str__(self) -> str:
        return f"{self.title} by {self.author.username}"
```
```

### Ruby on Rails Template

```markdown
## Rails Conventions

### Code Style
- Follow Rails conventions (CoC)
- Use StandardRB[^18] for linting
- Use Rails generators for scaffolding
- Keep controllers thin, models fat

### Models
- Use ActiveRecord validations
- Define associations explicitly
- Use scopes for common queries
- Keep business logic in models
- Use concerns for shared behavior

### Controllers
- RESTful actions only (index, show, new, create, edit, update, destroy)
- Use strong parameters
- Handle errors with rescue_from
- Render JSON with JBuilder or ActiveModel::Serializer

### Views
- Use partials for reusable components
- Use helpers for view logic
- Prefer ERB templates
- Use form_with for forms

### Testing
- Use RSpec[^19] for testing
- Use FactoryBot[^20] for test data
- Test models, controllers, and features
- Use VCR[^21] for external API tests
- Aim for 90%+ coverage

### Database
- Use migrations for schema changes
- Add indexes for foreign keys
- Use database constraints
- Never edit old migrations

### Model Example
```ruby
class Article < ApplicationRecord
  belongs_to :author, class_name: 'User'
  has_many :comments, dependent: :destroy

  validates :title, presence: true, length: { maximum: 200 }
  validates :content, presence: true

  scope :published, -> { where.not(published_at: nil) }
  scope :recent, -> { order(created_at: :desc).limit(10) }

  def published?
    published_at.present?
  end

  def publish!
    update!(published_at: Time.current)
  end
end
```

### Controller Example
```ruby
class ArticlesController < ApplicationController
  before_action :authenticate_user!, except: [:index, :show]
  before_action :set_article, only: [:show, :edit, :update, :destroy]

  def index
    @articles = Article.published.recent
  end

  def create
    @article = current_user.articles.build(article_params)

    if @article.save
      redirect_to @article, notice: 'Article created successfully.'
    else
      render :new, status: :unprocessable_entity
    end
  end

  private

  def set_article
    @article = Article.find(params[:id])
  end

  def article_params
    params.require(:article).permit(:title, :content)
  end
end
```
```

## Maintenance

### When to Update

`.cursorrules` **SHOULD** be updated when:

- New frameworks or libraries are adopted
- Team coding conventions change
- Architectural decisions are made
- Common code review feedback emerges
- Language or framework versions are upgraded

### Update Frequency

| Project Stage | Update Frequency |
|---------------|------------------|
| Active development | Monthly or as conventions evolve |
| Maintenance mode | Quarterly or when major changes occur |
| Stable/mature | Annually or when dependencies upgrade |

### Version Control

The `.cursorrules` file **MUST** be committed to version control.

**Why**: Team members and CI systems need consistent AI behavior. Versioning enables:

- Tracking convention evolution over time
- Reverting problematic rule changes
- Reviewing rule additions in pull requests
- Ensuring all developers use same conventions

### Review Process

Changes to `.cursorrules` **SHOULD** follow this process:

1. **Propose**: Create PR with rationale for changes
2. **Review**: Team reviews for accuracy and necessity
3. **Test**: Validate AI generates code matching new rules
4. **Document**: Update related AGENTS.md if needed
5. **Merge**: Require approval from tech lead or team consensus

### Keeping Rules Current

To prevent stale rules:

1. **Regular audits**: Review quarterly for outdated references
2. **Remove deprecated**: Delete rules for removed libraries/frameworks
3. **Update examples**: Ensure code examples compile and reflect current API
4. **Check links**: Verify external references remain valid
5. **Consolidate**: Merge redundant or overlapping rules

## Anti-Patterns

### 1. Over-Specification

**Don't**: Include rules already enforced by automated tools.

**Wrong**:
```markdown
## Code Style
- Use 2 spaces for indentation
- Use single quotes for strings
- Add trailing commas in multi-line objects
- Use semicolons at end of statements
```

**Right**:
```markdown
## Code Style
- Follow Prettier[^22] configuration in .prettierrc
- Prefer descriptive variable names over abbreviations
- Group imports by type (external, internal, relative)
```

**Why**: Linters and formatters handle mechanical style. `.cursorrules` should focus on
semantic patterns, architecture, and team preferences that tools can't enforce.

### 2. Excessive Length

**Don't**: Create files exceeding 1000 lines with exhaustive examples.

**Wrong**: 1500-line file covering every possible edge case.

**Right**: 400-line file with representative examples and links to full documentation.

**Why**: AI models have context limits. Lengthy files dilute important rules and slow
processing. Link to full style guides instead of duplicating them.

### 3. Vague Instructions

**Don't**: Use ambiguous or subjective language.

**Wrong**:
```markdown
- Write clean code
- Make it performant
- Keep functions small
- Use good naming
```

**Right**:
```markdown
- Functions should do one thing (Single Responsibility Principle)
- Functions exceeding 50 lines should be refactored
- Use descriptive names: getUserById not gubi
- Optimize hot paths identified by profiler, not prematurely
```

**Why**: Vague rules are unenforceable and interpreted differently by different AI models.
Specific, measurable criteria produce consistent results.

### 4. Language Mixing

**Don't**: Combine multiple language conventions in single file without clear separation.

**Wrong**:
```markdown
## Code Style
- Python: Use snake_case
- TypeScript: Use camelCase
- Go: Use MixedCaps
[rules continue to mix languages...]
```

**Right**: Either maintain language-specific sections clearly, or create separate files:
- `.cursorrules` (general project rules)
- `.cursorrules.python`
- `.cursorrules.typescript`

**Why**: Mixed conventions create confusion. Separate clearly or split into multiple files.

### 5. Outdated References

**Don't**: Reference deprecated libraries or old versions.

**Wrong**:
```markdown
## Testing
- Use Enzyme for React component testing
- Use Moment.js for dates
- Use request for HTTP calls
```

**Right**:
```markdown
## Testing
- Use React Testing Library[^23] for component testing
- Use date-fns or native Temporal API for dates
- Use fetch API or axios for HTTP calls
```

**Why**: Outdated rules guide AI toward deprecated patterns, creating technical debt.

### 6. Duplicating AGENTS.md

**Don't**: Repeat high-level project context from AGENTS.md.

**Wrong**: Including architecture overview, database schema, deployment process in both files.

**Right**:
- **AGENTS.md**: Architecture, database, deployment, team contacts
- **.cursorrules**: Coding patterns, testing conventions, style preferences

**Why**: Reduces maintenance burden and prevents conflicting information.

### 7. No Examples

**Don't**: State rules without showing code examples.

**Wrong**:
```markdown
## Error Handling
- Use custom error types
- Include context in errors
- Handle errors at appropriate level
```

**Right**:
```markdown
## Error Handling
- Use custom error types
- Include context in errors
- Handle errors at appropriate level

Example:
```typescript
class UserNotFoundError extends Error {
  constructor(userId: string) {
    super(`User not found: ${userId}`);
    this.name = 'UserNotFoundError';
  }
}

async function getUser(userId: string): Promise<User> {
  const user = await db.users.findById(userId);
  if (!user) {
    throw new UserNotFoundError(userId);
  }
  return user;
}
```
```

**Why**: Examples clarify intent and show AI exactly what patterns to generate.

### 8. Conflicting Rules

**Don't**: Include contradictory instructions.

**Wrong**:
```markdown
## Functions
- Keep functions under 20 lines
- Include comprehensive error handling in all functions
- Add detailed logging to all functions
- Document all parameters with examples
[Results in 50+ line functions]
```

**Right**:
```markdown
## Functions
- Keep functions under 30 lines including error handling
- Extract complex error handling to dedicated error handler
- Log at service boundaries, not within pure functions
- Document public API functions; internal functions use clear naming
```

**Why**: Conflicting rules confuse AI and produce inconsistent code.

## Complete Example Files

### Example 1: Next.js + TypeScript Project

```markdown
# .cursorrules - NextAuth Starter

## Project Overview
Full-stack Next.js 14 app with TypeScript, NextAuth.js, Prisma, and Tailwind CSS.

## Code Style
- Follow Prettier config (.prettierrc)
- Use Biome for linting
- 100 character line length
- Trailing commas in multi-line structures

## TypeScript
- Enable strict mode
- Avoid `any` (use `unknown` if type truly unknown)
- Export types with implementations
- Use interfaces for object shapes, type for unions/intersections

## Next.js Patterns

### App Router
- Use app directory structure (not pages)
- Server Components by default
- Add "use client" only when needed (interactivity, hooks, browser APIs)
- Use Server Actions[^24] for mutations

### File Structure
```
app/
├── (auth)/
│   ├── login/
│   │   └── page.tsx
│   └── layout.tsx
├── (dashboard)/
│   ├── dashboard/
│   │   └── page.tsx
│   └── layout.tsx
├── api/
│   └── auth/
│       └── [...nextauth]/
│           └── route.ts
└── layout.tsx
components/
├── ui/              # Shadcn components
└── features/        # Feature-specific components
lib/
├── auth.ts          # NextAuth config
├── db.ts            # Prisma client
└── utils.ts         # Utilities
```

### Data Fetching
- Fetch in Server Components when possible
- Use React Query[^25] for client-side fetching
- Implement loading.tsx and error.tsx in route segments
- Use Suspense boundaries for async components

## Database (Prisma)

### Schema
- Use camelCase for model names
- Add createdAt and updatedAt to all models
- Use @db.VarChar for limited strings
- Index foreign keys and frequently queried fields[^26]

### Client Usage
- Import from lib/db.ts (singleton pattern)
- Use transactions for multi-step operations
- Handle unique constraint violations explicitly

Example:
```typescript
import { db } from '@/lib/db';

export async function getUser(id: string) {
  const user = await db.user.findUnique({
    where: { id },
    include: { posts: true },
  });

  if (!user) {
    throw new Error(`User ${id} not found`);
  }

  return user;
}
```

## Authentication (NextAuth.js)

### Session Management
- Use JWT strategy for sessions[^27]
- Store minimal data in token (id, email, role)
- Fetch fresh user data on protected routes
- Use middleware.ts for route protection

### Protected Routes
```typescript
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';
import { redirect } from 'next/navigation';

export default async function ProtectedPage() {
  const session = await getServerSession(authOptions);

  if (!session) {
    redirect('/login');
  }

  return <div>Protected content</div>;
}
```

## Components

### Naming
- PascalCase for component files and functions
- Suffix with component type: Button.tsx, UserCard.tsx
- Group related components in directories

### Props
- Define interface named ComponentNameProps
- Export props interface
- Destructure in function signature

### Styling
- Use Tailwind[^15] utility classes
- Extract repeated patterns to components
- Use CVA (class-variance-authority)[^28] for variants

Example:
```typescript
import { cva, type VariantProps } from 'class-variance-authority';

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-md font-medium',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground hover:bg-primary/90',
        destructive: 'bg-destructive text-destructive-foreground',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-9 px-3',
        lg: 'h-11 px-8',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export function Button({ className, variant, size, ...props }: ButtonProps) {
  return (
    <button
      className={buttonVariants({ variant, size, className })}
      {...props}
    />
  );
}
```

## Testing

### Unit Tests (Vitest)
- Place tests in __tests__ directory or .test.tsx files
- Test component behavior, not implementation
- Use React Testing Library[^23]
- Mock external dependencies

### E2E Tests (Playwright)
- Place in e2e/ directory
- Test critical user flows[^29]
- Use test data factory
- Clean up test data after runs

## Environment Variables
- Define all vars in .env.example
- Never commit .env to git
- Validate env vars at startup (t3-env pattern)
- Use NEXT_PUBLIC_ prefix only for client-exposed vars

## Anti-Patterns to Avoid
- Don't use getServerSideProps (use Server Components)
- Don't fetch in Client Components unless necessary
- Don't use CSS-in-JS (use Tailwind)
- Don't put business logic in Server Actions (use service layer)
- Don't use default exports for utilities (named exports only)
```

### Example 2: Python FastAPI Project

```markdown
# .cursorrules - FastAPI Microservice

## Project Context
FastAPI microservice with PostgreSQL, SQLAlchemy, Redis caching, and async patterns.

## Package Management
- Use uv for all dependency management
- Pin exact versions in pyproject.toml
- Run all commands with `uv run`

## Code Style
- Follow Google Python Style Guide[^2]
- Use Ruff[^4] for linting and formatting (configured in pyproject.toml)
- Type hint all function signatures
- Maximum line length: 100 characters

## Project Structure
```
src/
├── api/
│   ├── v1/
│   │   ├── endpoints/
│   │   │   ├── users.py
│   │   │   └── auth.py
│   │   └── router.py
│   └── deps.py
├── core/
│   ├── config.py
│   ├── security.py
│   └── logging.py
├── models/
│   ├── user.py
│   └── base.py
├── schemas/
│   ├── user.py
│   └── auth.py
├── services/
│   └── user_service.py
└── main.py
tests/
├── api/
├── services/
└── conftest.py
```

## FastAPI Patterns

### Routers
- One router per resource
- Use APIRouter with prefix and tags
- Define in api/v1/endpoints/
- Include in main router

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db
from schemas.user import User, UserCreate
from services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Create new user."""
    service = UserService(db)
    return await service.create_user(user_in)
```

### Dependencies
- Define reusable dependencies in api/deps.py
- Use Depends() for dependency injection
- Yield for resources needing cleanup

```python
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import async_session

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with async_session() as session:
        yield session
```

### Schemas (Pydantic)
- Use Pydantic[^5] v2 models
- Separate request/response schemas
- Use ConfigDict for ORM mode
- Add field descriptions and examples

```python
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr = Field(..., description="User email address")
    name: str = Field(..., min_length=1, max_length=100)

class UserCreate(UserBase):
    """Schema for user creation."""
    password: str = Field(..., min_length=8)

class User(UserBase):
    """Schema for user response."""
    id: int
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)
```

## Database (SQLAlchemy)

### Models
- Use declarative base[^30]
- Add __tablename__ explicitly
- Include created_at, updated_at timestamps
- Add indexes for foreign keys and query filters

```python
from sqlalchemy import Boolean, Integer, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base

class User(Base):
    """User database model."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
```

### Queries
- Use async session
- Prefer select() over query()
- Use scalars() for single model queries
- Add type hints for query results

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

async def get_user_by_email(
    db: AsyncSession,
    email: str
) -> User | None:
    """Get user by email address."""
    result = await db.execute(
        select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()
```

## Services Layer

### Pattern
- Separate business logic from routes
- One service per domain model
- Accept database session in constructor
- Return domain models or raise exceptions

```python
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from models.user import User
from schemas.user import UserCreate
from core.security import hash_password

class UserService:
    """User business logic service."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, user_in: UserCreate) -> User:
        """Create new user with hashed password."""
        # Check if user exists
        existing = await get_user_by_email(self.db, user_in.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create user
        user = User(
            email=user_in.email,
            name=user_in.name,
            hashed_password=hash_password(user_in.password)
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
```

## Error Handling

### HTTP Exceptions
- Use FastAPI's HTTPException
- Provide detailed error messages
- Use appropriate status codes
- Include error codes for client handling

```python
from fastapi import HTTPException, status

class UserNotFoundError(HTTPException):
    """User not found exception."""
    def __init__(self, user_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )
```

## Testing

### Fixtures (pytest)
- Define fixtures in conftest.py
- Use async fixtures for async code
- Provide test database
- Clean up after tests

```python
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Test client fixture."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Test database session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with AsyncSession(engine) as session:
        yield session
```

### Test Structure
- Test happy path and error cases
- Use AAA pattern (Arrange, Act, Assert)
- Mock external dependencies
- Test service layer separately from routes

```python
@pytest.mark.asyncio
async def test_create_user_success(client: AsyncClient):
    """Test successful user creation."""
    # Arrange
    user_data = {
        "email": "test@example.com",
        "name": "Test User",
        "password": "securepass123"
    }

    # Act
    response = await client.post("/api/v1/users/", json=user_data)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_data["email"]
    assert "password" not in data
```

## Async Patterns

### Use async/await
- All I/O operations must be async
- Use asyncio for concurrent operations
- Use httpx (not requests) for HTTP calls
- Use aioredis for Redis operations

### Concurrency
```python
import asyncio
from typing import List

async def fetch_multiple_users(user_ids: List[int]) -> List[User]:
    """Fetch multiple users concurrently."""
    tasks = [get_user(user_id) for user_id in user_ids]
    return await asyncio.gather(*tasks)
```

## Configuration

### Settings (Pydantic Settings)
- Use pydantic-settings for config
- Load from environment variables
- Validate at startup
- Use .env for local development

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings."""
    model_config = SettingsConfigDict(env_file=".env")

    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str
    DEBUG: bool = False

settings = Settings()
```
```

These examples demonstrate comprehensive `.cursorrules` files that provide clear, actionable
guidance for AI-assisted development while avoiding common anti-patterns.

## See Also

- [AGENTS.md Guide](agents-md.md) - Project context files for AI assistants
- [Prompt Engineering Guide](prompt-engineering.md) - Effective prompting strategies
- [AI Development Overview](README.md) - When and how to use AI assistance
- [Python Style Guide](../languages/python.md) - Python conventions
- [TypeScript Style Guide](../languages/typescript.md) - TypeScript conventions
- [Testing Guide](../process/testing.md) - Testing best practices

## References

[^1]: [Cursor - The AI-first Code Editor](https://cursor.sh/)
[^2]: [Google Style Guides](https://google.github.io/styleguide/)
[^3]: [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)
[^4]: [Ruff - An extremely fast Python linter and formatter](https://docs.astral.sh/ruff/)
[^5]: [Pydantic - Data validation using Python type hints](https://docs.pydantic.dev/)
[^6]: [pytest - A mature full-featured testing framework](https://docs.pytest.org/)
[^7]: [Biome - One toolchain for your web project](https://biomejs.dev/)
[^8]: [TypeScript Compiler (tsc)](https://www.typescriptlang.org/docs/handbook/compiler-options.html)
[^9]: [Vitest - A blazing fast unit test framework](https://vitest.dev/)
[^10]: [pnpm - Fast, disk space efficient package manager](https://pnpm.io/)
[^11]: [golangci-lint - Fast Go linters runner](https://golangci-lint.run/)
[^12]: [goimports - Updates Go import lines](https://pkg.go.dev/golang.org/x/tools/cmd/goimports)
[^13]: [govulncheck - Go vulnerability scanner](https://pkg.go.dev/golang.org/x/vuln/cmd/govulncheck)
[^14]: [Testify - A toolkit with common assertions and mocks](https://github.com/stretchr/testify)
[^15]: [Tailwind CSS - A utility-first CSS framework](https://tailwindcss.com/)
[^16]: [Django REST Framework](https://www.django-rest-framework.org/)
[^17]: [factory_boy - A test fixtures replacement](https://factoryboy.readthedocs.io/)
[^18]: [StandardRB - Ruby style guide, linter, and formatter](https://github.com/standardrb/standard)
[^19]: [RSpec - Behaviour Driven Development for Ruby](https://rspec.info/)
[^20]: [FactoryBot - A library for setting up Ruby objects as test data](https://github.com/thoughtbot/factory_bot)
[^21]: [VCR - Record HTTP interactions for deterministic tests](https://github.com/vcr/vcr)
[^22]: [Prettier - Opinionated code formatter](https://prettier.io/)
[^23]: [React Testing Library - Simple and complete testing utilities](https://testing-library.com/react)
[^24]: [Next.js Server Actions](https://nextjs.org/docs/app/building-your-application/data-fetching/server-actions-and-mutations)
[^25]: [TanStack Query (React Query) - Powerful asynchronous state management](https://tanstack.com/query/)
[^26]: [Prisma - Next-generation ORM for Node.js and TypeScript](https://www.prisma.io/)
[^27]: [NextAuth.js - Authentication for Next.js](https://next-auth.js.org/)
[^28]: [CVA (class-variance-authority) - CSS-in-TS utilities](https://cva.style/docs)
[^29]: [Playwright - Fast and reliable end-to-end testing](https://playwright.dev/)
[^30]: [SQLAlchemy - The Python SQL Toolkit and ORM](https://www.sqlalchemy.org/)

