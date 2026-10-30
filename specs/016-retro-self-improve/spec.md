# Feature Specification: Post-Run Retro for Self-Improvement

**Feature Branch**: `016-retro-self-improve`

**Created**: 2026-10-30

**Status**: Draft

**Input**: User description: "Add a post-run retro step: after a run reaches `pr-open` and before `drop`, a read-only standard-tier `retro` role mines the ended run's ledger, issues and verdicts for improvement signals (analyze escalation rate, recurring fixer finding classes, per-reviewer judge rejection rate, in-est outliers, halts) and returns up to 3 deduplicated improvement candidates that the orchestrator persists into the factory home's `improvements/` backlog."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Every finished run leaves improvement candidates (Priority: P1)

A factory maintainer finishes a run that opens a PR. Without any extra action, the factory reviews how that run went and records up to three concrete improvement candidates in the improvement backlog. The next time the maintainer runs `/factory improve`, those candidates appear next to the existing per-run backlog, ready to pick.

**Why this priority**: This is the whole value of the feature: the self-improve loop gets fed automatically by every run instead of depending on someone to read run artifacts by hand.

**Independent Test**: Complete a run that reaches `pr-open` with a known pattern in its digest (for example, a reviewer whose findings the judge rejected in every round). Confirm the retro runs between `pr-open` and `drop`, and that a `ready` backlog entry naming that signal appears in the improvement backlog and is listed by `/factory improve`.

**Acceptance Scenarios**:

1. **Given** a run has just been set to `pr-open`, **When** the orchestrator continues the PR step, **Then** it spawns the `retro` role once with the run's digest (the run summary output plus the round verdict paths) before it archives the run.
2. **Given** the retro returns candidates, **When** the orchestrator accepts them, **Then** each accepted candidate is persisted in the factory home's improvement backlog as a `ready` entry and appears in the `/factory improve` listing.
3. **Given** the retro role runs, **When** it finishes, **Then** it has changed no file in the worktree, the run state, or the factory home; only the orchestrator writes backlog entries.
4. **Given** the retro role was spawned, **When** the run is archived, **Then** the archived run's ledger contains the retro spawn's cost entry.

---

### User Story 2 - Candidates stay few and non-duplicated (Priority: P2)

A maintainer who runs many features does not want the backlog flooded. Each run contributes at most three candidates, and a signal that an open `ready` backlog entry already covers is skipped rather than recorded again.

**Why this priority**: Without the cap and dedupe the backlog grows noisy and the loop loses its value; still, the loop works (noisily) without it, so it ranks after P1.

**Independent Test**: Seed the backlog with a `ready` entry covering signal X, then finish a run whose digest shows signals X, Y, Z and W. Confirm no new entry for X is written and at most three new entries exist.

**Acceptance Scenarios**:

1. **Given** the retro finds more than three signals, **When** it returns, **Then** its envelope carries at most three candidates, ranked by impact.
2. **Given** an open `ready` backlog entry already covers a signal, **When** the retro or the orchestrator considers that signal, **Then** no new entry is written for it.
3. **Given** the retro returns two candidates covering the same signal, **When** the orchestrator persists them, **Then** only one entry is written.

---

### User Story 3 - Retro never blocks a finished run (Priority: P2)

The PR is already open when retro runs. If the retro role fails, the maintainer still gets the archived run, the pushed branch and the final notice; the notice says the retro was skipped.

**Why this priority**: A post-run analysis must never cost the user their delivered PR or leave a run half-archived.

**Independent Test**: Force the retro role to return a malformed or failed envelope twice. Confirm the run still archives, pushes and notifies, and the final notice names the skipped retro.

**Acceptance Scenarios**:

1. **Given** the retro role fails once, **When** the orchestrator applies the standard failure policy, **Then** it spawns one fresh retry.
2. **Given** the retry also fails, **When** the orchestrator continues, **Then** it skips the retro, writes no backlog entry from it, archives the run, and the final `NOTIFY` names the skipped retro and why.
3. **Given** the retro returns zero candidates, **When** the orchestrator continues, **Then** it writes nothing and the run finishes normally.

### Edge Cases

