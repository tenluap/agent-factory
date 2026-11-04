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

Agents never run this section and never create GitHub repositories. Behaviour under test: [contracts/pr-publication.md](contracts/pr-publication.md).

Prerequisites: `gh auth status` shows the account you expect (call it `<you>`); `/factory` installed from this branch.

1. **Disposable repository**: `gh repo create <you>/factory-pr-assign-check --private --clone --add-readme`, then `cd factory-pr-assign-check`.
2. **New PR is self-assigned (SC-001, SC-004)**: run `/factory` on a one-line feature (for example "add a CHANGELOG.md with one line"), approve at the approver gate. Confirm `gh pr list --head <branch> --json assignees --jq '.[0].assignees[].login'` prints `<you>`, and no question asked for a GitHub username at any point.
3. **Resume reuses the PR (SC-002)**: start a second run with `--stop-at pr` and Approve; the run pauses before publishing. Push the branch and open its PR by hand with `gh pr create --head <branch> --fill --assignee @me`, then `/factory resume <branch>`. Confirm `gh pr list --head <branch> --state all --json number --jq length` prints `1` and the run's final notice shows that PR's URL.
4. **Unassigned PR is reported (SC-003)**: repeat step 3 with a third run, but open the PR without `--assignee`. Confirm the run finishes with the PR recorded, still exactly one PR for the branch, and the final notice names the assignment problem on its own line, separate from the PR link.
5. **Clean up**: `gh repo delete <you>/factory-pr-assign-check --yes` (needs the `delete_repo` scope: `gh auth refresh -s delete_repo`).
