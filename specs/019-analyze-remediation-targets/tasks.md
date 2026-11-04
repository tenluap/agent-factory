---
description: "Task list for 019-analyze-remediation-targets"
---

# Tasks: Enforce Analyze remediation targets

**Input**: `specs/019-analyze-remediation-targets/` (spec.md, plan.md)

**Tests**: Required (engineering.md). Each behaviour-changing task is one commit unit: failing test (red proof), implementation, passing check, committed together. Runner: `python3 -m unittest discover -s tools` (existing). Seams and failure paths: plan.md "Test seams" (scope confirmed: Q1 accepted 2026-11-04, snapshot `factory/relay-plan-1.json`; clarify Q1 = A keeps that scope). No task tests a path outside it. Test only through the declared seams (ENG-4); `checks.analyze_baseline` is exercised through `gate_violation(state, "implement")` and `analyze-record`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: parallel-safe (different files, no dependency)
- **[Story]**: US1-US4 from spec.md

## Phase 1: Setup

- [X] T001 Update `DESIGN.md` "Analyze loop", "Gate table", "Analysis recording repair" and "Modes": `analyze.baseline` set once by `analyze-record` (stored or derived per FR-010, `--fresh-baseline` per FR-012); implement gate targets (CRITICAL 0, HIGH 0, total and LOW `2 * latest < baseline`, zero stays zero, every unmet target named); remediate gate cap at 2 cycles with guided-pass decision; `checkpoint remediate` as the `loops`/`pass` writer; `amendment-check`; approved-only constitution amendments; escalated re-analysis into `factory/analyze-<n>-full.md` with `pass`/`loops` untouched, at most once per run (none while `analyze.reports` holds a `-full.md` report; later CRITICAL/HIGH follows the repair-cycle rule) (FR-013); refusal causes classified from `factory show` (FR-024); why any non-auto analyze answer newer than `result.at` safely authorises a guided pass (grill Q3), including that an escalation record is always followed by a re-analysis with a newer `result.at`. Replace the "no `analyze.result` keeps old gate behaviour" note (legacy runs without a trustworthy baseline are refused). Add a "Validation plan" entry, "Analyze acceptance targets validation": a real run keeps the baseline across recheck and escalation, stops after 2 repair cycles, and fast mode leaves the exhaustion question unanswered; a remediate proposing a constitution amendment writes the draft, leaves the constitution byte-identical on decline, and applies the approved draft before the recheck. Use the `CONTEXT.md` terms (implement gate, baseline analysis, recheck, repair cycle, acceptance targets, exhaustion question). Exempt: DESIGN.md - documentation only (constitution I: lands before core edits). Done: each item above named in DESIGN.md; old note gone; validation entry present.

- [X] T002 [P] Write `docs/adr/0014-analyze-acceptance-targets.md` (context, decision Q1-Q7 from `factory/brief.md`, consequences: baseline immutability, integer half rule, 2-cycle cap, `requires_user` exhaustion question, approved-hash amendments, legacy refusal). Exempt: ADR - documentation only. Done: ADR follows the 0013 layout and cites FR-001..FR-024.

## Phase 2: Foundational

- [ ] T003 [US2] Validate `analyze.baseline` in `validate_state`, `core/skills/factory/bin/factory_cli/state.py`; tests in `tools/tests/test_analyze_record.py`.
  - Seam: `factory_cli.state.validate_state`. Failure paths: negative count; missing count; non-integer count; empty `report`.
  - Red: tests first: a state with a valid baseline `{critical, high, medium, low, report, at}` validates; each failure path (a `bool` count counts as non-integer) yields a problem whose `location` is `analyze.baseline` (or `analyze.baseline.<field>`); absent baseline is valid. Run; fails (no baseline validation exists).
  - Implement: one check for the baseline shape (non-negative non-bool ints for the four counts, non-empty string `report`); `at` gets no new check (clarify Q1).
  - Pass: runner green.
  - Done: the valid, absent and four failure-path cases asserted and passing; no unparsable-`at` or `write_run` assertion (outside the confirmed scope).

## Phase 3: User Story 1 + 2 - Acceptance targets and baseline at the gate (P1)

**Goal**: implement gate compares latest with baseline. **Independent test**: `gate_violation` over hand-built states for each Story 1 scenario.

