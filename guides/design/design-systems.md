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
  --primary-200: #c7d2fe;
  --primary-300: #a5b4fc;
  --primary-400: #818cf8;
  --primary-500: #6366f1;
  --primary-600: #4f46e5;
  --primary-700: #4338ca;
  --primary-800: #3730a3;
  --primary-950: #1e1b4b;

  /* Success (green) */
  --success-50:  #ecfdf5;
  --success-300: #6ee7b7;
  --success-400: #34d399;
  --success-700: #047857;
  --success-800: #065f46;
  --success-950: #022c22;

  /* Warning (amber) */
  --warning-50:  #fffbeb;
  --warning-300: #fcd34d;
  --warning-400: #fbbf24;
  --warning-700: #b45309;
  --warning-800: #92400e;
  --warning-950: #451a03;

  /* Error (red) */
  --error-50:  #fef2f2;
  --error-300: #fca5a5;
  --error-400: #f87171;
  --error-700: #b91c1c;
  --error-800: #991b1b;
  --error-950: #450a0a;

  /* Info (blue) */
  --info-50:  #eff6ff;
  --info-300: #93c5fd;
  --info-400: #60a5fa;
  --info-700: #1d4ed8;
  --info-800: #1e40af;
  --info-950: #172554;
}
```

Primitives carry no accessibility guarantee. `--primary-500` is legible on white
as a fill but not as body text; `--gray-400` is legible on black but not on
white. A primitive becomes safe only once a semantic token pairs it with an
approved background, as the [contrast tables](#contrast-requirements) below do.
Primitives are not part of a component's API — components reference semantic
tokens, as [Token Architecture](#token-architecture) requires.

#### Semantic Colors

Named by purpose, not appearance. Every semantic foreground token MUST declare
the role it serves — text, icon, control boundary, or fill — because WCAG sets a
different threshold for each. A token MUST NOT be reused in another role until
the new pairing has been measured.

```css
:root {
  color-scheme: light;

  /* Surfaces: the approved backgrounds for every text token below */
  --surface-page:     var(--gray-50);
  --surface-card:     #ffffff;
  --surface-elevated: #ffffff;
  --surface-inset:    var(--gray-100);

  /* Text: 4.5:1 or better on every surface above */
  --text-primary:   var(--gray-900);
  --text-secondary: var(--gray-700);
  --text-muted:     var(--gray-600);
  --text-on-fill:   #ffffff;

  /* Inactive controls only: exempt from SC 1.4.3, MUST NOT carry meaning */
  --text-disabled:  var(--gray-400);

  /* Icons and control boundaries: 3:1 or better (SC 1.4.11) */
  --icon-default:   var(--gray-700);
  --icon-subtle:    var(--gray-500);
  --border-control: var(--gray-500);

  /* Decorative rules: convey nothing, so no minimum applies */
  --border-default:  var(--gray-200);
  --border-muted:    var(--gray-100);
  --border-emphasis: var(--gray-300);

  /* Interactive: text or icon on a surface, or a fill under --text-on-fill */
  --interactive-default: var(--primary-600);
  --interactive-hover:   var(--primary-700);
  --interactive-active:  var(--primary-800);

  /* Status: one text/icon value, one tint surface, one solid fill per hue */
  --status-success:            var(--success-700);
  --status-success-surface:    var(--success-50);
  --status-success-on-surface: var(--success-800);
  --status-success-fill:       var(--success-800);

  --status-warning:            var(--warning-700);
  --status-warning-surface:    var(--warning-50);
  --status-warning-on-surface: var(--warning-800);
  --status-warning-fill:       var(--warning-800);

  --status-error:            var(--error-700);
  --status-error-surface:    var(--error-50);
  --status-error-on-surface: var(--error-800);
  --status-error-fill:       var(--error-800);

  --status-info:            var(--info-700);
  --status-info-surface:    var(--info-50);
  --status-info-on-surface: var(--info-800);
  --status-info-fill:       var(--info-800);

  /* Rings: solid indicator plus an optional translucent halo */
  --focus-ring-color:  var(--interactive-default);
  --focus-ring-width:  2px;
  --focus-ring-offset: 2px;
  --focus-ring-halo:   color-mix(in srgb, var(--interactive-default) 25%, transparent);
  --error-ring-halo:   color-mix(in srgb, var(--status-error) 25%, transparent);
}
```

**Why the role split?** WCAG 2.1 requires 4.5:1 for body text (SC 1.4.3) but
only 3:1 for icons, control boundaries, and focus indicators (SC 1.4.11). A
single `--status-error` tuned for a 3:1 badge fill fails as error-message text;
a single value tuned for text is needlessly dark as a fill. Naming the role in
the token makes the applicable threshold, and therefore the required test,
unambiguous.

**Why `--text-disabled` is separate.** SC 1.4.3 exempts "inactive user
interface components". `--text-disabled` is the only token permitted to fall
below 4.5:1, and only on a control that is genuinely disabled. Placeholder text
is *not* exempt — WCAG states the criterion "applies to text in the page,
including placeholder text" — so placeholders MUST use `--text-muted` or
stronger.

```css
/* ✗ DON'T: a 3:1 icon token as text (4.39:1), or a disabled token as
   placeholder (2.33:1) */
