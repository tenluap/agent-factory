#!/usr/bin/env bash
# Render the factory for a harness into the user's factory home
# (${FACTORY_HOME:-~/.factory}/dist/<harness>) and symlink the harness's
# skill and agent directories from that per-user copy.
# Usage: ./install.sh [--harness <name>|all] [--uninstall]. Default harness: claude-code. Re-run after pulling.
# Harnesses: see adapters/ (python3 tools/render.py --list).
set -euo pipefail

src="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
factory_home="${FACTORY_HOME:-$HOME/.factory}"
harness="claude-code"
uninstall=""
mirror_done=""
add_path=""
while [ $# -gt 0 ]; do
  case "$1" in
    --harness)
      if [ $# -lt 2 ] || [ -z "$2" ]; then
        echo "usage: $0 [--harness <name>|all] [--uninstall]" >&2
        echo "error: --harness needs a value (see adapters/, python3 tools/render.py --list)" >&2
        exit 2
      fi
      harness="$2"; shift 2 ;;
    --uninstall) uninstall=1; shift ;;
    --add-skill)
      if [ $# -lt 2 ] || [ -z "$2" ] || [[ "$2" == --* ]]; then
        echo "usage: --add-skill <path>" >&2; exit 2
      fi
      add_path="$2"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done
if [ -n "$uninstall" ] && [ -n "$add_path" ]; then
  echo "usage: --add-skill cannot be combined with --uninstall" >&2; exit 2
fi

# Factory-home policy: a missing default home ~/.factory is created; an
# explicitly configured home must exist as a writable directory — anything
# else fails naming the path, before anything is rendered or linked.
if [ -e "$factory_home" ] && [ ! -d "$factory_home" ]; then
  echo "error: not a directory: $factory_home" >&2
  exit 2
fi
if [ ! -d "$factory_home" ]; then
  if [ -n "${FACTORY_HOME:-}" ]; then
    echo "error: FACTORY_HOME does not exist: $factory_home" >&2
    exit 2
  fi
  if [ -z "$add_path" ]; then mkdir -p "$factory_home"; fi
fi
if [ -d "$factory_home" ] && [ ! -w "$factory_home" ]; then
  echo "error: not writable: $factory_home" >&2
  exit 2
fi

# A config.json that does not parse aborts the install before any render
# or link (FR-022): the message names the file and the parse error.
config="$factory_home/config.json"
if [ -f "$config" ]; then
  if ! parse_error="$(python3 -c 'import json, sys
try:
    json.load(open(sys.argv[1]))
except Exception as error:
    sys.exit(str(error))' "$config" 2>&1)"; then
    echo "error: $config does not parse: $parse_error" >&2
    exit 2
  fi
fi

# The vendored library is `.agents/skills/`, managed by the `skills` CLI
# (ADR 0018). A folder belongs to it only when its SKILL.md frontmatter name
# has an entry in `skills-lock.json`; anything else there (for example the
# speckit skills `specify init` writes for this checkout) is never linked.
lib="$src/.agents/skills"
lock="$src/skills-lock.json"
if [ -f "$lock" ]; then
  if ! parse_error="$(python3 -c 'import json, sys
try:
    data = json.load(open(sys.argv[1]))
    assert isinstance(data.get("skills"), dict), "no \"skills\" object"
except Exception as error:
    sys.exit(str(error))' "$lock" 2>&1)"; then
    echo "error: $lock does not parse: $parse_error" >&2
    exit 2
  fi
fi

# One folder name per line for every library folder with a SKILL.md, in
# name order; a folder the lock does not own is prefixed with `!`.
library_entries() {
  python3 - "$lib" "$lock" <<'PY'
import json, re, sys
from pathlib import Path

root, lock = Path(sys.argv[1]), Path(sys.argv[2])
try:
    owned = set(json.loads(lock.read_text(encoding="utf-8"))["skills"])
except (OSError, ValueError, KeyError, TypeError):
    owned = set()
folders = sorted(root.iterdir()) if root.is_dir() else []
for folder in folders:
    skill = folder / "SKILL.md"
    if folder.name.startswith(".") or not skill.is_file():
        continue
    text = skill.read_text(encoding="utf-8", errors="replace")
    match = re.match(r"\A---\s*\n(.*?)\n---", text, re.S)
    name = re.search(r"^name:\s*(.*?)\s*$", match.group(1), re.M) if match else None
    value = name.group(1).strip().strip("'\"") if name else ""
    print(("" if value in owned else "!") + folder.name)
PY
}

owned_entry() { printf '%s\n' "$library" | grep -qxF -- "$1"; }

# The per-user layer doubles as the browsing mirror of the vendored library
# (Q&A). Mirror links point into this checkout's library (or, before
# ADR 0018, its `skills/`) and are managed only by the mirror functions; the
# per-user skill scan must never treat them as per-user skills.
mirror_entry() {
  [ -L "$1" ] || return 1
  local target
  target="$(readlink "$1")"
  [[ "$target" == "$lib"/* || "$target" == "$src"/skills/* ]]
}

# A real per-user skill: a folder with a SKILL.md that is not a mirror link.
user_skill() {
  [ -f "$factory_home/skills/$1/SKILL.md" ] && ! mirror_entry "$factory_home/skills/$1"
}

mirror_link() {
  local from="$1" to="$2"
  if [ -L "$to" ] && ! mirror_entry "$to"; then
    echo "skip: $to exists and is not a mirror link; to adopt it: ./install.sh --add-skill $to, remove the original, re-run"
    return
  fi
  [ -e "$to" ] && [ ! -L "$to" ] && return  # a real per-user skill wins
  if [ ! -L "$to" ] || [ "$(readlink "$to")" != "$from" ]; then
    ln -sfn "$from" "$to"
  fi
}

mirror_library() {
  [ -d "$factory_home/skills" ] || return 0
  local f entry
  library="$(library_entries)"
  for f in "$factory_home"/skills/*; do
    [ -L "$f" ] || continue
    if [ ! -e "$f" ]; then
      rm "$f"
      echo "pruned: $f (stale link)"
    elif mirror_entry "$f" && { [[ "$(readlink "$f")" != "$lib"/* ]] || ! owned_entry "$(basename "$(readlink "$f")")"; }; then
      rm "$f"
      echo "pruned: $f (stale link)"
    fi
  done
  while IFS= read -r entry; do
    [ -n "$entry" ] && [[ "$entry" != '!'* ]] || continue
    mirror_link "$lib/$entry" "$factory_home/skills/$entry"
  done <<< "$library"
  mirror_done=1
}

add_skill() {
  local path="$1" name dest temp error
  if [[ "$path" == *://* ]] || [ ! -d "$path" ]; then
    echo "error: $path: not a local directory" >&2; return 2
  fi
  name="$(basename "$path")"
  if [ "$name" = factory ]; then echo "reserved: factory" >&2; return 2; fi
  if [ ! -f "$path/SKILL.md" ]; then echo "error: $path: no SKILL.md" >&2; return 2; fi
  if ! error="$(python3 - "$path/SKILL.md" "$name" 2>&1 <<'PY'
import re, sys
from pathlib import Path

try:
    text = Path(sys.argv[1]).read_text()
    match = re.match(r'\A---\s*\n(.*?)\n---\s*(?:\n|\Z)', text, re.S)
    name = re.search(r'^name:\s*(.*?)\s*$', match.group(1), re.M) if match else None
    if not name or not name.group(1).strip(" '\""):
        sys.exit('no frontmatter')
    value = name.group(1).strip().strip("'\"")
    if value != sys.argv[2]:
        sys.exit(f"name '{value}' does not match folder '{sys.argv[2]}'")
except (OSError, UnicodeError) as exc:
    sys.exit(str(exc))
PY
  )"; then
    echo "error: $path: $error" >&2; return 2
  fi
  dest="$factory_home/skills/$name"
  if [ -e "$dest" ] || [ -L "$dest" ]; then echo "exists: $dest" >&2; return 2; fi
  mkdir -p "$factory_home/skills"
  temp="$factory_home/skills/.$name.tmp.$$"
  if ! cp -RH "$path" "$temp" || ! mv "$temp" "$dest"; then
    rm -rf "$temp"
    echo "error: $path: copy failed" >&2; return 1
  fi
  echo "added: $dest"
}

[ -z "$add_path" ] || add_skill "$add_path"

link() {
  local from="$1" to="$2"
  if [ -e "$to" ] && [ ! -L "$to" ]; then
    echo "skip: $to exists and is not a symlink" >&2
    return
  fi
  ln -sfn "$from" "$to"
  echo "linked: $to"
}

verify_link() {
  local from="$1" to="$2"
  if [ ! -L "$to" ] || [[ "$(readlink "$to")" != "$from" ]]; then
    echo "error: factory link not installed at $to" >&2
    echo "       resolve any existing file at that path, then rerun: ./install.sh --harness $harness" >&2
    return 1
  fi
}

unlink_ours() {
  local to="$1"
  if [ -L "$to" ] && [[ "$(readlink "$to")" == "$factory_home"/dist/* ]]; then
    rm "$to"
    echo "removed: $to"
  fi
}

library_link() {
  [ -L "$1" ] || return 1
  local target
  target="$(readlink "$1")"
  [[ "$target" == "$lib"/* || "$target" == "$src"/skills/* || "$target" == "$factory_home"/dist/* || "$target" == "$factory_home"/skills/* ]]
}

link_skill() {
  local from="$1" to="$2"
  if { [ -e "$to" ] || [ -L "$to" ]; } && ! library_link "$to"; then
    echo "skip: $to exists and is not a library link; to adopt it: ./install.sh --add-skill $to, remove the original, re-run"
    return
  fi
  if ! [ -L "$to" ] || [ "$(readlink "$to")" != "$from" ]; then
    ln -sfn "$from" "$to"
  fi
  echo "linked: $to"
}

install_skills() {
  local root="$1" f target entry
  library="$(library_entries)"
  mkdir -p "$root"
  for f in "$root"/*; do
    [ -L "$f" ] || continue
    target="$(readlink "$f")"
    if library_link "$f" && [ ! -e "$f" ]; then
      rm "$f"
      echo "removed: $f"
    elif [[ "$target" == "$src"/core/skills/* || "$target" == "$src"/skills/* ]]; then
      # links from superseded layouts: first-party skills linked from source
      # (ADR 0012, superseded by ADR 0019) and the vendored library in
      # `skills/` (`.agents/skills/` replaced it, ADR 0018)
      rm "$f"
      echo "removed: $f"
    elif [[ "$target" == "$lib"/* ]] && ! owned_entry "$(basename "$target")"; then
      # the folder is still there but skills-lock.json no longer owns it
      rm "$f"
      echo "removed: $f"
    fi
  done
  # Library skills link under their folder name (the `skills` CLI derives it
  # from the frontmatter name); a per-user skill with the same name wins.
  # Factory-authored skills are lock-owned local entries, so this one loop
  # covers vendored and factory skills alike (ADR 0019). Links into a
  # pre-0019 rendered distribution's skills/ are library links whose target
  # the renderer no longer creates, so the stale-link rule above prunes them.
  while IFS= read -r entry; do
    [ -n "$entry" ] || continue
    if [[ "$entry" == '!'* ]]; then
      echo "skip: ${entry#!}: not in skills-lock.json"
      continue
    fi
    f="$lib/$entry"
    if [ "$entry" = factory ]; then
      echo "skip: $f: name reserved for the factory skill"
      continue
    fi
    user_skill "$entry" && continue
    link_skill "$f" "$root/$entry"
  done <<< "$library"
  for f in "$factory_home"/skills/*; do
    # the browsing mirror lives here but points back at the vendored library
    mirror_entry "$f" && continue
    [ -d "$f" ] && [ -f "$f/SKILL.md" ] || continue
    if [ "$(basename "$f")" = factory ]; then
      echo "skip: $f: name reserved for the factory skill"
      continue
    fi
    link_skill "$f" "$root/$(basename "$f")"
  done
}

unlink_skills() {
  local f
  for f in "$1"/*; do
    if library_link "$f"; then
      rm "$f"
      echo "removed: $f"
    fi
  done
}

# Uninstall leaves the per-user layer to the user: it removes mirror links
# only when their targets are gone from the checkout, so an uninstalled
# mirror can still be browsed but shows nothing dead.
prune_mirror() {
  [ -d "$factory_home/skills" ] || return 0
  local f
  for f in "$factory_home"/skills/*; do
    if mirror_entry "$f" && [ ! -e "$f" ]; then
      rm "$f"
      echo "pruned: $f (stale link)"
    fi
  done
}

# OpenCode loads every .js in its plugins directory. The design-to-code trigger
# plugin is linked straight from repo source (no render step) and removed on
# uninstall only when the link still points here.
plugin_target() { echo "$(dirname "$skills_root")/plugins/design-to-code-trigger.js"; }

install_plugin() {
  mkdir -p "$(dirname "$(plugin_target)")"
  link "$src/plugins/design-to-code-trigger.js" "$(plugin_target)"
}

unlink_plugin() {
  local to
  to="$(plugin_target)"
  if [ -L "$to" ] && [[ "$(readlink "$to")" == "$src"/plugins/* ]]; then
    rm "$to"
    echo "removed: $to"
  fi
}

# claude-code and codex share one UserPromptSubmit hook script (same stdin
# shape, same additionalContext output). The script is copied into
# $factory_home/bin and wired by hand — install.sh never edits the user's
# settings.json or hooks.json, so it prints the snippet to paste instead.
hook_script_target() { echo "$factory_home/bin/design-to-code-hook.mjs"; }

install_hook_script() {
  local target
  target="$(hook_script_target)"
  mkdir -p "$(dirname "$target")"
  if ! cp "$src/plugins/design-to-code-hook.mjs" "$target"; then
    echo "error: hook script copy failed: $target" >&2
    return 1
  fi
  chmod +x "$target"
  echo "installed: $target"
  cat <<EOF
wire it manually (this installer never edits your harness config):

  claude-code — add to "hooks" in ~/.claude/settings.json:

    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "node \"$target\"",
            "timeout": 5,
            "statusMessage": "Checking UI intent..."
          }
        ]
      }
    ]

  codex — add to "hooks" in ~/.codex/hooks.json:

    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "node \"$target\"",
            "timeout": 5,
            "statusMessage": "Checking UI intent..."
          }
        ]
      }
    ]

  codex also requires trusting the hook once: run /hooks in Codex and approve it.
EOF
}

uninstall_hook_script() {
  local target
  target="$(hook_script_target)"
  if [ -f "$target" ]; then
    rm "$target"
    echo "removed: $target"
    echo "note: remove the matching UserPromptSubmit entry from ~/.claude/settings.json or ~/.codex/hooks.json if you wired it"
  fi
}

install_one() {
  local dist skill_dir agent_dir skills_root
  echo "== $1"
  dist="$factory_home/dist/$1"
  python3 "$src/tools/render.py" "$1" --out "$dist"
  eval "$(python3 "$src/tools/render.py" "$1" --paths --out "$dist")"
  if [ -n "$uninstall" ]; then
    unlink_skills "$skills_root"
    prune_mirror
    unlink_ours "$skill_dir"
    [ "$1" = "opencode" ] && unlink_plugin
    case "$1" in claude-code|codex) uninstall_hook_script ;; esac
    for f in "$dist"/agents/*; do unlink_ours "$agent_dir/$(basename "$f")"; done
    rm -rf "$dist"
    echo "removed: $dist"
    return
  fi
  mkdir -p "$(dirname "$skill_dir")" "$agent_dir"
  link "$dist/skill" "$skill_dir"
  verify_link "$dist/skill" "$skill_dir"
  for f in "$dist"/agents/*; do
    link "$f" "$agent_dir/$(basename "$f")"
    verify_link "$f" "$agent_dir/$(basename "$f")"
  done
  install_skills "$skills_root"
  case "$1" in
    opencode)
      install_plugin
      echo "ready: OpenCode factory skill, role agents and design-to-code trigger plugin linked; start a fresh OpenCode session to load them."
      ;;
    claude-code|codex)
      install_hook_script
      ;;
  esac
  python3 "$src/tools/render.py" "$1" --models
}

if [ "$harness" = "all" ]; then
  harnesses="$(python3 "$src/tools/render.py" --list)"
else
  harnesses="$harness"
fi
for h in $harnesses; do install_one "$h"; done
[ -n "$uninstall" ] && exit 0

# The browsing mirror is refreshed once per run, after the per-user renders
# it may point at are in place.
mirror_library
[ -n "$mirror_done" ] || echo "note: no browsing mirror: $factory_home/skills does not exist yet (use --add-skill to create it)"

pending="$factory_home/pending"
mkdir -p "$pending"
# Pending runs from before the harness split lived under ~/.claude/factory/pending.
old="$HOME/.claude/factory/pending"
if [ -d "$old" ] && [ -n "$(ls -A "$old")" ]; then
  mv -n "$old"/* "$pending"/
  echo "moved: pending runs from $old to $pending"
fi
