# Component Patterns

> [Doctrine](../../README.md) > [Design](./README.md) > Components

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

---

## Overview

Components are reusable building blocks that combine design tokens with
behavior. Well-designed components are consistent, accessible, and composable.

## Quick Reference

| Component Type | Purpose                | Examples                 |
| -------------- | ---------------------- | ------------------------ |
| Primitives     | Atomic building blocks | Button, Input, Badge     |
| Composites     | Combined primitives   | Card, Modal, Dropdown    |
| Patterns       | Recurring solutions   | Form layout, Data table  |
| Templates      | Page-level structures | Dashboard, Settings page |

---

## Component Architecture

### Composition Hierarchy

Components MUST be organized in increasing complexity:

```text
Templates     <- Page layouts combining patterns
    |
Patterns      <- Solutions to common problems
    |
Composites    <- Combinations of primitives
    |
Primitives    <- Atomic, single-purpose components
    |
Tokens        <- Design values (color, space, type)
```

### Primitive Requirements

Every primitive component MUST:

1. Be single-purpose (do one thing well)
2. Use design tokens exclusively
3. Support all interaction states
4. Be keyboard accessible
5. Include ARIA attributes where needed
6. Work in isolation (no external dependencies)

---

## Buttons

### Button Variants

Every project MUST define these button variants:

| Variant   | Usage                          | Visual Treatment                |
| --------- | ------------------------------ | ------------------------------- |
| Primary   | Main action, one per view      | Solid background, high contrast |
| Secondary | Supporting actions             | Border or subtle background     |
| Ghost     | Tertiary actions, tight spaces | Text only, background on hover  |
| Danger    | Destructive actions            | Red/error color scheme          |

### Button Sizes

```css
.btn {
  /* Base styles */
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  font-weight: var(--font-medium);
  border-radius: var(--radius-lg);
  transition: all var(--duration-fast) var(--ease-out);
}

.btn-sm {
  padding: var(--space-1) var(--space-2);
  font-size: var(--text-xs);
}

.btn-md {
  padding: var(--space-2) var(--space-4);
  font-size: var(--text-sm);
}

.btn-lg {
  padding: var(--space-3) var(--space-6);
  font-size: var(--text-base);
}
```

### Button States

Every button MUST define these states:

```css
.btn {
  /* Default state */
  background: var(--interactive-default);
  color: white;
}

.btn:hover {
  background: var(--interactive-hover);
  transform: translateY(-1px);
}

.btn:active {
  background: var(--interactive-active);
  transform: translateY(0);
}

.btn:focus-visible {
  outline: 2px solid var(--interactive-default);
  outline-offset: 2px;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}
```

### Button Loading State

Buttons performing async actions MUST show loading state:

```html
<button class="btn btn-primary" disabled aria-busy="true">
  <span class="spinner" aria-hidden="true"></span>
  <span>Saving...</span>
</button>
```

### Button Accessibility

- Buttons MUST have accessible labels (visible text or `aria-label`)
- Icon-only buttons MUST have `aria-label`
- Loading buttons MUST have `aria-busy="true"`
- Disabled buttons SHOULD use `aria-disabled` for screen reader visibility

---

## Form Inputs

### Input Structure

```html
<div class="form-field">
  <label for="email" class="form-label">
    Email address
    <span class="required" aria-hidden="true">*</span>
  </label>
  <input
    type="email"
    id="email"
    name="email"
    class="form-input"
    required
    aria-describedby="email-hint email-error"
  />
  <p id="email-hint" class="form-hint">We'll never share your email.</p>
  <p id="email-error" class="form-error" role="alert" hidden>
    Please enter a valid email address.
  </p>
</div>
```

### Input States

```css
.form-input {
  /* Default */
  width: 100%;
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  background: var(--surface-card);
  color: var(--text-primary);
}

.form-input::placeholder {
  color: var(--text-muted);
}

.form-input:hover {
  border-color: var(--border-emphasis);
}

.form-input:focus {
  outline: none;
  border-color: var(--interactive-default);
  box-shadow: 0 0 0 3px var(--interactive-default / 0.15);
}

.form-input:disabled {
  background: var(--surface-inset);
  cursor: not-allowed;
}

/* Error state */
.form-input[aria-invalid="true"] {
  border-color: var(--status-error);
}

.form-input[aria-invalid="true"]:focus {
  box-shadow: 0 0 0 3px var(--status-error / 0.15);
}
```

