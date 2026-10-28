# Specification Analysis Report — 013-skill-library, pass 2

Artifacts: `spec.md` (2007 words, budget 3000), `plan.md` (1158, budget 2000), `tasks.md` (1681, budget 2500), plus `research.md`, `data-model.md`, `contracts/install-cli.md`, `CONTEXT.md` "Skill library", `docs/adr/0009-library-skills-are-linked-not-rendered.md`, `.specify/memory/constitution.md`, `adapters/*/harness.md` (`RESOLVE` search orders). Extension hooks skipped (factory owns hooks).

## Pass 1 findings

All nine pass-1 findings are resolved in the current artifacts:

- D1: T004, T016 and SC-004 now run `test -z "$(git status --porcelain -- dist/)"`; plan Constitution Check III names it.
- U1: R6/T006/FR-002 copy LICENSE from upstream only; no offline fallback.
- U2: temp folder removed on failure (T012, R5); dot-folders never linked (T008, T010), tested in T007(f), T009, T011.
- U3: `mkdir -p` after validation (T012), absent-layer case in T011.
- A1: unchanged link prints `linked:` again (US1 AS3, T007(b), R4, contract).
- I1: T004/T016 marked "Verification task, no seam".
- I2: FR-005 reworded to the library-link ownership rule.
- U4: basename of the path as given (FR-008, T012), tested in T011.
- U5: shared Codex/Copilot root documented in T001, T015, spec edge cases, contract.

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| C1 | Inconsistency | MEDIUM | spec.md FR-004, FR-012, SC-001, Edge Cases (home override); adapters/{claude-code,opencode,zcode}/harness.md `RESOLVE` | With `CLAUDE_HOME`, `ZCODE_HOME` or `XDG_CONFIG_HOME` set, library links go to `$CLAUDE_HOME/skills`, `$ZCODE_HOME/skills` or `$XDG_CONFIG_HOME/opencode/skills` (FR-004), but each `RESOLVE` search order lists the literal default paths (`~/.claude/skills/`, `~/.zcode/skills/`, `~/.config/opencode/skills/`), and FR-012 freezes `RESOLVE`. SC-001 ("every installed harness … zero missing-skill stops") is then not guaranteed under an override. The pass-1 note "every declared root is already in each harness's `RESOLVE`" holds only for default homes. | Either state in Assumptions that the `~/.claude`, `~/.zcode`, `~/.config` prefixes in `RESOLVE` denote the harness home (so an override is honoured by the harness itself), or scope SC-001 to default homes. No `RESOLVE` edit needed (keeps FR-012). |
| U1 | Underspecification | LOW | tasks.md T011; plan.md S3 seam | The failed-copy case is induced by "an unreadable file in the source". Under root (common in CI containers) `chmod 000` does not make `cp` fail, so the test passes vacuously or fails spuriously. | Induce the failure with a `PATH`-shimmed failing `cp`/`mv` in the sandbox, or skip that sub-case when `os.geteuid() == 0`. |
| U2 | Underspecification | LOW | research.md R3; data-model.md "Library link"; tasks.md T008, T014 | Ownership is a string-prefix match on the current `$src/skills/`. A library link created from another checkout or worktree, or before the checkout moved, is classified as user-owned: install skips it with an adoption hint (which would copy the old repo-layer skill into the per-user layer) and uninstall leaves it. | Document this limitation in DESIGN.md/README (T001, T015), with the fix "remove the old link and re-run"; no code change required. |
| I1 | Inconsistency | LOW | spec.md FR-001, Edge Cases (license not obtainable); tasks.md T005, T006 | FR-001 requires all six vendored skills and T005 asserts all six, while T006 says a skill whose LICENSE cannot be obtained is "not vendored; report the gap instead". The task does not say that a gap stops the run (T005 then can never pass). | In T006, state that a gap stops implementation and is escalated, rather than completing with fewer than six skills. |

Seam check (factory override): every implementation task maps to a plan seam with its failing-test task immediately before it — T002→T003 (S1), T007→T008 (S2), T009→T010 (S2), T011→T012 (S3), T013→T014 (S4). T001, T006, T015 are plan-exempt; T004, T016 are verification tasks. No HIGH seam findings. Plan `Confirmed:` line lists exactly the five current seam names.

ENG-10: every new file, abstraction and dependency in plan.md "New files, abstractions and dependencies" carries a reason; dependency stated as `none`. No findings.

Word budgets: all three artifacts within budget. No findings.

## Coverage Summary

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 vendored repo layer | Yes | T005, T006 | I1 |
| FR-002 LICENSE + SOURCES.md | Yes | T005, T006 | |
| FR-003 per-user layer never committed | Yes | T009–T012 | Lives outside the checkout |
| FR-004 adapter skills roots + home override | Yes | T002, T003 | C1 |
| FR-005 link both layers, exclusions, stale prune | Yes | T007–T010 | U2 |
| FR-006 per-user wins | Yes | T009, T010 | |
| FR-007 skip non-library | Yes | T007, T008 | |
| FR-008 `--add-skill` validation/copy/reserved | Yes | T011, T012 | U1 |
| FR-009 `exists:` refusal | Yes | T011, T012 | |
| FR-010 uninstall library links only, layers kept | Yes | T013, T014 | |
| FR-011 no `dist/` change | Yes | T004, T016 | |
| FR-012 RESOLVE unchanged | Yes (no-op) | — | C1 |
| FR-013 tests | Yes | T002, T005, T007, T009, T011, T013 | |
| FR-014 README + DESIGN.md | Yes | T001, T015 | |
| SC-001 preflight finds six skills | Yes | T005–T008 | C1 under home override |
| SC-002 one-command add | Yes | T011, T012 | |
| SC-003 non-library files unchanged | Yes | T007, T013 | |
| SC-004 build + porcelain + tests | Yes | T004, T016 | |

**Constitution Alignment Issues:** none. I: T001 precedes installer/adapter work. II: no `core/` change. III: re-render plus porcelain gate after the adapter edit (T004) and at the end (T016). IV: N/A. V: every new item has a reason.

**Unmapped Tasks:** none (T004 and T016 are verification tasks).

## Metrics

- Total requirements: 14 FR + 4 SC = 18
- Total tasks: 16
- Coverage: 18/18 (100%) with at least one task (FR-012 needs no change by design)
- Ambiguity count: 0
- Duplication count: 0
- Critical issues: 0
- Severity counts: CRITICAL 0, HIGH 0, MEDIUM 1, LOW 3

## Next Actions

- No blocking findings; implementation may proceed.
- Remediate C1 with an Assumptions line (or SC-001 scoping), and fold U1, U2, I1 into T011, T001/T015 and T006 as small in-place edits.
