# Research: Stabilise and optimise the factory

Phase 0 output for `007-stabilise-factory`. Format per entry: **Decision**, **Rationale**, **Alternatives considered**.

## R1. Where the state writer lives

- **Decision**: `core/skills/factory/bin/factory` stays a thin entry script (argv → `factory_cli.cli.main`, exit codes preserved); logic lives in `core/skills/factory/bin/factory_cli/` modules (`__init__`, `cli`, `state`, `lock`, `checks`, `totals`, `commands`). The renderer's `copytree` already carries the folder into every `dist/<harness>/skill/` unchanged.
- **Rationale**: the brief fixes this layout; it keeps every rendered skill self-contained on all five harnesses and keeps `dist/` generated (Constitution III).
- **Alternatives considered**: a separate `tools/factory_cli/` package (breaks the shipped-skill self-containment); one growing script (the current 322-line file is already at the limit where validation, locking and gates would tangle).

## R2. State schema version 4

- **Decision**: `version: 4` adds `decisions` (append-only), `started_at`/`ended_at` per ledger entry, a `verify` payload on verify history entries, and locks the history-event vocabulary to `complete`, `verify-pass`, `verify-fail`, `approved`, `gate-override`, `aborted`, `pr-open`, `resumed`, each event written by the one command R5 names for it (FR-003). Timeline kinds stay `questions | notice | approver | halt`. Readers accept 1–4 including legacy relay shapes; the writer upgrades a run in the same atomic write that first changes it (FR-022).
- **Rationale**: one version bump per brief decision ("State schema bumps to version 4"); upgrade-on-write needs no migration command and never rewrites a run that is only read (US1 scenario 3).
- **Alternatives considered**: per-field versioning (no evidence of need); a standalone `factory migrate` command (violates "writers upgrade on first write" simplicity).

## R3. The verify record

