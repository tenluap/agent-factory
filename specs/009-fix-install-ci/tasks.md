# Tasks: Restore installer CI coverage

**Input**: `specs/009-fix-install-ci/spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/installer-tests.md`, and `quickstart.md`.

**Scope**: Fix the two existing OpenCode installer checks in `tools/tests/test_install.py`; preserve `install.sh` behavior. Reuse existing failing tests rather than introduce new tests or abstractions.

**Seam for all implementation tasks**: `install.sh subprocess in disposable HOME/XDG_CONFIG_HOME/FACTORY_HOME` (confirmed in plan.md).

## Phase 1: Setup

No setup tasks: Python unittest, Bash, and the existing disposable subprocess fixtures are already available. No new runner, dependency, or project structure is needed.

## Phase 2: Foundational prerequisites

No foundational changes. Read the existing methods and accepted plan before the sequential story tasks below. Feature planning documents are exempt from test tasks: documentation only.

## Phase 3: User Story 1 — Reliable installation checks (P1, MVP)

**Goal**: Let existing success and conflict checks reach their intended installer paths under the existing explicit-home policy.

**Independent test**: `python3 -m unittest discover -s tools -p test_install.py` must pass, including existing missing-explicit-home rejection coverage.

- [x] T001 [US1] Observe the existing red `InstallArgValidationTests.test_opencode_install_verifies_skill_and_agents` in `tools/tests/test_install.py` through the confirmed `install.sh subprocess in disposable HOME/XDG_CONFIG_HOME/FACTORY_HOME` seam: run `python3 -m unittest discover -s tools -p test_install.py -k test_opencode_install_verifies_skill_and_agents` and retain the missing-FACTORY_HOME failure before T002. Do not write a duplicate test.
- [x] T002 [US1] Correct `test_opencode_install_verifies_skill_and_agents` in `tools/tests/test_install.py` at the confirmed `install.sh subprocess in disposable HOME/XDG_CONFIG_HOME/FACTORY_HOME` seam: create its temporary `.factory` directory before invocation; derive expected `factory-{role}.md` names from `core/roles/*.md`, explicitly assert a nonempty expected set, and retain installed-name equality, every-agent symlink checks, skill symlink, and fresh-session guidance. Run that method green. Commit this correction with T001 red proof.
- [x] T003 [US1] Observe the existing red `InstallArgValidationTests.test_opencode_install_fails_clearly_on_conflicting_skill_path` in `tools/tests/test_install.py` through the confirmed `install.sh subprocess in disposable HOME/XDG_CONFIG_HOME/FACTORY_HOME` seam: run `python3 -m unittest discover -s tools -p test_install.py -k test_opencode_install_fails_clearly_on_conflicting_skill_path` and retain the missing-FACTORY_HOME failure before T004. Do not write a duplicate test.
- [x] T004 [US1] Correct `test_opencode_install_fails_clearly_on_conflicting_skill_path` in `tools/tests/test_install.py` at the confirmed `install.sh subprocess in disposable HOME/XDG_CONFIG_HOME/FACTORY_HOME` seam: create its temporary `.factory` directory before invocation; retain nonzero status, the conflict-resolution diagnostic, and exact unchanged `user file` contents. Run that method green. Commit this correction with T003 red proof.
- [x] T005 [US1] Run `python3 -m unittest discover -s tools -p test_install.py` against `tools/tests/test_install.py`; verify both repaired outcomes and unchanged `InstallHomePolicyTests.test_missing_explicit_factory_home_fails_naming_the_path` coverage pass. No production changes or additional tests.

**Checkpoint**: Both repaired checks pass and the existing policy remains enforced. FR-001/FR-002 map to T001–T002; FR-003 maps to T003–T004; FR-004 maps to T002/T004 constraints and T005.

## Phase 4: Repository verification

- [x] T006 Run the full suite with `python3 -m unittest discover -s tools` from the worktree; require zero failures across `tools/tests/` (FR-005).
- [x] T007 Render all supported adapters using `for h in claude-code opencode codex copilot zcode; do python3 tools/render.py "$h" || exit; done`, then require `bash -n install.sh` and `test -z "$(git status --porcelain -- dist/)"` to pass (FR-005). Never hand-edit `dist/`; porcelain does not inspect ignored contents, so retain successful render and existing render-test evidence.

## Dependencies and execution order

`T001 → T002 → T003 → T004 → T005 → T006 → T007`.

There is one story, so its complete implementation is the MVP. Setup and foundation introduce no work. Red tasks immediately precede each implementation task and target the same confirmed seam. Each fixture remains isolated inside its existing TemporaryDirectory; no production-policy relaxation is permitted.

## Parallel example: User Story 1

No parallel implementation tasks: both corrections own `tools/tests/test_install.py`, and observing each red result must precede its correction. Run the seven tasks in order; no `[P]` labels are appropriate.

## Implementation strategy

Reuse the two existing failures as red proof, apply one fixture correction at a time, and verify each green before proceeding. Use the engineering commit-body form `Red: <test name> failed as expected` with the exact test name observed. Run the focused suite, then full tests, all five renders, syntax, and distribution checks. Rollback is reverting the focused test changes. No new files, abstractions, or dependencies are introduced by implementation.
