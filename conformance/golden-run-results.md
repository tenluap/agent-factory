# Golden-run results (FR-013)

Per adapter and capability tier. The live two-harness run is recorded after
merge (one enforcing harness paired with one disclosing harness); the
checklists live in `golden-run/<harness>.md`.

| Harness | Tier | Run date | Result | Steps passed | Notes |
|---|---|---|---|---|---|
| claude-code | enforcing | _after merge_ | not yet run | / | |
| opencode | enforcing | _after merge_ | not yet run | / | |
| copilot | enforcing | _after merge_ | not yet run | / | |
| zcode | enforcing | _after merge_ | not yet run | / | |
| codex | disclosing | _after merge_ | not yet run | / | read-only by instruction only |

A result records the fixture commit, both harnesses used, and the kill/resume
leg. `/` marks a step that does not apply on that adapter.

## Run reliability (012)

Native workflow acceptance follows [run-reliability.md](run-reliability.md). Packaging checks do not prove agent behavior. Record each matrix case separately; preserve the subject's original output before assessing it.

| Case | Instruction commit/hash | Native subject and input | Observed evidence | Before | After |
|---|---|---|---|---|---|
| S1 matrix | old `3cef63f`; changed S1 instructions | fresh native `s1_before` / `s1_after`, identical nine-case input | excerpts below; archived full outputs/hashes under run `factory/trials/s1/` | gate/recovery failures observed | 9 decision cases passed |
| S2 matrix | old `3cef63f`; changed `bbefbca` | fresh native before/after; symmetric healthy S2-new repeat | six fixture cases plus reviewer controls; task/git/test artifacts below | separate-checkbox conflict observed; passing controls retained | one ordered unit; resume and protected stop passed |
| S3 matrix | old `3cef63f`; changed `ad65834` | fresh native before/after, identical eleven-case scope input | decision envelopes, artifact excerpts and hashes below | missing failure/acceptance blockers and same-name expansion gap | eleven stage-contract cases passed |
| S4 matrix | old `3cef63f`; changed `d2eb19b` | fresh native before/after, affected-case v2 and verification resume | actual clocks/commands/commits, independent root fixture check and CLI controls below | required-check admission gap; optional/inflight controls retained | accurate pending handoff, no false overrun, verification completed |

Each result must name actual envelope/fixture paths, decisive output excerpts, relevant git commits/checkboxes or CLI statuses, and any capability limitation. Keep before/after subjects fresh and record differing absolute paths/deadlines. Pending/unavailable cases do not count as completed acceptance. The model-policy baseline is recorded in `specs/012-run-reliability/factory/baseline.md`: 19 focused tests ran with three existing policy failures before behavior edits.

### S1 observed before/after — 2026-10-28

Two fresh native contexts read frozen old/new factory+OpenCode instructions and the same synthetic inventory scenarios. Before: `3cef63f` core/adapter contracts; after: T003+T004 source changes. Subjects received neutral scenario facts, without the outcome rubric or feature artifacts. Full reports, input and prompt hashes, and focused-test logs were captured under `specs/012-run-reliability/factory/trials/s1/` for run archival. The in-use after snapshot contained an exact duplicated preflight paragraph; source cleanup removed the duplicate without changing its rule. Both tested and cleaned source hashes are retained.

| Case | Before observed decision | After observed decision | Result |
|---|---|---|---|
| S1-hit | No inventory gate; continue | `listed_access_unverified`; exact `fixture/selected` retained | pass; listed is not access proof |
| S1-miss | Pending-state creation eligible despite excluded selection | `authoritatively_unavailable`; resource creation false; exact ID/source and reinstall/recheck steps | observed red→green |
| S1-error | No inventory-specific status/recovery | `unverified`; original exit-2 diagnostic preserved; bounded policy retained | pass |
| S1-partial | No inventory-specific status/recovery | `unverified`; omitted ID cannot reject from partial results | pass |
| S1-unsupported | No inventory-specific status/recovery | `unverified`; no invented API | pass |
| S1-inherit | Inherited selection preserved without inspection disclosure | `unverified`; unresolved inheritance preserved | pass |
| S1-effective | Installed override retained but pending creation eligible despite exclusion | `fixture/installed` rejected; listed repository default not substituted; no resources | observed red→green |
| S1-reject | Generic retry once, then halt | Original rejection and choice preserved; actionable correction/recheck plus unchanged one-retry/halt | pass; recovery improved |
| S1-resume | Skill paths re-resolved; no model reinspection gate | Changed `fixture/new` inspected and rejected before resources/role | observed red→green |

These are native preflight/recovery **decision** trials using injected observations, not live provider access probes. Neither subject created production resources or launched a runtime retry. S1-reject preserves/assesses the bounded retry decision; actual generic retry/accounting execution remains covered by existing factory tests. Provider access and unavailable inventory APIs remain explicitly unverified. No model/configuration/credential changes occurred.

