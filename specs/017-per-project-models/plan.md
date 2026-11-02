# Implementation Plan: Per-project deep and standard models

**Branch**: `017-per-project-models` | **Date**: 2026-11-02 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/017-per-project-models/spec.md`; settled decisions Q1-Q12 in `factory/brief.md`.

## Summary

Add a project model layer `<repo>/.factory/config.json` above the user config and the adapter defaults. One resolver in the state CLI produces the per-harness, per-tier model plus its source (`project` | `user` | `adapter`). Preflight records it in run state and passes the tier's model into every `SPAWN`/`SPAWN_PARALLEL`. Two new CLI commands: `factory models [--json]` (report) and `factory init` (seed the project config and its README sidecar). `tools/render.py`, dist and `install.sh` stay unchanged.

## Technical Context

**Language/Version**: Python 3 (standard library only), Markdown skill prose.

**Primary Dependencies**: none new.

**Storage**: JSON files: `<repo>/.factory/config.json`, `${FACTORY_HOME}/config.json`, run `state.json` (v5, additive `models` block).

**Testing**: `python3 -m unittest discover -s tools/tests -t .` (existing runner).

**Target Platform**: macOS/Linux shells running the five harnesses.

**Project Type**: CLI plus agent skill prose.

**Performance Goals**: N/A (reads three small files once per preflight).

**Constraints**: Harness-neutral core (constitution II); no render/install change (FR-017); malformed config stops the run, never silent (FR-008); init never clobbers (FR-014).

**Scale/Scope**: 5 harnesses x 2 tiers.

### Adapter defaults at runtime

The installed skill (`<harness skills>/factory/`) ships `SKILL.md`, `bin/`, `references/` and `roles/` only; `adapters/*/adapter.json` is not installed. The CLI therefore cannot read adapter defaults from `adapters/` at run time, and init must seed all five harnesses. Decided (plan Q1, option A): a checked-in data file `core/skills/factory/bin/factory_cli/adapter_models.json` mapping each harness to its `{deep, standard}` defaults, kept equal to every `adapters/<name>/adapter.json` `"models"` by a parity test in `tools/tests/test_render_models.py`. It is copied with `bin/` by the existing render/install, so render.py, dist and install.sh stay unchanged. It is the CLI's only run-time source of adapter defaults; `adapters/*/adapter.json` stays the authored source, and the parity test fails on any drift between the two. `copilot` and `zcode` pin no models (`"models": {}`; their `harness.md` says "not set by default"), so `adapter_models.json` carries `"copilot": {"deep": "", "standard": ""}` and `"zcode": {"deep": "", "standard": ""}`: empty string = inherit the session's model, today's behaviour. The parity test treats a tier absent from `adapter.json` `"models"` as `""` and asserts equality including empties; `factory init` seeds those empty strings with source `adapter`.

### Spawn-time model support per harness

| Harness | Spawn takes a model | Adapter file change |
|---|---|---|
| claude-code | yes (Agent tool `model`) | `adapters/claude-code/harness.md`: pass resolved model on spawn |
| opencode | yes (subagent tool `model`) | `adapters/opencode/harness.md`: pass resolved model on spawn |
| codex | no | `adapters/codex/harness.md`: disclosure at preflight, run on installed selections |
| copilot | no | `adapters/copilot/harness.md`: disclosure |
| zcode | no | `adapters/zcode/harness.md`: disclosure |

Support is a static per-adapter fact (spec assumption); it lives in each `harness.md`, not in core (constitution II).

## Constitution Check

- **I. Design First**: PASS. `DESIGN.md` gains the project model layer, cascade, CLI commands and init route before core/adapter edits (first task).
- **II. Harness-Neutral Core**: PASS. Core prose uses `SPAWN`/`SHELL` and refers to "the resolved model"; harness tool parameters live in `adapters/*/harness.md`. `adapter_models.json` is CLI data keyed by harness name, like `config.json`, not a tool, path or command.
- **III. Generated Dist**: PASS. No render.py change; dist stays reproducible; nothing in dist reads user/project config.
- **IV. Stateless Agents**: PASS. Resolution recorded in `state.json`; spawned agents receive the model as an input.
- **V. Simplicity and Reuse**: PASS. One resolver module; no flags beyond `--json`.

## Project Structure

### Documentation (this feature)

```text
specs/017-per-project-models/
├── plan.md
├── spec.md
└── tasks.md   (tasks stage)
```

### Source Code (repository root)

```text
core/skills/factory/bin/factory_cli/
├── models.py              # NEW resolver, report, init
├── adapter_models.json    # NEW adapter default data (Q1)
├── cli.py                 # models / init dispatch + USAGE
└── commands.py            # read_config() unchanged; models.py owns strict reading
core/skills/factory/SKILL.md            # step 0 init route; preflight resolve/record/delta/disclose; SPAWN model
core/skills/factory/references/verbs.md # SPAWN carries resolved model
core/skills/factory/references/state.md # v5 additive "models" block
adapters/*/harness.md                   # pass-through or disclosure
DESIGN.md
tools/tests/test_models.py              # NEW
tools/tests/test_render_models.py       # parity test added
```

**Structure Decision**: New module `factory_cli/models.py` rather than a section in `commands.py`: `commands.py` is already over 1500 lines of run/state commands; model resolution is one coherent concern with three callers (preflight, `models`, `init`) and its own strict error policy (raise, naming the file), unlike `read_config()` which returns `{}` on malformed input for budget use.

### New files, abstractions, dependencies

- `core/skills/factory/bin/factory_cli/models.py` - file - single resolver required by FR-004; keeps strict config errors out of `commands.py`.
- `core/skills/factory/bin/factory_cli/adapter_models.json` - file - adapter defaults must be readable by the installed CLI, which has no `adapters/` (decided Q1); parity-tested against `adapters/*/adapter.json`.
- `tools/tests/test_models.py` - file - tests for the new module and commands.
- `resolve(repo, home) -> {harness: {tier: (model, source)}}` - abstraction - one resolver shared by preflight, report and init.
- `ModelConfigError(path, detail)` - abstraction - dedicated error class so CLI exit paths can name the offending file distinctly from generic `CLIError(1)`.
- Dependencies: none.

### Design

- `resolve(repo, home)`: for each harness in `adapter_models.json`, per tier `deep`/`standard`: project value if the key is present, else user, else adapter. Empty string is a valid value (inherit session model). Missing file, missing `models`, missing harness entry: fall through. Invalid JSON, non-object `models`/harness entry, unknown harness key, unknown tier key or non-string value: raise `ModelConfigError(path, detail)`; the CLI exits non-zero with `<path>: <detail>` and the fix line `Fix the file or delete it to fall back to the next layer.`
- Unknown harness keys (not in `adapter_models.json`) in project or user config are a malformed-config error, never ignored: the detail names the key and the known harnesses. Unknown tier keys likewise name the key and `deep`, `standard`.
- `<repo>` is the main checkout root: parent of `git rev-parse --path-format=absolute --git-common-dir` (`main_repo(cwd)` / `state.repo`), never the worktree, so a run started from a worktree reads the main checkout's `.factory/config.json`.
- `factory models [--json]`: table `harness tier model source`; `--json` prints `{harness: {tier: {"model", "source"}}}`. Exit 1 on `ModelConfigError`.
- `factory init`: refuse (exit 1, name path) if `<repo>/.factory/config.json` exists, keyed on `config.json` alone (a missing README does not unlock init; an existing README without `config.json` is rewritten). Otherwise resolve with the project layer ignored, write `config.json` (sorted keys, all five harnesses, both tiers) and `config.README.md` (schema, precedence, defaults table with sources, restore instructions), print the table with `adapter`/`user` sources and the "unverified until a run's preflight" note. Never writes `${FACTORY_HOME}`. Writes go to a temp file then `os.replace` (no partial config on failure).
- State: preflight writes `models: {resolved: {deep, standard}, source: {deep, standard}}` for the run's harness. On resume, compare with the recorded block, disclose each changed tier `old (source) -> new (source)`, overwrite, continue.
- Preflight on a no-spawn-model harness with any `project`/`user` source: disclose and continue on installed selections.

### Quality constraints

- Security: config is local user data; values are passed as model IDs only, never executed. Paths are fixed (`.factory/config.json`), no user path input.
- Data integrity: init refuses existing config; atomic replace; global config never written.
- Errors: every malformed case names file, error and fix (FR-008, SC-003).
- Compatibility: repos without `.factory/` resolve exactly as today (SC-002); state `models` block is additive to v5.

## Test seams (fix round 1 scope — orchestrator-confirmed 2026-11-02)

Confirmed by the user (relay, 2026-11-02) as the fix-round-1 seam scope for verdict round 1, supplementing the seams above:

- `factory_cli` state writer: new write command `models-record` (dispatch + cmd_*, validate models block shape {resolved:{deep,standard}, source:{deep,standard}}, source ∈ project|user|adapter; reject unknown source; atomic write + commit; usage error on malformed JSON payload). SKILL.md preflight prose updated to call it (FR-005, FR-009).
- Role→tier map: rendered skill gains a machine-readable role→tier map (preferred: roles/tiers.json emitted by render.py — FR-017's no-render-change rule is explicitly relaxed by the user for this one additive output only; render stays otherwise untouched). Test: rendered tree contains the map matching core/roles frontmatter for all five harnesses.
- opencode spawn-model prose: adapters/opencode/harness.md wording must state the truthful inheritance mechanism for an empty resolved model on a model-pinned installed agent (FR-003 accuracy fix); verified against OpenCode docs/behavior before wording.
- Resolver/init hardening failure paths (test_models.py): symlinked `.factory/` dir refused (init); symlinked or non-regular config file refused (resolve); config file over the 1 MiB cap refused (resolve); control-character model values refused (resolve + table sanitize); init publish race: existing destination at publish → refusal with temp cleanup; init publish failure leaves no artifacts (retryable).
- Full-suite bar stays: 343 tests, 342 pass, only the pre-existing design-to-code permissions failure.

## Test seams

- Seam: `factory_cli.models.resolve` - cascade per tier, empty-string value, missing file/key/harness fall-through. Failure paths: invalid JSON in project config; invalid JSON in user config; non-object `models` or harness entry; unknown harness key; unknown tier key; non-string tier value.
- Seam: `bin/factory` CLI command surface, `models [--json]` - table and JSON output with source labels. Failure paths: malformed config exits non-zero naming file and fix.
- Seam: `bin/factory` CLI command surface, `init` - seeded five harnesses x two tiers with effective values, README written, global config untouched, post-init `models` values unchanged. Failure paths: existing `config.json` refused with non-zero exit and byte-identical file; malformed user config stops init.
- Seam: `adapter_models.json` parity with `adapters/*/adapter.json` (`tools/tests/test_render_models.py`). Failure paths: none.
- Exempt: `DESIGN.md`, `core/skills/factory/SKILL.md`, `references/verbs.md`, `references/state.md` prose - documentation only.
- Exempt: `adapters/*/harness.md` - documentation only.
- Overridden: none

Confirmed: 2026-11-02 - Q13 accepted - seams: factory_cli.models.resolve, bin/factory models [--json], bin/factory init, adapter_models.json parity; failure paths: resolve -> invalid JSON in project config, invalid JSON in user config, non-object models or harness entry, unknown harness key, unknown tier key, non-string tier value; models -> malformed config exits non-zero naming file and fix; init -> existing config.json refused with non-zero exit and byte-identical file, malformed user config stops init; parity -> none (drift fails the test)

Superseded (remediation 1 added resolve failure path "unknown harness key"; replaced by Q13 above): 2026-11-02 - Q2 accepted - seams: factory_cli.models.resolve, bin/factory models [--json], bin/factory init, adapter_models.json parity; failure paths: resolve -> invalid JSON in project config, invalid JSON in user config, non-object models or harness entry, unknown tier key, non-string tier value; models -> malformed config exits non-zero naming file and fix; init -> existing config.json refused with non-zero exit and byte-identical file, malformed user config stops init; parity -> none (drift fails the test)

## Complexity Tracking

None.
