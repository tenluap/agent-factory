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

from factory_cli import checks, state  # noqa: E402
from tests import Sandbox, fixture  # noqa: E402


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


class ModeCommandTests(unittest.TestCase):
    """Seam: `bin/factory mode [flags...]` (FR-001..FR-003). Read-only."""

    def setUp(self):
        self.sb = Sandbox()

    def tearDown(self):
        self.sb.close()

    def mode(self, *flags):
        return self.sb.cli("mode", *flags)

    def test_no_flags_prints_the_default_mode(self):
        out = self.mode()
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(json.loads(out.stdout), {"chain": "lite", "fast": True, "cruise": False})

    def test_cruise_gives_fast_and_cruise(self):
        out = self.mode("--cruise")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(json.loads(out.stdout), {"chain": "lite", "fast": True, "cruise": True})

    def test_pairs_resolve_last_wins(self):
        cases = {
            ("--no-fast", "--cruise", "--no-cruise"): {"chain": "lite", "fast": False, "cruise": False},
            ("--cruise", "--no-cruise"): {"chain": "lite", "fast": True, "cruise": False},
            ("--no-cruise", "--cruise"): {"chain": "lite", "fast": True, "cruise": True},
            ("--no-cruise",): {"chain": "lite", "fast": True, "cruise": False},
        }
        for flags, expected in cases.items():
            out = self.mode(*flags)
            self.assertEqual(out.returncode, 0, (flags, out.stderr))
            self.assertEqual(json.loads(out.stdout), expected, flags)

    def test_chain_flags_set_the_chain(self):
        self.assertEqual(json.loads(self.mode("--full").stdout)["chain"], "full")
        self.assertEqual(json.loads(self.mode("--full", "--lite").stdout)["chain"], "lite")

    def test_cruise_with_no_fast_conflicts_in_either_order(self):
        for flags in (
            ("--cruise", "--no-fast"),
            ("--no-fast", "--cruise"),
            ("--no-fast", "--fast", "--cruise"),
        ):
            out = self.mode(*flags)
            self.assertEqual(out.returncode, 5, flags)
            self.assertIn("--cruise", out.stderr, flags)
            self.assertIn("--no-fast", out.stderr, flags)

    def test_unknown_flag_exits_five(self):
        self.assertEqual(self.mode("--bogus").returncode, 5)

    def test_mode_writes_nothing(self):
        head = self.sb.git("rev-parse", "HEAD").strip()
        pending = sorted((self.sb.home / "pending").iterdir())
        self.mode("--cruise")
        self.mode("--cruise", "--no-fast")
        self.assertEqual(self.sb.git("rev-parse", "HEAD").strip(), head)
        self.assertEqual(sorted((self.sb.home / "pending").iterdir()), pending)


