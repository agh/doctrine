# Design Systems

> [Doctrine](../../README.md) > [Design](./README.md) > Design Systems

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

---

## Overview

A design system is the single source of truth for visual design decisions.
It ensures consistency across interfaces, accelerates development, and makes
design intent explicit through code.

## Quick Reference

| Concept         | Implementation          | Purpose                            |
| --------------- | ----------------------- | ---------------------------------- |
| Design tokens   | CSS custom properties   | Single source of truth for values  |
| Primitives      | Base components         | Building blocks for composition    |
| Semantic tokens | Named by purpose        | Abstract meaning from raw values   |
| Theming         | Token overrides         | Support light/dark/custom themes   |

---

## Design Tokens

### What Are Design Tokens?

Design tokens are named values representing design decisions. Instead of
hardcoding `#3b82f6`, use `var(--color-primary)`. This abstraction enables:

- Consistent values across the codebase
- Theme switching without code changes
- Design changes without hunting for hex values
- Clear communication between designers and developers

### Token Architecture

Tokens MUST be organized in three layers:

```text
┌─────────────────────────────────────────────────────────────┐
│  Component Tokens (highest specificity)                     │
│  --button-bg, --card-border, --input-focus-ring            │
├─────────────────────────────────────────────────────────────┤
│  Semantic Tokens (meaning-based)                            │
│  --color-primary, --text-secondary, --surface-elevated     │
├─────────────────────────────────────────────────────────────┤
│  Primitive Tokens (raw values)                              │
│  --blue-500, --gray-100, --space-4                         │
└─────────────────────────────────────────────────────────────┘
```

**Why three layers?**

- **Primitives** define the palette of available values
- **Semantic tokens** assign meaning to primitives
- **Component tokens** allow component-specific customization

Components SHOULD reference semantic tokens. Semantic tokens MUST reference
primitives. Primitives MUST contain raw values.

---

## Typography

### Font Stack

Projects MUST define a complete font stack with fallbacks:

```css
:root {
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI',
               Roboto, 'Helvetica Neue', Arial, sans-serif;
  --font-mono: 'JetBrains Mono', 'SF Mono', 'Fira Code', Consolas,
               'Liberation Mono', monospace;
}
```

**Why Inter?**

- Designed for screens, optimized for UI
- Excellent legibility at small sizes
- Variable font support for precise weight control
- Open source, widely available

**Why JetBrains Mono?**

- Clear character distinction (0/O, 1/l/I)
- Designed for code readability
- Consistent character width

### Type Scale

The type scale MUST be based on a consistent ratio. Recommended: Major Third
(1.25) or Perfect Fourth (1.333).

```css
:root {
  --text-xs:   0.75rem;   /* 12px */
  --text-sm:   0.875rem;  /* 14px */
  --text-base: 1rem;      /* 16px - body text */
  --text-lg:   1.25rem;   /* 20px */
  --text-xl:   1.5rem;    /* 24px */
  --text-2xl:  2rem;      /* 32px */
  --text-3xl:  2.5rem;    /* 40px */
}
```

**Usage guidelines:**

| Size          | Use Case                                 |
| ------------- | ---------------------------------------- |
| `--text-xs`   | Captions, badges, timestamps             |
| `--text-sm`   | Secondary text, table cells, form labels |
| `--text-base` | Body text, primary content               |
| `--text-lg`   | Section headers, card titles             |
| `--text-xl`   | Page titles                              |
| `--text-2xl`  | Hero numbers, dashboard metrics          |
| `--text-3xl`  | Marketing headlines (sparingly)          |

### Font Weights

```css
:root {
  --font-normal:   400;  /* Body text */
  --font-medium:   500;  /* Emphasized text, labels */
  --font-semibold: 600;  /* Headings, important values */
  --font-bold:     700;  /* Hero numbers, critical emphasis */
}
```

### Line Height

```css
:root {
  --leading-none:    1;      /* Single-line elements */
  --leading-tight:   1.25;   /* Headings */
  --leading-snug:    1.375;  /* Subheadings */
  --leading-normal:  1.5;    /* Body text (default) */
  --leading-relaxed: 1.625;  /* Long-form content */
}
```

Body text MUST use `--leading-normal` (1.5) minimum for readability.

---

## Color System

### Color Space

Colors SHOULD be defined in OKLCH for perceptual uniformity:

```css
/* OKLCH: Lightness, Chroma, Hue */
--blue-500: oklch(58% 0.20 250);
```

**Why OKLCH?**

- Perceptually uniform: equal steps look equal
- Predictable lightness across hues
- Better for generating color scales programmatically

When OKLCH is not supported, provide HSL or hex fallbacks.

### Color Architecture

#### Primitive Colors

Raw color values forming the complete palette:

