# Brief — 016-retro-self-improve

## Feature

Add a post-run retro step to the factory. After a run reaches `pr-open` and before `drop`, the orchestrator spawns a dedicated read-only standard-tier `retro` role. It receives the ended run's digest (`factory show` JSON plus the round verdict paths) and mines five improvement signals, returning up to three deduplicated improvement candidates in its envelope. The orchestrator persists accepted candidates into `${FACTORY_HOME}/improvements/` as `ready` backlog entries, feeding the existing `/factory improve` loop. The self-improve loop then compounds: every future run leaves the backlog smarter.

## Decisions (settled in grilling, 2026-10-30)

- **Architecture**: dedicated read-only `retro` role returns candidates in its envelope; the orchestrator writes the backlog files. No inline orchestrator mining, no new deterministic CLI command in v1.
- **Signals, all five v1**: analyze escalation rate; fixer recurring finding classes; judge rejection rate per reviewer; `in-est` outliers per role; halt/issue clusters.
- **Cap and dedupe**: at most 3 candidates per run; a signal already covered by an open `ready` backlog entry is skipped, not duplicated.
- **Trigger scope**: `pr-open` runs only, at `drop` time. Aborted/halted retro triggers are out of scope for this feature.
- **Timing**: retro runs between `set-status pr-open` and `drop` (SKILL.md step 9, after step 4 `set-status`, before step 5 `drop`), so the live state records retro's own spawn cost through `ledger-add` and the digest reads from the worktree.
- **Failure policy**: one fresh retry per the standard failure policy, then skip with a disclosed note; retro never halts or blocks the run — the PR is already open. The skipped retro is named in the final `NOTIFY`.
- **Chain**: full (`specify → clarify → grill-with-docs → plan → tasks → analyze`). Chosen for the cross-file contract surface: new role file, SKILL.md step, protocol envelope shape, DESIGN.md, state/ledger notes.
- **Commands** (confirmed; repo has no CLAUDE.md/AGENTS.md): build `python3 -m compileall -q tools core/skills/factory/bin`; test `python3 -m unittest discover -s tools -p 'test_*.py'`.
- Harness `opencode`, tier 1. Model inspection recorded unverified (partial provider inventory); bounded runtime retry/halt applies on rejection.

## Source

Backlog `claude-factory-015-retro-self-improve` (claimed 2026-10-30T22:26:48Z), originating from the 2026-10-30 EGM/factory improvement analysis conversation.
