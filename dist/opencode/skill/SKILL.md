---
name: factory
description: Software factory orchestrator. Takes a feature from grilling through SpecKit, implementation, parallel reviews and your approval to a PR. Resumable.
disable-model-invocation: true
argument-hint: "[<feature description> | resume <branch>] [--lite | --full] [--fast | --no-fast] [--stop-at <stage>]"
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
- [`references/skills.md`](references/skills.md): skill-integration precedence and loading rules, shared with `code-build` and `fixer`.

Every agent you `SPAWN` gets `F` (the absolute path of `<F>`) in its inputs, so it can read the references.

## 0. Route

- `$ARGUMENTS` empty: `SHELL: python3 <F>/bin/factory runs` (state.md, "CLI"). Offer each run it lists (branch or name, stage, status, last activity) as a resume option plus "start a new run". No runs: ask for the feature.
- `resume <branch>`: `SHELL: python3 <F>/bin/factory show <branch-or-name>` (state.md, "CLI"), then resume that run from the digest (state.md, "Resume").
- Anything else: the feature description of a new run. Classify its **intake intent** from the request text (DESIGN.md, "Skill routing"), deciding which stage starts the run:
  - **Exploration** — open-ended idea wording with no settled solution (e.g. "I have an idea for...", "explore whether we could...", "not sure yet, but what if..."): after step 1, go to step 2 (`brainstorm`).
  - **Delivery** — concrete feature/change wording, or a request naming an existing spec (e.g. "add a `--no-fast` flag", "fix the resume path so..."): after step 1, go straight to step 3 (`grill`), skipping step 2.
  - **Ambiguous** — neither set of cues present, or both: after step 1, `ASK` exactly one relay question (protocol.md, "Questions") — explore first, or settle it as a feature now — with no new command flag; the answer picks step 2 or step 3 as above, and is saved as that question's relay answer.

Flags are recognised wherever they appear in `$ARGUMENTS`, on either form, and may combine:

- `--lite` / `--full`: pin the spec chain (step 5, "Stage order"). The last one wins.
- `--fast` / `--no-fast`: whether relay rounds auto-accept their recommended answers. The last one wins.
- `--stop-at <stage>`: pause the run cleanly before that stage (Policies, "Stop point"). Valid stages: `specify`, `clarify`, `grill-with-docs`, `plan`, `tasks`, `analyze`, `implement`, `review`, `approver`, `pr`.

The **default mode** is `lite` chain with `fast` on: wherever a flag did not pin it, that is what the run uses. Strip the flags from `$ARGUMENTS` before routing; flags alone (no feature text, no `resume`) route as empty `$ARGUMENTS`. On a new run record `stop_at` and `mode` in state (state.md) at creation; on a resume the flags update the same fields before the stage restarts. An unknown flag or a `--stop-at` value outside the list is never silently ignored: name it and ask the user to correct it or drop it.

## 1. Preflight

1. Pick your harness file: `references/harness/$FACTORY_HARNESS.md` when that environment variable is set, otherwise the file whose "Recognise it by" line describes you. No file fits: stop and say which harness you are and that it has no adapter. Read `verbs.md` and that file (from here on, `harness.md`). Record `harness` (its `name`) in the pending state. Use its mapping for every verb for the rest of the run.
2. Confirm the current directory is inside a git repo. Record `repo` as the main checkout (the parent of `git rev-parse --path-format=absolute --git-common-dir`, so a run started from a worktree still anchors on the main checkout), the default branch (`gh repo view --json defaultBranchRef -q .defaultBranchRef.name`, else `main`), and `base` = `origin/<default-branch>` after `git -C <repo> fetch origin <default-branch>`.
3. `.specify/` missing: ask once to run `specify init --here <speckit_init>` (`harness.md`), then follow the resolved `speckit-constitution` file with the user. Declined: stop.
4. `RESOLVE` every skill the run needs: `speckit-specify`, `speckit-clarify`, `speckit-plan`, `speckit-tasks`, `speckit-analyze`, `speckit-implement`, `grilling`, `domain-modeling`, `pr`. A missing one: stop and name it. Also `RESOLVE` `ponytail` and `tdd` here, before the run ever commits to delivery; record whichever resolve in `skills`, but do not stop here if either is missing — code delivery (step 6, step 7) stops that work alone, naming the missing skill, when it is about to start. On the idea path only (intake intent is exploration), also `RESOLVE` `brainstorming`; missing there, stop and name it the same way as the always-required skills — it is never resolved on the feature path. `impeccable` is resolved later, only on a UI diff. On resume, `RESOLVE` any of these names still absent from `skills`, and every resolved path again when `harness` changed, before any role is spawned (state.md, "Resume").
5. Read the repo's CLAUDE.md / AGENTS.md for build and test commands; record them as `commands.build` / `commands.test`. None documented: detect from the project files and confirm with the user once.

