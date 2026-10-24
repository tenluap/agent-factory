# Specification Analysis Report — pass 2

Feature: `003-zcode-harness` (ZCode Harness Adapter)
Artifacts: `spec.md`, `plan.md`, `tasks.md`, `research.md`, `data-model.md`, `quickstart.md`, `CONTEXT.md`,
`docs/adr/0005-the-rendered-distribution-is-tracked-in-git.md`
Constitution: `.specify/memory/constitution.md` v1.0.0
Read-only: no artifact was modified by this pass.

## Status of analyze-1 findings

| ID | Severity (pass 1) | Status | Evidence |
|----|---|---|---|
| D1 | CRITICAL | **resolved** | FR-018 added; `.gitignore` loses `/dist/`; ADR 0005 written; plan Constitution Check III and T001 implement tracking, so `git add dist/` works and the gate can fail. |
| D2 | CRITICAL | **resolved** | FR-016 now requires the generalised spec-kit setup line; T013 explicitly rewrites `DESIGN.md:69` to `specify init --here <harness.speckit_init>`; research R4 records the scope boundary. |
| C1 | HIGH | **resolved** | FR-010 and the matching edge case now list exactly the four verified roots; clarification recorded in spec.md §Clarifications; research R2 marked closed. |
| C2 | HIGH | **resolved** | T015 removed (Phase 6 note); the spec correction was applied at clarify, not deferred to implementation. |
| S1 | HIGH | **resolved** | Seam 4 is now "render every harness, then `git diff --exit-code -- dist/`" over a *tracked* `dist/`, with a stated red proof (T002) and SC-003/SC-006 reworded around a check that can fail. |
| X1 | MEDIUM | **resolved** | Plan exemption is now `dist/** - generated output for every harness ...`; T006 and T011 quote it verbatim. |
| G1 | MEDIUM | **resolved** | T018 carries SC-005 (a) and (b) as explicit resume steps in both directions; quickstart step 5 matches. |
| N1 | LOW | **resolved** | The empty-folder task is folded into T004 (Phase 1 note). |
| N2 | LOW | **resolved** | "Deviations from the spec" is now "Research corrections folded into the spec", both closed. |

All nine pass-1 findings are resolved. The findings below are new, and all three HIGHs were introduced by
the pass-1 remediation itself (the move to a tracked `dist/`) or by task wording written after it.

## Findings

