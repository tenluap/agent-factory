# Harness-agnostic factory: design and plan

Oct 22, 2026 · @Paul · Status: **proposal, waiting for Paul's go-ahead.** Nothing has been changed in `claude-factory` yet.

## Summary

The factory's *logic* is already almost harness-neutral: the flow, the state file, the envelope, the findings shapes and the reviewer lenses are all plain Markdown and JSON. What ties it to Claude Code is a thin layer: where files are installed, how subagents are declared and spawned, `SendMessage`, `AskUserQuestion`, `PushNotification`, model names, and a handful of hard-coded `~/.claude/...` paths.

The proposal is to split the repo into a **portable core** (the orchestrator skill, the role prompts, the references) and **thin per-harness adapters** (one `harness.md` describing how to do each primitive, plus generated agent files in that harness's native format). The orchestrator is written against six neutral verbs instead of Claude tool names, and reads the active harness's `harness.md` at the start of a run.

The one real behaviour change: spec-builder becomes **stateless per stage** (a fresh agent each turn, given state and relay answers), which removes the dependency on `SendMessage`. The factory's resume path already works this way, so this mostly reuses existing design.

## What is Claude-specific today

| Where | Coupling | Portable replacement |
| --- | --- | --- |
| `install.sh` | Symlinks into `~/.claude/skills` and `~/.claude/agents` | `install.sh --harness <name>` links into that harness's dirs |
| `agents/*.md` frontmatter | Claude subagent format: `tools: Read, Edit…`, `model: opus/sonnet` | Role bodies with neutral metadata (`tier`, `access`); adapter renders native frontmatter |
| Agent bodies | Hard-coded `~/.claude/skills/factory/references/...` | `<F>/references/...`, with `<F>` passed in every spawn prompt |
| SKILL.md step 4 | `SendMessage` to drive spec-builder turn by turn | Fresh spawn per stage (state + relay answers in the prompt) |
| SKILL.md 1.4, policies | `ToolSearch`, `PushNotification` | `NOTIFY` verb, optional; no-op where absent |
| SKILL.md step 7 | `AskUserQuestion` | `ASK` verb; plain chat question where no picker exists |
| SKILL.md 6.3 | "spawn in parallel in one message" | `SPAWN_PARALLEL` verb; sequential fallback |
| SKILL.md 1.3 | Skill search in `.claude/skills`, `~/.claude/skills`, `~/.claude/plugins` | Adapter supplies the search path list |
| SpecKit | `specify init --ai claude`; resolves `speckit-*` **skills** | `--ai <harness>`; resolver maps `speckit.<stage>` to wherever SpecKit installed that harness's command/prompt file |
| impeccable | `--providers=claude` | `--providers=<adapter value>` |
| state.md | Pending dir `~/.claude/factory/pending/` | `${FACTORY_HOME:-~/.factory}/pending/` |
| SKILL.md 8.5 | Desktop Auto-fix offer | Claude-only optional extra in the Claude adapter |

Already portable and kept as is: the flow and every decision in DESIGN.md, `state.json` (stored in the worktree), the envelope and "final fenced `json` block" convention, findings and verdict shapes, git/gh/worktree commands, CLAUDE.md / AGENTS.md command discovery, and all reviewer lenses.

## Proposed layout

```
factory/                      (repo; rename from claude-factory is an open question)
  DESIGN.md                   source of truth, gains a "Harness model" section
  core/
    skills/factory/
      SKILL.md                orchestrator, written against the neutral verbs
      references/             state.md, protocol.md, findings.md, verbs.md (new)
    roles/                    spec-builder.md, code-build.md, 5 reviewers, judge, fixer
    roles.yaml                role -> tier (deep|standard), access (read|write), description
  adapters/
    claude-code/  harness.md  adapter.yaml
    opencode/     harness.md  adapter.yaml
    codex/        harness.md  adapter.yaml
    copilot/      harness.md  adapter.yaml
  tools/render                generates dist/<harness>/ from core + adapter
  install.sh                  --harness <name> [--uninstall]
```

- **`SKILL.md` stays one file for every harness.** Agent Skills (`SKILL.md` with frontmatter) is now read natively by Claude Code, Codex, OpenCode and GitHub Copilot, so the orchestrator itself needs no translation. Its only harness-specific frontmatter (`disable-model-invocation`, `argument-hint`) is ignored where unsupported; where a harness invokes skills only via a slash command or prompt file, the adapter adds a one-line command that loads the skill.
- **`harness.md`** is read by the orchestrator in preflight. It says, for that harness, how to perform each verb, where skills and SpecKit commands live, the impeccable provider name, and which capability tier applies.
- **`adapter.yaml`** drives rendering: install dirs, agent file format, model for each tier, tool names for each access level.
- **Role files** are the current agent bodies minus frontmatter. The renderer wraps each one in native frontmatter (Claude subagent `.md`, OpenCode agent `.md` with `mode: subagent`, Copilot `.agent.md`, Codex agent/profile) and substitutes `<F>`.

## The neutral verbs

`references/verbs.md` defines six verbs. The orchestrator and roles use only these.

| Verb | Meaning | Claude Code | Fallback |
| --- | --- | --- | --- |
| `SPAWN(role, inputs)` | Run one role to completion in a fresh context, get its final message | Agent tool, `subagent_type` | Headless CLI subprocess, then inline |
| `SPAWN_PARALLEL([...])` | Same, concurrently | Several Agent calls in one message | Background subprocesses, then sequential |
| `ASK(questions)` | Put questions or a choice to the user and wait | `AskUserQuestion` / plain message | Plain chat message |
| `NOTIFY(text)` | Tell the user the run is waiting | `PushNotification` | No-op |
| `RESOLVE(skill)` | Absolute path to a skill or SpecKit command file | `.claude/skills`, `~/.claude/skills`, plugins | Adapter's search list |
| `SHELL(cmd)` | Run a command in the worktree | Bash | Every target harness has one |

## Capability tiers

Each adapter declares which tier it runs at; the orchestrator's behaviour adjusts in one place (`verbs.md`).

1. **Native subagents.** The harness can spawn a named custom agent with its own prompt, tools and model. Full fidelity: independent reviewers, parallel fan-out, separate judge.
2. **Headless subprocess.** The harness has no usable subagent, but has a non-interactive CLI (`claude -p`, `codex exec`, `opencode run`, `copilot -p`). The orchestrator runs each role as `<cli> <role prompt + inputs>`, captures stdout, parses the final `json` block. Parallel = background processes. Side benefit: roles can run on a *different* harness than the orchestrator (for example a Codex reviewer in a Claude run) if you ever want model diversity in review.
3. **Inline.** No subagents and no headless CLI. The orchestrator plays each role itself, sequentially, reading the role file as instructions and writing the envelope to disk. Works everywhere, but reviewers and judge share the orchestrator's context, so review is weaker. The approver screen says so.

## Per-harness adapter sketch

These are my current understanding of each harness; **each adapter phase starts by checking that harness's current docs**, since these surfaces change often.

|  | Claude Code | OpenCode | Codex CLI | GitHub Copilot |
| --- | --- | --- | --- | --- |
| Skill dir | `~/.claude/skills` | `~/.config/opencode/skill` (also reads `.claude/skills`) | `~/.codex/skills` | `~/.copilot/skills`, `.github/skills` |
| Agent files | `~/.claude/agents/*.md` | `~/.config/opencode/agent/*.md`, `mode: subagent` | Subagent support if present, else tier 2 via `codex exec` | `.agent.md` custom agents (VS Code `runSubagent`, Copilot CLI) |
| Expected tier | 1 | 1 | 1 or 2 | 1 (VS Code / CLI) |
| Ask | `AskUserQuestion` | chat | chat | chat |
| Notify | `PushNotification` | none / OS notify via shell | none | none |
| SpecKit `--ai` | `claude` | `opencode` | `codex` | `copilot` |
| Model tiers | deep=opus, standard=sonnet | configured per user | configured per user | configured per user |

Model tiers are config, not code: `adapter.yaml` ships sensible defaults and you override them in `${FACTORY_HOME}/config.yaml`.

## Changes to the flow (DESIGN.md)

1. **Spec-builder is stateless per stage.** Each stage, and each relay round within a stage, is a fresh `SPAWN` with `state.json`, the stage, and any answered `relay`. This is exactly today's resume path ("a fresh spec-builder gets the answered questions and asks only the rest"), now used for every turn. Cost: each turn re-reads the brief and artifacts. Gain: no `SendMessage`, and resume is no longer a special case.
2. **State records the harness.** `state.json` gains `harness` (who is running it now) and `history[].harness`. `agents` ids become optional. A run started in Claude Code can be resumed in Codex, since state, artifacts and checkpoints all live in the worktree.
3. **Skill resolution becomes logical.** State stores `speckit.specify` etc.; `RESOLVE` maps them per harness, so a cross-harness resume re-resolves paths instead of trusting stale ones.
4. **Pending dir** moves to `${FACTORY_HOME:-~/.factory}/pending/`, shared by every harness so discovery finds runs started anywhere.
5. **Optional extras** (desktop Auto-fix binding, push notifications) move into the Claude adapter's `harness.md` rather than the core flow.

Everything else in DESIGN.md (grilling, worktree, analyze loop, review, approver, PR, checkpoints, `--stop-at`) is unchanged.

## Implementation phases

Per the project rules: no commits per phase. All phases stay uncommitted in one branch until the PR review step, then one commit.

1. **Core extraction, Claude only.** Move files into `core/` + `adapters/claude-code/`, introduce `verbs.md` and `<F>` paths, write the renderer and `install.sh --harness claude-code`. Rendered Claude output should be functionally identical to today's. DESIGN.md updated first.
2. **Stateless spec-builder.** Replace `SendMessage` driving with per-stage spawns. Re-run the existing validation plan on Claude Code (tiny feature in WayUnoMcpTool, `--stop-at review`, resume in a fresh session, kill mid-implement).
3. **OpenCode adapter** (closest to Claude's model, good first proof of portability).
4. **Codex adapter**, including the tier-2 headless path if native subagents are not adequate.
5. **Copilot adapter** (VS Code custom agents and Copilot CLI; the async cloud coding agent is out of scope).
6. **Cross-harness check.** Start a run in one harness, `--stop-at implement`, resume in another.

Validation for each adapter: the same tiny-feature run to the approver, without opening a PR.

## Decisions (settled 2026-10-22, all on the recommendations below; repo name: agent-factory)

1. **Which harnesses, in what order.** Recommendation: Claude Code, then OpenCode, then Codex, then Copilot.
2. **Runtime adapter vs fully generated files.** Recommendation: the hybrid above (one shared `SKILL.md` that reads `harness.md` at runtime; only agent files are generated). Fully generated per-harness skills are more native but mean four copies of the orchestrator to keep in sync.
3. **Stateless spec-builder everywhere, or keep `SendMessage` on Claude as an optimisation.** Recommendation: stateless everywhere, so there is one behaviour to test.
4. **Renderer language.** Recommendation: a single Python 3 stdlib script (frontmatter and YAML-ish config are awkward in bash). Alternative: keep everything in bash.
5. **Repo name.** `claude-factory` no longer fits; suggestion: `factory` or `agent-factory`.

## Risks

- **Harness drift.** Agent and skill formats are still moving; adapters must be small enough to fix in minutes. Mitigation: adapters hold only paths, names and verb mappings.
- **Uneven review quality.** Tier 3 weakens reviewer independence. Mitigation: the approver screen states the tier the run used.
- **Interactive relay on weaker harnesses.** Batch Q&A via plain chat works everywhere, but harnesses without a picker get a slightly clunkier approver step.
- **SpecKit command shapes differ per agent.** SpecKit generates different files per `--ai` target; `RESOLVE` must be tested against each one.
