# Specification Analysis Report — pass 4

Feature: `003-zcode-harness` (ZCode Harness Adapter)
Artifacts: `spec.md`, `plan.md`, `tasks.md`, `research.md`, `data-model.md`, `quickstart.md`,
`checklists/requirements.md`, `CONTEXT.md`, `docs/adr/0005-the-rendered-distribution-is-tracked-in-git.md`
Constitution: `.specify/memory/constitution.md` v1.0.0
Read-only: no artifact was modified by this pass. (A canonical render was run and re-run to verify C1/C2;
`dist/` is left at the canonical render and `git status` is clean.)

## Status of analyze-3 findings

| ID | Severity (pass 3) | Status | Evidence |
|----|---|---|---|
| C1 | HIGH (blocking) | **resolved (verified by execution)** | `FACTORY_HOME=/nonexistent` replaces `-u FACTORY_HOME` in plan.md (Constraints, Seams 3/4), tasks.md (T001, T007, T011, T017, Notes), quickstart.md step 2 `$CANON`, and `factory/state.json` `commands.build`. Prose follows in FR-018, SC-003, ADR 0005 and quickstart, each stating *why* unsetting is insufficient. Reproduced the fix: with `$SCRATCH/fh/config.json` = `{"models":{"claude-code":{"deep":"opus-test"}}}`, the canonical wrapper renders `model: anthropic/claude-opus-5-5` (the adapter's own value) and no file contains `opus-test`; the same render with `FACTORY_HOME=$SCRATCH/fh` emits `opus-test` into `factory-spec-builder.md` and `factory-review-judge.md`. `tools/render.py:40-42` confirms the mechanism (`config.exists()` is false for `/nonexistent/config.json`). |
| C2 | HIGH (blocking) | **resolved (verified by execution)** | `-u COPILOT_HOME` is present in all eight occurrences of the wrapper (plan Constraints + Seam 4; tasks T001, T007, T011, T017, Notes; quickstart `$CANON`) and in `state.json` `commands.build`; the wrapper string is character-identical in every one. plan.md states why, quickstart's "Without `$CANON`" paragraph lists it, FR-018 says "all of them, including the one the Copilot adapter reads". Reproduced the sensitivity it guards against: `COPILOT_HOME=/tmp/zzz python3 tools/render.py copilot` rewrites the skill path in `dist/copilot/agents/factory-*.agent.md`; the canonical render restores `~/.copilot/...`. |
| C3 | LOW | **not resolved — regression** | The citation was changed from `README.md:72` to `README.md:71`, but `grep -n "SpecKit set up" README.md` returns **72**; line 71 is the `Skills:` bullet. The pass-3 finding was itself wrong, so the remediation replaced a correct number with an incorrect one. The added descriptor ("the \"SpecKit set up\" bullet") does make the reference recoverable. Reported below as D1. |
| C4 | LOW | **resolved** | ADR 0005's chosen option now ends with the sentence tying the gate to FR-018's canonical render environment and the `git checkout -- dist/` recovery. |

Two blocking findings closed and verified against the repository; one low finding re-opens with the
opposite off-by-one. **No blocking finding remains.**

## Findings

| ID | Category | Severity | Blocking | Location(s) | Summary | Recommendation |
|----|----------|----------|----------|-------------|---------|----------------|
| D1 | Style / traceability | LOW | no | tasks.md T012 | The SpecKit requirement bullet is `README.md:72`, not `:71` (verified: 69 `An agent harness…`, 70 `In the target repo…`, 71 `Skills: …`, 72 `SpecKit set up for your harness: specify init --here --ai <claude\|opencode\|codex\|copilot> …`). The citation has now been wrong in both directions across two passes. | Drop the line number entirely: cite it as the `"SpecKit set up for your harness"` bullet in `README.md`. The quoted bullet text is already in T012, so nothing is lost and the reference cannot drift again. |
| D2 | Inconsistency / instruction cannot be followed literally | MEDIUM | no | tasks.md T013; plan.md "Constitution Check" → I. Design First; research.md R4; `DESIGN.md:69` | T013 says to "replace the Claude-shaped parenthetical `(--ai <harness>, plus --ai-skills outside Claude Code …)` **with** `specify init --here <harness.speckit_init>`", and the plan's Constitution I bullet says the line "is generalised to `specify init --here <harness.speckit_init>`". But `DESIGN.md:69` **already reads** `offer to run `specify init --here <harness.speckit_init>` (`--ai <harness>`, plus `--ai-skills` outside Claude Code so SpecKit's commands land as skills)`. The generalised command is present; the only Claude-shaped text left is the parenthetical gloss. Followed literally, T013 produces a duplicated command (`specify init --here <harness.speckit_init> (specify init --here <harness.speckit_init>)`), and the plan's Constitution I justification cites a change that is already true rather than the edit the feature actually needs. Documentation-only and obvious at implementation time, so not blocking. | Reword T013 to: "delete the Claude-shaped parenthetical at `DESIGN.md:69`, replacing it with a neutral gloss — each adapter states its own `speckit_init` arguments (ZCode's: `--integration zcode --integration-options=\"--skills\"`)". Align the plan's Constitution I bullet and research R4's note to say the *parenthetical* is what changes. |
| D3 | Style / consistency | LOW | no | tasks.md T012; README.md:7-12 | The row T012 dictates is written without code formatting — `\| ZCode \| ./install.sh --harness zcode \| /factory <feature> \| ~/.zcode/agents/factory-*.md \|` — while every existing row in the harness table wraps the command and path in backticks (`` `./install.sh --harness codex` ``). Taken literally the new row renders as plain text beside four code-formatted rows, and `<feature>` inside a Markdown table without backticks is at risk of being read as an HTML tag. | Add backticks in T012's quoted row, matching `README.md:9-12`. |

