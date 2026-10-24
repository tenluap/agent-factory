# Feature Specification: ZCode Harness Adapter

**Feature Branch**: `003-zcode-harness`

**Created**: 2026-10-24

**Status**: Draft

**Input**: User description: "add zcode harness to the software factory"

## Clarifications

### Session 2026-10-24

- Q: Which skill locations does ZCode actually read, for FR-010? → A: Only the ZCode and shared-agent skill roots, project before user; the Claude roots are not read (verified against ZCode 3.16.3; FR-010 and the matching edge case corrected).
- Q: How should the build prove that the committed distribution matches a fresh render? → A: Stop ignoring the distribution directory and commit it, so a plain difference check against the committed distribution after a render is a gate that can fail (FR-015, SC-003, SC-006).
- Q: How far should the design record's spec-kit setup line change? → A: Generalise that one line so each adapter states its own setup arguments; no other adapter's recorded setup is corrected in this feature (FR-016).
- Q: How should cross-harness resume be verified? → A: Add an explicit manual resume check in both directions to the feature's validation (SC-005).
- Q: Whose rendered distribution does this change commit? → A: All five harnesses' rendered output (the four existing adapters plus ZCode) is tracked and committed in this change, so the whole distribution directory is under version control from here on (FR-018, SC-003, SC-006).
- Q: What metadata do the ZCode agent files carry? → A: Exactly the Claude Code frontmatter set — name, description and tools — and nothing else; no model, permission, turn-limit or skills keys (FR-004).
- Q: Which UI-review provider does ZCode use? → A: Reuse the existing `codex` provider identifier, with a note in the ZCode harness document saying why ZCode has no provider of its own (FR-012).
- Q: How does a session recognise it is ZCode? → A: The recognition line rests on a signal the session can check — the ZCode home environment variable or the ZCode home directory — rather than self-description alone; no other adapter's recognition line changes in this feature (FR-012).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Install the factory into ZCode (Priority: P1)

A ZCode user clones the factory repository and installs it for their harness. The installer places the factory skill and one agent file per role in ZCode's own user directories, so that a new ZCode session offers the factory and can address each factory role by name.

**Why this priority**: Nothing else in the feature is reachable until the factory is installed where ZCode looks for skills and agents.

**Independent Test**: Run the installer selecting ZCode and confirm the skill and all role agents appear in ZCode's user skill and agent locations with valid, ZCode-readable metadata; a fresh ZCode session lists the factory and the roles.

**Acceptance Scenarios**:

1. **Given** a machine with ZCode installed and no factory files, **When** the user installs the factory for ZCode, **Then** the factory skill is available under the ZCode home and one agent file exists per factory role.
2. **Given** the ZCode home location is overridden by its environment variable, **When** the user installs, **Then** the files land under the overridden location instead of the default.
3. **Given** an install has already been done, **When** the user installs again after updating the repository, **Then** the installed files reflect the updated source with no manual cleanup.

---

### User Story 2 - Run a full factory run inside ZCode (Priority: P1)

A ZCode user starts a run with the factory's invoke command and a feature description. The session recognises it is running in ZCode, picks the ZCode adapter, and carries the feature through the factory flow: grilling, worktree, the spec chain, implementation, reviews, approval and a pull request — spawning each role as a ZCode subagent, asking questions in the factory's question layout, and resolving skills from the locations ZCode reads.

**Why this priority**: This is the feature's purpose: the flow must run unchanged on ZCode.

**Independent Test**: Start a run in ZCode on a sample repository and observe that roles run as separate subagents, questions appear in the factory layout and accept the documented replies, and the run reaches its next checkpoint without harness-specific workarounds.

**Acceptance Scenarios**:

