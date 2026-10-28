# Feature: Blank-name greeting

## User Story 1 (P1)
As a caller I receive a useful greeting when a name is blank.

Acceptance: `greet("")` and `greet("  ")` return `Hello, stranger!`; `greet("world")` remains `Hello, world!`.

## Functional Requirements
- FR-001: Empty or whitespace-only names use `stranger` as the greeting name.
- FR-002: Preserve every nonblank name exactly, including surrounding whitespace.

## Success Criteria
- SC-001: The normal, empty and whitespace-only greeting checks pass under the existing Python unittest runner.

No new dependency, network behavior, persistence or public entry point.
