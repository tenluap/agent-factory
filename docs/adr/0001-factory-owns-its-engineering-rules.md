# The factory owns its engineering rules instead of depending on the `tdd` skill

The discipline every code-writing role follows lives in one self-contained reference inside the factory, `core/skills/factory/references/engineering.md`, with no dependency on any skill outside the factory. It covers test-first delivery and proportionate practices for correctness, readability, maintainability, security and performance. The obvious alternative, pointing roles at the existing external `tdd` skill, was rejected because that skill confirms test seams with the user mid-loop and factory agents are stateless and never talk to the user; a shared in-factory reference also renders into every harness unchanged, which an external skill cannot guarantee.

## Consequences

- The rules must be maintained here, and can drift from the external `tdd` skill. That is accepted: the factory's copy is the authority for factory runs.
- Each rule carries a stable `ENG-n` id so findings, verdicts and plan overrides can name a rule without quoting it, and so renumbering is a deliberate act.
- The 2026-10-25 expansion preserves `ENG-1`..`ENG-11` and adds `ENG-12`..`ENG-31`, covering the 34-practice quality checklist without reinterpreting old rule ids. External articles are optional reading; roles can apply the rules without fetching them.
