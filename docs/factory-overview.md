# Software Factory overview

The factory turns a feature brief into a reviewed pull request. The main agent session runs the workflow, specialists handle scoped work, and the Python CLI records decisions and checks that the run has the evidence it needs to advance.

## From request to pull request

```mermaid
flowchart TD
    Request["Feature request"] --> Preflight["Preflight: repo, harness, skills, models, and build and test commands"]
    Preflight --> Intake{"Open-ended idea?"}
    Intake -- Yes --> Brainstorm["Brainstorm alternatives"]
    Intake -- No --> Grill["Confirm requirements with you"]
    Brainstorm --> Grill
    Grill --> Worktree["Save the brief and create a feature branch in a sibling worktree"]
    Worktree --> Spec["Spec chain: define, plan, create tasks, and analyze"]
    Spec -- "Implementation gate passes" --> Implement["Implement and commit passing task units"]
    Implement --> Verify{"Main session runs build and tests"}
    Verify -- "First failure" --> Repair["One implementation repair attempt"]
    Repair --> Verify
    Verify -- "Still failing" --> Halt["Pause for your direction"]
    Verify -- "Passing verification recorded" --> Review["Independent specialist review and judge verdict"]
    Review --> Approval{"Your approval decision"}
    Approval -- "Request changes" --> Fixer["Fixer applies your requested changes"]
    Fixer --> Verify
    Approval -- Abort --> Abort["End run and keep the worktree"]
    Approval -- Approve --> PublishGate{"Approval recorded and any required design evidence current?"}
    PublishGate -- No --> Halt
    PublishGate -- Yes --> Publish["Push branch and open PR"]
    Publish --> Retro["Run a retrospective and archive run evidence"]
    Retro --> Cleanup["Push cleanup and report the PR"]
```

