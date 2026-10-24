# Research: ZCode harness adapter

Facts verified at plan time against ZCode 3.16.3 (`/Applications/ZCode.app/Contents/Resources/glm/zcode.cjs`),
specify-cli 1.1.0 (`specify --version`) and impeccable (`npx impeccable install --help`).

## R1 - ZCode subagents, skills and agent files

- **Decision**: capability tier 1. `SPAWN` = the Agent/Task tool with `subagent_type: factory-<role>`;
  `SPAWN_PARALLEL` = one Agent call per role in a single message.
- **Rationale**: the bundle ships an Agent/Task tool taking `subagent_type`, and loads custom agents from
  `<storageRoot>/agents` (user, storage root `~/.zcode`) and `<cwd>/.zcode/agents` (project) with Claude-style
  frontmatter: `name`, `description`, `tools`, `disallowedTools`, `model`, `permissionMode`, `maxTurns`,
  `skills`, `background`, `injectAgentsMd`.
- **Alternatives**: tier 2 (headless CLI subprocess) - rejected, native subagents exist and are cheaper.

## R2 - Skill roots ZCode reads

- **Decision**: `RESOLVE(name)` = first match of `<name>/SKILL.md` in `<repo>/.zcode/skills/`,
  `<repo>/.agents/skills/`, `~/.zcode/skills/`, `~/.agents/skills/`.
- **Rationale**: the bundle's skill-root resolver uses exactly two directory constants, `.zcode` and
  `.agents`, with the subdirectory `skills`, resolved under the home base and under the project base
  (walking up to the git worktree root, depth 10). No `.claude` skill root exists in the bundle.
- **Consequence**: FR-010 originally also listed `<repo>/.claude/skills/` and `~/.claude/skills/`. It and
  its edge case were corrected to these four roots during clarify, so spec, plan and adapter now agree and
  no deviation is open.
- **Alternatives**: keeping the `.claude` entries - rejected, ZCode never reads them, so they would send a
  reader to a location the harness ignores.

## R3 - Factory install locations

- **Decision**: `home` = env `ZCODE_HOME`, default `~/.zcode`; `skill_dir` = `{home}/skills/factory`;
  `agent_dir` = `{home}/agents`; `agent_file` = `factory-{role}.md`; `agent_format` = `markdown`.
- **Rationale**: `ZCODE_HOME` is read by the bundle; the user-level skill root is `~/.zcode/skills` and the
  user-level agent directory is `<storageRoot>/agents`, so both installed trees land where ZCode scans.
- **Alternatives**: installing to `~/.agents/skills/factory` (shared with Codex/Copilot) - rejected, the
  factory skill is byte-identical per harness and a per-harness home keeps uninstall unambiguous.

## R4 - SpecKit initialisation (brief claim disproved)

- **Decision**: `speckit_init` = `--integration zcode --integration-options="--skills"`.
- **Rationale**: specify-cli 1.1.0 has **no** `--ai` or `--ai-skills` flag (`specify init --help` lists
  `--integration` and `--integration-options` only), and it ships a native ZCode integration
  (`specify_cli/integrations/zcode`): key `zcode`, folder `.zcode/`, commands subdir `skills`, markdown,
  `$ARGUMENTS`, files written as `.zcode/skills/speckit-<name>/SKILL.md`, skills on by default, invoked in
  chat as `$speckit-<name>`. `specify check` lists ZCode as a known integration.
- **Alternatives**: the brief's `--ai codex --ai-skills` - rejected, the flags do not exist in the installed
  CLI and the codex integration would write `.agents/skills` when a native ZCode layout is available.
- **Note**: `DESIGN.md:69` states the setup as `--ai <harness>` plus `--ai-skills`, which the ZCode adapter
  contradicts. This feature generalises that one line to `specify init --here <harness.speckit_init>`,
  whose argument shape each adapter states, so Constitution I holds (FR-016). The other four adapters'
  recorded setup values are left as they are: correcting them is out of scope.

## R5 - impeccable provider

- **Decision**: `impeccable_provider` = `codex`, with the harness note that ZCode has no provider of its own.
- **Rationale**: `npx impeccable install --help` takes `--providers=<names>`; the documented provider set is
  `claude, cursor, gemini, codex, github, grok, hermes, opencode, pi, qoder, trae, trae-cn, rovo-dev, vibe,
  veto` - no `zcode`. User-wide installs for the `codex` provider land in `~/.agents/skills/`, which ZCode
  scans (R2), so the impeccable skill resolves inside ZCode.
- **Alternatives**: `claude` - rejected, it installs under `~/.claude/skills/`, which ZCode does not read.

## R6 - Questions, notification, ledger

- **Decision**: `ASK` = the factory's Markdown layout (protocol.md) for grilling and relay rounds,
  `AskUserQuestion` for other choice asks, a plain message for free text. `NOTIFY` = no-op. Ledger
  `reported: null`.
- **Rationale**: the bundle exposes `AskUserQuestion` and no notification tool; Agent results carry no token
  usage, matching the Claude Code and Codex adapters' ledger note.

## R7 - Models

- **Decision**: empty `models` (`{"deep": "", "standard": ""}`); agents inherit the session model.
- **Rationale**: `render.py` appends a `model` field only when the tier maps to a non-empty string, and
  `load_adapter` updates `adapter["models"]` from `${FACTORY_HOME}/config.json`, so the key must exist for
  the user override path to work. Z.ai model ids are account-dependent, so pinning a default would break
  sessions on other plans.

## R8 - Tracking the rendered distribution (FR-018)

- **Decision**: remove the `/dist/` line from `.gitignore` and commit the rendered output of all five
  harnesses; the build gate stays `git diff --exit-code -- dist/` after a full render.
- **Rationale**: `git ls-files dist/` returned 0 files and `.gitignore` listed `/dist/`, so a plain
  `git add dist/` was refused and the gate passed vacuously - Constitution III ("dist committed with its
  source") was neither satisfied nor checked. Tracking the directory makes the commit normal and the check
  able to fail. Recorded as `docs/adr/0005-the-rendered-distribution-is-tracked-in-git.md`.
- **Alternatives**: `git add -f dist/` with `git diff --cached --exit-code` - rejected, the gate then
  depends on a step a contributor can forget; rendering into a scratch tree and comparing - rejected, it
  leaves no installable distribution in the clone, which is what `install.sh` reads.
- **Consequence**: the first commit is large (four existing harnesses' trees enter version control at
  once) and every later render shows generated files in diffs; accepted in ADR 0005.

## R9 - Cross-harness resume (SC-005)

- **Decision**: resume needs no ZCode-specific mechanism - `state.json` under the worktree's spec folder is
  harness-neutral - but SC-005 is verified by a manual check in both directions (start in ZCode, resume
  elsewhere; start elsewhere, resume in ZCode).
- **Rationale**: the adapter changes only dispatch, install paths and verb mappings; no run state is
  harness-tagged beyond the `harness` field the resuming session re-reads.
