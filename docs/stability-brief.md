# Agent Factory — product brief and stability plan

**Prepared:** 25 October 2026
**Baseline:** commit `3bed157` (main)
**Companion to:** [product-brief.md](product-brief.md) (the full rebuild blueprint, baseline `3162747`). This document is shorter: it states what the product is today, and lists what must change before it can be called stable. It changes no behaviour; each item below needs its own design decision in `DESIGN.md` before implementation.

## 1. Product in brief

Agent Factory turns one feature request in one repository into a reviewed pull request. A single orchestrator skill (`/factory`, `$factory` on Codex) runs the feature through grilling, an isolated git worktree, the SpecKit chain, implementation, parallel reviews, a judge verdict, bounded fix rounds, human approval and PR creation. Every stage is checkpoint-committed, so a run resumes from disk in any later session or on another harness.

| Aspect | Today |
|---|---|
| Users | Developers comfortable with git, a coding-agent harness and PRs. |
| Harnesses | Claude Code, OpenCode V2, Codex, GitHub Copilot, ZCode — one `adapters/<name>/` folder each. |
| Core | `core/skills/factory/SKILL.md` (162 lines), 8 references, 9 roles. About 2,000 lines total, mostly instructions. |
| Code | `tools/render.py` (renderer), `install.sh` (symlinks), `bin/factory` (read-only `runs` / `show` CLI). Stdlib Python only. |
| Defaults | Lite chain, fast mode on. `--full`, `--no-fast`, `--stop-at <stage>` override. |
| Review | Security, code standards, spec conformance always; UI and UX on a UI diff; a judge deduplicates and verifies; at most 2 automatic fix rounds. |
| Human gates | Initial grilling, protected relay questions, halts, final approval. Approval never merges or deploys. |
| Tests | 6 unit tests, all on the renderer. No CI. |

**Product promise:** describe the change, settle the important decisions, and receive a reviewable implementation with evidence of what was built, checked, assumed and left unresolved.

### What works

