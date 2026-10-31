"""`factory detect` / `profile-record` (spec 017): marker-file stack detection.

The profile is orientation, never contract: detection never raises on repo
content, unknown markers are disclosed, and the write path records the profile
through the single writer with a changed-stack disclosure on re-record.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[2] / "core" / "skills" / "factory" / "bin")
)

from factory_cli import detect  # noqa: E402


def make_repo(files):
    root = Path(tempfile.mkdtemp())
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if content is None:
            path.touch()
        else:
            path.write_text(content)
    return root


AVALONIA_CSPROJ = (
    '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>'
    "<TargetFramework>net9.0</TargetFramework></PropertyGroup><ItemGroup>"
    '<PackageReference Include="Avalonia" Version="11.2.0" />'
    "</ItemGroup></Project>"
)

PLAIN_CSPROJ = (
    '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>'
    "<TargetFrameworks>net8.0;net9.0</TargetFrameworks></PropertyGroup>"
    "</Project>"
)


class DetectionTests(unittest.TestCase):
    def test_avalonia_nested_project(self):
        root = make_repo({"src/App/App.csproj": AVALONIA_CSPROJ})
        profile = detect.detect(root)
        self.assertEqual([l["name"] for l in profile["languages"]], ["csharp"])
        self.assertEqual(profile["languages"][0]["version"], "net9.0")
        self.assertEqual([f["name"] for f in profile["frameworks"]], ["avalonia"])
        self.assertTrue(profile["ui"])
        self.assertFalse(profile["monorepo"])
        self.assertEqual(profile["projects"], ["src/App/App.csproj"])
        self.assertEqual(
            profile["commands"]["build"],
            {"value": "dotnet build", "source": "detected", "manager": "dotnet"},
        )
        self.assertEqual(detect.validate_profile(profile), [])

    def test_plain_csproj_no_ui(self):
        root = make_repo({"Lib/Lib.csproj": PLAIN_CSPROJ})
        profile = detect.detect(root)
        self.assertEqual(profile["languages"][0]["version"], "net8.0")
        self.assertEqual(profile["frameworks"], [])
        self.assertFalse(profile["ui"])

    def test_node_typescript_with_pnpm_workspace(self):
        root = make_repo(
            {
                "package.json": json.dumps(
                    {
                        "dependencies": {"react": "^19.0.0"},
                        "devDependencies": {"typescript": "^5"},
                    }
                ),
                "tsconfig.json": None,
                "pnpm-lock.yaml": None,
                "pnpm-workspace.yaml": 'packages:\n  - "apps/*"',
            }
        )
        profile = detect.detect(root)
        self.assertEqual([l["name"] for l in profile["languages"]], ["typescript"])
        self.assertIn("react", [f["name"] for f in profile["frameworks"]])
        self.assertTrue(profile["ui"])
        self.assertTrue(profile["monorepo"])
        managers = {m["name"]: m for m in profile["package_managers"]}
        self.assertTrue(managers["pnpm"]["primary"])
        self.assertIn("pnpm-lock.yaml", managers["pnpm"]["lockfiles"])

    def test_mixed_stack_discloses_and_picks_one_primary(self):
        root = make_repo(
            {
                "package.json": json.dumps({"dependencies": {"express": "^4.19.0"}}),
                "dotnet/Lib.csproj": AVALONIA_CSPROJ,
            }
        )
        profile = detect.detect(root)
        managers = {m["name"]: m for m in profile["package_managers"]}
        self.assertIn("npm", managers)
        self.assertIn("dotnet", managers)
        primaries = [m for m in profile["package_managers"] if m["primary"]]
        self.assertEqual(len(primaries), 1)
        self.assertTrue(profile["notes"], "a mixed stack is disclosed in notes")
        self.assertTrue(any("mixed" in note for note in profile["notes"]))

    def test_python_frameworks_from_both_manifests(self):
        root = make_repo(
            {
                "api/pyproject.toml": '[project]\ndependencies = ["fastapi>=0.115"]',
                "tools/requirements.txt": "flask==3.0.0\n",
            }
        )
        profile = detect.detect(root)
        self.assertEqual([l["name"] for l in profile["languages"]], ["python"])
        self.assertEqual(
            sorted(f["name"] for f in profile["frameworks"]), ["fastapi", "flask"]
        )
        self.assertFalse(profile["ui"])

    def test_go_version_from_directive(self):
        root = make_repo({"go.mod": "module example\n\ngo 1.23.0\n"})
        profile = detect.detect(root)
        self.assertEqual(profile["languages"][0]["name"], "go")
        self.assertEqual(profile["languages"][0]["version"], "1.23.0")

    def test_unknown_markers_listed_never_fatal(self):
        root = make_repo({"Makefile": "all:\n\techo hi\n", "weird.proj": "???"})
        profile = detect.detect(root)
        self.assertEqual(profile["languages"], [])
        self.assertEqual(profile["frameworks"], [])
        self.assertEqual(profile["commands"], {})
        self.assertEqual(detect.validate_profile(profile), [])

    def test_empty_repo_valid_empty_profile(self):
        root = make_repo({})
        profile = detect.detect(root)
        self.assertEqual(detect.validate_profile(profile), [])
        markdown = detect.render_markdown(profile)
        self.assertIn("Languages:", markdown)

    def test_node_modules_ignored(self):
        root = make_repo(
            {
                "package.json": json.dumps({"dependencies": {"vue": "^3.4.0"}}),
                "node_modules/vue/package.json": json.dumps(
                    {"dependencies": {"react": "^18.0.0"}}
                ),
            }
        )
        profile = detect.detect(root)
        self.assertEqual(profile["projects"], ["package.json"])
        self.assertEqual([f["name"] for f in profile["frameworks"]], ["vue"])

    def test_validate_rejects_two_primaries(self):
        profile = {
            "languages": [],
            "frameworks": [],
            "package_managers": [
                {"name": "a", "primary": True, "evidence": []},
                {"name": "b", "primary": True, "evidence": []},
            ],
            "ui": False,
            "monorepo": False,
            "projects": [],
            "commands": {},
            "unknown_markers": [],
            "notes": [],
            "detected_at": "2026-01-01T00:00:00Z",
        }
        problems = detect.validate_profile(profile)
        self.assertTrue(any("primary" in p["reason"] for p in problems))

    def test_markdown_renders_managers_and_commands(self):
        root = make_repo({"src/App/App.csproj": AVALONIA_CSPROJ})
        markdown = detect.render_markdown(detect.detect(root))
        self.assertIn("csharp net9.0", markdown)
        self.assertIn("avalonia 11.2.0", markdown)
        self.assertIn("dotnet (primary)", markdown)
        self.assertIn("dotnet build", markdown)


if __name__ == "__main__":
    unittest.main()
