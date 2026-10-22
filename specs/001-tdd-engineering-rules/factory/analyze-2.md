# Specification Analysis Report — pass 2

**Feature**: `001-tdd-engineering-rules` — Engineering discipline for factory code-writing roles
**Artifacts**: `spec.md`, `plan.md`, `tasks.md`, `research.md`, `data-model.md`, `contracts/{engineering-reference,commit-body,plan-artifact}.md`, `quickstart.md`, `checklists/requirements.md`, plus the repository documents the run already committed (`CONTEXT.md`, `docs/adr/0001`..`0004`)
**Constitution**: `.specify/memory/constitution.md` v1.0.0
**Previous pass**: [analyze-1.md](./analyze-1.md); remediation: [remediation-1.md](./remediation-1.md)
**Mode**: read-only. No artifact was modified.

## Status of pass 1

All 15 findings of pass 1 (D1, U1–U3, I1–I4, A1, A2, L1–L5) were re-checked against the regenerated artifacts and every one is fixed:

- **D1** — `tasks.md` now renders and commits `dist/` inside every `core/`-editing task (T003–T010), `[P]` is gone from them, "Parallel Opportunities" and the Notes match, and `plan.md`'s Constitution Check III states the same timing. No commit in the planned history carries a stale `dist/`.
- **U1** — FR-015b, FR-015e, T007(a), T009 and `contracts/commit-body.md` give the spec-conformance reviewer the commit log (`git log --format='%H%n%s%n%b%n--' <base>..HEAD`); verified against `core/skills/factory/references/findings.md` ("Reviewing" currently scopes only the diff), so the added scope line is the right fix.
- **U2** — the fix-commit rule is decided: matched against `<spec_dir>/factory/reviews/round-<n-1>/verdict.json`. Verified against `core/skills/factory/SKILL.md` review steps 3–4: the orchestrator already writes that path and already passes `spec_dir` and the round to every reviewer, so the reviewer can read it in one spawn (constitution IV). Residual gap for the approver's user-changes fix commit is finding **U4** below.
- **U3, I1–I4, A1, A2, L1–L5** — all present in the artifacts as the remediation log describes (commit-level finding shape; one term per concept; `ENG-2` yields to a plan exemption; the three analyze conditions aligned between FR-019/FR-020/SC-002 and `contracts/plan-artifact.md`; canonical `Exempt:`/`Overridden:` lines in `plan.md`; both red-proof forms in the glossary; the fixed quickstart grep; the FR-025 coverage note; the advisory `evidence`; T001/T011 scoped).

Note on this feature's own test tasks: `plan.md` ("Test seams") still declares the whole change documentation/configuration-exempt with the reason stated and the canonical lines (FR-025, FR-020a), so every task is **excluded** from the seam-mapping and preceding-test-task checks rather than reported at a lower severity. No finding below is raised for the absence of test tasks.

