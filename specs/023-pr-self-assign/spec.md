# Feature Specification: Assign factory PRs to the signed-in GitHub account

**Feature Branch**: `023-pr-self-assign`

**Created**: 2026-11-04

**Status**: Draft

**Input**: User description: "Assign each newly opened factory PR to the authenticated GitHub CLI account that opens it (plan: docs/superpowers/plans/2026-11-03-factory-pr-self-assignment-plan.md). Add `--assignee @me` to the PR creation step, keeping the human approval before push/PR. When creation or assignment reports an error, look up the branch's existing PR before retrying; if a PR exists but assignment failed, preserve its URL and report the assignment problem separately. Verify with a disposable GitHub repository: actual assignee, and resuming interrupted publication does not create a duplicate PR. Acceptance: new PR lists the authenticated gh account as assignee; a failed assignment is visible; a retry reuses an existing PR; approval flow never asks for a GitHub username." (settled decisions Q1-Q7 in `factory/brief.md`)

## Clarifications

### Session 2026-11-04 (grill, settled under cruise)

- Q1: How is the PR assigned? → A: The single PR-creation request in the PR step asks GitHub to assign the PR to the signed-in account (`--assignee @me`); there is no separate assignment request. The approver gate before push/PR is unchanged, and no GitHub username is ever asked.
- Q2: How is a duplicate PR prevented? → A: Publication is idempotent. The branch's PR is looked up before creation and again after any creation error; an existing PR is reused and its URL recorded, never recreated.
- Q3: What happens when assignment fails? → A: Non-blocking. The URL is kept, the run continues, and the assignment problem is reported separately in the final notice. No new state field and no new issue kind.
- Q4: What does resume of the `pr` stage do? → A: It follows the same lookup-then-create path.
- Q5: How is it verified? → A: An automated text-contract test of the factory skill's PR step and resume rule; the disposable-repository live check is a manual runbook in `quickstart.md`, run by the user, never by agents.
- Q6: Which files change? → A: Core only (factory skill PR step, state reference's `pr` resume rule), re-rendered for all five harnesses. No ADR, no new glossary term.
- Q7: Chain? → A: Lite.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - New PR is assigned to the person who opened it (Priority: P1)

A user approves a finished factory run. The run pushes the branch and opens the PR, and the PR shows the user's own GitHub account as its assignee, so it appears in their "assigned to me" view without any manual step. The user is never asked for a GitHub username.

**Why this priority**: The feature's whole value: every factory PR has an owner from the moment it opens.

**Independent Test**: Approve a run against a repository where the signed-in account can assign itself; confirm the opened PR lists that account as its only assignee and that no question about a username was shown at any point.

**Acceptance Scenarios**:

1. **Given** a run at the approver gate, **When** the user picks Approve, **Then** the branch is pushed and the PR is opened with the GitHub CLI's signed-in account as its assignee.
2. **Given** a run at the approver gate, **When** the user has not picked Approve, **Then** nothing is pushed and no PR exists (unchanged behaviour).
3. **Given** any run, in any mode (including cruise), **When** it reaches and completes the PR step, **Then** no question asks the user for a GitHub username or account.

---

### User Story 2 - Retry or resume never opens a duplicate PR (Priority: P1)

Publication can be interrupted: the PR-creation request may report an error after GitHub has already created the PR, or the session may die between creating the PR and recording its URL. When the run retries or the user resumes it, the factory finds the branch's existing PR and reuses it rather than opening a second one.

**Why this priority**: A duplicate PR splits review, confuses CI and must be cleaned up by hand; idempotent publication is what makes the assignment change safe to retry.

**Independent Test**: In a disposable repository, open a PR for a run's branch, then resume the run at its `pr` stage; confirm the run records the existing PR's URL and the repository still has exactly one PR for the branch.

**Acceptance Scenarios**:

1. **Given** the PR step is about to create a PR, **When** an open PR for the branch already exists, **Then** no new PR is created and the existing PR's URL is recorded as the run's PR.
2. **Given** the PR-creation request reports an error, **When** the follow-up lookup finds an open PR for the branch, **Then** that PR is reused and its URL recorded; no second creation is attempted.
3. **Given** the PR-creation request reports an error, **When** the follow-up lookup finds no PR, **Then** creation is retried once; if that also fails and a final lookup still finds no PR, the run halts with the error as its halt reason and nothing is recorded as published.
4. **Given** a run interrupted during the `pr` stage, **When** the user resumes it, **Then** the resume follows the same lookup-then-create path and the repository ends with exactly one PR for the branch.

---

### User Story 3 - A failed assignment is visible but does not block publication (Priority: P2)

Sometimes the PR opens but the assignment does not take (for example, the account lacks permission to assign, or the reused PR was created earlier without an assignee). The run still records the PR and finishes, and the final notice tells the user, separately from the PR link, that the PR is not assigned to them.

**Why this priority**: Assignment is a convenience; losing a published PR or halting over it would cost more than the assignment saves, but a silent failure would defeat the feature.

**Independent Test**: Reuse a PR that has no assignees (opened by hand before resuming the run); confirm the run records its URL, finishes, and the final notice names the assignment problem on its own line.

**Acceptance Scenarios**:

1. **Given** a PR exists for the branch, **When** the signed-in account is not among its assignees, **Then** the run keeps the PR URL, continues through retro, archive and final push, and the final notice reports the assignment problem separately from the PR URL.
2. **Given** a PR exists for the branch, **When** the signed-in account is among its assignees, **Then** the final notice carries no assignment problem.
3. **Given** the assignment problem is reported, **When** the run's state is inspected, **Then** no new state field or issue kind was introduced to carry it.

---

### Edge Cases

- **PR created but the request reported an error** (network drop after GitHub accepted it): the after-error lookup finds it and the run reuses it (US2 scenario 2).
- **Lookup itself fails** (GitHub unreachable, CLI not signed in): the run never treats an unanswered lookup as "no PR". It does not create a PR it cannot first rule out as a duplicate; it halts with the lookup error as the halt reason, and resume repeats lookup-then-create.
- **Only a closed or merged PR exists for the branch**: it is not reused; the run creates a new PR (as `gh pr create` itself would allow) with the signed-in account as assignee.
- **Signed-in account cannot be determined** after the PR exists: treated as an assignment problem (reported, non-blocking), never as a reason to ask the user for a username.
- **PR reused from an earlier attempt or opened by hand without an assignee**: reported as an assignment problem (US3); the run does not issue a separate assignment request.
- **Interrupted after the PR URL is recorded** (`pr-open` set): unchanged; the existing manual recovery (`factory drop`, then `git push`) applies.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The PR step MUST open the PR with a single creation request that asks GitHub to assign it to the GitHub CLI's signed-in account (`--assignee @me`). It MUST NOT issue a separate assignment request.
- **FR-002**: The approver gate MUST remain the only route to the PR step: nothing is pushed and no PR is created before the user's own Approve, in every mode including cruise.
- **FR-003**: No step of the approval or publication flow MUST ask the user for a GitHub username or account; the account is always the CLI's signed-in identity.
- **FR-004**: Before the creation request, the PR step MUST look up the branch's PR (URL and assignees). An open PR found there MUST be reused: its URL is recorded as the run's PR through the existing `pr-open` status write, and no creation request is made.
- **FR-005**: After any creation request that reports an error, the PR step MUST look up the branch's PR again before any retry. A found open PR MUST be reused as in FR-004.
- **FR-006**: When the after-error lookup finds no PR, the PR step MUST retry creation at most once (preceded by that lookup). When the retry also fails and a final lookup finds no PR, the run MUST halt through the existing halt policy with the creation error as the halt reason, recording no PR URL.
- **FR-007**: When a lookup itself fails (it cannot say whether a PR exists), the PR step MUST NOT create a PR; it MUST halt through the existing halt policy with the lookup error as the halt reason.
- **FR-008**: After the run's PR is known (created or reused), the run MUST check whether the signed-in account is among its assignees. When it is not, or when the check cannot be completed, the run MUST keep the PR URL, continue the PR step unchanged (retro, archive, final push), and report the assignment problem in the final notice as its own item, separate from the PR URL.
- **FR-009**: Assignment problems MUST NOT add a state field, an issue kind or a history event; the existing state schema and vocabularies stay unchanged.
- **FR-010**: Resuming a run whose recorded stage is `pr` MUST follow the same lookup-then-create path as FR-004 to FR-008, so an interrupted publication never creates a duplicate PR.
- **FR-011**: The behaviour MUST be recorded in the design document's PR section (constitution principle I) and in the harness-neutral core (factory skill PR step; state reference's `pr` resume rule), using only neutral verbs, and MUST render cleanly for all five harnesses.
- **FR-012**: An automated test MUST fail when the factory skill's PR step loses the self-assignment option, the before-creation lookup, the after-error lookup, or the separate assignment report, or when the state reference's `pr` resume rule stops pointing to the same lookup-then-create path.
- **FR-013**: `quickstart.md` MUST carry a manual runbook for the live check against a disposable GitHub repository: confirm the actual assignee of a newly opened PR, confirm a resumed `pr` stage reuses an existing PR (exactly one PR for the branch afterwards), confirm an unassigned reused PR is reported, and delete the disposable repository afterwards. Agents MUST NOT run it or create GitHub repositories.

