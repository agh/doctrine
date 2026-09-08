# React Style Guide

> [Doctrine](../../README.md) > [Frameworks](../README.md) > React

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119][rfc2119].

[rfc2119]: https://datatracker.ietf.org/doc/html/rfc2119

Extends [TypeScript style guide](../languages/typescript.md) with React-specific conventions.

**Target Version**: React 19.2.8 and React DOM 19.2.8 with TypeScript — the current stable
release as of 2026-09-08[^react-npm].

New projects **MUST** install `react@19.2.8` and `react-dom@19.2.8`. Projects already on an
older 19.x line **MUST** track the newest patch of that line. Projects that render React Server
Components **MUST** also satisfy the patch floors in
[Server Component Security](#server-component-security), which apply to the
`react-server-dom-*` packages rather than to `react` itself.

## Quick Reference

All TypeScript tooling applies. Projects **MUST** use the additional React-specific tools:

| Task | Tool | Command |
| ---- | ---- | ------- |
| Lint | Biome[^1] + React rules | `biome check .` |
| Format | Biome[^1] | `biome format --write .` |
| Type check | TypeScript[^2] | `tsc --noEmit` |
| Test | Vitest[^3] + Testing Library[^4] | `vitest` |
| Coverage | Vitest[^3] | `vitest --coverage` |
| E2E | Playwright[^5] | `playwright test` |

## Why React

React remains the most widely adopted view library for building user interfaces:

- **Component model**: Composable, reusable UI components with clear data flow
- **TypeScript integration**: First-class type support for props, state, and events
- **Server components**: React 19 enables zero-JavaScript components for improved performance
- **Ecosystem**: Largest library ecosystem with mature tooling for routing, state, forms, and testing
- **Performance**: React Compiler automatically optimizes re-renders without manual memoization
- **Backward compatibility**: Stable API with gradual upgrade path for new features

**When to use React**: Web applications requiring rich interactivity, real-time updates, or
complex state management. For static content-heavy sites, consider Astro[^6] or Next.js[^7]
with server components.

## Project Structure

Projects **SHOULD** use feature-based organization:

```text
src/
├── features/
│   ├── auth/
│   │   ├── components/
│   │   │   ├── LoginForm.tsx
│   │   │   └── LoginForm.test.tsx
│   │   ├── hooks/
│   │   │   └── useAuth.ts
│   │   ├── types.ts
│   │   └── index.ts
│   ├── orders/
│   │   ├── components/
│   │   ├── hooks/
│   │   └── api.ts
│   └── products/
├── components/          # Shared components
│   ├── Button/
│   │   ├── Button.tsx
│   │   ├── Button.test.tsx
│   │   └── index.ts
│   └── Input/
├── hooks/              # Shared hooks
│   └── useLocalStorage.ts
├── lib/                # Utilities
│   ├── api.ts
│   └── formatters.ts
├── app.tsx
└── main.tsx
```

**Why feature-based organization**: Co-locating related components, hooks, and tests improves
maintainability by keeping feature logic together. Shared components are promoted to
`/components` only when reused across features.

## Components

### Functional Components by Default

Projects **MUST** use functional components for ordinary UI. Class components are still supported
by React and are not deprecated[^react-component], but they **MUST NOT** be used for new
components — with one exception: error boundaries, which have no function-component equivalent.
See [Error Boundaries](#error-boundaries).

```tsx
// GOOD: Functional component
type ButtonProps = {
  children: React.ReactNode;
  onClick: () => void;
  variant?: 'primary' | 'secondary';
};

export function Button({ children, onClick, variant = 'primary' }: ButtonProps) {
  return (
    <button onClick={onClick} className={variant}>
      {children}
    </button>
  );
}

// BAD: Class component for ordinary UI (supported, but not recommended for new code)
class Button extends React.Component<ButtonProps> {
  render() {
    return <button onClick={this.props.onClick}>{this.props.children}</button>;
  }
}
```

**Why functional components**: Simpler syntax, better TypeScript inference, access to hooks,
and improved performance with React Compiler. Because classes are supported rather than
deprecated, existing class components **MUST NOT** be rewritten purely to satisfy this rule;
convert them when the surrounding code changes for another reason.

### Error Boundaries

Error boundaries are the sole exception to the rule above. `static getDerivedStateFromError` and
`componentDidCatch` have no function-component equivalent, so React's own guidance is to write one
`ErrorBoundary` class and reuse it, or to take that behaviour from a library[^react-component].

Applications **MUST** render at least one error boundary above the route tree and **SHOULD** add
one per route so that a failure in a single view does not blank the whole application. Every
boundary **MUST** provide a fallback UI, a reset path, and error logging.

Projects **SHOULD** satisfy this with a framework-provided boundary (for example the Next.js
`error.tsx` convention[^nextjs-error]) or with `react-error-boundary`[^react-error-boundary],
which exports the same class plus a `useErrorBoundary` hook for forwarding event-handler and
asynchronous errors to the nearest boundary:

```bash
npm install react-error-boundary@6.1.5
```

Projects that take neither **MUST** write exactly one boundary class and reuse it:

```tsx
// components/ErrorBoundary.tsx
import { Component, type ErrorInfo, type ReactNode } from 'react';

type ErrorBoundaryProps = {
  children: ReactNode;
  fallback: (error: Error, reset: () => void) => ReactNode;
  onError?: (error: Error, componentStack: string) => void;
};

type ErrorBoundaryState = {
  error: Error | null;
};

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    this.props.onError?.(error, info.componentStack ?? '');
  }

  reset = () => {
    this.setState({ error: null });
  };

  render() {
    const { error } = this.state;

    if (error) return this.props.fallback(error, this.reset);

    return this.props.children;
  }
}
```

```tsx
// GOOD: fallback, reset, and logging supplied at the boundary
function App() {
  return (
    <ErrorBoundary
      fallback={(error, reset) => <ErrorPanel message={error.message} onRetry={reset} />}
      onError={(error, componentStack) => logger.error(error, { componentStack })}
    >
      <Dashboard />
    </ErrorBoundary>
  );
}
```

**Why fallback, reset, and logging together**: A boundary without a fallback renders nothing and
looks like a crash; one without a reset traps the user until a full page reload; one without
logging silently discards the only record of the failure. `getDerivedStateFromError` **MUST**
stay pure — side effects such as reporting belong in `componentDidCatch`[^react-component].

Error boundaries do not catch errors thrown in event handlers, in the boundary itself, during
server-side rendering, or in asynchronous callbacks such as `setTimeout` — the one asynchronous
exception being the function passed to `startTransition`[^react-component]. Those paths **MUST**
be handled with ordinary `try`/`catch` and explicit error state.

### Naming Conventions

Component files **MUST** use PascalCase matching the component name:

```text
Button.tsx      (exports Button)
LoginForm.tsx   (exports LoginForm)
UserAvatar.tsx  (exports UserAvatar)
```

Component names **MUST** be PascalCase. Event handlers **MUST** be prefixed with `handle`:

```tsx
function OrderList() {
  function handleOrderClick(id: string) {
    // ...
  }

  function handleDeleteClick(id: string) {
    // ...
  }

  return (
    <ul>
      {orders.map((order) => (
        <li key={order.id} onClick={() => handleOrderClick(order.id)}>
          {order.name}
          <button onClick={() => handleDeleteClick(order.id)}>Delete</button>
        </li>
      ))}
    </ul>
  );
}
```

### Props Destructuring

Props **SHOULD** be destructured in the function signature:

```tsx
// GOOD: Destructured props
function UserProfile({ name, email, avatar }: UserProfileProps) {
  return (
    <div>
      <img src={avatar} alt={name} />
      <h1>{name}</h1>
      <p>{email}</p>
    </div>
  );
}

// ACCEPTABLE: Non-destructured when forwarding many props
function UserCard(props: UserCardProps) {
  return <UserProfile {...props} />;
}
```

## Hooks

### Rules of Hooks

Projects **MUST** follow the Rules of Hooks[^8]:

1. Only call hooks at the top level (not inside conditions, loops, or nested functions)
2. Only call hooks from React function components or custom hooks

```tsx
// GOOD: Hook at top level
function UserProfile({ userId }: { userId: string }) {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    fetchUser(userId).then(setUser);
  }, [userId]);

  if (!user) return <Loading />;
  return <div>{user.name}</div>;
}

// BAD: Hook inside condition
function UserProfile({ userId }: { userId: string }) {
  const [user, setUser] = useState<User | null>(null);

  if (userId) {
    useEffect(() => {  // WRONG: Hook in conditional
      fetchUser(userId).then(setUser);
    }, [userId]);
  }

  return <div>{user?.name}</div>;
}
```

### useState

State **MUST** be typed explicitly for complex types:

```tsx
type User = {
  id: string;
  name: string;
  email: string;
};

// GOOD: Explicit type with union for null
function UserProfile() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);  // Inferred as boolean

  // ...
}

// GOOD: State updater functions for derived updates
function Counter() {
  const [count, setCount] = useState(0);

  function handleIncrement() {
    setCount((prev) => prev + 1);  // Use updater function
  }

  return <button onClick={handleIncrement}>{count}</button>;
}
```

**Why updater functions**: When new state depends on previous state, updater functions prevent
race conditions with batched updates.

### useEffect

Effects **MUST** include all dependencies in the dependency array:

```tsx
// GOOD: Complete dependency array
function UserProfile({ userId }: { userId: string }) {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    let cancelled = false;

    fetchUser(userId).then((data) => {
      if (!cancelled) setUser(data);
    });

    return () => {
      cancelled = true;  // Cleanup to prevent state updates after unmount
    };
  }, [userId]);

  return <div>{user?.name}</div>;
}

// BAD: Missing dependency
function SearchResults({ query, filters }: SearchProps) {
  useEffect(() => {
    fetchResults(query, filters);  // filters not in deps!
  }, [query]);  // WRONG: Missing filters dependency
}
```

Effects **SHOULD** return cleanup functions when appropriate:

```tsx
function ChatRoom({ roomId }: { roomId: string }) {
  useEffect(() => {
    const socket = connectToRoom(roomId);

    return () => {
      socket.disconnect();  // Cleanup on unmount or roomId change
    };
  }, [roomId]);

  return <div>Chat room {roomId}</div>;
}
```

### Custom Hooks

Custom hooks **MUST** start with `use` prefix:

```tsx
// GOOD: Custom hook for local storage
function useLocalStorage<T>(key: string, initialValue: T) {
  const [value, setValue] = useState<T>(() => {
    const stored = localStorage.getItem(key);
    return stored ? JSON.parse(stored) : initialValue;
  });

  useEffect(() => {
    localStorage.setItem(key, JSON.stringify(value));
  }, [key, value]);

  return [value, setValue] as const;
}

// Usage
function UserSettings() {
  const [theme, setTheme] = useLocalStorage('theme', 'light');

  return (
    <button onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}>
      Toggle theme
    </button>
  );
}
```

**Why custom hooks**: Extract reusable stateful logic that can be shared across components
without prop drilling or render prop patterns.

### React 19 Hooks

React 19 introduces new hooks for form handling and optimistic updates[^react19]:

#### useActionState

Use `useActionState` for form submissions with loading and error states:

```tsx
import { useActionState } from 'react';

async function submitForm(prevState: FormState, formData: FormData) {
  const email = formData.get('email') as string;
  try {
    await subscribe(email);
    return { success: true, message: 'Subscribed!' };
  } catch (error) {
    return { success: false, message: 'Failed to subscribe' };
  }
}

function NewsletterForm() {
  const [state, formAction, isPending] = useActionState(submitForm, {
    success: false,
    message: '',
  });

  return (
    <form action={formAction}>
      <input type="email" name="email" required disabled={isPending} />
      <button type="submit" disabled={isPending}>
        {isPending ? 'Subscribing...' : 'Subscribe'}
      </button>
      {state.message && <p>{state.message}</p>}
    </form>
  );
}
```

#### useFormStatus

Use `useFormStatus` to access parent form state from child components:

```tsx
import { useFormStatus } from 'react-dom';

function SubmitButton() {
  const { pending } = useFormStatus();

  return (
    <button type="submit" disabled={pending}>
      {pending ? 'Submitting...' : 'Submit'}
    </button>
  );
}

function ContactForm() {
  return (
    <form action={submitContact}>
      <input name="message" />
      <SubmitButton />  {/* Automatically knows form state */}
    </form>
  );
}
```

#### useOptimistic

Use `useOptimistic` for instant UI feedback before server confirmation:

```tsx
import { useOptimistic } from 'react';

function TodoList({ todos }: { todos: Todo[] }) {
  const [optimisticTodos, addOptimisticTodo] = useOptimistic(
    todos,
    (state, newTodo: Todo) => [...state, { ...newTodo, pending: true }]
  );

  async function handleAdd(formData: FormData) {
    const title = formData.get('title') as string;
    const newTodo = { id: crypto.randomUUID(), title, pending: true };

    addOptimisticTodo(newTodo);  // Instant UI update
    await createTodo(title);     // Server request
  }

  return (
    <form action={handleAdd}>
      <input name="title" />
      <button type="submit">Add</button>
      <ul>
        {optimisticTodos.map((todo) => (
          <li key={todo.id} style={{ opacity: todo.pending ? 0.5 : 1 }}>
            {todo.title}
          </li>
        ))}
      </ul>
    </form>
  );
}
```

#### use API

Use `use` to read resources (promises, context) during render:

```tsx
import { use, Suspense } from 'react';

function UserProfile({ userPromise }: { userPromise: Promise<User> }) {
  const user = use(userPromise);  // Suspends until resolved

  return <div>{user.name}</div>;
}

function App() {
  const userPromise = fetchUser(userId);

  return (
    <Suspense fallback={<Loading />}>
      <UserProfile userPromise={userPromise} />
    </Suspense>
  );
}
```

Unlike hooks, `use` can be called conditionally:

```tsx
function UserDetails({ userId, showProfile }: { userId: string; showProfile: boolean }) {
  // GOOD: use() can be called conditionally (unlike useState/useEffect)
  if (showProfile) {
    const user = use(fetchUser(userId));
    return <Profile user={user} />;
  }

  return <div>Profile hidden</div>;
}
```

Use `use` with Context for cleaner context consumption:

```tsx
import { use, createContext } from 'react';

const ThemeContext = createContext<Theme | null>(null);

function ThemedButton() {
  // GOOD: use() works with context - more concise than useContext
  const theme = use(ThemeContext);

  if (!theme) throw new Error('ThemedButton must be used within ThemeProvider');

  return <button style={{ background: theme.primary }}>Click me</button>;
}

// Can also be called conditionally with context
function ConditionalTheme({ useTheme }: { useTheme: boolean }) {
  // GOOD: the context value is nullable, so the fallback is applied after the conditional read
  const contextTheme = useTheme ? use(ThemeContext) : null;
  const theme = contextTheme ?? defaultTheme;

  return <div style={{ color: theme.text }}>Content</div>;
}

// BAD: `use(ThemeContext)` returns `Theme | null`, so `theme.text` throws without a provider
function BrokenConditionalTheme({ useTheme }: { useTheme: boolean }) {
  const theme = useTheme ? use(ThemeContext) : defaultTheme;

  return <div style={{ color: theme.text }}>Content</div>;
}
```

**Why narrow before reading**: `createContext<Theme | null>(null)` makes `null` the value React
returns when no provider is mounted, so the ternary widens the result to `Theme | null` rather
than narrowing it. Either fall back explicitly, as above, or throw as `ThemedButton` does — the
choice **MUST** be deliberate rather than left to a runtime `TypeError`.

**Why React 19 hooks**: These hooks simplify form handling patterns that previously required
manual loading states, optimistic update logic, and third-party libraries.

## State Management

### When to Use Context

Context **SHOULD** be used for:

- Theme/UI state (dark mode, locale)
- User authentication state
- Feature flags
- Shared configuration

Context **SHOULD NOT** be used for:

- Frequently changing data (use external state library)
- Data that only affects 2-3 components (use prop drilling)

```tsx
// GOOD: Context for authentication
type AuthContextValue = {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  const login = async (email: string, password: string) => {
    const user = await authApi.login(email, password);
    setUser(user);
  };

  const logout = () => setUser(null);

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
```

### When to Use External State Libraries

Projects **SHOULD** use external state libraries (Zustand[^9], Jotai[^10], Redux Toolkit[^11])
when:

- State is accessed by many components at different nesting levels
- State updates frequently (multiple times per second)
- Complex state logic requires reducers or middleware
- DevTools integration is needed

```tsx
// GOOD: Zustand for shared cart state
import { create } from 'zustand';

type CartState = {
  items: CartItem[];
  addItem: (item: CartItem) => void;
  removeItem: (id: string) => void;
};

export const useCartStore = create<CartState>((set) => ({
  items: [],
  addItem: (item) => set((state) => ({ items: [...state.items, item] })),
  removeItem: (id) => set((state) => ({
    items: state.items.filter((item) => item.id !== id),
  })),
}));

// GOOD: derived values are selectors over the stored state, not fields in it
export const selectCartTotal = (state: CartState) =>
  state.items.reduce((sum, item) => sum + item.price, 0);

// Usage in any component
function CartSummary() {
  const itemCount = useCartStore((state) => state.items.length);
  const total = useCartStore(selectCartTotal);

  return <button>Cart ({itemCount}) — {formatCurrency(total)}</button>;
}
```

Derived values **MUST NOT** be declared as state fields:

```tsx
// BAD: `total` is declared as a number but initialised with a function.
// tsc rejects this with TS2322: Type '() => number' is not assignable to type 'number'.
type CartState = {
  items: CartItem[];
  total: number;
};

export const useCartStore = create<CartState>((set, get) => ({
  items: [],
  total: () => get().items.reduce((sum, item) => sum + item.price, 0),
}));
```

**Why derive rather than store**: A `total` typed as `number` has to be recomputed by every action
that touches `items`, and one missed update leaves the store internally inconsistent. Typing it as
`() => number` compiles, but then `useCartStore((state) => state.total)` selects a stable function
reference: the component never re-renders when `items` changes, so it keeps displaying the
previous total even though calling `total()` would return the new one. A selector is recomputed
from `items` and re-subscribes on every change, so it cannot drift.

**Why Zustand**: Minimal boilerplate, TypeScript-first API, no providers needed, excellent
performance with automatic re-render optimization.

## TypeScript Patterns

### Typing Props

Props **MUST** be typed with explicit type aliases:

```tsx
// GOOD: Explicit type alias
type ButtonProps = {
  children: React.ReactNode;
  onClick: () => void;
  variant?: 'primary' | 'secondary' | 'danger';
  disabled?: boolean;
};

export function Button({ children, onClick, variant = 'primary', disabled }: ButtonProps) {
  return (
    <button onClick={onClick} disabled={disabled} className={variant}>
      {children}
    </button>
  );
}

// GOOD: Extending HTML attributes
type InputProps = React.InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  error?: string;
};

export function Input({ label, error, ...props }: InputProps) {
  return (
    <div>
      <label>{label}</label>
      <input {...props} />
      {error && <span className="error">{error}</span>}
    </div>
  );
}
```

### Typing Events

Event handlers **MUST** use React's built-in event types:

```tsx
type FormProps = {
  onSubmit: (data: FormData) => void;
};

function Form({ onSubmit }: FormProps) {
  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    onSubmit(formData);
  }

  function handleInputChange(event: React.ChangeEvent<HTMLInputElement>) {
    console.log(event.target.value);
  }

  function handleButtonClick(event: React.MouseEvent<HTMLButtonElement>) {
    console.log('Clicked', event.currentTarget.name);
  }

  return (
    <form onSubmit={handleSubmit}>
      <input onChange={handleInputChange} />
      <button onClick={handleButtonClick}>Submit</button>
    </form>
  );
}
```

### Typing Refs

Refs **MUST** be typed with the element type:

```tsx
function VideoPlayer() {
  const videoRef = useRef<HTMLVideoElement>(null);

  function handlePlay() {
    videoRef.current?.play();
  }

  function handlePause() {
    videoRef.current?.pause();
  }

  return (
    <div>
      <video ref={videoRef} src="/video.mp4" />
      <button onClick={handlePlay}>Play</button>
      <button onClick={handlePause}>Pause</button>
    </div>
  );
}

// Forwarding refs
type InputProps = {
  label: string;
};

export const Input = forwardRef<HTMLInputElement, InputProps>(
  function Input({ label }, ref) {
    return (
      <div>
        <label>{label}</label>
        <input ref={ref} />
      </div>
    );
  }
);
```

### Generic Components

Generic components **SHOULD** be used for reusable data structures:

```tsx
type ListProps<T> = {
  items: T[];
  renderItem: (item: T) => React.ReactNode;
  keyExtractor: (item: T) => string;
};

function List<T>({ items, renderItem, keyExtractor }: ListProps<T>) {
  return (
    <ul>
      {items.map((item) => (
        <li key={keyExtractor(item)}>{renderItem(item)}</li>
      ))}
    </ul>
  );
}

// Usage with full type inference
type Product = { id: string; name: string; price: number };

function ProductList({ products }: { products: Product[] }) {
  return (
    <List
      items={products}
      renderItem={(product) => <span>{product.name} - ${product.price}</span>}
      keyExtractor={(product) => product.id}
    />
  );
}
```

## Testing

### React Testing Library Principles

Tests **MUST** follow Testing Library's guiding principles[^4]:

1. Test user behavior, not implementation
2. Query by accessible roles and labels
3. Avoid testing internal state

```tsx
// GOOD: Testing user behavior
import { render, screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { LoginForm } from './LoginForm';

test('submits form with valid credentials', async () => {
  const user = userEvent.setup();
  const handleSubmit = vi.fn();

  render(<LoginForm onSubmit={handleSubmit} />);

  await user.type(screen.getByLabelText(/email/i), 'user@example.com');
  await user.type(screen.getByLabelText(/password/i), 'password123');
  await user.click(screen.getByRole('button', { name: /log in/i }));

  expect(handleSubmit).toHaveBeenCalledWith({
    email: 'user@example.com',
    password: 'password123',
  });
});

// BAD: Testing implementation details
test('updates email state on input change', () => {
  const { result } = renderHook(() => useState(''));
  const [email, setEmail] = result.current;

  act(() => setEmail('user@example.com'));

  expect(result.current[0]).toBe('user@example.com');  // Testing internal state
});
```

### What to Test

Tests **SHOULD** cover:

- User interactions (clicks, typing, navigation)
- Conditional rendering based on props/state
- Error states and loading states
- Accessibility (ARIA attributes, keyboard navigation)

Tests **SHOULD NOT** cover:

- Internal state variables
- Implementation details (function names, variable names)
- Third-party library behavior

```tsx
// GOOD: Testing conditional rendering
test('shows loading state while fetching', () => {
  render(<UserProfile userId="123" />);

  expect(screen.getByText(/loading/i)).toBeInTheDocument();
});

test('shows error message on fetch failure', async () => {
  server.use(
    http.get('/api/users/:id', () => HttpResponse.error())
  );

  render(<UserProfile userId="123" />);

  expect(await screen.findByText(/error loading user/i)).toBeInTheDocument();
});

test('displays user data after successful fetch', async () => {
  render(<UserProfile userId="123" />);

  expect(await screen.findByText(/john doe/i)).toBeInTheDocument();
  expect(screen.getByText(/john@example.com/i)).toBeInTheDocument();
});
```

### Testing Hooks

Custom hooks **SHOULD** be tested using `renderHook`:

```tsx
import { renderHook, waitFor } from '@testing-library/react';
import { useLocalStorage } from './useLocalStorage';

test('reads initial value from localStorage', () => {
  localStorage.setItem('theme', JSON.stringify('dark'));

  const { result } = renderHook(() => useLocalStorage('theme', 'light'));

  expect(result.current[0]).toBe('dark');
});

test('updates localStorage when value changes', async () => {
  const { result } = renderHook(() => useLocalStorage('theme', 'light'));

  act(() => {
    result.current[1]('dark');
  });

  await waitFor(() => {
    expect(localStorage.getItem('theme')).toBe(JSON.stringify('dark'));
  });
});
```

### MSW for API Mocking

Projects **MUST** use MSW[^12] (Mock Service Worker) for API mocking:

```tsx
// vitest.setup.ts
import { beforeAll, afterEach, afterAll } from 'vitest';
import { server } from './mocks/server';

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

```tsx
// mocks/handlers.ts
import { http, HttpResponse } from 'msw';

type LoginBody = {
  email: string;
  password: string;
};

function isLoginBody(body: unknown): body is LoginBody {
  if (typeof body !== 'object' || body === null) return false;

  const { email, password } = body as Record<string, unknown>;

  return typeof email === 'string' && typeof password === 'string';
}

export const handlers = [
  http.get('/api/users/:id', ({ params }) => {
    return HttpResponse.json({
      id: params.id,
      name: 'John Doe',
      email: 'john@example.com',
    });
  }),

  http.post('/api/login', async ({ request }) => {
    const body: unknown = await request.json();

    // GOOD: reject a malformed body explicitly instead of destructuring blind
    if (!isLoginBody(body)) {
      return HttpResponse.json({ error: 'Malformed request body' }, { status: 400 });
    }

    if (body.email === 'user@example.com' && body.password === 'password123') {
      return HttpResponse.json({ token: 'fake-token' });
    }

    return HttpResponse.json({ error: 'Invalid credentials' }, { status: 401 });
  }),
];
```

Handlers **MUST NOT** destructure a decoded body without narrowing it first:

```tsx
// BAD: `request.json()` resolves to MSW's `DefaultBodyType`.
// tsc rejects this with TS2339: Property 'email' does not exist on type 'DefaultBodyType'.
http.post('/api/login', async ({ request }) => {
  const { email, password } = await request.json();
  // ...
});
```

MSW's request-body generic (`http.post<PathParams, LoginBody>`) documents the contract and makes
the handler compile, but it is an unchecked assertion: it does not validate the payload, so a
test that posts the wrong shape still reaches the handler body. Handlers **SHOULD** validate
instead, so that a test sending a malformed request gets a 400 rather than `undefined`
comparisons that silently fall through to the 401 branch.

**Why MSW**: Intercepts requests at the network level, works in both tests and browser,
provides realistic API mocking without coupling tests to implementation details like
fetch/axios.

## Performance

### React Compiler (React 19)

Projects using React 19 **SHOULD** enable the React Compiler[^13] to automatically optimize re-renders.

#### Installation and Configuration

```bash
npm install -D babel-plugin-react-compiler eslint-plugin-react-compiler
```

```js
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [
    react({
      babel: {
        plugins: [['babel-plugin-react-compiler', { target: '19' }]],
      },
    }),
  ],
});
```

```js
// next.config.js (Next.js 15+)
/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    reactCompiler: true,
  },
};

