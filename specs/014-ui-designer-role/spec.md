# Feature Specification: UI Designer Role

**Feature Branch**: `014-ui-designer-role`

**Created**: 2026-10-28

**Status**: Draft

**Input**: Add factory role `ui-designer` (agent `factory-ui-designer`, tier standard, access write), spawned in implement on UI design runs: it detects the UI framework, maps the design source to the codebase, and updates the targeted file plus its component dependencies or, with no target, the whole UI surface in dependency batches. Reviews, shared fix rounds and approver gate are unchanged. Prior art: the user's `pen-to-avalonia` agent and `ui-agent` skill (`factory/brief.md`).

## Context

Today Pen design work rides on `code-build` and `fixer`; `DESIGN.md` ("Pen design references") adds no role. Design-to-code work has its own state machine (discover, survey, plan components, implement batches, validate fidelity). This feature adds it as one write role, generalised beyond Avalonia and Pen (FR-026 keeps repair and review unchanged).

## Clarifications

### Session 2026-10-28

- Mixed-run routing → explicit `[UI]` task marker only (FR-006).
- Whole-surface enumeration and protected scope question → plan stage; tasks batch the accepted list (FR-018, FR-019).
- Framework detection → `spec-builder` at plan; `ui-designer` re-verifies (FR-009).
- Text-only classification → plan, purely visual changes only; ambiguity gets one relay question (FR-005).
- Text-only gates → build/runtime required; mapping and fidelity not applicable (FR-015).
- `ui-agent` → one pass, in the spawn completing the last `[UI]` task (FR-024).
- Evidence at drop → `docs/design/<branch>/` (FR-030).
- `figma` capability → resolved at plan, re-resolved at implement (FR-008).

### Session 2026-10-29

- Pen backend for `ui-designer` → pen CLI exclusive, never a Pen MCP backend; a missing or unauthenticated CLI records affected gates unavailable with setup guidance (FR-031).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Implement one screen from a Pen design (Priority: P1)

A factory user runs a feature whose brief names a Pen design frame and one target view file in an Avalonia or web project. In implement the orchestrator spawns `ui-designer` for the `[UI]` tasks. The role re-verifies the framework recorded at plan, surveys the frame, updates the target view and its dependency components, maintains the design-code map, and reports build, runtime, mapping and fidelity evidence. Review, fix rounds and approval run as today.

**Why this priority**: Prior-art workflow (`pen-to-avalonia`); smallest design-faithful slice.

**Independent Test**: Run the factory on a fixture project with one Pen frame and one named view; confirm the role is spawned in implement, edits only the target view and its dependency components, writes map records for every scoped node, and returns an envelope whose `design` field references actual evidence.

**Acceptance Scenarios**:

1. **Given** a run whose saved design context names a Pen source, a target frame and one target file, **When** the implement step starts, **Then** the orchestrator spawns `factory-ui-designer` with the design context, the resolved `pen-design` path, the detected framework reference and the target file.
2. **Given** the target view uses a shared component that other views also use, **When** the role plans its changes, **Then** it inspects the other callers first and, when the change would alter them, returns a protected (`requires_user: true`) scope question instead of editing them.
3. **Given** the role finished its batches, **When** it returns, **Then** every scoped design node has a map record (mapped or explicitly accounted for) and the envelope reports build/runtime, mapping and fidelity gate results without claiming any gate it did not observe.
4. **Given** the session offers a Pen MCP backend, **When** the role surveys, captures or otherwise reaches the Pen source, **Then** it uses only the pen CLI (`pen` commands, headless `pen interactive`, direct reads of the local `.pen` snapshot), and with the CLI missing or unauthenticated the affected gates are recorded `unavailable`/blocked with setup guidance instead of an MCP fallback.

---

### User Story 2 - Restyle the whole UI surface (Priority: P2)

A user names a design source but no target file. The plan stage enumerates the project's whole UI surface (views and components) and relays the file list as a protected decision that fast mode cannot auto-accept. The tasks stage then orders the accepted files into dependency batches (tokens and assets, then shared components, then views), and the role updates them batch by batch.

**Why this priority**: Common request with the largest blast radius, so scope needs protected confirmation.

**Independent Test**: Run on a fixture with three views and two shared components and no named target; confirm the file list is relayed as a `requires_user: true` question, that fast mode leaves it unanswered, and that after acceptance the tasks follow dependency-batch order.

**Acceptance Scenarios**:

