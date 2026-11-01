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
  [[ "$target" == "$src"/skills/* || "$target" == "$factory_home"/dist/* || "$target" == "$factory_home"/skills/* ]]
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

skill_harnesses() {
  python3 - "$src/skills/SOURCES.md" "$1" <<'PY'
import re, sys
try:
    text = open(sys.argv[1]).read()
except OSError:
    raise SystemExit(0)
row = re.search(r"(?m)^\|\s*%s\s*\|(?:[^|]*\|){4}\s*([^|]*)\|" % re.escape(sys.argv[2]), text)
print(row.group(1).strip().lower() if row else "")
PY
}

# Link name for a repo-layer skill: the SKILL.md frontmatter name, which may
# differ from the folder name so per-harness variants (folder suffixes) all
# install under one skill name.
skill_name() {
  python3 - "$1/SKILL.md" <<'PY'
import re, sys
try:
    text = open(sys.argv[1]).read()
except OSError:
    raise SystemExit(0)
match = re.match(r'\A---\s*\n(.*?)\n---', text, re.S)
name = re.search(r'^name:\s*(.*?)\s*$', match.group(1), re.M) if match else None
print(name.group(1).strip().strip("'\"") if name else "")
PY
}

install_skills() {
  local root="$1" dist="$2" harness="$3" f name allowed linked=""
  mkdir -p "$root"
  for f in "$root"/*; do
    if library_link "$f" && [ ! -e "$f" ]; then
      rm "$f"
      echo "removed: $f"
    elif [ -L "$f" ] && [[ "$(readlink "$f")" == "$src"/core/skills/* ]]; then
      # links from the superseded link-from-source layout; the rendered
      # distribution is the source of first-party skills now
      rm "$f"
      echo "removed: $f"
    fi
  done
  # First-party skills are linked from the rendered distribution (ADR 0012),
  # ahead of the vendored and per-user layers, which win on name collision.
  for f in "$dist"/skills/*; do
    [ -d "$f" ] || continue
    name="$(skill_name "$f")"
    if [ -z "$name" ]; then
      echo "skip: $f: no frontmatter name"
      continue
    fi
    if [ -f "$factory_home/skills/$name/SKILL.md" ]; then
      echo "skip: $name: per-user skill takes precedence"
      continue
    fi
    linked="$linked,$name"
    link_skill "$f" "$root/$name"
  done
  for f in "$src"/skills/* "$factory_home"/skills/*; do
    [ -d "$f" ] && [ -f "$f/SKILL.md" ] || continue
    if [ "$(basename "$f")" = factory ]; then
      echo "skip: $f: name reserved for the factory skill"
      continue
    fi
    if [[ "$f" == "$src"/skills/* ]]; then
      name="$(skill_name "$f")"
      if [ -z "$name" ]; then
        echo "skip: $f: no frontmatter name"
        continue
      fi
      if [ -f "$factory_home/skills/$name/SKILL.md" ]; then
        continue
      fi
      if [ "$name" = factory ]; then
        echo "skip: $f: name reserved for the factory skill"
        continue
      fi
      allowed="$(skill_harnesses "$(basename "$f")")"
      if [ -n "$allowed" ] && [[ ",$allowed," != *,"$harness",* ]]; then
        if [ -L "$root/$name" ] && [ "$(readlink "$root/$name")" = "$f" ]; then
          rm "$root/$name"
          echo "removed: $root/$name"
        fi
        echo "skip: $name: not linked for harness $harness (SOURCES.md harnesses: $allowed)"
        continue
      fi
      case ",$linked," in
        *",$name,"*)
          echo "skip: $f: another variant is already linked as $name for harness $harness"
          continue
          ;;
      esac
      linked="$linked,$name"
    else
      name="$(basename "$f")"
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
  install_skills "$skills_root" "$dist" "$1"
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

pending="$factory_home/pending"
mkdir -p "$pending"
# Pending runs from before the harness split lived under ~/.claude/factory/pending.
old="$HOME/.claude/factory/pending"
if [ -d "$old" ] && [ -n "$(ls -A "$old")" ]; then
  mv -n "$old"/* "$pending"/
  echo "moved: pending runs from $old to $pending"
fi
