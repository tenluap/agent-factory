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

`./install.sh --harness all` installs every adapter and links the skill library described below. Start a new session afterwards so the harness picks up the skill and agents. Re-run after pulling. `--uninstall` removes the links.

The OpenCode adapter requires V2's `subagent` and `shell` tools and uses native `permissions` rules. Install with `./install.sh --harness opencode`; it verifies the factory skill and role-agent links. Start a fresh OpenCode session after installation so it loads them. If an existing non-symlink blocks a link, resolve that path and rerun the installer. If `/factory` loads but reports a missing tool, enable that capability and restart the session; if `/factory` itself is unavailable, install and reload first. OpenCode translates supported V1 agent and skill files, so existing installations are intended to keep working. See the [OpenCode migration guide](https://opencode.ai/v2/docs/migrate-v1).

## Install

`install.sh` renders `core/` with the adapter into `dist/<harness>/`, then symlinks the skill and agents into the harness's directories. The skill is the same on every harness: it carries every adapter's `harness.md` and picks its own at the start of a run (set `FACTORY_HARNESS=<name>` to force one).

Harness-neutral data lives in `${FACTORY_HOME:-~/.factory}`: pending runs, and an optional `config.json` to override models per harness:

```json
{ "models": { "claude-code": { "deep": "opus", "standard": "sonnet" }, "opencode": { "deep": "anthropic/<model-id>" } } }
```

Only Claude Code pins agent models by default (its harness requires defaults); on the other harnesses agents use the session's model until you pin them here and re-run `install.sh`, which renders a per-user copy into `${FACTORY_HOME:-~/.factory}/dist/<harness>` with your overrides merged and links that harness's skill and agent directories from it, printing the effective model per role. The committed `dist/` in the repository stays canonical: no install ever merges your configuration into it.

### Skill library

The installer links skills from this checkout's `skills/` and `${FACTORY_HOME:-~/.factory}/skills/` into the selected harness's skill root. The per-user layer wins when names match. Add a local skill with `./install.sh --harness opencode --add-skill /path/to/name`; the folder must contain a `SKILL.md` whose frontmatter name matches its folder. `factory` is reserved, and dot-prefixed folders are ignored.

Existing files, directories, and links outside the current library are preserved and reported with `skip:`. To adopt one, run the suggested `--add-skill` command, remove the original, and rerun installation. Links made from another checkout or before moving this checkout are treated as user-owned: remove the old link and rerun. Stale library links are removed automatically.

Uninstall removes library links but keeps both layers. Codex and Copilot share `~/.agents/skills`, so uninstalling either removes their shared library links. Maintainers refresh vendored skills manually by copying the upstream skill and license and updating `skills/SOURCES.md` with the source commit; no sync tool is provided.

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

A new run takes the feature through: grilling (with you, in this session), a worktree on its own branch, the SpecKit spec chain, implementation, parallel reviews, a judge verdict, fix rounds, your approval, and a PR. Progress is checkpoint-committed per stage: a checkpoint commits the spec directory plus exactly the files the role's envelope declared, and reports anything else dirty without committing it. A run that stops — deliberately or not — resumes from the recorded stage with `/factory resume <branch>`, even on a different harness. Sharing `${FACTORY_HOME}` alone does not move a run: after moving or copying a worktree, run `factory rebind <branch> --worktree <new-path>` to validate the branch and rewrite the run's stored paths.

After the PR opens, `factory drop` archives the run folder at `${FACTORY_HOME:-~/.factory}/archive/<repo-name>-<branch>/` and commits its removal from the branch. The archive is verified before removal and excludes the transient lock. Design evidence, when present, moves to `docs/design/<branch>/` in the same commit.

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

### Benchmark factory versions

`python3 tools/bench.py run --harness opencode --bench greet-001` replays a
pre-settled greeting feature in a disposable repository, stopping before the
approver gate. This spends model tokens; nothing is approved and no PR opens.
Headless drivers support `opencode` and `claude-code` only.

Score recorded runs offline with `python3 tools/bench.py score <state.json>`;
save two outputs and run `python3 tools/bench.py compare before.json after.json`.
All four named conditions must pass. Missing evidence is a failed condition,
not a successful benchmark. See [benchmark guide](docs/benchmark.md) for the
manual fallback on other harnesses and reproducible comparison steps.

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

### First run, pause, and resume

