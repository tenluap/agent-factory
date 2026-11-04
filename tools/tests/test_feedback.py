"""Post-PR feedback refresh seam tests (FR-002..FR-006, FR-012).

`factory_cli.feedback.refresh` reads archived runs' PRs through one injectable
`gh` runner and records PR outcomes in `${FACTORY_HOME}/outcomes/`. The
archive stays byte-identical; a fake runner stands in for GitHub.
"""

import hashlib
import json
import os
import subprocess
import sys
import time
import unittest
from pathlib import Path
from unittest import mock

CORE_BIN = Path(__file__).resolve().parents[2] / "core" / "skills" / "factory" / "bin"
sys.path.insert(0, str(CORE_BIN))

from factory_cli import feedback  # noqa: E402

from tests import Sandbox  # noqa: E402

NOW = "2026-11-04T01:00:00Z"
HEAD = "b167" * 10
PR_URL = "https://github.com/o/r/pull/7"
PR_FIELDS = "state,mergedAt,closedAt,headRefOid,statusCheckRollup,url"


class FakeGh:
    """Records every call; answers the two reads from inline JSON."""

    def __init__(self, pr, reviews=()):
        self.pr = pr
        self.reviews = reviews
        self.calls = []

    def __call__(self, args):
        self.calls.append(list(args))
        if args[0] == "pr":
            return 0, json.dumps(self.pr), ""
        return 0, "".join(json.dumps(r) + "\n" for r in self.reviews), ""


def pr(checks=(), state="OPEN", **extra):
    body = {
        "state": state,
        "mergedAt": None,
        "closedAt": None,
        "headRefOid": HEAD,
        "statusCheckRollup": list(checks),
        "url": PR_URL,
    }
    body.update(extra)
    return body


def check_run(name, conclusion, completed="2026-11-04T00:30:00Z", url="https://ci/1"):
    return {
        "__typename": "CheckRun",
        "name": name,
        "conclusion": conclusion,
        "completedAt": completed,
        "detailsUrl": url,
    }


def review(review_id, state, user="Some.User", url="https://github.com/o/r/pull/7#review"):
    return {
        "id": review_id,
        "state": state,
        "submitted_at": "2026-11-04T00:40:00Z",
        "html_url": url,
        "user": user,
    }


class FeedbackTestCase(unittest.TestCase):
    def setUp(self):
        self.sb = Sandbox()
        self.addCleanup(self.sb.close)
        self.repo = str(self.sb.repo.resolve())

    def archive(self, branch="feature-x", pr_url=PR_URL, name=None):
        folder = self.sb.home / "archive" / (name or f"repo-{branch}")
        folder.mkdir(parents=True, exist_ok=True)
        run = {
            "repo": self.repo,
            "branch": branch,
            "spec_dir": f"specs/{branch}",
            "status": "pr-open",
        }
        if pr_url is not None:
            run["pr_url"] = pr_url
        path = folder / "state.json"
        path.write_text(json.dumps(run, indent=2) + "\n")
        return path

    def refresh(self, gh):
        return feedback.refresh(self.sb.home, self.repo, gh=gh, now=NOW)

    def refresh_branch(self, gh, branch):
        return feedback.refresh(self.sb.home, self.repo, branch=branch, gh=gh, now=NOW)

    def outcomes(self, branch="feature-x"):
        path = self.sb.home / "outcomes" / f"repo-{branch}.json"
        if not path.exists():
            return {}
        return {o["id"]: o for o in json.loads(path.read_text())["outcomes"]}


