# Harness: Claude Code

- `name`: `claude-code`
- `invoke`: `/factory` (how the user starts the factory)
- Recognise it by: you are Claude Code; you have the Agent, Bash, Read, Edit and Skill tools.
- Capability tier: **1** (native subagents).
- `speckit_init`: `--ai claude`
- `impeccable_provider`: `claude`

## Verbs

| Verb | On Claude Code |
|---|---|
| `SPAWN(role, inputs)` | The Agent tool with `subagent_type: factory-<role>` and the inputs as the prompt. Its result is the agent's final message. |
| `SPAWN_PARALLEL([...])` | One Agent tool call per role, all in **one message**. |
| `ASK(text, options?)` | Initial grilling and relays, even one question: a plain Markdown message using protocol.md, "Questions", then wait. Other asks with options: `AskUserQuestion`. Other free text: a plain message, then wait. |
| `NOTIFY(text)` | `PushNotification`. Load it once in preflight with `ToolSearch` (`select:PushNotification`). Unavailable: `NOTIFY` is a no-op for the run. |
| `RESOLVE(name)` | First match of `<name>/SKILL.md` in: `<repo>/.claude/skills/`, `~/.claude/skills/`, then `~/.claude/plugins/**/skills/`. |
| `SHELL(cmd)` | The Bash tool. |

## Notes

- `speckit-*` skills and `grill-with-docs` set `disable-model-invocation: true`: never call them with the Skill tool. `grilling`, `domain-modeling` and `pr` may be invoked with the Skill tool or read and followed.
- `$ARGUMENTS` is substituted by Claude Code from the `/factory` arguments.
- Ledger (reported usage): Agent-tool results expose no token usage — record `reported: null` and rely on the estimates.

## After-PR extras

- When the desktop app's PR tools are available, offer (do not do) binding the PR to the Auto-fix monitor.
