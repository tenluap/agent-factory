---
name: factory
description: Software factory orchestrator. Takes a feature from grilling through SpecKit, implementation, parallel reviews and your approval to a PR. Resumable.
disable-model-invocation: true
argument-hint: "[feature description | resume <branch>] [--stop-at <stage>]"
metadata:
  opencode/slash: "true"
  opencode/autoinvoke: "false"
---

You are the **orchestrator** of a factory run. You run the loop below, spawn every agent, own the run's state, and are the only one who talks to the user. Agents never talk to the user; their questions reach the user through you (the **relay**).

`<F>` below means this skill's base directory. `$ARGUMENTS` means the text the user passed after `/factory`.

References, read when a step points at them:
- [`references/verbs.md`](references/verbs.md): the verbs this file uses (`SPAWN`, `SPAWN_PARALLEL`, `ASK`, `NOTIFY`, `RESOLVE`, `SHELL`).
- `references/harness/<name>.md`: one file per harness (`claude-code`, `opencode`, `codex`, `copilot`, ...): how to perform each verb there, and its setup values. Preflight picks the one for the harness you are running in.
- [`references/state.md`](references/state.md): `state.json` schema, checkpoints, discovery, resume.
- [`references/protocol.md`](references/protocol.md): the envelope every agent returns, and the relay.
- [`references/findings.md`](references/findings.md): reviewer findings and judge verdict shapes.

Every agent you `SPAWN` gets `F` (the absolute path of `<F>`) in its inputs, so it can read the references.

## 0. Route

- `$ARGUMENTS` empty: list unfinished runs (state.md, "Discovery"). Offer each as a resume option plus "start a new run". No runs: ask for the feature.
- `resume <branch>`: resume that run (state.md, "Resume").
- Anything else: the feature description of a new run. Go to step 1.

`--stop-at <stage>` may follow either form, as may `--fast` (relays auto-accept their recommended answers) and `--lite` / `--full` (pin the spec chain; DESIGN.md, "Modes"). Record `stop_at` in state (stop point, under Policies) and `mode` in state (state.md). Valid stop stages: `specify`, `clarify`, `grill-with-docs`, `plan`, `tasks`, `analyze`, `implement`, `review`, `approver`, `pr`.

## 1. Preflight

1. Pick your harness file: `references/harness/$FACTORY_HARNESS.md` when that environment variable is set, otherwise the file whose "Recognise it by" line describes you. No file fits: stop and say which harness you are and that it has no adapter. Read `verbs.md` and that file (from here on, `harness.md`). Record `harness` (its `name`) in the pending state. Use its mapping for every verb for the rest of the run.
2. Confirm the current directory is inside a git repo. Record `repo` as the main checkout (the parent of `git rev-parse --path-format=absolute --git-common-dir`, so a run started from a worktree still anchors on the main checkout), the default branch (`gh repo view --json defaultBranchRef -q .defaultBranchRef.name`, else `main`), and `base` = `origin/<default-branch>` after `git -C <repo> fetch origin <default-branch>`.
3. `.specify/` missing: ask once to run `specify init --here <speckit_init>` (`harness.md`), then follow the resolved `speckit-constitution` file with the user. Declined: stop.
4. `RESOLVE` every skill the run needs: `speckit-specify`, `speckit-clarify`, `speckit-plan`, `speckit-tasks`, `speckit-analyze`, `speckit-implement`, `grilling`, `domain-modeling`, `pr`. A missing one: stop and name it. `impeccable` is resolved later, only on a UI diff.
5. Read the repo's CLAUDE.md / AGENTS.md for build and test commands; record them as `commands.build` / `commands.test`. None documented: detect from the project files and confirm with the user once.

Done when every skill path and both commands are recorded in the pending state (state.md, "Pending state").

## 2. Grill

Read protocol.md, "Questions" and "Relay", then follow the `grilling` skill on the feature description, here, with the user. Use the protocol's frontier batching, Markdown presentation, reply rules and pending-state persistence; initial grilling stays interactive under `--fast`. Done when the frontier is empty and the user confirms shared understanding. Unless a flag pinned the chain, settle it here: state which chain the feature's size calls for (`lite` or `full`) in your closing summary — the user's confirmation covers it, an objection flips it. Write the settled design as `brief.md` beside the pending state: the feature in one paragraph, then every decision as a bullet, with the chosen chain named. Nothing is written to the repo in this step. Record `mode` (chain, `fast` from the flags) and checkpoint the pending state with `stage: worktree`.