class CaptureTests(FeedbackTestCase):
    def test_failed_check_and_change_request_are_recorded(self):
        self.archive()
        gh = FakeGh(pr([check_run("test", "FAILURE")]), [review(11, "CHANGES_REQUESTED")])

        report = self.refresh(gh)

        found = self.outcomes()
        check = found[f"check:test@{HEAD}"]
        self.assertEqual(check["kind"], "check")
        self.assertEqual(check["event_at"], "2026-11-04T00:30:00Z")
        self.assertEqual(check["url"], "https://ci/1")
        self.assertEqual(check["detail"], {"name": "test", "conclusion": "failure"})
        self.assertEqual(check["recorded_at"], NOW)
        change = found["review:11"]
        self.assertEqual(change["kind"], "review")
        self.assertEqual(change["event_at"], "2026-11-04T00:40:00Z")
        self.assertEqual(change["url"], "https://github.com/o/r/pull/7#review")
        self.assertEqual(change["detail"], {"reviewer": "Some.User"})
        self.assertEqual(len(report["refreshed"]), 1)
        self.assertEqual(report["refreshed"][0]["run"], "feature-x")
        self.assertEqual(len(report["refreshed"][0]["new_outcomes"]), 2)
        self.assertEqual(report["gaps"], [])

    def test_read_arguments_match_the_two_github_reads(self):
        self.archive()
        gh = FakeGh(pr())

        self.refresh(gh)

        self.assertEqual(gh.calls[0], ["pr", "view", PR_URL, "--json", PR_FIELDS])
        self.assertEqual(
            gh.calls[1][:5],
            ["api", "--hostname", "github.com", "--paginate", "repos/o/r/pulls/7/reviews"],
        )
        self.assertIn("--jq", gh.calls[1])

    def test_status_context_failure_and_null_login_as_ghost(self):
        self.archive()
        context = {
            "__typename": "StatusContext",
            "context": "ci/legacy",
            "state": "FAILURE",
            "startedAt": "2026-11-04T00:10:00Z",
            "targetUrl": "https://t/1",
        }
        gh = FakeGh(pr([context]), [review(12, "CHANGES_REQUESTED", user=None)])

        self.refresh(gh)

        found = self.outcomes()
        status = found[f"check:ci/legacy@{HEAD}"]
        self.assertEqual(status["event_at"], "2026-11-04T00:10:00Z")
        self.assertEqual(status["url"], "https://t/1")
        self.assertEqual(status["detail"], {"name": "ci/legacy", "conclusion": "failure"})
        self.assertEqual(found["review:12"]["detail"], {"reviewer": "ghost"})

    def test_merged_and_closed_pr_states(self):
        self.archive("merged-run")
        self.refresh(FakeGh(pr(state="MERGED", mergedAt="2026-11-04T00:50:00Z")))
        merged = self.outcomes("merged-run")
        self.assertEqual(list(merged), ["state:merged"])
        self.assertEqual(merged["state:merged"]["event_at"], "2026-11-04T00:50:00Z")
        self.assertEqual(merged["state:merged"]["url"], PR_URL)
        self.assertEqual(merged["state:merged"]["detail"], {})

        self.archive("closed-run")
        self.refresh(FakeGh(pr(state="CLOSED", closedAt="2026-11-04T00:55:00Z")))
        closed = self.outcomes("closed-run")
        self.assertEqual(list(closed), ["state:closed"])
        self.assertEqual(closed["state:closed"]["event_at"], "2026-11-04T00:55:00Z")

    def test_ignored_results_store_nothing(self):
        self.archive()
        checks = [
            check_run("a", "SUCCESS"),
            check_run("b", "CANCELLED"),
            check_run("c", "NEUTRAL"),
            check_run("d", "SKIPPED"),
        ] + [
            {"__typename": "StatusContext", "context": "e", "state": s, "startedAt": None, "targetUrl": None}
            for s in ("ERROR", "PENDING", "SUCCESS")
        ]
        gh = FakeGh(pr(checks), [review(13, "APPROVED"), review(14, "COMMENTED")])

        report = self.refresh(gh)

        self.assertEqual(report["refreshed"][0]["new_outcomes"], [])
        self.assertEqual(self.outcomes(), {})

    def test_same_check_on_same_head_keeps_the_first(self):
        self.archive()
        first = check_run("test", "FAILURE", completed="2026-11-04T00:30:00Z")
        second = check_run("test", "TIMED_OUT", completed="2026-11-04T00:45:00Z")

        self.refresh(FakeGh(pr([first, second])))

        found = self.outcomes()
        self.assertEqual(list(found), [f"check:test@{HEAD}"])
        self.assertEqual(found[f"check:test@{HEAD}"]["event_at"], "2026-11-04T00:30:00Z")

    def test_runs_without_pr_url_or_of_other_repos_are_not_fetched(self):
        self.archive("no-pr", pr_url=None)
        other = self.archive("elsewhere")
        run = json.loads(other.read_text())
        run["repo"] = "/somewhere/else"
        other.write_text(json.dumps(run) + "\n")
        gh = FakeGh(pr())

        report = self.refresh(gh)

        self.assertEqual(gh.calls, [])
        self.assertEqual(report, {"refreshed": [], "skipped": [], "gaps": []})

    def test_unreadable_archive_state_is_skipped_not_a_gap(self):
        bad = self.sb.home / "archive" / "repo-broken"
        bad.mkdir(parents=True)
        (bad / "state.json").write_text("{not json")
        self.archive()

        report = self.refresh(FakeGh(pr()))

        self.assertEqual(
            report["skipped"], [{"run": "repo-broken", "reason": "unreadable archive state"}]
        )
        self.assertEqual(report["gaps"], [])

    def test_zero_runs_give_empty_lists(self):
        report = self.refresh(FakeGh(pr()))
        self.assertEqual(report, {"refreshed": [], "skipped": [], "gaps": []})

    def test_archive_is_byte_identical_after_refresh(self):
        path = self.archive()
        before = path.read_bytes()

        self.refresh(FakeGh(pr([check_run("test", "FAILURE")])))

        self.assertEqual(path.read_bytes(), before)


