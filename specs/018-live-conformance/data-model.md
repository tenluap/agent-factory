# Data model: Live-conformance unblockers

## Provenance record (`<out>/provenance.json`)

```json
{
  "version": 1,
  "written_at": "2026-11-04T00:00:00Z",
  "bench": "greet-001",
  "harness": "claude-code",
  "model": null,
  "repo": "<out>/fixture-greet-001",
  "checkout": {
    "path": "<checkout root>",
    "revision": "<sha> | unavailable",
    "changed_paths": ["tools/bench.py", "new-file.txt"],
    "diff_sha256": "<hex> | null | unavailable"
  },
  "render": { "mode": "installed | checkout", "digest": "<hex> | none" },
  "installed_factory": { "skill_dir": "<resolved path> | unavailable", "digest": "<hex> | unavailable" },
  "harness_versions": { "claude": "<version text> | unavailable", "opencode": "<version text> | unavailable" }
}
```

Rules:

- `changed_paths` is `[]` and `diff_sha256` is `null` for a clean checkout; both are `"unavailable"` when git cannot report.
- `diff_sha256` covers tracked changes only; untracked paths appear in `changed_paths`.
- `render.digest` is `"none"` exactly when `render.mode` is `installed`.
- A value that cannot be determined is the string `"unavailable"`; the record is still written.
- The record never contains credentials or environment values.
- Written before the harness launches; never rewritten by the run.

Tree digest: sha256 over each regular file under the directory (symlinks followed), in sorted relative-path order, of `<relative path>\0<sha256 of bytes>\n`.

## Score entry (addition)

Each `scores[]` entry gains one key; nothing else changes:

- `"provenance": { ...record... }` when found and its `repo` matches the state's `repo`;
- `"provenance": { "missing": "<reason>" }` otherwise (no state, no `repo`, file absent, malformed, or repo mismatch).

`pass`, `metrics` and `conditions` are computed exactly as before; `compare` reads only `metrics` and `pass`.

## Run output directory layout

```text
<out>/
├── provenance.json
├── harness.log
├── fixture-<bench>/            fixture repo (session working directory)
├── fixture-<bench>-factory/    factory worktrees (created by the session)
├── home/                       FACTORY_HOME: pending/, and dist/ in checkout mode
└── harness-config/             checkout mode only: CLAUDE_CONFIG_DIR or XDG_CONFIG_HOME
```

## Leg (results document)

One row per leg in `conformance/golden-run-results.md`: headless smoke, golden run, pause/resume, cross-harness resume, approval/PR, UI (deferred). Columns: leg, harness(es), mode (checkout or installed baseline), run date, provenance path, result, evidence, notes.
