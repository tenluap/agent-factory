# Harness: Codex

- `name`: `codex`
- `invoke`: `$factory` (how the user starts the factory)
- Recognise it by: you are OpenAI Codex (CLI, IDE extension or app).
- Capability tier: **1** (native subagents).
- `speckit_init`: `--integration codex --integration-options="--skills" --force`
- `impeccable_provider`: `codex` (confirm the name with `npx impeccable install --help` before installing)

## Verbs

| Verb | On Codex |
|---|---|
| `SPAWN(role, inputs, model)` | Spawn the custom agent `factory_<role>` (hyphens in the role become underscores, e.g. `factory_spec_builder`) with the inputs as its task, and wait for its result. Spawn cannot take a model; use the installed selection. This skill's instruction is your explicit request to spawn it. |
| `SPAWN_PARALLEL([...])` | Spawn every listed agent at once, wait until all results are in, then continue. |
| `ASK(text, options?)` | A plain message, then wait for the reply. Initial grilling and relays, even one question, use the Markdown presentation in protocol.md, "Questions". |
| `NOTIFY(text)` | No-op. |
| `RESOLVE(name)` | First match of `<name>/SKILL.md` in: `<repo>/.agents/skills/`, `<repo>/.codex/skills/`, `~/.agents/skills/`, `~/.codex/skills/`, `/etc/codex/skills/`. For a `speckit-<stage>` name with no skill, take the prompt file `speckit.<stage>.md` under `<repo>/.codex/`. |
| `SHELL(cmd)` | Your shell tool. |
| `WEB_SEARCH(query)` | Your web search tool, when the session enables it. Without it, report the gap; do not fall back to `SHELL`. |
| `WEB_FETCH(url)` | Your web search tool's page open, when enabled. Without it, report the gap. |

## Notes

- `no_prompt_launch`: `codex --dangerously-bypass-approvals-and-sandbox` (alias `--yolo`) runs every command without approvals or sandboxing (Codex CLI reference). Use only inside an externally sandboxed environment; launch-time only.
- Main agent (`mode: primary`): unsupported; Codex custom agents are subagents only. Ask your session to spawn `factory_<role_>` instead.
- Figma capability discovery: inspect the session's available MCP tool inventory for Figma inspection tools; pass exact identities and schemas to the role. If unavailable, report the gap.
- The factory's agents are TOML files in `~/.codex/agents/` (`factory_<role>.toml`). Subagents inherit the session's sandbox and approval policy, so read-only roles are read-only by instruction. The session needs write access to the worktree and network for `git push` and `gh`.
- Agent models come from the adapter defaults. To override them, set `models.codex.deep` / `.standard` in `${FACTORY_HOME}/config.json` and re-run `./install.sh --harness codex`.
- If the review fan-out exceeds `agents.max_concurrent_threads_per_session`, spawn the rest as slots free up.
- Never invoke the `speckit-*` skills or `grill-with-docs` as skills: read the resolved file and follow it.
- Invoke the factory as `$factory <args>` (or pick it from `/skills`). `$ARGUMENTS` is whatever follows the skill name.
- Ledger (reported usage): subagent results expose no token usage — record `reported: null` and rely on the estimates.

## Model inspection and recovery

Preflight resolves configuration in order: `<repo>/.factory/config.json` (project), `${FACTORY_HOME}/config.json` (user), then adapter defaults. If either resolved tier's source is `project` or `user`, disclose that project/user model selections cannot apply at spawn and continue on the installed (rendered) selections.

Read effective installed role selections and their configuration source, including overrides; preserve an unresolved inherited session choice. This adapter provides no authoritative model inventory command. Unless the session itself exposes a supported authoritative inventory, disclose availability as unverified and retain the existing bounded runtime retry/halt policy. Never invent an inventory API or treat rendered IDs as proof of service access.

For a rejected model, preserve the exact selection and original diagnostic. Name the installed agent or `${FACTORY_HOME}/config.json` source; guide correction through `models.codex.deep` / `.standard`, `./install.sh --harness codex`, then a fresh session and recheck. Preserve user model/credential choices; never guess aliases or silently substitute.
