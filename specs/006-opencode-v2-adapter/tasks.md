# Tasks: OpenCode V2 adapter

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md), [contract](contracts/opencode.md), [validation guide](quickstart.md).

**Scope**: Native V2 adoption, with supported V1 compatibility retained. No core-flow changes, dependencies, installation migration, user configuration edits, or new model calls.

**Tests**: Mandatory through the confirmed `render_agent()`, `agent_fields()`, and `render()` seams. Python standard-library unittest needs no installation or runner setup; adding the test module is T003. Each behavior task has its test task immediately before it. Commit each test/implementation pair together, never a separate red commit.

## Phase 1: Setup — design first

- [x] T001 Update `DESIGN.md` with the native OpenCode V2 subagent/shell and ordered permission contract, unchanged role access and models, supported V1 compatibility, and verification limits. Exempt: documentation only. Commit this task separately before changing adapter behavior; include the already prepared feature planning artifacts as appropriate.

## Phase 2: Foundational — preserve the baseline

- [x] T002 Inspect `specs/006-opencode-v2-adapter/factory/state.json` and its `prior_work.handoff`; capture canonically rendered baseline `dist/` bytes outside tracked output, following `specs/006-opencode-v2-adapter/quickstart.md`, and retain the location for T006. Inspect saved tests/source changes without applying production changes. Exempt: validation/planning artifacts only; no behavior change. Preserve the invoking checkout, all its edits and Codex setup. The handoff patch contains historical planning and generated files: do not import its plan, `dist/`, or apply it wholesale.

**Checkpoint**: Design contract committed; baseline available; work remains confined to this worktree. Existing stdlib unittest is runnable. Do not proceed if the test command cannot run.

## Phase 3: User Story 1 — native V2 roles (P1, MVP)

**Goal**: All nine roles use native ordered permissions; instructions retain named dispatch, model behavior and installation locations.

**Independent test**: Render OpenCode; inspect every role and instruction against `contracts/opencode.md`. Confirm read roles deny edit then subagent; write roles deny subagent only.

- [x] T003 [US1] Adopt the six saved cases into `tools/test_render.py` without importing production changes; exercise `render_agent()`, `agent_fields()`, and `render()`. Run `python3 -m unittest discover -s tools -p 'test_*.py'` against the baseline and observe actual failures, including `RenderAgentTests.test_ordered_permission_rules_are_valid_yaml_sequences` and native-role/distribution failures. Preserve precise failing test names and diagnostics for T004; unchanged legacy Markdown, TOML output and structured-field rejection should pass. Prior red claims are not fresh evidence. Stop if the command cannot run.
- [x] T004 [US1] Extend the existing serializer in `tools/render.py` minimally for ordered lists of JSON flow mappings; first search that module and imported helpers for reusable serialization logic. Update `adapters/opencode/adapter.json` and `adapters/opencode/harness.md` to native subagent/shell instructions and ordered permissions, retaining all nine roles, action/resource/effect order, wildcard deny rules, paths, model defaults/overrides and foreground named-role dispatch. Preserve scalar, flat-map, string-list and TOML behavior. Configuration/instruction portions are plan-exempt; verify their consumed output through `agent_fields()` and `render()`. Regenerate every harness into `dist/` canonically per `quickstart.md`; generated portions are plan-exempt and must not be hand-edited or imported. Rerun T003 green. Commit T003+T004 together, source and generated output included, with `Red: RenderAgentTests.test_ordered_permission_rules_are_valid_yaml_sequences failed as expected` only after observing that failure.

**Checkpoint**: Native roles and instructions pass the saved suite. Write roles retain edit intent; no role gains child-agent dispatch. Other harness behavior remains subject to the next phase's full byte comparison.

## Phase 4: User Story 2 — preserve other harnesses (P2)

**Goal**: Every distribution remains reproducible; native output outside OpenCode and operator model behavior remain stable.

**Independent test**: Compare canonical full distributions against T002; only OpenCode agents and every bundle's OpenCode reference may differ.

