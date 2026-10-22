# agent-factory

A software factory for coding-agent harnesses. Run `/factory <feature>` in any repo with [SpecKit](https://github.com/github/spec-kit) installed, and the session becomes an orchestrator that takes the feature through grilling, the SpecKit spec flow, implementation, parallel reviews and your approval to a pull request. Runs are resumable: run `/factory` with no arguments to list unfinished runs.

The flow is harness-neutral; each harness gets a thin adapter in `adapters/`.

| Harness | Install | Start a run | Agents installed to |
|---|---|---|---|
| Claude Code | `./install.sh` | `/factory <feature>` | `~/.claude/agents/factory-*.md` |
| OpenCode | `./install.sh --harness opencode` | `/factory <feature>` | `~/.config/opencode/agents/factory-*.md` |
| Codex | `./install.sh --harness codex` | `$factory <feature>` | `~/.codex/agents/factory_*.toml` |
| GitHub Copilot (CLI, VS Code agent mode) | `./install.sh --harness copilot` | `/factory <feature>` | `~/.copilot/agents/factory-*.agent.md` |

`./install.sh --harness all` installs every adapter. Start a new session afterwards so the harness picks up the skill and agents. Re-run after pulling. `--uninstall` removes the links.

## Install

`install.sh` renders `core/` with the adapter into `dist/<harness>/`, then symlinks the skill and agents into the harness's directories. The skill is the same on every harness: it carries every adapter's `harness.md` and picks its own at the start of a run (set `FACTORY_HARNESS=<name>` to force one).

Harness-neutral data lives in `${FACTORY_HOME:-~/.factory}`: pending runs, and an optional `config.json` to override models per harness:

```json
{ "models": { "claude-code": { "deep": "opus", "standard": "sonnet" }, "opencode": { "deep": "anthropic/<model-id>" } } }
```

Only Claude Code pins agent models by default; on the other harnesses agents use the session's model until you pin them here and re-run `install.sh`.

## Requirements

- An agent harness with an adapter in `adapters/`, and Python 3 for the renderer.
- In the target repo: git, SpecKit (`.specify/` plus its commands for your harness), and `gh` authenticated for the PR step.
- Skills: `grilling`, `domain-modeling`, `pr`, in a skill directory your harness reads (`~/.agents/skills/` is read by OpenCode, Codex and Copilot; Claude Code reads `~/.claude/skills/`, which OpenCode also reads).
- SpecKit set up for your harness: `specify init --here --ai <claude|opencode|codex|copilot>` (add `--ai-skills` outside Claude Code). The factory offers to do this when `.specify/` is missing.
- `impeccable` for UI reviews; the factory offers to install it the first time a run touches UI files.

## Layout

- `DESIGN.md`: every decision behind the flow and the harness model. Change it first, then the files built from it.
- `core/skills/factory/SKILL.md`: the orchestrator loop, written against neutral verbs.
- `core/skills/factory/references/`: verbs, run state and resume, the agent protocol, the findings shapes.
- `core/roles/`: spec-builder, code-build, five reviewers, review-judge, fixer, with neutral `tier` and `access`.
- `adapters/<harness>/`: `harness.md` (how to recognise this harness and perform each verb on it) and `adapter.json` (install paths, agent file format, fields, access, models). A new harness is one new folder here.
- `tools/render.py`: builds `dist/<harness>/` from core and an adapter.
