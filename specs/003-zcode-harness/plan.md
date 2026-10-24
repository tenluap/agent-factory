# Implementation Plan: ZCode Harness Adapter

**Branch**: `003-zcode-harness` | **Date**: 2026-10-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-zcode-harness/spec.md`

## Summary

Add a fifth adapter, `zcode`, as one new folder `adapters/zcode/` holding `adapter.json` (install paths,
Markdown agent format, fields `name`/`description`/`tools` only, access lists, empty models) and
`harness.md` (recognition line resting on `ZCODE_HOME`/`~/.zcode`, tier 1 verb mappings, setup values,
`impeccable_provider: codex`, notes), then render every harness and commit the whole of `dist/`. The
`/dist/` line is removed from `.gitignore` and all five harnesses' rendered output is tracked from this
change on (FR-018, ADR 0005), which turns `git diff --exit-code -- dist/` into a gate that can fail.
Documentation gains a ZCode row and requirement in `README.md`, ZCode in `DESIGN.md`'s adapter lists plus a
generalised spec-kit setup line (FR-016), and ZCode in `CONTEXT.md`'s Harness definition. No file under
`core/` changes (FR-017). All harness facts are verified in [research.md](./research.md).

## Technical Context

**Language/Version**: Markdown and JSON data files; Python 3 for the existing renderer (`tools/render.py`),
Bash for `install.sh`. No code change to either.

**Primary Dependencies**: none added. Target harness: ZCode 3.16.x (desktop app and bundled
`glm/zcode.cjs`). External tools named by the adapter text: specify-cli 1.1.0, impeccable.

**Storage**: files only - `adapters/zcode/`, generated and now tracked `dist/` (all five harnesses).

**Testing**: the repository's documented build and test commands, run in the canonical render environment
below: `python3 tools/render.py <harness>` for every harness, then `git diff --exit-code -- dist/` against
the tracked distribution; plus a frontmatter parse check over `dist/zcode/agents/*.md`.

**Target Platform**: developer machines running any supported harness; the rendered output targets ZCode.

**Project Type**: single repository that generates per-harness distributions.

**Performance Goals**: none (a render takes under a second per harness).

**Constraints**: `core/` stays harness-neutral; `dist/` is generated and committed in the same change as its
source, and must be tracked (not ignored) for the commit and the difference check to work; other harnesses'
output must be unchanged apart from the new `references/harness/zcode.md` the shared skill carries.
**Canonical render environment**: `tools/render.py` resolves each adapter's `{home}` from its home
environment variable and merges `${FACTORY_HOME}/config.json` model overrides into the frontmatter, so the
output is environment-dependent. Every render whose result is committed, and every run of the Seam 4 gate,
is therefore wrapped in
`env -u CLAUDE_HOME -u CODEX_HOME -u ZCODE_HOME -u XDG_CONFIG_HOME -u FACTORY_HOME …` (FR-018). A local
render or install with any of those set (for example the `ZCODE_HOME=/tmp/zc` override check) rewrites the
tracked tree and must be followed by `git checkout -- dist/` or a canonical re-render.

**Scale/Scope**: one adapter folder (2 files), five rendered distributions first brought under version
control (ZCode's 9 role agents + skill tree, plus the four existing harnesses' trees), `.gitignore` and
3 documentation files touched.

## Constitution Check

*GATE: passed before Phase 0; re-checked after Phase 1 design - still passing.*

- **I. Design First**: `DESIGN.md` is edited in the same change before the adapter is relied on: the
  adapter lists gain ZCode, and the spec-kit setup line (`DESIGN.md:69`) is generalised to
  `specify init --here <harness.speckit_init>`, whose argument shape each adapter states, so the record and
  the ZCode adapter's `--integration zcode --integration-options="--skills"` agree. No other adapter's
  recorded setup changes (FR-016). Pass.
- **II. Harness-Neutral Core**: no `core/` file is touched; every ZCode name lives in `adapters/zcode/`.
  Pass (FR-017).
- **III. Generated Dist (NON-NEGOTIABLE)**: every harness is re-rendered and the whole of `dist/` committed
  with the source. The `/dist/` line is removed from `.gitignore` and all five harnesses' output is added to
  version control in this change (FR-018, ADR 0005), so a plain `git add dist/` works and
  `git diff --exit-code -- dist/` after a fresh render is a check that reports differences when source and
  render diverge. Pass.
- **IV. Stateless Agents**: unchanged; the adapter adds no run state. Pass.
- **V. Simplicity and Reuse**: no new renderer feature, no new field, no new verb - the existing
  Markdown-agent path covers ZCode. Pass; reasons for each new file are listed below.

**Complexity Tracking**: no violations, table omitted.

## Research corrections folded into the spec

No open deviation remains: both plan-time findings were folded back into `spec.md`, so the plan builds what
the spec says.

- **R2 → FR-010 (closed)**: `RESOLVE` is `<repo>/.zcode/skills/`, `<repo>/.agents/skills/`,
  `~/.zcode/skills/`, `~/.agents/skills/`. The `.claude` roots the ZCode 3.16.3 bundle never reads were
  removed from FR-010 and its edge case during clarify; the plan matches the corrected FR-010.
- **R4 → FR-011 (closed)**: `speckit_init` is `--integration zcode --integration-options="--skills"`, not
  the brief's `--ai codex --ai-skills`: specify-cli 1.1.0 removed `--ai` and ships a native ZCode
  integration. FR-011 is worded neutrally and the spec's assumption now records the correction;
  `DESIGN.md:69` is generalised in this change so the design record agrees (FR-016).

## Project Structure

### Documentation (this feature)

```text
specs/003-zcode-harness/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── tasks.md          # /speckit-tasks output
```

### Source Code (repository root)

```text
adapters/zcode/
├── adapter.json      # new: install paths, agent format, fields, access, models
└── harness.md        # new: recognition, tier, verbs, setup values, notes

dist/zcode/           # new: generated by tools/render.py (skill/ + agents/factory-*.md)
dist/<other four>/    # newly tracked: re-rendered claude-code, codex, copilot, opencode trees

.gitignore            # the `/dist/` line is removed (FR-018)
README.md             # harness table row, requirements line
DESIGN.md             # harness model list, "Adapters today", generalised spec-kit setup line
CONTEXT.md            # Harness definition (and docs/adr/0005 records the tracked-dist decision)
```

**Structure Decision**: the existing per-adapter layout. A new harness is one folder under `adapters/`
(`DESIGN.md`, "Harness model"), so no structural change is needed.

### Adapter values (detail in [data-model.md](./data-model.md))

`name` zcode · `home` env `ZCODE_HOME`, default `~/.zcode` · `skill_dir` `{home}/skills/factory` ·
`agent_dir` `{home}/agents` · `agent_file` `factory-{role}.md` · `agent_format` markdown ·
fields `name: factory-{role}`, `description: {description}` · access read `Read, Grep, Glob, Bash`,
write `Read, Edit, Write, Bash, Grep, Glob` · `models` `{"deep": "", "standard": ""}` (the key is required
by `load_adapter`'s user-override update; empty values make agents inherit the session model, so no `model`
key is rendered). The rendered frontmatter is therefore exactly `name`, `description` and `tools` — the
Claude Code set and nothing more (FR-004).

## Test seams

Seams put under test - the public seam of this change is the renderer's output for the new adapter:

- **Seam 1 - `python3 tools/render.py --list`**: includes `zcode`. Red before
  `adapters/zcode/adapter.json` exists.
- **Seam 2 - `python3 tools/render.py zcode`**: exits 0 and produces `dist/zcode/skill/` plus one
  `dist/zcode/agents/factory-<role>.md` for every file in `core/roles/` (9). Red before the adapter exists
  (`unknown harness 'zcode'`). **Both adapter files are written together**: `known()` counts any folder
  holding `adapter.json`, and `render()` copies *every* known adapter's `harness.md` into *every* harness's
  skill tree, so an `adapters/zcode/adapter.json` without `adapters/zcode/harness.md` makes every
  harness's render fail with `FileNotFoundError`. Seam 2 goes green only once both files exist, and no
  ordered step may leave the folder half-built (tasks.md, Phase 3).
- **Seam 3 - frontmatter of `dist/zcode/agents/factory-*.md`**: every file has parseable YAML frontmatter
  carrying exactly `name`, `description` and `tools` and no other key (FR-004), with the role's access
  list. Asserted over a canonical render: a `models.zcode` override in `${FACTORY_HOME}/config.json` would
  add a `model:` key and break the exact key-set assertion, which is one more reason the committed render
  unsets `FACTORY_HOME`. Red before the adapter exists (no files to parse).
- **Seam 4 - canonical render of every harness, then `git diff --exit-code -- dist/`**: the repository's own
  test, made real by FR-018. Every render in this seam runs in the canonical environment above
  (`env -u CLAUDE_HOME -u CODEX_HOME -u ZCODE_HOME -u XDG_CONFIG_HOME -u FACTORY_HOME` around the render
  loop); without it a contributor with any of those set sees spurious differences, because the rendered
  skill paths and any `models.<harness>` override are substituted into the output. The order is: remove
  `/dist/` from `.gitignore`, `git add dist/` and commit the current canonical
  render of all five harnesses, then re-render canonically and run the check. Because `dist/` is tracked, the command
  reports every divergence between the committed distribution and a fresh render and exits non-zero
  (SC-003, SC-006). Red proof: with the adapter built but `dist/` not re-rendered and re-committed (for
  example after editing `adapters/zcode/harness.md`, which every harness's skill copies), the same command
  fails; before FR-018 it passed vacuously on an ignored directory.

Checks run with the repository's documented commands (`tools/render.py` plus `git diff --exit-code -- dist/`),
with Seam 3 as a `python3 -c` assertion over the rendered files. The repository has a test runner, so none
is introduced.

Exemptions (documentation, configuration or generated output only):

- `Exempt: adapters/zcode/harness.md - documentation only - prose the orchestrator reads at runtime; its
  only build-time effect, being copied into every skill, is covered by Seam 2.`
- `Exempt: README.md - documentation only.`
- `Exempt: DESIGN.md - documentation only.`
- `Exempt: CONTEXT.md - documentation only.`
- `Exempt: dist/** - generated output for every harness, produced by the render and guarded by Seam 4,
  never hand-written (the render rewrites every harness's skill tree, so the exemption covers all five).`
- `Exempt: .gitignore - configuration only - one removed line; its effect is what makes Seam 4 able to
  fail, and Seam 4 covers it.`
- `Exempt: docs/adr/0005-the-rendered-distribution-is-tracked-in-git.md - documentation only.`
- `Exempt: specs/003-zcode-harness/** - documentation only - this feature's own spec artifacts.`

`Overridden: none`

## New files, abstractions and dependencies (ENG-10)

- `adapters/zcode/adapter.json - file - the renderer needs one descriptor per harness; without it
  render.py cannot know ZCode's install paths, agent format or access lists.`
- `adapters/zcode/harness.md - file - the orchestrator needs one harness document per adapter to recognise
  ZCode and map every neutral verb; it is also copied into every harness's skill.`
- `dist/** - file - generated build output that Constitution III requires to be committed with its source;
  all five harnesses' trees are newly tracked because an ignored dist/ makes that requirement
  uncheckable (FR-018, ADR 0005).`
- `docs/adr/0005-the-rendered-distribution-is-tracked-in-git.md - file - records why dist/ stopped being
  ignored, so the reversal of a repo-wide rule is traceable.`
- `abstraction - none - the existing Markdown agent format, fields, access and models mechanisms cover
  ZCode unchanged.`
- `dependency - none.`

Note: `docs/adr/0005-the-rendered-distribution-is-tracked-in-git.md` and the ZCode line in `CONTEXT.md`
were already written on this branch by the domain-modeling step, so no task creates them — T001 implements
the ADR's decision and T014 verifies the `CONTEXT.md` line (tasks.md, Notes). They are listed here because
they are outputs of this change, not because they are still to be written.

## Phase 1 outputs

- [data-model.md](./data-model.md): adapter descriptor fields, harness document sections, rendered agent
  file shape, tracked distribution.
- [quickstart.md](./quickstart.md): track `dist/`, build, gate, install, resume check and validate the
  ZCode adapter end to end.
- `contracts/`: not produced - the only interfaces are the adapter descriptor consumed by `tools/render.py`
  and the harness document consumed by the orchestrator, both fully specified in `data-model.md`.
