# Research: Drop the factory folder at run end

## R1. Which run does `factory drop` act on?

- Decision: the worktree run whose recorded `worktree` equals the current directory and whose status is `pr-open`.
- Rationale: `resolve_target` skips ended runs by design, so it cannot be reused. Matching the recorded `worktree` excludes copies of older runs (`specs/007..010/*/factory/`) that ride along in the same checkout.
- Alternatives: a `<run>` argument (unneeded; the orchestrator is already in the worktree); matching by branch name only (older pr-open copies share the worktree).

## R2. Failed copy

- Decision: copy into `${FACTORY_HOME}/archive/.<name>.<pid>.tmp`, verify, then `os.rename` into place; remove the temp dir on any failure.
- Rationale: a failure leaves no partial archive, so a retry is not blocked by the collision rule. Rename within one directory is atomic on POSIX. Supersedes the spec's earlier "leave the partial archive" edge case (orchestrator guidance; spec updated).
- Alternatives: copy straight to the target (partial archive blocks retry).

## R3. Verification

- Decision: recursive `filecmp.dircmp` plus `filecmp.cmp(shallow=False)` on common files.
- Rationale: stdlib, byte-level, reports differing or missing names for the error message.
- Alternatives: hashing (more code, same result).

## R4. Lock

- Decision: `lock.acquire` for the check-and-copy; exclude `lock.json` from the copy; release before `git rm`.
- Rationale: matches "refuses under a live lock" for writers; `lock.json` is transient and must not land in the archive or the commit.

## R6. Design evidence move (FR-017)

- Decision: `git mv` `factory/design/` to `docs/design/<branch>/` and replace the quoted prefix `"specs/<branch>/factory/design/` with `"docs/design/<branch>/` in the `docs/design-code-map.json` text, in the drop commit.
- Rationale: grill-with-docs Q1; a textual replace keeps every other map byte (no JSON re-serialisation drift).
- Alternatives: keep `factory/design/` on the branch (rejected by the user); JSON load/dump (reformats the map).

## R5. Git failure after the archive lands

- Decision: restore the folder from HEAD, remove the archive, exit 1.
- Rationale: keeps SC-003 (a refusal changes nothing) and leaves a retry unblocked.
