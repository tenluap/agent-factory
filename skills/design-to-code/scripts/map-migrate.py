#!/usr/bin/env python3
"""Upgrade a design-code map to version 3 in place.

Usage: python3 -P map-migrate.py <map.json> <framework>

Version 1 (top-level designSource, validation, components, ...) moves into
targets[0]. Version 2 codeAnchor.xName becomes codeAnchor.anchor. Version 3 adds a
top-level "framework" (avalonia, maui, blazor, react, nextjs, html-js-css). The old
file is kept as <map.json>.bak. A map already at version 3 is left untouched.

Exit codes: 0 migrated or already current, 2 input error.
"""

import json
import shutil
import sys
from pathlib import Path

FRAMEWORKS = {"avalonia", "maui", "blazor", "react", "nextjs", "html-js-css"}
TARGET_KEYS = (
    "designSource",
    "validation",
    "components",
    "instances",
    "nodeMap",
    "unmappedDesignNodes",
    "orphanedCode",
)


def rename_anchor(record):
    anchor = record.get("codeAnchor")
    if isinstance(anchor, dict) and "xName" in anchor:
        anchor.setdefault("anchor", anchor.pop("xName"))


def migrate(doc, framework):
    if "targets" not in doc:
        target = {key: doc.pop(key) for key in TARGET_KEYS if key in doc}
        if isinstance(target.get("validation"), dict):
            target["validation"] = [target["validation"]]
        doc["targets"] = [target]
    for target in doc["targets"]:
        for key in ("instances", "nodeMap"):
            for record in target.get(key, []):
                rename_anchor(record)
    doc["version"] = 3
    doc.setdefault("framework", framework)
    return doc


def main():
    if len(sys.argv) != 3 or sys.argv[2] not in FRAMEWORKS:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    path = Path(sys.argv[1])
    try:
        doc = json.loads(path.read_text())
    except (OSError, ValueError) as error:
        print(f"input error: {error}", file=sys.stderr)
        sys.exit(2)
    if doc.get("version") == 3:
        print("already version 3")
        return
    shutil.copyfile(path, path.with_name(path.name + ".bak"))
    path.write_text(json.dumps(migrate(doc, sys.argv[2]), indent=2) + "\n")
    print(f"migrated to version 3 ({sys.argv[2]})")


if __name__ == "__main__":
    main()
