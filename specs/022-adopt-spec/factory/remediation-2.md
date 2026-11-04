# Remediation 2 (for analyze-2.md)

- U1: deferred to clarify (pending_clarify `Q5-pre-adoption-commit-evidence`: whether commits before `adopted.base_commit` and pre-adoption tasks are also outside the ENG-1/ENG-3 commit-evidence checks; widens settled grill Q9).
- C1: research.md D2 states that a `<src>` failing `git check-ref-format --branch` (`../x`, `a..b`) is no match, exit 1, nothing read or written; contracts/cli.md exit 1 says the same; tasks.md T004 Red adds `adopt ../x` to the existing "no matching source exits 1" case. Within the declared failure path; plan.md "Test seams" and the Q2 snapshot are unchanged.
- I1: tasks.md T004 Red fixture is now a clean committed `factory/state.json` asserting `refusal` names `resume 007-x` with `dirty: []`.
- I2: spec.md FR-016 and Key Entities "Adoption source" say "branch and spec dir".
- I3: spec.md FR-021 and US6-1 require the hint `adopt <branch|spec_dir>` (the CLI's own verb), matching contracts/cli.md, D9 and T009.
- U2: research.md D2 names the step-3 candidate set (local branch names plus `specs/*/` names on `base` and local `<default>`, matched equal or by `-<src>` suffix); tasks.md T004 names the fixture as local branches `007-x` and `008-x`.

Word counts after: spec.md 2987/3000, plan.md 1497/2000 (unchanged), tasks.md 2499/2500.

## Q5 applied

- Q5-pre-adoption-commit-evidence (answer A): the pre-adoption boundary now covers ENG-1 (commit evidence per checked task), ENG-2 and ENG-3 (commit unit); code is still reviewed in full. Changed: spec.md (clarify Q5, US5 why/scenario 1, FR-019, FR-023, Key Entities, SC-005; edge case and assumption trimmed for budget), plan.md (summary, structure, `adopted_base` reason, Review step 7, Exempt line gains `core/roles/code-standards.md`; test seams and Q2 confirmation unchanged), research.md D10, tasks.md (T013 adds `core/roles/code-standards.md` and ENG-1 skipping in spec-conformance; T001 wording trimmed), quickstart.md step 6, docs/adr/0017-adopted-runs-enter-at-most-at-analyze.md (decision 4, rejected option). CONTEXT.md already states the general rule; unchanged.

Word counts after Q5: spec.md 2998/3000, plan.md 1556/2000, tasks.md 2500/2500.
