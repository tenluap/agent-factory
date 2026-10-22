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

## `tasks.md`: task ordering

- Every implementation task is immediately preceded by a task that writes a failing test for the seam that implementation task targets, and the test task names the seam (FR-019, SC-002).
- Each seam named by a task appears in the plan's "Test seams" section.
- Tasks covered by a plan exemption carry no test task, and say which exemption they fall under.
- When the repository has no test runner, the runner-setup task is task 1.

## Analyze check

For each implementation task in `tasks.md`:

| Observation | Report |
|---|---|
| Mapped to a seam listed in the plan, and preceded by a test task for that seam | Nothing |
| No mapped seam, and not covered by a plan exemption | HIGH, blocking: names the task and the missing seam |
| No test task immediately before it, and not covered by a plan exemption | HIGH, blocking: names the task |
| Covered by a plan exemption with a stated reason | Nothing (excluded from the check, not downgraded) |
| Names a seam the plan does not list | HIGH, blocking: names the task and the unlisted seam |

HIGH, never CRITICAL: CRITICAL stays reserved for constitution violations. A HIGH finding feeds the orchestrator's existing remediation loop (FR-020, FR-020a). All three blocking conditions above — no mapped seam, no immediately preceding test task, a seam the plan does not list — are the ones FR-019, FR-020 and SC-002 state, so the gate and the requirement cannot diverge.

## Clarify check

The clarify stage asks about test seams only when the feature description leaves them ambiguous. Clear seams raise no question (FR-021).

## Implementation-time guarantee

The implementing role uses only the seams this artefact lists. A task needing an unlisted seam ends the implement stage with `failed`, naming the task and the missing seam, so the orchestrator's existing failure policy halts the run and asks the user (FR-011a).
