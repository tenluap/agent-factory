"""Model-policy seam tests over `tools/render.py` render output (FR-015).

Exactly one adapter ships models (claude-code opus/sonnet); personal provider
IDs ship nowhere; `${FACTORY_HOME}/config.json` overrides reach the rendered
agents only when FACTORY_HOME is set explicitly, so the committed dist stays
machine-independent; the README statement matches `adapters/`.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ADAPTERS = REPO / "adapters"
DIST = REPO / "dist"
HARNESSES = ("claude-code", "codex", "copilot", "opencode", "zcode")
PERSONAL_IDS = ("xiaomi-token-plan-sgp", "mimo-v2.6-pro")


def render(harness, config=None):
    """Render one harness; FACTORY_HOME points at a temp home holding `config`."""
    home = tempfile.mkdtemp(prefix="factory-render-home-")
    env = dict(os.environ)
    env.pop("FACTORY_HOME", None)
    if config is not None:
        (Path(home) / "config.json").write_text(json.dumps(config))
        env["FACTORY_HOME"] = home
    out = subprocess.run(
        [sys.executable, str(REPO / "tools" / "render.py"), harness],
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    return out


class ModelPolicyTests(unittest.TestCase):
    def tearDown(self):
        # leave the working tree's dist exactly canonical
        for harness in HARNESSES:
            env = dict(os.environ)
            env.pop("FACTORY_HOME", None)
            subprocess.run(
                [sys.executable, str(REPO / "tools" / "render.py"), harness],
                cwd=REPO,
                env=env,
                capture_output=True,
                check=True,
            )

    def test_exactly_claude_code_ships_models(self):
        shipped = []
        for name in HARNESSES:
            adapter = json.loads((ADAPTERS / name / "adapter.json").read_text())
            models = adapter.get("models")
            self.assertIsInstance(models, dict, name)
            if models:
                shipped.append(name)
                self.assertEqual(name, "claude-code", f"{name} ships models")
                self.assertIn("opus", models.get("deep", ""), name)
                self.assertIn("sonnet", models.get("standard", ""), name)
        self.assertEqual(shipped, ["claude-code"])

    def test_no_personal_provider_ids_ship_in_adapters(self):
        for name in HARNESSES:
            text = (ADAPTERS / name / "adapter.json").read_text()
            for personal in PERSONAL_IDS:
                self.assertNotIn(personal, text, f"{name} ships a personal model id")

    def test_readme_statement_matches_adapters(self):
        readme = (REPO / "README.md").read_text()
        self.assertIn(
            "Only Claude Code pins agent models by default",
            readme,
            "the README names claude-code as the only defaults carrier",
        )
        other = [n for n in HARNESSES if n != "claude-code"]
        for name in other:
            adapter = json.loads((ADAPTERS / name / "adapter.json").read_text())
            self.assertEqual(adapter.get("models"), {}, name)


class RenderOverrideTests(unittest.TestCase):
    def tearDown(self):
        env = dict(os.environ)
        env.pop("FACTORY_HOME", None)
        subprocess.run(
            [sys.executable, str(REPO / "tools" / "render.py"), "opencode"],
            cwd=REPO,
            env=env,
            capture_output=True,
            check=True,
        )

    def agent_texts(self):
        return [p.read_text() for p in sorted((DIST / "opencode" / "agents").iterdir())]

    def test_config_overrides_reach_the_rendered_agents(self):
        render(
            "opencode",
            config={"models": {"opencode": {"deep": "test-org/test-deep-model"}}},
        )
        texts = self.agent_texts()
        self.assertTrue(
            any("test-org/test-deep-model" in t for t in texts),
            "the deep-tier agents carry the override",
        )
        standard = [t for t in texts if "test-org/test-deep-model" not in t]
        self.assertEqual(
            len(standard),
            len(texts) - 2,
            "only the deep-tier agents (spec-builder, review-judge) take the override",
        )

    def test_without_explicit_home_the_render_ignores_the_default_home(self):
        # even once ~/.factory/config.json exists on this machine, a plain
        # render stays canonical: overrides apply when FACTORY_HOME is set
        default_home = Path(os.environ.get("FACTORY_HOME", "~/.factory")).expanduser()
        sentinel = default_home / "config.json"
        existed = sentinel.exists()
        if not existed:
            default_home.mkdir(parents=True, exist_ok=True)
            sentinel.write_text(
                json.dumps({"models": {"opencode": {"deep": "test-org/leaked"}}})
            )
        try:
            render("opencode")  # no FACTORY_HOME in the child env
            self.assertFalse(
                any("test-org/leaked" in t for t in self.agent_texts()),
                "the default home is not consulted without an explicit FACTORY_HOME",
            )
        finally:
            if not existed:
                sentinel.unlink()

    def test_effective_models_are_printable_per_role(self):
        out = render(
            "opencode",
            config={"models": {"opencode": {"deep": "test-org/test-deep-model"}}},
        )
        plain = subprocess.run(
            [sys.executable, str(REPO / "tools" / "render.py"), "opencode", "--models"],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=True,
            env={**os.environ, "FACTORY_HOME": ""},
        )  # empty home: no config
        self.assertIn("spec-builder: (session default)", plain.stdout)
        override_home = tempfile.mkdtemp(prefix="factory-render-home-")
        (Path(override_home) / "config.json").write_text(
            json.dumps({"models": {"opencode": {"deep": "test-org/test-deep-model"}}})
        )
        effective = subprocess.run(
            [sys.executable, str(REPO / "tools" / "render.py"), "opencode", "--models"],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=True,
            env={**os.environ, "FACTORY_HOME": override_home},
        )
        self.assertIn("spec-builder: test-org/test-deep-model", effective.stdout)


if __name__ == "__main__":
    unittest.main()
