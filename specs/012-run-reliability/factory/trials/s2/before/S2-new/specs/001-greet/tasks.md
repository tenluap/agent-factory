# Tasks: Blank names

## Phase 1: Setup
Existing Python stdlib unittest runner and project structure need no setup.

## Phase 2: Foundational
No additional prerequisites.

## Phase 3: User Story 1 — Blank names (P1, MVP)
Goal: Empty and whitespace-only names receive the stranger greeting; preserve all other names.
Independent test: Run `python3 -m unittest discover -s .`; assert empty, whitespace-only and normal-name greetings.

- [ ] T001 [US1] Add and observe failing `GreetTests.test_blank_names` in `test_greet.py`; seam `greet`, covering empty and whitespace-only inputs and preserving normal names.
- [ ] T002 [US1] Implement blank-name fallback in `src/greet.py`; seam `greet`; make `GreetTests.test_blank_names` and existing name coverage pass.

## Final Phase: Polish
No separate polish changes required. Final build/test uses the existing unittest command.

## Dependencies and execution order
T001 → T002. US1 is the whole MVP. No parallel opportunities: both tasks share the tested behavior and depend on each other.

## Parallel example: US1
None; execute T001 then T002.

## Implementation strategy
Write and run the blank-name test first, then make the smallest passing change at the confirmed greet seam. Preserve nonblank names verbatim.
