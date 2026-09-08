# TypeScript Style Guide

> [Doctrine](../../README.md) > [Languages](README.md) > TypeScript

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

Extends [Google TypeScript Style Guide](../../reference/google/typescript.html).

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
| Test perf | Vitest[^5] | `vitest doctor` |

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
# Install (exact version)
npm install --save-dev --save-exact @biomejs/biome@2.5.12

# Initialize config
npx biome init

# Lint and format
npx biome check --write .

# CI mode
npx biome ci .

# Update an older configuration after a Biome upgrade
npx biome migrate --write
```

Projects **MUST** pin Biome to an exact version. Biome validates `biome.json`
against the schema version recorded in `$schema` and rejects unknown keys, so a
floating install silently pairs a new binary with an old configuration and fails
the whole run.

### Configuration (biome.json)

The schema version **MUST** match the installed Biome version. Biome 2 moved
import sorting out of the linter into the assist actions, so `organizeImports`
at the top level is now an unknown key and is a fatal configuration error.
Biome 2.5 also replaced `linter.rules.recommended` with `linter.rules.preset`.

```json
{
  "$schema": "https://biomejs.dev/schemas/2.5.12/schema.json",
  "assist": {
    "enabled": true,
    "actions": {
      "source": {
        "organizeImports": "on"
      }
    }
  },
  "linter": {
    "enabled": true,
    "rules": {
      "preset": "recommended",
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

Projects **MAY** use ESLint[^6] for projects requiring extensive plugin ecosystems.

ESLint 10 removed `.eslintrc.*` support entirely: the only configuration format
is flat config in `eslint.config.*`. An eslintrc-style object with `parser`,
`plugins`, `extends`, and `parserOptions` is not read at all, and ESLint exits
with "couldn't find an eslint.config.* file".

typescript-eslint 8.70.0 declares `peerDependencies.typescript` as
`>=4.8.4 <6.1.0`, so it **MUST NOT** be installed alongside TypeScript 7.
Projects that need ESLint **MUST** stay on TypeScript 6.0.3 until
typescript-eslint publishes a release that accepts TypeScript 7; installing with
`--force` or `--legacy-peer-deps` produces a parser running against an
unsupported compiler API.

```bash
npm install --save-dev --save-exact \
  eslint@10.10.0 typescript-eslint@8.70.0 @eslint/js@10.0.1 typescript@6.0.3
```

```javascript
// eslint.config.mjs
import eslint from '@eslint/js';
import tseslint from 'typescript-eslint';

export default tseslint.config(
  eslint.configs.recommended,
  tseslint.configs.strictTypeChecked,
  tseslint.configs.stylisticTypeChecked,
  {
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
  },
  { ignores: ['dist/', 'eslint.config.mjs'] },
);
```

`projectService: true` replaces `parserOptions.project`: it lets the parser ask
the TypeScript project service for each file's program instead of requiring
every linted file to be listed in a `tsconfig.json` `include`.

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

TypeScript implements two decorator systems and a project **MUST** choose
exactly one for the whole program. They are not interoperable.

| Mode | Compiler flags | Decorator signature | Parameter decorators |
| ---- | -------------- | ------------------- | -------------------- |
| Standard (TC39, TypeScript 5.0+) | none | `(target, context)` | Not supported |
| Legacy (experimental) | `experimentalDecorators` | `(target, key, descriptor)` | Supported |

#### Why the modes must be kept apart

`experimentalDecorators` is a program-wide switch, not a per-file opt-in.
Compiling the standard-decorator examples below under that flag makes the
compiler reject every one of them with TS1238, TS1240, TS1241, TS1270, and
TS1271. `emitDecoratorMetadata` **MUST NOT** be enabled outside legacy mode: it
is only implemented for the experimental system and has no standard equivalent.

Standard decorators (`tsconfig.json`) — no decorator flags at all:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "strict": true
  }
}
```

Legacy decorators (`tsconfig.json`) — required by NestJS[^17], TypeORM[^18],
and Angular[^19]:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "strict": true,
    "experimentalDecorators": true,
    "emitDecoratorMetadata": true
  }
}
```

#### Running decorated code under Vitest

Vite[^8] 8's oxc transform implements legacy decorators only, auto-detected from
`tsconfig.json`. Standard-decorator sources reach Node untransformed and fail
with `SyntaxError`, so projects on standard decorators **MUST** compile with
`tsc` before running Vitest[^5]:

```bash
npx tsc -p tsconfig.json && npx vitest run dist
```

### Class Decorators

Standard mode. A class decorator receives the class and a
`ClassDecoratorContext`, and **MAY** return a replacement class.

```typescript
function Singleton<T extends new (...args: any[]) => object>(
  target: T,
  _context: ClassDecoratorContext,
) {
  let instance: InstanceType<T> | undefined;
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
  constructor(readonly url: string) {}
}

// Same instance; the second constructor's arguments are discarded
const db1 = new Database('postgres://...');
const db2 = new Database('mysql://...');
console.log(db1 === db2); // true
console.log(db2.url); // 'postgres://...'
```

### Method Decorators

Standard mode. Type the wrapper generically so the decorated method keeps its
signature; `any` erases the return type at every call site.

```typescript
function Log<This, Args extends unknown[], Return>(
  target: (this: This, ...args: Args) => Return,
  context: ClassMethodDecoratorContext<This, (this: This, ...args: Args) => Return>,
) {
  const methodName = String(context.name);
  return function (this: This, ...args: Args): Return {
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

### Accessor Decorators

Standard mode. Validation **MUST** be applied through an accessor decorator, not
a field decorator. A field decorator's initialiser runs once, so it cannot see
any later assignment.

**Don't** — validates only the declared initial value:

```typescript
function Validate(min: number, max: number) {
  return function (_target: undefined, _context: ClassFieldDecoratorContext) {
    return function (initialValue: number): number {
      if (initialValue < min || initialValue > max) throw new Error('out of range');
      return initialValue;
    };
  };
}

class Product {
  @Validate(0, 100)
  quantity = 10;
}

const p = new Product();
p.quantity = 5000; // accepted: the decorator never runs again
```

**Do** — `accessor` gives the decorator both `init` and `set`:

```typescript
function Range(min: number, max: number) {
  return function <This>(
    target: ClassAccessorDecoratorTarget<This, number>,
    context: ClassAccessorDecoratorContext<This, number>,
  ): ClassAccessorDecoratorResult<This, number> {
    const name = String(context.name);
    const check = (value: number): number => {
      if (!Number.isFinite(value) || value < min || value > max) {
        throw new RangeError(`${name} must be between ${min} and ${max}`);
      }
      return value;
    };
    return {
      get(this: This) {
        return target.get.call(this);
      },
      set(this: This, value: number) {
        target.set.call(this, check(value));
      },
      init: check,
    };
  };
}

class Product {
  @Range(0, 100) accessor quantity = 10;
}

const p = new Product();
p.quantity = 5000; // throws RangeError
```

### Legacy Decorators (NestJS, TypeORM)

These are framework-provided legacy decorators, not standard ones. They **MUST**
be compiled with the legacy `tsconfig.json` shown above; the standard decorators
in this guide **MUST NOT** appear in the same program.

```typescript
// Requires "experimentalDecorators": true and "emitDecoratorMetadata": true
import { Controller, Get, Injectable } from '@nestjs/common';
import { Column, Entity, PrimaryGeneratedColumn } from 'typeorm';

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
  id!: number;

  @Column()
  name!: string;
}

