# Harness: ZCode

- `name`: `zcode`
- `invoke`: `/factory` (how the user starts the factory)
- Recognise it by: you are ZCode (Z.ai's coding agent, desktop app or CLI): `ZCODE_HOME` is set or `~/.zcode` exists, and you have the Agent, Bash, Read, Edit and Skill tools.
- Capability tier: **1** (native subagents).
- `speckit_init`: `--integration zcode --integration-options="--skills" --force`
- `impeccable_provider`: `codex` (ZCode has no provider of its own; the codex provider installs to `~/.agents/skills/`, which ZCode reads)

## Verbs

| Verb | On ZCode |
|---|---|
| `SPAWN` | Agent/Task tool with `subagent_type: factory-<role>`, inputs as the prompt. Spawn cannot take a model; use the installed selection. |
| `SPAWN_PARALLEL` | one Agent call per role, all in one message |
| `ASK` | grilling and relays: Markdown layout from protocol.md; other choice asks: `AskUserQuestion`; free text: plain message |
| `NOTIFY` | no-op (no notification tool) |
| `RESOLVE` | first `<name>/SKILL.md` in `<repo>/.zcode/skills/`, `<repo>/.agents/skills/`, `~/.zcode/skills/`, `~/.agents/skills/` |
| `SHELL` | the Bash tool |
| `WEB_SEARCH` | the WebSearch tool |
| `WEB_FETCH` | the WebFetch tool |

## Notes

- `no_prompt_launch`: none documented. No verified launch-time or config option was found for ZCode, so cruise runs here keep harness prompts; the orchestrator's preflight disclosure says so.
- Main agent (`mode: primary`): unverified. Try `zcode --agent factory-<role>`; otherwise ask your session to spawn `factory-<role>`.
- Figma capability discovery: inspect the session's available MCP tool inventory for Figma inspection tools; pass exact identities and schemas to the role. If unavailable, report the gap.
- The factory's agents are Markdown files in `~/.zcode/agents/` (`factory-<role>.md`).
- Agent models are not set by default, so every agent inherits the session's model. To pin them, set `models.zcode.deep` / `.standard` in `${FACTORY_HOME}/config.json` and re-run `./install.sh --harness zcode`.
- Never invoke the `speckit-*` skills or `grill-with-docs` with the Skill tool: read the resolved file and follow it.
- Invoke the factory as `/factory <args>`. `$ARGUMENTS` is whatever follows `/factory`.
- Ledger (reported usage): Agent results expose no token usage — record `reported: null` and rely on the estimates.

## Model inspection and recovery

Preflight resolves configuration in order: `<repo>/.factory/config.json` (project), `${FACTORY_HOME}/config.json` (user), then adapter defaults. If either resolved tier's source is `project` or `user`, disclose that project/user model selections cannot apply at spawn and continue on the installed (rendered) selections.

Read effective installed role selections and their configuration source, including overrides; preserve an unresolved inherited session choice. This adapter provides no authoritative model inventory command. Unless the session itself exposes a supported authoritative inventory, disclose availability as unverified and retain the existing bounded runtime retry/halt policy. Never invent an inventory API or treat rendered IDs as proof of service access.

For a rejected model, preserve the exact selection and original diagnostic. Name the installed agent or `${FACTORY_HOME}/config.json` source; guide correction through `models.zcode.deep` / `.standard`, `./install.sh --harness zcode`, then a fresh session and recheck. Preserve user model/credential choices; never guess aliases or silently substitute.
