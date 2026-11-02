# Brief: Per-project deep and standard models (017)

## Feature

The factory's deep and standard models become selectable per project. A project carries its own model configuration file; a run in that project resolves the deep/standard selections for that project. Different projects can pin different model structures. A project without the configuration (or without the relevant keys) falls back to the existing chain: the user's `${FACTORY_HOME}/config.json`, then the adapter defaults rendered into the installed agents.

## Decisions settled in grilling (2026-11-02)

- **Project config location (Q1)**: `<repo>/.factory/config.json` — same filename as the user-level config, inside a dot-folder in the repo. Symmetric with `${FACTORY_HOME}/config.json`, gitignore-able, out of the way.
- **Schema and precedence (Q2)**: identical schema to the user config: `{"models": {"<harness>": {"deep": "...", "standard": "..."}}}`. Cascade: **project → user global → adapter default**, merged per key (per tier). Model IDs are harness dialects, so the harness key stays. An empty-string model value inherits the session's model (existing convention preserved).
- **Effect path (Q3)**: spawn-time pass-through. The orchestrator resolves the cascade once at preflight and passes the tier→model mapping into every `SPAWN`/`SPAWN_PARALLEL` as the model to run the child agent with. No re-render, no reinstall; editing the file takes effect on the next run. Harnesses whose spawn mechanism cannot take a model disclose that at preflight (project models cannot apply there) and continue on the baked (installed) selections — never silent.
- **Malformed or unresolvable config (Q4)**: stop the run (preflight stop, same spirit as FR-022's install abort and the existing model-inspection stop), naming the exact file, the parse error or the unresolvable selection, and the correction step. Silent fallback would mask a typo'd model ID for the whole run.
- **State and resume (Q5)**: resolved `models` (per harness tier→ID) plus per-tier `source` labels (`project` | `user` | `adapter`) are recorded in run state at preflight. Resume re-resolves every preflight (existing behavior for skills); values that changed are disclosed as a delta, and the run continues with the new values. No freezing.
- **`factory models` command (Q6)**: new read command in the state CLI: `factory models [--json]` prints the effective per-role cascade for the current repo with each row's source labeled. One resolver, testable; preflight and `/factory init` build on it instead of re-implementing resolution in skill prose.
- **`/factory init` (Q7)**: creates the **project** config `<repo>/.factory/config.json`, seeded with all five harnesses (`claude-code`, `codex`, `copilot`, `opencode`, `zcode`) and both tiers. Global config untouched (it means "override"; seeding it would hide the cascade). `--global` flag reserved, not built (YAGNI).
- **Seed values (Q8)**: the **effective** values a run in this repo would use today (adapter defaults merged with the user's existing global overrides). Init therefore changes no behavior; editing any seeded line becomes an explicit override. Init's printed output labels each value's source (`adapter` or `user`).
- **Knowing the default after editing (Q9)**: init also writes `.factory/config.README.md` beside the config: schema, precedence, the seeded defaults table with sources, and how to restore. Plain Markdown sidecar; JSONC rejected (parsers reject comments).
- **Existing file (Q10)**: init refuses (names the path, non-zero exit) and never clobbers hand edits. No merge, no `--force` until the friction is real.
- **Invocation (Q11)**: new route inside the existing `/factory` skill (`init` alongside `resume`/`improve`) that runs `SHELL: python3 <F>/bin/factory init`, shows the printed table, and stops. Logic lives in the CLI (`factory_cli`), not in agent prose.
- **Validation of seeded IDs (Q12)**: init does not probe model inventories (honest cross-harness verification is impossible at init time). It prints a note that values are unverified until a run's preflight, which keeps the existing model-inspection behavior.

## Out of scope

- No changes to `tools/render.py` merge logic or the canonical dist render (FR-002 stands: dist never reads user or project config).
- No per-project re-render or install.sh changes.
- No global-config seeding, no JSONC, no `--force`, no `--global` (kept in reserve).
- No new model inventory APIs; per-adapter inspection guidance stays as is.
