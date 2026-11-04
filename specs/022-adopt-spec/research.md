# Research: Adopt a spec started outside factory

Decisions behind [plan.md](plan.md). Each records the choice, why, and what was rejected. Settled answers: grill Q1-Q9, clarify Q1-Q4, grill-with-docs Q1-Q4 (spec.md "Clarifications"); ADR 0017.

## D1 Ordering

- **Decision**: `/factory adopt <src>` runs `factory adopt <src> --dry-run` first, before any pending file exists. Only a clean report proceeds to pending creation, preflight (whose default-branch fetch still runs, clarify Q3), the adoption grill and the write.
- **Rationale**: a refusal creates nothing anywhere (FR-007, SC-002).
- **Rejected**: dry-run after preflight (leaves a pending file per refused source).

## D2 Source resolution

One function shared by dry-run and write; first match wins:

1. `<src>` names a local branch → shape `branch`.
2. Else `refs/remotes/origin/<src>` exists → shape `remote-branch`.
3. Else `<src>` (with or without `specs/`) names a spec dir: a local branch named after it → `branch`; else the dir exists on `base` → `default-branch`, branch = dir name; else the dir exists on local `refs/heads/<default>` only → refusal "spec dir is on local `<default>` but not on `<base>`; push it or create its branch first" (clarify Q2); else no match, exit 1.