- **Decision**: a verify record is one history entry written by `factory verify --commands ... --pass|--fail`, with event `verify-pass` or `verify-fail` — the two verify values of FR-003's closed vocabulary — carrying `commands` (each command string and its exit status) and `at`. The review gate reads the latest verify entry and requires `verify-pass`; a failed entry followed by a passing one is decided by the latest; none at all is refused (spec Edge Cases).
- **Rationale**: FR-003's vocabulary is closed and contains no bare `verify` event; naming the pair of events is the only reading consistent with it and with the record's pass/fail payload. Key Entities now uses the same pair wording, so one term names one concept.
- **Alternatives considered**: a separate `verify` list outside `history` (would need a second vocabulary and a second read path); a bare `verify` event (breaks FR-003's closed list).

## R4. Atomic writes, locking, takeover

- **Decision**: `state.py` writes `state.json` as temp file + `os.replace` in the same directory, validating first. `lock.py` keeps a JSON lock file: `<worktree>/specs/<branch>/factory/lock.json` for a worktree run, beside the pending file (`<name>.lock.json`) for a pending one (FR-005). The lock records owner PID, host, harness and time. A write under a live lock is refused and the owner reported; a lock is stale only when the recorded host is this host and the owner process is gone (`os.kill(pid, 0)`); elsewhere it is never stale automatically; `factory lock take <run>` is the only takeover and records the takeover explicitly.
- **Rationale**: matches FR-005 and the clarified staleness rule ("recorded host, owner process gone; elsewhere never automatically; takeover always explicit").
- **Alternatives considered**: `fcntl` advisory locks (do not survive process death in a diagnosable way and are host-local anyway); stale-by-age (the clarifications reject it).

## R5. Transition gates

- **Decision**: `checks.py` holds one gate table checked before the write that would advance a stage: → `review` needs the latest verify record to pass (FR-006); → `pr` needs a recorded approval decision; → `implement` needs analyze recorded clean, remediated, or a user override. A gate override is a normal decision-record entry (stage, question ID, answer, `auto: false`, time) in the approver's veto list, and the transition it permits also gets a `gate-override` history entry referencing that decision. An approval follows the same shape: `decisions-add <stage> <qid> '<answer>' --kind approved` at `approver` records it, and the `approver` → `pr` transition it permits gets the `approved` history entry referencing that decision. The run-ending events have their writer in `set-status`: its `aborted` and `pr-open` forms append those history entries and set `ended_at`. With `checkpoint`'s `complete`/`approved`/`gate-override`, `verify`'s pair and the resume path's `resumed`, every event of FR-003's vocabulary has exactly one writer. Refusals name the missing record.
- **Rationale**: one table gives one refusal vocabulary for tests and for the orchestrator's messages (SC-005); recording approvals as decision entries (not bare history events) keeps one audit list and one writer path (`decisions-add`), matching the settled clarification on gate overrides.
- **Alternatives considered**: scattered `if` checks per command (harder to test exhaustively); letting `set-status` bypass gates (that is exactly run 006's failure); an `approve` command of its own (a second writer for one record kind); approvals as bare `approved` history events with no decision entry (nothing to audit or veto, and the `pr` gate would read history instead of decisions).

## R6. Role-output shape checking

- **Decision**: `checks.py` validates the final fenced `json` block of a role's output file against the three shapes: envelope (protocol.md), reviewer report and judge verdict (findings.md). Key sets, types and required fields are encoded in the module, documented with the reference section they mirror; the fenced examples in `protocol.md` and `findings.md` are test fixtures that must pass, and one malformed variant per shape must fail (FR-007).
- **Rationale**: prose cannot be machine-checked; encoding the shapes once in code with the reference examples as fixtures keeps code and prose aligned (ENG-6).
- **Alternatives considered**: a JSON Schema file per shape (a second artefact to keep in sync for three small shapes); trusting the orchestrator (that is S4's problem).

## R7. Effort accounting

- **Decision**: `totals.py` computes agent effort as the union of ledger spawn intervals (`started_at`/`ended_at`, with `duration_ms` kept for older entries) and human time as the union of timeline wait intervals (`at` → `answered_at`), reports them separately, and derives overhead as `max(wall − human − agent, 0)`; no report sums parallel durations (FR-009).
- **Rationale**: unions make the SC-003 invariant (human + agent ≤ wall clock) hold by construction whenever waits and spawns do not overlap, which the flow guarantees.
- **Alternatives considered**: summing durations with a clamp (the run-005 defect); a scheduler model that tracks overlap across categories (no requirement needs it).

## R8. Test layout and fixtures

- **Decision**: a new `tools/tests/` package (`__init__.py` + modules `test_state`, `test_commands`, `test_gates`, `test_envelope`, `test_totals`, `test_lock`, `test_recovery`, `test_install`, `test_render_models`) with `tools/tests/fixtures/`. The 005/006 run states are recovered from git history (`git log --all -- 'specs/*/factory/state.json'`, commits before `5a8e7da` / `37e7d86`) and stored as fixtures with a defect manifest naming the stability-brief §3 core defects each replay must report, each appended extra carrying a written reason (SC-002). Test helper code builds throwaway states and fixture repos under `tempfile`.
- **Rationale**: `python3 -m unittest discover -s tools` discovers packages recursively, so the command stays unchanged; recovered real states beat synthetic ones for the replay.
- **Alternatives considered**: more `test_*.py` files directly in `tools/` (mixes tool and test code as the suite grows); synthesising 005/006 states by hand (they must show the real recorded defects).

## R9. Model configuration (S10)

- **Decision**: `adapters/claude-code/adapter.json` keeps `models: {"deep": "anthropic/claude-opus-5-5", "standard": "anthropic/claude-sonnet-5-5"}`; `codex`, `copilot`, `opencode`, `zcode` ship `"models": {}`. Personal choices live in `${FACTORY_HOME}/config.json` (the renderer already merges `{"models": {"<harness>": {...}}}`); the user's current personal OpenCode picks move into that file as part of the change. `install.sh` prints the effective model per role after rendering. A test asserts: exactly one adapter ships defaults, the README statement matches `adapters/`, and config overrides reach the rendered agents (FR-015).
- **Rationale**: matches the brief decision and README's existing claim; the merge hook already exists in `render.load_adapter`.
- **Alternatives considered**: documenting the pinned models instead (FR-015 explicitly rejects shipping personal provider IDs); generating README from `adapter.json` (more machinery than an alignment test needs).

## R10. Preflight setup guidance (S11)

- **Decision**: when the current harness's SpecKit skills are missing, preflight names the exact `specify init --here <speckit_init>` command from `harness.md` and offers to run it, exactly as for a missing `.specify/`; decline stops the run with the command printed (FR-016). A `SKILL.md` step 1 edit plus a `harness.md` field where a harness needs extra arguments.
- **Rationale**: run 006's halt was a missing guidance path, not a missing capability.
- **Alternatives considered**: auto-running init (violates the ask-once pattern); installing skills silently (out of scope).

## R11. Declared-file checkpoints (S12, FR-017)

- **Decision**: a role's final output declares every changed file in its envelope `files` list. `factory checkpoint <stage> --files <path>...` (or `--envelope <file>` to read the list) stages exactly `spec_dir` plus that list, commits with `factory: <stage> complete`, and reports any other modified or untracked worktree file without committing it.
- **Rationale**: `git add -A` is the run-005/006 secret-commit risk; the envelope already has a `files` field (protocol.md), so no new role contract is needed.
- **Alternatives considered**: refusing to checkpoint when anything else is dirty (too strict for local build output); a pre-commit hook (the factory owns commits).

## R12. Rebind and prune (S13, S16, FR-012, FR-019)

- **Decision**: `factory rebind <run> --worktree <path>` validates that the path is a git worktree on the recorded branch, then rewrites stored absolute paths (`worktree`, `repo`) and reports the rewrite; sharing `FACTORY_HOME` alone is documented as not moving a run. `factory prune [--dry-run]` lists stale pending files — a pending file whose run has a worktree state or has ended (`pr-open`/`aborted`); a run whose only state is the pending file is never stale — and deletes nothing without the explicit `--delete` form.
- **Rationale**: both follow the clarified rules verbatim.
- **Alternatives considered**: automatic cleanup (brief §6 excludes automatic deletion); path-rewriting on read (would rewrite state the user never asked to change).

## R13. Read-only role access (S15, FR-014)

- **Decision**: a static conformance test renders every adapter and asserts each `read`-access agent file denies editing in the terms that adapter supports (Claude Code/ZCode tool lists without `Edit`/`Write`, OpenCode's deny-permission rules, Copilot's tool list). `codex` has no enforceable read-only agent surface; `adapters/codex/harness.md` documents the limitation and the golden-run checklist records it per adapter.
- **Rationale**: FR-014 requires verification where enforceable and disclosure where not; a static check is the only check available before a live run.
- **Alternatives considered**: runtime conformance probing per harness (part of the live golden run, recorded after merge).

## R14. CI (S9, FR-018)

- **Decision**: `.github/workflows/ci.yml` runs `python3 -m unittest discover -s tools`, re-renders all five harnesses and fails on `test -z "$(git status --porcelain -- dist/)"`, and runs `bash -n install.sh` (FR-018's installer syntax check).
- **Rationale**: the porcelain gate is the repository constitution's own gate and sees untracked additions, which `git diff --exit-code -- dist/` misses.
- **Alternatives considered**: `git diff --exit-code -- dist/` (constitution names it as not the gate); a separate drift script (the shell gate is one line).

## R15. Pen rules consolidation (S19, FR-021)

- **Decision**: `core/skills/factory/references/design-code-mapping.md` becomes the single home for Pen design rules. Duplicated prose in `SKILL.md` (steps 6, 8, 9), `state.md` ("Pen design context" keeps its schema facts only) and any other reference is replaced by pointers; every rule sentence is accounted for in a checked list so nothing is lost. `DESIGN.md`'s "Pen design references" section keeps its decision summary and links to the reference.
- **Rationale**: FR-021 requires one reference and no lost rule; `DESIGN.md` is the design authority (Constitution I), not the rule book.
- **Alternatives considered**: deleting the rules outright (would lose them); a generated reference (no source of truth exists to generate from).

## R16. Documentation corrections (FR-024)

- **Decision**: each S-item's design decision is a `DESIGN.md` "Decisions" entry written before its implementation task. The same change corrects the contradicted sentences: the manual-write fallback in `DESIGN.md` (State CLI paragraph) and `state.md` ("manual paths… fallback", checkpoint's `git add -A`), the unresolved wording in `docs/product-brief.md` §14 rows this run settles, and `README.md` (read-only CLI description, model defaults, checkpoint behaviour).
- **Rationale**: FR-024 and Constitution I ("the file is wrong unless `DESIGN.md` is changed deliberately in the same change").
- **Alternatives considered**: a follow-up documentation PR (FR-024 requires the same change).

## R17. Reported usage (S18, FR-010)

- **Decision**: ledger entries keep `reported: null` unless an adapter names a usage source; `show` and the totals line label reported usage separately from the word-count estimates (`in_est`/`out_est`), never merged into one number. No adapter exposes usage in tier 1, so the label is exercised with fixtures.
- **Rationale**: FR-010 requires the separation, not new collection machinery.
- **Alternatives considered**: scraping harness output for usage (no named source exists today).