class NarrowTests(FeedbackTestCase):
    def test_branch_narrows_the_refresh_to_one_run(self):
        self.archive("feature-x")
        self.archive("feature-y", pr_url="https://github.com/o/r/pull/9")
        gh = FakeGh(pr([check_run("test", "FAILURE")]))

        report = self.refresh_branch(gh, "feature-y")

        self.assertEqual([r["run"] for r in report["refreshed"]], ["feature-y"])
        self.assertEqual(gh.calls[0][2], "https://github.com/o/r/pull/9")
        self.assertTrue(all(c[2] == "https://github.com/o/r/pull/9" for c in gh.calls if c[0] == "pr"))
        self.assertTrue((self.sb.home / "outcomes" / "repo-feature-y.json").exists())
        self.assertFalse((self.sb.home / "outcomes" / "repo-feature-x.json").exists())

    def test_branch_naming_no_archived_run_is_refused(self):
        self.archive("feature-x")
        gh = FakeGh(pr())

        with self.assertRaises(ValueError) as caught:
            self.refresh_branch(gh, "missing-run")

        self.assertIn("missing-run", str(caught.exception))
        self.assertEqual(gh.calls, [])
        self.assertFalse((self.sb.home / "outcomes").exists())

    def test_branch_of_a_run_without_pr_url_is_refused(self):
        self.archive("feature-x", pr_url=None)
        gh = FakeGh(pr())

        with self.assertRaises(ValueError) as caught:
            self.refresh_branch(gh, "feature-x")

        self.assertIn("pr_url", str(caught.exception))
        self.assertEqual(gh.calls, [])
        self.assertFalse((self.sb.home / "outcomes").exists())


