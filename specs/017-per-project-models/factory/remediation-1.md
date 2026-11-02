# Remediation 1 (analyze-1)

- M1: plan "Adapter defaults at runtime" states `adapter_models.json` carries `{"deep": "", "standard": ""}` for copilot and zcode (empty = inherit session model), parity test treats an absent adapter tier as `""`, init seeds them with source `adapter`; T002 implement/pass, T003 and T005 red cases updated.
- M2: plan Design defines `<repo>` as parent of `git rev-parse --path-format=absolute --git-common-dir`; T003 adds a linked-worktree test case and the implement note.
- M3: plan Design rules unknown harness keys (and unknown tier keys) in project or user config a malformed-config error naming file, key and known values; resolve seam gains failure path "unknown harness key" (plan Test seams, T003, T004); spec Edge Case reworded. Seam scope changed, so the Q2 confirmation is marked superseded and fresh acceptance is returned as pending Q13 (requires_user).
- M4: plan "New files, abstractions, dependencies" adds `ModelConfigError` line with its reason.
- M5: plan Design states refusal keys on `config.json` alone; T005 adds both cases (README missing with config present refuses; README present without config rewrites both).
- L1: plan Structure Decision corrects `commands.py` size to "over 1500 lines".
- L2: tasks Dependencies: T008-T011 independent of T007, start after T004.
- L3: T005 adds pre-existing empty `.factory/` case.
- L4: T007 tagged `[US6]`.