// Dependency injection: parameter decorators exist only in legacy mode
@Injectable()
class UserService {
  constructor(private readonly repo: UserRepository) {}
}
```

### Decorator Patterns

Standard mode. Cross-cutting decorators change the lifetime and failure
semantics of every method they wrap, so each one **MUST** state its cache scope,
key derivation, and error classification explicitly.

#### Memoisation

A memoisation decorator **MUST** scope its cache per instance and **MUST** take
an explicit key function. A module-level `Map` keyed by `JSON.stringify(args)`
shares one entry across every instance, so a receiver-dependent method returns
another object's result; `JSON.stringify` also throws on `BigInt` and cyclic
arguments and maps `undefined` onto `null`.

A memoised method **MUST NOT** return a single-use value such as a `Response`,
a `ReadableStream`, or an iterator: the second caller receives an already
consumed object.

```typescript
function Memoize<This extends object, Args extends unknown[], Return>(
  keyOf: (...args: Args) => string,
) {
  return function (
    target: (this: This, ...args: Args) => Return,
    _context: ClassMethodDecoratorContext<This, (this: This, ...args: Args) => Return>,
  ) {
    const caches = new WeakMap<This, Map<string, Return>>();
    return function (this: This, ...args: Args): Return {
      let cache = caches.get(this);
      if (!cache) {
        cache = new Map<string, Return>();
        caches.set(this, cache);
      }
      const key = keyOf(...args);
      if (cache.has(key)) return cache.get(key) as Return;
      const result = target.call(this, ...args);
      cache.set(key, result);
      // A rejected promise must not be cached, or the failure is permanent
      if (result instanceof Promise) {
        void result.catch(() => cache.delete(key));
      }
      return result;
    };
  };
}
```

#### Retry

A retry decorator **MUST** retry only classified transient failures on
idempotent operations, **MUST** back off between attempts, and **MUST** honour
an `AbortSignal`. Retrying every exception immediately turns a permanent
`TypeError` into `n` synchronous failures and makes cancellation impossible.

```typescript
function sleep(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) {
      reject(signal.reason);
      return;
    }
    const onAbort = () => {
      clearTimeout(timer);
      reject(signal?.reason);
    };
    const timer = setTimeout(() => {
      signal?.removeEventListener('abort', onAbort);
      resolve();
    }, ms);
    signal?.addEventListener('abort', onAbort, { once: true });
  });
}

