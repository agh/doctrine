# CSS Style Guide

> [Doctrine](../../README.md) > [Languages](../README.md) > CSS

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

Extends [Google HTML/CSS Style Guide](google/htmlcss.html).

## Quick Reference

| Task | Tool | Command |
| ---- | ---- | ------- |
| Lint | Stylelint[^1] | `npx stylelint "**/*.css"` |
| Format | Prettier[^2] | `npx prettier --write "**/*.css"` |
| Type check | - | - |
| Semantic | - | - |
| Dead code | PurgeCSS[^3] (optional) | `npx purgecss --config purgecss.config.js` |
| Coverage | - | - |
| Complexity | - | - |
| Fuzz | - | - |
| Test perf | - | - |

## Framework Recommendation: Tailwind CSS

For new projects, you **SHOULD** use Tailwind CSS[^4]. It has the highest
retention rate (75.5%) among CSS frameworks and provides:

- Utility-first approach with granular control
- JIT compiler that only includes used styles
- Excellent performance with minimal CSS output

### Why Tailwind CSS

Tailwind CSS offers significant advantages over traditional CSS frameworks:

- **Performance**: The JIT compiler ensures only used styles are included,
  reducing CSS bundle size by up to 90% compared to full framework imports
- **Developer Experience**: Utility classes enable rapid development without
  context switching between HTML and CSS files
- **Maintainability**: Colocation of styles with markup reduces cognitive
  overhead and makes refactoring easier
- **Consistency**: Design tokens built into the framework ensure consistent
  spacing, colors, and typography
- **Community**: Highest retention rate (75.5%) indicates strong satisfaction
  and extensive ecosystem support

### Installing Tailwind CSS 4

Tailwind CSS 4[^4] splits the framework across packages: `tailwindcss` holds
the engine and exposes no executable, and the command-line binary ships
separately as `@tailwindcss/cli`. There is no `init` command, because
configuration now lives in CSS rather than in a generated JavaScript file.

You **MUST** install both packages, pinned, for command-line builds:

```bash
npm install --save-dev tailwindcss@4.3.3 @tailwindcss/cli@4.3.3
```

You **MUST** pull the framework in with a CSS `@import`:

```css
/* src/input.css */
@import "tailwindcss";
```

Tailwind scans your project for class names automatically. Add `@source` only
for template directories automatic detection skips, such as anything excluded
by `.gitignore`. Its path is resolved relative to the stylesheet, not the
project root:

```css
/* src/input.css — templates/ is listed in .gitignore */
@import "tailwindcss";
@source "../templates/**/*.html";
```

Build the stylesheet:

```bash
npx @tailwindcss/cli -i src/input.css -o dist/output.css --minify
```

For Vite[^13] projects you **SHOULD** use the Vite plugin instead of the CLI,
so Tailwind runs inside the existing build and hot-reload pipeline:

```bash
npm install --save-dev tailwindcss@4.3.3 @tailwindcss/vite@4.3.3
```

```javascript
// vite.config.js
import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [tailwindcss()],
});
```

You **MUST NOT** use the Tailwind 3 setup. Installing `tailwindcss` alone
creates no `node_modules/.bin/tailwindcss`, so `npx tailwindcss init` fails
with `could not determine executable to run`, and the CLI that does exist
rejects the subcommand with `Invalid command: init`:

```bash
# Don't: installs no binary, and `init` was removed in Tailwind 4
npm install -D tailwindcss
npx tailwindcss init
```

See the [Tailwind CSS guide](../frameworks/tailwind.md) for theme tokens,
utilities, and component patterns.

For projects requiring traditional CSS or component libraries, consider:

- **Bulma**[^5]: Lightweight, Flexbox-based, beginner-friendly
- **Bootstrap**[^6]: Extensive components, good for rapid prototyping

## Linting: Stylelint

You **MUST** use Stylelint[^1] for CSS linting.

```bash
npm install --save-dev stylelint stylelint-config-standard
```

### Why Stylelint

Stylelint[^1] is the industry-standard CSS linter because:

- **Comprehensive**: Supports CSS, SCSS, Sass[^7], Less[^8], and CSS-in-JS
- **Extensible**: Over 170 built-in rules with plugin architecture for custom
  rules
- **Modern**: Actively maintained with support for latest CSS features
  (nesting, container queries, etc.)
- **Framework Integration**: Official plugins for Tailwind,
  styled-components[^9], and other frameworks
- **Auto-fix**: Many rules support automatic fixing, reducing manual corrections

### Configuration (.stylelintrc.json)

```json
{
  "extends": ["stylelint-config-standard"],
  "rules": {
    "selector-class-pattern": "^[a-z][a-z0-9]*(-[a-z0-9]+)*$",
    "custom-property-pattern": "^[a-z][a-z0-9]*(-[a-z0-9]+)*$",
    "declaration-block-no-redundant-longhand-properties": true,
    "shorthand-property-no-redundant-values": true,
    "color-hex-length": "short",
    "color-named": "never"
  }
}
```

