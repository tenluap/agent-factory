# Specification Analysis Report - pass 1

**Feature**: 005-skill-routing | **Date**: 2026-10-25 | **Mode**: lite chain, fast on

Artifacts: `spec.md`, `plan.md`, `tasks.md`, `research.md`, `data-model.md`, `quickstart.md`,
`checklists/requirements.md`; constitution `.specify/memory/constitution.md` v1.0.0. Read-only analysis.

## Findings

| ID | Category | Severity | Blocking | Location(s) | Summary | Recommendation |
|----|----------|----------|----------|-------------|---------|----------------|
| I1 | Inconsistency | MEDIUM | yes | plan.md Summary (L17-20), plan.md Scale/Scope (L72-74) vs tasks.md T004-T019 | Plan says "four roles" but names five (`spec-builder`, `code-build`, `fixer`, `ui-reviewer`, `ux-reviewer`, also listed as five in Project Structure), and "11 edited source and document files" while the tasks edit 13 (`DESIGN.md`, `SKILL.md`, `state.md`, `protocol.md`, 5 roles, ADR 0001, `README.md`, `docs/product-brief.md`, `CONTEXT.md`). | Correct to "five roles" and "13 edited source and document files" in Summary and Scale/Scope. |
| U1 | Underspecification | MEDIUM | yes | tasks.md T001 vs plan.md "Test seams" exemption list (L161-175) | T001 carries `Exempt: configuration only - no product file changes.`, which is not one of the plan's exemptions; every other exempt task quotes a plan exemption verbatim. | Add `Exempt: setup/environment steps - configuration only - no product file changes.` to the plan's exemption list, or drop T001's exemption line and fold the setup into T002/T003's preconditions. |
| G1 | Coverage gap | MEDIUM | yes | spec.md FR-030; tasks.md (no task), quickstart.md | FR-030 (no new agent role, harness verb, model tier, external service or second planning chain; existing `state`/`ledger`/`history` carry the new activity instead of new telemetry) is argued in plan.md Constitution Check V but has no task and no verification step. T020 only checks that no adapter-specific model setting changed. | Extend T021 with an explicit FR-030 check (no new role file under `core/roles/`, no new verb in `references/verbs.md`, no new `state` telemetry field, model tiers unchanged), or add it to T020's confirmation line. |
| G2 | Coverage gap | MEDIUM | yes | spec.md SC-010; plan.md Seam 2 (L148-152); quickstart.md Manual checks (L126-145) | SC-010 ("stated once as the source of truth and agree with every role instruction depending on them") is cited by T004 and T005, but nothing verifies agreement: Seam 2 only proves `references/skills.md` exists and is mentioned by three files, and the six manual checks cover SC-001..SC-008 only. | Add a manual check 7 (or a step in T021) that reads `DESIGN.md` plus `references/skills.md` against `SKILL.md`, `code-build.md`, `fixer.md`, `ui-reviewer.md` and confirms no restated or conflicting precedence rule. |
| G3 | Coverage gap | LOW | no | spec.md FR-027; tasks.md T006-T016 | FR-027 (update orchestrator intake, conditional resolution, role inputs, UI detection, the state and protocol references and the four roles "where the routing affects them") is satisfied in substance by T006-T016 but is cited by no task, so its coverage is implicit only. | Add `FR-027` to the citation lists of T006, T011 and T013-T016. |
| I2 | Inconsistency | LOW | no | plan.md Seam 3 (L153-159) vs quickstart.md L115-116 | Plan's Seam 3 says `requires_user` is documented in `protocol.md`'s question fields; the quickstart assertion requires the token in **both** `protocol.md` and `state.md` (which T012 supplies). | Say "documented in `protocol.md`'s question fields and `state.md`'s fast-mode step" in the plan's Seam 3 bullet. |
| G4 | Coverage gap | LOW | no | plan.md Constraints "Context cost" (L57-59); tasks.md T005 | The "under 60 lines, restates no `ENG-n` rule" constraint on `references/skills.md` is an instruction to T005 with no check in any seam, so a later edit can silently breach it. | Add a one-line assertion to Seam 2 / T021 (`wc -l` under 60 and no `ENG-` match in `references/skills.md`), or state in the plan that the constraint is review-enforced only. |
| I3 | Inconsistency | LOW | no | tasks.md "Render discipline" (L16) vs T020 (L108) | Render discipline makes every `core/`-editing task finish with a canonical render of all five harnesses, which makes T020's "re-render and commit" a no-op by the time it runs. | Reword T020 as the final render gate and scope check (render, confirm the gate is clean, confirm no model setting changed) rather than as the render step. |
| A1 | Ambiguity | LOW | no | spec.md FR-001, SC-001; data-model.md "Intake intent" (L14-18) | Classification rests on descriptive cues ("open-ended idea wording", "concrete feature/change wording"), with no enumerated examples, so SC-001's three trials and T006's implementation rest on judgement. The both-cues case is resolved (spec Edge Cases, the single intent question). | Have T004 record two or three example cue phrases per intent in `DESIGN.md`'s routing contract, and name those exact phrases in quickstart manual check 1 so the trials are repeatable. |
| F1 | Inconsistency | LOW | no | spec.md Key Entities (L156-157) vs plan.md / tasks.md / data-model.md | The spec names the stage "Exploration stage" and the skills only in Assumptions, while plan, tasks and data-model use the concrete `brainstorm`/`grill` stage values and `ponytail`/`tdd`/`brainstorming`/`impeccable`. Only data-model.md's intent table states the mapping. | Add the concrete stage values to the spec's "Exploration stage" entry (`brainstorm`, settling into `grill`) so the vocabulary is one term per concept across artifacts. |

