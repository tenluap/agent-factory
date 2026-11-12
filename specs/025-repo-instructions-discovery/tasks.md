# Tasks: The factory discovers the repository's own instructions

**Input**: Design documents from `specs/025-repo-instructions-discovery/` (plan.md, spec.md, research.md, data-model.md, contracts/cli.md, quickstart.md)

**Tests**: Required (engineering.md; plan "Test seams"). Every behaviour-changing task is one checkbox and one commit: failing test, implementation, passing check. Commit body carries `Red: <test name> failed as expected` and a `New:` line per new function or class (plan already gives reasons for `instructions.py`, `test_instructions.py`, `.factory/config.json`).

**Test command**: `python3 -m unittest discover -s tools` (single file: `python3 -m unittest tools.tests.test_instructions -v`). Fixture trees are built in `Sandbox` git repos from `tools/tests/__init__.py`, never tracked fixture directories.

**Paths**: `M` = `core/skills/factory/bin/factory_cli/`; `T` = `tools/tests/test_instructions.py`.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup (Design first)

- [x] T001 Record the decision in `DESIGN.md` before any `core/` change (Constitution I, FR-025): the factory discovers repo instructions itself from git objects at the run's ref and never relies on harness auto-loading; the `factory instructions` report and `factory instructions-record` writer; the `instructions` state summary and `instructions.json` run-folder file; preflight call after `profile-record`; `always` reads at the recorded ref; command sourcing from every root-scope entry; the catalogue as data in `core/` (Principle II justification from plan.md). Add a "Repo instructions validation" entry under `DESIGN.md` "Validation plan": machine checks `tools/tests/test_instructions.py` (S1-S6); agent-driven runs: a new run whose preflight records and discloses the index, a resume disclosing the delta, and a fixture repository whose test command is documented only in `CONTRIBUTING.md` recorded as documented (SC-003, SC-006). **Exempt: `DESIGN.md` - documentation only.** Done: `DESIGN.md` section and validation entry present; `git diff --stat` touches only `DESIGN.md`.

---

## Phase 2: User Story 1 - See every instruction file a repository publishes (P1) 🎯 MVP

**Goal**: read-only, deterministic report of tracked instruction files at a ref.
**Independent test**: `factory instructions` over a fixture lists each expected file once; nothing written.

- [x] T002 [US1] Scanner core and `factory instructions` command. Seam **S1**; failure paths **F1.1, F1.2, F1.9**.
  1. Test (red) in `T`: sandbox repo with root `AGENTS.md`, `CLAUDE.md` symlink to `AGENTS.md`, an untracked `GEMINI.md`, a committed `CONVENTIONS.md` then modified in the working tree, a submodule-like gitlink, a symlink to a missing path and one to `../outside.md`. Assert via `Sandbox.cli("instructions", "--ref", ...)`: one entry `AGENTS.md` with `aliases: ["CLAUDE.md"]`, `kind: "always"`, `scope: ["/"]`, `size`, `hash` = `"sha256:<hex>"`, `title` from first heading, `source: "catalogue"`; `GEMINI.md` absent; no entry at or under the gitlink path; `CONVENTIONS.md` hash equals the committed blob; no default-`HEAD` vs explicit ref difference; broken and outside symlinks skipped with notes (F1.9); two runs byte-identical (SC-002); `git status --porcelain` unchanged. F1.1: run outside a git repo → exit 2. F1.2: `--ref no-such-ref` → exit 5, stderr names the ref.
  2. Implement `M/instructions.py`: resolve ref with `git rev-parse --verify <ref>^{commit}`; one `git ls-tree -r -z --full-tree <sha>` (drop type `commit`, mode `120000` = symlink resolved in-repo only); one `git cat-file --batch` for needed blobs; `CATALOGUE` tuple with the `agents-md` row first (source URL comment per row); entry fields per data-model.md "Instruction entry"; duplicate content at the same scope = one entry on the regular file (else lexicographically first), others in sorted `aliases` (FR-010); order by kind then path; `combined_hash` per research R7; JSON `sort_keys`, indent 2, trailing newline. argv lists only, never a shell (ENG-25). Add `cmd_instructions` to `M/commands.py` and the usage line and dispatch to `M/cli.py` per contracts/cli.md.
  3. Verify: `python3 -m unittest tools.tests.test_instructions -v` green; full suite green.
  Done: `factory instructions` prints the index JSON for the fixture; exits 2/5 as specified.

