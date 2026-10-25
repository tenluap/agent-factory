# Feature Specification: Factory skill routing

**Feature Branch**: `005-skill-routing`

**Created**: 2026-10-25

**Status**: Draft

**Input**: Implement `docs/superpowers/specs/2026-10-25-factory-skill-routing-design.md`: route brainstorming, grilling, ponytail+tdd and impeccable to the right factory stage and role.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - An idea is explored before it becomes a feature (Priority: P1)

A user brings an exploratory idea rather than a settled feature. The factory recognises it as exploration, explores alternatives and tradeoffs, records the confirmed direction, and only then continues into feature settlement. A user bringing a concrete feature or a spec link is not asked to explore first.

**Why this priority**: Intake decides the whole run's path; without it users either lose exploration or sit through a redundant interview.

**Independent Test**: Start a run with exploratory wording, with delivery wording, and with neither; confirm the first explores, the second goes straight to feature settlement, and the third asks one intent question.

**Acceptance Scenarios**:

1. **Given** a request worded as open exploration, **When** intake runs, **Then** exploration runs first and the path continues exploration → feature settlement → worktree → the existing spec chain.
2. **Given** a request worded as concrete delivery, or naming an existing spec, **When** intake runs, **Then** the run starts at feature settlement with no exploration interview.
3. **Given** an ambiguous request, **When** intake runs, **Then** the user is asked one question (explore or deliver) and the answer selects the path; no new command flag is needed.
4. **Given** exploration produced a confirmed direction, **When** the user stops there, **Then** the run is paused at feature settlement with the direction in the pending brief and nothing written to the invoking checkout.
5. **Given** such a paused run, **When** it is resumed, **Then** it continues into feature settlement with the recorded answers settled, asking only unresolved feature questions.
6. **Given** a run saved before this change, **When** it is resumed, **Then** it still resumes at its recorded stage with saved answers readable.

---

### User Story 2 - Implementation and repair follow a code-craft method (Priority: P2)

Every fresh code-writing or fixing turn receives and reads the external code-craft instructions (reuse-first minimum-sufficient change, test-driven technique) alongside the factory's engineering rules, so quality does not depend on an agent remembering an earlier turn.

**Why this priority**: Where the routing changes the delivered code; depends only on skill resolution, not the intake path.

**Independent Test**: Inspect a code-writing and a fixing turn's inputs for the resolved absolute paths, then remove one skill and confirm the affected work stops with setup guidance.

**Acceptance Scenarios**:

1. **Given** a run that will deliver code, **When** it commits to delivery, **Then** both code-craft skills are resolved up front and their absolute paths go to every fresh code-writing and fixing turn.
2. **Given** a required code-craft skill cannot be resolved, **When** the affected work would start, **Then** it stops with actionable setup guidance and no turn claims the skill was applied.
3. **Given** a resumed run, **When** a skill name was never resolved or the harness changed, **Then** missing names are resolved and paths re-resolved before work continues.
4. **Given** code-craft guidance would simplify a change, **When** applied, **Then** it stays inside the approved specification, removes no requirement, security control, accessibility behaviour, planned test, repository tooling or engineering-rule evidence, and does not replace the role's result envelope.
5. **Given** the external test-driven guidance defers refactoring to review while the engineering rules allow small behaviour-preserving refactoring while green, **When** they conflict, **Then** the engineering rules win and the adaptation is stated where the roles read it.
6. **Given** a skill's instructions reference its own companion files, **When** a role follows them, **Then** those references resolve from that skill's own directory, not from the factory or the consuming repository.
7. **Given** implementation proceeds, **When** a task completes, **Then** the existing one-commit-per-task, red-proof, exemption and missing-runner rules still apply, including after a handover.

---

### User Story 3 - The user confirms test seams even in fast mode (Priority: P3)

Before implementation begins, the proposed public test seams reach the user for confirmation. Fast mode, which otherwise auto-accepts recommended answers, never answers this confirmation for them.

**Why this priority**: Protects a decision the user must own, but the run can already deliver code without it.

**Independent Test**: With fast mode on, confirm the seam question is shown and waits; resume with unchanged seams and confirm it is not re-asked.

