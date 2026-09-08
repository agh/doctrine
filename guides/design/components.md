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

.form-input:focus-visible {
  outline: var(--focus-ring-width) solid var(--focus-ring-color);
  outline-offset: var(--focus-ring-offset);
  border-color: var(--interactive-default);
  box-shadow: 0 0 0 3px var(--focus-ring-halo);
}

.form-input:disabled {
  background: var(--surface-inset);
  cursor: not-allowed;
}

/* Error state */
.form-input[aria-invalid="true"] {
  border-color: var(--status-error);
}

.form-input[aria-invalid="true"]:focus-visible {
  box-shadow: 0 0 0 3px var(--error-ring-halo);
}
```

### Focus Indicators

Focus styling MUST be valid CSS, not merely intended CSS:

- An outline MUST be declared before any decorative ring, so the indicator
  still exists if the ring is dropped
- Translucent rings MUST use `color-mix()` or a dedicated ring token; alpha
  MUST NOT be appended inside `var()`
- The focus indicator MUST reach 3:1 contrast against both the adjacent
  component colour and the background it sits on

```css
/* ✗ DON'T: invalid var() grammar. The declaration is discarded, so the
   input is left with `outline: none` and no focus indicator at all. */
.form-input:focus {
  outline: none;
  box-shadow: 0 0 0 3px var(--interactive-default / 0.15);
}

/* ✓ DO: a valid translucent ring on top of a self-sufficient outline */
.form-input:focus-visible {
  outline: 2px solid var(--interactive-default);
  outline-offset: 1px;
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--interactive-default) 25%, transparent);
}
```

**Why**: `var()` accepts a custom property name followed only by an optional
comma and fallback, so `var(--interactive-default / 0.15)` is a syntax error
and Chromium reports `CSS.supports()` as `false` for it. The whole declaration
is dropped while the sibling `outline: none` survives, which removes the focus
indicator entirely — and for an invalid input the error border already matches
the focus border, so nothing at all changes on focus.
[`color-mix()`](https://drafts.csswg.org/css-color-5/#color-mix) has been
[Baseline widely available since 9 May 2023](https://api.webstatus.dev/v1/features/color-mix)
and produces the alpha the token cannot carry. A solid 2px outline is also the
simplest way to satisfy the minimum-area part of
[WCAG 2.2 Focus Appearance](https://www.w3.org/WAI/WCAG22/Understanding/focus-appearance.html),
and these tokens clear its 3:1 contrast requirement in both themes:
`#6366f1` on white measures 4.47:1, `#818cf8` on the dark card `#0a0a0a`
measures 6.64:1.

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
<dialog
  class="modal"
  role="dialog"
  aria-modal="true"
  aria-labelledby="modal-title"
>
  <header class="modal-header">
    <h2 id="modal-title" class="modal-title">Modal Title</h2>
    <button class="modal-close" aria-label="Close modal">
      <svg aria-hidden="true"><!-- X icon --></svg>
    </button>
  </header>
  <div class="modal-body">
    <!-- Modal content -->
  </div>
  <footer class="modal-footer">
    <button class="btn btn-ghost">Cancel</button>
    <button class="btn btn-primary">Confirm</button>
  </footer>
</dialog>
```

A modal dialog MUST NOT ship its own backdrop element. `showModal()` renders
the dialog in the top layer with a `::backdrop` pseudo-element, which a
separate `<div>` can only compete with:

```css
.modal::backdrop {
  background: rgb(0 0 0 / 0.5);
}
```

### Modal Requirements

Modals MUST:

1. Use `<dialog>` opened with `showModal()`
2. Keep focus inside the dialog while it is open
3. Return focus to the invoking element on close
4. Close on Escape key
5. Have accessible title (`aria-labelledby`)
6. Prevent background scroll, and restore whatever scroll state the page had

**Why**: `showModal()` puts the dialog in the top layer, marks everything else
in the document
[inert](https://developer.mozilla.org/en-US/docs/Web/API/HTMLDialogElement/showModal),
and handles Escape as a close request. Chromium confirms it: with a modal
dialog open, repeated Tab presses cycle only through the dialog's own controls,
and Escape fires `cancel` then `close`. A hand-written focus trap and keydown
listener therefore add nothing, and both are common sources of the lifecycle
bugs below.

### Focus Management

State that `open()` changes MUST be restored by the `close` event, not by the
`close()` method, because Escape and a `<form method="dialog">` submit close
the dialog without going through it:

```javascript
class Modal {
  constructor(dialog, { fallbackFocus = null } = {}) {
    this.dialog = dialog;
    this.fallbackFocus = fallbackFocus;
    this.invoker = null;
    this.previousOverflow = null;

    // Bound once. Reopening MUST NOT accumulate listeners, and every close
    // path — Escape, close(), method="dialog" — ends in this event.
    this.dialog.addEventListener('close', () => this.restore());
  }

