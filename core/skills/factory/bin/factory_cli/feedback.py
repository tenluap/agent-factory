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


def _review_outcomes(reviews):
    found = []
    for review in reviews:
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


class Gap(Exception):
    """A classified fetch problem for one run, listed under `gaps`."""

    def __init__(self, cls, reason):
        super().__init__(reason)
        self.cls = cls
        self.reason = reason


def _first_line(text):
    return next((line.strip() for line in text.splitlines() if line.strip()), "")


def _classify(code, stderr):
    """Gap class of a non-zero `gh` exit: auth and access problems are
    inaccessible, a PR that does not exist is missing, anything else (5xx,
    network) is transient."""
    if code == 4 or "gh auth login" in stderr or "HTTP 401" in stderr:
        return "inaccessible"
    if "Could not resolve to a PullRequest" in stderr or "HTTP 404" in stderr:
        return "missing"
    if (
        "Could not resolve to a Repository" in stderr
        or "HTTP 403" in stderr
        or "Resource not accessible" in stderr
    ):
        return "inaccessible"
    return "transient"


def _gh_read(gh, args):
    """One GitHub read; every failure becomes a Gap for the run."""
    try:
        code, out, err = gh(args)
    except OSError as e:  # `gh` is not installed or not executable
        raise Gap("inaccessible", str(e)) from e
    except subprocess.TimeoutExpired as e:
        raise Gap("transient", str(e)) from e
    if code != 0:
        raise Gap(_classify(code, err), _first_line(err) or f"gh exited {code}")
    return out


def _parse_pr(text):
    try:
        pr = json.loads(text)
    except ValueError as e:
        raise Gap("transient", f"unparseable pr view JSON: {e}") from e
    if (
        not isinstance(pr, dict)
        or pr.get("state") not in ("OPEN", "CLOSED", "MERGED")
        or not isinstance(pr.get("headRefOid"), str)
        or not re.fullmatch(r"[0-9a-f]+", pr["headRefOid"])
        or not isinstance(pr.get("statusCheckRollup"), list)
        or not all(isinstance(item, dict) for item in pr["statusCheckRollup"])
    ):
        raise Gap("transient", "unexpected pr view shape")
    return pr


def _parse_reviews(text):
    reviews = []
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            review = json.loads(line)
        except ValueError as e:
            raise Gap("transient", f"unparseable review JSON: {e}") from e
        if not isinstance(review, dict) or not isinstance(review.get("state"), str):
            raise Gap("transient", "unexpected review shape")
        if review["state"] == "CHANGES_REQUESTED" and type(review.get("id")) is not int:
            raise Gap("transient", "changes-requested review without an integer id")
        reviews.append(review)
    return reviews


def _fetch(pr_url, gh):
    """Two sequential reads; first outcome per id kept, in response order."""
    match = PR_URL.fullmatch(pr_url)
    if match is None:
        raise Gap("missing", "unparseable pr_url")
    host, owner, repo_name, number = match.groups()
    pr = _parse_pr(_gh_read(gh, ["pr", "view", pr_url, "--json", PR_FIELDS]))
    reviews = _parse_reviews(
        _gh_read(
            gh,
            [
                "api",
                "--hostname",
                host,
                "--paginate",
                f"repos/{owner}/{repo_name}/pulls/{number}/reviews",
                "--jq",
                REVIEW_JQ,
            ],
        )
    )
    candidates = _check_outcomes(pr) + _review_outcomes(reviews) + _state_outcomes(pr)
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


def _slug(text):
    """Signal-key slug: lowercase, each run outside `[a-z0-9-]` one `-`, at most
    64 characters, `unnamed` when nothing is left."""
    slug = re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")[:64].rstrip("-")
    return slug or "unnamed"


def _line(text, limit=100):
    """Feature-text display: one printable line of at most `limit` characters."""
    flat = " ".join("".join(c if c.isprintable() else " " for c in str(text)).split())
    return flat[:limit]


