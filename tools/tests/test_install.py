"""Install seam tests: `install.sh` argument validation (FR-020, S17).

The plan's declared seam covers the usage-error path only: `--harness`
with no value must print a clear usage message and exit non-zero, never
die on `set -u` with an unbound-variable crash. Everything runs under a
throwaway `HOME` so no real harness directory or factory state is touched.
"""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
INSTALL = REPO / "install.sh"


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
            expected = {path.name for path in (REPO / "dist/opencode/agents").glob("*")}
            self.assertEqual(
                {path.name for path in installed.glob("factory-*")}, expected
            )
            self.assertTrue(all((installed / name).is_symlink() for name in expected))
            self.assertIn("start a fresh OpenCode session", out.stdout)

    def test_opencode_install_fails_clearly_on_conflicting_skill_path(self):
        with tempfile.TemporaryDirectory(prefix="factory-install-") as home:
            config = Path(home) / ".config"
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


if __name__ == "__main__":
    unittest.main()
