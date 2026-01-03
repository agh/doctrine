# TypeScript Style Guide

> [Doctrine](../../README.md) > [Languages](../README.md) > TypeScript

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

Extends [Google TypeScript Style Guide](google/typescript.html).

## Quick Reference

| Task | Tool | Command |
| ---- | ---- | ------- |
| Lint | Biome[^1] | `biome check .` |
| Format | Biome[^1] | `biome format --write .` |
| Type check | tsc[^2] | `tsc --noEmit` |
| Semantic | - | - |
| Dead code | ts-prune[^3] | `ts-prune` |
| Coverage | c8[^4] | `c8 vitest` |
| Complexity | - | via Biome[^1] |
| Fuzz | - | - |
| Test perf | Vitest[^5] | `vitest --pool=threads` |

## Linting & Formatting: Biome

Projects **MUST** use Biome[^1] for linting and formatting unless extensive
plugin ecosystems are required (see ESLint Alternative below).

### Why Biome

- **Performance**: 20x faster than ESLint[^6]+Prettier[^7]
- **Unified tooling**: Combines linting, formatting, and import organization in one tool
- **Zero config**: Works out of the box with sensible defaults
- **Better errors**: Provides more actionable error messages
- **Native binary**: No JavaScript runtime overhead

```bash
# Install
npm install --save-dev @biomejs/biome

# Initialize config
npx biome init

# Lint and format
npx biome check --write .

# CI mode
npx biome ci .
```

### Configuration (biome.json)

```json
{
  "$schema": "https://biomejs.dev/schemas/1.9.4/schema.json",
  "organizeImports": {
    "enabled": true
  },
  "linter": {
    "enabled": true,
    "rules": {
      "recommended": true,
      "complexity": {
        "noExcessiveCognitiveComplexity": {
          "level": "warn",
          "options": { "maxAllowedComplexity": 15 }
        }
      },
      "suspicious": {
        "noExplicitAny": "error"
      },
      "style": {
        "useConst": "error",
        "noNonNullAssertion": "warn"
      }
    }
  },
  "formatter": {
    "enabled": true,
    "indentStyle": "space",
    "indentWidth": 2,
    "lineWidth": 100
  },
  "javascript": {
    "formatter": {
      "quoteStyle": "single",
      "semicolons": "always"
    }
  }
}
```

### ESLint Alternative

Projects **MAY** use ESLint[^6] for projects requiring extensive plugin ecosystems:

```bash
npm install --save-dev eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin
```

```json
{
  "parser": "@typescript-eslint/parser",
  "plugins": ["@typescript-eslint"],
  "extends": [
    "eslint:recommended",
    "plugin:@typescript-eslint/strict-type-checked",
    "plugin:@typescript-eslint/stylistic-type-checked"
  ],
  "parserOptions": {
    "project": true
  }
}
```

## Type Checking: tsc

Projects **MUST** enable strict type checking with TypeScript[^2]'s compiler.

### Why tsc

- **Official compiler**: The authoritative TypeScript type checker
- **Strict mode**: Catches entire classes of bugs at compile time
- **IDE integration**: Provides real-time type checking in editors
- **Zero-cost abstraction**: Type checking happens at build time with no runtime overhead

```bash
# Check types without emitting
npx tsc --noEmit

# Watch mode
npx tsc --noEmit --watch
```

### tsconfig.json (Strict)

Projects **MUST** enable all strict type checking options:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "exactOptionalPropertyTypes": true,
    "skipLibCheck": true
  }
}
```

## Decorators

Projects **MAY** use decorators for cross-cutting concerns like logging,
validation, and dependency injection. TypeScript 5.0+ supports ECMAScript
decorators natively.

### Why Decorators

- **Separation of concerns**: Keep business logic clean by extracting cross-cutting behavior
- **Reusability**: Apply common patterns (logging, caching, authorization) declaratively
- **Metaprogramming**: Modify or extend class behavior at design time
- **Framework support**: Required for frameworks like NestJS[^17], TypeORM[^18], and Angular[^19]

### Enabling Decorators

```json
// tsconfig.json
{
  "compilerOptions": {
    // For TC39 decorators (TypeScript 5.0+)
    // No flag needed - enabled by default

    // For legacy/experimental decorators (older frameworks)
    "experimentalDecorators": true,
    "emitDecoratorMetadata": true
  }
}
```

### Class Decorators

```typescript
// Modern TC39 decorator (TypeScript 5.0+)
function Singleton<T extends new (...args: any[]) => object>(
  target: T,
  context: ClassDecoratorContext
) {
  let instance: InstanceType<T>;
  return class extends target {
    constructor(...args: any[]) {
      if (instance) return instance;
      super(...args);
      instance = this as InstanceType<T>;
    }
  };
}

