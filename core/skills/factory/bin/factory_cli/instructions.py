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
import tempfile
from collections import namedtuple

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
SOURCE_ORDER = {"catalogue": 0, "governance": 0, "config": 0, "import": 1, "link": 2}
SYMLINK_HOPS = 8
IMPORT_HOPS = 4
CONFIG_PATH = ".factory/config.json"
# A blob above this is hashed by streaming and never held or parsed (ENG-24).
BLOB_CAP = 1 << 20
# Config-matched files (`include`/`reference`) are held up to this many bytes in
# total; past it they are indexed unparsed, their hash streamed (ENG-24).
CONFIG_BUDGET = 16 << 20
# A config glob longer than this is skipped with a note (ENG-24).
GLOB_CAP = 256


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
    if ref.startswith("-"):
        raise ScanError(f"ref does not resolve to a commit: {ref}")
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


Blob = namedtuple("Blob", "size digest data")


def _stream_digests(repo, oids):
    """{oid: sha256 digest} of blobs hashed in chunks in one `cat-file --batch`
    pass, so none is held in memory and one git process serves them all."""
    digests = {}
    if not oids:
        return digests
    with tempfile.TemporaryFile() as names:
        names.write("".join(f"{o}\n" for o in oids).encode())
        names.seek(0)
        try:
            with subprocess.Popen(
                ["git", "-C", str(repo), "cat-file", "--batch"],
                stdin=names, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            ) as proc:
                for oid in oids:
                    left, digest = int(proc.stdout.readline().split()[2]), hashlib.sha256()
                    while left:
                        chunk = proc.stdout.read(min(left, 1 << 16))
                        if not chunk:
                            raise ScanError(f"cannot read blob {oid}")
                        digest.update(chunk)
                        left -= len(chunk)
                    proc.stdout.read(1)
                    digests[oid] = "sha256:" + digest.hexdigest()
        except (OSError, ValueError, IndexError) as err:
            raise ScanError("cannot read blobs") from err
    return digests


