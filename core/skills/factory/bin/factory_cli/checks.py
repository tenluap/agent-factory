"""Transition gates and role-output shape checks (FR-006, FR-007; R5, R6).

The gate table is the one source of refusal reasons for illegal stage
transitions; refusals name the missing record. The permitting decision of a
gate becomes that transition's `approved`/`gate-override` history event.
The shape checker validates a role output's final fenced json block against
the envelope (protocol.md), reviewer report and judge verdict (findings.md)
shapes; the references' own fenced examples are the fixtures.
"""

import json
import re

from factory_cli import state

ENVELOPE_STATUSES = ("done", "needs_input", "partial", "failed")
VERDICTS = ("pass", "fix")
# ADR 0016: automatic repair cycles per run (FR-014)
REPAIR_CYCLE_CAP = 2
# the six self-report causes; `unreported` is detected-only (state.py) and
# never valid in a role's own overrun report
SELF_REPORT_CAUSES = tuple(c for c in state.OVERRUN_CAUSES if c != "unreported")


def _str(value):
    return isinstance(value, str) and bool(value)


def _int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def block_problems(block, shape):
    """Every violation of one role-output shape as {"location", "reason"}."""
    problems = []

    def bad(location, reason):
        problems.append({"location": location, "reason": reason})

    if not isinstance(block, dict):
        return [{"location": "", "reason": f"the {shape} block is not a JSON object"}]

    if shape == "envelope":
        status = block.get("status")
        if status not in ENVELOPE_STATUSES:
            bad(
                "status",
                f"{status!r} is off-vocabulary; expected one of: {', '.join(ENVELOPE_STATUSES)}",
            )
        for field in ("stage", "summary"):
            if not _str(block.get(field)):
                bad(field, "missing or empty string")
        files = block.get("files")
        if not isinstance(files, list) or not all(isinstance(f, str) for f in files):
            bad("files", "must be a list of file paths")
        if status == "needs_input" and not isinstance(block.get("questions"), list):
            bad(
                "questions",
                "a needs_input envelope carries its whole frontier of questions",
            )
        if status == "failed" and not _str(block.get("error")):
            bad("error", "a failed envelope carries its error")
        overrun = block.get("overrun")
        if overrun is not None:
            if not isinstance(overrun, dict):
                bad("overrun", "must be an object with cause and detail")
            else:
                if overrun.get("cause") not in SELF_REPORT_CAUSES:
                    bad(
                        "overrun.cause",
                        f"{overrun.get('cause')!r} is off-vocabulary; expected "
                        f"one of: {', '.join(SELF_REPORT_CAUSES)}",
                    )
                if not _str(overrun.get("detail")):
                    bad("overrun.detail", "a non-empty detail is required")
        return problems

    if shape == "reviewer":
        for field in ("reviewer", "summary"):
            if not _str(block.get(field)):
                bad(field, "missing or empty string")
        if not _int(block.get("round")):
            bad("round", "must be an integer")
        findings = block.get("findings")
        if not isinstance(findings, list):
            bad("findings", "must be a list")
            return problems
        for i, finding in enumerate(findings):
            if not isinstance(finding, dict):
                bad(f"findings[{i}]", "not an object")
                continue
            for field, kind in (
                ("id", _str),
                ("severity", _str),
                ("blocking", lambda v: isinstance(v, bool)),
                ("file", _str),
                ("line", _int),
                ("summary", _str),
                ("evidence", _str),
                ("fix", _str),
            ):
                if not kind(finding.get(field)):
                    bad(f"findings[{i}].{field}", "missing or of the wrong type")
        return problems

    if shape == "verdict":
        if not _int(block.get("round")):
            bad("round", "must be an integer")
        if block.get("verdict") not in VERDICTS:
            bad(
                "verdict",
                f"{block.get('verdict')!r} is off-vocabulary; expected one of: {', '.join(VERDICTS)}",
            )
        for field in ("confirmed_blocking", "advisory", "rejected"):
            if not isinstance(block.get(field), list):
                bad(field, "must be a list")
        for i, entry in enumerate(block.get("confirmed_blocking") or []):
            _confirmed(bad, f"confirmed_blocking[{i}]", entry)
        for i, entry in enumerate(block.get("advisory") or []):
            _advisory(bad, f"advisory[{i}]", entry)
        for i, entry in enumerate(block.get("rejected") or []):
            if not isinstance(entry, dict):
                bad(f"rejected[{i}]", "not an object")
                continue
            for field in ("id", "reason"):
                if not _str(entry.get(field)):
                    bad(f"rejected[{i}].{field}", "missing or empty string")
        escalate = block.get("escalate")
        if escalate is not None and not (
            _str(escalate.get("reason")) if isinstance(escalate, dict) else False
        ):
            bad("escalate", "carries a reason when present")
        return problems

    bad("", f"unknown shape '{shape}'")
    return problems


