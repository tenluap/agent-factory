# Factory-authored skills live in the library as local entries

2026-11-20: the four factory-authored skills — `create-project-agents-file`, `design-to-code`, `pen-design` and `prompt-optimiser` — moved from `core/skills/` into the CLI-managed library `.agents/skills/`, each with a `"sourceType": "local"` lock entry ([ADR 0018](0018-vendored-skills-are-managed-by-the-skills-cli.md)). This supersedes [ADR 0012](0012-first-party-skills-live-in-core-skills.md): the factory no longer keeps a first-party skill layer, and the renderer no longer produces `dist/<harness>/skills/`.

## Decision

1. **One source of skills: the library.** `core/skills/` holds only the orchestrator (`factory`), which still renders into `dist/<harness>/skill/` (ADR 0005). Every other skill the factory authors lives in `.agents/skills/` as the original, edited in place, with a local lock entry; `skills update` skips it and the license check exempts it (ADR 0018, rule 5).
2. **The lock decides linking, as before.** The installer's single rule — link a library folder when its frontmatter name has a lock entry — now covers the factory's own skills with no special case. A per-user skill still wins on name collision; the former first-party tier between per-user and vendored is gone.
3. **No rendered skills.** `dist/<harness>/` carries the orchestrator skill and the role agents only. Library skills are linked, not rendered (ADR 0009), and that now holds for every non-orchestrator skill.

## Considered options

- **Keep rendering them from `core/skills/`** (ADR 0012, dropped): one distribution carries everything. But it needed a second skill source root, a second installer rule and a precedence tier between per-user and vendored, all to express ownership that the lock's `sourceType: local` already expresses.
- **Link them from `core/skills/` at install time**: no copies, but links into a moving checkout go stale, and ownership still needed a rule outside the lock.

## Consequences

A factory skill is added, renamed or removed with the same operations as a vendored skill: edit the folder, keep the lock entry, commit. The skill library tests (`tools/tests/test_skill_library.py`) require each of the four to stay a lock-owned local entry whose folder name and frontmatter name agree. Installs from before this decision have skill links into the rendered distribution's `skills/` folder; the renderer no longer creates that folder, so the links die on the next render and the stale-link rule prunes them before the lock-owned library links take over.