class DedupeTests(FeedbackTestCase):
    def test_second_identical_refresh_leaves_the_file_unchanged(self):
        self.archive()
        gh = FakeGh(pr([check_run("test", "FAILURE")]))
        self.refresh(gh)
        path = self.sb.home / "outcomes" / "repo-feature-x.json"
        before = path.read_bytes()

        report = feedback.refresh(self.sb.home, self.repo, gh=gh, now="2026-11-04T02:00:00Z")

        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(report["refreshed"][0]["new_outcomes"], [])

    def test_stored_outcome_keeps_its_recorded_at(self):
        self.archive()
        gh = FakeGh(pr([check_run("test", "FAILURE")]))
        self.refresh(gh)

        feedback.refresh(self.sb.home, self.repo, gh=gh, now="2026-11-04T02:00:00Z")

        self.assertEqual(self.outcomes()[f"check:test@{HEAD}"]["recorded_at"], NOW)

    def test_same_check_on_a_new_head_adds_one_outcome(self):
        self.archive()
        self.refresh(FakeGh(pr([check_run("test", "FAILURE")])))
        new_head = "d00d" * 10

        self.refresh(FakeGh(pr([check_run("test", "FAILURE")], headRefOid=new_head)))

        found = self.outcomes()
        self.assertEqual(len(found), 2)
        self.assertIn(f"check:test@{new_head}", found)

    def test_terminal_run_is_skipped_and_not_fetched(self):
        self.archive()
        self.refresh(FakeGh(pr(state="MERGED", mergedAt="2026-11-04T00:50:00Z")))
        gh = FakeGh(pr([check_run("test", "FAILURE")]))

        report = self.refresh(gh)

        self.assertEqual(gh.calls, [])
        self.assertEqual(report["refreshed"], [])
        self.assertEqual(
            report["skipped"], [{"run": "feature-x", "reason": "terminal outcome recorded"}]
        )

    def test_outcome_appended_during_the_fetch_is_kept(self):
        self.archive()
        path = self.sb.home / "outcomes" / "repo-feature-x.json"

        class ConcurrentGh(FakeGh):
            def __call__(self, args):
                if not path.exists():
                    path.parent.mkdir(parents=True, exist_ok=True)
                    other = {"id": "review:99", "kind": "review", "event_at": None,
                             "url": "", "detail": {"reviewer": "Other"}, "recorded_at": NOW}
                    path.write_text(json.dumps({"run": {}, "outcomes": [other]}))
                return super().__call__(args)

        self.refresh(ConcurrentGh(pr([check_run("test", "FAILURE")])))

        found = self.outcomes()
        self.assertIn("review:99", found)
        self.assertIn(f"check:test@{HEAD}", found)


class BacklogMappingTests(FeedbackTestCase):
    def feedback_entries(self):
        return [
            json.loads(path.read_text())
            for path in sorted((self.sb.home / "improvements").glob("*.feedback.*.json"))
        ]

    def backlog_bytes(self):
        directory = self.sb.home / "improvements"
        if not directory.exists():
            return {}
        return {path.name: path.read_bytes() for path in sorted(directory.glob("*.json"))}

    def test_failed_check_maps_to_ci_failure_entry(self):
        self.archive()
        report = self.refresh(FakeGh(pr([check_run("Lint / test", "FAILURE")])))

        [entry] = self.feedback_entries()
        self.assertEqual(entry["kind"], "feedback")
        self.assertEqual(entry["signal_key"], "ci-failure:lint-test")
        self.assertEqual(
            entry["suggested_feature"],
            "Prevent factory PRs failing CI check 'Lint / test' (seen on run feature-x)",
        )
        self.assertEqual(entry["evidence"], ["https://ci/1"])
        self.assertEqual(
            entry["run"],
            {"repo": self.repo, "branch": "feature-x", "spec_dir": "specs/feature-x"},
        )
        self.assertEqual(entry["status"], "ready")
        self.assertEqual(report["refreshed"][0]["backlog"]["created"], [entry["name"]])

    def test_change_request_maps_to_changes_requested_entry(self):
        self.archive()
        self.refresh(FakeGh(pr(), [review(11, "CHANGES_REQUESTED")]))

        [entry] = self.feedback_entries()
        self.assertEqual(entry["signal_key"], "changes-requested:some-user")
        self.assertEqual(
            entry["suggested_feature"],
            "Address the changes Some.User requests on factory PRs (seen on run feature-x)",
        )
        self.assertEqual(entry["evidence"], ["https://github.com/o/r/pull/7#review"])

    def test_unmerged_close_maps_and_merged_maps_to_nothing(self):
        self.archive()
        self.refresh(FakeGh(pr(state="CLOSED", closedAt="2026-11-04T00:50:00Z")))

        [entry] = self.feedback_entries()
        self.assertEqual(entry["signal_key"], "pr-closed:unmerged")
        self.assertEqual(
            entry["suggested_feature"],
            "Find why factory PRs are closed without merging (seen on run feature-x)",
        )

        self.archive(branch="feature-y")
        self.refresh_branch(
            FakeGh(pr(state="MERGED", mergedAt="2026-11-04T00:50:00Z")), "feature-y"
        )
        self.assertEqual(
            [e["run"]["branch"] for e in self.feedback_entries()], ["feature-x"]
        )

    def test_slug_and_feature_name_are_bounded(self):
        self.archive()
        long_name = "x" * 150 + "\n" + "y" * 149
        checks = [
            check_run("  Weird!!  Name  ", "FAILURE", url="https://ci/a"),
            check_run("!!!", "FAILURE", url="https://ci/b"),
            check_run("a" * 80, "FAILURE", url="https://ci/c"),
            check_run(long_name, "FAILURE", url="https://ci/d"),
        ]
        self.refresh(FakeGh(pr(checks)))

        by_key = {e["signal_key"]: e for e in self.feedback_entries()}
        self.assertIn("ci-failure:weird-name", by_key)
        self.assertIn("ci-failure:unnamed", by_key)
        self.assertIn("ci-failure:" + "a" * 64, by_key)
        feature = by_key["ci-failure:" + "x" * 64]["suggested_feature"]
        prefix = "Prevent factory PRs failing CI check '"
        self.assertTrue(feature.startswith(prefix))
        self.assertNotIn("\n", feature)
        shown = feature[len(prefix) : feature.index("' (seen")]
        self.assertEqual(shown, "x" * 100)

    def test_second_refresh_changes_no_backlog_file(self):
        self.archive()
        gh = FakeGh(pr([check_run("test", "FAILURE")]), [review(11, "CHANGES_REQUESTED")])
        self.refresh(gh)
        settled = self.backlog_bytes()
        self.assertEqual(len(settled), 2)

        report = self.refresh(gh)

        self.assertEqual(self.backlog_bytes(), settled)
        self.assertEqual(report["refreshed"][0]["new_outcomes"], [])
        self.assertEqual(
            report["refreshed"][0]["backlog"], {"created": [], "updated": [], "claimed": []}
        )


