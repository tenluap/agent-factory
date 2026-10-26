"""Transition gates and role-output shape checks (FR-006, FR-007; R5, R6).

The gate table is the one source of refusal reasons for illegal stage
transitions; refusals name the missing record. The permitting decision of a
gate becomes that transition's `approved`/`gate-override` history event.
"""

from factory_cli import state


def latest_verify(state_dict):
    """The latest verify history record; the latest one decides (R3)."""
    for entry in reversed(state_dict.get("history") or []):
        if isinstance(entry, dict) and entry.get("event") in (
            "verify-pass",
            "verify-fail",
        ):
            return entry
    return None


def _decisions(state_dict, stage, kinds):
    return [
        d
        for d in state_dict.get("decisions") or []
        if isinstance(d, dict) and d.get("stage") == stage and d.get("kind") in kinds
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
        if analyze.get("pending_clarify"):
            return (
                f"analyze.pending_clarify holds {len(analyze['pending_clarify'])} "
                "unanswered finding(s)"
            )
        return None
    if into == "pr":
        if _decisions(state_dict, "approver", ("approved", "gate-override")):
            return None
        return (
            "no approved decision recorded at approver "
            "(`factory decisions-add approver <qid> '<answer>' --kind approved`)"
        )
    return None  # stages without a gate


def permitting_decision(state_dict, into):
    """The decision record permitting this gate, or None (event stays `complete`)."""
    if into == "pr":
        candidates = _decisions(state_dict, "approver", ("approved", "gate-override"))
    elif into == "implement":
        candidates = _decisions(state_dict, "analyze", ("gate-override",))
    else:
        return None
    return max(candidates, key=lambda d: d.get("at") or "", default=None)
