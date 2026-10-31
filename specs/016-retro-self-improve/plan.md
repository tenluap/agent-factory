# Implementation Plan: Post-Run Retro for Self-Improvement

**Branch**: `016-retro-self-improve` | **Date**: 2026-10-31 | **Spec**: [spec.md](spec.md)

## Summary

After `set-status pr-open` and before `drop`, the orchestrator spawns a new read-only, standard-tier `retro` role over the ended run's digest. Retro mines five improvement signals and returns at most three improvement candidates in its envelope. The orchestrator saves that output in the run folder and persists candidates only through a new deterministic writer, `factory improvements add --from <file> --run <branch>`. The writer validates, dedupes, caps, writes Retro entries atomically under one home-level lock and prints `written`/`skipped`/`dropped` JSON. `DESIGN.md` changes land first (FR-013, constitution I).

## Technical Context

**Language/Version**: Python 3 stdlib only (existing `factory_cli`); Markdown role/skill prompts.
**Primary Dependencies**: none new.
**Storage**: JSON files in `${FACTORY_HOME}/improvements/`; run `state.json` (schema v5, unchanged version).
**Testing**: `python3 -m unittest discover -s tools -p 'test_*.py'` with the existing hermetic `tools/tests.Sandbox`.
**Target Platform**: macOS/Linux, every harness adapter (claude-code, opencode, codex, copilot, zcode).
**Project Type**: CLI + agent prompt distribution.
**Performance/Scale**: a backlog of tens to hundreds of small files; one directory scan per `add`. No performance requirement beyond that.
**Constraints**: retro never halts or blocks the run (FR-011); writer is deterministic and mines nothing (FR-015); core stays harness-neutral (FR-014).

## Constitution Check

- I Design First: task 1 edits `DESIGN.md` ("Post-run retro" subsection under "Time budget, issues, improvement backlog, benchmark") before any core/adapter change. PASS.
- II Harness-Neutral Core: `core/roles/retro.md` and the SKILL.md step use only `SPAWN`, `SHELL`, `NOTIFY`. PASS.
- III Generated Dist: no `dist/` edits; render test covers the new role. PASS.
- IV Stateless Agents: retro reads only its inputs; spawn marker lives in the ledger. PASS.
- V Simplicity: one role, one CLI subcommand, reuse of `lock.py`, `checks.extract_block` and the export atomic-write pattern. PASS. Re-checked after design: PASS.

`Overridden: none`

## Settled deferred items

1. **Retro entry file name**: `<repo-name>-<branch>.retro.<kind>.<subject>.json`, derived only from source run and signal key (FR-016). The Run export stays `<repo-name>-<branch>.json`. The grammar below keeps names unique and injective.
2. **Candidates file**: the orchestrator saves the retro role's raw output to `<spec_dir>/factory/retro-envelope.md`. `ledger-add retro` commits it with the spec directory, and `drop` archives it as evidence. `improvements add --from` reads its final fenced `json` block exactly as `envelope check` does (`checks.extract_block`).
3. **Re-runs and the cap**: yes, they count. The cap is per source run across invocations: a run never holds more than 3 Retro entries. Rewriting a candidate whose own-run entry is still `ready` replaces that same file and adds nothing; an own-run entry already `claimed` is skipped (`reason: "claimed"`), never overwritten.

## Design

### Signal key grammar

