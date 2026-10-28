"""Skill library layout and installer contracts."""

import re
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SKILLS = ("grilling", "domain-modeling", "pr", "ponytail", "tdd", "brainstorming")


class SkillLibraryLayoutTests(unittest.TestCase):
    def test_required_skills_have_matching_names_licenses_and_provenance(self):
        sources = (REPO / "skills/SOURCES.md").read_text()
        for name in SKILLS:
            with self.subTest(name=name):
                folder = REPO / "skills" / name
                text = (folder / "SKILL.md").read_text()
                self.assertRegex(
                    text,
                    rf"(?ms)^---\s*\n.*?^name:\s*['\"]?{re.escape(name)}['\"]?\s*$.*?^---\s*$",
                )
                self.assertTrue((folder / "LICENSE").is_file())
                self.assertRegex(
                    sources,
                    rf"(?m)^\|\s*{re.escape(name)}\s*\|\s*https://[^|]+\|\s*[^|]+\|\s*[0-9a-f]{{40}}\s*\|\s*MIT\s*\|",
                )


import os
import shutil
from unittest.mock import patch
from tools.tests import test_install


class SkillLibraryInstallTests(test_install.InstallSandbox, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.checkout = self.home.parent / "checkout"
        self.checkout.mkdir()
        for folder in ("core", "adapters", "skills"):
            shutil.copytree(REPO / folder, self.checkout / folder)
        (self.checkout / "tools").mkdir()
        shutil.copy2(REPO / "tools/render.py", self.checkout / "tools/render.py")
        shutil.copy2(REPO / "install.sh", self.checkout / "install.sh")
        self.enterContext(patch.object(test_install, "INSTALL", self.checkout / "install.sh"))
        self.enterContext(patch.dict(os.environ, {key: str(self.home / key) for key in
                          ("CLAUDE_HOME", "ZCODE_HOME", "CODEX_HOME", "COPILOT_HOME")}))
        self.root = self.xdg / "opencode/skills"

    def test_repo_links_are_idempotent_and_ignore_non_skills(self):
        for name in (".hidden", "factory"):
            folder = self.checkout / "skills" / name
            folder.mkdir()
            (folder / "SKILL.md").write_text("test")
        first = self.run_install()
        self.assertEqual(first.returncode, 0, first.stderr)
        for name in SKILLS:
            self.assertEqual((self.root / name).readlink(), self.checkout / "skills" / name)
        self.assertFalse((self.root / ".hidden").exists())
        self.assertFalse((self.root / "SOURCES.md").exists())
        self.assertIn(f"skip: {self.checkout}/skills/factory: name reserved for the factory skill", first.stdout)
        before = {p.name: p.readlink() for p in self.root.iterdir()}
        second = self.run_install()
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(before, {p.name: p.readlink() for p in self.root.iterdir()})
        for name in SKILLS:
            self.assertIn(f"linked: {self.root / name}", second.stdout)

    def test_conflicts_are_not_replaced(self):
        self.root.mkdir(parents=True)
        (self.root / "grilling").mkdir()
        outside = self.home / "outside"
        outside.mkdir()
        (self.root / "pr").symlink_to(outside)
        (self.root / "tdd").symlink_to(self.home / "missing")
        result = self.run_install()
        self.assertEqual(result.returncode, 0, result.stderr)
        for name in ("grilling", "pr", "tdd"):
            target = self.root / name
            self.assertIn(f"skip: {target} exists and is not a library link; to adopt it: ./install.sh --add-skill {target}, remove the original, re-run", result.stdout + result.stderr)
        self.assertTrue((self.root / "grilling").is_dir())
        self.assertEqual((self.root / "pr").readlink(), outside)
        self.assertEqual((self.root / "tdd").readlink(), self.home / "missing")

    def test_all_harnesses_share_agents_root(self):
        result = self.run_install("--harness", "all")
        self.assertEqual(result.returncode, 0, result.stderr)
        for name in SKILLS:
            self.assertEqual((self.home / ".agents/skills" / name).readlink(), self.checkout / "skills" / name)

    def test_stale_repo_link_is_removed(self):
        first = self.run_install()
        self.assertEqual(first.returncode, 0, first.stderr)
        shutil.rmtree(self.checkout / "skills/pr")
        result = self.run_install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.root / "pr").is_symlink())
        self.assertIn(f"removed: {self.root / 'pr'}", result.stdout)

    def test_user_layer_precedence_exclusions_and_stale_fallback(self):
        first = self.run_install()
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual((self.root / "tdd").readlink(), self.checkout / "skills/tdd")
        for name in ("personal", "tdd", ".tdd.tmp.123", "factory"):
            folder = self.factory_home / "skills" / name
            folder.mkdir(parents=True)
            (folder / "SKILL.md").write_text("test")
        second = self.run_install()
        self.assertEqual(second.returncode, 0, second.stderr)
        for name in ("personal", "tdd"):
            self.assertEqual((self.root / name).readlink(), self.factory_home / "skills" / name)
        self.assertFalse((self.root / ".tdd.tmp.123").exists())
        self.assertIn(f"skip: {self.factory_home}/skills/factory: name reserved for the factory skill", second.stdout)
        self.assertEqual((self.root / "factory").readlink(), self.factory_home / "dist/opencode/skill")
        shutil.rmtree(self.factory_home / "skills/tdd")
        third = self.run_install()
        self.assertEqual(third.returncode, 0, third.stderr)
        self.assertIn(f"removed: {self.root / 'tdd'}", third.stdout)
        self.assertEqual((self.root / "tdd").readlink(), self.checkout / "skills/tdd")

    def test_add_skill_copies_and_accepts_symlink_basename(self):
        source = self.home.parent / "different"
        source.mkdir()
        (source / "SKILL.md").write_text("---\nname: adopted\n---\ncontent\n")
        given = self.home.parent / "adopted"
        given.symlink_to(source, target_is_directory=True)
        result = self.run_install("--add-skill", str(given))
        self.assertEqual(result.returncode, 0, result.stderr)
        dest = self.factory_home / "skills/adopted"
        self.assertEqual((dest / "SKILL.md").read_text(), (source / "SKILL.md").read_text())
        self.assertIn(f"added: {dest}", result.stdout)
        self.assertEqual((self.root / "adopted").readlink(), dest)

    def test_add_skill_refusals_write_nothing(self):
        self.home.mkdir(parents=True)
        base = self.home.parent / "inputs"
        base.mkdir()
        for name, content in (("empty", None), ("no-front", "name: no-front\n"),
                              ("mismatch", "---\nname: other\n---\n"),
                              ("factory", "---\nname: factory\n---\n"),
                              ("exists", "---\nname: exists\n---\n")):
            folder = base / name
            folder.mkdir()
            if content is not None:
                (folder / "SKILL.md").write_text(content)
        existing = self.home / "skills/exists"
        existing.mkdir(parents=True)
        cases = [(str(base / "missing"), "not a local directory"),
                 ("https://example.com/skill", "not a local directory"),
                 (str(base / "empty"), "no SKILL.md"),
                 (str(base / "no-front"), "no frontmatter"),
                 (str(base / "mismatch"), "name 'other' does not match folder 'mismatch'"),
                 (str(base / "factory"), "reserved: factory"),
                 (str(base / "exists"), f"exists: {existing}")]
        before = sorted(str(p.relative_to(self.home)) for p in self.home.rglob("*"))
        for value, message in cases:
            with self.subTest(value=value):
                result = self.run_install("--add-skill", value)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn(message, result.stdout + result.stderr)
                self.assertEqual(before, sorted(str(p.relative_to(self.home)) for p in self.home.rglob("*")))
        for args in (("--add-skill",), ("--add-skill", str(base / "exists"), "--uninstall")):
            result = self.run_install(*args)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertEqual(before, sorted(str(p.relative_to(self.home)) for p in self.home.rglob("*")))

    def test_add_skill_failed_copy_cleans_temporary_directory(self):
        folder = self.home.parent / "sample"
        folder.mkdir()
        (folder / "SKILL.md").write_text("---\nname: sample\n---\n")
        bindir = self.home.parent / "bin"
        bindir.mkdir()
        cp = bindir / "cp"
        cp.write_text("#!/bin/sh\nexit 1\n")
        cp.chmod(0o755)
        with patch.dict(os.environ, {"PATH": f"{bindir}:{os.environ['PATH']}"}):
            result = self.run_install("--add-skill", str(folder))
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.factory_home / "skills/sample").exists())
        self.assertEqual(list((self.factory_home / "skills").glob(".sample.tmp.*")), [])
