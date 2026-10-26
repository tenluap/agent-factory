# Software Factory: Design

Source of truth for how `/factory` behaves. `core/` and the adapters in `adapters/` are built from this document; when they disagree, fix them to match this one (or change this one first, deliberately).

Agreed in a grilling session on 2026-10-21. Harness model and stateless agents agreed on 2026-10-22. Skill routing agreed on 2026-10-25 (`docs/superpowers/specs/2026-10-25-factory-skill-routing-design.md`).

Pen design-code mapping agreed on 2026-10-25 ([approved contract](docs/superpowers/specs/2026-10-25-pen-design-code-mapping-design.md)).

## What it is

`/factory` is one user-invoked skill. Whichever agent session runs it becomes the **orchestrator**: it runs the loop below, spawns every agent, owns the run's state, and is the only thing that talks to the user. Agents never talk to the user directly.

The skill is global (installed into the harness's skill directory) and works in any git repo that has SpecKit (`.specify/`) installed.

## Harness model

The factory runs on any agent harness (Claude Code, OpenCode, Codex, GitHub Copilot, ZCode, ...). It is split into a portable core and thin per-harness adapters.

- **Core** (`core/`): the orchestrator `SKILL.md`, its references, and the role prompts in `core/roles/`. Core files never name a harness tool. They use the neutral **verbs** defined in `core/skills/factory/references/verbs.md`: `SPAWN`, `SPAWN_PARALLEL`, `ASK`, `NOTIFY`, `RESOLVE`, `SHELL`.
- **Adapter** (`adapters/<harness>/`): `harness.md`, which tells the orchestrator how to recognise the harness, how to perform each verb there, where skills and SpecKit commands live, and the harness's setup values; and `adapter.json`, which tells the renderer where to install and how to write native agent files (Markdown or TOML, fields, access, models).
- **One skill for every harness.** The installed skill is byte-identical on every harness and carries every adapter's `harness.md` under `references/harness/`. In preflight the orchestrator picks its own (`$FACTORY_HARNESS`, else the file whose "Recognise it by" line fits). This matters because harnesses read each other's skill directories (OpenCode reads `~/.claude/skills`, Copilot and Codex read `~/.agents/skills`): whichever copy a harness finds, it is the same skill. Only the agent files are generated per harness, by `tools/render.py`.
- **Adapters today**: `claude-code`, `opencode`, `codex`, `copilot` (CLI and VS Code agent mode; the github.com cloud agent is out of scope since it cannot relay questions), `zcode` (Z.ai's coding agent, desktop app or CLI). Every adapter supplies `deep` and `standard` model defaults in `adapter.json`. `${FACTORY_HOME}/config.json` overrides those defaults; an empty model value inherits the session's model.
- **Roles** carry neutral metadata (`tier`: `deep` | `standard`; `access`: `read` | `write`). The adapter maps tiers to models and access to tool lists. Users override models in `${FACTORY_HOME}/config.json`.
- **Capability tiers.** An adapter declares the tier its harness runs at: 1 native subagents, 2 headless CLI subprocesses, 3 inline (the orchestrator plays each role itself). The approver screen states the tier when it is not 1, since tier 3 weakens reviewer independence.
- **Factory home.** Harness-neutral files live in `${FACTORY_HOME:-~/.factory}`: pending runs, user config. Every harness shares it, so discovery finds runs started anywhere.
- **Agents are stateless.** Every agent turn is a fresh `SPAWN`; nothing relies on continuing a live agent. Whatever a later turn needs is in `state.json` or on disk. This is what lets every harness, and a resume on a different harness, run the same flow.
- **State CLI.** The skill carries `bin/factory`, the factory's single state writer (stdlib Python, thin entry over `bin/factory_cli/`). Read commands (`runs`, `show`, `validate`) do the mechanical discovery and digest work outside the orchestrator's context so routing cost stays flat; write commands (`checkpoint`, `ledger-add`, `wait-open`/`wait-close`, `answer`, `set-status`, `decisions-add`, `verify`, `rebind`, `resume`) stamp, validate, write atomically and commit — the orchestrator never hand-edits `state.json`, and a missing Python 3 halts the run instead of falling back to manual writes. `envelope check`, `lock take` and `prune` complete the command surface (gates and hardening below).

## OpenCode V2 adapter

OpenCode V2 uses foreground `subagent` calls targeting the named `factory-<role>` agent with complete inputs. Parallel dispatch waits for every result; each spawn starts a fresh child session. `SHELL` uses `shell`. Question relay, skill resolution, all nine roles, global/project installation paths and model tiers remain unchanged.

Native Markdown emits `mode: subagent` and an ordered `permissions` sequence. Every rule retains `action`, `resource`, `effect` field order, wildcard resource `*` and effect `deny`. Read roles deny `edit` then `subagent`; write roles deny `subagent` only. The orchestrator alone dispatches roles. Other permissions follow OpenCode configuration. JSON flow mappings inside YAML sequences preserve wildcard quoting without a dependency; existing scalar, flat-map, string-list and TOML behavior stays unchanged.

Supported V1 agent and skill definitions remain intended to work through OpenCode's compatibility translation; this is native V2 adoption, not a claim that supported V1 definitions broke. The factory uses neither the plugin nor server API. Existing installer and model overrides still apply; no user configuration migration is needed.

Static rendering verifies output and cross-harness byte compatibility. Historical OpenCode v2.1.4 discovery loaded nine global symlinked roles with expected policy and the factory skill; loading does not establish model-backed dispatch or runtime permission enforcement. Those two checks remain unverified without an actual runtime trial. No new model calls are required for this change, and an observed runtime contract conflict blocks delivery rather than weakening the rules.

## Flow

```
feature
  -> intake: classify exploration vs delivery ("Skill routing"), one question if ambiguous
  -> [idea path] brainstorm         (orchestrator, invoking checkout, writes nothing to the repo)
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

## Skill routing

Agreed 2026-10-25 (`docs/superpowers/specs/2026-10-25-factory-skill-routing-design.md`). Uses the right externally-installed skill at the right point in the run, without weakening stateless roles, saved answers, worktree isolation, independent review or publication approval.

### Routing contract

| Trigger | Skill | Owner | First/applied stage |
|---|---|---|---|
| An exploratory idea without a settled solution — e.g. "I have an idea for...", "explore whether we could...", "not sure yet, but what if..." | `brainstorming` | Orchestrator | `brainstorm`, before `grill` |
| A concrete feature, change, or an idea already ready to build — e.g. "add a `--no-fast` flag", "fix the resume path so...", a named existing spec | `grilling` | Orchestrator | `grill` (idea path's second stage, feature path's first) |
| Neither set of cues, or both | — one intent question decides, then routes as above | Orchestrator | — |
| Implementation or repair of code | `ponytail` and `tdd` | `code-build`, `fixer` | `implement`, `fix` |
| A UI-related diff enters review | `impeccable` audit and critique | `ui-reviewer` | `review` |
| A user-facing flow changes | existing UX lens (complementary, not a repeat of the UI pass) | `ux-reviewer` | `review` |

Intake intent is not a stored field: step 0 of `SKILL.md` decides it from the request text, visible afterwards only in the run's first `stage` value and, when a question was needed, in that question's saved relay answer. The idea path is `brainstorm -> grill -> worktree -> the existing spec chain`; the feature path starts at `grill`. Stopping after `brainstorm` leaves the run paused with the confirmed direction in the pending brief and nothing written to the invoking checkout; resuming continues into `grill`, which treats brainstorming's settled decisions as inputs and asks only what is still open. A run saved before this routing existed keeps resuming at its recorded stage unchanged — `brainstorm` is additive to the stage vocabulary (`state.md`), not a replacement of any existing one.

### Skill resolution and precedence

Every lookup is the active adapter's `RESOLVE` operation; machine-specific paths never enter `core/`. `speckit-*`, `grilling`, `domain-modeling` and `pr` resolve at preflight as today. `brainstorming` resolves only on the idea path. `ponytail` and `tdd` resolve at preflight, before a run commits to code delivery, and their absolute paths go to every fresh `code-build`/`fixer` spawn. `impeccable` resolves later, only on a UI diff, through the existing install offer with a disclosed skip. A resume re-resolves any name never resolved and, when `harness` changed, every path. A required missing skill stops the affected work with setup guidance naming it; nothing is installed beyond the existing authorised `impeccable` offer.

Precedence when a skill's guidance and the factory's own rules could conflict: `core/skills/factory/references/engineering.md` always wins. In particular, the external `tdd` skill defers refactoring to review, while `ENG-1` permits small behaviour-preserving refactoring while tests stay green — the engineering rules govern. A skill's own guidance applies only inside the approved specification: it removes no requirement, security control, accessibility behaviour, planned test, repository tooling or `ENG-n` evidence, and never replaces a role's required result envelope. A skill's own companion references (e.g. `tdd`'s `tests.md`/`mocking.md`) resolve from that skill's own directory, never from the factory or the consuming repository. These rules are stated once, compactly, in `core/skills/factory/references/skills.md`, and `SKILL.md`, `code-build.md` and `fixer.md` link to it rather than restating it.

### Protected confirmations

`tdd` requires user-confirmed test seams before writing tests, and factory roles never talk to the user directly, so `spec-builder` relays the plan's proposed public seams as one question at the end of `plan`, before implementation starts. Relay questions gain an optional `requires_user: true` field (`protocol.md`): fast mode must never auto-answer such a question, alongside the existing `pending_clarify` exclusion; a question saved without the field keeps today's behaviour. The seam confirmation is persisted with the plan (`plan.md`, "Test seams", `Confirmed: <date> - <Qid> accepted - seams: ...`) and reused only while the seams and scope it names match; a changed seam list requires a new confirmation, and a plan whose every part is exempt skips the question entirely. `code-build` and `fixer` read the plan's seams, never the confirmation line, and never ask the user: a task needing an unlisted seam is `ENG-4`'s existing stop-and-report failure, not a question.

### Widened UI-change detection

Step 6.1's UI classification (`SKILL.md`) widens from a short extension/directory list to: view markup and styles, design tokens and themes, UI assets (icons, images, fonts shipped to the interface), locale and string files, and a diff whose only change is user-visible copy inside UI code. A diff touching none of these skips the UI passes (`ui-reviewer`, `ux-reviewer`, the `impeccable` install offer). `ui-reviewer` follows `impeccable`'s audit-and-critique route explicitly, running its setup once in the reviewer's own context, staying read-only, and disclosing whether its evidence was rendered or static rather than describing static inspection as an observed interaction; a skipped or evidence-limited UI evaluation is disclosed at the approver gate. `ux-reviewer` keeps its distinct, complementary lens rather than repeating the UI pass.

## Pen design references

Whenever a factory run creates, references, or updates a Pen design intended as an implementation reference, activate the framework-independent [mapping contract](core/skills/factory/references/design-code-mapping.md). Resolve `pen-design` conditionally through the active adapter; a missing required skill or backend capability is a disclosed blocker, not an inferred API. Keep framework-specific guidance separate, starting with [Avalonia](core/skills/factory/references/design-code-mapping-avalonia.md). Standalone Pen invocations outside the factory are outside this boundary.

The repository's canonical `docs/design-code-map.json` (or its existing equivalent) supports multiple sources, exhaustive scoped node coverage, canonical components/instances, stable code anchors, explicit removals/exceptions, and reverse lookup from the same records. A design-only task records source/targets without requiring code. Existing implementations bootstrap only the requested scope and dependencies. Persist context in pending storage before worktree creation and under the feature's `factory/design/` afterward; the permanent map references scoped committed sources, exports, captures, and comparison metadata.

Design governs visual decisions. Default implementation updates to design → code; design edits require an explicit request. Resolve a unique target from the request or saved context/map, and ask on ambiguity. Check source freshness and code anchors on each new/resumed run. Inspect shared consumers, obtain agreement before expanding visual scope, and preserve application behavior when a design element is removed. Unsupported inspection, missing identifiers, or unavailable revisions must be reported honestly.

Mapped implementations require current build/runtime, mapping, and rendered-fidelity evidence independently of optional impeccable evaluation. Exact supported design values and matching viewport/theme/state/DPI/scale comparison are required; no universal pixel threshold is imposed. Static desktop review cannot establish rendered fidelity. Treat a demonstrated violation of the approved reference as a requirement failure, rather than advisory styling preference.

Mapping/visual findings share the existing two automatic fix rounds with all other findings; persist the counter before each design fix attempt so resume cannot reset it. A design gate failure goes through this queue, not a fresh code-build retry for visual repair. Missing prerequisites or exhausted rounds leave work partial/blocked. An explicit, scoped user exception may permit proceeding, while retaining the failed/missing gate and unverified status. Fast mode and ordinary publication approval cannot infer that exception. Non-Pen runs preserve their existing flow and UI policy.

Fresh spec-builder, code-build, fixer, reviewers, and judge receive the saved `design` context reference. The orchestrator independently checks evidence identity/results, routes protected decisions, and reports design status and exceptions at approval and in the PR. No new agent role, harness verb, second map, or repair loop is introduced.

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
- **Missing `.specify/`**: offer to run `specify init --here <harness.speckit_init>` — each adapter states its own `speckit_init` arguments (ZCode's: `--integration zcode --integration-options="--skills"`) — then the constitution step. Ask once.
- **impeccable missing**: ask once, then `npx impeccable install --providers=<harness.impeccable_provider> --scope=global`.
- **Skills that block model invocation**: every `speckit-*` skill and `grill-with-docs` set `disable-model-invocation: true` (or are commands rather than skills on some harnesses), so no agent invokes them. Agents read the resolved file and follow it as instructions. `grill-with-docs` runs as its two parts: `grilling` + `domain-modeling`.

### Isolation
- Grilling runs in the invoking checkout and writes nothing to the repo. Its output (`brief.md`) and pre-run state live under `${FACTORY_HOME}/pending/` until the worktree exists.
- The branch name comes from SpecKit's git script in `--dry-run` mode. The factory creates a git worktree on that branch, and everything after grilling runs inside it.
- The spec directory is passed explicitly (`SPECIFY_FEATURE_DIRECTORY=specs/<branch>`), so branch and spec folder always match.
- SpecKit extension hooks are skipped: the factory owns the branch and every commit.
- Several runs may go at once in one repo, one per session. Branch creation reserves the number, so a later dry-run sees it.

### Modes
- **Chain** (`full` | `lite`), recorded in `state.mode.chain`. Default `lite`: a run starts on the lite chain unless a flag pinned it (`--lite` pins lite, `--full` pins full; the last one wins). Grilling's closing summary names the chain in effect and the user's confirmation covers it — an objection flips it to `full`, which the orchestrator recommends when the feature's size calls for it. `lite` = specify → plan → tasks → analyze, one pass, no loop: clarify and grill-with-docs are skipped (the top grilling captured what they would have). Any CRITICAL/HIGH analyze finding escalates: the chain becomes `full` and continues from clarify (clarify, grill-with-docs, then plan and tasks re-derived, then analyze under the normal loop rules). MEDIUM/LOW: remediate once, then implement. Every stage keeps its checkpoints, so a lite run resumes like any other.
- **Fast** (`state.mode.fast`, on by default; `--fast` pins it on, `--no-fast` turns it off, the last one wins): the orchestrator auto-accepts every relay round with the agent's recommended answers, recorded with `"auto": true` in `state.relay`, collapsing multi-round stages to agent-only turns. Never auto-answered: questions in `state.analyze.pending_clarify` (a patch that overturns a decision is the user's to make), and every halt — loop exhaustion, red build, agent failure, `--stop-at`. The approver screen lists the auto-accepted rounds for veto.

### Interactive steps (relay)
- Grilling at the top runs in the orchestrator directly. It uses the same question presentation and reply rules as later relays and stays interactive even in fast mode.
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
- `--stop-at <stage>` (on a new run or a resume) pauses the run cleanly before that stage starts: checkpoint, `status: paused`, notify, end the turn. A `--stop-at` stage the chain never reaches (e.g. `clarify` on a lite run that never escalates) never triggers. `resume <branch>` (with the harness's invoke command, e.g. `/factory` or `$factory`) continues from that stage in any session, on any harness. Flags on a resume update the run before the stage restarts: `--lite` / `--full` rewrite `mode.chain`, `--fast` / `--no-fast` rewrite `mode.fast`.
- Plain `/factory` lists unfinished runs in the current repo (`bin/factory runs`, scanning `git worktree list` plus `${FACTORY_HOME}/pending/`) and offers to resume one; `/factory <feature>` starts a new run. `resume <branch>` fetches a resume digest (`bin/factory show`) — scalars plus aggregates, never the whole state — and restarts the recorded stage from it.

### State CLI (v4)
- **Writer layout**: `bin/factory` stays a thin entry script (argv → `factory_cli.cli.main`, exit codes preserved); all logic lives in `core/skills/factory/bin/factory_cli/` modules (`__init__`, `cli`, `state`, `lock`, `checks`, `totals`, `commands`), which the renderer's `copytree` already carries into every `dist/<harness>/skill/` unchanged. Every state mutation goes through it; the orchestrator never hand-edits `state.json`, and a missing Python 3 halts the run with a clear message instead of falling back to manual writes.
- **Schema v4**: `version: 4` adds an append-only `decisions` list and per-spawn `started_at`/`ended_at` intervals; the history-event vocabulary is closed — `complete`, `verify-pass`, `verify-fail`, `approved`, `gate-override`, `aborted`, `pr-open`, `resumed` — and anything else is a validation violation with its location. Readers accept versions 1–4 including legacy relay shapes and report, never rewrite, what they read; the writer upgrades a run to v4 in the same atomic write that first changes it (temp file + `os.replace`).
- **Effort accounting**: agent time is the union of ledger spawn intervals, human time the union of recorded user-wait intervals (`at` → `answered_at`), both reported separately; overhead derives as `max(wall − human − agent, 0)`. No report sums parallel durations or subtracts summed durations from wall clock, so human + agent never exceeds wall time by construction.
- **Test layout**: a new `tools/tests/` package (one module per seam plus `fixtures/`) that `python3 -m unittest discover -s tools` discovers unchanged. Runs 005 and 006's saved states are recovered from git history as replay fixtures, each with a defect manifest naming stability-brief §3's core defects the replay must report.

### Enforced gates (M2)
- **Lock lifecycle**: every write acquires `lock.json` beside the state it guards — `<worktree>/specs/<branch>/factory/lock.json` for a worktree run, `<pending-name>.lock.json` beside the pending file before that — recording owner PID, host, harness and time. A write under a live foreign lock is refused with the owner reported; a lock is stale only on its recorded host when the owner process is gone (`os.kill(pid, 0)`), never automatically elsewhere; `factory lock take <run> [--force]` is the only takeover and records `taken_over: true` with the previous lock for audit (FR-005).
- **Gate table**: `factory_cli/checks.py` holds one table checked by `checkpoint` before the write that advances a stage: → `review` requires the latest verify record to be `verify-pass`; → `implement` requires analyze clean, remediated, or an explicit override decision; → `pr` requires an `approved` decision recorded at `approver` (or a `gate-override`). Refusals name the missing record. `factory verify --pass|--fail --commands '<json>'` writes the verify record; `decisions-add --kind approved|gate-override` records the decisions; the transition a gate decision permits also gets an `approved`/`gate-override` history entry carrying that decision's question ID. Every history event keeps exactly one writer (FR-006).
- **Role-output shapes**: `envelope check <file>` validates a role output's final fenced `json` block against the three shapes — envelope (protocol.md), reviewer report and judge verdict (findings.md). Key sets, types and required fields are encoded once in `checks.py` with the references' own fenced examples as passing fixtures; one malformed variant per shape is refused with the offending location. Malformed output enters the retry-once policy (FR-007).
- **CI**: `.github/workflows/ci.yml` runs the full suite, re-renders all five harnesses and fails on the constitution's porcelain drift gate (`test -z "$(git status --porcelain -- dist/)"`, which sees untracked additions a bare diff misses), and checks `install.sh` syntax with `bash -n` (FR-018).

### Portable and safe (M3)
- **Model policy**: only `claude-code` ships default models (opus/sonnet, its harness requires them); `codex`, `copilot`, `opencode` and `zcode` ship `"models": {}` and inherit session models. Personal choices live in the user's `${FACTORY_HOME}/config.json` under `models.<harness>`; they merge only into the per-user render that `install.sh` creates at `${FACTORY_HOME:-~/.factory}/dist/<harness>` (`render.py <harness> --out`), never into the canonical `render.py <harness>` render or the committed `dist/`. `install.sh` prints the effective model per role resolved from the default home, and a render-seam test keeps the README's statement aligned with `adapters/` (FR-015).
- **Preflight guidance**: when the current harness's SpecKit skills are missing, preflight names the exact `specify init --here <speckit_init>` command from `adapters/<harness>/harness.md` and offers to run it, exactly as for a missing `.specify/`; declining stops the run with the command printed (FR-016). Extra per-harness arguments are recorded in `harness.md`.
- **Declared-file checkpoints**: a role's envelope `files` list declares everything it changed. `checkpoint <stage> [--files <path>...] [--envelope <file>]` stages exactly `spec_dir` plus that list, commits `factory: <stage> complete`, and reports every other modified or untracked path without committing it — `git add -A` is gone (FR-017).
- **Rebind**: `factory rebind <run> --worktree <path>` validates the path is a git worktree on the recorded branch, rewrites the stored absolute paths (`worktree`, `repo`) and reports the rewrite; sharing `${FACTORY_HOME}` alone does not move a run (FR-012).

### Proven (M4)
- **Recovery**: a kill-and-resume suite drives a throwaway fixture run to every stage, kills it there, and resumes it through the CLI: no answered question re-asked (relay/decisions survive checkpoints), no committed task redone (tasks.md checkboxes are the resume point), and no duplicate branch, worktree or pull request (SC-006). The suite exposes any missing resume behaviour — the `resumed` history entry is written through the writer (FR-003), and each stage's resume digest is the only thing a restarting agent reads.
- **Golden run**: a fixture repository plus a per-harness golden-run checklist (start, pause at `review`, kill, resume on a second harness, approve, PR against a throwaway remote) records FR-013's evidence; the live two-harness run is recorded after merge in `conformance/golden-run-results.md`.
- **Read-only access**: a static conformance check renders every adapter and asserts each `read`-access agent denies editing in that harness's own terms — tool lists without `Edit`/`Write` (Claude Code, ZCode), OpenCode deny rules, Copilot's tool list. `codex` has no enforceable read-only surface; `adapters/codex/harness.md` documents the limitation and the golden-run checklist records it per adapter (FR-014, R13).

### Hardening and context trim (P2)
- **Prune preview**: `factory prune [--dry-run|--delete]` lists stale pending files — one whose run has a worktree state or has ended (`pr-open`/`aborted`); a run whose only state is the pending file is never stale — and deletes nothing without the explicit `--delete` (FR-019).
- **Installer argument validation**: `install.sh`'s option loop validates every value; a missing `--harness` value prints a clear usage message and exits non-zero instead of crashing on an unbound variable (FR-020, S17).
- **Reported usage labelling**: a ledger entry's `reported` stays `null` unless a harness names a usage source; `show` and the totals line label reported usage separately from the `in_est`/`out_est` word-count estimates, never merged into one number (FR-010, R17).
- **Pen rules in one reference**: `references/design-code-mapping.md` is the single home for the Pen design rules; the duplicated prose in `SKILL.md` (steps 6, 8, 9) and `references/state.md` is replaced by pointers, with every rule sentence accounted for in a checked list so nothing is lost (FR-021, R15).

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

The factory's coding discipline lives in one shared, harness-neutral reference: `core/skills/factory/references/engineering.md`, addressed by roles as `<F>/references/engineering.md`, carrying the stable rule ids `ENG-1`..`ENG-31` ([ADR 0001](docs/adr/0001-factory-owns-its-engineering-rules.md)). Every role that writes, plans, reviews or judges code points at it and restates no rule inline.

Professional code is correct, readable, maintainable, secure, and fast enough for its requirements. The 2026-10-25 revision preserves the original eleven ids and the factory's test-first/commit process, refines clean code, SOLID, reuse and functional preferences to require judgement, and extends the reference to cover the user's 34-practice checklist: problem understanding; KISS/YAGNI/DRY; cohesion, coupling and contracts; types, state and errors; trustworthy tests and incremental refactoring; measured performance, data access and concurrency; resource limits, security and integrity; dependencies, automation, reviewability, observability and safe delivery. Apply relevant practices to the actual change. Do not require an interface, abstraction, service, cache, benchmark or new tool without a concrete need.

- **Red proof**: the red step is recorded as one `Red:` line in the task's own commit body, in one of the two accepted forms; there is no separate red commit, so history stays bisectable ([ADR 0002](docs/adr/0002-red-proof-lives-in-the-task-commit-body.md)).
- **Test seams**: the plan settles, at plan time, the public seams put under test and any test-first exemption with its reason; an implementing or fixing role never invents a seam — it stops and reports a missing one as a failure ([ADR 0003](docs/adr/0003-test-seams-are-settled-at-plan-time.md)).
- **Enforcement**: `code-standards` enforces the rules on the code (diff), `spec-conformance` checks red proofs against `tasks.md` (and fix commits against the prior round's verdict), and the judge verifies and rates findings by rule id.
- **Precedence**: a consuming repository's constitution or documented conventions win; the plan records `Overridden: ENG-n - <repo rule that wins>`.
- **Judgement-call ceiling and advisory route**: a finding based only on design or style guidance, including `ENG-7`..`ENG-10`, is at most MEDIUM and never blocking, lowered rather than dropped. Similar-looking code or a missing speculative abstraction is not by itself a defect. A concrete correctness, security, integrity, resource, performance-requirement or documented-contract failure is rated by its demonstrated consequence and cites the relevant requirement or engineering rule; it is not downgraded because the same code also raises a design preference. The factory's test, red-proof and seam requirements keep their existing enforcement. A capped finding is advisory: no verdict-driven fix round acts on it, it reaches the user in the verdict's advisory list, and the approver's existing "Request changes" is the user's route to having it fixed ([ADR 0004](docs/adr/0004-judgement-call-rules-advise-they-never-block.md), refined 2026-10-25).
- **Stop on an un-runnable test command**: a repository with a test runner whose test command cannot be run is a stop, not an exemption. Both code-writing roles return a failure naming the command and its error and ride the orchestrator's existing failure policy, writing no behaviour-changing code and no third form of red proof.
- **Plan-time reason line**: the plan states a reason for each new file, new abstraction and new dependency it introduces; analyze reports a MEDIUM, non-blocking finding for a missing one.
- **Proportionate planning and review**: the plan records relevant security, integrity, failure/resource, performance, dependency, observability and delivery constraints and how to verify them. Reuse existing tools and checks. Reviewers apply the relevant shared rules within their lenses; omissions are findings only when supported by a requirement, risk or demonstrated defect. Performance optimisation needs representative before/after evidence when performance is part of the change, not an unrelated benchmark on every feature.

## Validation plan

Run end-to-end on a tiny real feature in WayUnoMcpTool. Run with `--stop-at review`, then `/factory resume <branch>` in a fresh session to confirm review starts from the paused state. Separately, kill a session mid-implement and confirm resume continues from the right task. Stop at the approver without opening a PR. Repeat for each new adapter; once two adapters exist, start a run on one harness with `--stop-at implement` and resume it on the other.

For the expanded engineering rules, also check that the plan captures applicable quality constraints, automatic fixing leaves guidance-only findings advisory, and concrete defects retain their justified severity. In particular, similar-looking code with different business meanings must not trigger mandatory abstraction; an exposed secret, duplicate consequential retry or violated performance requirement must not be dismissed as a style preference. Source/link checks and canonical renders validate packaging; they do not replace this role-behaviour validation.

### Skill routing validation

Three machine-checkable seams, exact commands in `specs/005-skill-routing/quickstart.md`:

- **Seam 1 — canonical render + dist gate**: every harness re-rendered, then `test -z "$(git status --porcelain -- dist/)"`; proves every `core/` edit (including the new shared reference) reaches all five `dist/<harness>/skill/` trees untouched by hand.
- **Seam 2 — relative-link integrity**: every relative link in the changed Markdown resolves, `references/skills.md` is linked from `SKILL.md`, `code-build.md` and `fixer.md`, and the shared reference stays under 60 lines and restates no `ENG-n` rule.
- **Seam 3 — state/question contract**: `bin/factory show` over throwaway fixtures passes `stage: "brainstorm"` and `requires_user` through verbatim, and version 1/2 fixtures still digest, with both named in `state.md`/`protocol.md`.

Agent-driven manual checks (role behaviour, not machine-checkable): three intake trials routing correctly with exactly one question on the ambiguous case; stop-after-`brainstorm` then resume with no repository writes and no repeated questions; a fast-mode run showing and waiting on the seam confirmation, not re-asking it unchanged on resume; removing `ponytail`/`tdd` stopping the affected work with setup guidance; four UI-detection trials (tokens, locale string, user-visible copy, backend-only) classifying correctly with zero UI-reviewer edits; a pre-existing saved run resuming at its recorded stage; and a document read confirming `DESIGN.md`, the shared reference and the five dependent role/orchestrator files state each precedence rule once with no conflict.

### Pen mapping validation

Check relative links and JSON examples, unchanged native-agent metadata, canonical five-harness parity/reproducibility, and state-CLI pass-through for optional `design`, protected questions, consumed repairs, and a pending design-fix reservation; retain version-1/2 and ordinary-run compatibility. The [implementation plan](docs/superpowers/plans/2026-10-25-pen-design-code-mapping-plan.md) records the packaging results. Real Pen inspection and matched application capture are separate acceptance trials: exercise scoped bootstrap/update, a shared-component conflict, stale evidence/resume, interrupted reserved repair, two-round exhaustion, and explicit exceptions from the [approved scenarios](docs/superpowers/specs/2026-10-25-pen-design-code-mapping-design.md). Static packaging checks cannot establish rendered fidelity.
