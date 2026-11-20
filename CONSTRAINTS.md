# Constraints

Last reviewed: 2026-11-20 by @tenluap

## Floor (always enforced, no setup required)

- No new suppression comments: `# noqa`, `# type: ignore`, `# pylint: disable`
- No unimplemented stubs: `raise NotImplementedError` without a plan-declared exemption, empty `except:` or `except: pass`, a `TODO` standing where the implementation belongs
- No skipped or deleted tests without the reason in the commit message (`@unittest.skip`)
- No secrets in source
- `dist/` is never committed or hand-edited (Constitution III)
- Behavior changes update `DESIGN.md` first (Constitution I); `core/` stays harness-neutral (Constitution II)
- This file does not get weakened to make a change pass

## Enforced with numbers

| Dimension | Rule | Checked by | Runs at |
|-----------|------|-----------|---------|
| Tests | Full unittest suite green | `python3 -m unittest discover -s tools` | task end, CI |
| Trigger hook | 7/7 pass | `node --test tools/tests/test_design_to_code_trigger.mjs` | task end |
| Render | All five harnesses render cleanly | `for h in $(python3 tools/render.py --list); do FACTORY_HOME="$(mktemp -d)" python3 tools/render.py "$h"; done` | before push, CI |
| Dist untracked | 0 tracked files under `dist/` | `test -z "$(git ls-files -- dist/)"` | CI |
| Installer | Syntax valid | `bash -n install.sh` | CI |

Every row names the command that produces the verdict. A dimension with a number and no
command in the `Checked by` column is an aspiration, not a constraint.

## Measured, not yet enforced

| Metric | Today | Direction |
|--------|-------|-----------|
| Suite size | 739 tests, ~9 min wall | must not fall |
| Fast path | module run, seconds | must stay out of the edit loop |

## Exceptions

| ID | Rule | Path | Reason | Owner | Expires |
|----|------|------|--------|-------|---------|
| E1 | Tests: suite green | `tools/tests/test_skill_library.py`, `tools/tests/test_render_models.py` | Uncommitted move of first-party skills `core/skills/` → `.agents/skills/` leaves 5 errors + 2 failures on the working tree as of 2026-11-20; resolve with the move, not by weakening assertions | @tenluap | 2027-02-18 |

Resolved 2026-11-20: the move completed as ADR 0019 — the four skills are lock-owned local library entries, the renderer no longer emits `dist/<harness>/skills/`, and the suite is green with the assertions rewritten for the new layout, not weakened. E1 is closed and kept here for the record.
