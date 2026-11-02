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
| `SPAWN(role, inputs, model)` | The `subagent` tool targeting agent ID `factory-<role>`, with a short `description` and the complete inputs as `prompt`. Pass a nonempty resolved tier model as its `model` parameter. An empty value inherits the parent session only when the installed agent has no configured model; omission does not clear an agent's pinned model. If the installed agent is pinned and the parent model cannot be explicitly selected using a supported mechanism, stop and disclose the limitation rather than silently using the pinned model (FR-003). Use a foreground call and return the child's final message. Each spawn starts a fresh child session. |
| `SPAWN_PARALLEL([...])` | One foreground `subagent` call per role, all in **one message**, or concurrent calls through `execute` when the catalog exposes them there. Map each role's resolved model as above. Wait for every result. |
| `ASK(text, options?)` | Initial grilling and relays, even one question: a plain Markdown message using protocol.md, "Questions", then wait. Other asks with options: the `question` tool when available. Otherwise: a plain message, then wait. |
| `NOTIFY(text)` | No-op. |
| `RESOLVE(name)` | First match of `<name>/SKILL.md` in: `<repo>/.opencode/skills/`, `<repo>/.claude/skills/`, `<repo>/.agents/skills/`, `~/.config/opencode/skills/`, `~/.claude/skills/`, `~/.agents/skills/`. For a `speckit-<stage>` name with no skill, take the command file `speckit.<stage>.md` under `<repo>/.opencode/`. |
| `SHELL(cmd)` | The `shell` tool. |
| `WEB_SEARCH(query)` | The `websearch` tool. |
| `WEB_FETCH(url)` | The `webfetch` tool. |

## Notes

- Main agent (`mode: primary`): rendered `mode: all`; select it with Tab or the agent picker. Other agents can still call it.
- Figma capability discovery: search the session's available tool catalog for Figma MCP inspection tools; pass exact identities and schemas to the role. If unavailable, report the gap.
- The factory's agents live in `~/.config/opencode/agents/` with `mode: subagent` and ordered V2 `permissions` rules. Read-only roles deny `edit`; every role denies `subagent`, so only the orchestrator launches roles. Other permissions follow the user's OpenCode configuration.
- Override `models.opencode.deep` / `.standard` (as `provider/model-id#variant`, with optional variant) in project or user config; preflight resolves the change without reinstalling. An empty model inherits the session model only when the installed agent has no configured model (FR-003); otherwise follow the stop rule above.
- Never load the `speckit-*` skills or `grill-with-docs` with the `skill` tool: read the resolved file and follow it.
- Invoke the factory as `/factory <args>` (the skill sets `opencode/slash`). `$ARGUMENTS` is whatever follows `/factory`.
- Ledger (reported usage): unless the `subagent` result supplies attributable token usage, record `reported: null` and rely on the estimates.

## Compatibility

This adapter targets OpenCode V2. Supported V1 agent and skill files remain compatible through OpenCode's translation, but V2 uses `subagent` and `shell` tools and native `permissions` rules. The factory uses neither the plugin API nor the server API. See the [migration guide](https://opencode.ai/v2/docs/migrate-v1), [tools](https://opencode.ai/v2/docs/tools), and [permissions](https://opencode.ai/v2/docs/permissions).

## Model inspection and recovery

Read effective model/variant selections from `<repo>/.factory/config.json` first, then `${FACTORY_HOME}/config.json`, then installed adapter defaults; repository defaults alone are insufficient. Check local `opencode models --help` for this version, then use supported `opencode models` inventory. Treat it as authoritative for rejection only when its result is complete for the selected provider; partial, failed or unknown-coverage output is unverified. Inventory membership does not prove provider access. If no supported inventory or resolvable inherited ID exists, disclose unverified and retain bounded runtime retry/halt.

For a rejected model, preserve its exact ID/variant, configuration source and original diagnostic. Guide the user to choose a valid accessible selection in the applicable project or user config at `models.opencode.deep` / `.standard` and recheck. For installed adapter selections, reinstall with `./install.sh --harness opencode` and start a fresh session before rechecking. Do not guess an alias, silently choose another model or alter credentials.
