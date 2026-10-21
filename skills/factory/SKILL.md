---
name: factory
description: Software factory orchestrator. Takes a feature from grilling through SpecKit, implementation, parallel reviews and your approval to a PR. Resumable.
disable-model-invocation: true
argument-hint: "[feature description | resume <branch>]"
---

You are the **orchestrator** of a factory run. You run the loop below, spawn every agent, own the run's state, and are the only one who talks to the user. Agents never talk to the user; their questions reach the user through you (the **relay**).

`<F>` below means this skill's base directory.

References, read when a step points at them:
- [`references/state.md`](references/state.md): `state.json` schema, checkpoints, discovery, resume.
- [`references/protocol.md`](references/protocol.md): the envelope every agent returns, and the relay.
- [`references/findings.md`](references/findings.md): reviewer findings and judge verdict shapes.

## 0. Route

- `$ARGUMENTS` empty: list unfinished runs (state.md, "Discovery"). Offer each as a resume option plus "start a new run". No runs: ask for the feature.
- `resume <branch>`: resume that run (state.md, "Resume").
- Anything else: the feature description of a new run. Go to step 1.

## 1. Preflight

1. Confirm the current directory is inside a git repo. Record `repo` as the main checkout (the parent of `git rev-parse --path-format=absolute --git-common-dir`, so a run started from a worktree still anchors on the main checkout), the default branch (`gh repo view --json defaultBranchRef -q .defaultBranchRef.name`, else `main`), and `base` = `origin/<default-branch>` after `git -C <repo> fetch origin <default-branch>`.
2. `.specify/` missing: ask once to run `specify init --here --ai claude`, then follow the resolved `speckit-constitution` SKILL.md with the user. Declined: stop.
3. Resolve every skill the run needs to an absolute `SKILL.md` path, first match wins: `<repo>/.claude/skills/<name>/`, `~/.claude/skills/<name>/`, then `~/.claude/plugins/**/skills/<name>/`. Needed: `speckit-specify`, `speckit-clarify`, `speckit-plan`, `speckit-tasks`, `speckit-analyze`, `speckit-implement`, `grilling`, `domain-modeling`, `pr`. A missing one: stop and name it. `impeccable` is resolved later, only on a UI diff.
4. Load the deferred tools `SendMessage` and `PushNotification` with one `ToolSearch` (`select:SendMessage,PushNotification`). PushNotification unavailable: skip notifications for the run.
5. Read the repo's CLAUDE.md / AGENTS.md for build and test commands; record them as `commands.build` / `commands.test`. None documented: detect from the project files and confirm with the user once.

Done when every skill path and both commands are recorded in the pending state (state.md, "Pending state").

## 2. Grill

Invoke the `grilling` skill on the feature description, here, with the user. Done when the user confirms shared understanding. Write the settled design as `brief.md` beside the pending state: the feature in one paragraph, then every decision as a bullet. Nothing is written to the repo in this step. Checkpoint the pending state with `stage: worktree`.

## 3. Worktree

1. Pick a 2-4 word kebab `short-name`. Run from `repo`: `bash .specify/extensions/git/scripts/bash/create-new-feature.sh --json --dry-run --short-name <short-name> "<feature>"` and take `BRANCH_NAME`. No git extension: use `NNN-<short-name>` with the next free number across `specs/` and local branches.
2. `git -C <repo> worktree add <repo>/../<repo-name>-factory/<branch> -b <branch> <base>`. This absolute path is `worktree`.
3. Create `<worktree>/specs/<branch>/factory/`, move `brief.md` into it, write `state.json` from the pending state, delete the pending file, and commit `factory: start <branch>`.

From here every Bash command runs as `cd <worktree> && ...`, and every agent gets `worktree` in its prompt.

## 4. Spec

Spawn `factory-spec-builder` with: `worktree`, `branch`, `spec_dir` (`specs/<branch>`), the brief path, the resolved skill paths, and the first stage. Send `analyze` and `remediate` with the pass number `analyze.pass`. Record its agent id in state. Then drive it one stage per turn with `SendMessage`. Each turn ends with an envelope (protocol.md):

- `needs_input`: run the relay (protocol.md), then send the answers back.
- `done`: checkpoint (state.md), then send the next stage.
- `failed`: failure policy (below).

Stage order: `specify`, `clarify`, `grill-with-docs`, `plan`, `tasks`, `analyze`. After `analyze`, read the severity counts in the envelope:

