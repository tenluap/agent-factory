# Feature Specification: Factory Skill Library

**Feature Branch**: `013-skill-library`
**Created**: 2026-10-28
**Status**: Draft
**Input**: User description: "I want to be able to store several skills in the software factory to make it easier to manage all the skills I really, really use on my project."

## Clarifications

### Session 2026-10-28

- Q: Which command is the `dist/` gate in SC-004? → A: The constitution's porcelain check, `test -z "$(git status --porcelain -- dist/)"`, after rendering every harness; `git diff --exit-code -- dist/` alone is not the gate (analyze D1).
- Q: Where does a vendored skill's LICENSE come from when the upstream cannot be cloned? → A: Only from the upstream repository's own LICENSE file, copied verbatim; a skill whose LICENSE cannot be obtained is not vendored (analyze U1).
- Q: What happens to the temporary copy when `--add-skill` fails part-way, and are dot-folders library skills? → A: The temporary folder is removed on failure; dot-prefixed folders in either layer are never linked (analyze U2).
- Q: Does `--add-skill` create a missing per-user layer? → A: Yes, it creates `${FACTORY_HOME}/skills/` after validation passes and before copying (analyze U3).
- Q: What does a re-run print for a library link that is already correct? → A: `linked: <target>` again, like the existing factory link helper; output and filesystem are identical across runs (analyze A1).
- Q: Which folder name is checked against frontmatter `name` in `--add-skill`? → A: The basename of the path as given, before symlink resolution, so the adoption hint works for a symlink pointing outside the library (analyze U4).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Required skills install with the factory (Priority: P1)

A user runs `./install.sh` and every skill the factory itself requires (`grilling`, `domain-modeling`, `pr`, `ponytail`, `tdd`, `brainstorming`) becomes available in each selected harness, so factory preflight no longer stops on a missing required skill.

**Why this priority**: Missing required skills block every factory run today; this is the core value.

**Independent Test**: On a clean home directory, run the installer for one harness and check that each required skill resolves through a symlink into the repository's `skills/` directory.

**Acceptance Scenarios**:

1. **Given** a clean harness skills root, **When** the user runs `./install.sh --harness <h>`, **Then** each repo-layer skill is a symlink in that harness's skills root pointing at `skills/<name>/`.
2. **Given** the library is installed, **When** factory preflight resolves required skills, **Then** all six resolve through the existing search order with no preflight change.
3. **Given** the installer ran once, **When** it runs again, **Then** the result is identical (idempotent), each unchanged library link prints `linked: <target>` again, and no file outside the links changes.

---

### User Story 2 - Manually add personal skills (Priority: P2)

A user adds a skill they rely on to the per-user library layer, either with `./install.sh --add-skill <path>` or by placing a folder in `${FACTORY_HOME}/skills/` and re-running the installer, and the skill is linked into every selected harness.

**Why this priority**: The user explicitly asked to manage their own skills from one place.

**Independent Test**: Run `--add-skill` with a valid local skill folder and check the copy in the per-user layer plus the harness links.

**Acceptance Scenarios**:

1. **Given** a local folder containing `SKILL.md` with frontmatter `name` equal to the folder name, **When** the user runs `./install.sh --add-skill <path>`, **Then** the folder is copied into `${FACTORY_HOME}/skills/<name>/` and linked into each selected harness.
2. **Given** a folder with no `SKILL.md`, missing frontmatter, or a `name` that differs from the folder name, **When** the user runs `--add-skill`, **Then** the installer refuses with a message naming the problem and changes nothing.
3. **Given** `${FACTORY_HOME}/skills/<name>/` already exists, **When** the user runs `--add-skill` with a skill of that name, **Then** the installer refuses with `exists: <path>` and changes nothing.
4. **Given** a skill folder placed by hand in `${FACTORY_HOME}/skills/`, **When** the user re-runs `./install.sh`, **Then** that skill is linked like any other library skill.
5. **Given** a per-user skill with the same name as a repo-layer skill, **When** the installer links skills, **Then** the per-user copy wins.

---

### User Story 3 - Safe conflicts and uninstall (Priority: P3)

The installer never deletes or overwrites user files, and `--uninstall` removes only the links it owns.

**Why this priority**: Users already have skills in their harness directories; the library must coexist with them.

**Independent Test**: Pre-create a real directory at a target path, install, then uninstall, and check the directory is untouched.

**Acceptance Scenarios**:

1. **Given** a target path exists and is not a symlink, **When** the installer runs, **Then** it skips that skill with a `skip:` message explaining how to adopt it (add it with `--add-skill`, remove the original, re-run).
2. **Given** library links and unrelated skills exist, **When** the user runs `./install.sh --uninstall`, **Then** only links pointing into the repo or per-user library layer are removed.

---

### Edge Cases

