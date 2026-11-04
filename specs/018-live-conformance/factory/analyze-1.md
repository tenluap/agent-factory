# Specification Analysis Report — 018-live-conformance, pass 1

Artifacts: `spec.md` (2872 words), `plan.md` (1131), `tasks.md` (1961), `research.md`, `data-model.md`, `contracts/bench-cli.md`, `quickstart.md`, `factory/relay/plan-Q1.md`; constitution `.specify/memory/constitution.md` v2.0.0. Claims checked against `tools/bench.py`, `tools/render.py` (`load_adapter`), `install.sh`, `adapters/{claude-code,opencode}/adapter.json`, `tools/tests/__init__.py` (`Sandbox`), `DESIGN.md` ("Benchmark" bullet, line 291) and `conformance/golden-run/*.md`.

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| C1 | Inconsistency | MEDIUM | spec.md Quality Requirements "Isolation"; plan.md Technical Context "Constraints"; research.md R4 "Credentials" | Spec and plan say an opt-in checkout run "writes only under its output directory". R4 says OpenCode keeps provider auth under its data directory, which isolation does not move; OpenCode also stores sessions/logs there (only `XDG_CONFIG_HOME` is redirected). The absolute claim is untrue for OpenCode trials. SC-004 itself (factory home and harness configuration unchanged) is consistent. | Narrow the Quality "Isolation" line and the plan constraint to the factory home and harness configuration (SC-004 wording), and state that OpenCode's data directory (auth, session storage) is shared by design. Have T008 note it in the OpenCode isolation step. |
| U1 | Underspecification | MEDIUM | tasks.md T003 Implement ("skill directory from `render.load_adapter` under the isolated environment"); plan.md Source Code tree | `render.load_adapter(name, use_env=True)` reads the process `os.environ` and returns an already formatted `skill_dir`; it takes no environment argument. T003 does not say how the isolated skill directory is derived: mutating `os.environ` in the driver (shared mutation, ENG-9) or adding a parameter to `tools/render.py` (not in the plan's source tree or new-items list; constitution V requires a reason for a new field). | State the derivation in T003 and the plan, e.g. a scoped environment override around the call, or `<out>/harness-config` plus the adapter's `skill_dir` template; if `render.py` changes, list it in the plan with its reason. |
| G1 | Coverage Gap | MEDIUM | spec.md FR-011, FR-012 ("no capability-note placeholders left"); tasks.md T007, T008 Done; `conformance/golden-run/claude-code.md` and `opencode.md` lines 32-34, "Resume on a second harness" step | The checklists' capability notes hold `<fill ...>` and also `<enforced \| disclosed limitation>`; the resume step holds `<second>`. T007/T008 replace only `<fill ...>` and verify with `grep -n "<fill"`, so FR-011/FR-012 can be marked done with a placeholder left. | Name every placeholder in T007/T008 (Invoke, Read-only enforcement, Extra setup arguments, `<second>`) and make the done check cover them, e.g. `grep -nE "<(fill\|enforced\|second)" <file>` empty. |
| G2 | Coverage Gap | LOW | spec.md Edge Cases ("A model choice is given together with the checkout flag: both apply"); tasks.md T002, T003 | No task asserts `--model` together with `--from-checkout`. | Add one assertion to T003: a checkout run with `--model` carries the model option and the isolated environment. |
| U2 | Underspecification | LOW | tasks.md T002 Red ("`--add-dir` entries for the skill directory (link path and resolved target)"); contracts/bench-cli.md Launch commands | The T002 sandbox leaves `CLAUDE_HOME` empty, so link path and resolved target are equal and deduplicate to one entry; the resolved-target branch is never exercised. Behaviour when the installed skill directory is absent (still granted, or omitted) is also unstated. | In T002 create `CLAUDE_HOME/skills/factory` as a symlink to a sandbox directory outside `<out>` and assert both entries; state in the contract whether an absent skill directory is granted. |
| S1 | Security (guidance) | LOW | spec.md Quality "Security" ("narrowest set"); research.md R2; tasks.md T007 | `Bash(python3:*)` and `Bash(git:*)` permit arbitrary code execution through `python3 -c` or git config hooks. The allow-list is a settled user decision (brief Q2), and confinement to the disposable fixture is the real control. | Keep the list; have T007 state the residual risk and that the grant applies only to disposable bench runs. |
| R1 | Underspecification | LOW | research.md R2 "Trial-time check"; `install.sh` `install_skills` | In checkout mode `install.sh` links repo-layer skills (`<checkout>/skills/*`) into `<out>/harness-config/skills`, so library skill reads resolve outside `<out>` and rely on the bare `Read` rule, the same as the installed baseline. R2's trial-time check names only the installed baseline. | Extend the R2 trial-time check, and the T007 smoke step, to checkout mode. |
| I1 | Inconsistency | LOW | tasks.md T009; `conformance/golden-run-results.md` existing per-adapter table (lines 7-13) | The results document already has a per-adapter table with "not yet run" rows for the same live run. T009 adds a per-leg table without saying how the two relate, leaving two places to record one trial. | State in T009 whether the per-leg table supersedes, or is referenced from, the per-adapter rows for claude-code and opencode. |

No CRITICAL or HIGH findings.

## Test-scope and commit-unit check (engineering.md)

- Declared seams: `bench.py run` CLI (6 failure paths), `bench.py score` CLI (4), `bench.checkout_provenance(path)` (1). Exempt: four documentation parts (T001, T007, T008, T009), excluded from this check.
- Confirmation: `Confirmed:` line names every seam and failure path in plan.md; it matches the declarations one-for-one and the snapshot `factory/relay/plan-Q1.md`; `state.decisions` records plan Q1 = A, `auto: false`. Current and complete.
- Every implementation task (T002-T006) has a mapped plan seam, ordered Red / Implement / Pass steps in one checkbox, required failure paths drawn only from the declarations, and an observable Done condition. Every declared failure path is covered: executable missing (T002); install fails, `--from-checkout` with `--home` (T003); not a git repository (T004); harness non-zero, `--version` fails, installed factory absent (T005); no record, malformed record, repo mismatch, unreadable state (T006).
- T010 is verification only (no file change, no commit unit).

## ENG-10 and word budgets

- plan.md "New files, abstractions and dependencies" gives a reason for each new abstraction (`launch_command`, `isolated_install`, `checkout_provenance`/`tree_digest`/`write_provenance`, `load_provenance`) and states files and dependencies as none. No ENG-10 finding.
- Word counts within budget: spec.md 2872/3000, plan.md 1131/2000, tasks.md 1961/2500.

## Coverage Summary

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 scoped Claude Code grant | Yes | T002, T003 | |
| FR-002 no bypass mode | Yes | T002 | both harnesses, with and without `--model` |
| FR-003 model option | Yes | T002 | |
| FR-004 opt-in checkout render | Yes | T003 | see U1 |
| FR-005 unchanged without flag | Yes | T003 | |
| FR-006 render failure stops | Yes | T003 | |
| FR-007 provenance before launch | Yes | T004, T005 | |
| FR-008 unavailable values | Yes | T004, T005 | |
| FR-009 score carries provenance | Yes | T006 | |
| FR-010 existing behaviour preserved | Yes | T002, T006, T010 | |
| FR-011 Claude Code checklist | Yes | T007 | see G1 |
| FR-012 OpenCode checklist | Yes | T008 | see G1, C1 |
| FR-013 per-leg results rows | Yes | T009 | see I1 |
| FR-014 throwaway PR repo | Yes | T007, T008 | |
| FR-015 offline verification | Yes | T002-T006, T010 | stubs for both harnesses |
| SC-001 | Yes | T002 | |
| SC-002 | Yes | T002 | |
| SC-003 | Yes | T005, T006 | |
| SC-004 | Yes | T003 | see C1 |
| SC-005 | Yes | T010 | |
| SC-006 | Yes | T007, T008, T009 | see G1 |

**Constitution Alignment Issues:** none. I (Design First): T001 updates the DESIGN.md "Benchmark" bullet before `tools/bench.py`. II: no `core/` change. III: renders go under the run's output directory; T010 checks `dist/` is untracked. IV: no agent change. V: reasons stated (U1 notes one possible unplanned `render.py` field).

**Unmapped Tasks:** none (T001 maps to constitution I; T010 to SC-005).

## Metrics

- Total requirements: 21 (15 FR, 6 SC)
- Total tasks: 10
- Coverage: 100% (21/21 with at least one task)
- Ambiguity count: 2 (U1, U2)
- Duplication count: 0
- Critical issues: 0
- Severity counts: CRITICAL 0, HIGH 0, MEDIUM 3, LOW 5

## Next Actions

No blocking findings. Remediation can fix C1, U1 and G1 in place (spec Quality line, plan constraint, T003, T007, T008) and the five LOW findings with targeted edits; none needs a user decision or changes the confirmed test scope (the G2 and U2 assertions add cases within existing seams and failure paths).