- [ ] T004 [US1][US2] Add `analyze_baseline(analyze)` and rewrite the `into == "implement"` branch of `gate_violation` in `core/skills/factory/bin/factory_cli/checks.py`; tests in `tools/tests/test_gates.py` (`ImplementGateTests`).
  - Seam: `factory_cli.checks.gate_violation(state, "implement")`. Failure paths: CRITICAL > 0; HIGH > 0 including a new HIGH on a clean baseline; total exactly half (12 -> 6) and above; LOW exactly half (6 -> 3); odd baseline (7 -> 4); zero baseline with nonzero latest (LOW 0 -> 1); `pending_clarify` non-empty with targets met; unanswered `requires_user` relay question; no baseline with zero reports, several reports, or a result naming another report.
  - Red: tests first: baseline 12 total / 6 LOW with latest 0/0/5 total/2 LOW allows; 6 total or 3 LOW refuses naming `total 6 (baseline 12, must be < 6)` / the LOW target; 7 -> 3 total met, 7 -> 4 refused; LOW 0 -> 1 refused with `(baseline 0, must stay 0)`, 0 -> 0 met; clean baseline plus new HIGH refused with `HIGH 1 (must be 0)` though totals met; zero-finding first analysis allows; latest equal to a non-clean baseline refused; several unmet targets all named in one `; `-joined reason; `pending_clarify` and an unanswered `requires_user` relay question (by id) refuse with targets met; analyze `gate-override` allows (existing test kept); no stored baseline with exactly one report named by `result` derives and evaluates; zero reports refuses with the existing "analyze.reports is empty" (FR-011, clarify Q5); several reports, or `result.report` naming another report, refuses with "no trustworthy baseline: re-run analysis as a fresh baseline, record a gate-override, or abort". Update existing `test_passes_clean_remediated_or_overridden` cases to the new rule. Run; fails.
  - Implement: `analyze_baseline` returns the valid stored baseline, else the derived `result` (FR-010), else `None`; never reads report markdown. Gate collects every problem in the plan's order with integer comparisons only (`latest == 0` when `b == 0`, else `2 * latest < b`); `permitting_decision` unchanged.
  - Pass: runner green, `test_analyze_record.py` included.
  - Done: every Story 1 acceptance scenario and every listed failure path asserted and passing (SC-001, SC-002).

## Phase 4: User Story 2 - Baseline recorded once (P1)

**Goal**: `analyze-record` writes the baseline. **Independent test**: two records in sequence; baseline keeps the first.

- [ ] T005 [US2] Set the baseline in `cmd_analyze_record` (`core/skills/factory/bin/factory_cli/commands.py`) and add `--fresh-baseline` to the `analyze-record` dispatch and USAGE in `core/skills/factory/bin/factory_cli/cli.py`; tests in `tools/tests/test_analyze_record.py`.
  - Seam: `bin/factory analyze-record`. Failure paths: `--fresh-baseline` with an existing or derivable baseline refused with state and HEAD unchanged.
  - Red: subprocess tests first: first record sets `analyze.baseline` to its counts, spec-relative report and the same `at` as `result`; second record changes only `result` and `reports`; legacy state (no baseline, one report named by `result`) gets the derived baseline stored on the next record, not the new record; legacy state with two reports and no baseline stays without baseline after a record; `--fresh-baseline` on that underivable state sets the new record as baseline; `--fresh-baseline` with a stored or derivable baseline exits 1, state bytes and HEAD unchanged; escalation (US2.4, FR-003, grill Q4): after the baseline record of `factory/analyze-1.md`, recording `factory/analyze-1-full.md` keeps `analyze.baseline` (report `factory/analyze-1.md`), `loops` and `pass` unchanged. Run; fails.
  - Implement: add `--fresh-baseline` to USAGE (not asserted); inside the existing `mutate`, compute `checks.analyze_baseline` on fresh locked state before updating `result`, per plan "`analyze-record`"; refusal raised before any write.
  - Pass: runner green.
  - Done: every listed case asserted and passing (FR-001, FR-002, FR-003 escalation half, FR-010, FR-012, SC-004).

## Phase 5: User Story 3 - Bounded repair cycles (P2)

**Goal**: at most 2 automatic cycles; loops written by the CLI. **Independent test**: gate and checkpoint over states at `loops` 0, 1, 2.