Before step 1, a `<src>` failing `git check-ref-format --branch` (for example `../x`, `a..b`) is no match: exit 1, nothing read or written. Spec-dir candidates in step 3 are local branch names plus `specs/*/` names on `base` and on local `<default>`; `<src>` matches one equal to it or ending in `-<src>` (`find_matches`'s rule).

Spec dir on a branch: `specs/<branch>/` when present on the ref, else the single `specs/*/` directory the branch adds over `base` (`git diff --name-only <base>...<ref> -- specs/`), recorded unchanged (US3-3). Several candidates (spec dirs, or a name matching several dirs by `find_matches`'s `NNN-` suffix rule) → exit 3 listing them. A branch present locally and on `origin` resolves to the local branch. Artifacts and `[NEEDS CLARIFICATION]` lines are read from the ref (`git ls-tree`, `git show <ref>:<path>`), never a working tree.

- **Rejected**: resolving from the main checkout's files (misses branch-only specs; reads dirty content).

## D3 No fetch

`factory adopt` never runs `fetch`, `pull` or `push` and never refreshes the source branch (clarify Q3). The dry-run, run before preflight, takes `base` from `refs/remotes/origin/HEAD` (else `origin/main` when present, else `main`) and prints it; the write uses the pending run's `default_branch` and `base` from preflight and is authoritative.

## D4 Pending identity (clarify Q1)

- **Decision**: the adoption's pending file is `${FACTORY_HOME}/pending/<repo-name>-adopt-<branch>.json`; the dry-run report prints this name as `pending`. The orchestrator reuses it on retry (keeping relay and decisions) and replaces it when it has ended (`aborted`). Any other readable pending file of the repo refuses dry-run and write (FR-007), naming the file with a hint to resume or prune it.
- **Rationale**: `factory runs` shows pending runs with `branch: null`, and every pending-state command selects through `resolve_target`, which exits 3 when the repo has several pending runs. A fixed name plus the sole-pending rule keeps both working; `resume <branch>` already matches the name by its `-<branch>` suffix, so an interrupted adoption grill resumes as today.
- **Rejected**: selecting by stored `branch` field (invisible to `runs`; still breaks `resolve_target`).

## D5 Refusal order

First reason named in `refusal`; every dirty path listed even when another reason also applies: no match / ambiguous (exit 3) / local-only default-branch dir; other pending file; dirty paths (`git status --porcelain` of the main checkout limited to the spec dir, plus full status of any checkout holding the source branch); spec dir has `factory/state.json` (names `resume <branch>`); no `spec.md`; branch checked out in a checkout (names it, hint to switch away); target worktree path exists.

## D6 Entry stage and chain

`tasks.md` → `analyze` (any checkbox state); else `plan.md` → `tasks`; else `plan`. `--stage` accepts `specify|plan|tasks|analyze`; anything else exits 5 in `cli.py` before any read. The adoption grill recommends the `full` chain when the chosen stage is `tasks` or `analyze` (grill-with-docs Q3).

## D7 Write steps

Holding the pending run's lock (`lock.acquire` on the pending path; a live foreign lock exits 1) for the whole write:

1. Load `pending/<repo-name>-adopt-<branch>.json` (branch from the re-resolved source). Missing → exit 1 "no pending adoption `<name>`; run `/factory adopt <src>`". Status `aborted` or `pr-open` → exit 1, ended.
2. Re-run the inspection against the pending `base`; any refusal (including another pending file) exits 1, nothing written. This also re-reads the branch HEAD, so a branch that moved since the dry-run is adopted at its new HEAD (spec edge case).
3. `git worktree add <path> <branch>` (`branch`), `git worktree add --track -b <branch> <path> origin/<branch>` (`remote-branch`), or `git worktree add -b <branch> <path> <base>` (`default-branch`).
4. Record `base_commit` = `git rev-parse <branch>` in the new worktree; write `<worktree>/<spec_dir>/factory/state.json` from the pending state through `state.write_state` (`worktree`, `branch`, `spec_dir`, `stage` = chosen, `status: running`, the `adopted` block, one `adopted` history entry, [data-model.md](data-model.md)); copy `<pending>.brief.md` → `brief.md` and `<pending>.profile.md` → `profile.md` when present.
5. `commit_worktree(worktree, "factory: adopt <branch>", spec_dir=<spec_dir>/factory)`, staging only that folder (FR-014).
6. After the commit succeeds, delete the pending JSON, brief and profile, as step 4 of a new run does.

Any failure in 3-5 (a `CLIError` from `git`, a `StateError`, an `OSError`): `git worktree remove --force <path>`, `git branch -D <branch>` only when step 3 created it, pending untouched, exit 1 with the cause (FR-013). Steps 1-2 refuse before anything exists.

## D8 Declined adoption

`set-status aborted` on the pending run, as a declined new run; nothing reached the repository; `prune` already lists aborted pending files.

## D9 Resume hint

`one_run` gains an optional `hint` appended to its `no run '<name>' in <repo>` message; only `cmd_resume` passes `use adopt <branch|spec_dir> for a spec factory did not start`. The CLI names its own verb; the skill names the harness invocation (constitution II).

## D10 Pre-adoption boundary

- **Commits and checked tasks (FR-019)**: SKILL.md step 7 passes `adopted_base` (= `adopted.base_commit`) to the reviewers and `review-judge` when present. Code-standards applies the ENG-3 commit-unit check to `<adopted_base>..HEAD` only. Spec-conformance checks `Red:` lines (ENG-2) on `<adopted_base>..HEAD` only and skips the ENG-1 one-passing-test-and-implementation-commit check for tasks checked in `git show <adopted_base>:<spec_dir>/tasks.md`. Both list `<base>..<adopted_base>` commits and those tasks as pre-adoption; the judge never confirms an ENG-1, ENG-2 or ENG-3 commit-evidence finding against them. All reviewers still review `<base>...HEAD` in full (user answer Q5, widening grill Q9).
- **Tasks (FR-025)**: the spec-builder's `analyze` stage reads `git show <base_commit>:<spec_dir>/tasks.md`, takes the IDs of tasks checked there, excludes those IDs from the blocking test-scope check and lists them under "Pre-adoption tasks". A renumbered or new task gets the full check.
- **Artifacts (FR-024)**: when state has `adopted`, the spec-builder's `specify`, `plan` and `tasks` stages edit an existing `spec.md`, `plan.md` or `tasks.md` in place.
- **Rejected**: a CLI helper computing pre-adoption task IDs (one `git show` in agent prose suffices; constitution V).

## D11 Disclosure

`show`'s digest passes small fields verbatim, so `adopted` reaches the approver and retro unchanged. The approver line and retro summary state source, shape and chosen stage (FR-020).
