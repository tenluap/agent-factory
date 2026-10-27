# Research: agent time budget, session issue backlog, benchmark

Phase 0 output. Every decision below was settled in the brief (brainstorm/grill rounds) or is resolved here; no `NEEDS CLARIFICATION` remains.

## 1. Enforcement model

- **Decision**: cooperative deadline in role inputs plus post-hoc ledger detection (brief, Q2/Q8, G2/G3).
- **Rationale**: no new harness verb, no kill switch; the orchestrator already timestamps every spawn in `state.ledger`, so detection is a comparison, not new machinery.
- **Alternatives considered**: hard kill via watchdog (loses uncommitted work); detect-only (leaves runs unbounded).

## 2. Budget resolution

- **Decision**: `factory_cli/budget.py` reads `${FACTORY_HOME}/config.json` `budget: { "default_s": 300, "roles": { "<role>": <seconds> } }`. Missing config, missing role entry or unusable (non-positive, non-integer) value falls back to 300. A new read command `factory budget <role>` prints `{ "role", "seconds", "deadline" }` with `deadline` = now + seconds, ISO UTC.
- **Rationale**: one source of truth for the fallback rules (FR-001, edge cases); the orchestrator derives a spawn deadline by one `SHELL` call instead of parsing config itself, and `role: orchestrator` reuses the same lookup for FR-007.
- **Alternatives considered**: orchestrator parses config.json directly (duplicates the fallback rules); a `deadline` CLI flag (config would not bind it).

## 3. Deadline passing

- **Decision**: before every `SPAWN`/`SPAWN_PARALLEL` role the orchestrator runs `factory budget <role>` and passes `deadline` in the spawn's inputs, alongside `F` and `worktree`. Core files stay harness-neutral (verbs only).
- **Rationale**: constitution II; the deadline is spawn input data, not a harness feature.

## 4. Overrun recording and dedupe

- **Decision**: `factory ledger-add` gains `--overrun '<json>'` carrying the role's self-report `{ "cause", "detail" }`. After appending the ledger entry the writer records **exactly one** issue: cause from the self-report when present, `unreported` when only the ledger duration exceeds the role budget, nothing when neither holds. A shared `append_issue(...)` helper is the single append path used by `issue-add`, `ledger-add`, `set-status halted` and `verify --fail`.
- **Rationale**: "recorded once" (FR-006, edge case 1) becomes structural instead of an orchestrator convention; the writer sees both signals in one locked write.
- **Alternatives considered**: orchestrator-side dedupe (relies on prompt discipline, untestable); a separate `issue-dedupe` command (extra surface).

## 5. Stall cap bookkeeping (FR-004, G1, grill-with-docs Q1)

- **Decision**: every `partial` return of a stage counts toward the three-strike stall cap when no new commit lands between them, whatever its stop reason (grill-with-docs Q1; FR-004 is the authority). Every `partial` return is recorded as exactly one issue: a deadline stop as `overrun` (cause from the self-report, `unreported` when the report is missing), any other stop reason (e.g. low context) as `retry`. A failure-policy retry (crash, unparseable output) is **not** a `partial` return: it records `retry` unmarked and never counts. The two `retry` sources are told apart by a per-record discriminator: `issue-add`/`ledger-add` gain `--partial-return`, which stamps `partial_return: true` on the recorded issue and is accepted only for kinds `overrun`/`retry` of the file-writing roles (spec-builder, code-build, fixer), refused otherwise (exit 1, named reason). Every counted record carries `commit` = worktree HEAD at record time. `issue-add`/`ledger-add` return `stalls: { "stage", "consecutive_no_commit", "cap": 3, "halt": <bool> }` for records that count: trailing `partial_return: true` issues of one stage sharing one `commit`. At 3 the orchestrator runs `set-status halted --halt-reason ...`, NOTIFYs and asks. Any new commit resets the count, so committed progress is uncapped. Records of the never-stopped roles (reviewers, judge, orchestrator) never count — those roles never return `partial`, so their records are post-hoc detections and the writer refuses the mark for them — and neither do `agent-failure`, `halt` or `verify-fail`, which end or diagnose the run instead of resuming a stage.
- **Rationale**: the count must survive resume and cross sessions (constitution IV), so it derives from append-only state rather than agent memory; the `commit` field is the minimal provenance that makes "no new commit between them" checkable, and `partial_return` makes the counted set exactly FR-004's partial returns. Kind and role alone cannot key the set: a failure-policy retry shares the `retry` kind with a non-deadline `partial` stop but must not count. The mark is accepted only where a partial return exists (the file-writing roles' `overrun`/`retry` records), so never-stopped roles' records are excluded structurally, not by cause.
- **Alternatives considered**: counting deadline stops only (the earlier narrowing — rejected by grill-with-docs Q1: a loop of non-deadline `partial` returns with no new commit must halt too); keying the count on kind and role (rejected: it also counts failure-policy retries, which FR-004 excludes); a `partial_stops` state field (adds a second schema field beyond `issues[]`); keying the count on the `unreported` cause (it cannot tell a deadline stop from a slow finish).

