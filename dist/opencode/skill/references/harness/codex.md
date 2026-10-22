# Harness: Codex

- `name`: `codex`
- `invoke`: `$factory` (how the user starts the factory)
- Recognise it by: you are OpenAI Codex (CLI, IDE extension or app).
- Capability tier: **1** (native subagents).
- `speckit_init`: `--ai codex --ai-skills`
- `impeccable_provider`: `codex` (confirm the name with `npx impeccable install --help` before installing)

## Verbs

| Verb | On Codex |
|---|---|
| `SPAWN(role, inputs)` | Spawn the custom agent `factory_<role>` (hyphens in the role become underscores, e.g. `factory_spec_builder`) with the inputs as its task, and wait for its result. This skill's instruction is your explicit request to spawn it. |
| `SPAWN_PARALLEL([...])` | Spawn every listed agent at once, wait until all results are in, then continue. |
| `ASK(text, options?)` | A plain message, then wait for the reply. Initial grilling and relays, even one question, use the Markdown presentation in protocol.md, "Questions". |
| `NOTIFY(text)` | No-op. |
| `RESOLVE(name)` | First match of `<name>/SKILL.md` in: `<repo>/.agents/skills/`, `<repo>/.codex/skills/`, `~/.agents/skills/`, `~/.codex/skills/`, `/etc/codex/skills/`. For a `speckit-<stage>` name with no skill, take the prompt file `speckit.<stage>.md` under `<repo>/.codex/`. |
| `SHELL(cmd)` | Your shell tool. |

## Notes

- The factory's agents are TOML files in `~/.codex/agents/` (`factory_<role>.toml`). Subagents inherit the session's sandbox and approval policy, so read-only roles are read-only by instruction. The session needs write access to the worktree and network for `git push` and `gh`.
- Agent models are not set by default, so every agent inherits the session's model. To pin them, set `models.codex.deep` / `.standard` in `${FACTORY_HOME}/config.json` and re-run `./install.sh --harness codex`.
- If the review fan-out exceeds `agents.max_concurrent_threads_per_session`, spawn the rest as slots free up.
- Never invoke the `speckit-*` skills or `grill-with-docs` as skills: read the resolved file and follow it.
- Invoke the factory as `$factory <args>` (or pick it from `/skills`). `$ARGUMENTS` is whatever follows the skill name.
- Ledger (reported usage): subagent results expose no token usage — record `reported: null` and rely on the estimates.
