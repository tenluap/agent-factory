# Research: Factory Run Reliability

## Evidence

The archived backlog contains two inaccessible OpenCode model attempts, a task/implementation/seam restart, and three 3–8 second overshoots with different work commits. It does not prove repeated pointless testing or a performance bottleneck.

## Model inspection

Decision: use existing per-harness capabilities and preserve a three-way outcome. Local `opencode --help` lists `models`; `opencode models --help` says it lists available models and accepts server/standalone flags. No live inventory or auth probe was needed to establish that interface. Other adapters currently name no model-inventory operation; they must disclose unverified unless their actual session supports one. Effective installed files take priority over stale source defaults. Inventory membership is evidence of listing, not proof of provider access.

Alternative rejected: fabricate a universal API, auto-fix aliases, switch models or probe credentials. Those change user choice or invent capabilities.

## Existing model-policy mismatch

DESIGN's model-policy paragraph, README and `test_render_models.py` require only Claude Code defaults with opus/sonnet. Current adapters ship Claude Code opus/haiku, Codex and OpenCode model mappings. The correct documented focused test command ran 19 tests with three policy failures and no errors; see [factory/baseline.md](factory/baseline.md). Decision: the user explicitly accepted plan Q2 on 2026-10-28, preserving the shipped selections and aligning stale policy/tests. Rationale: this matches the approved scope and repairs the demonstrated mismatch without changing models. Alternative rejected by the accepted choice: restore old inherited/opus-sonnet defaults. This is not ignored as an acceptable permanently red baseline.

## Atomic task unit

Decision: one behavior task owns red/implementation/passing checks/one commit. Existing spec-builder requires separate failing-test tasks while ENG-3/code-build commit each task once. Treat legacy adjacent test/implementation entries as one explicitly identified unit when unambiguous; report ambiguous pairing. Do not build a speculative task parser or new state schema.

## Scope and deadlines

Decision: confirmation covers seam identities plus injected failure paths; analyze checks coverage before implementation. Existing name-only reuse is insufficient when a task expands git-failure injection. Near-deadline choices use available observed command durations, without changing budgets. Keep mandatory final checks and actual overrun/stall accounting.

Alternative rejected: tolerance windows hiding small overruns, raising budgets without measurement, or treating unchanged checks as passed after handoff.

## Validation

Decision: extend existing stdlib unittest renderer/accounting coverage and run native-agent fixture trials for prompt behavior. Static string tests can prove packaging contracts, never actual agent decisions. No new runtime dependencies. Protected plan Q1 confirmed the complete declared S1–S4 scope and failure paths on 2026-10-28; Q2 confirmed the model policy on the same date. Both answers are explicit (`auto: false`) in the plan relay. No planning clarification remains.
