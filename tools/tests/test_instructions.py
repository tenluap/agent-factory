"""Repo instruction discovery tests (spec 025): the scanner behind
`factory instructions` and the `instructions-record` writer.

Fixture trees are built in Sandbox git repos, never tracked fixture directories.
"""

import json
import os
import socket
import sys
import unittest
from pathlib import Path

CORE_BIN = Path(__file__).resolve().parents[2] / "core" / "skills" / "factory" / "bin"
sys.path.insert(0, str(CORE_BIN))

from factory_cli.instructions import glob_regex  # noqa: E402
from tests import Sandbox, fixture  # noqa: E402


class ScanBase(unittest.TestCase):
    def setUp(self):
        self.box = Sandbox()
        self.addCleanup(self.box.close)

    def add(self, files, message="add"):
        """Write `files` ({path: text}) into the sandbox repo and commit them."""
        for rel, text in files.items():
            path = self.box.repo / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        self.box.git("add", "-A")
        self.box.git("commit", "-q", "-m", message)

    def link(self, rel, target):
        path = self.box.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        os.symlink(target, path)

    def scan(self, *extra):
        out = self.box.cli("instructions", *extra)
        self.assertEqual(out.returncode, 0, out.stderr)
        return json.loads(out.stdout)

    def entries(self, *extra):
        return {e["path"]: e for e in self.scan(*extra)["entries"]}


class ScannerCoreTests(ScanBase):
    def build(self):
        self.add({"AGENTS.md": "# Agents\nrules\n", "CONVENTIONS.md": "# Conv\nv1\n"})
        self.link("CLAUDE.md", "AGENTS.md")
        self.link("broken/AGENTS.md", "missing.md")
        self.link("outside/AGENTS.md", "../../outside.md")
        self.box.git("add", "-A")
        self.box.git("commit", "-q", "-m", "links")
        (self.box.repo / "GEMINI.md").write_text("# untracked\n")
        (self.box.repo / "CONVENTIONS.md").write_text("# Conv\nedited\n")
        blob = self.box.git("rev-parse", "HEAD:CONVENTIONS.md").strip()
        sub = self.box.git("rev-parse", "HEAD:AGENTS.md").strip()
        self.box.git("update-index", "--add", "--cacheinfo", f"160000,{sub},vendor/lib")
        self.box.git("commit", "-q", "-m", "gitlink")
        self.assertTrue(blob)

    def test_scan_lists_tracked_entries_once_with_fields(self):
        self.build()
        status = self.box.git("status", "--porcelain")
        index = self.scan()
        entries = {e["path"]: e for e in index["entries"]}
        agents = entries["AGENTS.md"]
        self.assertEqual(agents["aliases"], ["CLAUDE.md"])
        self.assertEqual(agents["kind"], "always")
        self.assertEqual(agents["scope"], ["/"])
        self.assertEqual(agents["source"], "catalogue")
        self.assertEqual(agents["title"], "Agents")
        self.assertEqual(agents["size"], len("# Agents\nrules\n"))
        self.assertRegex(agents["hash"], r"^sha256:[0-9a-f]{64}$")
        self.assertNotIn("CLAUDE.md", entries)
        self.assertNotIn("GEMINI.md", entries)
        self.assertFalse([p for p in entries if p.startswith("vendor/")])
        self.assertFalse([p for p in entries if p.startswith(("broken/", "outside/"))])
        self.assertTrue(index["notes"])
        # the committed blob is hashed, not the modified working tree file
        import hashlib

        committed = self.box.git("show", "HEAD:CONVENTIONS.md").encode()
        self.assertEqual(
            entries["CONVENTIONS.md"]["hash"],
            "sha256:" + hashlib.sha256(committed).hexdigest(),
        )
        self.assertEqual(self.box.git("status", "--porcelain"), status)

    def test_default_ref_equals_explicit_head_and_runs_are_identical(self):
        self.build()
        first = self.box.cli("instructions")
        second = self.box.cli("instructions", "--ref", "HEAD")
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(first.stdout, self.box.cli("instructions").stdout)

    def test_not_a_git_repository_exits_2(self):
        out = self.box.cli("instructions", cwd=self.box.dir)
        self.assertEqual(out.returncode, 2)

    def test_unresolvable_ref_exits_5_naming_the_ref(self):
        out = self.box.cli("instructions", "--ref", "no-such-ref")
        self.assertEqual(out.returncode, 5)
        self.assertIn("no-such-ref", out.stderr)


