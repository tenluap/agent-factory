# Quickstart: Assign factory PRs to the signed-in GitHub account

## Automated checks (agents and CI)

From the repository root:

```bash
python3 -m unittest tools.tests.test_pr_publication -v   # text contract (FR-012)
python3 -m unittest discover -s tools                     # whole suite
export FACTORY_HOME="$(mktemp -d)"; for h in claude-code opencode codex copilot zcode; do python3 tools/render.py "$h" || exit 1; done; bash -n install.sh
test -z "$(git ls-files -- dist/)"                        # dist stays untracked
```

Expected: all tests pass, every harness renders, no tracked `dist/` file.

## Manual runbook: live check (user only, FR-013)

Agents never run this section and never create GitHub repositories. Behaviour under test: [contracts/pr-publication.md](contracts/pr-publication.md) and SKILL.md step 9 item 3 (sub-steps 1-4), item 4 and item 8, with state.md's Resume `pr` rule.

Prerequisites: `gh auth status` shows the account you expect (call it `<you>`); `/factory` installed from this branch.

1. **Disposable repository**: `gh repo create <you>/factory-pr-assign-check --private --clone --add-readme`, then `cd factory-pr-assign-check`.
2. **New PR is self-assigned (SC-001, SC-004)**: run `/factory` on a one-line feature (for example "add a CHANGELOG.md with one line"), approve at the approver gate. Confirm `gh pr list --head <branch> --json assignees --jq '.[0].assignees[].login'` prints `<you>`, no question asked for a GitHub username at any point, and the final notice names no assignment problem (step 9 item 8).
3. **Resume reuses the PR (SC-002)**: start a second run with `--stop-at pr` and Approve; the run pauses before publishing. Push the branch and open its PR by hand with `gh pr create --head <branch> --fill --assignee @me`, then `/factory resume <branch>`. Resume restarts step 9 from item 1, and its Branch PR lookup (item 3, sub-step 1) reuses the open PR instead of creating another. Confirm `gh pr list --head <branch> --state all --json number --jq length` prints `1` and the run's final notice shows that PR's URL.
4. **Unassigned PR is reported (SC-003)**: repeat step 3 with a third run, but open the PR without `--assignee`. Confirm the run finishes with the PR recorded, still exactly one PR for the branch, and the final notice names the assignment problem (item 8) on its own line, separate from the PR link.
5. **After-error path (optional, FR-005/FR-006)**: steps 3 and 4 exercise the item 3 sub-step 1 lookup on resume. The lookup after a `gh pr create` error (item 3 sub-step 3) is covered only by the text contract (`lookup-after-error`). To exercise it live, edit the installed step 9 item 3 sub-step 2 `gh pr create` line to add a second, invalid `--assignee <nonexistent-login>`, run a fourth feature to the PR step, and confirm `gh pr list --head <branch> --state all --json number --jq length` prints at most `1` and the run either reuses that PR or halts with the creation error and no recorded URL. Reinstall from this branch afterwards.
6. **Clean up**: `gh repo delete <you>/factory-pr-assign-check --yes` (needs the `delete_repo` scope: `gh auth refresh -s delete_repo`).
