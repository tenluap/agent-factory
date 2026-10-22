# Feature Specification: Engineering discipline for factory code-writing roles

**Feature Branch**: `001-tdd-engineering-rules`

**Created**: 2026-10-22

**Status**: Draft

**Input**: User description: "I want the code build and coding process to always use a TDD approach of writing code. Use the best coding practice, clean code, follow SOLID principles, functional programming, and it should do its best not to over-engineer stuff by always reusing functions/methods if they exist." (settled decisions in `specs/001-tdd-engineering-rules/factory/brief.md`)

## User Scenarios & Testing *(mandatory)*

The actors here are the factory's roles (the agents a `/factory` run spawns) and the user who starts a run. The "system" is the factory's instruction set: the design document, the shared engineering reference, the role prompts, and the rendered per-harness copies of them.

### User Story 1 - Code is written test-first (Priority: P1)

A user starts a `/factory` run on a feature. The implementing role works task by task, and for each behaviour it writes a test that fails first, then the smallest code that makes it pass, then refactors while the tests stay green. The user can see, in the run's commit history, that each implementation step was driven by a test that was observed failing.

**Why this priority**: This is the core of the request. Without it, nothing else in the feature has value.

**Independent Test**: Run the factory on a small feature and inspect the resulting commits: each implementation commit body states the test that was seen failing, and the test exists and asserts the behaviour the task added.

**Acceptance Scenarios**:

1. **Given** a task that adds behaviour to code, **When** the implementing role starts the task, **Then** it writes or extends a test for that behaviour, runs it, and confirms it fails before writing implementation code.
2. **Given** a test that has been seen failing, **When** the role implements the behaviour, **Then** it writes only enough code to make that test pass, refactors only while the tests are green, and re-runs the tests after refactoring.
3. **Given** a finished task, **When** the role commits it, **Then** the commit body records the name of the test that failed as expected, and the task's test and implementation changes are in that one commit (no separate red commit).
4. **Given** a task that only changes documentation or configuration, **When** the plan has stated the exemption and its reason, **Then** the role implements it without a test and no step is skipped silently.

---

### User Story 2 - The run plans for test-first work (Priority: P1)

Before any code is written, the planning artefacts already say what will be tested and how. The plan names the public seams under test; the task list puts a failing-test task in front of every implementation task; when the repository has no test runner, setting one up is the first task.

**Why this priority**: A stateless implementing role cannot stop mid-loop to agree seams with the user, so the seams must be settled at plan time. Equal priority to Story 1: test-first work without agreed seams degrades into invented seams.

**Independent Test**: Run the spec stages on a small feature and inspect `plan.md` and `tasks.md`: the plan has a test-seams section listing public seams, and every implementation task in `tasks.md` is preceded by a test task that targets one of those seams.

**Acceptance Scenarios**:

1. **Given** the plan stage, **When** the plan is written, **Then** it contains a "Test seams" section naming the public seams that will be put under test, and states the exemption and reason for any part of the change that is documentation or configuration only.
2. **Given** a repository with no test runner, **When** the plan is written, **Then** setting up the test runner is the first task in the task list.
3. **Given** the tasks stage, **When** the task list is written, **Then** each implementation task is preceded by a task that writes a failing test for the seam that task implements.
4. **Given** seams that the feature description leaves ambiguous, **When** the clarify stage runs, **Then** it asks the user about those seams; when the seams are clear, it asks nothing about them.
5. **Given** a written plan and task list, **When** the analyze stage runs, **Then** it reports a finding for any implementation task with no mapped seam, or with no test task before it.

---

### User Story 3 - Review enforces the discipline (Priority: P2)

The reviewing role checks the run's diff against the same written rules the implementing role followed, so a run that skipped a test, duplicated an existing helper, or ignored the design rules does not pass review unnoticed.

**Why this priority**: Enforcement closes the loop, but the discipline already has value from stories 1 and 2 before review is tightened.

**Independent Test**: Hand the reviewing role a diff that adds behaviour with no test and a function duplicating an existing helper; it returns both as findings, with the duplication blocking.

**Acceptance Scenarios**:

1. **Given** a diff that adds behaviour with no test asserting it, **When** review runs, **Then** a finding cites the engineering rules and names the untested behaviour.
2. **Given** a diff with new code that duplicates an existing function in the repository, **When** review runs, **Then** a blocking finding names the existing function that should have been reused or extended.
3. **Given** a diff that follows the rules, **When** review runs, **Then** no engineering-rule finding is raised on style preference alone.

---

### User Story 4 - One shared set of rules, carried to every harness (Priority: P2)

The rules exist once, in a single harness-neutral reference. Every role that writes, plans or reviews code points at that one file, and every harness's installed copy of the factory carries the same rules.

**Why this priority**: Prevents the rules drifting between roles and harnesses, which would make the discipline unenforceable. Required by the repository's constitution.

**Independent Test**: Grep the roles for engineering rules: the rules appear in one reference file only, each relevant role references it, and the rendered output for every harness contains that reference and matches its source.

**Acceptance Scenarios**:

1. **Given** the rules reference, **When** a role needs the rules, **Then** the role points at the shared reference instead of restating the rules inline.
2. **Given** a change to the rules, **When** the change is made, **Then** the design document is updated first, then the source roles and reference, then the generated per-harness output is re-rendered and committed with the source change.
3. **Given** the rendered output, **When** the repository's test command runs, **Then** no difference is reported between the generated output and its source.
4. **Given** a repository whose own constitution or documented conventions contradict a rule, **When** a run works in that repository, **Then** the repository's documented rule wins and the run records which rule was overridden.

---

### Edge Cases

- A change that is documentation or configuration only: exempt from test-first, with the reason stated in the plan; the exemption is never implicit.
- A repository with no test runner: a setup task comes first, so the first behaviour task has somewhere to put its failing test.
- A behaviour whose test cannot be made to fail first (for example, behaviour already covered by an existing passing test): the role records why and states which existing test covers it, rather than silently skipping the red step.
- A seam the plan did not list but a task clearly needs: the implementing role does not invent it; the gap is a finding for analyze and a question for clarify.
- An existing function that is close but not an exact fit: extending it is preferred over a near-duplicate; a genuinely different concern may be new code, with the difference stated.
- A language or repository whose idiom is not functional (for example, a framework demanding inheritance): the functional preferences yield to the language's and repository's idiom.
- A rule the repository's constitution overrides: the override is honoured and named; the factory's own rules are not edited per-run.

## Requirements *(mandatory)*

### Functional Requirements

**Shared rules**

- **FR-001**: The factory MUST hold its engineering rules in one shared, harness-neutral reference file; no role restates them inline.
- **FR-002**: The shared rules MUST be self-contained, with no dependency on any skill outside the factory.
- **FR-003**: The shared rules MUST cover: test-first (red-green-refactor), clean code, SOLID design, preferred functional style, and reuse-before-writing.
- **FR-004**: The code-writing, planning and reviewing roles MUST each reference the shared rules file.
- **FR-005**: The rules MUST apply to every run by default; a repository's own constitution MAY override a specific rule, and the run MUST record which rule was overridden and why.
- **FR-006**: The rules MUST state that the repository's documented conventions win over the factory's stylistic preferences when the two conflict.

**Test-first in implementation**

- **FR-007**: The implementing role MUST, for each task that changes behaviour, write or extend a test, run it, and observe it fail before writing implementation code.
- **FR-008**: The implementing role MUST then write the smallest code that makes the test pass, refactor only while the tests are green, and re-run the tests after refactoring, all inside the same task.
- **FR-009**: The implementing role MUST record proof of the red step in the task's commit body as `Red: <test name> failed as expected`.
- **FR-010**: Each task MUST be committed as one commit containing its test and implementation changes; separate red commits MUST NOT be created, so history stays bisectable.
- **FR-011**: The implementing role MUST NOT invent test seams: it uses the seams the plan lists.
- **FR-012**: A task exempt from test-first (documentation or configuration only) MUST be exempt only where the plan states the exemption and its reason; skipping the test-first steps without a stated reason MUST NOT happen.
- **FR-013**: The fixing role MUST follow the same rules as the implementing role when its fix changes behaviour.

