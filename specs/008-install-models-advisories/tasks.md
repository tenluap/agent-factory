# Tasks: Install model pipeline and round-3 advisory fixes

**Input**: `/specs/008-install-models-advisories/` — plan.md (required), spec.md, research.md, data-model.md, contracts/cli-delta.md, quickstart.md

**Tests**: mandatory — every implementation task is immediately preceded by a failing-test task naming the plan.md "Test seams" seam it targets (paired red/implement task structure, `Overridden: ENG-3` per plan.md); a plan-exempt task carries `Exempt: <part> - <reason>` instead; no other seam.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: parallelizable with the tasks beside it
- **[Story]**: spec.md user story (US1–US5)
- Every task names its file paths; code tasks name their seam

**Run tests**: `python3 -m unittest discover -s tools`.

**Build gate** (Constitution III): a task changing `core/skills/factory/bin/factory_cli/` ends with `for h in claude-code opencode codex copilot zcode; do python3 tools/render.py "$h"; done` and the rendered `dist/` drift committed so `test -z "$(git status --porcelain -- dist/)"` is clean afterwards; `tools/`, `install.sh`, `docs/` and `specs/` tasks render nothing.

**Setup (Phase 1)**: nothing to initialise — no new module, dependency or test runner (plan.md "New files, abstractions, dependencies"). **Foundational (Phase 2)**: none — the stories share only the existing suite and build gate.

---

## Phase 3: US1 — Personal model choices reach the installed agents (P1) 🎯 MVP

**Story goal**: `install.sh` links agents carrying the user's own models from a per-user render, while the committed `dist/` stays canonical and machine-independent.

**Independent Test**: sandbox install with `config.json` in the default home and `FACTORY_HOME` unset: linked agents and the models report carry the overrides and `git status --porcelain -- dist/` is empty (SC-001, quickstart S1).

