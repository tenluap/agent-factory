---

description: "Task list for Factory skill routing"
---

# Tasks: Factory skill routing

**Input**: Design documents from `/specs/005-skill-routing/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [quickstart.md](./quickstart.md)

**Tests**: this feature is an instruction set. The plan lists three machine-checkable seams (render gate, link integrity, state/question contract) and exempts every Markdown and generated file as documentation or configuration only. Each exempt task below carries its plan exemption verbatim instead of a test task; the seam checks are run red first in Phase 2 and green in the final phase. Exact commands: [quickstart.md](./quickstart.md).

**Test runner**: not introduced - `state.commands` already documents build and test (plan, Technical Context).

**Render discipline**: every task that edits `core/` finishes with the canonical render of all five harnesses (quickstart, Seam 1) so `dist/` is committed in the same commit as its source (Constitution III, ENG-3: one commit per task, test and implementation together).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependencies)
- **[Story]**: US1-US5 from spec.md

---

## Phase 1: Setup

- [ ] T001 Export `$CANON` from [quickstart.md](./quickstart.md), confirm `git status --porcelain -- dist/` is empty, and create a throwaway `FACTORY_HOME` under `$SCRATCH` for the Seam 3 fixtures (never under the repository). `Exempt: setup/environment steps - configuration only - no product file changes.`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: prove the seams red, then land the design record and the shared reference every later task links to.

**⚠️ No user story work may begin until T005 is complete.**

- [ ] T002 [Seam 2] Run the relative-link assertion from [quickstart.md](./quickstart.md) §Seam 2 and record the red result: `references/skills.md` does not exist and `core/skills/factory/SKILL.md`, `core/roles/code-build.md`, `core/roles/fixer.md` do not link it (FR-026, SC-010).
- [ ] T003 [Seam 3] Write the three throwaway pending fixtures and run the contract assertion from [quickstart.md](./quickstart.md) §Seam 3; record the red result: the version 1 and version 2 fixtures digest and `stage: "brainstorm"` plus `requires_user: true` pass through `core/skills/factory/bin/factory show` verbatim, while `core/skills/factory/references/state.md` and `references/protocol.md` do not yet document them (FR-006, FR-017, SC-008).
- [ ] T004 Update `DESIGN.md` **first** (Constitution I) with the routing contract (intake intent → first stage) including two or three example cue phrases per intent so classification is repeatable, skill resolution and precedence, the protected confirmations, the widened UI-change classes and the validation plan covering the three seams plus the agent-driven manual checks (FR-001, FR-026, FR-027, SC-001, SC-010). `Exempt: DESIGN.md - documentation only - the design record.`
- [ ] T005 Create `core/skills/factory/references/skills.md`: logical skill names and `RESOLVE`-only lookup, required vs conditional skills, precedence (`engineering.md` wins; refactor-while-green stated), bounded application inside the approved spec, companion references resolved from the skill's own directory, missing-skill stop-and-report. Keep it under 60 lines and restate no `ENG-n` rule (ENG-6, ENG-10, Constitution V). `Exempt: core/skills/factory/references/skills.md - documentation only - agent instructions; Seam 2 proves it exists and is linked, Seam 1 that it ships.`

---

## Phase 3: User Story 1 - An idea is explored before it becomes a feature (Priority: P1) 🎯 MVP

**Goal**: intake classifies exploration vs delivery, the idea path runs a resumable `brainstorm` stage, and the feature path is untouched.

**Independent Test**: three intake trials (exploration wording, delivery wording, ambiguous) take the right path and only the ambiguous one asks a single question; stop after exploration and resume ([quickstart.md](./quickstart.md) manual checks 1, 2, 6).

- [ ] T006 [US1] In `core/skills/factory/SKILL.md`: add intake classification at step 0 per [data-model.md](./data-model.md) ("Intake intent"), exactly one intent relay question when ambiguous and no new flag, the `brainstorm` stage before `grill` on the idea path, conditional `RESOLVE` of `brainstorming` only on that path with stop-and-report when missing, pending-storage-only artifacts that move into the worktree, and `grill` treating the brief's settled decisions as inputs (FR-001..FR-005, FR-007, FR-008, FR-011, FR-027). `Exempt: core/skills/factory/SKILL.md - documentation only - orchestrator instructions.`
- [ ] T007 [US1] In `core/skills/factory/references/state.md`: add `brainstorm` to the stage vocabulary before `grill`, its pending-state and `brief.md` handling, and its resume path into `grill`, keeping every existing stage value and saved run readable (FR-006, SC-008). `Exempt: core/skills/factory/references/state.md - documentation only - schema prose; its new vocabulary is asserted by Seam 3.`

**Checkpoint**: the Seam 3 stage half is green; US1 is independently testable via the manual intake trials.

---

## Phase 4: User Story 2 - Implementation and repair follow a code-craft method (Priority: P2)

**Goal**: every fresh code-writing and fixing turn receives and reads `ponytail` and `tdd` alongside the engineering rules.

**Independent Test**: inspect a code-writing and a fixing turn's inputs for both resolved absolute paths, then remove one skill and confirm the affected work stops with setup guidance ([quickstart.md](./quickstart.md) manual check 4).

- [ ] T008 [US2] In `core/skills/factory/SKILL.md`: resolve `ponytail` and `tdd` at preflight before a code-delivery run commits, record them in `state.skills`, pass their absolute paths plus `references/skills.md` into every `code-build` and `fixer` spawn, re-resolve unresolved names and all paths when `harness` changed on resume, and stop the affected work with setup guidance when either is missing (FR-009, FR-010, FR-011). `Exempt: core/skills/factory/SKILL.md - documentation only - orchestrator instructions.`
- [ ] T009 [US2] In `core/roles/code-build.md`: read the two skill paths and link `references/skills.md`; state that guidance applies inside the approved spec and removes no requirement, security control, accessibility behaviour, planned test, repository tooling or `ENG-n` evidence and never replaces the result envelope; `engineering.md` wins the refactor-while-green conflict; seams come from the plan's list only, never the confirmation line, and an unlisted seam is `ENG-4` stop-and-report with no question to the user; `ENG-2`, `ENG-3`, `ENG-5` and the missing-runner policy still apply after a handover (FR-012..FR-015, FR-019). `Exempt: core/roles/code-build.md - documentation only - role instructions.`
- [ ] T010 [US2] Apply the same additions to `core/roles/fixer.md`, including that a fixing turn needing an unlisted seam fails identically and that UI fixes are carried out here, not in the read-only review role (FR-013..FR-015, FR-019, FR-024). `Exempt: core/roles/fixer.md - documentation only - role instructions.`

**Checkpoint**: the Seam 2 linker half is green (all three files link the reference); US1 and US2 both work independently.

---

## Phase 5: User Story 3 - The user confirms test seams even in fast mode (Priority: P3)

**Goal**: the plan's seams reach the user as a protected question that fast mode never answers.

**Independent Test**: with fast mode on the seam question is shown and waited on; resume with unchanged seams does not re-ask it, a changed seam list does ([quickstart.md](./quickstart.md) manual check 3).

- [ ] T011 [P] [US3] In `core/skills/factory/references/protocol.md`: document the optional `requires_user` boolean in the question shape (absent = today's behaviour), state that fast mode must never auto-answer it and that its answer never carries `"auto": true`, alongside the unchanged `pending_clarify` exclusion (FR-017, FR-027). `Exempt: core/skills/factory/references/protocol.md - documentation only - protocol prose; its new field is asserted by Seam 3.`
- [ ] T012 [P] [US3] In `core/skills/factory/references/state.md`: add `requires_user` to the relay/fast-mode step as a question fast mode must skip, keeping questions saved without the field unchanged (FR-017, SC-008). `Exempt: core/skills/factory/references/state.md - documentation only - schema prose; its new vocabulary is asserted by Seam 3.`
- [ ] T013 [US3] In `core/roles/spec-builder.md`: at the end of `plan`, relay the plan's proposed public seams as one `requires_user` question before implementation, persist the `Confirmed: <date> - <Qid> accepted - seams: ...` line in `plan.md`'s "Test seams" section, reuse it only while the seam names and scope match, require a new decision when they change, and skip the question when every part is exempt (FR-016, FR-018, FR-027). `Exempt: core/roles/spec-builder.md - documentation only - role instructions.`

**Checkpoint**: Seam 3 is fully green; US1-US3 work independently.

---

## Phase 6: User Story 4 - UI changes get a disciplined UI evaluation (Priority: P4)

**Goal**: widened UI detection, an audit-and-critique UI review that stays read-only and discloses its evidence, and a distinct UX lens.

**Independent Test**: four diffs (design tokens, a locale string, user-visible copy in UI code, backend only) classify correctly and the UI review makes zero edits ([quickstart.md](./quickstart.md) manual check 5).

- [ ] T014 [US4] In `core/skills/factory/SKILL.md`: widen UI-change detection over `git diff <base>...HEAD` to the classes in [data-model.md](./data-model.md) ("UI change signal") including user-visible copy in UI code, skip the UI passes with no user-visible surface, `RESOLVE` `impeccable` only on a UI diff through the existing install offer, record `review.ui_diff` / `review.ui_reviewer_skipped` as today, and disclose a skipped or evidence-limited UI evaluation at the approval gate (FR-008, FR-020, FR-025, FR-027). `Exempt: core/skills/factory/SKILL.md - documentation only - orchestrator instructions.`
- [ ] T015 [P] [US4] In `core/roles/ui-reviewer.md`: follow `impeccable`'s audit-and-critique route with its setup run once in the reviewer's context and the applicable platform references resolved from the skill's own directory, stay read-only, keep the existing machine-readable findings shape and review/fix limits, prefer rendered evidence across relevant viewports, states, themes and interactions, and state whether the evidence was rendered or static without describing static inspection as an observed interaction; fixes go to `fixer` (FR-012, FR-021, FR-022, FR-024, FR-027). `Exempt: core/roles/ui-reviewer.md - documentation only - role instructions.`
- [ ] T016 [P] [US4] In `core/roles/ux-reviewer.md`: state the complementary lens that runs alongside the UI review rather than repeating it (FR-023, FR-027). `Exempt: core/roles/ux-reviewer.md - documentation only - role instructions.`

**Checkpoint**: US1-US4 work independently.

---

## Phase 7: User Story 5 - One consistent account of the routing (Priority: P5)

**Goal**: records and user-facing documents agree with the sources, and every harness distribution carries them identically.

**Independent Test**: read `DESIGN.md` and the shared reference for the routing rules, then render every harness and confirm the distributions match their sources.

- [ ] T017 [P] [US5] Revise `docs/adr/0001-factory-owns-its-engineering-rules.md` in place: the external test-driven skill now contributes testing technique under explicit factory orchestration, with `engineering.md` keeping precedence (FR-028). `Exempt: docs/adr/0001-factory-owns-its-engineering-rules.md - documentation only.`
- [ ] T018 [P] [US5] In `README.md` and `docs/product-brief.md`: separate required prerequisites (`speckit-*`, `grilling`, `domain-modeling`, `pr`, `ponytail`, `tdd`) from conditionally resolved skills (`brainstorming`, `impeccable`) (FR-028). `Exempt: README.md - documentation only.` `Exempt: docs/product-brief.md - documentation only.`
- [ ] T019 [P] [US5] In `CONTEXT.md`: add the glossary terms from [data-model.md](./data-model.md) - intake intent, brainstorm stage, skill map entry, protected question, seam confirmation, UI change signal, shared integration reference (FR-026). `Exempt: CONTEXT.md - documentation only.`
- [ ] T020 [US5] Final render gate and scope check (each earlier `core/` task already rendered per Render discipline): run the canonical render with `$CANON` once more, confirm the gate `test -z "$(git status --porcelain -- dist/)"` is clean across all five harnesses, and confirm no adapter-specific model setting changed (FR-029, SC-009). `Exempt: dist/** - generated output for all five harnesses, produced by the canonical render and guarded by Seam 1, never hand-written.`

---

## Phase 8: Polish & Verification

- [ ] T021 [Seam 1] [Seam 2] [Seam 3] Re-run all three seam checks from [quickstart.md](./quickstart.md) green: the render gate, `links ok`, and `contract ok` with no `FAIL` line; spot-check that `references/skills.md` is byte-identical in every `dist/<harness>/skill/`; confirm `references/skills.md` is under 60 lines (`wc -l`) and matches no `ENG-` (plan, Context cost); run quickstart manual check 7 - read `DESIGN.md` plus `references/skills.md` against `core/skills/factory/SKILL.md`, `core/roles/code-build.md`, `core/roles/fixer.md`, `core/roles/ui-reviewer.md` and confirm no restated or conflicting precedence rule (SC-010); confirm FR-030 - no new role file under `core/roles/`, no new verb in `references/verbs.md`, no new `state` telemetry field, model tiers unchanged; delete `$SCRATCH/fh` (FR-030, SC-008, SC-009, SC-010).
- [ ] T022 Run the six manual agent-driven checks 1-6 in [quickstart.md](./quickstart.md) (check 7 is a document read, run in T021) and report their results separately per `DESIGN.md`'s validation plan (SC-001..SC-007). `Exempt: specs/005-skill-routing/** - documentation only - this feature's own spec artifacts.`

---

## Dependencies & Execution Order

- **Phase 1** → **Phase 2**: T002 and T003 must record red before any source edit; T004 (`DESIGN.md`) precedes every other source edit (Constitution I); T005 precedes every task that links the reference.
- **Phases 3-7** depend on Phase 2 and are otherwise independent, in priority order P1 → P5. T020 depends on T004-T019 for the final gate; T021 depends on T020.
- `core/skills/factory/SKILL.md` is edited by T006, T008 and T014 and `references/state.md` by T007 and T012: those pairs are sequential, not `[P]`.

### Parallel Opportunities

- T011 and T012 (different files) within US3; T015 and T016 within US4; T017, T018 and T019 within US5.
- US4 and US5 documentation tasks may run alongside US3 once Phase 2 is complete.

## Implementation Strategy

MVP is Phase 1 + Phase 2 + Phase 3 (US1): intake routing and the resumable `brainstorm` stage, with `DESIGN.md` and the shared reference in place. Deliver US2, US3, US4 then US5 incrementally, finishing each with the canonical render so `dist/` never drifts from its source.
