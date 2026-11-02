# Verbs

The core never names a harness tool. It uses these verbs; `references/harness/<name>.md` for the harness running the run (SKILL.md, preflight; called `harness.md` below) says how to perform each one there. Read it once in preflight and keep its mapping for the run.

| Verb | Meaning |
|---|---|
| `SPAWN(role, inputs, model)` | Run one role (its agent file is named in `harness.md`, usually `factory-<role>`) to completion in a fresh context. `model` is the resolved model for the role's tier; an empty string omits it and inherits the session model. The prompt is the inputs plus `F` (this skill's base directory); apply `model` through the adapter's spawn mapping. Returns the role's final message. `harness.md` names where the harness exposes the spawn's reported token usage, if anywhere. Roles keep nothing between spawns: whatever a later spawn needs is in `state.json` or on disk. |
| `SPAWN_PARALLEL([(role, inputs, model), ...])` | `SPAWN` several roles concurrently, each with its own tier's resolved model, and collect every final message. Empty model strings omit the model and inherit the session model. |
| `ASK(text, options?)` | Put a question or a choice to the user and wait for the answer. |
| `NOTIFY(text)` | Tell the user the run is waiting on them. A no-op where the harness has no notification. |
| `RESOLVE(name)` | Absolute path of a skill's `SKILL.md`, or of a SpecKit command file, by logical name (`speckit-plan`, `grilling`, ...). The search order is in `harness.md`; first match wins. |
| `SHELL(cmd)` | Run a shell command. In a worktree: `cd <worktree> && <cmd>`. |
| `WEB_SEARCH(query)` | Role-only, `research` access. Search the web and return result titles, URLs and snippets. |
| `WEB_FETCH(url)` | Role-only, `research` access. Fetch one page and return its readable text. |

For Figma only, if `RESOLVE(figma)` finds no skill, inspect the active session's available capability inventory using `harness.md`. An available MCP inspection capability is an alternative, not a skill path: pass its usable identity and invocation guidance to the role, and rediscover after a harness change. The role must verify it can access the capability in its own context; otherwise report the blocker. A configured but unavailable server is not proof of a capability. Do not install anything or guess a tool API; if inventory or inspection is unavailable, report the blocker.

## Capability tiers

`harness.md` names the tier its harness runs at.

1. **Native subagents**: `SPAWN` starts a named custom agent with its own prompt, tools and model. `SPAWN_PARALLEL` starts them together.
2. **Headless subprocess**: `SPAWN` runs the harness's non-interactive CLI with the role file and inputs as the prompt, captures stdout, and takes the final fenced `json` block; the CLI's output may also expose token usage, and `harness.md` says where. `SPAWN_PARALLEL` runs them as background processes and waits for all.
3. **Inline**: `SPAWN` means the orchestrator reads `F/roles/<role>.md` (where `<F>` means F) and does the work itself, then writes the envelope or report it would have returned. `SPAWN_PARALLEL` runs the roles one after another. Reviewers and the judge share the orchestrator's context, so the approver screen must say the run used tier 3.

Whatever the tier, a role's output is its **final fenced `json` block** (protocol.md, findings.md). Parse that block; anything else in the message is commentary.