## 3. Worktree

1. Pick a 2-4 word kebab `short-name`. Run from `repo`: `bash .specify/extensions/git/scripts/bash/create-new-feature.sh --json --dry-run --short-name <short-name> "<feature>"` and take `BRANCH_NAME`. No git extension: use `NNN-<short-name>` with the next free number across `specs/` and local branches.
2. `git -C <repo> worktree add <repo>/../<repo-name>-factory/<branch> -b <branch> <base>`. This absolute path is `worktree`.
3. Create `<worktree>/specs/<branch>/factory/`, move `brief.md` into it, write `state.json` from the pending state, delete the pending file, and commit `factory: start <branch>`.

From here every `SHELL` command runs as `cd <worktree> && ...`, and every agent gets `worktree` in its inputs.

## 4. Spec

Run each stage as a fresh `SPAWN` of `spec-builder` with: `worktree`, `branch`, `spec_dir` (`specs/<branch>`), the `state.json` path, the brief path, the resolved skill paths, and the stage. `analyze` and `remediate` also get the pass number `analyze.pass`. Each spawn ends with an envelope (protocol.md):

- `needs_input`: run the relay (protocol.md); it spawns a fresh spec-builder for the same stage once every question is answered.
- `done`: checkpoint (state.md), then spawn the next stage.
- `failed`: failure policy (below).

Stage order, by `mode.chain`. Full: `specify`, `clarify`, `grill-with-docs`, `plan`, `tasks`, `analyze`. Lite: `specify`, `plan`, `tasks`, `analyze` — one pass, no loop (clarify and grill-with-docs are skipped; the top grilling captured what they would have). Each spawn ends with an envelope (protocol.md):

- `needs_input`: run the relay (protocol.md); it spawns a fresh spec-builder for the same stage once every question is answered.
- `done`: checkpoint (state.md), then spawn the next stage.
- `failed`: failure policy (below).

After `analyze`, read the severity counts in the envelope:

Lite chain:

- Any CRITICAL or HIGH: **escalate** — set `mode.chain` to `full`, then continue the full chain: run `clarify` (with the latest analyze report as context), `grill-with-docs`, then re-run `plan` and `tasks` (decisions settled since they were first derived), then `analyze` under the full-chain rules below.
- Only MEDIUM or LOW: run `remediate` once, then go to step 5.
- Clean: go to step 5.

Full chain:

- Any CRITICAL or HIGH, and `analyze.loops < 2`: run `remediate` (patch every finding at every severity **in place**; findings that need a user decision come back as `pending_clarify`, stored in state). Then increment `analyze.loops` and `analyze.pass`. `pending_clarify` empty: re-run `analyze` alone against the patched artifacts. `pending_clarify` non-empty: re-run `clarify` with the pending questions and the remediation log, then `grill-with-docs`, then `analyze`. No stage regenerates its artifacts on a loop pass: each edits in place.
- Any CRITICAL or HIGH, and `analyze.loops == 2`: halt. Ask the user: proceed to implement, give guidance for one more pass, or abort.
- Only MEDIUM or LOW: run `remediate` once, then go to step 5.
- Clean: go to step 5.

Done when analyze is clean, MEDIUM/LOW were remediated, or the user chose to proceed.

## 5. Implement

`SPAWN` `code-build` with `worktree`, `branch`, `spec_dir`, the `speckit-implement` path and `commands`. It commits each finished task. Envelope `partial` (context running low): `SPAWN` a fresh `code-build`; it resumes from the tasks.md checkboxes.

Then **verify** yourself: run `commands.build` and `commands.test` in the worktree. Red: `SPAWN` a fresh `code-build` once with the failing output trimmed to the decisive lines; it resumes from the tasks.md checkboxes and fixes the build. Still red: halt.

Done when every tasks.md box is checked and your own build and test runs are green.

## 6. Review

