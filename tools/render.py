#!/usr/bin/env python3
"""Render the factory for one harness: core/ + adapters/ -> dist/<harness>/.

dist/<harness>/skill/   the orchestrator skill, with references/harness/<name>.md for every
                        adapter and roles/ added; identical for every harness
dist/<harness>/agents/  one native agent file per role, in this harness's format

Usage: render.py <harness>          render, print nothing
       render.py <harness> --out <dir>  per-user render into <dir>
       render.py <harness> --paths  render, then print the install targets as shell assignments
       render.py --list             print the known harnesses
"""

import json
import os
import re
import shlex
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADAPTERS = ROOT / "adapters"


def frontmatter(text):
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        raise SystemExit("missing frontmatter")
    meta = dict(line.split(": ", 1) for line in m.group(1).splitlines())
    return meta, text[m.end() :]


def known():
    return sorted(p.name for p in ADAPTERS.iterdir() if (p / "adapter.json").exists())


def default_home():
    """The documented factory home: ${FACTORY_HOME:-~/.factory}, expanded."""
    return Path(os.environ.get("FACTORY_HOME") or "~/.factory").expanduser()


def config_models(name, home=None):
    """User model overrides for `name` from `<home>/config.json`
    (`{"models": {"<harness>": {"deep": "...", "standard": "..."}}}`); {}
    when the file or the keys are absent (per-key fallback, FR-003).

    `home=None` resolves the documented default home. The canonical dist/
    render never reads user configuration (FR-002); this feeds the per-user
    render (FR-001) and the effective-model report.
    """
    if home is None:
        home = default_home()
    config = home / "config.json"
    if not config.exists():
        return {}
    return json.loads(config.read_text()).get("models", {}).get(name, {})


def load_adapter(name):
    path = ADAPTERS / name / "adapter.json"
    if not path.exists():
        raise SystemExit(f"unknown harness '{name}' (known: {', '.join(known())})")
    adapter = json.loads(path.read_text())
    home = os.environ.get(adapter["home"]["env"]) or adapter["home"]["default"]
    adapter["skill_dir"] = adapter["skill_dir"].format(home=home)
    adapter["agent_dir"] = adapter["agent_dir"].format(home=home)
    return adapter


def agent_fields(adapter, meta, values, models=None):
    """Ordered (key, value) pairs for one agent's frontmatter."""
    if models is None:
        models = adapter["models"]
    fields = [(key, template.format(**values)) for key, template in adapter["fields"]]
    fields += list(adapter.get("extra", {}).items())
    fields += list(adapter["access"][meta["access"]].items())
    model = models.get(meta["tier"], "")
    if model:  # empty: the agent inherits the session's model
        fields.append(("model", model))
    return fields


def yaml_value(value):
    if isinstance(value, dict):
        return "".join(f"\n  {k}: {v}" for k, v in value.items())
    if isinstance(value, list):
        if value and all(isinstance(item, dict) for item in value):
            # JSON flow mappings are valid YAML; quoting protects wildcard resources.
            return "".join(f"\n  - {json.dumps(item)}" for item in value)
        return " [" + ", ".join(value) + "]"
    return f" {value}"


def toml_value(value):
    if isinstance(value, (dict, list)):
        raise SystemExit("toml agents take plain string fields only")
    return json.dumps(value)  # a JSON string is a valid TOML basic string


def render_agent(adapter, fields, body):
    if adapter["agent_format"] == "markdown":
        head = "\n".join(f"{key}:{yaml_value(value)}" for key, value in fields)
        return f"---\n{head}\n---\n{body}"
    if adapter["agent_format"] == "toml":
        if "'''" in body:
            raise SystemExit(
                "role body contains ''' and cannot be a TOML literal string"
            )
        head = "\n".join(f"{key} = {toml_value(value)}" for key, value in fields)
        return f"{head}\ndeveloper_instructions = '''\n{body.lstrip(chr(10))}'''\n"
    raise SystemExit(f"unknown agent_format '{adapter['agent_format']}'")


def render(name, out=None):
    """Render one harness tree and return (adapter, target, effective).

    out=None is the canonical dist/<harness> target and never merges user
    configuration (FR-002). An explicit `out` is the per-user render: the
    default home's config.json models merge per key over the adapter
    defaults (FR-001, FR-003).
    """
    adapter = load_adapter(name)
    if out is None:
        # interim: the canonical render's report keeps the explicit-home
        # lookup until the write-free report split (FR-004) lands
        explicit = os.environ.get("FACTORY_HOME")
        merge = config_models(name, Path(explicit).expanduser()) if explicit else {}
    else:
        merge = config_models(name)
    report_models = {**adapter["models"], **merge}
    models = report_models if out is not None else adapter["models"]
    effective = []  # (role, model) per role, for the effective-model report
    target = Path(out) if out is not None else ROOT / "dist" / name
    shutil.rmtree(target, ignore_errors=True)

    # The skill is the same for every harness: the orchestrator picks its harness file at runtime,
    # so harnesses that read each other's skill directories all see the same skill.
    skill = target / "skill"
    shutil.copytree(ROOT / "core" / "skills" / "factory", skill)
    (skill / "references" / "harness").mkdir()
    for other in known():
        shutil.copy(
            ADAPTERS / other / "harness.md",
            skill / "references" / "harness" / f"{other}.md",
        )
    (skill / "roles").mkdir()
    (target / "agents").mkdir()

    for role_file in sorted((ROOT / "core" / "roles").glob("*.md")):
        meta, body = frontmatter(role_file.read_text())
        (skill / "roles" / role_file.name).write_text(body.lstrip("\n"))
        values = {
            "role": meta["name"],
            "role_": meta["name"].replace("-", "_"),
            "description": meta["description"],
        }
        fields = agent_fields(adapter, meta, values, models=models)
        text = render_agent(adapter, fields, body.replace("<F>", adapter["skill_dir"]))
        (target / "agents" / adapter["agent_file"].format(**values)).write_text(text)
        effective.append((meta["name"], report_models.get(meta["tier"], "")))
    return adapter, target, effective


def main():
    args = sys.argv[1:]
    if args == ["--list"]:
        print("\n".join(known()))
        return
    out = None
    if "--out" in args:
        i = args.index("--out")
        if i + 1 >= len(args):
            raise SystemExit("--out needs a directory")
        out = args[i + 1]
        args = args[:i] + args[i + 2 :]
    if not args or args[0].startswith("-"):
        raise SystemExit(__doc__.strip())
    adapter, target, effective = render(args[0], out=out)
    if "--paths" in args:
        for key, value in (
            ("dist", str(target)),
            ("skill_dir", adapter["skill_dir"]),
            ("agent_dir", adapter["agent_dir"]),
        ):
            print(f"{key}={shlex.quote(os.path.expanduser(value))}")
    if "--models" in args:  # the effective model per role after overrides (FR-015)
        for role, model in effective:
            print(f"{role}: {model or '(session default)'}")


if __name__ == "__main__":
    main()
