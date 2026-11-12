# CLI contract: instruction discovery

Both commands join the existing usage text and exit-code table (0 success; 1 refused or no run; 2 not a git repository; 5 usage error).

## `factory instructions [--repo <path>] [--ref <ref>]`

Read-only. Needs no run; writes nothing.

- Scans `--ref` (default `HEAD`) of `--repo` (default the current directory's main repository).
- Stdout: the instruction index JSON (data-model.md), `sort_keys`, indent 2.
- Exit 2: not a git repository. Exit 5: the ref does not resolve to a commit; the message names the ref.
- Notes (malformed config, unparseable front matter, missing import target, import chain past 4 hops, non-UTF-8 content, content over 1 MiB, config files past the 16 MiB held budget, a config glob over 256 characters, broken symlink) never change the exit code.

## `factory instructions-record [--repo <path>]`

Writer under the existing write-command contract: validate, atomic write, live-lock refusal, commit on worktree runs (`factory: instructions recorded`, only when the index file changed).

- Target: the one writable run (`resolve_target`). Ref: research.md R8.
- Writes: state `instructions` summary; the index file (pending: `<pending-name>.instructions.json`; worktree: `<spec_dir>/factory/instructions.json`).
- Stdout:

```json
{
  "ref": "<sha>",
  "counts": { "always": 0, "scoped": 0, "reference": 0 },
  "always_bytes": 0,
  "notes": [],
  "warning": null,
  "empty": false,
  "delta": null,
  "index": "<path of the index file>",
  "committed": null,
  "error": null
}
```

- `warning`: `null`, or `{ "limit": 32768, "always_bytes": n, "largest": [{ "path", "size" }] }` (up to 5, largest first) when `always_bytes` > 32768.
- `empty`: true when the index has no entries.
- `delta`: data-model.md "Index delta".
- `error`: a scan failure (ref does not resolve, git failure). Exit 0, nothing written, the previous summary kept.
- Exit 1: no writable run, or a live lock (existing refusals, existing messages).
