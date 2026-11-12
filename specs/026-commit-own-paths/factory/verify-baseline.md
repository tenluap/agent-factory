# Verify baseline

User decision `verify-baseline` (grill): verify passes when the run adds no failures beyond this list. code-build and fixer never repair, skip or edit these tests.

- Base commit: `0c3bf71` (origin/main), worktree before any run change.
- Command: `python3 -m unittest discover -s tools` - Ran 631 tests in 330.8s, FAILED (failures=8), 2026-11-12T09:31:49Z..2026-11-12T09:37:20Z.
- CI on 0c3bf71 (run 42968500158) fails the first 7 below; `test_exceptions_are_still_needed (graphify)` fails only locally (graphify installed in this environment).

## Failing on base

- test_defaults_match_all_adapters (tests.test_render_models.AdapterModelsParityTests.test_defaults_match_all_adapters) (harness='opencode')
- test_shipped_model_policy_preserves_explicit_tiers (tests.test_render_models.ModelPolicyTests.test_shipped_model_policy_preserves_explicit_tiers)
- test_retro_role_renders_read_only_for_every_harness (tests.test_render_models.ReadOnlyConformanceTests.test_retro_role_renders_read_only_for_every_harness)
- test_every_lock_entry_has_a_folder_under_its_frontmatter_name (tests.test_skill_library.SkillLibraryLayoutTests.test_every_lock_entry_has_a_folder_under_its_frontmatter_name) (name='create-project-agents-file')
- test_every_lock_entry_has_a_folder_under_its_frontmatter_name (tests.test_skill_library.SkillLibraryLayoutTests.test_every_lock_entry_has_a_folder_under_its_frontmatter_name) (name='prompt-optimiser')
- test_exceptions_are_still_needed (tests.test_skill_library.SkillLibraryLayoutTests.test_exceptions_are_still_needed) (name='graphify')
- test_local_skills_are_edited_in_place (tests.test_skill_library.SkillLibraryLayoutTests.test_local_skills_are_edited_in_place) (name='create-project-agents-file')
- test_local_skills_are_edited_in_place (tests.test_skill_library.SkillLibraryLayoutTests.test_local_skills_are_edited_in_place) (name='prompt-optimiser')
