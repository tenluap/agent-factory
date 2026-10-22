#!/usr/bin/env bash
# Render the factory for a harness and symlink it into that harness's directories.
# Usage: ./install.sh [--harness <name>|all] [--uninstall]. Default harness: claude-code. Re-run after pulling.
# Harnesses: see adapters/ (python3 tools/render.py --list).
set -euo pipefail

src="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
harness="claude-code"
uninstall=""
while [ $# -gt 0 ]; do
  case "$1" in
    --harness) harness="$2"; shift 2 ;;
    --uninstall) uninstall=1; shift ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

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
  if [ -L "$to" ] && [[ "$(readlink "$to")" == "$src"/* ]]; then
    rm "$to"
    echo "removed: $to"
  fi
}

install_one() {
  local paths dist skill_dir agent_dir
  paths="$(python3 "$src/tools/render.py" "$1" --paths)"
  eval "$paths"
  echo "== $1"
  if [ -n "$uninstall" ]; then
    unlink_ours "$skill_dir"
    for f in "$dist"/agents/*; do unlink_ours "$agent_dir/$(basename "$f")"; done
    return
  fi
  mkdir -p "$(dirname "$skill_dir")" "$agent_dir"
  link "$dist/skill" "$skill_dir"
  for f in "$dist"/agents/*; do link "$f" "$agent_dir/$(basename "$f")"; done
}

if [ "$harness" = "all" ]; then
  harnesses="$(python3 "$src/tools/render.py" --list)"
else
  harnesses="$harness"
fi
for h in $harnesses; do install_one "$h"; done
[ -n "$uninstall" ] && exit 0

pending="${FACTORY_HOME:-$HOME/.factory}/pending"
mkdir -p "$pending"
# Pending runs from before the harness split lived under ~/.claude/factory/pending.
old="$HOME/.claude/factory/pending"
if [ -d "$old" ] && [ -n "$(ls -A "$old")" ]; then
  mv -n "$old"/* "$pending"/
  echo "moved: pending runs from $old to $pending"
fi
