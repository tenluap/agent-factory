"""Repo instruction discovery (spec 025, ADR 0020).

Reads the tracked instruction files of a repository at one ref, straight from
git objects (never the working tree), and classifies them into an index.
Standard library and git only. argv lists only, never a shell.
"""

import hashlib
import json
import posixpath
import subprocess

# One row per tool: (name, path patterns, default kind). A pattern is a file
# name or a directory-relative path; each matches at any depth. Source URLs
# live in specs/025-repo-instructions-discovery/research.md (R2).
CATALOGUE = (
    ("agents-md", ("AGENTS.md", "AGENTS.override.md", "AGENT.md"), "always"),
    ("claude-code", ("CLAUDE.md", ".claude/CLAUDE.md", "CLAUDE.local.md"), "always"),
    ("gemini", ("GEMINI.md",), "always"),
    ("aider", ("CONVENTIONS.md",), "always"),
)

KIND_ORDER = {"always": 0, "scoped": 1, "reference": 2}
SYMLINK_HOPS = 8


class ScanError(Exception):
    """The scan cannot run (the ref does not resolve, git failed)."""


def _git(repo, args, data=None):
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), *args], input=data, capture_output=True
        )
    except OSError as err:
        raise ScanError("git not runnable") from err
    if out.returncode != 0:
        raise ScanError(out.stderr.decode("utf-8", "replace").strip())
    return out.stdout


def resolve_ref(repo, ref):
    """The commit sha `ref` names; ScanError when it names no commit."""
    try:
        out = _git(repo, ["rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"])
    except ScanError as err:
        raise ScanError(f"ref does not resolve to a commit: {ref}") from err
    return out.decode().strip()


def read_tree(repo, sha):
    """{path: (mode, object id)} of every tracked blob; gitlinks dropped."""
    tree = {}
    raw = _git(repo, ["ls-tree", "-r", "-z", "--full-tree", sha])
    for record in raw.split(b"\0"):
        if not record:
            continue
        meta, _, path = record.partition(b"\t")
        mode, kind, oid = meta.decode().split()
        if kind == "blob":
            tree[path.decode("utf-8", "surrogateescape")] = (mode, oid)
    return tree


def read_blobs(repo, oids):
    """{oid: bytes} through one `git cat-file --batch` process."""
    wanted = sorted(set(oids))
    if not wanted:
        return {}
    raw = _git(
        repo, ["cat-file", "--batch"], data="".join(f"{o}\n" for o in wanted).encode()
    )
    blobs, pos = {}, 0
    for oid in wanted:
        end = raw.index(b"\n", pos)
        size = int(raw[pos:end].split()[2])
        blobs[oid] = raw[end + 1 : end + 1 + size]
        pos = end + 1 + size + 1
    return blobs


def _resolve_symlink(path, tree, blobs_of):
    """The regular-file path a tracked symlink reaches inside the repo, or None."""
    seen = set()
    for _ in range(SYMLINK_HOPS):
        mode, oid = tree[path]
        if mode != "120000":
            return path
        if path in seen:
            return None
        seen.add(path)
        target = posixpath.normpath(
            posixpath.join(
                posixpath.dirname(path), blobs_of(oid).decode("utf-8", "replace")
            )
        )
        if target.startswith("..") or target.startswith("/") or target not in tree:
            return None
        path = target
    return None


def _catalogue_match(path):
    """The default kind of a catalogue file at `path`, or None."""
    for _, patterns, kind in CATALOGUE:
        for pattern in patterns:
            if path == pattern or path.endswith("/" + pattern):
                return kind
    return None


def _title(text, path):
    for line in text.splitlines():
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return posixpath.basename(path)


def _entry_json(entry):
    return {k: entry[k] for k in sorted(entry)}


def scan(repo, ref="HEAD"):
    """The instruction index of `repo` at `ref` (data-model.md)."""
    sha = resolve_ref(repo, ref)
    tree = read_tree(repo, sha)
    notes = []
    cache = {}

    def blob(oid):
        if oid not in cache:
            cache.update(read_blobs(repo, [oid]))
        return cache[oid]

    candidates = [p for p in sorted(tree) if _catalogue_match(p)]
    cache.update(read_blobs(repo, [tree[p][1] for p in candidates]))

    groups = {}
    for path in candidates:
        real = _resolve_symlink(path, tree, blob)
        if real is None:
            notes.append(f"symlink skipped: {path}")
            continue
        content = blob(tree[real][1])
        digest = "sha256:" + hashlib.sha256(content).hexdigest()
        groups.setdefault((digest, _catalogue_match(path), "/"), []).append(
            (path, real, content)
        )

    entries = []
    for (digest, kind, scope), members in groups.items():
        regular = sorted(m for m in members if tree[m[0]][0] != "120000")
        primary = (regular or sorted(members))[0]
        text = primary[2].decode("utf-8", "replace")
        entries.append(
            {
                "path": primary[0],
                "kind": kind,
                "scope": [scope],
                "size": len(primary[2]),
                "hash": digest,
                "title": _title(text, primary[0]),
                "aliases": sorted(m[0] for m in members if m[0] != primary[0]),
                "source": "catalogue",
            }
        )
    entries.sort(key=lambda e: (KIND_ORDER[e["kind"]], e["path"]))
    entries = [_entry_json(e) for e in entries]
    combined = hashlib.sha256(
        json.dumps(entries, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return {
        "combined_hash": "sha256:" + combined,
        "entries": entries,
        "notes": sorted(notes),
        "ref": sha,
    }
