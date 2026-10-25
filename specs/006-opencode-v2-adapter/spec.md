# Feature Specification: OpenCode V2 adapter

**Feature Branch**: `006-opencode-v2-adapter`

**Created**: 2026-10-25

**Status**: Draft

**Input**: Check whether the existing OpenCode harness works with V2 and make the smallest update needed for native V2 operation. Continue the settled adapter change through the factory workflow.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Use native OpenCode V2 factory roles (Priority: P1)

As a factory operator upgrading OpenCode, I need the installed factory roles and instructions to use V2's native capabilities while retaining the access restrictions assigned to each role.

**Why this priority**: Operators need compatible role definitions and instructions before relying on a factory run after upgrading.

**Independent Test**: Generate the OpenCode distribution, inspect all nine role definitions and the harness instructions against the V2 contract, and compare each role's permitted actions with its existing access intent.

**Acceptance Scenarios**:

1. **Given** the nine factory roles, **When** their OpenCode definitions are generated, **Then** every role is defined as a subagent with native ordered permission rules; read-only roles deny editing and child-agent dispatch, and write roles deny child-agent dispatch without adding an edit denial.
2. **Given** the factory's OpenCode instructions, **When** an orchestrator follows spawning, parallel spawning, or shell instructions, **Then** those instructions name V2's native subagent and shell capabilities and retain the existing named-role, model-default, and override behavior.
3. **Given** an existing installation, **When** the updated distribution is installed, **Then** its global and project install locations remain the same and no user configuration migration is required.

---

### User Story 2 - Retain every other harness's behavior (Priority: P2)

As a factory maintainer, I need the OpenCode update to leave other harnesses' native roles and the shared factory flow intact so I can release the adapter without introducing unrelated migrations.

**Why this priority**: The shared distribution process serves multiple harnesses; a targeted compatibility update must preserve their existing contracts.

**Independent Test**: Generate every supported distribution with canonical model defaults and compare it with the baseline. Inspect differences in other harnesses to confirm that only their bundled shared OpenCode reference changes.

**Acceptance Scenarios**:

1. **Given** canonical generation inputs, **When** every supported harness is generated, **Then** other harnesses' native role definitions remain byte-identical to the baseline, while each distribution includes the updated shared OpenCode reference.
2. **Given** the updated source and committed distributions, **When** generation runs again with the same canonical inputs, **Then** every tracked distribution is reproduced without additions or modifications.
3. **Given** an operator's configured model overrides, **When** a distribution is generated for installation, **Then** existing model-default and override behavior is preserved.

---

### User Story 3 - Understand compatibility and verification limits (Priority: P2)

As a factory operator, I need a precise compatibility explanation and evidence report so I can distinguish successfully generated or discovered roles from a verified model-backed run.

**Why this priority**: Supported V1 definitions are intended to remain compatible with V2; the native update must not imply that the former setup is wholly broken or that untested execution has succeeded.

**Independent Test**: Review the design and delivery evidence against the checks actually performed, including the observed runtime version and any untested actions.

**Acceptance Scenarios**:

1. **Given** the supported V1 compatibility contract, **When** the update is documented, **Then** it is described as native V2 adoption, without claiming all V1 factory definitions fail on V2.
2. **Given** successful generation and runtime discovery, **When** results are reported, **Then** static checks, loaded role/skill discovery, model-backed dispatch, and runtime permission enforcement are identified separately; unperformed checks remain explicitly unverified.
3. **Given** observed V2 behavior that conflicts with required dispatch or access restrictions, **When** verification detects the conflict, **Then** it reports the version and mismatch as a blocker rather than weakening role restrictions or claiming success.

### Edge Cases

