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
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

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
  mkdir -p "$factory_home"
fi
if [ ! -w "$factory_home" ]; then
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

link() {
  local from="$1" to="$2"
  if [ -e "$to" ] && [ ! -L "$to" ]; then
    echo "skip: $to exists and is not a symlink" >&2
    return
  fi
  ln -sfn "$from" "$to"
  echo "linked: $to"
}

unlink_ours() {
  local to="$1"
  if [ -L "$to" ] && [[ "$(readlink "$to")" == "$factory_home"/dist/* ]]; then
    rm "$to"
    echo "removed: $to"
  fi
}

install_one() {
  local dist skill_dir agent_dir
  echo "== $1"
  dist="$factory_home/dist/$1"
  python3 "$src/tools/render.py" "$1" --out "$dist"
  eval "$(python3 "$src/tools/render.py" "$1" --paths --out "$dist")"
  if [ -n "$uninstall" ]; then
    unlink_ours "$skill_dir"
    for f in "$dist"/agents/*; do unlink_ours "$agent_dir/$(basename "$f")"; done
    rm -rf "$dist"
    echo "removed: $dist"
    return
  fi
  mkdir -p "$(dirname "$skill_dir")" "$agent_dir"
  link "$dist/skill" "$skill_dir"
  for f in "$dist"/agents/*; do link "$f" "$agent_dir/$(basename "$f")"; done
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
