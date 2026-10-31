---
description: "Task list for Post-Run Retro for Self-Improvement"
---

# Tasks: Post-Run Retro for Self-Improvement

**Input**: `specs/016-retro-self-improve/` — plan.md, spec.md

**Tests**: Required (engineering.md, "Commit units"). Every behavior-changing task is one checkbox and one commit: failing test, then implementation, then passing check. Its commit body carries a `Red:` line in one of the two engineering.md forms. Plan-exempt tasks carry their exemption instead.

**Test command**: `python3 -m unittest discover -s tools -p 'test_*.py'`. **Build**: `python3 -m compileall -q tools core/skills/factory/bin`.

**Seams** (plan.md "Test seams", confirmed 2026-10-31, plan-Q1): S1 `factory improvements add`; S2 `factory improvements` listing; S3 `ledger-add`/`issue-add` on a `pr-open` run; S4 retro role render.

**UI**: none. No task is `[UI]`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an unfinished task)
- **[Story]**: US1, US2, US3 from spec.md

---

## Phase 1: Setup

No setup. The repository already has the `unittest` runner and `tools/tests.Sandbox`.

---

## Phase 2: Foundational (design first, then state writer)

**Purpose**: Record the design before any core change (constitution I, FR-013). Then let the retro spawn be recorded on a `pr-open` run.

- [x] T001 Add a "Post-run retro" subsection under "Time budget, issues, improvement backlog, benchmark" in `DESIGN.md`. Cover: the retro step between `set-status pr-open` and `drop`; the read-only standard-tier `retro` role and its inputs (`factory show` JSON, `state.json` path, analyze report paths, verdict paths, `covered_keys`); the five signals and default thresholds (fixer-recurring class = first cited `ENG-n`, lower-cased); the signal key grammar `<kind>:<subject>`; the `retro.candidates` envelope field; the `factory improvements add` writer (validate, dedupe, cap 3 per run, home lock, atomic write, `written`/`skipped`/`dropped` JSON); Retro entry name `<repo-name>-<branch>.retro.<kind>.<subject>.json`; the `ledger-add`/`issue-add` `pr-open` exception for stage `retro`; the ledger re-entry marker (every spawn ledgered, failed attempts included; checked only on sub-step entry); retry once, then skip without halt; manual recovery of a run interrupted between `pr-open` and the final push (`factory drop`, then `git push`). Exempt: `DESIGN.md` - documentation only. Done when the subsection exists and names every item above.
- [x] T002 [P] Add the optional `retro` envelope field to `core/skills/factory/references/protocol.md`: `"retro": { "candidates": [ { "signal_key", "rank", "evidence", "suggested_feature" } ] }`, with `files: []` and `questions: []` on a retro envelope, and `suggested_feature` as one line usable as `/factory <feature>` unchanged (SC-005). Depends on T001. Exempt: `protocol.md` - documentation only. Done when the field shape and its constraints appear in the Envelope section.
- [x] T003 [P] Update `core/skills/factory/references/state.md`: add `retro` to the stage list after `pr`; state that `ledger-add` and `issue-add` accept stage `retro` on a `pr-open` run and refuse every other write to an ended run (and every `aborted` write); add the CLI line `factory improvements add --from <file> --run <branch>`. Depends on T001. Exempt: `state.md` - documentation only. Done when all three items appear.
- [x] T004 Allow retro records on a `pr-open` run (seam S3). Files: `core/skills/factory/bin/factory_cli/state.py`, `core/skills/factory/bin/factory_cli/commands.py`, `tools/tests/test_commands.py`. Depends on T001.
  1. Failing tests in `tools/tests/test_commands.py`: `ledger-add retro retro ...` on a `pr-open` run appends a ledger entry with stage `retro`; `issue-add retry retro retro ...` on a `pr-open` run appends an issue. Failure paths: `ledger-add plan ...` on a `pr-open` run is refused (exit 1, state unchanged); `ledger-add retro ...` and `issue-add ... retro ...` on an `aborted` run are refused. Run the test command and observe red.
  2. Implement: add `retro` after `pr` in `state.STAGES`; give `resolve_target` an `allow_pr_open` flag; `cmd_ledger_add` and `cmd_issue_add` pass it only when the stage is `retro`. Every other caller keeps the current refusal.
  3. Run the test command and the build command; both pass.
  Red proof: `Red: <new S3 test name> failed as expected`. Done when the four S3 tests pass and existing ended-run refusal tests still pass.

