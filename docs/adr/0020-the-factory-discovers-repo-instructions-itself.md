# The factory discovers repo instructions itself

2026-11-12: the factory finds a consuming repository's instructions with its own deterministic scanner and never relies on a harness auto-loading them. Harnesses load different files (one reads `CLAUDE.md`, another `AGENTS.md`, a third its own rule directory), most never load files inside a run's worktree, and none records what it loaded. A run must see the same instructions on every harness and be able to say which ones it treated as binding.

## Decision

1. **One scanner, at the run's ref.** A stdlib-only scanner in the factory CLI reads git objects at the run's ref. Only tracked files count; the working tree, untracked and local files, user-global files and submodule contents are never read, so two scans of one ref are byte-identical.
2. **A table-driven catalogue.** One row per tool names its instruction files and its default entry kind. Governance documents (`CONTRIBUTING*`, the SpecKit constitution, ADR directories), `@path` imports and one hop of relative links extend it. Other tools' config files are not read.
3. **Three entry kinds.** Every entry is `always`, `scoped` or `reference`, so consumers read only what applies; the index is never truncated.
4. **The repository tunes it.** `instructions.include`, `instructions.reference` and `instructions.exclude` in the tracked `.factory/config.json` add, demote and drop files. `factory init` does not seed them.
5. **Recorded at every preflight.** `factory instructions-record` writes `instructions.json` into the run folder and a summary into run state, reports the delta on a re-record, and never stops a run. The orchestrator reads the `always` entries at the recorded ref and takes documented build and test commands from every root-scope entry.

## Considered options

- **Rely on harness auto-loading**: no new code. But coverage differs per harness, worktree files are usually not loaded, and nothing records what applied.
- **Read only root `CLAUDE.md` and `AGENTS.md`** (the previous behaviour): simple. But nested files, other tools' rules and governance documents are missed.
- **Scan the working tree**: sees local edits. But the result would depend on the checkout, not the commit, and could include untracked files.
- **Own scanner over git objects** (chosen): harness-independent, reproducible and recordable.

## Consequences

The catalogue lives in `core/` as data about consuming repositories and must be re-checked against each tool's documentation when it changes. Role and reviewer consumption of the index is a later feature; until then only the orchestrator reads it.
