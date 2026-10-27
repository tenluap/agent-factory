# Benchmark fixture

Read the seeded brief before planning. Preserve the acceptance test.

- Build: `python3 -m compileall -q src`
- Test: `python3 -m unittest discover && python3 -m unittest test_acceptance`
- Record `python3 -m unittest test_acceptance` separately in the final verify
  command list, with its actual result. The offline scorer needs this evidence.
- No remote required; use local `main` as the base. Stop at `approver`.
