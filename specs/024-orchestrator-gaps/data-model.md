# Data Model: Close Orchestrator Bookkeeping Gaps

No schema version change (state version 5 stays). Fields below already exist unless marked new.

## Review counters (`state.review`)

| Field | Type | Writer | Rule |
|-------|------|--------|------|
| `round` | int ≥ 0 | `checkpoint review` | `max(round, highest n with factory/reviews/round-<n>/verdict.json)`; never decreases |
| `fix_rounds` | int ≥ 0 | `checkpoint fix` | `+1` only when run stage is `fix` and no matching `pending_design_fix` reservation |
| `pending_design_fix` | object or absent | `checkpoint review --next fix --design-fix <verdict>`; cleared by `checkpoint fix` | `{attempt, round, verdict}`; stores `attempt` = `fix_rounds + 1` without incrementing the counter; after fixer completion and verification, `checkpoint fix` counts and clears it atomically; a legacy reservation with `attempt == fix_rounds` suppresses the checkpoint increment |

## Relay question (`state.relay.rounds[-1].questions[]`)

Protocol question shape (protocol.md "Questions"). `answer --question` stores it when the id is absent or id-only. `requires_user: true` triggers the record.

## Relay record (new runtime file)

Path `<spec_dir>/factory/relay/<stage>-<qid>.md`. Immutable. Fields: stage, question id, answer, origin (`explicit` / `auto` / `cruise_override`), answer time, title, text, options. Layout in research.md R4.

## Overrun issue (`state.issues[]`, kind `overrun`, cause `unreported`)

`detail` = `"<role> ran <excess>s past its <seconds>s budget (<total>s total) without a self-report"`; `duration_ms` unchanged.

## Budget config (`${FACTORY_HOME}/config.json`)

`budget: { default_s, roles: {<role>: s}, review_full_s }`. `review_full_s` new, optional, positive int, default 600; applies only to `REVIEWER_ROLES` = `security-reviewer`, `code-standards`, `spec-conformance`, `ui-reviewer`, `ux-reviewer` on a full-diff review.