### Form Validation

- Validation errors MUST be associated via `aria-describedby`
- Error messages MUST have `role="alert"` for screen reader announcement
- Invalid inputs MUST have `aria-invalid="true"`
- Error messages MUST explain how to fix the problem

```css
.form-error {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  margin-top: var(--space-1);
  font-size: var(--text-xs);
  color: var(--status-error);
}
```

---

## Cards

### Card Structure

```html
<article class="card">
  <header class="card-header">
    <h3 class="card-title">Card Title</h3>
    <p class="card-subtitle">Optional subtitle</p>
  </header>
  <div class="card-body">
    <!-- Card content -->
  </div>
  <footer class="card-footer">
    <!-- Actions -->
  </footer>
</article>
```

### Card Variants

| Variant     | Usage                            |
| ----------- | -------------------------------- |
| Default     | Standard content container       |
| Interactive | Clickable cards (link/button)    |
| Elevated    | Floating UI, important content   |
| Bordered    | Subtle separation without shadow |

### Interactive Cards

Clickable cards MUST:

1. Have visible focus state
2. Support keyboard activation (Enter/Space)
3. Indicate interactivity on hover

```css
.card-interactive {
  cursor: pointer;
  transition: transform var(--duration-fast) var(--ease-spring),
              box-shadow var(--duration-fast) var(--ease-out);
}

.card-interactive:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.card-interactive:focus-visible {
  outline: 2px solid var(--interactive-default);
  outline-offset: 2px;
}
```

---

## Modals and Dialogs

### Modal Structure

```html
<div class="modal-backdrop" aria-hidden="true"></div>

<dialog
  class="modal"
  role="dialog"
  aria-modal="true"
  aria-labelledby="modal-title"
  aria-describedby="modal-desc"
>
  <header class="modal-header">
    <h2 id="modal-title" class="modal-title">Modal Title</h2>
    <button class="modal-close" aria-label="Close modal">
      <svg aria-hidden="true"><!-- X icon --></svg>
    </button>
  </header>
  <div id="modal-desc" class="modal-body">
    <!-- Modal content -->
  </div>
  <footer class="modal-footer">
    <button class="btn btn-ghost">Cancel</button>
    <button class="btn btn-primary">Confirm</button>
  </footer>
</dialog>
```

### Modal Requirements

Modals MUST:

1. Trap focus within the modal
2. Return focus to trigger element on close
3. Close on Escape key
4. Have accessible title (`aria-labelledby`)
5. Prevent background scroll
6. Use `<dialog>` element when possible

### Focus Management

```javascript
class Modal {
  open(triggerElement) {
    this.triggerElement = triggerElement;
    this.element.showModal();
    this.trapFocus();
    document.body.style.overflow = 'hidden';
  }

  close() {
    this.element.close();
    document.body.style.overflow = '';
    this.triggerElement?.focus();
  }

  trapFocus() {
    const focusable = this.element.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const first = focusable[0];
    const last = focusable[focusable.length - 1];

    this.element.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        this.close();
      }
      if (e.key === 'Tab') {
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    });

    first?.focus();
  }
}
```

---

## Tables

### Data Table Structure

```html
<div class="table-container" role="region" aria-label="Device inventory">
  <table class="table">
    <caption class="sr-only">List of all devices</caption>
    <thead>
      <tr>
        <th scope="col">Status</th>
        <th scope="col">Hostname</th>
        <th scope="col">Type</th>
        <th scope="col">
          <span class="sr-only">Actions</span>
        </th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Active</td>
        <td>blueridge</td>
        <td>Bare Metal</td>
        <td>
          <button aria-label="Actions for blueridge">⋮</button>
        </td>
      </tr>
    </tbody>
  </table>
</div>
```

### Table Requirements

- Tables MUST have `<caption>` (visible or `sr-only`)
- Header cells MUST use `<th>` with `scope="col"` or `scope="row"`
- Sortable columns MUST indicate current sort state (`aria-sort`)
- Action columns MUST have accessible labels
- Responsive tables SHOULD scroll horizontally on small screens

### Sortable Columns

