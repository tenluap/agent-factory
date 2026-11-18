# Glossary

| Term | Meaning |
|---|---|
| **Factory run** | One pass over one feature, from grilling to an open PR, on its own branch and worktree. |
| **Orchestrator** | The session running `/factory`. Owns state, spawns every role, only one that talks to you. |
| **Role** | A prompt an agent is spawned from, named by its job. |
| **Stage** | One named step a role does in one spawn: specify, clarify, plan, tasks, analyze, implement, review, fix... |
| **Harness** | The agent product the run executes in. |
| **Adapter** | Per-harness translation of neutral verbs and install paths. |
| **Relay** | The orchestrator carrying an agent's question batch to you and the answers back to a fresh agent. |
| **Envelope** | The single fenced JSON block a role ends its turn with. |
| **Finding** | One reviewable defect with a severity and a rule it rests on. |
| **Verdict** | The judge's merged, verified ruling over a review round. |
| **Fast mode** | Eligible relay questions auto-accept the recommended answer, logged for your veto. |
| **Cruise mode** | Unattended run to the approver. Never publishes without your Approve. |
| **Worktree** | The sibling git checkout holding one feature's branch. |
| **Checkpoint** | A commit of the spec directory plus role-declared files, written by the CLI. |
| **Baseline** | The first analyze counts. Later targets are relative to it. |
| **Rendered distribution** | Per-harness skill and agent files built from core and an adapter. |

The full domain glossary is `CONTEXT.md` at the repo root.