**Checkpoint**: Design recorded; retro spawns can be ledgered on a `pr-open` run.

---

## Phase 3: User Story 1 - Every finished run leaves improvement candidates (P1) 🎯 MVP

**Goal**: After `pr-open`, the retro role runs once, and its candidates become `ready` Retro entries that `/factory improve` lists.

**Independent test**: In a sandbox, set a run to `pr-open`, write a `retro-envelope.md` with one valid candidate, run `factory improvements add`, and confirm a `ready` Retro entry appears in `factory improvements` with its stored `suggested_feature`.

- [x] T005 [US1] Add the `factory improvements add` writer (seam S1, base paths). Files: `core/skills/factory/bin/factory_cli/improvements.py`, `core/skills/factory/bin/factory_cli/commands.py`, `core/skills/factory/bin/factory_cli/cli.py`, `tools/tests/test_improvements.py`. Depends on T004.
  1. Failing tests in `tools/tests/test_improvements.py`: a `--from` file whose final fenced `json` block holds one valid candidate, for a `pr-open` run, writes `<repo-name>-<branch>.retro.<kind>.<subject>.json` with body `name`, `kind: "retro"`, `run: {repo, branch, spec_dir}`, `signal_key`, `evidence`, `suggested_feature`, `rank`, `factory_sha`, `status: "ready"`, `exported_at`, `claimed_at: null`, and prints JSON with `written`, `skipped`, `dropped`. Re-running with the same file replaces the same entry (no new file). Failure paths: run not `pr-open` refused (exit 1, nothing written); `--from` without a parseable block, or without a `retro.candidates` list, refused (exit 1); unwritable `improvements/` exits 1 naming the path and leaves no temp file. Observe red.
  2. Implement: extract `_write_atomic(path, body)` (temp file plus `os.replace`, temp removed on failure) in `improvements.py`; make `export` and `claim` use it. Add `add(home, run_state, candidates, now=None)` and `cmd_improvements_add(repo, from_path, run)`: resolve the run by `--run`, refuse unless `pr-open`, read the block with `checks.extract_block`, write entries, report `OSError` with exit 1 while reporting entries already written. Wire `improvements add --from <file> --run <branch>` usage and arguments in `cli.py`.
  3. Run the test command and the build command; existing `export`/`claim` tests still pass.
  Red proof: `Red: <new S1 test name> failed as expected`. Done when the S1 base tests pass and Run export files are byte-shape unchanged.
- [ ] T006 [US1] Serialise writers with the home-level lock (seam S1, lock path). Files: `core/skills/factory/bin/factory_cli/improvements.py`, `tools/tests/test_improvements.py`. Depends on T005.
  1. Failing test: hold `<home>/improvements.lock.json` with another holder; `improvements add` retries for at most 5 s, then exits 1 naming the holder and writes nothing. Assert the lock file is not listed by `factory improvements`. Observe red.
  2. Implement: wrap the scan and writes of `add` in `lock.acquire(<home>/improvements, ...)` with a bounded 5 s wait; release in `finally`.
  3. Run the test command; pass.
  Red proof: `Red: <lock-wait test name> failed as expected`. Done when the lock-wait test passes and the run time stays bounded.