Done when every skill path and both commands are recorded in the pending state (state.md, "Pending state").

## 2. Brainstorm (idea path only)

Read protocol.md, "Questions" and "Relay", then follow the resolved `brainstorming` skill on the feature description, here, in the invoking checkout, with these overrides:

- You handle all user interaction yourself: use the protocol's frontier batching, Markdown presentation, reply rules and pending-state persistence instead of the skill's own one-question-at-a-time format. Offer its visual companion only for actual visual exploration and only with its own required consent.
- Write nothing to the invoking checkout: save every intake artifact (alternatives considered, tradeoffs, the confirmed direction) in the pending state alongside the request. These artifacts move into the worktree unchanged at step 4 (Worktree).
- You own every commit, not the skill: skip its own commit instruction and its handoff to a separate planning skill. SpecKit remains the only planning chain, continued at step 3 (Grill).

Done when the frontier is empty and the user has confirmed a direction (and, where the skill asks, whether to proceed to feature delivery). Write the confirmed direction into `brief.md` beside the pending state: the alternatives considered, then the chosen direction and every decision already settled, each as a bullet. Checkpoint the pending state with `stage: grill`, then go to step 3.

## 3. Grill

Read protocol.md, "Questions" and "Relay", then follow the `grilling` skill on the feature description, here, with the user. Use the protocol's frontier batching, Markdown presentation, reply rules and pending-state persistence; initial grilling stays interactive whatever the mode. When step 2 (`brainstorm`) ran first, read its `brief.md` decisions as settled inputs and ask only what is still open — never repeat an already-answered question. Done when the frontier is empty and the user confirms shared understanding. Name the chain in effect in your closing summary — the user's confirmation covers it, an objection flips it. The chain is `lite` unless a flag pinned it; recommend `full` in the summary when the feature's size calls for it. Write the settled design as `brief.md` beside the pending state: the feature in one paragraph, then every decision as a bullet (including any brainstorming already settled), with the chosen chain named. Nothing is written to the repo in this step. Record `mode` (the settled chain and `fast`) and checkpoint the pending state with `stage: worktree`.

## 4. Worktree

1. Pick a 2-4 word kebab `short-name`. Run from `repo`: `bash .specify/extensions/git/scripts/bash/create-new-feature.sh --json --dry-run --short-name <short-name> "<feature>"` and take `BRANCH_NAME`. No git extension: use `NNN-<short-name>` with the next free number across `specs/` and local branches.
2. `git -C <repo> worktree add <repo>/../<repo-name>-factory/<branch> -b <branch> <base>`. This absolute path is `worktree`.
3. Create `<worktree>/specs/<branch>/factory/`, move `brief.md` into it, write `state.json` from the pending state, delete the pending file, and commit `factory: start <branch>`.

From here every `SHELL` command runs as `cd <worktree> && ...`, and every agent gets `worktree` in its inputs.

## 5. Spec

Run each stage as a fresh `SPAWN` of `spec-builder` with: `worktree`, `branch`, `spec_dir` (`specs/<branch>`), the `state.json` path, the brief path, the resolved skill paths, and the stage. `analyze` and `remediate` also get the pass number `analyze.pass`. Each spawn ends with an envelope (protocol.md):

- `needs_input`: run the relay (protocol.md); it spawns a fresh spec-builder for the same stage once every question is answered.
- `done`: checkpoint (state.md), then spawn the next stage.
- `failed`: failure policy (below).

Stage order, by `mode.chain`. Full: `specify`, `clarify`, `grill-with-docs`, `plan`, `tasks`, `analyze`. Lite: `specify`, `plan`, `tasks`, `analyze` — one pass, no loop (clarify and grill-with-docs are skipped; the top grilling captured what they would have).