- [x] T003 [US1] Full catalogue, governance documents and ADR directories (FR-002, FR-003, FR-005). Seam **S1**; failure paths: none beyond T002.
  1. Test (red) in `T`: one fixture per data-model.md catalogue row (every listed path, including `.cursorrules`, `.devin/global_rules.md`, `.junie/guidelines/**/*.md`, `.roo/rules-<mode>/`, `.roorules-<mode>`, `.clinerules` file and directory forms) plus `CONTRIBUTING.md` at root, `.github/`, `docs/` and `pkg/a/CONTRIBUTING.md`, `.specify/memory/constitution.md`, a `constitution.md` elsewhere, `docs/adr/0001-x.md`, `architecture/decisions/a.md`, a bare `decisions/x.md`, a `.cursor/rules/x.md` (not `.mdc`), and root `README.md`. Assert the expected kind/scope/source table (governance `source: "governance"`; ADR `reference`); bare `decisions/x.md`, `.cursor/rules/x.md`, non-root constitution and `README.md` absent. Identical regular copies collapse to the first path with the other as alias.
  2. Implement the remaining `CATALOGUE` rows, governance matcher (`CONTRIBUTING*` always at root/`.github/`/`docs/`, else scoped to its directory; constitution root path only) and ADR rule from research R1 (`adr`/`adrs` any depth, case-insensitive; `decisions` under `doc`/`docs`/`architecture`; `*.md`, `*.markdown`).
  3. Verify: test file and full suite green.
  Done: every catalogue row and governance rule produces the tabled entries; SC-001 holds for the fixture.

**Checkpoint**: US1 report usable on any repository.

---

## Phase 3: User Story 2 - Each entry is classified (P1)

**Goal**: correct kind and scope for front matter, nesting, imports and links.
**Independent test**: assert kinds and scopes of a fixture against an expected table.

- [x] T004 [US2] Front-matter reader, row mappings and nested scope (FR-007, FR-009). Seam **S1**; failure paths **F1.4, F1.8**.
  1. Test (red) in `T`: `packages/api/AGENTS.md` → `scoped`, `["packages/api/"]`; `.cursor/rules/a.mdc` with `alwaysApply: true` → `always`; `globs: src/**/*.ts` → `scoped` with that glob; `description` only → `reference`; Copilot `applyTo: "a/**,b/**"` → `scoped` `["a/**","b/**"]`; Kiro `inclusion: fileMatch` + `fileMatchPattern` → `scoped`; Windsurf `trigger: model_decision` → `reference`; Continue `alwaysApply: false` no globs → `reference`; `globs: "**"` at root → `always`; nested `pkg/.cursor/rules/g.mdc` with `globs: x/*` → scope `["pkg/x/*"]`; title falls back to front-matter `description`, then file name. F1.4: unclosed front matter → row default kind, note `front matter unparseable: <path>`. F1.8: non-UTF-8 blob → indexed with size and hash, `title: ""`, note naming it.
  2. Implement one tolerant reader per research R5 (scalars, quoted strings, inline and block lists, comma lists); per-row mapping table from data-model.md; base-directory rule (derived `always` below root becomes `scoped` to `<base>/`; glob scopes prefixed with `<base>/`).
  3. Verify: test file and full suite green.
  Done: every row's mapping yields the tabled kind and scope; notes sorted.

- [x] T005 [US2] Imports and links to a fixpoint (FR-004, FR-008). Seam **S1**; failure paths **F1.5, F1.6, F1.7**.
  1. Test (red) in `T`: root `AGENTS.md` imports `@docs/style.md`, which imports `@docs/more.md` → both `always`, root scope, `source: "import"`; a scoped `pkg/AGENTS.md` import inherits `["pkg/"]`; `@` inside a fenced block or code span ignored; `user@example.com` ignored; a relative link `[g](docs/guide.md#x)` → `reference`, `source: "link"`, and links inside `docs/guide.md` not followed; links to URLs, `mailto:`, anchors only and `../../outside` ignored; a link to a catalogued file keeps its catalogue kind; a `reference` entry's imports not followed; an import reaching a link target promotes it to `always`. F1.5: `@missing.md` and an untracked target → note, importer kept. F1.6: `a.md` ↔ `b.md` cycle → each once. F1.7: chain of 6 → hops 1-4 indexed, note naming where the chain stopped.
  2. Implement research R6: seeds, per-round FR-012 precedence (strongest kind; ties catalogue/governance > import > link), import depth ≤ 4, link depth 1, visited set, fence and code-span stripping, anchor and query stripping, `/` root-relative, escape-the-root ignored.
  3. Verify: test file and full suite green; two scans byte-identical.
  Done: import and link fixtures match the table; README unlinked stays absent, linked becomes `reference`.