def _finding_like(bad, location, entry):
    if not isinstance(entry, dict):
        bad(location, "not an object")
        return
    for field in ("severity", "file", "summary", "evidence", "fix"):
        if not _str(entry.get(field)):
            bad(f"{location}.{field}", "missing or empty string")
    if not _int(entry.get("line")):
        bad(f"{location}.line", "must be an integer")
    sources = entry.get("sources")
    if not (isinstance(sources, list) and all(isinstance(s, str) for s in sources)):
        bad(f"{location}.sources", "must be a list of finding ids")


def _confirmed(bad, location, entry):
    """A confirmed blocking finding carries the full evidence (findings.md)."""
    _finding_like(bad, location, entry)


def _advisory(bad, location, entry):
    """An advisory entry keeps sources and the fix but no evidence of its own."""
    if not isinstance(entry, dict):
        bad(location, "not an object")
        return
    for field in ("severity", "file", "summary", "fix"):
        if not _str(entry.get(field)):
            bad(f"{location}.{field}", "missing or empty string")
    if not _int(entry.get("line")):
        bad(f"{location}.line", "must be an integer")
    sources = entry.get("sources")
    if not (isinstance(sources, list) and all(isinstance(s, str) for s in sources)):
        bad(f"{location}.sources", "must be a list of finding ids")


def detect_shape(block):
    """Which role-output shape this block claims to be, or None."""
    if not isinstance(block, dict):
        return None
    if "verdict" in block and "round" in block:
        return "verdict"
    if "reviewer" in block and "findings" in block:
        return "reviewer"
    if "status" in block and "stage" in block:
        return "envelope"
    return None


def extract_block(text):
    """A role output's final fenced json block: (block, None) or (None, reason)."""
    matches = list(re.finditer(r"```json\n(.*?)```", text, re.S))
    if not matches:
        return None, "no fenced json block found"
    try:
        return json.loads(matches[-1].group(1)), None
    except ValueError as e:
        return None, f"the final fenced json block does not parse: {e}"


def latest_verify(state_dict):
    """The latest verify history record; the latest one decides (R3)."""
    for entry in reversed(state_dict.get("history") or []):
        if isinstance(entry, dict) and entry.get("event") in (
            "verify-pass",
            "verify-fail",
        ):
            return entry
    return None


def verify_commands_passed(commands):
    """Require passing evidence for every command in a verification record."""
    return isinstance(commands, list) and bool(commands) and all(
        isinstance(command, dict)
        and _str(command.get("command"))
        and (
            command.get("status") == "pass"
            or (_int(command.get("status")) and command["status"] == 0)
        )
        for command in commands
    )


def _decisions(state_dict, stage, kinds):
    return [
        d
        for d in state_dict.get("decisions") or []
        if isinstance(d, dict) and d.get("stage") == stage and d.get("kind") in kinds
    ]


def analyze_baseline(analyze):
    """The acceptance baseline: the stored one, else the derived `result`, else None (FR-010).

    The derivation is only safe when `reports` holds exactly one entry and the
    result names it; report markdown is never read for counts.
    """
    stored = analyze.get("baseline")
    if isinstance(stored, dict) and not state.analyze_record_problems(stored):
        return stored
    result = analyze.get("result")
    reports = analyze.get("reports") or []
    if (
        isinstance(result, dict)
        and not state.analyze_record_problems(result)
        and len(reports) == 1
        and result.get("report") == reports[0]
    ):
        return result
    return None


def _unanswered_user_questions(relay):
    """Ids of relay questions flagged `requires_user` that carry no answer."""
    if not isinstance(relay, dict):
        return []
    answered = set()
    asked = []
    for one_round in relay.get("rounds") or []:
        answered.update((one_round.get("answers") or {}).keys())
        for question in one_round.get("questions") or []:
            if isinstance(question, dict) and question.get("requires_user") is True:
                asked.append(question.get("id"))
    return [qid for qid in asked if qid not in answered]


def _target(label, baseline, latest):
    """One integer half-rule target: None when met, else the named unmet reason."""
    if baseline == 0:
        if latest == 0:
            return None
        return f"{label} {latest} (baseline 0, must stay 0)"
    if 2 * latest < baseline:
        return None
    return f"{label} {latest} (baseline {baseline}, must be < {baseline / 2:g})"


def unmet_targets(baseline, latest):
    """Every acceptance target the latest counts miss, each named with its counts (FR-004, FR-005)."""
    if not isinstance(latest, dict) or state.analyze_record_problems(latest):
        return ["analyze.result is missing or not a valid analysis record"]
    problems = []
    for severity in ("critical", "high"):
        if latest[severity]:
            problems.append(f"{severity.upper()} {latest[severity]} (must be 0)")
    total_baseline = sum(baseline[k] for k in state.ANALYZE_COUNTS)
    total_latest = sum(latest[k] for k in state.ANALYZE_COUNTS)
    for reason in (
        _target("total", total_baseline, total_latest),
        _target("LOW", baseline["low"], latest["low"]),
    ):
        if reason:
            problems.append(reason)
    return problems


