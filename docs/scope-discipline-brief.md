# Scope discipline brief: keeping runs to the story's acceptance criteria

**Prepared:** 11 November 2026
**Source runs:** the 17 archived runs in `~/.factory/archive/`, chiefly `tm-TASK-7332-reworked` and `tm-TASK-8615-template-search-pagination` (repo `sainsburys-tech/task-management`) and `claude-factory-020`..`023`. Runs 020, 021 and 023 were squash-merged, so they have no per-commit evidence.
**Status:** settled in a grilling session (decisions D1–D17 below). Three feature texts, to be run in order. None is implemented yet.

## What happened

Factory runs add work the story never asked for and change code outside the story. After the TASK-7332 PR opened, about 3,700 lines were removed from it by hand: `96a332293` "Revert backend changes not needed for TASK-7332" (−1906), `c1026b4bd` "Remove extended one-off task fields and image upload" (−1447), `20d59d732` "Remove description preview and focus invalid schedule fields" (−294) and `cfb032ab7` (−44).

Extra work entered at every stage, most of it at the spec stage:

1. **Spec stage.** Fast mode auto-accepted each question's recommended answer, and the recommendations were the broader options. In TASK-7332 all six grill-with-docs answers and all four clarify answers were automatic. They added real push delivery (`c82b1e5ce` T031 `IAssignmentPushNotifier`, 21 files; `f8f204de0` T032), a new media category with 18-month retention (`f8bb1a587` T030), override handling at insert, reconcile and allocation (`ca4051643` T028, `7c2161d71` T029) and a 200-character training-name limit. Grill-with-docs answers were automatic in 4 of the 5 runs that had that stage. In TASK-8615 the spec added `pageNumber` and `excludedCount` log fields on its own. Runs 020 and 021 gained ADRs and CONTEXT.md terms their briefs never mention, and in 023 FR-011 added a DESIGN.md edit to a brief that said "Edit core only".
2. **Brief drift.** The TASK-7332 story said "all fields are required"; its brief reworded AC3 to "all in-scope fields required", which later forced change request B ("per AC3 ('all fields are required')"). The 023 feature text carried an "Acceptance: …" sentence that its brief dropped. The full story text survives only in `state.json` `feature`, and the specs cite the brief.
3. **Fix rounds.** TASK-7332 had 18 fix commits with 47 `Adjacent:` lines. `b0f4db8c3` declared 11 of them and changed backend authorization and the `bosun` dev, stg and prd configs; those backend changes were reverted after the ruling "no backend changes" (R6-Q5). In 021 a round-1 fix applied a cruise-only pr-open refusal to every run, and in 022 `6e8d1ac` added failure paths the plan did not declare. The next round caught both, at the cost of a round each.
4. **Implementation.** In TASK-8615, code-build repaired e2e tests that were already failing and unrelated to its task (`d27c0f978`, `1be0573e2`, both T013), and `a8d00f563` (T006) rewrote `docs/platform/patterns/api-pagination.md`, deleting cursor documentation the Contents endpoint still uses. In TASK-7332, `6ec522da6` (T009) reworked the scheduling controller (+270/−190 over 6 files) where the brief asked only to extract a summary list.
5. **Orchestrator commits.** Two `factory: resume TASK-7332-reworked` commits swept in whatever was staged: `28a020eea` deleted `frontend-ssc/pnpm-lock.yaml` (−7783), and `3e7408f4b` committed 594 lines of uncommitted work no task owned (six frontend files) and two `node_modules` symlinks.
6. **Review.** A keyword scan finds about 16 of 309 spec-conformance findings about added behaviour: 7 confirmed blocking, 5 advisory, 4 rejected. The blocking ones concerned undeclared tests and seams or behaviour a fix round added. Additions to the product shipped: TASK-8615's test repairs were rejected, and its focus change on every mount and its documentation rewrite were advisory.

## Why the factory lets it through