module.exports = nextConfig;
```

#### ESLint Integration

Projects **MUST** use the React Compiler ESLint plugin to catch violations:

```js
// eslint.config.js
import reactCompiler from 'eslint-plugin-react-compiler';

export default [
  {
    plugins: {
      'react-compiler': reactCompiler,
    },
    rules: {
      'react-compiler/react-compiler': 'error',
    },
  },
];
```

#### What the Compiler Optimizes

The compiler automatically handles optimizations that previously required manual intervention:

```tsx
// BEFORE: Manual memoization required (React 18)
function ProductList({ products, filter }: ProductListProps) {
  const filteredProducts = useMemo(
    () => products.filter((p) => p.category === filter),
    [products, filter]
  );

  const handleClick = useCallback(
    (id: string) => console.log('clicked', id),
    []
  );

  return (
    <ul>
      {filteredProducts.map((product) => (
        <MemoizedItem key={product.id} product={product} onClick={handleClick} />
      ))}
    </ul>
  );
}

const MemoizedItem = memo(ProductItem);

// AFTER: React Compiler handles this automatically (React 19)
function ProductList({ products, filter }: ProductListProps) {
  const filteredProducts = products.filter((p) => p.category === filter);

  function handleClick(id: string) {
    console.log('clicked', id);
  }

  return (
    <ul>
      {filteredProducts.map((product) => (
        <ProductItem key={product.id} product={product} onClick={handleClick} />
      ))}
    </ul>
  );
}
```

#### Rules of React for Compiler Compatibility

Code **MUST** follow the Rules of React for the compiler to optimize correctly:

```tsx
// GOOD: Pure component - compiler can optimize
function ProductCard({ product }: { product: Product }) {
  return (
    <div>
      <h3>{product.name}</h3>
      <p>${product.price}</p>
    </div>
  );
}

