---
description: "Task list for 017-per-project-models"
---

# Tasks: Per-project deep and standard models

**Input**: `specs/017-per-project-models/` (spec.md, plan.md)

**Tests**: Required (engineering.md). Each behaviour-changing task is one commit unit: failing test (red proof), implementation, passing check. Runner: `python3 -m unittest discover -s tools/tests -t .` (existing). Seams: plan.md "Test seams" (scope confirmed: Q13 accepted 2026-11-02, superseding Q2).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: parallel-safe (different files, no dependency)
- **[Story]**: US1-US6 from spec.md

## Phase 1: Setup

- [x] T001 Update `DESIGN.md` with project model layer `<repo>/.factory/config.json`, cascade (project → user → adapter, per key, empty string = inherit), `adapter_models.json` data file, `factory models` / `factory init`, `/factory init` route, state `models` block. Exempt: DESIGN.md - documentation only (constitution I: lands before core/adapter edits). Done: DESIGN.md names every item above.

## Phase 2: Foundational

- [x] T002 [US1] Add `core/skills/factory/bin/factory_cli/adapter_models.json` plus parity test in `tools/tests/test_render_models.py`.
  - Seam: `adapter_models.json` parity with `adapters/*/adapter.json`. Failure paths: none (drift fails test).
  - Red: add parity test first; it fails because `adapter_models.json` is missing.
  - Implement: write file mapping all five harnesses to `{deep, standard}` copied from each `adapters/<name>/adapter.json` `"models"`; `copilot` and `zcode` (`"models": {}`) get `{"deep": "", "standard": ""}`.
  - Pass: runner green; test asserts equality per harness (a tier absent from `adapter.json` counts as `""`, empties included) and same harness set.
  - Done: parity test passes; changing any value in either file makes it fail.

## Phase 3: User Story 1 + 2 - Resolver cascade and malformed stop (P1)

- [x] T003 [US1][US2] Add resolver `core/skills/factory/bin/factory_cli/models.py` with tests in new `tools/tests/test_models.py`.
  - Seam: `factory_cli.models.resolve(repo, home)`. Failure paths: invalid JSON in project config; invalid JSON in user config; non-object `models` or harness entry; unknown harness key; unknown tier key; non-string tier value.
  - Red: write tests first (temp dirs for repo and `FACTORY_HOME`): project beats user beats adapter per tier; per-key merge (project sets only `deep`); empty string kept as value with its layer's source; `copilot`/`zcode` with no project/user entry resolve to `""` with source `adapter`; missing file / missing `models` / missing harness fall through; no `.factory/` gives adapter values for all harnesses (SC-002); repo root from `cwd` inside a linked worktree (`git worktree add`) is the main checkout, so its `.factory/config.json` is read; each failure path (in project and in user config for unknown harness key, e.g. `opencod`) raises `ModelConfigError` whose message names the file path and detail (unknown harness/tier detail names the key and the known values). Run; fails on import.
  - Implement: `ModelConfigError(path, detail)`; `resolve` returns `{harness: {tier: (model, source)}}` over harnesses in `adapter_models.json`, rejecting harness keys outside it; strict reader separate from `commands.read_config()` (unchanged); `<repo>` is main checkout root = parent of `git rev-parse --path-format=absolute --git-common-dir`.
  - Pass: runner green.
  - Done: all listed cases asserted and passing.

## Phase 4: User Story 3 - `factory models [--json]` (P2)

- [x] T004 [US3] Wire `models [--json]` in `core/skills/factory/bin/factory_cli/cli.py` (dispatch + USAGE) using `models.py` report helper; tests in `tools/tests/test_models.py`.
  - Seam: `bin/factory` CLI command surface, `models [--json]`. Failure paths: malformed config (including unknown harness key) exits non-zero naming file and fix.
  - Red: subprocess tests on `core/skills/factory/bin/factory` with `cwd` = temp repo and `FACTORY_HOME` = temp dir: table rows `harness tier model source` for 5 x 2; `--json` gives `{harness: {tier: {"model", "source"}}}` with correct sources; malformed project or user config (invalid JSON; unknown harness key) exits 1, stderr contains `<path>: <detail>` and `Fix the file or delete it to fall back to the next layer.`; USAGE lists `models`. Run; fails (unknown command).
  - Implement: report formatter in `models.py`; dispatch and USAGE line in `cli.py`.
  - Pass: runner green.
  - Done: output and exit codes match tests.

## Phase 5: User Story 4 - `factory init` (P2)