### For Tailwind

```bash
npm install --save-dev stylelint-config-tailwindcss
```

```json
{
  "extends": ["stylelint-config-standard", "stylelint-config-tailwindcss"]
}
```

## Formatting: Prettier

You **MUST** use Prettier[^2] for CSS formatting.

```json
{
  "singleQuote": true,
  "tabWidth": 2
}
```

### Why Prettier

Prettier[^2] is the definitive code formatter for CSS:

- **Consistency**: Enforces uniform formatting across teams and projects
- **Zero Configuration**: Works out-of-the-box with sensible defaults
- **Language Support**: Formats CSS, SCSS, Less[^8], and CSS-in-JS alongside
  HTML and JavaScript
- **Editor Integration**: First-class support in all major editors
  (VS Code[^10], WebStorm, Vim, etc.)
- **Diff Quality**: Consistent formatting produces cleaner, more readable git diffs

## Tooling: 2025 Landscape

### Build Tools

You **SHOULD** use Lightning CSS[^11] for production builds.

| Tool | Use Case | Notes |
| ---- | -------- | ----- |
| **Lightning CSS**[^11] | Production build | 100x faster than PostCSS |
| **PostCSS**[^12] | Plugin ecosystem | Still useful for specific plugins |
| **Vite**[^13] | Development | Fast HMR, uses Lightning CSS |

### Preprocessors

Native CSS now supports variables and nesting. Preprocessors are **OPTIONAL**:

```css
/* Native CSS nesting (production-ready 2025) */
.card {
  background: white;

  & .title {
    font-size: 1.5rem;
  }

  &:hover {
    background: #f5f5f5;
  }
}
```

You **SHOULD** use native CSS features when possible. You **MAY** use Sass[^7]
only when you need:

- Advanced conditionals (`@if`, `@for`)
- Complex mixins
- Functions

## Naming Conventions

You **SHOULD** use BEM[^14] (Block Element Modifier) or utility classes.

### BEM

```css
/* Block */
.card { }

/* Element */
.card__title { }
.card__body { }

/* Modifier */
.card--featured { }
.card__title--large { }
```

### Utility Classes (Tailwind-style)

```css
.flex { display: flex; }
.items-center { align-items: center; }
.p-4 { padding: 1rem; }
```

## Dead Code: PurgeCSS

PurgeCSS[^3] is **OPTIONAL**. You **SHOULD** rely on your build's own dead
code elimination first and reach for PurgeCSS only where none exists.
Tailwind[^4] already emits nothing but the utilities it finds in your sources,
so layering PurgeCSS over a Tailwind build gains nothing and adds the risks
below. Bundlers are weaker here: Vite 8[^13] keeps a stylesheet in the bundle
even when the JavaScript module that imported it is tree-shaken away, because
a CSS import counts as a side effect. Hand-written stylesheets and whole
component libraries are where PurgeCSS earns its place.

You **MUST** measure the unused bytes in a production bundle before adopting
PurgeCSS, and **MUST NOT** adopt it on the assumption that a stylesheet is
wasteful.

### Why measurement comes first

PurgeCSS's default extractor treats every word in a content file as a
selector. It cannot see a class name a program assembles at run time, so it
deletes rules that are live in production. Given this component:

```javascript
// src/app.js
const state = "success";
document.getElementById("a").className = "alert-" + state;
```

the extractor records `alert-` and `state`, never `alert-success`, and both
`.alert-success` and `.alert-error` are stripped from the stylesheet. Nothing
in the build fails; the page simply renders unstyled in production.

The extractor's limitations are documented, and the framework-specific
extractors that address them carry an upstream warning that they are a work in
progress and not encouraged for production use. You **SHOULD NOT** rely on a
`purgecss-from-*` extractor to make a purge safe. Prefer static, greppable
class names in your markup, and safelist whatever remains dynamic.

### Auditing before purging

You **MUST** run PurgeCSS in report mode before you let it write any files.
`--rejected` lists what it would remove and writes nothing:

```bash
npx purgecss --css src/app.css --content 'src/**/*.html' 'src/**/*.js' --rejected
```

```json
[{"css":".static-used { color: blue; }\n","file":"src/app.css",
  "rejected":[".alert-success",".alert-error",".never-used"]}]
```

Review every rejected selector. Without `--output`, PurgeCSS prints this JSON
to stdout; with it, PurgeCSS writes purged stylesheets to the given directory.

### Configuration

You **MUST** pin PurgeCSS, **MUST** cover every source of markup in `content`
— server templates and generated pages included, not just `.html` and `.js`
under `src/` — and **MUST** safelist every dynamically constructed selector:

```bash
npm install --save-dev purgecss@8.0.0
```

