"""Resolve per-project, user and adapter model selections."""

import json
from pathlib import Path


class ModelConfigError(Exception):
    def __init__(self, path, detail):
        super().__init__(f"{path}: {detail}")


def _read_models(path, defaults):
    try:
        data = json.loads(path.read_text())
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as error:
        raise ModelConfigError(path, f"invalid JSON: {error}") from error
    except (OSError, UnicodeError) as error:
        raise ModelConfigError(path, str(error)) from error
    if not isinstance(data, dict):
        raise ModelConfigError(path, "config must be an object")
    models = data.get("models", {})
    if not isinstance(models, dict):
        raise ModelConfigError(path, "models must be an object")
    for harness, tiers in models.items():
        if harness not in defaults:
            raise ModelConfigError(
                path, f"unknown harness {harness!r}; known: {', '.join(defaults)}"
            )
        if not isinstance(tiers, dict):
            raise ModelConfigError(path, f"models.{harness} must be an object")
        for tier, value in tiers.items():
            if tier not in ("deep", "standard"):
                raise ModelConfigError(
                    path, f"unknown tier {tier!r}; known: deep, standard"
                )
            if not isinstance(value, str):
                raise ModelConfigError(
                    path, f"models.{harness}.{tier} must be a string"
                )
    return models


def resolve(repo, home):
    defaults = json.loads(Path(__file__).with_name("adapter_models.json").read_text())
    user = _read_models(Path(home) / "config.json", defaults)
    project = _read_models(Path(repo) / ".factory/config.json", defaults)
    result = {}
    for harness, tiers in defaults.items():
        result[harness] = {}
        for tier, default in tiers.items():
            value = (default, "adapter")
            for source, layer in (("user", user), ("project", project)):
                if tier in layer.get(harness, {}):
                    value = (layer[harness][tier], source)
            result[harness][tier] = value
    return result


def report(resolved, json_output=False):
    if json_output:
        return json.dumps(
            {
                h: {
                    t: {"model": value, "source": source}
                    for t, (value, source) in tiers.items()
                }
                for h, tiers in resolved.items()
            },
            indent=2,
            ensure_ascii=False,
        )
    lines = ["harness  tier  model  source"]
    for harness, tiers in resolved.items():
        for tier, (value, source) in tiers.items():
            lines.append(f"{harness}  {tier}  {value}  {source}")
    return "\n".join(lines)
