# Feature Specification: Live-conformance unblockers

**Feature Branch**: `018-live-conformance`

**Created**: 2026-11-04

**Status**: Draft

**Input**: User description: "Deliver the tooling and procedure that unblock the Factory live conformance plan (docs/superpowers/plans/2026-11-03-factory-live-conformance-plan.md): fix the headless permission and model blockers the last smoke tests hit, add isolated checkout installs and provenance recording to the benchmark driver, and write the per-leg golden-run procedure. The live, token-spending trials run after merge."

## Context

The live conformance plan must prove that a real coding-agent session can take a feature request through an interruption, a cross-harness resume and one approved pull request. Both installed-version smoke tests stopped before factory preflight:

- **Claude Code**: the headless session reached the model but lacked permission to read the factory references or invoke the state CLI.
- **OpenCode**: the provider rejected the default model setup (missing end-user identifier; the default server returned an internal error).

This feature removes those blockers and writes the procedure. It does **not** run the live trials; a maintainer runs them after merge and records the results in a follow-up commit. Factory implement roles never drive nested harness sessions.

## Clarifications

### Session 2026-11-04 (initial grilling, settled)

- Q1 Scope → Unblockers and runbook only; live trials run after merge, results in a follow-up commit.
- Q2 Claude Code headless permission → scoped allow-list, no bypass mode, disposable fixture only.
- Q3 Second harness → OpenCode once its model configuration is fixed; otherwise Codex, with the reason recorded.
- Q4 UI fixture leg → out of scope; recorded as deferred until the UI handoffs repair plan (docs/superpowers/plans/2026-11-03-factory-ui-handoffs-plan.md) lands.
- Q5 Throwaway PR target → a new private repository `tenluap/factory-golden-run-<date>`, created at trial time (not by this run), kept as evidence and deleted later by the user.
- Q6 Isolation → acceptance trials render the checkout into a temporary factory home and harness config directory; the installed-version baseline stays a separate result.
- Q7 Provenance → each benchmark run writes a provenance record; scoring carries it into its output.
- Q8 Procedure location → the existing Claude Code and OpenCode golden-run checklists, plus one results row per leg.
- Q9 OpenCode blocker → the benchmark run accepts an explicit model choice; the OpenCode checklist explains how to pick a compatible one.
- Q10 Checkout render → opt-in; without it the benchmark run behaves exactly as today.

## User Scenarios & Testing *(mandatory)*

The users are factory maintainers preparing and running live conformance trials.

### User Story 1 - Headless Claude Code smoke test can reach factory preflight (Priority: P1)

A maintainer runs the benchmark driver against the disposable greeting fixture with Claude Code. The headless session is launched with exactly the permissions the factory needs (reading the factory skill and its references, editing files in the fixture, spawning roles, and running git, Python and the factory state CLI) and nothing broader. It no longer stalls on permission prompts before preflight.

**Why this priority**: This blocker stopped the last Claude Code smoke test outright; no other leg can start until a headless session can read the factory and update state.

**Independent Test**: Run the driver offline with a stubbed harness executable and inspect the recorded launch command: it carries the scoped directory grant and tool allow-list, and never a permission-bypass mode.

**Acceptance Scenarios**:

1. **Given** the Claude Code harness is selected, **When** the benchmark run launches the session, **Then** the launch grants read access to the factory skill directory in use (installed, or the isolated render) and allows only Read, Edit, Write, Agent, Skill, and shell commands for git, python3 and the factory CLI.
2. **Given** any benchmark run, **When** the launch command is built, **Then** it never includes a permission-bypass mode or an unrestricted shell allowance.
3. **Given** the OpenCode harness is selected, **When** the session is launched, **Then** no Claude Code permission options are passed to it.

---

### User Story 2 - Choose a model for the headless session (Priority: P1)

A maintainer whose provider rejects the default model passes an explicit provider/model choice to the benchmark run. The driver forwards it to the selected harness in that harness's own form. Without the choice, the harness default applies as today.

**Why this priority**: The OpenCode blocker was a rejected default model; without a way to choose a compatible model, the cross-harness leg cannot run on OpenCode.

**Independent Test**: Run the driver offline with a stubbed harness for each supported harness, with and without a model choice, and compare the recorded launch commands.

**Acceptance Scenarios**:

1. **Given** a model choice and the OpenCode harness, **When** the session launches, **Then** OpenCode receives that model through its model option.
2. **Given** a model choice and the Claude Code harness, **When** the session launches, **Then** Claude Code receives that model through its model option.
3. **Given** no model choice, **When** the session launches, **Then** no model option is passed and the launch matches today's behaviour apart from the Story 1 permissions.

---

### User Story 3 - Trial runs against an isolated render of this checkout (Priority: P1)

For an acceptance trial, a maintainer asks the benchmark run to use the current checkout instead of the installed factory. The driver renders the checkout into a factory home and harness config directory inside the run's output directory and launches the harness against that isolated configuration, so the trial never reads or changes the maintainer's installed factory or harness settings.

**Why this priority**: The plan requires that acceptance trials exercise the code under test, separately from the installed-version baseline. Without isolation, a trial result cannot be attributed to a specific revision.

