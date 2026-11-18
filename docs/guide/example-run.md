# Example run, end to end

!!! note "Illustrative"
    The feature, branch name and question IDs below are made up to show the shape of a run. Exact wording and numbers differ in a real run.

**Request:** `/factory add a --json flag to the export command`

```mermaid
sequenceDiagram
    actor You
    participant O as Orchestrator
    participant CLI as Run-state CLI
    participant SB as spec-builder
    participant CB as code-build
    participant R as Reviewers
    participant J as review-judge
    participant Fx as fixer

    You->>O: /factory add a --json flag to export
    O->>O: Route, preflight (harness, models, skills, stack)
    O->>You: Grill: scope, output shape, errors?
    You->>O: Answers, confirm brief
    O->>CLI: create worktree and state
    CLI-->>O: branch 027-export-json, state.json
    loop specify, plan, tasks, analyze
        O->>SB: run one stage
        SB-->>O: envelope (files, questions)
        O->>You: relay questions (Q1..Qn)
        You->>O: Q1: accept, Q2: B
        O->>CLI: answer, checkpoint
    end
    O->>CLI: analyze-record (gate: counts OK)
    O->>CB: implement tasks.md
    CB-->>O: one commit per task
    O->>O: run build and tests
    O->>CLI: verify (pass)
    par parallel review
        O->>R: security
        O->>R: code standards
        O->>R: spec conformance
    end
    R-->>J: reports
    J-->>O: verdict: fix (1 blocker)
    O->>Fx: fix blocker
    O->>O: rebuild, retest
    O->>R: delta review of the fix
    J-->>O: verdict: pass
    O->>You: Approver screen
    You->>O: Approve
    O->>CLI: checkpoint approved
    O->>O: push, gh pr create
    O->>CLI: drop (archive run)
    O->>You: PR link and totals
```

## What you did

1. Wrote one sentence.
2. Answered the grilling interview and confirmed the brief.
3. Answered a few relay questions (fast mode took the rest).
4. Read the approver screen and chose **Approve**.

## What the factory did on its own

- Created an isolated branch and worktree.
- Wrote spec, plan and tasks, and gated on analyze.
- Committed one change per task, test first.
- Ran build and tests itself, twice.
- Fixed one blocker the judge confirmed, and re-reviewed only the fix.
- Opened the PR, archived the run, queued retro suggestions.

## What you would see if it went wrong

| Situation | What happens |
|---|---|
| Build stays red after one repair | Halt. You choose how to proceed. |
| Analyze still has HIGH findings after two loops | Halt. Guide a pass, proceed with a recorded override, or abort. |
| An agent hits its deadline | It returns `partial`. A fresh agent resumes from disk. |
| Your session dies | `/factory` lists the run. `/factory resume <branch>` continues. |

## After the PR

Check `/factory improve` for suggestions the retro agent wrote from this run's issues. Starting one is always your call.
