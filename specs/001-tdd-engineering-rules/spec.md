# Feature Specification: Engineering discipline for factory code-writing roles

**Feature Branch**: `001-tdd-engineering-rules`

**Created**: 2026-10-22

**Status**: Draft

**Input**: User description: "I want the code build and coding process to always use a TDD approach of writing code. Use the best coding practice, clean code, follow SOLID principles, functional programming, and it should do its best not to over-engineer stuff by always reusing functions/methods if they exist." (settled decisions in `specs/001-tdd-engineering-rules/factory/brief.md`)

## Clarifications

### Session 2026-10-22

- Q: What severity does the analyze stage give an implementation task with no mapped test seam, or with no failing-test task before it? → A: HIGH — blocking, and it triggers the remediation loop. CRITICAL stays reserved for constitution violations. Tasks the plan declares exempt (documentation or configuration only, reason stated) are excluded from the check rather than reported at a lower severity.
- Q: Where is it recorded when a repository's own constitution overrides one of the engineering rules? → A: In `plan.md`, in the plan's engineering/test-seams section, as a line of the form `Overridden: <rule> - <repo rule that wins>`. (Superseded in the grill-with-docs session below: the rule is named by its `ENG-n` id.)
- Q: How does a task prove the red step when an existing passing test already covers the behaviour? → A: The task's commit body records `Red: not applicable - <existing test> already covers this`, and SC-001 is reworded to require a red proof **or** a stated exemption.
- Q: What severity does the code-standards review give behaviour added with no asserting test? → A: HIGH and blocking — the same weight as real duplication.
- Q: When the repository has no test runner, who chooses which one to set up? → A: The plan picks the language's conventional default and states the choice and the reason; the user can object at the approver gate.

### Session 2026-10-22 (grill-with-docs)

- Q: Where is the plan/tasks/analyze test-first behaviour injected? → A: In the planning role's own stage instructions (test-seams section in plan, test task before each implementation task, tests never optional, analyze's seam-mapping check). Factory files only: a run never edits the consuming repository's SpecKit templates, skills or commands.
- Q: Who verifies the red proof in commit bodies? → A: The spec-conformance reviewer. It reads each implementation commit body in the run's diff and checks the `Red:` line against `tasks.md`, raising a finding for a missing, unparseable or unmatched proof.
- Q: Does the review judge reference the engineering rules? → A: Yes. The judge references the shared rules file so it can verify and rate engineering findings on the same written rules the reviewers cited.
- Q: How are the rules referred to in findings and overrides? → A: The shared reference numbers its rules with stable ids (`ENG-1`, `ENG-2`, ...). Reviewers and the judge cite the id, and a repository override reads `Overridden: ENG-n - <repo rule that wins>`.
- Q: How wide is the reuse search before writing a new function? → A: Bounded, not repo-wide: the module being changed plus the repository's shared utility locations, searched by concept keyword, before each new function.
- Q: How does this change satisfy its own rules, given it writes no product code? → A: Its plan declares the whole change documentation/configuration-exempt with the reason stated; the exemption is verified by the repository's own render and generated-output diff commands rather than by new tests.
- Q: How does the fixing role prove red, given it commits all fixes once? → A: One `Red:` line per behaviour-changing fix in that single commit body.
- Q: What happens when implementation needs a seam the plan never listed? → A: The implementing role stops and returns a failure naming the missing seam; the orchestrator's existing failure policy halts the run and asks the user. The role never invents the seam.
- Q: Does the approver screen gain a test-discipline line? → A: No. Engineering-rule findings already reach the approver through the judge verdict and the fixed/unresolved finding lists, and the plan plus commit bodies carry the positive evidence (SC-007). The orchestrator's approver screen is unchanged.

### Session 2026-10-22 (analyze loop 1)

