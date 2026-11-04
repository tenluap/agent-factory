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
            (spec / name).parent.mkdir(parents=True, exist_ok=True)
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


class DryRunRefusalTests(DryRunFixture):
    """Every refusal exits 1 (or 3 for ambiguity) and leaves the repo unchanged (T004)."""

    def setUp(self):
        super().setUp()
        self.spec_branch("007-x", {"spec.md": "# Spec\n"})

    def refused(self, src, *fragments):
        before = self.snapshot()
        out = self.box.cli("adopt", src, "--dry-run")
        self.assertEqual(out.returncode, 1, out.stdout + out.stderr)
        report = json.loads(out.stdout)
        self.assertIsNotNone(report["refusal"])
        for fragment in fragments:
            self.assertIn(fragment, report["refusal"])
        self.assertEqual(self.snapshot(), before)
        return report

    def test_dirty_spec_file_and_source_checkout_are_all_listed(self):
        # The spec tracked on main, then edited there; an untracked file in a worktree on 007-x.
        self.box.git("checkout", "-q", "007-x", "--", "specs/007-x")
        self.box.git("commit", "-q", "-m", "copy spec to main")
        (self.box.repo / "specs" / "007-x" / "spec.md").write_text("# edited\n")
        worktree = self.box.dir / "elsewhere"
        self.box.git("worktree", "add", "-q", str(worktree), "007-x")
        (worktree / "notes.txt").write_text("scratch\n")
        report = self.refused("007-x", "specs/007-x/spec.md", "notes.txt")
        self.assertEqual(report["dirty"], ["notes.txt", "specs/007-x/spec.md"])

    def test_committed_factory_state_names_resume(self):
        self.spec_branch("011-r", {"spec.md": "# S\n", "factory/state.json": "{}\n"})
        report = self.refused("011-r", "resume 011-r")
        self.assertEqual(report["dirty"], [])

    def test_spec_dir_without_spec_md_is_refused(self):
        self.spec_branch("012-p", {"plan.md": "# P\n"})
        self.refused("012-p", "spec.md")

    def test_branch_checked_out_in_main_checkout_names_switch_hint(self):
        self.box.git("checkout", "-q", "007-x")
        self.refused("007-x", "007-x", "switch")

    def test_branch_checked_out_in_another_worktree_names_its_path(self):
        worktree = self.box.dir / "elsewhere"
        self.box.git("worktree", "add", "-q", str(worktree), "007-x")
        self.refused("007-x", "elsewhere", "switch")

    def test_existing_worktree_path_is_named(self):
        (self.box.dir / "repo-factory" / "007-x").mkdir(parents=True)
        self.refused("007-x", "repo-factory", "007-x")

    def test_other_pending_file_is_named_with_resume_and_prune_hint(self):
        self.box.pending_run("other", fixture("state-v1.json"))
        self.refused("007-x", "repo-other", "resume", "prune")

    def test_own_pending_adoption_refuses_nothing(self):
        self.box.pending_run("adopt-007-x", fixture("state-v1.json"))
        out = self.box.cli("adopt", "007-x", "--dry-run")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIsNone(json.loads(out.stdout)["refusal"])

    def test_no_matching_source_exits_1(self):
        self.refused("nope", "no branch or spec dir matches 'nope'")

    def test_invalid_branch_name_is_no_match_exits_1(self):
        self.refused("../x", "not a valid branch name")

    def test_ambiguous_source_exits_3_listing_both_branches(self):
        self.box.git("branch", "008-x")
        before = self.snapshot()
        out = self.box.cli("adopt", "x", "--dry-run")
        self.assertEqual(out.returncode, 3, out.stdout + out.stderr)
        self.assertIn("007-x", out.stderr)
        self.assertIn("008-x", out.stderr)
        self.assertEqual(self.snapshot(), before)


