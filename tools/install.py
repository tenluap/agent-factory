#!/usr/bin/env python3
"""Install the factory for a harness (ADR 0019; was install.sh).

Renders the factory into ${FACTORY_HOME:-~/.factory}/dist/<harness> and
symlinks the harness's skill, agents and skill library from that per-user
copy. The shell entry points (install.sh, install.ps1, install.cmd) only find
a Python 3 interpreter and run this file; every rule lives here, so POSIX and
Windows installs behave the same.

Usage: install.py [--harness <name>|all] [--uninstall] [--add-skill <path>]
Default harness: claude-code. Re-run after pulling.

Environment read here (set by the entry points):
  FACTORY_INSTALL_ENTRY  the command users re-run, named in messages
  FACTORY_PYTHON_CMD     the interpreter command the entry point used; it is
                         rendered into the per-user skill in place of python3
"""

import json
import os
import platform
import re
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render  # noqa: E402  (tools/render.py, next to this file)

# abspath, not resolve: link targets keep the checkout path as given (`pwd`)
SRC = Path(os.path.abspath(__file__)).parent.parent
LIB = SRC / ".agents" / "skills"
LOCK = SRC / "skills-lock.json"
WINDOWS = os.name == "nt"


class Exit(Exception):
    """Stop the install with an exit code; the message is already printed."""

    def __init__(self, code):
        super().__init__(code)
        self.code = code


def out(text):
    print(text, flush=True)


def err(text):
    print(text, file=sys.stderr, flush=True)


def entry():
    default = ".\\install.cmd" if WINDOWS else "./install.sh"
    return os.environ.get("FACTORY_INSTALL_ENTRY") or default


def python_command():
    """The bare interpreter command to render into the skill (ADR 0019)."""
    given = os.environ.get("FACTORY_PYTHON_CMD")
    if given:
        return given
    if not WINDOWS:
        return "python3"
    return "py -3" if shutil.which("py") else "python"


# --- link primitives -------------------------------------------------------


def _norm(path):
    text = str(path)
    if text.startswith("\\\\?\\"):  # Win32 long-path prefix some tools store
        text = text[4:]
    return os.path.normcase(os.path.normpath(text))


def target_of(path):
    """The symlink's stored target, without any \\\\?\\ prefix."""
    text = os.readlink(path)
    return text[4:] if text.startswith("\\\\?\\") else text


def same(a, b):
    return _norm(a) == _norm(b)


def within(path, root):
    return _norm(path).startswith(_norm(root) + os.sep)


def is_link(path):
    return os.path.islink(path)


def exists(path):
    """True when the path resolves (a dangling link does not)."""
    return os.path.exists(path)


def remove_link(path):
    try:
        os.unlink(path)
    except (IsADirectoryError, PermissionError):
        os.rmdir(path)  # a Windows directory symlink


def make_link(source, link):
    """`ln -sfn source link`: replace an existing link, never a real file."""
    if is_link(link):
        remove_link(link)
    os.symlink(str(source), str(link), target_is_directory=os.path.isdir(source))


def entries(directory):
    """`dir/*`: the non-hidden entries, sorted (bash globs skip dotfiles)."""
    try:
        names = sorted(os.listdir(directory))
    except OSError:
        return []
    return [Path(directory) / name for name in names if not name.startswith(".")]


def check_symlinks():
    """Fail before changing anything when this host cannot create symlinks."""
    probe = Path(tempfile.mkdtemp(prefix="factory-symlink-"))
    try:
        (probe / "target").mkdir()
        os.symlink(probe / "target", probe / "link", target_is_directory=True)
    except OSError as error:
        err(f"error: cannot create symbolic links: {error}")
        if WINDOWS:
            err(
                "       turn on Developer Mode (Settings > System > For developers >"
                " Developer Mode), or run from an elevated shell, then re-run: "
                + entry()
            )
        raise Exit(2)
    finally:
        shutil.rmtree(probe, ignore_errors=True)


# --- frontmatter -----------------------------------------------------------


def frontmatter_name(skill_md):
    text = Path(skill_md).read_text(encoding="utf-8", errors="replace")
    match = re.match(r"\A---\s*\n(.*?)\n---", text, re.S)
    name = re.search(r"^name:\s*(.*?)\s*$", match.group(1), re.M) if match else None
    return name.group(1).strip().strip("'\"") if name else ""


