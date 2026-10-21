# Agent protocol

## Envelope

Every factory agent ends every turn with exactly one fenced `json` block, the **envelope**, as the last thing in its message:

```json
{
  "status": "done",
  "stage": "plan",
  "summary": "one or two sentences on what changed",
  "files": ["specs/016-x/plan.md"],
  "questions": [],
  "analyze": null,
  "error": null
}
```

- `status`: `done` (stage finished), `needs_input` (questions below; the agent waits), `partial` (code-build only: context running low, progress committed), `failed` (`error` says why).
- `questions` (with `needs_input`): the agent's **whole** queue for this stage, never one at a time: `[ { "id": "Q1", "title": "...", "text": "...", "options": ["A: ...", "B: ..."], "recommended": "B, because ..." } ]`.
- `analyze` (analyze stage only): `{ "report": "factory/analyze-<n>.md", "critical": 0, "high": 2, "medium": 1, "low": 0 }`.
- `pending_clarify` (remediate stage only): findings that need a user decision, as clarify questions in the `questions` item shape. The orchestrator stores them in `state.analyze.pending_clarify` and hands them to the next `clarify`.

Reviewers and the judge return their report or verdict (findings.md) as their final fenced block instead.

## Relay

How the orchestrator carries an agent's questions to the user and back:

1. Save the batch to `state.relay`, set `status: waiting_user`, notify.
2. Ask in grilling-round format, all questions in one message:

   ```
   ❓ **Q1** - **<title>**: <text and options>

   ➡️ <recommended>
   ```

3. As the user answers, write each answer into `state.relay.answers`. "accept" means every recommended answer.
4. All answered: `SendMessage` the agent `{ "answers": { "Q1": "...", ... } }`, set `status: running`.
5. The agent either continues the stage (more `needs_input` rounds are normal, e.g. grilling) or returns `done`.
