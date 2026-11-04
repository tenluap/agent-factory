# Brief: assign factory PRs to the signed-in GitHub account

Source plan: `docs/superpowers/plans/2026-11-03-factory-pr-self-assignment-plan.md`.

Every PR a factory run opens should be assigned to the GitHub CLI account that opened it, with no new question to the user. Step 9 (PR) of the factory skill adds `--assignee @me` to its single `gh pr create` call. Publication becomes idempotent: the branch's existing PR is looked up before creating one and again after any creation error, so a retry or a resumed `pr` stage reuses the PR instead of opening a duplicate. When the PR exists but the account is not among its assignees, the run keeps the URL, continues, and reports the assignment problem separately in its final notice.

Chain: **lite** (settled under cruise).

## Decisions

- Add `--assignee @me` to the single `gh pr create` call in step 9; no separate `gh pr edit` call. The human Approve gate before push/PR is unchanged. The run never asks for a GitHub username.
- Idempotent creation: before `gh pr create`, and again after any non-zero exit, look up the branch's PR with `gh pr view <branch> --json url,assignees`. An existing PR is reused (its URL recorded via `set-status pr-open`), never recreated.
- Assignment failure is non-blocking: when the PR exists but the authenticated account is not among its assignees, keep the URL, continue the run, and report the assignment problem separately in the final notice. No new state schema field and no new issue kind.
- Resume of the `pr` stage (state.md, "Resume") follows the same lookup-then-create path, so interrupted publication never creates a duplicate PR.
- Automated verification: a text-contract test under `tools/tests` asserting step 9 carries `--assignee @me`, the existing-PR lookup, and the separate assignment report. The disposable-GitHub-repository live check is written as a manual runbook in the spec's `quickstart.md` for the user; agents do not create GitHub repositories (outward-facing action).
- Edit core only (`core/skills/factory/SKILL.md` step 9, `core/skills/factory/references/state.md` Resume `pr`), then re-render `dist/` for all five harnesses. No ADR, no new CONTEXT.md term.
- Build: render the five harnesses and `bash -n install.sh`; test: `python3 -m unittest discover -s tools` (README CI line).
