# Feature Specification: Post-Run Retro for Self-Improvement

**Feature Branch**: `016-retro-self-improve`

**Created**: 2026-10-30

**Status**: Draft

**Input**: User description: "Add a post-run retro step: after a run reaches `pr-open` and before `drop`, a read-only standard-tier `retro` role mines the ended run's ledger, issues and verdicts for improvement signals (analyze escalation rate, recurring fixer finding classes, per-reviewer judge rejection rate, in-est outliers, halts) and returns up to 3 deduplicated improvement candidates that the orchestrator persists into the factory home's `improvements/` backlog."

## Clarifications

### Session 2026-10-30

- Q: How does the read-only retro role know which signals open `ready` backlog entries already cover? → A: The orchestrator passes the signal keys of open `ready` retro entries in the retro inputs; retro reads nothing outside its inputs.

### Grill-with-docs 2026-10-30

- Q: Where does retro read the ledger and history from? → A: The retro inputs add the run's `state.json` path; retro reads it read-only for ledger and history.
- Q: Who validates, dedupes, caps and writes retro backlog entries? → A: A new deterministic `factory improvements add --from <file> --run <branch>` writer validates, dedupes against open `ready` entries, caps at 3, writes atomically and returns `written`/`skipped`/`dropped` JSON. Mining stays in the retro role; the earlier "no new CLI" decision narrows to "no CLI that mines signals".
- Q: What does a retro backlog entry carry? → A: `kind: retro`, `signal_key`, `evidence` and `suggested_feature`. The listing prefers a stored `suggested_feature` when present; run exports stay unchanged.
- Q: How does a resumed run avoid a second retro? → A: A ledger entry with stage `retro` marks the retro as spawned; fixed entry names make writes idempotent; no new history event is added.
- Q: What does "improvement backlog" mean now? → A: An umbrella term with two kinds of entry: Run export and Retro entry.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Every finished run leaves improvement candidates (Priority: P1)

A factory maintainer finishes a run that opens a PR. Without any extra action, the factory reviews how that run went and records up to three concrete improvement candidates in the improvement backlog. The next time the maintainer runs `/factory improve`, those candidates appear next to the existing per-run backlog, ready to pick.

**Why this priority**: This is the whole value of the feature: the self-improve loop gets fed automatically by every run instead of depending on someone to read run artifacts by hand.

**Independent Test**: Complete a run that reaches `pr-open` with a known pattern in its digest (for example, a reviewer whose findings the judge rejected in every round). Confirm the retro runs between `pr-open` and `drop`, and that a `ready` backlog entry naming that signal appears in the improvement backlog and is listed by `/factory improve`.

**Acceptance Scenarios**:

1. **Given** a run has just been set to `pr-open`, **When** the orchestrator continues the PR step, **Then** it spawns the `retro` role once with the run's digest (the run summary output, the run's `state.json` path, the analyze report paths and the round verdict paths) before it archives the run.
2. **Given** the retro returns candidates, **When** the orchestrator accepts them, **Then** each accepted candidate is persisted in the factory home's improvement backlog as a `ready` entry and appears in the `/factory improve` listing.
3. **Given** the retro role runs, **When** it finishes, **Then** it has changed no file in the worktree, the run state, or the factory home; backlog entries are written only by the orchestrator through `factory improvements add`.
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
4. **Given** a candidates file with more than three valid candidates, **When** `factory improvements add` runs, **Then** it writes at most three and reports the rest as `dropped`.

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
- A run that re-enters the PR step's retro sub-step with a `retro` ledger entry already present does not spawn the retro again; re-running `factory improvements add` with the same candidates rewrites the same fixed entry names, so no duplicates appear.
- The digest is missing a source (for example no review rounds because the run used no review); the retro mines the signals it can and ignores the rest.
- A candidate in the envelope is malformed (missing signal key, evidence or suggested feature text); `factory improvements add` reports it as `dropped` and writes the valid ones.
- The factory home `improvements/` folder is not writable; the orchestrator skips persistence, discloses it in the final notice, and still finishes the run.

## Requirements *(mandatory)*

### Functional Requirements

FR IDs are stable; FR-015 to FR-017 were added during grilling and sit next to the requirements they refine.

