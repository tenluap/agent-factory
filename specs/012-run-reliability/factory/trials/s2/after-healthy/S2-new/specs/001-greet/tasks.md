# Tasks: Blank-name greeting

Input: approved spec.md and plan.md in specs/001-greet.
Tests are required by factory engineering rules. One checkbox is one passing test-and-implementation commit.

## Phase 1: Setup
Existing Python unittest runner and project structure need no setup tasks.

## Phase 2: Foundational
Public greet seam is confirmed in plan.md. No blocking infrastructure work.

## Phase 3: User Story 1 — useful blank-name greeting (P1, MVP)
Goal: FR-001 blank names use stranger; FR-002 all nonblank names remain unchanged.
Independent check: python3 -m unittest discover -s . covers normal, empty, whitespace-only and surrounding-whitespace inputs (SC-001).

- [X] T001 [US1] Handle blank names while preserving nonblank names in src/greet.py and test_greet.py. Seam: greet (public src.greet.greet). Ordered steps: (1) add GreetTests.test_blank_names_use_stranger and GreetTests.test_preserves_nonblank_names in test_greet.py; run python3 -m unittest test_greet.GreetTests.test_blank_names_use_stranger and observe expected assertion failure; (2) implement the smallest blank-name fallback in src/greet.py without stripping nonblank output; (3) run python3 -m unittest discover -s . and require all tests to pass. Required commit-body proof: Red: test_greet.GreetTests.test_blank_names_use_stranger failed as expected. Done when empty, spaces, tab/newline names greet stranger, nonblank names including surrounding whitespace are preserved, the suite passes, and test/code/task checkbox are committed together.

## Final Phase: Polish and cross-cutting concerns
No separate behavior or documentation changes required; final build/test use the existing unittest command.

## Dependencies and execution order
Setup/foundation are already available → T001 → final build/test. There is one story and one commit unit.

## Parallel example: US1
None: test and implementation share one ordered unit; red must precede code edits.

## Implementation strategy
Deliver US1 as the complete MVP. Observe red, implement, verify green, then check and commit T001 once. No new files, abstractions or dependencies.