// BAD: Mutating props - compiler cannot optimize safely
function ProductCard({ product }: { product: Product }) {
  product.viewCount++;  // WRONG: Mutating props breaks purity
  return <div>{product.name}</div>;
}

// BAD: Reading mutable values during render
let globalCounter = 0;

function Counter() {
  globalCounter++;  // WRONG: Side effect during render
  return <div>{globalCounter}</div>;
}

// GOOD: Use state for mutable values
function Counter() {
  const [count, setCount] = useState(0);
  return (
    <div>
      <p>{count}</p>
      <button onClick={() => setCount(c => c + 1)}>Increment</button>
    </div>
  );
}
```

#### Opting Out of Compilation

Use the `"use no memo"` directive to opt specific components out:

```tsx
function LegacyComponent({ data }: Props) {
  "use no memo";  // Skip compiler optimization for this component

  // Component with patterns incompatible with compiler
  return <div>{/* ... */}</div>;
}
```

**Why React Compiler**: Automatically memoizes components and values, eliminating the need for
manual `memo`, `useMemo`, and `useCallback` in most cases. Significantly reduces bundle size and
improves runtime performance.

### Manual Memoization (React 18)

Projects on React 18 **SHOULD** use memoization for expensive computations:

```tsx
// useMemo for expensive calculations
function ProductList({ products, filter }: ProductListProps) {
  const filteredProducts = useMemo(() => {
    return products.filter((p) => p.category === filter);
  }, [products, filter]);

  return (
    <ul>
      {filteredProducts.map((product) => (
        <li key={product.id}>{product.name}</li>
      ))}
    </ul>
  );
}

