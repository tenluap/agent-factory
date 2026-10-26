"""State read, validate and atomic write: the single writer's core (FR-001..FR-004, FR-022).

Readers accept versions 1-4 including legacy relay shapes and never rewrite
what they read. Writers validate first, refuse to rewrite the append-only
`decisions` list, upgrade the run to the current version, and replace the
file atomically (temp file + `os.replace` in the same directory).
"""

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from factory_cli import lock

VERSION = 4
STATUSES = ("running", "waiting_user", "paused", "halted", "aborted", "pr-open")
STAGES = (
    "brainstorm",
    "grill",
    "worktree",
    "specify",
    "clarify",
    "grill-with-docs",
    "plan",
    "tasks",
    "analyze",
    "remediate",
    "implement",
    "verify",
    "review",
    "fix",
    "approver",
    "pr",
)
TIMELINE_KINDS = ("questions", "notice", "approver", "halt")
# Closed vocabulary (FR-003); every event has exactly one writer command.
HISTORY_EVENTS = (
    "complete",
    "verify-pass",
    "verify-fail",
    "approved",
    "gate-override",
    "aborted",
    "pr-open",
    "resumed",
)
DECISION_KINDS = ("answer", "approved", "gate-override")
COMMAND_STAGES = STAGES[
    STAGES.index("implement") :
]  # a run here and later carries commands
REQUIRED_FIELDS = (
    "version",
    "started_at",
    "harness",
    "feature",
    "repo",
    "default_branch",
    "base",
    "branch",
    "spec_dir",
    "status",
    "stage",
    "mode",
)


class StateError(Exception):
    """A refused write, with the reason."""


def parse_iso(value):
    """Parse an ISO-8601 UTC timestamp; None when missing or malformed."""
    if not isinstance(value, str) or not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def iso(dt):
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def read_state(path):
    """Read one state file: (state, None) or (None, reason). Never writes."""
    try:
        loaded = json.loads(Path(path).read_text())
    except (OSError, ValueError) as e:
        return None, str(e)
    if isinstance(loaded, dict):
        return loaded, None
    return None, "state is not a JSON object"


def validate_state(state):
    """Every violation as {"location", "reason"}; an empty list means valid."""
    problems = []

    def bad(location, reason):
        problems.append({"location": location, "reason": reason})

    if not isinstance(state, dict):
        return [{"location": "", "reason": "state is not a JSON object"}]
    if state.get("version") not in (1, 2, 3, VERSION):
        bad(
            "version",
            f"unsupported version {state.get('version')!r}; readers accept 1-{VERSION}",
        )
    for field in REQUIRED_FIELDS:
        if state.get(field) in (None, "", {}, []):
            bad(field, "missing required field")
    for field, vocab in (("status", STATUSES), ("stage", STAGES)):
        if state.get(field) is not None and state.get(field) not in vocab:
            bad(
                field,
                f"{state.get(field)!r} is off-vocabulary; expected one of: {', '.join(vocab)}",
            )

    started = parse_iso(state.get("started_at"))
    if state.get("started_at") and not started:
        bad("started_at", "not an ISO-8601 UTC timestamp")
    ended = parse_iso(state.get("ended_at"))
    if state.get("ended_at") and not ended:
        bad("ended_at", "not an ISO-8601 UTC timestamp")
    if started and ended and ended < started:
        bad("ended_at", "ends before the run started")

    stage = state.get("stage")
    if stage in COMMAND_STAGES and not isinstance(state.get("commands"), dict):
        bad("commands", f"stage '{stage}' and later carry commands")
    if state.get("status") == "pr-open":
        if not state.get("pr_url"):
            bad("pr_url", "a pr-open run carries its URL")
        if not state.get("ended_at"):
            bad("ended_at", "a pr-open run has ended")

    decisions = _check_decisions(state, bad)
    _check_history(state, decisions, bad)
    _check_timeline(state, bad)
    _check_ledger(state, bad)
    _check_relay(state, bad)
    return problems


