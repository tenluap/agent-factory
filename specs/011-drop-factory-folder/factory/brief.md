# Brief: drop the factory folder at run end

When a factory run reaches the end of its flow and its PR is open, the factory removes the run-artifact folder `specs/<branch>/factory/` from the branch with one final commit, so the PR's file diff no longer contains run state, briefs, analyze reports or reviews. Before removing it, the factory archives the whole folder outside the repository so nothing is lost.

## Decisions

- Mechanism: a single final removal commit (`git rm -r specs/<branch>/factory`). State stays committed throughout the run, so checkpoints, resume and discovery are unchanged. No history rewrite, no gitignore/never-commit redesign.
- Timing: SKILL.md step 9 becomes push -> `gh pr create` -> `factory set-status pr-open --pr-url <url>` (final state + improvement backlog export, unchanged) -> `factory drop` -> push. The PR shows the folder only for the seconds before the second push.
- New CLI write command `factory drop` (single-writer rule, FR-001): refuses unless the run's status is `pr-open`; copies the whole `specs/<branch>/factory/` folder to `${FACTORY_HOME:-~/.factory}/archive/<repo-name>-<branch>/`; verifies the copy; then `git rm -r` the folder and commits `factory: drop run artifacts`. Prints JSON with the archive path.
- Archive collision: when the archive target already exists, `factory drop` refuses with a clear message and never overwrites.
- Only `pr-open` runs are dropped. Aborted runs keep their folder and worktree.
- No opt-out flag or config setting: always drop.
- Existing `specs/007..010/*/factory/` folders on main are left as they are (future runs only).
- The attached opencode `adapter.json` (models) is context only and out of scope; uncommitted adapter edits on main are untouched.
- Docs: update SKILL.md step 9, references/state.md (Location and CLI), README; re-render `dist/` for all harnesses; unit tests in `tools/tests/`.
- Chain: lite, fast mode on.