## 6. State schema v5

- **Decision**: `version: 5` adds only `issues[]`; readers accept 1–5; the first write upgrades in the same atomic write. Issue record: `{ "at", "kind", "stage", "role", "cause", "detail", "duration_ms", "commit" }`. `kind` closed: `overrun`, `agent-failure`, `retry`, `halt`, `verify-fail`. `cause` is `null` except for `overrun`, where it is required from `large-input`, `test-loop`, `retry`, `tool-slow`, `scope-too-big`, `other`, `unreported`. Append-only: the writer only appends.
- **Rationale**: FR-008/FR-009 and the assumption "schema v5 adds only `issues[]`"; `at`/`commit` are per-record provenance, consistent with every other append-only list in the state.

## 7. Existing event paths (FR-010)

- **Decision**: `set-status halted` records `halt` (detail = `--halt-reason`) and `verify --fail` records `verify-fail` inside the writer; the orchestrator's failure policy records `retry` and `agent-failure` via `factory issue-add <kind> <stage> <role> --detail --duration-ms [--cause] [--commit]` (the contract in `contracts/cli.md`; spec FR-008's older signature wording lags it — see plan.md "Spec alignment follow-ups"). A `partial` return's stop is recorded the same way: a deadline stop as `overrun` (via `ledger-add --overrun`/`issue-add`), any other stop reason as `retry` (§5) — each carrying `--partial-return`, the mark the stall rule counts; a failure-policy retry records `retry` without it.
- **Rationale**: two of the four paths are writer-owned already, so their issues cannot be forgotten; the two failure-policy events and the non-deadline partial stop need the spawn context only the orchestrator has.

## 8. Backlog export (FR-011)

- **Decision**: `set-status pr-open|aborted`, after its state write, exports `${FACTORY_HOME}/improvements/<repo-name>-<branch>.json` atomically (temp + `os.replace`), containing the run's issues, `totals.compute` output, `factory_sha` (best-effort `git -C <F> rev-parse HEAD`, `null` when the installed skill is not in a git tree), the run identity and `"status": "ready"`. Zero-issue runs export too.
- **Rationale**: the file's existence is the gate and it is created only at run end, structurally; totals reuse the one interval-union implementation (FR-009).

## 9. Claim gate (FR-012)

- **Decision**: `factory improvements` lists every `*.json` in the improvements directory with name, run, status, issue counts and a `suggested_feature` text built from the recorded issues. `factory improvements claim <name>` refuses (exit 1, message naming the problem) when the file is missing, when its status is not `ready`, and — when the source run is discoverable in the current repo — when that run has not ended, naming the run. A successful claim rewrites the file to `"status": "claimed"` with `claimed_at`.
- **Rationale**: re-verifying the source run makes the acceptance scenario ("claim refused naming the source run") testable even against a hand-written or copied file; `claimed` state gives the second-claim refusal its meaning.

## 10. `/factory improve` route (FR-013)

