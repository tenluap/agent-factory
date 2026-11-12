# Quickstart: validate "commit only what the run wrote"

Prerequisites: Python 3, git, this branch checked out.

1. Run the suite: `python3 -m unittest discover -s tools`.
   Expected: no failures beyond the 7 already failing on base 0c3bf71 (`test_render_models`, `test_skill_library`).
2. Focused AC-2 checks: `python3 -m unittest tools.tests.test_commands tools.tests.test_adopt`.
   Expected: the checkpoint, resume and adopt tests with an unrelated staged deletion of `pnpm-lock.yaml` pass: the deletion is absent from each factory commit and still staged afterwards.
3. Focused prose checks (AC-3, AC-4, AC-5): `python3 -m unittest tools.tests.test_commit_scope`.
   Expected: the real core text has no gaps, and each mutated copy reports exactly its removed marker.
4. Build: render all five harnesses with `tools/render.py`, confirm `git ls-files -- dist/` is empty, and run `bash -n install.sh` (the run's `commands.build`).
   Expected: exit 0.
