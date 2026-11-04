# Implementation Plan: Enforce Analyze remediation targets

**Branch**: `019-analyze-remediation-targets` | **Date**: 2026-11-04 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/019-analyze-remediation-targets/spec.md`; settled decisions Q1-Q7 in `factory/brief.md`.

## Summary

The implement gate in `factory_cli/checks.py` becomes the single decision point for the analyze loop: it compares `analyze.result` with a new `analyze.baseline` and refuses, naming every unmet target, until CRITICAL and HIGH are 0 and total and LOW meet the integer half rule. `analyze-record` sets the baseline once. A new gate into `remediate` caps automatic repair cycles at 2, and `checkpoint remediate` becomes the writer that increments `analyze.loops` and `analyze.pass` (no writer exists today, contrary to ADR 0006). A small `amendment-check` command hashes a constitution amendment draft and verifies an approved hash. Orchestrator and role prose (`SKILL.md` step 5, `roles/spec-builder.md`), `references/state.md`, `DESIGN.md` and ADR 0014 describe the new loop.

## Technical Context

**Language/Version**: Python 3 (standard library only: `hashlib` added), Markdown skill prose.

**Primary Dependencies**: none new.

**Storage**: run `state.json` (v5), additive `analyze.baseline` object. No version bump: readers already ignore unknown analyze keys.

**Testing**: `python3 -m unittest discover -s tools` (existing runner, CI).

**Target Platform**: macOS/Linux shells running the five harnesses.

**Project Type**: CLI plus agent skill prose.

**Performance Goals**: N/A (a few integer comparisons per checkpoint).

**Constraints**: Harness-neutral core (constitution II); state written only by the CLI writer (ADR 0006); refusals leave state and HEAD unchanged; render clean for all five harnesses.

**Scale/Scope**: one gate function, one recorder, one checkpoint branch, one new command, five prose files, one ADR.

## Constitution Check

- **I. Design First**: PASS. `DESIGN.md` ("Modes", "Analyze loop", "Gate table", "Analysis recording repair") is updated in the first task, before core edits.
- **II. Harness-Neutral Core**: PASS. Core prose uses `SHELL`, `ASK`, `NOTIFY`, `RESOLVE`; `speckit-constitution` is a resolved skill like the other SpecKit skills.
- **III. Generated Dist**: PASS. No render change; build renders all five harnesses and checks `dist/` is untracked.
- **IV. Stateless Agents**: PASS. Baseline, cycle count and the approved draft hash live in `state.json` (relay/decisions) and on disk; a fresh remediate re-verifies.
- **V. Simplicity and Reuse**: PASS. Reuses `analyze.result`, `loops`, `pass`, `decisions`, `gate-override`, `requires_user`, the gate table and the checkpoint writer. New field and command have stated reasons below.

## Project Structure

### Documentation (this feature)

```text
specs/019-analyze-remediation-targets/
├── spec.md
├── plan.md
└── tasks.md   (tasks stage)
```

Research, data model and validation are folded into this plan (sections below), matching earlier factory features.

### Source Code (repository root)

```text
core/skills/factory/bin/factory_cli/
├── checks.py     # analyze_baseline(); implement gate targets; remediate gate (cycle cap)
├── commands.py   # analyze-record baseline + --fresh-baseline; checkpoint remediate increments; cmd_amendment_check
├── cli.py        # amendment-check dispatch, --fresh-baseline flag, USAGE
└── state.py      # validate analyze.baseline shape
core/skills/factory/SKILL.md              # step 4 RESOLVE speckit-constitution; step 5 loop rewritten
core/skills/factory/references/state.md   # analyze.baseline, cycle writer, new command
core/roles/spec-builder.md                # remediate: amendment draft, approval, hash check
DESIGN.md
docs/adr/0014-analyze-acceptance-targets.md
tools/tests/test_gates.py                 # gate tests (extended)
tools/tests/test_analyze_record.py        # recorder, checkpoint, resume, amendment-check tests (extended)
```

### New files, abstractions, dependencies

- `docs/adr/0014-analyze-acceptance-targets.md` - file - FR-022 and Q7 require the rule recorded as ADR 0014.
- `analyze.baseline` - abstraction - state field required by FR-001; same shape as `analyze.result` so one validity check serves both.
- `checks.analyze_baseline(analyze)` - abstraction - one source of truth for the stored-or-derived baseline (FR-010), shared by the gate and `analyze-record`.
- `factory amendment-check <draft> [--sha256 <hex>]` - abstraction - one tested hash and verification step for amendment approval (FR-018, FR-019), identical on every harness instead of platform hash tools.
- `analyze-record --fresh-baseline` - abstraction - the only writer path for FR-012's explicit fresh-baseline choice.
- Dependencies: none (`hashlib` is standard library).

No new test files: tests extend `test_gates.py` and `test_analyze_record.py`.

## Research (settled defaults)

- **Draft hash**: SHA-256 of the draft file bytes, lower-case hex, computed by `amendment-check`. Any byte change changes the hash. Alternative (agent-run `shasum`) rejected: differs across platforms and is untestable.
- **Guided pass**: counts as a cycle; `checkpoint remediate` increments `loops` whatever authorized the pass.
- **Amendment number**: `constitution-amendment-<n>.md` with `n` = `analyze.pass`, the same number as `remediation-<n>.md`.
- **Latest equals baseline**: with findings it is unmet by arithmetic (`2 * b < b` is false for `b > 0`); with zero findings it is met.
- **Pre-change runs**: resume under the new rules; FR-010 to FR-012 handle the missing baseline. The old "no `analyze.result` keeps old gate behaviour" note in `DESIGN.md` is replaced: such a run has no trustworthy baseline and is refused (FR-011).
- **Cycle writer**: `checkpoint remediate` increments `loops` and `pass` only while the run's recorded `stage` is `remediate`, so a retried or repeated checkpoint after the stage advanced never charges twice (spec edge case: resume between remediate and recheck).
- **Cycle cap enforcement**: a gate into `remediate`, reusing the gate table, rather than a new command.
- **Skipped**: a writer for `pending_clarify` and `remediations` (pre-existing gap; routing reads the remediate envelope; add when resume needs them persisted); distinct pass numbers for escalation re-analysis (the escalated report reuses the pass number as today; the baseline keeps its stored counts).

## Design

### Data model

`analyze.baseline`: `{ "critical", "high", "medium", "low", "report", "at" }`, non-negative integer counts, spec-relative `report`, writer-stamped ISO `at`. Absent on runs that have not recorded an analysis. `validate_state` rejects a present baseline with a missing, negative or non-integer count, an empty `report` or an unparsable `at`.

### `checks.analyze_baseline(analyze)`

Returns the stored baseline when valid. When absent: returns `analyze.result` only if `reports` has exactly one entry and `result.report` names it; otherwise `None`. Never reads report markdown.

### Implement gate (`gate_violation(s, "implement")`)

1. An analyze `gate-override` decision permits (unchanged).
2. Empty `reports`: refuse (unchanged).
3. Collect every problem, joined with `; ` into one refusal:
   - `pending_clarify` non-empty (existing wording kept);
   - each relay question with `requires_user: true` and no answer, by id;
   - baseline `None`: "no trustworthy baseline: re-run analysis as a fresh baseline, record a gate-override, or abort";
   - otherwise each unmet target with counts: `CRITICAL n (must be 0)`, `HIGH n (must be 0)`, `total n (baseline b, must be < b/2)` or `(baseline 0, must stay 0)`, same for `LOW`. Target met: `latest == 0` when `b == 0`, else `2 * latest < b`.

### Remediate gate (`gate_violation(s, "remediate")`)

Permits while `analyze.loops < 2`. At 2 or more, permits only when a non-auto analyze `answer` decision is newer than `analyze.result.at` (the user's guided-pass answer to the exhaustion question); else refuses naming the loop count and the three choices. Escalation never enters `remediate`, so it consumes no cycle.

### `analyze-record`

Before updating `result`: no valid baseline and `reports` empty, the new record becomes the baseline; no stored baseline but derivable, the derived one is stored; otherwise the baseline is untouched. `--fresh-baseline` sets the new record as baseline and is refused (state and HEAD unchanged) when a baseline exists or is derivable.

### `checkpoint remediate`

Inside the same mutate as the gate and history: when `stage == "remediate"` and the run's recorded `stage` is `remediate`, increment `analyze.loops` and `analyze.pass`.

### `amendment-check <draft> [--sha256 <hex>]`

Prints `{"draft", "sha256"}`. Missing or unreadable draft: exit 1 naming the path. `--sha256` given and different: exit 1 naming approved and current hashes. Never writes.

### Orchestrator (SKILL.md step 5)

After `analyze-record`: lite with CRITICAL or HIGH escalates as today. Otherwise try `checkpoint analyze --next implement`; allowed, go to step 6. Refused for targets and `loops < 2`: `checkpoint analyze --next remediate`, spawn remediate (with the resolved `speckit-constitution` path), `checkpoint remediate --next analyze` (or `clarify` when `pending_clarify` is non-empty). Refused with `loops >= 2`: `NOTIFY` and ask one `requires_user` question showing baseline counts, latest counts and the refusal's unmet targets: guided pass (`decisions-add analyze <qid> '<guidance>'`, then cycle), `gate-override` (`decisions-add ... --kind gate-override`, then checkpoint), or abort. Untrustworthy baseline: ask re-run as fresh baseline (`analyze-record --fresh-baseline`), override, or abort.

### Remediate role (spec-builder.md)

Replace "Constitution conflicts are fixed in the artifacts, never in the constitution" with: a finding that warrants a constitution change gets `factory/constitution-amendment-<n>.md` (exact text, rationale, version bump) and a `requires_user` approval question carrying `amendment-check`'s sha256; the constitution is untouched. A fresh remediate with an approved answer runs `amendment-check <draft> --sha256 <approved>`; pass applies exactly the draft through `speckit-constitution`; failure asks a fresh approval and applies nothing. Declined: fix in artifacts or leave the finding counted.

### Quality constraints

- Data integrity: every write goes through the locked atomic writer; gate evaluation stays inside the writer's lock on fresh state; refusals change nothing.
- Correctness: integer arithmetic only; no rounding.
- Security: `amendment-check` is read-only; no input is executed.
- Compatibility: additive state field; legacy runs handled by FR-010 to FR-012.
- Observability: refusal text names every unmet target with counts.

## Test seams

- Seam: `factory_cli.checks.gate_violation(state, "implement")` - acceptance targets against stored or derived baseline. Failure paths: CRITICAL > 0; HIGH > 0 including a new HIGH on a clean baseline; total exactly half (12 -> 6) and above; LOW exactly half (6 -> 3); odd baseline (7 -> 4); zero baseline with nonzero latest (LOW 0 -> 1); `pending_clarify` non-empty with targets met; unanswered `requires_user` relay question; no baseline with zero reports, several reports, or a result naming another report.
- Seam: `factory_cli.checks.gate_violation(state, "remediate")` - cycle cap. Failure paths: `loops == 2` with no decision; an `auto: true` analyze decision; a guided decision older than `analyze.result.at`.
- Seam: `bin/factory analyze-record` - baseline set once, preserved by later records, derived for legacy runs, `--fresh-baseline`. Failure paths: `--fresh-baseline` with an existing or derivable baseline refused with state and HEAD unchanged.
- Seam: `bin/factory checkpoint` (remediate and into implement) - cycle increment and gate refusal. Failure paths: a repeated `checkpoint remediate` after the stage advanced does not increment; refused into `remediate` at the cap leaves state unchanged; into `implement` after remediate with the stale pre-remediation result is refused until a fresh analysis is recorded.
- Seam: `bin/factory resume` - baseline and `loops` preserved across resume on another harness. Failure paths: none.
- Seam: `factory_cli.state.validate_state` - `analyze.baseline` shape. Failure paths: negative count; missing count; non-integer count; empty `report`.
- Seam: `bin/factory amendment-check` - prints the draft sha256. Failure paths: missing draft exits 1; changed draft (hash mismatch) exits 1; constitution file byte-identical after each.
- Exempt: `DESIGN.md`, `docs/adr/0014-analyze-acceptance-targets.md`, `core/skills/factory/SKILL.md`, `core/skills/factory/references/state.md`, `core/roles/spec-builder.md` - documentation only (agent instructions).
- Overridden: none

## Validation

- `python3 -m unittest discover -s tools` passes, including the spec's acceptance examples (12/6, exactly half, odd and zero baselines, new serious finding, resume, legacy derivation and refusal, amendment refusal, fresh analysis after remediation).
- Build command renders all five harnesses, `dist/` untracked, `bash -n install.sh`.

## Complexity Tracking

None.
