"""`profile-record` write-path tests (spec 017): the single-writer recording.

A pending run records `profile` in state plus `<name>.profile.md` beside it; a
worktree run records into `specs/<branch>/factory/profile.md` and commits; a
re-record with a changed stack discloses the delta; a pre-profile state stays
valid; the profile survives `validate`.
"""

import json
import unittest
from pathlib import Path

from tests import Sandbox, fixture


class ProfileRecordTests(unittest.TestCase):
    def setUp(self):
        self.box = Sandbox()
        self.addCleanup(self.box.close)
        # the sandbox repo is plain: one nested Avalonia project makes detection real
        project = self.box.repo / "src" / "App"
        project.mkdir(parents=True)
        (project / "App.csproj").write_text(
            '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>'
            "<TargetFramework>net9.0</TargetFramework></PropertyGroup>"
            '<ItemGroup><PackageReference Include="Avalonia" Version="11.2.0" />'
            "</ItemGroup></Project>"
        )

    def test_pending_run_records_profile_and_sidecar(self):
        self.box.pending_run("017-a", fixture("state-v5.json"))
        out = self.box.cli("profile-record")
        self.assertEqual(out.returncode, 0, out.stderr)
        result = json.loads(out.stdout)
        self.assertEqual(result["changed"], None)
        profile = result["profile"]
        self.assertEqual([f["name"] for f in profile["frameworks"]], ["avalonia"])
        self.assertTrue(profile["ui"])
        pending = next((self.box.home / "pending").glob("*-017-a.json"))
        state = json.loads(pending.read_text())
        self.assertEqual(state["profile"]["ui"], True)
        sidecar = pending.with_name(pending.name.replace(".json", ".profile.md"))
        self.assertTrue(sidecar.is_file())
        self.assertIn("avalonia 11.2.0", sidecar.read_text())

    def test_worktree_run_commits_profile_md(self):
        self.box.worktree_run("017-b", fixture("state-v5.json"))
        out = self.box.cli("profile-record", cwd=self.box.dir / "wt-017-b")
        self.assertEqual(out.returncode, 0, out.stderr)
        result = json.loads(out.stdout)
        self.assertTrue(result["committed"], "the profile record commits")
        profile_md = (
            self.box.dir / "wt-017-b" / "specs" / "017-b" / "factory" / "profile.md"
        )
        self.assertTrue(profile_md.is_file())
        log = self.box.git("log", "--oneline", "-1", cwd=self.box.dir / "wt-017-b")
        self.assertIn("factory: profile recorded", log)

    def test_rerecord_discloses_changed_stack(self):
        self.box.pending_run("017-c", fixture("state-v5.json"))
        first = json.loads(self.box.cli("profile-record").stdout)
        # change the stack: the Avalonia project gains a react web client
        web = self.box.repo / "web"
        web.mkdir()
        (web / "package.json").write_text(
            json.dumps({"dependencies": {"react": "^19"}})
        )
        (web / "package-lock.json").touch()
        second = json.loads(self.box.cli("profile-record").stdout)
        self.assertTrue(second["changed"], "a stack change is disclosed")
        self.assertTrue(
            any(
                "javascript" in change or "react" in change or "npm" in change
                for change in second["changed"]
            ),
            second["changed"],
        )

    def test_unchanged_rerecord_discloses_nothing(self):
        self.box.pending_run("017-d", fixture("state-v5.json"))
        json.loads(self.box.cli("profile-record").stdout)
        second = json.loads(self.box.cli("profile-record").stdout)
        self.assertEqual(second["changed"], [])

    def test_state_with_profile_stays_valid(self):
        self.box.pending_run("017-e", fixture("state-v5.json"))
        json.loads(self.box.cli("profile-record").stdout)
        out = self.box.cli("validate", "--all")
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)

    def test_pre_profile_state_stays_valid(self):
        self.box.pending_run("017-f", fixture("state-v1.json"))
        out = self.box.cli("validate", "--all")
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)


if __name__ == "__main__":
    unittest.main()
