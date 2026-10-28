# Contract: `install.sh` and `render.py --paths`

## `./install.sh [--harness <name>|all] [--add-skill <path>] [--uninstall]`

Existing behaviour unchanged. Additions:

| Invocation | Effect | Exit |
|---|---|---|
| install (no `--add-skill`) | After factory skill and agents, per selected harness's `skills_root`: first remove each library link whose source is gone (`removed: <target>`); then link every library skill (per-user wins; dot-folders ignored) and print `linked: <target>` (also for an unchanged link) or `skip: <target> exists and is not a library link; to adopt it: ./install.sh --add-skill <target>, remove the original, re-run`. A `factory` folder in either layer prints `skip: <layer>/factory: name reserved for the factory skill`. | 0 |
| `--add-skill <path>` valid | Name = basename of `<path>` as given. Create `${FACTORY_HOME}/skills/` if absent, copy via a dot-prefixed temp folder (removed on failure) to `${FACTORY_HOME}/skills/<name>/`, print `added: <dest>`, then the normal install. | 0 |
| `--add-skill` path missing / not a directory / URL | `error: <path>: not a local directory`; nothing written. | 2 |
| `--add-skill` name `factory` | `reserved: factory`; nothing written. | 2 |
| `--add-skill` no `SKILL.md` / no frontmatter / name mismatch | `error: <path>: <problem>`; nothing written. | 2 |
| `--add-skill` destination exists | `exists: <dest>`; nothing written. | 2 |
| `--add-skill` without a value, or with `--uninstall` | usage error. | 2 |
| `--uninstall` | Also removes every library link in each selected `skills_root`, printing `removed: <target>`. Never removes non-library paths or either layer's folders or contents. Codex and Copilot share `~/.agents/skills`, so uninstalling one removes the other's library links. | 0 |

## `python3 tools/render.py <harness> --paths [--out <dir>]`

Prints, shell-quoted, one per line: `dist=`, `skill_dir=`, `agent_dir=`, and new `skills_root=` (home-expanded; follows `CLAUDE_HOME`, `ZCODE_HOME`, `XDG_CONFIG_HOME`; Codex/Copilot always `~/.agents/skills`). Writes nothing.
