# Run artifacts leave the branch at PR open

Run state stays committed under `specs/<branch>/factory/` for the whole run, because resume and cross-harness handoff depend on it. Once the PR opens, the new `factory drop` command copies the folder to `${FACTORY_HOME:-~/.factory}/archive/<repo-name>-<branch>/`, verifies the copy, and removes the folder in one final commit, so the PR diff and the default branch carry no run artifacts. Gitignoring the folder or rewriting history would break resume or force-push a shared branch, and an opt-out would keep the noise, so all were rejected (brief, grill Q1–Q8). Pen design evidence is the exception that must survive in the repository: the canonical design-code map points at it, so the drop moves `factory/design/` to `docs/design/<branch>/` and rewrites the map's references in the same commit (grill-with-docs Q1).

## Consequences

- Run artifacts of finished runs live only in the local archive; they are not shared through the remote.
- A dropped run is no longer discoverable; recovery from a failed final push is a manual `git push` from the worktree.
- The design-code-mapping contract has two evidence locations: `factory/design/` during the run and `docs/design/<branch>/` after the drop.