- No artifact keeps the story's acceptance criteria verbatim. `brief.md` is a paragraph plus decision bullets (`core/skills/factory/SKILL.md`, step 3), and when a story's ACs are listed the grill may reword them.
- Fast mode auto-accepts each question's recommended answer, and nothing asks the recommending role to prefer the narrower option.
- spec-conformance's "Unspecified" lens compares the diff with every spec artifact (`core/roles/spec-conformance.md:10-13`), so anything the spec, plan or tasks added counts as asked for. No reviewer reads the brief.
- The SpecKit tasks template seeds per-story "Add validation and error handling" and "Add logging" tasks and a "Polish & Cross-Cutting Concerns" phase (`.specify/templates/tasks-template.md:96-97`, `:150-158`); spec-builder does not override them.
- code-build has no file scope. The fixer's `Adjacent:` lines (`core/roles/fixer.md:30`) only declare a file, and the judge's `escalate` (`core/roles/review-judge.md:21`) re-runs the review without asking the user.
- Review rounds after the first review only the fix diff (`core/skills/factory/SKILL.md:145`), so nothing re-checks the whole change against the requirements after a fix round.
- An added-behaviour finding is rejected, made advisory or sent to the fixer. It never reaches the user as a keep-or-remove decision, and the approver screen (`core/skills/factory/SKILL.md:155`) has no AC checklist and no list of additions.
- `commit_worktree` stages only the declared paths but commits the whole index (`core/skills/factory/bin/factory_cli/commands.py:798`); `adopt` does the same (`adopt.py:390`), while `drop` passes a pathspec (`commands.py:706`).
- code-build treats every uncommitted change as its own interrupted task (`core/roles/code-build.md:26`).

## Decisions

The numbers match the grilling session's questions.

| # | Decision | Feature |
|---|---|---|
| D1 | Each run has a fixed, numbered acceptance-criteria list (`AC-1`..`AC-n`) in `brief.md`. The story's ACs are copied verbatim, and only the user's explicit decision changes the list. Everything downstream traces to it. | 2 |
| D2 | Additions beyond the ACs are always the user's decision. The judge lists added-behaviour findings separately and no fix round acts on them; a real defect inside an addition is still fixed. | 3 |
| D3 | spec-conformance moves to the deep tier and checks against the ACs. After the review loop, one final acceptance pass reads the whole diff cold, verified by the judge. No new role. | 3 |
| D4 | An unmet or partial AC at the final pass gets one extra fix round outside the two-round cap; if still unmet, it heads the approver screen. | 3 |
| D5 | Code-writing roles change only files their task or the plan names (others need `Adjacent:`), do no side work, and record what they notice in a "noticed, not done" list instead of doing it. | 3 |
| D6 | Spec-stage questions recommend the narrowest option that satisfies the ACs. A scope-growing option the user chooses becomes an AC amendment; declined options are listed at the approver. | 2 |
| D7 | Factory commits contain only the paths the run wrote. Uncommitted changes the run did not make are left alone and listed at the approver. | 1 |
| D8 | In an `Adjacent:` file the fixer makes only follow-through changes; anything more stops and asks the user. | 3 |
| D9 | Spec, plan and tasks cite the ACs they serve. Analyze rates an uncited item HIGH without lite-to-full escalation, and remediation cites or drops it. | 2 |
| D10 | The final pass labels each logical change traced, supporting or unplanned. Only unplanned changes need a decision. | 3 |
| D11 | The approver screen adds an AC checklist and lists of unplanned, supporting, declined, noticed and local changes, marked with emoji. | 3 |
| D12 | The approver offers Approve (keeps all unplanned additions), Remove `X…`, Request changes and Abort. | 3 |
| D13 | The PR body adds the AC checklist, AC amendments and kept additions. | 3 |
| D14 | Story ACs are copied verbatim with their labels; a story without ACs gets drafted ones the user confirms (a cruise override under cruise). No Jira fetch. | 2 |
| D15 | Adopted runs confirm ACs taken from `spec.md`; runs that predate AC lists fall back to `spec.md`. | 2, 3 |
| D16 | Run totals and the benchmark score count additions flagged, removed and kept, unmet ACs, analyze drops and declined scope. | 3 |
| D17 | Delivered as three focused `/factory` runs, in order. | — |

Considered and rejected:

- **Anchor on `spec.md`**: an agent writes the spec, so work it added would already count as planned.
- **A new `acceptance-auditor` role**: one more role to render and test across five harnesses, where the existing spec-conformance reviewer can do the final pass.
- **A keep-or-remove question before the approver**: cruise would answer it automatically, which breaks D2. The approver is never auto-answered.
- **Making every scope question wait for the user in fast mode**: more waits; narrow recommendations plus the final pass cover the same risk.
- **One run for everything**: its spec and plan would likely exceed analyze's word budgets.

## Running the features

