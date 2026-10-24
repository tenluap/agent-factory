# Quickstart: validate the ZCode adapter

Prerequisites: Python 3, git, this worktree, and (for the manual steps) ZCode 3.16.x.

## 1. Red check (before the adapter exists)

```bash
python3 tools/render.py --list                 # expect: no zcode line
python3 tools/render.py zcode                  # expect: unknown harness 'zcode'
```

## 2. Track dist/, build every harness canonically, then gate

The render is environment-dependent: `tools/render.py` substitutes each adapter's resolved `{home}` into
every agent body and merges `${FACTORY_HOME}/config.json` model overrides into the frontmatter. The
committed distribution is therefore always produced with every harness home variable unset *and*
`FACTORY_HOME` pointed at a path that holds no `config.json` — the **canonical render environment**
(FR-018). Unsetting `FACTORY_HOME` is not enough: the renderer falls back to `~/.factory/config.json`,
which most contributors have, and still merges `models.<harness>` into the frontmatter. Define the
wrapper once, and quote it identically everywhere:

```bash
CANON='env -u CLAUDE_HOME -u CODEX_HOME -u COPILOT_HOME -u ZCODE_HOME -u XDG_CONFIG_HOME FACTORY_HOME=/nonexistent'
RENDER='for h in $(python3 tools/render.py --list); do python3 tools/render.py "$h" || exit 1; done'

grep -c '^/dist/$' .gitignore                  # expect: 0 — the ignore line is removed (FR-018)
$CANON sh -c "$RENDER"
git add dist/ && git commit -m "render all five harnesses"
git ls-files dist/ | wc -l                     # expect: > 0 — the distribution is tracked

# the gate, run after any later render:
$CANON sh -c "$RENDER"
git diff --exit-code -- dist/                  # expect: clean; non-zero whenever source and render diverge
```

Without `$CANON`, a contributor who has `XDG_CONFIG_HOME`, `CLAUDE_HOME`, `CODEX_HOME`, `COPILOT_HOME`,
`ZCODE_HOME` or a `models.<harness>` override set rewrites paths and frontmatter in the rendered tree, and the gate fails
spuriously. Recover with `git checkout -- dist/` and re-render canonically.

`--list` must now include `zcode` (Seam 1) and `dist/zcode/` must exist (Seam 2).

Red proof for Seam 4: touch a source file the render copies (for example add a line to
`adapters/zcode/harness.md`), re-render, and `git diff --exit-code -- dist/` exits non-zero. Before the
`.gitignore` change the same command always exited 0 on an ignored, untracked directory.

## 3. Rendered output checks

```bash
ls dist/zcode/agents | wc -l                   # expect: equals `ls core/roles/*.md | wc -l` (9)
ls dist/zcode/skill/references/harness/        # expect: zcode.md plus every other adapter
python3 - <<'PY'
import pathlib, re
for p in sorted(pathlib.Path("dist/zcode/agents").glob("factory-*.md")):
    m = re.match(r"---\n(.*?)\n---\n", p.read_text(), re.S)
    assert m, f"{p}: no frontmatter"
    keys = dict(line.split(": ", 1) for line in m.group(1).splitlines())
    assert set(keys) == {"name", "description", "tools"}, (p, sorted(keys))   # FR-004
    assert keys["name"] == p.stem, p
    assert keys["description"] and keys["tools"], p
    assert "<F>" not in p.read_text(), p
print("frontmatter ok")
PY
```

That block is Seam 3; step 2's `git diff --exit-code -- dist/` is Seam 4 (no other harness drifts).

## 4. Install and run in ZCode (manual, SC-001/SC-002)

`install.sh` renders before it installs, so each command below rewrites the tracked `dist/` tree with
environment-dependent paths. Restore the canonical render after every one of them:

```bash
./install.sh --harness zcode
ls ~/.zcode/skills/factory ~/.zcode/agents/factory-*.md
git checkout -- dist/ && git diff --exit-code -- dist/        # back to the canonical render

ZCODE_HOME=/tmp/zc ./install.sh --harness zcode && ls /tmp/zc/agents   # env override
git checkout -- dist/ && git diff --exit-code -- dist/        # expect: clean again (FR-018)
```

Start a fresh ZCode session in a target repository and run `/factory <feature>`. Expect: preflight
recognises ZCode, roles run as subagents, grilling questions appear in the factory's Markdown layout.
If `.specify/` is missing, the offered command is
`specify init --here --integration zcode --integration-options="--skills"`, which writes
`.zcode/skills/speckit-*/SKILL.md`.

## 5. Cross-harness resume (manual, SC-005)

```bash
# ZCode → another harness
# in ZCode: /factory <feature>, answer grilling, let it reach a checkpoint, stop the session
# in Claude Code (or any installed harness): /factory  → resume the run
# expect: it continues from the stage recorded in specs/<branch>/factory/state.json, nothing re-asked
#
# other harness → ZCode: repeat in the opposite direction with a second feature
```

Both directions must resume at the recorded stage with no loss of progress; `state.json` is
harness-neutral, so the only ZCode-specific part is the adapter the resuming session picks.

## 6. Documentation checks (FR-016)

`README.md` harness table has a ZCode row (install, `/factory <feature>`, `~/.zcode/agents/factory-*.md`)
and the requirements list names ZCode's SpecKit setup; `DESIGN.md` lists `zcode` under "Adapters today"
and its spec-kit setup line reads `specify init --here <harness.speckit_init>` with each adapter stating
its own arguments; `CONTEXT.md`'s Harness definition names ZCode; `docs/adr/0005-...md` records the
tracked-distribution decision.

## 7. Cleanup

```bash
./install.sh --harness zcode --uninstall
```
