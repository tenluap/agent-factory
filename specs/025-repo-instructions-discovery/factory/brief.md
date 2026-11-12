# Brief: 025-repo-instructions-discovery

## Feature

Give the factory its own discovery of repo instructions (run 1 of the source brief below, "Run 1: discovery"). Add a deterministic, stdlib-only scanner to the factory CLI that reads git objects at the run's ref and indexes tracked agent instruction files at any depth from a table-driven catalogue, governance documents, `@path` imports and one-hop links; classify each entry as `always`, `scoped` or `reference` with its scope, size, hash and title; read `instructions.include`, `instructions.reference` and `instructions.exclude` from `<repo>/.factory/config.json`; add the read-only `factory instructions` report and the `factory instructions-record` writer, which stores a summary in run state, writes the index file in the run folder and reports the delta on a re-record; call the writer at every preflight (new run, resume, adopt) after `profile-record` and disclose counts, sizes, notes, the over-32-KiB warning and the no-instructions case; have the orchestrator read the `always` entries at preflight and grill and take documented build and test commands from every root-scope entry; record the new terms in `CONTEXT.md` and the decision as an ADR; add this repository's own config lists; and cover the scanner with unit tests over fixture trees.

Chain: **full** (cruise run; stops at the approver).

## Decisions settled at grill (cruise, self-answered; on the approver veto list)

- Chain: full. Source brief Q27 settles both runs on the full chain; its run-1 invocation is `/factory --full`.
- Branch and spec number: `025-repo-instructions-discovery`. The source brief's "spec 024" is taken by the local branch `024-orchestrator-gaps` (an unfinished factory run parked at its approver) and by `origin/024-windows-install`. Read the source brief's "spec 024" as this run, and "spec 025" (run 2) as a later number.
- ADR number: **0020**, not 0019. `origin/024-windows-install` (no PR yet) already adds `docs/adr/0019-the-installer-is-a-python-module.md`. If 0020 is also taken at implement time, use the next number free on `origin/main` and every remote branch. Everywhere the source brief says "ADR 0019", read the ADR this run writes.
- Source brief handling: `docs/repo-instructions-brief.md` is staged only in the user's main checkout and is not on `origin/main`, so it is absent from the worktree. The run neither adds nor edits that file. Its full text is reproduced verbatim below and is the settled design for this run. `spec.md` and `plan.md` must be self-contained; they may cite the doc path as background only.
- Scope: run 1 (discovery) only. Every run-2 item (index path in spawn inputs, the shared reference and pointer lines, planner sorting with `Overridden:`/`Not applied:` lines and relay questions, `code-standards` reading the index, the breach severity rule, the approver's changed-instruction-files list, the bench case and golden-run lines) stays out of scope.
- The source brief's "Open points for the runs" that bear on run 1 (whether the scanner reads other tools' config for extra file names; the exact ADR directory patterns; the name and format of the index file) are settled at clarify/plan, as the source brief directs. The shared reference's name is run 2's.
- Commands: this repository has no root `CLAUDE.md` or `AGENTS.md`; build and test come from the README's CI line and `.github/workflows/ci.yml` (decision `setup-commands`). Build: render all five harnesses into a temporary `FACTORY_HOME`, fail if `dist/` is tracked, `bash -n install.sh`. Test: `python3 -m unittest discover -s tools`.
- Stack profile: the detector found no known stack (stdlib Python, no marker files it recognises). No UI work and no design context.
- Repository conventions the source brief names: record each behaviour change in `DESIGN.md` first; follow `CONTEXT.md` terms; ADRs under `docs/adr/`.

## Source brief (verbatim copy of docs/repo-instructions-brief.md, staged in the main checkout on 11 November 2026)

# Repo instructions brief: the factory reads the repository's own rules

**Prepared:** 11 November 2026
**Baseline:** commit `0c3bf71` (main)
**Status:** design settled in a grilling session (decisions Q1–Q28 below). Nothing is implemented yet. Two factory runs deliver it; each records its behaviour change in `DESIGN.md` first.

## What is wrong today

