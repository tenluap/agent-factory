# Implementation Plan: Restore installer CI coverage

**Branch**: `009-fix-install-ci` | **Date**: 2026-10-27 | **Spec**: [spec.md](spec.md)

## Summary

Correct only the two existing OpenCode subprocess test fixtures in `tools/tests/test_install.py`: create their explicitly configured factory home before running the installer. Preserve the success, conflict, and user-file preservation assertions. Derive the complete expected role filenames from source roles rather than ignored checkout distribution output, and explicitly require a nonempty expected set. Installer policy and production files remain unchanged.

## Technical Context

- Language/version: repository Python 3 and Bash; standard-library unittest, pathlib, tempfile, subprocess.
- Dependencies: existing Python and Bash only; no additions.
- Storage: disposable temporary directories owned by each test; no persistent data.
- Testing: existing `python3 -m unittest discover -s tools` runner.
- Platforms: Linux CI and local macOS.
- Project type: installer CLI and its integration tests.
- Performance: no new targets; bounded existing installer runs, no benchmarks needed.
- Scope: two existing test methods in one module; no new fixtures, helpers, APIs, or product behavior.

## Constitution Check

Before and after design: pass. No factory behavior changes require DESIGN.md updates; no core or adapter edits are planned. Never edit generated dist files. Render every supported harness and run the prescribed porcelain check. The constitution's committed-dist wording predates ignored generated dist; this change does not amend that policy or claim porcelain proves ignored file content equality. Stateless handoff uses these artifacts and factory state. The minimal fixture edits follow simplicity and reuse.

## Project Structure

```text
tools/tests/test_install.py          # sole implementation target
specs/009-fix-install-ci/
  spec.md
  plan.md
  research.md
  data-model.md
  quickstart.md
  contracts/installer-tests.md
  tasks.md                          # next stage
```

Retain the existing test classes and subprocess boundary. For each affected method, create `Path(home) / ".factory"` before supplying it as FACTORY_HOME. In the success test, expected names come from `core/roles/*.md` using OpenCode's existing `factory-{role}.md` convention, with an explicit nonempty check. Keep equality against installed `factory-*` names, every-link symlink checks, skill-link verification, and session guidance. Do not discover expectations from the same installed directory being checked.

## Test seams

- `install.sh subprocess in disposable HOME/XDG_CONFIG_HOME/FACTORY_HOME`: existing success and conflicting-skill tests exercise this seam. Existing home-policy tests cover missing explicitly configured homes. Reuse these tests; no new seam, runner, or speculative tests.
- Exempt: feature planning documents - documentation only.
- Overridden: none.

Confirmed: 2026-10-27 - Q1 accepted - seams: install.sh subprocess in disposable HOME/XDG_CONFIG_HOME/FACTORY_HOME

## Verification and delivery

1. Before editing, retain the existing red proof: `python3 -m unittest discover -s tools -p test_install.py` reports 13 tests with the two named tests failing on missing FACTORY_HOME. Re-run this command if fresh proof is needed.
2. Apply the small fixture/assertion correction and run that same focused command. Both named tests must reach their intended success/conflict paths; existing home-policy tests must remain green.
3. Run `python3 -m unittest discover -s tools`.
4. Render `claude-code`, `opencode`, `codex`, `copilot`, and `zcode` with `python3 tools/render.py <harness>`.
5. Run `bash -n install.sh` and `test -z "$(git status --porcelain -- dist/)"`.

Disposable environments and unchanged installer policy preserve filesystem isolation, conflict data integrity, diagnostics, and compatibility. Existing temporary-directory cleanup owns resources. No new security, network, concurrency, instrumentation, migration, or deployment mechanisms apply. Rollback is reverting the focused test change. Commit test correction and red proof together under factory engineering rules.

## New items and reasons

- `specs/009-fix-install-ci/plan.md` - file - records the bounded implementation and verification plan.
- `specs/009-fix-install-ci/research.md` - file - records the existing policy, failing fixtures, and clean-checkout assertion decision.
- `specs/009-fix-install-ci/data-model.md` - file - documents temporary fixture ownership and absence of production model changes.
- `specs/009-fix-install-ci/quickstart.md` - file - provides repeatable focused and repository validation commands.
- `specs/009-fix-install-ci/contracts/installer-tests.md` - file - records the existing installer outcomes the corrected tests must retain.
- New abstractions: none.
- New dependencies: none.

## Complexity Tracking

No constitution violations or additional complexity.