def raising(exc):
    def run(args):
        raise exc

    return run


def reply(pr_text=None, review_text=None):
    healthy_pr = json.dumps(pr([check_run("test", "FAILURE")]))

    def run(args):
        if args[0] == "pr":
            return 0, pr_text if pr_text is not None else healthy_pr, ""
        return 0, review_text or "", ""

    return run


def exits(code, stderr):
    return lambda args: (code, "", stderr)


class Routed:
    """Answers PR 7 (feature-x) with `on_x` and PR 8 (feature-y) healthily."""

    def __init__(self, on_x=None):
        self.on_x = on_x or reply()
        self.healthy = FakeGh(pr([check_run("lint", "FAILURE", url="https://ci/y")]))
        self.calls = []

    def __call__(self, args):
        self.calls.append(list(args))
        if any("pull/7" in a or "pulls/7/" in a for a in args):
            return self.on_x(args)
        return self.healthy(args)


class GapTests(FeedbackTestCase):
    def setUp(self):
        super().setUp()
        self.archive(branch="feature-x", pr_url=PR_URL)
        self.archive(branch="feature-y", pr_url="https://github.com/o/r/pull/8")
        self.refresh(Routed())
        self.settled = self.snapshot()
        self.assertEqual(len(list((self.sb.home / "improvements").glob("*.json"))), 2)

    def snapshot(self):
        home = self.sb.home
        return {
            str(path.relative_to(home)): path.read_bytes()
            for path in sorted(home.rglob("*"))
            if path.is_file()
        }

    def assert_gap(self, on_x, cls, reason=None):
        gh = Routed(on_x)
        report = self.refresh(gh)
        self.assertEqual(len(report["gaps"]), 1, report)
        gap = report["gaps"][0]
        self.assertEqual(gap["run"], "feature-x")
        self.assertEqual(gap["pr_url"], PR_URL)
        self.assertEqual(gap["class"], cls)
        if reason is not None:
            self.assertEqual(gap["reason"], reason)
        self.assertEqual([r["run"] for r in report["refreshed"]], ["feature-y"])
        self.assertEqual(self.snapshot(), self.settled)
        for read in ("pr", "api"):
            reads = [c for c in gh.calls if c[0] == read and any("pull/7" in a or "pulls/7/" in a for a in c)]
            self.assertLessEqual(len(reads), 1, read)

    def test_github_access_and_fetch_failures_are_classified(self):
        cases = [
            (raising(FileNotFoundError(2, "No such file or directory", "gh")), "inaccessible", None),
            (exits(4, "To get started, please run: gh auth login\n"), "inaccessible", "To get started, please run: gh auth login"),
            (exits(1, "HTTP 401: Bad credentials\n"), "inaccessible", "HTTP 401: Bad credentials"),
            (exits(1, "GraphQL: Could not resolve to a PullRequest with the number of 7.\n"), "missing", None),
            (exits(1, "HTTP 404: Not Found\n"), "missing", "HTTP 404: Not Found"),
            (exits(1, "GraphQL: Could not resolve to a Repository with the name 'o/r'.\n"), "inaccessible", None),
            (exits(1, "HTTP 403: Forbidden\n"), "inaccessible", None),
            (exits(1, "Resource not accessible by integration\n"), "inaccessible", None),
            (raising(subprocess.TimeoutExpired(["gh"], 60)), "transient", None),
            (exits(1, "HTTP 502: Bad Gateway\n"), "transient", "HTTP 502: Bad Gateway"),
        ]
        for index, (on_x, cls, reason) in enumerate(cases):
            with self.subTest(case=index, cls=cls):
                self.assert_gap(on_x, cls, reason)

    def test_malformed_reads_are_transient_gaps(self):
        cases = [
            reply(pr_text="{"),
            reply(pr_text=json.dumps(pr(state="MERGING"))),
            reply(pr_text=json.dumps(pr(headRefOid="XYZ"))),
            reply(pr_text=json.dumps(pr(statusCheckRollup={}))),
            reply(review_text="[]\n"),
            reply(review_text=json.dumps({"id": 1}) + "\n"),
            reply(review_text=json.dumps({"state": "CHANGES_REQUESTED"}) + "\n"),
        ]
        for index, on_x in enumerate(cases):
            with self.subTest(case=index):
                self.assert_gap(on_x, "transient")

    def test_approved_review_without_id_is_not_a_gap(self):
        report = self.refresh(Routed(reply(review_text=json.dumps({"state": "APPROVED"}) + "\n")))
        self.assertEqual(report["gaps"], [])
        self.assertEqual([r["run"] for r in report["refreshed"]], ["feature-x", "feature-y"])

    def test_unparseable_pr_url_is_missing_and_never_calls_gh(self):
        self.archive(branch="feature-z", pr_url="https://example.com/not-a-pr")
        gh = Routed()
        report = self.refresh(gh)
        [gap] = [g for g in report["gaps"] if g["run"] == "feature-z"]
        self.assertEqual(gap["class"], "missing")
        self.assertEqual(gap["reason"], "unparseable pr_url")
        self.assertFalse(any("not-a-pr" in a for call in gh.calls for a in call))