- Run them in order from this repository, each as `/factory <feature text>` with its own PR. Feature 1 goes first because the commit sweep is damaging repositories now.
- The feature texts are self-contained. Commit this brief to the default branch first if you want the runs to read it, since each run's worktree starts from `origin/<default-branch>`.
- Until feature 2 ships, the grill does not copy acceptance criteria verbatim by itself. When the grill shows its closing summary, check that every AC below appears in `brief.md` unchanged.
- Feature 3 relies on feature 2's AC list and citations; on a run without them it falls back to `spec.md` (its criterion 10).
- Each run's grill chooses the chain.

## Feature 1: commit only what the run wrote

```text
Story: As a factory user, I want every factory commit to contain only the files the run wrote, so that a run never commits, deletes or absorbs work that is not its own.

Acceptance criteria
1. Every state CLI command that commits (checkpoint, resume, adopt and the other writer commands) stages its declared paths and commits with exactly that pathspec, as `drop` already does.
2. Given an unrelated staged change, such as a deleted pnpm-lock.yaml, when checkpoint, resume or adopt commits, then that change is not in the commit and is still staged afterwards.
3. code-build, design-to-code and fixer stage files by explicit path, never with `git add -A`, `git add .` or `git commit -a`.
4. code-build treats an uncommitted change as its interrupted work only when the task it resumes names that path; it neither commits nor discards any other uncommitted change.
5. At the approver, every path `git status --porcelain` reports in the worktree is listed under "📂 Uncommitted local changes the run didn't make"; the run neither commits nor discards them.

Out of scope: any other approver change.
```

## Feature 2: acceptance-criteria baseline and spec-stage scope

```text
Story: As a factory user, I want each run to fix the story's acceptance criteria at the start and trace every spec, plan and task item to them, so that the spec stages cannot add work the story never asked for.

Acceptance criteria
1. The grill ends by writing an "Acceptance criteria" section into brief.md, numbered AC-1..AC-n. When the feature description contains acceptance criteria, each is copied verbatim and in order, keeping the story's own label (for example "AC-3 (Jira AC3)"). The orchestrator never rewords an AC; an interpretation goes in a note under it.
2. When the feature description has no acceptance criteria, the grill drafts them, marks each "(drafted)" and shows them in its closing summary for the user to confirm. Under cruise, drafted ACs are confirmed with a cruise override and listed in the veto list's cruise group; verbatim ACs need no override.
3. After the grill, the AC list changes only through the user's explicit decision: a scope-growing answer the user chose, or a "Request changes" at the approver that adds or changes behaviour. Each change is recorded in brief.md as an AC amendment carrying its decision id.
4. Every question a spec stage asks (specify, clarify, grill-with-docs, plan, tasks) recommends the narrowest option that satisfies the ACs as written. Where an option would add behaviour, data, UI, integrations, configuration or documentation beyond the ACs, the recommendation is to leave it out, noted as a follow-up. Fast mode still auto-accepts recommendations.
5. Every scope-growing option not taken, whether the user declined it or an auto-accepted recommendation left it out, is recorded with its stage and question id and listed at the approver under "↩️ Declined scope".
6. In spec.md, every user story, functional requirement, success criterion, acceptance scenario and edge case cites the AC or ACs it serves, for example "(AC-2)".
7. In plan.md, each reason line for a new file, abstraction or dependency names the AC it serves: "<path or name> - <file | abstraction | dependency> - AC-n - <reason>".
8. In tasks.md, every task carries the ids of the ACs it serves (for example "T012 [US1] [AC-2] ..."); setup and foundational tasks cite the ACs they enable. SpecKit's per-story "Add logging" and "Add validation and error handling" tasks and its "Polish & Cross-Cutting Concerns" tasks appear only when they cite an AC.
9. Analyze reports every spec item, plan reason line or task that cites no AC as a HIGH finding, counted separately in its envelope. These findings must be resolved before implement but never trigger the lite-to-full escalation. Remediation adds the missing citation when the item serves an AC, or drops the item; each dropped item is listed at the approver under "↩️ Declined scope".
10. On an adopted run, the adoption grill proposes ACs copied verbatim from spec.md's acceptance scenarios and asks the user to confirm or edit them; the confirmed list is then fixed as for any run, with a cruise override under cruise.
11. A run whose brief.md has no AC list (started before this change) resumes with no new question and is not held to criteria 6-9; the approver says the run predates AC lists.

Out of scope: fetching a story from Jira by its key (the story text is pasted); the final acceptance pass and the approver's keep-or-remove options (feature 3).
```

## Feature 3: acceptance check, unplanned additions and code-writing limits

