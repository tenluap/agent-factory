#!/usr/bin/env python3
"""Build nodeMap records for one target of a design-code map.

Usage: python3 -P map-coverage.py <rows.txt> <map.json> [target-index]

rows.txt is the survey's tab-separated rows: id, type, name, depth, index, x, y,
width, height, ref, problems. A row is covered by itself when it is mapped (a
component, an instance, or a nodeMap entry with codeAnchor). Otherwise it is covered
by its nearest mapped ancestor. Rows without a mapped ancestor get status "unmapped".
Prints a JSON array. Merge it into the target's nodeMap with jq.
"""

import json
import sys
from pathlib import Path


def code_anchor(code):
    """Convert a component's code record into the nodeMap codeAnchor shape."""
    if not isinstance(code, dict):
        return None
    anchor = {key: code[key] for key in ("file", "symbol") if code.get(key)}
    if code.get("anchor"):
        anchor["anchor"] = code["anchor"]
    return anchor or None


def current_anchor(anchor):
    """Rename a version 2 codeAnchor.xName to the version 3 codeAnchor.anchor."""
    if isinstance(anchor, dict) and "xName" in anchor and "anchor" not in anchor:
        anchor = dict(anchor)
        anchor["anchor"] = anchor.pop("xName")
    return anchor


def main():
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    rows_path, map_path = Path(sys.argv[1]), Path(sys.argv[2])
    index = int(sys.argv[3]) if len(sys.argv) == 4 else 0
    doc = json.loads(map_path.read_text()) if map_path.exists() else {}
    target = doc["targets"][index] if "targets" in doc else doc

    mapped = {}
    for record in target.get("components", []) + target.get("instances", []):
        mapped[record["designId"]] = record
    for record in target.get("nodeMap", []):
        if record.get("codeAnchor"):
            mapped.setdefault(record["designId"], record)

    records, stack = [], []
    for line in rows_path.read_text().splitlines():
        if not line.strip():
            continue
        columns = line.split("\t")
        if len(columns) != 11:
            sys.exit(
                f"{rows_path}: expected 11 tab-separated columns, got {len(columns)}: {line[:60]!r}"
            )
        design_id, depth = columns[0], int(columns[3])
        while stack and stack[-1][0] >= depth:
            stack.pop()
        parent = stack[-1][1] if stack else None
        inherited = stack[-1][2] if stack else None
        record = mapped.get(design_id)
        if record is not None:
            covered = design_id
            anchor = current_anchor(record.get("codeAnchor")) or code_anchor(
                record.get("code")
            )
            status = record.get("status", "planned")
        else:
            covered = inherited
            anchor = None
            status = "planned" if covered else "unmapped"
        records.append(
            {
                "designId": design_id,
                "parentDesignId": parent,
                "coveredBy": covered,
                "codeAnchor": anchor,
                "status": status,
            }
        )
        stack.append((depth, design_id, covered))
    json.dump(records, sys.stdout, indent=1)
    print()


if __name__ == "__main__":
    main()