- [x] T005 [US2] Extend `tools/test_render.py` through confirmed `render()` with isolated temporary FACTORY_HOME configurations: test a nonempty model override appears in generated OpenCode role fields, and empty model values omit model fields for session inheritance. Restore environment/module patches and remove temporary files on success/failure; keep operator config untouched. Verify complete role counts, copied references, unchanged legacy formats and tier mapping with the saved cases. Existing model logic should remain unchanged; do not add production logic to satisfy already-correct behavior. This is regression coverage of unchanged behavior, not another behavior implementation task; run and commit the tests green without manufacturing red evidence.
- [ ] T006 [US2] Run canonical all-harness generation using absent override config and default adapter homes per `specs/006-opencode-v2-adapter/quickstart.md`; compare final `dist/` bytes with T002, recording results in that guide. Require byte-identical native agents and unrelated skill contents for every non-OpenCode harness; their only allowed change is `skill/references/harness/opencode.md`. Confirm all five skill bundles carry the maintained OpenCode reference. Exempt: generated output and verification documentation only. Report unexpected differences rather than accepting or hiding them.

**Checkpoint**: All nine OpenCode roles, five distributions and normal override/inheritance behavior are verified without local configuration contamination.

## Phase 5: User Story 3 — accurate evidence (P2)

**Goal**: Operators understand intended V1 compatibility, native V2 adoption and the limits of verification.

**Independent test**: Cross-check the evidence record with actual commands/results; no unexecuted check is reported as passed.

- [ ] T007 [US3] Update `specs/006-opencode-v2-adapter/quickstart.md` with performed checks and separate static, runtime discovery, model-backed dispatch and runtime permission-enforcement outcomes. Exempt: documentation only. Identify prior OpenCode v2.1.4 discovery as historical evidence: nine global symlinked roles, expected loaded policy and factory skill discovery; it proves loading only. Keep dispatch/enforcement unverified and make no new model calls. If an optional fresh discovery is performed, bound registration waits and record version/errors; any observed permission or dispatch mismatch blocks delivery without weakening rules. Describe supported V1 compatibility and existing installer/rollback steps accurately.

## Phase 6: Polish and constitution gate

- [ ] T008 Run `python3 -m unittest discover -s tools -p 'test_*.py'`, `bash -n install.sh`, `git diff --check`, and changed Markdown local-link checks; retain outcomes in `specs/006-opencode-v2-adapter/quickstart.md`. Exempt: verification/documentation only. After source plus generated output are committed, rerender all harnesses canonically and require `test -z "$(git status --porcelain -- dist/)"`; this must detect untracked additions as well as tracked drift. Confirm repeated generation byte parity and that the invoking checkout remains intact. Fix or report failures; a bare distribution diff is not the constitution gate.

## Dependencies and execution order

T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008.

T003 immediately precedes the only behavior implementation task, T004; keep both in one commit. T001 is a separate earlier documentation commit. Each adapter source change must have canonically regenerated `dist/` committed with it. T005 adds regression tests only and requires no invented implementation. All remaining tasks carry the plan's documentation/configuration/generated exemptions.

User story dependencies: US1 establishes native source/output; US2 verifies compatibility against the untouched baseline; US3 describes the resulting evidence. Each has its independent check above. The MVP is US1 after setup/foundation, but release requires all three stories and T008.

## Parallel opportunities

No implementation tasks are marked parallel: tests share `tools/test_render.py`, and all generation shares `dist/`. Within US1, instruction inspection may run alongside unittest after edits settle; within US2, comparisons of the four unaffected native agent directories may run concurrently after generation; within US3, evidence-category and link reviews may run concurrently on the settled document. Keep mutations, red observation, commits and regeneration sequential.

## Implementation strategy

Record design, preserve baseline, observe real red, implement the smallest serializer/adapter change, and regenerate all distributions in its commit. Then add model regression coverage, prove byte compatibility, document evidence limits and pass the postcommit constitution gate. Preserve prior saved work as a reference, never as a substitute for observed validation. Skip SpecKit extension hooks; the factory owns commits and publication approval.
