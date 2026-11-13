# First-party skills render into the distribution

2026-11-07: `design-to-code` and `pen-design` are first-party skills in `core/skills/` again. The 2026-11-01 move back to the vendored `skills/` folder ended when that folder was replaced by the CLI-managed `.agents/skills/`, whose `skills-lock.json` only describes third-party sources ([ADR 0018](0018-vendored-skills-are-managed-by-the-skills-cli.md)).

The factory previously had exactly one skill of its own: the orchestrator, rendered into `dist/` (ADR 0005). Everything else in the skill library was vendored (`skills/`, tracked in `skills/SOURCES.md`) or per-user. The `design-to-code` skill — the write role's engine, with its modes, framework rules, scripts, tests and evals — and its `pen-design` dependency were homegrown but lived in the vendored layer, so the factory's core capability depended on folders `skills/SOURCES.md` does not own.

First-party skills now live in `core/skills/<name>/` next to `core/skills/factory/`, and the renderer copies every one that carries a `SKILL.md` — except `factory` itself — verbatim into `dist/<harness>/skills/<name>/`. The distribution therefore shows the factory's core skill set in one place, and `install.sh` links each rendered skill into the harness's skills root under its frontmatter name, before the vendored and per-user layers: a per-user skill with the same name wins, and a vendored skill with the same name is skipped as a variant. Core skills reach every harness; no SOURCES.md row can exclude them.

## Considered options

- **Keep them in `skills/`**: no installer change. But the vendored layer is defined by `skills/SOURCES.md` upstream rows, and a first-party skill there is unowned — nothing distinguishes it from a vendored copy, and a maintainer refreshing the library has no rule protecting it.
- **Link them from source** (`$src/core/skills/`): no copies. But the skills would be invisible in `dist/` — a consumer reading the rendered distribution would not see the factory's own skills — and ownership of a link would have to recognise a second source root.
- **Render them into `dist/<harness>/skills/`** (chosen): one distribution carries everything, the dist gate (`git status --porcelain -- dist/`, ADR 0005) proves the rendered skills match their sources, and the installer keeps a single rule for recognising its own links.

## Consequences

The rendered skills are identical across harnesses, so a source edit re-renders into all five trees — deliberate duplication, the same trade ADR 0005 accepts for the orchestrator skill. `library_link` treats `$factory_home/dist/` targets as the installer's own, so pruning, uninstall and adoption cover rendered-skill links too. A new first-party skill is a folder with a `SKILL.md` under `core/skills/`; no SOURCES.md row, no adapter change, and it appears in `dist/` on the next render.