No CRITICAL findings. No HIGH findings.

## Seam and test-task check (factory override)

Every implementation task is covered by a plan exemption and carries it verbatim (T004-T020, T022);
the only non-exempt tasks are the seam checks themselves (T002, T003 red; T021 green). No implementation
task lacks a mapped seam, lacks a preceding test task, or names a seam the plan does not list. Exempt
tasks are excluded from this check, so no HIGH finding arises. The only exemption defect is U1 above
(an exemption on T001 that the plan does not list).

Seam names used in tasks (`Seam 1`, `Seam 2`, `Seam 3`) all exist in plan.md's "Test seams" section.
`Overridden: none` is present. `Test runner` is correctly not introduced: `state.commands` already
documents build and test.

**Seam commands were executed as written to confirm they are runnable:**

- Seam 1 paths: `python3 tools/render.py --list` yields the five harnesses and every
  `dist/<harness>/skill/references/` tree exists, so the quickstart spot-check path for
  `skills.md` is correct on all five.
- Seam 2: the link-integrity script runs over 26 sources and currently prints `links ok` (0 broken
  relative links), so T002's recorded red will come from the three "does not link" assertions only -
  which matches the plan. `SKILL.md` does use Markdown relative links, so the plan's stated red (a link
  added before the file exists) will also fire.
- Seam 3: the three fixtures were written under a scratch `FACTORY_HOME` and digested with
  `core/skills/factory/bin/factory show`. Results: `stage: "brainstorm"` passes through; the unanswered
  question keeps `requires_user: true` verbatim (`relay_digest` spreads the question dict); the version 1
  single-batch relay digests (`total: 1`) and the version 2 string answer digests (`answered: 1`).
  The plan's and research.md's R1/R2 pass-through claims hold. Fixtures were kept outside the repository.

## ENG-10 check (new files, abstractions, dependencies)

plan.md "New files, abstractions and dependencies (ENG-10)" states a reason for each of: the new file
`core/skills/factory/references/skills.md`, the `state.stage` value `brainstorm`, the question field
`requires_user`, and `dependency - none added`. **No ENG-10 findings.**

## Word budget check

| Artifact | `wc -w` | Budget | Status |
|---|---|---|---|
| spec.md | 2992 | 3000 | within (8 words of headroom) |
| plan.md | 1677 | 2000 | within |
| tasks.md | 1978 | 2500 | within |

