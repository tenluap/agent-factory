---
name: create-project-agents-file
description: 'Use when asked to create, generate, update, or refresh an AGENTS.md agent-guidance file at a repository root — e.g. "write an AGENTS.md", "add agent instructions for this repo", or onboarding AI coding agents to a project.'
---

# Create Project AGENTS.md

## Overview

Write or refresh a single root `../../../AGENTS.md` giving AI agents and advanced contributors only what
they cannot infer from a quick file scan: verified build/test commands, project-specific
conventions, and gotchas. Core principle: every documented command must have been executed
successfully this session — no guessed syntax, no aspirational commands.

If `../../../AGENTS.md` already exists this is a refresh: re-verify every command, update stale facts and
the verification date, keep content that is still accurate.

**When not to use** — READMEs or contribution guides; repo-wide agent rules that belong in
instruction files (`.github/instructions`, `.copilot/instructions`), not per-project facts.

## Workflow

1. **Survey** — identify stacks, solution/meta files, build system, test runners, formatter/
   linter configs, CI workflows. Note vendored code, generated/output dirs, and code on disk the
   main solution does *not* reference.
2. **Verify** — run the build, each test suite, and every single-test filter syntax you plan to
   document. Record real pass counts and durations. If a suite cannot run locally (hardware,
   admin, registry), document the exact command anyway and mark the unverified prerequisite.
3. **Prove the add-a-test recipe** — create one small scratch test following the recipe, run it,
   delete it during cleanup.
4. **Write** — draft per the content spec below: dense bullets and fenced commands, ≤120 lines
   (shorter for small projects; no padding to hit a floor).
5. **Ship the Rider catalog** — copy `references/rider-mcp-catalog.md` (shipped next to this
   SKILL.md) to `<repo root>/docs/rider-mcp-catalog.md`, creating `docs/` if missing. Overwrite
   any existing copy. Without this the catalog reference in the Base Agent Rules points at a
   missing file.
6. **Clean up** — delete every file created during verification except `../../../AGENTS.md` and
   `docs/rider-mcp-catalog.md`; delete caches (`__pycache__`, `.pytest_cache`, bin/obj) *after*
   the final verification run, since runners regenerate them. Confirm nothing else was left
   behind (git status, or a recursive directory listing without git).

## Content spec

Header line states purpose plus a verification date, refreshed each run. All sections present,
in this order; when a section does not apply (no build step, no linter/formatter), keep the
section and state the absence in one line:
1. **Layout** — one-line role per top-level dir/module; vendored code vs project code;
   generated/output dirs; which solution/meta-file covers what — explicitly flag code on disk
   that the main solution does *not* reference.
2. **Build/Configuration** — exact commands, SDK/toolchain versions and what is installed,
   prerequisites, output layout.
3. **Testing** — run command per suite; single-test filter syntax per runner; an add-a-new-test
   recipe including any registration step (build-file entry, naming, folder); slow/excluded/
   hardware-dependent suites and how to skip them; locks and concurrency gotchas.
4. **Code style and conventions** — centrally enforced compiler/project settings, naming and
   file-organization patterns, architecture/testability rules, formatter and linter commands
   (only if they exist).
5. **Additional development notes / gotchas** — anything that costs discovery time:
   admin/registration requirements, stale or duplicate build dirs, cross-stack rebuild
   coupling, misleading config files.

**Quality bar**
- *Verified*: every documented command was executed successfully this session — no guessed
  syntax, no aspirational commands.
- *Dense*: bullets and fenced commands, ≤120 lines, no prose filler.
- *Quantified*: current-state facts carry numbers where possible ("53/53 tests", "~60 s") so
  staleness is detectable.
- *Stable*: only durable facts; no TODO state or details that rot within days.
- *Machine-actionable*: an agent can copy-paste any line and succeed without extra research.
- *Singular*: one file at the repository root, plus the shipped `docs/rider-mcp-catalog.md`;
  nested `../../../AGENTS.md` only to override sub-area specifics in very large monorepos.
- *Clean*: no secrets, credentials, or personal IDE artifacts referenced as convention.
- *Multi-stack aware*: when native and managed stacks coexist, give each its own build/test
  subsection; if a suite cannot run locally (hardware, admin, registry), document the exact
  command anyway and mark the unverified prerequisite.

**Anti-requirements** — never include:
- language/framework tutorials and generic advice ("write clean code");
- content already in the README unless restated with agent-relevant precision (flags, paths, filters);
- greetings, meta-commentary about the document itself, status narration;
- commands from other projects or remembered habits — only what ran here.

## Common mistakes

| Mistake | Fix |
|---|---|
| Documenting commands that were never run | Execute every command first; copy real counts from output. |
| Generic test advice ("write good tests") | Exact run command, filter syntax per runner, add-a-test recipe. |
| Scratch tests/files left behind | Cleanup step deletes everything except `../../../AGENTS.md` and `docs/rider-mcp-catalog.md`. |
| Catalog reference in AGENTS.md dangles | Ship the catalog step copies `references/rider-mcp-catalog.md` to `docs/` before finishing. |
| Restating the README | Only facts an agent cannot get from a file scan. |
| Tutorials and framework basics | Assume expertise; project-specific content only. |


Create a AGENTS.md file at the root directory that add the following base rule for the project with any relevant details that will aid future development on this project. This should include, but is not limited to:

1. **Build/Configuration Instructions**: If specific build or configuration steps are required, provide clear and detailed instructions for setting up the project.

