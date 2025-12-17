# Next.js Style Guide

> [Doctrine](../../README.md) > [Frameworks](../README.md) > Next.js

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119.txt).

Extends [TypeScript style guide](../languages/typescript.md) with Next.js-specific conventions.

**Target Version**: Next.js 15+ with App Router and React 19

## Quick Reference

All TypeScript tooling applies. Additional Next.js-specific tools:

| Task | Tool | Command |
|------|------|---------|
| Install | npm/pnpm/yarn | `npx create-next-app@latest` |
| Run dev | Next.js | `npm run dev` |
| Build | Next.js | `npm run build` |
| Bundler | Turbopack[^1] | `next dev --turbo` |
| Test | Vitest[^2] + Testing Library[^3] | `vitest` |
| E2E | Playwright[^4] | `playwright test` |
| Lint | ESLint + next plugin[^5] | `next lint` |

## Why Next.js?

Next.js[^6] is a full-stack React framework with server-side rendering, static site generation, and built-in optimizations for production applications.

**Key advantages**:
- Server and Client Components for optimal performance
- Built-in routing with file-based conventions
- Automatic code splitting and image optimization
- Full-stack capabilities with Server Actions
- Zero-config TypeScript support
- Excellent developer experience with Fast Refresh

Use Next.js for React applications requiring SEO, server rendering, or full-stack features. For client-only SPAs, consider Vite + React. For static sites, consider Astro.

## Project Structure

Projects **MUST** use the App Router directory structure:

```
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

**Why**: The App Router co-locates routes with their components, making the file system the API. Route groups organize pages without affecting URLs, and special files (`loading.tsx`, `error.tsx`) provide consistent UX patterns.

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

**Why**: File-based routing eliminates routing configuration, makes page discovery intuitive, and enables automatic code splitting per route.

## Route Groups and Parallel Routes

Projects **SHOULD** use route groups for organization:

```
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

**Why**: Route groups organize files without adding URL segments. Parallel routes enable advanced patterns like modals, split views, and conditional rendering.

## Server vs Client Components

Components **MUST** be Server Components by default. Client Components **MUST** be explicitly marked with `'use client'`.

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
|---------------------------|---------------------------|
| Data fetching | Interactivity (onClick, onChange) |
| Backend resources access | State (useState, useReducer) |
| Sensitive data (API keys) | Effects (useEffect, useLayoutEffect) |
| Large dependencies | Browser APIs (localStorage, window) |
| SEO-critical content | Event listeners |

**Why**: Server Components reduce JavaScript bundle size, enable direct backend access, and improve initial page load. Client Components provide interactivity where needed without forcing the entire app client-side.

## Partial Prerendering (PPR)

Next.js 15 introduces Partial Prerendering[^ppr], which combines static and dynamic rendering in a single route. Projects **SHOULD** enable PPR for optimal performance:

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

**Why PPR**: Traditional SSR waits for all data before sending HTML. PPR sends a static shell instantly (best TTFB) while streaming dynamic content as it resolves. This provides the speed of static sites with the personalization of dynamic pages.

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

**Why**: Request deduplication prevents waterfall fetching and redundant network calls, improving performance without manual caching logic.

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

**Why**: Explicit cache control balances performance with data freshness. Tag-based revalidation enables surgical cache invalidation without rebuilding the entire site.

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

**Why**: Server Actions eliminate the need for API routes for simple mutations, provide type safety, and work without client-side JavaScript (progressive enhancement).

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
|----------|---------|
| Authentication | Check tokens, redirect to login |
| Authorization | Role-based access control |
| Redirects | A/B testing, localization |
| Bot detection | User-Agent analysis |
| Rate limiting | Request throttling |

**Why**: Middleware runs on the Edge before rendering, enabling fast authentication checks, redirects, and request modification without full server computation.

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

**Why**: Route Handlers provide REST API endpoints when needed. For form submissions and mutations, prefer Server Actions for better type safety and progressive enhancement.

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

**Why**: Vitest provides fast unit testing with React Server Component support. Playwright enables reliable E2E testing across browsers with automatic waiting and screenshot/video recording.

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

**Why**: Vercel provides zero-config deployments, automatic HTTPS, edge functions, and built-in analytics. Preview deployments for every pull request enable safe testing before production.

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

**Why**: Standalone output creates a minimal Node.js server with only required dependencies. Docker enables consistent deployments across environments with isolated dependencies.

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

**Why**: Turbopack provides 700x faster updates than Webpack in development. Production builds still use Webpack for maximum optimization.

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

**Why**: Next.js Image automatically optimizes images, serves modern formats (AVIF/WebP), generates responsive sizes, and lazy loads by default.

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

**Why**: `next/font` automatically self-hosts Google Fonts (eliminating external requests), optimizes loading with CSS size-adjust, and prevents layout shift.

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

**Why**: Next.js automatically generates SEO tags from metadata, supports dynamic per-page metadata, and provides type safety for Open Graph and Twitter Cards.

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
