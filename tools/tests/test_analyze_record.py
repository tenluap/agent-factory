"""Analysis results must reach state through the CLI before implementation."""

import hashlib
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from tests import Sandbox, fixture

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core/skills/factory/bin"))
from factory_cli import commands, state


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


class AnalyzeBaselineValidationTests(unittest.TestCase):
    """`validate_state` checks the shape of the stored `analyze.baseline` (FR-001)."""

    BASELINE = {
        "critical": 0,
        "high": 1,
        "medium": 4,
        "low": 2,
        "report": "factory/analyze-1.md",
        "at": "2026-11-04T00:10:00Z",
    }

    def with_baseline(self, **changes):
        s = fixture("state-v4.json")
        s["analyze"] = {
            "pass": 1,
            "loops": 0,
            "reports": ["factory/analyze-1.md"],
            "remediations": [],
            "pending_clarify": [],
            "baseline": {**self.BASELINE, **changes},
        }
        return s

    def locations(self, s):
        return [p["location"] for p in state.validate_state(s)]

    def test_valid_and_absent_baselines_validate(self):
        s = self.with_baseline()
        self.assertEqual(state.validate_state(s), [])
        del s["analyze"]["baseline"]
        self.assertEqual(state.validate_state(s), [])

    def test_negative_count_is_located_at_its_field(self):
        self.assertEqual(self.locations(self.with_baseline(high=-1)), ["analyze.baseline.high"])

    def test_missing_count_is_located_at_its_field(self):
        s = self.with_baseline()
        del s["analyze"]["baseline"]["low"]
        self.assertEqual(self.locations(s), ["analyze.baseline.low"])

    def test_non_integer_count_is_located_at_its_field(self):
        self.assertEqual(self.locations(self.with_baseline(medium="4")), ["analyze.baseline.medium"])
        self.assertEqual(self.locations(self.with_baseline(medium=4.0)), ["analyze.baseline.medium"])

    def test_bool_count_counts_as_non_integer(self):
        self.assertEqual(self.locations(self.with_baseline(critical=False)), ["analyze.baseline.critical"])

    def test_empty_report_is_located_at_report(self):
        self.assertEqual(self.locations(self.with_baseline(report="")), ["analyze.baseline.report"])