CATALOGUE_FIXTURE = {
    "AGENTS.md": "always",
    "AGENTS.override.md": "always",
    "AGENT.md": "always",
    "CLAUDE.md": "always",
    ".claude/CLAUDE.md": "always",
    "CLAUDE.local.md": "always",
    ".claude/rules/a/b.md": "always",
    "GEMINI.md": "always",
    ".github/copilot-instructions.md": "always",
    ".github/instructions/x/y.instructions.md": "reference",
    ".cursor/rules/x/y.mdc": "reference",
    ".cursorrules": "always",
    ".windsurf/rules/a.md": "always",
    ".windsurf/global_rules.md": "always",
    ".windsurfrules": "always",
    ".devin/rules/a.md": "always",
    ".devin/global_rules.md": "always",
    ".clinerules": "always",
    ".cline/rules/a.txt": "always",
    ".roo/rules/a.md": "always",
    ".roorules": "always",
    ".roo/rules-code/a.md": "reference",
    ".roorules-code": "reference",
    ".junie/AGENTS.md": "always",
    ".junie/rules/a.md": "always",
    ".junie/playbook.md": "always",
    ".junie/guidelines.md": "always",
    ".junie/guidelines/sub/a.md": "always",
    ".kiro/steering/a.md": "always",
    "CONVENTIONS.md": "always",
    ".rules": "always",
    ".continue/rules/a.md": "always",
}


class CatalogueTests(ScanBase):
    def test_every_catalogue_row_and_governance_rule(self):
        self.add({p: f"# {p}\n" for p in CATALOGUE_FIXTURE})
        index = self.entries()
        for path, kind in CATALOGUE_FIXTURE.items():
            if path == ".clinerules":  # file form; directory form is a separate repo
                continue
            self.assertIn(path, index, path)
            self.assertEqual(index[path]["kind"], kind, path)
            self.assertEqual(index[path]["scope"], ["/"], path)
            self.assertEqual(index[path]["source"], "catalogue", path)

    def test_clinerules_directory_form(self):
        self.add({".clinerules/a.md": "# a\n", ".clinerules/b.txt": "# b\n"})
        self.assertEqual(
            sorted(self.entries()), [".clinerules/a.md", ".clinerules/b.txt"]
        )

    def test_governance_documents_and_adrs(self):
        self.add(
            {
                "CONTRIBUTING.md": "# c1\n",
                ".github/CONTRIBUTING.md": "# c2\n",
                "docs/CONTRIBUTING.md": "# c3\n",
                "pkg/a/CONTRIBUTING.md": "# c4\n",
                ".specify/memory/constitution.md": "# const\n",
                "other/constitution.md": "# no\n",
                "docs/adr/0001-x.md": "# adr\n",
                "architecture/decisions/a.md": "# adr2\n",
                "decisions/x.md": "# no\n",
                ".cursor/rules/x.md": "# no\n",
                "README.md": "# readme\n",
            }
        )
        index = self.entries()
        for path in ("CONTRIBUTING.md", ".github/CONTRIBUTING.md", "docs/CONTRIBUTING.md"):
            self.assertEqual(
                (index[path]["kind"], index[path]["scope"], index[path]["source"]),
                ("always", ["/"], "governance"),
                path,
            )
        nested = index["pkg/a/CONTRIBUTING.md"]
        self.assertEqual((nested["kind"], nested["scope"]), ("scoped", ["pkg/a/"]))
        const = index[".specify/memory/constitution.md"]
        self.assertEqual((const["kind"], const["source"]), ("always", "governance"))
        for path in ("docs/adr/0001-x.md", "architecture/decisions/a.md"):
            self.assertEqual(
                (index[path]["kind"], index[path]["source"]), ("reference", "governance")
            )
        for absent in (
            "other/constitution.md",
            "decisions/x.md",
            ".cursor/rules/x.md",
            "README.md",
        ):
            self.assertNotIn(absent, index)

    def test_identical_copies_collapse_to_first_path(self):
        self.add({"GEMINI.md": "# same\n", "CONVENTIONS.md": "# same\n"})
        index = self.entries()
        self.assertEqual(sorted(index), ["CONVENTIONS.md"])
        self.assertEqual(index["CONVENTIONS.md"]["aliases"], ["GEMINI.md"])


