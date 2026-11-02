# Analyze report 2: 017-per-project-models

In-place verification of remediation 1 (commit 1d065db). Artifacts: `spec.md` 1863 words, `plan.md` 1423, `tasks.md` 1277; all within budgets (3000 / 2000 / 2500).

## Pass-1 findings

| ID | Status | Evidence |
|----|--------|----------|
| M1 | closed | plan "Adapter defaults at runtime": copilot/zcode carry `{"deep": "", "standard": ""}`, parity treats absent tier as `""`, init seeds with source `adapter`; T002 implement/pass, T003 and T005 red cases cover it. |
| M2 | closed | plan Design defines `<repo>` via `git rev-parse --path-format=absolute --git-common-dir`; T003 red case uses `git worktree add`. |
| M3 | closed (rule), see H1 | plan Design and spec Edge Cases make unknown harness/tier keys malformed config; resolve seam, T003 and T004 carry the "unknown harness key" path. Q13 answered "A - accept" in `state.relay`, but the acceptance is not yet recorded in the plan. |
| M4 | closed | plan new-abstractions list has the `ModelConfigError` line with reason. |
| M5 | closed | plan Design keys refusal on `config.json` alone; T005 tests both README cases. |
| L1 | closed | plan Structure Decision says "over 1500 lines". |
| L2 | closed | tasks Dependencies: T008-T011 independent of T007, after T004. |
| L3 | closed | T005 has the pre-existing empty `.factory/` case. |
| L4 | closed | T007 tagged `[US6]`. |

## New findings

| ID | Category | Severity | Location | Summary | Recommendation |
|----|----------|----------|----------|---------|----------------|
| H1 | Test scope confirmation | HIGH (blocking) | plan.md "Test seams" line 121; tasks.md line 9 | The declared seam scope changed (resolve gained "unknown harness key"). The plan holds only the superseded Q2 line and says "fresh acceptance pending as Q13". No `Confirmed:` line covers the complete current scope, so the plan lacks current explicit confirmation per engineering.md "Confirmed test scope". The user accepted Q13 (`state.relay`, 2026-11-02T10:56:20Z, not auto), so no new question is needed. | Remediation: add `Confirmed: 2026-11-02 - Q13 accepted - seams: factory_cli.models.resolve, bin/factory models [--json], bin/factory init, adapter_models.json parity; failure paths: <current scope from plan Test seams, including resolve -> unknown harness key>`. Keep the Superseded Q2 line. Update tasks.md line 9 to cite Q13 as accepted. |

## Re-checks

- FR coverage still 100% (17 FR, 5 SC). Coverage matrix from analyze-1 unchanged; M1, M3 and M5 notes now resolved.
- Seams vs TDD tasks: resolve -> T003, models -> T004, init -> T005, parity -> T002. Failure paths in T003 equal plan resolve paths exactly (six). T004 "malformed config (including unknown harness key)" falls under the plan's models path. T005 paths equal plan init paths. Ordered Red / Implement / Pass steps present in T002-T005.
- Plan-exempt tasks (T001, T007-T011) and verification tasks (T006, T012, T013) excluded from the test-scope check.
- No new inconsistency between spec Edge Cases, plan Design and tasks: unknown key rule, worktree root and README refusal agree in all three.
- Constitution: no violations.

## Metrics

Counts: CRITICAL 0, HIGH 1, MEDIUM 0, LOW 0.
