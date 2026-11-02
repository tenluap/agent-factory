#!/usr/bin/env python3
"""Render the factory for one harness: core/ + adapters/ -> dist/<harness>/.

dist/<harness>/skill/    the orchestrator skill, with references/harness/<name>.md for every
                         adapter and roles/ added; identical for every harness
dist/<harness>/skills/   the first-party skills (core/skills/ except factory), verbatim
dist/<harness>/agents/   one native agent file per role, in this harness's format

Usage: render.py <harness>          render, print nothing
       render.py <harness> --out <dir>  per-user render into <dir>
       render.py <harness> --paths  report the install targets, write nothing
       render.py <harness> --models report the effective model per role, write nothing
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
    meta = {}
    block = m.group(1)
    lines = block.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.startswith("  "):  # continuation of a block value
            raise SystemExit(f"frontmatter: unexpected continuation line: {line!r}")
        key, colon, value = line.partition(":")
        if not colon:
            raise SystemExit(f"frontmatter: expected 'key: value', got: {line!r}")
        stripped = value.strip()
        if stripped in ("", "|", ">"):  # block list or literal: collect indented lines
            items = []
            index += 1
            while index < len(lines) and lines[index].startswith("  "):
                items.append(lines[index].strip())
                index += 1
            if (
                stripped == ""
                and items
                and all(item.startswith("- ") for item in items)
            ):
                values = [item[2:].strip() for item in items]
                if all(
                    value.startswith("{") and value.endswith("}") for value in values
                ):
                    import json

                    meta[key] = [json.loads(value) for value in values]
                else:
                    meta[key] = values
            elif items:
                raise SystemExit(f"frontmatter: unsupported block for '{key}'")
            else:
                raise SystemExit(f"frontmatter: '{key}' has no value")
            continue
        meta[key] = stripped
        index += 1
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
    try:
        models = json.loads(config.read_text())
        for key in ("models", name):
            if not isinstance(models, dict):
                raise ValueError("expected a JSON object")
            models = models.get(key, {})
        if not isinstance(models, dict):
            raise ValueError("expected a JSON object")
    except (OSError, ValueError) as error:
        raise SystemExit(f"{config}: {error}")
    return models


def load_adapter(name, *, use_env=True):
    path = ADAPTERS / name / "adapter.json"
    if not path.exists():
        raise SystemExit(f"unknown harness '{name}' (known: {', '.join(known())})")
    adapter = json.loads(path.read_text())
    home = adapter["home"]["default"]
    if use_env:
        home = os.environ.get(adapter["home"]["env"]) or home
    adapter["skill_dir"] = adapter["skill_dir"].format(home=home)
    adapter["skills_root"] = adapter["skills_root"].format(home=home)
    adapter["agent_dir"] = adapter["agent_dir"].format(home=home)
    return adapter


def agent_fields(adapter, meta, values, models=None):
    """Ordered (key, value) pairs for one agent's frontmatter."""
    if models is None:
        models = adapter["models"]
    fields = [(key, template.format(**values)) for key, template in adapter["fields"]]
    # A role's `mode` (e.g. primary) maps to adapter fields that replace same-named extras.
    mode = adapter.get("modes", {}).get(meta.get("mode", ""), {})
    fields += [(k, v) for k, v in adapter.get("extra", {}).items() if k not in mode]
    fields += list(mode.items())
    fields += list(adapter["access"][meta["access"]].items())
    # A role's optional `permissions` passthrough (approval prompts a harness
    # can enforce, e.g. OpenCode's shell rules) merges into one field after
    # the access rules. Frontmatter rules are JSON objects
    # ({"action": "shell", "resource": "*npm install*", "effect": "ask"}).
    # Adapters that cannot express them (tools lists, TOML string fields)
    # drop them: permissions are advisory where a harness can carry them,
    # and one role must not break every harness's render.
    rules = []
    for rule in meta.get("permissions", []):
        if not isinstance(rule, dict):
            raise SystemExit(f"role '{meta['name']}': bad permission rule {rule!r}")
        effect = rule.get("effect", "ask")
        if (
            not isinstance(rule.get("action"), str)
            or not isinstance(rule.get("resource"), str)
            or effect not in ("ask", "deny", "allow")
        ):
            raise SystemExit(f"role '{meta['name']}': bad permission rule {rule!r}")
        rules.append(
            {"action": rule["action"], "resource": rule["resource"], "effect": effect}
        )
    if rules and any("permissions" in access for access in adapter["access"].values()):
        merged = list(next(v for k, v in fields if k == "permissions"))
        merged += rules
        fields = [(k, merged if k == "permissions" else v) for k, v in fields]
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


def roles():
    """(file name, meta, body) per role file, sorted — one pass over core/roles."""
    for role_file in sorted((ROOT / "core" / "roles").glob("*.md")):
        meta, body = frontmatter(role_file.read_text())
        yield role_file.name, meta, body


def effective_models(models):
    """(role, model) per role — the effective-model report rows."""
    return [(meta["name"], models.get(meta["tier"], "")) for _, meta, _ in roles()]


def render(name, out=None):
    """Render one harness tree into the target directory and return it.

    out=None is the canonical dist/<harness> target and never reads user
    configuration (FR-002). An explicit `out` is the per-user render: the
    default home's config.json models merge per key over the adapter
    defaults (FR-001, FR-003).
    """
    adapter = load_adapter(name, use_env=out is not None)
    merge = config_models(name) if out is not None else {}
    models = {**adapter["models"], **merge}
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
    # First-party skills render next to the orchestrator (ADR 0012): consumers
    # see the whole core skill set inside dist/<harness>/skills/.
    skills = target / "skills"
    for source in sorted((ROOT / "core" / "skills").iterdir()):
        if source.name != "factory" and (source / "SKILL.md").exists():
            shutil.copytree(source, skills / source.name)
    (skill / "roles").mkdir()
    (target / "agents").mkdir()

    tiers = {}
    for role_name, meta, body in roles():
        tiers[meta["name"]] = meta["tier"]
        (skill / "roles" / role_name).write_text(body.lstrip("\n"))
        values = {
            "role": meta["name"],
            "role_": meta["name"].replace("-", "_"),
            "description": meta["description"],
        }
        fields = agent_fields(adapter, meta, values, models=models)
        text = render_agent(adapter, fields, body.replace("<F>", adapter["skill_dir"]))
        (target / "agents" / adapter["agent_file"].format(**values)).write_text(text)
    (skill / "roles" / "tiers.json").write_text(json.dumps(tiers, indent=2) + "\n")
    return target


def print_paths(adapter, target):
    for key, value in (
        ("dist", str(target)),
        ("skill_dir", adapter["skill_dir"]),
        ("skills_root", adapter["skills_root"]),
        ("agent_dir", adapter["agent_dir"]),
    ):
        print(f"{key}={shlex.quote(os.path.expanduser(value))}")


def print_models(harness):
    adapter = load_adapter(harness)
    models = {**adapter["models"], **config_models(harness)}
    for role, model in effective_models(models):
        print(f"{role}: {model or '(session default)'}")


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
    harness = args[0]
    if "--models" in args or "--paths" in args:
        # write-free reports (FR-004): print and leave the tree alone
        adapter = load_adapter(harness)
        if "--paths" in args:
            print_paths(
                adapter, Path(out) if out is not None else ROOT / "dist" / harness
            )
        if "--models" in args:
            print_models(harness)
        return
    render(harness, out=out)


if __name__ == "__main__":
    main()