```javascript
// purgecss.config.js
module.exports = {
  content: [
    './src/**/*.{html,js,ts,jsx,tsx}',
    './templates/**/*.{html,jinja,erb}',
  ],
  css: ['./build/css/*.css'],
  output: './dist/css/',
  safelist: {
    standard: ['is-active', 'has-error'],
    greedy: [/^alert-/, /^col-\d+$/],
  },
};
```

Read `css` and write `output` in separate directories: PurgeCSS writes each
purged file under its base name, so a flat output directory collapses
same-named stylesheets drawn from different source directories.

Where a rule is easier to protect at its definition than in a central list,
safelist it in the stylesheet itself:

```css
/* purgecss ignore */
.alert-success { color: green; }
```

Do:

```javascript
// Class names are literal, so the extractor can find them
const CLASSES = { success: 'alert-success', error: 'alert-error' };
element.className = CLASSES[state];
```

Don't:

```javascript
// Assembled at run time; invisible to the extractor and silently purged
element.className = 'alert-' + state;
```

### Regression testing

A purge is a change to production styling that no unit test observes. You
**MUST** run visual and interaction regression tests against the purged
bundle, not against the development build, and **MUST** exercise every state
that reveals a dynamic class — errors, empty states, modals, and any markup
rendered only after user input. See the
[Testing Guide](../process/testing.md) for visual regression strategies.

## Best Practices

### Custom Properties

You **SHOULD** use CSS custom properties for design tokens:

```css
:root {
  --color-primary: #3b82f6;
  --color-secondary: #6366f1;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --font-sans: system-ui, sans-serif;
}

.button {
  background: var(--color-primary);
  padding: var(--spacing-sm) var(--spacing-md);
}
```

### Logical Properties

You **SHOULD** use logical properties for internationalization and RTL support:

```css
/* Use logical properties for RTL support */
.card {
  margin-inline-start: 1rem;  /* Not margin-left */
  padding-block: 1rem;        /* Not padding-top/bottom */
}
```

### Container Queries

You **MAY** use container queries for component-based responsive design:

```css
.card-container {
  container-type: inline-size;
}

@container (min-width: 400px) {
  .card {
    display: flex;
  }
}
```

## Pre-commit Configuration

```yaml
repos:
  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v4.0.0-alpha.8
    hooks:
      - id: prettier
        types: [css, scss]

  - repo: https://github.com/thibaudcolas/pre-commit-stylelint
    rev: v16.0.0
    hooks:
      - id: stylelint
        additional_dependencies:
          - stylelint@16.0.0
          - stylelint-config-standard@36.0.0
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
      - run: npx stylelint "**/*.css"
      - run: npx prettier --check "**/*.css"
```

## References

[^1]: [Stylelint](https://stylelint.io/) - A mighty CSS linter that helps you avoid errors and enforce conventions
[^2]: [Prettier](https://prettier.io/) - An opinionated code formatter with support for CSS, SCSS, Less, and more
[^3]: [PurgeCSS](https://purgecss.com/) - Remove unused CSS to optimize your final bundle size
[^4]: [Tailwind CSS](https://tailwindcss.com/) - A utility-first CSS framework for rapidly building custom user interfaces
[^5]: [Bulma](https://bulma.io/) - A modern CSS framework based on Flexbox
[^6]: [Bootstrap](https://getbootstrap.com/) - The most popular HTML, CSS, and JS framework for developing responsive, mobile-first projects
[^7]: [Sass](https://sass-lang.com/) - CSS with superpowers - the most mature, stable, and powerful professional grade CSS extension language
[^8]: [Less](https://lesscss.org/) - A dynamic preprocessor style sheet language that can be compiled into CSS
[^9]: [styled-components](https://styled-components.com/) - Visual primitives for the component age - use the best bits of ES6 and CSS to style your apps
[^10]: [Visual Studio Code](https://code.visualstudio.com/) - A lightweight but powerful source code editor with rich ecosystem of extensions
[^11]: [Lightning CSS](https://lightningcss.dev/) - An extremely fast CSS parser, transformer, bundler, and minifier written in Rust
[^12]: [PostCSS](https://postcss.org/) - A tool for transforming CSS with JavaScript plugins
[^13]: [Vite](https://vitejs.dev/) - Next generation frontend tooling with instant server start and lightning fast HMR
[^14]: [BEM](https://getbem.com/) - Block Element Modifier methodology for creating reusable components and code sharing in front-end development

## See Also

- [TypeScript Style Guide](typescript.md) - For CSS-in-JS and styled-components
- [Testing Guide](../testing.md) - Visual regression testing strategies
- [CI/CD Guide](../ci.md) - Continuous integration best practices
- [Google HTML/CSS Style Guide](google/htmlcss.html) - Base style guide
- [MDN CSS Reference](https://developer.mozilla.org/en-US/docs/Web/CSS)
- [Can I Use](https://caniuse.com/) - Browser compatibility tables
