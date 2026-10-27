# Feature Specification: Agent time budget, session issue backlog, benchmark

**Feature Branch**: `010-agent-time-budget`

**Created**: 2026-10-27

**Status**: Draft

**Input**: User description: "Improve the software/agent factory: put a work time limiter on every agent and sub agent (under 5 minutes). If an agent exceeds that time, stop it, identify why it took long, note the issue, and collect it into a pending issue for this session. Resume the stopped process to continue the factory flow. The saved pending improvement may start only once the session that created it is done. Use the session's identified issues to improve the factory recursively (agents, tools, skills). Add a benchmark to score and test before/after." (see `factory/brief.md` for the settled decisions)

## Clarifications

### Session 2026-10-27 (grill-with-docs)

- Q: What is authoritative for the FR-004 stall cap? → A: The spec (FR-004 stands): every `partial` return counts toward the three, whatever its stop reason; overrun records of never-stopped roles (reviewers, judge, orchestrator) never count. Design artifacts widen in the plan re-run.

## User Scenarios & Testing *(mandatory)*

The user is a developer running factory sessions who needs: no run silently eating hours of agent time, every thing that went wrong recorded where they can read it, improvement work startable only after its source run is over, and factory versions comparable on equal footing.

### User Story 1 - Every spawned agent works inside a time budget (Priority: P1)

A run owner sets a time budget (default 5 minutes, overridable per role) and every agent the factory spawns — including parallel and sub-agent spawns — receives a deadline. A file-writing role that runs past its deadline finishes the unit of work in flight, commits that progress, reports why it ran long, and a fresh spawn of the same stage continues from disk. A reviewer or the judge is never stopped: it finishes, and its overrun is recorded afterwards.

**Why this priority**: unbounded agent time is the problem the feature exists to solve; the rest of the feature reads the records this story produces.

**Independent Test**: Set a small budget for one file-writing role, run that stage, and observe the `partial` return with its reason, the recorded overrun, and a continuation that picks up from committed progress.

**Acceptance Scenarios**:

1. **Given** a budget configuration with a per-role override, **When** a role is spawned, **Then** the spawn carries a deadline derived from that role's budget (default 5 minutes when no override applies).
2. **Given** a file-writing role working past its deadline, **When** it reaches the end of the unit of work in flight, **Then** it commits that progress and returns `partial` with a report of why it ran long, drawn from a closed list of causes plus a free-text detail, and the overshoot beyond the deadline is visible in that detail.
3. **Given** such a `partial` return, **When** the orchestrator continues the stage, **Then** a fresh spawn receives the same inputs and resumes from the work already on disk.
4. **Given** three consecutive `partial` returns for the same stage with no new commit between them, **When** the orchestrator checks, **Then** the run halts; while each stop is accompanied by committed progress, resumption continues without a cap.
5. **Given** a reviewer or the judge running past its budget, **When** the spawn finishes, **Then** it is never stopped and its overrun is recorded afterwards.

---

### User Story 2 - Everything that went wrong becomes a session issue (Priority: P2)

A run owner reads the run state and finds one record for every overrun, agent failure, retry, halt and red verify of the session — each tagged with its kind, stage, role, cause, detail and duration — so a later reader can group and count them without re-deriving anything.

**Why this priority**: the improvement backlog and the benchmark both consume these records; without them the later stories have no data.

**Independent Test**: Drive each of the five event paths in the automated suite and assert exactly one issue record per event in the run state.

**Acceptance Scenarios**:

1. **Given** any overrun — self-reported, detected after the fact, or both, **When** the issue is recorded, **Then** exactly one issue exists for it, with cause `unreported` only when the role did not self-report.
2. **Given** a non-deadline `partial` stop (e.g. low context), a retry under the failure policy, a second failure of the same agent, a halted run, and a red verify, **When** each happens, **Then** each records its issue with the matching kind (`retry`, `retry`, `agent-failure`, `halt`, `verify-fail`). Only the partial stop carries `partial_return: true`; a failure-policy retry is unmarked and never counts toward the stall cap. A deadline stop records `overrun` (FR-002), still marked when it is a `partial` return's stop.
3. **Given** recorded issues, **When** the state is read by an older reader, **Then** the run state remains readable across schema versions.

---

### User Story 3 - The improvement backlog exists only after its run is over (Priority: P2)