@Singleton
class Database {
  constructor(private url: string) {}
}

// Same instance
const db1 = new Database('postgres://...');
const db2 = new Database('mysql://...');
console.log(db1 === db2); // true
```

### Method Decorators

```typescript
function Log(
  target: any,
  context: ClassMethodDecoratorContext
) {
  const methodName = String(context.name);
  return function (this: any, ...args: any[]) {
    console.log(`[${methodName}] called with:`, args);
    const result = target.call(this, ...args);
    console.log(`[${methodName}] returned:`, result);
    return result;
  };
}

class Calculator {
  @Log
  add(a: number, b: number): number {
    return a + b;
  }
}
```

### Field Decorators

```typescript
function Validate(min: number, max: number) {
  return function (
    target: undefined,
    context: ClassFieldDecoratorContext
  ) {
    return function (initialValue: number): number {
      if (initialValue < min || initialValue > max) {
        throw new Error(`Value must be between ${min} and ${max}`);
      }
      return initialValue;
    };
  };
}

class Product {
  @Validate(0, 100)
  quantity = 10;
}
```

### Legacy Decorators (NestJS, TypeORM)

```typescript
// Legacy experimental decorators for frameworks
import { Controller, Get, Injectable } from '@nestjs/common';
import { Entity, Column, PrimaryGeneratedColumn } from 'typeorm';

// NestJS controller
@Controller('users')
class UserController {
  @Get()
  findAll() {
    return [];
  }
}

// TypeORM entity
@Entity()
class User {
  @PrimaryGeneratedColumn()
  id: number;

  @Column()
  name: string;
}

// Dependency injection
@Injectable()
class UserService {
  constructor(private readonly repo: UserRepository) {}
}
```

### Decorator Patterns

```typescript
// Memoization decorator
function Memoize(
  target: any,
  context: ClassMethodDecoratorContext
) {
  const cache = new Map<string, any>();
  return function (this: any, ...args: any[]) {
    const key = JSON.stringify(args);
    if (cache.has(key)) return cache.get(key);
    const result = target.call(this, ...args);
    cache.set(key, result);
    return result;
  };
}

// Retry decorator
function Retry(attempts: number) {
  return function (target: any, context: ClassMethodDecoratorContext) {
    return async function (this: any, ...args: any[]) {
      for (let i = 0; i < attempts; i++) {
        try {
          return await target.call(this, ...args);
        } catch (e) {
          if (i === attempts - 1) throw e;
        }
      }
    };
  };
}

class ApiClient {
  @Memoize
  @Retry(3)
  async fetchUser(id: string) {
    return await fetch(`/api/users/${id}`);
  }
}
```

## Declaration Files

Projects **MUST** provide type declarations for any public JavaScript APIs.
Declaration files (`.d.ts`) describe the shape of existing JavaScript code.

### Why Declaration Files

- **Type safety**: Enable TypeScript to type-check usage of JavaScript libraries
- **IDE support**: Provide autocomplete and documentation for JavaScript APIs
- **Interoperability**: Bridge untyped JavaScript with typed TypeScript
- **Documentation**: Serve as machine-readable API documentation

### Generating Declarations

```json
// tsconfig.json
{
  "compilerOptions": {
    "declaration": true,
    "declarationDir": "./types",
    "declarationMap": true,  // Enables "Go to Definition" to source
    "emitDeclarationOnly": true  // Only emit .d.ts files
  }
}
```

### Writing Declaration Files

```typescript
// types/mylib.d.ts

// Module declaration
declare module 'mylib' {
  export function greet(name: string): string;
  export const VERSION: string;

  export interface Config {
    debug: boolean;
    timeout: number;
  }

  export class Client {
    constructor(config: Config);
    connect(): Promise<void>;
    disconnect(): void;
  }

  // Default export
  export default function init(config: Config): Client;
}

// Ambient declarations for global variables
declare global {
  interface Window {
    myApp: {
      version: string;
      init(): void;
    };
  }

  const __DEV__: boolean;
  const __VERSION__: string;
}

