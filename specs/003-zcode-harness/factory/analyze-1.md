# Specification Analysis Report — pass 1

Feature: `003-zcode-harness` (ZCode Harness Adapter)
Artifacts: `spec.md`, `plan.md`, `tasks.md`, `research.md`, `data-model.md`, `quickstart.md`
Constitution: `.specify/memory/constitution.md` v1.0.0
Read-only: no artifact was modified by this pass.

## Findings

| ID | Category | Severity | Blocking | Location(s) | Summary | Recommendation |
|----|----------|----------|----------|-------------|---------|----------------|
| D1 | Constitution Alignment | CRITICAL | yes | plan.md "Constitution Check III" / "Test seams" Seam 4; tasks.md T011, T017; quickstart.md step 2; repo `.gitignore` | `.gitignore` lists `/dist/` and `git ls-files dist/` returns 0 files: `dist/` is untracked and ignored repo-wide. Every artifact rests on Constitution III ("dist committed with its source") and on `git diff --exit-code -- dist/` as the gate. As written, a plain `git add dist/` is refused and `git diff --exit-code -- dist/` can never fail, so the non-negotiable principle is neither satisfied nor checked. | Fix in the artifacts: make the staging step explicit (`git add -f dist/`) and replace the inert check with one that can fail (`git add -f dist/ && git diff --cached --exit-code -- dist/`, or re-render into a temp tree and `diff -r`). If the repo-level choice is instead to stop ignoring `/dist/` or to drop the commit-dist requirement, that is a user decision — escalate it as `pending_clarify` rather than guessing. |
| D2 | Constitution Alignment | CRITICAL | yes | DESIGN.md:69; plan.md "Deviations" D2; tasks.md T008, T012, T013 | Constitution I makes `DESIGN.md` the source of truth: an adapter that disagrees with it is wrong unless `DESIGN.md` changes in the same change. `DESIGN.md:69` states SpecKit init as `--ai <harness>` plus `--ai-skills`; the ZCode adapter's `speckit_init` is `--integration zcode --integration-options="--skills"` (research R4). T013 edits only the harness list and "Adapters today", so `DESIGN.md` is left contradicting the new adapter. | Extend T013 to generalise `DESIGN.md:69` ("`<harness.speckit_init>`, whose shape each adapter states") so the adapter and `DESIGN.md` agree in this change. |
| C1 | Inconsistency / Conflicting requirement | HIGH | yes | spec.md FR-010; plan.md D1; research.md R2; tasks.md T009, T015 | FR-010 requires six skill roots including the two `.claude` roots; research R2 verified ZCode reads only `<repo>/.zcode/skills/`, `<repo>/.agents/skills/`, `~/.zcode/skills/`, `~/.agents/skills/`. Plan and tasks implement the four-root form, so the spec contradicts what will be built. | Correct FR-010 in `spec.md` in place to the four verified roots (and fold plan deviation D1 into a note), so the spec is right before implementation starts. |
| C2 | Task seam/exemption validity | HIGH | yes | tasks.md T015; plan.md "Test seams" exemptions | T015 is an implementation task that edits `specs/003-zcode-harness/spec.md` and cites `Exempt: specs/**.md - documentation only`, an exemption the plan's list does not contain (the plan exempts only `adapters/zcode/harness.md`, `README.md`, `DESIGN.md`, `CONTEXT.md`, `dist/zcode/**`). It also defers a spec correction into implementation, where the spec is supposed to be settled. | Drop T015 and apply the FR-010 correction to `spec.md` now (see C1). If any spec-folder edit must survive as a task, add the matching exemption to the plan's exemption list first. |
| S1 | Underspecification / untestable criterion | HIGH | yes | plan.md "Test seams" Seam 4; tasks.md T007, T011, T017; spec.md SC-003, SC-006 | Seam 4 is defined as `git diff --exit-code -- dist/`. With `/dist/` gitignored and untracked, the command always exits 0, so it cannot be red before the change and proves nothing: SC-003 ("zero differences between the committed distribution and a fresh render") and SC-006 ("existing harness outputs unchanged") have no working coverage. T007's stated red ("MUST fail now") is also unachievable by that command. | Redefine Seam 4 as a check that can fail (render every harness into a scratch tree and compare it with `dist/`, or stage with `git add -f` and use `git diff --cached --exit-code`), and update T007/T011/T017 and quickstart step 2 to the new form. Note that every harness's skill legitimately gains `references/harness/zcode.md`, so the comparison must be made after the render, not against the pre-change tree. |
| X1 | Inconsistency | MEDIUM | no | tasks.md T011; plan.md "Test seams" exemptions | T011 cites `Exempt: dist/** - generated output ...` while the plan's exemption reads `dist/zcode/**`. The wider path silently exempts every other harness's regenerated output. | Quote the plan's exemption verbatim, or widen the plan's exemption to `dist/**` with the reason (the render rewrites every harness's skill tree) so plan and tasks match. |
| G1 | Coverage Gap | MEDIUM | no | spec.md SC-005; tasks.md T018 | SC-005 (a run started in ZCode resumes on another harness and vice versa) is listed in T018's header but none of T018's steps resume a run: the steps cover install, env override, a fresh `/factory` start and uninstall. | Add an explicit resume step to T018 (start a run in ZCode, stop it, resume from another installed harness and back), or state that SC-005 follows from the shared `state.json` with no ZCode-specific work and record that as the coverage note. |
| N1 | Underspecification | LOW | no | tasks.md T001 | T001 creates an empty `adapters/zcode/` folder. Git does not track empty directories and `tools/render.py:known()` only counts folders containing `adapter.json`, so the task has no observable effect. | Merge T001 into T004 (which creates `adapters/zcode/adapter.json`) or delete it. |
| N2 | Style | LOW | no | plan.md "Deviations from the spec" | The plan records D1/D2 as deviations that "should" be corrected in the spec later rather than the spec being corrected; this is what produced C1 and C2. | After the FR-010 fix, restate D1/D2 as resolved research corrections rather than open deviations. |

## Coverage Summary

| Requirement key | Has task? | Task IDs | Notes |
|---|---|---|---|
| FR-001 | yes | T004, T008 | adapter.json + harness.md |
| FR-002 | yes | T009 | SPAWN / SPAWN_PARALLEL rows |
| FR-003 | yes | T004 | home/env/default, skill_dir, agent_dir |
| FR-004 | yes | T004, T005, T006 | frontmatter asserted by Seam 3 |
| FR-005 | yes | T004 | access read/write tool lists |
| FR-006 | yes | T004, T010 | empty `models`, config override note |
| FR-007 | yes | T010 | `$ARGUMENTS` note |
| FR-008 | yes | T009 | ASK row |
| FR-009 | yes | T009 | NOTIFY no-op |
| FR-010 | yes | T009 | **conflicts with spec text — C1** |
| FR-011 | yes | T008 | `speckit_init`; see D2 for DESIGN.md |
| FR-012 | yes | T008 | recognition line + impeccable provider |
| FR-013 | yes | T010 | no Skill-tool invocation of speckit/grilling |
| FR-014 | yes | T010 | ledger `reported: null` |
| FR-015 | yes | T011 | full render; gate inert — S1 |
| FR-016 | yes | T012, T013, T014 | README / DESIGN / CONTEXT |
| FR-017 | yes | T016 | `git diff --name-only` over `core/` |
| SC-001 | yes | T018 | manual |
| SC-002 | yes | T006, T018 | 9 roles confirmed in `core/roles/` |
| SC-003 | weak | T011, T017 | gate cannot fail — S1 |
| SC-004 | yes | T005, T006 | Seam 3 |
| SC-005 | no | (T018 header only) | G1 |
| SC-006 | weak | T007, T011 | gate cannot fail — S1 |

Coverage: 17/17 functional requirements have ≥1 task (100%); 4/6 success criteria have working coverage (SC-003 and SC-006 rest on an inert gate, SC-005 has no step).

## Test-seam check (factory override)

- Implementation tasks with a failing-test task immediately before them: T004 (after T003, Seams 1–2) ✓.
- Plan-exempt tasks (excluded from the check): T006, T008, T009, T010, T011, T012, T013, T014.
- Tasks citing an exemption the plan does not list: T015 (C2, HIGH blocking); T011 cites a wider path than the plan (X1, MEDIUM).
- Seams named by tasks that the plan lists: Seams 1, 2, 3, 4 ✓ — but Seam 4 itself is not a working seam (S1).
- Test runner: the repo has one (documented build/test commands); no runner-setup task is required and none is added ✓.

## ENG-10 / budget checks

- New files, abstractions and dependencies: `plan.md` states a reason for `adapters/zcode/adapter.json`, `adapters/zcode/harness.md` and `dist/zcode/**`, and `none` for abstraction and dependency. No ENG-10 finding.
- Word budgets (`wc -w`): `spec.md` 1717/3000, `plan.md` 1013/2000, `tasks.md` 1605/2500. All within budget; no finding.

## Unmapped tasks

None. T002, T016, T017, T018 are verification/validation tasks tied to the seams and success criteria above.

## Metrics

- Total requirements: 17 FR + 6 SC
- Total tasks: 18
- Coverage: 100% FR, 67% SC with working coverage
- Ambiguity count: 0 unresolved placeholders
- Duplication count: 0
- CRITICAL: 2 · HIGH: 3 · MEDIUM: 2 · LOW: 2

## Next actions

Two CRITICAL and three HIGH findings are blocking; remediate before implementation. D1 is the one that may need a user decision (whether `/dist/` stays gitignored and `git add -f` is used, or the repo stops ignoring it) — everything else is a targeted in-place edit to `spec.md`, `plan.md`, `tasks.md` and `quickstart.md`.
