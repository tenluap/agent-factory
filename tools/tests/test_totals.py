"""Totals seam tests: `factory_cli.totals` interval unions (SC-003, FR-009).

Agent effort is the union of spawn intervals, human time the union of user
waits; neither is ever a sum of parallel durations, and human + agent never
exceeds wall clock by construction.
"""

import sys
import unittest
from pathlib import Path

CORE_BIN = Path(__file__).resolve().parents[2] / "core" / "skills" / "factory" / "bin"
sys.path.insert(0, str(CORE_BIN))

from factory_cli import totals  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def ledger(started_at, ended_at, duration_ms=None, in_est=0, out_est=0, reported=None):
    entry = {
        "at": started_at,
        "stage": "review",
        "role": "code-standards",
        "harness": "opencode",
        "reported": reported,
    }
    if started_at and ended_at:
        entry.update(started_at=started_at, ended_at=ended_at)
    entry["duration_ms"] = duration_ms if duration_ms is not None else 0
    entry["in_est"] = in_est
    entry["out_est"] = out_est
    return entry


def wait(at, answered_at, latency_ms=None):
    return {
        "at": at,
        "kind": "questions",
        "stage": "review",
        "summary": "s",
        "answered_at": answered_at,
        "latency_ms": latency_ms,
    }


def run(started_at, ended_at, timeline=(), spawns=()):
    return {
        "started_at": started_at,
        "ended_at": ended_at,
        "timeline": list(timeline),
        "ledger": list(spawns),
    }


