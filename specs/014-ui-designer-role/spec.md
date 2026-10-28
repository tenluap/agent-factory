# Feature Specification: UI Designer Role

**Feature Branch**: `014-ui-designer-role`

**Created**: 2026-10-28

**Status**: Draft

**Input**: User description: "Add a new factory role `ui-designer` (agent `factory-ui-designer`, tier standard, access write). The orchestrator spawns it in the implement step on UI design runs. It detects the project's UI framework, maps the design source to the codebase, and updates the targeted file (plus its component dependencies) or, with no target, the whole UI surface (components and views) in dependency batches. Reviews, shared fix rounds and approver gate are unchanged." Behaviour source: the user's `pen-to-avalonia` agent and the `ui-agent` skill (see `factory/brief.md`).

## Context

Today a factory run implements every task through `code-build`. Pen design work rides on `code-build` and `fixer` through the design-code mapping contract, and `DESIGN.md` ("Pen design references") states that no new agent role is introduced for it. Design-to-code work has a distinct state machine — discover, survey, plan components, implement dependency batches, validate fidelity — that the user already runs outside the factory with the `pen-to-avalonia` agent and the `ui-agent` skill. This feature brings that behaviour into the factory as one dedicated write role, generalised beyond Avalonia and beyond Pen sources, without adding a second repair loop or changing review and approval.

Settled decisions (grilling, 2026-10-28): placement in the implement step; framework detection with Avalonia and web shipped first; four design source kinds; scope by named file or whole UI surface; `ui-agent` at most once inside the role with review/fix rounds shared; tier standard, write access; Figma resolved like `pen-design` and blocked when absent; full chain.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Implement one screen from a Pen design (Priority: P1)

A factory user runs a feature whose brief names a Pen design frame and one target view file in an Avalonia or web project. In the implement step the orchestrator spawns `ui-designer` instead of handling the UI work with `code-build`. The role detects the framework, surveys the Pen frame, maps it to the codebase, updates the target view and the components it depends on, maintains the canonical design-code map, and reports build, runtime, mapping and fidelity evidence. Review, fix rounds and the approver gate then run exactly as today.

**Why this priority**: This is the prior-art workflow (`pen-to-avalonia`) and the smallest slice that delivers design-faithful UI inside a factory run.

**Independent Test**: Run the factory on a fixture project with one Pen frame and one named view; confirm the role is spawned in implement, edits only the target view and its dependency components, writes map records for every scoped node, and returns an envelope whose `design` field references actual evidence.

**Acceptance Scenarios**:

1. **Given** a run whose saved design context names a Pen source, a target frame and one target file, **When** the implement step starts, **Then** the orchestrator spawns `factory-ui-designer` with the design context, the resolved `pen-design` path, the detected framework reference and the target file.
2. **Given** the target view uses a shared component that other views also use, **When** the role plans its changes, **Then** it inspects the other callers first and, when the change would alter them, returns a protected (`requires_user: true`) scope question instead of editing them.
3. **Given** the role finished its batches, **When** it returns, **Then** every scoped design node has a map record (mapped or explicitly accounted for) and the envelope reports build/runtime, mapping and fidelity gate results without claiming any gate it did not observe.

---

### User Story 2 - Restyle the whole UI surface (Priority: P2)

A user names a design source but no target file. The role enumerates the project's whole UI surface (views and components), orders it into dependency batches (tokens and assets, then shared components, then views), and updates it batch by batch. Before any edit the enumerated file list is shown to the user as a protected decision that fast mode cannot auto-accept.

**Why this priority**: Whole-project restyles are the second most common request and carry the largest blast radius, so they need the protected scope confirmation.

**Independent Test**: Run on a fixture with three views and two shared components and no named target; confirm the file list is relayed as a `requires_user: true` question, that fast mode leaves it unanswered, and that after acceptance the tasks follow dependency-batch order.

**Acceptance Scenarios**:

