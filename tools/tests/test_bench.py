"""Benchmark score/compare public CLI seams; no live harness or token cost."""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

import bench as bench_module
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


STUB = '''#!__PY__
import json
import os
import sys

name = "__NAME__"
argv = sys.argv[1:]
if argv == ["--version"]:
    if os.environ.get("STUB_VERSION_FAIL"):
        sys.exit(3)
    print(name + " 9.9.9-stub")
    sys.exit(0)
keys = ("FACTORY_HOME", "FACTORY_HARNESS", "CLAUDE_CONFIG_DIR", "CLAUDE_HOME", "XDG_CONFIG_HOME")
env = {key: os.environ[key] for key in keys if key in os.environ}
with open(os.environ["STUB_RECORD"], "a") as record:
    record.write(json.dumps({"name": name, "argv": argv, "env": env}) + "\\n")
sys.exit(int(os.environ.get("STUB_EXIT", "0")))
'''

CLAUDE_TOOLS = ["Read", "Edit", "Write", "Agent", "Skill", "Bash(git:*)", "Bash(python3:*)"]


class StubHarness:
    """Python stand-ins for `claude` and `opencode` that record argv and env."""

    def __init__(self, box, names=("claude", "opencode"), folder="bin"):
        self.bin = box.dir / folder
        self.bin.mkdir()
        for name in names:
            path = self.bin / name
            path.write_text(STUB.replace("__PY__", sys.executable).replace("__NAME__", name))
            path.chmod(0o755)
        self.record = box.dir / f"{folder}-record.jsonl"
        self.env = {
            "HOME": str(box.dir / "sandbox-home"),
            "USERPROFILE": str(box.dir / "sandbox-home"),
            "CLAUDE_HOME": str(box.dir / "claude-home"),
            "XDG_CONFIG_HOME": str(box.dir / "xdg"),
            "FACTORY_HOME": str(box.dir / "factory-home"),
            "STUB_RECORD": str(self.record),
        }

    def bench(self, *args, path=None, extra=None):
        env = dict(os.environ)
        for key in ("CLAUDE_CONFIG_DIR", "FACTORY_HARNESS", "ANTHROPIC_API_KEY"):
            env.pop(key, None)
        env.update(self.env, PATH=path or f"{self.bin}{os.pathsep}{os.environ['PATH']}")
        env.update(extra or {})
        return subprocess.run(
            [sys.executable, str(REPO_ROOT / "tools" / "bench.py"), "run", *map(str, args)],
            capture_output=True,
            text=True,
            env=env,
        )

    def calls(self):
        if not self.record.exists():
            return []
        return [json.loads(line) for line in self.record.read_text().splitlines()]


def add_dirs(argv):
    return [argv[i + 1] for i, arg in enumerate(argv) if arg == "--add-dir"]


