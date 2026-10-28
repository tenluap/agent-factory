# Data Model: Factory Skill Library

All entities are filesystem objects; nothing is stored in `state.json` or `config.json`.

## Library skill

- Folder `<layer>/<name>/` containing `SKILL.md` plus any supporting files.
- Validation (`--add-skill` only): `SKILL.md` exists; it starts with a `---` frontmatter block; frontmatter `name` equals `<name>`.
- Vendored skills also carry `LICENSE`, copied verbatim from upstream.
- Never a library skill: dot-prefixed folders; the reserved name `factory` (skipped with `skip:`, refused by `--add-skill` with `reserved: factory`).

## Repo layer

- `skills/` in the checkout (`$src/skills`), committed.
- Holds `grilling`, `domain-modeling`, `pr`, `ponytail`, `tdd`, `brainstorming` and `SOURCES.md`.
- `SOURCES.md` row: `| name | source URL | path | commit | license |`; commit is the upstream git SHA.

## Per-user layer

- `${FACTORY_HOME:-~/.factory}/skills/`, outside the repository, never committed.
- Created by `--add-skill` after validation passes, before copying. Absent: only the repo layer is linked.
- Kept by `--uninstall`, contents included; relinked by the next install.

## Skills root

- Adapter key `skills_root` (see research R2), expanded with the adapter `home` (so it follows `CLAUDE_HOME`, `ZCODE_HOME`, `XDG_CONFIG_HOME`; Codex/Copilot fixed at `~/.agents/skills`) and reported by `render.py <h> --paths`.

## Library link

- Symlink `<skills_root>/<name>` whose target starts with `$src/skills/` or `${FACTORY_HOME}/skills/`.
- Transitions:
  - absent → link to winning layer (install).
  - library link → re-pointed to winning layer (install; unchanged link prints `linked:` again).
  - library link with missing source → absent, `removed:` printed, then relinked to the repo copy if any (install).
  - non-library path (including a dangling outside symlink) → unchanged, `skip:` printed (install).
  - library link → absent (uninstall). Non-library paths and layer folders are never removed.
