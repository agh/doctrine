# Next.js Style Guide

> [Doctrine](../../README.md) > [Frameworks](../README.md) > Next.js

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119][rfc2119].

[rfc2119]: https://datatracker.ietf.org/doc/html/rfc2119

Extends [TypeScript style guide](../languages/typescript.md) with Next.js-specific conventions.

**Target Version**: Next.js 15+ with App Router and React 19

## Quick Reference

All TypeScript tooling applies. Additional Next.js-specific tools:

| Task | Tool | Command |
| ---- | ---- | ------- |
| Install | npm/pnpm/yarn | `npx create-next-app@latest` |
| Run dev | Next.js | `npm run dev` |
| Build | Next.js | `npm run build` |
| Bundler | Turbopack[^1] | `next dev --turbo` |
| Test | Vitest[^2] + Testing Library[^3] | `vitest` |
| E2E | Playwright[^4] | `playwright test` |
| Lint | ESLint + next plugin[^5] | `next lint` |

## Why Next.js?

Next.js[^6] is a full-stack React framework with server-side rendering, static site generation,
and built-in optimizations for production applications.

**Key advantages**:

- Server and Client Components for optimal performance
- Built-in routing with file-based conventions
- Automatic code splitting and image optimization
- Full-stack capabilities with Server Actions
- Zero-config TypeScript support
- Excellent developer experience with Fast Refresh

Use Next.js for React applications requiring SEO, server rendering, or full-stack features. For
client-only SPAs, consider Vite + React. For static sites, consider Astro.

## Project Structure

Projects **MUST** use the App Router directory structure:

```text
my-app/
├── app/
│   ├── layout.tsx              # Root layout
│   ├── page.tsx                # Home page
│   ├── globals.css
│   ├── (marketing)/            # Route group (URL-less)
│   │   ├── about/
│   │   │   └── page.tsx
│   │   └── layout.tsx
│   ├── dashboard/
│   │   ├── page.tsx
│   │   ├── loading.tsx         # Loading UI
│   │   ├── error.tsx           # Error boundary
│   │   └── settings/
│   │       └── page.tsx
│   └── api/
│       └── users/
│           └── route.ts        # API route handler
├── components/
│   ├── ui/                     # Reusable UI components
│   │   ├── button.tsx
│   │   └── card.tsx
│   └── features/               # Feature-specific components
│       └── user-profile.tsx
├── lib/
│   ├── db.ts                   # Database client
│   ├── actions.ts              # Server Actions
│   └── utils.ts                # Utilities
├── public/
│   ├── images/
│   └── fonts/
├── middleware.ts               # Edge middleware
├── next.config.ts
├── tsconfig.json
└── package.json
```

**Why**: The App Router co-locates routes with their components, making the file system the API.
Route groups organize pages without affecting URLs, and special files (`loading.tsx`,
`error.tsx`) provide consistent UX patterns.

## File-Based Routing

Routes **MUST** be defined using the file system conventions:

```tsx
// app/page.tsx - Home page at /
export default function HomePage() {
  return <h1>Home</h1>;
}

// app/blog/page.tsx - Blog index at /blog
export default function BlogPage() {
  return <h1>Blog</h1>;
}

// app/blog/[slug]/page.tsx - Dynamic route at /blog/:slug
export default function BlogPostPage({
  params,
}: {
  params: { slug: string };
}) {
  return <h1>Post: {params.slug}</h1>;
}

// app/blog/[...slug]/page.tsx - Catch-all route at /blog/*
export default function BlogCatchAll({
  params,
}: {
  params: { slug: string[] };
}) {
  return <h1>Path: {params.slug.join('/')}</h1>;
}
```

**Why**: File-based routing eliminates routing configuration, makes page discovery intuitive,
and enables automatic code splitting per route.

## Route Groups and Parallel Routes

Projects **SHOULD** use route groups for organization:

```text
app/
├── (marketing)/
│   ├── layout.tsx        # Marketing layout
│   ├── about/page.tsx
│   └── pricing/page.tsx
├── (app)/
│   ├── layout.tsx        # App layout (with auth)
│   ├── dashboard/page.tsx
│   └── settings/page.tsx
└── @modal/               # Parallel route (named slot)
    └── login/page.tsx
```

```tsx
// app/(app)/layout.tsx - Layout for app routes
export default function AppLayout({
  children,
  modal,
}: {
  children: React.ReactNode;
  modal: React.ReactNode;
}) {
  return (
    <div>
      <nav>App Navigation</nav>
      {children}
      {modal}
    </div>
  );
}
```

**Why**: Route groups organize files without adding URL segments. Parallel routes enable advanced
patterns like modals, split views, and conditional rendering.

## Server vs Client Components

Components **MUST** be Server Components by default. Client Components **MUST** be explicitly
marked with `'use client'`.

```tsx
// app/components/user-profile.tsx - Server Component (default)
import { getUser } from '@/lib/db';

export default async function UserProfile({ userId }: { userId: string }) {
  const user = await getUser(userId); // Direct database access

  return (
    <div>
      <h2>{user.name}</h2>
      <p>{user.email}</p>
    </div>
  );
}
```

```tsx
// app/components/counter.tsx - Client Component
'use client';

import { useState } from 'react';

export default function Counter() {
  const [count, setCount] = useState(0);

  return (
    <button onClick={() => setCount(count + 1)}>
      Count: {count}
    </button>
  );
}
```

### When to Use Each

| Use Server Components for | Use Client Components for |
| ------------------------- | ------------------------- |
| Data fetching | Interactivity (onClick, onChange) |
| Backend resources access | State (useState, useReducer) |
| Sensitive data (API keys) | Effects (useEffect, useLayoutEffect) |
| Large dependencies | Browser APIs (localStorage, window) |
| SEO-critical content | Event listeners |

**Why**: Server Components reduce JavaScript bundle size, enable direct backend access, and
improve initial page load. Client Components provide interactivity where needed without forcing
the entire app client-side.

## Partial Prerendering (PPR)

Next.js 15 introduces Partial Prerendering[^ppr], which combines static and dynamic rendering in
a single route. Projects **SHOULD** enable PPR for optimal performance:

```typescript
// next.config.ts
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  experimental: {
    ppr: 'incremental',  // Enable per-route
  },
};

export default nextConfig;
```

Mark individual routes for PPR:

```tsx
// app/dashboard/page.tsx
export const experimental_ppr = true;

import { Suspense } from 'react';
import { UserGreeting } from './user-greeting';
import { RecentActivity } from './recent-activity';

// Static shell renders immediately, dynamic parts stream in
export default function Dashboard() {
  return (
    <div>
      <h1>Dashboard</h1>  {/* Static - instant */}

      <Suspense fallback={<div>Loading user...</div>}>
        <UserGreeting />  {/* Dynamic - streams in */}
      </Suspense>

      <Suspense fallback={<div>Loading activity...</div>}>
        <RecentActivity />  {/* Dynamic - streams in */}
      </Suspense>
    </div>
  );
}
```

**Why PPR**: Traditional SSR waits for all data before sending HTML. PPR sends a static shell
instantly (best TTFB) while streaming dynamic content as it resolves. This provides the speed
of static sites with the personalization of dynamic pages.

## Data Fetching in Server Components

Server Components **MUST** fetch data using async/await:

```tsx
// app/blog/[slug]/page.tsx
import { notFound } from 'next/navigation';
import { getPost } from '@/lib/db';

export default async function BlogPost({
  params,
}: {
  params: { slug: string };
}) {
  const post = await getPost(params.slug);

  if (!post) {
    notFound(); // Renders 404 page
  }

  return (
    <article>
      <h1>{post.title}</h1>
      <p>{post.content}</p>
    </article>
  );
}

// Generate static params at build time
export async function generateStaticParams() {
  const posts = await getAllPosts();
  return posts.map((post) => ({ slug: post.slug }));
}
```

### Request Deduplication

Next.js automatically deduplicates identical `fetch` requests:

```tsx
// These three fetches result in only ONE network request
async function Header() {
  const user = await fetch('/api/user').then(r => r.json());
  return <div>{user.name}</div>;
}

async function Sidebar() {
  const user = await fetch('/api/user').then(r => r.json());
  return <div>{user.email}</div>;
}

async function Content() {
  const user = await fetch('/api/user').then(r => r.json());
  return <div>{user.bio}</div>;
}
```

**Why**: Request deduplication prevents waterfall fetching and redundant network calls,
improving performance without manual caching logic.

## Fetch Caching and Revalidation

Projects **MUST** configure caching behavior explicitly:

```tsx
// Static data (cached indefinitely)
const response = await fetch('https://api.example.com/data');

// Revalidate every 60 seconds
const response = await fetch('https://api.example.com/data', {
  next: { revalidate: 60 },
});

// Never cache (always fresh)
const response = await fetch('https://api.example.com/data', {
  cache: 'no-store',
});

// Revalidate on-demand via tag
const response = await fetch('https://api.example.com/data', {
  next: { tags: ['posts'] },
});
```

```tsx
// app/actions.ts - Revalidate tagged data
'use server';

import { revalidateTag, revalidatePath } from 'next/cache';

export async function updatePost(id: string) {
  await db.posts.update({ id });
  revalidateTag('posts'); // Revalidate all fetches tagged 'posts'
  revalidatePath('/blog'); // Revalidate /blog route
}
```

**Why**: Explicit cache control balances performance with data freshness. Tag-based revalidation
enables surgical cache invalidation without rebuilding the entire site.

## Server Actions

Projects **SHOULD** use Server Actions for mutations:

```tsx
// app/actions.ts
'use server';

import { revalidatePath } from 'next/cache';
import { db } from '@/lib/db';
import { z } from 'zod';

const createPostSchema = z.object({
  title: z.string().min(1).max(100),
  content: z.string().min(1),
});

export async function createPost(formData: FormData) {
  const parsed = createPostSchema.parse({
    title: formData.get('title'),
    content: formData.get('content'),
  });

  const post = await db.posts.create({
    data: parsed,
  });

  revalidatePath('/blog');
  return { success: true, postId: post.id };
}
```

```tsx
// app/blog/new/page.tsx
import { createPost } from '@/app/actions';

export default function NewPostPage() {
  return (
    <form action={createPost}>
      <input name="title" required />
      <textarea name="content" required />
      <button type="submit">Create Post</button>
    </form>
  );
}
```

### Progressive Enhancement

Server Actions work without JavaScript:

```tsx
// With useFormStatus for loading states
'use client';

import { useFormStatus } from 'react-dom';

function SubmitButton() {
  const { pending } = useFormStatus();

  return (
    <button type="submit" disabled={pending}>
      {pending ? 'Creating...' : 'Create Post'}
    </button>
  );
}

export default function NewPostForm({ action }) {
  return (
    <form action={action}>
      <input name="title" required />
      <SubmitButton />
    </form>
  );
}
```

**Why**: Server Actions eliminate the need for API routes for simple mutations, provide type
safety, and work without client-side JavaScript (progressive enhancement).

## Middleware

Projects **SHOULD** use middleware for cross-cutting concerns:

```ts
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  // Authentication redirect
  const token = request.cookies.get('auth-token');

  if (!token && request.nextUrl.pathname.startsWith('/dashboard')) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  // Add custom headers
  const response = NextResponse.next();
  response.headers.set('x-custom-header', 'value');

  return response;
}

// Specify which routes to run middleware on
export const config = {
  matcher: ['/dashboard/:path*', '/api/:path*'],
};
```

### Middleware Use Cases

| Use Case | Pattern |
| -------- | ------- |
| Authentication | Check tokens, redirect to login |
| Authorization | Role-based access control |
| Redirects | A/B testing, localization |
| Bot detection | User-Agent analysis |
| Rate limiting | Request throttling |

**Why**: Middleware runs on the Edge before rendering, enabling fast authentication checks,
redirects, and request modification without full server computation.

## Rate Limiting

Projects **SHOULD** use Upstash Ratelimit[^ratelimit] for serverless-compatible rate limiting:

### Why

Traditional rate limiting libraries require persistent connections and server-side state.
Upstash Ratelimit uses HTTP-based Redis, making it the only connectionless rate limiting
solution designed for serverless environments (Vercel, AWS Lambda, Cloudflare Workers).

### Edge Middleware Implementation

