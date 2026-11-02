# Analyze report 1: 017-per-project-models

Artifacts: `spec.md` (1836 words), `plan.md` (1243), `tasks.md` (1130). All within word budgets (3000 / 2000 / 2500).

## Findings

| ID | Category | Severity | Location | Summary | Recommendation |
|----|----------|----------|----------|---------|----------------|
| M1 | Underspecification | MEDIUM | plan.md "Adapter defaults at runtime"; tasks.md T002, T005; spec FR-011 | `adapters/copilot/adapter.json` and `adapters/zcode/adapter.json` have `"models": {}`. FR-011 requires init to seed both tiers for all five harnesses, and T002 says parity is "equality per harness". Neither artifact states what `adapter_models.json` holds for a harness with no adapter pin (`{}` vs `{"deep": "", "standard": ""}`), nor what `resolve` returns for a tier absent from every layer. | State in plan Design and T002/T003: an absent adapter tier resolves to `""` (inherit session model, FR-003) with source `adapter`; parity test treats a missing adapter tier as `""` (or `adapter_models.json` mirrors `{}` and `resolve` fills `""`). Add a T003 test case for it. |
| M2 | Coverage gap | MEDIUM | spec Edge Cases (worktree); tasks.md T003 | Edge case "run in a worktree looks up config at `state.repo`, not the worktree" is an implementation note in T003 but no test asserts it. | Add a T003/T004 red case: `cwd` inside a linked worktree resolves the main repo's `.factory/config.json`. |
| M3 | Ambiguity | MEDIUM | spec FR-008, SC-003, Edge Cases; plan Design | A project/user `models` key naming an unknown harness (e.g. typo `opencod`) is silently ignored by `resolve`, which iterates only harnesses in `adapter_models.json`. Spec's edge case ignores entries "for other harnesses" while SC-003 demands 100% of unresolvable configs stop. A typo'd harness key silently falls back — the failure mode Q4 meant to prevent. | Decide: unknown harness key raises `ModelConfigError`, or is explicitly allowed and documented. Needs a user decision if not covered by brief Q4; otherwise state it in plan Design and add a T003 failure path (changes confirmed seam scope). |
| M4 | ENG-10 (non-blocking) | MEDIUM | plan.md "New files, abstractions, dependencies" | New abstraction `ModelConfigError(path, detail)` (plan Design, T003) has no stated reason line. | Add `ModelConfigError - abstraction - <reason>` to the list. |
| M5 | Coverage gap | MEDIUM | spec Edge Cases (README exists, config absent); tasks.md T005 | Edge case "`config.README.md` exists but `config.json` does not: init writes config and regenerates README" has no T005 test. | Add T005 red case asserting README is overwritten and config written. |
| L1 | Drift | LOW | plan.md Structure Decision | States `commands.py` is "~800 lines"; actual file is 1557 lines. | Correct the figure or drop it. |
| L2 | Ambiguity | LOW | tasks.md Dependencies | "T008-T011 parallel after T007 drafting starts" is not an observable ordering. | Say "after T007" or "independent of T007". |
| L3 | Coverage gap | LOW | spec Edge Cases (`.factory/` exists without config); tasks.md T005 | Not explicitly tested. | Add one T005 case with pre-existing empty `.factory/`. |
| L4 | Traceability | LOW | tasks.md T007 | T007 implements the FR-007 disclosure step (US6) but is tagged `[US1][US2][US5][US4]` only. | Add `[US6]`. |

No CRITICAL or HIGH findings. Test-scope checks per engineering.md: every behaviour-changing task (T002-T005) maps to a seam declared in plan "Test seams", has ordered Red / Implement / Pass steps, and its failure paths match the declarations; the plan carries current explicit confirmation (`Confirmed: 2026-11-02 - Q2 accepted`) covering the complete declared scope. Plan-exempt tasks (T001, T007-T011) and verification tasks (T006, T012, T013) excluded from this check.

## Coverage matrix

| Requirement | Tasks | Notes |
|---|---|---|
| FR-001 project config path/schema | T003, T001 | |
| FR-002 cascade per tier | T003 | |
| FR-003 empty string inherits | T003, T008, T010 | see M1 for absent adapter tier |
| FR-004 single resolver, source labels | T003, T004, T005 | |
| FR-005 preflight records models/source | T007, T009 | prose, exempt |
| FR-006 SPAWN passes model | T007, T008, T010 | |
| FR-007 no-spawn-model disclosure | T007, T011 | |
| FR-008 malformed stop | T003, T004, T005, T007 | see M3 |
| FR-009 resume delta | T007, T009 | |
| FR-010 `factory models [--json]` | T004 | |
| FR-011 init seeds 5x2 effective values | T005, T002 | see M1 |
| FR-012 init table, unverified note, no probe | T005 | |
| FR-013 README sidecar | T005 | see M5 |
| FR-014 init refuses existing | T005 | |
| FR-015 global untouched | T005 | |
| FR-016 `/factory init` route | T007 | |
| FR-017 render/dist/install unchanged | T012 | `render.py` copies whole `core/skills/factory` tree, so `adapter_models.json` ships without render change |
| SC-001..SC-005 | T003, T004, T005, T012, T013 | |

## Specific checks

- Confirmed test seams (plan) vs TDD tasks: match (resolve -> T003; models -> T004; init -> T005; parity -> T002), failure paths identical.
- `[UI]` tasks: none; no design context; correct.
- Q1=A `adapter_models.json`: consistent across plan (runtime source, parity test, Constitution II note, structure, new-files list) and tasks (T001, T002, T003, T012).
- Brief decisions: cascade (FR-002/T003), spawn pass-through (FR-006/T007-T010), init seed + README + refusal (FR-011..015/T005), models CLI (FR-010/T004), malformed stop (FR-008/T003-T005/T007), resume disclosure (FR-009/T007/T009), harness disclosure (FR-007/T011) all covered.
- Paths spot-checked and present: `core/skills/factory/bin/factory_cli/{cli.py,commands.py}`, `tools/tests/test_render_models.py`, `adapters/*/adapter.json`, `adapters/*/harness.md`, `core/skills/factory/references/{verbs.md,state.md}`, `core/skills/factory/SKILL.md`. `commands.read_config()` and `main_repo()` exist as the plan cites.
- Constitution: no violations found.

## Metrics

- Requirements: 17 FR + 5 SC; FR coverage 100%.
- Tasks: 13; unmapped tasks: 0 (T006/T012/T013 verification).
- Counts: CRITICAL 0, HIGH 0, MEDIUM 5, LOW 4.

```json
{
  "status": "done",
  "stage": "analyze",
  "summary": "Analyze pass 1: FR coverage 100%, seams match TDD tasks, Q1=A consistent, brief decisions covered. 0 CRITICAL, 0 HIGH, 5 MEDIUM, 4 LOW. M1 copilot/zcode empty adapter models vs init seed shape; M3 unknown harness key silently ignored (pending user decision); M2 worktree config lookup untested; M5 README-regenerate edge untested; M4 ModelConfigError reason unstated (non-blocking).",
  "files": ["specs/017-per-project-models/factory/analyze-1.md"],
  "questions": [],
  "analyze": {"report": "factory/analyze-1.md", "critical": 0, "high": 0, "medium": 5, "low": 4},
  "counts": {"critical": 0, "high": 0, "medium": 5, "low": 4}
}
```
