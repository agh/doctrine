# Tailwind CSS Style Guide

> [Doctrine](../../README.md) > [Frameworks](../README.md) > Tailwind CSS

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119][rfc2119].

[rfc2119]: https://datatracker.ietf.org/doc/html/rfc2119

**Target Version**: Tailwind CSS v4.1+

## Quick Reference

| Task | Tool | Command |
| ---- | ---- | ------- |
| Install | npm | `npm install tailwindcss` |
| Build | Tailwind CLI | `npx @tailwindcss/cli -i input.css -o output.css` |
| Watch | Tailwind CLI | `npx @tailwindcss/cli -i input.css -o output.css --watch` |
| Build (prod) | Tailwind CLI | `NODE_ENV=production npx @tailwindcss/cli -i input.css -o output.css --minify` |
| Vite plugin | npm | `npm install @tailwindcss/vite` |

## Why Tailwind CSS

Tailwind CSS[^1] is a utility-first CSS framework that enables rapid UI
development by composing small, single-purpose utility classes directly in
HTML.

**Why utility-first:**

- Faster development: No context switching between HTML and CSS files
- Smaller CSS bundles: Only the utilities you use are included in production
- Consistent design: Built-in design system prevents arbitrary values
- Maintainability: Co-locating styles with markup makes changes predictable
- No naming fatigue: Eliminates bikeshedding over class names like `.user-card-header-title`

**Tailwind vs Component Frameworks (Bootstrap, Bulma):**

| Aspect | Tailwind | Component Frameworks |
| ------ | -------- | -------------------- |
| Approach | Utility-first, composable | Pre-built components |
| Customization | Highly flexible via config | Limited, requires overrides |
| Bundle size | Minimal (only used utilities) | Larger (includes all components) |
| Learning curve | Steeper initially | Easier initially |
| Design freedom | Complete control | Constrained to framework style |
| Best for | Custom designs, design systems | Prototypes, standard layouts |

Use Tailwind when building custom designs or design systems. Use component
frameworks for rapid prototyping with standard UI patterns.

## Installation and Configuration

Projects using Tailwind CSS v4+ **MUST** use the simplified CSS-first configuration.

### Basic Installation

```bash
npm install tailwindcss
```

### CSS Configuration (v4+)

Projects **MUST** use the single-line CSS import:

```css
/* input.css */
@import "tailwindcss";

/* Custom theme configuration */
@theme {
  --color-brand: oklch(0.6 0.2 250);
  --font-sans: "Inter", system-ui, sans-serif;
  --breakpoint-3xl: 1920px;
}

/* Custom utilities */
@utility slide-in {
  animation: slide-in 0.3s ease-out;
}

@keyframes slide-in {
  from { transform: translateY(-100%); }
  to { transform: translateY(0); }
}
```

**Why CSS-first configuration:**

- Simpler setup: No JavaScript configuration file required
- Better performance: Direct CSS integration leverages native browser optimization
- Type safety: Custom properties are validated at build time
- Co-location: Theme values live where they're used, not in a separate config file

### Vite Integration

Projects using Vite **SHOULD** use the official Tailwind Vite plugin[^2]:

```javascript
// vite.config.js
import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [tailwindcss()],
})
```

```css
/* src/index.css */
@import "tailwindcss";
```

**Why Vite plugin:**

- Zero configuration: Automatic content detection
- Maximum performance: Tight integration with Vite's build pipeline
- Built-in HMR: Instant updates during development
- Native imports: No PostCSS configuration required

### Legacy Configuration (v3)

Projects still on Tailwind v3 **MUST** migrate to v4, but **MAY** use this configuration temporarily:

```javascript
// tailwind.config.js (v3 only - migrate to CSS @theme)
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{html,js,jsx,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        brand: '#5b21b6',
      },
    },
  },
  plugins: [],
}
```

**Migration path**: Use the automated upgrade tool[^3]:

```bash
npx @tailwindcss/upgrade
```

## Project Organization

### File Structure

Projects **SHOULD** organize Tailwind styles using this structure:

```text
src/
├── styles/
│   ├── app.css              # Main entry point
│   ├── base.css             # Base styles, resets
│   ├── components.css       # Component classes
│   └── utilities.css        # Custom utilities
├── components/
│   ├── Button.tsx
│   └── Card.tsx
└── index.html
```

