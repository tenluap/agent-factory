#!/usr/bin/env python3
"""Render the factory for one harness: core/ + adapters/ -> dist/<harness>/.

dist/<harness>/skill/   the orchestrator skill, with references/harness/<name>.md for every
                        adapter and roles/ added; identical for every harness
dist/<harness>/agents/  one native agent file per role, in this harness's format

Usage: render.py <harness>          render, print nothing
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
    return meta, text[m.end():]


def known():
    return sorted(p.name for p in ADAPTERS.iterdir() if (p / "adapter.json").exists())


def load_adapter(name):
    path = ADAPTERS / name / "adapter.json"
    if not path.exists():
        raise SystemExit(f"unknown harness '{name}' (known: {', '.join(known())})")
    adapter = json.loads(path.read_text())
    # User overrides: ${FACTORY_HOME}/config.json {"models": {"<harness>": {"deep": "...", "standard": "..."}}}
    config = Path(os.path.expanduser(os.environ.get("FACTORY_HOME", "~/.factory"))) / "config.json"
    if config.exists():
        adapter["models"].update(json.loads(config.read_text()).get("models", {}).get(name, {}))
    home = os.environ.get(adapter["home"]["env"]) or adapter["home"]["default"]
    adapter["skill_dir"] = adapter["skill_dir"].format(home=home)
    adapter["agent_dir"] = adapter["agent_dir"].format(home=home)
    return adapter


def agent_fields(adapter, meta, values):
    """Ordered (key, value) pairs for one agent's frontmatter."""
    fields = [(key, template.format(**values)) for key, template in adapter["fields"]]
    fields += list(adapter.get("extra", {}).items())
    fields += list(adapter["access"][meta["access"]].items())
    model = adapter["models"].get(meta["tier"], "")
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
            raise SystemExit("role body contains ''' and cannot be a TOML literal string")
        head = "\n".join(f"{key} = {toml_value(value)}" for key, value in fields)
        return f"{head}\ndeveloper_instructions = '''\n{body.lstrip(chr(10))}'''\n"
    raise SystemExit(f"unknown agent_format '{adapter['agent_format']}'")


def render(name):
    adapter = load_adapter(name)
    out = ROOT / "dist" / name
    shutil.rmtree(out, ignore_errors=True)

    # The skill is the same for every harness: the orchestrator picks its harness file at runtime,
    # so harnesses that read each other's skill directories all see the same skill.
    skill = out / "skill"
    shutil.copytree(ROOT / "core" / "skills" / "factory", skill)
    (skill / "references" / "harness").mkdir()
    for other in known():
        shutil.copy(ADAPTERS / other / "harness.md", skill / "references" / "harness" / f"{other}.md")
    (skill / "roles").mkdir()
    (out / "agents").mkdir()

    for role_file in sorted((ROOT / "core" / "roles").glob("*.md")):
        meta, body = frontmatter(role_file.read_text())
        (skill / "roles" / role_file.name).write_text(body.lstrip("\n"))
        values = {
            "role": meta["name"],
            "role_": meta["name"].replace("-", "_"),
            "description": meta["description"],
        }
        fields = agent_fields(adapter, meta, values)
        text = render_agent(adapter, fields, body.replace("<F>", adapter["skill_dir"]))
        (out / "agents" / adapter["agent_file"].format(**values)).write_text(text)
    return adapter, out


def main():
    args = sys.argv[1:]
    if args == ["--list"]:
        print("\n".join(known()))
        return
    if not args or args[0].startswith("-"):
        raise SystemExit(__doc__.strip())
    adapter, out = render(args[0])
    if "--paths" in args:
        for key, value in (("dist", str(out)), ("skill_dir", adapter["skill_dir"]), ("agent_dir", adapter["agent_dir"])):
            print(f"{key}={shlex.quote(os.path.expanduser(value))}")


if __name__ == "__main__":
    main()