class RunTests(unittest.TestCase):
    def setUp(self):
        self.box = Sandbox()
        self.addCleanup(self.box.close)
        self.stub = StubHarness(self.box)
        self.out = self.box.dir / "out"
        self.home = self.box.dir / "home"

    def run_bench(self, harness, *extra, out=None, path=None, env=None):
        return self.stub.bench(
            "--harness", harness, "--out", out or self.out, *extra, path=path, extra=env
        )

    def skill_link(self):
        """A skill directory in use, as a symlink to a source outside the output."""
        target = self.box.dir / "skill-src"
        target.mkdir()
        link = Path(self.stub.env["CLAUDE_HOME"]) / "skills" / "factory"
        link.parent.mkdir(parents=True)
        link.symlink_to(target)
        return link, target.resolve()

    def test_claude_code_grant_is_scoped_and_never_bypasses(self):
        link, resolved = self.skill_link()
        out = self.run_bench("claude-code", "--home", self.home)
        self.assertEqual(out.returncode, 0, out.stderr)
        (call,) = self.stub.calls()
        argv = call["argv"]
        self.assertEqual(argv[0], "-p")
        self.assertTrue(argv[1].startswith("/factory resume "))
        self.assertEqual(
            sorted(add_dirs(argv)),
            sorted(str(p) for p in (self.out.resolve(), link, resolved, self.home.resolve())),
        )
        i = argv.index("--allowedTools")
        self.assertEqual(
            argv[i + 1 :], [*CLAUDE_TOOLS, f"Bash({link}/bin/factory:*)"]
        )
        for forbidden in ("--dangerously-skip-permissions", "--permission-mode", "Bash"):
            self.assertNotIn(forbidden, argv)

    def test_opencode_launch_is_plain_run_without_model(self):
        out = self.run_bench("opencode", "--home", self.home)
        self.assertEqual(out.returncode, 0, out.stderr)
        (call,) = self.stub.calls()
        self.assertEqual(call["argv"][0], "run")
        self.assertEqual(len(call["argv"]), 2)
        self.assertTrue(call["argv"][1].startswith("/factory resume "))

    def test_model_option_is_forwarded_to_each_harness(self):
        out = self.run_bench("claude-code", "--model", "sonnet", "--home", self.home)
        self.assertEqual(out.returncode, 0, out.stderr)
        out = self.run_bench(
            "opencode", "--model", "p/m", "--home", self.box.dir / "home-2", out=self.box.dir / "out-2"
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        claude, opencode = self.stub.calls()
        argv = claude["argv"]
        self.assertEqual(argv[argv.index("--model") + 1], "sonnet")
        self.assertEqual(argv[0], "-p")
        self.assertEqual(opencode["argv"][:3], ["run", "-m", "p/m"])
        self.assertEqual(len(opencode["argv"]), 4)

    def test_no_bypass_or_model_option_without_flags_for_either_harness(self):
        for harness in ("claude-code", "opencode"):
            with self.subTest(harness=harness):
                self.run_bench(harness, "--home", self.home)
        for call in self.stub.calls():
            self.assertNotIn("--model", call["argv"])
            self.assertNotIn("-m", call["argv"])
            self.assertNotIn("--dangerously-skip-permissions", call["argv"])
            self.assertNotIn("--permission-mode", call["argv"])

    def test_missing_executable_stops_before_output_directory(self):
        only_opencode = StubHarness(self.box, names=("opencode",), folder="only-opencode")
        out = self.run_bench("claude-code", path=str(only_opencode.bin))
        self.assertEqual(out.returncode, 1)
        self.assertIn("use the manual benchmark fallback", out.stderr)
        self.assertFalse(self.out.exists())

    def test_checkout_renders_under_output_and_launches_against_it(self):
        out = self.run_bench("claude-code", "--from-checkout")
        self.assertEqual(out.returncode, 0, out.stderr)
        root = self.out.resolve()
        config = root / "harness-config"
        self.assertTrue((root / "home" / "dist" / "claude-code").is_dir())
        self.assertTrue((config / "skills" / "factory").exists())
        (call,) = self.stub.calls()
        self.assertEqual(call["env"]["CLAUDE_CONFIG_DIR"], str(config))
        self.assertEqual(call["env"]["CLAUDE_HOME"], str(config))
        self.assertEqual(call["env"]["FACTORY_HOME"], str(root / "home"))
        argv = call["argv"]
        self.assertEqual(add_dirs(argv), [str(root)])
        i = argv.index("--allowedTools")
        self.assertEqual(argv[-1], f"Bash({config}/skills/factory/bin/factory:*)")
        self.assertEqual(argv[i + 1 :][:-1], CLAUDE_TOOLS)

    def test_checkout_model_option_keeps_isolated_environment(self):
        out = self.run_bench("claude-code", "--from-checkout", "--model", "sonnet")
        self.assertEqual(out.returncode, 0, out.stderr)
        (call,) = self.stub.calls()
        argv = call["argv"]
        self.assertEqual(argv[argv.index("--model") + 1], "sonnet")
        config = self.out.resolve() / "harness-config"
        self.assertEqual(call["env"]["CLAUDE_CONFIG_DIR"], str(config))

    def test_opencode_checkout_renders_and_isolates_config(self):
        out = self.run_bench("opencode", "--from-checkout")
        self.assertEqual(out.returncode, 0, out.stderr)
        root = self.out.resolve()
        self.assertTrue((root / "home" / "dist" / "opencode").is_dir())
        (call,) = self.stub.calls()
        self.assertEqual(call["env"]["XDG_CONFIG_HOME"], str(root / "harness-config"))

    def test_without_checkout_flag_nothing_is_rendered_under_output(self):
        out = self.run_bench("claude-code", "--home", self.home)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertFalse((self.out / "home" / "dist").exists())
        self.assertFalse((self.out / "harness-config").exists())
        (call,) = self.stub.calls()
        self.assertNotIn("CLAUDE_CONFIG_DIR", call["env"])
        self.assertEqual(call["env"]["CLAUDE_HOME"], self.stub.env["CLAUDE_HOME"])

    def test_checkout_run_leaves_sandboxed_homes_unchanged(self):
        roots = [
            Path(self.stub.env[key])
            for key in ("HOME", "CLAUDE_HOME", "XDG_CONFIG_HOME")
        ]
        for root in roots:
            (root / "marker.txt").parent.mkdir(parents=True, exist_ok=True)
            (root / "marker.txt").write_text("keep\n")
        before = snapshot(roots)
        out = self.run_bench("claude-code", "--from-checkout")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(snapshot(roots), before)

    def test_failed_render_stops_before_launch(self):
        bash_dir = self.box.dir / "bash-bin"
        bash_dir.mkdir()
        fake = bash_dir / "bash"
        fake.write_text(
            f"#!{sys.executable}\nimport sys\nprint('render boom: missing dependency')\nsys.exit(7)\n"
        )
        fake.chmod(0o755)
        path = f"{bash_dir}{os.pathsep}{self.stub.bin}{os.pathsep}{os.environ['PATH']}"
        out = self.run_bench("claude-code", "--from-checkout", path=path)
        self.assertEqual(out.returncode, 1)
        self.assertIn("benchmark run: checkout render failed (exit 7):", out.stderr)
        self.assertIn("render boom: missing dependency", out.stderr)
        self.assertEqual(self.stub.calls(), [])

    def test_from_checkout_with_home_is_rejected_before_any_effect(self):
        home = self.box.dir / "explicit-home"
        out = self.run_bench("claude-code", "--from-checkout", "--home", home)
        self.assertEqual(out.returncode, 2)
        self.assertFalse(self.out.exists())
        self.assertFalse(home.exists())


def snapshot(roots):
    """Content hashes and symlink targets under each root (absent roots are empty)."""
    entries = {}
    for root in roots:
        for dirpath, dirnames, filenames in os.walk(root):
            for name in dirnames + filenames:
                full = os.path.join(dirpath, name)
                if os.path.islink(full):
                    entries[full] = ("link", os.readlink(full))
                elif os.path.isfile(full):
                    digest = hashlib.sha256(Path(full).read_bytes()).hexdigest()
                    entries[full] = ("file", digest)
    return entries


def git_bytes(path, *args):
    return subprocess.run(
        ["git", "-C", str(path), *args], capture_output=True, check=True
    ).stdout


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.box = Sandbox()
        self.addCleanup(self.box.close)
        self.repo = self.box.repo

    def test_clean_checkout_has_revision_and_no_changes(self):
        head = git_bytes(self.repo, "rev-parse", "HEAD").decode().strip()
        record = bench_module.checkout_provenance(self.repo)
        self.assertEqual(record["revision"], head)
        self.assertEqual(record["changed_paths"], [])
        self.assertIsNone(record["diff_sha256"])

    def test_tracked_edit_and_untracked_file_are_both_reported(self):
        (self.repo / "README.md").write_text("changed\n")
        (self.repo / "new-file.txt").write_text("new\n")
        record = bench_module.checkout_provenance(self.repo)
        self.assertEqual(record["changed_paths"], ["README.md", "new-file.txt"])
        expected = hashlib.sha256(git_bytes(self.repo, "diff", "HEAD", "--binary")).hexdigest()
        self.assertEqual(record["diff_sha256"], expected)

    def test_untracked_only_change_has_no_tracked_diff_digest(self):
        (self.repo / "new-file.txt").write_text("new\n")
        record = bench_module.checkout_provenance(self.repo)
        self.assertEqual(record["changed_paths"], ["new-file.txt"])
        self.assertIsNone(record["diff_sha256"])

    def test_plain_directory_is_unavailable_without_raising(self):
        plain = self.box.dir / "plain"
        plain.mkdir()
        record = bench_module.checkout_provenance(plain)
        self.assertEqual(
            record,
            {"revision": "unavailable", "changed_paths": "unavailable", "diff_sha256": "unavailable"},
        )

    def test_tree_digest_follows_the_recorded_formula_and_detects_one_byte(self):
        tree = self.box.dir / "tree"
        (tree / "sub").mkdir(parents=True)
        (tree / "b.txt").write_bytes(b"bravo")
        (tree / "sub" / "a.txt").write_bytes(b"alpha")
        records = "".join(
            f"{rel}\0{hashlib.sha256(data).hexdigest()}\n"
            for rel, data in (("b.txt", b"bravo"), ("sub/a.txt", b"alpha"))
        )
        # The record stream is hashed as one sha256 over sorted relative paths.
        expected = hashlib.sha256(records.encode()).hexdigest()
        self.assertEqual(bench_module.tree_digest(tree), expected)
        (tree / "b.txt").write_bytes(b"Bravo")
        self.assertNotEqual(bench_module.tree_digest(tree), expected)

    def test_missing_or_non_directory_root_is_unavailable_not_the_empty_tree(self):
        afile = self.box.dir / "afile"
        afile.write_bytes(b"not a directory")
        for name, root in (("missing", self.box.dir / "absent"), ("file", afile)):
            with self.subTest(name):
                self.assertEqual(bench_module.tree_digest(root), "unavailable")

    @unittest.skipIf(getattr(os, "geteuid", lambda: -1)() == 0, "root reads unreadable directories")
    def test_unreadable_subdirectory_is_unavailable_not_silently_skipped(self):
        tree = self.box.dir / "tree"
        locked = tree / "locked"
        locked.mkdir(parents=True)
        (tree / "a.txt").write_bytes(b"alpha")
        (locked / "b.txt").write_bytes(b"bravo")
        locked.chmod(0)
        self.addCleanup(locked.chmod, 0o755)
        self.assertEqual(bench_module.tree_digest(tree), "unavailable")

    def test_symlink_cycle_is_bounded_and_unavailable(self):
        tree = self.box.dir / "tree"
        (tree / "sub").mkdir(parents=True)
        (tree / "a.txt").write_bytes(b"alpha")
        (tree / "sub" / "loop").symlink_to(tree, target_is_directory=True)
        self.assertEqual(bench_module.tree_digest(tree), "unavailable")


class ProvenanceRunTests(unittest.TestCase):
    """Provenance written by `run` before the harness launches."""

    setUp = RunTests.setUp
    run_bench = RunTests.run_bench
    skill_link = RunTests.skill_link

    def record(self):
        return json.loads((self.out / "provenance.json").read_text())

    def test_installed_run_writes_record_before_launch(self):
        link, resolved = self.skill_link()
        out = self.run_bench("claude-code", "--home", self.home)
        self.assertEqual(out.returncode, 0, out.stderr)
        printed = json.loads(out.stdout)
        self.assertEqual(printed["provenance"], str(self.out.resolve() / "provenance.json"))
        record = self.record()
        self.assertEqual(
            set(record),
            {"version", "written_at", "bench", "harness", "model", "repo", "checkout",
             "render", "installed_factory", "harness_versions"},
        )
        self.assertEqual(record["version"], 1)
        self.assertEqual(record["bench"], "greet-001")
        self.assertEqual(record["harness"], "claude-code")
        self.assertIsNone(record["model"])
        self.assertEqual(record["repo"], str(self.out.resolve() / "fixture-greet-001"))
        self.assertEqual(record["render"], {"mode": "installed", "digest": "none"})
        self.assertEqual(
            record["installed_factory"],
            {"skill_dir": str(resolved), "digest": bench_module.tree_digest(link)},
        )
        self.assertEqual(
            record["harness_versions"],
            {"claude": "claude 9.9.9-stub", "opencode": "opencode 9.9.9-stub"},
        )
        self.assertEqual(
            set(record["checkout"]), {"path", "revision", "changed_paths", "diff_sha256"}
        )

    def test_checkout_run_digests_its_render(self):
        out = self.run_bench("claude-code", "--from-checkout")
        self.assertEqual(out.returncode, 0, out.stderr)
        rendered = self.out.resolve() / "home" / "dist" / "claude-code"
        record = self.record()
        self.assertEqual(
            record["render"],
            {"mode": "checkout", "digest": bench_module.tree_digest(rendered)},
        )

    def test_secrets_never_reach_the_record(self):
        out = self.run_bench(
            "claude-code", "--home", self.home, env={"ANTHROPIC_API_KEY": "stub-secret"}
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertNotIn("stub-secret", (self.out / "provenance.json").read_text())

    def test_failed_harness_still_leaves_the_record(self):
        out = self.run_bench("claude-code", "--home", self.home, env={"STUB_EXIT": "5"})
        self.assertEqual(out.returncode, 1)
        self.assertTrue((self.out / "provenance.json").exists())

    def test_failed_version_probe_is_recorded_as_unavailable(self):
        out = self.run_bench(
            "claude-code", "--home", self.home, env={"STUB_VERSION_FAIL": "1"}
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(
            self.record()["harness_versions"],
            {"claude": "unavailable", "opencode": "unavailable"},
        )

    def test_absent_installed_factory_is_unavailable_and_not_granted(self):
        out = self.run_bench("claude-code", "--home", self.home)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(
            self.record()["installed_factory"],
            {"skill_dir": "unavailable", "digest": "unavailable"},
        )
        (call,) = self.stub.calls()
        self.assertFalse(any("skills" in path for path in add_dirs(call["argv"])))


class ScoreProvenanceTests(unittest.TestCase):
    """`score` attaches the run's provenance without changing pass."""

    def setUp(self):
        self.box = Sandbox()
        self.addCleanup(self.box.close)
        self.dir = self.box.dir
        self.repo = self.dir / "fixture-greet-001"

    def state(self, name="run", repo=None):
        """A copy of the passing recorded run (its verdicts sit beside state.json)."""
        folder = self.dir / name
        shutil.copytree(FIXTURES / "bench-pass", folder)
        path = folder / "state.json"
        loaded = json.loads(path.read_text())
        loaded["repo"] = str(repo or self.repo)
        path.write_text(json.dumps(loaded))
        return path

    def record(self, **changes):
        body = {"version": 1, "repo": str(self.repo), "bench": "greet-001"}
        body.update(changes)
        return body

    def score_one(self, path):
        out = bench("score", path)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertNotIn("Traceback", out.stderr)
        return json.loads(out.stdout)["scores"][0]

    def test_matching_record_is_attached_and_pass_is_unchanged(self):
        (self.dir / "provenance.json").write_text(json.dumps(self.record()))
        score = self.score_one(self.state())
        self.assertEqual(score["provenance"], self.record())
        self.assertTrue(score["pass"])

    def test_absent_malformed_or_mismatched_record_is_marked_missing(self):
        path = self.state()
        cases = {
            "absent": None,
            "malformed": "{not json",
            "mismatched": json.dumps(self.record(repo=str(self.dir / "elsewhere"))),
        }
        for name, content in cases.items():
            with self.subTest(name):
                record = self.dir / "provenance.json"
                if content is None:
                    record.unlink(missing_ok=True)
                else:
                    record.write_text(content)
                score = self.score_one(path)
                self.assertIn("missing", score["provenance"])
                self.assertTrue(score["provenance"]["missing"])
                self.assertTrue(score["pass"])

    def test_unreadable_state_is_marked_missing_alongside_failed_conditions(self):
        out = bench("score", self.dir / "absent-state.json")
        self.assertEqual(out.returncode, 0, out.stderr)
        score = json.loads(out.stdout)["scores"][0]
        self.assertIn("missing", score["provenance"])
        self.assertFalse(score["pass"])

    def test_each_state_gets_its_own_record(self):
        (self.dir / "provenance.json").write_text(json.dumps(self.record()))
        with_record = self.state("with")
        without = self.state("without", repo=self.dir / "other-repo")
        out = bench("score", with_record, without)
        self.assertEqual(out.returncode, 0, out.stderr)
        first, second = json.loads(out.stdout)["scores"]
        self.assertEqual(first["provenance"], self.record())
        self.assertIn("missing", second["provenance"])