After `analyze`, read the severity counts in the envelope:

Lite chain:

- Any CRITICAL or HIGH: **escalate** — set `mode.chain` to `full`, then continue the full chain: run `clarify` (with the latest analyze report as context), `grill-with-docs`, then re-run `plan` and `tasks` (decisions settled since they were first derived), then `analyze` under the full-chain rules below.
- Only MEDIUM or LOW: run `remediate` once, then go to step 6.
- Clean: go to step 6.

Full chain:

- Any CRITICAL or HIGH, and `analyze.loops < 2`: run `remediate` (patch every finding at every severity **in place**; findings that need a user decision come back as `pending_clarify`, stored in state). Then increment `analyze.loops` and `analyze.pass`. `pending_clarify` empty: re-run `analyze` alone against the patched artifacts. `pending_clarify` non-empty: re-run `clarify` with the pending questions and the remediation log, then `grill-with-docs`, then `analyze`. No stage regenerates its artifacts on a loop pass: each edits in place.
- Any CRITICAL or HIGH, and `analyze.loops == 2`: halt. Ask the user: proceed to implement, give guidance for one more pass, or abort.
- Only MEDIUM or LOW: run `remediate` once, then go to step 6.
- Clean: go to step 6.

Done when analyze is clean, MEDIUM/LOW were remediated, or the user chose to proceed.

## 6. Implement

`ponytail` or `tdd` unresolved in `skills`: stop this work and tell the user the missing skill's setup guidance; nothing is spawned and no work is reported done.

`SPAWN` `code-build` with `worktree`, `branch`, `spec_dir`, the `speckit-implement` path, the resolved `ponytail` and `tdd` paths, and `commands`. It commits each finished task. Envelope `partial` (context running low): `SPAWN` a fresh `code-build` with the same inputs; it resumes from the tasks.md checkboxes.

Then **verify** yourself: run `commands.build` and `commands.test` in the worktree. Red: `SPAWN` a fresh `code-build` once with the failing output trimmed to the decisive lines; it resumes from the tasks.md checkboxes and fixes the build. Still red: halt.

Done when every tasks.md box is checked and your own build and test runs are green.

## 7. Review

1. Diff: `git diff <base>...HEAD` in the worktree. The run is a **UI diff** (`review.ui_diff`) when any changed path is a UI file: view markup and styles (`*.axaml`, `*.xaml`, `*.html`, `*.tsx`, `*.jsx`, `*.vue`, `*.svelte`, `*.css`, `*.scss`, SwiftUI/Compose views, or anything under `Views/`, `ViewModels/`, `components/`, `pages/`); design tokens and themes (token/theme/style resource files, token JSON, `Themes/`); UI assets shipped to the interface (icons, images, fonts); or locale and string files (`*.resx`, `*.strings`, `*.arb`, locale JSON/YAML catalogues). A diff confined to one of these files is still a UI diff even when its only change is literal user-visible copy. A diff touching none of these skips `ui-reviewer`, `ux-reviewer` and the `impeccable` install offer below (`review.ui_diff: false`).
2. UI diff and `RESOLVE impeccable` finds nothing: ask once, then run `npx impeccable install --providers=<impeccable_provider> --scope=global` (`harness.md`). Declined: skip `ui-reviewer`, record `review.ui_reviewer_skipped: true`, and tell the approver (disclosed at step 8).
3. `SPAWN_PARALLEL`: `security-reviewer`, `code-standards`, `spec-conformance`, plus `ui-reviewer` and `ux-reviewer` on a UI diff. Each gets `worktree`, `spec_dir`, `base`, the review round, and (UI reviewer) the impeccable SKILL.md path. Round 1 reviews the full diff. Every later round is a **delta review**: each reviewer also gets `delta_base` (the checkpoint commit of the previous round) and the previous round's `verdict.json` path, and reviews only the fix diff against that verdict (findings.md, "Reviewing"). Save each report to `<spec_dir>/factory/reviews/round-<n>/<agent>.json`.
4. `SPAWN` `review-judge` with `worktree`, `spec_dir`, `base`, the round, the round folder, and (round > 1) `delta_base` and the previous verdict path. Save its verdict as `verdict.json` in the same folder. Checkpoint.
5. The verdict carries `escalate`: re-run this step's reviews once in full mode (drop `delta_base`, same round number). Otherwise, verdict has confirmed blocking findings and `review.fix_rounds < 2`: `ponytail` or `tdd` unresolved: stop this fix round the same way as step 6. Else `SPAWN` `fixer` with `worktree`, `spec_dir`, `commands`, the resolved `ponytail` and `tdd` paths and the verdict path, verify (step 6), increment `review.fix_rounds`, and repeat this step from 1 with the next round number.

