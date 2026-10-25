# Specification Analysis Report — pass 1

Reviewed `spec.md`, `plan.md`, `tasks.md`, supporting research/data-model/contract/validation guide, the project constitution, and the factory engineering rules. Prerequisite discovery succeeded and resolved this feature directory. Spec artifacts were read only; this report is the sole output. Extension hooks were skipped as required by the factory role.

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| — | — | — | — | No actionable inconsistencies, coverage gaps, or constitution conflicts found. | Proceed with the planned implementation and verification gates. |

## Coverage summary

All success criteria describe deliverable behavior or verification, rather than post-launch business outcomes, and are included in the inventory.

| Requirement key | Has task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 | Yes | T003, T004 | Native role definitions and ordered permission serialization. |
| FR-002 | Yes | T003, T004 | All nine roles preserve read/write access intent and deny child dispatch. |
| FR-003 | Yes | T004 | Native named foreground subagent, parallel dispatch, and shell instructions. |
| FR-004 | Yes | T004, T006, T007 | Retain install paths, model behavior, relay, skill resolution, and neutral flow. |
| FR-005 | Yes | T002, T004, T006 | Canonical baseline and full distribution byte comparison. |
| FR-006 | Yes | T003, T004, T005 | Ordered mappings with existing Markdown/TOML behavior preserved. |
| FR-007 | Yes | T001, T004, T006, T008 | Design-first commit, generated output with source, postcommit reproducibility gate. |
| FR-008 | Yes | T003, T005, T006, T008 | Role policy, legacy formats, model fields, complete generation, and parity checks. |
| FR-009 | Yes | T001, T007 | Supported V1 compatibility, native adoption, historical version, and separate evidence categories. |
| FR-010 | Yes | T007, T008 | Observed dispatch/policy conflicts block delivery without weaker restrictions. |
| SC-001 | Yes | T003, T004, T006 | Nine generated roles checked against the native contract. |
| SC-002 | Yes | T002, T004, T006 | All five distributions; unaffected native agents and unrelated contents remain identical. |
| SC-003 | Yes | T006, T008 | Repeated canonical generation and clean tracked/untracked distribution status. |
| SC-004 | Yes | T007, T008 | Static, discovery, dispatch, and enforcement outcomes recorded accurately. |
| SC-005 | Yes | T004, T005, T006, T007 | Existing installation/model contracts and unchanged shared flow. |

All three user stories have task coverage and an independent check. No task is unmapped: T001 and T002 establish the design and baseline required by US1/US2; T003–T007 implement or verify the stories; T008 supplies the release gates.

## Constitution and engineering alignment

- **Design First:** T001 is a separate contract commit before T004 changes adapter behavior.
- **Harness-Neutral Core:** The scope confines native details to the OpenCode adapter and leaves `core/` unchanged.
- **Generated Dist:** T004 generates all harnesses and commits output with source. T008 rerenders after commit and uses `git status --porcelain -- dist/` to include untracked additions in the required gate.
- **Stateless Agents:** Handoff/baseline/evidence locations are persisted on disk; historical proof is not reused as fresh red evidence.
- **Simplicity and Reuse:** The plan extends the existing serializer, uses standard-library unittest, introduces no production abstraction or dependency, and states reasons for its new files.
- **Protected test seams:** The plan's confirmation names exactly `render_agent()`, `agent_fields()`, and `render()`. T003 immediately precedes the sole behavior implementation task T004, maps those seams, requires observed failures, and keeps tests plus implementation in one commit with precise red proof.
- **Exempt tasks:** Documentation, configuration, generated output, and verification tasks carry the plan's reasons. T004 still tests the serializer behavior and consumed adapter output. T005 adds regression coverage of already-correct model behavior; it is not a second behavior implementation task and does not require manufactured red evidence.
- **Proportionate quality constraints:** Policy restrictions, isolated temporary configuration, cleanup, bounded optional discovery, compatibility, reproducibility, and evidence limits are planned. No unrelated service, benchmark, telemetry, or model-call requirement is introduced.

There are no constitution alignment issues, unmapped implementation seams, missing adjacent test tasks, or unstated new-file/abstraction/dependency reasons to report.

## Budgets and metrics

Word counts use `wc -w` on the reviewed files.

| Artifact | Words | Budget | Result |
|----------|------:|-------:|--------|
| `spec.md` | 1,383 | 3,000 | Within budget |
| `plan.md` | 935 | 2,000 | Within budget |
| `tasks.md` | 1,209 | 2,500 | Within budget |

- Requirements: 15 (10 functional requirements, 5 success criteria).
- Tasks: 8.
- Requirements with task coverage: 15/15 (100%).
- Ambiguity findings: 0.
- Duplication findings: 0.
- Critical: 0; high: 0; medium: 0; low: 0.
- Blocking findings: 0.

## Next action

Proceed to implementation in the declared sequence. This analysis approves artifact consistency; it does not establish runtime dispatch or permission enforcement. Those checks remain unverified unless actually executed, as required by the plan.
