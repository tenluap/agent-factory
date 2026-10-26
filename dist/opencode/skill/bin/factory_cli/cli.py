"""argv parsing, usage text and exit codes for the factory CLI (FR-020's shape).

Exit codes (contracts/cli.md): 0 success; 1 no matching run or refused write;
2 not a git repository or git not runnable; 3 ambiguous run name; 4 the run's
recorded worktree no longer exists; 5 usage error.
"""

import json
import sys
from pathlib import Path

from factory_cli import commands
from factory_cli.commands import CLIError

USAGE = """usage: factory <command> [args]

commands:
  runs [--repo <path>]              unfinished runs of the repo, JSON
  show <run> [--repo <path>]        resume digest for one run, JSON
  validate <run> | validate --all   validation violations; exit 1 when any

<run> is a run's branch (worktree runs) or a pending file's name, with or
without the <repo-name>- prefix and .json suffix. Exit codes: 0 success,
1 no run or refused, 2 not a git repository, 3 ambiguous name, 4 the run's
recorded worktree is gone, 5 usage error."""


def die_usage(message):
    raise CLIError(5, f"{message}\n\n{USAGE}")


def parse_flags(rest, command, value_flags=("--repo",), allow_all=False):
    """Split `rest` into (positional, flags); usage errors exit 5."""
    positional, flags = [], {}
    rest = iter(rest)
    for flag in rest:
        if flag == "--all" and allow_all:
            flags["--all"] = True
            continue
        if not flag.startswith("-"):
            positional.append(flag)
            continue
        if flag not in value_flags:
            die_usage(f"{command}: unknown argument '{flag}'")
        value = next(rest, None)
        if not value:
            die_usage(f"{command}: {flag} needs a value")
        flags[flag] = value
    return positional, flags


def emit(result):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


def main(argv):
    args = argv[1:]
    if not args:
        raise CLIError(5, USAGE)
    command, rest = args[0], args[1:]
    try:
        if command == "runs":
            _, flags = parse_flags(rest, command)
            repo = commands.main_repo(Path(flags.get("--repo") or Path.cwd()))
            result = commands.cmd_runs(repo)
        elif command == "show":
            positional, flags = parse_flags(rest, command)
            if len(positional) != 1:
                die_usage("show needs exactly one <run>")
            repo = commands.main_repo(Path(flags.get("--repo") or Path.cwd()))
            result = commands.cmd_show(repo, positional[0])
        elif command == "validate":
            positional, flags = parse_flags(rest, command, allow_all=True)
            repo = commands.main_repo(Path(flags.get("--repo") or Path.cwd()))
            result = commands.cmd_validate(
                repo,
                positional[0] if positional else None,
                all_runs=bool(flags.get("--all")),
            )
            emit(result)
            raise SystemExit(1 if result else 0)
        else:
            die_usage(f"unknown command '{command}'")
        emit(result)
    except CLIError as e:
        print(f"factory: {e}", file=sys.stderr)
        raise SystemExit(e.code)
