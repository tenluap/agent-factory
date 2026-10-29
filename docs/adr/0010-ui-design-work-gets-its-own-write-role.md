# UI design work gets its own write role

The Pen design-code mapping contract (2026-10-25) deliberately added no agent role: Pen implementation rode on `code-build` and `fixer`. We now add one write role, `ui-designer`, spawned in the implement step for tasks marked `[UI]` on a UI design run, because design-to-code work has its own state machine (detect framework, survey once, plan canonical components, implement dependency batches, validate fidelity, one quality pass) that does not fit `code-build`'s test-first task loop, and the user already runs it outside the factory. The role adds no route, stage, harness verb, second map, new gate or second repair loop: review, the two shared fix rounds and the approver gate stay as they are, and `fixer` still repairs design findings.

`spec-builder` classifies the run at plan (a text-only restyle only for a purely visual brief) and resolves a needed `figma` capability there, so a missing capability blocks before tasks. The role's one `ui-agent` quality pass runs in the spawn completing the last `[UI]` task and is recorded so a resume does not repeat it. At drop, design evidence rehomes to `docs/design/<branch>/`.

## Considered options

- **Keep design work on `code-build`** (the 2026-10-25 decision): no new role. But `code-build` would carry framework detection, source authority rules and the batch state machine as conditional branches.
- **A separate `/factory design` route**: rejected, as it would duplicate the run lifecycle for one kind of task.
- **One write role routed by task marker** (chosen): mixed runs keep `code-build` for non-UI tasks, and non-design runs are unchanged.