// useCallback for event handlers passed as props
function SearchBar({ onSearch }: { onSearch: (query: string) => void }) {
  const [query, setQuery] = useState('');

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      onSearch(query);
    },
    [query, onSearch]
  );

  return (
    <form onSubmit={handleSubmit}>
      <input value={query} onChange={(e) => setQuery(e.target.value)} />
    </form>
  );
}

// memo for pure components that re-render frequently
export const ExpensiveComponent = memo(function ExpensiveComponent({
  data,
}: {
  data: LargeDataset;
}) {
  return <div>{/* complex rendering logic */}</div>;
});
```

**When NOT to use memoization**: Don't memoize unless profiling shows a performance issue.
Premature optimization adds complexity without guaranteed benefit.

### Code Splitting

Large applications **SHOULD** use code splitting with `React.lazy`:

```tsx
import { lazy, Suspense } from 'react';

const Dashboard = lazy(() => import('./features/dashboard/Dashboard'));
const Settings = lazy(() => import('./features/settings/Settings'));

function App() {
  return (
    <Suspense fallback={<Loading />}>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Suspense>
  );
}
```

**Why code splitting**: Reduces initial bundle size by loading route components on demand.
Essential for large applications with many routes.

## Server Components (React 19)

### Server Component Security

React Server Components are the subject of a continuing advisory series that opened with remote
code execution (CVE-2025-55182[^rsc-rce]) and has since produced repeated denial-of-service and
source-code-exposure disclosures[^rsc-dos]. Every patch floor published so far has been
superseded by a later one: the December 2025 patches were re-issued twice, the versions React
published as safe on 26 January 2026 (19.0.4, 19.1.5, 19.2.4) were superseded in April and again
in May 2026, and those in turn by CVE-2026-44907[^rsc-dos-2026] in July 2026.

Projects that render Server Components **MUST** satisfy all of the following:

- `react-server-dom-webpack`, `react-server-dom-parcel`, and `react-server-dom-turbopack`
  **MUST** be at least **19.2.8**, or at least **19.1.9** or **19.0.8** on the older maintained
  lines. These are the floors for CVE-2026-44907[^rsc-dos-2026], the most recent disclosure as
  of 2026-09-08.
- The owning framework or bundler plugin — `next`, `react-router`, `waku`, `@parcel/rsc`,
  `@vitejs/plugin-rsc`, or `rwsdk` — **MUST** be upgraded to its own patched release. Every
  advisory in this series names only the `react-server-dom-*` packages, so upgrading `react` and
  `react-dom` alone does **not** remediate: the vulnerable code reaches the application through
  the framework's own pinned or bundled copy.
- The floors above **MUST** be re-checked against the GitHub Advisory Database[^rsc-advisories]
  before pinning, because this series has repeatedly superseded its own published floors.
- Hosting-provider mitigations **MUST NOT** be treated as a substitute for upgrading[^rsc-dos].

Applications that use no framework, bundler, or bundler plugin with Server Component support are
not affected by this series.

**Why a named floor plus a re-check rule**: A version number alone goes stale — several of the
floors React itself published were later declared unsafe. Naming the current floor gives readers
something actionable today; requiring the advisory-database check stops the guide from becoming
the reason an application ships a known-vulnerable RSC runtime.

### When to Use Server Components

Server Components **SHOULD** be used for:

- Data fetching from databases or APIs
- Content-heavy pages (blog posts, documentation)
- Components without interactivity
- Reducing client JavaScript bundle size

```tsx
// app/blog/[slug]/page.tsx (Server Component)
import { db } from '@/lib/db';

