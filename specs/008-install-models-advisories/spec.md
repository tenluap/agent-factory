# Feature Specification: Install model pipeline and round-3 advisory fixes

**Feature Branch**: `008-install-models-advisories`

**Created**: 2026-10-26

**Status**: Draft

**Input**: User description: "Fix the unresolved FR-015 install-model blocker from PR #3 judge round 3, every round-3 advisory, and the open-run wall-clock bug in the totals sentence." (see `factory/brief.md` for the settled decisions; findings source: `specs/007-stabilise-factory/factory/reviews/round-3/verdict.json`)

## Clarifications

### Session 2026-10-26

- Q: When does the "exactly one open relay round" rule bind? → A: At most one relay round may hold unanswered questions and it must be the last round; a null relay and a fully answered relay awaiting checkpoint are conformant. Several open rounds are reported at `relay`; unanswered questions in a non-last round are reported at `relay.rounds[i]`.
- Q: What must the installer do when `config.json` is malformed? → A: The install fails cleanly: a message naming the file and the parse error, a non-zero exit, nothing rendered or linked, and the committed `dist/` untouched.

## User Scenarios & Testing *(mandatory)*

The user is a developer who installs the factory into one or more harnesses, runs factory sessions recorded in run state, and reads the CLI's reports — and who must be able to trust all three: personal configuration reaching the installed agents, clean refusals instead of crashes, and totals that tell the truth.

### User Story 1 - Personal model choices reach the installed agents (Priority: P1)

A developer pins their own models in `${FACTORY_HOME:-~/.factory}/config.json` and runs `./install.sh`. The linked skill and agents carry their model ids; the repository's committed rendered distribution is untouched by their personal choices; the printed models report lists exactly what the installed agents use.

**Why this priority**: this is the unresolved PR #3 blocker; today personal overrides either never reach the installed agents (default home ignored) or leak personal model ids into the shared, committed rendered distribution (exported `FACTORY_HOME`).

**Independent Test**: With `config.json` in the default home and `FACTORY_HOME` unset, run the installer in a sandbox and compare the linked agent files and the models report against the overrides; afterwards confirm the committed `dist/` shows no diff.

**Acceptance Scenarios**:

1. **Given** a `config.json` at `~/.factory` with model overrides and `FACTORY_HOME` unset, **When** the installer runs, **Then** the installed agents carry the overridden model ids and the models report lists them as effective.
2. **Given** an exported `FACTORY_HOME` pointing at a personal home, **When** the installer runs, **Then** the personal overrides apply to the per-user copy that is linked, and the committed `dist/` is byte-identical afterwards.
3. **Given** no `config.json`, **When** the installer runs, **Then** the adapter defaults are used and reported, with no error.
4. **Given** a `config.json` that does not parse, **When** the installer runs, **Then** the install fails with a message naming the file and the parse error and a non-zero exit, nothing is rendered or linked, and the committed `dist/` is untouched.

---

### User Story 2 - Commands refuse cleanly, never crash (Priority: P2)

A run owner types something the CLI cannot use — a malformed timestamp, an unwritable run, a lock whose owner cannot be probed. Every case exits with the documented code and a message naming the problem; nothing raises a traceback.

**Why this priority**: crashes and silent acceptance both destroy trust in the single writer; several round-3 findings are exactly these paths.

**Independent Test**: Feed each bad input to the CLI in the automated suite and assert exit code, message and absence of a traceback.

**Acceptance Scenarios**:

1. **Given** `ledger-add` with a malformed timestamp, **When** the command runs, **Then** it exits 5 (usage) with a message naming the bad value, not a traceback.
2. **Given** a lock whose owner PID is out of the OS-call's range, **When** liveness is checked, **Then** the lock is treated as live (and `lock take --force` still takes it).
3. **Given** an ended run that is still pending, **When** a write targets it, **Then** the write is refused as not writable.

---

### User Story 3 - Every state write goes through the one writer (Priority: P2)

A run owner moves a worktree (`rebind`), records a stage checkpoint, or validates state, and every mutation takes the lock, re-reads under the lock and leaves one coherent history — including when the git commit at a checkpoint fails.

**Why this priority**: the round-3 review found one command bypassing the writer and a checkpoint path that advances state before its commit and then duplicates history on retry.

**Independent Test**: Exercise `rebind` and checkpoint under a competing lock and a failing commit; assert single-writer behaviour and a retry that does not duplicate history.

