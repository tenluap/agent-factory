# Harness: OpenCode V2

- `name`: `opencode`
- `invoke`: `/factory` (how the user starts the factory)
- Recognise it by: you are running in OpenCode V2; you have the `subagent`, `skill`, `shell`, `read` and `edit` tools, directly or through `execute`'s tool catalog.
- Required before starting: `subagent` and `shell`. If either is unavailable, do not create pending state or a worktree. Tell the user which capability is missing, then guide them to run `./install.sh --harness opencode`, resolve any conflicting install path reported by the installer, and start a fresh OpenCode session. If `/factory` itself is unavailable, this skill did not load; install and reload before invoking it again.
- Capability tier: **1** (native subagents).
- `speckit_init`: `--ai opencode --ai-skills`
- `impeccable_provider`: `opencode` (confirm the name with `npx impeccable install --help` before installing)

## Verbs

| Verb | On OpenCode |
|---|---|
| `SPAWN(role, inputs)` | The `subagent` tool targeting agent ID `factory-<role>`, with a short `description` and the complete inputs as `prompt`. Use a foreground call and return the child's final message. Each spawn starts a fresh child session. |
| `SPAWN_PARALLEL([...])` | One foreground `subagent` call per role, all in **one message**, or concurrent calls through `execute` when the catalog exposes them there. Wait for every result. |
| `ASK(text, options?)` | Initial grilling and relays, even one question: a plain Markdown message using protocol.md, "Questions", then wait. Other asks with options: the `question` tool when available. Otherwise: a plain message, then wait. |
| `NOTIFY(text)` | No-op. |
| `RESOLVE(name)` | First match of `<name>/SKILL.md` in: `<repo>/.opencode/skills/`, `<repo>/.claude/skills/`, `<repo>/.agents/skills/`, `~/.config/opencode/skills/`, `~/.claude/skills/`, `~/.agents/skills/`. For a `speckit-<stage>` name with no skill, take the command file `speckit.<stage>.md` under `<repo>/.opencode/`. |
| `SHELL(cmd)` | The `shell` tool. |

## Notes

- The factory's agents live in `~/.config/opencode/agents/` with `mode: subagent` and ordered V2 `permissions` rules. Read-only roles deny `edit`; every role denies `subagent`, so only the orchestrator launches roles. Other permissions follow the user's OpenCode configuration.
- Agent models come from the adapter defaults. Override `models.opencode.deep` / `.standard` (as `provider/model-id#variant`, with optional variant) in `${FACTORY_HOME}/config.json` and re-run `./install.sh --harness opencode`. An empty model inherits the session's model.
- Never load the `speckit-*` skills or `grill-with-docs` with the `skill` tool: read the resolved file and follow it.
- Invoke the factory as `/factory <args>` (the skill sets `opencode/slash`). `$ARGUMENTS` is whatever follows `/factory`.
- Ledger (reported usage): unless the `subagent` result supplies attributable token usage, record `reported: null` and rely on the estimates.

## Compatibility

This adapter targets OpenCode V2. Supported V1 agent and skill files remain compatible through OpenCode's translation, but V2 uses `subagent` and `shell` tools and native `permissions` rules. The factory uses neither the plugin API nor the server API. See the [migration guide](https://opencode.ai/v2/docs/migrate-v1), [tools](https://opencode.ai/v2/docs/tools), and [permissions](https://opencode.ai/v2/docs/permissions).
