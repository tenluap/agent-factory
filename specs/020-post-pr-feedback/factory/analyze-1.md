# Specification Analysis Report — 020-post-pr-feedback, pass 1

Artifacts: `spec.md` (2546 words), `plan.md` (1972 words), `tasks.md` (2494 words). Constitution 2.0.0. All three artifacts are within their word budgets (3000 / 2000 / 2500).

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| G1 | Test scope (engineering.md "Confirmed test scope") | HIGH (blocking) | tasks.md:L108 (T009); plan.md:L93, L164, L170 | T009 requires two S1 (`factory_cli.feedback.refresh`) failure paths that the S1 declaration and its `Confirmed:` scope do not list. (a) A foreign or unreadable backlog file at the entry name → `inaccessible`, with both files untouched. The gap table at L93 lists this, but S1 at L164 does not. (b) An outcome write that fails after the backlog write succeeded. This needs an injected write failure (for example patching `improvements._write_atomic`), and that injection point is not declared anywhere (ENG-4). | Add both paths, and the way the write failure is injected, to the S1 declaration. Otherwise drop them from T009. Either way the seam scope changes, so a fresh `requires_user: true` scope confirmation is needed. |
| G2 | Test scope (engineering.md "Confirmed test scope") | HIGH (blocking) | tasks.md:L54 (T004); plan.md:L164, L166, L170 | T004 tests "`<branch>` naming no archived run" and "`<branch>` without `pr_url`" (raise `ValueError`, runner never called, nothing written) and labels them S1 failure paths. The plan declares and confirms these paths only on S3, the CLI. S1's declared failure paths do not include them. | Add both refusals to S1's declared failure paths and re-confirm them together with G1. Otherwise re-word T004 so it tests narrowing behaviour only and leaves the refusals to T010/S3. |
| I1 | Inconsistency / data integrity (ENG-26) | HIGH | plan.md:L134, L94; tasks.md:L108 (T009); spec.md:L127 (FR-012) | The plan's write order is `add_feedback` under the backlog lock first, then the outcome write under the outcomes lock. If the outcomes lock is held past the 5 s wait, the backlog entry has therefore already been written. T009 expects "outcomes lock held past the 5 s wait -> `transient`, nothing written for that run", and FR-012 requires that nothing is written for an affected run. A correct implementation of the plan cannot pass T009's test. | Pick one rule and apply it in plan and tasks. Option 1: take the outcomes lock first (re-read, compute new ids), then run `add_feedback` under the backlog lock, nested in the fixed order outcomes→improvements. Retro `add` and `claim` take only the backlog lock, so this order cannot deadlock. Write the outcomes last. Option 2: state in the plan and spec that an outcomes-lock timeout can leave backlog links written (they are idempotent on the next refresh), and amend T009's expectation to match. |
| I2 | Inconsistency | MEDIUM | spec.md:L105, L127, L152; plan.md:L91-L94 | Spec FR-012 and the Assumptions define gap classes only for GitHub fetch problems. The plan adds classes for local and other failures: unparseable `pr_url` → `missing`, malformed outcome file → `inaccessible`, foreign or unreadable backlog file → `inaccessible`, lock held → `transient`. The spec edge case at L105 says "reported as a gap" without a class. | Add the local-failure mappings to the spec's Assumptions gap-class line and the L105 edge case. |
| I3 | Inconsistency | MEDIUM | spec.md:L103, L128 (FR-013); plan.md:L145, L149 | FR-013 says to exit 1 "when any gap exists and 0 otherwise", and the output names refreshed runs and gaps. The plan also exits 1 for a refused `<branch>`, which is not a gap, so FR-013 as written would require exit 0. The plan also adds a `skipped` list to the report. | Amend FR-013 and the L103 edge case: a refused `<branch>` exits 1, and the report includes `skipped` runs with their reason. |
| C1 | Coverage gap | MEDIUM | spec.md:L79 (US3 AS7); core/skills/factory/SKILL.md:L30; tasks.md:L84, L122 | US3 AS7 says the backlog listing shows the entry's `kind`, `signal_key` and suggested feature. T006 covers the `list_backlogs` JSON, which already carries these fields. The user-facing `improve` route shows "name, run, kind counts and `suggested_feature`" and no task changes it. A `feedback` entry would show empty kind counts and no `kind` or `signal_key`. | Extend T011 (documentation-exempt) so the `improve` route also shows `kind` and `signal_key`. Otherwise narrow AS7 to the JSON listing. |
| C2 | Coverage gap | MEDIUM | plan.md:L140; tasks.md:L35 (T001), L118-L119 (T010) | The plan's CLI contract, and T001's design text, give `factory feedback [<branch>] [--repo <path>]`. T010 does not parse, implement or test `--repo`, and its dispatch and USAGE text name only `feedback [<branch>]`. | Add `--repo` parsing to T010, following the existing `value_flags=("--repo",)` convention, plus one S3 test. Otherwise remove `--repo` from the plan and T001. |
| U1 | Underspecification / correctness | MEDIUM | plan.md:L79, L91; tasks.md:L103 (T008) | Any review without an integer `id` or a string `state`/`user` is treated as malformed, which makes the whole run a `transient` gap. GitHub returns `user: null` for deleted accounts, so the `--jq` projection gives `user: null`. One such review, in any state including `APPROVED`, would make the run a permanent gap: exit 1 on every refresh, and its failed checks and change requests never recorded. | Validate shape strictly only for `CHANGES_REQUESTED` reviews, and map a null login to a fixed placeholder (for example `ghost`) rather than raising a gap. Add the case to T008 under the existing malformed-response path, or as capture behaviour in T003. |
| A1 | Inconsistency (terminology drift) | LOW | spec.md:L154; plan.md:L128; tasks.md:L89 | The spec's slug assumption leaves out the trimming, the 64-character cap and the `unnamed` fallback that the plan and T007 require. | Align the spec's Assumptions with the plan's slug rule. |
| A2 | Ambiguity | LOW | spec.md:L156; plan.md:L25, L79 | The spec says "a small, fixed number of GitHub reads". The plan's reviews read uses `--paginate`, so its cost grows with the number of review pages. | Re-word it as "two `gh` calls per run; reviews paginated". |
| U2 | Underspecification | LOW | spec.md:L117 (FR-002); plan.md:L73 | A PR that was closed and then reopened is never fetched again once `state:closed` is recorded. This follows settled decision Q2 but is not recorded as a known limitation. | Note the limitation in T001's `DESIGN.md` subsection. |
| U3 | Underspecification | LOW | plan.md:L101; spec.md:L119 (FR-004) | Status contexts in state `ERROR` are ignored. This is consistent with Q4, but CI that only posts status contexts may report errors that are then lost. | Record the choice in T001's `DESIGN.md` subsection so it is visible. |
| U4 | Underspecification / observability | LOW | plan.md:L70 | An unreadable archive `state.json` is skipped silently. If that run has a `pr_url`, it disappears from the report and is neither listed under `gaps` nor `skipped`. | List skipped unreadable archives under `skipped` with their reason, or state in the spec why they are silent. |
| F1 | Inconsistency (field drift) | LOW | plan.md:L123; tasks.md:L84 | `evidence` is a string on Retro entries and a list on Feedback entries. The field has the same name and a different type in one backlog directory. No current reader (`list_backlogs`, the `improve` route) uses it. | Note the per-kind type in `CONTEXT.md` (T002) and `DESIGN.md` (T001), or rename the field to `evidence_links`. |
| I4 | Inconsistency | LOW | plan.md:L43-L53; tasks.md:L83-L84 (T006) | The plan's Project Structure leaves out `tools/tests/test_improvements.py`, which T006 extends. | Add it to the structure tree. |
| I5 | Inconsistency | LOW | tasks.md:L129 (T013); plan.md:L167 | T013 carries "Exempt: verification only", but the plan's Exempt declarations list only the four documentation files. T013 changes no behaviour, so this does not block. | Drop the `Exempt:` label from T013 (it is a verification step, not an implementation task) or add it to the plan's exemptions. |