- Q: What severity may a review finding carry when it rests on the clean-code, SOLID, functional-style or over-engineering rules (`ENG-7`..`ENG-10`)? → A: At most MEDIUM, and never blocking: those rules are judgement calls, so they advise rather than halt a run. Only `ENG-6` duplication (FR-015) and behaviour added with no asserting test (FR-015a) stay HIGH and blocking. The judge applies the same ceiling when it rates an engineering finding. (Narrowed in FR-015f: the ceiling is keyed on the cited id, so findings resting on `ENG-1`..`ENG-6` — including red-proof and seam defects — keep the severity their own requirement states.)
- Q: What does the implementing role do when the repository has a test runner but the test command cannot be run (missing dependency, broken configuration, no runner binary)? → A: It stops and returns a failure naming the un-runnable command, exactly as FR-011a handles a missing seam, so the orchestrator's existing failure policy halts the run and asks the user. It never writes implementation code without an observed red step, and the red proof keeps exactly its two accepted forms (FR-009, FR-009a) — "could not run the tests" is not a third form.

### Session 2026-10-22 (grill-with-docs, analyze loop 1)

- Q: Do advisory engineering findings (`ENG-7`..`ENG-10`, FR-015f) ever get fixed inside the run? → A: No. They are information for the user: they reach the user through the judge verdict's advisory list and the approver screen, and the fixing role performs no work on them. A user who wants one fixed uses the approver's existing "Request changes", which sends the run back with that finding named. No new gate, list or stage is added.
- Q: Is there a plan-time gate for over-engineering (`ENG-10`), or is it review-only? → A: Plan-time too, but soft: `plan.md` MUST state a reason for each new file, new abstraction and new dependency it introduces, and the analyze stage reports a MEDIUM, **non-blocking** finding when a reason is missing. It never blocks, because the judgement-call ceiling of FR-015f applies to `ENG-10` at artifact time as well.
- Q: Does FR-011b's un-runnable-test-command stop bind the fixing role as well as the implementing role? → A: Yes. The fixing role stops the same way and returns a failure naming the un-runnable command and its error; it never writes a behaviour-changing fix with no observed red step.

### Session 2026-10-22 (grill-with-docs, analyze loop 2)

No new open design decision arose: remediation pass 2 settled every finding inside the artifacts. The two decisions it made that outlive this run were recorded in the documents rather than re-asked, and the terms they rest on are now in `CONTEXT.md`:

- How a fix commit that answers the user's "Request changes" is verified, since it matches no `confirmed_blocking` finding → A **user-changes fix round** is checked for the grammar of each `Red:` line and for one line per behaviour-changing fix in its diff, against neither the verdict nor `tasks.md` (FR-015d, `contracts/commit-body.md`, `docs/adr/0002`). Matching the request's prose was rejected: a change request is not a finding list and two reviewers would disagree.
- How an advisory finding keeps its `ENG-n` citation in the judge verdict → In the existing `advisory[]` entry: the id is named in `summary` and the full evidence is reachable through `sources`, so no verdict field is added (constitution V, `docs/adr/0004`).

## User Scenarios & Testing *(mandatory)*

The actors here are the factory's roles (the agents a `/factory` run spawns) and the user who starts a run. The "system" is the factory's instruction set: the design document, the shared engineering reference, the role prompts, and the rendered per-harness copies of them.

### User Story 1 - Code is written test-first (Priority: P1)

A user starts a `/factory` run on a feature. The implementing role works task by task, and for each behaviour it writes a test that fails first, then the smallest code that makes it pass, then refactors while the tests stay green. The user can see, in the run's commit history, that each implementation step was driven by a test that was observed failing.

**Why this priority**: This is the core of the request. Without it, nothing else in the feature has value.

**Independent Test**: Run the factory on a small feature and inspect the resulting commits: each implementation commit body states the test that was seen failing, and the test exists and asserts the behaviour the task added.

**Acceptance Scenarios**:

1. **Given** a task that adds behaviour to code, **When** the implementing role starts the task, **Then** it writes or extends a test for that behaviour, runs it, and confirms it fails before writing implementation code.
2. **Given** a test that has been seen failing, **When** the role implements the behaviour, **Then** it writes only enough code to make that test pass, refactors only while the tests are green, and re-runs the tests after refactoring.
3. **Given** a finished task, **When** the role commits it, **Then** the commit body records the name of the test that failed as expected (or, where an existing passing test already covered the behaviour, that test as the stated exemption), and the task's test and implementation changes are in that one commit (no separate red commit).
4. **Given** a task that only changes documentation or configuration, **When** the plan has stated the exemption and its reason, **Then** the role implements it without a test and no step is skipped silently.
5. **Given** a task needing a seam the plan never listed, **When** the implementing role reaches it, **Then** it stops and reports the missing seam as a failure, the run halts, and the user is asked instead of a seam being invented.
6. **Given** a fixing role resolving several behaviour-changing findings in one commit, **When** it commits, **Then** that commit body carries one `Red:` line per behaviour-changing fix.
7. **Given** a repository whose test runner exists but whose test command cannot be run, **When** the implementing role tries to observe the red step, **Then** it stops and returns a failure naming the un-runnable command and its error, the run halts, and the user is asked instead of implementation code being written with no observed red step.
8. **Given** that same un-runnable test command, **When** the fixing role tries to observe the red step for a behaviour-changing fix, **Then** it stops and returns a failure naming the un-runnable command and its error, exactly as the implementing role does, instead of committing the fix with no red proof.

