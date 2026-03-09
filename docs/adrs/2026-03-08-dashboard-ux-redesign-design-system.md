# ADR: Dashboard UX Redesign — Design System & Interaction Standards

**Date:** 2026-03-08
**Status:** Accepted
**Context:** homelab-ai dashboard (`dashboard/`) — React/TypeScript frontend

---

## Decision

Establish a Linear/Vercel-inspired dark command-center aesthetic as the canonical design language for the homelab-ai dashboard, replacing the ad-hoc "retro" system with intentional, documented conventions for visual style, animation, typography, navigation, and interactivity.

---

## Context

The dashboard had accumulated a set of components named "retro" that were actually a generic dark Tailwind UI — not pixel-art, not intentionally designed. Specific problems:

- Navigation used emoji icons (`💬`, `🤖`, `📋`) — visually inconsistent, non-scalable, platform-dependent rendering
- Badges were pill-shaped (`border-radius: 9999px`) with 10px font and no tracking — indistinguishable from generic AI-generated UIs
- Card/panel/kanban headers had inconsistent typography (`font-weight: 700`, no uppercase/tracking)
- Hover animations applied transform lift to all cards, including non-interactive ones
- Button active state used `translateY(1px)` (wrong direction — pushes away from user instead of pressing in)
- No `prefers-reduced-motion` coverage
- Transition easing defaulted to CSS `ease` everywhere — no intentional curve selection
- Skeleton loaders used flat opacity pulse instead of directional shimmer
- No documented design context for future sessions — every agent started from scratch

The single user (Josh) described the desired feel as: **command center, command center, command center** — dense, technical, controlled. Linear/Vercel dark as the visual reference. No emojis, no generic SaaS patterns, no decorative animation.

---

## Options Considered

### Option A: Generic SaaS (status quo)
Keep the existing patterns — pill badges, emoji nav, unstyled headers, CSS `ease` everywhere.

- **Pro:** No migration cost
- **Con:** Looks like every AI-generated Tailwind dashboard; violates the "command center" intent; makes the tool feel less authoritative than it is

### Option B: Pixel-art "retro" (lean into the name)
Commit to the retro aesthetic — pixel fonts, dithering, 8-bit icons.

- **Pro:** Distinctive; consistent with the AoE2 Command page
- **Con:** Actively requested against; hard to read data in pixel fonts; would fight the serious data (LLM metrics, agent logs, task queues)

### Option C: Linear/Vercel dark (chosen)
Minimal dark UI, 1px borders, no decorative noise, Berkeley Mono for data, tight typography hierarchy, intentional easing curves.