## Test-scope check (factory override)

- Plan declarations: S1 `factory_cli.feedback.refresh`, S2 `factory_cli.improvements` feedback entries, S3 `bin/factory feedback [<branch>]` CLI. The `Confirmed:` line (plan.md:L170) records plan-Q1, which `state.decisions` shows was explicitly answered (`auto: false`). Its stored scope matches the current declarations exactly.
- Every implementation task T003-T010 maps to a declared seam and has ordered failing-test, implementation and passing-check steps, red proof and a done condition.
- Uncovered paths: T009 (G1: foreign or unreadable backlog file via refresh, and outcome-write failure after the backlog write) and T004 (G2: `<branch>` refusals on S1). Fixing either changes the declared scope and makes the current confirmation stale.
- Plan-exempt tasks are excluded from the check: T001, T002, T011, T012. T013 is verification only.

## ENG-10 new-code reasons

Every new file (`feedback.py`, `test_feedback.py`), abstraction (`run_gh`, `Gap`, `add_feedback`) and dependency (none) has a stated reason (plan.md:L57-L64). The rename `_acquire_backlog_lock` → `_acquire_home_lock` has its reason at L136. No findings.

## Coverage Summary

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 command + route | Yes | T010, T011 | `--repo` gap (C2) |
| FR-002 discovery, narrowing, terminal skip | Yes | T003, T004, T005 | |
| FR-003 read-only reads | Yes | T003 | exact argument lists asserted |
| FR-004 capture/ignore rules | Yes | T003 | |
| FR-005 ids and record fields | Yes | T003 | |
| FR-006 outcome file, atomic, archive unchanged | Yes | T003, T005 | |
| FR-007 stored id unchanged | Yes | T005 | |
| FR-008 signal keys, merged not actionable | Yes | T007 | |
| FR-009 one entry per run/key, ready/claimed | Yes | T006, T007 | |
| FR-010 entry body, template, lock | Yes | T006, T007 | |
| FR-011 listing/claim, regressions | Yes | T006 | route display (C1) |
| FR-012 gap classification | Yes | T008, T009 | I1, I2 |
| FR-013 JSON, exit codes, no retry | Yes | T008, T010 | I3 |
| FR-014 injectable runner, no credentials | Yes | T003, T010 | |
| FR-015 design first, harness-neutral | Yes | T001, T011, T013 | |
| SC-001 | Yes | T003 | |
| SC-002 | Yes | T005, T007 | |
| SC-003 | Yes | T008, T009 | |
| SC-004 | Yes | T007 | |
| SC-005 | Yes | T003 | |

**Constitution Alignment Issues:** none. I (T001 first), II (`SHELL` only), III (build in T003/T010/T013), IV (no agent) and V (reasons stated) all hold.

**Unmapped Tasks:** none.

## Metrics

- Total requirements: 20 (15 FR, 5 SC)
- Total tasks: 13
- Coverage: 100% (20/20 have at least one task)
- Ambiguity count: 1 (A2)
- Duplication count: 0
- Critical issues: 0
- Severity counts: CRITICAL 0, HIGH 3, MEDIUM 5, LOW 8

## Next actions

HIGH findings G1, G2 and I1 block implementation. Remediate them in place:
- Fix I1's write order. The fix decides whether "outcome-write failure after the backlog write" stays a failure path.
- Update the S1 declarations for G1 and G2, then get fresh explicit confirmation of the changed seam scope (`requires_user: true`).

The MEDIUM and LOW findings can be fixed with targeted edits in the same remediation pass.
