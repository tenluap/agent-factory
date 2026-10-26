"""State seam tests: the `factory_cli.state` module API (read, validate, write).

Covers versions 1-4 read acceptance, legacy relay shapes, state copies in later
worktrees, vocabulary and timestamp violations with their location, the atomic
write, the first-write upgrade to v4 and the append-only `decisions` guard.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

CORE_BIN = Path(__file__).resolve().parents[2] / "core" / "skills" / "factory" / "bin"
sys.path.insert(0, str(CORE_BIN))

from factory_cli import state  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def fixture(name):
    return json.loads((FIXTURES / name).read_text())


class ReadAcceptanceTests(unittest.TestCase):
    def test_read_accepts_versions_one_through_four(self):
        for name, version in (
            ("state-v1.json", 1),
            ("state-v2.json", 2),
            ("state-v3.json", 3),
            ("state-v4.json", 4),
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
        ):
            self.assertEqual(state.validate_state(fixture(name)), [], name)


class WriteTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "state.json"

    def test_atomic_write_leaves_no_debris_and_complete_content(self):
        written = state.write_state(self.path, fixture("state-v3.json"))
        self.assertEqual(written["version"], 4)
        on_disk = json.loads(self.path.read_text())
        self.assertEqual(on_disk, written)
        leftovers = [
            p.name for p in self.path.parent.iterdir() if p.name != "state.json"
        ]
        self.assertEqual(leftovers, [], "no temp files left behind")

    def test_first_write_upgrades_to_v4(self):
        written = state.write_state(self.path, fixture("state-v1.json"))
        self.assertEqual(written["version"], 4)
        self.assertEqual(written["decisions"], [])
        # a v3 ledger entry gains its derived spawn interval
        v3 = state.write_state(
            Path(self.tmp.name) / "v3.json", fixture("state-v3.json")
        )
        entry = v3["ledger"][0]
        self.assertEqual(entry["started_at"], entry["at"])
        self.assertEqual(entry["ended_at"], "2026-10-22T14:03:43Z")

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


if __name__ == "__main__":
    unittest.main()
