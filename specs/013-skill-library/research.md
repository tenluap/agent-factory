# Research: Factory Skill Library

## R1. Where library linking lives

- **Decision**: Extend `install.sh` with skill-library functions; no new script or Python module.
- **Rationale**: The installer already owns argument parsing, `FACTORY_HOME` policy, `--harness` selection, the `link`/`unlink_ours` symlink pattern and `--uninstall`. Library links are the same operation against another directory (FR-005, constitution V).
- **Alternatives considered**: A `tools/skills.py` helper (rejected: second entry point for the same install flow); rendering skills into `dist/` (rejected by FR-011).

## R2. How each harness's skills root is declared

- **Decision**: New `skills_root` key in every `adapters/<h>/adapter.json`, expanded by `render.py load_adapter` like `skill_dir`, and printed by `render.py <h> --paths` as `skills_root=...`. Values: claude-code `{home}/skills`, opencode `{home}/opencode/skills`, zcode `{home}/skills`, codex and copilot `~/.agents/skills`.
- **Home override**: `{home}` resolves from the adapter `home.env` exactly as for `skill_dir`, so `CLAUDE_HOME`, `ZCODE_HOME` and `XDG_CONFIG_HOME` move the root; the fixed Codex/Copilot value has no `{home}`, so `CODEX_HOME`/`COPILOT_HOME` do not.
- **Rationale**: FR-004 requires adapters to declare it. `install.sh` already `eval`s `--paths` output, so the installer gets the expanded root with zero new parsing. `skills_root` is not used in rendering, so `dist/` output is unchanged (FR-011).
- **Alternatives considered**: Deriving the root as `dirname(skill_dir)` (rejected: Copilot's `skill_dir` is `~/.copilot/skills/factory` but its settled skills root is `~/.agents/skills`); hard-coding roots in `install.sh` (rejected: breaks "a new harness is one adapter folder").

## R3. Which links are "ours"

- **Decision**: A library link is a symlink whose `readlink` target starts with `$src/skills/` (repo layer) or `$factory_home/skills/` (per-user layer). Install replaces only such links; any other existing path (file, directory, or symlink elsewhere) is skipped with `skip: <target> exists and is not a library link; to adopt it: ./install.sh --add-skill <target>, remove the original, re-run`. Uninstall removes only such links.
- **Rationale**: FR-007, FR-010 and the edge case "symlink pointing outside the library". The existing `link` helper replaces any symlink, so a separate `link_skill` helper is needed (ADR 0009). Ownership is checked on the `readlink` string, so a dangling link is classified without following it.
- **Name `factory`**: reserved (FR-005, FR-008). `install_skills` skips a `factory` folder in either layer with `skip: <layer>/factory: name reserved for the factory skill` before any link work, so the factory skill link is never touched.
- **Dot-folders**: folders whose name starts with `.` in either layer are ignored silently (covers a leftover `--add-skill` temp folder).

## R4. Precedence and shared roots

- **Decision**: Build the link set by listing repo-layer folders, then per-user folders; a per-user name overwrites the repo entry (FR-006). Only folders containing `SKILL.md` count, so `skills/SOURCES.md` is ignored. Linking an existing library link to the same target changes nothing on disk and prints `linked: <target>` again, like the existing `link` helper; re-pointing a library link from repo to per-user layer is allowed. Codex and Copilot share `~/.agents/skills`, so `--harness all` links each skill once and the second pass is idempotent.
- **Stale links**: before linking, `install_skills` scans the root for library links (R3) whose target no longer exists (`[ -L t ] && [ ! -e t ]`), removes each with `removed: <target>`, then links the winners, so a deleted per-user skill falls back to the repo copy when one exists. Dangling links pointing outside the library are user-owned and left alone.

## R5. `--add-skill` validation and copy

- **Decision**: Refuse if the path looks like a URL or is not an existing directory. The folder name is `basename` of the path as given (trailing `/` stripped), never of its resolved target, so the adoption hint works on an outside symlink. Refuse `factory` with `reserved: factory`. Parse `SKILL.md` frontmatter with inline `python3` stdlib (first line `---`, closing `---`, a `name:` line, quotes stripped), as the installer already does for `config.json`. Refuse naming the problem: `error: <path>: no SKILL.md`, `... no frontmatter`, `... name '<n>' does not match folder '<f>'`. If `$factory_home/skills/<name>` exists, print `exists: <path>` and exit 2. Only then `mkdir -p "$factory_home/skills"`, copy with `cp -RH` (follows the given path if it is a symlink, keeps inner links) into `$factory_home/skills/.<name>.tmp.$$` (removed with `rm -rf` if `cp` or `mv` fails), `mv` into place, print `added: <dest>`, then run the normal install for the selected harnesses.
- **Rationale**: Validation precedes any write, so refusals change nothing (US2 AS2-3). Temp-and-rename plus cleanup prevents a half-copied folder (ENG-26); the dot-prefixed temp name is never linked (R3). Name equals the folder basename, so it cannot contain `/` (ENG-25).
- **Combination**: `--add-skill` with `--uninstall` is a usage error (exit 2).

## R6. Vendoring the six skills

- **Decision**: For each skill, shallow-clone its upstream, record `git rev-parse HEAD`, copy the skill folder verbatim into `skills/<name>/`, and copy the upstream root `LICENSE` verbatim to `skills/<name>/LICENSE`. No offline fallback: a skill whose upstream repository and LICENSE cannot be obtained is not vendored (FR-002), and the gap is reported.
- Sources: `grilling` mattpocock/skills `skills/productivity/grilling`; `domain-modeling` mattpocock/skills `skills/engineering/domain-modeling`; `pr` mattpocock/skills `skills/in-progress/pr`; `ponytail` dietrichgebert/ponytail `skills/ponytail`; `tdd` backnotprop/pstack `skills/tdd`; `brainstorming` obra/superpowers `skills/brainstorming`. All MIT.
- `skills/SOURCES.md`: one table row per skill: name, source URL, path, commit, license.

## R7. Quality constraints

- **Security**: `--add-skill` takes a local path only; no network, no eval of skill content. Paths are quoted everywhere.
- **Data integrity**: never delete or overwrite non-library paths; refusals write nothing; atomic rename on add with temp cleanup; uninstall keeps both layers.
- **Compatibility**: bash and macOS/Linux `readlink` without `-f`; existing installs keep working (new links only).
- **Performance/observability**: six-plus folders, no concern; each action prints `linked:`, `skip:`, `removed:` or `exists:` as the installer does today.
- **Delivery**: CI already runs the suite, re-renders, checks dist porcelain and `bash -n install.sh`; no new CI.
