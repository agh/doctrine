---
name: test-writer-javascript
description: "Jest/Vitest, React Testing Library, TypeScript mock patterns"
model: sonnet
---

# Test Writer: JavaScript/TypeScript Module

> [Test Writer Agent](../test-writer.md) > JavaScript/TypeScript

JavaScript and TypeScript-specific guidance for test generation.

## Quick Reference

| Task | Tool | Command |
| ---- | ---- | ------- |
| Run tests | Jest | `npm test` |
| Run tests | Vitest | `npx vitest` |
| Coverage | c8/Jest | `npm test -- --coverage` |
| Watch mode | Jest/Vitest | `npm test -- --watch` |

## Framework Detection

Detect testing framework from project files:

| Indicator | Framework |
| --------- | --------- |
| `jest.config.js`, `jest` in package.json | Jest |
| `vitest.config.ts`, `vitest` in package.json | Vitest |
| `*.test.ts` with Vitest imports | Vitest |
| `*.spec.js` with Jest imports | Jest |
| No indicators | Default to Vitest (modern projects) |

## Jest Patterns

### Basic Test Structure

```typescript
import { calculateTotal } from './calculator';

describe('calculateTotal', () => {
  it('returns zero for empty array', () => {
    expect(calculateTotal([])).toBe(0);
  });

  it('returns item value for single item', () => {
    expect(calculateTotal([42])).toBe(42);
  });

  it('sums multiple items', () => {
    expect(calculateTotal([1, 2, 3])).toBe(6);
  });
});
```

### Setup and Teardown

```typescript
describe('DatabaseService', () => {
  let service: DatabaseService;
  let mockConnection: jest.Mocked<Connection>;

  beforeEach(() => {
    mockConnection = createMockConnection();
    service = new DatabaseService(mockConnection);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('connects on initialization', () => {
    expect(mockConnection.connect).toHaveBeenCalled();
  });
});
```

### Mocking

```typescript
import { fetchUser } from './api';
import axios from 'axios';

jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('fetchUser', () => {
  it('fetches user from API', async () => {
    mockedAxios.get.mockResolvedValue({
      data: { id: 1, name: 'Test User' }
    });

    const user = await fetchUser(1);

    expect(axios.get).toHaveBeenCalledWith('/api/users/1');
    expect(user.name).toBe('Test User');
  });

  it('throws on network error', async () => {
    mockedAxios.get.mockRejectedValue(new Error('Network error'));

    await expect(fetchUser(1)).rejects.toThrow('Network error');
  });
});
```

### Async Testing

```typescript
describe('async operations', () => {
  it('resolves with data', async () => {
    const result = await fetchData();
    expect(result).toBeDefined();
  });

  it('handles promise rejection', async () => {
    await expect(failingOperation()).rejects.toThrow('Expected error');
  });

  // With done callback (legacy pattern)
  it('calls callback with result', (done) => {
    fetchWithCallback((err, result) => {
      expect(err).toBeNull();
      expect(result).toBe('success');
      done();
    });
  });
});
```

## Vitest Patterns

### Basic Structure

```typescript
import { describe, it, expect, vi } from 'vitest';
import { calculateTotal } from './calculator';

describe('calculateTotal', () => {
  it('returns zero for empty array', () => {
    expect(calculateTotal([])).toBe(0);
  });
});
```

### Mocking with Vitest

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { fetchUser } from './api';

vi.mock('./http-client', () => ({
  httpClient: {
    get: vi.fn(),
  },
}));

import { httpClient } from './http-client';

describe('fetchUser', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches user from API', async () => {
    vi.mocked(httpClient.get).mockResolvedValue({ id: 1, name: 'Test' });

    const user = await fetchUser(1);

    expect(httpClient.get).toHaveBeenCalledWith('/users/1');
    expect(user.name).toBe('Test');
  });
});
```

### Snapshot Testing

```typescript
import { render } from '@testing-library/react';

describe('UserCard', () => {
  it('matches snapshot', () => {
    const { container } = render(<UserCard user={mockUser} />);
    expect(container).toMatchSnapshot();
  });

  it('matches inline snapshot', () => {
    const result = formatUserName({ first: 'John', last: 'Doe' });
    expect(result).toMatchInlineSnapshot(`"John Doe"`);
  });
});
```

## React Testing Library

```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LoginForm } from './LoginForm';

describe('LoginForm', () => {
  it('renders email and password inputs', () => {
    render(<LoginForm onSubmit={vi.fn()} />);

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
  });

  it('calls onSubmit with form data', async () => {
    const handleSubmit = vi.fn();
    const user = userEvent.setup();

    render(<LoginForm onSubmit={handleSubmit} />);

    await user.type(screen.getByLabelText(/email/i), 'test@example.com');
    await user.type(screen.getByLabelText(/password/i), 'password123');
    await user.click(screen.getByRole('button', { name: /submit/i }));

    expect(handleSubmit).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'password123',
    });
  });

  it('displays validation error for invalid email', async () => {
    const user = userEvent.setup();
    render(<LoginForm onSubmit={vi.fn()} />);

    await user.type(screen.getByLabelText(/email/i), 'invalid-email');
    await user.click(screen.getByRole('button', { name: /submit/i }));

    await waitFor(() => {
      expect(screen.getByText(/invalid email/i)).toBeInTheDocument();
    });
  });
});
```

## Coverage Commands

```bash
# Jest coverage
npm test -- --coverage --coverageReporters=lcov,text

# Vitest coverage
npx vitest --coverage

# Coverage threshold enforcement
# In jest.config.js or vitest.config.ts:
# coverageThreshold: { global: { lines: 80, branches: 70 } }
```

## Coverage Report Parsing

Parse `coverage/lcov.info`:

```text
TN:
SF:src/calculator.ts
FN:1,calculateTotal
FNDA:5,calculateTotal
FNF:1
FNH:1
DA:2,5
DA:3,5
DA:4,0    # Line 4 not covered
LF:3
LH:2
end_of_record
```

## TypeScript-Specific Patterns

### Type-Safe Mocks

```typescript
import { Mock } from 'vitest';

interface UserRepository {
  findById(id: number): Promise<User | null>;
  save(user: User): Promise<void>;
}

function createMockRepository(): jest.Mocked<UserRepository> {
  return {
    findById: vi.fn(),
    save: vi.fn(),
  };
}

describe('UserService', () => {
  it('returns null for non-existent user', async () => {
    const repo = createMockRepository();
    repo.findById.mockResolvedValue(null);

    const service = new UserService(repo);
    const result = await service.getUser(999);

    expect(result).toBeNull();
  });
});
```

### Testing Types

```typescript
import { expectTypeOf } from 'vitest';

describe('type tests', () => {
  it('returns correct type', () => {
    const result = parseConfig('{}');
    expectTypeOf(result).toEqualTypeOf<Config>();
  });
});
```

## See Also

- [JavaScript Style Guide](../../../../guides/languages/javascript.md)
- [TypeScript Style Guide](../../../../guides/languages/typescript.md)
- [Testing Guide](../../../../guides/process/testing.md)
