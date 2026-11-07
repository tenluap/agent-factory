# Framework: .NET MAUI

Verify every property name and unit against the project's MAUI version (use `find-docs` when unsure). MAUI's units differ from Avalonia's in several places noted below.

## Companion

none (use `find-docs` for MAUI APIs).

## Conventions and defaults

Reuse existing controls, styles, and resources first. `ContentView` for repeated configured blocks; `ControlTemplate`/`DataTemplate` or MVVM when behavior or binding needs it; implicit or keyed `Style` for repeated visual primitives. Preserve the project's MVVM toolkit. Blazor Hybrid UI: use `blazor.md` for the UI and this file for host, fonts, and capture.

## Layout

- flow → `VerticalStackLayout`/`HorizontalStackLayout`; gap → `Spacing`; padding → `Padding`.
- fill_container → `HorizontalOptions`/`VerticalOptions` `Fill`, or star size in a `Grid`. fit_content → no fixed size. Fixed size → `WidthRequest`/`HeightRequest`.
- absolute → `AbsoluteLayout.LayoutBounds` with `AbsoluteLayoutFlags="None"`.
- fill → `Background`; radius → `Border.StrokeShape="RoundRectangle <radius>"`; clip → `IsClippedToBounds` or `Clip`; opacity → `Opacity`; text growth → `LineBreakMode`.

## Typography

- Fonts in `Resources/Fonts` as `MauiFont`; register each file in `MauiProgram.ConfigureFonts` with one alias per weight and style (`fonts.AddFont("Inter-SemiBold.ttf", "InterSemiBold")`). `FontAttributes` only has Bold and Italic: numeric weights need their own file and alias.
- `FontSize` in DIPs. `Label.LineHeight` is a multiplier, like pen `lineHeight`: copy it unchanged. `CharacterSpacing`: verify its unit in the project's version before converting from pen percent.
- `HorizontalTextAlignment`, `VerticalTextAlignment`.

## Strokes

- `Border` with `Stroke` and `StrokeThickness`. Confirm stroke placement with `bounds-diff.py` once per target; when it differs from the design's `inner`/`center`/`outer`, compensate with `Margin` and record an override.
- Per-side widths → nested `Border` or `BoxView` edges, recorded as override. Dashes → `StrokeDashArray`.

## Effects

- Shadow → `Shadow` (`Brush`, `Offset`, `Radius`, `Opacity`); pen shadows have no spread. Inner shadow → divergence. Confirm blur mapping once with the pixel diff.
- Linear → `LinearGradientBrush`, relative `StartPoint`/`EndPoint` from pen `rotation` (degrees counter-clockwise from up). Radial → `RadialGradientBrush` (`Center`, `Radius`). Angular, layer blur, background blur, blend modes → divergence.

## Tokens

- Reuse the project's token file. Otherwise create `Resources/Styles/Tokens.xaml`, merged in `App.xaml` `MergedDictionaries`.
- Themed values: keep `<name>Light` and `<name>Dark` `Color` resources and consume `{AppThemeBinding Light={StaticResource <name>Light}, Dark={StaticResource <name>Dark}}` (MAUI has no `ThemeDictionaries`). Theme-independent values: plain keys.
- Spacing → `Thickness` or `x:Double`; radius → `x:Double`; font size → `x:Double`.

## Assets

Images in `Resources/Images` as `MauiImage` (lowercase letters, digits, underscores; SVG is rasterized at build). Icons from path data → `Path` with exact `Data`.

## Anchors

Anchor = `x:Name`. Anchor path as in `avalonia.md` (named ancestors below the root, then own name).

## Build and smoke

- `dotnet build <project> -f <tfm>` with the desktop TFM from `TargetFrameworks` (`net*-maccatalyst` on macOS, `net*-windows*` on Windows).
- Smoke: `dotnet build -t:Run -f <tfm>`. Run it in the background with the log redirected to a file. Scan the log after 20 s or on process exit, whichever comes first, then stop the process unless capture reuses it. Scan for `Unhandled exception`, `StaticResource not found for key`, and binding diagnostics; confirm exact strings on first run.
- Runtime scale probe: `DeviceDisplay.MainDisplayInfo.Density` logged by the capture hook.

## Capture

No headless renderer exists. `captureMethod: device`, machine-dependent. Offer in the grouped question to scaffold a debug-only capture hook:

- Compiled under `#if DEBUG`, activated by a request file `<dir>/capture-request.json` (`{"id", "theme", "out"}`) whose path the app reads from `DESIGN_CAPTURE_REQUEST` or, when the launcher drops environment variables, from a fixed path under the app's cache directory. The hook quits the app after writing.
- Hosts the target view alone in a window sized to the design size, sets `Application.Current.UserAppTheme`, disables animations, clears focus, waits for layout.
- Writes `capture.png` from `await root.CaptureAsync()` (verify the API) and `bounds.json` from each named element's `Frame` summed up the parent chain to the root. Logs display density; a density different from `<scale>` means re-export the reference at that scale.
- `commands.capture`: a small script that writes the request file for `<id>`, `<dir>`, `<theme>`, runs `dotnet build -t:Run -f <tfm>`, waits for `<dir>/bounds.json` with a 180 s timeout, and exits non-zero when it is missing. Confirm on the first run that the app sees the request.

Refused: visual gate is `blocked`; bounds and pixel checks are skipped and reported.

## Audit

`SemanticProperties.Description` on icon-only controls, `SemanticProperties.HeadingLevel` on headings, `TabIndex`/`IsTabStop` order, visible focus state in `VisualStateManager`, hit targets.