- The orchestrator reads only the root `CLAUDE.md` and `AGENTS.md`, and only for build and test commands (`core/skills/factory/SKILL.md`, step 1, item 5).
- `code-standards` is the only role told to collect the repository's standards. It does so at review time, from a fixed list of names, with no nested files and no other tools' files (`core/roles/code-standards.md`).
- `spec-builder`, `code-build`, `design-to-code` and `fixer` have no step that reads repository instructions. They depend on whatever the harness loads by itself.
- ENG-11 says the repository's documented conventions beat the factory's rules (`core/skills/factory/references/engineering.md`). No role is told where to find those conventions.
- Roles work in a sibling worktree created from `origin/<default-branch>`, outside the session's directory (`core/skills/factory/SKILL.md`, step 4).

Two failures follow:

- **Pain A.** Writing roles break repository conventions. The breach is found late, in review, or not at all.
- **Pain B.** Instruction files outside the root, or under names the factory does not look for, are never read.

No specific run was named as the trigger, so acceptance rests on fixtures (Q23).

## What the harnesses load by themselves

Researched from official documentation on 11 November 2026 by a research sub-agent. "Inferred" means read from the wording of the discovery rules, not stated outright. Re-check each source before relying on a cell.

| Harness | Files read | Custom subagent gets them | Files inside the sibling worktree |
|---|---|---|---|
| Claude Code | `CLAUDE.md` family and `.claude/rules/`; `AGENTS.md` only when no `CLAUDE.md` exists (v2.1.277+) | Yes, the main checkout's copy | No (inferred); `--add-dir` needs `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1` and still skips `AGENTS.md` and path rules |
| OpenCode V2 | `AGENTS.md`; `instructions` globs in `opencode.json` | Likely yes (inferred) | No (inferred); lazy discovery covers only paths below the workspace |
| Codex | `AGENTS.md` chain from the project root to the working directory; nothing below it; 32 KiB combined cap | Undocumented | No (inferred) |
| Copilot CLI | `.github/copilot-instructions.md`, `*.instructions.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.claude/rules/` | No, unless the agent file sets `include-custom-instructions: true` | No, unless `COPILOT_CUSTOM_INSTRUCTIONS_DIRS`; subagents do not inherit it |
| ZCode | Root `AGENTS.md` only; no nesting; `CLAUDE.md` not read | Yes since v3.7.1 | Unverified |

Consequences:

- The same repository yields five different instruction sets. A repository with only `CLAUDE.md` is invisible on Codex, OpenCode V2 and ZCode.
- Nested and path-scoped files load on no harness, because roles read files outside the session's directory.
- Where a subagent does inherit, it gets the main checkout's copy: whatever branch and local edits sit there, not the run's commit.
- No cross-tool index standard for repository instruction files exists. `llms.txt` targets websites.

Sources:

- Claude Code: <https://code.claude.com/docs/en/memory>, <https://code.claude.com/docs/en/sub-agents#what-loads-at-startup>, <https://code.claude.com/docs/en/worktrees#isolate-subagents-with-worktrees>
- OpenCode: <https://opencode.ai/docs/instructions/>, <https://opencode.ai/docs/rules/>, <https://opencode.ai/docs/agents/>
- Codex: <https://developers.openai.com/codex/guides/agents-md>, <https://developers.openai.com/codex/subagents>
- Copilot: <https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions>, <https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference>, <https://code.visualstudio.com/docs/agents/reference/custom-instructions-reference.md>
- ZCode: <https://zcode.z.ai/en/docs/agents#project-instructions>, <https://zcode.z.ai/en/docs/subagents#agents-md>
- Index conventions: <https://llmstxt.org/>, <https://agents.md/>

## Design

### Discovery

- A deterministic scan in the factory CLI, stdlib Python, beside `detect.py`.
- It reads git objects at the run's ref: `base` for a new run, the adoption source ref for adopt, the worktree `HEAD` after step 4. Only tracked files count.
- It finds agent instruction files at any depth from a table-driven catalogue, governance documents (`CONTRIBUTING*`, `.specify/memory/constitution.md`, ADR directories), `@path` imports up to 4 hops, and relative links one hop.
- `<repo>/.factory/config.json` carries three glob lists: `instructions.include` (kind `always`, root scope), `instructions.reference` and `instructions.exclude`.
- It runs at every preflight: new run, resume and adopt. Nothing is cached across runs.

### Instruction index

One entry per file: path, kind, scope, size, hash, title.