```bash
npm install @upstash/ratelimit @upstash/redis
```

```ts
// middleware.ts
import { Ratelimit } from '@upstash/ratelimit';
import { Redis } from '@upstash/redis';
import { NextRequest, NextResponse } from 'next/server';

const ratelimit = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(10, '10 s'), // 10 requests per 10 seconds
  analytics: true,
  prefix: '@upstash/ratelimit',
});

export async function middleware(request: NextRequest) {
  // Use IP address or authenticated user ID
  const ip = request.ip ?? request.headers.get('x-forwarded-for') ?? '127.0.0.1';
  const { success, limit, reset, remaining } = await ratelimit.limit(ip);

  if (!success) {
    return NextResponse.json(
      { error: 'Too many requests' },
      {
        status: 429,
        headers: {
          'X-RateLimit-Limit': limit.toString(),
          'X-RateLimit-Remaining': remaining.toString(),
          'X-RateLimit-Reset': reset.toString(),
        },
      }
    );
  }

  const response = NextResponse.next();
  response.headers.set('X-RateLimit-Limit', limit.toString());
  response.headers.set('X-RateLimit-Remaining', remaining.toString());
  return response;
}

export const config = {
  matcher: '/api/:path*',
};
```

### Rate Limiting Algorithms

| Algorithm | Use Case |
|-----------|----------|
| `slidingWindow(limit, window)` | Smooth rate limiting, prevents bursts |
| `tokenBucket(refillRate, maxTokens)` | Allow controlled bursts |
| `fixedWindow(limit, window)` | Simple, lowest cost |

### Multi-Region Configuration

Projects with global users **SHOULD** use regional Redis instances:

```ts
const ratelimit = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(100, '60 s'),
  // Automatically routes to nearest region
  enableProtection: true,
});
```

**Why**: Edge middleware blocks traffic before it reaches your backend, reducing costs and
protecting against abuse. Multi-region Redis minimizes latency globally.

## API Routes (Route Handlers)

Projects **MAY** use Route Handlers for API endpoints:

```ts
// app/api/users/route.ts
import { NextResponse } from 'next/server';
import { db } from '@/lib/db';

export async function GET() {
  const users = await db.users.findMany();
  return NextResponse.json(users);
}

export async function POST(request: Request) {
  const body = await request.json();
  const user = await db.users.create({ data: body });
  return NextResponse.json(user, { status: 201 });
}
```

```ts
// app/api/users/[id]/route.ts
export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  const user = await db.users.findUnique({ where: { id: params.id } });

  if (!user) {
    return NextResponse.json({ error: 'User not found' }, { status: 404 });
  }

  return NextResponse.json(user);
}

export async function DELETE(
  request: Request,
  { params }: { params: { id: string } }
) {
  await db.users.delete({ where: { id: params.id } });
  return new NextResponse(null, { status: 204 });
}
```

**Why**: Route Handlers provide REST API endpoints when needed. For form submissions and
mutations, prefer Server Actions for better type safety and progressive enhancement.

## Testing

### Unit and Integration Tests

Projects **MUST** test Server and Client Components separately:

```tsx
// components/counter.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import Counter from './counter';

describe('Counter', () => {
  it('increments count on click', () => {
    render(<Counter />);
    const button = screen.getByRole('button');

    expect(button).toHaveTextContent('Count: 0');
    fireEvent.click(button);
    expect(button).toHaveTextContent('Count: 1');
  });
});
```

```tsx
// components/user-profile.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import UserProfile from './user-profile';

vi.mock('@/lib/db', () => ({
  getUser: vi.fn().mockResolvedValue({
    name: 'John Doe',
    email: 'john@example.com',
  }),
}));

describe('UserProfile', () => {
  it('renders user data', async () => {
    render(await UserProfile({ userId: '1' }));
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('john@example.com')).toBeInTheDocument();
  });
});
```

### E2E Tests

Projects **SHOULD** use Playwright for end-to-end testing:

```ts
// e2e/auth.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('user can log in', async ({ page }) => {
    await page.goto('/login');

    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL('/dashboard');
    await expect(page.locator('h1')).toContainText('Dashboard');
  });

  test('protected route redirects to login', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL('/login');
  });
});
```

**Why**: Vitest provides fast unit testing with React Server Component support. Playwright
enables reliable E2E testing across browsers with automatic waiting and screenshot/video
recording.

## Authentication

Projects **SHOULD** use Auth.js[^authjs] (NextAuth.js v5) for authentication:

### Why

Auth.js is the standard open-source authentication library for Next.js. Version 5 is a complete
rewrite with edge-first design, App Router support, and a universal `auth()` function that
works across all Next.js contexts.

### Installation and Setup

```bash
npm install next-auth@beta @auth/core
```

```ts
// auth.ts
import NextAuth from 'next-auth';
import GitHub from 'next-auth/providers/github';
import Google from 'next-auth/providers/google';
import Credentials from 'next-auth/providers/credentials';
import { PrismaAdapter } from '@auth/prisma-adapter';
import { prisma } from '@/lib/db';

export const { handlers, auth, signIn, signOut } = NextAuth({
  adapter: PrismaAdapter(prisma),
  providers: [
    GitHub, // Uses AUTH_GITHUB_ID and AUTH_GITHUB_SECRET automatically
    Google,
    Credentials({
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' },
      },
      async authorize(credentials) {
        // Validate credentials against database
        const user = await validateUser(credentials);
        return user ?? null;
      },
    }),
  ],
  session: { strategy: 'jwt' }, // Required for Edge Runtime/middleware
  callbacks: {
    authorized({ auth, request }) {
      const isLoggedIn = !!auth?.user;
      const isProtected = request.nextUrl.pathname.startsWith('/dashboard');
      if (isProtected && !isLoggedIn) return false;
      return true;
    },
    jwt({ token, user }) {
      if (user) {
        token.role = user.role;
      }
      return token;
    },
    session({ session, token }) {
      session.user.role = token.role;
      return session;
    },
  },
});
```

```ts
// app/api/auth/[...nextauth]/route.ts
import { handlers } from '@/auth';
export const { GET, POST } = handlers;
```

### Middleware-Based Protection

