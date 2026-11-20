"""Skill library layout and installer contracts (ADR 0018)."""

import json
import os
import re
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.tests import test_install


REPO = Path(__file__).resolve().parents[2]
LIBRARY = REPO / ".agents/skills"
LICENSES = REPO / ".agents/LICENSES"
LOCK = REPO / "skills-lock.json"
# Skills the factory RESOLVEs by name and expects from the vendored library.
REQUIRED = (
    "grilling",
    "domain-modeling",
    "pr",
    "ponytail",
    "ponytail-review",
    "csharp-expert",
    "verification-before-completion",
    "tdd",
    "brainstorming",
    "impeccable",
)
# Skills the factory authors; they live in the library as local lock
# entries (ADR 0019), edited in place like every other local skill.
FIRST_PARTY = (
    "create-project-agents-file",
    "design-to-code",
    "pen-design",
    "prompt-optimiser",
)
# Accepted exceptions, decided by the maintainer when the library moved
# (ADR 0018). Keep each one named so a new case still fails.
CASE_INSENSITIVE_ONLY = set()
# markpitt/claude-skills publishes no license.
UNLICENSED_SOURCES = {"markpitt/claude-skills"}


def frontmatter_name(skill_md):
    text = skill_md.read_text(encoding="utf-8", errors="replace")
    match = re.match(r"\A---\s*\n(.*?)\n---", text, re.S)
    name = re.search(r"^name:\s*(.*?)\s*$", match.group(1), re.M) if match else None
    return name.group(1).strip().strip("'\"") if name else ""


def library_folders():
    """Frontmatter name -> folder for every library folder with a SKILL.md."""
    return {
        frontmatter_name(folder / "SKILL.md"): folder
        for folder in sorted(LIBRARY.iterdir())
        if (folder / "SKILL.md").is_file()
    }


class SkillLibraryLayoutTests(unittest.TestCase):
    def setUp(self):
        self.lock = json.loads(LOCK.read_text(encoding="utf-8"))["skills"]
        self.folders = library_folders()

    def test_every_lock_entry_has_a_folder_under_its_frontmatter_name(self):
        for name in self.lock:
            if name in CASE_INSENSITIVE_ONLY:
                continue
            with self.subTest(name=name):
                # case-sensitive: a lowercase skill.md is invisible on Linux and macOS
                self.assertTrue(
                    name in self.folders, f"no .agents/skills/*/SKILL.md named {name!r}"
                )

    def test_required_skills_are_vendored(self):
        for name in REQUIRED:
            with self.subTest(name=name):
                self.assertIn(name, self.lock)
                self.assertEqual(self.folders[name].name, name)

    def test_every_source_ships_its_license(self):
        # Either one file per upstream in .agents/LICENSES, or a license in
        # every skill folder vendored from that upstream.
        by_source = {}
        for name, entry in self.lock.items():
            if entry.get("sourceType") == "local":
                continue  # the maintainer's own skills; no upstream license
            by_source.setdefault(entry["source"], []).append(name)
        for source, names in sorted(by_source.items()):
            if source in UNLICENSED_SOURCES:
                continue
            with self.subTest(source=source):
                shared = LICENSES / (source.replace("/", "-") + ".txt")
                per_skill = all(
                    any(
                        p.name.upper().startswith("LICENSE")
                        for p in self.folders[n].iterdir()
                    )
                    for n in names
                    if n in self.folders
                )
                self.assertTrue(
                    shared.is_file() or per_skill,
                    f"{source}: add {shared.relative_to(REPO)} (skills: {', '.join(names)})",
                )

    def test_local_skills_are_edited_in_place(self):
        # A local entry's source is the library itself, so its folder is the
        # original: never a copy of a path outside the checkout.
        local = {n: e for n, e in self.lock.items() if e.get("sourceType") == "local"}
        for name, entry in local.items():
            with self.subTest(name=name):
                self.assertEqual(entry["source"], ".agents/skills")
                self.assertEqual(self.folders[name].name, name)

    def test_exceptions_are_still_needed(self):
        for name in CASE_INSENSITIVE_ONLY:
            with self.subTest(name=name):
                self.assertIn(name, self.lock)
                self.assertNotIn(name, self.folders)
        sources = {entry["source"] for entry in self.lock.values()}
        for source in UNLICENSED_SOURCES:
            with self.subTest(source=source):
                self.assertIn(source, sources)
                self.assertFalse(
                    (LICENSES / (source.replace("/", "-") + ".txt")).exists()
                )

    def test_speckit_skills_stay_project_local(self):
        # `specify init` owns them per repository; linking a copy into every
        # harness would shadow its RESOLVE fallbacks.
        self.assertEqual([n for n in self.lock if n.startswith("speckit-")], [])

    def test_factory_skills_are_local_library_entries(self):
        # The factory-authored skills moved out of core/skills/ (ADR 0019):
        # lock-owned local entries, so every harness links them like any
        # vendored skill, and `skills update` skips them.
        for name in FIRST_PARTY:
            with self.subTest(name=name):
                self.assertIn(name, self.lock)
                self.assertEqual(self.lock[name]["sourceType"], "local")
                self.assertEqual(self.lock[name]["source"], ".agents/skills")
                self.assertEqual(self.folders[name].name, name)
                self.assertEqual(
                    frontmatter_name(self.folders[name] / "SKILL.md"), name
                )
        self.assertFalse((REPO / "skills/SOURCES.md").exists())


