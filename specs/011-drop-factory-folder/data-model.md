# Data model: Drop the factory folder at run end

No state schema change.

- **Run folder** `<worktree>/specs/<branch>/factory/`: committed through the run; removed by the drop commit.
- **Run archive** `${FACTORY_HOME:-~/.factory}/archive/<repo-name>-<branch>/`: byte copy of the run folder minus `lock.json`. Name shares the improvement backlog key (`improvements.backlog_name` without `.json`). Created once by `os.rename` from a temp sibling `.<name>.<pid>.tmp`; never overwritten.
- **Drop commit**: message `factory: drop run artifacts`; deletes paths under the run folder and, on Pen runs, renames `factory/design/` to `docs/design/<branch>/` and rewrites `docs/design-code-map.json` path prefixes. Touches nothing else.
- **Permanent design evidence** `docs/design/<branch>/`: Pen evidence after the drop, referenced by the canonical map. Never overwritten; an existing target refuses the drop.
- **Drop output**: JSON `dropped`, `archive`, `design`, `commit`, `pr_url`, `totals_sentence`, `dropped_at` (contracts/cli.md). Step 9 `NOTIFY`s from it because `state.json` has left the worktree.

State transitions: `pr-open` → (drop) → no discoverable state on the branch. No other status is droppable.