**Checkpoint**: US1 and US2 complete; index content final except config.

---

## Phase 4: User Story 3 - Repository tunes discovery through config (P2)

**Goal**: `instructions.include`, `.reference`, `.exclude` at the scanned ref.
**Independent test**: one fixture with all three lists.

- [ ] T006 [US3] Config lists and glob translator (FR-012, FR-013). Seam **S1**; failure path **F1.3**.
  1. Test (red) in `T`: committed `.factory/config.json` with `include: ["docs/conventions.md"]` → `always`, `["/"]`, `source: "config"`; `reference: ["DESIGN.md"]` → `reference`; `exclude: ["conformance/**"]` drops `conformance/bench/x/AGENTS.md` and blocks it as import or link target; include beats reference for the same file; root `AGENTS.md` also in `include` keeps `source: "catalogue"`; a working-tree-only config edit has no effect (read at the ref). Glob cases: `conformance/**` matches nested, `*.md` does not cross `/`, `**/x.md` matches root and nested, `?` one non-`/` char. F1.3: section not an object, list of non-strings, unparseable JSON → note, catalogue alone applies, exit 0.
  2. Implement the translator per research R4 and the config read at the ref with precedence exclude > include > reference > derived.
  3. Verify: test file and full suite green.
  Done: all three lists behave per spec US3 scenarios 1-4.

- [ ] T007 [US3] This repository's config lists (FR-015, SC-005). **Exempt: `.factory/config.json` - configuration only; its effect is asserted under S1.**
  1. Write `.factory/config.json`: `{"instructions": {"reference": ["DESIGN.md", "CONTEXT.md"], "exclude": ["conformance/**"]}}` (merge into any existing keys).
  2. Add to `T` an S1 assertion that copies this file's committed content into a sandbox with `DESIGN.md`, `CONTEXT.md` and `conformance/x/AGENTS.md`: both `reference`, nothing under `conformance/`. Exempt commit: no `Red:` line (ENG-2).
  3. Verify: after commit, quickstart step 2 prints `reference reference always` and `[]`.
  Done: SC-005 holds on this repository.

---

## Phase 5: User Story 4 - Every run records and discloses its index (P1)

**Goal**: writer stores summary and index file; reports delta, warning, empty flag.
**Independent test**: record twice against differing fixtures; check summary, file and delta.

- [ ] T008 [US4] `factory instructions-record` writer and state summary (FR-017, FR-020). Seams **S2, S4**; failure paths **F2.2, F2.3, F4.1**.
  1. Test (red) in `T`: pending new run → scans `base`, writes `<pending-name>.instructions.json` beside the pending file, state `instructions` = `{ref, counts, combined_hash}`; pending adoption → scans the ref `adopt._resolve` returns; worktree run → scans worktree `HEAD`, writes `<spec_dir>/factory/instructions.json`, commits `factory: instructions recorded` only when the file changed (second identical record: `committed: null`); stdout keys per contracts/cli.md. F2.2: no writable run → exit 1, nothing written. F2.3: live lock → exit 1, nothing written. S4/F4.1: `factory validate` on a state whose `instructions` has a non-object `counts` or non-string `ref` reports a violation; a state without the field validates.
  2. Implement `cmd_instructions_record` in `M/commands.py` reusing `resolve_target`, `write_run`, `commit_worktree`, the `.profile.md` sidecar pattern and `adopt._resolve`; usage and dispatch in `M/cli.py`; light optional-field validation in `M/state.py`.
  3. Verify: test file, `tools.tests.test_state`, `tools.tests.test_profile_record` and full suite green.
  Done: each run type records the summary and index file in its place.

- [ ] T009 [US4] Delta, 32 KiB warning, empty flag and scan error (FR-018, FR-019, R9). Seam **S2**; failure paths **F2.1, F2.4**.
  1. Test (red) in `T`: re-record after one file added, one removed, one changed (hash) → `delta` lists exactly those three paths, sorted (SC-004); a kind or scope change counts as changed; alias-only and title-only changes do not; first record `delta: null`. `always` entries totalling > 32768 bytes → `warning` `{limit: 32768, always_bytes, largest}` (up to 5, largest first); index not truncated. Empty repo → `empty: true`, counts zero. F2.1: pending run whose `base` does not resolve → exit 0, `error` set, nothing written, previous summary kept. F2.4: unreadable previous index file → `delta: null`, note saying so.
  2. Implement delta by path identity; warning, `always_bytes`, `empty`, `error` per contracts/cli.md.
  3. Verify: test file and full suite green.
  Done: writer output matches the contract in every case.

