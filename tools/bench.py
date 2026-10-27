#!/usr/bin/env python3
"""Replay a fixture manually/headlessly, score recorded runs offline, compare scores."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core" / "skills" / "factory" / "bin"))

from factory_cli import checks, state, totals  # noqa: E402

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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    scoring = commands.add_parser("score")
    scoring.add_argument("states", nargs="+")
    scoring.add_argument("--bench", default="greet-001")
    comparing = commands.add_parser("compare")
    comparing.add_argument("a")
    comparing.add_argument("b")
    args = parser.parse_args(argv)
    if args.command == "compare":
        compare(args.a, args.b)
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