.hint        { color: var(--icon-subtle); background: var(--surface-inset); }
.placeholder { color: var(--text-disabled); }

/* ✓ DO: use the token whose role matches the pixels (7.03:1 for both) */
.hint        { color: var(--text-muted); background: var(--surface-inset); }
.placeholder { color: var(--text-muted); }
```

#### Alpha and Translucent Tokens

`var()` takes a custom-property name and an optional fallback only. It has no
slash syntax, so `var(--status-error / 0.15)` is a parse error and the whole
declaration is dropped — silently removing a focus ring in a rule that has
already set `outline: none`. Translucent values MUST be produced with
[`color-mix()`](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Values/color_value/color-mix),
Baseline widely available since May 2023 (Chrome 111, Edge 111, Firefox 113,
Safari 16.2).

```css
/* ✗ DON'T: var() has no alpha channel */
.form-input:focus { box-shadow: 0 0 0 3px var(--interactive-default / 0.15); }

/* ✓ DO: mix the token with transparent, and keep a solid indicator */
.form-input:focus-visible {
  outline: var(--focus-ring-width) solid var(--focus-ring-color);
  outline-offset: var(--focus-ring-offset);
  box-shadow: 0 0 0 3px var(--focus-ring-halo);
}
```

The halo is decoration. A translucent 25% mix cannot reach the 3:1 that SC
1.4.11 demands of a focus indicator, so the solid `outline` MUST remain.

### Dark Mode

Dark mode MUST NOT simply invert colors. It requires intentional design, and it
MUST redefine every semantic token the light theme defines — a partial override
leaves light-theme surfaces underneath dark-theme text:

```css
:root[data-theme="dark"] {
  color-scheme: dark;

  /* Surfaces: true blacks for OLED efficiency */
  --surface-page:     #000000;
  --surface-card:     #0a0a0a;
  --surface-elevated: #141414;
  --surface-inset:    #050505;

  /* Text: reduced brightness, still 4.5:1 on every surface above */
  --text-primary:   var(--gray-100);
  --text-secondary: var(--gray-300);
  --text-muted:     var(--gray-400);
  --text-on-fill:   var(--gray-950);
  --text-disabled:  var(--gray-600);

  --icon-default:   var(--gray-300);
  --icon-subtle:    var(--gray-500);
  --border-control: var(--gray-500);

  /* Borders: subtle in dark mode */
  --border-default:  var(--gray-800);
  --border-muted:    #1a1a1a;
  --border-emphasis: var(--gray-700);

  /* Interactive: lighter fills, so the on-fill foreground becomes dark */
  --interactive-default: var(--primary-400);
  --interactive-hover:   var(--primary-300);
  --interactive-active:  var(--primary-200);

  --status-success:            var(--success-400);
  --status-success-surface:    var(--success-950);
  --status-success-on-surface: var(--success-300);
  --status-success-fill:       var(--success-400);

  --status-warning:            var(--warning-400);
  --status-warning-surface:    var(--warning-950);
  --status-warning-on-surface: var(--warning-300);
  --status-warning-fill:       var(--warning-400);

  --status-error:            var(--error-400);
  --status-error-surface:    var(--error-950);
  --status-error-on-surface: var(--error-300);
  --status-error-fill:       var(--error-400);

  --status-info:            var(--info-400);
  --status-info-surface:    var(--info-950);
  --status-info-on-surface: var(--info-300);
  --status-info-fill:       var(--info-400);
}
```

**Dark mode principles:**

1. Reduce overall brightness to prevent eye strain
2. Use true black (#000) for OLED efficiency when appropriate
3. Maintain or increase contrast ratios
4. Flip the on-fill foreground: light fills need dark ink
5. Test semantic colors for visibility
6. Consider dimming images slightly

**Why one selector for the whole palette?** Splitting a theme across `.dark`
and `[data-theme="dark"]` means one selector wins for surfaces and the other
for text. Setting `data-theme="dark"` on a document whose dark palette is
keyed to `.dark` leaves `--surface-card` at its light value while
`--text-primary` flips: `#f4f4f5` on `#ffffff` measures 1.09:1. Themes MUST
therefore use exactly one selector contract, and `--surface-*` and `--text-*`
MUST flip together.

