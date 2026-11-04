# Remediation 1 (analyze-1)

- U1: contracts/pr-publication.md item 3 sub-step 4, data-model.md "Lookup outcome" and tasks.md T005 Implement now say the post-creation lookup uses assignees only on "found"; none or failed keeps the `gh pr create` URL, counts as an assignment problem, and never creates, retries or halts. The table's create/halt actions are limited to sub-steps 1 and 3.
- A1: `lookup-after-error` restated as one section line containing the four literals `gh pr create`, `error`, `Branch PR lookup`, `retry` (contract table, T003 Red); T003 Implement notes sub-step 3's line carries all four. Contract states markers are case-sensitive literal substrings.
- I1: research.md R6, plan.md "New code reasons" and spec.md Assumptions corrected: `tools/tests/test_render_models.py` already reads core role text for harness neutrality/rendering; the publication contract gets its own module for its own injected-failure fixtures.
- U2: `no-ask` defined as no whole-word `\bASK\b` match in the section (contract table, T002 Red).
- U3: `assignment-report` anchored to the item 8 line (`^\s*8\.\s`) in the contract table and T005 Red, matching the plan's declared failure path. Seam and failure-path names unchanged, so the Q1 confirmation stays current.
- G1: quickstart.md adds step 5 stating the after-error path is covered only by the `lookup-after-error` text contract, with an optional user-run step forcing a `gh pr create` error; cleanup renumbered to step 6.
- I2: spec.md Clarifications Q2 notes the lookup command follows research R2 (`gh pr list --head <branch> --state open`) instead of the grill answer's `gh pr view <branch>`, intent unchanged.
