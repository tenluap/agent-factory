---
description: "Task list for 018-live-conformance"
---

# Tasks: Live-conformance unblockers

**Input**: `specs/018-live-conformance/` (spec.md, plan.md, research.md, data-model.md, contracts/bench-cli.md, quickstart.md)

**Tests**: Required (engineering.md). Each behaviour-changing task is one commit unit: failing test (red proof), implementation, passing check, committed together. Runner: `python3 -m unittest discover -s tools` (existing); focused: `python3 -m unittest discover -s tools -p test_bench.py`. Seams: plan.md "Test seams" (scope confirmed: plan Q1 accepted 2026-11-04; snapshot `specs/018-live-conformance/factory/relay/plan-Q1.md`). No test runs a real `claude` or `opencode` binary or spends tokens (FR-015).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: parallel-safe (different files, no dependency on an incomplete task)
- **[Story]**: US1-US5 from spec.md

## Phase 1: Setup

- [ ] T001 Update the "Benchmark" bullet in `DESIGN.md` (section "Time budget, issues, improvement backlog, benchmark"): `run` options `--model` (forwarded as `claude --model` / `opencode run -m`) and `--from-checkout` (isolated `install.sh` render under the output directory; exclusive with `--home`); the scoped Claude Code grant (`--add-dir` output directory plus skill directory in use; `--allowedTools Read Edit Write Agent Skill Bash(git:*) Bash(python3:*) Bash(<skill_dir>/bin/factory:*)`; never a bypass mode); `provenance.json` written before launch; `score` entries carry `provenance` or a missing marker without changing `pass`. Exempt: `DESIGN.md` benchmark bullet - documentation only (constitution I: lands before the `tools/bench.py` changes). Done: the bullet names every item above.

## Phase 2: Foundational

None. The stub-harness test helper is test code built inside T002's commit unit and reused by T003, T005.

## Phase 3: User Stories 1 + 2 - Scoped Claude Code launch and model choice (P1)

**Goal**: headless launches carry exactly the scoped grant and an optional model. **Independent test**: stubbed `bench.py run` for both harnesses, with and without `--model`; inspect recorded argv.

- [ ] T002 [US1][US2] Add `launch_command` and `--model` to `tools/bench.py` with a new `RunTests` class in `tools/tests/test_bench.py`.
  - Seam: `bench.py run` CLI (plan seam 1). Failure path: selected harness executable missing.
  - Test helper (test code): write Python stub executables `claude` and `opencode` (shebang `sys.executable`) into a temp `bin/` placed first on `PATH`; each appends one JSON line `{argv, env}` (env limited to `FACTORY_HOME`, `FACTORY_HARNESS`, `CLAUDE_CONFIG_DIR`, `CLAUDE_HOME`, `XDG_CONFIG_HOME`) to a record file named by `STUB_RECORD`; `--version` prints `<name> 9.9.9-stub` unless `STUB_VERSION_FAIL` is set (then exits 3); other calls exit with `STUB_EXIT` (default 0). The run subprocess gets sandboxed `HOME`, `CLAUDE_HOME`, `XDG_CONFIG_HOME`, `FACTORY_HOME` under a temp dir.
  - Red: write tests first: Claude Code argv starts `claude -p <prompt>`, the prompt directly after `-p`; contains `--add-dir <out>`; contains `--allowedTools` followed by exactly `Read Edit Write Agent Skill Bash(git:*) Bash(python3:*) Bash(<skill_dir>/bin/factory:*)` where `<skill_dir>` is the sandboxed `CLAUDE_HOME/skills/factory`; `--add-dir` entries for the skill directory (link path and resolved target) and for a `--home` outside `<out>`, each once, none already inside `<out>`; never `--dangerously-skip-permissions`, `--permission-mode` or a bare `Bash` element (US1-1, US1-2, SC-001); OpenCode argv is `opencode run <prompt>` with no Claude Code option (US1-3); `--model sonnet` gives `claude ... --model sonnet` and `--model p/m` gives `opencode run -m p/m <prompt>`; without `--model` neither option appears (US2, SC-002); missing executable: `PATH` holds only the other harness's stub, exit 1, stderr contains `use the manual benchmark fallback`, `--out` directory not created. Run; launch and model tests fail (no `--model` option, plain `claude -p <prompt>`).
  - Implement: pure `launch_command(harness, prompt, *, model, out, home, skill_dir)` returning argv per contracts/bench-cli.md "Launch commands"; `skill_dir` from `render.load_adapter(harness)["skill_dir"]` with `~` expanded (installed mode); `--add-dir` deduplicated and omitted when inside `<out>`; `--model` argparse option on `run`; `run` launches `launch_command(...)` in place of `[*driver, prompt]`; executable check stays before any directory is created.
  - Pass: runner green, existing `ScoreTests` unchanged.
  - Done: every assertion above passes; a test asserting the forbidden options never appear covers both harnesses with and without `--model`.

