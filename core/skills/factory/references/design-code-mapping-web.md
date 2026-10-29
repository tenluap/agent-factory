# Web translation and capture

Load only for a web target under the [shared mapping contract](design-code-mapping.md). The shared contract owns identity, scope, evidence, exceptions and repair limits.

## Discover and survey

Identify web targets from HTML/CSS or `package.json` and project files for React/TSX, Vue or Svelte. Locate the target, its component dependencies, tokens, assets, existing build/test commands and supported launch/capture path. Follow repository conventions and guidance; an unavailable runtime cannot be replaced by claimed evidence.

Survey component definitions and relevant instances, including hidden children, optional content, layout, assets, fonts, effects and tokens. Inspect other callers before modifying shared components. Record and match viewport, route, active state, theme, device scale and capture configuration.

## Translate by dependency

Reuse existing primitives, components, styles and tokens at their canonical project locations; use the repository's component and token directories rather than introducing parallel ones. Put repeated visual blocks in existing or canonical components, one-off composition in the parent, and preserve actual instance differences. Use the project's layout and responsive patterns to match reference geometry.

Implement tokens and assets before shared components and views. Preserve child order, instance counts, overrides, visibility, content, typography, wrapping and accessibility behavior. Record unavailable assets or effects as gaps or approved departures, not silent approximations. Map to stable source files and component, element or token anchors that resolve in current code.

## Validate the running target

Use build and runtime commands discovered from the repository, and run relevant existing tests for behavior changes. Launch the actual target, inspect runtime errors and capture its current rendering with matching configuration. Compare the whole reference first, then localized crops and impacted shared consumers. Check responsive sizing, clipping, theme, keyboard and focus behavior.

Reuse fresh build, survey and captures until source, code or configuration changes invalidate them. Consolidate mismatches in the shared repair queue; static review never substitutes for runtime and matched rendered comparison.