1. **Given** no target file is named, **When** the plan is produced, **Then** `tasks.md` lists the UI surface as dependency batches and the enumerated file list is relayed as one `requires_user: true` question.
2. **Given** fast mode is on, **When** the scope question is relayed, **Then** the orchestrator does not auto-answer it and waits for the user.
3. **Given** the user removes files from the list, **When** the role runs, **Then** it edits only the accepted files and records the excluded ones as out of scope.

---

### User Story 3 - Other design sources (Priority: P2)

A user supplies a Figma node, an image or screenshot, or only a text instruction ("make the settings page denser"). The role treats each source by its authority: Figma nodes are mapped like Pen nodes; images are visual reference only, with no node mapping; text-only restyles keep the existing code as the baseline and use `impeccable` guidance for the change.

**Why this priority**: Widens the role beyond Pen, but each kind reuses the same flow, so it follows the P1 slice.

**Independent Test**: Run three trials — Figma with the capability present, an image, a text-only instruction — and confirm the source kind recorded in the design context, the presence or absence of node mapping, and the gates required for each kind.

**Acceptance Scenarios**:

1. **Given** a Figma source and no resolvable `figma` skill or MCP capability, **When** the role starts, **Then** it stops that work as a disclosed blocker with setup guidance and installs nothing.
2. **Given** an image source, **When** the role finishes, **Then** the map records the image as a visual reference with no node records, and fidelity is reported against the image.
3. **Given** a text-only restyle, **When** the role finishes, **Then** no design-code map records are required, and the change is reported as a restyle of the existing baseline.

---

### User Story 4 - Unsupported framework (Priority: P3)

A user runs the role on a project whose UI framework has no shipped reference (for example Qt or SwiftUI).

**Why this priority**: Correct refusal protects users from guessed code; it is small but required.

**Independent Test**: Run on a fixture with only a framework the factory does not support; confirm the role reports the detected framework as unsupported and edits nothing.

**Acceptance Scenarios**:

1. **Given** framework detection finds no supported framework, **When** the role starts, **Then** it returns `failed` naming the detected framework (or "none detected") and the supported list, and writes no UI file.
2. **Given** detection finds two supported frameworks and the target is ambiguous, **When** the role starts, **Then** it returns a protected question naming the candidates instead of guessing.

---

### User Story 5 - Quality pass and shared repair budget (Priority: P3)

After the role's batches pass their gates, it runs the `ui-agent` pipeline (critique, audit, typeset, polish, re-verify) once over the changed surface. Remaining findings go to the normal review, judge and fixer flow, which shares the existing two fix rounds; no second repair loop is added.

**Why this priority**: Matches the user's existing quality habit without adding loops the factory has deliberately removed.

**Independent Test**: Inspect a run's ledger and state: `ui-agent` appears at most once per role spawn, and `review.fix_rounds` never exceeds 2 regardless of design findings.

**Acceptance Scenarios**:

1. **Given** the role's gates pass, **When** it finishes, **Then** it has run `ui-agent` at most once and reported applied, skipped and deferred recommendations with reasons.
2. **Given** a `ui-agent` recommendation conflicts with a design-sourced value, **When** the role decides, **Then** the design value wins and the recommendation is recorded as skipped with its reason.
3. **Given** design findings remain after review, **When** fixing, **Then** they share the existing two fix rounds with all other findings.

### Edge Cases

- The role reaches its deadline mid-batch: it finishes the batch in flight, commits it, and returns `partial` with an overrun report; a fresh spawn resumes from the committed batches and the map.
- The design source changed since the saved survey: the role marks affected map records stale and refreshes only the affected scope.
- A design element is removed: application behaviour stays; the role records the removal rather than deleting behaviour.
- The named target file does not exist or is not a UI file: the role returns a protected question naming the closest candidates.
- `ui-agent` or `impeccable` is not installed: the quality pass is skipped and disclosed; required design gates still apply.
- A run mixes UI design tasks and non-UI tasks: `code-build` runs the non-UI tasks and `ui-designer` runs the UI design tasks, in `tasks.md` order.
- Launch or screen capture is unavailable: implementation may proceed, but the fidelity gate stays unverified and the run cannot claim it passed.
- A resumed run started before this feature: it continues with `code-build` as recorded; nothing migrates.