## Phase 4: User Story 3 - Isolated checkout render (P1)

**Goal**: `--from-checkout` renders this checkout under `<out>` and launches against it. **Independent test**: stubbed checkout run; rendered files under `<out>`, config location pointed there, sandboxed homes unchanged.

- [ ] T003 [US3] Add `--from-checkout` and `isolated_install` to `tools/bench.py`; tests in `RunTests`.
  - Seam: `bench.py run` CLI (plan seam 1). Failure paths: isolated install fails; `--from-checkout` combined with `--home`.
  - Red: tests first: Claude Code checkout run renders `<out>/home/dist/claude-code` and `<out>/harness-config/skills/factory`; stub env has `CLAUDE_CONFIG_DIR` and `CLAUDE_HOME` = `<out>/harness-config`, `FACTORY_HOME` = `<out>/home`; `--allowedTools` factory entry uses `<out>/harness-config/skills/factory/bin/factory`; no `--add-dir` beyond `<out>` (the isolated skill directory lies inside it) (US3-1); OpenCode checkout run renders `<out>/home/dist/opencode` and stub env has `XDG_CONFIG_HOME` = `<out>/harness-config` (US3-2); without the flag no `<out>/home/dist` and no `<out>/harness-config` exist and launch env matches T002 (US3-3, FR-005); isolation (SC-004): sha256 snapshot of every file and symlink target under the sandboxed `HOME`, `CLAUDE_HOME` and `XDG_CONFIG_HOME` before and after a checkout run is identical; install failure: a stub `bash` first on `PATH` exits 7, run exits 1, stderr contains `benchmark run: checkout render failed (exit 7):` and the stub's output tail, harness record file absent (US3-4, FR-006); `--from-checkout --home <dir>` exits 2 with an argparse error and creates neither `--out` nor `<dir>`. Run; fails (unknown option).
  - Implement: `--from-checkout` and `--home` in an argparse mutually exclusive group; `isolated_install(harness, out)` creates `<out>/home` and `<out>/harness-config` (install.sh requires an explicit `FACTORY_HOME` to exist), runs `["bash", ROOT / "install.sh", "--harness", harness]` resolved through `PATH` with env `FACTORY_HOME=<out>/home`, the adapter `home.env` variable = `<out>/harness-config`, `HOME=<out>`; non-zero exit raises `ValueError` with the exit code and the last lines of combined output; called after the output directory exists and before fixture copy (contract "Order of effects"); launch env adds `CLAUDE_CONFIG_DIR`+`CLAUDE_HOME` (Claude Code) or `XDG_CONFIG_HOME` (OpenCode); skill directory from `render.load_adapter` under the isolated environment.
  - Pass: runner green.
  - Done: all cases above pass; no test writes outside its temp directories.

## Phase 5: User Story 4 - Provenance record and score (P2)

**Goal**: every run writes `provenance.json` before launch; scores carry it. **Independent test**: stubbed runs and `score` over their states.

