# Implementation Plan: Enforce Analyze remediation targets

**Branch**: `019-analyze-remediation-targets` | **Date**: 2026-11-04 | **Spec**: [spec.md](spec.md)

**Input**: `spec.md`; settled decisions Q1-Q7 in `factory/brief.md`, clarify Q1-Q5 (`factory/relay-clarify-1.json`), grill-with-docs Q1-Q5 (`factory/relay-grill-with-docs-1.json`), terms in `CONTEXT.md`.

## Summary

The implement gate (`factory_cli/checks.py`) compares `analyze.result` (the latest recheck) with a new `analyze.baseline` and refuses, naming every unmet acceptance target, until CRITICAL and HIGH are 0 and total and LOW meet the integer half rule. `analyze-record` sets the baseline once. A gate into `remediate` caps automatic repair cycles at 2; `checkpoint remediate` becomes the missing writer for `analyze.loops` and `analyze.pass` (ADR 0006). `amendment-check` hashes a constitution amendment draft and verifies an approved hash. The orchestrator classifies refusals from run state (FR-024). Prose, ADR 0014 and two overview docs describe the loop.

## Technical Context

- **Language/Dependencies**: Python 3 standard library (`hashlib` added), Markdown prose; no new dependencies.
- **Storage**: run `state.json` v5, additive `analyze.baseline`; no version bump (readers ignore unknown analyze keys).
- **Testing**: `python3 -m unittest discover -s tools` (existing runner, CI).
- **Platform**: macOS/Linux, five harnesses. Performance: N/A.
- **Constraints**: harness-neutral core; state written only by the CLI writer (ADR 0006); refusals change nothing.
- **Scope**: two gates, one recorder, one checkpoint branch, one command, six prose files, one ADR.

## Constitution Check

- **I. Design First**: PASS. `DESIGN.md` ("Modes", "Analyze loop", "Gate table", "Analysis recording repair", a new "Validation plan" entry) is updated first.
- **II. Harness-Neutral Core**: PASS. Prose uses `SHELL`, `ASK`, `NOTIFY`, `RESOLVE`; `speckit-constitution` is a resolved skill.
- **III. Generated Dist**: PASS. No render change; build renders all five harnesses, `dist/` untracked.
- **IV. Stateless Agents**: PASS. Baseline, cycle count and approved draft hash live in `state.json` and on disk; a fresh remediate re-verifies.
- **V. Simplicity and Reuse**: PASS. Reuses `analyze.result`, `loops`, `pass`, `decisions`, `gate-override`, `requires_user`, the gate table and the checkpoint writer.

## Project Structure

Research, data model and validation are folded into this plan.

### Source Code (repository root)

```text
core/skills/factory/bin/factory_cli/
├── checks.py     # analyze_baseline(); implement gate targets; remediate gate (cycle cap)
├── commands.py   # analyze-record baseline + --fresh-baseline; checkpoint remediate increments; cmd_amendment_check
├── cli.py        # amendment-check dispatch, --fresh-baseline flag, USAGE
└── state.py      # validate analyze.baseline shape
core/skills/factory/SKILL.md              # step 4 RESOLVE speckit-constitution; step 5 loop rewritten
core/skills/factory/references/state.md   # analyze.baseline, cycle writer, new command
core/roles/spec-builder.md                # amendment draft and hash check; escalated report name
DESIGN.md                                 # loop, gate table, "Analyze acceptance targets validation"
docs/adr/0014-analyze-acceptance-targets.md
docs/factory-overview.md                  # analyze diagram and paragraph
docs/product-brief.md                     # "Analysis and remediation policy" + revision line
tools/tests/test_gates.py                 # gate tests (extended)
tools/tests/test_analyze_record.py        # recorder, checkpoint, resume, amendment-check tests (extended)
```

### New files, abstractions, dependencies

- `docs/adr/0014-analyze-acceptance-targets.md` - file - FR-022 and Q7 require it.
- `analyze.baseline` - abstraction - state field required by FR-001; same shape as `analyze.result` so one validity check serves both.
- `checks.analyze_baseline(analyze)` - abstraction - one source of truth for the stored-or-derived baseline (FR-010), shared by the gate and `analyze-record`.
- `factory amendment-check <draft> [--sha256 <hex>]` - abstraction - one tested hash check for amendment approval (FR-018, FR-019), identical on every harness.
- `analyze-record --fresh-baseline` - abstraction - the only writer path for FR-012's explicit fresh-baseline choice.
- Dependencies: none (`hashlib` is standard library).

No new test files.

## Research (settled defaults)

