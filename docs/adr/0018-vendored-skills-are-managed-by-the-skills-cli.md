# Vendored skills are managed by the `skills` CLI in `.agents/skills/`

2026-11-07: the vendored library moved from `skills/` (hand-copied, provenance in `skills/SOURCES.md`) to `.agents/skills/`, which the [`skills` CLI](https://skills.sh) installs, updates and removes, with provenance in `skills-lock.json`. This supersedes ADR 0009's repo-layer path and the manual refresh rule; linking rather than rendering library skills (ADR 0009) still stands.

## Decision

1. **The lock decides membership.** A folder in `.agents/skills/` is a vendored skill only when its `SKILL.md` frontmatter name has an entry in `skills-lock.json`. The installer links exactly those, under their folder name, into every harness. Other tools write into the same folder: `specify init --integration codex` owns this checkout's `speckit-*` skills there, and they must stay project-local, since a globally linked copy would win `RESOLVE` in repositories that never ran `specify init`. Folders the lock does not own are reported with `skip:` and never linked.
2. **Copies are committed.** `skills add` copies each skill verbatim and the result is committed, so installing needs no Node, network or CLI, and an update is a reviewable diff. `skills update` refreshes them; `skills add` and `skills remove` curate the set.
3. **Licenses live beside the library.** The CLI copies a skill folder only, which drops repository-level licenses and notices. Each upstream source in the lock has its license (and any `NOTICE`) at `.agents/LICENSES/<owner>-<repo>.txt`, unless every skill from that source carries its own `LICENSE*` file. A test fails when a source has neither.
4. **No per-harness restriction.** The `SOURCES.md` `harnesses` column is gone with `SOURCES.md`. Its only user, `impeccable`, is now one upstream variant linked into every harness. If a skill needs excluding again, add a small overlay file then.
5. **First-party skills stay out of the lock.** `skills-lock.json` describes third-party sources, so `design-to-code` and `pen-design` returned to `core/skills/` and render into `dist/` (ADR 0012). Skills without a public upstream that are personal, not factory capabilities, belong in the per-user layer (`install.sh --add-skill`).
6. **Migration.** The installer treats links into the old `skills/` folder as its own: it removes them and links the `.agents/skills/` folder with the same name when the lock owns one. The browsing mirror in `${FACTORY_HOME}/skills/` follows the lock the same way.

## Considered options

- **Keep `skills/` and add `.agents/skills/` as a second layer**: no migration. But names overlap, so two sources of truth would need a precedence rule, and the manual refresh stays.
- **Link every folder in `.agents/skills/`**: no lock parsing. But it would link `specify`'s project-local speckit skills globally, shadowing the factory's speckit fallbacks.
- **Gitignore `.agents/skills/` and restore it from the lock at install**: a smaller repository. But installing would need Node, `npx` and network access, and upstream drift would arrive unreviewed.
- **Lock-owned, committed copies** (chosen): one managed folder, one rule for what is linked, reproducible installs.

## Consequences

Installer ownership recognises link targets under `.agents/skills/` and, for migration, the old `skills/`. A link to a folder the lock no longer owns is removed like a stale link. The `skills` CLI keys the lock by frontmatter name and names the folder after it (`X Money guide` -> `x-money-guide/`), so the installer reads frontmatter to match them. A skill whose file is not exactly `SKILL.md` (for example a lowercase `skill.md`) is invisible on case-sensitive file systems, and the layout test fails on it. Two exceptions were accepted at the move and are named in `tools/tests/test_skill_library.py`, which fails once either stops applying: `graphify` ships a lowercase `skill.md` and so works only where file names are case-insensitive, and `markpitt/claude-skills` (`avalonia`) publishes no license.
