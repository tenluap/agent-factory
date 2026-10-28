# Research: Factory Skill Library

## R1. Where library linking lives

- **Decision**: Extend `install.sh` with skill-library functions; no new script or Python module.
- **Rationale**: The installer already owns argument parsing, `FACTORY_HOME` policy, `--harness` selection, the `link`/`unlink_ours` symlink pattern and `--uninstall`. Library links are the same operation against another directory (FR-005, constitution V).
- **Alternatives considered**: A `tools/skills.py` helper (rejected: second entry point for the same install flow); rendering skills into `dist/` (rejected by FR-011).

## R2. How each harness's skills root is declared

- **Decision**: New `skills_root` key in every `adapters/<h>/adapter.json`, expanded by `render.py load_adapter` like `skill_dir`, and printed by `render.py <h> --paths` as `skills_root=...`. Values: claude-code `{home}/skills`, opencode `{home}/opencode/skills`, zcode `{home}/skills`, codex and copilot `~/.agents/skills`.
- **Rationale**: FR-004 requires adapters to declare it. `install.sh` already `eval`s `--paths` output, so the installer gets the expanded root with zero new parsing. `skills_root` is not used in rendering, so `dist/` output is unchanged (FR-011).
- **Alternatives considered**: Deriving the root as `dirname(skill_dir)` (rejected: Copilot's `skill_dir` is `~/.copilot/skills/factory` but its settled skills root is `~/.agents/skills`); hard-coding roots in `install.sh` (rejected: breaks "a new harness is one adapter folder").

## R3. Which links are "ours"

- **Decision**: A library link is a symlink whose `readlink` target starts with `$src/skills/` (repo layer) or `$factory_home/skills/` (per-user layer). Install replaces only such links; any other existing path (file, directory, or symlink elsewhere) is skipped with `skip: <target> exists and is not a library link; to adopt it: ./install.sh --add-skill <target>, remove the original, re-run`. Uninstall removes only such links.
- **Rationale**: FR-007, FR-010 and the edge case "symlink pointing outside the library". The existing `link` helper replaces any symlink, so a separate `link_skill` helper is needed.
- **Name `factory`**: the factory skill is linked first; a library skill named `factory` then meets a symlink into `dist/` and is skipped by the same rule. No special case.

## R4. Precedence and shared roots

- **Decision**: Build the link set by listing repo-layer folders, then per-user folders; a per-user name overwrites the repo entry (FR-006). Only folders containing `SKILL.md` count, so `skills/SOURCES.md` is ignored. Linking an existing library link to the same target is a no-op; re-pointing a library link from repo to per-user layer is allowed. Codex and Copilot share `~/.agents/skills`, so `--harness all` links each skill once and the second pass is idempotent.
- **Stale links**: a library link whose source folder was deleted is left in place until `--uninstall` (YAGNI; not in spec).

## R5. `--add-skill` validation and copy

- **Decision**: Resolve the path with `cd "$path" && pwd -P`; refuse if not an existing directory or if it looks like a URL. Parse `SKILL.md` frontmatter with inline `python3` stdlib (first line `---`, closing `---`, a `name:` line, quotes stripped), as the installer already does for `config.json`. Refuse naming the problem: `error: <path>: no SKILL.md`, `... no frontmatter`, `... name '<n>' does not match folder '<f>'`. If `$factory_home/skills/<name>` exists, print `exists: <path>` and exit non-zero. Copy with `cp -R` into `$factory_home/skills/.<name>.tmp.$$`, then `mv` into place, then run the normal install for the selected harnesses.
- **Rationale**: Validation precedes any write, so refusals change nothing (US2 AS2-3). Temp-and-rename prevents a half-copied folder on a failed copy (ENG-26). Name equals the folder basename, so it cannot contain `/` (ENG-25).
- **Combination**: `--add-skill` with `--uninstall` is a usage error (exit 2).

## R6. Vendoring the six skills

- **Decision**: For each skill, shallow-clone its upstream, record `git rev-parse HEAD`, copy the skill folder verbatim into `skills/<name>/`, and copy the upstream root `LICENSE` to `skills/<name>/LICENSE`. If the network is unavailable, copy `~/.agents/skills/<name>/` and record the `skillFolderHash` from `~/.agents/.skill-lock.json` in place of the commit.
- Sources: `grilling` mattpocock/skills `skills/productivity/grilling`; `domain-modeling` mattpocock/skills `skills/engineering/domain-modeling`; `pr` mattpocock/skills `skills/in-progress/pr`; `ponytail` dietrichgebert/ponytail `skills/ponytail`; `tdd` backnotprop/pstack `skills/tdd`; `brainstorming` obra/superpowers `skills/brainstorming`. All MIT.
- `skills/SOURCES.md`: one table row per skill: name, source URL, path, commit (or `lock:<hash>`), license.

## R7. Quality constraints

- **Security**: `--add-skill` takes a local path only; no network, no eval of skill content. Paths are quoted everywhere.
- **Data integrity**: never delete or overwrite non-library paths; refusals write nothing; atomic rename on add.
- **Compatibility**: bash and macOS/Linux `readlink` without `-f`; existing installs keep working (new links only).
- **Performance/observability**: six-plus folders, no concern; each action prints `linked:`, `skip:`, `removed:` or `exists:` as the installer does today.
- **Delivery**: CI already runs the suite, re-renders, checks dist porcelain and `bash -n install.sh`; no new CI.
