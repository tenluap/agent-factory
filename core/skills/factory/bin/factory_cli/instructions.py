"""Repo instruction discovery (spec 025, ADR 0020).

Reads the tracked instruction files of a repository at one ref, straight from
git objects (never the working tree), and classifies them into an index.
Standard library and git only. argv lists only, never a shell.
"""

import hashlib
import json
import posixpath
import re
import subprocess

# One row per tool: (name, ((pattern, default kind), ...)). A pattern is a glob
# (glob_regex) matched at any depth; the directory holding the match's first
# segment is its base directory. Source URLs live in
# specs/025-repo-instructions-discovery/research.md (R2).
CATALOGUE = (
    ("agents-md", (("AGENTS.md", "always"), ("AGENTS.override.md", "always"), ("AGENT.md", "always"))),
    (
        "claude-code",
        (
            ("CLAUDE.md", "always"),
            (".claude/CLAUDE.md", "always"),
            ("CLAUDE.local.md", "always"),
            (".claude/rules/**/*.md", "always"),
        ),
    ),
    ("gemini", (("GEMINI.md", "always"),)),
    (
        "copilot",
        (
            (".github/copilot-instructions.md", "always"),
            (".github/instructions/**/*.instructions.md", "reference"),
        ),
    ),
    ("cursor", ((".cursor/rules/**/*.mdc", "reference"), (".cursorrules", "always"))),
    (
        "windsurf-devin",
        tuple(
            (pattern, "always")
            for pattern in (
                ".windsurf/rules/*.md",
                ".windsurf/global_rules.md",
                ".windsurfrules",
                ".devin/rules/*.md",
                ".devin/global_rules.md",
            )
        ),
    ),
    (
        "cline",
        (
            (".clinerules", "always"),
            (".clinerules/**/*.md", "always"),
            (".clinerules/**/*.txt", "always"),
            (".cline/rules/**/*.md", "always"),
            (".cline/rules/**/*.txt", "always"),
        ),
    ),
    (
        "roo",
        (
            (".roo/rules/**/*.md", "always"),
            (".roo/rules/**/*.txt", "always"),
            (".roorules", "always"),
            (".roo/rules-*/**/*.md", "reference"),
            (".roo/rules-*/**/*.txt", "reference"),
            (".roorules-*", "reference"),
        ),
    ),
    (
        "junie",
        tuple(
            (pattern, "always")
            for pattern in (
                ".junie/AGENTS.md",
                ".junie/rules/*.md",
                ".junie/playbook.md",
                ".junie/guidelines.md",
                ".junie/guidelines/**/*.md",
            )
        ),
    ),
    ("kiro", ((".kiro/steering/*.md", "always"),)),
    ("aider", (("CONVENTIONS.md", "always"),)),
    ("zed", ((".rules", "always"),)),
    ("continue", ((".continue/rules/*.md", "always"),)),
)

# Directories whose CONTRIBUTING* file applies to the whole repository.
ROOT_GOVERNANCE_DIRS = ("", ".github", "docs")
CONSTITUTION = ".specify/memory/constitution.md"
ADR_PARENTS = ("doc", "docs", "architecture")

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


def glob_regex(glob):
    """An anchored regex for `glob`: `**/` zero or more directories, `**` any
    characters, `*` any characters but `/`, `?` one non-`/` character."""
    out, i = [], 0
    while i < len(glob):
        if glob.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif glob.startswith("**", i):
            out.append(".*")
            i += 2
        elif glob[i] == "*":
            out.append("[^/]*")
            i += 1
        elif glob[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(glob[i]))
            i += 1
    return re.compile("".join(out) + r"\Z")


_ROWS = tuple(
    (glob_regex(pattern), kind, name)
    for name, patterns in CATALOGUE
    for pattern, kind in patterns
)


def _suffixes(path):
    """(base directory, rest) for every directory boundary of `path`."""
    yield "", path
    for i, ch in enumerate(path):
        if ch == "/":
            yield path[:i], path[i + 1 :]


def _is_adr(path):
    parts = path.lower().split("/")
    if not parts[-1].endswith((".md", ".markdown")):
        return False
    dirs = parts[:-1]
    return any(
        d in ("adr", "adrs") or (d == "decisions" and i and dirs[i - 1] in ADR_PARENTS)
        for i, d in enumerate(dirs)
    )


def classify_path(path):
    """(kind, base directory, row) of a tracked path by catalogue, or the
    governance result (kind, scope list, "governance"); None when neither."""
    for base, rest in _suffixes(path):
        for regex, kind, row in _ROWS:
            if regex.match(rest):
                return kind, base, row
    directory, _, name = path.rpartition("/")
    if name.startswith("CONTRIBUTING"):
        if directory in ROOT_GOVERNANCE_DIRS:
            return "always", ["/"], "governance"
        return "scoped", [directory + "/"], "governance"
    if path == CONSTITUTION:
        return "always", ["/"], "governance"
    if _is_adr(path):
        return "reference", ["/"], "governance"
    return None


