# Specification Quality Checklist: Adopt a spec started outside factory

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-11-04
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

- The product is the factory's own command surface, so the command and flags (`/factory adopt`, `--dry-run`, `--stage`), exit codes, the worktree path, history events and run-state fields (`adopted`, `base_commit`) are user-facing contract, not implementation detail. The exact `adopted` block layout and source-shape labels are left to plan.
- All decisions come from the settled brief (Q1-Q9); no clarification markers were needed. Remaining gaps are documented as edge cases or assumptions: ambiguous source exits 3; local branch wins over `origin` with no fetch; an existing worktree path refuses; the write re-checks refusals and rolls back on failure; abandoned pending adoptions use the existing `prune` path.
- Validation pass 1: all items pass. Word count 2710 (budget 3000).