- [ ] T004 [US4] Add `checkout_provenance(path)` and `tree_digest(path)` to `tools/bench.py`; tests in new `ProvenanceTests` in `tools/tests/test_bench.py` (import `bench` from `tools/`).
  - Seam: `bench.checkout_provenance(path)` (plan seam 3). Failure path: path is not a git repository.
  - Red: tests first with `Sandbox` repos: clean repo gives `revision` = `git rev-parse HEAD`, `changed_paths` = `[]`, `diff_sha256` = `null` (US4-1, data-model "`changed_paths` is `[]` and `diff_sha256` is `null` for a clean checkout"); edited tracked file plus a new untracked file gives both paths in `changed_paths` and `diff_sha256` = sha256 of `git diff HEAD --binary` (US4-2, "`diff_sha256` covers tracked changes only; untracked paths appear in `changed_paths`"); an untracked-only change lists the path and gives `diff_sha256` = `null` (empty tracked diff); a plain temp directory gives `revision`, `changed_paths`, `diff_sha256` all `"unavailable"` and raises nothing ("both are `"unavailable"` when git cannot report"); `tree_digest` equals the data-model formula ("sha256 over each regular file under the directory (symlinks followed), in sorted relative-path order, of `<relative path>\0<sha256 of bytes>\n`") and changes when one byte changes. Run; fails on missing function.
  - Implement: git calls with `capture_output`, `text`, `timeout=10`; any `OSError`, `CalledProcessError` or `TimeoutExpired` yields `"unavailable"`; `path` is the checkout root (`ROOT`) when called by `run`.
  - Pass: runner green.
  - Done: all cases above pass.

- [ ] T005 [US4] Write `<out>/provenance.json` before launch in `tools/bench.py` (`write_provenance`); tests in `RunTests`.
  - Seam: `bench.py run` CLI (plan seam 1). Failure paths: harness exits non-zero; harness `--version` fails; installed factory absent.
  - Red: tests first: an installed-mode run writes a record matching data-model.md keys (`version` 1, `written_at`, `bench`, `harness`, `model`, `repo` = `<out>/fixture-<bench>`, `checkout`, `render`, `installed_factory`, `harness_versions`) with `render` = `{"mode": "installed", "digest": "none"}` ("`render.digest` is `"none"` exactly when `render.mode` is `installed`") (US4-3); a checkout-mode run has `render.mode` `checkout` and `render.digest` = `tree_digest(<out>/home/dist/<harness>)`; `harness_versions` holds both stub `--version` outputs; stdout JSON gains `"provenance": "<out>/provenance.json"` with existing keys unchanged; with `ANTHROPIC_API_KEY=stub-secret` in the run env, `stub-secret` is absent from the record ("The record never contains credentials or environment values"); `STUB_EXIT=5`: run exits 1 and `provenance.json` exists; `STUB_VERSION_FAIL`: both versions `"unavailable"`, run exits 0 (US4-5, FR-008); empty sandboxed adapter home: `installed_factory` `skill_dir` and `digest` `"unavailable"`, run continues. Run; fails (no file).
  - Implement: `write_provenance` after pending-state seeding and before launch ("Written before the harness launches; never rewritten by the run"); versions via `[name, "--version"]` with `timeout=10`, missing, non-zero or timeout = `"unavailable"`; installed factory from `render.load_adapter(harness)` under the driver's own environment (the maintainer's installed baseline), resolved path and `tree_digest`, `"unavailable"` when absent.
  - Pass: runner green.
  - Done: all cases above pass; SC-003 holds for both modes.