class UnionTests(unittest.TestCase):
    def test_overlapping_spawns_union_never_sum(self):
        t = totals.compute(
            run(
                "2026-10-23T10:00:00Z",
                "2026-10-23T10:20:00Z",
                spawns=[
                    ledger("2026-10-23T10:00:00Z", "2026-10-23T10:10:00Z"),
                    ledger("2026-10-23T10:05:00Z", "2026-10-23T10:15:00Z"),
                ],
            )
        )
        self.assertEqual(
            t["agent_ms"], 15 * 60_000, "union of 0-10 and 5-15 is 15 minutes"
        )
        self.assertEqual(t["spawns"], 2)

    def test_overlapping_waits_union_never_sum(self):
        t = totals.compute(
            run(
                "2026-10-23T10:00:00Z",
                "2026-10-23T10:20:00Z",
                timeline=[
                    wait("2026-10-23T10:00:00Z", "2026-10-23T10:10:00Z"),
                    wait("2026-10-23T10:05:00Z", "2026-10-23T10:15:00Z"),
                ],
            )
        )
        self.assertEqual(t["human_ms"], 15 * 60_000)
        self.assertEqual(t["waits"], 2)

    def test_zero_length_interval_counts_nothing(self):
        t = totals.compute(
            run(
                "2026-10-23T10:00:00Z",
                "2026-10-23T10:10:00Z",
                spawns=[ledger("2026-10-23T10:05:00Z", "2026-10-23T10:05:00Z")],
                timeline=[wait("2026-10-23T10:05:00Z", "2026-10-23T10:05:00Z")],
            )
        )
        self.assertEqual((t["agent_ms"], t["human_ms"]), (0, 0))

    def test_missing_intervals_fall_back_to_duration(self):
        t = totals.compute(
            run(
                "2026-10-23T10:00:00Z",
                "2026-10-23T10:30:00Z",
                spawns=[
                    {
                        "at": "2026-10-23T10:05:00Z",
                        "duration_ms": 5 * 60_000,
                    },  # legacy v3 entry
                    {"at": "2026-10-23T10:20:00Z"},  # nothing measurable
                    {"at": "2026-10-23T10:25:00Z", "duration_ms": 60_000},
                ],
            )
        )
        self.assertEqual(
            t["agent_ms"], 6 * 60_000, "at+duration for legacy, 0 for the blind entry"
        )

    def test_open_wait_never_counts_as_human_time(self):
        t = totals.compute(
            run(
                "2026-10-23T10:00:00Z",
                "2026-10-23T10:10:00Z",
                timeline=[
                    wait("2026-10-23T10:00:00Z", None),
                    wait("2026-10-23T10:02:00Z", "2026-10-23T10:05:00Z"),
                ],
            )
        )
        self.assertEqual(t["human_ms"], 3 * 60_000)
        self.assertEqual(t["waits"], 2)
        self.assertEqual(t["open_waits"], 1)

    def test_parallel_reviews_stay_within_wall_clock(self):
        state = run(
            "2026-10-23T10:00:00Z",
            "2026-10-23T11:00:00Z",
            timeline=[
                wait("2026-10-23T10:00:00Z", "2026-10-23T10:20:00Z"),
                wait("2026-10-23T10:10:00Z", "2026-10-23T10:30:00Z"),
            ],
            spawns=[
                ledger("2026-10-23T10:20:00Z", "2026-10-23T10:40:00Z"),
                ledger("2026-10-23T10:35:00Z", "2026-10-23T10:50:00Z"),
            ],
        )
        t = totals.compute(state)
        self.assertEqual(t["human_ms"], 30 * 60_000)
        self.assertEqual(t["agent_ms"], 30 * 60_000)
        self.assertLessEqual(t["human_ms"] + t["agent_ms"], t["wall_ms"])

    def test_run_005_parallel_reviews_no_longer_exceed_wall_clock(self):
        import json

        state = json.loads((FIXTURES / "replay-005.json").read_text())
        t = totals.compute(state)
        summed = sum(e["duration_ms"] for e in state["ledger"]) + sum(
            e["latency_ms"] for e in state["timeline"]
        )
        self.assertLessEqual(t["human_ms"] + t["agent_ms"], t["wall_ms"])
        self.assertLess(
            t["agent_ms"],
            summed - t["human_ms"],
            "the union is strictly smaller than the parallel sum",
        )

    def test_overhead_is_the_residual_and_never_negative(self):
        t = totals.compute(
            run(
                "2026-10-23T10:00:00Z",
                "2026-10-23T10:10:00Z",
                timeline=[wait("2026-10-23T10:00:00Z", "2026-10-23T10:04:00Z")],
                spawns=[ledger("2026-10-23T10:04:00Z", "2026-10-23T10:09:00Z")],
            )
        )
        self.assertEqual(t["overhead_ms"], 60_000)
        squeezed = totals.compute(
            run(
                "2026-10-23T10:00:00Z",
                "2026-10-23T10:10:00Z",
                spawns=[ledger("2026-10-23T10:00:00Z", "2026-10-23T10:20:00Z")],
            )
        )
        self.assertGreaterEqual(
            squeezed["overhead_ms"], 0, "max(wall - human - agent, 0)"
        )

    def test_missing_run_bounds(self):
        t = totals.compute(
            run(
                None,
                None,
                timeline=[wait("2026-10-23T10:00:00Z", "2026-10-23T10:01:00Z")],
                spawns=[ledger("2026-10-23T10:00:00Z", "2026-10-23T10:02:00Z")],
            )
        )
        self.assertEqual(t["wall_ms"], 0)
        self.assertGreater(t["human_ms"] + t["agent_ms"], 0)


class OpenRunTests(unittest.TestCase):
    """FR-016: totals for an open run (no ended_at) measure wall clock from
    the recorded start to now instead of reporting zero."""

    def test_open_run_measures_wall_clock_to_now(self):
        before = totals.compute(run("2026-10-23T10:00:00Z", None))
        self.assertGreater(before["wall_ms"], 0, "an open run's wall clock is not zero")
        after = totals.compute(run("2026-10-23T10:00:00Z", None))
        self.assertGreaterEqual(
            after["wall_ms"], before["wall_ms"], "wall clock grows with now"
        )

    def test_open_run_stays_bounded_when_started(self):
        self.assertTrue(totals.compute(run("2026-10-23T10:00:00Z", None))["bounded"])

    def test_open_run_effort_stays_within_wall_clock(self):
        t = totals.compute(
            run(
                "2026-10-23T10:00:00Z",
                None,
                timeline=(wait("2026-10-23T10:00:30Z", "2026-10-23T10:01:30Z", 60000),),
                spawns=(
                    ledger("2026-10-23T10:00:00Z", "2026-10-23T10:05:00Z", 300000),
                ),
            )
        )
        self.assertLessEqual(
            t["human_ms"] + t["agent_ms"],
            t["wall_ms"],
            "human + agent never exceed the open run's wall clock",
        )


