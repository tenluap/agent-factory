# Feature Specification: Per-project deep and standard models

**Feature Branch**: `017-per-project-models`

**Created**: 2026-11-02

**Status**: Draft

**Input**: User description: "Per-project deep and standard model selection with /factory init bootstrap" (settled decisions Q1-Q12 in `factory/brief.md`)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Project config overrides models for a run (Priority: P1)

A user pins different deep/standard models in two repositories. A factory run in each repository spawns its role agents with that repository's models, falling back per tier to the user's global config and then to the adapter defaults.

**Why this priority**: Core value of the feature; every other story builds on the resolved cascade.

**Independent Test**: Place `<repo>/.factory/config.json` with an override for one harness tier, run preflight, and confirm state records the project value with source `project` and that spawns pass that model.

**Acceptance Scenarios**:

1. **Given** `<repo>/.factory/config.json` sets `models.opencode.deep`, **When** a run starts in that repo on opencode, **Then** deep-tier spawns use the project value and run state records it with source `project`.
2. **Given** the project config sets only `deep` and the user config sets `standard`, **When** preflight resolves, **Then** deep comes from `project`, standard from `user`, each labelled.
3. **Given** no project config and no user override, **When** preflight resolves, **Then** both tiers come from `adapter` defaults and behaviour equals today's.
4. **Given** a tier value is the empty string at any level, **When** it wins the cascade, **Then** the spawned agent inherits the session's model (existing convention).
5. **Given** the user edits the project config between runs, **When** the next run starts, **Then** the new values apply with no re-render or reinstall.

---

### User Story 2 - Malformed or unresolvable config stops the run (Priority: P1)

A typo in the project or user config must not silently run the whole factory on the wrong model.

**Why this priority**: Silent fallback masks errors for an entire run; safety gate for Story 1.

**Independent Test**: Write invalid JSON (or a wrong-shape `models` entry) to `.factory/config.json` and confirm preflight stops with the file path, error and fix step.

**Acceptance Scenarios**:

1. **Given** `.factory/config.json` is not valid JSON, **When** preflight runs, **Then** the run stops naming the exact file, the parse error and the correction step.
2. **Given** a config whose `models` shape or tier value is unresolvable (e.g. non-string, unknown tier), **When** preflight runs, **Then** the run stops naming the file, the offending selection and the correction step.
3. **Given** a resolved model that the existing model-inspection preflight rejects, **When** preflight runs, **Then** the existing inspection stop applies unchanged.

---

### User Story 3 - Inspect the effective cascade (Priority: P2)

A user runs `factory models` to see which model each role tier will use in the current repo and where each value comes from.

**Why this priority**: Single resolver shared by preflight and init; makes the cascade visible and testable.

**Independent Test**: Run `factory models` and `factory models --json` in a repo with mixed project/user/adapter sources and check each row's value and source label.

**Acceptance Scenarios**:

1. **Given** any repo, **When** the user runs `factory models`, **Then** it prints per harness and tier the effective model and its source (`project` | `user` | `adapter`).
2. **Given** `--json`, **When** the command runs, **Then** it prints the same data as machine-readable JSON.
3. **Given** a malformed config, **When** the command runs, **Then** it exits non-zero with the same file/error/fix message as preflight.

---

### User Story 4 - Bootstrap the project config with `/factory init` (Priority: P2)

A user runs `/factory init` to create `<repo>/.factory/config.json` seeded with today's effective values for all harnesses, plus a README sidecar explaining how to edit and restore.

**Why this priority**: Removes guesswork about schema and current defaults; optional for Story 1.

**Independent Test**: Run `factory init` in a repo without `.factory/`, then confirm both files exist, the config holds all five harnesses and both tiers with effective values, and `factory models` output is unchanged by init.

**Acceptance Scenarios**:

1. **Given** no `.factory/config.json`, **When** the user runs `/factory init`, **Then** the skill runs `python3 <F>/bin/factory init`, which writes the config seeded for `claude-code`, `codex`, `copilot`, `opencode`, `zcode` with `deep` and `standard` each, shows the printed table, and stops.
2. **Given** init ran, **When** values are compared with pre-init resolution, **Then** they are identical (adapter defaults merged with the user's global overrides), so init changes no behaviour.
3. **Given** init ran, **When** the user reads the output, **Then** each value is labelled `adapter` or `user`, and a note says values are unverified until a run's preflight.
4. **Given** init ran, **When** the user opens `.factory/config.README.md`, **Then** it states the schema, the precedence, the seeded defaults table with sources, and how to restore a default.
5. **Given** `.factory/config.json` already exists, **When** the user runs init, **Then** it refuses, names the path, exits non-zero, and leaves the file untouched.
6. **Given** a user global config, **When** init runs, **Then** the global config is not modified.

---

### User Story 5 - Resume re-resolves and discloses changes (Priority: P3)

A user edits the project config while a run is paused; on resume the factory uses the new values and says what changed.

**Why this priority**: Keeps resume honest without freezing selections; existing resume re-resolution pattern.

**Independent Test**: Start a run, change one tier in `.factory/config.json`, resume, and confirm the delta is disclosed and state holds the new value and source.

**Acceptance Scenarios**:

1. **Given** recorded `models` in run state and an edited config, **When** the run resumes, **Then** preflight re-resolves, discloses each changed tier as old→new with sources, updates state, and continues.
2. **Given** no change, **When** the run resumes, **Then** no delta is disclosed.

---

### User Story 6 - Harness cannot take a spawn-time model (Priority: P3)

On a harness whose spawn mechanism cannot accept a model, the user is told project models cannot apply there.

**Why this priority**: Prevents silent no-op on such harnesses.

**Independent Test**: Simulate preflight on a harness marked as not supporting spawn-time models and confirm the disclosure and continuation on installed selections.

**Acceptance Scenarios**:

1. **Given** a harness whose spawn cannot take a model, **When** preflight runs with a project or user override, **Then** it discloses that the overrides cannot apply and continues on the installed (baked) selections.

---

### Edge Cases

- Project config exists but has no `models` key, or no entry for the current harness: every tier falls through to user, then adapter.
- Project config has entries for other harnesses only: those are ignored for this run; no error.
- `.factory/` exists without `config.json`: init writes both files into it.
- `config.README.md` exists but `config.json` does not: init refuses only on an existing `config.json`, so it writes the config and regenerates the README it owns.
- User global config itself malformed: same preflight stop, naming the global file.
- Run executing in a worktree: the project config is looked up at the run's repository root (`state.repo`), not the worktree.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The factory MUST read a project model config at `<repo>/.factory/config.json`, using the same schema as `${FACTORY_HOME}/config.json`: `{"models": {"<harness>": {"deep": "...", "standard": "..."}}}`.
- **FR-002**: Model resolution MUST cascade per harness tier: project → user global → adapter default, merged per key.
- **FR-003**: An empty-string model value MUST keep its existing meaning: inherit the session's model.
- **FR-004**: A single resolver in the state CLI (`factory_cli`) MUST produce the effective tier→model mapping with per-tier source labels `project` | `user` | `adapter`; preflight, `factory models` and `factory init` MUST use it.
- **FR-005**: Preflight MUST resolve the cascade once and record resolved `models` and per-tier `source` labels in run state.
- **FR-006**: The orchestrator MUST pass the resolved model for the agent's tier into every `SPAWN` and `SPAWN_PARALLEL`. No re-render or reinstall is required for a change to take effect on the next run.
- **FR-007**: On a harness whose spawn mechanism cannot take a model, preflight MUST disclose that project/user models cannot apply and continue on the installed selections; it MUST NOT be silent.
- **FR-008**: A malformed (unparseable) or unresolvable config at project or user level MUST stop the run at preflight, naming the exact file, the parse error or unresolvable selection, and the correction step.
- **FR-009**: On resume, preflight MUST re-resolve, disclose every changed tier as a delta (old→new with sources), update state, and continue with the new values.
- **FR-010**: The state CLI MUST provide `factory models [--json]`, printing the effective per-harness, per-tier cascade for the current repo with each row's source.
- **FR-011**: The state CLI MUST provide `factory init`, creating `<repo>/.factory/config.json` seeded with all five harnesses (`claude-code`, `codex`, `copilot`, `opencode`, `zcode`) and both tiers, using the effective values (adapter defaults merged with user global overrides).
- **FR-012**: `factory init` MUST print a table labelling each seeded value's source (`adapter` or `user`) and a note that values are unverified until a run's preflight; it MUST NOT probe model inventories.
- **FR-013**: `factory init` MUST write `.factory/config.README.md` stating schema, precedence, the seeded defaults table with sources, and how to restore a default.
- **FR-014**: `factory init` MUST refuse when `<repo>/.factory/config.json` exists: name the path, exit non-zero, modify nothing.
- **FR-015**: `factory init` MUST NOT modify the user global config. `--global`, `--force`, merging and JSONC are out of scope.
- **FR-016**: The `/factory` skill MUST route `init` (alongside `resume`/`improve`) to `SHELL: python3 <F>/bin/factory init`, show its printed table, and stop.
- **FR-017**: `tools/render.py`, the canonical dist render and `install.sh` MUST stay unchanged; dist MUST never read user or project config.

### Key Entities

- **Project model config**: `<repo>/.factory/config.json`; optional; same schema as user config; highest precedence.
- **User model config**: `${FACTORY_HOME}/config.json`; existing; middle precedence.
- **Adapter defaults**: model selections rendered into installed agents per harness; lowest precedence.
- **Resolved models**: per harness tier→model ID plus source label, recorded in run state at preflight.
- **Config README sidecar**: `.factory/config.README.md`; human guidance written by init.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Two repos with different project configs produce different recorded models in run state and in spawn requests, with zero reinstall steps.
- **SC-002**: A repo without project config resolves exactly the same models as before the feature (no behaviour change).
- **SC-003**: 100% of malformed or unresolvable configs stop preflight with a message naming file, error and fix.
- **SC-004**: Immediately after `factory init`, `factory models` output values are identical to pre-init output; only source labels change to `project`.
- **SC-005**: Running `factory init` twice leaves the first file byte-identical and the second call exits non-zero.

## Assumptions

- `<repo>` is the run's repository root (`state.repo`), the same root the factory already uses.
- Adapter defaults are readable by the CLI from the existing adapter/profile data without re-rendering.
- The five harness keys are the current adapter set; adding a harness later extends init's seed list.
- Existing per-adapter model-inspection guidance at preflight stays unchanged and runs on resolved values.
- Whether a harness's spawn mechanism accepts a model is a static per-adapter fact the plan stage records.