// Module augmentation (extending existing types)
declare module 'express' {
  interface Request {
    userId?: string;
    sessionId?: string;
  }
}
```

### Package Type Declarations

```json
// package.json
{
  "name": "my-package",
  "main": "./dist/index.js",
  "types": "./dist/index.d.ts",
  "exports": {
    ".": {
      "types": "./dist/index.d.ts",
      "import": "./dist/index.mjs",
      "require": "./dist/index.cjs"
    },
    "./utils": {
      "types": "./dist/utils.d.ts",
      "import": "./dist/utils.mjs",
      "require": "./dist/utils.cjs"
    }
  }
}
```

### DefinitelyTyped

For third-party JavaScript libraries without types, use types from DefinitelyTyped[^20]:

```bash
# Install types for a library
npm install --save-dev @types/lodash
npm install --save-dev @types/express
npm install --save-dev @types/node

# Types are automatically used by TypeScript
```

### Triple-Slash Directives

```typescript
// Reference another declaration file
/// <reference path="./other-types.d.ts" />

// Reference built-in lib types
/// <reference lib="dom" />
/// <reference lib="es2022" />

// Reference types package
/// <reference types="node" />
```

### Declaration File Patterns

```typescript
// types/utils.d.ts

// Function overloads
export function parse(input: string): object;
export function parse(input: Buffer): object;
export function parse(input: string, options: ParseOptions): object;

// Generic functions
export function identity<T>(value: T): T;
export function map<T, U>(array: T[], fn: (item: T) => U): U[];

// Utility types
export type Nullable<T> = T | null;
export type DeepReadonly<T> = {
  readonly [P in keyof T]: DeepReadonly<T[P]>;
};

// Conditional types
export type Unwrap<T> = T extends Promise<infer U> ? U : T;
export type ElementOf<T> = T extends (infer E)[] ? E : never;
```

## Module Resolution

Projects **MUST** configure module resolution to match their runtime
environment and bundler requirements.

### Why Module Resolution Matters

- **Correctness**: Ensures TypeScript finds the same modules as the runtime
- **Compatibility**: Different environments (Node.js, browsers, bundlers) have
  different resolution rules
- **Performance**: Proper configuration reduces failed resolution attempts
- **Predictability**: Eliminates "works on my machine" module resolution issues

### Module Resolution Strategies

| Strategy | Use Case | tsconfig Setting |
| -------- | -------- | ---------------- |
| Node16/NodeNext | Modern Node.js (ESM + CJS) | `"moduleResolution": "NodeNext"` |
| Bundler | Webpack, Vite, esbuild | `"moduleResolution": "Bundler"` |
| Node10 (legacy) | Older Node.js CJS only | `"moduleResolution": "Node"` |

### Modern Node.js (Recommended)

```json
// tsconfig.json for Node.js 16+
{
  "compilerOptions": {
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "target": "ES2022"
  }
}
```

```typescript
// With NodeNext, extensions are required for relative imports
import { foo } from './foo.js';  // Note: .js extension even for .ts files
import { bar } from './utils/bar.js';

// Package imports work as expected
import express from 'express';
import { z } from 'zod';
```

### Bundler Mode (Vite, Webpack)

```json
// tsconfig.json for bundler environments
{
  "compilerOptions": {
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "allowImportingTsExtensions": true,
    "noEmit": true
  }
}
```

```typescript
// With Bundler, extensions are optional
import { foo } from './foo';
import { bar } from './utils/bar';

// Bundler-specific features work
import styles from './styles.module.css';
import data from './data.json';
```

### Path Aliases

```json
// tsconfig.json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@components/*": ["src/components/*"],
      "@utils/*": ["src/utils/*"]
    }
  }
}
```

```typescript
// Use path aliases instead of relative paths
import { Button } from '@components/Button';
import { formatDate } from '@utils/date';
import { config } from '@/config';