1. **Given** a ZCode session with the factory installed, **When** the user starts a run with a feature description, **Then** the session identifies ZCode as the harness and proceeds with the ZCode adapter's behaviour.
2. **Given** a stage that needs several roles at once, **When** the orchestrator dispatches them, **Then** all of those roles are requested together in a single turn and each runs as its own subagent.
3. **Given** a stage that asks the user something, **When** the question is shown, **Then** grilling and relay rounds use the factory's Markdown question layout and other choice questions use ZCode's question facility.
4. **Given** the harness exposes no notification facility, **When** the flow would notify the user, **Then** the run continues with no notification and no error.
5. **Given** a stage that needs a named skill, **When** the skill is resolved, **Then** the first match is taken from the documented ZCode-readable locations, project before user.
6. **Given** a run started in ZCode that stops, **When** the user resumes it from another harness (or resumes a run from another harness inside ZCode), **Then** the run continues from its recorded stage.

---

### User Story 3 - Understand ZCode support from the documentation (Priority: P2)

A prospective user reads the repository's documentation and learns that ZCode is supported: how to install for it, how to start a run, where agents are installed, and what ZCode-specific requirements apply.

**Why this priority**: Support that is not discoverable is not usable, but it does not block a user who already knows the command.

**Independent Test**: Read the repository's entry documentation, the design record and the domain terms, and confirm each lists ZCode alongside the existing harnesses with accurate install and invocation details.

**Acceptance Scenarios**:

1. **Given** the repository documentation, **When** a reader looks for supported harnesses, **Then** ZCode appears with its install command, invoke command and agent install location.
2. **Given** the spec-kit setup requirement, **When** a reader follows it for ZCode, **Then** the documented setup places the spec-kit skills where ZCode reads them.

---

### Edge Cases

- The ZCode home environment variable is unset: the default ZCode home is used.
- A skill name exists in several readable locations: the first match in the documented order (project ZCode skills, project shared agent skills, user ZCode skills, user shared agent skills) wins, and no second copy is consulted.
- A subagent result carries no usage figures: the run's cost ledger records the usage as unreported and relies on its estimates, without failing the stage.
- The project does not use ZCode's own skill folder but does carry the shared agent skills folder: resolution still finds the skill.
- Automatic harness recognition is ambiguous: the user forces the adapter through the existing harness override variable.
- No remote is reachable when the run starts: the run bases itself on the local default branch.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The factory MUST provide a ZCode adapter, named `zcode`, covering the ZCode desktop application and its bundled command-line interface, held in the same adapter shape as the existing harnesses (an adapter descriptor plus a harness document).
- **FR-002**: The adapter MUST declare the capability tier for native subagents, mapping single dispatch to a ZCode subagent invocation addressed by the role's agent name, and parallel dispatch to one such invocation per role issued in a single turn.
- **FR-003**: The adapter MUST declare install locations under a ZCode home that is read from its environment variable and falls back to a documented default: the factory skill under the home's skill directory and one Markdown agent file per role, named per role, under the home's agent directory.
- **FR-004**: Each rendered agent file MUST carry exactly the same metadata set as the Claude Code agent files — the agent's name, its description, and the tool access its role requires — and no other metadata keys.
- **FR-005**: The adapter MUST express role access as tool lists: read-only roles get read, search and shell access; writing roles additionally get edit and create access.
- **FR-006**: The adapter MUST NOT pin models; agents inherit the session's model unless the user pins models for ZCode in the shared factory configuration file.
- **FR-007**: The harness document MUST state how the user starts a run in ZCode and how the run's arguments are supplied.
- **FR-008**: The harness document MUST state how the user is asked questions: the factory's Markdown layout for grilling and relay rounds, the harness's question facility for other choice questions, and a plain message for free-text questions.
- **FR-009**: The harness document MUST record that notification is unavailable on ZCode and is therefore a no-op for the run.
- **FR-010**: The harness document MUST define skill resolution for ZCode as the first match over the project's ZCode skills, the project's shared agent skills, then the same two under the user's home, in that order. Claude-only skill locations are not part of the order: ZCode does not read them.
- **FR-011**: The harness document MUST state the spec-kit initialisation arguments for ZCode, so the spec-kit skills land in a location ZCode reads.
- **FR-012**: The harness document MUST state the recognition line by which a session identifies itself as ZCode, resting on a signal the session can check (the ZCode home environment variable or the ZCode home directory) rather than self-description alone, and MUST leave every other adapter's recognition line unchanged. It MUST also name the UI-review provider for ZCode as the existing `codex` provider, with a note recording that ZCode has no provider of its own.
- **FR-013**: The harness document MUST forbid invoking the spec-chain and doc-grilling skills through the harness's skill facility, requiring the resolved file to be read and followed instead.
- **FR-014**: The harness document MUST record that subagent results expose no token usage, so the ledger records usage as unreported.
- **FR-015**: Building the distribution MUST render ZCode alongside every existing harness, producing the ZCode skill and role agent files without altering any other harness's output.
- **FR-016**: The repository documentation MUST present ZCode as a supported harness: the harness table (install command, start command, agent install location), the ZCode requirements, the design record's list of adapters, and the domain definition of a harness. The design record's spec-kit setup line MUST be generalised to state that each adapter declares its own setup arguments; no other adapter's recorded setup is changed in this feature.
- **FR-017**: No file in the harness-neutral core may be changed to name ZCode; all ZCode-specific behaviour lives in the ZCode adapter.
- **FR-018**: The rendered distribution for all five harnesses (the four existing adapters and ZCode) MUST be tracked in version control and committed with its source in this change: the repository MUST stop excluding the distribution directory, so that comparing the working tree with the committed distribution after a fresh render is a check that can fail when the two diverge.

