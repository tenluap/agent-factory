# Specification Analysis Report — 016-retro-self-improve (pass 1)

Artifacts: `spec.md` (2097 words), `plan.md` (1510), `tasks.md` (2162), `checklists/requirements.md`, constitution 2.0.0. All within word budgets (3000 / 2000 / 2500).

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| U1 | Underspecification | MEDIUM | plan.md:L46; spec.md FR-004; core `references/findings.md` verdict shape | The `fixer-recurring` signal keys on a "finding class such as `eng-17`", but the verdict shape has no class field: ENG ids appear only inside `evidence` text and reviewer ids (`UX-2`, `SEC-1`) are per-finding. Findings without an `ENG-n` citation have no defined class, so the signal and its key subject are not deterministic. | Define the class source in plan.md and T008: e.g. the `ENG-n` id cited in a confirmed finding's evidence, lower-cased; findings with no `ENG-n` are not counted. |
| U2 | Underspecification | MEDIUM | plan.md:L45; spec.md FR-003; state.md `analyze.result` | `analyze-escalation` triggers on "any recorded analyze pass with CRITICAL or HIGH > 0", but `state.json` keeps only report paths plus the latest `analyze.result`; per-pass counts live in `factory/analyze-<n>.md`, which are not retro inputs (FR-003: retro reads nothing outside its inputs). The retro cannot see earlier passes. | Either base the signal on data in `state.json` (`analyze.loops > 0` or latest result) or add the analyze report paths to the retro inputs in FR-003, plan and T008/T009. |
| I1 | Inconsistency | MEDIUM | spec.md FR-010, Edge Cases L79; plan.md:L92 | FR-010 and the edge case speak of a "resumed run" not respawning retro, but plan.md states `resume` still refuses ended (`pr-open`) runs, so the marker only guards re-entry within the same orchestrator turn. The retro step also widens the window between `set-status pr-open` and `drop`/final push; an interruption there leaves a `pr-open` run unarchived and unpushed with no documented recovery (US3: "never leave a run half-archived"). | Align FR-010 wording with the plan (re-entry of step 9, not `resume`), and state the recovery for an interrupted retro window (e.g. manual `factory drop` + `git push` named in DESIGN.md/SKILL.md), or accept it explicitly in plan. |
| I2 | Inconsistency | MEDIUM | tasks.md T009 (L73), Dependencies L119 | T009 collects `covered_keys` from the `signal_key` field of the listing, which T007 adds; T009 depends on T004, T005, T008 but not T007. | Add T007 to T009's dependencies (task text and Dependencies section). |
| U3 | Underspecification | MEDIUM | plan.md:L88; tasks.md T009/T012; spec.md FR-010 | Unclear whether a failed retro attempt (crash / `failed` envelope) gets a `ledger-add retro` entry. FR-010 says every spawn is ledgered; plan step 3 ledgers only after saving output and logs failures only via `issue-add`. If failed spawns are not ledgered their cost is lost; if they are, the first failed attempt sets the resume marker before the retry. | State in plan and T012 that each spawn (including failed attempts) is ledgered and that the marker check happens only at step-9 entry, so the in-turn retry is unaffected. |
| I3 | Inconsistency | LOW | plan.md:L107; tasks.md T004 | Plan's project structure lists `tools/tests/test_state.py` for tests; T004 places the S3 tests in `tools/tests/test_commands.py` and no task edits `test_state.py`. | Replace `test_state.py` with `test_commands.py` in plan.md. |
| I4 | Inconsistency | LOW | spec.md FR-004 vs plan.md:L46 | FR-004 says "recurring finding classes the fixer repaired"; plan defines the signal as a class "confirmed blocking in 2+ rounds or 2+ times in one round" (confirmed, not necessarily repaired). | Align wording (e.g. "recurring confirmed-blocking finding classes sent to the fixer"). |
| I5 | Inconsistency | LOW | spec.md FR-007, FR-015; plan.md:L72 | Spec says the writer skips a key any open `ready` Retro entry covers; plan skips only keys covered by *another* run's entry and rewrites the own-run `ready` entry in place. Behaviour is intended (idempotent rewrite, Edge Cases L79) but FR-015 wording does not carve out the own-run case. | Add "from another run" to FR-015/Assumptions, or note the own-run replacement rule. |
| S1 | Style | LOW | spec.md L95-L104 | FR numbering is out of order (FR-015..017 sit between FR-008 and FR-009). | Optional: reorder or add a note; IDs must stay stable. |
| S2 | Style | LOW | checklists/requirements.md | Checklist marks "No implementation details" while spec names the `factory improvements add --from <file> --run <branch>` CLI and entry field names; the note justifies factory vocabulary but not CLI flags. | Extend the checklist note to cover the CLI writer as a settled grill decision. |