| ID | Category | Severity | Blocking | Location(s) | Summary | Recommendation |
|----|----------|----------|----------|-------------|---------|----------------|
| B1 | Task ordering / unachievable green | HIGH | yes | tasks.md T004, T006, Phase 3 "Independent Test", plan.md Seam 2; `tools/render.py:98-99` | `render()` copies **every** known adapter's `harness.md` into every harness's skill tree, and `known()` counts any folder holding `adapter.json`. So the moment T004 creates `adapters/zcode/adapter.json` without `adapters/zcode/harness.md`, *every* harness's render dies with `FileNotFoundError: .../adapters/zcode/harness.md` (reproduced). T006 ("`python3 tools/render.py zcode`, confirm 9 agents") therefore cannot pass, T004's claim that it "turns T003 green for Seams 1 and 2" is false (only Seam 1 goes green), and the whole repository build is broken between T004 and T008 — which sits two phases later. Phase 3's "MVP: the adapter renders and installs" is unreachable as ordered. | Create both adapter files together: either extend T004 to write `adapters/zcode/harness.md` as well, or move T008 (and ideally T009/T010) ahead of T006 into Phase 3. Update the dependency list (`T003 → T004 → T005 → T006`) and plan Seam 2's red/green wording so no step leaves `adapter.json` present without `harness.md`. |
| B2 | Requirement not implemented as written | HIGH | yes | tasks.md T008; spec.md FR-012 + clarification 8; data-model.md §2 | FR-012 and the recorded clarification require the recognition line to rest on a **checkable signal** (`ZCODE_HOME` set or `~/.zcode` present); data-model §2 spells that line out. T008 quotes the line to write as "you are ZCode (Z.ai's coding agent, desktop app or CLI); you have the Agent, Bash, Read, Edit and Skill tools." — the checkable signal is dropped, leaving self-description plus a tool list, which is exactly what FR-012 forbids. The only task that creates the recognition line would therefore violate the requirement it implements. | Quote data-model §2's line verbatim in T008: "you are ZCode (Z.ai's coding agent, desktop app or CLI): `ZCODE_HOME` is set or `~/.zcode` exists, and you have the Agent, Bash, Read, Edit and Skill tools." |
| B3 | Underspecification / gate cannot hold | HIGH | yes | spec.md FR-018, SC-003, SC-006; plan.md "Test seams" Seam 4, "Constraints"; tasks.md T001, T007, T011, T017, T018; quickstart.md steps 2 and 4 | The rendered output is **environment-dependent**, which the move to a tracked `dist/` turns into a live problem. `load_adapter` resolves `{home}` from each adapter's home env var and `render()` substitutes it into every agent body (`<F>` → `skill_dir`), and it merges `${FACTORY_HOME}/config.json` model overrides into the frontmatter. Reproduced: `XDG_CONFIG_HOME=/Users/x/.cfg python3 tools/render.py opencode` rewrites `~/.config/opencode/skills/factory/...` to `/Users/x/.cfg/...` in every agent file; a `models.zcode` override adds a `model:` key to `dist/zcode/agents/*.md`. With `dist/` ignored this was invisible; with `dist/` tracked, any contributor who has `XDG_CONFIG_HOME`, `CLAUDE_HOME`, `CODEX_HOME`, `ZCODE_HOME` or a `FACTORY_HOME` model override set makes `git diff --exit-code -- dist/` fail spuriously, so SC-003/SC-006 ("zero differences after a fresh render") do not hold in general environments. The same mechanism means quickstart step 4 / T018's `ZCODE_HOME=/tmp/zc ./install.sh --harness zcode` (and any plain `./install.sh`, which renders) rewrites the tracked tree as a side effect — and a `model:` key in the rendered output would also break Seam 3's exact `{name, description, tools}` assertion. | Define the canonical render environment in the artifacts: state in FR-018/SC-003 (and the plan's Constraints + Seam 4, T001/T011/T017, quickstart step 2) that the build and the gate run with the harness home variables and `FACTORY_HOME` unset — e.g. `env -u CLAUDE_HOME -u CODEX_HOME -u ZCODE_HOME -u XDG_CONFIG_HOME -u FACTORY_HOME` around the render loop — and add to T018/quickstart step 4 the instruction to restore the canonical render (`git checkout -- dist/` or a clean re-render) after the `ZCODE_HOME` override and after any local `install.sh`. |
| M1 | Inconsistency (documentation accuracy) | MEDIUM | no | tasks.md T012; README.md:72; research.md R4 | R4 established that specify-cli 1.1.0 has **no** `--ai`/`--ai-skills` flags at all. T012 extends README's existing line `specify init --here --ai <claude\|opencode\|codex\|copilot>` (add `--ai-skills`) with ZCode's `--integration zcode --integration-options="--skills"`, producing one requirement line that presents a non-existent flag family and the real one side by side. FR-016's scope decision (no other adapter's recorded setup changes in this feature) is respected, but the resulting line is self-contradictory for a reader following US3's "accurate install details". | Have T012 add ZCode's form as its own sentence or table entry rather than as another value of the `--ai` enumeration, and note that the other harnesses' recorded form is out of scope for this feature (same wording as research R4's note). |
| M2 | Terminology / verifiability | MEDIUM | no | tasks.md T003; quickstart.md steps 2-3 | T003 says to "add the two commands as an executable check in `specs/003-zcode-harness/quickstart.md` step 2-3 form and run them", but quickstart already contains them; as written the task's deliverable is ambiguous (add what, where) and it is the only test task without a concrete artifact of its own. | Reword T003 to "run the Seam 1 and Seam 2 commands already written in quickstart.md steps 2-3 and record their failure output", matching T005's wording. |
| L1 | Style / traceability | LOW | no | plan.md "New files ... (ENG-10)"; tasks.md Notes | `docs/adr/0005-...md` and the `CONTEXT.md` ZCode line are listed as outputs of this change but already exist on the branch (written by the domain-modeling step) and no task creates them. The tasks' Notes say so, the plan does not. | Add the same one-line note to the plan's ENG-10 list so the reader is not looking for a missing task. |

## Coverage Summary

