# Remediation log — pass 1

Source: `factory/analyze-1.md`. All edits in place; no seam or failure-path change, so the plan's `Confirmed:` line stays valid.

- C1: tasks.md T012 step 1 now asserts that preflight, after `instructions-record`, reads every `always` entry in full at the recorded ref (FR-023 preflight read).
- D1: tasks.md T001 now adds a "Repo instructions validation" entry under `DESIGN.md` "Validation plan" (machine checks plus agent-driven runs: preflight records and discloses, resume delta, `CONTRIBUTING.md`-only test command fixture; SC-003, SC-006).
- A1: spec.md SC-006 reworded to an executable criterion: the orchestrator text records the command as documented and the text-contract test asserts it; the fixture run lives in the D1 validation entry.
- I1: spec.md edge case "Not a git repository…" now says the writer reports it in `error` and the orchestrator discloses it, matching contracts/cli.md and research R9.
- I2: plan.md Performance Goals now says three git processes per scan (`rev-parse`, `ls-tree`, `cat-file --batch`).
- I3: plan.md Complexity Tracking now carries a Principle II row referencing the Constitution Check justification instead of "No constitution violations".
- U1: tasks.md T002 step 1 asserts no entry at or under the gitlink path.
- U2: data-model.md `source` states a root catalogue agent file matched by `instructions.include` keeps `source: "catalogue"` (FR-024 top tier preserved); tasks.md T006 asserts it.
- C2: tasks.md T011 done condition checks `factory init` writes a `config.json` with no `instructions` key (FR-014).
- T1: tasks.md T014 drops the "Exempt:" label; it is described as a verification step that changes no files.

Word counts after edits: spec.md 2994/3000, plan.md and tasks.md within budget.