class OtherShapeTests(DryRunFixture):
    """The remote-branch, default-branch and renamed-dir shapes, previewed only (T005)."""

    def setUp(self):
        super().setUp()
        self.origin = self.box.dir / "origin.git"
        self.box.git("init", "-q", "--bare", str(self.origin))
        self.box.git("remote", "add", "origin", str(self.origin))
        self.box.git("push", "-q", "origin", "main")

    def publish_spec(self, branch):
        """Push `branch` and drop its local copy, so only origin/<branch> remains."""
        self.box.git("push", "-q", "origin", branch)
        self.box.git("branch", "-D", branch)

    def dry_run(self, src):
        out = self.box.cli("adopt", src, "--dry-run")
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        return json.loads(out.stdout)

    def test_branch_only_on_origin_is_remote_branch(self):
        self.spec_branch("007-x", {"spec.md": "# S\n"})
        self.publish_spec("007-x")
        report = self.dry_run("007-x")
        self.assertEqual(report["shape"], "remote-branch")
        self.assertEqual(report["base"], "origin/main")
        self.assertEqual(report["artifacts"], ["spec.md"])
        self.assertIsNone(report["refusal"])

    def test_spec_dir_on_base_without_own_branch_is_default_branch(self):
        self.write_main_spec("010-d")
        report = self.dry_run("010-d")
        self.assertEqual(report["shape"], "default-branch")
        self.assertEqual(report["branch"], "010-d")
        self.assertEqual(report["spec_dir"], "specs/010-d")
        self.assertIsNone(report["refusal"])

    def test_same_dir_with_a_local_branch_is_branch_shape(self):
        self.write_main_spec("010-d")
        self.box.git("branch", "010-d")
        self.assertEqual(self.dry_run("010-d")["shape"], "branch")

    def test_branch_holding_renamed_spec_dir_records_that_dir(self):
        self.box.git("checkout", "-q", "-b", "feat-y")
        spec = self.box.repo / "specs" / "009-renamed"
        spec.mkdir(parents=True)
        (spec / "spec.md").write_text("# S\n")
        self.box.git("add", "-A")
        self.box.git("commit", "-q", "-m", "renamed spec")
        self.box.git("checkout", "-q", "main")
        report = self.dry_run("feat-y")
        self.assertEqual(report["shape"], "branch")
        self.assertEqual(report["spec_dir"], "specs/009-renamed")
        self.assertEqual(report["inferred_stage"], "plan")

    def test_spec_dir_only_on_local_default_is_refused(self):
        self.write_main_spec("011-l", push=False)
        before = self.snapshot()
        out = self.box.cli("adopt", "011-l", "--dry-run")
        self.assertEqual(out.returncode, 1, out.stdout + out.stderr)
        refusal = json.loads(out.stdout)["refusal"]
        self.assertIn("not on 'origin/main'", refusal)
        self.assertIn("push it or create its branch first", refusal)
        self.assertEqual(self.snapshot(), before)

    def test_local_branch_also_on_origin_uses_local_artifacts(self):
        self.spec_branch("012-v", {"spec.md": "# S\n"})
        self.box.git("push", "-q", "origin", "012-v")
        self.box.git("checkout", "-q", "012-v")
        (self.box.repo / "specs" / "012-v" / "plan.md").write_text("# P\n")
        self.box.git("add", "-A")
        self.box.git("commit", "-q", "-m", "local plan")
        self.box.git("checkout", "-q", "main")
        report = self.dry_run("012-v")
        self.assertEqual(report["shape"], "branch")
        self.assertEqual(report["inferred_stage"], "tasks")

    def test_remote_ahead_of_last_fetch_is_not_fetched(self):
        self.spec_branch("013-r", {"spec.md": "# S\n"})
        self.publish_spec("013-r")
        other = self.box.dir / "other"
        self.box.git("clone", "-q", str(self.origin), str(other))
        self.box.git("checkout", "-q", "013-r", cwd=other)
        (other / "specs" / "013-r" / "plan.md").write_text("# P\n")
        self.box.git("add", "-A", cwd=other)
        self.box.git(
            "-c", "user.email=a@example.com", "-c", "user.name=Other",
            "commit", "-q", "-m", "ahead", cwd=other,
        )
        self.box.git("push", "-q", "origin", "013-r", cwd=other)
        before = self.snapshot()
        report = self.dry_run("013-r")
        self.assertEqual(report["artifacts"], ["spec.md"])
        self.assertEqual(self.snapshot(), before)

    def write_main_spec(self, name, push=True):
        spec = self.box.repo / "specs" / name
        spec.mkdir(parents=True)
        (spec / "spec.md").write_text("# S\n")
        self.box.git("add", "-A")
        self.box.git("commit", "-q", "-m", f"spec {name} on main")
        if push:
            self.box.git("push", "-q", "origin", "main")


