# Feature Specification: Drop the factory folder at run end

**Feature Branch**: `011-drop-factory-folder`

**Created**: 2026-10-28

**Status**: Draft

**Input**: User description: "At the end of the whole factory flow, drop the factory folder the run adds under specs/<branch>/ so it is no longer committed in PRs."

## Clarifications

### Session 2026-10-28

- Q: Where does step 9 get the run totals and PR URL once the drop has removed `state.json` from the worktree? → A: `factory drop` computes the totals sentence from the final state before removal and includes it, the PR URL and the archive path in its JSON output. Step 9 `NOTIFY`s from that output. The PR stage is done when the PR URL is recorded in the archived state and shown to the user.
- Q: What does `factory drop` do with `specs/<branch>/factory/design/` on Pen design runs? → A: Everything in `factory/` leaves the branch. On a Pen run, the drop first moves `factory/design/` to the permanent path `docs/design/<branch>/` and rewrites every `docs/design-code-map.json` reference to it, in the same drop commit. The mapping contract (`design-code-mapping.md`, DESIGN.md) states that evidence moves to the permanent path at drop.
- Q: How is a failed final push (after the drop commit) recovered, given the run is no longer discoverable? → A: The orchestrator retries the push once in the same turn. If the second attempt fails, it `NOTIFY`s the user to run `git push` from the named worktree path. No resume is involved.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - PR diff carries no run artifacts (Priority: P1)

A developer runs `/factory` on a feature. When the run opens its PR, the reviewer sees only the feature's real changes and its spec artifacts (`spec.md`, `plan.md`, `tasks.md` and the like). Run state, the brief, analyze reports, remediation logs and review findings under `specs/<branch>/factory/` are not part of the PR's file diff.

**Why this priority**: This is the whole point of the feature. Run artifacts inflate every PR, distract reviewers and land on the default branch on merge.

**Independent Test**: Run the factory to the PR step on a test repository. After step 9 completes, the branch tip contains no `specs/<branch>/factory/` path, and the PR's file list shows none.

**Acceptance Scenarios**:

1. **Given** a run whose PR was just created and whose status was just set to `pr-open`, **When** the orchestrator runs `factory drop` and pushes, **Then** the branch's last commit is `factory: drop run artifacts`, it removes every file under `specs/<branch>/factory/`, and nothing else changes in that commit except the design evidence move of FR-017 on Pen runs.
2. **Given** the drop commit is pushed, **When** a reviewer opens the PR's file diff, **Then** no path under `specs/<branch>/factory/` appears.
3. **Given** the run is in progress (any status other than `pr-open`), **When** the orchestrator checkpoints, resumes or discovers runs, **Then** behaviour is unchanged: the folder stays committed and readable on the branch.

---

### User Story 2 - Nothing is lost (Priority: P1)

A maintainer who studies how runs went (issues, timeline, ledger, analyze reports, reviews) still finds every artifact of a finished run after its folder leaves the branch.

**Why this priority**: Removing the folder without a copy destroys the evidence the improvement loop and benchmarks rely on. Equal to P1 because the drop must never happen without it.

**Independent Test**: After `factory drop`, compare the archive folder with the folder as it stood in the commit before the drop. Every file is present with identical bytes.

**Acceptance Scenarios**:

1. **Given** a `pr-open` run, **When** `factory drop` runs, **Then** the whole `specs/<branch>/factory/` folder is copied to `${FACTORY_HOME:-~/.factory}/archive/<repo-name>-<branch>/` before anything is removed from git.
2. **Given** the copy completes, **When** verification compares the copy with the source, **Then** the removal proceeds only if every file matches; otherwise the command refuses, removes nothing from git, and reports which files differ or are missing.
3. **Given** a successful drop, **When** the command exits, **Then** it prints JSON naming the archive path, the PR URL and the run totals sentence computed from the final state.

---

### User Story 3 - Safe refusals (Priority: P2)

The orchestrator calls `factory drop` at the wrong time, or twice, or on a branch whose archive already exists. The command refuses with a clear reason and changes nothing.

