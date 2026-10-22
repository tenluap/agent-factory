# Phase 0 Research: Engineering discipline for factory code-writing roles

No `NEEDS CLARIFICATION` marker survives into the Technical Context: the brief, the clarify session, the grill-with-docs session and the three ADRs settled every open question. This file records the decisions that shape the plan, and the facts about this repository that the plan rests on.

## D1 - The rules live in the factory, not in the external `tdd` skill

- **Decision**: one self-contained reference, `core/skills/factory/references/engineering.md`, with no dependency on any skill outside the factory (FR-001, FR-002).
- **Rationale**: factory agents are stateless and never talk to the user, so a skill that confirms seams with the user mid-loop cannot be followed; and a file inside `core/` renders into every harness unchanged. Recorded as ADR 0001.
- **Alternatives considered**: pointing the roles at the external `tdd` skill (rejected: mid-loop user confirmation, and no guarantee the skill is installed on every harness); inlining the rules in each role prompt (rejected: six copies drift, and SC-004 requires exactly one source).

## D2 - Rules carry stable `ENG-n` ids

- **Decision**: each rule is numbered `ENG-1`, `ENG-2`, ... ; reviewers, the judge and plan overrides cite the id (FR-004a, FR-005, FR-015c).
- **Rationale**: an id lets a finding name a rule without quoting it, keeps the override line short and machine-checkable, and makes renumbering a deliberate act.
- **Alternatives considered**: citing rules by heading text (rejected: text drifts, findings become unmatchable); no citation (rejected: SC-004a and the judge's rating need a shared token).
- **Rule set chosen** (11 rules, covering FR-003, FR-006, FR-014a): test-first, red proof, one commit per task, use the plan's seams, declared exemptions, reuse-before-writing with a bounded search, clean code, SOLID, functional preference, smallest change, repository conventions win. See [contracts/engineering-reference.md](./contracts/engineering-reference.md).

## D3 - The existing reference mechanism carries the file; the renderer needs no change

- **Fact**: `tools/render.py` copies `core/skills/factory` wholesale into `dist/<harness>/skill/`, so any new file under `core/skills/factory/references/` is rendered for every harness with no code change. Role bodies have `<F>` replaced by the harness's `skill_dir` when agent files are written, so `<F>/references/engineering.md` resolves on every harness.
- **Decision**: add the file under `core/skills/factory/references/` and reference it as `<F>/references/engineering.md`, exactly as the roles already reference `protocol.md` and `findings.md`.
- **Rationale**: constitution V (reuse before adding); zero renderer and zero adapter risk.
- **Alternatives considered**: a new top-level `core/engineering/` directory or a renderer flag (both rejected: new machinery for no gain).
- **Constraint inherited**: the Codex adapter writes role bodies into a TOML literal string, so no role body may contain `'''`. The rules reference is copied, not embedded, so this only binds the role edits.

## D4 - Test-first behaviour lives in the planning role's stage instructions

- **Decision**: the plan's "Test seams" section, the test-task-before-implementation-task rule, the analyze seam-mapping check and clarify's seam questions are written into `core/roles/spec-builder.md`. A run never edits the consuming repository's SpecKit templates, skills or commands (FR-006a).
- **Rationale**: the factory already runs SpecKit skills as instructions with per-stage overrides, so one more override per stage is the smallest change, and it survives any repository's SpecKit version. Recorded as ADR 0003.
- **Alternatives considered**: patching the consuming repo's `plan-template.md` and `tasks-template.md` (rejected: edits foreign files, breaks on SpecKit upgrades, invisible to other harnesses).

## D5 - The red proof is a line in the existing task commit

- **Decision**: `Red: <test name> failed as expected` in the body of the single commit that carries the task's test and implementation; `Red: not applicable - <existing test> already covers this` where an existing passing test already covers the behaviour; the fixing role writes one such line per behaviour-changing fix in its single fix commit (FR-009, FR-009a, FR-010, FR-013a).
- **Rationale**: the per-task commit already exists and the reviewers already read the run's diff, so no new commit type, state field or artefact is needed; history stays bisectable. Recorded as ADR 0002.
- **Alternatives considered**: a separate red commit (rejected: non-bisectable history); a `state.json` field or a side-file of proofs (rejected: duplicates what the commit already says).
- **Accepted cost**: verification is textual (the line matches a task in `tasks.md`), not a replay of the failing run.

## D6 - Severity and ownership of the enforcement checks

- **Decision**: analyze reports HIGH and blocking for a non-exempt implementation task with no mapped seam or no preceding test task, and reports nothing for tasks the plan declares exempt; CRITICAL stays reserved for constitution violations (FR-020, FR-020a). The code-standards reviewer rates untested added behaviour and real duplication HIGH and blocking (FR-015, FR-015a). The spec-conformance reviewer checks the `Red:` lines against `tasks.md` (FR-015b). The judge rates both against the shared rules by id (FR-015c).
- **Rationale**: HIGH is exactly the severity that triggers the existing remediation loop, so the discipline is enforced by machinery that already exists; excluding exempt tasks outright, rather than reporting them at a lower severity, keeps the loop free of noise that can never be fixed.
- **Alternatives considered**: CRITICAL for a missing seam (rejected: collides with the constitution-violation meaning); MEDIUM (rejected: does not trigger the loop).
- **Unchanged**: the approver screen. Engineering findings already reach the user through the judge verdict and the fixed/unresolved lists, and the positive evidence is in `plan.md` and the commit bodies (SC-007).

## D7 - A missing seam at implementation time rides the existing failure policy

- **Decision**: the implementing role returns `failed` naming the task and the missing seam; the orchestrator's existing policy (retry once, then halt and ask) takes over. No new halt reason, stage or state field (FR-011a).
- **Rationale**: the behaviour the user needs (a halt and a question) already exists; adding a dedicated path would duplicate it.
- **Alternatives considered**: letting the role invent a seam (rejected: turns test-first into test-after silently); a new `halt_reason` value (rejected: the existing agent-failure path already notifies and asks).

## D8 - This change's own verification, and the test-runner question

- **Fact**: the repository has no test runner. Its `commands.build` renders every harness; its `commands.test` is `git diff --exit-code -- dist/`.
- **Decision**: the plan declares the whole change documentation/configuration-exempt from test-first with the reason stated, and verifies it with those two commands plus the inspection checks in `quickstart.md` (FR-025, SC-005). FR-018's "set up a test runner first" does not apply, because the change adds no executable behaviour that would need one.
- **Rationale**: a test runner installed to test Markdown instruction files would be machinery with nothing to assert, against constitution V; the render and the generated-output diff are the repository's real, existing correctness checks for instruction changes.
- **Alternatives considered**: adding a prompt-linting test suite (rejected: new dependency, no stated need, out of this feature's scope); claiming a seam that does not exist (rejected: an invented seam is precisely what the feature forbids).
- **Note for future runs**: FR-018 remains in force for features that do add behaviour; the plan's exemption here is scoped to this change only.
