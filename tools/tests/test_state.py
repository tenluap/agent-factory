"""State seam tests: the `factory_cli.state` module API (read, validate, write).

Covers versions 1-5 read acceptance, legacy relay shapes, state copies in later
worktrees, vocabulary and timestamp violations with their location, the atomic
write, the first-write upgrade to the current version, the append-only
`decisions` guard, and the schema v5 `issues[]` validation and append-only
guard.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

CORE_BIN = Path(__file__).resolve().parents[2] / "core" / "skills" / "factory" / "bin"
sys.path.insert(0, str(CORE_BIN))

from factory_cli import state  # noqa: E402
from tests import replay  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def fixture(name):
    return json.loads((FIXTURES / name).read_text())


class ReadAcceptanceTests(unittest.TestCase):
    def test_read_accepts_versions_one_through_five(self):
        for name, version in (
            ("state-v1.json", 1),
            ("state-v2.json", 2),
            ("state-v3.json", 3),
            ("state-v4.json", 4),
            ("state-v5.json", 5),
        ):
            loaded, error = state.read_state(FIXTURES / name)
            self.assertIsNone(error, name)
            self.assertEqual(loaded["version"], version, name)

    def test_read_accepts_legacy_relay_shapes(self):
        v1, _ = state.read_state(FIXTURES / "state-v1.json")
        self.assertIn("questions", v1["relay"])  # version 1: one batch, no rounds
        v2, _ = state.read_state(FIXTURES / "state-v2.json")
        self.assertIsInstance(v2["relay"]["rounds"][0]["answers"]["Q1"], str)
        self.assertEqual(state.validate_state(v1), [], "v1 fixture validates clean")
        self.assertEqual(state.validate_state(v2), [], "v2 fixture validates clean")

    def test_state_copy_in_later_worktree_reads_without_rewrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "specs" / "003-v3-shape" / "factory" / "state.json"
            copy.parent.mkdir(parents=True)
            original = (FIXTURES / "state-v3.json").read_text()
            copy.write_text(original)
            loaded, error = state.read_state(copy)
            self.assertIsNone(error)
            self.assertEqual(state.validate_state(loaded), [])
            self.assertEqual(
                copy.read_text(), original, "reading never rewrites the file"
            )


def open_round(qid):
    return {
        "questions": [{"id": qid, "text": "Pick", "recommended": "A"}],
        "answers": {},
    }


def answered_round(qid):
    return {
        "questions": [{"id": qid, "text": "Pick", "recommended": "A"}],
        "answers": {qid: {"answer": "A", "at": "2026-10-23T10:00:00Z", "auto": True}},
    }


class ValidationTests(unittest.TestCase):
    def violations(self, mutate):
        loaded = fixture("state-v4.json")
        mutate(loaded)
        return state.validate_state(loaded)

    def test_vocabulary_violations_carry_location(self):
        found = self.violations(
            lambda s: (
                s.__setitem__("status", "finished"),
                s["history"][1].__setitem__("event", "round-1-complete"),
                s["timeline"][0].__setitem__("kind", "approval"),
                s.__setitem__("stage", "deployed"),
            )
        )
        locations = {v["location"]: v["reason"] for v in found}
        self.assertIn("status", locations)
        self.assertIn("history[1].event", locations)
        self.assertIn("timeline[0].kind", locations)
        self.assertIn("stage", locations)

    def test_timestamp_violations_carry_location(self):
        found = self.violations(
            lambda s: (
                s["history"][0].__setitem__(
                    "at", "2026-10-24T00:00:00Z"
                ),  # after later entries
                s["ledger"][0].__setitem__("duration_ms", -5),
                s["timeline"][1].__setitem__("at", "2026-10-22T00:00:00Z"),
            )
        )
        locations = {v["location"] for v in found}
        self.assertIn(
            "history[1].at", locations, "history[1] is the entry that goes backwards"
        )
        self.assertIn("ledger[0].duration_ms", locations)
        self.assertIn("timeline[1].at", locations)

    def test_ended_before_started_is_reported(self):
        found = self.violations(
            lambda s: s.__setitem__("ended_at", "2026-10-22T00:00:00Z")
        )
        self.assertTrue(any(v["location"] == "ended_at" for v in found))

    def test_required_fields_per_stage(self):
        found = self.violations(lambda s: s.pop("commands"))
        self.assertTrue(any(v["location"] == "commands" for v in found))
        pr_missing = self.violations(
            lambda s: (
                s.__setitem__("status", "pr-open"),
                s.__setitem__("ended_at", None),
            )
        )
        self.assertTrue(any(v["location"] == "pr_url" for v in pr_missing))
        self.assertTrue(any(v["location"] == "ended_at" for v in pr_missing))

    def test_relay_answer_keys_must_match_question_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            loaded = fixture("state-v2.json")
            loaded["relay"]["rounds"][0]["answers"]["Q9"] = "orphan"
            path.write_text(json.dumps(loaded))
            found = state.validate_state(loaded)
            self.assertTrue(any("Q9" in v["location"] for v in found))

    def test_clean_fixtures_report_zero_violations(self):
        for name in (
            "state-v1.json",
            "state-v2.json",
            "state-v3.json",
            "state-v4.json",
            "state-v5.json",
        ):
            self.assertEqual(state.validate_state(fixture(name)), [], name)

    def test_null_relay_and_fully_answered_relay_conform(self):
        self.assertEqual(self.violations(lambda s: s.__setitem__("relay", None)), [])
        answered = self.violations(
            lambda s: s.__setitem__(
                "relay",
                {
                    "stage": "plan",
                    "rounds": [answered_round("Q5"), answered_round("Q6")],
                },
            )
        )
        self.assertEqual(
            answered, [], "a fully answered relay awaiting checkpoint conforms"
        )

    def test_several_open_rounds_report_at_relay(self):
        found = self.violations(
            lambda s: s.__setitem__(
                "relay",
                {"stage": "plan", "rounds": [open_round("Q7"), open_round("Q8")]},
            )
        )
        self.assertTrue(
            any(v["location"] == "relay" for v in found),
            "several open rounds are reported at relay",
        )

    def test_unanswered_questions_in_a_non_last_round_report_at_the_round(self):
        found = self.violations(
            lambda s: s.__setitem__(
                "relay",
                {"stage": "plan", "rounds": [open_round("Q7"), answered_round("Q6")]},
            )
        )
        self.assertTrue(
            any(v["location"] == "relay.rounds[0]" for v in found),
            "the early open round is named",
        )
        self.assertFalse(
            any(v["location"] == "relay" for v in found),
            "a single open round is not reported at relay",
        )


class IssueValidationTests(unittest.TestCase):
    """Schema v5 `issues[]`: closed vocabularies naming the offending location
    and the `partial_return` mark rules (data-model.md, Session issue)."""

    def violations(self, mutate):
        loaded = fixture("state-v5.json")
        mutate(loaded)
        return state.validate_state(loaded)

    def locations(self, mutate):
        return {v["location"]: v["reason"] for v in self.violations(mutate)}

    def test_unknown_kind_names_the_record(self):
        found = self.locations(lambda s: s["issues"][0].__setitem__("kind", "crash"))
        self.assertIn("issues[0].kind", found)

    def test_unknown_overrun_cause_names_the_record(self):
        found = self.locations(lambda s: s["issues"][0].__setitem__("cause", "slow"))
        self.assertIn("issues[0].cause", found)

    def test_missing_cause_on_overrun_names_the_record(self):
        found = self.locations(lambda s: s["issues"][0].__setitem__("cause", None))
        self.assertIn("issues[0].cause", found)

    def test_non_null_cause_on_non_overrun_kind_refused(self):
        found = self.locations(
            lambda s: s["issues"][2].__setitem__("cause", "test-loop")
        )
        self.assertIn("issues[2].cause", found)

    def test_partial_return_refused_on_non_overrun_retry_kinds(self):
        found = self.locations(
            lambda s: s["issues"][2].__setitem__("partial_return", True)
        )
        self.assertIn("issues[2].partial_return", found)

    def test_partial_return_refused_on_never_stopped_roles(self):
        found = self.locations(
            lambda s: s["issues"][0].__setitem__("role", "review-judge")
        )
        self.assertIn("issues[0].partial_return", found)

    def test_non_boolean_partial_return_refused(self):
        found = self.locations(
            lambda s: s["issues"][0].__setitem__("partial_return", "yes")
        )
        self.assertIn("issues[0].partial_return", found)

    def test_negative_duration_and_bad_timestamp_name_the_record(self):
        found = self.locations(
            lambda s: (
                s["issues"][0].__setitem__("duration_ms", -1),
                s["issues"][1].__setitem__("at", "not-a-time"),
            )
        )
        self.assertIn("issues[0].duration_ms", found)
        self.assertIn("issues[1].at", found)

    def test_issues_not_a_list_is_reported(self):
        found = self.locations(lambda s: s.__setitem__("issues", "nope"))
        self.assertIn("issues", found)


class ReplayVocabularyTests(unittest.TestCase):
    """FR-019: tools/tests/replay.py resolves its timestamp parsing and
    vocabularies from factory_cli.state, not private copies."""

    def test_replay_shares_the_state_vocabularies(self):
        self.assertIs(replay.parse_iso, state.parse_iso)
        self.assertIs(replay.TIMELINE_KINDS, state.TIMELINE_KINDS)
        self.assertIs(replay.HISTORY_EVENTS, state.HISTORY_EVENTS)
        self.assertTrue(
            set(replay.AGENT_STAGES) <= set(state.STAGES),
            "the agent stages come from the shared stage vocabulary",
        )


class WriteTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "state.json"

    def test_atomic_write_leaves_no_debris_and_complete_content(self):
        written = state.write_state(self.path, fixture("state-v3.json"))
        self.assertEqual(written["version"], 5)
        on_disk = json.loads(self.path.read_text())
        self.assertEqual(on_disk, written)
        leftovers = [
            p.name for p in self.path.parent.iterdir() if p.name != "state.json"
        ]
        self.assertEqual(leftovers, [], "no temp files left behind")

    def test_first_write_upgrades_to_the_current_version(self):
        written = state.write_state(self.path, fixture("state-v1.json"))
        self.assertEqual(written["version"], state.VERSION)
        self.assertEqual(written["decisions"], [])
        # a v3 ledger entry gains its derived spawn interval
        v3 = state.write_state(
            Path(self.tmp.name) / "v3.json", fixture("state-v3.json")
        )
        entry = v3["ledger"][0]
        self.assertEqual(entry["started_at"], entry["at"])
        self.assertEqual(entry["ended_at"], "2026-10-22T14:03:43Z")

    def test_first_write_upgrades_to_v5_additively(self):
        """Schema v5: `issues[]` the only new top-level key; every v4 key keeps
        its name and shape (data-model.md, State schema change)."""
        written = state.write_state(self.path, fixture("state-v4.json"))
        v4 = fixture("state-v4.json")
        self.assertEqual(written["version"], 5)
        self.assertEqual(written["issues"], [])
        self.assertEqual(set(written) - set(v4), {"issues"})
        for key, value in v4.items():
            self.assertEqual(
                written[key],
                value if key != "version" else 5,
                f"v4 key '{key}' keeps its name and shape",
            )

    def test_append_only_issues_never_rewritten(self):
        first = fixture("state-v5.json")
        state.write_state(self.path, first)
        trimmed = fixture("state-v5.json")
        trimmed["issues"] = trimmed["issues"][1:]  # dropped the earliest record
        with self.assertRaises(state.StateError):
            state.write_state(self.path, trimmed)
        self.assertEqual(
            json.loads(self.path.read_text())["issues"],
            first["issues"],
            "a refused write leaves the recorded issues untouched",
        )
        grown = fixture("state-v5.json")
        grown["issues"] = first["issues"] + [
            {
                "at": "2026-10-23T11:00:00Z",
                "kind": "halt",
                "stage": "implement",
                "role": "orchestrator",
                "cause": None,
                "detail": "three partial returns with no new commit",
                "duration_ms": 1000,
                "commit": "bbb0007",
                "partial_return": False,
            }
        ]
        state.write_state(self.path, grown)  # appending is allowed
        self.assertEqual(len(json.loads(self.path.read_text())["issues"]), 4)

    def test_write_refuses_invalid_state_and_keeps_file(self):
        good = state.write_state(self.path, fixture("state-v4.json"))
        bad = fixture("state-v4.json")
        bad["status"] = "finished"
        with self.assertRaises(state.StateError):
            state.write_state(self.path, bad)
        self.assertEqual(json.loads(self.path.read_text()), good)

    def test_append_only_decisions_never_rewritten(self):
        first = fixture("state-v4.json")
        state.write_state(self.path, first)
        trimmed = fixture("state-v4.json")
        trimmed["decisions"] = trimmed["decisions"][1:]  # dropped the earliest entry
        with self.assertRaises(state.StateError):
            state.write_state(self.path, trimmed)
        self.assertEqual(
            json.loads(self.path.read_text())["decisions"],
            first["decisions"],
            "a refused write leaves the recorded decisions untouched",
        )
        grown = fixture("state-v4.json")
        grown["decisions"] = first["decisions"] + [
            {
                "stage": "review",
                "question": "Q2",
                "answer": "ok",
                "auto": True,
                "at": "2026-10-23T11:00:00Z",
                "kind": "answer",
            }
        ]
        state.write_state(self.path, grown)  # appending is allowed
        self.assertEqual(len(json.loads(self.path.read_text())["decisions"]), 3)

    def test_write_state_reapplies_the_mutation_to_the_current_state(self):
        """Read-modify-write is exclusive: a write based on a stale read
        re-applies its mutation to the state current under the lock, never
        dropping a change another writer landed in between."""
        state.write_state(self.path, fixture("state-v4.json"))
        stale_read, _ = state.read_state(self.path)

        def other_writer(s):
            s["timeline"] = (s.get("timeline") or []) + [
                {
                    "at": "2026-10-23T12:00:00Z",
                    "kind": "notice",
                    "stage": s.get("stage"),
                    "summary": "landed while we worked",
                    "answered_at": None,
                    "latency_ms": None,
                }
            ]
            return s

        state.write_state(self.path, stale_read, mutate=other_writer)

        def our_writer(s):
            s["history"] = (s.get("history") or []) + [
                {
                    "at": "2026-10-23T12:30:00Z",
                    "stage": s.get("stage"),
                    "event": "resumed",
                    "commit": None,
                    "harness": s.get("harness"),
                }
            ]
            return s

        state.write_state(self.path, stale_read, mutate=our_writer)
        final = json.loads(self.path.read_text())
        self.assertTrue(
            any(
                e.get("summary") == "landed while we worked" for e in final["timeline"]
            ),
            "a stale read must not drop another writer's landed change",
        )
        self.assertEqual(final["history"][-1]["event"], "resumed")


if __name__ == "__main__":
    unittest.main()