- [ ] T007 [P] [US1] Show Retro entries in the listing (seam S2). Files: `core/skills/factory/bin/factory_cli/improvements.py`, `tools/tests/test_improvements.py`. Depends on T005.
  1. Failing tests: `factory improvements` lists a Retro entry with `kind: "retro"`, its `signal_key` and its stored `suggested_feature`; a Run export shows `kind: "run-export"`, `signal_key: null` and its generated suggested feature; `claim` works on a Retro entry. Failure path: none beyond the existing unreadable-file skip (plan S2). Observe red.
  2. Implement in `list_backlogs`: add `kind` (default `run-export`) and `signal_key` (null for exports); prefer a stored `suggested_feature`.
  3. Run the test command; pass, including existing listing tests.
  Red proof: `Red: <S2 listing test name> failed as expected`. Done when both kinds list correctly and existing listing fields are unchanged.
- [ ] T008 [P] [US1] Add the `retro` role (seam S4). Files: `core/roles/retro.md`, `tools/tests/test_render_models.py`. Depends on T001, T002.
  1. Failing test in `tools/tests/test_render_models.py`: for every harness, `tools/render.py` renders a `retro` role with tier `standard`, access `read` and no edit tools; the core role file names no harness tool. Update the expected role table if the test lists roles. Failure path: none (plan S4). Observe red.
  2. Implement `core/roles/retro.md`: frontmatter `name: retro`, `tier: standard`, `access: read`, description "Spawned by the /factory orchestrator only". Inputs: `F`, `worktree`, `spec_dir`, `branch`, `deadline`, `factory show` JSON, `state.json` path (read-only), every `analyze.reports` path, every round's `verdict.json` path, `covered_keys`. Work: mine the five signals with the plan thresholds (analyze-escalation: any input analyze report with CRITICAL or HIGH > 0; fixer-recurring: one finding class — first `ENG-n` cited in a confirmed blocking finding's `evidence`, lower-cased; no `ENG-n`, not counted — blocking in 2+ rounds or 2+ times in one round; judge-rejection: reviewer with 2+ findings and at least half `rejected`; in-est-outlier: a role's largest `in_est` at least 2x the run-wide median, 4+ ledger entries; halt-cluster: 2+ `halt`/`agent-failure`/`retry`/`overrun` issues in one stage). Use the key grammar; skip covered keys and missing sources; rank by halt-cluster, judge-rejection, fixer-recurring, analyze-escalation, in-est-outlier, ties by count; return at most 3 in `retro.candidates`. Writes nothing, asks nothing; status `done` (list may be empty) or `failed`. Role prose is exempt (plan); its packaging is covered here.
  3. Run `python3 tools/render.py` for every harness, then the test command; pass.
  Red proof: `Red: <S4 retro render test name> failed as expected`. Done when the S4 test passes for every harness and `dist/` stays untracked.
- [ ] T009 [US1] Insert the "Retro" sub-step in step 9 of `core/skills/factory/SKILL.md`, between `set-status pr-open` and `drop`: (1) `factory show <branch>`; a ledger entry with stage `retro` skips to (4); this check runs only on entry. (2) `factory improvements`; collect `signal_key` of `ready` Retro entries as `covered_keys` (the T007 listing field); `factory budget retro`; `SPAWN retro` with the T008 inputs, taking `analyze.reports` from `state.json`. (3) Save the output to `<spec_dir>/factory/retro-envelope.md`, then `ledger-add retro retro ...`. (4) When the file holds candidates, run `factory improvements add --from <file> --run <branch>`. (5) Continue with `drop`. Use only `SPAWN`, `SHELL`, `NOTIFY`. Depends on T004, T005, T007, T008. Exempt: `SKILL.md` - orchestrator prose only. Done when the sub-step is in place and harness-neutral.

**Checkpoint**: A `pr-open` run produces listed Retro entries (MVP).

---

## Phase 4: User Story 2 - Candidates stay few and non-duplicated (P2)

**Goal**: At most 3 Retro entries per run; no duplicate of a covered signal.

**Independent test**: Seed a `ready` Retro entry for key X from another run; add candidates X, Y, Z, W; confirm X is `skipped` and at most 3 entries exist for the run.

