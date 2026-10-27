"""Model-policy seam tests over `tools/render.py` render output (FR-015, FR-002).

Exactly one adapter ships models (claude-code opus/sonnet); personal provider
IDs ship nowhere; the canonical `render.py <harness>` render never reads
`config.json`, so the committed dist stays machine-independent whatever the
environment; the README statement matches `adapters/`.
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


def render_to(harness, out=None, config=None, exported=True, flags=()):
    """`--out` render into `out` (or a flag-only run when out is None); the
    factory home is a temp dir holding `config`.

    `exported=True` sets FACTORY_HOME to that home; `exported=False` leaves it
    unset so the documented default home `${FACTORY_HOME:-~/.factory}` resolves
    through the sandboxed HOME.
    """
    home = Path(tempfile.mkdtemp(prefix="factory-render-home-"))
    env = dict(os.environ)
    env.pop("FACTORY_HOME", None)
    env["HOME"] = str(home)
    factory_home = home if exported else home / ".factory"
    if config is not None:
        factory_home.mkdir(parents=True, exist_ok=True)
        (factory_home / "config.json").write_text(json.dumps(config))
    if exported:
        env["FACTORY_HOME"] = str(home)
    cmd = [sys.executable, str(REPO / "tools" / "render.py"), harness, *flags]
    if out is not None:
        cmd += ["--out", str(out)]
    return subprocess.run(
        cmd,
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )


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


class CanonicalRenderTests(unittest.TestCase):
    """FR-002: the canonical render into dist/ never merges config.json,
    whatever the environment; personal ids and overrides stay out of it."""

    def tearDown(self):
        for harness in ("claude-code", "opencode"):
            env = dict(os.environ)
            env.pop("FACTORY_HOME", None)
            subprocess.run(
                [sys.executable, str(REPO / "tools" / "render.py"), harness],
                cwd=REPO,
                env=env,
                capture_output=True,
                check=True,
            )

    def agent_texts(self, harness):
        return [p.read_text() for p in sorted((DIST / harness / "agents").iterdir())]

    def test_exported_home_with_overrides_leaves_dist_at_adapter_defaults(self):
        render(
            "claude-code",
            config={"models": {"claude-code": {"deep": "test-org/test-deep-model"}}},
        )
        texts = self.agent_texts("claude-code")
        self.assertFalse(
            any("test-org/test-deep-model" in t for t in texts),
            "the canonical render never merges config.json, even exported",
        )
        self.assertTrue(
            any("opus" in t for t in texts),
            "the adapter's own model defaults stay in place",
        )

    def test_exported_home_with_overrides_leaves_opencode_canonical(self):
        render(
            "opencode",
            config={"models": {"opencode": {"deep": "test-org/test-deep-model"}}},
        )
        texts = self.agent_texts("opencode")
        self.assertFalse(
            any("test-org/test-deep-model" in t for t in texts),
            "the canonical opencode render never carries the override",
        )

    def test_without_explicit_home_the_render_ignores_the_default_home(self):
        # even once ~/.factory/config.json exists on this machine, a plain
        # render stays canonical: the dist path reads no config at all
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
                any("test-org/leaked" in t for t in self.agent_texts("opencode")),
                "the default home is never consulted by the canonical render",
            )
        finally:
            if not existed:
                sentinel.unlink()


class PerUserRenderTests(unittest.TestCase):
    """FR-001/FR-003: `render.py <harness> --out <dir>` renders the harness
    tree into <dir> with `${FACTORY_HOME:-~/.factory}/config.json` models
    merged per key over the adapter defaults; absent config or keys fall
    back per key."""

    OVER = "test-org/test-deep-model"

    def out_texts(self, out):
        return [p.read_text() for p in sorted((Path(out) / "agents").iterdir())]

    def test_out_render_merges_from_the_default_home_when_unset(self):
        out = tempfile.mkdtemp(prefix="factory-per-user-")
        render_to(
            "opencode",
            out,
            config={"models": {"opencode": {"deep": self.OVER}}},
            exported=False,
        )
        self.assertTrue(
            any(self.OVER in t for t in self.out_texts(out)),
            "an unset FACTORY_HOME still resolves ~/.factory/config.json",
        )
        self.assertTrue((Path(out) / "skill").is_dir(), "the tree lands in <dir>")

    def test_out_render_merges_from_an_exported_factory_home(self):
        out = tempfile.mkdtemp(prefix="factory-per-user-")
        render_to("opencode", out, config={"models": {"opencode": {"deep": self.OVER}}})
        self.assertTrue(any(self.OVER in t for t in self.out_texts(out)))

    def test_out_render_falls_back_per_key_on_absent_keys(self):
        out = tempfile.mkdtemp(prefix="factory-per-user-")
        render_to(
            "claude-code",
            out,
            config={"models": {"claude-code": {"standard": "test-org/test-standard"}}},
        )
        texts = self.out_texts(out)
        self.assertTrue(
            any("test-org/test-standard" in t for t in texts),
            "a present key merges over the default",
        )
        self.assertTrue(
            any("opus" in t for t in texts),
            "an absent key keeps the adapter default",
        )

    def test_out_render_without_config_uses_defaults(self):
        out = tempfile.mkdtemp(prefix="factory-per-user-")
        render_to("claude-code", out)  # no config.json in the home at all
        texts = self.out_texts(out)
        self.assertTrue(any("opus" in t for t in texts), "adapter defaults stand")
        self.assertFalse(
            any("test-org/" in t for t in texts), "nothing personal merges"
        )


class ReportTests(unittest.TestCase):
    """FR-004: `--models` and `--paths` are write-free reports; `--models`
    prints the effective model per role resolved from the default home,
    FACTORY_HOME exported or not."""

    OVER = "test-org/test-deep-model"

    def tearDown(self):
        # the write-free assertions delete dist/<harness>; leave it canonical
        for harness in ("opencode",):
            env = dict(os.environ)
            env.pop("FACTORY_HOME", None)
            subprocess.run(
                [sys.executable, str(REPO / "tools" / "render.py"), harness],
                cwd=REPO,
                env=env,
                capture_output=True,
                check=True,
            )

    def test_models_report_writes_nothing(self):
        shutil.rmtree(DIST / "opencode", ignore_errors=True)
        render_to(
            "opencode",
            flags=("--models",),
            config={"models": {"opencode": {"deep": self.OVER}}},
        )
        self.assertFalse((DIST / "opencode").exists(), "--models renders nothing")

    def test_paths_report_writes_nothing(self):
        shutil.rmtree(DIST / "opencode", ignore_errors=True)
        render_to("opencode", flags=("--paths",))
        self.assertFalse((DIST / "opencode").exists(), "--paths renders nothing")

    def test_models_report_resolves_from_the_default_home(self):
        cfg = {"models": {"opencode": {"deep": self.OVER}}}
        unset = render_to("opencode", flags=("--models",), config=cfg, exported=False)
        self.assertIn(f"spec-builder: {self.OVER}", unset.stdout)
        exported = render_to("opencode", flags=("--models",), config=cfg)
        self.assertIn(f"spec-builder: {self.OVER}", exported.stdout)

    def test_models_report_without_config_prints_defaults(self):
        out = render_to("opencode", flags=("--models",), exported=False)
        self.assertIn("spec-builder: (session default)", out.stdout)

    def test_bad_config_fails_naming_the_file_without_a_traceback(self):
        for text in ("{not json", "[]", '{"models": 5}', '{"models": {"opencode": 1}}'):
            with self.subTest(config=text):
                home = Path(tempfile.mkdtemp(prefix="factory-render-home-"))
                self.addCleanup(shutil.rmtree, home, True)
                (home / "config.json").write_text(text)
                env = dict(os.environ, FACTORY_HOME=str(home))
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(REPO / "tools" / "render.py"),
                        "opencode",
                        "--models",
                    ],
                    cwd=REPO,
                    env=env,
                    capture_output=True,
                    text=True,
                )
                self.assertNotEqual(proc.returncode, 0)
                self.assertIn("config.json", proc.stderr)
                self.assertNotIn("Traceback", proc.stderr)

    def test_paths_report_prints_the_install_targets(self):
        out = render_to("opencode", flags=("--paths",), exported=False)
        for key in ("dist=", "skill_dir=", "agent_dir="):
            self.assertIn(key, out.stdout)


class ReadOnlyConformanceTests(unittest.TestCase):
    """Static read-only conformance (FR-014, R13): every rendered read-access
    agent denies editing in its adapter's own terms; codex is excluded by its
    documented disclosure."""

    ENFORCING = ("claude-code", "copilot", "opencode", "zcode")

    def read_roles(self):
        import render as render_mod

        for role_file in sorted((render_mod.ROOT / "core" / "roles").glob("*.md")):
            meta, _ = render_mod.frontmatter(role_file.read_text())
            if meta["access"] == "read":
                yield meta

    def agent_path(self, harness, meta):
        adapter = json.loads((ADAPTERS / harness / "adapter.json").read_text())
        name = adapter["agent_file"].format(
            role=meta["name"],
            role_=meta["name"].replace("-", "_"),
            description=meta["description"],
        )
        return DIST / harness / "agents" / name

    def tearDown(self):
        for harness in self.ENFORCING:
            env = dict(os.environ)
            env.pop("FACTORY_HOME", None)
            subprocess.run(
                [sys.executable, str(REPO / "tools" / "render.py"), harness],
                cwd=REPO,
                env=env,
                capture_output=True,
                check=True,
            )

    def test_read_agents_deny_editing_in_each_adapters_terms(self):
        for harness in self.ENFORCING:
            render(harness)
            for meta in self.read_roles():
                path = self.agent_path(harness, meta)
                self.assertTrue(path.exists(), path)
                text = path.read_text()
                with self.subTest(harness=harness, role=meta["name"]):
                    if harness in ("claude-code", "zcode"):
                        self.assertIn("tools:", text)
                        tools_line = next(
                            line
                            for line in text.splitlines()
                            if line.startswith("tools:")
                        )
                        self.assertNotIn("Edit", tools_line, path)
                        self.assertNotIn("Write", tools_line, path)
                    elif harness == "copilot":
                        tools_line = next(
                            line
                            for line in text.splitlines()
                            if line.startswith("tools:")
                        )
                        self.assertNotIn("edit", tools_line.lower(), path)
                        self.assertNotIn("write", tools_line.lower(), path)
                    elif harness == "opencode":
                        self.assertIn('"effect": "deny"', text, path)
                        self.assertIn('"action": "edit"', text, path)

    def test_codex_limitation_is_disclosed(self):
        disclosure = (ADAPTERS / "codex" / "harness.md").read_text()
        self.assertIn(
            "read-only roles are read-only by instruction",
            disclosure,
            "codex documents that it cannot enforce read-only agents",
        )

    def test_write_roles_keep_edit_access(self):
        import render as render_mod

        render("claude-code")
        adapter = json.loads((ADAPTERS / "claude-code" / "adapter.json").read_text())
        for role_file in sorted((render_mod.ROOT / "core" / "roles").glob("*.md")):
            meta, _ = render_mod.frontmatter(role_file.read_text())
            if meta["access"] == "write":
                text = self.agent_path("claude-code", meta).read_text()
                tools_line = next(
                    line for line in text.splitlines() if line.startswith("tools:")
                )
                self.assertIn("Edit", tools_line, meta["name"])
                self.assertIn("Write", tools_line, meta["name"])


if __name__ == "__main__":
    unittest.main()
