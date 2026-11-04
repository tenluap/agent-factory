# Implementation Plan: Live-conformance unblockers

**Branch**: `018-live-conformance` | **Date**: 2026-11-04 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/018-live-conformance/spec.md`

## Summary

Extend `tools/bench.py run` so a headless trial can reach factory preflight and be attributed: a scoped Claude Code permission grant (no bypass), an optional `--model` forwarded to either harness, an opt-in `--from-checkout` isolated install that reuses `install.sh`, and a `provenance.json` written before launch. `bench.py score` carries each run's provenance. Fill the Claude Code and OpenCode golden-run checklists and give the results document one row per leg. No live trials run in this feature. Design decisions: [research.md](research.md).

**Settled spec addition (orchestrator request)**: the `--add-dir` grant does cover the run's factory home. It grants the whole run output directory, which holds the fixture, the factory's sibling worktree and the default factory home, plus the factory skill directory in use and `--home` when outside the output directory (research R1). The spec's Assumptions line is updated to match.

## Technical Context

**Language/Version**: Python 3 (standard library only, as `tools/bench.py` today); Bash for `install.sh` (unchanged)

**Primary Dependencies**: none new; reuses `factory_cli` (`state`, `totals`, `checks`), `tools/render.py` (`load_adapter`) and `install.sh`

**Storage**: JSON files in the run's output directory (`provenance.json`)

**Testing**: `python3 -m unittest discover -s tools` (existing runner); new cases in `tools/tests/test_bench.py`

**Target Platform**: macOS and Linux maintainer machines

**Project Type**: CLI tooling plus Markdown procedure

**Performance Goals**: none beyond today; provenance adds a few bounded subprocess calls (10-second timeout each)

**Constraints**: offline tests only (FR-015); never a permission-bypass mode (FR-002); checkout runs leave the maintainer's factory home and harness configuration unchanged, with the rendered factory home and harness configuration under the output directory (SC-004); OpenCode's data directory (provider auth, sessions, logs) is shared by design; existing CLI usage unchanged (FR-010)

**Scale/Scope**: one module (~313 lines) extended by roughly 150 lines; three Markdown documents; one DESIGN.md paragraph

## Quality constraints and verification

- **Security**: narrowest grant (R1, R2); never `--dangerously-skip-permissions`, `--permission-mode` or a bare `Bash` entry. The driver never creates, copies or logs credentials; provenance stores no environment values. Verified by launch-command assertions over stub-recorded argv.
- **Isolated skill directory**: formatted from the adapter's raw `skill_dir` template with `home=<out>/harness-config` (read from `render.ADAPTERS`), because `render.load_adapter` reads only the process environment; the driver never mutates `os.environ` and `tools/render.py` is unchanged.
- **Isolation**: checkout mode sets `HOME=<out>` for the installer so its legacy pending migration cannot move real runs; `--from-checkout` excludes `--home`. Verified by snapshotting the sandboxed home, `CLAUDE_HOME` and `XDG_CONFIG_HOME` trees before and after a run.
- **Integrity**: provenance is written before launch; score accepts a record only when its `repo` matches the state's `repo`.
- **Errors/resources**: install failure stops before launch with the installer exit code and output tail; every provenance subprocess has a 10-second timeout and degrades to `"unavailable"`; the scorer stays exception-safe.
- **Compatibility**: new options are additive; `score` adds one key per entry; `compare` unchanged. Existing bench tests stay green.
- **Dependencies, observability, delivery**: no new dependency; `run` prints the provenance path in its existing stdout JSON; no rollout or migration.

## Constitution Check

| Principle | Status |
|---|---|
| I. Design First | Pass: the DESIGN.md "Benchmark" bullet is updated in the first task, before the `bench.py` changes. |
| II. Harness-Neutral Core | Pass: no `core/` change; harness names live in `tools/bench.py`, which already maps them. |
| III. Generated Dist | Pass: no `dist/` edits; isolated renders go under the run's output directory; the build gate still renders all five harnesses. |
| IV. Stateless Agents | Pass: no agent behaviour change. |
| V. Simplicity and Reuse | Pass: no new file in source; reuses `install.sh`, `render.load_adapter` and the existing CLI; reasons below. |

Post-design re-check: unchanged, pass.

## New files, abstractions and dependencies

- Files: none — `tools/bench.py`, `tools/tests/test_bench.py`, `DESIGN.md` and the three `conformance/` documents already exist. (Spec artifacts under `specs/018-live-conformance/` are SpecKit outputs.)
- `bench.launch_command` - abstraction - one pure builder for each harness's argv, so permission and model rules are asserted in one place.
- `bench.isolated_install` - abstraction - wraps the `install.sh` call with the isolated environment and the stop-before-launch error.
- `bench.checkout_provenance`, `bench.tree_digest`, `bench.write_provenance` - abstraction - provenance gathering; `tree_digest` is shared by the rendered and installed fingerprints.
- `bench.load_provenance` - abstraction - score-side lookup returning the record or a missing marker without raising.
- Dependencies: none.

## Test seams

Declared public seams and required injected failure paths:

1. **`bench.py run` CLI** (subprocess; Python stub `claude` and `opencode` executables first on `PATH` record argv and selected environment; sandboxed `HOME`, `CLAUDE_HOME`, `XDG_CONFIG_HOME`, `FACTORY_HOME`). Covers FR-001 to FR-008, SC-001, SC-002, SC-004. Required failure paths:
   - isolated install fails (stub `bash` first on `PATH` exits non-zero) → exit 1, message names the render failure, harness never launched;
   - harness exits non-zero → exit 1, `provenance.json` already written;
   - harness `--version` fails → version recorded `"unavailable"`, run continues;
   - installed factory absent (sandboxed adapter homes empty) → `installed_factory` recorded `"unavailable"`, run continues;
   - selected harness executable missing → existing manual-fallback error, output directory not created;
   - `--from-checkout` combined with `--home` → argparse error, exit 2, nothing created.
2. **`bench.py score` CLI** (subprocess over recorded states). Covers FR-009, FR-010, SC-003. Required failure paths:
   - no `provenance.json` beside the state's `repo` → `{"missing": ...}`, `pass` unchanged;
   - malformed `provenance.json` → `{"missing": ...}`, no traceback;
   - record whose `repo` differs from the state's `repo` → `{"missing": ...}`;
   - unreadable state → `{"missing": ...}` alongside the existing failed conditions.
3. **`bench.checkout_provenance(path)`** (imported from `tools/bench.py`; throwaway git repos via the existing `Sandbox`). Covers FR-007, FR-008 and the untracked-file edge case. Required failure paths:
   - path is not a git repository → `revision`, `changed_paths` and `diff_sha256` recorded `"unavailable"`, no exception.
4. **`bench.tree_digest(root)`** (imported from `tools/bench.py`; throwaway directory trees under the `Sandbox`). Covers the rendered and installed digests (data-model.md tree digest). Required failure paths:
   - root missing or not a directory → `"unavailable"`, never the empty-tree sha256;
   - unreadable subdirectory under root → `"unavailable"`, never silently skipped;
   - symlink cycle under root → bounded walk, no hang, `"unavailable"`.

Exempt: `conformance/golden-run/claude-code.md` - documentation only (FR-011)
Exempt: `conformance/golden-run/opencode.md` - documentation only (FR-012)
Exempt: `conformance/golden-run-results.md` - documentation only (FR-013, FR-014)
Exempt: `DESIGN.md` benchmark bullet - documentation only (constitution I)

Overridden: none

Confirmed: 2026-11-04 - Q1 accepted - seams: `bench.py run` CLI, `bench.py score` CLI, `bench.checkout_provenance(path)`; failure paths: `bench.py run` CLI -> isolated install fails, harness exits non-zero, harness `--version` fails, installed factory absent, selected harness executable missing, `--from-checkout` with `--home`; `bench.py score` CLI -> no `provenance.json`, malformed `provenance.json`, provenance repo mismatch, unreadable state; `bench.checkout_provenance(path)` -> not a git repository. Accepted scope snapshot: `specs/018-live-conformance/factory/relay/plan-Q1.md`. Review round 1 relay Q1 (requires_user, accepted explicitly by the user 2026-11-04, option A) adds seam `bench.tree_digest(root)`; failure paths: root missing or not a directory, unreadable subdirectory under root, symlink cycle under root (each `unavailable`). Accepted scope snapshot: `specs/018-live-conformance/factory/relay/review-Q1.md`.

## Project Structure

### Documentation (this feature)

```text
specs/018-live-conformance/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/bench-cli.md
├── checklists/requirements.md
└── tasks.md            (tasks stage)
```

### Source Code (repository root)

```text
DESIGN.md                              benchmark bullet: new run options, provenance
tools/bench.py                         launch_command, isolated_install, provenance, score lookup
tools/tests/test_bench.py              run/score/provenance tests with stub harnesses
conformance/golden-run/claude-code.md  invoke, isolation, credentials, permissions, pause/kill/resume, PR leg
conformance/golden-run/opencode.md     same, plus compatible-model selection and Codex fallback
conformance/golden-run-results.md      one row per leg; UI deferred; baseline recorded separately
```

**Structure Decision**: extend the existing benchmark module and its test file; procedure lives in the existing conformance documents (Q8).

## Implementation order

1. DESIGN.md benchmark bullet (exempt).
2. `--model` and scoped Claude Code launch via `launch_command` (seam 1).
3. `--from-checkout` isolated install, failure stop and `--home` exclusion (seam 1).
4. `checkout_provenance` (seam 3) and `tree_digest` (seam 4).
5. `provenance.json` written before launch, versions and installed digest (seam 1).
6. Score provenance lookup (seam 2).
7. Golden-run checklists and results rows (exempt).

## Complexity Tracking

No constitution violations.
