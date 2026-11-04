# Implementation Plan: Cruise mode

**Branch**: `021-cruise-mode` | **Date**: 2026-11-04 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/021-cruise-mode/spec.md`; settled decisions Q1-Q7 and confirmed defaults in `factory/brief.md`; clarify Q1 and grill-with-docs Q1-Q4 (spec Clarifications, `CONTEXT.md`, ADR 0014).

## Summary

Add `mode.cruise` and a `cruise_override` marker to run state, both additive and written only through the state CLI. The CLI gains one read-only `mode` command (resolves flags into a mode, rejects the cruise/`--no-fast` conflict) and mode flags on `resume`; `answer` and `decisions-add` gain `--cruise-override`. The validator and the `pr` gate make an automatic approval structurally impossible. Everything else is orchestrator prose: cruise answers relays, grilling, setup offers and analyze exhaustion itself, stops at the approver, and groups the veto list. Adapters document their no-prompt launch option. No render, install or dist change.

## Technical Context

**Language/Version**: Python 3 (standard library only), Markdown skill prose.

**Primary Dependencies**: none new.

**Storage**: run `state.json` v5; additive optional `mode.cruise` and `cruise_override` fields; no version bump.

**Testing**: `python3 -m unittest discover -s tools` (existing runner, `tools/tests/`).

**Target Platform**: macOS/Linux shells running the five harnesses.

**Project Type**: state CLI plus agent skill prose.

**Performance Goals**: N/A (one small JSON write per decision, as today).

**Constraints**: harness-neutral core (constitution II); `DESIGN.md` first (I); render clean (III); every state write through the CLI (FR-005); pre-feature states valid (FR-004).

**Scale/Scope**: 5 harnesses; ~6 CLI functions touched.

## Decisions (research)

- **Marker shape**: a boolean field `cruise_override: true` on relay answers and decision records, absent otherwise. Rationale: `kind` keeps its gate meaning (`answer` | `approved` | `gate-override`), so `checks.py` gates and history cross-checks stay unchanged; absence keeps every older record valid. Alternative rejected: a new decision kind `cruise-override`, which would need new gate logic for analyze exhaustion and would collide with `answer` for protected relay answers.
- **Marker invariants** (validator, `state.py`): `cruise_override` is boolean when present; `true` requires `auto: true`; `true` is never with kind `approved` and never at stage `approver`; a marked `gate-override` is exempt from "a gate decision is never auto". The `analyze`-only restriction on a marked `gate-override` (analyze-exhaustion auto-proceed) is enforced by the `decisions-add --cruise-override` guard, not the validator (clarify Q1).
- **`pr` gate**: `checks.gate_violation` and `permitting_decision` for `pr` share one filtered approver candidate list that drops any record carrying `cruise_override` (tested through `gate_violation` only, clarify Q1), so even a hand-crafted state cannot publish without the user's Approve (FR-015, FR-016).
- **Writer guard**: `answer --cruise-override` and `decisions-add --cruise-override` are refused (exit 1, state and HEAD unchanged) unless the target run has `mode.cruise: true`. This keeps fast mode's protections intact (FR-009). The two-line check sits inline in `cmd_answer` and `cmd_decisions_add`; no shared helper.
- **Mode resolution**: one function `state.resolve_mode(base, flags)` applies `--lite|--full|--fast|--no-fast|--cruise|--no-cruise` in argv order (last wins per pair), sets `fast` true when `cruise` ends on, and raises on the conflict "cruise on (flag or stored) and `--no-fast` present". `--no-cruise` leaves `fast` unchanged. Callers:
  - `factory mode [flags...]`: read-only, base = default `{chain: lite, fast: true, cruise: false}`; prints the mode JSON. Step 0 calls it before any pending state exists and writes the result into the pending state at creation (today's creation path), so a conflict creates nothing (SC-005).
  - `factory resume <run> [flags...]`: base = stored mode (absent `cruise` = false); a conflict exits 5 before the `resumed` entry is written; otherwise mode and the `resumed` entry land in one atomic write. This also gives today's resume `--lite/--full/--fast/--no-fast` a writer.
- **Conflict exit code**: 5 (usage), like `prune --dry-run --delete`; the message names both flags.
- **Mode validation**: `mode.cruise` is boolean when present; `cruise: true` requires `fast: true`.
- **Veto list**: `veto_list` is unchanged (cruise overrides already carry `auto: true`); entries keep `cruise_override`, and the approver prose groups by it. No new digest field.
- **Non-question overrides** use fixed question ids with `decisions-add <stage> <id> '<answer>' --cruise-override`: at stage `grill`: `setup-speckit`, `setup-commands`, `intake`; at `review`: `setup-impeccable`; at `analyze`: `analyze-exhaustion` (with `--kind gate-override`). `STAGES` is unchanged (grill Q2).
- **No-prompt launch**: one bullet `no_prompt_launch` per `adapters/*/harness.md`, verified against each harness's docs (`WEB_FETCH`) when written; an unverifiable option is written as "none documented". Known candidates: Claude Code `--permission-mode bypassPermissions`; Codex `--dangerously-bypass-approvals-and-sandbox`; Copilot CLI `--allow-all-tools`; OpenCode an `allow` permission config; ZCode unknown.

## Constitution Check

- **I. Design First**: PASS. Task 1 records cruise in `DESIGN.md` ("Modes", "Interactive steps", "Approver", "Validation plan") before core/adapter edits; `CONTEXT.md` terms and ADR 0014 were written at grill-with-docs.
- **II. Harness-Neutral Core**: PASS. Core names "the adapter's no-prompt launch option"; concrete options live only in `adapters/*/harness.md`.
- **III. Generated Dist**: PASS. No `render.py` change; build renders all five harnesses.
- **IV. Stateless Agents**: PASS. Mode and markers live in `state.json`; roles read them from state.
- **V. Simplicity and Reuse**: PASS. Reuses `answer`, `decisions-add`, `resume`, `veto_list` and the gates; one new read-only command and one field. Reasons below.

Re-check after design: PASS, no violations.

## Project Structure

### Documentation (this feature)

```text
specs/021-cruise-mode/
├── plan.md
├── spec.md
└── tasks.md   (tasks stage)
```

### Source Code (repository root)

```text
core/skills/factory/bin/factory_cli/
├── state.py      # resolve_mode; mode.cruise + cruise_override validation
├── checks.py     # pr gate ignores cruise_override records
├── commands.py   # cmd_mode; cmd_resume flags; cmd_answer/cmd_decisions_add marker; settled_answers carries marker
└── cli.py        # mode dispatch, resume flags, --cruise-override, USAGE
core/skills/factory/SKILL.md                         # argument-hint, route, preflight, grill, relay, halts, approver, notify
core/skills/factory/references/protocol.md           # relay step 2 under cruise
core/skills/factory/references/state.md              # mode.cruise, cruise_override, CLI surface
core/skills/factory/references/engineering.md        # cruise-override acceptance in "Confirmed test scope"
core/skills/factory/references/design-code-mapping.md # cruise-override exception acceptance
core/roles/spec-builder.md, core/roles/spec-conformance.md # Confirmed line marks cruise override
adapters/*/harness.md                                # no_prompt_launch bullet
DESIGN.md
README.md                                            # --cruise/--no-cruise usage, flag rows, resume example
CONTEXT.md, docs/adr/0014-cruise-mode-overrides-protections-but-never-publishes.md  # written at grill-with-docs
tools/tests/test_cruise.py                           # NEW
```

**Structure Decision**: extend the existing CLI modules; no new module. `resolve_mode` sits in `state.py` beside the other state vocabularies and is shared by `mode` and `resume`.

### New files, abstractions, dependencies

- `docs/adr/0014-cruise-mode-overrides-protections-but-never-publishes.md` - file - records the protection-override and publish-boundary trade-off (grill Q4).
- `tools/tests/test_cruise.py` - file - groups this feature's CLI seams in one suite, as `test_models.py` does for 017.
- `state.resolve_mode(base, flags)` - abstraction - single source of the last-wins and conflict rules for both new runs and resume (DRY, FR-001..FR-003).
- `factory mode [flags...]` - abstraction - read-only CLI entry so the orchestrator checks flags through the same rule before any state exists.
- `mode.cruise`, `cruise_override`, `--cruise-override`, `no_prompt_launch` - abstraction - additive state fields, writer flag and adapter bullet; reasons under "Decisions".
- Dependencies: none.

## Design (orchestrator prose)

- **Route (step 0)**: parse `--cruise/--no-cruise`; call `factory mode <mode flags in order>`; exit 5 names the conflict, create nothing. Ambiguous intake under cruise: delivery, `decisions-add grill intake 'delivery' --cruise-override`.
- **Preflight (step 1)**: under cruise, once per start/resume, print a plain message (no `NOTIFY`, no wait) that harness prompts may still appear unless launched with the adapter's `no_prompt_launch`. Setup offers (`.specify/` or speckit skill missing; detected commands; later the `impeccable` install) run their recommended default without a question and record their fixed id with `--cruise-override` at the stage named in "Non-question overrides". A failing setup command halts.
- **Brainstorm/grill (steps 2-3)**: under cruise the orchestrator answers its own frontier with recommendations (`answer <qid> '<rec>' --auto --stage grill|brainstorm`), confirms its recommended chain and direction, skips the visual companion, writes `brief.md`, continues.
- **Relay (protocol.md step 2)**: under cruise fill every unanswered question that has a usable recommendation: `requires_user` or `pending_clarify` origin with `answer --cruise-override`, the rest with `--auto`. A question with no usable recommendation is shown and waited on (`wait-open`, `NOTIFY`). The batch notice is a log line only. Cruise turned on by resume fills the open round the same way, preserving existing answers.
- **Analyze exhaustion (step 5)**: under cruise `decisions-add analyze analyze-exhaustion 'proceed to implement' --kind gate-override --cruise-override`, checkpoint into implement, carry `analyze.result.report` to the approver.
- **Halts and stop points**: unchanged: red build, second agent failure, stall cap, hard stops, a missing or stale test seam at implement or fix (ENG-4, grill Q1), `--stop-at` still stop and notify.
- **Approver (step 8)**: under cruise show the veto list in two groups: `cruise_override: true` entries (each with stage, question, answer), then the rest; an empty group says "none". When `analyze-exhaustion` exists, show the unresolved report. The `ASK` is never auto-answered; `approved` is recorded only from the user's Approve. Request changes runs the fix loop under cruise and returns here.
- **Notify**: under cruise `NOTIFY` only for real waits (approver, failure halts, stop points, a question without a recommendation).
- **Protected acceptance**: a cruise-override answer to the seam confirmation or a design exception counts as recorded acceptance of that exact scope; the Confirmed line reads `Confirmed: <date> - <Qid> accepted (cruise override) - seams: ...; failure paths: ...`. Scope changes still invalidate it.

### Quality constraints

- Security: no new executed input; answers stay argv strings as today; publishing gated by the user-only `approved` record.
- Data integrity: refused writes leave state and HEAD unchanged; append-only `decisions` untouched; mode and `resumed` entry in one atomic write.
- Errors: conflict and guard refusals name the flags or reason on stderr.
- Compatibility: absent fields read as off; existing fixtures and tests pass unchanged (SC-004).
- Observability: overrides visible in `decisions`, `show` and the approver screen.

## Test seams

- Seam: `bin/factory mode [flags...]` - last-wins per pair, cruise sets fast, no-cruise keeps fast, JSON output, no state written. Failure paths: `--cruise` with `--no-fast` in either order exits 5 naming the conflict; unknown flag exits 5.
- Seam: `bin/factory resume <run> [mode flags]` - updates `mode` (including absent `cruise` read as off) and appends `resumed` atomically. Failure paths: `--no-fast` with cruise on from a flag exits 5, state and HEAD unchanged, no `resumed` entry; `--no-fast` with cruise stored on and no `--no-cruise` exits 5 likewise.
- Seam: `bin/factory answer <qid> <answer> --cruise-override` - stores `auto: true, cruise_override: true`; `checkpoint` migrates the marker into `decisions`; `show` lists it. Failure paths: run without `mode.cruise: true` refused with exit 1, state unchanged.
- Seam: `bin/factory decisions-add ... --cruise-override` - records kind `answer`, or `gate-override` at `analyze` that permits `checkpoint analyze --next implement`. Failure paths: run without `mode.cruise: true` refused; `--kind approved` with the marker refused; `--kind gate-override` with the marker at a stage other than `analyze` refused.
- Seam: `factory_cli.state.validate_state` - pre-feature states (no `cruise`, no marker) valid. Failure paths: non-boolean `mode.cruise`; `cruise: true` with `fast: false`; non-boolean `cruise_override` on a decision or relay answer; marker with `auto: false`; marker on `approved` or at stage `approver`.
- Seam: `factory_cli.checks.gate_violation` into `pr` - user `approved` record permits. Failure paths: a record carrying `cruise_override` at `approver` never permits `pr`.
- Exempt: `DESIGN.md`, `README.md`, `CONTEXT.md`, `core/skills/factory/SKILL.md`, `references/protocol.md`, `references/state.md`, `references/engineering.md`, `references/design-code-mapping.md`, `core/roles/spec-builder.md`, `core/roles/spec-conformance.md` - documentation only (agent prose; validated by the `DESIGN.md` validation plan).
- Exempt: `adapters/*/harness.md` - documentation only.
- Overridden: none

Confirmed: 2026-11-04 - Q1 accepted - seams: `bin/factory mode`, `bin/factory resume` mode flags, `bin/factory answer --cruise-override`, `bin/factory decisions-add --cruise-override`, `factory_cli.state.validate_state`, `factory_cli.checks.gate_violation` (`pr`); failure paths: `mode` -> `--cruise` with `--no-fast` in either order exits 5 naming the conflict, unknown flag exits 5; `resume` -> `--no-fast` with cruise on from a flag exits 5 with state and HEAD unchanged and no `resumed` entry, `--no-fast` with cruise stored on and no `--no-cruise` exits 5 likewise; `answer` -> run without `mode.cruise: true` refused with exit 1, state unchanged; `decisions-add` -> run without `mode.cruise: true` refused, `--kind approved` with the marker refused, `--kind gate-override` with the marker at a stage other than `analyze` refused; `validate_state` -> non-boolean `mode.cruise`, `cruise: true` with `fast: false`, non-boolean `cruise_override` on a decision or relay answer, marker with `auto: false`, marker on `approved` or at stage `approver`; `gate_violation` -> a record carrying `cruise_override` at `approver` never permits `pr`.

## Complexity Tracking

None.
