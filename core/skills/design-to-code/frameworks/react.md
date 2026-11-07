# Framework: React

Layout, Typography, Strokes, Effects, Tokens, Assets, Anchors, Harness, Playwright, Smoke, and Audit follow `references/web-css.md`. This file holds only React specifics. Next.js projects use `nextjs.md` instead.

## Companion

`typescript-best-practices` when the project uses TypeScript; otherwise none.

## Conventions and defaults

- Detect the bundler (Vite, CRA, Parcel, Rsbuild), language (TS or JS), package manager (lockfile: `pnpm-lock.yaml`, `yarn.lock`, `bun.lock*`, `package-lock.json`), and styling system (Tailwind, CSS Modules, styled-components, Emotion, vanilla-extract, plain CSS). Reuse all of them.
- Component unit: function component; props only for real instance differences; `children` for slots.
- No styling system: CSS Modules (`Component.module.css`) plus one global `tokens.css`.

## Layout, Typography, Strokes, Effects

See `references/web-css.md`. In `style` props, write numbers as px strings when the property is not unitless (`lineHeight: "20px"`).

## Tokens

`src/styles/tokens.css` (or the existing variables file), imported once in the entry file. Add it to `revisionFiles`.

## Assets

Fonts and images under `src/assets` (imported) or `public/` (root-relative URLs), following the project's choice. SVG icons as inline JSX or the project's SVG loader.

## Anchors

`data-design-id` per `references/web-css.md`. Reusable components accept and forward a `data-design-id` prop (or spread `...rest`) onto their root element.

## Build and smoke

- Build: the `build` script with the detected package manager; also the `typecheck` or `tsc --noEmit` script when present.
- Smoke: start the `dev` script once and keep it running; scan its log for `error`, `Failed to resolve import`, and `Uncaught`; `web-capture.mjs` fails on page errors.
- Runtime scale probe: none; default 2.

## Capture

`captureMethod: playwright`. Harness order per `references/web-css.md`. Default dev-only harness: `src/__design/Harness.tsx` mounted when the URL has `?design=<id>`, imported behind `import.meta.env.DEV` (Vite) or `process.env.NODE_ENV !== "production"`, so production bundles drop it. Example:

```
node <skill>/scripts/web-capture.mjs --url "http://localhost:5173/?design=<id>&theme=<theme>" --root <root anchor> --out <dir> --scale <scale> --theme <theme> --width <w> --height <h>
```

## Audit

`references/web-css.md` Audit, plus: icon-only buttons have `aria-label`, interactive elements are real `button`/`a` (no click handlers on `div`), list keys stable.