```ts
// middleware.ts
import { auth } from '@/auth';

export default auth((req) => {
  const isLoggedIn = !!req.auth;
  const isAuthPage = req.nextUrl.pathname.startsWith('/login');

  if (isAuthPage && isLoggedIn) {
    return Response.redirect(new URL('/dashboard', req.nextUrl));
  }

  if (!isLoggedIn && req.nextUrl.pathname.startsWith('/dashboard')) {
    return Response.redirect(new URL('/login', req.nextUrl));
  }
});

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
```

### Using Auth in Server Components

```tsx
// app/dashboard/page.tsx
import { auth } from '@/auth';
import { redirect } from 'next/navigation';

export default async function DashboardPage() {
  const session = await auth();

  if (!session) {
    redirect('/login');
  }

  return (
    <div>
      <h1>Welcome, {session.user.name}</h1>
      <p>Role: {session.user.role}</p>
    </div>
  );
}
```

### Role-Based Access Control (RBAC)

```ts
// lib/auth-utils.ts
import { auth } from '@/auth';

type Role = 'user' | 'admin' | 'moderator';

export async function requireRole(allowedRoles: Role[]) {
  const session = await auth();

  if (!session) {
    throw new Error('Unauthorized');
  }

  if (!allowedRoles.includes(session.user.role as Role)) {
    throw new Error('Forbidden');
  }

  return session;
}
```

```tsx
// app/admin/page.tsx
import { requireRole } from '@/lib/auth-utils';

export default async function AdminPage() {
  const session = await requireRole(['admin']);

  return <AdminDashboard user={session.user} />;
}
```

### Session Strategies

| Strategy | Pros | Cons |
|----------|------|------|
| JWT | Edge-compatible, no DB lookups, horizontal scaling | Cannot revoke until expiry |
| Database | Immediate revocation, audit trail | Requires DB access, more latency |

Projects **MUST** use JWT strategy when using middleware auth checks (Edge Runtime cannot access
databases directly).

**Why**: Auth.js provides type-safe authentication with zero vendor lock-in. JWT sessions work
in Edge Runtime while database sessions enable immediate session revocation for
security-critical applications.

## Deployment

### Vercel (Recommended)

Projects deployed to Vercel[^7] **SHOULD** use automatic deployments:

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy to production
vercel --prod

# Preview deployments happen automatically on git push
```

```ts
// next.config.ts
import type { NextConfig } from 'next';

const config: NextConfig = {
  // Vercel-specific optimizations are automatic
  images: {
    formats: ['image/avif', 'image/webp'],
  },
};

export default config;
```

**Why**: Vercel provides zero-config deployments, automatic HTTPS, edge functions, and built-in
analytics. Preview deployments for every pull request enable safe testing before production.

### Self-Hosted

Projects self-hosting **MUST** use the standalone output:

```ts
// next.config.ts
const config: NextConfig = {
  output: 'standalone',
};
```

```dockerfile
# Dockerfile
FROM node:20-alpine AS base

# Dependencies
FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# Builder
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# Runner
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
```

```yaml
# docker-compose.yml
services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/myapp
    depends_on:
      - db

  db:
    image: postgres:17
    environment:
      POSTGRES_PASSWORD: pass
      POSTGRES_USER: user
      POSTGRES_DB: myapp
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

**Why**: Standalone output creates a minimal Node.js server with only required dependencies.
Docker enables consistent deployments across environments with isolated dependencies.

## Performance Optimization

### Turbopack

Projects **SHOULD** use Turbopack for faster development builds:

```json
// package.json
{
  "scripts": {
    "dev": "next dev --turbo",
    "build": "next build"
  }
}
```

**Why**: Turbopack provides 700x faster updates than Webpack in development. Production builds
still use Webpack for maximum optimization.

### Image Optimization

Projects **MUST** use Next.js Image component:

```tsx
import Image from 'next/image';

// Local images (imported)
import heroImage from '@/public/hero.jpg';

export function Hero() {
  return (
    <Image
      src={heroImage}
      alt="Hero image"
      priority // LCP optimization
      placeholder="blur" // Automatic blur placeholder
    />
  );
}

// Remote images
export function Avatar({ src }: { src: string }) {
  return (
    <Image
      src={src}
      alt="User avatar"
      width={40}
      height={40}
      // Remote images require dimensions
    />
  );
}
```

```ts
// next.config.ts
const config: NextConfig = {
  images: {
    formats: ['image/avif', 'image/webp'],
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'cdn.example.com',
      },
    ],
  },
};
```

**Why**: Next.js Image automatically optimizes images, serves modern formats (AVIF/WebP),
generates responsive sizes, and lazy loads by default.

### Font Optimization

Projects **SHOULD** use `next/font` for automatic font optimization:

```tsx
// app/layout.tsx
import { Inter, Roboto_Mono } from 'next/font/google';

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
});

const robotoMono = Roboto_Mono({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-roboto-mono',
});

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={`${inter.variable} ${robotoMono.variable}`}>
      <body>{children}</body>
    </html>
  );
}
```

```css
/* app/globals.css */
body {
  font-family: var(--font-inter), sans-serif;
}

code {
  font-family: var(--font-roboto-mono), monospace;
}
```

**Why**: `next/font` automatically self-hosts Google Fonts (eliminating external requests),
optimizes loading with CSS size-adjust, and prevents layout shift.

### Metadata and SEO

Projects **MUST** define metadata for SEO:

```tsx
// app/layout.tsx
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: {
    template: '%s | My App',
    default: 'My App',
  },
  description: 'My awesome Next.js app',
  openGraph: {
    title: 'My App',
    description: 'My awesome Next.js app',
    images: ['/og-image.jpg'],
  },
};
```

```tsx
// app/blog/[slug]/page.tsx
import type { Metadata } from 'next';

export async function generateMetadata({
  params,
}: {
  params: { slug: string };
}): Promise<Metadata> {
  const post = await getPost(params.slug);

  return {
    title: post.title,
    description: post.excerpt,
    openGraph: {
      title: post.title,
      description: post.excerpt,
      images: [post.coverImage],
    },
  };
}
```

**Why**: Next.js automatically generates SEO tags from metadata, supports dynamic per-page
metadata, and provides type safety for Open Graph and Twitter Cards.