2. **Testing Information**:
    - Instructions for configuring and running tests.
    - Guidelines on adding and executing new tests.
    - Create and run a simple test to demonstrate the process.

3. **Additional Development Information**: Information about the code style or any other information you believe would be useful for the development or debugging process.

**Important Notes**:
- This information is intended for an advanced developer; there's no need to include basic things, only information specific to this project.
- Сheck that the test examples work before writing the information to the file.
- At the end delete all additional files that you created except `../../../AGENTS.md` and `docs/rider-mcp-catalog.md`

And add this at the bottom of the file:
```markdown
[//]: # (------------Custom Agent Rules starts-------------------)
# Base Agent Rules

## 1. Session Init

Invoke `/caveman ultra` on the first message of a session, before any other output. Once per
session only.

## Rider MCP

Prefer Rider MCP for work on the open solution. Check the current client's Rider tool definitions first.
Use the most specific exposed action, its exact arguments, and the intended solution root when supported.

**Catalog:** If no direct Rider action fits or you need a router-only action, read `docs/rider-mcp-catalog.md`
from the repository root. Use it to find candidate names and syntax, not as proof that an action is enabled.

Use semantic tools for symbols, callers, usages, and refactorings; use text search for literal matches.
Preview refactorings when supported and review the diff. Prefer Rider inspections, run configurations, and
debugger controls when IDE context matters. Follow repository verification commands for checks not covered
by Rider. Use specialized actions only when relevant and authorized.

Use `execute_tool` only after verifying that the target is enabled and confirming its exact argument syntax.
Never invent tool calls, arguments, or outputs. If a call is rejected as unknown or invalid, refresh discovery
and retry only if you find a concrete correction. If no verified Rider action fits, stop in Rider-only mode;
otherwise identify any authorized, documented fallback you use. Do not write a substitute script or wrapper
without permission.

Preserve unrelated changes and respect approvals. Never route around a denial. After a timeout or partial
write, inspect the resulting state before retrying. Report only observed actions and outcomes.

## 2. Ambiguity Handling

**Trigger** — input shows any of: no stated platform/framework/runtime; goal without a measurable
outcome; two or more incompatible readings; open "how to X" with no bounded deliverable;
unprioritised feature list; typos or fragments that block parsing.

**Then, in order:** invoke `/prompt-optimiser full` → display the optimised prompt verbatim →
confirm direction (ask only when a decision still changes the implementation) → proceed.

State in the same response that `/prompt-optimiser full` ran and why. Never substitute your own
interpretation for the optimiser output.

## 3. UI Change Critique Loop

**Trigger** — any edit to: component/view files (`.tsx .jsx .vue .razor .cshtml .html .svelte
.xaml .axaml`); templates, markup, or partials rendered to a screen; stylesheets (`.css .scss .less`) or
utility-class markup; design tokens, theme, or Tailwind config; layout, spacing, typography,
colour, or motion; user-visible copy, labels, error messages, empty states, or i18n strings.

**Then, before declaring the task complete:**

1. Invoke `/impeccable critique` on the changed UI. Pass the changed files and the user-facing intent.
2. List every returned recommendation with its priority.
3. Implement each one that is actionable in scope and does not contradict an explicit user
   constraint.
4. Run `/impeccable audit` on the updated UI to catch issues that survive the first pass.
5. Run `/impeccable typeset` to validate hierarchy, typography, spacing, and reading rhythm.
6. Run `/impeccable polish` to finalise the visual consistency and quality pass.
7. Re-verify: re-read the edited files, confirm each implemented item is present, and confirm the
   change still builds or renders via the project's existing command.
8. Report which recommendations were applied and which were deferred, one line of justification
   per deferred item.

**Cap** — two critique-and-fix iterations per change set. If high or critical findings remain
after the second, stop, list them, escalate to the user.

**Never** — declare a UI task complete without at least one `impeccable` critique; surface
recommendations without acting on the actionable ones; expand scope beyond the changed surface.

## 4. Research

Before any non-trivial framework, library, SDK, API, or config decision, query Context7. For
Microsoft technologies (.NET, Azure, ASP.NET Core, EF Core, M365, Windows), also query Microsoft
Learn. Cite title and URL when a decision depends on retrieved docs. If no reliable source is
found, state what was checked, take the conservative option, and name the validation step.

## 5. .NET Standards

Nullable reference types on; `async`/`await` end to end with no `.Result` or `.Wait()`; DI over
static state; `IOptions<T>` for config; structured logging via `ILogger<T>`; `CancellationToken`
propagated on async APIs; file-scoped namespaces. Match the repo's existing style and target
framework. Run only build/test/lint commands that already exist.

## 6. Output Discipline

Every response line must carry information the user asked for or directly needs. Silence is always preferred over noise.

Never emit:
- Status narration ("I'll now look at…", "Let me check…", "I've updated X")
- Redundant confirmations ("Done!", "Sure!", "Of course!", "Understood")
- Filler transitions ("Moving on to…", "Next up…", "As a next step…")
- Unprompted commentary ("Interesting problem", "Good question!")
- Re-stating what the user said before answering
- Announcing tool calls before making them

When in doubt: omit it.

## 7. Precedence

Explicit user instruction this turn > repository instruction files > this file. On conflict,
follow the higher rule and state the conflict in one sentence.


[//]: # (------------Custom Agent Rules ends-------------------)

```




