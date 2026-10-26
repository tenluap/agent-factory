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
            env = dict(os.environ, HOME=home, FACTORY_HOME=str(Path(home) / ".factory"))
            return subprocess.run(
                ["bash", str(INSTALL), *args],
                capture_output=True,
                text=True,
                env=env,
            )

    def test_harness_without_a_value_is_a_usage_error(self):
        out = self.run_install("--harness")
        self.assertNotEqual(out.returncode, 0, "the usage error exits non-zero")
        message = out.stderr + out.stdout
        self.assertIn("--harness", message, "the message names the offending flag")
        self.assertNotIn("unbound variable", message, "no set -u crash")


if __name__ == "__main__":
    unittest.main()