## Requirements *(mandatory)*

### Functional Requirements

**Design first and packaging**

- **FR-001**: `DESIGN.md` MUST be updated first, before any `core/` or `adapters/` change: add `factory-ui-designer` (tier standard, access write) to the Agents table, add it to the Flow and the Implement decisions, add a routing-contract row for UI design work, and replace the "No new agent role ... is introduced" sentence in "Pen design references" with the deliberate new decision and its reason.
- **FR-002**: The role MUST be one new role prompt in `core/roles/` with the same metadata shape as existing roles, using only neutral verbs and naming no harness tool, path or command.
- **FR-003**: Every harness adapter MUST render the new agent, and the committed rendered distribution for all five harnesses MUST match a fresh render (no drift).
- **FR-004**: Wherever the factory enumerates file-writing roles (time budget, deadline stop, partial-return handling, read-only/write access checks, role counts in documentation), `ui-designer` MUST be included as a file-writing role.

**Activation and inputs**

- **FR-005**: A run MUST be a **UI design run** when its saved design context records a design source (Pen, Figma, image or text-only restyle) and UI targets or whole-surface scope; any other run MUST keep today's implement flow unchanged.
- **FR-006**: On a UI design run the orchestrator MUST spawn `ui-designer` in the implement step for the UI design tasks, and `code-build` for any remaining non-UI tasks, preserving `tasks.md` order. No new `/factory` route, stage name or harness verb is added.
- **FR-007**: The orchestrator MUST pass the role the usual implement inputs (worktree, branch, spec_dir, `speckit-implement`, `ponytail`, `tdd`, commands, deadline) plus the design context reference, the source kind, the scope (named file or whole surface), and the resolved design-source capability path (`pen-design` or `figma`) when the source needs one.
- **FR-008**: The orchestrator MUST resolve a `figma` skill or MCP capability through `RESOLVE` only when the source is Figma; when absent, the Figma work MUST stop as a disclosed blocker with setup guidance, and nothing MUST be installed automatically.

**Framework detection**

- **FR-009**: The role MUST detect the UI framework from project files before any edit and record the result in the design context.
- **FR-010**: The role MUST load exactly one framework reference for the detected framework: Avalonia (the existing Avalonia mapping reference, reused) and web (HTML/CSS and component frameworks such as TSX, Vue and Svelte) MUST ship.
- **FR-011**: When no supported framework is detected, the role MUST report it as unsupported and edit nothing; when several candidates fit the target, it MUST ask a protected question; it MUST never guess.

**Design sources**

- **FR-012**: A Pen source MUST be authoritative and mapped under the existing design-code mapping contract.
- **FR-013**: A Figma source MUST be mapped by node like Pen once the capability resolves.
- **FR-014**: An image or screenshot source MUST be a visual reference only: no node mapping, fidelity judged against the image, and the reference recorded in the design context.
- **FR-015**: A text-only restyle MUST treat the existing code as the baseline, use `impeccable` guidance, and require no map records.

**Scope**

- **FR-016**: With a named target file, the role MUST limit edits to that file and its component dependencies, and MUST inspect other callers of any shared component before changing it.
- **FR-017**: A change that would alter shared components beyond the request MUST be relayed as a `requires_user: true` scope question, never applied silently.
- **FR-018**: With no named target, the plan MUST enumerate the whole UI surface (views and components) as dependency batches in `tasks.md`: tokens and assets, then shared components, then views.
- **FR-019**: The enumerated file list MUST be relayed as one `requires_user: true` question before implementation; fast mode MUST NOT auto-accept it, and the accepted list MUST be persisted outside `relay`.