class AnalyzeBaselineRecordTests(unittest.TestCase):
    """`analyze-record` sets the baseline once and keeps it (FR-001..FR-003, FR-010, FR-012)."""

    def setUp(self):
        self.box = Sandbox()
        self.addCleanup(self.box.close)
        self.branch = "096-baseline"
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
        for name in ("analyze-1.md", "analyze-2.md", "analyze-1-full.md"):
            (self.spec / "factory" / name).write_text("# Analysis\n")

    def load(self):
        return json.loads(self.state_path.read_text())

    def record(self, report, fresh=False, **counts):
        block = {
            "status": "done",
            "stage": "analyze",
            "summary": "Analysis",
            "files": [],
            "questions": [],
            "error": None,
            "analyze": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                **counts,
                "report": report,
            },
        }
        path = self.box.write_temp(f"analysis-{report.replace('/', '_')}.json", json.dumps(block))
        args = ["analyze-record", path] + (["--fresh-baseline"] if fresh else [])
        return self.box.cli(*args, cwd=self.wt)

    def legacy_state(self, reports):
        """A pre-019 run: no baseline, `result` names the report when exactly one exists."""
        def mutate(s):
            s["analyze"] = {
                "pass": 1,
                "loops": 0,
                "reports": reports,
                "remediations": [],
                "pending_clarify": [],
                "result": {
                    "critical": 0,
                    "high": 0,
                    "medium": 4,
                    "low": 0,
                    "report": "factory/analyze-1.md",
                    "at": "2026-11-04T00:00:00Z",
                },
            }
        self.box.corrupt_worktree_state(self.branch, mutate)

    def test_first_record_sets_the_baseline_to_its_counts_and_time(self):
        self.assertEqual(self.record("factory/analyze-1.md", medium=2, low=1).returncode, 0)
        analyze = self.load()["analyze"]
        self.assertEqual(
            analyze["baseline"],
            {
                "critical": 0,
                "high": 0,
                "medium": 2,
                "low": 1,
                "report": "factory/analyze-1.md",
                "at": analyze["result"]["at"],
            },
        )

    def test_later_record_changes_only_result_and_reports(self):
        self.record("factory/analyze-1.md", medium=2, low=1)
        before = self.load()["analyze"]["baseline"]
        self.assertEqual(self.record("factory/analyze-2.md", medium=0).returncode, 0)
        analyze = self.load()["analyze"]
        self.assertEqual(analyze["baseline"], before)
        self.assertEqual(analyze["result"]["report"], "factory/analyze-2.md")
        self.assertEqual(analyze["reports"], ["factory/analyze-1.md", "factory/analyze-2.md"])

    def test_legacy_single_report_derives_the_baseline_on_the_next_record(self):
        self.legacy_state(["factory/analyze-1.md"])
        self.assertEqual(self.record("factory/analyze-2.md", medium=1).returncode, 0)
        baseline = self.load()["analyze"]["baseline"]
        self.assertEqual(baseline["report"], "factory/analyze-1.md")
        self.assertEqual(baseline["medium"], 4)

    def test_legacy_two_reports_without_baseline_stay_without_baseline(self):
        self.legacy_state(["factory/analyze-1.md", "factory/analyze-1-full.md"])
        self.assertEqual(self.record("factory/analyze-2.md", medium=1).returncode, 0)
        self.assertNotIn("baseline", self.load()["analyze"])

    def test_fresh_baseline_on_an_underivable_state_sets_the_new_record(self):
        self.legacy_state(["factory/analyze-1.md", "factory/analyze-1-full.md"])
        out = self.record("factory/analyze-2.md", fresh=True, medium=3)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(self.load()["analyze"]["baseline"]["report"], "factory/analyze-2.md")
        self.assertEqual(self.load()["analyze"]["baseline"]["medium"], 3)

    def assert_fresh_refused_unchanged(self):
        before = self.state_path.read_bytes()
        head = self.box.git("rev-parse", "HEAD", cwd=self.wt)
        out = self.record("factory/analyze-2.md", fresh=True, medium=0)
        self.assertEqual(out.returncode, 1, out.stderr)
        self.assertEqual(self.state_path.read_bytes(), before)
        self.assertEqual(self.box.git("rev-parse", "HEAD", cwd=self.wt), head)

    def test_fresh_baseline_refused_with_a_stored_baseline(self):
        self.record("factory/analyze-1.md", medium=2)
        self.assert_fresh_refused_unchanged()

    def test_fresh_baseline_refused_with_a_derivable_baseline(self):
        self.legacy_state(["factory/analyze-1.md"])
        self.assert_fresh_refused_unchanged()

    def test_escalation_record_keeps_baseline_loops_and_pass(self):
        self.record("factory/analyze-1.md", medium=2)
        before = self.load()["analyze"]
        self.assertEqual(self.record("factory/analyze-1-full.md", high=1).returncode, 0)
        after = self.load()["analyze"]
        self.assertEqual(after["baseline"], before["baseline"])
        self.assertEqual((after["loops"], after["pass"]), (0, 1))
        self.assertEqual(after["result"]["report"], "factory/analyze-1-full.md")