A run owner ends a run (pull request open or aborted) and only then does a backlog file for that run appear in the factory home, carrying the session's issues, the run totals and the factory version (`factory_sha`) that produced them. Before the run ends, no claim can take it; the improvement route lists what is ready and suggests a feature text, and starting any improvement run stays a manual act.

**Why this priority**: the "pending improvement starts only after its session is done" rule is the safety property of the feature; it must be structural, not a convention.

**Independent Test**: Attempt to claim the backlog before and after ending the source run; assert refusal before, presence and claimability after.

**Acceptance Scenarios**:

1. **Given** a run still in progress, **When** the backlog is looked for, **Then** no backlog file for that run exists anywhere.
2. **Given** a run set to pull-request-open or aborted, **When** the writer records that end, **Then** the backlog file appears in the factory home with the issues, run totals, the factory version and a `ready` status.
3. **Given** a backlog whose source run has not ended, **When** `claim` is invoked on it, **Then** the claim is refused with a message naming the source run.
4. **Given** ready backlogs, **When** the improvement route runs, **Then** it lists them and prints a suggested feature text; it never starts a run by itself.

---

### User Story 4 - Factory versions can be benchmarked before and after (Priority: P3)

A maintainer replays the same pre-settled fixture feature headlessly against a factory version, gets a score (wall time, agent time, spawns, overruns, issues by kind, token estimates, review rounds, pass/fail), and compares two scores to see the delta after a change.

**Why this priority**: the claim "improve the factory recursively" is unverifiable without a before/after measurement; the score is only useful once the stories above exist.

**Independent Test**: Score two recorded run states and assert the emitted metrics and the printed delta; run the fixture once end to end and assert the pass definition resolves to a clear verdict.

**Acceptance Scenarios**:

1. **Given** a pre-settled fixture feature with a pending run state seeded at the worktree stage and fast mode, **When** the benchmark driver runs it, **Then** it drives the harness headlessly, stops at the approver gate, opens no pull request and approves nothing automatically.
2. **Given** one or more run states, **When** scoring runs, **Then** every listed metric is emitted, and the pass flag is true only when the run reached the approver, the last verify was green, no unresolved blocking findings remain, and the fixture's own acceptance test passes.
3. **Given** two score files, **When** comparison runs, **Then** the delta between them is printed per metric.
4. **Given** no headless harness available, **When** a maintainer needs a number, **Then** the documented manual path (run the factory on the fixture, then score) works as a fallback.

---

### Edge Cases

- An overrun both self-reported and ledger-detected is recorded once, not twice.
- A unit of work in flight at the deadline overshoots it; the overshoot is recorded in the issue detail, and the role still stops at the unit boundary.
- A stage whose `partial` returns each carry committed progress resumes without limit.
- Orchestrator verify time over budget is recorded as an overrun issue with role `orchestrator` and never stops anything.
- A missing budget override, budget section, or usable value falls back to the 5-minute default; the deadline is always well-formed.
- A run that ends with zero issues still produces its backlog file, keeping the gate structural.
- The export succeeds with `factory_sha: null` when the factory install is not in a git tree.
- `claim` on a missing or already-claimed name is refused with a message naming the problem, never a traceback.
- A fixture run that halts or fails before the approver gate scores as a fail naming the condition, never a scorer crash.
- Run state written by the new version stays readable by readers that predate this feature.

## Requirements *(mandatory)*

### Functional Requirements

**Time budget**

