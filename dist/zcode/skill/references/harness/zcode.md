# Harness: ZCode

- `name`: `zcode`
- `invoke`: `/factory` (how the user starts the factory)
- Recognise it by: you are ZCode (Z.ai's coding agent, desktop app or CLI): `ZCODE_HOME` is set or `~/.zcode` exists, and you have the Agent, Bash, Read, Edit and Skill tools.
- Capability tier: **1** (native subagents).
- `speckit_init`: `--integration zcode --integration-options="--skills"`
- `impeccable_provider`: `codex` (ZCode has no provider of its own; the codex provider installs to `~/.agents/skills/`, which ZCode reads)

## Verbs

| Verb | On ZCode |
|---|---|
| `SPAWN` | Agent/Task tool with `subagent_type: factory-<role>`, inputs as the prompt |
| `SPAWN_PARALLEL` | one Agent call per role, all in one message |
| `ASK` | grilling and relays: Markdown layout from protocol.md; other choice asks: `AskUserQuestion`; free text: plain message |
| `NOTIFY` | no-op (no notification tool) |
| `RESOLVE` | first `<name>/SKILL.md` in `<repo>/.zcode/skills/`, `<repo>/.agents/skills/`, `~/.zcode/skills/`, `~/.agents/skills/` |
| `SHELL` | the Bash tool |

## Notes

- The factory's agents are Markdown files in `~/.zcode/agents/` (`factory-<role>.md`).
- Agent models are not set by default, so every agent inherits the session's model. To pin them, set `models.zcode.deep` / `.standard` in `${FACTORY_HOME}/config.json` and re-run `./install.sh --harness zcode`.
- Never invoke the `speckit-*` skills or `grill-with-docs` with the Skill tool: read the resolved file and follow it.
- Invoke the factory as `/factory <args>`. `$ARGUMENTS` is whatever follows `/factory`.
- Ledger (reported usage): Agent results expose no token usage — record `reported: null` and rely on the estimates.
