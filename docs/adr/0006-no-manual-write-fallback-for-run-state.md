# No manual write fallback for run state

Run state mutates only through the CLI writer: it stamps, validates, writes atomically and commits, and when it cannot run (missing Python 3, missing script) the run halts instead of falling back to editing `state.json` by hand. The manual paths in `state.md` stop being a fallback and remain only the definition of what the script does. The alternative — letting a human patch state when tooling is unavailable — was rejected because runs 005 and 006 show hand-edited state damage: a bypassed validation writes backwards timestamps and off-vocabulary events that no later step detects, so the cheap escape destroys the guarantee every other gate rests on. Halting is the deliberate trade: availability is given up to keep state trustworthy.

## Consequences

- A machine without Python 3 cannot run the factory; preflight and the installer say so up front rather than degrading.
- Recovery from a halt is tooling repair, never a hand edit, so resume can trust what it reads.
- The design decision per S-item lives in `DESIGN.md`; this record holds the trade-off only.