def front_matter(text):
    """({key: str | list}, body) of a leading `---` block; (None, text) when the
    block is unclosed or malformed (research R5); ({}, text) when absent."""
    lines = text.split("\n")
    if lines[0].strip() != "---":
        return {}, text
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return None, text
    fields, key = {}, None
    for line in lines[1:end]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- ") and key is not None and fields[key] == "":
            fields[key] = []
        if stripped.startswith("- ") and isinstance(fields.get(key), list):
            fields[key].append(stripped[2:].strip().strip("\"'"))
            continue
        name, colon, value = stripped.partition(":")
        if not colon or " " in name:
            return None, text
        key, value = name, value.strip()
        if value.startswith("[") and value.endswith("]"):
            fields[key] = [v.strip().strip("\"'") for v in value[1:-1].split(",") if v.strip()]
        else:
            fields[key] = value.strip("\"'")
    return fields, "\n".join(lines[end + 1 :])


def _globs(value):
    items = value if isinstance(value, list) else value.split(",")
    return [g.strip() for g in items if g.strip()]


def _mapped(row, fields):
    """(kind, globs) the row's front matter implies, or None for the default."""
    flag = fields.get("alwaysApply", "").lower() if isinstance(fields.get("alwaysApply"), str) else ""
    if row in ("cursor", "continue"):
        if flag == "true":
            return "always", []
        if fields.get("globs"):
            return "scoped", _globs(fields["globs"])
        return ("reference", []) if row == "continue" and flag == "false" else None
    if row == "copilot" and fields.get("applyTo"):
        return "scoped", _globs(fields["applyTo"])
    if row in ("claude-code", "cline") and fields.get("paths"):
        return "scoped", _globs(fields["paths"])
    if row == "kiro":
        inclusion = fields.get("inclusion")
        if inclusion == "fileMatch" and fields.get("fileMatchPattern"):
            return "scoped", _globs(fields["fileMatchPattern"])
        return ("reference", []) if inclusion in ("manual", "auto") else None
    if row == "windsurf-devin":
        trigger = fields.get("trigger")
        if trigger == "always_on":
            return "always", []
        if trigger == "glob" and fields.get("globs"):
            return "scoped", _globs(fields["globs"])
        return ("reference", []) if trigger in ("model_decision", "manual") else None
    return None


def _kind_scope(kind, base, globs):
    """Final (kind, scope) of a catalogue match at `base` with derived `globs`."""
    prefix = base + "/" if base else ""
    if globs and not (not base and set(globs) <= {"**", "**/*"}):
        return "scoped", [prefix + g for g in globs]
    if kind == "scoped" or (kind == "always" and base):
        return ("scoped", [prefix]) if base else ("always", ["/"])
    return kind, ["/"] if kind == "always" or not base else [prefix]


def _title(text, path, fields=None):
    for line in text.splitlines():
        if line.startswith("#"):
            return line.lstrip("#").strip()
    if fields and isinstance(fields.get("description"), str) and fields["description"]:
        return fields["description"]
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

    candidates = [p for p in sorted(tree) if classify_path(p)]
    cache.update(read_blobs(repo, [tree[p][1] for p in candidates]))

    groups = {}
    for path in candidates:
        real = _resolve_symlink(path, tree, blob)
        if real is None:
            notes.append(f"symlink skipped: {path}")
            continue
        content = blob(tree[real][1])
        digest = "sha256:" + hashlib.sha256(content).hexdigest()
        kind, where, row = classify_path(path)
        title_fields = None
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            text = None
            notes.append(f"not UTF-8: {path}")
        if row == "governance":
            scope, source = tuple(where), "governance"
        else:
            fields, text_body = front_matter(text) if text is not None else ({}, "")
            if fields is None:
                notes.append(f"front matter unparseable: {path}")
                fields = {}
            title_fields = fields
            mapped = _mapped(row, fields)
            kind, globs = mapped if mapped else (kind, [])
            kind, scope = _kind_scope(kind, where, globs)
            scope, source = tuple(scope), "catalogue"
        title = "" if text is None else _title(text_body if row != "governance" else text, path, title_fields)
        groups.setdefault((digest, kind, scope, source), []).append(
            (path, real, content, title)
        )

    entries = []
    for (digest, kind, scope, source), members in groups.items():
        regular = sorted(m for m in members if tree[m[0]][0] != "120000")
        primary = (regular or sorted(members))[0]
        entries.append(
            {
                "path": primary[0],
                "kind": kind,
                "scope": list(scope),
                "size": len(primary[2]),
                "hash": digest,
                "title": primary[3],
                "aliases": sorted(m[0] for m in members if m[0] != primary[0]),
                "source": source,
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
