# Quickstart: validate adoption

## Automated

```bash
python3 -m unittest discover -s tools          # includes tools/tests/test_adopt.py
export FACTORY_HOME="$(mktemp -d)"; for h in claude-code opencode codex copilot zcode; do python3 tools/render.py "$h" || exit 1; done; bash -n install.sh
test -z "$(git ls-files -- dist/)"
```

`test_adopt.py` covers every seam in [plan.md](plan.md) "Test seams" in throwaway `Sandbox` repositories.

## End to end (DESIGN.md validation plan, after merge, as for spec 021)

1. In a scratch repository, write `specs/007-x/spec.md` and `plan.md` on branch `007-x`, commit, switch the main checkout to `main`.
2. `/factory adopt 007-x --dry-run`: report shows shape `branch`, inferred stage `tasks`; `git status`, refs and `git worktree list` unchanged.
3. `/factory adopt 007-x`: summary of the spec, open gaps, chain (`full` recommended), stage confirmation; accept.
4. Expect worktree `<repo>/../<repo-name>-factory/007-x` on `007-x`, one commit `factory: adopt 007-x`, and the run continuing at `tasks`.
5. Decline a second attempt on another spec: nothing exists in the repository afterwards.
6. Carry the run to the approver: the screen states the adoption; reviewers list pre-adoption commits without ENG-2 blockers; analyze lists checked tasks as pre-adoption (SC-001, SC-005).