Focused command: `python3 -m unittest discover -s tools -p test_render_models.py`. Before: 19 tests, three known model-policy failures. After: 19 tests, **OK**, including exact shipped selections, installed override behavior, canonical-config isolation and inherited-model reporting. All five harnesses rendered; adapter JSON mappings unchanged. Full-suite/final clean-dist checks are recorded in the final verification section; independent orchestrator verification is a separate required gate.


### S2 observed task-generation/resume — 2026-10-28

Frozen old and changed instructions were exercised by fresh native subjects with neutral inputs, isolated Python greeting repositories and actual task/git/test evidence. Permanent reports, fixture artifacts, command/commit logs, prompts and source hashes are under `specs/012-run-reliability/factory/trials/s2/`.

| Case | Old instructions | Changed instructions | Assessment |
|---|---|---|---|
| S2-new | Healthy full tasks→analyze→implement run generated **two** separate test/implementation checkboxes. Subject explicitly resolved the old conflicting obligations by pairing T001/T002 in one passing commit. | Healthy full run generated **one** T001 checkbox with ordered red/implementation/passing steps; clean analysis recorded before implementation; one passing commit with valid red proof. | `S2-new-generation-atomic-unit` fails old output (2 boxes), passes changed output (1); no claim that old execution necessarily fails. |
| S2-red-resume | Observed existing red test, implemented and committed once. | Continued the same incomplete unit, observed red then green and committed once. | Preserved passing control; real files/test output and git bodies captured. |
| S2-complete | Checked passing unit preserved; no duplicate implementation commit. | Same completed commit preserved and checks passed. | Preserved passing control. |
| S2-legacy-complete | Checked pair and passing commit preserved. | Same existing pair/commit preserved. | Preserved passing control. |
| S2-legacy-partial | Checked red half plus uncommitted test completed with implementation in one passing commit. | Explicitly reconciled the pair and finished both entries together in one passing commit. | Preserved passing behavior, now an explicit shared contract. |
| S2-ambiguous | Stopped without production-code change after observing red; disclosed task/commit conflict and ambiguous pairing. | Stopped before any fixture behavior/test edits, naming ambiguous T001→T002/T003 pairing. | Protected stop retained; no pairing invented. |
| S2-review | Actual commit reviews accepted mapped observed-red proof; instruction-level controls accepted existing-test proof and valid documentation exemption. | Same red-proof/exemption rules retained; actual unit commit review has no findings. | Preserved controls; proof-form controls are labeled instruction-level, not separate executed behavior commits. |

The healthy before subject disclosed the conflict between a separate failing-test task, the per-task commit instruction and ENG-3. Its successful joint commit is retained as evidence rather than manufactured into a failure. The generation acceptance check reads the **native-produced tasks artifact**, not source-text presence. Replay: `python3 specs/012-run-reliability/factory/trials/s2/assess-generated-unit.py before` exits 1; `... after` exits 0. Both healthy fixtures observed red failures for blank-name inputs, then all three greeting tests passed; normal/surrounding-whitespace behavior remained intact. Their state/analysis histories show the normal lite transitions before implementation.

**Experiment correction:** initial S2-new fixtures omitted normal analysis/constitution prerequisites; one initial subject also used an incorrect default analyze transition. Those original reports are retained as invalid-fixture history and are excluded from the full-stage pass. Only fresh, symmetric `before-healthy` and `after-healthy` S2-new runs count for that case. The other five isolated cases retain their actual observed outcomes. The original before-fixture skill paths were corrected to the main checkout; those setup-only state changes are not product behavior evidence.

All five harnesses canonical-rendered after the source changes. `python3 -m unittest discover -s tools -p 'test_render*.py'` passed **27 tests**; `git diff --check` passed. The configured budgets, runtime state schema, model mappings and mandatory final checks are unchanged. S3/S4 evidence follows; T012 checks are recorded in the final verification section.


### S3 observed scope/confirmation contracts — 2026-10-28

Two fresh native subjects applied frozen old/new plan/analyze contracts to the same eleven independent task/plan/spec artifact sets. Inputs explicitly supplied unrelated prerequisites as satisfied and used an unambiguously paired legacy red/implementation task, compatible with both task formats. These are **stage-contract decision trials**: actual envelopes/findings and proposed confirmation edits are recorded in reports; no full SpecKit pipeline, live user relay, production state or fixture edits are claimed. Raw reports, identical artifact bytes, neutral prompts and tested source hashes are retained under `specs/012-run-reliability/factory/trials/s3/` for archival.

