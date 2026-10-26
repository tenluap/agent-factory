"""Interval-union effort accounting (FR-009, R7).

Agent time is the union of ledger spawn intervals, human time the union of
recorded user-wait intervals; overhead is the non-negative residual. No
report sums parallel durations, so human + agent never exceeds wall clock
whenever waits and spawns do not overlap (which the flow guarantees).
"""

from datetime import timedelta
import json

from factory_cli import state


def _intervals_from(entries, start_key, end_key, duration_key):
    """Measurable (start, end) pairs; legacy entries fall back to at+duration."""
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        start, end = (
            state.parse_iso(entry.get(start_key)),
            state.parse_iso(entry.get(end_key)),
        )
        if start and end:
            yield start, end
            continue
        start = state.parse_iso(entry.get("at"))
        duration = entry.get(duration_key)
        if start and isinstance(duration, (int, float)):
            yield start, start + timedelta(milliseconds=max(duration, 0))


def _union_ms(intervals):
    """Total covered time, merging overlaps; zero-length intervals count nothing."""
    ordered = sorted((s, e) for s, e in intervals if e > s)
    covered, current = 0, None
    for start, end in ordered:
        if current and start <= current[1]:
            current = (current[0], max(current[1], end))
        else:
            if current:
                covered += (current[1] - current[0]).total_seconds() * 1000
            current = (start, end)
    if current:
        covered += (current[1] - current[0]).total_seconds() * 1000
    return int(covered)


def compute(state_dict):
    started = state.parse_iso(state_dict.get("started_at"))
    ended = state.parse_iso(state_dict.get("ended_at")) or started
    wall_ms = int((ended - started).total_seconds() * 1000) if started else 0
    timeline = [e for e in state_dict.get("timeline") or [] if isinstance(e, dict)]
    ledger = [e for e in state_dict.get("ledger") or [] if isinstance(e, dict)]
    human_ms = _union_ms(_intervals_from(timeline, "at", "answered_at", "latency_ms"))
    agent_ms = _union_ms(
        _intervals_from(ledger, "started_at", "ended_at", "duration_ms")
    )
    return {
        "bounded": bool(started),
        "wall_ms": wall_ms,
        "human_ms": human_ms,
        "agent_ms": agent_ms,
        "overhead_ms": max(wall_ms - human_ms - agent_ms, 0),
        "waits": len(timeline),
        "open_waits": sum(1 for e in timeline if not e.get("answered_at")),
        "spawns": len(ledger),
        **usage_totals(ledger),
    }


def fmt_dur(ms):
    s = max(int(ms or 0), 0) // 1000
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    if h:
        return f"{h}h {m}m"
    if m:
        return f"{m}m {s}s" if s else f"{m}m"
    return f"{s}s"


def usage_totals(ledger):
    """FR-010, R17: word-count estimates summed under their own labels;
    harness-reported usage kept verbatim, never merged into one number."""
    entries = [e for e in ledger if isinstance(e, dict)]
    return {
        "in_est": sum(e.get("in_est") or 0 for e in entries),
        "out_est": sum(e.get("out_est") or 0 for e in entries),
        "reported": [e["reported"] for e in entries if e.get("reported") is not None],
    }


def fmt_tokens(n):
    return f"{n // 1000}k" if n >= 1000 else str(n)


def sentence(t):
    """The one totals line; None for a run that never recorded its start."""
    if not t.get("bounded"):
        return None
    line = (
        f"Run took {fmt_dur(t['wall_ms'])}: {fmt_dur(t['human_ms'])} you ({t['waits']} waits), "
        f"{fmt_dur(t['agent_ms'])} agents ({t['spawns']} spawns), {fmt_dur(t['overhead_ms'])} overhead."
    )
    u = t.get("in_est"), t.get("out_est"), t.get("reported")
    if u[0] or u[1]:
        line += f" Usage: {fmt_tokens(u[0])} in/{fmt_tokens(u[1])} out estimated."
    if u[2]:
        line += f" harness-reported: {json.dumps(u[2])}."
    return line