```text
Story: As a factory user, I want the code-writing roles to stay inside their tasks and a final check to compare the finished change with the acceptance criteria, so that before anything is published I can see which ACs are met and decide, item by item, whether to keep anything added beyond them.

Acceptance criteria
1. code-build, design-to-code (within its UI scope) and fixer change only files their task or the plan names. A commit that changes any other file carries one "Adjacent: <path> - <reason>" line per such file.
2. These roles make no change their task does not need: no refactor, rename, reformat, comment rewrite, dependency change or extra behaviour, even where it would improve the code.
3. Anything these roles notice but were not asked to do (a defect, a refactor idea, a missing edge case) goes into a new optional `noticed` list in their envelope and is never implemented.
4. In a file named only by an Adjacent line, the fixer changes only what the fix forces: call sites, imports, renamed references and the fixed code's own tests. A fix that needs more (a new helper, new behaviour, configuration, infrastructure or deployment files, or another layer of the system) stops and returns the proposed change, and the orchestrator asks the user as a protected question. Under cruise the recommended answer is taken: leave the finding unresolved and flag it at the approver.
5. spec-conformance runs at the deep tier and checks the diff against the run's AC list through the AC citations: missing and partial ACs, and behaviour no AC asks for.
6. The judge puts every verified added-behaviour finding into a new verdict list, `additions`. It never confirms one as blocking and no fix round acts on one. A real defect inside an addition (security, correctness, data integrity) is still rated and fixed like any other finding.
7. After the review loop ends (a pass or the two-round cap), the orchestrator runs one final acceptance pass: a fresh spec-conformance spawn over the whole base...HEAD diff, given only the AC list, the diff, the commit log and tasks.md, with no earlier verdicts or fix descriptions. The judge verifies its report and merges in every earlier round's `additions` entry still present in the code.
8. The final pass reports each AC as met, partial or unmet, with evidence (file and line, and test name).
9. The final pass groups the diff into one entry per logical change, giving its files, line ranges, commits and the stage it came from (spec, plan, tasks, implement or fix), and labels each entry:
   - traced: implements an AC through its task, as the task says;
   - supporting: needed for a traced change and nothing more: its tests; wiring, imports and call-site updates; schema, migration or configuration the AC needs; error handling, input validation and data integrity on the new code paths (ENG-17, ENG-25, ENG-26); documentation the repository's own conventions (CLAUDE.md, AGENTS.md, the constitution) require;
   - unplanned: everything else, including new behaviour, options, fields, UI or endpoints; refactors, renames or reformatting a traced change did not force; rewrites of existing documentation; repairs of tests that were already failing; dependency, infrastructure or deployment changes that were not needed; ADR or CONTEXT entries the repository's conventions do not require; and logging no AC asks for.
10. A run without an AC list uses spec.md's acceptance scenarios and functional requirements as the final pass's baseline, and the approver says so.
11. When the final pass finds an unmet or partial AC, the orchestrator runs one fix round aimed only at those ACs, outside the two-round review cap, followed by verify, a review round and the final pass again. An AC still unmet after that heads the approver screen marked ❌.
12. The approver screen shows, above its current content and in this order: the AC checklist (✅ met, ⚠️ partial, ❌ unmet, each with its verbatim text and evidence); 🔴 unplanned additions numbered X1..Xn (what each does, its files and commits, the stage it came from, the agent's stated reason, what depends on it, and the final pass's keep-or-remove recommendation); 🟡 supporting changes, one line each; ↩️ declined scope; 💡 noticed, not done; 📂 uncommitted local changes the run didn't make. The first two sections always appear, saying "none" when empty; the others appear only when they have entries. Traced changes are not listed one by one.
13. The approver's options are "Approve (keeps all 🔴)", "Remove X…", "Request changes" and "Abort"; Remove and Request changes can be combined in one reply. Remove runs a user-changes fix round that removes exactly the named additions with their tests and documentation, then verify, review and the final pass, and returns to the approver. Kept additions are recorded as approver decisions and do not become ACs. Under cruise the approver still waits for the user.
14. The PR body adds the AC checklist (verbatim text and status), the AC amendments made during the run with their decision ids, and each kept 🔴 addition with its reason. It does not include noticed-not-done items or declined scope.
15. Run totals and the benchmark score report 🔴 additions flagged, removed and kept; partial and unmet ACs at the final pass; items dropped at analyze; and declined scope options.

Out of scope: a new role; a keep-or-remove question before the approver; removing additions automatically; a new retro signal kind.
```
