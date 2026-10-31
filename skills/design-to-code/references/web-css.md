# Web CSS mapping (shared)

Shared by `blazor.md`, `react.md`, `nextjs.md`, and `html-js-css.md`. Read once, at the first plan step. When the project uses Tailwind or a CSS-in-JS library, express the same values in its syntax: arbitrary values (`gap-[12px]`) beat nearest-scale classes.

## Base

The harness root and every component use `box-sizing: border-box` (pen widths include padding). Values are CSS px at design scale; never round.

## Layout

- flow → `display: flex`, `flex-direction: row | column`; gap → `gap`; padding → `padding`.
- main-axis alignment → `justify-content`; cross-axis → `align-items`.
- fill_container → main axis `flex: 1 1 0; min-width: 0` (`min-height: 0` in a column); cross axis `align-self: stretch`.
- fit_content → `flex: 0 0 auto`, no fixed size. Fixed size → `width`/`height` plus `flex-shrink: 0`.
- absolute → `position: absolute; left; top` inside a `position: relative` parent.
- fill → `background`; radius → `border-radius`; clip → `overflow: hidden`; opacity → `opacity`.
- text growth: auto width → `white-space: nowrap`; fixed width → wrap; fixed size → `overflow: hidden`.

## Typography

- Self-host every used weight and style with `@font-face` (`font-display: swap`); no CDN fonts. A missing font file is a blocker.
- `font-size` px; `font-weight` numeric; `font-style`; `line-height` in px, exact (pen `lineHeight` is a multiplier of font size: px = multiplier × size); `letter-spacing` = pen percent ÷ 100 in `em`; `text-align`.
- Harness root: `-webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale` to match pen's grayscale anti-aliasing.

## Strokes

- `inner`: `border` with `border-box`. When `bounds-diff.py` shows children shifted by the stroke width, switch to `box-shadow: inset 0 0 0 <w> <color>` (uniform widths only) and record an override.
- `center`: `outline: <w> solid <color>; outline-offset: -<w/2>`. `outer`: `outline-offset: 0`. Per-side widths come from `strokeWidth` `{top, right, bottom, left}`. Outlines follow `border-radius` and never affect layout.
- Per-side widths → `border-<side>-width`. Dashes → `border-style: dashed` is not exact: use an SVG stroke, or record a divergence.

## Effects

- Shadow (`shadowType` `outer`) → `box-shadow: <offset.x> <offset.y> <blur> 0 <color>` (pen shadows have no spread); `inner` → `inset`; several → comma list in design order. Map blur 1:1, confirm once per target with the pixel diff, record corrections in `overrides`.
- Linear → `linear-gradient(<angle>, stops)`. Pen `rotation` is degrees counter-clockwise from up; CSS angles run clockwise from up, so CSS angle = (360 − rotation) mod 360. Stop `position` 0–1 → percent. Radial → `radial-gradient`. Angular → `conic-gradient`.
- Layer blur → `filter: blur()`; background blur → `backdrop-filter: blur()`; blend modes → `mix-blend-mode`. Confirm each with the pixel diff; a visible mismatch is a divergence.

## Tokens

- Reuse the project's token system (CSS variables, Tailwind theme, `@theme` in Tailwind v4, theme object). Otherwise create one `tokens.css`: `:root { --<name>: ... }` for light and theme-independent values, `[data-theme="dark"] { ... }` for dark. `<name>` is the pen variable name without `$`.
- Consumers use `var(--<name>)`. The theme switch sets `data-theme` on `<html>`; `web-capture.mjs` sets it too.

## Assets

- Icons from path geometry → inline `<svg>` with exact `viewBox`, `d`, `fill`, and stroke values.
- Image fills → pen `Export` into the project's static folder; set `width` and `height`.

## Anchors

Anchor = `data-design-id="<segment>"` on the element. The anchor path joins the segments of anchored ancestors below the root, then the element's own. Give each repeated instance a distinct segment (`Card1`, `Card2`) at its use site, so the component's inner segments (`Title`) stay unique through the path. Attributes stay in production markup; they are inert.

## Harness

Capture needs a URL rendering only the target at design size. Order: `map.commands.capture`; an existing Storybook story; else ask once to scaffold the framework's dev-only harness route. The harness wraps the target in `<div data-design-id="<root>" style="width:<w>px;height:<h>px">` only when the target itself is not the root element, imports the same global CSS and tokens, and never ships in production builds.

## Playwright

`web-capture.mjs` resolves Playwright from the web project's `node_modules`. Missing: ask once to add `@playwright/test` as a dev dependency and run `npx playwright install chromium`; the script falls back to installed Google Chrome. A project without `package.json` (Blazor, plain HTML) gets a `tests/visual/package.json` only after approval.

## Smoke

Start the dev server once per run in the background, log to a file, reuse it for every capture, and stop it at the end of the run. Bind it to `127.0.0.1`; never fetch `.pen` or dotfiles through it. `web-capture.mjs` fails on uncaught page errors. Also scan the dev server log for the framework's failure strings.

## Audit

Semantic elements (`button`, `a`, ordered headings, `label` for inputs), `aria-label` on icon-only controls, `alt` on images, visible `:focus-visible` styles, tab order following DOM order, `lang` on `<html>`, `prefers-reduced-motion` respected. Use the project's a11y linter (for example `eslint-plugin-jsx-a11y`) when present.
