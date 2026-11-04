"""Adopt seam tests: the `adopted` state block and history event (T002).

Later units add the dry-run report, refusals and the write with rollback
through the public `bin/factory adopt` command, over throwaway Sandbox repos.
"""

import sys
import unittest
from pathlib import Path

CORE_BIN = Path(__file__).resolve().parents[2] / "core" / "skills" / "factory" / "bin"
sys.path.insert(0, str(CORE_BIN))

from factory_cli import state  # noqa: E402
from tests import fixture  # noqa: E402

BASE_SHA = "0123456789abcdef0123456789abcdef01234567"


def adopted_state():
    """A v5 run adopted at `analyze`: one adopted entry, no complete entries."""
    run = fixture("state-v5.json")
    run.update(stage="analyze", status="running")
    run.pop("commands", None)
    run["adopted"] = {
        "source": {
            "shape": "branch",
            "branch": "007-x",
            "spec_dir": "specs/007-x",
        },
        "inferred_stage": "tasks",
        "chosen_stage": "analyze",
        "base_commit": BASE_SHA,
    }
    run["history"] = [
        {
            "at": "2026-11-04T10:00:00Z",
            "stage": "analyze",
            "event": "adopted",
            "commit": None,
            "harness": "opencode",
        }
    ]
    return run


def problems_for(mutate):
    run = adopted_state()
    mutate(run)
    return state.validate_state(run)


class AdoptedStateTests(unittest.TestCase):
    def test_adopted_state_at_analyze_validates_clean(self):
        self.assertEqual(state.validate_state(adopted_state()), [])

    def test_state_without_adopted_block_still_validates(self):
        run = fixture("state-v5.json")
        self.assertEqual(state.validate_state(run), [])

    def test_non_object_adopted_names_the_block(self):
        problems = problems_for(lambda run: run.update(adopted="007-x"))
        self.assertEqual([p["location"] for p in problems], ["adopted"])

    def test_off_vocabulary_shape_is_one_problem(self):
        def mutate(run):
            run["adopted"]["source"]["shape"] = "fork"

        problems = problems_for(mutate)
        self.assertEqual([p["location"] for p in problems], ["adopted.source.shape"])

    def test_missing_source_branch_is_one_problem(self):
        def mutate(run):
            del run["adopted"]["source"]["branch"]

        problems = problems_for(mutate)
        self.assertEqual([p["location"] for p in problems], ["adopted.source.branch"])

    def test_missing_source_spec_dir_is_one_problem(self):
        def mutate(run):
            run["adopted"]["source"]["spec_dir"] = ""

        problems = problems_for(mutate)
        self.assertEqual(
            [p["location"] for p in problems], ["adopted.source.spec_dir"]
        )

    def test_inferred_stage_outside_adopt_stages_is_one_problem(self):
        def mutate(run):
            run["adopted"]["inferred_stage"] = "implement"

        problems = problems_for(mutate)
        self.assertEqual(
            [p["location"] for p in problems], ["adopted.inferred_stage"]
        )

    def test_chosen_stage_outside_adopt_stages_is_one_problem(self):
        def mutate(run):
            run["adopted"]["chosen_stage"] = "grill"

        problems = problems_for(mutate)
        self.assertEqual([p["location"] for p in problems], ["adopted.chosen_stage"])

    def test_uppercase_base_commit_is_one_problem(self):
        def mutate(run):
            run["adopted"]["base_commit"] = BASE_SHA.upper()

        problems = problems_for(mutate)
        self.assertEqual([p["location"] for p in problems], ["adopted.base_commit"])

    def test_short_base_commit_is_one_problem(self):
        def mutate(run):
            run["adopted"]["base_commit"] = BASE_SHA[:39]

        problems = problems_for(mutate)
        self.assertEqual([p["location"] for p in problems], ["adopted.base_commit"])

    def test_adopted_history_entry_without_block_is_one_problem(self):
        def mutate(run):
            del run["adopted"]

        problems = problems_for(mutate)
        self.assertEqual(len(problems), 1)
        self.assertIn("adopted", problems[0]["reason"])
        self.assertEqual(problems[0]["location"], "history[0].event")

    def test_adopted_event_is_in_history_vocabulary(self):
        self.assertIn("adopted", state.HISTORY_EVENTS)
        self.assertEqual(
            state.ADOPT_SHAPES, ("branch", "remote-branch", "default-branch")
        )
        self.assertEqual(
            state.ADOPT_STAGES, ("specify", "plan", "tasks", "analyze")
        )


if __name__ == "__main__":
    unittest.main()
