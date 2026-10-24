# Specification Analysis Report — pass 3

Feature: `003-zcode-harness` (ZCode Harness Adapter)
Artifacts: `spec.md`, `plan.md`, `tasks.md`, `research.md`, `data-model.md`, `quickstart.md`, `CONTEXT.md`,
`docs/adr/0005-the-rendered-distribution-is-tracked-in-git.md`
Constitution: `.specify/memory/constitution.md` v1.0.0
Read-only: no artifact was modified by this pass.

## Status of analyze-2 findings

| ID | Severity (pass 2) | Status | Evidence |
|----|---|---|---|
| B1 | HIGH (blocking) | **resolved** | T008 now sits in Phase 3 immediately after T004; T004 states it turns T003 green for *Seam 1 only* and names the `FileNotFoundError`; Phase 3 Goal/Independent Test cover both adapter files; dependency line reads `T003 → T004 → T008 → T005 → T006`; Notes require one commit for T004+T008; plan Seam 2 explains `known()`/`render()` and "no ordered step may leave the folder half-built". Phase 4 carries the pointer note. |
| B2 | HIGH (blocking) | **resolved** | T008 quotes data-model §2 verbatim, checkable signal included ("`ZCODE_HOME` is set or `~/.zcode` exists"), with the FR-012 / clarification-8 note. |
| B3 | HIGH (blocking) | **partially resolved** | The canonical render environment is now written into FR-018, SC-003, SC-006, plan Constraints + Testing + Seams 3/4, T001, T007, T011, T017, T018 and quickstart steps 2 and 4, with the `git checkout -- dist/` recovery. But the canonicalisation itself is wrong in two concrete ways (C1, C2 below), so the gate is still not deterministic across contributors. The *structure* of the fix is right; the *variable list and the `FACTORY_HOME` treatment* are not. |
| M1 | MEDIUM | **resolved** | T012 states ZCode's setup as its own sentence, explicitly not as another `--ai` value, and carries research R4's out-of-scope note (line reference is stale — C3). |
| M2 | MEDIUM | **resolved** | T003 now reads "run the Seam 1 and Seam 2 commands already written in quickstart.md steps 2-3 and record their failure output". |
| L1 | LOW | **resolved** | plan.md's ENG-10 section carries the note that ADR 0005 and the `CONTEXT.md` line already exist on this branch (T001 implements the ADR, T014 verifies the line). |

Five of six pass-2 findings are fully resolved; B3's remediation is structurally complete but factually
wrong in its command, which this pass reports as two new blocking findings rather than as a reopened B3.

## Findings