- **FR-001**: The factory MUST define a dedicated `retro` role that is read-only and runs at the standard model tier.
- **FR-002**: The orchestrator MUST spawn the `retro` role only for runs that reach `pr-open`, after recording `pr-open` and before archiving the run.
- **FR-003**: The orchestrator MUST give the retro role the ended run's digest (the run summary output, the run's `state.json` path, the paths of every recorded analyze report and the paths of every review round verdict) and the signal keys of every open `ready` retro backlog entry. The retro role MUST read `state.json` read-only, for its ledger and history, and MUST read nothing outside these inputs.
- **FR-004**: The retro role MUST mine these five signals: analyze escalation rate; recurring confirmed-blocking finding classes sent to the fixer; judge rejection rate per reviewer; time-estimate (`in-est`) outliers per role; and halt and issue clusters.
- **FR-005**: The retro role MUST return its candidates in its protocol envelope; each candidate MUST name its signal, a stable signal key, the supporting evidence from the digest, and a suggested feature text ready for `/factory <feature>`.
- **FR-006**: The retro role MUST return at most three candidates per run.
- **FR-007**: The retro role MUST skip any signal whose key is in the covered signal keys it received, and `factory improvements add` MUST re-check against the backlog before writing.
- **FR-008**: The orchestrator MUST persist accepted candidates only through `factory improvements add --from <file> --run <branch>`, which writes each one to the factory home's `improvements/` backlog as a `ready` Retro entry. The existing `/factory improve` listing and claim flow MUST handle Retro entries without change to their user-visible behaviour for Run exports.
- **FR-015**: `factory improvements add` MUST be deterministic and mine no signals. It MUST validate each candidate, drop malformed ones, skip any whose signal key an open `ready` Retro entry from another run already covers (the run's own `ready` entry for that key is replaced in place, per FR-016), cap the written entries at 3 per run, write each entry atomically, and print JSON naming the `written`, `skipped` and `dropped` candidates.
- **FR-016**: A Retro entry MUST carry `kind: retro`, its `signal_key`, `evidence`, `suggested_feature` and its source run. Its name MUST derive only from the source run and signal key, so rewriting the same candidate replaces the same entry. Run exports MUST stay unchanged.
- **FR-017**: The improvements listing MUST show a Retro entry's stored `suggested_feature` and expose its `kind` and `signal_key`; a Run export keeps its generated suggested feature. The orchestrator MUST take the covered signal keys for FR-003 from this listing.
- **FR-009**: The retro role MUST NOT write files, edit state, or ask the user questions.
- **FR-010**: Every retro spawn, including a failed attempt, MUST be recorded in the run ledger with stage `retro`, like every other spawn, before the run is archived. A `retro` ledger entry present when the orchestrator enters the PR step's retro sub-step marks the retro as spawned: on re-entry of that sub-step the orchestrator MUST NOT spawn the retro again. The check runs only on entry, so the in-turn retry (FR-011) is unaffected. No new history event is added. A run interrupted between `pr-open` and archiving is recovered by hand (archive with `factory drop`, then push), named in the design record and orchestrator skill.
- **FR-011**: A failed retro MUST get exactly one fresh retry; a second failure MUST skip the retro without halting or blocking the run.
- **FR-012**: The final notice MUST name a skipped retro or a skipped backlog write and the reason.
- **FR-013**: The protocol envelope reference MUST define the retro candidate field shape, and `DESIGN.md` MUST record the retro step before the core and adapter files change.
- **FR-014**: The new role and orchestrator step MUST stay harness-neutral in `core/` and MUST render for every harness.

### Key Entities

- **Run digest**: The ended run's summary output (ledger, issues, totals, history), its `state.json` path (read-only), the recorded analyze report paths and the review round verdict paths. Input only, passed with the covered signal keys.
- **Improvement signal**: One of the five signal kinds, identified by a stable signal key (signal kind plus subject, for example a reviewer or role name).
- **Improvement candidate**: A proposed improvement: signal key, evidence, impact rank and suggested feature text. Returned by retro, at most three per run.
- **Improvement backlog**: The factory home `improvements/` folder, with two kinds of entry, each `ready` until claimed by the existing improve flow.
- **Run export**: The existing run-end entry with one run's issues, totals and factory version; unchanged by this feature.
- **Retro entry**: One persisted candidate (`kind: retro`, signal key, evidence, suggested feature, source run), written only by `factory improvements add`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of runs that reach `pr-open` either run the retro or name its skip in the final notice.
- **SC-002**: No run gains more than 3 retro backlog entries.
- **SC-003**: Zero new backlog entries duplicate a signal already covered by an open `ready` entry.
- **SC-004**: Zero runs fail, halt or lose their PR because of the retro step.
- **SC-005**: Every retro candidate a maintainer picks from `/factory improve` can start a run with its suggested feature text unchanged.

## Assumptions

- "Accepted" candidates are those `factory improvements add` validates (well-formed, within the cap, not duplicates); no user approval step is added.
- Each candidate is persisted as its own Retro entry next to the existing Run export, so the existing listing and claim behaviour keep working; the plan fixes the exact file name and the candidates file location.
- "Covered by an open `ready` entry" means an existing `ready` (not claimed) entry from another run with the same signal key; the run's own `ready` entry is rewritten in place.
- The existing per-run backlog export at `pr-open` stays unchanged.
- Signal thresholds (what counts as an outlier or a recurring class) use simple defaults chosen in the plan; tuning is out of scope.
- No CLI command mines signals; the only new CLI command is the deterministic `factory improvements add` writer.
- Retro for aborted or halted runs is out of scope.
