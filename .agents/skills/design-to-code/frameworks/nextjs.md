# Framework: Next.js

Layout, Typography, Strokes, Effects, Tokens, Assets, Anchors, Harness, Playwright, Smoke, and Audit follow `references/web-css.md`. React component rules from `react.md` (Conventions, Anchors) apply. This file holds only Next.js specifics.

## Companion

`typescript-best-practices` when the project uses TypeScript; use `find-docs` for Next.js APIs.

## Conventions and defaults

- Detect App Router (`app/`) or Pages Router (`pages/`) and keep it. Detect the styling system as in `react.md`.
- App Router: components stay Server Components unless they need state, effects, or event handlers; then add `"use client"` to the smallest wrapping component.
- Theme: reuse `next-themes` or the existing provider; otherwise set `data-theme` on `<html>` in the root layout.

## Typography

Fonts through `next/font/local` with exact files, one `src` entry per weight and style, exposed as a CSS variable (`variable: "--font-<name>"`) on `<html>`. Typography values per `references/web-css.md`.

## Tokens

`app/tokens.css` (or `styles/tokens.css` for Pages Router, or the existing variables file), imported in the root layout (`app/layout.tsx`) or `pages/_app.tsx`. Add it, the root layout, and `globals.css` to `revisionFiles`.

## Assets

Images under `public/`; use `next/image` with exact `width` and `height` when the project does, plain `<img>` otherwise. Inline SVG for icons.

## Build and smoke

- Build: the `build` script (`next build`), which also type-checks and lints.
- Smoke: start `next dev` once and keep it running; scan its log for `Error:`, `Module not found`, and `Hydration failed`; `web-capture.mjs` fails on page errors.
- Runtime scale probe: none; default 2.

## Capture

`captureMethod: playwright`. Harness route (App Router folders starting with `_` are private, so no `__design`): `app/design-harness/[id]/page.tsx`, or `pages/design-harness/[id].tsx`. It calls `notFound()` when `process.env.NODE_ENV === "production"`. Example:

```
node <skill>/scripts/web-capture.mjs --url "http://localhost:3000/design-harness/<id>?theme=<theme>" --root <root anchor> --out <dir> --scale <scale> --theme <theme> --width <w> --height <h>
```

## Audit

`references/web-css.md` Audit, plus: `<html lang>` set in the root layout, `metadata` title per page, `next/link` for internal navigation.
