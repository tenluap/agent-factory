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


def ledger(started_at, ended_at, duration_ms=None):
    entry = {
        "at": started_at,
        "stage": "review",
        "role": "code-standards",
        "harness": "opencode",
        "in_est": 0,
        "out_est": 0,
        "reported": None,
    }
    if started_at and ended_at:
        entry.update(started_at=started_at, ended_at=ended_at)
    entry["duration_ms"] = duration_ms if duration_ms is not None else 0
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


if __name__ == "__main__":
    unittest.main()
