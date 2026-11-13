# Quickstart: validate repo instructions discovery

Run from the worktree root.

## 1. Suite and build

```bash
python3 -m unittest discover -s tools
export FACTORY_HOME="$(mktemp -d)"; for h in claude-code opencode codex copilot zcode; do python3 tools/render.py "$h" || exit 1; done
test -z "$(git ls-files -- dist/)" && bash -n install.sh
```

Expected: all tests pass (including `tools/tests/test_instructions.py`), every harness renders, no tracked `dist/`.

## 2. Read-only report on this repository (SC-005)

```bash
python3 core/skills/factory/bin/factory instructions --ref HEAD > /tmp/a.json
python3 core/skills/factory/bin/factory instructions --ref HEAD > /tmp/b.json
cmp /tmp/a.json /tmp/b.json
python3 -c "import json;i=json.load(open('/tmp/a.json'));k={e['path']:e['kind'] for e in i['entries']};print(k['DESIGN.md'],k['CONTEXT.md'],k['.specify/memory/constitution.md']);print([p for p in k if p.startswith('conformance/')])"
git status --short
```

Expected: `cmp` silent (SC-002); `reference reference always`; `[]`; `docs/adr/*.md` listed as `reference`; `git status` unchanged (nothing written).

## 3. Errors

```bash
python3 core/skills/factory/bin/factory instructions --ref no-such-ref; echo $?   # 5, names the ref
(cd /tmp && python3 "$OLDPWD/core/skills/factory/bin/factory" instructions); echo $?   # 2
```

## 4. Writer and delta (SC-004)

Covered by the sandbox tests: a pending run records `<name>.instructions.json` beside the pending file; a worktree run commits `<spec_dir>/factory/instructions.json`; a re-record after adding, removing and changing one file each reports exactly those three paths.

## 5. Orchestrator text

`core/skills/factory/SKILL.md` step 1 item 5 calls `instructions-record` right after `profile-record`, discloses counts, sizes, delta, notes, the 32 KiB warning and the no-instructions hint (`create-project-agents-file`), reads every `always` entry with `git show <ref>:<path>`, and sources documented build and test commands from every root-scope entry. The text-contract test asserts each.