- A run with no signals (no issues, no escalations, no rejections, no outliers, no halts) returns an empty candidate list; nothing is written.
- A run that ends as `aborted` or halts before `pr-open` gets no retro (out of scope).
- A resumed run that already completed the retro before an interruption does not run it again or write duplicate entries.
- The digest is missing a source (for example no review rounds because the run used no review); the retro mines the signals it can and ignores the rest.
- A candidate in the envelope is malformed (missing signal, evidence or suggested feature text); the orchestrator drops that candidate and keeps the valid ones.
- The factory home `improvements/` folder is not writable; the orchestrator skips persistence, discloses it in the final notice, and still finishes the run.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The factory MUST define a dedicated `retro` role that is read-only and runs at the standard model tier.
- **FR-002**: The orchestrator MUST spawn the `retro` role only for runs that reach `pr-open`, after recording `pr-open` and before archiving the run.
- **FR-003**: The orchestrator MUST give the retro role the ended run's digest: the run summary output and the paths of every review round verdict.
- **FR-004**: The retro role MUST mine these five signals: analyze escalation rate; recurring finding classes the fixer repaired; judge rejection rate per reviewer; time-estimate (`in-est`) outliers per role; and halt and issue clusters.
- **FR-005**: The retro role MUST return its candidates in its protocol envelope; each candidate MUST name its signal, a stable signal key, the supporting evidence from the digest, and a suggested feature text ready for `/factory <feature>`.
- **FR-006**: The retro role MUST return at most three candidates per run.
- **FR-007**: The retro role MUST skip any signal that an open `ready` backlog entry already covers, and the orchestrator MUST re-check this before writing.
- **FR-008**: The orchestrator MUST persist each accepted candidate in the factory home's `improvements/` backlog as a `ready` entry that the existing `/factory improve` listing and claim flow handle without change to their user-visible behaviour.
- **FR-009**: The retro role MUST NOT write files, edit state, or ask the user questions.
- **FR-010**: The retro spawn MUST be recorded in the run ledger like every other spawn, before the run is archived.
- **FR-011**: A failed retro MUST get exactly one fresh retry; a second failure MUST skip the retro without halting or blocking the run.
- **FR-012**: The final notice MUST name a skipped retro or a skipped backlog write and the reason.
- **FR-013**: The protocol envelope reference MUST define the retro candidate field shape, and `DESIGN.md` MUST record the retro step before the core and adapter files change.
- **FR-014**: The new role and orchestrator step MUST stay harness-neutral in `core/` and MUST render for every harness.

### Key Entities

- **Run digest**: The ended run's summary output (ledger, issues, totals, history) plus the review round verdict paths. Input only.
- **Improvement signal**: One of the five signal kinds, identified by a stable key (signal kind plus subject, for example a reviewer or role name).
- **Improvement candidate**: A proposed improvement: signal key, evidence, impact rank and suggested feature text. Returned by retro, at most three per run.
- **Backlog entry**: A `ready` item in the factory home `improvements/` folder, listed and claimed by the existing improve flow; a retro entry links back to its source run.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of runs that reach `pr-open` either run the retro or name its skip in the final notice.
- **SC-002**: No run gains more than 3 retro backlog entries.
- **SC-003**: Zero new backlog entries duplicate a signal already covered by an open `ready` entry.
- **SC-004**: Zero runs fail, halt or lose their PR because of the retro step.
- **SC-005**: Every retro candidate a maintainer picks from `/factory improve` can start a run with its suggested feature text unchanged.

## Assumptions

- "Accepted" candidates are those the orchestrator validates (well-formed, within the cap, not duplicates); no user approval step is added.
- Each candidate is persisted as its own backlog entry next to the existing per-run backlog export, so the existing listing and claim behaviour keep working; the plan fixes the exact file shape.
- "Covered by an open `ready` entry" means an existing `ready` (not claimed) entry with the same signal key.
- The existing per-run backlog export at `pr-open` stays unchanged.
- Signal thresholds (what counts as an outlier or a recurring class) use simple defaults chosen in the plan; tuning is out of scope.
- No new deterministic CLI command is added in v1.
- Retro for aborted or halted runs is out of scope.
