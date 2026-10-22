# Specification Analysis Report — pass 3

**Feature**: `001-tdd-engineering-rules` — Engineering discipline for factory code-writing roles
**Artifacts**: `spec.md`, `plan.md`, `tasks.md`, `research.md`, `data-model.md`, `contracts/{engineering-reference,commit-body,plan-artifact}.md`, `quickstart.md`, `checklists/requirements.md`, plus the repository documents this run authored (`CONTEXT.md`, `docs/adr/0001`..`0004`)
**Constitution**: `.specify/memory/constitution.md` v1.0.0
**Previous passes**: [analyze-1.md](./analyze-1.md), [analyze-2.md](./analyze-2.md); remediation: [remediation-1.md](./remediation-1.md), [remediation-2.md](./remediation-2.md)
**Mode**: read-only. No artifact was modified.

## Status of pass 2

All 10 findings of pass 2 (D2, I5, C2, U4, I6, I7, L6–L9) were re-checked against the regenerated artifacts and every one is fixed:

- **D2** (CRITICAL, constitution I) — `tasks.md` T002 now records in `DESIGN.md`: the `ENG-7`..`ENG-10` ceiling with the advisory route (lowered not dropped, no verdict-driven fix work, "Request changes" as the user's route), the stop on a test command that cannot be run binding both code-writing roles, and the plan-time reason line with analyze's MEDIUM non-blocking check; it links all four ADRs. `plan.md`'s "Project Structure" `DESIGN.md` annotation and Constitution Check I carry the same list; `quickstart.md` step 7 gained the expectation plus the `grep -n 'ENG-7\|advisory\|cannot be run\|reason\|adr/000' DESIGN.md` check, cited by T013. Verified that `DESIGN.md` really has `## Decisions` and `## Validation plan`, so T002's insertion point exists. No behaviour now reaches `core/` unrecorded. PASS.
- **I5** (HIGH) — FR-015f is keyed on the cited id, lists what `ENG-1`..`ENG-6` keep (HIGH and blocking for duplication, untested added behaviour, `Red:`-line defects, seam defects) and closes with "MUST NOT be read as licence to lower any other engineering finding". T007(d) requires the limit sentence in `findings.md` beside the ceiling, as an explicit override of that file's own default guidance (verified: `core/skills/factory/references/findings.md` does carry "`critical` and `high` are blocking unless the reviewer says why not"). Mirrored in `data-model.md`, `contracts/engineering-reference.md` row 3, `quickstart.md` step 9, ADR 0004.
- **C2** (MEDIUM) — the no-fix rule is scoped to a **verdict-driven fix round** everywhere (FR-015g, US3 scenario 8, T005, T007(e), T009, T010, `CONTEXT.md`), and a change request naming an advisory finding is implemented as asked. Verified against `core/roles/fixer.md` step 2 and `core/skills/factory/SKILL.md` step 7: the same `fixer` serves both routes, so the scope was the right fix.
- **U4** (MEDIUM) — `contracts/commit-body.md` now has the "A user-changes fix round's commit" subsection with its own table and the grammar/per-fix-presence rule; the same rule is in FR-015d, T009, `data-model.md` and `plan.md`'s `spec-conformance.md` annotation.
- **I6** (MEDIUM) — no verdict field was added. Verified against `findings.md`: an `advisory[]` entry is `severity, file, line, summary, fix, sources`, and T007(c)/T010 keep the `ENG-n` id in `summary` with `sources` as the link. `spec.md` Assumptions, `plan.md` Constitution Check V and T015 are now true.
- **I7** (MEDIUM) — `data-model.md` "Engineering rules reference" lists three definitions, matching the contract and T003 (but see **L12** for the stale count word left in T003).
- **L6** — Assumptions say "the four decisions", comma-joined. **L7** — `factory(fix): <finding ids, or "user changes">` is quoted in the contract and T009. **L8** — T005 extends `fixer.md`'s existing sentence, and the lifecycle lives in `findings.md` only (T007(e)). **L9** — the non-blocking gloss now says "remediated once like any other MEDIUM finding … reaches the user through the analyze report", which matches `SKILL.md` step 4.

Note on this feature's own test tasks: `plan.md` ("Test seams") still declares the whole change documentation/configuration-exempt (FR-025, FR-020a) with the reason stated and the canonical `Exempt:`/`Overridden:` lines, and all sixteen tasks name that exemption in their text. Every task is therefore **excluded** from the seam-mapping and preceding-test-task checks rather than reported at a lower severity, and no finding below is raised for the absence of test tasks.

The findings below are new. Two come from checking the artifacts against the orchestrator flow they rely on (`core/skills/factory/SKILL.md`), and the rest are wording or verification-strength defects.

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| I8 | Inconsistency / Underspecification | HIGH | spec.md FR-015d, US3 scenario 6, the fix-commit edge case; contracts/commit-body.md "Verification by spec-conformance" + "The fix commit (two kinds of fix round)"; tasks.md T009; data-model.md "Red proof"; research.md D12, D13; core/skills/factory/SKILL.md step 6.5 and step 7 | The whole fix-commit rule assumes a run has **one** fix commit, and keys its verdict on the reviewer's current round: "the one whose subject is `factory(fix): …` **is the** fix commit" (T009), matched against `<spec_dir>/factory/reviews/round-<n-1>/verdict.json`, with "in round 1 there is no fix commit and no such file". The orchestrator produces more than one: step 6.5 repeats the review step with the next round number for up to two verdict-driven fix rounds (`review.fix_rounds < 2`), and step 7's "Request changes" spawns `fixer` again and re-runs step 6 — every one of those commits stays in `<base>..HEAD` for all later rounds. So a reviewer in round 3 sees the round-1 fix commit and the round-2 fix commit, and the `n-1` rule points both at the round-2 verdict: the round-1 commit's `Red:` lines name tests for findings that verdict never lists, and its own confirmed findings have no line to match, so the reviewer raises spurious "missing `Red:` line for finding X" findings or silently checks nothing. The contract's own promise — "A fix commit **is** checked, whichever round produced it (FR-013a would otherwise be unverifiable)" — fails for every fix commit but the most recent, and the "round 1 has no fix commit" sentence is false in a post-"Request changes" re-review. | Key each fix commit to **its own** verdict instead of to the reviewer's round. In `spec.md` FR-015d, `contracts/commit-body.md`, `tasks.md` T009, `data-model.md` "Red proof" and `research.md` D12: say "each fix commit in the run's commit log" (plural), and have the reviewer pick, for a verdict-driven fix commit, the verdict under `<spec_dir>/factory/reviews/round-*/verdict.json` whose `confirmed_blocking` entries carry the finding ids the commit's subject names (the subject is already the discriminator, L7); when no such verdict file exists or none of the subject's ids is found in any of them, fall back to the user-changes rows (grammar plus one line per behaviour-changing fix in that commit's own diff) rather than raising an unmatched finding. Drop or correct the "in round 1 there is no fix commit" sentence in the contract, T009 and research D12. |
| U5 | Underspecification | MEDIUM | spec.md FR-007, FR-011b, FR-013b, SC-001; tasks.md T004, T005; contracts/engineering-reference.md "When the red step cannot be observed at all"; research.md D10 (un-runnable test command); core/roles/code-build.md step 3, core/roles/fixer.md step 3 | No artifact says **which command** a role runs to observe the red step, although the stop of FR-011b/FR-013b is defined entirely in terms of "its test command". The only test command either role has is `commands.test` from its inputs, which both roles today run once at the end of their work, not per task; T004 and T005 say "write or extend a test, run it and observe it fail" and never name a command or allow a narrowed invocation. Two agents will therefore differ on the trigger: one runs `commands.test` whole and treats any non-zero exit as the red step (so an unrelated pre-existing failure reads as red), another invents a focused runner invocation (`pytest <file>::<test>`-style) that the artifacts never sanction, and a third reads a plain test failure as "cannot be run" and halts the run. SC-001's "100% of behaviour-changing tasks have a red proof" is unverifiable while the observation itself is undefined. | State it once, in the third definition of `contracts/engineering-reference.md` (which T003 copies into `engineering.md`) and in T004/T005: the role observes red by running `commands.test`, narrowed to the new or changed test where the runner supports selecting one, and the proof names that test; "cannot be run" means that command (or its narrowed form) **fails to execute** — missing dependency, broken configuration, no runner binary — and a test that runs and fails is the red step, never a stop. Add the same sentence to FR-011b (or to the Assumption that already describes the stop) so the requirement and the rule text agree. |
| L10 | Inconsistency / Terminology | LOW | spec.md FR-015g; data-model.md "Advisory lifecycle"; CONTEXT.md "Advisory finding"; contracts/engineering-reference.md severity bullet | After I5 keyed the ceiling on the cited id, FR-015g still identifies an advisory finding by **severity**: "An engineering finding held at or below the FR-015f ceiling is advisory"; `data-model.md` repeats "a finding held at or below the ceiling". Read literally that covers a MEDIUM or LOW finding citing `ENG-1`..`ENG-6`, which `CONTEXT.md` ("resting on a judgement-call rule (`ENG-7`..`ENG-10`)") and the contract's id-keyed row do not. The practical effect is small — the fixer only works `confirmed_blocking` — but it is the same severity-vs-id confusion I5 removed, re-entering through the definition of "advisory". | Identify it by id in both places: "An engineering finding whose cited id is `ENG-7`..`ENG-10`, and which the ceiling therefore caps at MEDIUM, is advisory", matching `CONTEXT.md` and `contracts/engineering-reference.md`. |
| L11 | Underspecification / Verification strength | LOW | quickstart.md steps 7 and 10; tasks.md T013 | The greps that prove the three `DESIGN.md` additions and the two role stops are file-wide and use very common words: `grep -n 'ENG-7\|advisory\|cannot be run\|reason\|adr/000' DESIGN.md` passes on any `reason` anywhere in a 120-line design document, and `grep -n 'reason\|new file\|dependency' core/roles/spec-builder.md` / `grep -n 'cannot be run\|un-runnable\|failed' core/roles/code-build.md core/roles/fixer.md` match words both files already contain (`failed` is in `code-build.md` and `fixer.md` today). The inspection that D2 was fixed to enable can pass without the new content being present or in the right section. | Anchor the checks: read the section before grepping (`sed -n '/^## Engineering discipline/,/^## /p' DESIGN.md \| grep -n 'ENG-7\|advisory\|cannot be run\|adr/000'`) and grep for distinguishing phrases rather than single words (`un-runnable`/`cannot be run` **with** `red step`, `new file, new abstraction and new dependency`, `MEDIUM`/`non-blocking`). Update T013's restatement to match. |
| L12 | Inconsistency | LOW | tasks.md T003 ("The file also carries the two definitions …") vs contracts/engineering-reference.md "Definitions the rule text carries", data-model.md "Engineering rules reference" | I7's fix added the third definition to the contract and to `data-model.md`, and T003's enumeration does list all three ("and **when the red step cannot be observed at all** (the third definition of that block …)"), but the sentence still opens "the **two** definitions … one sentence each". The count contradicts the list immediately after it, and the same count error is what L6 corrected in Assumptions. | Change "the two definitions" to "the three definitions" in T003. |
| L13 | Duplication | LOW | tasks.md T013 vs quickstart.md steps 3, 4, 5, 7, 8, 9, 10 | T013 says "Run the inspection checks of quickstart.md steps 3, 4, 5, 7, 8, 9 and 10" and then restates every one of those commands and expectations in a single paragraph. Two copies of the same seven checks are two places to drift (constitution V asks for reference over duplication), and L11's fix would have to be applied twice. | Keep the commands and expectations in `quickstart.md` only and let T013 name the steps plus the requirement ids they prove (`SC-004`, `SC-004a`, `FR-004`, `FR-022`, `FR-006a`, `FR-015f`, `FR-015g`, `FR-020b`, `FR-011b`, `FR-013b`), as T012 already does for steps 1, 2 and 6. |

No other finding reached the reporting threshold; no overflow.

## Coverage Summary

Unchanged from pass 2 in structure: remediation 2 added no requirement (FR-015f and FR-015g were narrowed in place), so all 44 functional requirements map to at least one task and all 13 success criteria are addressed, five deliberately deferred to the next real run.

| Requirement key | Has task? | Task IDs | Notes |
|---|---|---|---|
| FR-001, FR-002, FR-003, FR-006 | Yes | T003 | One self-contained, harness-neutral reference |
| FR-004 | Yes | T004, T005, T006, T008, T009, T010, T013 | Six roles reference it; T013/quickstart 5 grep exactly those six |
| FR-004a | Yes | T003, T007(c), T008, T009, T010 | Id cited in the existing `evidence` field (verified present in `findings.md`) |
| FR-005 | Yes | T003 (`ENG-11`), T006(a) | `Overridden: ENG-n - ...` |
| FR-006a | Yes | T006(e), T013 | `.specify/` untouched is the check |
| FR-007, FR-008, FR-010, FR-011, FR-012 | Yes | T004 | Red-green-refactor, one commit, the plan's seams only; the red-observation command is undefined (U5) |
| FR-009, FR-009a | Yes | T003, T004 | Both accepted forms, no third form |
| FR-011a | Yes | T004, T005 | Stop-and-report rides the existing failure policy |
| FR-011b | Yes | T003 (definition), T004, T013 | Stop, not an exemption; trigger command undefined (U5) |
| FR-013, FR-013a | Yes | T005, T009 | Verification path exists for one fix commit only (I8) |
| FR-013b | Yes | T003, T005, T013 | Binds the fixing role on the same terms (U5 applies) |
| FR-014, FR-014a | Yes | T003, T004, T005 | Bounded search, defined once |
| FR-015, FR-015a | Yes | T008 | HIGH and blocking |
| FR-015b | Yes | T007(a), T009 | Commit-log scope present |
| FR-015c | Yes | T010, T013 | Judge rates by id |
| FR-015d | Yes | T009 | Both kinds of fix round covered; multi-fix-commit keying broken (I8) |
| FR-015e | Yes | T007(a), T007(b), T009 | Commit-log scope and commit-level finding shape |
| FR-015f | Yes | T007(d), T008, T010, T013 | Ceiling keyed on the cited id, written as an explicit override |
| FR-015g | Yes | T005, T007(e), T010, T013 | Scoped to verdict-driven fix rounds; identified by severity in one place (L10) |
| FR-016, FR-017, FR-018, FR-019, FR-020, FR-020a, FR-021 | Yes | T006 | Three blocking conditions aligned with the contract |
| FR-020b | Yes | T006(a), T006(c), T013 | Reason line + MEDIUM non-blocking check; L11 weakens the inspection |
| FR-022 | Yes | T002, T013 | `DESIGN.md` leads, with the full content list (D2 fixed) |
| FR-023 | Yes | T003..T011, T012 | Per-task render; drift proof |
| FR-024 | Yes | T003, T004, T006, T008, T014 | Writing Standards re-read |
| FR-025 | By artifact | (plan.md "Test seams") + T001, T012, T016 | Recorded in the `tasks.md` coverage note |

| Success criterion | Has task? | Task IDs | Notes |
|---|---|---|---|
| SC-001 | Deferred | T016 | Observable on a real run; U5 must be settled for it to be checkable |
| SC-002, SC-003 | Yes | T006 | |
| SC-003a | Yes (two legs) | T006, T013 (quickstart 10), T016 | Plan-side leg is this plan's own worked example |
| SC-004 | Yes | T003, T013, T014 | |
| SC-004a | Yes | T003, T007(c), T013 | |
| SC-005 | Yes | T001, T011, T012 | |
| SC-006, SC-006a | Deferred | T016 | Trial review needs a diff |
| SC-006b, SC-006c | Deferred | T016 | Ceiling and advisory behaviour observed in the trial review |
| SC-007 | Deferred | T016 | |

No post-launch or business-KPI criteria were counted.

## Constitution Alignment Issues

None. No finding in this pass is a constitution violation.

- **I. Design First** — PASS. Pass 2's D2 is resolved: T002's content list covers every behaviour the loop added and links `docs/adr/0001`..`0004`; `plan.md`'s annotation and Constitution Check I say the same; the insertion point (`## Decisions` → `## Validation plan`) exists in `DESIGN.md`. L11 only weakens the *inspection* of this, not the record itself.
- **II. Harness-Neutral Core** — PASS. `engineering.md` and every role edit use `<F>/references/...` and the neutral verbs; `adapters/` and `tools/render.py` stay untouched (T015).
- **III. Generated Dist (NON-NEGOTIABLE)** — PASS. Every `core/`-editing task renders all four harnesses and commits `dist/` in its own commit, none of them is `[P]`, and T011/T012 close with the full render and the drift proof.
- **IV. Stateless Agents** — PASS for every input the artifacts name: the rules, the seams, the commit log and the verdict file are all read from disk in one spawn, and the reviewer already receives `spec_dir` and the round (verified in `SKILL.md` step 6.3). I8 is a keying defect in which verdict file to read, not a statelessness defect.
- **V. Simplicity and Reuse** — PASS, weakened by **L13** (T013 restating quickstart's seven checks). No new file, verb, field, severity, gate or list is added; pass 2's I6 and L8 stay fixed.
- **Writing Standards** — PASS, with **L10** and **L12** as wording defects (one term per concept for "advisory", a stale count in T003). `CONTEXT.md` carries `red proof`, `behaviour-changing`, `advisory finding`, `verdict-driven fix round` and `user-changes fix round`, and T014 checks their use.
- **Development Workflow** — PASS. `commands.build` and `git diff --exit-code -- dist/` are the stated verification; end-to-end validation is deferred per `DESIGN.md`.

## Unmapped Tasks

None. T013 (inspection), T014 (Writing Standards), T015 (untouched surface) and T016 (deferred end-to-end validation) each map to a stated requirement, success criterion, contract or constitution principle.

## Metrics

- Total requirements: 57 (44 FR + 13 SC)
- Total tasks: 16 (T001–T016)
- Coverage: 44/44 FR with >= 1 task (100%; FR-025 met by `plan.md` with verification tasks), 13/13 SC addressed (5 deliberately deferred to the next real run)
- Ambiguity count: 1 (U5 — the red-observation command)
- Duplication count: 1 (L13)
- Inconsistency count: 3 (I8, L10, L12)
- Underspecification count: 2 (U5, L11)
- Critical issues: 0
- By severity: CRITICAL 0, HIGH 1, MEDIUM 1, LOW 4 (6 total)
- Pass 2 findings resolved: 10 of 10 (pass 1: 15 of 15, still holding)

## Next Actions

1. **Resolve I8 before implement** — it is the only HIGH finding and the only one that would make a shipped instruction misbehave: key each fix commit to the verdict whose `confirmed_blocking` ids its subject names, make the rule plural, and give it the user-changes fallback when no such verdict exists. Edit `spec.md` FR-015d, `contracts/commit-body.md`, `tasks.md` T009, `data-model.md` and `research.md` D12.
2. **Resolve U5** — name the command the red step is observed with (`commands.test`, narrowed where the runner allows) and separate "fails to execute" from "a test failed", in `contracts/engineering-reference.md`'s third definition, T004, T005 and FR-011b.
3. Fold L10–L13 into the artifacts: id-key the definition of "advisory", anchor and sharpen the quickstart greps, fix T003's "two definitions", and let T013 point at `quickstart.md` instead of restating it.
4. No finding requires a user decision: each is a wording, keying or task-content edit inside the artifacts, and the fallback I8 recommends follows the rule remediation 2 already settled for a commit that answers no verdict. None is returned as `pending_clarify`, so remediation can proceed directly.
