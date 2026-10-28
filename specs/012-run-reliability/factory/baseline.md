# Pre-implementation baseline

At base `3cef63f`, before implementation changes:

`python3 -m unittest discover -s tools -p test_render_models.py` ran 19 tests and failed 3:

- `ModelPolicyTests.test_exactly_claude_code_ships_models`: expects sonnet, Claude Code ships haiku.
- `ModelPolicyTests.test_readme_statement_matches_adapters`: expects Codex adapter models to be empty, adapter has explicit deep/standard selections.
- `ReportTests.test_models_report_without_config_prints_defaults`: expects inherited OpenCode model, current report shows explicit adapter models.

No errors with the documented discovery path. An earlier direct module invocation caused two import-path errors; those were invocation errors and are not baseline defects.

Resolve the policy mismatch explicitly in the plan relay. Preserve shipped model selections unless the user chooses otherwise.
