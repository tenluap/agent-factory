# Quickstart: UI Designer Role

1. Build: `export FACTORY_HOME="$(mktemp -d)"; for h in claude-code opencode codex copilot zcode; do python3 tools/render.py "$h" || exit 1; done`
2. Drift gate: `test -z "$(git status --porcelain -- dist/)"`
3. Test: `python3 -m unittest discover -s tools`
4. Check each harness dist contains `factory-ui-designer` with tier standard and write access.
