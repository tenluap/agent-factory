"""Adopt seam tests: the `adopted` state block and history event (T002).

Later units add the dry-run report, refusals and the write with rollback
through the public `bin/factory adopt` command, over throwaway Sandbox repos.
"""

import json
import os
import sys
import unittest
from pathlib import Path

CORE_BIN = Path(__file__).resolve().parents[2] / "core" / "skills" / "factory" / "bin"
sys.path.insert(0, str(CORE_BIN))

from factory_cli import state  # noqa: E402
from tests import Sandbox, fixture  # noqa: E402

BASE_SHA = "0123456789abcdef0123456789abcdef01234567"
REPORT_KEYS = {
    "source",
    "shape",
    "branch",
    "spec_dir",
    "base",
    "artifacts",
    "dirty",
    "inferred_stage",
    "needs_clarification",
    "worktree",
    "pending",
    "refusal",
}


def files_under(root):
    """Every regular file under `root` (outside .git) as {relative path: bytes}."""
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(root).parts
    }


def adopted_state():
    """A v5 run adopted at `analyze`: one adopted entry, no complete entries."""
    run = fixture("state-v5.json")
    run.update(stage="analyze", status="running")
    run.pop("commands", None)
    run["adopted"] = {
        "source": {
            "shape": "branch",
            "branch": "007-x",
            "spec_dir": "specs/007-x",
        },
        "inferred_stage": "tasks",
        "chosen_stage": "analyze",
        "base_commit": BASE_SHA,
    }
    run["history"] = [
        {
            "at": "2026-11-04T10:00:00Z",
            "stage": "analyze",
            "event": "adopted",
            "commit": None,
            "harness": "opencode",
        }
    ]
    return run


def problems_for(mutate):
    run = adopted_state()
    mutate(run)
    return state.validate_state(run)


class AdoptedStateTests(unittest.TestCase):
    def test_adopted_state_at_analyze_validates_clean(self):
        self.assertEqual(state.validate_state(adopted_state()), [])

    def test_state_without_adopted_block_still_validates(self):
        run = fixture("state-v5.json")
        self.assertEqual(state.validate_state(run), [])

    def test_non_object_adopted_names_the_block(self):
        problems = problems_for(lambda run: run.update(adopted="007-x"))
        self.assertEqual([p["location"] for p in problems], ["adopted"])

    def test_off_vocabulary_shape_is_one_problem(self):
        def mutate(run):
            run["adopted"]["source"]["shape"] = "fork"

        problems = problems_for(mutate)
        self.assertEqual([p["location"] for p in problems], ["adopted.source.shape"])

    def test_missing_source_branch_is_one_problem(self):
        def mutate(run):
            del run["adopted"]["source"]["branch"]

        problems = problems_for(mutate)
        self.assertEqual([p["location"] for p in problems], ["adopted.source.branch"])

    def test_missing_source_spec_dir_is_one_problem(self):
        def mutate(run):
            run["adopted"]["source"]["spec_dir"] = ""

        problems = problems_for(mutate)
        self.assertEqual(
            [p["location"] for p in problems], ["adopted.source.spec_dir"]
        )

    def test_inferred_stage_outside_adopt_stages_is_one_problem(self):
        def mutate(run):
            run["adopted"]["inferred_stage"] = "implement"

        problems = problems_for(mutate)
        self.assertEqual(
            [p["location"] for p in problems], ["adopted.inferred_stage"]
        )

    def test_chosen_stage_outside_adopt_stages_is_one_problem(self):
        def mutate(run):
            run["adopted"]["chosen_stage"] = "grill"

        problems = problems_for(mutate)
        self.assertEqual([p["location"] for p in problems], ["adopted.chosen_stage"])

    def test_uppercase_base_commit_is_one_problem(self):
        def mutate(run):
            run["adopted"]["base_commit"] = BASE_SHA.upper()

        problems = problems_for(mutate)
        self.assertEqual([p["location"] for p in problems], ["adopted.base_commit"])

    def test_short_base_commit_is_one_problem(self):
        def mutate(run):
            run["adopted"]["base_commit"] = BASE_SHA[:39]

        problems = problems_for(mutate)
        self.assertEqual([p["location"] for p in problems], ["adopted.base_commit"])

    def test_adopted_history_entry_without_block_is_one_problem(self):
        def mutate(run):
            del run["adopted"]

        problems = problems_for(mutate)
        self.assertEqual(len(problems), 1)
        self.assertIn("adopted", problems[0]["reason"])
        self.assertEqual(problems[0]["location"], "history[0].event")

    def test_adopted_event_is_in_history_vocabulary(self):
        self.assertIn("adopted", state.HISTORY_EVENTS)
        self.assertEqual(
            state.ADOPT_SHAPES, ("branch", "remote-branch", "default-branch")
        )
        self.assertEqual(
            state.ADOPT_STAGES, ("specify", "plan", "tasks", "analyze")
        )