// Instead of:
import { Button } from '../../../components/Button';
```

### Package.json Exports

```json
// package.json
{
  "name": "my-lib",
  "type": "module",
  "exports": {
    ".": {
      "types": "./dist/index.d.ts",
      "import": "./dist/index.js",
      "require": "./dist/index.cjs"
    },
    "./utils": {
      "types": "./dist/utils.d.ts",
      "import": "./dist/utils.js"
    }
  },
  "typesVersions": {
    "*": {
      "utils": ["./dist/utils.d.ts"]
    }
  }
}
```

### Subpath Imports

```json
// package.json
{
  "imports": {
    "#utils/*": "./src/utils/*.js",
    "#components/*": "./src/components/*.js",
    "#config": {
      "development": "./src/config/dev.js",
      "production": "./src/config/prod.js"
    }
  }
}
```

```typescript
// Use subpath imports (private to package)
import { logger } from '#utils/logger';
import { Button } from '#components/Button';
```

### Module Resolution Debugging

```bash
# Trace module resolution
npx tsc --traceResolution

# Check specific module
npx tsc --traceResolution 2>&1 | grep "some-module"

# Explain why a file is included
npx tsc --explainFiles
```

### Common Resolution Issues

```typescript
// Issue: "Cannot find module './foo'"
// Solution 1: Add extension for NodeNext
import { foo } from './foo.js';

// Solution 2: Check paths in tsconfig.json
// Solution 3: Verify file exists and casing matches

// Issue: "Cannot find type definitions for 'express'"
// Solution: Install @types package
// npm install --save-dev @types/express

// Issue: Module works at runtime but TypeScript errors
// Solution: Check moduleResolution matches your runtime
```

## Dead Code Detection: ts-prune

Projects **SHOULD** regularly check for unused exports using ts-prune[^3].

```bash
# Install
npm install --save-dev ts-prune

# Find unused exports
npx ts-prune
```

## Code Coverage: c8

Projects **SHOULD** measure code coverage using c8[^4] or Vitest[^5]'s built-in coverage provider.

c8[^4] uses V8's built-in coverage for fast, accurate results.

```bash
# With Vitest
npx c8 vitest run

# Threshold
npx c8 --check-coverage --lines 80 vitest run
```

Or with Vitest[^5]'s built-in coverage:

```typescript
// vitest.config.ts
export default defineConfig({
  test: {
    coverage: {
      provider: 'v8',
      thresholds: {
        lines: 80,
        branches: 80,
      },
    },
  },
});
```

## Test Performance: Vitest

Projects **MUST** use Vitest[^5] as the test runner for TypeScript projects.

### Why Vitest

- **Native ESM support**: Works seamlessly with modern TypeScript modules
- **Vite-powered**: Leverages Vite[^8]'s transform pipeline for instant hot module replacement
- **Jest-compatible API**: Easy migration from Jest[^9] with familiar syntax
- **Built-in coverage**: Native V8 coverage support without additional configuration
- **Fast watch mode**: Near-instant test re-runs on file changes

```bash
# Install
npm install --save-dev vitest

# Run
npx vitest

# Parallel (threads)
npx vitest --pool=threads

# Watch mode
npx vitest --watch
```

### Configuration

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    pool: 'threads',
    poolOptions: {
      threads: {
        minThreads: 1,
        maxThreads: 4,
      },
    },
  },
});
```

## Pre-commit Configuration

```yaml
repos:
  - repo: https://github.com/biomejs/pre-commit
    rev: v0.6.0
    hooks:
      - id: biome-check
        additional_dependencies: ['@biomejs/biome@1.9.4']
```

## CI Pipeline

```yaml
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
```

## Dependencies & Package Management

Projects **SHOULD** prefer pnpm[^10] for package management due to its speed and disk efficiency:

```bash
# Prefer pnpm for speed
pnpm install
pnpm add express
pnpm add -D @types/express
```

**Lock files**: Projects **MUST** commit lock files (`package-lock.json` or
`pnpm-lock.yaml`) for reproducible builds.

**Version constraints**:

- `^1.2.3` - Compatible updates (>=1.2.3 <2.0.0)
- `~1.2.3` - Patch updates only (>=1.2.3 <1.3.0)
- `1.2.3` - Exact version (pinned)

**Vulnerability scanning**: Projects **MUST** regularly scan for vulnerabilities:

```bash
npm audit
pnpm audit
```

**Dependabot**: Projects **SHOULD** enable automated dependency updates[^11] (.github/dependabot.yml):

```yaml
version: 2
updates:
  - package-ecosystem: npm
    directory: /
    schedule:
      interval: weekly
```

## E2E & Acceptance Testing

Projects **SHOULD** use Playwright[^12] for browser E2E testing and **MAY** use
Cucumber.js[^13] for BDD-style acceptance testing.

