"""Resolve per-project, user and adapter model selections."""

import json
import os
import secrets
import stat
from pathlib import Path


class ModelConfigError(Exception):
    def __init__(self, path, detail):
        super().__init__(f"{path}: {detail}")


def _read_models(path, defaults):
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
        with os.fdopen(fd, "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise ModelConfigError(path, "config must be a regular file")
            contents = stream.read(1024 * 1024 + 1)
        if len(contents) > 1024 * 1024:
            raise ModelConfigError(path, "config exceeds 1 MiB")
        data = json.loads(contents)
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


def resolve(repo, home, *, include_project=True):
    defaults = json.loads(Path(__file__).with_name("adapter_models.json").read_text())
    user = _read_models(Path(home) / "config.json", defaults)
    project = (
        _read_models(Path(repo) / ".factory/config.json", defaults)
        if include_project
        else {}
    )
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


def init(repo, home):
    directory = Path(repo) / ".factory"
    config = directory / "config.json"
    if config.exists() or config.is_symlink():
        raise FileExistsError(f"{config}: already exists; refusing to overwrite")
    resolved = resolve(repo, home, include_project=False)
    seeded = {
        h: {t: value for t, (value, _) in tiers.items()}
        for h, tiers in resolved.items()
    }
    table = report(resolved)
    readme = (
        "# Factory model configuration\n\n"
        'Schema: `{"models": {"<harness>": {"deep": "<model>", "standard": "<model>"}}}`.\n'
        "An empty string inherits the session model.\n\n"
        "Precedence per tier: project, then user, then adapter.\n\n"
        "## Seeded defaults and sources\n\n```\n" + table + "\n```\n\n"
        "To restore a default, remove the tier key to inherit the user or adapter value, "
        "or restore the value shown above.\n"
    )
    directory.mkdir(parents=True, exist_ok=True)
    try:
        dirfd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError as error:
        raise ModelConfigError(directory, str(error)) from error
    try:
        for filename, text in (
            (
                "config.json",
                json.dumps({"models": seeded}, indent=2, sort_keys=True) + "\n",
            ),
            ("config.README.md", readme),
        ):
            name = ".factory-" + secrets.token_hex(16)
            created = False
            try:
                fd = os.open(
                    name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=dirfd
                )
                created = True
                with os.fdopen(fd, "w", encoding="utf-8") as temp:
                    temp.write(text)
                os.replace(name, filename, src_dir_fd=dirfd, dst_dir_fd=dirfd)
            finally:
                if created:
                    try:
                        os.unlink(name, dir_fd=dirfd)
                    except FileNotFoundError:
                        pass
    finally:
        os.close(dirfd)
    return table + "\n\nModels are unverified until a run's preflight."