```css
:root {
  /* Gray scale */
  --gray-50:  #fafafa;
  --gray-100: #f4f4f5;
  --gray-200: #e4e4e7;
  --gray-300: #d4d4d8;
  --gray-400: #a1a1aa;
  --gray-500: #71717a;
  --gray-600: #52525b;
  --gray-700: #3f3f46;
  --gray-800: #27272a;
  --gray-900: #18181b;
  --gray-950: #09090b;

  /* Primary (example: indigo) */
  --primary-50:  #eef2ff;
  --primary-100: #e0e7ff;
  --primary-500: #6366f1;
  --primary-600: #4f46e5;
  --primary-700: #4338ca;
}
```

#### Semantic Colors

Named by purpose, not appearance:

```css
:root {
  /* Surfaces */
  --surface-page:     var(--gray-50);
  --surface-card:     white;
  --surface-elevated: white;
  --surface-inset:    var(--gray-100);

  /* Text */
  --text-primary:   var(--gray-900);
  --text-secondary: var(--gray-600);
  --text-tertiary:  var(--gray-500);
  --text-muted:     var(--gray-400);

  /* Borders */
  --border-default:  var(--gray-200);
  --border-muted:    var(--gray-100);
  --border-emphasis: var(--gray-300);

  /* Interactive */
  --interactive-default: var(--primary-500);
  --interactive-hover:   var(--primary-600);
  --interactive-active:  var(--primary-700);

  /* Status */
  --status-success: #10b981;
  --status-warning: #f59e0b;
  --status-error:   #ef4444;
  --status-info:    #3b82f6;
}
```

### Dark Mode

Dark mode MUST NOT simply invert colors. It requires intentional design:

```css
.dark {
  /* Surfaces - true blacks for OLED efficiency */
  --surface-page:     #000000;
  --surface-card:     #0a0a0a;
  --surface-elevated: #141414;
  --surface-inset:    #050505;

  /* Text - reduced brightness to prevent eye strain */
  --text-primary:   #f4f4f5;
  --text-secondary: #a1a1aa;
  --text-tertiary:  #71717a;
  --text-muted:     #52525b;

  /* Borders - subtle in dark mode */
  --border-default: #27272a;
  --border-muted:   #1a1a1a;

  /* Interactive - slightly lighter for visibility */
  --interactive-default: #818cf8;
  --interactive-hover:   #a5b4fc;
}
```

**Dark mode principles:**