### Key Entities

- **Branch PR**: the pull request whose head is the run's branch. Attributes the run relies on: URL, open/closed state, assignees. At most one open Branch PR exists per run.
- **Signed-in account**: the GitHub account the GitHub CLI is authenticated as when the PR step runs; the assignee target. Never supplied by the user.
- **Assignment problem**: a note that the Branch PR is not assigned to the signed-in account (or that this could not be checked). Lives only in the final notice; never persisted as a new state field or issue kind.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In the manual runbook, 100% of PRs newly opened by an approved run list the signed-in account as assignee.
- **SC-002**: In the manual runbook, resuming an interrupted `pr` stage leaves exactly 1 PR for the branch, every time.
- **SC-003**: When the run's PR is not assigned to the signed-in account, the final notice states so in 100% of runs, as an item separate from the PR link, and the run still finishes with its PR recorded.
- **SC-004**: Zero questions about a GitHub username or account appear in any run, in any mode.
- **SC-005**: The automated test suite fails whenever any of the four PR-step behaviours or the resume rule in FR-012 is removed, and passes on the changed core; every harness renders without error.

## Assumptions

- The GitHub CLI is installed and signed in wherever the PR step runs today; this feature adds no new prerequisite. `@me` resolves to that signed-in account.
- "Core only" in the settled decisions means no adapter changes. The design document's PR section is updated as well, because constitution principle I requires every behaviour change to be recorded there first; no ADR and no new glossary term are added.
- One in-turn creation retry mirrors the step's existing "retry once" rule for the final push; repeated failures go to the existing halt policy, from which resume repeats lookup-then-create.
- Only an open PR is reused. A closed or merged PR for the branch is rare for factory branches and is not resurrected; a new PR is opened instead.
- Determining the signed-in account's login, for the assignee check, uses the already-signed-in GitHub CLI; nothing reads or stores credentials.
- The automated verification is a text-contract test in the existing `tools` test suite, matching how other core instruction changes are tested; live GitHub behaviour is verified only through the manual runbook because creating repositories and PRs is outward-facing.
- The `pr` skill keeps writing the PR body; this feature changes only the creation, lookup and reporting around it.
