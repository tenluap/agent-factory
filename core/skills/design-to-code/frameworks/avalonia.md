# Framework: Avalonia

Verify every property name against the project's Avalonia package version.

## Companion

`avalonia` (also `avalonia-mvvm`, `avalonia-data-binding` for MVVM and binding questions).

## Conventions and defaults

Reuse existing controls, styles, and resources first. `UserControl` for repeated configured blocks; `ControlTemplate`/`DataTemplate` or MVVM when behavior or binding needs it; a `Style` or resource for repeated visual-only primitives. Preserve the project's MVVM toolkit.

## Layout

- flow → `StackPanel.Orientation`; gap → `Spacing`; padding → `Padding`.
- fill_container → `HorizontalAlignment`/`VerticalAlignment` `Stretch`, or star size in a `Grid`. fit_content → no fixed size.
- absolute → `Canvas.Left`, `Canvas.Top`.
- fill → `Background`; radius → `CornerRadius`; clip → `ClipToBounds`; opacity → `Opacity`; text growth → `TextWrapping`.

## Typography

- Embed exact font files as `AvaloniaResource`; reference `avares://<Assembly>/Assets/Fonts#<Family>`.
- `FontSize`; `FontWeight` numeric; `FontStyle`. `LineHeight` in DIPs = pen `lineHeight` multiplier × font size. `LetterSpacing` in DIPs; if absent in the project's version, record a divergence.
- `TextAlignment`; vertical alignment through the container's `VerticalAlignment`.
- Capture root: `RenderOptions.TextRenderingMode="Antialias"` to match pen's grayscale anti-aliasing.

## Strokes

- `inner`: `Border` `BorderThickness` + `BorderBrush`; drawn inside bounds, no compensation.
- `center`: grow by the stroke width (negative `Margin` of half the width per stroked side). Record an override.
- `outer`: grow by twice the width (negative `Margin` of the full width per stroked side). Record an override.
- Per-side widths → four-value `Thickness`. Dashes → divergence unless a `Shape` with `StrokeDashArray` draws it.

## Effects

- Shadow → `BoxShadow="<offset.x> <offset.y> <blur> 0 <color>"` (pen shadows have no spread); `inner` → prefix `inset`. Map blur 1:1, confirm once per target with the pixel diff; record any correction in `overrides`.
- Linear → `LinearGradientBrush` with relative `StartPoint`/`EndPoint` computed from pen `rotation` (degrees counter-clockwise from up) and `size.height`, exact stops. Radial → `RadialGradientBrush`. Angular, layer blur, background blur, blend modes → divergence.

## Tokens

- Reuse the project's token file. Otherwise create `Styles/Tokens.axaml`, merged in `App.axaml`. Themed values in `ResourceDictionary.ThemeDictionaries` under `Light` and `Dark`; theme-independent values at top level.
- Color → `Color` plus `SolidColorBrush` keyed `<name>Brush`. Spacing → `Thickness` or `x:Double`. Radius → `CornerRadius`. Font size and line height → `x:Double`. Font family → `FontFamily`.
- Themed brushes via `DynamicResource`; others via `StaticResource`.

## Assets

Export image fills with pen `Export` into the existing asset folder; reference `avares://<Assembly>/<path>`. Icons: `PathIcon` or `Path` with exact `Data` from path geometry.

## Anchors

Anchor = `x:Name`. Anchor path = `x:Name` values of named visual ancestors below the root, then the element's own (`Card1/Title`). Named elements inside `UserControl` namescopes stay distinct through the path.

## Build and smoke

- `dotnet build <project> --no-restore` (drop `--no-restore` when restore is stale). Avoid clean and full-solution builds.
- Smoke: launch the app, or a headless test that instantiates the target view with App resources. An app launch runs in the background with the log redirected to a file; scan it after 20 s or on exit, then stop the app unless capture reuses it. Scan for `Unhandled exception`, binding errors, and resource-not-found errors; confirm the exact strings on first run.
- Runtime scale probe: top-level `RenderScaling` via DevTools (verify the property name).
- DevTools prerequisites (fallback, smoke, live trials only): `AvaloniaUI.DiagnosticsSupport` referenced and `WithDeveloperTools`/`AttachDeveloperTools` called. Missing: grouped question; never add without approval.

## Capture

Headless test project (`captureMethod: headless`). None exists: offer to scaffold `*.Visual.Tests` in the grouped question; on approval store `commands.capture`:

```
dotnet test tests/App.Visual.Tests --filter "Target=<id>" -- Capture.Out=<dir> Capture.Scale=<scale> Capture.Theme=<theme>
```

- Use the solution's test framework (`Avalonia.Headless.XUnit`, `.NUnit`, or MSTest + `Avalonia.Headless`); default xUnit; match the app's Avalonia version.
- `AppBuilder.Configure<App>().UseSkia().UseHeadless(new AvaloniaHeadlessPlatformOptions { UseHeadlessDrawing = false })`, app fonts registered.
- Host the view in a `Window` sized to the target's design size; theme via `RequestedThemeVariant`; render scale `<scale>` (verify the API).
- Disable transitions, clear focus, hide carets, `Dispatcher.UIThread.RunJobs()`, wait for fonts, then `CaptureRenderedFrame()`. Crop to the root when the target is inside a larger view.
- Bounds: `element.TranslatePoint(new Point(0, 0), root)` plus `Bounds.Size` for every named element.

Fallback (refused scaffold), `captureMethod: devtools`: attach to the running app, apply determinism where possible, `screenshot({nodeId})` of the target root (not the window), bounds from `props Bounds` along the parent chain.

DevTools (`tools.avalonia_devtools`): `search({query, scopeNodeId, limit})`, `tree({nodeId, treeKind: Logical|Visual|Merged, depth})`, `props({nodeId, propertyNames})`, `styles({nodeId, propertyNames, includeDefaults})`, `screenshot({nodeId})`, `attach-to-app({id})`, `attach-to-file({xamlFilePath, xamlProjectPath, build})`, `set-prop({nodeId, propertyName, value, isXamlValue})` for live trials. Node IDs go stale after reloads.

## Audit

Focus visuals, `KeyboardNavigation.TabIndex` order, `AutomationProperties.Name` on icon-only controls, text clipping (`TextTrimming`), hit targets.
