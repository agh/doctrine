# Motion and Interaction

> [Doctrine](../../README.md) > [Design](./README.md) > Motion

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

---

## Overview

Motion is communication. Every animation MUST answer "what just happened?" or
"what will happen?" Animation without purpose is visual noise.

## Quick Reference

| Duration | Use Case                          | Token               |
| -------- | --------------------------------- | ------------------- |
| 150ms    | Micro-interactions (hover, focus) | `--duration-fast`   |
| 250ms    | Standard transitions              | `--duration-normal` |
| 400ms    | Complex animations                | `--duration-slow`   |
| 600ms    | Page transitions                  | `--duration-slower` |

---

## Motion Principles

### 1. Purpose Over Decoration

Every animation MUST serve a purpose:

- **Feedback**: Confirm an action occurred
- **Orientation**: Show where something came from or went
- **Guidance**: Direct attention to important changes
- **Continuity**: Maintain spatial relationships

```css
/* ✓ DO: Animation provides feedback */
.button:active {
  transform: scale(0.98);  /* Confirms click */
}

/* ✗ DON'T: Animation is decorative */
.logo {
  animation: bounce 2s infinite;  /* No purpose */
}
```

### 2. Swift Over Slow

Users perceive animations >400ms as slow. Keep motion fast:

| Perception | Duration  | Use For               |
| ---------- | --------- | --------------------- |
| Instant    | <100ms    | Cursor feedback       |
| Fast       | 100-200ms | Hovers, toggles       |
| Moderate   | 200-400ms | Reveals, transitions  |
| Slow       | >400ms    | Special emphasis only |

### 3. Natural Over Mechanical

Use easing curves that mimic physical motion:

```css
:root {
  /* Avoid linear - feels robotic */
  --ease-linear: linear;

  /* Standard easing */
  --ease-in: cubic-bezier(0.4, 0, 1, 1);
  --ease-out: cubic-bezier(0, 0, 0.2, 1);
  --ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);

  /* Spring easing - natural bounce */
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);

  /* Emphasis - dramatic entrance */
  --ease-emphasis: cubic-bezier(0.2, 0, 0, 1);
}
```

**When to use each:**

| Easing        | Use Case                               |
| ------------- | -------------------------------------- |
| `ease-out`    | Elements entering (appear, expand)     |
| `ease-in`     | Elements exiting (disappear, collapse) |
| `ease-in-out` | Elements changing state                |
| `ease-spring` | Playful interactions, bouncy feedback  |

### 4. Respect Over Imposition

Always respect user preferences:

```css
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

---

## Motion Tokens

### Duration Tokens

```css
:root {
  --duration-instant: 50ms;   /* Immediate feedback */
  --duration-fast:    150ms;  /* Micro-interactions */
  --duration-normal:  250ms;  /* Standard transitions */
  --duration-slow:    400ms;  /* Complex animations */
  --duration-slower:  600ms;  /* Page transitions */
}
```

### Easing Tokens

```css
:root {
  --ease-out:       cubic-bezier(0, 0, 0.2, 1);
  --ease-in:        cubic-bezier(0.4, 0, 1, 1);
  --ease-in-out:    cubic-bezier(0.4, 0, 0.2, 1);
  --ease-spring:    cubic-bezier(0.34, 1.56, 0.64, 1);
  --ease-bounce:    cubic-bezier(0.34, 1.8, 0.64, 1);
  --ease-emphasis:  cubic-bezier(0.2, 0, 0, 1);
}
```

---

## Common Animation Patterns

### Fade

```css
@keyframes fade-in {
  from { opacity: 0; }
  to   { opacity: 1; }
}

@keyframes fade-out {
  from { opacity: 1; }
  to   { opacity: 0; }
}

