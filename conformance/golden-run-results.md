# Golden-run results (FR-013)

Per adapter and capability tier. The live two-harness run is recorded after
merge (one enforcing harness paired with one disclosing harness); the
checklists live in `golden-run/<harness>.md`.

| Harness | Tier | Run date | Result | Steps passed | Notes |
|---|---|---|---|---|---|
| claude-code | enforcing | _after merge_ | not yet run | / | |
| opencode | enforcing | _after merge_ | not yet run | / | |
| copilot | enforcing | _after merge_ | not yet run | / | |
| zcode | enforcing | _after merge_ | not yet run | / | |
| codex | disclosing | _after merge_ | not yet run | / | read-only by instruction only |

A result records the fixture commit, both harnesses used, and the kill/resume
leg. `/` marks a step that does not apply on that adapter.

## Run reliability (012)

Native workflow acceptance follows [run-reliability.md](run-reliability.md). Packaging checks do not prove agent behavior. Record each matrix case separately; preserve the subject's original output before assessing it.

| Case | Instruction commit/hash | Native subject and input | Observed evidence | Before | After |
|---|---|---|---|---|---|
| S1 matrix | pending | pending | pending | pending | pending |
| S2 matrix | pending | pending | pending | pending | pending |
| S3 matrix | pending | pending | pending | pending | pending |
| S4 matrix | pending | pending | pending | pending | pending |

Each result must name actual envelope/fixture paths, decisive output excerpts, relevant git commits/checkboxes or CLI statuses, and any capability limitation. Keep before/after subjects fresh and record differing absolute paths/deadlines. Pending/unavailable cases do not count as completed acceptance. The model-policy baseline is recorded in `specs/012-run-reliability/factory/baseline.md`: 19 focused tests ran with three existing policy failures before behavior edits.