def write_skill(folder, name=None, extra=""):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "SKILL.md").write_text(
        f"---\nname: {name or folder.name}\n{extra}---\nbody\n"
    )


class SkillLibraryInstallTests(test_install.InstallSandbox, unittest.TestCase):
    """Installer behaviour against a synthetic checkout library."""

    VENDORED = ("grilling", "pr", "tdd", "ponytail")

    def setUp(self):
        super().setUp()
        self.checkout = self.home.parent / "checkout"
        self.checkout.mkdir()
        for folder in ("core", "adapters", "plugins"):
            shutil.copytree(REPO / folder, self.checkout / folder)
        (self.checkout / "tools").mkdir()
        shutil.copy2(REPO / "tools/render.py", self.checkout / "tools/render.py")
        shutil.copy2(REPO / "install.sh", self.checkout / "install.sh")
        self.lib = self.checkout / ".agents/skills"
        for name in self.VENDORED:
            write_skill(self.lib / name)
        write_skill(self.lib / "x-money-guide", "X Money guide")
        write_skill(self.lib / "speckit-plan")  # not owned by the lock
        (self.lib / "notes").mkdir()  # no SKILL.md
        self.write_lock(
            *self.VENDORED, "X Money guide", local=("design-to-code", "pen-design")
        )
        write_skill(self.lib / "design-to-code")
        write_skill(self.lib / "pen-design")
        self.enterContext(
            patch.object(test_install, "INSTALL", self.checkout / "install.sh")
        )
        self.enterContext(
            patch.dict(
                os.environ,
                {
                    key: str(self.home / key)
                    for key in (
                        "CLAUDE_HOME",
                        "ZCODE_HOME",
                        "CODEX_HOME",
                        "COPILOT_HOME",
                    )
                },
            )
        )
        self.root = self.xdg / "opencode/skills"
        self.factory_home = self.home  # run_install exports FACTORY_HOME=$HOME

    def write_lock(self, *names, local=()):
        skills = {
            name: {
                "source": "owner/repo",
                "sourceType": "github",
                "skillPath": f"skills/{name}/SKILL.md",
                "computedHash": "0",
            }
            for name in names
        }
        for name in local:
            skills[name] = {"source": ".agents/skills", "sourceType": "local"}
        (self.checkout / "skills-lock.json").write_text(
            json.dumps({"version": 1, "skills": skills}, indent=2)
        )

    def ok(self, *args):
        result = self.run_install(*args)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def test_locked_folders_link_idempotently_and_others_are_skipped(self):
        write_skill(self.lib / "factory")
        write_skill(self.lib / ".hidden")
        self.write_lock(
            *self.VENDORED,
            "X Money guide",
            "factory",
            ".hidden",
            local=("design-to-code", "pen-design"),
        )
        first = self.ok()
        for name in self.VENDORED:
            self.assertEqual((self.root / name).readlink(), self.lib / name)
        # the link name is the folder, not the frontmatter name
        self.assertEqual(
            (self.root / "x-money-guide").readlink(), self.lib / "x-money-guide"
        )
        self.assertFalse((self.root / "speckit-plan").exists())
        self.assertIn("skip: speckit-plan: not in skills-lock.json", first.stdout)
        for name in ("notes", ".hidden"):
            self.assertFalse((self.root / name).exists())
        self.assertIn(
            f"skip: {self.lib}/factory: name reserved for the factory skill",
            first.stdout,
        )
        self.assertEqual(
            (self.root / "factory").readlink(),
            self.factory_home / "dist/opencode/skill",
        )
        for name in ("design-to-code", "pen-design"):
            self.assertEqual((self.root / name).readlink(), self.lib / name)
        before = {p.name: p.readlink() for p in self.root.iterdir()}
        second = self.ok()
        self.assertEqual(before, {p.name: p.readlink() for p in self.root.iterdir()})
        for name in self.VENDORED:
            self.assertIn(f"linked: {self.root / name}", second.stdout)

    def test_conflicts_are_not_replaced(self):
        self.root.mkdir(parents=True)
        (self.root / "grilling").mkdir()
        outside = self.home / "outside"
        outside.mkdir()
        (self.root / "pr").symlink_to(outside)
        (self.root / "tdd").symlink_to(self.home / "missing")
        result = self.ok()
        for name in ("grilling", "pr", "tdd"):
            target = self.root / name
            self.assertIn(
                f"skip: {target} exists and is not a library link; to adopt it: ./install.sh --add-skill {target}, remove the original, re-run",
                result.stdout + result.stderr,
            )
        self.assertTrue((self.root / "grilling").is_dir())
        self.assertEqual((self.root / "pr").readlink(), outside)
        self.assertEqual((self.root / "tdd").readlink(), self.home / "missing")

    def test_all_harnesses_share_agents_root(self):
        self.ok("--harness", "all")
        for name in self.VENDORED:
            self.assertEqual(
                (self.home / ".agents/skills" / name).readlink(), self.lib / name
            )

    def test_removed_folder_and_dropped_lock_entry_unlink(self):
        self.ok()
        shutil.rmtree(self.lib / "pr")
        self.write_lock(
            "grilling",
            "ponytail",
            "X Money guide",
            local=("design-to-code", "pen-design"),
        )  # tdd dropped, folder kept
        result = self.ok()
        for name in ("pr", "tdd"):
            self.assertFalse((self.root / name).is_symlink())
            self.assertIn(f"removed: {self.root / name}", result.stdout)
        self.assertIn("skip: tdd: not in skills-lock.json", result.stdout)
        self.assertTrue((self.root / "grilling").is_symlink())

    def test_unparseable_lock_aborts_before_linking(self):
        (self.checkout / "skills-lock.json").write_text("{not json")
        result = self.run_install()
        self.assertEqual(result.returncode, 2)
        self.assertIn(
            f"error: {self.checkout}/skills-lock.json does not parse:", result.stderr
        )
        self.assertFalse(self.root.exists())

    def test_user_layer_precedence_exclusions_and_stale_fallback(self):
        self.ok()
        self.assertEqual((self.root / "tdd").readlink(), self.lib / "tdd")
        for name in ("personal", "tdd", ".tdd.tmp.123", "factory"):
            write_skill(self.factory_home / "skills" / name)
        second = self.ok()
        for name in ("personal", "tdd"):
            self.assertEqual(
                (self.root / name).readlink(), self.factory_home / "skills" / name
            )
        self.assertFalse((self.root / ".tdd.tmp.123").exists())
        self.assertIn(
            f"skip: {self.factory_home}/skills/factory: name reserved for the factory skill",
            second.stdout,
        )
        self.assertEqual(
            (self.root / "factory").readlink(),
            self.factory_home / "dist/opencode/skill",
        )
        shutil.rmtree(self.factory_home / "skills/tdd")
        third = self.ok()
        self.assertIn(f"removed: {self.root / 'tdd'}", third.stdout)
        self.assertEqual((self.root / "tdd").readlink(), self.lib / "tdd")

    def test_mirror_follows_the_lock_and_does_not_shadow_vendored_links(self):
        (self.factory_home / "skills").mkdir(parents=True)
        self.ok()
        mirror = self.factory_home / "skills"
        for name in (*self.VENDORED, "x-money-guide"):
            self.assertEqual((mirror / name).readlink(), self.lib / name)
        self.assertFalse((mirror / "speckit-plan").exists())
        # A second harness installed after the mirror exists still links
        # every vendored skill from the library, not from the mirror.
        self.ok("--harness", "claude-code")
        for name in self.VENDORED:
            self.assertEqual(
                (self.home / "CLAUDE_HOME/skills" / name).readlink(), self.lib / name
            )
        self.write_lock(
            "grilling",
            "pr",
            "ponytail",
            "X Money guide",
            local=("design-to-code", "pen-design"),
        )
        result = self.ok()
        self.assertFalse((mirror / "tdd").is_symlink())
        self.assertIn(f"pruned: {mirror / 'tdd'} (stale link)", result.stdout)

    def test_links_into_the_superseded_skills_folder_migrate(self):
        legacy = self.checkout / "skills"
        write_skill(legacy / "grilling")  # still present: live legacy link
        self.root.mkdir(parents=True)
        (self.root / "grilling").symlink_to(legacy / "grilling")
        (self.root / "pr").symlink_to(legacy / "pr")  # dangling legacy link
        (self.root / "gone").symlink_to(legacy / "gone")
        mirror = self.factory_home / "skills"
        mirror.mkdir(parents=True)
        (mirror / "grilling").symlink_to(legacy / "grilling")
        (mirror / "gone").symlink_to(legacy / "gone")
        result = self.ok()
        for name in ("grilling", "pr"):
            self.assertEqual((self.root / name).readlink(), self.lib / name)
        self.assertFalse((self.root / "gone").is_symlink())
        self.assertIn(f"removed: {self.root / 'gone'}", result.stdout)
        self.assertEqual((mirror / "grilling").readlink(), self.lib / "grilling")
        self.assertFalse((mirror / "gone").is_symlink())

    def test_add_skill_copies_and_accepts_symlink_basename(self):
        source = self.home.parent / "different"
        source.mkdir()
        (source / "SKILL.md").write_text("---\nname: adopted\n---\ncontent\n")
        given = self.home.parent / "adopted"
        given.symlink_to(source, target_is_directory=True)
        result = self.ok("--add-skill", str(given))
        dest = self.factory_home / "skills/adopted"
        self.assertEqual(
            (dest / "SKILL.md").read_text(), (source / "SKILL.md").read_text()
        )
        self.assertIn(f"added: {dest}", result.stdout)
        self.assertEqual((self.root / "adopted").readlink(), dest)

    def test_add_skill_refusals_write_nothing(self):
        self.home.mkdir(parents=True)
        base = self.home.parent / "inputs"
        base.mkdir()
        for name, content in (
            ("empty", None),
            ("no-front", "name: no-front\n"),
            ("mismatch", "---\nname: other\n---\n"),
            ("factory", "---\nname: factory\n---\n"),
            ("exists", "---\nname: exists\n---\n"),
        ):
            folder = base / name
            folder.mkdir()
            if content is not None:
                (folder / "SKILL.md").write_text(content)
        existing = self.home / "skills/exists"
        existing.mkdir(parents=True)
        cases = [
            (str(base / "missing"), "not a local directory"),
            ("https://example.com/skill", "not a local directory"),
            (str(base / "empty"), "no SKILL.md"),
            (str(base / "no-front"), "no frontmatter"),
            (str(base / "mismatch"), "name 'other' does not match folder 'mismatch'"),
            (str(base / "factory"), "reserved: factory"),
            (str(base / "exists"), f"exists: {existing}"),
        ]
        before = sorted(str(p.relative_to(self.home)) for p in self.home.rglob("*"))
        for value, message in cases:
            with self.subTest(value=value):
                result = self.run_install("--add-skill", value)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn(message, result.stdout + result.stderr)
                self.assertEqual(
                    before,
                    sorted(str(p.relative_to(self.home)) for p in self.home.rglob("*")),
                )
        for args in (
            ("--add-skill",),
            ("--add-skill", str(base / "exists"), "--uninstall"),
        ):
            result = self.run_install(*args)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertEqual(
                before,
                sorted(str(p.relative_to(self.home)) for p in self.home.rglob("*")),
            )

    def test_add_skill_failed_copy_cleans_temporary_directory(self):
        folder = self.home.parent / "sample"
        write_skill(folder)
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

    def test_uninstall_removes_only_library_links_in_shared_root(self):
        self.home.mkdir(parents=True)
        write_skill(self.home / "skills/personal")
        root = self.home / ".agents/skills"
        root.mkdir(parents=True)
        (root / "real-dir").mkdir()
        (root / "real-file").write_text("keep")
        (root / "outside").symlink_to(self.home / "missing")
        self.ok("--harness", "copilot")
        self.assertTrue((root / "personal").is_symlink())
        result = self.ok("--harness", "codex", "--uninstall")
        for name in (*self.VENDORED, "personal"):
            self.assertFalse((root / name).is_symlink())
            self.assertIn(f"removed: {root / name}", result.stdout)
        self.assertTrue((root / "real-dir").is_dir())
        self.assertEqual((root / "real-file").read_text(), "keep")
        self.assertEqual((root / "outside").readlink(), self.home / "missing")
        self.assertTrue((self.home / "skills/personal").is_dir())
        for name in self.VENDORED:
            self.assertTrue((self.lib / name / "SKILL.md").is_file())


if __name__ == "__main__":
    unittest.main()