def fm(**fields):
    lines = [f"{k}: {v}" for k, v in fields.items()]
    return "---\n" + "\n".join(lines) + "\n---\nbody\n"


class ClassificationTests(ScanBase):
    def kinds(self, files):
        self.add(files)
        return {p: (e["kind"], e["scope"]) for p, e in self.entries().items()}

    def test_front_matter_mappings_and_nested_scope(self):
        got = self.kinds(
            {
                "packages/api/AGENTS.md": "# api\n",
                ".cursor/rules/a.mdc": fm(alwaysApply="true"),
                ".cursor/rules/b.mdc": fm(globs="src/**/*.ts"),
                ".cursor/rules/c.mdc": fm(description="x"),
                ".github/instructions/a.instructions.md": fm(applyTo='"a/**,b/**"'),
                ".kiro/steering/k.md": fm(inclusion="fileMatch", fileMatchPattern="k/*"),
                ".windsurf/rules/w.md": fm(trigger="model_decision"),
                ".continue/rules/c.md": fm(alwaysApply="false"),
                ".continue/rules/d.md": fm(globs='"**"'),
                "pkg/.cursor/rules/g.mdc": fm(globs="x/*"),
            }
        )
        self.assertEqual(got["packages/api/AGENTS.md"], ("scoped", ["packages/api/"]))
        self.assertEqual(got[".cursor/rules/a.mdc"], ("always", ["/"]))
        self.assertEqual(got[".cursor/rules/b.mdc"], ("scoped", ["src/**/*.ts"]))
        self.assertEqual(got[".cursor/rules/c.mdc"][0], "reference")
        self.assertEqual(
            got[".github/instructions/a.instructions.md"], ("scoped", ["a/**", "b/**"])
        )
        self.assertEqual(got[".kiro/steering/k.md"], ("scoped", ["k/*"]))
        self.assertEqual(got[".windsurf/rules/w.md"][0], "reference")
        self.assertEqual(got[".continue/rules/c.md"][0], "reference")
        self.assertEqual(got[".continue/rules/d.md"], ("always", ["/"]))
        self.assertEqual(got["pkg/.cursor/rules/g.mdc"], ("scoped", ["pkg/x/*"]))

    def test_title_falls_back_to_description_then_file_name(self):
        self.add({".cursor/rules/a.mdc": fm(description="Desc"), ".rules": "plain\n"})
        index = self.entries()
        self.assertEqual(index[".cursor/rules/a.mdc"]["title"], "Desc")
        self.assertEqual(index[".rules"]["title"], ".rules")

    def test_unclosed_front_matter_keeps_row_default_with_note(self):
        self.add({".cursor/rules/a.mdc": "---\nalwaysApply: true\nbody\n"})
        index = self.scan()
        self.assertEqual(index["entries"][0]["kind"], "reference")
        self.assertIn("front matter unparseable: .cursor/rules/a.mdc", index["notes"])

    def test_non_utf8_blob_is_indexed_with_note(self):
        path = self.box.repo / "AGENTS.md"
        path.write_bytes(b"\xff\xfe bad\n")
        self.box.git("add", "-A")
        self.box.git("commit", "-q", "-m", "bin")
        index = self.scan()
        entry = index["entries"][0]
        self.assertEqual((entry["title"], entry["size"]), ("", 7))
        self.assertIn("not UTF-8: AGENTS.md", index["notes"])