def _check_decisions(state, bad):
    """Well-formed decision records, non-decreasing; returns them for history cross-checks."""
    decisions = state.get("decisions")
    if decisions is None:
        return []  # pre-v4 state: accepted and upgraded on first write
    if not isinstance(decisions, list):
        bad("decisions", "not a list")
        return []
    last = None
    for i, entry in enumerate(decisions):
        if not isinstance(entry, dict):
            bad(f"decisions[{i}]", "not an object")
            continue
        for field in ("stage", "question", "answer", "auto", "at", "kind"):
            if entry.get(field) is None and field != "auto":
                bad(f"decisions[{i}].{field}", "missing required field")
        if entry.get("kind") not in DECISION_KINDS:
            bad(f"decisions[{i}].kind", f"{entry.get('kind')!r} is off-vocabulary")
        if (
            entry.get("kind") in ("approved", "gate-override")
            and entry.get("auto") is not False
        ):
            bad(f"decisions[{i}].auto", "a gate decision is never auto")
        if entry.get("stage") not in STAGES:
            bad(f"decisions[{i}].stage", f"{entry.get('stage')!r} is off-vocabulary")
        at = parse_iso(entry.get("at"))
        if entry.get("at") and not at:
            bad(f"decisions[{i}].at", "not an ISO-8601 UTC timestamp")
        if at and last and at < last:
            bad(f"decisions[{i}].at", "decisions go backwards in time")
        last = at or last
    return [e for e in decisions if isinstance(e, dict)]


def _check_history(state, decisions, bad):
    history = state.get("history")
    if history is None:
        return
    if not isinstance(history, list):
        bad("history", "not a list")
        return
    last = None
    for i, entry in enumerate(history):
        if not isinstance(entry, dict):
            bad(f"history[{i}]", "not an object")
            continue
        if entry.get("event") not in HISTORY_EVENTS:
            bad(
                f"history[{i}].event",
                f"{entry.get('event')!r} is off-vocabulary; "
                f"expected one of: {', '.join(HISTORY_EVENTS)}",
            )
        at = parse_iso(entry.get("at"))
        if entry.get("at") and not at:
            bad(f"history[{i}].at", "not an ISO-8601 UTC timestamp")
        if at and last and at < last:
            bad(f"history[{i}].at", "history timestamps go backwards")
        last = at or last
        if entry.get("event") in ("verify-pass", "verify-fail"):
            commands = entry.get("commands")
            if not (
                isinstance(commands, list)
                and commands
                and all(
                    isinstance(c, dict) and "command" in c and "status" in c
                    for c in commands
                )
            ):
                bad(
                    f"history[{i}].commands",
                    "a verify record carries its commands and exit statuses",
                )
        if entry.get("decision") is not None:
            named = [
                d
                for d in decisions
                if d.get("question") == entry.get("decision")
                and d.get("stage") == entry.get("stage")
            ]
            if not named:
                bad(
                    f"history[{i}].decision",
                    f"no decision entry names '{entry.get('decision')}' "
                    f"at stage '{entry.get('stage')}'",
                )


def _check_timeline(state, bad):
    timeline = state.get("timeline")
    if timeline is None:
        return
    if not isinstance(timeline, list):
        bad("timeline", "not a list")
        return
    last = None
    for i, entry in enumerate(timeline):
        if not isinstance(entry, dict):
            bad(f"timeline[{i}]", "not an object")
            continue
        if entry.get("kind") not in TIMELINE_KINDS:
            bad(
                f"timeline[{i}].kind",
                f"{entry.get('kind')!r} is off-vocabulary; "
                f"expected one of: {', '.join(TIMELINE_KINDS)}",
            )
        at = parse_iso(entry.get("at"))
        if entry.get("at") and not at:
            bad(f"timeline[{i}].at", "not an ISO-8601 UTC timestamp")
        if at and last and at < last:
            bad(f"timeline[{i}].at", "timeline timestamps go backwards")
        last = at or last
        latency = entry.get("latency_ms")
        if latency is not None and (
            not isinstance(latency, (int, float)) or latency < 0
        ):
            bad(f"timeline[{i}].latency_ms", "negative or non-numeric latency")


