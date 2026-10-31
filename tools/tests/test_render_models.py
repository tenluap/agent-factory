"""Model-policy seam tests over `tools/render.py` render output (FR-015, FR-002).

Claude Code, Codex and OpenCode ship explicit tier selections; personal provider
IDs ship nowhere; the canonical `render.py <harness>` render never reads
`config.json`, so the committed dist stays machine-independent whatever the
environment; the README statement matches `adapters/`.
"""

import json
import os
import re
import shlex
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

    def test_shipped_model_policy_preserves_explicit_tiers(self):
        expected = {
            "claude-code": {
                "deep": "claude-opus-5-5",
                "standard": "claude-haiku-5-5",
            },
            "codex": {"deep": "openai/gpt-6.1-sol", "standard": "openai/gpt-6.1-terra"},
            "opencode": {
                "deep": "claude-code/claude-opus-5-5[1m]",
                "standard": "openai/gpt-6.1-terra",
            },
        }
        shipped = []
        for name in HARNESSES:
            adapter = json.loads((ADAPTERS / name / "adapter.json").read_text())
            models = adapter.get("models")
            self.assertIsInstance(models, dict, name)
            self.assertEqual(models, expected.get(name, {}), name)
            if models:
                shipped.append(name)
                self.assertEqual(set(models), {"deep", "standard"}, name)
                for tier, selected in models.items():
                    self.assertIsInstance(selected, str, (name, tier))
                    self.assertTrue(selected.strip(), (name, tier))
        self.assertEqual(shipped, ["claude-code", "codex", "opencode"])

    def test_no_personal_provider_ids_ship_in_adapters(self):
        for name in HARNESSES:
            text = (ADAPTERS / name / "adapter.json").read_text()
            for personal in PERSONAL_IDS:
                self.assertNotIn(personal, text, f"{name} ships a personal model id")

    def test_readme_statement_matches_adapters(self):
        readme = (REPO / "README.md").read_text()
        self.assertIn(
            "Claude Code, Codex and OpenCode pin agent models by default", readme
        )
        self.assertIn("Copilot and Zcode inherit the session model", readme)
        for name in ("copilot", "zcode"):
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
        adapter = json.loads((ADAPTERS / "opencode" / "adapter.json").read_text())
        self.assertIn(f"spec-builder: {adapter['models']['deep']}", out.stdout)
        self.assertIn(f"code-build: {adapter['models']['standard']}", out.stdout)
        inherited = render_to("copilot", flags=("--models",), exported=False)
        self.assertIn("spec-builder: (session default)", inherited.stdout)

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

    def test_paths_report_skills_roots_and_home_overrides(self):
        with tempfile.TemporaryDirectory(prefix="factory paths ") as temp:
            home = Path(temp) / "home"
            home.mkdir()
            override = Path(temp) / "override home"
            defaults = {
                "claude-code": ".claude/skills",
                "opencode": ".config/opencode/skills",
                "codex": ".agents/skills",
                "copilot": ".agents/skills",
                "zcode": ".zcode/skills",
            }
            overrides = {
                "claude-code": ("CLAUDE_HOME", "skills"),
                "opencode": ("XDG_CONFIG_HOME", "opencode/skills"),
                "codex": ("CODEX_HOME", None),
                "copilot": ("COPILOT_HOME", None),
                "zcode": ("ZCODE_HOME", "skills"),
            }
            for harness, default in defaults.items():
                for use_override in (False, True):
                    with self.subTest(harness=harness, override=use_override):
                        env = dict(
                            os.environ,
                            HOME=str(home),
                            FACTORY_HOME=str(home / ".factory"),
                        )
                        for key, _ in overrides.values():
                            env.pop(key, None)
                        variable, suffix = overrides[harness]
                        if use_override:
                            env[variable] = str(override)
                        target = Path(temp) / "never-written"
                        result = subprocess.run(
                            [
                                sys.executable,
                                str(REPO / "tools/render.py"),
                                harness,
                                "--paths",
                                "--out",
                                str(target),
                            ],
                            cwd=REPO,
                            env=env,
                            text=True,
                            capture_output=True,
                            check=True,
                        )
                        paths = dict(
                            shlex.split(line)[0].split("=", 1)
                            for line in result.stdout.splitlines()
                        )
                        expected = (
                            override / suffix
                            if use_override and suffix
                            else home / default
                        )
                        self.assertEqual(paths.get("skills_root"), str(expected))
                        self.assertFalse(target.exists())