class ResumeHintTests(unittest.TestCase):
    """`resume` with no matching run points at `adopt` (D9); other callers do not."""

    def setUp(self):
        self.box = Sandbox()
        self.addCleanup(self.box.close)
        base = self.box.git("rev-parse", "--abbrev-ref", "HEAD").strip()
        self.box.git("checkout", "-q", "-b", "007-x")
        spec = self.box.repo / "specs" / "007-x"
        spec.mkdir(parents=True)
        (spec / "spec.md").write_text("# Spec\n")
        self.box.git("add", "-A")
        self.box.git("commit", "-q", "-m", "spec 007-x")
        self.box.git("checkout", "-q", base)

    def snapshot(self):
        return (
            self.box.git("status", "--porcelain"),
            self.box.git("branch", "--list"),
            self.box.git("worktree", "list", "--porcelain"),
        )

    def test_resume_without_run_hints_adopt_and_creates_nothing(self):
        before = self.snapshot()
        out = self.box.cli("resume", "007-x")
        self.assertEqual(out.returncode, 1, out.stdout)
        self.assertIn("no run '007-x'", out.stderr)
        self.assertIn("use adopt <branch|spec_dir>", out.stderr)
        self.assertEqual(self.snapshot(), before)

    def test_show_without_run_has_no_adopt_hint(self):
        out = self.box.cli("show", "nope")
        self.assertEqual(out.returncode, 1)
        self.assertIn("no run 'nope'", out.stderr)
        self.assertNotIn("adopt", out.stderr)

    def test_pending_run_still_resumes(self):
        self.box.pending_run("007-x", fixture("state-v1.json"))
        out = self.box.cli("resume", "007-x")
        self.assertEqual(out.returncode, 0, out.stderr)


class DryRunFixture(unittest.TestCase):
    """A repo whose default branch is `main`, with SpecKit specs on their own branches."""

    def setUp(self):
        self.box = Sandbox()
        self.addCleanup(self.box.close)
        self.box.git("branch", "-M", "main")

    def spec_branch(self, branch, files):
        """Commit `files` (name -> text) under specs/<branch>/ on a new branch, back on main."""
        self.box.git("checkout", "-q", "-b", branch)
        spec = self.box.repo / "specs" / branch
        spec.mkdir(parents=True, exist_ok=True)
        for name, text in files.items():
            (spec / name).write_text(text)
        self.box.git("add", "-A")
        self.box.git("commit", "-q", "-m", f"spec {branch}")
        self.box.git("checkout", "-q", "main")

    def snapshot(self):
        """What a dry run must leave byte-identical (SC-002)."""
        return {
            "status": self.box.git("status", "--porcelain", "--untracked-files=all"),
            "refs": self.box.git("for-each-ref"),
            "worktrees": self.box.git("worktree", "list", "--porcelain"),
            "files": files_under(self.box.repo),
            "pending": files_under(self.box.home / "pending"),
        }