class ImportAndLinkTests(ScanBase):
    def test_imports_follow_to_a_fixpoint_and_inherit_kind_and_scope(self):
        self.add(
            {
                "AGENTS.md": "# A\n@docs/style.md\n```\n@docs/fenced.md\n```\n"
                "use `@docs/span.md` mail user@example.com\n",
                "docs/style.md": "# Style\n@docs/more.md\n",
                "docs/more.md": "# More\n",
                "docs/fenced.md": "x\n",
                "docs/span.md": "x\n",
                "pkg/AGENTS.md": "# P\n@rules.md\n",
                "pkg/rules.md": "# Rules\n",
            }
        )
        got = self.entries()
        for path in ("docs/style.md", "docs/more.md"):
            self.assertEqual((got[path]["kind"], got[path]["scope"]), ("always", ["/"]))
            self.assertEqual(got[path]["source"], "import")
        self.assertEqual(got["pkg/rules.md"]["scope"], ["pkg/"])
        self.assertEqual(got["pkg/rules.md"]["kind"], "scoped")
        for path in ("docs/fenced.md", "docs/span.md"):
            self.assertNotIn(path, got)

    def test_links_are_one_hop_reference_entries(self):
        self.add(
            {
                "AGENTS.md": "# A\n[g](docs/guide.md#x) [u](https://x.io) [m](mailto:a@b.c)\n"
                "[a](#top) [o](../../outside.md) [c](CONVENTIONS.md)\n[ref]: docs/ref.md\n",
                "CONVENTIONS.md": "# C\n",
                "docs/guide.md": "# G\n[n](docs/next.md)\n@docs/imp.md\n",
                "docs/next.md": "x\n",
                "docs/imp.md": "x\n",
                "docs/ref.md": "# Ref\n",
                "README.md": "# Readme\n",
            }
        )
        got = self.entries()
        self.assertEqual((got["docs/guide.md"]["kind"], got["docs/guide.md"]["source"]), ("reference", "link"))
        self.assertEqual(got["docs/ref.md"]["source"], "link")
        self.assertEqual((got["CONVENTIONS.md"]["kind"], got["CONVENTIONS.md"]["source"]), ("always", "catalogue"))
        for path in ("docs/next.md", "docs/imp.md", "README.md"):
            self.assertNotIn(path, got)

    def test_import_promotes_a_link_target(self):
        self.add(
            {
                "AGENTS.md": "# A\n[p](docs/p.md)\n@docs/q.md\n",
                "docs/q.md": "@docs/p.md\n",
                "docs/p.md": "# P\n",
            }
        )
        got = self.entries()
        self.assertEqual((got["docs/p.md"]["kind"], got["docs/p.md"]["source"]), ("always", "import"))

    def test_missing_and_untracked_import_targets_note_and_keep_importer(self):
        self.add({"AGENTS.md": "# A\n@missing.md\n@local.md\n"})
        (self.box.repo / "local.md").write_text("x\n")
        index = self.scan()
        self.assertEqual([e["path"] for e in index["entries"]], ["AGENTS.md"])
        self.assertIn("import target not tracked: AGENTS.md -> missing.md", index["notes"])
        self.assertIn("import target not tracked: AGENTS.md -> local.md", index["notes"])

    def test_import_cycle_is_followed_once(self):
        self.add({"AGENTS.md": "@a.md\n", "a.md": "@b.md\n", "b.md": "@a.md\n"})
        paths = [e["path"] for e in self.scan()["entries"]]
        self.assertEqual(sorted(paths), ["AGENTS.md", "a.md", "b.md"])

    def test_import_chain_stops_after_four_hops_with_a_note(self):
        files = {"AGENTS.md": "@c1.md\n"}
        files.update({f"c{i}.md": f"@c{i + 1}.md\n" for i in range(1, 7)})
        self.add(files)
        index = self.scan()
        paths = {e["path"] for e in index["entries"]}
        self.assertEqual(paths, {"AGENTS.md", "c1.md", "c2.md", "c3.md", "c4.md"})
        self.assertIn("import chain stopped at depth 4: c4.md -> c5.md", index["notes"])