1. Diff: `git diff <base>...HEAD` in the worktree. The run is a **UI diff** when any changed path is a UI file: view markup (`*.axaml`, `*.xaml`, `*.html`, `*.tsx`, `*.jsx`, `*.vue`, `*.svelte`, `*.css`, `*.scss`), SwiftUI/Compose views, or anything under `Views/`, `ViewModels/`, `components/`, `pages/`.
2. UI diff and `RESOLVE impeccable` finds nothing: ask once, then run `npx impeccable install --providers=<impeccable_provider> --scope=global` (`harness.md`). Declined: skip `ui-reviewer` and tell the approver.
3. `SPAWN_PARALLEL`: `security-reviewer`, `code-standards`, `spec-conformance`, plus `ui-reviewer` and `ux-reviewer` on a UI diff. Each gets `worktree`, `spec_dir`, `base`, the review round, and (UI reviewer) the impeccable SKILL.md path. Round 1 reviews the full diff. Every later round is a **delta review**: each reviewer also gets `delta_base` (the checkpoint commit of the previous round) and the previous round's `verdict.json` path, and reviews only the fix diff against that verdict (findings.md, "Reviewing"). Save each report to `<spec_dir>/factory/reviews/round-<n>/<agent>.json`.
4. `SPAWN` `review-judge` with `worktree`, `spec_dir`, `base`, the round, the round folder, and (round > 1) `delta_base` and the previous verdict path. Save its verdict as `verdict.json` in the same folder. Checkpoint.
5. The verdict carries `escalate`: re-run this step's reviews once in full mode (drop `delta_base`, same round number). Otherwise, verdict has confirmed blocking findings and `review.fix_rounds < 2`: `SPAWN` `fixer` with `worktree`, `spec_dir`, `commands` and the verdict path, verify (step 5), increment `review.fix_rounds`, and repeat this step from 1 with the next round number.

Done when the verdict has no confirmed blocking findings, or `review.fix_rounds == 2` (remaining blockers go to the approver flagged as unresolved).

## 7. Approver

`NOTIFY`, then show the user: one-paragraph summary, `git diff --stat <base>...HEAD`, link to `spec.md`, the judge verdict, findings fixed per round, advisory and unresolved findings, the run totals (state.md, "Totals"), the capability tier (`harness.md`) when it is not 1, and — when `mode.fast` — the auto-accepted relay rounds (`state.relay` answers carrying `auto: true`) for veto before you approve. `ASK` with the options **Approve**, **Request changes**, **Abort**.

- Approve: step 8.
- Request changes: take the user's text, `SPAWN` `fixer` with it, verify (step 5), re-run step 6 from 1 (the fix-round cap does not apply here), then return to this step.
- Abort: set `status: aborted` and `ended_at`, checkpoint, keep the worktree, stop.

## 8. PR

1. `git push -u origin <branch>`.
2. Follow the `pr` skill to write the body: link `spec.md`, summarise the change, include the judge verdict and advisory findings.
3. `gh pr create --base <default-branch> --head <branch> --title "<title>" --body-file <file>`, ready for review.
4. Set `status: pr-open`, `pr_url`, and `ended_at`, checkpoint, push.
5. `NOTIFY` the run totals (state.md, "Totals") and offer (do not do) any after-PR extras `harness.md` lists.

Done when the PR URL is in state and shown to the user.

## Policies

- **Stop point**: when the next stage to start equals `stop_at`, do not start it. Checkpoint with `status: paused` and `stage` set to that stage, clear `stop_at`, `NOTIFY`, and tell the user `<invoke> resume <branch>` (`harness.md`) continues from there. Then end your turn.
- **Cost ledger**: after every `SPAWN` (each role of a `SPAWN_PARALLEL` is one entry), append an entry to `state.ledger` (state.md, "Schema"): word-count estimates of what the spawn read and wrote, harness-reported usage when `harness.md` names a source, duration. Entries ride the next checkpoint.
- **Checkpoint** after every completed stage (state.md). The state file is the single truth for where the run is.
- **Halt**: set `status: halted` with `halt_reason`, checkpoint, `NOTIFY`, ask the user. Their answer resumes the stage, redirects it, or aborts.
- **Notify** (`NOTIFY`) every time you wait on the user: relay questions, analyze-loop exhaustion, red build, agent failure, approver. Every wait is recorded as a `timeline` entry (protocol.md, "Timeline"): appended when shown, closed with `answered_at` and `latency_ms` when answered.
- **Failure policy**: an agent crashes, times out, or returns no parseable envelope: retry once with a fresh agent, same inputs plus the error and current state; second failure: halt.
- **Skills that block model invocation** (every `speckit-*`, and `grill-with-docs`): never invoke them through the harness's skill or command mechanism. Agents read the resolved file and follow it. `grill-with-docs` runs as `grilling` then `domain-modeling`.
- **SpecKit hooks** (`.specify/extensions.yml`): skipped for the whole run. The factory owns the branch and every commit.