- Any CRITICAL or HIGH, and `analyze.loops < 2`: send `remediate` (fix every finding at every severity; findings that need a user decision come back as `pending_clarify`, stored in state). Then increment `analyze.loops` and `analyze.pass`, and re-run `clarify` through `analyze`, passing the latest analyze report, remediation log and `pending_clarify` to `clarify`, and the report and log to `plan` and `tasks`.
- Any CRITICAL or HIGH, and `analyze.loops == 2`: halt. Ask the user: proceed to implement, give guidance for one more pass, or abort.
- Only MEDIUM or LOW: send `remediate` once, then go to step 5.
- Clean: go to step 5.

Done when analyze is clean, MEDIUM/LOW were remediated, or the user chose to proceed.

## 5. Implement

Spawn `factory-code-build` with `worktree`, `branch`, `spec_dir`, the `speckit-implement` path and `commands`. It commits each finished task. Envelope `partial` (context running low): spawn a fresh `factory-code-build`; it resumes from the tasks.md checkboxes.

Then **verify** yourself: run `commands.build` and `commands.test` in the worktree. Red: send the output to code-build once (`SendMessage`); still red: halt.

Done when every tasks.md box is checked and your own build and test runs are green.

## 6. Review

1. Diff: `git diff <base>...HEAD` in the worktree. The run is a **UI diff** when any changed path is a UI file: view markup (`*.axaml`, `*.xaml`, `*.html`, `*.tsx`, `*.jsx`, `*.vue`, `*.svelte`, `*.css`, `*.scss`), SwiftUI/Compose views, or anything under `Views/`, `ViewModels/`, `components/`, `pages/`.
2. UI diff and `impeccable` not resolvable (step 1.3 search order): ask once, then run `npx impeccable install --providers=claude --scope=global`. Declined: skip `factory-ui-reviewer` and tell the approver.
3. In **one message**, spawn in parallel: `factory-security-reviewer`, `factory-code-standards`, `factory-spec-conformance`, plus `factory-ui-reviewer` and `factory-ux-reviewer` on a UI diff. Each gets `worktree`, `spec_dir`, `base`, the review round, and (UI reviewer) the impeccable SKILL.md path. Save each report to `<spec_dir>/factory/reviews/round-<n>/<agent>.json`.
4. Spawn `factory-review-judge` with `worktree`, `spec_dir`, `base`, the round and the round folder. Save its verdict as `verdict.json` in the same folder. Checkpoint.
5. Verdict has confirmed blocking findings and `review.fix_rounds < 2`: spawn `factory-fixer` with `worktree`, `spec_dir`, `commands` and the verdict path, verify (step 5), increment `review.fix_rounds`, and repeat this step from 1 with the next round number.

Done when the verdict has no confirmed blocking findings, or `review.fix_rounds == 2` (remaining blockers go to the approver flagged as unresolved).

## 7. Approver

Notify, then show the user: one-paragraph summary, `git diff --stat <base>...HEAD`, link to `spec.md`, the judge verdict, findings fixed per round, advisory and unresolved findings. Ask with `AskUserQuestion`: **Approve**, **Request changes**, **Abort**.

- Approve: step 8.
- Request changes: take the user's text, spawn `factory-fixer` with it, verify (step 5), re-run step 6 from 1 (the fix-round cap does not apply here), then return to this step.
- Abort: set `status: aborted`, checkpoint, keep the worktree, stop.

## 8. PR

1. `git push -u origin <branch>`.
2. Invoke the `pr` skill to write the body: link `spec.md`, summarise the change, include the judge verdict and advisory findings.
3. `gh pr create --base <default-branch> --head <branch> --title "<title>" --body-file <file>`, ready for review.
4. Set `status: pr-open` and `pr_url`, checkpoint, push.
5. When the desktop app's PR tools are available, offer (do not do) Auto-fix binding.

Done when the PR URL is in state and shown to the user.

## Policies

- **Checkpoint** after every completed stage (state.md). The state file is the single truth for where the run is.
- **Halt**: set `status: halted` with `halt_reason`, checkpoint, notify, ask the user. Their answer resumes the stage, redirects it, or aborts.
- **Notify** (`PushNotification`) every time you wait on the user: relay questions, analyze-loop exhaustion, red build, agent failure, approver.
- **Failure policy**: an agent crashes, times out, or returns no parseable envelope: retry once with a fresh agent, same inputs plus the error and current state; second failure: halt.
- **Skills that block model invocation** (every `speckit-*`, and `grill-with-docs`): never call them with the Skill tool. Agents `Read` the resolved `SKILL.md` and follow it. `grill-with-docs` runs as `grilling` then `domain-modeling`.
- **SpecKit hooks** (`.specify/extensions.yml`): skipped for the whole run. The factory owns the branch and every commit.