| Kind | Sources | Duty |
|---|---|---|
| `always` | Root agent files, the constitution, `CONTRIBUTING*`, rule files flagged always-apply, their `@path` imports, `instructions.include` | Every consuming role reads all of them, in full, at start |
| `scoped` | Nested agent files (scope: their own directory subtree); rule files with glob front matter (`paths`, `applyTo`, `globs`) | Read before creating, editing or reviewing a file in scope |
| `reference` | ADR directories; files that instruction files link to; on-demand rule files; `instructions.reference` | Listed with a title; read when relevant to the work |

- The closest scope wins: nested beats root, path-scoped beats always-on.
- The index is never truncated. When the `always` entries total more than 32 KiB, preflight warns and names the largest files.

### CLI, state and preflight

- `factory instructions [--repo] [--ref]` is a read-only report. It needs no run.
- `factory instructions-record` is the writer. It stores a summary in state (ref, counts, combined hash), writes the index file in the run folder (beside the pending file before the worktree exists), and reports the delta on a re-record. `drop` removes the index file before the PR.
- Preflight (step 1, item 5) calls the writer after `profile-record` and discloses counts, sizes, the delta and any notes.
- A repository with no instruction files is disclosed, and the run continues. The disclosure names the `create-project-agents-file` skill as a hint.
- The orchestrator reads the `always` entries at preflight and at grill. Documented build and test commands come from every root-scope entry. `commands` keeps its two slots.

### Consumption

- The orchestrator passes the index path to every spawn. One shared reference states the read duty. Each role file gets one pointer line.
- Consumers: `spec-builder`, `code-build`, `design-to-code`, `fixer`, the five reviewers and `review-judge`. Not `retro`, not `facets-advisor`, not standalone `design-to-code`.
- The repository wins on code conventions (ENG-11). The factory keeps its commit, branch and PR mechanics and all its gates.
- The planner sorts directives once, at plan:
  - A code convention is binding.
  - A convention that beats a factory rule is recorded as `Overridden: ENG-n - <repo rule that wins>`.
  - A delivery convention the factory does not adopt is recorded as `Not applied: <repo rule> - <factory mechanic that wins>`.
  - "Ask a human before X" becomes a relay question when the plan involves X.
  - A same-scope contradiction between two instruction files becomes one ordinary relay question, recommending the rule the neighbouring code follows.
  - An assistant-behaviour directive (tone, reply language, tool choice) is ignored with no record.

### Review

- `code-standards` takes its standards list from the index instead of its fixed list of names.
- A breach of an explicit, checkable rule in an indexed file is a documented-contract failure. It is blocking, rated by consequence, and not subject to the judgement-call ceiling. `evidence` quotes the rule and the file.
- Vague guidance ("write clean code") stays under the ceiling.
- When the run's own diff touches an indexed file, the approver screen lists that file as its own item.

### Terms and decision record

New `CONTEXT.md` entries:

- **Repo instructions**: tracked files in a consuming repository that state how work there is done.
- **Instruction index**: the per-run record of repo instructions at the run's ref.
- **Instruction entry**: one file in the instruction index.
- **Entry kind**: `always`, `scoped` or `reference`.
- **Unapplied rule**: a repository rule that loses to a factory mechanic, recorded in `plan.md` as `Not applied:`. The mirror of **Rule override**.

ADR 0019: the factory discovers repo instructions itself; harness auto-loading is never relied on.

## Decision log