type PageProps = {
  params: Promise<{ slug: string }>;
};

export default async function BlogPost({ params }: PageProps) {
  const { slug } = await params;
  const post = await db.post.findUnique({ where: { slug } });

  if (!post) return <NotFound />;

  return (
    <article>
      <h1>{post.title}</h1>
      <div>{post.content}</div>
    </article>
  );
}
```

### When to Use Client Components

Client Components **MUST** be used for:

- Interactive elements (onClick, onChange handlers)
- Hooks (useState, useEffect, useContext)
- Browser-only APIs (localStorage, window, document)
- Real-time updates (WebSockets, polling)

```tsx
'use client';

import { useState } from 'react';

export function Counter() {
  const [count, setCount] = useState(0);

  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={() => setCount(count + 1)}>Increment</button>
    </div>
  );
}
```

### Server and Client Composition

Server Components **SHOULD** compose Client Components via props:

```tsx
// app/dashboard/page.tsx (Server Component)
import { db } from '@/lib/db';
import { InteractiveChart } from './InteractiveChart';

export default async function Dashboard() {
  const data = await db.metrics.findMany();

  return (
    <div>
      <h1>Dashboard</h1>
      <InteractiveChart data={data} />  {/* Client Component with server data */}
    </div>
  );
}

// app/dashboard/InteractiveChart.tsx (Client Component)
'use client';

