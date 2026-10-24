# Data model: ZCode harness adapter

Three artifacts, each an instance of an existing shape. No new shape is introduced.

## 1. ZCode adapter descriptor - `adapters/zcode/adapter.json`

Consumed by `tools/render.py` (`load_adapter`, `agent_fields`, `render_agent`).

| Field | Value | Note |
|---|---|---|
| `name` | `zcode` | must equal the folder name |
| `home.env` | `ZCODE_HOME` | read by `load_adapter`; empty/unset falls back to the default |
| `home.default` | `~/.zcode` | ZCode's storage root |
| `skill_dir` | `{home}/skills/factory` | a user skill root ZCode scans |
| `agent_dir` | `{home}/agents` | ZCode's user agent directory |
| `agent_file` | `factory-{role}.md` | one per role in `core/roles/` |
| `agent_format` | `markdown` | YAML frontmatter + body |
| `fields` | `[["name", "factory-{role}"], ["description", "{description}"]]` | ZCode frontmatter keys |
| `access.read.tools` | `Read, Grep, Glob, Bash` | read-only roles |
| `access.write.tools` | `Read, Edit, Write, Bash, Grep, Glob` | writing roles |
| `models` | `{"deep": "", "standard": ""}` | key required by the config override path; empty = inherit |

Validation rules: valid JSON; every templated path uses only `{home}`; `agent_format` is one the renderer
knows; `access` has exactly the keys the roles declare (`read`, `write`); `models` has `deep` and
`standard`.

## 2. ZCode harness document - `adapters/zcode/harness.md`

Same sections as every existing `harness.md`.

- Header values: `name` `zcode`; `invoke` `/factory`; recognition line resting on a checkable signal (FR-012)
  - "you are ZCode (Z.ai's coding agent, desktop app or CLI): `ZCODE_HOME` is set or `~/.zcode` exists, and
  you have the Agent, Bash, Read, Edit and Skill tools."; capability tier **1**;
  `speckit_init` `--integration zcode --integration-options="--skills"`; `impeccable_provider` `codex`
  (ZCode has no provider of its own; the codex provider installs to `~/.agents/skills/`, which ZCode reads).
- Verb table:

| Verb | On ZCode |
|---|---|
| `SPAWN` | Agent/Task tool with `subagent_type: factory-<role>`, inputs as the prompt |
| `SPAWN_PARALLEL` | one Agent call per role, all in one message |
| `ASK` | grilling and relays: Markdown layout from protocol.md; other choice asks: `AskUserQuestion`; free text: plain message |
| `NOTIFY` | no-op (no notification tool) |
| `RESOLVE` | first `<name>/SKILL.md` in `<repo>/.zcode/skills/`, `<repo>/.agents/skills/`, `~/.zcode/skills/`, `~/.agents/skills/` |
| `SHELL` | the Bash tool |

- Notes: agents live in `~/.zcode/agents/factory-<role>.md`; models unpinned, pin via
  `${FACTORY_HOME}/config.json` `models.zcode` then re-run `./install.sh --harness zcode`; never invoke
  `speckit-*` or `grill-with-docs` with the Skill tool - read the resolved file and follow it; `$ARGUMENTS`
  is whatever follows `/factory`; ledger `reported: null` because Agent results expose no token usage.

## 3. Rendered role agent file - `dist/zcode/agents/factory-<role>.md`

Produced by the renderer, one per `core/roles/*.md`:

```text
---
name: factory-<role>
description: <role description>
tools: <access list for the role>
---
<role body, with <F> replaced by the resolved skill_dir>
```

Validation rules: frontmatter parses; the key set is exactly `name`, `description`, `tools` (FR-004);
`name` matches the filename stem; `tools` matches the role's `access`; no `model`, `permissionMode`,
`maxTurns` or `skills` key; the body contains no `<F>` placeholder.

## 4. Tracked distribution - `dist/` (FR-018)

Not a new shape: the existing rendered trees, now under version control. `.gitignore` loses its `/dist/`
line, and `dist/<harness>/` for all five harnesses is committed with the source that produced it. State
after the change: `git ls-files dist/` lists every rendered file, and `git diff --exit-code -- dist/` after
a full render is clean exactly when source and render agree.

## Relationships

`core/roles/*.md` (9 roles) + `adapters/zcode/adapter.json` → `dist/zcode/agents/*.md` (9 files).
`core/skills/factory/` + every adapter's `harness.md` → `dist/<harness>/skill/`, so adding
`adapters/zcode/harness.md` adds `references/harness/zcode.md` to **every** harness's skill.
