# Brief: agent time budget, session issue backlog, benchmark

Give every factory role spawn a time budget (default 5 minutes, per-role overrides). File-writing roles stop cooperatively at their deadline, report why they ran long, and a fresh spawn resumes the stage; reviewers and the judge finish but are recorded. Every overrun, failure, retry, halt and red verify becomes a session issue in run state; when the run ends the issues are exported as a gated improvement backlog that a later, manually started improvement run consumes. A benchmark replays fixture features headlessly and scores runs so factory versions can be compared before and after. Chain: lite, fast mode on.

## Alternatives considered

- Scope: one run for all four pieces (time limit, issue backlog, recursive improver, benchmark) vs. this run covering time limit + issue backlog + benchmark core with the recursive improver deferred (chosen) vs. time limit + backlog only.
- Enforcement: cooperative deadline with post-hoc detection (chosen) vs. hard kill via background spawn + watchdog (tier-2 only, loses uncommitted work) vs. detect-only.
- Diagnosis: the overrunning role self-reports its cause plus orchestrator ledger facts (chosen) vs. a new overrun-analyst role.
- Backlog start: manual `/factory improve` with a CLI gate (chosen) vs. automatic start after PR opens.
- Backlog location: run state + FACTORY_HOME export (chosen) vs. worktree-only file vs. GitHub issue.
- Benchmark: fixture replay driven by headless harness CLI, scored from state.json (chosen) vs. scoring recorded real runs only vs. manual live execution.

## Chosen direction

- Scope: this run delivers the time budget, session issues, gated improvement backlog and benchmark core. The recursive improver agent is a follow-up run that consumes the backlog. Out of scope: improver agent, hard kill, GitHub issue publishing.
- Budget config: `${FACTORY_HOME}/config.json` `budget: { default_s: 300, roles: { <role>: <seconds> } }`; default 5 minutes, per-role override.
- The orchestrator passes a `deadline` (ISO UTC) in every spawn's inputs.
- File-writing roles (spec-builder, code-build, fixer) check the clock between units of work; past the deadline they commit progress and return `partial` with an `overrun` field `{ "cause", "detail" }`. Causes are a closed list: `large-input`, `test-loop`, `retry`, `tool-slow`, `scope-too-big`, `other`.
- `partial` is extended from code-build-only to all three file-writing roles; the orchestrator re-spawns a fresh agent with the same inputs, which resumes from disk.
- Reviewers and the judge have a soft limit: they finish normally; overruns are recorded post-hoc.
- The orchestrator detects overruns after every spawn from the ledger duration vs. the role budget; an overrun without a self-report is recorded with cause `unreported`.
- Session issues: new writer command `factory issue-add <kind> <stage> <role> --cause --detail --duration-ms`; `kind` in `overrun`, `agent-failure`, `retry`, `halt`, `verify-fail`. Stored append-only in `state.json` `issues[]` (state schema v5; readers accept 1-5).
- Existing paths emit issues: failure-policy retry -> `retry`, second failure -> `agent-failure`, `set-status halted` -> `halt`, `verify --fail` -> `verify-fail`.
- Gated backlog: on `set-status pr-open|aborted` the writer exports `${FACTORY_HOME}/improvements/<repo>-<branch>.json` (issues, run totals, factory git sha, status `ready`). The file exists only after the run ends, so the gate is structural. `factory improvements` lists ready backlogs; `factory improvements claim <name>` refuses unless the source run has ended.
- `/factory improve` route (this run): lists ready backlogs and prints a suggested feature text. Starting an improvement run is manual.
- Benchmark: `conformance/bench/` holds fixture feature(s) on `conformance/fixture-repo`, a pre-settled brief and a pending state seeded at the `worktree` stage with fast mode, run with `--stop-at approver` (no auto-approve, no PR). `tools/bench.py run --harness <h>` drives the headless harness CLI (`claude -p`, `opencode run`); `tools/bench.py score <state.json>...` emits JSON (wall time, agent time, spawns, overruns, issues by kind, token estimates, review rounds, pass/fail); `compare a.json b.json` prints the delta. The manual path (run /factory on the fixture, then score) is documented as fallback.
- Testing: unittest for `issue-add`, budget check, export gate, v5 migration, scorer and compare; the scorer is tested on recorded states; live benchmark runs are manual (token cost), not CI. Render all harnesses; `dist/` stays clean.

## Grill decisions

- Resume cap: halt after 3 consecutive `partial` spawns of a stage with no new commit; unlimited while progress is committed.
- Roles stop only between units of work: the unit in flight finishes, then the role returns `partial`; the overshoot is recorded in the issue `detail`.
- The budget is enforced on spawned roles only. Orchestrator verify (build/test) time over budget is recorded as an `overrun` issue with role `orchestrator` and never stopped.
- An overrun both self-reported and detected from the ledger is recorded once.
- Benchmark runs use `--stop-at approver` and are scored at that point; there is no auto-approve flag and no PR.
- Benchmark pass = run reached approver, last verify green, no unresolved blocking findings, and the fixture's own acceptance test (extended per bench feature) passes.
- Chain: lite, fast mode on.
