#!/usr/bin/env bash
# Symlink the factory skill and agents into ~/.claude. Re-run after pulling; pass --uninstall to remove the links.
set -euo pipefail

src="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
claude="${CLAUDE_HOME:-$HOME/.claude}"

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

if [ "${1:-}" = "--uninstall" ]; then
  unlink_ours "$claude/skills/factory"
  for f in "$src"/agents/*.md; do unlink_ours "$claude/agents/$(basename "$f")"; done
  exit 0
fi

mkdir -p "$claude/skills" "$claude/agents" "$claude/factory/pending"
link "$src/skills/factory" "$claude/skills/factory"
for f in "$src"/agents/*.md; do link "$f" "$claude/agents/$(basename "$f")"; done