No budget findings. Note for remediation: `spec.md` is 8 words below its budget, so any edit to it must
be net-neutral or trimming.

## Coverage summary

| Requirement | Has task? | Task IDs |
|---|---|---|
| FR-001..FR-005 | yes | T006 |
| FR-006 | yes | T007 (+ Seam 3 / T003, T021) |
| FR-007, FR-008 | yes | T006, T008, T014 |
| FR-009, FR-010 | yes | T008 |
| FR-011 | yes | T006, T008 |
| FR-012 | yes | T009, T010, T015 |
| FR-013..FR-015 | yes | T009, T010 |
| FR-016, FR-018 | yes | T013 |
| FR-017 | yes | T011, T012 |
| FR-019 | yes | T009, T010 |
| FR-020, FR-025 | yes | T014 |
| FR-021, FR-022 | yes | T015 |
| FR-023 | yes | T016 |
| FR-024 | yes | T010, T015 |
| FR-026 | yes | T004, T005, T019 |
| FR-027 | implicit | T006-T016 (G3) |
| FR-028 | yes | T017, T018 |
| FR-029 | yes | T020 |
| FR-030 | **no** | - (G1) |
| SC-001..SC-003 | yes | quickstart manual checks 1-2 |
| SC-004 | yes | manual check 4 |
| SC-005 | yes | manual check 3 |
| SC-006, SC-007 | yes | manual check 5 |
| SC-008 | yes | T003, T021, manual check 6 |
| SC-009 | yes | T020, T021 |
| SC-010 | **partial** | T004, T005; no agreement check (G2) |

Unmapped tasks: none. Every task cites at least one FR/SC or is a seam check.

## Constitution alignment

| Principle | Verdict |
|---|---|
| I. Design First | Pass - T004 edits `DESIGN.md` before every other source edit, and the dependency section states it. |
| II. Harness-Neutral Core | Pass - all new `core/` text uses logical skill names and `RESOLVE` only; plan states the impeccable launcher stays "the skill's own directory". |
| III. Generated Dist (NON-NEGOTIABLE) | Pass - Seam 1 is the documented gate, render discipline is per task, T020/T021 confirm (see I3 for the wording overlap). |
| IV. Stateless Agents | Pass - intent, seams and skill paths live in `brief.md`, `plan.md`, `state.json`; no role talks to the user (FR-019). |
| V. Simplicity and Reuse | Pass - one new file, one stage value, one optional field, each with a stated reason; no new role, verb, tier or chain (FR-030 is unverified, G1, but not violated). |

No constitution violations, so no CRITICAL findings.

## Metrics

- Total functional requirements: 30 (FR-001..FR-030); success criteria: 10 (SC-001..SC-010)
- Total tasks: 22 (T001..T022), 8 phases
- Requirement coverage: 29/30 with at least one task (96.7%); 1 uncovered (FR-030)
- Success-criteria coverage: 9/10 fully, 1 partial (SC-010)
- Ambiguity findings: 1 | Duplication findings: 0 | Inconsistency findings: 3 | Coverage gaps: 4 | Underspecification: 1
- Severity counts: CRITICAL 0, HIGH 0, MEDIUM 4, LOW 5 (total 9)
- Placeholders found (TODO/TKTK/???/NEEDS CLARIFICATION): 0
- Referenced source files that exist: 17/18 (only the new `core/skills/factory/references/skills.md` is absent, as intended)

## Next actions

No CRITICAL or HIGH findings, so nothing blocks implementation on severity. The four MEDIUM findings are
blocking under the factory's remediation rules and are all in-place artifact edits:

1. I1 - fix the role and file counts in `plan.md`.
2. U1 - reconcile T001's exemption with the plan's exemption list.
3. G1 - add an FR-030 verification step to T020/T021.
4. G2 - add an SC-010 agreement check to the quickstart manual checks and T021.

Then the five LOW findings (G3, I2, G4, I3, A1) as targeted wording edits. None of the findings needs a
user decision, so remediation should return an empty `pending_clarify`.
