# Quickstart: validate the skill library

Run everything under a throwaway home so no real harness directory changes.

```bash
unset FACTORY_HOME CLAUDE_HOME CODEX_HOME COPILOT_HOME ZCODE_HOME
export HOME="$(mktemp -d)"
export XDG_CONFIG_HOME="$HOME/.config"   # separate line: must expand the new HOME
./install.sh --harness opencode
ls -l "$XDG_CONFIG_HOME/opencode/skills"   # six library links into <repo>/skills/ plus factory
```

Expected: `grilling`, `domain-modeling`, `pr`, `ponytail`, `tdd`, `brainstorming` link into `<repo>/skills/`.

## Add a personal skill

```bash
mkdir -p /tmp/demo && printf -- '---\nname: demo\ndescription: d\n---\n' > /tmp/demo/SKILL.md
./install.sh --harness opencode --add-skill /tmp/demo   # added: ~/.factory/skills/demo
./install.sh --harness opencode --add-skill /tmp/demo   # exists: ..., exit 2
rm -rf ~/.factory/skills/demo && ./install.sh --harness opencode   # removed: .../opencode/skills/demo
```

## Conflict and uninstall

```bash
mkdir "$XDG_CONFIG_HOME/opencode/skills/mine"
./install.sh --harness opencode --uninstall   # library links removed; mine/ and ~/.factory/skills/ untouched
```

## Gates

```bash
python3 -m unittest discover -s tools
for h in claude-code opencode codex copilot zcode; do python3 tools/render.py "$h"; done
test -z "$(git status --porcelain -- dist/)"
```

Contracts: [contracts/install-cli.md](contracts/install-cli.md). Entities: [data-model.md](data-model.md).