def pending_state(repo, **extra):
    """A pending adoption as `factory adopt` leaves it after a clean dry run (T006 fixture)."""
    run = {
        "version": 5,
        "started_at": "2026-11-04T10:00:00Z",
        "ended_at": None,
        "harness": "opencode",
        "feature": "Spec 007",
        "repo": str(repo),
        "default_branch": "main",
        "base": "main",
        "branch": "007-x",
        "worktree": None,
        "spec_dir": "specs/007-x",
        "status": "running",
        "stage": "grill",
        "halt_reason": None,
        "mode": {"chain": "lite", "fast": True, "cruise": False},
        "history": [],
    }
    run.update(extra)
    return run


class AdoptWriteFixture(DryRunFixture):
    """SpecKit branch 007-x (spec.md, plan.md) with its pending adoption and brief/profile (T006)."""

    def setUp(self):
        super().setUp()
        self.spec_branch("007-x", {"spec.md": "# Spec\n", "plan.md": "# Plan\n"})
        self.pending = self.box.pending_run("adopt-007-x", pending_state(self.box.repo))
        self.brief = self.pending.with_name(self.pending.name.replace(".json", ".brief.md"))
        self.profile = self.pending.with_name(self.pending.name.replace(".json", ".profile.md"))
        self.brief.write_text("# Brief\n")
        self.profile.write_text("# Profile\n")
        self.worktree = self.box.dir / "repo-factory" / "007-x"

    def commit_on(self, branch, files, message):
        """Commit `files` (relative to specs/<branch>/) on `branch` through a throwaway checkout."""
        tmp = self.box.dir / f"edit-{branch}"
        self.box.git("worktree", "add", "-q", str(tmp), branch)
        for name, text in files.items():
            (tmp / "specs" / branch / name).parent.mkdir(parents=True, exist_ok=True)
            (tmp / "specs" / branch / name).write_text(text)
        self.box.git("add", "-A", cwd=tmp)
        self.box.git("commit", "-q", "-m", message, cwd=tmp)
        self.box.git("worktree", "remove", "--force", str(tmp))

    def write_run(self, *args):
        return self.box.cli("adopt", "007-x", *args)

    def branch_names(self):
        return self.box.git("branch", "--format=%(refname:short)")

    def refused(self, *fragments):
        before = self.snapshot()
        out = self.write_run()
        combined = out.stdout + out.stderr
        self.assertEqual(out.returncode, 1, combined)
        for fragment in fragments:
            self.assertIn(fragment, combined)
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(self.worktree.exists())


class AdoptWriteTests(AdoptWriteFixture):
    """`factory adopt <src>` writes the branch-shape worktree run in one commit (T006)."""

    def test_branch_shape_writes_worktree_state_and_one_commit(self):
        head = self.box.git("rev-parse", "007-x").strip()
        names = self.branch_names()
        out = self.write_run()
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertEqual(json.loads(out.stdout)["stage"], "tasks")
        self.assertEqual(self.branch_names(), names)
        self.assertEqual(
            os.path.realpath(self.worktree),
            os.path.realpath(self.box.dir / "repo-factory" / "007-x"),
        )
        folder = self.worktree / "specs" / "007-x" / "factory"
        run = json.loads((folder / "state.json").read_text())
        self.assertEqual(state.validate_state(run), [])
        self.assertEqual(run["stage"], "tasks")
        self.assertEqual(run["status"], "running")
        self.assertEqual(
            run["adopted"],
            {
                "source": {"shape": "branch", "branch": "007-x", "spec_dir": "specs/007-x"},
                "inferred_stage": "tasks",
                "chosen_stage": "tasks",
                "base_commit": head,
            },
        )
        self.assertEqual([e["event"] for e in run["history"]], ["adopted"])
        self.assertEqual(run["history"][0]["stage"], "tasks")
        self.assertEqual((folder / "brief.md").read_text(), "# Brief\n")
        self.assertEqual((folder / "profile.md").read_text(), "# Profile\n")
        self.assertFalse(self.pending.exists())
        self.assertFalse(self.brief.exists())
        self.assertFalse(self.profile.exists())
        commits = self.box.git("log", "--format=%s", f"{head}..007-x").splitlines()
        self.assertEqual(commits, ["factory: adopt 007-x"])
        changed = self.box.git("diff", "--name-only", f"{head}..007-x").splitlines()
        self.assertTrue(changed and all(p.startswith("specs/007-x/factory/") for p in changed))

    def test_stage_flag_records_the_chosen_stage(self):
        out = self.write_run("--stage", "plan")
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        run = json.loads((self.worktree / "specs/007-x/factory/state.json").read_text())
        self.assertEqual(run["stage"], "plan")
        self.assertEqual(run["adopted"]["chosen_stage"], "plan")
        self.assertEqual(run["adopted"]["inferred_stage"], "tasks")

    def test_commit_made_after_the_dry_run_is_the_recorded_base(self):
        self.commit_on("007-x", {"notes.md": "later\n"}, "spec 007-x follow-up")
        head = self.box.git("rev-parse", "007-x").strip()
        out = self.write_run()
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        run = json.loads((self.worktree / "specs/007-x/factory/state.json").read_text())
        self.assertEqual(run["adopted"]["base_commit"], head)

    def test_file_dirtied_after_the_dry_run_refuses_and_writes_nothing(self):
        (self.box.repo / "specs" / "007-x").mkdir(parents=True)
        (self.box.repo / "specs" / "007-x" / "notes.md").write_text("dirty\n")
        self.refused("uncommitted changes")

    def test_factory_state_committed_after_the_dry_run_refuses(self):
        self.commit_on("007-x", {"factory/state.json": "{}\n"}, "factory state 007-x")
        self.refused("already has factory/state.json", "resume")

    def test_other_pending_file_added_after_the_dry_run_refuses(self):
        self.box.pending_run("other", pending_state(self.box.repo, branch="008-y"))
        self.refused("another pending run")

    def test_missing_pending_file_refuses(self):
        self.pending.unlink()
        self.refused("no pending adoption")

    def test_aborted_pending_adoption_refuses(self):
        self.pending.write_text(
            json.dumps(dict(pending_state(self.box.repo), status="aborted"), indent=2)
        )
        self.refused("aborted")

    def test_live_foreign_lock_on_the_pending_path_refuses(self):
        lock_file = self.pending.with_suffix(".lock.json")
        lock_file.write_text(
            json.dumps(
                {
                    "owner_pid": 1,
                    "host": "another-host",
                    "harness": "codex",
                    "at": "2026-11-04T10:00:00Z",
                    "taken_over": False,
                    "previous": None,
                }
            )
        )
        self.refused("locked")
        self.assertTrue(lock_file.exists())


