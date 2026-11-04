# Contract: `tools/bench.py` CLI

## `run`

```text
bench.py run --harness <claude-code|opencode> [--bench <name>] [--out <dir>]
             [--model <provider/model>] [--home <dir> | --from-checkout]
```

| Option | New | Behaviour |
|---|---|---|
| `--model` | yes | Forwarded as `claude --model <m>` / `opencode run -m <m>`; absent means no model option. |
| `--from-checkout` | yes | Render this checkout via `install.sh` into `<out>/home` and `<out>/harness-config`; launch against it. Mutually exclusive with `--home` (argparse error, exit 2). |
| `--harness`, `--bench`, `--home`, `--out` | no | Unchanged. |

Order of effects:

1. Unsupported harness or missing executable: exit 1 with the existing "use the manual benchmark fallback" message; nothing is created.
2. Output directory created (existing directory refused, as today).
3. Checkout mode: `install.sh` runs; non-zero exit stops the run with exit 1 and `benchmark run: checkout render failed (exit <n>): <installer output tail>`; no harness launch.
4. Fixture copy, git init, pending seed and brief (unchanged).
5. `provenance.json` written.
6. Harness launched. Non-zero exit: exit 1 as today; provenance already present.

Launch commands:

```text
claude -p <prompt> [--model <m>] --add-dir <out> [--add-dir <skill_dir>] [--add-dir <resolved skill_dir>] [--add-dir <home>]
       --allowedTools Read Edit Write Agent Skill Bash(git:*) Bash(python3:*) Bash(<skill_dir>/bin/factory:*)
opencode run [-m <m>] <prompt>
```

`--add-dir` entries already inside `<out>` are omitted; duplicates are removed. A skill directory that does not exist is not granted (no `--add-dir` for it or its target); the `Bash(<skill_dir>/bin/factory:*)` entry still names the path. No launch ever contains `--dangerously-skip-permissions`, `--permission-mode`, or a bare `Bash` allow entry.

Launch environment: inherited environment plus `FACTORY_HOME`, `FACTORY_HARNESS`; checkout mode adds `CLAUDE_CONFIG_DIR` and `CLAUDE_HOME` (Claude Code) or `XDG_CONFIG_HOME` (OpenCode) set to `<out>/harness-config`.

stdout JSON (one line) gains `"provenance": "<out>/provenance.json"`; existing keys unchanged.

## `score`

Unchanged arguments and exit status. Each `scores[]` entry gains `provenance` (see data-model.md). A missing or malformed record never raises and never changes `pass`.

## `compare`

Unchanged.
