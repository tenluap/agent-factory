"""Envelope seam tests: the `factory_cli.checks` output-shape checker (FR-007).

The fenced examples in `references/protocol.md` (envelope) and
`references/findings.md` (reviewer report, judge verdict) are the passing
fixtures, extracted from the references themselves so code and prose stay
aligned; one malformed variant per shape is refused with its location.
"""

import json
import re
import sys
import unittest
from pathlib import Path

CORE_BIN = Path(__file__).resolve().parents[2] / "core" / "skills" / "factory" / "bin"
sys.path.insert(0, str(CORE_BIN))

from factory_cli import checks  # noqa: E402

REFERENCES = (
    Path(__file__).resolve().parents[2] / "core" / "skills" / "factory" / "references"
)


def fenced_blocks(path):
    text = Path(path).read_text()
    return [
        json.loads(m.group(1)) for m in re.finditer(r"```json\n(.*?)```", text, re.S)
    ]


def example(path, key):
    for block in fenced_blocks(path):
        if key in block:
            return block
    raise AssertionError(f"no fenced block with key '{key}' in {path}")


ENVELOPE = example(REFERENCES / "protocol.md", "status")
REVIEWER = example(REFERENCES / "findings.md", "reviewer")
VERDICT = example(REFERENCES / "findings.md", "verdict")


class ReferenceExamplesPass(unittest.TestCase):
    def test_envelope_example_is_valid(self):
        self.assertEqual(checks.block_problems(ENVELOPE, "envelope"), [])

    def test_reviewer_report_example_is_valid(self):
        self.assertEqual(checks.block_problems(REVIEWER, "reviewer"), [])

    def test_judge_verdict_example_is_valid(self):
        self.assertEqual(checks.block_problems(VERDICT, "verdict"), [])

    def test_shapes_are_detected(self):
        self.assertEqual(checks.detect_shape(ENVELOPE), "envelope")
        self.assertEqual(checks.detect_shape(REVIEWER), "reviewer")
        self.assertEqual(checks.detect_shape(VERDICT), "verdict")


class MalformedVariantsRefused(unittest.TestCase):
    def problems(self, shape, mutate):
        import copy

        block = copy.deepcopy(
            {"envelope": ENVELOPE, "reviewer": REVIEWER, "verdict": VERDICT}[shape]
        )
        mutate(block)
        return checks.block_problems(block, shape)

    def test_envelope_off_vocabulary_status(self):
        found = self.problems("envelope", lambda b: b.__setitem__("status", "finished"))
        self.assertTrue(any(p["location"] == "status" for p in found))

    def test_envelope_needs_input_without_questions(self):
        found = self.problems(
            "envelope",
            lambda b: (
                b.__setitem__("status", "needs_input"),
                b.__setitem__("questions", None),
            ),
        )
        self.assertTrue(any(p["location"] == "questions" for p in found))

    def test_envelope_failed_without_error(self):
        found = self.problems(
            "envelope",
            lambda b: (b.__setitem__("status", "failed"), b.__setitem__("error", None)),
        )
        self.assertTrue(any(p["location"] == "error" for p in found))

    def test_reviewer_finding_without_evidence(self):
        found = self.problems("reviewer", lambda b: b["findings"][0].pop("evidence"))
        self.assertTrue(any("findings[0].evidence" == p["location"] for p in found))

    def test_reviewer_finding_with_non_boolean_blocking(self):
        found = self.problems(
            "reviewer", lambda b: b["findings"][0].__setitem__("blocking", "yes")
        )
        self.assertTrue(any(p["location"] == "findings[0].blocking" for p in found))

    def test_verdict_off_vocabulary_verdict(self):
        found = self.problems("verdict", lambda b: b.__setitem__("verdict", "maybe"))
        self.assertTrue(any(p["location"] == "verdict" for p in found))

    def test_verdict_sources_must_be_strings(self):
        found = self.problems(
            "verdict", lambda b: b["confirmed_blocking"][0].__setitem__("sources", [3])
        )
        self.assertTrue(
            any("confirmed_blocking[0].sources" == p["location"] for p in found)
        )

    def test_non_object_block_is_refused(self):
        found = checks.block_problems(["not", "an", "object"], "envelope")
        self.assertTrue(found)


class OverrunShapeTests(unittest.TestCase):
    """A deadline-stopped `partial` envelope carries `overrun`:
    an object with a known cause and a non-empty detail (FR-002)."""

    def problems(self, mutate):
        import copy

        block = copy.deepcopy(ENVELOPE)
        block["status"] = "partial"
        mutate(block)
        return checks.block_problems(block, "envelope")

    def locations(self, mutate):
        return {p["location"]: p["reason"] for p in self.problems(mutate)}

    def test_partial_without_overrun_is_valid(self):
        self.assertEqual(self.problems(lambda b: None), [])

    def test_valid_overrun_report(self):
        found = self.problems(
            lambda b: b.__setitem__(
                "overrun", {"cause": "test-loop", "detail": "41s past deadline"}
            )
        )
        self.assertEqual(found, [])

    def test_overrun_must_be_an_object(self):
        found = self.locations(lambda b: b.__setitem__("overrun", "ran long"))
        self.assertIn("overrun", found)

    def test_unknown_cause_refused(self):
        found = self.locations(
            lambda b: b.__setitem__("overrun", {"cause": "slow", "detail": "d"})
        )
        self.assertIn("overrun.cause", found)

    def test_empty_or_missing_detail_refused(self):
        for detail in (None, ""):
            found = self.locations(
                lambda b, d=detail: b.__setitem__(
                    "overrun", {"cause": "other", "detail": d}
                )
            )
            self.assertIn("overrun.detail", found, repr(detail))


class ExtractFinalBlock(unittest.TestCase):
    def test_the_final_fenced_block_is_the_output(self):
        text = (
            'prose\n```json\n{"stage": "earlier"}\n```\nmore\n```json\n'
            + json.dumps(ENVELOPE)
            + "\n```\n"
        )
        block, error = checks.extract_block(text)
        self.assertIsNone(error)
        self.assertEqual(block["status"], "done")

    def test_no_fenced_block_is_an_error(self):
        block, error = checks.extract_block("just prose")
        self.assertIsNone(block)
        self.assertIn("no fenced json block", error)

    def test_unparsable_block_is_an_error(self):
        block, error = checks.extract_block("```json\n{oops\n```")
        self.assertIsNone(block)
        self.assertIn("parse", error)


class EnvelopeCliTests(unittest.TestCase):
    def setUp(self):
        from tests import Sandbox

        self.box = Sandbox()
        self.addCleanup(self.box.close)

    def test_envelope_check_passes_reference_examples(self):
        out = self.box.write_temp(
            "envelope.md", "```json\n" + json.dumps(ENVELOPE) + "\n```"
        )
        result = self.box.cli("envelope", "check", out)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_envelope_check_refuses_malformed_with_location(self):
        bad = dict(ENVELOPE, status="finished")
        out = self.box.write_temp("bad.md", "```json\n" + json.dumps(bad) + "\n```")
        result = self.box.cli("envelope", "check", out)
        self.assertEqual(result.returncode, 1)
        self.assertIn("status", result.stderr)

    def test_envelope_check_missing_file(self):
        result = self.box.cli("envelope", "check", "/nonexistent/envelope.md")
        self.assertEqual(result.returncode, 1)


if __name__ == "__main__":
    unittest.main()
