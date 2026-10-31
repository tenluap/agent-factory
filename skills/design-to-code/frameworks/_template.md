# Framework: <Name>

Copy this file to add a framework, keep every heading, then add its row to the SKILL.md framework table and its name to `FRAMEWORKS` in `scripts/map-migrate.py`. A section that does not apply says "N/A" and why. Verify every API name against the project's own package version at run time.

## Companion

Skill to load for framework questions the project does not answer, or "none".

## Conventions and defaults

What to reuse first (detect the project's existing patterns), and the defaults when the project has none: component unit, file layout, styling system. Adding a dependency always goes through the grouped question.

## Layout

Design layout to framework mapping: flow and gap, padding, fill and fit sizing, fixed size, absolute position, alignment, fill, radius, clip, opacity, text growth.

## Typography

Font embedding (exact files, one per weight and style; a missing font is a blocker), size, numeric weight, style, line height (pen `lineHeight` is a multiplier of font size), letter spacing (pen percent × font size ÷ 100), alignment, anti-aliasing setting for capture.

## Strokes

Pen `strokeAlignment` `inner`, `center`, `outer`; per-side `strokeWidth`; dashes.

## Effects

Outer and inner shadow (pen has no spread); linear, radial, and angular gradients (pen `rotation` is degrees counter-clockwise from up); layer and background blur, blend modes. Anything unsupported: divergence record, never approximate.

## Tokens

Token file location, light and dark mechanism, key naming (pen variable name without `$`), how consumers reference themed and static values.

## Assets

Asset folder, image fill export, icon path data, reference syntax.

## Anchors

What an anchor is in this framework, how to set one on an element, and how the anchor path forms.

## Build and smoke

Incremental build command, smoke check, the exact failure strings to scan for, and the runtime scale probe (or "none: default 2").

## Capture

Backend, prerequisites (scaffolds and installs go through the grouped question), isolation of the target (harness), `commands.capture` example, fallback.

## Audit

Framework-specific accessibility checks for `qa`: accessible names, focus visuals, tab order, semantics.
