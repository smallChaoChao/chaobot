---
name: ui-ux
description: "UI/UX design intelligence for chaobot dashboard. 67 styles, 96 color palettes, 57 font pairings, 25 chart types, 13 tech stacks. Design beautiful admin panels, dashboards, and configuration interfaces with professional aesthetics."
homepage: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
metadata: {"chaobot":{"emoji":"🎨","requires":{"bins":["python3"]}}}
---

# UI/UX Pro Max - Design Intelligence

Comprehensive design guide for chaobot dashboard and web interfaces. Contains 67+ UI styles, 96 color palettes, 57 font pairings, 99 UX guidelines, and 25 chart types.

## When to Apply

Use this skill when:
- Designing or improving chaobot dashboard UI
- Creating configuration management interfaces
- Building admin panels or control panels
- Choosing color palettes and typography for web apps
- Reviewing frontend code for UX issues
- Implementing accessibility requirements

## Quick Reference

### Critical Rules (Priority 1-2)

| Rule | Description |
|------|-------------|
| `color-contrast` | Minimum 4.5:1 ratio for normal text |
| `focus-states` | Visible focus rings on interactive elements |
| `touch-target-size` | Minimum 44x44px touch targets |
| `cursor-pointer` | Add cursor-pointer to all clickable elements |
| `loading-buttons` | Disable button during async operations |

### High Priority (Priority 3-4)

| Rule | Description |
|------|-------------|
| `image-optimization` | Use WebP, srcset, lazy loading |
| `viewport-meta` | width=device-width initial-scale=1 |
| `readable-font-size` | Minimum 16px body text on mobile |
| `z-index-management` | Define z-index scale (10, 20, 30, 50) |

### Medium Priority (Priority 5-6)

| Rule | Description |
|------|-------------|
| `line-height` | Use 1.5-1.75 for body text |
| `font-pairing` | Match heading/body font personalities |
| `duration-timing` | Use 150-300ms for micro-interactions |
| `transform-performance` | Use transform/opacity, not width/height |

## How to Use This Skill

### Step 1: Analyze Requirements

Extract key information:
- **Product type**: admin panel, dashboard, configuration interface
- **Style keywords**: modern, professional, minimal, elegant
- **Industry**: AI assistant, developer tools, SaaS
- **Stack**: html-tailwind (default for chaobot dashboard)

### Step 2: Generate Design System

```bash
python3 chaobot/skills/ui-ux/scripts/search.py "admin panel dashboard configuration" --design-system -p "Chaobot Dashboard"
```

### Step 3: Get Stack Guidelines

```bash
python3 chaobot/skills/ui-ux/scripts/search.py "form card layout responsive" --stack html-tailwind
```

### Step 4: Search Specific Domains (as needed)

```bash
# Get style options
python3 chaobot/skills/ui-ux/scripts/search.py "modern minimal" --domain style

# Get color palettes
python3 chaobot/skills/ui-ux/scripts/search.py "saas dashboard" --domain color

# Get typography
python3 chaobot/skills/ui-ux/scripts/search.py "professional modern" --domain typography

# Get UX guidelines
python3 chaobot/skills/ui-ux/scripts/search.py "form animation accessibility" --domain ux
```

## Available Domains

| Domain | Use For | Example Keywords |
|--------|---------|------------------|
| `product` | Product type recommendations | admin panel, dashboard, configuration, SaaS |
| `style` | UI styles, colors, effects | glassmorphism, minimalism, dark mode, neumorphism |
| `typography` | Font pairings, Google Fonts | professional, modern, elegant, clean |
| `color` | Color palettes by product type | saas, dashboard, developer tools, tech |
| `landing` | Page structure, layout patterns | hero, sidebar, card-based, tabbed |
| `chart` | Chart types, data visualization | trend, comparison, status, metric |
| `ux` | Best practices, anti-patterns | animation, accessibility, form, loading |
| `web` | Web interface guidelines | aria, focus, keyboard, semantic |

## Available Stacks

| Stack | Focus |
|-------|-------|
| `html-tailwind` | Tailwind utilities, responsive, a11y (DEFAULT) |
| `react` | State, hooks, performance, patterns |
| `vue` | Composition API, Vue Router |
| `shadcn` | shadcn/ui components, theming |

## Common Rules for Professional Dashboard UI

### Icons & Visual Elements

| Rule | Do | Don't |
|------|----|----- |
| **No emoji icons** | Use SVG icons (Heroicons, Lucide) | Use emojis as UI icons |
| **Stable hover states** | Use color/opacity transitions | Use scale transforms that shift layout |
| **Consistent icon sizing** | Use fixed viewBox (24x24) | Mix different icon sizes |

### Interaction & Cursor

| Rule | Do | Don't |
|------|----|----- |
| **Cursor pointer** | Add `cursor-pointer` to all clickable elements | Leave default cursor |
| **Hover feedback** | Provide visual feedback (color, shadow) | No indication element is interactive |
| **Smooth transitions** | Use `transition-colors duration-200` | Instant or too slow (>500ms) |

### Layout & Spacing

| Rule | Do | Don't |
|------|----|----- |
| **Floating navbar** | Add `top-4 left-4 right-4` spacing | Stick navbar to edges |
| **Content padding** | Account for fixed navbar height | Let content hide behind navbar |
| **Consistent max-width** | Use same `max-w-6xl` or `max-w-7xl` | Mix different widths |

### Forms & Inputs

| Rule | Do | Don't |
|------|----|----- |
| **Clear labels** | Use visible labels above inputs | Hide labels or use placeholders only |
| **Focus states** | Visible focus ring on all inputs | Remove default focus styles |
| **Error feedback** | Show errors near problem field | Show all errors at top |

## Pre-Delivery Checklist

### Visual Quality
- [ ] No emojis used as icons (use SVG instead)
- [ ] All icons from consistent icon set
- [ ] Hover states don't cause layout shift
- [ ] Use theme colors directly

### Interaction
- [ ] All clickable elements have `cursor-pointer`
- [ ] Hover states provide clear visual feedback
- [ ] Transitions are smooth (150-300ms)
- [ ] Focus states visible for keyboard navigation

### Light/Dark Mode
- [ ] Light mode text has sufficient contrast (4.5:1)
- [ ] Glass/transparent elements visible in light mode
- [ ] Borders visible in both modes

### Layout
- [ ] Floating elements have proper spacing from edges
- [ ] No content hidden behind fixed elements
- [ ] Responsive at 375px, 768px, 1024px, 1440px
- [ ] No horizontal scroll on mobile

### Accessibility
- [ ] All images have alt text
- [ ] Form inputs have labels
- [ ] Color is not the only indicator
- [ ] `prefers-reduced-motion` respected

## Example: Beautify Chaobot Dashboard

```bash
# Generate design system for admin panel
python3 chaobot/skills/ui-ux/scripts/search.py "admin panel dashboard configuration modern professional" --design-system -p "Chaobot Dashboard"

# Get Tailwind-specific guidelines
python3 chaobot/skills/ui-ux/scripts/search.py "card form button tab responsive" --stack html-tailwind

# Get color palette recommendations
python3 chaobot/skills/ui-ux/scripts/search.py "saas tech developer tools" --domain color

# Get typography recommendations
python3 chaobot/skills/ui-ux/scripts/search.py "professional modern clean" --domain typography
```

Then apply the design system to create a beautiful, professional dashboard interface.
