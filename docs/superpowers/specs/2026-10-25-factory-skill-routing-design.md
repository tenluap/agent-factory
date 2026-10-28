# Factory skill routing

**Date:** 25 October 2026  
**Status:** Proposed design for review. Live workflow instructions have not been changed for this proposal.

## Purpose

Use the right skill at the right point in a factory run: brainstorming to turn an idea into an agreed direction, grilling to settle a feature, ponytail and TDD to implement or fix code, and impeccable to audit and critique UI changes. Preserve the existing engineering rules, stateless roles, saved answers, worktree isolation, independent verification and publication approval.

## Approaches considered

| Approach | Benefit | Cost |
|---|---|---|
| Route by intent and stage — recommended | Ideas receive exploration; concrete features reach implementation without a redundant interview. Existing roles and stages remain useful. | Requires an explicit idea path and skill-specific integration rules. |
| Always brainstorm, then grill | One intake sequence for all requests. | Repeats exploration for already specified features and increases user waits. |
| Add skills as optional suggestions only | Smallest instruction change. | Does not ensure implementation roles actually load ponytail/TDD or that UI review follows the requested method. |

The proposed default is intent-based routing. An unclear request gets one intent question before choosing a path; the user can explicitly ask for exploration or feature delivery. Do not treat a skill's installation alone as evidence that it was used.

## Routing contract

| Trigger | Skill | Owner | Completion condition |
|---|---|---|---|
| An exploratory idea without a settled solution | `brainstorming` | Orchestrator | Alternatives and tradeoffs are explored; the user confirms a direction and whether to proceed to feature delivery. |
| A concrete new feature, feature change, or idea now ready to build | `grilling` | Orchestrator | Behaviour, scope, constraints, acceptance criteria and planning mode are settled and confirmed. |
| Implementation or repair of code | `ponytail` and `tdd` | Code-build and fixer | The accepted tasks/fixes are implemented with appropriate behavioural tests, minimal changes, required commit evidence, and passing verification. |
| A UI-related change enters review | `impeccable` audit and critique | UI reviewer | Relevant UI is evaluated; evidenced findings and evaluation limitations are returned without edits. |
| A user-facing flow changes | Existing UX lens | UX reviewer | Journeys, states, copy, accessibility and recovery are checked against the spec. It remains a complementary review, not a second identical impeccable pass. |

The idea path is `brainstorm → grill → worktree → existing spec chain`. The feature path starts at `grill`. A user who wants only idea exploration can stop after the direction is recorded; brainstorming does not authorise implementation or publication. Both intake paths reuse settled answers instead of repeating the interview.

Use the existing pending-state storage before a worktree exists. Add `brainstorm` to the stage vocabulary and resume handling; preserve existing stages and saved runs. No new agent role, harness verb, model tier or service is needed. A short shared skill-integration reference is justified because implementation and fixing need the same precedence and skill-loading rules.

## Skill resolution and dependencies

- Use the active adapter's existing `RESOLVE` operation. Keep local machine paths out of the portable core.
- Resolve brainstorming only on the idea path. Resolve grilling for feature intake.
- Resolve ponytail and TDD before committing to a code-delivery run, and pass their absolute instruction paths to each fresh code-build/fixer invocation. On resume, resolve missing names and re-resolve paths when the harness changes.
- Resolve impeccable only when UI review is relevant. Keep the existing install offer and disclosed skip when the user declines installation.
- A required missing skill produces actionable setup guidance and pauses the affected work; never silently claim that the skill was applied. Do not install arbitrary skills or execute a fetched installer without the user's existing authorisation.
- Read skill-relative references from that skill's own directory. For example, TDD's `tests.md` and `mocking.md` do not resolve relative to the factory directory or consuming repository.
- Record selected logical skill names and resolved paths in the existing state skill map. Use the existing ledger/history for stage and role activity; avoid adding a separate telemetry system.

## Integrating skills with factory contracts

### Brainstorming and grilling

The orchestrator handles all user interaction. Preserve the skills' purpose while using the factory's question protocol, persistence and resume rules. Brainstorming explores alternatives and gets a direction confirmed; grilling then examines the chosen feature's unresolved decisions. Existing answers are inputs, not prompts to ask the same questions again.

Brainstorming's default document location, commit instructions and planner handoff are adapted to the factory: save intake artifacts in pending storage, move them into the feature worktree when created, let the factory own commits, and continue through SpecKit planning. Do not introduce a second planning chain or a write to the invoking checkout during intake. Offer a visual companion only for actual visual exploration and only with its required consent.

