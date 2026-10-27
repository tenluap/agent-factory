# Harness: GitHub Copilot

- `name`: `copilot`
- `invoke`: `/factory` (how the user starts the factory)
- Recognise it by: you are GitHub Copilot (Copilot CLI, or agent mode in VS Code).
- Capability tier: **1** (custom agents run as subagents). Falls back to **2** where delegation is unavailable (below).
- `speckit_init`: `--ai copilot --ai-skills`
- `impeccable_provider`: `copilot` (confirm the name with `npx impeccable install --help` before installing)

## Verbs

| Verb | On GitHub Copilot |
|---|---|
| `SPAWN(role, inputs)` | Delegate to the custom agent `factory-<role>` with the inputs as its task (the agent/subagent tool), and wait for its result. **Tier 2 fallback** when you cannot delegate: `SHELL` `copilot --agent factory-<role> --prompt "<inputs>"`, with the tool-approval flags your setup needs for a non-interactive run, and take the final fenced `json` block from its output. |
| `SPAWN_PARALLEL([...])` | Delegate to every listed agent at once if the harness runs subagents in parallel; otherwise one after another. In tier 2: background processes, then wait for all. |
| `ASK(text, options?)` | A plain message, then wait for the reply. Initial grilling and relays, even one question, use the Markdown presentation in protocol.md, "Questions". |
| `NOTIFY(text)` | No-op. |
| `RESOLVE(name)` | First match of `<name>/SKILL.md` in: `<repo>/.github/skills/`, `<repo>/.claude/skills/`, `<repo>/.agents/skills/`, `~/.copilot/skills/`, `~/.agents/skills/`. For a `speckit-<stage>` name with no skill, take `speckit.<stage>.agent.md` under `<repo>/.github/agents/` or `speckit.<stage>.prompt.md` under `<repo>/.github/prompts/`. |
| `SHELL(cmd)` | Your shell/terminal tool. |

## Notes

- The factory's agents are `~/.copilot/agents/factory-<role>.agent.md`. Read-only roles get `tools: [read, search, execute]`.
- Agent models are not set by default, so every agent uses the default model. To pin them, set `models.copilot.deep` / `.standard` in `${FACTORY_HOME}/config.json` and re-run `./install.sh --harness copilot`.
- In VS Code, user-level agents and skills may need to be enabled or pointed at `~/.copilot/` in settings; the Copilot CLI reads them as installed.
- The cloud coding agent (assigning an issue to Copilot on github.com) is not supported: it cannot relay questions or wait for the approver.
- Invoke the factory as `/factory <args>`. `$ARGUMENTS` is whatever follows `/factory`.
- Ledger (reported usage): delegation exposes no token usage — record `reported: null`. Tier-2 fallback: the `copilot --agent` output usually prints token usage; take `reported` from there when it does.