```css
/* src/styles/app.css */
@import "tailwindcss";
@import "./base.css";
@import "./components.css";
@import "./utilities.css";
```

```css
/* src/styles/base.css */
@layer base {
  h1 {
    @apply text-4xl font-bold tracking-tight;
  }

  a {
    @apply text-blue-600 hover:text-blue-800 underline;
  }
}
```

```css
/* src/styles/components.css */
@layer components {
  .btn-primary {
    @apply px-4 py-2 bg-blue-600 text-white rounded-lg;
    @apply hover:bg-blue-700 focus:ring-2 focus:ring-blue-500;
  }
}
```

**Why this structure:**

- Separation of concerns: Base styles, components, and utilities are clearly
  separated
- Layer control: `@layer` ensures proper cascade ordering
- Maintainability: Easy to find and modify specific style categories
- Scalability: Scales from small to large projects

### Component Patterns

Projects **MUST** co-locate utility classes with component markup:

```tsx
// GOOD: Utilities in component
export function Button({ children, variant = 'primary' }: ButtonProps) {
  const baseClasses = "px-4 py-2 rounded-lg font-medium transition-colors"
  const variantClasses = {
    primary: "bg-blue-600 text-white hover:bg-blue-700",
    secondary: "bg-gray-200 text-gray-900 hover:bg-gray-300",
  }

  return (
    <button className={`${baseClasses} ${variantClasses[variant]}`}>
      {children}
    </button>
  )
}
```

```tsx
// BAD: Separate CSS file for simple components
/* button.css */
.button { /* ... */ }
.button-primary { /* ... */ }
.button-secondary { /* ... */ }
```

**Why co-location:**

- Single source of truth: Styles and markup evolve together
- No context switching: See exactly how component looks without checking CSS
- Better tree-shaking: Unused components and their styles are removed together
- Easier refactoring: Rename or delete components without orphaned CSS

## Utility Patterns

### Spacing

Projects **MUST** use Tailwind's spacing scale consistently:

```html
<!-- GOOD: Consistent spacing scale -->
<div class="p-4 space-y-6">
  <div class="mb-2">Header</div>
  <div class="mt-8">Content</div>
</div>

<!-- BAD: Arbitrary values without reason -->
<div class="p-[17px] space-y-[23px]">
  <div class="mb-[9px]">Header</div>
</div>
```

**Spacing scale reference:**

- `1` = 0.25rem (4px)
- `4` = 1rem (16px)
- `8` = 2rem (32px)
- `12` = 3rem (48px)

Use arbitrary values only for one-off designs that don't fit the scale:

```html
<!-- Acceptable: One-off layout requirement -->
<div class="w-[calc(100%-80px)]"></div>
```

### Colors

Projects **SHOULD** use semantic color names from the theme:

```html
<!-- GOOD: Semantic theme colors -->
<button class="bg-primary text-white hover:bg-primary/90">
  Submit
</button>

<!-- ACCEPTABLE: Standard palette -->
<div class="bg-blue-600 text-white">
  Info message
</div>

<!-- BAD: Arbitrary colors -->
<div class="bg-[#3b82f6]">
  Info message
</div>
```

### Color Opacity

Projects **SHOULD** use the `/` opacity modifier:

```html
<!-- GOOD: Opacity modifier -->
<div class="bg-blue-600/50">Semi-transparent</div>
<div class="text-gray-900/75">Faded text</div>

<!-- BAD: Separate opacity utility -->
<div class="bg-blue-600 opacity-50">Semi-transparent</div>
```

**Why `/` modifier:**

- More specific: Only affects the color, not the entire element
- Better composability: Easily adjust opacity without affecting children
- Clearer intent: Immediately obvious which property has opacity

### Typography

Projects **MUST** use consistent typography scales:

```html
<!-- GOOD: Standard text utilities -->
<h1 class="text-4xl font-bold leading-tight tracking-tight">
  Heading
</h1>

<p class="text-base leading-relaxed text-gray-700">
  Body text with comfortable reading line-height.
</p>

<!-- BETTER: Custom prose classes for long-form content -->
<article class="prose prose-lg max-w-prose">
  <h1>Article Title</h1>
  <p>Article content...</p>
</article>
```