def _check_ledger(state, bad):
    ledger = state.get("ledger")
    if ledger is None:
        return
    if not isinstance(ledger, list):
        bad("ledger", "not a list")
        return
    last = None
    for i, entry in enumerate(ledger):
        if not isinstance(entry, dict):
            bad(f"ledger[{i}]", "not an object")
            continue
        at = parse_iso(entry.get("at"))
        if entry.get("at") and not at:
            bad(f"ledger[{i}].at", "not an ISO-8601 UTC timestamp")
        if at and last and at < last:
            bad(f"ledger[{i}].at", "ledger timestamps go backwards")
        last = at or last
        duration = entry.get("duration_ms")
        if duration is not None and (
            not isinstance(duration, (int, float)) or duration < 0
        ):
            bad(f"ledger[{i}].duration_ms", "negative or non-numeric duration")
        start, end = (
            parse_iso(entry.get("started_at")),
            parse_iso(entry.get("ended_at")),
        )
        if start and end and end < start:
            bad(f"ledger[{i}].ended_at", "spawn ends before it started")


def _check_relay(state, bad):
    relay = state.get("relay")
    if relay is None:
        return
    if not isinstance(relay, dict):
        bad("relay", "not an object")
        return
    rounds = relay.get("rounds")
    if rounds is None and relay.get("questions") is not None:  # version 1: one batch
        _check_round(bad, "relay", relay)
        return
    if rounds is None:
        return
    if not isinstance(rounds, list):
        bad("relay.rounds", "not a list")
        return
    for r, one_round in enumerate(rounds):
        _check_round(bad, f"relay.rounds[{r}]", one_round)


def _check_round(bad, location, one_round):
    if not isinstance(one_round, dict):
        bad(location, "not an object")
        return
    questions = one_round.get("questions")
    answers = one_round.get("answers") or {}
    ids = {q.get("id") for q in questions or [] if isinstance(q, dict) and q.get("id")}
    for key in answers:
        if ids and key not in ids:
            bad(
                f"{location}.answers.{key}",
                "no question with this id in the same round",
            )


def upgrade(state):
    """The first-write upgrade to the current version: version 4, a decisions
    list, and derived spawn intervals on ledger entries that lack them."""
    state = dict(state)
    state["version"] = VERSION
    state.setdefault("decisions", [])
    state["ledger"] = [_with_interval(entry) for entry in state.get("ledger") or []]
    return state


def _with_interval(entry):
    if not isinstance(entry, dict) or (
        entry.get("started_at") and entry.get("ended_at")
    ):
        return entry
    entry = dict(entry)
    start = parse_iso(entry.get("started_at")) or parse_iso(entry.get("at"))
    end = parse_iso(entry.get("ended_at"))
    if start and not end:
        duration = entry.get("duration_ms")
        end = start + timedelta(milliseconds=max(duration or 0, 0))
    if start:
        entry["started_at"] = iso(start)
    if end:
        entry["ended_at"] = iso(end)
    return entry


def write_state(path, state, mutate=None):
    """Validate, guard the append-only decisions, upgrade and replace atomically.

    With `mutate`, the lock is taken first and the mutation is re-applied to
    the state freshly read under it, so a read-modify-write never drops a
    change that landed while the caller worked; without it, `state` is the
    full record to write. Returns the upgraded state actually written.
    Raises StateError, leaving the file untouched, on any violation or on a
    decisions rewrite.
    """
    path = Path(path)
    lock.acquire(path, harness=state.get("harness") or "unknown")
    try:
        if mutate is not None:
            current, error = read_state(path)
            if error or not isinstance(current, dict):
                raise StateError(
                    f"cannot re-read {path} under the lock: "
                    f"{error or 'not a JSON object'}"
                )
            state = mutate(current)
        violations = validate_state(state)
        if violations:
            detail = "; ".join(f"{v['location']}: {v['reason']}" for v in violations)
            raise StateError(f"refusing to write invalid state ({detail})")
        if path.exists():
            old, error = read_state(path)
            if not error and isinstance(old.get("decisions"), list):
                new = state.get("decisions") or []
                recorded = old["decisions"]
                if recorded != new[: len(recorded)]:
                    raise StateError(
                        "refusing to rewrite the append-only decisions list "
                        f"({len(recorded)} recorded entries must persist unchanged)"
                    )
        state = upgrade(state)
        text = json.dumps(state, indent=2, ensure_ascii=False) + "\n"
        tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
        try:
            tmp.write_text(text)
            os.replace(tmp, path)
        except BaseException:
            tmp.unlink(missing_ok=True)
            raise
    finally:
        lock.release(path)
    return state
