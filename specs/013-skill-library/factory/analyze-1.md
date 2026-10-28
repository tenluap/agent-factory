# Specification Analysis Report — 013-skill-library, pass 1

Artifacts: `spec.md` (1221 words, budget 3000), `plan.md` (912, budget 2000), `tasks.md` (1369, budget 2500), plus `research.md`, `data-model.md`, `contracts/install-cli.md`, `.specify/memory/constitution.md`. Extension hooks skipped (factory owns hooks).

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| D1 | Constitution | CRITICAL | tasks.md T004, T016; spec.md SC-004; plan.md Constitution Check III | Constitution "Development Workflow" mandates `test -z "$(git status --porcelain -- dist/)"` and states a bare `git diff --exit-code -- dist/` "is not the gate". T004, T016 and SC-004 only use `git diff --exit-code -- dist/`. Plan claims "porcelain gate checked", but no task runs it. | Add the porcelain check to T004 and T016, and name it in SC-004 alongside the build command. |
| U1 | Underspecification | MEDIUM | tasks.md T006; research.md R6; spec.md FR-002 | The offline fallback copies `~/.agents/skills/<name>/`, which may not carry the upstream `LICENSE`. In that case FR-002 ("keep its upstream LICENSE") and seam S5 (T005) cannot be met. | State where the fallback gets `LICENSE` (e.g. the upstream LICENSE text for the recorded license), or say the fallback is not allowed when LICENSE is absent. |
| U2 | Underspecification | MEDIUM | tasks.md T010, T012; research.md R5 | `add_skill` copies into `$factory_home/skills/.<name>.tmp.$$`. No task removes the temp folder when the copy fails. `install_skills` links "folders containing `SKILL.md`" and does not exclude dot-folders, so a leftover temp folder would be linked as a skill. | In T012 remove the temp folder on failure (trap or explicit cleanup). In T010 ignore dot-prefixed folders. Add both cases to the T009/T011 tests. |
| U3 | Coverage | MEDIUM | spec.md Edge Cases ("`${FACTORY_HOME}/skills/` … created on first `--add-skill`"); tasks.md T011, T012 | No task creates the per-user layer when absent (`mkdir -p`) before the temp copy, and no test adds a skill when `${FACTORY_HOME}/skills/` does not exist. | Add `mkdir -p "$factory_home/skills"` to T012 after validation. Add the absent-layer case to T011. |
| A1 | Ambiguity | LOW | tasks.md T007(b); spec.md US1 AS3 | "A second run is identical and prints no change outside the links" does not say whether an unchanged library link prints `linked:` again. Research R4 calls it a no-op. | Define the re-run output for an unchanged link (e.g. no line, or `linked:` again) and assert it in T007(b). |
| I1 | Inconsistency | LOW | tasks.md T004, T016; plan.md Test seams | T016 carries "Exempt: verification only", which is not a plan exemption. T004 cites the adapter-values exemption for a verification-only step. Neither is an implementation task, so the seam check does not apply. | Drop the exemption labels from T004/T016 or mark them "verification task, no seam". |
| I2 | Inconsistency | LOW | spec.md FR-005; research.md R3; plan.md "New files" | FR-005 requires "the same symlink pattern as the factory skill", while R3 and the plan need a separate `link_skill` because the ownership rule differs (outside symlinks are skipped, not replaced). | Reword FR-005 to "symlinks, as for the factory skill, under the library-link ownership rule (FR-007)". |
| U4 | Underspecification | LOW | spec.md US3 AS1; contracts/install-cli.md skip message; tasks.md T012 | The adoption hint suggests `./install.sh --add-skill <target>`. For a symlink pointing outside the library, `cd "$path" && pwd -P` resolves to the real folder, whose basename can differ from the link name, so the hint can end in a name-mismatch refusal. The plan does not say whether the folder name comes from the given path or the resolved path. | State in T012 which basename is checked against frontmatter `name` (given path recommended), and test the adoption hint against an outside symlink. |
| U5 | Underspecification | LOW | spec.md FR-010; tasks.md T014 | Codex and Copilot share `~/.agents/skills`. `--uninstall --harness codex` also removes links that Copilot relies on. Neither the spec nor the README task mentions this. | Note the shared-root effect in T015 (README) and DESIGN.md (T001). |

No HIGH seam findings: every implementation task (T003, T008, T010, T012, T014) maps to a plan seam with its failing-test task immediately before it (T002, T007, T009, T011, T013). T006 (vendored content) follows its layout test T005 and is plan-exempt. No ENG-10 findings: every new file, abstraction and dependency in the plan has a stated reason. No word-budget findings.

## Coverage Summary

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 vendored repo layer | Yes | T005, T006 | |
| FR-002 LICENSE + SOURCES.md | Yes | T005, T006 | U1 offline gap |
| FR-003 per-user layer never committed | Partial | T009, T010, T012 | Lives outside the checkout; no explicit check needed |
| FR-004 adapter skills roots | Yes | T002, T003 | |
| FR-005 link both layers | Yes | T007–T010 | |
| FR-006 per-user wins | Yes | T009, T010 | |
| FR-007 skip non-library | Yes | T007, T008 | |
| FR-008 `--add-skill` validation/copy | Yes | T011, T012 | U2, U3, U4 |
| FR-009 `exists:` refusal | Yes | T011, T012 | |
| FR-010 uninstall library links only | Yes | T013, T014 | U5 |
| FR-011 no `dist/` change | Yes | T004, T016 | D1 gate wording |
| FR-012 RESOLVE unchanged | Yes (no-op) | — | Verified: every declared root is already in each harness's `RESOLVE` search order |
| FR-013 tests | Yes | T002, T005, T007, T009, T011, T013 | |
| FR-014 README + DESIGN.md | Yes | T001, T015 | |
| SC-001 preflight finds six skills | Yes | T005–T008 | |
| SC-002 one-command add | Yes | T011, T012 | |
| SC-003 non-library files unchanged | Yes | T007, T013 | |
| SC-004 build + test pass | Yes | T016 | D1 |

**Constitution Alignment Issues:** D1 (Development Workflow porcelain gate). Principles I–V are otherwise met: DESIGN.md goes first (T001), `core/` is untouched, there is a re-render after the adapter edit, no agent/state change, and every new item has a stated reason.

**Unmapped Tasks:** none (T004 and T016 are verification tasks).

## Metrics

- Total requirements: 14 FR + 4 SC = 18
- Total tasks: 16
- Coverage: 18/18 (100%) with at least one task (FR-012 needs no change by design)
- Ambiguity count: 1
- Duplication count: 0
- Critical issues: 1
- Severity counts: CRITICAL 1, HIGH 0, MEDIUM 3, LOW 5

## Next Actions

- Remediate D1 before implementation (small, in-place edit to T004, T016 and SC-004).
- Fold U1–U3 into T006, T010–T012 and their tests; the LOW items are optional wording fixes.
