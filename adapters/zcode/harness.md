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
