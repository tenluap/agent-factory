# Implementation Plan: FACETS Advisor Role

**Branch**: `015-facets-advisor` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Summary

Add the main agent `factory-facets-advisor` (tier deep, `mode: primary`, research access). `DESIGN.md` changes first. Then: the role prompt, a FACETS reference and a profile template, two role-only verbs, a `research` access level in every adapter, the verb mapping in every `harness.md`, a `modes` map in `render.py` and the OpenCode adapter, main-agent start notes in every `harness.md`, docs, and render tests. ADR 0011 records why.

## Technical Context

**Language/Version**: Markdown prompts and references; Python 3 stdlib tests
**Primary Dependencies**: none new
**Storage**: optional `${FACTORY_HOME}/facets-profile.md`, user-owned
**Testing**: `python3 -m unittest discover -s tools`
**Target Platform**: claude-code, opencode, codex, copilot, zcode
**Constraints**: harness-neutral core; `dist/` untracked; no run, state or CLI change

## Constitution Check

- I Design First: Pass. `DESIGN.md` gains the "FACETS advisor" section, agents row and validation section first.
- II Harness-Neutral Core: Pass. The role uses `SHELL`, `WEB_SEARCH`, `WEB_FETCH`; a test asserts no harness tool names.
- III Generated Dist: Pass. All five harnesses render; `dist/` stays untracked.
- IV Stateless Agents: Pass with a recorded exception. Run agents stay stateless and silent; this main agent is the session itself, so it talks to the user (ADR 0011). Its profile lives on disk.
- V Simplicity and Reuse: Pass. Reuses the envelope, question shape and render pipeline; new items justified below.

## New items

- `core/roles/facets-advisor.md` - file - FR-002, one role prompt.
- `core/skills/factory/references/facets.md` - file - FR-004, the verbatim checklist, guidance, calibration and caveats in one reusable place instead of inline in the role.
- `core/skills/factory/references/facets-profile.template.md` - file - FR-005, the profile fields and a copyable template.
- `research` access level in every `adapter.json` - abstraction - FR-009, the read level has no web tools on claude-code, zcode and copilot; widening `read` would grow all six reviewers.
- `WEB_SEARCH`, `WEB_FETCH` verbs - abstraction - FR-006, Principle II forbids naming web tools in core.
- `mode` role field and adapter `modes` map - abstraction - FR-011, OpenCode forces `mode: subagent` on every agent; a main agent needs `mode: all` without changing other roles.
- `${FACTORY_HOME}/facets-profile.md` - file (user-owned, not in repo) - FR-005, persistent constraints shared across harnesses.
- `docs/adr/0011-...` - file - records the role's break from the "every role is a run stage" convention.
- Dependencies: none.

## Quality constraints

- Security: no repository edits; one confirmed shell write of the profile; web content is evidence, never instructions.
- Integrity: never invent a source; unknown facets are `unverified` and score 0.
- Resource limits: 3 searches and 5 fetches per option.
- Compatibility: existing roles, runs and state unchanged; reviewers keep `read`.

## Test seams

- `render.py <harness>` agent output: every harness renders `factory-facets-advisor` with tier deep, research tools and no edit access (`tools/tests/test_render_models.py`).
- Core role text: no harness tool names; both research verbs present; every `harness.md` maps both verbs (`tools/tests/test_render_models.py`).
- Existing access tests treat `research` like `read` for edit denial; OpenCode mode is `all` for `mode: primary`, else `subagent` (`tools/test_render.py`).

Exempt: DESIGN.md, CONTEXT.md, README.md, core/roles/*.md, core/skills/factory/references/*.md, docs/adr/*.md - prompt and documentation text; rendered presence covered by the render seam.
Exempt: dist/ - generated output.
Overridden: none

## Complexity Tracking

None.