---

### User Story 2 - The run plans for test-first work (Priority: P1)

Before any code is written, the planning artefacts already say what will be tested and how. The plan names the public seams under test; the task list puts a failing-test task in front of every implementation task; when the repository has no test runner, setting one up is the first task.

**Why this priority**: A stateless implementing role cannot stop mid-loop to agree seams with the user, so the seams must be settled at plan time. Equal priority to Story 1: test-first work without agreed seams degrades into invented seams.

**Independent Test**: Run the spec stages on a small feature and inspect `plan.md` and `tasks.md`: the plan has a test-seams section listing public seams, and every implementation task in `tasks.md` is preceded by a test task that targets one of those seams.

**Acceptance Scenarios**:

1. **Given** the plan stage, **When** the plan is written, **Then** it contains a "Test seams" section naming the public seams that will be put under test, and states the exemption and reason for any part of the change that is documentation or configuration only.
2. **Given** a repository with no test runner, **When** the plan is written, **Then** setting up the test runner is the first task in the task list, and the plan names the language's conventional default runner it chose and why.
3. **Given** the tasks stage, **When** the task list is written, **Then** each implementation task is immediately preceded by a task that writes a failing test for the seam that task implements.
4. **Given** seams that the feature description leaves ambiguous, **When** the clarify stage runs, **Then** it asks the user about those seams; when the seams are clear, it asks nothing about them.
5. **Given** a written plan and task list, **When** the analyze stage runs, **Then** it reports a HIGH, blocking finding for any non-exempt implementation task with no mapped seam, with no test task immediately before it, or naming a seam the plan does not list, and reports nothing for tasks the plan declares exempt.
6. **Given** a plan that introduces a new file, a new abstraction or a new dependency without stating why, **When** the analyze stage runs, **Then** it reports a MEDIUM, non-blocking finding naming that file, abstraction or dependency, so the run is not halted, the analyze loop's blocking path is not triggered, and the user sees the omission in the analyze report.

---

### User Story 3 - Review enforces the discipline (Priority: P2)

The reviewing roles check the run's diff against the same written rules the implementing role followed, so a run that skipped a test, duplicated an existing helper, or ignored the design rules does not pass review unnoticed. The code-standards reviewer judges the code itself; the spec-conformance reviewer checks each implementation commit body's red proof against the task list; the judge rates both against the same rule ids.

**Why this priority**: Enforcement closes the loop, but the discipline already has value from stories 1 and 2 before review is tightened.

**Independent Test**: Hand the code-standards reviewer a diff that adds behaviour with no test and a function duplicating an existing helper; it returns both as HIGH blocking findings citing rule ids. Hand the spec-conformance reviewer a commit whose body has no `Red:` line; it returns that as a finding.

**Acceptance Scenarios**:

1. **Given** a diff that adds behaviour with no test asserting it, **When** review runs, **Then** a HIGH, blocking finding cites the engineering rules and names the untested behaviour.
2. **Given** a diff with new code that duplicates an existing function in the repository, **When** review runs, **Then** a HIGH, blocking finding names the existing function that should have been reused or extended.
3. **Given** a diff that follows the rules, **When** review runs, **Then** no engineering-rule finding is raised on style preference alone.
4. **Given** an implementation commit whose body has no `Red:` line, or names a test no task maps to, **When** the spec-conformance review runs, **Then** it reads the run's commit log, raises a finding naming that commit (the sha in `file`) and the task it belongs to.
5. **Given** any engineering-rule finding, **When** it is written and when the judge rates it, **Then** both cite the rule's id (`ENG-n`) from the shared reference.
6. **Given** a fix commit carrying one `Red:` line per behaviour-changing fix, **When** the spec-conformance review runs, **Then** it matches each line against the round's confirmed blocking findings and raises nothing, instead of reporting the lines as unmatched against `tasks.md`.
7. **Given** a diff whose only engineering weakness rests on clean code, SOLID, functional style or over-engineering (`ENG-7`..`ENG-10`), **When** the review runs and the judge rates the finding, **Then** it is at most MEDIUM and non-blocking, so it advises the user without halting the run, while a finding in the same diff citing `ENG-1`..`ENG-6` (duplication, untested behaviour, a missing `Red:` line, a seam defect) keeps its own HIGH and blocking weight.
8. **Given** such an advisory engineering finding in the verdict, **When** the verdict-driven fix round runs and the approver screen is shown, **Then** no fix work is performed on it and the user reads it in the verdict's advisory list, able to send it back with the approver's existing "Request changes" — and when the user does, the fixing role implements that request exactly as asked.

---

### User Story 4 - One shared set of rules, carried to every harness (Priority: P2)

The rules exist once, in a single harness-neutral reference. Every role that writes, plans or reviews code points at that one file, and every harness's installed copy of the factory carries the same rules.

**Why this priority**: Prevents the rules drifting between roles and harnesses, which would make the discipline unenforceable. Required by the repository's constitution.

**Independent Test**: Grep the roles for engineering rules: the rules appear in one reference file only, each relevant role references it, and the rendered output for every harness contains that reference and matches its source.

**Acceptance Scenarios**:

1. **Given** the rules reference, **When** a role needs the rules, **Then** the role points at the shared reference instead of restating the rules inline.
2. **Given** a change to the rules, **When** the change is made, **Then** the design document is updated first, then the source roles and reference, then the generated per-harness output is re-rendered and committed with the source change.
3. **Given** the rendered output, **When** the repository's test command runs, **Then** no difference is reported between the generated output and its source.
4. **Given** a repository whose own constitution or documented conventions contradict a rule, **When** a run works in that repository, **Then** the repository's documented rule wins and `plan.md` records the override as `Overridden: ENG-n - <repo rule that wins>`.

---

### Edge Cases

- A change that is documentation or configuration only: exempt from test-first, with the reason stated in the plan; the exemption is never implicit.
- A repository with no test runner: a setup task comes first, so the first behaviour task has somewhere to put its failing test.
- A behaviour whose test cannot be made to fail first (for example, behaviour already covered by an existing passing test): the commit body records `Red: not applicable - <existing test> already covers this`, rather than silently skipping the red step.
- A seam the plan did not list but a task clearly needs: the implementing role does not invent it; analyze should have caught the gap beforehand, and if it reaches implementation the role returns a failure naming the missing seam and the run halts for the user.
- A fix commit's red proofs: they name tests written for confirmed findings, not for tasks, so the spec-conformance reviewer matches them against the round's verdict and never reports them as unmatched against `tasks.md` (FR-015d).
- A repository whose test runner exists but whose test command cannot be run: the implementing role, and equally the fixing role (FR-013b), stops and returns a failure naming the un-runnable command and its error (FR-011b), the run halts for the user, and no behaviour-changing code is written without an observed red step. This is the same stop-and-report pattern as a missing seam (FR-011a), not a new halt reason.
- A weakness that is only a judgement call (clean code, SOLID, functional style, over-engineering): the finding is raised at most MEDIUM and non-blocking (FR-015f), so the run is not halted on taste; duplication, untested behaviour, red-proof defects and seam defects keep their own HIGH and blocking weight, because the ceiling is keyed on the cited id (`ENG-7`..`ENG-10`) and not on the word "engineering".
- An advisory engineering finding the user wants fixed: no verdict-driven fix round acts on it (FR-015g); the user names it at the approver gate with "Request changes", which is the existing route back into the run, and the fixing role then implements that request exactly as asked.
- A plan that introduces a new file, abstraction or dependency with no stated reason: analyze reports it MEDIUM and non-blocking (FR-020b), so the run is never halted and the analyze loop's blocking path is never triggered by it; the finding reaches the user in the analyze report, and the remediate stage writes the missing reason as it does for any other MEDIUM finding.
- A reuse search that finds nothing in the changed module or the shared utility locations: the role writes the new function; the search is bounded on purpose and is not widened to the whole repository.
- An existing function that is close but not an exact fit: extending it is preferred over a near-duplicate; a genuinely different concern may be new code, with the difference stated.
- A language or repository whose idiom is not functional (for example, a framework demanding inheritance): the functional preferences yield to the language's and repository's idiom.
- A rule the repository's constitution overrides: the override is honoured and named in `plan.md` as `Overridden: ENG-n - <repo rule that wins>`; the factory's own rules are not edited per-run.
- A repository whose SpecKit templates or commands differ from the factory's expectations: the factory adapts in its own role instructions and never edits the consuming repository's SpecKit files.
- A repository with no test runner and no stated preference: the plan picks the language's conventional default, names it with the reason, and the user can object at the approver gate instead of being asked mid-run.