**Independent Test**: Run the driver offline with the opt-in flag and a stubbed harness; confirm the rendered factory files exist under the output directory, the harness was launched with its config location pointing there, and the maintainer's real home and harness config were untouched.

**Acceptance Scenarios**:

1. **Given** the opt-in checkout flag and Claude Code, **When** the run launches, **Then** the factory is rendered from this checkout under the output directory and Claude Code is launched with its config directory pointed at the isolated location and its directory grant pointed at the isolated factory skill.
2. **Given** the opt-in checkout flag and OpenCode, **When** the run launches, **Then** the factory is rendered under the output directory and OpenCode is launched with its config home pointed at the isolated location.
3. **Given** no opt-in flag, **When** the run launches, **Then** the installed factory is used and no render occurs (installed baseline, unchanged).
4. **Given** the render fails, **When** the run is attempted, **Then** the run stops before launching any harness session and reports the render failure.

---

### User Story 4 - Every run records its provenance; scores carry it (Priority: P2)

Every benchmark run writes a provenance record into its output directory naming exactly what was tested: the checkout revision, whether and how the checkout had local changes, the rendered output fingerprint, the installed factory revision, and the harness CLI versions. When the run is scored, the score output carries that provenance, so a recorded result can always be traced back to the code it exercised.

**Why this priority**: The plan's first task requires recording the checkout revision, local changes and installed versions. It matters only once runs can execute (Stories 1–3).

**Independent Test**: Run the driver offline against a checkout with and without local edits, then score a state file from that output directory; confirm the provenance fields and that the score output contains them.

**Acceptance Scenarios**:

1. **Given** a clean checkout, **When** a run completes its setup, **Then** the provenance record names the checkout revision, an empty local-change list and no local-change fingerprint.
2. **Given** a checkout with uncommitted changes, **When** a run completes its setup, **Then** the record lists the changed paths and a fingerprint of the local changes.
3. **Given** a run with the opt-in checkout render, **Then** the record includes a fingerprint of the rendered output; **given** no render, it records that none was made.
4. **Given** a scored state that belongs to a run with a provenance record, **When** it is scored, **Then** the score output includes that provenance; **given** no record exists, **Then** the score marks provenance as missing and its pass/fail result is unchanged.
5. **Given** a harness CLI version or installed factory revision that cannot be determined, **Then** the record states it is unavailable instead of failing the run.

---

### User Story 5 - Per-leg golden-run procedure and results table (Priority: P2)

A maintainer opens the Claude Code and OpenCode golden-run checklists and finds everything needed to run each leg: how to invoke it, how to isolate it, which permissions it grants, the pause, kill and resume steps, how to choose a compatible model, and the PR leg against the throwaway repository. The results document has one row per leg so that each leg's evidence is recorded separately.

**Why this priority**: The live trials run after merge and need a written procedure, but the procedure is only usable once the tooling in Stories 1–4 exists.

**Independent Test**: Read the two checklists and the results document; every leg named in the plan has a step list and a results row, and no placeholder remains in the checklists' capability notes.

**Acceptance Scenarios**:

1. **Given** the Claude Code checklist, **When** a maintainer follows it, **Then** it states the invoke command, the isolation setup (including the one-time login or API key needed in the isolated config directory), the scoped permissions, the pause/kill/resume steps and the PR leg.
2. **Given** the OpenCode checklist, **Then** it additionally explains how to pick a known-compatible model and states the Codex fallback for the cross-harness leg, with the reason to be recorded.
3. **Given** the results document, **Then** it has one row each for: headless smoke, golden run, pause/resume, cross-harness resume, approval/PR, and UI (deferred until the UI handoffs repair plan lands).
4. **Given** the PR leg, **Then** the procedure names the private throwaway repository pattern `tenluap/factory-golden-run-<date>`, created at trial time and kept as evidence.

### Edge Cases