- Two real runs reached a PR end to end: `005-skill-routing` (PR #1, Claude Code, one fix round) and `006-opencode-v2-adapter` (PR #2, started on Codex, finished on OpenCode).
- Cross-harness resume worked in practice (`006`).
- Rendering is deterministic: re-rendering all five harnesses produces no diff against the tracked `dist/`.
- The CLI keeps routing cheap and now refuses to resume a run whose worktree is gone (`3bed157`).

## 2. Definition of "stable"

The factory is stable when all of the following hold on at least two harnesses:

1. **State is trustworthy.** Every `state.json` a run writes passes schema validation; timestamps are real and monotonic; every spawn and every stage transition is recorded.
2. **Invariants are enforced, not just instructed.** An orchestrator that drifts from the instructions cannot advance a stage, skip verification, or publish without the recorded gates.
3. **Recovery is proven.** A run killed at any stage resumes without re-asking answered questions, redoing committed tasks, or creating duplicate branches, worktrees or PRs.
4. **Reports are accurate.** Totals, the approver package and the auto-accept audit reflect what actually happened.
5. **Regressions are caught automatically.** CI runs the renderer, CLI and conformance tests on every change.

## 3. Evidence: what the last two runs show

Both runs succeeded, but their saved state shows the orchestrator drifting from the written contract. Because the contract is enforced only by instructions, nothing caught it.

| Observation | Run | Effect |
|---|---|---|
| `history` timestamps go backwards: `specify` 00:25, then `plan` 00:07. Several are rounded (`00:08:00Z`), which suggests invented times. | 005 | Timeline, last-activity sort and totals are unreliable. |
| No `implement` or `verify` history entry, although 8 tasks were committed. | 006 | Nothing in state proves the orchestrator ran its own build and test. |
| Ledger has 5 entries, all spec-builder. Implement, review and judge spawns are missing; the first entry has `duration_ms: 0`. | 006 | Totals report "32m overhead" that is really unrecorded agent work. |
| Off-vocabulary values: history events `continued-existing-scope`, `round-1-complete`, `approved-paused-before-pr`; timeline `kind: approval` (schema says `approver`). | 006 | Tools that read state by vocabulary misread the run. |
| Totals sentence: 6h 13m human + 1h 10m agents exceeds the 7h 12m wall clock; overhead clamps to `0s`. | 005 | Parallel reviewer durations are summed, so the formula is wrong whenever reviews run in parallel (known in product-brief §14, still unfixed in `bin/factory`). |
| Preflight halted because Codex SpecKit skills were missing; the run was then continued on another harness. | 006 | Preflight setup guidance is not yet self-sufficient per harness. |
| `relay` is cleared at every checkpoint, but the approver lists auto-accepted answers from `state.relay`. | All | The fast-mode audit shown at approval is empty for every stage except the current one (known in product-brief §14, still unfixed). |

## 4. Stability gaps

### P0 — required before calling the factory stable

| ID | Gap | Why it matters | Proposed change |
|---|---|---|---|
| S1 | **No state writer.** The orchestrator hand-edits `state.json`. | Source of every drift in §3: invented timestamps, missing entries, off-vocabulary values. | Extend `bin/factory` with narrow write commands: `checkpoint <stage>`, `ledger-add`, `wait-open` / `wait-close`, `answer`, `set-status`. Each stamps the time itself, validates vocabulary, writes atomically (temp file + rename) and commits the checkpoint. SKILL.md calls these instead of editing JSON. |
| S2 | **No schema validation.** Unknown or malformed fields are passed through verbatim. | Bad state is discovered only on resume, when it is hardest to repair. | Add `factory validate <run>` against the version 3 schema (stage, status, timeline kind, history event vocabularies; required fields per stage). Writers call it before every write; `show` reports violations. |
| S3 | **Transition gates are not enforced.** Nothing stops `implement → review` without a recorded green verify, or `approver → pr` without an approval decision. | `006` reached a PR with no recorded verify. | `checkpoint` refuses illegal transitions: `review` requires a `verify` entry with passing commands; `pr` requires an `approver` decision; `implement` requires analyze clean, remediated or user-overridden. |
| S4 | **Envelopes are trusted as prose.** The orchestrator decides whether a role output is valid. | A persuasive but malformed envelope can advance a stage. | Add `factory envelope check <file>` that validates the final fenced JSON block (envelope, findings, verdict shapes from protocol.md and findings.md). Malformed output enters the existing retry-once policy. |
| S5 | **Decision audit is lost at checkpoint.** | Fast-mode auto-accepts cannot be vetoed at approval, contradicting the README. | Move completed answers into an append-only `decisions` list (stage, question ID, answer, `auto`, time) before clearing `relay`. The approver reads `decisions`. |
| S6 | **Totals formula is wrong.** | Reports are misleading on every run with parallel reviews. | Store spawn start and end times; compute agent elapsed time as the union of intervals, and report aggregate agent effort separately. Never subtract summed parallel durations from wall time. |
| S7 | **No concurrency guard.** Two sessions can resume the same run. | Concurrent writers corrupt state and duplicate commits. | Lock file in the run's `factory/` directory with owner PID, harness and time; writers refuse while a live lock exists; `show` reports it; a stale lock needs explicit takeover. |
| S8 | **CLI and resume are untested.** All 6 tests cover the renderer. | The CLI already needed two fixes this week (`cb9c5e7`, `3bed157`). | Fixture-based tests for `runs`, `show` and every new write command: versions 1–3, pending runs, state copies in later worktrees, missing worktrees, ambiguous names, legacy relay shapes. |
| S9 | **No CI.** | Drift between `core/`, `adapters/` and tracked `dist/` is caught only by hand. | GitHub Actions workflow: run all tests, re-render every harness and fail on any `dist/` diff, run `bash -n install.sh`. |

### P1 — required for reliable multi-harness use

| ID | Gap | Proposed change |
|---|---|---|
| S10 | **Model configuration contradicts the docs.** README says only Claude Code pins models by default; every adapter pins models, and `adapters/opencode/adapter.json` pins personal provider IDs (`xiaomi-token-plan-sgp/...`, `zai-coding-plan/...`). | Ship adapters without models except where the harness requires one; keep personal choices in `${FACTORY_HOME}/config.json`. `install.sh` prints the effective model per role. Test that README and adapters agree. |
| S11 | **Preflight halts instead of guiding setup** when SpecKit skills for the current harness are missing (`006`). | Preflight names the exact `specify init --ai <harness>` command from `harness.md` and offers to run it, as it already does for a missing `.specify/`. |
| S12 | **Checkpoint uses `git add -A`.** Any untracked file in the worktree (build output, local secrets) is committed. | Stage only the spec directory plus files the role declared in its envelope `files`; report undeclared changes instead of committing them. |
| S13 | **Cross-machine resume is unproven.** State stores absolute `repo`, `worktree` and skill paths. | Add `factory rebind <run> --worktree <path>` that validates the branch and rewrites paths; document that sharing `FACTORY_HOME` alone does not move a run. |
| S14 | **No end-to-end conformance fixture.** | A tiny fixture repository plus a scripted "golden run" checklist per harness: start, pause at `review`, kill, resume on a second harness, approve, PR (against a throwaway remote). Record results per adapter and capability tier. |
| S15 | **Read-only role access is unverified per harness.** | Conformance test per adapter that a `read` role cannot edit files, or a documented disclosure where the harness cannot enforce it. |

### P2 — hardening after the above

- S16: Stale `pending/` files are never cleaned; add `factory prune --dry-run`.
- S17: `install.sh --harness` with no value fails with an unbound-variable error; validate arguments.
- S18: Usage figures are word-count estimates only; capture harness-reported usage where an adapter exposes it, labelled separately from estimates.
- S19: SKILL.md and the references repeat Pen-design rules in several places; consolidate into `design-code-mapping.md` to shrink the orchestrator's context.

## 5. Recommended sequence

| Milestone | Items | Exit condition |
|---|---|---|
| M1 — Trustworthy state | S1, S2, S5, S6, S8 | A run's state can be written only through the CLI; replaying the `005` and `006` states through `validate` reports their known defects; totals are correct for parallel reviews. |
| M2 — Enforced gates | S3, S4, S7, S9 | An illegal transition, malformed envelope or concurrent writer is refused by code, with a test for each; CI is green on main. |
| M3 — Portable and safe | S10–S13 | Adapters carry no personal models; checkpoints commit only declared files; a run is rebound to a new path and resumes. |
| M4 — Proven | S14, S15 | The golden run passes on Claude Code and OpenCode, including kill-and-resume across the two. |

Keep judgement (spec writing, review, fixes) in roles. Move only mechanical bookkeeping into code: the time, the vocabulary, the file write, the transition check. This keeps the factory instruction-driven and harness-portable while removing the failure points the recorded runs show.

## 6. Out of scope

Unchanged from [product-brief.md §5](product-brief.md#5-scope-product-boundaries-and-priorities): automatic merge or deploy, hosted dashboard, multi-repository features, a database, and automatic worktree deletion.