**Why this priority**: Guards against data loss and stray commits. Needed but secondary to the main flow.

**Independent Test**: Call `factory drop` on runs in each refusal condition and confirm exit code, message and an unchanged working tree, git history and archive directory.

**Acceptance Scenarios**:

1. **Given** a run whose status is `running`, `waiting_user`, `paused`, `halted` or `aborted`, **When** `factory drop` runs, **Then** it refuses, names the current status, and creates no archive and no commit.
2. **Given** the archive target `${FACTORY_HOME:-~/.factory}/archive/<repo-name>-<branch>/` already exists, **When** `factory drop` runs, **Then** it refuses with a message naming that path, overwrites nothing, and creates no commit.
3. **Given** the run is held by a live lock, **When** `factory drop` runs, **Then** it refuses like every other write command.
4. **Given** the folder was already dropped (no `specs/<branch>/factory/` on the branch), **When** `factory drop` runs again, **Then** it refuses because no matching run is found, and changes nothing.

---

### Edge Cases

- Aborted runs: never dropped. Their folder and worktree stay as they are.
- Copy fails midway (disk full, permission error): the copy goes to a temporary sibling under `${FACTORY_HOME:-~/.factory}/archive/` and is renamed into place only after verification. On failure the command removes the temporary copy, leaves the folder in git untouched, and refuses; no partial archive remains, so a retry is not blocked.
- The PR exists but the final push fails: the drop commit stays local and complete. The orchestrator retries the push once in the same turn; if that also fails, it `NOTIFY`s the user to run `git push` from the named worktree path. No resume is involved (the run is no longer discoverable).
- Totals after the drop: `state.json` is gone from the worktree, so step 9 takes the totals sentence, PR URL and archive path from the `factory drop` JSON output instead of reading state.
- Resume after the drop: discovery no longer finds the run on the branch, which matches today's behaviour for `pr-open` runs (they are already excluded from discovery).
- Improvement backlog: `set-status pr-open` exports the backlog before the drop, so the export is unaffected. `factory improvements claim` treats a run with no discoverable state as ended, as it does for any non-discoverable run today.
- Untracked or ignored files inside the folder: the archive copies the folder as it is on disk; the removal commit removes the tracked files. Any untracked leftovers are archived too.
- Existing runs `specs/007..010/*/factory/` on the default branch: out of scope; left as they are.
- Pen design run (`factory/design/` exists): the archive still copies it with the rest of the folder. The drop commit then moves it to `docs/design/<branch>/` and points the map at the new path, so the map never references a removed file.
- Design evidence target `docs/design/<branch>/` already exists: the command refuses before any archive or git change, naming the path.
- Non-Pen run: no `factory/design/`, so no move and no map edit.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The state CLI MUST provide a write command `factory drop` that follows the single-writer rule: it stamps its own time, refuses under a live lock, and is the only way the folder is removed.
- **FR-002**: `factory drop` MUST refuse unless the run's status is `pr-open`. The refusal names the actual status and exits with the CLI's refused-write code.
- **FR-003**: `factory drop` MUST copy the whole `specs/<branch>/factory/` folder to `${FACTORY_HOME:-~/.factory}/archive/<repo-name>-<branch>/`, using the same `<repo-name>` derivation the improvement backlog export uses.
- **FR-004**: `factory drop` MUST refuse, overwrite nothing and commit nothing when the archive target already exists. The message names the existing path.
- **FR-005**: `factory drop` MUST verify the copy (same file set, identical content) before removing anything from git. A failed verification refuses and leaves git untouched.
- **FR-006**: After a verified copy, `factory drop` MUST remove the folder from git (`git rm -r specs/<branch>/factory`) and create exactly one commit with the message `factory: drop run artifacts`, touching no other path except the FR-017 design evidence move.
- **FR-007**: On success `factory drop` MUST print JSON that includes the archive path, the PR URL from the final state, and the run totals sentence computed from the final state before removal.
- **FR-008**: `factory drop` MUST NOT push. Pushing stays with the orchestrator.
- **FR-009**: SKILL.md step 9 MUST run, in order: push, `gh pr create`, `factory set-status pr-open --pr-url <url>`, `factory drop`, push, then `NOTIFY` the totals sentence and PR URL taken from the `factory drop` JSON output. If the final push fails, the orchestrator retries it once in the same turn; a second failure `NOTIFY`s the user to run `git push` from the named worktree path. The stage's "Done when" becomes: the PR URL is recorded in the archived state and shown to the user. The final state and the improvement backlog export of `set-status pr-open` are unchanged.
- **FR-010**: Run state MUST stay committed throughout the run. Checkpoints, resume, discovery and the existing write commands keep their current behaviour; no history rewrite and no gitignore change.
- **FR-011**: The drop MUST apply to every run that reaches `pr-open`, with no opt-out flag or configuration setting.
- **FR-012**: `aborted` runs MUST keep their folder and worktree.
- **FR-013**: DESIGN.md MUST record the new end-of-run behaviour (PR step, state CLI surface, archive location, design evidence move) before or with the core change (constitution I).
- **FR-014**: references/state.md MUST document the archive under "Location" and `factory drop` under "CLI"; README MUST describe the drop and the archive location.
- **FR-015**: `dist/` MUST be re-rendered for every harness and committed with the source change (constitution III).
- **FR-016**: Unit tests in `tools/tests/` MUST cover: success (archive equals source, folder gone, one commit with the expected message touching only the folder, JSON output carrying archive path, PR URL and totals sentence), refusal for each non-`pr-open` status, refusal on archive collision, refusal under a live lock, no git change on a failed verification, and on a Pen run: `factory/design/` lands at `docs/design/<branch>/` with identical content, every map reference to the old path is rewritten, and an existing target refuses with no change.
- **FR-017**: When `specs/<branch>/factory/design/` exists, `factory drop` MUST, in the drop commit, move it to `docs/design/<branch>/` (`git mv`) and rewrite every `specs/<branch>/factory/design/` path prefix in `docs/design-code-map.json` to `docs/design/<branch>/`, preserving all other map content. It MUST refuse with no change when the target exists. `design-code-mapping.md` MUST state that evidence lives under `factory/design/` during the run and at `docs/design/<branch>/` after the drop.

