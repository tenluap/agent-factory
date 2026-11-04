"""Post-PR feedback refresh (FR-002..FR-006, FR-012; ADR 0014).

`refresh` reads archived runs' pull requests through one injectable `gh`
runner and appends new PR outcomes to
`${FACTORY_HOME}/outcomes/<repo-name>-<branch>.json`. Nothing is written to
GitHub or to the archive; the archive is opened read-only.
"""

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from factory_cli import commands, improvements, lock, state
from factory_cli.improvements import _acquire_home_lock, _write_atomic

PR_FIELDS = "state,mergedAt,closedAt,headRefOid,statusCheckRollup,url"
REVIEW_JQ = ".[] | {id, state, submitted_at, html_url, user: .user.login}"
PR_URL = re.compile(
    r"https://([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/pull/(\d+)"
)
CHECK_FAILURES = ("FAILURE", "TIMED_OUT", "STARTUP_FAILURE")


def run_gh(args):
    """The one GitHub runner: `(returncode, stdout, stderr)`; tests inject a fake."""
    out = subprocess.run(
        ["gh", *args], capture_output=True, text=True, timeout=60
    )
    return out.returncode, out.stdout, out.stderr


def _outcome(outcome_id, kind, event_at, url, detail):
    return {
        "id": outcome_id,
        "kind": kind,
        "event_at": event_at,
        "url": url or "",
        "detail": detail,
    }


def _check_outcomes(pr):
    head = pr["headRefOid"]
    found = []
    for item in pr.get("statusCheckRollup") or []:
        if "context" in item:
            if item.get("state") != "FAILURE":
                continue
            name = item["context"]
            found.append(
                _outcome(
                    f"check:{name}@{head}",
                    "check",
                    item.get("startedAt"),
                    item.get("targetUrl"),
                    {"name": name, "conclusion": "failure"},
                )
            )
        elif item.get("conclusion") in CHECK_FAILURES:
            name = item.get("name")
            found.append(
                _outcome(
                    f"check:{name}@{head}",
                    "check",
                    item.get("completedAt"),
                    item.get("detailsUrl"),
                    {"name": name, "conclusion": item["conclusion"].lower()},
                )
            )
    return found


def _review_outcomes(text):
    found = []
    for line in text.splitlines():
        if not line.strip():
            continue
        review = json.loads(line)
        if review.get("state") != "CHANGES_REQUESTED":
            continue
        found.append(
            _outcome(
                f"review:{review['id']}",
                "review",
                review.get("submitted_at"),
                review.get("html_url"),
                {"reviewer": review.get("user") or "ghost"},
            )
        )
    return found


def _state_outcomes(pr):
    if pr.get("state") == "MERGED":
        return [_outcome("state:merged", "state", pr.get("mergedAt"), pr.get("url"), {})]
    if pr.get("state") == "CLOSED":
        return [_outcome("state:closed", "state", pr.get("closedAt"), pr.get("url"), {})]
    return []


def _fetch(pr_url, gh):
    """Two sequential reads; first outcome per id kept, in response order."""
    host, owner, repo_name, number = PR_URL.fullmatch(pr_url).groups()
    _, pr_out, _ = gh(["pr", "view", pr_url, "--json", PR_FIELDS])
    pr = json.loads(pr_out)
    _, review_out, _ = gh(
        [
            "api",
            "--hostname",
            host,
            "--paginate",
            f"repos/{owner}/{repo_name}/pulls/{number}/reviews",
            "--jq",
            REVIEW_JQ,
        ]
    )
    candidates = _check_outcomes(pr) + _review_outcomes(review_out) + _state_outcomes(pr)
    unique = {}
    for candidate in candidates:
        unique.setdefault(candidate["id"], candidate)
    return list(unique.values())


def _has_pr(run):
    return isinstance(run.get("pr_url"), str) and bool(run["pr_url"])


def _archived_runs(home, repo):
    """Every readable archived run of `repo`; unreadable archive state is skipped."""
    runs, skipped = [], []
    for path in sorted((Path(home) / "archive").glob("*/state.json")):
        try:
            run = json.loads(path.read_text())
            if not isinstance(run, dict):
                raise ValueError("not an object")
        except (OSError, ValueError):
            skipped.append({"run": path.parent.name, "reason": "unreadable archive state"})
            continue
        if run.get("repo") == repo:
            runs.append(run)
    return runs, skipped


TERMINAL_IDS = ("state:merged", "state:closed")


def _outcome_path(home, run):
    return Path(home) / "outcomes" / improvements.backlog_name(run["repo"], run["branch"])


def _is_terminal(home, run):
    """An unlocked read: a stored merged or closed PR state ends the run's refreshes."""
    path = _outcome_path(home, run)
    if not path.exists():
        return False
    try:
        body = json.loads(path.read_text())
    except (OSError, ValueError):
        return False
    return any(o.get("id") in TERMINAL_IDS for o in body.get("outcomes", []))


def _store(home, run, candidates, now):
    """Append outcomes whose ids are not stored yet; returns the new ones."""
    directory = Path(home) / "outcomes"
    directory.mkdir(parents=True, exist_ok=True)
    path = _outcome_path(home, run)
    _acquire_home_lock(directory, "feedback")
    try:
        if path.exists():
            body = json.loads(path.read_text())
        else:
            body = {
                "run": {k: run.get(k) for k in ("repo", "branch", "spec_dir", "pr_url")},
                "outcomes": [],
            }
        stored = {outcome["id"] for outcome in body["outcomes"]}
        new = [dict(c, recorded_at=now) for c in candidates if c["id"] not in stored]
        if new:
            body["outcomes"].extend(new)
            _write_atomic(path, body)
    finally:
        lock.release(directory)
    return new


def refresh(home, repo, branch=None, gh=run_gh, now=None):
    """Record new PR outcomes for the repository's archived runs with a `pr_url`,
    or only `branch`'s run. Refusals raise ValueError before any GitHub read."""
    now = now or state.iso(datetime.now(timezone.utc))
    runs, skipped = _archived_runs(home, str(commands.main_repo(repo)))
    if branch is None:
        runs = [run for run in runs if _has_pr(run)]
    else:
        named = [run for run in runs if run.get("branch") == branch]
        if not named:
            raise ValueError(f"no archived run for branch '{branch}'")
        if not _has_pr(named[0]):
            raise ValueError(f"archived run '{branch}' has no pr_url")
        runs = named
    report = {"refreshed": [], "skipped": skipped, "gaps": []}
    for run in runs:
        if _is_terminal(home, run):
            report["skipped"].append({"run": run["branch"], "reason": "terminal outcome recorded"})
            continue
        new = _store(home, run, _fetch(run["pr_url"], gh), now)
        report["refreshed"].append(
            {"run": run["branch"], "pr_url": run["pr_url"], "new_outcomes": new}
        )
    return report
