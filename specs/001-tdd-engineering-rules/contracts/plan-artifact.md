# Contract: the plan and task-list artefacts after this change

The shape every future factory run's `plan.md` and `tasks.md` must have. Producer: the planning role (`spec-builder`, plan and tasks stages). Consumers: the planning role's own analyze stage, the implementing and fixing roles (read the seams and exemptions), the spec-conformance reviewer (reads exemptions and task mapping), the user at the approver gate.

## `plan.md`: the "Test seams" section

Required in every plan produced after this change (FR-016, SC-003). Contents:

```text
## Test seams

<one entry per seam: the public entry point put under test, and the behaviour it covers>

Exempt: <part of the change that is documentation or configuration only> - <reason>
Test runner: <runner chosen> - <why> # only when the repository has none
Overridden: ENG-n - <repo rule that wins> # one line per override, or "Overridden: none"
```

- At least one seam, or a stated exemption covering the part of the change with no seam. Both may appear.
- `Exempt:` is required for any part of the change that carries no seam; a part with neither a seam nor an exemption is an analyze finding.
- `Test runner:` appears only when the repository has no runner; the plan names the language's conventional default and the reason, and setting it up becomes the first task (FR-018). The user may object at the approver gate; the run does not ask mid-flow.
- `Overridden:` names the rule by its `ENG-n` id and the repository rule that wins (FR-005). Absent overrides are stated as `Overridden: none`.

## `plan.md`: reasons for new files, abstractions and dependencies

Required in every plan produced after this change (FR-020b, SC-003a, `ENG-10`, constitution V where the repository has one). One line per thing introduced:

```text
<path or name> - <file | abstraction | dependency> - <reason it is needed>
```

- One reason per new file, new abstraction and new dependency the plan introduces. A table row carrying the same three parts satisfies this.
- A kind the change introduces nothing of is stated as `none` explicitly ("new dependency: none"), so silence is never read as completeness.
- The reason may live elsewhere in the plan (typically the Constitution Check) as long as the line points at it; it is not restated twice.
- A generated file is justified as mandated by the render, not chosen.
- Scope: what this change adds. Files the repository already had need no reason.

## `tasks.md`: task ordering

- Every implementation task is immediately preceded by a task that writes a failing test for the seam that implementation task targets, and the test task names the seam (FR-019, SC-002).
- Each seam named by a task appears in the plan's "Test seams" section.
- Tasks covered by a plan exemption carry no test task, and say which exemption they fall under.
- When the repository has no test runner, the runner-setup task is task 1.

## Analyze check

For each implementation task in `tasks.md`, and for each new file, abstraction and dependency `plan.md` introduces:

| Observation | Report |
|---|---|
| Mapped to a seam listed in the plan, and preceded by a test task for that seam | Nothing |
| No mapped seam, and not covered by a plan exemption | HIGH, blocking: names the task and the missing seam |
| No test task immediately before it, and not covered by a plan exemption | HIGH, blocking: names the task |
| Covered by a plan exemption with a stated reason | Nothing (excluded from the check, not downgraded) |
| Names a seam the plan does not list | HIGH, blocking: names the task and the unlisted seam |
| A new file, abstraction or dependency the plan introduces with no stated reason | MEDIUM, **non-blocking**: names that file, abstraction or dependency and cites `ENG-10` |
| Every new file, abstraction and dependency carries a reason (`none` stated for a kind with nothing new) | Nothing |

HIGH, never CRITICAL: CRITICAL stays reserved for constitution violations. A HIGH finding feeds the orchestrator's existing remediation loop (FR-020, FR-020a). All three blocking conditions above — no mapped seam, no immediately preceding test task, a seam the plan does not list — are the ones FR-019, FR-020 and SC-002 state, so the gate and the requirement cannot diverge.

The reason-line row is the one non-blocking condition in this table: it is MEDIUM and never blocking, and it never by itself triggers the remediation loop's blocking path, because `ENG-10` is a judgement call and the FR-015f severity ceiling applies at artifact time as well as to diffs (FR-020b, SC-003a). The run continues with the omission visible to the user.

## Clarify check

The clarify stage asks about test seams only when the feature description leaves them ambiguous. Clear seams raise no question (FR-021).

## Implementation-time guarantee

The implementing role uses only the seams this artefact lists. A task needing an unlisted seam ends the implement stage with `failed`, naming the task and the missing seam, so the orchestrator's existing failure policy halts the run and asks the user (FR-011a).

The same stop applies when the repository has a test runner whose test command cannot be run (missing dependency, broken configuration, no runner binary): the implementing role, and equally the fixing role, ends with `failed` naming the task or fix, the un-runnable command and the error it produced (FR-011b, FR-013b). Neither role writes behaviour-changing code with no observed red step, and neither records a third form of red proof.
