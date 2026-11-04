# Specification Analysis Report: 020-post-pr-feedback, pass 2

This pass runs after the full-chain re-run (clarify Q10-Q14, grill-with-docs Q15-Q19, plan Q20, tasks). It checks `spec.md` (2988 words), `plan.md` (1999 words) and `tasks.md` (2490 words) against constitution 2.0.0. All three artifacts are within their word budgets (3000 / 2000 / 2500), but none has more than 12 words to spare. Remediation must therefore trim at least as many words as it adds.

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| G1 | Test scope (engineering.md "Confirmed test scope") | HIGH (blocking) | tasks.md:L104 (T009); plan.md:L170, L177; plan.md:L93 | T009 requires a test for an **unreadable** existing outcome file mapping to `inaccessible`. The S1 declaration (L170) and the Q20 `Confirmed:` scope (L177) list only a "malformed existing outcome file". The gap table (L93) and FR-012 do name "unreadable". This is the same table-versus-declaration drift that pass 1 found in G1. | Cheapest fix: change T009 to "a malformed existing outcome file". The confirmed scope then stays current and needs no new question. If "unreadable" must be tested, add it to the S1 declaration. That changes the scope, so a fresh `requires_user: true` confirmation is needed. |
| G2 | Test scope (engineering.md "Confirmed test scope") | HIGH (blocking) | tasks.md:L114 (T010); plan.md:L172, L177; plan.md:L152 | T010 asserts "Extra positional arguments exit 5" through S3. The S3 declaration and the confirmed scope list five failure paths, and none of them is a usage error. Exit 5 appears only in the CLI contract (L152). | Cheapest fix: drop the exit-5 assertion from T010. Exit 5 is the shared `die_usage` path in `cli.py`, so no new code needs this test. If the test should stay, declare the usage path on S3 and get a fresh `requires_user: true` confirmation. |
| I1 | Inconsistency / data integrity (ENG-26) | MEDIUM | spec.md:L141 (FR-012); plan.md:L94-L96, L137; tasks.md:L105 (T009 step 2) | FR-012 makes one exception to "nothing written": a failed **outcome-file** write after the backlog write. `add_feedback` writes one entry per signal key. If a backlog write fails with an I/O error (`OSError` raised as `AddError`) partway through, entries already written for that run remain. Neither the spec nor the plan's gap table covers this case or gives it a class. T009 step 2 sends it to `inaccessible` implicitly ("other `AddError` refusals"). Recovery is the same idempotent re-run as for the outcome-write case. | Widen FR-012's exception to any write failure after a backlog write: links already written stay, and the next refresh does not duplicate them. Add a gap-table row "backlog write fails -> `transient`" or "`inaccessible`", choosing one. Do not add a test path, because that would change the confirmed scope. |
| U1 | Underspecification | LOW | plan.md:L106; tasks.md:L47 (T003) | The `url` (evidence link) of the `state:merged` and `state:closed` outcomes is never stated. Read 1 fetches the PR `url`, but neither the capture rules nor T003 say it is the state outcome's `url`. The `pr-closed:unmerged` entry's evidence comes from this field. | Add "`url` = read 1 `url`" to plan L106 and the T003 `MERGED`/`CLOSED` assertion. |
| T1 | Inconsistency (terminology drift) | LOW | plan.md:L119; tasks.md:L35 (T001), L66 (T005); CONTEXT.md "PR outcome" | Grill Q15 settled on "PR outcome" and lists "outcome record" under `_Avoid_`. The plan still says "Records are append-only", and T001/T005 say "record fields", "a stored record", "adds one record" and "a record appended". | Replace "record(s)" with "outcome(s)" or "PR outcome(s)" in these places. |

## Analyze-1 findings: status

| Pass-1 ID | Status | Evidence |
|-----------|--------|----------|
| G1 (S1 missing foreign backlog file + outcome-write failure) | Resolved | S1 now declares both, with the `_write_atomic` patch injection (plan.md:L168, L170). Both are confirmed in Q20 (L177). T009 maps them. |
| G2 (`<branch>` refusals tested on S1, declared only on S3) | Resolved | Both refusals are declared on S1 (L170) and confirmed (L177). T004 maps them. |
| I1 (write order versus "nothing written on outcomes-lock timeout") | Resolved | FR-010 sets the order: outcomes lock first, then the nested backlog lock, then the outcome write (spec.md:L139; plan.md:L137). The FR-012 exception covers the failed outcome write. T009 matches. |
| I2 (local gap classes missing from spec) | Resolved | FR-012 lists the local classes (spec.md:L141). The edge case at L120 gives the class. |
| I3 (exit 1 on refused `<branch>`, `skipped` list) | Resolved | FR-013 (spec.md:L142); Key Entities "Skipped run" (L153). |
| C1 (`improve` route lacks `kind`/`signal_key`) | Resolved | plan.md:L156; T011 extends the `improve` route. |
| C2 (`--repo` not implemented) | Resolved | FR-001; plan.md:L152, L172; T010 (`value_flags=("--repo",)`, plus a test). |
| U1 (null login / non-`CHANGES_REQUESTED` review shape) | Resolved | FR-004; spec Q13; plan.md:L92, L105; T003 and T008. |
| A1 (slug rule in spec) | Resolved | spec.md:L168. |
| A2 ("fixed number of reads") | Resolved | spec.md:L170. |
| U2 (reopened PR limitation) | Resolved | plan.md:L164; T001; ADR 0014 Consequences. |
| U3 (`ERROR` status contexts) | Resolved | plan.md:L103, L164; T001. |
| U4 (unreadable archive silent) | Resolved | It is now listed under `skipped` (plan.md:L71; FR-013; T003), and the S1 path is declared. |
| F1 (`evidence` type differs per kind) | Resolved | plan.md:L133; T001; T002 adds the type to `CONTEXT.md`. |
| I4 (`test_improvements.py` missing from structure) | Resolved | plan.md:L53. |
| I5 (T013 exemption undeclared) | Resolved | plan.md:L174 declares the final-verification exemption; the confirmed scope lists it. |