class DryRunReportTests(DryRunFixture):
    """`factory adopt <src> --dry-run` prints the contracts/cli.md report (T003)."""

    def setUp(self):
        super().setUp()
        self.spec_branch("007-x", {"spec.md": "# Spec\n"})

    def test_branch_shape_prints_the_report_and_exits_0(self):
        before = self.snapshot()
        out = self.box.cli("adopt", "007-x", "--dry-run")
        self.assertEqual(out.returncode, 0, out.stderr)
        report = json.loads(out.stdout)
        self.assertEqual(set(report), REPORT_KEYS)
        self.assertEqual(report["source"], "007-x")
        self.assertEqual(report["shape"], "branch")
        self.assertEqual(report["branch"], "007-x")
        self.assertEqual(report["spec_dir"], "specs/007-x")
        self.assertEqual(report["base"], "main")
        self.assertEqual(report["artifacts"], ["spec.md"])
        self.assertEqual(report["dirty"], [])
        self.assertEqual(report["inferred_stage"], "plan")
        self.assertEqual(report["needs_clarification"], [])
        self.assertEqual(
            os.path.realpath(report["worktree"]),
            os.path.realpath(self.box.dir / "repo-factory" / "007-x"),
        )
        self.assertEqual(report["pending"], "repo-adopt-007-x")
        self.assertIsNone(report["refusal"])
        self.assertEqual(self.snapshot(), before)

    def test_plan_md_infers_tasks(self):
        self.spec_branch("008-y", {"spec.md": "# S\n", "plan.md": "# P\n"})
        report = json.loads(self.box.cli("adopt", "008-y", "--dry-run").stdout)
        self.assertEqual(report["inferred_stage"], "tasks")

    def test_tasks_md_with_checked_boxes_infers_analyze(self):
        self.spec_branch(
            "009-z",
            {"spec.md": "# S\n", "plan.md": "# P\n", "tasks.md": "- [x] T001 done\n"},
        )
        report = json.loads(self.box.cli("adopt", "009-z", "--dry-run").stdout)
        self.assertEqual(report["inferred_stage"], "analyze")

    def test_every_needs_clarification_line_is_listed(self):
        self.spec_branch(
            "010-m",
            {
                "spec.md": "# S\n[NEEDS CLARIFICATION: scope]\nok\n"
                "[NEEDS CLARIFICATION: auth]\n"
            },
        )
        report = json.loads(self.box.cli("adopt", "010-m", "--dry-run").stdout)
        self.assertEqual(
            report["needs_clarification"],
            ["[NEEDS CLARIFICATION: scope]", "[NEEDS CLARIFICATION: auth]"],
        )

    def test_spec_dir_argument_resolves_the_same_branch(self):
        by_branch = json.loads(self.box.cli("adopt", "007-x", "--dry-run").stdout)
        out = self.box.cli("adopt", "specs/007-x", "--dry-run")
        self.assertEqual(out.returncode, 0, out.stderr)
        report = json.loads(out.stdout)
        self.assertEqual(report["source"], "specs/007-x")
        for key in (
            "shape",
            "branch",
            "spec_dir",
            "base",
            "artifacts",
            "inferred_stage",
            "worktree",
            "pending",
        ):
            self.assertEqual(report[key], by_branch[key], key)

    def test_stage_outside_adopt_stages_exits_5_and_writes_nothing(self):
        for stage in ("implement", "bogus"):
            before = self.snapshot()
            out = self.box.cli("adopt", "007-x", "--stage", stage, "--dry-run")
            self.assertEqual(out.returncode, 5, out.stdout + out.stderr)
            self.assertIn("--stage", out.stderr)
            self.assertEqual(self.snapshot(), before)

    def test_stage_inside_adopt_stages_is_accepted(self):
        out = self.box.cli("adopt", "007-x", "--stage", "plan", "--dry-run")
        self.assertEqual(out.returncode, 0, out.stderr)


if __name__ == "__main__":
    unittest.main()
