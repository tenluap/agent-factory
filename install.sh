#!/usr/bin/env bash
# Render the factory for a harness into ${FACTORY_HOME:-~/.factory}/dist/<harness>
# and symlink the harness's skill and agent directories from that per-user copy.
# Usage: ./install.sh [--harness <name>|all] [--uninstall] [--add-skill <path>]
# Default harness: claude-code. Re-run after pulling. Harnesses: see adapters/.
#
# Thin entry point (ADR 0019): it finds Python 3.9+ and runs tools/install.py,
# which holds every install rule. FACTORY_PYTHON overrides the interpreter
# command, e.g. FACTORY_PYTHON="python3.13".
set -euo pipefail

src="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
probe='import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)'

if [ -n "${FACTORY_PYTHON:-}" ]; then
  candidates=("$FACTORY_PYTHON")
else
  case "$(uname -s 2>/dev/null)" in
    MINGW* | MSYS* | CYGWIN*) candidates=("py -3" "python" "python3") ;;
    *) candidates=("python3" "python") ;;
  esac
fi

python=""
for candidate in "${candidates[@]}"; do
  # word-split on purpose: "py -3" is a command and an argument; the Windows
  # Store stub on PATH fails this probe and is skipped
  # shellcheck disable=SC2086
  if $candidate -c "$probe" >/dev/null 2>&1; then
    python="$candidate"
    break
  fi
done

if [ -z "$python" ]; then
  echo "error: Python 3.9 or newer was not found (tried: ${candidates[*]})" >&2
  case "$(uname -s 2>/dev/null)" in
    MINGW* | MSYS* | CYGWIN*) echo "       install it with: winget install Python.Python.3.13" >&2 ;;
    Darwin) echo "       install it with: brew install python" >&2 ;;
    *) echo "       install it with your package manager (for example: sudo apt install python3)" >&2 ;;
  esac
  echo "       or set FACTORY_PYTHON to an interpreter command, then re-run: ./install.sh" >&2
  exit 2
fi

export FACTORY_PYTHON_CMD="$python"
export FACTORY_INSTALL_ENTRY="${FACTORY_INSTALL_ENTRY:-./install.sh}"
# shellcheck disable=SC2086
exec $python "$src/tools/install.py" "$@"
