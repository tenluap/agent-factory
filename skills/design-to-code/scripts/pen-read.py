#!/usr/bin/env python3
"""Run read-only pen interactive commands in one process, one output file per section.

Usage: python3 -I pen-read.py <source.pen | app:NAME> <commands-file> <out-dir>

The commands file has sections introduced by `#! NAME` lines. Every other non-empty
line is one execute({ input: '...' }) call. Section NAME writes <out-dir>/NAME.txt with
its Print output. The full log goes to <out-dir>/pen-read.log. The source file is never
written; headless runs use <out-dir>/scratch.pen. Mutating calls (save, Insert, Update,
...) are refused. A failed call exits 2 after every section is written, and the error
names its section. Discard sections marked FAILED.
"""

import re
import subprocess
import sys
from pathlib import Path

ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
MUTATIONS = re.compile(
    r"\b(save|Insert|Copy|Update|Replace|Move|Delete|SetVariables|Generate)\s*\("
)
SECTION = re.compile(r"^#!\s*([A-Za-z0-9_-]+)\s*$")
TIMEOUT_SECONDS = 300
ERROR_LINES = 20
ERROR_SPAN = 40


def expand(text):
    lines, names, current = [], [], None
    for line in text.splitlines():
        match = SECTION.match(line)
        if match:
            if current is not None:
                lines.append(f"execute({{ input: 'Print(\"@@END {current}\")' }})")
            current = match.group(1)
            names.append(current)
            lines.append(f"execute({{ input: 'Print(\"@@BEGIN {current}\")' }})")
        elif line.strip():
            if current is None:
                sys.exit("refused: command line before the first '#! NAME' section")
            lines.append(line)
    if not names:
        sys.exit("refused: commands file needs at least one '#! NAME' section")
    lines.append(f"execute({{ input: 'Print(\"@@END {current}\")' }})")
    lines.append("exit()")
    return "\n".join(lines) + "\n", names


def parse(log):
    # Pen prints each call's response as: status, banner, "## Print output", the Print
    # lines, then a blank line. Only the Print lines belong to a section.
    data, begun, failed, errors = {}, set(), set(), []
    current, printing, in_error, span = None, False, False, 0
    for line in log.splitlines():
        if in_error:
            errors.append(line)
            span += 1
            if "editId" in line or span >= ERROR_SPAN:
                in_error = False
            continue
        if line.startswith("Error:"):
            in_error, span = True, 1
            failed.add(current or "?")
            errors.append(f"[{current or '?'}] {line}")
        elif line.startswith("## Print output"):
            printing = True
        elif not line.strip():
            printing = False
        elif printing:
            text = line.rstrip(" ")
            if text.startswith("@@BEGIN "):
                current = text[len("@@BEGIN ") :].strip()
                begun.add(current)
                data.setdefault(current, [])
            elif text.startswith("@@END "):
                current = None
            elif current is not None and not text.startswith("Exported "):
                data[current].append(text)
    return data, begun, failed, errors


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    source, commands, out_dir = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    script, names = expand(commands.read_text())
    mutation = MUTATIONS.search(script)
    if mutation:
        sys.exit(f"refused: read-only commands must not call {mutation.group(1)}()")
    out_dir.mkdir(parents=True, exist_ok=True)
    if source.startswith("app:"):
        command = ["pen", "interactive", "--app", source[4:]]
    else:
        command = [
            "pen",
            "interactive",
            "--in",
            source,
            "--out",
            str(out_dir / "scratch.pen"),
        ]
    try:
        run = subprocess.run(
            command,
            input=script,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        sys.exit(f"pen interactive timed out after {TIMEOUT_SECONDS}s")
    log = ANSI.sub("", run.stdout or "")
    (out_dir / "pen-read.log").write_text(log)

    data, begun, failed, errors = parse(log)
    missing = [name for name in names if name not in begun]
    for name in names:
        lines = data.get(name, [])
        path = out_dir / f"{name}.txt"
        path.write_text("\n".join(lines) + ("\n" if lines else ""))
        status = "FAILED" if name in failed or name in missing else "ok"
        print(f"{name}: {len(lines)} lines {status} -> {path}")
    if errors or missing or run.returncode:
        print("\n".join(errors[:ERROR_LINES]) or log[-2000:], file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