**Playwright[^12]** for browser E2E:

```typescript
import { test, expect } from '@playwright/test';

test('user login flow', async ({ page }) => {
  await page.goto('/login');
  await page.fill('#email', 'user@example.com');
  await page.fill('#password', 'password123');
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL('/dashboard');
});
```

**Cucumber.js[^13]** for BDD acceptance:

```gherkin
Feature: User Authentication
  Scenario: Successful login
    Given I am on the login page
    When I enter valid credentials
    Then I should see the dashboard
```

```typescript
import { Given, When, Then } from '@cucumber/cucumber';

Given('I am on the login page', async function () {
  await this.page.goto('/login');
});
```

**Page Object Pattern**: Projects **SHOULD** use the Page Object Pattern for maintainable E2E tests:

```typescript
class LoginPage {
  constructor(private page: Page) {}

  async login(email: string, password: string) {
    await this.page.fill('#email', email);
    await this.page.fill('#password', password);
    await this.page.click('button[type="submit"]');
  }
}
```

## Thread Safety Testing

**Web Workers**:

```typescript
test('worker communication', async () => {
  const worker = new Worker('./worker.ts');
  const result = await new Promise((resolve) => {
    worker.onmessage = (e) => resolve(e.data);
    worker.postMessage({ type: 'process', data: [1, 2, 3] });
  });
  expect(result).toEqual([2, 4, 6]);
});
```

**SharedArrayBuffer and Atomics**:

```typescript
test('atomic operations', () => {
  const sab = new SharedArrayBuffer(4);
  const view = new Int32Array(sab);
  Atomics.store(view, 0, 42);
  expect(Atomics.load(view, 0)).toBe(42);
});
```

**Testing async race conditions**:

```typescript
test('no race condition in concurrent updates', async () => {
  const store = new ConcurrentStore();
  await Promise.all([
    store.increment('counter'),
    store.increment('counter'),
    store.increment('counter'),
  ]);
  expect(store.get('counter')).toBe(3);
});
```

## Idempotence Testing

**Retry-safe API calls**:

```typescript
test('duplicate requests produce same result', async () => {
  const result1 = await api.createOrder({ idempotencyKey: 'key-123', items: [] });
  const result2 = await api.createOrder({ idempotencyKey: 'key-123', items: [] });
  expect(result1.id).toBe(result2.id);
});
```

**Optimistic update testing**:

```typescript
test('rollback on conflict', async () => {
  const ui = renderComponent();
  ui.updateItem(1, { name: 'New Name' }); // Optimistic
  await waitFor(() => expect(ui.getItem(1).name).toBe('Original Name')); // Rolled back
});
```

## Reliability & Resilience Testing

**AbortController**:

```typescript
test('cancellable fetch', async () => {
  const controller = new AbortController();
  const promise = fetch('/api/data', { signal: controller.signal });
  controller.abort();
  await expect(promise).rejects.toThrow('aborted');
});
```

**Timeout and retry**:

```typescript
test('retries on failure', async () => {
  let attempts = 0;
  const fn = async () => {
    attempts++;
    if (attempts < 3) throw new Error('fail');
    return 'success';
  };
  const result = await retry(fn, { maxAttempts: 3 });
  expect(result).toBe('success');
  expect(attempts).toBe(3);
});
```

**Network error simulation**:

```typescript
test('handles network errors', async () => {
  server.use(
    http.get('/api/data', () => HttpResponse.networkError())
  );
  await expect(fetchData()).rejects.toThrow();
});
```

## Compatibility Testing

**Browser compatibility** (Playwright):

```typescript
import { chromium, firefox, webkit } from '@playwright/test';

for (const browserType of [chromium, firefox, webkit]) {
  test(`works in ${browserType.name()}`, async () => {
    const browser = await browserType.launch();
    const page = await browser.newPage();
    await page.goto('/');
    await expect(page.locator('h1')).toBeVisible();
    await browser.close();
  });
}
```

**Node.js version matrix** (.github/workflows/test.yml):

```yaml
strategy:
  matrix:
    node-version: [18, 20, 22]
steps:
  - uses: actions/setup-node@v4
    with:
      node-version: ${{ matrix.node-version }}
```