- [ ] T006 [US3] Add the `into == "remediate"` branch of `gate_violation` in `core/skills/factory/bin/factory_cli/checks.py`; tests in `tools/tests/test_gates.py` (new `RemediateGateTests`).
  - Seam: `factory_cli.checks.gate_violation(state, "remediate")`. Failure paths: `loops == 2` with no decision; an `auto: true` analyze decision; a guided decision older than `analyze.result.at`.
  - Red: tests first: `loops` 0 and 1 allow; `loops == 2` with no analyze decision refuses naming the loop count and the three choices (guided pass, gate-override, abort); an `auto: true` analyze answer newer than `result.at` refuses; a non-auto analyze `answer` older than `result.at` refuses; a non-auto analyze `answer` newer than `result.at` allows; `loops == 3` behaves like 2. Run; fails (ungated today).
  - Implement: reuse `_decisions(state, "analyze", ("answer",))`, filter `auto` and compare `at` with `result.at`; any newer non-auto answer qualifies (grill Q3).
  - Pass: runner green.
  - Done: every listed case asserted and passing (FR-014, FR-016, SC-003).

- [ ] T007 [US3][US2] Increment `analyze.loops` and `analyze.pass` in `cmd_checkpoint` (`core/skills/factory/bin/factory_cli/commands.py`) for `checkpoint remediate` while the recorded `stage` is `remediate`; tests in `tools/tests/test_analyze_record.py`.
  - Seams: `bin/factory checkpoint` (remediate and into implement); `bin/factory resume`. Failure paths: checkpoint -> a repeated `checkpoint remediate` after the stage advanced does not increment; refused into `remediate` at the cap leaves state unchanged; into `implement` with the stale pre-remediation result refused until a fresh analysis is recorded. resume -> none.
  - Red: subprocess tests first: record a non-clean analysis, `checkpoint analyze --next remediate`, `checkpoint remediate --next analyze` gives `loops` 1 and `pass` 2; repeating `checkpoint remediate` after the stage advanced leaves both unchanged; `checkpoint analyze --next implement` with the stale result refuses, then succeeds after `analyze-record` of a report meeting targets (FR-021); escalation consumes no cycle (US3.3, grill Q4): two `analyze-record` calls and a refused `checkpoint analyze --next implement`, with no `checkpoint remediate`, leave `loops` and `pass` at 0 and 1; at `loops == 2` with no guided decision `checkpoint analyze --next remediate` exits non-zero, state bytes and HEAD unchanged; `resume` on another harness keeps `analyze.baseline` and `loops` identical (FR-003, SC-004). Run; fails (no writer increments `loops`).
  - Implement: increment inside the same `mutate` as the gate and history entry, conditioned on fresh locked state's `stage == "remediate"`.
  - Pass: runner green.
  - Done: every listed case asserted and passing (FR-003, FR-014, FR-021, SC-004).

## Phase 6: User Story 4 - Approved-only constitution amendments (P2)

**Goal**: a tested hash check for amendment drafts. **Independent test**: `amendment-check` over temp drafts.

- [ ] T008 [US4] Add `cmd_amendment_check` to `core/skills/factory/bin/factory_cli/commands.py` and `amendment-check <draft> [--sha256 <hex>]` dispatch and USAGE to `core/skills/factory/bin/factory_cli/cli.py`; tests in `tools/tests/test_analyze_record.py`.
  - Seam: `bin/factory amendment-check`. Failure paths: missing draft exits 1; changed draft (hash mismatch) exits 1; constitution file byte-identical after each.
  - Red: subprocess tests first: prints `{"draft", "sha256"}` with the lower-case hex SHA-256 of the file bytes; matching `--sha256` exits 0; missing draft exits 1 naming the path; a draft edited after hashing exits 1 naming approved and current hashes; `.specify/memory/constitution.md` in the temp repo is byte-identical after each call. USAGE is updated in Implement and not asserted (no usage-refusal failure path is declared). Run; fails (unknown command).
  - Implement: `hashlib.sha256` over the file bytes; read-only; reuse `die` for exits; add the command to USAGE.
  - Pass: runner green.
  - Done: every listed case asserted and passing (FR-018, FR-019, SC-005).

## Phase 7: Orchestrator and role prose (US1-US4)

