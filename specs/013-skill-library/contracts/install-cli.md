# Contract: `install.sh` and `render.py --paths`

## `./install.sh [--harness <name>|all] [--add-skill <path>] [--uninstall]`

Existing behaviour unchanged. Additions:

| Invocation | Effect | Exit |
|---|---|---|
| install (no `--add-skill`) | After factory skill and agents: link every library skill (per-user wins) into each selected harness's `skills_root`. Prints `linked: <target>` or `skip: <target> exists and is not a library link; to adopt it: ./install.sh --add-skill <target>, remove the original, re-run` per skill. | 0 |
| `--add-skill <path>` valid | Copy folder to `${FACTORY_HOME}/skills/<name>/`, print `added: <dest>`, then the normal install. | 0 |
| `--add-skill` path missing / not a directory / URL | `error: <path>: not a local directory`; nothing written. | 2 |
| `--add-skill` no `SKILL.md` / no frontmatter / name mismatch | `error: <path>: <problem>`; nothing written. | 2 |
| `--add-skill` destination exists | `exists: <dest>`; nothing written. | 2 |
| `--add-skill` without a value, or with `--uninstall` | usage error. | 2 |
| `--uninstall` | Also removes every library link in each selected `skills_root`, printing `removed: <target>`. Never removes non-library paths or either layer's folders. | 0 |

## `python3 tools/render.py <harness> --paths [--out <dir>]`

Prints, shell-quoted, one per line: `dist=`, `skill_dir=`, `agent_dir=`, and new `skills_root=` (home-expanded). Writes nothing.
