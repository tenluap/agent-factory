# Data model: Assign factory PRs to the signed-in GitHub account

No persisted data changes: `state.json` schema, status, issue-kind and history-event vocabularies are unchanged (FR-009). The entities below exist only for the duration of step 9.

## Branch PR

The open pull request whose head is the run's branch, read from `gh pr list --head <branch> --state open --json url,assignees`.

- `url` (string): recorded through the existing `set-status pr-open --pr-url <url>`.
- `assignees` (list of `{ login }`): read for the assignment check only.
- Rule: only an open PR is a Branch PR; closed or merged PRs are ignored and a new PR is created.

## Lookup outcome

Each Branch PR lookup yields exactly one of the outcomes below. The actions apply to the lookups before creation and after a creation error (contract item 3 sub-steps 1 and 3). The lookup after a successful creation (sub-step 4) only reads assignees: found supplies them; none or failed keeps the URL `gh pr create` printed and counts as an assignment problem, and never creates, retries or halts.

| Outcome | Signal | Step 9 action |
|---------|--------|---------------|
| found | exit 0, non-empty list | reuse first entry; no creation |
| none | exit 0, `[]` | create (or retry once after an error) |
| failed | non-zero exit | halt with the lookup error; never create |

## Signed-in account

`login` from `gh api user --jq .login`. Never supplied by or asked of the user.

## Assignment problem

An in-turn note, set when the signed-in login is not among the Branch PR's assignees or when the login or assignees could not be read. Shown as its own item in step 9 item 8's `NOTIFY`, separate from the PR URL. Never written to `state.json`.