## Coverage Summary

| Requirement | Has Task? | Task IDs | Notes |
|-------------|-----------|----------|-------|
| FR-001 retro role read-only standard | Yes | T008 | S4 |
| FR-002 spawn between pr-open and drop | Yes | T009 | |
| FR-003 retro inputs | Yes | T008, T009 | see U2 |
| FR-004 five signals | Yes | T008 | see U1, U2 |
| FR-005 envelope candidates | Yes | T002, T008 | |
| FR-006 at most 3 | Yes | T008, T011 | |
| FR-007 skip covered keys | Yes | T008, T009, T011 | |
| FR-008 persist only via writer | Yes | T005, T009 | |
| FR-009 no writes/questions | Yes | T008 | |
| FR-010 ledger marker, no history event | Yes | T004, T009 | see I1, U3 |
| FR-011 one retry then skip | Yes | T012 | |
| FR-012 final notice names skip | Yes | T012 | |
| FR-013 protocol + DESIGN first | Yes | T001, T002 | |
| FR-014 harness-neutral, renders | Yes | T008, T013 | |
| FR-015 deterministic writer | Yes | T005, T006, T010, T011 | |
| FR-016 entry shape / name | Yes | T005 | |
| FR-017 listing kind/signal_key | Yes | T007, T009 | see I2 |
| SC-001 retro or named skip | Yes | T009, T012 | |
| SC-002 cap 3 | Yes | T011 | |
| SC-003 no duplicate | Yes | T011 | |
| SC-004 never blocks | Yes | T012 | see I1 |
| SC-005 suggested_feature usable | Yes | T002, T010 | |

## Test-seam scope check (engineering.md "Confirmed test scope")

Declared seams (plan.md L125-L135) and confirmation (L137, decision `plan` Q1, `auto: false`, 2026-10-31T02:01Z) match one-to-one.

| Seam / failure path | Task | Status |
|---------------------|------|--------|
| S1 malformed candidate dropped | T010 | covered |
| S1 covered by another run's `ready` entry skipped | T011 | covered |
| S1 over-cap dropped counting own-run entries | T011 | covered |
| S1 claimed own-run entry not overwritten | T011 | covered |
| S1 run not `pr-open` refused | T005 | covered |
| S1 `--from` unparseable refused | T005 | covered |
| S1 lock held past wait refused | T006 | covered |
| S1 unwritable `improvements/` exit 1, no debris | T005 | covered |
| S2 listing (none) | T007 | covered |
| S3 non-`retro` stage on `pr-open` refused | T004 | covered |
| S3 `retro` on `aborted` refused | T004 | covered |
| S4 render (none) | T008 | covered |

Every behaviour-changing task (T004-T008, T010, T011) has a mapped seam, ordered failing-test / implement / passing-check steps and a red-proof line. Exempt tasks (T001-T003, T009, T012, T013) match plan exemptions or are verification-only. No HIGH seam finding. Confirmation is current: no seam or failure path changed after acceptance.

ENG-10: new file `core/roles/retro.md`, abstractions `improvements.add`/`cmd_improvements_add` and `_write_atomic`, and dependency `none` are each stated with a reason (plan.md L110-L115). Runtime files `retro-envelope.md` and `improvements.lock.json` carry reasons in "Settled deferred items" and "Quality constraints". No finding.

## Constitution Alignment

- I Design First: T001 precedes all core/adapter tasks. Pass.
- II Harness-Neutral Core: T008/T009 restrict to neutral verbs; S4 asserts no harness tool. Pass.
- III Generated Dist: T008/T013 check `dist/` untracked. Pass.
- IV Stateless Agents: retro reads only inputs; marker in ledger. Pass.
- V Simplicity: new file/fields have stated reasons. Pass.

No constitution issues.

## Unmapped Tasks

None. T013 is verification-only polish.

## Metrics

- Total requirements: 17 FR + 5 SC = 22
- Total tasks: 13
- Coverage: 100% (22/22)
- Ambiguity/underspecification count: 3 (U1-U3)
- Duplication count: 0
- Critical issues: 0
- Severity counts: CRITICAL 0, HIGH 0, MEDIUM 5, LOW 5

## Next Actions

No CRITICAL or HIGH findings; implementation is not blocked. Remediate U1, U2, I1, I2, U3 in place in spec.md, plan.md and tasks.md; LOW items are wording fixes.