```html
<th scope="col">
  <button
    class="table-sort"
    aria-sort="ascending"
    aria-label="Sort by hostname, currently ascending"
  >
    Hostname
    <svg aria-hidden="true" class="sort-icon"><!-- sort icon --></svg>
  </button>
</th>
```

---

## Toasts and Notifications

### Toast Structure

```html
<div class="toast-container" aria-live="polite" aria-atomic="true">
  <div class="toast toast-success" role="status">
    <svg class="toast-icon" aria-hidden="true"><!-- check --></svg>
    <p class="toast-message">Settings saved successfully</p>
    <button class="toast-close" aria-label="Dismiss">
      <svg aria-hidden="true"><!-- X --></svg>
    </button>
  </div>
</div>
```

### Toast Variants

| Variant | Usage               | Role            |
| ------- | ------------------- | --------------- |
| Success | Completed actions   | `role="status"` |
| Error   | Failed actions      | `role="alert"`  |
| Warning | Potential issues    | `role="status"` |
| Info    | Neutral information | `role="status"` |

### Toast Requirements

- Error toasts MUST use `role="alert"` for immediate announcement
- Non-error toasts SHOULD use `role="status"`
- Toasts MUST be dismissible
- Toasts SHOULD auto-dismiss after 5-10 seconds (except errors)
- Toast container MUST have `aria-live="polite"`

---

## Empty States

### Empty State Structure

```html
<div class="empty-state">
  <div class="empty-illustration">
    <svg aria-hidden="true"><!-- illustration --></svg>
  </div>
  <h3 class="empty-title">No devices found</h3>
  <p class="empty-description">
    Try adjusting your filters or add a new device.
  </p>
  <div class="empty-actions">
    <button class="btn btn-ghost">Clear filters</button>
    <button class="btn btn-primary">Add device</button>
  </div>
</div>
```

### Empty State Requirements

Every empty state MUST include:

1. Clear explanation of why it's empty
2. Guidance on what to do next
3. Action buttons when applicable

Empty states SHOULD NOT:

- Use technical jargon
- Blame the user
- Leave users without next steps

---

## Loading States

### Skeleton Screens

Use skeleton screens for content-heavy loading:

```html
<div class="skeleton-card">
  <div class="skeleton skeleton-avatar"></div>
  <div class="skeleton skeleton-line" style="width: 60%"></div>
  <div class="skeleton skeleton-line" style="width: 80%"></div>
  <div class="skeleton skeleton-line" style="width: 40%"></div>
</div>
```

```css
.skeleton {
  background: linear-gradient(
    90deg,
    var(--surface-inset) 25%,
    var(--surface-elevated) 50%,
    var(--surface-inset) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: var(--radius-sm);
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
```

### Spinners

Use spinners for action-based loading:

```html
<span class="spinner" aria-label="Loading"></span>
```

```css
.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid var(--border-default);
  border-top-color: var(--interactive-default);
  border-radius: var(--radius-full);
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
```

### Loading Requirements

- Long operations (>1s) MUST show loading indicator
- Loading states MUST be announced to screen readers
- Loading MUST NOT block critical UI
- Progress bars SHOULD show determinate progress when known

---

## Component Documentation

### Documentation Requirements

Every component MUST be documented with:

1. **Purpose**: What the component does
2. **Variants**: All visual variations
3. **States**: All interaction states
4. **Props/API**: Configuration options
5. **Accessibility**: ARIA requirements and keyboard behavior
6. **Examples**: Code snippets for common uses
7. **Do's and Don'ts**: Usage guidelines

### Documentation Template

```markdown
# Component Name

Brief description of what this component does.

## Usage

When to use this component.

## Variants

| Variant | Description |
|---------|-------------|
| Primary | Main usage |
| Secondary | Alternative usage |

## States

- Default
- Hover
- Active
- Focus
- Disabled
- Loading
- Error

## API

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| variant | string | 'primary' | Visual variant |
| disabled | boolean | false | Disabled state |

## Accessibility

- Keyboard behavior
- ARIA requirements
- Screen reader notes

## Examples

[Code examples]

## Do's and Don'ts

✓ Do: [Good practice]
✗ Don't: [Anti-pattern]
```

---

## See Also

- [Design Systems](./design-systems.md) - Design tokens
- [Accessibility](./accessibility.md) - Accessibility standards
- [Motion](./motion.md) - Animation patterns
- [React](../frameworks/react.md) - React component patterns