1. Reduce overall brightness to prevent eye strain
2. Use true black (#000) for OLED efficiency when appropriate
3. Maintain or increase contrast ratios
4. Test semantic colors for visibility
5. Consider dimming images slightly

### Contrast Requirements

All color combinations MUST meet WCAG 2.1 AA requirements:

| Element                            | Minimum Contrast |
| ---------------------------------- | ---------------- |
| Normal text (<18px)                | 4.5:1            |
| Large text (>=18px or >=14px bold) | 3:1              |
| UI components and graphics         | 3:1              |
| Focus indicators                   | 3:1              |

Use tools like [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
to verify.

---

## Spacing System

### Base Unit

Spacing MUST be based on a consistent unit. Recommended: 4px base.

```css
:root {
  --space-0:    0;
  --space-px:   1px;
  --space-0.5:  0.125rem;  /* 2px */
  --space-1:    0.25rem;   /* 4px */
  --space-1.5:  0.375rem;  /* 6px */
  --space-2:    0.5rem;    /* 8px */
  --space-3:    0.75rem;   /* 12px */
  --space-4:    1rem;      /* 16px */
  --space-5:    1.25rem;   /* 20px */
  --space-6:    1.5rem;    /* 24px */
  --space-8:    2rem;      /* 32px */
  --space-10:   2.5rem;    /* 40px */
  --space-12:   3rem;      /* 48px */
  --space-16:   4rem;      /* 64px */
  --space-20:   5rem;      /* 80px */
  --space-24:   6rem;      /* 96px */
}
```

### Usage Guidelines

| Context                    | Recommended Spacing          |
| -------------------------- | ---------------------------- |
| Inline element gap         | `--space-1` to `--space-2`   |
| Related items              | `--space-2` to `--space-3`   |
| Component internal padding | `--space-3` to `--space-4`   |
| Card padding               | `--space-4` to `--space-6`   |
| Section gap                | `--space-6` to `--space-8`   |
| Page sections              | `--space-12` to `--space-16` |

**Never use arbitrary values.** If the scale doesn't fit, reconsider the design
rather than introducing one-off spacing.

---

## Border Radius

### Radius Scale

```css
:root {
  --radius-none: 0;
  --radius-sm:   4px;   /* Small elements: badges, tags */
  --radius-md:   6px;   /* Inputs, small buttons */
  --radius-lg:   8px;   /* Buttons, small cards */
  --radius-xl:   12px;  /* Cards, panels */
  --radius-2xl:  16px;  /* Large cards, modals */
  --radius-3xl:  24px;  /* Hero elements */
  --radius-full: 9999px; /* Pills, avatars */
}
```

### Usage Guidelines

| Element              | Radius          |
| -------------------- | --------------- |
| Badges, tags         | `--radius-sm`   |
| Inputs, select       | `--radius-md`   |
| Buttons              | `--radius-lg`   |
| Cards                | `--radius-xl`   |
| Modals               | `--radius-2xl`  |
| Avatars, status dots | `--radius-full` |

Consistency in radius creates visual harmony. Mixing many different radii
creates visual discord.

---

## Shadows

### Shadow Scale

```css
:root {
  --shadow-sm:
    0 1px 2px 0 rgb(0 0 0 / 0.05);

  --shadow-md:
    0 4px 6px -1px rgb(0 0 0 / 0.1),
    0 2px 4px -2px rgb(0 0 0 / 0.1);

  --shadow-lg:
    0 10px 15px -3px rgb(0 0 0 / 0.1),
    0 4px 6px -4px rgb(0 0 0 / 0.1);

  --shadow-xl:
    0 20px 25px -5px rgb(0 0 0 / 0.1),
    0 8px 10px -6px rgb(0 0 0 / 0.1);
}
```

### Elevation System

| Level | Shadow        | Usage                               |
| ----- | ------------- | ----------------------------------- |
| 0     | none          | Flat elements, inline content       |
| 1     | `--shadow-sm` | Cards at rest                       |
| 2     | `--shadow-md` | Cards on hover, dropdowns           |
| 3     | `--shadow-lg` | Modals, popovers                    |
| 4     | `--shadow-xl` | Command palette, important overlays |

In dark mode, shadows are less visible. Consider using subtle borders or
background color differences to indicate elevation instead.

---

## Z-Index

### Z-Index Scale

Establish a z-index scale to prevent z-index wars:

```css
:root {
  --z-base:           0;
  --z-dropdown:       10;
  --z-sticky:         20;
  --z-fixed:          30;
  --z-modal-backdrop: 40;
  --z-modal:          50;
  --z-popover:        60;
  --z-tooltip:        70;
  --z-toast:          80;
  --z-max:            9999;
}
```

Components MUST use these tokens. Arbitrary z-index values MUST NOT be used.

---

## Theming

### Theme Implementation

Themes MUST be implemented via CSS custom property overrides:

```css
/* Base theme (light) */
:root {
  --surface-page: white;
  --text-primary: #18181b;
}

/* Dark theme */
.dark,
[data-theme="dark"] {
  --surface-page: #000000;
  --text-primary: #f4f4f5;
}

/* High contrast theme */
[data-theme="high-contrast"] {
  --surface-page: white;
  --text-primary: black;
  --border-default: black;
}
```

### Theme Switching

```javascript
function setTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('theme', theme);
}

// Respect system preference
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)');
if (!localStorage.getItem('theme')) {
  setTheme(prefersDark.matches ? 'dark' : 'light');
}
```

### Theme Requirements

All themes MUST:

1. Meet WCAG 2.1 AA contrast requirements
2. Be tested with all UI components
3. Support `prefers-color-scheme` media query
4. Persist user preference in `localStorage`
5. Apply without page reload (CSS custom properties enable this)

---

## Anti-Patterns

### Hardcoded Values

```css
/* ✗ DON'T: Hardcoded values */
.card {
  padding: 16px;
  border-radius: 8px;
  background: #ffffff;
}

/* ✓ DO: Design tokens */
.card {
  padding: var(--space-4);
  border-radius: var(--radius-xl);
  background: var(--surface-card);
}
```

### Magic Numbers

```css
/* ✗ DON'T: Arbitrary values */
.modal {
  z-index: 99999;
  padding: 23px;
}

/* ✓ DO: System values */
.modal {
  z-index: var(--z-modal);
  padding: var(--space-6);
}
```

### One-Off Colors

```css
/* ✗ DON'T: Inline colors */
.warning-text {
  color: #f5a623;
}

/* ✓ DO: Semantic tokens */
.warning-text {
  color: var(--status-warning);
}
```

---

## Implementation Checklist

- [ ] All values use design tokens (no hardcoded values)
- [ ] Token architecture has three layers (primitive, semantic, component)
- [ ] Type scale based on consistent ratio
- [ ] Spacing based on consistent unit
- [ ] Dark mode intentionally designed (not inverted)
- [ ] All color combinations meet WCAG AA contrast
- [ ] Z-index uses defined scale
- [ ] Theme switching works without page reload
- [ ] System theme preference respected

---

## See Also

- [CSS](../languages/css.md) - CSS language standards
- [Tailwind](../frameworks/tailwind.md) - Tailwind CSS configuration
- [Components](./components.md) - Component patterns
- [Accessibility](./accessibility.md) - Accessibility standards
