# Specification Analysis Report: 020-post-pr-feedback, pass 3

This pass re-checks the artifacts after remediation 1, which applied targeted edits for the analyze-2 findings. It checks `spec.md` (2987 words), `plan.md` (1998 words) and `tasks.md` (2489 words) against constitution 2.0.0. All three are within their word budgets (3000 / 2000 / 2500), so there are no word-budget findings.

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| — | — | — | — | No findings. | — |

## Analyze-2 findings: status

| Pass-2 ID | Status | Evidence |
|-----------|--------|----------|
| G1 (T009 tests an "unreadable" outcome file, which is not declared) | Resolved | T009 step 1 (tasks.md:L104) now tests only "a malformed existing outcome file -> `inaccessible`". This matches the S1 declaration (plan.md:L170) and the Q20 scope (L177). Step 2 still maps unreadable files to `inaccessible` in the same handler, as the gap table (L93) and FR-012 require. No new test path was added. |
| G2 (T010 asserts usage exit 5, which is not declared on S3) | Resolved | The exit-5 assertion is gone from T010 step 1 (tasks.md:L114). Exit 5 stays in the CLI contract (plan.md:L152) as the existing `die_usage` behaviour. The five S3 paths in T010 match the declaration (L172) and the Q20 scope. |
| I1 (partial backlog write has no class) | Resolved | FR-012 (spec.md:L141) now says that any write failing after a backlog write keeps the links already written, and that the next refresh must not duplicate them. It also adds "unwritable backlog file" to the `inaccessible` class. The plan agrees in the gap table (plan.md:L94), and so do the Write-order paragraph (L137) and T009 step 2 (tasks.md:L105). Existing `improvements.add` already wraps an `OSError` raised during a write as `AddError` (improvements.py:L185), so `inaccessible` is reachable as designed. The declared scope is unchanged. |
| U1 (state outcome `url` source) | Resolved | plan.md:L106 now says "`url` = read 1 `url`". T003 asserts it for both `MERGED` and `CLOSED` (tasks.md:L47). |
| T1 ("record" versus "PR outcome") | Resolved | plan.md:L119 now reads "Outcomes are append-only". T001 and T005 use "outcome". The only remaining uses of "record" are verbs or unrelated nouns ("design record", "the JSON report is the record"). |

## Test-scope check (factory override)

- **Declarations.** Three seams are declared, each with explicit failure paths:
  - S1 `factory_cli.feedback.refresh` (plan.md:L170)
  - S2 `factory_cli.improvements` feedback entries (L171)
  - S3 `bin/factory feedback` CLI (L172)

  Two `Exempt:` lines cover the four documentation files and the final verification task (L173-L174). The plan records `Overridden: none` (L175).
- **Confirmation.**
  - `Confirmed: 2026-11-04 - Q20 accepted` (plan.md:L177) stores the full seam-to-failure-path scope.
  - `state.decisions` records plan Q20 = `A` with `auto: false`, which is explicit user acceptance.
  - Remediation 1 did not change any declaration. The edits to the gap table and FR-012 add no tested path.
  - The stored scope still matches the S1/S2/S3 declarations and the exemptions item for item, so the confirmation is current.
- **Task mapping.**
  - T003-T010 each map to one declared seam.
  - Each of these tasks carries ordered failing-test, implementation and passing-check steps, a `Red:` proof and an observable done condition.
  - Failure paths required by the tasks:
    - T003: unreadable archive state, listed under `skipped`.
    - T004: the two `<branch>` refusals.
    - T006: unreadable or foreign entry; backlog lock held.
    - T008: the GitHub classes, both malformed reads and an unparseable `pr_url`.
    - T009: malformed outcome file; foreign or unreadable backlog file; both locks; the patched outcome write.
    - T010: the five S3 paths.
  - Every one of these paths is declared and confirmed. No task requires an undeclared path.
- **Uncovered paths:** none.
- **Exempt tasks.** T001, T002, T011, T012 and T013 are plan-exempt and are excluded from this check.

## ENG-10 new-code reasons

Every new item has a stated reason at plan.md:L58-L65:

- **Files:** `feedback.py`, `test_feedback.py`.
- **Abstractions:** `run_gh`, `Gap`, `add_feedback`.
- **Dependencies:** none.

The rename from `_acquire_backlog_lock` to `_acquire_home_lock` has its reason at L139. There are no findings.

## Referenced code check

All helpers the plan and tasks reuse exist in the worktree:

| Helper | Location |
|--------|----------|
| `commands.main_repo` | commands.py:L42 |
| `improvements.backlog_name` | improvements.py:L33 |
| `improvements.factory_sha` | improvements.py:L38 |
| `improvements._write_atomic` | improvements.py:L52 |
| `improvements._acquire_backlog_lock(directory)` | improvements.py:L62 |
| `AddError` | improvements.py:L27 |
| `state.iso` / `state.parse_iso` | state.py:L99 / L88 |
| `lock.acquire` / `lock.LockHeld` | lock.py:L115 / L19 |
| `value_flags=("--repo",)` convention | cli.py:L64 |
| `die` | commands.py:L28 |
| `die_usage` | cli.py:L57 |
| `Sandbox.cli` | tools/tests/__init__.py:L83 |

## Coverage Summary

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 command, `--repo`, route | Yes | T010, T011, T012 | |
| FR-002 discovery, repo match, narrowing, terminal skip | Yes | T003, T004, T005 | |
| FR-003 read-only reads | Yes | T003 | exact runner arguments asserted |
| FR-004 capture/ignore, malformed review, `ghost` | Yes | T003, T008 | |
| FR-005 ids and fields | Yes | T003 | state `url` now specified |
| FR-006 outcome file, atomic, archive unchanged | Yes | T003, T005 | |
| FR-007 stored id unchanged | Yes | T005 | |
| FR-008 signal keys, merged not actionable | Yes | T007 | |
| FR-009 one entry per run/key, ready/claimed, no cap | Yes | T006, T007 | |
| FR-010 entry body, template, lock order | Yes | T006, T007, T009 | |
| FR-011 listing/claim, regressions | Yes | T006, T011 | |
| FR-012 gap classification, post-backlog write exception | Yes | T008, T009 | |
| FR-013 JSON, `skipped`, exit codes, no retry | Yes | T003, T005, T008, T010 | |
| FR-014 injectable runner, no credentials | Yes | T003, T010 | |
| FR-015 design first, harness-neutral | Yes | T001, T011, T013 | |
| SC-001 | Yes | T003 | |
| SC-002 | Yes | T005, T007 | |
| SC-003 | Yes | T008, T009 | |
| SC-004 | Yes | T006, T007 | |
| SC-005 | Yes | T003 | |

**Constitution Alignment Issues:** none.

| Principle | Status |
|-----------|--------|
| I. Design First | T001 runs first and the other tasks depend on it. |
| II. Harness-Neutral Core | The route uses only `SHELL`. |
| III. Generated Dist | The build command runs in T003, T010 and T013. |
| IV. Stateless Agents | No agent is spawned. |
| V. Simplicity and Reuse | Every new item has a reason, and existing helpers are reused. |

**Unmapped Tasks:** none.

## Metrics

- Total requirements: 20 (15 FR, 5 SC)
- Total tasks: 13
- Coverage: 100% (20/20)
- Ambiguity count: 0
- Duplication count: 0
- Critical issues: 0
- Severity counts: CRITICAL 0, HIGH 0, MEDIUM 0, LOW 0

## Next actions

No blocking or non-blocking findings remain. The artifacts are ready for implementation. Word headroom is small (spec 13, plan 2, tasks 11 words), so any later edit must trim as much as it adds.