class Installer:
    def __init__(self, harness, uninstall, add_path):
        self.harness = harness
        self.uninstall = uninstall
        self.add_path = add_path
        self.home = Path(render.expand(os.environ.get("FACTORY_HOME") or "~/.factory"))
        self.skills = self.home / "skills"
        self.mirror_done = False
        self.library = []

    # The vendored library is `.agents/skills/`, managed by the `skills` CLI
    # (ADR 0018). A folder belongs to it only when its SKILL.md frontmatter
    # name has an entry in `skills-lock.json`; anything else there (for
    # example the speckit skills `specify init` writes) is never linked.
    def library_entries(self):
        """(folder name, owned) for every library folder with a SKILL.md."""
        try:
            owned = set(json.loads(LOCK.read_text(encoding="utf-8"))["skills"])
        except (OSError, ValueError, KeyError, TypeError):
            owned = set()
        found = []
        for folder in sorted(LIB.iterdir()) if LIB.is_dir() else []:
            skill = folder / "SKILL.md"
            if folder.name.startswith(".") or not skill.is_file():
                continue
            found.append((folder.name, frontmatter_name(skill) in owned))
        return found

    def owned_entry(self, name):
        return (name, True) in self.library

    # The per-user layer doubles as the browsing mirror of the vendored
    # library. Mirror links point into this checkout's library (or, before
    # ADR 0018, its `skills/`) and are managed only by the mirror functions;
    # the per-user skill scan never treats them as per-user skills.
    def mirror_entry(self, path):
        if not is_link(path):
            return False
        target = target_of(path)
        return within(target, LIB) or within(target, SRC / "skills")

    def user_skill(self, name):
        """A real per-user skill: a folder with a SKILL.md, not a mirror link."""
        folder = self.skills / name
        return (folder / "SKILL.md").is_file() and not self.mirror_entry(folder)

    def mirror_link(self, source, link):
        if is_link(link) and not self.mirror_entry(link):
            out(
                f"skip: {link} exists and is not a mirror link; to adopt it: "
                f"{entry()} --add-skill {link}, remove the original, re-run"
            )
            return
        if exists(link) and not is_link(link):
            return  # a real per-user skill wins
        if not is_link(link) or not same(target_of(link), source):
            make_link(source, link)

    def mirror_library(self):
        if not self.skills.is_dir():
            return
        self.library = self.library_entries()
        for path in entries(self.skills):
            if not is_link(path):
                continue
            if not exists(path):
                remove_link(path)
                out(f"pruned: {path} (stale link)")
            elif self.mirror_entry(path):
                target = target_of(path)
                if not within(target, LIB) or not self.owned_entry(os.path.basename(target)):
                    remove_link(path)
                    out(f"pruned: {path} (stale link)")
        for name, owned in self.library:
            if owned:
                self.mirror_link(LIB / name, self.skills / name)
        self.mirror_done = True

    def add_skill(self, path):
        if "://" in path or not os.path.isdir(path):
            err(f"error: {path}: not a local directory")
            raise Exit(2)
        name = os.path.basename(path.rstrip("/\\"))
        if name == "factory":
            err("reserved: factory")
            raise Exit(2)
        skill_md = Path(path) / "SKILL.md"
        if not skill_md.is_file():
            err(f"error: {path}: no SKILL.md")
            raise Exit(2)
        try:
            text = skill_md.read_text(encoding="utf-8")
            match = re.match(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", text, re.S)
            found = re.search(r"^name:\s*(.*?)\s*$", match.group(1), re.M) if match else None
            if not found or not found.group(1).strip(" '\""):
                problem = "no frontmatter"
            else:
                value = found.group(1).strip().strip("'\"")
                problem = (
                    None
                    if value == name
                    else f"name '{value}' does not match folder '{name}'"
                )
        except (OSError, UnicodeError) as error:
            problem = str(error)
        if problem:
            err(f"error: {path}: {problem}")
            raise Exit(2)
        dest = self.skills / name
        if exists(dest) or is_link(dest):
            err(f"exists: {dest}")
            raise Exit(2)
        self.skills.mkdir(parents=True, exist_ok=True)
        temp = self.skills / f".{name}.tmp.{os.getpid()}"
        try:
            # follows links (cp -RH did for the given path) so the per-user
            # copy is self-contained; a dangling link fails the copy
            shutil.copytree(path, temp, symlinks=False)
            os.rename(temp, dest)
        except (OSError, shutil.Error):
            shutil.rmtree(temp, ignore_errors=True)
            err(f"error: {path}: copy failed")
            raise Exit(1)
        out(f"added: {dest}")

    def link(self, source, link):
        if exists(link) and not is_link(link):
            err(f"skip: {link} exists and is not a symlink")
            return
        make_link(source, link)
        out(f"linked: {link}")

    def verify_link(self, source, link):
        if not is_link(link) or not same(target_of(link), source):
            err(f"error: factory link not installed at {link}")
            err(
                "       resolve any existing file at that path, then rerun: "
                f"{entry()} --harness {self.harness}"
            )
            raise Exit(1)

    def unlink_ours(self, link):
        if is_link(link) and within(target_of(link), self.home / "dist"):
            remove_link(link)
            out(f"removed: {link}")

    def library_link(self, path):
        if not is_link(path):
            return False
        target = target_of(path)
        return any(
            within(target, root)
            for root in (LIB, SRC / "skills", self.home / "dist", self.skills)
        )

    def link_skill(self, source, link):
        if (exists(link) or is_link(link)) and not self.library_link(link):
            out(
                f"skip: {link} exists and is not a library link; to adopt it: "
                f"{entry()} --add-skill {link}, remove the original, re-run"
            )
            return
        if not is_link(link) or not same(target_of(link), source):
            make_link(source, link)
        out(f"linked: {link}")

    @staticmethod
    def skill_name(folder):
        """Link name for a rendered first-party skill: its frontmatter name."""
        try:
            return frontmatter_name(Path(folder) / "SKILL.md")
        except OSError:
            return ""

    def install_skills(self, root, dist):
        self.library = self.library_entries()
        root.mkdir(parents=True, exist_ok=True)
        for path in entries(root):
            if not is_link(path):
                continue
            target = target_of(path)
            if self.library_link(path) and not exists(path):
                remove_link(path)
                out(f"removed: {path}")
            elif within(target, SRC / "core" / "skills") or within(target, SRC / "skills"):
                # links from superseded layouts: first-party skills linked from
                # source (the rendered distribution replaced them, ADR 0012) and
                # the vendored library in `skills/` (`.agents/skills/`, ADR 0018)
                remove_link(path)
                out(f"removed: {path}")
            elif within(target, LIB) and not self.owned_entry(os.path.basename(target)):
                # the folder is still there but skills-lock.json no longer owns it
                remove_link(path)
                out(f"removed: {path}")
        # First-party skills link from the rendered distribution (ADR 0012),
        # ahead of the vendored and per-user layers; a per-user skill wins on
        # name collision, a vendored one is skipped.
        linked = set()
        for folder in entries(dist / "skills"):
            if not folder.is_dir():
                continue
            name = self.skill_name(folder)
            if not name:
                out(f"skip: {folder}: no frontmatter name")
                continue
            if self.user_skill(name):
                out(f"skip: {name}: per-user skill takes precedence")
                continue
            linked.add(name)
            self.link_skill(folder, root / name)
        # Vendored skills link under their folder name (the `skills` CLI
        # derives it from the frontmatter name); a per-user skill wins.
        for name, owned in self.library:
            if not owned:
                out(f"skip: {name}: not in skills-lock.json")
                continue
            folder = LIB / name
            if name == "factory":
                out(f"skip: {folder}: name reserved for the factory skill")
                continue
            if self.user_skill(name):
                continue
            if name in linked:
                out(f"skip: {folder}: the first-party skill {name} is already linked")
                continue
            self.link_skill(folder, root / name)
        for folder in entries(self.skills):
            # the browsing mirror lives here but points back at the library
            if self.mirror_entry(folder):
                continue
            if not (folder.is_dir() and (folder / "SKILL.md").is_file()):
                continue
            if folder.name == "factory":
                out(f"skip: {folder}: name reserved for the factory skill")
                continue
            self.link_skill(folder, root / folder.name)

    def unlink_skills(self, root):
        for path in entries(root):
            if self.library_link(path):
                remove_link(path)
                out(f"removed: {path}")

    def prune_mirror(self):
        """Uninstall leaves the per-user layer to the user: mirror links go
        only when their targets are gone from the checkout."""
        if not self.skills.is_dir():
            return
        for path in entries(self.skills):
            if self.mirror_entry(path) and not exists(path):
                remove_link(path)
                out(f"pruned: {path} (stale link)")

    # OpenCode loads every .js in its plugins directory. The design-to-code
    # trigger plugin links straight from repo source (no render step) and is
    # removed on uninstall only when the link still points here.
    @staticmethod
    def plugin_target(skills_root):
        return Path(skills_root).parent / "plugins" / "design-to-code-trigger.js"

    def install_plugin(self, skills_root):
        target = self.plugin_target(skills_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        self.link(SRC / "plugins" / "design-to-code-trigger.js", target)

    def unlink_plugin(self, skills_root):
        target = self.plugin_target(skills_root)
        if is_link(target) and within(target_of(target), SRC / "plugins"):
            remove_link(target)
            out(f"removed: {target}")

    # claude-code and codex share one UserPromptSubmit hook script. It is
    # copied into $FACTORY_HOME/bin and wired by hand: the installer never
    # edits settings.json or hooks.json, so it prints the snippet instead.
    def hook_script_target(self):
        return self.home / "bin" / "design-to-code-hook.mjs"

    def install_hook_script(self):
        target = self.hook_script_target()
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(SRC / "plugins" / "design-to-code-hook.mjs", target)
            target.chmod(target.stat().st_mode | 0o111)
        except OSError:
            err(f"error: hook script copy failed: {target}")
            raise Exit(1)
        out(f"installed: {target}")
        # forward slashes paste into JSON unescaped and run from Git Bash
        command = json.dumps(f'node "{target.as_posix()}"')
        block = "\n".join(
            [
                '    "UserPromptSubmit": [',
                "      {",
                '        "hooks": [',
                "          {",
                '            "type": "command",',
                f'            "command": {command},',
                '            "timeout": 5,',
                '            "statusMessage": "Checking UI intent..."',
                "          }",
                "        ]",
                "      }",
                "    ]",
            ]
        )
        out(
            "wire it manually (this installer never edits your harness config):\n\n"
            '  claude-code — add to "hooks" in ~/.claude/settings.json:\n\n'
            f"{block}\n\n"
            '  codex — add to "hooks" in ~/.codex/hooks.json:\n\n'
            f"{block}\n\n"
            "  codex also requires trusting the hook once: run /hooks in Codex and approve it."
        )
        if shutil.which("node") is None:
            out("note: the hook runs with Node.js, and node is not on PATH yet")

    def uninstall_hook_script(self):
        target = self.hook_script_target()
        if target.is_file():
            target.unlink()
            out(f"removed: {target}")
            out(
                "note: remove the matching UserPromptSubmit entry from "
                "~/.claude/settings.json or ~/.codex/hooks.json if you wired it"
            )

    def install_one(self, harness):
        out(f"== {harness}")
        dist = self.home / "dist" / harness
        render.render(harness, out=dist, python=python_command())
        adapter = render.load_adapter(harness)
        skill_dir = Path(render.expand(adapter["skill_dir"]))
        skills_root = Path(render.expand(adapter["skills_root"]))
        agent_dir = Path(render.expand(adapter["agent_dir"]))
        if self.uninstall:
            self.unlink_skills(skills_root)
            self.prune_mirror()
            self.unlink_ours(skill_dir)
            if harness == "opencode":
                self.unlink_plugin(skills_root)
            if harness in ("claude-code", "codex"):
                self.uninstall_hook_script()
            for agent in entries(dist / "agents"):
                self.unlink_ours(agent_dir / agent.name)
            shutil.rmtree(dist, ignore_errors=True)
            out(f"removed: {dist}")
            return
        skill_dir.parent.mkdir(parents=True, exist_ok=True)
        agent_dir.mkdir(parents=True, exist_ok=True)
        self.link(dist / "skill", skill_dir)
        self.verify_link(dist / "skill", skill_dir)
        for agent in entries(dist / "agents"):
            self.link(agent, agent_dir / agent.name)
            self.verify_link(agent, agent_dir / agent.name)
        self.install_skills(skills_root, dist)
        if harness == "opencode":
            self.install_plugin(skills_root)
            out(
                "ready: OpenCode factory skill, role agents and design-to-code trigger "
                "plugin linked; start a fresh OpenCode session to load them."
            )
        elif harness in ("claude-code", "codex"):
            self.install_hook_script()
        render.print_models(harness)

    def check_home(self):
        """A missing default home is created; an explicitly configured home
        must exist as a writable directory, before anything is rendered."""
        if exists(self.home) and not self.home.is_dir():
            err(f"error: not a directory: {self.home}")
            raise Exit(2)
        if not self.home.is_dir():
            if os.environ.get("FACTORY_HOME"):
                err(f"error: FACTORY_HOME does not exist: {self.home}")
                raise Exit(2)
            if not self.add_path:
                self.home.mkdir(parents=True, exist_ok=True)
        if self.home.is_dir() and not os.access(self.home, os.W_OK):
            err(f"error: not writable: {self.home}")
            raise Exit(2)

    def check_config(self):
        """A config.json or skills-lock.json that does not parse aborts the
        install before any render or link (FR-022)."""
        config = self.home / "config.json"
        if config.is_file():
            try:
                json.loads(config.read_text(encoding="utf-8"))
            except (OSError, ValueError) as error:
                err(f"error: {config} does not parse: {error}")
                raise Exit(2)
        if LOCK.is_file():
            try:
                data = json.loads(LOCK.read_text(encoding="utf-8"))
                assert isinstance(data.get("skills"), dict), 'no "skills" object'
            except Exception as error:  # noqa: BLE001  (any failure is a parse error)
                err(f"error: {LOCK} does not parse: {error}")
                raise Exit(2)

    def run(self):
        self.check_home()
        self.check_config()
        if WINDOWS:
            check_symlinks()
        if self.add_path:
            self.add_skill(self.add_path)
        harnesses = render.known() if self.harness == "all" else [self.harness]
        for harness in harnesses:
            self.install_one(harness)
        if self.uninstall:
            return
        # The browsing mirror is refreshed once per run, after the per-user
        # renders it may point at are in place.
        self.mirror_library()
        if not self.mirror_done:
            out(
                f"note: no browsing mirror: {self.skills} does not exist yet "
                "(use --add-skill to create it)"
            )
        pending = self.home / "pending"
        pending.mkdir(parents=True, exist_ok=True)
        # Pending runs from before the harness split lived under ~/.claude/factory/pending.
        old = Path(render.expand("~/.claude/factory/pending"))
        if old.is_dir() and any(old.iterdir()):
            for item in sorted(old.iterdir()):
                if not exists(pending / item.name):
                    shutil.move(str(item), str(pending / item.name))
            out(f"moved: pending runs from {old} to {pending}")


def parse(argv):
    harness, uninstall, add_path = "claude-code", False, None
    args = list(argv)
    while args:
        arg = args.pop(0)
        if arg == "--harness":
            if not args or not args[0]:
                err(f"usage: {entry()} [--harness <name>|all] [--uninstall]")
                err(
                    "error: --harness needs a value "
                    "(see adapters/, python3 tools/render.py --list)"
                )
                raise Exit(2)
            harness = args.pop(0)
        elif arg == "--uninstall":
            uninstall = True
        elif arg == "--add-skill":
            if not args or not args[0] or args[0].startswith("--"):
                err("usage: --add-skill <path>")
                raise Exit(2)
            add_path = args.pop(0)
        else:
            err(f"unknown argument: {arg}")
            raise Exit(2)
    if uninstall and add_path:
        err("usage: --add-skill cannot be combined with --uninstall")
        raise Exit(2)
    return harness, uninstall, add_path


def main(argv):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="backslashreplace")
        except (AttributeError, ValueError):
            pass
    try:
        harness, uninstall, add_path = parse(argv)
        out(f"python: {python_command()} ({platform.python_version()})")
        Installer(harness, uninstall, add_path).run()
    except Exit as stop:
        return stop.code
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
