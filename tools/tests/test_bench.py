"""Benchmark score/compare public CLI seams; no live harness or token cost."""

import json
import os
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
            "CLAUDE_HOME": str(box.dir / "claude-home"),
            "XDG_CONFIG_HOME": str(box.dir / "xdg"),
            "FACTORY_HOME": str(box.dir / "factory-home"),
            "STUB_RECORD": str(self.record),
        }

    def bench(self, *args, path=None):
        env = dict(os.environ)
        for key in ("CLAUDE_CONFIG_DIR", "FACTORY_HARNESS", "ANTHROPIC_API_KEY"):
            env.pop(key, None)
        env.update(self.env, PATH=path or f"{self.bin}{os.pathsep}{os.environ['PATH']}")
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

    def run_bench(self, harness, *extra, out=None, path=None):
        return self.stub.bench(
            "--harness", harness, "--out", out or self.out, *extra, path=path
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
