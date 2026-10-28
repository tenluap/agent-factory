# Tasks: Blank names

Input: spec.md and plan.md. Existing stdlib unittest runner.

## Phase 1: Setup
Existing project and runner need no changes.

## Phase 2: Foundation
No additional prerequisites.

## Phase 3: US1 — Blank names (P1, MVP)
Goal: Empty and whitespace-only names receive the stranger greeting while all other names remain unchanged.
Independent check: `python3 -m unittest discover -s .`.

- [x] T001 [US1] Implement blank-name greeting through planned seam `greet` (`src.greet.greet`): first add `GreetTests.test_blank_names` in `test_greet.py` asserting empty and whitespace-only names return `Hello, stranger!` and preserve ordinary/nonblank padded names; run it and observe expected failure; then implement the fallback in `src/greet.py`; finally run `python3 -m unittest discover -s .` passing. Required commit proof: `Red: GreetTests.test_blank_names failed as expected` (or the ENG-2 existing-test form if already covered). Done when blank inputs fall back, every nonblank name is preserved, all tests pass, and test/code/task checkbox are committed together once.

## Final phase: Verification
Passing verification is included in T001; no separate test-only or implementation-only commit.

## Dependencies and execution
T001 is the sole unit; no parallel opportunities because test and implementation form one commit. US1 is the MVP and full scope. Run red, implementation, passing verification sequentially, then mark complete and commit.
