# Harness: OpenCode

- `name`: `opencode`
- `invoke`: `/factory` (how the user starts the factory)
- Recognise it by: you are running in OpenCode; you have the `task`, `skill`, `bash`, `read` and `edit` tools.
- Capability tier: **1** (native subagents).
- `speckit_init`: `--ai opencode --ai-skills`
- `impeccable_provider`: `opencode` (confirm the name with `npx impeccable install --help` before installing)

## Verbs

| Verb | On OpenCode |
|---|---|
| `SPAWN(role, inputs)` | The `task` tool with subagent `factory-<role>` and the inputs as the prompt. Its result is the subagent's final message. |
| `SPAWN_PARALLEL([...])` | One `task` call per role, all in **one message**. |
| `ASK(text, options?)` | With options: the `question` tool when it is available. Otherwise, and for free text or a question batch: a plain message, then wait for the reply. |
| `NOTIFY(text)` | No-op. |
| `RESOLVE(name)` | First match of `<name>/SKILL.md` in: `<repo>/.opencode/skills/`, `<repo>/.claude/skills/`, `<repo>/.agents/skills/`, `~/.config/opencode/skills/`, `~/.claude/skills/`, `~/.agents/skills/`. For a `speckit-<stage>` name with no skill, take the command file `speckit.<stage>.md` under `<repo>/.opencode/`. |
| `SHELL(cmd)` | The `bash` tool. |

## Notes

- The factory's agents live in `~/.config/opencode/agents/` with `mode: subagent`; read-only roles have `permission.edit: deny`.
- Agent models are not set by default, so every agent uses the session's model. To pin them, set `models.opencode.deep` / `.standard` (as `provider/model-id`) in `${FACTORY_HOME}/config.json` and re-run `./install.sh --harness opencode`.
- Never load the `speckit-*` skills or `grill-with-docs` with the `skill` tool: read the resolved file and follow it.
- Invoke the factory as `/factory <args>` (the skill sets `opencode/slash`). `$ARGUMENTS` is whatever follows `/factory`.
- Ledger (reported usage): `task` results expose no token usage — record `reported: null` and rely on the estimates.