**Work, mapping and gates**

- **FR-020**: The role MUST follow the prior-art state machine: discover, survey once, plan canonical components and mapping, implement dependency batches, validate, report.
- **FR-021**: The role MUST reuse the canonical `docs/design-code-map.json` and the existing mapping gates (build/runtime, mapping, rendered fidelity); no second map or new gate MUST be introduced.
- **FR-022**: The role MUST follow `engineering.md` commit units and the plan's declared test seams and exemptions, committing each batch as one unit; it MUST NOT invent a seam.
- **FR-023**: The role MUST return the standard envelope, with the optional `design` field referencing the actual context, map and evidence paths, and MUST NOT report a gate as passed without current evidence.

**Quality and repair**

- **FR-024**: The role MUST run `ui-agent` at most once per spawn, after its gates pass, over the changed surface only; when `ui-agent` is unavailable it MUST disclose the skip.
- **FR-025**: Design-sourced values MUST win over conflicting quality recommendations, which are recorded as skipped with a reason.
- **FR-026**: Review, judge, fixer, the two shared fix rounds and the approver gate MUST stay unchanged; the feature MUST add no second repair loop.

**Time budget and resume**

- **FR-027**: The role MUST obey the time budget like other file-writing roles: check time between batches, finish the batch in flight past the deadline, commit, and return `partial` with an overrun report.
- **FR-028**: A fresh role MUST resume from committed batches, the map and the design context; a run saved before this feature MUST resume unchanged.

**Verification**

- **FR-029**: Automated tests MUST cover: the role renders for every harness with tier standard and write access; the rendered distribution matches its source; the role is listed among file-writing roles wherever that list exists; the core role file names no harness tool.

### Key Entities

- **UI design run**: A factory run whose design context records a design source and UI scope; it routes UI tasks to `ui-designer`.
- **Design source**: One of Pen file, Figma node, image/screenshot, or text-only instruction, each with a defined authority (mapped, mapped, visual reference, baseline restyle).
- **Framework reference**: The per-framework guidance file the role loads after detection (Avalonia, web).
- **UI scope**: Either a named target file with its component dependencies, or the user-accepted whole-surface file list in dependency batches.
- **Dependency batch**: One coherent layer of the UI (tokens/assets, shared components, or views) implemented and committed as one unit.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In a fixture UI design run with one named target, 100% of edited files are the target or its component dependencies.
- **SC-002**: In a whole-surface run with fast mode on, the scope question is answered by the user in 100% of trials (0 auto-accepted).
- **SC-003**: Every scoped Pen or Figma node in a completed run has a map record (0 unaccounted nodes).
- **SC-004**: The quality pass runs at most once per role spawn, and fix rounds never exceed 2 in any run.
- **SC-005**: On an unsupported framework, the role edits 0 UI files and names the detected framework.
- **SC-006**: All five harness renders include the new role and the committed distribution shows 0 drift after a fresh render.
- **SC-007**: Non-design runs show no change in implement behaviour: the same roles are spawned in the same order as before the feature.

## Assumptions

- "UI design run" is decided from the saved design context created during grilling/specify, extending the existing Pen design context to the other source kinds; no new state schema version is needed beyond optional fields.
- The Avalonia mapping reference is reused as the Avalonia framework reference; a new web framework reference is the only new reference file.
- `ui-agent` and `impeccable` are optional external skills resolved through `RESOLVE`; their absence is disclosed, never installed silently beyond the existing authorised `impeccable` offer.
- Behaviour comes from the user's `pen-to-avalonia` agent and `ui-agent` skill, adapted to factory rules: stateless spawns, relay questions, shared fix rounds, and the engineering rules, which win on conflict.
- Design edits (writing back to the Pen or Figma source) stay out of scope unless explicitly requested, as today.
- Frameworks beyond Avalonia and web are future work; they are reported unsupported.
- The role gets its own time-budget entry, defaulting to the standard 300 seconds.
