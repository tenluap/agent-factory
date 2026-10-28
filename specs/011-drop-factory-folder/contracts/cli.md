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
  "commit": "a1b2c3d",
  "dropped_at": "2026-10-28T01:00:00Z"
}
```

Refusals (exit 1, reason on stderr, nothing changed):

| Condition | Message names |
|-----------|---------------|
| no run recorded for this worktree (incl. already dropped) | the directory |
| status not `pr-open` | the status |
| live lock | the lock owner |
| archive target exists | the target path |
| copy or verification failed | the differing or missing files |
| git rm/commit failed | the git error (folder restored, archive removed) |

Never pushes. Usage errors exit 5.