def config(**lists):
    return json.dumps({"instructions": lists})


class ConfigListTests(ScanBase):
    def test_include_reference_exclude_lists(self):
        self.add(
            {
                ".factory/config.json": config(
                    include=["docs/conventions.md", "AGENTS.md", "both.md"],
                    reference=["DESIGN.md", "both.md"],
                    exclude=["conformance/**"],
                ),
                "AGENTS.md": "# A\n@conformance/bench/x/AGENTS.md\n[l](conformance/y.md)\n",
                "docs/conventions.md": "# Conv\n",
                "DESIGN.md": "# Design\n",
                "both.md": "# Both\n",
                "conformance/bench/x/AGENTS.md": "# no\n",
                "conformance/y.md": "# no\n",
            }
        )
        got = self.entries()
        self.assertEqual(
            (got["docs/conventions.md"]["kind"], got["docs/conventions.md"]["scope"], got["docs/conventions.md"]["source"]),
            ("always", ["/"], "config"),
        )
        self.assertEqual((got["DESIGN.md"]["kind"], got["DESIGN.md"]["source"]), ("reference", "config"))
        self.assertEqual(got["both.md"]["kind"], "always")
        self.assertEqual(got["AGENTS.md"]["source"], "catalogue")
        self.assertFalse([p for p in got if p.startswith("conformance/")])

    def test_config_is_read_at_the_ref_not_the_working_tree(self):
        self.add({"AGENTS.md": "# A\n", "DESIGN.md": "# D\n"})
        (self.box.repo / ".factory").mkdir()
        (self.box.repo / ".factory" / "config.json").write_text(config(include=["DESIGN.md"]))
        self.assertNotIn("DESIGN.md", self.entries())

    def test_glob_translation(self):
        self.assertTrue(glob_regex("conformance/**").match("conformance/a/b/AGENTS.md"))
        self.assertFalse(glob_regex("*.md").match("docs/a.md"))
        self.assertTrue(glob_regex("*.md").match("a.md"))
        self.assertTrue(glob_regex("**/x.md").match("x.md"))
        self.assertTrue(glob_regex("**/x.md").match("a/b/x.md"))
        self.assertTrue(glob_regex("a?.md").match("ab.md"))
        self.assertFalse(glob_regex("a?.md").match("a/.md"))

    def test_malformed_config_notes_and_falls_back_to_the_catalogue(self):
        for text in ('{"instructions": 3}', '{"instructions": {"include": [1]}}', "{not json"):
            with self.subTest(text=text):
                self.add({".factory/config.json": text, "AGENTS.md": "# A\n", "DESIGN.md": "# D\n"})
                index = self.scan()
                self.assertEqual([e["path"] for e in index["entries"]], ["AGENTS.md"])
                self.assertTrue([n for n in index["notes"] if n.startswith("instructions config ignored")])

    def test_this_repositorys_config_lists(self):
        repo = Path(__file__).resolve().parents[2]
        self.add(
            {
                ".factory/config.json": (repo / ".factory" / "config.json").read_text(),
                "AGENTS.md": "# A\n",
                "DESIGN.md": "# D\n",
                "CONTEXT.md": "# C\n",
                "conformance/x/AGENTS.md": "# no\n",
            }
        )
        got = self.entries()
        self.assertEqual((got["DESIGN.md"]["kind"], got["CONTEXT.md"]["kind"]), ("reference", "reference"))
        self.assertFalse([p for p in got if p.startswith("conformance/")])


class RecordBase(ScanBase):
    def state(self, **extra):
        return dict(fixture("state-v5.json"), base="HEAD", **extra)

    def pending(self, name, **extra):
        return self.box.pending_run(name, self.state(**extra))


