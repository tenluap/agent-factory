# Review gaps brief: findings the factory review missed

**Prepared:** 4 November 2026
**Source run:** `TASK-8615-template-search-pagination` (repo `sainsburys-tech/task-management`, PR #1022), archived at `~/.factory/archive/tm-TASK-8615-template-search-pagination`.
**Status:** improvement backlog. Each item below is a candidate change to the factory core; none is implemented yet.

## What happened

The run passed four review rounds (security, code-standards, spec-conformance, ui-reviewer and ux-reviewer, then review-judge) and the approver approved. Within minutes of the PR opening, Copilot's PR reviewer raised two valid findings that no factory reviewer had reported:

1. **Pagination controls are buttons, not links (medium).** `PaginatedTemplateResults.tsx:41` changes the URL (`?templatePage=N`) through Fable Pagination's `onChange`, so the controls are announced as actions and cannot be opened in a new tab. Fable supports link mode through `createHref` with `linkAs={Link}`.
2. **The documented e2e command is wrong (low).** `quickstart.md`, `tasks.md` and `plan.md` documented `SSC_SCHEDULING_E2E=1 pnpm test:e2e`, which uses the base Playwright config and starts neither the fixture API nor the app. The working command needs `--config ./playwright-e2e/scheduling.config.ts`. The orchestrator used the correct config in every verify run, and the round-3 spec-conformance reviewer recommended the wrong command, which the judge copied into its verdict.

After the PR opened, SonarQube also failed the backend Quality Gate with three new issues in `GetTemplatesQuery.cs`:

3. **Synchronous reads in an async handler (medium, twice).** The new `ExecuteAsync` used `results.Read<TaskTemplate>()` and `results.ReadSingle<int>()` instead of awaiting `ReadAsync` and `ReadSingleAsync`. Other handlers in the repo already await the async readers.
4. **`BuildSqlQuery` can be static (info).** The refactor removed the base class, so `BuildSqlQuery` stopped being an override and no longer used instance data.

A related gap from the same run: Playwright was not part of `commands.test`, so an 18-test regression introduced by a merge of the default branch was found only because the orchestrator ran the e2e suite by hand.

## Why the review missed them

- No reviewer role says that a control which changes the URL or route must be a link. The check depended on the model thinking of it.
- `ui-reviewer`, `ux-reviewer` and `spec-conformance` run at the `standard` tier (Haiku on Claude Code).
- Delta reviews look only at changed lines. The `onChange` line sat in the same component as the round-3 fix but was unchanged, so it was out of scope.
- The orchestrator's delta-review prompts named the fix ("isCompact removed"), which anchored every reviewer on that one finding.
- No role compares the commands written in the spec artifacts with the commands the run actually executed.
- The judge does not check a reviewer's proposed `fix` text, so a wrong command passed straight into the verdict.
- `commands` has no slot for an e2e command, so the orchestrator's verify gate does not cover it.
- The repo's CI quality gates (SonarQube) run only in CI. The local build has no matching analyzers, so build and tests stayed green, and no role runs the CI analyzers before the PR.
- code-standards reviews against written conventions only. The async-read convention exists only in code, and the role does not compare new code with similar existing code.

## Proposed changes

| # | Change | Where |
|---|---|---|
| 1 | Add a navigation-semantics check: any control that changes the URL or route must be a link (`<a>`, framework `Link`, or the design system's link mode), support open-in-new-tab, and be announced as a link. A button with an `onChange` that navigates is a finding. | `core/roles/ui-reviewer.md`, `core/roles/ux-reviewer.md` |
| 2 | Move `ui-reviewer`, `ux-reviewer` and `spec-conformance` from `standard` to `deep`. | `tier:` frontmatter in `core/roles/ui-reviewer.md`, `ux-reviewer.md` and `spec-conformance.md` (rendered into `roles/tiers.json` by `tools/render.py`) |
| 3 | In a delta review, also review unchanged code in every file the fix diff touches, not only the changed lines. | `core/skills/factory/references/findings.md`, "Reviewing" |
| 4 | The orchestrator passes only `delta_base` and the previous verdict path to delta reviewers; it never describes the fix or names the finding it addresses. | `core/skills/factory/SKILL.md`, step 7 |
| 5 | spec-conformance checks every command in `quickstart.md`, `plan.md` and `tasks.md` against the commands recorded in the run's verify history, including config flags. A mismatch is a finding. | `core/roles/spec-conformance.md` |
| 6 | Add `commands.e2e` to preflight and to the orchestrator's verify gate, so end-to-end suites are run and recorded like build and test. | `core/skills/factory/SKILL.md`, steps 1 and 6; `references/state.md` |
| 7 | The judge checks each reviewer's proposed fix before putting it in the verdict; a fix that names a command must match a recorded command. | `core/roles/review-judge.md` |
| 8 | Before the approver step, run a cold-read review with no hints: either an external PR reviewer on a draft PR, or a fresh deep-tier reviewer given only the diff and the spec. Fold its findings into the last round. Overlaps with spec 020 (post-PR feedback), which only captures feedback after the PR is published. | `core/skills/factory/SKILL.md`, between steps 7 and 8 |
| 9 | Preflight detects the repo's CI quality gates (for example SonarQube or lint workflows) and records how to run each one locally, such as a SonarScanner run or a build with `SonarAnalyzer.CSharp`. The verify gate runs them. A gate with no local equivalent is recorded as such and disclosed, never silently skipped. | `core/skills/factory/SKILL.md`, steps 1 and 6; `references/state.md` |
| 10 | code-standards finds two or three existing implementations of the same kind as each new one (for example other Dapper multi-read handlers) and reports differences. This covers conventions that are followed in code but not documented. | `core/roles/code-standards.md` |

## Feature text

Ready to submit from this repository as `/factory <feature>`:

> Close the review gaps found in run TASK-8615 (see docs/review-gaps-brief.md): add a navigation-semantics check to the UI and UX reviewers; move ui-reviewer, ux-reviewer and spec-conformance to the deep tier; widen delta reviews to unchanged code in touched files; stop the orchestrator describing fixes to delta reviewers; have spec-conformance compare documented commands with recorded verify commands; add commands.e2e to preflight and verify; have the judge check reviewers' proposed fixes; add a hint-free cold-read review before the approver; run the repo's CI quality gates (such as SonarQube) locally in verify; and have code-standards compare new code with similar existing implementations.