## Requirements *(mandatory)*

### Functional Requirements

**Shared rules**

- **FR-001**: The factory MUST hold its engineering rules in one shared, harness-neutral reference file; no role restates them inline.
- **FR-002**: The shared rules MUST be self-contained, with no dependency on any skill outside the factory.
- **FR-003**: The shared rules MUST cover: test-first (red-green-refactor), clean code, SOLID design, preferred functional style, and reuse-before-writing.
- **FR-004**: The code-writing roles (implementing, fixing), the planning role, the code-standards reviewer, the spec-conformance reviewer and the review judge MUST each reference the shared rules file.
- **FR-004a**: Each rule in the shared reference MUST carry a stable numbered id (`ENG-1`, `ENG-2`, ...), and reviewers and the judge MUST cite the id of the rule a finding rests on.
- **FR-005**: The rules MUST apply to every run by default; a repository's own constitution MAY override a specific rule, and the run MUST record the override in `plan.md`, in the plan's engineering/test-seams section, as `Overridden: ENG-n - <repo rule that wins>`.
- **FR-006**: The rules MUST state that the repository's documented conventions win over the factory's stylistic preferences when the two conflict.
- **FR-006a**: The test-first behaviour of the plan, tasks and analyze stages MUST be carried in the planning role's own stage instructions inside the factory's files; a run MUST NOT edit the consuming repository's SpecKit templates, skills or commands.

**Test-first in implementation**

- **FR-007**: The implementing role MUST, for each task that changes behaviour, write or extend a test, run it, and observe it fail before writing implementation code. A unit of work (task or fix) is **behaviour-changing** when it changes what an entry point returns or does; a change confined to documentation, configuration or generated output is not behaviour-changing. This definition is the trigger for FR-009, FR-013a and SC-001.
- **FR-008**: The implementing role MUST then write the smallest code that makes the test pass, refactor only while the tests are green, and re-run the tests after refactoring, all inside the same task.
- **FR-009**: The implementing role MUST record proof of the red step in the task's commit body as `Red: <test name> failed as expected`.
- **FR-009a**: Where an existing passing test already covers the behaviour and so cannot be made to fail first, the commit body MUST instead record `Red: not applicable - <existing test> already covers this`; no other wording stands in for a red proof.
- **FR-010**: Each task MUST be committed as one commit containing its test and implementation changes; separate red commits MUST NOT be created, so history stays bisectable.
- **FR-011**: The implementing role MUST NOT invent test seams: it uses the seams the plan lists.
- **FR-011a**: When a task needs a seam the plan does not list, the implementing role MUST stop and return a failure naming the task and the missing seam, so the orchestrator's existing failure policy halts the run and asks the user. It MUST NOT proceed with an invented seam and MUST NOT silently drop the test.
- **FR-011b**: When the repository has a test runner but its test command cannot be run (missing dependency, broken configuration, or no runner binary), the implementing role MUST stop and return a failure naming the task and the un-runnable command with the error it produced, so the orchestrator's existing failure policy halts the run and asks the user. It MUST NOT write implementation code without an observed red step, and MUST NOT record any third form of red proof: the two forms of FR-009 and FR-009a remain the only accepted ones.
- **FR-012**: A task exempt from test-first (documentation or configuration only) MUST be exempt only where the plan states the exemption and its reason; skipping the test-first steps without a stated reason MUST NOT happen.
- **FR-013**: The fixing role MUST follow the same rules as the implementing role when its fix changes behaviour.
- **FR-013a**: The fixing role commits its fixes as one commit and MUST record one `Red:` line in that commit body per behaviour-changing fix, in the same wording as FR-009 and FR-009a.
- **FR-013b**: FR-011b binds the fixing role as well: when the test command cannot be run, the fixing role MUST stop and return a failure naming the un-runnable command and the error it produced, so the orchestrator's existing failure policy halts the run and asks the user. It MUST NOT commit a behaviour-changing fix without an observed red step and MUST NOT record any third form of red proof.

