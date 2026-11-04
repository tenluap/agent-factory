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
        clean = base(analyze=analysis(result=counts(report="factory/analyze-1.md")))
        self.assertIsNone(checks.gate_violation(clean, "implement"))
        remediated = base(
            analyze=analysis(
                baseline=counts(medium=6, low=6),
                result=counts(medium=3, low=2, report="factory/analyze-2.md"),
                reports=("factory/analyze-1.md", "factory/analyze-2.md"),
                pass_=2,
                loops=1,
            )
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


def counts(
    critical=0,
    high=0,
    medium=0,
    low=0,
    report="factory/analyze-1.md",
    at="2026-11-04T00:00:00Z",
):
    return {
        "critical": critical,
        "high": high,
        "medium": medium,
        "low": low,
        "report": report,
        "at": at,
    }


def analysis(baseline=None, result=None, reports=("factory/analyze-1.md",), **kw):
    loops = kw.pop("loops", 0)
    pass_ = kw.pop("pass_", 1)
    record = {
        "pass": pass_,
        "loops": loops,
        "reports": list(reports),
        "remediations": [],
        "pending_clarify": [],
    }
    if baseline is not None:
        record["baseline"] = baseline
    if result is not None:
        record["result"] = result
    return record


def answered_relay(qid, answered):
    answers = {qid: {"answer": "yes", "at": "2026-11-04T00:05:00Z"}} if answered else {}
    question = {"id": qid, "requires_user": True}
    return {"stage": "analyze", "rounds": [{"questions": [question], "answers": answers}]}


class AcceptanceTargetTests(unittest.TestCase):
    """The implement gate compares latest with baseline (FR-004..FR-008, ADR 0016)."""

    def gate(self, baseline, latest, **kw):
        s = base(analyze=analysis(baseline=baseline, result=latest, **kw))
        return checks.gate_violation(s, "implement")

    def test_half_rule_allows_below_half_and_refuses_exactly_half(self):
        baseline = counts(medium=6, low=6)
        self.assertIsNone(self.gate(baseline, counts(medium=3, low=2)))
        reason = self.gate(baseline, counts(medium=4, low=2))
        self.assertIn("total 6 (baseline 12, must be < 6)", reason)
        self.assertNotIn("LOW", reason)

    def test_low_exactly_half_is_refused(self):
        reason = self.gate(counts(medium=0, low=6), counts(low=3))
        self.assertIn("LOW 3 (baseline 6, must be < 3)", reason)

    def test_odd_baseline_seven_allows_three_and_refuses_four(self):
        baseline = counts(medium=7)
        self.assertIsNone(self.gate(baseline, counts(medium=3)))
        reason = self.gate(baseline, counts(medium=4))
        self.assertIn("total 4 (baseline 7, must be < 3.5)", reason)

    def test_zero_baseline_must_stay_zero(self):
        reason = self.gate(counts(), counts(low=1))
        self.assertIn("LOW 1 (baseline 0, must stay 0)", reason)
        self.assertIsNone(self.gate(counts(), counts()))

    def test_critical_must_be_zero(self):
        reason = self.gate(counts(medium=6, low=6), counts(critical=1, medium=3, low=2))
        self.assertIn("CRITICAL 1 (must be 0)", reason)

    def test_new_high_on_clean_baseline_is_refused(self):
        reason = self.gate(counts(), counts(high=1))
        self.assertIn("HIGH 1 (must be 0)", reason)

    def test_every_unmet_target_is_named_in_one_refusal(self):
        reason = self.gate(counts(medium=6, low=6), counts(critical=1, medium=2, low=3))
        self.assertEqual(
            reason.split("; "),
            [
                "CRITICAL 1 (must be 0)",
                "total 6 (baseline 12, must be < 6)",
                "LOW 3 (baseline 6, must be < 3)",
            ],
        )

    def test_latest_equal_to_a_non_clean_baseline_is_refused(self):
        reason = self.gate(counts(medium=2), counts(medium=2))
        self.assertIn("total 2 (baseline 2, must be < 1)", reason)

    def test_zero_findings_against_a_clean_baseline_allows(self):
        self.assertIsNone(self.gate(counts(), counts()))

    def test_pending_clarify_refuses_with_targets_met(self):
        s = base(analyze=analysis(baseline=counts(medium=6, low=6), result=counts(medium=1)))
        s["analyze"]["pending_clarify"] = [{"id": "Q9"}]
        reason = checks.gate_violation(s, "implement")
        self.assertIn("pending_clarify", reason)

    def test_unanswered_requires_user_question_refuses_by_id(self):
        s = base(analyze=analysis(baseline=counts(medium=6, low=6), result=counts(medium=1)))
        s["relay"] = answered_relay("Q7", answered=False)
        self.assertIn("Q7", checks.gate_violation(s, "implement"))
        s["relay"] = answered_relay("Q7", answered=True)
        self.assertIsNone(checks.gate_violation(s, "implement"))

    def test_derives_the_baseline_from_one_named_report(self):
        clean = base(analyze=analysis(result=counts()))
        self.assertIsNone(checks.gate_violation(clean, "implement"))
        dirty = base(analyze=analysis(result=counts(medium=2)))
        self.assertIn("total 2 (baseline 2, must be < 1)", checks.gate_violation(dirty, "implement"))

    def test_several_reports_without_a_baseline_have_no_trustworthy_baseline(self):
        s = base(
            analyze=analysis(
                result=counts(report="factory/analyze-2.md"),
                reports=("factory/analyze-1.md", "factory/analyze-2.md"),
            )
        )
        reason = checks.gate_violation(s, "implement")
        self.assertIn("no trustworthy baseline", reason)
        self.assertIn("gate-override", reason)

    def test_result_naming_another_report_has_no_trustworthy_baseline(self):
        s = base(analyze=analysis(result=counts(report="factory/analyze-2.md")))
        self.assertIn("no trustworthy baseline", checks.gate_violation(s, "implement"))

    def test_stored_baseline_is_used_when_valid(self):
        s = base(analyze=analysis(baseline=counts(medium=6, low=6), result=counts(medium=1)))
        self.assertIsNone(checks.gate_violation(s, "implement"))

    def test_zero_reports_still_refuses_with_the_existing_reason(self):
        s = base(analyze=analysis(reports=()))
        self.assertIn("analyze.reports is empty", checks.gate_violation(s, "implement"))


class RemediateGateTests(unittest.TestCase):
    """The repair-cycle cap (FR-014, FR-016): a gate into `remediate` at two loops."""

    RESULT_AT = "2026-11-04T00:30:00Z"

    def state_at(self, loops, *answers):
        s = base(
            stage="analyze",
            analyze=analysis(
                baseline=counts(medium=6, low=6),
                result=counts(medium=4, at=self.RESULT_AT),
                loops=loops,
            ),
        )
        s["decisions"] = list(answers)
        return s

    def answer(self, at, auto=False):
        return {
            "stage": "analyze",
            "question": "Q9",
            "answer": "guided pass",
            "auto": auto,
            "at": at,
            "kind": "answer",
        }

    def test_loops_below_the_cap_allow_a_repair_cycle(self):
        self.assertIsNone(checks.gate_violation(self.state_at(0), "remediate"))
        self.assertIsNone(checks.gate_violation(self.state_at(1), "remediate"))

    def test_the_cap_refuses_without_a_decision_and_names_the_three_choices(self):
        reason = checks.gate_violation(self.state_at(2), "remediate")
        self.assertIsNotNone(reason)
        self.assertIn("2", reason)
        for choice in ("guided pass", "gate-override", "abort"):
            self.assertIn(choice, reason)

    def test_an_auto_answer_newer_than_the_result_refuses(self):
        s = self.state_at(2, self.answer("2026-11-04T00:40:00Z", auto=True))
        self.assertIsNotNone(checks.gate_violation(s, "remediate"))

    def test_a_non_auto_answer_older_than_the_result_refuses(self):
        s = self.state_at(2, self.answer("2026-11-04T00:10:00Z"))
        self.assertIsNotNone(checks.gate_violation(s, "remediate"))

    def test_a_non_auto_answer_newer_than_the_result_allows(self):
        s = self.state_at(2, self.answer("2026-11-04T00:40:00Z"))
        self.assertIsNone(checks.gate_violation(s, "remediate"))


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
