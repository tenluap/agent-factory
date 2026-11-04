# Specification Analysis Report: 022-adopt-spec (analyze pass 1)

Artifacts: `spec.md` (2710 words), `plan.md` (1967 words), `tasks.md` (2239 words), constitution 2.0.0. All within word budgets (3000 / 2000 / 2500). Extension hooks skipped (factory owns hooks and commits).

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| U1 | Underspecification / Inconsistency | HIGH | plan.md:L41, L48, L114; spec.md:L130 (edge case), FR-013; tasks.md T006, T009 | The pending-reuse rule cannot work as planned: plan says the orchestrator finds "an unfinished pending run with the same `branch` in `factory runs`", but `cmd_runs` emits each pending run's identity with `branch: null` (`find_runs` sets `{"source": "pending", "branch": None, "name": ...}`, spread over the entry), so a stored `branch` is never visible there. A retry after a failed write (the designed FR-013 path: "the pending run stays for a retry") therefore creates a second pending file, and write step 1 (`resolve_target`) then exits 3 "several pending runs of <repo>; name one", which adopt cannot do. Any unrelated pending run in the same repo blocks the write the same way. Neither case is in the spec, the plan or the confirmed write-seam failure paths. | Give the adoption's pending file a deterministic identity the CLI can find (for example the name `<repo-name>-adopt-<branch>` and reuse via `runs`'s `name`, or have `adopt` select the pending file whose stored `branch`/`spec_dir` match instead of `resolve_target`), and state in spec.md what happens when another pending run exists. A changed write-seam failure scope (for example "several pending runs" or "matching pending selected among others") invalidates the Q1 confirmation and needs a fresh `requires_user: true` scope question. |
| I1 | Inconsistency | MEDIUM | spec.md:L128, L186 (Assumptions); plan.md:L25, L113; SKILL.md step 1.2 | Spec says adopt "never fetches, pulls or pushes", but the planned route runs preflight (step 1), whose item 2 runs `git -C <repo> fetch origin <default-branch>`. The CLI itself never fetches (T005 asserts this for the dry-run only), so the statement is true of `factory adopt` but not of `/factory adopt`. | Scope the spec statement to the `factory adopt` CLI and the source branch, and note that preflight's existing default-branch fetch still runs (which is also why the write's re-inspection against pending `base` is authoritative). |
| U2 | Underspecification | MEDIUM | spec.md:L75 (US3-2), FR-004/FR-005; plan.md:L33, L36; tasks.md T005 | The `default-branch` shape is resolved only when the spec dir "exists on `base`" (`origin/<default>`). A spec dir committed to the local default branch but not pushed (a common plain-SpecKit state) matches nothing and exits 1 with the generic no-match reason; branching from `base` would also lose it. Spec says only "spec dir on the default branch". | State the rule in spec.md (the dir must be on `base`) and give the local-only case its own refusal reason (for example "spec dir is on local `<default>` but not on `<base>`; push it or create its branch first"). Adding that refusal changes the dry-run seam's failure paths, so it needs fresh scope confirmation. |
| U3 | Underspecification | MEDIUM | spec.md:L189 (Assumptions), US4, FR-009; core/roles/spec-builder.md "specify" stage; plan.md Project Structure | Spec assumes "re-running `specify` on an adopted spec updates the existing `spec.md` in place", but the spec-builder's `specify` stage says "the brief is the feature description. Write `spec.md`", i.e. it regenerates from the brief. Nothing in the plan or tasks makes an adopted run's `specify` pass treat the user's existing `spec.md` as its base, so `--stage specify` can replace user-authored content with a brief-derived spec. | Either add a prose task (exempt, documentation) telling the spec-builder's `specify` stage to edit an existing `spec.md` in place when `adopted` is present, or narrow the spec assumption to what the current role does and say so in the adoption grill's entry-stage option. |
| T1 | Terminology | LOW | spec.md:L15, L121 (US6-1); plan.md:L50; tasks.md T008 | Spec quotes the resume error as "no matching run"; the real `one_run` message (and T008's assertion) is `no run '<name>' in <repo>`. | Use "no run" in spec.md, or quote the actual message. |
| U4 | Underspecification | LOW | plan.md:L44, L67; spec.md FR-012, FR-015 | The `adopted` history entry's fields are not given: which `stage` it carries (chosen stage?) and its `commit` (the sha is unknown until after the commit; `complete` entries use `null`). | Add one line to plan.md "Data model": `{at, stage: <chosen_stage>, event: "adopted", commit: null, harness}`. |
| C1 | Coverage | LOW | spec.md:L133 (edge case); tasks.md T006 | Edge case "the source branch moves between dry-run and the write ... `base_commit` from the branch HEAD at the write" has no test that actually moves the branch; T006 asserts `base_commit` = pre-write HEAD with no intervening commit. | Add to T006's Red step: commit on `007-x` after the dry-run, then assert `base_commit` equals the new HEAD. (Same declared seam; no scope change.) |
| C2 | Coverage | LOW | spec.md SC-001, SC-005, US5 independent test; tasks.md T001 | SC-001's grill-to-running-stage flow and SC-005's reviewer behaviour on pre-adoption commits are prose-only; T001 writes a DESIGN.md validation-plan entry but no task runs it. This matches the repository's convention (spec 021 did the same) and constitution "Development Workflow" ("before it is relied on"). | Optional: note in T001 that the validation-plan run happens after merge, as for 021. |

## Coverage Summary

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 | Yes | T009 | prose (exempt) |
| FR-002 | Yes | T003, T006 | |
| FR-003 | Yes | T003, T004 | |
| FR-004 | Yes | T003, T005 | see U2 |
| FR-005 | Yes | T006, T007 | |
| FR-006 | Yes | T003, T006 | |
| FR-007 | Yes | T004, T006 | |
| FR-008 | Yes | T003 | |
| FR-009 | Yes | T003, T006 | |
| FR-010 | Yes | T009 | prose (exempt) |
| FR-011 | Yes | T009 | prose (exempt) |
| FR-012 | Yes | T006 | |
| FR-013 | Yes | T006, T007 | retry path broken, see U1 |
| FR-014 | Yes | T006 | |
| FR-015 | Yes | T002 | see U4 |
| FR-016 | Yes | T002, T006 | |
| FR-017 | Yes | T002 | |
| FR-018 | Yes | T006, T009 | digest passes `adopted` (non-LARGE field) |
| FR-019 | Yes | T009, T011 | |
| FR-020 | Yes | T009, T011 | |
| FR-021 | Yes | T008 | see T1 |
| FR-022 | Yes | T006 | |
| FR-023 | Yes | T001, T009-T012 | |
| SC-001 | Partial | T003-T007, T009 | grill not exercised, see C2 |
| SC-002 | Yes | T003, T004 | |
| SC-003 | Yes | T006, T007 | see U1 (duplicate pending) |
| SC-004 | Yes | T002, T008, T013 | |
| SC-005 | Partial | T011 | prose only, see C2 |
| SC-006 | Yes | T012 | |

## Test-scope and commit-unit check (factory override)

- Behaviour-changing tasks T002-T008 each have a mapped seam, ordered Red / Implement / Pass steps and a Done condition; every failure path they require is declared in plan.md "Test seams". No uncovered declared failure path: dry-run seam (T003 exit 5; T004 the rest), write seam (T006, T007), `validate_state` (T002), `resume` (T008).
- Confirmation: `Confirmed: 2026-11-04 - Q1 accepted` with snapshot `factory/relay/plan-Q1.md`; the snapshot is byte-identical to the current "Test seams" section, and `state.json` decisions record `Q1-test-scope` and plan `Q1` as explicit (`auto: false`). Current and complete.
- Plan-exempt tasks T001, T009-T013 excluded from this check.
- ENG-10: every new file (`adopt.py`, ADR 0017, `test_adopt.py`), abstraction and dependency (`none`) carries a reason. No finding.
- `Overridden: none` present; the repository has a runner, so no `Test runner:` line is needed.

## Constitution Alignment Issues

None. I (Design First): T001 lands first. II (Harness-Neutral Core): prose uses `SHELL`/`ASK`; the CLI hint names its own verb. III (Generated Dist): T012 builds all five harnesses and checks `dist/` is untracked. IV (Stateless Agents): adoption facts live in `state.json`; `adopted_base` is passed as input. V (Simplicity and Reuse): reuse is stated and every new file, field and verb has a reason.

## Unmapped Tasks

None (T012, T013 are verification for FR-023 / SC-004 / SC-006).

## Metrics

- Total requirements: 29 (23 FR, 6 SC)
- Total tasks: 13
- Coverage: 100% (29/29 with at least one task; SC-001 and SC-005 partial, prose-only)
- Ambiguity count: 0
- Duplication count: 0
- Critical issues: 0
- Severity counts: CRITICAL 0, HIGH 1, MEDIUM 3, LOW 4

## Next Actions

- Resolve U1 before implementation: it breaks the specified retry path and the pending-reuse edge case. Its fix changes the write seam's failure scope, so remediation must return a fresh `requires_user: true` test-scope question.
- U2 and U3 are recommended before implementation. U2 also changes seam scope, so it can go in the same re-confirmation round.
- I1 and the LOW findings are spec and plan wording edits only.
