# Quickstart: validate the ZCode adapter

Prerequisites: Python 3, git, this worktree, and (for the manual steps) ZCode 3.16.x.

## 1. Red check (before the adapter exists)

```bash
python3 tools/render.py --list                 # expect: no zcode line
python3 tools/render.py zcode                  # expect: unknown harness 'zcode'
```

## 2. Build every harness

```bash
for h in $(python3 tools/render.py --list); do python3 tools/render.py "$h" || exit 1; done
git diff --exit-code -- dist/                  # expect: clean after the dist/ changes are committed
```

`--list` must now include `zcode` (Seam 1) and `dist/zcode/` must exist (Seam 2).

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
    assert keys["name"] == p.stem, p
    assert keys["description"] and keys["tools"], p
    assert "<F>" not in p.read_text(), p
print("frontmatter ok")
PY
```

That block is Seam 3; step 2's `git diff --exit-code -- dist/` is Seam 4 (no other harness drifts).

## 4. Install and run in ZCode (manual, SC-001/SC-002)

```bash
./install.sh --harness zcode
ls ~/.zcode/skills/factory ~/.zcode/agents/factory-*.md
ZCODE_HOME=/tmp/zc ./install.sh --harness zcode && ls /tmp/zc/agents   # env override
```

Start a fresh ZCode session in a target repository and run `/factory <feature>`. Expect: preflight
recognises ZCode, roles run as subagents, grilling questions appear in the factory's Markdown layout.
If `.specify/` is missing, the offered command is
`specify init --here --integration zcode --integration-options="--skills"`, which writes
`.zcode/skills/speckit-*/SKILL.md`.

## 5. Documentation checks (FR-016)

`README.md` harness table has a ZCode row (install, `/factory <feature>`, `~/.zcode/agents/factory-*.md`)
and the requirements list names ZCode's SpecKit setup; `DESIGN.md` lists `zcode` under "Adapters today";
`CONTEXT.md`'s Harness definition names ZCode.

## 6. Cleanup

```bash
./install.sh --harness zcode --uninstall
```
