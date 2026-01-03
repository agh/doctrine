# Accessibility

> [Doctrine](../../README.md) > [Design](./README.md) > Accessibility

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

---

## Overview

Accessibility ensures interfaces work for everyone, regardless of ability.
This is not optional—it is a legal requirement in many jurisdictions and a
moral imperative everywhere.

All projects MUST meet WCAG 2.1 Level AA compliance at minimum.

## Quick Reference

| Category       | Key Requirements                                         |
| -------------- | -------------------------------------------------------- |
| Perceivable    | Text alternatives, color contrast, resizable text        |
| Operable       | Keyboard accessible, no time limits, no seizure triggers |
| Understandable | Readable, predictable, error prevention                  |
| Robust         | Compatible with assistive technologies                   |

---

## WCAG 2.1 AA Requirements

### 1. Perceivable

#### 1.1 Text Alternatives

All non-text content MUST have text alternatives:

```html
<!-- Images with meaning -->
<img src="chart.png" alt="Sales increased 25% from Q1 to Q2" />

<!-- Decorative images -->
<img src="decorative-line.svg" alt="" role="presentation" />

<!-- Icons with meaning -->
<svg role="img" aria-label="Warning">
  <use href="#icon-warning"></use>
</svg>

<!-- Icons that are decorative -->
<svg aria-hidden="true">
  <use href="#icon-decorative"></use>
</svg>
```

#### 1.3 Adaptable Structure

Content structure MUST be programmatically determinable:

```html
<!-- Use semantic HTML -->
<main>
  <article>
    <header>
      <h1>Page Title</h1>
    </header>
    <section aria-labelledby="section-1">
      <h2 id="section-1">Section Title</h2>
      <!-- Content -->
    </section>
  </article>
</main>

<!-- Use landmarks -->
<header role="banner">...</header>
<nav role="navigation" aria-label="Main">...</nav>
<main role="main">...</main>
<aside role="complementary">...</aside>
<footer role="contentinfo">...</footer>
```

#### 1.4 Distinguishable

**Color Contrast Requirements:**

| Content Type                         | Minimum Ratio |
| ------------------------------------ | ------------- |
| Normal text (< 18px)                 | 4.5:1         |
| Large text (>= 18px or >= 14px bold) | 3:1           |
| UI components                        | 3:1           |
| Focus indicators                     | 3:1           |

**Color Independence:**

Information MUST NOT be conveyed through color alone:

```html
<!-- ✗ DON'T: Color only -->
<span style="color: red">Error</span>

<!-- ✓ DO: Color + icon + text -->
<span class="error">
  <svg aria-hidden="true"><!-- error icon --></svg>
  Error: Invalid email address
</span>
```

**Text Resizing:**

- Text MUST be resizable up to 200% without loss of functionality
- Use relative units (`rem`, `em`) not pixels for text
- Test with browser zoom at 200%

---

### 2. Operable

#### 2.1 Keyboard Accessible

All functionality MUST be available via keyboard:

```css
/* Visible focus indicators */
:focus-visible {
  outline: 2px solid var(--interactive-default);
  outline-offset: 2px;
}

/* Never remove focus outline without replacement */
/* ✗ DON'T */
:focus { outline: none; }

/* ✓ DO */
:focus:not(:focus-visible) { outline: none; }
:focus-visible { outline: 2px solid var(--interactive-default); }
```

**Keyboard Navigation Requirements:**

| Key        | Expected Behavior                           |
| ---------- | ------------------------------------------- |
| Tab        | Move focus to next interactive element      |
| Shift+Tab  | Move focus to previous interactive element  |
| Enter      | Activate buttons, links, submit forms       |
| Space      | Activate buttons, toggle checkboxes         |
| Escape     | Close modals, dropdowns, cancel operations  |
| Arrow keys | Navigate within widgets (tabs, menus, etc.) |

**Focus Management:**

```javascript
// Return focus after modal close
function closeModal(modal, triggerElement) {
  modal.close();
  triggerElement.focus();
}

// Focus trap for modals
function trapFocus(container) {
  const focusable = container.querySelectorAll(
    'a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  const first = focusable[0];
  const last = focusable[focusable.length - 1];

  container.addEventListener('keydown', (e) => {
    if (e.key !== 'Tab') return;

    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  });
}
```