interface RetryOptions<This> {
  attempts: number;
  baseDelayMs: number;
  maxDelayMs: number;
  isTransient: (error: unknown) => boolean;
  signal?: (this: This) => AbortSignal | undefined;
}

function Retry<This, Args extends unknown[], Return>(options: RetryOptions<This>) {
  return function (
    target: (this: This, ...args: Args) => Promise<Return>,
    _context: ClassMethodDecoratorContext<This, (this: This, ...args: Args) => Promise<Return>>,
  ) {
    return async function (this: This, ...args: Args): Promise<Return> {
      for (let attempt = 1; ; attempt += 1) {
        const signal = options.signal?.call(this);
        signal?.throwIfAborted();
        try {
          return await target.call(this, ...args);
        } catch (error) {
          if (attempt >= options.attempts || !options.isTransient(error)) throw error;
          const backoff = Math.min(options.maxDelayMs, options.baseDelayMs * 2 ** (attempt - 1));
          await sleep(backoff * (0.5 + Math.random() / 2), signal);
        }
      }
    };
  };
}
```

#### Composing them

Decorators apply bottom-up, so `@Retry` wraps the method and `@Memoize` caches
the fully retried result. The method returns parsed data rather than the
`Response` itself, because a `Response` body can only be read once.

```typescript
class HttpError extends Error {
  constructor(readonly status: number) {
    super(`HTTP ${status}`);
  }
}

interface User {
  id: string;
  name: string;
}

class ApiClient {
  readonly #controller = new AbortController();

  @Memoize<ApiClient, [string], Promise<User>>((id) => id)
  @Retry<ApiClient, [string], User>({
    attempts: 3,
    baseDelayMs: 100,
    maxDelayMs: 2_000,
    isTransient: (error) => error instanceof HttpError && error.status >= 500,
    signal() {
      return this.#controller.signal;
    },
  })
  async fetchUser(id: string): Promise<User> {
    const response = await fetch(`https://api.example.com/users/${id}`, {
      signal: this.#controller.signal,
    });
    if (!response.ok) throw new HttpError(response.status);
    return (await response.json()) as User;
  }

