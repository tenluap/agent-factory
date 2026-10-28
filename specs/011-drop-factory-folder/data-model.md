# Data model: Drop the factory folder at run end

No state schema change.

- **Run folder** `<worktree>/specs/<branch>/factory/`: committed through the run; removed by the drop commit.
- **Run archive** `${FACTORY_HOME:-~/.factory}/archive/<repo-name>-<branch>/`: byte copy of the run folder minus `lock.json`. Name shares the improvement backlog key (`improvements.backlog_name` without `.json`). Created once by `os.rename` from a temp sibling `.<name>.<pid>.tmp`; never overwritten.
- **Drop commit**: message `factory: drop run artifacts`; deletes only paths under the run folder.

State transitions: `pr-open` → (drop) → no discoverable state on the branch. No other status is droppable.
