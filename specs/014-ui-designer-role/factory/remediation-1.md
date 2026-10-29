# Remediation log — pass 1

- I1: spec.md Assumptions now says the role-generic 300-second default applies with no role-specific entry; "time budget" removed from FR-004's enumeration (and "read-only/" dropped, since only write access applies).
- U1: spec.md FR-030 now requires that a map reference to a missing evidence file fails the drop before any move, naming the path, with the map and run folder unchanged. This traces the confirmed S3 failure path; seam scope unchanged.
- C1: plan.md "Quality constraints" records that SC-001..SC-005 and SC-007 are verified by prompt review of exempt text (T013, T016), with live fixture trials out of scope and SC-006 automated; tasks.md T016 adds the trace step.
- A1: spec.md FR-006 states one spawn per contiguous run of `[UI]` tasks; FR-024 and tasks.md T014 define "last" as no unchecked `[UI]` task remaining in `tasks.md` (derived by the role, so FR-007 inputs unchanged); tasks.md T006 states the spawn unit and adds `ui-designer` to SKILL.md's "Time budget" file-writing role list.
- I2: plan.md "New items" and tasks.md T004 list `scope` with nested `target` or `accepted_files`/`excluded`, matching data-model.md; no top-level `accepted_files`.
- C2: spec.md FR-029 narrowed to the CLI file-writing role check accepting the role's `partial` return, matching seam S1; no seam added.

Word budgets: spec.md 3000/3000, plan.md 717/2000, tasks.md 2498/2500 (tasks.md trimmed: duplicate "Parallel examples" and "New files" sections removed; spec.md Context tightened). Confirmed test scope (S1–S3 and failure paths) unchanged.
