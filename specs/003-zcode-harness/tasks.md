---

description: "Task list for the ZCode harness adapter"
---

# Tasks: ZCode Harness Adapter

**Input / prerequisites**: `/specs/003-zcode-harness/` — plan.md, spec.md, research.md, data-model.md,
quickstart.md

**Tests**: Mandatory. Every behaviour-changing task is preceded by a failing-test task naming the seam it
targets (plan.md, "Test seams"). Tasks covered by a plan exemption carry that exemption instead.

**Test runner**: the repository's own commands - the canonical render loop (plan.md, "Canonical render
environment") then `git diff --exit-code -- dist/`, plus the frontmatter assertion in quickstart.md. No
runner is introduced.

**Organization**: grouped by user story (US1 install, US2 run, US3 documentation). `[P]` = parallelisable;
paths are relative to the repository root.

---

## Phase 1: Setup

> The old empty-folder task is folded into T004 (git tracks no empty directory; analyze-1 N1). T001 is
> the tracked-distribution setup that makes Seam 4 able to fail.

- [X] T001 Make the rendered distribution tracked (FR-018, ADR 0005, quickstart step 2): remove the
      `/dist/` line from `.gitignore`, run the full render **in the canonical render environment**
      (FR-018; plan.md, "Canonical render environment"):
      `env -u CLAUDE_HOME -u CODEX_HOME -u COPILOT_HOME -u ZCODE_HOME -u XDG_CONFIG_HOME FACTORY_HOME=/nonexistent sh -c 'for h in
      $(python3 tools/render.py --list); do python3 tools/render.py "$h" || exit 1; done'`, then
      `git add dist/` and commit **all five** rendered trees (`dist/claude-code/`, `dist/codex/`,
      `dist/copilot/`, `dist/opencode/`, and `dist/zcode/` once T004 exists — at this point the four
      existing ones). Confirm `grep -c '^/dist/$' .gitignore` is 0 and `git ls-files dist/ | wc -l` is > 0.
      Confirm the render is canonical: repeating the same `env -u …` render leaves
      `git diff --exit-code -- dist/` clean even with `XDG_CONFIG_HOME` or a model override set.
      `Exempt: .gitignore - configuration only - one removed line; its effect is what makes Seam 4 able to
      fail, and Seam 4 covers it` and `Exempt: dist/** - generated output for every harness, produced by
      the render and guarded by Seam 4, never hand-written` (plan.md, "Test seams").

---

## Phase 2: Foundational (Blocking Prerequisites)

- [X] T002 Record the red baseline from `specs/003-zcode-harness/quickstart.md` step 1: run
      `python3 tools/render.py --list` (no `zcode` line) and `python3 tools/render.py zcode`
      (`unknown harness 'zcode'`), and keep both outputs for the `Red:` lines of T003 and T005. Also
      record Seam 4's red proof, which T001 made possible: edit a source file the render copies, re-render,
      and `git diff --exit-code -- dist/` exits non-zero; restore the edit afterwards.

**Checkpoint**: `dist/` is tracked and the baseline is captured; story work can begin.

---

## Phase 3: User Story 1 - Install the factory into ZCode (Priority: P1) 🎯 MVP

**Goal**: `tools/render.py` knows the `zcode` adapter and produces an installable ZCode distribution
(skill + one agent per role) with ZCode-readable metadata. Both adapter files are created here (T004 and
T008); T009/T010 extend `harness.md` in Phase 4.

**Independent Test** (both adapter files present — `adapter.json` and `harness.md`, T004 + T008):
`python3 tools/render.py --list` lists `zcode`; `python3 tools/render.py zcode`
exits 0; `dist/zcode/agents/` holds one `factory-<role>.md` per file in `core/roles/` (9) with parseable
frontmatter; `./install.sh --harness zcode` places them under `~/.zcode`.

### Tests for User Story 1

- [X] T003 [US1] Failing test for **Seam 1** (`python3 tools/render.py --list` includes `zcode`) and
      **Seam 2** (`python3 tools/render.py zcode` exits 0 and writes `dist/zcode/skill/` plus one
      `dist/zcode/agents/factory-<role>.md` per `core/roles/*.md`): run the Seam 1 and Seam 2 commands
      already written in `specs/003-zcode-harness/quickstart.md` steps 2-3 and record their failure
      output; both MUST fail now (`zcode` absent, `unknown harness 'zcode'`).

### Implementation for User Story 1