1. **Given** no target file is named, **When** the plan is produced, **Then** `plan.md` lists the whole UI surface and the file list is relayed as one `requires_user: true` question; after acceptance `tasks.md` lists only the accepted files as `[UI]` dependency batches.
2. **Given** fast mode is on, **When** the scope question is relayed, **Then** the orchestrator does not auto-answer it and waits for the user.
3. **Given** the user removes files from the list, **When** tasks are written and the role runs, **Then** only the accepted files get tasks and edits, and the excluded ones are recorded as out of scope.

---

### User Story 3 - Other design sources (Priority: P2)

A user supplies a Figma node, an image or screenshot, or only a text instruction ("make the settings page denser"). The role treats each source by its authority: Figma nodes are mapped like Pen nodes; images are visual reference only, with no node mapping; text-only restyles keep the existing code as the baseline and use `impeccable` guidance for the change.

**Why this priority**: Widens the role beyond Pen on the same flow.

**Independent Test**: Run three trials — Figma with the capability present, an image, a text-only instruction — and confirm the source kind recorded in the design context, the presence or absence of node mapping, and the gates required for each kind.

**Acceptance Scenarios**:

1. **Given** a recorded Figma source and no resolvable `figma` skill or MCP capability, **When** the plan stage ends, **Then** the run is blocked before tasks with setup guidance and nothing is installed.
2. **Given** an image source, **When** the role finishes, **Then** the map records the image as a visual reference with no node records, and fidelity is reported against the image.
3. **Given** a text-only restyle, **When** the role finishes, **Then** build/runtime evidence is reported, mapping and fidelity are recorded not applicable ("no design reference"), and a before/after capture is attached when capture is available.
4. **Given** a brief that may or may not change behaviour, **When** the plan stage classifies it, **Then** one ordinary relay question decides; work that changes behaviour stays on `code-build`.

---

### User Story 4 - Unsupported framework (Priority: P3)

A user runs the role on a project whose UI framework has no shipped reference (for example Qt or SwiftUI).

**Why this priority**: Correct refusal prevents guessed code.

**Independent Test**: Run on a fixture with only a framework the factory does not support; confirm the plan stage reports the detected framework as unsupported, the run stops before tasks, and no UI file is edited.

**Acceptance Scenarios**:

1. **Given** plan-stage detection finds no supported framework, **When** the plan stage ends, **Then** `spec-builder` returns `failed` naming the detected framework (or "none detected") and the supported list, the run stops before tasks, and no UI file is written.
2. **Given** detection finds two supported frameworks and the target is ambiguous, **When** the plan stage runs, **Then** it returns a protected question naming the candidates instead of guessing.
3. **Given** the recorded framework no longer matches the project files at implement time, **When** `ui-designer` re-verifies, **Then** it returns `failed` with both values and edits nothing.

---

### User Story 5 - Quality pass and shared repair budget (Priority: P3)

The spawn that completes the last `[UI]` task runs the `ui-agent` pipeline (critique, audit, typeset, polish, re-verify) once over the whole changed UI surface, with no internal second iteration. Remaining findings go to review, judge and fixer, sharing the existing two fix rounds.

**Why this priority**: Keeps the user's quality habit without new loops.

**Independent Test**: Inspect a run's ledger and state: `ui-agent` appears at most once per run, also across resumes, and `review.fix_rounds` never exceeds 2.

**Acceptance Scenarios**:

1. **Given** the last `[UI]` task's gates pass, **When** the role finishes, **Then** it has run `ui-agent` once, recorded that in the design context, and reported applied, skipped and deferred recommendations with reasons.
2. **Given** a `ui-agent` recommendation conflicts with a design-sourced value, **When** the role decides, **Then** the design value wins and the recommendation is recorded as skipped with its reason.
3. **Given** design findings remain after review, **When** fixing, **Then** they share the existing two fix rounds with all other findings.

### Edge Cases

- The role reaches its deadline mid-batch: it finishes the batch in flight, commits it, and returns `partial` with an overrun report; a fresh spawn resumes from the committed batches and the map.
- The design source changed since the saved survey: the role marks affected map records stale and refreshes only the affected scope.
- A design element is removed: application behaviour stays; the role records the removal rather than deleting behaviour.
- The named target file does not exist or is not a UI file: the role returns a protected question naming the closest candidates.
- `ui-agent` or `impeccable` is not installed: the quality pass is skipped and disclosed; required design gates still apply.
- A run mixes UI design tasks and non-UI tasks: `ui-designer` runs the `[UI]`-marked tasks and `code-build` runs the rest, in `tasks.md` order.
- Launch or screen capture is unavailable: implementation may proceed, but the fidelity gate stays unverified and the run cannot claim it passed.
- A resumed run started before this feature: it continues with `code-build` as recorded; nothing migrates.