class RecordTests(RecordBase):

    def test_pending_new_run_scans_base_and_writes_sidecar_and_summary(self):
        self.add({"AGENTS.md": "# A\n", "docs/x.md": "# X\n"})
        path = self.pending("025-a")
        out = self.box.cli("instructions-record")
        self.assertEqual(out.returncode, 0, out.stderr)
        result = json.loads(out.stdout)
        sidecar = path.with_name(path.name.replace(".json", ".instructions.json"))
        self.assertEqual(result["index"], str(sidecar))
        index = json.loads(sidecar.read_text())
        self.assertEqual(index["ref"], self.box.git("rev-parse", "HEAD").strip())
        summary = json.loads(path.read_text())["instructions"]
        self.assertEqual(
            summary,
            {"ref": index["ref"], "counts": {"always": 1, "scoped": 0, "reference": 0}, "combined_hash": index["combined_hash"]},
        )
        self.assertEqual(result["counts"], summary["counts"])
        self.assertEqual(result["always_bytes"], len("# A\n"))
        self.assertIsNone(result["committed"])
        self.assertIsNone(result["error"])

    def test_pending_adoption_scans_the_adopted_branch(self):
        self.add({"AGENTS.md": "# A\n"})
        self.box.git("checkout", "-q", "-b", "feat")
        self.add({"GEMINI.md": "# G\n"})
        self.box.git("checkout", "-q", "-")
        path = self.pending("adopt-feat", branch="feat", spec_dir="specs/feat")
        result = json.loads(self.box.cli("instructions-record").stdout)
        self.assertEqual(result["ref"], self.box.git("rev-parse", "feat").strip())
        self.assertEqual(result["counts"]["always"], 2)
        self.assertTrue(path.with_name(path.name.replace(".json", ".instructions.json")).is_file())

    def test_worktree_run_commits_the_index_only_when_it_changed(self):
        self.add({"AGENTS.md": "# A\n"})
        wt = self.box.worktree_run("025-b", self.state())
        first = json.loads(self.box.cli("instructions-record", cwd=wt).stdout)
        self.assertTrue(first["committed"])
        target = wt / "specs" / "025-b" / "factory" / "instructions.json"
        self.assertTrue(target.is_file())
        self.assertIn("factory: instructions recorded", self.box.git("log", "--oneline", "-1", cwd=wt))
        second = json.loads(self.box.cli("instructions-record", cwd=wt).stdout)
        self.assertIsNone(second["committed"])

    def test_no_writable_run_exits_1_and_writes_nothing(self):
        self.add({"AGENTS.md": "# A\n"})
        out = self.box.cli("instructions-record")
        self.assertEqual(out.returncode, 1)
        self.assertEqual(list((self.box.home / "pending").glob("*")), [])

    def test_live_lock_exits_1_and_writes_nothing(self):
        self.add({"AGENTS.md": "# A\n"})
        path = self.pending("025-c")
        path.with_suffix(".lock.json").write_text(
            json.dumps({"owner_pid": os.getpid(), "host": socket.gethostname(), "harness": "x", "acquired_at": "2026-01-01T00:00:00Z"})
        )
        out = self.box.cli("instructions-record")
        self.assertEqual(out.returncode, 1, out.stderr)
        self.assertNotIn("instructions", json.loads(path.read_text()))
        self.assertFalse(path.with_name(path.name.replace(".json", ".instructions.json")).exists())

    def test_validate_checks_the_instructions_summary_types(self):
        good = {"ref": "a" * 40, "counts": {"always": 0, "scoped": 0, "reference": 0}, "combined_hash": "sha256:x"}
        for bad in ({**good, "counts": 3}, {**good, "ref": 7}):
            with self.subTest(bad=bad):
                self.pending("025-d", instructions=bad)
                out = self.box.cli("validate", "--all")
                self.assertEqual(out.returncode, 1, out.stdout)
                self.assertIn("instructions", out.stdout)
        self.pending("025-d", instructions=good)
        self.assertEqual(self.box.cli("validate", "--all").returncode, 0)
        self.pending("025-d")
        self.assertEqual(self.box.cli("validate", "--all").returncode, 0)