### Responsive Design

Projects **MUST** use mobile-first responsive design:

```html
<!-- GOOD: Mobile-first, progressive enhancement -->
<div class="w-full md:w-1/2 lg:w-1/3">
  Responsive column
</div>

<img
  class="w-full md:w-auto md:h-48 object-cover"
  src="image.jpg"
  alt="Description"
/>

<!-- BAD: Desktop-first -->
<div class="w-1/3 md:w-full">
  Wrong approach
</div>
```

**Breakpoint scale:**

- Default (mobile): 0px+
- `sm`: 640px (small tablets)
- `md`: 768px (tablets, small laptops)
- `lg`: 1024px (laptops, desktops)
- `xl`: 1280px (large desktops)
- `2xl`: 1536px (extra large screens)

### Container Queries (v4+)

Projects **SHOULD** use container queries for component-based responsive design:

```html
<!-- Container definition -->
<div class="@container">
  <div class="grid grid-cols-1 @md:grid-cols-2 @lg:grid-cols-3 gap-4">
    <div>Card 1</div>
    <div>Card 2</div>
    <div>Card 3</div>
  </div>
</div>
```

**Container query breakpoints:**

- `@sm`: 384px
- `@md`: 448px
- `@lg`: 512px
- `@xl`: 576px
- `@2xl`: 672px

**Why container queries:**

- True component modularity: Components respond to their container, not viewport
- Reusable layouts: Same component works in sidebar, modal, or full-width
- Better encapsulation: Component styling independent of page layout

## Component Extraction

### When to Use @apply

Projects **MAY** use `@apply` for frequently repeated utility combinations:

```css
/* GOOD: Extracting repeated complex patterns */
@layer components {
  .card {
    @apply rounded-lg bg-white p-6 shadow-md;
  }

  .btn {
    @apply inline-flex items-center justify-center;
    @apply px-4 py-2 rounded-md font-medium;
    @apply transition-colors duration-200;
  }
}
```

```html
<div class="card">
  <h2>Card Title</h2>
  <button class="btn bg-blue-600 text-white">Action</button>
</div>
```

Projects **MUST NOT** overuse `@apply` for simple utility combinations:

```css
/* BAD: Unnecessary extraction */
.text-large {
  @apply text-xl font-semibold;
}

/* Just use utilities directly */
<h2 class="text-xl font-semibold">Title</h2>
```

**When to extract:**

- Repeated 5+ times across codebase (yes)
- Complex combinations with 10+ utilities (yes)
- Team-wide component patterns (yes)
- Simple 2-3 utility combinations (no)
- One-off component styles (no)
- Utilities that vary by state/context (no)

### Component Abstraction

Projects **SHOULD** prefer component-level abstraction over `@apply`:

```tsx
// GOOD: Component abstraction (React)
export function Card({ children, className = '' }: CardProps) {
  return (
    <div className={`rounded-lg bg-white p-6 shadow-md ${className}`}>
      {children}
    </div>
  )
}

// Usage
<Card className="hover:shadow-lg">
  <h2>Title</h2>
</Card>
```

```vue
<!-- GOOD: Component abstraction (Vue) -->
<template>
  <div class="rounded-lg bg-white p-6 shadow-md" :class="className">
    <slot />
  </div>
</template>

<script setup>
defineProps<{ className?: string }>()
</script>
```

**Why component abstraction:**

- Framework-native: Works with component lifecycle, props, and state
- Better developer experience: IDE autocomplete and type checking
- More flexible: Easily add props, events, and logic
- Testable: Can unit test component behavior

## Dark Mode

Projects implementing dark mode **MUST** use Tailwind's dark mode utilities[^4].

By default `dark:*` compiles to a `@media (prefers-color-scheme: dark)` query.
Theme variables **MUST NOT** be used to change this: `@theme` declares design
tokens, not variants, so a `--color-scheme` entry has no effect on the `dark`
variant and does not set the CSS `color-scheme` property.

### Class-Based Dark Mode

Projects **SHOULD** override the `dark` variant with a selector so users
control the theme:

```css
/* app.css */
@import "tailwindcss";

@custom-variant dark (&:where(.dark, .dark *));
```

With that override `dark:bg-gray-900` compiles to
`.dark\:bg-gray-900:where(.dark, .dark *)` rather than a media query, so adding
`dark` to the `html` element switches the theme:

