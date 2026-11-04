# Research: Live-conformance unblockers

All Technical Context unknowns are resolved below. Facts come from `tools/bench.py`, `install.sh`, `tools/render.py`, `adapters/*/adapter.json` and `core/skills/factory/SKILL.md` at the branch base.

## R1 Directory grant for headless Claude Code

- **Decision**: `--add-dir` covers the run's output directory, the factory skill directory in use (link path and resolved target), and `--home` when it lies outside the output directory.
- **Rationale**: the session's working directory is the fixture repo `<out>/fixture-<bench>`. The factory creates its worktree as a sibling (`<repo>/../<repo-name>-factory/<branch>`, SKILL.md step 2), and the default factory home `<out>/home` holds the seeded pending state and brief. Both are outside the working directory, so a grant limited to the skill directory would stall at worktree creation and at reading the brief. The output directory is disposable and owned by the run, so it is the narrowest single grant covering fixture, worktree and home. This settles the open spec question: the grant does cover the factory home.
- **Alternatives**: skill directory plus home only (rejected: worktree edits blocked); the whole user home (rejected: too broad).

## R2 Allow-list and argument order

- **Decision**: `claude -p <prompt> [--model <m>] --add-dir <dir>... --allowedTools Read Edit Write Agent Skill "Bash(git:*)" "Bash(python3:*)" "Bash(<skill_dir>/bin/factory:*)"`. The prompt stays directly after `-p`.
- **Rationale**: `--add-dir` and `--allowedTools` are variadic, so a prompt placed after them could be read as a directory or tool. The factory invokes its CLI as `python3 <F>/bin/factory` (SKILL.md), covered by `Bash(python3:*)`; the direct-path entry covers a session that runs the executable itself. No `--permission-mode` and no `--dangerously-skip-permissions` is ever emitted.
- **Trial-time check**: the headless smoke leg confirms the grant reaches preflight; library skills outside the grant are read under the bare `Read` allow rule, in both the installed baseline and checkout mode (where `install.sh` links repo-layer skills from `<checkout>/skills/*` into `<out>/harness-config/skills`, so their targets resolve outside `<out>`); the smoke leg records whether that held in each mode.

## R3 Model option

- **Decision**: `--model <provider/model>` on `bench.py run`, forwarded as `opencode run -m <m>` and `claude --model <m>`; omitted entirely when absent.
- **Rationale**: Q9. Each harness's own option name; no validation of the value (the harness owns model names).

## R4 Isolated checkout install

- **Decision**: `--from-checkout` runs the existing `install.sh --harness <h>` with `FACTORY_HOME=<out>/home`, the adapter home variable (`CLAUDE_HOME` for Claude Code, `XDG_CONFIG_HOME` for OpenCode) set to `<out>/harness-config`, and `HOME=<out>`. The harness is then launched with `CLAUDE_CONFIG_DIR` and `CLAUDE_HOME` (Claude Code) or `XDG_CONFIG_HOME` (OpenCode) pointed at `<out>/harness-config`. `--from-checkout` and `--home` are mutually exclusive.
- **Rationale**: Q10 and "reuse existing render and install tooling". `install.sh` already renders into `$FACTORY_HOME/dist/<harness>` and links into the adapter home (`render.py --paths` honours the adapter `home.env`). Its only other `$HOME` use migrates `~/.claude/factory/pending` into the factory home, which would move the maintainer's real pending runs; setting `HOME=<out>` prevents that. Forbidding `--home` keeps every rendered file under the output directory.
- **Alternatives**: calling `render.py --out` and linking by hand (rejected: duplicates install.sh logic).
- **Credentials**: the isolated Claude Code config directory has no login; the procedure documents a one-time `claude` login or `ANTHROPIC_API_KEY`. OpenCode keeps provider auth, session storage and logs under its data directory, which isolation does not move; that directory is shared by design and is outside SC-004's scope (factory home and harness configuration).

## R5 Provenance

- **Decision**: `<out>/provenance.json`, written after fixture and pending-state setup and before the harness launch (schema in data-model.md).
- Checkout: `git rev-parse HEAD`, `git status --porcelain` (tracked and untracked paths), and a sha256 of `git diff HEAD --binary` when changes exist (untracked files are listed, not hashed).
- Rendered output: sha256 tree digest of `<out>/home/dist/<harness>` in checkout mode, else `"none"`.
- Installed factory: the brief's "installed factory SHA". An installed render is a copy under `~/.factory/dist`, not a git repository, so the record holds the resolved installed skill directory and its sha256 tree digest, comparable with the rendered digest. Located through `render.load_adapter(harness)["skill_dir"]`, which honours the adapter home variables.
- Harness CLI versions: `claude --version` and `opencode --version` for both drivers, each `"unavailable"` when missing, non-zero or timed out.
- Every subprocess carries a 10-second timeout; any failure records `"unavailable"` and the run continues (FR-008).

## R6 Score lookup

- **Decision**: a scored state's provenance is `Path(state.repo).parent / "provenance.json"`, accepted only when its `repo` equals the state's `repo`. Otherwise the entry carries `{"missing": "<reason>"}`.
- **Rationale**: `bench.py run` sets the state's `repo` to `<out>/fixture-<bench>`, so the record's location follows from the state itself; the `repo` match prevents attributing a state to another run's record. No ancestor walk.

## R7 Test approach

- **Decision**: subprocess tests of the CLI with Python stub executables for `claude`, `opencode` and (for the install failure) `bash` first on `PATH`, plus sandboxed `HOME`, `CLAUDE_HOME`, `XDG_CONFIG_HOME` and `FACTORY_HOME`. Checkout provenance is tested as a function against throwaway git repos because the real checkout's cleanliness cannot be controlled.
- **Rationale**: FR-015. Both harness names are always stubbed, so no test runs a real harness CLI, even for `--version`.
