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
- **FR-012**: A task exempt from test-first (documentation or configuration only) MUST be exempt only where the plan states the exemption and its reason; skipping the test-first steps without a stated reason MUST NOT happen.
- **FR-013**: The fixing role MUST follow the same rules as the implementing role when its fix changes behaviour.
- **FR-013a**: The fixing role commits its fixes as one commit and MUST record one `Red:` line in that commit body per behaviour-changing fix, in the same wording as FR-009 and FR-009a.

**Reuse**

- **FR-014**: Before writing a new function or method, the implementing and fixing roles MUST search for an existing one and reuse or extend it when one fits.
- **FR-014a**: That search MUST be bounded, not repository-wide: the module being changed plus the repository's shared utility locations, searched by the concept's keywords, once per new function. **Shared utility locations** means the directories the repository's own conventions name as shared (for example `helpers/`, `utils/`, `util/`, `common/`, `lib/`, `shared/`), plus any module the module being changed already imports for helpers. The search is a keyword-level text search (`grep`-level) over those locations, not a semantic review of the whole repository.
- **FR-015**: The code-standards reviewer MUST flag new code that duplicates an existing helper, and MUST rate real duplication HIGH and blocking.
- **FR-015a**: The code-standards reviewer MUST rate behaviour added with no asserting test HIGH and blocking, the same weight as real duplication.
- **FR-015b**: The spec-conformance reviewer MUST read the run's commit log (`git log <base>..HEAD`, subjects and bodies) in addition to the run's diff, and MUST check each implementation commit body's `Red:` line against `tasks.md`, raising a finding when the line is missing (and the commit's task is not plan-exempt), unparseable, or names a test that no task in `tasks.md` maps to.
- **FR-015d**: The spec-conformance reviewer MUST apply the same check to the fixing role's fix commit, matching each `Red:` line in it against the judge verdict's `confirmed_blocking` findings for that round instead of against `tasks.md`; an unmatched-against-`tasks.md` finding MUST NOT be raised for a fix commit.
- **FR-015e**: The shared findings reference MUST state that a reviewer whose lens needs commit metadata reads the run's commit log as well as the diff, and that a commit-level finding puts the commit sha (with the task id where one applies) in the report's `file` field and omits `line` or sets it to `0`.
- **FR-015c**: The review judge MUST reference the shared rules file so it verifies and rates engineering findings against the same written rules, by id.

**Planning for test-first**

- **FR-016**: The plan MUST contain a "Test seams" section naming the public seams the feature will put under test.
- **FR-017**: The plan MUST state, for any part of the change exempt from test-first, which part and why.
- **FR-018**: The plan MUST make setting up a test runner the first task when the repository has none, and MUST pick the language's conventional default runner, naming the choice and the reason in the plan so the user can object at the approver gate.
- **FR-019**: The task list MUST place a failing-test task immediately before each implementation task, naming the seam it targets; grouping test tasks ahead of a block of implementation tasks does not satisfy this.
- **FR-020**: The analyze stage MUST report a HIGH, blocking finding when an implementation task has no mapped seam, has no test task immediately before it, or names a seam the plan does not list, so the finding triggers the remediation loop; CRITICAL stays reserved for constitution violations.
- **FR-020a**: Tasks the plan declares exempt from test-first (documentation or configuration only, with the reason stated) MUST be excluded from the FR-020 check, not reported at a lower severity.
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

- **SC-001**: In a run on a repository with a test runner, 100% of behaviour-changing tasks have a commit body carrying either a red proof (the test that failed as expected) or a stated exemption (the existing test that already covers the behaviour).
- **SC-002**: In a generated task list, 100% of non-exempt implementation tasks are immediately preceded by a test task naming a seam listed in the plan.
- **SC-003**: Every plan produced after this change contains a test-seams section, and every part of a change not covered by a seam has a stated exemption reason.
- **SC-004**: The engineering rules appear in exactly one source file; each of the code-writing, planning and reviewing roles and the judge reaches them by reference, with zero inline restatements.
- **SC-004a**: Every rule in the reference has a unique `ENG-n` id, and every engineering-rule finding and plan override names one of those ids.
- **SC-005**: After the change, the repository's build and test commands pass, with the generated output showing no difference from its source for every harness.
- **SC-006**: A diff that adds untested behaviour or duplicates an existing helper produces at least one HIGH, blocking review finding naming it, in a trial review.
- **SC-006a**: In a trial review of a run whose implementation commit bodies lack a `Red:` line, the spec-conformance report names every such commit, with zero findings on commits whose proof matches a task in `tasks.md`.
- **SC-007**: A user reading a finished run can tell, from the plan and the commits alone and without reading the code, which seams were tested and which steps were exempt.

## Assumptions

- The shared rules live at `core/skills/factory/references/engineering.md` and are reached through the roles' existing reference mechanism, as settled in the brief.
- Scope of roles: the implementing and fixing roles follow the rules; the planning role plans for them in its own stage instructions (plan's test-seams section, test task before each implementation task, analyze's mapping check, clarify's seam questions); the code-standards reviewer enforces them on the code, the spec-conformance reviewer checks the red proofs in commit bodies, and the review judge rates both against the shared rules. The security, UI and UX reviewers and the orchestrator's flow are unchanged.
- The approver screen is unchanged: engineering-rule findings reach the user through the judge verdict and the fixed/unresolved lists already shown there, and the positive evidence is in `plan.md` and the commit bodies.
- A missing seam at implementation time rides the orchestrator's existing failure policy (retry once, then halt and ask); no new halt reason or stage is introduced.
- The external `tdd` skill is deliberately not used; the factory owns self-contained rules because its agents are stateless and cannot confirm seams with the user mid-loop.
- Functional style is a preference, not a mandate: pure functions, immutable data, side effects at the edges, composition over inheritance, within the language's idiom.
- Red proof is a line in the existing task commit body; no new commit type, state field or artefact is introduced.
- This change edits instructions only (design document, source roles, the new reference, and the regenerated per-harness output). No orchestrator flow stage is added or removed.
- Verification of this feature is by inspection of the changed instruction files plus the repository's existing build and test commands; the end-to-end behaviour is observed on the next real run, per the design document's validation plan.
- Terminology for this feature is fixed in the repository glossary (`CONTEXT.md`); the three decisions with lasting consequences are recorded as `docs/adr/0001-factory-owns-its-engineering-rules.md`, `docs/adr/0002-red-proof-lives-in-the-task-commit-body.md` and `docs/adr/0003-test-seams-are-settled-at-plan-time.md`.
- The repository's constitution continues to apply unchanged; rule overrides are expressed in the consuming repository's own constitution, never by editing the factory's rules per-run.
