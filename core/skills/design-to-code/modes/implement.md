# Mode: implement

Deliver exact design values, reusable components, and a current design-code map. Optimize round trips and repeated work, never fidelity. Stay inside the requested frame or component and its dependencies. Design values are authoritative.

Flow: discover, survey, plan, implement batches, validate, report. **Review** skips implementation. **Update** starts from the map.

## 1. Discover

- Find the design source, target node, app project, existing tokens, the map, and `map.commands`. Inspect the workspace first; the OpenCode config directory is usually not the app project.
- Load the framework file (SKILL.md step 2) and `sources/pen.md`. Follow the source's Access steps.
- Resolve viewport, scale, and theme before the survey. Theme defaults to `light`; use `dark` only when the user names it. Scale: the current validation record's `scale`, else the framework file's runtime scale probe, else `2`. Re-export the reference only when a capture reports a different scale. Viewport defaults to the target's design width × height from `rows.txt`.
- Read project instructions, project files, and relevant views, styles, tokens, and view models. Load the framework's companion skill (named in its file) only for questions the project does not answer.
- Capture backend: `map.commands.capture` when set; otherwise follow the framework file's Capture section, and before the first capture persist the exact command that passed into `map.commands.capture` — with the `<id>`, `<dir>`, `<scale>`, and `<theme>` placeholders intact, never resolved values, or verification cannot substitute its own output directory (set `commands.launch` when a server must start; it is one runnable shell command from the project root, no annotations). Resume and independent verification re-run both as recorded. Put any scaffold, package, or tooling prerequisite in the one grouped question. On refusal, use the framework's fallback or exit `blocked` for the visual gate.

## 2. Survey once

Run the source's Survey. Record IDs, child order, geometry, sizing, gap, padding, text growth, visibility, typography, fill, stroke, opacity, radius, effects, references, overrides, and icon path data. Report unsupported geometry or missing fonts. Never approximate. Keep definitions and instance overrides separate. Before changing a shared component, inspect its other instances and callers.

## 3. Plan and map

- Reuse a matching component or style. One canonical implementation per explicit design component. A shared template for a subtree repeated 2+ times. A style or resource for a repeated visual-only primitive. A parent view for a one-off.
- Follow project conventions, then the framework file's defaults. Expose only real instance differences. Preserve accessibility.
- Apply the framework file's Layout, Typography, Strokes, Effects, Tokens, and Assets sections. Unsupported properties go in the component's `overrides` or a divergence record with a reason.
- Give every geometry-bearing mapped node an anchor as the framework's Anchors section defines.
- Batch order: tokens and assets, then components, then the parent frame.
- Map: read `references/map-schema.md` before the first map edit. Migrate old maps first. Generate `nodeMap` with `map-coverage.py`, then set `codeAnchor.anchor` on every geometry-bearing record. List token and global style files in `revisionFiles`. Set `codeRevision` from `map-revision.py`.

## 4. Implement batches

1. Before a batch's first edit, copy each existing file it will touch to `$TMPDIR/design-to-code-undo/<run>/<batch>/` and record files the batch creates in `created.txt` beside them. Undo restores the copies and deletes the created files, never through git.
2. Work from the cached survey and plan. Re-read only changed code or stale evidence.
3. One edit message: components, overrides, and parents with exact child order, instance counts, sizing, spacing, and visibility.
4. Review the diff for omissions, duplicates, unresolved resources, stray files, and map gaps. Update the map once.
5. One incremental build (framework file, Build). Fix build failures before dependent batches. When behavior or bindings change, run existing tests for the affected units.

Never build per primitive, re-survey per component, or restart per edit. Reuse a running app, dev server, or DevTools attachment.

## 5. Validate

Keep one finding queue keyed by anchor, category, and mismatch. Dispositions: fixed, design conflict, out of scope, blocked, deferred.

1. **Build and runtime:** the project builds. Once per change set, after the last code edit, run the framework's smoke check and scan its log for the framework's failure strings. A build alone never passes this gate.
2. **Visual:** read `references/capture-contract.md`, capture, then apply its pass rule. Store `threshold` and `captureMethod` in the validation record, and keep `map.commands.capture` (and `commands.launch` when needed) recording the exact command — a passing gate whose command is not in the map fails resume and verification.
3. **Mapping:** every scoped node is mapped or explained. Components are unique. Instance counts and overrides match. Anchors resolve (one `rg` pass). No unexplained orphaned or stale records.
4. **UI quality:** run `modes/qa.md` in **fidelity-locked** form on the changed surface.

| Loop | Budget |
|---|---|
| Tool failure | One corrected retry, then switch backend or report a blocker. Never repeat identical calls or poll stalled work. |
| Build or runtime | Two repair rounds per checkpoint, each with a specific cause and a changed fix. Same error signature: diagnose or exit `blocked`. |
| Visual and UI quality | Two rounds per target and change set, shared by visual and QA findings. Run QA before round two. Fidelity-locked QA uses this budget, not `maxIterations`: one QA iteration per repair round. |

A repair round is one edit, one build, one capture. Fix order: layout and spacing, typography, colors/borders/radius, then effects, icons, and clipping. Apply independent fixes together. Compare with the previous `pixel-diff.py` numbers. No measurable gain, oscillating fixes, or a spent budget ends repair. Undo any change that regresses fidelity.

## Branches

- **Design update:** re-survey. Diff `rows.txt` and jq-compare `full.txt` against the previous cache or map. Classify: definitions, overrides, tokens, geometry, visibility, additions, removals. Recompute shared definitions first. Validate changed targets and their consumers.
- **Code update:** keep design evidence while the revision matches. Update anchors and impact records.
- **Resume:** see `references/map-schema.md`, Resume.

## Report

- Framework; target; reused and new components; instance-count agreement; changed files; tokens and assets; map path and status counts.
- Build, tests, smoke check, `bounds-diff.py` and `pixel-diff.py` results with capture configuration (viewport, scale, theme, threshold, capture method); remaining mismatches and blockers. Flag machine-dependent captures.
- QA findings: applied, logged as design conflicts, or deferred, with reasons.
- Batches, builds, captures, repair rounds, and cache reuse.

`complete` requires faithful composition, matched instances and overrides, resolved resources, passing gates 1–4, a current map, and no unexplained unmapped, orphaned, or unrelated changes. Unresolved fidelity or any unlogged high or critical finding blocks `complete`. Findings with disposition `design conflict` do not block; list them under QA findings.
