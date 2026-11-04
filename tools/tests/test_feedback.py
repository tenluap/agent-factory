"""Post-PR feedback refresh seam tests (FR-002..FR-006, FR-012).

`factory_cli.feedback.refresh` reads archived runs' PRs through one injectable
`gh` runner and records PR outcomes in `${FACTORY_HOME}/outcomes/`. The
archive stays byte-identical; a fake runner stands in for GitHub.
"""

import json
import sys
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
