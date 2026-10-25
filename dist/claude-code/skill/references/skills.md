# Skill integration and precedence

Shared by the orchestrator and every code-writing role, so the rules below live once and are linked, not
restated (`SKILL.md`, `roles/code-build.md`, `roles/fixer.md`).

## Lookup

Every skill is a logical name resolved by the active adapter's `RESOLVE` operation (`verbs.md`); the
resolved absolute path lives in `state.skills`, valid only on the harness that resolved it. No harness tool,
path or command name enters `core/`. On resume, a name never resolved is resolved, and every path is
re-resolved when `harness` changed.

## Required vs conditional

| Logical name | Resolved | Scope |
|---|---|---|
| `speckit-*`, `grilling`, `domain-modeling`, `pr` | preflight | every run |
| `ponytail`, `tdd` | preflight, before a run commits to code delivery | every fresh `code-build`/`fixer` spawn gets both absolute paths |
| `brainstorming` | preflight | idea path only; never resolved on the feature path |
| `impeccable` | step 6, on a UI diff | existing install offer; declined install is a disclosed skip |

A required skill that cannot be resolved stops the affected work with setup guidance naming the logical name
and the directories searched. Nothing is installed beyond the existing authorised `impeccable` offer, and no
turn claims an unavailable skill was applied.

## Precedence

The factory's own engineering-rules reference always wins over a skill's guidance. In particular: the
factory permits small behaviour-preserving refactoring while tests stay green; a skill that instead defers
all refactoring to review does not change that. A skill's guidance applies only inside the approved
specification — it removes no requirement, security control, accessibility behaviour, planned test,
repository tooling or rule evidence, and never replaces a role's required result envelope.

## Companion references

A skill's own companion files (for example a test-writing skill's mocking guidance) resolve from that
skill's own directory, never from the factory's directory or the consuming repository.

## Bounded application

Apply a skill's technique or persona proportionately, bounded by the approved spec: it changes how work is
done, not what was agreed. A seam a skill's method needs that the plan does not list is a missing seam, not
an invented one — stop and report it as a failure; never ask the user directly from a code-writing or
fixing turn.