| ID | Category | Severity | Blocking | Location(s) | Summary | Recommendation |
|----|----------|----------|----------|-------------|---------|----------------|
| C1 | Underspecification / gate cannot hold | HIGH | yes | spec.md FR-018 and SC-003; plan.md "Constraints" → Canonical render environment, Seams 3 and 4; tasks.md T001, T007, T011, T017, Notes; quickstart.md step 2 (`$CANON`); state.json `commands.build` | **Unsetting `FACTORY_HOME` does not disable model overrides.** `tools/render.py:40` reads `os.environ.get("FACTORY_HOME", "~/.factory")`, so with the variable unset the renderer falls back to `~/.factory/config.json` and still merges `models.<harness>` into the frontmatter. Reproduced: with `~/.factory/config.json` = `{"models": {"claude-code": {"deep": "opus-test"}}}` and the artifacts' exact wrapper `env -u CLAUDE_HOME -u CODEX_HOME -u ZCODE_HOME -u XDG_CONFIG_HOME -u FACTORY_HOME python3 tools/render.py claude-code`, the render still emits `model: opus-test` in `dist/claude-code/agents/factory-{review-judge,spec-builder}.md`. The repository the factory runs in already has a `~/.factory/` directory, so this is the common case, not an edge one. Consequences: SC-003/SC-006's "holds on any contributor's machine" is false; T001's own confirmation step ("repeating the same `env -u …` render leaves `git diff --exit-code -- dist/` clean even with … a model override set") fails as written; and Seam 3's exact `{name, description, tools}` key-set assertion over `dist/zcode/agents/*.md` breaks for any contributor with a `models.zcode` override — the very risk the plan's Seam 3 paragraph claims the canonical environment removes. | Canonicalise by **pointing** `FACTORY_HOME` at a path that has no `config.json`, not by unsetting it: replace `-u FACTORY_HOME` with `FACTORY_HOME=/nonexistent` (or an empty scratch dir) in FR-018's wording ("the factory configuration-home variable unset" → "pointed at a location with no configuration file"), in the plan's Canonical render environment paragraph and Seams 3/4, in T001/T007/T011/T017 and the Notes bullet, and in quickstart step 2's `$CANON`. The orchestrator's stored `commands.build` needs the same correction. |
| C2 | Inconsistency / incomplete canonical environment | HIGH | yes | plan.md "Constraints" → Canonical render environment, Seam 4; tasks.md T001, T007, T011, T017, Notes; quickstart.md step 2; state.json `commands.build`; `adapters/copilot/adapter.json:3` | **`COPILOT_HOME` is missing from the `env -u …` list.** The Copilot adapter resolves `{home}` from `COPILOT_HOME` (default `~/.copilot`), so it is one of the "every harness home variable" FR-018's prose requires, but every concrete command in the plan, tasks, quickstart and the stored build command lists only `CLAUDE_HOME`, `CODEX_HOME`, `ZCODE_HOME`, `XDG_CONFIG_HOME`, `FACTORY_HOME`. Reproduced: `COPILOT_HOME=/tmp/zzz python3 tools/render.py copilot` rewrites the skill path in every `dist/copilot/agents/factory-*.agent.md` body (`/tmp/zzz/skills/factory/references/...`). A contributor with `COPILOT_HOME` set therefore commits a non-canonical `dist/copilot/` tree or sees the Seam 4 gate fail spuriously — the exact failure mode B3 was raised to close. The spec prose is correct; only the operational commands are wrong, which is what contributors actually run. | Add `-u COPILOT_HOME` to the canonical wrapper in plan.md (Constraints, Seam 4), tasks.md (T001, T007, T011, T017, Notes bullet), quickstart.md step 2's `$CANON`, and the stored `commands.build`. Fix together with C1 so the wrapper is written once in the plan and quoted identically everywhere: `env -u CLAUDE_HOME -u CODEX_HOME -u COPILOT_HOME -u ZCODE_HOME -u XDG_CONFIG_HOME FACTORY_HOME=/nonexistent`. |
| C3 | Style / traceability | LOW | no | tasks.md T012; README.md:71 | T012 cites `README.md:72` for the SpecKit requirement line, but that line (`SpecKit set up for your harness: specify init --here --ai <claude\|opencode\|codex\|copilot> …`) is line **71**; line 72 is the `impeccable` bullet. Carried over from analyze-2 M1's own citation. Harmless to a reader who greps, misleading to one who jumps to the line. | Change the citation to `README.md:71`, or drop the line number and quote the line's opening words instead, so it cannot drift again. |
| C4 | Inconsistency (documentation accuracy) | LOW | no | `docs/adr/0005-the-rendered-distribution-is-tracked-in-git.md`; spec.md FR-018 | ADR 0005 states that tracking `dist/` makes `git diff --exit-code -- dist/` "a gate that can actually fail" but says nothing about the render being environment-dependent, which FR-018 now makes a condition of the decision working at all. A reader of the ADR alone would conclude the gate is unconditional. | Add one sentence to ADR 0005's chosen option recording that the tracked distribution is the one produced in the canonical render environment (FR-018), and that non-canonical local renders must be reverted. |

## Coverage Summary

