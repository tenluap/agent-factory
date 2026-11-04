"""Cruise mode seam tests (spec 021): state validation, mode resolution, the
CLI writers for `--cruise-override`, and the `pr` gate.

Each class covers one seam from plan.md "Test seams". CLI tests run the real
`bin/factory` subprocess against a hermetic Sandbox (see tests/__init__.py).
"""

import copy
import json
import sys
import unittest
from pathlib import Path

CORE_BIN = Path(__file__).resolve().parents[2] / "core" / "skills" / "factory" / "bin"
sys.path.insert(0, str(CORE_BIN))

from factory_cli import state  # noqa: E402
from tests import fixture  # noqa: E402


def cruise_base():
    """A valid v5 run at `implement` with cruise on (fast is on, as cruise requires)."""
    base = fixture("state-v5.json")
    base["mode"] = {"chain": "full", "fast": True, "cruise": True}
    return base


def relay_with_answer(answer):
    return {
        "rounds": [
            {
                "questions": [{"id": "Q1", "text": "Pick", "recommended": "A"}],
                "answers": {"Q1": answer},
            }
        ]
    }


class CruiseStateValidationTests(unittest.TestCase):
    """Seam: factory_cli.state.validate_state (FR-004, FR-022)."""

    def violations(self, mutate, base=None):
        loaded = copy.deepcopy(base if base is not None else fixture("state-v5.json"))
        mutate(loaded)
        return state.validate_state(loaded)

    def locations(self, mutate, base=None):
        return {v["location"] for v in self.violations(mutate, base)}

    def test_pre_feature_states_validate_clean(self):
        # FR-004 / SC-004: no `cruise`, no marker
        for name in ("state-v4.json", "state-v5.json"):
            self.assertEqual(state.validate_state(fixture(name)), [], name)
        self.assertEqual(state.validate_state(cruise_base()), [])

    def test_cruise_on_with_fast_is_valid(self):
        self.assertEqual(state.validate_state(cruise_base()), [])

    def test_marked_answer_decision_is_valid(self):
        base = cruise_base()
        base["decisions"].append(
            {
                "stage": "grill",
                "question": "Q2",
                "answer": "delivery",
                "auto": True,
                "at": "2026-10-23T09:00:00Z",
                "kind": "answer",
                "cruise_override": True,
            }
        )
        self.assertEqual(state.validate_state(base), [])

    def test_marked_analyze_exhaustion_gate_override_is_valid(self):
        base = cruise_base()
        base["decisions"].append(
            {
                "stage": "analyze",
                "question": "analyze-exhaustion",
                "answer": "proceed to implement",
                "auto": True,
                "at": "2026-10-23T09:00:00Z",
                "kind": "gate-override",
                "cruise_override": True,
            }
        )
        self.assertEqual(state.validate_state(base), [])

    def test_marked_relay_answer_is_valid(self):
        base = cruise_base()
        base["relay"] = relay_with_answer(
            {"answer": "A", "at": "2026-10-23T09:00:00Z", "auto": True, "cruise_override": True}
        )
        self.assertEqual(state.validate_state(base), [])

    def test_non_boolean_mode_cruise_is_reported(self):
        found = self.locations(lambda s: s["mode"].__setitem__("cruise", "yes"), cruise_base())
        self.assertIn("mode.cruise", found)

    def test_cruise_without_fast_is_reported(self):
        found = self.locations(lambda s: s["mode"].__setitem__("fast", False), cruise_base())
        self.assertIn("mode.cruise", found)

    def test_non_boolean_marker_on_decision_is_reported(self):
        def mutate(s):
            s["decisions"][0]["cruise_override"] = "true"

        self.assertIn("decisions[0].cruise_override", self.locations(mutate))

    def test_non_boolean_marker_on_relay_answer_is_reported(self):
        def mutate(s):
            s["relay"] = relay_with_answer(
                {"answer": "A", "at": "2026-10-23T09:00:00Z", "auto": True, "cruise_override": 1}
            )

        self.assertIn("relay.rounds[0].answers.Q1.cruise_override", self.locations(mutate))

    def test_marker_with_auto_false_is_reported(self):
        def mutate(s):
            s["decisions"].append(
                {
                    "stage": "grill",
                    "question": "Q2",
                    "answer": "delivery",
                    "auto": False,
                    "at": "2026-10-23T09:00:00Z",
                    "kind": "answer",
                    "cruise_override": True,
                }
            )

        self.assertIn("decisions[1].cruise_override", self.locations(mutate, cruise_base()))

    def test_marker_on_approved_record_is_reported(self):
        def mutate(s):
            s["decisions"].append(
                {
                    "stage": "approver",
                    "question": "approve",
                    "answer": "approved",
                    "auto": False,
                    "at": "2026-10-23T09:00:00Z",
                    "kind": "approved",
                    "cruise_override": True,
                }
            )

        self.assertIn("decisions[1].cruise_override", self.locations(mutate, cruise_base()))

    def test_marker_at_approver_stage_is_reported(self):
        def mutate(s):
            s["decisions"].append(
                {
                    "stage": "approver",
                    "question": "approve",
                    "answer": "changes",
                    "auto": True,
                    "at": "2026-10-23T09:00:00Z",
                    "kind": "answer",
                    "cruise_override": True,
                }
            )

        self.assertIn("decisions[1].cruise_override", self.locations(mutate, cruise_base()))


if __name__ == "__main__":
    unittest.main()
