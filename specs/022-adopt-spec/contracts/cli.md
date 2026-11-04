# CLI contract: `factory adopt`

## `factory adopt <src> [--stage <stage>] --dry-run`

Read-only. Prints one JSON object:

```json
{
  "source": "<src as given>",
  "shape": "branch | remote-branch | default-branch | null",
  "branch": "007-x",
  "spec_dir": "specs/007-x",
  "base": "origin/main",
  "artifacts": ["spec.md", "plan.md"],
  "dirty": ["specs/007-x/spec.md"],
  "inferred_stage": "tasks",
  "needs_clarification": ["<line containing [NEEDS CLARIFICATION]>"],
  "worktree": "<repo>/../<repo-name>-factory/007-x",
  "pending": "<repo-name>-adopt-007-x",
  "refusal": null
}
```

Exit: 0 clean; 1 refused (report still printed, `refusal` set; a `<src>` failing `git check-ref-format --branch` is no match); 3 ambiguous (candidates listed on stderr); 5 usage (`--stage` outside `specify|plan|tasks|analyze`, missing `<src>`). Never fetches; writes nothing.

## `factory adopt <src> [--stage <stage>]`

The write ([research.md](../research.md) D7). Prints the resume digest of the new run, as `resume` does. Exit: 0 adopted; 1 refused, no pending adoption, ended pending adoption, live lock, or a failed step (rolled back, pending kept); 3 ambiguous; 5 usage.

## `factory resume <name>` (changed message only)

No match: exit 1, `no run '<name>' in <repo> (runs: ...); use adopt <branch|spec_dir> for a spec factory did not start`.