  open(invoker = document.activeElement) {
    if (this.dialog.open) return;
    this.invoker = invoker;
    // `close` is dispatched asynchronously, so a reopen in the same task can
    // land before the previous restore. Only the first lock records state.
    if (this.previousOverflow === null) {
      this.previousOverflow = document.body.style.overflow;
    }
    document.body.style.overflow = 'hidden';
    this.dialog.showModal();
    this.initialFocus().focus();
  }

  close(returnValue) {
    this.dialog.close(returnValue);
  }

  restore() {
    if (this.dialog.open) return; // reopened before this close was delivered

    // Put back the page's own value, which may not have been the default.
    document.body.style.overflow = this.previousOverflow ?? '';
    this.previousOverflow = null;

    // The invoker may have been removed by the action the dialog performed.
    const target = this.invoker?.isConnected ? this.invoker : this.fallbackFocus;
    this.invoker = null;
    target?.focus();
  }

  initialFocus() {
    return (
      this.dialog.querySelector('[autofocus]') ??
      this.dialog.querySelector('.modal-body :is(a[href], button, input, select, textarea)') ??
      this.dialog
    );
  }
}
```

Confirming a destructive action before it happens belongs in `cancel`, which
is cancellable, rather than in a keydown handler:

```javascript
dialog.addEventListener('cancel', (event) => {
  if (form.hasUnsavedChanges) event.preventDefault();
});
```

The `fallbackFocus` element MUST itself be focusable — usually the heading of
the region the dialog acted on, given `tabindex="-1"` — or focus silently
falls back to `<body>`.

**Why**: each of these rules fixes a failure that headless Chromium reproduces
in the naive version. Adding the keydown listener inside `open()` leaves two
listeners after a second open, so one Escape runs `close()` twice. Setting
`document.body.style.overflow = ''` on close discards a page that was already
`clip`. Cleaning up in `close()` rather than on the `close` event leaves the
body stuck at `hidden` when the dialog closes natively. Initial focus follows
the [APG dialog pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/):
an explicit `autofocus` target, otherwise the first control in the body,
otherwise the dialog itself, which `showModal()` makes focusable without a
`tabindex`.

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
- Sortable columns MUST expose sort state with `aria-sort` on the `<th>`, never
  on the button inside it
- No more than one header per table MUST carry `aria-sort` at a time
- Action columns MUST have accessible labels
- Responsive tables SHOULD scroll horizontally on small screens

### Sortable Columns

The sort button is the control; the header cell holds the state:

```html
<thead>
  <!-- ✓ DO: aria-sort on the sorted column header -->
  <tr>
    <th scope="col" aria-sort="ascending">
      <button type="button" class="table-sort">
        Hostname
        <span aria-hidden="true" class="sort-icon">▲</span>
      </button>
    </th>
    <th scope="col">
      <button type="button" class="table-sort">
        Type
        <span aria-hidden="true" class="sort-icon"></span>
      </button>
    </th>
    <th scope="col">Address</th>
  </tr>
</thead>
```

```html
<!-- ✗ DON'T: aria-sort is not defined for the button role, so the header's
     sort state is never exposed -->
<th scope="col">
  <button class="table-sort" aria-sort="ascending">Hostname</button>
</th>
```

Sorting moves the attribute rather than adding a second one:

```javascript
function setSortState(header, direction) {
  for (const th of header.closest('tr').querySelectorAll('th[aria-sort]')) {
    if (th === header) continue;
    th.removeAttribute('aria-sort');
    th.querySelector('.sort-icon').textContent = '';
  }
  header.setAttribute('aria-sort', direction);
  header.querySelector('.sort-icon').textContent =
    direction === 'ascending' ? '▲' : '▼';
}

function initSortableTable(table, sortRows) {
  for (const button of table.querySelectorAll('th .table-sort')) {
    button.addEventListener('click', () => {
      const header = button.closest('th');
      // An unsorted column starts ascending; the sorted column toggles.
      const direction =
        header.getAttribute('aria-sort') === 'ascending' ? 'descending' : 'ascending';
      sortRows(header.cellIndex, direction);
      setSortState(header, direction);
    });
  }
}
```

The sort buttons' purpose SHOULD be described once in the caption rather than
repeated in every button label:

```html
<caption>
  Device inventory
  <span class="sr-only">Column headers with buttons sort the table.</span>
</caption>
```

**Why**: `aria-sort` is defined only for the `columnheader` and `rowheader`
roles, which a nested `<button>` does not have, so on the button it says
nothing about the column. [MDN's `aria-sort`
reference](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Attributes/aria-sort)
and the [APG sortable-table
example](https://www.w3.org/WAI/ARIA/apg/patterns/table/examples/sortable-table/)
both set the attribute on the currently sorted header, keep it on exactly one
header at a time, and move it when another column is sorted. MDN also puts the
sorting instructions in the caption rather than repeating them in every column
label.

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