| Requirement key | Has task? | Task IDs | Notes |
|---|---|---|---|
| FR-001 | yes | T004, T008 | both adapter files now created together in Phase 3 (B1 closed) |
| FR-002 | yes | T009 | SPAWN / SPAWN_PARALLEL rows |
| FR-003 | yes | T004 | home/env/default, skill_dir, agent_dir |
| FR-004 | yes | T004, T005, T006 | Seam 3; still exposed to a `models.zcode` override — C1 |
| FR-005 | yes | T004 | access read/write tool lists |
| FR-006 | yes | T004, T010 | empty `models`, config override note |
| FR-007 | yes | T010 | `$ARGUMENTS` note |
| FR-008 | yes | T009 | ASK row |
| FR-009 | yes | T009 | NOTIFY no-op |
| FR-010 | yes | T009 | four verified roots |
| FR-011 | yes | T008 | `speckit_init`; DESIGN.md generalised by T013 |
| FR-012 | yes | T008 | recognition line now carries the checkable signal (B2 closed) |
| FR-013 | yes | T010 | no Skill-tool invocation of speckit/grilling |
| FR-014 | yes | T010 | ledger `reported: null` |
| FR-015 | yes | T011 | canonical render of every harness |
| FR-016 | yes | T012, T013, T014 | README sentence fixed (M1 closed); stale line number — C3 |
| FR-017 | yes | T016 | `git diff --name-only` over `core/` |
| FR-018 | weak | T001, T011, T017 | tracking works; the canonical environment as written is not canonical — C1, C2 |
| SC-001 | yes | T018 | manual install + start |
| SC-002 | yes | T006, T018 | 9 roles confirmed in `core/roles/` |
| SC-003 | weak | T011, T017 | "holds on any contributor's machine" is false under C1/C2 |
| SC-004 | yes | T005, T006 | Seam 3 |
| SC-005 | yes | T018 (a)(b), quickstart 5 | both directions |
| SC-006 | weak | T007, T011, T017 | same two defects |

Coverage: 18/18 functional requirements have ≥1 task (100%); 6/6 success criteria have a step, 3 of them
(FR-018, SC-003, SC-006) conditional on C1 and C2.

## Constitution Alignment Issues

None. Constitution III (Generated Dist) is satisfied in principle by FR-018 and T001/T011; C1 and C2 are
defects in the *mechanism* that proves it, not violations of the principle, so neither is CRITICAL.

## Test-seam check (factory override)

- Implementation tasks with a failing-test task immediately before them: T004 (after T003, Seams 1-2) ✓.
  T008 follows T004 inside the same commit and is plan-exempt; T005 precedes T006 ✓.
- Plan-exempt tasks (excluded from this check): T001, T006, T008, T009, T010, T011, T012, T013, T014.
- Every exemption quoted by a task appears verbatim in the plan's exemption list ✓.
- Seams named by tasks are all listed in the plan (Seams 1-4) ✓; Seam 4 can fail, subject to C1/C2.
- Test runner: the repository has one; no runner-setup task is added ✓.
- `Overridden: none` is stated in the plan ✓.

## ENG-10 / budget checks

- New files, abstractions and dependencies: the plan states a reason for `adapters/zcode/adapter.json`,
  `adapters/zcode/harness.md`, `dist/**` and `docs/adr/0005-...md`, and `none` for abstraction and
  dependency. No ENG-10 finding.
- Word budgets (`wc -w`): `spec.md` 2451/3000, `plan.md` 1767/2000, `tasks.md` 2499/2500. All within
  budget; no finding. (`tasks.md` has 1 word of headroom — the C1/C2 edits are substitutions inside the
  existing `env -u …` strings plus one added flag, so they fit, but any added prose must be offset.)

## Unmapped tasks

None. T002, T016, T017 and T018 are baseline/verification tasks tied to the seams and success criteria
above.

## Metrics

- Total requirements: 18 FR + 6 SC
- Total tasks: 17 (T001-T018, T015 removed)
- Coverage: 100% FR with a task; 3 criteria carry a caveat (C1, C2)
- Ambiguity count: 0 unresolved placeholders
- Duplication count: 0
- CRITICAL: 0 · HIGH: 2 · MEDIUM: 0 · LOW: 2
- Pass-2 findings resolved: 5 of 6 fully, 1 (B3) structurally with two factual defects reported as C1/C2

## Next actions

Two HIGH findings block implementation; neither is a constitution violation. Both are mechanical in-place
string edits with no user decision needed: define the canonical wrapper once in `plan.md` as
`env -u CLAUDE_HOME -u CODEX_HOME -u COPILOT_HOME -u ZCODE_HOME -u XDG_CONFIG_HOME FACTORY_HOME=/nonexistent`
and quote it identically in `tasks.md` (T001, T007, T011, T017, Notes) and `quickstart.md` step 2, and
reword FR-018's "the factory configuration-home variable unset" to "pointed at a location holding no
configuration file". The orchestrator's stored `commands.build` in `factory/state.json` carries the same
two defects and should be corrected with them. C3 and C4 are one-line documentation fixes.