**Acceptance Scenarios**:

1. **Given** a plan proposing public test seams, **When** that stage finishes, **Then** the seams are relayed to the user as a question marked as requiring a user answer, before implementation starts.
2. **Given** fast mode is on, **When** that question is relayed, **Then** it is not auto-answered and the run waits for the user.
3. **Given** a question saved without the new field, **When** fast mode evaluates it, **Then** its current behaviour is unchanged.
4. **Given** confirmed seams with unchanged plan and scope, **When** the run resumes, **Then** the confirmation is reused, not re-asked.
5. **Given** the seams changed after confirmation, **When** implementation would start, **Then** a new confirmation is required.
6. **Given** a plan whose parts are all exempt, **When** the confirmation would be relayed, **Then** it is skipped.
7. **Given** a task needs an unlisted seam, **When** implementation reaches it, **Then** it fails under the existing missing-seam policy; those turns never ask the user directly and never invent a seam.

---

### User Story 4 - UI changes get a disciplined UI evaluation (Priority: P4)

When a change can affect what a user sees, the UI review follows the external audit-and-critique method, stays read-only, and states what evidence it had. Changes that cannot affect the interface skip the UI passes.

**Why this priority**: Improves review quality for a subset of runs; independent of intake and implementation routing.

**Independent Test**: Produce diffs limited to design tokens, a locale string, user-visible copy in UI code, and backend code only; confirm the first three are UI changes and the last skips the UI passes.

**Acceptance Scenarios**:

1. **Given** a diff touching view markup or styles, design tokens or themes, UI assets, or locale and string files, **When** review is reached, **Then** it counts as a UI change.
2. **Given** a diff whose only change is user-visible copy inside UI code, **When** review is reached, **Then** it also counts as a UI change.
3. **Given** a diff touching no user-visible surface, **When** review is reached, **Then** the UI passes are skipped.
4. **Given** a UI change, **When** review runs, **Then** the UI review applies the audit and critique method and the user-experience review runs alongside it rather than repeating the same pass.
5. **Given** the UI review runs, **When** it reports, **Then** it makes no edits, returns findings in the existing machine-readable shape, respects existing review and fix round limits, and discloses whether its evidence was rendered or static.
6. **Given** the UI review was skipped or evidence-limited, **When** the user reaches the approval gate, **Then** that limitation is disclosed there.
7. **Given** confirmed UI findings, **When** they are fixed, **Then** the fixes go through the existing fixing, verification and review path, not the read-only review role.

---

### User Story 5 - A maintainer can read one consistent account of the routing (Priority: P5)

The design record, shared integration reference, role instructions, decision records and user-facing documents all describe the same routing, and every harness distribution carries it identically.

**Why this priority**: Needed for maintainability and identical behaviour on every harness, but it adds no run behaviour by itself.

**Independent Test**: Read the design record and shared reference for the routing rules, then render every harness and confirm the distributions match their sources.

**Acceptance Scenarios**:

1. **Given** the behaviour change, **When** it is made, **Then** the design record states the routing, precedence, protected confirmations and validation before the instruction files carry it.
2. **Given** the code-writing and fixing roles need the same precedence and skill-loading rules, **When** the change lands, **Then** one compact shared integration reference holds them and both roles plus the orchestrator link to it.
3. **Given** the decision record that rejected an external test-driven skill, **When** the change lands, **Then** it is revised in place to describe the skill's contribution under factory orchestration and precedence.
4. **Given** a reader consulting the readme or product brief, **When** they look for prerequisites, **Then** they can tell required skills apart from conditionally resolved ones.
5. **Given** changed sources, **When** every harness is rendered, **Then** the distributions match their sources exactly, with no hand-edited distribution file and no change to harness-specific model settings.

### Edge Cases