  cancel(): void {
    this.#controller.abort();
  }
}
```

#### Required tests

These are the cases that distinguish a correct implementation from the
plausible-looking one it replaces, so a project using these patterns **MUST**
cover all of them:

```typescript
import { expect, test } from 'vitest';
import { Memoize, Product, Retry } from '../patterns.js';

test('accessor decorator validates assignment, not just initialisation', () => {
  const p = new Product();
  expect(p.quantity).toBe(10);
  expect(() => {
    p.quantity = 500;
  }).toThrow(RangeError);
  p.quantity = 50;
  expect(p.quantity).toBe(50);
});

class Counter {
  calls = 0;

  @Memoize<Counter, [string], string>((k) => k)
  lookup(key: string): string {
    this.calls += 1;
    return `${key}:${this.calls}`;
  }
}

test('memoisation is per instance', () => {
  const a = new Counter();
  const b = new Counter();
  expect(a.lookup('x')).toBe('x:1');
  expect(a.lookup('x')).toBe('x:1');
  expect(a.calls).toBe(1);
  expect(b.lookup('x')).toBe('x:1');
  expect(b.calls).toBe(1);
});

class Flaky {
  attempts = 0;

  @Memoize<Flaky, [], Promise<string>>(() => 'only')
  async load(): Promise<string> {
    this.attempts += 1;
    if (this.attempts === 1) throw new Error('boom');
    return 'ok';
  }
}

test('a rejected promise is evicted from the cache', async () => {
  const f = new Flaky();
  await expect(f.load()).rejects.toThrow('boom');
  await expect(f.load()).resolves.toBe('ok');
  expect(f.attempts).toBe(2);
});

class Transient extends Error {}

class Service {
  attempts = 0;
  readonly controller = new AbortController();

  @Retry<Service, [], string>({
    attempts: 5,
    baseDelayMs: 1,
    maxDelayMs: 4,
    isTransient: (error) => error instanceof Transient,
    signal() {
      return this.controller.signal;
    },
  })
  async run(): Promise<string> {
    this.attempts += 1;
    if (this.attempts < 3) throw new Transient('retry me');
    return 'done';
  }

  @Retry<Service, [], string>({
    attempts: 5,
    baseDelayMs: 1,
    maxDelayMs: 4,
    isTransient: (error) => error instanceof Transient,
  })
  async fatal(): Promise<string> {
    this.attempts += 1;
    throw new TypeError('not transient');
  }
}

test('retries only classified transient failures', async () => {
  const s = new Service();
  await expect(s.run()).resolves.toBe('done');
  expect(s.attempts).toBe(3);
});

test('a non-transient error is not retried', async () => {
  const s = new Service();
  await expect(s.fatal()).rejects.toThrow(TypeError);
  expect(s.attempts).toBe(1);
});

test('an aborted signal stops the retry loop', async () => {
  const s = new Service();
  s.controller.abort(new Error('cancelled'));
  await expect(s.run()).rejects.toThrow('cancelled');
  expect(s.attempts).toBe(0);
});
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

Ambient module declarations and global augmentations **MUST NOT** share a file.
A `declare global` block is only legal when it is directly nested in an external
module — a file with a top-level `import` or `export`. Combining it with a
script-style `declare module 'mylib'` block fails with TS2669, and adding
`export {}` to fix that would silently turn the `mylib` declaration into an
augmentation of an existing module instead of a new one.

A script-style ambient module declaration, `types/mylib.d.ts`:

```typescript
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
```

Global augmentation in its own external-module file, `types/globals.d.ts`. The
`export {}` is what makes the file a module and the `declare global` block legal:

```typescript
export {};

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
```

Module augmentation in its own external-module file, `types/express.d.ts`. The
`import` both makes the file a module and pins the augmentation to the real
package:

```typescript
import 'express';

declare module 'express' {
  interface Request {
    userId?: string;
    sessionId?: string;
  }
}
```

