"""Model cascade and CLI tests."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "core/skills/factory/bin"))
from factory_cli import commands, models


class ResolveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / "repo"
        self.home = Path(self.temp.name) / "home"
        self.repo.mkdir()
        self.home.mkdir()
        self.project = self.repo / ".factory/config.json"
        self.user = self.home / "config.json"

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))

    def test_defaults_and_fallthrough(self):
        defaults = json.loads(
            (
                ROOT / "core/skills/factory/bin/factory_cli/adapter_models.json"
            ).read_text()
        )
        resolved = models.resolve(self.repo, self.home)
        self.assertEqual(
            resolved,
            {
                h: {t: (v, "adapter") for t, v in tiers.items()}
                for h, tiers in defaults.items()
            },
        )
        for harness in ("copilot", "zcode"):
            self.assertEqual(
                resolved[harness],
                {"deep": ("", "adapter"), "standard": ("", "adapter")},
            )
        self.write(
            self.user,
            {
                "models": {
                    "opencode": {"deep": "user-deep", "standard": "user-standard"}
                }
            },
        )
        for config in ({}, {"models": {}}, {"models": {"codex": {}}}):
            self.write(self.project, config)
            self.assertEqual(
                models.resolve(self.repo, self.home)["opencode"]["deep"],
                ("user-deep", "user"),
            )

    def test_cascade_per_tier_and_empty_strings(self):
        self.write(
            self.user,
            {
                "models": {
                    "opencode": {"deep": "user-deep", "standard": "user-standard"},
                    "codex": {"deep": ""},
                }
            },
        )
        self.write(self.project, {"models": {"opencode": {"deep": ""}}})
        result = models.resolve(self.repo, self.home)
        self.assertEqual(
            result["opencode"],
            {"deep": ("", "project"), "standard": ("user-standard", "user")},
        )
        self.assertEqual(result["codex"]["deep"], ("", "user"))
        self.assertEqual(result["codex"]["standard"][1], "adapter")

    def test_invalid_configs_name_path_and_details(self):
        cases = [
            ("{invalid", "JSON"),
            (json.dumps({"models": []}), "models"),
            (json.dumps({"models": {"opencode": []}}), "opencode"),
            (json.dumps({"models": {"opencod": {}}}), "opencod"),
            (json.dumps({"models": {"opencode": {"deeep": "x"}}}), "deeep"),
            (json.dumps({"models": {"opencode": {"deep": 1}}}), "deep"),
        ]
        for path in (self.project, self.user):
            for contents, detail in cases:
                with self.subTest(path=path, contents=contents):
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(contents)
                    with self.assertRaises(models.ModelConfigError) as caught:
                        models.resolve(self.repo, self.home)
                    message = str(caught.exception)
                    self.assertIn(str(path), message)
                    self.assertIn(detail, message)
                    if detail == "opencod":
                        self.assertIn("opencode", message)
                    if detail == "deeep":
                        self.assertIn("deep", message)
                        self.assertIn("standard", message)
                    path.unlink()

    def test_linked_worktree_uses_main_checkout(self):
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(self.repo),
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.com",
                "commit",
                "--allow-empty",
                "-qm",
                "initial",
            ],
            check=True,
        )
        worktree = Path(self.temp.name) / "worktree"
        subprocess.run(
            [
                "git",
                "-C",
                str(self.repo),
                "worktree",
                "add",
                "-qb",
                "test",
                str(worktree),
            ],
            check=True,
        )
        self.write(self.project, {"models": {"opencode": {"deep": "main-model"}}})
        (worktree / "nested").mkdir()
        repo = commands.main_repo(worktree / "nested")
        self.assertEqual(Path(repo), self.repo.resolve())
        self.assertEqual(
            models.resolve(repo, self.home)["opencode"]["deep"],
            ("main-model", "project"),
        )


class ModelsCLITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / "repo"
        self.home = Path(self.temp.name) / "home"
        self.repo.mkdir()
        self.home.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        self.project = self.repo / ".factory/config.json"
        self.user = self.home / "config.json"

    def cli(self, *args):
        return subprocess.run(
            [sys.executable, str(ROOT / "core/skills/factory/bin/factory"), *args],
            cwd=self.repo,
            env=dict(os.environ, FACTORY_HOME=str(self.home)),
            capture_output=True,
            text=True,
        )

    def test_models_table_and_json(self):
        self.user.write_text(
            json.dumps({"models": {"opencode": {"standard": "user-model"}}})
        )
        self.project.parent.mkdir()
        self.project.write_text(
            json.dumps({"models": {"opencode": {"deep": "project-model"}}})
        )
        out = self.cli("models", "--json")
        self.assertEqual(out.returncode, 0, out.stderr)
        data = json.loads(out.stdout)
        self.assertEqual(len(data), 5)
        self.assertEqual(
            data["opencode"]["deep"], {"model": "project-model", "source": "project"}
        )
        self.assertEqual(
            data["opencode"]["standard"], {"model": "user-model", "source": "user"}
        )
        table = self.cli("models")
        self.assertEqual(table.returncode, 0, table.stderr)
        self.assertEqual(len(table.stdout.splitlines()), 11)
        for harness, tiers in data.items():
            for tier, item in tiers.items():
                self.assertTrue(
                    any(
                        harness in line
                        and tier in line
                        and item["model"] in line
                        and item["source"] in line
                        for line in table.stdout.splitlines()
                    )
                )
        self.assertIn("models", self.cli().stderr)

    def test_models_reports_bad_config_with_fix(self):
        for path in (self.project, self.user):
            for contents in ("{bad", '{"models":{"opencod":{}}}'):
                with self.subTest(path=path, contents=contents):
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(contents)
                    result = self.cli("models", "--json")
                    self.assertEqual(result.returncode, 1)
                    self.assertIn(str(path) + ":", result.stderr)
                    self.assertIn(
                        "Fix the file or delete it to fall back to the next layer.",
                        result.stderr,
                    )
                    path.unlink()