class ResumeModeTests(unittest.TestCase):
    """Seam: `bin/factory resume <run> [mode flags]` (FR-004, FR-005, US4)."""

    BRANCH = "021-resume-run"

    def setUp(self):
        self.box = Sandbox()
        halted = fixture("state-v5.json")
        halted.update(status="halted", halt_reason="stopped for test", stage="implement")
        halted["mode"] = {"chain": "full", "fast": True}
        self.wt = self.box.worktree_run(self.BRANCH, halted)

    def tearDown(self):
        self.box.close()

    def state(self):
        return json.loads((self.wt / "specs" / self.BRANCH / "factory" / "state.json").read_text())

    def store(self, mode):
        def mutate(s):
            s["mode"] = mode

        path = self.wt / "specs" / self.BRANCH / "factory" / "state.json"
        loaded = json.loads(path.read_text())
        mutate(loaded)
        path.write_text(json.dumps(loaded, indent=2) + "\n")
        self.box.git("add", "-A", cwd=self.wt)
        self.box.git("commit", "-q", "-m", "test: stored mode", cwd=self.wt)

    def snapshot(self):
        path = self.wt / "specs" / self.BRANCH / "factory" / "state.json"
        return (
            path.read_bytes(),
            self.box.git("rev-parse", "HEAD", cwd=self.wt).strip(),
            len(self.state()["history"]),
        )

    def test_resume_with_cruise_stores_mode_and_one_resumed_entry(self):
        before = len(self.state()["history"])
        head = self.box.git("rev-parse", "HEAD", cwd=self.wt).strip()
        out = self.box.cli("resume", self.BRANCH, "--cruise")
        self.assertEqual(out.returncode, 0, out.stderr)
        loaded = self.state()
        self.assertEqual(loaded["mode"], {"chain": "full", "fast": True, "cruise": True})
        self.assertEqual(len(loaded["history"]), before + 1)
        self.assertEqual(loaded["history"][-1]["event"], "resumed")
        self.assertNotEqual(self.box.git("rev-parse", "HEAD", cwd=self.wt).strip(), head)

    def test_state_without_cruise_resumes_as_off_and_stays_valid(self):
        out = self.box.cli("resume", self.BRANCH)
        self.assertEqual(out.returncode, 0, out.stderr)
        loaded = self.state()
        self.assertFalse(loaded["mode"].get("cruise", False))
        self.assertEqual(state.validate_state(loaded), [])

    def test_no_cruise_on_a_cruise_run_keeps_fast(self):
        self.store({"chain": "full", "fast": True, "cruise": True})
        out = self.box.cli("resume", self.BRANCH, "--no-cruise")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(self.state()["mode"], {"chain": "full", "fast": True, "cruise": False})

    def test_no_cruise_and_no_fast_on_a_cruise_run_turns_both_off(self):
        self.store({"chain": "full", "fast": True, "cruise": True})
        out = self.box.cli("resume", self.BRANCH, "--no-cruise", "--no-fast")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(self.state()["mode"], {"chain": "full", "fast": False, "cruise": False})

    def test_cruise_with_no_fast_is_refused_and_writes_nothing(self):
        before = self.snapshot()
        out = self.box.cli("resume", self.BRANCH, "--cruise", "--no-fast")
        self.assertEqual(out.returncode, 5, out.stderr)
        self.assertEqual(self.snapshot(), before)

    def test_no_fast_on_a_stored_cruise_run_is_refused_and_writes_nothing(self):
        self.store({"chain": "full", "fast": True, "cruise": True})
        before = self.snapshot()
        out = self.box.cli("resume", self.BRANCH, "--no-fast")
        self.assertEqual(out.returncode, 5, out.stderr)
        self.assertEqual(self.snapshot(), before)


