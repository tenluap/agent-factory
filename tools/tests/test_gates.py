"""Gate seam tests: `factory_cli.checks` transition rules (FR-006, SC-005).

One refusal per illegal transition, one pass per legal one, each refusal
naming the missing record; the accepting side records its decision and the
permitted transition carries the `approved`/`gate-override` history event.
"""

import json
import sys
import unittest
from pathlib import Path

CORE_BIN = Path(__file__).resolve().parents[2] / "core" / "skills" / "factory" / "bin"
sys.path.insert(0, str(CORE_BIN))

from factory_cli import checks  # noqa: E402
from tests import Sandbox, fixture  # noqa: E402


def base(stage="implement", **overrides):
    s = fixture("state-v4.json")
    s.update(stage=stage, status="running", **overrides)
    s["history"] = [h for h in s["history"] if h["event"] == "complete"]
    s["decisions"] = [
        d
        for d in s.get("decisions") or []
        if d.get("kind") not in ("approved", "gate-override")
    ]
    return s


def decision(stage, kind="approved", question="Q1", at="2026-10-23T10:00:00Z"):
    return {
        "stage": stage,
        "question": question,
        "answer": "because",
        "auto": False,
        "at": at,
        "kind": kind,
    }


def verify(event):
    return {
        "at": "2026-10-23T09:00:00Z",
        "stage": "implement",
        "event": event,
        "commit": None,
        "harness": "opencode",
        "commands": [
            {"command": "make test", "status": 0 if event == "verify-pass" else 1}
        ],
    }


class ReviewGateTests(unittest.TestCase):
    def test_refuses_without_any_verify_record(self):
        reason = checks.gate_violation(base(stage="review"), "review")
        self.assertIsNotNone(reason)
        self.assertIn("verify", reason.lower())

    def test_refuses_when_the_latest_verify_record_failed(self):
        s = base(stage="review")
        s["history"] += [verify("verify-fail")]
        reason = checks.gate_violation(s, "review")
        self.assertIsNotNone(reason)
        self.assertIn("verify-fail", reason)

    def test_the_latest_verify_record_decides(self):
        s = base(stage="review")
        s["history"] += [verify("verify-fail"), verify("verify-pass")]
        self.assertIsNone(checks.gate_violation(s, "review"))
        s["history"] += [verify("verify-fail")]
        self.assertIsNotNone(checks.gate_violation(s, "review"))

    def test_latest_pass_record_requires_passing_command_statuses(self):
        s = base(stage="review")
        latest = verify("verify-pass")
        s["history"] += [verify("verify-pass"), latest]
        latest["commands"].append({"command": "make build", "status": "pass"})
        self.assertIsNone(checks.gate_violation(s, "review"))
        latest["commands"][1]["status"] = 1
        self.assertIsNotNone(checks.gate_violation(s, "review"))


class ImplementGateTests(unittest.TestCase):
    def test_refuses_when_analyze_never_reported(self):
        s = base(
            analyze={
                "pass": 0,
                "loops": 0,
                "reports": [],
                "remediations": [],
                "pending_clarify": [],
            }
        )
        reason = checks.gate_violation(s, "implement")
        self.assertIsNotNone(reason)
        self.assertIn("analyze", reason.lower())

    def test_refuses_with_pending_clarify(self):
        s = base(
            analyze={
                "pass": 1,
                "loops": 0,
                "reports": ["factory/analyze-1.md"],
                "remediations": [],
                "pending_clarify": [{"id": "Q1"}],
            }
        )
        self.assertIsNotNone(checks.gate_violation(s, "implement"))

    def test_passes_clean_remediated_or_overridden(self):
        clean = base()
        self.assertIsNone(checks.gate_violation(clean, "implement"))
        remediated = base(
            analyze={
                "pass": 2,
                "loops": 1,
                "reports": ["factory/analyze-1.md"],
                "remediations": ["factory/remediation-1.md"],
                "pending_clarify": [],
            }
        )
        self.assertIsNone(checks.gate_violation(remediated, "implement"))
        overridden = base(
            analyze={
                "pass": 2,
                "loops": 2,
                "reports": ["factory/analyze-1.md"],
                "remediations": ["factory/remediation-1.md"],
                "pending_clarify": [],
            }
        )
        overridden["decisions"] = [
            decision("analyze", kind="gate-override", question="Q9")
        ]
        self.assertIsNone(checks.gate_violation(overridden, "implement"))


