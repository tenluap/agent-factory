# Software Factory: Design

Source of truth for how `/factory` behaves. `core/` and the adapters in `adapters/` are built from this document; when they disagree, fix them to match this one (or change this one first, deliberately).

Agreed in a grilling session on 2026-10-21. Harness model and stateless agents agreed on 2026-10-22.

## What it is

`/factory` is one user-invoked skill. Whichever agent session runs it becomes the **orchestrator**: it runs the loop below, spawns every agent, owns the run's state, and is the only thing that talks to the user. Agents never talk to the user directly.

The skill is global (installed into the harness's skill directory) and works in any git repo that has SpecKit (`.specify/`) installed.

## Harness model

The factory runs on any agent harness (Claude Code, OpenCode, Codex, GitHub Copilot, ...). It is split into a portable core and thin per-harness adapters.

- **Core** (`core/`): the orchestrator `SKILL.md`, its references, and the role prompts in `core/roles/`. Core files never name a harness tool. They use the neutral **verbs** defined in `core/skills/factory/references/verbs.md`: `SPAWN`, `SPAWN_PARALLEL`, `ASK`, `NOTIFY`, `RESOLVE`, `SHELL`.
- **Adapter** (`adapters/<harness>/`): `harness.md`, which tells the orchestrator how to recognise the harness, how to perform each verb there, where skills and SpecKit commands live, and the harness's setup values; and `adapter.json`, which tells the renderer where to install and how to write native agent files (Markdown or TOML, fields, access, models).
- **One skill for every harness.** The installed skill is byte-identical on every harness and carries every adapter's `harness.md` under `references/harness/`. In preflight the orchestrator picks its own (`$FACTORY_HARNESS`, else the file whose "Recognise it by" line fits). This matters because harnesses read each other's skill directories (OpenCode reads `~/.claude/skills`, Copilot and Codex read `~/.agents/skills`): whichever copy a harness finds, it is the same skill. Only the agent files are generated per harness, by `tools/render.py`.
- **Adapters today**: `claude-code`, `opencode`, `codex`, `copilot` (CLI and VS Code agent mode; the github.com cloud agent is out of scope since it cannot relay questions). Agent models are pinned only on Claude Code (opus/sonnet); elsewhere agents inherit the session's model unless `${FACTORY_HOME}/config.json` pins them.
- **Roles** carry neutral metadata (`tier`: `deep` | `standard`; `access`: `read` | `write`). The adapter maps tiers to models and access to tool lists. Users override models in `${FACTORY_HOME}/config.json`.
- **Capability tiers.** An adapter declares the tier its harness runs at: 1 native subagents, 2 headless CLI subprocesses, 3 inline (the orchestrator plays each role itself). The approver screen states the tier when it is not 1, since tier 3 weakens reviewer independence.
- **Factory home.** Harness-neutral files live in `${FACTORY_HOME:-~/.factory}`: pending runs, user config. Every harness shares it, so discovery finds runs started anywhere.
- **Agents are stateless.** Every agent turn is a fresh `SPAWN`; nothing relies on continuing a live agent. Whatever a later turn needs is in `state.json` or on disk. This is what lets every harness, and a resume on a different harness, run the same flow.

## Flow

```
feature
  -> grilling                       (orchestrator, invoking checkout, writes nothing to the repo)
  -> worktree on NNN-name branch    (orchestrator)
  -> specify -> clarify -> grill-with-docs -> plan -> tasks -> analyze     (spec-builder)
        ^                                                          |
        +------ remediate (patch), then verify loop (max 2 loops) --+
  -> implement                      (code-build)
  -> build + test verified          (orchestrator)
  -> reviews in parallel            (5 reviewers, UI/UX conditional)
  -> judge                          (review-judge)
  -> fix confirmed findings, re-review (fixer, max 2 rounds)
  -> approver                       (user)
  -> PR                             (orchestrator)
```

Lite chain (DESIGN, "Modes"): specify -> plan -> tasks -> analyze, one pass, no loop; any CRITICAL/HIGH escalates to the full chain from clarify.

## Agents

| Agent | Tier | Access | Role |
|---|---|---|---|
| `factory-spec-builder` | deep | write | Runs specify through analyze, one stage per spawn; remediates analyze findings |
| `factory-code-build` | standard | write | Runs speckit.implement against tasks.md; must finish green |
| `factory-security-reviewer` | standard | read | Security review of the diff |
| `factory-code-standards` | standard | read | Diff vs the repo's documented conventions |
| `factory-spec-conformance` | standard | read | Diff vs spec, plan, tasks |
| `factory-ui-reviewer` | standard | read | impeccable audit + critique of changed UI (UI diffs only) |
| `factory-ux-reviewer` | standard | read | UX flows, states, copy (UI diffs only) |
| `factory-review-judge` | deep | read | Merges, dedupes, verifies findings; one verdict |
| `factory-fixer` | standard | write | Fixes confirmed findings or the user's requested changes |

On Claude Code, `deep` is opus and `standard` is sonnet.

Agents cannot spawn agents, so the "reviewer agent" is the **judge**: the orchestrator fans out the reviewers and hands their output to the judge.

All reviewers return the same findings shape (`core/skills/factory/references/findings.md`).

## Decisions

### Setup
- **Missing `.specify/`**: offer to run `specify init --here <harness.speckit_init>` (`--ai <harness>`, plus `--ai-skills` outside Claude Code so SpecKit's commands land as skills), then the constitution step. Ask once.
- **impeccable missing**: ask once, then `npx impeccable install --providers=<harness.impeccable_provider> --scope=global`.
- **Skills that block model invocation**: every `speckit-*` skill and `grill-with-docs` set `disable-model-invocation: true` (or are commands rather than skills on some harnesses), so no agent invokes them. Agents read the resolved file and follow it as instructions. `grill-with-docs` runs as its two parts: `grilling` + `domain-modeling`.

### Isolation
- Grilling runs in the invoking checkout and writes nothing to the repo. Its output (`brief.md`) and pre-run state live under `${FACTORY_HOME}/pending/` until the worktree exists.
- The branch name comes from SpecKit's git script in `--dry-run` mode. The factory creates a git worktree on that branch, and everything after grilling runs inside it.
- The spec directory is passed explicitly (`SPECIFY_FEATURE_DIRECTORY=specs/<branch>`), so branch and spec folder always match.
- SpecKit extension hooks are skipped: the factory owns the branch and every commit.
- Several runs may go at once in one repo, one per session. Branch creation reserves the number, so a later dry-run sees it.

### Modes
- **Chain** (`full` | `lite`), recorded in `state.mode.chain`. Default: the orchestrator judges the feature's size at the end of grilling and states which chain it picked; `--lite` / `--full` pin it. `lite` = specify → plan → tasks → analyze, one pass, no loop: clarify and grill-with-docs are skipped (the top grilling captured what they would have). Any CRITICAL/HIGH analyze finding escalates: the chain becomes `full` and continues from clarify (clarify, grill-with-docs, then plan and tasks re-derived, then analyze under the normal loop rules). MEDIUM/LOW: remediate once, then implement. Every stage keeps its checkpoints, so a lite run resumes like any other.
- **Fast** (`state.mode.fast`, opt-in `--fast`): the orchestrator auto-accepts every relay round with the agent's recommended answers, recorded with `"auto": true` in `state.relay`, collapsing multi-round stages to agent-only turns. Never auto-answered: questions in `state.analyze.pending_clarify` (a patch that overturns a decision is the user's to make), and every halt — loop exhaustion, red build, agent failure, `--stop-at`. The approver screen lists the auto-accepted rounds for veto.

### Interactive steps (relay)
- Grilling at the top runs in the orchestrator directly. It uses the same question presentation and reply rules as later relays and stays interactive under `--fast`.
- Work the design tree in rounds. Each round contains the **whole frontier**: every open decision whose prerequisites are settled. Defer questions whose wording or options depend on unanswered decisions; recompute the frontier after the round is answered.
- clarify, grill-with-docs, and specify's clarification markers run inside spec-builder. When spec-builder has questions it ends its turn with the whole frontier (with recommended answers). The orchestrator saves every answer to state as it arrives, then spawns a fresh spec-builder for the same stage. That role reads every round from `state.relay`, treats answered questions as settled, and asks only what is still open. Relay restarts and resume use the same path.
- **Presentation** is chat Markdown on every harness, even for one question: `🧭 Question N of M · Qid`, a `❓` question heading, helper text, lettered options with meaningful emojis and short descriptions, an `✨ AI suggested` marker on the recommended option, and a `💡 Suggested answer` block with the answer, a concise `🎯` rationale grounded in known context, and a textual `✅ Use suggested answer: Qid: accept` shortcut. Separate questions with horizontal rules. N/M counts positions in the current round; Qids remain unique within the stage across rounds. Shortcuts are text, not interactive buttons.
- **Custom answers**: each choice question includes a final `💬 Something else` option. Use free text without artificial choices for open-ended questions; their recommendation may be proposed text.
- **Replies**: accept `Q7: B`, `Q7: <custom text>`, and `Q7: accept`. Bare `accept` fills only unanswered questions with their recommendations, preserving explicit answers. Bare option letters are valid only when exactly one question remains unanswered. Clarify ambiguous replies before assigning them; save each unambiguous answer immediately.
- **Compatibility**: keep existing saved answers and IDs. New question fields support helper text, structured option descriptions/emojis, and a separate recommendation rationale. Read old question shapes too, showing available information in the new layout without inventing missing descriptions or rationale. Accepted answers contain the selection or proposed text, separate from its rationale. Fast-mode eligibility stays unchanged, including the `pending_clarify` exclusion.

### Analyze loop
- After analyze: if any CRITICAL or HIGH finding exists, spec-builder **patches every finding at every severity in place** (remediation edits `spec.md`, `plan.md`, `tasks.md` and the other artifacts; it never regenerates them). Findings that need a user decision become clarify questions instead of silent fixes. Then analyze **re-runs against the patched artifacts** (pass + 1) to confirm the fixes.
- clarify and grill-with-docs re-enter the loop only when a remediation finding was deferred to clarify (a decision-touching patch): the pending questions are answered, the settled decisions are edited into the artifacts, and analyze verifies again. A loop whose patches touched no decision re-runs analyze alone.
- At most 2 loops. If CRITICAL/HIGH findings remain after the second loop, halt and ask the user: proceed, give guidance for one more pass, or abort.
- If analyze reports only MEDIUM/LOW findings: remediate once (patches in place), then go straight to implement (no loop).

### Implement
- code-build reads build and test commands from the repo's CLAUDE.md / AGENTS.md, falling back to detection.
- Done = every task in tasks.md checked, build green, tests green. The orchestrator re-runs build and tests itself to verify. Still red after code-build's own attempts: one fresh code-build gets the failing output; still red: halt and ask.

### Review
- Always: security, code-standards, spec-conformance.
- Only when the diff touches UI files: UI (impeccable) and UX.
- Round 1 reviews the full diff. Every later round is a **delta review**: reviewers see the fix diff since the previous round's checkpoint together with the previous verdict, and check that the fixes landed and added nothing. The fixer declares every file it touches beyond the findings' own files as `Adjacent: <path> - <reason>` in its commit body; the judge checks the fix diff's file list against the findings' files and those lines, and its verdict can carry `escalate`, which re-runs the round once in full review.
- The judge merges, dedupes and verifies. Confirmed blocking findings go to the fixer; then build + test, then a delta re-review. At most 2 fix rounds. Advisory findings go to the approver untouched.

### Approver
Shows summary, diff stat, spec link, judge verdict, fixed findings, remaining advisory findings, the capability tier when it is not 1, and (when `mode.fast`) the auto-accepted relay rounds. Options:
- **Approve**: push and open the PR.
- **Request changes** (free text): fixer, build + test, re-review, back to the approver. No cap; the user drives it.
- **Abort**: keep the worktree, state `aborted`.

### PR
Push the branch, open a ready-for-review PR against the default branch with a body written via the `pr` skill (links the spec, includes the review summary). State becomes `pr-open` with the URL. The worktree is kept until the branch merges. Harness-specific extras (on Claude Code, offering the desktop app's Auto-fix binding) come from `harness.md` and are offered, not automatic.

### State and resume
- State lives at `specs/<branch>/factory/state.json` inside the worktree (schema: `core/skills/factory/references/state.md`). It records the `harness` running the run; each `history` entry records the harness that wrote it.
- One checkpoint commit per stage (`factory: <stage> complete`) plus a state update. Implement additionally resumes per task from the tasks.md checkboxes.
- Resume restarts the interrupted stage from its beginning. A relay in progress resumes from the saved Q&A: a fresh spec-builder gets the answered questions and asks only the rest.
- A run may be resumed on a different harness: the orchestrator re-resolves every skill path.
- `--stop-at <stage>` (on a new run or a resume) pauses the run cleanly before that stage starts: checkpoint, `status: paused`, notify, end the turn. `resume <branch>` (with the harness's invoke command, e.g. `/factory` or `$factory`) continues from that stage in any session, on any harness.
- Plain `/factory` lists unfinished runs in the current repo (scanning `git worktree list` plus `${FACTORY_HOME}/pending/`) and offers to resume one. `/factory <feature>` starts a new run.

### Cost ledger
- Every `SPAWN` (each role of a `SPAWN_PARALLEL` counts as one) appends one entry to `state.ledger` (schema: `state.md`): stage, role, harness, input/output token estimates, harness-reported usage when available, duration.
- Estimates are harness-neutral: 1.35 × word count of what the spawn was told to read (its role file, the resolved skill files, the artifacts its inputs name) and of what it wrote (the returned envelope plus new files under the spec's `factory/` folder).
- `reported` is reserved for usage the harness exposes (today: none in tier 1; tier-2 CLI output where the harness prints it). Every efficiency change to the flow is measured against a prior run's ledger, not guessed.
- The ledger's own cost is one `wc -w` and one state write per spawn.

### Policies
- Agent failure (crash, unparseable output, timeout): retry once with the error attached, then halt and ask.
- Notification (`NOTIFY`, a no-op where the harness has none) on every wait for the user: relay questions, analyze-loop exhaustion, red build, agent failure, approver.
- `speckit.checklist` and `speckit.taskstoissues` are not part of the flow.

## Engineering discipline

The factory's coding discipline lives in one shared, harness-neutral reference: `core/skills/factory/references/engineering.md`, addressed by roles as `<F>/references/engineering.md`, carrying the stable rule ids `ENG-1`..`ENG-11` ([ADR 0001](docs/adr/0001-factory-owns-its-engineering-rules.md)). Every role that writes, plans, reviews or judges code points at it and restates no rule inline.

- **Red proof**: the red step is recorded as one `Red:` line in the task's own commit body, in one of the two accepted forms; there is no separate red commit, so history stays bisectable ([ADR 0002](docs/adr/0002-red-proof-lives-in-the-task-commit-body.md)).
- **Test seams**: the plan settles, at plan time, the public seams put under test and any test-first exemption with its reason; an implementing or fixing role never invents a seam — it stops and reports a missing one as a failure ([ADR 0003](docs/adr/0003-test-seams-are-settled-at-plan-time.md)).
- **Enforcement**: `code-standards` enforces the rules on the code (diff), `spec-conformance` checks red proofs against `tasks.md` (and fix commits against the prior round's verdict), and the judge verifies and rates findings by rule id.
- **Precedence**: a consuming repository's constitution or documented conventions win; the plan records `Overridden: ENG-n - <repo rule that wins>`.
- **Judgement-call ceiling and advisory route**: a finding whose cited id is `ENG-7`..`ENG-10` is at most MEDIUM and never blocking, lowered rather than dropped, while a finding citing `ENG-1`..`ENG-6` keeps the severity its own rule states. A capped finding is advisory: no verdict-driven fix round acts on it, it reaches the user in the verdict's advisory list, and the approver's existing "Request changes" is the user's route to having it fixed ([ADR 0004](docs/adr/0004-judgement-call-rules-advise-they-never-block.md)).
- **Stop on an un-runnable test command**: a repository with a test runner whose test command cannot be run is a stop, not an exemption. Both code-writing roles return a failure naming the command and its error and ride the orchestrator's existing failure policy, writing no behaviour-changing code and no third form of red proof.
- **Plan-time reason line**: the plan states a reason for each new file, new abstraction and new dependency it introduces; analyze reports a MEDIUM, non-blocking finding for a missing one.

## Validation plan

Run end-to-end on a tiny real feature in WayUnoMcpTool. Run with `--stop-at review`, then `/factory resume <branch>` in a fresh session to confirm review starts from the paused state. Separately, kill a session mid-implement and confirm resume continues from the right task. Stop at the approver without opening a PR. Repeat for each new adapter; once two adapters exist, start a run on one harness with `--stop-at implement` and resume it on the other.