- The output directory already exists: the run refuses to start, as today.
- The selected harness executable is missing: the run fails with today's "use the manual benchmark fallback" message, before any render or provenance work that would mislead.
- The checkout is not a git repository or git is unavailable: provenance records the revision and local changes as unavailable; the run continues.
- Local changes include untracked files: they appear in the changed-path list, and the fingerprint covers tracked diffs; untracked paths are listed by name.
- An isolated Claude Code config directory has no credentials: the session cannot authenticate; the procedure documents the one-time login or API key, and the driver does not create or copy credentials.
- A model choice is given together with the checkout flag: both apply.
- The harness exits non-zero: provenance has already been written, so a failed run is still attributable.
- Scoring several states, some with provenance and some without: each score entry carries its own provenance or a missing marker.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: When launching Claude Code headless, the benchmark run MUST grant directory access to the factory skill directory in use (installed or isolated render) and MUST restrict allowed tools to Read, Edit, Write, Agent, Skill, and shell commands for git, python3 and the factory CLI.
- **FR-002**: The benchmark run MUST NOT launch any harness with a permission-bypass mode or an unrestricted shell allowance.
- **FR-003**: The benchmark run MUST accept an optional provider/model choice and forward it to OpenCode and Claude Code through each harness's model option; without it, no model option is passed.
- **FR-004**: The benchmark run MUST offer an opt-in checkout mode that renders the current checkout into a factory home and harness config directory under the run's output directory and launches the harness with its config location (Claude Code config directory; OpenCode config home) pointed there.
- **FR-005**: Without the opt-in checkout mode, the benchmark run MUST keep its current behaviour (installed factory, no render), apart from FR-001 to FR-003.
- **FR-006**: If the checkout render fails, the run MUST stop before launching a harness and report the failure.
- **FR-007**: Every benchmark run MUST write a provenance record into its output directory before launching the harness, containing: checkout revision; list of locally changed paths; a fingerprint of local changes; fingerprint of the rendered output (or "none"); installed factory revision; and harness CLI versions.
- **FR-008**: A provenance value that cannot be determined MUST be recorded as unavailable rather than abort the run.
- **FR-009**: Scoring MUST include, per scored state, the provenance record of the run that produced it, or a missing marker; provenance MUST NOT change a score's pass/fail outcome.
- **FR-010**: Existing benchmark scoring, comparison and recorded-score behaviour MUST be preserved; existing benchmark tests MUST keep passing.
- **FR-011**: The Claude Code golden-run checklist MUST state the invoke command, isolation setup (including credentials for the isolated config directory), scoped permissions, pause/kill/resume steps and the PR leg, with no capability-note placeholders left.
- **FR-012**: The OpenCode golden-run checklist MUST state the same items as FR-011 for OpenCode plus how to pick a known-compatible model, and the Codex fallback for the cross-harness leg with its reason recorded.
- **FR-013**: The golden-run results document MUST have one row per leg — headless smoke, golden run, pause/resume, cross-harness resume, approval/PR, UI — with the UI row marked deferred until the UI handoffs repair plan lands, and MUST state that each leg's evidence is recorded separately and that the installed-version baseline is a separate result.
- **FR-014**: The procedure MUST name the PR target as a private throwaway repository `tenluap/factory-golden-run-<date>`, created at trial time and kept as evidence.
- **FR-015**: All verification for this feature MUST run offline: no test spends model tokens or invokes a real harness CLI.

### Quality Requirements

- **Security**: Permission grants are the narrowest set that lets the factory run in the disposable fixture; they apply only to benchmark runs and never to the maintainer's own sessions. The driver never creates, copies or logs credentials.
- **Isolation**: An opt-in checkout run puts its factory home and harness configuration under its output directory; the maintainer's installed factory home and harness configuration are not read for configuration and not modified. OpenCode's data directory (provider auth, session storage) stays shared by design.
- **Integrity**: The provenance record is written before the harness starts, so every launched run is attributable even if the session fails.
- **Compatibility**: Existing command-line usage of the benchmark run, score and compare commands keeps working unchanged.
- **Dependencies**: No new third-party dependency.

### Key Entities

- **Benchmark run**: one invocation of the driver against the disposable fixture; owns an output directory holding the fixture copy, factory home, harness log and provenance record.
- **Provenance record**: what a run tested — checkout revision, local changes and their fingerprint, rendered output fingerprint, installed factory revision, harness CLI versions.
- **Isolated install**: a render of this checkout plus a harness config directory, both under one run's output directory.
- **Leg**: one separately evidenced part of the live conformance plan (headless smoke, golden run, pause/resume, cross-harness resume, approval/PR, UI).
- **Installed-version baseline**: a run against the maintainer's installed factory, recorded separately from checkout trials.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of headless Claude Code launches built by the driver carry the scoped directory grant and tool allow-list; 0 carry a permission-bypass mode.
- **SC-002**: A maintainer can select a model for either supported harness with one option, verified for both harnesses with and without the option.
- **SC-003**: Every benchmark run's output directory contains a provenance record; every score of a state from such a run reports the same provenance.
- **SC-004**: An opt-in checkout run leaves the maintainer's installed factory home and harness configuration byte-for-byte unchanged.
- **SC-005**: The full offline test suite passes, including all pre-existing benchmark tests, with zero real harness invocations and zero model tokens spent.
- **SC-006**: Each of the six legs has exactly one results row and a checklist path a maintainer can follow without consulting another source for invoke, isolation, permissions, resume or PR steps.

## Assumptions

- Only Claude Code and OpenCode have headless drivers in the benchmark run; Codex remains a manual fallback for the cross-harness leg and is not added as a driver here.
- The Claude Code directory grant also covers the run's output directory, because the seeded pending state and brief (factory home) and the factory's sibling worktree live there outside the fixture; a factory home given outside the output directory is granted explicitly. The grant never reaches beyond the disposable run, apart from the factory skill directory in use.
- "Factory CLI" means the factory state CLI invoked through Python from the installed or isolated factory; the allow-list scopes shell commands by command prefix.
- Harness CLI versions are read from each harness executable's version output; reading a version is not a model invocation.
- The opt-in render reuses the repository's existing render and install tooling rather than a new installer.
- The live trials, creation of the throwaway PR repository, and live diagnosis of the OpenCode model rejection happen at trial time after merge, outside this feature.
- The UI fixture leg is out of scope and recorded only as deferred.