class AdoptRollbackTests(AdoptWriteFixture):
    """A commit rejected after the worktree exists is rolled back; the pending files stay (T007)."""

    def reject_commits(self):
        hook = self.box.repo / ".git" / "hooks" / "pre-commit"
        hook.write_text("#!/bin/sh\necho 'rejected by test hook' >&2\nexit 1\n")
        hook.chmod(0o755)
        return hook

    def test_rejecting_pre_commit_hook_rolls_back_and_exits_1(self):
        head = self.box.git("rev-parse", "007-x").strip()
        worktrees = self.box.git("worktree", "list", "--porcelain")
        brief, profile = self.brief.read_text(), self.profile.read_text()
        self.reject_commits()
        out = self.write_run()
        combined = out.stdout + out.stderr
        self.assertEqual(out.returncode, 1, combined)
        self.assertIn("rejected by test hook", combined)
        self.assertFalse(self.worktree.exists())
        self.assertEqual(self.box.git("worktree", "list", "--porcelain"), worktrees)
        self.assertEqual(self.box.git("rev-parse", "007-x").strip(), head)
        self.assertEqual(self.box.git("branch", "--format=%(refname:short)").split(), ["007-x", "main"])
        self.assertTrue(self.pending.exists())
        self.assertEqual(self.brief.read_text(), brief)
        self.assertEqual(self.profile.read_text(), profile)

    def test_retry_after_the_hook_is_removed_reuses_the_pending_file(self):
        head = self.box.git("rev-parse", "007-x").strip()
        hook = self.reject_commits()
        self.assertEqual(self.write_run().returncode, 1)
        hook.unlink()
        out = self.write_run()
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertEqual(
            self.box.git("log", "--format=%s", f"{head}..007-x").splitlines(),
            ["factory: adopt 007-x"],
        )
        self.assertFalse(self.pending.exists())