```html
<!-- GOOD: .dark on <html> drives every dark: utility -->
<html class="dark">
  <body class="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
    <div class="bg-gray-100 dark:bg-gray-800 p-4">
      <h1 class="text-gray-900 dark:text-white">Title</h1>
    </div>
  </body>
</html>
```

```html
<!-- DON'T: without @custom-variant, dark: still follows the media query -->
<!-- and this class toggle changes nothing -->
<html class="dark">
```

The preference script **MUST** run in `head` before the first paint, otherwise
the page renders in the wrong theme and then flips:

```html
<head>
  <link rel="stylesheet" href="/styles/app.css">
  <script>
    document.documentElement.classList.toggle(
      'dark',
      localStorage.theme === 'dark' ||
        (!('theme' in localStorage) &&
          window.matchMedia('(prefers-color-scheme: dark)').matches)
    )
  </script>
</head>
```

```javascript
// Explicit user choices, written by the theme control
function setTheme(choice) {
  if (choice === 'system') {
    localStorage.removeItem('theme')
  } else {
    localStorage.theme = choice
  }
  document.documentElement.classList.toggle(
    'dark',
    localStorage.theme === 'dark' ||
      (!('theme' in localStorage) &&
        window.matchMedia('(prefers-color-scheme: dark)').matches)
  )
}
```

### Native Control Colours

`color-scheme` is a separate CSS property that tells the browser which palette
to use for scrollbars, form controls and system colours. It is not the `dark`
variant. Projects **SHOULD** set it with the `scheme-*` utilities so native
widgets follow the selected theme:

```html
<!-- GOOD: scheme-dark wins whenever .dark is present -->
<html class="dark scheme-light dark:scheme-dark">
```

### Media Query Dark Mode

Projects **MAY** use media query-based dark mode for automatic system preference:

```html
<!-- Automatically follows system preference: this is the default, -->
<!-- so app.css needs no @custom-variant override -->
<div class="bg-white dark:bg-gray-900">
  Content
</div>
```

**Why class-based:**

- User control: Users can override system preference
- Persistent: Remember user choice via localStorage
- Testable: Easy to toggle in development and testing

## Custom Utilities

### Extending the Configuration

Projects **MUST** extend Tailwind's configuration in CSS using `@theme`:

```css
/* app.css */
@import "tailwindcss";

@theme {
  /* Custom colors */
  --color-brand-50: oklch(0.95 0.02 250);
  --color-brand-500: oklch(0.6 0.2 250);
  --color-brand-900: oklch(0.3 0.15 250);

  /* Custom spacing */
  --spacing-18: 4.5rem;
  --spacing-128: 32rem;

  /* Custom fonts */
  --font-display: "Cabinet Grotesk", sans-serif;

  /* Custom breakpoints */
  --breakpoint-3xl: 1920px;
}

/* Use custom values */
.hero {
  @apply text-brand-500 font-display;
}
```

### Custom Utility Classes

Projects **MAY** define custom utilities using `@utility`:

```css
@utility blur-xs {
  filter: blur(2px);
}

@utility text-balance {
  text-wrap: balance;
}

@utility grid-auto-fit {
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
}
```

```html
<div class="grid grid-auto-fit gap-4">
  <div>Card 1</div>
  <div>Card 2</div>
  <div>Card 3</div>
</div>

<h1 class="text-balance">
  Nicely balanced headline text
</h1>
```

### Plugins

Projects **SHOULD** use official Tailwind plugins for extended functionality:

```bash
npm install @tailwindcss/typography @tailwindcss/forms @tailwindcss/container-queries
```

```css
@import "tailwindcss";
@plugin "@tailwindcss/typography";
@plugin "@tailwindcss/forms";
@plugin "@tailwindcss/container-queries";
```

**Official plugins:**

- `@tailwindcss/typography`[^5]: Beautiful typographic defaults for prose content
- `@tailwindcss/forms`[^6]: Better default styles for form elements
- `@tailwindcss/container-queries`[^7]: Container query utilities (built-in v4.1+)

## Performance

### Production Optimization

Projects **MUST** optimize Tailwind for production:

```bash
# Production build with minification
NODE_ENV=production npx @tailwindcss/cli -i input.css -o output.css --minify
```

