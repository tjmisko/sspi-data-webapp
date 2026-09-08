# SSPI Design Language — Style Guide

This guide codifies the site's existing design language so every page reads as
one system. The reference standard is the **data pages** (`/data`,
`/data/pillar|category|indicator/<code>`): calm, bordered panels on a deep navy
ground, with color reserved for data. Nothing in this guide invents a new
direction; it names what the strongest pages already do and closes the gaps
where other pages drifted.

## 1. Voice

The SSPI is an academic policy index. The register is **policy paper, not
dashboard product**: quiet chrome, generous measure for prose, data rendered
large and unboxed, one restrained accent. Decoration never competes with a
chart.

## 2. Typography

Three working faces, all already loaded or on-device:

| Role | Token | Stack | Use |
|---|---|---|---|
| Display | `--title-font-family` | `'REM', system-ui, sans-serif` | Wordmark, `h1`, page/section titles, stat-tile numerals |
| UI / body | `--body-font-family` | `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif` | Everything not otherwise specified; set on `body` |
| Long-form serif | `--article-body-font-family` | `'Libre Baskerville', Georgia, serif` | Article and methodology prose only — the "policy paper" register |
| Code | `--code-font-family` | `ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace` | Series codes, code chips, score functions |

Rules:

- `--header-font-family` aliases the UI stack. Headings differ from body by
  size and weight, not by family; REM is reserved for display moments so it
  stays special.
- `h1` weight comes from `--title-weight` (400 light / 300 dark — the dark
  theme goes lighter to compensate for halation; keep this).
- The heading scale must be monotonic (h6 < h5 < h4 …).
- Serif is opt-in via `.print-style-article` / article prose containers, never
  the default.
- Body `line-height` is unitless (`1.5`), never a fixed length.
- Abril Fatface is not part of the system and is not loaded.
- Root font-size is 16pt (1rem = 21.33px). Author sizes accordingly; do not
  copy Tailwind-idiom values (`0.875rem` etc.) that assume a 16px root.
- Minimum text size ~0.6rem (≈12.8px); no interface text below that.

## 3. Color

### Ground

Dark theme (default): navy ladder from `--page-background` up through
`--box-background-color`. Light theme mirrors it in neutral grays. Cards are
separated from the page by a **1px border plus a background step — never a
shadow**. `--shadow-*` is reserved for genuinely floating elements (menus,
modals, tooltips).

### Accent discipline (the core rule)

- **`--green-accent`** is the single chrome accent: link hovers, focus,
  affirmative values, active states. Applied as a `color-mix` tint of the
  existing surface (10–15%), never as a background swap.
- **Pillar colors encode data, never chrome.** `--sus-color` green,
  `--ms-color` orange, `--pg-color` blue, `--sspi-color` gold appear in
  charts, chips, and left-edge rails that classify content — never as page or
  section decoration. There is no green header on the Sustainability page.
- **`--primary-color`** blue is for interactive UI (buttons, focus rings) and
  is theme-aware.
- Pillar colors used against surfaces go through the theme-aware
  `--sus-accent` / `--ms-accent` / `--pg-accent` variants (hue preserved,
  lightness adjusted per theme) so they pass AA on both grounds. Raw brand
  hexes never appear as small text.

### Contrast floor

All text ≥ 4.5:1 against its real composited background in **both themes**;
UI affordances ≥ 3:1. When a brand color fails, mix it toward the theme's
text pole (`color-mix(... , black)` on light, `..., white` on dark) rather
than swapping hue.

## 4. Surfaces and cards

- Card recipe: `background: var(--box-background-color); border: 1px solid
  var(--border-color); border-radius: var(--border-radius)` (8px) for compact
  components, `--border-radius-lg` (12px) for page-level panels. Nested radii
  step down, never up.
- Two-tone card: recessed header in `--region-background-color`, body in
  `--box-background-color`, parent `overflow: hidden` clips both to the
  radius.
- **Chrome is carded; data is not.** Charts float bare on the page background
  with only padding.
- Collapsibles use native `<details>/<summary>` wherever no JS state is
  needed.
- Interior rhythm: `> *:not(summary) { padding: 0.5rem }` and
  `:last-child { margin-bottom: 0 }`.
- Hierarchy inside a list/tree comes from **indentation + a pillar-colored
  left border + typographic weight**, not from full-row background tints.

## 5. Interaction

- Hover = tint the existing surface with the accent (`color-mix` 10–15%), plus
  at most a 1px border-color change and `--shadow-sm`. Reserve layout space so
  nothing jumps (transparent borders at rest).
- Every focusable element gets `:focus-visible { outline: 2px solid
  var(--primary-color); outline-offset: 2px }` or the component's accent
  equivalent.
- Elements are clickable-looking only when clickable (`cursor: pointer` never
  decorates).
- One transform per hover; parent and child never both move.

## 6. Layout

- Content column: `.content-container`, max-width 1280px. Long-form prose:
  `.print-style-article`, max-width 70ch.
- Page sections separated by 2rem; the footer is pinned by a flex column
  `body` (`min-height: 100vh`, `main { flex: 1 }`) so sparse pages never
  float it mid-viewport.
- Breadcrumb-as-title on data pages: current item larger but lighter (400)
  than its ancestors (500).
- One breakpoint per component, two modes, one markup.

## 7. Tokens

`variables.css` is the single source of truth. Rules:

- No undefined `var()` references — every alias used anywhere must be defined
  (aliased to a real token if legacy).
- One name per value: `--border-color` (not `--subtle-line-color`),
  `--header-text-color` (not `--header-font-color`); legacy names remain as
  aliases only.
- Page CSS may define a page-scoped semantic accent
  (`--download-accent`-style) but never a private palette.
- Component CSS is scoped to the component's root class; generic names
  (`.card-header`, `.no-data-message`, `.collapse-icon`) never ship unscoped
  in the global bundle.