### Ponytail

Apply ponytail's reuse-first, standard-library-first and minimum-sufficient-change guidance within the approved specification. A role's read of the resolved file is the skill's activation, at its full level (its default) for the whole role session; `lite`'s deferral and `ultra`'s request pushback are interactive-turn choices. Its output preferences do not replace the required role envelope. Its simplification advice does not remove requirements, security, accessibility, planned tests, repository tooling or engineering-rule evidence. Dependency choices and design judgements remain proportionate.

### TDD

Use behavioural tests at public seams, independent expected values, useful boundary mocking, and one test/implementation slice at a time. Keep the factory's required `Red:` evidence, one completed task commit, exemptions and missing-runner failures.

TDD requires user-confirmed seams before writing tests. The spec-builder therefore relays the proposed plan's public test seams through the orchestrator before implementation. Reuse an existing confirmation only when the same seams and scope were already explicitly agreed. Persist confirmation with the plan and saved answer; changed seams need a new decision. Code-build and fixer do not ask the user directly or invent seams.

Add an optional `requires_user: true` question field for confirmations that must remain manual, including test seams. Fast-mode automation skips these questions as well as existing decision-changing remediation questions. Legacy questions without the field preserve their current behaviour. Initial brainstorming and grilling remain interactive.

The local TDD skill defers refactoring to review, while the factory's engineering rules permit small behaviour-preserving refactoring while green. Keep the engineering rules authoritative for this conflict and state the adaptation explicitly. Do not weaken the existing `ENG-1` through `ENG-31` rules by adding a skill pointer.

### Impeccable UI evaluation

The UI reviewer already follows impeccable audit and critique. Make this route explicit and preserve its read-only role, JSON findings and current review/fix limits. Run setup once in the reviewer context and resolve the applicable web/native evaluation references.

Use rendered evidence when available and evaluate relevant viewports, states, themes and interactions. When only source or existing captures are available, disclose the evidence and its limits; do not describe a static review as an observed interaction test. UI detection includes markup/styles, design tokens/themes, UI assets and user-visible copy, rather than relying only on a short filename-extension list. Backend-only changes skip the UI passes.

Impeccable's refinement and editing commands belong to a separately authorised implementation/fix task, not the read-only review role. Confirmed fixes return through the existing fixer and verification/review path.

## Files to align after design approval

1. Update `DESIGN.md` first, recording routing, precedence, protected confirmations and validation.
2. Add a compact shared integration reference and link it from the orchestrator and code-writing roles.
3. Update orchestrator intake, conditional resolution, role inputs and UI detection.
4. Update state/protocol references for brainstorming resume and `requires_user`; keep old states readable.
5. Update spec-builder, code-build, fixer and UI-reviewer instructions where the routing affects their work.
6. Revise ADR 0001's rejection of external TDD: the skill now contributes testing technique under explicit factory orchestration and precedence.
7. Align README requirements and the product brief so readers can distinguish prerequisites and conditional skills.
8. Render every harness canonically. Do not hand-edit generated distributions or change adapter-specific model settings as part of this feature.

## Acceptance scenarios

- An exploratory idea enters brainstorming; a concrete feature skips that extra interview and enters grilling.
- Brainstorming captures alternatives and a confirmed direction without writing to the invoking checkout; the user can stop before feature delivery.
- Grilling reuses settled brainstorming decisions and asks only unresolved feature questions.
- A paused idea resumes at brainstorming with saved answers; existing feature runs still resume at their recorded stage.
- Every fresh code-build/fixer receives and reads ponytail/TDD instructions. Missing required skills stop affected work with setup guidance.
- Behavioural implementation uses vertical test/implementation slices and the existing `Red:` commit evidence, including after an implementation handover.
- A test-seam confirmation reaches the user even with fast mode enabled; confirmed unchanged seams are not asked again on resume.
- A missing seam or unavailable required runner still fails through the existing policy.
- A UI change runs impeccable audit and critique plus the complementary UX review. Copy/theme/token-only changes are detected where relevant; backend-only changes skip them.
- UI reviewers remain read-only and distinguish rendered evidence from static inspection; skipped or limited evaluation appears at approval.
- A harness change re-resolves selected skills, and all rendered distributions carry the same portable skill and integration reference.

Static link/schema/render checks validate packaging and compatibility. Real agent-driven runs are needed to establish routing, protected-question and role-following behaviour; report those separately.