- Exploration skill missing on the idea path: that path pauses with setup guidance naming the skill; no substitute, nothing auto-installed. The feature path never needs it.
- User declines installing the UI evaluation skill: the UI review is skipped and disclosed at approval, as today.
- Intake wording carries both exploration and delivery cues: the single intent question decides.
- User answers only the intent question and stops: the run stays paused and resumable, with no repository writes.
- Harness changes between pause and resume: skill paths are re-resolved before any role uses them.
- A fixing turn, not the first implementation turn, needs a seam the plan omits: the missing-seam failure applies equally.
- Test runner exists but cannot be run: the existing stop-and-report policy applies unchanged.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Intake MUST classify the request text into exploration or delivery, route explicit exploration wording to idea exploration, route explicit delivery wording or a spec link to feature settlement, and ask exactly one intent question when the request is ambiguous, without adding a command flag.
- **FR-002**: The idea path MUST run exploration, then feature settlement, then worktree creation, then the existing spec chain; the feature path MUST start at feature settlement.
- **FR-003**: Feature settlement MUST treat decisions already settled during exploration as inputs and ask only unresolved questions.
- **FR-004**: Intake MUST write nothing to the invoking checkout; its artifacts MUST live in the existing pending storage until a worktree exists, then move into it, and the factory MUST keep ownership of commits.
- **FR-005**: Stopping after exploration MUST leave the run paused at feature settlement with the confirmed direction in the pending brief; resume MUST continue into feature settlement.
- **FR-006**: The stage vocabulary and resume handling MUST include the exploration stage while keeping every existing stage and saved run readable.
- **FR-007**: All skill lookups MUST use the active adapter's existing resolution operation, keeping machine-specific paths out of the harness-neutral core, and MUST record the selected logical skill names and resolved paths in the existing state skill map.
- **FR-008**: The exploration skill MUST be resolved only on the idea path, and the UI evaluation skill only when UI review is relevant.
- **FR-009**: Both code-craft skills MUST be resolved before a code-delivery run commits, and their absolute instruction paths MUST be passed to every fresh code-writing and fixing turn.
- **FR-010**: On resume, unresolved skill names MUST be resolved and all resolved paths MUST be re-resolved when the harness has changed.
- **FR-011**: A required missing skill MUST stop the affected work with actionable setup guidance; no role may claim an unavailable skill was applied, and nothing may be installed beyond the existing authorised install offer.
- **FR-012**: References inside a skill's instructions MUST be resolved from that skill's own directory.
- **FR-013**: Code-craft guidance MUST apply within the approved specification and MUST NOT remove requirements, security, accessibility, planned tests, repository tooling or engineering-rule evidence, nor replace a role's required result envelope.
- **FR-014**: The factory engineering rules MUST remain authoritative over skill guidance; the refactor-while-green conflict MUST be resolved in their favour and stated explicitly, and no existing engineering rule may be weakened.
- **FR-015**: Implementation MUST keep the existing red-proof evidence, one-commit-per-task rule, test exemptions and missing-runner failure policy, including after a handover.
- **FR-016**: The spec-building role MUST relay the plan's proposed public test seams to the user before implementation, as a question flagged as requiring a user answer.
- **FR-017**: Fast-mode automation MUST NOT answer questions flagged as requiring a user answer, in addition to the existing decision-changing remediation questions; questions saved without the flag MUST keep their current behaviour.
- **FR-018**: A seam confirmation MUST be reused only when the same seams and scope were already explicitly agreed; changed seams MUST require a new decision, and a plan whose parts are all exempt MUST skip the confirmation.
- **FR-019**: Code-writing and fixing turns MUST NOT ask the user directly and MUST NOT invent a seam; a needed seam the plan omits MUST fail under the existing policy.
- **FR-020**: UI-change detection MUST cover view markup and styles, design tokens and themes, UI assets, and locale and string files, and MUST additionally treat a diff whose only change is user-visible copy in UI code as a UI change; a diff with no user-visible surface MUST skip the UI passes.
- **FR-021**: The UI review MUST follow the external audit and critique method, stay read-only, return findings in the existing machine-readable shape, respect existing review and fix limits, and run its setup once in the reviewer's context with the applicable platform references resolved.
- **FR-022**: The UI review MUST use rendered evidence when available, covering relevant viewports, states, themes and interactions, and MUST disclose the evidence it had and its limits rather than describing static inspection as an observed interaction.
- **FR-023**: The complementary user-experience review MUST remain a distinct lens rather than a second identical UI pass.
- **FR-024**: UI fixes MUST be carried out by the existing fixing role through the existing verification and review path.
- **FR-025**: A skipped or evidence-limited UI evaluation MUST be disclosed at the approval gate.
- **FR-026**: The design record MUST be updated first with routing, precedence, protected confirmations and validation; a single compact shared integration reference MUST hold the precedence and skill-loading rules and be linked from the orchestrator and both code-writing roles.
- **FR-027**: Orchestrator intake, conditional skill resolution, role inputs, UI detection, the state and protocol references, and the spec-building, code-writing, fixing and UI review roles MUST be updated where the routing affects them.
- **FR-028**: The decision record rejecting an external test-driven skill MUST be revised in place, and the readme and product brief MUST distinguish required prerequisites from conditional skills.
- **FR-029**: Every harness MUST be rendered canonically from the changed sources; generated distributions MUST NOT be hand-edited, and harness-specific model settings MUST NOT change in this feature.
- **FR-030**: No new agent role, harness verb, model tier, external service or second planning chain may be added; the existing state, ledger and history MUST carry the new activity rather than a new telemetry mechanism.