#### 2.4 Navigable

**Skip Links:**

```html
<body>
  <a href="#main-content" class="skip-link">Skip to main content</a>
  <nav>...</nav>
  <main id="main-content">...</main>
</body>
```

```css
.skip-link {
  position: absolute;
  left: -9999px;
  z-index: 999;
  padding: 1rem;
  background: var(--surface-card);
}

.skip-link:focus {
  left: 0;
}
```

**Descriptive Headings:**

- Each page MUST have one `<h1>`
- Headings MUST be hierarchical (no skipping levels)
- Headings MUST describe the content that follows

```html
<!-- ✓ DO: Proper hierarchy -->
<h1>Dashboard</h1>
  <h2>Recent Activity</h2>
  <h2>Statistics</h2>
    <h3>Monthly Overview</h3>
    <h3>Yearly Trends</h3>

<!-- ✗ DON'T: Skipped levels -->
<h1>Dashboard</h1>
  <h3>Recent Activity</h3>  <!-- Skipped h2 -->
```

**Descriptive Link Text:**

```html
<!-- ✗ DON'T: Vague link text -->
<a href="/docs">Click here</a>
<a href="/more">Read more</a>

<!-- ✓ DO: Descriptive link text -->
<a href="/docs">View documentation</a>
<a href="/more">Read more about accessibility</a>
```

---

### 3. Understandable

#### 3.1 Readable

**Language Declaration:**

```html
<html lang="en">
  <!-- Page content in English -->
  <p>Welcome to our site.</p>

  <!-- Content in different language -->
  <p lang="es">Bienvenido a nuestro sitio.</p>
</html>
```

#### 3.2 Predictable

- Navigation MUST be consistent across pages
- Components MUST behave consistently
- Focus changes MUST NOT cause unexpected context changes

#### 3.3 Input Assistance

**Error Identification:**

```html
<div class="form-field">
  <label for="email">Email</label>
  <input
    type="email"
    id="email"
    aria-invalid="true"
    aria-describedby="email-error"
  />
  <p id="email-error" class="error" role="alert">
    Please enter a valid email address (e.g., name@example.com)
  </p>
</div>
```

**Error Prevention:**

- Confirm destructive actions
- Allow users to review before submission
- Provide clear instructions before complex forms

---

### 4. Robust

#### 4.1 Compatible

**Valid HTML:**

- Use valid, semantic HTML
- Close all tags properly
- Use unique IDs

**ARIA Usage:**

ARIA supplements HTML—it does not replace it:

```html
<!-- ✗ DON'T: ARIA instead of semantic HTML -->
<div role="button" tabindex="0">Click me</div>

<!-- ✓ DO: Semantic HTML -->
<button>Click me</button>

<!-- ✓ DO: ARIA when needed -->
<button aria-expanded="false" aria-controls="menu">
  Menu
</button>
<ul id="menu" hidden>...</ul>
```

---

## Common ARIA Patterns

### Live Regions

Announce dynamic content to screen readers:

```html
<!-- Polite: Announced after current speech -->
<div aria-live="polite" aria-atomic="true">
  3 items in cart
</div>

<!-- Assertive: Announced immediately -->
<div aria-live="assertive" role="alert">
  Error: Connection lost
</div>
```

### Expanded/Collapsed

```html
<button aria-expanded="false" aria-controls="details">
  Show details
</button>
<div id="details" hidden>
  <!-- Details content -->
</div>
```

```javascript
button.addEventListener('click', () => {
  const expanded = button.getAttribute('aria-expanded') === 'true';
  button.setAttribute('aria-expanded', !expanded);
  details.hidden = expanded;
});
```

### Tabs