- [ ] T009 [US1][US2][US3] Edit `core/skills/factory/SKILL.md`: section 1 item 4 also `RESOLVE` `speckit-constitution`; section 5 analyze loop per plan "Orchestrator (SKILL.md step 5)": lite escalation on CRITICAL/HIGH unchanged, consumes no cycle, happens at most once per run (only while `analyze.reports` holds no `-full.md` report; afterwards CRITICAL/HIGH follows (4)), and writes the re-analysis to `factory/analyze-<n>-full.md` with `pass`/`loops` untouched (FR-013); try `checkpoint analyze --next implement`; on refusal read `factory show`, never the reason text, and route in FR-024's order: (1) open `pending_clarify` or unanswered `requires_user` question -> `clarify` or the relay wait, no cycle charged; (2) zero reports -> run analyze, no question; (3) no stored and no derivable baseline (`reports` length not 1, or `result.report` names another) -> ask fresh baseline (re-analysis into a new `factory/analyze-<n>-baseline.md`, never overwriting a listed report; `analyze-record --fresh-baseline`), override or abort; a derivable baseline falls through to (4); (4) unmet targets with `loops < 2` -> one repair cycle (`checkpoint analyze --next remediate`, remediate with the `speckit-constitution` path, `checkpoint remediate --next analyze`, or `clarify`/`grill-with-docs` first when `pending_clarify` is non-empty, then recheck); at `loops >= 2` `NOTIFY` baseline counts, latest counts and unmet targets and ask the `requires_user` exhaustion question (guided pass via `decisions-add analyze`, `gate-override`, abort). Remove the lite "remediate once, then implement" and full-chain "loops < 2 on CRITICAL/HIGH" rules. Replace the step 5 done condition ("Done when analyze is clean, MEDIUM/LOW were remediated, or the user chose to proceed") with: acceptance targets met with no protected question open, or a recorded `gate-override`. Exempt: SKILL.md - documentation only. Done: FR-007 and FR-012..FR-017, FR-024 each cited by a step; new done condition present; `CONTEXT.md` terms; harness-neutral verbs only.

- [ ] T010 [P] [US2][US3] Edit `core/skills/factory/references/state.md`: `analyze.baseline` schema and immutability, `checkpoint remediate` as the `loops`/`pass` writer (escalation and resume leave both unchanged), `analyze-record --fresh-baseline`, `amendment-check`. Exempt: state.md - documentation only. Done: schema, writers and resume semantics documented.

- [ ] T011 [P] [US4] Edit `core/roles/spec-builder.md` remediate bullet per plan "Remediate role": replace "Constitution conflicts are fixed in the artifacts, never in the constitution" with the draft at `factory/constitution-amendment-<n>.md` (`n` = `analyze.pass`; exact text, rationale, version bump, implied changes to other governed files such as `DESIGN.md`), `requires_user` approval carrying `amendment-check` sha256, verify with `--sha256 <approved>` before applying through `speckit-constitution` plus the draft's implied changes, listing the constitution and each file actually changed (never a missing file) in envelope `files` so one checkpoint commits them, mismatch or missing draft asks fresh approval and applies nothing, declined, aborted or overridden fixes in artifacts or leaves the finding counted. The analyze stage writes an escalated re-analysis to `factory/analyze-<n>-full.md` (FR-013) and a fresh-baseline re-analysis to `factory/analyze-<n>-baseline.md` (FR-012). Exempt: spec-builder.md - documentation only. Done: FR-013 and FR-018..FR-021 each stated, including the implied-file apply and envelope `files`.

- [ ] T012 [P] [US1][US3] Update `docs/factory-overview.md` (analyze diagram: replace the "Remediate once" node with the repair-cycle loop, cap of 2 and exhaustion question; the paragraph below it describes acceptance targets and approved-only amendments instead of pointing to the proposal) and `docs/product-brief.md` "Analysis and remediation policy" (replace the "one remediation pass" rule with baseline-relative acceptance targets and the 2-cycle cap; add a header revision line, like "Engineering policy revised"). Exempt: overview docs - documentation only. Done: neither file describes "remediate once"; revision line present; both cite ADR 0014 (FR-022).

## Phase 8: Verification

- [ ] T013 Run the test command (`python3 -m unittest discover -s tools`) and the build command (five-harness render, `dist/` untracked, `bash -n install.sh`). The end-to-end "Analyze acceptance targets validation" run is out of this task's scope (DESIGN.md records it). Not behaviour-changing: runs the test and build commands only. Done: both pass with zero new failures (SC-006); any pre-existing failure named with its origin commit.

## Dependencies

- T001 first (constitution I). T002 any time after T001.
- T003 -> T004 -> T005 -> T006 -> T007 (shared files `checks.py`, `commands.py`, test files; T005 needs `analyze_baseline`, T007 needs both gates).
- T008 after T005 (shares `cli.py`, `commands.py`).
- T009-T012 after T007 and T008 (describe the shipped commands); T010, T011 and T012 parallel; T012 after T002 (cites ADR 0014).
- T013 last.

## Parallel examples

- After T001: T002 alongside T003.
- After T008: T010, T011 and T012 together, then T009.

## Implementation strategy

MVP: T001-T005 (US1 + US2: gate enforces targets against a recorded baseline). Then T006-T007 (US3 cycle cap), T008 (US4), prose T009-T012, verification T013. Each task is one passing commit.