**Why `:root[data-theme="dark"]` rather than `[data-theme="dark"]`?** A bare
attribute selector has the same specificity as `:root`, so any later `:root`
block that touches a themed token silently defeats the theme — the token
reverts while its neighbours do not, which is the same broken pairing by
another route. Theme selectors MUST out-specify the base `:root` block.

```css
/* ✗ DON'T: two contracts, so surfaces and text disagree */
.dark { --surface-card: #0a0a0a; --text-primary: #f4f4f5; }
[data-theme="dark"] { --text-primary: #f4f4f5; }

/* ✓ DO: one contract, complete palette, out-specifying :root */
:root[data-theme="dark"] {
  --surface-card: #0a0a0a;
  --text-primary: #f4f4f5;
}
```

### Contrast Requirements

All color combinations MUST meet WCAG 2.1 AA. WCAG defines large-scale text in
points, not CSS pixels:

| Element                                         | Minimum Contrast |
| ----------------------------------------------- | ---------------- |
| Normal text, below the large-scale threshold    | 4.5:1            |
| Large text: 18pt (24px), or 14pt bold (18.67px) | 3:1              |
| UI components and graphical objects             | 3:1              |
| Focus indicators                                | 3:1              |

`1pt = 1.333px`, so 18pt is 24 CSS px and 14pt bold is 18.67 CSS px. WCAG's
own note rounds these to "approximately 18.5px and 24px"; when working in CSS
pixels you MUST round the bold threshold *up*, to 19px, because 18.5px is
smaller than 14pt. **18px normal-weight text is not large text** and MUST meet
4.5:1.

Three further rules apply:

- Ratios MUST NOT be rounded up. WCAG treats the thresholds as exact, so
  4.499:1 fails 4.5:1.
- Very thin or unusual faces render fainter than their declared colour. Such
  faces SHOULD exceed the normative ratio rather than sit on it.
- Placeholder text, hover text, and focus-revealed text are text. Only
  genuinely inactive controls are exempt.

