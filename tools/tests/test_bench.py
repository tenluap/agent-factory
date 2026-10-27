"""Benchmark score/compare public CLI seams; no live harness or token cost."""

import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

from tests import FIXTURES, REPO_ROOT, Sandbox


def bench(*args):
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "tools" / "bench.py"), *map(str, args)],
        capture_output=True,
        text=True,
    )


class ScoreTests(unittest.TestCase):
    def test_emits_all_metrics_and_pass_conditions_offline(self):
        out = bench("score", FIXTURES / "bench-pass" / "state.json")
        self.assertEqual(out.returncode, 0, out.stderr)
        body = json.loads(out.stdout)
        self.assertEqual(body["bench"], "greet-001")
        score = body["scores"][0]
        self.assertEqual(score["run"], "001-greet")
        self.assertEqual(
            score["metrics"],
            {
                "wall_ms": 600000,
                "agent_ms": 240000,
                "human_ms": 60000,
                "spawns": 2,
                "overruns": 1,
                "issues_by_kind": {
                    "overrun": 1,
                    "agent-failure": 0,
                    "retry": 0,
                    "halt": 0,
                    "verify-fail": 0,
                },
                "tokens": {
                    "in_est": 300,
                    "out_est": 50,
                    "reported": [{"input_tokens": 220, "output_tokens": 40}],
                },
                "review_rounds": 2,
                "fix_rounds": 1,
            },
        )
        self.assertTrue(score["pass"])
        self.assertEqual(
            set(score["conditions"]),
            {
                "reached-approver",
                "last-verify-green",
                "no-blocking-findings",
                "fixture-acceptance",
            },
        )
        self.assertTrue(all(c["met"] for c in score["conditions"].values()))

    def test_latest_failed_verify_does_not_reuse_earlier_acceptance(self):
        out = bench("score", FIXTURES / "bench-fail" / "state.json")
        self.assertEqual(out.returncode, 0, out.stderr)
        score = json.loads(out.stdout)["scores"][0]
        self.assertFalse(score["pass"])
        for name, condition in score["conditions"].items():
            self.assertFalse(condition["met"], name)
            self.assertTrue(condition["detail"], name)

    def test_acceptance_supports_writer_exit_status_zero(self):
        box = Sandbox()
        self.addCleanup(box.close)
        folder = box.dir / "recorded"
        shutil.copytree(FIXTURES / "bench-pass", folder)
        path = folder / "state.json"
        loaded = json.loads(path.read_text())
        loaded["history"][-1]["commands"][0]["status"] = 0
        path.write_text(json.dumps(loaded))
        out = bench("score", path)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertTrue(json.loads(out.stdout)["scores"][0]["pass"])

    def test_missing_or_malformed_state_and_missing_verdict_never_raise(self):
        box = Sandbox()
        self.addCleanup(box.close)
        malformed = box.write_temp("malformed.json", '{"ledger": [false]}')
        missing_verdict = box.dir / "state.json"
        shutil.copyfile(FIXTURES / "bench-pass" / "state.json", missing_verdict)
        out = bench("score", box.dir / "absent.json", malformed, missing_verdict)
        self.assertEqual(out.returncode, 0, out.stderr)
        scores = json.loads(out.stdout)["scores"]
        self.assertEqual(len(scores), 3)
        self.assertTrue(all(not s["pass"] for s in scores))
        self.assertFalse(scores[2]["conditions"]["no-blocking-findings"]["met"])

    def test_latest_round_is_numeric_and_blocking_verdict_fails(self):
        box = Sandbox()
        self.addCleanup(box.close)
        folder = box.dir / "recorded"
        shutil.copytree(FIXTURES / "bench-pass", folder)
        newest = folder / "reviews" / "round-10"
        newest.mkdir()
        (newest / "verdict.json").write_text(
            json.dumps(
                {
                    "verdict": "pass",
                    "confirmed_blocking": [{"id": "F1"}],
                }
            )
        )
        out = bench("score", folder / "state.json")
        self.assertEqual(out.returncode, 0, out.stderr)
        score = json.loads(out.stdout)["scores"][0]
        self.assertFalse(score["conditions"]["no-blocking-findings"]["met"])
        self.assertIn("round-10", score["conditions"]["no-blocking-findings"]["detail"])

    def test_compare_prints_each_metric_delta_and_pass_transition(self):
        box = Sandbox()
        self.addCleanup(box.close)
        a = bench("score", FIXTURES / "bench-pass" / "state.json")
        b = bench("score", FIXTURES / "bench-fail" / "state.json")
        a_path = box.write_temp("a.json", a.stdout)
        b_path = box.write_temp("b.json", b.stdout)
        out = bench("compare", a_path, b_path)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("agent_ms: 240000 -> 0 (-240000)", out.stdout)
        self.assertIn("tokens.in_est: 300 -> 0 (-300)", out.stdout)
        self.assertIn("issues_by_kind.verify-fail: 0 -> 1 (+1)", out.stdout)
        self.assertIn("pass: true -> false", out.stdout)
        for metric in (
            "wall_ms",
            "human_ms",
            "spawns",
            "overruns",
            "review_rounds",
            "fix_rounds",
            "tokens.reported",
        ):
            self.assertIn(f"{metric}:", out.stdout)