- [ ] T006 [US4] Add `load_provenance(state)` to `tools/bench.py` and the `provenance` key to each `score` entry; tests in `ScoreTests`.
  - Seam: `bench.py score` CLI (plan seam 2). Failure paths: no `provenance.json`; malformed `provenance.json`; record `repo` differs from the state's `repo`; unreadable state.
  - Red: tests first: a state whose `repo` is `<dir>/fixture-greet-001` with a matching `<dir>/provenance.json` gives that record under `provenance` and the same `pass` as before (US4-4); absent file gives `{"missing": ...}` and unchanged `pass`; malformed JSON gives `{"missing": ...}`, exit 0, no traceback; mismatched `repo` gives `{"missing": ...}`; unreadable state gives `{"missing": ...}` alongside the existing failed conditions; scoring two states, one with and one without, gives each its own value; existing `compare` test unchanged (FR-010). Run; fails (no key).
  - Implement: lookup at `Path(state["repo"]).parent / "provenance.json"` (research R6), no ancestor walk; never raises; `pass`, `metrics`, `conditions` untouched.
  - Pass: runner green, all pre-existing `ScoreTests` green.
  - Done: all cases above pass.

## Phase 6: User Story 5 - Golden-run procedure and results (P2)

**Goal**: a maintainer can run every leg from the checklists. **Independent test**: read the documents; each leg has steps and one results row; no capability placeholder remains.

- [ ] T007 [P] [US5] Fill `conformance/golden-run/claude-code.md`: invoke (`python3 tools/bench.py run --harness claude-code --from-checkout [--model <m>] --out <dir>`), isolation (`<out>/harness-config`, one-time `claude` login or `ANTHROPIC_API_KEY` there; driver never copies credentials), scoped permissions (exact `--add-dir`/`--allowedTools`), pause/kill/resume steps, installed baseline run (no `--from-checkout`) as a separate result, PR leg against private `tenluap/factory-golden-run-<date>` created at trial time and kept as evidence; replace every `<fill ...>` capability note. Exempt: `conformance/golden-run/claude-code.md` - documentation only (FR-011). Done: FR-011 items present; `grep -n "<fill" conformance/golden-run/claude-code.md` empty.

- [ ] T008 [P] [US5] Fill `conformance/golden-run/opencode.md`: same items as T007 for `opencode run` (`XDG_CONFIG_HOME` isolation; provider auth stays in OpenCode's data directory), how to pick a known-compatible model (`opencode models`, then `--model <provider/model>`; the default-model rejection as the reason), Codex fallback for the cross-harness leg via `conformance/golden-run/codex.md` with the reason recorded. Exempt: `conformance/golden-run/opencode.md` - documentation only (FR-012). Done: FR-012 items present; no `<fill` left.

- [ ] T009 [US5] Add a per-leg table to `conformance/golden-run-results.md`: rows headless smoke, golden run, pause/resume, cross-harness resume, approval/PR, UI (deferred until `docs/superpowers/plans/2026-11-03-factory-ui-handoffs-plan.md` lands); columns leg, harness(es), mode (checkout or installed baseline), run date, provenance path, result, evidence, notes; state that each leg's evidence is recorded separately and the installed-version baseline is a separate result; link T007, T008 checklists. Exempt: `conformance/golden-run-results.md` - documentation only (FR-013, FR-014). Done: exactly six leg rows (SC-006).

## Phase 7: Polish

- [ ] T010 Final verification (no file change, no commit unit): run the build command (`for h in claude-code opencode codex copilot zcode; do python3 tools/render.py "$h"; done && bash -n install.sh`), `python3 -m unittest discover -s tools`, and `test -z "$(git ls-files -- dist/)"`. Done: all three succeed (SC-005); record results in the run log.

## Dependencies

- T001 first (constitution I).
- T002 → T003 (launch env and skill directory) → T005 (checkout render digest).
- T004 → T005 (`checkout_provenance`, `tree_digest`) → T006 (record shape).
- T007, T008, T009 depend on T002-T006 (procedure describes final options); T007 ∥ T008; T009 after both (links).
- T010 last.

## Parallel opportunities

- T004 can run beside T002/T003 in effort, but all edit `tools/bench.py` and `tools/tests/test_bench.py`, so commit serially in ID order.
- T007 and T008 touch different files: parallel.

## Implementation strategy

MVP: T001-T003 (US1-US3) unblock the headless smoke leg. Then T004-T006 add attribution (US4), then T007-T009 the procedure (US5), then T010.
