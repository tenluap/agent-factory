"""Stack detection for the factory CLI (spec 017).

Read-only marker-file detection: languages, frameworks, package managers and
proposed build/test commands, from stdlib parsing alone — no subprocess, no
network, no side effects. The orchestrator runs `factory detect` at preflight
(every new run and every resume) and records the returned profile in run state
and `profile.md`.

The profile is orientation, never contract: an unknown or mixed repo is a
disclosure, not a halt (ADR-0004).
"""

import json
import re
import xml.etree.ElementTree as ElementTree
from datetime import datetime, timezone
from pathlib import Path

# directories never entered during the subdirectory scan
IGNORED_DIRS = {
    "node_modules",
    "dist",
    "build",
    "bin",
    "obj",
    ".venv",
    "venv",
    "target",
    ".git",
    ".idea",
    ".vs",
    ".vscode",
    "__pycache__",
    ".next",
    ".nuxt",
    "vendor",
    "site-packages",
    "Pods",
    "DerivedData",
}

MAX_DEPTH = 1  # root plus one subdirectory level (spec 017)

# one entry per stack; adding a stack is one dict/table entry
PYTHON_FRAMEWORKS = ("django", "fastapi", "flask")
NODE_FRAMEWORKS = (
    "react",
    "next",
    "vue",
    "svelte",
    "astro",
    "angular",
    "nuxt",
    "solid-js",
    "preact",
    "express",
    "@nestjs/core",
)
UI_FRAMEWORKS = {
    "avalonia",
    "react",
    "next",
    "vue",
    "svelte",
    "astro",
    "angular",
    "nuxt",
    "solid-js",
    "preact",
    "flutter",
    "swiftui",
}
LOCKFILE_MANAGERS = {
    "package-lock.json": "npm",
    "pnpm-lock.yaml": "pnpm",
    "yarn.lock": "yarn",
    "bun.lockb": "bun",
    "bun.lock": "bun",
}
PYPROJECT_LOCK_MANAGERS = {
    "poetry.lock": "poetry",
    "uv.lock": "uv",
}


# --------------------------------------------------------------------------
# parsing helpers (stdlib only)
# --------------------------------------------------------------------------


