# Harness: ZCode

- `name`: `zcode`
- `invoke`: `/factory` (how the user starts the factory)
- Recognise it by: you are ZCode (Z.ai's coding agent, desktop app or CLI): `ZCODE_HOME` is set or `~/.zcode` exists, and you have the Agent, Bash, Read, Edit and Skill tools.
- Capability tier: **1** (native subagents).
- `speckit_init`: `--integration zcode --integration-options="--skills"`
- `impeccable_provider`: `codex` (ZCode has no provider of its own; the codex provider installs to `~/.agents/skills/`, which ZCode reads)
