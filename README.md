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

## Contents

- [Features](#features)
- [Requirements](#requirements)
- [Install](#install)
- [Usage](#usage)
- [Configuration](#configuration)
- [Run-state CLI](#run-state-cli)
- [Design-to-code](#design-to-code)
- [Self-improvement](#self-improvement)
- [FACETS advisor](#facets-advisor)
- [Benchmark and conformance](#benchmark-and-conformance)
- [Layout](#layout)

## Features

| Capability | What it does |
|---|---|
| Harness adapters | One shared workflow renders for Claude Code, OpenCode V2, Codex, GitHub Copilot and ZCode. Adapters own harness-specific tools, permissions, paths, model settings and the capability tier (native subagents, headless subprocess, or inline). |
| Idea intake | The request is classified as exploration, delivery or ambiguous. Exploratory ideas go through `brainstorming` first; concrete requests go straight to grilling; ambiguous ones get one question. You confirm requirements before anything is written to the repository. |
| Grilling and relays | A relentless interview settles the design and the spec chain. Later agent questions reach you as batched relay rounds with lettered options, suggested answers and reply shortcuts. |
| Spec chain | Lite chain `specify → plan → tasks → analyze` by default; full chain adds `clarify` and `grill-with-docs` with a bounded analyze/remediate loop. CRITICAL/HIGH findings on lite escalate to full automatically. |
| Fast mode | On by default: eligible relay questions auto-accept the recommended answer, are logged, and are listed for veto at approval. Remediation questions that would overturn your decisions, and every halt, always reach you. |
| Stack detection | Preflight detects languages, frameworks, package managers, monorepo layout and UI stacks from marker files (no network, no subprocess), records the profile in run state and `profile.md`, and proposes build/test commands where the repo documents none. |
| Isolated delivery | Each feature gets its own branch and sibling worktree. Stage checkpoints commit only the spec directory and role-declared files; unrelated dirty files are reported, not included. |
| Engineering rules | Every planning, coding and reviewing role follows [`engineering.md`](core/skills/factory/references/engineering.md) (ENG-1..ENG-31): test-first with the red step recorded in the commit body, seams settled at plan time, KISS/YAGNI, deliberate error handling. The repo's own conventions win and are recorded as overrides. |
| Specialist roles | Spec builder, code builder, design-to-code (UI write role), fixer, five reviewers (security, code standards, spec conformance, and UI/UX on UI diffs), an independent review judge, and a post-PR retro. Reviews run in parallel where the harness supports it. |
| Verification and repair | The orchestrator runs build and test commands itself. Verdict-driven fix rounds are capped at two; later rounds are delta reviews of the fix only. Red builds, exhausted loops and repeated agent failures halt for your direction. |
| Time budgets | Each spawned role gets a deadline (default 300 s, configurable per role). File-writing roles stop at safe commit boundaries and return `partial`; a fresh agent resumes from disk. Three partial returns of one stage with no new commit halt the run. |
| Cost ledger and totals | Every spawn is ledgered with timing, estimated and harness-reported token usage, and any overrun. Approval and the final notice show one totals line: wall clock split into your time, agent time and overhead. |
| Per-project models | `<repo>/.factory/config.json` selects deep/standard models per project; runs cascade project → user → adapter defaults per tier, record the resolution in run state, and disclose changes on resume. |
| Resumable audit trail | Versioned `state.json` holds stage, answers, decisions, waits, ledger, issues, verification, findings, checkpoints and PR URL. A run resumes in any session, on any installed harness on the same machine. |
| Approval gate | Nothing is pushed until you choose **Approve**. The factory never merges or deploys. |
| Archive on PR | After the PR opens, the run folder is archived under `${FACTORY_HOME}/archive/` and removed from the branch; design evidence moves to `docs/design/<branch>/`. |
| Retro and improvement backlog | After every PR a retro agent proposes up to three improvement candidates from the run's issues; `/factory improve` lists them as ready-made feature descriptions. |
| Design-to-code | Pen, Figma, image or text-only design sources map to code anchors with rendered-fidelity evidence, across Avalonia and web stacks. Also usable standalone, with an auto-trigger plugin/hook. |
| Skill library | The installer links a vendored skill library, the factory's first-party skills and your own per-user skills into each harness, with collision precedence and per-harness restrictions. |
| Benchmark | Replays a pre-settled feature headlessly and scores runs, so factory versions can be compared before and after a change. |

## Requirements

- An agent harness with an adapter in `adapters/`, and Python 3 (for the renderer and the run-state CLI).
- In the target repo: git, SpecKit (`.specify/` plus its commands for your harness), and `gh` authenticated for the PR step.
- SpecKit set up for your harness: `specify init --here --ai <claude|opencode|codex|copilot>` (add `--ai-skills` outside Claude Code). For ZCode: `specify init --here --integration zcode --integration-options="--skills"`. The factory offers to do this when `.specify/` is missing.
- Required skills, resolved at preflight for every run: `grilling`, `domain-modeling`, `pr`, and — before any code-delivery work starts — `ponytail` and `tdd`. They must be in a skill directory your harness reads (`~/.agents/skills/` is read by OpenCode, Codex and Copilot; Claude Code reads `~/.claude/skills/`, which OpenCode also reads). The bundled skill library provides all of them.
- Conditionally resolved skills:
  - `brainstorming` when a run starts from an exploratory idea.
  - `impeccable` for UI reviews; the factory offers to install it the first time a run touches UI files.
  - `pen-design` when a run creates, references or updates a Pen design used as an implementation reference. Missing capabilities are reported, never installed or assumed. The `design-to-code` role reaches a Pen source only through the pen CLI, never a Pen MCP backend.
  - A `figma` skill, or an available Figma MCP inspection capability, when the design source is Figma.
- Node.js, only for the optional design-to-code trigger hook on Claude Code and Codex.

## Install

```sh
./install.sh                              # Claude Code (default)
./install.sh --harness opencode           # one harness
./install.sh --harness all                # every adapter
./install.sh --harness opencode --add-skill /path/to/my-skill
./install.sh --harness <name|all> --uninstall
python3 tools/render.py --list            # available harnesses
```

`./install.sh` renders `core/` with the adapter into `${FACTORY_HOME:-~/.factory}/dist/<harness>/`, merging any model overrides from your config, then symlinks the skill, skills and agents into the harness's directories and prints the effective model per role. The repository's own `dist/` stays canonical: no install ever merges your configuration into it. The orchestrator skill is the same on every harness: it carries every adapter's `harness.md` and picks its own at the start of a run (set `FACTORY_HARNESS=<name>` to force one).

A config file that does not parse aborts the install before anything is rendered or linked. An explicitly configured `FACTORY_HOME` must exist and be writable; the default `~/.factory` is created when missing.

### Harness notes

- **OpenCode** requires V2's `subagent` and `shell` tools and uses native `permissions` rules. The installer verifies the skill and role-agent links and also links the design-to-code trigger plugin into OpenCode's `plugins/` directory. If an existing non-symlink blocks a link, resolve that path and rerun. If `/factory` loads but reports a missing tool, enable that capability and restart; if `/factory` is unavailable, install and reload first. OpenCode translates V1 agent and skill files, so existing installations keep working; see the [OpenCode migration guide](https://opencode.ai/v2/docs/migrate-v1).
- **Claude Code and Codex** get the design-to-code trigger as a `UserPromptSubmit` hook script copied to `${FACTORY_HOME}/bin/design-to-code-hook.mjs`. The installer never edits your harness config; it prints the snippet to paste into `~/.claude/settings.json` or `~/.codex/hooks.json`.
- **Codex, Copilot and ZCode** cannot take a model at spawn time: they run on the installed (rendered) model selections.

### Skill library

The installer links three layers of skills into the selected harness's skill root:

1. **Per-user** skills in `${FACTORY_HOME:-~/.factory}/skills/` — they win on name collision and always link to every harness.
2. **First-party** skills rendered from `core/skills/` (every folder with a `SKILL.md` except `factory`) into `dist/<harness>/skills/` ([ADR 0012](docs/adr/0012-first-party-skills-live-in-core-skills.md)).
3. **Vendored** skills in this checkout's `skills/`, with provenance in `skills/SOURCES.md` — including `grilling`, `domain-modeling`, `pr`, `ponytail`, `tdd`, `brainstorming`, `impeccable`, `design-to-code` and `pen-design`.

Add a local skill with `--add-skill /path/to/name`; the folder must contain a `SKILL.md` whose frontmatter name matches its folder. `factory` is reserved, and dot-prefixed folders are ignored.

A `skills/SOURCES.md` row may restrict a vendored skill to specific harnesses with the optional sixth `harnesses` column: a comma-separated list of adapter names (`claude-code`, `codex`, `copilot`, `opencode`, `zcode`). An empty cell links the skill into every harness. An excluded skill has its existing link removed and is reported with `skip:`.

After every non-uninstall run, the installer refreshes a browsing mirror of the vendored library in `${FACTORY_HOME}/skills/`: one symlink per `skills/` folder. Mirror links are not per-user skills and never override vendored links; stale mirror links are pruned. A non-symlink, or a symlink pointing elsewhere, in the per-user layer is a real per-user skill and is skipped with an adoption hint.

Existing files, directories and links outside the library are preserved and reported with `skip:`. To adopt one, run the suggested `--add-skill` command, remove the original, and rerun. Links made from another checkout are treated as user-owned: remove the old link and rerun. Stale library links are removed automatically. Uninstall removes library links but keeps all layers; Codex and Copilot share `~/.agents/skills`, so uninstalling either removes their shared links. Maintainers refresh vendored skills by copying the upstream skill and license and updating `skills/SOURCES.md` with the source commit.

### Updating and removing

After pulling, rerun the same install command; it re-renders the adapter and refreshes factory-owned links. `./install.sh --harness <name> --uninstall` (or `all`) removes factory-owned links, the OpenCode plugin link and rendered copies. Your configuration, pending runs, archives and backlogs under `${FACTORY_HOME}` are kept.

## Usage

Start a run from the repo you want the feature built in. On Claude Code, OpenCode, Copilot and ZCode the skill is `/factory`; on Codex it is `$factory`.

```
/factory                                      list unfinished runs; pick one to resume, or start a new run
/factory <feature description>                start a new run — lite chain and fast mode by default
/factory <feature> --full                     start on the full chain instead
/factory <feature> --no-fast                  ask every relay question instead of auto-accepting
/factory <feature> --cruise                   run unattended to the approver; never publishes without your Approve
/factory <feature> --stop-at review           pause cleanly before the review stage
/factory resume <branch>                      resume that run from where it stopped (any session, any harness)
/factory adopt <branch|spec_dir> [--stage <s>]  continue a SpecKit spec started outside factory on its own branch (preview first with `factory adopt <src> --dry-run`)
/factory resume <branch> --full --no-fast     resume, switching mode before the stage restarts
/factory resume <branch> --cruise             resume with cruise on: the open relay round is filled, then it runs to the approver
/factory init                                 seed <repo>/.factory/config.json with effective model defaults + README
/factory improve                              list ready improvement backlogs with suggested feature text
```

### Flags

Flags follow the feature description or `resume <branch>` and may combine; when both flags of a pair appear, the last one wins. An unknown flag or invalid stage is never ignored: the factory names it and asks you to fix or drop it.

| Flag | Effect |
|---|---|
| `--lite` | Pin the **lite chain**: specify → plan → tasks → analyze, one pass, no loop. Clarify and grill-with-docs are skipped — the top grilling captures what they would have. Any CRITICAL/HIGH analyze finding escalates to the full chain automatically. **Default.** |
| `--full` | Pin the **full chain**: specify → clarify → grill-with-docs → plan → tasks → analyze, with the analyze loop (max 2 passes). |
| `--fast` | Relay rounds auto-accept the agent's recommended answer. Each accept is logged and listed on the approver screen for veto. Never automated: questions a remediation defers to you, protected design decisions, and every halt. Grilling is always with you unless `--cruise` is on (see that row; cruise is the only automation of these). **Default.** |
| `--no-fast` | Every relay round reaches you for an answer. Conflicts with `--cruise` (exit 5). |
| `--cruise` | Opt-in cruise mode: implies `--fast`; answers relay questions, grilling, setup offers and analyze exhaustion itself, using recorded cruise overrides shown on the approver screen. Stops at the approver and never opens a PR without your Approve. |
| `--no-cruise` | Turn cruise off again (on resume, or to override a stored cruise). |
| `--stop-at <stage>` | Pause cleanly before that stage and end the turn. Valid stages: `specify`, `clarify`, `grill-with-docs`, `plan`, `tasks`, `analyze`, `implement`, `review`, `approver`, `pr`. A stage the chain skips never triggers. |

Grilling's closing summary names the chain in effect and recommends `full` when the feature's size calls for it; object once to flip it.

### The run, stage by stage

1. **Route** — list runs, resume, `init`, `improve`, or classify a new request as exploration, delivery or ambiguous.
2. **Preflight** — pick the harness adapter, check required capabilities, resolve models (project → user → adapter) and skills, detect the stack profile, confirm build/test commands, and activate design context when a design source is present. Nothing partial is started if a requirement is missing.
3. **Brainstorm** (exploration only) — alternatives and trade-offs, saved as a brief.
4. **Grill** — interview until shared understanding; writes `brief.md` and settles the chain.
5. **Worktree** — a numbered feature branch and a sibling worktree at `<repo>/../<repo-name>-factory/<branch>`; run state moves to `specs/<branch>/factory/state.json`.
6. **Spec** — one fresh `spec-builder` per SpecKit stage, with checkpoints and the analyze/remediate rules for the chosen chain.
7. **Implement** — `code-build` (and `design-to-code` for `[UI]` tasks) works through `tasks.md`, committing per task; the orchestrator then runs build and tests itself and gives a red build one repair attempt.
8. **Review** — parallel reviewers, then the `review-judge` merges, dedupes and verifies findings into one verdict. Confirmed blockers go to the `fixer`, up to two rounds.
9. **Approver** — your decision (below).
10. **PR** — push, PR body written with the `pr` skill, `gh pr create`, retro, archive, final push and totals.

Progress is checkpoint-committed per stage. A checkpoint commits the spec directory plus exactly the files the role declared, and reports anything else dirty without committing it.

### What the run asks of you

- **Grilling** at the start: a relentless interview until you confirm shared understanding. Grilling and relays share one chat layout: 🧭 round progress, lettered options with descriptions, ✨ AI-suggested markers, and 💡 suggested answers with a rationale and reply shortcut.
- **Relays**: each round shows every question whose prerequisites are settled; dependent questions wait for later rounds. Reply `Q7: B`, `Q7: <your answer>` or `Q7: accept`; bare `accept` takes only unanswered suggestions and keeps your explicit answers. Choice questions include 💬 Something else; open-ended questions accept free text.
- **Halts**: trouble always reaches you — CRITICAL/HIGH findings left after 2 loop passes, a build that stays red, an agent that fails twice, a stage stalled by three partial returns. Your answer resumes, redirects or aborts.
- **The approver**: summary, diff stat, spec link, judge verdict, what each fix round fixed, advisory and unresolved findings, run totals, the capability tier when it is not native subagents, UI-review coverage on UI diffs, and (with fast mode) every auto-accepted answer for veto.
  - **Approve** opens the PR.
  - **Request changes** sends your text to the `fixer`, re-verifies and re-reviews (no round cap), then returns to approval.
  - **Abort** marks the run aborted and keeps the worktree.

### First run, pause and resume

1. Install the adapter for your harness, then start a fresh session.
2. In the repository to change, invoke `/factory <feature>` (Codex: `$factory <feature>`). Describe the desired behaviour and constraints; the factory interviews you and confirms a brief before creating any repository work.
3. Answer relay questions by ID. Fast mode may accept eligible recommendations automatically; every automatic decision appears at approval and can be vetoed.
4. Let the run plan, implement, verify and review. Only **Approve** allows the push and PR.

Pause with `--stop-at <stage>` and continue with `/factory resume <branch>`. After a crash or session change, invoke `/factory` with no arguments to discover unfinished runs (worktree runs and pending runs from `${FACTORY_HOME}/pending/`), then resume one. Resume rechecks models, skills and the stack profile, discloses anything that changed, and restarts the recorded stage from its beginning while keeping committed progress.

`/factory adopt <branch|spec_dir>` takes over a spec that was written outside factory: it previews the source, asks you to confirm the entry stage (at most `analyze`), then creates the worktree and one `factory: adopt <branch>` commit; nothing is written if the preview refuses.

Sharing `${FACTORY_HOME}` alone does not move a run. After moving or copying a worktree, run `python3 <factory-skill>/bin/factory rebind <branch> --worktree <new-path>` to validate the branch and rewrite the run's stored paths.

### After the PR

The orchestrator runs the retro (see [Self-improvement](#self-improvement)), then `factory drop` archives the run folder at `${FACTORY_HOME}/archive/<repo-name>-<branch>/` and commits its removal from the branch. The archive is verified before removal and excludes the transient lock. Design evidence moves to `docs/design/<branch>/` in the same commit. If the session is interrupted between opening the PR and the final push, run `python3 <factory-skill>/bin/factory drop` and then `git push` from the worktree.

## Configuration

### Environment

| Variable | Meaning |
|---|---|
| `FACTORY_HARNESS` | Force a specific adapter's `harness.md` in preflight instead of auto-recognition. |
| `FACTORY_HOME` | Harness-neutral home (default `~/.factory`): `pending/`, `archive/`, `improvements/`, `dist/`, `skills/`, `bin/`, `config.json`, and the optional `facets-profile.md`. Every harness shares it. |

### User config: `${FACTORY_HOME}/config.json`

```json
{
  "models": {
    "claude-code": { "deep": "opus", "standard": "sonnet" },
    "opencode": { "deep": "anthropic/<model-id>" }
  },
  "budget": {
    "default_s": 300,
    "roles": { "code-build": 900, "spec-builder": 600 }
  }
}
```

- **`models`** — per-harness overrides for the two tiers. Deep roles: `spec-builder`, `review-judge`, `facets-advisor`; every other role is standard. Claude Code, Codex and OpenCode pin agent models by default; Copilot and ZCode inherit the session model. The defaults in `adapters/<harness>/adapter.json` are authoritative; re-run `install.sh` after changing overrides. An empty string inherits the session model.
- **`budget`** — seconds per spawned role. `default_s` applies to every role without its own entry; a missing or invalid value falls back to 300 and never fails a run. Reviewers and the judge are never stopped (their overruns are only recorded).

### Per-project models: `<repo>/.factory/config.json`

Same schema as the user-level `models` block. At the start of every run the orchestrator resolves **project → user → adapter defaults** per tier and passes each spawned agent its tier's resolved model; the resolution is recorded in run state and changes are disclosed on resume.

- `/factory init` seeds the project config with every harness's effective values (each labelled with its source) plus a `config.README.md` documenting schema, precedence and restore steps. It refuses when a config already exists.
- `python3 <factory-skill>/bin/factory models [--json]` prints the effective per-role cascade with sources for the current repo.
- A malformed project or user config (bad JSON, unknown harness or tier key, control-character or oversized values, symlinked files) stops the run naming the file and the fix. Delete or fix the entry to fall back to the next layer.
- Codex, Copilot and ZCode cannot take a model at spawn time: their preflight discloses that project and user selections cannot apply and continues on the installed selections.
- An unavailable model, when the adapter can prove it from a complete inventory, stops startup with the exact ID, its config source and correction steps. Models are never silently replaced.

## Run-state CLI

`<factory-skill>/bin/factory` (stdlib Python 3) is the run's **single writer**: every state change goes through it, is time-stamped, validated, written atomically and committed. State files are never hand-edited, and there is no manual fallback. Run `python3 <factory-skill>/bin/factory` with no arguments for full usage.

| Group | Commands |
|---|---|
| Read | `runs`, `show <run>`, `validate <run>\|--all`, `resume <run>`, `budget <role>`, `models [--json]`, `improvements`, `detect` |
| Run state | `checkpoint`, `analyze-record`, `profile-record`, `ledger-add`, `issue-add`, `wait-open`/`wait-close`, `answer`, `set-status`, `decisions-add`, `verify`, `models-record` |
| Lifecycle | `init`, `drop`, `rebind <run> --worktree <path>`, `prune [--dry-run\|--delete]`, `lock take <run> [--force]` |
| Backlog | `improvements claim <name>`, `improvements add --from <file> --run <branch>` |
| Agents | `envelope check <file>` validates a role's final fenced `json` block |

`<run>` is a branch name (worktree runs) or a pending file's name. Exit codes: 0 success, 1 no run or refused, 2 not a git repository, 3 ambiguous name, 4 recorded worktree gone, 5 usage error. Writes refuse under a live lock held by another session.

## Design-to-code

When a run has a UI design source — a Pen (pen.dev `.pen`) file, a Figma node, an image, or a text-only description against existing code — the factory activates design context during intake and follows the [design-code mapping contract](core/skills/factory/references/design-code-mapping.md), with framework guidance for [Avalonia](core/skills/factory/references/design-code-mapping-avalonia.md) and [web stacks](core/skills/factory/references/design-code-mapping-web.md). The detected stack profile seeds the framework choice; an ambiguous stack becomes one relay question.

- `docs/design-code-map.json` (or an existing equivalent) maps scoped design nodes, components and instances to stable code anchors. Later requests such as "update the design" resolve the saved target; ambiguous targets are clarified. Editing the design source requires an explicit request.
- `[UI]` tasks in `tasks.md` are routed to the `design-to-code` role in contiguous ranges; other tasks go to `code-build`.
- The design governs visual decisions. Mapped implementation requires current build/runtime, mapping and rendered-comparison evidence. Sources, exports, captures and metadata live under `specs/<branch>/factory/design/` during the run.
- Design repairs share the two automatic fix rounds. Missing or failed required evidence leaves the work partial or blocked; only an explicit scoped exception from you lets the run proceed, and it stays labelled unverified. Ordinary approval and fast mode never infer that exception.
- Existing projects bootstrap the requested scope only; nothing migrates the whole application.

Outside factory runs, `design-to-code` is also a standalone main agent and skill for implementing, reviewing or QA-checking UI in Avalonia, MAUI, Blazor, React, Next.js or HTML/JS/CSS. The OpenCode plugin and the Claude Code/Codex hook arm it once per session when a prompt mentions `ui`, `ux`, `.pen`, `pen.dev` or `figma`; they stay inert inside factory runs.

## Self-improvement

Everything that goes wrong in a run — retries, agent failures, overruns, partial returns, failed verification, halts — is recorded as an issue in run state.

- When a run reaches `pr-open` or `aborted`, the writer exports its issues and totals to `${FACTORY_HOME}/improvements/<repo-name>-<branch>.json`. The backlog never exists before its run ends.
- After the PR opens, a `retro` agent reads the run's state, analyze reports and verdicts and proposes up to three ranked candidates, each with evidence and a one-line feature description. Candidates are deduplicated against existing ready entries. A failed retro is retried once and otherwise skipped; it never halts the run.
- `/factory improve` lists ready backlogs with kind counts and a `suggested_feature`. Starting an improvement run stays manual: submit the chosen text with `/factory <feature>`. `factory improvements claim <name>` marks a backlog taken.

## FACETS advisor

`facets-advisor` is a main agent you start directly (it is never spawned by `/factory`). It scores projects or income options on the six-facet FACETS checklist using cited web research, ranks them (pursue / investigate / drop) and discusses trade-offs. It keeps your constraints in `${FACTORY_HOME}/facets-profile.md`, which it writes only after you confirm. See [`facets.md`](core/skills/factory/references/facets.md).

## Benchmark and conformance

```sh
python3 tools/bench.py run --harness opencode --bench greet-001
python3 tools/bench.py score <state.json>
python3 tools/bench.py compare before.json after.json
```

`run` replays a pre-settled greeting feature (`conformance/bench/greet-001/`) in a disposable repository, stopping before the approver gate. It spends model tokens; nothing is approved and no PR opens. Headless drivers support `opencode` and `claude-code` only. All four named conditions must pass, and missing evidence is a failed condition. See the [benchmark guide](docs/benchmark.md) for the manual fallback on other harnesses.

`conformance/` also holds a fixture repo and per-harness golden-run transcripts. CI runs the full test suite (`python3 -m unittest discover -s tools`), renders all five harnesses, and checks installer syntax.

## Layout

- `DESIGN.md`: every decision behind the flow and the harness model. Change it first, then the files built from it. `CONTEXT.md` holds the domain glossary; `docs/adr/` the architecture decisions.
- `core/skills/factory/SKILL.md`: the orchestrator loop, written against neutral verbs (`SPAWN`, `SPAWN_PARALLEL`, `ASK`, `NOTIFY`, `RESOLVE`, `SHELL`, `WEB_SEARCH`, `WEB_FETCH`).
- `core/skills/factory/bin/factory`: the run-state CLI and single writer.
- `core/skills/factory/references/`: verbs, run state and resume, the agent protocol, findings shapes, engineering rules, design-code mapping and the FACETS checklist.
- `core/roles/`: twelve roles with neutral `tier` and `access` — spec-builder, code-build, design-to-code, fixer, five reviewers, review-judge, retro, and facets-advisor.
- `adapters/<harness>/`: `harness.md` (how to recognise the harness and perform each verb on it) and `adapter.json` (install paths, agent file format, fields, access, models). A new harness is one new folder here.
- `skills/`: the vendored skill library and `SOURCES.md`.
- `plugins/`: the design-to-code trigger (OpenCode plugin and Claude Code/Codex hook).
- `tools/render.py`: builds `dist/<harness>/` from core and an adapter. `tools/bench.py`: the benchmark. `tools/tests/`: the test suite.
- `conformance/`: benchmark fixtures and golden runs.
- `specs/`: the SpecKit specs for each factory feature.
