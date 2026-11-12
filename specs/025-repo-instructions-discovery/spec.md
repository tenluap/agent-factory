# Feature Specification: The factory discovers the repository's own instructions

**Feature Branch**: `025-repo-instructions-discovery`

**Created**: 2026-11-12

**Status**: Draft

**Input**: User description: "Give the factory its own discovery of repo instructions": a stdlib-only scanner reading git objects at the run's ref, the `factory instructions` report and `factory instructions-record` writer, preflight recording and disclosure, orchestrator reads of `always` entries, `CONTEXT.md` terms, an ADR, this repository's config lists and fixture-tree tests. Settled decisions are under Clarifications. The source design document, `docs/repo-instructions-brief.md`, is background only and outside this change.

## Clarifications

### Session 2026-11-12 (grill, settled under cruise)

- Q1: Chain? → A: Full.
- Q2: Which ADR number? → A: 0020, not 0019 (0019 is taken on `origin/024-windows-install`). If 0020 is also taken at implement time, use the next number free on `origin/main` and every remote branch.
- Q3: Is the source design document added? → A: No. It stays outside the change; this spec and the plan are self-contained.
- Q4: Scope? → A: Run 1 (discovery) only; consumption by roles and reviewers is a later feature. Open points (other tools' config, ADR directory patterns, index file name and format) settle at clarify or plan.

### Session 2026-11-12 (clarify, settled under cruise)

- Q: Are other tools' config files read for file names? → A: No (FR-002).
- Q: Default kind for absent or unparseable front matter? → A: The catalogue row's default (FR-009).
- Q: Which path does a duplicate entry carry? → A: Regular file, others as aliases (FR-010).
- Q: Precedence when several sources match? → A: Exclude, then config, then strongest kind (FR-012).
- Q: Index file name and format? → A: `instructions.json` (FR-017).

### Session 2026-11-12 (grill-with-docs, settled under cruise)

- Q5: Input line? → A: Self-contained.
- Q6: Which entries are followed for imports and links? → A: `always` and `scoped` only (FR-004).
- Q7: Kind of `CONTRIBUTING*` and the constitution? → A: Root, `.github/` or `docs/` is `always`; elsewhere `scoped`; constitution only at `.specify/memory/constitution.md` (FR-003, FR-007).
- Q8: Which copy does the orchestrator read? → A: The recorded ref (FR-023).
- Q9: Conflicting documented commands? → A: Root catalogue agent files first; same-tier conflicts go to the setup-commands confirmation (FR-024).
- Q10: Delta identity? → A: By path; changed = hash, kind or scope (FR-018).

## Background

Today the orchestrator reads only the root `CLAUDE.md` and `AGENTS.md`, for build and test commands. No harness loads files inside the run's worktree. This feature gives the factory one deterministic, harness-independent discovery of the repository's instructions at the run's commit.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See every instruction file a repository publishes (Priority: P1)

A factory user asks the CLI which instruction files a repository publishes at a commit. They get one deterministic report of every tracked instruction file at any depth, governance document, imported file and linked document, each with kind, scope, size, hash and title. No run is needed; nothing is written.

**Independent Test**: Run the report against a fixture with root and nested agent files, a Copilot `applyTo` file, a Cursor rule, `CONTRIBUTING.md`, an ADR directory and a linked document; confirm each appears once with the expected kind and scope, and nothing is written.

**Acceptance Scenarios**:

1. **Given** a repository with instruction files at the root and in subdirectories, **When** the user runs the read-only report, **Then** every tracked file matching the catalogue appears once, with path, kind, scope, size, hash and title.
2. **Given** an instruction file that exists in the working tree but is not tracked by git, or is only modified locally, **When** the report runs, **Then** the untracked file is absent and a tracked file is reported with its content at the requested commit, not the working-tree copy.
3. **Given** a ref argument, **When** the report runs, **Then** it reads that commit; with no ref, `HEAD`.
4. **Given** a root `CLAUDE.md` that is a symlink to `AGENTS.md`, **When** the report runs, **Then** it lists one entry with path `AGENTS.md` and alias `CLAUDE.md`.

---

### User Story 2 - Each entry is classified so roles know what to read when (Priority: P1)

Each entry carries a kind (FR-007): `always` is read in full at start; `scoped` before touching a file in its scope; `reference` when relevant.

**Independent Test**: Assert each fixture file's kind and scope against an expected table.

**Acceptance Scenarios**:

1. **Given** a root `AGENTS.md`, **When** indexed, **Then** its kind is `always` and its scope is the repository root.
2. **Given** `packages/api/AGENTS.md`, **When** indexed, **Then** its kind is `scoped` and its scope is `packages/api/`.
3. **Given** a rule file whose front matter declares globs, **When** indexed, **Then** its kind is `scoped` and its scope is those globs.
4. **Given** a rule file flagged always-apply, **When** indexed, **Then** its kind is `always`.
5. **Given** a rule file whose front matter cannot be parsed, **When** indexed, **Then** it stays in the index (with its catalogue row's default kind) and the report carries a note naming it.
6. **Given** an `always` file that imports `@docs/style.md`, which imports another file, **When** indexed, **Then** each imported file is an entry that inherits the importer's kind and scope, following up to 4 import hops.
7. **Given** an instruction file with a relative link to a tracked document, **When** indexed, **Then** the linked document is a `reference` entry; links inside that document are not followed.
8. **Given** the root `README.md` not linked or included by any instruction file, **When** indexed, **Then** it is not an entry.

---

### User Story 3 - The repository tunes discovery through its own config (Priority: P2)

A repository owner adds three glob lists to the tracked `<repo>/.factory/config.json`: `instructions.include`, `instructions.reference` and `instructions.exclude`. The scan honours them (FR-012).

**Independent Test**: In a fixture with all three lists, confirm each list's effect.

**Acceptance Scenarios**:

1. **Given** `instructions.include` naming `docs/conventions.md`, **When** indexed, **Then** that file is an `always` entry with root scope.
2. **Given** `instructions.reference` naming `DESIGN.md`, **When** indexed, **Then** that file is a `reference` entry.
3. **Given** `instructions.exclude` naming `conformance/**`, **When** `conformance/bench/x/AGENTS.md` exists, **Then** it is absent from the index.
4. **Given** a missing or malformed `instructions` section, **When** indexed, **Then** the catalogue alone applies; a malformed section yields a note, never a halt.
5. **Given** this repository after the change, **When** indexed, **Then** `DESIGN.md` and `CONTEXT.md` are `reference` entries and nothing under `conformance/` appears.

---

### User Story 4 - Every run records and discloses its instruction index at preflight (Priority: P1)

At every preflight the orchestrator calls the writer after the stack profile is recorded, then discloses the result (FR-022) and continues.

**Independent Test**: Record twice against differing fixtures; confirm the summary, index file and delta.

**Acceptance Scenarios**:

1. **Given** a pending new run, a pending adoption or a worktree run, **When** the writer runs, **Then** it scans the ref FR-017 names for that run and writes the summary and index file where FR-017 says.
2. **Given** a resumed run whose instruction files changed since the last record, **When** the writer runs, **Then** it reports the added, removed and changed entries; the orchestrator discloses them and the run continues without re-planning.
3. **Given** `always` entries totalling more than 32 KiB, **When** preflight discloses, **Then** it warns and names the largest `always` files; the index itself is never truncated.
4. **Given** a repository with no instruction files, **When** preflight discloses, **Then** it says so, names `create-project-agents-file` as a hint, and the run continues.
5. **Given** a run reaching PR open, **When** run artifacts leave the branch, **Then** the index file leaves with them.

---

### User Story 5 - The orchestrator follows the always entries from the start (Priority: P2)

At preflight and grill, the orchestrator reads every `always` entry in full. Build and test commands documented in any root-scope entry count as documented commands (FR-024).

**Independent Test**: Text-contract test on the orchestrator skill (FR-028).

**Acceptance Scenarios**:

1. **Given** a repository whose test command is documented only in `CONTRIBUTING.md`, **When** preflight records commands, **Then** that command is recorded as documented, not proposed by the detector.
2. **Given** `always` entries, **When** grill runs, **Then** the orchestrator has read them in full first.
3. **Given** documented commands for purposes other than build and test, **When** preflight records commands, **Then** only `build` and `test` are recorded.

---

### Edge Cases

- **Not a git repository, or the ref does not resolve**: the read-only report exits with a usage-style error naming the problem; the writer at preflight records nothing new and reports it in `error`; the orchestrator discloses it. Discovery never halts a run.
- **Import cycle or import of a missing or untracked file**: the cycle is followed once; a missing target is reported as a note; the importer stays indexed.
- **Imports deeper than 4 hops**: not followed; a note names where the chain stopped.
- **Links to URLs, anchors or paths outside the repository**: ignored. A linked catalogued file keeps its catalogue kind.
- **Binary or non-UTF-8 content in a matched file**: indexed with size and hash; title empty; a note names it.

## Requirements *(mandatory)*

### Functional Requirements

**Discovery**

- **FR-001**: The factory CLI MUST provide a deterministic instruction scanner that uses only the language's standard library and git, and reads git objects at a given ref; only files tracked at that ref count, and the working tree is never read.
- **FR-002**: The scanner MUST match files at any depth against a table-driven catalogue, one row per tool, covering at least: `AGENTS.md` (and `AGENTS.override.md`, Amp's `AGENT.md` fallback); Claude Code (`CLAUDE.md`, `.claude/CLAUDE.md`, `CLAUDE.local.md`, `.claude/rules/**/*.md`); `GEMINI.md`; Copilot (`.github/copilot-instructions.md`, `.github/instructions/**/*.instructions.md`); Cursor (`.cursor/rules/**/*.mdc`); Windsurf/Devin (`.windsurf/rules/*.md`, `.windsurf/global_rules.md`, `.windsurfrules`, `.devin/rules/*.md`); Cline (`.clinerules`, `.cline/rules/`); Roo Code (`.roo/rules/`, `.roo/rules-{mode}/`, `.roorules`, `.roorules-{mode}`); Junie (`.junie/AGENTS.md`, `.junie/rules/*.md`, `.junie/playbook.md`, `.junie/guidelines.md`); Kiro (`.kiro/steering/*.md`); Aider's `CONVENTIONS.md`; Zed's `.rules`; Continue (`.continue/rules/*.md`). Each catalogue path is re-checked against its source at plan time. Other tools' config files are not read; owners add such files through `instructions.include`.
- **FR-003**: The scanner MUST also index governance documents: `CONTRIBUTING*`, the constitution (only at `.specify/memory/constitution.md`), and files in ADR directories.
- **FR-004**: The scanner MUST follow `@path` imports up to 4 hops and relative links one hop, only from `always` and `scoped` entries (including imported ones); `reference` entries are leaves. An import is an `@` token at line start or after whitespace, outside code spans and fenced blocks; a link is a Markdown inline or reference-style link outside code, anchor stripped, resolved against the file's directory.
- **FR-005**: The scanner MUST NOT scan submodule contents, and MUST NOT index the root `README.md` unless it is linked or included.

**Index entries and classification**

- **FR-006**: Each entry MUST carry path, kind (`always`, `scoped` or `reference`), scope, size in bytes, content hash, title and aliases.
- **FR-007**: Classification MUST follow: `always` = root agent files, the constitution, `CONTRIBUTING*` at the root, `.github/` or `docs/` (root scope), rule files flagged always-apply, their imports, `instructions.include`; `scoped` = nested agent files and other `CONTRIBUTING*` (scope: their own directory subtree) and rule files with glob front matter (`globs`, `paths`, `applyTo`, `fileMatch`; scope: those globs); `reference` = ADR files, linked documents, description-only, manual, model-decision or mode-specific rule files, `instructions.reference`. Each catalogue row records its tool's documented default kind and front-matter-to-kind mapping.
- **FR-008**: Imported files MUST inherit the importer's kind and scope.
- **FR-009**: One tolerant front-matter reader MUST serve every catalogue row. A rule file with absent or unparseable front matter MUST take its row's default kind; an unparseable one also gets a note naming it.
- **FR-010**: The same content at the same scope MUST be indexed once, carrying the regular file's path (the symlink target), or for identical regular copies the lexicographically first path; the other paths go in the entry's aliases.
- **FR-011**: The index MUST never be truncated, and its order MUST be stable for identical input.

**Configuration**

- **FR-012**: The scanner MUST read `instructions.include`, `instructions.reference` and `instructions.exclude` glob lists from `<repo>/.factory/config.json` at the scanned ref. Include makes files `always` with root scope; reference makes files `reference`; exclude drops files. When several sources match one file: exclude wins; else include beats reference; else the strongest derived kind wins (`always` > `scoped` > `reference`), ties going catalogue/governance > import > link.
- **FR-013**: A missing config or missing section MUST mean empty lists. A malformed section MUST be reported as a note, never halt.
- **FR-014**: `factory init` MUST NOT seed these lists. The config documentation MUST describe them.
- **FR-015**: This repository's tracked `.factory/config.json` MUST set `instructions.reference` to `DESIGN.md` and `CONTEXT.md`, and `instructions.exclude` to `conformance/**`.

**CLI and state**

- **FR-016**: `factory instructions [--repo <path>] [--ref <ref>]` MUST print the index as a read-only report, needing no run and writing nothing.
- **FR-017**: `factory instructions-record` MUST scan the one writable run at its ref (pending new run: `base`; pending adoption: the adoption source ref; worktree run: worktree `HEAD`), store a summary in state (ref, counts per kind, combined hash), write the full index as `instructions.json` (ref, combined hash, notes, ordered entries; sorted keys) in the run folder (beside the pending file before the worktree exists; `<spec_dir>/factory/` after, committed like `profile.md`), and follow the existing write-command contract (validate, atomic write, live-lock refusal, commit on worktree runs).
- **FR-018**: On a re-record, the writer MUST report the delta against the previous index: added, removed and changed entries. Entries match by path; changed means a different hash, kind or scope; alias-only or title-only differences are not changes.
- **FR-019**: The writer's result MUST carry the counts, total size of `always` entries, notes, the over-32-KiB warning with the largest `always` files when the fixed 32 KiB limit is exceeded, and a no-instructions flag when the index is empty.
- **FR-020**: The state summary MUST be optional: older states without it stay valid. The run-state reference MUST document it.
- **FR-021**: The index file MUST leave the branch with the other run artifacts before the PR.

**Orchestrator**

- **FR-022**: Preflight MUST call the writer at every preflight (new run, resume, adopt), immediately after the stack profile is recorded, and disclose counts, sizes, the delta and any notes; the over-32-KiB warning; and the no-instructions case with `create-project-agents-file` as a hint. Discovery MUST never stop a run.
- **FR-023**: The orchestrator MUST read every `always` entry in full at preflight and at grill, at the index's recorded ref (`git show <ref>:<path>`), so content matches the recorded hash.
- **FR-024**: Documented build and test commands MUST come from every root-scope entry, not only root `CLAUDE.md` and `AGENTS.md`. Root catalogue agent files win over governance and include entries; a remaining same-tier conflict goes to the existing setup-commands confirmation (under cruise: first in index order, recorded with that decision). Documented commands still win over detector proposals. `commands` keeps exactly `build` and `test`.
- **FR-025**: The change MUST be recorded in `DESIGN.md` first and carried into the harness-neutral core using only neutral verbs, rendering cleanly for every harness. The catalogue lives in `core/` as data about consuming repositories; the plan carries one justification line for constitution principle II.

**Records and proof**

- **FR-026**: `CONTEXT.md` MUST define **Repo instructions** (tracked files in a consuming repository that state how work there is done), **Instruction index** (the per-run record of repo instructions at the run's ref), **Instruction entry** (one file in the index), **Entry kind** (`always`, `scoped` or `reference`) and **Unapplied rule** (a repository rule that loses to a factory mechanic, recorded in `plan.md` as `Not applied:`; the mirror of **Rule override**).
- **FR-027**: An ADR (number 0020, or the next free number per the grill decision) MUST record that the factory discovers repo instructions itself and never relies on harness auto-loading.
- **FR-028**: Unit tests over fixture trees MUST cover the catalogue, nesting, glob front matter, unparseable front matter, links, imports (including the hop limit), include, reference and exclude, the ref-based read (untracked and locally modified files ignored), duplicate content, and the re-record delta. A text-contract test MUST cover the orchestrator's preflight call, disclosures, `always` reads and command sourcing.

### Key Entities

- **Repo instructions**, **Instruction index**, **Instruction entry**, **Entry kind**: per FR-026.
- **Instruction catalogue**: the table of tool naming conventions the scanner matches; one row per tool.
- **Index summary**: the state record: ref, counts per kind, combined hash.
- **Index delta**: added, removed and changed entries between two records of one run.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For every fixture tree, 100% of expected instruction files appear exactly once with the expected kind and scope, and 0 untracked, excluded or submodule files appear.
- **SC-002**: Two scans of the same repository and ref produce byte-identical output, on every harness.
- **SC-003**: Every preflight (new run, resume, adopt) records and discloses the index; 0 runs stop because of discovery.
- **SC-004**: A re-record after one instruction file is added, one removed and one changed reports exactly those 3 changes.
- **SC-005**: Indexing this repository after the change lists `DESIGN.md` and `CONTEXT.md` as `reference` entries and 0 entries under `conformance/`.
- **SC-006**: The orchestrator text records a test command documented only in a root-scope file other than `CLAUDE.md` or `AGENTS.md` as documented; the text-contract test asserts it.
- **SC-007**: Tests pass; every harness renders; no build output is tracked.

## Assumptions

- Consumption of the index by roles, reviewers, the approver and the bench is out of scope.
- Default ADR directory patterns: `docs/adr/`, `docs/adrs/`, `docs/decisions/`, `doc/adr/`, `adr/` at any depth, Markdown files only; plan settles the final list.
- Content hash: a standard digest of the blob bytes; combined hash: a digest over the ordered entries. Title: first Markdown heading, else front-matter `description`, else file name.
- "Root agent files" means catalogued agent files whose scope is the repository root, including tool directories at the root (for example `.github/copilot-instructions.md`, `.junie/AGENTS.md`).
- Nested scope is the directory holding the file, or for a tool directory below the root (such as `.cursor/rules/`), the directory holding it.
- Untracked, local and user-global files, repo-shipped skills, outside sources, generating instruction files and Trae rules are out of scope. The stack profile keeps scanning the working tree.
