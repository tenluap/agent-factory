"""argv parsing, usage text and exit codes for the factory CLI (FR-020's shape).

Exit codes (contracts/cli.md): 0 success; 1 no matching run or refused write;
2 not a git repository or git not runnable; 3 ambiguous run name; 4 the run's
recorded worktree no longer exists; 5 usage error.
"""

import json
import sys
from pathlib import Path

from factory_cli import adopt, commands, models, state
from factory_cli.commands import CLIError

USAGE = """usage: factory <command> [args]

read:
  runs [--repo <path>]              unfinished runs of the repo, JSON
  show <run> [--repo <path>]        resume digest for one run, JSON
  validate <run> | validate --all   validation violations; exit 1 when any
  resume <run> [mode flags]         record the resumed entry, print the resume digest
  mode [--lite|--full] [--fast|--no-fast] [--cruise|--no-cruise]
                                    resolve mode flags into mode JSON; writes nothing
  budget <role>                     the role's resolved seconds and deadline, JSON
  models [--json]                   effective models and sources
  improvements                      backlogs, kind counts and suggested features, JSON
  detect [--repo <path>]            the repo's stack profile, JSON (spec 017)
  adopt <branch|spec_dir> [--stage <s>] [--dry-run]
                                    adopt a spec factory did not start: the report with
                                    --dry-run (JSON), else the worktree run's resume digest

write (the single writer; each stamps its time, validates, writes atomically):
  init                              seed project model configuration
  models-record [--from <path>]     record run models from a file or stdin;
                                     never inline JSON on the command line
  drop                              archive and remove a completed run
  checkpoint <stage> [--next <stage>] [--files <path>... | --envelope <file>]
  amendment-check <draft> [--sha256 <hex>]
                                    hash a constitution draft; refuses a changed draft
  analyze-record <envelope> [--fresh-baseline]
                                    validate and record an analysis outcome; the
                                    first record sets the baseline
  profile-record                    detect the repo and record the profile into
                                    the one writable run; discloses a changed stack
  ledger-add <stage> <role> [--started-at a] [--ended-at e]
            [--in-est N] [--out-est N] [--reported '<json>']
            [--overrun '<json>'] [--partial-return]
  issue-add <kind> <stage> <role> --detail <text> --duration-ms <n>
            [--cause <cause>] [--commit <sha>] [--partial-return]
  improvements claim <name>         claim a ready backlog, never start a run
  improvements add --from <file> --run <branch>  write retro candidates
  feedback [<branch>] [--repo <path>]  refresh archived runs' PR outcomes and feedback entries
  wait-open <kind> <stage> <summary> -> wait-id     open a user wait
  wait-close <wait-id>                              close it
  answer <qid> '<answer>' [--auto] [--stage <stage>]  settle one relay answer
  set-status <status> [--halt-reason <text>] [--pr-url <url>]
  decisions-add <stage> <qid> '<answer>' [--kind answer|approved|gate-override]
  envelope check <file>                             validate the final fenced json block\n  verify --pass|--fail --commands '<json>'          record the build/test verify pair
  prune [--dry-run|--delete]                        list stale pending files; only --delete deletes\n  rebind <run> --worktree <path>                    rewrite a moved run's stored paths\n  lock take <run> [--force]                         the only explicit takeover

<run> is a run's branch (worktree runs) or a pending file's name, with or
without the <repo-name>- prefix and .json suffix. Exit codes: 0 success,
1 no run, refused, or a feedback gap, 2 not a git repository, 3 ambiguous
name, 4 the run's recorded worktree is gone, 5 usage error."""


MODE_FLAGS = ("--lite", "--full", "--fast", "--no-fast", "--cruise", "--no-cruise")


def die_usage(message):
    raise CLIError(5, f"{message}\n\n{USAGE}")


def parse_flags(
    rest,
    command,
    value_flags=("--repo",),
    bool_flags=(),
    allow_all=False,
    repeat_flags=(),
):
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
        if flag in repeat_flags:
            value = next(rest, None)
            if not value:
                die_usage(f"{command}: {flag} needs a value")
            flags.setdefault(flag, []).append(value)
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


