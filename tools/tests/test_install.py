"""Install seam tests: `install.sh` argument validation (FR-020) and the
per-user install flow (FR-001..FR-005).

Everything runs under a throwaway `HOME` so no real harness directory,
factory state or the user's checkout is touched; the committed rendered
distribution is only ever read.
"""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
INSTALL = REPO / "install.sh"
OPENCODE_DEEP = json.loads((REPO / "adapters" / "opencode" / "adapter.json").read_text())["models"]["deep"]


class InstallArgValidationTests(unittest.TestCase):
    """A missing option value is a usage error, not a crash."""

    def run_install(self, *args):
        with tempfile.TemporaryDirectory(prefix="factory-install-") as home:
            env = dict(
                os.environ,
                HOME=home,
                XDG_CONFIG_HOME=str(Path(home) / ".config"),
                FACTORY_HOME=str(Path(home) / ".factory"),
            )
            return subprocess.run(
                ["bash", str(INSTALL), *args],
                capture_output=True,
                text=True,
                env=env,
            )

    def test_opencode_install_verifies_skill_and_agents(self):
        with tempfile.TemporaryDirectory(prefix="factory-install-") as home:
            config = Path(home) / ".config"
            (Path(home) / ".factory").mkdir()
            env = dict(
                os.environ,
                HOME=home,
                XDG_CONFIG_HOME=str(config),
                FACTORY_HOME=str(Path(home) / ".factory"),
            )
            out = subprocess.run(
                ["bash", str(INSTALL), "--harness", "opencode"],
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertTrue((config / "opencode/skills/factory").is_symlink())
            installed = config / "opencode/agents"
            expected = {
                f"factory-{path.stem}.md" for path in (REPO / "core/roles").glob("*.md")
            }
            self.assertTrue(expected)
            self.assertEqual(
                {path.name for path in installed.glob("factory-*")}, expected
            )
            self.assertTrue(all((installed / name).is_symlink() for name in expected))
            self.assertIn("start a fresh OpenCode session", out.stdout)

    def test_opencode_install_fails_clearly_on_conflicting_skill_path(self):
        with tempfile.TemporaryDirectory(prefix="factory-install-") as home:
            config = Path(home) / ".config"
            (Path(home) / ".factory").mkdir()
            skill = config / "opencode/skills/factory"
            skill.parent.mkdir(parents=True)
            skill.write_text("user file")
            env = dict(
                os.environ,
                HOME=home,
                XDG_CONFIG_HOME=str(config),
                FACTORY_HOME=str(Path(home) / ".factory"),
            )
            out = subprocess.run(
                ["bash", str(INSTALL), "--harness", "opencode"],
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertNotEqual(out.returncode, 0)
            self.assertIn("resolve any existing file", out.stderr)
            self.assertEqual(skill.read_text(), "user file")

    def test_harness_without_a_value_is_a_usage_error(self):
        out = self.run_install("--harness")
        self.assertNotEqual(out.returncode, 0, "the usage error exits non-zero")
        message = out.stderr + out.stdout
        self.assertIn("--harness", message, "the message names the offending flag")
        self.assertNotIn("unbound variable", message, "no set -u crash")


class InstallSandbox:
    """Shared sandbox: a throwaway HOME + XDG tree, an installer runner and
    the committed-dist porcelain check. No test touches the real home."""

    OVER = "test-org/test-deep-model"
    CONFIG = {"models": {"opencode": {"deep": OVER}}}

    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="factory-install-")
        self.addCleanup(tmp.cleanup)
        self.home = Path(tmp.name) / "home"
        self.xdg = self.home / ".config"

    def run_install(self, *args, config=None, config_text=None, exported=True):
        """Run install.sh under the sandbox; `config` lands in the factory
        home that ${FACTORY_HOME:-~/.factory} resolves to for this run."""
        self.home.mkdir(parents=True, exist_ok=True)
        self.factory_home = self.home if exported else self.home / ".factory"
        if config_text is not None:
            self.factory_home.mkdir(parents=True, exist_ok=True)
            (self.factory_home / "config.json").write_text(config_text)
        elif config is not None:
            self.factory_home.mkdir(parents=True, exist_ok=True)
            (self.factory_home / "config.json").write_text(json.dumps(config))
        env = dict(os.environ)
        env["HOME"] = str(self.home)
        env["XDG_CONFIG_HOME"] = str(self.xdg)
        if exported:
            env["FACTORY_HOME"] = str(self.factory_home)
        else:
            env.pop("FACTORY_HOME", None)
        return subprocess.run(
            ["bash", str(INSTALL), "--harness", "opencode", *args],
            capture_output=True,
            text=True,
            env=env,
            cwd=REPO,
        )

    def dist_porcelain(self):
        return subprocess.run(
            ["git", "status", "--porcelain", "--", "dist/"],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=True,
        ).stdout


class InstallFlowTests(InstallSandbox, unittest.TestCase):
    """FR-001/FR-002/FR-004/FR-005: each selected harness is rendered into
    ${FACTORY_HOME:-~/.factory}/dist/<harness>, its skill/ and agents/* link
    from that copy, the models report matches the linked agents, a second run
    re-links cleanly, and the committed rendered distribution is untouched."""

    def assert_install_carries_overrides(self, exported):
        proc = self.run_install(config=self.CONFIG, exported=exported)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        per_user = self.factory_home / "dist" / "opencode"
        self.assertTrue(
            (per_user / "skill").is_dir(),
            "the per-user render exists in the factory home",
        )
        skill = self.xdg / "opencode" / "skills" / "factory"
        agents = self.xdg / "opencode" / "agents"
        self.assertEqual(
            skill.resolve(),
            (per_user / "skill").resolve(),
            "the skill links from the per-user copy",
        )
        linked = sorted(agents.glob("factory-*.md"))
        self.assertTrue(linked, "the agents link into the harness directory")
        for agent in linked:
            self.assertEqual(
                agent.resolve().parent,
                (per_user / "agents").resolve(),
                str(agent),
            )
        self.assertIn(
            self.OVER,
            (agents / "factory-spec-builder.md").read_text(),
            "the linked agent carries the override",
        )
        self.assertIn(
            f"spec-builder: {self.OVER}",
            proc.stdout,
            "the models report matches the linked agents",
        )
        self.assertEqual(self.dist_porcelain(), "", "the committed dist is untouched")
        again = self.run_install(config=self.CONFIG, exported=exported)
        self.assertEqual(again.returncode, 0, again.stderr + again.stdout)
        self.assertTrue(
            (agents / "factory-spec-builder.md").is_symlink(),
            "a second run re-links cleanly",
        )

    def test_exported_factory_home_overrides_reach_the_installed_agents(self):
        self.assert_install_carries_overrides(exported=True)

    def test_default_home_overrides_reach_the_installed_agents(self):
        # FR-005: config at ~/.factory, FACTORY_HOME unset
        self.assert_install_carries_overrides(exported=False)

    def test_install_without_config_reports_defaults(self):
        proc = self.run_install()
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertIn(f"spec-builder: {OPENCODE_DEEP}", proc.stdout)
        self.assertEqual(self.dist_porcelain(), "", "the committed dist is untouched")


class UninstallTests(InstallSandbox, unittest.TestCase):
    """FR-001: --uninstall removes the links it created and the per-user
    render at ${FACTORY_HOME:-~/.factory}/dist/<harness>, leaving config.json,
    pending runs and the committed rendered distribution untouched."""

    def test_uninstall_removes_its_links_and_per_user_render(self):
        proc = self.run_install(config=self.CONFIG)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        skill = self.xdg / "opencode" / "skills" / "factory"
        agents = self.xdg / "opencode" / "agents"
        config = self.factory_home / "config.json"
        pending = self.factory_home / "pending" / "keep-run.json"
        pending.parent.mkdir(parents=True, exist_ok=True)
        pending.write_text("{}\n")
        out = self.run_install("--uninstall")
        self.assertEqual(out.returncode, 0, out.stderr + out.stdout)
        self.assertFalse(
            skill.exists() or skill.is_symlink(), "the skill link is removed"
        )
        self.assertEqual(
            list(agents.glob("factory-*.md")), [], "the agent links are removed"
        )
        self.assertFalse(
            (self.factory_home / "dist" / "opencode").exists(),
            "the per-user render is removed",
        )
        self.assertTrue(config.exists(), "config.json survives")
        self.assertTrue(pending.exists(), "pending runs survive")
        self.assertEqual(self.dist_porcelain(), "", "the committed dist is untouched")


class ConfigParseGuardTests(InstallSandbox, unittest.TestCase):
    """FR-022: a config.json that does not parse aborts the install before
    anything is rendered or linked — message naming the file and the parse
    error, non-zero exit, no traceback."""

    def test_unparseable_config_aborts_the_install(self):
        proc = self.run_install(config_text="{not json")
        self.assertNotEqual(proc.returncode, 0, "the install aborts")
        message = proc.stderr + proc.stdout
        self.assertIn("config.json", message, "the message names the file")
        self.assertNotIn("Traceback", message, "no traceback reaches the user")
        self.assertFalse((self.factory_home / "dist").exists(), "nothing was rendered")
        self.assertFalse((self.xdg / "opencode").exists(), "nothing was linked")
        self.assertEqual(self.dist_porcelain(), "", "the committed dist is untouched")

    def test_wrong_shape_config_aborts_the_install_without_a_traceback(self):
        for text in ("[]", '{"models": 5}', '{"models": {"opencode": "x"}}'):
            with self.subTest(config=text):
                proc = self.run_install(config_text=text)
                self.assertNotEqual(proc.returncode, 0, "the install aborts")
                message = proc.stderr + proc.stdout
                self.assertIn("config.json", message, "the message names the file")
                self.assertNotIn("Traceback", message, "no traceback reaches the user")
                self.assertFalse((self.xdg / "opencode").exists(), "nothing was linked")


class InstallHomePolicyTests(unittest.TestCase):
    """FR-001: a missing default home ~/.factory is created; an explicitly
    set FACTORY_HOME that does not exist, is not a directory or is not
    writable fails naming the path, writing nothing, with no traceback."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="factory-install-")
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        self.home = self.tmp / "home"
        self.xdg = self.home / ".config"

    def run_install(self, factory_home, exported=True):
        self.home.mkdir(parents=True, exist_ok=True)
        env = dict(os.environ)
        env["HOME"] = str(self.home)
        env["XDG_CONFIG_HOME"] = str(self.xdg)
        if exported:
            env["FACTORY_HOME"] = str(factory_home)
        else:
            env.pop("FACTORY_HOME", None)
        return subprocess.run(
            ["bash", str(INSTALL), "--harness", "opencode"],
            capture_output=True,
            text=True,
            env=env,
            cwd=REPO,
        )

    def dist_porcelain(self):
        return subprocess.run(
            ["git", "status", "--porcelain", "--", "dist/"],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=True,
        ).stdout

    def assert_clean_failure(self, proc, path):
        self.assertNotEqual(proc.returncode, 0, "the bad home fails the install")
        self.assertIn(
            str(path), proc.stderr + proc.stdout, "the message names the path"
        )
        self.assertNotIn(
            "Traceback", proc.stderr + proc.stdout, "no traceback reaches the user"
        )
        self.assertEqual(self.dist_porcelain(), "", "the committed dist is untouched")
        self.assertFalse(
            (self.xdg / "opencode" / "agents").exists(), "nothing was linked"
        )

    def test_missing_default_home_is_created(self):
        proc = self.run_install(self.home / ".factory", exported=False)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertTrue(
            (self.home / ".factory" / "dist" / "opencode" / "skill").is_dir(),
            "the default home and the per-user render are created",
        )

    def test_missing_explicit_factory_home_fails_naming_the_path(self):
        missing = self.tmp / "missing-home"
        self.assert_clean_failure(self.run_install(missing), missing)

    def test_home_that_is_not_a_directory_fails_naming_the_path(self):
        plain_file = self.tmp / "not-a-dir"
        plain_file.write_text("not a home\n")
        self.assert_clean_failure(self.run_install(plain_file), plain_file)

    def test_unwritable_home_fails_naming_the_path(self):
        locked = self.tmp / "locked-home"
        locked.mkdir()
        locked.chmod(0o500)
        self.addCleanup(locked.chmod, 0o700)
        self.assert_clean_failure(self.run_install(locked), locked)


if __name__ == "__main__":
    unittest.main()
