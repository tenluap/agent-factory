# Quickstart: validate the bookkeeping writers

Prerequisite: worktree of `024-orchestrator-gaps`; `F=core/skills/factory`.

1. Full suite: `python3 -m unittest discover -s tools` passes.
2. Build: `export FACTORY_HOME="$(mktemp -d)"; for h in claude-code opencode codex copilot zcode; do python3 tools/render.py "$h" || exit 1; done; bash -n install.sh` succeeds; `test -z "$(git ls-files -- dist/)"`.
3. Counters (fixture run at stage `review`, `factory/reviews/round-1/verdict.json` present): `checkpoint review --next fix` → result `review.round` 1; `checkpoint fix --next review` → `fix_rounds` 1; repeat with `round-2` → 2 and 2. `state.json` never hand-edited.
4. Relay record: on a worktree run in stage `review`, `answer R1-Q1 A --question '{"id":"R1-Q1","title":"Confirm seams","options":[...],"requires_user":true}'` → `factory/relay/review-R1-Q1.md` exists in `git show --stat HEAD`; re-run with `B` → exit 1.
5. Overrun: `ledger-add review spec-conformance --started-at 2026-01-01T00:00:00Z --ended-at 2026-01-01T00:05:19Z --round 2` → issue detail `spec-conformance ran 19s past its 300s budget (319s total) without a self-report`.
6. Budget: `budget code-standards --round 1` → `seconds` 600; `--round 2` → 300; with `--round 1` a 450 s `ledger-add` records no issue.

Contracts: [contracts/cli.md](contracts/cli.md).