- [ ] T001 [US1] Failing tests in `tools/tests/test_render_models.py` — seam: `tools/render.py` render output — the canonical `render.py <harness>` render never reads `config.json`: with overrides present and `FACTORY_HOME` exported, the rendered `dist/<harness>` model fields stay at adapter defaults (FR-002).
- [ ] T002 [US1] Implement canonical render purity in `tools/render.py`: the `dist/<harness>` path never loads user configuration, whatever the environment (FR-002; seam: `tools/render.py` render output).
- [ ] T003 [US1] Failing tests in `tools/tests/test_render_models.py` — seam: `tools/render.py` render output — `render.py <harness> --out <dir>` renders into `<dir>` with `${FACTORY_HOME:-~/.factory}/config.json` `models.<harness>` merged per key over the adapter defaults; an absent `config.json` or absent harness/model keys fall back per key (FR-001, FR-003).
- [ ] T004 [US1] Implement the default-home resolver (`${FACTORY_HOME:-~/.factory}`, expanded) and the per-user `--out <dir>` render merging `config.json` models per key in `tools/render.py` (FR-001, FR-003; seam: `tools/render.py` render output).
- [ ] T005 [US1] Failing tests in `tools/tests/test_render_models.py` — seam: `tools/render.py` render output — `--models` and `--paths` write nothing at all and `--models` reports the effective model per role resolved from the default home, `FACTORY_HOME` exported or not (FR-004).
- [ ] T006 [US1] Implement `--models` / `--paths` as write-free reports in `tools/render.py` (`--models` merges defaults with the default home's `config.json` per key) (FR-004; seam: `tools/render.py` render output).
- [ ] T007 [US1] Failing tests in `tools/tests/test_install.py` — seam: `install.sh` install/uninstall flow — under a throwaway `HOME`: each selected harness is rendered into `${FACTORY_HOME:-~/.factory}/dist/<harness>`, its `skill/` and `agents/*` link from that copy, the models report lists the effective models matching the linked agents, `git status --porcelain -- dist/` stays empty, and a second run re-links cleanly; the FR-005 default-home case (`FACTORY_HOME` unset, `config.json` at `~/.factory`) and the exported-`FACTORY_HOME` case both carry the overrides (FR-001, FR-002, FR-004, FR-005).
- [ ] T008 [US1] Implement the per-user render, linking and report in `install.sh`: render into `${FACTORY_HOME:-~/.factory}/dist/<harness>`, link `skill/` and `agents/*` from that copy, print the effective-model report, never render or dirty the committed `dist/` (FR-001, FR-002, FR-004, FR-005; seam: `install.sh` install/uninstall flow).
- [ ] T009 [US1] Failing tests in `tools/tests/test_install.py` — seam: `install.sh` install/uninstall flow — a nonexistent or unwritable factory home fails with a message naming the path, with no traceback and `git status --porcelain -- dist/` empty.
- [ ] T010 [US1] Implement the factory-home failure path in `install.sh` (create the render root or fail naming it, writing nothing to the repository) (seam: `install.sh` install/uninstall flow).
- [ ] T011 [US1] Failing tests in `tools/tests/test_install.py` — seam: `install.sh` install/uninstall flow — `--uninstall` removes only links pointing into the per-user copy (or the repository's `dist/`), leaves other files alone and never touches the repository's `dist/`.
- [ ] T012 [US1] Implement `--uninstall`'s identity-checked link removal in `install.sh` (FR-001; seam: `install.sh` install/uninstall flow).
- [ ] T013 [US1] Correct the model-merge wording to the delivered behaviour in `README.md`, `DESIGN.md` and the `tools/render.py` comment/docstring (FR-006). Exempt: `README.md`, `DESIGN.md` and `tools/render.py` comments - documentation only.

---

## Phase 4: US2 — Commands refuse cleanly, never crash (P2)

**Story goal**: every bad input and unsafe lock path exits with the documented code and a message naming the cause; nothing raises a traceback at the user.

**Independent Test**: each bad input through the CLI in the suite asserting exit code, message and absence of a traceback (SC-002, SC-003, quickstart S2).

- [ ] T014 [US2] Failing tests in `tools/tests/test_commands.py` — seam: `bin/factory` CLI command surface — `ledger-add --started-at/--ended-at` in every malformed shape (empty, wrong format, non-string) exits 5 naming the offending value, no traceback, and the value never reaches the duration arithmetic (FR-007).
- [ ] T015 [US2] Implement timestamp usage validation for `ledger-add` in `core/skills/factory/bin/factory_cli/cli.py` with `state.parse_iso`, calling `die_usage` (exit 5) naming the bad value (FR-007; seam: `bin/factory` CLI command surface); then the build gate.
- [ ] T016 [US2] Failing tests in `tools/tests/test_commands.py` — seam: `bin/factory` CLI command surface — a write targeting an ended run that is still pending is refused as not writable, with the ended status named (FR-009).
- [ ] T017 [US2] Extend the ended-run skip to pending-run selection in `core/skills/factory/bin/factory_cli/commands.py` so an ended pending run can never be mutated (FR-009; seam: `bin/factory` CLI command surface); then the build gate.
- [ ] T018 [US2] Failing tests in `tools/tests/test_lock.py` — seam: `factory_cli.lock` lifecycle — an owner PID the OS probe cannot evaluate (zero, negative, astronomically large, non-numeric) counts as live and never raises (FR-012).
- [ ] T019 [US2] Implement the liveness judgment in `core/skills/factory/bin/factory_cli/lock.py` `_alive`: unjudgeable PID → live, `ProcessLookupError` → gone, other `OSError` → live (FR-012; seam: `factory_cli.lock` lifecycle); then the build gate.
- [ ] T020 [US2] Failing tests in `tools/tests/test_lock.py` — seam: `factory_cli.lock` lifecycle — `lock take --force` takes over a live lock regardless of holder liveness (force evaluated before liveness) and without `--force` a live lock refuses with the owner reported (FR-013).
- [ ] T021 [US2] Implement force-first takeover in `core/skills/factory/bin/factory_cli/lock.py` `take` and `cmd_lock_take` (FR-013; seam: `factory_cli.lock` lifecycle); then the build gate.
- [ ] T022 [US2] Failing tests in `tools/tests/test_lock.py` — seam: `factory_cli.lock` lifecycle — a lock file replaced by another owner between write and release is left in place: `release` unlinks only the file whose identity (`st_dev`, `st_ino`) it just read (FR-014).
- [ ] T023 [US2] Implement identity-checked release in `core/skills/factory/bin/factory_cli/lock.py` `release` (FR-014; seam: `factory_cli.lock` lifecycle); then the build gate.

---

## Phase 5: US3 — Every state write goes through the one writer (P2)

**Story goal**: `rebind` and checkpoint mutate through `write_run` (lock, re-read under the lock, validate, atomic write), and validation enforces the relay-round invariant.

**Independent Test**: `rebind` under a competing lock, a checkpoint with a failing commit and its retry, and a relay with zero or two open rounds through the suite (SC-002, SC-005, quickstart S3).

- [ ] T024 [US3] Failing tests in `tools/tests/test_commands.py` — seam: `bin/factory` CLI command surface — `rebind <run> --worktree <path>` rewrites through the single writer: the run's lock is held and state re-read under it before `worktree`/`repo` are replaced (FR-008).
- [ ] T025 [US3] Implement `cmd_rebind` in `core/skills/factory/bin/factory_cli/commands.py` as a `mutate` passed to `write_run` instead of a direct `state.write_state` call (FR-008; seam: `bin/factory` CLI command surface); then the build gate.
- [ ] T026 [US3] Failing tests in `tools/tests/test_commands.py` — seam: `bin/factory` CLI command surface — a checkpoint whose git commit fails after the state write exits 1 with `state written, commit failed: <reason>`, its JSON carrying `commit: null` and `commit_error`, and a retry of the same stage reuses the pending history entry instead of appending a second one (FR-011).
- [ ] T027 [US3] Implement the checkpoint commit-failure report and the pending-entry reuse in `core/skills/factory/bin/factory_cli/commands.py` `cmd_checkpoint` (FR-011; seam: `bin/factory` CLI command surface); then the build gate.
- [ ] T028 [US3] Failing tests in `tools/tests/test_state.py` — seam: `factory_cli.state` module API — `validate_state` accepts exactly one open relay round and reports zero or several open rounds at `relay` / `relay.rounds[i]`, `validate` naming the location (FR-010).
- [ ] T029 [US3] Implement the exactly-one-open-relay-round rule in `core/skills/factory/bin/factory_cli/state.py` `validate_state` (FR-010; seam: `factory_cli.state` module API); then the build gate.

---

## Phase 6: US4 — Reports that tell the truth about time (P3)

**Story goal**: the digest aggregates come from union-based totals only, open runs show real elapsed wall clock, and aborted runs never appear where resume refuses them.

**Independent Test**: fixtures with two parallel spawns and with no `ended_at` checked through the digest and the totals sentence (SC-004, quickstart S4).

- [ ] T030 [US4] Failing tests in `tools/tests/test_totals.py` — seam: `factory_cli.totals` interval unions — a run without `ended_at` measures wall clock from `started_at` to now (non-zero, growing), `bounded` stays true when `started_at` exists, and human + agent never exceed wall clock (FR-016).
- [ ] T031 [US4] Implement open-run wall clock in `core/skills/factory/bin/factory_cli/totals.py` `compute` (`ended_at` or now) (FR-016; seam: `factory_cli.totals` interval unions); then the build gate.
- [ ] T032 [US4] Failing tests in `tools/tests/test_commands.py` — seam: `bin/factory` CLI command surface — with overlapping spawns the `show` digest's elapsed aggregates come from `totals` alone and the summed `waits.human_ms` / `spawns.agent_ms` duplicates are absent (FR-015).
- [ ] T033 [US4] Implement the digest's union-only aggregates in `core/skills/factory/bin/factory_cli/commands.py` `digest`, dropping the summed parallel duplicates (FR-015; seam: `bin/factory` CLI command surface); then the build gate.
- [ ] T034 [US4] Failing tests in `tools/tests/test_commands.py` — seam: `bin/factory` CLI command surface — `runs` skips aborted runs as it already skips `pr-open`, since resume refuses both (FR-017).
- [ ] T035 [US4] Implement the aborted-run skip in `core/skills/factory/bin/factory_cli/commands.py` `cmd_runs` (FR-017; seam: `bin/factory` CLI command surface); then the build gate.

---

## Phase 7: US5 — Documentation and tests match what ships (P3)

**Story goal**: tests exist once and share one vocabulary source; the contract and 007's plan record what was actually decided.

**Independent Test**: quickstart S5 — the replay reports the same 005/006 defects, `tools/tests/test_lock.py` defines each behaviour once, the contract carries `resume <run>`, 007's plan carries the override (FR-018–FR-021).

- [ ] T036 [US5] Failing tests in `tools/tests/test_lock.py` — seam: `factory_cli.lock` lifecycle — the module defines no test method twice and defines none after the runner's `unittest.main()` exit call, so each lock behaviour is exercised exactly once (FR-018).
- [ ] T037 [US5] Delete the dead duplicate `LockCliTests` methods after `unittest.main()` in `tools/tests/test_lock.py`, leaving each behaviour covered once (FR-018; seam: `factory_cli.lock` lifecycle).
- [ ] T038 [US5] Failing tests in `tools/tests/test_state.py` — seam: `tools/tests/replay.py` defect detectors — `tools/tests/replay.py` resolves `parse_iso`, `TIMELINE_KINDS`, `HISTORY_EVENTS` and the stage vocabularies from `factory_cli.state`, not private copies (FR-019).
- [ ] T039 [US5] Implement the import move in `tools/tests/replay.py` (shared vocabulary and timestamp parsing from `factory_cli.state`) so `python3 tools/tests/replay.py` still reports every 005/006 fixture defect (FR-019; seam: `tools/tests/replay.py` defect detectors), then close with the full suite, the build gate and quickstart.md S1–S5 (SC-006).
- [ ] T040 [US5] Document `resume <run>` in `specs/007-stabilise-factory/contracts/cli.md` in the same form as the other commands and align the `runs` wording with the aborted-run skip (FR-020). Exempt: `specs/007-stabilise-factory/contracts/cli.md` rows - documentation only.
- [ ] T041 [US5] Record `Overridden: ENG-3 - paired red/implement task structure` in `specs/007-stabilise-factory/plan.md` beside its seam confirmations, replacing `Overridden: none.` (FR-021). Exempt: `specs/007-stabilise-factory/plan.md` line - documentation only.

---

## Dependencies & Execution Order

- Phases run in story order US1 → US2 → US3 → US4 → US5 (P1 first); every test task immediately precedes its implementation task and fails until it lands.
- T004 precedes T006 (the report reuses the resolver); T008 depends on T002/T004/T006; T010 and T012 depend on T008.
- T019, T021, T023 all touch `tools/tests/test_lock.py` and `core/skills/factory/bin/factory_cli/lock.py` — run them in order; T036/T037 close that file afterwards.
- T025, T027, T033, T035 all touch `core/skills/factory/bin/factory_cli/commands.py` — in order; T031 precedes T033.
- T039 depends on T029 (the shared vocabulary lives in `state.py`); T040, T041 are independent documentation tasks.

## Parallel execution examples

- US2 after T008: T014/T015 ∥ T018/T019 (different files); US4: T030/T031 ∥ T032/T033.
- US5: T036/T037 ∥ T040 ∥ T041; US1's T009–T012 pairs run beside US2's lock pairs.

## Implementation strategy

MVP is US1: personal models reach the installed agents while `git status --porcelain -- dist/` stays empty after every installer run (quickstart S1). US2/US3 then harden the writer and the lock, US4 fixes the reporting, US5 the hygiene. Each `core/` task closes green under the build gate before the next opens; documentation corrections (T013, T040, T041) land with or before the item they describe. The run closes at T039 with the full suite, the build gate and quickstart.md S1–S5.