- [ ] T010 [US4] Sidecar life cycle on adopt and drop (FR-021, R8). Seams **S3, S5**; failure path **F3.1**.
  1. Test (red): in `tools/tests/test_adopt.py`, a successful adopt moves `<pending-name>.instructions.json` to `<spec_dir>/factory/instructions.json`; F3.1: a refused adoption keeps the pending sidecar. In `tools/tests/test_drop.py`, `drop` removes `instructions.json` with the run folder (S5; may pass already: then `Red: not applicable - <existing drop test> already covers this`).
  2. Implement the move and clean-up in `M/adopt.py` beside `.profile.md`.
  3. Verify: `tools.tests.test_adopt`, `tools.tests.test_drop` and full suite green.
  Done: the index file follows the run folder through adopt and drop.

- [ ] T011 [P] [US4] Document the summary, writer and report in `core/skills/factory/references/state.md` (FR-020), and the three config lists in the config README text in `M/models.py` (FR-014; `factory init` still seeds none). **Exempt: `references/state.md` and `models.py` config README text - documentation only.** Done: both texts describe the field, file, commands and lists; `factory init` in a sandbox writes a `config.json` with no `instructions` key (FR-014; existing init test or one added assertion); full suite green.

---

## Phase 6: User Story 5 - Orchestrator follows the always entries (P2)

**Goal**: preflight calls the writer, discloses results, reads `always` entries, sources commands.
**Independent test**: text-contract test on `core/skills/factory/SKILL.md`.

- [ ] T012 [US5] Orchestrator text (FR-022, FR-023, FR-024). Seam **S6**; failure paths: none.
  1. Test (red) in `T`: read `core/skills/factory/SKILL.md` and assert: step 1 item 5 calls `factory instructions-record` immediately after `profile-record` at every preflight (new, resume, adopt); disclosure of counts, sizes, delta and notes; the 32 KiB warning; the no-instructions case naming `create-project-agents-file`; "never stops a run"; step 4.3 moves the pending `<pending-name>.instructions.json` into `factory/instructions.json` beside `brief.md` before the start commit; adoption step 1 names `instructions-record` with `profile-record`; preflight, after `instructions-record`, reads every `always` entry in full at the recorded ref; grill reads every `always` entry in full with `git show <ref>:<path>`; documented build and test commands come from every root-scope entry, root catalogue agent files win, same-tier conflicts go to the setup-commands confirmation (cruise: first in index order); `commands` keeps exactly `build` and `test`.
  2. Edit `core/skills/factory/SKILL.md` using only neutral verbs (`SHELL`), no harness names.
  3. Verify: test file and full suite green; build command renders all five harnesses.
  Done: the text contract passes and every harness renders.

---

## Phase 7: Polish

- [ ] T013 Records check (FR-026, FR-027). **Exempt: `CONTEXT.md` and the ADR - documentation only, already written.** Run `git ls-remote --heads origin` and `git ls-tree -r --name-only origin/<branch> docs/adr` for `origin/main` and every remote branch; if `0020` is taken, rename `docs/adr/0020-the-factory-discovers-repo-instructions-itself.md` to the next free number and update references (`git grep -n 0020-the-factory`). Done: ADR number unique; `CONTEXT.md` defines the five terms.
- [ ] T014 Final verification: run the test command, the build command from state (`FACTORY_HOME="$(mktemp -d)"` render loop, untracked `dist/`, `bash -n install.sh`) and quickstart steps 2-3. Verification step; changes no files. Done: all green; `cmp` silent; exits 5 and 2.

---

## Dependencies

- T001 before every `core/` task.
- T002 → T003 → T004 → T005 → T006 → T007 (same files `instructions.py`, `T`).
- T008 after T006; T009 after T008; T010 after T008.
- T011 [P] any time after T008.
- T012 after T008 (names the writer and its outputs).
- T013 independent; T014 last.

## Parallel opportunities

- T011 alongside T009/T010 (different files).
- T013 alongside any phase.
- Story tasks share `instructions.py` and `T`, so they run in order.

## Implementation strategy

MVP = Phases 1-2 (T001-T003): the read-only report. Then classification (US2), config (US3), recording (US4), orchestrator (US5). Each checkpoint leaves the suite green and the build rendering.
