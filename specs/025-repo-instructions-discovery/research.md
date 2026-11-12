# Research: repo instructions discovery

All open points from the spec are settled here. No `NEEDS CLARIFICATION` remains.

## R1. ADR directory patterns (the remaining open point)

- **Decision**: a tracked Markdown file (`*.md`, `*.markdown`) is an ADR file when any directory on its path, at any depth, is named `adr` or `adrs` (case-insensitive), or is named `decisions` and its parent is `doc`, `docs` or `architecture`. Every Markdown file below such a directory counts, including `README.md` and templates. ADR files are `reference` entries.
- **Rationale**: covers adr-tools (`doc/adr`), log4brains and most repos (`docs/adr`, `docs/adrs`), MADR (`docs/decisions`) and arc42-style `architecture/decisions`. A bare `decisions/` directory is too generic (product data, fixtures), so it needs a documentation parent. This repository's `docs/adr/` matches.
- **Alternatives**: the spec's assumption list only (misses `architecture/decisions`, nested `adr/` under packages is the same rule); any directory named `decisions` (false positives); config-only (every repo would need config).

## R2. Catalogue re-check (FR-002)

Re-checked 2026-11-12 against the live docs:

- **Cline** (docs.cline.bot/features/cline-rules): workspace rules in `.clinerules/` or `.cline/rules/` (any Markdown/text file inside); `paths` front matter scopes a rule; no front matter = always; unparseable front matter fails open (always). Cline also reads `.cursorrules` and `.windsurfrules`, which confirms `.cursorrules` as a live convention: added to the Cursor row (root, `always`). A single `.clinerules` file stays in the row as the legacy form.
- **Kiro** (kiro.dev/docs/steering): `.kiro/steering/*.md`; `inclusion: always` (default) = `always`; `inclusion: fileMatch` with `fileMatchPattern` (string or list) = `scoped`; `manual` and `auto` = `reference`. Correction to the starting catalogue: the glob key is `fileMatchPattern`, not `fileMatch`.
- **Continue** (docs.continue.dev/customize/deep-dives/rules): `.continue/rules/*.md`; `alwaysApply: true` = `always`; `globs` = `scoped`; `alwaysApply: false` without globs, or `regex` only, = `reference`; no fields = `always`.

The other rows (AGENTS.md/Amp/Codex/OpenCode, Claude Code, Gemini, Copilot, Cursor, Windsurf/Devin, Roo, Junie, Aider, Zed) are carried from the source research of this month; their front-matter mappings are in data-model.md. Each row carries its source URL in a comment so the next re-check is mechanical.

## R3. Reading git objects

- **Decision**: one `git ls-tree -r -z --full-tree <commit>` lists every tracked path with mode, type and object id; type `commit` (submodule) entries are dropped; mode `120000` entries are symlinks. Blob contents come from one `git cat-file --batch` process fed only the object ids the scan needs. The ref is resolved once with `git rev-parse --verify <ref>^{commit}`; the index records the resolved SHA as `ref`.
- **Rationale**: stdlib `subprocess` plus git only (FR-001); two processes per scan regardless of entry count (ENG-21); the resolved SHA keeps `git show <ref>:<path>` reproducible when `base` (for example `origin/main`) later moves.
- **Alternatives**: `git show` per file (one process per entry); reading the working tree (rejected by FR-001).

## R4. Globs

- **Decision**: a small translator in the scanner turns a glob into an anchored regex: `**/` matches zero or more directories, `**` any characters, `*` any characters except `/`, `?` one non-`/` character; everything else is literal. It serves the three config lists only. Front-matter globs are stored as scope strings, never matched.
- **Rationale**: `fnmatch` treats `*` as crossing `/` and has no `**`; `PurePath.full_match` needs Python 3.13 and CI runs `3.x`, so behaviour would depend on the runner. No existing matcher in `factory_cli` (searched `fnmatch`, `glob`, `translate`).
- **Alternatives**: `fnmatch` (wrong semantics for `conformance/**` vs nested paths); a dependency (Principle V, stdlib-only FR-001).

## R5. Front matter

- **Decision**: one tolerant reader: the file must start with a `---` line and have a closing `---` line; inside, `key: value` scalars (quotes stripped), inline lists `[a, b]`, block lists (`- item`) and comma-separated strings (Copilot `applyTo`). Anything else inside the block, or an unclosed block, is unparseable: the row default applies and a note names the file. A glob list equal to `**` or `**/*` means root scope, so it maps to `always`.
- **Rationale**: no YAML library in the standard library; every catalogue row uses only flat keys.

## R6. Imports, links and precedence

- **Decision**: classification runs to a fixpoint. Seeds are catalogue, governance, include and reference matches. Each round resolves every candidate path by FR-012 precedence, then expands imports (depth ≤ 4 from the seed) and one-hop links from the `always` and `scoped` entries only; a newly reached or promoted path triggers another round. Exclude blocks a path from every source. A visited set stops cycles. Fenced blocks and inline code spans are stripped before matching. An import token is `@` at line start or after whitespace followed by a path containing `/` or `.`; `@~/…` and absolute paths outside the repo are ignored. Link targets with a scheme, `mailto:`, or anchor-only are ignored; `#…` and `?…` are stripped; a leading `/` is repository-root relative; `..` escaping the root is ignored.
- **Rationale**: FR-004 and FR-012 interact (an import can promote a linked file); a fixpoint keeps the result independent of traversal order (SC-002).

## R7. Determinism, hashes and order

- **Decision**: entry `hash` = `sha256:` + hex of the blob bytes; `combined_hash` = `sha256:` + hex of the canonical JSON (`sort_keys`, `separators=(",", ":")`) of the ordered entry list. Entries order by kind (`always`, `scoped`, `reference`), then path; `aliases` and `notes` sorted. The JSON file is written with `sort_keys=True`, indent 2 and a trailing newline.
- **Rationale**: SC-002 byte-identical output; `always` first is the order the orchestrator reads and the "index order" FR-024's cruise tie-break uses.

## R8. Ref per run and file placement

- **Decision**: pending new run: `base`; pending adoption: the ref `adopt` resolves for the pending `branch` (reuse `adopt._resolve`); worktree run: worktree `HEAD`. Pending runs write `<pending-name>.instructions.json` beside the pending file (the `.profile.md` pattern); worktree creation (SKILL step 4.3) and `adopt` move it to `<spec_dir>/factory/instructions.json`; `drop` already removes the run folder, so the file leaves the branch with it (FR-021). The delta compares against the previous `instructions.json` at the same place.
- **Rationale**: reuses the existing sidecar life cycle instead of a new one (Principle V).

## R9. Preflight failure behaviour

- **Decision**: the writer never exits non-zero because of discovery. A ref that does not resolve or a git failure yields exit 0 with `error` set, nothing written, and the previous summary kept. Write-contract refusals (no writable run, live lock) keep their existing exit 1; the orchestrator discloses them and continues (FR-022).
