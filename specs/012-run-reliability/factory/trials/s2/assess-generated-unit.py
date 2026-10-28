"""Assess the native-generated task artifact for the single greeting behavior unit."""
import sys
from pathlib import Path

phase = sys.argv[1]
tasks = Path(__file__).parent / f"{phase}-healthy" / "S2-new/specs/001-greet/tasks.md"
checkboxes = [line for line in tasks.read_text().splitlines() if line.startswith("- [")]
assert len(checkboxes) == 1, f"S2-new-generation-atomic-unit: expected one checkbox, observed {len(checkboxes)}"
print("S2-new-generation-atomic-unit passed: one native-generated behavior commit unit")