## Coverage Summary

| Requirement key | Has task? | Task IDs | Notes |
|---|---|---|---|
| FR-001 | yes | T004, T008 | both adapter files created together in Phase 3 |
| FR-002 | yes | T009 | SPAWN / SPAWN_PARALLEL rows |
| FR-003 | yes | T004 | home/env/default, skill_dir, agent_dir |
| FR-004 | yes | T004, T005, T006 | Seam 3; empty `models` + canonical `FACTORY_HOME` keep the key set exact (C1 closed) |
| FR-005 | yes | T004 | access read/write tool lists |
| FR-006 | yes | T004, T010 | empty `models`, config override note |
| FR-007 | yes | T010 | `$ARGUMENTS` note |
| FR-008 | yes | T009 | ASK row |
| FR-009 | yes | T009 | NOTIFY no-op |
| FR-010 | yes | T009 | four verified roots |
| FR-011 | yes | T008 | `speckit_init`; DESIGN.md line by T013 — wording defect D2 |
| FR-012 | yes | T008 | recognition line carries the checkable signal |
| FR-013 | yes | T010 | no Skill-tool invocation of speckit/grilling |
| FR-014 | yes | T010 | ledger `reported: null` |
| FR-015 | yes | T011 | canonical render of every harness |
| FR-016 | yes | T012, T013, T014 | citation D1 and row style D3 in T012; D2 in T013; `CONTEXT.md:24` already names ZCode, as T014 expects |
| FR-017 | yes | T016 | `git diff --name-only` over `core/` |
| FR-018 | yes | T001, T011, T017 | canonical environment now correct and reproduced; `.gitignore:1` is `/dist/` and `git ls-files dist/` is 0, so T001's two confirmations are meaningful preconditions |
| SC-001 | yes | T018 | manual install + start |
| SC-002 | yes | T006, T018 | `core/roles/` holds 9 files, matching the expected agent count |
| SC-003 | yes | T011, T017 | "holds on any contributor's machine" is now true under the corrected wrapper |
| SC-004 | yes | T005, T006 | Seam 3 |
| SC-005 | yes | T018 (a)(b), quickstart 5 | both directions |
| SC-006 | yes | T007, T011, T017 | same correction |

Coverage: 18/18 functional requirements have ≥1 task (100%); 6/6 success criteria have a verification step,
none conditional any longer.

## Constitution Alignment Issues

None. I (Design First) is met by the `DESIGN.md` edit in T013 — D2 is a defect in how that edit is worded,
not an omission of it. II is met (no `core/` file changes; T016 verifies). III is met and now checkable
(FR-018, T001/T011, ADR 0005). IV and V unaffected.

## Test-seam check (factory override)

- Implementation tasks with a failing-test task immediately before them: T003 → T004 (Seams 1-2) ✓;
  T005 → T006 ✓. T008 follows T004 inside the same commit and is plan-exempt.
- Plan-exempt tasks (excluded from this check): T001, T006, T008, T009, T010, T011, T012, T013, T014.
- Every exemption quoted by a task appears verbatim in the plan's exemption list ✓.
- Every seam named by a task (1-4) is listed in the plan ✓; Seam 4 can genuinely fail once `/dist/` leaves
  `.gitignore`, and the wrapper it runs under is now correct.
- Test runner: the repository has one (render loop + `git diff --exit-code -- dist/`); no runner-setup task
  is added, and tasks.md states this ✓.
- `Overridden: none` is stated in the plan ✓.

## ENG-10 / budget checks

- New files, abstractions and dependencies: the plan states a reason for `adapters/zcode/adapter.json`,
  `adapters/zcode/harness.md`, `dist/**` and `docs/adr/0005-…md`, with `abstraction - none` and
  `dependency - none`. No ENG-10 finding.
- Word budgets (`wc -w`): `spec.md` 2508/3000, `plan.md` 1861/2000, `tasks.md` 2493/2500. All within
  budget; no finding. `tasks.md` has 7 words of headroom — D1 (dropping `:71`) and D3 (backticks) are
  neutral-to-negative in word count, and D2's rewording should be made inside T013's existing sentence.

## Unmapped tasks

None. T002, T016, T017 and T018 are baseline and verification tasks tied to the seams and success criteria
above.

## Metrics

- Total requirements: 18 FR + 6 SC
- Total tasks: 17 (T001-T018, T015 removed)
- Coverage: 100% FR with a task; 0 criteria now carry a caveat
- Ambiguity count: 0 unresolved placeholders
- Duplication count: 0
- CRITICAL: 0 · HIGH: 0 · MEDIUM: 1 · LOW: 2
- Pass-3 findings: 3 of 4 resolved (C1 and C2 verified by execution); C3 regressed and is re-reported as D1

## Next actions

Nothing blocks implementation. The three remaining findings are one-line edits inside `tasks.md`
(plus two sentences in `plan.md`/`research.md` for D2) and need no user decision: drop the `README.md`
line number (D1), reword T013 so it deletes the Claude-shaped parenthetical rather than re-adding the
command already on `DESIGN.md:69` (D2), and backtick the README table row (D3).
