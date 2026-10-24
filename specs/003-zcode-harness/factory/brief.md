# Brief: add zcode harness

Add a `zcode` adapter to the software factory so `/factory` runs inside Z.ai's ZCode (desktop app 3.16.x and its bundled CLI, `glm/zcode.cjs`). ZCode has a native Agent/Task tool taking `subagent_type`, loads custom agents from `~/.zcode/agents/*.md` (user) and `<repo>/.zcode/agents/` (project) with Claude-style frontmatter (`name`, `description`, `tools`, `disallowedTools`, `model`, `permissionMode`, `maxTurns`, `skills`), and reads skills from `.zcode/skills/` and `.agents/skills/` in home and in the project (walking up to the git root).

Chain: **lite** (pinned by `--lite`).

## Decisions

- Q1: The adapter is named `zcode`, in `adapters/zcode/` (`adapter.json` + `harness.md`), and covers the ZCode desktop app and its bundled CLI.
- Q2: Capability tier 1 (native subagents): `SPAWN` = the Agent tool with `subagent_type: factory-<role>`; `SPAWN_PARALLEL` = one Agent call per role in one message.
- Q3: Install: skill at `{home}/skills/factory`, agents at `{home}/agents/factory-{role}.md`, Markdown format; `home` env `ZCODE_HOME`, default `~/.zcode`.
- Q4: Access: Claude Code-style `tools` lists: read = `Read, Grep, Glob, Bash`; write = `Read, Edit, Write, Bash, Grep, Glob`.
- Q5: Models: not pinned (empty `models`); agents inherit the session model; users pin via `${FACTORY_HOME}/config.json` `models.zcode`.
- Q6: `speckit_init`: `--ai codex --ai-skills` (SpecKit's skills land in `.agents/skills`, which ZCode scans; verify the flag at plan time). `RESOLVE` order: `<repo>/.zcode/skills/`, `<repo>/.agents/skills/`, `<repo>/.claude/skills/`, `~/.zcode/skills/`, `~/.agents/skills/`, `~/.claude/skills/`.
- Q7: Docs: README harness table row and requirements, DESIGN.md "Adapters today", CONTEXT.md "Harness" definition.
- Q8: Run base is local `main` (origin unreachable at run start).
- Invoke command: `/factory <args>` (ZCode runs `/<skill-name>` via its Skill tool); `$ARGUMENTS` is what follows `/factory`.
- `ASK`: Markdown presentation (protocol.md) for grilling and relays; `AskUserQuestion` for other choice asks; plain message for free text.
- `NOTIFY`: no-op (ZCode exposes no notification tool).
- `impeccable_provider`: `zcode`, to be confirmed with `npx impeccable install --help` before installing.
- Ledger: Agent results expose no token usage, so `reported: null`.
- Recognise line: "you are ZCode (Z.ai's coding agent, desktop app or CLI); you have the Agent, Bash, Read, Edit and Skill tools."
- Never invoke `speckit-*` or `grill-with-docs` with the Skill tool; read the resolved file and follow it.
- Verification: render every adapter with `tools/render.py`; `dist/zcode/agents/factory-*.md` carries valid frontmatter.