import { useState } from 'react';

const CHART_VIEWS = ['day', 'week', 'month'] as const;

type ChartView = (typeof CHART_VIEWS)[number];

function isChartView(value: string): value is ChartView {
  return (CHART_VIEWS as readonly string[]).includes(value);
}

type ChartProps = {
  data: Metric[];
};

export function InteractiveChart({ data }: ChartProps) {
  const [view, setView] = useState<ChartView>('day');

  function handleViewChange(event: React.ChangeEvent<HTMLSelectElement>) {
    const value = event.currentTarget.value;

    // GOOD: reject anything outside the union before it reaches state
    if (!isChartView(value)) {
      throw new Error(`Unsupported chart view: ${value}`);
    }

    setView(value);
  }

  return (
    <div>
      <select value={view} onChange={handleViewChange}>
        {CHART_VIEWS.map((option) => (
          <option key={option} value={option}>{option}</option>
        ))}
      </select>
      <Chart data={filterDataByView(data, view)} />
    </div>
  );
}
```

Event values **MUST NOT** be passed straight into a union-typed setter:

```tsx
// BAD: `event.target.value` is `string`, not the state union.
// tsc rejects this with TS2345: Argument of type 'string' is not assignable to
// parameter of type 'SetStateAction<"day" | "month" | "week">'.
<select value={view} onChange={(e) => setView(e.target.value)}>
```

**Why narrow explicitly**: The DOM types `HTMLSelectElement.value` as `string` regardless of
which `<option>` elements are rendered, so TypeScript cannot infer the union from the markup.
Deriving both the options and the type from a single `as const` tuple keeps the rendered choices
and the state type in step, and the guard converts a silently invalid value — from a stale cached
bundle or a browser extension rewriting the DOM — into a visible failure.

**Why this pattern**: Server Components fetch data with zero client JavaScript, Client Components
provide interactivity where needed, and props create a clean boundary between server and client.

## Accessibility

### Semantic HTML

Components **MUST** use semantic HTML elements:

```tsx
// GOOD: Semantic HTML
function Navigation() {
  return (
    <nav>
      <ul>
        <li><a href="/home">Home</a></li>
        <li><a href="/about">About</a></li>
      </ul>
    </nav>
  );
}