.fade-in {
  animation: fade-in var(--duration-normal) var(--ease-out);
}
```

### Scale

```css
@keyframes scale-in {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.scale-in {
  animation: scale-in var(--duration-normal) var(--ease-spring);
}
```

### Slide

```css
@keyframes slide-in-up {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slide-in-down {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.slide-in-up {
  animation: slide-in-up var(--duration-normal) var(--ease-out);
}
```

### Stagger

Animate list items sequentially:

```css
.stagger-item {
  animation: fade-in var(--duration-normal) var(--ease-out) backwards;
}

.stagger-item:nth-child(1) { animation-delay: 0ms; }
.stagger-item:nth-child(2) { animation-delay: 50ms; }
.stagger-item:nth-child(3) { animation-delay: 100ms; }
.stagger-item:nth-child(4) { animation-delay: 150ms; }
.stagger-item:nth-child(5) { animation-delay: 200ms; }
```

### Loading Spinner

```css
@keyframes spin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}

.spinner {
  animation: spin 0.6s linear infinite;
}
```

### Skeleton Shimmer

```css
@keyframes shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.skeleton {
  background: linear-gradient(
    90deg,
    var(--surface-inset) 25%,
    var(--surface-elevated) 50%,
    var(--surface-inset) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
```

### Pulse (Status Indicator)

```css
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50%      { opacity: 0.5; }
}

.status-active {
  animation: pulse 2s ease-in-out infinite;
}
```

---

## Interaction Feedback

### Hover States

```css
.card {
  transition:
    transform var(--duration-fast) var(--ease-spring),
    box-shadow var(--duration-fast) var(--ease-out);
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}
```

### Click/Active States

```css
.button {
  transition: transform var(--duration-fast) var(--ease-spring);
}

.button:active {
  transform: scale(0.98);
}
```

### Focus States

Focus transitions SHOULD be instant or very fast:

```css
.input {
  transition: box-shadow var(--duration-fast) var(--ease-out);
}

.input:focus {
  box-shadow: 0 0 0 3px var(--interactive-default / 0.2);
}
```

### Success Feedback

```css
@keyframes success-check {
  0%   { transform: scale(0); opacity: 0; }
  50%  { transform: scale(1.2); }
  100% { transform: scale(1); opacity: 1; }
}

.success-icon {
  animation: success-check var(--duration-slow) var(--ease-spring);
}
```

### Error Feedback

```css
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25%      { transform: translateX(-4px); }
  75%      { transform: translateX(4px); }
}

.error-shake {
  animation: shake var(--duration-normal) var(--ease-out);
}
```

---

## Page Transitions

### Enter Transition

```css
.page-enter {
  animation: fade-in var(--duration-normal) var(--ease-out);
}
```

### Exit Transition

```css
.page-exit {
  animation: fade-out var(--duration-fast) var(--ease-in);
}
```

### Shared Element Transitions

For connected animations between pages, use the View Transitions API:

```javascript
// Simple view transition
document.startViewTransition(() => {
  updateDOM();
});
```

```css
/* Define transition behavior */
::view-transition-old(root) {
  animation: fade-out var(--duration-fast) var(--ease-in);
}

::view-transition-new(root) {
  animation: fade-in var(--duration-normal) var(--ease-out);
}
```

---

## Performance

### GPU Acceleration

Only animate properties that trigger GPU acceleration:

| GPU Accelerated (Good) | Causes Layout/Paint (Avoid) |
| ---------------------- | --------------------------- |
| `transform`            | `width`, `height`           |
| `opacity`              | `margin`, `padding`         |
| `filter`               | `top`, `left`               |

```css
/* ✓ DO: GPU-accelerated */
.slide {
  transform: translateX(100%);
}

/* ✗ DON'T: Triggers layout */
.slide {
  left: 100%;
}
```

### Will-Change

Use sparingly for complex animations:

```css
.complex-animation {
  will-change: transform, opacity;
}

/* Remove after animation completes */
.complex-animation.done {
  will-change: auto;
}
```

### Contain

Isolate animated elements:

```css
.animated-container {
  contain: layout paint;
}
```

### Animation Playback Control

Pause animations when not visible:

```javascript
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    const animation = entry.target.getAnimations()[0];
    if (animation) {
      entry.isIntersecting ? animation.play() : animation.pause();
    }
  });
});

document.querySelectorAll('.animated').forEach(el => observer.observe(el));
```

---

## Testing Motion

### Reduced Motion Testing

1. Enable reduced motion in OS settings
2. Verify animations are disabled or minimal
3. Verify all functionality works without animation

**macOS**: System Preferences → Accessibility → Display → Reduce Motion

**Windows**: Settings → Ease of Access → Display → Show animations

### Performance Testing

1. Open DevTools → Performance
2. Enable "CPU throttling" to simulate slower devices
3. Record animation performance
4. Look for dropped frames (should maintain 60fps)

### Motion Sickness Testing

Have team members with motion sensitivity test:

- Large movements
- Parallax effects
- Continuous animations
- Screen transitions

---

## Anti-Patterns

### Animation for Animation's Sake

```css
/* ✗ DON'T: Decorative animation */
.logo {
  animation: bounce 2s infinite;
}
```

### Too Slow

```css
/* ✗ DON'T: Feels sluggish */
.modal {
  transition: opacity 800ms ease;
}

/* ✓ DO: Snappy */
.modal {
  transition: opacity 200ms ease-out;
}
```

### Linear Easing

```css
/* ✗ DON'T: Robotic */
.card {
  transition: transform 200ms linear;
}

/* ✓ DO: Natural */
.card {
  transition: transform 200ms ease-out;
}
```

### Animating Layout Properties

```css
/* ✗ DON'T: Triggers layout recalculation */
.expand {
  transition: height 300ms ease;
}

/* ✓ DO: Use transform */
.expand {
  transition: transform 300ms ease;
  transform-origin: top;
}
.expand.collapsed {
  transform: scaleY(0);
}
```

### Blocking Interactions

```css
/* ✗ DON'T: Animation blocks interaction */
.button {
  pointer-events: none;
  animation: entrance 2s ease;
}

/* ✓ DO: Keep interactive */
.button {
  animation: entrance 300ms ease;
}
```

---

## Checklist

- [ ] All animations serve a purpose (feedback, orientation, guidance)
- [ ] Durations are appropriate (<400ms for most interactions)
- [ ] Easing feels natural (not linear)
- [ ] `prefers-reduced-motion` is respected
- [ ] Only transform/opacity animated for performance
- [ ] Animations tested at 60fps
- [ ] Complex animations use `will-change` (removed after)
- [ ] No animation blocks interactivity

---

## See Also

- [Design Systems](./design-systems.md) - Motion tokens
- [Components](./components.md) - Component animation patterns
- [Accessibility](./accessibility.md) - Reduced motion support
- [CSS](../languages/css.md) - CSS animation syntax
