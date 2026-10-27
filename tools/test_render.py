"""Checks for native agent output across the factory's harness adapters."""

import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

import render


class RenderHomeTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        shutil.copytree(render.ROOT / "core", self.root / "core")
        self.enterContext(patch.object(render, "ROOT", self.root))
        self.adapters = {
            name: json.loads((render.ADAPTERS / name / "adapter.json").read_text())
            for name in render.known()
        }
        env = {adapter["home"]["env"]: "" for adapter in self.adapters.values()}
        env["FACTORY_HOME"] = str(self.root / "factory-home")
        self.enterContext(patch.dict(os.environ, env))

    def test_canonical_distribution_ignores_home_overrides(self):
        for name, adapter in self.adapters.items():
            with self.subTest(harness=name):
                out = render.render(name)
                expected = {
                    path.relative_to(out): path.read_bytes()
                    for path in out.rglob("*")
                    if path.is_file()
                }
                env = {adapter["home"]["env"]: "/home/runner/.config"}
                with patch.dict(os.environ, env):
                    render.render(name)
                actual = {
                    path.relative_to(out): path.read_bytes()
                    for path in out.rglob("*")
                    if path.is_file()
                }
                self.assertEqual(actual.keys(), expected.keys())
                for path in expected:
                    self.assertEqual(actual[path], expected[path], str(path))

    def test_out_preserves_home_overrides_in_agent_paths(self):
        for name, adapter in self.adapters.items():
            if "{home}" not in adapter["skill_dir"]:
                continue
            with self.subTest(harness=name):
                home = str(self.root / "custom-home")
                out = self.root / "user-dist" / name
                env = {adapter["home"]["env"]: home}
                argv = ["render.py", name, "--out", str(out)]
                with patch.dict(os.environ, env), patch.object(sys, "argv", argv):
                    render.main()
                agents = list((out / "agents").iterdir())
                self.assertTrue(agents)
                for agent in agents:
                    self.assertIn(adapter["skill_dir"].format(home=home), agent.read_text())


class RenderAgentTests(unittest.TestCase):
    def test_ordered_permission_rules_are_valid_yaml_sequences(self):
        rules = [
            {"action": "edit", "resource": "*", "effect": "deny"},
            {"action": "subagent", "resource": "*", "effect": "deny"},
        ]
        output = render.render_agent(
            {"agent_format": "markdown"}, [("permissions", rules)], "Body\n"
        )
        self.assertEqual(
            output,
            "---\npermissions:\n"
            '  - {"action": "edit", "resource": "*", "effect": "deny"}\n'
            '  - {"action": "subagent", "resource": "*", "effect": "deny"}\n'
            "---\nBody\n",
        )

    def test_legacy_markdown_output_is_unchanged(self):
        fields = [
            ("description", "Example agent"),
            ("tools", ["read", "search", "execute"]),
            ("permission", {"edit": "deny", "task": "deny"}),
        ]
        self.assertEqual(
            render.render_agent({"agent_format": "markdown"}, fields, "Body\n"),
            "---\ndescription: Example agent\ntools: [read, search, execute]\n"
            "permission:\n  edit: deny\n  task: deny\n---\nBody\n",
        )

    def test_toml_output_is_unchanged(self):
        self.assertEqual(
            render.render_agent(
                {"agent_format": "toml"}, [("name", "factory_example")], "\nBody\n"
            ),
            "name = \"factory_example\"\ndeveloper_instructions = '''\nBody\n'''\n",
        )

    def test_toml_rejects_structured_fields(self):
        for value in ({"edit": "deny"}, ["read"]):
            with self.subTest(value=value), self.assertRaises(SystemExit):
                render.render_agent(
                    {"agent_format": "toml"}, [("tools", value)], "Body\n"
                )

    def test_opencode_roles_preserve_access_and_models(self):
        adapter = json.loads((render.ADAPTERS / "opencode/adapter.json").read_text())
        for role_file in sorted((render.ROOT / "core/roles").glob("*.md")):
            meta, body = render.frontmatter(role_file.read_text())
            with self.subTest(role=meta["name"]):
                fields = render.agent_fields(
                    adapter, meta, {"description": meta["description"]}
                )
                values = dict(fields)
                expected = [{"action": "subagent", "resource": "*", "effect": "deny"}]
                if meta["access"] == "read":
                    expected.insert(
                        0, {"action": "edit", "resource": "*", "effect": "deny"}
                    )
                self.assertEqual(values["mode"], "subagent")
                self.assertEqual(values.get("permissions"), expected)
                self.assertNotIn("permission", values)
                model = adapter["models"].get(meta["tier"], "")
                if (
                    model
                ):  # only claude-code ships models; the rest inherit the session's
                    self.assertEqual(values["model"], model)
                else:
                    self.assertNotIn("model", values)
                output = render.render_agent(adapter, fields, body)
                self.assertIn("\npermissions:\n  - {", output)

    def test_complete_opencode_distribution(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(render.ROOT / "core", root / "core")
            env = {
                "FACTORY_HOME": str(root / "factory-home"),
                "XDG_CONFIG_HOME": "~/.config",
            }
            with patch.object(render, "ROOT", root), patch.dict(os.environ, env):
                out = render.render("opencode")
            role_files = sorted((root / "core/roles").glob("*.md"))
            self.assertEqual(len(list((out / "agents").glob("*.md"))), len(role_files))
            for role_file in role_files:
                meta, _ = render.frontmatter(role_file.read_text())
                text = (out / "agents" / f"factory-{meta['name']}.md").read_text()
                self.assertIn("\nmode: subagent\npermissions:\n", text)
                rules = [
                    json.loads(line[4:])
                    for line in text.split("\n---\n", 1)[0].splitlines()
                    if line.startswith("  - ")
                ]
                actions = [rule["action"] for rule in rules]
                expected = (
                    ["edit", "subagent"] if meta["access"] == "read" else ["subagent"]
                )
                self.assertEqual(actions, expected)
            for name in render.known():
                self.assertEqual(
                    (out / "skill/references/harness" / f"{name}.md").read_bytes(),
                    (render.ADAPTERS / name / "harness.md").read_bytes(),
                )


if __name__ == "__main__":
    unittest.main()
