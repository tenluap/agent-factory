#!/usr/bin/env python3
"""Hash the code files that a design-code map points at.

Usage: python3 -P map-revision.py <map.json> <project-root>

Collects code.file from components, codeAnchor.file from instances and nodeMap
records, across all targets, plus the map's top-level revisionFiles and every
framework entry file under the project root (App.axaml, App.xaml, MauiProgram.cs,
App.razor; bin, obj, node_modules, and dot directories skipped). Web entry files
(global CSS, layout, tokens) go in revisionFiles. Prints
sha256:<16 hex> over the sorted (path, content) pairs. Exits 2 when a listed file
is missing or the map is unreadable. Needs no git.
"""

import hashlib
import json
import sys
from pathlib import Path

SKIPPED = {"bin", "obj", "node_modules"}
ENTRY_FILES = ("App.axaml", "App.xaml", "MauiProgram.cs", "App.razor")


def anchor_file(anchor):
    if isinstance(anchor, dict) and anchor.get("file"):
        return anchor["file"]
    return None


def mapped_files(doc):
    files = set(doc.get("revisionFiles", []))
    for target in doc.get("targets", [doc]):
        for record in target.get("components", []):
            path = anchor_file(record.get("code"))
            if path:
                files.add(path)
        for record in target.get("instances", []) + target.get("nodeMap", []):
            path = anchor_file(record.get("codeAnchor"))
            if path:
                files.add(path)
    return files


def app_files(root):
    found = set()
    for name in ENTRY_FILES:
        for path in root.rglob(name):
            parts = path.relative_to(root).parts
            if any(part in SKIPPED or part.startswith(".") for part in parts[:-1]):
                continue
            found.add(path.relative_to(root).as_posix())
    return found


def main():
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    try:
        doc = json.loads(Path(sys.argv[1]).read_text())
    except (OSError, ValueError) as error:
        print(f"input error: {error}", file=sys.stderr)
        sys.exit(2)
    root = Path(sys.argv[2])
    digest = hashlib.sha256()
    for relative in sorted(mapped_files(doc) | app_files(root)):
        path = root / relative
        if not path.is_file():
            print(f"missing mapped file: {relative}", file=sys.stderr)
            sys.exit(2)
        digest.update(relative.encode() + b"\0" + path.read_bytes() + b"\0")
    print("sha256:" + digest.hexdigest()[:16])


if __name__ == "__main__":
    main()
