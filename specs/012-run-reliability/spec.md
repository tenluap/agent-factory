# Feature Specification: Factory Run Reliability

**Feature Branch**: `012-run-reliability`

**Created**: 2026-10-28

**Status**: Ready for planning

**Input**: Improve the factory from the recorded issues of run `011-drop-factory-folder`: unavailable models, conflicting test/implementation tasks, an unplanned failure-injection seam, and short deadline overshoots.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Discover unusable model setup before delivery (Priority: P1)

As a factory user, I want the factory to check the model setup it can inspect and explain a rejected model accurately, so I can correct the setup without discovering the same rejection repeatedly after a run starts.

**Why this priority**: Two rejected model selections caused two startup halts in the source run.

**Independent Test**: Exercise supported model-availability checks with available, unavailable, and indeterminate results; verify that the selected model is preserved and each result has an appropriate continuation or recovery path.

**Acceptance Scenarios**:

1. **Given** an explicitly selected model that the active harness authoritatively reports unavailable, **When** preflight checks it, **Then** the factory stops before creating run state or a worktree and names the rejected model and the correction/recheck steps.
2. **Given** the selected model appears in the supported inventory, **When** preflight succeeds, **Then** the factory continues with that exact selection; inventory membership is not described as proof of service access.
3. **Given** the harness cannot inspect model availability, or inspection fails, **When** preflight runs, **Then** it states that availability is unverified and continues under the existing bounded spawn-failure policy rather than inventing success or selecting a replacement.
4. **Given** a later spawn rejects a model, **When** the failure is reported, **Then** the diagnostic preserves the model and rejection details, provides actionable recovery, and follows the existing retry/halt policy without silently changing models.

---

### User Story 2 - Complete test-first work as one passing commit unit (Priority: P1)

As a factory user, I want generated tasks, execution, review, and resume to agree on the unit of work, so an agent can write a failing test, implement the behavior, and commit the passing result without contradictory instructions.

**Why this priority**: The source run restarted implementation because separate test and implementation tasks conflicted with the requirement to commit them together.

**Independent Test**: Follow a generated behavior-changing task from its observed failing test through a passing implementation and a single commit, then repeat from an interrupted task.

**Acceptance Scenarios**:

1. **Given** a new behavior-changing task, **When** tasks are generated, **Then** its test-first and implementation steps form one named commit unit with a mapped seam and an observable completion condition.
2. **Given** a commit unit whose test fails as expected, **When** implementation makes it pass, **Then** the agent records the required red proof and commits test and implementation together once; the test step alone is not marked complete or committed separately.
3. **Given** an interruption between the failing test and passing implementation, **When** a fresh agent resumes, **Then** it inspects saved artifacts and current work, continues the same incomplete unit, and does not require a separate red commit or repeat completed commits.
4. **Given** older tasks with adjacent test/implementation entries, **When** a run resumes, **Then** both entries are treated as one passing commit unit where their pairing is unambiguous; an ambiguous pairing is reported for resolution before behavior-changing work.

---

### User Story 3 - Resolve missing test seams before implementation (Priority: P1)

As a factory user, I want task requirements checked against the confirmed test plan, so failure-path tests do not discover missing or unconfirmed seams during implementation.

**Why this priority**: The source tasks required a git-failure injection path that the plan had not covered clearly enough.

**Independent Test**: Analyze tasks that require an undeclared or changed failure-injection seam and verify they cannot proceed to implementation until the plan and confirmation cover the requirement.

**Acceptance Scenarios**:

1. **Given** tasks requiring a failure-path test absent from the plan, **When** analysis runs, **Then** it reports a HIGH blocking seam-coverage finding naming the task and the uncovered failure path.
2. **Given** a plan updated with a new seam or a broader failure-injection scope, **When** the plan is reconsidered, **Then** the earlier confirmation is invalidated and a protected user confirmation is required before implementation.
3. **Given** every task and required failure path is covered by the confirmed plan, **When** analysis runs, **Then** seam coverage passes without treating the confirmation text itself as a seam declaration.
4. **Given** a documentation/configuration task with a stated valid exemption, **When** analysis runs, **Then** it honors that exemption without inventing a runtime seam or weakening requirements for non-exempt tasks.

---

### User Story 4 - Hand off at useful deadline boundaries (Priority: P2)

As a factory user, I want agents to account for time before starting additional work, so short budgets do not trigger avoidable verification restarts and required verification still finishes before approval.

**Why this priority**: The source run recorded overshoots of 8, 6, and 3 seconds at commit or verification boundaries, with progress each time; these do not establish runaway test loops.

**Independent Test**: Exercise an agent near its deadline with a completed task and pending optional verification, then resume it and verify that required checks and progress remain accounted for.

**Acceptance Scenarios**:

1. **Given** a completed passing commit unit and insufficient remaining time for optional repeated broad verification, **When** the agent chooses its next action, **Then** it saves progress and returns partial rather than starting an avoidable broad test run.
2. **Given** a unit already in flight when its deadline passes, **When** it reaches a safe completion boundary, **Then** it finishes and commits that unit, reports the actual overshoot, and starts no further unit.
3. **Given** required checks still pending when an agent returns partial, **When** the run resumes, **Then** they remain pending and the orchestrator independently completes the required checks before review/approval; a partial handoff never claims verification passed.
4. **Given** small boundary overshoots or repeated partial returns, **When** issues are recorded, **Then** actual durations, causes, work commits, and existing no-progress stall enforcement remain intact.