| Requirement key | Has task? | Task IDs | Notes |
|---|---|---|---|
| FR-001 | yes | T004, T008 | adapter.json + harness.md (ordering defect — B1) |
| FR-002 | yes | T009 | SPAWN / SPAWN_PARALLEL rows |
| FR-003 | yes | T004 | home/env/default, skill_dir, agent_dir |
| FR-004 | yes | T004, T005, T006 | Seam 3; see B3 for the `model:` key risk |
| FR-005 | yes | T004 | access read/write tool lists |
| FR-006 | yes | T004, T010 | empty `models`, config override note |
| FR-007 | yes | T010 | `$ARGUMENTS` note |
| FR-008 | yes | T009 | ASK row |
| FR-009 | yes | T009 | NOTIFY no-op |
| FR-010 | yes | T009 | four verified roots — matches spec now |
| FR-011 | yes | T008 | `speckit_init`; DESIGN.md generalised by T013 |
| FR-012 | weak | T008 | recognition line drops the checkable signal — B2 |
| FR-013 | yes | T010 | no Skill-tool invocation of speckit/grilling |
| FR-014 | yes | T010 | ledger `reported: null` |
| FR-015 | yes | T011 | full render of every harness |
| FR-016 | yes | T012, T013, T014 | README / DESIGN / CONTEXT; README line mixed — M1 |
| FR-017 | yes | T016 | `git diff --name-only` over `core/` |
| FR-018 | yes | T001, T011 | tracking works; gate is environment-sensitive — B3 |
| SC-001 | yes | T018 | manual install + start |
| SC-002 | yes | T006, T018 | 9 roles confirmed in `core/roles/` |
| SC-003 | weak | T011, T017 | holds only under a canonical render environment — B3 |
| SC-004 | yes | T005, T006 | Seam 3 |
| SC-005 | yes | T018 (a)(b), quickstart 5 | resolved from pass 1 |
| SC-006 | weak | T007, T011, T017 | same environment sensitivity — B3 |

Coverage: 18/18 functional requirements have ≥1 task (100%); 6/6 success criteria have a step, 2 of them
(SC-003, SC-006) conditional on B3 and 1 (FR-012's part of SC-001/US2) weakened by B2.

## Test-seam check (factory override)

- Implementation tasks with a failing-test task immediately before them: T004 (after T003, Seams 1-2) ✓.
- Plan-exempt tasks (excluded from this check): T001, T006, T008, T009, T010, T011, T012, T013, T014.
- Every exemption quoted by a task appears verbatim in the plan's exemption list ✓ (pass-1 X1 fixed).
- Seams named by tasks are all listed in the plan (Seams 1-4) ✓; Seam 4 is now a check that can fail,
  subject to B3's environment caveat.
- Test runner: the repository has one (`tools/render.py` + `git diff --exit-code -- dist/`); no
  runner-setup task is added ✓.
- `Overridden: none` is stated in the plan ✓.

## ENG-10 / budget checks

- New files, abstractions and dependencies: the plan states a reason for `adapters/zcode/adapter.json`,
  `adapters/zcode/harness.md`, `dist/**` and `docs/adr/0005-...md`, and `none` for abstraction and
  dependency. No ENG-10 finding.
- Word budgets (`wc -w`): `spec.md` 2349/3000, `plan.md` 1470/2000, `tasks.md` 2243/2500. All within
  budget; no finding.

## Unmapped tasks

None. T002, T016, T017 and T018 are baseline/verification tasks tied to the seams and success criteria
above.

## Metrics

- Total requirements: 18 FR + 6 SC
- Total tasks: 17 (T001-T018, T015 removed)
- Coverage: 100% FR with a task; 3 success criteria carry a caveat (B2, B3)
- Ambiguity count: 0 unresolved placeholders
- Duplication count: 0
- CRITICAL: 0 · HIGH: 3 · MEDIUM: 2 · LOW: 1
- Pass-1 findings resolved: 9 of 9

## Next actions

Three HIGH findings block implementation; none is a CRITICAL constitution violation. B1 and B2 are
mechanical in-place edits to `tasks.md` (and one wording line in `plan.md`). B3 needs the canonical render
environment written into `spec.md` (FR-018/SC-003/SC-006), `plan.md` (Constraints, Seam 4), `tasks.md`
(T001, T007, T011, T017, T018) and `quickstart.md` (steps 2 and 4); the `env -u ...` form is the smallest
change that makes the tracked-`dist/` gate deterministic, so it needs no user decision unless the
remediator prefers a different canonicalisation. M1, M2 and L1 are non-blocking wording fixes.