class AnswerCruiseOverrideTests(unittest.TestCase):
    """Seam: `bin/factory answer <qid> <answer> --cruise-override` (FR-008, FR-009)."""

    BRANCH = "021-answer-run"

    def relay_state(self, cruise):
        loaded = fixture("state-v5.json")
        loaded.update(status="running", stage="grill")
        loaded["mode"] = {"chain": "full", "fast": True, "cruise": cruise}
        loaded["relay"] = {
            "stage": "grill",
            "rounds": [
                {
                    "questions": [
                        {"id": "Q1", "text": "Pick", "requires_user": True, "recommended": "A"}
                    ],
                    "answers": {},
                }
            ],
        }
        return loaded

    def setUp(self):
        self.box = Sandbox()

    def tearDown(self):
        self.box.close()

    def stored(self, wt):
        return json.loads((wt / "specs" / self.BRANCH / "factory" / "state.json").read_text())

    def test_marked_answer_is_stored_with_auto_and_marker(self):
        wt = self.box.worktree_run(self.BRANCH, self.relay_state(cruise=True))
        out = self.box.cli("answer", "Q1", "A", "--cruise-override", cwd=wt)
        self.assertEqual(out.returncode, 0, out.stderr)
        answer = self.stored(wt)["relay"]["rounds"][-1]["answers"]["Q1"]
        self.assertEqual(answer["answer"], "A")
        self.assertIs(answer["auto"], True)
        self.assertIs(answer["cruise_override"], True)

    def test_ordinary_auto_answer_carries_no_marker(self):
        wt = self.box.worktree_run(self.BRANCH, self.relay_state(cruise=True))
        out = self.box.cli("answer", "Q1", "A", "--auto", cwd=wt)
        self.assertEqual(out.returncode, 0, out.stderr)
        answer = self.stored(wt)["relay"]["rounds"][-1]["answers"]["Q1"]
        self.assertNotIn("cruise_override", answer)

    def test_marker_on_a_run_without_cruise_is_refused_and_writes_nothing(self):
        for cruise in (False, None):
            loaded = self.relay_state(cruise=False)
            if cruise is None:
                loaded["mode"].pop("cruise")
            branch = f"{self.BRANCH}-{cruise}"
            wt = self.box.worktree_run(branch, loaded)
            path = wt / "specs" / branch / "factory" / "state.json"
            before = path.read_bytes()
            head = self.box.git("rev-parse", "HEAD", cwd=wt).strip()
            out = self.box.cli("answer", "Q1", "A", "--cruise-override", cwd=wt)
            self.assertEqual(out.returncode, 1, (cruise, out.stderr))
            self.assertIn("cruise", out.stderr)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(self.box.git("rev-parse", "HEAD", cwd=wt).strip(), head)

    def test_checkpoint_migrates_marked_answer_and_show_lists_it(self):
        wt = self.box.worktree_run(self.BRANCH, self.relay_state(cruise=True))
        out = self.box.cli("answer", "Q1", "A", "--cruise-override", cwd=wt)
        self.assertEqual(out.returncode, 0, out.stderr)
        out = self.box.cli("checkpoint", "grill", "--next", "plan", cwd=wt)
        self.assertEqual(out.returncode, 0, out.stderr)
        migrated = [d for d in self.stored(wt)["decisions"] if "cruise_override" in d]
        self.assertEqual(len(migrated), 1, migrated)
        self.assertEqual(migrated[0]["question"], "Q1")
        self.assertEqual(migrated[0]["kind"], "answer")
        self.assertIs(migrated[0]["auto"], True)
        self.assertIs(migrated[0]["cruise_override"], True)
        out = self.box.cli("show", self.BRANCH, cwd=wt)
        self.assertEqual(out.returncode, 0, out.stderr)
        veto = json.loads(out.stdout)["decisions"]
        self.assertIn(
            ("Q1", True),
            [(d.get("question"), d.get("cruise_override")) for d in veto],
        )