function Article({ post }: { post: Post }) {
  return (
    <article>
      <header>
        <h1>{post.title}</h1>
        <time dateTime={post.publishedAt}>{formatDate(post.publishedAt)}</time>
      </header>
      <section>{post.content}</section>
    </article>
  );
}

// BAD: Non-semantic HTML
function Navigation() {
  return (
    <div className="nav">
      <div className="nav-item">Home</div>
      <div className="nav-item">About</div>
    </div>
  );
}
```

### ARIA Attributes

ARIA attributes **MUST** be used when semantic HTML is insufficient:

```tsx
function Modal({ isOpen, onClose, children }: ModalProps) {
  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      aria-describedby="modal-description"
    >
      <h2 id="modal-title">Confirmation</h2>
      <p id="modal-description">Are you sure you want to proceed?</p>
      <div>{children}</div>
      <button onClick={onClose}>Close</button>
    </div>
  );
}

function Tabs({ tabs }: { tabs: Tab[] }) {
  const [activeTab, setActiveTab] = useState(0);

  return (
    <div>
      <div role="tablist">
        {tabs.map((tab, index) => (
          <button
            key={tab.id}
            role="tab"
            aria-selected={activeTab === index}
            aria-controls={`panel-${tab.id}`}
            onClick={() => setActiveTab(index)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div role="tabpanel" id={`panel-${tabs[activeTab].id}`}>
        {tabs[activeTab].content}
      </div>
    </div>
  );
}
```

### Focus Management

Interactive components **MUST** manage focus properly:

```tsx
import { useRef, useEffect } from 'react';

function Dialog({ isOpen, onClose }: DialogProps) {
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (isOpen) {
      closeButtonRef.current?.focus();  // Focus close button on open
    }
  }, [isOpen]);

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Escape') {
      onClose();
    }
  }

  if (!isOpen) return null;

  return (
    <div role="dialog" onKeyDown={handleKeyDown}>
      <h2>Dialog Title</h2>
      <p>Dialog content</p>
      <button ref={closeButtonRef} onClick={onClose}>
        Close
      </button>
    </div>
  );
}
```

### Alt Text and Labels

Images and form inputs **MUST** have descriptive text:

```tsx
// Images
function ProductCard({ product }: { product: Product }) {
  return (
    <div>
      <img src={product.image} alt={`${product.name} product photo`} />
      <h3>{product.name}</h3>
    </div>
  );
}

