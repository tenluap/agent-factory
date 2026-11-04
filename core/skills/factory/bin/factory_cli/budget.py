"""Time budget resolution and deadline derivation (FR-001, FR-007).

One source of truth for the fallback rules shared by the `budget` read
command and `ledger-add`'s overrun detection: a missing or unusable value
falls back to the 300-second default and never fails the run.
"""

from datetime import datetime, timedelta, timezone

from factory_cli import state

DEFAULT_SECONDS = 300
REVIEWER_ROLES = {
    "security-reviewer",
    "code-standards",
    "spec-conformance",
    "ui-reviewer",
    "ux-reviewer",
}


def resolve(role, config, full=False):
    """Seconds allowed for `role`: `budget.roles[<role>]` when a positive
    integer, else `budget.default_s` when a positive integer, else 300.
    Malformed entries fall back per entry; this never raises."""
    section = config.get("budget") if isinstance(config, dict) else None
    if not isinstance(section, dict):
        section = {}
    roles = section.get("roles")
    value = roles.get(role) if isinstance(roles, dict) else None
    fallback = section.get("default_s")
    normal = next(
        (v for v in (value, fallback, DEFAULT_SECONDS) if type(v) is int and v > 0)
    )
    full_seconds = section.get("review_full_s")
    if type(full_seconds) is not int or full_seconds <= 0:
        full_seconds = 600
    return max(normal, full_seconds) if full and role in REVIEWER_ROLES else normal


def deadline_for(seconds, now=None):
    """The absolute ISO-8601 UTC deadline: now + seconds."""
    moment = now or datetime.now(timezone.utc)
    return state.iso(moment + timedelta(seconds=seconds))
