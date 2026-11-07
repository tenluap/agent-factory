#!/usr/bin/env python3
"""Grade an implement-mode run on the implement-html fixture.

Usage: python3 -I check.py <run-dir>

<run-dir> is a copy of fixture/ (with tests/visual/node_modules linked to a
Playwright install) after design-to-code implemented frame dqvK9 ("Screen") of
design/cards.pen. Checks, independently of the agent's own claims:
  1. docs/design-code-map.json: version 3, framework html-js-css, frame dqvK9,
     component wYD2U with instanceCount 2, a passing light/2 validation record.
  2. Tokens: CSS custom properties hold #1A56DB and #F3F4F6.
  3. Fresh capture: starts commands.launch (if set), runs commands.capture into a
     temp dir, then bounds-diff.py against expected/rows.txt (all 7 nodes checked)
     and pixel-diff.py against expected/dqvK9.png at --max-diff 0.5.
  4. report.md contains "Status: complete".

Prints one PASS or FAIL line per check. Exit 0 all pass, 1 any fail, 2 input error.
"""

import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parents[2] / "scripts"
TARGET, COMPONENT, NODES = "dqvK9", "wYD2U", 7


def main():
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    root = Path(sys.argv[1]).resolve()
    results = []

    map_path = root / "docs" / "design-code-map.json"
    try:
        doc = json.loads(map_path.read_text())
    except (OSError, ValueError) as error:
        print(f"FAIL map unreadable: {error}")
        sys.exit(1)
    target = next(
        (
            t
            for t in doc.get("targets", [])
            if t.get("designSource", {}).get("frameId") == TARGET
        ),
        None,
    )
    results.append(
        (
            doc.get("version") == 3 and doc.get("framework") == "html-js-css",
            "map: version 3, html-js-css",
        )
    )
    results.append((target is not None, f"map: target {TARGET}"))
    target = target or {}
    component = next(
        (c for c in target.get("components", []) if c.get("designId") == COMPONENT), {}
    )
    results.append(
        (
            component.get("instanceCount") == 2,
            f"map: component {COMPONENT} instanceCount {component.get('instanceCount')}",
        )
    )
    record = next(
        (
            v
            for v in target.get("validation", [])
            if v.get("theme") == "light" and v.get("scale") == 2
        ),
        {},
    )
    results.append(
        (
            record.get("result") == "pass",
            f"map: validation record result {record.get('result')}",
        )
    )

    css = "\n".join(
        p.read_text() for p in root.rglob("*.css") if "node_modules" not in p.parts
    )
    for value in ("#1a56db", "#f3f4f6"):
        found = re.search(r"--[\w-]+\s*:\s*" + value, css, re.I)
        results.append((bool(found), f"tokens: custom property = {value}"))

    commands = doc.get("commands", {})
    capture = commands.get("capture", "")
    launch = commands.get("launch", "")
    if not capture:
        results.append((False, "capture: commands.capture missing"))
    else:
        server = None
        out = Path(tempfile.mkdtemp(prefix="d2c-grade-"))
        try:
            if launch:
                server = subprocess.Popen(
                    launch,
                    shell=True,
                    cwd=root,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                time.sleep(3)
            command = (
                capture.replace("<id>", TARGET)
                .replace("<dir>", str(out))
                .replace("<scale>", "2")
                .replace("<theme>", "light")
            )
            run = subprocess.run(
                command,
                shell=True,
                cwd=root,
                capture_output=True,
                text=True,
                timeout=300,
            )
            ok = (
                run.returncode == 0
                and (out / "capture.png").exists()
                and (out / "bounds.json").exists()
            )
            results.append(
                (ok, f"capture: exit {run.returncode} {run.stderr.strip()[-200:]}")
            )
            if ok:
                bounds = subprocess.run(
                    [
                        sys.executable,
                        "-P",
                        str(SCRIPTS / "bounds-diff.py"),
                        str(HERE / "expected" / "rows.txt"),
                        str(out / "bounds.json"),
                        str(map_path),
                    ],
                    capture_output=True,
                    text=True,
                )
                checked = re.search(r"checked (\d+) nodes", bounds.stderr)
                results.append(
                    (
                        bounds.returncode == 0
                        and checked
                        and int(checked.group(1)) == NODES,
                        f"bounds-diff: exit {bounds.returncode}, {bounds.stderr.strip()[-160:]}",
                    )
                )
                pixels = subprocess.run(
                    [
                        sys.executable,
                        "-P",
                        str(SCRIPTS / "pixel-diff.py"),
                        str(HERE / "expected" / f"{TARGET}.png"),
                        str(out / "capture.png"),
                        "--max-diff",
                        "0.5",
                    ],
                    capture_output=True,
                    text=True,
                )
                results.append(
                    (
                        pixels.returncode == 0,
                        f"pixel-diff: exit {pixels.returncode}, {pixels.stdout.strip()[-160:]}",
                    )
                )
        except subprocess.TimeoutExpired:
            results.append((False, "capture: timed out"))
        finally:
            if server:
                import os, signal

                try:
                    os.killpg(server.pid, signal.SIGTERM)
                except (PermissionError, ProcessLookupError):
                    try:  # the child may have its own pgid or be gone already
                        server.terminate()
                    except ProcessLookupError:
                        pass
            shutil.rmtree(out, ignore_errors=True)

    report = (root / "report.md").read_text() if (root / "report.md").exists() else ""
    results.append(("Status: complete" in report, "report: Status: complete"))

    for ok, message in results:
        print(("PASS " if ok else "FAIL ") + message)
    sys.exit(0 if all(ok for ok, _ in results) else 1)


if __name__ == "__main__":
    main()
