"""Replay runs 005 and 006 through the defect detectors: SC-002's evidence.

Every defect listed in ``fixtures/defects.json`` under ``core-defects`` must be
reported for its run (nothing falsely passes); every defect reported beyond the
core must appear under ``extras`` with a written reason.

Run directly: ``python3 tools/tests/replay.py`` (exit non-zero on any gap).
"""

import json
import sys
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"
MANIFEST = FIXTURES / "defects.json"

# FR-019: one vocabulary source — parse_iso and the closed vocabularies come
# from the shared state module the CLI validates with.
CORE_BIN = Path(__file__).resolve().parents[2] / "core" / "skills" / "factory" / "bin"
if str(CORE_BIN) not in sys.path:
    sys.path.insert(0, str(CORE_BIN))

from factory_cli.state import HISTORY_EVENTS, TIMELINE_KINDS, parse_iso  # noqa: E402

AGENT_STAGES = (
    "implement",
    "review",
    "fix",
)  # stages whose spawns belong in the ledger


def _backwards(entries):
    times = [parse_iso(e.get("at")) for e in entries if isinstance(e, dict)]
    times = [t for t in times if t]
    return any(b < a for a, b in zip(times, times[1:]))


def _rounded(entries):
    seconds = [parse_iso(e.get("at")).second for e in entries if parse_iso(e.get("at"))]
    return seconds.count(0) >= 2 and any(s != 0 for s in seconds)


def _totals_exceed_wall(state):
    start, end = parse_iso(state.get("started_at")), parse_iso(state.get("ended_at"))
    if not start or not end:
        return False
    wall = (end - start).total_seconds() * 1000
    timeline = [e for e in state.get("timeline") or [] if isinstance(e, dict)]
    ledger = [e for e in state.get("ledger") or [] if isinstance(e, dict)]
    human = sum(e.get("latency_ms") or 0 for e in timeline)
    agent = sum(e.get("duration_ms") or 0 for e in ledger)
    return human + agent > wall


def _off_vocabulary_events(state):
    return any(
        e.get("event") not in HISTORY_EVENTS
        for e in state.get("history") or []
        if isinstance(e, dict)
    )


def _off_vocabulary_kinds(state):
    return any(
        e.get("kind") not in TIMELINE_KINDS
        for e in state.get("timeline") or []
        if isinstance(e, dict)
    )


def _missing_implement_verify(state):
    if state.get("status") != "pr-open":
        return False
    return not any(
        e.get("stage") in ("implement", "verify")
        for e in state.get("history") or []
        if isinstance(e, dict)
    )


def _ledger_incomplete(state):
    ledger = [e for e in state.get("ledger") or [] if isinstance(e, dict)]
    if any(e.get("duration_ms") == 0 for e in ledger):
        return True
    stages = {e.get("stage") for e in state.get("history") or [] if isinstance(e, dict)}
    if any(stage in stages for stage in AGENT_STAGES) and not (
        stages & {e.get("stage") for e in ledger}
    ):
        return True
    roles = {e.get("role") for e in ledger}
    return len(roles) <= 1 and bool(ledger)


def _decision_audit_lost(state):
    if state.get("decisions"):
        return False
    relay = state.get("relay")
    rounds = []
    if isinstance(relay, dict):
        rounds = relay.get("rounds") or ([relay] if relay.get("questions") else [])
    answered = any(r.get("answers") for r in rounds if isinstance(r, dict))
    # relay already cleared at a checkpoint, or rounds with answers, but no decisions list
    return relay is None or answered


DETECTORS = {
    "history-timestamps-backwards": lambda s: _backwards(s.get("history") or []),
    "rounded-timestamps": lambda s: _rounded(s.get("history") or []),
    "totals-exceed-wall-clock": _totals_exceed_wall,
    "history-events-off-vocabulary": _off_vocabulary_events,
    "timeline-kind-off-vocabulary": _off_vocabulary_kinds,
    "history-missing-implement-verify": _missing_implement_verify,
    "ledger-incomplete-spawns": _ledger_incomplete,
    "decision-audit-lost": _decision_audit_lost,
}


def replay(state):
    """Defect ids reported for one run state."""
    return sorted(name for name, detect in DETECTORS.items() if detect(state))


def check(manifest_path=MANIFEST):
    """Compare each run's reported defects against its manifest slice.

    Returns (ok, report lines). A missing core defect is a false pass; a
    reported defect absent from core and extras is unexpected.
    """
    manifest = json.loads(Path(manifest_path).read_text())
    lines, ok = [], True
    for name, slice_ in manifest["runs"].items():
        state = json.loads((FIXTURES / slice_["fixture"]).read_text())
        reported = replay(state)
        core, extras = slice_["core-defects"], set(slice_["extras"])
        for defect in core:
            if defect not in reported:
                ok = False
                lines.append(f"FAIL {name}: core defect not reported: {defect}")
        for defect in reported:
            if defect not in core and defect not in extras:
                ok = False
                lines.append(
                    f"FAIL {name}: unexpected defect (add a reason or fix): {defect}"
                )
        lines.append(f"{name}: reported {', '.join(reported)}")
    return ok, lines


def main():
    ok, lines = check()
    print("\n".join(lines))
    if not ok:
        sys.exit(1)
    print("replay: every §3 core defect reported, nothing falsely passing")


if __name__ == "__main__":
    main()