Done when the verdict has no confirmed blocking findings, or `review.fix_rounds == 2` (remaining blockers go to the approver flagged as unresolved).

## 8. Approver

`NOTIFY`, then show the user: one-paragraph summary, `git diff --stat <base>...HEAD`, link to `spec.md`, the judge verdict, findings fixed per round, advisory and unresolved findings, the run totals (state.md, "Totals"), the capability tier (`harness.md`) when it is not 1, and — when `mode.fast` — the auto-accepted relay rounds (`state.relay` answers carrying `auto: true`) for veto before you approve. When `review.ui_diff` is true, disclose the UI evaluation's state: `review.ui_reviewer_skipped` (the install was declined), or, when `ui-reviewer` ran, whether its findings disclosed rendered or only static/evidence-limited evaluation. `ASK` with the options **Approve**, **Request changes**, **Abort**.

- Approve: step 9.
- Request changes: `ponytail` or `tdd` unresolved: stop the same way as step 6/7. Else take the user's text, `SPAWN` `fixer` with it and the resolved `ponytail` and `tdd` paths, verify (step 6), re-run step 7 from 1 (the fix-round cap does not apply here), then return to this step.
- Abort: set `status: aborted` and `ended_at`, checkpoint, keep the worktree, stop.

## 9. PR

1. `git push -u origin <branch>`.
2. Follow the `pr` skill to write the body: link `spec.md`, summarise the change, include the judge verdict and advisory findings.
3. `gh pr create --base <default-branch> --head <branch> --title "<title>" --body-file <file>`, ready for review.
4. Set `status: pr-open`, `pr_url`, and `ended_at`, checkpoint, push.
5. `NOTIFY` the run totals (state.md, "Totals") and offer (do not do) any after-PR extras `harness.md` lists.

Done when the PR URL is in state and shown to the user.

## Policies

- **Stop point**: when the next stage to start equals `stop_at`, do not start it. Checkpoint with `status: paused` and `stage` set to that stage, clear `stop_at`, `NOTIFY`, and tell the user `<invoke> resume <branch>` (`harness.md`) continues from there. Then end your turn. A `stop_at` the chain never reaches (e.g. `clarify` on a lite run that never escalates) simply never triggers; the run finishes with the setting unset.
- **Cost ledger**: after every `SPAWN` (each role of a `SPAWN_PARALLEL` is one entry), append an entry to `state.ledger` (state.md, "Schema"): word-count estimates of what the spawn read and wrote, harness-reported usage when `harness.md` names a source, duration. Entries ride the next checkpoint.
- **Checkpoint** after every completed stage (state.md). The state file is the single truth for where the run is.
- **Halt**: set `status: halted` with `halt_reason`, checkpoint, `NOTIFY`, ask the user. Their answer resumes the stage, redirects it, or aborts.
- **Notify** (`NOTIFY`) every time you wait on the user: relay questions, analyze-loop exhaustion, red build, agent failure, approver. Every wait is recorded as a `timeline` entry (protocol.md, "Timeline"): appended when shown, closed with `answered_at` and `latency_ms` when answered.
- **Failure policy**: an agent crashes, times out, or returns no parseable envelope: retry once with a fresh agent, same inputs plus the error and current state; second failure: halt.
- **Skills that block model invocation** (every `speckit-*`, and `grill-with-docs`): never invoke them through the harness's skill or command mechanism. Agents read the resolved file and follow it. `grill-with-docs` runs as `grilling` then `domain-modeling`.
- **SpecKit hooks** (`.specify/extensions.yml`): skipped for the whole run. The factory owns the branch and every commit.
