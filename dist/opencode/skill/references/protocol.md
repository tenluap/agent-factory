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
- `questions` (with `needs_input`): the **whole frontier** for this round: every open question whose prerequisites are settled. Defer questions whose wording or options depend on unanswered decisions. Use the question shape below. IDs are unique within a stage; later rounds continue the numbering.
- `analyze` (analyze stage only): `{ "report": "factory/analyze-<n>.md", "critical": 0, "high": 2, "medium": 1, "low": 0 }`.
- `pending_clarify` (remediate stage only): findings that need a user decision, as clarify questions in the `questions` item shape. The orchestrator stores them in `state.analyze.pending_clarify` and hands them to the next `clarify`.

Reviewers and the judge return their report or verdict (findings.md) as their final fenced block instead.

## Questions

New questions use this shape; `pending_clarify` uses it too:

```json
{
  "id": "Q7",
  "title": "How should the agent apply changes?",
  "text": "",
  "helper": "Choose one option, or describe your own approach.",
  "options": [
    { "id": "A", "label": "Ask before every change", "description": "Review and approve each edit before it is applied.", "emoji": "🛡️" },
    { "id": "B", "label": "Work in a separate worktree", "description": "Let the agent work independently, then review the result.", "emoji": "🌿" },
    { "id": "C", "label": "Something else", "description": "Describe how you would like the agent to work.", "emoji": "💬" }
  ],
  "recommended": "B",
  "rationale": "Fits your preference to review changes before merging.",
  "requires_user": false
}
```

- `title` is the question; `text` carries any additional context. `helper` states how to answer. Keep descriptions and rationale concise; ground the rationale in known context rather than attributing an unstated preference to the user.
- `requires_user` (optional boolean, default `false` when absent — today's behaviour unchanged): marks a question fast mode must never auto-answer, alongside the existing `pending_clarify` exclusion. An answer to such a question is stored like any other and never carries `"auto": true`. A test-seam confirmation (DESIGN.md, "Protected confirmations") is one example.
- Choice options have unique consecutive letter IDs, labels, short descriptions and contextual emojis. Include a final `💬 Something else` option. `recommended` is a substantive option ID; `rationale` explains it separately so acceptance records only the answer. For open-ended questions use `options: []`, a free-text helper, and proposed answer text in `recommended`.
- **Legacy questions** may omit `title`, `helper`, `options`, or `rationale`; options may be strings such as `"A: ..."`, and `recommended` may combine answer and reason. Preserve stored questions, answers and IDs. Render available fields in the layout below: use `text` as the heading when `title` is absent, omit missing context/descriptions/rationale, and use a neutral answer instruction when `helper` is absent. Recognise a legacy option letter or recommendation match only when unambiguous; otherwise display the original text without a suggested-option marker. Keep a legacy `recommended` verbatim when accepted rather than guessing how to split it. An old question without options stays free text.

### Presentation

Use this chat Markdown for initial grilling and every displayed relay round, on every harness, including a one-question batch. This presentation and the reply rules below override the upstream skill's question format and acceptance aliases. Use contextual option emojis; retain letter IDs and readable labels. Separate question sections with `---`.

```markdown
### 🧭 Question 2 of 4 · Q7

❓ **How should the agent apply changes?**
☝️ Choose one option, or describe your own approach.

**A · 🛡️ Ask before every change**
Review and approve each edit before it is applied.

**B · 🌿 Work in a separate worktree — ✨ AI suggested**
Let the agent work independently, then review the result.

**C · 💬 Something else**
Describe how you would like the agent to work.

> 💡 **Suggested answer**
>
> 🌿 **B · Work in a separate worktree**
>
> 🎯 Fits your preference to review changes before merging.
>
> ✅ Use suggested answer: `Q7: accept`
```

Render nonempty `text` between the heading and helper. For free text, omit options and show the proposed answer in the suggestion block. The shortcut is text to reply with, not a button. For a multi-question round, add one closing hint: `✅ Accept all unanswered suggestions: accept · 💬 Reply by ID: Q7: B or Q7: <your answer>`.

`N of M` is the question's position in the stored current round, not a predicted total for the stage. Keep those positions and stage-wide Qids when redisplaying unanswered questions after a partial reply or resume; show only unanswered questions. A new round starts its position count at 1 and continues Qids after the highest existing ID.

### Replies

- Accept keyed selections (`Q7: B`), keyed custom text (`Q7: <your answer>`), and keyed recommendation acceptance (`Q7: accept`), including several keyed answers in one message. Store the option ID for a recognised selection, the user's text for a custom answer, or `recommended` for acceptance. If the user selects only `Something else`, request their custom text and leave that question unanswered until supplied.
- Bare `accept` fills only unanswered questions in the current round with their recommendations. Preserve explicit answers unless the user explicitly revises them. Missing or unclear recommendations require user input; invent none.
- A bare option letter is valid only when exactly one question remains unanswered and the letter identifies one of its options. Unkeyed free text may answer that single remaining question when its intent is clear. Multiple unanswered questions, unknown IDs/options, or otherwise ambiguous replies: save any unambiguous answers and ask for clarification of the rest before assigning them. Generic acknowledgments are not acceptance aliases.

## Relay

How the orchestrator carries an agent's questions to the user and back:

1. Append the frontier to `state.relay.rounds` as `{ "questions": [...], "answers": {} }` (creating `relay` for this stage if null). An existing open round on resume is reused, with its saved answers, rather than appended again.
2. **Fast mode** (`mode.fast` true, except initial grilling): fill only unanswered eligible questions from `recommended`, as `{ "answer": "<recommended>", "at": "<now>", "auto": true }`. Preserve explicit answers. Never auto-answer anything stored in `state.analyze.pending_clarify`, nor any question carrying `requires_user: true` ("Questions"); carry its origin (or flag) through every frontier until answered. Notify once per auto-accepted batch ("auto-accepted N questions in <stage>"). If all answered, continue at step 5; otherwise show the remaining questions normally.
3. Append the `timeline` entry for this user wait (below), set `status: waiting_user`, `NOTIFY`, then show all unanswered questions in one message using "Presentation". Keep an existing open wait entry on resume or partial replies.
4. Resolve replies by "Replies". Write each answer immediately into the last round's `answers` as `{ "answer": "<text>", "at": "<now>" }`. Wait until every question has an answer; then close the round's timeline entry.
5. Set `status: running` and `SPAWN` a fresh agent of the same role for the same stage, with the usual inputs and `state.json` path. It reads every round, applies settled answers, recomputes the frontier, and returns another round or `done`. Clear `relay` when the stage completes (state.md, "Checkpoint").

For initial grilling, the orchestrator follows the same frontier, presentation, persistence and reply rules in pending state, then recomputes the frontier itself rather than spawning a role. Grilling finishes only when the frontier is empty and the user confirms shared understanding.

## Timeline

Every wait on the user is one `timeline` entry (state.md, "Schema"). Append `{ "at": "<now>", "kind": ..., "stage": ..., "summary": "<one line>" }` when the message is shown — `kind` is `questions` for a relay round, `notice` for any other `NOTIFY` that ends your turn, `approver` for the gate, `halt`. When the user answers, set that entry's `answered_at` and `latency_ms` in place (for a round with several answers, latency runs from the round's `at` to the last answer). Never clear or rewrite earlier entries; a wait the run never came back from keeps its nulls.