**Acceptance Scenarios**:

1. **Given** a moved worktree, **When** `rebind` runs, **Then** the rewrite happens through the single write interface, with the run's lock held and the state re-read under it.
2. **Given** a checkpoint whose git commit fails, **When** the command returns, **Then** the failure is reported explicitly and distinguishes "state written, commit failed" from a full success.
3. **Given** a retry after that failure, **When** the command runs again, **Then** no history entry is silently duplicated.
4. **Given** state whose relay holds more than one open round, or unanswered questions in a non-last round, **When** validation runs, **Then** the violation is reported at its location (`relay` or `relay.rounds[i]`); a null relay or a fully answered relay awaiting checkpoint is conformant and reports no anomaly.

---

### User Story 4 - Reports that tell the truth about time (Priority: P3)

A run owner reads the run digest and totals sentence. Parallel work is never summed beside union totals, and a run still in progress shows its real elapsed wall clock rather than `0s`.

**Why this priority**: the round-3 review found the digest mixing summed parallel durations with union totals, and open runs reporting zero elapsed time.

**Independent Test**: Build a fixture with two parallel spawns and one with no `ended_at`; check the digest aggregates and the totals sentence.

**Acceptance Scenarios**:

1. **Given** a run with overlapping spawn intervals, **When** the digest is read, **Then** all elapsed aggregates come from the union-based totals, with no summed parallel duplicates beside them.
2. **Given** an open run (no `ended_at`), **When** totals are computed, **Then** wall clock runs from the start to now and the sentence shows the elapsed time, not `0s`.
3. **Given** an aborted run, **When** `runs` lists unfinished runs, **Then** the aborted run is skipped, since resume refuses it.

---

### User Story 5 - Documentation and tests match what ships (Priority: P3)

A maintainer reads the CLI contract, the 007 plan and the test suite and finds them true: the documented commands are all documented, the recorded process override is stated where the process decision lives, tests exist once and share one vocabulary source.

**Why this priority**: round-3 low findings are exactly these drifts; they cost reviewers real time and hide behaviour.

**Independent Test**: Grep the contract for each documented command, run the suite after the dead-code deletion, and confirm the replay helpers resolve to one definition.

**Acceptance Scenarios**:

1. **Given** the CLI contract, **When** read alongside the CLI's commands, **Then** `resume <run>` has its row like every other command.
2. **Given** `tools/tests/test_lock.py`, **When** run, **Then** no test method is defined twice and none is dead code after the runner's exit call.
3. **Given** `tools/tests/replay.py`, **When** read, **Then** its timestamp parsing and vocabularies come from the shared state module, not private copies.
4. **Given** `specs/007-stabilise-factory/plan.md`, **When** read, **Then** it records the task-structure override (`Overridden: ENG-3 - paired red/implement task structure`) beside its seam confirmations.

---

### Edge Cases

- **Factory home during install**: a missing default home `~/.factory` is created (`mkdir -p`, as today); an explicitly set `FACTORY_HOME` that does not exist, or any home that is not a directory or not writable, fails the install with a message naming the path, writing nothing — the committed rendered distribution is untouched either way.
- `config.json` present but missing the harness key or individual model keys: absent entries fall back to the adapter defaults, per key.
- `config.json` present but unparseable: the install aborts before any render or link, with a message naming the file and the parse error and a non-zero exit; the committed `dist/` is untouched.
- Installing twice re-links cleanly; `--uninstall` after a per-user render removes the links and `${FACTORY_HOME:-~/.factory}/dist/<harness>`, leaving `config.json`, pending runs and the committed rendered distribution untouched.
- Malformed ledger timestamps in every shape (empty, wrong format, non-string): each exits 5 with the offending value named.
- A lock file whose owner PID is `0`, negative, astronomically large, or non-numeric: treated as live, never a crash; `--force` still takes over.
- A lock file replaced by another owner between this process's write and release: release leaves the foreign lock alone.
- A run whose relay holds two open rounds or unanswered questions in a non-last round, a run ended while still pending, and a run whose git commit fails at checkpoint: each is refused or reported, never half-applied. A null relay and a fully answered relay awaiting checkpoint are conformant.

## Requirements *(mandatory)*

### Functional Requirements

**Personal model pipeline (resolves 007 FR-015; verdict finding at `install.sh:44`)**

