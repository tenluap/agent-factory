# Data Model: Factory Skill Library

All entities are filesystem objects; nothing is stored in `state.json` or `config.json`.

## Library skill

- Folder `<layer>/<name>/` containing `SKILL.md` plus any supporting files.
- Validation (`--add-skill` only): `SKILL.md` exists; it starts with a `---` frontmatter block; frontmatter `name` equals `<name>`.
- Vendored skills also carry `LICENSE`.

## Repo layer

- `skills/` in the checkout (`$src/skills`), committed.
- Holds `grilling`, `domain-modeling`, `pr`, `ponytail`, `tdd`, `brainstorming` and `SOURCES.md`.
- `SOURCES.md` row: `| name | source URL | path | commit | license |`; commit is a git SHA or `lock:<skillFolderHash>`.

## Per-user layer

- `${FACTORY_HOME:-~/.factory}/skills/`, outside the repository, never committed.
- Created on first `--add-skill`. Absent: only the repo layer is linked.

## Skills root

- Adapter key `skills_root` (see research R2), expanded with the adapter `home` and reported by `render.py <h> --paths`.

## Library link

- Symlink `<skills_root>/<name>` whose target starts with `$src/skills/` or `${FACTORY_HOME}/skills/`.
- Transitions:
  - absent → link to winning layer (install).
  - library link → re-pointed to winning layer (install; no-op when unchanged).
  - non-library path → unchanged, `skip:` printed (install).
  - library link → absent (uninstall). Non-library paths are never removed.
