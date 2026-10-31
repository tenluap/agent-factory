#!/usr/bin/env python3
"""Compare survey geometry with the app's measured bounds for one target.

Usage: python3 -P bounds-diff.py <rows.txt> <bounds.json> <map.json> [target-index] [--tol N]

rows.txt is the survey's 11-column output. Its x and y are parent-relative; this
script sums them down the depth stack into target-root-relative coordinates, with
the target root at 0,0. bounds.json comes from the capture command:

  {"root": "<root anchor>", "elements": {"<anchor path>": {"x": 0, "y": 0, "width": 0, "height": 0}}}

Values are DIPs (CSS px on the web) relative to the root element. Keys are anchor
paths such as Card1/Title (see references/capture-contract.md). A row is checked
when the target's nodeMap, components, or instances map its design ID to an anchor
path (codeAnchor.anchor, then the version 2 codeAnchor.xName, then code.anchor).
The first row is the target root; it must
be mapped and match bounds.json "root". Mismatches over --tol DIPs (default 1)
print one per line as tab-separated id, anchor path, field, design, app. The
checked-node count goes to stderr.

Exit codes: 0 no mismatches, 1 mismatches, 2 input error (unreadable or malformed
input, unmapped or mismatched root, or a mapped anchor path missing from bounds.json).
"""

import json
import sys
from pathlib import Path

FIELDS = ("x", "y", "width", "height")


def anchor_path(record):
    anchor = record.get("codeAnchor")
    if isinstance(anchor, dict):
        for key in ("anchor", "xName"):
            if anchor.get(key):
                return anchor[key]
    code = record.get("code")
    if isinstance(code, dict) and code.get("anchor"):
        return code["anchor"]
    return None


def root_relative(rows_path):
    geometry, stack = {}, []
    for line in rows_path.read_text().splitlines():
        if not line.strip():
            continue
        columns = line.split("\t")
        if len(columns) != 11:
            raise ValueError(
                f"{rows_path}: expected 11 tab-separated columns, got {len(columns)}: {line[:60]!r}"
            )
        design_id, depth = columns[0], int(columns[3])
        x, y, width, height = (float(value) for value in columns[5:9])
        while stack and stack[-1][0] >= depth:
            stack.pop()
        if stack:
            x, y = stack[-1][1] + x, stack[-1][2] + y
        else:
            x, y = 0.0, 0.0
        geometry[design_id] = {"x": x, "y": y, "width": width, "height": height}
        stack.append((depth, x, y))
    return geometry


def fail(message):
    print(message, file=sys.stderr)
    sys.exit(2)


def load(args):
    tolerance = 1.0
    if "--tol" in args:
        position = args.index("--tol")
        tolerance = float(args[position + 1])
        del args[position : position + 2]
    if len(args) not in (3, 4):
        fail(__doc__)
    rows_path, bounds_path, map_path = (Path(value) for value in args[:3])
    index = int(args[3]) if len(args) == 4 else 0

    doc = json.loads(map_path.read_text())
    target = doc["targets"][index] if "targets" in doc else doc
    names = {}
    for record in (
        target.get("components", [])
        + target.get("instances", [])
        + target.get("nodeMap", [])
    ):
        name = anchor_path(record)
        if name:
            names.setdefault(record["designId"], name)

    design = root_relative(rows_path)
    bounds = json.loads(bounds_path.read_text())
    return tolerance, names, design, bounds


def main():
    try:
        tolerance, names, design, bounds = load(sys.argv[1:])
    except (OSError, ValueError, KeyError, IndexError, TypeError) as error:
        fail(f"input error: {error}")
    elements = bounds.get("elements", {})

    root_id = next(iter(design), None)
    if root_id not in names:
        fail(f"target root {root_id} has no mapped anchor")
    if bounds.get("root") != names[root_id]:
        fail(
            f"bounds.json root {bounds.get('root')!r} is not the mapped root {names[root_id]!r}"
        )

    missing = [
        name
        for design_id, name in names.items()
        if design_id in design and name not in elements
    ]
    if missing:
        fail("anchor missing from bounds.json: " + ", ".join(sorted(set(missing))))

    mismatches, checked = 0, 0
    for design_id, name in names.items():
        if design_id not in design:
            continue
        checked += 1
        for field in FIELDS:
            expected, actual = design[design_id][field], float(elements[name][field])
            if abs(expected - actual) > tolerance:
                mismatches += 1
                print(f"{design_id}\t{name}\t{field}\t{expected:g}\t{actual:g}")
    print(
        f"checked {checked} nodes, {mismatches} mismatches, tolerance {tolerance:g}",
        file=sys.stderr,
    )
    sys.exit(1 if mismatches else 0)


if __name__ == "__main__":
    main()