- [ ] T010 [US2] Validate candidates in `add` (seam S1, malformed path). Files: `core/skills/factory/bin/factory_cli/improvements.py`, `tools/tests/test_improvements.py`. Depends on T006.
  1. Failing tests. Failure paths: a candidate is `dropped` with a reason when its key breaks the grammar (kind outside the five, subject not `[a-z0-9][a-z0-9-]{0,63}`), its `evidence` is empty or over 2000 chars, its `suggested_feature` is empty, multi-line or over 500 chars, or its `rank` is not a positive int; valid candidates in the same batch are still written. A second candidate with the same key in one batch is `skipped`. No file name comes from unvalidated input. Observe red.
  2. Implement validation before any write.
  3. Run the test command; pass.
  Red proof: `Red: <malformed candidate test name> failed as expected`. Done when malformed and batch-duplicate tests pass.
- [ ] T011 [US2] Dedupe and cap in `add` (seam S1, covered/cap/claimed paths). Files: `core/skills/factory/bin/factory_cli/improvements.py`, `tools/tests/test_improvements.py`. Depends on T010.
  1. Failing tests. Failure paths: a key covered by another run's `ready` Retro entry is `skipped` with `covered_by`; with 2 existing own-run Retro entries and 3 new valid keys, only 1 is written and 2 are `dropped` with reason `cap` (ordered by rank); an own-run entry that is `claimed` is `skipped` with reason `claimed` and its file is unchanged; rewriting an own-run `ready` entry replaces it and does not count twice. Observe red.
  2. Implement under the lock: scan entries once; skip covered keys; order by rank; write while the run total stays at most 3; drop the rest with `cap`.
  3. Run the test command; pass.
  Red proof: `Red: <cap counting own-run test name> failed as expected`. Done when all S1 dedupe and cap tests pass (SC-002, SC-003).

**Checkpoint**: S1 failure paths fully covered.

---

## Phase 5: User Story 3 - Retro never blocks a finished run (P2)

**Goal**: A failed retro or failed write never halts the run and is named in the final notice.

**Independent test**: Follow SKILL.md with a retro that fails twice; the run still drops, pushes and notifies with the skip named.

- [ ] T012 [US3] Add retro failure handling to `core/skills/factory/SKILL.md`: in the Retro sub-step, every spawn, failed attempts included, is ledgered with `ledger-add retro retro ...` (the entry-only marker check leaves the in-turn retry unaffected); a crash, unparseable envelope or `failed` status gets `issue-add retry retro retro` and one fresh retry; a second failure gets `issue-add agent-failure retro retro`, no halt, and the skip is noted; zero candidates writes nothing; a non-zero `improvements add` exit notes the skipped write and reason. The final `NOTIFY` names any skipped retro or skipped write (FR-011, FR-012). Add the retro exception to the Policies failure-policy line. Name the manual recovery for a run interrupted between `pr-open` and the final push: `python3 <F>/bin/factory drop`, then `git push`. Depends on T009. Exempt: `SKILL.md` - orchestrator prose only. Done when each failure branch ends at `drop` and the notice text is defined.

---

## Phase 6: Polish

- [ ] T013 Run `python3 tools/render.py` for every harness, the build command and the full test command; confirm `git status` shows no `dist/` files and no `CONTEXT.md` change is needed. Depends on T001-T012. Exempt: verification only, no code change. Done when all three commands pass.

---

## Dependencies

- T001 first. T002, T003 after T001 (parallel). T004 after T001.
- US1: T005 after T004; T006 after T005; T007 and T008 parallel after T005 / T002; T009 after T004, T005, T007, T008.
- US2: T010 after T006; T011 after T010.
- US3: T012 after T009.
- T013 last.

T005, T006, T007, T010, T011 all edit `improvements.py` and `test_improvements.py`; run them in order. T007 is `[P]` only against T008.

## Parallel example

```text
After T005: T007 (listing, improvements.py) with T008 (retro role, core/roles/retro.md + test_render_models.py)
After T001: T002 (protocol.md) with T003 (state.md)
```

## Implementation strategy

MVP is Phases 2-3 (T001-T009): a `pr-open` run writes listed Retro entries. Phase 4 adds full validation, dedupe and cap. Phase 5 adds the no-block failure path. Each task is one passing commit.
