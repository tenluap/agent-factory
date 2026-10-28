# Contract: `factory drop`

```sh
python3 <F>/bin/factory drop [--repo <path>]
```

Run from the run's worktree. No positional arguments.

Success (exit 0):

```json
{
  "dropped": "specs/011-drop-factory-folder/factory",
  "archive": "/Users/me/.factory/archive/claude-factory-011-drop-factory-folder",
  "design": "docs/design/011-drop-factory-folder",
  "commit": "a1b2c3d",
  "pr_url": "https://github.com/me/claude-factory/pull/7",
  "totals_sentence": "Run took 2h 14m: 38m you (12 waits), 1h 12m agents (23 spawns), 24m overhead.",
  "dropped_at": "2026-10-28T01:00:00Z"
}
```

`design` is `null` on runs without `factory/design/`. `totals_sentence` is computed from the final state before removal and is `null` for a run that never recorded its start. On Pen runs the drop commit also carries the `git mv` of `factory/design/` to `design` and the rewritten `docs/design-code-map.json` (every `"specs/<branch>/factory/design/` prefix becomes `"docs/design/<branch>/`). The archive excludes `lock.json`.

Refusals (exit 1, reason on stderr, nothing changed):

| Condition | Message names |
|-----------|---------------|
| no run recorded for this worktree (incl. already dropped) | the directory |
| status not `pr-open` | the status |
| live lock | the lock owner |
| archive target exists | the target path |
| `factory/design/` exists and `docs/design/<branch>/` exists | the design target path |
| copy or verification failed | the differing or missing files |
| git mv/rm/commit failed | the git error (folder, map and design paths restored; archive removed) |

Never pushes; SKILL.md step 9 pushes, retries once, then tells the user to `git push` from the worktree. Usage errors exit 5.