- **Draft hash**: SHA-256 of the draft bytes, lower-case hex, from `amendment-check`. Agent-run `shasum` rejected: platform-dependent and untestable.
- **Terms** (grill Q1, `CONTEXT.md`): implement gate, baseline analysis, recheck, repair cycle, acceptance targets, exhaustion question. "Fresh analysis" in the verbatim confirmed scope means a recheck.
- **Amendment number**: `n` = `analyze.pass`, as for `remediation-<n>.md`.
- **Escalated report** (clarify Q3): `factory/analyze-<n>-full.md`, keeping the baseline report file; `pass` and `loops` untouched. Prose-only: `analyze-record` accepts any report in `spec_dir`, and the stored baseline makes derivation moot.
- **Refusal causes** (clarify Q2): the orchestrator reads `factory show`, never the reason text (FR-024).
- **Latest equals baseline**: unmet with findings (`2 * b < b` is false for `b > 0`), met with none.
- **Pre-change runs**: resume under the new rules (FR-010 to FR-012); `DESIGN.md`'s old-gate note is replaced.
- **Cycle cap**: a gate into `remediate`, reusing the gate table, rather than a new command. Every pass into `remediate`, guided or automatic, counts.
- **Skipped**: writers for `pending_clarify`, `remediations` and `mode.chain` (pre-existing gaps). Relay routing enforces FR-007's `pending_clarify` clause; the gate check is defensive (clarify Q4).

## Design

### Data model

`analyze.baseline`: `{ "critical", "high", "medium", "low", "report", "at" }`, non-negative integer counts, spec-relative `report`, writer-stamped `at`; absent until the first record. `validate_state` rejects a present baseline with a missing, negative or non-integer count or an empty `report`; `at` gets no new check (clarify Q1).

### `checks.analyze_baseline(analyze)`

Returns the stored baseline when valid; when absent, `analyze.result` only if `reports` has exactly one entry that `result.report` names; otherwise `None`. Never reads report markdown.

### Implement gate (`gate_violation(s, "implement")`)

1. An analyze `gate-override` decision permits (unchanged).
2. Empty `reports`: refuse with the existing "analyze.reports is empty" (FR-011, clarify Q5).
3. Join every problem with `; ` into one refusal:
   - `pending_clarify` non-empty (existing wording kept; defensive, FR-007);
   - each relay question with `requires_user: true` and no answer, by id;
   - baseline `None`: "no trustworthy baseline: re-run analysis as a fresh baseline, record a gate-override, or abort";
   - otherwise each unmet target with counts: `CRITICAL n (must be 0)`, `HIGH n (must be 0)`, `total n (baseline b, must be < b/2)` or `(baseline 0, must stay 0)`, same for `LOW`. Target met: `latest == 0` when `b == 0`, else `2 * latest < b`.

### Remediate gate (`gate_violation(s, "remediate")`)