### Key Entities

- **Intake intent**: exploration or delivery; decides the path, settled by wording or one question.
- **Exploration stage** `brainstorm`: the idea path's first stage, settling into `grill`; its confirmed direction lands in the pending brief, resumable from pending storage.
- **Skill map entry**: a logical skill name plus the path resolved for the active harness, stored in run state, re-resolved when the harness changes.
- **Protected question**: a relay question flagged as requiring a user answer, which fast mode must not auto-accept; seam confirmation is one.
- **Seam confirmation**: the agreed public test seams, persisted with the plan and invalidated when seams or scope change.
- **UI change signal**: a diff's classification as affecting a user-visible surface: tokens, themes, assets, locale strings, user-visible copy.
- **Shared integration reference**: the one compact document holding skill precedence and loading rules for the orchestrator and code-writing roles.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In three intake trials (explicit exploration, explicit delivery, ambiguous), the path matches the intent every time and the ambiguous case asks exactly one question.
- **SC-002**: A user with only an idea reaches a recorded, confirmed direction and can stop, with zero files changed in the invoking checkout.
- **SC-003**: Feature settlement after exploration repeats none of the already-answered questions.
- **SC-004**: 100% of fresh code-writing and fixing turns receive both code-craft paths; with one skill removed, 100% of affected turns stop with setup guidance and none report work as completed.
- **SC-005**: With fast mode on, the seam confirmation reaches the user in every run with a testable seam, and is re-asked only when seams or scope changed.
- **SC-006**: Across four UI-detection trials (tokens, locale strings, user-visible copy in UI code, backend-only), classification is correct in all four and the UI review makes zero edits.
- **SC-007**: Every UI review report states whether its evidence was rendered or static, and every skip or limitation appears at approval.
- **SC-008**: Every run saved before this change still resumes at its recorded stage with its answers intact.
- **SC-009**: After rendering every harness, the distributions match their sources with no differences and no hand edits, and link and schema checks pass.
- **SC-010**: The routing, precedence and protected-confirmation rules are stated once as the source of truth and agree with every role instruction depending on them.

## Assumptions

- The design document dated 25 October 2026 is approved and implemented as written; its "Files to align" list and "Acceptance scenarios" bound the scope.
- The external skills (`brainstorming`, `grilling`, `ponytail`, `tdd`, `impeccable`) are user-installed and resolved by logical name; this feature neither vendors nor auto-installs them, beyond the existing authorised UI-evaluation install offer.
- The code-craft simplification skill runs at its default intensity, bounded by the approved spec and the engineering rules.
- The product changed here is the factory instruction set: behaviour lives in the harness-neutral sources and adapters; distributions are re-rendered, never edited.
- Static link, schema and render checks are the automated verification available; routing, protected-question and role-following behaviour need real agent-driven runs and are reported separately.
- Existing question shapes, saved answers, question IDs, state fields and resume digests stay backward compatible.
