# Tasks: Stabilise and optimise the factory

**Input**: `/specs/007-stabilise-factory/` — plan.md (required), spec.md, research.md, data-model.md, contracts/cli.md, quickstart.md

**Tests**: mandatory — every implementation task is immediately preceded by a failing-test task naming the plan.md "Test seams" seam it targets; a plan-exempt task carries `Exempt: <part> - <reason>` instead; no other seam.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: parallelizable with the tasks beside it
- **[Story]**: spec.md user story (US1–US6); phases are the milestones M1 → M2 → M3 → M4 → P2 (`factory/brief.md` §5)
- Every task names its file paths; code tasks name their seam

**Run tests**: `python3 -m unittest discover -s tools`.

**Build gate** (Constitution III): a task changing `core/` or `adapters/` ends with `for h in claude-code opencode codex copilot zcode; do python3 tools/render.py "$h"; done` and a clean `test -z "$(git status --porcelain -- dist/)"`; `docs/`, `specs/` and `tools/` tasks render nothing.

---

## Phase 2: M1 — Trustworthy state (S1, S2, S5, S6, S8)

**Story goal**: US1/US2 — state written only through the CLI writer, the 005/006 replay reporting their stability-brief §3 defects, totals respecting the wall clock under parallel reviews.

**Independent test**: suite green and `tools/tests/replay.py` on both fixtures reporting every §3 core defect with no false pass (SC-002).

