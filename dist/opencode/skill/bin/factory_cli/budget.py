"""Time budget resolution and deadline derivation (FR-001, FR-007).

One source of truth for the fallback rules shared by the `budget` read
command and `ledger-add`'s overrun detection: a missing or unusable value
falls back to the 300-second default and never fails the run.
"""

from datetime import datetime, timedelta, timezone

from factory_cli import state

DEFAULT_SECONDS = 300


def resolve(role, config):
    """Seconds allowed for `role`: `budget.roles[<role>]` when a positive
    integer, else `budget.default_s` when a positive integer, else 300.
    Malformed entries fall back per entry; this never raises."""
    section = config.get("budget") if isinstance(config, dict) else None
    if not isinstance(section, dict):
        return DEFAULT_SECONDS
    roles = section.get("roles")
    if isinstance(roles, dict):
        value = roles.get(role)
        if isinstance(value, int) and not isinstance(value, bool) and value > 0:
            return value
    fallback = section.get("default_s")
    if isinstance(fallback, int) and not isinstance(fallback, bool) and fallback > 0:
        return fallback
    return DEFAULT_SECONDS


def deadline_for(seconds, now=None):
    """The absolute ISO-8601 UTC deadline: now + seconds."""
    moment = now or datetime.now(timezone.utc)
    return state.iso(moment + timedelta(seconds=seconds))
