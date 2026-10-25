# agent-factory

A software factory for coding-agent harnesses. Run `/factory <feature>` in any repo with [SpecKit](https://github.com/github/spec-kit) installed, and the session becomes an orchestrator that takes the feature through grilling, the SpecKit spec flow, implementation, parallel reviews and your approval to a pull request. Runs are resumable: run `/factory` with no arguments to list unfinished runs.

The flow is harness-neutral; each harness gets a thin adapter in `adapters/`.

| Harness | Install | Start a run | Agents installed to |
|---|---|---|---|
| Claude Code | `./install.sh` | `/factory <feature>` | `~/.claude/agents/factory-*.md` |
| OpenCode V2 | `./install.sh --harness opencode` | `/factory <feature>` | `~/.config/opencode/agents/factory-*.md` |
| Codex | `./install.sh --harness codex` | `$factory <feature>` | `~/.codex/agents/factory_*.toml` |
| GitHub Copilot (CLI, VS Code agent mode) | `./install.sh --harness copilot` | `/factory <feature>` | `~/.copilot/agents/factory-*.agent.md` |
| ZCode | `./install.sh --harness zcode` | `/factory <feature>` | `~/.zcode/agents/factory-*.md` |

`./install.sh --harness all` installs every adapter. Start a new session afterwards so the harness picks up the skill and agents. Re-run after pulling. `--uninstall` removes the links.

The OpenCode adapter targets V2's `subagent` and `shell` tools and native `permissions` rules. OpenCode translates supported V1 agent and skill files, so existing installations are intended to keep working. Re-run `./install.sh --harness opencode` after pulling to use the V2 adapter, then start a new session. See the [OpenCode migration guide](https://opencode.ai/v2/docs/migrate-v1).

## Install

`install.sh` renders `core/` with the adapter into `dist/<harness>/`, then symlinks the skill and agents into the harness's directories. The skill is the same on every harness: it carries every adapter's `harness.md` and picks its own at the start of a run (set `FACTORY_HARNESS=<name>` to force one).

Harness-neutral data lives in `${FACTORY_HOME:-~/.factory}`: pending runs, and an optional `config.json` to override models per harness:

```json
{ "models": { "claude-code": { "deep": "opus", "standard": "sonnet" }, "opencode": { "deep": "anthropic/<model-id>" } } }
```

Only Claude Code pins agent models by default; on the other harnesses agents use the session's model until you pin them here and re-run `install.sh`.

## Usage

Start a run from the repo you want the feature built in. On Claude Code, OpenCode and Copilot the skill is `/factory`; on Codex it is `$factory`.

```
/factory                                      list unfinished runs; pick one to resume, or start a new run
/factory resume <branch>                      resume that run from where it stopped (any session, any harness)
/factory <feature description>                start a new run — lite chain and fast mode by default
/factory <feature> --full                     start on the full chain instead
/factory <feature> --no-fast                  ask every relay question instead of auto-accepting
/factory <feature> --stop-at review           pause cleanly before the review stage
/factory resume <branch> --full --no-fast     resume, switching mode before the stage restarts
```

A new run takes the feature through: grilling (with you, in this session), a worktree on its own branch, the SpecKit spec chain, implementation, parallel reviews, a judge verdict, fix rounds, your approval, and a PR. Progress is checkpoint-committed per stage, so a run that stops — deliberately or not — resumes from the recorded stage with `/factory resume <branch>`, even from a different harness or machine that shares `${FACTORY_HOME}`.

### Flags

Flags follow the feature description or `resume <branch>` and may combine; when both flags of a pair appear, the last one wins:

| Flag | Effect |
|---|---|
| `--lite` | Pin the **lite chain**: specify → plan → tasks → analyze, one pass, no loop. The two interactive spec stages (clarify, grill-with-docs) are skipped — the top grilling captures what they would have. Any CRITICAL/HIGH analyze finding escalates the run to the full chain automatically. **This is the default.** |
| `--full` | Pin the **full chain**: specify → clarify → grill-with-docs → plan → tasks → analyze, with the analyze loop (max 2). |
| `--fast` | Relay rounds auto-accept the agent's recommended answer. Each accept is logged; the approver screen lists them all for veto before you approve. Never automated: questions a remediation defers to you (it would overturn one of your decisions), and every halt — loop exhaustion, red build, agent failure. Grilling at the top is always with you. **This is the default.** |
| `--no-fast` | Turn fast mode off: every relay round reaches you for an answer. |
| `--stop-at <stage>` | Pause the run cleanly before that stage and end the turn; resume later. Valid stages: `specify`, `clarify`, `grill-with-docs`, `plan`, `tasks`, `analyze`, `implement`, `review`, `approver`, `pr`. |

The defaults are `--lite --fast`: a run with no flags uses the lite chain and auto-accepts relay rounds. Grilling's closing summary names the chain in effect and your confirmation covers it — object once to flip it to `full`. Flags also work on `resume <branch>` and update the run before the stage restarts; a `--stop-at` stage the chain skips (say `clarify` on a lite run that never escalates) simply never triggers.

### What the run asks of you

- **Grilling** at the start: a relentless interview until you confirm shared understanding. The chain choice is settled here. Grilling and relays share the same emoji-rich chat layout: 🧭 round progress, lettered options with descriptions, ✨ AI suggested markers, and 💡 suggested answers with a rationale and reply shortcut.
- **Relays**: each round shows the whole frontier of questions whose prerequisites are settled; dependent questions wait for later rounds. Reply `Q7: B`, `Q7: <your answer>`, or `Q7: accept`; bare `accept` takes only unanswered suggestions and preserves your explicit answers. Choice questions include 💬 Something else; open-ended questions accept free text. Under fast mode (the default; `--no-fast` turns it off), eligible relay questions auto-accept; remediation questions still reach you. Existing saved runs use the new layout with their answers and IDs preserved.
- **Halts**: trouble always reaches you — CRITICAL/HIGH findings left after 2 loop passes, a build that stays red, an agent that fails twice. Your answer resumes, redirects, or aborts.
- **The approver**: summary, diff stat, spec link, judge verdict, what each fix round fixed, remaining advisory findings, and (with fast mode on) the auto-accepted answers. Approve opens the PR; request changes sends it back through a fix round; abort keeps the worktree.

### Environment

| Variable | Meaning |
|---|---|
| `FACTORY_HARNESS` | Force a specific adapter's `harness.md` in preflight instead of auto-recognition. |
| `FACTORY_HOME` | Where pending runs and `config.json` live (default `~/.factory`). |

## Requirements

- An agent harness with an adapter in `adapters/`, and Python 3 (for the renderer and the run-state CLI).
- In the target repo: git, SpecKit (`.specify/` plus its commands for your harness), and `gh` authenticated for the PR step.
- Required skills, resolved at preflight for every run: `grilling`, `domain-modeling`, `pr`, `ponytail`, `tdd` (the last two before any code-delivery work starts), in a skill directory your harness reads (`~/.agents/skills/` is read by OpenCode, Codex and Copilot; Claude Code reads `~/.claude/skills/`, which OpenCode also reads).
- SpecKit set up for your harness: `specify init --here --ai <claude|opencode|codex|copilot>` (add `--ai-skills` outside Claude Code). The factory offers to do this when `.specify/` is missing. For ZCode: `specify init --here --integration zcode --integration-options="--skills"`.
- Conditionally resolved skills, only when relevant: `brainstorming` when a run starts from an exploratory idea rather than a settled feature, and `impeccable` for UI reviews — the factory offers to install the latter the first time a run touches UI files.
- `pen-design` when a run creates, references, or updates a Pen design intended as an implementation reference. Missing skill/backend inspection or rendering capabilities are reported explicitly; they are not installed or assumed automatically.

### Pen design references

Pen reference work automatically follows the [design-code mapping contract](core/skills/factory/references/design-code-mapping.md), across frameworks, with [Avalonia guidance](core/skills/factory/references/design-code-mapping-avalonia.md) for that stack. The repository's `docs/design-code-map.json` (or existing equivalent) maps scoped design nodes, components, and instances to stable code anchors. Later requests such as “update the design” resolve the saved target and update code from the design; ambiguous targets are clarified. Editing the design source requires an explicit request.

The reference governs visual decisions. Mapped implementation requires current build/runtime, mapping, and rendered-comparison evidence, independently of optional UI polish. Scoped sources, exports, captures, and metadata live under `specs/<branch>/factory/design/`; the permanent map points to them. Design-only tasks record source/targets until code implementation begins. Existing projects bootstrap the requested scope rather than migrating the whole application.

Design repairs share the existing two automatic fix rounds. Missing or failed required evidence leaves the work partial/blocked; an explicit scoped exception can permit proceeding while retaining its unverified status. Ordinary approval and fast mode do not infer that exception. These are factory orchestration instructions, not a background synchronizer for standalone Pen invocations.

## Layout

- `DESIGN.md`: every decision behind the flow and the harness model. Change it first, then the files built from it.
- `core/skills/factory/SKILL.md`: the orchestrator loop, written against neutral verbs.
- `core/skills/factory/bin/factory`: read-only state CLI (`runs`, `show`); the orchestrator lists unfinished runs and builds resume digests with it instead of reading whole `state.json` files into context.
- `core/skills/factory/references/`: verbs, run state and resume, the agent protocol, the findings shapes.
- `core/roles/`: spec-builder, code-build, five reviewers, review-judge, fixer, with neutral `tier` and `access`.
- `adapters/<harness>/`: `harness.md` (how to recognise this harness and perform each verb on it) and `adapter.json` (install paths, agent file format, fields, access, models). A new harness is one new folder here.
- `tools/render.py`: builds `dist/<harness>/` from core and an adapter.