def _feedback_item(run, outcome):
    """The feedback entry an actionable new outcome maps to, or None (merged
    PRs and other states are not actionable)."""
    seen = f"(seen on run {run['branch']})"
    detail = outcome["detail"]
    if outcome["kind"] == "check":
        name = detail.get("name") or ""
        key = f"ci-failure:{_slug(name)}"
        feature = f"Prevent factory PRs failing CI check '{_line(name)}' {seen}"
    elif outcome["kind"] == "review":
        reviewer = detail.get("reviewer") or "ghost"
        key = f"changes-requested:{_slug(reviewer)}"
        feature = f"Address the changes {_line(reviewer)} requests on factory PRs {seen}"
    elif outcome["id"] == "state:closed":
        key = "pr-closed:unmerged"
        feature = f"Find why factory PRs are closed without merging {seen}"
    else:
        return None
    return {"signal_key": key, "evidence": outcome["url"], "suggested_feature": feature}


def _load_outcomes(path, run):
    """The run's stored outcome file, or a fresh body; a malformed file is a gap."""
    if not path.exists():
        return {
            "run": {k: run.get(k) for k in ("repo", "branch", "spec_dir", "pr_url")},
            "outcomes": [],
        }
    try:
        body = json.loads(path.read_text())
    except (OSError, ValueError) as e:
        raise Gap("inaccessible", f"unreadable outcome file {path}: {e}") from e
    if not isinstance(body, dict) or not all(
        isinstance(o, dict) and "id" in o for o in body.get("outcomes") or [None]
    ):
        raise Gap("inaccessible", f"malformed outcome file {path}")
    return body


def _add_backlog(home, run, items, now):
    """Feedback entries for the new outcomes; a held lock is transient, any
    other refused entry file (its written links kept) is inaccessible."""
    try:
        return improvements.add_feedback(home, run, items, now=now)
    except improvements.AddError as e:
        if isinstance(e.__cause__, lock.LockHeld):
            raise Gap("transient", f"backlog lock held: {e.__cause__}") from e
        raise Gap("inaccessible", str(e)) from e


def _store(home, run, candidates, now):
    """Append outcomes whose ids are not stored yet, and their feedback entries,
    under the outcomes lock (outcomes, then backlog); the outcome write comes
    last, so a failed write is retried without duplicate links. Returns the new
    outcomes and the backlog result; local failures raise Gap."""
    directory = Path(home) / "outcomes"
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise Gap("inaccessible", f"cannot create {directory}: {e}") from e
    path = _outcome_path(home, run)
    try:
        _acquire_home_lock(directory, "feedback")
    except lock.LockHeld as e:
        raise Gap("transient", f"outcomes lock held: {e}") from e
    backlog = {"created": [], "updated": [], "claimed": []}
    try:
        body = _load_outcomes(path, run)
        stored = {outcome["id"] for outcome in body["outcomes"]}
        new = [dict(c, recorded_at=now) for c in candidates if c["id"] not in stored]
        if new:
            items = [_feedback_item(run, outcome) for outcome in new]
            items = [item for item in items if item]
            if items:
                backlog = _add_backlog(home, run, items, now)
            body["outcomes"].extend(new)
            try:
                _write_atomic(path, body)
            except OSError as e:
                raise Gap("transient", f"outcome write failed: {e}") from e
    finally:
        lock.release(directory)
    return new, backlog


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
        try:
            new, backlog = _store(home, run, _fetch(run["pr_url"], gh), now)
        except Gap as gap:
            report["gaps"].append(
                {
                    "run": run["branch"],
                    "pr_url": run["pr_url"],
                    "class": gap.cls,
                    "reason": gap.reason,
                }
            )
            continue
        report["refreshed"].append(
            {
                "run": run["branch"],
                "pr_url": run["pr_url"],
                "new_outcomes": new,
                "backlog": backlog,
            }
        )
    return report
