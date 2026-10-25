# Avalonia translation and capture

Load only for an Avalonia target under the [shared mapping contract](design-code-mapping.md). This guide supplies framework choices; the shared contract owns identity, scope, evidence, exceptions, and repair limits.

## Discover and survey

Locate the target Avalonia project, view, view model, resources/themes, build/test commands, and supported launch/capture path. Read repository guidance and available Avalonia guidance once through the adapter's skill resolution when needed. Reuse a working runtime/DevTools connection; its absence cannot be replaced by claimed runtime evidence.

Survey component definitions and relevant instances, including hidden children, optional content, wrapping/growth, exact vector/icon assets, fonts, effects, and theme variables. Inspect other callers before modifying shared controls. Match capture viewport, active view/state, theme, DPI, zoom, and export scale.

## Translate by dependency

| Design construct | Avalonia choice |
|---|---|
| Existing matching primitive/style | Reuse the project resource/control. |
| Repeated configured visual block | Canonical `UserControl` following project conventions. |
| Behavior/binding-dependent control | Existing MVVM or templated-control pattern; expose only actual instance differences. |
| Repeated visual-only variant | Style/resource rather than another behavior abstraction. |
| One-off composition | Parent view. |
| Directional flow, gap, padding | Appropriate panels/grid and container padding/margins, preserving measured values. |
| Fill/fit sizing | Stretch/star versus auto sizing, validated against actual rendering. |
| Absolute placement | Exact offsets/Canvas when the reference requires it. |

Implement tokens/assets before canonical components and parent composition. Preserve child order, instance counts, overrides, visibility, content, typography/wrapping, exact geometry, and accessibility behavior. Optional visibility/content is needed when relevant instances vary. Unsupported effects or unavailable fonts become explicit gaps or approved departures, not silent approximations.

Map to stable `.axaml` files plus symbols, `x:Name`, or resource keys. Include code-behind/view-model anchors only where they actually implement design behavior. A code anchor must resolve in current code; line numbers are hints.

## Validate the running target

Build the affected project at coherent runnable checkpoints with the discovered command. Run relevant existing tests for behavior/binding changes. Observe the target for binding/resource/runtime errors and capture its actual current rendering. Compare the whole frame first; inspect crops for localized differences or impacted shared consumers. Check wrapping, clipping/overflow, theme behavior, keyboard/focus/accessibility conflicts, and relevant stretch behavior.

Reuse current build, survey, reference capture, and live connection until source/code/configuration changes invalidate them. Refresh runtime inspection IDs after UI reload. Consolidate mismatches in the factory's shared repair queue. Static `.axaml` review supplements this evidence and never substitutes for a running target and matched screenshot comparison.