class PrGateTests(unittest.TestCase):
    def test_refuses_without_a_recorded_approval(self):
        reason = checks.gate_violation(base(stage="approver"), "pr")
        self.assertIsNotNone(reason)
        self.assertIn("approver", reason)

    def test_passes_with_an_approved_decision_at_approver(self):
        s = base(stage="approver")
        s["decisions"] = [decision("approver", kind="approved")]
        self.assertIsNone(checks.gate_violation(s, "pr"))

    def test_passes_with_a_gate_override_at_approver(self):
        s = base(stage="approver")
        s["decisions"] = [decision("approver", kind="gate-override", question="Q5")]
        self.assertIsNone(checks.gate_violation(s, "pr"))

    def test_an_approval_at_another_stage_does_not_satisfy_the_pr_gate(self):
        s = base(stage="approver")
        s["decisions"] = [decision("review", kind="approved")]
        self.assertIsNotNone(checks.gate_violation(s, "pr"))


class UngatedTransitionsPass(unittest.TestCase):
    def test_stages_without_a_gate_need_no_records(self):
        for into in (
            "worktree",
            "specify",
            "plan",
            "tasks",
            "analyze",
            "remediate",
            "verify",
            "fix",
            "approver",
        ):
            self.assertIsNone(checks.gate_violation(base(stage="review"), into), into)


class AcceptingSideCliTests(unittest.TestCase):
    """decisions-add feeds the gates; the permitted transition records the event."""

    def setUp(self):
        self.box = Sandbox()
        self.addCleanup(self.box.close)
        self.branch = "070-gates"
        self.wt = self.box.worktree_run(self.branch, fixture("state-v4.json"))
        self.state_path = self.wt / "specs" / self.branch / "factory" / "state.json"

    def load(self):
        return json.loads(self.state_path.read_text())

    def test_verify_pass_refuses_a_failed_command_without_writing(self):
        before = self.load()
        head = self.box.git("rev-parse", "HEAD", cwd=self.wt)
        out = self.box.cli(
            "verify",
            "--pass",
            "--commands",
            json.dumps(
                [
                    {"command": "make build", "status": 0},
                    {"command": "make test", "status": 1},
                ]
            ),
            cwd=self.wt,
        )
        self.assertNotEqual(out.returncode, 0, out.stdout)
        self.assertIn("passing", out.stderr)
        self.assertEqual(self.load(), before)
        self.assertEqual(self.box.git("rev-parse", "HEAD", cwd=self.wt), head)

    def test_approval_satisfies_pr_gate_and_history_carries_the_decision(self):
        out = self.box.cli(
            "decisions-add",
            "approver",
            "Q1",
            "Approve",
            "--kind",
            "approved",
            cwd=self.wt,
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        out = self.box.cli("checkpoint", "approver", cwd=self.wt)  # approver -> pr
        self.assertEqual(out.returncode, 0, out.stderr)
        after = self.load()
        self.assertEqual(after["stage"], "pr")
        entry = after["history"][-1]
        self.assertEqual(
            (entry["event"], entry["decision"], entry["stage"]),
            ("approved", "Q1", "approver"),
        )

    def test_checkpoint_into_review_refuses_without_verify(self):
        s = self.load()
        s["stage"] = "implement"
        s["history"] = [h for h in s["history"] if not h["event"].startswith("verify-")]
        self.state_path.write_text(json.dumps(s, indent=2))
        out = self.box.cli("checkpoint", "implement", "--next", "review", cwd=self.wt)
        self.assertEqual(out.returncode, 1)
        self.assertIn("verify", out.stderr.lower())
        self.assertEqual(
            self.load()["stage"], "implement", "a refused checkpoint changes nothing"
        )

    def test_gate_override_permits_implement_and_history_carries_the_decision(self):
        s = self.load()
        s["stage"] = "analyze"
        s["analyze"] = {
            "pass": 2,
            "loops": 2,
            "reports": ["factory/analyze-1.md"],
            "remediations": ["factory/remediation-1.md"],
            "pending_clarify": [],
        }
        self.state_path.write_text(json.dumps(s, indent=2))
        self.box.cli(
            "decisions-add",
            "analyze",
            "Q9",
            "proceed with findings",
            "--kind",
            "gate-override",
            cwd=self.wt,
        )
        out = self.box.cli("checkpoint", "analyze", "--next", "implement", cwd=self.wt)
        self.assertEqual(out.returncode, 0, out.stderr)
        entry = self.load()["history"][-1]
        self.assertEqual((entry["event"], entry["decision"]), ("gate-override", "Q9"))


if __name__ == "__main__":
    unittest.main()
