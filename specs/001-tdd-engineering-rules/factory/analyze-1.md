# Specification Analysis Report — pass 1

**Feature**: `001-tdd-engineering-rules` — Engineering discipline for factory code-writing roles
**Artifacts**: `spec.md`, `plan.md`, `tasks.md`, `research.md`, `data-model.md`, `contracts/{engineering-reference,commit-body,plan-artifact}.md`, `quickstart.md`, `checklists/requirements.md`
**Constitution**: `.specify/memory/constitution.md` v1.0.0
**Mode**: read-only. No artifact was modified.

Note on this feature's own test tasks: `plan.md` ("Test seams") declares the whole change documentation/configuration-exempt from test-first with a stated reason (FR-025, FR-020a). Every task in `tasks.md` is therefore **excluded** from the seam-mapping / preceding-test-task check rather than reported at a lower severity. No finding below is raised for the absence of test tasks.

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| D1 | Constitution Alignment | CRITICAL | tasks.md Phase 2–6 (T003–T011), "Dependencies & Execution Order", "Notes"; plan.md Constitution Check III | Constitution III (NON-NEGOTIABLE) requires the rendered `dist/` to be committed **with** the source change. `tasks.md` defers all rendering to T011 in Phase 6, while the implementing role commits one commit per task (`core/roles/code-build.md`: "After each task ... commit code plus `tasks.md` together"). Commits for T003–T010 therefore each carry a `core/` change with a stale `dist/`, so `dist/` drifts from its source in the run's history. `tasks.md` itself is self-contradictory here: "Nothing in Phase 6 is parallel" and "US4 ... structurally last" versus Notes/"Within Each Story": "re-render and commit it with the source after any `core/` edit". | Fix in `tasks.md` (never in the constitution): make the render part of every `core/`-editing task — append to T003–T010 "then render every harness and commit the regenerated `dist/` in this task's commit" — and keep T011/T012 as the final full render plus drift verification. Consequently drop the `[P]` markers from T004/T005 and T007–T010 (a render writes all four harness trees, so parallel tasks would collide on `dist/`) and update "Parallel Opportunities" and the "Parallel Example" block accordingly. Alternatively state explicitly in `tasks.md` that T003–T010 plus T011 are committed as one logical commit, and say so as an override of code-build's per-task commit rule. |
| U1 | Underspecification / Coverage Gap | HIGH | spec.md FR-015b, SC-006a; tasks.md T009, T007; contracts/commit-body.md "Verification by spec-conformance"; core/skills/factory/references/findings.md "Reviewing" | FR-015b requires the spec-conformance reviewer to read **each implementation commit body** and check its `Red:` line. The reviewer's scope, defined in `findings.md` ("Scope: the change set, `cd <worktree> && git diff <base>...HEAD`"), is a squashed diff that contains no commit messages, and the reviewer's role file states no inputs beyond that. No task changes this: T007 edits `findings.md` only to require the `ENG-n` citation in `evidence`, and T009 edits `spec-conformance.md` to perform a check it has no input for. As planned, FR-015b and SC-006a are not implementable. ADR 0002 rests on the same wrong premise ("the reviewers already read the run's diff"). | Extend the scope in T007 (or add it to T009): `findings.md` "Reviewing" gains that a reviewer whose lens needs commit metadata reads `git log <base>..HEAD` (subjects and bodies) in addition to the diff; T009 states the exact command the spec-conformance reviewer runs to list the run's implementation commits and their bodies. Add the scope line to `plan.md`'s source-file list for `findings.md`. |
| U2 | Underspecification / Inconsistency | HIGH | spec.md FR-013a, FR-015b; contracts/commit-body.md ("Verification by spec-conformance", "Placement"); tasks.md T009 | The fixing role's red proofs have no verification path, and the stated one mis-fires. T009 and the contract's verification table scope the check to "each **implementation** commit"; a `factory(fix): <finding ids>` commit is not one, so FR-013a's one-`Red:`-line-per-behaviour-changing-fix is never checked. If fix commits were included, the table's "names a test no task in `tasks.md` maps to → Finding (unmatched)" rule raises a false blocking finding for every fix commit, because a fix's test maps to a verdict finding id, not to a task. | Decide and record the fix-commit rule in `contracts/commit-body.md` and in T009: state whether fix commits are checked, and if so match their `Red:` lines against the verdict's `confirmed_blocking` finding ids instead of `tasks.md`, so the "unmatched" rule cannot fire on a correct fix commit. Mirror the decision in FR-015b. |
| I1 | Inconsistency / Terminology drift | MEDIUM | spec.md US3 title/body, FR-015, FR-015a, SC-006 ("conventions reviewer") vs spec.md Clarifications Q4 and Assumptions ("code-standards reviewer"), plan.md, tasks.md T008, contracts/engineering-reference.md, CONTEXT.md "Role" | One concept, three names: "conventions reviewer", "code-standards reviewer", `code-standards`. `CONTEXT.md` fixes role names as the role's job name and the constitution's Writing Standards require one term for one concept everywhere. Same drift, more mildly, for "implementing role"/"code-writing role" vs `code-build` and "planning role"/"spec-building role" vs `spec-builder`. | Use `code-standards` (or consistently "the code-standards reviewer") throughout `spec.md`; keep the neutral role nouns only where they are defined once against the role file name, e.g. in Key Entities. |
| I2 | Inconsistency | MEDIUM | contracts/engineering-reference.md rule table, rows `ENG-2` and `ENG-3`; spec.md FR-012; contracts/commit-body.md "Placement" | `ENG-2` ("Record the red step in the task's commit body") is listed as yielding to "Nothing", but `commit-body.md` says an exempt task "carries no `Red:` line; the exemption lives in the plan, not in the commit", and FR-012/`ENG-5` permit exactly that. `ENG-1` correctly yields to "A declared test-first exemption in the plan"; `ENG-2` does not. `tasks.md`'s Tests header adds a third reading ("Every task names that exemption in place of a red proof"), which `commit-body.md` forbids in the commit. | Set `ENG-2`'s "Yields to" to "A declared test-first exemption in the plan" in `contracts/engineering-reference.md` (and so in T003's rule text), and reword the `tasks.md` Tests header to say the exemption is named in the task text and the plan, not in the commit body. |
| A1 | Ambiguity | MEDIUM | spec.md FR-014a, Edge Cases; contracts/engineering-reference.md `ENG-6`; CONTEXT.md "Reuse search"; tasks.md T004, T005 | "The repository's shared utility locations" is never defined, in any artifact, yet it bounds a rule the code-standards reviewer must enforce HIGH and blocking (FR-015, SC-006). Two agents will draw the boundary differently, so the same diff can pass one review and fail another. | Define it once, in T003's `ENG-6` text and in `CONTEXT.md`: e.g. the directories the repository's own conventions name as shared (helpers/utils/common/lib), plus any module the changed module already imports for helpers; and state that the search is `grep`-level by concept keyword. |
| A2 | Ambiguity | MEDIUM | spec.md FR-007, FR-013, FR-013a, SC-001; contracts/commit-body.md | "Behaviour-changing" is the trigger for the whole discipline (a red proof is required for a behaviour-changing task or fix) and is never defined. The only objective discriminator any artifact gives is the plan's documentation/configuration exemption, which is a different test. | Add one sentence to `ENG-1` (T003) or to `data-model.md` "Red proof": a unit of work is behaviour-changing when it changes what an entry point returns or does; a change confined to documentation, configuration or generated output is not. |
| I3 | Inconsistency | MEDIUM | spec.md FR-019, FR-020, SC-002 vs contracts/plan-artifact.md ("`tasks.md`: task ordering", "Analyze check") and tasks.md T006(b),(c) | The downstream contract is stricter than the requirement it implements, in two ways the HIGH blocking gate will act on: (a) FR-019/SC-002 say a test task "precedes"/"is preceded by", the contract and T006 say "**immediately** before" — a plan that groups test tasks ahead of a block of implementation tasks fails the gate without violating FR-019; (b) the contract's analyze table and T006(c) add a third blocking condition, "Names a seam the plan does not list", which FR-020 does not list. | Align the wording: amend FR-019/SC-002 to "immediately preceded" if that is the intent, and add the unlisted-seam condition to FR-020 (it is the artifact-time counterpart of FR-011a and worth keeping) — or relax the contract and T006 to match the spec. |
| I4 | Inconsistency | MEDIUM | plan.md "Test seams" vs contracts/plan-artifact.md "`plan.md`: the \"Test seams\" section" | This feature's own plan does not use the literal line shapes its contract prescribes: the contract requires `Exempt: <part> - <reason>` (and `Overridden: ENG-n - ...` / `Overridden: none`), while `plan.md` writes a bolded prose sentence plus a separate "**Reason**:" paragraph, and "**Overridden**: none." The analyze and spec-conformance checks being built are textual, so the form matters; as written, the feature fails its own contract. | Either add the canonical lines to `plan.md`'s "Test seams" section (`Exempt: whole change - Markdown instruction files only, no executable behaviour`, `Overridden: none`), keeping the prose as the reason, or state in `contracts/plan-artifact.md` that the line shapes bind plans produced **after** this change lands. The first is cheaper and makes this plan a worked example. |
| U3 | Underspecification | MEDIUM | spec.md FR-015b; tasks.md T009; core/skills/factory/references/findings.md "Reviewer report" | A red-proof finding is about a commit, but the reviewer report shape requires `file` and `line`. No artifact says what a commit-level finding puts there. | Have T007/T009 state it: `file` holds the commit sha (or the sha plus the task id) and `line` is omitted or `0` for a commit-level finding. |
| L1 | Inconsistency | LOW | CONTEXT.md "Red proof" vs spec.md FR-009a, Key Entities, contracts/commit-body.md | The glossary defines a red proof only as the line recording the test seen failing; it omits the second accepted form (`Red: not applicable - <existing test> already covers this`), which FR-009a makes equally valid. | Add the second form to the glossary entry so the one term covers both accepted lines. |
| L2 | Underspecification | LOW | quickstart.md step 3 | The command `grep -rl 'ENG-1\b' core/` cannot establish the stated expectation ("the only file under `core/` that states a rule"): it lists files mentioning the literal `ENG-1`, and nothing checks for rule text under other ids. | Point the check at what it means: list files under `core/` matching `ENG-[0-9]` and expect exactly `core/skills/factory/references/engineering.md`, with a note that role files may name ids only in citation instructions. |
| L3 | Coverage Gap | LOW | spec.md FR-025; tasks.md | FR-025 has no task: it is already satisfied by `plan.md`'s "Test seams" section, and its verification rides T001/T012/T016. This is correct but undocumented, so the next analyze pass will re-flag it. | Add a line to the `tasks.md` Tests header, or a row to a coverage note, recording that FR-025 is met by `plan.md` itself and verified by T001, T012 and T016. |
| L4 | Coverage Gap | LOW | spec.md SC-004a, FR-004a; tasks.md T007, T010; core/skills/factory/references/findings.md "Judge verdict" | The verdict's `advisory[]` entry shape has no `evidence` field, so an engineering finding downgraded to advisory loses its `ENG-n` citation, which SC-004a requires every engineering-rule finding to carry. | In T007, state that an advisory entry derived from an engineering finding keeps the `ENG-n` id (add `evidence`, or require the id in `summary`). |
| L5 | Duplication | LOW | tasks.md T001, T011, T012; core/roles/code-build.md step 3 | T001, T011 and T012 re-specify the build and generated-output check the implementing role already runs at the end of every stage. Harmless, but it is three tasks for an existing guarantee (constitution V). | Keep T011 (the render is a real deliverable) and T012 (it adds the per-harness `diff -q`); fold T001's baseline into T011's description, or keep it and say explicitly that it exists only to attribute a later failure. |

No other finding reached the reporting threshold; no overflow.

## Coverage Summary

All 35 functional requirements (FR-001..FR-025 including the `a`/`b`/`c` variants) map to at least one task. Grouped:

| Requirement key | Has task? | Task IDs | Notes |
|---|---|---|---|
| FR-001, FR-002, FR-003, FR-006 | Yes | T003 | The one shared, self-contained reference and its topic coverage |
| FR-004 | Yes | T004, T005, T006, T008, T009, T010, T013 | Six roles reference the file; T013 greps that it is exactly those six |
| FR-004a | Yes | T003, T007, T008, T009, T010 | Ids defined once; citation required in `evidence` (see U3, L4) |
| FR-005 | Yes | T003 (`ENG-11`), T006(a) | Override line in the plan |
| FR-006a | Yes | T006(e), T013 | `.specify/` untouched is the check |
| FR-007, FR-008, FR-010, FR-011, FR-012 | Yes | T004 | Red-green-refactor, one commit, plan's seams only |
| FR-009, FR-009a | Yes | T004 | Both accepted `Red:` forms |
| FR-011a | Yes | T004, T005 | Stop-and-report rides the existing failure policy (verified: `failed` → retry once → halt) |
| FR-013, FR-013a | Yes | T005 | Verification path missing — see U2 |
| FR-014, FR-014a | Yes | T004, T005 | Bound is ambiguous — see A1 |
| FR-015, FR-015a | Yes | T008 | HIGH and blocking for duplication and untested behaviour |
| FR-015b | Yes (not implementable as written) | T009 | See U1 |
| FR-015c | Yes | T010, T013 | Judge references the rules; rates by id |
| FR-016, FR-017, FR-018, FR-019, FR-020, FR-020a, FR-021 | Yes | T006 | See I3 for the FR-020/contract mismatch |
| FR-022 | Yes | T002, T013 | `DESIGN.md` leads; task order enforces it |
| FR-023 | Yes | T011, T012 | See D1 for the commit-level timing |
| FR-024 | Yes | T003, T004, T006, T008, T014 | Writing Standards re-read |
| FR-025 | By artifact | (plan.md) + T001, T012, T016 | See L3 |

| Success criterion | Has task? | Task IDs | Notes |
|---|---|---|---|
| SC-001 | Deferred | T016 | Observable only on a real run, per the DESIGN.md validation plan |
| SC-002, SC-003 | Yes | T006 | |
| SC-004 | Yes | T003, T013, T014 | |
| SC-004a | Yes | T003, T007, T013 | See L4 |
| SC-005 | Yes | T001, T011, T012 | |
| SC-006 | Deferred | T016 | Trial review needs a diff |
| SC-006a | Deferred | T016 | Blocked by U1 until the reviewer can read commit bodies |
| SC-007 | Deferred | T016 | |

No post-launch or business-KPI criteria were counted.

## Constitution Alignment Issues

- **III. Generated Dist (NON-NEGOTIABLE)** — violated by the task ordering: finding **D1**. Fix in `tasks.md`, not in the constitution.
- I (Design First): satisfied — T002 precedes T003 and the dependency section states it (FR-022).
- II (Harness-Neutral Core): satisfied — T003/T014 forbid naming a harness tool, path or command; verified that `tools/render.py` already copies `core/skills/factory/` into `dist/<harness>/skill/`, so no adapter or renderer change is needed (research D3 confirmed against the repository).
- IV (Stateless Agents): satisfied — every rule, seam and proof is read from disk or the commit history in a single spawn.
- V (Simplicity and Reuse): satisfied — one new file with a stated reason in the Constitution Check; L5 is a mild redundancy only.
- Writing Standards (one term per concept): weakened by **I1**.
- Development Workflow: satisfied, with D1's timing caveat.

## Unmapped Tasks

None. T013 (inspection), T014 (Writing Standards), T015 (untouched surface) and T016 (deferred end-to-end validation) each map to a stated requirement, success criterion, contract or constitution principle.

## Metrics

- Total requirements: 44 (35 FR + 9 SC)
- Total tasks: 16 (T001–T016)
- Coverage: 35/35 FR with >= 1 task (100%; FR-025 met by `plan.md` with verification tasks), 9/9 SC addressed (4 deliberately deferred to the next real run)
- Ambiguity count: 2 (A1, A2)
- Duplication count: 1 (L5)
- Inconsistency count: 4 (I1–I4)
- Underspecification count: 3 (U1–U3)
- Critical issues: 1 (D1)
- By severity: CRITICAL 1, HIGH 2, MEDIUM 7, LOW 5 (15 total)

## Next Actions

1. **Resolve D1 before implement** — it is a NON-NEGOTIABLE constitution violation and is fixed entirely inside `tasks.md` (render per `core/`-editing task, drop the now-invalid `[P]` markers).
2. **Resolve U1 and U2** — without them FR-015b, FR-013a and SC-006a ship as unenforceable text, and U2 would generate false blocking findings on every correct fix commit.
3. Fold I1–I4, A1, A2 and U3 into the artifacts: they are wording and definition edits to `spec.md`, `plan.md`, `tasks.md` and `contracts/`, with no user decision needed.
4. L1–L5 are low-cost improvements; L3 in particular stops the next pass re-flagging FR-025.
5. No finding requires a user decision, so none is returned as `pending_clarify`. Remediation can proceed directly on the artifacts.
