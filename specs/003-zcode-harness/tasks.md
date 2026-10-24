---

description: "Task list for the ZCode harness adapter"
---

# Tasks: ZCode Harness Adapter

**Input**: Design documents from `/specs/003-zcode-harness/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Mandatory. Every behaviour-changing task is preceded by a failing-test task naming the seam it
targets (plan.md, "Test seams"). Tasks covered by a plan exemption carry that exemption instead.

**Test runner**: the repository's own commands - `for h in $(python3 tools/render.py --list); do python3
tools/render.py "$h" || exit 1; done` then `git diff --exit-code -- dist/`, plus the `python3 -c`
frontmatter assertion in quickstart.md. No runner is introduced.

**Organization**: grouped by user story (US1 install, US2 run, US3 documentation).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependencies)
- Paths are relative to the repository root.

---

## Phase 1: Setup

- [ ] T001 Create the empty adapter folder `adapters/zcode/` (no file yet) so later tasks have a home.

---

## Phase 2: Foundational (Blocking Prerequisites)

- [ ] T002 Record the red baseline from `specs/003-zcode-harness/quickstart.md` step 1: run
      `python3 tools/render.py --list` (no `zcode` line) and `python3 tools/render.py zcode`
      (`unknown harness 'zcode'`), and keep both outputs for the `Red:` lines of T003 and T005.

**Checkpoint**: baseline captured; story work can begin.

---

## Phase 3: User Story 1 - Install the factory into ZCode (Priority: P1) 🎯 MVP

**Goal**: `tools/render.py` knows the `zcode` adapter and produces an installable ZCode distribution
(skill + one agent per role) with ZCode-readable metadata.

**Independent Test**: `python3 tools/render.py --list` lists `zcode`; `python3 tools/render.py zcode`
exits 0; `dist/zcode/agents/` holds one `factory-<role>.md` per file in `core/roles/` (9) with parseable
frontmatter; `./install.sh --harness zcode` places them under `~/.zcode`.

### Tests for User Story 1

- [ ] T003 [US1] Failing test for **Seam 1** (`python3 tools/render.py --list` includes `zcode`) and
      **Seam 2** (`python3 tools/render.py zcode` exits 0 and writes `dist/zcode/skill/` plus one
      `dist/zcode/agents/factory-<role>.md` per `core/roles/*.md`): add the two commands as an executable
      check in `specs/003-zcode-harness/quickstart.md` step 2-3 form and run them; both MUST fail now
      (`zcode` absent, `unknown harness 'zcode'`).

### Implementation for User Story 1

- [ ] T004 [US1] Create `adapters/zcode/adapter.json` with exactly the values in data-model.md §1:
      `name` `zcode`; `home` `{ "env": "ZCODE_HOME", "default": "~/.zcode" }`; `skill_dir`
      `{home}/skills/factory`; `agent_dir` `{home}/agents`; `agent_file` `factory-{role}.md`;
      `agent_format` `markdown`; `fields` `[["name", "factory-{role}"], ["description", "{description}"]]`;
      `access.read.tools` `"Read, Grep, Glob, Bash"`; `access.write.tools`
      `"Read, Edit, Write, Bash, Grep, Glob"`; `models` `{ "deep": "", "standard": "" }` (the key is
      required by `load_adapter`'s config override; empty values make agents inherit the session model).
      Validation (data-model.md §1): valid JSON, templated paths use only `{home}`, `access` has exactly
      the keys the roles declare (`read`, `write`), `models` has `deep` and `standard`. Turns T003 green
      for Seams 1 and 2.

- [ ] T005 [US1] Failing test for **Seam 3** (frontmatter of `dist/zcode/agents/factory-*.md`): run the
      `python3 - <<'PY' ... PY` block in `specs/003-zcode-harness/quickstart.md` step 3 - every file parses
      as YAML frontmatter with `name` equal to the filename stem, non-empty `description` and `tools`, and
      no `<F>` left in the body. MUST fail now (no files to parse).

- [ ] T006 [US1] Generate the ZCode distribution: `python3 tools/render.py zcode`, then confirm
      `ls dist/zcode/agents | wc -l` equals `ls core/roles/*.md | wc -l` (9) and re-run T005's assertion
      until green. `Exempt: dist/zcode/** - generated output, produced by Seam 2 and guarded by Seam 4,
      never hand-written` (plan.md, "Test seams").

**Checkpoint**: US1 complete - the adapter renders and installs.

---

## Phase 4: User Story 2 - Run a full factory run inside ZCode (Priority: P1)

**Goal**: the orchestrator recognises ZCode and performs every neutral verb there, with the harness
document carried into every harness's skill.

**Independent Test**: `dist/<harness>/skill/references/harness/zcode.md` exists for every harness and
carries the recognition line, tier 1, the verb table and the notes; a ZCode session running `/factory`
selects it.

### Tests for User Story 2

- [ ] T007 [US2] Failing test for **Seam 2** (rendered skill content) and **Seam 4** (no other harness
      drifts): after a full render, assert `references/harness/zcode.md` exists under
      `dist/<h>/skill/` for every `h` in `python3 tools/render.py --list`, then run
      `git diff --exit-code -- dist/`. MUST fail now (`zcode.md` is in no skill tree).

### Implementation for User Story 2

- [ ] T008 [US2] Create `adapters/zcode/harness.md` in the shape of `adapters/codex/harness.md`, with the
      values in data-model.md §2: `name` `zcode`; `invoke` `/factory`; recognition line "you are ZCode
      (Z.ai's coding agent, desktop app or CLI); you have the Agent, Bash, Read, Edit and Skill tools.";
      capability tier **1**; `speckit_init` `--integration zcode --integration-options="--skills"`
      (research R4); `impeccable_provider` `codex` with the note that ZCode has no provider of its own and
      the codex provider installs to `~/.agents/skills/`, which ZCode reads (R5).
      `Exempt: adapters/zcode/harness.md - documentation only - prose the orchestrator reads at runtime;
      its only build-time effect, being copied into every skill, is covered by Seam 2` (plan.md).

- [ ] T009 [US2] Add the verb table to `adapters/zcode/harness.md` exactly as data-model.md §2 states:
      `SPAWN` = Agent/Task tool with `subagent_type: factory-<role>`, inputs as the prompt (FR-002);
      `SPAWN_PARALLEL` = one Agent call per role, all in one message; `ASK` = the Markdown layout from
      `protocol.md` for grilling and relays, `AskUserQuestion` for other choice asks, a plain message for
      free text (FR-008); `NOTIFY` = no-op, no notification tool (FR-009); `RESOLVE` = first
      `<name>/SKILL.md` in `<repo>/.zcode/skills/`, `<repo>/.agents/skills/`, `~/.zcode/skills/`,
      `~/.agents/skills/` (FR-010 as corrected by plan deviation D1 / research R2); `SHELL` = the Bash
      tool. Same exemption as T008.

- [ ] T010 [US2] Add the Notes section to `adapters/zcode/harness.md`: agents live in
      `~/.zcode/agents/factory-<role>.md`; models unpinned, pin via `${FACTORY_HOME}/config.json`
      `models.zcode` then re-run `./install.sh --harness zcode` (FR-006); never invoke `speckit-*` or
      `grill-with-docs` with the Skill tool - read the resolved file and follow it (FR-013); `$ARGUMENTS`
      is whatever follows `/factory` (FR-007); ledger `reported: null` because Agent results expose no
      token usage (FR-014). Same exemption as T008.

- [ ] T011 [US2] Re-render every harness and commit the result:
      `for h in $(python3 tools/render.py --list); do python3 tools/render.py "$h" || exit 1; done`, then
      `git diff --exit-code -- dist/` after staging, so `dist/` never drifts (Constitution III, FR-015,
      SC-003). Turns T007 green. `Exempt: dist/** - generated output, produced by Seam 2 and guarded by
      Seam 4, never hand-written` (plan.md).

**Checkpoint**: US1 and US2 both work; the factory runs on ZCode.

---

## Phase 5: User Story 3 - Understand ZCode support from the documentation (Priority: P2)

**Goal**: ZCode is discoverable in the repository's entry documentation, design record and domain terms
(FR-016).

**Independent Test**: `README.md`, `DESIGN.md` and `CONTEXT.md` each name ZCode with accurate install,
invoke and agent-location details.

> No test tasks: every task below is covered by a plan exemption (documentation only).

- [ ] T012 [P] [US3] `README.md`: add the harness-table row
      `| ZCode | ./install.sh --harness zcode | /factory <feature> | ~/.zcode/agents/factory-*.md |`, and
      extend the SpecKit requirement line (currently `specify init --here --ai <...>`) with ZCode's
      verified form `specify init --here --integration zcode --integration-options="--skills"`
      (research R4). `Exempt: README.md - documentation only` (plan.md).

- [ ] T013 [P] [US3] `DESIGN.md`: add `zcode` to "Harness model" (the harness list) and to "Adapters
      today", noting agents inherit the session model unless `${FACTORY_HOME}/config.json` pins them.
      `Exempt: DESIGN.md - documentation only` (plan.md).

- [ ] T014 [P] [US3] `CONTEXT.md`: name ZCode in the **Harness** definition alongside the existing
      harnesses. `Exempt: CONTEXT.md - documentation only` (plan.md).

**Checkpoint**: all three stories complete.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T015 Correct `specs/003-zcode-harness/spec.md` FR-010 to the four roots verified in research R2
      (`<repo>/.zcode/skills/`, `<repo>/.agents/skills/`, `~/.zcode/skills/`, `~/.agents/skills/`),
      removing the `.claude` roots per plan deviation D1, so spec and adapter agree.
      `Exempt: specs/**.md - documentation only` (plan.md, documentation exemption).

- [ ] T016 Verify FR-017: `git diff --name-only` shows no file under `core/` changed.

- [ ] T017 Run `specs/003-zcode-harness/quickstart.md` steps 2-3 end to end (full render, Seam 3
      frontmatter assertion, `git diff --exit-code -- dist/`) and confirm all four seams are green.

- [ ] T018 Manual validation (SC-001, SC-002, SC-004, SC-005): `./install.sh --harness zcode`, check
      `~/.zcode/skills/factory` and `~/.zcode/agents/factory-*.md`, repeat with
      `ZCODE_HOME=/tmp/zc` for the env override, start `/factory <feature>` in a fresh ZCode session, then
      `./install.sh --harness zcode --uninstall` (quickstart steps 4 and 6).

---

## Dependencies & Execution Order

- **Phase 1 → Phase 2**: T001 before T002.
- **Phase 2 blocks everything**: the red baseline (T002) is the evidence for T003 and T005.
- **US1 (Phase 3)**: T003 → T004 → T005 → T006, strictly sequential (same adapter, same output tree).
- **US2 (Phase 4)**: depends on T004 (the renderer must know `zcode` before its skill renders).
  T007 → T008 → T009 → T010 → T011; T008-T010 touch the same file, so none is `[P]`.
- **US3 (Phase 5)**: independent of US1/US2 content; T012, T013 and T014 are different files and run in
  parallel.
- **Polish (Phase 6)**: T015 any time after T009; T016-T018 after T011.

### Parallel Opportunities

- T012, T013, T014 together (three different documentation files).
- US3 can run in parallel with Phase 3/4 by a second person.
- Nothing else parallelises: the adapter is two files and one generated tree.

---

## Implementation Strategy

**MVP** = Phase 1 + Phase 2 + Phase 3 (US1): the adapter renders and installs into ZCode.

**Incremental delivery**: MVP → US2 (the harness document, so runs actually work on ZCode) → US3
(documentation) → polish. Each phase ends green with `git diff --exit-code -- dist/`.

## Notes

- Commit each task once, test and implementation together, with a `Red: <check> failed as expected` line
  for T004 (from T003) and T006 (from T005); exempt tasks carry no `Red:` line.
- Never edit `dist/` by hand (Constitution III); always regenerate and commit with the source.
- No file under `core/` may name ZCode (FR-017, Constitution II).
