"""Analysis results must reach state through the CLI before implementation."""

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from tests import Sandbox, fixture

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core/skills/factory/bin"))
from factory_cli import commands


class AnalyzeRecordTests(unittest.TestCase):
    def setUp(self):
        self.box = Sandbox()
        self.addCleanup(self.box.close)
        self.branch = "095-analysis"
        state = fixture("state-v4.json")
        state.update(stage="analyze", relay=None)
        state["analyze"] = {
            "pass": 1,
            "loops": 0,
            "reports": [],
            "remediations": [],
            "pending_clarify": [],
        }
        self.wt = self.box.worktree_run(self.branch, state)
        self.spec = self.wt / "specs" / self.branch
        self.state_path = self.spec / "factory" / "state.json"
        self.report = self.spec / "factory" / "analyze-1.md"
        self.report.write_text("# Analysis\n\nNo findings.\n")
        self.envelope = {
            "status": "done",
            "stage": "analyze",
            "summary": "Clean",
            "files": [str(self.report.relative_to(self.wt))],
            "questions": [],
            "error": None,
            "analyze": {
                "report": "factory/analyze-1.md",
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
            },
        }

    def load(self):
        return json.loads(self.state_path.read_text())

    def record(self, envelope=None):
        path = self.box.write_temp(
            "analysis.json", json.dumps(envelope or self.envelope)
        )
        return self.box.cli("analyze-record", path, cwd=self.wt)

    def test_clean_result_unblocks_checkpoint_without_override(self):
        refused = self.box.cli(
            "checkpoint", "analyze", "--next", "implement", cwd=self.wt
        )
        self.assertEqual(refused.returncode, 1, refused.stderr)
        out = self.record()
        self.assertEqual(out.returncode, 0, out.stderr)
        saved = self.load()
        self.assertEqual(saved["analyze"]["reports"], ["factory/analyze-1.md"])
        self.assertEqual(saved["analyze"]["result"]["high"], 0)
        self.assertEqual(saved["stage"], "analyze")
        self.assertFalse(any(d["kind"] == "gate-override" for d in saved["decisions"]))
        out = self.box.cli("checkpoint", "analyze", "--next", "implement", cwd=self.wt)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(self.load()["stage"], "implement")
        self.assertEqual(self.box.git("status", "--porcelain", cwd=self.wt), "")

    def test_repository_relative_report_is_normalized_and_not_duplicated(self):
        self.envelope["analyze"]["report"] = str(self.report.relative_to(self.wt))
        self.assertEqual(self.record().returncode, 0)
        self.assertEqual(self.record().returncode, 0)
        self.assertEqual(self.load()["analyze"]["reports"], ["factory/analyze-1.md"])

    def test_unresolved_counts_and_pending_questions_still_block(self):
        self.envelope["analyze"]["high"] = 1
        out = self.record()
        self.assertEqual(out.returncode, 0, out.stderr)
        refused = self.box.cli(
            "checkpoint", "analyze", "--next", "implement", cwd=self.wt
        )
        self.assertEqual(refused.returncode, 1)
        self.assertIn("HIGH", refused.stderr)
        self.envelope["analyze"]["high"] = 0
        self.box.corrupt_worktree_state(
            self.branch,
            lambda s: s["analyze"].update(
                pending_clarify=[{"id": "Q9", "text": "Unsettled"}]
            ),
        )
        self.assertEqual(self.record().returncode, 0)
        self.assertEqual(self.load()["analyze"]["pending_clarify"][0]["id"], "Q9")
        refused = self.box.cli(
            "checkpoint", "analyze", "--next", "implement", cwd=self.wt
        )
        self.assertEqual(refused.returncode, 1)
        self.assertIn("pending_clarify", refused.stderr)

    def test_invalid_results_leave_state_and_head_unchanged(self):
        for field, value in (
            ("critical", -1),
            ("high", True),
            ("low", "0"),
            ("report", "../outside.md"),
            ("report", "factory/missing.md"),
        ):
            with self.subTest(field=field, value=value):
                envelope = json.loads(json.dumps(self.envelope))
                envelope["analyze"][field] = value
                before = self.state_path.read_bytes()
                head = self.box.git("rev-parse", "HEAD", cwd=self.wt)
                out = self.record(envelope)
                self.assertEqual(out.returncode, 1, out.stderr)
                self.assertEqual(self.state_path.read_bytes(), before)
                self.assertEqual(self.box.git("rev-parse", "HEAD", cwd=self.wt), head)

    def test_failed_or_wrong_stage_envelope_is_refused(self):
        for field, value in (
            ("status", "failed"),
            ("stage", "plan"),
            ("analyze", None),
        ):
            with self.subTest(field=field):
                envelope = dict(self.envelope, **{field: value})
                self.assertEqual(self.record(envelope).returncode, 1)

    def test_final_fenced_envelope_is_supported(self):
        path = self.box.write_temp(
            "analysis.md", "Result\n```json\n" + json.dumps(self.envelope) + "\n```\n"
        )
        out = self.box.cli("analyze-record", path, cwd=self.wt)
        self.assertEqual(out.returncode, 0, out.stderr)

    def test_symlink_to_external_report_is_refused(self):
        self.report.unlink()
        outside = self.box.write_temp("outside.md", "not run evidence")
        self.report.symlink_to(outside)
        out = self.record()
        self.assertEqual(out.returncode, 1, out.stderr)
        self.assertEqual(self.load()["analyze"]["reports"], [])

    def test_checkpoint_rechecks_gate_against_state_read_under_lock(self):
        self.assertEqual(self.record().returncode, 0)
        writer = commands.write_run

        def blocking_analysis_arrives(path, loaded, mutate):
            self.envelope["analyze"]["high"] = 1
            out = self.record()
            self.assertEqual(out.returncode, 0, out.stderr)
            return writer(path, loaded, mutate)

        with patch.object(commands, "write_run", side_effect=blocking_analysis_arrives):
            with self.assertRaisesRegex(commands.CLIError, "HIGH"):
                commands.cmd_checkpoint(
                    self.box.repo, self.wt, "analyze", next_stage="implement"
                )
        self.assertEqual(self.load()["stage"], "analyze")
        self.assertEqual(self.load()["analyze"]["result"]["high"], 1)