**Reuse**

- **FR-014**: Before writing a new function or method, the implementing and fixing roles MUST search the repository for an existing one and reuse or extend it when one fits.
- **FR-015**: The reviewing role MUST flag new code that duplicates an existing helper, and MUST treat real duplication as blocking.

**Planning for test-first**

- **FR-016**: The plan MUST contain a "Test seams" section naming the public seams the feature will put under test.
- **FR-017**: The plan MUST state, for any part of the change exempt from test-first, which part and why.
- **FR-018**: The plan MUST make setting up a test runner the first task when the repository has none.
- **FR-019**: The task list MUST place a failing-test task before each implementation task, naming the seam it targets.
- **FR-020**: The analyze stage MUST report a finding when an implementation task has no mapped seam, or has no test task before it.
- **FR-021**: The clarify stage MUST ask the user about test seams only when the seams are ambiguous.

**Carrying the change through the repository**

- **FR-022**: The design document MUST be updated before the roles and reference, in the same change.
- **FR-023**: The generated per-harness output MUST be re-rendered for every harness and committed with the source change, with no hand edits to generated files.
- **FR-024**: Role prompts MUST stay short, imperative and unambiguous, and the shared reference MUST use one term per concept throughout.

### Key Entities

- **Engineering rules reference**: the single shared statement of the discipline (test-first, clean code, SOLID, functional preference, reuse) that roles point at.
- **Test seam**: a public entry point of the change that is put under test, agreed at plan time and named by the tasks that test and implement it.
- **Red proof**: the recorded evidence, in a task's commit body, that the task's test was seen failing before the implementation existed.
- **Test-first exemption**: a documentation- or configuration-only part of a change, declared in the plan with its reason.
- **Code-writing role**: a role that changes code in a run (implementing and fixing); bound by the rules directly.
- **Planning role**: the role producing the plan, task list and analyze report; makes the discipline plannable and checkable.
- **Reviewing role**: the role checking the diff against documented rules; makes the discipline enforceable.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In a run on a repository with a test runner, 100% of behaviour-changing tasks have a commit body recording the test that failed as expected.
- **SC-002**: In a generated task list, 100% of implementation tasks are preceded by a test task naming a seam listed in the plan.
- **SC-003**: Every plan produced after this change contains a test-seams section, and every part of a change not covered by a seam has a stated exemption reason.
- **SC-004**: The engineering rules appear in exactly one source file; each of the code-writing, planning and reviewing roles reaches them by reference, with zero inline restatements.
- **SC-005**: After the change, the repository's build and test commands pass, with the generated output showing no difference from its source for every harness.
- **SC-006**: A diff that adds untested behaviour or duplicates an existing helper produces at least one review finding naming it, in a trial review.
- **SC-007**: A user reading a finished run can tell, from the plan and the commits alone and without reading the code, which seams were tested and which steps were exempt.

## Assumptions

- The shared rules live at `core/skills/factory/references/engineering.md` and are reached through the roles' existing reference mechanism, as settled in the brief.
- Scope of roles: the implementing and fixing roles follow the rules; the spec-building role plans for them (plan's test-seams section, test task before each implementation task, analyze's mapping check, clarify's seam questions); the code-standards reviewing role enforces them. Other reviewers are unchanged.
- The external `tdd` skill is deliberately not used; the factory owns self-contained rules because its agents are stateless and cannot confirm seams with the user mid-loop.
- Functional style is a preference, not a mandate: pure functions, immutable data, side effects at the edges, composition over inheritance, within the language's idiom.
- Red proof is a line in the existing task commit body; no new commit type, state field or artefact is introduced.
- This change edits instructions only (design document, source roles, the new reference, and the regenerated per-harness output). No orchestrator flow stage is added or removed.
- Verification of this feature is by inspection of the changed instruction files plus the repository's existing build and test commands; the end-to-end behaviour is observed on the next real run, per the design document's validation plan.
- The repository's constitution continues to apply unchanged; rule overrides are expressed in the consuming repository's own constitution, never by editing the factory's rules per-run.
