# Validation Guide

Work in `012-run-reliability`; use temporary fixture checkouts and throwaway remotes for native behavior trials. Read [contracts/workflow.md](contracts/workflow.md) and the confirmed S1–S4 scope in [plan.md](plan.md).

1. Read the accepted plan Q1/Q2 decisions: all S1–S4 cases are confirmed; preserve current shipped model selections and align stale policy/tests. The existing model-policy baseline is recorded in [factory/baseline.md](factory/baseline.md). Keep that evidence; rerun `python3 -m unittest discover -s tools -p test_render_models.py` after the policy/test alignment and require it to pass.
2. Follow `conformance/run-reliability.md` once implemented. Exercise S1 inventory includes/excludes/error/unverified with synthetic IDs; confirm exact selections survive and rejected setup creates no resources. Never modify real credentials.
3. Exercise S2 on the tiny fixture: red → implementation → one green commit; interrupt after red and resume; then inspect complete, partial and ambiguous legacy pairs. Inspect real boxes, commits and red proof.
4. Exercise S3: omitted git-failure scope blocks analyze; expanded scope invalidates confirmation; fast mode waits; explicit acceptance repairs eligibility. Covered/exempt controls proceed.
5. Exercise S4 with a short deadline: hand off at a passing boundary with required suite pending; finish in-flight work and report actual overshoot; resume and verify. Run `python3 -m unittest discover -s tools -p test_budget.py` to preserve ledger and no-progress behavior.
6. Render every harness (`python3 tools/render.py <harness>` for claude-code, opencode, codex, copilot, zcode) and commit distributions with source changes. Run `python3 -m unittest discover -s tools`, `bash -n install.sh`, and `test -z "$(git status --porcelain -- dist/)"`. Record native trial results in `conformance/golden-run-results.md`; unavailable trials remain unverified.

The orchestrator independently repeats the recorded build/test commands before review. A passing render, source assertion or fixture-state test never substitutes for observed native role behavior. Stop at the final factory approval gate; these validation trials do not authorize publication.