def iso_or_usage(value, flag):
    """An ISO-8601 UTC timestamp or a usage refusal naming the bad value."""
    if value is None or not state.parse_iso(value):
        die_usage(f"{flag} needs an ISO-8601 UTC timestamp, got '{value}'")
    return value


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
        if command == "init":
            positional, _ = parse_flags(rest, command, value_flags=())
            if positional:
                die_usage("init takes no arguments")
            repo = commands.main_repo(Path.cwd())
            try:
                print(models.init(repo, commands.factory_home()))
            except FileExistsError as e:
                raise CLIError(1, str(e)) from e
            return
        elif command == "models-record":
            positional, flags = parse_flags(
                rest, command, value_flags=("--repo", "--from")
            )
            if positional:
                die_usage(
                    "models-record takes no inline JSON; write the block to a file and pass"
                    " --from <path>, or pipe it on stdin"
                )
            source = flags.get("--from")
            if source is not None:
                try:
                    raw = Path(source).read_text(encoding="utf-8")
                except OSError as error:
                    die_usage(f"models-record: cannot read {source}: {error}")
            else:
                raw = sys.stdin.read()
            try:
                block = json.loads(raw)
            except ValueError:
                die_usage("models-record needs JSON")
            repo = commands.main_repo(Path(flags.get("--repo") or Path.cwd()))
            result = commands.cmd_models_record(repo, Path.cwd(), block)
        elif command == "models":
            positional, flags = parse_flags(
                rest, command, value_flags=(), bool_flags=("--json",)
            )
            if positional:
                die_usage("models takes no positional arguments")
            repo = commands.main_repo(Path.cwd())
            print(
                models.report(
                    models.resolve(repo, commands.factory_home()),
                    bool(flags.get("--json")),
                )
            )
            return
        elif command == "runs":
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
        elif command == "drop":
            positional, flags = parse_flags(rest, command)
            if positional:
                die_usage("drop takes no positional arguments")
            repo = commands.main_repo(Path(flags.get("--repo") or Path.cwd()))
            result = commands.cmd_drop(repo, Path.cwd())
        elif command == "checkpoint":
            positional, flags = parse_flags(
                rest,
                command,
                value_flags=("--repo", "--next", "--envelope"),
                repeat_flags=("--files",),
            )
            if len(positional) != 1:
                die_usage("checkpoint needs exactly one <stage>")
            repo = commands.main_repo(Path(flags.get("--repo") or Path.cwd()))
            result = commands.cmd_checkpoint(
                repo,
                Path.cwd(),
                positional[0],
                next_stage=flags.get("--next"),
                files=flags.get("--files"),
                envelope=flags.get("--envelope"),
            )
        elif command == "detect":
            _, flags = parse_flags(rest, command)
            repo = commands.main_repo(Path(flags.get("--repo") or Path.cwd()))
            result = commands.cmd_detect(repo)
        elif command == "profile-record":
            _, flags = parse_flags(rest, command)
            repo = commands.main_repo(Path(flags.get("--repo") or Path.cwd()))
            result = commands.cmd_profile_record(repo, Path.cwd())
        elif command == "amendment-check":
            positional, flags = parse_flags(rest, command, value_flags=("--sha256",))
            if len(positional) != 1:
                die_usage("amendment-check needs exactly one <draft>")
            result = commands.cmd_amendment_check(positional[0], flags.get("--sha256"))
        elif command == "analyze-record":
            positional, flags = parse_flags(
                rest, command, bool_flags=("--fresh-baseline",)
            )
            if len(positional) != 1:
                die_usage("analyze-record needs exactly one <envelope>")
            repo = commands.main_repo(Path(flags.get("--repo") or Path.cwd()))
            result = commands.cmd_analyze_record(
                repo,
                Path.cwd(),
                positional[0],
                fresh_baseline=bool(flags.get("--fresh-baseline")),
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
                    "--overrun",
                ),
                bool_flags=("--partial-return",),
            )
            if len(positional) != 2:
                die_usage("ledger-add needs <stage> <role>")
            repo = commands.main_repo(Path(flags.get("--repo") or Path.cwd()))
            result = commands.cmd_ledger_add(
                repo,
                Path.cwd(),
                positional[0],
                positional[1],
                started_at=iso_or_usage(flags["--started-at"], "--started-at")
                if "--started-at" in flags
                else None,
                ended_at=iso_or_usage(flags["--ended-at"], "--ended-at")
                if "--ended-at" in flags
                else None,
                in_est=int_or_usage(flags["--in-est"], "--in-est")
                if "--in-est" in flags
                else 0,
                out_est=int_or_usage(flags["--out-est"], "--out-est")
                if "--out-est" in flags
                else 0,
                reported=json_or_usage(flags["--reported"], "--reported")
                if "--reported" in flags
                else None,
                overrun=json_or_usage(flags["--overrun"], "--overrun")
                if "--overrun" in flags
                else None,
                partial_return=bool(flags.get("--partial-return")),
            )
        elif command == "issue-add":
            positional, flags = parse_flags(
                rest,
                command,
                value_flags=(
                    "--repo",
                    "--detail",
                    "--duration-ms",
                    "--cause",
                    "--commit",
                ),
                bool_flags=("--partial-return",),
            )
            if len(positional) != 3:
                die_usage("issue-add needs <kind> <stage> <role>")
            if not flags.get("--detail") or "--duration-ms" not in flags:
                die_usage("issue-add needs --detail and --duration-ms")
            try:
                duration_ms = int(flags["--duration-ms"])
            except ValueError:
                commands.die(1, "issue-add: --duration-ms needs an integer")
            repo = commands.main_repo(Path(flags.get("--repo") or Path.cwd()))
            result = commands.cmd_issue_add(
                repo,
                Path.cwd(),
                *positional,
                detail=flags["--detail"],
                duration_ms=duration_ms,
                cause=flags.get("--cause"),
                commit=flags.get("--commit"),
                partial_return=bool(flags.get("--partial-return")),
            )
        elif command == "budget":
            positional, flags = parse_flags(rest, command)
            if len(positional) != 1:
                die_usage("budget needs exactly one <role>")
            result = commands.cmd_budget(positional[0])
        elif command == "improvements":
            positional, flags = parse_flags(
                rest, command, value_flags=("--repo", "--from", "--run")
            )
            if positional[:1] == ["claim"]:
                if len(positional) != 2:
                    die_usage("improvements claim needs exactly one <name>")
                repo = commands.main_repo(Path(flags.get("--repo") or Path.cwd()))
                result = commands.cmd_improvements_claim(repo, positional[1])
            elif positional == ["add"]:
                if not flags.get("--from") or not flags.get("--run"):
                    die_usage("improvements add needs --from <file> --run <branch>")
                repo = commands.main_repo(Path(flags.get("--repo") or Path.cwd()))
                result = commands.cmd_improvements_add(
                    repo, flags["--from"], flags["--run"]
                )
            elif not positional:
                result = commands.cmd_improvements()
            else:
                die_usage("improvements supports only: improvements [claim <name>]")
        elif command == "feedback":
            positional, flags = parse_flags(rest, command, value_flags=("--repo",))
            if len(positional) > 1:
                die_usage("feedback takes at most one <branch>")
            repo = commands.main_repo(Path(flags.get("--repo") or Path.cwd()))
            result = commands.cmd_feedback(repo, positional[0] if positional else None)
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
                rest,
                command,
                value_flags=("--repo", "--stage", "--question"),
                bool_flags=("--auto", "--cruise-override"),
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
                cruise_override=bool(flags.get("--cruise-override")),
                question=flags.get("--question"),
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
        elif command == "prune":
            _, flags = parse_flags(rest, command, bool_flags=("--dry-run", "--delete"))
            if flags.get("--dry-run") and flags.get("--delete"):
                die_usage("prune takes --dry-run or --delete, not both")
            result = commands.cmd_prune(delete=bool(flags.get("--delete")))
        elif command == "mode":
            result = commands.cmd_mode(rest)
        elif command == "resume":
            # mode flags keep argv order (last wins per pair), so they bypass parse_flags
            mode_flags = [f for f in rest if f in MODE_FLAGS]
            positional, flags = parse_flags(
                [f for f in rest if f not in MODE_FLAGS], command
            )
            if len(positional) != 1:
                die_usage("resume needs exactly one <run>")
            repo = commands.main_repo(Path(flags.get("--repo") or Path.cwd()))
            result = commands.cmd_resume(repo, positional[0], mode_flags=mode_flags)
        elif command == "rebind":
            positional, flags = parse_flags(
                rest, command, value_flags=("--repo", "--worktree")
            )
            if len(positional) != 1 or not flags.get("--worktree"):
                die_usage("rebind needs <run> --worktree <path>")
            repo = commands.main_repo(Path(flags.get("--repo") or Path.cwd()))
            result = commands.cmd_rebind(
                repo, Path.cwd(), positional[0], flags["--worktree"]
            )
        elif command == "verify":
            _, flags = parse_flags(
                rest,
                command,
                value_flags=("--repo", "--commands"),
                bool_flags=("--pass", "--fail"),
            )
            if bool(flags.get("--pass")) == bool(flags.get("--fail")):
                die_usage("verify needs exactly one of --pass or --fail")
            payload = (
                json_or_usage(flags["--commands"], "--commands")
                if "--commands" in flags
                else []
            )
            if (
                not isinstance(payload, list)
                or not payload
                or not all(isinstance(command, dict) for command in payload)
            ):
                die_usage("--commands needs a JSON list of {command, status} objects")
            repo = commands.main_repo(Path(flags.get("--repo") or Path.cwd()))
            result = commands.cmd_verify(
                repo,
                Path.cwd(),
                passed=bool(flags.get("--pass")),
                commands_payload=[(c.get("command"), c.get("status")) for c in payload],
            )
        elif command == "lock":
            sub = rest[:1]
            if sub != ["take"]:
                die_usage("lock supports only: lock take <run> [--force]")
            positional, flags = parse_flags(rest[1:], command, bool_flags=("--force",))
            if len(positional) != 1:
                die_usage("lock take needs exactly one <run>")
            repo = commands.main_repo(Path(flags.get("--repo") or Path.cwd()))
            result = commands.cmd_lock_take(
                repo, positional[0], force=bool(flags.get("--force"))
            )
        elif command == "decisions-add":
            positional, flags = parse_flags(
                rest,
                command,
                value_flags=("--repo", "--kind"),
                bool_flags=("--cruise-override",),
            )
            if len(positional) != 3:
                die_usage("decisions-add needs <stage> <qid> <answer>")
            repo = commands.main_repo(Path(flags.get("--repo") or Path.cwd()))
            result = commands.cmd_decisions_add(
                repo,
                Path.cwd(),
                *positional,
                kind=flags.get("--kind") or "answer",
                cruise_override=bool(flags.get("--cruise-override")),
            )
        elif command == "adopt":
            positional, flags = parse_flags(
                rest, command, value_flags=("--stage",), bool_flags=("--dry-run",)
            )
            if len(positional) != 1:
                die_usage("adopt needs exactly one <src>")
            if flags.get("--stage") not in (None, *state.ADOPT_STAGES):
                die_usage(
                    f"adopt: --stage must be one of {', '.join(state.ADOPT_STAGES)}"
                )
            repo = commands.main_repo(Path.cwd())
            if flags.get("--dry-run"):
                result = adopt.inspect(repo, positional[0], adopt.default_base(repo))
                if result["refusal"]:
                    emit(result)
                    raise SystemExit(1)
            else:
                result = adopt.write(repo, positional[0], flags.get("--stage"))
        else:
            die_usage(f"unknown command '{command}'")
        emit(result)
        if command == "feedback" and result["gaps"]:
            raise SystemExit(1)
        if isinstance(result, dict) and result.get("commit_error"):
            # FR-011: the state write landed, the commit did not — the JSON
            # above names it and the exit code says the command failed
            raise SystemExit(1)
    except models.ModelConfigError as e:
        print(
            f"factory: {e}\nFix the file or delete it to fall back to the next layer.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    except commands.state.StateError as e:  # a refused write names its reason
        print(f"factory: {e}", file=sys.stderr)
        raise SystemExit(1)
    except CLIError as e:
        print(f"factory: {e}", file=sys.stderr)
        raise SystemExit(e.code)