## Real-Time Communication

Serverless platforms like Vercel **MUST NOT** use WebSockets directly (serverless functions are
ephemeral and cannot maintain persistent connections). Projects **SHOULD** use managed
real-time services:

### Why

Vercel and other serverless platforms run ephemeral functions that scale up and down. WebSocket
connections require persistent server processes. Managed services like Pusher[^pusher] and
Ably[^ably] handle connection infrastructure while your serverless functions communicate via
their APIs.

### Pusher Integration

```bash
npm install pusher pusher-js
```

```ts
// lib/pusher.ts (server-side)
import Pusher from 'pusher';

export const pusher = new Pusher({
  appId: process.env.PUSHER_APP_ID!,
  key: process.env.NEXT_PUBLIC_PUSHER_KEY!,
  secret: process.env.PUSHER_SECRET!,
  cluster: process.env.NEXT_PUBLIC_PUSHER_CLUSTER!,
  useTLS: true,
});
```

```ts
// app/api/messages/route.ts
import { pusher } from '@/lib/pusher';
import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  const { message, channelId } = await request.json();

  await pusher.trigger(`channel-${channelId}`, 'new-message', {
    message,
    timestamp: Date.now(),
  });

  return NextResponse.json({ success: true });
}
```

```tsx
// components/chat.tsx
'use client';

import { useEffect, useState } from 'react';
import PusherClient from 'pusher-js';

export function Chat({ channelId }: { channelId: string }) {
  const [messages, setMessages] = useState<string[]>([]);

  useEffect(() => {
    const pusher = new PusherClient(process.env.NEXT_PUBLIC_PUSHER_KEY!, {
      cluster: process.env.NEXT_PUBLIC_PUSHER_CLUSTER!,
    });

    const channel = pusher.subscribe(`channel-${channelId}`);
    channel.bind('new-message', (data: { message: string }) => {
      setMessages((prev) => [...prev, data.message]);
    });

    return () => {
      channel.unbind_all();
      pusher.unsubscribe(`channel-${channelId}`);
    };
  }, [channelId]);

  return (
    <ul>
      {messages.map((msg, i) => (
        <li key={i}>{msg}</li>
      ))}
    </ul>
  );
}
```

### Real-Time Service Comparison

| Service | Best For | Pricing Model |
|---------|----------|---------------|
| Pusher[^pusher] | Quick integration, simple API | Per message/connection |
| Ably[^ably] | Enterprise, presence, history | Per message |
| Supabase Realtime | PostgreSQL integration | Per project |
| Liveblocks | Collaborative features | Per user |

### Self-Hosted Alternative

For self-hosted deployments with persistent servers, Socket.IO[^socketio] **MAY** be used:

```ts
// server.ts (custom server, NOT compatible with Vercel)
import { createServer } from 'http';
import { Server } from 'socket.io';
import next from 'next';

const dev = process.env.NODE_ENV !== 'production';
const app = next({ dev });
const handle = app.getRequestHandler();

app.prepare().then(() => {
  const server = createServer((req, res) => {
    handle(req, res);
  });

  const io = new Server(server);

  io.on('connection', (socket) => {
    socket.on('message', (data) => {
      io.emit('message', data);
    });
  });

  server.listen(3000);
});
```

**Why**: Managed services handle WebSocket infrastructure, scaling, and global presence. They
integrate cleanly with serverless functions while providing reliable real-time delivery.

## Background Jobs

Projects running on serverless platforms **SHOULD** use managed background job services:

### Why

Serverless functions have execution time limits (Vercel: 10s default, 60s max on Pro).
Long-running tasks require dedicated infrastructure. Managed services like Inngest[^inngest]
and Trigger.dev[^triggerdev] handle orchestration, retries, and monitoring.

### Vercel Cron Jobs

For simple scheduled tasks, use Vercel Cron[^vercelcron]:

```json
// vercel.json
{
  "crons": [
    {
      "path": "/api/cron/daily-report",
      "schedule": "0 9 * * *"
    },
    {
      "path": "/api/cron/cleanup",
      "schedule": "0 0 * * 0"
    }
  ]
}
```

```ts
// app/api/cron/daily-report/route.ts
import { NextResponse } from 'next/server';

export async function GET(request: Request) {
  // Verify cron secret (prevent unauthorized access)
  const authHeader = request.headers.get('authorization');
  if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  await generateDailyReport();
  return NextResponse.json({ success: true });
}
```

### Inngest for Complex Workflows

```bash
npm install inngest
```

```ts
// inngest/client.ts
import { Inngest } from 'inngest';

export const inngest = new Inngest({ id: 'my-app' });
```

```ts
// inngest/functions.ts
import { inngest } from './client';

export const processOrder = inngest.createFunction(
  { id: 'process-order', retries: 3 },
  { event: 'order/created' },
  async ({ event, step }) => {
    // Step 1: Validate inventory
    const inventory = await step.run('validate-inventory', async () => {
      return await checkInventory(event.data.items);
    });

    // Step 2: Charge payment (with automatic retry)
    const payment = await step.run('charge-payment', async () => {
      return await chargePayment(event.data.paymentMethod, event.data.total);
    });

    // Step 3: Send confirmation email
    await step.run('send-confirmation', async () => {
      await sendEmail(event.data.email, {
        orderId: event.data.orderId,
        total: event.data.total,
      });
    });

    return { success: true, paymentId: payment.id };
  }
);
```

```ts
// app/api/inngest/route.ts
import { serve } from 'inngest/next';
import { inngest } from '@/inngest/client';
import { processOrder } from '@/inngest/functions';

export const { GET, POST, PUT } = serve({
  client: inngest,
  functions: [processOrder],
});
```

### Background Job Service Comparison

| Service | Best For | Vercel Compatible |
|---------|----------|-------------------|
| Vercel Cron[^vercelcron] | Simple scheduled tasks | Native |
| Inngest[^inngest] | Complex workflows, AI pipelines | Yes |
| Trigger.dev[^triggerdev] | Long-running tasks, integrations | Yes |
| BullMQ[^bullmq] | Self-hosted, Redis-based | No (needs server) |

