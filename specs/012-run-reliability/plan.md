# Implementation Plan: Factory Run Reliability

**Branch**: `012-run-reliability` | **Date**: 2026-10-28 | **Spec**: [spec.md](spec.md)

## Summary

Change the factory's agent instructions and adapters at the existing orchestration boundary. Make setup inspection honest, test-first work an atomic passing commit unit, seam confirmation cover failure-path scope, and deadline handoffs preserve pending verification. Keep runtime state schema, budgets, accounting and explicit model selections unchanged. No universal model service probe or new orchestration engine is needed.

## Technical Context

- Language/platform: Markdown role/skill contracts; Python 3 stdlib renderer and unittest checks; shell installer; five native harness targets.
- Dependencies/storage: existing renderer, CLI and JSON state; no new runtime dependency or state version.
- Performance: avoid optional repeated broad checks near a deadline; no speedup claim or budget increase.
- Scope: `DESIGN.md` first, then `core/roles/`, `core/skills/factory/` and `adapters/*/harness.md`; canonical generated `dist/`; focused model-policy tests and conformance evidence.
- Commands: use state `commands.build` and `commands.test`; focused tests use `python3 -m unittest discover -s tools -p test_render_models.py` or `test_budget.py`.

## Constitution Check

Pre-design and post-design: pass conditionally on the pending model-policy decision. Update DESIGN first, keep core harness-neutral, retain stateless handoffs and generate all five distributions in every source-changing task commit. Extend existing contracts and tests. No constitution amendment or exception is proposed.

## Decisions and implementation order

1. **Model setup**: extend the preflight contract with a three-way result: listed, unavailable in the active supported inventory, or unverified. Inspect installed/effective role selections, not merely repository defaults. Never change a model or credentials. A complete supported inventory can reject a selection for this setup; membership does not establish provider access. Partial, failed or unsupported inspection remains unverified. Repeat on relevant harness/model changes; preserve later rejection diagnostics and existing bounded retry/halt behavior.
2. **Adapter capability**: OpenCode's locally inspected `opencode --help` and `opencode models --help` expose `opencode models` as the inventory command. Keep this command in `adapters/opencode/harness.md`; inspect local help before using it on another version. The other four adapters disclose unverified when the session exposes no authoritative model inventory. An inherited model with no resolvable identifier is also unverified. Recovery names the exact selected ID and configuration source, then the existing per-harness model configuration/reinstall steps; it never guesses aliases.
3. **Model-policy baseline — pending Q2**: current adapters pin Claude Code, Codex and OpenCode; tests and DESIGN still say only Claude Code pins and expect sonnet rather than the current haiku standard model. Recommended: preserve current selections and align DESIGN/README, adapter notes and test expectations with the shipped mapping. Alternative: restore the old policy by changing defaults. Do not implement either until explicitly answered. Effective user overrides and canonical-render isolation remain unchanged.
4. **Commit units**: update engineering's authoritative task definition, then spec-builder generation/analyze, code-build, fixer, review/conformance and resume guidance to refer to it. New tasks contain ordered red, implementation and passing verification steps under one checkbox/commit unit. Preserve the two accepted `Red:` forms. Resume inspects incomplete work and completes the same unit. Unambiguous legacy adjacent test/implementation entries form one unit; both boxes become complete together, and completed work stays complete. Ambiguous legacy pairing stops before behavior changes.
5. **Seam scope**: the plan declares each seam plus required injected failure paths. Protected confirmation records that exact scope separately from declarations. Analyze checks every non-exempt task against declarations and confirmation; absent paths or stale/missing confirmation are HIGH blocking. Scope changes route through fresh protected confirmation; code-writing roles retain their stop-and-report guard.
6. **Deadlines**: at a passing commit boundary, check time before another unit or optional repeated broad verification. Use available observed check duration; when insufficient or uncertain near deadline, hand off rather than repeat it. Finish in-flight work safely; make a task red state explicit and never mark it complete. Partial summaries identify the next unit and pending required checks. Required final build/tests and independent orchestrator verification remain mandatory before review. Preserve actual overshoot, work-commit provenance and stall rules.

## Test seams

These are public workflow entry points. Native fixture trials test actual role decisions; output/link tests prove packaging only.

- **S1 — model setup and effective rendered selection**: preflight plus existing `tools/render.py --models`/per-user render. Cases: complete inventory includes/excludes the selected ID, failed/partial/unsupported inventory, inherited unresolved selection, installed-vs-default mismatch, later rejection, harness/model change; no substitution or state/worktree on confirmed rejection. Inject inventory outcomes through fixture task inputs, never provider credentials or live auth changes.
- **S2 — task generation, execution and resume**: factory tasks/implement/resume on `conformance/fixture-repo`. Cases: observed red then green in one commit, interruption after red, completed unit resume, unambiguous complete/partial legacy pair and ambiguous pairing; inspect real task boxes, git log and `Red:` proof.
- **S3 — plan scope confirmation and analyze gate**: factory plan/analyze entry points. Cases: undeclared seam, same seam with missing git-failure path, missing/stale confirmation, added/removed/renamed/expanded scope, valid exemptions and fully covered scope. Inject task/plan fixture text; use protected relay answers, not confirmation text as declarations.
- **S4 — deadline handoff and accounting**: file-writing role boundary plus existing `factory budget`, `ledger-add`, `issue-add`, `verify` CLI. Cases: completed unit near deadline, optional repeated suite omitted, in-flight overshoot, required checks still pending, resume then independent verification, progress vs three no-progress partials. Supply short deadlines and deterministic timestamps in fixture inputs; retain actual command durations in ledger. No process-kill/clock monkeypatch or new accounting seam is needed.

Exempt: explanatory DESIGN/README/reference prose, adapter metadata/notes and generated distributions - documentation/configuration-only parts; packaging checks still apply. Role behavior changes retain the S1–S4 fixture acceptance trials and are not waived by this exemption.

Overridden: none.

Awaiting explicit protected confirmation of S1–S4 and their listed failure paths; no `Confirmed:` line is valid yet.

## Project structure and additions

Extend existing files rather than introducing a runtime module. Keep source knowledge authoritative in DESIGN and the relevant shared reference, with role pointers where possible.

- `conformance/run-reliability.md` - file - reusable native-agent acceptance trials and required evidence for S1–S4.
- `conformance/golden-run-results.md` - existing evidence ledger; append honest trial outcomes and limitations.
- `specs/012-run-reliability/{research.md,data-model.md,quickstart.md,contracts/workflow.md}` - files - required planning decisions, conceptual contracts and validation guide for this run.
- New abstractions: none. New dependencies: none. New production state fields/commands: none.

## Verification and delivery constraints

Write a focused behavioral check/trial before each behavior unit, observe its failure against old instructions, then make the smallest change and verify passing output. For this run's legacy task-generation override, adjacent test/implementation entries are explicitly one commit unit: never commit or tick the red half independently. Commit each passing pair once with red proof and both boxes. Render and commit all five harness outputs with the source unit; inspect links and native metadata. Run the full Python suite, installer syntax check and final clean-dist gate after task commits; orchestrator repeats mandatory verification independently.

Use synthetic model names, temporary fixture repos and throwaway remotes; no real credentials, user config edits or publication during conformance trials. Preserve state-writer/append-only contracts, no-progress behavior and old state readability. Report unavailable native harness trials as unverified, never passed by static text checks. Capture paths, invocation, outcome and decisive git/CLI evidence. Resolve pending model-policy Q2 before baseline-green verification; do not suppress failing tests or silently rewrite defaults.
