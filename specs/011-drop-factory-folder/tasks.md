---

description: "Task list for 011-drop-factory-folder"
---

# Tasks: Drop the factory folder at run end

**Input**: Design documents from `specs/011-drop-factory-folder/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli.md, quickstart.md

**Tests**: Required. Every implementation task is preceded by a failing-test task naming the seam it targets (plan "Test seams": seam 1 `factory drop`). Plan-exempt tasks carry their exemption instead.

**Organization**: Grouped by user story. Test runner exists: `python3 -m unittest discover -s tools`; no runner-setup task.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1, US2, US3 from spec.md

---

## Phase 1: Setup

No setup: the runner, `Sandbox` helper (`tools/tests/`) and the `factory_cli` package exist.

---

## Phase 2: Foundational (Design First)

**Purpose**: Constitution I: DESIGN.md records the behaviour before the core change.

- [ ] T001 Update `DESIGN.md`: in the "PR" section, record step 9 order (push, `gh pr create`, `factory set-status pr-open --pr-url <url>`, `factory drop`, push) and the drop commit `factory: drop run artifacts`; add `factory drop` to the state CLI write surface; in the "Factory home" bullet add `archive/<repo-name>-<branch>/` beside `pending/` and `improvements/`. Exempt: `DESIGN.md` - documentation only.
- [ ] T002 [P] Add the terms "Run folder", "Run archive" and "Drop commit" (definitions from spec.md "Key Entities") to `CONTEXT.md`. Exempt: `CONTEXT.md` - documentation only.

**Checkpoint**: design recorded; core work can start.

---

## Phase 3: User Story 1 - PR diff carries no run artifacts (P1) 🎯 MVP

**Goal**: `factory drop` on a `pr-open` run removes `specs/<branch>/factory/` in one commit and prints JSON.

**Independent Test**: In a `Sandbox` worktree run at `pr-open`, `bin/factory drop` exits 0; HEAD is `factory: drop run artifacts`; `git show --name-status HEAD` lists only deletions under `<spec_dir>/factory/`; no `<spec_dir>/factory` path in `git ls-tree -r HEAD`; stdout JSON has `dropped`, `archive`, `commit`, `dropped_at`.

- [ ] T003 [US1] Failing test, seam `factory drop` (process via `Sandbox.cli`), in new `tools/tests/test_drop.py`: build a worktree run with status `pr-open` and a committed run folder (`state.json`, `brief.md`, one nested file); run `drop` with `FACTORY_HOME` set to a temp dir; assert exit 0, HEAD message exactly `factory: drop run artifacts`, the commit deletes only paths under `<spec_dir>/factory/` (FR-006), the folder is absent from HEAD and from disk, no push happened (no remote ref change, FR-008), and stdout JSON keys `dropped` = `<spec_dir>/factory`, `archive`, `commit` (short sha of HEAD), `dropped_at` (FR-007). Run it and confirm it fails (unknown command).
- [ ] T004 [US1] Implement `cmd_drop(repo, cwd)` in `core/skills/factory/bin/factory_cli/commands.py` per plan "Design" steps 1, 3, 6, 7: find the run with `deduped(find_runs(repo))` matching the worktree realpath to `cwd` (none → `die(1, "no run to drop from <cwd>")`); status not `pr-open` → `die(1, "run is <status>; drop needs pr-open")`; target `factory_home()/"archive"/<backlog_name(repo, branch) without .json>`; `shutil.copytree(folder, target, ignore=ignore_patterns("lock.json"))`; `git rm -r -q -- <spec_dir>/factory`; `git commit -q -m "factory: drop run artifacts" -- <spec_dir>/factory`; `rmtree` untracked leftovers; return the JSON dict. Add `elif command == "drop"` (no positionals, `--repo` accepted; extra args → usage exit 5) and one USAGE line under "write" in `core/skills/factory/bin/factory_cli/cli.py` (USAGE text exempt: documentation string). T003 passes.

**Checkpoint**: MVP: PR branch tip carries no run folder.

---

## Phase 4: User Story 2 - Nothing is lost (P1)

**Goal**: archive is a verified, byte-identical copy that appears atomically before git changes.

**Independent Test**: after `drop`, `filecmp` deep comparison of `${FACTORY_HOME}/archive/<repo-name>-<branch>/` with the folder at `HEAD~1` shows no difference (except `lock.json`, never copied); an injected copy or verify failure leaves git, folder and `archive/` unchanged with no `.*.tmp` debris.

- [ ] T005 [US2] Failing tests, seam `factory drop` (process via `Sandbox.cli` and in-process `factory_cli.commands.cmd_drop`), in `tools/tests/test_drop.py`: (a) archive at `<FACTORY_HOME>/archive/<repo-name>-<branch>/` (name equals `improvements.backlog_name(repo, branch)` without `.json`, FR-003) holds every file of the pre-drop folder with identical bytes, including an untracked file, and no `lock.json` (data-model "Run archive"); (b) in-process with `shutil.copytree` patched to raise `OSError` mid-copy: `CLIError` exit 1, HEAD unchanged, folder still tracked and on disk, `archive/` contains no entry and no `.<name>.<pid>.tmp`; (c) in-process with the verification forced to report a differing file: exit 1, message names the file, same unchanged checks (FR-005, SC-003); (d) in-process with `git commit` failing: exit 1, folder restored in index and on disk, archive removed. Confirm (b)-(d) fail.
- [ ] T006 [US2] In `cmd_drop` in `core/skills/factory/bin/factory_cli/commands.py`, implement plan "Design" steps 4-6 safety: copy to `tmp = target.with_name(f".{target.name}.{os.getpid()}.tmp")`; verify recursively with `filecmp.dircmp` (no left/right-only, no `diff_files`) plus `filecmp.cmp(shallow=False)` per file; on failure `rmtree(tmp)` and `die(1, "archive copy failed: <files>")`; `os.rename(tmp, target)` only after verification; on git rm/commit failure run `git reset -q -- <folder>`, `git checkout -q -- <folder>`, `rmtree(target)`, `die(1, <git error>)`. T005 and T003 pass.

**Checkpoint**: US1 + US2 deliver the full happy path safely.

---

## Phase 5: User Story 3 - Safe refusals (P2)

**Goal**: wrong time, twice, collision or live lock refuse with a clear reason and change nothing.

**Independent Test**: each refusal exits 1, stderr names the reason, and HEAD, working tree and `archive/` are unchanged.

- [ ] T007 [US3] Failing tests, seam `factory drop` (process via `Sandbox.cli`), in `tools/tests/test_drop.py`: for each status `running`, `waiting_user`, `paused`, `halted`, `aborted` → exit 1, stderr names the status (FR-002, FR-012); existing archive target → exit 1, stderr names the path, existing archive bytes untouched (FR-004); live lock held by another pid → exit 1 naming the owner (FR-001); second `drop` after a successful one → exit 1 "no run to drop" (US3 scenario 4); for every case assert HEAD, `git status --porcelain` and `archive/` listing unchanged (SC-003). Confirm collision and lock cases fail.
- [ ] T008 [US3] In `cmd_drop` in `core/skills/factory/bin/factory_cli/commands.py`: take `lock.acquire(path, harness)` before the collision check and copy (`LockHeld` → `die(1, …)` naming the owner); check `target.exists()` → `die(1, "archive <target> already exists; refusing to overwrite")` before any copy; `lock.release` after `os.rename` and before `git rm`, and on every refusal path after acquisition. T007, T005, T003 pass.

**Checkpoint**: all stories pass `python3 -m unittest discover -s tools`.

---

## Phase 6: Polish & Cross-Cutting

- [ ] T009 [P] Update step 9 in `core/skills/factory/SKILL.md` to: push, `gh pr create`, `SHELL: python3 <F>/bin/factory set-status pr-open --pr-url <url>`, `SHELL: python3 <F>/bin/factory drop`, push; note resume of `pr` after a failed final push repeats only the push (FR-009). No harness names (constitution II). Exempt: `core/skills/factory/SKILL.md` - agent instructions only.
- [ ] T010 [P] Document `${FACTORY_HOME:-~/.factory}/archive/<repo-name>-<branch>/` under "Location" and `factory drop` (contract `contracts/cli.md`: output keys, refusals, never pushes) under "CLI" in `core/skills/factory/references/state.md` (FR-014). Exempt: `core/skills/factory/references/state.md` - documentation only.
- [ ] T011 [P] Describe the end-of-run drop and the archive location in `README.md` (FR-014). Exempt: `README.md` - documentation only.
- [ ] T012 Re-render `dist/` for all five harnesses: `export FACTORY_HOME="$(mktemp -d)"; for h in claude-code opencode codex copilot zcode; do python3 tools/render.py "$h"; done`; commit `dist/**` with the source change (FR-015). Exempt: `dist/**` - generated output, checked by the build gate.
- [ ] T013 Run the gates from `quickstart.md`: `python3 -m unittest discover -s tools` and the build command with `git diff --exit-code -- dist/` (SC-005). Exempt: verification only, no code change.

---

## Dependencies & Execution Order

- Phase 2 (T001, T002) before any core change (constitution I).
- US1 (T003 → T004) first; US2 (T005 → T006) builds on `cmd_drop`; US3 (T007 → T008) builds on the US2 copy path.
- All test tasks share `tools/tests/test_drop.py` and all implementation tasks share `commands.py`: no [P] inside stories.
- Polish: T009-T011 parallel after T008; T012 after T009-T011 (render picks up SKILL.md and references); T013 last.

## Parallel Example

```text
T009 core/skills/factory/SKILL.md
T010 core/skills/factory/references/state.md
T011 README.md
```

## Implementation Strategy

MVP = Phase 2 + US1 (T001-T004). Do not ship US1 without US2: the drop must never run without a verified archive (spec US2 priority note). Then US3, then polish and gates. Commit each test/implementation pair once (ENG-3) with its `Red:` line (ENG-2).