- [X] T001 [US1] Record the M1 design decisions in `DESIGN.md` "Decisions" first: R1 writer layout (`bin/factory_cli/`), R2 schema v4 with the closed history vocabulary, R7 interval-union accounting, R8 test layout. Exempt: `DESIGN.md` decision entries - documentation only.
- [X] T002 [US1] Failing tests in `tools/tests/test_state.py` with version 1–4 and legacy-relay fixtures under `tools/tests/fixtures/` — seam: `factory_cli.state` module API — covering version 1–4 read acceptance, state copies in later worktrees, vocabulary and timestamp violations with location, atomic write, first-write upgrade, append-only `decisions` never rewritten.
- [X] T003 [US1] Implement `core/skills/factory/bin/factory_cli/__init__.py` and `core/skills/factory/bin/factory_cli/state.py` — `read_state`, `validate_state`, `write_state` (temp + `os.replace`), closed vocabularies (status, stage, timeline kind, history events per FR-003), per-stage required fields, non-decreasing timestamps, first-write upgrade to v4 (FR-001–FR-004, FR-022; seam: `factory_cli.state` module API); then the build gate.
- [X] T004 [US1] Failing tests in `tools/tests/test_commands.py` plus `tools/tests/replay.py` and `tools/tests/fixtures/defects.json` — seam: `bin/factory` CLI command surface — for `runs`, `show`, `validate` exit codes and digests, `show`'s approver veto list naming every `auto: true` answer and every `gate-override` decision of every stage before `pr` (SC-004, FR-006), and the 005/006 replay reporting every §3 core defect, nothing falsely passing (SC-002).
- [X] T005 [US1] Implement `core/skills/factory/bin/factory_cli/cli.py` and the read commands `runs`, `show`, `validate` in `core/skills/factory/bin/factory_cli/commands.py` per `contracts/cli.md` exit codes, and slim `core/skills/factory/bin/factory` to argv → `factory_cli.cli.main` (FR-003, FR-011; seam: `bin/factory` CLI command surface); then the build gate.
- [X] T006 [US2] Failing tests in `tools/tests/test_commands.py` for every mutating command — seam: `bin/factory` CLI command surface — `checkpoint`, `ledger-add`, `wait-open`, `wait-close`, `answer`, `set-status`, `decisions-add`: each stamping its time, validating before write, writing atomically and committing; `set-status` `aborted|pr-open` appending its history entry and `ended_at` (SC-001).
- [X] T007 [US2] Implement the writer commands in `core/skills/factory/bin/factory_cli/commands.py` (FR-001), with `checkpoint <stage>` appending the `complete` history entry, setting the next stage, and moving the stage's settled relay answers into `decisions` before clearing `relay` (FR-008; seam: `bin/factory` CLI command surface); then the build gate. Lock refusal: T015; declared-file staging: T026; gate history events: T017.
- [X] T008 [US2] Failing tests in `tools/tests/test_totals.py` — seam: `factory_cli.totals` interval unions — overlapping spawns, overlapping waits, zero-length and missing intervals, human + agent never exceeding wall clock, no report summing parallel durations (SC-003).
- [X] T009 [US2] Implement `core/skills/factory/bin/factory_cli/totals.py` interval-union accounting and wire `ledger-add` `started_at`/`ended_at` (v4 spawn interval, `duration_ms` derived) and `show`'s `totals_sentence` (FR-009; seam: `factory_cli.totals` interval unions); then the build gate.
- [X] T010 [US1] Correct the contradicted sentences and document schema v4: `DESIGN.md` "State CLI" paragraph (manual-write fallback) and `core/skills/factory/references/state.md` (manual edit paths, the checkpoint's `git add -A`) now describe the single writer, its records and commands. Exempt: `DESIGN.md` corrections and `references/state.md` prose - documentation only.
- [X] T011 [US2] Correct `docs/product-brief.md` §14 rows this run settles (totals formula under parallel reviews, the auto-accept audit at approval) and `README.md`'s read-only CLI description. Exempt: `docs/` corrections and `README.md` prose - documentation only.
- [X] T012 [US1] Update `core/skills/factory/SKILL.md` to record state through the writer commands instead of editing `state.json`, naming the halt-with-message path when Python 3 is missing (FR-002). Exempt: `SKILL.md` prose - documentation only.

---

## Phase 3: M2 — Enforced gates (S3, S4, S7, S9)

**Story goal**: US3 — illegal transitions, malformed role blocks and concurrent writers refused by code, CI keeping them refused.

**Independent test**: a test per refusal (SC-005); the workflow green on the branch.

- [X] T013 [US3] Record the M2 design decisions in `DESIGN.md` "Decisions": R4 lock lifecycle and takeover, R5 gate table and gate-override records, R6 role-output shapes, R14 CI gates. Exempt: `DESIGN.md` decision entries - documentation only.
- [X] T014 [US3] Failing tests in `tools/tests/test_lock.py` — seam: `factory_cli.lock` lifecycle — live-lock refusal with the owner reported, staleness only on the recorded host with the owner process gone, explicit `lock take` recording `taken_over` and `previous`, and the pending-run lock beside its pending file.
- [X] T015 [US3] Implement `core/skills/factory/bin/factory_cli/lock.py` (`lock.json` beside the state file or the pending file, recording owner PID, host, harness, time), acquire it around every write in `state.py`/`commands.py`, and add `lock take <run> [--force]` (FR-005; seam: `factory_cli.lock` lifecycle); then the build gate.
- [X] T016 [US3] Failing tests in `tools/tests/test_gates.py` — seam: `factory_cli.checks` transition rules — one refusal per illegal transition (→ `review` without a passing latest verify record, → `pr` without a recorded approval, → `implement` without analyze clean/remediated/overridden) and one pass per legal one, each naming the missing record, plus the accepting side: `decisions-add --kind approved` at `approver` satisfying the `pr` gate and each permitted transition's `approved`/`gate-override` history entry referencing its decision.
- [X] T017 [US3] Implement the gate table in `core/skills/factory/bin/factory_cli/checks.py`, wire it into `checkpoint`, add `verify --pass|--fail --commands '<json>'` writing the verify history record, and `decisions-add --kind answer|approved|gate-override` with `checkpoint` writing the `approved`/`gate-override` history event for a gate-permitted transition (FR-006, research R3/R5; seam: `factory_cli.checks` transition rules); then the build gate.
- [X] T018 [US3] Failing tests in `tools/tests/test_envelope.py` — seam: `factory_cli.checks` output-shape checker — envelope, reviewer-report and judge-verdict blocks, using the fenced examples of `core/skills/factory/references/protocol.md` and `core/skills/factory/references/findings.md` as passing fixtures and one malformed variant per shape as a refusal.
- [X] T019 [US3] Implement the role-output shape checker in `core/skills/factory/bin/factory_cli/checks.py` and `envelope check <file>` in `commands.py`/`cli.py`, exiting non-zero with the offending location (FR-007; seam: `factory_cli.checks` output-shape checker); then the build gate.
- [X] T020 [US3] Add `.github/workflows/ci.yml` running `python3 -m unittest discover -s tools`, re-rendering all five harnesses and failing on `test -z "$(git status --porcelain -- dist/)"`, and `bash -n install.sh` (FR-018). Exempt: `.github/workflows/ci.yml` - configuration only; its behaviour is checked through the render and install seams.

---

## Phase 4: M3 — Portable and safe (S10–S13)

**Story goal**: US4 — no personal models in shared adapters, guided setup, declared-file checkpoints, a moved run rebound and resumed.

**Independent test**: only `claude-code` ships models, checkpoints commit only declared files (SC-008), a rebind resumes at the recorded stage.

- [X] T021 [US4] Record the M3 design decisions in `DESIGN.md` "Decisions": R9 model policy and `${FACTORY_HOME}/config.json`, R10 preflight guidance, R11 declared-file checkpoints, R12 rebind. Exempt: `DESIGN.md` decision entries - documentation only.
- [X] T022 [US4] Failing tests in `tools/tests/test_render_models.py` — seam: `tools/render.py` render output — exactly one adapter shipping models (claude-code opus/sonnet), empty models elsewhere, `${FACTORY_HOME}/config.json` overrides reaching the rendered agents, no personal provider ID in any `adapters/*/adapter.json`, and the README statement matching `adapters/` (FR-015).
- [X] T023 [US4] Implement the model policy: `"models": {}` in `adapters/codex/adapter.json`, `adapters/copilot/adapter.json`, `adapters/opencode/adapter.json`, `adapters/zcode/adapter.json` (claude-code keeps its defaults), and `install.sh` printing the effective model per role after rendering (FR-015; seam: `tools/render.py` render output); then the build gate.
- [X] T024 [US4] Move the personal OpenCode picks (`xiaomi-token-plan-sgp/mimo-v2.6-pro` deep, `zai-coding-plan/glm-5.3-flash` standard) out of `adapters/opencode/adapter.json` into the user's `${FACTORY_HOME:-~/.factory}/config.json` under `models.opencode`. Exempt: `adapters/*/adapter.json` model fields - configuration only; the user-machine config file is outside the repository and covered by the render-seam override test.
- [X] T025 [US4] Failing tests in `tools/tests/test_commands.py` — seam: `bin/factory` CLI command surface — a checkpoint with declared and undeclared dirty files commits only the spec directory plus the declared list, reports every other dirty path uncommitted, and `--envelope` reads the list from the role output's `files` field (SC-008).
- [X] T026 [US4] Implement declared-file staging in `core/skills/factory/bin/factory_cli/commands.py` `checkpoint` (`--files <path>...`, `--envelope <file>`): stage `spec_dir` plus exactly the declared list, commit `factory: <stage> complete`, report the rest without committing (FR-017; seam: `bin/factory` CLI command surface); then the build gate.
- [X] T027 [US4] Failing tests in `tools/tests/test_commands.py` — seam: `bin/factory` CLI command surface — `rebind` validating the target is a git worktree on the recorded branch, rewriting `worktree` and `repo`, reporting the rewrite, refusing a missing worktree with exit 4 and an ambiguous run name with exit 3 (FR-012).
- [X] T028 [US4] Implement `rebind <run> --worktree <path>` in `core/skills/factory/bin/factory_cli/commands.py` (FR-012; seam: `bin/factory` CLI command surface); then the build gate.
- [X] T029 [US4] Preflight setup guidance (FR-016): `core/skills/factory/SKILL.md` step 1 names the exact `specify init --here <speckit_init>` command from the harness reference and offers to run it as for a missing `.specify/`, with any extra arguments recorded in `adapters/<h>/harness.md`. Exempt: `SKILL.md` prose and `adapters/*/harness.md` - documentation only.
- [X] T030 [US4] Correct `README.md` for this milestone's behaviour: effective model defaults per adapter, declared-file checkpoints, and that sharing `${FACTORY_HOME}` alone does not move a run (FR-012). Exempt: `README.md` prose - documentation only.

---

## Phase 5: M4 — Proven (S14, S15)

**Story goal**: US5 — recovery demonstrated by a kill-and-resume suite; read-only roles verified per adapter or the limitation disclosed.

**Independent test**: the kill-and-resume suite passes for a fixture run killed at every stage (SC-006); the static read-only check passes where enforceable.

- [X] T031 [US5] Record the M4 design decisions in `DESIGN.md` "Decisions": S14 (fixture repository, per-harness golden-run checklist, automated kill-and-resume tests, live two-harness run recorded after merge) and R13 read-only access verification. Exempt: `DESIGN.md` decision entries - documentation only.
- [X] T032 [US5] Failing tests in `tools/tests/test_recovery.py` — seam: `bin/factory` CLI command surface — a throwaway fixture run killed at each stage and resumed through the CLI: no answered question re-asked, no committed task redone, no duplicate branch, worktree or pull request (SC-006).
- [X] T033 [US5] Implement the resume behaviour the suite exposes as missing in `core/skills/factory/bin/factory_cli/commands.py` and `state.py` — a `resumed` history entry written through the writer (FR-003) and any digest gap the suite names — so the suite passes (seam: `bin/factory` CLI command surface); then the build gate.
- [X] T034 [US5] Extend `tools/tests/test_render_models.py` with the static read-only conformance check — seam: `tools/render.py` render output — every rendered `read`-access agent denying edits in that adapter's terms (tool lists without `Edit`/`Write`, OpenCode deny rules, Copilot tool list), `codex` excluded by its documented disclosure (FR-014).
- [X] T035 [US5] Implement any missing read-only permissions in `adapters/*/adapter.json` `access` blocks so the static check passes, and document the `codex` limitation in `adapters/codex/harness.md` (FR-014; seam: `tools/render.py` render output); then the build gate.
- [X] T036 [US5] Add `conformance/fixture-repo/` (files plus init instructions), `conformance/golden-run/<harness>.md` checklists (start, pause at `review`, kill, resume on a second harness, approve, PR against a throwaway remote) and a `conformance/golden-run-results.md` skeleton per adapter and capability tier, the live two-harness run recorded after merge. Exempt: `conformance/fixture-repo/`, `conformance/golden-run/` and `conformance/golden-run-results.md` - documentation and test data only.

---

## Phase 6: P2 — Hardening and context trim (S16–S19, FR-024)

**Story goal**: US6 — self-explaining installer errors, preview-first cleanup, reported usage labelled separately, Pen rules in one reference, corrected source documents.

**Independent test**: `install.sh --harness` with no value fails with a usage message (FR-020); `prune --dry-run` deletes nothing; the design rules exist in one reference.

- [X] T037 [US6] Record the P2 design decisions in `DESIGN.md` "Decisions": R12 prune preview, S17 installer argument validation, R17 reported-usage labelling, R15 Pen consolidation. Exempt: `DESIGN.md` decision entries - documentation only.
- [X] T038 [US6] Failing tests in `tools/tests/test_commands.py` — seam: `bin/factory` CLI command surface — `prune --dry-run` listing stale pending files (run has a worktree state or ended `pr-open`/`aborted`) and deleting nothing, `prune --delete` being the only deleting form, and a run whose only state is the pending file never listed (FR-019).
- [X] T039 [US6] Implement `prune [--dry-run|--delete]` in `core/skills/factory/bin/factory_cli/commands.py` (FR-019; seam: `bin/factory` CLI command surface); then the build gate.
- [X] T040 [US6] Failing tests in `tools/tests/test_install.py` — seam: `install.sh` argument validation — `--harness` with no value printing a clear usage message and exiting non-zero with no unbound-variable crash, under a throwaway `HOME` (FR-020).
- [X] T041 [US6] Implement argument validation in `install.sh`'s option loop, failing with a usage message instead of a crash (FR-020; seam: `install.sh` argument validation).
- [X] T042 [US6] Failing tests in `tools/tests/test_totals.py` — seam: `factory_cli.totals` interval unions — reported usage (`reported`) labelled separately from the word-count estimates (`in_est`/`out_est`) in `show` and the totals line, never merged into one number (FR-010).
- [X] T043 [US6] Implement the reported-vs-estimate labelling in `core/skills/factory/bin/factory_cli/totals.py` and `show`, with `ledger-add --reported` storing harness-reported usage where an adapter exposes it (FR-010, S18; seam: `factory_cli.totals` interval unions); then the build gate.
- [X] T044 [US6] Consolidate the Pen design rules into `core/skills/factory/references/design-code-mapping.md` (FR-021): move every rule sentence from `core/skills/factory/SKILL.md` steps 6, 8, 9 and the duplicated prose of `core/skills/factory/references/state.md` (keeping its schema facts) into the one reference against a checked list of accounted rules, replacing removed prose with pointers and trimming redundant prose. Exempt: `SKILL.md` and `references/` prose - documentation only.
- [X] T045 [US6] Move `Harness-agnostic factory design and plan.md` to `docs/` marked implemented and update the inbound links in `README.md`, `DESIGN.md` and `specs/`. Exempt: `docs/` moves - documentation only.
- [X] T046 [US6] FR-024 closing pass: correct every sentence still contradicted by the delivered behaviour in `DESIGN.md`, `core/skills/factory/references/state.md`, `docs/product-brief.md` §14 and `README.md`, each correction deliberate in this same change. Exempt: `README.md`, `docs/` and `references/` corrections - documentation only.

---

## Dependencies

- Milestones run in order M1 → M2 → M3 → M4 → P2; each closes green under build and test.
- Every test task immediately precedes its implementation task and fails until it lands.
- T003 precedes T004; T005 precedes T006/T007; T015's lock refusal is exercised by every later write test; T026 depends on T007; T028 on T005.
- T024 follows T023; T035 follows T034; T043 follows T009; T044–T046 close the change.

## Parallel execution examples

- M1 after T005: T006/T007 ∥ T008/T009; M3: T022/T023 ∥ T025/T026 ∥ T027/T028; P2: T038/T039 ∥ T040/T041 ∥ T042/T043.

## Implementation strategy

MVP is M1: state flows only through the CLI and the 005/006 replay proves validation catches real defects. Each milestone closes green under the build gate before the next opens. FR-024 corrections land with or before the item they describe; the context trim (T044–T046) is last, touching no code path.