def read_blobs(repo, oids, hold=None):
    """{oid: Blob(size, digest, data)}; sizes come first from `git cat-file
    --batch-check`. `data` is None for a blob above BLOB_CAP and for any blob
    that would take the bytes held past `hold` (in `oids` order); those are
    hashed by streaming."""
    wanted = list(dict.fromkeys(oids))
    if not wanted:
        return {}
    names = "".join(f"{o}\n" for o in wanted).encode()
    sizes = {}
    for line in _git(repo, ["cat-file", "--batch-check"], names).decode().splitlines():
        oid, _, size = line.split()
        sizes[oid] = int(size)
    small, held = [], 0
    for oid in wanted:
        if sizes[oid] <= BLOB_CAP and (hold is None or held + sizes[oid] <= hold):
            small.append(oid)
            held += sizes[oid]
    blobs = {}
    if small:
        raw = _git(repo, ["cat-file", "--batch"], "".join(f"{o}\n" for o in small).encode())
        pos = 0
        for oid in small:
            end = raw.index(b"\n", pos)
            data = raw[end + 1 : end + 1 + sizes[oid]]
            blobs[oid] = Blob(sizes[oid], "sha256:" + hashlib.sha256(data).hexdigest(), data)
            pos = end + 1 + sizes[oid] + 1
    rest = [o for o in wanted if o not in blobs]
    for oid, digest in _stream_digests(repo, rest).items():
        blobs[oid] = Blob(sizes[oid], digest, None)
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
        link = blobs_of(oid).data
        if link is None:
            return None
        target = posixpath.normpath(
            posixpath.join(posixpath.dirname(path), link.decode("utf-8", "replace"))
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


def glob_matcher(glob):
    """An object whose `match(path)` agrees with `glob_regex(glob).match` but runs
    a state-set simulation, linear in the path, so a hostile glob from the
    repository's config cannot make a regex backtrack catastrophically."""
    tokens, i = [], 0
    while i < len(glob):
        if glob.startswith("**/", i):
            tokens += [("opt",), ("lit", "/")]
            i += 3
        elif glob.startswith("**", i):
            tokens.append(("any",))
            i += 2
        else:
            tokens.append(("star",) if glob[i] == "*" else ("one",) if glob[i] == "?" else ("lit", glob[i]))
            i += 1
        if len(tokens) > 1 and tokens[-1][0] in ("star", "any") and tokens[-2][0] in ("star", "any"):
            # a run of wildcards matches what its widest member does: keep one token
            widest = "any" if "any" in (tokens[-1][0], tokens[-2][0]) else "star"
            tokens[-2:] = [(widest,)]
    return _Glob(tuple(tokens))


class _Glob:
    def __init__(self, tokens):
        self.tokens = tokens

    def _close(self, states):
        """`states` plus every position reached by skipping an optional token."""
        pending, seen = list(states), set(states)
        while pending:
            at = pending.pop()
            kind = self.tokens[at][0] if at < len(self.tokens) else None
            for nxt in {"star": (at + 1,), "any": (at + 1,), "opt": (at + 1, at + 2)}.get(kind, ()):
                if nxt not in seen:
                    seen.add(nxt)
                    pending.append(nxt)
        return seen

    def match(self, path):
        states = self._close({0})
        for ch in path:
            step = set()
            for at in states:
                if at == len(self.tokens):
                    continue
                kind, *arg = self.tokens[at]
                if kind in ("any", "opt") or (kind in ("star", "one") and ch != "/"):
                    step.add(at if kind in ("star", "any", "opt") else at + 1)
                elif kind == "lit" and ch == arg[0]:
                    step.add(at + 1)
            states = self._close(step)
            if not states:
                return False
        return len(self.tokens) in states


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


_IMPORT = re.compile(r"(?:^|\s)@(\S+)")
_LINK = re.compile(r"\]\(<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\)|^\s*\[[^\]]+\]:\s*<?(\S+?)>?\s*$")
_SCHEME = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*:")


def _prose(body):
    """Body lines outside fenced blocks, with inline code spans removed."""
    fenced = False
    for line in body.splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
        elif not fenced:
            yield re.sub(r"`[^`\n]*`", "", line)


def _imports(body):
    """`@path` tokens (sorted, unique) of the prose in `body`; `@~/...` and
    absolute paths are ignored."""
    found = set()
    for line in _prose(body):
        for token in _IMPORT.findall(line):
            token = token.rstrip(".,;:)")
            if ("/" in token or "." in token) and not token.startswith(("~", "/")):
                found.add(token)
    return sorted(found)


def _links(body):
    """Relative link targets (sorted, unique) of the prose in `body`."""
    found = set()
    for line in _prose(body):
        for match in _LINK.finditer(line):
            target = (match.group(1) or match.group(2)).split("#")[0].split("?")[0]
            if target and not _SCHEME.match(target):
                found.add(target)
    return sorted(found)


def _locate(token, importer, tree, relative_only=False):
    """The tracked path `token` names from `importer`: relative to its
    directory, then (imports only) to the repository root; None when it
    escapes the root or is not tracked."""
    here = posixpath.dirname(importer)
    roots = [token[1:]] if token.startswith("/") else [posixpath.join(here, token)]
    if not relative_only and not token.startswith("/"):
        roots.append(token)
    for candidate in roots:
        path = posixpath.normpath(candidate)
        if not path.startswith("..") and path in tree:
            return path
    return None


def _config_globs(tree, blob, notes):
    """{include, reference, exclude: [compiled glob]} from the committed
    `instructions` config section; all empty (with a note) when it is unusable."""
    lists = {"include": [], "reference": [], "exclude": []}
    if CONFIG_PATH not in tree:
        return lists
    try:
        raw = blob(tree[CONFIG_PATH][1]).data
        if raw is None:
            raise ValueError(f"file over {BLOB_CAP} bytes")
        section = json.loads(raw).get("instructions", {})
        if not isinstance(section, dict):
            raise ValueError("section is not an object")
        for name in lists:
            globs = section.get(name, [])
            if not isinstance(globs, list) or not all(isinstance(g, str) for g in globs):
                raise ValueError(f"{name} is not a list of strings")
            for g in globs:
                if len(g) > GLOB_CAP:
                    notes.append(f"instructions config glob skipped: over {GLOB_CAP} characters: {g[:40]}...")
            lists[name] = [glob_matcher(g) for g in globs if len(g) <= GLOB_CAP]
    except (ValueError, AttributeError) as err:
        notes.append(f"instructions config ignored: {err}")
        return {name: [] for name in lists}
    return lists


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
    links = [oid for mode, oid in tree.values() if mode == "120000"]
    cache.update(read_blobs(repo, [tree[p][1] for p in candidates] + links))

    def warm(paths, hold=None):
        """Read the blobs of `paths` (and their symlink targets) in one batch;
        the bytes held, at most `hold`."""
        reals = (_resolve_symlink(p, tree, blob) for p in paths)
        got = read_blobs(repo, [tree[r][1] for r in reals if r and tree[r][1] not in cache], hold)
        cache.update(got)
        return sum(len(b.data) for b in got.values() if b.data is not None)

    def read(path):
        """(real path, Blob, text or None) of a tracked path; None for a
        symlink that leaves the repository or reaches nothing. The text is None
        for a blob that is not UTF-8 or is over the read cap (each noted)."""
        real = _resolve_symlink(path, tree, blob)
        if real is None:
            notes.append(f"symlink skipped: {path}")
            return None
        got = blob(tree[real][1])
        if got.data is None:
            cap = BLOB_CAP if got.size > BLOB_CAP else CONFIG_BUDGET
            notes.append(f"over {cap} bytes, not parsed: {path}")
            return real, got, None
        try:
            return real, got, got.data.decode("utf-8")
        except UnicodeDecodeError:
            notes.append(f"not UTF-8: {path}")
            return real, got, None

    config = _config_globs(tree, blob, notes)

    def listed(name, path):
        return any(regex.match(path) for regex in config[name])

    info = {}
    for path in candidates:
        if listed("exclude", path):
            continue
        got = read(path)
        if got is None:
            continue
        real, content, text = got
        kind, where, row = classify_path(path)
        fields = {}
        if row == "governance":
            scope, source, body = tuple(where), "governance", text or ""
        else:
            fields, body = front_matter(text) if text is not None else ({}, "")
            if fields is None:
                notes.append(f"front matter unparseable: {path}")
                fields = {}
            mapped = _mapped(row, fields)
            kind, globs = mapped if mapped else (kind, [])
            kind, scope = _kind_scope(kind, where, globs)
            scope, source = tuple(scope), "catalogue"
        info[path] = {
            "kind": kind, "scope": scope, "source": source, "real": real, "blob": content,
            "body": body, "title": "" if text is None else _title(body, path, fields),
        }

    def merge(path, kind, scope, source):
        """Add or strengthen `path` (FR-012); True when the index changed."""
        if listed("exclude", path):
            return False
        if path in info:
            cur = info[path]
            if (KIND_ORDER[kind], SOURCE_ORDER[source]) >= (
                KIND_ORDER[cur["kind"]], SOURCE_ORDER[cur["source"]]
            ):
                return False
            cur.update(kind=kind, scope=tuple(scope), source=source)
            return True
        got = read(path)
        if got is None:
            return False
        real, content, text = got
        fields, body = front_matter(text) if text is not None else ({}, "")
        info[path] = {
            "kind": kind, "scope": tuple(scope), "source": source, "real": real, "blob": content,
            "body": body if fields is not None else text,
            "title": "" if text is None else _title(body if fields is not None else text, path, fields),
        }
        return True

    budget = CONFIG_BUDGET
    for name, kind in (("include", "always"), ("reference", "reference")):
        matched = [p for p in sorted(tree) if listed(name, p) and p not in info]
        budget -= warm(matched, budget)
        for path in sorted(tree):
            if listed(name, path):
                merge(path, kind, ("/",), "config")

    depth = {p: 0 for p, e in info.items() if e["kind"] != "reference"}
    queue = sorted(depth)
    while queue:
        following, queue = queue, []
        warm(
            t for p in following for tok in _imports(info[p]["body"])
            if (t := _locate(tok, p, tree)) is not None and t not in info
        )
        for path in following:
            entry = info[path]
            for token in _imports(entry["body"]):
                target = _locate(token, path, tree)
                if target is None:
                    notes.append(f"import target not tracked: {path} -> {token}")
                    continue
                if depth[path] + 1 > IMPORT_HOPS:
                    notes.append(f"import chain stopped at depth {IMPORT_HOPS}: {path} -> {target}")
                    continue
                changed = merge(target, entry["kind"], entry["scope"], "import")
                if target in depth and depth[target] <= depth[path] + 1:
                    if changed:
                        queue.append(target)
                elif target in info:
                    depth[target] = depth[path] + 1
                    queue.append(target)
    linking = sorted(p for p, e in info.items() if e["kind"] != "reference")
    warm(
        t for p in linking for tok in _links(info[p]["body"])
        if (t := _locate(tok, p, tree, relative_only=True)) is not None and t not in info
    )
    for path in linking:
        for token in _links(info[path]["body"]):
            target = _locate(token, path, tree, relative_only=True)
            if target is not None:
                merge(target, "reference", ("/",), "link")

    groups = {}
    for path, e in info.items():
        key = (e["blob"].digest, e["kind"], e["scope"], e["source"])
        groups.setdefault(key, []).append((path, e))

    entries = []
    for (digest, kind, scope, source), members in groups.items():
        # the regular file the content lives in, even when only a link reached it
        primary = min(members, key=lambda m: (m[1]["real"], m[0]))
        entries.append(
            {
                "path": primary[1]["real"],
                "kind": kind,
                "scope": list(scope),
                "size": primary[1]["blob"].size,
                "hash": digest,
                "title": primary[1]["title"],
                "aliases": sorted({m[0] for m in members} - {primary[1]["real"]}),
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
