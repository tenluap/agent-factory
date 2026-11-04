# Analyze acceptance targets are baseline-relative, capped at two repair cycles, and amendments need an approved hash

2026-11-04: the analyze loop let implementation proceed on "remediate once" without measuring the result against the first analysis. A run could enter implementation with findings that were never reduced, and a repaired run could loop without a bound. The gate also compared only the latest counts, so a regression on a clean baseline went unnoticed unless it was CRITICAL or HIGH. Constitution changes proposed during remediation had no approval step, so an amendment could land without the user seeing its exact text. This ADR records the rule that replaces those paths (spec 019; FR-001..FR-024).

## Context

- The first completed analyze report is the baseline (`analyze.baseline`, FR-001). `analyze-record` sets it once; later records change only `analyze.result`, and escalation (`analyze-<n>-full.md`) changes neither the baseline, `pass` nor `loops` (FR-002, FR-003). `--fresh-baseline` is the only explicit replacement, and it is refused when a baseline exists or is derivable (FR-012).
- Legacy runs without a stored baseline derive it only when `analyze.reports` holds exactly one report and `analyze.result.report` names it. Report markdown is never parsed for counts (FR-010, FR-011).
- The implement gate (`factory_cli/checks.py`) refuses until CRITICAL is 0, HIGH is 0, total and LOW meet the integer half rule against the baseline, and a zero baseline count stays zero. A refusal names every unmet target with its counts (FR-004..FR-009).
- Protected questions (`pending_clarify` and unanswered `requires_user` relay questions) keep blocking independently of the counts (FR-007).
- A gate into `remediate` caps automatic repair cycles at 2 (`analyze.loops`), and `checkpoint remediate` is the only writer of `loops` and `pass` (FR-014).
- At the cap the orchestrator notifies the baseline counts, latest counts and unmet targets, then asks an exhaustion question that is `requires_user` and never auto-accepted in fast mode (FR-016, FR-017).
- A constitution amendment draft is written to `factory/constitution-amendment-<n>.md`, approved by exact SHA-256, and applied only after `factory amendment-check <draft> --sha256 <approved>` verifies it (FR-018..FR-021).
- The orchestrator classifies refusals from `factory show`, never from the refusal text (FR-024).

## Decision

1. **Targets.** Implementation requires CRITICAL 0 and HIGH 0 in the latest analysis. Total and LOW must satisfy `2 * latest < baseline`, or `latest == 0` when the baseline is 0. Integer arithmetic only: exactly half fails (12 -> 6 refused), and an odd baseline is judged on its exact value (7 -> 3 passes, 7 -> 4 refused). Newly discovered findings count, including a new HIGH on a clean baseline. MEDIUM has no separate target beyond the total (Q1, Q6).
2. **Baseline immutability.** `analyze.baseline` is `{critical, high, medium, low, report, at}` with non-negative integer counts. It is written once by `analyze-record` (or derived for a legacy run as in Context) and preserved across records, resume and escalation (Q1, Q4).
3. **Repair cap.** Each remediate-plus-recheck cycle increments `analyze.loops`; the cap is 2 per run on either chain. It applies to MEDIUM/LOW-only failures too, replacing the lite "remediate once" and full-chain "loops < 2 on CRITICAL/HIGH" rules. Lite-to-full escalation on CRITICAL/HIGH is kept and consumes no cycle (FR-013, Q2).
4. **Exhaustion.** After two unsuccessful cycles the run pauses on a `requires_user` question offering a guided pass, a recorded `gate-override`, or abort. A newer non-auto answer is the only route back into `remediate` (Q3).
5. **Approved-only amendments.** Remediate writes the exact draft, rationale and version bump to `factory/constitution-amendment-<n>.md` and asks a `requires_user` approval carrying its SHA-256. The constitution changes only when a fresh remediate verifies that hash. Any change to the draft needs a new approval; declined or missing approval leaves the constitution byte-identical (Q5).

## Considered options

- **Keep "remediate once" and check CRITICAL/HIGH only**: smallest change, but a clean baseline could regress to many MEDIUM/LOW findings without a stop, and nothing bounds repeated repair.
- **Compare against the previous analysis instead of the first**: each cycle could pass while the run drifts upward over time. Rejected; the first analysis is the fixed reference the user saw.
- **Parse report markdown for counts when no baseline is stored**: would make legacy runs work without a re-run, but a report's layout is not a contract. Rejected in favour of the one-report derivation and the fresh-baseline path (Q4).
- **Hash the constitution after amendment instead of the draft**: the approval would cover the result rather than the text the user read. Rejected; the draft is the approved artifact.

## Consequences

- Baseline immutability makes the targets reproducible across resume and escalation. Preserving the baseline means a run cannot reset its reference by recording a new analysis.
- The integer half rule is strict on purpose: a baseline of 12 total allows at most 5 findings. This is stricter than "reduce by half" in prose and is the reason the gate names each unmet target with its counts.
- A legacy run without a trustworthy baseline is refused into implementation until the user re-runs analysis as a fresh baseline, records an override, or aborts. This is a behaviour change for pre-existing runs; `DESIGN.md` records it.
- The exhaustion question and amendment approval are protected: fast mode never answers them, and the constitution never changes without the approved hash.
- The rule is enforced by the CLI writer and gate (`checks.py`, `commands.py`, `cli.py`, `state.py`), not by agent prose. The prose in `SKILL.md`, `references/state.md` and `spec-builder.md` describes it and is checked by the role-behaviour validation in `DESIGN.md`.
