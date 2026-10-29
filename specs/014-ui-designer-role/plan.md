# Implementation Plan: UI Designer Role

**Branch**: `014-ui-designer-role` | **Date**: 2026-10-28 | **Spec**: [spec.md](spec.md)

## Summary

Add write role `factory-ui-designer` (tier standard). `DESIGN.md` changes first. Then: one role prompt in `core/roles/`, one web framework reference, orchestrator routing by `[UI]` task marker, spec-builder plan/tasks duties (framework detection, text-only classification, whole-surface scope question, Figma `RESOLVE`), file-writing role list in the CLI, a drop regression test for design evidence (code only if a gap shows), render of all five harnesses, tests.

## Technical Context

**Language/Version**: Python 3 stdlib (CLI `core/skills/factory/bin/factory_cli`, `tools/render.py`); Markdown prompts/references
**Primary Dependencies**: none new
**Storage**: `state.json`, design context JSON, `docs/design-code-map.json`
**Testing**: `python3 -m unittest discover -s tools` (existing)
**Target Platform**: claude-code, opencode, codex, copilot, zcode adapters
**Project Type**: CLI + agent prompt distribution
**Performance Goals**: none beyond existing budgets; role-generic budget default 300 s applies unchanged
**Constraints**: harness-neutral core (verbs only); committed `dist/` equals fresh render; old `state.json` resumes unchanged (optional fields only, no schema version)
**Scale/Scope**: 1 new role, 1 new reference, edits to ~8 existing core files

## Constitution Check

- I Design First: Pass — `DESIGN.md` edit is task 1 (FR-001).
- II Harness-Neutral Core: Pass — role uses `SPAWN`/`RESOLVE`/`SHELL` only; a test asserts no harness tool names.
- III Generated Dist: Pass — every core/adapter task ends with render of all harnesses and `git status --porcelain -- dist/` empty.
- IV Stateless Agents: Pass — resume reads committed batches, map, design context; `ui-agent` pass recorded in design context.
- V Simplicity and Reuse: Pass — reuses mapping contract, Avalonia reference, gates, fix rounds; new items justified below.

Post-design re-check: Pass, no violations.

## Project Structure

```text
DESIGN.md, CONTEXT.md, README.md
core/roles/ui-designer.md                       (new)
core/roles/spec-builder.md                      (plan/tasks duties)
core/skills/factory/SKILL.md                    (implement routing, Figma RESOLVE)
core/skills/factory/references/design-code-mapping.md        (source kinds, text-only gates)
core/skills/factory/references/design-code-mapping-web.md    (new)
core/skills/factory/references/state.md, protocol.md         (role lists, optional fields)
core/skills/factory/bin/factory_cli/state.py    (file-writing roles); commands.py only if drop gap
(adapters do not list roles; render discovers core/roles/)
dist/        (rendered)
tools/tests/test_render_models.py, test_state.py, test_drop.py
```

## New items

- `core/roles/ui-designer.md` - file - FR-002 needs one role prompt; distinct state machine from `code-build`.
- `core/skills/factory/references/design-code-mapping-web.md` - file - FR-010 web framework reference; Avalonia one reused.
- `factory-ui-designer` agent - abstraction - new role, reason recorded in `DESIGN.md` (FR-001).
- `[UI]` task marker - abstraction - FR-006 routing key; no new route/verb.
- Optional design-context fields (`source_kind`, `framework`, `scope` with nested `target` or `accepted_files`/`excluded`, `ui_agent_pass`) - abstraction - FR-005/009/018/024 persistence outside relay.
- Dependencies: none.

## Quality constraints

- Security: no install of missing capabilities (FR-008); paths from design context are repo-relative.
- Integrity: never claim a gate without current evidence (FR-023); protected scope questions (FR-017/018).
- Compatibility: pre-feature runs resume on `code-build` (FR-028); non-design runs unchanged (SC-007).
- Resource limits: existing deadline/partial handling extended to the role (FR-027).
- Verification: existing unittest suite plus render drift gate.
- Fixture-run criteria (SC-001, SC-002, SC-003, SC-004, SC-005, SC-007) describe behaviour carried by exempt prompt text. They are verified by prompt review, not automated runs: T013 checks the US4 statements, and T016 checks that each criterion traces to a stated rule in `ui-designer.md`, `spec-builder.md`, `SKILL.md` or `design-code-mapping.md`. Live fixture trials are out of scope; SC-006 stays automated.

## Test seams

- `PARTIAL_RETURN_ROLES` / file-writing role check in `factory_cli.state` — `ui-designer` accepted as file-writing role returning `partial` with `overrun`; failure path: `partial` from a non-file-writing role still rejected (`tools/tests/test_state.py`).
- `render.py <harness>` agent output — every harness renders `factory-ui-designer` with tier standard and write access; core role file names no harness tool; failure path: none (`tools/tests/test_render_models.py`).
- `factory drop` design rehome — drop already moves the whole `factory/design/` folder (`commands.py` drop); regression test that Figma/image evidence files there move to `docs/design/<branch>/` with map references rewritten; failure paths: missing evidence file, `../` traversal evidence reference, and symlink inside `factory/design/` pointing outside it; each reports the reference, leaves the map unchanged and does not move `factory/` (`tools/tests/test_drop.py`).

Exempt: DESIGN.md, CONTEXT.md, README.md, core/roles/*.md, core/skills/factory/SKILL.md, core/skills/factory/references/*.md - documentation/prompt text only; rendered presence covered by the render seam
Exempt: dist/ - generated output; covered by the drift gate
Overridden: none

Not a seam: time-budget lookup is role-generic and defaults to 300 s; no change (Q1).

Confirmed: 2026-10-29 - Q3 accepted - seams: `PARTIAL_RETURN_ROLES` / file-writing role check in `factory_cli.state`; `render.py <harness>` agent output; `factory drop` design rehome; failure paths: `PARTIAL_RETURN_ROLES` -> `partial` from a non-file-writing role still rejected; `render.py <harness>` -> none; `factory drop` -> missing evidence file, `../` traversal evidence reference, and symlink inside `factory/design/` pointing outside it; each reports the reference, leaves the map unchanged and does not move `factory/`.

## Complexity Tracking

None.