- [x] T005 [US4] Wire `init` in `cli.py` (dispatch + USAGE) with `init` function in `models.py`; tests in `tools/tests/test_models.py`.
  - Seam: `bin/factory` CLI command surface, `init`. Failure paths: existing `config.json` refused with non-zero exit and byte-identical file; malformed user config stops init.
  - Red: tests first: init in clean repo writes `.factory/config.json` (sorted keys, five harnesses, both tiers, effective adapter+user values) and `.factory/config.README.md` (schema, precedence, defaults table with sources, restore steps); stdout table labels `adapter`/`user` and contains unverified-until-preflight note; `${FACTORY_HOME}/config.json` bytes unchanged; `models --json` values identical before and after init, sources become `project` (SC-004); `copilot`/`zcode` seeded as `""` labelled `adapter`; second init exits non-zero naming path and file stays byte-identical (SC-005); init with `config.json` present but README deleted still refuses (refusal keys on `config.json` alone); init with stale `config.README.md` but no `config.json` writes config and rewrites README; init with pre-existing empty `.factory/` succeeds; malformed user config makes init exit non-zero, no `.factory/config.json` created. Run; fails.
  - Implement: resolve with project layer ignored; write via temp file + `os.replace`; never write `${FACTORY_HOME}`; no model inventory probe.
  - Pass: runner green.
  - Done: all listed cases asserted and passing.

- [x] T006 Verification: run `python3 -m unittest discover -s tools/tests -t .`; full suite green (existing tests included). Done: zero failures recorded in commit message or run log.
      Note (2026-11-02): the documented `-t .` form is broken on Python 3.14 (imports 140 tests, 23 ModuleNotFoundError for the `tests` helper package); working form `python3 -m unittest discover -s tools/tests -t tools` = 343 tests, 342 pass, 1 pre-existing failure (`test_design_to_code_permissions_reach_only_supporting_adapters`, broken on origin/main by f9bc303 removing the design-to-code permissions block without updating the test). Zero new failures.

## Phase 6: User Stories 1, 2, 5, 6 - Skill prose (P1-P3)

- [x] T007 [US1][US2][US4][US5][US6] Edit `core/skills/factory/SKILL.md`: step 0 routes `init` (alongside `resume`/`improve`) to `SHELL: python3 <F>/bin/factory init`, show table, stop (FR-016); preflight resolves cascade via `factory models --json`, records `models: {resolved: {deep, standard}, source: {deep, standard}}` for run harness in state (FR-005), stops on non-zero exit showing CLI message (FR-008); on resume compares with recorded block and discloses each changed tier `old (source) -> new (source)`, overwrites, continues (FR-009); every `SPAWN`/`SPAWN_PARALLEL` passes resolved model for agent's tier (FR-006); disclosure step for harnesses whose spawn cannot take a model (FR-007), worded harness-neutral. Exempt: SKILL.md - documentation only. Done: each FR above cited by a prose step; no harness tool names in core.

- [ ] T008 [P] [US1] Edit `core/skills/factory/references/verbs.md`: `SPAWN`/`SPAWN_PARALLEL` carry resolved model for tier; empty string = inherit session model. Exempt: verbs.md - documentation only. Done: verb definition names model input.

- [ ] T009 [P] [US1][US5] Edit `core/skills/factory/references/state.md`: v5 additive `models` block (`resolved`, `source` per tier); absent block on older states means not yet resolved. Exempt: state.md - documentation only. Done: schema and resume semantics documented.

## Phase 7: User Stories 1, 6 - Adapter prose

- [ ] T010 [P] [US1] Edit `adapters/claude-code/harness.md` and `adapters/opencode/harness.md`: map `SPAWN` model input to spawn tool `model` parameter; empty string omits parameter. Exempt: adapters/*/harness.md - documentation only. Done: both files state the mapping.

- [ ] T011 [P] [US6] Edit `adapters/codex/harness.md`, `adapters/copilot/harness.md`, `adapters/zcode/harness.md`: spawn cannot take a model; preflight discloses that project/user models cannot apply when any source is `project`/`user`, continue on installed selections. Exempt: adapters/*/harness.md - documentation only. Done: all three state the disclosure.

## Phase 8: Polish and verification

- [ ] T012 Render-side check: confirm core `SKILL.md`/references stay harness-neutral (no adapter tool names; adapter specifics only in `adapters/*/harness.md`); `tools/render.py`, `install.sh` untouched (`git diff --stat main -- tools/render.py install.sh` empty, FR-017); run `python3 tools/render.py` and confirm `adapter_models.json` appears under each `dist/<harness>/skills/factory/bin/factory_cli/`. Exempt: verification only. Done: checks recorded.

- [ ] T013 Final verification: `python3 -m unittest discover -s tools/tests -t .` green; render parity/dist tests green. Done: zero failures.

## Dependencies

- T001 first. T002 before T003 (resolver reads `adapter_models.json`). T003 before T004, T005. T004 before T005 (init tests use `models --json`). T006 after T005.
- T007 after T004 (prose calls `factory models --json`). T008, T009, T010, T011 parallel with each other and independent of T007 (separate files); start after T004.
- T012, T013 last.

## Implementation Strategy

MVP = T001-T006 (CLI resolver, report, init, tested). Then prose T007-T011 enabling runs to use resolved models. Then T012-T013.