### Edge Cases

- The installed model configuration differs from repository defaults, or the harness inherits its model without exposing a resolvable model identifier.
- Model inventory is unavailable, stale, or contradicted by a later access rejection; an unchecked result must remain distinct from an available result.
- A resumed run changes harness or model setup; the applicable setup check is repeated before further role work.
- Legacy tasks contain a completed pair, a partly completed pair, or ambiguous dependencies; completed work is preserved and unresolved pairing is not guessed.
- A task names an existing seam but introduces a new injected failure path; matching only its name must not bypass scope confirmation.
- A red test exists at interruption, a commit finishes after the deadline, or the full suite is still running; red proof and outstanding verification are preserved accurately.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Preflight MUST check effective model selections using the active harness's supported inspection capabilities before new run state/worktree creation, and on resumed runs when the applicable harness/model setup changes. It MUST distinguish confirmed unavailability from an indeterminate check.
- **FR-002**: A confirmed unavailable model MUST block startup with its exact selection, available diagnostic evidence, and actionable correction/recheck guidance. Unsupported or failed inspection MUST be disclosed as unverified and MUST retain the existing bounded runtime failure policy.
- **FR-003**: Model checks and recovery MUST preserve explicit user choices. The factory MUST NOT guess aliases, silently substitute a model, change credentials, or describe inventory membership as confirmed access. Rejections discovered later MUST retain their evidence and existing retry/halt accounting.
- **FR-004**: New behavior-changing tasks MUST define one commit unit containing the failing-test step, passing implementation, mapped seam, required red proof, and a completion condition. Generation, analysis, execution, fixing, review, and resume instructions MUST agree on this unit. Valid documentation/configuration exemptions remain supported.
- **FR-005**: A unit MUST be completed and committed once with test and implementation together. Resume MUST preserve completed work, inspect partial work, and continue unfinished units. Unambiguously paired legacy test/implementation tasks MUST remain resumable without separate red commits; ambiguous pairings MUST be surfaced before behavior-changing work.
- **FR-006**: Before implementation, analysis MUST check every non-exempt task's required test seams and injected failure paths against the plan's declared and confirmed scope. Missing coverage or confirmation MUST be HIGH and blocking; implementation/fixing MUST retain the existing stop-and-report guard for any later-discovered gap.
- **FR-007**: Adding, removing, renaming, or expanding the confirmed seam/failure-path scope MUST require a fresh protected user confirmation. Fast mode MUST NOT infer this confirmation. Confirmation evidence MUST remain separate from seam declarations.
- **FR-008**: File-writing roles MUST check remaining time at commit-unit boundaries and avoid starting optional repeated expensive verification when it cannot reasonably fit. They MUST finish an in-flight unit safely and return partial at the next boundary once the deadline has passed, with accurate progress and overrun information where applicable.
- **FR-009**: Deadline handling MUST preserve configured budgets, mandatory task checks, independent orchestrator verification, issue records, and the existing no-progress stall limit. Pending required checks MUST be explicit across handoffs; no unperformed check may be represented as passed.
- **FR-010**: Changes MUST follow the repository's design-first, harness-neutral core, stateless-role, and generated-distribution contracts. All supported harnesses MUST receive consistent portable task/seam/deadline guidance; model inspection details MUST remain specific to the active harness's actual capabilities.

### Key Entities

- **Model setup result**: The effective selection, evidence source, and available/unavailable/unverified outcome; an available inventory entry does not prove access.
- **Commit unit**: One behavior-changing task's red step, implementation, verification, completion state, and single passing commit; legacy task pairs may jointly represent one unit.
- **Confirmed test scope**: Declared seams and required failure paths, paired with explicit user acceptance of that exact scope.
- **Verification handoff**: Completed work and outstanding checks preserved for a fresh role and the orchestrator.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every exercised confirmed-unavailable model case stops before creating run resources and identifies the rejected selection plus a recovery action; no case silently changes model selection. Every unsupported/failed-inspection case is labeled unverified.
- **SC-002**: Every exercised new behavior-changing task completes with one passing test-and-implementation commit and the required red proof; interruption/resume cases preserve that result without a separate red commit or duplicate completed work.
- **SC-003**: Every exercised missing seam, missing injected failure path, or stale confirmation case is blocked before implementation; all covered and validly exempt cases remain eligible to proceed.
- **SC-004**: Every exercised deadline handoff preserves completed work and pending checks, records real overshoots without suppression, and reaches approval only after all required verification passes. No test case changes the configured budget or bypasses stall enforcement.
- **SC-005**: All supported harness outputs remain reproducible from their sources, existing automated checks pass, and focused end-to-end scenarios demonstrate the changed setup, task/resume, seam-confirmation, and deadline flows.

## Assumptions

- The user accepted this scope, the lite specification chain with fast relays, and the repository verification commands during initial grilling. Protected seam confirmations and final publication approval remain explicit.
- Supported model inspection capabilities vary by harness. This feature improves available checks and honest recovery guidance; it does not promise a universal live access probe or repair third-party model services.
- The source backlog is evidence of the named situations, not proof of eight independent defects or of a test-performance bottleneck. Raising budgets, hiding overruns, and optimizing unmeasured test performance are outside scope.
- Existing run-state compatibility, atomic writer rules, failure limits, and skill integration remain in force. The accepted intake writer exception is specific to this run and does not expand this feature into a general intake-state redesign.