Permits while `analyze.loops < 2`. At 2 or more, permits only when a non-auto analyze `answer` decision is newer than `analyze.result.at` (the user's guided-pass answer to the exhaustion question); else refuses naming the loop count and the three choices. Escalation never enters `remediate`, so it consumes no cycle.

Any newer non-auto answer is safe (grill Q3; stated in `DESIGN.md` too): abort ends the run, an override never enters `remediate`, and a fresh baseline records a newer `result.at` first, so only a guided pass reaches it.

### `analyze-record`

Before updating `result`: no valid baseline and `reports` empty, the new record becomes the baseline; no stored baseline but derivable, the derived one is stored; otherwise the baseline is untouched. `--fresh-baseline` sets the new record as baseline and is refused (state and HEAD unchanged) when a baseline exists or is derivable.

### `checkpoint remediate`

Inside the same mutate as the gate and history, increment `analyze.loops` and `analyze.pass` only while the recorded `stage` is `remediate`, so a repeated checkpoint never charges twice.

### `amendment-check <draft> [--sha256 <hex>]`

Prints `{"draft", "sha256"}`. Missing or unreadable draft: exit 1 naming the path. `--sha256` given and different: exit 1 naming approved and current hashes. Never writes.

### Orchestrator (SKILL.md step 5)

After `analyze-record`: lite with CRITICAL or HIGH escalates as today (re-analysis into `factory/analyze-<n>-full.md`, no cycle). Otherwise try `checkpoint analyze --next implement`; allowed, go to step 6. Refused: read `factory show` and route in FR-024's order:

1. Open `pending_clarify` or an unanswered `requires_user` question: `clarify` or the relay wait; no cycle charged.
2. Zero reports: run analyze, no user question.
3. No stored `analyze.baseline`: ask re-run as fresh baseline (`analyze-record --fresh-baseline`), override, or abort.
4. Unmet targets, `loops < 2`: `checkpoint analyze --next remediate`, spawn remediate (with the resolved `speckit-constitution` path), `checkpoint remediate --next analyze` (or `clarify` when `pending_clarify` is non-empty), recheck.
5. Unmet targets, `loops >= 2`: `NOTIFY`; ask the exhaustion question (`requires_user`) with baseline and latest counts and unmet targets: guided pass (`decisions-add analyze <qid> '<guidance>'`, then cycle), `gate-override` (`decisions-add ... --kind gate-override`, then checkpoint), or abort.

Step 5's done condition becomes: acceptance targets met with no protected question open, or a recorded `gate-override`.

### Remediate role (spec-builder.md)

Replace "Constitution conflicts are fixed in the artifacts, never in the constitution": a finding warranting a constitution change gets `factory/constitution-amendment-<n>.md` (exact text, rationale, version bump, implied `DESIGN.md` changes) and a `requires_user` approval question carrying `amendment-check`'s sha256; the constitution is untouched. With an approved answer, a fresh remediate runs `amendment-check <draft> --sha256 <approved>`: pass applies exactly the draft through `speckit-constitution`; failure asks fresh approval and applies nothing. Declined, aborted or overridden: fix in artifacts or leave the finding counted. The analyze stage names an escalated re-analysis `analyze-<n>-full.md`.

### Quality constraints

- Data integrity: writes go through the locked atomic writer; gates evaluate fresh state inside the lock; refusals change nothing. Integer arithmetic only.
- Security: `amendment-check` is read-only and executes nothing.
- Compatibility: additive state field (FR-010 to FR-012). Observability: refusals name every unmet target with counts.

## Test seams

- Seam: `factory_cli.checks.gate_violation(state, "implement")` - acceptance targets against stored or derived baseline. Failure paths: CRITICAL > 0; HIGH > 0 including a new HIGH on a clean baseline; total exactly half (12 -> 6) and above; LOW exactly half (6 -> 3); odd baseline (7 -> 4); zero baseline with nonzero latest (LOW 0 -> 1); `pending_clarify` non-empty with targets met; unanswered `requires_user` relay question; no baseline with zero reports, several reports, or a result naming another report.
- Seam: `factory_cli.checks.gate_violation(state, "remediate")` - cycle cap. Failure paths: `loops == 2` with no decision; an `auto: true` analyze decision; a guided decision older than `analyze.result.at`.
- Seam: `bin/factory analyze-record` - baseline set once, preserved by later records, derived for legacy runs, `--fresh-baseline`. Failure paths: `--fresh-baseline` with an existing or derivable baseline refused with state and HEAD unchanged.
- Seam: `bin/factory checkpoint` (remediate and into implement) - cycle increment and gate refusal. Failure paths: a repeated `checkpoint remediate` after the stage advanced does not increment; refused into `remediate` at the cap leaves state unchanged; into `implement` after remediate with the stale pre-remediation result is refused until a fresh analysis is recorded.
- Seam: `bin/factory resume` - baseline and `loops` preserved across resume on another harness. Failure paths: none.
- Seam: `factory_cli.state.validate_state` - `analyze.baseline` shape. Failure paths: negative count; missing count; non-integer count; empty `report`.
- Seam: `bin/factory amendment-check` - prints the draft sha256. Failure paths: missing draft exits 1; changed draft (hash mismatch) exits 1; constitution file byte-identical after each.
- Exempt: `DESIGN.md`, `docs/adr/0014-analyze-acceptance-targets.md`, `docs/factory-overview.md`, `docs/product-brief.md`, `core/skills/factory/SKILL.md`, `core/skills/factory/references/state.md`, `core/roles/spec-builder.md` - documentation only (agent instructions and overview docs).
- Overridden: none

Confirmed: 2026-11-04 - Q1 accepted - seams: `factory_cli.checks.gate_violation(state, "implement")`, `factory_cli.checks.gate_violation(state, "remediate")`, `bin/factory analyze-record`, `bin/factory checkpoint` (remediate and into implement), `bin/factory resume`, `factory_cli.state.validate_state`, `bin/factory amendment-check`; failure paths: implement gate -> CRITICAL > 0, HIGH > 0 including a new HIGH on a clean baseline, total exactly half (12 -> 6) and above, LOW exactly half (6 -> 3), odd baseline (7 -> 4), zero baseline with nonzero latest (LOW 0 -> 1), `pending_clarify` non-empty with targets met, unanswered `requires_user` relay question, no baseline with zero reports / several reports / a result naming another report; remediate gate -> `loops == 2` with no decision, an `auto: true` analyze decision, a guided decision older than `analyze.result.at`; analyze-record -> `--fresh-baseline` with an existing or derivable baseline refused, state and HEAD unchanged; checkpoint -> repeated `checkpoint remediate` after the stage advanced does not increment, refused into `remediate` at the cap leaves state unchanged, into `implement` with the stale pre-remediation result refused until a fresh analysis is recorded; resume -> none; validate_state -> negative count, missing count, non-integer count, empty `report`; amendment-check -> missing draft exits 1, changed draft (hash mismatch) exits 1, constitution file byte-identical after each. Snapshot of the accepted question: `factory/relay-plan-1.json` (Q1).

## Validation

- `python3 -m unittest discover -s tools` passes, including the spec's acceptance examples (12/6, exactly half, odd and zero baselines, new serious finding, resume, legacy derivation and refusal, amendment refusal, recheck after remediation).
- Escalation (US2.4, US3.3, SC-004; grill Q4) is verified through the `analyze-record` seam: a later record keeps the baseline and `loops`; no new seam or failure path.
- Build command renders all five harnesses, `dist/` untracked, `bash -n install.sh`.
- End to end: new `DESIGN.md` "Analyze acceptance targets validation": a real run keeps the baseline across recheck and escalation, stops after 2 repair cycles, and fast mode leaves the exhaustion question unanswered.

## Complexity Tracking

None.
