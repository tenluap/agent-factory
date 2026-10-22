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

- `status`: `done` (stage finished), `needs_input` (questions below; the agent stops, and a fresh one continues the stage once they are answered), `partial` (code-build only: context running low, progress committed), `failed` (`error` says why).
- `questions` (with `needs_input`): the agent's **whole** queue for this stage, never one at a time: `[ { "id": "Q1", "title": "...", "text": "...", "options": ["A: ...", "B: ..."], "recommended": "B, because ..." } ]`. Ids are unique within a stage: a later round continues the numbering.
- `analyze` (analyze stage only): `{ "report": "factory/analyze-<n>.md", "critical": 0, "high": 2, "medium": 1, "low": 0 }`.
- `pending_clarify` (remediate stage only): findings that need a user decision, as clarify questions in the `questions` item shape. The orchestrator stores them in `state.analyze.pending_clarify` and hands them to the next `clarify`.

Reviewers and the judge return their report or verdict (findings.md) as their final fenced block instead.

## Relay

How the orchestrator carries an agent's questions to the user and back:

1. Append the batch to `state.relay.rounds` as `{ "questions": [...], "answers": {} }` (creating `relay` for this stage if it is null), append a `timeline` entry for it (below), set `status: waiting_user`, `NOTIFY`.
2. Ask in grilling-round format, all questions in one message:

   ```
   ❓ **Q1** - **<title>**: <text and options>

   ➡️ <recommended>
   ```

3. As the user answers, write each into the last round's `answers` as `{ "answer": "<text>", "at": "<now>" }` (add `"auto": true` where fast mode chose it). "accept" means every recommended answer.
   - **Fast mode** (`mode.fast` true): steps 1–2 collapse — take every question's `recommended` as the answer, write it into the round's `answers` as `{ "answer": "<recommended>", "at": "<now>", "auto": true }`, `NOTIFY` once ("auto-accepted N questions in <stage>"), and continue at step 4. Never auto-answered: anything stored in `state.analyze.pending_clarify` — those questions relay to the user normally.
4. All answered: set `status: running` and `SPAWN` a fresh agent of the same role for the same stage, with the usual inputs and the `state.json` path. It reads every round in `state.relay` and asks only what is still open.
5. The new agent either asks another round (normal for grilling and clarify) or returns `done`. `relay` is cleared when the stage completes (state.md, "Checkpoint").

## Timeline

Every wait on the user is one `timeline` entry (state.md, "Schema"). Append `{ "at": "<now>", "kind": ..., "stage": ..., "summary": "<one line>" }` when the message is shown — `kind` is `questions` for a relay round, `notice` for any other `NOTIFY` that ends your turn, `approver` for the gate, `halt`. When the user answers, set that entry's `answered_at` and `latency_ms` in place (for a round with several answers, latency runs from the round's `at` to the last answer). Never clear or rewrite earlier entries; a wait the run never came back from keeps its nulls.
