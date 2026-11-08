"""Model cascade and CLI tests."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "core/skills/factory/bin"))
from factory_cli import commands, models
from . import Sandbox, fixture


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

    def test_refuses_symlink_special_and_oversized_configs(self):
        for path in (self.project, self.user):
            path.parent.mkdir(parents=True, exist_ok=True)
            target = self.repo / "target"
            target.write_text("{}")
            path.symlink_to(target)
            with self.assertRaises(models.ModelConfigError):
                models.resolve(self.repo, self.home)
            path.unlink()
            if hasattr(os, "mkfifo"):  # no FIFOs on Windows
                os.mkfifo(path)
                with self.assertRaises(models.ModelConfigError):
                    models.resolve(self.repo, self.home)
                path.unlink()
            path.write_bytes(b" " * (1024 * 1024 + 1))
            with self.assertRaises(models.ModelConfigError):
                models.resolve(self.repo, self.home)
            path.unlink()

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

    def test_refuses_control_character_model_values(self):
        for value in ("bad\x1b[31m", "x\x7f", "line\nbreak", "null\x00"):
            with self.subTest(value=repr(value)):
                self.write(
                    self.project,
                    {"models": {"opencode": {"deep": value}}},
                )
                with self.assertRaises(models.ModelConfigError) as caught:
                    models.resolve(self.repo, self.home)
                message = str(caught.exception)
                self.assertIn(str(self.project), message)
                self.assertIn("deep", message)
                self.assertIn("control", message)

    def test_table_sanitizes_control_characters(self):
        resolved = {
            "opencode": {
                "deep": ("esc\x1b]52" + "b" + "\x07gone", "user"),
                "standard": ("ok", "adapter"),
            }
        }
        table = models.report(resolved)
        for line in table.splitlines():
            self.assertNotRegex(line, r"[\x00-\x1f\x7f]")
        self.assertIn("ok", table)

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

    def test_init_seeds_effective_values_and_preserves_global_config(self):
        original = b'{"models": {"opencode": {"deep": "my-model"}}}\n'
        self.user.write_bytes(original)
        before = json.loads(self.cli("models", "--json").stdout)
        result = self.cli("init")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("unverified until", result.stdout.lower())
        self.assertIn("user", result.stdout)
        self.assertIn("adapter", result.stdout)
        for harness in ("copilot", "zcode"):
            self.assertTrue(
                any(
                    harness in line and "adapter" in line
                    for line in result.stdout.splitlines()
                )
            )
        self.assertEqual(self.user.read_bytes(), original)
        raw = self.project.read_text()
        seeded = json.loads(raw)
        self.assertEqual(raw, json.dumps(seeded, indent=2, sort_keys=True) + "\n")
        self.assertEqual(set(seeded["models"]), set(before))
        after = json.loads(self.cli("models", "--json").stdout)
        for harness, tiers in before.items():
            self.assertEqual(set(seeded["models"][harness]), {"deep", "standard"})
            for tier, item in tiers.items():
                self.assertEqual(seeded["models"][harness][tier], item["model"])
                self.assertEqual(
                    after[harness][tier], {"model": item["model"], "source": "project"}
                )
        readme = (self.project.parent / "config.README.md").read_text()
        for phrase in (
            "models",
            "deep",
            "standard",
            "project",
            "user",
            "adapter",
            "restore",
            "my-model",
        ):
            self.assertIn(phrase, readme.lower())
        saved = self.project.read_bytes()
        for remove_readme in (False, True):
            if remove_readme:
                (self.project.parent / "config.README.md").unlink()
            refused = self.cli("init")
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn(str(self.project), refused.stderr)
            self.assertEqual(self.project.read_bytes(), saved)

    def test_init_replaces_stale_readme_and_accepts_empty_directory(self):
        self.project.parent.mkdir()
        readme = self.project.parent / "config.README.md"
        readme.write_text("stale")
        result = self.cli("init")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.project.exists())
        self.assertNotEqual(readme.read_text(), "stale")
        self.project.unlink()
        readme.unlink()
        result = self.cli("init")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_init_rejects_malformed_user_config(self):
        self.user.write_text("{bad")
        result = self.cli("init")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(str(self.user), result.stderr)
        self.assertFalse(self.project.exists())

    def test_init_refuses_symlinked_factory_directory(self):
        target = self.repo / "outside"
        target.mkdir()
        readme = target / "config.README.md"
        readme.write_text("important")
        self.project.parent.symlink_to(target, target_is_directory=True)
        result = self.cli("init")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(".factory", result.stderr)
        self.assertEqual(readme.read_text(), "important")
        self.assertFalse((target / "config.json").exists())


class InitPublishTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / "repo"
        self.home = Path(self.temp.name) / "home"
        self.repo.mkdir()
        self.home.mkdir()
        self.factory = self.repo / ".factory"
        self.config = self.factory / "config.json"

    def leftovers(self):
        return [n for n in os.listdir(self.factory) if n.startswith(".factory-")]

    def test_publish_race_refuses_without_clobber(self):
        real_link = os.link

        def racing_link(src, dst, **kwargs):
            # dir_fd-relative names on POSIX, full paths where dir_fd is unsupported
            if os.path.basename(dst) == "config.json":
                fd = os.open(
                    dst,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                    0o600,
                    dir_fd=kwargs.get("dst_dir_fd"),
                )
                with os.fdopen(fd, "wb") as other:
                    other.write(b"other writer")
            return real_link(src, dst, **kwargs)

        with mock.patch.object(models.os, "link", racing_link):
            with self.assertRaises(FileExistsError) as caught:
                models.init(self.repo, self.home)
        self.assertIn(str(self.config), str(caught.exception))
        self.assertEqual(self.config.read_bytes(), b"other writer")
        self.assertFalse((self.factory / "config.README.md").exists())
        self.assertEqual(self.leftovers(), [])

    def test_readme_failure_rolls_back_and_converts_oserror(self):
        real_link = os.link

        def failing_link(src, dst, **kwargs):
            if os.path.basename(dst) == "config.README.md":
                raise OSError("disk full")
            return real_link(src, dst, **kwargs)

        with mock.patch.object(models.os, "link", failing_link):
            with self.assertRaises(models.ModelConfigError) as caught:
                models.init(self.repo, self.home)
        self.assertIn(str(self.factory), str(caught.exception))
        self.assertIn("disk full", str(caught.exception))
        self.assertFalse(self.config.exists())
        self.assertFalse((self.factory / "config.README.md").exists())
        self.assertEqual(self.leftovers(), [])


class ModelsRecordTests(unittest.TestCase):
    def test_records_pending_and_worktree_with_resume_delta(self):
        box = Sandbox()
        self.addCleanup(box.close)
        block = {
            "resolved": {"deep": "d", "standard": "s"},
            "source": {"deep": "project", "standard": "adapter"},
        }
        pending = box.pending_run("models", fixture("state-v3.json"))
        out = box.cli(
            "models-record", "--from", box.write_temp("block.json", json.dumps(block))
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(json.loads(pending.read_text())["models"], block)
        self.assertIsNone(json.loads(out.stdout)["previous"])
        pending.unlink()
        wt = box.worktree_run("040-models", fixture("state-v3.json"))
        state_path = wt / "specs/040-models/factory/state.json"
        out = box.cli(
            "models-record",
            "--from",
            box.write_temp("block.json", json.dumps(block)),
            cwd=wt,
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(json.loads(state_path.read_text())["models"], block)
        changed = {
            "resolved": {"deep": "new", "standard": "s"},
            "source": {"deep": "user", "standard": "adapter"},
        }
        out = box.cli(
            "models-record",
            "--from",
            box.write_temp("changed.json", json.dumps(changed)),
            cwd=wt,
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(json.loads(out.stdout)["previous"], block)
        self.assertEqual(json.loads(out.stdout)["current"], changed)
        self.assertEqual(box.git("status", "--porcelain", cwd=wt).strip(), "")
        for payload in (
            "{bad",
            json.dumps({"resolved": {}, "source": {}}),
            json.dumps(
                {
                    "resolved": block["resolved"],
                    "source": {"deep": "other", "standard": "user"},
                }
            ),
        ):
            before = state_path.read_bytes()
            out = box.cli(
                "models-record",
                "--from",
                box.write_temp("bad.json", payload),
                cwd=wt,
            )
            self.assertNotEqual(out.returncode, 0)
            self.assertEqual(state_path.read_bytes(), before)

    def test_models_record_reads_stdin_and_refuses_inline_json(self):
        box = Sandbox()
        self.addCleanup(box.close)
        adversarial = "x'$(touch factory-sec1-marker)'"
        block = {
            "resolved": {"deep": adversarial, "standard": "s"},
            "source": {"deep": "project", "standard": "adapter"},
        }
        wt = box.worktree_run("040-sec1", fixture("state-v3.json"))
        out = box.cli("models-record", input=json.dumps(block), cwd=wt)
        self.assertEqual(out.returncode, 0, out.stderr)
        state_path = wt / "specs/040-sec1/factory/state.json"
        recorded = json.loads(state_path.read_text())["models"]
        self.assertEqual(recorded, block)
        self.assertEqual(recorded["resolved"]["deep"], adversarial)
        self.assertFalse((box.dir / "factory-sec1-marker").exists())
        inline = box.cli("models-record", json.dumps(block), cwd=wt)
        self.assertEqual(inline.returncode, 5, inline.stderr)
        self.assertIn("no inline JSON", inline.stderr)
        self.assertEqual(json.loads(state_path.read_text())["models"], recorded)

    def test_models_record_from_path_errors(self):
        box = Sandbox()
        self.addCleanup(box.close)
        box.pending_run("models", fixture("state-v3.json"))
        missing = box.cli("models-record", "--from", str(box.dir / "nope.json"))
        self.assertEqual(missing.returncode, 5, missing.stderr)
        self.assertIn("nope.json", missing.stderr)