- Target is a symlink pointing outside the library: treated as user-owned and skipped, never replaced.
- `--add-skill` source path does not exist or is not a directory: refused, nothing changes.
- `--add-skill` source is a git URL: unsupported; only local folder paths are accepted.
- `${FACTORY_HOME}/skills/` does not exist: `--add-skill` creates it after validation passes and before copying; installing without it links only the repo layer.
- `--add-skill` copy fails part-way: the temporary copy is removed and the per-user layer is unchanged.
- Dot-prefixed folders (such as a leftover temporary copy) in either layer are not library skills and are never linked.
- `--add-skill` given a symlink pointing outside the library (the adoption hint): the link's own name is checked against frontmatter `name`.
- Harnesses sharing a skills root (Codex and Copilot use `~/.agents/skills`): each skill is linked once, no error on the second harness; `--uninstall --harness codex` also removes the library links Copilot uses, and vice versa.
- A vendored skill whose upstream license forbids redistribution, or whose upstream LICENSE file cannot be obtained: not vendored.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The repository MUST ship a repo layer `skills/<name>/` containing verbatim copies of `grilling`, `domain-modeling`, `pr`, `ponytail`, `tdd` and `brainstorming`.
- **FR-002**: Each vendored skill MUST keep its upstream LICENSE file, copied verbatim from the upstream repository (never reconstructed), and `skills/SOURCES.md` MUST record source URL, path, commit and license per skill.
- **FR-003**: The per-user layer `${FACTORY_HOME}/skills/<name>/` MUST hold the user's manual additions and MUST never be committed to the repository.
- **FR-004**: Each adapter MUST declare its harness's skills root: Claude Code `~/.claude/skills`, OpenCode `~/.config/opencode/skills`, Codex and Copilot `~/.agents/skills`, ZCode `~/.zcode/skills`.
- **FR-005**: `./install.sh` MUST symlink every skill from both layers into the skills root of each harness chosen by `--harness`, using symlinks as for the factory skill and role agents, under the library-link ownership rule of FR-007 (existing symlinks pointing outside the library are skipped, not replaced). Dot-prefixed folders are not linked.
- **FR-006**: On a name clash between layers, the per-user skill MUST win.
- **FR-007**: A target that exists and is not a symlink into the library MUST be skipped with a `skip:` message describing how to adopt it; the installer MUST NOT delete or overwrite user files.
- **FR-008**: `./install.sh --add-skill <path>` MUST accept only a local folder path, validate that `SKILL.md` exists with frontmatter whose `name` matches the folder name, copy the folder into the per-user layer, then link it. The folder name checked is the basename of the path as given, not of its resolved symlink target.
- **FR-009**: `--add-skill` MUST refuse with `exists: <path>` when the per-user folder already exists; updating requires deleting the folder and re-adding.
- **FR-010**: `./install.sh --uninstall` MUST remove only links that point into a library layer.
- **FR-011**: Library skills MUST be linked from their source folders and MUST NOT be rendered into `dist/`; `tools/render.py` output MUST NOT change because of library content.
- **FR-012**: Factory preflight `RESOLVE` MUST stay unchanged.
- **FR-013**: Tests in `tools/tests` MUST cover linking, conflict skip, add, add clash, per-user precedence and uninstall, run by `python3 -m unittest discover -s tools`.
- **FR-014**: README and DESIGN.md MUST document both layers, `--add-skill`, conflict handling, the shared Codex/Copilot skills root on uninstall, and manual refresh of vendored skills (maintainer re-copies and updates `skills/SOURCES.md`; no sync tool).

### Key Entities

- **Library skill**: a folder with `SKILL.md` (frontmatter `name` equals folder name) plus supporting files.
- **Repo layer**: committed `skills/` directory with the factory-required set and `SOURCES.md`.
- **Per-user layer**: `${FACTORY_HOME}/skills/`, user-managed, never committed.
- **Skills root**: per-harness directory where the installer places skill links, declared by the adapter.
- **Library link**: a symlink in a skills root pointing into a library layer; the only thing the installer creates or removes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After one `./install.sh` run, factory preflight finds all six required skills on every installed harness with zero missing-skill stops.
- **SC-002**: Adding a personal skill takes one command and it appears in every selected harness without further steps.
- **SC-003**: Install, re-install and uninstall leave 100% of pre-existing non-library files in skills roots unchanged.
- **SC-004**: After rendering all five harnesses, the constitution's dist gate `test -z "$(git status --porcelain -- dist/)"` passes, and the test command passes.

## Assumptions

- `FACTORY_HOME` is already defined by the installer (as in the existing factory install).
- All four upstreams (mattpocock/skills, dietrichgebert/ponytail, backnotprop/pstack, obra/superpowers) are MIT and allow redistribution.
- Symlinks are supported on all target platforms, as for the existing factory skill links.
- No network access or git fetching is needed by the installer.