def _read_json(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def _toml_value(text):
    """Best-effort scalar extraction from a toml value expression."""
    value = text.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return None


def _toml_sections(path, wanted):
    """{section: {key: raw value string}} for wanted section names.

    Minimal toml reader: sections, string/bool scalars, single-line string
    arrays. Enough for go.mod's `go` directive and pyproject's project table.
    """
    result = {}
    try:
        lines = path.read_text().splitlines()
    except OSError:
        return result
    current = None
    for line in lines:
        line = line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if line.lstrip().startswith("["):
            match = re.fullmatch(r"\s*\[\s*([^\]]+?)\s*\]", line)
            current = None
            if match:
                name = match.group(1).strip().strip('"').strip("'")
                leaf = name.split(".")[-1]
                if leaf in wanted:
                    current = leaf
            continue
        if current:
            key, sep, value = line.partition("=")
            if sep:
                result.setdefault(current, {})[key.strip().strip('"').strip("'")] = (
                    value.strip()
                )
    return result


def _go_directive(path):
    """go.mod's bare `go 1.x` version line (a keyless directive, not a table)."""
    try:
        lines = path.read_text().splitlines()
    except OSError:
        return None
    for line in lines:
        stripped = line.split("#", 1)[0].strip()
        if stripped.startswith("go "):
            version = stripped[3:].strip()
            return version or None
    return None
    return result


def _read_csproj(path, central_versions=None):
    """(target framework moniker, {package: version}) from one SDK-style project."""
    try:
        root = ElementTree.parse(path).getroot()
    except (OSError, ElementTree.ParseError):
        return None, {}
    tfm = None
    packages = {}
    for element in root.iter():
        tag = element.tag.rsplit("}", 1)[-1]
        if tag == "TargetFramework":
            tfm = (element.text or "").strip() or tfm
        elif tag == "TargetFrameworks" and not tfm:
            monikers = (element.text or "").strip()
            tfm = monikers.split(";")[0] if monikers else tfm
        elif tag in ("PackageReference",):
            name = element.get("Include") or element.get("Update")
            if name:
                packages[name.lower()] = element.get("Version") or central_versions.get(
                    name.lower(), ""
                )
    return tfm, packages


def _read_central_versions(root):
    """{package: version} from Directory.Packages.props, when present."""
    props = root / "Directory.Packages.props"
    versions = {}
    if not props.is_file():
        return versions
    try:
        tree = ElementTree.parse(props)
    except (OSError, ElementTree.ParseError):
        return versions
    for element in tree.getroot().iter():
        if element.tag.rsplit("}", 1)[-1] == "PackageVersion":
            name = element.get("Include") or element.get("Update")
            if name:
                versions[name.lower()] = (element.get("Version") or "").strip()
    return versions


def _requirements_names(path):
    try:
        lines = path.read_text().splitlines()
    except OSError:
        return []
    names = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith(("-", "#")):
            continue
        names.append(re.split(r"[<>=!~\[\s;]", stripped, 1)[0].lower())
    return names


def _pyproject_names(path):
    """Dependency names from pyproject's [project] table (strings in arrays)."""
    sections = _toml_sections(path, ("project",))
    deps_raw = sections.get("project", {}).get("dependencies", "")
    names = []
    for item in re.findall(r'"([^"]+)"|\'([^\']+)\'', deps_raw):
        spec = item[0] or item[1]
        names.append(re.split(r"[<>=!~\[\s;]", spec, 1)[0].lower())
    return names


# --------------------------------------------------------------------------
# marker classification
# --------------------------------------------------------------------------


def marker_kind(path):
    """None, "workspace", "lock" or "project" for a filesystem entry."""
    if not path.is_file():
        return None
    name = path.name
    if name in (
        "pnpm-workspace.yaml",
        "turbo.json",
        "nx.json",
        "lerna.json",
    ) or name.endswith((".sln", ".slnx")):
        return "workspace"
    if (
        name in LOCKFILE_MANAGERS
        or name in PYPROJECT_LOCK_MANAGERS
        or name
        in (
            "package-lock.json",
            "poetry.lock",
            "uv.lock",
            "Gemfile.lock",
            "Pipfile.lock",
            "Cargo.lock",
            "go.sum",
            "pubspec.lock",
            "packages.lock.json",
        )
    ):
        return "lock"
    if name in (
        "package.json",
        "pyproject.toml",
        "requirements.txt",
        "Pipfile",
        "Cargo.toml",
        "go.mod",
        "Gemfile",
        "pubspec.yaml",
        "Package.swift",
        "build.gradle",
        "build.gradle.kts",
        "settings.gradle",
        "settings.gradle.kts",
        "pom.xml",
        "mix.exs",
        "composer.json",
    ) or name.endswith((".csproj", ".fsproj", ".vbproj")):
        return "project"
    return None


def discover_projects(root):
    """Project/workspace/lock markers from the root to two subdirectory levels,
    with the ignore list. Bounded: at most three fixed levels, never a tree
    walk. Covers `src/App/App.csproj` as well as `api/pyproject.toml`."""
    found = []
    try:
        root_entries = sorted(root.iterdir())
    except OSError:
        return found

    def collect(entries):
        pairs = []
        for entry in entries:
            kind = marker_kind(entry)
            if kind:
                pairs.append((entry.relative_to(root).as_posix(), kind))
        return pairs

    found.extend(collect(root_entries))

    level1 = [
        child
        for child in root_entries
        if child.is_dir()
        and not child.name.startswith(".")
        and child.name not in IGNORED_DIRS
    ]
    for child in level1:
        try:
            entries = sorted(child.iterdir())
        except OSError:
            continue
        found.extend(collect(entries))
        for grandchild in entries:
            if (
                not grandchild.is_dir()
                or grandchild.name.startswith(".")
                or grandchild.name in IGNORED_DIRS
            ):
                continue
            try:
                found.extend(collect(sorted(grandchild.iterdir())))
            except OSError:
                continue
    return found


# --------------------------------------------------------------------------
# detection
# --------------------------------------------------------------------------


def detect(root):
    """Profile dict for the repo at `root`; never raises on repo content."""
    root = Path(root)
    markers = discover_projects(root)
    central_versions = _read_central_versions(root)

    languages = []
    frameworks = []
    managers = {}
    projects = []
    ui = False
    unknown_markers = []
    workspace_manifests = [rel for rel, kind in markers if kind == "workspace"]

    def add_language(name, version, evidence):
        for entry in languages:
            if entry["name"] == name:
                if version and not entry["version"]:
                    entry["version"] = version
                if evidence not in entry["evidence"]:
                    entry["evidence"].append(evidence)
                return
        languages.append({"name": name, "version": version, "evidence": [evidence]})

    def add_framework(name, version, evidence):
        for entry in frameworks:
            if entry["name"] == name:
                if version and not entry["version"]:
                    entry["version"] = version
                if evidence not in entry["evidence"]:
                    entry["evidence"].append(evidence)
                return
        frameworks.append(
            {"name": name, "version": version or None, "evidence": [evidence]}
        )
        if name in UI_FRAMEWORKS:
            nonlocal ui
            ui = True

    def add_manager(name, evidence, lockfile=None):
        entry = managers.setdefault(
            name, {"name": name, "primary": False, "evidence": [], "lockfiles": []}
        )
        if evidence not in entry["evidence"]:
            entry["evidence"].append(evidence)
        if lockfile and lockfile not in entry["lockfiles"]:
            entry["lockfiles"].append(lockfile)

    for rel, kind in markers:
        path = root / rel
        parent = path.parent
        name = path.name

        if kind == "workspace":
            continue  # disclosed via the monorepo flag, not as a project

        if kind == "lock":
            if name in LOCKFILE_MANAGERS:
                add_manager(LOCKFILE_MANAGERS[name], evidence_dir(rel), rel)
            elif name in PYPROJECT_LOCK_MANAGERS:
                add_manager(PYPROJECT_LOCK_MANAGERS[name], evidence_dir(rel), rel)
            continue

        # kind == "project"
        projects.append(rel)

        if name.endswith((".csproj", ".fsproj", ".vbproj")):
            tfm, packages = _read_csproj(path, central_versions)
            add_language("csharp", tfm, rel)
            for package, version in packages.items():
                if package == "avalonia":
                    add_framework("avalonia", version, rel)
            add_manager(
                "dotnet",
                evidence_dir(rel),
                str(parent / "packages.lock.json")
                if (parent / "packages.lock.json").is_file()
                else None,
            )

        elif name == "package.json":
            loaded = _read_json(path)
            if not isinstance(loaded, dict):
                unknown_markers.append(rel)
                continue
            deps = {}
            for section_name in ("dependencies", "devDependencies", "peerDependencies"):
                section = loaded.get(section_name)
                if isinstance(section, dict):
                    deps.update({str(k).lower(): str(v) for k, v in section.items()})
            is_ts = (parent / "tsconfig.json").is_file()
            add_language("typescript" if is_ts else "javascript", None, rel)
            for fw in NODE_FRAMEWORKS:
                if fw in deps:
                    add_framework(fw, deps[fw], rel)
            for lockfile, manager in LOCKFILE_MANAGERS.items():
                if (parent / lockfile).is_file():
                    add_manager(
                        manager, evidence_dir(rel), f"{rel_lock(rel, lockfile)}"
                    )
                    break
            else:
                add_manager("npm", evidence_dir(rel))

        elif name in ("pyproject.toml", "requirements.txt", "Pipfile"):
            names = (
                _pyproject_names(path)
                if name == "pyproject.toml"
                else _requirements_names(path)
            )
            add_language("python", None, rel)
            for fw in PYTHON_FRAMEWORKS:
                if fw in names:
                    add_framework(fw, None, rel)
            for lockfile, manager in PYPROJECT_LOCK_MANAGERS.items():
                if (root / lockfile).is_file() or (parent / lockfile).is_file():
                    add_manager(
                        manager,
                        evidence_dir(rel),
                        (parent / lockfile).as_posix(),
                    )
            if not any(m in managers for m in ("poetry", "uv")):
                add_manager("pip", evidence_dir(rel))

        elif name == "go.mod":
            add_language("go", _go_directive(path), rel)
            add_manager("gomod", evidence_dir(rel))

        elif name == "Cargo.toml":
            add_language("rust", None, rel)
            add_manager(
                "cargo",
                evidence_dir(rel),
                (parent / "Cargo.lock").as_posix()
                if (parent / "Cargo.lock").is_file()
                else None,
            )

        elif name == "Gemfile":
            add_language("ruby", None, rel)
            add_manager(
                "bundler",
                evidence_dir(rel),
                (parent / "Gemfile.lock").as_posix()
                if (parent / "Gemfile.lock").is_file()
                else None,
            )

        elif name == "pubspec.yaml":
            add_language("dart", None, rel)
            add_framework("flutter", None, rel)
            add_manager(
                "pub",
                evidence_dir(rel),
                (parent / "pubspec.lock").as_posix()
                if (parent / "pubspec.lock").is_file()
                else None,
            )

        elif name == "Package.swift":
            add_language("swift", None, rel)
            add_manager("spm", evidence_dir(rel))

        elif name in (
            "build.gradle",
            "build.gradle.kts",
            "settings.gradle",
            "settings.gradle.kts",
            "pom.xml",
        ):
            add_language("java", None, rel)
            add_manager("gradle" if "gradle" in name else "maven", evidence_dir(rel))

        elif name in ("mix.exs",):
            add_language("elixir", None, rel)
            add_manager("mix", evidence_dir(rel))

        elif name in ("composer.json",):
            add_language("php", None, rel)
            add_manager("composer", evidence_dir(rel))

        else:
            unknown_markers.append(rel)

    monorepo = bool(workspace_manifests) or _mixed_root_managers(managers)
    primary = _pick_primary(managers)
    for entry in managers.values():
        entry["primary"] = entry["name"] == primary

    profile = {
        "languages": languages,
        "frameworks": frameworks,
        "package_managers": sorted(
            managers.values(), key=lambda m: (not m["primary"], m["name"])
        ),
        "ui": ui,
        "monorepo": monorepo,
        "projects": projects,
        "commands": _detect_commands(managers, languages),
        "unknown_markers": unknown_markers,
        "notes": _notes(managers, primary),
        "detected_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "detected_by": "factory detect 017",
    }
    return profile


def evidence_dir(rel):
    """Repo-relative directory of a project marker ("." at the root)."""
    return rel.rsplit("/", 1)[0] if "/" in rel else "."


def rel_lock(rel, lockfile):
    """Repo-relative path of a lockfile beside the project marker `rel`."""
    directory = evidence_dir(rel)
    return f"{directory}/{lockfile}" if directory != "." else lockfile


def _mixed_root_managers(managers):
    """Two or more managers with root-level evidence — a mixed stack."""
    root_level = [
        name
        for name, entry in managers.items()
        if any("/" not in evidence for evidence in entry["evidence"])
    ]
    return len(root_level) > 1


def _pick_primary(managers):
    """Root-level evidence wins; ties and absences break toward most evidence,
    then alphabetical. One primary or None."""
    if not managers:
        return None

    def root_count(entry):
        return sum(1 for e in entry["evidence"] if "/" not in e)

    with_root = [name for name, entry in managers.items() if root_count(entry) > 0]
    pool = with_root or list(managers)
    return sorted(pool, key=lambda name: (-root_count(managers[name]), name))[0]


def _notes(managers, primary):
    notes = []
    root_level = [
        name
        for name, entry in managers.items()
        if any("/" not in e for e in entry["evidence"])
    ]
    if len(root_level) > 1:
        notes.append(
            "mixed stack: " + ", ".join(sorted(root_level)) + f"; primary is {primary}"
        )
    return notes


def _detect_commands(managers, languages):
    """Proposed build/test commands for the primary manager (source: detected)."""
    names = {lang["name"] for lang in languages}
    commands = {}
    if "dotnet" in managers:
        commands["build"] = {
            "value": "dotnet build",
            "source": "detected",
            "manager": "dotnet",
        }
        commands["test"] = {
            "value": "dotnet test",
            "source": "detected",
            "manager": "dotnet",
        }
        return commands
    if "node" in names or "typescript" in names:
        runner = _first_of(managers, ("pnpm", "yarn", "bun", "npm")) or "npm"
        commands["build"] = {
            "value": f"{runner} run build",
            "source": "detected",
            "manager": runner,
        }
        commands["test"] = {
            "value": f"{runner} run test",
            "source": "detected",
            "manager": runner,
        }
        return commands
    if "python" in names:
        commands["test"] = {
            "value": "python -m pytest",
            "source": "detected",
            "manager": "pip",
        }
        return commands
    if "go" in names:
        commands["build"] = {
            "value": "go build ./...",
            "source": "detected",
            "manager": "gomod",
        }
        commands["test"] = {
            "value": "go test ./...",
            "source": "detected",
            "manager": "gomod",
        }
        return commands
    if "rust" in names:
        commands["build"] = {
            "value": "cargo build",
            "source": "detected",
            "manager": "cargo",
        }
        commands["test"] = {
            "value": "cargo test",
            "source": "detected",
            "manager": "cargo",
        }
        return commands
    if "java" in names:
        runner = "gradle" if "gradle" in managers else "maven"
        build = f"{runner} build" if runner == "gradle" else "mvn package"
        test = f"{runner} test" if runner == "gradle" else "mvn test"
        commands["build"] = {"value": build, "source": "detected", "manager": runner}
        commands["test"] = {"value": test, "source": "detected", "manager": runner}
        return commands
    return commands


def _first_of(managers, order):
    for name in order:
        if name in managers:
            return name
    return None


# --------------------------------------------------------------------------
# validation + rendering
# --------------------------------------------------------------------------


def validate_profile(profile):
    """Every violation as {"location", "reason"}; empty list means valid.

    Light validation: presence and types of the known fields. Unknown extra
    fields pass through untouched (same pattern as `design` context).
    """
    problems = []

    def bad(location, reason):
        problems.append({"location": location, "reason": reason})

    if not isinstance(profile, dict):
        return [{"location": "profile", "reason": "profile is not a JSON object"}]
    for field in (
        "languages",
        "frameworks",
        "package_managers",
        "projects",
        "unknown_markers",
    ):
        value = profile.get(field)
        if not isinstance(value, list):
            bad(field, "missing or not a list")
    for field in ("ui", "monorepo"):
        if not isinstance(profile.get(field), bool):
            bad(field, "missing or not a boolean")
    if not isinstance(profile.get("commands"), dict):
        bad("commands", "missing or not an object")
    if not isinstance(profile.get("notes"), list):
        bad("notes", "missing or not a list")
    if not profile.get("detected_at"):
        bad("detected_at", "missing")
    if not isinstance(profile.get("languages", []), list):
        pass
    for i, lang in enumerate(profile.get("languages", []) or []):
        if not isinstance(lang, dict) or not lang.get("name"):
            bad(f"languages[{i}]", "missing name")
    for i, fw in enumerate(profile.get("frameworks", []) or []):
        if not isinstance(fw, dict) or not fw.get("name"):
            bad(f"frameworks[{i}]", "missing name")
    for i, manager in enumerate(profile.get("package_managers", []) or []):
        if not isinstance(manager, dict) or not manager.get("name"):
            bad(f"package_managers[{i}]", "missing name")
        elif not isinstance(manager.get("evidence"), list):
            bad(f"package_managers[{i}].evidence", "missing or not a list")
    primaries = [
        m
        for m in profile.get("package_managers", []) or []
        if isinstance(m, dict) and m.get("primary")
    ]
    if len(primaries) > 1:
        bad("package_managers", "more than one primary")
    return problems


def render_markdown(profile):
    """The human-readable profile.md body."""
    lines = ["# Stack profile", ""]

    def versions(entries):
        parts = []
        for entry in entries:
            label = entry["name"]
            if entry.get("version"):
                label += f" {entry['version']}"
            parts.append(label)
        return ", ".join(parts) or "unknown"

    lines.append(f"**Languages:** {versions(profile.get('languages', []))}")
    lines.append("")
    lines.append(f"**Frameworks:** {versions(profile.get('frameworks', []))}")
    lines.append("")

    managers = profile.get("package_managers", [])
    if managers:
        parts = []
        for manager in managers:
            label = manager["name"] + (" (primary)" if manager.get("primary") else "")
            if manager.get("lockfiles"):
                label += f" — {', '.join(manager['lockfiles'])}"
            parts.append(label)
        lines.append(f"**Package managers:** " + "; ".join(parts))
        lines.append("")

    lines.append(f"**UI:** {'yes' if profile.get('ui') else 'no'}")
    lines.append("")
    lines.append(f"**Monorepo:** {'yes' if profile.get('monorepo') else 'no'}")
    lines.append("")

    projects = profile.get("projects", [])
    if projects:
        lines.append("**Projects:**")
        lines.append("")
        for project in projects:
            lines.append(f"- `{project}`")
        lines.append("")

    commands = profile.get("commands", {})
    if commands:
        lines.append("**Commands (proposed):**")
        lines.append("")
        lines.append("| purpose | command | source | manager |")
        lines.append("|---|---|---|---|")
        for purpose in sorted(commands):
            entry = commands[purpose]
            lines.append(
                f"| {purpose} | `{entry.get('value', '')}` | {entry.get('source', '')} "
                f"| {entry.get('manager', '')} |"
            )
        lines.append("")

    if profile.get("unknown_markers"):
        lines.append("**Unrecognized markers:**")
        lines.append("")
        for marker in profile["unknown_markers"]:
            lines.append(f"- `{marker}`")
        lines.append("")

    for note in profile.get("notes", []):
        lines.append(f"> {note}")
    if profile.get("notes"):
        lines.append("")

    lines.append(
        f"_Detected {profile.get('detected_at', '')} by "
        f"{profile.get('detected_by', 'factory detect')}._"
    )
    lines.append("")
    return "\n".join(lines)
