# Adopted runs are created by an explicit verb, enter at most at analyze, and exempt pre-adoption work only from factory-only rules

2026-11-04: factory could only resume runs it had created, so a plain SpecKit spec (no `factory/state.json`) either dead-ended at `resume` or was duplicated by a new run on a new branch. Spec 022 adds `/factory adopt <branch|spec_dir>`, backed by the CLI writer `factory adopt`, which creates the state the existing resume flow expects. This ADR records the boundaries a future reader would otherwise "fix".

## Decision

1. **Explicit verb, never implicit.** Only `adopt` creates an adopted run. `resume` stays unchanged and only hints at `adopt` in its `no run '<name>' in <repo>` error; a new-feature request never adopts. Adoption is read-only until the user confirms: `--dry-run` report, confirmation grill in pending state under the fixed name `<repo-name>-adopt-<branch>`, then one write committing `factory: adopt <branch>` and nothing else.
2. **Entry at most at analyze.** The entry stage is inferred from the artifacts (`spec.md` -> `plan`, `+plan.md` -> `tasks`, `tasks.md` -> `analyze`) and may be overridden only to `specify`, `plan`, `tasks` or `analyze`. Work authored outside factory always passes factory's analysis before implementation; `implement` is a usage error. The grill recommends the `full` chain when entry is `tasks` or `analyze`.
3. **Adopted artifacts are edited in place.** `specify`, `plan` and `tasks` treat an existing `spec.md`, `plan.md` or `tasks.md` as their base and apply targeted edits; they never regenerate the user's work from the brief.
4. **Pre-adoption boundary at `adopted.base_commit`.** The adopted branch's HEAD at the write splits the run. Reviewers review the whole `base...HEAD` diff, but the commit-evidence rules apply only to later commits and to tasks unchecked at `base_commit`: ENG-2 (red proof in the task commit body), ENG-3 (commit unit) and ENG-1's one passing test-and-implementation commit per checked task. Earlier commits and tasks checked in `tasks.md` at `base_commit` (by task ID) are disclosed as pre-adoption; those tasks are likewise excluded from analyze's blocking test-scope check. Every unchecked, renumbered or new task gets the full checks.
5. **Provenance in state.** A new `adopted` history event and an optional `adopted` block (source and shape, inferred and chosen stage, `base_commit`). Validation accepts an adopted run with no `complete` entries before its chosen stage; states without the block stay valid. The approver screen and retro disclose adoption.

## Considered options

- **Let `resume` adopt a spec it cannot find**: one command fewer, but a typo or wrong branch would silently create a run and commit to someone's branch. Rejected for an explicit, previewed verb.
- **Allow entry at `implement` when `tasks.md` has checked boxes**: faster for nearly finished work, but it would skip the only gate that checks outside artifacts against factory's test-scope and commit-unit rules. Rejected; implement still resumes from the checkboxes after analyze.
- **Hold pre-adoption commits and checked tasks to ENG-1, ENG-2, ENG-3 and the test-scope check**: every adopted run with history would raise blockers no one can fix without rewriting published commits. Rejected; the code is still reviewed in full, only the factory-only process rules are waived.
- **Regenerate adopted artifacts from the brief**: simpler stage prose, but it would discard the user's own spec, plan and tasks.

## Consequences

- `adopted` and `base_commit` are part of the state schema and the closed history-event vocabulary; removing them later is a state migration.
- Pre-adoption tasks are identified by task ID at `base_commit`, so renumbering a task after adoption returns it to the full check.
- Adoption never fetches the source branch; the stale-view risk is the user's, and the write re-checks every refusal against the branch HEAD at that moment.