class LocalGapTests(FeedbackTestCase):
    def setUp(self):
        super().setUp()
        self.archive(branch="feature-x", pr_url=PR_URL)
        self.archive(branch="feature-y", pr_url="https://github.com/o/r/pull/8")
        self.refresh(Routed())
        repo_hash = hashlib.sha256(self.repo.encode()).hexdigest()[:12]
        self.outcome_file = self.sb.home / "outcomes" / f"{self.sb.repo.name}-feature-x.json"
        self.entry_file = (
            self.sb.home / "improvements"
            / f"{self.sb.repo.name}-feature-x.{repo_hash}.feedback.ci-failure.new.json"
        )

    def snapshot(self):
        home = self.sb.home
        return {
            str(path.relative_to(home)): path.read_bytes()
            for path in sorted(home.rglob("*"))
            if path.is_file()
        }

    def new_failure(self):
        return Routed(reply(pr_text=json.dumps(pr([check_run("new", "FAILURE", url="https://ci/new")]))))

    def hold_lock(self, name):
        (self.sb.home / f"{name}.lock.json").write_text(
            json.dumps({"owner_pid": 12345, "host": "other-host", "harness": "holder", "at": "now"})
        )

    def assert_gap_leaves_files(self, cls):
        before = self.snapshot()
        report = self.refresh(self.new_failure())
        self.assertEqual(
            [(g["run"], g["class"]) for g in report["gaps"]], [("feature-x", cls)], report
        )
        self.assertEqual([r["run"] for r in report["refreshed"]], ["feature-y"])
        self.assertEqual(self.snapshot(), before)

    def test_malformed_outcome_file_is_inaccessible(self):
        self.outcome_file.write_text("{not json")
        self.assert_gap_leaves_files("inaccessible")

    def test_empty_stored_outcome_list_is_not_a_malformed_file(self):
        body = json.loads(self.outcome_file.read_text())
        body["outcomes"] = []
        self.outcome_file.write_text(json.dumps(body))
        report = self.refresh(self.new_failure())
        self.assertEqual(report["gaps"], [])
        self.assertIn(f"check:new@{HEAD}", self.outcomes())

    def test_foreign_backlog_file_at_entry_name_is_inaccessible(self):
        self.entry_file.write_text(
            json.dumps(
                {
                    "kind": "feedback",
                    "run": {"repo": "/another/repo", "branch": "feature-x"},
                    "signal_key": "ci-failure:new",
                    "status": "ready",
                    "evidence": [],
                }
            )
        )
        self.assert_gap_leaves_files("inaccessible")

    def test_unreadable_backlog_file_at_entry_name_is_inaccessible(self):
        self.entry_file.write_text("{not json")
        self.assert_gap_leaves_files("inaccessible")

    def test_held_outcomes_lock_waits_then_is_transient(self):
        # The outcomes lock is home-wide, so every run waits and is transient.
        self.hold_lock("outcomes")
        before = self.snapshot()
        started = time.monotonic()
        report = self.refresh(self.new_failure())
        self.assertGreaterEqual(time.monotonic() - started, 4.5)
        self.assertEqual(
            [(g["run"], g["class"]) for g in report["gaps"]],
            [("feature-x", "transient"), ("feature-y", "transient")],
        )
        self.assertEqual(report["refreshed"], [])
        self.assertEqual(self.snapshot(), before)

    def test_held_backlog_lock_is_transient_and_outcome_file_unchanged(self):
        self.hold_lock("improvements")
        self.assert_gap_leaves_files("transient")
        self.assertFalse(self.entry_file.exists())

    def test_outcome_write_failing_after_backlog_write_keeps_links_once(self):
        with mock.patch("factory_cli.feedback._write_atomic", side_effect=OSError("disk full")):
            report = self.refresh(self.new_failure())
        self.assertEqual([(g["run"], g["class"]) for g in report["gaps"]], [("feature-x", "transient")])
        self.assertEqual(json.loads(self.entry_file.read_text())["evidence"], ["https://ci/new"])
        self.assertNotIn(f"check:new@{HEAD}", self.outcomes())

        report = self.refresh(self.new_failure())

        self.assertEqual(report["gaps"], [])
        self.assertIn(f"check:new@{HEAD}", self.outcomes())
        self.assertEqual(json.loads(self.entry_file.read_text())["evidence"], ["https://ci/new"])
        self.assertEqual(
            report["refreshed"][0]["backlog"], {"created": [], "updated": [], "claimed": []}
        )


