# Data model: repo instructions discovery

## Instruction catalogue (`instructions.CATALOGUE`)

A tuple of rows, one per tool. Every row matches at any depth; a match below the root has the directory holding the file (or holding the tool directory, such as `.cursor/`) as its base directory.

| Row | Paths (relative to the base directory) | Default kind | Front-matter mapping |
|---|---|---|---|
| agents-md | `AGENTS.md`, `AGENTS.override.md`, `AGENT.md` | always | none |
| claude-code | `CLAUDE.md`, `.claude/CLAUDE.md`, `CLAUDE.local.md`, `.claude/rules/**/*.md` | always | `paths` = scoped |
| gemini | `GEMINI.md` | always | none |
| copilot | `.github/copilot-instructions.md` (always); `.github/instructions/**/*.instructions.md` | reference | `applyTo` (comma list) = scoped |
| cursor | `.cursor/rules/**/*.mdc`, `.cursorrules` (always) | reference | `alwaysApply: true` = always; `globs` = scoped; `description` only = reference |
| windsurf-devin | `.windsurf/rules/*.md`, `.windsurf/global_rules.md`, `.windsurfrules`, `.devin/rules/*.md`, `.devin/global_rules.md` | always | `trigger`: `always_on` = always; `glob` + `globs` = scoped; `model_decision`, `manual` = reference |
| cline | `.clinerules` (file), `.clinerules/**`, `.cline/rules/**` (`.md`, `.txt`) | always | `paths` = scoped |
| roo | `.roo/rules/**`, `.roorules` (always); `.roo/rules-<mode>/**`, `.roorules-<mode>` (reference) | per path | none |
| junie | `.junie/AGENTS.md`, `.junie/rules/*.md`, `.junie/playbook.md`, `.junie/guidelines.md`, `.junie/guidelines/**/*.md` | always | none |
| kiro | `.kiro/steering/*.md` | always | `inclusion`: `always` = always; `fileMatch` + `fileMatchPattern` = scoped; `manual`, `auto` = reference |
| aider | `CONVENTIONS.md` | always | none |
| zed | `.rules` | always | none |
| continue | `.continue/rules/*.md` | always | `alwaysApply: true` = always; `globs` = scoped; `alwaysApply: false` without globs, or `regex` only = reference |

Governance (not catalogue rows, same tier for precedence): `CONTRIBUTING*` (always at root, `.github/`, `docs/`; else scoped to its directory); `.specify/memory/constitution.md` (always, root only); ADR files (reference; research.md R1).

Kind at a base directory below the root: a derived `always` becomes `scoped` to `<base>/`; derived glob scopes are prefixed with `<base>/`. A glob scope of `**` or `**/*` at the root is `always`.

## Instruction entry

| Field | Type | Rule |
|---|---|---|
| `path` | string | repository-relative POSIX path of the regular file |
| `kind` | `always` \| `scoped` \| `reference` | FR-007, FR-012 |
| `scope` | list of strings | `["/"]` = root; `["pkg/api/"]` = directory subtree (trailing `/`); otherwise globs as declared (prefixed per above); `reference` entries carry `["/"]` |
| `size` | integer | blob bytes (above 1 MiB the content is hashed by streaming, never held or parsed; a note names the file) |
| `hash` | string | `sha256:<hex>` of blob bytes |
| `title` | string | first Markdown heading, else front-matter `description`, else file name; empty for non-UTF-8 |
| `aliases` | list of strings | sorted other paths with the same content at the same scope (symlinks, identical copies) |
| `source` | `catalogue` \| `governance` \| `config` \| `import` \| `link` | the winning source (precedence tie-break, FR-024 tiering) |

Reason for `source` (Principle V): FR-024 ranks root catalogue agent files above governance and include entries, so the orchestrator needs the winning source per entry. A root catalogue agent file also matched by `instructions.include` keeps `source: "catalogue"` (its kind is already `always` at root scope), so an include never demotes it from the top FR-024 tier.

## Instruction index (`instructions.json`)

```json
{
  "combined_hash": "sha256:…",
  "entries": [ { "aliases": [], "hash": "sha256:…", "kind": "always", "path": "AGENTS.md", "scope": ["/"], "size": 812, "source": "catalogue", "title": "Agents" } ],
  "notes": ["front matter unparseable: .cursor/rules/x.mdc"],
  "ref": "<resolved commit sha>"
}
```

Validation: `kind` in the three values; `size` ≥ 0; paths unique; entries ordered by kind then path; `notes` sorted.

## Index summary (state field `instructions`, optional)

```json
"instructions": { "ref": "<sha>", "counts": { "always": 3, "scoped": 1, "reference": 22 }, "combined_hash": "sha256:…" }
```

Optional like `profile`: states without it stay valid (FR-020). `factory validate` light-checks presence and types when the field exists; unknown extra fields pass through.

## Index delta

`{ "added": [paths], "removed": [paths], "changed": [paths] }`, each sorted. Match by `path`; changed = different `hash`, `kind` or `scope`; alias-only and title-only differences are not changes. `null` on a first record or when the previous index is unreadable: invalid JSON, not an object, or entries lacking `path`, `hash`, `kind` or `scope` (a note says which).

## Config lists (`<repo>/.factory/config.json` at the scanned ref)

```json
{ "instructions": { "include": ["docs/conventions.md"], "reference": ["DESIGN.md"], "exclude": ["conformance/**"] } }
```

Each list holds glob strings (research.md R4). Missing file or section = empty lists. A section that is not an object, a list that is not a list of strings, or unparseable JSON = a note, and the lists are treated as empty.

## State transitions

Preflight (new, resume, adopt) → `instructions-record` → summary replaced, index file rewritten, delta reported. Worktree creation and adoption move the pending sidecar into the run folder. `drop` removes it with the run folder.