- **Pro:** Matches stated intent; scales well with dense data; feels like a precision tool; consistent with how Josh actually uses it (glance-and-check, not sit-and-browse)
- **Con:** Requires systematic refactor of existing components; "retro" naming is now a misnomer (acceptable — it's a codename, not a descriptor)

---

## Decisions Made

### 1. Visual Aesthetic — Linear/Vercel Dark

The dashboard targets a Linear/Vercel dark aesthetic:
- Background: `#0f172a`, surfaces: `#1e293b`, borders: `#334155` (existing tokens unchanged)
- Single blue accent (`#60a5fa`) for interactive elements
- Semantic colors (green/amber/red) reserved exclusively for status and priority — never decorative
- No gradients, no glow effects, no decorative shadows
- Dark mode only — no light variant planned

Reference doc: `homelab-ai/CLAUDE.md` (Design Context section).

### 2. Navigation — SVG Icons + Left-Border Active Indicator

**Emojis removed.** Navigation icons are minimal 15×15 SVG paths with 1.3px stroke, consistent style across all views. Defined inline in `App.tsx` as `NAV_ICONS` record.

Active state uses a **left-border indicator** (Linear pattern):
- All nav links have `border-l-2` always — `border-transparent` inactive, `border-[--retro-border-active]` active
- Content starts at 20px from edge (2px border + 18px padding = `pl-[18px]`) to align with sidebar header `px-5`
- No box, no background box border, no pill — just the left accent line + subtle bg lift

MobileNav icons updated to match — same SVG set, same stroke weight.

### 3. Badges — Square with Uppercase Tracking

Badge shape changed from pill (`border-radius: 9999px`) to square (`border-radius: 3px`).

Typography: `font-size: 0.6875rem`, `font-weight: 500`, `letter-spacing: 0.06em`, `text-transform: uppercase`, `line-height: 1.2`.

Rationale: Pill badges are the most overused pattern in generic UI kits. Square badges with uppercase tracking read as **labels** (semantic, functional) rather than **chips** (decorative, consumer). Matches how Linear, GitHub, and Vercel render status labels.

### 4. Section Header Typography — Uniform Uppercase Tracking

All section-level headers use the same treatment:
- `font-size: 0.6875rem` (11px)
- `font-weight: 600`
- `letter-spacing: 0.08em`
- `text-transform: uppercase`
- `color: var(--retro-text-muted)`

Applies to: `.retro-card__title`, `.retro-panel-header`, `.retro-kanban-column-header`, nav section labels.

Rationale: Uniform header treatment creates consistent visual rhythm. Muted color keeps headers subordinate to content — they orient, not dominate.

### 5. Data Typography — Berkeley Mono + Tabular Nums

Numeric data values use:
- `font-family: 'Berkeley Mono', ui-monospace, monospace` (Berkeley Mono is already the base font, but explicit for stat values)
- `font-variant-numeric: tabular-nums` — numbers align in columns

Applies to: `.retro-stat-value`, progress bar labels, any component displaying metrics.

Inputs and selects: explicit `font-size: 0.875rem` to prevent cross-browser inheritance issues.

### 6. Animation Philosophy

**Easing:** Custom CSS vars added to `.theme-retro`:
```css
--ease-out-quart: cubic-bezier(0.25, 1, 0.5, 1);   /* smooth, refined */
--ease-out-expo:  cubic-bezier(0.16, 1, 0.3, 1);    /* confident, decisive */
```
These replace `ease` and `ease-out` everywhere transitions matter. CSS default `ease` is banned for UI animations.

**Timing:** 150–200ms for feedback, 200–250ms for layout changes. Nothing exceeds 300ms except deliberate page-level transitions.

**Button active feedback:** `scale(0.97)` replaces `translateY(1px)`. Pressing *in* (scale) is the correct physical metaphor. Pushing *down* is wrong direction.

**No:** bounce easing, elastic easing, glow pulses, decorative particle effects, celebratory animations. Every animation must serve information transfer or spatial orientation.

**Skeleton loaders:** Gradient sweep shimmer (`.retro-skeleton`) replaces flat opacity pulse. Direction of shimmer communicates "loading left to right" — more informative than pulsing in place.

**Task panel / slide-in panels:** Travel distance reduced from 100% to 16px. A panel sliding from off-screen to position feels like a product reveal. A panel appearing 16px closer feels like it was always there, just hidden — more surgical.

### 7. Card Interactivity Scoping

Card hover transform (`translateY(-1px)`) restricted to `[role="button"]` cards only.

```css
.retro-card:hover { border-color + shadow only }
.retro-card[role="button"]:hover { + translateY(-1px) }
.retro-card[role="button"]:active { translateY(0) scale(0.995) }
```

`RetroCard` already sets `role="button"` when `onClick` is provided. Non-interactive cards showing status/data no longer pretend to be clickable by lifting on hover.

### 8. Accessibility — prefers-reduced-motion

Blanket `prefers-reduced-motion: reduce` block added at end of `retro-theme.css`:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

This was entirely absent before. Now all animations degrade gracefully.

---

## Implementation

All changes applied to:
- `dashboard/src/styles/retro-theme.css` — CSS tokens, component styles, animations
- `dashboard/src/App.tsx` — AppHeader, AppNavigation (SVG icons, active state, spacing)
- `dashboard/src/components/ui/MobileNav.tsx` — SVG icons replacing emoji strings
- `dashboard/src/components/ui/ResponsiveLayout.tsx` — SVG hamburger/close icons
- `dashboard/src/components/ui/LoadingSpinner.tsx` — Skeleton component uses `.retro-skeleton`
- `homelab-ai/CLAUDE.md` — Design Context section (persisted for all future sessions)

Committed: `d0cdf2cb` — "feat(dashboard): full UX redesign — Linear/command-center aesthetic"

---

## Consequences

### Positive
- All future dashboard work has documented design context in `CLAUDE.md` — no more cold-start drift
- Consistent visual hierarchy across all views without per-component negotiation
- Animations feel mechanical and fast — appropriate for a monitoring/ops tool
- Accessibility baseline established
- Navigation is keyboard-accessible and screen-reader friendly (no emoji noise)

### Negative
- "Retro" naming in CSS classes (`retro-btn`, `retro-card`, etc.) is now a misnomer — the aesthetic is modern dark, not retro
- Some views (Agents, Sessions, Tasks) still use inline Tailwind classes that may not conform to the new system — incremental cleanup needed

### Mitigations
- "Retro" as a codename is acceptable; renaming all classes would break things with no user-visible benefit — defer indefinitely
- Per-view cleanup can happen opportunistically as those views are touched

---

## Related Decisions

- [2026-02-18-consolidated-adr-dashboard.md](2026-02-18-consolidated-adr-dashboard.md) — prior dashboard architecture decisions
- `homelab-ai/CLAUDE.md` — living design context document; update this if direction changes