def _approver_permits(state_dict):
    """Approver records that may permit `pr`. A record carrying cruise_override
    never does: cruise may not publish, only the user's own Approve (FR-015, FR-016)."""
    return [
        d
        for d in _decisions(state_dict, "approver", ("approved", "gate-override"))
        if d.get("cruise_override") is not True
    ]


def gate_violation(state_dict, into):
    """None when the transition into `into` may record; else the missing record."""
    if into == "review":
        latest = latest_verify(state_dict)
        if latest is None:
            return (
                "no verify record in history: run `factory verify --pass|--fail` "
                "after re-running build and test"
            )
        if latest.get("event") != "verify-pass":
            return (
                f"the latest verify record is '{latest.get('event')}' "
                f"({latest.get('at')}); a passing latest verify record is required"
            )
        if not verify_commands_passed(latest.get("commands")):
            return "the latest verify-pass record lacks passing results for every command"
        return None
    if into == "implement":
        if _decisions(state_dict, "analyze", ("gate-override",)):
            return None
        analyze = state_dict.get("analyze") or {}
        if not analyze.get("reports"):
            return (
                "no analyze report records the analyze loop's outcome "
                "(analyze.reports is empty)"
            )
        problems = []
        if analyze.get("pending_clarify"):
            problems.append(
                f"analyze.pending_clarify holds {len(analyze['pending_clarify'])} "
                "unanswered finding(s)"
            )
        for qid in _unanswered_user_questions(state_dict.get("relay")):
            problems.append(f"relay question {qid} requires the user's answer")
        baseline = analyze_baseline(analyze)
        if baseline is None:
            problems.append(
                "no trustworthy baseline: re-run analysis as a fresh baseline, "
                "record a gate-override, or abort"
            )
        else:
            problems.extend(unmet_targets(baseline, analyze.get("result")))
        return "; ".join(problems) or None
    if into == "remediate":
        analyze = state_dict.get("analyze") or {}
        loops = analyze.get("loops") or 0
        if loops < REPAIR_CYCLE_CAP:
            return None
        result_at = (analyze.get("result") or {}).get("at") or ""
        guided = [
            d
            for d in _decisions(state_dict, "analyze", ("answer",))
            if not d.get("auto") and (d.get("at") or "") > result_at
        ]
        if guided:
            return None
        return (
            f"analyze.loops is {loops}: the repair cycles are exhausted; record a "
            "guided pass after the latest analysis (`decisions-add analyze <qid> "
            "'<guidance>'`), a gate-override, or abort"
        )
    if into == "pr":
        if _approver_permits(state_dict):
            return None
        return (
            "no approved decision recorded at approver "
            "(`factory decisions-add approver <qid> '<answer>' --kind approved`)"
        )
    return None  # stages without a gate


def permitting_decision(state_dict, into):
    """The decision record permitting this gate, or None (event stays `complete`)."""
    if into == "pr":
        candidates = _approver_permits(state_dict)
    elif into == "implement":
        candidates = _decisions(state_dict, "analyze", ("gate-override",))
    else:
        return None
    return max(candidates, key=lambda d: d.get("at") or "", default=None)


_COMMIT_SUBJECT = {
    "implement": re.compile(r"^factory\(implement\): \S"),
    "fix": re.compile(r"^factory\(fix\): \S"),
}
# Exactly the forms engineering.md defines: ENG-2 (Red), ENG-6 (New), the fixer's Adjacent.
_COMMIT_LINES = {
    "Red": re.compile(
        r"^Red: (\S.* failed as expected|not applicable - \S.* already covers this)$"
    ),
    "New": re.compile(r"^New: \S.* - \S.*$"),
    "Adjacent": re.compile(r"^Adjacent: \S.* - \S.*$"),
}
_COMMIT_KEYED = re.compile(r"^[\s>*-]*(red|new|adjacent)\s*:", re.IGNORECASE)


def commit_message_problems(message, kind=None):
    """Every way a role's commit message misses the grammar, as readable strings.

    `kind` pins the subject to `implement` or `fix`; None accepts either. Red,
    New and Adjacent lines must match their one form exactly, at column 0.
    """
    lines = message.splitlines()
    subject = lines[0] if lines else ""
    kinds = [kind] if kind else list(_COMMIT_SUBJECT)
    problems = []
    if not any(_COMMIT_SUBJECT[k].match(subject) for k in kinds):
        wanted = " or ".join(f"factory({k}): <...>" for k in kinds)
        problems.append(f"subject {subject!r} must read {wanted}")
    for number, line in enumerate(lines[1:], start=2):
        keyed = _COMMIT_KEYED.match(line)
        if not keyed:
            continue
        word = keyed.group(1).capitalize()
        if not _COMMIT_LINES[word].match(line):
            problems.append(f"line {number} is not a valid {word}: line: {line!r}")
    return problems
