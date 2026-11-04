# Brief: cruise mode

Add an opt-in **cruise mode** to the software factory. It is like YOLO: once started, a run needs no user input. Every question an agent or the orchestrator would ask is answered with its recommended answer, every one-off setup offer is accepted, and decision halts resolve themselves. The one exception is publishing. Cruise always stops at the existing approver gate, and the factory never pushes the branch or opens a PR until the user explicitly chooses Approve.

Chain: **lite** (default; escalates to full on any CRITICAL/HIGH analyze finding).

## Decisions

- **Flag (Q1)**: `--cruise` / `--no-cruise`, off by default, last one wins, valid on new runs and on `resume`. Stored as `mode.cruise` (boolean) in state. Cruise turns `mode.fast` on. `--no-fast` together with `--cruise` (cruise still on) is rejected as a conflict and named to the user, never silently resolved.
- **Initial grilling (Q2)**: under cruise the orchestrator answers its own grilling frontier with its recommended answers, records each one as `auto: true`, writes `brief.md` and continues with no wait. Every such answer appears in the approver's veto list.
- **Protected questions (Q3)**: cruise auto-accepts `requires_user: true` questions (test-seam confirmation, design scope/identity/exception decisions) and `analyze.pending_clarify` questions with their recommended answers. Each one is recorded with a distinct cruise-override marker and highlighted separately in the approver's veto list. Fast mode without cruise keeps today's protections unchanged.
- **Halts (Q4)**: decision halts auto-resolve. Analyze-loop exhaustion picks "proceed to implement" and carries the unresolved findings to the approver. Failure halts still halt and notify: a red build after the retry, a second agent failure, and the three-partial-returns stall cap.
- **Stop point (Q5)**: the existing approver gate is cruise's stop. Cruise never auto-approves. Nothing is pushed and no PR is created before the user picks Approve. Request changes and Abort keep working. After Request changes, the fix → verify → re-review loop runs in cruise again until it returns to the approver.
- **Harness permissions (Q6)**: no rendering change. Each adapter's `harness.md` documents that harness's no-prompt launch option (for example Claude Code `--permission-mode bypassPermissions`). Cruise preflight tells the user the session may still prompt when it is not launched that way, then continues.
- **One-off setup offers (Q7)**: cruise accepts each offer with its recommended default: `specify init` plus a constitution drafted from the repo, confirmation of detected build/test commands, the global `npx impeccable install`, and the ambiguous-intake question (defaults to delivery). Each acceptance is recorded in the veto list.
- **Defaults settled with the user's confirmation**:
  - Notifications: under cruise the orchestrator notifies only when it actually waits on the user (the approver gate and failure halts). The per-batch "auto-accepted N questions" notice becomes a log line, not a notification.
  - `--stop-at` still works under cruise and pauses where it says.
  - The approver screen shows the veto list in two groups: cruise overrides (protected questions, auto-resolved halts, accepted setup offers) first, then ordinary auto-accepted answers.
  - The exact state shape of the cruise-override marker (an answer/decision field or a decision `kind`) is a plan-time decision. It must stay additive, so older states remain valid, and every write must still go through the state CLI.
- **Out of scope**: changing any harness's permission mode programmatically, auto-merging, and auto-approving the PR gate.

## Commands

- build: render all five harnesses into a temp `FACTORY_HOME`, then `bash -n install.sh` (from README/CI)
- test: `python3 -m unittest discover -s tools`
