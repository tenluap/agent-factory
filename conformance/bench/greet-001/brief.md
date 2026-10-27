# Benchmark: uppercase greetings

Add an optional keyword argument `uppercase=False` to `src.greet.greet`.
The existing greeting remains `Hello, <name>!` by default. When uppercase is
true, uppercase the entire greeting using Python's string behavior.

## Settled decisions

- Delivery intent; initial grilling is complete. Use the lite chain, fast mode.
- Keep existing callers compatible. No dependencies, CLI or UI.
- Public test seam: `src.greet.greet(name, uppercase=False)`. Test default,
  uppercase, and empty-name greetings only through this function.
- This fixture explicitly confirms that exact seam for the generated plan;
  a changed seam or scope still requires a protected confirmation.
- Preserve the seam name `src.greet.greet(name, uppercase=False)` in the plan's
  Test seams section. Record its fixture-author confirmation as
  `Confirmed: 2026-10-27 - BENCH-SEAM accepted - seams: src.greet.greet(name, uppercase=False)`.
  This confirmation covers this fixed fixture only, never a changed scope.
- `test_acceptance.py` is the fixture's acceptance test. Preserve it and run
  `python3 -m unittest test_acceptance` as a separate recorded verify command.
- Build: `python3 -m compileall -q src`.
- Test: `python3 -m unittest discover && python3 -m unittest test_acceptance`.
- Stop before the approver stage. No approval, PR, or network remote required.
