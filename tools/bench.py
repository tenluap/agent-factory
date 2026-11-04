#!/usr/bin/env python3
"""Replay a fixture manually/headlessly, score recorded runs offline, compare scores."""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core" / "skills" / "factory" / "bin"))

from factory_cli import checks, state, totals  # noqa: E402

sys.path.insert(0, str(ROOT / "tools"))
import render  # noqa: E402

CONDITIONS = (
    "reached-approver",
    "last-verify-green",
    "no-blocking-findings",
    "fixture-acceptance",
)


def load_bench(name):
    if Path(name).name != name:
        raise ValueError(f"invalid benchmark name '{name}'")
    folder = ROOT / "conformance" / "bench" / name
    return folder, json.loads((folder / "bench.json").read_text())


def score(path, acceptance):
    """A missing or malformed artifact fails by condition name, never by traceback."""
    result = {
        "state": str(path),
        "run": Path(path).stem,
        "metrics": {
            "wall_ms": 0,
            "agent_ms": 0,
            "human_ms": 0,
            "spawns": 0,
            "overruns": 0,
            "issues_by_kind": dict.fromkeys(state.ISSUE_KINDS, 0),
            "tokens": {"in_est": 0, "out_est": 0, "reported": None},
            "review_rounds": 0,
            "fix_rounds": 0,
        },
        "conditions": {
            name: {"met": False, "detail": "missing evidence"} for name in CONDITIONS
        },
        "pass": False,
    }
    try:
        loaded, error = state.read_state(path)
        if error:
            raise ValueError(error)
        result["run"] = loaded.get("branch") or result["run"]
        computed = totals.compute(loaded)
        metrics = result["metrics"]
        for key in ("wall_ms", "agent_ms", "human_ms", "spawns"):
            metrics[key] = computed[key]
        metrics["tokens"] = {
            key: computed[key] for key in ("in_est", "out_est", "reported")
        }
        for issue in loaded.get("issues") or []:
            kind = issue.get("kind")
            if kind in metrics["issues_by_kind"]:
                metrics["issues_by_kind"][kind] += 1
        metrics["overruns"] = metrics["issues_by_kind"]["overrun"]
        review = loaded.get("review") or {}
        metrics["review_rounds"] = review.get("round", 0)
        metrics["fix_rounds"] = review.get("fix_rounds", 0)
        conditions = result["conditions"]
        reached = loaded.get("stage") in ("approver", "pr") or any(
            e.get("stage") == "approver" for e in loaded.get("history") or []
        )
        conditions["reached-approver"] = {
            "met": reached,
            "detail": f"recorded stage: {loaded.get('stage')}",
        }
        verify = checks.latest_verify(loaded) or {}
        conditions["last-verify-green"] = {
            "met": verify.get("event") == "verify-pass",
            "detail": f"latest verify: {verify.get('event', 'missing')}",
        }
        accepted = bool(acceptance) and any(
            command.get("command") == acceptance
            and (
                command.get("status") == "pass"
                or (type(command.get("status")) is int and command["status"] == 0)
            )
            for command in verify.get("commands") or []
        )
        conditions["fixture-acceptance"] = {
            "met": accepted,
            "detail": f"latest verify must record passing command: {acceptance}",
        }
        verdicts = []
        for verdict_path in Path(path).parent.glob("reviews/round-*/verdict.json"):
            number = verdict_path.parent.name.removeprefix("round-")
            if number.isdigit():
                verdicts.append((int(number), verdict_path))
        if verdicts:
            verdict_path = max(verdicts)[1]
            verdict = json.loads(verdict_path.read_text())
            conditions["no-blocking-findings"] = {
                "met": verdict.get("verdict") == "pass"
                and verdict.get("confirmed_blocking") == [],
                "detail": f"latest verdict: {verdict_path.parent.name} ({verdict.get('verdict')})",
            }
        result["pass"] = all(c["met"] for c in conditions.values())
    except (OSError, ValueError, TypeError, AttributeError, OverflowError) as error:
        # Files are external input; keep one bad run from hiding other scores.
        for condition in result["conditions"].values():
            condition.update(met=False, detail=f"unresolvable evidence: {error}")
    return result


def metric_leaves(metrics, prefix=""):
    """Flatten grouped numeric metrics without losing their domain names."""
    for key, value in metrics.items():
        name = f"{prefix}{key}"
        if isinstance(value, dict):
            yield from metric_leaves(value, name + ".")
        else:
            yield name, value


