# The installer is a Python module; shell scripts are thin entry points

2026-11-07: the install logic moved from `install.sh` (bash) to `tools/install.py`. `install.sh`, `install.ps1` and `install.cmd` now only find a Python 3.9+ interpreter and run it, so a clone installs and runs the same way on Linux, macOS and native Windows.

## Context

The factory already needed Python for `render.py` and the state CLI, but the installer was 500 lines of bash built on `ln -sfn`, `readlink` string comparisons and about ten embedded Python snippets. Installing it on Windows exposed one failure after another:

- With `core.autocrlf=true`, `install.sh` checked out with CRLF line endings and bash refused to run it.
- Git Bash's `ln -s` silently copies unless `MSYS=winsymlinks:nativestrict` is set, which defeats the ownership rules that read link targets.
- Windows Python writes `\r\n` to stdout, so the names that shell captures read back carried a CR and created dead links.
- `render.py --paths` printed `C:\...` paths while Git Bash's `readlink` printed `/c/...`, so `verify_link` rejected correct links.
- Text reads without `encoding=` used cp1252 and crashed on UTF-8 role files.
- `factory_cli` used `os.O_NONBLOCK`/`O_NOFOLLOW`/`dir_fd`, none of which Windows has. Its lock liveness probe used `os.kill(pid, 0)`, which on Windows calls `TerminateProcess` and kills the process instead of probing it.

## Decision

1. **One implementation.** `tools/install.py` holds every install rule: argument handling, the factory-home and config guards, rendering, the three skill layers, the browsing mirror, the OpenCode plugin and the hook script. It imports `render.py` from the same folder and works with native paths, using `os.symlink` and `os.readlink`. Messages, exit codes, flags and precedence are unchanged. `tools/tests/test_install.py` and `test_skill_library.py` are the contract, and they run through whichever entry point `FACTORY_TEST_ENTRY` selects (`sh`, `cmd`, `ps1` or `py`).
2. **Thin entry points.** `install.sh` (POSIX and Git Bash) and `install.ps1` (Windows PowerShell 5.1 and later) find an interpreter and run `tools/install.py`. The interpreter must pass a version probe: on Windows they try `py -3`, then `python`, then `python3`; elsewhere `python3`, then `python`. The Microsoft Store stub fails the probe and is skipped. `FACTORY_PYTHON` overrides the search. The entry points never install software: when no interpreter is found they print the command that installs one (`winget install Python.Python.3.13` on Windows). `install.cmd` is the documented Windows command. It runs `install.ps1` with `-ExecutionPolicy Bypass` for that one process, so the machine's policy is never changed. Each entry point sets `FACTORY_INSTALL_ENTRY` to the command the user re-runs, and messages that suggest a re-run name it.
3. **Real symlinks only.** On Windows the installer first checks that it can create a symlink, and if it can't, it stops before changing anything and explains how to turn on Developer Mode. Junctions, hard links and copies were rejected: junctions can't link the agent files, and copies break the link-ownership rules. Copies left by an earlier Git Bash install are reported by the existing `skip:` messages and are not migrated.
4. **The interpreter is rendered.** The entry point passes the command it used (`FACTORY_PYTHON_CMD`). For a per-user render only, `render.py --python <cmd>` replaces `python3` with it in the rendered Markdown and TOML, so the skill's `python3 <F>/bin/factory` calls work where `python3` is not the interpreter's name (for example `py -3` in Git Bash or PowerShell). The canonical `dist/` render keeps `python3`. The command is detected on every install and stored nowhere, and the installer prints it as `python: <cmd> (<version>)`.
5. **Portable I/O.** Every text read and write in `render.py`, `install.py` and `factory_cli` is UTF-8 and writes LF line endings. `~` expands the way the harnesses resolve it: `$HOME` on POSIX and `%USERPROFILE%` on Windows, where Node's `os.homedir()` ignores `HOME`, so a custom Git Bash `HOME` doesn't redirect the links. Test sandboxes set both variables. Paths stored in run state use `/`. `factory_cli` probes lock liveness on Windows with `OpenProcess`/`GetExitCodeProcess`. Where `O_NOFOLLOW` and `dir_fd` are missing, it refuses symlinked configs and directories with an explicit check.
6. **`.gitattributes` fixes line endings**: LF for shell, Python, Markdown, JavaScript and the factory CLI; CRLF for `.ps1` and `.cmd`.

## Considered options

- **Fix `install.sh` for Git Bash**: the smallest diff. But it needs `MSYS` symlink flags, CR stripping on every Python capture, and path conversion between `/c/...` and `C:\...` for every comparison, and none of that helps a PowerShell user.
- **A second, native `install.ps1` implementation**: no Python changes. But two installers would drift, and the tests could only cover one of them.
- **WSL only**: no changes at all. But the harnesses run natively on Windows, so the links have to point at Windows paths.
- **Python module behind thin wrappers** (chosen): one implementation that the existing tests cover on every OS.

## Consequences

Installing still needs only Python and Git, and Node only for the optional hook. `--add-skill` now dereferences every link in the copied skill (previously only the given path), so the per-user copy is self-contained and a dangling link fails the copy. Claude Code is fully supported at runtime on Windows, since its Bash tool runs in Git Bash. OpenCode, Codex, Copilot and ZCode install on Windows, but their runtime there is best-effort, because they may run the skill's shell commands in PowerShell. The `unwritable home` install test is skipped on Windows, where directories ignore read-only mode bits. CI runs the suite and a real install on `windows-latest` as well as `ubuntu-latest`.