- **FR-001**: The factory home configuration MUST carry a time budget of the form `budget: { default_s: 300, roles: { <role>: <seconds> } }`: 5 minutes by default, one override per role. Every spawn — including parallel and sub-agent spawns — MUST receive a deadline (absolute, in UTC) derived from its role's budget.
- **FR-002**: File-writing roles (spec-builder, code-build, fixer) MUST check the clock between units of work. Past the deadline, the role MUST finish the unit in flight, commit that progress, and return `partial` with an `overrun` report `{ "cause", "detail" }`, with the overshoot past the deadline visible in `detail`. `cause` MUST come from the closed list `large-input`, `test-loop`, `retry`, `tool-slow`, `scope-too-big`, `other`.
- **FR-003**: The `partial` return MUST be accepted from all three file-writing roles (not code-build alone), and the orchestrator MUST re-spawn a fresh agent with the same inputs so the stage resumes from work on disk.
- **FR-004**: The orchestrator MUST halt the run after three consecutive `partial` returns for the same stage with no new commit between them; while `partial` returns carry committed progress, resumption MUST continue without a cap. Failure-policy retries are not `partial` returns and MUST NOT count.
- **FR-005**: Reviewers and the judge MUST NOT be stopped at their budget: they finish normally, and an overrun past their budget is recorded after the spawn.
- **FR-006**: After every spawn, the orchestrator MUST detect overruns from the ledger duration against the role's budget. An overrun with no self-report MUST be recorded with cause `unreported`; an overrun both self-reported and detected MUST be recorded exactly once.
- **FR-007**: The budget MUST bind spawned roles only. Orchestrator verify (build/test) time over budget MUST be recorded as an `overrun` issue with role `orchestrator` and MUST NOT stop anything.

**Session issues**

- **FR-008**: A new writer command `factory issue-add <kind> <stage> <role> --detail --duration-ms [--cause] [--commit] [--partial-return]` MUST append an issue to the run state's `issues[]`. `kind` MUST be one of `overrun`, `agent-failure`, `retry`, `halt`, `verify-fail`. Issues are append-only records `{ at, kind, stage, role, cause, detail, duration_ms, commit, partial_return }` so they can be grouped later. `--cause` is required only for `overrun` (null otherwise); `--commit` defaults to the worktree HEAD. `--partial-return` marks a partial return's stop, accepted only on `overrun`/`retry` of file-writing roles; only marked records count toward FR-004's stall cap.
- **FR-009**: The run state schema MUST advance to version 5 with `issues[]` added, and readers MUST accept schema versions 1 through 5.
- **FR-010**: The existing event paths MUST record their issues: a non-deadline `partial` stop (e.g. low context) records `retry` marked `partial_return: true`; a failure-policy retry also records `retry`, but unmarked and never counting toward the stall cap. A deadline stop is recorded as `overrun` (FR-002), still marked when it is a `partial` return's stop. A second failure of the same agent records `agent-failure`; `set-status halted` records `halt`; `verify --fail` records `verify-fail`. FR-004 counts only partial returns.

**Gated improvement backlog**

- **FR-011**: On `set-status pr-open|aborted`, the writer MUST export `${FACTORY_HOME}/improvements/<repo-name>-<branch>.json` containing the run's issues, its run totals, the factory version (`factory_sha`) and status `ready`. The file MUST NOT exist before that end is recorded, so the gate is structural. The export MUST happen even when the run has zero issues; `factory_sha` is null when the factory install is not in a git tree.
- **FR-012**: `factory improvements` MUST list the ready backlogs; `factory improvements claim <name>` MUST refuse unless the source run has ended, naming the source run in the refusal.
- **FR-013**: The `/factory improve` route MUST list ready backlogs and print a suggested feature text built from the recorded issues. Starting an improvement run MUST remain manual. The recursive improver agent is out of scope for this run.

**Benchmark**

- **FR-014**: `conformance/bench/` MUST hold fixture feature(s) on `conformance/fixture-repo`: a pre-settled brief and a pending run state seeded at the worktree stage with fast mode. A benchmark run stops at the approver gate; there is no auto-approve flag and no pull request.
- **FR-015**: `tools/bench.py run --harness <h>` MUST drive the headless harness command for the chosen harness; `tools/bench.py score <state.json>...` MUST emit JSON with wall time, agent time, spawns, overruns, issues by kind, token estimates, review rounds and pass/fail; `compare a.json b.json` MUST print the per-metric delta.
- **FR-016**: A benchmark pass MUST mean all four: the run reached the approver, the last verify was green, no unresolved blocking findings remain, and the fixture's own acceptance test (extended per bench feature) passes. Any missing condition MUST score as a fail with the condition named.
- **FR-017**: The scorer MUST read recorded run state through the same state-reading code the rest of the tooling uses (one source of truth), and MUST be tested on recorded states. Live benchmark runs are a manual, token-costing activity, not part of the automated suite.
- **FR-018**: The manual benchmark path (run the factory on the fixture, then score) MUST be documented as the fallback for environments without a headless harness.

**Testing and delivery**