### Key Entities

- **ZCode adapter**: the per-harness translation for ZCode, consisting of a descriptor (install paths, agent file format and fields, access lists, models) and a harness document (recognition, capability tier, verb mappings, notes).
- **ZCode home**: the user-level directory ZCode reads, located by an environment variable with a documented default, under which the skill and agents are installed.
- **Role agent file**: one rendered Markdown file per factory role, carrying the metadata ZCode needs to run that role as a subagent.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A ZCode user installs the factory with a single documented command and starts a run in a new session without editing any file by hand.
- **SC-002**: Every factory role is available as a ZCode subagent after install: the count of installed role agents equals the number of roles the factory defines.
- **SC-003**: A build renders all five harnesses, including ZCode, and a difference check of the tracked distribution against that fresh render reports zero differences — a check that reports differences whenever the committed distribution and the render diverge.
- **SC-004**: 100% of the rendered ZCode agent files carry metadata ZCode accepts, with no file rejected at load.
- **SC-005**: A run begun in ZCode can be resumed on another supported harness, and a run begun elsewhere can be resumed in ZCode, with no loss of recorded progress — verified by a manual resume check performed in both directions.
- **SC-006**: Adding ZCode changes no behaviour of any existing harness: the four existing harnesses' rendered output is committed in this change alongside ZCode's, after a fresh render it differs only by the additions required by shared documentation, and the difference check of SC-003 reports a clean tree. No existing adapter's recognition line or UI-review provider changes.

## Assumptions

- ZCode's subagent, skill, shell, read and edit facilities behave as described in the feature brief (desktop app 3.16.x and its bundled CLI); the spec-kit initialisation arguments were verified during planning against the installed spec-kit CLI, which offers a native ZCode integration rather than the flag shape the brief assumed.
- ZCode reads custom agent definitions with the same frontmatter conventions as the existing Markdown-agent harnesses, so the existing renderer shape suffices.
- The run's base is the local default branch, because the remote is unreachable at run start.
- ZCode has no UI-review provider of its own, so the adapter reuses the `codex` provider identifier and the harness document records why.
- ZCode does not honour the "do not invoke this skill directly" frontmatter key that the spec-chain and doc-grilling skills rely on (it is not part of the metadata set ZCode accepts). The prohibition in FR-013 is therefore stated as a rule in the harness document and relied on as such, not enforced by the harness.
- No change to the factory flow, roles, protocol or state model is in scope: this feature adds an adapter and the documentation that announces it.