1. Install the adapter for your harness (table above), then start a fresh session.
2. In the repository to change, invoke `/factory <feature>` (Codex: `$factory <feature>`). Describe desired behaviour and constraints; the factory interviews you and confirms a brief before creating repository work.
3. Answer relay questions by ID, for example `Q1: B`, `Q1: <answer>`, or `Q1: accept`. Bare `accept` accepts unanswered recommendations only. Fast mode may accept eligible recommendations automatically; every automatic decision appears in final approval and can be vetoed.
4. Let the run plan, implement, verify, and review. At approval, choose **Approve**, **Request changes**, or **Abort**. Only approval allows push and PR creation; factory does not merge or deploy.

Pause with `--stop-at <stage>` and continue with `/factory resume <branch>` (Codex: `$factory resume <branch>`). After a crash or session change, invoke `/factory` with no arguments to discover unfinished runs, then resume one. Worktrees are siblings of the main checkout; run state and evidence live in `specs/<branch>/factory/`. If a worktree was moved, rebind it with `python3 <factory-skill>/bin/factory rebind <branch> --worktree <new-path>`; sharing `FACTORY_HOME` alone does not move worktree files.

### Feature inventory

| Capability | What it does |
|---|---|
| Harness adapters | One shared workflow renders for Claude Code, OpenCode V2, Codex, GitHub Copilot, and ZCode; adapters own harness-specific tools, permissions, paths, and model settings. |
| Idea intake | Exploratory requests can brainstorm alternatives before feature grilling; concrete requests go directly to grilling. The user confirms requirements before repository changes begin. |
| Planning | Lite chain is `specify → plan → tasks → analyze`; full adds `clarify` and `grill-with-docs`, with bounded analysis/remediation loops. Serious findings in lite automatically escalate to full. |
| Isolated delivery | Each feature gets its own branch and worktree. Stage checkpoints commit only the spec directory and role-declared files; unrelated dirty files are reported, not included. |
| Specialist roles | Spec builder, implementation agent, security/code-standards/spec-conformance reviewers, conditional UI/UX reviewers, independent review judge, and fixer. Reviews run in parallel where supported. |
| Verification and repair | Orchestrator independently runs repository build and test commands. Verdict-driven automatic fixes are capped at two rounds; failed checks, exhausted loops, and repeated agent failures halt for user direction. |
| Resumable audit trail | Versioned state persists stage, answers and decisions, waits, role ledger, verification, findings, checkpoints, and PR URL. Resume can use another installed harness on the same machine when worktree paths remain valid. |
| Pen design references | Scoped design-to-code mapping and rendered fidelity evidence apply when a Pen design is used as implementation reference; see [Pen design references](#pen-design-references). |
| Run-state CLI | `factory runs`, `show`, and `validate` inspect state; writer commands enforce validated atomic updates, checkpoints, verification, locks, rebind, and safe pending-run pruning. State files are not edited by hand. |

### Updating and removing

After pulling updates, rerun the same install command; it re-renders the selected adapter and refreshes factory-owned links. Remove factory-owned links and rendered copies with `./install.sh --harness <name> --uninstall` (use `all` for every adapter). User configuration and pending runs under `${FACTORY_HOME:-~/.factory}` are separate from rendered adapters. The installer preserves existing non-symlink files rather than replacing them; resolve any reported path conflict, then rerun installation.

## Layout

- `DESIGN.md`: every decision behind the flow and the harness model. Change it first, then the files built from it.
- `core/skills/factory/SKILL.md`: the orchestrator loop, written against neutral verbs.
- `core/skills/factory/bin/factory`: the state CLI and single writer. Read commands (`runs`, `show`, `validate`) list unfinished runs, build resume digests and report violations without reading whole `state.json` files into context; write commands (`checkpoint`, `ledger-add`, `wait-open`/`wait-close`, `answer`, `set-status`, `decisions-add`, `verify`, `rebind`, `resume`) stamp, validate, write atomically and commit — state is never hand-edited. `envelope check`, `lock take` and `prune` complete the surface.
- `core/skills/factory/references/`: verbs, run state and resume, the agent protocol, the findings shapes.
- `core/roles/`: spec-builder, code-build, five reviewers, review-judge, fixer, with neutral `tier` and `access`.
- `adapters/<harness>/`: `harness.md` (how to recognise this harness and perform each verb on it) and `adapter.json` (install paths, agent file format, fields, access, models). A new harness is one new folder here.
- `tools/render.py`: builds `dist/<harness>/` from core and an adapter.