**Reuse**

- **FR-014**: Before writing a new function or method, the implementing and fixing roles MUST search for an existing one and reuse or extend it when one fits.
- **FR-014a**: That search MUST be bounded, not repository-wide: the module being changed plus the repository's shared utility locations, searched by the concept's keywords, once per new function. **Shared utility locations** means the directories the repository's own conventions name as shared (for example `helpers/`, `utils/`, `util/`, `common/`, `lib/`, `shared/`), plus any module the module being changed already imports for helpers. The search is a keyword-level text search (`grep`-level) over those locations, not a semantic review of the whole repository.
- **FR-015**: The code-standards reviewer MUST flag new code that duplicates an existing helper, and MUST rate real duplication HIGH and blocking.
- **FR-015a**: The code-standards reviewer MUST rate behaviour added with no asserting test HIGH and blocking, the same weight as real duplication.
- **FR-015b**: The spec-conformance reviewer MUST read the run's commit log (`git log <base>..HEAD`, subjects and bodies) in addition to the run's diff, and MUST check each implementation commit body's `Red:` line against `tasks.md`, raising a finding when the line is missing (and the commit's task is not plan-exempt), unparseable, or names a test that no task in `tasks.md` maps to.
- **FR-015c**: The review judge MUST reference the shared rules file so it verifies and rates engineering findings against the same written rules, by id.
- **FR-015d**: The spec-conformance reviewer MUST apply the same check to the fixing role's fix commit, matching each `Red:` line in it against the judge verdict's `confirmed_blocking` findings for that round instead of against `tasks.md`; an unmatched-against-`tasks.md` finding MUST NOT be raised for a fix commit. A fix commit of a **user-changes fix round** (subject `factory(fix): user changes`, or a round whose verdict carries no `confirmed_blocking` entries) answers the user and no verdict: it MUST be checked only for the grammar of each `Red:` line it carries and for one such line per behaviour-changing fix its diff shows, MUST be matched against neither the verdict nor `tasks.md`, and an empty `confirmed_blocking` list MUST NOT by itself be a finding.
- **FR-015e**: The shared findings reference MUST state that a reviewer whose lens needs commit metadata reads the run's commit log as well as the diff, and that a commit-level finding puts the commit sha (with the task id where one applies) in the report's `file` field and omits `line` or sets it to `0`.
- **FR-015f**: A review finding **whose cited id is `ENG-7`, `ENG-8`, `ENG-9` or `ENG-10`** MUST be rated at most MEDIUM and MUST NOT be blocking, by both the reviewer that raises it and the judge that rates it. The ceiling applies to those four ids only: a finding resting on `ENG-1`..`ENG-6` keeps the severity its own requirement states — HIGH and blocking for real duplication (`ENG-6`, FR-015), for behaviour added with no asserting test (FR-015a), for a missing, unparseable or unmatched `Red:` line (`ENG-2`, FR-015b, FR-015d) and for a seam defect (`ENG-4`, FR-020). A finding above the ceiling MUST be lowered to MEDIUM rather than dropped, so the user still sees it. This ceiling MUST override any higher severity the shared findings reference's default severity guidance would give a finding citing one of those four ids, and MUST NOT be read as licence to lower any other engineering finding.
- **FR-015g**: An engineering finding held at or below the FR-015f ceiling is advisory: a **verdict-driven fix round** MUST NOT perform fix work on it. It MUST reach the user through the judge verdict's advisory list and the orchestrator's existing approver screen, and the user's route to having it fixed is the approver's existing "Request changes" — a change request that names an advisory finding is implemented exactly as asked, like any other request. No new gate, list, severity or stage is introduced for it.

**Planning for test-first**