class DeltaAndWarningTests(RecordBase):
    def record(self):
        out = self.box.cli("instructions-record")
        self.assertEqual(out.returncode, 0, out.stderr)
        return json.loads(out.stdout)

    def test_delta_lists_added_removed_and_changed_paths_sorted(self):
        self.add({"AGENTS.md": "# A\n", "GEMINI.md": "# G\n", "CONVENTIONS.md": "# C\n", ".rules": "r\n"})
        self.pending("025-e")
        self.assertIsNone(self.record()["delta"])
        self.box.git("rm", "-q", "GEMINI.md")
        self.add({"CONVENTIONS.md": "# C2\n", "docs/adr/0001-x.md": "# x\n", ".rules": "r\n"})
        self.assertEqual(
            self.record()["delta"],
            {"added": ["docs/adr/0001-x.md"], "removed": ["GEMINI.md"], "changed": ["CONVENTIONS.md"]},
        )
        # a kind change counts as changed; alias and title changes do not
        self.add({".rules": "r\n", "AGENTS.md": "# Renamed title\n"})
        self.assertEqual(self.record()["delta"], {"added": [], "removed": [], "changed": ["AGENTS.md"]})
        self.add({"CLAUDE.md": "# Renamed title\n"})
        self.assertEqual(self.record()["delta"], {"added": [], "removed": [], "changed": []})

    def test_kind_change_is_a_change(self):
        self.add({"DESIGN.md": "# D\n", "AGENTS.md": "# A\n", ".factory/config.json": config(reference=["DESIGN.md"])})
        self.pending("025-f")
        self.record()
        self.add({".factory/config.json": config(include=["DESIGN.md"])})
        self.assertIn("DESIGN.md", self.record()["delta"]["changed"])

    def test_warning_above_32_kib_of_always_entries(self):
        files = {"AGENTS.md": "a" * 20000, "GEMINI.md": "b" * 20000}
        files.update({f"docs/adr/{i}.md": f"x{i}" for i in range(3)})
        self.add(files)
        self.pending("025-g")
        result = self.record()
        self.assertEqual(result["warning"]["limit"], 32768)
        self.assertEqual(result["warning"]["always_bytes"], 40000)
        self.assertEqual(result["warning"]["largest"], [{"path": "AGENTS.md", "size": 20000}, {"path": "GEMINI.md", "size": 20000}])
        self.assertEqual(len(json.loads(Path(result["index"]).read_text())["entries"]), 5)

    def test_empty_repository_flags_empty(self):
        self.add({"README.md": "# r\n"})
        self.pending("025-h")
        result = self.record()
        self.assertTrue(result["empty"])
        self.assertEqual(result["counts"], {"always": 0, "scoped": 0, "reference": 0})

    def test_unresolvable_base_reports_error_keeps_the_summary_and_writes_nothing(self):
        self.add({"AGENTS.md": "# A\n"})
        path = self.pending("025-i")
        self.record()
        before = path.read_text()
        data = json.loads(before)
        data["base"] = "no-such-ref"
        path.write_text(json.dumps(data, indent=2) + "\n")
        result = self.record()
        self.assertIn("no-such-ref", result["error"])
        self.assertEqual(json.loads(path.read_text())["instructions"], json.loads(before)["instructions"])

    def test_unreadable_previous_index_gives_null_delta_and_a_note(self):
        self.add({"AGENTS.md": "# A\n"})
        path = self.pending("025-j")
        self.record()
        path.with_name(path.name.replace(".json", ".instructions.json")).write_text("{broken")
        result = self.record()
        self.assertIsNone(result["delta"])
        self.assertTrue([n for n in result["notes"] if n.startswith("previous index unreadable")])


if __name__ == "__main__":
    unittest.main()
