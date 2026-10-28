# Tasks: Blank-name greeting

**Input**: Approved spec.md and plan.md in specs/001-greet/.
**Tests**: Required by factory ENG-1; existing Python unittest runner.

## Phase 1: Setup
Existing src/greet.py, test_greet.py and unittest need no setup or new dependency.

## Phase 2: Foundational
No additional prerequisite work.

## Phase 3: User Story 1 — Useful blank-name greeting (P1, MVP)
**Goal**: FR-001 blank names use stranger; FR-002 preserves every nonblank name.
**Independent test**: python3 -m unittest discover -s . passes all normal, blank and surrounding-whitespace cases (SC-001).

- [X] T001 [US1] Add failing greet seam tests GreetTests.test_blank_names_use_stranger and GreetTests.test_preserves_nonblank_whitespace in test_greet.py; retain GreetTests.test_greets_by_name. Run before implementation and observe blank cases fail (FR-001, FR-002).
- [X] T002 [US1] Implement blank-name fallback at greet seam src.greet.greet in src/greet.py, preserving every nonblank name; pass T001 tests and existing GreetTests.test_greets_by_name (FR-001, FR-002, SC-001).

## Phase 4: Polish and validation
Run existing build/test command after T002. No extra artifact, abstraction or dependency.

## Dependencies and execution order
T001 immediately precedes T002. Observe red during T001, then implement T002 and run green. Commit test and implementation together once under ENG-3, naming both task IDs and recording the observed failing test. No separate red commit.

## Parallel example: User Story 1
None: T002 depends on T001 and the red observation.

## Implementation strategy
Complete US1 as the MVP, using the confirmed greet seam only; verify all acceptance cases with the existing runner. No test exemption applies.