**tsconfig target options**:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM"]
  }
}
```

## Internationalization Testing

**UTF-8 handling** (native):

```typescript
test('handles unicode correctly', () => {
  const text = '你好世界 🌍';
  expect(text.length).toBe(6); // Code units
  expect([...text].length).toBe(6); // Code points
});
```

**i18next[^16] testing**:

```typescript
import i18n from 'i18next';

test('translates messages', async () => {
  await i18n.init({
    lng: 'es',
    resources: {
      es: { translation: { hello: 'Hola' } },
    },
  });
  expect(i18n.t('hello')).toBe('Hola');
});
```

**RTL layout testing**:

```typescript
test('supports RTL layout', async ({ page }) => {
  await page.goto('/?lang=ar');
  const dir = await page.locator('html').getAttribute('dir');
  expect(dir).toBe('rtl');
});
```

## Data Integrity Testing

Projects **MUST** validate runtime data using schema validation libraries like Zod[^14].

**Zod[^14] schema validation**:

```typescript
import { z } from 'zod';

const UserSchema = z.object({
  email: z.string().email(),
  age: z.number().min(0),
});

test('validates user data', () => {
  expect(() => UserSchema.parse({ email: 'invalid', age: -1 })).toThrow();
  expect(UserSchema.parse({ email: 'user@example.com', age: 25 })).toEqual({
    email: 'user@example.com',
    age: 25,
  });
});
```

**API contract testing**:

```typescript
test('API response matches schema', async () => {
  const response = await fetch('/api/users/1');
  const data = await response.json();
  expect(() => UserSchema.parse(data)).not.toThrow();
});
```

## A/B Testing & Feature Flags

**Feature flag libraries** (Unleash[^15]):

```typescript
import { Unleash } from 'unleash-client';

const unleash = new Unleash({
  url: 'https://unleash.example.com/api',
  appName: 'my-app',
});

if (unleash.isEnabled('new-checkout-flow')) {
  // New implementation
}
```

**Testing both flag states**:

```typescript
test.each([
  { flag: true, expected: 'New UI' },
  { flag: false, expected: 'Old UI' },
])('renders correct UI when flag is $flag', ({ flag, expected }) => {
  vi.spyOn(featureFlags, 'isEnabled').mockReturnValue(flag);
  const ui = render(<Component />);
  expect(ui.getByText(expected)).toBeInTheDocument();
});
```

## References

[^1]: [Biome](https://biomejs.dev/) - Fast formatter and linter for JavaScript/TypeScript
[^2]: [TypeScript](https://www.typescriptlang.org/) - TypeScript official website and documentation
[^3]: [ts-prune](https://github.com/nadeesha/ts-prune) - Find unused exports in TypeScript projects
[^4]: [c8](https://github.com/bcoe/c8) - Native V8 code coverage tool
[^5]: [Vitest](https://vitest.dev/) - Next generation testing framework powered by Vite
[^6]: [ESLint](https://eslint.org/) - Pluggable linting utility for JavaScript and TypeScript
[^7]: [Prettier](https://prettier.io/) - Opinionated code formatter
[^8]: [Vite](https://vitejs.dev/) - Next generation frontend tooling
[^9]: [Jest](https://jestjs.io/) - Delightful JavaScript testing framework
[^10]: [pnpm](https://pnpm.io/) - Fast, disk space efficient package manager
[^11]: [Dependabot](https://docs.github.com/en/code-security/dependabot) - Automated dependency updates
[^12]: [Playwright](https://playwright.dev/) - End-to-end testing for modern web apps
[^13]: [Cucumber.js](https://github.com/cucumber/cucumber-js) - BDD testing framework for JavaScript
[^14]: [Zod](https://zod.dev/) - TypeScript-first schema validation library
[^15]: [Unleash](https://www.getunleash.io/) - Open-source feature management platform
[^16]: [i18next](https://www.i18next.com/) - Internationalization framework for JavaScript
[^17]: [NestJS](https://nestjs.com/) - Progressive Node.js framework for building server-side applications
[^18]: [TypeORM](https://typeorm.io/) - ORM for TypeScript and JavaScript
[^19]: [Angular](https://angular.io/) - Platform for building web applications
[^20]: [DefinitelyTyped](https://github.com/DefinitelyTyped/DefinitelyTyped) - Repository for high-quality TypeScript type definitions

## See Also

- [Testing Guide](../testing.md) - Comprehensive testing strategies and best practices
- [CI Guide](../ci.md) - Continuous integration configuration and workflows