## Requirements *(mandatory)*

### Functional Requirements

**Design first and packaging**

- **FR-001**: `DESIGN.md` MUST be updated first, before any `core/` or `adapters/` change: add `factory-ui-designer` (tier standard, access write) to the Agents table, add it to the Flow and the Implement decisions, add a routing-contract row for UI design work, and replace the "No new agent role ... is introduced" sentence in "Pen design references" with the deliberate new decision and its reason.
- **FR-002**: The role MUST be one new role prompt in `core/roles/` with the same metadata shape as existing roles, using only neutral verbs and naming no harness tool, path or command.
- **FR-003**: Every harness adapter MUST render the new agent, and the committed rendered distribution for all five harnesses MUST match a fresh render (no drift).
- **FR-004**: Wherever the factory enumerates file-writing roles (deadline stop, partial-return handling, write access checks, role counts in documentation), `ui-designer` MUST be included as a file-writing role.

**Activation and inputs**

- **FR-005**: A run MUST be a **UI design run** when its saved design context records a design source (Pen, Figma, image or text-only restyle) and UI targets or whole-surface scope; any other run MUST keep today's implement flow unchanged. `spec-builder` MUST classify a run as text-only at plan only when the brief asks for a purely visual change with no behaviour change, and record it in the design context; an ambiguous brief MUST get one ordinary relay question, and mixed work stays on `code-build`.
- **FR-006**: On a UI design run the tasks stage MUST mark each UI design task with an explicit `[UI]` marker. In the implement step the orchestrator MUST route by that marker only: `ui-designer` for `[UI]` tasks, `code-build` for the rest, preserving `tasks.md` order; one spawn covers each contiguous run of `[UI]` tasks. No new `/factory` route, stage name or harness verb is added.
- **FR-007**: The orchestrator MUST pass the role the usual implement inputs (worktree, branch, spec_dir, `speckit-implement`, `ponytail`, `tdd`, commands, deadline) plus the design context reference, the source kind, the scope (named file or whole surface), and the resolved design-source capability path (`pen-design` or `figma`) when the source needs one.
- **FR-008**: The orchestrator MUST resolve a `figma` skill or MCP capability through `RESOLVE` at plan, only when a Figma source is recorded; when absent, the run MUST be blocked before tasks with setup guidance and nothing installed. Implement MUST re-resolve it before spawning the role.

**Framework detection**

- **FR-009**: On a UI design run `spec-builder` MUST detect the UI framework from project files during the plan stage and record it in the design context; an unsupported framework MUST stop the run before tasks. `ui-designer` MUST re-verify the recorded framework before any edit and return `failed` on mismatch.
- **FR-010**: The role MUST load exactly one framework reference for the detected framework: Avalonia (the existing Avalonia mapping reference, reused) and web (HTML/CSS and component frameworks such as TSX, Vue and Svelte) MUST ship.
- **FR-011**: When no supported framework is detected, the plan stage MUST report it as unsupported and no UI file MUST be edited; when several candidates fit the target, it MUST ask a protected question; detection MUST never guess.

**Design sources**

- **FR-012**: A Pen source MUST be authoritative and mapped under the existing design-code mapping contract.
- **FR-013**: A Figma source MUST be mapped by node like Pen once the capability resolves.
- **FR-014**: An image or screenshot source MUST be a visual reference only: no node mapping, fidelity judged against the image, and the reference recorded in the design context.
- **FR-015**: A text-only restyle MUST treat the existing code as the baseline, use `impeccable` guidance, require no map records, and require build/runtime evidence; mapping and fidelity MUST be recorded not applicable with reason "no design reference", and a before/after capture MUST be attached when capture is available.
- **FR-031**: The `ui-designer` role MUST reach a Pen source only through the pen CLI — `pen` commands, headless `pen interactive`, and direct reads of the local `.pen` snapshot — and MUST NOT use a Pen MCP backend offered by the harness; with the CLI missing or unauthenticated, affected gates MUST be recorded `unavailable`/blocked with setup guidance, with no MCP fallback and no automatic installation.

**Scope**