**Why**: Managed background job services provide retries, observability, and durability. Inngest
and Trigger.dev run tasks outside your serverless function limits while integrating with your
Next.js codebase.

## Circuit Breakers

Projects calling external APIs **SHOULD** implement circuit breakers with Opossum[^opossum]:

### Why

Circuit breakers prevent cascading failures when external services are unavailable. When
failures exceed a threshold, the circuit "opens" and fails fast instead of waiting for
timeouts. This protects both your application and the failing service.

### Implementation

```bash
npm install opossum
```

```ts
// lib/circuit-breaker.ts
import CircuitBreaker from 'opossum';

const options = {
  timeout: 3000, // 3 second timeout
  errorThresholdPercentage: 50, // Open circuit when 50% of requests fail
  resetTimeout: 30000, // Try again after 30 seconds
};

async function fetchExternalApi(endpoint: string) {
  const response = await fetch(`https://api.external-service.com${endpoint}`);
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }
  return response.json();
}

export const apiBreaker = new CircuitBreaker(fetchExternalApi, options);

// Fallback when circuit is open
apiBreaker.fallback(() => ({
  data: null,
  cached: true,
  message: 'Service temporarily unavailable',
}));

// Logging
apiBreaker.on('open', () => console.log('Circuit opened'));
apiBreaker.on('halfOpen', () => console.log('Circuit half-open'));
apiBreaker.on('close', () => console.log('Circuit closed'));
```

```ts
// app/api/external-data/route.ts
import { NextResponse } from 'next/server';
import { apiBreaker } from '@/lib/circuit-breaker';

export async function GET() {
  try {
    const data = await apiBreaker.fire('/data');
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: 'Service unavailable', cached: true },
      { status: 503 }
    );
  }
}
```

### Circuit States

| State | Behavior |
|-------|----------|
| Closed | Requests pass through normally |
| Open | Requests fail immediately (no network call) |
| Half-Open | One request allowed through to test recovery |

### Serverless Considerations

```ts
// For serverless environments, initialize state from external store
const breaker = new CircuitBreaker(fetchExternalApi, {
  ...options,
  // Enable state export for serverless
  volumeThreshold: 5, // Minimum requests before opening
});

// Export/import state for serverless persistence
export async function getCircuitState() {
  return {
    state: breaker.status.stats,
    isOpen: breaker.opened,
  };
}
```

**Why**: Circuit breakers prevent your application from repeatedly calling failing services.
Opossum is the most mature Node.js circuit breaker with 70,000+ weekly downloads and serverless
support.

## Feature Flags

Projects **SHOULD** use the Vercel Flags SDK[^flagssdk] for feature flag integration:

### Why

Feature flags enable gradual rollouts, A/B testing, and kill switches. The Vercel Flags SDK
provides a framework-agnostic interface that works with any provider (LaunchDarkly, Statsig,
custom) while optimizing for Edge Runtime performance.

### Installation

```bash
npm install flags @flags-sdk/statsig  # or @flags-sdk/launchdarkly
```

### Configuration with Statsig

```ts
// flags.ts
import { flag } from 'flags/next';
import { statsigAdapter } from '@flags-sdk/statsig';

export const showNewDashboard = flag<boolean>({
  key: 'show-new-dashboard',
  adapter: statsigAdapter(),
  defaultValue: false,
  description: 'Enable the redesigned dashboard UI',
  options: [
    { value: true, label: 'Enabled' },
    { value: false, label: 'Disabled' },
  ],
});

export const pricingTier = flag<'basic' | 'premium' | 'enterprise'>({
  key: 'pricing-tier',
  adapter: statsigAdapter(),
  defaultValue: 'basic',
});
```

### Using Flags in Server Components

```tsx
// app/dashboard/page.tsx
import { showNewDashboard } from '@/flags';

export default async function DashboardPage() {
  const useNewDashboard = await showNewDashboard();

  if (useNewDashboard) {
    return <NewDashboard />;
  }

  return <LegacyDashboard />;
}
```

### Using Flags in Middleware

```ts
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { showNewDashboard } from '@/flags';

export async function middleware(request: NextRequest) {
  const useNewDashboard = await showNewDashboard();

  if (useNewDashboard && request.nextUrl.pathname === '/dashboard') {
    return NextResponse.rewrite(new URL('/dashboard-v2', request.url));
  }

  return NextResponse.next();
}
```

### Feature Flag Provider Comparison

| Provider | Best For | Free Tier |
|----------|----------|-----------|
| Statsig[^statsig] | Experimentation, analytics | Unlimited flags |
| LaunchDarkly[^launchdarkly] | Enterprise, compliance | Limited |
| Vercel Edge Config | Simple flags, fast reads | Included |
| OpenFeature | Vendor-agnostic | N/A (standard) |

### Flags with Edge Config (Fastest)

```ts
// For simple flags with minimal latency
import { get } from '@vercel/edge-config';

export async function getFeatureFlags() {
  return {
    maintenanceMode: await get('maintenance_mode'),
    newPricing: await get('new_pricing_enabled'),
  };
}
```

**Why**: The Flags SDK provides a unified interface across providers while Vercel Edge Config
bootstraps flags without network requests. This combination enables <1ms flag evaluation at the
edge.

## Static Site Generation (SSG) and ISR

Projects **SHOULD** use Static Site Generation (SSG) and Incremental Static Regeneration (ISR)
for content that doesn't change frequently.

### Why SSG and ISR

- **Performance**: Pre-rendered pages serve instantly from CDN edge nodes
- **Cost**: Reduce server compute by serving static files
- **SEO**: Complete HTML available for crawlers without JavaScript
- **Reliability**: Static pages work even if backend services fail

### Rendering Strategies Comparison

| Strategy | Build Time | User Wait | Data Freshness | Best For |
|----------|------------|-----------|----------------|----------|
| SSG | Pre-render | None | Build-time | Marketing pages, docs |
| ISR | Pre-render + revalidate | None (cache hit) | Configurable | Blogs, product pages |
| PPR | Partial pre-render | Streaming | Real-time | Dashboards, personalized |
| Dynamic | On request | Full | Real-time | Auth-required, search |

### Full Static Generation

```tsx
// app/blog/[slug]/page.tsx
// Fully static - built at build time
export async function generateStaticParams() {
  const posts = await getPosts();
  return posts.map((post) => ({
    slug: post.slug,
  }));
}

