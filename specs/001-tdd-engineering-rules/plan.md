# Implementation Plan: Engineering discipline for factory code-writing roles

**Branch**: `001-tdd-engineering-rules` | **Date**: 2026-10-22 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-tdd-engineering-rules/spec.md`

## Summary

Give the factory one shared, harness-neutral engineering rules reference (`core/skills/factory/references/engineering.md`) whose rules carry stable `ENG-n` ids, and point the code-writing, planning, reviewing and judging roles at it. The planning role's own stage instructions gain the test-first behaviour (a "Test seams" section in the plan, a failing-test task before each implementation task, a HIGH blocking seam-mapping check in analyze, a MEDIUM non-blocking reason-line check for new files, abstractions and dependencies (FR-020b), seam questions in clarify only when seams are ambiguous). The implementing and fixing roles gain red-green-refactor, the `Red:` proof line in the task commit body, the bounded reuse search, the stop-on-missing-seam failure, and the same stop when the repository's test command cannot be run at all (FR-011b, FR-013b). The spec-conformance reviewer checks each implementation commit body's `Red:` line against `tasks.md` and distinguishes the two kinds of fix round a run can have (FR-015d): a **verdict-driven fix round**'s commit is matched against `confirmed_blocking` in the previous round's verdict file, while a **user-changes fix round**'s commit answers the user and no verdict and is therefore checked only for the grammar of each `Red:` line and for one such line per behaviour-changing fix its diff shows, matched against neither the verdict nor `tasks.md`. Enforcement is tiered by cited rule id: findings citing `ENG-1`..`ENG-6` (duplication, untested added behaviour, red-proof defects, seam defects) keep the severity their own requirement states, HIGH and blocking, while `ENG-7`..`ENG-10` are judgement calls capped at MEDIUM, never blocking and never fixed by a verdict-driven fix round (FR-015f, FR-015g) — a cap that the shared findings reference must state as an override of its own default "critical and high are blocking" guidance, with its four-id limit stated beside it. `DESIGN.md` records the discipline first, including that ceiling, the un-runnable-command stop and the plan-time reason line (constitution I), then `core/` changes, then every harness is re-rendered and the generated `dist/` is committed with the source (constitution III).

The change is instructions and generated output only: nine Markdown files under `DESIGN.md` and `core/` (`DESIGN.md`, the new `engineering.md`, the shared `findings.md` and six role prompts), plus the four rendered copies under `dist/`. No product code, no renderer change, no orchestrator flow stage, no new state field, no new severity level and no new reviewer, gate or list.

## Technical Context

**Language/Version**: Markdown instruction files (role prompts, skill references, design document); Python 3 only as the existing, unchanged renderer `tools/render.py`

**Primary Dependencies**: `tools/render.py` and the four adapters in `adapters/` (`claude-code`, `codex`, `copilot`, `opencode`); the roles' existing `<F>/references/<name>.md` reference mechanism

**Storage**: Files in git. The red proof lives in the task's commit body; nothing new is persisted in `state.json`

**Testing**: The repository has no test runner and needs none for this change (see "Test seams" below). Verification is `commands.build` (render every harness) followed by `commands.test` (`git diff --exit-code -- dist/`)

**Target Platform**: Any agent harness the factory supports; the rules file and role text are byte-identical across harnesses

**Project Type**: Instruction set / prompt library with a generator (`core/` + `adapters/` -> `dist/`)

**Performance Goals**: N/A. The only budget that matters is prompt length: role prompts stay short, and the rules live in one reference the roles point at rather than restate

**Constraints**: `core/` names no harness tool, path or command (constitution II); `dist/` is never hand-edited (constitution III); role prompts stay short, imperative and unambiguous with one term per concept (Writing Standards); agents are stateless, so every rule must be readable from disk in a single spawn (constitution IV)

**Scale/Scope**: 1 new reference file, 1 design-document section, 6 role prompts touched, 1 shared reference touched, 4 rendered harness trees regenerated; 11 rules (`ENG-1` .. `ENG-11`)

## Test seams

Seams: none. The canonical lines this section must carry ([contracts/plan-artifact.md](./contracts/plan-artifact.md)), which the analyze and spec-conformance checks match textually:

```text
Exempt: whole change - Markdown instruction files and their generated per-harness copies only, no executable behaviour
Overridden: none
```

**This change is documentation/configuration-exempt from test-first, in whole (FR-025).**

**Reason**: the change adds and edits Markdown instruction files for agents (`DESIGN.md`, the new `core/skills/factory/references/engineering.md`, six role prompts, one shared reference) and the generated per-harness copies of them. It introduces no executable behaviour: there is no function, no entry point and no runtime path a test could call. The repository has no test runner and this change does not create a need for one, so FR-018's runner-setup task does not apply here.

**Seams under test**: none. There is no public entry point in this change.

**Verification instead of tests** (FR-025, SC-005):

1. `commands.build` - `for h in $(python3 tools/render.py --list); do python3 tools/render.py "$h" || exit 1; done` - renders every harness; a malformed role file (missing frontmatter, or a `'''` in a body that breaks the TOML agents) fails the build.
2. `commands.test` - `git diff --exit-code -- dist/` - proves the committed `dist/` matches `core/` + `adapters/` for every harness, so no harness carries stale or hand-edited rules.
3. Inspection checks in [quickstart.md](./quickstart.md): the rules appear in exactly one source file (SC-004), every rule has a unique `ENG-n` id (SC-004a), each of the six roles references the file, and the rendered tree contains it for every harness.

End-to-end behaviour (a real run producing red proofs and seam findings) is observed on the next factory run, per the "Validation plan" in `DESIGN.md`.

`Overridden: none` — no rule of the shared reference is overridden by this repository's constitution; the two agree (constitution V is the source of `ENG-10`). `Test runner:` is absent on purpose: this change creates no need for one (FR-018 does not apply).

The whole-change exemption (FR-025) is unaffected by the stop added in FR-011b/FR-013b: that stop fires only where a repository has a test runner whose command cannot be run. This repository has no test runner and needs none here, so no task of this change ever tries to run one.

## Reasons for new files, abstractions and dependencies (ENG-10, FR-020b)

One line per new file, new abstraction and new dependency this change introduces, so the analyze stage's MEDIUM, non-blocking reason check (FR-020b, SC-003a) finds a stated reason for every one of them. This plan is the worked example of the artefact shape in [contracts/plan-artifact.md](./contracts/plan-artifact.md).

| New thing | Kind | Reason |
|---|---|---|
| `core/skills/factory/references/engineering.md` | new file (source) | FR-001 requires the rules in exactly one harness-neutral place that six roles point at; inlining them in six prompts would duplicate them and let them drift (SC-004). Also recorded in the Constitution Check (V) and ADR 0001 |
| `dist/<harness>/skill/references/engineering.md` (four files) | new files (generated) | Mandated, not chosen: constitution III requires the rendered copy of every `core/` file for every harness, written by `tools/render.py` and never by hand (FR-023) |
| `CONTEXT.md`, `docs/adr/0001`..`0004` | new files (already committed in the grill-with-docs stage) | The repository had no glossary and no ADR trail; the four decisions with lasting consequences need a stable record the roles and future runs can cite (ADR 0004 carries the judgement-call ceiling of FR-015f/FR-015g). Documentation only; no role reads them at run time |
| `specs/001-tdd-engineering-rules/contracts/*.md`, `research.md`, `data-model.md`, `quickstart.md`, `checklists/requirements.md` | new files (feature artefacts) | Produced by the spec stages themselves for this one feature; they write down contracts the change already implies and are not part of the shipped instruction set |
| — | new abstraction | None. No new verb, role, stage, severity level, state field, finding type, gate or list is introduced; the change reuses the existing reference mechanism, the per-task commit, the existing failure policy, the existing verdict shape and the existing approver screen (FR-015g) |
| — | new dependency | None. No package, tool or external skill is added; `tools/render.py` and the four adapters are unchanged, and the rules depend on no skill outside the factory (FR-002) |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Gate | Status |
|---|---|---|
| I. Design First | The behaviour change is recorded in `DESIGN.md` before `core/` and `adapters/` carry it, in this change | PASS - task order puts the `DESIGN.md` "Engineering discipline" section first (FR-022), and T002's content list covers every behaviour this change adds — the rules reference and ids, the red proof, plan-time seams, enforcement and the override line, plus the `ENG-7`..`ENG-10` ceiling with its advisory route (ADR 0004), the stop on a test command that cannot be run and the plan-time reason line with analyze's MEDIUM non-blocking check — linking `docs/adr/0001`..`0004`; `core/` edits follow |
| II. Harness-Neutral Core | No file added or edited under `core/` names a harness tool, path or command | PASS - `engineering.md` and the role edits use only the `<F>/references/...` form and the neutral verbs; no adapter needs a change |
| III. Generated Dist (NON-NEGOTIABLE) | Every `core/`/`adapters/` change is followed by a render of every harness, and `dist/` is committed with the source | PASS - every `core/`-editing task re-renders all four harnesses and commits the regenerated `dist/` in that task's own commit, so no commit in the run's history carries a stale `dist/`; the final render task plus `commands.test` prove no drift (SC-005). Because one render writes all four harness trees, no two `core/`-editing tasks run in parallel |
| IV. Stateless Agents | No role relies on memory of an earlier turn | PASS - the rules are read from the shared reference each spawn; the red proof is read from the commit body and `tasks.md`; the seams are read from `plan.md`. The external `tdd` skill is rejected for exactly this reason (ADR 0001) |
| V. Simplicity and Reuse | Smallest change; a new file needs a stated reason in the plan | PASS - one new source file, `core/skills/factory/references/engineering.md`. **Reason**: FR-001 requires the rules in exactly one harness-neutral place that six roles point at; inlining them in six prompts would duplicate them and let them drift (SC-004). Nothing else is added: no new verb, no new state field, no new verdict field (an advisory entry keeps the `ENG-n` id in its existing `summary` and links evidence through its existing `sources`), no new stage, no new commit type, no new severity level, no new gate or list, no renderer change; the change reuses the existing reference mechanism, the existing per-task commit, the existing failure policy, the existing verdict shape and the existing approver screen (FR-015g). Every new file, abstraction and dependency is listed with its reason in "Reasons for new files, abstractions and dependencies" above (`ENG-10`, FR-020b, SC-003a) |
| Writing Standards | Prompts and references short, imperative, unambiguous, one term per concept | PASS - the rules reference is one numbered rule per entry; terms come from the glossary in `CONTEXT.md`; the role edits add lines, not prose |
| Development Workflow | Build renders every harness; `git diff --exit-code -- dist/` passes; flow changes validated per `DESIGN.md` | PASS - both commands are the stated verification; end-to-end validation is deferred to the next real run, as the design document's validation plan already prescribes |

Post-design re-check (after Phase 1, re-run on analyze loops 1 and 2): unchanged, all PASS. The Phase 1 artifacts add no file to `core/`, no verb and no adapter change; `contracts/` only writes down the three textual contracts the change already implies. The requirements added in the loop (FR-011b, FR-013b, FR-015f, FR-015g, FR-020b) add instruction lines to files this plan already touches — `fixer.md`, `code-standards.md`, `review-judge.md`, `spec-builder.md` and the shared `findings.md` — and no new file, abstraction or dependency, so principles II, IV and V are untouched. Loop 2 changed no gate either: FR-015d was extended in place with the user-changes fix-round carve-out, which is one more condition in instructions `spec-conformance.md` and `contracts/commit-body.md` already carry, and the two terms it rests on (**verdict-driven fix round**, **user-changes fix round**) were added to the existing glossary in `CONTEXT.md` — no new file, abstraction, dependency, severity, field or stage, so principle V still passes and the Writing Standards row's "one term per concept" is now anchored for both fix rounds.

## Project Structure

### Documentation (this feature)

```text
specs/001-tdd-engineering-rules/
├── plan.md              # This file
├── spec.md
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── engineering-reference.md
│   ├── commit-body.md
│   └── plan-artifact.md
├── checklists/requirements.md
└── factory/             # run state, brief, analyze and remediation logs
```

Repository-level documentation already written in grill-with-docs: `CONTEXT.md` (glossary) and `docs/adr/0001-factory-owns-its-engineering-rules.md`, `docs/adr/0002-red-proof-lives-in-the-task-commit-body.md`, `docs/adr/0003-test-seams-are-settled-at-plan-time.md`, `docs/adr/0004-judgement-call-rules-advise-they-never-block.md` (the FR-015f/FR-015g ceiling). Grill-with-docs loop 2 extended two of them rather than adding any: `CONTEXT.md` gained the **verdict-driven fix round** and **user-changes fix round** entries this plan's terms come from, and ADR 0002 gained the user-changes fix round's verification rule (FR-015d). This plan changes none of them; their reasons are in "Reasons for new files, abstractions and dependencies" above.

### Source Code (repository root)

```text
DESIGN.md                                   # + "Engineering discipline" section (written first): the shared rules reference with ENG-n ids; the red proof in the task commit body; seams settled at plan time; enforcement by code-standards, spec-conformance and the judge; the Overridden: line; the ENG-7..ENG-10 severity ceiling and the advisory route (FR-015f, FR-015g); the stop on a test command that cannot be run (FR-011b, FR-013b); the plan-time reason line per new file/abstraction/dependency with analyze's MEDIUM non-blocking check (FR-020b); links to docs/adr/0001..0004
core/
├── skills/factory/
│   ├── SKILL.md                            # unchanged
│   └── references/
│       ├── engineering.md                  # NEW: ENG-1 .. ENG-11, the shared rules
│       ├── findings.md                     # + reviewers needing commit metadata read the run's commit log; commit-level finding shape; engineering findings cite the ENG-n id; the ENG-7..ENG-10 MEDIUM non-blocking ceiling, written as an override of this file's own default "critical and high are blocking" line (FR-015f); the ceiling's four-id limit, so an ENG-1..ENG-6 finding keeps its own severity; the advisory lifecycle, stated here only; an advisory[] entry derived from an engineering finding keeps its ENG-n citation in its existing summary, with sources as the link to the full evidence and no new verdict field
│       ├── protocol.md                     # unchanged
│       ├── state.md                        # unchanged
│       └── verbs.md                        # unchanged
└── roles/
    ├── spec-builder.md                     # plan/tasks/analyze/clarify test-first instructions; + a reason line per new file, abstraction and dependency in the plan, and analyze's MEDIUM non-blocking check for a missing one (FR-020b)
    ├── code-build.md                       # red-green-refactor, Red: line, reuse search, missing-seam failure, + stop on an un-runnable test command (FR-011b)
    ├── fixer.md                            # same rules; one Red: line per behaviour-changing fix; + the same stop on an un-runnable test command (FR-013b); its existing "Advisory findings stay untouched" sentence extended: no verdict-driven fix work on advisory engineering findings, while a user change request naming one is implemented as asked (FR-015g)
    ├── code-standards.md                   # untested behaviour and duplication HIGH blocking, cite ENG-n; + ENG-7..ENG-10 findings at most MEDIUM and never blocking, by pointing at the ceiling in findings.md (FR-015f)
    ├── spec-conformance.md                 # read the run's commit log; check each implementation commit body's Red: line against tasks.md, and a verdict-driven fix round's commit against confirmed_blocking in <spec_dir>/factory/reviews/round-<n-1>/verdict.json; a user-changes fix round's commit is checked for the grammar of each Red: line and one line per behaviour-changing fix only, against neither the verdict nor tasks.md (FR-015d)
    ├── review-judge.md                     # reference the rules; rate engineering findings by id; + the same ENG-7..ENG-10 ceiling, those findings routed to advisory[] keeping their ENG-n id in the entry's summary (no new field)
    ├── security-reviewer.md                # unchanged
    ├── ui-reviewer.md                      # unchanged
    └── ux-reviewer.md                      # unchanged
adapters/                                   # unchanged (no harness-specific behaviour added)
tools/render.py                             # unchanged
dist/{claude-code,codex,copilot,opencode}/  # regenerated, committed with the source
```

**Structure Decision**: the existing `core/` + `adapters/` -> `dist/` layout is kept exactly. The rules land in `core/skills/factory/references/` because `tools/render.py` already copies that whole directory into `dist/<harness>/skill/references/` and the roles already address it as `<F>/references/<name>.md`; that is why no renderer and no adapter change is needed (research.md, D3).

## Complexity Tracking

> Fill ONLY if Constitution Check has violations that must be justified

None. No principle is violated and no simpler alternative was rejected on complexity grounds; the one new file is justified in the Constitution Check (V) and in ADR 0001.