- **FR-001**: The installer MUST render a per-user copy of each selected harness's tree into `${FACTORY_HOME:-~/.factory}/dist/<harness>` with the user's `config.json` model overrides merged, and link that harness's skill and agent directories from the per-user copy. A missing default home `~/.factory` is created; an explicitly set `FACTORY_HOME` that does not exist, or any home that is not a directory or not writable, fails the install with a message naming the path, writing nothing. `--uninstall` MUST remove the links it created and the per-user render at `${FACTORY_HOME:-~/.factory}/dist/<harness>`, leaving `config.json`, pending runs and the committed rendered distribution untouched.
- **FR-002**: The committed rendered distribution MUST stay canonical and machine-independent: rendering for the repository MUST NOT merge personal configuration into it, and no installer run may rewrite or dirty it.
- **FR-003**: Effective-model resolution MUST honour the documented default home `${FACTORY_HOME:-~/.factory}` — an unset `FACTORY_HOME` reads `~/.factory/config.json`, never "no config".
- **FR-004**: The installer's models report MUST print the effective model per role as resolved from the default home, matching what the linked agents carry.
- **FR-005**: An automated check MUST cover the default-home case (config at `~/.factory`, `FACTORY_HOME` unset), asserting the overrides reach the installed copy and the report.
- **FR-006**: The incorrect comment describing override behaviour in the renderer and the `README.md` / `DESIGN.md` wording about where models are merged MUST be corrected to the delivered behaviour.

**Clean refusals and write safety (round-3 medium advisories)**

- **FR-007**: `ledger-add` MUST reject a malformed timestamp with a usage error (exit 5) naming the bad value, never a traceback.
- **FR-008**: `rebind` MUST perform its state rewrite through the single write interface, holding the run's lock and re-reading state under it, like every other mutation.
- **FR-009**: A run that has ended MUST NOT be writable; the ended-status skip MUST apply to the pending-run selection as well, so an ended pending run cannot be mutated.
- **FR-010**: State validation MUST enforce that at most one relay round holds unanswered questions and that round MUST be the last; a null relay and a fully answered relay awaiting checkpoint are conformant. Several open rounds MUST be reported at `relay`, and unanswered questions in a non-last round at `relay.rounds[i]`.
- **FR-011**: A checkpoint MUST report a git commit failure explicitly, distinguishing "state written, commit failed" from success, and a retry MUST NOT silently duplicate history entries.

**Lock safety (round-3 findings at `lock.py:52` and `lock.py:160`)**

- **FR-012**: An owner PID the OS liveness probe cannot evaluate (out of range or wrong type) MUST be treated as a live holder, not raise.
- **FR-013**: `lock take --force` MUST take over regardless of holder liveness (force evaluated before liveness); without `--force`, a live lock MUST still refuse with the owner reported.
- **FR-014**: Releasing a lock MUST re-check the lock file's identity before unlinking and leave a lock owned by someone else in place.

**Truthful reporting (round-3 findings and the totals bug)**

- **FR-015**: The run digest MUST derive its elapsed aggregates from the union-based totals; summed parallel durations MUST NOT appear beside them.
- **FR-016**: Totals for an open run (no `ended_at`) MUST measure wall clock from the recorded start to now instead of reporting zero.
- **FR-017**: The run discovery list MUST skip aborted runs, which the resume path refuses.

**Contract and test hygiene (round-3 low advisories)**

- **FR-018**: The duplicate, dead test methods defined after the test runner's exit call in `tools/tests/test_lock.py` MUST be deleted; the suite must exercise each of those behaviours once.
- **FR-019**: `tools/tests/replay.py` MUST import its timestamp parsing and vocabularies from the shared state module instead of duplicating them (single source of truth).
- **FR-020**: The CLI contract `specs/007-stabilise-factory/contracts/cli.md` MUST document `resume <run>` in the same form as the other commands.
- **FR-021**: `specs/007-stabilise-factory/plan.md` MUST record `Overridden: ENG-3 - paired red/implement task structure`, the process decision made while delivering 007.

**Installer configuration failure (clarified 2026-10-26)**

- **FR-022**: A `config.json` that does not parse MUST abort the install cleanly: a message naming the file and the parse error, a non-zero exit, nothing rendered or linked, and the committed `dist/` untouched.

### Key Entities

