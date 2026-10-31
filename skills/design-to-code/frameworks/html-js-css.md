# Framework: HTML/JS/CSS

Layout, Typography, Strokes, Effects, Tokens, Assets, Anchors, Harness, Playwright, Smoke, and Audit follow `references/web-css.md`. This file holds only plain-web specifics.

## Companion

none.

## Conventions and defaults

- Reuse the project's file layout, CSS methodology, and any JS rendering pattern. Add no framework or bundler.
- Component unit: a CSS class block per design component (BEM-style names when the project has no convention) in one stylesheet. Repeated subtrees: duplicate markup when static; a `<template>` cloned by a small JS function when the project already renders from JS; Web Components only when the project already uses them.

## Tokens

`css/tokens.css` (or the existing variables file), linked before other stylesheets in every page. Add it to `revisionFiles`.

## Assets

Fonts under `fonts/`, images under `images/` (or the existing folders), root-relative URLs.

## Build and smoke

- Build: none, unless `package.json` defines one; then run it.
- Smoke: serve over HTTP on loopback only, from the project root: `python3 -m http.server 8000 --bind 127.0.0.1` (or the project's dev server bound to `127.0.0.1`); fonts and modules fail over `file://`. `web-capture.mjs` fails on page errors. Run an HTML validator only when the project already has one.
- Runtime scale probe: none; default 2.

## Capture

`captureMethod: playwright`. Harness: `__design/<id>.html`, linking the same stylesheets and scripts, containing only the target. The harness is the capture backend the map records: while `commands.capture` references `__design/`, keep it so resume and independent verification can re-run the command, and cover the deploy-exclusion question in the grouped question (ask, or confirm nothing deploys it). Delete `__design/` at the end of the run only when the recorded capture no longer depends on it and the project's deployment would publish it with no ignore list excluding it; report either outcome. Example:

```
cd tests/visual && node <skill>/scripts/web-capture.mjs --url http://localhost:8000/__design/<id>.html --root <root anchor> --out <dir> --scale <scale> --theme <theme> --width <w> --height <h>
```

## Audit

`references/web-css.md` Audit.