class AdoptSourceShapeWriteTests(DryRunFixture):
    """The remote-branch and default-branch shapes create their local branch in the write (T008)."""

    def setUp(self):
        super().setUp()
        self.origin = self.box.dir / "origin.git"
        self.box.git("init", "-q", "--bare", str(self.origin))
        self.box.git("remote", "add", "origin", str(self.origin))
        self.box.git("push", "-q", "origin", "main")
        self.worktree = self.box.dir / "repo-factory" / "007-x"
        self.pending = self.box.pending_run(
            "adopt-007-x", pending_state(self.box.repo, base="origin/main")
        )
        self.brief = self.pending.with_name("repo-adopt-007-x.brief.md")
        self.profile = self.pending.with_name("repo-adopt-007-x.profile.md")
        self.brief.write_text("# Brief\n")
        self.profile.write_text("# Profile\n")

    def publish_remote_only(self):
        """A SpecKit branch that exists only as origin/007-x."""
        self.spec_branch("007-x", {"spec.md": "# Spec\n", "plan.md": "# Plan\n"})
        self.box.git("push", "-q", "origin", "007-x")
        self.box.git("branch", "-D", "007-x")

    def publish_default_branch_spec(self):
        """The spec dir lives on origin/main with no branch of its own."""
        spec = self.box.repo / "specs" / "007-x"
        spec.mkdir(parents=True)
        (spec / "spec.md").write_text("# Spec\n")
        (spec / "plan.md").write_text("# Plan\n")
        self.box.git("add", "-A")
        self.box.git("commit", "-q", "-m", "spec on main")
        self.box.git("push", "-q", "origin", "main")

    def write_run(self):
        return self.box.cli("adopt", "007-x")

    def remote_refs(self):
        return self.box.git("ls-remote", "origin")

    def test_remote_only_branch_is_created_tracking_origin(self):
        self.publish_remote_only()
        remote_head = self.box.git("rev-parse", "origin/007-x").strip()
        refs = self.remote_refs()
        out = self.write_run()
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertEqual(self.box.git("rev-parse", "--abbrev-ref", "007-x@{upstream}").strip(), "origin/007-x")
        run = json.loads((self.worktree / "specs/007-x/factory/state.json").read_text())
        self.assertEqual(run["adopted"]["source"]["shape"], "remote-branch")
        self.assertEqual(run["adopted"]["base_commit"], remote_head)
        changed = self.box.git("diff", "--name-only", f"{remote_head}..007-x").splitlines()
        self.assertTrue(changed and all(p.startswith("specs/007-x/factory/") for p in changed))
        self.assertEqual(self.box.git("log", "--format=%s", f"{remote_head}..007-x").splitlines(), ["factory: adopt 007-x"])
        self.assertEqual(self.remote_refs(), refs)
        self.assertFalse(self.pending.exists())

    def test_default_branch_spec_dir_creates_branch_at_base(self):
        self.publish_default_branch_spec()
        base = self.box.git("rev-parse", "origin/main").strip()
        out = self.write_run()
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        run = json.loads((self.worktree / "specs/007-x/factory/state.json").read_text())
        self.assertEqual(run["adopted"]["source"], {"shape": "default-branch", "branch": "007-x", "spec_dir": "specs/007-x"})
        self.assertEqual(run["adopted"]["base_commit"], base)
        self.assertEqual(self.box.git("log", "--format=%s", "origin/main..007-x").splitlines(), ["factory: adopt 007-x"])
        self.assertFalse(self.pending.exists())

    def test_rejected_commit_removes_the_remote_branch_it_created(self):
        self.publish_remote_only()
        refs, pending_before = self.remote_refs(), files_under(self.box.home / "pending")
        self.reject_commits()
        out = self.write_run()
        self.assertEqual(out.returncode, 1, out.stdout + out.stderr)
        self.assertFalse(self.worktree.exists())
        self.assertNotIn("007-x", self.box.git("branch", "--format=%(refname:short)").split())
        self.assertEqual(self.remote_refs(), refs)
        self.assertEqual(files_under(self.box.home / "pending"), pending_before)

    def test_rejected_commit_removes_the_default_branch_it_created(self):
        self.publish_default_branch_spec()
        refs = self.remote_refs()
        self.reject_commits()
        out = self.write_run()
        self.assertEqual(out.returncode, 1, out.stdout + out.stderr)
        self.assertFalse(self.worktree.exists())
        self.assertNotIn("007-x", self.box.git("branch", "--format=%(refname:short)").split())
        self.assertEqual(self.remote_refs(), refs)
        self.assertTrue(self.pending.exists())

    def reject_commits(self):
        hook = self.box.repo / ".git" / "hooks" / "pre-commit"
        hook.write_text("#!/bin/sh\necho 'rejected by test hook' >&2\nexit 1\n")
        hook.chmod(0o755)


if __name__ == "__main__":
    unittest.main()
