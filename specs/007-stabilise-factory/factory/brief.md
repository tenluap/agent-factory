# Brief: stabilise and optimise the factory

Deliver every item of `docs/stability-brief.md` (S1–S19) so Agent Factory meets the brief's definition of "stable": trustworthy state written only through the CLI, invariants enforced by code, proven recovery, accurate reports and automatic regression checks. In the same change, trim the orchestrator's context where bookkeeping prose moves into the CLI. Inputs: `docs/stability-brief.md`, `docs/product-brief.md`, `DESIGN.md`, and `Harness-agnostic factory design and plan.md`.

## Decisions

- Scope: all of S1–S19 (P0, P1, P2), plus a context trim: S19 and removal of SKILL.md/reference prose made redundant by the CLI.
- Shape: one run, one PR; tasks ordered by milestone M1 (state), M2 (gates), M3 (portable and safe), M4 (proven), then P2.
- State schema bumps to version 4. Readers accept versions 1–4; writers upgrade a run on its first write.
- State writes go only through the CLI. The orchestrator never hand-edits `state.json`; missing Python 3 halts the run (no manual write fallback).
- CLI layout: `bin/factory` stays a thin entry script; logic lives in modules under `bin/factory_cli/`; the renderer copies the folder into `dist/`.
- S10: only the Claude Code adapter ships default models (opus/sonnet). Codex, Copilot, OpenCode and ZCode ship empty models (inherit the session). Personal model choices live in `${FACTORY_HOME}/config.json`; the current personal OpenCode picks are moved there for the user.
- S14: ship a fixture repository, a scripted golden-run checklist, and automated CLI-level kill-and-resume tests. The live two-harness golden run is recorded after merge, not inside this run.
- S15: verify read-only access with a static test of rendered agent permissions; document harnesses that cannot enforce it.
- `Harness-agnostic factory design and plan.md` moves to `docs/` with its status marked implemented.
- The 005/006 run states recoverable from git history serve as `validate` fixtures with their known defects.
- Out of scope: renaming the repository; the brief's §6 exclusions.
- Commands: build re-renders all five harnesses and fails on any `dist/` diff; test is `python3 -m unittest discover -s tools` (extend discovery as new test folders are added).
- Chain: full. Fast mode on.
