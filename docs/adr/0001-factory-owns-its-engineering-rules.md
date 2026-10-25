# The factory owns its engineering rules; `tdd` and `ponytail` contribute technique under its orchestration

The discipline every code-writing role follows lives in one self-contained reference inside the factory, `core/skills/factory/references/engineering.md`, and it stays authoritative: no skill outside the factory weakens a rule or replaces a role's required result envelope. Pointing roles directly at the external `tdd` skill was originally rejected outright, because that skill confirms test seams with the user mid-loop and factory agents are stateless and never talk to the user.

2026-10-25: that gap is closed, not avoided. `spec-builder` now relays the plan's proposed seams as one protected (`requires_user`) relay question at the end of `plan`, persisted with the plan and reused only while the seams and scope match (`core/skills/factory/references/skills.md`; `DESIGN.md`, "Protected confirmations"). With the user's confirmation carried through state rather than asked by the skill itself, `code-build` and `fixer` now read `tdd`'s testing technique and `ponytail`'s reuse-first, minimum-sufficient-change guidance directly, bounded by the approved spec. Where `tdd` defers refactoring to review and `engineering.md`'s `ENG-1` permits small behaviour-preserving refactoring while green, `engineering.md` wins — stated explicitly in the shared reference, not left implicit.

The rule reference itself keeps no dependency on any skill: `engineering.md` renders into every harness unchanged, which an external skill cannot guarantee, and remains the single source of the `ENG-n` ids findings, verdicts and plan overrides cite.

## Consequences

- The rules must be maintained here, and can drift from the external `tdd` skill's own guidance. That is accepted: the factory's copy is the authority for factory runs, and it wins every stated conflict.
- Each rule carries a stable `ENG-n` id so findings, verdicts and plan overrides can name a rule without quoting it, and so renumbering is a deliberate act.
- The 2026-10-25 expansion preserves `ENG-1`..`ENG-11` and adds `ENG-12`..`ENG-31`, covering the 34-practice quality checklist without reinterpreting old rule ids. External articles are optional reading; roles can apply the rules without fetching them.
- `ponytail` and `tdd` are resolved skills, not vendored code: a missing one stops the affected code-delivery work with setup guidance rather than silently skipping its technique (`core/skills/factory/references/skills.md`).