export default async function BlogPost({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const post = await getPost(slug);
  return <Article post={post} />;
}

// This page is 100% static - no server execution after build
export const dynamic = 'force-static';
```

### Incremental Static Regeneration (ISR)

```tsx
// app/products/[id]/page.tsx
// Static with time-based revalidation
export const revalidate = 3600; // Revalidate every hour

export async function generateStaticParams() {
  // Pre-generate top 100 products at build
  const products = await getTopProducts(100);
  return products.map((p) => ({ id: p.id.toString() }));
}

export default async function ProductPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  // Cached and revalidated every hour
  const product = await getProduct(id);
  return <ProductDetail product={product} />;
}

// Dynamic params (not pre-generated) will be SSR then cached
export const dynamicParams = true; // default
```

### On-Demand Revalidation

```tsx
// app/api/revalidate/route.ts
import { revalidatePath, revalidateTag } from 'next/cache';
import { NextRequest } from 'next/server';

export async function POST(request: NextRequest) {
  const { secret, path, tag } = await request.json();

  // Verify webhook secret
  if (secret !== process.env.REVALIDATION_SECRET) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 });
  }

  // Revalidate by path
  if (path) {
    revalidatePath(path);
    return Response.json({ revalidated: true, path });
  }

  // Revalidate by tag
  if (tag) {
    revalidateTag(tag);
    return Response.json({ revalidated: true, tag });
  }

  return Response.json({ error: 'No path or tag provided' }, { status: 400 });
}
```

```tsx
// lib/api.ts - Tag-based caching
export async function getProducts() {
  const res = await fetch('https://api.example.com/products', {
    next: {
      tags: ['products'],
      revalidate: 3600,
    },
  });
  return res.json();
}

export async function getProduct(id: string) {
  const res = await fetch(`https://api.example.com/products/${id}`, {
    next: {
      tags: ['products', `product-${id}`],
      revalidate: 3600,
    },
  });
  return res.json();
}
```

### ISR with fallback loading

```tsx
// app/posts/[slug]/page.tsx
import { Suspense } from 'react';
import { notFound } from 'next/navigation';

// Pre-generate some pages at build time
export async function generateStaticParams() {
  const posts = await getRecentPosts(50);
  return posts.map((post) => ({ slug: post.slug }));
}

// Generate other slugs on-demand
export const dynamicParams = true;

export default async function PostPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const post = await getPost(slug);

  if (!post) {
    notFound();
  }

  return (
    <article>
      <h1>{post.title}</h1>
      <Suspense fallback={<CommentsSkeleton />}>
        <Comments postId={post.id} />
      </Suspense>
    </article>
  );
}
```

### Static Export

```ts
// next.config.ts - Full static export (no server needed)
import type { NextConfig } from 'next';

const config: NextConfig = {
  output: 'export',
  // Optional: Change output directory
  distDir: 'out',
  // Optional: Trailing slashes for static hosts
  trailingSlash: true,
};

export default config;
```

**Why**: SSG provides the best performance and lowest cost for content that changes infrequently.
ISR adds flexibility to update content without full rebuilds, making it ideal for content-heavy
sites.

## Internationalization (i18n)

Projects with multilingual content **SHOULD** implement i18n using Next.js routing patterns and
message catalogs.

### Why i18n

- **Market reach**: Serve users in their preferred language
- **SEO**: Proper hreflang tags improve search visibility per locale
- **UX**: Users engage more with localized content
- **Legal**: Some regions require content in local languages

### Routing Strategies

| Strategy | URL Pattern | Best For |
|----------|-------------|----------|
| Subdirectory | `/en/about`, `/fr/about` | Most sites, SEO-friendly |
| Domain | `en.example.com`, `fr.example.com` | Enterprise, regional sites |
| Cookie/Header | Same URL, detect locale | SPAs, APIs |

### Subdirectory Routing (Recommended)

```text
app/
├── [lang]/
│   ├── layout.tsx
│   ├── page.tsx
│   ├── about/
│   │   └── page.tsx
│   └── blog/
│       └── [slug]/
│           └── page.tsx
├── dictionaries/
│   ├── en.json
│   └── fr.json
└── middleware.ts
```

### Middleware for Language Detection

```ts
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { match } from '@formatjs/intl-localematcher';
import Negotiator from 'negotiator';

const locales = ['en', 'fr', 'de', 'es'];
const defaultLocale = 'en';

