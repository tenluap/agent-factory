# Quickstart: validate `factory drop`

1. Tests: `python3 -m unittest discover -s tools` — `tools/tests/test_drop.py` passes.
2. Build gate: `export FACTORY_HOME="$(mktemp -d)"; for h in claude-code opencode codex copilot zcode; do python3 tools/render.py "$h"; done; test -z "$(git status --porcelain -- dist/)"`.
3. Manual, in a throwaway repo with a worktree run at `pr-open`:
   - `FACTORY_HOME=$(mktemp -d) python3 <F>/bin/factory drop` from the worktree → JSON with `archive`, `pr_url`, `totals_sentence`; time it (SC-004: under 5 s).
   - `git log -1 --stat` → `factory: drop run artifacts`, only `specs/<branch>/factory/*` deleted.
   - `diff -r <archive> <(git show HEAD~1:specs/<branch>/factory)` equivalent: archive matches the pre-drop folder.
   - Run `factory drop` again → exit 1, "no run to drop".
4. Pen run: add `specs/<branch>/factory/design/x.json` and a `docs/design-code-map.json` referencing it, drop → `docs/design/<branch>/x.json` exists, the map points there, same commit. Pre-create `docs/design/<branch>/` → drop refuses, nothing changes.
5. Refusal: on a `running` run, `factory drop` → exit 1 naming `running`; `archive/` unchanged.
