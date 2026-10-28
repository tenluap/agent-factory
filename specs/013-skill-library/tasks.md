# Tasks: Factory Skill Library

**Input**: Design documents from `specs/013-skill-library/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/install-cli.md, quickstart.md

**Tests**: Required. Each implementation task is preceded by a failing-test task naming its plan seam; plan-exempt tasks carry their exemption instead. Test runner: `python3 -m unittest discover -s tools`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependencies)
- **[Story]**: user story (US1, US2, US3)

Seams (plan.md "Test seams"): **S1** `render.py --paths skills_root`; **S2** `install.sh library linking`; **S3** `install.sh --add-skill`; **S4** `install.sh --uninstall library links`; **S5** `repo skill layer layout`.

## Phase 1: Setup

- [X] T001 Add a "Skill library" section to `DESIGN.md` before any installer or adapter change (constitution I): repo layer `skills/` and per-user layer `${FACTORY_HOME}/skills/`, per-user precedence, library-link ownership rule (symlink whose target starts with `$src/skills/` or `$factory_home/skills/`; a link made from another checkout or worktree, or before the checkout moved, counts as user-owned — fix: remove the old link and re-run), reserved name `factory`, dot-folders never linked, stale-link pruning, `--add-skill`, uninstall (layers kept; Codex and Copilot share `~/.agents/skills`, so uninstalling one removes the other's library links), link-not-render decision citing ADR 0009, manual refresh of vendored skills (maintainer re-copies and updates `skills/SOURCES.md`; no sync tool) (FR-014). Exempt: DESIGN.md - documentation only

---

## Phase 2: Foundational (skills root per harness)

**Purpose**: `install.sh` needs each harness's expanded `skills_root` before any story can link skills.

- [X] T002 Failing test for seam S1 (`render.py --paths skills_root`) in `tools/tests/test_render_models.py`: for each of the five harnesses, `python3 tools/render.py <h> --paths` prints `skills_root=` with the home-expanded FR-004 root — claude-code `~/.claude/skills`, opencode `~/.config/opencode/skills`, codex and copilot `~/.agents/skills`, zcode `~/.zcode/skills` — and writes nothing; with `CLAUDE_HOME`, `ZCODE_HOME` or `XDG_CONFIG_HOME` set the root follows the override; with `CODEX_HOME`/`COPILOT_HOME` set Codex and Copilot stay on `~/.agents/skills`.
- [X] T003 Implement seam S1: in `tools/render.py` expand `skills_root` in `load_adapter` the same way as `skill_dir`, and print it shell-quoted in `print_paths`. Add the `skills_root` key to `adapters/{claude-code,opencode,codex,copilot,zcode}/adapter.json` (claude-code `{home}/skills`, opencode `{home}/opencode/skills`, zcode `{home}/skills`, codex and copilot `~/.agents/skills`; research R2). Adapter values: Exempt: adapters/*/adapter.json `skills_root` values - configuration; reported values covered by the `--paths` seam
- [X] T004 Re-render all five harnesses (`for h in claude-code opencode codex copilot zcode; do python3 tools/render.py "$h"; done`) and run the constitution's dist gate `test -z "$(git status --porcelain -- dist/)"`; it must pass (FR-011, SC-004, constitution III). Verification task, no seam.

**Checkpoint**: `--paths` reports `skills_root` for every harness; `dist/` unchanged.

---

## Phase 3: User Story 1 - Required skills install with the factory (P1) MVP

**Goal**: `./install.sh` links the six vendored required skills into each selected harness's skills root.

**Independent Test**: In a throwaway `HOME`, run `./install.sh --harness opencode`; each of the six names in `~/.config/opencode/skills/` is a symlink into `$src/skills/<name>/`.

- [X] T005 [US1] Failing test for seam S5 (`repo skill layer layout`) in new `tools/tests/test_skill_library.py`: for each of `grilling`, `domain-modeling`, `pr`, `ponytail`, `tdd`, `brainstorming`, `skills/<name>/SKILL.md` exists with frontmatter `name` equal to the folder, `skills/<name>/LICENSE` exists, and `skills/SOURCES.md` has a row `| name | source URL | path | commit | license |` where commit is a 40-hex git SHA.
- [X] T006 [US1] Vendor the six skills verbatim into `skills/<name>/` per research R6 (shallow-clone upstream, record `git rev-parse HEAD`, copy the skill folder and the upstream root `LICENSE` verbatim; no offline fallback), and write `skills/SOURCES.md` with one row per skill (FR-001, FR-002). Do not vendor any skill whose license forbids redistribution or whose upstream repository and LICENSE cannot be obtained; a gap stops implementation and is escalated to the user rather than completing with fewer than six skills (FR-001, T005). Exempt: skills/<name>/ vendored content - verbatim third-party documentation; structure covered by the repo skill layer layout seam
- [X] T007 [US1] Failing test for seam S2 (`install.sh library linking`) in `tools/tests/test_skill_library.py`, reusing `InstallSandbox` from `tools/tests/test_install.py`: (a) every repo-layer skill is linked into the selected root and `SOURCES.md` is not; (b) a second run leaves the filesystem identical and prints `linked: <target>` again for each unchanged link; (c) a pre-existing real directory at a target is untouched and reported with `skip: <target> exists and is not a library link; to adopt it: ./install.sh --add-skill <target>, remove the original, re-run`; (d) a pre-existing symlink pointing outside the library, live or dangling, is untouched and skipped the same way; (e) `--harness all` links each skill once into the shared `~/.agents/skills` with no error; (f) a dot-prefixed folder with `SKILL.md` in `skills/` is never linked; (g) a `factory` folder in the repo layer is skipped with `skip: <layer>/factory: name reserved for the factory skill` and the factory skill link is untouched; (h) a library link whose source folder is gone is removed with `removed: <target>`.
- [X] T008 [US1] Implement seam S2 (repo layer) in `install.sh`: add `link_skill` (create link when absent; re-point only an existing library link; otherwise print `skip:` and leave the path untouched; `readlink` without `-f`) and `install_skills "$skills_root"` (first prune library links whose target no longer exists, printing `removed: <target>`; then link only folders containing `SKILL.md`, ignoring dot-prefixed folders and skipping `factory` with `skip:`; research R3, R4), called from `install_one` after the factory skill and agents; read `skills_root` from the existing `eval` of `render.py --paths`. Print `linked: <target>` per link.

**Checkpoint**: US1 delivers SC-001: preflight `RESOLVE` (unchanged, FR-012) finds all six skills.

---

## Phase 4: User Story 2 - Manually add personal skills (P2)

**Goal**: Per-user skills in `${FACTORY_HOME}/skills/` are linked, win over the repo layer, and can be added with one command.

**Independent Test**: `./install.sh --harness opencode --add-skill <valid folder>` prints `added: ${FACTORY_HOME}/skills/<name>` and the skill is linked.

- [X] T009 [US2] Failing test for seam S2 (`install.sh library linking`, per-user layer) in `tools/tests/test_skill_library.py`: a folder dropped by hand into `${FACTORY_HOME}/skills/<name>/` with `SKILL.md` is linked on re-run; a per-user skill named like a repo-layer skill (e.g. `tdd`) wins and the existing repo link is re-pointed; without `${FACTORY_HOME}/skills/` only the repo layer is linked; a dot-prefixed folder (e.g. `.tdd.tmp.123`) and a `factory` folder in the per-user layer are never linked; after a per-user skill shadowing a repo skill is deleted, a re-run prints `removed: <target>` and relinks to the repo copy.
- [X] T010 [US2] Implement seam S2 (per-user layer) in `install.sh` `install_skills`: list repo-layer folders, then `$factory_home/skills/` folders, a per-user name overwriting the repo entry (FR-006); apply the same dot-folder and `factory` exclusions; skip the per-user layer when the directory is absent.
- [X] T011 [US2] Failing test for seam S3 (`install.sh --add-skill`) in `tools/tests/test_skill_library.py`: a valid local folder is copied to `${FACTORY_HOME}/skills/<name>/`, `added: <dest>` is printed, and it is linked; the per-user layer is created when absent; a symlink pointing outside the library whose own name matches frontmatter `name` (the adoption hint) is accepted even when its target folder has another basename; a failed copy (induced by a failing `cp` shim placed first on the sandbox `PATH`, so the case also fails correctly when run as root) exits non-zero and leaves no `.<name>.tmp.*` folder and no destination; each refusal exits 2 and writes nothing in either layer or skills root — missing path or not a directory and a URL (`error: <path>: not a local directory`), no `SKILL.md`, no frontmatter, `name '<n>' does not match folder '<f>'`, folder `factory` (`reserved: factory`), existing destination (`exists: <dest>`); `--add-skill` without a value and `--add-skill` with `--uninstall` are usage errors (exit 2).
- [X] T012 [US2] Implement seam S3 in `install.sh`: parse `--add-skill <path>`, reject it with `--uninstall`; `add_skill` runs once before the harness loop: refuse URLs and non-directories, take the name from the basename of the path as given (trailing `/` stripped, never the resolved target), refuse `factory` with `reserved: factory`, parse `SKILL.md` frontmatter with inline `python3` stdlib (first line `---`, closing `---`, a `name:` line, quotes stripped), refuse on `exists:`; only then `mkdir -p "$factory_home/skills"`, `cp -RH` into `$factory_home/skills/.<name>.tmp.$$`, `rm -rf` the temp folder if `cp` or `mv` fails, and `mv` into place (research R5, ENG-25, ENG-26). Never execute skill content.

**Checkpoint**: US2 delivers SC-002.

---

## Phase 5: User Story 3 - Safe conflicts and uninstall (P3)

**Goal**: `--uninstall` removes only library links. (Install-time conflict skip is delivered by T007/T008.)

**Independent Test**: Pre-create a real directory in the skills root, install, uninstall; the directory survives and every library link is gone.

- [X] T013 [US3] Failing test for seam S4 (`install.sh --uninstall library links`) in `tools/tests/test_skill_library.py`: after install, `--uninstall` removes every link into `$src/skills/` and `${FACTORY_HOME}/skills/` printing `removed: <target>`, including links in `~/.agents/skills` that Copilot shares when uninstalling `--harness codex`; a real directory, a regular file and a symlink pointing elsewhere in the skills root survive; `skills/` and `${FACTORY_HOME}/skills/` survive unchanged.
- [X] T014 [US3] Implement seam S4 in `install.sh`: add `unlink_skills "$skills_root"` removing only symlinks whose `readlink` target starts with either layer prefix, called from the uninstall branch for each selected harness (FR-010).

**Checkpoint**: US3 delivers SC-003.

---

## Phase 6: Polish & Cross-Cutting

- [X] T015 [P] Add a skill library section to `README.md`: both layers, `--add-skill`, reserved name `factory`, `skip:` conflict handling and adoption, links from another checkout or a moved checkout treated as user-owned (remove the old link and re-run), stale-link removal, uninstall (shared Codex/Copilot root: uninstalling either removes library links for both), manual refresh of vendored skills, and a note in the install table (FR-014). Exempt: README.md - documentation only
- [x] T016 Run the build command (render all five harnesses, `git diff --exit-code -- dist/`, then the constitution's porcelain gate `test -z "$(git status --porcelain -- dist/)"`), `python3 -m unittest discover -s tools` and `bash -n install.sh`; confirm all pass (SC-004). Verification task, no seam.

---

## Dependencies & Execution Order

- T001 first (constitution I), then Phase 2 (T002 → T003 → T004) blocks all stories.
- US1: T005 → T006; T007 → T008. The T005/T006 pair and the T007/T008 pair touch different files and can run in either order.
- US2 depends on T008 (`install_skills`, `link_skill`): T009 → T010 → T011 → T012.
- US3 depends on T008: T013 → T014. It may run in parallel with US2 only if `install.sh` edits are serialised.
- T015 can run any time after T001; T016 last.

## Parallel Example

```text
After T004: T005+T006 (skills/, test layout) alongside T007 (test linking)
Any time after T001: T015 (README.md)
```

## Implementation Strategy

1. MVP: Phases 1-3 (US1). Validate with the US1 independent test and `quickstart.md`.
2. Add US2, then US3, each verified by its independent test.
3. Polish: README and full build/test run.