- **FR-016**: With a named target file, the role MUST limit edits to that file and its component dependencies, and MUST inspect other callers of any shared component before changing it.
- **FR-017**: A change that would alter shared components beyond the request MUST be relayed as a `requires_user: true` scope question, never applied silently.
- **FR-018**: With no named target, the plan stage MUST enumerate the whole UI surface (views and components) in `plan.md` and relay the file list as one `requires_user: true` question; fast mode MUST NOT auto-accept it, and the accepted list MUST be persisted outside `relay`.
- **FR-019**: The tasks stage MUST write `[UI]` dependency batches for the accepted list only: tokens and assets, then shared components, then views.

**Work, mapping and gates**

- **FR-020**: The role MUST follow the prior-art state machine: discover, survey once, plan canonical components and mapping, implement dependency batches, validate, report.
- **FR-021**: The role MUST reuse the canonical `docs/design-code-map.json` and the existing mapping gates (build/runtime, mapping, rendered fidelity); no second map or new gate MUST be introduced.
- **FR-022**: The role MUST follow `engineering.md` commit units and the plan's declared test seams and exemptions, committing each batch as one unit; it MUST NOT invent a seam.
- **FR-023**: The role MUST return the standard envelope, with the optional `design` field referencing the actual context, map and evidence paths, and MUST NOT report a gate as passed without current evidence.

**Quality and repair**

- **FR-024**: Only the spawn that completes the last `[UI]` task (no unchecked `[UI]` task remains in `tasks.md`) MUST run `ui-agent`, as a single pass (no internal second iteration) after its gates pass, over the whole changed UI surface; it MUST record the pass in the design context so a resume does not repeat it, and MUST disclose the skip when `ui-agent` is unavailable.
- **FR-025**: Design-sourced values MUST win over conflicting quality recommendations, which are recorded as skipped with a reason.
- **FR-026**: Review, judge, fixer, the two shared fix rounds and the approver gate MUST stay unchanged; the feature MUST add no second repair loop.

**Time budget and resume**

- **FR-027**: The role MUST obey the time budget like other file-writing roles: check time between batches, finish the batch in flight past the deadline, commit, and return `partial` with an overrun report.
- **FR-028**: A fresh role MUST resume from committed batches, the map and the design context; a run saved before this feature MUST resume unchanged.

**Verification**

- **FR-029**: Automated tests MUST cover: the role renders for every harness with tier standard and write access; the rendered distribution matches its source; the CLI's file-writing role check accepts its `partial` return; the core role file names no harness tool; the Pen CLI precedence rule (FR-031) is asserted in the core role and the mapping contract.
- **FR-030**: At drop, Pen, Figma and image evidence and references MUST rehome to `docs/design/<branch>/`, and map references MUST be rewritten to the new paths. A map reference to a missing evidence file MUST fail the drop before any move, naming the path, with the map and run folder unchanged.

### Key Entities

UI design run, UI design task, design source, framework reference, UI scope and dependency batch are defined in `CONTEXT.md` ("UI design").

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In a fixture UI design run with one named target, 100% of edited files are the target or its component dependencies.
- **SC-002**: In a whole-surface run with fast mode on, the scope question is answered by the user in 100% of trials (0 auto-accepted).
- **SC-003**: Every scoped Pen or Figma node in a completed run has a map record (0 unaccounted nodes).
- **SC-004**: The quality pass runs at most once per run, including resumes, and fix rounds never exceed 2 in any run.
- **SC-005**: On an unsupported framework, the run stops at plan, edits 0 UI files and names the detected framework.
- **SC-006**: All five harness renders include the new role and the committed distribution shows 0 drift after a fresh render.
- **SC-007**: Non-design runs show no change in implement behaviour: the same roles are spawned in the same order as before the feature.

## Assumptions

- "UI design run" is decided from the saved design context, extended from Pen to the other source kinds; only optional state fields are added, no schema version.
- The Avalonia mapping reference is reused; a web framework reference is the only new reference file.
- `ui-agent` and `impeccable` are optional skills resolved through `RESOLVE`; absence is disclosed, never installed beyond the existing authorised `impeccable` offer.
- Prior-art behaviour is adapted to factory rules (stateless spawns, relay questions, shared fix rounds); engineering rules win on conflict.
- Design edits (writing back to the Pen or Figma source) stay out of scope unless explicitly requested, as today.
- Frameworks beyond Avalonia and web are future work; they are reported unsupported.
- The role-generic 300-second time-budget default applies; no role-specific entry.
