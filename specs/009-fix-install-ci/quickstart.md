# Validation guide

Run from the feature worktree with Python 3, Bash, and Git available. No pre-generated checkout dist or additional dependency is required.

```sh
python3 -m unittest discover -s tools -p test_install.py
python3 -m unittest discover -s tools
for h in claude-code opencode codex copilot zcode; do
  python3 tools/render.py "$h" || exit
done
bash -n install.sh
test -z "$(git status --porcelain -- dist/)"
```

Before correction, the focused command has two failures naming nonexistent FACTORY_HOME. After correction, focused and full suites must pass. All five renders and both final checks must succeed. The porcelain check follows repository policy but ignored dist content is verified by generation and existing render tests rather than porcelain visibility alone.

Review [installer outcomes](contracts/installer-tests.md) for the retained assertions and [fixture ownership](data-model.md) for cleanup boundaries.