- **FR-016**: The plan MUST contain a "Test seams" section naming the public seams the feature will put under test.
- **FR-017**: The plan MUST state, for any part of the change exempt from test-first, which part and why.
- **FR-018**: The plan MUST make setting up a test runner the first task when the repository has none, and MUST pick the language's conventional default runner, naming the choice and the reason in the plan so the user can object at the approver gate.
- **FR-019**: The task list MUST place a failing-test task immediately before each implementation task, naming the seam it targets; grouping test tasks ahead of a block of implementation tasks does not satisfy this.
- **FR-020**: The analyze stage MUST report a HIGH, blocking finding when an implementation task has no mapped seam, has no test task immediately before it, or names a seam the plan does not list, so the finding triggers the remediation loop; CRITICAL stays reserved for constitution violations.
- **FR-020a**: Tasks the plan declares exempt from test-first (documentation or configuration only, with the reason stated) MUST be excluded from the FR-020 check, not reported at a lower severity.
- **FR-020b**: The plan MUST state a reason for each new file, new abstraction and new dependency it introduces (`ENG-10`), and the analyze stage MUST report a MEDIUM, **non-blocking** finding naming any one of them whose reason is missing. This finding MUST NOT block the run or by itself trigger the remediation loop's blocking path.
- **FR-021**: The clarify stage MUST ask the user about test seams only when the seams are ambiguous.

**Carrying the change through the repository**

- **FR-022**: The design document MUST be updated before the roles and reference, in the same change.
- **FR-023**: The generated per-harness output MUST be re-rendered for every harness and committed with the source change, with no hand edits to generated files.
- **FR-024**: Role prompts MUST stay short, imperative and unambiguous, and the shared reference MUST use one term per concept throughout.
- **FR-025**: This change's own plan MUST declare the whole change documentation/configuration-exempt from test-first, with the reason stated, and MUST verify it instead by the repository's render command and its generated-output diff command.

### Key Entities