The main session handles questions from specialists. Fast mode can accept eligible recommendations and records them for review. Initial requirements, protected decisions, and final approval stay with you. Publication on a design run requires current evidence or an explicit exception for the affected scope. A run can pause before a selected stage and resume from the worktree, saved answers, and completed commits. [Workflow](../core/skills/factory/SKILL.md) · [Question relay](../core/skills/factory/references/protocol.md) · [Resume behavior](../core/skills/factory/references/state.md#resume)

## Spec chain and Analyze repair loops

```mermaid
flowchart TD
    Brief["Confirmed brief"] --> Specify["Specify: write spec.md"]
    Specify --> Mode{"Lite or full?"}
    Mode -- "Lite, the default" --> Plan["Plan: record approach, test scope, and repo rule overrides"]
    Mode -- Full --> Clarify["Clarify gaps"]
    Clarify --> GrillDocs["Walk through the written spec with you"]
    GrillDocs --> Plan
    Plan --> Tasks["Tasks: write ordered implementation and verification units"]
    Tasks --> Analyze{"Analyze: compare requirements, plan, and tasks"}
    Analyze -- "High or critical in lite" --> Escalate["Switch to full and carry the report forward"]
    Escalate --> Clarify
    Analyze -- "High or critical in full" --> Repair1["Loop 1: repair the existing documents"]
    Repair1 --> Check1{"Recheck 1: high or critical remains?"}
    Check1 -- Yes --> Repair2["Loop 2: repair the existing documents again"]
    Repair2 --> Check2{"Recheck 2: high or critical remains?"}
    Check2 -- Yes --> Decision{"Pause for your decision"}
    Decision -- "Guide another pass" --> Guided["User-directed repair and recheck"]
    Guided --> GuidedCheck{"High or critical remains?"}
    GuidedCheck -- Yes --> Decision
    GuidedCheck -- No --> Minor
    Decision -- "Explicitly proceed" --> Override["Record an implementation gate override"]
    Decision -- Abort --> End["End run and keep the worktree"]
    Analyze -- "No high or critical" --> Minor{"Medium or low findings remain?"}
    Check1 -- No --> Minor
    Check2 -- No --> Minor
    Minor -- Yes --> Targets{"Acceptance targets met against the baseline?"}
    Targets -- "No, repair cycles left (cap 2)" --> Repair1
    Targets -- "No, cap reached" --> Decision
    Targets -- Yes --> Ready["Implementation checkpoint"]
    Override --> Ready
```

The initial Analyze precedes both repair loops and sets the baseline. Implementation waits until CRITICAL and HIGH are zero and the total and LOW counts meet the baseline-relative targets: each must be below half its baseline, and a zero baseline stays zero. Repair runs at most two cycles; after that the run pauses for your decision. When a repair needs a decision, the main session relays the question and returns to clarification before the recheck. The current loop repairs feature documents in place. A constitution change is applied only after you approve its exact draft ([ADR 0014](adr/0014-analyze-acceptance-targets.md)). [Current spec chain](../core/skills/factory/SKILL.md#5-spec) · [Spec builder](../core/roles/spec-builder.md)

## Independent specialist review

```mermaid
flowchart TD
    Start["Recorded build and test pass"] --> Fan["Orchestrator sends the diff to reviewers"]
    Fan --> Security["Security: vulnerabilities and security risks"]
    Fan --> Standards["Code standards: conventions and engineering rules"]
    Fan --> Conformance["Spec conformance: requirements and acceptance criteria"]
    Fan --> UIChange{"Does the diff touch the UI?"}
    UIChange -- Yes --> UX["UX reviewer: journeys, states, copy, and recovery"]
    UIChange -- Yes --> VisualAccess{"Visual review available?"}
    VisualAccess -- Yes --> Visual["UI reviewer: visual audit, critique, and evidence"]
    VisualAccess -- "Install declined" --> Skip["Record and disclose the skipped visual review"]

    Repo["Target repo: agent instructions, constitution, style settings, and ADRs"] --> Standards
    Factory["Factory engineering rules"] --> Standards
    Plan["Plan records which documented repo rule wins each conflict"] --> Standards

    Security --> Judge
    Standards --> Judge
    Conformance --> Judge
    UX --> Judge
    Visual --> Judge
    Judge["Review judge: verify evidence, merge duplicates, and classify findings"] --> Scope{"Fix diff outside expected scope?"}
    Scope -- Yes --> Full["Rerun this round on the full diff"]
    Full --> Fan
    Scope -- No --> Verdict{"Confirmed blockers and automatic repair rounds left?"}
    Verdict -- Yes --> Fixer["Fixer addresses confirmed blockers"]
    Fixer --> Recheck{"Main session reruns build and tests"}
    Recheck -- Pass --> Delta["Review the fix diff against the previous verdict"]
    Delta --> Fan
    Recheck -- "Still failing after repair" --> Halt["Pause for your direction"]
    Verdict -- No --> Approval["Show verdict, advisories, and any unresolved blockers"]
    Skip -. "Disclose at approval" .-> Approval
```

The first round covers the full diff. The judge can expand a later round back to a full review when the fix goes outside its expected scope. The factory allows up to two automatic review fixes. Required design evidence still goes through spec conformance if visual review is skipped. Approval discloses skipped review, static-only evidence, and unresolved findings. [Review workflow](../core/skills/factory/SKILL.md#7-review) · [Reviewer rules](../core/roles/code-standards.md) · [Judge](../core/roles/review-judge.md) · [Repo rule precedence](../core/skills/factory/references/engineering.md#rules)

## What owns decisions and evidence

| Component | Responsibility |
|---|---|
| Main session | Runs preflight, dispatches fresh roles, relays questions, runs independent checks, and opens the PR after approval. |
| Harness adapter | Maps factory operations to the host’s tools, model selection, agent format, and permissions. |
| Specialists | Produce scoped artifacts, implementation commits, review findings, or a judge verdict. |
| State CLI | Records checkpoints, answers, analysis counts, and verification. It requires settled analysis or a recorded override before implementation, passing verification before review, and recorded approval or an explicit override before PR entry. |
| Git worktree and archive | Hold the task commits and evidence used on resume. The run archive retains the audit record after PR creation and preserves deliverable design evidence in the project. |

The CLI validates recorded results. The main session runs the commands that produce them. [Transition checks](../core/skills/factory/bin/factory_cli/checks.py) · [State writer](../core/skills/factory/bin/factory_cli/state.py) · [Publication and archive](../core/skills/factory/SKILL.md#9-pr)

## Known gaps and planned work

The diagrams show the intended flow of the current implementation. Two UI instructions need repair. The orchestrator still refers to the old UI writer name, and the OpenCode reviewer’s delegation policy conflicts with the bundled standalone web critique. Both are documented in the [UI handoff plan](superpowers/plans/2026-11-03-factory-ui-handoffs-plan.md). Their live impact remains unverified.

- [Live end-to-end conformance](superpowers/plans/2026-11-03-factory-live-conformance-plan.md)
- [Bind publication to tested, reviewed, and approved work](superpowers/plans/2026-11-03-factory-publication-evidence-plan.md)
- [Collect feedback after PR creation](superpowers/plans/2026-11-03-factory-post-pr-feedback-plan.md)
- [Assign PRs to the signed-in GitHub account](superpowers/plans/2026-11-03-factory-pr-self-assignment-plan.md)
