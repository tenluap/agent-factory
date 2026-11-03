# `ponytail` governs change size; `engineering.md` keeps the process and hard-defect rules

2026-11-03: code-writing roles wrote large, mostly additive changes and copied existing code instead of reusing it. Factory commits added far more than they removed (`a7d0eeb` +207/−1, `dc8d0f6` +189/−13), and a round-3 verdict found a fix that replaced a call to the existing `json_or_usage` helper with an inline copy. `ponytail` was already active at full level, but ADR 0001 let `engineering.md` win every conflict "including its permission to refactor", so its design rules (SOLID, encapsulation, types, layering) outranked `ponytail`'s smallest complete change. `ENG-6` fired only before a new function and searched only the changed module and utility folders, so an inline copy never triggered it.

Where skill guidance conflicts with `engineering.md`, the skill now wins, except on `ENG-1`..`ENG-5` (tests, red proof, commit units, seams, exemptions), `ENG-11` (repository conventions), `ENG-17` (error handling) and `ENG-23`..`ENG-26` (concurrency, resource limits, security, integrity), where `engineering.md` wins. The design-guidance rules `ENG-7`..`ENG-10` and `ENG-13`..`ENG-16` apply only to the code a unit changes, and `ENG-1`/`ENG-19` bound refactoring the same way. `ENG-6` now runs before any new code, including a new logic block, as a repository-wide keyword search once per concept per commit unit. Each new file, function, method or class that remains carries a `New: <path or symbol> - <why no existing code fits>` line in its commit body; test code and plan-justified files are exempt.

## Considered options

- **Drop only "including its permission to refactor"**: smallest edit, but the design rules still outrank `ponytail` and keep pushing for more structure.
- **Make reuse findings blocking**: a stronger feedback loop, but it reverses ADR 0004's severity ceiling before the cheaper instruction changes are measured. Deferred.
- **Skill wins outside process and hard-defect rules** (chosen): `ponytail` decides how much code a unit adds, while test-first, commit evidence, repository conventions and real defects keep `engineering.md`'s authority.

## Consequences

`DESIGN.md` states this precedence once, and `code-build`, `fixer` and `design-to-code` each carry it as one inline phrase. `code-standards` reads the `New:` lines and reports a missing or false one as a MEDIUM, non-blocking `ENG-6` finding under ADR 0004. Plan and task granularity upstream is unchanged; if replays still show oversized units, that is the next lever.
