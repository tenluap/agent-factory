# Brief: factory skill library

The factory gains a two-layer skill library. The repository's `skills/` directory ships vendored copies of the six skills the factory itself requires, and `${FACTORY_HOME}/skills/` holds skills the user adds manually. `./install.sh` symlinks both layers into each installed harness's skill directory, so the skills the user relies on are managed, versioned and installed from one place, and factory preflight no longer stops on missing required skills once the library is installed.

## Decisions

- Library model: a bundled skill library installed globally by `install.sh`, using the same symlink pattern as the factory skill and role agents (Q1).
- Contents: seeded with the factory-required skills (`grilling`, `domain-modeling`, `pr`, `ponytail`, `tdd`, `brainstorming`); the user can manually add any other skills (Q2).
- Build command: render all five harnesses with `python3 tools/render.py <harness>` and fail on `git diff --exit-code -- dist/`. Test command: `python3 -m unittest discover -s tools` (Q3, matches CI).
- Two layers (Q4): repo layer `skills/<name>/` (committed) holds the factory-required set; per-user layer `${FACTORY_HOME}/skills/<name>/` (never committed) holds the user's manual additions. On a name clash the per-user copy wins.
- Third-party skills are vendored verbatim with attribution (Q5): keep each upstream LICENSE, and record source URL, path, commit and license per skill in `skills/SOURCES.md`. A skill whose license forbids redistribution is not vendored. All four upstreams (mattpocock/skills, dietrichgebert/ponytail, backnotprop/pstack, obra/superpowers) are MIT.
- Manual add (Q6): `./install.sh --add-skill <path>` copies an existing skill folder into the per-user layer after validating that `SKILL.md` exists with frontmatter whose `name` matches the folder name, then links it. Dropping a folder into the per-user layer by hand and re-running `./install.sh` also works.
- Link targets (Q7): each adapter declares its harness's skills root (Claude Code `~/.claude/skills`, OpenCode `~/.config/opencode/skills`, Codex/Copilot `~/.agents/skills`, ZCode `~/.zcode/skills`); `--harness` selects which roots are linked, as for the factory skill.
- Conflicts (Q8): a target that exists and is not a symlink is skipped with a `skip:` message explaining how to adopt it (add it with `--add-skill`, remove the original, re-run). The installer never deletes or overwrites user files.
- `--add-skill` name clash (Q9): refuse with `exists: <path>`; to update, delete the per-user folder and re-add.
- `--add-skill` source (Q10): local folder path only; no git fetching.
- Refreshing vendored skills (Q11): manual. A maintainer re-copies the skill and updates its `skills/SOURCES.md` row; no sync tool.
- `--uninstall` removes only links that point into the library layers.
- Preflight `RESOLVE` is unchanged: linked library skills resolve through the existing search order.
- Library skills are linked directly from their source folders, not rendered into `dist/`, so there is no dist drift.
- Tests in `tools/tests` cover linking, conflict skip, add, add clash, per-user precedence and uninstall; README and DESIGN.md document the library.
- Chain: lite (specify, plan, tasks, analyze), fast mode on (Q12).
