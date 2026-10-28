# Implementation plan

Use Python 3 stdlib, existing `src/greet.py` and `test_greet.py`, and `python3 -m unittest discover -s .`. Preserve the public function and normal-name behavior. The fixture constitution applies. No new files, abstractions or dependencies are planned.

## Test seams
- greet — public `src.greet.greet`; normal names (including surrounding whitespace), empty and whitespace-only inputs.
Exempt: none
Overridden: none
Confirmed: 2026-10-28 - Q1 accepted - seams: greet
