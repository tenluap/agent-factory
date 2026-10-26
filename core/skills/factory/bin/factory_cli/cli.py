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

read:
  runs [--repo <path>]              unfinished runs of the repo, JSON
  show <run> [--repo <path>]        resume digest for one run, JSON
  validate <run> | validate --all   validation violations; exit 1 when any

write (the single writer; each stamps its time, validates, writes atomically):
  checkpoint <stage> [--next <stage>]                 record a stage complete
  ledger-add <stage> <role> [--started-at a] [--ended-at e]
            [--in-est N] [--out-est N] [--reported '<json>']
  wait-open <kind> <stage> <summary> -> wait-id     open a user wait
  wait-close <wait-id>                              close it
  answer <qid> '<answer>' [--auto] [--stage <stage>]  settle one relay answer
  set-status <status> [--halt-reason <text>] [--pr-url <url>]
  decisions-add <stage> <qid> '<answer>' [--kind answer|approved|gate-override]
  envelope check <file>                             validate the final fenced json block\n  verify --pass|--fail --commands '<json>'          record the build/test verify pair
  lock take <run> [--force]                         the only explicit takeover

<run> is a run's branch (worktree runs) or a pending file's name, with or
without the <repo-name>- prefix and .json suffix. Exit codes: 0 success,
1 no run or refused, 2 not a git repository, 3 ambiguous name, 4 the run's
recorded worktree is gone, 5 usage error."""


def die_usage(message):
    raise CLIError(5, f"{message}\n\n{USAGE}")


def parse_flags(rest, command, value_flags=("--repo",), bool_flags=(), allow_all=False):
    """Split `rest` into (positional, flags); usage errors exit 5."""
    positional, flags = [], {}
    rest = iter(rest)
    for flag in rest:
        if flag == "--all" and allow_all:
            flags["--all"] = True
            continue
        if flag in bool_flags:
            flags[flag] = True
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


def int_or_usage(value, flag):
    try:
        return int(value)
    except (TypeError, ValueError):
        die_usage(f"{flag} needs an integer")


def json_or_usage(value, flag):
    try:
        return json.loads(value)
    except ValueError:
        die_usage(f"{flag} needs JSON")


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
        elif command == "checkpoint":
            positional, flags = parse_flags(
                rest, command, value_flags=("--repo", "--next")
            )
            if len(positional) != 1:
                die_usage("checkpoint needs exactly one <stage>")
            repo = commands.main_repo(Path(flags.get("--repo") or Path.cwd()))
            result = commands.cmd_checkpoint(
                repo, Path.cwd(), positional[0], next_stage=flags.get("--next")
            )
        elif command == "ledger-add":
            positional, flags = parse_flags(
                rest,
                command,
                value_flags=(
                    "--repo",
                    "--started-at",
                    "--ended-at",
                    "--in-est",
                    "--out-est",
                    "--reported",
                ),
            )
            if len(positional) != 2:
                die_usage("ledger-add needs <stage> <role>")
            repo = commands.main_repo(Path(flags.get("--repo") or Path.cwd()))
            result = commands.cmd_ledger_add(
                repo,
                Path.cwd(),
                positional[0],
                positional[1],
                started_at=flags.get("--started-at"),
                ended_at=flags.get("--ended-at"),
                in_est=int_or_usage(flags["--in-est"], "--in-est")
                if "--in-est" in flags
                else 0,
                out_est=int_or_usage(flags["--out-est"], "--out-est")
                if "--out-est" in flags
                else 0,
                reported=json_or_usage(flags["--reported"], "--reported")
                if "--reported" in flags
                else None,
            )
        elif command == "wait-open":
            positional, flags = parse_flags(rest, command)
            if len(positional) != 3:
                die_usage("wait-open needs <kind> <stage> <summary>")
            repo = commands.main_repo(Path(flags.get("--repo") or Path.cwd()))
            result = commands.cmd_wait_open(repo, Path.cwd(), *positional)
        elif command == "wait-close":
            positional, flags = parse_flags(rest, command)
            if len(positional) != 1:
                die_usage("wait-close needs <wait-id>")
            repo = commands.main_repo(Path(flags.get("--repo") or Path.cwd()))
            result = commands.cmd_wait_close(
                repo, Path.cwd(), int_or_usage(positional[0], "wait-id")
            )
        elif command == "answer":
            positional, flags = parse_flags(
                rest, command, value_flags=("--repo", "--stage"), bool_flags=("--auto",)
            )
            if len(positional) != 2:
                die_usage("answer needs <qid> <answer>")
            repo = commands.main_repo(Path(flags.get("--repo") or Path.cwd()))
            result = commands.cmd_answer(
                repo,
                Path.cwd(),
                positional[0],
                positional[1],
                auto=bool(flags.get("--auto")),
                stage=flags.get("--stage"),
            )
        elif command == "set-status":
            positional, flags = parse_flags(
                rest, command, value_flags=("--repo", "--halt-reason", "--pr-url")
            )
            if len(positional) != 1:
                die_usage("set-status needs exactly one <status>")
            repo = commands.main_repo(Path(flags.get("--repo") or Path.cwd()))
            result = commands.cmd_set_status(
                repo,
                Path.cwd(),
                positional[0],
                halt_reason=flags.get("--halt-reason"),
                pr_url=flags.get("--pr-url"),
            )
        elif command == "envelope":
            if rest[:1] != ["check"] or len(rest) < 2:
                die_usage("envelope supports only: envelope check <file>")
            if rest[2:]:
                die_usage("envelope check takes exactly one <file>")
            result = commands.cmd_envelope_check(rest[1])
        elif command == "verify":
            _, flags = parse_flags(
                rest, command, value_flags=("--repo",), bool_flags=("--pass", "--fail")
            )
            if bool(flags.get("--pass")) == bool(flags.get("--fail")):
                die_usage("verify needs exactly one of --pass or --fail")
            payload = (
                json_or_usage(flags["--commands"], "--commands")
                if "--commands" in flags
                else []
            )
            if not isinstance(payload, list) or payload == []:
                die_usage("--commands needs a JSON list of {command, status} objects")
            repo = commands.main_repo(Path(flags.get("--repo") or Path.cwd()))
            result = commands.cmd_verify(
                repo,
                Path.cwd(),
                passed=bool(flags.get("--pass")),
                commands_payload=[
                    (c.get("command"), c.get("status")) for c in payload if isinstance(c, dict)
                ],
            )
        elif command == "lock":
            sub = rest[:1]
            if sub != ["take"]:
                die_usage("lock supports only: lock take <run> [--force]")
            positional, flags = parse_flags(rest[1:], command, bool_flags=("--force",))
            if len(positional) != 1:
                die_usage("lock take needs exactly one <run>")
            repo = commands.main_repo(Path(flags.get("--repo") or Path.cwd()))
            result = commands.cmd_lock_take(repo, positional[0], force=bool(flags.get("--force")))
        elif command == "decisions-add":
            positional, flags = parse_flags(
                rest, command, value_flags=("--repo", "--kind")
            )
            if len(positional) != 3:
                die_usage("decisions-add needs <stage> <qid> <answer>")
            repo = commands.main_repo(Path(flags.get("--repo") or Path.cwd()))
            result = commands.cmd_decisions_add(
                repo, Path.cwd(), *positional, kind=flags.get("--kind") or "answer"
            )
        else:
            die_usage(f"unknown command '{command}'")
        emit(result)
    except commands.state.StateError as e:  # a refused write names its reason
        print(f"factory: {e}", file=sys.stderr)
        raise SystemExit(1)
    except CLIError as e:
        print(f"factory: {e}", file=sys.stderr)
        raise SystemExit(e.code)