class ReadOnlyConformanceTests(unittest.TestCase):
    """Static read-only conformance (FR-014, R13): every rendered read-access
    agent denies editing in its adapter's own terms; codex is excluded by its
    documented disclosure."""

    ENFORCING = ("claude-code", "copilot", "opencode", "zcode")

    def test_retro_role_renders_read_only_for_every_harness(self):
        import render as render_mod

        role = REPO / "core/roles/retro.md"
        self.assertTrue(role.exists(), "retro role missing")
        source = role.read_text()
        meta, _ = render_mod.frontmatter(source)
        self.assertEqual(
            (meta["name"], meta["tier"], meta["access"]), ("retro", "standard", "read")
        )
        for harness in HARNESSES:
            with self.subTest(harness=harness):
                render(harness)
                adapter = json.loads((ADAPTERS / harness / "adapter.json").read_text())
                text = self.agent_path(harness, meta).read_text()
                model = adapter["models"].get("standard")
                if model:
                    self.assertIn(model, text)
                if harness in ("claude-code", "zcode", "copilot"):
                    tools = next(
                        line for line in text.splitlines() if line.startswith("tools:")
                    )
                    self.assertNotIn("edit", tools.lower())
                    self.assertNotIn("write", tools.lower())
                if harness == "opencode":
                    self.assertIn('"action": "edit"', text)
                    self.assertIn('"effect": "deny"', text)
                for access in adapter["access"].values():
                    names = access.get("tools", [])
                    if isinstance(names, str):
                        names = names.split(", ")
                    for name in names:
                        pattern = rf"(?:`{re.escape(name)}`|\b{re.escape(name)} tool\b)"
                        self.assertNotRegex(source, pattern)

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

    def test_ui_designer_renders_for_every_harness(self):
        import render as render_mod

        role = REPO / "core/roles/ui-designer.md"
        self.assertTrue(role.exists(), "ui-designer role missing")
        meta, _ = render_mod.frontmatter(role.read_text())
        self.assertEqual(
            (meta["name"], meta["tier"], meta["access"]),
            ("ui-designer", "standard", "write"),
        )
        for harness in HARNESSES:
            with self.subTest(harness=harness):
                render(harness)
                adapter = json.loads((ADAPTERS / harness / "adapter.json").read_text())
                path = self.agent_path(harness, meta)
                self.assertTrue(path.exists(), path)
                text = path.read_text()
                model = adapter["models"].get("standard")
                if model:
                    self.assertIn(model, text)
                if harness in ("claude-code", "zcode"):
                    tools_line = next(
                        line for line in text.splitlines() if line.startswith("tools:")
                    )
                    self.assertIn("Edit", tools_line)
                    self.assertIn("Write", tools_line)
                if harness == "copilot":
                    self.assertIn(
                        "edit",
                        next(
                            line
                            for line in text.splitlines()
                            if line.startswith("tools:")
                        ),
                    )
                if harness == "opencode":
                    self.assertNotIn('"action": "edit"', text)

    def test_ui_designer_core_role_names_no_harness_tool(self):
        text = (REPO / "core/roles/ui-designer.md").read_text()
        self.assertNotIn("adapters/", text)
        self.assertNotIn("dist/", text)
        for path in ADAPTERS.glob("*/adapter.json"):
            adapter = json.loads(path.read_text())
            for access in adapter["access"].values():
                names = access.get("tools", [])
                if isinstance(names, str):
                    names = names.split(", ")
                for name in names:
                    if name == "web":
                        # Copilot's research label; `web` is also a framework value here.
                        continue
                    # Labels such as Read and edit also occur as ordinary prose.
                    pattern = rf"(?:`{re.escape(name)}`|\b{re.escape(name)} tool\b)"
                    self.assertNotRegex(text, pattern, (path, name))

    def test_ui_designer_pen_source_is_cli_exclusive(self):
        # FR-031: Pen source access goes through the pen CLI only; a harness
        # Pen MCP backend is never a fallback, and a missing CLI is an
        # honestly recorded unavailable gate, not an install trigger.
        role = (REPO / "core/roles/ui-designer.md").read_text()
        self.assertIn("pen CLI", role)
        self.assertIn("pen interactive", role)
        self.assertIn("Never use a Pen MCP backend", role)
        self.assertIn("do not fall back to an MCP backend", role)
        contract = (
            REPO / "core/skills/factory/references/design-code-mapping.md"
        ).read_text()
        self.assertIn("only through the pen CLI", contract)
        self.assertIn("no MCP fallback", contract)

    def test_facets_advisor_renders_research_access_for_every_harness(self):
        import render as render_mod

        role = REPO / "core/roles/facets-advisor.md"
        self.assertTrue(role.exists(), "facets-advisor role missing")
        meta, _ = render_mod.frontmatter(role.read_text())
        self.assertEqual(
            (meta["name"], meta["tier"], meta["access"]),
            ("facets-advisor", "deep", "research"),
        )
        self.assertEqual(meta.get("mode"), "primary")
        for harness in HARNESSES:
            with self.subTest(harness=harness):
                render(harness)
                adapter = json.loads((ADAPTERS / harness / "adapter.json").read_text())
                self.assertIn("research", adapter["access"])
                path = self.agent_path(harness, meta)
                self.assertTrue(path.exists(), path)
                text = path.read_text()
                model = adapter["models"].get("deep")
                if model:
                    self.assertIn(model, text)
                if harness in ("claude-code", "zcode"):
                    tools_line = next(
                        line for line in text.splitlines() if line.startswith("tools:")
                    )
                    self.assertIn("WebSearch", tools_line)
                    self.assertIn("WebFetch", tools_line)
                    self.assertNotIn("Edit", tools_line)
                    self.assertNotIn("Write", tools_line)
                if harness == "copilot":
                    tools_line = next(
                        line for line in text.splitlines() if line.startswith("tools:")
                    )
                    self.assertIn("web", tools_line)
                    self.assertNotIn("edit", tools_line)
                if harness == "opencode":
                    self.assertIn('"action": "edit"', text)
                    self.assertIn('"effect": "deny"', text)
                    self.assertIn("\nmode: all\n", text)

    def test_facets_advisor_core_role_names_no_harness_tool(self):
        text = (REPO / "core/roles/facets-advisor.md").read_text()
        self.assertNotIn("adapters/", text)
        self.assertNotIn("dist/", text)
        self.assertIn("WEB_SEARCH", text)
        self.assertIn("WEB_FETCH", text)
        for path in ADAPTERS.glob("*/adapter.json"):
            adapter = json.loads(path.read_text())
            for access in adapter["access"].values():
                names = access.get("tools", [])
                if isinstance(names, str):
                    names = names.split(", ")
                for name in names:
                    pattern = rf"(?:`{re.escape(name)}`|\b{re.escape(name)} tool\b)"
                    self.assertNotRegex(text, pattern, (path, name))

    def test_only_primary_roles_leave_opencode_subagent_mode(self):
        import render as render_mod

        render("opencode")
        for role_file in sorted((render_mod.ROOT / "core" / "roles").glob("*.md")):
            meta, _ = render_mod.frontmatter(role_file.read_text())
            text = self.agent_path("opencode", meta).read_text()
            expected = "all" if meta.get("mode") == "primary" else "subagent"
            with self.subTest(role=meta["name"]):
                self.assertIn(f"\nmode: {expected}\n", text)
                self.assertEqual(text.count("\nmode: "), 1)

    def test_every_harness_documents_main_agent_mode(self):
        for harness in HARNESSES:
            text = (ADAPTERS / harness / "harness.md").read_text()
            with self.subTest(harness=harness):
                self.assertIn("Main agent (`mode: primary`)", text)

    def test_every_harness_maps_the_research_verbs(self):
        for harness in HARNESSES:
            text = (ADAPTERS / harness / "harness.md").read_text()
            with self.subTest(harness=harness):
                self.assertIn("WEB_SEARCH", text)
                self.assertIn("WEB_FETCH", text)


if __name__ == "__main__":
    unittest.main()