def compare(a_path, b_path):
    """Compare by run, not array position; missing pairs remain visible."""
    try:
        a = {s["run"]: s for s in json.loads(Path(a_path).read_text())["scores"]}
        b = {s["run"]: s for s in json.loads(Path(b_path).read_text())["scores"]}
        for run in sorted(a.keys() | b.keys()):
            print(f"run: {run}")
            if run not in a or run not in b:
                print("unpaired score")
                continue
            before = dict(metric_leaves(a[run]["metrics"]))
            after = dict(metric_leaves(b[run]["metrics"]))
            for name in sorted(before.keys() | after.keys()):
                av, bv = before.get(name), after.get(name)
                delta = (
                    f"{bv - av:+g}"
                    if type(av) in (int, float) and type(bv) in (int, float)
                    else "n/a"
                )
                print(f"{name}: {json.dumps(av)} -> {json.dumps(bv)} ({delta})")
            print(f"pass: {json.dumps(a[run]['pass'])} -> {json.dumps(b[run]['pass'])}")
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as error:
        print(f"cannot compare scores: {error}", file=sys.stderr)


EXECUTABLES = {"claude-code": "claude", "opencode": "opencode"}


CLAUDE_TOOLS = ["Read", "Edit", "Write", "Agent", "Skill", "Bash(git:*)", "Bash(python3:*)"]


def launch_command(harness, prompt, *, model, out, home, skill_dir):
    """Headless argv per contracts/bench-cli.md; Claude Code gets a scoped grant, never a bypass."""
    if harness == "opencode":
        return ["opencode", "run", *(["-m", model] if model else []), prompt]
    model_args = ["--model", model] if model else []
    out, skill = Path(out), Path(skill_dir)
    candidates = [out]
    if skill.exists():
        candidates += [skill, skill.resolve()]
    candidates.append(Path(home))
    # The output directory already covers anything inside it; each path is granted once.
    grants = []
    for path in candidates:
        if (path == out or out not in path.parents) and str(path) not in grants:
            grants.append(str(path))
    add_dirs = [arg for grant in grants for arg in ("--add-dir", grant)]
    allowed = [*CLAUDE_TOOLS, f"Bash({skill}/bin/factory:*)"]
    return ["claude", "-p", prompt, *model_args, *add_dirs, "--allowedTools", *allowed]


def adapter_template(harness):
    return json.loads((render.ADAPTERS / harness / "adapter.json").read_text())


def checkout_env(harness, config):
    """Launch variables pointing the harness at the isolated config directory."""
    if harness == "claude-code":
        return {"CLAUDE_CONFIG_DIR": str(config), "CLAUDE_HOME": str(config)}
    return {"XDG_CONFIG_HOME": str(config)}


