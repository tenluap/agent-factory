# Software Factory: Design

Source of truth for how `/factory` behaves. `skills/factory/SKILL.md` and the agent files in `agents/` are built from this document; when they disagree, fix them to match this one (or change this one first, deliberately).

Agreed in a grilling session on 2026-10-21.

## What it is

`/factory` is one user-invoked skill. Whichever Claude Code session runs it becomes the **orchestrator**: it runs the loop below, spawns every agent, owns the run's state, and is the only thing that talks to the user. Agents never talk to the user directly.

The skill is global (symlinked into `~/.claude/skills/factory`) and works in any git repo that has SpecKit (`.specify/`) installed.

## Flow

```
feature
  -> grilling                       (orchestrator, invoking checkout, writes nothing to the repo)
  -> worktree on NNN-name branch    (orchestrator)
  -> specify -> clarify -> grill-with-docs -> plan -> tasks -> analyze     (spec-builder)
        ^                                                          |
        +------ remediate, then loop (max 2 loops) ----------------+
  -> implement                      (code-build)
  -> build + test verified          (orchestrator)
  -> reviews in parallel            (5 reviewers, UI/UX conditional)
  -> judge                          (review-judge)
  -> fix confirmed findings, re-review (fixer, max 2 rounds)
  -> approver                       (user)
  -> PR                             (orchestrator)
```

## Agents

| Agent | Model | Role |
|---|---|---|
| `factory-spec-builder` | opus | Runs specify through analyze, one stage per turn; remediates analyze findings |
| `factory-code-build` | sonnet | Runs speckit.implement against tasks.md; must finish green |
| `factory-security-reviewer` | sonnet | Security review of the diff |
| `factory-code-standards` | sonnet | Diff vs the repo's documented conventions |
| `factory-spec-conformance` | sonnet | Diff vs spec, plan, tasks |
| `factory-ui-reviewer` | sonnet | impeccable audit + critique of changed UI (UI diffs only) |
| `factory-ux-reviewer` | sonnet | UX flows, states, copy (UI diffs only) |
| `factory-review-judge` | opus | Merges, dedupes, verifies findings; one verdict |
| `factory-fixer` | sonnet | Fixes confirmed findings or the user's requested changes |

Subagents cannot spawn subagents, so the "reviewer agent" is the **judge**: the orchestrator fans out the reviewers and hands their output to the judge.

All reviewers return the same findings shape (`skills/factory/references/findings.md`).

## Decisions

### Setup
- **Missing `.specify/`**: offer to run `specify init --here --ai claude`, then the constitution step. Ask once.
- **impeccable missing**: ask once, then `npx impeccable install --providers=claude --scope=global`.
- **Skills that block model invocation**: every `speckit-*` skill and `grill-with-docs` set `disable-model-invocation: true`, so no agent can call them via the Skill tool. Agents `Read` the resolved `SKILL.md` and follow it as instructions. `grill-with-docs` runs as its two parts: `grilling` + `domain-modeling`.

### Isolation
- Grilling runs in the invoking checkout and writes nothing to the repo. Its output (`brief.md`) and pre-run state live under `~/.claude/factory/pending/` until the worktree exists.
- The branch name comes from SpecKit's git script in `--dry-run` mode. The factory creates a git worktree on that branch, and everything after grilling runs inside it.
- The spec directory is passed explicitly (`SPECIFY_FEATURE_DIRECTORY=specs/<branch>`), so branch and spec folder always match.
- SpecKit extension hooks are skipped: the factory owns the branch and every commit.
- Several runs may go at once in one repo, one per session. Branch creation reserves the number, so a later dry-run sees it.

### Interactive steps (relay)
- Grilling at the top runs in the orchestrator directly.
- clarify, grill-with-docs, and specify's clarification markers run inside spec-builder. When spec-builder has questions it ends its turn with the **whole queue** (with recommended answers). The orchestrator asks the user in grilling-round format, saves every answer to state as it arrives, and sends the answers back with `SendMessage`.

### Analyze loop
- After analyze: if any CRITICAL or HIGH finding exists, spec-builder **fixes every finding at every severity** (remediation). Findings that need a user decision become clarify questions instead of silent fixes. Then the flow returns to clarify and re-runs clarify, grill-with-docs, plan, tasks, analyze. Plan and tasks receive the analyze report and remediation log so regeneration keeps the fixes.
- At most 2 loops. If CRITICAL/HIGH findings remain after the second loop, halt and ask the user: proceed, give guidance for one more pass, or abort.
- If analyze reports only MEDIUM/LOW findings: remediate once, then go straight to implement (no loop).

### Implement
- code-build reads build and test commands from the repo's CLAUDE.md / AGENTS.md, falling back to detection.
- Done = every task in tasks.md checked, build green, tests green. The orchestrator re-runs build and tests itself to verify. Still red after code-build's own attempts: halt and ask.

### Review
- Always: security, code-standards, spec-conformance.
- Only when the diff touches UI files: UI (impeccable) and UX.
- The judge merges, dedupes and verifies. Confirmed blocking findings go to the fixer; then build + test, then re-review. At most 2 fix rounds. Advisory findings go to the approver untouched.

### Approver
Shows summary, diff stat, spec link, judge verdict, fixed findings, remaining advisory findings. Options:
- **Approve**: push and open the PR.
- **Request changes** (free text): fixer, build + test, re-review, back to the approver. No cap; the user drives it.
- **Abort**: keep the worktree, state `aborted`.

### PR
Push the branch, open a ready-for-review PR against the default branch with a body written via the `pr` skill (links the spec, includes the review summary). State becomes `pr-open` with the URL. The worktree is kept until the branch merges. Binding the PR to the desktop app's Auto-fix monitor is offered, not automatic.

### State and resume
- State lives at `specs/<branch>/factory/state.json` inside the worktree (schema: `skills/factory/references/state.md`).
- One checkpoint commit per stage (`factory: <stage> complete`) plus a state update. Implement additionally resumes per task from the tasks.md checkboxes.
- Resume restarts the interrupted stage from its beginning. A relay in progress resumes from the saved Q&A: a fresh spec-builder gets the answered questions and asks only the rest.
- `--stop-at <stage>` (on a new run or a resume) pauses the run cleanly before that stage starts: checkpoint, `status: paused`, notify, end the turn. `/factory resume <branch>` continues from that stage in any session.
- Plain `/factory` lists unfinished runs in the current repo (scanning `git worktree list` plus `~/.claude/factory/pending/`) and offers to resume one. `/factory <feature>` starts a new run.

### Policies
- Agent failure (crash, unparseable output, timeout): retry once with the error attached, then halt and ask.
- Push notification on every wait for the user: relay questions, analyze-loop exhaustion, red build, agent failure, approver.
- `speckit.checklist` and `speckit.taskstoissues` are not part of the flow.

## Validation plan

Run end-to-end on a tiny real feature in WayUnoMcpTool. Run with `--stop-at review`, then `/factory resume <branch>` in a fresh session to confirm review starts from the paused state. Separately, kill a session mid-implement and confirm resume continues from the right task. Stop at the approver without opening a PR.
