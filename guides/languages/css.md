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
| Dead code | PurgeCSS[^3] | `npx purgecss --css *.css --content *.html` |
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

```bash
npm install -D tailwindcss
npx tailwindcss init
```

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

You **SHOULD** use PurgeCSS[^3] to remove unused CSS in production builds.

```bash
npm install --save-dev purgecss
```

```javascript
// purgecss.config.js
module.exports = {
  content: ['./src/**/*.html', './src/**/*.js'],
  css: ['./src/**/*.css'],
  output: './dist/',
};
```

Note: Tailwind[^4] includes PurgeCSS[^3] automatically.

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
