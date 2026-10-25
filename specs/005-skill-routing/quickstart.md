# Quickstart: validating Factory skill routing

Run everything from the worktree root. `$CANON` below is the canonical render environment
([research.md](./research.md), R3); quote it character for character wherever a render is involved,
including the gate.

```sh
CANON='env -u CLAUDE_HOME -u CODEX_HOME -u COPILOT_HOME -u ZCODE_HOME -u XDG_CONFIG_HOME FACTORY_HOME=/nonexistent'
```

## Prerequisites

- Python 3 (renderer and state CLI; nothing else).
- A clean `git status` for `dist/` before you start, so the gate's result is about your change.
- A local render or install made outside `$CANON` rewrites the tracked `dist/` tree: follow it with
  `git checkout -- dist/` or a canonical re-render.

## Seam 1 - build and gate (the repository's documented commands)

```sh
$CANON sh -c 'for h in $(python3 tools/render.py --list); do python3 tools/render.py "$h" || exit 1; done'
test -z "$(git status --porcelain -- dist/)"
```

Expected: both exit 0 once `dist/` has been re-rendered and committed with the source. With any `core/`
edit not yet re-rendered, the second command exits non-zero and `git status --porcelain -- dist/` names the
drifted files. Spot-check the new reference reached every harness:

```sh
for h in $(python3 tools/render.py --list); do
  diff -q core/skills/factory/references/skills.md "dist/$h/skill/references/skills.md" || echo "DRIFT $h"
done
```

## Seam 2 - relative-link integrity

```sh
python3 - <<'PY'
import pathlib, re, sys
root = pathlib.Path('.')
sources = [p for d in ('core', 'docs') for p in root.glob(f'{d}/**/*.md')]
sources += [root / n for n in ('DESIGN.md', 'README.md', 'CONTEXT.md')]
link = re.compile(r'\[[^\]]*\]\(([^)#]+)(?:#[^)]*)?\)')
bad = []
for src in sources:
    for target in link.findall(src.read_text()):
        if target.startswith(('http://', 'https://', 'mailto:', '<')):
            continue
        if not (src.parent / target).resolve().exists():
            bad.append(f'{src}: {target}')
ref = 'references/skills.md'
linkers = ['core/skills/factory/SKILL.md', 'core/roles/code-build.md', 'core/roles/fixer.md']
for name in linkers:
    text = (root / name).read_text()
    if ref not in text:
        bad.append(f'{name}: does not link {ref}')
print('\n'.join(bad) or 'links ok')
sys.exit(1 if bad else 0)
PY
```

Expected: `links ok`, exit 0. Red while `SKILL.md` links `references/skills.md` before that file exists, or
if either code-writing role omits the link.

## Seam 3 - state and question contract

Write three throwaway fixtures under a scratch `FACTORY_HOME` (never under the repository), then digest
them with the state CLI. `<main-checkout>` is the path in `state.json`'s `repo`.

```sh
python3 - <<'PY'
import json, os, pathlib
repo = "<main-checkout>"
home = pathlib.Path(os.environ["SCRATCH"]) / "fh" / "pending"
home.mkdir(parents=True, exist_ok=True)
base = {"version": 3, "started_at": "2026-10-25T00:00:00Z", "harness": "claude-code", "feature": "f",
        "repo": repo, "default_branch": "main", "base": "origin/main", "status": "waiting_user",
        "mode": {"chain": "lite", "fast": True}, "skills": {}, "timeline": [], "ledger": [], "history": []}
# new: brainstorm stage + a protected question
json.dump({**base, "stage": "brainstorm", "relay": {"stage": "brainstorm", "rounds": [
    {"questions": [{"id": "Q1", "title": "Direction?", "requires_user": True, "recommended": "A"}],
     "answers": {}}]}}, open(home / "fx-new.json", "w"))
# legacy version 1: one batch at the top of relay, no rounds
json.dump({**base, "version": 1, "stage": "clarify", "relay": {
    "stage": "clarify", "questions": [{"id": "Q1", "text": "old"}], "answers": {}}},
    open(home / "fx-v1.json", "w"))
# legacy version 2: string answer
json.dump({**base, "version": 2, "stage": "plan", "relay": {"stage": "plan", "rounds": [
    {"questions": [{"id": "Q1", "text": "old"}], "answers": {"Q1": "yes"}}]}},
    open(home / "fx-v2.json", "w"))
PY

for f in new v1 v2; do
  FACTORY_HOME="$SCRATCH/fh" python3 core/skills/factory/bin/factory show "fx-$f" --repo "<main-checkout>" > "$SCRATCH/$f.json" || echo "FAIL $f"
done

python3 - <<'PY'
import json, os, pathlib, sys
s = pathlib.Path(os.environ["SCRATCH"])
new = json.loads((s / "new.json").read_text())
bad = []
if new["stage"] != "brainstorm":
    bad.append("stage not passed through")
q = new["relay"]["unanswered"][0]
if q.get("requires_user") is not True or q["id"] != "Q1":
    bad.append("requires_user not passed through")
if json.loads((s / "v1.json").read_text())["relay"]["total"] != 1:
    bad.append("version 1 relay not read")
if json.loads((s / "v2.json").read_text())["relay"]["answered"] != 1:
    bad.append("version 2 string answer not read")
state = pathlib.Path("core/skills/factory/references/state.md").read_text()
proto = pathlib.Path("core/skills/factory/references/protocol.md").read_text()
if "brainstorm" not in state:
    bad.append("state.md does not document the brainstorm stage")
if "requires_user" not in proto or "requires_user" not in state:
    bad.append("requires_user not documented in protocol.md and state.md")
print("\n".join(bad) or "contract ok")
sys.exit(1 if bad else 0)
PY
```

Expected: `contract ok`, exit 0, and no `FAIL` line. Red before the `state.md` and `protocol.md` edits (the
documented-vocabulary checks fail), and red again if a future CLI change stops passing unknown stage values
or question fields through. Delete `$SCRATCH/fh` afterwards; nothing here is committed.

## Manual checks (role behaviour)

These need real agent-driven runs and are reported separately, per `DESIGN.md`'s validation plan and the
spec's assumptions:

1. Three intake trials - explicit exploration, explicit delivery, ambiguous wording: the path matches the
   intent and only the ambiguous case asks one question (SC-001).
2. Stop after exploration, then resume: the confirmed direction is in the pending brief, the invoking
   checkout has zero changed files, and feature settlement asks no already-answered question (SC-002,
   SC-003).
3. A code-delivery run with `--fast`: the seam confirmation is shown and waited on; resume with unchanged
   seams does not re-ask it; a changed seam list does (SC-005).
4. Remove `ponytail` (or `tdd`) from the skill directory: the affected work stops with setup guidance naming
   the skill, and reports no completed work (SC-004).
5. Four diffs - design tokens, a locale string, user-visible copy in UI code, backend only: the first three
   are UI changes and the last skips the UI passes; the UI review makes zero edits and states whether its
   evidence was rendered or static (SC-006, SC-007).
6. Resume a run saved before this change: it restarts at its recorded stage with its answers intact
   (SC-008).