class RepairCycleCheckpointTests(unittest.TestCase):
    """`checkpoint remediate` is the only writer of loops and pass (FR-003, FR-014, FR-021)."""

    def setUp(self):
        self.box = Sandbox()
        self.addCleanup(self.box.close)
        self.branch = "097-cycles"
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
        for name in ("analyze-1.md", "analyze-1-full.md", "analyze-2.md"):
            (self.spec / "factory" / name).write_text("# Analysis\n")

    def load(self):
        return json.loads(self.state_path.read_text())

    def analyze(self):
        return self.load()["analyze"]

    def record(self, report, **counts):
        block = {
            "status": "done",
            "stage": "analyze",
            "summary": "Analysis",
            "files": [],
            "questions": [],
            "error": None,
            "analyze": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                **counts,
                "report": report,
            },
        }
        path = self.box.write_temp(f"analysis-{report.replace('/', '_')}.json", json.dumps(block))
        return self.box.cli("analyze-record", path, cwd=self.wt)

    def checkpoint(self, stage, nxt):
        return self.box.cli("checkpoint", stage, "--next", nxt, cwd=self.wt)

    def run_one_cycle(self):
        self.assertEqual(self.record("factory/analyze-1.md", medium=2).returncode, 0)
        self.assertEqual(self.checkpoint("analyze", "remediate").returncode, 0)
        out = self.checkpoint("remediate", "analyze")
        self.assertEqual(out.returncode, 0, out.stderr)

    def test_a_cycle_increments_loops_and_pass_once(self):
        self.run_one_cycle()
        self.assertEqual((self.analyze()["loops"], self.analyze()["pass"]), (1, 2))

    def test_repeated_checkpoint_remediate_after_the_stage_advanced_does_not_increment(self):
        self.run_one_cycle()
        self.assertEqual(self.checkpoint("remediate", "analyze").returncode, 0)
        self.assertEqual((self.analyze()["loops"], self.analyze()["pass"]), (1, 2))

    def test_stale_result_refuses_implement_until_a_fresh_analysis_is_recorded(self):
        self.run_one_cycle()
        refused = self.checkpoint("analyze", "implement")
        self.assertEqual(refused.returncode, 1, refused.stderr)
        self.assertEqual(self.load()["stage"], "analyze")
        self.assertEqual(self.record("factory/analyze-2.md").returncode, 0)
        out = self.checkpoint("analyze", "implement")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(self.load()["stage"], "implement")

    def test_escalation_consumes_no_cycle(self):
        self.assertEqual(self.record("factory/analyze-1.md", high=1).returncode, 0)
        self.assertEqual(self.record("factory/analyze-1-full.md", high=1).returncode, 0)
        self.assertEqual((self.analyze()["loops"], self.analyze()["pass"]), (0, 1))

    def test_the_cap_refuses_a_checkpoint_into_remediate_without_writing(self):
        self.box.corrupt_worktree_state(self.branch, lambda s: s["analyze"].update(loops=2))
        self.assertEqual(self.record("factory/analyze-1.md", medium=2).returncode, 0)
        before = self.state_path.read_bytes()
        head = self.box.git("rev-parse", "HEAD", cwd=self.wt)
        out = self.checkpoint("analyze", "remediate")
        self.assertEqual(out.returncode, 1, out.stderr)
        self.assertEqual(self.state_path.read_bytes(), before)
        self.assertEqual(self.box.git("rev-parse", "HEAD", cwd=self.wt), head)

    def test_resume_on_another_harness_keeps_baseline_and_loops(self):
        self.run_one_cycle()
        before = self.analyze()
        self.box.corrupt_worktree_state(self.branch, lambda s: s.update(harness="opencode"))
        out = self.box.cli("resume", self.branch)
        self.assertEqual(out.returncode, 0, out.stderr)
        after = self.analyze()
        self.assertEqual(after["baseline"], before["baseline"])
        self.assertEqual(after["loops"], before["loops"])


class AmendmentCheckTests(unittest.TestCase):
    """`amendment-check` hashes an approved constitution draft read-only (FR-018, FR-019, SC-005)."""

    def setUp(self):
        self.box = Sandbox()
        self.addCleanup(self.box.close)
        self.constitution = self.box.repo / ".specify" / "memory" / "constitution.md"
        self.constitution.parent.mkdir(parents=True)
        self.constitution.write_text("# Constitution v1\n")
        self.draft = self.box.dir / "constitution-amendment-1.md"
        self.draft.write_text("# Constitution v2\n\nRationale.\n")

    def check(self, *args):
        return self.box.cli("amendment-check", *args, cwd=self.box.repo)

    def test_prints_the_lower_case_sha256_of_the_draft_bytes(self):
        out = self.check(str(self.draft))
        self.assertEqual(out.returncode, 0, out.stderr)
        digest = hashlib.sha256(self.draft.read_bytes()).hexdigest()
        self.assertEqual(json.loads(out.stdout), {"draft": str(self.draft), "sha256": digest})

    def test_matching_approved_hash_exits_zero(self):
        digest = hashlib.sha256(self.draft.read_bytes()).hexdigest()
        out = self.check(str(self.draft), "--sha256", digest)
        self.assertEqual(out.returncode, 0, out.stderr)

    def test_missing_draft_exits_one_naming_the_path(self):
        missing = self.box.dir / "absent.md"
        out = self.check(str(missing))
        self.assertEqual(out.returncode, 1)
        self.assertIn(str(missing), out.stderr)

    def test_draft_edited_after_approval_exits_one_naming_both_hashes(self):
        approved = hashlib.sha256(self.draft.read_bytes()).hexdigest()
        self.draft.write_text("# Constitution v2 (edited)\n")
        current = hashlib.sha256(self.draft.read_bytes()).hexdigest()
        out = self.check(str(self.draft), "--sha256", approved)
        self.assertEqual(out.returncode, 1)
        self.assertIn(approved, out.stderr)
        self.assertIn(current, out.stderr)

    def test_constitution_stays_byte_identical_after_each_call(self):
        before = self.constitution.read_bytes()
        digest = hashlib.sha256(self.draft.read_bytes()).hexdigest()
        self.check(str(self.draft))
        self.check(str(self.draft), "--sha256", digest)
        self.check(str(self.box.dir / "absent.md"))
        self.assertEqual(self.constitution.read_bytes(), before)