`<kind>:<subject>`. `kind` is one of `analyze-escalation`, `fixer-recurring`, `judge-rejection`, `in-est-outlier`, `halt-cluster`. `subject` matches `[a-z0-9][a-z0-9-]{0,63}`. Subjects: `analyze` (analyze-escalation), finding class (fixer-recurring: the first `ENG-n` id cited in a confirmed blocking finding's `evidence`, lower-cased, e.g. `eng-17`; a finding citing no `ENG-n` has no class and is not counted), reviewer role (judge-rejection), role (in-est-outlier), stage (halt-cluster). The file name replaces `:` with `.`.

### Retro role (`core/roles/retro.md`)

Frontmatter: `name: retro`, `tier: standard`, `access: read`, description "Spawned by the /factory orchestrator only". Inputs: `F`, `worktree`, `spec_dir`, `branch`, `deadline`, the `factory show` JSON, the `state.json` path (read-only), every `analyze.reports` path (resolved against `spec_dir`), every round's `verdict.json` path, `covered_keys`. Work: mine the five signals with these defaults, skip covered keys and missing sources, rank by impact, return at most 3.

- analyze-escalation: any input analyze report whose severity counts show CRITICAL or HIGH > 0.
- fixer-recurring: one finding class (see grammar) confirmed blocking in 2+ rounds, or 2+ times in one round.
- judge-rejection: a reviewer with 2+ findings and at least half `rejected`.
- in-est-outlier: a role whose largest `in_est` is at least 2x the run-wide median (4+ ledger entries).
- halt-cluster: 2+ `halt`, `agent-failure`, `retry` or `overrun` issues sharing one stage.

Impact order: halt-cluster, judge-rejection, fixer-recurring, analyze-escalation, in-est-outlier; ties by count. Read-only: writes nothing, asks nothing (FR-009). Status `done` (possibly empty list) or `failed`.

### Envelope (protocol.md)

Optional field on the retro envelope:

```json
"retro": { "candidates": [
  { "signal_key": "judge-rejection:security-reviewer", "rank": 1,
    "evidence": "round-1 and round-2 verdicts rejected 4 of 5 findings",
    "suggested_feature": "Tighten security-reviewer ..." } ] }
```

`files: []`, `questions: []`. `suggested_feature` is one line, usable as `/factory <feature>` unchanged (SC-005).

### Writer (`factory_cli/improvements.py` `add`, CLI `improvements add`)

1. Resolve the run by `--run` in the repo; refuse (exit 1) unless status `pr-open`. Read `--from`; no parseable block or no `retro.candidates` list: exit 1.
2. Validate each candidate: key grammar; `evidence` non-empty string at most 2000 chars; `suggested_feature` non-empty single-line string at most 500 chars; `rank` positive int. Invalid: `dropped` with reason; batch duplicates: `skipped`.
3. Acquire `lock.acquire(<home>/improvements, ...)` (lock file `<home>/improvements.lock.json`, outside the listing glob). Retry for at most 5 s, then exit 1 naming the holder. Release in `finally`.
4. Under the lock, scan entries once. A key covered by another run's `ready` Retro entry is `skipped` with `covered_by`. Order the remaining candidates by rank. Write while the run's total stays at most 3; the rest are `dropped` with reason `cap`.
5. Write each entry with a shared `_write_atomic(path, body)` (temp + `os.replace`, temp removed on failure). `export` and `claim` reuse it. An `OSError` exits 1 with the path; already-written entries stay valid and are reported.

Entry body: `name`, `kind: "retro"`, `run: {repo, branch, spec_dir}`, `signal_key`, `evidence`, `suggested_feature`, `rank`, `factory_sha`, `status: "ready"`, `exported_at`, `claimed_at: null`. The listing adds `kind` (`run-export` when absent) and `signal_key` (null for exports), and shows the stored `suggested_feature` for Retro entries (FR-017). `claim` works unchanged on both kinds.

### State writer

- `state.STAGES` gains `retro` after `pr`, so `ledger-add` and `issue-add` accept it.
- `resolve_target` gains `allow_pr_open`; `ledger-add` and `issue-add` pass it only when stage is `retro`. Every other write to an ended run stays refused; `aborted` stays refused.

### SKILL.md step 9 placement

Between sub-step 4 (`set-status pr-open`) and the old sub-step 5 (`drop`), insert "Retro":

1. `factory show <branch>`; a ledger entry with stage `retro` exists: skip to 4 (re-entry marker, FR-010). This check runs only here, on entry, so the retry in 3 is unaffected.
2. `factory improvements`; collect `signal_key` of `ready` Retro entries as `covered_keys`. `factory budget retro`. `SPAWN retro` with the inputs above (`analyze.reports` read from the `state.json` path).
3. Save its output to `<spec_dir>/factory/retro-envelope.md`, then `ledger-add retro retro ...`. Every spawn is ledgered, failed attempts included, so their cost is kept. Failure (crash, no parseable envelope, `failed`): `issue-add retry retro retro`, one fresh retry (ledgered too); second failure: `issue-add agent-failure retro retro`, no halt, note the skip.
4. When `retro-envelope.md` holds candidates: `factory improvements add --from <file> --run <branch>`. Non-zero exit: note the skipped write and reason.
5. Continue with `drop`. The final `NOTIFY` names any skipped retro or skipped write (FR-012).

`resume` still refuses ended runs, so the marker guards re-entry of step 9 within the orchestrator's turn; widening resume is out of scope. An interruption between `set-status pr-open` and the final push leaves a `pr-open` run unarchived; recovery is manual: `python3 <F>/bin/factory drop` from the worktree, then `git push`. DESIGN.md (T001) and SKILL.md (T012) name it. The Policies failure-policy line names the retro exception.

## Project Structure

```text
DESIGN.md                                      # retro subsection (first)
CONTEXT.md                                     # terms already added; no change
core/roles/retro.md                            # new role
core/skills/factory/SKILL.md                   # step 9 + failure-policy note
core/skills/factory/references/protocol.md     # retro envelope field
core/skills/factory/references/state.md        # retro stage, pr-open ledger rule, CLI line
core/skills/factory/bin/factory_cli/improvements.py  # add, listing kind, _write_atomic
core/skills/factory/bin/factory_cli/commands.py      # cmd_improvements_add, allow_pr_open
core/skills/factory/bin/factory_cli/cli.py           # improvements add usage/args
core/skills/factory/bin/factory_cli/state.py         # STAGES += retro
tools/tests/test_improvements.py, test_commands.py, test_render_models.py
```

New items:

- `core/roles/retro.md` - file - FR-001 needs a dedicated read-only role; no existing role mines run history.
- `improvements.add` / `cmd_improvements_add` - abstraction - FR-015 deterministic single writer; extends the existing backlog module.
- `_write_atomic` - abstraction - removes the existing duplicate temp+replace code in `export`/`claim` and serves `add` (ENG-6).
- dependency - none.

## Quality constraints

- Security/integrity: `--from` content is untrusted; strict validation, length bounds, filenames only from the validated grammar, so no path escape. Home-level lock gives single-writer consistency between concurrent runs; atomic replace prevents torn files.
- Failure/resources: bounded 5 s lock wait; one directory scan; retro failure never halts.
- Observability: writer JSON result; ledger and issue records for retro spawns; final notice.
- Compatibility: Run exports byte-shape unchanged; state version stays 5; existing listing fields kept.
- Delivery: render every harness; `dist/` stays untracked.

## Test seams

- **S1 `factory improvements add` (CLI)** - required failure paths: malformed candidate dropped; key covered by another run's `ready` entry skipped; over-cap candidates dropped including existing own-run entries; claimed own-run entry not overwritten; run not `pr-open` refused; `--from` without a parseable block refused; lock held past the wait refused; unwritable `improvements/` exits 1 with no temp debris.
- **S2 `factory improvements` (listing)** - required failure paths: none beyond the existing unreadable-file skip (kind, signal_key, stored suggested_feature asserted).
- **S3 `factory ledger-add` / `issue-add` on a `pr-open` run** - required failure paths: non-`retro` stage on a `pr-open` run refused; `retro` on an `aborted` run refused.
- **S4 retro role render (`tools/render.py`)** - required failure paths: none (asserts tier `standard`, access `read`, no edit tools for every harness, core role names no harness tool).

Exempt: `DESIGN.md`, `CONTEXT.md`, `SKILL.md`, `protocol.md`, `state.md` - documentation/orchestrator prose only.
Exempt: `core/roles/retro.md` prose (signal mining instructions) - role prompt documentation; its rendered packaging is covered by S4.

Test runner: existing `unittest` suite; no new runner.

Confirmed: 2026-10-31 - plan-Q1 accepted - seams: S1 improvements add (failure paths: malformed candidate dropped; covered-by-other-run skipped; over-cap dropped counting own-run entries; claimed own-run not overwritten; non-pr-open refused; unparseable --from refused; lock-wait refused; unwritable dir exit 1 no debris); S2 none; S3 ledger-add/issue-add pr-open (non-retro refused; retro on aborted refused); S4 render none

## Complexity Tracking

None.