## Test-scope check (factory override)

- **Declarations.** The plan declares three seams: S1 `factory_cli.feedback.refresh`, S2 `factory_cli.improvements` feedback entries, and S3 `bin/factory feedback [<branch>] [--repo <path>]`. Each has explicit failure paths. The two `Exempt:` lines cover the four documentation files and the final verification task. The plan also records `Overridden: none`.
- **Confirmation.**
  - `Confirmed: 2026-11-04 - Q20 accepted` (plan.md:L177) stores the full seam-to-failure-path scope.
  - `state.decisions` records plan Q20 = `A` with `auto: false`, which is explicit user acceptance.
  - The stored scope matches the current S1/S2/S3 declarations and exemptions item for item.
  - The relay kept only the id of Q20, so the question text itself cannot be cross-checked. The scope stored on the `Confirmed:` line is the evidence.
- **Task mapping.**
  - T003-T010 each map to one declared seam.
  - Each task carries ordered failing-test, implementation and passing-check steps, a `Red:` proof and a done condition.
- **Uncovered paths:**
  - **T009:** the "unreadable" outcome file (G1).
  - **T010:** usage exit 5 (G2).
  - All other failure paths required by tasks are declared and confirmed. For example: T003 unreadable archive; T004 refusals; T006 foreign/unreadable entry and backlog lock; T008 the GitHub classes and unparseable `pr_url`; T009 foreign backlog file, both locks and the patched outcome write; T010 the five S3 paths.
- **Exempt tasks.** T001, T002, T011, T012 and T013 are plan-exempt and are excluded from this check.

## ENG-10 new-code reasons

Every new item has a stated reason at plan.md:L58-L65:

- **Files:** `feedback.py`, `test_feedback.py`.
- **Abstractions:** `run_gh`, `Gap`, `add_feedback`.
- **Dependencies:** none.

The `_acquire_backlog_lock` → `_acquire_home_lock` generalisation has its reason at L139. The new `outcomes/` storage traces to Q3 and ADR 0014. There are no findings.

## Coverage Summary

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 command, `--repo`, route | Yes | T010, T011, T012 | |
| FR-002 discovery, repo match, narrowing, terminal skip | Yes | T003, T004, T005 | |
| FR-003 read-only reads | Yes | T003 | exact runner arguments asserted |
| FR-004 capture/ignore, malformed review, `ghost` | Yes | T003, T008 | |
| FR-005 ids and fields | Yes | T003 | state `url` source (U1) |
| FR-006 outcome file, atomic, archive unchanged | Yes | T003, T005 | |
| FR-007 stored id unchanged | Yes | T005 | |
| FR-008 signal keys, merged not actionable | Yes | T007 | |
| FR-009 one entry per run/key, ready/claimed, no cap | Yes | T006, T007 | |
| FR-010 entry body, template, lock order | Yes | T006, T007, T009 | |
| FR-011 listing/claim, regressions | Yes | T006, T011 | |
| FR-012 gap classification | Yes | T008, T009 | I1, G1 |
| FR-013 JSON, `skipped`, exit codes, no retry | Yes | T003, T005, T008, T010 | G2 |
| FR-014 injectable runner, no credentials | Yes | T003, T010 | |
| FR-015 design first, harness-neutral | Yes | T001, T011, T013 | |
| SC-001 | Yes | T003 | |
| SC-002 | Yes | T005, T007 | |
| SC-003 | Yes | T008, T009 | |
| SC-004 | Yes | T006, T007 | |
| SC-005 | Yes | T003 | |

**Constitution Alignment Issues:** none.
- **I. Design First:** T001 runs first and the other tasks depend on it.
- **II. Harness-Neutral Core:** the route uses only `SHELL`.
- **III. Generated Dist:** the build command runs in T003, T010 and T013.
- **IV. Stateless Agents:** no agent is spawned.
- **V. Simplicity and Reuse:** every new item has a stated reason, and existing helpers are reused.

**Unmapped Tasks:** none.

## Metrics

- Total requirements: 20 (15 FR, 5 SC)
- Total tasks: 13
- Coverage: 100% (20/20 have at least one task)
- Ambiguity count: 0
- Duplication count: 0
- Critical issues: 0
- Severity counts: CRITICAL 0, HIGH 2, MEDIUM 1, LOW 2

## Next actions

G1 and G2 block implementation. Both can be fixed in `tasks.md` alone by narrowing T009 and T010 to the confirmed scope. That avoids a new scope confirmation. Declaring either path instead invalidates Q20 and needs fresh `requires_user: true` acceptance.

Fix I1, U1 and T1 with targeted edits in the same pass, and stay within the word budgets: spec 12, plan 1 and tasks 10 words remain.