- **FR-019**: The automated suite MUST cover `issue-add`, the budget check, the export gate, the schema v5 migration, the scorer and the compare. Every harness MUST be re-rendered after the change, with the rendered distribution committed and clean.

### Key Entities

- **Time budget**: seconds allowed per spawned role — a default of 300 and per-role overrides; expressed to each spawn as an absolute deadline.
- **Overrun report**: a role's own account of running long — a cause from a closed list plus free-text detail, including the overshoot past the deadline.
- **Session issue**: an append-only record of one thing that went wrong — kind, stage, role, cause, detail, duration — collected in the run state.
- **Improvement backlog**: the run-end export of one session's issues, run totals and the factory version (`factory_sha`), marked `ready`; its existence is the gate on starting improvement work from it.
- **Partial return**: a file-writing role's stopped-but-committed result, resumable by a fresh spawn from disk.
- **Benchmark score**: one run's measured outcome — time, spawns, overruns, issues, token estimates, review rounds and a pass verdict — comparable against another score.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: With a reduced per-role budget, 100% of file-writing overruns produce exactly one issue with a valid cause and a continuation that resumes from committed progress; three consecutive `partial` returns without a new commit halt the stage in every test.
- **SC-002**: Each of the five event kinds (`overrun`, `agent-failure`, `retry`, `halt`, `verify-fail`) is recorded exactly once per event across the automated tests, and a run written by this version is still read successfully by an older reader.
- **SC-003**: In 100% of attempts, a backlog claim before its run ends is refused and no backlog file exists before the run ends; after the run ends the file exists with issues, totals, the factory version (`factory_sha`) and `ready` status, and is claimable.
- **SC-004**: Scoring a recorded run emits every listed metric, and comparing two scores prints a delta per metric; a fixture run that misses any pass condition reports a fail naming the condition, with zero scorer crashes.
- **SC-005**: The full automated test suite passes and the build gate is clean — every harness re-rendered with no generated-output drift — after the change.

## Assumptions

- The recursive improver agent, hard-kill/watchdog enforcement and publishing issues to GitHub are out of scope; this run delivers the time budget, session issues, gated backlog and benchmark core. A follow-up run consumes the backlog.
- "Every agent and sub agent" means every spawn the factory performs, including parallel spawns, each on its own role's budget; the orchestrator is never stopped (FR-007).
- A "unit of work" is the role's existing unit of committed work (the task/commit granularity the roles already use); the feature relies on that boundary and invents no new one.
- A missing budget section, missing role entry, or unusable budget value falls back to the 300-second default rather than failing the run; budget values are seconds and must be positive.
- Ledger durations are the accepted measurement for post-hoc overrun detection; score token estimates are approximations for before/after comparison, not accounting.
- The backlog file name `<repo-name>-<branch>.json` is derived from its run; `factory_sha` records the factory version (null outside a git tree). A zero-issue run still exports so the gate stays structural. Schema v5 adds only `issues[]`; no existing field changes shape.
- CLI command names, exit codes and file paths here are the product's user-facing contract (repository convention), not implementation detail.
- Bench fixtures live in the repository so replay is reproducible; live benchmark runs cost tokens and stay manual, while the automated suite tests the scorer on recorded states.
### Quality and Verification Constraints

- **Data integrity**: issues are append-only through the single writer; the backlog export is written once, atomically, only at run end; claim state changes cannot fabricate a backlog that does not exist.
- **Security**: the backlog and score output contain only run facts (no secrets, no personal configuration); the improvement route writes nothing outside the factory home.
- **Error and resource limits**: `issue-add`, `improvements` and `claim` refuse invalid input with the documented exit code and a message naming the problem — no traceback at the user; the budget check is one clock read between units, unbounded in nothing else.
- **Performance**: per-spawn overhead is a deadline derivation plus one clock read per unit; scoring runs offline on recorded state.
- **Dependencies**: standard-library-only tooling; no new runtime or test dependency.
- **Observability**: every issue is visible in the run state and in the CLI's reports; the score JSON names every metric; a fail verdict names the condition that failed.
- **Compatibility**: run states written before this change remain readable (schema 1–5); the rendered distribution covers every harness; documented commands and docs stay aligned with delivered behaviour.
- **Delivery**: the build re-renders every harness and the gate `test -z "$(git status --porcelain -- dist/)"` passes; tests run through the repository's standard-library runner named in the run's commands.