def isolated_install(harness, out):
    """Render this checkout under `out`; the maintainer's factory home and config stay untouched."""
    home, config = out / "home", out / "harness-config"
    home.mkdir()
    config.mkdir()
    env = dict(
        os.environ,
        FACTORY_HOME=str(home),
        HOME=str(out),
        **checkout_env(harness, config),
    )
    result = subprocess.run(
        ["bash", str(ROOT / "install.sh"), "--harness", harness],
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        tail = "\n".join((result.stdout + result.stderr).splitlines()[-8:])
        raise ValueError(f"checkout render failed (exit {result.returncode}): {tail}")


def run(args):
    """Prepare a disposable repository; only the selected headless CLI spends tokens."""
    if args.harness not in EXECUTABLES:
        raise ValueError(
            f"unsupported headless harness '{args.harness}'; use the manual benchmark fallback"
        )
    executable = EXECUTABLES[args.harness]
    if not shutil.which(executable):
        raise ValueError(
            f"harness '{args.harness}' command '{executable}' is unavailable; use the manual benchmark fallback"
        )
    folder, config = load_bench(args.bench)
    if args.out:
        out = Path(args.out).expanduser().resolve()
        out.mkdir(parents=True, exist_ok=False)
    else:
        out = Path(tempfile.mkdtemp(prefix="factory-bench-"))
    repo = out / f"fixture-{args.bench}"
    if args.from_checkout:
        isolated_install(args.harness, out)
        home = out / "home"
    else:
        home = Path(args.home).expanduser().resolve() if args.home else out / "home"
    shutil.copytree(
        ROOT / config["fixture_repo"],
        repo,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    # Reuse the repository's SpecKit scaffold, then apply fixture-specific policy.
    for part in ("scripts", "templates"):
        source = ROOT / ".specify" / part
        if source.is_dir():
            shutil.copytree(source, repo / ".specify" / part)
    shutil.copytree(folder / config["overlay"], repo, dirs_exist_ok=True)
    for command in (
        ["init", "-q", "-b", "main"],
        ["config", "user.name", "Factory Benchmark"],
        ["config", "user.email", "benchmark@example.invalid"],
        ["add", "-A"],
        ["commit", "-q", "-m", "Benchmark fixture baseline"],
        ["remote", "add", "origin", str(repo)],
        ["fetch", "-q", "origin", "main"],
    ):
        subprocess.run(
            ["git", *command], cwd=repo, check=True, capture_output=True, text=True
        )
    pending = home / "pending" / f"{repo.name}-{args.bench}.json"
    pending.parent.mkdir(parents=True, exist_ok=True)
    if pending.exists():
        raise ValueError(f"pending benchmark already exists: {pending}")
    now = state.iso(datetime.now(timezone.utc))
    seed = json.loads((folder / config["seed"]).read_text())
    seed.update(
        started_at=now,
        harness=args.harness,
        repo=str(repo),
        base="origin/main",
        branch=args.bench,
        spec_dir=f"specs/{args.bench}",
    )
    seed["decisions"].append(
        {
            "stage": "plan",
            "question": "BENCH-SEAM",
            "kind": "answer",
            "auto": False,
            "at": now,
            "answer": "Fixture-author confirmation: src.greet.greet(name, uppercase=False); see seeded brief.",
        }
    )
    problems = state.validate_state(seed)
    if problems:
        raise ValueError(f"invalid benchmark seed: {problems}")
    pending.write_text(json.dumps(seed, indent=2) + "\n")
    pending.with_suffix(".brief.md").write_text((folder / config["brief"]).read_text())
    prompt = (
        f"/factory resume {pending.stem} --stop-at approver\n"
        "The seeded fixture brief contains settled decisions and explicit test-seam confirmation. "
        "Resolve required skills for this harness before spawning roles. "
        "Use the local origin/main base; no network remote is required. "
        f"Record the fixture acceptance command separately in verify: {config['acceptance']}. "
        "Stop before approver; do not approve or open a PR."
    )
    log = out / "harness.log"
    env = dict(os.environ, FACTORY_HOME=str(home), FACTORY_HARNESS=args.harness)
    if args.from_checkout:
        config_dir = out / "harness-config"
        env.update(checkout_env(args.harness, config_dir))
        skill_dir = adapter_template(args.harness)["skill_dir"].format(home=config_dir)
    else:
        skill_dir = Path(render.load_adapter(args.harness)["skill_dir"]).expanduser()
    launch = launch_command(
        args.harness,
        prompt,
        model=args.model,
        out=out,
        home=home,
        skill_dir=skill_dir,
    )
    with log.open("w") as stream:
        process = subprocess.run(
            launch,
            cwd=repo,
            env=env,
            stdout=stream,
            stderr=subprocess.STDOUT,
        )
    print(
        json.dumps(
            {
                "repo": str(repo),
                "home": str(home),
                "pending": str(pending),
                "log": str(log),
                "exit_status": process.returncode,
            }
        )
    )
    if process.returncode:
        raise ValueError(
            f"harness '{args.harness}' exited {process.returncode}; see {log}"
        )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    scoring = commands.add_parser("score")
    scoring.add_argument("states", nargs="+")
    scoring.add_argument("--bench", default="greet-001")
    comparing = commands.add_parser("compare")
    comparing.add_argument("a")
    comparing.add_argument("b")
    running = commands.add_parser("run")
    running.add_argument("--harness", required=True)
    running.add_argument("--bench", default="greet-001")
    running.add_argument("--model")
    source = running.add_mutually_exclusive_group()
    source.add_argument("--home")
    source.add_argument("--from-checkout", action="store_true")
    running.add_argument("--out")
    args = parser.parse_args(argv)
    if args.command == "compare":
        compare(args.a, args.b)
        return 0
    if args.command == "run":
        try:
            run(args)
        except (
            OSError,
            ValueError,
            TypeError,
            KeyError,
            subprocess.CalledProcessError,
        ) as error:
            print(f"benchmark run: {error}", file=sys.stderr)
            return 1
        return 0
    try:
        _, config = load_bench(args.bench)
    except (OSError, ValueError, TypeError) as error:
        config = {"acceptance": None}
        print(f"benchmark {args.bench}: {error}", file=sys.stderr)
    print(
        json.dumps(
            {
                "bench": args.bench,
                "scores": [
                    score(path, config.get("acceptance")) for path in args.states
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