| Case | Old observed contract result | Changed observed contract result | Assessment |
|---|---|---|---|
| S3-undeclared | HIGH, ineligible | HIGH, ineligible; acceptance of another seam does not declare it | Preserved blocking control |
| S3-git-path | Same seam name sufficed; HIGH 0, eligible despite undeclared git failure | HIGH 1, ineligible; names T001/T002 and missing git failure | Observed red→green |
| S3-missing | HIGH 0, eligible without scope acceptance | HIGH 1, ineligible; acceptance absent | Observed red→green |
| S3-stale | HIGH 0, eligible although saved scope lacked added git failure | HIGH 1, ineligible; accepted snapshot mismatches declaration | Observed red→green |
| S3-add/remove/rename | Protected needs_input, initially ineligible | Same protected needs_input for exact current scope | Preserved controls |
| S3-expand | Plan reused equal seam names; done/eligible | needs_input, ineligible; same-name failure expansion requires acceptance | Observed red→green |
| S3-covered | HIGH 0, eligible | HIGH 0, eligible | Preserved valid coverage/confirmation |
| S3-exempt | Eligible without invented runtime seam | Eligible under valid documentation exemption | Preserved exemption |
| S3-protected | Fast mode did not answer protected question; supplied explicit reply permitted continuation | Same initial protected wait, zero auto accepts; explicit fixture reply produced `Confirmed: ... seams: greet; failure paths: greet={copy failure}` and eligible continuation | Preserved protection; complete scope now retained |

`S3-failure-scope-acceptance` assesses native outputs: `python3 specs/012-run-reliability/factory/trials/s3/assess-scope.py before` exits 1 for missing git-path/missing/stale blockers and same-name expansion; `... after` exits 0 for all eleven cases. Source uses one shared confirmed-scope definition; declarations and acceptance remain separate. Legacy name-only acceptance is reusable only with independent exact-scope evidence. No runtime state field, budget, model mapping or accounting change was introduced.

All five harnesses canonical-rendered. Focused renderer/model suite passed **27 tests**; `git diff --check` passed. S4 evidence follows; final repository checks and independent verification are separate gates.

### S4 observed boundary/handoff/accounting — 2026-10-28

Evidence: `specs/012-run-reliability/factory/trials/s4/` retains native neutral prompts, input facts, original/changed/v2 reports, tested source snapshots/hashes, real git/command evidence, resume and independent verification reports, accounting CLI records and runnable `assess.py`. Subjects had no outcome rubric. Code-build was the native subject; the other file-writing roles share the same protocol and were inspected statically, not claimed as separate native trials.

| Case | Before observation | After observation | Assessment |
|---|---|---|---|
| S4-optional / uncertain | Already omitted unnecessary repeats; done with supplied required checks complete | Same behavior; omitted probes with known/unknown fit rationale | Preserved controls, no manufactured red |
| S4-pending | Started broad-check probe despite supplied prior300s vs45s remaining; old contract had no admission handoff | Explicit partial, exact mandatory checks pending, no invocation; v2 replay omits false overrun | Observed `S4-required-check-admission` red→green |
| S4-inflight | Committed in-flight work and reported actual1.412s overshoot | Same safe commit/partial with actual clock and overshoot | Preserved control |
| S4-resume | Existing role-check completion retained | Fresh45s verification role started pending check despite historical300s, completed commands, preserved commit | Anti-deferral control; required checks not skipped |
| Independent verification | Not inferred from role report | Root reran build/test separately: both0; actual probe invocation count1→2 | Independent fixture verification observed |
| S4-progress / stall | Existing behavior | Actual budget/ledger/issue/verify CLI: new work commit resets count; third same-commit partial returns halt:true | Existing accounting preserved |

The300s values are supplied historical fixture data for admission decisions, not measurements of the fast invocation probe or a claimed speedup. Required checks remain mandatory; the fresh-role exception prevents endless deferral when duration exceeds a fresh budget. A first after-subject incorrectly attached a0s overrun to an early partial; that report is preserved as a failed ambiguity. Shared protocol now explicitly omits overrun before deadline; a fresh affected-case v2 replay confirmed partial/no invocation/no overrun. Original before build probe had a shell-quoting error, corrected and disclosed by the subject; it is not product red evidence.

`assess.py s4-before-output.json` fails admission as expected; `assess.py s4-effective-output.json` passes. The effective matrix explicitly combines unchanged original controls and the authoritative fresh v2 pending case. Native per-case clocks are separate from outer subject runtime budgets; no false fixture timing claim is made.

Existing `python3 -m unittest discover -s tools -p test_budget.py`:16 tests OK before and after. All five distributions canonical-rendered; whitespace clean. Budgets, production state schema/CLI, issue provenance and stall limit unchanged. T012 repository checks are recorded in the final verification section; independent orchestrator verification remains a separate required gate.
