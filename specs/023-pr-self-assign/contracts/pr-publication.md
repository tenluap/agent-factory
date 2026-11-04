# Contract: PR publication (SKILL.md step 9, state.md Resume `pr`)

## Behaviour

Step 9 keeps its item numbers; only items 3, 4 and 8 change.

- **Item 3 - publish (lookup-then-create)**:
  1. Branch PR lookup: `gh pr list --head <branch> --state open --json url,assignees`. Found: reuse its `url`, skip creation. Failed: halt with the lookup error as halt reason.
  2. None: `gh pr create --base <default-branch> --head <branch> --title "<title>" --body-file <file> --assignee @me`, ready for review.
  3. After a `gh pr create` error, repeat the Branch PR lookup before any retry. Found: reuse. Failed: halt with the lookup error. None: retry creation once; after a second error and a lookup still finding none, halt with the creation error. No URL is recorded on any halt.
  4. After a successful creation, repeat the Branch PR lookup once to read its assignees; a failed lookup here keeps the URL `gh pr create` printed and counts as an assignment problem.
- **Item 4 - record and check**: `set-status pr-open --pr-url <url>`. Read the signed-in login with `gh api user --jq .login`. When it is not among the Branch PR's assignees, or either read failed, note an assignment problem for item 8. Continue; never halt, never `ASK`.
- **Item 8 - final notice**: the `NOTIFY` names any assignment problem as its own item, separate from `pr_url`.
- **state.md Resume `pr`**: restart SKILL.md step 9 from item 1; its Branch PR lookup reuses an existing open PR, so resume never opens a duplicate.

## Text-contract elements (tested by `tools/tests/test_pr_publication.py`)

`pr_contract_gaps(skill_text, state_text)` returns the names of missing elements, in this order. "Section" is the text from `## 9. PR` up to the next `## ` heading of SKILL.md.

| Element | Present when |
|---------|--------------|
| `self-assign` | a section line contains `gh pr create` and `--assignee @me` |
| `lookup-before-create` | the section contains `gh pr list --head <branch> --state open --json url,assignees` before its first `gh pr create` |
| `lookup-after-error` | a section line contains `gh pr create` error wording (`error`) and `Branch PR lookup` and `retry` |
| `assignment-report` | a section line matching `^\s*\d+\.\s` contains `NOTIFY` and `assignment problem` |
| `no-ask` | the section contains no `ASK` verb |
| `resume-rule` | the state.md Resume line starting `` - `pr`: `` contains `step 9` and `Branch PR lookup` and not `gh pr view` |

Injected failure paths: for each element, a copy of the real core text with that element's marker removed (or, for `no-ask`, an `ASK` line inserted into the section) makes `pr_contract_gaps` return exactly that element's name.
