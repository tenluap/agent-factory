# Tasks: UI Designer Role

**Input**: Design documents from `specs/014-ui-designer-role/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Required (overrides the SpecKit "Tests are OPTIONAL" rule). Each behaviour-changing task is one checkbox and one commit unit: (1) write the failing test, run it, observe red; (2) implement the smallest change; (3) run the passing check. Commit test, implementation, rendered `dist/` and the task checkbox together, with the `Red:` line from engineering.md "Red proof" in the commit body. Plan-exempt tasks carry their exemption and no `Red:` line. Test runner: `python3 -m unittest discover -s tools` (existing).

**Render rule (constitution III)**: every task that changes `core/` runs the build `export FACTORY_HOME="$(mktemp -d)"; for h in claude-code opencode codex copilot zcode; do python3 tools/render.py "$h" || exit 1; done` and commits the rendered `dist/` in the same commit; `test -z "$(git status --porcelain -- dist/)"` passes after that commit.

**Harness-neutral rule (constitution II)**: `core/` text uses only `SPAWN`, `SPAWN_PARALLEL`, `ASK`, `NOTIFY`, `RESOLVE`, `SHELL`; it names no harness tool, path or command.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: user story (US1..US5)

Seams (plan.md "Test seams", confirmed 2026-10-29 Q1):

- **S1** `PARTIAL_RETURN_ROLES` / file-writing role check in `factory_cli.state`; failure path: `partial` from a non-file-writing role still rejected.
- **S2** `render.py <harness>` agent output; failure path: none.
- **S3** `factory drop` design rehome; failure path: map reference to a missing evidence file reported, map left unchanged.

## Phase 1: Setup (design first)

- [X] T001 Update `DESIGN.md` before any `core/` or `adapters/` change (constitution I, FR-001): add `factory-ui-designer` (tier standard, access write) to the Agents table; add it to the Flow and the Implement decisions (route by `[UI]` task marker: `ui-designer` for `[UI]` tasks, `code-build` for the rest, `tasks.md` order kept); add a routing-contract row for UI design work; replace the sentence "No new agent role, harness verb, second map, or repair loop is introduced." in "Pen design references" (line ~116) with the deliberate decision (one new write role; still no new verb, second map or repair loop) and its reason (design-to-code has its own state machine: discover, survey, plan components, implement batches, validate); add `ui-designer` to "the file-writing roles (spec-builder, code-build, fixer)" in "Deadline stop" (line ~259) and change "all three file-writing roles" to "all file-writing roles". Exempt: DESIGN.md - documentation only
- [X] T002 Check `CONTEXT.md` "UI design" (line ~159) defines UI design run, UI design task, design source, framework reference, UI scope and dependency batch exactly as spec.md uses them; add any missing term in place. Exempt: CONTEXT.md - documentation only

---

## Phase 2: Foundational (file-writing role list)

**Purpose**: the CLI must accept `partial` returns from `ui-designer` before the role can stop at a deadline (FR-004, FR-027).

- [ ] T003 Seam S1 commit unit. (1) Failing test in `tools/tests/test_state.py`, next to `test_partial_return_refused_on_never_stopped_roles`: `test_partial_return_accepted_for_ui_designer` builds a state whose `issues[0]` is `{ "kind": "overrun", "role": "ui-designer", "cause": "other", "partial_return": true, ... }` and asserts validation reports no `issues[0].partial_return` error; required failure path `test_partial_return_still_refused_for_non_file_writing_role` asserts the same record with role `code-standards` still reports `issues[0].partial_return`. Run `python3 -m unittest tools.tests.test_state`; observe the accept test red. (2) Implement: add `"ui-designer"` to `PARTIAL_RETURN_ROLES` in `core/skills/factory/bin/factory_cli/state.py` (line 63, single source of truth, ENG-6); update the role names in the error messages in `state.py` (line ~352) and `core/skills/factory/bin/factory_cli/commands.py` (lines ~912 and ~1006) to "spec-builder, code-build, ui-designer, fixer"; keep the substring "of the file-writing roles" asserted in `tools/tests/test_issues.py`. (3) Pass: `python3 -m unittest discover -s tools` green; render rule. Red proof: `Red: test_partial_return_accepted_for_ui_designer failed as expected`. Done when: `ui-designer` partial is accepted and `code-standards` partial is still rejected.
- [ ] T004 Add `ui-designer` to the file-writing role lists in `core/skills/factory/references/state.md` (`issues` record, line ~107; `issue-add` text, line ~147) and `core/skills/factory/references/protocol.md` (`partial` status, line 19); add the optional design-context fields `source_kind`, `framework`, `scope` (nested `target` or `accepted_files`/`excluded`), `ui_agent_pass` from data-model.md to the design-context description, marked optional with no schema version (FR-028); render rule. Exempt: core/skills/factory/references/*.md - documentation/prompt text only; rendered presence covered by the render seam

**Checkpoint**: S1 green; reference lists match `PARTIAL_RETURN_ROLES`.

---

## Phase 3: User Story 1 - Implement one screen from a Pen design (P1) MVP

**Goal**: in implement, `[UI]` tasks spawn `factory-ui-designer`, which edits only the target and its component dependencies and reports actual gate evidence.

**Independent Test**: fixture run with one Pen frame and one named view: role spawned in implement, only the target and its dependency components edited, every scoped node has a map record, envelope `design` field references actual evidence.

- [ ] T005 [US1] Seam S2 commit unit. (1) Failing test in `tools/tests/test_render_models.py`: `test_ui_designer_renders_for_every_harness` renders each of claude-code, opencode, codex, copilot, zcode and asserts the `factory-ui-designer` agent file exists with tier standard and write access (claude-code `tools:` line contains `Edit` and `Write`, as `test_write_roles_keep_edit_access` checks); `test_ui_designer_core_role_names_no_harness_tool` reads `core/roles/ui-designer.md` and asserts it contains none of the harness tool names the adapters map the neutral verbs to (read the list from `adapters/*/adapter.json`, not a hard-coded list) and no `adapters/` or `dist/` path. Failure path: none (plan S2). Observe red (file absent). (2) Implement `core/roles/ui-designer.md` with the metadata shape of `core/roles/code-build.md` (`name: ui-designer`, tier standard, access write) and these sections: Inputs (FR-007: worktree, branch, spec_dir, `speckit-implement`, `ponytail`, `tdd`, commands, deadline, design context reference, source kind, scope, resolved `pen-design` or `figma` path); Work as the state machine discover → survey once → plan canonical components and mapping → implement dependency batches → validate → report (FR-020); re-verify the recorded `framework` against project files before any edit and return `failed` naming both values on mismatch (FR-009, US4 scenario 3); load exactly one framework reference: `design-code-mapping-avalonia.md` or `design-code-mapping-web.md` (FR-010); Pen source authoritative under `design-code-mapping.md` (FR-012); named-target scope: edit only the target and its component dependencies, inspect other callers of a shared component first, and return a `requires_user: true` scope question instead of changing callers beyond the request (FR-016, FR-017); a missing or non-UI target returns a `requires_user: true` question naming the closest candidates; reuse `docs/design-code-map.json` and existing build/runtime, mapping and fidelity gates, no second map or gate (FR-021); stale map records when the source changed since survey, refresh only affected scope; removed design elements recorded, behaviour kept; follow `engineering.md` commit units and plan seams, one batch per commit unit, never invent a seam (FR-022); time budget per protocol.md "Verification handoff": check time between batches, finish the batch in flight past the deadline, commit, return `partial` with `overrun` (FR-027); resume from committed batches, the map and the design context (FR-028); capture unavailable keeps fidelity unverified; Done: standard envelope with the optional `design` field referencing actual context, map and evidence paths and no gate claimed without current evidence (FR-023). (3) Pass: full suite green; render rule (FR-003). Red proof: `Red: test_ui_designer_renders_for_every_harness failed as expected`. Done when: all five harness renders contain `factory-ui-designer` with tier standard and write access, and the core role names no harness tool.
- [ ] T006 [US1] Edit `core/skills/factory/SKILL.md` implement step (FR-005, FR-006, FR-007): a UI design run is one whose saved design context records a design source (Pen, Figma, image, text) and UI targets or whole-surface scope; on such a run route each task by its `[UI]` marker only (`SPAWN` `factory-ui-designer` for `[UI]` tasks, `code-build` for the rest, `tasks.md` order kept; one spawn per contiguous run of `[UI]` tasks, resuming from checkboxes); pass the FR-007 inputs; add `ui-designer` to the "Time budget" file-writing role list; non-design runs and runs whose `state.json` predates this feature keep today's `code-build` flow (FR-028, SC-007); no new route, stage name or verb; render rule. Exempt: core/skills/factory/SKILL.md - documentation/prompt text only; rendered presence covered by the render seam
- [ ] T007 [US1] Edit `core/roles/spec-builder.md` plan duty for UI design runs (FR-009, FR-011): detect the UI framework from project files at plan and record `framework` in the design context; supported: `avalonia`, `web`; no supported framework returns `failed` naming the detected framework (or "none detected") and the supported list, before tasks; several candidates for an ambiguous target return a `requires_user: true` question naming them; never guess. Tasks duty: mark each UI design task `[UI]`; with a named target, write `[UI]` tasks for the target and its component dependencies. Render rule. Exempt: core/roles/*.md - documentation/prompt text only; rendered presence covered by the render seam
- [ ] T008 [P] [US1] Create `core/skills/factory/references/design-code-mapping-web.md` (FR-010), shaped like `design-code-mapping-avalonia.md`: detection signals (HTML/CSS, `package.json` with React/TSX, Vue, Svelte), canonical component and token locations, launch/capture configuration for fidelity, build/runtime gate commands taken from the repository; render rule. Exempt: core/skills/factory/references/*.md - documentation/prompt text only; rendered presence covered by the render seam

**Checkpoint**: MVP: a Pen + named-target run routes `[UI]` tasks to the rendered role.

---

## Phase 4: User Story 2 - Restyle the whole UI surface (P2)

**Goal**: no named target → plan enumerates the whole UI surface, user confirms it (protected), tasks batch only accepted files.

**Independent Test**: fixture with three views and two shared components, no target: scope relayed as `requires_user: true`, fast mode leaves it unanswered, accepted tasks follow dependency-batch order.

- [ ] T009 [US2] Edit `core/roles/spec-builder.md` (FR-018, FR-019): with no named target, the plan enumerates the whole UI surface (views and components) in `plan.md` and returns one `requires_user: true` question carrying the file list; record the accepted list and excluded files in the design context `scope` (`{ "kind": "surface", "accepted_files": [...], "excluded": [...] }`), outside `relay`; the tasks stage writes `[UI]` dependency batches for accepted files only, in order tokens and assets, shared components, views; excluded files are recorded out of scope. Add to `core/roles/ui-designer.md` that whole-surface scope edits only `accepted_files`. Render rule. Exempt: core/roles/*.md - documentation/prompt text only; rendered presence covered by the render seam

---

## Phase 5: User Story 3 - Other design sources (P2)

**Goal**: Figma, image and text-only sources work on the same flow with gates by source kind.

**Independent Test**: three trials (Figma present, image, text-only): recorded `source_kind`, presence or absence of node mapping, and required gates per kind.

- [ ] T010 [US3] Edit `core/skills/factory/references/design-code-mapping.md` (FR-012..FR-015): add source kinds `pen | figma | image | text` with authority (Figma mapped by node like Pen; image is a visual reference only, no node records, fidelity judged against the image, reference recorded in the design context; text-only keeps existing code as baseline, uses `impeccable` guidance, needs no map records, requires build/runtime evidence, records mapping and fidelity `not_applicable` with reason "no design reference", attaches a before/after capture when capture is available). Render rule. Exempt: core/skills/factory/references/*.md - documentation/prompt text only; rendered presence covered by the render seam
- [ ] T011 [US3] Edit `core/skills/factory/SKILL.md` (FR-008): only when a Figma source is recorded, `RESOLVE` a `figma` skill or MCP capability at plan; absent → block before tasks with setup guidance, install nothing; re-`RESOLVE` at implement before `SPAWN` of the role. Edit `core/roles/spec-builder.md` (FR-005): classify text-only at plan only for a purely visual change with no behaviour change and record `source_kind: text`; an ambiguous brief gets one ordinary relay question; mixed work stays on `code-build`. Edit `core/roles/ui-designer.md`: per-source handling referencing `design-code-mapping.md` source kinds. Render rule. Exempt: core/skills/factory/SKILL.md, core/roles/*.md - documentation/prompt text only; rendered presence covered by the render seam
- [ ] T012 [US3] Seam S3 commit unit (FR-030). (1) Tests in `tools/tests/test_drop.py`, beside `test_design_evidence_moves_and_rewrites_map_in_drop_commit`: `test_figma_and_image_evidence_move_and_map_rewritten` puts a Figma evidence file and an image reference under `<spec_dir>/factory/design/`, references both in `docs/design-code-map.json`, runs drop, and asserts both files are under `docs/design/<branch>/` and the map references are rewritten (regression, expected green); required failure path `test_drop_reports_missing_evidence_and_leaves_map_unchanged` references a file under `factory/design/` that does not exist, runs drop, and asserts a non-zero exit naming the missing path, the map bytes unchanged and the run folder not moved. Run `python3 -m unittest tools.tests.test_drop`. (2) Implement only if the failure-path test is red: in `cmd_drop` in `core/skills/factory/bin/factory_cli/commands.py` (line ~438, where the map is read), before any move, check every map reference starting with `"{folder}/design/` resolves to an existing file and `die` naming the first missing path. (3) Pass: full suite green; render rule. Red proof: `Red: test_drop_reports_missing_evidence_and_leaves_map_unchanged failed as expected`, or, if it passes before any code change, `Red: not applicable - test_drop_reports_missing_evidence_and_leaves_map_unchanged already covers this` with no code change. Done when: both tests pass and the map is unchanged on missing evidence.

---

## Phase 6: User Story 4 - Unsupported framework (P3)

**Goal**: unsupported or ambiguous frameworks stop before any UI edit.

**Independent Test**: fixture with only Qt: plan reports it unsupported, run stops before tasks, 0 UI files edited.

- [ ] T013 [US4] Verify `core/roles/spec-builder.md` (T007) and `core/roles/ui-designer.md` (T005) state all three US4 scenarios (unsupported → `failed` before tasks; ambiguous → protected question; implement mismatch → `failed`, no edit) and that `core/skills/factory/SKILL.md` stops the run before tasks on a plan `failed` for unsupported framework; fill gaps in place; render rule. Exempt: core/roles/*.md, core/skills/factory/SKILL.md - documentation/prompt text only; rendered presence covered by the render seam

---

## Phase 7: User Story 5 - Quality pass and shared repair budget (P3)

**Goal**: one `ui-agent` pass per run; remaining findings share the existing two fix rounds.

**Independent Test**: ledger and state show `ui-agent` at most once per run, also across resumes; `review.fix_rounds` ≤ 2.

- [ ] T014 [US5] Edit `core/roles/ui-designer.md` (FR-024, FR-025, FR-026): only the spawn completing the last `[UI]` task (none unchecked remain in `tasks.md`), after its gates pass, runs `ui-agent` once over the whole changed UI surface (no internal second iteration), first checking `ui_agent_pass` in the design context and skipping when set; record `ui_agent_pass` `{ "at", "applied", "skipped", "deferred" }`; design-sourced values win over conflicting recommendations, recorded as skipped with reason; `ui-agent` or `impeccable` unavailable → skip disclosed, required gates still apply; remaining findings go to review, judge and fixer with the existing two fix rounds; no second repair loop. Render rule. Exempt: core/roles/*.md - documentation/prompt text only; rendered presence covered by the render seam

---

## Phase 8: Polish & cross-cutting

- [ ] T015 [P] Update `README.md` role list and role count to include `ui-designer` (FR-004). Exempt: README.md - documentation only
- [ ] T016 Final verification: run the build, then `test -z "$(git status --porcelain -- dist/)"` (SC-006), then `python3 -m unittest discover -s tools`; grep each `dist/<harness>/` for `factory-ui-designer` (quickstart step 4); trace SC-001..SC-005 and SC-007 to stated prompt rules (plan "Quality constraints"). Commit nothing new if all pass; a failure reopens the owning task. Exempt: dist/ - generated output; covered by the drift gate

---

## Dependencies

- T001 → everything (constitution I). T002 after T001.
- T003, T004 (Phase 2) before Phase 3.
- T005 before T006, T007, T009, T011, T013, T014 (role file exists). T008 [P] with T006/T007 after T005.
- T009 after T007 (same file). T010 before T011. T012 independent of T009..T011 after Phase 2.
- T013 after T005, T007, T011. T014 after T005. T015 [P] after T001. T016 last.

## Implementation strategy

MVP = Phases 1-3 (T001-T008): Pen + named target end to end. Then US2 (T009), US3 (T010-T012), US4 (T013), US5 (T014), polish (T015-T016). Each phase ends with a green suite and zero `dist/` drift.

New files and their reasons: plan.md "New items".
