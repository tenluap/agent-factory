# Enforce Analyze remediation targets

**Proposed workflow change.** Require measurable improvement after remediation and explicit approval before the factory amends a constitution.

## Tasks

- [ ] Have the existing analysis writer retain the first completed report and its counts by severity as the baseline. Subsequent reports update the latest result. Preserve the baseline on resume and when lite escalates to full. For an older in-progress run, establish the baseline from trustworthy original evidence or ask how to restart analysis if that evidence is unavailable.
- [ ] Have the spec builder apply recommended fixes in place to the affected spec, plan, and tasks, then run fresh analysis. If a finding warrants changing the constitution itself, present the exact proposed amendment, its rationale, and the version bump for explicit approval. Apply only the approved draft through the constitution amendment process. A change to that draft requires fresh approval.
- [ ] Enforce the acceptance rule in the implementation checkpoint. Critical and high counts must both reach zero. The total and low counts must each be strictly below half their respective baseline counts. When a baseline count is zero, its recheck count must remain zero. Count newly discovered findings and keep protected questions pending until explicitly answered.
- [ ] Keep lite-to-full escalation for serious findings. Allow up to two automatic repair-and-recheck cycles when targets remain unmet, including when the remaining findings are medium or low. After two unsuccessful attempts, show the original counts, latest counts, and unmet targets. Implementation stays paused while any target is unmet.

## Acceptance

- For 12 initial findings with 6 low, a recheck may have at most 5 total, at most 2 low, and zero critical or high.
- Exactly half fails. Odd and zero baselines are checked without rounding ambiguity. New serious findings block implementation.
- Resume retains the baseline and consumed repair attempts. A declined or missing approval leaves the constitution unchanged. An approved amendment is followed by fresh analysis.

[Current analysis workflow](../../../core/skills/factory/SKILL.md) · [Constitution governance](../../../.specify/memory/constitution.md)