### Key Entities

- **Run folder**: `specs/<branch>/factory/` in the worktree. Holds `state.json`, `brief.md`, analyze reports, remediation logs, review findings and other run artifacts.
- **Run archive**: `${FACTORY_HOME:-~/.factory}/archive/<repo-name>-<branch>/`. A byte-identical copy of the run folder at drop time. Written once, never overwritten by the factory.
- **Drop commit**: the single commit `factory: drop run artifacts` that removes the run folder from the branch and, on Pen runs, moves design evidence to its permanent home.
- **Permanent design evidence**: `docs/design/<branch>/`. Pen design evidence after the drop; the canonical map references it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For 100% of runs that reach `pr-open`, the PR's final file diff contains zero paths under `specs/<branch>/factory/`.
- **SC-002**: For 100% of dropped runs, the archive contains every file of the run folder with identical content.
- **SC-003**: Every refusal condition (wrong status, archive collision, live lock, failed verification, already dropped) leaves git history, working tree and existing archives unchanged, as proven by the unit tests.
- **SC-004**: The drop adds exactly one commit to the branch and runs in under 5 seconds for a typical run folder.
- **SC-005**: The build gate passes: every harness renders and `dist/` shows no drift.

## Assumptions

- The repository name used in the archive path matches the one the improvement backlog export uses (`<repo-name>-<branch>`), so both artifacts of one run share a key.
- A failed copy leaves no archive behind (temporary copy plus atomic rename), so the collision rule only ever sees complete archives.
- `set-status pr-open` has already written the final state before the drop, so the archived `state.json` is the run's final state.
- The attached opencode `adapter.json` model edits are context only; uncommitted adapter edits on the default branch are not touched.
- Existing `specs/007..010/*/factory/` folders on the default branch stay; only future runs drop.
- Chain is lite with fast mode on.
