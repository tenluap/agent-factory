# Remediation log - pass 1

**Feature**: 005-skill-routing | **Date**: 2026-10-25 | **Report**: [analyze-1.md](./analyze-1.md)

All 9 findings (4 MEDIUM, 5 LOW) fixed in place. No finding needed a user decision, so
`pending_clarify` is empty.

| ID | Severity | What changed |
|----|----------|--------------|
| I1 | MEDIUM | `plan.md` Summary now says "five roles" (was "four", while naming five); Scale/Scope now says "13 edited source and document files (... 5 roles ...)" (was "11 ... 4 roles"), matching the file list and T004-T019. |
| U1 | MEDIUM | Added `Exempt: setup/environment steps - configuration only - no product file changes.` to `plan.md`'s exemption list and rewrote T001's exemption line to quote it verbatim, so every exempt task again quotes a plan exemption. |
| G1 | MEDIUM | `tasks.md` T021 now carries an explicit FR-030 check (no new role file under `core/roles/`, no new verb in `references/verbs.md`, no new `state` telemetry field, model tiers unchanged) and cites FR-030. FR-030 now has a task and a verification step. |
| G2 | MEDIUM | Added `quickstart.md` manual check 7 (read `DESIGN.md` + `references/skills.md` against `SKILL.md`, `code-build.md`, `fixer.md`, `ui-reviewer.md`; each precedence/loading rule stated once, no restatement or conflict) and wired it into T021 for SC-010. T022 now reads "checks 1-6 (check 7 is a document read, run in T021)". |
| G3 | LOW | Added `FR-027` to the citation lists of T006, T011, T013, T014, T015 and T016 (and to T004), so FR-027's coverage is explicit. |
| I2 | LOW | `plan.md` Seam 3 now reads "`requires_user` documented in `protocol.md`'s question fields and `state.md`'s fast-mode step", matching the quickstart assertion and T012. |
| G4 | LOW | The context-cost constraint is now machine-checked: `quickstart.md` Seam 2 asserts `references/skills.md` is under 60 lines and contains no `ENG-` match (guarded by `exists()` so the red run still works); the plan's Seam 2 bullet and Constraints "Context cost" line say it is asserted by Seam 2; T021 confirms it. Assertion executed - still prints the expected red (file absent, three links missing), exit 1, no crash. |
| I3 | LOW | T020 reworded as the final render gate and scope check (render once more, confirm the gate is clean, confirm no model setting changed), noting earlier `core/` tasks already rendered per Render discipline, so it is no longer stated as the render step. |
| A1 | LOW | T004 now records two or three example cue phrases per intent in `DESIGN.md`'s routing contract (citing FR-001, SC-001), and quickstart manual check 1 names concrete cue phrases for the three trials and points at the recorded contract, making SC-001 repeatable. |
| F1 | LOW | `spec.md` Key Entities "Exploration stage" now names the concrete stage values: `` **Exploration stage** `brainstorm` ``, "settling into `grill`". |

## spec.md word budget

`spec.md` had 8 words of headroom. The F1 edit was offset by trimming the "UI change signal"
entry ("including tokens, ... and user-visible copy" to a colon-led list), so `wc -w spec.md`
is **2992**, unchanged. Current counts: `spec.md` 2992/3000, `plan.md` 1710/2000,
`tasks.md` 2090/2500 - all within budget.

## Not changed

No constitution edit (none needed; no CRITICAL findings). No artifact regenerated: every change
is a targeted edit. `.specify/memory/constitution.md`, `research.md`, `data-model.md` and
`checklists/requirements.md` were untouched.