**Tailwind v4+ automatic optimizations:**

- Dead code elimination: Unused utilities are automatically removed
- CSS minification: Built-in minification via Lightning CSS
- Vendor prefixing: Automatic browser prefixing
- Modern CSS: Leverages cascade layers and native features

### Content Detection

Projects using Tailwind v4+ **SHOULD** rely on automatic content detection:

```javascript
// vite.config.js - no content configuration needed
import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [tailwindcss()],
})
```

Tailwind v4 automatically detects template files without configuration.

### Dynamic Class Names

Projects **MUST** avoid dynamically constructing class names:

```tsx
// BAD: Dynamic class names won't be detected
const Button = ({ color }: { color: string }) => (
  <button className={`bg-${color}-500`}>Click</button>
)

// GOOD: Complete class names
const Button = ({ color }: { color: 'blue' | 'red' }) => {
  const colorClasses = {
    blue: 'bg-blue-500 hover:bg-blue-600',
    red: 'bg-red-500 hover:bg-red-600',
  }
  return <button className={colorClasses[color]}>Click</button>
}
```

Classes that only ever appear in CMS or API data are never in a source file, so
projects **MUST** safelist them with `@source inline(...)`. `@custom-variant`
defines a variant and `@variant` applies one; neither generates a utility:

```css
/* app.css - ALSO GOOD: safelist utilities that only exist in remote data */
@import "tailwindcss";

@source inline("{hover:,}bg-{blue,red}-{500,600}");
```

The argument is brace-expanded, so this emits `bg-blue-500`, `bg-blue-600`,
`bg-red-500`, `bg-red-600` and a `hover:` variant of each.

```css
/* DON'T: variant directives do not safelist anything, and this fails the */
/* build with "defines an invalid variant name" */
@import "tailwindcss";
@variant data-[color="blue"] (.data-color-blue);
```

**Why complete class names:**

- Build-time detection: Tailwind scans for complete strings
- Smaller bundles: Only includes classes actually used
- Predictable output: No runtime surprises from missing classes

### Bundle Size Best Practices

Projects **SHOULD** follow these bundle size best practices:

1. **Use utilities judiciously**: Don't add utilities you don't need
2. **Prefer standard palette**: Custom colors increase bundle size
3. **Extract common patterns**: Reduce repetition in HTML
4. **Split CSS**: Load only critical CSS initially

Critical CSS **MUST** be extracted at build time from compiled Tailwind output.
A browser resolves an `@import` string as a stylesheet URL, so an uncompiled
`@import "tailwindcss"` inside a `style` element fetches nothing, generates no
utilities and leaves the page unstyled.

Build a second entry point restricted to the above-the-fold templates:

```css
/* src/critical.css - only the shell that renders above the fold */
@import "tailwindcss" source(none);
@source "../templates/shell.html";
```

```bash
# Compile both sheets; src/app.css is the project's existing entry point
npx @tailwindcss/cli@4.3.3 -i src/app.css -o dist/app.css --minify
npx @tailwindcss/cli@4.3.3 -i src/critical.css -o dist/critical.css --minify
```

Inline the compiled critical sheet server-side and link the full sheet
normally. Inline event handlers **MUST NOT** be used to defer stylesheets,
because CSP's `script-src` covers handlers such as `onload`; a blocked handler
leaves a `media="print"` sheet print-only forever:

```html
<head>
  <!-- GOOD: compiled CSS inlined at render time, nonce for a strict CSP -->
  <style nonce="{{ cspNonce }}">{{ include "dist/critical.css" }}</style>
  <link rel="stylesheet" href="/styles/app.css">
</head>
```

```html
<!-- DON'T: the browser cannot resolve an npm package, and a CSP that -->
<!-- blocks the onload handler leaves the full sheet print-only -->
<style>
  @import "tailwindcss";
</style>
<link rel="stylesheet" href="/styles/app.css" media="print" onload="this.media='all'">
```

**Why build-time extraction:**

- Correctness: Only the Tailwind CLI, Vite, PostCSS or webpack adapter turns
  `@import "tailwindcss"` into utilities
- Resilience: The full sheet loads without JavaScript, so a blocked or failed
  script cannot leave the page unstyled
