# Feature Specification: Enforce Analyze remediation targets

**Feature Branch**: `019-analyze-remediation-targets`

**Created**: 2026-11-04

**Status**: Draft

**Input**: User description: "Enforce Analyze remediation targets: implement the plan at `docs/superpowers/plans/2026-11-03-factory-analyze-remediation-plan.md` (retain the first analyze report as baseline, remediate in place with approved-only constitution amendments, enforce baseline-relative acceptance targets at the implementation checkpoint, allow up to two automatic repair-and-recheck cycles, pause implementation while any target is unmet)." Settled decisions Q1-Q7 are in `factory/brief.md`.

## Clarifications

### Session 2026-11-04

- Q: Trim T003 to the confirmed test scope, or add an unparsable baseline `at` to `validate_state`? → A: Keep the plan Q1 scope; no test asserts an unparsable `at` or a `write_run` refusal (Edge Cases).
- Q: How does the orchestrator tell implement-gate refusal causes apart? → A: It reads run state (`factory show`), never the reason text (FR-024).
- Q: Keep the first report file when a lite run escalates and analysis runs again? → A: Yes; the escalated re-analysis writes `factory/analyze-<n>-full.md` (FR-013).
- Q: How is "implementation waits while remediation questions are pending" enforced when no writer exists for `analyze.pending_clarify`? → A: Relay routing enforces it; the gate check is defensive only (FR-007).
- Q: Zero reports: what does the gate say, and what does the orchestrator do? → A: Keep the existing "analyze.reports is empty" refusal; the orchestrator runs analyze unasked (FR-011).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Implementation waits for measurable improvement (Priority: P1)

A factory user wants implementation to start only after remediation has measurably reduced the spec findings. The implement gate compares the latest recheck with the baseline analysis and refuses to enter implementation until every acceptance target is met.

**Why this priority**: Today implementation proceeds whatever the recheck shows; the gate makes improvement a precondition.

**Independent Test**: Feed the implement gate a run state with a baseline and a latest result, and check that it allows or refuses with a reason that names each unmet target, for each acceptance example below.

**Acceptance Scenarios**:

1. **Given** a baseline of 12 total findings with 6 LOW, **When** the latest recheck has 0 CRITICAL, 0 HIGH, 5 total and 2 LOW, **Then** the gate allows implementation.
2. **Given** the same baseline, **When** the recheck has 6 total (exactly half) or 3 LOW (exactly half), **Then** the gate refuses and names the unmet target.
3. **Given** a baseline of 7 total, **When** the recheck has 3 total, **Then** the total target is met; **When** it has 4 total, **Then** it is not.
4. **Given** a baseline with 0 LOW, **When** the recheck has 1 LOW, **Then** the gate refuses; **When** it has 0 LOW, **Then** the LOW target is met.
5. **Given** a baseline with no CRITICAL or HIGH findings, **When** a recheck discovers a new HIGH finding, **Then** the gate refuses even if total and LOW targets are met.
6. **Given** a first analysis with zero findings, **When** the run reaches the implement gate, **Then** the gate allows implementation with no remediation.
7. **Given** targets are met but `analyze.pending_clarify` holds a question or a `requires_user` question is unanswered, **When** the run reaches the implement gate, **Then** the gate refuses until it is answered.
8. **Given** a recorded `gate-override` decision for analyze, **When** the run reaches the implement gate, **Then** the gate allows implementation and the override stays on the approver's veto list.

---

### User Story 2 - The first analysis is kept as the baseline (Priority: P1)

The first completed analysis report's severity counts are stored once as the baseline; later reports update only the latest result. Resume and lite-to-full escalation never move the baseline.

**Why this priority**: The acceptance targets are meaningless without a stable baseline; Story 1 depends on it.

**Independent Test**: Record two analyze envelopes (the second stands for a recheck or an escalated re-analysis) and check that the baseline holds the first's counts, path and time and the latest result the second's; then resume and check the baseline is unchanged.

**Acceptance Scenarios**:

1. **Given** a run with no baseline, **When** the first analyze envelope is recorded, **Then** the baseline holds its CRITICAL/HIGH/MEDIUM/LOW counts, report path and record time, and the latest result holds the same.
2. **Given** a baseline exists, **When** a later analyze envelope is recorded, **Then** only the latest result and the report list change.
3. **Given** a run with a baseline and consumed repair cycles, **When** the run is resumed, **Then** the baseline and the consumed cycle count are unchanged.
4. **Given** a lite run whose first analysis has CRITICAL or HIGH findings, **When** it escalates to the full chain and analysis runs again into `factory/analyze-<n>-full.md`, **Then** the baseline is still the first lite report, that report file is unchanged, and `analyze.pass` and `analyze.loops` are unchanged.
5. **Given** a legacy run without a baseline whose report list has exactly one entry that the latest result names, **When** the gate or the next record needs a baseline, **Then** it is derived from that latest result.
6. **Given** a legacy run without a baseline and with several reports, or with a latest result that names a different report, **When** the run reaches the implement gate, **Then** the gate refuses with a reason saying no trustworthy baseline exists, and the orchestrator offers fresh baseline, override or abort.
7. **Given** a run with zero reports, **When** it reaches the implement gate, **Then** the gate keeps its existing "analyze.reports is empty" refusal and the orchestrator runs analyze without asking the user.

---

### User Story 3 - Bounded automatic repair, then the user decides (Priority: P2)

When targets are unmet the factory repairs the artifacts in place and rechecks, at most twice automatically. If targets stay unmet, the user sees baseline and latest counts and the unmet targets, and decides.

**Why this priority**: Prevents endless loops and silent progress past unmet targets; builds on Stories 1 and 2.

**Independent Test**: Simulate a run whose rechecks stay above target and check that exactly two remediate-plus-recheck cycles run, then a `requires_user` exhaustion question appears that fast mode does not answer.

**Acceptance Scenarios**:

1. **Given** targets are unmet after an analysis and fewer than 2 cycles were consumed, **When** the orchestrator continues, **Then** it runs `remediate`, increments `analyze.loops` and `analyze.pass`, and rechecks (FR-014).
2. **Given** only MEDIUM or LOW findings keep a target unmet, **When** cycles remain, **Then** a cycle runs exactly as for serious findings, on either chain.
3. **Given** a lite run with CRITICAL or HIGH findings, **When** it escalates to the full chain, **Then** the escalation consumes no cycle.
4. **Given** 2 cycles were consumed and a target is still unmet, **When** the orchestrator continues, **Then** it shows baseline counts, latest counts and each unmet target, and asks the exhaustion question (`requires_user`): one more guided pass, an explicit recorded `gate-override`, or abort.
5. **Given** fast mode is on, **When** the exhaustion question is asked, **Then** it is never auto-answered.
6. **Given** the user chooses one more guided pass, **When** that pass's recheck still misses a target, **Then** the exhaustion question is asked again.
7. **Given** any recheck meets every target and no protected question is open, **When** the orchestrator continues, **Then** implementation starts with no further cycle.

---

### User Story 4 - Constitution amendments only with explicit approval (Priority: P2)

When a finding is best fixed by changing the project constitution, the user sees the exact amendment, its rationale and its version bump, and the constitution changes only after the user approves that exact draft.

**Why this priority**: Protects project governance from silent agent edits.

**Independent Test**: Drive a remediate pass that proposes an amendment; check the draft file and the `requires_user` question with the draft's hash; then check that a decline leaves the constitution byte-identical, an edited draft needs fresh approval, and an approved draft is applied and followed by a recheck.

**Acceptance Scenarios**:

1. **Given** a finding that warrants a constitution change, **When** remediate runs, **Then** it writes the amendment draft (FR-018), leaves the constitution unchanged, and returns a `requires_user` question carrying the draft's content hash.
2. **Given** the user declines, or the run is aborted or overridden without approval, **When** the cycle ends, **Then** the constitution is unchanged and the finding is either fixed in the spec artifacts or stays counted.
3. **Given** the user approved a draft, **When** a fresh remediate verifies the draft's current hash equals the approved hash, **Then** it applies exactly that draft through the constitution amendment process (version bump and sync impact report), and the cycle's recheck runs afterwards.
4. **Given** the draft changed after approval, **When** remediate verifies the hash, **Then** it does not apply the draft and asks for a fresh approval of the new hash.

---

### Edge Cases

