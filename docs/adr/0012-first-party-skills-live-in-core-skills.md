# First-party skills live in core/skills

The factory previously had exactly one skill of its own: the orchestrator, rendered into `dist/` (ADR 0005). Everything else in the skill library was vendored (`skills/`, tracked in `skills/SOURCES.md`) or per-user. The `design-to-code` skill — the write role's engine, with its modes, framework rules, scripts, tests and evals — and its `pen-design` dependency were homegrown but lived in the vendored layer, so the factory's core capability depended on folders `skills/SOURCES.md` does not own and any checkout could prune without breaking the factory's own contract.

First-party skills now live in `core/skills/<name>/` next to `core/skills/factory/`. The installer links each one from source into every harness's skills root under its frontmatter name — the same linked-not-rendered rule as the library (ADR 0009) — with `core/skills/factory` still excluded, because it reaches the harness through the rendered distribution. Core skills take precedence over vendored skills with the same name; the per-user layer still wins over both.

## Considered options

- **Keep them in `skills/`**: no installer change. But the vendored layer is defined by `skills/SOURCES.md` upstream rows, and a first-party skill there is unowned — nothing distinguishes it from a vendored copy, and a maintainer refreshing the library has no rule protecting it.
- **Render them into `dist/<harness>/`**: one install path for everything. But it would duplicate every core skill across all five harness dists in tracked output, coupling the dist gate to content that never varies per harness — exactly what ADR 0009 rejected for library skills.
- **Link from source under `core/skills/`** (chosen): updates take effect with no reinstall, ownership is decidable (a link into `$src/core/skills/` is the installer's own), and the per-user precedence rule keeps working unchanged.

## Consequences

`library_link` recognises `$src/core/skills/` targets, so pruning, uninstall and adoption treat core-skill links like library links. The install loop walks `core/skills/` between the repo layer and the per-user layer, skipping `core/skills/factory`; a core skill whose frontmatter name matches a per-user skill is skipped for that harness. A new first-party skill is a folder with a `SKILL.md` under `core/skills/` — no SOURCES.md row, no render step, no adapter change.
