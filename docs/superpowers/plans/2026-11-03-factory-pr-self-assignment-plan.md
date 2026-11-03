# Assign factory PRs to the signed-in GitHub account

**Proposed workflow change.** Assign each newly opened factory PR to the authenticated GitHub CLI account that opens it.

## Tasks

- [ ] Add `--assignee @me` to the PR creation step. Keep the existing human approval before the branch is pushed and the PR is opened.
- [ ] When creation or assignment reports an error, look up the branch’s existing PR before retrying. If a PR exists but assignment failed, preserve its URL and report the assignment problem separately.
- [ ] Verify with a disposable GitHub repository. Check the actual assignee and confirm that resuming interrupted publication does not create a duplicate PR.

## Acceptance

The newly created PR lists the authenticated GitHub CLI account as its assignee. A failed assignment is visible, and a retry reuses an existing PR. The factory approval flow does not ask for a GitHub username.

[GitHub CLI PR creation options](https://cli.github.com/manual/gh_pr_create)
