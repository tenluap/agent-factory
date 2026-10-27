"""Budget seam tests: resolution order, deadline derivation, the
`factory budget <role>` read command (FR-001, FR-007); the ledger-add
overrun detection lives in the later tasks of this seam.
"""

import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

CORE_BIN = Path(__file__).resolve().parents[2] / "core" / "skills" / "factory" / "bin"
sys.path.insert(0, str(CORE_BIN))

from factory_cli import budget, state  # noqa: E402

from tests import Sandbox  # noqa: E402


class ResolutionTests(unittest.TestCase):
    def test_role_override_wins(self):
        config = {"budget": {"default_s": 120, "roles": {"code-build": 240}}}
        self.assertEqual(budget.resolve("code-build", config), 240)

    def test_default_when_the_role_has_no_entry(self):
        config = {"budget": {"default_s": 120, "roles": {"code-build": 240}}}
        self.assertEqual(budget.resolve("spec-builder", config), 120)

    def test_fallback_is_300_seconds(self):
        self.assertEqual(budget.resolve("code-build", {}), 300)
        self.assertEqual(budget.resolve("code-build", None), 300)

    def test_malformed_values_fall_back_per_entry(self):
        for bad in (0, -5, "240", 2.5, None, True):
            config = {"budget": {"roles": {"code-build": bad}, "default_s": 120}}
            self.assertEqual(budget.resolve("code-build", config), 120, repr(bad))
        self.assertEqual(
            budget.resolve("code-build", {"budget": {"default_s": "x", "roles": {}}}),
            300,
        )

    def test_budget_not_a_dict_never_fails(self):
        self.assertEqual(budget.resolve("code-build", {"budget": "nope"}), 300)

    def test_orchestrator_is_a_valid_role(self):
        config = {"budget": {"roles": {"orchestrator": 600}}}
        self.assertEqual(budget.resolve("orchestrator", config), 600)


class BudgetCommandTests(unittest.TestCase):
    def setUp(self):
        self.box = Sandbox()
        self.addCleanup(self.box.close)
        self.config = self.box.home / "config.json"

    def cli(self, *args):
        return self.box.cli("budget", *args)

    def test_reports_role_seconds_and_absolute_deadline(self):
        self.config.write_text(json.dumps({"budget": {"roles": {"code-build": 240}}}))
        out = self.cli("code-build")
        self.assertEqual(out.returncode, 0, out.stderr)
        body = json.loads(out.stdout)
        self.assertEqual(body["role"], "code-build")
        self.assertEqual(body["seconds"], 240)
        deadline = state.parse_iso(body["deadline"])
        self.assertIsNotNone(deadline, "deadline is an ISO-8601 UTC timestamp")
        now = datetime.now(timezone.utc)
        skew = abs((deadline - now).total_seconds() - 240)
        self.assertLess(skew, 5, "deadline is now + the role's seconds")

    def test_missing_or_malformed_config_never_fails(self):
        out = self.cli("code-build")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(json.loads(out.stdout)["seconds"], 300)
        self.config.write_text("{not json")
        out = self.cli("code-build")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(json.loads(out.stdout)["seconds"], 300)

    def test_orchestrator_budget_resolves(self):
        self.config.write_text(json.dumps({"budget": {"roles": {"orchestrator": 600}}}))
        out = self.cli("orchestrator")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(json.loads(out.stdout)["seconds"], 600)


if __name__ == "__main__":
    unittest.main()
