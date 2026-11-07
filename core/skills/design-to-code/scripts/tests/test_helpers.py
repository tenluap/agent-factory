#!/usr/bin/env python3
"""Exit-code and output checks for the design-to-code helper scripts.

Usage: python3 -P tests/test_helpers.py
Run with -P: pixel-diff.py needs numpy and Pillow from the user site-packages.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

HELPERS = Path(__file__).resolve().parent.parent

ROWS = (
    "R\tframe\tRoot\t0\t0\t100\t50\t400\t300\t\t\n"
    "A\tframe\tCard\t1\t0\t16.25\t16\t200\t100\t\t\n"
    "B\ttext\tTitle\t2\t0\t12.4\t8\t120\t20\t\t\n"
    "C\tframe\tCard\t1\t1\t16\t132\t200\t100\t\t\n"
    "D\ttext\tTitle\t2\t0\t12\t8\t120\t20\t\t\n"
)

MAP = {
    "version": 3,
    "framework": "avalonia",
    "targets": [
        {
            "components": [
                {
                    "designId": "B",
                    "code": {"file": "Views/Card.axaml", "anchor": "Card1/Title"},
                }
            ],
            "instances": [
                {
                    "designId": "C",
                    "codeAnchor": {"file": "Views/Main.axaml", "anchor": "Card2"},
                }
            ],
            "nodeMap": [
                {"designId": "R", "codeAnchor": {"anchor": "Root"}},
                {"designId": "A", "codeAnchor": {"xName": "Card1"}},
                {"designId": "D", "codeAnchor": {"anchor": "Card2/Title"}},
            ],
        }
    ],
}

BOUNDS = {
    "root": "Root",
    "elements": {
        "Root": {"x": 0, "y": 0, "width": 400, "height": 300},
        "Card1": {"x": 16, "y": 16, "width": 200, "height": 100},
        "Card1/Title": {"x": 28.6, "y": 24, "width": 120, "height": 20},
        "Card2": {"x": 16, "y": 132, "width": 200, "height": 100},
        "Card2/Title": {"x": 28, "y": 140, "width": 120, "height": 20},
    },
}


def run(script, *args, cwd=None):
    command = ["node"] if script.endswith(".mjs") else [sys.executable, "-P"]
    return subprocess.run(
        [*command, str(HELPERS / script), *map(str, args)],
        capture_output=True,
        text=True,
        cwd=cwd,
    )


class HelperTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.dir = Path(self.temp.name)
        self.rows = self.write("rows.txt", ROWS)
        self.map = self.write("map.json", json.dumps(MAP))

    def tearDown(self):
        self.temp.cleanup()

    def write(self, name, text):
        path = self.dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def bounds(self, **changes):
        doc = json.loads(json.dumps(BOUNDS))
        for key, value in changes.items():
            if key == "root":
                doc["root"] = value
            else:
                name, field = key.split("__")
                doc["elements"][name.replace("_", "/")][field] = value
        return self.write("bounds.json", json.dumps(doc))

    # bounds-diff.py

    def test_bounds_pass_with_repeated_names(self):
        result = run("bounds-diff.py", self.rows, self.bounds(), self.map)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("checked 5 nodes, 0 mismatches", result.stderr)

    def test_bounds_mismatch(self):
        result = run(
            "bounds-diff.py", self.rows, self.bounds(Card2_Title__y=150), self.map
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("D\tCard2/Title\ty\t140\t150", result.stdout)

    def test_bounds_tolerance(self):
        bounds = self.bounds(Card2_Title__y=142)
        self.assertEqual(
            run("bounds-diff.py", self.rows, bounds, self.map).returncode, 1
        )
        self.assertEqual(
            run("bounds-diff.py", self.rows, bounds, self.map, "--tol", 3).returncode, 0
        )

    def test_bounds_input_errors(self):
        cases = [
            (
                self.rows,
                self.write("other-root.json", json.dumps(dict(BOUNDS, root="Other"))),
                self.map,
            ),
            (self.rows, self.dir / "missing.json", self.map),
            (self.write("bad.txt", "bad\n"), self.bounds(), self.map),
            (
                self.rows,
                self.write("empty.json", '{"root": "Root", "elements": {}}'),
                self.map,
            ),
        ]
        for args in cases:
            with self.subTest(args=args):
                self.assertEqual(run("bounds-diff.py", *args).returncode, 2)
        self.assertEqual(
            run(
                "bounds-diff.py", self.rows, self.bounds(), self.map, "--tol"
            ).returncode,
            2,
        )

    # map-coverage.py

    def test_coverage_keeps_anchors(self):
        result = run("map-coverage.py", self.rows, self.map)
        self.assertEqual(result.returncode, 0, result.stderr)
        records = {record["designId"]: record for record in json.loads(result.stdout)}
        self.assertEqual(records["D"]["codeAnchor"], {"anchor": "Card2/Title"})
        self.assertEqual(records["A"]["codeAnchor"], {"anchor": "Card1"})
        self.assertEqual(records["D"]["parentDesignId"], "C")
        self.assertEqual(
            records["B"]["codeAnchor"],
            {"file": "Views/Card.axaml", "anchor": "Card1/Title"},
        )

    def test_coverage_rejects_bad_rows(self):
        self.assertNotEqual(
            run("map-coverage.py", self.write("bad.txt", "bad\n"), self.map).returncode,
            0,
        )

    # map-revision.py

    def test_revision_tracks_dependencies(self):
        project = self.dir / "app"
        self.write("app/Views/Card.axaml", "<Card/>")
        self.write("app/Views/Main.axaml", "<Main/>")
        app = self.write("app/App.axaml", "<App/>")
        self.write("app/obj/App.axaml", "<Ignored/>")
        tokens = self.write("app/Styles/Tokens.axaml", "<Tokens/>")
        doc = dict(MAP, revisionFiles=["Styles/Tokens.axaml"])
        map_path = self.write("map2.json", json.dumps(doc))

        first = run("map-revision.py", map_path, project)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertRegex(first.stdout.strip(), r"^sha256:[0-9a-f]{16}$")

        tokens.write_text("<Tokens changed/>")
        second = run("map-revision.py", map_path, project).stdout
        self.assertNotEqual(first.stdout, second)

        app.write_text("<App changed/>")
        self.assertNotEqual(second, run("map-revision.py", map_path, project).stdout)

        self.write("app/obj/App.axaml", "<Still ignored/>")
        third = run("map-revision.py", map_path, project).stdout
        self.assertEqual(third, run("map-revision.py", map_path, project).stdout)

        maui = self.write("app/Maui/App.xaml", "<Maui/>")
        fourth = run("map-revision.py", map_path, project).stdout
        self.assertNotEqual(third, fourth)
        maui.write_text("<Maui changed/>")
        self.assertNotEqual(fourth, run("map-revision.py", map_path, project).stdout)

        tokens.unlink()
        self.assertEqual(run("map-revision.py", map_path, project).returncode, 2)

    # map-migrate.py

    def test_migrate_version_1(self):
        doc = {
            "designSource": {"file": "a.pen"},
            "validation": {"theme": "light"},
            "nodeMap": [{"designId": "R", "codeAnchor": {"xName": "Root"}}],
        }
        path = self.write("v1.json", json.dumps(doc))
        result = run("map-migrate.py", path, "avalonia")
        self.assertEqual(result.returncode, 0, result.stderr)
        migrated = json.loads(path.read_text())
        self.assertEqual(migrated["version"], 3)
        self.assertEqual(migrated["framework"], "avalonia")
        target = migrated["targets"][0]
        self.assertEqual(target["validation"], [{"theme": "light"}])
        self.assertEqual(target["nodeMap"][0]["codeAnchor"], {"anchor": "Root"})
        self.assertTrue((self.dir / "v1.json.bak").exists())

    def test_migrate_version_2_and_current(self):
        doc = json.loads(json.dumps(MAP))
        doc["version"] = 2
        del doc["framework"]
        doc["targets"][0]["nodeMap"][0]["codeAnchor"] = {"xName": "Root"}
        path = self.write("v2.json", json.dumps(doc))
        self.assertEqual(run("map-migrate.py", path, "maui").returncode, 0)
        migrated = json.loads(path.read_text())
        self.assertEqual(migrated["framework"], "maui")
        self.assertEqual(
            migrated["targets"][0]["nodeMap"][0]["codeAnchor"], {"anchor": "Root"}
        )
        again = run("map-migrate.py", path, "maui")
        self.assertIn("already version 3", again.stdout)

    def test_migrate_input_errors(self):
        self.assertEqual(run("map-migrate.py", self.map, "flutter").returncode, 2)
        self.assertEqual(
            run("map-migrate.py", self.dir / "missing.json", "react").returncode, 2
        )

    # tests/evals/qa-html/check.py

    def test_qa_eval_fixture_has_three_defects(self):
        evals = HELPERS.parent / "tests" / "evals" / "qa-html"
        result = subprocess.run(
            [
                sys.executable,
                "-I",
                str(evals / "check.py"),
                str(evals / "fixture"),
                "--no-report",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(result.stdout.count("FAIL "), 3, result.stdout)

    def test_qa_locked_fixture_needs_fixes(self):
        evals = HELPERS.parent / "tests" / "evals"
        result = subprocess.run(
            [sys.executable, "-I", str(evals / "qa-html" / "check.py"), str(evals / "qa-locked" / "fixture"), "--no-report", "--locked"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(result.stdout.count("FAIL "), 2, result.stdout)
        self.assertIn("PASS muted paragraph color kept", result.stdout)

    def test_implement_eval_fixture_has_no_map(self):
        evals = HELPERS.parent / "tests" / "evals" / "implement-html"
        result = subprocess.run(
            [sys.executable, "-I", str(evals / "check.py"), str(evals / "fixture")],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("FAIL map unreadable", result.stdout)
        rows = (evals / "expected" / "rows.txt").read_text().splitlines()
        self.assertEqual(len(rows), 7)
        self.assertEqual(Image.open(evals / "expected" / "dqvK9.png").size, (720, 448))

    # web-capture.mjs

    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_web_capture_input_errors(self):
        self.assertEqual(run("web-capture.mjs", "--url", "x").returncode, 2)
        missing = run(
            "web-capture.mjs",
            *"--url http://localhost --root R --out o --scale 2 --theme light --width 10 --height 10".split(),
            cwd=self.dir,
        )
        self.assertEqual(missing.returncode, 2)
        self.assertIn("Playwright not found", missing.stderr)

    @unittest.skipUnless(
        os.environ.get("WEB_CAPTURE_PROJECT"),
        "set WEB_CAPTURE_PROJECT to a directory with playwright installed",
    )
    def test_web_capture_live(self):
        page = self.write(
            "page.html",
            '<body style="margin:0"><div data-design-id="Root" '
            'style="width:200px;height:100px;padding:16px;box-sizing:border-box;background:#fff">'
            '<div data-design-id="Card1" style="width:100px;height:40px">'
            '<span data-design-id="Title" style="display:block;height:20px">Hi</span>'
            "</div></div></body>",
        )
        out = self.dir / "out"
        result = run(
            "web-capture.mjs",
            "--url",
            page.as_uri(),
            "--root",
            "Root",
            "--out",
            out,
            "--scale",
            2,
            "--theme",
            "light",
            "--width",
            200,
            "--height",
            100,
            cwd=os.environ["WEB_CAPTURE_PROJECT"],
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        bounds = json.loads((out / "bounds.json").read_text())
        self.assertEqual(bounds["root"], "Root")
        self.assertEqual(bounds["elements"]["Card1/Title"]["y"], 16)
        self.assertEqual(Image.open(out / "capture.png").size, (400, 200))

    # pixel-diff.py

    def image(self, name, size=(40, 30), box=None):
        image = Image.new("RGB", size, (255, 255, 255))
        if box:
            image.paste((0, 0, 0), box)
        path = self.dir / name
        image.save(path)
        return path

    def test_pixel_identical(self):
        result = run(
            "pixel-diff.py", self.image("a.png"), self.image("b.png"), "--max-diff", 0.5
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("differing pixels: 0.00%", result.stdout)

    def test_pixel_over_threshold(self):
        result = run(
            "pixel-diff.py",
            self.image("a.png"),
            self.image("b.png", box=(0, 0, 10, 10)),
            "--max-diff",
            0.5,
        )
        self.assertEqual(result.returncode, 1)

    def test_pixel_size_mismatch(self):
        result = run(
            "pixel-diff.py", self.image("a.png"), self.image("b.png", size=(41, 30))
        )
        self.assertEqual(result.returncode, 3)

    def test_pixel_input_error(self):
        self.assertEqual(
            run(
                "pixel-diff.py", self.image("a.png"), self.dir / "missing.png"
            ).returncode,
            2,
        )
        self.assertEqual(run("pixel-diff.py", self.image("a.png")).returncode, 2)


if __name__ == "__main__":
    unittest.main(verbosity=1)