### Package Type Declarations

`package.json` is strict JSON: it **MUST NOT** contain comments, so the filename
label stays out of the file. The following is the complete contents of
`package.json`:

```json
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

TypeScript 7 removed `moduleResolution: "node10"` together with its `"Node"`
alias, and rejects the option with TS5108. Projects targeting Node **MUST** use
`NodeNext`; projects whose modules are resolved by a bundler **MUST** use
`Bundler`.

### Modern Node.js (Recommended)

`tsconfig.json` for Node.js 16+:

```json
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

`tsconfig.json` for bundler environments:

```json
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

`paths` only affects how **TypeScript** resolves a specifier. `tsc` emits the
specifier unchanged, so an alias **MUST NOT** be used unless something in the
pipeline implements the identical mapping at run time. Emitting
`import { formatDate } from '@utils/date.js'` and running it under Node fails
with `ERR_MODULE_NOT_FOUND`.

TypeScript 7 also removed `baseUrl` (TS5102) and now requires every `paths`
target to be relative to the config file (TS5090).

**Bundler applications** — declare the alias twice, once for the type checker
and once for the bundler, and keep the two in step:

```json
{
  "compilerOptions": {
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "noEmit": true,
    "paths": {
      "@/*": ["./src/*"],
      "@utils/*": ["./src/utils/*"]
    }
  }
}
```

```typescript
// vite.config.ts
import { fileURLToPath, URL } from 'node:url';
import { defineConfig } from 'vite';

export default defineConfig({
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      '@utils': fileURLToPath(new URL('./src/utils', import.meta.url)),
    },
  },
});
```

**Node applications** — use package subpath imports instead. Node implements
`#`-prefixed specifiers natively, and TypeScript resolves them through the same
`package.json` field, so no second mapping can drift:

```typescript
import { formatDate } from '#utils/date';
```

See [Subpath Imports](#subpath-imports) below for the matching `package.json`.

### Package.json Exports

The following is the complete contents of `package.json`:

```json
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

Import targets **MUST** point at the emitted files, not the sources.
TypeScript maps the emitted path back to its input through `outDir` and
`rootDir`, so both the compiler and Node resolve the same specifier.

A conditional target **MUST** end in a `"default"` branch. `development` and
`production` are user conditions: Node only applies them when they are passed
with `node --conditions`, and setting `NODE_ENV` has no effect on package
resolution. Without a `default`, `#config` fails with
`ERR_PACKAGE_IMPORT_NOT_DEFINED`.

The following is the complete contents of `package.json`:

```json
{
  "name": "my-app",
  "type": "module",
  "imports": {
    "#utils/*": "./dist/utils/*.js",
    "#components/*": "./dist/components/*.js",
    "#config": {
      "development": "./dist/config/dev.js",
      "default": "./dist/config/prod.js"
    }
  }
}
```

Declare the same user condition for the type checker with `customConditions`,
which requires `moduleResolution: "NodeNext"` or `"Bundler"`:

```json
{
  "compilerOptions": {
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "outDir": "./dist",
    "rootDir": "./src",
    "customConditions": ["development"]
  }
}
```

```typescript
// Use subpath imports (private to package)
import config from '#config';
import { logger } from '#utils/logger';
```

```bash
# Production: resolves the "default" branch
node dist/main.js

# Development: the condition must be requested explicitly
node --conditions=development dist/main.js
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
npm install --save-dev --save-exact vitest@5.0.0

# Run
npx vitest

# Watch mode
npx vitest --watch

# Report the environment and configuration Vitest actually resolved
npx vitest doctor
```

### Configuration

Vitest 5 removed `poolOptions`. Worker concurrency is now controlled by the
top-level `maxWorkers` and `fileParallelism` options.

The default pool is `forks`, which isolates each test file in its own child
process. `threads` is still supported and is faster for CPU-bound suites, but it
shares one process, so a test that mutates global state or leaks a native handle
can corrupt unrelated files. Projects **MUST NOT** switch pools without a
measurement from `vitest doctor` or a timed comparison showing the gain.

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    // 'forks' is the default; measure before overriding it
    pool: 'forks',
    maxWorkers: 4,
    fileParallelism: true,
  },
});
```

## Pre-commit Configuration

The hook repository is tagged in lockstep with the Biome[^1] release, so `rev`
**MUST** match the pinned `@biomejs/biome` version:

```yaml
repos:
  - repo: https://github.com/biomejs/pre-commit
    rev: v2.5.12
    hooks:
      - id: biome-check
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

