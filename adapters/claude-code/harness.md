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
| `SPAWN(role, inputs, model)` | The Agent tool with `subagent_type: factory-<role>` and the inputs as the prompt. Pass the resolved tier model as the Agent tool's `model` parameter; omit the parameter when it is empty. Its result is the agent's final message. |
| `SPAWN_PARALLEL([...])` | One Agent tool call per role, all in **one message**, with each role's resolved model mapped as above. |
| `ASK(text, options?)` | Initial grilling and relays, even one question: a plain Markdown message using protocol.md, "Questions", then wait. Other asks with options: `AskUserQuestion`. Other free text: a plain message, then wait. |
| `NOTIFY(text)` | `PushNotification`. Load it once in preflight with `ToolSearch` (`select:PushNotification`). Unavailable: `NOTIFY` is a no-op for the run. |
| `RESOLVE(name)` | First match of `<name>/SKILL.md` in: `<repo>/.claude/skills/`, `~/.claude/skills/`, then `~/.claude/plugins/**/skills/`. |
| `SHELL(cmd)` | The Bash tool. |
| `WEB_SEARCH(query)` | The WebSearch tool. |
| `WEB_FETCH(url)` | The WebFetch tool. |

## Notes

- Main agent (`mode: primary`): start with `claude --agent factory-<role>`, or set the `agent` setting.
- Figma capability discovery: use `ToolSearch` to discover available Figma MCP inspection tools; pass their exact identities and schemas to the role. If unavailable, report the gap.
- `speckit-*` skills and `grill-with-docs` set `disable-model-invocation: true`: never call them with the Skill tool. `grilling`, `domain-modeling` and `pr` may be invoked with the Skill tool or read and followed.
- `$ARGUMENTS` is substituted by Claude Code from the `/factory` arguments.
- Ledger (reported usage): Agent-tool results expose no token usage — record `reported: null` and rely on the estimates.

## After-PR extras

- When the desktop app's PR tools are available, offer (do not do) binding the PR to the Auto-fix monitor.

## Model inspection and recovery

Read effective resolved role selections and their configuration source: `<repo>/.factory/config.json` first, then `${FACTORY_HOME}/config.json`, then installed adapter defaults; preserve an unresolved inherited session choice. This adapter provides no authoritative model inventory command. Unless the session itself exposes a supported authoritative inventory, disclose availability as unverified and retain the existing bounded runtime retry/halt policy. Never invent an inventory API or treat rendered IDs as proof of service access.

For a rejected model, preserve the exact selection and original diagnostic. Name its project, user or adapter source; guide correction through `models.claude-code.deep` / `.standard` in the applicable config and recheck. For installed adapter selections, reinstall with `./install.sh --harness claude-code` and start a fresh session before rechecking. Preserve user model/credential choices; never guess aliases or silently substitute.