// Form inputs with labels
function LoginForm() {
  return (
    <form>
      <label htmlFor="email">Email address</label>
      <input id="email" type="email" required />

      <label htmlFor="password">Password</label>
      <input id="password" type="password" required />

      <button type="submit">Log in</button>
    </form>
  );
}
```

## CI Pipeline

```yaml
# .github/workflows/test.yml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '22'
          cache: 'npm'
      - run: npm ci
      - run: npx biome ci .
      - run: npx tsc --noEmit

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '22'
          cache: 'npm'
      - run: npm ci
      - run: npx vitest run --coverage

  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '22'
          cache: 'npm'
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npx playwright test
```

## See Also

- [TypeScript Guide](../languages/typescript.md) - Base TypeScript conventions and tooling
- [Testing Guide](../process/testing.md) - General testing principles and patterns
- [CI Guide](../process/ci.md) - Continuous integration best practices

## References

[^1]: [Biome](https://biomejs.dev/) - Fast formatter and linter for JavaScript/TypeScript with React support

[^2]: [TypeScript](https://www.typescriptlang.org/) - TypeScript official website and documentation

[^3]: [Vitest](https://vitest.dev/) - Next generation testing framework powered by Vite

[^4]: [React Testing Library](https://testing-library.com/react) - Light-weight solution for testing React components. Encourages testing user behavior over implementation details.

[^5]: [Playwright](https://playwright.dev/) - End-to-end testing for modern web apps across Chromium, Firefox, and WebKit

[^6]: [Astro](https://astro.build/) - Modern static site builder with partial hydration for content-heavy sites

[^7]: [Next.js](https://nextjs.org/) - React framework with server-side rendering, static generation, and file-based routing

[^8]: [Rules of Hooks](https://react.dev/reference/rules/rules-of-hooks) - Official React documentation on hook usage rules

[^9]: [Zustand](https://zustand.docs.pmnd.rs/) - Small, fast, and scalable state management library with minimal boilerplate

[^10]: [Jotai](https://jotai.org/) - Primitive and flexible state management library for React using atomic design

[^11]: [Redux Toolkit](https://redux-toolkit.js.org/) - Official, opinionated Redux toolset for efficient Redux development

[^12]: [MSW (Mock Service Worker)](https://mswjs.io/) - API mocking library that intercepts requests at the network level for seamless testing

[^13]: [React Compiler](https://react.dev/learn/react-compiler) - Automatic optimization compiler that memoizes components and values in React 19+

[^react19]: [React 19 New Hooks](https://react.dev/blog/2024/12/05/react-19) - Official React 19 release notes covering useActionState, useFormStatus, useOptimistic, and the use API

[^react-npm]: [react on npm](https://registry.npmjs.org/react/latest) - Registry metadata for the `latest` dist-tag; 19.2.8 as of 2026-09-08

[^react-component]: [React `Component` reference](https://react.dev/reference/react/Component) - Confirms class components remain supported, documents `getDerivedStateFromError` and `componentDidCatch`, and lists what error boundaries do not catch

[^react-error-boundary]: [react-error-boundary](https://github.com/bvaughn/react-error-boundary) - Maintained error boundary abstraction recommended by the React documentation

[^nextjs-error]: [Next.js `error.js` convention](https://nextjs.org/docs/app/api-reference/file-conventions/error) - Framework-provided error boundary for App Router segments

[^rsc-rce]: [Critical Security Vulnerability in React Server Components](https://react.dev/blog/2025/12/03/critical-security-vulnerability-in-react-server-components) - CVE-2025-55182, remote code execution in React Server Components

[^rsc-dos]: [Denial of Service and Source Code Exposure in React Server Components](https://react.dev/blog/2025/12/11/denial-of-service-and-source-code-exposure-in-react-server-components) - CVE-2025-55183, CVE-2025-55184, CVE-2025-67779, and CVE-2026-23864; also records that earlier patches were incomplete

[^rsc-dos-2026]: [GHSA-wx67-qw84-cm4g](https://github.com/advisories/GHSA-wx67-qw84-cm4g) - CVE-2026-44907, denial of service in Server Functions; patched in react-server-dom-\* 19.0.8, 19.1.9, and 19.2.8

[^rsc-advisories]: [GitHub Advisory Database: react-server-dom-webpack](https://github.com/advisories?query=react-server-dom-webpack) - Authoritative, continuously updated list of React Server Component advisories and their patched versions