class DecisionsAddCruiseOverrideTests(unittest.TestCase):
    """Seam: `bin/factory decisions-add ... --cruise-override` (FR-010, FR-011)."""

    BRANCH = "021-decisions-run"

    def setUp(self):
        self.box = Sandbox()

    def tearDown(self):
        self.box.close()

    def run_state(self, cruise):
        loaded = fixture("state-v5.json")
        loaded.update(status="running", stage="grill")
        loaded["mode"] = {"chain": "full", "fast": True, "cruise": cruise}
        return loaded

    def paths(self, wt, branch):
        return wt / "specs" / branch / "factory" / "state.json"

    def test_marked_answer_is_recorded_as_auto_with_marker(self):
        wt = self.box.worktree_run(self.BRANCH, self.run_state(cruise=True))
        out = self.box.cli(
            "decisions-add", "grill", "intake", "delivery", "--cruise-override", cwd=wt
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        record = json.loads(self.paths(wt, self.BRANCH).read_text())["decisions"][-1]
        self.assertEqual(record["kind"], "answer")
        self.assertIs(record["auto"], True)
        self.assertIs(record["cruise_override"], True)
        self.assertEqual(state.validate_state(json.loads(self.paths(wt, self.BRANCH).read_text())), [])

    def test_marked_analyze_exhaustion_gate_override_is_recorded_and_valid(self):
        wt = self.box.worktree_run(self.BRANCH, self.run_state(cruise=True))
        out = self.box.cli(
            "decisions-add", "analyze", "analyze-exhaustion", "proceed to implement",
            "--kind", "gate-override", "--cruise-override", cwd=wt,
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        loaded = json.loads(self.paths(wt, self.BRANCH).read_text())
        record = loaded["decisions"][-1]
        self.assertEqual(record["kind"], "gate-override")
        self.assertIs(record["cruise_override"], True)
        self.assertEqual(state.validate_state(loaded), [])

    def test_marked_analyze_exhaustion_lets_checkpoint_enter_implement(self):
        loaded = self.run_state(cruise=True)
        loaded["stage"] = "analyze"
        wt = self.box.worktree_run(self.BRANCH, loaded)
        out = self.box.cli(
            "decisions-add", "analyze", "analyze-exhaustion", "proceed to implement",
            "--kind", "gate-override", "--cruise-override", cwd=wt,
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        out = self.box.cli("checkpoint", "analyze", "--next", "implement", cwd=wt)
        self.assertEqual(out.returncode, 0, out.stderr)
        stored = json.loads(self.paths(wt, self.BRANCH).read_text())
        self.assertEqual(stored["stage"], "implement")
        self.assertEqual(stored["history"][-1]["event"], "gate-override")

    def test_without_the_flag_decisions_add_is_unchanged(self):
        wt = self.box.worktree_run(self.BRANCH, self.run_state(cruise=True))
        out = self.box.cli("decisions-add", "grill", "intake", "delivery", cwd=wt)
        self.assertEqual(out.returncode, 0, out.stderr)
        record = json.loads(self.paths(wt, self.BRANCH).read_text())["decisions"][-1]
        self.assertIs(record["auto"], False)
        self.assertNotIn("cruise_override", record)

    def assert_refused(self, wt, args, cruise_state):
        path = self.paths(wt, self.BRANCH)
        before = path.read_bytes()
        head = self.box.git("rev-parse", "HEAD", cwd=wt).strip()
        out = self.box.cli("decisions-add", *args, cwd=wt)
        self.assertEqual(out.returncode, 1, (args, out.stderr))
        self.assertTrue(out.stderr.strip(), args)
        self.assertEqual(path.read_bytes(), before, args)
        self.assertEqual(self.box.git("rev-parse", "HEAD", cwd=wt).strip(), head, args)

    def test_marker_without_cruise_mode_is_refused(self):
        wt = self.box.worktree_run(self.BRANCH, self.run_state(cruise=False))
        self.assert_refused(wt, ("grill", "intake", "delivery", "--cruise-override"), False)

    def test_marker_with_approved_kind_is_refused(self):
        wt = self.box.worktree_run(self.BRANCH, self.run_state(cruise=True))
        self.assert_refused(
            wt, ("approver", "approve", "approved", "--kind", "approved", "--cruise-override"), True
        )

    def test_marked_gate_override_outside_analyze_is_refused(self):
        wt = self.box.worktree_run(self.BRANCH, self.run_state(cruise=True))
        self.assert_refused(
            wt,
            ("plan", "analyze-exhaustion", "proceed", "--kind", "gate-override", "--cruise-override"),
            True,
        )


class PrGateTests(unittest.TestCase):
    """Seam: `factory_cli.checks.gate_violation` into `pr` (FR-015, FR-016).

    Hand-built dicts bypass validate_state, so a forged record is reachable."""

    def run_with(self, *records):
        loaded = fixture("state-v5.json")
        loaded["decisions"] = list(records)
        return loaded

    def approver(self, kind, **extra):
        record = {
            "stage": "approver",
            "question": "approve",
            "answer": "yes",
            "auto": False,
            "at": "2026-11-04T01:00:00Z",
            "kind": kind,
        }
        record.update(extra)
        return record

    def test_user_approval_permits_pr(self):
        s = self.run_with(self.approver("approved"))
        self.assertIsNone(checks.gate_violation(s, "pr"))

    def test_forged_cruise_approval_never_permits_pr(self):
        s = self.run_with(self.approver("approved", cruise_override=True, auto=True))
        self.assertIsNotNone(checks.gate_violation(s, "pr"))

    def test_forged_cruise_gate_override_at_approver_never_permits_pr(self):
        s = self.run_with(self.approver("gate-override", cruise_override=True, auto=True))
        self.assertIsNotNone(checks.gate_violation(s, "pr"))

    def test_marked_record_does_not_hide_a_real_approval(self):
        s = self.run_with(
            self.approver("approved", cruise_override=True, auto=True),
            self.approver("approved"),
        )
        self.assertIsNone(checks.gate_violation(s, "pr"))


if __name__ == "__main__":
    unittest.main()
