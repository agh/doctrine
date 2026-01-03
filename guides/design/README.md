# Design Guide

> [Doctrine](../../README.md) > Design

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

---

## Overview

This guide establishes design principles and standards for building interfaces
that are consistent, accessible, performant, and delightful. Design is not
decoration—it is communication, confidence-building, and craft.

## Guides in This Section

| Guide                                 | Description                                      |
| ------------------------------------- | ------------------------------------------------ |
| [Design Systems](./design-systems.md) | Tokens, theming, and systematic consistency      |
| [Components](./components.md)         | Reusable component patterns and architecture     |
| [Accessibility](./accessibility.md)   | WCAG compliance and inclusive design             |
| [Motion](./motion.md)                 | Animation, transitions, and interaction feedback |

---

## Design Principles

Every design decision MUST be guided by these principles, in priority order:

### 1. Clarity Over Decoration

Every visual element MUST serve a purpose. If an element does not aid
comprehension, guide action, or provide feedback, remove it.

**Why**: Visual noise increases cognitive load. Users should understand
interfaces instantly, not decode them.

```text
✓ DO: Use color to indicate status (green = healthy)
✗ DON'T: Use color for aesthetic variation without meaning
```

### 2. Consistency Over Novelty

Interfaces MUST use a shared design language. Novel solutions SHOULD only be
introduced when existing patterns fail to serve the use case.

**Why**: Consistency builds trust. Users learn patterns once and apply them
everywhere. Novelty forces relearning.

```text
✓ DO: Use the same button style across all pages
✗ DON'T: Create unique button designs per feature
```

### 3. Accessibility Over Convenience

Accessibility MUST NOT be deferred or treated as optional. All interfaces MUST
meet WCAG 2.1 AA standards at minimum.

**Why**: Accessible design benefits everyone. Keyboard navigation helps power
users. High contrast helps users in bright environments. Captions help users
in noisy environments.

```text
✓ DO: Design keyboard navigation from the start
✗ DON'T: Add accessibility "later" or "if time permits"
```

### 4. Performance Over Polish

A fast interface with simple visuals MUST be preferred over a slow interface
with elaborate visuals. Performance budgets MUST be established and enforced.

**Why**: Speed is a feature. A beautiful interface that takes 5 seconds to
load feels broken. A simple interface that loads instantly feels professional.

```text
✓ DO: Set a 100KB JavaScript budget and optimize to meet it
✗ DON'T: Add animations that block interactivity
```

### 5. Feedback Over Silence

Every user action MUST produce visible feedback. Users MUST never wonder
"did that work?"

**Why**: Feedback builds confidence. Silence creates anxiety. Even a subtle
animation confirming a click reduces user stress.

```text
✓ DO: Show loading states, success confirmations, error messages
✗ DON'T: Perform actions silently without acknowledgment
```

### 6. Progressive Disclosure Over Overwhelm

Interfaces MUST show essential information by default and reveal complexity
on demand. Users SHOULD NOT face all options simultaneously.

**Why**: Simplicity at first glance welcomes new users. Depth on demand
serves power users. Both can coexist.

```text
✓ DO: Show primary actions prominently, secondary in menus
✗ DON'T: Display every possible action in the main interface
```

---

## The Design Process

### Design-Development Workflow

Design and development MUST be collaborative, not sequential:

1. **Define tokens first**: Colors, typography, spacing MUST be established
   before components are built
2. **Build primitives together**: Designers and developers MUST agree on
   component APIs before implementation
3. **Document as you build**: Component documentation MUST be created
   alongside implementation, not after
4. **Test with real content**: Designs MUST be validated with realistic
   data, not lorem ipsum

### Design Review Checklist

Every interface MUST pass this checklist before shipping:

- [ ] Uses design tokens exclusively (no hardcoded values)
- [ ] Works in light and dark modes
- [ ] Meets WCAG 2.1 AA contrast requirements
- [ ] Fully keyboard navigable
- [ ] Tested with screen reader
- [ ] Responsive at all breakpoints (mobile, tablet, desktop)
- [ ] Loading states defined for async operations
- [ ] Error states defined and helpful
- [ ] Empty states designed and useful
- [ ] Animations respect `prefers-reduced-motion`

---

## Quick Reference

### Essential Tools

| Purpose               | Tool                        | Notes                                     |
| --------------------- | --------------------------- | ----------------------------------------- |
| Design tokens         | CSS Custom Properties       | See [Design Systems](./design-systems.md) |
| Icons                 | Lucide, Heroicons, Phosphor | Consistent stroke width required          |
| Typography            | Inter, system fonts         | See [Design Systems](./design-systems.md) |
| Color                 | OKLCH color space           | Perceptually uniform                      |
| Accessibility testing | axe, WAVE, Lighthouse       | Automated + manual testing required       |

### File Structure

```text
static/css/
├── tokens/
│   ├── colors.css         # Color primitives and semantic tokens
│   ├── typography.css     # Font families, scales, weights
│   ├── spacing.css        # Spacing scale
│   ├── motion.css         # Duration and easing tokens
│   └── index.css          # Token entry point
├── primitives/
│   ├── button.css         # Button component
│   ├── input.css          # Input component
│   ├── card.css           # Card component
│   └── index.css          # Primitive entry point
└── app.css                # Application styles
```

---

## Measuring Design Quality

### Quantitative Metrics

| Metric                   | Target | Tool            |
| ------------------------ | ------ | --------------- |
| Lighthouse Accessibility | >95    | Chrome DevTools |
| Lighthouse Performance   | >90    | Chrome DevTools |
| First Contentful Paint   | <1.5s  | WebPageTest     |
| Cumulative Layout Shift  | <0.1   | Chrome DevTools |
| WCAG violations          | 0      | axe-core        |

### Qualitative Signals

Good design manifests in user behavior:

- Users accomplish tasks without documentation
- Support requests decrease after redesigns
- Users describe the interface as "fast" or "easy"
- Error rates decrease
- Time-to-completion decreases

---

## Anti-Patterns

### Design Debt

Design debt accumulates when:

- One-off styles bypass the design system
- "Temporary" solutions become permanent
- Accessibility is deferred
- Performance budgets are ignored

Design debt MUST be tracked and paid down regularly, just like technical debt.

### Cargo Cult Design

Copying visual patterns without understanding their purpose leads to:

- Animations that add latency without adding meaning
- Dark mode that inverts colors without considering contrast
- Mobile layouts that shrink desktop rather than reimagining for touch

Every design decision MUST be justified by user needs, not trends.

### Pixel Perfection Paralysis

Obsessing over exact pixel measurements while ignoring:

- How the design behaves at different viewport sizes
- How the design works without images loaded
- How the design reads to screen readers
- How the design performs on slow connections

Responsive, accessible, performant design MUST take priority over static
perfection.

---

## See Also

- [CSS](../languages/css.md) - CSS language standards
- [Tailwind](../frameworks/tailwind.md) - Tailwind CSS framework guide
- [React](../frameworks/react.md) - React component patterns
- [Testing](../process/testing.md) - Testing standards including visual testing