- CSP compatibility: A nonced `style` element needs no `'unsafe-inline'` and no
  inline event handler

## Integration with Frameworks

### React

```tsx
// Install
npm install tailwindcss @tailwindcss/vite

// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
})
```

```tsx
// Component with Tailwind
import { useState } from 'react'

export function Button({ children, variant = 'primary' }) {
  const variants = {
    primary: 'bg-blue-600 hover:bg-blue-700 text-white',
    secondary: 'bg-gray-200 hover:bg-gray-300 text-gray-900',
  }

  return (
    <button className={`px-4 py-2 rounded-lg font-medium ${variants[variant]}`}>
      {children}
    </button>
  )
}
```

### Vue

```bash
# Install
npm install tailwindcss @tailwindcss/vite
```

```javascript
// vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [vue(), tailwindcss()],
})
```

```vue
<template>
  <button :class="variantClasses">
    <slot />
  </button>
</template>

<script setup>
const props = defineProps({
  variant: {
    type: String,
    default: 'primary',
  },
})

const variantClasses = computed(() => {
  const base = 'px-4 py-2 rounded-lg font-medium'
  const variants = {
    primary: 'bg-blue-600 hover:bg-blue-700 text-white',
    secondary: 'bg-gray-200 hover:bg-gray-300 text-gray-900',
  }
  return `${base} ${variants[props.variant]}`
})
</script>
```

### Next.js

Next.js has no built-in Tailwind step, so the PostCSS adapter **MUST** be
installed and configured[^8]. Without it `@import "tailwindcss"` reaches the
browser untransformed and no utilities exist.

```bash
# Install (Next.js 16.3.4, Tailwind CSS 4.3.3)
npm install -D tailwindcss@4.3.3 @tailwindcss/postcss@4.3.3
```

```javascript
// postcss.config.mjs
export default {
  plugins: {
    '@tailwindcss/postcss': {},
  },
}
```

```css
/* app/globals.css */
@import "tailwindcss";
```

```tsx
// app/layout.tsx
import './globals.css'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
```

```tsx
// app/page.tsx
export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      <h1 className="text-4xl font-bold">Welcome</h1>
    </div>
  )
}
```

JSX **MUST** use `className`; `class` is not a React DOM property and fails
type checking. Layout `children` **MUST** be typed as `React.ReactNode`,
otherwise `strict` mode rejects the implicit `any`.

### Svelte

```bash
# Install
npm install tailwindcss @tailwindcss/vite
```

```javascript
// vite.config.js
import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [svelte(), tailwindcss()],
})
```

```svelte
<script>
  export let variant = 'primary'

  const variants = {
    primary: 'bg-blue-600 hover:bg-blue-700 text-white',
    secondary: 'bg-gray-200 hover:bg-gray-300 text-gray-900',
  }
</script>

<button class="px-4 py-2 rounded-lg font-medium {variants[variant]}">
  <slot />
</button>
```

## See Also

- [CSS Best Practices](../docs/css.md) - General CSS conventions
- [JavaScript Guide](../languages/javascript.md) - JavaScript and TypeScript patterns
- [React Guide](./react.md) - React-specific conventions
- [Vue Guide](./vue.md) - Vue-specific conventions

## References

[^1]: [Tailwind CSS Documentation](https://tailwindcss.com/) - Official Tailwind CSS documentation and guides
[^2]: [Tailwind Vite Plugin](https://tailwindcss.com/docs/installation/using-vite) - Official Vite integration
[^3]: [Tailwind CSS v4.0 Release](https://tailwindcss.com/blog/tailwindcss-v4) - v4.0 release announcement and migration guide
[^4]: [Dark Mode - Tailwind CSS](https://tailwindcss.com/docs/dark-mode) - Dark mode implementation guide
[^5]: [Typography Plugin](https://tailwindcss.com/docs/typography-plugin) - Beautiful typographic defaults for prose content
[^6]: [Forms Plugin](https://github.com/tailwindlabs/tailwindcss-forms) - Better form element styling
[^7]: [Container Queries](https://tailwindcss.com/docs/hover-focus-and-other-states#container-queries) - Container query utilities
[^8]: [CSS - Next.js](https://nextjs.org/docs/app/getting-started/css#tailwind-css) - Official Next.js Tailwind CSS setup
