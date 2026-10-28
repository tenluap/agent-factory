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
  [[ "$target" == "$src"/skills/* || "$target" == "$factory_home"/skills/* ]]
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
  local root="$1" f name
  mkdir -p "$root"
  for f in "$root"/*; do
    if library_link "$f" && [ ! -e "$f" ]; then
      rm "$f"
      echo "removed: $f"
    fi
  done
  for f in "$src"/skills/* "$factory_home"/skills/*; do
    [ -d "$f" ] && [ -f "$f/SKILL.md" ] || continue
    name="$(basename "$f")"
    if [ "$name" = factory ]; then
      echo "skip: $f: name reserved for the factory skill"
      continue
    fi
    if [[ "$f" == "$src"/skills/* ]] && [ -f "$factory_home/skills/$name/SKILL.md" ]; then
      continue
    fi
    link_skill "$f" "$root/$name"
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

install_one() {
  local dist skill_dir agent_dir skills_root
  echo "== $1"
  dist="$factory_home/dist/$1"
  python3 "$src/tools/render.py" "$1" --out "$dist"
  eval "$(python3 "$src/tools/render.py" "$1" --paths --out "$dist")"
  if [ -n "$uninstall" ]; then
    unlink_skills "$skills_root"
    unlink_ours "$skill_dir"
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
  if [ "$1" = "opencode" ]; then
    echo "ready: OpenCode factory skill and role agents linked; start a fresh OpenCode session to load them."
  fi
  python3 "$src/tools/render.py" "$1" --models
}

if [ "$harness" = "all" ]; then
  harnesses="$(python3 "$src/tools/render.py" --list)"
else
  harnesses="$harness"
fi
for h in $harnesses; do install_one "$h"; done
[ -n "$uninstall" ] && exit 0

pending="$factory_home/pending"
mkdir -p "$pending"
# Pending runs from before the harness split lived under ~/.claude/factory/pending.
old="$HOME/.claude/factory/pending"
if [ -d "$old" ] && [ -n "$(ls -A "$old")" ]; then
  mv -n "$old"/* "$pending"/
  echo "moved: pending runs from $old to $pending"
fi