| # | Decision | Why |
|---|---|---|
| Q1 | Fix pain A and pain B. Per-harness differences disappear as a side effect. | No incident was named. |
| Q2 | In scope: agent instruction files at any depth, and governance documents (`CONTRIBUTING*`, the SpecKit constitution, ADRs, documents that instruction files link to). | Machine-enforced config is enforced by its tools through `commands`. Unwritten conventions and outside sources are unbounded and not reproducible. `RESOLVE` already handles repo-shipped skills. |
| Q3 | Only git-tracked files at the run's commit. | Same result on every machine and harness. The PR is judged against what the repository publishes. The worktree holds tracked files only. |
| Q4 | Scan at every preflight. Record the file list and hashes. Disclose changes on resume. No cache across runs, and no factory-maintained copy in the repository. | Same contract as `profile-record`. A cache adds only staleness. A copy becomes a second source of truth. |
| Q5 | The repository wins on code conventions, applied by every role from plan onward. The factory keeps its commit, branch and PR mechanics. A losing repository rule gets a `Not applied:` line. | `spec-conformance` parses `factory(implement):` subjects and the branch name is tied to the spec directory. Instruction files are repository-controlled text and cannot waive the approver, the review rounds or the state-writer rules. |
| Q6 | No instruction files: disclose, continue, name `create-project-agents-file` as a hint. | Discovery never halts. No offer inside a feature run. |
| Q7 | The factory never relies on harness auto-loading. | Five behaviours, none covering the sibling worktree. Per-harness gap tables would go stale. |
| Q8 | Deterministic scan in the factory CLI. | Same output on every harness, no tokens, stable hashes, unit-testable. |
| Q9 | Roles get the index path and read the source files verbatim. | Nothing is lost or invented, and the hash proves which version applied. A digest is lossy. Pasted text repeats its cost on every spawn. |
| Q10 | Uniform consumers, one shared reference, one pointer line per role. | Instruction files carry security and UI rules too. |
| Q11 | `instructions.include` and `instructions.exclude` in `<repo>/.factory/config.json`. | A catalogue cannot know project-specific locations. The config is tracked. Exclude drops fixtures. |
| Q12 | Read git objects at the run's ref. | One rule for all stages. Instruction edits not yet on `origin/<default-branch>` are invisible to a new run, as code is today. The stack profile keeps scanning the working tree. |
| Q13 | Closest scope wins. A same-scope contradiction is one ordinary relay question at plan. | Matches the AGENTS.md closest-file rule. A fixed file order hides a real inconsistency. Preferring the running harness's file makes the result harness-dependent again. |
| Q14 | A run may edit an indexed file. The approver screen lists it. | A role can loosen a rule and then follow it. |
| Q15 | `commands` keeps `build` and `test`. Documented commands come from every root-scope entry. The verify gate is unchanged. | Verify-gate slots belong to the review-gaps work (items 6 and 9). |
| Q16 | Three entry kinds. Imports inherit kind and scope. Links are followed one hop. A third config list, `instructions.reference`. | Roles cannot read every ADR and linked document on every spawn. |
| Q17 | The first version carries every verified convention in the starting catalogue, with one tolerant front-matter reader. An entry whose front matter cannot be parsed stays in the index with a disclosed note. | One table row per tool, like the stack tables in `detect.py`. |
| Q18 | The planner sorts directives once, at plan. | One verdict the approver can read, without noise from tool-specific files. |
| Q19 | Never truncate. Warn above 32 KiB of `always` entries. Fixed constant. | Truncation silently drops rules. 32 KiB is Codex's combined cap, the only documented one. |
| Q20 | Obedience is checked in review only. | Review is already the backstop for the diff. |
| Q21 | A breach of an explicit, checkable rule is a blocking documented-contract failure. | Without this a written repository rule reads as style, is capped at MEDIUM and reaches the approver unfixed. Pen reference mismatches are treated the same way. |
| Q22 | Read-only `factory instructions` and writer `factory instructions-record`, separate from the stack profile. | The profile is orientation from the working tree. Instructions are binding and read from a git ref. |
| Q23 | Scanner unit tests, one bench case, one checklist line per harness golden run. | Unit tests prove discovery. The bench case proves roles obey. |
| Q24 | Standalone `design-to-code` is unchanged. | A standalone session runs in the repository itself, where native loading works. |
| Q25 | The catalogue in `core/` complies with Principle II, with one justification line in the plan. Amend the wording (PATCH) only if analyze still flags it. | The catalogue is data about consuming repositories and is identical on every harness. `core/` already names `CLAUDE.md` and `AGENTS.md`. |
| Q26 | The terms above and ADR 0019. | The decision is surprising without context and rests on research that will age. |
| Q27 | Two runs, both on the full chain. | Each PR stays reviewable and ships value alone. |
| Q28 | This brief. | `/factory` cannot be invoked by a model, so each run is started by hand. |

## Confirmed details