- **Decision**: `SKILL.md` step 0 routes `improve` to `factory improvements`, shows the ready backlogs and each `suggested_feature`, and stops; starting an improvement run stays a manual `/factory <feature>` by the user. The recursive improver agent is out of scope.
- **Rationale**: FR-013's "never starts a run by itself".

## 11. Benchmark fixture and driver (FR-014/FR-015)

- **Decision**: `conformance/bench/<name>/` holds `bench.json` (fixture repo path, overlay dir, acceptance command, brief/seed filenames), a pre-settled `brief.md`, a `state-seed.json` pending state with `stage: "worktree"`, `mode: { "chain": "lite", "fast": true }`, `stop_at: "approver"`, and `overlay/` (`.specify/` scaffold plus fixture `CLAUDE.md`/`AGENTS.md` build/test commands). `tools/bench.py run --harness <h>` copies `conformance/fixture-repo` + overlay into a throwaway git repo, seeds `${FACTORY_HOME}/pending/`, and drives the headless harness with the factory's resume invocation. `score <state.json>...` and `compare a.json b.json` follow FR-015/FR-016.
- **Rationale**: a pre-settled fixture keeps replay reproducible and equal-footed across factory versions; the overlay supplies the SpecKit prerequisite the flow needs without touching the real checkout.

## 12. Headless harness support

- **Decision**: `tools/bench.py` maps `claude-code` → `claude -p <prompt>` and `opencode` → `opencode run <prompt>`; any other harness is refused with a message naming it. The documented manual fallback (run `/factory` on the fixture, then `score`) covers the rest (FR-018).
- **Rationale**: these are the two headless CLIs the brief names; refusing loudly beats a guessed command line.

## 13. Scorer single source of truth (FR-017)

- **Decision**: `tools/bench.py` imports `factory_cli.state.read_state`, `factory_cli.totals.compute` and `factory_cli.checks.latest_verify` — the same reading code the rest of the tooling uses. Live runs stay manual (token cost); the suite tests `score`/`compare` on recorded fixtures.
- **Rationale**: FR-017 and the brief's "scorer shared with recorded-state reading".

## 14. Benchmark pass conditions (FR-016, G5)

- **Decision**: `score` resolves all four conditions offline from recorded artifacts and reports each with its name:
  1. `reached-approver` — the state's `stage` is `approver`/`pr`, or a `history` entry carries stage `approver`.
  2. `last-verify-green` — `checks.latest_verify(state)` records `verify-pass`.
  3. `no-blocking-findings` — the latest `reviews/round-*/verdict.json` beside the state has `verdict: "pass"` (no `confirmed_blocking`).
  4. `fixture-acceptance` — the latest verify record's `commands` include the bench feature's `acceptance` command with `status: "pass"` (the recorded run of the fixture's own acceptance test, extended per bench feature).
  A missing artifact for any condition scores a fail naming that condition; the scorer never crashes (edge case 8).
- **Rationale**: scoring stays offline on recorded state (spec quality constraint) while all four conditions remain checkable from what a run records; the acceptance evidence is the verify record that already carries command/status pairs.
- **Alternatives considered**: running the acceptance test at score time (breaks offline scoring); a free-standing acceptance result file next to the state (a second source of truth beside the verify record).

## 15. Quality constraints (spec, "Quality and Verification Constraints")

- **Data integrity**: append-only issues through the single writer; atomic backlog export; claim cannot create a backlog.
- **Security**: exports/scores carry run facts only; the improvement route writes only under `${FACTORY_HOME}`.
- **Error limits**: every new command refuses bad input with the documented exit code and a message naming the problem; the budget check is one lookup plus one clock read per unit.
- **Performance**: per-spawn overhead is one `budget` read; scoring is offline.
- **Dependencies**: stdlib only (ENG-27).
- **Observability**: issues are visible in state and CLI reports; score JSON names every metric and every failed condition.
- **Compatibility**: readers accept schema 1–5; all five harnesses re-rendered.
- **Delivery**: build command re-renders every harness; `test -z "$(git status --porcelain -- dist/)"` gates drift (constitution III).