class SentenceTests(unittest.TestCase):
    def test_sentence_format_names_all_parts(self):
        t = totals.compute(
            run(
                "2026-10-23T10:00:00Z",
                "2026-10-23T11:00:00Z",
                timeline=[wait("2026-10-23T10:00:00Z", "2026-10-23T10:20:00Z")],
                spawns=[ledger("2026-10-23T10:20:00Z", "2026-10-23T10:50:00Z")],
            )
        )
        self.assertEqual(
            totals.sentence(t),
            "Run took 1h 0m: 20m you (1 waits), 30m agents (1 spawns), 10m overhead.",
        )

    def test_sentence_without_run_bounds(self):
        self.assertIsNone(totals.sentence(totals.compute(run(None, None))))


class UsageLabellingTests(unittest.TestCase):
    """FR-010, R17: reported usage is labelled separately, never merged."""

    def test_estimates_sum_under_their_own_labels(self):
        t = totals.compute(
            run(
                "2026-10-23T10:00:00Z",
                "2026-10-23T10:30:00Z",
                spawns=[
                    ledger(
                        "2026-10-23T10:00:00Z",
                        "2026-10-23T10:10:00Z",
                        in_est=15000,
                        out_est=4000,
                    ),
                    ledger(
                        "2026-10-23T10:20:00Z",
                        "2026-10-23T10:30:00Z",
                        in_est=8000,
                        out_est=1000,
                    ),
                ],
            )
        )
        self.assertEqual(t["in_est"], 23000, "the word-count estimates, summed")
        self.assertEqual(t["out_est"], 5000)
        self.assertEqual(t["reported"], [], "no harness-reported usage, empty list")

    def test_reported_is_kept_verbatim_and_never_merged(self):
        reported = {"input_tokens": 1200, "output_tokens": 300}
        t = totals.compute(
            run(
                "2026-10-23T10:00:00Z",
                "2026-10-23T10:30:00Z",
                spawns=[
                    ledger(
                        "2026-10-23T10:00:00Z",
                        "2026-10-23T10:10:00Z",
                        in_est=1000,
                        out_est=100,
                        reported=reported,
                    ),
                    ledger(
                        "2026-10-23T10:20:00Z",
                        "2026-10-23T10:30:00Z",
                        in_est=7,
                        out_est=3,
                    ),
                ],
            )
        )
        self.assertEqual(t["reported"], [reported], "harness-reported usage, verbatim")
        self.assertEqual(
            (t["in_est"], t["out_est"]),
            (1007, 103),
            "the estimate sums exclude reported usage",
        )

    def test_sentence_labels_estimates_and_reported_separately(self):
        t = totals.compute(
            run(
                "2026-10-23T10:00:00Z",
                "2026-10-23T10:30:00Z",
                spawns=[
                    ledger(
                        "2026-10-23T10:00:00Z",
                        "2026-10-23T10:10:00Z",
                        in_est=23000,
                        out_est=5000,
                        reported={"input_tokens": 1200},
                    )
                ],
            )
        )
        line = totals.sentence(t)
        self.assertIn("23k in/5k out estimated", line)
        self.assertIn("harness-reported", line, "reported usage carries its own label")
        self.assertIn('{"input_tokens": 1200}', line, "reported usage shown verbatim")

    def test_sentence_without_usage_stays_unlabelled(self):
        t = totals.compute(
            run(
                "2026-10-23T10:00:00Z",
                "2026-10-23T10:30:00Z",
                spawns=[ledger("2026-10-23T10:00:00Z", "2026-10-23T10:10:00Z")],
            )
        )
        self.assertNotIn("estimated", totals.sentence(t))
        self.assertNotIn("harness-reported", totals.sentence(t))


if __name__ == "__main__":
    unittest.main()