1. The same content at the same scope is indexed once. A `CLAUDE.md` symlinked to `AGENTS.md` is one entry.
2. A delta on resume is disclosed only. The run continues without a re-plan.
3. Submodule contents are not scanned.
4. The root `README.md` is not an instruction file unless it is linked or included.
5. A writer that meets a same-scope contradiction the plan did not settle follows the neighbouring code and says so in its envelope summary.
6. A writer that meets an "ask a human before X" directive the plan did not cover stops and returns `failed` naming it, as for a missing seam.
7. `factory init` does not seed the config lists. `config.README.md` documents them.
8. Instruction breaches inside pre-adoption commits are reviewed like any other defect.
9. No new cruise decision ids. The only new user wait is the Q13 relay question, which fast mode auto-accepts.

## Open points for the runs

These were not discussed. Each run's clarify or plan stage settles them.

- Whether the scanner reads other tools' config for extra file names (OpenCode `instructions`, Codex `project_doc_fallback_filenames`, Gemini `context.fileName`, Aider `read:`). `instructions.include` already covers such files by hand.
- The exact ADR directory patterns.
- The name of the shared reference, and the name and format of the index file.

## Delivery

Run 2 requires run 1 to be merged.

### Run 1: discovery (spec 024)

Everything the CLI and the orchestrator do at preflight.

- The catalogue scanner, the three config lists, `factory instructions`, `factory instructions-record` and the state summary.
- The preflight call, its disclosure, the 32 KiB warning and the no-instructions case.
- The orchestrator reads the `always` entries; documented commands come from every root-scope entry.
- The `CONTEXT.md` terms and ADR 0019.
- This repository's own lists: `instructions.reference` = `DESIGN.md`, `CONTEXT.md`; `instructions.exclude` = `conformance/**`.
- Proof: scanner unit tests over fixture trees covering the catalogue, nesting, glob front matter, links, imports, include and exclude, the ref-based read and the delta.

Expected touch points: `core/skills/factory/bin/factory_cli/`, `core/skills/factory/references/state.md`, `core/skills/factory/SKILL.md` (step 1 and Adoption), `DESIGN.md`, `CONTEXT.md`, `docs/adr/`, `tools/tests/`, `.factory/config.json`.

### Run 2: consumption (spec 025)

Everything the spawned roles and the review do.

- The index path in every spawn's inputs, the shared reference and the pointer lines.
- The planner's sorting step with `Overridden:` and `Not applied:` lines and its relay questions.
- `code-standards` reads its standards list from the index.
- The severity rule for a breached explicit rule.
- The approver's list of instruction files the run changed.
- Proof: one bench case whose fixture holds a nested instruction file with a rule a model breaks by default. The fixture's acceptance command checks the rule. Pass means the rule is obeyed with zero fix rounds. Each harness golden-run checklist gains one line.

Expected touch points: `core/roles/*.md`, a new file under `core/skills/factory/references/`, `findings.md`, `engineering.md` (ENG-11), `core/skills/factory/SKILL.md` (steps 5 to 8), `conformance/bench/`, `conformance/golden-run/`, `DESIGN.md`.

## Out of scope

- Adopting the repository's commit, PR and branch conventions (the rejected half of Q5). A later spec.
- Verify-gate slots for lint, format, typecheck and e2e commands. See `docs/review-gaps-brief.md`, items 6 and 9.
- Conventions that exist only in code. See `docs/review-gaps-brief.md`, item 10.
- Sources outside the repository, such as wikis and tickets.
- Untracked, local and user-global instruction files.
- Repo-shipped skills.
- Generating instruction files for a repository that has none.

## Starting catalogue

From the same research. The tracked-only rule (Q3) applies to every row. Re-check each source at plan time.