```html
<div class="tabs">
  <div role="tablist" aria-label="Settings tabs">
    <button
      role="tab"
      id="tab-1"
      aria-selected="true"
      aria-controls="panel-1"
    >
      General
    </button>
    <button
      role="tab"
      id="tab-2"
      aria-selected="false"
      aria-controls="panel-2"
      tabindex="-1"
    >
      Security
    </button>
  </div>
  <div
    role="tabpanel"
    id="panel-1"
    aria-labelledby="tab-1"
  >
    <!-- General settings -->
  </div>
  <div
    role="tabpanel"
    id="panel-2"
    aria-labelledby="tab-2"
    hidden
  >
    <!-- Security settings -->
  </div>
</div>
```

### Modal Dialog

```html
<dialog
  role="dialog"
  aria-modal="true"
  aria-labelledby="dialog-title"
  aria-describedby="dialog-desc"
>
  <h2 id="dialog-title">Confirm Delete</h2>
  <p id="dialog-desc">
    Are you sure you want to delete this item? This cannot be undone.
  </p>
  <button>Cancel</button>
  <button>Delete</button>
</dialog>
```

---

## Reduced Motion

Respect user preferences for reduced motion:

```css
/* Default animations */
.animate {
  transition: transform 0.3s ease;
}

/* Reduced motion preference */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

Provide alternatives for motion-based features:

```javascript
const prefersReducedMotion = window.matchMedia(
  '(prefers-reduced-motion: reduce)'
).matches;

if (prefersReducedMotion) {
  // Show static fallback instead of animation
  showStaticVersion();
} else {
  playAnimation();
}
```

---

## Testing

### Automated Testing

Use automated tools for baseline testing:

| Tool       | Purpose                              |
| ---------- | ------------------------------------ |
| axe-core   | Runtime accessibility testing        |
| Lighthouse | Audit tool in Chrome DevTools        |
| WAVE       | Browser extension for visual testing |
| pa11y      | CI/CD integration                    |

**Automated testing catches ~30% of issues.** Manual testing is required.

### Manual Testing

#### Keyboard Testing

1. Unplug your mouse
2. Navigate entire interface with Tab, Shift+Tab, Enter, Space, Escape
3. Verify focus is always visible
4. Verify all functionality is reachable
5. Verify modals trap focus

#### Screen Reader Testing

Test with at least one screen reader:

| Platform | Screen Reader        |
| -------- | -------------------- |
| macOS    | VoiceOver (built-in) |
| Windows  | NVDA (free) or JAWS  |
| iOS      | VoiceOver (built-in) |
| Android  | TalkBack (built-in)  |

**What to test:**

1. All content is announced
2. Headings structure is logical
3. Form labels are associated
4. Images have meaningful alt text
5. Dynamic content is announced
6. Error messages are announced

#### Visual Testing

1. Zoom to 200% - is content still usable?
2. Test with high contrast mode
3. Test with inverted colors
4. Test with grayscale (color blindness simulation)

---

## Checklist

### Before Development

- [ ] Color contrast verified (4.5:1 text, 3:1 UI)
- [ ] Focus states designed
- [ ] Error states designed with clear messages
- [ ] Keyboard interaction patterns defined

### During Development

- [ ] Semantic HTML used
- [ ] ARIA attributes added where needed
- [ ] Focus management implemented
- [ ] Skip links included
- [ ] Form labels associated

### Before Launch

- [ ] Automated testing passes (axe, Lighthouse)
- [ ] Manual keyboard testing complete
- [ ] Screen reader testing complete
- [ ] Zoom testing complete (200%)
- [ ] Reduced motion respected

---

## Resources

### Standards

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [HTML Accessibility](https://developer.mozilla.org/en-US/docs/Learn/Accessibility/HTML)

### Tools

- [axe DevTools](https://www.deque.com/axe/devtools/) - Browser extension
- [WAVE](https://wave.webaim.org/) - Web accessibility evaluation
- [Contrast Checker](https://webaim.org/resources/contrastchecker/) - Color contrast
- [NVDA](https://www.nvaccess.org/) - Free Windows screen reader

---

## See Also

- [Design Systems](./design-systems.md) - Color contrast tokens
- [Components](./components.md) - Accessible component patterns
- [Testing](../process/testing.md) - Testing strategies including a11y