- Ordered permission rules must retain their sequence and the intended action, resource, and effect for every role; a read-only role must not gain editing or child-agent access through conversion.
- Existing scalar, mapping, list, and native agent formats used by other harnesses must retain their output when nested permission rules are introduced.
- User model overrides must not contaminate the canonical generated distributions or disappear from normal installation behavior.
- A runtime that can discover definitions without executing a model is sufficient only for discovery evidence. Missing credentials, unavailable runtime capabilities, or unexecuted model calls must be reported as verification limits.
- If runtime discovery registers asynchronously, verification must wait for registration to settle within a bounded interval and report a failure or limitation if it does not.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The OpenCode distribution MUST express all nine factory roles using V2-native subagent definitions and ordered permissions, including each rule's action, resource, and effect. It MUST emit neither the legacy permission map nor the legacy child-agent permission action.
- **FR-002**: The generated rules MUST deny editing and child-agent dispatch for read-only roles, and deny child-agent dispatch for write roles while preserving their existing edit access intent.
- **FR-003**: OpenCode instructions MUST use V2-native subagent and shell capabilities for the existing spawning, parallel spawning, and shell operations, preserving named-role selection and configured model behavior.
- **FR-004**: The update MUST preserve existing global/project installation locations, skill resolution, question relays, neutral verbs, and the harness-neutral factory flow.
- **FR-005**: Canonical generation MUST update every distribution's bundled shared OpenCode reference and leave every other harness's native role definitions and unrelated distribution contents unchanged.
- **FR-006**: Generation MUST support the new ordered permission structure without changing output for previously supported metadata structures and other harnesses' native formats.
- **FR-007**: The changed OpenCode contract MUST be recorded in `DESIGN.md` before the adapter behavior is changed, and all generated distributions MUST be reproducible from their source without manual distribution edits.
- **FR-008**: Verification MUST cover every role's generated access restrictions, representative unchanged formats, complete distribution generation, canonical reproducibility, and existing model field mapping behavior.
- **FR-009**: Compatibility and verification documentation MUST distinguish intended supported V1 compatibility, native V2 adoption, static checks, runtime discovery, and executed model-backed behavior. It MUST report runtime versions and untested capabilities accurately.
- **FR-010**: If runtime validation observes a dispatch or permission contract mismatch, the update MUST treat it as a blocker, retaining access restrictions and the diagnostic evidence.

### Key Entities

- **Harness adapter**: The per-harness translation of factory operations, role metadata, and install locations; this feature changes the OpenCode adapter's native contract.
- **Role access intent**: The read-only or write classification and child-agent restriction that must survive native permission conversion.
- **Rendered distribution**: The generated installable roles, skill, and shared references for one harness, reproducible from the maintained source.
- **Verification evidence**: A record of the checks performed, their environment/version, outcomes, and explicit execution limits.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All nine generated OpenCode roles satisfy their specified V2 role and access contracts, with zero missing restrictions.
- **SC-002**: Every supported distribution is generated successfully; 100% of other harnesses' native role definitions match the pre-change baseline, and their only distribution changes are the bundled OpenCode reference.
- **SC-003**: A second canonical generation produces zero distribution additions or modifications relative to the committed result.
- **SC-004**: The delivery record identifies the outcome or unverified status of all four evidence categories: static checks, runtime discovery, model-backed dispatch, and runtime permission enforcement; zero unexecuted checks are reported as passed.
- **SC-005**: Existing installation locations, model defaults/overrides, and shared factory flow require zero operator migrations as a result of this update.

## Assumptions

- The settled design and saved implementation are context for this specification; this stage does not apply or validate the saved implementation.
- OpenCode intends supported V1 agent, skill, and command definitions to remain compatible. This is native V2 adoption rather than a broad compatibility repair.
- The factory does not integrate with OpenCode server or plugin APIs; migrating those interfaces is outside scope.
- Existing renderer and distribution tooling are reused without new dependencies. No shared factory flow redesign, unrelated V2 configuration, or user configuration edits are included.
- Existing discovery evidence for OpenCode v2.1.4 covers loaded agents, permission configuration, and the factory skill only. It does not establish model-backed dispatch or permission enforcement during tool calls.
- Runtime execution checks are conditional on a usable environment and authorization already available to the run. Missing runtime proof must be disclosed and cannot be replaced by static output assertions.