- **Per-user render**: a harness tree rendered into the user's factory home with personal model overrides merged; what the harness directories link to.
- **Committed rendered distribution**: the canonical, machine-independent rendered distribution tracked in the repository (`dist/` names its directory only); never carries personal configuration.
- **Effective model report**: the per-role model list resolved from the default factory home, printed at install time.
- **Run lock**: an owner/host/harness/time record guarding one run; liveness is a judgment, not a crash, and takeover is always explicit.
- **Open relay round**: an unanswered question round awaiting the user; state validity allows at most one and only as the last round — a null relay and a fully answered relay awaiting checkpoint are conformant.
- **Totals**: wall clock, human and agent effort derived from unions of recorded intervals; open runs measure to now.

### Quality and Verification Constraints

- **Data integrity**: every state mutation goes through the single writer (lock, re-read under the lock, validate, atomic write); ended runs are immutable; checkpoint history stays non-duplicated across retries.
- **Security**: no personal model ids or configuration ever enter the committed `dist/`, adapters or shared output; installer links only into the harness directories it names.
- **Error and resource limits**: every refusal exits with the documented code and a message naming the cause; no path raises a traceback at the user; explicit `--force` is the only takeover.
- **Performance**: no new runtime cost beyond one extra render into the factory home at install time; no change to per-write cost.
- **Dependencies**: standard-library-only tooling; no new runtime or test dependency.
- **Observability**: install prints the effective model per role; every refusal and failure (including "state written, commit failed") is visible in the command's output.
- **Compatibility**: existing installs keep working after re-running the installer; documented defaults, shipped adapters and docs stay aligned (FR-006); state files and saved runs are unaffected.
- **Delivery**: one stacked branch off `origin/007-stabilise-factory` and one PR targeting `007-stabilise-factory`; the build re-renders all five harnesses and fails on any `dist/` drift.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In 100% of install-pipeline tests, overrides from the default home reach the installed agents and the models report, the committed `dist/` shows zero diff after any installer run, and a malformed `config.json` aborts the install with the file and parse error named, a non-zero exit, and nothing rendered or linked. A missing default home is created; an explicitly configured home that does not exist, is not a directory or is not writable fails naming its path and writes nothing; `--uninstall` leaves `config.json`, pending runs and the committed rendered distribution untouched.
- **SC-002**: Every malformed-input and refused-write path exits with its documented code and message and zero tracebacks, asserted by a test per path (ledger-add timestamp, ended pending run, out-of-range lock PID, foreign lock release, failed checkpoint commit).
- **SC-003**: Lock behaviour is verified end to end: an unevaluable owner PID counts as live, `lock take --force` succeeds against it in 100% of test runs, and release never removes another owner's lock.
- **SC-004**: With parallel spawns, human plus agent time stays within wall clock in 100% of digest tests, and every open-run totals sentence reports a non-zero elapsed wall clock.
- **SC-005**: Validation reports zero anomalies for a conformant run — including a null relay and a fully answered relay awaiting checkpoint — and names the location for a run with several open rounds (`relay`) or unanswered questions in a non-last round (`relay.rounds[i]`).
- **SC-006**: The full automated test suite passes and the build gate is clean (all five harnesses re-rendered with no generated-output drift) after the change.

## Assumptions

- The round-3 blocker on 007's hand-edited `halted` history entry is already resolved: the delivered `specs/007-stabilise-factory/factory/state.json` rewrites that entry to the conformant shape and validates against the closed vocabulary. Validator legacy tolerance and a repair command are out of scope here, as the brief's decisions enumerate only FR-015, the round-3 advisories and the totals bug.
- The settled FR-015 decision (per-user render under `${FACTORY_HOME:-~/.factory}/dist/<harness>`, linked from there) deliberately supersedes the verdict's suggested fix (report-only from the user's home); where the two differ, `factory/brief.md` wins.
- "Default home" means the documented `${FACTORY_HOME:-~/.factory}`; effective models are resolved from it whether or not `FACTORY_HOME` is exported.
- Exit code 5 is the CLI's documented usage-error code (contracts/cli.md), and each advisory's cited file and line in `verdict.json` identifies the delivered location.
- Documentation corrections are confined to the sentences the verdict and brief name (`render.py` comment, `README.md`, `DESIGN.md`, `contracts/cli.md`, `specs/007-stabilise-factory/plan.md`); no other prose is rewritten.
- Scope excludes any new CLI command (in particular no state-repair command), schema or vocabulary change, and any change to adapters' default model policy beyond the pipeline fix.
- Tests run through the standard-library runner named in the run's commands; the build command is the five-harness re-render drift gate.
