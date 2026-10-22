# Phase 0 Research: Engineering discipline for factory code-writing roles

No `NEEDS CLARIFICATION` marker survives into the Technical Context: the brief, the clarify sessions, the grill-with-docs sessions and the four ADRs settled every open question. This file records the decisions that shape the plan, and the facts about this repository that the plan rests on. D9..D12 were added on analyze loop 1, for the requirements the loop settled (FR-011b, FR-013b, FR-015f, FR-015g, FR-020b, and the verdict source of FR-015d).

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
- **Refined on analyze loop 1**: the HIGH-and-blocking weight above is scoped to `ENG-6` duplication and untested added behaviour. Findings resting on `ENG-7`..`ENG-10` are capped at MEDIUM and never block (D9), and a missing plan-time reason for a new file, abstraction or dependency is MEDIUM and non-blocking (D11).

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
- **Scope of FR-011b here**: the stop on an un-runnable test command cannot fire in this change, because this repository has no test runner and no task of this change invokes one. The whole-change exemption (FR-025) therefore stands unchanged.

## D9 - Judgement-call rules advise; they never block, and never cause fix work

- **Decision**: a finding resting on `ENG-7`..`ENG-10` (clean code, SOLID, functional style, over-engineering) is rated at most MEDIUM and is never blocking, by the reviewer that raises it and by the judge that rates it; a finding above the ceiling is lowered rather than dropped. Such a finding is advisory: no fix round acts on it; it reaches the user in the verdict's `advisory[]` list and the existing approver screen, and the user's route to having it fixed is the approver's existing "Request changes" (FR-015f, FR-015g, SC-006b, SC-006c). Recorded as ADR 0004.
- **Rationale**: these four rules are taste with a wide honest range, so blocking on them would halt runs on disagreement rather than on defects, and auto-fixing them would let a reviewer's preference rewrite working code with no user consent. `ENG-6` duplication and untested added behaviour stay HIGH and blocking because both are objectively checkable.
- **Fact about the existing machinery**: `core/skills/factory/references/findings.md` ("Reviewer report") states a default — "`blocking`: the reviewer's call; `critical` and `high` are blocking unless the reviewer says why not" — and the judge verdict already carries an `advisory[]` list that the approver screen shows. So the ceiling needs no new field, list, severity or stage: it needs one stated exception to that default line.
- **Consequence for the plan**: `findings.md` must carry the ceiling **as an override of its own default severity guidance** (FR-015f), otherwise two instructions in the same file contradict each other and a reviewer may follow either. The same ceiling is repeated nowhere else as a rule: `code-standards.md` and `review-judge.md` point at it.
- **Alternatives considered**: leaving severity to reviewer judgement (rejected: the same diff then passes one run and halts another); dropping judgement-call findings entirely (rejected: the user loses information SC-006c requires to be readable); a new "advisory" severity (rejected: a new level for a distinction `blocking` already carries, against constitution V).

## D10 - An un-runnable test command stops the run, for both code-writing roles

- **Decision**: when the repository has a test runner but its test command cannot be run (missing dependency, broken configuration, no runner binary), the implementing role, and equally the fixing role, stops and returns `failed` naming the task or fix, the un-runnable command and the error it produced; the orchestrator's existing failure policy (retry once, then halt and ask) takes over. No third form of red proof is introduced: the two forms of FR-009 and FR-009a stay the only accepted ones (FR-011b, FR-013b).
- **Rationale**: identical in shape to D7's missing seam, so it reuses the same path and the same wording; the alternative — writing code with no observed red step — is exactly the silent degradation into test-after that this feature exists to prevent.
- **Alternatives considered**: recording "could not run the tests" as a red proof (rejected: unverifiable, and it would make SC-001 meaningless); skipping the test for that task (rejected: an undeclared exemption, against FR-012); a new `halt_reason` (rejected: the existing agent-failure path already notifies and asks).
- **Consequence for the plan**: one line in `code-build.md` and the same line in `fixer.md`; no orchestrator or state change.

## D11 - The over-engineering gate at plan time is soft

- **Decision**: `plan.md` states a reason for each new file, new abstraction and new dependency it introduces, and the analyze stage reports a **MEDIUM, non-blocking** finding naming any one of them whose reason is missing (FR-020b, SC-003a). It never blocks and never by itself triggers the remediation loop's blocking path.
- **Rationale**: `ENG-10` is a judgement call, so the FR-015f ceiling applies at artifact time as well as to diffs; a blocking gate would stop runs over a missing sentence. A MEDIUM finding still makes the omission visible to the user and to the next pass. The repository's own constitution (V) already demands the reason for a new file, so the check also carries a principle this repository holds.
- **Alternatives considered**: HIGH and blocking (rejected: contradicts FR-015f and would halt a run on a wording omission); no plan-time check at all (rejected: the only other `ENG-10` check is review-time, after the file already exists); refusing the plan at the approver gate (rejected: the approver screen is explicitly unchanged).
- **Consequence for the plan**: one analyze-table row in `contracts/plan-artifact.md`, the plan's own "Reasons for new files, abstractions and dependencies" section as the worked example, and the check in `spec-builder.md`.

## D12 - The verdict a fix commit is matched against is a named file

- **Fact**: the orchestrator saves each round's judge verdict at `<spec_dir>/factory/reviews/round-<n>/verdict.json` (`core/skills/factory/SKILL.md`, review step 4), alongside each reviewer's report in the same folder.
- **Decision**: FR-015d's "the round's verdict" is pinned to that path: a spec-conformance reviewer running in round `n` matches the fix commit's `Red:` lines against `confirmed_blocking` in `<spec_dir>/factory/reviews/round-<n-1>/verdict.json`, because the fix commit it is looking at was produced from the previous round's verdict. In round 1 there is no fix commit and no such file, so the check does not apply.
- **Rationale**: a stateless reviewer cannot be told "the round's verdict" and find it; it needs a path it can read in one spawn (constitution IV). The file already exists, so nothing is added.
- **Alternatives considered**: passing the confirmed findings to the reviewer in its spawn inputs (rejected: changes the orchestrator's review step, which this feature leaves unchanged); re-deriving them from the fix commit's subject (rejected: the subject carries finding ids but not their severity or their behaviour-changing status).