Node's `fetch` has no origin, so a relative specifier such as `/api/data`
rejects with `TypeError: Failed to parse URL` before any request is made. Tests
in the default Node environment **MUST** use an absolute URL and **MUST**
install a request mock, otherwise an assertion on cancellation or on a response
body passes or fails for the wrong reason.

**MSW server lifecycle** (shared by the tests below):

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    setupFiles: ['./test/setup.ts'],
  },
});
```

```typescript
// test/server.ts
import { setupServer } from 'msw/node';

export const server = setupServer();
```

```typescript
// test/setup.ts
import { afterAll, afterEach, beforeAll } from 'vitest';
import { server } from './server.js';

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

**AbortController**:

```typescript
import { delay, http, HttpResponse } from 'msw';
import { expect, test } from 'vitest';
import { server } from './server.js';

const BASE_URL = 'https://api.example.test';

test('cancelling an in-flight request rejects with AbortError', async () => {
  server.use(
    http.get(`${BASE_URL}/data`, async () => {
      await delay('infinite');
      return HttpResponse.json({});
    }),
  );
  const controller = new AbortController();
  const promise = fetch(`${BASE_URL}/data`, { signal: controller.signal });
  controller.abort();
  await expect(promise).rejects.toMatchObject({ name: 'AbortError' });
});
```

Assert on `name: 'AbortError'` rather than on message text: the message differs
between runtimes and between an explicit `abort()` and a timeout.

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

**Network error simulation**: MSW[^21] produces a Fetch network error with
`HttpResponse.error()`. There is no `HttpResponse.networkError()`.

```typescript
test('handles network errors', async () => {
  server.use(http.get(`${BASE_URL}/data`, () => HttpResponse.error()));
  await expect(fetch(`${BASE_URL}/data`)).rejects.toThrow(TypeError);
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

**UTF-8 handling** (native): `String.prototype.length` counts UTF-16 code
units, so the astral-plane 🌍 counts as two. Iteration yields code points, and
neither figure matches user-perceived characters — combining marks, emoji
sequences, and Hangul jamo all span several code points. Use `Intl.Segmenter`
whenever the answer is meant to be "how many characters would a reader see".

```typescript
test('handles unicode correctly', () => {
  const text = '你好世界 🌍';
  expect(text.length).toBe(7); // UTF-16 code units: 🌍 is a surrogate pair
  expect([...text].length).toBe(6); // Code points
  const segmenter = new Intl.Segmenter('en', { granularity: 'grapheme' });
  expect([...segmenter.segment(text)].length).toBe(6); // Grapheme clusters
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

**API contract testing**: the request **MUST** be mocked and the URL absolute,
or the test fails on URL parsing before the schema is ever exercised.

```typescript
test('API response matches schema', async () => {
  server.use(
    http.get(`${BASE_URL}/users/1`, () =>
      HttpResponse.json({ email: 'user@example.com', age: 25 }),
    ),
  );
  const response = await fetch(`${BASE_URL}/users/1`);
  expect(response.ok).toBe(true);
  expect(UserSchema.parse(await response.json())).toEqual({
    email: 'user@example.com',
    age: 25,
  });
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
[^21]: [MSW](https://mswjs.io/) - API mocking library for browser and Node.js

## See Also

- [Testing Guide](../process/testing.md) - Comprehensive testing strategies and best practices
- [CI Guide](../process/ci.md) - Continuous integration configuration and workflows
