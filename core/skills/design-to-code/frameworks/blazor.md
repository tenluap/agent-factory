# Framework: Blazor

Layout, Typography, Strokes, Effects, Tokens, Assets, Anchors, Harness, Playwright, Smoke, and Audit follow `references/web-css.md`. This file holds only Blazor specifics.

## Companion

`aspnet-core`.

## Conventions and defaults

- Detect render mode (Server, WebAssembly, Auto, static SSR) and keep it. Reuse existing components and CSS first.
- Component unit: `.razor` with `[Parameter]` properties for real instance differences and `RenderFragment` for slots. Styles: CSS isolation (`Component.razor.css`) unless the project uses a global stylesheet or a CSS framework.
- Interactive components need an interactive render mode; presentational ones stay static.

## Layout, Typography, Strokes, Effects

See `references/web-css.md`. Scoped CSS cannot style child components' internals: use `::deep` only when the project already does.

## Tokens

`wwwroot/css/tokens.css` (or the project's existing variables file), linked in `App.razor` (or `wwwroot/index.html` for standalone WebAssembly) before component styles. Add it to `revisionFiles`.

## Assets

Static files under `wwwroot/`; fonts under `wwwroot/fonts`; reference with root-relative URLs or `@Assets["..."]` when the project uses static asset mapping.

## Anchors

`data-design-id` per `references/web-css.md`. Components forward it with `@attributes` splatting or an explicit parameter.

## Build and smoke

- `dotnet build <project> --no-restore` (drop `--no-restore` when restore is stale).
- Smoke: `dotnet run` (or `dotnet watch`) once, then capture the harness. Scan the server log for `Unhandled exception` and `fail:` lines, and treat a visible `#blazor-error-ui` as a failure.
- Runtime scale probe: none; default 2.

## Capture

`captureMethod: playwright`. Harness: a `@page "/__design/{Id}"` component that renders the target by ID, registered only when `app.Environment.IsDevelopment()` (or under `#if DEBUG`). Example:

```
cd tests/visual && node <skill>/scripts/web-capture.mjs --url http://localhost:5000/__design/<id>?theme=<theme> --root <root anchor> --out <dir> --scale <scale> --theme <theme> --width <w> --height <h>
```

## Audit

`references/web-css.md` Audit, plus: `<FocusOnNavigate>` present for routed pages, `<PageTitle>` set, form components with `<label for>` or `aria-label`.