function getLocale(request: NextRequest): string {
  const headers = { 'accept-language': request.headers.get('accept-language') || '' };
  const languages = new Negotiator({ headers }).languages();
  return match(languages, locales, defaultLocale);
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Check if pathname already has locale
  const pathnameHasLocale = locales.some(
    (locale) => pathname.startsWith(`/${locale}/`) || pathname === `/${locale}`
  );

  if (pathnameHasLocale) return;

  // Redirect to locale-prefixed path
  const locale = getLocale(request);
  request.nextUrl.pathname = `/${locale}${pathname}`;
  return NextResponse.redirect(request.nextUrl);
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
```

### Dictionary Loading

```ts
// lib/dictionaries.ts
import 'server-only';

const dictionaries = {
  en: () => import('@/dictionaries/en.json').then((m) => m.default),
  fr: () => import('@/dictionaries/fr.json').then((m) => m.default),
  de: () => import('@/dictionaries/de.json').then((m) => m.default),
  es: () => import('@/dictionaries/es.json').then((m) => m.default),
};

export type Locale = keyof typeof dictionaries;
export type Dictionary = Awaited<ReturnType<typeof dictionaries.en>>;

export async function getDictionary(locale: Locale): Promise<Dictionary> {
  return dictionaries[locale]();
}
```

```json
// dictionaries/en.json
{
  "navigation": {
    "home": "Home",
    "about": "About",
    "contact": "Contact"
  },
  "home": {
    "title": "Welcome to our site",
    "description": "We build great products"
  }
}
```

```json
// dictionaries/fr.json
{
  "navigation": {
    "home": "Accueil",
    "about": "À propos",
    "contact": "Contact"
  },
  "home": {
    "title": "Bienvenue sur notre site",
    "description": "Nous créons de super produits"
  }
}
```

### Using Dictionaries in Components

```tsx
// app/[lang]/page.tsx
import { getDictionary, type Locale } from '@/lib/dictionaries';

export default async function Home({
  params,
}: {
  params: Promise<{ lang: Locale }>;
}) {
  const { lang } = await params;
  const dict = await getDictionary(lang);

  return (
    <main>
      <h1>{dict.home.title}</h1>
      <p>{dict.home.description}</p>
    </main>
  );
}

export async function generateStaticParams() {
  return [{ lang: 'en' }, { lang: 'fr' }, { lang: 'de' }, { lang: 'es' }];
}
```

### Language Switcher

```tsx
// components/language-switcher.tsx
'use client';

import { usePathname, useRouter } from 'next/navigation';

const locales = [
  { code: 'en', label: 'English' },
  { code: 'fr', label: 'Français' },
  { code: 'de', label: 'Deutsch' },
  { code: 'es', label: 'Español' },
];

export function LanguageSwitcher({ currentLocale }: { currentLocale: string }) {
  const pathname = usePathname();
  const router = useRouter();

  const switchLocale = (locale: string) => {
    // Replace current locale in pathname
    const newPath = pathname.replace(`/${currentLocale}`, `/${locale}`);
    router.push(newPath);
  };

  return (
    <select
      value={currentLocale}
      onChange={(e) => switchLocale(e.target.value)}
      aria-label="Select language"
    >
      {locales.map((locale) => (
        <option key={locale.code} value={locale.code}>
          {locale.label}
        </option>
      ))}
    </select>
  );
}
```

### SEO with hreflang

```tsx
// app/[lang]/layout.tsx
import type { Metadata } from 'next';

const locales = ['en', 'fr', 'de', 'es'];
const baseUrl = 'https://example.com';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ lang: string }>;
}): Promise<Metadata> {
  const { lang } = await params;

  return {
    alternates: {
      canonical: `${baseUrl}/${lang}`,
      languages: Object.fromEntries(
        locales.map((locale) => [locale, `${baseUrl}/${locale}`])
      ),
    },
  };
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ lang: string }>;
}) {
  const { lang } = await params;

  return (
    <html lang={lang}>
      <body>{children}</body>
    </html>
  );
}
```

### Date and Number Formatting

```tsx
// lib/formatters.ts
import { type Locale } from './dictionaries';

export function formatDate(date: Date, locale: Locale): string {
  return new Intl.DateTimeFormat(locale, {
    dateStyle: 'long',
  }).format(date);
}

export function formatCurrency(
  amount: number,
  locale: Locale,
  currency: string = 'USD'
): string {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
  }).format(amount);
}

export function formatNumber(number: number, locale: Locale): string {
  return new Intl.NumberFormat(locale).format(number);
}
```

```tsx
// Usage in component
import { formatDate, formatCurrency } from '@/lib/formatters';

export default async function ProductPage({
  params,
}: {
  params: Promise<{ lang: Locale }>;
}) {
  const { lang } = await params;
  const product = await getProduct();

  return (
    <article>
      <h1>{product.name}</h1>
      <p>{formatCurrency(product.price, lang, 'EUR')}</p>
      <p>Added: {formatDate(product.createdAt, lang)}</p>
    </article>
  );
}
```

**Why**: Next.js App Router's segment-based routing provides clean i18n implementation without
external libraries. Server Components enable per-request dictionary loading with zero client
bundle impact.

## See Also

- [TypeScript Style Guide](../languages/typescript.md) - Base TypeScript conventions
- [Testing Guide](../process/testing.md) - Testing best practices
- [CI Guide](../process/ci.md) - Continuous integration patterns

## References

[^1]: [Turbopack](https://turbo.build/pack) - Incremental bundler optimized for JavaScript and TypeScript
[^2]: [Vitest](https://vitest.dev/) - Blazing fast unit test framework powered by Vite
[^3]: [React Testing Library](https://testing-library.com/react) - Simple and complete React DOM testing utilities
[^4]: [Playwright](https://playwright.dev/) - End-to-end testing for modern web apps
[^5]: [eslint-config-next](https://nextjs.org/docs/app/building-your-application/configuring/eslint) - Next.js ESLint configuration with framework-specific rules
[^6]: [Next.js](https://nextjs.org/) - The React Framework for the Web
[^7]: [Vercel](https://vercel.com/) - Platform for deploying Next.js applications with zero configuration
[^ppr]: [Partial Prerendering](https://nextjs.org/docs/app/building-your-application/rendering/partial-prerendering) - Combine static and dynamic rendering in a single route
[^ratelimit]: [Upstash Ratelimit](https://github.com/upstash/ratelimit-js) - Rate limiting library for serverless runtimes using HTTP-based Redis
[^authjs]: [Auth.js](https://authjs.dev/) - Authentication for the Web, formerly NextAuth.js
[^pusher]: [Pusher](https://pusher.com/) - Managed real-time messaging service with pub/sub channels
[^ably]: [Ably](https://ably.com/) - Enterprise real-time messaging platform with presence and history
[^socketio]: [Socket.IO](https://socket.io/) - Bidirectional event-based communication library (requires persistent server)
[^inngest]: [Inngest](https://www.inngest.com/) - Workflow orchestration platform for background jobs and AI pipelines
[^triggerdev]: [Trigger.dev](https://trigger.dev/) - Open-source platform for background jobs and long-running tasks
[^vercelcron]: [Vercel Cron Jobs](https://vercel.com/docs/cron-jobs) - Native scheduled tasks for Vercel deployments
[^bullmq]: [BullMQ](https://bullmq.io/) - Redis-based background job processing for self-hosted environments
[^opossum]: [Opossum](https://github.com/nodeshift/opossum) - Node.js circuit breaker with 70,000+ weekly downloads
[^flagssdk]: [Vercel Flags SDK](https://vercel.com/docs/feature-flags/feature-flags-pattern) - Framework-agnostic feature flags with provider adapters
[^statsig]: [Statsig](https://statsig.com/) - Feature flags and experimentation platform with unlimited free flags
[^launchdarkly]: [LaunchDarkly](https://launchdarkly.com/) - Enterprise feature management platform
