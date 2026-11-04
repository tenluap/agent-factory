# Remediation 2 (for analyze-2.md)

- U1: deferred to clarify (pending_clarify `Q5-pre-adoption-commit-evidence`: whether commits before `adopted.base_commit` and pre-adoption tasks are also outside the ENG-1/ENG-3 commit-evidence checks; widens settled grill Q9).
- C1: research.md D2 states that a `<src>` failing `git check-ref-format --branch` (`../x`, `a..b`) is no match, exit 1, nothing read or written; contracts/cli.md exit 1 says the same; tasks.md T004 Red adds `adopt ../x` to the existing "no matching source exits 1" case. Within the declared failure path; plan.md "Test seams" and the Q2 snapshot are unchanged.
- I1: tasks.md T004 Red fixture is now a clean committed `factory/state.json` asserting `refusal` names `resume 007-x` with `dirty: []`.
- I2: spec.md FR-016 and Key Entities "Adoption source" say "branch and spec dir".
- I3: spec.md FR-021 and US6-1 require the hint `adopt <branch|spec_dir>` (the CLI's own verb), matching contracts/cli.md, D9 and T009.
- U2: research.md D2 names the step-3 candidate set (local branch names plus `specs/*/` names on `base` and local `<default>`, matched equal or by `-<src>` suffix); tasks.md T004 names the fixture as local branches `007-x` and `008-x`.

Word counts after: spec.md 2987/3000, plan.md 1497/2000 (unchanged), tasks.md 2499/2500.