- [X] T004 [US1] Create `adapters/zcode/adapter.json` (which creates the folder) with exactly the values
      in data-model.md §1:
      `name` `zcode`; `home` `{ "env": "ZCODE_HOME", "default": "~/.zcode" }`; `skill_dir`
      `{home}/skills/factory`; `agent_dir` `{home}/agents`; `agent_file` `factory-{role}.md`;
      `agent_format` `markdown`; `fields` `[["name", "factory-{role}"], ["description", "{description}"]]`;
      `access.read.tools` `"Read, Grep, Glob, Bash"`; `access.write.tools`
      `"Read, Edit, Write, Bash, Grep, Glob"`; `models` `{ "deep": "", "standard": "" }` (the key is
      required by `load_adapter`'s config override; empty values make agents inherit the session model).
      Validation (data-model.md §1): valid JSON, templated paths use only `{home}`, `access` has exactly
      the role keys (`read`, `write`), `models` has `deep` and `standard`. Turns T003 green
      for **Seam 1 only**: `known()` counts any folder holding `adapter.json` and `render()` copies every
      known adapter's `harness.md` into every skill tree, so until T008 exists *every* harness's render
      fails with `FileNotFoundError: adapters/zcode/harness.md`. T008 therefore follows immediately and is
      committed with T004 (plan.md, Seam 2).

- [X] T008 [US1] Create `adapters/zcode/harness.md` in the shape of `adapters/codex/harness.md`, with the
      header values in data-model.md §2: `name` `zcode`; `invoke` `/factory`; recognition line quoted
      verbatim — "you are ZCode (Z.ai's coding agent, desktop app or CLI): `ZCODE_HOME` is set or
      `~/.zcode` exists, and you have the Agent, Bash, Read, Edit and Skill tools." — the checkable
      signal is required by FR-012 and clarification 8, so self-description plus a tool list is not
      enough; capability tier **1**; `speckit_init` `--integration zcode --integration-options="--skills"`
      (research R4); `impeccable_provider` `codex` with the note that ZCode has no provider of its own and
      the codex provider installs to `~/.agents/skills/`, which ZCode reads (R5). The verb table (T009)
      and Notes (T010) are added later in Phase 4. Together with T004 this makes Seam 2 able to go green.
      `Exempt: adapters/zcode/harness.md - documentation only - prose the orchestrator reads at runtime;
      its only build-time effect, being copied into every skill, is covered by Seam 2` (plan.md).

- [X] T005 [US1] Failing test for **Seam 3** (frontmatter of `dist/zcode/agents/factory-*.md`): run the
      `python3 - <<'PY' … PY` block in quickstart.md step 3 — every file parses as YAML frontmatter with
      keys exactly `name`/`description`/`tools`, `name` equal to the filename stem, and no `<F>` left in
      the body. MUST fail now (no files to parse).

- [X] T006 [US1] Generate the ZCode distribution: `python3 tools/render.py zcode`, confirm
      `ls dist/zcode/agents | wc -l` equals `ls core/roles/*.md | wc -l` (9), re-run T005 until green. `Exempt: dist/** - generated output for every harness, produced by the render and
      guarded by Seam 4, never hand-written (the render rewrites every harness's skill tree, so the
      exemption covers all five)` (plan.md, "Test seams").

**Checkpoint**: US1 complete - the adapter renders and installs.

---

## Phase 4: User Story 2 - Run a full factory run inside ZCode (Priority: P1)

**Goal**: the orchestrator recognises ZCode and performs every neutral verb there.

**Independent Test**: `dist/<harness>/skill/references/harness/zcode.md` exists for every harness and
carries the recognition line, tier 1, the verb table and the notes; a ZCode `/factory` session selects it.

### Tests for User Story 2

- [X] T007 [US2] Failing test for **Seam 2** (rendered skill content) and **Seam 4** (the tracked
      distribution matches a fresh render, so no harness drifts): after a full render in the canonical
      environment (`env -u CLAUDE_HOME -u CODEX_HOME -u COPILOT_HOME -u ZCODE_HOME -u XDG_CONFIG_HOME FACTORY_HOME=/nonexistent …`,
      T001), assert
      `references/harness/zcode.md` exists under `dist/<h>/skill/` for every `h` in
      `python3 tools/render.py --list`, then run `git diff --exit-code -- dist/` against the tree T001
      committed. MUST fail now: `zcode.md` is in no skill tree, and because `dist/` is tracked the
      difference check reports the divergence and exits non-zero rather than passing vacuously.

### Implementation for User Story 2

> T008 has moved into **Phase 3** beside T004 (analyze-2 B1): `adapter.json` without `harness.md` breaks
> every harness's render. Its ID is unchanged; T009-T010 add the rest of that same file.

- [X] T009 [US2] Add the verb table to `adapters/zcode/harness.md` **exactly as data-model.md §2 states**,
      row for row: `SPAWN` and `SPAWN_PARALLEL` via the Agent tool with `subagent_type: factory-<role>`
      (FR-002); `ASK` (FR-008); `NOTIFY` = no-op (FR-009); `RESOLVE` = first `<name>/SKILL.md` in the four
      roots `<repo>/.zcode/skills/`, `<repo>/.agents/skills/`, `~/.zcode/skills/`, `~/.agents/skills/`
      (FR-010, research R2); `SHELL` = the Bash tool. Same exemption as T008.

- [ ] T010 [US2] Add the Notes section to `adapters/zcode/harness.md` as data-model.md §2 states: agents
      in `~/.zcode/agents/factory-<role>.md`; models unpinned, pinned via `${FACTORY_HOME}/config.json`
      `models.zcode` then re-install (FR-006); never invoke `speckit-*` or `grill-with-docs` with the
      Skill tool — read the resolved file (FR-013); `$ARGUMENTS` is whatever follows `/factory` (FR-007);
      ledger `reported: null`, Agent results expose no token usage (FR-014). Same exemption as T008.

- [ ] T011 [US2] Re-render every harness in the canonical environment and commit the result:
      `env -u CLAUDE_HOME -u CODEX_HOME -u COPILOT_HOME -u ZCODE_HOME -u XDG_CONFIG_HOME FACTORY_HOME=/nonexistent sh -c 'for h in
      $(python3 tools/render.py --list); do python3 tools/render.py "$h" || exit 1; done'`, then
      `git add dist/` and commit all five trees (each now carries `references/harness/zcode.md`), then
      re-run the Seam 4 gate `git diff --exit-code -- dist/` on a clean tree: it must exit 0 because the
      committed distribution equals the fresh canonical render (Constitution III, FR-015, FR-018, SC-003,
      SC-006). If an earlier local render or install ran outside the canonical environment, run
      `git checkout -- dist/` and re-render canonically first. Turns T007 green. `Exempt: dist/** - generated output for every harness, produced by the render and guarded by
      Seam 4, never hand-written (the render rewrites every harness's skill tree, so the exemption covers
      all five)` (plan.md, "Test seams").

**Checkpoint**: US1 and US2 both work; the factory runs on ZCode.

---

## Phase 5: User Story 3 - Understand ZCode support from the documentation (Priority: P2)

**Goal**: ZCode is discoverable in the entry documentation, design record and domain terms (FR-016).

**Independent Test**: `README.md`, `DESIGN.md` and `CONTEXT.md` each name ZCode with accurate install,
invoke and agent-location details.

> No test tasks: every task below is covered by a plan exemption (documentation only).

- [ ] T012 [P] [US3] `README.md`: add the harness-table row
      ``| ZCode | `./install.sh --harness zcode` | `/factory <feature>` | `~/.zcode/agents/factory-*.md` |``
      (backticked like `README.md:9-12`), and state ZCode's SpecKit setup as **its own sentence**
      after the requirement line (the "SpecKit set up for your harness" bullet) —
      "For ZCode: `specify init --here --integration zcode --integration-options="--skills"`" — **not** as another value of that line's
      `--ai <...>` enumeration, a flag family specify-cli 1.1.0 no longer has. The other harnesses'
      recorded form is out of scope (FR-016, research R4).
      `Exempt: README.md - documentation only` (plan.md).

- [ ] T013 [P] [US3] `DESIGN.md`: add `zcode` to "Harness model" (the harness list) and to "Adapters
      today", noting agents inherit the session model unless `${FACTORY_HOME}/config.json` pins them.
      **Also fix the spec-kit setup line at `DESIGN.md:69`** (Constitution I, FR-016): it already reads
      `specify init --here <harness.speckit_init>`; delete only the Claude-shaped parenthetical
      `(--ai <harness>, plus --ai-skills outside Claude Code ...)`, leaving a neutral gloss:
      each adapter states its own `speckit_init` arguments (ZCode's:
      `--integration zcode --integration-options="--skills"`, research R4). No other adapter's recorded
      setup changes. `Exempt: DESIGN.md - documentation only` (plan.md).

- [ ] T014 [P] [US3] `CONTEXT.md`: name ZCode in the **Harness** definition alongside the existing
      harnesses. The domain-modeling step already added it, so this is a verification: confirm the line
      reads `(Claude Code, OpenCode, Codex, Copilot, ZCode)` and edit no further if it does.
      `Exempt: CONTEXT.md - documentation only` (plan.md).

**Checkpoint**: all three stories complete.

---

## Phase 6: Polish & Cross-Cutting Concerns

> T015 is removed (analyze-1 C2): FR-010 is already corrected in `spec.md` to research R2's four roots,
> so no spec edit remains. IDs are not renumbered.

- [ ] T016 Verify FR-017: `git diff --name-only` shows no file under `core/` changed.

- [ ] T017 Run `specs/003-zcode-harness/quickstart.md` steps 2-3 end to end and confirm all four seams are
      green: quickstart step 2's tracking checks still hold, full **canonical** render of every harness
      (`env -u CLAUDE_HOME -u CODEX_HOME -u COPILOT_HOME -u ZCODE_HOME -u XDG_CONFIG_HOME FACTORY_HOME=/nonexistent …`), Seam 1 (`--list` includes `zcode`), Seam 2 (`dist/zcode/`
      skill + 9 agents), Seam 3 (frontmatter assertion), and Seam 4 `git diff --exit-code -- dist/` on the
      tracked tree exiting 0. Also check the environment sensitivity: a *non-canonical* render (with
      `XDG_CONFIG_HOME` set) dirties `dist/`, and `git checkout -- dist/` restores a clean gate.
      Re-confirm Seam 4 can still fail by repeating T002's red proof.

- [ ] T018 Manual validation (SC-001, SC-002, SC-004, SC-005): `./install.sh --harness zcode`, check
      `~/.zcode/skills/factory` and `~/.zcode/agents/factory-*.md`, repeat with
      `ZCODE_HOME=/tmp/zc` for the env override. **`install.sh` renders, so each install rewrites the
      tracked `dist/` tree**: after each one run `git checkout -- dist/` and confirm
      `git diff --exit-code -- dist/` is clean again (FR-018). Then
      start `/factory <feature>` in a fresh ZCode session, then
      `./install.sh --harness zcode --uninstall` (quickstart steps 4 and 6). **SC-005, both directions**
      (quickstart step 5): (a) start a run in ZCode with `/factory <feature>`, answer grilling, reach a
      checkpoint, stop the session, then run `/factory` in another installed harness (e.g. Claude Code)
      and confirm it resumes at the stage in `specs/<branch>/factory/state.json` with nothing re-asked;
      (b) repeat in the opposite direction with a second feature. Record both outcomes; a failure in
      either direction blocks SC-005.

---

## Dependencies & Execution Order

- **Phase 1 → Phase 2**: T001 before T002 — `dist/` must be tracked and committed before any red proof of
  Seam 4 is possible.
- **Phase 2 blocks everything**: the red baseline (T002) is the evidence for T003, T005 and T007.
- **US1 (Phase 3)**: T003 → T004 → T008 → T005 → T006, strictly sequential (same adapter, same output
  tree). T004 and T008 land in one commit: `adapter.json` without `harness.md` breaks *every* harness's
  render (analyze-2 B1), so no ordered step leaves the adapter folder half-built.
- **US2 (Phase 4)**: depends on T004 + T008 (the renderer must know `zcode` and find its harness document
  before any skill renders). T007 → T009 → T010 → T011; T008-T010 touch the same file, so none is `[P]`.
- **US3 (Phase 5)**: independent of US1/US2 content; T012, T013 and T014 are different files and run in
  parallel.
- **Polish (Phase 6)**: T016-T018 after T011 (T018's resume check also needs T006's installed agents).

### Parallel Opportunities

- T012, T013, T014 together (three different documentation files); US3 as a whole can run alongside
  Phases 3-4. Nothing else parallelises: the adapter is two files and one generated tree.

---

## Implementation Strategy

**MVP** = Phases 1-3 (US1): the adapter renders and installs into ZCode. Then US2 (the harness document's
verbs and notes) → US3 (documentation) → polish. Each phase ends green with the Seam 4 gate.

## Notes

- Commit each task once, test and implementation together (T004 and T008 share one commit), with a
  `Red: <check> failed as expected` line for T004 (from T003) and T006 (from T005); exempt tasks carry
  no `Red:` line.
- Never edit `dist/` by hand (Constitution III); always regenerate and commit with the source. From T001
  on, `dist/` is tracked (FR-018, ADR 0005), so `git diff --exit-code -- dist/` is a gate that fails.
- Every render whose result is committed, and every run of the Seam 4 gate, is wrapped in
  `env -u CLAUDE_HOME -u CODEX_HOME -u COPILOT_HOME -u ZCODE_HOME -u XDG_CONFIG_HOME FACTORY_HOME=/nonexistent` (plan.md,
  "Canonical render environment"). Any non-canonical render or `install.sh` run rewrites the tracked tree
  and is undone with `git checkout -- dist/`.
- Total tasks: 17 (T001-T018, T015 removed; T008 runs in Phase 3).
- No file under `core/` may name ZCode (FR-017, Constitution II).
- `docs/adr/0005-...md` and `CONTEXT.md`'s ZCode line were already written by the domain-modeling step,
  so no task creates them (plan.md, ENG-10 note); T001 implements the ADR and T014 verifies the line.