| Tool | Path patterns | Nested | Scoping | Source |
|---|---|---|---|---|
| AGENTS.md format | `**/AGENTS.md` | Yes; the file closest to the edited file wins | Always-on | <https://agents.md/> |
| Claude Code | `CLAUDE.md`, `.claude/CLAUDE.md`, `CLAUDE.local.md`, `.claude/rules/**/*.md` | Yes | Always-on; rules scoped by `paths` | <https://code.claude.com/docs/en/memory> |
| Gemini CLI | `GEMINI.md` | Yes | Always-on | <https://geminicli.com/docs/cli/gemini-md/> |
| Copilot | `.github/copilot-instructions.md`, `.github/instructions/**/*.instructions.md` | Subfolders | Always-on; scoped by `applyTo` | <https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions> |
| Cursor | `.cursor/rules/**/*.mdc` (`.cursorrules` unverified in current docs) | Yes | `alwaysApply`, `globs`, `description`, manual | <https://cursor.com/docs/context/rules> |
| Windsurf (now Devin) | `.windsurf/rules/*.md`, `.windsurf/global_rules.md`, `.windsurfrules`, `.devin/rules/*.md` | Yes | `trigger`: `always_on`, `glob`, `model_decision`, `manual` | <https://docs.devin.ai/cli/extensibility/rules.md> |
| Cline | `.clinerules/`, `.cline/rules/` | Not documented | Always-on; scoped by `paths` | <https://docs.cline.bot/features/cline-rules> |
| Roo Code | `.roo/rules/`, `.roo/rules-{mode}/`, `.roorules`, `.roorules-{mode}` | Workspace root only | Always-on, per mode | <https://docs.roocode.com/features/custom-instructions> |
| Junie | `.junie/AGENTS.md`, `.junie/rules/*.md`, `.junie/playbook.md`, legacy `.junie/guidelines.md` | Not documented | Always-on | <https://junie.jetbrains.com/docs/guidelines-and-memory.html> |
| Kiro | `.kiro/steering/*.md` | Unverified | `inclusion`: `always`, `fileMatch`, `manual`, `auto` | <https://kiro.dev/docs/steering/> |
| Aider | `CONVENTIONS.md` | No discovery | Always-on once configured | <https://aider.chat/docs/usage/conventions.html> |
| Amp | `AGENTS.md`; fallback `AGENT.md` | Yes | Always-on | <https://ampcode.com/docs/customize/agents-md> |
| Zed | `.rules` | Not documented | Always-on | <https://zed.dev/docs/ai/instructions> |
| Continue | `.continue/rules/*.md` | Not documented | `alwaysApply`, `globs`, `regex`, `description` | <https://docs.continue.dev/customize/deep-dives/rules> |
| OpenCode | `AGENTS.md` | Yes | Always-on | <https://opencode.ai/docs/instructions/> |
| Codex | `AGENTS.md`, `AGENTS.override.md` | Yes, root to working directory | Always-on | <https://developers.openai.com/codex/guides/agents-md> |

Left out until verified: Trae (`.trae/rules`); its documentation could not be retrieved.

## Feature text

Ready to submit from this repository. Run 1 first; run 2 after run 1 is merged.

Run 1, as `/factory --full <feature>`:

> Give the factory its own discovery of repo instructions (see docs/repo-instructions-brief.md, run 1): add a deterministic, stdlib-only scanner to the factory CLI that reads git objects at the run's ref and indexes tracked agent instruction files at any depth from a table-driven catalogue, governance documents, @path imports and one-hop links; classify each entry as always, scoped or reference with its scope, size, hash and title; read instructions.include, instructions.reference and instructions.exclude from .factory/config.json; add the read-only `factory instructions` report and the `factory instructions-record` writer, which stores a summary in run state, writes the index file in the run folder and reports the delta on a re-record; call the writer at every preflight after profile-record and disclose counts, sizes, notes, the over-32-KiB warning and the no-instructions case; have the orchestrator read the always entries at preflight and grill and take documented build and test commands from every root-scope entry; record the new terms in CONTEXT.md and the decision as ADR 0019; add this repository's own config lists; and cover the scanner with unit tests over fixture trees.

Run 2, as `/factory --full <feature>`:

> Make every factory role follow the repo's instruction index (see docs/repo-instructions-brief.md, run 2; requires run 1): pass the index path to every spawn; add one shared reference stating the read duty for always, scoped and reference entries and the closest-scope rule, and point every planning, writing, reviewing and judging role at it with one line; have the planner sort directives once at plan into binding conventions, Overridden lines, Not applied lines and relay questions for same-scope contradictions and ask-a-human directives, ignoring assistant-behaviour directives; have code-standards take its standards list from the index; treat a breach of an explicit, checkable rule in an indexed file as a blocking documented-contract failure that quotes the rule and the file; list instruction files the run itself changed on the approver screen; and add a bench case with a nested instruction file whose rule a model breaks by default, plus one golden-run checklist line per harness.