Use tools like [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
to verify.

#### Measured Token Pairings

Every pairing below was computed with the WCAG relative-luminance formula and
truncated, never rounded up. The worst case for light-theme text is
`--surface-inset` (`#f4f4f5`); for dark-theme text it is `--surface-elevated`
(`#141414`).

| Light-theme pairing                                   | Ratio    | Required |
| ----------------------------------------------------- | -------- | -------- |
| `--text-primary` on the worst surface                 | 16.11:1  | 4.5:1    |
| `--text-secondary` on the worst surface               | 9.50:1   | 4.5:1    |
| `--text-muted` on the worst surface                   | 7.03:1   | 4.5:1    |
| `--icon-subtle` / `--border-control` on worst surface | 4.39:1   | 3:1      |
| `--interactive-default` as text on worst surface      | 5.72:1   | 4.5:1    |
| `--text-on-fill` on `--interactive-default`           | 6.28:1   | 4.5:1    |
| `--text-on-fill` on `--interactive-hover`             | 7.90:1   | 4.5:1    |
| `--text-on-fill` on `--interactive-active`            | 9.93:1   | 4.5:1    |
| `--status-success` on the worst surface               | 4.98:1   | 4.5:1    |
| `--status-warning` on the worst surface               | 4.56:1   | 4.5:1    |
| `--status-error` on the worst surface                 | 5.88:1   | 4.5:1    |
| `--status-info` on the worst surface                  | 6.09:1   | 4.5:1    |
| `--status-*-on-surface` on `--status-*-surface`       | 6.83:1 + | 4.5:1    |
| `--text-on-fill` on `--status-*-fill`                 | 7.09:1 + | 4.5:1    |

| Dark-theme pairing                                    | Ratio    | Required |
| ----------------------------------------------------- | -------- | -------- |
| `--text-primary` on the worst surface                 | 16.76:1  | 4.5:1    |
| `--text-secondary` on the worst surface               | 12.46:1  | 4.5:1    |
| `--text-muted` on the worst surface                   | 7.18:1   | 4.5:1    |
| `--icon-subtle` / `--border-control` on worst surface | 3.81:1   | 3:1      |
| `--interactive-default` as text on worst surface      | 6.17:1   | 4.5:1    |
| `--text-on-fill` on `--interactive-default`           | 6.66:1   | 4.5:1    |
| `--text-on-fill` on `--interactive-hover`             | 9.97:1   | 4.5:1    |
| `--text-on-fill` on `--interactive-active`            | 13.33:1  | 4.5:1    |
| `--status-success` on the worst surface               | 9.58:1   | 4.5:1    |
| `--status-warning` on the worst surface               | 11.03:1  | 4.5:1    |
| `--status-error` on the worst surface                 | 6.66:1   | 4.5:1    |
| `--status-info` on the worst surface                  | 7.24:1   | 4.5:1    |
| `--status-*-on-surface` on `--status-*-surface`       | 8.14:1 + | 4.5:1    |
| `--text-on-fill` on `--status-*-fill`                 | 7.19:1 + | 4.5:1    |

`--text-disabled` (2.33:1 light, 2.38:1 dark) and the decorative
`--border-default` / `--border-muted` / `--border-emphasis` tokens are the only
entries below threshold. They MUST be confined to inactive controls and
non-meaningful rules respectively.

`--status-warning` has the least headroom in the light theme. Changing any
light surface MUST trigger a re-run of the contrast suite below.

#### Testing Contrast

Contrast MUST be asserted in CI, once per theme, role, and state. Palettes
drift; a test is the only thing that notices. The check needs no dependencies —
Node.js 20 or later ships a stable `node:test` runner:

```javascript
// tokens.contrast.test.mjs — run with: node --test tokens.contrast.test.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';

const channel = (c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);

const luminance = (hex) => {
  const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255);
  return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b);
};

const contrast = (a, b) => {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
};

// Worst-case background per theme, then one row per foreground token.
const SUITE = [
  { theme: 'light', bg: '#f4f4f5', rows: [
    ['--text-primary', '#18181b', 4.5],
    ['--text-secondary', '#3f3f46', 4.5],
    ['--text-muted', '#52525b', 4.5],
    ['--icon-subtle', '#71717a', 3],
    ['--border-control', '#71717a', 3],
    ['--interactive-default', '#4f46e5', 4.5],
    ['--status-success', '#047857', 4.5],
    ['--status-warning', '#b45309', 4.5],
    ['--status-error', '#b91c1c', 4.5],
    ['--status-info', '#1d4ed8', 4.5],
  ] },
  { theme: 'dark', bg: '#141414', rows: [
    ['--text-primary', '#f4f4f5', 4.5],
    ['--text-secondary', '#d4d4d8', 4.5],
    ['--text-muted', '#a1a1aa', 4.5],
    ['--icon-subtle', '#71717a', 3],
    ['--border-control', '#71717a', 3],
    ['--interactive-default', '#818cf8', 4.5],
    ['--status-success', '#34d399', 4.5],
    ['--status-warning', '#fbbf24', 4.5],
    ['--status-error', '#f87171', 4.5],
    ['--status-info', '#60a5fa', 4.5],
  ] },
];

// Fills and tints are foreground/background pairs in their own right.
const PAIRS = [
  ['light interactive rest', '#ffffff', '#4f46e5', 4.5],
  ['light interactive hover', '#ffffff', '#4338ca', 4.5],
  ['light interactive active', '#ffffff', '#3730a3', 4.5],
  ['light error tint', '#991b1b', '#fef2f2', 4.5],
  ['dark interactive rest', '#09090b', '#818cf8', 4.5],
  ['dark interactive hover', '#09090b', '#a5b4fc', 4.5],
  ['dark interactive active', '#09090b', '#c7d2fe', 4.5],
  ['dark error tint', '#fca5a5', '#450a0a', 4.5],
];

for (const { theme, bg, rows } of SUITE) {
  for (const [token, fg, min] of rows) {
    test(`${theme}: ${token} on ${bg}`, () => {
      const ratio = contrast(fg, bg);
      assert.ok(ratio >= min, `${fg} on ${bg} is ${ratio.toFixed(4)}:1, needs ${min}:1`);
    });
  }
}

for (const [name, fg, bg, min] of PAIRS) {
  test(name, () => {
    const ratio = contrast(fg, bg);
    assert.ok(ratio >= min, `${fg} on ${bg} is ${ratio.toFixed(4)}:1, needs ${min}:1`);
  });
}
```

Extend `SUITE` whenever a theme is added and `PAIRS` whenever a new
foreground/background combination ships. A token with no row is untested.

---

## Spacing System

### Base Unit

Spacing MUST be based on a consistent unit. Recommended: 4px base.

```css
:root {
  --space-0:    0;
  --space-px:   1px;
  --space-0-5:  0.125rem;  /* 2px */
  --space-1:    0.25rem;   /* 4px */
  --space-1-5:  0.375rem;  /* 6px */
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

### Half-Step Names

A custom-property name is a `<dashed-ident>`, and an identifier MUST NOT
contain an unescaped full stop. Browsers do not warn: they discard the
declaration, `var(--space-0.5)` resolves to nothing, and the affected property
falls back to its inherited or initial value. Half steps MUST therefore be
spelled with a hyphen.

```css
/* ✗ DON'T: invalid identifier, silently dropped */
:root { --space-0.5: 0.125rem; }

/* ✓ DO: valid dashed identifier */
:root { --space-0-5: 0.125rem; }
```

Escaping the stop is also valid, but the escape belongs to CSS syntax only: the
declaration and every `var()` must be written `--space-0\.5`, while the CSSOM
name is the unescaped `--space-0.5`, so `getPropertyValue('--space-0\\.5')`
returns an empty string and `getPropertyValue('--space-0.5')` returns the
value. That asymmetry breaks token pipelines and theme-inspection code, so
escaping SHOULD NOT be used.

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

Themes MUST be implemented via CSS custom property overrides, and every theme
MUST use the same selector contract. This guide uses `data-theme` on the root
element throughout, because that is what the switcher below writes, and it
qualifies each theme with `:root` so a theme rule always out-specifies the base
block whatever the source order.

```css
/* Base theme (light) - see "Semantic Colors" for the complete token set */
:root {
  color-scheme: light;
  --surface-page: var(--gray-50);
  --text-primary: var(--gray-900);
}

/* Dark theme - defined once, in full, under "Dark Mode" */

/* High contrast theme */
:root[data-theme="high-contrast"] {
  color-scheme: light;
  --surface-page: #ffffff;
  --text-primary: #000000;
  --border-default: #000000;
}
```

A theme MUST override the whole semantic layer, not a subset. Overriding
`--text-primary` without `--surface-card` produces `#f4f4f5` on `#ffffff`, a
measured 1.09:1. A theme rule that redefines any `--text-*` token MUST also
redefine every `--surface-*` token, and vice versa.

### Theme Switching

The switcher stores the user's *preference* — including `system` — and writes
the *resolved* theme to `data-theme`, so the CSS only ever sees a concrete
theme name:

```javascript
const THEMES = ['light', 'dark', 'high-contrast'];
const systemDark = window.matchMedia('(prefers-color-scheme: dark)');

function resolveTheme(preference) {
  if (THEMES.includes(preference)) return preference;
  return systemDark.matches ? 'dark' : 'light';
}

function setTheme(preference) {
  document.documentElement.setAttribute('data-theme', resolveTheme(preference));
  localStorage.setItem('theme', preference);
}

setTheme(localStorage.getItem('theme') ?? 'system');

// Follow the system while the user has not chosen a specific theme
systemDark.addEventListener('change', () => {
  if ((localStorage.getItem('theme') ?? 'system') === 'system') setTheme('system');
});
```

**Why resolve rather than pass through?** `data-theme="system"` matches no rule,
so the document silently falls back to the light palette. Resolving in
JavaScript keeps one selector contract in CSS and lets the media query keep
working after load.

### Theme Requirements

All themes MUST:

1. Meet WCAG 2.1 AA contrast requirements, verified by the contrast suite
2. Redefine every semantic token, not a subset
3. Use a single selector contract, qualified so it out-specifies base `:root`
4. Be tested with all UI components
5. Support `prefers-color-scheme` for users who have expressed no preference
6. Persist user preference in `localStorage`
7. Apply without page reload (CSS custom properties enable this)

Switching a theme MUST be verified by reading the computed foreground and
background of a real component, not by inspecting the stylesheet.

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
- [ ] Every semantic foreground token names its role (text, icon, border, fill)
- [ ] Type scale based on consistent ratio
- [ ] Spacing based on consistent unit, half steps use valid identifiers
- [ ] Dark mode intentionally designed (not inverted)
- [ ] Every theme overrides the complete semantic layer under one selector
- [ ] All color combinations meet WCAG AA contrast, asserted by an automated test
- [ ] Translucent values use `color-mix()`, never a slash inside `var()`
- [ ] Z-index uses defined scale
- [ ] Theme switching works without page reload
- [ ] System theme preference respected

---

## See Also

- [CSS](../languages/css.md) - CSS language standards
- [Tailwind](../frameworks/tailwind.md) - Tailwind CSS configuration
- [Components](./components.md) - Component patterns
- [Accessibility](./accessibility.md) - Accessibility standards
