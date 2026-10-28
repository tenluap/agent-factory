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
| S2 matrix | pending | pending | pending | pending | pending |
| S3 matrix | pending | pending | pending | pending | pending |
| S4 matrix | pending | pending | pending | pending | pending |

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

Focused command: `python3 -m unittest discover -s tools -p test_render_models.py`. Before: 19 tests, three known model-policy failures. After: 19 tests, **OK**, including exact shipped selections, installed override behavior, canonical-config isolation and inherited-model reporting. All five harnesses rendered; adapter JSON mappings unchanged. Full-suite/final clean-dist checks remain pending T012 and independent orchestrator verification.


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

All five harnesses canonical-rendered after the source changes. `python3 -m unittest discover -s tools -p 'test_render*.py'` passed **27 tests**; `git diff --check` passed. The configured budgets, runtime state schema, model mappings and mandatory final checks are unchanged. S3/S4 and T012 full verification remain pending.
