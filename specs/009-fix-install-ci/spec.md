# Feature Specification: Restore installer CI coverage

**Feature Branch**: `009-fix-install-ci`

**Created**: 2026-10-27

**Status**: Draft

**Input**: Fix the two failing OpenCode installer tests by correcting their temporary environment while preserving installer validation.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reliable installation checks (Priority: P1)

As a maintainer, I need the installation checks to reach the success and conflict behavior they are intended to verify, so CI failures identify real regressions.

**Why this priority**: Two existing checks currently fail at an unrelated environment prerequisite and block CI.

**Independent Test**: Run the affected installation checks in disposable user environments and verify both their intended outcomes.

**Acceptance Scenarios**:

1. **Given** an existing explicitly configured factory home and no conflicting harness files, **When** installation runs, **Then** it succeeds, installs the factory skill and every role-agent link, and reports the session guidance.
2. **Given** an existing explicitly configured factory home and a user file occupying the skill destination, **When** installation runs, **Then** it fails with the conflict-resolution diagnostic and preserves that file unchanged.
3. **Given** an explicitly configured factory home that does not exist, **When** installation runs, **Then** the existing missing-directory rejection remains in effect.

### Edge Cases

- The success check must verify a nonempty complete role-agent set even in a clean checkout with no pre-generated distribution.
- Every filesystem change made by the installation checks stays inside its disposable environment.
- Conflict rejection must preserve the exact contents of the existing user file.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The two affected checks MUST establish the existing-directory prerequisite before attempting installation.
- **FR-002**: The success check MUST retain verification of the installed skill link, all role-agent links, and fresh-session guidance; its expected role set MUST remain meaningful without pre-generated checkout output.
- **FR-003**: The conflict check MUST retain verification of nonzero exit status, the conflict-resolution diagnostic, and unchanged user-file contents.
- **FR-004**: The change MUST preserve the installer policy that an explicitly configured factory home already exists; it MUST introduce no product behavior changes.
- **FR-005**: Verification MUST cover the full existing test suite, generation for all five supported harnesses, distribution drift, and installer shell syntax.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Both previously failing checks pass and reach their intended success or conflict outcomes.
- **SC-002**: The complete existing test suite finishes with zero failures.
- **SC-003**: All five supported harness distributions generate successfully, the drift check passes, and installer syntax validation passes.
- **SC-004**: The conflict scenario leaves the user file byte-for-byte unchanged, and existing missing-directory rejection remains unchanged.

## Assumptions

- Scope is test setup and related assertion correctness only; installer policy and factory workflow are settled.
- The existing installer subprocess boundary is the accepted verification seam; no new dependency or test runner is needed.
- Generated checkout distribution output may be absent on a clean checkout. Installation itself produces the per-user distribution.