The findings below are new, and all but one arise from the requirements the loop added (FR-011b, FR-013b, FR-015d–FR-015g, FR-020b).

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| D2 | Constitution Alignment | CRITICAL | tasks.md T002; plan.md "Project Structure" (`DESIGN.md` line), Summary; docs/adr/0004; spec.md FR-022 | Constitution I (MUST) requires every behaviour change to be recorded in `DESIGN.md` first. T002 is the only task that writes `DESIGN.md`, and its content list stops at the pass-1 scope: rules reference with `ENG-n` ids, red proof in the task commit, seams at plan time, enforcement by `code-standards`/`spec-conformance`/judge, and the `Overridden:` line, linking ADRs 0001–0003. None of the behaviour the loop added is in it: the `ENG-7`..`ENG-10` severity ceiling and the advisory no-fix route (FR-015f, FR-015g, ADR 0004), the stop on a test command that cannot be run (FR-011b, FR-013b), and the plan-time reason line with its MEDIUM non-blocking analyze check (FR-020b). ADR 0004 is not linked at all, although `plan.md` and `spec.md` both name it as a decision with lasting consequences. As planned, `core/` would carry behaviour `DESIGN.md` never records — the exact drift principle I forbids, and the one T013/quickstart step 7 cannot catch because they only grep for the section's existence. | Fix in `tasks.md` (never in the constitution): extend T002's content list with (a) the judgement-call ceiling and the advisory route, linking `docs/adr/0004-judgement-call-rules-advise-they-never-block.md`, (b) the un-runnable-test-command stop as a failure that rides the existing failure policy, binding both code-writing roles, and (c) the plan's reason line per new file/abstraction/dependency and analyze's MEDIUM non-blocking check. Update `plan.md`'s "Project Structure" annotation for `DESIGN.md` to the same list, and add the four ADR links (0001–0004) to T002. Optionally add "the section names the ceiling, the stop and the reason check" to quickstart step 7 so the inspection can see it. |
| I5 | Inconsistency / Conflicting requirement | HIGH | spec.md FR-015f (last clause) vs FR-015b, FR-015d, FR-020, SC-002, SC-006a; contracts/engineering-reference.md "Severity contract" row 2; tasks.md T007(d), T008, T010 | FR-015f states the ceiling and then adds: "only the duplication rule (`ENG-6`, FR-015) and behaviour added with no asserting test (FR-015a) carry HIGH and blocking weight". Taken as written that excludes the red-proof and seam findings the same feature makes HIGH and blocking: a missing, unparseable or unmatched `Red:` line (FR-015b, FR-015d, `ENG-2`) and an unmapped or unlisted seam (FR-020, `ENG-4`). `contracts/engineering-reference.md` contradicts it directly, giving `ENG-2`..`ENG-5` "Blocking? Yes". T007(d) writes the ceiling into `findings.md` as an override of that file's default severity guidance, so a reviewer reading the ceiling plus FR-015f's "only" clause has written authority to lower a missing-`Red:`-line finding to MEDIUM — which would silently disable the enforcement of US3 and SC-006a. | Narrow the clause in `spec.md` FR-015f to what it means: the ceiling applies to findings whose cited id is `ENG-7`..`ENG-10`, and findings resting on `ENG-1`..`ENG-6` keep the severity their own requirement states (HIGH and blocking for duplication, untested added behaviour, red-proof defects and seam defects). Say the same in one sentence in T007(d) so the text that lands in `findings.md` cannot be read as a blanket "only two things block", and keep `contracts/engineering-reference.md` row 2 as the authority it already is. |
| C2 | Inconsistency / Conflicting instruction | MEDIUM | tasks.md T005; spec.md FR-015g, US3 scenario 8, Assumptions; core/roles/fixer.md (existing "Work" step 2 and Inputs); core/skills/factory/SKILL.md step 7 ("Request changes") | FR-015g makes "Request changes" the user's route to having an advisory finding fixed, and the orchestrator implements that route by spawning the **same** `fixer` with the user's text ("implement exactly what it asks"). T005 tells `fixer.md` to "perform no fix work on an advisory engineering finding" with no scope on it. A fixer spawned with a change request that names an advisory finding then holds two contradictory instructions, and the stronger-sounding one is the new blanket prohibition — so the very route the spec relies on can be refused. | Scope the sentence in T005 (and in FR-015g's wording): no fix work on an advisory finding **in a fix round driven by a verdict**; a user change request that names one is implemented exactly as asked, like any other request. Mirror the scope in T007(e) and T010 so `findings.md` and the judge say the same. |
| U4 | Underspecification | MEDIUM | contracts/commit-body.md "The fix commit"; tasks.md T009; spec.md FR-013a, FR-015d; core/roles/fixer.md step 4 | The fix-commit verification path covers only the verdict-driven fix commit. The approver's "Request changes" produces a second kind — `factory(fix): user changes` — which re-runs review (`SKILL.md` step 7: "re-run step 6 from 1"), is behaviour-changing often enough that FR-013a demands a `Red:` line per fix, and matches no `confirmed_blocking` entry (the round `n-1` verdict for that re-review may be `pass` and carry none). The contract's table has no row for it, and T009's rule ("match one `Red:` line per behaviour-changing `confirmed_blocking` finding the commit fixes") decides nothing about it, so two agents will treat the same commit differently: one raises a missing-proof finding, the other raises nothing. | Add one row and one sentence: a fix commit whose subject names user changes (or whose round has no `confirmed_blocking` entries) is checked only for the **grammar** of any `Red:` line it carries and for one line per behaviour-changing fix the diff shows; it is never matched against `tasks.md` or the verdict, and an empty `confirmed_blocking` list is not by itself a finding. Put it in `contracts/commit-body.md` "The fix commit" and in T009. |
| I6 | Inconsistency | MEDIUM | spec.md Assumptions ("no new severity level or field is introduced"), FR-015g ("No new gate, list, severity or stage"); tasks.md T007(c), T015; data-model.md "Engineering finding"; core/skills/factory/references/findings.md "Judge verdict" | T007(c) adds an `evidence` field to the verdict's `advisory[]` entries, and `plan.md`/T015 still assert that no new field is added while an Assumption says it explicitly: "The existing judge verdict shape carries both; no new severity level or field is introduced." Verified against `findings.md`: an `advisory[]` entry today is `severity, file, line, summary, fix, sources`, and `sources` already points at the reviewer finding whose `evidence` carries the `ENG-n` id — so the citation is reachable without a new field (constitution V, reuse before adding). Either way, one of the two statements is wrong. | Decide and state it once. Cheapest and reuse-consistent: drop the new field from T007(c) and require instead that an advisory entry derived from an engineering finding names the `ENG-n` id in its `summary` (one token, no shape change), keeping `sources` as the link to the full evidence; then Assumptions and T015 stay true. If the field is kept, delete the "no new field" clause from Assumptions, from `plan.md`'s Constitution Check V and from T015, and justify the field in the plan's "Reasons for new files, abstractions and dependencies" table (`ENG-10`, FR-020b). |
| I7 | Inconsistency | MEDIUM | data-model.md "Engineering rules reference" (Fields) vs contracts/engineering-reference.md "Definitions the rule text carries" and tasks.md T003 | `data-model.md` says the reference carries "two one-sentence definitions ... **behaviour-changing** and **shared utility locations**". The contract and T003 require **three**: both of those plus "when the red step cannot be observed at all" (`ENG-1`, FR-011b/FR-013b). T013's inspection reads the contract, so the file that lands will have three and `data-model.md` will be stale — the same artifact drift pass 1 flagged as I4, in the other direction. | Add the third definition to `data-model.md`'s Fields list (one clause) so the entity description, the contract and T003 agree. |
| L6 | Inconsistency | LOW | spec.md Assumptions (last-but-two bullet) | "the three decisions with lasting consequences are recorded as `docs/adr/0001`... and `docs/adr/0003`... and `docs/adr/0004`..." — the count says three and the list names four (verified: all four ADR files exist). | Change "three" to "four" and join the list with commas. |
| L7 | Inconsistency / Terminology | LOW | contracts/commit-body.md "Placement" and "Verification by spec-conformance"; tasks.md T009 vs core/roles/fixer.md step 4 | The contract quotes the fix-commit subject as `factory(fix): <finding ids>`; the role actually writes `factory(fix): <finding ids, or "user changes">`. The prefix match still works, so nothing breaks, but the contract misquotes an existing shape it says it is pinning, and that is the shape U4's new row has to key on. | Quote the real subject in `contracts/commit-body.md` and in T009 (`factory(fix): <finding ids, or "user changes">`), which also gives U4's rule its discriminator. |
| L8 | Duplication | LOW | tasks.md T005; spec.md FR-015g; core/roles/fixer.md step 2 ("Advisory findings stay untouched") | `fixer.md` already states, in the file T005 edits, that advisory findings stay untouched. FR-015g's fix-round half is therefore an existing guarantee, and T005 adds a second sentence saying it again (T007(e) and T010 say it a third and fourth time). Constitution V asks for extension or reference rather than duplication, and four copies of one rule are four places to drift. | Keep the ceiling and the advisory lifecycle in `findings.md` only (T007(e)) and have T005 **extend** the existing sentence in `fixer.md` — qualifying it per C2 and pointing at `findings.md` — instead of adding a parallel statement. T010's mention can be a pointer too. |
| L9 | Underspecification | LOW | spec.md FR-020b, SC-003a; contracts/plan-artifact.md ("The run continues with the omission visible to the user"); core/skills/factory/SKILL.md step 4 | "Non-blocking" is claimed more strongly than the orchestrator behaves. Verified in `SKILL.md` step 4: "Only MEDIUM or LOW: run `remediate` once, then go to step 5." So a missing reason line does run the remediate stage, which fixes every finding at every severity — the reason gets written, and the user never sees the omission the contract promises to leave visible. The run is not halted and no loop is triggered, so FR-020b's normative text holds; only the "visible to the user" gloss is wrong. | Reword the gloss in `contracts/plan-artifact.md` (and the matching edge case in `spec.md`) to what actually happens: the finding never blocks the run and never triggers the analyze loop's blocking path; it is remediated once like any other MEDIUM finding, and it reaches the user through the analyze report rather than by surviving into the approved plan. |

No other finding reached the reporting threshold; no overflow.

## Coverage Summary

All 44 functional requirements (FR-001..FR-025 with the letter variants, including the five the loop added) map to at least one task; the 13 success criteria are addressed, with five deliberately deferred to the next real run.

| Requirement key | Has task? | Task IDs | Notes |
|---|---|---|---|
| FR-001, FR-002, FR-003, FR-006 | Yes | T003 | One self-contained, harness-neutral reference |
| FR-004 | Yes | T004, T005, T006, T008, T009, T010, T013 | Six roles reference it; T013 greps exactly those six |
| FR-004a | Yes | T003, T007(c), T008, T009, T010 | Ids defined once, cited in `evidence` (see I6) |
| FR-005 | Yes | T003 (`ENG-11`), T006(a) | `Overridden: ENG-n - ...` |
| FR-006a | Yes | T006(e), T013 | `.specify/` untouched is the check |
| FR-007, FR-008, FR-010, FR-011, FR-012 | Yes | T004 | Red-green-refactor, one commit, plan's seams only |
| FR-009, FR-009a | Yes | T003, T004 | Both accepted forms, no third form |
| FR-011a | Yes | T004, T005 | Stop-and-report rides the existing failure policy |
| FR-011b | Yes | T003 (definition), T004, T013 | Un-runnable test command is a stop, not an exemption |
| FR-013, FR-013a | Yes | T005, T009 | Verification path now exists; user-changes commit still open (U4) |
| FR-013b | Yes | T003, T005, T013 | Binds the fixing role on the same terms |
| FR-014, FR-014a | Yes | T003, T004, T005 | Bounded search, defined once |
| FR-015, FR-015a | Yes | T008 | HIGH and blocking |
| FR-015b | Yes | T007(a), T009 | Commit-log scope added |
| FR-015c | Yes | T010, T013 | Judge rates by id |
| FR-015d | Yes | T009 | Fix commit matched against the pinned verdict file (path verified in `SKILL.md` step 4) |
| FR-015e | Yes | T007(a), T007(b), T009 | Commit-log scope and commit-level finding shape |
| FR-015f | Yes | T007(d), T008, T010, T013 | Ceiling written as an explicit override; see I5 |
| FR-015g | Yes | T005, T007(e), T010, T013 | See C2 and L8 |
| FR-016, FR-017, FR-018, FR-019, FR-020, FR-020a, FR-021 | Yes | T006 | Three blocking conditions aligned with the contract |
| FR-020b | Yes | T006(a), T006(c), T013 | Plan reason line + MEDIUM non-blocking check; see L9 |
| FR-022 | Yes | T002, T013 | `DESIGN.md` leads — but its content list is short (D2) |
| FR-023 | Yes | T003..T011, T012 | Render per `core/`-editing task; drift proof |
| FR-024 | Yes | T003, T004, T006, T008, T014 | Writing Standards re-read |
| FR-025 | By artifact | (plan.md "Test seams") + T001, T012, T016 | Recorded in the `tasks.md` Coverage note |

| Success criterion | Has task? | Task IDs | Notes |
|---|---|---|---|
| SC-001 | Deferred | T016 | Observable on a real run |
| SC-002, SC-003 | Yes | T006 | |
| SC-003a | Yes (two legs) | T006, T013 (quickstart 10), T016 | Plan-side leg is this plan's own worked example |
| SC-004 | Yes | T003, T013, T014 | |
| SC-004a | Yes | T003, T007(c), T013 | See I6 |
| SC-005 | Yes | T001, T011, T012 | |
| SC-006, SC-006a | Deferred | T016 | Trial review needs a diff |
| SC-006b, SC-006c | Deferred | T016 | Ceiling and advisory behaviour observed in the trial review |
| SC-007 | Deferred | T016 | |

No post-launch or business-KPI criteria were counted.

## Constitution Alignment Issues

- **I. Design First** — violated by T002's content list and ADR links: finding **D2** (CRITICAL). Fixed in `tasks.md` and `plan.md`, never in the constitution.
- **III. Generated Dist (NON-NEGOTIABLE)** — pass 1's D1 is resolved: every `core/`-editing task renders all four harnesses and commits `dist/` in its own commit, `[P]` was removed from them, and T011/T012 close with the full render and the drift proof. PASS.
- II (Harness-Neutral Core): PASS — `engineering.md` and every role edit use `<F>/references/...` and the neutral verbs; `adapters/` and `tools/render.py` are untouched (T015).
- IV (Stateless Agents): PASS — every input is read from disk in one spawn, including the verdict file, whose path the orchestrator already writes and whose round the reviewer already receives (verified in `SKILL.md` steps 3–4).
- V (Simplicity and Reuse): weakened, not violated — **L8** (the advisory rule restated beside an identical existing sentence in `fixer.md`) and **I6** (a new verdict field where `sources` already reaches the citation). Both are fixable by reference.
- Writing Standards (one term per concept): PASS — pass 1's I1 drift is gone; `CONTEXT.md` now carries `behaviour-changing`, `advisory finding`, `red proof` with both forms, and the role names.
- Development Workflow: PASS — build and `git diff --exit-code -- dist/` are the stated verification; end-to-end validation is deferred per `DESIGN.md`.

## Unmapped Tasks

None. T013 (inspection), T014 (Writing Standards), T015 (untouched surface) and T016 (deferred end-to-end validation) each map to a stated requirement, success criterion, contract or constitution principle.

## Metrics

- Total requirements: 57 (44 FR + 13 SC)
- Total tasks: 16 (T001–T016)
- Coverage: 44/44 FR with >= 1 task (100%; FR-025 met by `plan.md` with verification tasks), 13/13 SC addressed (5 deliberately deferred to the next real run)
- Ambiguity count: 0 (pass 1's A1, A2 are defined and verified in the reference, the glossary and `spec.md`)
- Duplication count: 1 (L8)
- Inconsistency count: 5 (I5, I6, I7, L6, L7)
- Underspecification count: 2 (U4, L9)
- Critical issues: 1 (D2)
- By severity: CRITICAL 1, HIGH 1, MEDIUM 4, LOW 4 (10 total)
- Pass 1 findings resolved: 15 of 15

## Next Actions

1. **Resolve D2 before implement** — it is the NON-NEGOTIABLE-adjacent constitution I violation and is fixed entirely in `tasks.md` T002 plus the `DESIGN.md` annotation in `plan.md`: add the ceiling and advisory route (ADR 0004), the un-runnable-command stop and the plan-time reason check to the section T002 writes.
2. **Resolve I5** — narrow FR-015f's "only ... carry HIGH and blocking" clause to `ENG-7`..`ENG-10` and say so in T007(d); as written the ceiling text that lands in `findings.md` can be read as permission to downgrade red-proof and seam findings, which would disable US3's enforcement.
3. Fold C2, U4, I6 and I7 into the artifacts: scope the advisory no-fix rule to verdict-driven fix rounds, add the user-changes fix-commit row to `contracts/commit-body.md` and T009, settle the advisory-citation field question one way in `spec.md`/`tasks.md`/`data-model.md`, and add the third definition to `data-model.md`.
4. L6–L9 are wording and reuse improvements; L8 and I6 also tighten constitution V.
5. No finding requires a user decision: every one is a wording, scoping or task-content edit inside the artifacts. None is returned as `pending_clarify`, so remediation can proceed directly.