FAKE_GH = (
    "#!" + sys.executable + "\n"
    "import json, os, sys\n"
    "if os.environ.get('FAKE_GH_MODE') == '502':\n"
    "    print('HTTP 502: Bad Gateway', file=sys.stderr)\n"
    "    sys.exit(1)\n"
    "if sys.argv[1] == 'pr':\n"
    "    print(" + repr(json.dumps(pr([check_run("test", "FAILURE")]))) + ")\n"
    "else:\n"
    "    print('')\n"
)


class FeedbackCommandTests(unittest.TestCase):
    def setUp(self):
        self.box = Sandbox()
        self.addCleanup(self.box.close)
        self.repo = str(self.box.repo.resolve())
        bin_dir = self.box.dir / "bin"
        bin_dir.mkdir()
        gh = bin_dir / "gh"
        gh.write_text(FAKE_GH)
        gh.chmod(0o755)
        self.patch_env(PATH=f"{bin_dir}{os.pathsep}{os.environ['PATH']}", FAKE_GH_MODE="ok")

    def patch_env(self, **values):
        patcher = mock.patch.dict(os.environ, values)
        patcher.start()
        self.addCleanup(patcher.stop)

    def archive(self, branch, pr_url=PR_URL):
        folder = self.box.home / "archive" / f"{self.box.repo.name}-{branch}"
        folder.mkdir(parents=True, exist_ok=True)
        run = {"repo": self.repo, "branch": branch, "spec_dir": f"specs/{branch}", "status": "pr-open"}
        if pr_url is not None:
            run["pr_url"] = pr_url
        (folder / "state.json").write_text(json.dumps(run))

    def feedback(self, *args, cwd=None):
        return self.box.cli("feedback", *args, cwd=cwd or self.box.repo)

    def test_prints_report_and_exits_zero_without_gaps(self):
        self.archive("feature-x")
        out = self.feedback()
        self.assertEqual(out.returncode, 0, out.stderr)
        report = json.loads(out.stdout)
        self.assertEqual(set(report), {"refreshed", "skipped", "gaps"})
        self.assertEqual(report["gaps"], [])
        self.assertEqual([r["run"] for r in report["refreshed"]], ["feature-x"])

    def test_zero_runs_exits_zero(self):
        out = self.feedback()
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(json.loads(out.stdout), {"refreshed": [], "skipped": [], "gaps": []})

    def test_branch_refreshes_only_that_run(self):
        self.archive("feature-x")
        self.archive("feature-y")
        out = self.feedback("feature-x")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual([r["run"] for r in json.loads(out.stdout)["refreshed"]], ["feature-x"])

    def test_repo_flag_selects_that_repository_from_another_directory(self):
        self.archive("feature-x")
        out = self.feedback("--repo", self.repo, cwd=self.box.home)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual([r["run"] for r in json.loads(out.stdout)["refreshed"]], ["feature-x"])

    def test_unknown_branch_exits_one_and_writes_nothing(self):
        out = self.feedback("missing")
        self.assertEqual(out.returncode, 1, out.stderr)
        self.assertIn("missing", out.stderr)
        self.assertFalse((self.box.home / "outcomes").exists())

    def test_branch_without_pr_url_exits_one_and_writes_nothing(self):
        self.archive("feature-x", pr_url=None)
        out = self.feedback("feature-x")
        self.assertEqual(out.returncode, 1, out.stderr)
        self.assertIn("pr_url", out.stderr)
        self.assertFalse((self.box.home / "outcomes").exists())

    def test_repo_outside_git_exits_two_and_writes_nothing(self):
        self.archive("feature-x")
        out = self.box.cli("feedback", "--repo", str(self.box.home), cwd=self.box.home)
        self.assertEqual(out.returncode, 2, out.stderr)
        self.assertFalse((self.box.home / "outcomes").exists())

    def test_gh_not_on_path_is_an_inaccessible_gap(self):
        self.archive("feature-x")
        self.patch_env(PATH=f"{self.box.dir / 'empty'}{os.pathsep}/usr/bin{os.pathsep}/bin")
        out = self.feedback()
        self.assertEqual(out.returncode, 1, out.stderr)
        report = json.loads(out.stdout)
        self.assertEqual([(g["run"], g["class"]) for g in report["gaps"]], [("feature-x", "inaccessible")])

    def test_server_error_is_a_transient_gap(self):
        self.archive("feature-x")
        self.patch_env(FAKE_GH_MODE="502")
        out = self.feedback()
        self.assertEqual(out.returncode, 1, out.stderr)
        report = json.loads(out.stdout)
        self.assertEqual([(g["run"], g["class"]) for g in report["gaps"]], [("feature-x", "transient")])


if __name__ == "__main__":
    unittest.main()
