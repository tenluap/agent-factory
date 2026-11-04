# Implementation Plan: Close Orchestrator Bookkeeping Gaps

**Branch**: `024-orchestrator-gaps` | **Date**: 2026-11-04 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/024-orchestrator-gaps/spec.md`

## Summary

Extend four existing state-CLI writers so that review-loop bookkeeping needs no hand edits:

1. `checkpoint review` derives `review.round` from verdict folders; `checkpoint fix` increments `review.fix_rounds` with the same stage-guard idempotency as the `remediate` counters (ADR 0006).
2. `answer` accepts an optional full question (`--question '<json>'`) and renders an immutable relay record `<spec_dir>/factory/relay/<stage>-<qid>.md` for `requires_user` questions, committed with the answer.
3. `ledger-add` detected-overrun detail states the excess (rounded up), the budget and the total.
4. `budget` and `ledger-add` accept `--round <n>` / `--full`; reviewer roles on a full-diff review resolve the round-1 reviewer budget (`budget.review_full_s`, default 600, never below the role's normal budget).

DESIGN.md records each change first; state.md and SKILL.md step 7 document the flags and the review-stage relay path; design-code-mapping.md §5 gets the reservation order that feeds `checkpoint fix`. Details: [research.md](research.md), [data-model.md](data-model.md), [contracts/cli.md](contracts/cli.md), [quickstart.md](quickstart.md).

## Technical Context

**Language/Version**: Python 3 (standard library only), Markdown references

**Primary Dependencies**: none new

**Storage**: run `state.json` (schema version 5, unchanged) and Markdown files under the spec directory

**Testing**: `unittest`, `python3 -m unittest discover -s tools`; CLI driven through `tools/tests` `Sandbox.cli`

**Target Platform**: macOS/Linux shells running any of the five harnesses

**Project Type**: CLI plus harness-neutral skill/reference files rendered by `tools/render.py`

**Performance Goals**: none beyond today; `checkpoint review` adds one directory listing of `factory/reviews/`

**Constraints**: single writer of `state.json` (state.md "CLI"); refusals before any state write; no schema bump; config never fails the run

**Scale/Scope**: four writers in `commands.py`, `budget.py`, `cli.py`; three reference files; DESIGN.md

### Quality requirements

- **Data integrity**: every new refusal (`answer` record conflict, malformed `--question`, bad `--round`) fires before `write_run`, so a refused call writes nothing. Counter increments are guarded by the run's stage so a retried checkpoint never double-counts. The relay record is never overwritten.
- **Error/resource limits**: malformed budget config falls back per entry (FR-017). `--round` must be a positive integer, else usage exit 2.
- **Security**: `<stage>` and `<qid>` become a file name only when a record is due (`requires_user: true` question on a worktree run). In that case the writer refuses a qid or stage that is not `[A-Za-z0-9_-]+` (exit 1, before any write) so no path escapes `factory/relay/`; answers with no record due are not checked (FR-009).
- **Compatibility**: old fixtures without verdict folders keep `review.round` unchanged; `answer` without `--question` and without `requires_user` behaves exactly as today; `budget <role>` and `ledger-add` without the new flags resolve as today.
- **Observability/delivery**: no new telemetry. Checkpoint result gains a `review` object (FR-004). Rollback = revert the commit; no migration.
- **Dependencies**: none added.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Design First | PASS | Task 1 edits DESIGN.md ("Time budget", review loop, relay) before code tasks. |
| II. Harness-Neutral Core | PASS | Edits in `core/` use only `SHELL` CLI calls and neutral verbs; no harness names. |
| III. Generated Dist | PASS | No `dist/` edits; build renders all five harnesses; `git ls-files -- dist/` stays empty. |
| IV. Stateless Agents | PASS | Counters and relay records live in `state.json` / on disk. |
| V. Simplicity and Reuse | PASS | Extends `checkpoint`, `answer`, `budget`, `ledger-add`; no new command, file module or role. New config key and flags have stated reasons below. |

Post-design re-check: PASS (no violations; Complexity Tracking empty).

## Project Structure

### Documentation (this feature)

```text
specs/024-orchestrator-gaps/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/cli.md
└── tasks.md            # next stage
```

### Source Code (repository root)

```text
DESIGN.md                                    # FR-019: record first
core/skills/factory/SKILL.md                 # step 7: round/full flags, relay path, drop hand increment
core/skills/factory/references/state.md      # Checkpoint, CLI, Schema
core/skills/factory/references/design-code-mapping.md  # §5: verify, then checkpoint fix counts and clears
core/skills/factory/bin/factory_cli/
├── budget.py        # REVIEWER_ROLES, resolve(role, config, full=False)
├── commands.py      # cmd_checkpoint, cmd_answer (+ record render), cmd_budget, cmd_ledger_add, overrun_issue
└── cli.py           # --round/--full on budget and ledger-add; --question on answer
tools/tests/
├── test_budget.py   # budget and overrun seams
├── test_commands.py # checkpoint counters, answer relay record
└── fixtures/        # reused (state-v4.json etc.)
```

**Structure Decision**: Single existing CLI package; extend modules in place.

### New files, abstractions, dependencies

- `specs/024-orchestrator-gaps/*` - file - SpecKit artifacts for this feature.
- `<spec_dir>/factory/relay/<stage>-<qid>.md` (runtime output) - file - FR-006 acceptance evidence; replaces the hand-written records of run 018.
- `budget.REVIEWER_ROLES` - abstraction - FR-015 names the reviewer set once for `budget` and `ledger-add`.
- `budget.review_full_s` config key - abstraction - FR-013 round-1 reviewer budget must be configurable next to `default_s`.
- `render_relay_record` helper in `commands.py` - abstraction - one renderer for the FR-006 layout, used only by `cmd_answer`.
- `answer --question` flag - abstraction - FR-005: store the full question so the record can render it.
- `budget`/`ledger-add` `--round <n>` flag - abstraction - FR-013/FR-016: select round-1 or delta reviewer budget.
- `budget`/`ledger-add` `--full` flag - abstraction - FR-013: escalated full-mode re-run uses the round-1 budget.
- `review` result field on `checkpoint review|fix` - abstraction - FR-004: cap state readable without opening `state.json`.
- `full` result field on `budget` - abstraction - FR-013: shows which budget was resolved.
- `record` and `unchanged` result fields on `answer` - abstraction - FR-006/FR-008: cite the record path; report the identical re-answer no-op.
- Dependencies: none.

No new source module: the renderer is small and has one caller, so it stays in `commands.py` beside `cmd_answer`.

## Design decisions

1. **Round derivation (FR-001)**: in `cmd_checkpoint`, for `stage == "review"` with a worktree, scan `<worktree>/<spec_dir>/factory/reviews/round-<n>/verdict.json`; `review.round = max(current, highest n)`. No match leaves it unchanged. Escalated re-run reuses the folder, so the value does not move.
2. **Fix counter (FR-002/FR-003)**: `checkpoint review --next fix --design-fix <verdict>` reserves an active design attempt without incrementing. After the fixer completes and verification passes, inside `checkpoint fix`'s `mutate`, when `stage == "fix" and s["stage"] == "fix"`, increment `review.fix_rounds` unless `review.pending_design_fix` is a dict whose `attempt` equals the current counter (a legacy reservation that already counted the attempt), and clear the reservation in that same locked write. A retried checkpoint after a commit failure sees the advanced stage and skips, mirroring `remediate`. The counter increments only at the stored stage `fix`; an approver-requested fix gets no special counting rule.
3. **Checkpoint result (FR-004)**: for `review` and `fix` checkpoints add `"review": {"round": n, "fix_rounds": m}` to the returned JSON, including the commit-failure return.
4. **Relay record (FR-005..FR-009)**: `answer <qid> '<answer>' [--question '<json>']`. The JSON must be an object whose `id` equals `<qid>` (else exit 1). Stored in the open round when the id is absent or stored as id-only. After resolving the stored question, if `requires_user is True` and the run has a worktree, a record is due. Pre-write checks, only when a record is due: qid and stage match `[A-Za-z0-9_-]+` (else exit 1); existing record with the same answer → return `{"answered": qid, "unchanged": true}` only if the record is in HEAD and record and state are clean; otherwise complete the pending commit; different answer → exit 1 naming the path. Record written after the state write and before `commit_worktree`, which already stages `spec_dir`, so both land in one commit.
5. **Overrun wording (FR-011)**: `excess = ceil((duration_ms - seconds*1000)/1000)`, `total = ceil(duration_ms/1000)`; detail `"<role> ran <excess>s past its <seconds>s budget (<total>s total) without a self-report"`.
6. **Round-1 budget (FR-013..FR-018)**: `budget.resolve(role, config, full=False)`. When `full` and `role in REVIEWER_ROLES`: `max(normal, review_full_s if positive int else 600)`. `--round 1` or `--full` sets `full`; `--round n>1` is delta; non-reviewers ignore both. `cmd_budget` and `overrun_issue` share the call. `budget` output adds `"full": bool`.
7. **SKILL.md step 7 and design-code-mapping.md §5**: pass `--round <n>` (or `--full` on an escalated re-run) to `budget` and `ledger-add`. For a fix, use `checkpoint review --next fix` (add `--design-fix <verdict>` for active design runs), spawn the fixer, verify after it returns done, then use `checkpoint fix --next review`. On resume, re-spawn the saved fixer before verification and checkpointing; preserve a design reservation. The checkpoint counts and clears the reservation atomically, with no double count for legacy attempts. When clean or capped, use `checkpoint review --next approver`. Document `requires_user` relay in every stage (`answer --question`, cite the record path; cruise answers protected questions only with `--cruise-override`), with round-unique ids for verdict questions.

## Test seams

Declarations (public seams; tests drive the CLI through `Sandbox.cli` in `tools/tests`):

- **S1 `factory checkpoint review|fix`** (`commands.cmd_checkpoint`) - FR-001..FR-004, FR-021. Required injected failure paths: (a) commit failure after the state write, then retry → `fix_rounds` incremented once; (b) no `round-<n>/verdict.json` present → `review.round` unchanged; (c) active `review.pending_design_fix` with `attempt` equal to the counter → no increment; (d) repeated `checkpoint fix` after the stage moved on → no increment. Fix-round extension: `checkpoint review --next fix --design-fix <verdict-path>` writes the reservation and `checkpoint fix` atomically counts and clears it, including legacy resume.
- **S2 `factory answer [--question]`** (`commands.cmd_answer`) - FR-005..FR-009. Required injected failure paths: (a) existing record with a different answer → exit 1 naming the path, state and files unchanged; (b) malformed `--question` JSON or `id` mismatch → exit 1, nothing written; (c) unsafe qid/stage characters with a record due (`requires_user: true` question on a worktree run) → exit 1, nothing written; the same characters with no record due → answered as today (FR-009); (d) pending run without worktree → answer stored, no record. Fix-round extension: answer commit failure after state and record writes, then identical retry commits both.
- **S3 `factory budget <role> [--round n | --full]`** (`commands.cmd_budget` / `budget.resolve`) - FR-013..FR-015, FR-017. Required injected failure paths: (a) missing or malformed `review_full_s` / config → 600 fallback without failure; (b) non-positive or non-integer `--round` → usage exit 2.
- **S4 `factory ledger-add [--round n | --full]` overrun detection** (`commands.overrun_issue`) - FR-011, FR-012, FR-016. Required injected failure paths: (a) duration 1 ms over budget → excess rounds up to 1 s; (b) self-reported overrun → detail unchanged.

`bench.py score` already reads `review.round` / `review.fix_rounds` (tools/bench.py:94); S1 tests prove the values, existing `test_bench.py` covers the read. No new seam.

Exempt: DESIGN.md - documentation only
Exempt: core/skills/factory/SKILL.md step 7 - documentation only (orchestrator instructions)
Exempt: core/skills/factory/references/state.md - documentation only
Exempt: core/skills/factory/references/design-code-mapping.md §5 - documentation only
Overridden: none

Confirmed: 2026-11-04 - remediate Q1 accepted (cruise override) - seams: S1 `factory checkpoint review|fix`, S2 `factory answer [--question]`, S3 `factory budget <role> [--round n | --full]`, S4 `factory ledger-add [--round n | --full]` overrun detection; failure paths: S1 - (a) commit failure after state write then retry increments `fix_rounds` once, (b) no `round-<n>/verdict.json` leaves `review.round` unchanged, (c) active `pending_design_fix` with `attempt` equal to the counter does not increment, (d) repeated `checkpoint fix` after the stage moved on does not increment; S2 - (a) existing record with a different answer exits 1 naming the path, state and files unchanged, (b) malformed `--question` JSON or `id` mismatch exits 1, nothing written, (c) unsafe qid/stage characters with a record due (`requires_user: true` question on a worktree run) exit 1, nothing written; the same characters with no record due are answered as today, (d) pending run without worktree stores the answer, no record; S3 - (a) missing or malformed `review_full_s` / config falls back to 600 without failure, (b) non-positive or non-integer `--round` is a usage exit 2; S4 - (a) duration 1 ms over budget rounds excess up to 1 s, (b) self-reported overrun keeps detail unchanged.

Confirmed fix-round extension: 2026-11-04 - orchestrator reports cruise override at fix stage: S2 answer commit-failure retry; S1 design-reservation writer flag on `checkpoint review --next fix` and atomic clear in `checkpoint fix`; fix-stage resume re-spawns the fixer before counting. Existing S2(c) acceptance is narrowed to refusing unsafe qid/stage only when a record is due. All other declared scope remains unchanged.

Test runner: existing (`python3 -m unittest discover -s tools`); none added.

Verification: build command renders five harnesses and `bash -n install.sh`; full test suite; `test -z "$(git ls-files -- dist/)"`.

## Complexity Tracking

None.