- **Engineering rules reference**: the single shared statement of the discipline (test-first, clean code, SOLID, functional preference, reuse) that roles point at.
- **Rule id**: the stable `ENG-n` label of one rule in the reference; the token findings, judge verdicts and plan overrides use to name a rule.
- **Test seam**: a public entry point of the change that is put under test, agreed at plan time and named by the tasks that test and implement it.
- **Red proof**: the recorded evidence, in a task's commit body, that the task's test was seen failing before the implementation existed; where an existing passing test already covers the behaviour, the stated exemption naming that test takes its place.
- **Test-first exemption**: a documentation- or configuration-only part of a change, declared in the plan with its reason.
- **Code-writing role**: a role that changes code in a run; bound by the rules directly. Exactly two, and these are the only names this spec uses for them: the implementing role (`code-build`) and the fixing role (`fixer`).
- **Planning role**: the role producing the plan, task list and analyze report (`spec-builder`); makes the discipline plannable and checkable.
- **Reviewing roles**: the code-standards reviewer (`code-standards`, diff against the rules), the spec-conformance reviewer (`spec-conformance`, commit bodies' red proofs against the task list) and the review judge (`review-judge`, rating both by rule id); together they make the discipline enforceable.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In a run on a repository with a test runner, 100% of behaviour-changing tasks have a commit body carrying either a red proof (the test that failed as expected) or a stated exemption (the existing test that already covers the behaviour); a run whose test command cannot be run halts (FR-011b) instead of producing such a commit with no proof.
- **SC-002**: In a generated task list, 100% of non-exempt implementation tasks are immediately preceded by a test task naming a seam listed in the plan.
- **SC-003**: Every plan produced after this change contains a test-seams section, and every part of a change not covered by a seam has a stated exemption reason.
- **SC-003a**: In a plan produced after this change, 100% of the new files, new abstractions and new dependencies it introduces carry a stated reason, and any that do not appear in the analyze report as MEDIUM, non-blocking findings.
- **SC-004**: The engineering rules appear in exactly one source file; each of the code-writing, planning and reviewing roles and the judge reaches them by reference, with zero inline restatements.
- **SC-004a**: Every rule in the reference has a unique `ENG-n` id, and every engineering-rule finding and plan override names one of those ids.
- **SC-005**: After the change, the repository's build and test commands pass, with the generated output showing no difference from its source for every harness.
- **SC-006**: A diff that adds untested behaviour or duplicates an existing helper produces at least one HIGH, blocking review finding naming it, in a trial review.
- **SC-006a**: In a trial review of a run whose implementation commit bodies lack a `Red:` line, the spec-conformance report names every such commit, with zero findings on commits whose proof matches a task in `tasks.md`.
- **SC-006b**: In the SC-006 trial review, every finding resting on `ENG-7`..`ENG-10` is MEDIUM or lower and none is blocking, so zero runs halt on a clean-code, SOLID, functional-style or over-engineering finding alone.
- **SC-006c**: In the SC-006 trial review, zero verdict-driven fix-round changes are made for advisory engineering findings, and every one of them is readable by the user in the verdict's advisory list with its `ENG-n` id named in the entry's `summary`.
- **SC-007**: A user reading a finished run can tell, from the plan and the commits alone and without reading the code, which seams were tested and which steps were exempt.

## Assumptions

- The shared rules live at `core/skills/factory/references/engineering.md` and are reached through the roles' existing reference mechanism, as settled in the brief.
- Scope of roles: the implementing and fixing roles follow the rules; the planning role plans for them in its own stage instructions (plan's test-seams section, test task before each implementation task, analyze's mapping check, clarify's seam questions); the code-standards reviewer enforces them on the code, the spec-conformance reviewer checks the red proofs in commit bodies, and the review judge rates both against the shared rules. The security, UI and UX reviewers and the orchestrator's flow are unchanged.
- The approver screen is unchanged: engineering-rule findings reach the user through the judge verdict and the fixed/unresolved lists already shown there, and the positive evidence is in `plan.md` and the commit bodies.
- A missing seam at implementation time, and a test command that exists but cannot be run, both ride the orchestrator's existing failure policy (retry once, then halt and ask); no new halt reason or stage is introduced, and the stop binds the fixing role on the same terms as the implementing role (FR-013b).
- Advisory engineering findings (`ENG-7`..`ENG-10`, FR-015f) are information for the user, not work a verdict-driven fix round performs. They travel to the user in the judge verdict's advisory list and the existing approver screen, and the user sends any of them back into the run with the approver's existing "Request changes" (FR-015g), which the fixing role implements exactly as asked, like any other change request. No new gate, list, severity or stage is added.
- The over-engineering gate at plan time is soft on purpose (FR-020b): a missing reason for a new file, abstraction or dependency is a MEDIUM, non-blocking analyze finding, because `ENG-10` is a judgement call and the FR-015f ceiling applies to artifacts as well as to diffs. Non-blocking means it never halts the run and never by itself triggers the analyze loop's blocking path; like any other MEDIUM finding it is remediated once and reaches the user through the analyze report.
- Severity for engineering findings has a ceiling by cited rule id, not by reviewer judgement: `ENG-7`..`ENG-10` advise at MEDIUM, while `ENG-1`..`ENG-6` findings (duplication, untested behaviour, red-proof defects, seam defects) keep the severity their own requirement states. The existing judge verdict shape carries both; no new severity level or field is introduced — an advisory entry derived from an engineering finding names the `ENG-n` id in its existing `summary` and links the full evidence through its existing `sources`.
- The external `tdd` skill is deliberately not used; the factory owns self-contained rules because its agents are stateless and cannot confirm seams with the user mid-loop.
- Functional style is a preference, not a mandate: pure functions, immutable data, side effects at the edges, composition over inheritance, within the language's idiom.
- Red proof is a line in the existing task commit body; no new commit type, state field or artefact is introduced.
- This change edits instructions only (design document, source roles, the new reference, and the regenerated per-harness output). No orchestrator flow stage is added or removed.
- Verification of this feature is by inspection of the changed instruction files plus the repository's existing build and test commands; the end-to-end behaviour is observed on the next real run, per the design document's validation plan.
- Terminology for this feature is fixed in the repository glossary (`CONTEXT.md`); the four decisions with lasting consequences are recorded as `docs/adr/0001-factory-owns-its-engineering-rules.md`, `docs/adr/0002-red-proof-lives-in-the-task-commit-body.md`, `docs/adr/0003-test-seams-are-settled-at-plan-time.md` and `docs/adr/0004-judgement-call-rules-advise-they-never-block.md`.
- The repository's constitution continues to apply unchanged; rule overrides are expressed in the consuming repository's own constitution, never by editing the factory's rules per-run.