- Exactly half fails; a baseline of 1 total requires 0. MEDIUM counts only through the total.
- Non-blocking MEDIUM findings (ENG-10, word budget) and new findings count; no per-finding matching against the baseline.
- A recheck that is worse than the baseline is simply unmet; it does not replace the baseline.
- The latest result is the baseline itself (no recheck yet) and the baseline is non-clean: targets are unmet, so a cycle runs.
- An escalated run whose full-chain analysis already meets every target enters implementation without consuming a cycle.
- Resume between a remediate and its recheck charges no extra cycle; the recheck runs next.
- A malformed baseline (a missing, negative or non-integer count, or an empty `report`) is rejected by the state writer like any other invalid analyze field. Tests cover exactly these failure paths.
- An amendment draft file that is missing or unreadable when the approved remediate runs: nothing is applied and a fresh approval is requested.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The analysis recorder MUST store the first completed analyze report's CRITICAL, HIGH, MEDIUM and LOW counts, its report path and its record time as `analyze.baseline`, exactly once per run.
- **FR-002**: Every later recorded report MUST update only `analyze.result` and the report list; only a fresh-baseline choice (FR-012) may change `analyze.baseline`.
- **FR-003**: Resume (on any harness) and lite-to-full escalation MUST preserve `analyze.baseline` and `analyze.loops` unchanged. Tests verify escalation through a later `analyze-record` keeping the baseline and `analyze.loops` changing only via `checkpoint remediate`; a `mode.chain` writer is out of scope.
- **FR-004**: The implement gate MUST refuse unless the latest result has CRITICAL == 0 and HIGH == 0.
- **FR-005**: For each of total (CRITICAL + HIGH + MEDIUM + LOW) and LOW, the gate MUST require: when the baseline count is 0, a latest count of 0; otherwise `2 * latest < baseline`, using integer arithmetic only.
- **FR-006**: Every finding in the latest report MUST count, including newly discovered and non-blocking findings.
- **FR-007**: The gate MUST keep refusing while `analyze.pending_clarify` is non-empty or any `requires_user` question for the analyze loop is unanswered, regardless of counts. Relay routing enforces the `pending_clarify` clause (a remediate envelope's `pending_clarify` routes to `clarify`); the gate check is defensive, and no state writer is added.
- **FR-008**: Each refusal MUST name every unmet target with its baseline and latest counts, or the protected question or missing baseline that blocks.
- **FR-009**: A recorded analyze `gate-override` decision MUST let the gate pass and MUST appear on the approver's veto list.
- **FR-010**: When the baseline is absent, the gate and recorder MUST derive it from `analyze.result` only when `analyze.reports` has exactly one entry and `analyze.result.report` names it.
- **FR-011**: When the baseline is absent, `analyze.reports` has one or more entries, and the baseline cannot be derived, the gate MUST refuse with a reason stating that no trustworthy baseline exists; report markdown MUST NOT be parsed for counts. With zero reports the gate keeps its existing "analyze.reports is empty" refusal, and the orchestrator runs analyze without a user question.
- **FR-012**: For an underivable baseline the orchestrator MUST ask the user to re-run analysis as a fresh baseline, record a `gate-override`, or abort; a fresh-baseline choice makes the next recorded report the baseline.
- **FR-013**: Lite-to-full escalation on CRITICAL or HIGH findings MUST be kept and MUST NOT consume a repair cycle. The escalated re-analysis MUST be written to `factory/analyze-<n>-full.md`, so the baseline report file is never overwritten, and it leaves `analyze.pass` and `analyze.loops` untouched. Escalation happens at most once per run (none while `analyze.reports` holds a `-full.md` report); later CRITICAL or HIGH follows FR-014 and FR-016. This is a prose rule in `SKILL.md` and `roles/spec-builder.md`.
- **FR-014**: When any target is unmet and `analyze.loops < 2`, the orchestrator MUST run one repair cycle: `remediate`, increment `analyze.loops` and `analyze.pass`, then recheck (via `clarify` and `grill-with-docs` first when `pending_clarify` is non-empty). It applies on both chains, including MEDIUM/LOW-only findings, replacing the lite "remediate once" and full-chain "CRITICAL/HIGH only" rules.
- **FR-015**: Remediation MUST edit `spec.md`, `plan.md`, `tasks.md` and other spec artifacts in place; it never regenerates them.
- **FR-016**: When targets are unmet after 2 cycles, the orchestrator MUST show baseline counts, latest counts and the unmet targets, and ask the exhaustion question, `requires_user`, with options: one more guided pass, an explicit recorded `gate-override`, or abort. Fast mode MUST NOT auto-answer it.
- **FR-017**: Implementation MUST stay paused while any target is unmet and no `gate-override` is recorded.
- **FR-018**: When a finding warrants a constitution change, remediate MUST write the exact amendment text, rationale, version bump and implied changes to other governed files (e.g. `DESIGN.md`) to `<spec_dir>/factory/constitution-amendment-<n>.md` and return a `requires_user` question carrying the draft's content hash, without touching the constitution.
- **FR-019**: After approval, a fresh remediate MUST verify the current draft hash equals the approved hash and then apply exactly that draft through the `speckit-constitution` amendment process, plus those implied changes, listing the constitution and each file it changed, never a missing file, in its envelope `files` so one checkpoint commits them; any mismatch or missing draft MUST trigger a fresh approval question and apply nothing.
- **FR-020**: A declined amendment, or a run aborted or overridden without approval, MUST leave the constitution unchanged; the finding is fixed in the spec artifacts or stays counted.
- **FR-021**: An applied amendment MUST be followed by the cycle's recheck before the gate is evaluated.
- **FR-022**: The rule MUST be recorded as ADR 0014 and reflected in `DESIGN.md` (including a "Validation plan" entry), `references/state.md`, `SKILL.md` step 5 (rules and done condition) and `roles/spec-builder.md`. `docs/factory-overview.md` and `docs/product-brief.md` are updated, documentation-exempt; behaviour changes live in `core/` and render cleanly for all five harnesses.
- **FR-023**: Automated tests MUST cover every acceptance example in this spec, including exactly-half, odd and zero baselines, legacy derivation and refusal, and a missing or hash-mismatched amendment draft.
- **FR-024**: After an implement-gate refusal, the orchestrator MUST classify the cause from run state (`factory show`), never from the reason text, in this order. (1) An open `pending_clarify` or an unanswered `requires_user` question routes to `clarify` or the relay wait, with no cycle charged. (2) Zero reports runs analyze (FR-011). (3) No stored and no derivable baseline (FR-010) asks for a fresh baseline, an override or an abort (FR-012); a derivable one falls through. (4) Otherwise, unmet targets run a repair cycle when `analyze.loops < 2` (FR-014), or ask the exhaustion question (FR-016).

### Key Entities

- **Baseline analysis**: the first completed analysis of a run; four severity counts, report path, record time. Its report file is never overwritten; it changes only through a fresh-baseline choice.
- **Recheck**: any analysis after the baseline; the most recent one is the latest result.
- **Implement gate**: the transition check that refuses implementation while any acceptance target is unmet, a protected question is open, or no trustworthy baseline exists.
- **Acceptance targets**: zero CRITICAL, zero HIGH, total below half of baseline total, LOW below half of baseline LOW, and zero stays zero.
- **Repair cycle**: one remediate plus recheck (including any clarify and grill-with-docs loop pass); counted in `analyze.loops`, capped at 2 automatic cycles per run.
- **Amendment draft**: a proposed constitution change file with its rationale, version bump and content hash; applied only after approval of that hash.
- **Exhaustion question**: the `requires_user` question asked when targets stay unmet after 2 repair cycles.
- **Gate override**: an explicit recorded user decision that lets implementation start with unmet targets; listed for the approver.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of the acceptance examples in Story 1 produce the expected allow or refuse outcome in automated tests.
- **SC-002**: No run enters implementation with an unmet target unless a `gate-override` decision is recorded; verified by tests covering every refusal path.
- **SC-003**: A run performs at most 2 automatic repair cycles; the third attempt always requires an explicit user answer, including in fast mode.
- **SC-004**: The baseline and consumed cycle count are unchanged in 100% of resume, later-record and no-`checkpoint remediate` tests; the last two cover escalation.
- **SC-005**: In tests, a missing or hash-mismatched amendment draft leaves the constitution byte-identical.
- **SC-006**: The build renders all five harnesses cleanly and the full test suite passes.

## Assumptions

- The existing `analyze.result` count fields, `analyze.loops`, `analyze.pass`, `pending_clarify`, `requires_user` and the analyze `gate-override` decision kind are reused; only `analyze.baseline` is new state.
- The existing state writer's validation rules (non-negative counts, non-decreasing timestamps, paths relative to `spec_dir`) extend to the baseline.
- The content hash is SHA-256 of the draft file bytes.
- "One more guided pass" increments `analyze.loops` like an automatic cycle; the user's guidance is passed to remediate.
- Past the cap, any non-auto analyze answer newer than the latest result authorises remediate; only a guided pass reaches it (abort ends the run, an override passes the gate, a fresh baseline or an escalation record is followed by a newer result). Plan and `DESIGN.md` state why.
- The amendment file number `<n>` is the current `analyze.pass`.
- A run started before this change resumes under the new rules, with legacy baseline handling per FR-010 to FR-012.
- Build and test commands are those in `factory/brief.md` (Q1).
